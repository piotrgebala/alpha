"""
test_diagnose_early_stopping_t4.py

Testy czystych funkcji diagnostyki T4. Najwazniejszy jest `test_pick_matches_xgboost`:
cala runda opiera sie na tym, ze decyzje early stoppingu da sie odtworzyc z krzywej
walidacyjnej. Gdyby odtworzenie rozjezdzalo sie z XGBoost, D1-D3 mierzylyby
nieistniejacy mechanizm.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

from agents.ml_optimizer import (
    MIN_VALIDATION_ROWS,
    REVERSION_FEATURES,
    train_regime_model,
)
from backtest.diagnose_early_stopping_t4 import curves, early_stopping_pick, split_sizes


def test_split_sizes_fraction_rule_when_large():
    assert split_sizes(1000, 0.2) == (800, 200, False)


def test_split_sizes_floor_binds_when_small():
    n_fit, n_val, bound = split_sizes(100, 0.2)
    assert (n_fit, n_val, bound) == (100 - MIN_VALIDATION_ROWS, MIN_VALIDATION_ROWS, True)


def test_pick_monotone_decreasing_takes_last():
    assert early_stopping_pick(np.linspace(1.0, 0.5, 200), patience=20) == 199


def test_pick_stops_after_patience():
    curve = np.concatenate([[1.0, 0.9, 0.8], np.full(50, 0.85), [0.1]])
    # 0.1 lezy za oknem cierpliwosci — XGBoost przerwal wczesniej i go nie widzi.
    assert early_stopping_pick(curve, patience=20) == 2


def test_pick_ties_keep_earlier():
    curve = np.array([1.0, 0.5, 0.5, 0.5, 0.6])
    assert early_stopping_pick(curve, patience=20) == 1


def _synthetic(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, len(REVERSION_FEATURES)))
    signal = x[:, 0] + rng.normal(scale=2.0, size=n)
    label = np.where(signal > 1.0, 1.0, np.where(signal < -1.0, -1.0, 0.0))
    frame = pd.DataFrame(x, columns=REVERSION_FEATURES)
    frame["label"] = label
    return frame


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_pick_matches_xgboost(seed):
    """Decyzja odtworzona z krzywej == `best_iteration` z produkcyjnego `train_regime_model`."""
    frame = _synthetic(360, seed)
    booster = train_regime_model(
        frame,
        frame,
        REVERSION_FEATURES,
        validation_fraction=0.2,
        class_weight_mode="balanced",
    )
    n_fit, _, _ = split_sizes(len(frame), 0.2)
    _, c = curves(frame.iloc[:n_fit], {"val": frame.iloc[n_fit:]})
    expected = getattr(booster, "best_iteration", None)
    assert expected is not None
    assert early_stopping_pick(c["val"]) == expected


def test_curves_returns_full_weighted_curve():
    frame = _synthetic(200, 7)
    booster, c = curves(frame.iloc[:150], {"val": frame.iloc[150:]})
    assert isinstance(booster, xgb.Booster)
    assert len(c["val"]) == 200
    # Pierwsza runda przy wagach `balanced` startuje z rozkladu rownego: strata ~ ln 3.
    assert abs(c["val"][0] - np.log(3)) < 0.01
