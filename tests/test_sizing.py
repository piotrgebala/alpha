"""Testy backtest/sizing.py (runda SZ1): R0, sufit, brak przyszłości, hamulec z histerezą."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import sizing as sz


def _two(n=400, seed=0, vols=(0.01, 0.03)):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"a": rng.normal(0, vols[0], n), "b": rng.normal(0, vols[1], n)}, index=idx)


def test_r0_is_average_of_components():
    r = _two()
    out = sz.apply_rules(r, "R0")
    assert out["ret"].to_numpy() == pytest.approx(r.mean(axis=1).to_numpy())


def test_r1_cap_and_inverse_vol():
    r = _two()
    out = sz.apply_rules(r, "R1", target_vol=5.0, cap=2.0)
    assert out[["k_a", "k_b"]].max().max() <= 2.0 + 1e-12
    late = out.iloc[-1]
    out2 = sz.apply_rules(r, "R1", target_vol=0.2, cap=100.0)
    assert out2.iloc[-1]["k_a"] > out2.iloc[-1]["k_b"]  # spokojniejsza składowa dostaje więcej
    assert late["k_a"] == pytest.approx(2.0)


def test_r1_multipliers_use_only_past():
    r = _two()
    a = sz.apply_rules(r, "R1")
    r2 = r.copy()
    r2.iloc[200:] = r2.iloc[200:] * 10  # zmiana przyszłości od dnia 200
    b = sz.apply_rules(r2, "R1")
    # mnożniki ustalone w dniu 196 (i % 7 == 0) i trzymane do 202 nie mogą się zmienić
    assert a.loc[196:199, "k_a"].to_numpy() == pytest.approx(b.loc[196:199, "k_a"].to_numpy())


def test_r2_brake_hysteresis():
    idx = pd.date_range("2021-01-01", periods=140, freq="D", tz="UTC")
    x = np.zeros(140)
    x[70:77] = -0.05  # obsunięcie > 15 %
    x[90:130] = 0.02  # odrabianie
    r = pd.DataFrame({"a": x, "b": x}, index=idx)
    out = sz.apply_rules(r, "R2", warmup=1000, dd_on=0.15, dd_off=0.075)
    assert out["brake"].any()
    first_on = out.index[out["brake"]][0]
    assert first_on >= 77
    assert not out["brake"].iloc[-1]


def test_summary_basic():
    idx = pd.date_range("2021-01-01", periods=365, freq="D", tz="UTC")
    s = sz.summary(pd.Series(0.001, index=idx))
    assert s["cagr"] == pytest.approx(1.001**365 - 1, rel=1e-9)
    assert s["max_dd"] == 0.0
