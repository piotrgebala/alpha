# -*- coding: utf-8 -*-
"""Z10: niezalezne przeliczenie liczby zbiorczej zamykajacej Faze 0 (CLAUDE.md zasada 16a)."""
import math

Z95 = 1.959964
Z80 = 0.841621

# Kanoniczne pomiary p PO naprawie przecieku early stopping (Z17+Z21), z raw_output.txt.
# S1 wylaczony: te same dane co S1b, ale zmierzone na pipelinie z MARTWYM early stoppingiem.
POMIARY = [
    ("5m  range (Z17+Z21)", 7043, 0.503763),
    ("5m  trend (Z17+Z21)",  299, 0.508361),
    ("4h  range (S1b)",      345, 0.475362),
]

print("=" * 80)
print("BILANS ZAMKNIECIA FAZY 0 — trafnosc kierunku na najczystszych pomiarach")
print("=" * 80)
n_tot = 0
w_tot = 0
for nazwa, n, p in POMIARY:
    w = p * n
    assert abs(w - round(w)) < 0.01, f"{nazwa}: {w} nie jest calkowite"
    w = int(round(w))
    half = Z95 * math.sqrt(p * (1 - p) / n)
    print(f"  {nazwa:22s} n={n:5d}  wygranych={w:5d}  p={p*100:6.2f}%  "
          f"CI95=[{(p-half)*100:5.2f}%; {(p+half)*100:5.2f}%]")
    n_tot += n
    w_tot += w

p_pool = w_tot / n_tot
half_pool = Z95 * math.sqrt(p_pool * (1 - p_pool) / n_tot)
z_pool = (p_pool - 0.5) / math.sqrt(0.25 / n_tot)

print("-" * 80)
print(f"  POOLED                 n={n_tot:5d}  wygranych={w_tot:5d}  p={p_pool*100:6.2f}%  "
      f"CI95=[{(p_pool-half_pool)*100:5.2f}%; {(p_pool+half_pool)*100:5.2f}%]")
print(f"  z wobec H0: p = 50%    z = {z_pool:+.4f}  -> "
      f"{'NIEODROZNIALNE od monety' if abs(z_pool) < Z95 else 'ISTOTNIE rozne od monety'}")
print(f"  polowa szerokosci CI   = {half_pool*100:.2f} pp")

print()
print("=" * 80)
print("WOBEC PROGOW OPLACALNOSCI ZMIERZONYCH W PROJEKCIE")
print("=" * 80)
PROGI = [("5m  range (C2.11, taker)", 0.8281), ("1h  range (Z9)", 0.5677),
         ("4h  range (S1b, maker/taker)", 0.526862)]
for nazwa, prog in PROGI:
    print(f"  {nazwa:30s} prog={prog*100:6.2f}%  luka od pooled p = {(prog-p_pool)*100:+6.2f} pp")

prog_min = min(p for _, p in PROGI)
gorny = p_pool + half_pool
print()
print(f"  Najnizszy prog oplacalnosci w projekcie: {prog_min*100:.2f}%")
print(f"  Gorny kraniec CI95 dla pooled p:         {gorny*100:.2f}%")
print(f"  >>> CI {'NIE SIEGA' if gorny < prog_min else 'SIEGA'} najnizszego progu "
      f"(roznica {(prog_min-gorny)*100:+.2f} pp)")

n_req = ((Z95 * 0.5 + Z80 * math.sqrt(prog_min * (1 - prog_min))) / (prog_min - 0.5)) ** 2
print()
print(f"  Transakcji na wykrycie p={prog_min*100:.2f}% wobec H0=50% (moc 80%): {n_req:.0f}")
print(f"  Zmierzono lacznie w projekcie:                                   {n_tot}")
print(f"  >>> moc {'WYSTARCZAJACA' if n_tot >= n_req else 'NIEWYSTARCZAJACA'} "
      f"({n_tot/n_req:.1f}x wymaganej proby)")
