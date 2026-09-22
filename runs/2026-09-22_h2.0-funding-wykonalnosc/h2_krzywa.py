# -*- coding: utf-8 -*-
"""
H2.0c — KRZYWA WYKONALNOSCI per interwal.

Wlasciwe pytanie (nie "ile transakcji trzeba", tylko): czy prog oplacalnosci lezy
W ZASIEGU tego, co przy dostepnej probie da sie odroznic od monety?

  wykonalne  <=>  min_detectable_hit_rate(n) < break_even_p

Geometria liczona z ATR, wiec resample z 4h jest tu dopuszczalny (Z9: ceny zgodne co
do grosza; psuje sie WOLUMEN, ktory w tym rachunku nie wystepuje). Eksperyment
wymagalby juz danych natywnych.
"""
import pandas as pd
from agents.feature_miner import compute_atr_14
from backtest.costs import round_trip_cost_fraction, MAKER, TAKER
from backtest.metrics import break_even_hit_rate, min_detectable_hit_rate

ATR_M = 1.5
cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
LEJEK = (3642 / 4297) * (345 / 3642)   # 8,03% — zmierzony w S1b

c4 = pd.read_parquet("data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet")
c1 = pd.read_parquet("data/raw/BTC-USDT-USDT_1h_20230701T000000Z_20260701T000000Z.parquet")

def agreguj(df, n):
    """Skleja n kolejnych swiec w jedna (OHLC; wolumen pomijany - nieuzywany tutaj)."""
    if n == 1:
        return df
    g = df.index // n
    out = df.groupby(g).agg(open=("open", "first"), high=("high", "max"),
                            low=("low", "min"), close=("close", "last"))
    return out.reset_index(drop=True)

# Skala roczna: ile swiec danego interwalu miesci sie w 6,80 roku
LATA_4H, LATA_1H = 6.80, 3.00

print("=" * 96)
print("KRZYWA WYKONALNOSCI: prog oplacalnosci vs to, co da sie zmierzyc")
print("=" * 96)
print(f"  koszt round-trip C = {cost*100:.4f}% (maker wejscie / taker wyjscie)")
print(f"  lejek swieca->transakcja = {LEJEK*100:.2f}% (zmierzony w S1b)")
print()
print(f"  {'interwal':>8} | {'swiec/6,8l':>10} | {'B_eff':>8} | {'break-even':>10} | "
       f"{'n_szac':>7} | {'min wykryw.':>11} | {'zapas':>7} | {'werdykt':>13}")
print("  " + "-" * 94)

WARIANTY = [
    ("1h",  c1, 1,  LATA_1H), ("2h",  c1, 2,  LATA_1H), ("3h",  c1, 3,  LATA_1H),
    ("4h",  c4, 1,  LATA_4H), ("8h",  c4, 2,  LATA_4H), ("12h", c4, 3,  LATA_4H),
    ("1d",  c4, 6,  LATA_4H), ("2d",  c4, 12, LATA_4H), ("3d",  c4, 18, LATA_4H),
]
for nazwa, src, mult, lata_src in WARIANTY:
    df = agreguj(src, mult)
    df = df.assign(atr_14=compute_atr_14(df)).dropna(subset=["atr_14"])
    # przeskaluj liczbe swiec na pelne 6,80 roku dostepnej historii
    n_swiec = int(len(df) * (6.80 / lata_src))
    B = (ATR_M * df["atr_14"] / df["close"]).median()
    B_eff = B * 0.4 + B * 0.35 * 0.6          # 60% timeoutow (Z5b)
    be = break_even_hit_rate(cost_fraction=cost, barrier_fraction=B_eff)
    n_szac = n_swiec * LEJEK
    mdhr = min_detectable_hit_rate(break_even_p=0.5, n_trades=max(n_szac, 1))
    zapas = (be - mdhr) * 100
    print(f"  {nazwa:>8} | {n_swiec:10d} | {B_eff*100:7.4f}% | {be*100:9.2f}% | "
          f"{n_szac:7.0f} | {mdhr*100:10.2f}% | {zapas:+6.2f} pp | "
          f"{'WYKONALNE' if zapas > 0 else 'NIEWYKONALNE':>13}")

print()
print("  B_eff       = mediana 1,5xATR/cena, skorygowana o 60% timeoutow (Z5b)")
print("  break-even  = trafnosc, od ktorej strategia zarabia po kosztach")
print("  min wykryw. = najnizsza trafnosc, jaka przy n_szac da sie odroznic od 50% (95%/80%)")
print("  zapas > 0   => prog oplacalnosci jest W ZASIEGU pomiaru")
print("  swiece 1h przeskalowane z 3 lat na 6,8 roku (wymagalyby dociagniecia historii)")
