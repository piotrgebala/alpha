"""Testy pomocników backtest/run_crowding_tf1.py (runda TF1): suma fundingu i filtr tłoku."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import run_crowding_tf1 as tf


def test_funding_sum_trailing_window_no_future():
    idx = pd.date_range("2021-01-01", periods=10, freq="D", tz="UTC")
    f = pd.DataFrame({"A": np.arange(10, dtype=float)}, index=idx)
    s = tf.funding_sum(f, 3)
    assert np.isnan(s["A"].iloc[1])
    assert s["A"].iloc[5] == 3 + 4 + 5


def test_keep_fn_filters_only_crowded_side():
    idx = pd.date_range("2021-01-01", periods=3, freq="D", tz="UTC")
    fsum = pd.DataFrame({"A": 0.01, "B": 0.01, "C": -0.01, "D": 0.0}, index=idx)
    keep = tf.make_keep_fn(fsum, f_hi=0.0063)
    out = keep(idx[2], ["A", "B", "C", "D"], np.array([1.0, -1.0, -1.0, 1.0]))
    # A: long przy dodatnim tłoku → 0; B: short przy dodatnim → zostaje; C: short przy ujemnym → 0
    assert list(out) == [0.0, 1.0, 0.0, 1.0]
