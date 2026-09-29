"""Testy pomiaru wag Hyperliquid (`data/measure_hl_weights.py`, LH0 krok 1A) — bez sieci: strona aktywna,
filtry ruchu ceny F1/F2, kubełki minutowe (duplikaty, spóźnione), okna, rozpoznanie likwidacji i reguła M4,
waga zapytania, odczekanie po 429, ogranicznik wag (właściwość w hypothesis: suma w dowolnym oknie 60 s nigdy
nie przekracza sufitu), przedział Cloppera–Pearsona, podsumowanie na syntetycznych plikach, generowanie zadań
próbki i wykonanie zapytania na fałszywej sesji (stronicowanie, 429).
"""

from __future__ import annotations

import asyncio
import json
import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data import measure_hl_weights as m

A, B, C = "0xaaa", "0xbbb", "0xccc"
M0 = 29_844_500  # minuta od epoki (2026-09-29)


def _t(coin, side, px, t_ms, tid, h, buyer=A, seller=B):
    return {
        "coin": coin,
        "side": side,
        "px": str(px),
        "sz": "0.1",
        "time": t_ms,
        "tid": tid,
        "hash": h,
        "users": [buyer, seller],
    }


# ------------------------------------------------------------------ czyste funkcje
def test_taker_is_aggressor_side():
    assert m.taker_of(_t("BTC", "B", 1, 0, 1, "h")) == A
    assert m.taker_of(_t("BTC", "A", 1, 0, 1, "h")) == B


def test_query_weight_matches_docs():
    assert m.query_weight(0) == 20
    assert m.query_weight(1) == 21
    assert m.query_weight(20) == 21
    assert m.query_weight(21) == 22
    assert m.query_weight(2000) == 120 == m.MAX_PAGE_WEIGHT


def test_backoff_grows_and_is_capped():
    vals = [m.backoff_s(i) for i in range(10)]
    assert vals[0] == 10 and vals == sorted(vals) and max(vals) == 300


def test_f2_direction():
    assert m.f2_move("B", 101, 100) and not m.f2_move("B", 100, 100)
    assert m.f2_move("A", 99, 100) and not m.f2_move("A", 101, 100)
    assert not m.f2_move("B", 101, None)


def test_aggregator_f1_f2_dups_and_late():
    ag = m.MinuteAggregator()
    t0 = M0 * m.MIN_MS
    ag.add(_t("BTC", "B", 100, t0 + 1, 1, "h1"))  # pierwsze zlecenie: brak poprzedniej ceny
    ag.add(_t("BTC", "B", 101, t0 + 1, 2, "h1"))  # to samo zlecenie, 2. poziom -> F1
    ag.add(_t("BTC", "B", 101, t0 + 1, 2, "h1"))  # duplikat tid
    ag.add(
        _t("BTC", "A", 100.5, t0 + 5, 3, "h2", buyer=C, seller=C)
    )  # taker C sprzedaje poniżej 101 -> F2
    ag.add(_t("BTC", "B", 100.5, t0 + 6, 4, "h3", buyer=B, seller=C))  # ta sama cena -> bez ruchu
    ag.add(_t("DOGE", "B", 1, t0 + 6, 5, "h4"))  # poza monetami — ignorowane
    rec = ag.finalize(M0)
    tk = rec["BTC"]["takers"]
    assert rec["BTC"]["trades"] == 4
    assert tk[A] == [1, 1, 1] and tk[C] == [1, 0, 1] and tk[B] == [1, 0, 0]
    assert ag.dups == 1
    ag.add(_t("BTC", "B", 100, t0 + 10, 9, "h9"))  # minuta już zamknięta
    assert ag.late == 1


@given(st.lists(st.integers(1, 5), min_size=1, max_size=8))
def test_f1_iff_two_distinct_prices(pxs):
    ag = m.MinuteAggregator()
    for i, p in enumerate(pxs):
        ag.add(_t("ETH", "B", p, M0 * m.MIN_MS + i, i, "h"))
    takers = ag.finalize(M0)["ETH"]["takers"]
    assert takers[A][1] == int(len(set(pxs)) >= 2)
    assert takers[A][2] >= takers[A][1]  # F2 zawiera F1


def test_finalize_drops_older_buckets():
    ag = m.MinuteAggregator()
    ag.add(_t("BTC", "B", 1, (M0 - 5) * m.MIN_MS, 1, "h"))
    ag.finalize(M0)
    assert not ag.buckets


def test_window_takers_and_passes():
    mins = {
        M0: {c: {"takers": {}} for c in m.COINS},
        M0 + 1: {c: {"takers": {}} for c in m.COINS},
    }
    mins[M0]["BTC"]["takers"] = {A: [2, 1, 1]}
    mins[M0 + 1]["BTC"]["takers"] = {A: [1, 0, 1]}
    mins[M0 + 1]["SOL"]["takers"] = {B: [1, 0, 0]}
    wt = m.window_takers(mins, m.COINS, M0, 2)
    assert wt[A]["BTC"] == [3, 1, 2] and wt[B]["SOL"] == [1, 0, 0]
    assert m.passes(wt[A], ("BTC",), "F1") and not m.passes(wt[B], m.COINS, "F2")
    assert not m.passes(wt[B], ("BTC",), "all") and m.passes(wt[B], m.COINS, "all")


def _fill(coin, t, oid, start="1.0", liq=None, dirn="Close Long", h="h", tid=None):
    f = {
        "coin": coin,
        "time": t,
        "oid": oid,
        "startPosition": start,
        "dir": dirn,
        "hash": h,
        "tid": tid if tid is not None else oid * 10 + t,
    }
    if liq is not None:
        f["liquidation"] = liq
    return f


def test_analyze_fills_liquidation_rules_and_state():
    fills = [
        _fill("BTC", 5, 1, liq={"liquidatedUser": A, "method": "market"}, h="hx"),
        _fill("BTC", 6, 1, liq={"liquidatedUser": A, "method": "market"}, h="hx"),
        _fill("ETH", 7, 2, liq={"liquidatedUser": B, "method": "market"}),  # A kontrahentem
        _fill("SOL", 8, 3, start="0.0"),
        _fill("DOGE", 9, 4, liq={"liquidatedUser": A, "method": "market"}),  # poza zestawem
    ]
    an = m.analyze_fills(fills, A)
    assert len(an["liqs"]) == 1
    lq = an["liqs"][0]
    assert (lq["coin"], lq["oid"], lq["T"], lq["hash"], lq["fills"]) == ("BTC", 1, 5, "hx", 2)
    assert an["coins"]["SOL"] == {"start_flat": True, "oids": 1}
    assert an["coins"]["BTC"]["start_flat"] is False
    assert m.skippable(an["coins"], ("SOL",)) and not m.skippable(an["coins"], m.COINS)


def test_liquidation_without_user_field_uses_step0_rule():
    assert m.is_liquidation_of(_fill("BTC", 1, 1, liq={"method": "market"}), A)
    assert m.is_liquidation_of(
        _fill("BTC", 1, 1, liq={"liquidatedUser": B}, dirn="Liquidated Cross Long"), A
    )
    assert not m.is_liquidation_of(_fill("BTC", 1, 1), A)


@given(st.booleans(), st.integers(0, 3))
def test_skippable_never_true_for_real_liquidation(flat_other, extra_oids):
    # likwidacja zamyka ISTNIEJĄCĄ pozycję: pierwsze wypełnienie w monecie likwidacji ma startPosition != 0
    # albo w monecie są ≥ 2 zlecenia (otwarcie + likwidacja) — reguła M4 nie może takiego adresu pominąć
    fills = [_fill("BTC", 1, 1, start="0.0"), _fill("BTC", 2, 2, liq={"liquidatedUser": A})]
    fills += [
        _fill("ETH", 3 + i, 10 + i, start="0.0" if flat_other else "2") for i in range(extra_oids)
    ]
    an = m.analyze_fills(fills, A)
    assert an["liqs"] and not m.skippable(an["coins"], m.COINS)


# ------------------------------------------------------------------ ogranicznik wag
def test_limiter_waits_when_full():
    lim = m.WeightLimiter(target=100, hard_cap=900)
    lim.record(0.0, 90)
    assert lim.wait_s(1.0) == pytest.approx(59.0)
    assert lim.wait_s(60.5) == 0.0
    assert lim.used(60.5) == 0


def test_limiter_rejects_target_too_close_to_cap():
    with pytest.raises(ValueError):
        m.WeightLimiter(target=850, hard_cap=900)


@settings(max_examples=60, deadline=None)
@given(st.lists(st.tuples(st.floats(0, 5), st.integers(0, 2000)), min_size=1, max_size=120))
def test_limiter_property_never_exceeds_hard_cap(steps):
    lim = m.WeightLimiter()
    now, sent = 0.0, []
    for gap, items in steps:
        now += gap
        for _ in range(10):  # jak w `run_job`: czekaj, aż ogranicznik pozwoli (zaokrąglenia float)
            w = lim.wait_s(now)
            if w <= 0:
                break
            now += w
        assert lim.wait_s(now) == 0.0
        wt = m.query_weight(items)
        lim.record(now, wt)
        sent.append((now, wt))
    for t, _ in sent:  # każde okno 60 s kończące się na wysłaniu
        assert sum(w for s, w in sent if t - 60 < s <= t) <= m.HARD_CAP


# ------------------------------------------------------------------ statystyka
def test_clopper_pearson_known_values():
    assert m.clopper_pearson_upper(0, 59) <= 0.0610  # 1 − 0,025^(1/59) ≈ 0,0605
    assert m.clopper_pearson_upper(0, 59) == pytest.approx(1 - 0.025 ** (1 / 59), abs=1e-6)
    assert m.clopper_pearson_upper(0, 0) == 1.0 and m.clopper_pearson_upper(5, 5) == 1.0


@given(st.integers(1, 200), st.data())
def test_clopper_pearson_bounds(n, data):
    x = data.draw(st.integers(0, n))
    up = m.clopper_pearson_upper(x, n)
    assert x / n <= up <= 1.0
    if x < n:
        assert m.clopper_pearson_upper(x + 1, n) >= up - 1e-9


def test_stats_and_sampling():
    s = m.stats([1, 2, 3, 4, 100])
    assert (s["mean"], s["median"], s["p95"], s["max"]) == (22, 3, 100, 100)
    assert m.stats([])["mean"] is None
    pool = [f"0x{i}" for i in range(50)]
    a = m.sample_addresses(pool, 10, seed=7)
    assert a == m.sample_addresses(reversed(pool), 10, seed=7) and len(set(a)) == 10
    assert m.sample_addresses(pool[:3], 10, seed=7) == sorted(pool[:3])


# ------------------------------------------------------------------ podsumowanie
def test_summarize_synthetic():
    mins = []
    for i in range(60):
        takers = {"BTC": {A: [1, 1, 1], B: [1, 0, 0]}, "ETH": {C: [1, 0, 1]}, "SOL": {}}
        mins.append(
            {
                "m": M0 + i,
                "ok": True,
                "coins": {c: {"trades": 3, "takers": takers[c]} for c in m.COINS},
            }
        )
    q = []
    for i in range(60):
        q.append(
            {
                "kind": "probka",
                "N": 1,
                "w_start": M0 + i,
                "addr": B,
                "taker": {"BTC": [1, 0, 0]},
                "recv": (M0 + i + 1) * 60.0,
                "status": "ok",
                "pages": 1,
                "pages_sent": [((M0 + i + 1) * 60.0, 30)],
                "weight": 30,
                "coins": {"BTC": {"start_flat": False, "oids": 2}},
                "liqs": [
                    {"coin": "BTC", "T": (M0 + i) * m.MIN_MS, "order_f1": False, "order_f2": False}
                ],
                "n429": 0,
            }
        )
    out = m.summarize(mins, q)
    # S1: 2 adresy/min × w̄ 30 = 60 wagi/min
    line = [ln for ln in out.splitlines() if ln.startswith("S1") and "M1 pełny" in ln][0]
    assert " 60 " in line and "mieści się" in line
    assert "S1 F1: likwidacji=60 zgubionych=60" in out
    assert "odpowiedzi 429 łącznie: 0" in out


# ------------------------------------------------------------------ pętla bez sieci
def _meas(tmp_path, quota=None):
    return m.Measurement(tmp_path, 1.0, quota or {1: 2, 5: 3, 15: 1, 60: 1}, 700)


def test_close_minutes_and_jobs(tmp_path):
    ms = _meas(tmp_path)
    ms.up_since = (M0 - 1) * 60.0
    ms.down_since = None
    ms.agg.finalized_upto = M0 - 1
    for i in range(5):
        for j, u in enumerate((A, B, C)):
            ms.agg.add(
                _t("BTC", "B", 100 + j, (M0 + i) * m.MIN_MS + j, i * 10 + j, f"h{i}{j}", buyer=u)
            )
    ms.close_minutes((M0 + 5) * 60.0 + m.GRACE_S + 0.1)
    recs = m.load_jsonl(tmp_path / "minuty.jsonl")
    assert [r["m"] for r in recs] == list(range(M0, M0 + 5)) and all(r["ok"] for r in recs)
    kinds = [(j["kind"], j["N"]) for _, _, j in ms.jobs]
    assert kinds.count(("probka", 1)) == 5 * 2  # kwota 2 na każde okno 1-min
    assert kinds.count(("probka", 5)) == (3 if M0 % 5 == 0 else 0) or M0 % 5 != 0


def test_minute_not_ok_after_disconnect(tmp_path):
    ms = _meas(tmp_path)
    ms.up_since = M0 * 60.0 + 10
    ms.down_since = None
    assert not ms.minute_ok(M0) and ms.minute_ok(M0 + 1)
    ms.down_since = (M0 + 1) * 60.0 + 30
    assert not ms.minute_ok(M0 + 1)


class _Resp:
    def __init__(self, status, payload):
        self.status = status
        body = json.dumps(payload).encode()
        self.content = self
        self._body = body

    async def iter_chunked(self, n):  # noqa: D401 — async generator
        for i in range(0, len(self._body), n):
            yield self._body[i : i + n]

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.bodies = []

    def post(self, url, json=None, timeout=None):
        assert url == m.INFO_URL
        self.bodies.append(json)
        return _Resp(*self.responses.pop(0))


def test_run_job_paginates_and_handles_429(tmp_path, monkeypatch):
    async def fast_sleep(_):
        return None

    monkeypatch.setattr(m.asyncio, "sleep", fast_sleep)
    ms = _meas(tmp_path)
    t0 = M0 * m.MIN_MS
    page1 = [_fill("BTC", t0 + i, 100 + i, tid=i) for i in range(m.FILLS_PAGE)]
    liq = _fill("BTC", t0 + 50_000, 7, liq={"liquidatedUser": A, "method": "market"}, h="hl")
    ms.minutes[M0] = {
        "BTC": {"orders": {"hl": (A, False, True)}},
        "ETH": {"orders": {}},
        "SOL": {"orders": {}},
    }
    sess = _Session([(429, {}), (200, page1), (200, [liq])])
    job = {
        "kind": "probka",
        "N": 1,
        "start": M0,
        "addr": A,
        "taker": {"BTC": [1, 0, 1]},
        "enq": 0,
        "not_before": 0,
    }
    asyncio.run(ms.run_job(sess, job))
    rec = m.load_jsonl(tmp_path / "zapytania.jsonl")[0]
    assert rec["n429"] == 1 and rec["pages"] == 2 and rec["status"] == "ok"
    assert rec["weight"] == m.query_weight(m.FILLS_PAGE) + m.query_weight(1)
    assert sess.bodies[2]["startTime"] == t0 + m.FILLS_PAGE - 1 + 1
    assert sess.bodies[2]["endTime"] == (M0 + 1) * m.MIN_MS - 1
    (lq,) = rec["liqs"]
    assert (lq["order_f1"], lq["order_f2"]) == (False, True)
    assert math.isclose(sum(w for _, w in rec["pages_sent"]), rec["weight"])
