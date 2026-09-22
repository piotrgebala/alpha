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
    expected_trades,
    measurability_report,
    min_detectable_hit_rate,
    observed_wald_ci,
    required_trades,
    wald_half_width,
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
        "exit_reason": "tp",
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


# ---------------------------------------------------------------------------
# Z18 (Backlog II): jedna definicja `p` + rozbicie per typ wyjścia
# ---------------------------------------------------------------------------


def test_canonical_hit_rate_counts_profitable_timeouts_as_wins() -> None:
    """
    SEDNO Z18: `direction*label>0` liczyłoby KAŻDY timeout jako porażkę (bo label==0),
    także zamknięty z zyskiem. Definicja kanoniczna `gross_pnl>0` tego nie robi.
    """
    trades = _make_edge_trades(
        [{"gross_pnl": 1.0, "exit_reason": "tp"}] * 5
        + [{"gross_pnl": 1.0, "exit_reason": "timeout"}] * 3   # zyskowne timeouty
        + [{"gross_pnl": -1.0, "exit_reason": "sl"}] * 2
    )
    result = compute_hit_rate(trades)
    assert result["hit_rate"] == pytest.approx(0.8)  # 8/10, NIE 5/10
    # gdyby liczyć "tylko trafienia bariery poziomej", byłoby 5/10 — różnica 30 pp
    assert result["hit_rate"] != pytest.approx(0.5)


def test_edge_report_splits_hit_rate_by_exit_reason() -> None:
    trades = _make_edge_trades(
        [{"gross_pnl": 1.0, "exit_reason": "tp"}] * 6
        + [{"gross_pnl": -1.0, "exit_reason": "sl"}] * 4
        + [{"gross_pnl": 1.0, "exit_reason": "timeout"}] * 1
        + [{"gross_pnl": -1.0, "exit_reason": "timeout"}] * 9
    )
    row = summarize_edge_by_regime(trades).iloc[0]
    assert row["share_timeout"] == pytest.approx(0.5)
    assert row["hit_rate_barrier"] == pytest.approx(0.6)   # 6/10
    assert row["hit_rate_timeout"] == pytest.approx(0.1)   # 1/10
    assert row["hit_rate"] == pytest.approx(0.35)          # 7/20 — średnia ważona


def test_edge_report_timeout_columns_are_nan_without_exit_reason() -> None:
    """Journal sprzed C2.12 nie ma kolumny `exit_reason` — raport nie może się wywalić."""
    trades = _make_edge_trades([{"gross_pnl": 1.0}] * 5).drop(columns=["exit_reason"])
    row = summarize_edge_by_regime(trades).iloc[0]
    assert math.isnan(row["share_timeout"])
    assert math.isnan(row["hit_rate_barrier"])
    assert not math.isnan(row["hit_rate"])  # kanoniczna miara nadal policzalna


def test_edge_report_all_barrier_exits_gives_nan_timeout_rate() -> None:
    trades = _make_edge_trades([{"gross_pnl": 1.0, "exit_reason": "tp"}] * 5)
    row = summarize_edge_by_regime(trades).iloc[0]
    assert row["share_timeout"] == pytest.approx(0.0)
    assert math.isnan(row["hit_rate_timeout"])
    assert row["hit_rate_barrier"] == pytest.approx(1.0)


@given(
    n_tp=st.integers(min_value=0, max_value=40),
    n_sl=st.integers(min_value=0, max_value=40),
    n_to_win=st.integers(min_value=0, max_value=40),
    n_to_loss=st.integers(min_value=0, max_value=40),
)
@settings(max_examples=150, deadline=None)
def test_overall_hit_rate_is_weighted_average_of_components(
    n_tp: int, n_sl: int, n_to_win: int, n_to_loss: int
) -> None:
    """Niezmiennik: kanoniczna trafność = średnia ważona składowych per typ wyjścia."""
    trades = _make_edge_trades(
        [{"gross_pnl": 1.0, "exit_reason": "tp"}] * n_tp
        + [{"gross_pnl": -1.0, "exit_reason": "sl"}] * n_sl
        + [{"gross_pnl": 1.0, "exit_reason": "timeout"}] * n_to_win
        + [{"gross_pnl": -1.0, "exit_reason": "timeout"}] * n_to_loss
    )
    n_total = n_tp + n_sl + n_to_win + n_to_loss
    if n_total == 0:
        return
    row = summarize_edge_by_regime(trades).iloc[0]
    n_barrier, n_timeout = n_tp + n_sl, n_to_win + n_to_loss
    expected = (
        (row["hit_rate_barrier"] * n_barrier if n_barrier else 0.0)
        + (row["hit_rate_timeout"] * n_timeout if n_timeout else 0.0)
    ) / n_total
    assert row["hit_rate"] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Z19 (Backlog II): moc statystyczna pomiaru trafnosci
# ---------------------------------------------------------------------------


def test_wald_half_width_matches_manual_formula() -> None:
    # 1.959964 * sqrt(0.25 / 100) = 1.959964 * 0.05
    assert wald_half_width(100) == pytest.approx(1.959964 * 0.05, rel=1e-6)


def test_wald_half_width_shrinks_with_sample_size() -> None:
    """Czterokrotnie wieksza proba => polowa szerokosci przedzialu."""
    assert wald_half_width(400) == pytest.approx(wald_half_width(100) / 2.0, rel=1e-9)


def test_wald_half_width_nan_for_empty_sample() -> None:
    assert math.isnan(wald_half_width(0))
    assert math.isnan(wald_half_width(-5))


def test_min_detectable_hit_rate_is_break_even_plus_margin() -> None:
    """Trzeba zmierzyc WIECEJ niz break-even, bo pomiar ma niepewnosc."""
    be = 0.5274
    p_min = min_detectable_hit_rate(be, n_trades=1551)
    assert p_min > be
    assert p_min == pytest.approx(be + wald_half_width(1551))


def test_min_detectable_hit_rate_converges_to_break_even_for_huge_sample() -> None:
    be = 0.55
    assert min_detectable_hit_rate(be, n_trades=10_000_000) == pytest.approx(be, abs=1e-3)


def test_min_detectable_hit_rate_nan_on_degenerate_input() -> None:
    assert math.isnan(min_detectable_hit_rate(0.55, n_trades=0))
    assert math.isnan(min_detectable_hit_rate(float("nan"), n_trades=100))


def test_required_trades_reproduces_z19_four_hour_case() -> None:
    """Regresja na liczbie, ktora przesadzila o werdykcie Z19 dla 4h."""
    assert required_trades(0.5274, 0.5) == pytest.approx(2608, rel=0.01)


def test_required_trades_explodes_for_vanishing_effect() -> None:
    """Im mniejsza roznica do wykrycia, tym wieksza potrzebna proba."""
    assert required_trades(0.51, 0.5) > required_trades(0.55, 0.5)
    assert required_trades(0.5, 0.5) == float("inf")


def test_required_trades_nan_outside_unit_interval() -> None:
    assert math.isnan(required_trades(1.5, 0.5))
    assert math.isnan(required_trades(0.5, 0.0))


@given(
    n_low=st.integers(min_value=1, max_value=5000),
    extra=st.integers(min_value=1, max_value=5000),
)
@settings(max_examples=150, deadline=None)
def test_half_width_monotonically_decreasing_in_n(n_low: int, extra: int) -> None:
    assert wald_half_width(n_low) >= wald_half_width(n_low + extra)


@given(
    be=st.floats(min_value=0.51, max_value=0.9),
    n=st.integers(min_value=30, max_value=100_000),
)
@settings(max_examples=150, deadline=None)
def test_min_detectable_always_above_break_even(be: float, n: int) -> None:
    """Niezmiennik: nigdy nie wolno orzec rentownosci przy trafnosci rownej progowi."""
    assert min_detectable_hit_rate(be, n) > be


# ---------------------------------------------------------------------------
# K2 — MIERZALNOSC hipotezy PRZED eksperymentem
# (runs/2026-09-22_k2-naprawa-abstynencji/README.md, sprostowanie 1)
# ---------------------------------------------------------------------------


def test_expected_trades_counts_decisions_not_candles() -> None:
    """
    Sedno wniosku skumulowanego 19: liczba OBSERWACJI to nie liczba TRANSAKCJI.

    1 000 swiec przy abstynencji 66,58% (rozklad klas z H2.1) daje ~334 decyzje, a nie
    1 000. Dokladnie ten czlon brakowal w rachunkach mocy S1, S1b i H2.1 - trzy razy
    ten sam blad.
    """
    assert expected_trades(1_000, abstention_rate=0.0) == pytest.approx(1_000.0)
    assert expected_trades(1_000, abstention_rate=0.6658) == pytest.approx(334.2)
    assert expected_trades(1_000, abstention_rate=1.0) == pytest.approx(0.0)


def test_expected_trades_applies_remaining_gates_multiplicatively() -> None:
    """`admission_rate` to przezywalnosc pozostalych bramek (kosztowa, pewnosci, kill-switch)."""
    assert expected_trades(1_000, 0.5, admission_rate=0.5) == pytest.approx(250.0)
    assert expected_trades(1_000, 0.5, admission_rate=1.0) == pytest.approx(500.0)


def test_expected_trades_reproduces_the_h21_surprise() -> None:
    """
    Kontrola na REALNEJ liczbie: H2.1 dostal n=98 przy abstynencji 99,32%.

    Gdyby ta funkcja istniala przed H2.1, rachunek mocy pokazalby to Z GORY. Liczba swiec
    ocenionych w H2.1 to ~14 400; przy zmierzonej abstynencji wychodzi ~98.
    """
    assert expected_trades(14_400, abstention_rate=0.9932) == pytest.approx(98, abs=1.5)


@pytest.mark.parametrize(
    "n_rows, abstention, admission",
    [(-1, 0.5, 1.0), (100, -0.01, 1.0), (100, 1.01, 1.0), (100, 0.5, 1.5), (100, 0.5, -0.1)],
)
def test_expected_trades_returns_nan_outside_domain(n_rows, abstention, admission) -> None:
    """Spojne z konwencja NaN w compute_sharpe_ratio/compute_t_stat - nigdy cicha liczba."""
    assert math.isnan(expected_trades(n_rows, abstention, admission))


def test_expected_trades_returns_nan_for_nan_inputs() -> None:
    assert math.isnan(expected_trades(100, float("nan")))
    assert math.isnan(expected_trades(100, 0.5, float("nan")))


def test_detectability_band_depends_only_on_n() -> None:
    """
    Sprostowanie 1 z pre-rejestracji K2, przeliczone DRUGA DROGA.

    "Prog wykrywalnosci 58,2%" z K1 to artefakt siatki `q`. Wlasciwoscia przyrzadu jest
    szerokosc pasma "oplacalne, ale NIEWIDZIALNE" = z*sqrt(0,25/n) - zalezy WYLACZNIE od n,
    nie od progu oplacalnosci. Ten test pilnuje tego wprost: przy tym samym n dwie rozne
    wartosci break-even daja te sama szerokosc pasma.
    """
    for n in (50, 345, 7_687):
        szerokosc_a = min_detectable_hit_rate(0.50, n) - 0.50
        szerokosc_b = min_detectable_hit_rate(0.55, n) - 0.55
        assert szerokosc_a == pytest.approx(szerokosc_b)
        assert szerokosc_a == pytest.approx(wald_half_width(n))


def test_detectability_band_matches_preregistered_table() -> None:
    """
    KOTWICA LICZBOWA: tabela cytowana w pre-rejestracji K2, wpisana literalami.

    Gdyby ktos zmienil `wald_half_width` albo `Z_TWO_SIDED_95`, te liczby przestalyby sie
    zgadzac z tym, co juz jest opublikowane w `runs/` - i test to pokaze, zamiast pozwolic
    dokumentacji rozjechac sie z kodem po cichu.
    """
    oczekiwane_pp = {50: 13.86, 98: 9.90, 105: 9.56, 220: 6.61, 345: 5.28, 787: 3.49,
                     4_843: 1.41, 7_687: 1.12}
    for n, pp in oczekiwane_pp.items():
        assert 100.0 * wald_half_width(n) == pytest.approx(pp, abs=0.01), f"n={n}"


def test_measurability_report_says_measurable_when_effect_clears_the_band() -> None:
    raport = measurability_report(assumed_hit_rate=0.60, break_even_p=0.52, n_trades_expected=5_000)
    assert raport["verdict"] == "MIERZALNA"
    assert raport["measurable"] is True
    assert raport["margin_pp"] > 0


def test_measurability_report_says_unmeasurable_inside_the_invisible_band() -> None:
    """
    Przypadek, ktory ta funkcja ma lapac PRZED uruchomieniem: hipoteza oplacalna, ale
    zbyt slaba, zeby ja odroznic od progu przy tej probie. Taki eksperyment nie
    rozstrzygnie niczego NIEZALEZNIE OD WYNIKU.
    """
    raport = measurability_report(assumed_hit_rate=0.53, break_even_p=0.52, n_trades_expected=98)
    assert raport["verdict"] == "NIEMIERZALNA"
    assert raport["measurable"] is False
    assert raport["margin_pp"] < 0


def test_measurability_report_does_not_define_a_second_threshold() -> None:
    """
    Wymog z pre-rejestracji: NIE wolno dokladac trzeciej kopii progu (sa juz dwa trupy -
    MIN_VALIDATION_ROWS=30 i std<0.2). Raport musi WOLAC `min_detectable_hit_rate`,
    a nie liczyc czegos wlasnego.
    """
    be, n = 0.5246, 1_234
    raport = measurability_report(assumed_hit_rate=0.60, break_even_p=be, n_trades_expected=n)
    assert raport["p_detectable"] == pytest.approx(min_detectable_hit_rate(be, n))
    assert raport["band_width_pp"] == pytest.approx(100.0 * wald_half_width(n))


@pytest.mark.parametrize(
    "p, be, n",
    [(float("nan"), 0.52, 100), (0.6, float("nan"), 100), (0.6, 0.52, float("nan")),
     (0.6, 0.52, 0), (0.0, 0.52, 100), (1.0, 0.52, 100), (0.6, 0.0, 100), (0.6, 1.0, 100)],
)
def test_measurability_report_refuses_to_guess(p, be, n) -> None:
    """Smieciowe wejscie ma dac jawne N/D, nie liczbe, ktora ktos zacytuje w write-upie."""
    raport = measurability_report(assumed_hit_rate=p, break_even_p=be, n_trades_expected=n)
    assert raport["verdict"] == "N/D"
    assert raport["measurable"] is False
    assert math.isnan(raport["p_detectable"])


def test_measurability_chain_reproduces_h21_verdict_ex_ante() -> None:
    """
    Domkniecie petli: gdyby zasada 18 obowiazywala przed H2.1, runda NIE wystartowalaby.

    H2.1 mial ~14 400 swiec, abstynencje 99,32% i prog oplacalnosci 52,69% (sprostowany
    w H3). Przy zalozonej trafnosci 55% - hojnej wobec wszystkiego, co projekt kiedykolwiek
    zmierzyl - werdykt musi brzmiec NIEMIERZALNA.
    """
    n = expected_trades(14_400, abstention_rate=0.9932)
    raport = measurability_report(assumed_hit_rate=0.55, break_even_p=0.5269, n_trades_expected=n)
    assert raport["verdict"] == "NIEMIERZALNA"
    assert raport["band_width_pp"] > 9.0


# --- K2: jedno zrodlo wzoru na przedzial Walda wokol zaobserwowanej proporcji ---


def test_observed_wald_ci_is_the_single_source_used_by_compute_hit_rate() -> None:
    """
    `compute_hit_rate` NIE moze miec wlasnej kopii tej algebry.

    Do K2 wzor `z*sqrt(p(1-p)/n)` stal w dwoch miejscach: w `compute_hit_rate` (per przebieg)
    i w kodzie pool-ujacym w skrypcie rundy (12 losowan w jedna liczbe). Dwie kopie tego
    samego rachunku moga sie rozjechac bez sladu w diffie - ta sama klasa bledu, ktora H3
    usunelo przy bramce kosztowej.
    """
    n, hits = 400, 216
    trades = pd.DataFrame(
        {
            "gross_pnl": [1.0] * hits + [-1.0] * (n - hits),
            "kill_switch_active": [False] * n,
        }
    )
    z_journalu = compute_hit_rate(trades)
    wprost = observed_wald_ci(hits, n)

    assert z_journalu["hit_rate"] == pytest.approx(wprost["hit_rate"])
    assert z_journalu["ci_low"] == pytest.approx(wprost["ci_low"])
    assert z_journalu["ci_high"] == pytest.approx(wprost["ci_high"])


def test_observed_wald_ci_equals_conservative_band_exactly_at_half() -> None:
    """
    Przy p = 0,5 obie wielkosci sie spotykaja - i tylko tam. Test pilnuje, ze nie zaczely
    byc traktowane jako to samo (walidacja S1 zlapala juz raz dwie stale na ten sam kwantyl).
    """
    assert observed_wald_ci(500, 1000)["half_width"] == pytest.approx(wald_half_width(1000))
    # Poza p=0,5 wariant obserwowany jest WEZSZY niz konserwatywny.
    assert observed_wald_ci(700, 1000)["half_width"] < wald_half_width(1000)


def test_observed_wald_ci_reproduces_k2_pooled_row() -> None:
    """
    KOTWICA na liczbe opublikowana w `runs/2026-09-22_k2-naprawa-abstynencji/README.md`:
    ramie A2 na czystym szumie, 12 losowan zsumowanych.

    Gdyby ktos zmienil wzor albo `Z_TWO_SIDED_95`, tabela w write-upie przestalaby sie
    zgadzac z kodem - a tego rodzaju rozjazd jest dokladnie tym, co ta kotwica ma zlapac.
    """
    ci = observed_wald_ci(84_132, 167_160)
    assert 100 * ci["hit_rate"] == pytest.approx(50.33, abs=0.01)
    assert 100 * ci["ci_low"] == pytest.approx(50.09, abs=0.01)
    assert 100 * ci["ci_high"] == pytest.approx(50.57, abs=0.01)


@pytest.mark.parametrize("n", [0, -1])
def test_observed_wald_ci_returns_nan_for_empty_sample(n: int) -> None:
    ci = observed_wald_ci(0, n)
    assert math.isnan(ci["hit_rate"])
    assert math.isnan(ci["ci_low"])
