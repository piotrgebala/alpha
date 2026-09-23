"""
test_execution_managed.py

Wyjścia wielonogowe (`ManagedExitRule`, runda N1) w `backtest/execution.py`.

Najpierw WŁASNOŚCI (hypothesis) — to one chronią pomiar: ułamki nóg sumują się do 1, nogi są
w porządku czasowym i w oknie `[wypełnienie, timeout]`, stop na wejściu pojawia się TYLKO po
częściowym celu, cena każdej nogi należy do zbioru {bliższy cel, dalszy cel, stop, wejście,
close[t+V]}, brak lookaheadu, a `exit_*` wyniku opisuje ostatnią nogę. Potem PRZYKŁADY reguł 1–7
z pre-rejestracji (`runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md`).
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest.costs import (
    EXIT_REASON_BE_STOP,
    EXIT_REASON_SL,
    EXIT_REASON_TIMEOUT,
    EXIT_REASON_TP,
    EXIT_REASON_TP_PARTIAL,
)
from backtest.execution import (
    ENTRY_LIMIT_CLOSE,
    EntryRule,
    ExitLeg,
    ManagedExitRule,
    managed_targets,
    simulate_trade,
)

RULE = ManagedExitRule(partial_fraction=0.5, near_pct=0.0167)
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
ATR, M = 2.0, 1.5  # 1,5·ATR = 3,0 → przy wejściu 100: stop 97, dalszy cel 103, bliższy 101,67


def candles(*rows):
    arr = np.array(rows, dtype=float)
    return arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]


def trade(o, h, lo, c, direction=1.0, rule=RULE, atr=ATR):
    """Sygnał t=0, ważność 1, timeout t+3."""
    return simulate_trade(ENTRY, direction, 0, 1, 3, o, h, lo, c, atr, M, exit_rule=rule)


# --- reguła 1: cele uporządkowane -------------------------------------------------------------


def test_targets_near_first_including_inverted_case():
    assert managed_targets(1, 100.0, 2.0, 1.5, RULE) == (pytest.approx(101.67), 103.0)
    assert managed_targets(-1, 100.0, 2.0, 1.5, RULE) == (pytest.approx(98.33), 97.0)
    # cele „odwrócone": 1,5·ATR = 0,75 < 1,67 → bliższy = cel ATR
    assert managed_targets(1, 100.0, 0.5, 1.5, RULE) == (100.75, pytest.approx(101.67))


@pytest.mark.parametrize(
    "bad",
    [
        dict(partial_fraction=0.0),
        dict(partial_fraction=1.0),
        dict(near_pct=0.0),
        dict(near_pct=-0.01),
    ],
)
def test_rule_rejects_bad_parameters(bad):
    with pytest.raises(ValueError):
        ManagedExitRule(**bad)


# --- reguły 2–6: przykłady --------------------------------------------------------------------


def test_partial_at_near_then_rest_at_far():
    # wypełnienie na otwarciu świecy 1 (open 100 <= 100), bliższy cel 101,67 w świecy 1, dalszy 103 w świecy 2
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 102, 99.8, 101.5), (101.5, 103.5, 101, 103), (103, 104, 102, 103)
    )
    out = trade(o, h, lo, c)
    assert out.filled and out.fill_at_open
    assert out.legs == (
        ExitLeg(0.5, 1, pytest.approx(101.67), EXIT_REASON_TP_PARTIAL),
        ExitLeg(0.5, 2, 103.0, EXIT_REASON_TP),
    )
    assert (out.exit_idx, out.exit_price, out.exit_reason) == (2, 103.0, EXIT_REASON_TP)


def test_partial_then_break_even_stop():
    o, h, lo, c = candles(
        (100, 101, 99, 100),
        (100, 102, 99.8, 101.5),
        (101.5, 102, 99.9, 100.5),
        (100.5, 101, 100, 100.5),
    )
    out = trade(o, h, lo, c)
    assert out.legs[0].reason == EXIT_REASON_TP_PARTIAL
    assert out.legs[1] == ExitLeg(0.5, 2, 100.0, EXIT_REASON_BE_STOP)


def test_partial_then_timeout_for_the_rest():
    o, h, lo, c = candles(
        (100, 101, 99, 100),
        (100, 102, 99.8, 101.5),
        (101.5, 102.5, 100.5, 101),
        (101, 102, 100.5, 101.2),
    )
    out = trade(o, h, lo, c)
    assert out.legs[0].reason == EXIT_REASON_TP_PARTIAL
    assert out.legs[1] == ExitLeg(0.5, 3, 101.2, EXIT_REASON_TIMEOUT)


def test_stop_before_near_closes_whole_position():
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 101, 96.5, 97.5), (97.5, 103, 97, 102), (102, 104, 101, 103)
    )
    out = trade(o, h, lo, c)
    assert out.legs == (ExitLeg(1.0, 1, 97.0, EXIT_REASON_SL),)


def test_timeout_without_near_closes_whole_position():
    o, h, lo, c = candles(
        (100, 101, 99, 100),
        (100, 101, 99.5, 100.5),
        (100.5, 101.5, 99.5, 100.8),
        (100.8, 101.5, 100, 100.3),
    )
    out = trade(o, h, lo, c)
    assert out.legs == (ExitLeg(1.0, 3, 100.3, EXIT_REASON_TIMEOUT),)


def test_far_in_near_candle_only_when_close_proves_it():
    # świeca 1 sięga i bliższego (101,67), i dalszego (103) celu, ale zamyka się na 102 < 103:
    # nie wiadomo, czy dalszy padł PO bliższym → dalszy dopiero od świecy 2 (Poprawka 1)
    o, h, lo, c = candles(
        (100, 101, 99, 100),
        (100, 103.5, 99.9, 102),
        (102, 103.2, 101.5, 103),
        (103, 104, 102, 103),
    )
    out = trade(o, h, lo, c)
    assert [leg.idx for leg in out.legs] == [1, 2] and out.legs[1].reason == EXIT_REASON_TP
    # ta sama świeca zamknięta na 103,2 >= 103: ścieżka od bliższego celu do close przecięła dalszy → obie nogi w świecy 1
    o2, h2, lo2, c2 = candles(
        (100, 101, 99, 100),
        (100, 103.5, 99.9, 103.2),
        (103.2, 103.4, 102, 103),
        (103, 104, 102, 103),
    )
    out2 = trade(o2, h2, lo2, c2)
    assert out2.legs == (
        ExitLeg(0.5, 1, pytest.approx(101.67), EXIT_REASON_TP_PARTIAL),
        ExitLeg(0.5, 1, 103.0, EXIT_REASON_TP),
    )


def test_near_at_open_counts_full_candle_path():
    # świeca 2 otwiera się luką PONAD bliższym celem (102 >= 101,67): cała jej ścieżka liczy się dalej
    o, h, lo, c = candles(
        (100, 101, 99, 100),
        (100, 101, 99.5, 100.8),
        (102, 103.5, 101.5, 103),
        (103, 104, 102, 103),
    )
    out = trade(o, h, lo, c)
    assert [leg.idx for leg in out.legs] == [2, 2]
    assert out.legs[1] == ExitLeg(0.5, 2, 103.0, EXIT_REASON_TP)


def test_break_even_stop_in_near_candle_only_when_close_proves_it():
    # bliższy cel w środku świecy 1, świeca zamyka się PONIŻEJ wejścia → stop na wejściu padł po celu
    o, h, lo, c = candles(
        (100, 101, 99, 100),
        (100, 102, 99.5, 99.8),
        (99.8, 101, 99.5, 100.5),
        (100.5, 101, 100, 100.6),
    )
    out = trade(o, h, lo, c)
    assert out.legs == (
        ExitLeg(0.5, 1, pytest.approx(101.67), EXIT_REASON_TP_PARTIAL),
        ExitLeg(0.5, 1, 100.0, EXIT_REASON_BE_STOP),
    )
    # ta sama świeca zamknięta nad wejściem (100,5): minimum 99,5 to ślad wypełnienia, nie stopu → nic w świecy 1
    o2, h2, lo2, c2 = candles(
        (100, 101, 99, 100),
        (100, 102, 99.5, 100.5),
        (100.5, 101, 100.2, 100.8),
        (100.8, 101, 100.3, 100.6),
    )
    out2 = trade(o2, h2, lo2, c2)
    assert out2.legs[0].idx == 1 and out2.legs[1] == ExitLeg(0.5, 3, 100.6, EXIT_REASON_TIMEOUT)


def test_short_mirror_partial_then_far():
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 100.2, 98, 98.5), (98.5, 99, 96.5, 97), (97, 98, 96, 97)
    )
    out = trade(o, h, lo, c, direction=-1.0)
    assert out.legs == (
        ExitLeg(0.5, 1, pytest.approx(98.33), EXIT_REASON_TP_PARTIAL),
        ExitLeg(0.5, 2, 97.0, EXIT_REASON_TP),
    )


def test_inverted_targets_take_partial_at_atr_target_first():
    # ATR mały: 1,5·ATR = 0,75 < 1,67 → bliższy = 100,75, dalszy = 101,67
    o, h, lo, c = candles(
        (100, 100.5, 99.5, 100),
        (100, 101, 99.9, 100.9),
        (100.9, 101.8, 100.8, 101.7),
        (101.7, 102, 101, 101.5),
    )
    out = trade(o, h, lo, c, atr=0.5)
    assert out.legs[0] == ExitLeg(0.5, 1, 100.75, EXIT_REASON_TP_PARTIAL)
    assert out.legs[1].reason == EXIT_REASON_TP and out.legs[1].price == pytest.approx(101.67)


def test_no_rule_gives_single_leg_equal_to_exit_fields():
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 103.5, 99.5, 103), (103, 104, 102, 103), (103, 104, 102, 103)
    )
    out = simulate_trade(ENTRY, 1.0, 0, 1, 3, o, h, lo, c, ATR, M)
    assert out.legs == (ExitLeg(1.0, out.exit_idx, out.exit_price, out.exit_reason),)


# --- własności --------------------------------------------------------------------------------

N_BARS = 10
price_st = st.floats(min_value=50.0, max_value=150.0, allow_nan=False, allow_infinity=False)


@st.composite
def ohlc(draw):
    rows = []
    for _ in range(N_BARS):
        o = draw(price_st)
        c = draw(price_st)
        h = max(o, c) + draw(st.floats(min_value=0.0, max_value=5.0, allow_nan=False))
        lo = min(o, c) - draw(st.floats(min_value=0.0, max_value=5.0, allow_nan=False))
        rows.append((o, h, lo, c))
    return candles(*rows)


@st.composite
def rules(draw):
    return ManagedExitRule(
        partial_fraction=draw(st.floats(min_value=0.1, max_value=0.9)),
        near_pct=draw(st.floats(min_value=0.001, max_value=0.05)),
    )


ARGS = dict(
    data=ohlc(),
    rule=rules(),
    direction=st.sampled_from([1.0, -1.0]),
    t=st.integers(min_value=0, max_value=N_BARS - 5),
    atr=st.floats(min_value=0.1, max_value=6.0, allow_nan=False),
)


@settings(max_examples=300, deadline=None)
@given(**ARGS)
def test_property_legs_are_consistent(data, rule, direction, t, atr):
    o, h, lo, c = data
    timeout = t + 3
    out = simulate_trade(ENTRY, direction, t, 1, timeout, o, h, lo, c, atr, M, exit_rule=rule)
    if not out.filled:
        assert out.legs == ()
        return
    legs = out.legs
    assert 1 <= len(legs) <= 2
    assert sum(leg.fraction for leg in legs) == pytest.approx(1.0)
    assert all(out.fill_idx <= leg.idx <= timeout for leg in legs)
    assert all(a.idx <= b.idx for a, b in zip(legs, legs[1:], strict=False))
    near, far = managed_targets(direction, out.fill_price, atr, M, rule)
    stop = out.fill_price - direction * M * atr
    allowed = {near, far, stop, out.fill_price, float(c[timeout])}
    for leg in legs:
        assert any(leg.price == pytest.approx(p) for p in allowed)
    if len(legs) == 1:
        assert legs[0].reason in (EXIT_REASON_SL, EXIT_REASON_TIMEOUT)
        assert legs[0].fraction == 1.0
    else:
        assert legs[0].reason == EXIT_REASON_TP_PARTIAL and legs[0].price == pytest.approx(near)
        assert legs[0].fraction == pytest.approx(rule.partial_fraction)
        assert legs[1].reason in (EXIT_REASON_TP, EXIT_REASON_BE_STOP, EXIT_REASON_TIMEOUT)
        if legs[1].reason == EXIT_REASON_BE_STOP:
            assert legs[1].price == out.fill_price
        if legs[1].reason == EXIT_REASON_TP:
            assert legs[1].price == pytest.approx(far)
    last = legs[-1]
    assert (out.exit_idx, out.exit_price, out.exit_reason) == (last.idx, last.price, last.reason)


@settings(max_examples=200, deadline=None)
@given(**ARGS)
def test_property_no_lookahead(data, rule, direction, t, atr):
    o, h, lo, c = data
    timeout = t + 3
    base = simulate_trade(ENTRY, direction, t, 1, timeout, o, h, lo, c, atr, M, exit_rule=rule)
    o2, h2, lo2, c2 = (x.copy() for x in (o, h, lo, c))
    o2[timeout + 1 :] += 9.0
    h2[timeout + 1 :] += 11.0
    lo2[timeout + 1 :] -= 11.0
    c2[timeout + 1 :] += 9.0
    o2[:t] -= 4.0
    h2[:t] += 4.0
    lo2[:t] -= 4.0
    c2[:t] -= 4.0
    again = simulate_trade(ENTRY, direction, t, 1, timeout, o2, h2, lo2, c2, atr, M, exit_rule=rule)
    assert again.filled == base.filled and again.legs == base.legs
