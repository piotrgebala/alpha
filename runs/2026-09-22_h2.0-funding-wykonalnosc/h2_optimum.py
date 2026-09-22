# -*- coding: utf-8 -*-
"""H2.0f — OPTIMUM: czy istnieje prog, przy ktorym carry jest i oplacalne, i mierzalne?"""
import numpy as np, pandas as pd
from agents.feature_miner import compute_atr_14
from backtest.costs import round_trip_cost_fraction, MAKER, TAKER

ATR_M, Z95 = 1.5, 1.959964
cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
c = pd.read_parquet("data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet")
c = c.assign(atr_14=compute_atr_14(c)).dropna(subset=["atr_14"]).reset_index(drop=True)
B = (ATR_M * c["atr_14"] / c["close"]).median()
high, low, close, atr = (c["high"].to_numpy(), c["low"].to_numpy(),
                         c["close"].to_numpy(), c["atr_14"].to_numpy())
n = len(c)
r = pd.read_parquet("data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet")["funding_rate"]

V = 12  # 48h — powyzej tego trwanie sie nasyca (mediana 5 swiec niezaleznie od V)
trw = np.full(n, V, dtype=float)
for i in range(n - V):
    up, dn = close[i] + ATR_M * atr[i], close[i] - ATR_M * atr[i]
    for k in range(1, V + 1):
        if high[i + k] >= up or low[i + k] <= dn:
            trw[i] = k
            break
t = trw[: n - V]
okr_real, share_to = (t * 4 / 8).mean(), (t == V).mean()
B_eff = B * (1 - share_to) + B * 0.35 * share_to
trw_swiec = t.mean()

print("=" * 94)
print(f"OPTIMUM CARRY — V={V} (48h), realne trwanie {trw_swiec:.1f} swiec = {okr_real:.2f} okresow")
print(f"B_eff = {B_eff*100:.4f}%   C = {cost*100:.4f}%")
print("=" * 94)
print(f"  {'prog |f|':>9} | {'zdarzen':>7} | {'F real':>8} | {'prog p*':>8} | {'zapas do 50%':>12} | "
      f"{'n bez naklad.':>13} | {'n wymagane':>10} | {'margines':>9}")
print("  " + "-" * 90)
naklad = V * 4 / 8  # ile okresow funding trwa jedna pozycja -> co tyle mozna wejsc ponownie
best = None
for thr in (0.00010, 0.00012, 0.00015, 0.00020, 0.00025, 0.00030, 0.00040, 0.00050, 0.00080):
    sel = r[(r >= thr) | (r <= -thr)]
    n_zd = len(sel)
    F = sel.abs().mean() * okr_real
    p_star = 0.5 * (1 + (cost - F) / B_eff)
    zapas = 0.5 - p_star
    n_tx = n_zd / naklad
    n_req = (Z95 / zapas) ** 2 * 0.25 if zapas > 0 else float("inf")
    m = n_tx / n_req if n_req != float("inf") else 0.0
    if best is None or m > best[1]:
        best = (thr, m, n_tx, n_req, p_star)
    print(f"  {thr*100:8.3f}% | {n_zd:7d} | {F*100:7.4f}% | {p_star*100:7.2f}% | "
          f"{zapas*100:+11.2f} pp | {n_tx:13.0f} | "
          f"{('%.0f' % n_req) if n_req != float('inf') else 'n/d':>10} | {m:8.2f}x")

print()
print(f"  n wymagane = proba, przy ktorej dolny kraniec CI95 przebija p* przy prawdziwym p = 50%")
print(f"  (czyli: ile trzeba, zeby POKAZAC oplacalnosc nawet bez przewagi kierunkowej)")
print()
thr, m, n_tx, n_req, p_star = best
print(f"  NAJLEPSZA KOMORKA: prog |f| >= {thr*100:.3f}%, n={n_tx:.0f}, wymagane {n_req:.0f}, "
      f"margines {m:.2f}x -> {'WYKONALNE' if m >= 1 else 'NIEWYKONALNE'}")
