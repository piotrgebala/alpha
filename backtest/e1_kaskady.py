"""
e1_kaskady.py — WYKONYWALNA definicja „kaskady likwidacji” z karty E1 (`runs/DRAFT_E1.md`, zadanie 011).

Ten moduł jest częścią pre-rejestracji: zapisany i zacommitowany PRZED policzeniem jakichkolwiek
zdarzeń na danych (hash commitu w karcie). Po commicie karty jest ZAMROŻONY (`runs/ZAMROZONE.txt`,
zasada 13) — zmiana definicji = nowa karta i nowy wariant w liczniku E1, nie poprawka.

Wejście to WYŁĄCZNIE liczniki likwidacji: czas, symbol, strona zlikwidowanej pozycji i nominał
(USDT). Moduł nie widzi i nie przyjmuje żadnej ścieżki ceny — cena wejścia/wyjścia pojawi się dopiero
przy odczycie (najwcześniej po kontroli mocy z §10 karty), poza tym modułem.

Definicja (karta §4; trzy wolne parametry ustalone z góry, bez dostrajania):
- dla monety `s` z koszyka top-20 miesiąca `m` (`dziennik/koszyk.csv`, `czlonek_top20`) i strony `d`
  (zlikwidowany long / short) liczymy sumę nominału likwidacji Bybit w oknie przesuwnym
  `(t − W, t]`, W = 60 min;
- KASKADA w chwili `t*` = pierwsza likwidacja, po której suma strony `d` ≥ θ · V(s, m), gdzie
  θ = 0,5 %, a V(s, m) = `sredni_obrot_30d` (średni dzienny obrót USDT z 30 dni przed miesiącem);
- jeśli w tej chwili DRUGA strona tej monety też jest ≥ progu → zdarzenie niejednoznaczne, pomijane
  (bez blokady); w przeciwnym razie zdarzenie liczy się, a moneta jest zablokowana na H = 24 h
  (żadnego nowego zdarzenia tej monety po żadnej stronie w `[t*, t* + 24 h)`);
- kierunek transakcji: PRZECIW zlikwidowanym (zlikwidowane longi → kupno, `kierunek = +1`;
  zlikwidowane shorty → sprzedaż, `kierunek = −1`);
- wejście: początek drugiej pełnej minuty po `t*` (`floor_min(t*) + 2 min`, opóźnienie 60–120 s),
  wyjście: wejście + 24 h.
"""

from __future__ import annotations

import csv
import datetime as dt
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

WINDOW_MS = 60 * 60 * 1000  # W = 60 min
THETA = Decimal("0.005")  # θ = 0,5 % średniego dziennego obrotu
HOLD_MS = 24 * 60 * 60 * 1000  # H = 24 h (horyzont i blokada monety)
MINUTE_MS = 60 * 1000
ENTRY_DELAY_MIN = 2  # wejście na początku drugiej pełnej minuty po zdarzeniu
SIDES = ("long", "short")  # strona ZLIKWIDOWANEJ pozycji
DIRECTION = {"long": 1, "short": -1}  # przeciw zlikwidowanym


@dataclass(frozen=True)
class Liq:
    """Jedna likwidacja — tylko pola dozwolone w karcie (bez ceny)."""

    symbol: str
    t_ms: int
    side: str  # "long" | "short"
    notional: Decimal


@dataclass(frozen=True)
class Cascade:
    symbol: str
    side: str  # strona zlikwidowana
    direction: int  # +1 kupno, −1 sprzedaż
    t_ms: int  # chwila t* (czas likwidacji, która przekroczyła próg)
    entry_ms: int
    exit_ms: int
    window_notional: Decimal  # suma strony w oknie w chwili t*
    threshold: Decimal

    @property
    def day(self) -> str:
        return month_of(self.entry_ms, fmt="%Y-%m-%d")


def month_of(t_ms: int, fmt: str = "%Y-%m") -> str:
    return dt.datetime.fromtimestamp(t_ms / 1000, tz=dt.timezone.utc).strftime(fmt)


def entry_time(t_ms: int) -> int:
    """`floor_min(t*) + 2 min`."""
    return (t_ms // MINUTE_MS) * MINUTE_MS + ENTRY_DELAY_MIN * MINUTE_MS


def load_universe(path: Path) -> dict[tuple[str, str], Decimal]:
    """`dziennik/koszyk.csv` → {(miesiąc, symbol): średni dzienny obrót USDT} tylko dla `czlonek_top20`."""
    out: dict[tuple[str, str], Decimal] = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["czlonek_top20"].strip() != "True":
                continue
            v = Decimal(row["sredni_obrot_30d"])
            if v <= 0:
                raise ValueError(f"koszyk: niedodatni obrót {row['miesiac']} {row['symbol']}")
            out[(row["miesiac"], row["symbol"])] = v
    return out


def thresholds(universe: dict[tuple[str, str], Decimal], theta: Decimal = THETA):
    """{(miesiąc, symbol): θ · V}."""
    return {k: theta * v for k, v in universe.items()}


def detect_cascades(
    events: Iterable[Liq],
    thr: dict[tuple[str, str], Decimal],
    window_ms: int = WINDOW_MS,
    hold_ms: int = HOLD_MS,
) -> list[Cascade]:
    """Kaskady według karty E1 (§4). Zdarzenia spoza uniwersum miesiąca są ignorowane w całości.

    Okno `(t − window_ms, t]` liczone po czasie likwidacji; zdarzenia o tym samym `t_ms` wchodzą
    do okna w kolejności z wejścia (stabilne sortowanie), a próg sprawdza się po każdym.
    """
    per_symbol: dict[str, list[Liq]] = {}
    for e in events:
        if e.side not in SIDES:
            raise ValueError(f"E1: nieznana strona {e.side!r}")
        if e.notional < 0:
            raise ValueError("E1: ujemny nominał")
        per_symbol.setdefault(e.symbol, []).append(e)

    out: list[Cascade] = []
    for symbol in sorted(per_symbol):
        evs = sorted(per_symbol[symbol], key=lambda e: e.t_ms)
        win = {s: deque() for s in SIDES}
        tot = {s: Decimal(0) for s in SIDES}
        blocked_until = None
        for e in evs:
            key = (month_of(e.t_ms), symbol)
            if key not in thr:
                continue
            win[e.side].append(e)
            tot[e.side] += e.notional
            for s in SIDES:  # wypadają zdarzenia z t ≤ t_e − W
                q = win[s]
                while q and q[0].t_ms <= e.t_ms - window_ms:
                    tot[s] -= q.popleft().notional
            if blocked_until is not None and e.t_ms < blocked_until:
                continue
            limit = thr[key]
            if tot[e.side] < limit:
                continue
            other = "short" if e.side == "long" else "long"
            if tot[other] >= limit:  # obie strony naraz → niejednoznaczne, bez blokady
                continue
            entry = entry_time(e.t_ms)
            out.append(
                Cascade(
                    symbol=symbol,
                    side=e.side,
                    direction=DIRECTION[e.side],
                    t_ms=e.t_ms,
                    entry_ms=entry,
                    exit_ms=entry + hold_ms,
                    window_notional=tot[e.side],
                    threshold=limit,
                )
            )
            blocked_until = e.t_ms + hold_ms
    out.sort(key=lambda c: (c.t_ms, c.symbol))
    return out
