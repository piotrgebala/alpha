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
    MAKER,
    MAKER_FEE_RATE,
    SLIPPAGE_BPS,
    TAKER,
    TAKER_FEE_RATE,
    exit_leg_for_reason,
    leg_fee_rate,
    round_trip_cost_fraction,
    round_trip_fee_cost,
    slippage_cost,
    total_round_trip_cost,
)
from backtest.costs import funding_cost as funding_cost_fn


def test_round_trip_fee_cost_is_double_single_side_fee() -> None:
    notional = 10_000.0
    fee_rate = 0.0005
    assert round_trip_fee_cost(notional, fee_rate) == pytest.approx(
        2 * notional * fee_rate
    )


def test_slippage_cost_matches_bps_formula() -> None:
    notional = 20_000.0
    bps = 2.0
    assert slippage_cost(notional, bps) == pytest.approx(notional * bps / 10_000.0)


def test_funding_cost_long_pays_positive_funding() -> None:
    # direction=+1 (long), funding_rate_8h dodatni -> koszt dodatni (long płaci funding).
    notional = 10_000.0
    holding_candles = (
        FUNDING_PERIOD_HOURS * 60 / CANDLE_MINUTES
    )  # równo 1 okres funding (8h)
    cost = funding_cost_fn(
        notional, holding_candles, direction=1, funding_rate_8h=0.0001
    )
    assert cost == pytest.approx(10_000.0 * 0.0001 * 1.0)


def test_funding_cost_short_receives_positive_funding() -> None:
    # direction=-1 (short) przy dodatnim funding_rate_8h -> koszt ujemny (short otrzymuje).
    notional = 10_000.0
    holding_candles = FUNDING_PERIOD_HOURS * 60 / CANDLE_MINUTES
    cost = funding_cost_fn(
        notional, holding_candles, direction=-1, funding_rate_8h=0.0001
    )
    assert cost == pytest.approx(-10_000.0 * 0.0001 * 1.0)


def test_funding_cost_scales_linearly_with_holding_periods() -> None:
    notional = 10_000.0
    one_period_candles = FUNDING_PERIOD_HOURS * 60 / CANDLE_MINUTES
    cost_1 = funding_cost_fn(
        notional, one_period_candles, direction=1, funding_rate_8h=0.0002
    )
    cost_3 = funding_cost_fn(
        notional, one_period_candles * 3, direction=1, funding_rate_8h=0.0002
    )
    assert cost_3 == pytest.approx(cost_1 * 3)


def test_total_round_trip_cost_is_sum_of_components() -> None:
    notional = 15_000.0
    holding_candles = 12.0
    direction = 1
    taker_fee_rate = 0.0005
    funding_rate_8h = 0.0001
    slippage_bps = 2.0

    expected_fee = round_trip_fee_cost(notional, taker_fee_rate)
    expected_funding = funding_cost_fn(
        notional, holding_candles, direction, funding_rate_8h
    )
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


# ---------------------------------------------------------------------------
# Commit 2d — round_trip_cost_fraction (bramka wykonalności kosztowej)
# ---------------------------------------------------------------------------


def test_round_trip_cost_fraction_matches_manual_formula() -> None:
    # 2x taker 0.05% + 2x slippage 2bps = 0.100% + 0.040% = 0.140% nominału.
    assert round_trip_cost_fraction() == pytest.approx(0.0014)


def test_round_trip_cost_fraction_consistent_with_total_round_trip_cost() -> None:
    # Ta sama liczba co total_round_trip_cost po odjęciu funding (którego ta funkcja
    # świadomie nie zawiera — zależy od kierunku i czasu trzymania).
    notional = 50_000.0
    fee_and_slippage = round_trip_fee_cost(notional) + 2.0 * slippage_cost(notional)
    assert round_trip_cost_fraction() * notional == pytest.approx(fee_and_slippage)


def test_round_trip_cost_fraction_scales_with_inputs() -> None:
    assert round_trip_cost_fraction(
        taker_fee_rate=0.0002, slippage_bps=0.0
    ) == pytest.approx(0.0004)


# ---------------------------------------------------------------------------
# Commit 2.12 (Backlog Z6): koszt zależny od typu zlecenia per noga
# ---------------------------------------------------------------------------


def test_maker_fee_is_cheaper_than_taker() -> None:
    """Niezmiennik ekonomiczny — gdyby się odwrócił, cały sens modelu maker znika."""
    assert MAKER_FEE_RATE < TAKER_FEE_RATE
    assert leg_fee_rate(MAKER) < leg_fee_rate(TAKER)


def test_leg_fee_rate_rejects_unknown_leg() -> None:
    """Literówka w nazwie nogi musi być błędem głośnym, nie cichym wyborem stawki."""
    with pytest.raises(ValueError):
        leg_fee_rate("limit")


@pytest.mark.parametrize(
    "exit_reason, expected_leg",
    [("tp", MAKER), ("sl", TAKER), ("timeout", TAKER)],
)
def test_exit_leg_follows_exit_reason(exit_reason: str, expected_leg: str) -> None:
    """TP może spoczywać w księdze (maker); SL i timeout muszą być market (taker)."""
    assert exit_leg_for_reason(exit_reason) == expected_leg


def test_round_trip_cost_fraction_taker_only_is_backward_compatible() -> None:
    """Domyślne taker/taker MUSI dać 0.0014 — baseline C2.10/C2.11 odtwarzalny."""
    assert round_trip_cost_fraction() == pytest.approx(0.0014)
    assert round_trip_cost_fraction(entry_leg=TAKER, exit_leg=TAKER) == pytest.approx(0.0014)


def test_round_trip_cost_fraction_maker_entry_taker_exit() -> None:
    """maker wejście (0.02%, bez poślizgu) + taker wyjście (0.05% + 2bps) = 0.09%."""
    fraction = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
    assert fraction == pytest.approx(0.0002 + 0.0005 + 0.0002)


def test_round_trip_cost_fraction_both_maker_pays_no_slippage() -> None:
    """Zlecenie limit spoczywające w księdze samo wyznacza cenę — zero poślizgu."""
    assert round_trip_cost_fraction(entry_leg=MAKER, exit_leg=MAKER) == pytest.approx(0.0004)


def test_total_round_trip_cost_charges_slippage_only_on_taker_legs() -> None:
    notional = 10_000.0
    both_maker = total_round_trip_cost(
        notional=notional, holding_candles=0, direction=1, entry_leg=MAKER, exit_leg=MAKER
    )
    # Zero nóg taker => zero poślizgu; zostaje samo fee 2 x maker.
    assert both_maker == pytest.approx(2.0 * notional * MAKER_FEE_RATE)

    one_taker = total_round_trip_cost(
        notional=notional, holding_candles=0, direction=1, entry_leg=MAKER, exit_leg=TAKER
    )
    assert one_taker - both_maker == pytest.approx(
        notional * (TAKER_FEE_RATE - MAKER_FEE_RATE) + slippage_cost(notional)
    )


def test_winning_trade_is_cheaper_than_losing_trade() -> None:
    """
    Asymetria wynikająca z mechaniki: TP wychodzi limitem (maker), SL marketem (taker).
    Działa na NIEKORZYŚĆ strategii o niskiej trafności — czyli konserwatywnie wobec
    naszej hipotezy, nie na jej korzyść.
    """
    kwargs = dict(notional=10_000.0, holding_candles=6, direction=1, entry_leg=MAKER)
    cost_tp = total_round_trip_cost(exit_leg=exit_leg_for_reason("tp"), **kwargs)
    cost_sl = total_round_trip_cost(exit_leg=exit_leg_for_reason("sl"), **kwargs)
    assert cost_tp < cost_sl


def test_total_round_trip_cost_taker_only_matches_legacy_formula() -> None:
    """Regresja: domyślne argumenty liczą DOKŁADNIE to, co model sprzed Commitu 2.12."""
    notional, holding, direction = 25_000.0, 9.0, -1
    legacy = (
        round_trip_fee_cost(notional, TAKER_FEE_RATE)
        + funding_cost_fn(notional, holding, direction)
        + 2.0 * slippage_cost(notional, SLIPPAGE_BPS)
    )
    assert total_round_trip_cost(
        notional=notional, holding_candles=holding, direction=direction
    ) == pytest.approx(legacy)


def test_maker_model_is_strictly_cheaper_than_taker_only() -> None:
    """Sedno Rundy 2: przy tej samej transakcji nowy model wykonania kosztuje mniej."""
    kwargs = dict(notional=10_000.0, holding_candles=6, direction=1)
    taker_only = total_round_trip_cost(entry_leg=TAKER, exit_leg=TAKER, **kwargs)
    maker_sl = total_round_trip_cost(entry_leg=MAKER, exit_leg=TAKER, **kwargs)
    maker_tp = total_round_trip_cost(entry_leg=MAKER, exit_leg=MAKER, **kwargs)
    assert maker_tp < maker_sl < taker_only
