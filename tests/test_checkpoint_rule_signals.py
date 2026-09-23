"""
test_checkpoint_rule_signals.py

Runda A1: `build_rule_signals` i `summarize_trade_returns` w backtest/checkpoint_lib.py.

Reguła (bez modelu) ma dostać DOKŁADNIE tę samą populację świec co model: okna testowe
aktywnych foldów, etykieta i ATR nie-NaN, bramka kosztowa silnika — i sygnały w formacie,
który `engine.simulate_equity` czyta bez zmian (każdy kończy w jednym miejscu: journal albo
`unfilled`). Statystyki zwrotu per transakcja muszą domykać się arytmetycznie z journalem.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import build_rule_signals, summarize_result, summarize_trade_returns
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule
from tests.test_engine import _make_pipeline_test_ohlcv

FAST = dict(
    train_days=5,
    test_days=2,
    step_days=2,
    num_boost_round=50,
    early_stopping_rounds=10,
    min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu test_engine.py
    regime_feature_sets=[(REGIME_ALL, REVERSION_FEATURES)],
)
SIGNAL_FIELDS = {
    "original_index",
    "timestamp",
    "regime",
    "fold_idx",
    "signal_direction",
    "signal_confidence",
    "entry_price",
    "atr_14",
    "label",
    "exit_bar_offset",
}


@pytest.fixture(scope="module")
def collected():
    return collect_signals(_make_pipeline_test_ohlcv(seed=7), **FAST)


@pytest.fixture(scope="module")
def scored(collected):
    rng = np.random.default_rng(1)
    df = collected["df"].copy()
    df["score"] = rng.choice([-1.0, 0.0, 1.0], size=len(df), p=[0.2, 0.6, 0.2])
    return df


def _active(folds):
    return {f["fold_idx"]: f for f in folds if not f["skipped"]}


def test_signals_live_only_in_active_test_windows_and_are_sorted(collected, scored):
    signals, funnel = build_rule_signals(
        scored, collected["folds_summary"], "score", min_barrier_to_cost_ratio=0.0
    )
    active = _active(collected["folds_summary"])
    assert signals and funnel["n_signals"] == len(signals)
    for s in signals:
        fold = active[s["fold_idx"]]
        assert fold["test_start"] <= s["timestamp"] < fold["test_end"]
    stamps = [s["timestamp"] for s in signals]
    assert stamps == sorted(stamps)
    assert funnel["n_rows_window"] == sum(
        ((scored["timestamp"] >= f["test_start"]) & (scored["timestamp"] < f["test_end"])).sum()
        for f in active.values()
    )


def test_signal_fields_come_from_the_row_and_direction_is_sign_of_score(collected, scored):
    signals, _ = build_rule_signals(
        scored, collected["folds_summary"], "score", confidence=0.7, min_barrier_to_cost_ratio=0.0
    )
    for s in signals:
        assert set(s) == SIGNAL_FIELDS
        row = scored.loc[s["original_index"]]
        assert s["signal_direction"] == np.sign(row["score"]) != 0.0
        assert s["signal_confidence"] == 0.7 and s["regime"] == REGIME_ALL
        assert s["entry_price"] == row["close"] and s["atr_14"] == row["atr_14"]
        assert s["label"] == row["label"] and s["exit_bar_offset"] == row["exit_bar_offset"]
        assert s["timestamp"] == row["timestamp"]


def test_funnel_is_closed_and_nan_labels_are_dropped(collected, scored):
    df = scored.copy()
    _, before = build_rule_signals(
        df, collected["folds_summary"], "score", min_barrier_to_cost_ratio=0.0
    )
    # wyzeruj etykiety w 5 świecach z sygnałem wewnątrz okna — muszą wypaść do n_label_nan
    signals, _ = build_rule_signals(
        df, collected["folds_summary"], "score", min_barrier_to_cost_ratio=0.0
    )
    victims = [s["original_index"] for s in signals[:5]]
    df.loc[victims, "label"] = np.nan
    after_signals, after = build_rule_signals(
        df, collected["folds_summary"], "score", min_barrier_to_cost_ratio=0.0
    )
    for funnel in (before, after):
        assert (
            funnel["n_rows_window"]
            == funnel["n_no_signal"]
            + funnel["n_label_nan"]
            + funnel["n_cost_gated"]
            + funnel["n_signals"]
        )
    assert after["n_label_nan"] == before["n_label_nan"] + 5
    assert after["n_signals"] == before["n_signals"] - 5
    assert not {s["original_index"] for s in after_signals} & set(victims)


def test_cost_gate_rejects_every_signal_when_ratio_is_absurd(collected, scored):
    signals, funnel = build_rule_signals(
        scored, collected["folds_summary"], "score", min_barrier_to_cost_ratio=1e9
    )
    assert signals == [] and funnel["n_signals"] == 0
    assert (
        funnel["n_cost_gated"]
        == funnel["n_rows_window"] - funnel["n_no_signal"] - funnel["n_label_nan"]
    )


def test_fails_loud_on_missing_score_column_bad_index_or_no_active_folds(collected, scored):
    with pytest.raises(ValueError):
        build_rule_signals(scored, collected["folds_summary"], "nie_ma_takiej")
    with pytest.raises(ValueError):
        build_rule_signals(scored.iloc[10:], collected["folds_summary"], "score")
    skipped = [{**f, "skipped": True} for f in collected["folds_summary"]]
    with pytest.raises(ValueError):
        build_rule_signals(scored, skipped, "score")


@pytest.fixture(scope="module")
def rule_result(collected, scored):
    signals, _ = build_rule_signals(
        scored, collected["folds_summary"], "score", min_barrier_to_cost_ratio=0.0
    )
    result = simulate_equity(
        scored,
        signals,
        collected["folds_summary"],
        fill_model=FILL_MODEL_PATH,
        entry_rule=EntryRule(ENTRY_LIMIT_CLOSE),
        entry_validity_candles=1,
    )
    return signals, result


def test_rule_signals_run_through_the_engine_each_ending_in_one_place(rule_result):
    signals, result = rule_result
    trades, unfilled = result["trades"], result["unfilled"]
    assert len(trades) + len(unfilled) == len(signals)
    real = trades.loc[~trades["kill_switch_active"]]
    assert (real["n_legs"] == 1).all()
    assert set(real["regime"]) <= {REGIME_ALL}


def test_summarize_trade_returns_closes_arithmetically_with_the_journal(rule_result):
    _, result = rule_result
    w = summarize_trade_returns(summarize_result(result, 42))
    trades = result["trades"]
    real = trades.loc[~trades["kill_switch_active"]]
    assert w["n"] == len(real) and w["n_suppressed"] == int(trades["kill_switch_active"].sum())
    assert w["n_unfilled"] == len(result["unfilled"])
    assert w["p"] == pytest.approx(float((real["gross_pnl"] > 0).mean()))
    assert w["p_star"] == pytest.approx((w["l_mean"] + w["cost"]) / (w["w_mean"] + w["l_mean"]))
    assert w["t"] == pytest.approx(w["r_mean"] / w["se"])
    assert w["t_neff"] == pytest.approx(w["t"] * np.sqrt(w["n_eff"] / w["n"]))
    net = real["net_pnl"] / (real["position_size"] * real["entry_price"])
    assert w["r_mean"] == pytest.approx(float(net.mean()))
    assert 0.0 < w["n_eff"] <= w["n"]


def test_summarize_trade_returns_refuses_two_regimes(rule_result):
    _, result = rule_result
    summary = summarize_result(result, 42)
    two = pd.concat([summary["edge_per_regime"]] * 2, ignore_index=True)
    with pytest.raises(ValueError):
        summarize_trade_returns({**summary, "edge_per_regime": two})


def test_n_eff_is_capped_at_n_so_correction_never_adds_confidence(rule_result, monkeypatch):
    """A1 (Poprawka 2): ujemna autokorelacja daje N/(1+2Σρ) > n — cap jak w metrics.py."""
    import backtest.checkpoint_lib as lib

    _, result = rule_result
    monkeypatch.setattr(
        lib, "effective_sample_size", lambda r, max_lag=50: {"n": len(r), "n_eff": 3.0 * len(r)}
    )
    w = summarize_trade_returns(summarize_result(result, 42))
    assert w["n_eff"] == w["n"]
    assert w["t_neff"] == pytest.approx(w["t"])
