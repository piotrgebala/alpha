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
    CLASS_WEIGHT_BALANCED,
    CLASS_WEIGHT_NONE,
    CONFIDENCE_MODE_CLASS,
    CONFIDENCE_MODE_CONDITIONAL,
    DIRECTION_POLICY_ARGMAX3,
    DIRECTION_POLICY_FORCED,
    LABEL_TO_CLASS,
    MIN_VALIDATION_ROWS,
    best_iteration_or_last,
    class_weight_map,
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
        for a, b in zip(f1, f2, strict=True):
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

    accuracy = (signals["signal_direction"].to_numpy() == test_df["label"].to_numpy()).mean()
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
    train_df["f1"] = np.nan  # wszystkie wiersze train_df stają się niepoprawne po dropna

    with pytest.raises(ValueError):
        train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)


def test_train_regime_model_raises_on_empty_test_after_dropna() -> None:
    df = _make_separable_dataset(seed=4)
    train_df, test_df = _train_test_split(df)
    test_df = test_df.copy()
    test_df["label"] = np.nan  # wszystkie wiersze test_df stają się niepoprawne po dropna

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
        _labelled_frame(300, seed=1),
        _labelled_frame(100, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=None,
        embargo_candles=0,
    )
    assert captured["fit_rows"] == 300


def test_embargo_larger_than_train_fold_raises() -> None:
    with pytest.raises(ValueError, match="embargo"):
        train_regime_model(
            _labelled_frame(20, seed=1),
            _labelled_frame(50, seed=2),
            FEATURE_COLUMNS,
            embargo_candles=100,
        )


def test_too_small_fold_trains_without_early_stopping_instead_of_leaking(monkeypatch) -> None:
    """
    Gdy fold jest za mały na uczciwy podział, wolimy model BEZ early stoppingu niż
    early stopping na OOS. Świadomie gorszy model, ale bez przecieku.
    """
    captured = _spy_xgb_train(monkeypatch)
    n = MIN_VALIDATION_ROWS + 5
    train_regime_model(
        _labelled_frame(n, seed=1),
        _labelled_frame(50, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=0.2,
    )
    assert captured["eval_rows"] == []
    assert captured["early_stopping_rounds"] is None


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
def test_invalid_validation_fraction_raises(bad: float) -> None:
    with pytest.raises(ValueError, match="validation_fraction"):
        train_regime_model(
            _labelled_frame(200, seed=1),
            _labelled_frame(50, seed=2),
            FEATURE_COLUMNS,
            validation_fraction=bad,
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
    train_regime_model(
        frame,
        _labelled_frame(50, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=0.25,
        embargo_candles=0,
    )
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
        _labelled_frame(105, seed=1),
        _labelled_frame(50, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=0.2,
        embargo_candles=0,
    )
    assert captured["eval_rows"] == [MIN_VALIDATION_ROWS]
    assert captured["fit_rows"] == 105 - MIN_VALIDATION_ROWS
    assert captured["early_stopping_rounds"] is not None


def test_large_fold_unaffected_by_minimum(monkeypatch) -> None:
    """Na duzych foldach max() jest operacja pusta — wyniki na 5m musza zostac bez zmian."""
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(1000, seed=1),
        _labelled_frame(200, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=0.2,
        embargo_candles=0,
    )
    assert captured["eval_rows"] == [200]  # round(1000*0.2), nie MIN_VALIDATION_ROWS
    assert captured["fit_rows"] == 800


def test_fold_too_small_for_any_split_still_skips_early_stopping(monkeypatch) -> None:
    """Granica pozostaje: gdy po wydzieleniu walidacji nie zostaje dosc na trening."""
    captured = _spy_xgb_train(monkeypatch)
    train_regime_model(
        _labelled_frame(MIN_VALIDATION_ROWS + 5, seed=1),
        _labelled_frame(50, seed=2),
        FEATURE_COLUMNS,
        validation_fraction=0.2,
    )
    assert captured["eval_rows"] == []
    assert captured["early_stopping_rounds"] is None


# ---------------------------------------------------------------------------
# K2 — naprawa abstynencji: wagi klas, polityka kierunku, tryb pewnosci
# (runs/2026-09-22_k2-naprawa-abstynencji/README.md, ramiona A1 i A2)
# ---------------------------------------------------------------------------


def _imbalanced_frame(n_timeout: int = 300, n_directional: int = 30, seed: int = 0) -> pd.DataFrame:
    """
    Rozklad klas przypominajacy realia projektu: klasa `timeout` dominuje.

    Proporcja celowo ostrzejsza niz 66,58% z H2.1 (tu ~83%), zeby efekt wazenia byl
    widoczny na malej probie testowej. To fikstura do testowania MECHANIZMU, nie
    odwzorowanie rynku.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for label, n, (m1, m2) in (
        (0.0, n_timeout, (0.0, 0.0)),
        (1.0, n_directional, (5.0, 5.0)),
        (-1.0, n_directional, (-5.0, -5.0)),
    ):
        for a, b in zip(rng.normal(m1, 0.5, n), rng.normal(m2, 0.5, n), strict=True):
            rows.append({"f1": a, "f2": b, "label": label})
    return pd.DataFrame(rows).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def test_class_weight_map_none_means_no_weighting() -> None:
    """`none` to BASELINE - musi zwrocic None, a nie mape samych jedynek."""
    assert class_weight_map(np.array([0, 1, 1, 2]), mode=CLASS_WEIGHT_NONE) is None
    assert class_weight_map(np.array([0, 1, 1, 2])) is None  # domyslny = baseline


def test_class_weight_map_balanced_keeps_average_row_weight_at_one() -> None:
    """
    To jest WLASCIWOSC, na ktorej opiera sie docstring: suma wag po wierszach == N.

    Bez niej wazenie zmienialoby nie tylko proporcje miedzy klasami, ale i ogolna skale
    hesjanow - a przez nia `min_child_weight` i `eta` dzialalyby na innej skali niz
    w baseline. Wtedy ramie A1 roznilo by sie od A0 na DWOCH osiach naraz i porownanie
    nie mowiloby o wagach klas.
    """
    classes = np.array([0] * 10 + [1] * 60 + [2] * 30)
    weights = class_weight_map(classes, mode=CLASS_WEIGHT_BALANCED)

    per_row = np.array([weights[int(c)] for c in classes])
    assert per_row.sum() == pytest.approx(len(classes))
    assert per_row.mean() == pytest.approx(1.0)

    # Kazda klasa dostaje laczna mase N/K - to jest sens slowa "balanced".
    for c in (0, 1, 2):
        mass = per_row[classes == c].sum()
        assert mass == pytest.approx(len(classes) / 3)


def test_class_weight_map_balanced_weights_are_inverse_frequency() -> None:
    classes = np.array([0] * 10 + [1] * 60 + [2] * 30)
    weights = class_weight_map(classes, mode=CLASS_WEIGHT_BALANCED)
    for c, n_c in ((0, 10), (1, 60), (2, 30)):
        assert weights[c] == pytest.approx(100 / (3 * n_c))
    # Klasa rzadsza wazy wiecej - kierunek, nie tylko wartosc.
    assert weights[0] > weights[2] > weights[1]


def test_class_weight_map_skips_absent_classes_instead_of_dividing_by_zero() -> None:
    """
    Fold, w ktorym jakas klasa nie wystapila, jest w tym projekcie REALNY (rezim `trend`
    to 0,53% swiec - C2.5). Mapa nie moze wtedy zawierac wpisu z dzieleniem przez zero.
    """
    weights = class_weight_map(np.array([1, 1, 1, 2]), mode=CLASS_WEIGHT_BALANCED)
    assert set(weights) == {1, 2}
    assert all(np.isfinite(w) for w in weights.values())


@pytest.mark.parametrize("bad", ["inverse", "auto", "balanced ", "", "None"])
def test_class_weight_map_rejects_unknown_mode(bad: str) -> None:
    with pytest.raises(ValueError, match="class_weight_mode"):
        class_weight_map(np.array([0, 1, 2]), mode=bad)


def test_train_regime_model_default_is_bit_identical_to_pre_k2_baseline() -> None:
    """
    REGRESJA BASELINE'U - warunek, ktory pre-rejestracja K2 stawia ramieniu A0.

    Domyslny `class_weight_mode` musi dawac model IDENTYCZNY co do bajtu z wywolaniem
    bez tego argumentu. Gdyby K2 przesunelo baseline, zadne porownanie A0/A1/A2 nie
    mialoby punktu odniesienia, a wszystkie wczesniejsze rundy stalyby sie nieodtwarzalne.
    """
    df = _imbalanced_frame(seed=11)
    train_df, test_df = _train_test_split(df)

    bez_argumentu = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)
    jawny_baseline = train_regime_model(
        train_df, test_df, FEATURE_COLUMNS, seed=42, class_weight_mode=CLASS_WEIGHT_NONE
    )
    assert bez_argumentu.save_raw("json") == jawny_baseline.save_raw("json")


def test_train_regime_model_balanced_actually_changes_the_model() -> None:
    """Gdyby `balanced` nie zmienialo modelu, ramie A1 byloby pustym ramieniem."""
    df = _imbalanced_frame(seed=12)
    train_df, test_df = _train_test_split(df)
    kwargs = dict(seed=42, validation_fraction=0.2)

    baseline = train_regime_model(train_df, test_df, FEATURE_COLUMNS, **kwargs)
    balanced = train_regime_model(
        train_df, test_df, FEATURE_COLUMNS, class_weight_mode=CLASS_WEIGHT_BALANCED, **kwargs
    )
    assert baseline.save_raw("json") != balanced.save_raw("json")


def test_class_weights_refused_on_the_pre_z17_leaking_path() -> None:
    """
    Strażnik, ktory nie pozwala polaczyc naprawy z udokumentowana wada.

    `validation_fraction=None` to sciezka sprzed Z17: early stopping mierzony na foldzie
    OOS, czyli przeciek. Zostala w repo WYLACZNIE po to, zeby dalo sie odtworzyc wyniki
    C6-C2.13. Gdyby wolno bylo dolozyc do niej wagi klas, powstalby wariant "Z17 z wagami
    na wierzchu" - wygladajacy na ulepszenie, a bedacy regresja. Stad twardy blad zamiast
    cichego dzialania.

    Baseline (`none`) na tej sciezce MUSI dalej dzialac - inaczej stare wyniki przestalyby
    byc odtwarzalne.
    """
    df = _imbalanced_frame(n_timeout=120, n_directional=40, seed=19)
    train_df, test_df = _train_test_split(df)

    with pytest.raises(ValueError, match="validation_fraction"):
        train_regime_model(
            train_df,
            test_df,
            FEATURE_COLUMNS,
            seed=42,
            validation_fraction=None,
            class_weight_mode=CLASS_WEIGHT_BALANCED,
        )

    stara_sciezka = train_regime_model(
        train_df, test_df, FEATURE_COLUMNS, seed=42, validation_fraction=None
    )
    assert stara_sciezka is not None


def test_predict_signal_defaults_are_bit_identical_to_pre_k2_baseline() -> None:
    """Druga polowa regresji baseline'u: sciezka predykcji (ramie A0)."""
    df = _imbalanced_frame(seed=13)
    train_df, test_df = _train_test_split(df)
    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)

    bez_argumentow = predict_signal(booster, test_df, FEATURE_COLUMNS)
    jawny_baseline = predict_signal(
        booster,
        test_df,
        FEATURE_COLUMNS,
        direction_policy=DIRECTION_POLICY_ARGMAX3,
        confidence_mode=CONFIDENCE_MODE_CLASS,
    )
    pd.testing.assert_frame_equal(bez_argumentow, jawny_baseline)


def test_forced_policy_drives_abstention_to_zero() -> None:
    """
    Sedno ramienia A2. Uwaga interpretacyjna zapisana w pre-rejestracji: to jest
    TAUTOLOGIA (klasa timeout jest pomijana z konstrukcji), a nie odkrycie - test
    pilnuje mechanizmu, nie dostarcza argumentu za adopcja A2.
    """
    df = _imbalanced_frame(seed=14)
    train_df, test_df = _train_test_split(df)
    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)

    baseline = predict_signal(booster, test_df, FEATURE_COLUMNS)
    forced = predict_signal(
        booster,
        test_df,
        FEATURE_COLUMNS,
        direction_policy=DIRECTION_POLICY_FORCED,
        confidence_mode=CONFIDENCE_MODE_CONDITIONAL,
    )

    assert (baseline["signal_direction"] == 0.0).any(), "fikstura musi pokazywac abstynencje"
    assert (forced["signal_direction"] != 0.0).all()
    assert set(forced["signal_direction"].unique()).issubset({-1.0, 1.0})
    assert len(forced) == len(baseline), "wymuszenie kierunku nie moze gubic wierszy"


def test_conditional_confidence_equals_directional_posterior() -> None:
    """
    Pewnosc warunkowa to p(wybrany) / (p_long + p_short) - przeliczone DRUGA DROGA,
    wprost z `booster.predict`, a nie przez `predict_signal` (zasada 16a).
    """
    df = _imbalanced_frame(seed=15)
    train_df, test_df = _train_test_split(df)
    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)

    forced = predict_signal(
        booster,
        test_df,
        FEATURE_COLUMNS,
        direction_policy=DIRECTION_POLICY_FORCED,
        confidence_mode=CONFIDENCE_MODE_CONDITIONAL,
    )

    proba = booster.predict(
        xgb.DMatrix(test_df[FEATURE_COLUMNS]),
        iteration_range=(0, best_iteration_or_last(booster) + 1),
    )
    long_idx, short_idx = LABEL_TO_CLASS[1.0], LABEL_TO_CLASS[-1.0]
    p_long, p_short = proba[:, long_idx], proba[:, short_idx]
    oczekiwane = np.maximum(p_long, p_short) / (p_long + p_short)

    np.testing.assert_allclose(forced["signal_confidence"].to_numpy(), oczekiwane, rtol=1e-6)
    assert (forced["signal_confidence"] >= 0.5 - 1e-9).all()
    assert (forced["signal_confidence"] <= 1.0 + 1e-9).all()


def test_forced_policy_breaks_ties_towards_long_deterministically() -> None:
    """
    Remis `p_long == p_short` ma miare zero przy float32, ale gdyby kiedys przestal -
    ma byc PRZEWIDYWALNY, nie zalezny od kolejnosci indeksow. `np.argmax` po podzbiorze
    zwrocilby przy remisie PIERWSZY indeks, czyli po cichu short.
    """

    class _RemisBooster:
        """Podstawia rozklad z dokladnym remisem miedzy long i short."""

        best_iteration = 0

        def predict(self, dmatrix, iteration_range=None):
            n = dmatrix.num_row()
            proba = np.zeros((n, 3), dtype=np.float32)
            proba[:, LABEL_TO_CLASS[-1.0]] = 0.25
            proba[:, LABEL_TO_CLASS[1.0]] = 0.25
            proba[:, LABEL_TO_CLASS[0.0]] = 0.50
            return proba

    df = _imbalanced_frame(n_timeout=5, n_directional=5, seed=16)
    signals = predict_signal(
        _RemisBooster(),
        df,
        FEATURE_COLUMNS,
        direction_policy=DIRECTION_POLICY_FORCED,
        confidence_mode=CONFIDENCE_MODE_CONDITIONAL,
    )
    assert (signals["signal_direction"] == 1.0).all()
    assert signals["signal_confidence"].to_numpy() == pytest.approx(0.5)


def test_conditional_confidence_rejected_without_forced_direction() -> None:
    """
    Pewnosc warunkowa jest NIEZDEFINIOWANA dla wierszy o kierunku 0, wiec kombinacja
    argmax3+conditional ma padac, a nie produkowac cicho dziwna liczbe.
    """
    df = _imbalanced_frame(n_timeout=60, n_directional=30, seed=17)
    train_df, test_df = _train_test_split(df)
    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)

    with pytest.raises(ValueError, match="conditional"):
        predict_signal(
            booster,
            test_df,
            FEATURE_COLUMNS,
            direction_policy=DIRECTION_POLICY_ARGMAX3,
            confidence_mode=CONFIDENCE_MODE_CONDITIONAL,
        )


@pytest.mark.parametrize(
    "policy, mode, oczekiwany_komunikat",
    [
        ("force", CONFIDENCE_MODE_CLASS, "direction_policy"),
        (DIRECTION_POLICY_ARGMAX3, "raw", "confidence_mode"),
    ],
)
def test_predict_signal_rejects_unknown_variant_names(policy, mode, oczekiwany_komunikat) -> None:
    """Nazwane warianty, nie pokretla (precedens C2.12): literowka ma padac, nie milczec."""
    df = _imbalanced_frame(n_timeout=60, n_directional=30, seed=18)
    train_df, test_df = _train_test_split(df)
    booster = train_regime_model(train_df, test_df, FEATURE_COLUMNS, seed=42)

    with pytest.raises(ValueError, match=oczekiwany_komunikat):
        predict_signal(
            booster, test_df, FEATURE_COLUMNS, direction_policy=policy, confidence_mode=mode
        )
