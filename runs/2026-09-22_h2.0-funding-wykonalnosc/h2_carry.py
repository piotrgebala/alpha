# -*- coding: utf-8 -*-
"""
H2.0d — funding jako PRZYCHOD, nie koszt.

Cala Faza 0 modelowala funding jednostronnie: jako skladnik kosztu (stala +0,01%/8h).
Ale strona, ktora OTRZYMUJE funding (short przy dodatnim, long przy ujemnym), dostaje go
jako przychod. Nierownosc rzadzaca zmienia sie z

    (2p-1)*B > C        na        (2p-1)*B + F > C,    F = |funding| * liczba okresow

czyli prog oplacalnosci spada:  p* = 0,5 * (1 + (C-F)/B).
Gdy F > C, prog jest PONIZEJ 50% — nie trzeba przewagi kierunkowej, zeby wyjsc na plus.

To NIE jest spojrzenie na target: liczy wylacznie geometrie wyplaty i liczebnosc proby.
"""
import numpy as np
import pandas as pd
from agents.feature_miner import compute_atr_14
from backtest.costs import round_trip_cost_fraction, MAKER, TAKER
from backtest.metrics import min_detectable_hit_rate

ATR_M, Z95 = 1.5, 1.959964
cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
LEJEK = (3642 / 4297) * (345 / 3642)

c4 = pd.read_parquet("data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet")
c4 = c4.assign(atr_14=compute_atr_14(c4)).dropna(subset=["atr_14"])
B = (ATR_M * c4["atr_14"] / c4["close"]).median()
B_eff = B * 0.4 + B * 0.35 * 0.6
f = pd.read_parquet("data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet")
r = f["funding_rate"]
LATA = 6.80

print("=" * 100)
print("FUNDING JAKO PRZYCHOD — prog oplacalnosci p* = 0,5*(1 + (C-F)/B)")
print("=" * 100)
print(f"  B_eff = {B_eff*100:.4f}%   C = {cost*100:.4f}%   (prog bez funding: "
      f"{50*(1+cost/B_eff):.2f}%)")
print()
print(f"  {'prog |f|':>9} | {'okr.':>4} | {'n zdarzen':>9} | {'F sr.':>8} | {'F-C':>9} | "
      f"{'prog p*':>8} | {'min wykryw.':>11} | {'werdykt':>13}")
print("  " + "-" * 96)

for thr in (0.0001, 0.00015, 0.0002, 0.0003, 0.0005):
    mask = (r >= thr) | (r <= -thr)
    sel = r[mask].abs()
    n_zd = int(mask.sum())
    for okresow in (1, 3, 6):          # 8h, 24h, 48h trzymania
        F = sel.mean() * okresow
        netto = cost - F
        p_star = 0.5 * (1 + netto / B_eff)
        # liczba NIEZALEZNYCH transakcji: zdarzenia dziela sie przez dlugosc trzymania
        n_tx = n_zd / okresow * LEJEK / LEJEK  # zdarzenia sa juz 8-godzinne
        n_tx = n_zd / okresow
        mdhr = min_detectable_hit_rate(break_even_p=0.5, n_trades=max(n_tx, 1))
        # wykonalne, gdy prog jest ponizej 50% (nie trzeba przewagi) ALBO w zasiegu pomiaru
        if p_star < 0.5:
            werdykt = "PROG < 50%"
        elif p_star > mdhr:
            werdykt = "w zasiegu"
        else:
            werdykt = "NIEWYKONALNE"
        print(f"  {thr*100:8.3f}% | {okresow:4d} | {n_zd:9d} | {F*100:7.4f}% | "
              f"{netto*100:+8.4f}% | {p_star*100:7.2f}% | {mdhr*100:10.2f}% | {werdykt:>13}")

print()
print("  okr.        = liczba okresow funding trzymania pozycji (1 = 8h, 3 = 24h, 6 = 48h)")
print("  F           = sredni otrzymany funding = |stawka| x liczba okresow")
print("  prog p*     = trafnosc, od ktorej strategia zarabia PO uwzglednieniu przychodu z funding")
print("  min wykryw. = najnizsza trafnosc odrozialna od 50% przy n_zdarzen/okresow transakcji")
print()
print("  UWAGA: n_tx = n_zdarzen/okresow to GORNA granica — zaklada, ze zdarzenia nie")
print("  nakladaja sie i kazde daje transakcje. Realnie mniej (abstynencja, foldy, nakladanie).")
