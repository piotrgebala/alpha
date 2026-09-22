"""
engine.py

Backtest Fazy 0: pętla sygnał -> risk_controller -> PnL z kosztami -> equity curve
(STATUS.md §5 Commit 5). Orkiestruje cały pipeline na surowym OHLCV:
cechy (agents.feature_miner) -> triple-barrier labels (agents.labeling) -> split po
reżimie -> walk-forward foldy (agents.labeling) -> trening + predykcja per fold
(agents.ml_optimizer) -> sizing (risk_controller_fn) -> koszty (backtest.costs) ->
equity curve + trade journal (C5.6).

RISK CONTROLLER + KILL-SWITCH (Commit 5.5, `agents/risk_controller.py`):
Sizing pełni `agents.risk_controller.compute_sizing` (domyślny `risk_controller_fn`) —
kontrakt formalny ml_optimizer -> risk_controller, formuła size_risk/size_leverage/
min() + skalowanie confidence (docs/rag/03_ryzyko_i_sizing.md), zastępuje dawny
`_placeholder_risk_controller` (formuła identyczna, teraz formalny, testowany moduł).
Kill-switch (`agents.risk_controller.check_kill_switch`) sprawdzany PRZED sizingiem
każdego sygnału: drawdown equity od bieżącego peaku (running max śledzony w pętli
poniżej) > KILL_SWITCH_DRAWDOWN_PCT -> sygnał pomijany (position_size=0.0, equity bez
zmian), ale wiersz i tak trafia do `trades` z flagą `kill_switch_active=True`
(audytowalność — widać dokładnie, kiedy i jak często kill-switch by się aktywował).
Re-check dynamiczny przy KAŻDYM sygnale: kill-switch wznawia normalną pracę, gdy
equity odzyska się z powrotem powyżej progu (nie permanentny latch).

KILL-SWITCH COOLDOWN/RE-ARM (Commit 2c, 2026-08-01, patrz agents/risk_controller.py
dla pełnego uzasadnienia): equity NIE zmienia się, gdy sygnał jest stłumiony
(position_size=0.0 -> net_pnl=0.0), więc bez dodatkowego mechanizmu kill-switch
zostaje aktywny NA ZAWSZE po pierwszym zadziałaniu (deadlock potwierdzony
empirycznie w Commit 2b: 99,8% sygnałów stłumionych, equity zamrożone od
2025-09-27 do końca datasetu, mimo że model w kolejnych foldach nadal generował
liczne sygnały kandydujące). Pętla poniżej śledzi `kill_switch_tripped_at` — po
`kill_switch_cooldown_days` ciągłej suppresji resetuje `peak_equity` do bieżącego
(zamrożonego) equity, dając strategii kolejną szansę zamiast czekać na organiczne
odzyskanie, które strukturalnie nie może nastąpić w tej architekturze.

BRAMKA WYKONALNOŚCI KOSZTOWEJ (Commit 2d, 2026-09-21, patrz agents/risk_controller.py
dla pełnego uzasadnienia i liczb): sygnał wchodzi do gry tylko, gdy pełne trafienie
bariery zysku (ATR_MULTIPLIER * atr_14) daje co najmniej `min_barrier_to_cost_ratio`
wielokrotność kosztu round-trip. Powód: w reżimie `range` mediana bariery (0,130% ceny)
jest WĘŻSZA niż koszt round-trip (0,140% nominału), więc break-even wymagałby 103,9%
trafności kierunku — NO-GO Commitu 2c był w ~94% wynikiem arytmetycznym, nie
statystycznym (model trafiał kierunek w 54,6% realnych transakcji, a mimo to łączny
gross wyniósł -569 przy koszcie 9 168).

DECYZJA — bramka kosztowa filtruje KANDYDATURĘ sygnału, nie trafia do trade journalu
(inaczej niż kill-switch): kill-switch jest zdarzeniem zależnym od equity i historii,
więc jego moment ma znaczenie w torze transakcji i musi być widoczny w `trades`. Bramka
kosztowa jest deterministyczną właściwością POJEDYNCZEJ świecy (geometria bariery vs
koszt), niezależną od equity — jej miejsce jest obok istniejącego filtra
`direction == 0` w `_collect_candidate_signals`, a licznik odrzuceń w
`folds_summary["n_signals_cost_gated"]`. Dzięki temu `backtest/metrics.py` (liczenie
Sharpe) nie wymaga żadnej zmiany ani nowego wyjątku w filtrze realnych transakcji.

DECYZJA — brak modyfikacji agents/labeling.py: PnL wymaga znać cenę wyjścia z pozycji.
Dla label +1/-1 to trywialne (entry ± atr_multiplier*atr_14). Dla label 0.0 (vertical
timeout) potrzeba `close` w świecy `t + exit_bar_offset` z PEŁNEGO datasetu — ale
agents.feature_miner.split_by_regime() robi reset_index(drop=True), co gubi możliwość
takiego lookupu pozycyjnego. Rozwiązanie: engine.py NIE wywołuje split_by_regime —
filtruje reżim własnym jednolinijkowym boolean maskiem, który ZACHOWUJE oryginalny
index (`df[df["regime"] == regime_name]`, bez reset_index). Ponieważ
compute_all_features/compute_triple_barrier_labels nie resetują indexu, a engine.py
na starcie wymusza czysty RangeIndex 0..N-1, `df.loc[original_index + exit_bar_offset,
"close"]` jest zawsze bezpiecznym, poprawnym lookupem.

DECYZJA — Sharpe NIE liczony tutaj: to jawnie zadanie C6.1 (Commit 6). `run_backtest`
zwraca surowe składniki (equity_curve, trades z net_pnl per trade, folds_summary).

DECYZJA — chronologia ponad reżimy: modele trenowane per-regime per-fold niezależnie,
ale sygnały z OBU reżimów są zbierane do jednej listy i SORTOWANE po timestamp PRZED
sekwencyjną symulacją equity — inaczej trades z trend/range (które przeplatają się w
czasie) dałyby błędną chronologię compoundingu.

DECYZJA — kill-switch w `trades`, nie w osobnym kluczu: sygnały stłumione przez
kill-switch dostają pełny wiersz w `trades` (position_size=0.0, exit_price=NaN,
equity_before==equity_after, kill_switch_active=True) zamiast osobnej listy
`kill_switch_events` — jeden ustrukturyzowany trade journal zamiast dwóch równoległych
źródeł prawdy o tym, co się działo w czasie.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from agents.feature_miner import (
    DEFAULT_CANDLES_PER_DAY,
    DEFAULT_RANGE_THRESHOLD,
    DEFAULT_TREND_THRESHOLD,
    compute_all_features,
)
from agents.labeling import (
    VERTICAL_BARRIER_CANDLES,
    ATR_MULTIPLIER,
    STEP_DAYS,
    TEST_WINDOW_DAYS,
    TRAIN_WINDOW_DAYS,
    compute_triple_barrier_labels,
    generate_walk_forward_folds,
)
from agents.ml_optimizer import (
    DEFAULT_SEED,
    DEFAULT_VALIDATION_FRACTION,
    EARLY_STOPPING_ROUNDS,
    MOMENTUM_FEATURES,
    NUM_BOOST_ROUND,
    REVERSION_FEATURES,
    best_iteration_or_last,
    predict_signal,
    train_regime_model,
)
from agents.risk_controller import (
    KILL_SWITCH_COOLDOWN_DAYS,
    KILL_SWITCH_DRAWDOWN_PCT,
    MIN_BARRIER_TO_COST_RATIO,
    check_kill_switch,
    compute_sizing,
    is_cost_feasible,
    should_rearm_kill_switch,
)
from backtest.costs import (
    CANDLE_MINUTES,
    MAKER,
    TAKER,
    exit_leg_for_reason,
    round_trip_cost_fraction,
    total_round_trip_cost,
)

# Commit 2.12 (Backlog Z6): modele wykonania. "taker_only" = market po obu stronach
# (model Commitów 5-2.11, zachowany do regresji baseline'u); "maker_limit" = wejście
# limitem, wyjście zależnie od powodu (TP limitem, SL/timeout marketem) — decyzja
# użytkownika 2026-09-21. Nazwane warianty, NIE pokrętło do strojenia.
# Commit 2.13: prog pewnosci. PRE-REJESTROWANA wartosc q=0.75 (gorny kwartyl) - ta sama
# definicja, na ktorej zmierzono monotoniczna zaleznosc trafnosci od signal_confidence
# przed programem. JEDNA wartosc, zero sweepu: przeszukiwanie po q byloby dobieraniem
# parametru po wyniku (CLAUDE.md zasada 1 i 4). Domyslnie None = wylaczone, zeby baseline
# pozostal odtwarzalny co do cyfry.
PREREGISTERED_CONFIDENCE_QUANTILE = 0.75

EXECUTION_TAKER_ONLY = "taker_only"
EXECUTION_MAKER_LIMIT = "maker_limit"
DEFAULT_EXECUTION_MODEL = EXECUTION_MAKER_LIMIT

# Zabezpieczenie przed degenerate foldami (np. bardzo mało danych w rzadkim reżimie —
# STATUS.md C2.5: "reżim trend może być rzadki"). To engineering safeguard, NIE parametr
# strategii/modelu — świadomie NIE w config/settings.yaml (w przeciwieństwie do
# hiperparametrów XGBoost albo kosztów, to nie jest coś do kalibracji w walk-forward).
MIN_TRAIN_ROWS = 30

DEFAULT_INITIAL_EQUITY = 10_000.0

TRADE_COLUMNS = [
    "timestamp",
    "regime",
    "fold_idx",
    "signal_direction",
    "signal_confidence",
    "entry_price",
    "exit_price",
    "position_size",
    "exit_bar_offset",
    "exit_reason",
    "gross_pnl",
    "cost",
    "net_pnl",
    "equity_before",
    "equity_after",
    "kill_switch_active",
]

REGIME_FEATURE_SETS = [("trend", MOMENTUM_FEATURES), ("range", REVERSION_FEATURES)]


def _collect_candidate_signals(
    df: pd.DataFrame,
    train_days: int,
    test_days: int,
    step_days: int,
    xgb_params: dict | None,
    num_boost_round: int,
    early_stopping_rounds: int,
    seed: int,
    min_train_rows: int,
    min_barrier_to_cost_ratio: float,
    regime_feature_sets: list[tuple[str, list[str]]],
    execution_model: str,
    confidence_quantile: float | None,
    validation_fraction: float | None,
    embargo_candles: int,
    fold_start_offset_days: float,
) -> tuple[list[dict], list[dict]]:
    """
    Trenuje model_momentum/model_reversion per walk-forward fold, generuje sygnały
    na foldach OOS (test). Zwraca (candidate_signals, folds_summary) — sygnały BEZ
    sizingu/PnL jeszcze (patrz decyzja o chronologii w docstringu modułu).

    Commit 2d: tu też wypada bramka wykonalności kosztowej
    (`agents.risk_controller.is_cost_feasible`) — obok istniejącego filtra
    `direction == 0`, bo oba są właściwościami POJEDYNCZEJ świecy, niezależnymi od
    equity i toru transakcji (patrz decyzja w docstringu modułu). Liczba sygnałów
    odrzuconych przez bramkę trafia do `folds_summary["n_signals_cost_gated"]` —
    audytowalność bez zaśmiecania trade journalu wierszami zerowymi.

    `regime_feature_sets` (Commit 2.8): przekazywane z `run_backtest`, NIE czytane
    z modułowej stałej `REGIME_FEATURE_SETS` bezpośrednio — pozwala
    `backtest/evaluate_feature_candidate.py` porównać baseline vs kandydata (jedna
    nowa cecha dodana do `MOMENTUM_FEATURES`/`REVERSION_FEATURES`) przez ten sam
    pipeline, bez duplikacji logiki (ten sam wzorzec co `trend_threshold`/
    `candles_per_day` w C2.5/C2.6).
    """
    # Bramka kosztowa działa PRZED wejściem w pozycję, więc nie zna powodu wyjścia, a ten
    # decyduje o typie nogi wyjścia. Zakładamy więc wyjście TAKER (jakby każda transakcja
    # kończyła się stopem/timeoutem) — konserwatywnie, bo zaniżony koszt przepuszczałby
    # sygnały, których bariera go nie pokrywa. Patrz docstring round_trip_cost_fraction.
    entry_leg_for_gate = MAKER if execution_model == EXECUTION_MAKER_LIMIT else TAKER
    cost_fraction = round_trip_cost_fraction(entry_leg=entry_leg_for_gate, exit_leg=TAKER)
    candidate_signals: list[dict] = []
    folds_summary: list[dict] = []

    for regime_name, feature_columns in regime_feature_sets:
        # Świadomie NIE agents.feature_miner.split_by_regime() — patrz decyzja w
        # docstringu modułu (potrzebujemy zachowanego oryginalnego indexu).
        regime_df = df[df["regime"] == regime_name]

        # Zabezpieczenie: regime_df puste (np. reżim "trend" nigdy nie wystąpił w tym
        # oknie danych — STATUS.md C2.5 wyraźnie flaguje to jako realne ryzyko).
        # generate_walk_forward_folds() zakłada niepuste df (Commit 4, nie modyfikujemy) —
        # ochrona przed IndexError na .iloc[-1] pustej serii timestamp.
        if len(regime_df) == 0:
            folds_summary.append(
                {
                    "regime": regime_name,
                    "fold_idx": None,
                    "train_start": None,
                    "train_end": None,
                    "test_start": None,
                    "test_end": None,
                    "skipped": True,
                    "skip_reason": "regime_df jest puste — brak świec sklasyfikowanych jako ten reżim",
                    "n_signals": 0,
                    "n_signals_cost_gated": 0,
                    "best_iteration": None,
                    "seed": seed,
                }
            )
            continue

        folds = generate_walk_forward_folds(
            regime_df,
            train_days,
            test_days,
            step_days,
            start_offset_days=fold_start_offset_days,
        )

        for fold_idx, fold in enumerate(folds):
            train_df = regime_df[fold["train_mask"]]
            test_df = regime_df[fold["test_mask"]]

            n_train_valid = len(train_df.dropna(subset=[*feature_columns, "label"]))
            n_test_valid = len(test_df.dropna(subset=[*feature_columns, "label"]))
            if n_train_valid < min_train_rows or n_test_valid < min_train_rows:
                folds_summary.append(
                    {
                        "regime": regime_name,
                        "fold_idx": fold_idx,
                        "train_start": fold["train_start"],
                        "train_end": fold["train_end"],
                        "test_start": fold["test_start"],
                        "test_end": fold["test_end"],
                        "skipped": True,
                        "skip_reason": f"n_train_valid={n_train_valid}, n_test_valid={n_test_valid} < min_train_rows={min_train_rows}",
                        "n_signals": 0,
                        "n_signals_cost_gated": 0,
                        "n_signals_confidence_gated": 0,
                        "confidence_threshold": None,
                        "best_iteration": None,
                        "seed": seed,
                    }
                )
                continue

            booster = train_regime_model(
                train_df,
                test_df,
                feature_columns,
                params=xgb_params,
                num_boost_round=num_boost_round,
                early_stopping_rounds=early_stopping_rounds,
                seed=seed,
                validation_fraction=validation_fraction,
                embargo_candles=embargo_candles,
            )
            confidence_threshold = _train_fold_confidence_threshold(
                booster, train_df, feature_columns, confidence_quantile
            )
            signals = predict_signal(booster, test_df, feature_columns)

            n_signals = 0
            n_signals_cost_gated = 0
            n_signals_confidence_gated = 0
            for idx, row in signals.iterrows():
                direction = row["signal_direction"]
                if direction == 0.0:
                    continue
                label = test_df.loc[idx, "label"]
                if pd.isna(label):
                    continue

                # Commit 2.13 — bramka pewności. Świadomie PRZED bramką kosztową:
                # to filtr JAKOŚCI SYGNAŁU, a tamta filtruje HANDLOWALNOŚĆ świecy.
                # Dzięki tej kolejności n_signals_cost_gated zachowuje znaczenie
                # "odrzucone przez koszt spośród sygnałów, w które i tak byśmy weszli".
                if (
                    confidence_threshold is not None
                    and row["signal_confidence"] < confidence_threshold
                ):
                    n_signals_confidence_gated += 1
                    continue

                # Commit 2d — bramka wykonalności kosztowej (patrz docstring tej
                # funkcji i agents/risk_controller.py). Odrzucenie NIE trafia do
                # trade journalu: to właściwość świecy, nie zdarzenie w torze equity.
                if not is_cost_feasible(
                    atr_14=test_df.loc[idx, "atr_14"],
                    entry_price=test_df.loc[idx, "close"],
                    cost_fraction=cost_fraction,
                    atr_multiplier=ATR_MULTIPLIER,
                    min_barrier_to_cost_ratio=min_barrier_to_cost_ratio,
                ):
                    n_signals_cost_gated += 1
                    continue

                candidate_signals.append(
                    {
                        "original_index": idx,
                        "timestamp": test_df.loc[idx, "timestamp"],
                        "regime": regime_name,
                        "fold_idx": fold_idx,
                        "signal_direction": direction,
                        "signal_confidence": row["signal_confidence"],
                        "entry_price": test_df.loc[idx, "close"],
                        "atr_14": test_df.loc[idx, "atr_14"],
                        "label": label,
                        "exit_bar_offset": test_df.loc[idx, "exit_bar_offset"],
                    }
                )
                n_signals += 1

            folds_summary.append(
                {
                    "regime": regime_name,
                    "fold_idx": fold_idx,
                    "train_start": fold["train_start"],
                    "train_end": fold["train_end"],
                    "test_start": fold["test_start"],
                    "test_end": fold["test_end"],
                    "skipped": False,
                    "skip_reason": None,
                    "n_signals": n_signals,
                    "n_signals_cost_gated": n_signals_cost_gated,
                    "n_signals_confidence_gated": n_signals_confidence_gated,
                    "confidence_threshold": confidence_threshold,
                    "best_iteration": best_iteration_or_last(booster),
                    "seed": seed,
                }
            )

    return candidate_signals, folds_summary


def _resolve_exit_price(df: pd.DataFrame, signal: dict) -> float:
    """
    Cena wyjścia z pozycji wg triple-barrier labelu (nie symulacja stop/TP z
    risk_controllera — patrz docstring modułu):
        label == 1.0  -> entry + ATR_MULTIPLIER * atr_14 (upper barrier)
        label == -1.0 -> entry - ATR_MULTIPLIER * atr_14 (lower barrier)
        label == 0.0  -> close przy vertical barrier (lookup do PEŁNEGO df, bo
                          regime_df zachowuje oryginalny index — patrz docstring modułu)
    """
    entry_price = signal["entry_price"]
    atr_14 = signal["atr_14"]
    label = signal["label"]

    if label == 1.0:
        return entry_price + ATR_MULTIPLIER * atr_14
    if label == -1.0:
        return entry_price - ATR_MULTIPLIER * atr_14

    exit_idx = signal["original_index"] + int(signal["exit_bar_offset"])
    return df.loc[exit_idx, "close"]


def _train_fold_confidence_threshold(
    booster,
    train_df: pd.DataFrame,
    feature_columns: list[str],
    confidence_quantile: float | None,
) -> float | None:
    """
    Commit 2.13: prog `signal_confidence` wyznaczony WYLACZNIE na foldzie TRENINGOWYM.

    Dlaczego nie na testowym: kwantyl policzony na zbiorze testowym oznaczalby dobranie
    progu pod dane, na ktorych mierzymy wynik - czyli dokladnie ten rodzaj przeciekania
    decyzji, ktory ma wykluczac walk-forward (CLAUDE.md zasada 1).

    ZASTRZEZENIE JAWNE (kierunek obciazenia): predykcje na `train_df` sa IN-SAMPLE, wiec
    model jest na nich przesadnie pewny. Prog z ich kwantyla jest zatem ZAWYZONY wzgledem
    rozkladu pewnosci na tescie, co przepuszcza MNIEJ transakcji, niz sugeruje nominalne
    q. Obciazenie dziala wiec na niekorzysc hipotezy (konserwatywnie), nie na jej korzysc.

    Zwraca None, gdy prog jest wylaczony albo gdy model nie wygenerowal na treningu ani
    jednego sygnalu kierunkowego (brak podstawy do policzenia kwantyla).
    """
    if confidence_quantile is None:
        return None
    train_signals = predict_signal(booster, train_df, feature_columns)
    directional = train_signals.loc[
        train_signals["signal_direction"] != 0.0, "signal_confidence"
    ]
    if directional.empty:
        return None
    return float(directional.quantile(confidence_quantile))


def _resolve_exit_reason(direction: float, label: float) -> str:
    """
    Commit 2.12 (Z6): powód wyjścia z pozycji — potrzebny, żeby wycenić nogę wyjścia
    (`backtest.costs.exit_leg_for_reason`).

    `label` mówi, KTÓRA bariera triple-barrier została trafiona (+1 górna, -1 dolna,
    0 bariera pionowa/timeout), a `direction` — po której stronie stoi pozycja. Dopiero
    ich ILOCZYN mówi, czy to było take-profit czy stop-loss: short (-1) na świecy
    z etykietą -1 to TP, ten sam short na etykiecie +1 to SL.
    """
    if label == 0.0 or pd.isna(label):
        return "timeout"
    return "tp" if direction * label > 0 else "sl"


def _execution_legs(execution_model: str, exit_reason: str) -> tuple[str, str]:
    """
    Typy zleceń (maker/taker) nogi wejścia i wyjścia dla danego modelu wykonania.

        taker_only  - obie nogi market. Model Commitów 5-2.11, zachowany do regresji
                      baseline'u (odtwarza wynik C2.10/C2.11 co do cyfry).
        maker_limit - wejście jako limit (maker); wyjście zależnie od powodu:
                      TP limit (maker), SL i timeout market (taker). Decyzja
                      użytkownika 2026-09-21, uzasadnienie w costs.exit_leg_for_reason.
    """
    if execution_model == EXECUTION_TAKER_ONLY:
        return TAKER, TAKER
    if execution_model == EXECUTION_MAKER_LIMIT:
        return MAKER, exit_leg_for_reason(exit_reason)
    raise ValueError(
        f"execution_model musi być jednym z "
        f"{(EXECUTION_TAKER_ONLY, EXECUTION_MAKER_LIMIT)}, dostałem: {execution_model!r}"
    )


def run_backtest(
    raw_ohlcv: pd.DataFrame,
    initial_equity: float = DEFAULT_INITIAL_EQUITY,
    train_days: int = TRAIN_WINDOW_DAYS,
    test_days: int = TEST_WINDOW_DAYS,
    step_days: int = STEP_DAYS,
    xgb_params: dict | None = None,
    num_boost_round: int = NUM_BOOST_ROUND,
    early_stopping_rounds: int = EARLY_STOPPING_ROUNDS,
    seed: int = DEFAULT_SEED,
    risk_controller_fn: Callable[..., dict] = compute_sizing,
    min_train_rows: int = MIN_TRAIN_ROWS,
    kill_switch_drawdown_pct: float = KILL_SWITCH_DRAWDOWN_PCT,
    kill_switch_cooldown_days: float = KILL_SWITCH_COOLDOWN_DAYS,
    min_barrier_to_cost_ratio: float = MIN_BARRIER_TO_COST_RATIO,
    trend_threshold: float = DEFAULT_TREND_THRESHOLD,
    range_threshold: float = DEFAULT_RANGE_THRESHOLD,
    candles_per_day: int = DEFAULT_CANDLES_PER_DAY,
    regime_feature_sets: list[tuple[str, list[str]]] | None = None,
    fold_start_offset_days: float = 0.0,
    candle_minutes: int = CANDLE_MINUTES,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    confidence_quantile: float | None = None,
    validation_fraction: float | None = DEFAULT_VALIDATION_FRACTION,
    embargo_candles: int | None = None,
    vertical_barrier_candles: int = VERTICAL_BARRIER_CANDLES,
) -> dict:
    """
    Pełny backtest Fazy 0: surowy OHLCV -> cechy+labels+regime -> walk-forward per
    reżim -> trening+predykcja (agents.ml_optimizer) -> sizing (risk_controller_fn)
    -> koszty (backtest.costs) -> equity curve + trade journal.

    Uproszczenie Fazy 0 (jawne): każdy sygnał sizowany NIEZALEŻNIE względem equity
    W MOMENCIE sygnału, PnL akumulowany sekwencyjnie w porządku chronologicznym —
    nie modeluje capital lock-up / nakładających się pozycji (żadna kolejka
    egzekucji). To świadome uproszczenie badawcze Fazy 0 — realna egzekucja to
    Faza 3 (LEAN, docs/rag/04).

    Args:
        raw_ohlcv: DataFrame [timestamp, open, high, low, close, volume],
            posortowany chronologicznie.
        initial_equity: equity startowe (USD).
        train_days/test_days/step_days: parametry walk-forward (agents.labeling) —
            nadpisywalne np. do szybszych testów na małych danych syntetycznych.
        xgb_params: nadpisania DEFAULT_XGB_PARAMS (agents.ml_optimizer).
        num_boost_round/early_stopping_rounds/seed: przekazywane do train_regime_model.
        risk_controller_fn: funkcja sizingu — domyślnie `agents.risk_controller.compute_sizing`
            (patrz docstring modułu), wstrzykiwalna (np. do testów).
        min_train_rows: minimalna liczba poprawnych wierszy (po dropna) w train/test
            danego foldu, żeby go nie pominąć.
        kill_switch_drawdown_pct: próg drawdown od peaku equity, powyżej którego
            kill-switch tłumi nowe sygnały (agents.risk_controller.check_kill_switch).
            Domyślnie KILL_SWITCH_DRAWDOWN_PCT (0.15) — nadpisywalne np. do testów.
        kill_switch_cooldown_days: ile dni ciągłej suppresji kill-switcha, zanim
            peak_equity zostanie zresetowany do bieżącego equity (re-arm) — patrz
            docstring modułu i agents.risk_controller.KILL_SWITCH_COOLDOWN_DAYS.
            Domyślnie 7.0 — nadpisywalne np. do testów (wartość mała -> szybszy re-arm).
        min_barrier_to_cost_ratio: Commit 2d — minimalny stosunek szerokości bariery
            zysku do kosztu round-trip, żeby sygnał w ogóle wszedł do gry
            (agents.risk_controller.is_cost_feasible). Domyślnie 2.0. Wartość 0.0
            całkowicie wyłącza bramkę (przydatne do odtworzenia baseline'u Commitu 2c).
        trend_threshold/range_threshold: Commit 2.5 — progi reguły regime
            (agents.feature_miner.classify_regime), domyślnie wartości startowe
            (0.7/0.3, config/settings.yaml sekcja `regime_rule`). Nadpisywalne, żeby
            `backtest/calibrate_regime_thresholds.py` mogło porównywać z góry
            zarejestrowanych kandydatów przez ten sam pipeline, bez duplikacji.
        candles_per_day: Commit 2.6 — konwersja jednostek dla `atr_pctrank_20d`
            (agents.feature_miner.compute_atr_pctrank_20d), NIE parametr hipotezy.
            Domyślnie 288 (timeframe 5m, config/settings.yaml sekcja `features`).
            Musi być nadpisane na 24 (1h) / 6 (4h) przy uruchamianiu na danych o innym
            timeframe (`backtest/checkpoint_timeframe_robustness.py`) — inaczej okno
            "~20 dni" przestaje reprezentować 20 dni kalendarzowych.
        regime_feature_sets: Commit 2.8 — nadpisanie `REGIME_FEATURE_SETS` (domyślnie
            `[("trend", MOMENTUM_FEATURES), ("range", REVERSION_FEATURES)]` z
            `agents.ml_optimizer`). `None` (domyślnie) = zachowanie bez zmian.
            Nadpisywalne, żeby `backtest/evaluate_feature_candidate.py` mogło
            porównać baseline vs kandydata (nowa cecha dodana do jednego z zestawów)
            przez ten sam pipeline, bez duplikacji logiki (CLAUDE.md zasada 4 — jedna
            cecha na raz, mierzona OOS).
        fold_start_offset_days: Commit 2.9 (Z1) — przesunięcie startu pierwszego okna
            walk-forward w dniach (agents.labeling.generate_walk_forward_folds).
            Używane WYŁĄCZNIE przez sweep stabilności fold-jitter
            (`backtest/checkpoint_lib.py`) — perturbacja ARBITRALNEGO wyrównania
            granic foldów, NIE parametr hipotezy. Domyślne 0.0 = zachowanie
            identyczne jak przed Commitem 2.9.
        candle_minutes: Commit 2.9 (Z11) — długość świecy w minutach, przekazywana do
            `backtest.costs.total_round_trip_cost` (składnik funding zależy od
            REALNEGO czasu trzymania pozycji, nie liczby świec). Konwersja jednostek,
            analogiczna do `candles_per_day` — NIE parametr hipotezy. Domyślnie 5
            (timeframe 5m); przy danych 1h/4h MUSI być nadpisane na 60/240, inaczej
            funding jest liczony 12×/48× za nisko (materialnie mały efekt, ~0,0004%
            nominału, ale to bug jednostek, nie świadome uproszczenie).

    Returns:
        {
          "equity_curve": pd.DataFrame [timestamp, equity], sortowane chronologicznie,
          "trades": pd.DataFrame z kolumnami TRADE_COLUMNS (trade journal, C5.6),
          "folds_summary": list[dict] (per regime/fold: zakres dat, n_signals,
              n_signals_cost_gated, best_iteration, czy pominięty i dlaczego),
          "final_equity": float,
        }
    """
    df = raw_ohlcv.reset_index(drop=True).copy()
    df = compute_all_features(
        df,
        trend_threshold=trend_threshold,
        range_threshold=range_threshold,
        candles_per_day=candles_per_day,
    )
    # Z22: horyzont etykiety jest parametrem, bo eksperyment na innym interwale wymaga
    # innego V (Z16/Z5b: na 4h spójny jest wyłącznie V=3). ATR_MULTIPLIER celowo NIE jest
    # parametryzowany — musiałby zmienić się JEDNOCZEŚNIE w risk_controller (CLAUDE.md
    # zasada 3), a ta runda go nie rusza.
    labels = compute_triple_barrier_labels(df, vertical_barrier_candles=vertical_barrier_candles)
    df["label"] = labels["label"]
    df["exit_bar_offset"] = labels["exit_bar_offset"]

    active_feature_sets = (
        REGIME_FEATURE_SETS if regime_feature_sets is None else regime_feature_sets
    )
    # Embargo MUSI iść za horyzontem etykiety: to dokładnie te wiersze treningu, których
    # etykieta sięga w okno testowe (Z17+Z21). Domyślne None wiąże je z V automatycznie,
    # żeby nie dało się ich rozjechać przez przeoczenie — ten sam typ ryzyka co mnożnik ATR.
    effective_embargo = vertical_barrier_candles if embargo_candles is None else embargo_candles
    candidate_signals, folds_summary = _collect_candidate_signals(
        df,
        train_days=train_days,
        test_days=test_days,
        step_days=step_days,
        xgb_params=xgb_params,
        num_boost_round=num_boost_round,
        early_stopping_rounds=early_stopping_rounds,
        seed=seed,
        min_train_rows=min_train_rows,
        min_barrier_to_cost_ratio=min_barrier_to_cost_ratio,
        regime_feature_sets=active_feature_sets,
        execution_model=execution_model,
        confidence_quantile=confidence_quantile,
        validation_fraction=validation_fraction,
        embargo_candles=effective_embargo,
        fold_start_offset_days=fold_start_offset_days,
    )

    # Chronologia ponad reżimy — patrz docstring modułu.
    candidate_signals.sort(key=lambda s: s["timestamp"])

    equity = initial_equity
    trades: list[dict] = []
    equity_curve: list[dict] = [
        {"timestamp": df["timestamp"].iloc[0], "equity": equity}
    ]
    peak_equity = equity
    # Commit 2c: moment pierwszego nieprzerwanego zadziałania kill-switcha (None, gdy
    # nieaktywny) — patrz docstring modułu.
    kill_switch_tripped_at: pd.Timestamp | None = None

    for signal in candidate_signals:
        direction = signal["signal_direction"]
        confidence = signal["signal_confidence"]
        entry_price = signal["entry_price"]
        atr_14 = signal["atr_14"]

        # Kill-switch: peak_equity to running max ZANIM ten sygnał zostanie
        # rozpatrzony (tylko przeszłość/teraźniejszość — brak lookahead). Re-check
        # dynamiczny co sygnał — patrz docstring modułu.
        peak_equity = max(peak_equity, equity)

        # Cooldown/re-arm (Commit 2c) — patrz docstring modułu. Musi być PRZED
        # check_kill_switch, żeby zresetowany peak_equity obowiązywał już w tej
        # iteracji. Decyzja "czy już czas" delegowana do czystej, testowanej funkcji
        # (agents.risk_controller.should_rearm_kill_switch).
        if should_rearm_kill_switch(
            kill_switch_tripped_at, signal["timestamp"], kill_switch_cooldown_days
        ):
            peak_equity = equity
            kill_switch_tripped_at = None

        if check_kill_switch(equity, peak_equity, kill_switch_drawdown_pct):
            if kill_switch_tripped_at is None:
                kill_switch_tripped_at = signal["timestamp"]
            trades.append(
                {
                    "timestamp": signal["timestamp"],
                    "regime": signal["regime"],
                    "fold_idx": signal["fold_idx"],
                    "signal_direction": direction,
                    "signal_confidence": confidence,
                    "entry_price": entry_price,
                    "exit_price": float("nan"),
                    "position_size": 0.0,
                    "exit_bar_offset": signal["exit_bar_offset"],
                    "exit_reason": None,
                    "gross_pnl": 0.0,
                    "cost": 0.0,
                    "net_pnl": 0.0,
                    "equity_before": equity,
                    "equity_after": equity,
                    "kill_switch_active": True,
                }
            )
            equity_curve.append({"timestamp": signal["timestamp"], "equity": equity})
            continue

        kill_switch_tripped_at = None

        sizing = risk_controller_fn(
            signal_direction=direction,
            signal_confidence=confidence,
            regime=signal["regime"],
            atr_14=atr_14,
            entry_price=entry_price,
            equity=equity,
        )
        position_size = sizing["position_size"]

        exit_price = _resolve_exit_price(df, signal)
        gross_pnl = direction * (exit_price - entry_price) * position_size

        exit_reason = _resolve_exit_reason(direction, signal["label"])
        entry_leg, exit_leg = _execution_legs(execution_model, exit_reason)

        notional = position_size * entry_price
        cost = total_round_trip_cost(
            notional=notional,
            holding_candles=signal["exit_bar_offset"],
            direction=direction,
            candle_minutes=candle_minutes,
            entry_leg=entry_leg,
            exit_leg=exit_leg,
        )
        net_pnl = gross_pnl - cost

        equity_before = equity
        equity = equity_before + net_pnl

        trades.append(
            {
                "timestamp": signal["timestamp"],
                "regime": signal["regime"],
                "fold_idx": signal["fold_idx"],
                "signal_direction": direction,
                "signal_confidence": confidence,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "position_size": position_size,
                "exit_bar_offset": signal["exit_bar_offset"],
                "exit_reason": exit_reason,
                "gross_pnl": gross_pnl,
                "cost": cost,
                "net_pnl": net_pnl,
                "equity_before": equity_before,
                "equity_after": equity,
                "kill_switch_active": False,
            }
        )
        equity_curve.append({"timestamp": signal["timestamp"], "equity": equity})

    trades_df = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    equity_curve_df = pd.DataFrame(equity_curve, columns=["timestamp", "equity"])

    return {
        "equity_curve": equity_curve_df,
        "trades": trades_df,
        "folds_summary": folds_summary,
        "final_equity": equity,
    }
