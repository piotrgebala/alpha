"""Testy agents/ta_macd.py (MX1): MACD niezależną drogą, brak zaglądania w przyszłość, semantyka
„najpierw MACD, potem EMA”, właściwość sygnału (hypothesis)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agents import ta_macd as mx
from agents.ta_rules import rule_ma_cross


def _prices(n=600, seed=0, drift=0.0):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.01, n)))
    return pd.DataFrame({"close": close})


def _ema_loop(x: np.ndarray, span: int) -> np.ndarray:
    """EMA pętlą: alfa = 2/(span+1), start od pierwszej wartości nie-NaN, NaN przed `span` obserwacjami."""
    a = 2.0 / (span + 1.0)
    out = np.full(len(x), np.nan)
    m, seen = np.nan, 0
    for i, v in enumerate(x):
        if np.isnan(v):
            continue
        m = v if np.isnan(m) else a * v + (1 - a) * m
        seen += 1
        if seen >= span:
            out[i] = m
    return out


def test_macd_hist_matches_independent_loop():
    df = _prices()
    c = df["close"].to_numpy()
    macd = _ema_loop(c, 12) - _ema_loop(c, 26)
    hist = (macd - _ema_loop(macd, 9)) / c
    got = mx.compute_macd_hist(df).to_numpy()
    ok = ~np.isnan(hist)
    assert np.isnan(got[~ok]).all()
    assert np.allclose(got[ok], hist[ok], rtol=0, atol=1e-12)


@pytest.mark.parametrize("cut", [60, 150, 299, 300, 451, 599])
def test_no_lookahead_features_and_rules(cut):
    df = _prices(seed=3)
    full_f, full_r = mx.compute_mx_features(df), mx.compute_mx_rules(df)
    part = df.iloc[:cut]
    pd.testing.assert_frame_equal(mx.compute_mx_features(part), full_f.iloc[:cut])
    pd.testing.assert_frame_equal(mx.compute_mx_rules(part), full_r.iloc[:cut])


def _f(ma_signs, macd_signs, cross_at=3):
    ma = pd.Series(ma_signs, dtype=float)
    age = pd.Series(np.where(np.arange(len(ma)) == cross_at, 0.0, 5.0))
    return pd.DataFrame(
        {
            "ma_state": ma * 0.01,
            "ma_cross_age": age,
            "macd_hist": pd.Series(macd_signs, dtype=float) * 0.001,
        }
    )


@pytest.mark.parametrize(
    "ma, macd, expected",
    [
        ([-1, -1, -1, 1, 1, 1], [-1, -1, 1, 1, 1, 1], 1.0),  # MACD w t−1, potem EMA w t → long
        ([-1, -1, -1, 1, 1, 1], [-1, 1, 1, 1, 1, 1], 1.0),  # MACD wcześniej i trzyma → long
        (
            [-1, -1, -1, 1, 1, 1],
            [-1, -1, -1, 1, 1, 1],
            0.0,
        ),  # MACD w tej samej świecy → nie „wcześniej”
        (
            [-1, -1, -1, 1, 1, 1],
            [-1, 1, 1, -1, 1, 1],
            0.0,
        ),  # MACD zawrócił w t → brak potwierdzenia
        ([-1, -1, -1, 1, 1, 1], [-1, -1, -1, -1, -1, -1], 0.0),  # MACD przeciwnie → 0
        ([1, 1, 1, -1, -1, -1], [1, -1, -1, -1, -1, -1], -1.0),  # lustro: short
    ],
)
def test_rule_semantics(ma, macd, expected):
    r = mx.rule_macd_ema_cross(_f(ma, macd))
    assert r.iloc[3] == expected
    assert (r.drop(index=3) == 0).all()  # sygnał tylko w świecy przecięcia EMA


def test_rule_nan_macd_gives_zero():
    f = _f([-1, -1, -1, 1, 1, 1], [np.nan, np.nan, np.nan, 1, 1, 1])
    assert (mx.rule_macd_ema_cross(f) == 0).all()


@settings(max_examples=40, deadline=None)
@given(seed=st.integers(0, 10_000), drift=st.floats(-0.002, 0.002))
def test_property_signal_is_confirmed_subset_of_ema_cross(seed, drift):
    df = _prices(n=400, seed=seed, drift=drift)
    f = mx.compute_mx_features(df)
    r = mx.rule_macd_ema_cross(f)
    ema = rule_ma_cross(f)
    assert set(np.unique(r)) <= {-1.0, 0.0, 1.0}
    on = r != 0
    assert (r[on] == ema[on]).all()  # podzbiór przecięć EMA, ten sam kierunek
    h = np.sign(f["macd_hist"])
    assert (h[on] == r[on]).all() and (h.shift(1)[on] == r[on]).all()
    assert (f.loc[on, "ma_cross_age"] == 0).all()
