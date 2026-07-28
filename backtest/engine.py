"""
engine.py

Backtest Fazy 0: pętla sygnał -> risk_controller -> PnL z kosztami -> equity curve
(IMPLEMENTATION_PLAN.md §5 Commit 5). Orkiestruje cały pipeline na surowym OHLCV:
cechy (agents.feature_miner) -> triple-barrier labels (agents.labeling) -> split po
reżimie -> walk-forward foldy (agents.labeling) -> trening + predykcja per fold
(agents.ml_optimizer) -> sizing (risk_controller_fn) -> koszty (backtest.costs) ->
equity curve + trade journal (C5.6).

WAŻNE — `_placeholder_risk_controller` (C5.5, TYMCZASOWY):
`agents/risk_controller.py` to osobny Commit 5.5 (kontrakt formalny + kill-switch +
hypothesis property testy wymagane przez DoD). Ponieważ engine.py POTRZEBUJE jakiegoś
sizingu, żeby policzyć PnL już teraz, `_placeholder_risk_controller` implementuje
JUŻ udokumentowaną formułę (docs/rag/03_ryzyko_i_sizing.md) — size_risk/size_leverage/
min() + skalowanie confidence. Wstrzykiwany przez parametr `risk_controller_fn`, żeby
Commit 5.5 mógł podmienić na prawdziwy `agents/risk_controller.py` BEZ zmiany pętli
poniżej. Nie zamyka zadań C5.5.1-C5.5.4 z TASKS.md — te formalnie zostają dla
Commit 5.5 (osobny, testowany moduł + kill-switch, C5.5.5).

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
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from agents.feature_miner import compute_all_features
from agents.labeling import (
    ATR_MULTIPLIER,
    STEP_DAYS,
    TEST_WINDOW_DAYS,
    TRAIN_WINDOW_DAYS,
    compute_triple_barrier_labels,
    generate_walk_forward_folds,
)
from agents.ml_optimizer import (
    DEFAULT_SEED,
    EARLY_STOPPING_ROUNDS,
    MOMENTUM_FEATURES,
    NUM_BOOST_ROUND,
    REVERSION_FEATURES,
    predict_signal,
    train_regime_model,
)
from backtest.costs import total_round_trip_cost

# Zabezpieczenie przed degenerate foldami (np. bardzo mało danych w rzadkim reżimie —
# TASKS.md C2.5: "reżim trend może być rzadki"). To engineering safeguard, NIE parametr
# strategii/modelu — świadomie NIE w config/settings.yaml (w przeciwieństwie do
# hiperparametrów XGBoost albo kosztów, to nie jest coś do kalibracji w walk-forward).
MIN_TRAIN_ROWS = 30

DEFAULT_INITIAL_EQUITY = 10_000.0

# Sizing — wartości startowe (docs/rag/03_ryzyko_i_sizing.md), używane przez
# _placeholder_risk_controller. Formalne "źródło prawdy" dla tych wartości będzie
# agents/risk_controller.py (Commit 5.5).
RISK_PER_TRADE = 0.005  # 0.5% equity, fixed-fractional (NIE Kelly na tym etapie)
MAX_LEVERAGE = 3.0  # konserwatywnie, wartość startowa

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
    "gross_pnl",
    "cost",
    "net_pnl",
    "equity_before",
    "equity_after",
]

REGIME_FEATURE_SETS = [("trend", MOMENTUM_FEATURES), ("range", REVERSION_FEATURES)]


def _placeholder_risk_controller(
    signal_direction: float,
    signal_confidence: float,
    regime: str,
    atr_14: float,
    entry_price: float,
    equity: float,
    risk_per_trade: float = RISK_PER_TRADE,
    max_leverage: float = MAX_LEVERAGE,
    atr_multiplier: float = ATR_MULTIPLIER,
) -> dict:
    """
    Sizing tymczasowy (patrz docstring modułu) — implementuje formułę już w pełni
    udokumentowaną w docs/rag/03_ryzyko_i_sizing.md, TYMCZASOWO wewnątrz engine.py,
    do zastąpienia przez agents/risk_controller.py w Commit 5.5.

        size_risk     = (equity * risk_per_trade * signal_confidence) / (atr_multiplier * atr_14)
        size_leverage = (equity * max_leverage) / entry_price
        position_size = min(size_risk, size_leverage)

    `signal_confidence` skaluje WYŁĄCZNIE `risk_per_trade` (size_risk) — `size_leverage`
    zostaje twardym sufitem NIEZALEŻNYM od confidence, inaczej "leverage cap zawsze
    wygrywa" (CLAUDE.md zasada 5) przestałoby być prawdziwym hard cap.

    Returns:
        {"position_size": float, "stop_price": float, "take_profit_price": float}
        — kontrakt zgodny z docs/rag/03, choć engine.py liczy realizowane PnL z
        rzeczywistej ceny wyjścia (triple-barrier label), nie przez symulację
        względem stop_price/take_profit_price.
    """
    effective_risk_per_trade = risk_per_trade * signal_confidence
    size_risk = (equity * effective_risk_per_trade) / (atr_multiplier * atr_14)
    size_leverage = (equity * max_leverage) / entry_price
    position_size = min(size_risk, size_leverage)

    stop_price = entry_price - signal_direction * atr_multiplier * atr_14
    take_profit_price = entry_price + signal_direction * atr_multiplier * atr_14

    return {
        "position_size": position_size,
        "stop_price": stop_price,
        "take_profit_price": take_profit_price,
    }


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
) -> tuple[list[dict], list[dict]]:
    """
    Trenuje model_momentum/model_reversion per walk-forward fold, generuje sygnały
    na foldach OOS (test). Zwraca (candidate_signals, folds_summary) — sygnały BEZ
    sizingu/PnL jeszcze (patrz decyzja o chronologii w docstringu modułu).
    """
    candidate_signals: list[dict] = []
    folds_summary: list[dict] = []

    for regime_name, feature_columns in REGIME_FEATURE_SETS:
        # Świadomie NIE agents.feature_miner.split_by_regime() — patrz decyzja w
        # docstringu modułu (potrzebujemy zachowanego oryginalnego indexu).
        regime_df = df[df["regime"] == regime_name]

        # Zabezpieczenie: regime_df puste (np. reżim "trend" nigdy nie wystąpił w tym
        # oknie danych — TASKS.md C2.5 wyraźnie flaguje to jako realne ryzyko).
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
                    "best_iteration": None,
                    "seed": seed,
                }
            )
            continue

        folds = generate_walk_forward_folds(regime_df, train_days, test_days, step_days)

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
            )
            signals = predict_signal(booster, test_df, feature_columns)

            n_signals = 0
            for idx, row in signals.iterrows():
                direction = row["signal_direction"]
                if direction == 0.0:
                    continue
                label = test_df.loc[idx, "label"]
                if pd.isna(label):
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
                    "best_iteration": booster.best_iteration,
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
    risk_controller_fn: Callable[..., dict] = _placeholder_risk_controller,
    min_train_rows: int = MIN_TRAIN_ROWS,
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
        risk_controller_fn: funkcja sizingu — domyślnie `_placeholder_risk_controller`
            (TYMCZASOWY, patrz docstring modułu). Commit 5.5 wstrzyknie tu
            agents.risk_controller.compute_position_size (albo analogiczną).
        min_train_rows: minimalna liczba poprawnych wierszy (po dropna) w train/test
            danego foldu, żeby go nie pominąć.

    Returns:
        {
          "equity_curve": pd.DataFrame [timestamp, equity], sortowane chronologicznie,
          "trades": pd.DataFrame z kolumnami TRADE_COLUMNS (trade journal, C5.6),
          "folds_summary": list[dict] (per regime/fold: zakres dat, n_signals,
              best_iteration, czy pominięty i dlaczego),
          "final_equity": float,
        }
    """
    df = raw_ohlcv.reset_index(drop=True).copy()
    df = compute_all_features(df)
    labels = compute_triple_barrier_labels(df)
    df["label"] = labels["label"]
    df["exit_bar_offset"] = labels["exit_bar_offset"]

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
    )

    # Chronologia ponad reżimy — patrz docstring modułu.
    candidate_signals.sort(key=lambda s: s["timestamp"])

    equity = initial_equity
    trades: list[dict] = []
    equity_curve: list[dict] = [{"timestamp": df["timestamp"].iloc[0], "equity": equity}]

    for signal in candidate_signals:
        direction = signal["signal_direction"]
        confidence = signal["signal_confidence"]
        entry_price = signal["entry_price"]
        atr_14 = signal["atr_14"]

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

        notional = position_size * entry_price
        cost = total_round_trip_cost(
            notional=notional,
            holding_candles=signal["exit_bar_offset"],
            direction=direction,
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
                "gross_pnl": gross_pnl,
                "cost": cost,
                "net_pnl": net_pnl,
                "equity_before": equity_before,
                "equity_after": equity,
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
