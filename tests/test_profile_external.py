"""Testy data/profile_external.py — czyste funkcje profilu (runda P3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data import profile_external as pe


def _ts(n: int, freq: str = "5min", start: str = "2021-01-01") -> pd.Series:
    return pd.Series(pd.date_range(start, periods=n, freq=freq, tz="UTC"))


def test_infer_step_mode_of_diffs_and_short_series():
    ts = _ts(10)
    assert pe.infer_step(ts) == pd.Timedelta("5min")
    assert pe.infer_step(ts.iloc[:1]) is None
    # jedna luka nie zmienia ziarna (moda, nie średnia)
    with_gap = pd.concat([ts.iloc[:5], ts.iloc[7:]], ignore_index=True)
    assert pe.infer_step(with_gap) == pd.Timedelta("5min")


def test_gaps_reports_missing_points():
    ts = _ts(10)
    with_gap = pd.concat([ts.iloc[:5], ts.iloc[8:]], ignore_index=True)  # brak 5,6,7
    g = pe.gaps(with_gap, pd.Timedelta("5min"))
    assert len(g) == 1
    assert g.loc[0, "missing_points"] == 3
    assert (
        pd.Timestamp(g.loc[0, "from"]) == ts.iloc[4] and pd.Timestamp(g.loc[0, "to"]) == ts.iloc[8]
    )
    assert pe.gaps(ts, pd.Timedelta("5min")).empty
    assert pe.gaps(ts, None).empty


def test_coverage_counts_only_inside_base_window():
    ts = pd.Series(pd.date_range("2020-12-30", "2021-01-03", freq="D", tz="UTC"))
    cov = pe.coverage(
        ts,
        pd.Timedelta("1D"),
        pd.Timestamp("2021-01-01", tz="UTC"),
        pd.Timestamp("2021-01-05", tz="UTC"),
    )
    assert cov == {"expected": 4, "present": 3, "fraction": 0.75}
    assert np.isnan(pe.coverage(ts, None)["fraction"])


def test_point_mass_and_autocorr():
    x = pd.Series([0.0, 0.0, 0.0, 1.0, 2.0, np.nan])
    val, share = pe.point_mass(x)
    assert val == 0.0 and share == pytest.approx(3 / 5)
    assert pe.point_mass(pd.Series([np.nan]))[1] == 0.0
    trend = pd.Series(np.arange(50, dtype=float))
    assert pe.lag1_autocorr(trend) > 0.9
    assert np.isnan(pe.lag1_autocorr(pd.Series([1.0, 1.0, 1.0])))


def test_profile_frame_end_to_end():
    df = pd.DataFrame(
        {
            "timestamp": _ts(6, "1D"),
            "a": [1.0, 2.0, 2.0, 2.0, np.nan, -1.0],
            "label": ["x"] * 6,  # kolumna tekstowa pomijana
        }
    )
    head, cols, gp = pe.profile_frame(df, "t")
    assert head["wiersze"] == 6 and head["ziarno"] == pd.Timedelta("1D")
    assert head["duplikaty_znacznika"] == 0 and head["baza_obecne"] == 6
    assert list(cols["kolumna"]) == ["a"]
    row = cols.iloc[0]
    assert (
        row["braki"] == 1
        and row["niedodatnie"] == 1
        and row["masa_pkt_udział"] == pytest.approx(3 / 5)
    )
    assert gp.empty


def test_time_column_required():
    with pytest.raises(ValueError):
        pe.time_column(pd.DataFrame({"x": [1]}))
