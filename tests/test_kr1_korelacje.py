"""Testy backtest/run_kr1_korelacje.py (KR1): mieszanka 1/σ i współczynnik dywersyfikacji."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_kr1_korelacje as kr


def test_diversification_one_for_identical_legs_and_lower_for_independent():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 0.01, 5000)
    same = pd.DataFrame({"A": a, "B": 2 * a})
    assert kr.diversification(same) == pytest.approx(1.0)
    indep = pd.DataFrame({"A": a, "B": rng.normal(0, 0.02, 5000)})
    assert kr.diversification(indep) == pytest.approx(1 / np.sqrt(2), abs=0.03)


def test_inverse_vol_mix_equalises_risk_contributions():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"A": rng.normal(0, 0.01, 5000), "B": rng.normal(0, 0.04, 5000)})
    w = 1 / df.std()
    w = w / w.sum()
    assert w["A"] * df["A"].std() == pytest.approx(w["B"] * df["B"].std())
    assert kr.inverse_vol_mix(df).std() == pytest.approx(np.sqrt(2) * w["A"] * df["A"].std(), rel=0.03)
