"""
metrics.py

Commit 6 — Checkpoint go/no-go (IMPLEMENTATION_PLAN.md, docs/rag/03_ryzyko_i_sizing.md).
Sharpe po kosztach per fold, klasyfikacja GO/WARUNKOWY/NO-GO, rozbicie per reżim rynkowy.
`backtest.engine.run_backtest` celowo NIE liczy Sharpe'a (patrz docstring tego modułu) —
to jawnie zadanie C6.1-C6.4, zaimplementowane tutaj jako czyste, testowalne funkcje
operujące na `trades`/`folds_summary` zwróconych przez `run_backtest`.

METODOLOGIA SHARPE (ustalona z użytkownikiem, brak w docs/rag — trzeba było doprecyzować):
- risk-free rate = 0.
- Zwrot per trade = net_pnl / equity_before (NIE equity curve resamplowana kalendarzowo) —
  sygnały są rzadkie/nierównomierne w czasie (regime-gated), więc zwrot per-trade jest
  właściwą jednostką obserwacji, nie dzienna/godzinowa próbka equity.
- Wiersze z kill_switch_active=True są WYKLUCZONE z liczenia zwrotów — to nie są realne
  transakcje (position_size=0.0, equity_before==equity_after z definicji).
- Annualizacja: sqrt(trades_per_year), gdzie trades_per_year jest szacowane OSOBNO per
  fold z częstości transakcji w TYM foldzie: (n_trades / test_window_days) * 365.25.
  test_window_days pochodzi z folds_summary[i]["test_start"/"test_end"] tego foldu
  (nie globalna stała) — foldy przy granicy danych mogą być krótsze.
- Fold z <2 transakcjami lub zerową wariancją zwrotów -> Sharpe niedefiniowalny (NaN),
  wykluczony z mianownika w classify_checkpoint (raportowany osobno jako "insufficient data").

KRYTERIA KLASYFIKACJI (docs/rag/03_ryzyko_i_sizing.md, tabela GO/WARUNKOWY/NO-GO) —
progi metodologiczne, NIE parametry modelu/tradingu, więc świadomie NIE w
config/settings.yaml (analogicznie do MIN_TRAIN_ROWS w backtest/engine.py):
    GO:        >60% foldów (z policzalnym Sharpe) ma Sharpe > 0.5
    NO-GO:     >50% foldów (z policzalnym Sharpe) ma Sharpe <= 0 (większość)
    WARUNKOWY: wszystko pomiędzy (w tym niestabilny/mieszany znak między foldami)
Konstrukcyjnie rozłączne: >60% foldów z Sharpe>0.5 wyklucza >50% foldów z Sharpe<=0.

C6.4 (rozbicie per reżim rynkowy): interpretacja jako trend vs range (kolumna `regime`
w trades/folds_summary), NIE kalendarzowa — realny zakres danych (2025-07 -> 2026-07)
nie sięga 2023, więc dosłowna treść TASKS.md ("2023 vs 2024-25") nie pasuje do
faktycznie dostępnych danych. `summarize_by_regime` po prostu woła classify_checkpoint
osobno na podzbiorze fold_metrics dla każdego reżimu.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DAYS_PER_YEAR = 365.25

# Progi klasyfikacji checkpointu — docs/rag/03_ryzyko_i_sizing.md, tabela GO/WARUNKOWY/NO-GO.
SHARPE_THRESHOLD = 0.5
GO_FRACTION = 0.6
NO_GO_FRACTION = 0.5


def compute_trade_returns(trades: pd.DataFrame) -> pd.Series:
    """
    Zwrot per trade = net_pnl / equity_before. Wyklucza wiersze kill_switch_active
    (nie są realnymi transakcjami — patrz docstring modułu).

    Zachowuje oryginalny index `trades` (po odfiltrowaniu kill-switcha), żeby dało się
    łatwo dociąć per-fold maską boolean przed wywołaniem tej funkcji.
    """
    real_trades = trades.loc[~trades["kill_switch_active"]]
    return real_trades["net_pnl"] / real_trades["equity_before"]


def compute_sharpe_ratio(
    returns: pd.Series, periods_per_year: float, risk_free_rate: float = 0.0
) -> float:
    """
    Annualizowany Sharpe: (mean(returns) - risk_free_rate) / std(returns) * sqrt(periods_per_year).

    Zwraca NaN, gdy Sharpe jest niedefiniowalny: <2 obserwacje albo zerowa wariancja
    (dzielenie przez zero) — celowo NIE +/-inf, żeby dało się jednoznacznie odróżnić
    "brak wystarczających danych" od "policzalny, ale skrajny" wynik.
    """
    if len(returns) < 2:
        return float("nan")
    std = returns.std(ddof=1)
    if std == 0 or pd.isna(std):
        return float("nan")
    mean_excess = returns.mean() - risk_free_rate
    return float((mean_excess / std) * np.sqrt(periods_per_year))


def compute_fold_metrics(trades: pd.DataFrame, folds_summary: list[dict]) -> pd.DataFrame:
    """
    Per-fold (regime, fold_idx) Sharpe po kosztach — C6.1.

    Iteruje po folds_summary (a nie po grupach w trades), żeby foldy bez ŻADNYCH
    transakcji (skipped=True, albo fold_idx=None dla całkowicie pustego reżimu —
    patrz backtest/engine.py._collect_candidate_signals) też trafiły do wyniku z
    n_trades=0/sharpe=NaN, zamiast po prostu zniknąć z tabeli.

    Returns:
        DataFrame: regime, fold_idx, test_start, test_end, n_trades, mean_return,
        std_return, sharpe, skip_reason (passthrough z folds_summary, informacyjnie).
    """
    rows: list[dict] = []
    for fold in folds_summary:
        regime = fold["regime"]
        fold_idx = fold["fold_idx"]
        test_start = fold["test_start"]
        test_end = fold["test_end"]

        if fold_idx is None or test_start is None or test_end is None:
            rows.append(
                {
                    "regime": regime,
                    "fold_idx": fold_idx,
                    "test_start": test_start,
                    "test_end": test_end,
                    "n_trades": 0,
                    "mean_return": float("nan"),
                    "std_return": float("nan"),
                    "sharpe": float("nan"),
                    "skip_reason": fold.get("skip_reason"),
                }
            )
            continue

        fold_mask = (trades["regime"] == regime) & (trades["fold_idx"] == fold_idx)
        fold_returns = compute_trade_returns(trades.loc[fold_mask])
        n_trades = len(fold_returns)

        test_window_days = (test_end - test_start).total_seconds() / 86400.0
        if n_trades < 2 or test_window_days <= 0:
            sharpe = float("nan")
        else:
            trades_per_year = (n_trades / test_window_days) * DAYS_PER_YEAR
            sharpe = compute_sharpe_ratio(fold_returns, trades_per_year)

        rows.append(
            {
                "regime": regime,
                "fold_idx": fold_idx,
                "test_start": test_start,
                "test_end": test_end,
                "n_trades": n_trades,
                "mean_return": fold_returns.mean() if n_trades > 0 else float("nan"),
                "std_return": fold_returns.std(ddof=1) if n_trades > 1 else float("nan"),
                "sharpe": sharpe,
                "skip_reason": fold.get("skip_reason"),
            }
        )

    return pd.DataFrame(rows)


def classify_checkpoint(
    fold_metrics: pd.DataFrame,
    sharpe_threshold: float = SHARPE_THRESHOLD,
    go_fraction: float = GO_FRACTION,
    no_go_fraction: float = NO_GO_FRACTION,
) -> dict:
    """
    Klasyfikacja GO / WARUNKOWY / NO-GO wg kryteriów z docs/rag/03 — C6.2.

    Foldy z Sharpe=NaN (insufficient data) są wykluczone z mianownika ułamków, ale
    liczone osobno w n_total_folds/n_valid_folds dla przejrzystości raportu. Gdy
    n_valid_folds == 0 (zero foldów z policzalnym Sharpe w całym przebiegu) -> WARUNKOWY
    (ani kryterium GO, ani NO-GO nie jest formalnie spełnione przy braku jakichkolwiek
    danych — to NIE jest to samo co "Sharpe <= 0", więc NO-GO byłoby nieuprawnione).
    """
    n_total_folds = len(fold_metrics)
    valid = fold_metrics.dropna(subset=["sharpe"])
    n_valid_folds = len(valid)

    if n_valid_folds == 0:
        return {
            "classification": "WARUNKOWY",
            "n_valid_folds": 0,
            "n_total_folds": n_total_folds,
            "fraction_above_threshold": float("nan"),
            "fraction_le_zero": float("nan"),
            "fraction_positive_sign": float("nan"),
            "mean_sharpe": float("nan"),
        }

    fraction_above_threshold = float((valid["sharpe"] > sharpe_threshold).mean())
    fraction_le_zero = float((valid["sharpe"] <= 0).mean())
    fraction_positive_sign = float((valid["sharpe"] > 0).mean())
    mean_sharpe = float(valid["sharpe"].mean())

    if fraction_above_threshold > go_fraction:
        classification = "GO"
    elif fraction_le_zero > no_go_fraction:
        classification = "NO-GO"
    else:
        classification = "WARUNKOWY"

    return {
        "classification": classification,
        "n_valid_folds": n_valid_folds,
        "n_total_folds": n_total_folds,
        "fraction_above_threshold": fraction_above_threshold,
        "fraction_le_zero": fraction_le_zero,
        "fraction_positive_sign": fraction_positive_sign,
        "mean_sharpe": mean_sharpe,
    }


def summarize_by_regime(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Rozbicie klasyfikacji per reżim rynkowy (trend vs range) — C6.4. Jedna zagregowana
    liczba Sharpe po całym okresie maskuje niestabilność między reżimami (docs/rag/03) —
    ta funkcja woła classify_checkpoint OSOBNO na podzbiorze fold_metrics każdego reżimu.

    Returns:
        DataFrame: jeden wiersz per regime, kolumny = regime + klucze classify_checkpoint.
    """
    rows: list[dict] = []
    for regime, group in fold_metrics.groupby("regime"):
        result = classify_checkpoint(group)
        rows.append({"regime": regime, **result})
    return pd.DataFrame(rows)
