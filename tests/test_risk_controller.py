"""
test_risk_controller.py

Warstwa 1 (unit) + Warstwa 3 (hypothesis property-based, wymagane przez DoD dla
`agents/risk_controller.py` — docs/rag/05_metodologia_wytwarzania_i_testow.md) dla
sizingu i kill-switcha (IMPLEMENTATION_PLAN.md §5 Commit 5.5).
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.labeling import ATR_MULTIPLIER
from agents.risk_controller import (
    KILL_SWITCH_COOLDOWN_DAYS,
    KILL_SWITCH_DRAWDOWN_PCT,
    MAX_LEVERAGE,
    MIN_BARRIER_TO_COST_RATIO,
    RISK_PER_TRADE,
    barrier_to_cost_ratio,
    check_kill_switch,
    compute_position_size,
    compute_sizing,
    is_cost_feasible,
    should_rearm_kill_switch,
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
        equity,
        atr_14,
        entry_price,
        risk_per_trade=risk_per_trade,
        max_leverage=max_leverage,
        atr_multiplier=atr_multiplier,
    )

    size_risk = (equity * risk_per_trade) / (atr_multiplier * atr_14)
    size_leverage = (equity * max_leverage) / entry_price
    assert size == pytest.approx(min(size_risk, size_leverage))


def test_compute_position_size_default_atr_multiplier_matches_labeling() -> None:
    # CLAUDE.md zasada 3: atr_multiplier domyślny MUSI być agents.labeling.ATR_MULTIPLIER,
    # nigdy redefiniowany osobno.
    size_default = compute_position_size(
        equity=10_000.0, atr_14=50.0, entry_price=100.0
    )
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
    assert (
        check_kill_switch(equity=7_000.0, peak_equity=10_000.0, drawdown_threshold=0.15)
        is True
    )


def test_check_kill_switch_does_not_trigger_at_exact_threshold() -> None:
    # drawdown dokładnie == próg -> NIE wyzwala (ostre >, nie >=).
    assert (
        check_kill_switch(equity=8_500.0, peak_equity=10_000.0, drawdown_threshold=0.15)
        is False
    )


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
# Warstwa 1: unit tests — should_rearm_kill_switch (Commit 2c)
# ---------------------------------------------------------------------------


def test_should_rearm_kill_switch_false_when_not_tripped() -> None:
    now = pd.Timestamp("2025-01-01T00:00:00Z")
    assert should_rearm_kill_switch(None, now, cooldown_days=7.0) is False


def test_should_rearm_kill_switch_false_before_cooldown_elapsed() -> None:
    tripped_at = pd.Timestamp("2025-01-01T00:00:00Z")
    current = tripped_at + pd.Timedelta(days=3.0)
    assert should_rearm_kill_switch(tripped_at, current, cooldown_days=7.0) is False


def test_should_rearm_kill_switch_true_at_exact_cooldown_boundary() -> None:
    # Odwrotna konwencja graniczna niż check_kill_switch: tu >=, nie > (patrz
    # docstring should_rearm_kill_switch) -> dokładnie na granicy już True.
    tripped_at = pd.Timestamp("2025-01-01T00:00:00Z")
    current = tripped_at + pd.Timedelta(days=7.0)
    assert should_rearm_kill_switch(tripped_at, current, cooldown_days=7.0) is True


def test_should_rearm_kill_switch_uses_module_default_cooldown() -> None:
    tripped_at = pd.Timestamp("2025-01-01T00:00:00Z")
    current = tripped_at + pd.Timedelta(days=KILL_SWITCH_COOLDOWN_DAYS)
    assert should_rearm_kill_switch(tripped_at, current) is True


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
        signal_direction=1.0,
        regime="trend",
        atr_14=atr_14,
        entry_price=entry_price,
        equity=equity,
    )
    size_low = compute_sizing(signal_confidence=confidence_low, **kwargs)[
        "position_size"
    ]
    size_high = compute_sizing(signal_confidence=confidence_high, **kwargs)[
        "position_size"
    ]
    assert size_high >= size_low - 1e-9


@given(
    equity=st.floats(min_value=0.01, max_value=1e7),
    peak_equity=st.floats(min_value=0.01, max_value=1e7),
    drawdown_threshold=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=50, deadline=None)
def test_check_kill_switch_matches_drawdown_formula(
    equity, peak_equity, drawdown_threshold
) -> None:
    result = check_kill_switch(equity, peak_equity, drawdown_threshold)
    expected_drawdown = (peak_equity - equity) / peak_equity
    assert result == (expected_drawdown > drawdown_threshold)


@given(
    current_timestamp_offset_days=st.floats(min_value=0.0, max_value=365.0),
    cooldown_days=st.floats(min_value=0.0, max_value=365.0),
)
@settings(max_examples=50, deadline=None)
def test_should_rearm_kill_switch_false_when_never_tripped(
    current_timestamp_offset_days, cooldown_days
) -> None:
    # kill_switch_tripped_at=None -> zawsze False, niezależnie od cooldown_days czy
    # current_timestamp (nie ma czego re-armować).
    current_timestamp = pd.Timestamp("2025-01-01T00:00:00Z") + pd.Timedelta(
        days=current_timestamp_offset_days
    )
    assert should_rearm_kill_switch(None, current_timestamp, cooldown_days) is False


@given(
    cooldown_days=st.floats(min_value=0.01, max_value=365.0),
    extra_days=st.floats(min_value=0.0, max_value=365.0),
)
@settings(max_examples=50, deadline=None)
def test_should_rearm_kill_switch_true_once_cooldown_elapsed(
    cooldown_days, extra_days
) -> None:
    # current_timestamp skonstruowany tak, żeby upłynęło DOKŁADNIE cooldown_days +
    # extra_days (extra_days >= 0) -> zawsze >= cooldown_days -> zawsze True.
    tripped_at = pd.Timestamp("2025-01-01T00:00:00Z")
    current_timestamp = tripped_at + pd.Timedelta(days=cooldown_days + extra_days)
    assert (
        should_rearm_kill_switch(tripped_at, current_timestamp, cooldown_days) is True
    )


@given(
    cooldown_days=st.floats(min_value=0.01, max_value=365.0),
    fraction_elapsed=st.floats(min_value=0.0, max_value=0.999),
)
@settings(max_examples=50, deadline=None)
def test_should_rearm_kill_switch_false_before_cooldown_elapsed_property(
    cooldown_days, fraction_elapsed
) -> None:
    # current_timestamp skonstruowany tak, żeby upłynęło ŚCIŚLE MNIEJ niż
    # cooldown_days (margines >= 0.1% cooldown_days) -> zawsze False.
    tripped_at = pd.Timestamp("2025-01-01T00:00:00Z")
    current_timestamp = tripped_at + pd.Timedelta(days=cooldown_days * fraction_elapsed)
    assert (
        should_rearm_kill_switch(tripped_at, current_timestamp, cooldown_days) is False
    )


# ---------------------------------------------------------------------------
# Commit 2d — bramka wykonalności kosztowej
# Warstwa 1 (unit) + Warstwa 3 (hypothesis). Uzasadnienie i liczby empiryczne:
# agents/risk_controller.py (BRAMKA WYKONALNOŚCI KOSZTOWEJ) oraz
# backtest/diagnose_cost_feasibility.py.
# ---------------------------------------------------------------------------

COST_FRACTION_STARTOWY = 0.0014  # 2x taker 0.05% + 2x slippage 2bps (backtest/costs.py)


def test_barrier_to_cost_ratio_matches_manual_formula() -> None:
    # entry_price=100, atr_14=1.0, mnożnik 1.5 -> bariera = 1.5% ceny.
    # 1.5% / 0.14% = 10.714...
    ratio = barrier_to_cost_ratio(
        atr_14=1.0, entry_price=100.0, cost_fraction=COST_FRACTION_STARTOWY
    )
    expected = (ATR_MULTIPLIER * 1.0 / 100.0) / COST_FRACTION_STARTOWY
    assert ratio == pytest.approx(expected)


def test_barrier_to_cost_ratio_reproduces_range_regime_diagnosis() -> None:
    # Realia reżimu `range` (BTC 5m, diagnoza Commit 2d): mediana bariery 1.5xATR to
    # ~0,130% ceny przy koszcie 0,140% -> stosunek < 1, czyli nawet PEŁNE trafienie
    # bariery nie pokrywa kosztu. To jest dokładnie przypadek, dla którego bramka
    # powstała — test pilnuje, że formuła nadal go rozpoznaje.
    entry_price = 100_000.0
    atr_14 = 0.00130 * entry_price / ATR_MULTIPLIER
    ratio = barrier_to_cost_ratio(atr_14, entry_price, COST_FRACTION_STARTOWY)
    assert ratio < 1.0
    assert not is_cost_feasible(atr_14, entry_price, COST_FRACTION_STARTOWY)


def test_is_cost_feasible_accepts_wide_barrier() -> None:
    # Reżim `trend`: mediana bariery ~0,384% ceny -> stosunek ~2,75 > próg 2.0.
    entry_price = 100_000.0
    atr_14 = 0.00384 * entry_price / ATR_MULTIPLIER
    assert is_cost_feasible(atr_14, entry_price, COST_FRACTION_STARTOWY) is True


@pytest.mark.parametrize("entry_price", [0.0, -1.0])
def test_barrier_to_cost_ratio_fail_safe_on_degenerate_entry_price(entry_price) -> None:
    # Fail-safe (jak check_kill_switch): zamiast dzielić przez zero -> 0.0, czyli
    # sygnał ODRZUCONY, nie przepuszczony po cichu.
    assert barrier_to_cost_ratio(1.0, entry_price, COST_FRACTION_STARTOWY) == 0.0
    assert is_cost_feasible(1.0, entry_price, COST_FRACTION_STARTOWY) is False


def test_barrier_to_cost_ratio_fail_safe_on_zero_cost() -> None:
    assert barrier_to_cost_ratio(1.0, 100.0, cost_fraction=0.0) == 0.0


def test_is_cost_feasible_rejects_nan_atr() -> None:
    # Świeca bez policzalnego ATR (warmup) -> NaN -> porównanie z progiem False.
    assert is_cost_feasible(float("nan"), 100.0, COST_FRACTION_STARTOWY) is False


def test_min_barrier_to_cost_ratio_startup_value_matches_break_even_arithmetic() -> (
    None
):
    # Próg startowy nie jest dobrany po PnL — wynika z p = 0.5*(1 + 1/ratio).
    # ratio=2.0 -> wymagana trafność kierunku na break-even = 75%.
    p_break_even = 0.5 * (1.0 + 1.0 / MIN_BARRIER_TO_COST_RATIO)
    assert p_break_even == pytest.approx(0.75)


@given(
    atr_14=st.floats(min_value=1e-6, max_value=1e5),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
    cost_fraction=st.floats(min_value=1e-6, max_value=0.05),
    min_ratio=st.floats(min_value=0.0, max_value=10.0),
)
@settings(max_examples=100, deadline=None)
def test_is_cost_feasible_consistent_with_ratio(
    atr_14, entry_price, cost_fraction, min_ratio
) -> None:
    # Niezmiennik: bramka to DOKŁADNIE porównanie stosunku z progiem, nic więcej —
    # żadnej dodatkowej, ukrytej reguły.
    ratio = barrier_to_cost_ratio(atr_14, entry_price, cost_fraction)
    expected = ratio >= min_ratio
    assert (
        is_cost_feasible(
            atr_14, entry_price, cost_fraction, min_barrier_to_cost_ratio=min_ratio
        )
        is expected
    )


@given(
    atr_small=st.floats(min_value=1e-6, max_value=1e4),
    atr_extra=st.floats(min_value=0.0, max_value=1e4),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
    cost_fraction=st.floats(min_value=1e-6, max_value=0.05),
)
@settings(max_examples=100, deadline=None)
def test_barrier_to_cost_ratio_monotonic_nondecreasing_in_atr(
    atr_small, atr_extra, entry_price, cost_fraction
) -> None:
    # Niezmiennik: szersza bariera (większy ATR przy tej samej cenie) NIGDY nie
    # obniża stosunku — czyli sygnał raz dopuszczony nie staje się nagle odrzucony
    # przez sam wzrost zmienności.
    small = barrier_to_cost_ratio(atr_small, entry_price, cost_fraction)
    large = barrier_to_cost_ratio(atr_small + atr_extra, entry_price, cost_fraction)
    assert large >= small - 1e-9


@given(
    atr_14=st.floats(min_value=1e-6, max_value=1e5),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
    cost_fraction=st.floats(min_value=1e-6, max_value=0.05),
)
@settings(max_examples=100, deadline=None)
def test_is_cost_feasible_always_true_when_threshold_zero(
    atr_14, entry_price, cost_fraction
) -> None:
    # Próg 0.0 = bramka wyłączona (używane przez testy sprzed Commitu 2d oraz do
    # odtworzenia baseline'u Commitu 2c) — musi przepuszczać każdy poprawny sygnał.
    assert (
        is_cost_feasible(
            atr_14, entry_price, cost_fraction, min_barrier_to_cost_ratio=0.0
        )
        is True
    )
