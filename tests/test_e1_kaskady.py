"""Testy wykonywalnej definicji kaskady E1 (`backtest/e1_kaskady.py`, karta `runs/DRAFT_E1.md` §4) —
bez sieci, bez cen: próg, okno przesuwne, blokada 24 h, strona niejednoznaczna, uniwersum miesiąca,
czas wejścia; właściwości w `hypothesis` (brak nakładania transakcji na monecie, monotoniczność progu).
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import e1_kaskady as e1

D0 = 1_790_812_800_000  # 2026-10-01 00:00:00 UTC
MIN = 60_000
H = 60 * MIN
THR = {("2026-10", "BTCUSDT"): Decimal(100), ("2026-10", "ETHUSDT"): Decimal(50)}


def liq(t, side="long", n="60", sym="BTCUSDT"):
    return e1.Liq(symbol=sym, t_ms=t, side=side, notional=Decimal(n))


def test_constants_match_card():
    assert e1.WINDOW_MS == 60 * MIN
    assert e1.THETA == Decimal("0.005")
    assert e1.HOLD_MS == 24 * H
    assert e1.DIRECTION == {"long": 1, "short": -1}


def test_month_of_utc():
    assert e1.month_of(D0) == "2026-10"
    assert e1.month_of(D0 - 1) == "2026-09"


def test_single_event_below_threshold_is_not_cascade():
    assert e1.detect_cascades([liq(D0, n="99.99")], THR) == []


def test_two_events_inside_window_trigger_at_second():
    out = e1.detect_cascades([liq(D0, n="60"), liq(D0 + 59 * MIN, n="40")], THR)
    assert len(out) == 1
    c = out[0]
    assert c.t_ms == D0 + 59 * MIN and c.window_notional == Decimal(100)
    assert c.side == "long" and c.direction == 1  # przeciw zlikwidowanym longom: kupno


def test_window_is_open_on_the_left():
    # zdarzenie dokładnie W wcześniej już wypadło z okna (t ≤ t_e − W)
    assert e1.detect_cascades([liq(D0, n="60"), liq(D0 + H, n="40")], THR) == []


def test_short_cascade_direction_is_sell():
    out = e1.detect_cascades([liq(D0, side="short", n="100")], THR)
    assert out[0].direction == -1 and out[0].side == "short"


def test_entry_is_second_full_minute_and_exit_24h_later():
    t = D0 + 5 * MIN + 59_999
    c = e1.detect_cascades([liq(t, n="100")], THR)[0]
    assert c.entry_ms == D0 + 7 * MIN
    assert c.exit_ms == c.entry_ms + 24 * H
    assert 60_000 < c.entry_ms - c.t_ms <= 120_000


def test_block_24h_for_both_sides_then_free():
    evs = [
        liq(D0, n="100"),
        liq(D0 + 2 * H, side="short", n="100"),  # zablokowane
        liq(D0 + 24 * H - 1, n="100"),  # zablokowane
        liq(D0 + 24 * H, n="100"),  # wolne
    ]
    out = e1.detect_cascades(evs, THR)
    assert [c.t_ms for c in out] == [D0, D0 + 24 * H]


def test_ambiguous_both_sides_skipped_without_block():
    evs = [
        liq(D0, side="short", n="100"),  # zdarzenie short, blokada do D0 + 24 h
        liq(D0 + 24 * H - 30 * MIN, side="long", n="100"),  # w blokadzie
        liq(D0 + 24 * H - 30 * MIN, side="short", n="100"),  # w blokadzie
        liq(D0 + 24 * H + MIN, side="long", n="1"),  # long 101, short 100 → niejednoznaczne
        liq(D0 + 24 * H + 40 * MIN, side="short", n="100"),  # stare wypadły: short 100, long 1
    ]
    out = e1.detect_cascades(evs, THR)
    assert [(c.t_ms, c.side) for c in out] == [(D0, "short"), (D0 + 24 * H + 40 * MIN, "short")]


def test_symbol_outside_universe_or_month_is_ignored():
    evs = [liq(D0, sym="DOGEUSDT", n="1e9"), liq(D0 - 1, n="1e9")]  # spoza listy / wrzesień
    assert e1.detect_cascades(evs, THR) == []


def test_symbols_are_independent():
    evs = [liq(D0, n="100"), liq(D0 + MIN, sym="ETHUSDT", n="50")]
    out = e1.detect_cascades(evs, THR)
    assert [(c.symbol, c.t_ms) for c in out] == [("BTCUSDT", D0), ("ETHUSDT", D0 + MIN)]


def test_input_order_does_not_matter():
    evs = [liq(D0 + 30 * MIN, n="50"), liq(D0, n="50"), liq(D0 + 50 * MIN, sym="ETHUSDT", n="50")]
    assert e1.detect_cascades(evs, THR) == e1.detect_cascades(list(reversed(evs)), THR)


def test_bad_side_rejected():
    import pytest

    with pytest.raises(ValueError):
        e1.detect_cascades([e1.Liq("BTCUSDT", D0, "Buy", Decimal(1))], THR)


def test_load_universe_and_thresholds(tmp_path):
    p = tmp_path / "koszyk.csv"
    p.write_text(
        "miesiac,symbol,pozycja,sredni_obrot_30d,czlonek_top20,funding_pobrany\n"
        "2026-10,BTCUSDT,1,1000000,True,True\n"
        "2026-10,XUSDT,21,5000,False,True\n",
        encoding="utf-8",
    )
    u = e1.load_universe(p)
    assert u == {("2026-10", "BTCUSDT"): Decimal(1000000)}
    assert e1.thresholds(u) == {("2026-10", "BTCUSDT"): Decimal(5000)}


events_st = st.lists(
    st.tuples(
        st.integers(min_value=0, max_value=72 * 60),  # minuta w ciągu 3 dni
        st.sampled_from(["long", "short"]),
        st.integers(min_value=0, max_value=150),
        st.sampled_from(["BTCUSDT", "ETHUSDT"]),
    ),
    max_size=60,
)


def _mk(raw):
    return [liq(D0 + m * MIN, side=s, n=str(n), sym=sym) for m, s, n, sym in raw]


@settings(max_examples=200, deadline=None)
@given(events_st)
def test_property_no_overlap_and_threshold_met(raw):
    out = e1.detect_cascades(_mk(raw), THR)
    by_sym: dict[str, list[e1.Cascade]] = {}
    for c in out:
        assert c.window_notional >= c.threshold
        by_sym.setdefault(c.symbol, []).append(c)
    for cs in by_sym.values():
        for a, b in zip(cs, cs[1:], strict=False):
            assert b.t_ms >= a.t_ms + e1.HOLD_MS  # blokada 24 h → transakcje się nie nakładają
            assert b.entry_ms >= a.exit_ms


def _naive(evs, thr):
    """Niezależna implementacja O(n²) wprost z tekstu karty §4 (bez kolejek i sum bieżących)."""
    out = []
    for sym in sorted({e.symbol for e in evs}):
        seq = [e for e in sorted(evs, key=lambda e: e.t_ms) if e.symbol == sym]
        seq = [e for e in seq if (e1.month_of(e.t_ms), sym) in thr]
        blocked = None
        for i, e in enumerate(seq):
            if blocked is not None and e.t_ms < blocked:
                continue
            lim = thr[(e1.month_of(e.t_ms), sym)]
            seen = seq[: i + 1]
            s = {
                side: sum(
                    (x.notional for x in seen if x.side == side and x.t_ms > e.t_ms - e1.WINDOW_MS),
                    Decimal(0),
                )
                for side in e1.SIDES
            }
            other = "short" if e.side == "long" else "long"
            if s[e.side] >= lim and s[other] < lim:
                out.append((sym, e.t_ms, e.side))
                blocked = e.t_ms + e1.HOLD_MS
    return sorted(out, key=lambda x: (x[1], x[0]))


@settings(max_examples=300, deadline=None)
@given(events_st)
def test_property_matches_naive_reference(raw):
    evs = _mk(raw)
    got = [(c.symbol, c.t_ms, c.side) for c in e1.detect_cascades(evs, THR)]
    assert got == _naive(evs, THR)
