"""
test_engine.py

Warstwa 4 (integracyjne) testy dla backtest/engine.py — cały pipeline: cechy ->
labels -> regime split -> walk-forward -> trening+predykcja -> sizing -> koszty ->
equity curve. Nie testuje jakości modelu (to Commit 6 / realne dane) — sprawdza,
że pipeline wykonuje się end-to-end na danych syntetycznych i produkuje poprawnie
ustrukturyzowany wynik.

`_make_pipeline_test_ohlcv` konstruuje dane z jawnie odseparowanymi segmentami ATR/
kierunku (ambiguous warmup -> trend -> range), żeby DETERMINISTYCZNIE (dla ustalonego
seeda) wywołać OBA reżimy classify_regime — czysto losowe dane (i.i.d.) dają reżim
"range" dużo częściej niż "trend" (ryzyko odnotowane w TASKS.md C2.5), więc nie
gwarantowałyby ćwiczenia obu ścieżek.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.engine import TRADE_COLUMNS, run_backtest

N_WARMUP = 5760  # 20 dni @ 5m - wymagane, by atr_pctrank_20d (feature_miner.py) nie było NaN
N_TREND = 2880  # 10 dni - segment o wysokim, trwałym ATR + konsekwentny kierunek -> regime="trend"
N_RANGE = 2880  # 10 dni - segment o niskim ATR + losowym kierunku -> regime="range"


def _make_pipeline_test_ohlcv(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[tuple[float, float, float, float]] = []
    price = 100.0

    # Warmup: umiarkowany losowy ruch — punkt odniesienia ATR, klasyfikowany "ambiguous".
    # std=0.15 (nie 1.0) świadomie mały — kumulatywne odchylenie po 5760 krokach
    # (~11 przy std=0.15) musi zostać dużo mniejsze niż price=100 startowe, żeby cena
    # nigdy nie spadła <= 0 (co dałoby invalid log w return_lag_1/momentum_5).
    for _ in range(N_WARMUP):
        step = rng.normal(0.0, 0.15)
        o, c = price, price + step
        h, l = max(o, c) + 0.5, min(o, c) - 0.5
        rows.append((o, h, l, c))
        price = c

    # Trend: silny konsekwentny dryf w górę + wysoki true range -> wysoki atr_pctrank_20d
    # ORAZ wysoki direction_persistence_10 -> regime="trend".
    for _ in range(N_TREND):
        o = price
        c = price + rng.uniform(3.0, 4.0)
        h, l = c + 1.0, o - 1.0
        rows.append((o, h, l, c))
        price = c

    # Range: mały szum wokół stałego poziomu -> niski atr_pctrank_20d oraz niski
    # direction_persistence_10 (losowy znak zwrotu) -> regime="range".
    range_level = price
    for _ in range(N_RANGE):
        o = range_level + rng.normal(0.0, 0.15)
        c = range_level + rng.normal(0.0, 0.15)
        h, l = max(o, c) + 0.05, min(o, c) - 0.05
        rows.append((o, h, l, c))

    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df["volume"] = rng.uniform(50.0, 150.0, size=len(df))
    df["timestamp"] = pd.date_range("2026-01-01", periods=len(df), freq="5min", tz="UTC")
    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def test_run_backtest_produces_trades_for_both_regimes() -> None:
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)

    result = run_backtest(
        raw_ohlcv,
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
    )

    folds_summary = result["folds_summary"]
    regimes_with_signals = {
        f["regime"] for f in folds_summary if not f["skipped"] and f["n_signals"] > 0
    }
    assert "trend" in regimes_with_signals
    assert "range" in regimes_with_signals

    trades = result["trades"]
    assert list(trades.columns) == TRADE_COLUMNS
    assert len(trades) > 0
    assert (trades["position_size"] > 0).all()
    assert (trades["cost"] >= 0).all()
    assert set(trades["signal_direction"].unique()).issubset({-1.0, 1.0})

    equity_curve = result["equity_curve"]
    assert list(equity_curve.columns) == ["timestamp", "equity"]
    assert equity_curve["timestamp"].is_monotonic_increasing
    assert equity_curve["equity"].iloc[0] == 10_000.0
    assert result["final_equity"] == equity_curve["equity"].iloc[-1]


def test_run_backtest_empty_regime_has_correct_schema() -> None:
    # Dataset krótszy niż okno rolling atr_pctrank_20d (5760 świec) -> regime
    # zawsze "ambiguous" -> ZERO sygnałów w obu reżimach, ale bez crasha.
    rng = np.random.default_rng(1)
    n = 500
    close = 100.0 + np.cumsum(rng.normal(0.0, 0.5, size=n))
    open_ = np.roll(close, 1)
    open_[0] = 100.0
    high = np.maximum(open_, close) + 0.3
    low = np.minimum(open_, close) - 0.3
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(50.0, 150.0, size=n),
        }
    )

    result = run_backtest(df, train_days=1, test_days=1, step_days=1)

    assert list(result["trades"].columns) == TRADE_COLUMNS
    assert len(result["trades"]) == 0
    assert len(result["equity_curve"]) == 1
    assert result["final_equity"] == 10_000.0
    assert all(f["skipped"] for f in result["folds_summary"])
