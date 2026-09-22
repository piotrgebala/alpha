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

# --- K2: nazwane warianty naprawy abstynencji (NIE pokretla do strojenia) ---
#
# Ta sama konwencja co `execution_model` (C2.12) i `timeout_leg` (H3): skonczony zbior nazw,
# kazda z udokumentowanym uzasadnieniem, domyslna odtwarza baseline BIT-IDENTYCZNIE.
#
# Diagnoza, ktora je uzasadnia (K1): przy DOSKONALEJ wyroczni abstynencja modelu wynosi 66,48%,
# a udzial klasy timeout w etykietach 66,58% - zgodnosc do 0,1 pp. Abstynencja NIE jest wiec
# sama w sobie wada; wada jest jej ZAPASC do 99,7% przy slabym sygnale, gdy posterior kolapsuje
# do klasy wiekszosciowej. `multi:softprob` z `mlogloss` minimalizuje surowa log-loss na
# rozkladzie, w ktorym timeout ma 2/3 masy - argmax na klase wiekszosciowa jest wtedy dla
# modelu odpowiedzia OPTYMALNA.
CLASS_WEIGHT_NONE = "none"  # BASELINE - brak wazenia, dzisiejsze zachowanie
CLASS_WEIGHT_BALANCED = "balanced"  # w_c = N / (K_obecnych * n_c); srednia waga na wiersz == 1.0
CLASS_WEIGHT_MODES = (CLASS_WEIGHT_NONE, CLASS_WEIGHT_BALANCED)

DIRECTION_POLICY_ARGMAX3 = "argmax3"  # BASELINE - argmax po 3 klasach, timeout -> 0.0
DIRECTION_POLICY_FORCED = "forced"  # argmax po {-1, +1}; abstynencja z konstrukcji = 0%
DIRECTION_POLICIES = (DIRECTION_POLICY_ARGMAX3, DIRECTION_POLICY_FORCED)

CONFIDENCE_MODE_CLASS = "class"  # BASELINE - p(wybranej klasy)
CONFIDENCE_MODE_CONDITIONAL = "conditional"  # p / (p_long + p_short), zakres [0.5, 1.0]
CONFIDENCE_MODES = (CONFIDENCE_MODE_CLASS, CONFIDENCE_MODE_CONDITIONAL)

# Indeksy klas kierunkowych (z pominieciem timeoutu) - wyprowadzone z LABEL_TO_CLASS, nie
# wpisane literalem, zeby zmiana mapowania nie rozjechala sie po cichu z ta stala.
DIRECTIONAL_CLASSES = (LABEL_TO_CLASS[-1.0], LABEL_TO_CLASS[1.0])

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


def validate_signal_policy(direction_policy: str, confidence_mode: str) -> None:
    """
    Jedyne miejsce, ktore zna dopuszczalne kombinacje `direction_policy`/`confidence_mode`.

    Istnieje po to, zeby `backtest.engine.run_backtest` mogl odrzucic literowke w nazwie
    wariantu w NAJWCZESNIEJSZYM punkcie przebiegu - przed treningiem pierwszego modelu -
    nie majac wlasnej kopii regul. To ta sama decyzja co `gate_cost_fraction` w H3:
    usuwamy klase bledu (dwie kopie reguly, ktore moga sie rozjechac), nie jej instancje.

    Bez tego `predict_signal` wywalalby sie dopiero PO treningu, czyli - na realnych
    danych 4h - po kilkunastu minutach liczenia.

    Raises:
        ValueError: nazwa spoza zbioru albo kombinacja, ktorej nie przemyslelismy.
    """
    if direction_policy not in DIRECTION_POLICIES:
        raise ValueError(
            f"direction_policy musi byc jednym z {DIRECTION_POLICIES}, dostalem: {direction_policy!r}"
        )
    if confidence_mode not in CONFIDENCE_MODES:
        raise ValueError(
            f"confidence_mode musi byc jednym z {CONFIDENCE_MODES}, dostalem: {confidence_mode!r}"
        )
    if (
        direction_policy == DIRECTION_POLICY_ARGMAX3
        and confidence_mode == CONFIDENCE_MODE_CONDITIONAL
    ):
        # Pewnosc warunkowa jest NIEZDEFINIOWANA dla wierszy o kierunku 0 - nie przepuszczamy
        # kombinacji, ktorej nie przemyslelismy (fail fast zamiast cichej dziwnej liczby).
        raise ValueError(
            "confidence_mode='conditional' wymaga direction_policy='forced' - pewnosc warunkowa "
            "nie ma sensu dla wierszy, na ktorych model odmawia kierunku"
        )


def validate_class_weight_mode(mode: str) -> None:
    """Jak `validate_signal_policy`, dla wag klas - wolana przez silnik przed treningiem."""
    if mode not in CLASS_WEIGHT_MODES:
        raise ValueError(
            f"class_weight_mode musi byc jednym z {CLASS_WEIGHT_MODES}, dostalem: {mode!r}"
        )


def class_weight_map(
    class_indices: np.ndarray,
    mode: str = CLASS_WEIGHT_NONE,
) -> dict[int, float] | None:
    """
    Mapa waga-per-klasa dla `xgb.DMatrix(weight=...)`. `None` oznacza BRAK wazenia.

    `balanced`: w_c = N / (K_obecnych * n_c). Suma wag po wierszach == N, wiec skala
    hesjanow (a przez nia `min_child_weight` i `eta`) jest ta sama co bez wazenia - zmienia
    sie WYLACZNIE proporcja miedzy klasami, nie ogolna sila sygnalu uczacego.

    Klasy NIEOBECNE w `class_indices` nie trafiaja do mapy - brak dzielenia przez zero przy
    foldzie, w ktorym jakas klasa nie wystapila.

    UWAGA: `scale_pos_weight` z XGBoost NIE dziala tutaj - to parametr celu BINARNEGO, bez
    zadnego efektu przy `multi:softprob`. Jedyna poprawna dzwignia jest wektor `weight` per
    wiersz na DMatrix. (Zapisane, bo kazdy czytelnik najpierw siegnie po scale_pos_weight.)
    """
    validate_class_weight_mode(mode)
    if mode == CLASS_WEIGHT_NONE:
        return None

    values, counts = np.unique(class_indices, return_counts=True)
    n_total = int(counts.sum())
    n_classes = len(values)
    return {
        int(c): float(n_total / (n_classes * cnt)) for c, cnt in zip(values, counts, strict=True)
    }


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
    class_weight_mode: str = CLASS_WEIGHT_NONE,
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

    if class_weight_mode not in CLASS_WEIGHT_MODES:
        raise ValueError(
            f"class_weight_mode musi byc jednym z {CLASS_WEIGHT_MODES}, dostalem: {class_weight_mode!r}"
        )

    def _class_indices(frame: pd.DataFrame) -> np.ndarray:
        return frame[label_column].map(LABEL_TO_CLASS).to_numpy(dtype=np.int32)

    def _dmatrix(frame: pd.DataFrame, weight_map: dict[int, float] | None = None) -> xgb.DMatrix:
        labels = _class_indices(frame)
        if weight_map is None:
            # ROZGALEZIENIE, nie `weight=ones`. Matematycznie tozsame, ale to jest DOKLADNIE
            # ta sama linia kodu co przed K2 - bit-identycznosc baseline'u jest strukturalna,
            # nie numeryczna (lekcja H3: usuwamy klase watpliwosci, nie jej instancje).
            return xgb.DMatrix(frame[feature_columns], label=labels)
        # `.get(..., 1.0)`, nie `[...]`: mapa wag powstaje z czesci UCZACEJ, a stosuje sie
        # ja rowniez do czesci WALIDACYJNEJ. Klasa nieobecna w uczacej, ale obecna w
        # walidacyjnej, wywalalaby KeyError-em caly przebieg — realne w tym projekcie, bo
        # przy `min_train_rows` rowna 30 fold potrafi nie zawierac wszystkich trzech klas
        # (rezim `trend` to 0,53% swiec, C2.5). Klasa, ktorej w uczacej nie bylo, NIE MA
        # czestosci do odwrocenia, wiec jedyna obronna wartoscia jest waga neutralna 1.0;
        # dotyczy to wylacznie macierzy walidacyjnej (early stopping), nie gradientow.
        weights = np.array([weight_map.get(int(c), 1.0) for c in labels], dtype=np.float32)
        return xgb.DMatrix(frame[feature_columns], label=labels, weight=weights)

    if validation_fraction is None:
        if class_weight_mode != CLASS_WEIGHT_NONE:
            # Ta sciezka to UDOKUMENTOWANY PRZECIEK sprzed Z17 (early stopping na foldzie OOS),
            # zachowany wylacznie do odtwarzania C6-C2.13. Nowa naprawa nie ma prawa wejsc na
            # stara wade - inaczej powstalby wariant "Z17 z wagami na wierzchu", ktory wyglada
            # na ulepszenie, a jest regresja.
            raise ValueError(
                "class_weight_mode != 'none' wymaga validation_fraction (sciezka bez early "
                "stopping na OOS). Sciezka validation_fraction=None to przeciek sprzed Z17, "
                "zachowany wylacznie do odtwarzania wynikow historycznych."
            )
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

    # Z17b (2026-09-22): bierz CO NAJMNIEJ MIN_VALIDATION_ROWS wierszy na walidację, o ile
    # zostaje dość na trening. Stara formuła (sam ułamek) powodowała, że przy małych foldach
    # `n_val` wypadało poniżej progu i early stopping NIE ZAŁĄCZAŁ SIĘ WCALE — na 4h dotyczyło
    # to 58 z 63 foldów (92,1%), czyli naprawa Z17+Z21 była tam martwa. Na dużych foldach
    # max() jest operacją pustą, więc wyniki na 5m pozostają bez zmian.
    n_val = max(MIN_VALIDATION_ROWS, int(round(len(train_clean) * validation_fraction)))
    n_fit = len(train_clean) - n_val
    if n_fit < MIN_VALIDATION_ROWS:
        # Za mało danych na uczciwy podział. Trenuj BEZ early stoppingu na całym foldzie
        # treningowym — świadomie gorszy model, ale bez przecieku. Liczbę drzew wyznacza
        # wtedy num_boost_round (patrz best_iteration_or_last).
        return xgb.train(
            full_params,
            _dmatrix(train_clean, class_weight_map(_class_indices(train_clean), class_weight_mode)),
            num_boost_round=num_boost_round,
            verbose_eval=False,
        )

    # Walidacja to CHRONOLOGICZNY OGON treningu (nie losowa próbka): losowy podział
    # szeregu czasowego pozwoliłby modelowi walidować się na danych sprzed tych, na
    # których się uczy.
    fit_part = train_clean.iloc[:n_fit]
    val_part = train_clean.iloc[n_fit:]

    # JEDNA mapa wag, policzona WYLACZNIE na czesci fit, zastosowana do fit ORAZ walidacji.
    #
    # Dlaczego walidacja tez musi byc wazona: early stopping minimalizuje `mlogloss` na ogonie
    # treningu. Gdyby trening byl wazony, a walidacja nie, wybieralibysmy liczbe drzew wobec
    # INNEGO celu niz minimalizowany - niewazony mlogloss jest zdominowany przez klase
    # wiekszosciowa, wiec model odchodzacy od prioru timeoutu wyglada na nim GORZEJ i zostaje
    # uciety dokladnie wtedy, gdy zaczyna robic to, po co wagi wprowadzono. (Rozjazd celow
    # znieczylby naprawe tak samo, jak Z17 bez Z21.)
    #
    # Dlaczego mapa idzie z czesci FIT, a nie z walidacji: etykieta wiersza nigdy nie moze
    # decydowac o tym, jak ten wiersz jest oceniany. Dodatkowo ogon walidacyjny bywa dokladnie
    # MIN_VALIDATION_ROWS = 30 wierszy - estymacja wag na 30 wierszach to szum.
    weight_map = class_weight_map(_class_indices(fit_part), class_weight_mode)
    return xgb.train(
        full_params,
        _dmatrix(fit_part, weight_map),
        num_boost_round=num_boost_round,
        evals=[(_dmatrix(val_part, weight_map), "validation")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False,
    )


def predict_signal(
    booster: xgb.Booster,
    df: pd.DataFrame,
    feature_columns: list[str],
    direction_policy: str = DIRECTION_POLICY_ARGMAX3,
    confidence_mode: str = CONFIDENCE_MODE_CLASS,
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
    validate_signal_policy(direction_policy, confidence_mode)

    clean = df.dropna(subset=feature_columns)
    dmatrix = xgb.DMatrix(clean[feature_columns])

    best_iteration = best_iteration_or_last(booster)
    proba = booster.predict(dmatrix, iteration_range=(0, best_iteration + 1))

    if direction_policy == DIRECTION_POLICY_ARGMAX3:
        # BASELINE - dokladnie ta sama sciezka co przed K2.
        class_idx = np.argmax(proba, axis=1)
    else:
        # Wymuszenie kierunku: argmax WYLACZNIE po klasach kierunkowych. Klasa timeout jest
        # pomijana, wiec abstynencja spada do zera Z KONSTRUKCJI - to tautologia, nie odkrycie,
        # i tak jest zapisane w pre-rejestracji K2.
        #
        # Remis p_long == p_short rozstrzygamy deterministycznie na +1.0 (przy softmaxie float32
        # ma miare zero, ale gdyby kiedys przestal - lepiej, zeby byl przewidywalny niz zalezny
        # od kolejnosci indeksow).
        # Jawne porownanie, NIE np.argmax po podzbiorze: argmax przy remisie zwraca PIERWSZY
        # indeks, czyli po cichu klase -1. `>=` przechyla remis na +1, zgodnie z deklaracja.
        class_short, class_long = LABEL_TO_CLASS[-1.0], LABEL_TO_CLASS[1.0]
        class_idx = np.where(proba[:, class_long] >= proba[:, class_short], class_long, class_short)

    raw_confidence = proba[np.arange(len(proba)), class_idx]
    if confidence_mode == CONFIDENCE_MODE_CLASS:
        confidence = raw_confidence
    else:
        # Pewnosc WARUNKOWA: p(wybrany) / (p_long + p_short), zakres [0.5, 1.0].
        #
        # To jest posterior modelu O KIERUNKU POD WARUNKIEM, ze pozycja jest otwierana - czyli
        # dokladnie wielkosc, ktora rzadzi wyplata przy symetrycznych barierach.
        #
        # Surowe p(klasy) byloby tu BLEDEM i to bledem zmieniajacym ZNAK udokumentowanego
        # obciazenia: `engine._train_fold_confidence_threshold` liczy prog z kwantyla na
        # predykcjach in-sample, gdzie model jest przesadnie pewny - dzis zawyza to prog
        # i bramka przepuszcza MNIEJ (konserwatywnie). Przy surowej pewnosci i wymuszonym
        # kierunku na treningu p_kierunkowe ~ 0,02 (bo p_timeout ~ 1), wiec prog wypadalby
        # ZA NISKO i bramka OOS dopuszczalaby WIECEJ niz nominalne q. Konserwatyzm zmienilby
        # sie w anty-konserwatyzm po cichu - profil wady Z17.
        #
        # Drugi powod: `risk_controller.compute_sizing` skaluje ryzyko przez signal_confidence.
        # Surowa (~0,02-0,20) dalaby pozycje mniejsze o rzad wielkosci, wiec ramie A2 roznilaby
        # sie od baseline'u na DWOCH osiach naraz (regula decyzyjna + faktyczna dzwignia).
        #
        # CO TRACIMY (zapisane jawnie, docs/rag/03): warunkowa odrzuca informacje "model uwaza,
        # ze nic sie nie wydarzy". Przy p = [0.015, 0.98, 0.005] daje 0,75 mimo niemal pewnego
        # timeoutu. Wlasciwym rozwiazaniem, gdyby bramka pewnosci byla wlaczona, jest OSOBNY
        # filtr na p_timeout - nie przeciazanie signal_confidence dwiema rolami.
        directional_mass = proba[:, np.asarray(DIRECTIONAL_CLASSES)].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            confidence = np.where(directional_mass > 0.0, raw_confidence / directional_mass, 0.5)

    direction = np.array([CLASS_TO_LABEL[int(c)] for c in class_idx])

    return pd.DataFrame(
        {"signal_direction": direction, "signal_confidence": confidence},
        index=clean.index,
    )
