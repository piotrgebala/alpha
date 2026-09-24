"""Testy backtest/listing_events.py (runda NL1): P&L shorta, likwidacja, funding, błąd klastrowy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import listing_events as le

D0 = pd.Timestamp("2024-01-10", tz="UTC")


def _klines(closes, highs=None, start=D0):
    n = len(closes)
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    opens = [closes[0]] + list(closes[:-1])
    highs = highs if highs is not None else [max(o, c) for o, c in zip(opens, closes, strict=True)]
    return pd.DataFrame(
        {
            "open_time": idx,
            "open": opens,
            "high": highs,
            "low": np.minimum(opens, closes),
            "close": closes,
        }
    )


def _nofund():
    return pd.DataFrame({"timestamp": pd.Series(dtype="datetime64[ns, UTC]"), "funding_rate": []})


def test_entry_is_open_of_day_after_listing_and_exit_close_of_day_14():
    closes = [100.0] + [100.0 - i for i in range(1, 20)]  # d0 … d0+19
    k = _klines(closes)
    r = le.short_event_pnl(k, _nofund(), D0, cost_per_side=0.0)
    entry = k.loc[1, "open"]  # open d0+1 = close d0 = 100
    exit_ = k.loc[14, "close"]  # d0+14
    assert r["entry"] == entry
    assert r["pnl"] == pytest.approx(-(exit_ / entry - 1))
    assert r["days"] == 14 and not r["liquidated"]


def test_missing_first_full_day_returns_none():
    k = _klines([100.0] * 20).iloc[2:]
    assert le.short_event_pnl(k, _nofund(), D0) is None


def test_liquidation_caps_loss_and_stops_funding():
    closes = [100.0] * 20
    highs = [100.0] * 20
    highs[3] = 140.0  # +40 % w dniu d0+3 → likwidacja 3× (próg 30,8 %), nie 1×
    k = _klines(closes, highs)
    f = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                D0 + pd.Timedelta(days=1, hours=8), periods=40, freq="8h", tz="UTC"
            ),
            "funding_rate": 0.001,
        }
    )
    r3 = le.short_event_pnl(k, f, D0, leverage=3.0, cost_per_side=0.0)
    assert r3["liquidated"] and r3["days"] == 3
    # funding tylko do końca dnia likwidacji: d0+1 08:00 … d0+4 00:00 włącznie → 9 rozliczeń
    assert r3["funding"] == pytest.approx(0.009)
    assert r3["pnl"] == pytest.approx(-1 / 3 + 0.009)
    r1 = le.short_event_pnl(k, f, D0, leverage=1.0, cost_per_side=0.0)
    assert not r1["liquidated"] and r1["pnl"] == pytest.approx(0.0 + r1["funding"])


def test_funding_sign_short_receives_positive_rate():
    k = _klines([100.0] * 20)
    f = pd.DataFrame({"timestamp": [D0 + pd.Timedelta(days=2)], "funding_rate": [0.01]})
    assert le.short_event_pnl(k, f, D0, cost_per_side=0.0)["pnl"] == pytest.approx(0.01)
    f2 = pd.DataFrame({"timestamp": [D0 + pd.Timedelta(days=2)], "funding_rate": [-0.01]})
    assert le.short_event_pnl(k, f2, D0, cost_per_side=0.0)["pnl"] == pytest.approx(-0.01)


def test_delisted_inside_window_exits_on_last_close():
    k = _klines([100.0, 100.0, 90.0, 80.0, 70.0])  # d0 … d0+4
    r = le.short_event_pnl(k, _nofund(), D0, cost_per_side=0.0)
    assert r["days"] == 4 and r["pnl"] == pytest.approx(0.30)


@given(
    st.lists(st.floats(min_value=1.0, max_value=500.0), min_size=16, max_size=16),
    st.sampled_from([1.0, 2.0, 3.0]),
)
@settings(max_examples=80, deadline=None)
def test_pnl_bounded_below_by_margin(closes, lev):
    k = _klines(closes)
    r = le.short_event_pnl(k, _nofund(), D0, leverage=lev, cost_per_side=0.0)
    assert r is not None
    assert r["pnl"] >= -1.0 / lev - 1e-12


@given(st.floats(min_value=0.0, max_value=3.0), st.floats(min_value=0.0, max_value=3.0))
@settings(max_examples=60, deadline=None)
def test_pnl_monotone_non_increasing_in_peak(a, b):
    lo_peak, hi_peak = sorted([a, b])
    closes = [100.0] * 20
    res = []
    for peak in (lo_peak, hi_peak):
        highs = [100.0] * 20
        highs[5] = 100.0 * (1 + peak)
        res.append(le.short_event_pnl(_klines(closes, highs), _nofund(), D0, leverage=3.0)["pnl"])
    assert res[1] <= res[0] + 1e-12


def test_cluster_mean_ci_matches_iid_when_singletons():
    x = pd.Series([0.1, -0.2, 0.05, 0.3, -0.1])
    c = pd.Series(range(5))
    r = le.cluster_mean_ci(x, c)
    # CR1 z klastrami jednoelementowymi = iid z korektą n/(n−1) w miejscu ddof
    assert r["se"] == pytest.approx(r["se_iid"], rel=1e-9)
    assert r["mean"] == pytest.approx(x.mean())


def test_cluster_mean_ci_inflates_for_correlated_clusters():
    x = pd.Series([0.2, 0.2, 0.2, -0.2, -0.2, -0.2, 0.2, 0.2, -0.2, -0.2])
    c = pd.Series([0, 0, 0, 1, 1, 1, 2, 2, 3, 3])
    r = le.cluster_mean_ci(x, c)
    assert r["design_effect"] > 1.5
