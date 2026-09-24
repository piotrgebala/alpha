"""
tradfi_panel.py — panel cen dziennych 19 rynków spoza krypto z FRED (runda TX1, ADR-09 szczebel 1b):
13 walut względem USD, ropa Brent, Nasdaq Composite, Nikkei 225 oraz obligacje
skarbowe USA 2/10/30 lat (indeks zwrotu z rentowności).

Konwencje (zapisane w pre-rejestracji TX1, przed wynikiem):
- waluty jako cena waluty w USD: serie kwotowane „waluta za USD” (DEXJPUS, …) są odwracane;
- WTI wykluczone (cena ujemna 2020-04-20 — zwrot nieokreślony); Brent zostaje;
- gaz Henry Hub (DHHNGSP) wykluczony PRZED wynikiem: dzienny spot fizyczny, skoki do +319 %/dzień
  (90 dni > 20 %) — towar nieprzechowywalny, po tej cenie nie da się handlować;
- obligacje: r_t = −D·(y_t − y_{t−1})/100 + y_{t−1}/100/365 na każdy dzień kalendarzowy
  (D stałe: 2 lata 1,9; 10 lat 8,5; 30 lat 18), potem indeks = Π(1 + r);
- indeks dzienny KALENDARZOWY z przeniesieniem ostatniej ceny na dni bez notowań (weekendy,
  święta) — zwrot 0 w te dni, więc σ̂ roczna z 365 dni jest poprawna i silnik TS1 (28 dni,
  7 faz, 365) działa bez zmiany parametrów; przeniesienie używa tylko przeszłych cen.
Testy: `tests/test_tradfi_panel.py`. Pobranie: `py -m data.tradfi_panel` (FRED, bez klucza).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

OUT_DIR = Path("data/raw/tradfi")
FX_USD_PER_UNIT = ["DEXUSEU", "DEXUSUK", "DEXUSAL", "DEXUSNZ"]
FX_UNITS_PER_USD = [
    "DEXJPUS",
    "DEXSZUS",
    "DEXCAUS",
    "DEXSDUS",
    "DEXNOUS",
    "DEXMXUS",
    "DEXKOUS",
    "DEXBZUS",
    "DEXSIUS",
]
PRICES = ["DCOILBRENTEU", "NASDAQCOM", "NIKKEI225"]
BONDS = {"DGS2": 1.9, "DGS10": 8.5, "DGS30": 18.0}
ALL_SERIES = FX_USD_PER_UNIT + FX_UNITS_PER_USD + PRICES + list(BONDS)
ASSET_CLASS = {
    **{s: "waluty" for s in FX_USD_PER_UNIT + FX_UNITS_PER_USD},
    "DCOILBRENTEU": "energia",
    "NASDAQCOM": "akcje",
    "NIKKEI225": "akcje",
    **{s: "obligacje" for s in BONDS},
}


def calendar_ffill(s: pd.Series, start: str, end: str) -> pd.Series:
    """Seria na każdym dniu kalendarzowym [start, end], ostatnia znana wartość przeniesiona dalej."""
    idx = pd.date_range(start, end, freq="D", tz="UTC")
    s = s.dropna()
    s.index = pd.to_datetime(s.index, utc=True).normalize()
    return s.reindex(s.index.union(idx)).ffill().reindex(idx)


def bond_index(yield_pct: pd.Series, duration: float) -> pd.Series:
    """Indeks zwrotu z rentowności (%) na siatce kalendarzowej: −D·Δy + narosłe odsetki y/365."""
    y = yield_pct.astype(float)
    r = -duration * y.diff() / 100.0 + y.shift(1) / 100.0 / 365.0
    first = y.first_valid_index()
    r = r.where(r.index > first)
    return (1.0 + r.fillna(0.0)).cumprod().where(y.notna())


def build_panel(raw: dict[str, pd.Series], start: str, end: str) -> pd.DataFrame:
    """Panel cen (kolumny = serie) na dniach kalendarzowych; waluty odwrócone, obligacje jako indeks."""
    cols = {}
    for name, s in raw.items():
        s = calendar_ffill(s, start, end)
        if name in FX_UNITS_PER_USD:
            s = 1.0 / s
        elif name in BONDS:
            s = bond_index(s, BONDS[name])
        if (s.dropna() <= 0).any():
            raise ValueError(f"{name}: cena ≤ 0 — seria nie nadaje się do zwrotów")
        cols[name] = s
    return pd.DataFrame(cols)


def load_raw(out_dir: Path = OUT_DIR) -> dict[str, pd.Series]:
    raw = {}
    for name in ALL_SERIES:
        df = pd.read_parquet(out_dir / f"fred_{name}_1d.parquet")
        raw[name] = df.set_index(pd.to_datetime(df["date"]))["value"].astype(float)
    return raw


def fetch(out_dir: Path = OUT_DIR, start: str = "1985-01-01") -> None:
    from data.fetch_external import fetch_fred

    for name in ALL_SERIES:
        fetch_fred(name, start, out_dir, force=True)


if __name__ == "__main__":
    fetch(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR)
