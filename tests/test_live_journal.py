"""Testy dziennika na żywo (`backtest/live_journal.py`, `data/fetch_live.py`) — bez sieci, na danych
syntetycznych z `backtest/negative_control.py`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import live_journal as lj
from backtest.negative_control import synthetic_ohlc, synthetic_returns
from backtest.sizing import apply_rules
from backtest.ts_momentum import (
    PHASES,
    formation_dates,
    phase_returns_liq,
    portfolio,
    signal_sign,
)
from data.fetch_live import active_usdt_perpetuals, parse_klines_1d

FEE = 0.0007


def _write_live(tmp_path, n_days=480, n_coins=22, seed=3):
    r = synthetic_returns(n_days, n_coins, seed=seed, start="2025-06-01")
    r.columns = ["BTCUSDT"] + [f"C{i:02d}USDT" for i in range(1, n_coins)]
    o = synthetic_ohlc(r, seed=seed)
    rng = np.random.default_rng(seed)
    for c in r.columns:
        pd.DataFrame(
            {
                "open_time": r.index,
                "open": o["open"][c].to_numpy(),
                "high": o["high"][c].to_numpy(),
                "low": o["low"][c].to_numpy(),
                "close": o["close"][c].to_numpy(),
                "quote_volume": rng.uniform(1e6, 1e8, n_days),
            }
        ).to_parquet(tmp_path / f"{c}_1d.parquet", index=False)
        ts = pd.date_range(r.index[0], periods=3 * n_days, freq="8h")
        pd.DataFrame({"timestamp": ts, "funding_rate": 1e-4}).to_parquet(
            tmp_path / f"{c}_funding.parquet", index=False
        )
    btc = o["close"]["BTCUSDT"]
    prem = 1.0 + 0.001 * np.sin(np.arange(n_days) / 9.0)
    pd.DataFrame({"open_time": r.index, "close": btc.to_numpy() * prem}).to_parquet(
        tmp_path / "coinbase_BTC-USD_1d.parquet", index=False
    )
    ts8 = pd.date_range(r.index[0], periods=3 * n_days, freq="8h")
    pd.DataFrame({"timestamp": ts8, "close": np.repeat(btc.to_numpy(), 3)}).to_parquet(
        tmp_path / "spot_BTC-USDT_8h.parquet", index=False
    )
    # poprawka 8: Fear & Greed jak z `fetch_external.fetch_fng` (date, value, label)
    v = rng.integers(5, 96, n_days).astype(float)
    pd.DataFrame(
        {"date": r.index, "value": v, "label": np.where(v < 45, "Fear", "Greed")}
    ).to_parquet(tmp_path / lj.FNG_FILE, index=False)
    return lj.load_live(tmp_path)


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    return _write_live(tmp_path_factory.mktemp("live"))


def _formation_day(data, phase=0):
    close = data["close"]
    end = close.index[-1] + pd.Timedelta(days=1)
    return formation_dates(close.index, lj.ENGINE_START, end, phase)[-3]


def test_today_phase_matches_engine_notional(live):
    """Σ|wag| fazy formowanej w t (×7) = nominał tej fazy w silniku na początku dnia t+1."""
    t = _formation_day(live)
    pos, _, _, _ = lj.positions(live, t, FEE)
    tr = pos[(pos["component"] == "trend") & pos["today"]]
    assert len(tr) and tr["phase"].nunique() == 1
    ph = int(tr["phase"].iloc[0])
    d = lj.truncate(live, t + pd.Timedelta(days=1))
    members = lj.monthly_members(d["volume"], lj._months(t))
    _, per_phase = portfolio(
        d["close"],
        d["funding"],
        members,
        lj.ENGINE_START,
        t + pd.Timedelta(days=2),
        FEE,
        liq={"high": d["high"], "low": d["low"], "lev": lj.LEV_TREND, "mmr": lj.MMR},
    )
    engine = per_phase[ph].loc[t + pd.Timedelta(days=1), "gross_notional"]
    assert PHASES * tr["weight"].abs().sum() == pytest.approx(engine, rel=1e-9)
    # znak = znak zwrotu 28 dni w dniu formowania
    s = signal_sign(d["close"]).loc[t]
    for row in tr.itertuples():
        assert row.sign == s[row.symbol]


def test_no_lookahead_positions(live):
    """Dopisanie dni po t nie zmienia pozycji ogłoszonych na podstawie danych do t."""
    t = _formation_day(live)
    a, ka, _, _ = lj.positions(lj.truncate(live, t), t, FEE)
    b, kb, _, _ = lj.positions(live, t, FEE)
    pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))
    assert ka == pytest.approx(kb)


def test_next_multipliers_equal_rule_on_next_day(live):
    t = _formation_day(live)
    rets, _ = lj.components(live, t + pd.Timedelta(days=1), FEE)
    _, k_next = lj.next_multipliers(rets.iloc[:-1])
    full = apply_rules(rets, "R1").set_index("date")
    assert k_next["trend"] == pytest.approx(full["k_trend"].iloc[-1])
    assert k_next["coinbase"] == pytest.approx(full["k_coinbase"].iloc[-1])


def test_journal_rows_equity_and_drawdown():
    idx = pd.date_range("2026-09-25", periods=4, freq="D", tz="UTC")
    hist = pd.DataFrame(
        {"ret": [0.10, -0.20, 0.05, 0.0], "k_trend": 1.0, "k_coinbase": 0.5}, index=idx
    )
    rets = pd.DataFrame({"trend": 0.0, "coinbase": 0.0}, index=idx)
    out = lj.journal_rows(hist, rets, start=idx[0])
    assert out["equity"].to_numpy() == pytest.approx([1.10, 0.88, 0.924, 0.924])
    assert out["drawdown"].to_numpy() == pytest.approx(
        [0.0, 0.20, 1 - 0.924 / 1.1, 1 - 0.924 / 1.1]
    )


def test_append_is_idempotent_and_flags_changed_history(tmp_path):
    path = tmp_path / "wyniki.csv"
    a = pd.DataFrame({"date": ["2026-09-25", "2026-09-26"], "r_port": [0.01, -0.02]})
    assert lj.append_rows(path, a, ["date"], ["r_port"]) == (2, [])
    assert lj.append_rows(path, a, ["date"], ["r_port"]) == (0, [])
    b = pd.DataFrame({"date": ["2026-09-26", "2026-09-27"], "r_port": [-0.03, 0.04]})
    n, changed = lj.append_rows(path, b, ["date"], ["r_port"])
    assert n == 1 and changed == ["2026-09-26:r_port"]
    saved = pd.read_csv(path)
    assert saved["r_port"].tolist() == [0.01, -0.02, 0.04]  # stary zapis NIE nadpisany


def test_stop_status_thresholds():
    assert lj.stop_status(0.0) == "OK"
    assert lj.stop_status(lj.WARN_DD - 1e-6) == "OK"
    assert lj.stop_status(lj.WARN_DD) == "OSTRZEŻENIE"
    assert lj.stop_status(lj.STOP_DD) == "STOP"
    assert lj.WARN_DD < lj.STOP_DD


def test_run_writes_journal_and_log(tmp_path, live, monkeypatch):
    src = tmp_path / "live"
    src.mkdir()
    _write_live(src)
    jdir = tmp_path / "dziennik"
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert "DZIENNIK" in text and "mnożniki R1" in text
    first = pd.read_csv(jdir / "wyniki.csv")
    text2 = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert "HISTORIA ZMIENIONA" not in text2
    assert len(pd.read_csv(jdir / "wyniki.csv")) == len(first)
    assert len((jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()) == 2
    # poprawka 7: etykieta stanu rynku dopisywana raz na dzień, bez zmian przy powtórce
    st = pd.read_csv(jdir / "stan_rynku.csv")
    assert list(st.columns) == ["date", "btc_vol30", "vol_stan", "btc_r90", "trend90"]
    assert len(st) > 0 and st["date"].is_unique
    assert "stan rynku +" in (jdir / "przebiegi.log").read_text(encoding="utf-8")
    # poprawka 8: etykieta Fear & Greed w osobnym pliku od JOURNAL_START, bez zmian przy powtórce
    fg = pd.read_csv(jdir / "fng.csv")
    assert list(fg.columns) == ["date", "fng", "fng_etykieta"]
    assert fg["date"].is_unique and fg["date"].min() == "2026-08-01"
    assert fg["fng"].between(0, 100).all() and set(fg["fng_etykieta"]) <= {"Fear", "Greed"}
    log_lines = (jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()
    assert f"F&G +{len(fg)} |" in log_lines[0] and "F&G +0 |" in log_lines[1]
    assert "Fear & Greed (poprawka 8, tylko zapis): 2026-09-" in text2 and "dopisane +0" in text2


def test_fng_rows_filters_start_future_and_duplicates():
    days = pd.date_range("2026-09-20", periods=8, freq="D", tz="UTC")
    fng = pd.DataFrame(
        {
            "date": list(days) + [days[3]],
            "value": [10.0, 30.4, 50.6, 70, 80, 90, 95, 99, 30.4],
            "label": ["Extreme Fear", "Fear", "Greed", "Greed"] + ["Extreme Greed"] * 4 + ["Fear"],
        }
    )
    out = lj.fng_rows(fng, start=days[2], now=days[5])
    assert list(out.columns) == ["date", "fng", "fng_etykieta"]
    assert out["date"].tolist() == [d.strftime("%Y-%m-%d") for d in days[2:6]]
    assert out["fng"].tolist() == [51, 70, 80, 90]  # do całości; dni po `now` odrzucone
    assert out["fng_etykieta"].tolist() == ["Greed", "Greed", "Extreme Greed", "Extreme Greed"]


def test_fng_rows_rejects_unknown_label():
    days = pd.date_range("2026-09-24", periods=2, freq="D", tz="UTC")
    bad = pd.DataFrame({"date": days, "value": [50.0, 51.0], "label": ["Neutral", "=1+1"]})
    with pytest.raises(ValueError, match="nieznana klasa"):
        lj.fng_rows(bad, start=days[0], now=days[-1])
    ok = bad.assign(label=["Neutral", "Extreme Greed"])
    assert lj.fng_rows(ok, start=days[0], now=days[-1])["fng_etykieta"].tolist() == [
        "Neutral",
        "Extreme Greed",
    ]


def test_fng_append_backfills_missing_days_and_flags_revision(tmp_path):
    days = pd.date_range("2026-09-24", periods=6, freq="D", tz="UTC")
    full = pd.DataFrame({"date": days, "value": [20.0, 25, 30, 35, 40, 45], "label": "Fear"})
    path, start, now = tmp_path / "fng.csv", days[0], days[-1]
    cols = ["fng", "fng_etykieta"]
    assert lj.append_rows(path, lj.fng_rows(full.iloc[:3], start, now), ["date"], cols) == (3, [])
    # przerwa 3 dni (awaria źródła) → następny udany przebieg dopisuje brakujące dni z historii
    assert lj.append_rows(path, lj.fng_rows(full, start, now), ["date"], cols) == (3, [])
    revised = full.copy()
    revised.loc[1, "value"] = 99.0  # rewizja opublikowanej wartości → „historia zmieniona”
    n, changed = lj.append_rows(path, lj.fng_rows(revised, start, now), ["date"], cols)
    assert n == 0 and changed == ["2026-09-25:fng"]
    assert pd.read_csv(path)["fng"].tolist() == [20, 25, 30, 35, 40, 45]  # stary zapis zostaje


def test_run_without_fng_file_keeps_journal(tmp_path, monkeypatch):
    src = tmp_path / "live"
    src.mkdir()
    _write_live(src)
    (src / lj.FNG_FILE).unlink()
    jdir = tmp_path / "dziennik"
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert (jdir / "wyniki.csv").exists() and not (jdir / "fng.csv").exists()
    assert "| F&G brak pliku |" in (jdir / "przebiegi.log").read_text(encoding="utf-8")
    assert "Fear & Greed (poprawka 8, tylko zapis): brak pliku" in text


def test_fetch_fng_safe_swallows_errors(tmp_path, monkeypatch):
    import data.fetch_external as fe
    from data.fetch_live import fetch_fng_safe

    def boom(out_dir, force=False):
        raise ConnectionError("sieć")

    monkeypatch.setattr(fe, "fetch_fng", boom)
    assert fetch_fng_safe(tmp_path) is None
    monkeypatch.setattr(fe, "fetch_fng", lambda out_dir, force=False: tmp_path / "x.parquet")
    assert fetch_fng_safe(tmp_path) == tmp_path / "x.parquet"


def test_parse_klines_keeps_high_low_and_drops_open_candle():
    day = 86_400_000
    rows = [
        [0, "1", "2", "0.5", "1.5", "0", 0, "100"],
        [day, "1.5", "3", "1", "2", "0", 0, "200"],
    ]
    df = parse_klines_1d(rows, end_ms=day + day // 2)  # druga świeca jeszcze otwarta
    assert len(df) == 1
    assert df.iloc[0][["open", "high", "low", "close", "quote_volume"]].tolist() == [
        1,
        2,
        0.5,
        1.5,
        100,
    ]
    assert parse_klines_1d([], end_ms=day).empty


def test_active_usdt_perpetuals_filters():
    info = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "contractType": "PERPETUAL",
                "status": "TRADING",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "USDCUSDT",
                "contractType": "PERPETUAL",
                "status": "TRADING",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "ETHUSDT",
                "contractType": "PERPETUAL",
                "status": "SETTLING",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "TSLAUSDT",
                "contractType": "TRADIFI_PERPETUAL",
                "status": "TRADING",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "BTCUSDT_261225",
                "contractType": "CURRENT_QUARTER",
                "status": "TRADING",
                "quoteAsset": "USDT",
            },
            {
                "symbol": "SOLUSDC",
                "contractType": "PERPETUAL",
                "status": "TRADING",
                "quoteAsset": "USDC",
            },
        ]
    }
    assert active_usdt_perpetuals(info) == ["BTCUSDT"]


def test_symbol_names_are_safe_for_file_paths():
    """Przegląd bezpieczeństwa: nazwa symbolu z odpowiedzi giełdy trafia do nazwy pliku."""
    base = {"contractType": "PERPETUAL", "status": "TRADING", "quoteAsset": "USDT"}
    info = {
        "symbols": [
            {**base, "symbol": s}
            for s in (
                "1000PEPEUSDT",
                "币安人生USDT",
                "../universe/BTCUSDT",
                "C:/x/aUSDT",
                "btcUSDT",
                "A-BUSDT",
                "币/安USDT",
                "币.USDT",
                "币\u202eUSDT",
                "\uff21\uff0fBUSDT",
                "A_BUSDT",
            )
        ]
    }
    assert active_usdt_perpetuals(info) == ["1000PEPEUSDT", "币安人生USDT"]


def test_engine_start_is_shared():
    from data import fetch_live

    assert fetch_live.ENGINE_START == lj.ENGINE_START


def test_coinbase_file_is_not_a_symbol(live, tmp_path):
    """`coinbase_BTC-USD_1d.parquet` leży obok świec perpetuali — nie może stać się „monetą”."""
    from data.fetch_live import funding_symbols, symbol_files

    assert "coinbase_BTC-USD" not in live["close"].columns
    src = tmp_path / "live2"
    src.mkdir()
    _write_live(src)
    assert "coinbase_BTC-USD" not in symbol_files(src)
    need = funding_symbols(src, pd.Timestamp("2026-09-20", tz="UTC"))
    assert "BTCUSDT" in need and len(need) >= 20


# ------------------------------------------------------------------ X1 (poprawka 3)
def _x1(data, as_of):
    d = lj.truncate(data, as_of)
    members = lj.monthly_members(d["volume"], lj._months(as_of))
    r, pos = lj.x1_component(
        d["close"], d["funding"], members, as_of, as_of + pd.Timedelta(days=1), FEE
    )
    return r, pos, d, members


def test_x1_series_is_mean_of_seven_phase_engines(live):
    """Zwrot X1 = średnia 7 przebiegów `long_short_returns` (fazy od ENGINE_START + 0…6 dni)."""
    from backtest.xs_momentum import long_short_returns

    as_of = live["close"].index[-1]
    r, _, d, members = _x1(live, as_of)
    end = as_of + pd.Timedelta(days=1)
    per = [
        long_short_returns(
            d["close"],
            d["funding"],
            members,
            formation_dates(d["close"].index, lj.ENGINE_START, end, ph),
            FEE,
        ).set_index("date")["r_net"]
        for ph in range(PHASES)
    ]
    first = max(s.first_valid_index() for s in per)
    manual = pd.concat(per, axis=1).loc[first:].mean(axis=1)
    pd.testing.assert_series_equal(r, manual, check_names=False)
    assert r.index[0] == lj.ENGINE_START + pd.Timedelta(days=PHASES)


def test_x1_positions_legs_weights_and_signal(live):
    """Każda faza: 5 long + 5 short po ±0,5/5/7; long mają wyższy zwrot 28 dni niż short; faza dnia oznaczona."""
    from backtest.xs_momentum import signal_panel

    t = _formation_day(live, phase=2)
    _, pos, d, _ = _x1(live, t)
    assert sorted(pos["phase"].unique()) == list(range(PHASES))
    for _ph, g in pos.groupby("phase"):
        assert (g["sign"] > 0).sum() == 5 and (g["sign"] < 0).sum() == 5
        assert g["weight"].to_numpy() == pytest.approx(g["sign"].to_numpy() * 0.5 / 5 / PHASES)
        sig = signal_panel(d["close"]).loc[pd.Timestamp(g["formed"].iloc[0], tz="UTC")]
        assert sig[g[g["sign"] > 0]["symbol"]].min() >= sig[g[g["sign"] < 0]["symbol"]].max()
    today = pos[pos["today"]]
    assert today["phase"].unique().tolist() == [2]
    assert pos["weight"].abs().sum() == pytest.approx(1.0)


def test_x1_no_lookahead(live):
    """Dopisanie dni po `as_of` nie zmienia ani zwrotów X1 do `as_of`, ani ogłoszonych nóg."""
    t = _formation_day(live)
    r_a, pos_a, _, _ = _x1(lj.truncate(live, t), t)
    r_b, pos_b, _, _ = _x1(live, t)
    pd.testing.assert_series_equal(r_a, r_b)
    pd.testing.assert_frame_equal(pos_a, pos_b)


def test_x1_rows_and_thresholds():
    idx = pd.date_range("2026-09-24", periods=4, freq="D", tz="UTC")
    r = pd.Series([0.5, 0.10, -0.20, 0.05], index=idx)
    out = lj.x1_rows(r)  # domyślny start = X1_START (25.09) — 24.09 pominięty
    assert out["date"].tolist() == ["2026-09-25", "2026-09-26", "2026-09-27"]
    assert out["equity"].to_numpy() == pytest.approx([1.10, 0.88, 0.924])
    assert lj.x1_rows(r.iloc[:1]).empty
    assert lj.X1_STOP_DD == pytest.approx(1.5 * lj.X1_WARN_DD)
    assert lj.stop_status(0.60, lj.X1_WARN_DD, lj.X1_STOP_DD) == "OSTRZEŻENIE"
    assert lj.stop_status(0.60) == "STOP"  # progi R1 bez zmian


def test_run_writes_x1_journal_separately(tmp_path, monkeypatch):
    src = tmp_path / "live"
    src.mkdir()
    _write_live(src)
    jdir = tmp_path / "dziennik"
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))
    monkeypatch.setattr(lj, "X1_START", pd.Timestamp("2026-08-01", tz="UTC"))
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert "X1 (papierowo" in text
    main = pd.read_csv(jdir / "wyniki.csv")
    x1 = pd.read_csv(jdir / "x1_wyniki.csv")
    assert len(x1) == len(main) and "r_x1" in x1.columns and "r_x1" not in main.columns
    sig = pd.read_csv(jdir / "x1_sygnaly.csv")
    assert set(sig.columns) == {"as_of", "phase", "formed", "today", "symbol", "sign", "weight"}
    text2 = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert "HISTORIA ZMIENIONA" not in text2
    assert len(pd.read_csv(jdir / "x1_wyniki.csv")) == len(x1)
    assert "X1 sygnały +0 wyniki +0" in (jdir / "przebiegi.log").read_text(encoding="utf-8")


def test_x1_error_does_not_stop_main_journal(tmp_path, monkeypatch):
    """Błąd w X1 → wpis w logu i wydruku; dziennik główny zapisany normalnie."""
    src = tmp_path / "live"
    src.mkdir()
    _write_live(src)
    jdir = tmp_path / "dziennik"
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))

    def boom(*a, **k):
        raise ValueError("test")

    monkeypatch.setattr(lj, "x1_component", boom)
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert "X1: BŁĄD ValueError: test" in text and "mnożniki R1" in text
    assert len(pd.read_csv(jdir / "wyniki.csv")) > 0
    assert not (jdir / "x1_wyniki.csv").exists()
    assert "BŁĄD ValueError" in (jdir / "przebiegi.log").read_text(encoding="utf-8")


def _btc(n=260, seed=7):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2026-01-01", periods=n, freq="D", tz="UTC")
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.03, n))), index=days)


@pytest.mark.parametrize("cut", [150, 230])
def test_market_state_no_lookahead(cut):
    """Poprawka 7: etykieta dnia d nie zmienia się po obcięciu zamknięć po d."""
    c = _btc()
    start = c.index[100]
    full = lj.market_state(c, start).set_index("date")
    d = c.index[cut]
    part = lj.market_state(c[c.index <= d], start).set_index("date")
    pd.testing.assert_frame_equal(full.loc[: d.strftime("%Y-%m-%d")], part)


def test_market_state_thresholds_and_start():
    c = _btc()
    st = lj.market_state(c, c.index[120])
    assert st["date"].min() == c.index[120].strftime("%Y-%m-%d")
    lo, hi = lj.VOL_TERCILES
    expect = np.where(
        st["btc_vol30"] < lo, "niska", np.where(st["btc_vol30"] < hi, "srednia", "wysoka")
    )
    assert (st["vol_stan"] == expect).all()
    assert set(st["trend90"]) <= {-1, 0, 1}
    assert (np.sign(st["btc_r90"]) == st["trend90"]).all()


# ------------------------------------------------------------------ poprawka 9: lista transakcji


def test_phase_lots_liquidation_and_engine_identity():
    """Ręczny przykład: long z krachem (likwidacja 2×), short z rotacją; Σ |w|·zwrot = P&L fazy silnika."""
    idx = pd.date_range("2026-01-01", periods=20, freq="D", tz="UTC")
    close = pd.DataFrame({"A": 100.0, "B": 100.0}, index=idx)
    close.loc[idx[3:], "B"] = [
        101,
        103,
        104,
        106,
        108,
        110,
        111,
        112,
        113,
        112,
        111,
        110,
        109,
        108,
        107,
        106,
        105,
    ]
    close.loc[idx[4:], "A"] = 80.0
    low, high = close * 0.99, close * 1.01
    low.loc[idx[5], "A"] = 45.0  # minimum 45 % ceny wejścia → likwidacja przy 2× (próg 51 %)
    w1 = np.array([0.1, -0.2])
    forms = [(2, w1), (9, np.array([0.0, -0.1])), (16, np.array([0.05, 0.0]))]
    lots = lj.phase_lots(close, low, high, forms, idx[19], lj.LEV_TREND)
    a, b = lots[0], lots[1]
    assert a["status"] == "likwidacja" and a["exit_pos"] == 5
    assert a["exit_price"] == pytest.approx(100.0 * (1 - (0.5 - 0.01))) and a["ret"] == -0.5
    assert b["status"] == "rotacja" and b["exit_pos"] == 9
    assert b["ret"] == pytest.approx(-(close["B"].iat[9] / 100.0 - 1.0))
    assert lots[-1]["status"] == "otwarta" and lots[-1]["t_pos"] == 16  # formowanie z 16 trwa
    rets = close.pct_change().to_numpy()
    lo_rel = (low / close.shift(1)).to_numpy()
    hi_rel = (high / close.shift(1)).to_numpy()
    eng = phase_returns_liq(
        rets, np.zeros_like(rets), idx, forms, 0.0, lo_rel, hi_rel, lj.LEV_TREND, lj.MMR
    ).set_index("date")
    week = eng.loc[(eng.index > idx[2]) & (eng.index <= idx[9]), "gross"]
    assert np.prod(1 + week) - 1 == pytest.approx(0.1 * a["ret"] + 0.2 * b["ret"], abs=1e-12)
    assert eng.loc[idx[5], "liquidations"] == 1


def _ledger(live, as_of, monkeypatch, start="2026-06-01"):
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp(start, tz="UTC"))
    monkeypatch.setattr(lj, "X1_START", pd.Timestamp(start, tz="UTC"))
    pos, k, hist, _ = lj.positions(live, as_of, FEE)
    closed, opened = lj.trade_ledger(live, as_of, hist, k)
    return pos, k, closed, opened


def test_ledger_trend_matches_engine_phase_pnl(live, monkeypatch):
    """Każde zamknięte formowanie fazy trendu: Π(1 + gross silnika) − 1 = Σ |waga·7| · zwrot pozycji."""
    as_of = live["close"].index[-2]
    _, _, closed, _ = _ledger(live, as_of, monkeypatch)
    d = lj.truncate(live, as_of)
    members = lj.monthly_members(d["volume"], lj._months(as_of))
    liq = {"high": d["high"], "low": d["low"], "lev": lj.LEV_TREND, "mmr": lj.MMR}
    end = as_of + pd.Timedelta(days=1)
    _, per_phase = portfolio(d["close"], d["funding"], members, lj.ENGINE_START, end, FEE, liq=liq)
    tr = closed[closed["skladowa"] == "trend"]
    assert len(tr) > 100 and set(tr["powod_wyjscia"]) <= {"rotacja", "likwidacja"}
    checked = 0
    for (ph, formed), g in tr.groupby(["faza", "data_wejscia"]):
        f0 = pd.Timestamp(formed, tz="UTC")
        eng = per_phase[ph]
        gross = eng.loc[(eng.index > f0) & (eng.index <= f0 + pd.Timedelta(days=7)), "gross"]
        lots = (g["waga"].abs() * PHASES * g["zwrot_pozycji_proc"] / 100).sum()
        assert np.prod(1 + gross) - 1 == pytest.approx(lots, abs=1e-9)
        checked += 1
    assert checked >= 10


def test_ledger_open_lots_match_published_positions(live, monkeypatch):
    """Otwarte pozycje trendu/premii/X1 = pozycje ogłaszane w sygnaly.csv / x1_sygnaly.csv (poza likwidacjami)."""
    as_of = live["close"].index[-2]
    pos, _, closed, opened = _ledger(live, as_of, monkeypatch)
    comp = {"trend": "trend", "coinbase": "premia_coinbase"}
    want = {
        (comp[r.component], r.phase, r.formed, r.symbol, r.sign, round(r.weight, 12))
        for r in pos.itertuples()
    }
    liq_now = {
        (r.skladowa, r.faza, r.data_wejscia, r.symbol)
        for r in closed.itertuples()
        if r.powod_wyjscia == "likwidacja" and r.data_wejscia >= min(p[2] for p in want)
    }
    got = {
        (
            r.skladowa,
            r.faza,
            r.data_wejscia,
            r.symbol,
            1 if r.kierunek == "long" else -1,
            round(r.waga, 12),
        )
        for r in opened.itertuples()
        if r.skladowa != "x1"
    }
    assert got == {w for w in want if w[:4] not in liq_now}
    d = lj.truncate(live, as_of)
    _, pos_x1 = lj.x1_component(
        d["close"],
        d["funding"],
        lj.monthly_members(d["volume"], lj._months(as_of)),
        as_of,
        as_of + pd.Timedelta(days=1),
        FEE,
    )
    want_x1 = {
        (r.phase, r.formed, r.symbol, r.sign, round(r.weight, 12)) for r in pos_x1.itertuples()
    }
    got_x1 = {
        (r.faza, r.data_wejscia, r.symbol, 1 if r.kierunek == "long" else -1, round(r.waga, 12))
        for r in opened.itertuples()
        if r.skladowa == "x1"
    }
    assert got_x1 == want_x1 and len(got_x1) == 70  # 7 faz × (5 long + 5 short)


def test_ledger_closed_history_is_stable(live, monkeypatch):
    """Transakcje zamknięte do dnia t mają te same liczby, gdy liczyć je dzień później (append-only)."""
    idx = live["close"].index
    _, _, c1, _ = _ledger(live, idx[-9], monkeypatch)
    _, _, c2, _ = _ledger(live, idx[-2], monkeypatch)
    m = c1.merge(c2, on=lj.TRADE_KEY, suffixes=("_a", "_b"), validate="one_to_one")
    assert len(m) == len(c1) > 0
    for c in ("cena_wejscia", "cena_wyjscia", "wielkosc_proc_kapitalu", "zwrot_pozycji_proc"):
        assert np.allclose(m[f"{c}_a"], m[f"{c}_b"], rtol=0, atol=1e-12)
    assert (m["data_wyjscia_a"] == m["data_wyjscia_b"]).all()


def test_run_writes_trade_files(tmp_path, monkeypatch):
    src = tmp_path / "live"
    src.mkdir()
    _write_live(src)
    jdir = tmp_path / "dziennik"
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))
    monkeypatch.setattr(lj, "X1_START", pd.Timestamp("2026-08-01", tz="UTC"))
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    closed = pd.read_csv(jdir / "transakcje.csv")
    opened = pd.read_csv(jdir / "transakcje_otwarte.csv")
    assert list(closed.columns) == lj.TRADE_CLOSED_COLS and len(closed) > 0
    assert list(opened.columns) == lj.TRADE_OPEN_COLS and opened["as_of"].nunique() == 1
    assert set(closed["skladowa"]) == {"trend", "premia_coinbase", "x1"}
    assert (closed["data_wyjscia"] >= "2026-08-01").all()
    assert "Transakcje (poprawka 9): zamknięte dopisane +" in text
    text2 = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    assert len(pd.read_csv(jdir / "transakcje.csv")) == len(closed)
    assert "HISTORIA ZMIENIONA" not in text2
    log = (jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()
    assert f"transakcje +{len(closed)} |" in log[0] and "transakcje +0 |" in log[1]


# ------------------------------------------------------------------ poprawka 10: opisy strategii
def test_every_journal_component_has_description(live, monkeypatch):
    from backtest import journal_strategies as js

    book = {s["id"]: s for s in lj.strategy_book()}
    assert set(book) == {"trend", "coinbase", "portfel_r1", "x1"}
    for s in book.values():
        assert s["nazwa"] and s["opis"] and s["status"] and len(s["zalozenia"]) >= 4
    as_of = live["close"].index[-2]
    pos, _, closed, opened = _ledger(live, as_of, monkeypatch)
    assert set(pos["component"]) <= set(book)  # składowe z sygnaly.csv
    names = set(closed["skladowa"]) | set(opened["skladowa"])
    assert names == set(js.LEDGER_TO_ID) and {js.LEDGER_TO_ID[n] for n in names} <= set(book)


def test_descriptions_follow_engine_constants(monkeypatch):
    import backtest.run_coinbase_cp1 as cp
    import backtest.ts_momentum as tsm

    monkeypatch.setattr(tsm, "LOOKBACK_DAYS", 99)
    monkeypatch.setattr(cp, "SHORT", 5)
    book = {s["id"]: s for s in lj.strategy_book()}
    assert "ostatnich 99 dni" in book["trend"]["opis"]
    assert any("średnia premii z 5 dni" in z for z in book["coinbase"]["zalozenia"])


def test_strategie_md_is_current():
    from pathlib import Path

    from backtest.journal_strategies import render_markdown

    doc = Path(__file__).resolve().parents[1] / "dziennik" / "STRATEGIE.md"
    assert doc.read_text(encoding="utf-8") == render_markdown(
        lj.strategy_book()
    ), "dziennik/STRATEGIE.md nieaktualny — uruchom: py -m backtest.journal_strategies > dziennik/STRATEGIE.md"


def test_run_writes_strategy_descriptions(tmp_path, monkeypatch):
    from backtest.journal_strategies import CSV_COLS

    src = tmp_path / "live"
    src.mkdir()
    _write_live(src)
    jdir = tmp_path / "dziennik"
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    st = pd.read_csv(jdir / "strategie.csv")
    assert list(st.columns) == CSV_COLS and set(st["id"]) == {
        "trend",
        "coinbase",
        "portfel_r1",
        "x1",
    }
    assert "STRATEGIE AKTYWNE" in text and all(
        f"{k} — " in text for k in ("TS1", "CP1", "R1", "X1")
    )
    assert "| opisy strategii 4 |" in (jdir / "przebiegi.log").read_text(encoding="utf-8")
