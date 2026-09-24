"""Testy dziennika na żywo (`backtest/live_journal.py`, `data/fetch_live.py`) — bez sieci, na danych
syntetycznych z `backtest/negative_control.py`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import live_journal as lj
from backtest.negative_control import synthetic_ohlc, synthetic_returns
from backtest.sizing import apply_rules
from backtest.ts_momentum import PHASES, formation_dates, portfolio, signal_sign
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
