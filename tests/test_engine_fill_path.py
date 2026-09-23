"""
test_engine_fill_path.py

W1: tryb `fill_model="path"` w `backtest/engine.py` obok domyślnego `"label"`.

Najważniejsze dwie własności: (1) domyślne wywołanie `run_backtest` jest bit w bit tym samym,
co przed W1 — pilnują tego literały w `test_engine.py` (1 280 transakcji, `final_equity`
95 126,0168…) ORAZ test równoważności `collect_signals` + `simulate_equity` ≡ `run_backtest`;
(2) w trybie "path" lejek sygnałów jest identyczny z trybem "label" (jeden trening, jedna lista
kandydatów), a każdy sygnał kończy w DOKŁADNIE jednym miejscu: wiersz journalu (wypełniony
albo stłumiony) albo dziennik `unfilled`.
"""

from __future__ import annotations

import pandas as pd
import pytest

from agents.labeling import VERTICAL_BARRIER_CANDLES
from backtest.costs import EXIT_REASON_SL, EXIT_REASON_TIMEOUT, EXIT_REASON_TP, MAKER, TAKER
from backtest.engine import (
    EXECUTION_MAKER_LIMIT,
    EXECUTION_TAKER_ONLY,
    FILL_MODEL_LABEL,
    FILL_MODEL_PATH,
    TRADE_COLUMNS,
    UNFILLED_COLUMNS,
    _entry_leg_for,
    collect_signals,
    run_backtest,
    simulate_equity,
)
from backtest.execution import (
    ENTRY_LIMIT_CLOSE,
    ENTRY_LIMIT_PULLBACK,
    ENTRY_STOP_BREAKOUT,
    EntryRule,
)
from tests.test_engine import _make_pipeline_test_ohlcv

FAST = dict(
    train_days=5,
    test_days=2,
    step_days=2,
    num_boost_round=50,
    early_stopping_rounds=10,
    min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu test_engine.py
)


@pytest.fixture(scope="module")
def collected():
    return collect_signals(_make_pipeline_test_ohlcv(seed=7), **FAST)


@pytest.fixture(scope="module")
def label_result(collected):
    return simulate_equity(
        collected["df"], collected["candidate_signals"], collected["folds_summary"]
    )


def test_default_is_label_mode_with_zero_fill_offset_and_empty_unfilled():
    result = run_backtest(_make_pipeline_test_ohlcv(seed=7), **FAST)
    assert result["fill_model"] == FILL_MODEL_LABEL
    real = result["trades"].loc[~result["trades"]["kill_switch_active"]]
    assert (real["fill_bar_offset"] == 0.0).all()
    assert (
        result["trades"]["fill_bar_offset"].loc[result["trades"]["kill_switch_active"]].isna().all()
    )
    assert list(result["unfilled"].columns) == UNFILLED_COLUMNS and result["unfilled"].empty


def test_collect_then_simulate_equals_run_backtest(collected, label_result):
    direct = run_backtest(_make_pipeline_test_ohlcv(seed=7), **FAST)
    pd.testing.assert_frame_equal(direct["trades"], label_result["trades"])
    pd.testing.assert_frame_equal(direct["equity_curve"], label_result["equity_curve"])
    assert direct["final_equity"] == label_result["final_equity"]
    assert direct["folds_summary"] == label_result["folds_summary"]


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(fill_model="nieznany"),
        dict(fill_model=FILL_MODEL_PATH),  # brak entry_rule
        dict(
            fill_model=FILL_MODEL_PATH,
            entry_rule=EntryRule(ENTRY_LIMIT_CLOSE),
            entry_validity_candles=0,
        ),
        dict(
            fill_model=FILL_MODEL_PATH,
            entry_rule=EntryRule(ENTRY_LIMIT_CLOSE),
            entry_validity_candles=VERTICAL_BARRIER_CANDLES + 1,
        ),
        dict(fill_model=FILL_MODEL_LABEL, intrabar_ohlcv=pd.DataFrame()),
    ],
)
def test_path_mode_validation_fails_fast(collected, kwargs):
    with pytest.raises(ValueError):
        simulate_equity(
            collected["df"], collected["candidate_signals"], collected["folds_summary"], **kwargs
        )


@pytest.mark.parametrize("kind", [ENTRY_LIMIT_CLOSE, ENTRY_LIMIT_PULLBACK, ENTRY_STOP_BREAKOUT])
def test_path_mode_accounts_for_every_candidate_exactly_once(collected, label_result, kind):
    path = simulate_equity(
        collected["df"],
        collected["candidate_signals"],
        collected["folds_summary"],
        fill_model=FILL_MODEL_PATH,
        entry_rule=EntryRule(kind),
        entry_validity_candles=1,
    )
    # lejek identyczny z konstrukcji (ten sam obiekt folds_summary)
    assert path["folds_summary"] is collected["folds_summary"]
    # każdy kandydat: wiersz journalu (wypełniony/stłumiony) ALBO wpis w unfilled
    assert len(path["trades"]) + len(path["unfilled"]) == len(collected["candidate_signals"])
    assert len(label_result["trades"]) == len(collected["candidate_signals"])
    assert list(path["trades"].columns) == TRADE_COLUMNS
    assert list(path["unfilled"].columns) == UNFILLED_COLUMNS
    assert path["fill_model"] == FILL_MODEL_PATH

    real = path["trades"].loc[~path["trades"]["kill_switch_active"]]
    assert len(real) > 0
    assert (real["fill_bar_offset"] >= 1.0).all()
    assert (real["exit_bar_offset"] >= real["fill_bar_offset"]).all()
    assert (real["exit_bar_offset"] <= VERTICAL_BARRIER_CANDLES).all()
    assert set(real["exit_reason"]).issubset({EXIT_REASON_TP, EXIT_REASON_SL, EXIT_REASON_TIMEOUT})
    # bariery liczone od ceny wypełnienia: TP zawsze zyskowne brutto, SL zawsze stratne
    tp, sl = real["exit_reason"] == EXIT_REASON_TP, real["exit_reason"] == EXIT_REASON_SL
    assert (real.loc[tp, "gross_pnl"] > 0).all() and (real.loc[sl, "gross_pnl"] < 0).all()
    assert (real["position_size"] > 0).all() and (real["entry_price"] > 0).all()


def test_limit_close_fills_almost_everything_and_pullback_fills_less(collected):
    def n_unfilled(kind):
        r = simulate_equity(
            collected["df"],
            collected["candidate_signals"],
            collected["folds_summary"],
            fill_model=FILL_MODEL_PATH,
            entry_rule=EntryRule(kind),
        )
        return len(r["unfilled"])

    # Dane syntetyczne: w segmencie „range” kolejna świeca otwiera się NIEZALEŻNIE od poprzedniego
    # zamknięcia (szum wokół poziomu), więc limit po close bywa nieprzebity (~7%); na realnych
    # świecach 4h to 0,2% (pomiar opisowy w pre-rejestracji W1). Sprawdzamy rząd wielkości
    # i kolejność, nie dokładną wartość.
    n_total = len(collected["candidate_signals"])
    assert n_unfilled(ENTRY_LIMIT_CLOSE) < 0.10 * n_total
    assert n_unfilled(ENTRY_LIMIT_PULLBACK) > n_unfilled(ENTRY_LIMIT_CLOSE)


def test_unfilled_journal_keeps_label_and_level_for_selection_diagnostics(collected):
    r = simulate_equity(
        collected["df"],
        collected["candidate_signals"],
        collected["folds_summary"],
        fill_model=FILL_MODEL_PATH,
        entry_rule=EntryRule(ENTRY_LIMIT_PULLBACK, 1.0),
    )
    unfilled = r["unfilled"]
    assert len(unfilled) > 0
    assert set(unfilled["label"].dropna().unique()).issubset({-1.0, 0.0, 1.0})
    long = unfilled["signal_direction"] > 0
    assert (unfilled.loc[long, "entry_level"] < unfilled.loc[long, "entry_close"]).all()
    assert (unfilled.loc[~long, "entry_level"] > unfilled.loc[~long, "entry_close"]).all()


def test_entry_leg_follows_order_type_only_in_path_mode_with_maker_model():
    limit, stop = EntryRule(ENTRY_LIMIT_CLOSE), EntryRule(ENTRY_STOP_BREAKOUT)
    assert _entry_leg_for(FILL_MODEL_PATH, EXECUTION_MAKER_LIMIT, limit, MAKER) == MAKER
    assert _entry_leg_for(FILL_MODEL_PATH, EXECUTION_MAKER_LIMIT, stop, MAKER) == TAKER
    # taker_only: wszystko market, niezależnie od zlecenia
    assert _entry_leg_for(FILL_MODEL_PATH, EXECUTION_TAKER_ONLY, stop, TAKER) == TAKER
    # tryb label: jak dotąd
    assert _entry_leg_for(FILL_MODEL_LABEL, EXECUTION_MAKER_LIMIT, None, MAKER) == MAKER


def test_breakout_entries_cost_more_than_limit_entries_per_notional(collected):
    def mean_cost_fraction(kind):
        r = simulate_equity(
            collected["df"],
            collected["candidate_signals"],
            collected["folds_summary"],
            fill_model=FILL_MODEL_PATH,
            entry_rule=EntryRule(kind),
        )
        real = r["trades"].loc[~r["trades"]["kill_switch_active"]]
        # tylko wyjścia po TP, żeby noga wyjścia była ta sama (maker) w obu wariantach
        tp = real.loc[real["exit_reason"] == EXIT_REASON_TP]
        return (tp["cost"] / (tp["position_size"] * tp["entry_price"])).mean()

    assert mean_cost_fraction(ENTRY_STOP_BREAKOUT) > mean_cost_fraction(ENTRY_LIMIT_CLOSE)
