"""Testy pomocników backtest/run_horizon_y.py (serie Y1/Y2): ATR/close i rachunek ex ante."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_horizon_y as ry


def _ohlc(n: int, step: float = 0.01) -> pd.DataFrame:
    """Cena stała 100, każda świeca high = 101, low = 99 → TR = 2, ATR/close = 0,02."""
    ts = pd.date_range("2021-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(
        {"timestamp": ts, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0}
    )


def test_atr_fraction_constant_range():
    df = _ohlc(40)
    atr = ry._atr_fraction(df)
    assert atr.iloc[: ry.ATR_WINDOW].isna().all() or np.isnan(atr.iloc[0])
    assert atr.iloc[-1] == pytest.approx(0.02)


def test_ex_ante_uses_barrier_from_atr_and_reports_measurability():
    df = _ohlc(24 * 400)  # 400 dni 1h
    ea = ry._ex_ante("1h", df, ry.HORIZONS["1h"])
    assert ea["barrier"] == pytest.approx(1.5 * 0.02)
    assert ea["be"] == pytest.approx(0.5 * (1 + ry.COST_REF / (1.5 * 0.02)))
    assert ea["n_oos"] == 24 * 400 - 60 * 24
    assert ea["n_exp"] == pytest.approx(ea["n_oos"] * (1 - ry.ABSTENTION_REF) * ry.FILL_RATE_REF)
    assert "verdict" in ea["report"] or isinstance(ea["report"], dict)


def test_horizons_config_is_internally_consistent():
    for tf, cfg in ry.HORIZONS.items():
        assert cfg["candles_per_day"] * cfg["candle_minutes"] == 24 * 60, tf
        assert cfg["train_days"] > cfg["test_days"] >= cfg["step_days"] > 0
