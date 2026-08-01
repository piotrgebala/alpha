"""
test_metrics.py

Testy dla backtest/metrics.py (Commit 6 — checkpoint go/no-go). Czysto syntetyczne
dane (bez sieci/ccxt/xgboost) — sprawdza formuły Sharpe'a, obsługę brzegowych
przypadków (foldy bez transakcji, zerowa wariancja) oraz klasyfikację GO/WARUNKOWY/
NO-GO wg progów z docs/rag/03_ryzyko_i_sizing.md. Realny przebieg na danych z Binance
to backtest/run_checkpoint.py (poza zakresem pytest — patrz jego docstring).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest.metrics import (
    classify_checkpoint,
    compute_fold_metrics,
    compute_sharpe_ratio,
    compute_trade_returns,
    summarize_by_regime,
)


def _make_trades(rows: list[dict]) -> pd.DataFrame:
    """Minimalny trades DataFrame — tylko kolumny czytane przez metrics.py."""
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Warstwa 1: compute_trade_returns
# ---------------------------------------------------------------------------


def test_compute_trade_returns_formula() -> None:
    trades = _make_trades(
        [
            {"regime": "trend", "fold_idx": 0, "net_pnl": 100.0, "equity_before": 10_000.0, "kill_switch_active": False},
            {"regime": "trend", "fold_idx": 0, "net_pnl": -50.0, "equity_before": 10_100.0, "kill_switch_active": False},
            {"regime": "trend", "fold_idx": 0, "net_pnl": 25.0, "equity_before": 10_050.0, "kill_switch_active": False},
        ]
    )
    returns = compute_trade_returns(trades)
    expected = [100.0 / 10_000.0, -50.0 / 10_100.0, 25.0 / 10_050.0]
    assert returns.tolist() == pytest.approx(expected)


def test_compute_trade_returns_excludes_kill_switch_rows() -> None:
    trades = _make_trades(
        [
            {"regime": "trend", "fold_idx": 0, "net_pnl": 100.0, "equity_before": 10_000.0, "kill_switch_active": False},
            # net_pnl absurdalnie duży, żeby test JAWNIE wykrył, gdyby wiersz nie został wykluczony.
            {"regime": "trend", "fold_idx": 0, "net_pnl": 999_999.0, "equity_before": 10_000.0, "kill_switch_active": True},
        ]
    )
    returns = compute_trade_returns(trades)
    assert len(returns) == 1
    assert returns.iloc[0] == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# Warstwa 1: compute_sharpe_ratio
# ---------------------------------------------------------------------------


def test_compute_sharpe_ratio_matches_manual_formula() -> None:
    returns = pd.Series([0.01, 0.02, -0.005, 0.015])
    periods_per_year = 252.0
    sharpe = compute_sharpe_ratio(returns, periods_per_year)
    expected = (returns.mean() / returns.std(ddof=1)) * np.sqrt(periods_per_year)
    assert sharpe == pytest.approx(expected)


@pytest.mark.parametrize("n_obs", [0, 1])
def test_compute_sharpe_ratio_nan_below_two_observations(n_obs: int) -> None:
    returns = pd.Series([0.01] * n_obs)
    assert math.isnan(compute_sharpe_ratio(returns, periods_per_year=252.0))


def test_compute_sharpe_ratio_nan_zero_variance() -> None:
    returns = pd.Series([0.01, 0.01, 0.01])
    assert math.isnan(compute_sharpe_ratio(returns, periods_per_year=252.0))


def test_compute_sharpe_ratio_risk_free_rate_lowers_result() -> None:
    returns = pd.Series([0.01, 0.02, 0.015, 0.005])
    sharpe_zero_rf = compute_sharpe_ratio(returns, periods_per_year=252.0, risk_free_rate=0.0)
    sharpe_positive_rf = compute_sharpe_ratio(returns, periods_per_year=252.0, risk_free_rate=0.005)
    assert sharpe_positive_rf < sharpe_zero_rf


# ---------------------------------------------------------------------------
# Warstwa 2: compute_fold_metrics
# ---------------------------------------------------------------------------


def test_compute_fold_metrics_basic_grouping() -> None:
    trades = _make_trades(
        [
            {"regime": "trend", "fold_idx": 0, "net_pnl": 100.0, "equity_before": 10_000.0, "kill_switch_active": False},
            {"regime": "trend", "fold_idx": 0, "net_pnl": 50.0, "equity_before": 10_100.0, "kill_switch_active": False},
            {"regime": "range", "fold_idx": 0, "net_pnl": -30.0, "equity_before": 10_000.0, "kill_switch_active": False},
            {"regime": "range", "fold_idx": 0, "net_pnl": -40.0, "equity_before": 9_970.0, "kill_switch_active": False},
        ]
    )
    folds_summary = [
        {
            "regime": "trend",
            "fold_idx": 0,
            "test_start": pd.Timestamp("2026-01-01", tz="UTC"),
            "test_end": pd.Timestamp("2026-01-15", tz="UTC"),
            "skip_reason": None,
        },
        {
            "regime": "range",
            "fold_idx": 0,
            "test_start": pd.Timestamp("2026-01-01", tz="UTC"),
            "test_end": pd.Timestamp("2026-01-15", tz="UTC"),
            "skip_reason": None,
        },
    ]

    fold_metrics = compute_fold_metrics(trades, folds_summary)

    assert len(fold_metrics) == 2
    trend_row = fold_metrics[fold_metrics["regime"] == "trend"].iloc[0]
    range_row = fold_metrics[fold_metrics["regime"] == "range"].iloc[0]
    assert trend_row["n_trades"] == 2
    assert range_row["n_trades"] == 2
    assert trend_row["sharpe"] > 0  # same-sign dodatnie zwroty
    assert range_row["sharpe"] < 0  # same-sign ujemne zwroty


def test_compute_fold_metrics_whole_regime_skip_none_fold_idx() -> None:
    """folds_summary entry z fold_idx=None (regime_df całkowicie puste — patrz
    backtest/engine.py._collect_candidate_signals) nie ma odpowiadających transakcji."""
    trades = _make_trades([])
    folds_summary = [
        {
            "regime": "trend",
            "fold_idx": None,
            "test_start": None,
            "test_end": None,
            "skip_reason": "regime_df jest puste",
        }
    ]
    fold_metrics = compute_fold_metrics(trades, folds_summary)
    assert len(fold_metrics) == 1
    row = fold_metrics.iloc[0]
    assert row["n_trades"] == 0
    assert math.isnan(row["sharpe"])
    assert row["skip_reason"] == "regime_df jest puste"


def test_compute_fold_metrics_fold_with_zero_matching_trades() -> None:
    """fold_idx obecny w folds_summary, ale zero pasujących wierszy w trades (np.
    wszystkie sygnały stłumione przez kill-switch) -> n_trades=0, sharpe=NaN, bez crasha."""
    trades = _make_trades(
        [{"regime": "trend", "fold_idx": 0, "net_pnl": 5.0, "equity_before": 10_000.0, "kill_switch_active": True}]
    )
    folds_summary = [
        {
            "regime": "trend",
            "fold_idx": 0,
            "test_start": pd.Timestamp("2026-01-01", tz="UTC"),
            "test_end": pd.Timestamp("2026-01-15", tz="UTC"),
            "skip_reason": None,
        }
    ]
    fold_metrics = compute_fold_metrics(trades, folds_summary)
    assert fold_metrics.iloc[0]["n_trades"] == 0
    assert math.isnan(fold_metrics.iloc[0]["sharpe"])


def test_compute_fold_metrics_single_trade_insufficient() -> None:
    trades = _make_trades(
        [{"regime": "trend", "fold_idx": 0, "net_pnl": 5.0, "equity_before": 10_000.0, "kill_switch_active": False}]
    )
    folds_summary = [
        {
            "regime": "trend",
            "fold_idx": 0,
            "test_start": pd.Timestamp("2026-01-01", tz="UTC"),
            "test_end": pd.Timestamp("2026-01-15", tz="UTC"),
            "skip_reason": None,
        }
    ]
    fold_metrics = compute_fold_metrics(trades, folds_summary)
    assert fold_metrics.iloc[0]["n_trades"] == 1
    assert math.isnan(fold_metrics.iloc[0]["sharpe"])


# ---------------------------------------------------------------------------
# Warstwa 2: classify_checkpoint
# ---------------------------------------------------------------------------


def _fold_metrics_from_sharpes(sharpes: list[float], regime: str = "trend") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "regime": [regime] * len(sharpes),
            "fold_idx": list(range(len(sharpes))),
            "sharpe": sharpes,
        }
    )


def test_classify_checkpoint_go() -> None:
    # 7/10 > 0.5 (70% > 60%), reszta ujemna ale mniejszościowa.
    sharpes = [1.0] * 7 + [-0.2] * 3
    result = classify_checkpoint(_fold_metrics_from_sharpes(sharpes))
    assert result["classification"] == "GO"
    assert result["fraction_above_threshold"] == pytest.approx(0.7)


def test_classify_checkpoint_no_go() -> None:
    # 7/10 <= 0 (70% > 50%).
    sharpes = [-0.3] * 7 + [1.0] * 3
    result = classify_checkpoint(_fold_metrics_from_sharpes(sharpes))
    assert result["classification"] == "NO-GO"
    assert result["fraction_le_zero"] == pytest.approx(0.7)


def test_classify_checkpoint_warunkowy_middle_ground() -> None:
    # 4/10 > 0.5 (40%, nie GO), 3/10 <= 0 (30%, nie NO-GO) -> WARUNKOWY.
    sharpes = [1.0] * 4 + [0.2] * 3 + [-0.1] * 3
    result = classify_checkpoint(_fold_metrics_from_sharpes(sharpes))
    assert result["classification"] == "WARUNKOWY"


def test_classify_checkpoint_boundary_exactly_at_go_fraction_not_go() -> None:
    # Dokładnie 60% (6/10) > 0.5 -> NIE spełnia ostrego ">" 60% -> WARUNKOWY, nie GO.
    sharpes = [1.0] * 6 + [0.1] * 4
    result = classify_checkpoint(_fold_metrics_from_sharpes(sharpes))
    assert result["fraction_above_threshold"] == pytest.approx(0.6)
    assert result["classification"] == "WARUNKOWY"


def test_classify_checkpoint_boundary_exactly_at_no_go_fraction_not_no_go() -> None:
    # Dokładnie 50% (5/10) <= 0 -> NIE spełnia ostrego ">" 50% -> WARUNKOWY, nie NO-GO.
    sharpes = [-0.3] * 5 + [0.3] * 5
    result = classify_checkpoint(_fold_metrics_from_sharpes(sharpes))
    assert result["fraction_le_zero"] == pytest.approx(0.5)
    assert result["classification"] == "WARUNKOWY"


def test_classify_checkpoint_zero_valid_folds() -> None:
    fold_metrics = _fold_metrics_from_sharpes([float("nan"), float("nan")])
    result = classify_checkpoint(fold_metrics)
    assert result["classification"] == "WARUNKOWY"
    assert result["n_valid_folds"] == 0
    assert result["n_total_folds"] == 2


def test_classify_checkpoint_excludes_nan_from_denominator() -> None:
    sharpes = [1.0, 1.0, 1.0, float("nan"), float("nan")]
    result = classify_checkpoint(_fold_metrics_from_sharpes(sharpes))
    assert result["n_total_folds"] == 5
    assert result["n_valid_folds"] == 3
    assert result["fraction_above_threshold"] == pytest.approx(1.0)
    assert result["classification"] == "GO"


# ---------------------------------------------------------------------------
# Warstwa 2: summarize_by_regime
# ---------------------------------------------------------------------------


def test_summarize_by_regime_independent_classification() -> None:
    trend = _fold_metrics_from_sharpes([1.0] * 7 + [-0.2] * 3, regime="trend")
    range_ = _fold_metrics_from_sharpes([-0.3] * 7 + [1.0] * 3, regime="range")
    combined = pd.concat([trend, range_], ignore_index=True)

    summary = summarize_by_regime(combined)

    assert set(summary["regime"]) == {"trend", "range"}
    trend_row = summary[summary["regime"] == "trend"].iloc[0]
    range_row = summary[summary["regime"] == "range"].iloc[0]
    assert trend_row["classification"] == "GO"
    assert range_row["classification"] == "NO-GO"


# ---------------------------------------------------------------------------
# Warstwa 3: hypothesis property-based
# ---------------------------------------------------------------------------


@given(
    sharpes=st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False) | st.just(float("nan")),
        min_size=0,
        max_size=30,
    )
)
@settings(max_examples=50, deadline=None)
def test_classify_checkpoint_always_returns_valid_label(sharpes: list[float]) -> None:
    fold_metrics = _fold_metrics_from_sharpes(sharpes) if sharpes else pd.DataFrame(
        {"regime": [], "fold_idx": [], "sharpe": []}
    )
    result = classify_checkpoint(fold_metrics)
    assert result["classification"] in {"GO", "WARUNKOWY", "NO-GO"}
