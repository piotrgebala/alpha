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

import xgboost as xgb

from agents.ml_optimizer import (
    CLASS_TO_LABEL,
    LABEL_TO_CLASS,
    MIN_VALIDATION_ROWS,
    best_iteration_or_last,
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


# ---------------------------------------------------------------------------
# Z17+Z21 (Backlog II): walidacja z ogona treningu + embargo na granicy train/test
# ---------------------------------------------------------------------------


def _labelled_frame(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "f1": rng.normal(size=n),
            "f2": rng.normal(size=n),
            "label": rng.choice([-1.0, 0.0, 1.0], size=n),
        }
    )


class _SpyBooster:
    best_iteration = 5


def _spy_xgb_train(monkeypatch) -> dict:
    """Przechwytuje argumenty xgb.train — pozwala sprawdzić, NA CZYM liczy się early stopping."""
    captured: dict = {}

    def fake_train(params, dtrain, num_boost_round=None, evals=None, **kwargs):
        captured["fit_rows"] = dtrain.num_row()
        captured["eval_rows"] = [d.num_row() for d, _ in (evals or [])]
        captured["eval_names"] = [name for _, name in (evals or [])]
        captured["early_stopping_rounds"] = kwargs.get("early_stopping_rounds")
        return _SpyBooster()

    monkeypatch.setattr(xgb, "train", fake_train)
    return captured


def test_validation_split_never_evaluates_on_test_fold(monkeypatch) -> None:
    """
    SEDNO Z17: przy `validation_fraction` early stopping MUSI liczyć się na ogonie
    treningu, nie na foldzie OOS. Rozmiary dobrane tak, że liczba wierszy walidacji
    (38) jest różna od rozmiaru testu (100) — test jednoznacznie odróżnia obie wersje.
    """
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(200, seed=1),
        _labelled_frame(100, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=0.2,
        embargo_candles=12,
    )
    # 200 - 12 (embargo) = 188; n_val = round(188*0.2) = 38; n_fit = 150
    assert captured["fit_rows"] == 150
    assert captured["eval_rows"] == [38]
    assert captured["eval_names"] == ["validation"]
    assert 100 not in captured["eval_rows"], "early stopping nie może widzieć foldu testowego"


def test_legacy_path_still_evaluates_on_test(monkeypatch) -> None:
    """Ścieżka sprzed Z17 zachowana do regresji baseline'u C6-C2.13 — i jawnie nazwana."""
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(200, seed=1),
        _labelled_frame(100, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=None,
    )
    assert captured["fit_rows"] == 200
    assert captured["eval_rows"] == [100]
    assert captured["eval_names"] == ["test"]


def test_embargo_removes_tail_of_training_fold(monkeypatch) -> None:
    """Z21: ostatnie V wierszy treningu mają etykiety sięgające w okno testowe."""
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(300, seed=1),
        _labelled_frame(100, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=None,
        embargo_candles=50,
    )
    assert captured["fit_rows"] == 250


def test_embargo_zero_is_identical_to_no_embargo(monkeypatch) -> None:
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(300, seed=1), _labelled_frame(100, seed=2),
        FEATURE_COLUMNS, validation_fraction=None, embargo_candles=0,
    )
    assert captured["fit_rows"] == 300


def test_embargo_larger_than_train_fold_raises() -> None:
    with pytest.raises(ValueError, match="embargo"):
        train_regime_model(
            _labelled_frame(20, seed=1), _labelled_frame(50, seed=2),
            FEATURE_COLUMNS, embargo_candles=100,
        )


def test_too_small_fold_trains_without_early_stopping_instead_of_leaking(monkeypatch) -> None:
    """
    Gdy fold jest za mały na uczciwy podział, wolimy model BEZ early stoppingu niż
    early stopping na OOS. Świadomie gorszy model, ale bez przecieku.
    """
    captured = _spy_xgb_train(monkeypatch)
    n = MIN_VALIDATION_ROWS + 5
    train_regime_model(
        _labelled_frame(n, seed=1), _labelled_frame(50, seed=2),
        FEATURE_COLUMNS, validation_fraction=0.2,
    )
    assert captured["eval_rows"] == []
    assert captured["early_stopping_rounds"] is None


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
def test_invalid_validation_fraction_raises(bad: float) -> None:
    with pytest.raises(ValueError, match="validation_fraction"):
        train_regime_model(
            _labelled_frame(200, seed=1), _labelled_frame(50, seed=2),
            FEATURE_COLUMNS, validation_fraction=bad,
        )


def test_best_iteration_or_last_falls_back_when_no_early_stopping() -> None:
    """xgboost >= 2.0 podnosi AttributeError bez early stoppingu — guard na 3 wywołania."""

    class _NoES:
        pass

    assert best_iteration_or_last(_NoES(), num_boost_round=200) == 199
    assert best_iteration_or_last(_SpyBooster()) == 5


def test_validation_split_is_chronological_tail_not_random(monkeypatch) -> None:
    """
    Losowy podział szeregu czasowego pozwoliłby walidować się na danych SPRZED tych,
    na których model się uczy. Sprawdzamy, że walidacja to dokładnie ogon.
    """
    seen: dict = {}

    def fake_train(params, dtrain, num_boost_round=None, evals=None, **kwargs):
        seen["fit"] = dtrain.get_label().tolist()
        seen["val"] = evals[0][0].get_label().tolist() if evals else []
        return _SpyBooster()

    monkeypatch.setattr(xgb, "train", fake_train)
    frame = _labelled_frame(200, seed=7)
    train_regime_model(frame, _labelled_frame(50, seed=2), FEATURE_COLUMNS,
                       validation_fraction=0.25, embargo_candles=0)
    expected = frame["label"].map(LABEL_TO_CLASS).tolist()
    n_val = 50
    assert seen["fit"] == expected[: 200 - n_val]
    assert seen["val"] == expected[200 - n_val :]


# ---------------------------------------------------------------------------
# Z17b: early stopping musi sie ZALACZAC takze na malych foldach
# ---------------------------------------------------------------------------


def test_small_fold_still_gets_early_stopping(monkeypatch) -> None:
    """
    REGRESJA na wade wykryta w walidacji S1: przy n=105 i frac=0.2 stara formula dawala
    n_val=21 < MIN_VALIDATION_ROWS=30 i CALKOWICIE wylaczala early stopping. Nowa bierze
    max(30, 21) = 30, zostawiajac 75 wierszy na trening — wiec early stopping DZIALA.
    """
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(105, seed=1), _labelled_frame(50, seed=2),
        FEATURE_COLUMNS, validation_fraction=0.2, embargo_candles=0,
    )
    assert captured["eval_rows"] == [MIN_VALIDATION_ROWS]
    assert captured["fit_rows"] == 105 - MIN_VALIDATION_ROWS
    assert captured["early_stopping_rounds"] is not None


def test_large_fold_unaffected_by_minimum(monkeypatch) -> None:
    """Na duzych foldach max() jest operacja pusta — wyniki na 5m musza zostac bez zmian."""
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(1000, seed=1), _labelled_frame(200, seed=2),
        FEATURE_COLUMNS, validation_fraction=0.2, embargo_candles=0,
    )
    assert captured["eval_rows"] == [200]  # round(1000*0.2), nie MIN_VALIDATION_ROWS
    assert captured["fit_rows"] == 800


def test_fold_too_small_for_any_split_still_skips_early_stopping(monkeypatch) -> None:
    """Granica pozostaje: gdy po wydzieleniu walidacji nie zostaje dosc na trening."""
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(MIN_VALIDATION_ROWS + 5, seed=1), _labelled_frame(50, seed=2),
        FEATURE_COLUMNS, validation_fraction=0.2,
    )
    assert captured["eval_rows"] == []
    assert captured["early_stopping_rounds"] is None
