"""
ml_optimizer.py

Dwa niezależnie trenowane modele XGBoost — model_momentum (Test 1, świece "trend")
i model_reversion (Test 2, świece "range"). Żadnego wspólnego modelu na tym etapie —
uzasadnienie: docs/rag/01_hipoteza_i_architektura.md (momentum i reversion to
sprzeczne zakłady, nie warianty jednego problemu).

KONTRAKT (ml_optimizer -> risk_controller, docs/rag/03_ryzyko_i_sizing.md):
    ml_optimizer emituje:
      { signal_direction: -1|0|1, signal_confidence: float,
        regime: "trend"|"range", atr_14: float, entry_price: float }

Multi-class klasyfikacja (objective="multi:softprob"): klasa = triple-barrier
`label` (agents.labeling.compute_triple_barrier_labels), {-1.0, 0.0, 1.0}.
`signal_direction` = argmax predict_proba. `signal_confidence` = predict_proba
WYBRANEJ (argmax) klasy — nie surowa etykieta (docs/rag/03: "Output: predict_proba,
nie tylko klasa — potrzebne jako signal_confidence").

XGBoost wymaga nieujemnych indeksów klas zaczynających się od 0 — LABEL_TO_CLASS/
CLASS_TO_LABEL robią przejście {-1.0,0.0,1.0} <-> {0,1,2} w obie strony.

Hiperparametry startowe (OBA modele identyczne na tym etapie — docs/rag/03), źródło
prawdy: config/settings.yaml sekcja `model`. Kalibracja WYŁĄCZNIE wewnątrz walk-forward
(CLAUDE.md zasada 1) — early_stopping_rounds liczony na foldzie OOS (test), NIGDY na
train, inaczej model dopasowuje się do szumu treningowego.

Używa natywnego API `xgboost.train()`/`DMatrix` (nie sklearn-wrapper `XGBClassifier`) —
unika zależności od scikit-learn i mapuje `early_stopping_rounds`/`evals` bezpośrednio
na wymaganie C5.2.

Feature sety per model — źródło prawdy: agents/feature_registry.yaml (role="signal"
ORAZ test_group in {"shared", <trend|range>}). role="base" (atr_14) i
role="regime_filter" (atr_pctrank_20d, direction_persistence_10) NIE wchodzą jako
cechy modelu — służą tylko do labelingu/sizingu/klasyfikacji reżimu.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb

# Źródło prawdy: agents/feature_registry.yaml (role=signal, test_group).
MOMENTUM_FEATURES = ["return_lag_1", "volume_zscore_20", "momentum_5", "ema_diff_9_21"]
REVERSION_FEATURES = ["return_lag_1", "volume_zscore_20", "rsi_14", "price_zscore_20"]

# XGBoost multi:softprob wymaga indeksów klas {0, 1, ..., num_class-1}.
LABEL_TO_CLASS = {-1.0: 0, 0.0: 1, 1.0: 2}
CLASS_TO_LABEL = {v: k for k, v in LABEL_TO_CLASS.items()}

# Źródło prawdy: config/settings.yaml, sekcja `model`. Wartości startowe — kalibracja
# WYŁĄCZNIE wewnątrz walk-forward (CLAUDE.md zasada 1).
DEFAULT_SEED = 42
DEFAULT_XGB_PARAMS = {
    "max_depth": 4,
    "eta": 0.05,  # native API: "eta" == sklearn-API "learning_rate"
    "objective": "multi:softprob",
    "num_class": 3,
    "eval_metric": "mlogloss",
}
NUM_BOOST_ROUND = 200  # sklearn-API: n_estimators
EARLY_STOPPING_ROUNDS = 20  # na foldzie OOS (test), nigdy na train


def train_regime_model(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_columns: list[str],
    label_column: str = "label",
    params: dict | None = None,
    num_boost_round: int = NUM_BOOST_ROUND,
    early_stopping_rounds: int = EARLY_STOPPING_ROUNDS,
    seed: int = DEFAULT_SEED,
) -> xgb.Booster:
    """
    Trenuje pojedynczy model XGBoost (multi-class -1/0/1) na `train_df`, z early
    stopping mierzonym na `test_df` — OOS fold z walk-forward (agents.labeling.
    generate_walk_forward_folds), CLAUDE.md zasada 1: kalibracja/early-stop NIGDY
    na danych treningowych.

    Wiersze z NaN w feature_columns/label_column (ATR/wskaźnik warmup, niepełne okno
    triple-barrier na końcu datasetu) są wykluczane PRZED treningiem — nie mogą być
    poprawnie zakodowane jako klasa.

    Random seed jawny (nie domyślny/losowy) — docs/rag/05 (reprodukowalność):
    wynik treningu musi być powtarzalny na tych samych danych.

    Args:
        train_df: dane treningowe danego foldu walk-forward, z kolumnami
            feature_columns + label_column.
        test_df: dane OOS (test) TEGO SAMEGO foldu — używane WYŁĄCZNIE do early
            stopping, nigdy do liczenia gradientów.
        feature_columns: lista kolumn-cech (MOMENTUM_FEATURES albo REVERSION_FEATURES).
        label_column: kolumna z triple-barrier labelem, wartości w {-1.0, 0.0, 1.0}.
        params: nadpisania DEFAULT_XGB_PARAMS (np. do kalibracji w walk-forward).
        num_boost_round: maksymalna liczba drzew (sklearn-API: n_estimators).
        early_stopping_rounds: liczba rund bez poprawy na `test_df` przed przerwaniem.
        seed: jawny random seed XGBoost.

    Returns:
        Wytrenowany xgb.Booster. `booster.best_iteration` wskazuje iterację z
        najlepszym wynikiem na `test_df` (użyć przy predict_signal, nie ostatnią).

    Raises:
        ValueError: jeśli train_df albo test_df nie ma ani jednego poprawnego
            wiersza (wszystkie feature_columns/label_column NaN) po dropna.
    """
    subset_columns = [*feature_columns, label_column]
    train_clean = train_df.dropna(subset=subset_columns)
    test_clean = test_df.dropna(subset=subset_columns)

    if len(train_clean) == 0:
        raise ValueError("train_df nie ma żadnego poprawnego wiersza po dropna (feature/label NaN)")
    if len(test_clean) == 0:
        raise ValueError("test_df nie ma żadnego poprawnego wiersza po dropna (feature/label NaN)")

    y_train = train_clean[label_column].map(LABEL_TO_CLASS).to_numpy(dtype=np.int32)
    y_test = test_clean[label_column].map(LABEL_TO_CLASS).to_numpy(dtype=np.int32)

    dtrain = xgb.DMatrix(train_clean[feature_columns], label=y_train)
    dtest = xgb.DMatrix(test_clean[feature_columns], label=y_test)

    full_params = {**DEFAULT_XGB_PARAMS, **(params or {}), "seed": seed}

    booster = xgb.train(
        full_params,
        dtrain,
        num_boost_round=num_boost_round,
        evals=[(dtest, "test")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False,
    )
    return booster


def predict_signal(
    booster: xgb.Booster,
    df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Generuje sygnały z wytrenowanego modelu (C5.3): `signal_direction` = argmax
    predict_proba (zdekodowany z klasy XGBoost do {-1.0, 0.0, 1.0}), `signal_confidence`
    = predict_proba WYBRANEJ klasy (nie surowa etykieta).

    Używa wyłącznie drzew do `booster.best_iteration` (ustawionego przez early
    stopping w train_regime_model) — ignoruje drzewa dodane PO najlepszej iteracji
    na OOS foldzie.

    Wiersze z NaN w feature_columns są wykluczone (brak kompletnych cech -> brak
    sygnału) — wynikowy DataFrame może mieć mniej wierszy niż `df`.

    Args:
        booster: model z train_regime_model.
        df: dane, na których liczymy sygnał (typowo test/OOS fold).
        feature_columns: te samo cechy, w tym samym porządku, co przy treningu.

    Returns:
        DataFrame [signal_direction, signal_confidence], indeksowany jak `df`
        (po dropna) — zachowuje oryginalny index `df`, żeby wywołujący mógł
        zmapować sygnał z powrotem na konkretny wiersz/timestamp.
    """
    clean = df.dropna(subset=feature_columns)
    dmatrix = xgb.DMatrix(clean[feature_columns])

    best_iteration = booster.best_iteration
    proba = booster.predict(dmatrix, iteration_range=(0, best_iteration + 1))

    class_idx = np.argmax(proba, axis=1)
    confidence = proba[np.arange(len(proba)), class_idx]
    direction = np.array([CLASS_TO_LABEL[int(c)] for c in class_idx])

    return pd.DataFrame(
        {"signal_direction": direction, "signal_confidence": confidence},
        index=clean.index,
    )
