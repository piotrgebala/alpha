"""
test_ml_optimizer.py

Warstwa 1 (unit) testy dla agents/ml_optimizer.py. Cechy syntetyczne (nazwy f1/f2,
nie MOMENTUM_FEATURES/REVERSION_FEATURES) — train_regime_model/predict_signal są
generyczne względem feature_columns, testujemy je w izolacji od feature_miner.py.
Brak wymogu hypothesis (DoD, docs/rag/05: property-based testy wymagane tylko dla
risk_controller.py/labeling.py, nie dla ml_optimizer.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agents.ml_optimizer import (
    CLASS_TO_LABEL,
    LABEL_TO_CLASS,
    predict_signal,
    train_regime_model,
)

FEATURE_COLUMNS = ["f1", "f2"]


def _make_separable_dataset(n_per_class: int = 150, seed: int = 0) -> pd.DataFrame:
    """3 klasy o dobrze rozseparowanych średnich w przestrzeni cech (f1, f2) —
    trywialnie rozdzielne dla drzew decyzyjnych, do testowania samego pipeline'u
    treningu/predykcji (nie jakości modelu na realnych cechach)."""
    rng = np.random.default_rng(seed)
    class_means = {-1.0: (-5.0, -5.0), 0.0: (0.0, 0.0), 1.0: (5.0, 5.0)}
    rows = []
    for label, (m1, m2) in class_means.items():
        f1 = rng.normal(m1, 0.5, size=n_per_class)
        f2 = rng.normal(m2, 0.5, size=n_per_class)
        for a, b in zip(f1, f2):
            rows.append({"f1": a, "f2": b, "label": label})
    df = pd.DataFrame(rows)
    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _train_test_split(
    df: pd.DataFrame, test_frac: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_test = int(len(df) * test_frac)
    return df.iloc[:-n_test].copy(), df.iloc[-n_test:].copy()


# ---------------------------------------------------------------------------
# LABEL_TO_CLASS / CLASS_TO_LABEL
# ---------------------------------------------------------------------------


def test_label_class_round_trip() -> None:
    for label in (-1.0, 0.0, 1.0):
        class_idx = LABEL_TO_CLASS[label]
        assert CLASS_TO_LABEL[class_idx] == label


def test_class_indices_are_zero_based_contiguous() -> None:
    assert sorted(LABEL_TO_CLASS.values()) == [0, 1, 2]


# ---------------------------------------------------------------------------
# train_regime_model
# ---------------------------------------------------------------------------


def test_train_regime_model_learns_separable_pattern() -> None:
    df = _make_separable_dataset(seed=1)
    train_df, test_df = _train_test_split(df)

    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)
    signals = predict_signal(booster, test_df, FEATURE_COLUMNS)

    accuracy = (
        signals["signal_direction"].to_numpy() == test_df["label"].to_numpy()
    ).mean()
    assert accuracy > 0.9


def test_train_regime_model_early_stopping_engages() -> None:
    df = _make_separable_dataset(seed=2)
    train_df, test_df = _train_test_split(df)

    booster = train_regime_model(
        train_df,
        test_df,
        FEATURE_COLUMNS,
        num_boost_round=200,
        early_stopping_rounds=5,
        seed=42,
    )
    # Dataset trywialnie rozdzielny -> mlogloss na test_df płaskieje szybko ->
    # early stopping powinien przerwać dużo przed osiągnięciem num_boost_round.
    assert booster.best_iteration < 199


def test_train_regime_model_raises_on_empty_train_after_dropna() -> None:
    df = _make_separable_dataset(seed=3)
    train_df, test_df = _train_test_split(df)
    train_df = train_df.copy()
    train_df["f1"] = (
        np.nan
    )  # wszystkie wiersze train_df stają się niepoprawne po dropna

    with pytest.raises(ValueError):
        train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)


def test_train_regime_model_raises_on_empty_test_after_dropna() -> None:
    df = _make_separable_dataset(seed=4)
    train_df, test_df = _train_test_split(df)
    test_df = test_df.copy()
    test_df["label"] = (
        np.nan
    )  # wszystkie wiersze test_df stają się niepoprawne po dropna

    with pytest.raises(ValueError):
        train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)


# ---------------------------------------------------------------------------
# predict_signal
# ---------------------------------------------------------------------------


def test_predict_signal_returns_valid_direction_and_confidence() -> None:
    df = _make_separable_dataset(seed=5)
    train_df, test_df = _train_test_split(df)

    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)
    signals = predict_signal(booster, test_df, FEATURE_COLUMNS)

    assert set(signals["signal_direction"].unique()).issubset({-1.0, 0.0, 1.0})
    assert (signals["signal_confidence"] >= 0.0).all()
    assert (signals["signal_confidence"] <= 1.0).all()


def test_predict_signal_preserves_index_after_dropna() -> None:
    df = _make_separable_dataset(seed=6)
    train_df, test_df = _train_test_split(df)
    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)

    test_with_nan = test_df.copy()
    nan_index = test_with_nan.index[0]
    test_with_nan.loc[nan_index, "f1"] = np.nan

    signals = predict_signal(booster, test_with_nan, FEATURE_COLUMNS)

    assert nan_index not in signals.index
    assert len(signals) == len(test_with_nan) - 1
    assert list(signals.index) == [i for i in test_with_nan.index if i != nan_index]
