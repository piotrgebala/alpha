"""Testy backtest/run_pr1_portfel.py (PR1): wagi ERC, brak przyszłości w mnożnikach, miary ryzyka."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_pr1_portfel as pr


def _cov(sig, corr):
    sig = np.asarray(sig, dtype=float)
    return np.outer(sig, sig) * np.asarray(corr, dtype=float)


def test_erc_two_assets_equals_inverse_vol_for_any_correlation():
    for rho in (-0.5, 0.0, 0.7):
        w = pr.erc_weights(_cov([0.1, 0.3], [[1, rho], [rho, 1]]))
        assert w == pytest.approx([0.75, 0.25], abs=1e-6)


def test_erc_uncorrelated_equals_inverse_vol_and_correlated_differs():
    sig = [0.1, 0.2, 0.4]
    inv = (1 / np.array(sig)) / (1 / np.array(sig)).sum()
    assert pr.erc_weights(_cov(sig, np.eye(3))) == pytest.approx(inv, abs=1e-6)
    corr = [[1, 0.8, 0.0], [0.8, 1, 0.0], [0.0, 0.0, 1]]
    cov = _cov(sig, corr)
    w = pr.erc_weights(cov)
    rc = w * (cov @ w)
    assert rc == pytest.approx(np.full(3, rc.mean()), rel=1e-4)  # równe wkłady ryzyka
    assert w[2] > inv[2]  # nieskorelowana noga dostaje więcej niż przy 1/σ
    assert w.sum() == pytest.approx(1.0) and (w >= 0).all()


def _returns(n=200, seed=0):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame(
        rng.normal(0, [0.01, 0.02, 0.015], (n, 3)), index=days, columns=["A", "B", "C"]
    )


def test_apply_erc_no_lookahead_and_warmup():
    r = _returns()
    out = pr.apply_erc(r, warmup=60, step=7).set_index("date")
    assert (out.iloc[:60][["k_A", "k_B", "k_C"]] == 1 / 3).all().all()  # rozbieg: równe wagi
    r2 = r.copy()
    r2.iloc[120:] *= 5.0  # zmiana przyszłości po dniu 119
    out2 = pr.apply_erc(r2, warmup=60, step=7).set_index("date")
    pd.testing.assert_frame_equal(
        out.iloc[:120][["k_A", "k_B", "k_C"]], out2.iloc[:120][["k_A", "k_B", "k_C"]]
    )
    assert (out[["k_A", "k_B", "k_C"]] <= 2.0).all().all()  # sufit


def test_risk_metrics_known_series():
    days = pd.date_range("2024-01-01", periods=140, freq="D", tz="UTC")  # 20 pełnych tygodni
    x = pd.Series(0.001, index=days)
    x.iloc[10] = -0.05  # jeden zły dzień w drugim tygodniu
    m = pr.risk_metrics(x)
    assert m["worst_day"] == pytest.approx(-0.05)
    week = x.resample("W-FRI").sum()
    assert m["worst_week"] == pytest.approx(week.min())
    assert m["es95_week"] == pytest.approx(week[week <= week.quantile(0.05)].mean())
    assert m["max_dd"] > 0.04


def test_margin_share_uses_leverage_per_leg():
    k = pd.DataFrame({"k_TS1": [1.0], "k_CP1": [0.6], "k_X1": [0.5]})
    assert pr.margin_share(k, ["TS1", "CP1", "X1"]).iloc[0] == pytest.approx(
        1.0 / 2 + 0.6 / 3 + 0.5
    )
