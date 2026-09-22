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
EARLY_STOPPING_ROUNDS = 20

# Z17+Z21 (Backlog II) — walidacja early stoppingu wycinana z CHRONOLOGICZNEGO OGONA
# foldu treningowego, plus embargo na granicy train/test.
#
# Stan sprzed Z17 (zachowany jako `validation_fraction=None`): early stopping liczyło się
# na `test_df`, czyli na foldzie OOS. To przeciek decyzji — liczba drzew była dobierana
# pod dane, na których mierzymy wynik, więc raportowane `p` było ZAWYŻONE. Docstringi
# i config/settings.yaml opisywały to jako decyzję ("na foldzie OOS, nigdy na train"),
# co utrwalało buga jako wybór projektowy.
#
# Embargo: etykieta triple-barrier wiersza t patrzy do t+VERTICAL_BARRIER_CANDLES, więc
# ostatnie V wierszy treningu ma etykiety sięgające W OKNO TESTOWE. Bez odcięcia ich
# walidacja (ogon treningu) byłaby skażona ruchem z okresu testowego — czyli naprawa
# Z17 bez Z21 nie naprawiałaby niczego. Stąd oba w jednej zmianie: dotyczą TEJ SAMEJ
# granicy. `embargo_candles=0` zachowuje stan sprzed zmiany.
DEFAULT_VALIDATION_FRACTION = 0.2
MIN_VALIDATION_ROWS = 30  # spójne z backtest.engine.MIN_TRAIN_ROWS

# UWAGA (walidacja S1, 2026-09-22): przy małych foldach ten próg powoduje, że early stopping
# NIE ZAŁĄCZA SIĘ WCALE. Na 4h (okno testowe 28 dni) mediana n_val wyniosła 21, więc 58 z 63
# foldów (92,1%) trenowało się bez early stoppingu, do pełnych num_boost_round. Naprawa Z17+Z21
# jest wtedy formalnie obecna, ale martwa. `folds_summary` nie raportuje tego faktu — jeśli
# runda zależy od early stoppingu, policz udział foldów z walidacją PRZED interpretacją wyniku.


def best_iteration_or_last(booster: xgb.Booster, num_boost_round: int = NUM_BOOST_ROUND) -> int:
    """
    `booster.best_iteration` istnieje TYLKO wtedy, gdy zadziałał early stopping.
    Bez niego xgboost >= 2.0 podnosi AttributeError — a wariant bez early stoppingu
    powstaje legalnie, gdy fold jest za mały na wydzielenie walidacji. Zwraca wtedy
    indeks ostatniego drzewa.
    """
    best = getattr(booster, "best_iteration", None)
    if best is None:
        return num_boost_round - 1
    return int(best)


def train_regime_model(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_columns: list[str],
    label_column: str = "label",
    params: dict | None = None,
    num_boost_round: int = NUM_BOOST_ROUND,
    early_stopping_rounds: int = EARLY_STOPPING_ROUNDS,
    seed: int = DEFAULT_SEED,
    validation_fraction: float | None = None,
    embargo_candles: int = 0,
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

    # Z21: odetnij ogon treningu, którego etykiety sięgają w okno testowe.
    if embargo_candles > 0:
        if len(train_clean) <= embargo_candles:
            raise ValueError(
                f"embargo_candles={embargo_candles} wycina cały fold treningowy "
                f"({len(train_clean)} wierszy) — fold powinien zostać pominięty wcześniej"
            )
        train_clean = train_clean.iloc[:-embargo_candles]

    full_params = {**DEFAULT_XGB_PARAMS, **(params or {}), "seed": seed}

    def _dmatrix(frame: pd.DataFrame) -> xgb.DMatrix:
        labels = frame[label_column].map(LABEL_TO_CLASS).to_numpy(dtype=np.int32)
        return xgb.DMatrix(frame[feature_columns], label=labels)

    if validation_fraction is None:
        # ŚCIEŻKA SPRZED Z17 — early stopping na foldzie OOS. Zachowana WYŁĄCZNIE po to,
        # żeby dało się odtworzyć wyniki C6-C2.13 co do cyfry. Nie używać do nowych pomiarów.
        booster = xgb.train(
            full_params,
            _dmatrix(train_clean),
            num_boost_round=num_boost_round,
            evals=[(_dmatrix(test_clean), "test")],
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=False,
        )
        return booster

    if not 0.0 < validation_fraction < 1.0:
        raise ValueError(f"validation_fraction musi być w (0, 1), dostałem {validation_fraction}")

    n_val = int(round(len(train_clean) * validation_fraction))
    n_fit = len(train_clean) - n_val
    if n_val < MIN_VALIDATION_ROWS or n_fit < MIN_VALIDATION_ROWS:
        # Za mało danych na uczciwy podział. Trenuj BEZ early stoppingu na całym foldzie
        # treningowym — świadomie gorszy model, ale bez przecieku. Liczbę drzew wyznacza
        # wtedy num_boost_round (patrz best_iteration_or_last).
        return xgb.train(
            full_params,
            _dmatrix(train_clean),
            num_boost_round=num_boost_round,
            verbose_eval=False,
        )

    # Walidacja to CHRONOLOGICZNY OGON treningu (nie losowa próbka): losowy podział
    # szeregu czasowego pozwoliłby modelowi walidować się na danych sprzed tych, na
    # których się uczy.
    fit_part = train_clean.iloc[:n_fit]
    val_part = train_clean.iloc[n_fit:]
    return xgb.train(
        full_params,
        _dmatrix(fit_part),
        num_boost_round=num_boost_round,
        evals=[(_dmatrix(val_part), "validation")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False,
    )


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

    best_iteration = best_iteration_or_last(booster)
    proba = booster.predict(dmatrix, iteration_range=(0, best_iteration + 1))

    class_idx = np.argmax(proba, axis=1)
    confidence = proba[np.arange(len(proba)), class_idx]
    direction = np.array([CLASS_TO_LABEL[int(c)] for c in class_idx])

    return pd.DataFrame(
        {"signal_direction": direction, "signal_confidence": confidence},
        index=clean.index,
    )
