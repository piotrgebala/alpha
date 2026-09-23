"""
test_execution.py

Testy symulacji wykonania (`backtest/execution.py`, runda W1). Trzy grupy, w kolejności wagi:

1. WŁASNOŚCI (hypothesis) — to one chronią pomiar: brak lookaheadu (wynik zależy wyłącznie od
   świec `> t` i nie dalej niż `timeout_idx`), cena wypełnienia w zakresie świecy i po właściwej
   stronie poziomu, wyjście w oknie `[wypełnienie, timeout]` po cenie ze zbioru {TP, SL, close},
   brak przebicia ⇒ brak transakcji, zgodność trybów „bar” i „intrabar” na ścieżce monotonicznej.
2. PRZYKŁADY reguł 1–4 z pre-rejestracji (`runs/2026-09-23_w1-wykonanie-po-cenie/README.md`):
   ścisłe przebicie, wypełnienie po otwarciu przy luce, świeca wypełnienia bez TP, obie bariery
   w jednej świecy (reguła etykiety vs SL-first), timeout, przypięcie 5m do 4h.
3. Konstrukcja ścieżki drobnej: pełne bloki albo błąd, brak danych = −1.
"""

from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest.costs import EXIT_REASON_SL, EXIT_REASON_TIMEOUT, EXIT_REASON_TP, MAKER, TAKER
from backtest.execution import (
    ENTRY_LIMIT_CLOSE,
    ENTRY_LIMIT_PULLBACK,
    ENTRY_STOP_BREAKOUT,
    RESOLUTION_BAR,
    RESOLUTION_INTRABAR,
    TIE_CLOSER_TO_OPEN,
    TIE_SL_FIRST,
    EntryRule,
    Fill,
    IntrabarPath,
    barrier_levels,
    build_intrabar_path,
    crossed,
    fill_price_at,
    simulate_exit,
    simulate_fill,
    simulate_trade,
)

RULES = [
    EntryRule(ENTRY_LIMIT_CLOSE),
    EntryRule(ENTRY_LIMIT_PULLBACK, 0.5),
    EntryRule(ENTRY_STOP_BREAKOUT),
]


def candles(*rows: tuple[float, float, float, float]) -> tuple[np.ndarray, ...]:
    """rows = (open, high, low, close) per świeca → cztery tablice."""
    arr = np.array(rows, dtype=float)
    return arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]


def same_outcome(a, b) -> bool:
    """Równość wyników z NaN == NaN (pola nieużywane przy braku wypełnienia są NaN)."""
    da, db = asdict(a), asdict(b)
    for key, x in da.items():
        y = db[key]
        if isinstance(x, float) and isinstance(y, float) and np.isnan(x) and np.isnan(y):
            continue
        if x != y:
            return False
    return True


# --- reguła wejścia ----------------------------------------------------------------------------


def test_entry_rule_levels_and_legs():
    close_t, high_t, low_t, atr = 100.0, 103.0, 98.0, 2.0
    assert EntryRule(ENTRY_LIMIT_CLOSE).level(1, close_t, high_t, low_t, atr) == 100.0
    assert EntryRule(ENTRY_LIMIT_PULLBACK, 0.5).level(1, close_t, high_t, low_t, atr) == 99.0
    assert EntryRule(ENTRY_LIMIT_PULLBACK, 0.5).level(-1, close_t, high_t, low_t, atr) == 101.0
    assert EntryRule(ENTRY_STOP_BREAKOUT).level(1, close_t, high_t, low_t, atr) == 103.0
    assert EntryRule(ENTRY_STOP_BREAKOUT).level(-1, close_t, high_t, low_t, atr) == 98.0
    assert EntryRule(ENTRY_LIMIT_CLOSE).entry_leg == MAKER
    assert EntryRule(ENTRY_STOP_BREAKOUT).entry_leg == TAKER


@pytest.mark.parametrize(
    "bad", [("nieznany", 0.5), (ENTRY_LIMIT_PULLBACK, -0.1), (ENTRY_LIMIT_PULLBACK, float("nan"))]
)
def test_entry_rule_rejects_bad_arguments(bad):
    with pytest.raises(ValueError):
        EntryRule(*bad)


# --- reguła 1: ścisłe przebicie, cena wypełnienia -------------------------------------------------


def test_touch_is_not_a_fill_but_trade_through_is():
    # long limit po 100: low == 100 to dotknięcie (brak), low == 99.99 to przebicie
    assert not crossed(False, 1, 100.0, high_j=105.0, low_j=100.0)
    assert crossed(False, 1, 100.0, high_j=105.0, low_j=99.99)
    # short limit po 100: high musi przebić w górę
    assert not crossed(False, -1, 100.0, high_j=100.0, low_j=95.0)
    assert crossed(False, -1, 100.0, high_j=100.01, low_j=95.0)
    # long stop ponad 103: high musi przebić w górę; short stop pod 98: low w dół
    assert not crossed(True, 1, 103.0, high_j=103.0, low_j=99.0)
    assert crossed(True, 1, 103.0, high_j=103.5, low_j=99.0)
    assert crossed(True, -1, 98.0, high_j=101.0, low_j=97.0)


def test_fill_price_is_open_when_candle_opens_beyond_level():
    # long limit po 100, świeca otwiera się na 99 → wypełnienie po 99, na otwarciu
    assert fill_price_at(False, 1, 100.0, open_j=99.0) == (99.0, True)
    # long limit po 100, otwarcie 101 → wypełnienie po 100 gdzieś w środku
    assert fill_price_at(False, 1, 100.0, open_j=101.0) == (100.0, False)
    # long stop ponad 103, otwarcie 104 (luka) → po 104, na otwarciu
    assert fill_price_at(True, 1, 103.0, open_j=104.0) == (104.0, True)
    # short limit po 100, otwarcie 101 → po 101 (lepiej), na otwarciu
    assert fill_price_at(False, -1, 100.0, open_j=101.0) == (101.0, True)
    # short stop pod 98, otwarcie 97 (luka) → po 97, na otwarciu
    assert fill_price_at(True, -1, 98.0, open_j=97.0) == (97.0, True)


def test_simulate_fill_respects_validity_window():
    o, h, lo, c = candles((100, 101, 100, 100), (100, 102, 100, 101), (101, 102, 99, 100))
    rule = EntryRule(ENTRY_LIMIT_CLOSE)
    # poziom 100 przebity dopiero w świecy 2 (low 99) — przy ważności do świecy 1 brak wypełnienia
    assert simulate_fill(rule, 1, 100.0, o, h, lo, 1, 1) is None
    fill = simulate_fill(rule, 1, 100.0, o, h, lo, 1, 2)
    assert fill == Fill(idx=2, price=100.0, at_open=False)


# --- reguły 3–4: wyjścia ----------------------------------------------------------------------


def test_exit_in_fill_candle_counts_only_sl_when_not_filled_at_open():
    # long, TP 103, SL 97; świeca wypełnienia (idx 1) ma high 104 i low 96 — TP zignorowany, SL liczony
    o, h, lo, c = candles((100, 100, 100, 100), (101, 104, 96, 100))
    fill = Fill(idx=1, price=100.0, at_open=False)
    ex = simulate_exit(1, fill, 103.0, 97.0, o, h, lo, c, 1, TIE_CLOSER_TO_OPEN)
    assert ex.reason == EXIT_REASON_SL and ex.price == 97.0 and ex.idx == 1


def test_exit_in_fill_candle_uses_full_path_when_filled_at_open():
    # jak wyżej, ale wypełnienie na otwarciu (open 100 <= 100): obie bariery, bliższa otwarciu = TP (103 vs 97 równe → upper)
    o, h, lo, c = candles((100, 100, 100, 100), (100, 104, 96, 100))
    fill = Fill(idx=1, price=100.0, at_open=True)
    ex = simulate_exit(1, fill, 103.0, 97.0, o, h, lo, c, 1, TIE_CLOSER_TO_OPEN)
    assert ex.reason == EXIT_REASON_TP  # remis odległości → górna bariera, jak w labeling.py


def test_tie_rule_sl_first_on_fine_candles():
    o, h, lo, c = candles((100, 100, 100, 100), (100, 104, 96, 100))
    fill = Fill(idx=1, price=100.0, at_open=True)
    assert (
        simulate_exit(1, fill, 103.0, 97.0, o, h, lo, c, 1, TIE_SL_FIRST).reason == EXIT_REASON_SL
    )


def test_closer_to_open_rule_matches_labeling_for_short():
    # short: TP 97 (lower), SL 103 (upper); open 102 bliżej upper → SL pierwszy
    o, h, lo, c = candles((100, 100, 100, 100), (102, 104, 96, 100))
    fill = Fill(idx=1, price=100.0, at_open=True)
    assert (
        simulate_exit(-1, fill, 97.0, 103.0, o, h, lo, c, 1, TIE_CLOSER_TO_OPEN).reason
        == EXIT_REASON_SL
    )
    o, h, lo, c = candles((100, 100, 100, 100), (98, 104, 96, 100))  # open 98 bliżej lower (TP)
    assert (
        simulate_exit(-1, fill, 97.0, 103.0, o, h, lo, c, 1, TIE_CLOSER_TO_OPEN).reason
        == EXIT_REASON_TP
    )


def test_timeout_exits_at_close_of_last_candle():
    o, h, lo, c = candles((100, 100, 100, 100), (100, 101, 99, 100.5), (100.5, 101, 99.5, 100.2))
    fill = Fill(idx=1, price=100.0, at_open=True)
    ex = simulate_exit(1, fill, 103.0, 97.0, o, h, lo, c, 2, TIE_CLOSER_TO_OPEN)
    assert ex == (ex.__class__(idx=2, price=100.2, reason=EXIT_REASON_TIMEOUT))


def test_barrier_levels_symmetric_around_fill_price():
    assert barrier_levels(1, 100.0, 2.0, 1.5) == (103.0, 97.0)
    assert barrier_levels(-1, 100.0, 2.0, 1.5) == (97.0, 103.0)


# --- cała transakcja, tryb „bar” -------------------------------------------------------------


def test_simulate_trade_unfilled_when_level_never_crossed():
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 102, 100, 101), (101, 103, 100.5, 102), (102, 103, 101, 102)
    )
    out = simulate_trade(
        EntryRule(ENTRY_LIMIT_PULLBACK, 0.5), 1, 0, 1, 3, o, h, lo, c, atr_t=2.0, atr_multiplier=1.5
    )
    assert not out.filled and out.entry_level == 99.0 and out.resolution == RESOLUTION_BAR
    assert out.exit_reason is None


def test_simulate_trade_limit_close_fills_at_open_and_hits_tp():
    # sygnał t=0 close 100; świeca 1 otwiera 100 (<= 100 → wypełnienie na otwarciu po 100), high 103.5 >= TP 103
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 103.5, 99.5, 103), (103, 104, 102, 103), (103, 104, 102, 103)
    )
    out = simulate_trade(EntryRule(ENTRY_LIMIT_CLOSE), 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5)
    assert out.filled and out.fill_idx == 1 and out.fill_price == 100.0 and out.fill_at_open
    assert out.exit_reason == EXIT_REASON_TP and out.exit_price == 103.0 and out.exit_idx == 1


def test_simulate_trade_breakout_is_taker_and_anchors_barriers_at_fill():
    # sygnał t=0 high 101; świeca 1 przebija (high 102 > 101), otwiera 100.5 → wypełnienie po 101
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100.5, 102, 100, 101.5), (101.5, 102, 97.5, 98), (98, 99, 97, 98)
    )
    out = simulate_trade(EntryRule(ENTRY_STOP_BREAKOUT), 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5)
    assert out.filled and out.fill_price == 101.0 and not out.fill_at_open
    assert (out.tp_level, out.sl_level) == (104.0, 98.0)
    # świeca 1 po wypełnieniu: TP nie liczy się, SL 98 nie padł (low 100); świeca 2: low 97.5 <= 98 → SL
    assert out.exit_reason == EXIT_REASON_SL and out.exit_idx == 2


def test_simulate_trade_validity_never_exceeds_timeout():
    o, h, lo, c = candles(
        (100, 101, 99, 100), (101, 102, 100.5, 101), (101, 102, 100.5, 101), (101, 102, 99, 100)
    )
    # ważność 5 świec, timeout w świecy 3: przebicie w świecy 3 (low 99 < 100) — wypełnienie i timeout w tej samej świecy
    out = simulate_trade(EntryRule(ENTRY_LIMIT_CLOSE), 1, 0, 5, 3, o, h, lo, c, 2.0, 1.5)
    assert out.filled and out.fill_idx == 3 and out.exit_idx == 3
    assert out.exit_reason == EXIT_REASON_TIMEOUT and out.exit_price == 100.0


@pytest.mark.parametrize("validity,timeout", [(0, 3), (1, 0)])
def test_simulate_trade_rejects_bad_windows(validity, timeout):
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 101, 99, 100), (100, 101, 99, 100), (100, 101, 99, 100)
    )
    with pytest.raises(ValueError):
        simulate_trade(EntryRule(ENTRY_LIMIT_CLOSE), 1, 0, validity, timeout, o, h, lo, c, 2.0, 1.5)


# --- ścieżka drobna ----------------------------------------------------------------------------


def make_intrabar(
    bar_ts: pd.Series, per_bar: dict[int, list[tuple[float, float, float, float]]]
) -> pd.DataFrame:
    """Świece 5m dla wybranych świec 4h (`per_bar[j]` = lista 48 krotek OHLC)."""
    rows = []
    for j, ohlc in per_bar.items():
        assert len(ohlc) == 48
        for m, (o, h, lo, c) in enumerate(ohlc):
            rows.append((bar_ts.iloc[j] + pd.Timedelta(minutes=5 * m), o, h, lo, c, 1.0))
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def flat(o: float, h: float, lo: float, c: float) -> list[tuple[float, float, float, float]]:
    return [(o, h, lo, c)] * 48


def test_build_intrabar_path_marks_missing_bars_and_rejects_partial_blocks():
    bar_ts = pd.Series(pd.date_range("2026-01-01", periods=4, freq="4h", tz="UTC"))
    sub = make_intrabar(bar_ts, {1: flat(100, 101, 99, 100), 2: flat(100, 101, 99, 100)})
    path = build_intrabar_path(bar_ts, sub, candle_minutes=240)
    assert list(path.start) == [-1, 0, 48, -1] and list(path.count) == [0, 48, 48, 0]
    assert path.covers(1, 2) and not path.covers(0, 2) and not path.covers(2, 3)
    assert path.bar_of(0) == 1 and path.bar_of(47) == 1 and path.bar_of(48) == 2
    with pytest.raises(ValueError):
        build_intrabar_path(bar_ts, sub.iloc[:-1], candle_minutes=240)


def test_intrabar_resolves_order_that_bar_mode_must_guess():
    """Świeca 4h: open 100, high 104, low 96 — w trybie „bar” remis → TP (górna). Ścieżka 5m idzie
    NAJPIERW w dół do 96, potem w górę — w trybie „intrabar” wychodzi SL. To jest cała racja bytu
    części kalibracyjnej W1."""
    bar_ts = pd.Series(pd.date_range("2026-01-01", periods=4, freq="4h", tz="UTC"))
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 104, 96, 100), (100, 101, 99, 100), (100, 101, 99, 100)
    )
    down_then_up = [(100, 100, 96, 96)] * 24 + [(96, 104, 96, 100)] * 24
    sub = make_intrabar(
        bar_ts, {1: down_then_up, 2: flat(100, 101, 99, 100), 3: flat(100, 101, 99, 100)}
    )
    path = build_intrabar_path(bar_ts, sub, 240)
    rule = EntryRule(ENTRY_LIMIT_CLOSE)
    bar = simulate_trade(rule, 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5)
    fine = simulate_trade(rule, 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5, intrabar=path)
    assert bar.exit_reason == EXIT_REASON_TP and bar.resolution == RESOLUTION_BAR
    assert fine.exit_reason == EXIT_REASON_SL and fine.resolution == RESOLUTION_INTRABAR
    assert fine.fill_idx == 1 and fine.exit_idx == 1 and fine.fill_price == 100.0


def test_intrabar_requires_full_coverage_of_the_trade_window():
    bar_ts = pd.Series(pd.date_range("2026-01-01", periods=4, freq="4h", tz="UTC"))
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 101, 99, 100), (100, 101, 99, 100), (100, 101, 99, 100)
    )
    path = build_intrabar_path(bar_ts, make_intrabar(bar_ts, {1: flat(100, 101, 99, 100)}), 240)
    with pytest.raises(ValueError):
        simulate_trade(
            EntryRule(ENTRY_LIMIT_CLOSE), 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5, intrabar=path
        )


# --- własności (hypothesis) --------------------------------------------------------------------

N_BARS = 12
price_st = st.floats(min_value=50.0, max_value=150.0, allow_nan=False, allow_infinity=False)


@st.composite
def ohlc_arrays(draw):
    """Losowe, spójne świece: low <= min(open, close) <= max(open, close) <= high."""
    rows = []
    for _ in range(N_BARS):
        o = draw(price_st)
        c = draw(price_st)
        h = max(o, c) + draw(st.floats(min_value=0.0, max_value=5.0, allow_nan=False))
        lo = min(o, c) - draw(st.floats(min_value=0.0, max_value=5.0, allow_nan=False))
        rows.append((o, h, lo, c))
    return candles(*rows)


trade_args = dict(
    rule=st.sampled_from(RULES),
    direction=st.sampled_from([1.0, -1.0]),
    t=st.integers(min_value=0, max_value=N_BARS - 5),
    validity=st.integers(min_value=1, max_value=3),
    atr_t=st.floats(min_value=0.1, max_value=6.0, allow_nan=False),
)


@settings(max_examples=250, deadline=None)
@given(data=ohlc_arrays(), **trade_args)
def test_property_no_lookahead_and_no_look_before(data, rule, direction, t, validity, atr_t):
    """Zmiana świec poza `(t, t+V]` (w tym samej świecy t poza polami użytymi do poziomu) NIE zmienia wyniku."""
    o, h, lo, c = data
    timeout = t + 3
    base = simulate_trade(rule, direction, t, validity, timeout, o, h, lo, c, atr_t, 1.5)
    o2, h2, l2, c2 = (x.copy() for x in (o, h, lo, c))
    # przyszłość za horyzontem
    o2[timeout + 1 :] += 7.0
    h2[timeout + 1 :] += 9.0
    l2[timeout + 1 :] -= 9.0
    c2[timeout + 1 :] += 7.0
    # przeszłość przed sygnałem
    o2[:t] -= 3.0
    h2[:t] += 3.0
    l2[:t] -= 3.0
    c2[:t] -= 3.0
    again = simulate_trade(rule, direction, t, validity, timeout, o2, h2, l2, c2, atr_t, 1.5)
    assert same_outcome(again, base)


@settings(max_examples=250, deadline=None)
@given(data=ohlc_arrays(), **trade_args)
def test_property_fill_and_exit_are_physically_consistent(
    data, rule, direction, t, validity, atr_t
):
    o, h, lo, c = data
    timeout = t + 3
    out = simulate_trade(rule, direction, t, validity, timeout, o, h, lo, c, atr_t, 1.5)
    if not out.filled:
        # brak przebicia w oknie ważności
        last = min(t + validity, timeout)
        assert not any(
            crossed(rule.is_stop, direction, out.entry_level, h[j], lo[j])
            for j in range(t + 1, last + 1)
        )
        return
    f = out.fill_idx
    assert t < f <= min(t + validity, timeout)
    assert lo[f] <= out.fill_price <= h[f]
    # cena wypełnienia po właściwej stronie poziomu: limit nie gorzej niż poziom, stop nie lepiej
    waits_below = (direction > 0) != rule.is_stop
    assert (
        (out.fill_price <= out.entry_level) if waits_below else (out.fill_price >= out.entry_level)
    )
    assert f <= out.exit_idx <= timeout
    assert out.exit_price in (out.tp_level, out.sl_level, c[out.exit_idx])
    assert out.exit_reason in (EXIT_REASON_TP, EXIT_REASON_SL, EXIT_REASON_TIMEOUT)
    if out.exit_reason == EXIT_REASON_TP:
        assert out.exit_price == out.tp_level
    if out.exit_reason == EXIT_REASON_SL:
        assert out.exit_price == out.sl_level


@settings(max_examples=150, deadline=None)
@given(
    data=ohlc_arrays(),
    rule=st.sampled_from(RULES),
    direction=st.sampled_from([1.0, -1.0]),
    atr_t=st.floats(min_value=0.1, max_value=6.0, allow_nan=False),
)
def test_property_bar_and_intrabar_agree_on_monotone_paths(data, rule, direction, atr_t):
    """Gdy każda świeca 4h jest przebyta jednostajnie od open do close, oba tryby dają to samo
    wypełnienie i to samo wyjście (poza remisem odległości, który dla ścieżki monotonicznej nie istnieje).
    """
    o, h, lo, c = data
    # ścieżka monotoniczna: high/low = max/min(open, close) — nadpisujemy, żeby 5m było spójne z 4h
    h = np.maximum(o, c)
    lo = np.minimum(o, c)
    t, validity, timeout = 0, 1, 3
    bar_ts = pd.Series(pd.date_range("2026-01-01", periods=N_BARS, freq="4h", tz="UTC"))
    per_bar = {}
    for j in range(1, timeout + 1):
        steps = np.linspace(o[j], c[j], 49)
        per_bar[j] = [
            (steps[m], max(steps[m], steps[m + 1]), min(steps[m], steps[m + 1]), steps[m + 1])
            for m in range(48)
        ]
    path = build_intrabar_path(bar_ts, make_intrabar(bar_ts, per_bar), 240)
    bar = simulate_trade(rule, direction, t, validity, timeout, o, h, lo, c, atr_t, 1.5)
    fine = simulate_trade(
        rule, direction, t, validity, timeout, o, h, lo, c, atr_t, 1.5, intrabar=path
    )
    assert bar.filled == fine.filled
    if bar.filled:
        assert bar.fill_idx == fine.fill_idx
        assert bar.fill_price == pytest.approx(fine.fill_price)
        assert bar.fill_at_open == fine.fill_at_open
        # Wyjścia zgadzają się, gdy wypełnienie nastąpiło na otwarciu (oba tryby liczą pełną
        # ścieżkę). Przy wypełnieniu w środku świecy tryb „bar” jest Z KONSTRUKCJI ostrożniejszy
        # (ignoruje TP i liczy SL, choć na ścieżce monotonicznej SL mógł paść PRZED wypełnieniem)
        # — to mierzy część kalibracyjna W1, patrz test przykładowy niżej.
        if bar.fill_at_open:
            assert bar.exit_reason == fine.exit_reason
            assert bar.exit_idx == fine.exit_idx


def test_bar_mode_is_more_conservative_than_intrabar_inside_fill_candle():
    """Stop na wybiciu wypełniony w środku świecy, która potem monotonicznie idzie do TP:
    tryb „bar” nie zalicza TP w świecy wypełnienia (może paść przed), tryb „intrabar” widzi,
    że padł PO wypełnieniu. Kierunek obciążenia trybu „bar”: na niekorzyść strategii."""
    bar_ts = pd.Series(pd.date_range("2026-01-01", periods=4, freq="4h", tz="UTC"))
    # sygnał t=0: high 101 (poziom stopu); świeca 1: 100 → 105 monotonicznie (przebija 101, potem TP 104)
    o, h, lo, c = candles(
        (100, 101, 99, 100), (100, 105, 100, 105), (105, 105, 104, 104.5), (104.5, 105, 104, 104.5)
    )
    steps = np.linspace(100.0, 105.0, 49)
    up = [(steps[m], steps[m + 1], steps[m], steps[m + 1]) for m in range(48)]
    path = build_intrabar_path(
        bar_ts,
        make_intrabar(
            bar_ts, {1: up, 2: flat(105, 105, 104, 104.5), 3: flat(104.5, 105, 104, 104.5)}
        ),
        240,
    )
    rule = EntryRule(ENTRY_STOP_BREAKOUT)
    bar = simulate_trade(rule, 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5)
    fine = simulate_trade(rule, 1, 0, 1, 3, o, h, lo, c, 2.0, 1.5, intrabar=path)
    assert bar.fill_price == fine.fill_price == 101.0 and not bar.fill_at_open
    assert fine.exit_reason == EXIT_REASON_TP and fine.exit_idx == 1
    assert (
        bar.exit_reason == EXIT_REASON_TP and bar.exit_idx == 2
    )  # dopiero następna świeca (high 105 >= 104)
