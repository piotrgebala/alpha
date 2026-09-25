"""Testy backtest/run_au2_ml.py (AU2 kroki 1–2): cechy bez przyszłości, permutacja, koszyk, werdykt."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_au2_ml as ml


def _panel(n=200, k=6, seed=0):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    cols = ["BTCUSDT"] + [f"C{i}USDT" for i in range(k - 1)]
    close = pd.DataFrame(
        100 * np.exp(np.cumsum(rng.normal(0, 0.03, (n, k)), 0)), index=days, columns=cols
    )
    qvol = pd.DataFrame(np.exp(rng.normal(15, 1, (n, k))), index=days, columns=cols)
    funding = pd.DataFrame(rng.normal(0, 1e-4, (n, k)), index=days, columns=cols)
    oi = pd.DataFrame(np.exp(rng.normal(18, 0.2, (n, k))), index=days, columns=cols)
    return close, qvol, funding, oi


@pytest.mark.parametrize("cut", [120, 170])
def test_build_features_no_lookahead(cut):
    """Zasada 2: cechy dnia t identyczne po obcięciu wszystkich danych po t."""
    close, qvol, funding, oi = _panel()
    full = ml.build_features(close, qvol, funding, oi)
    t = close.index[cut]
    part = ml.build_features(*(x[x.index <= t] for x in (close, qvol, funding, oi)))
    assert set(full) == set(ml.FEATURES)
    for k in ml.FEATURES:
        pd.testing.assert_series_equal(full[k].loc[t], part[k].loc[t], check_names=False)


def test_cross_rank_and_z_respect_mask():
    x = np.array([[3.0, 1.0, 2.0, 100.0]])
    valid = np.array([[True, True, True, False]])
    r = ml.cross_rank(x, valid)
    assert r[0, :3].tolist() == pytest.approx([1.0, 1 / 3, 2 / 3]) and np.isnan(r[0, 3])
    z = ml.cross_z(x, valid)
    assert np.nanmean(z[0]) == pytest.approx(0.0) and np.isnan(z[0, 3])


def test_permute_within_rows_keeps_row_values_and_mask():
    rng = np.random.default_rng(1)
    y = rng.normal(size=(50, 8))
    valid = rng.random((50, 8)) > 0.3
    p = ml.permute_within_rows(y, valid, rng)
    assert np.isnan(p[~valid]).all()
    for t in range(50):
        assert sorted(p[t, valid[t]]) == pytest.approx(sorted(y[t, valid[t]]))
    assert not np.allclose(np.nan_to_num(p), np.nan_to_num(np.where(valid, y, np.nan)))


def test_basket_returns_gross_turnover_and_cost():
    score = np.tile(np.arange(4.0), (8, 1))  # zawsze ten sam ranking: long 3, short 0
    fwd = np.tile(np.array([-0.02, 0.0, 0.0, 0.04]), (8, 1))
    valid = np.ones_like(score, dtype=bool)
    b = ml.basket_returns(score, fwd, valid, fee=0.001, leg=1)
    assert b["gross"].tolist() == pytest.approx([0.03] * 8)
    assert b["turnover"].tolist() == pytest.approx(
        [1.0] * 7 + [0.0]
    )  # faza 0 wraca w dniu 7 bez zmian
    assert b["cost"].iloc[0] == pytest.approx(0.001)


def test_weekly_phase_average_uses_non_overlapping_weeks():
    x = pd.Series(np.arange(14.0))
    w = ml.weekly_phase_average(x)
    assert w.tolist() == pytest.approx([3.0, 10.0])


def test_verdict_positive_for_strong_signal_and_not_for_noise():
    rng = np.random.default_rng(2)
    n = 700
    strong = pd.DataFrame({"gross": 0.01 + rng.normal(0, 0.02, n), "cost": 0.0005})
    noise = pd.DataFrame({"gross": rng.normal(0, 0.02, n), "cost": 0.0005})
    assert ml.verdict(strong, 0.05 + rng.normal(0, 0.1, n))["positive"]
    assert not ml.verdict(noise, rng.normal(0, 0.1, n))["positive"]


def test_quarters_cover_test_days_without_gaps():
    days = pd.date_range("2022-03-01", "2022-12-31", freq="D", tz="UTC")
    start = int(np.searchsorted(days, pd.Timestamp("2022-04-01", tz="UTC")))
    q = ml.quarters(days, start)
    assert q[0][0] == start and q[-1][1] == len(days)
    assert all(a[1] == b[0] for a, b in zip(q, q[1:], strict=False))
    assert len(q) == 3


def test_fit_predict_models_learn_monotone_relation():
    rng = np.random.default_rng(3)
    x = rng.random((600, 3))
    y = x[:, 0] + 0.1 * rng.normal(size=600)
    q = np.repeat(np.arange(60), 10)
    for m in ml.MODELS:
        p = ml.fit_predict(m, x[:500], y[:500], q[:500], x[500:])
        assert np.corrcoef(p, y[500:])[0, 1] > 0.7, m
