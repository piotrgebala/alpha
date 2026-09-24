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
            for s in ("1000PEPEUSDT", "../universe/BTCUSDT", "C:/x/aUSDT", "btcUSDT", "A-BUSDT")
        ]
    }
    assert active_usdt_perpetuals(info) == ["1000PEPEUSDT"]


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
