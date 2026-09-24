"""Testy pomocników backtest/run_crowding_tl1.py (TL1) i data/fetch_oi_panel.py — bez sieci."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_crowding_tl1 as tl
from data import fetch_oi_panel as fo


def _close_oi(n=30):
    idx = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")
    close = pd.DataFrame({"A": np.linspace(100, 130, n), "B": np.linspace(100, 70, n)}, index=idx)
    rows = []
    for i, d in enumerate(idx):
        rows.append({"symbol": "A", "date": d, "oi": 1000 * 1.05**i})
        rows.append({"symbol": "B", "date": d, "oi": 1000.0})
    return close, pd.DataFrame(rows)


def test_crowd_panel_sign_and_no_future():
    close, oi = _close_oi()
    c = tl.crowd_panel(oi, close, 7)
    t = close.index[20]
    assert c.loc[t, "A"] == pytest.approx(7 * np.log(1.05))  # OI rośnie, cena rośnie → +
    assert c.loc[t, "B"] == pytest.approx(0.0)
    c_cut = tl.crowd_panel(oi[oi["date"] <= t], close.loc[:t], 7)
    assert c_cut.loc[t, "A"] == pytest.approx(c.loc[t, "A"])


def test_legs_long_lowest_short_highest():
    idx = pd.date_range("2022-01-01", periods=1, freq="D", tz="UTC")
    crowd = pd.DataFrame([[0.5, -0.3, 0.1, 0.9]], index=idx, columns=["A", "B", "C", "D"])
    legs = tl.make_legs_fn(crowd)
    row = pd.Series(0.0, index=crowd.columns, name=idx[0])
    longs, shorts = legs(row, ["A", "B", "C", "D"], None, 1)
    assert longs == ["B"] and shorts == ["D"]
    assert legs(row, ["A"], None, 1) is None


def test_last_snapshot_takes_last_positive_row():
    m = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2022-01-01 00:05", "2022-01-01 23:55", "2022-01-01 23:50"], utc=True
            ),
            "sum_open_interest": [10.0, 0.0, 12.0],
            "sum_open_interest_value": [100.0, 0.0, 120.0],
        }
    )
    snap = fo.last_snapshot(m)
    assert snap["oi"] == 12.0


def test_needed_days_includes_pad():
    m = pd.Timestamp("2022-02-01", tz="UTC")
    days = fo.needed_days({m: ["A"]})
    assert ("A", m - pd.Timedelta(days=fo.LOOKBACK_PAD)) in days
    assert ("A", pd.Timestamp("2022-02-28", tz="UTC")) in days
