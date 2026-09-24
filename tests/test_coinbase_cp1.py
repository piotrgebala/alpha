"""Testy pomocników backtest/run_coinbase_cp1.py (runda CP1): premia i sygnał bez przyszłości."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_coinbase_cp1 as cp


def _data(n=120):
    days = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    cb = pd.DataFrame({"open_time": days, "close": 101.0})
    t8 = pd.date_range("2021-01-01", periods=3 * n, freq="8h", tz="UTC")
    spot = pd.DataFrame({"timestamp": t8, "close": np.where(t8.hour == 16, 100.0, 50.0)})
    return cb, spot


def test_daily_premium_uses_16h_candle_close():
    cb, spot = _data()
    prem = cp.daily_premium(cb, spot)
    assert len(prem) == 120
    assert prem.iloc[0] == pytest.approx(0.01)


@pytest.mark.parametrize("cut", [95, 110])
def test_premium_signal_no_lookahead(cut):
    rng = np.random.default_rng(0)
    prem = pd.Series(
        rng.normal(0, 0.001, 150),
        index=pd.date_range("2021-01-01", periods=150, freq="D", tz="UTC"),
    )
    full = cp.premium_signal(prem)
    part = cp.premium_signal(prem.iloc[: cut + 1])
    assert full.iloc[cut] == part.iloc[cut]
    assert full.iloc[: cp.LONG - 1].isna().all()
