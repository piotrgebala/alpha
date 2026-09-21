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
    MIN_TRADES_FOR_HIT_RATE_CI,
    MIN_TRADES_FOR_N_EFF,
    break_even_hit_rate,
    classify_checkpoint,
    compute_fold_metrics,
    compute_hit_rate,
    compute_sharpe_ratio,
    compute_t_stat,
    compute_trade_returns,
    summarize_by_regime,
    summarize_edge_by_regime,
    summarize_pooled_by_regime,
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
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 100.0,
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            },
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": -50.0,
                "equity_before": 10_100.0,
                "kill_switch_active": False,
            },
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 25.0,
                "equity_before": 10_050.0,
                "kill_switch_active": False,
            },
        ]
    )
    returns = compute_trade_returns(trades)
    expected = [100.0 / 10_000.0, -50.0 / 10_100.0, 25.0 / 10_050.0]
    assert returns.tolist() == pytest.approx(expected)


def test_compute_trade_returns_excludes_kill_switch_rows() -> None:
    trades = _make_trades(
        [
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 100.0,
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            },
            # net_pnl absurdalnie duży, żeby test JAWNIE wykrył, gdyby wiersz nie został wykluczony.
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 999_999.0,
                "equity_before": 10_000.0,
                "kill_switch_active": True,
            },
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
    sharpe_zero_rf = compute_sharpe_ratio(
        returns, periods_per_year=252.0, risk_free_rate=0.0
    )
    sharpe_positive_rf = compute_sharpe_ratio(
        returns, periods_per_year=252.0, risk_free_rate=0.005
    )
    assert sharpe_positive_rf < sharpe_zero_rf


# ---------------------------------------------------------------------------
# Warstwa 2: compute_fold_metrics
# ---------------------------------------------------------------------------


def test_compute_fold_metrics_basic_grouping() -> None:
    trades = _make_trades(
        [
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 100.0,
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            },
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 50.0,
                "equity_before": 10_100.0,
                "kill_switch_active": False,
            },
            {
                "regime": "range",
                "fold_idx": 0,
                "net_pnl": -30.0,
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            },
            {
                "regime": "range",
                "fold_idx": 0,
                "net_pnl": -40.0,
                "equity_before": 9_970.0,
                "kill_switch_active": False,
            },
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
    wszystkie sygnały stłumione przez kill-switch) -> n_trades=0, sharpe=NaN, bez crasha.
    """
    trades = _make_trades(
        [
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 5.0,
                "equity_before": 10_000.0,
                "kill_switch_active": True,
            }
        ]
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
        [
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 5.0,
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            }
        ]
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


def _fold_metrics_from_sharpes(
    sharpes: list[float], regime: str = "trend"
) -> pd.DataFrame:
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
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False)
        | st.just(float("nan")),
        min_size=0,
        max_size=30,
    )
)
@settings(max_examples=50, deadline=None)
def test_classify_checkpoint_always_returns_valid_label(sharpes: list[float]) -> None:
    fold_metrics = (
        _fold_metrics_from_sharpes(sharpes)
        if sharpes
        else pd.DataFrame({"regime": [], "fold_idx": [], "sharpe": []})
    )
    result = classify_checkpoint(fold_metrics)
    assert result["classification"] in {"GO", "WARUNKOWY", "NO-GO"}


# ---------------------------------------------------------------------------
# Warstwa 1: compute_t_stat + summarize_pooled_by_regime (Commit 2.9, Z2+Z3)
# ---------------------------------------------------------------------------


def test_compute_t_stat_matches_manual_formula() -> None:
    returns = pd.Series([0.01, 0.02, -0.005, 0.015])
    expected = returns.mean() / (returns.std(ddof=1) / np.sqrt(len(returns)))
    assert compute_t_stat(returns) == pytest.approx(float(expected))


@pytest.mark.parametrize(
    "returns",
    [pd.Series([], dtype=float), pd.Series([0.01]), pd.Series([0.02, 0.02, 0.02])],
)
def test_compute_t_stat_nan_for_degenerate_input(returns: pd.Series) -> None:
    # <2 obserwacje albo zerowa wariancja — spójnie z compute_sharpe_ratio.
    assert math.isnan(compute_t_stat(returns))


def test_compute_fold_metrics_includes_t_stat_column() -> None:
    trades = _make_trades(
        [
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 100.0,
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            },
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": -50.0,
                "equity_before": 10_100.0,
                "kill_switch_active": False,
            },
            {
                "regime": "trend",
                "fold_idx": 0,
                "net_pnl": 25.0,
                "equity_before": 10_050.0,
                "kill_switch_active": False,
            },
        ]
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
    metrics = compute_fold_metrics(trades, folds_summary)
    assert "t_stat" in metrics.columns
    returns = compute_trade_returns(trades)
    assert metrics.iloc[0]["t_stat"] == pytest.approx(compute_t_stat(returns))


def test_summarize_pooled_by_regime_pools_across_folds_and_excludes_kill_switch() -> (
    None
):
    rng = np.random.default_rng(0)
    rows = []
    # 100 transakcji trend rozrzuconych po 5 foldach — pooling MUSI je połączyć.
    for i in range(100):
        rows.append(
            {
                "regime": "trend",
                "fold_idx": i % 5,
                "net_pnl": float(rng.normal(5.0, 20.0)),
                "equity_before": 10_000.0,
                "kill_switch_active": False,
            }
        )
    # Wiersz stłumiony przez kill-switch — musi zostać wykluczony z n_trades.
    rows.append(
        {
            "regime": "trend",
            "fold_idx": 0,
            "net_pnl": 999_999.0,
            "equity_before": 10_000.0,
            "kill_switch_active": True,
        }
    )
    trades = _make_trades(rows)

    summary = summarize_pooled_by_regime(trades)
    assert list(summary["regime"]) == ["trend"]
    row = summary.iloc[0]
    assert row["n_trades"] == 100
    returns = compute_trade_returns(trades)
    assert row["mean_return"] == pytest.approx(float(returns.mean()))
    assert row["t_stat"] == pytest.approx(compute_t_stat(returns))
    # Z3: N_eff policzone (n >= MIN_TRADES_FOR_N_EFF), w przedziale (0, n],
    # a t_stat_neff jest konserwatywny: |t_neff| <= |t| gdy n_eff <= n.
    assert 100 >= MIN_TRADES_FOR_N_EFF
    assert 0 < row["n_eff"] <= row["n_trades"]
    assert abs(row["t_stat_neff"]) <= abs(row["t_stat"]) + 1e-9


def test_summarize_pooled_by_regime_n_eff_nan_below_min_trades() -> None:
    rows = [
        {
            "regime": "range",
            "fold_idx": 0,
            "net_pnl": float(v),
            "equity_before": 10_000.0,
            "kill_switch_active": False,
        }
        for v in [10.0, -5.0, 7.0]  # 3 < MIN_TRADES_FOR_N_EFF
    ]
    summary = summarize_pooled_by_regime(_make_trades(rows))
    row = summary.iloc[0]
    assert row["n_trades"] == 3
    assert math.isnan(row["n_eff"])
    assert math.isnan(row["t_stat_neff"])
    # t_stat na pełnym n nadal policzalne.
    assert not math.isnan(row["t_stat"])


# ---------------------------------------------------------------------------
# Commit 2.11: instrumentacja edge'u — hit rate, break-even, rozbicie (2p-1)*B vs C
# ---------------------------------------------------------------------------


def _make_edge_trades(rows: list[dict]) -> pd.DataFrame:
    """Trades z kolumnami czytanymi przez compute_hit_rate/summarize_edge_by_regime."""
    defaults = {
        "regime": "range",
        "fold_idx": 0,
        "position_size": 1.0,
        "entry_price": 100.0,
        "exit_price": 101.0,
        "gross_pnl": 1.0,
        "cost": 0.14,
        "kill_switch_active": False,
    }
    if not rows:
        # Pusty journal ma w engine.py pełen zestaw TRADE_COLUMNS (pd.DataFrame(columns=...)),
        # więc pusty frame BEZ kolumn byłby artefaktem testu, nie realnym wejściem.
        return pd.DataFrame(columns=list(defaults))
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_break_even_hit_rate_matches_manual_formula() -> None:
    # p = 0.5 * (1 + C/B); C=0.0014, B=0.0028 -> 0.5 * 1.5 = 0.75
    assert break_even_hit_rate(0.0014, 0.0028) == pytest.approx(0.75)
    # bariera == koszt -> potrzeba 100% trafności
    assert break_even_hit_rate(0.0014, 0.0014) == pytest.approx(1.0)
    # koszt zerowy -> rzut monetą wystarcza
    assert break_even_hit_rate(0.0, 0.0028) == pytest.approx(0.5)


def test_break_even_hit_rate_reproduces_c2_10_range_diagnosis() -> None:
    """Regresja na realnym pomiarze z C2.10: range B=0.2707%, C=0.1399% -> ~75.8%."""
    assert break_even_hit_rate(0.001399, 0.002707) == pytest.approx(0.7584, abs=1e-3)


def test_break_even_hit_rate_nan_on_degenerate_barrier() -> None:
    assert math.isnan(break_even_hit_rate(0.0014, 0.0))
    assert math.isnan(break_even_hit_rate(0.0014, -0.001))
    assert math.isnan(break_even_hit_rate(0.0014, float("nan")))
    assert math.isnan(break_even_hit_rate(float("nan"), 0.0028))


def test_compute_hit_rate_counts_gross_wins_not_net() -> None:
    """Trafność liczy się z gross_pnl — netto mieszałoby jakość sygnału z kosztem."""
    trades = _make_edge_trades(
        [{"gross_pnl": 10.0, "net_pnl": -1.0}] * 3 + [{"gross_pnl": -10.0, "net_pnl": -20.0}]
    )
    result = compute_hit_rate(trades)
    assert result["n_trades"] == 4
    # 3/4 wygranych brutto, mimo że WSZYSTKIE są stratne netto.
    assert result["hit_rate"] == pytest.approx(0.75)


def test_compute_hit_rate_excludes_kill_switch_rows() -> None:
    trades = _make_edge_trades(
        [
            {"gross_pnl": 10.0},
            {"gross_pnl": 10.0},
            {"gross_pnl": 0.0, "kill_switch_active": True},
            {"gross_pnl": 0.0, "kill_switch_active": True},
        ]
    )
    result = compute_hit_rate(trades)
    assert result["n_trades"] == 2
    assert result["hit_rate"] == pytest.approx(1.0)


def test_compute_hit_rate_empty_is_nan_not_zero() -> None:
    trades = _make_edge_trades([{"gross_pnl": 0.0, "kill_switch_active": True}])
    result = compute_hit_rate(trades)
    assert result["n_trades"] == 0
    assert math.isnan(result["hit_rate"])
    assert math.isnan(result["z_stat"])


def test_compute_hit_rate_ci_suppressed_below_min_trades() -> None:
    """Poniżej progu: sam ułamek tak, ale CI/z NIE — aproksymacja normalna nie działa."""
    few = _make_edge_trades([{"gross_pnl": 1.0}] * (MIN_TRADES_FOR_HIT_RATE_CI - 1))
    result = compute_hit_rate(few)
    assert result["hit_rate"] == pytest.approx(1.0)
    assert math.isnan(result["z_stat"])
    assert math.isnan(result["ci_low"])

    enough = _make_edge_trades([{"gross_pnl": 1.0}] * MIN_TRADES_FOR_HIT_RATE_CI)
    assert not math.isnan(compute_hit_rate(enough)["z_stat"])


def test_compute_hit_rate_z_stat_is_zero_for_coin_flip() -> None:
    trades = _make_edge_trades([{"gross_pnl": 1.0}] * 50 + [{"gross_pnl": -1.0}] * 50)
    result = compute_hit_rate(trades)
    assert result["hit_rate"] == pytest.approx(0.5)
    assert result["z_stat"] == pytest.approx(0.0)


def test_summarize_edge_by_regime_splits_inequality_into_terms() -> None:
    """B, C i break_even_p liczone z kolumn journalu; margin = hit_rate - break_even_p."""
    # entry=100, exit=101 -> B = 1%; notional=100, cost=0.25 -> C = 0.25%.
    # break_even_p = 0.5*(1 + 0.25/1.0) = 0.625.
    trades = _make_edge_trades(
        [{"gross_pnl": 1.0, "cost": 0.25}] * 15 + [{"gross_pnl": -1.0, "cost": 0.25}] * 5
    )
    row = summarize_edge_by_regime(trades).iloc[0]
    assert row["barrier_pct"] == pytest.approx(0.01)
    assert row["cost_pct"] == pytest.approx(0.0025)
    assert row["break_even_p"] == pytest.approx(0.625)
    assert row["hit_rate"] == pytest.approx(0.75)
    assert row["margin"] == pytest.approx(0.125)


def test_summarize_edge_by_regime_one_row_per_regime() -> None:
    trades = _make_edge_trades(
        [{"regime": "range", "gross_pnl": 1.0}] * 3 + [{"regime": "trend", "gross_pnl": -1.0}] * 2
    )
    summary = summarize_edge_by_regime(trades).set_index("regime")
    assert sorted(summary.index) == ["range", "trend"]
    assert summary.loc["range", "hit_rate"] == pytest.approx(1.0)
    assert summary.loc["trend", "hit_rate"] == pytest.approx(0.0)


def test_summarize_edge_by_regime_survives_zero_width_barrier() -> None:
    """exit == entry (bariera zerowa) nie może wysadzić raportu ani dać inf."""
    trades = _make_edge_trades([{"gross_pnl": -1.0, "exit_price": 100.0}] * 5)
    row = summarize_edge_by_regime(trades).iloc[0]
    assert row["barrier_pct"] == pytest.approx(0.0)
    assert math.isnan(row["break_even_p"])
    assert math.isnan(row["margin"])


@given(
    cost=st.floats(min_value=1e-6, max_value=0.05),
    barrier=st.floats(min_value=1e-6, max_value=0.5),
)
@settings(max_examples=200, deadline=None)
def test_break_even_always_above_half_for_positive_cost(cost: float, barrier: float) -> None:
    """Przy dodatnim koszcie rzut monetą NIGDY nie wystarcza."""
    p = break_even_hit_rate(cost, barrier)
    assert p > 0.5


@given(
    cost_low=st.floats(min_value=1e-6, max_value=0.01),
    extra=st.floats(min_value=1e-6, max_value=0.01),
    barrier=st.floats(min_value=1e-3, max_value=0.5),
)
@settings(max_examples=200, deadline=None)
def test_break_even_monotonic_in_cost(cost_low: float, extra: float, barrier: float) -> None:
    """Droższe wykonanie => wymagana wyższa trafność. Niezmiennik kierunku, nie wartości."""
    assert break_even_hit_rate(cost_low + extra, barrier) > break_even_hit_rate(cost_low, barrier)


@given(n_wins=st.integers(min_value=0, max_value=60), n_losses=st.integers(min_value=0, max_value=60))
@settings(max_examples=100, deadline=None)
def test_hit_rate_within_unit_interval_and_matches_count(n_wins: int, n_losses: int) -> None:
    trades = _make_edge_trades(
        [{"gross_pnl": 1.0}] * n_wins + [{"gross_pnl": -1.0}] * n_losses
    )
    result = compute_hit_rate(trades)
    assert result["n_trades"] == n_wins + n_losses
    if n_wins + n_losses == 0:
        assert math.isnan(result["hit_rate"])
    else:
        assert 0.0 <= result["hit_rate"] <= 1.0
        assert result["hit_rate"] == pytest.approx(n_wins / (n_wins + n_losses))
