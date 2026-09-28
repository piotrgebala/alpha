"""Testy reportera OS1 (otwarcia sesji): czas otwarć z czasem letnim/zimowym, okna zwrotu, start F1."""

import numpy as np
import pandas as pd

from backtest.run_os1_otwarcia import SESSIONS, f1_tradable_days, session_opens, window_return


def _utc(days, name):
    tz, hhmm = SESSIONS[name]
    return list(session_opens(pd.DatetimeIndex(days), tz, hhmm).strftime("%H:%M"))


def test_session_opens_follow_daylight_saving():
    # 2024: czas letni USA od 10.03, Wielkiej Brytanii od 31.03; zimowy USA od 03.11, UK od 27.10.
    days = ["2024-01-15", "2024-03-12", "2024-04-02", "2024-10-29", "2024-11-05"]
    assert _utc(days, "nowy_jork") == ["14:30", "13:30", "13:30", "13:30", "14:30"]
    assert _utc(days, "londyn") == ["08:00", "08:00", "07:00", "08:00", "08:00"]
    assert _utc(days, "tokio") == ["00:00"] * 5


def _candles(start, n, step_pct=0.01):
    ts = pd.date_range(start, periods=n, freq="30min", tz="UTC")
    close = 100 * (1 + step_pct) ** np.arange(1, n + 1)
    open_ = np.concatenate([[100.0], close[:-1]])
    return pd.Series(open_, index=ts), pd.Series(close, index=ts)


def test_window_return_spans_exact_candles():
    open_, close = _candles("2024-01-15 00:00", 12)
    starts = pd.DatetimeIndex([pd.Timestamp("2024-01-15 00:00", tz="UTC")])
    # [+30, +240) = 7 świec po 1 % → 1,01^7 − 1
    r = window_return(open_, close, starts, 30, 240)
    assert np.isclose(r.iloc[0], 1.01**7 - 1)
    assert np.isclose(window_return(open_, close, starts, 0, 60).iloc[0], 1.01**2 - 1)


def test_window_return_missing_candle_is_nan():
    open_, close = _candles("2024-01-15 00:00", 12)
    gap = pd.Timestamp("2024-01-15 02:00", tz="UTC")
    open_, close = open_.drop(gap), close.drop(gap)
    starts = pd.DatetimeIndex([pd.Timestamp("2024-01-15 00:00", tz="UTC")])
    assert np.isnan(window_return(open_, close, starts, 30, 240).iloc[0])
    assert not np.isnan(window_return(open_, close, starts, 0, 60).iloc[0])


def test_f1_needs_65_prior_observations():
    days = pd.bdate_range("2021-01-01", periods=200, tz="UTC")
    valid = pd.Series(True, index=days)
    # dzień z indeksem 65 ma dokładnie 65 wcześniejszych obserwacji → handluje od niego
    assert f1_tradable_days(valid) == 200 - 65
