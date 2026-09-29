"""
liq_binance.py — cena likwidacji izolowanej wg progów depozytu Binance wobec płaskiego progu dziennika
(zadanie 017, runda LP1: `runs/2026-09-29_lp1-likwidacja-progi-binance/README.md`).

Moduł TYLKO OPISOWY. Nie jest w łańcuchu importów dziennika i niczego w nim nie zmienia: dziennik
(`backtest/live_journal.py`, `backtest/ts_momentum.py`) liczy dalej próg `1/dźwignia − MMR`, MMR = 1 %.

Wzór Binance (USDT-M, jedna pozycja izolowana, tryb jednokierunkowy), przepisany samodzielnie
z dokumentacji giełdy (bez importu freqtrade — zasada 8):

    LP = (WB + cum − s·Q·EP) / (Q·MMR − s·Q),   s = +1 long, −1 short,
    WB = Q·EP / L (depozyt izolowany),  N = Q·EP (nominał przy wejściu),

    ⇒ odległość do likwidacji jako ułamek ceny wejścia:
       long :  1 − LP/EP = (1/L + cum/N − MMR) / (1 − MMR)
       short:  LP/EP − 1 = (1/L + cum/N − MMR) / (1 + MMR)

`MMR` i `cum` (maintenance amount) z progu (bracket), do którego wpada nominał N:
`notionalFloor ≤ N < notionalCap`. Pomija opłaty i funding (jak próg dziennika).

Płaski próg dziennika: `1/L − mmr` (bez mianownika 1 ∓ MMR i bez cum).

Przekroczenia (krok 2): pozycja otwarta po zamknięciu dnia t po cenie OSTATNIEJ (last), okno dni
t+1…t+h; long „likwidowany” gdy min(low)/entry − 1 ≤ −próg, short gdy max(high)/entry − 1 ≥ próg.
Ta sama cena wejścia dla obu szeregów ekstremów (last i mark) — różnica mierzy tylko, czym giełda
WYZWALA likwidację (mark), a nie wejście.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

QUOTE = "USDT"


@dataclass(frozen=True)
class Tier:
    floor: float
    cap: float
    mmr: float
    cum: float
    max_lev: float


def tier_key(symbol: str) -> str:
    """'1000BONKUSDT' → '1000BONK/USDT:USDT' (klucz migawki freqtrade/ccxt)."""
    if not symbol.endswith(QUOTE) or len(symbol) == len(QUOTE):
        raise ValueError(f"nie symbol *USDT: {symbol}")
    return f"{symbol[: -len(QUOTE)]}/{QUOTE}:{QUOTE}"


def parse_tiers(raw: dict) -> dict[str, list[Tier]]:
    """Migawka (dict z JSON) → {klucz: progi rosnąco po floor}. Tylko kontrakty USDT-M."""
    out: dict[str, list[Tier]] = {}
    for key, rows in raw.items():
        if not key.endswith(f"/{QUOTE}:{QUOTE}"):
            continue
        tiers = []
        for r in rows:
            info = r.get("info", {})
            tiers.append(
                Tier(
                    floor=float(r["minNotional"]),
                    cap=float(r["maxNotional"]),
                    mmr=float(r["maintenanceMarginRate"]),
                    cum=float(info["cum"]),
                    max_lev=float(r["maxLeverage"]),
                )
            )
        tiers.sort(key=lambda t: t.floor)
        out[key] = tiers
    return out


def load_tiers(path: str | Path) -> dict[str, list[Tier]]:
    with open(path, encoding="utf-8") as fh:
        return parse_tiers(json.load(fh))


def bracket(tiers: list[Tier], notional: float) -> Tier:
    """Próg, do którego wpada nominał: floor ≤ N < cap. N ≥ ostatni cap → błąd (poza tabelą giełdy)."""
    if notional <= 0:
        raise ValueError("nominał musi być dodatni")
    for t in tiers:
        if t.floor <= notional < t.cap:
            return t
    raise ValueError(f"nominał {notional} poza progami (max cap {tiers[-1].cap})")


def binance_distance(lev: float, mmr: float, cum: float, notional: float, side: int) -> float:
    """Odległość ceny likwidacji od ceny wejścia (ułamek, > 0) wg wzoru Binance; side +1 long, −1 short."""
    if side not in (1, -1):
        raise ValueError("side musi być +1 albo −1")
    return (1.0 / lev + cum / notional - mmr) / (1.0 - side * mmr)


def binance_liq_price(
    entry: float, lev: float, mmr: float, cum: float, qty: float, side: int
) -> float:
    """Cena likwidacji wprost ze wzoru LP (druga droga do `binance_distance`, używana w teście)."""
    wb = qty * entry / lev
    return (wb + cum - side * qty * entry) / (qty * mmr - side * qty)


def flat_distance(lev: float, mmr: float = 0.01) -> float:
    """Próg dziennika: 1/dźwignia − MMR (ten sam dla longa i shorta)."""
    return 1.0 / lev - mmr


def forward_extremes(
    low: pd.DataFrame, high: pd.DataFrame, h: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Dla dnia t: min(low) i max(high) w dniach t+1…t+h (NaN, gdy w oknie brakuje choć jednego dnia).
    Patrzy w przód CELOWO: to pomiar ścieżki po wejściu, nie cecha modelu.
    """
    lo = low.rolling(h, min_periods=h).min().shift(-h)
    hi = high.rolling(h, min_periods=h).max().shift(-h)
    return lo, hi


def crossing_flags(
    entry: pd.DataFrame,
    fwd_low: pd.DataFrame,
    fwd_high: pd.DataFrame,
    thr_long: pd.Series | float,
    thr_short: pd.Series | float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(long_crossed, short_crossed) — bool; NaN w danych → False (maskę braków liczy wywołujący)."""
    move_down = 1.0 - fwd_low / entry
    move_up = fwd_high / entry - 1.0
    long_x = (
        move_down.ge(thr_long, axis=1) if isinstance(thr_long, pd.Series) else move_down >= thr_long
    )
    short_x = (
        move_up.ge(thr_short, axis=1) if isinstance(thr_short, pd.Series) else move_up >= thr_short
    )
    return long_x.fillna(False).astype(bool), short_x.fillna(False).astype(bool)


def contingency(last_x: pd.DataFrame, mark_x: pd.DataFrame, valid: pd.DataFrame) -> dict[str, int]:
    """Tabela 2×2 na komórkach `valid`: tylko last, tylko mark, oba, żaden."""
    v = valid.to_numpy(dtype=bool)
    a = last_x.to_numpy(dtype=bool) & v
    b = mark_x.to_numpy(dtype=bool) & v
    return {
        "n": int(v.sum()),
        "tylko_last": int((a & ~b).sum()),
        "tylko_mark": int((~a & b).sum()),
        "oba": int((a & b).sum()),
        "zaden": int((v & ~a & ~b).sum()),
    }


def flagged_cells(flags: pd.DataFrame, valid: pd.DataFrame) -> list[tuple[pd.Timestamp, str]]:
    """Lista (dzień, symbol) z flagą True w komórkach ważnych."""
    m = flags.to_numpy(dtype=bool) & valid.to_numpy(dtype=bool)
    rows, cols = np.nonzero(m)
    return [(flags.index[r], flags.columns[c]) for r, c in zip(rows, cols, strict=True)]
