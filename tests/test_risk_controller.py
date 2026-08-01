"""
test_risk_controller.py

Warstwa 1 (unit) + Warstwa 3 (hypothesis property-based, wymagane przez DoD dla
`agents/risk_controller.py` — docs/rag/05_metodologia_wytwarzania_i_testow.md) dla
sizingu i kill-switcha (IMPLEMENTATION_PLAN.md §5 Commit 5.5).
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.labeling import ATR_MULTIPLIER
from agents.risk_controller import (
    KILL_SWITCH_DRAWDOWN_PCT,
    MAX_LEVERAGE,
    RISK_PER_TRADE,
    check_kill_switch,
    compute_position_size,
    compute_sizing,
)

# ---------------------------------------------------------------------------
# Warstwa 1: unit tests — compute_position_size / compute_sizing
# ---------------------------------------------------------------------------


def test_compute_position_size_picks_size_leverage_when_atr_small() -> None:
    # ATR bardzo mały -> size_risk ogromny -> size_leverage (twardy sufit) binduje.
    size = compute_position_size(
        equity=10_000.0,
        atr_14=0.001,
        entry_price=100.0,
        risk_per_trade=0.005,
        max_leverage=3.0,
        atr_multiplier=1.5,
    )
    expected_size_leverage = (10_000.0 * 3.0) / 100.0
    assert size == pytest.approx(expected_size_leverage)


def test_compute_position_size_picks_size_risk_when_atr_large() -> None:
    # ATR duży -> size_risk mały -> to on binduje, nie leverage cap.
    size = compute_position_size(
        equity=10_000.0,
        atr_14=50.0,
        entry_price=100.0,
        risk_per_trade=0.005,
        max_leverage=3.0,
        atr_multiplier=1.5,
    )
    expected_size_risk = (10_000.0 * 0.005) / (1.5 * 50.0)
    expected_size_leverage = (10_000.0 * 3.0) / 100.0
    assert size == pytest.approx(expected_size_risk)
    assert size < expected_size_leverage


def test_compute_position_size_matches_manual_formula() -> None:
    equity, atr_14, entry_price = 20_000.0, 200.0, 50_000.0
    risk_per_trade, max_leverage, atr_multiplier = 0.01, 2.0, 1.5

    size = compute_position_size(
        equity, atr_14, entry_price,
        risk_per_trade=risk_per_trade, max_leverage=max_leverage, atr_multiplier=atr_multiplier,
    )

    size_risk = (equity * risk_per_trade) / (atr_multiplier * atr_14)
    size_leverage = (equity * max_leverage) / entry_price
    assert size == pytest.approx(min(size_risk, size_leverage))


def test_compute_position_size_default_atr_multiplier_matches_labeling() -> None:
    # CLAUDE.md zasada 3: atr_multiplier domyślny MUSI być agents.labeling.ATR_MULTIPLIER,
    # nigdy redefiniowany osobno.
    size_default = compute_position_size(equity=10_000.0, atr_14=50.0, entry_price=100.0)
    size_explicit = compute_position_size(
        equity=10_000.0,
        atr_14=50.0,
        entry_price=100.0,
        risk_per_trade=RISK_PER_TRADE,
        max_leverage=MAX_LEVERAGE,
        atr_multiplier=ATR_MULTIPLIER,
    )
    assert size_default == pytest.approx(size_explicit)


def test_compute_sizing_scales_effective_risk_by_confidence() -> None:
    # size_risk binduje w obu przypadkach (atr_14=50 duży) -> skalowanie liniowe widoczne.
    kwargs = dict(
        signal_direction=1.0,
        regime="trend",
        atr_14=50.0,
        entry_price=100.0,
        equity=10_000.0,
    )
    full_confidence = compute_sizing(signal_confidence=1.0, **kwargs)
    half_confidence = compute_sizing(signal_confidence=0.5, **kwargs)
    assert half_confidence["position_size"] == pytest.approx(
        full_confidence["position_size"] / 2.0
    )


def test_compute_sizing_stop_and_take_profit_for_long() -> None:
    result = compute_sizing(
        signal_direction=1.0,
        signal_confidence=0.8,
        regime="trend",
        atr_14=10.0,
        entry_price=100.0,
        equity=10_000.0,
        atr_multiplier=1.5,
    )
    assert result["stop_price"] == pytest.approx(85.0)
    assert result["take_profit_price"] == pytest.approx(115.0)


def test_compute_sizing_stop_and_take_profit_for_short() -> None:
    result = compute_sizing(
        signal_direction=-1.0,
        signal_confidence=0.8,
        regime="range",
        atr_14=10.0,
        entry_price=100.0,
        equity=10_000.0,
        atr_multiplier=1.5,
    )
    assert result["stop_price"] == pytest.approx(115.0)
    assert result["take_profit_price"] == pytest.approx(85.0)


def test_compute_sizing_returns_expected_keys() -> None:
    result = compute_sizing(
        signal_direction=1.0,
        signal_confidence=0.5,
        regime="trend",
        atr_14=10.0,
        entry_price=100.0,
        equity=10_000.0,
    )
    assert set(result.keys()) == {"position_size", "stop_price", "take_profit_price"}


# ---------------------------------------------------------------------------
# Warstwa 1: unit tests — check_kill_switch
# ---------------------------------------------------------------------------


def test_check_kill_switch_triggers_above_threshold() -> None:
    assert check_kill_switch(equity=7_000.0, peak_equity=10_000.0, drawdown_threshold=0.15) is True


def test_check_kill_switch_does_not_trigger_at_exact_threshold() -> None:
    # drawdown dokładnie == próg -> NIE wyzwala (ostre >, nie >=).
    assert check_kill_switch(equity=8_500.0, peak_equity=10_000.0, drawdown_threshold=0.15) is False


def test_check_kill_switch_no_drawdown_when_at_peak() -> None:
    assert check_kill_switch(equity=10_000.0, peak_equity=10_000.0) is False


def test_check_kill_switch_peak_non_positive_is_fail_safe() -> None:
    assert check_kill_switch(equity=0.0, peak_equity=0.0) is True
    assert check_kill_switch(equity=-50.0, peak_equity=-100.0) is True


def test_check_kill_switch_uses_module_default_threshold() -> None:
    # equity = 16% poniżej peaku, bez podania drawdown_threshold -> używa
    # KILL_SWITCH_DRAWDOWN_PCT (0.15) -> 0.16 > 0.15 -> True.
    equity = (1.0 - KILL_SWITCH_DRAWDOWN_PCT - 0.01) * 10_000.0
    assert check_kill_switch(equity=equity, peak_equity=10_000.0) is True


# ---------------------------------------------------------------------------
# Warstwa 3: hypothesis property-based (wymagane DoD dla risk_controller.py,
# docs/rag/05_metodologia_wytwarzania_i_testow.md)
# ---------------------------------------------------------------------------


@given(
    equity=st.floats(min_value=1, max_value=1e7),
    atr_14=st.floats(min_value=0.01, max_value=1e5),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
)
@settings(max_examples=50, deadline=None)
def test_position_size_never_exceeds_leverage_cap(equity, atr_14, entry_price) -> None:
    size = compute_position_size(
        equity, atr_14, entry_price, risk_per_trade=0.005, max_leverage=3.0
    )
    max_allowed = (equity * 3.0) / entry_price
    assert size <= max_allowed + 1e-9  # tolerancja float


@given(
    equity=st.floats(min_value=1, max_value=1e7),
    atr_14=st.floats(min_value=0.01, max_value=1e5),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
)
@settings(max_examples=50, deadline=None)
def test_position_size_non_negative(equity, atr_14, entry_price) -> None:
    size = compute_position_size(
        equity, atr_14, entry_price, risk_per_trade=0.005, max_leverage=3.0
    )
    assert size >= 0


@given(
    equity=st.floats(min_value=1, max_value=1e7),
    atr_14=st.floats(min_value=0.01, max_value=1e5),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
    confidence_low=st.floats(min_value=0.01, max_value=1.0),
    confidence_delta=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=50, deadline=None)
def test_position_size_monotonic_nondecreasing_in_confidence(
    equity, atr_14, entry_price, confidence_low, confidence_delta
) -> None:
    confidence_high = min(1.0, confidence_low + confidence_delta)
    kwargs = dict(
        signal_direction=1.0, regime="trend", atr_14=atr_14, entry_price=entry_price, equity=equity
    )
    size_low = compute_sizing(signal_confidence=confidence_low, **kwargs)["position_size"]
    size_high = compute_sizing(signal_confidence=confidence_high, **kwargs)["position_size"]
    assert size_high >= size_low - 1e-9


@given(
    equity=st.floats(min_value=0.01, max_value=1e7),
    peak_equity=st.floats(min_value=0.01, max_value=1e7),
    drawdown_threshold=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=50, deadline=None)
def test_check_kill_switch_matches_drawdown_formula(equity, peak_equity, drawdown_threshold) -> None:
    result = check_kill_switch(equity, peak_equity, drawdown_threshold)
    expected_drawdown = (peak_equity - equity) / peak_equity
    assert result == (expected_drawdown > drawdown_threshold)
