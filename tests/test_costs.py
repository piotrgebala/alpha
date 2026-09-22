"""
test_costs.py

Warstwa 1 (unit, algebraiczne) testy dla backtest/costs.py — proste sprawdzenie
wzorów kosztów transakcyjnych (docs/rag/04_narzedzia_zewnetrzne.md). Brak testu
leakage (koszty nie zależą od przyszłości).

H3: property-based testy WCHODZĄ tutaj mimo zapisu w docs/rag/05 ("wymagane tylko dla
risk_controller.py/labeling.py"). Powód: runda wprowadza niezmiennik MIĘDZY DWIEMA
ŚCIEŻKAMI KOSZTU (bramka `gate_cost_fraction` musi dominować każdy koszt journalowy
`round_trip_cost_fraction`), a takiego przykłady wymyślone ręcznie nie pilnują — trzeba
go sprawdzić przy DOWOLNYCH stawkach, żeby przeżył przyszłą zmianę fee.
"""

from __future__ import annotations

import pytest

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from backtest.costs import (
    CANDLE_MINUTES,
    EXECUTION_MAKER_LIMIT,
    EXECUTION_TAKER_ONLY,
    EXIT_REASON_SL,
    EXIT_REASON_TIMEOUT,
    EXIT_REASON_TP,
    FUNDING_PERIOD_HOURS,
    MAKER,
    MAKER_FEE_RATE,
    SLIPPAGE_BPS,
    TAKER,
    TAKER_FEE_RATE,
    VALID_EXECUTION_MODELS,
    VALID_EXIT_REASONS,
    execution_legs,
    exit_leg_for_reason,
    gate_cost_fraction,
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


# --- H3: noga "timeout" jako nazwany wariant + bramka wyprowadzana z journalu ---
#
# Dwie asercje sprzed H3 (`test_exit_leg_follows_exit_reason` z wariantem ("timeout", TAKER)
# i `test_execution_legs_maker_limit_depends_on_exit_reason` w test_engine.py) ZOSTAJA
# nietkniete - przypinaja domyslny argument. To bezposrednia konsekwencja wyboru "mierzymy
# pasmo" zamiast "przerzucamy flage": gdyby zmieniac domyslna, trzeba by je przepisac.


def test_exit_leg_timeout_maker_variant_changes_only_timeout() -> None:
    """Drugi kraniec pasma rusza WYLACZNIE noge timeout - tp i sl sa nietkniete."""
    assert exit_leg_for_reason(EXIT_REASON_TP, timeout_leg=MAKER) == MAKER
    assert exit_leg_for_reason(EXIT_REASON_SL, timeout_leg=MAKER) == TAKER
    assert exit_leg_for_reason(EXIT_REASON_TIMEOUT, timeout_leg=MAKER) == MAKER


@pytest.mark.parametrize("timeout_leg", [MAKER, TAKER])
def test_timeout_leg_never_makes_stop_loss_maker(timeout_leg: str) -> None:
    """
    Niezmiennik ekonomiczny: stop-loss MUSI byc market przy kazdej wartosci wariantu.

    Zlecenie limit nie daje gwarancji wyjscia, a stop-loss bez gwarancji wyjscia nie jest
    stop-lossem. Gdyby ktos kiedys rozszerzyl `timeout_leg` na "wszystkie nogi maker",
    ten test zapali sie pierwszy.
    """
    assert exit_leg_for_reason(EXIT_REASON_SL, timeout_leg=timeout_leg) == TAKER


@pytest.mark.parametrize("bad_reason", ["TP", "tp ", "stop", "", "vertical", "Timeout"])
def test_exit_leg_for_reason_rejects_unknown_reason(bad_reason: str) -> None:
    """
    Whitelist zamiast `else`. Do H3 stalo tu `return MAKER if reason == "tp" else TAKER`,
    wiec KAZDA z tych literowek cicho wybierala TAKER - blad niewidoczny w wyniku.
    """
    with pytest.raises(ValueError):
        exit_leg_for_reason(bad_reason)


def test_exit_leg_for_reason_rejects_unknown_timeout_leg() -> None:
    with pytest.raises(ValueError):
        exit_leg_for_reason(EXIT_REASON_TIMEOUT, timeout_leg="limit")


@pytest.mark.parametrize("exit_reason", VALID_EXIT_REASONS)
@pytest.mark.parametrize("timeout_leg", [MAKER, TAKER])
def test_execution_legs_taker_only_ignores_timeout_leg(exit_reason, timeout_leg) -> None:
    """Regresja baseline'u C2.10/C2.11: model taker_only jest gluchy na oba warianty."""
    assert execution_legs(EXECUTION_TAKER_ONLY, exit_reason, timeout_leg) == (TAKER, TAKER)


def test_execution_legs_rejects_unknown_execution_model() -> None:
    with pytest.raises(ValueError):
        execution_legs("maker_only", EXIT_REASON_TP)


def test_execution_legs_validates_reason_even_when_model_ignores_it() -> None:
    """
    taker_only nie czyta `exit_reason`, ale literowka i tak musi byc glosna - inaczej
    blad przechodzi cicho tylko dlatego, ze akurat wybrano model, ktory tego nie uzywa.
    """
    with pytest.raises(ValueError):
        execution_legs(EXECUTION_TAKER_ONLY, "vertical")


def _journal_cost(execution_model: str, exit_reason: str, timeout_leg: str) -> float:
    entry_leg, exit_leg = execution_legs(execution_model, exit_reason, timeout_leg)
    return round_trip_cost_fraction(entry_leg=entry_leg, exit_leg=exit_leg)


@pytest.mark.parametrize("execution_model", VALID_EXECUTION_MODELS)
@pytest.mark.parametrize("timeout_leg", [MAKER, TAKER])
def test_gate_cost_fraction_equals_max_over_exit_reasons(execution_model, timeout_leg) -> None:
    """Bramka to DOKLADNIE maksimum po osiagalnych powodach wyjscia, nie osobna formula."""
    expected = max(_journal_cost(execution_model, r, timeout_leg) for r in VALID_EXIT_REASONS)
    assert gate_cost_fraction(execution_model, timeout_leg) == expected


@pytest.mark.parametrize(
    "execution_model, exit_reason, timeout_leg, expected",
    [
        (EXECUTION_MAKER_LIMIT, EXIT_REASON_TP, TAKER, 0.0004),
        (EXECUTION_MAKER_LIMIT, EXIT_REASON_SL, TAKER, 0.0009),
        (EXECUTION_MAKER_LIMIT, EXIT_REASON_TIMEOUT, TAKER, 0.0009),
        (EXECUTION_MAKER_LIMIT, EXIT_REASON_TP, MAKER, 0.0004),
        (EXECUTION_MAKER_LIMIT, EXIT_REASON_SL, MAKER, 0.0009),
        (EXECUTION_MAKER_LIMIT, EXIT_REASON_TIMEOUT, MAKER, 0.0004),
        (EXECUTION_TAKER_ONLY, EXIT_REASON_TP, TAKER, 0.0014),
        (EXECUTION_TAKER_ONLY, EXIT_REASON_SL, TAKER, 0.0014),
        (EXECUTION_TAKER_ONLY, EXIT_REASON_TIMEOUT, TAKER, 0.0014),
        (EXECUTION_TAKER_ONLY, EXIT_REASON_TIMEOUT, MAKER, 0.0014),
    ],
)
def test_leg_cost_table_matches_hardcoded_literals(
    execution_model, exit_reason, timeout_leg, expected
) -> None:
    """
    KOTWICA NIEZALEZNA od `execution_legs`: pelna tabela kosztu round-trip per (model
    wykonania, powod wyjscia, noga timeout), wpisana LITERALAMI.

    Po co, skoro `test_gate_cost_fraction_equals_max_over_exit_reasons` juz sprawdza
    bramke: tamten test wyprowadza oczekiwana wartosc z tej samej `execution_legs`, ktora
    testuje, wiec blad w MAPOWANIU nog przesunalby obie strony rownosci naraz i przeszedl
    niezauwazony. Dokladnie ta sama dziura byla w walidacji "druga droga" w sekcji 4 rundy
    H3 (`backtest/run_timeout_leg_band.py`), ktora tez konsumowala `execution_legs`.
    Literaly ponizej sa jedynym miejscem w repo, ktore ZNA te liczby bez pytania kodu.

    Arytmetyka do recznego sprawdzenia (fee maker 0,02%, fee taker 0,05%, slippage 2 bps,
    slippage tylko na nogach taker):
      maker+maker = 0,02 + 0,02                       = 0,04%
      maker+taker = 0,02 + 0,05 + 0,02                = 0,09%
      taker+taker = 0,05 + 0,05 + 0,02 + 0,02         = 0,14%
    """
    assert _journal_cost(execution_model, exit_reason, timeout_leg) == pytest.approx(expected)


def test_gate_cost_fraction_baseline_values() -> None:
    """
    Regresja dwoch liczb cytowanych w runs/INDEX.md i w write-upie H2.0.

    0,0009 to DOKLADNIE wartosc, ktora do H3 produkowal literal w engine.py - dowod, ze
    przeniesienie bramki na `gate_cost_fraction` nie zmienilo niczego liczbowo.
    """
    assert gate_cost_fraction(EXECUTION_MAKER_LIMIT) == round_trip_cost_fraction(
        entry_leg=MAKER, exit_leg=TAKER
    )
    assert gate_cost_fraction(EXECUTION_MAKER_LIMIT) == pytest.approx(0.0009)
    assert gate_cost_fraction(EXECUTION_TAKER_ONLY) == pytest.approx(0.0014)


def test_gate_cost_fraction_is_invariant_to_timeout_leg() -> None:
    """
    KLUCZOWE dla uczciwosci pomiaru H3: maksimum realizuje `sl` (maker/taker), niezaleznie
    od nogi timeout. Dzieki temu bramka przepuszcza DOKLADNIE te same sygnaly w obu
    wariantach pasma, a roznica w wyniku nie moze pochodzic z innego lejka.
    """
    for model in VALID_EXECUTION_MODELS:
        assert gate_cost_fraction(model, MAKER) == gate_cost_fraction(model, TAKER)


def test_timeout_maker_saves_exactly_taker_minus_maker_plus_slippage() -> None:
    """Oszczednosc na nodze timeout to dokladnie (taker - maker) + slippage, nie 'mniej wiecej'."""
    notional = 10_000.0
    kwargs = dict(notional=notional, holding_candles=6, direction=1, entry_leg=MAKER)
    cost_taker = total_round_trip_cost(
        exit_leg=exit_leg_for_reason(EXIT_REASON_TIMEOUT, TAKER), **kwargs
    )
    cost_maker = total_round_trip_cost(
        exit_leg=exit_leg_for_reason(EXIT_REASON_TIMEOUT, MAKER), **kwargs
    )
    expected = notional * (TAKER_FEE_RATE - MAKER_FEE_RATE + SLIPPAGE_BPS / 10_000.0)
    assert cost_taker - cost_maker == pytest.approx(expected)
    assert expected == pytest.approx(notional * 0.0005)


# --- property (hypothesis): niezmiennik MIEDZY sciezkami kosztu ---

_RATES = st.floats(min_value=0.0, max_value=0.01, allow_nan=False, allow_infinity=False)
_SLIP = st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False)


@settings(max_examples=100, deadline=None)
@given(
    execution_model=st.sampled_from(VALID_EXECUTION_MODELS),
    exit_reason=st.sampled_from(VALID_EXIT_REASONS),
    timeout_leg=st.sampled_from([MAKER, TAKER]),
    maker_fee=_RATES,
    taker_fee=_RATES,
    slippage_bps=_SLIP,
)
def test_gate_cost_fraction_dominates_every_journal_cost_property(
    execution_model, exit_reason, timeout_leg, maker_fee, taker_fee, slippage_bps
) -> None:
    """
    NIEZMIENNIK RUNDY: bramka nigdy nie jest tansza niz koszt, ktory realnie obciazy
    journal. Sprawdzany przy DOWOLNYCH stawkach, zeby przezyl przyszla zmiane fee -
    przyklady wymyslone recznie pilnuja tego tylko dla dzisiejszych wartosci.
    """
    entry_leg, exit_leg = execution_legs(execution_model, exit_reason, timeout_leg)
    journal = round_trip_cost_fraction(
        taker_fee_rate=taker_fee,
        slippage_bps=slippage_bps,
        entry_leg=entry_leg,
        exit_leg=exit_leg,
        maker_fee_rate=maker_fee,
    )
    gate = gate_cost_fraction(
        execution_model,
        timeout_leg,
        taker_fee_rate=taker_fee,
        slippage_bps=slippage_bps,
        maker_fee_rate=maker_fee,
    )
    assert journal <= gate + 1e-15


@settings(max_examples=100, deadline=None)
@given(
    execution_model=st.sampled_from(VALID_EXECUTION_MODELS),
    timeout_leg=st.sampled_from([MAKER, TAKER]),
    maker_fee=_RATES,
    taker_fee=_RATES,
    slippage_bps=_SLIP,
)
def test_gate_cost_fraction_is_attained_property(
    execution_model, timeout_leg, maker_fee, taker_fee, slippage_bps
) -> None:
    """
    Bramka jest OSIAGANA przez co najmniej jeden powod wyjscia.

    Bez tego poprzedni test daloby sie "naprawic" zawyzeniem bramki dowolna stala -
    bylaby wtedy bezpieczna, ale odrzucalaby sygnaly bez powodu.
    """
    rates = dict(taker_fee_rate=taker_fee, slippage_bps=slippage_bps, maker_fee_rate=maker_fee)
    gate = gate_cost_fraction(execution_model, timeout_leg, **rates)
    costs = []
    for r in VALID_EXIT_REASONS:
        entry_leg, exit_leg = execution_legs(execution_model, r, timeout_leg)
        costs.append(
            round_trip_cost_fraction(entry_leg=entry_leg, exit_leg=exit_leg, **rates)
        )
    assert any(abs(c - gate) <= 1e-15 for c in costs)


@settings(max_examples=100, deadline=None)
@given(maker_fee=_RATES, taker_fee=_RATES, slippage_bps=_SLIP)
def test_timeout_maker_never_costs_more_than_timeout_taker_property(
    maker_fee, taker_fee, slippage_bps
) -> None:
    """
    Kraniec "maker" jest faktycznie OGRANICZENIEM GORNYM korzysci, przy zalozeniu
    maker_fee <= taker_fee. Gdyby stawki sie odwrocily, nazwy krancow pasma przestalyby
    opisywac to, co opisuja - dlatego zalozenie jest tu jawne, a nie milczace.
    """
    assume(maker_fee <= taker_fee)
    kwargs = dict(taker_fee_rate=taker_fee, slippage_bps=slippage_bps, maker_fee_rate=maker_fee)
    c_maker = round_trip_cost_fraction(
        entry_leg=MAKER, exit_leg=exit_leg_for_reason(EXIT_REASON_TIMEOUT, MAKER), **kwargs
    )
    c_taker = round_trip_cost_fraction(
        entry_leg=MAKER, exit_leg=exit_leg_for_reason(EXIT_REASON_TIMEOUT, TAKER), **kwargs
    )
    assert c_maker <= c_taker + 1e-15
