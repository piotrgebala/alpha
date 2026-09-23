"""
test_engine_managed.py

Runda N1: `exit_rule` (wyjście wielonogowe) w `backtest/engine.py`. Sprawdza, że journal domyka
się arytmetycznie (gross z nóg = gross w journalu), że kolumny częściowego wyjścia są spójne,
że wiersze jednonogowe zgadzają się z pojedynczym wyjściem na tych samych sygnałach, i że tryb
"label" oraz `path` bez reguły pozostają nietknięte.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.costs import EXIT_REASON_BE_STOP, EXIT_REASON_SL, EXIT_REASON_TIMEOUT, EXIT_REASON_TP
from backtest.engine import (
    FILL_MODEL_LABEL,
    FILL_MODEL_PATH,
    TRADE_COLUMNS,
    collect_signals,
    simulate_equity,
)
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule, ManagedExitRule
from tests.test_engine import _make_pipeline_test_ohlcv

FAST = dict(
    train_days=5,
    test_days=2,
    step_days=2,
    num_boost_round=50,
    early_stopping_rounds=10,
    min_barrier_to_cost_ratio=0.0,
)
RULE = ManagedExitRule(partial_fraction=0.5, near_pct=0.0167)


@pytest.fixture(scope="module")
def collected():
    return collect_signals(_make_pipeline_test_ohlcv(seed=7), **FAST)


def run(collected, **kwargs):
    return simulate_equity(
        collected["df"], collected["candidate_signals"], collected["folds_summary"], **kwargs
    )


def test_exit_rule_requires_path_mode(collected):
    with pytest.raises(ValueError):
        run(collected, fill_model=FILL_MODEL_LABEL, exit_rule=RULE)


def test_label_mode_journal_has_single_leg_columns(collected):
    trades = run(collected)["trades"]
    assert list(trades.columns) == TRADE_COLUMNS
    real = trades.loc[~trades["kill_switch_active"]]
    assert (real["n_legs"] == 1).all() and real["partial_exit_price"].isna().all()
    assert (trades.loc[trades["kill_switch_active"], "n_legs"] == 0).all()


def test_managed_journal_is_arithmetically_closed(collected):
    res = run(
        collected,
        fill_model=FILL_MODEL_PATH,
        entry_rule=EntryRule(ENTRY_LIMIT_CLOSE),
        exit_rule=RULE,
    )
    trades = res["trades"]
    real = trades.loc[~trades["kill_switch_active"]].copy()
    assert set(real["n_legs"].unique()).issubset({1, 2})
    assert (
        real["n_legs"] == 2
    ).any(), "na danych syntetycznych powinno być choć jedno częściowe wyjście"

    d, size, e = real["signal_direction"], real["position_size"], real["entry_price"]
    two = real["n_legs"] == 2
    gross_two = d * size * (0.5 * (real["partial_exit_price"] - e) + 0.5 * (real["exit_price"] - e))
    gross_one = d * size * (real["exit_price"] - e)
    expected = np.where(two, gross_two, gross_one)
    assert np.allclose(real["gross_pnl"].to_numpy(), expected)
    assert np.allclose(real["net_pnl"], real["gross_pnl"] - real["cost"])

    # kolumny częściowego wyjścia: tylko przy 2 nogach, w oknie [wypełnienie, wyjście]
    assert real.loc[~two, "partial_exit_price"].isna().all()
    assert real.loc[two, "partial_exit_price"].notna().all()
    assert (real.loc[two, "partial_exit_bar_offset"] >= real.loc[two, "fill_bar_offset"]).all()
    assert (real.loc[two, "partial_exit_bar_offset"] <= real.loc[two, "exit_bar_offset"]).all()
    # przy 2 nogach ostatnia noga to dalszy cel, stop na wejściu albo timeout
    assert set(real.loc[two, "exit_reason"]).issubset(
        {EXIT_REASON_TP, EXIT_REASON_BE_STOP, EXIT_REASON_TIMEOUT}
    )
    be = real["exit_reason"] == EXIT_REASON_BE_STOP
    assert np.allclose(real.loc[be, "exit_price"], real.loc[be, "entry_price"])
    # przy 1 nodze — tylko stop albo timeout (bliższy cel nie padł)
    assert set(real.loc[~two, "exit_reason"]).issubset({EXIT_REASON_SL, EXIT_REASON_TIMEOUT})
    # częściowe wyjście na bliższym celu jest zawsze zyskowne brutto na swojej połowie
    assert ((real.loc[two, "partial_exit_price"] - e[two]) * d[two] > 0).all()


def test_single_leg_rows_match_single_exit_run_per_unit(collected):
    """Wiersze bez częściowego wyjścia muszą mieć ten sam powód i cenę wyjścia co pojedyncze wyjście."""
    single = run(collected, fill_model=FILL_MODEL_PATH, entry_rule=EntryRule(ENTRY_LIMIT_CLOSE))[
        "trades"
    ]
    managed = run(
        collected,
        fill_model=FILL_MODEL_PATH,
        entry_rule=EntryRule(ENTRY_LIMIT_CLOSE),
        exit_rule=RULE,
    )["trades"]
    s = single.loc[~single["kill_switch_active"]].set_index("timestamp")
    m = managed.loc[~managed["kill_switch_active"] & (managed["n_legs"] == 1)].set_index(
        "timestamp"
    )
    both = m.join(s, lsuffix="_m", rsuffix="_s", how="inner")
    assert len(both) > 0
    assert (both["exit_reason_m"] == both["exit_reason_s"]).all()
    assert np.allclose(both["exit_price_m"], both["exit_price_s"])
    assert np.allclose(both["entry_price_m"], both["entry_price_s"])


def test_managed_run_keeps_funnel_and_unfilled_identical(collected):
    single = run(collected, fill_model=FILL_MODEL_PATH, entry_rule=EntryRule(ENTRY_LIMIT_CLOSE))
    managed = run(
        collected,
        fill_model=FILL_MODEL_PATH,
        entry_rule=EntryRule(ENTRY_LIMIT_CLOSE),
        exit_rule=RULE,
    )
    assert managed["folds_summary"] is collected["folds_summary"]
    assert len(managed["trades"]) + len(managed["unfilled"]) == len(collected["candidate_signals"])
    # Kill-switch zależy od toru equity, więc może stłumić INNE sygnały w obu przebiegach — sygnał
    # stłumiony nie jest sprawdzany pod kątem wypełnienia. Na sygnałach niestłumionych w żadnym
    # z przebiegów status wypełnienia musi być identyczny (ten sam poziom, te same świece).
    suppressed = set(
        single["trades"].loc[single["trades"]["kill_switch_active"], "timestamp"]
    ) | set(managed["trades"].loc[managed["trades"]["kill_switch_active"], "timestamp"])
    unf_s = set(single["unfilled"]["timestamp"]) - suppressed
    unf_m = set(managed["unfilled"]["timestamp"]) - suppressed
    assert unf_s == unf_m
