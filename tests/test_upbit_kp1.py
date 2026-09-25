"""Testy pomocników backtest/run_upbit_kp1.py (runda KP1): kurs USD/KRW i premia bez przyszłości."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import run_upbit_kp1 as kp


def _fx(dates: list[str], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"date": pd.to_datetime(dates, utc=True), "value": values})


def test_fx_asof_weekend_uses_friday_and_skips_holiday_nan():
    # piątek 8.01 = święto w USA (brak kursu), potem weekend
    fx = _fx(["2021-01-07", "2021-01-08", "2021-01-11"], [1000.0, np.nan, 1010.0])
    days = pd.date_range("2021-01-07", "2021-01-11", freq="D", tz="UTC")
    rate, age = kp.fx_asof(days, fx)
    assert rate.tolist() == [1000.0, 1000.0, 1000.0, 1000.0, 1010.0]
    assert age.tolist() == [0, 1, 2, 3, 0]


def test_fx_asof_never_uses_later_rate_and_drops_stale():
    fx = _fx(["2021-01-10", "2021-01-20"], [1000.0, 1100.0])
    days = pd.date_range("2021-01-09", "2021-01-20", freq="D", tz="UTC")
    rate, _ = kp.fx_asof(days, fx, max_stale_days=5)
    assert np.isnan(rate.iloc[0])  # dzień przed pierwszą obserwacją: brak, nie kurs z przyszłości
    assert rate.loc["2021-01-15"] == 1000.0  # wiek 5 dni — jeszcze dozwolony
    assert np.isnan(rate.loc["2021-01-16"])  # wiek 6 dni — za stary
    assert rate.loc["2021-01-20"] == 1100.0


@settings(max_examples=60, deadline=None)
@given(
    values=st.lists(st.floats(900, 1600), min_size=5, max_size=40),
    gaps=st.lists(st.integers(1, 4), min_size=40, max_size=40),
    cut=st.integers(0, 150),
)
def test_fx_asof_no_lookahead_property(values, gaps, cut):
    """Kurs dla dni ≤ d nie zależy od obserwacji po d (obcięcie danych nic nie zmienia)."""
    dates = pd.Timestamp("2021-01-04", tz="UTC") + pd.to_timedelta(
        np.cumsum([0, *gaps[: len(values) - 1]]), unit="D"
    )
    fx = pd.DataFrame({"date": dates, "value": values})
    days = pd.date_range("2021-01-01", periods=160, freq="D", tz="UTC")
    d = days[cut]
    full, _ = kp.fx_asof(days[: cut + 1], fx)
    part, _ = kp.fx_asof(days[: cut + 1], fx[fx["date"] <= d])
    pd.testing.assert_series_equal(full, part)


def _prices(n: int = 30, x: float = 0.02):
    days = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    t8 = pd.date_range("2021-01-01", periods=3 * n, freq="8h", tz="UTC")
    spot_close = np.where(t8.hour == 16, 100.0 + np.arange(3 * n) / 3, 1.0)
    spot = pd.DataFrame({"timestamp": t8, "close": spot_close})
    fx = _fx([str(d.date()) for d in days if d.dayofweek < 5], [1100.0] * sum(days.dayofweek < 5))
    s16 = spot_close[t8.hour == 16]
    upbit = pd.DataFrame({"open_time": days, "close": s16 * 1100.0 * (1 + x)})
    return upbit, spot, fx


def test_korea_premium_recovers_known_premium_with_16h_close():
    upbit, spot, fx = _prices(x=0.02)
    prem = kp.korea_premium(upbit, spot, fx)
    assert len(prem) == 30
    assert prem.to_numpy() == pytest.approx(0.02)


@pytest.mark.parametrize("cut", [10, 25])
def test_korea_premium_point_in_time(cut):
    upbit, spot, fx = _prices()
    rng = np.random.default_rng(1)
    upbit["close"] *= 1 + rng.normal(0, 0.01, len(upbit))
    d = upbit["open_time"].iloc[cut]
    full = kp.korea_premium(upbit, spot, fx)
    part = kp.korea_premium(
        upbit[upbit["open_time"] <= d],
        spot[spot["timestamp"] < d + pd.Timedelta(days=1)],
        fx[fx["date"] <= d],
    )
    pd.testing.assert_series_equal(full[full.index <= d], part)
