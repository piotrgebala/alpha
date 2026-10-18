"""
measure_hl_weights.py — LH0 krok 1A (zadanie 004): pomiar kosztu wag Info API Hyperliquid dla kolektora
likwidacji w trybie ograniczonym (kilka głównych monet). NIE jest kolektorem i NIE zestawia likwidacji z cenami
(zero odczytu E1). Pre-rejestracja: `runs/2026-09-29_lh0-kolektor-hyperliquid/README.md`, „Krok 1”.

Co robi (plik jest samodzielny: tylko biblioteka standardowa + aiohttp, żeby dało się go uruchomić z kopii
poza repo):
1. słucha darmowego WebSocket `trades` dla BTC, ETH, SOL i co minutę zapisuje (`minuty.jsonl`) — per moneta —
   adresy stron aktywnych (taker) z liczbą zleceń aktywnych i liczbą zleceń z ruchem ceny (filtry F1, F2);
2. z tych zliczeń koszt sposobów M1–M4 liczy się PÓŹNIEJ (`--podsumuj`), bez żadnych zapytań;
3. na LOSOWEJ PRÓBCE stron aktywnych każdego okna (1, 5, 15, 60 min) wykonuje prawdziwe zapytania
   `userFillsByTime` (`zapytania.jsonl`): zmierzona waga, stronicowanie, likwidacje i opóźnienie wykrycia;
   co 60 min jedno okno 1-min odpytane w całości (porównanie z pełnym odpytaniem);
4. pilnuje budżetu wag: okno przesuwne 60 s, cel `--cel` (domyślnie 700), sufit twardy 900 (przed każdym
   zapytaniem suma z ostatnich 60 s + szacunek ≤ cel; jedna strona waży najwyżej 20 + 100, więc suma nie przekroczy
   cel − 21 + 120 ≤ 900); przy 429 rosnące odczekanie 10 s → 300 s, nigdy obchodzenie.

Fakty z dokumentacji Hyperliquid (strony pobrane 2026-09-29, krok 0 tej rundy):
- REST 1 200 wagi/min na IP; `userFillsByTime` waga 20 + 1 za każde rozpoczęte 20 zwróconych wypełnień;
  najwyżej 2 000 wypełnień na odpowiedź (wyniki rosnąco po czasie — sprawdzone na żywo 2026-09-29, stąd
  stronicowanie `startTime = max(time) + 1`);
- `WsTrade` = `coin, side, px, sz, hash, time, tid, users: [kupujący, sprzedający]`; strona aktywna = `users[0]` przy
  `side "B"`, `users[1]` przy `"A"` (krok 0: 10 680 / 10 680 zgodnych z polem `crossed`);
- likwidacja = wypełnienie z polem `liquidation` (`liquidatedUser`, `markPx`, `method`); ta sama reguła co w kroku 0.

Zapis (katalog `--dir`, domyślnie `$HOME/likwidacje_hl/pomiar_krok1`): `minuty.jsonl`, `zapytania.jsonl`,
`status.json`, `pomiar.log`.

    python measure_hl_weights.py --godziny 26                 # pomiar (w tle, setsid nohup)
    python measure_hl_weights.py --status
    python measure_hl_weights.py --podsumuj > raw_output.txt  # tabele kroku A
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import heapq
import json
import math
import os
import random
import sys
import time
from pathlib import Path

WS_URL = "wss://api.hyperliquid.xyz/ws"
INFO_URL = "https://api.hyperliquid.xyz/info"
DEFAULT_DIR = Path.home() / "likwidacje_hl" / "pomiar_krok1"
COINS = ("BTC", "ETH", "SOL")
SETS = {"S1": ("BTC",), "S2": ("BTC", "ETH"), "S3": ("BTC", "ETH", "SOL")}
WINDOWS = (1, 5, 15, 60)  # długości okien (min); 1 = M1/M2, 5/15/60 = M3
DEFAULT_QUOTA = {1: 10, 5: 30, 15: 45, 60: 90}  # adresów w próbce na okno
FULL_CHECK_MINUTE = (
    30  # co godzinę: okno 1-min zaczynające się w tej minucie godziny — odpytane w całości
)
FILLS_PAGE = 2000
MAX_PAGES = 5
BASE_WEIGHT = 20
EST_WEIGHT = 21  # szacunek przed wysłaniem (krok 0: średnio 21,8)
TARGET_WEIGHT = 700
HARD_CAP = 900
MAX_PAGE_WEIGHT = BASE_WEIGHT + FILLS_PAGE // 20
GRACE_S = 15.0  # minuta jest zamykana 15 s po końcu (spóźnione transakcje)
PING_EVERY_S = 30.0
SILENCE_S = 120.0  # brak transakcji BTC przez 2 min = ponowne połączenie
MAX_REST_BYTES = 50 * 2**20
KEEP_MIN = 200  # ile minut zliczeń trzymać w pamięci
MIN_MS = 60_000


# ------------------------------------------------------------------ czyste funkcje
def taker_of(trade: dict) -> str:
    """Adres strony aktywnej transakcji (`side` = strona agresora)."""
    users = trade["users"]
    return users[0] if trade["side"] == "B" else users[1]


def query_weight(n_items: int) -> int:
    """Waga jednej strony `userFillsByTime`: 20 + 1 za każde rozpoczęte 20 zwróconych pozycji."""
    return BASE_WEIGHT + math.ceil(n_items / 20)


def backoff_s(attempt: int) -> float:
    """Odczekanie po 429: 10 s, 20 s, 40 s … najwyżej 300 s."""
    return float(min(300, 10 * 2 ** max(0, attempt)))


def f2_move(side: str, first_px: float, last_px: float | None) -> bool:
    """Ruch ceny wg F2 (bez F1): pierwsza cena zlecenia dalej w kierunku agresora niż poprzednia transakcja."""
    if last_px is None:
        return False
    return first_px > last_px if side == "B" else first_px < last_px


class MinuteAggregator:
    """Zbiera transakcje w kubełki minutowe per moneta; zlecenie aktywne = (moneta, taker, hash)."""

    def __init__(self, coins=COINS):
        self.coins = tuple(coins)
        self.last_px: dict[str, float] = {}
        self.buckets: dict[int, dict] = (
            {}
        )  # minuta -> moneta -> {"trades": n, "orders": {(taker, hash): rec}}
        self.seen_tids: dict[int, set] = collections.defaultdict(set)  # minuta -> tid
        self.finalized_upto = -1  # ostatnia zamknięta minuta
        self.late = 0
        self.dups = 0

    def add(self, trade: dict) -> None:
        coin = trade["coin"]
        if coin not in self.coins:
            return
        m = int(trade["time"]) // MIN_MS
        if m <= self.finalized_upto:
            self.late += 1
            return
        tid = trade["tid"]
        if tid in self.seen_tids[m]:
            self.dups += 1
            return
        self.seen_tids[m].add(tid)
        px = float(trade["px"])
        b = self.buckets.setdefault(m, {c: {"trades": 0, "orders": {}} for c in self.coins})[coin]
        b["trades"] += 1
        key = (taker_of(trade), trade["hash"])
        rec = b["orders"].get(key)
        if rec is None:
            rec = {"pxs": set(), "f2": f2_move(trade["side"], px, self.last_px.get(coin))}
            b["orders"][key] = rec
        rec["pxs"].add(px)
        self.last_px[coin] = px

    def finalize(self, m: int) -> dict:
        """Zamyka minutę m: {moneta: {"trades": n, "takers": {adres: [zlecenia, F1, F2]}, "orders": {...}}}."""
        raw = self.buckets.pop(m, {c: {"trades": 0, "orders": {}} for c in self.coins})
        self.seen_tids.pop(m, None)
        for old in [k for k in self.buckets if k < m]:  # np. migawka sprzed startu
            del self.buckets[old]
            self.seen_tids.pop(old, None)
        self.finalized_upto = max(self.finalized_upto, m)
        out = {}
        for coin, b in raw.items():
            takers: dict[str, list[int]] = {}
            orders = {}
            for (taker, h), rec in b["orders"].items():
                f1 = len(rec["pxs"]) >= 2
                f2 = f1 or rec["f2"]
                t = takers.setdefault(taker, [0, 0, 0])
                t[0] += 1
                t[1] += int(f1)
                t[2] += int(f2)
                orders[h] = (taker, f1, f2)
            out[coin] = {"trades": b["trades"], "takers": takers, "orders": orders}
        return out


def window_takers(minutes: dict, coins, start: int, n: int) -> dict[str, dict[str, list[int]]]:
    """Adresy stron aktywnych w oknie [start, start+n) minut: adres -> {moneta: [zlecenia, F1, F2]}."""
    res: dict[str, dict[str, list[int]]] = {}
    for m in range(start, start + n):
        rec = minutes.get(m)
        if rec is None:
            continue
        for coin in coins:
            for addr, v in rec[coin]["takers"].items():
                acc = res.setdefault(addr, {}).setdefault(coin, [0, 0, 0])
                for i in range(3):
                    acc[i] += v[i]
    return res


def passes(summary: dict[str, list[int]], coins, filt: str) -> bool:
    """Czy adres przechodzi filtr w zestawie monet: 'all' (M1/M3), 'F1', 'F2' (M2)."""
    idx = {"all": 0, "F1": 1, "F2": 2}[filt]
    return any(summary.get(c, [0, 0, 0])[idx] > 0 for c in coins)


def is_liquidation_of(fill: dict, user: str) -> bool:
    """Wypełnienie, w którym zlikwidowanym jest ten adres (reguła z kroku 0)."""
    lq = fill.get("liquidation")
    if not lq:
        return False
    return lq.get("liquidatedUser") in (None, user) or str(fill.get("dir", "")).startswith(
        "Liquidated"
    )


def analyze_fills(fills: list[dict], user: str, coins=COINS) -> dict:
    """Likwidacje (zlecenia) i stan na początku okna per moneta z odpowiedzi `userFillsByTime`."""
    liqs: dict[tuple, dict] = {}
    per_coin: dict[str, dict] = {}
    for f in sorted(fills, key=lambda x: (x.get("time", 0), x.get("tid", 0))):
        coin = f.get("coin")
        if coin not in coins:
            continue
        pc = per_coin.setdefault(coin, {"start": f.get("startPosition"), "oids": set()})
        pc["oids"].add(f.get("oid"))
        if is_liquidation_of(f, user):
            key = (coin, f.get("oid"))
            if key not in liqs:
                liqs[key] = {
                    "coin": coin,
                    "oid": f.get("oid"),
                    "T": f.get("time"),
                    "method": f["liquidation"].get("method"),
                    "hash": f.get("hash"),
                    "fills": 0,
                }
            liqs[key]["fills"] += 1
    coins_state = {
        c: {"start_flat": _is_zero(v["start"]), "oids": len(v["oids"])} for c, v in per_coin.items()
    }
    return {"liqs": list(liqs.values()), "coins": coins_state}


def _is_zero(x) -> bool:
    try:
        return float(x) == 0.0
    except (TypeError, ValueError):
        return False


def skippable(coins_state: dict, coins) -> bool:
    """M4 (górna granica): brak pozycji na starcie okna we wszystkich monetach zestawu z wypełnieniami i łącznie
    najwyżej jedno zlecenie w tych monetach — likwidacja niemożliwa."""
    st = [coins_state[c] for c in coins if c in coins_state]
    if not st:
        return True
    return all(s["start_flat"] for s in st) and sum(s["oids"] for s in st) <= 1


class WeightLimiter:
    """Okno przesuwne 60 s wag wysłanych zapytań."""

    def __init__(self, target: int = TARGET_WEIGHT, hard_cap: int = HARD_CAP):
        if target + MAX_PAGE_WEIGHT - EST_WEIGHT > hard_cap:
            raise ValueError("cel za blisko sufitu twardego")
        self.target = target
        self.hard_cap = hard_cap
        self.events: collections.deque = collections.deque()

    def used(self, now: float) -> int:
        while self.events and self.events[0][0] <= now - 60.0:
            self.events.popleft()
        return sum(w for _, w in self.events)

    def wait_s(self, now: float, est: int = EST_WEIGHT) -> float:
        """0, jeśli można wysłać teraz; inaczej ile czekać, aż zwolni się miejsce."""
        used = self.used(now)
        if used + est <= self.target:
            return 0.0
        need = used + est - self.target
        freed = 0
        for t, w in self.events:
            freed += w
            if freed >= need:
                return max(0.01, t + 60.0 - now)
        return 60.0

    def record(self, now: float, weight: int) -> None:
        self.events.append((now, weight))


def sample_addresses(addrs, k: int, seed: int) -> list[str]:
    """Losowa próbka k adresów (powtarzalna: ziarno = początek okna)."""
    pool = sorted(addrs)
    if k >= len(pool):
        return pool
    return random.Random(seed).sample(pool, k)


def clopper_pearson_upper(x: int, n: int, alpha: float = 0.05) -> float:
    """Górna granica dwustronnego przedziału Cloppera–Pearsona (1 − alpha) dla x sukcesów na n."""
    if n <= 0:
        return 1.0
    if x >= n:
        return 1.0

    def cdf(p: float) -> float:  # P(X <= x)
        if p <= 0:
            return 1.0
        if p >= 1:
            return 0.0
        lp, lq = math.log(p), math.log1p(-p)
        s = 0.0
        for i in range(x + 1):
            s += math.exp(
                math.lgamma(n + 1)
                - math.lgamma(i + 1)
                - math.lgamma(n - i + 1)
                + i * lp
                + (n - i) * lq
            )
        return s

    lo, hi = x / n, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha / 2:
            lo = mid
        else:
            hi = mid
    return hi


def stats(values) -> dict:
    """Średnia, mediana, p95 (najbliższy rang), maks."""
    v = sorted(values)
    if not v:
        return {"n": 0, "mean": None, "median": None, "p95": None, "max": None}
    n = len(v)
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    p95 = v[min(n - 1, math.ceil(0.95 * n) - 1)]
    return {"n": n, "mean": sum(v) / n, "median": med, "p95": p95, "max": v[-1]}


async def read_limited(chunks, limit: int = MAX_REST_BYTES) -> bytes:
    """Czyta całą odpowiedź kawałkami; więcej niż `limit` bajtów = błąd."""
    buf = bytearray()
    async for ch in chunks:
        buf.extend(ch)
        if len(buf) > limit:
            raise RuntimeError("odpowiedź za duża")
    return bytes(buf)


# ------------------------------------------------------------------ podsumowanie (bez sieci)
def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _fmt(x, nd=0) -> str:
    if x is None:
        return "—"
    return f"{x:,.{nd}f}".replace(",", " ")


def summarize(minute_recs: list[dict], query_recs: list[dict]) -> str:
    lines: list[str] = []
    P = lines.append
    minutes = {r["m"]: r["coins"] for r in minute_recs if r.get("ok")}
    all_m = [r["m"] for r in minute_recs]
    P(f"minut zapisanych: {len(all_m)}, pełnych (połączenie bez przerwy): {len(minutes)}")
    if all_m:
        P(
            f"zakres (UTC, minuty od epoki): {min(all_m)} .. {max(all_m)} = "
            f"{time.strftime('%Y-%m-%d %H:%M', time.gmtime(min(all_m) * 60))} .. "
            f"{time.strftime('%Y-%m-%d %H:%M', time.gmtime(max(all_m) * 60))}"
        )
    probe = [q for q in query_recs if q.get("kind") == "probka" and q.get("status") == "ok"]
    full = [q for q in query_recs if q.get("kind") == "pelny" and q.get("status") == "ok"]
    P(
        f"zapytań: próbka ok={len(probe)}, pełne okna ok={len(full)}, "
        f"statusy={dict(collections.Counter(q.get('status') for q in query_recs))}"
    )
    n429 = sum(q.get("n429", 0) for q in query_recs)
    P(f"odpowiedzi 429 łącznie: {n429}")

    # waga samego pomiaru per minuta
    per_min = collections.Counter()
    for q in query_recs:
        for t, w in q.get("pages_sent", []):
            per_min[int(t // 60)] += w
    if per_min:
        span = range(min(per_min), max(per_min) + 1)
        st_self = stats([per_min.get(m, 0) for m in span])
        P(
            "waga samego pomiaru [wagi/min]: średnia {} mediana {} p95 {} maks {}".format(
                _fmt(st_self["mean"]),
                _fmt(st_self["median"]),
                _fmt(st_self["p95"]),
                _fmt(st_self["max"]),
            )
        )
    P("")

    # średnia waga zapytania z próbki per okno N i zestaw
    def wbar(n: int, coins, filt: str = "all"):
        ws = [
            q["weight"]
            for q in probe
            if q["N"] == n and passes(q["taker"], coins, filt) and passes(q["taker"], coins, "all")
        ]
        return (sum(ws) / len(ws), len(ws)) if ws else (None, 0)

    P("ŚREDNIA WAGA ZAPYTANIA z próbki (w̄, liczba zapytań) per okno N i zestaw:")
    for n in WINDOWS:
        P(
            f"  N={n:>2}: "
            + "  ".join(
                f"{s}: {_fmt(wbar(n, c)[0], 1)} (n={wbar(n, c)[1]})" for s, c in SETS.items()
            )
        )
    P("")

    P(
        "KOSZT SPOSOBÓW [wagi/min] = unikalne adresy × w̄ (/N dla M3); w nawiasie dolna granica 20/zapytanie. "
        "Próg: średnia ≤ 600 ORAZ p95 ≤ 1 200."
    )
    P(
        f"{'zestaw':<6} {'sposób':<14} {'okien':>6} {'adr.śr':>7} {'w̄':>6} {'średnia':>9} {'mediana':>9} "
        f"{'p95':>9} {'maks':>9} {'(dolna śr.)':>11} {'M4 oszcz.':>9}  werdykt"
    )
    for sname, coins in SETS.items():
        for label, n, filt in (
            ("M1 pełny/1min", 1, "all"),
            ("M2 F1/1min", 1, "F1"),
            ("M2 F2/1min", 1, "F2"),
            ("M3 N=5", 5, "all"),
            ("M3 N=15", 15, "all"),
            ("M3 N=60", 60, "all"),
        ):
            counts = []
            for start in sorted(minutes):
                if start % n:
                    continue
                if any((start + i) not in minutes for i in range(n)):
                    continue
                wt = window_takers(minutes, coins, start, n)
                counts.append(sum(1 for s in wt.values() if passes(s, coins, filt)))
            wb, _ = wbar(n, coins, filt)
            if wb is None:
                wb, _ = wbar(n, coins)
            costs = [c * wb / n for c in counts] if wb else []
            st_c = stats(costs)
            lower = stats([c * BASE_WEIGHT / n for c in counts])
            sq = [q for q in probe if q["N"] == n and passes(q["taker"], coins, filt)]
            skip = sum(1 for q in sq if skippable(q["coins"], coins)) / len(sq) if sq else None
            ok = (
                st_c["mean"] is not None
                and st_c["mean"] <= 600
                and st_c["p95"] is not None
                and st_c["p95"] <= 1200
            )
            P(
                f"{sname:<6} {label:<14} {len(counts):>6} "
                f"{_fmt(sum(counts) / len(counts) if counts else None, 1):>7} {_fmt(wb, 1):>6} "
                f"{_fmt(st_c['mean']):>9} {_fmt(st_c['median']):>9} {_fmt(st_c['p95']):>9} "
                f"{_fmt(st_c['max']):>9} {_fmt(lower['mean']):>11} "
                f"{(_fmt(100 * skip, 1) + ' %') if skip is not None else '—':>9}  "
                f"{'mieści się' if ok else 'NIE'}"
            )
    P(
        "  (M4 oszcz. = górna granica udziału zapytań zbędnych przy pełnej wiedzy o pozycji; koszt M4 = koszt × (1 − oszcz.))"
    )
    P("")

    # gubienie likwidacji przez filtry
    P(
        "CZY FILTR GUBI LIKWIDACJE (próbka losowa; jednostka = zlecenie likwidacyjne; próg: górna granica CP95 ≤ 5 %):"
    )
    for sname, coins in SETS.items():
        liqs = [(q, lq) for q in probe for lq in q.get("liqs", []) if lq["coin"] in coins]
        for filt in ("F1", "F2"):
            lost = sum(1 for q, _ in liqs if not passes(q["taker"], coins, filt))
            n = len(liqs)
            up = clopper_pearson_upper(lost, n)
            P(
                f"  {sname} {filt}: likwidacji={n} zgubionych={lost} "
                f"udział={_fmt(100 * lost / n if n else None, 1)} % górna CP95={_fmt(100 * up, 1)} % → "
                f"{'nie gubi' if n and up <= 0.05 else 'gubi / nierozstrzygnięte (próbka)'}"
            )
        order_lvl = [lq for _, lq in liqs if lq.get("order_f1") is not None]
        P(
            f"  {sname} poziom zlecenia (samo zlecenie likwidacyjne): z F1={sum(1 for x in order_lvl if x['order_f1'])}"
            f" z F2={sum(1 for x in order_lvl if x['order_f2'])} z {len(order_lvl)} dopasowanych do `trades`"
        )
    P("")
    P("PEŁNE OKNA 1-min (wszystkie strony aktywne S3 odpytane):")
    by_win = collections.defaultdict(list)
    for q in full:
        by_win[q["w_start"]].append(q)
    tot = collections.Counter()
    for _w, qs in sorted(by_win.items()):
        lq = [(q, x) for q in qs for x in q.get("liqs", [])]
        tot["okna"] += 1
        tot["adresy"] += len(qs)
        tot["waga"] += sum(q["weight"] for q in qs)
        tot["likw"] += len(lq)
        tot["F1"] += sum(1 for q, _ in lq if passes(q["taker"], COINS, "F1"))
        tot["F2"] += sum(1 for q, _ in lq if passes(q["taker"], COINS, "F2"))
    P(
        f"  okien={tot['okna']} adresów={tot['adresy']} waga={tot['waga']} likwidacji={tot['likw']} "
        f"zachowanych przez F1={tot['F1']} F2={tot['F2']}"
    )
    P("")
    P("OPÓŹNIENIE WYKRYCIA [s] = odbiór odpowiedzi − T wypełnienia (próbka), per N:")
    for n in WINDOWS:
        d = [(q["recv"] - lq["T"] / 1000) for q in probe if q["N"] == n for lq in q.get("liqs", [])]
        s = stats(d)
        P(
            f"  N={n:>2}: likwidacji={s['n']} mediana={_fmt(s['median'])} p95={_fmt(s['p95'])} maks={_fmt(s['max'])}"
        )
    P("")
    pag = [q for q in probe + full if q.get("pages", 1) > 1]
    trunc = [q for q in probe + full if q.get("truncated")]
    P(
        f"STRONICOWANIE: zapytań z > 1 stroną={len(pag)} (per N: "
        f"{dict(collections.Counter(q['N'] for q in pag))}), uciętych na {MAX_PAGES} stronach={len(trunc)}"
    )
    methods = collections.Counter(
        lq.get("method") for q in probe + full for lq in q.get("liqs", [])
    )
    P(f"metody likwidacji w próbce: {dict(methods)}")
    return "\n".join(lines)


# ------------------------------------------------------------------ sieć i pętla pomiaru
class Measurement:
    def __init__(self, root: Path, hours: float, quota: dict, target: int, seed_salt: int = 0):
        self.root = root
        self.hours = hours
        self.quota = quota
        self.agg = MinuteAggregator()
        self.limiter = WeightLimiter(target=target)
        self.minutes: dict[int, dict] = {}  # zamknięte minuty (ok) z mapą zleceń
        self.jobs: list = []  # kopiec (not_before, seq, job)
        self.seq = 0
        self.up_since: float | None = None
        self.down_since: float | None = time.time()
        self.last_trade = time.time()
        self.c = collections.Counter()
        self.t_start = time.time()
        self.seed_salt = seed_salt

    # --- pliki
    def _append(self, name: str, rec: dict) -> None:
        with open(self.root / name, "a") as f:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")

    def log(self, msg: str) -> None:
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
        with open(self.root / "pomiar.log", "a") as f:
            f.write(line + "\n")

    def write_status(self) -> None:
        now = time.time()
        st = {
            "czas": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "pid": os.getpid(),
            "start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.t_start)),
            "koniec_plan": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.t_start + self.hours * 3600)
            ),
            "waga_ostatnie_60s": self.limiter.used(now),
            "polaczony": self.down_since is None,
            "ostatnia_transakcja_s_temu": round(now - self.last_trade, 1),
            "zadan_w_kolejce": len(self.jobs),
            "liczniki": dict(self.c),
            "spoznione": self.agg.late,
            "duplikaty": self.agg.dups,
        }
        tmp = self.root / "status.json.tmp"
        tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1))
        os.replace(tmp, self.root / "status.json")

    # --- minuty i zadania
    def minute_ok(self, m: int) -> bool:
        start = m * 60.0
        return (
            self.up_since is not None
            and self.up_since <= start
            and (self.down_since is None or self.down_since >= start + 60.0)
        )

    def close_minutes(self, now: float) -> None:
        upto = int((now - GRACE_S) // 60) - 1
        first = self.agg.finalized_upto + 1 if self.agg.finalized_upto >= 0 else upto
        for m in range(first, upto + 1):
            rec = self.agg.finalize(m)
            ok = self.minute_ok(m)
            self._append(
                "minuty.jsonl",
                {
                    "m": m,
                    "ok": ok,
                    "coins": {
                        c: {"trades": v["trades"], "takers": v["takers"]} for c, v in rec.items()
                    },
                },
            )
            self.c["minuty"] += 1
            self.c["minuty_ok"] += int(ok)
            if ok:
                self.minutes[m] = rec
            for old in [k for k in self.minutes if k < m - KEEP_MIN]:
                del self.minutes[old]
            self.make_jobs(m, now)

    def make_jobs(self, m: int, now: float) -> None:
        for n in WINDOWS:
            if (m + 1) % n:
                continue
            start = m - n + 1
            if any((start + i) not in self.minutes for i in range(n)):
                self.c[f"okna_niepelne_N{n}"] += 1
                continue
            wt = window_takers(self.minutes, COINS, start, n)
            chosen = sample_addresses(wt, self.quota[n], seed=start * 100 + n + self.seed_salt)
            spread = 50.0 if n == 1 else n * 60.0 * 0.9
            for i, a in enumerate(chosen):
                nb = now + spread * i / max(1, len(chosen))
                self.push(nb, {"kind": "probka", "N": n, "start": start, "addr": a, "taker": wt[a]})
            self.c[f"okna_N{n}"] += 1
        if m % 60 == FULL_CHECK_MINUTE and m in self.minutes:
            wt = window_takers(self.minutes, COINS, m, 1)
            for a in sorted(wt):
                self.push(now, {"kind": "pelny", "N": 1, "start": m, "addr": a, "taker": wt[a]})
            self.c["pelne_okna"] += 1

    def push(self, not_before: float, job: dict) -> None:
        self.seq += 1
        job["enq"] = time.time()
        job["not_before"] = not_before
        heapq.heappush(self.jobs, (not_before, self.seq, job))

    def orders_of(self, addr: str, start: int, n: int) -> dict:
        out = {}
        for m in range(start, start + n):
            rec = self.minutes.get(m)
            if not rec:
                continue
            for coin in COINS:
                for h, (taker, f1, f2) in rec[coin]["orders"].items():
                    if taker == addr:
                        out[(coin, h)] = (f1, f2)
        return out

    # --- sieć
    async def post(self, session, body: dict):
        import aiohttp

        async with session.post(INFO_URL, json=body, timeout=aiohttp.ClientTimeout(total=30)) as r:
            if r.status == 429:
                return 429, None
            data = await read_limited(r.content.iter_chunked(65536))
            if r.status != 200:
                return r.status, None
            return 200, json.loads(data)

    async def run_job(self, session, job: dict) -> None:
        n, start, addr = job["N"], job["start"], job["addr"]
        t0, t1 = start * MIN_MS, (start + n) * MIN_MS - 1
        # zamrażamy mapę zleceń adresu przed zapytaniem (minuty mogą wypaść z pamięci)
        orders = self.orders_of(addr, start, n)
        fills: list = []
        seen = set()
        pages_sent: list = []
        n429 = 0
        s = t0
        truncated = False
        status = "ok"
        page = 0
        while True:
            while True:
                w = self.limiter.wait_s(time.time())
                if w <= 0:
                    break
                await asyncio.sleep(w)
            code, data = await self.post(
                session, {"type": "userFillsByTime", "user": addr, "startTime": s, "endTime": t1}
            )
            if code == 429:
                n429 += 1
                self.c["429"] += 1
                self.limiter.record(time.time(), EST_WEIGHT)
                d = backoff_s(n429 - 1)
                self.log(f"429 (adres {addr[:10]}, próba {n429}) — odczekanie {d:.0f} s")
                await asyncio.sleep(d)
                if n429 >= 6:
                    status = "429_porzucone"
                    break
                continue
            if code != 200 or not isinstance(data, list):
                status = f"http_{code}"
                self.limiter.record(time.time(), EST_WEIGHT)
                break
            now = time.time()
            wgt = query_weight(len(data))
            self.limiter.record(now, wgt)
            pages_sent.append((now, wgt))
            page += 1
            for f in data:
                k = (f.get("tid"), f.get("oid"), f.get("coin"))
                if k not in seen:
                    seen.add(k)
                    fills.append(f)
            if len(data) < FILLS_PAGE:
                break
            if page >= MAX_PAGES:
                truncated = True
                break
            s = max(int(f["time"]) for f in data) + 1
            if s > t1:
                break
        recv = time.time()
        an = analyze_fills(fills, addr)
        for lq in an["liqs"]:
            fl = orders.get((lq["coin"], lq["hash"]))
            lq["order_f1"], lq["order_f2"] = fl if fl else (None, None)
            lq["delay_s"] = round(recv - lq["T"] / 1000, 1)
        rec = {
            "kind": job["kind"],
            "N": n,
            "w_start": start,
            "addr": addr,
            "taker": job["taker"],
            "enq": round(job["enq"], 1),
            "not_before": round(job["not_before"], 1),
            "recv": round(recv, 1),
            "status": status,
            "pages": page,
            "pages_sent": [(round(t, 1), w) for t, w in pages_sent],
            "weight": sum(w for _, w in pages_sent),
            "fills": len(fills),
            "truncated": truncated,
            "n429": n429,
            "coins": an["coins"],
            "liqs": an["liqs"],
        }
        self._append("zapytania.jsonl", rec)
        self.c["zapytania"] += 1
        self.c["waga"] += rec["weight"]
        self.c["likwidacje"] += len(an["liqs"])

    async def worker(self, session, deadline: float) -> None:
        while time.time() < deadline:
            if not self.jobs or self.jobs[0][0] > time.time():
                await asyncio.sleep(0.5)
                continue
            _, _, job = heapq.heappop(self.jobs)
            stale = job["N"] * 120 + 300
            if time.time() - job["not_before"] > stale:
                self.c["porzucone_przeterminowane"] += 1
                continue
            try:
                await self.run_job(session, job)
            except Exception as e:  # noqa: BLE001 — błąd jednego zapytania nie przerywa pomiaru
                self.c["bledy_zapytan"] += 1
                self.log(f"błąd zapytania: {type(e).__name__}: {e}")
                await asyncio.sleep(2)

    async def ticker(self, deadline: float) -> None:
        last_status = last_log = 0.0
        while time.time() < deadline:
            now = time.time()
            self.close_minutes(now)
            if now - last_status >= 30:
                self.write_status()
                last_status = now
            if now - last_log >= 300:
                self.log(
                    f"waga60s={self.limiter.used(now)} zapytania={self.c['zapytania']} waga={self.c['waga']} "
                    f"likw={self.c['likwidacje']} 429={self.c['429']} kolejka={len(self.jobs)} "
                    f"minuty_ok={self.c['minuty_ok']}/{self.c['minuty']}"
                )
                last_log = now
            await asyncio.sleep(1.0)

    async def ws_loop(self, session, deadline: float) -> None:
        import aiohttp

        attempt = 0
        while time.time() < deadline:
            cycle_start = time.time()
            try:
                async with session.ws_connect(
                    WS_URL, heartbeat=None, max_msg_size=16 * 2**20
                ) as ws:
                    for c in COINS:
                        await ws.send_str(
                            json.dumps(
                                {
                                    "method": "subscribe",
                                    "subscription": {"type": "trades", "coin": c},
                                }
                            )
                        )
                    self.up_since = time.time()
                    self.down_since = None
                    self.last_trade = time.time()
                    self.log("połączono, subskrypcje trades: " + ",".join(COINS))
                    last_ping = time.time()
                    while time.time() < deadline:
                        if time.time() - last_ping > PING_EVERY_S:
                            await ws.send_str(json.dumps({"method": "ping"}))
                            last_ping = time.time()
                        if time.time() - self.last_trade > SILENCE_S:
                            self.log("cisza > 120 s — ponowne połączenie")
                            break
                        try:
                            m = await ws.receive(timeout=5)
                        except asyncio.TimeoutError:
                            continue
                        if m.type != aiohttp.WSMsgType.TEXT:
                            self.log(f"koniec strumienia: {m.type}")
                            break
                        d = json.loads(m.data)
                        if d.get("channel") == "trades":
                            for t in d.get("data", []):
                                self.agg.add(t)
                                if t.get("coin") == "BTC":
                                    self.last_trade = time.time()
                        elif d.get("channel") == "error":
                            self.c["ws_bledy"] += 1
                            self.log("ws error: " + str(m.data)[:300])
            except Exception as e:  # noqa: BLE001
                self.log(f"błąd połączenia: {type(e).__name__}: {e}")
            self.down_since = time.time()
            self.c["rozlaczenia"] += 1
            attempt = 0 if time.time() - cycle_start > 60 else attempt + 1
            await asyncio.sleep(min(60, 2**attempt))

    async def run(self) -> None:
        import aiohttp

        deadline = self.t_start + self.hours * 3600
        self.log(
            f"start pomiaru: godziny={self.hours} kwoty={self.quota} cel={self.limiter.target} "
            f"sufit={self.limiter.hard_cap} pid={os.getpid()}"
        )
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                self.ws_loop(session, deadline),
                self.ticker(deadline),
                self.worker(session, deadline),
            )
        self.write_status()
        self.log(f"koniec pomiaru: {dict(self.c)}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--godziny", type=float, default=26.0)
    ap.add_argument("--cel", type=int, default=TARGET_WEIGHT)
    ap.add_argument(
        "--kwoty", default=",".join(f"{n}:{k}" for n, k in DEFAULT_QUOTA.items()), help="N:k,…"
    )
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--podsumuj", action="store_true")
    a = ap.parse_args(argv)
    if a.status:
        p = a.dir / "status.json"
        print(p.read_text() if p.exists() else "BRAK status.json")
        return 0
    if a.podsumuj:
        print(summarize(load_jsonl(a.dir / "minuty.jsonl"), load_jsonl(a.dir / "zapytania.jsonl")))
        return 0
    quota = {int(k): int(v) for k, v in (x.split(":") for x in a.kwoty.split(","))}
    if set(quota) != set(WINDOWS):
        ap.error("kwoty muszą podać wszystkie okna 1,5,15,60")
    a.dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(Measurement(a.dir, a.godziny, quota, a.cel).run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
