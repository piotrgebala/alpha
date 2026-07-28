"""
test_costs.py

Warstwa 1 (unit, algebraiczne) testy dla backtest/costs.py — proste sprawdzenie
wzorów kosztów transakcyjnych (docs/rag/04_narzedzia_zewnetrzne.md). Brak testu
leakage (koszty nie zależą od przyszłości) i brak wymogu hypothesis (DoD,
docs/rag/05: property-based testy wymagane tylko dla risk_controller.py/labeling.py).
"""

from __future__ import annotations

import pytest

from backtest.costs import (
    CANDLE_MINUTES,
    FUNDING_PERIOD_HOURS,
    round_trip_fee_cost,
    slippage_cost,
    total_round_trip_cost,
)
from backtest.costs import funding_cost as funding_cost_fn


def test_round_trip_fee_cost_is_double_single_side_fee() -> None:
    notional = 10_000.0
    fee_rate = 0.0005
    assert round_trip_fee_cost(notional, fee_rate) == pytest.approx(2 * notional * fee_rate)


def test_slippage_cost_matches_bps_formula() -> None:
    notional = 20_000.0
    bps = 2.0
    assert slippage_cost(notional, bps) == pytest.approx(notional * bps / 10_000.0)


def test_funding_cost_long_pays_positive_funding() -> None:
    # direction=+1 (long), funding_rate_8h dodatni -> koszt dodatni (long płaci funding).
    notional = 10_000.0
    holding_candles = FUNDING_PERIOD_HOURS * 60 / CANDLE_MINUTES  # równo 1 okres funding (8h)
    cost = funding_cost_fn(notional, holding_candles, direction=1, funding_rate_8h=0.0001)
    assert cost == pytest.approx(10_000.0 * 0.0001 * 1.0)


def test_funding_cost_short_receives_positive_funding() -> None:
    # direction=-1 (short) przy dodatnim funding_rate_8h -> koszt ujemny (short otrzymuje).
    notional = 10_000.0
    holding_candles = FUNDING_PERIOD_HOURS * 60 / CANDLE_MINUTES
    cost = funding_cost_fn(notional, holding_candles, direction=-1, funding_rate_8h=0.0001)
    assert cost == pytest.approx(-10_000.0 * 0.0001 * 1.0)


def test_funding_cost_scales_linearly_with_holding_periods() -> None:
    notional = 10_000.0
    one_period_candles = FUNDING_PERIOD_HOURS * 60 / CANDLE_MINUTES
    cost_1 = funding_cost_fn(notional, one_period_candles, direction=1, funding_rate_8h=0.0002)
    cost_3 = funding_cost_fn(notional, one_period_candles * 3, direction=1, funding_rate_8h=0.0002)
    assert cost_3 == pytest.approx(cost_1 * 3)


def test_total_round_trip_cost_is_sum_of_components() -> None:
    notional = 15_000.0
    holding_candles = 12.0
    direction = 1
    taker_fee_rate = 0.0005
    funding_rate_8h = 0.0001
    slippage_bps = 2.0

    expected_fee = round_trip_fee_cost(notional, taker_fee_rate)
    expected_funding = funding_cost_fn(notional, holding_candles, direction, funding_rate_8h)
    expected_slippage = 2.0 * slippage_cost(notional, slippage_bps)
    expected_total = expected_fee + expected_funding + expected_slippage

    total = total_round_trip_cost(
        notional=notional,
        holding_candles=holding_candles,
        direction=direction,
        taker_fee_rate=taker_fee_rate,
        funding_rate_8h=funding_rate_8h,
        slippage_bps=slippage_bps,
    )
    assert total == pytest.approx(expected_total)


def test_total_round_trip_cost_zero_holding_has_no_funding_component() -> None:
    notional = 15_000.0
    total = total_round_trip_cost(notional=notional, holding_candles=0.0, direction=1)
    expected = round_trip_fee_cost(notional) + 2.0 * slippage_cost(notional)
    assert total == pytest.approx(expected)
