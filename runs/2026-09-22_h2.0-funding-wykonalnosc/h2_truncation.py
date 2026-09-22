# -*- coding: utf-8 -*-
"""
H2.0e — KONTROLA: czy bariera ATR ucina zbieranie funding?

Rachunek carry zaklada F = |f| x liczba_okresow. Ale triple-barrier zamyka pozycje,
gdy cena dotknie +/-1,5xATR — a wtedy funding przestaje sie naliczac. Jesli bariera
pada srednio po 1 okresie, a zakladalismy 6, cala arytmetyka carry jest fikcja.

Mierzone: ile okresow funding pozycja REALNIE przezywa. To pomiar geometrii (kiedy
pada bariera), niezalezny od kierunku — nie jest spojrzeniem na target.
"""
import numpy as np
import pandas as pd
from agents.feature_miner import compute_atr_14

ATR_M = 1.5
c = pd.read_parquet("data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet")
c = c.assign(atr_14=compute_atr_14(c)).dropna(subset=["atr_14"]).reset_index(drop=True)

high, low, close, atr = (c["high"].to_numpy(), c["low"].to_numpy(),
                         c["close"].to_numpy(), c["atr_14"].to_numpy())
n = len(c)

print("=" * 84)
print("ILE SWIEC 4h PRZEZYWA POZYCJA, ZANIM DOTKNIE BARIERY +/-1,5xATR")
print("=" * 84)
for V in (3, 6, 12, 18):
    trwanie = np.full(n, V, dtype=float)
    for i in range(n - V):
        up, dn = close[i] + ATR_M * atr[i], close[i] - ATR_M * atr[i]
        for k in range(1, V + 1):
            if high[i + k] >= up or low[i + k] <= dn:
                trwanie[i] = k
                break
    t = trwanie[: n - V]
    okresy = t * 4 / 8            # swiece 4h -> okresy funding 8h
    print(f"  V={V:2d} ({V*4:3d}h): mediana trwania = {np.median(t):4.1f} swiec "
          f"({np.median(okresy):4.2f} okresow funding), srednia = {t.mean():4.1f} "
          f"({okresy.mean():4.2f} okr.), timeoutow = {(t == V).mean()*100:5.1f}%")

print()
print("=" * 84)
print("SKUTEK DLA ARYTMETYKI CARRY (prog p* = 0,5*(1 + (C-F)/B))")
print("=" * 84)
from backtest.costs import round_trip_cost_fraction, MAKER, TAKER
cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
B = (ATR_M * c["atr_14"] / c["close"]).median()
f = pd.read_parquet("data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet")
r = f["funding_rate"]

print(f"  {'prog |f|':>9} | {'V':>3} | {'okr. ZAKL.':>10} | {'okr. REAL':>9} | "
      f"{'F zakl.':>8} | {'F real':>8} | {'p* zakl.':>8} | {'p* real':>8}")
print("  " + "-" * 82)
for thr in (0.0002, 0.0003, 0.0005):
    sel = r[(r >= thr) | (r <= -thr)].abs().mean()
    for V in (6, 12):
        trwanie = np.full(n, V, dtype=float)
        for i in range(n - V):
            up, dn = close[i] + ATR_M * atr[i], close[i] - ATR_M * atr[i]
            for k in range(1, V + 1):
                if high[i + k] >= up or low[i + k] <= dn:
                    trwanie[i] = k
                    break
        okr_real = (trwanie[: n - V] * 4 / 8).mean()
        okr_zakl = V * 4 / 8
        # B_eff: bariera pelna gdy trafiona, ~0,35 gdy timeout
        share_to = (trwanie[: n - V] == V).mean()
        B_eff = B * (1 - share_to) + B * 0.35 * share_to
        F_z, F_r = sel * okr_zakl, sel * okr_real
        p_z = 0.5 * (1 + (cost - F_z) / B_eff)
        p_r = 0.5 * (1 + (cost - F_r) / B_eff)
        print(f"  {thr*100:8.3f}% | {V:3d} | {okr_zakl:10.1f} | {okr_real:9.2f} | "
              f"{F_z*100:7.4f}% | {F_r*100:7.4f}% | {p_z*100:7.2f}% | {p_r*100:7.2f}%")
