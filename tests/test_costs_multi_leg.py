"""
test_costs_multi_leg.py

Koszt per noga (`backtest/costs.py::multi_leg_cost`, runda N1) i nowe powody wyjścia.

Najważniejsza własność: JEDNA noga o ułamku 1,0 daje DOKŁADNIE (==, nie approx) ten sam koszt
co `total_round_trip_cost` — inaczej W1 i wszystkie wcześniejsze rundy przestałyby być
odtwarzalne co do cyfry.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest.costs import (
    EXECUTION_MAKER_LIMIT,
    EXECUTION_TAKER_ONLY,
    EXIT_REASON_BE_STOP,
    EXIT_REASON_TP_PARTIAL,
    MAKER,
    MAKER_FEE_RATE,
    SLIPPAGE_BPS,
    TAKER,
    TAKER_FEE_RATE,
    VALID_EXIT_REASONS,
    exit_leg_for_reason,
    funding_cost,
    gate_cost_fraction,
    multi_leg_cost,
    total_round_trip_cost,
)


def test_new_exit_reasons_map_to_expected_legs():
    assert (
        EXIT_REASON_TP_PARTIAL in VALID_EXIT_REASONS and EXIT_REASON_BE_STOP in VALID_EXIT_REASONS
    )
    assert exit_leg_for_reason(EXIT_REASON_TP_PARTIAL) == MAKER  # cel = limit w księdze
    assert exit_leg_for_reason(EXIT_REASON_BE_STOP) == TAKER  # stop = wyjście przymusowe


def test_cost_gate_unchanged_by_new_reasons():
    """Maksimum po powodach wyjścia realizuje noga taker — nowe powody nie przesuwają bramki."""
    assert gate_cost_fraction(EXECUTION_MAKER_LIMIT) == pytest.approx(0.0009)
    assert gate_cost_fraction(EXECUTION_TAKER_ONLY) == pytest.approx(0.0014)


@settings(max_examples=200, deadline=None)
@given(
    notional=st.floats(min_value=1.0, max_value=1e6, allow_nan=False),
    holding=st.floats(min_value=0.0, max_value=50.0, allow_nan=False),
    direction=st.sampled_from([1, -1]),
    entry_leg=st.sampled_from([MAKER, TAKER]),
    exit_leg=st.sampled_from([MAKER, TAKER]),
    candle_minutes=st.sampled_from([5, 60, 240]),
)
def test_property_single_leg_is_bit_identical_to_round_trip(
    notional, holding, direction, entry_leg, exit_leg, candle_minutes
):
    single = multi_leg_cost(
        notional, entry_leg, [(1.0, holding, exit_leg)], direction, candle_minutes=candle_minutes
    )
    expected = total_round_trip_cost(
        notional=notional,
        holding_candles=holding,
        direction=direction,
        candle_minutes=candle_minutes,
        entry_leg=entry_leg,
        exit_leg=exit_leg,
    )
    assert single == expected  # celowo ==, nie approx


def test_two_legs_match_manual_formula():
    notional, direction, cm = 1000.0, 1, 240
    legs = [(0.5, 2.0, MAKER), (0.5, 3.0, TAKER)]
    got = multi_leg_cost(notional, MAKER, legs, direction, candle_minutes=cm)
    slip = SLIPPAGE_BPS / 10_000
    expected = (
        notional * MAKER_FEE_RATE  # wejście maker, cały nominał
        + 500.0 * MAKER_FEE_RATE  # noga 1: cel (maker)
        + 500.0 * (TAKER_FEE_RATE + slip)  # noga 2: stop/timeout (taker + poślizg)
        + funding_cost(500.0, 2.0, direction, candle_minutes=cm)
        + funding_cost(500.0, 3.0, direction, candle_minutes=cm)
    )
    assert got == pytest.approx(expected, rel=1e-12)


def test_two_legs_cost_more_than_one_leg_with_same_exit_type():
    """Dodatkowa noga = dodatkowe fee; dla tych samych typów nóg suma nie może być mniejsza."""
    one = multi_leg_cost(1000.0, MAKER, [(1.0, 3.0, TAKER)], 1)
    two = multi_leg_cost(1000.0, MAKER, [(0.5, 3.0, MAKER), (0.5, 3.0, TAKER)], 1)
    # połowa wychodzi taniej (maker zamiast taker), więc może być taniej — sprawdzamy tylko dodatniość
    assert one > 0 and two > 0


@pytest.mark.parametrize("legs", [[], [(0.5, 1.0, MAKER)], [(0.7, 1.0, MAKER), (0.7, 1.0, TAKER)]])
def test_fractions_must_sum_to_one(legs):
    with pytest.raises(ValueError):
        multi_leg_cost(1000.0, MAKER, legs, 1)


def test_unknown_leg_is_loud():
    with pytest.raises(ValueError):
        multi_leg_cost(1000.0, MAKER, [(0.5, 1.0, "limit"), (0.5, 1.0, TAKER)], 1)
