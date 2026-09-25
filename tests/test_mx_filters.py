"""Testy agents/mx_filters.py (MX2): brak zaglądania w przyszłość, semantyka filtrów, podzbiór MX1."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agents import mx_filters as mf


def _ohlcv(n=1300, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    spread = np.abs(rng.normal(0, 0.004, n)) * close
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC"),
            "open": close,
            "high": close + spread,
            "low": close - spread,
            "close": close,
            "volume": rng.lognormal(10, 0.5, n),
        }
    )


@pytest.mark.parametrize("cut", [700, 900, 1101, 1299])
def test_no_lookahead(cut):
    df = _ohlcv()
    full_i, full_r = mf.compute_filter_inputs(df), mf.compute_mx2_rules(df)
    part = df.iloc[:cut]
    pd.testing.assert_frame_equal(mf.compute_filter_inputs(part), full_i.iloc[:cut])
    pd.testing.assert_frame_equal(mf.compute_mx2_rules(part), full_r.iloc[:cut])


def test_filter_semantics():
    inputs = pd.DataFrame(
        {
            "ret28": [0.1, 0.1, -0.1, np.nan, 0.1, 0.1],
            "adx_14": [30, 20, 25, 40, np.nan, 26],
            "volume_zscore_20": [0.5, -0.5, 0.0, 1.0, 1.0, np.nan],
            "rsi_14": [55, 55, 45, 50, 60, 40],
            "hour": [13, 12, 20, 21, 0, 16],
        }
    )
    d = pd.Series([1.0, -1.0, -1.0, 1.0, 1.0, -1.0])
    ok = mf.filter_pass(inputs, d)
    assert ok["trend28"].tolist() == [True, False, True, False, True, False]
    assert ok["adx25"].tolist() == [True, False, False, True, False, True]  # 25 nie jest > 25
    assert ok["wolumen"].tolist() == [True, False, False, True, True, False]
    assert ok["sesja_usa"].tolist() == [True, False, True, False, False, True]
    assert ok["rsi50"].tolist() == [True, False, True, False, True, True]  # 50 nie przechodzi


def test_filtered_rules_are_subsets_of_mx1():
    df = _ohlcv(n=3000, seed=7)
    r = mf.compute_mx2_rules(df)
    base = r["rule_macd_ema_cross"]
    assert (base != 0).sum() > 20  # jest z czego filtrować
    for name in mf.FILTERS:
        col = r[f"rule_mx2_{name}"]
        on = col != 0
        assert set(np.unique(col)) <= {-1.0, 0.0, 1.0}
        assert (col[on] == base[on]).all()  # tylko sygnały MX1, ten sam kierunek
        assert on.sum() <= (base != 0).sum()
