"""Testy backtest/run_kr2_tradfi.py (KR2): zmiana tygodniowa (zwrot vs różnica poziomu)."""

from __future__ import annotations

import pandas as pd
import pytest

from backtest import run_kr2_tradfi as kr2


def test_weekly_change_ret_and_diff_use_friday_close():
    days = pd.date_range("2024-01-01", "2024-01-19", freq="D", tz="UTC")  # pn 1.01 … pt 19.01
    level = pd.Series(range(100, 100 + len(days)), index=days, dtype=float)
    ret = kr2.weekly_change(level, "ret")
    diff = kr2.weekly_change(level, "diff")
    # piątki: 5.01 (104), 12.01 (111), 19.01 (118)
    assert diff.tolist() == [7.0, 7.0]
    assert ret.iloc[0] == pytest.approx(111 / 104 - 1)
