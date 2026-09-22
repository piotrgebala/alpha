# -*- coding: utf-8 -*-
"""H2.0b — wykonalnosc formulowania BEZ BRAMKI (funding jako 11. cecha na wszystkich swiecach)."""
import pandas as pd
from agents.feature_miner import compute_atr_14
from backtest.costs import round_trip_cost_fraction, MAKER, TAKER
from backtest.metrics import break_even_hit_rate, required_trades, Z_TWO_SIDED_95, Z_POWER_80

ATR_M = 1.5
cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)

# Lejek zmierzony w S1b (4h, rezim `range`, early stopping DZIALAJACY) — jedyne realne
# odniesienie, jakie mamy dla nowego pipeline'u.
S1B_KANDYDATOW = 4297      # swiec `range` po odsianiu `ambiguous`
S1B_OCENIONYCH = 3642      # z tego w oknach testowych
S1B_TRANSAKCJI = 345       # z tego z kierunkiem, po kill-switchu
udzial_okien = S1B_OCENIONYCH / S1B_KANDYDATOW
udzial_transakcji = S1B_TRANSAKCJI / S1B_OCENIONYCH

print("=" * 86)
print("LEJEK ODNIESIENIA (zmierzony w S1b, early stopping dzialajacy)")
print("=" * 86)
print(f"  swiec kandydujacych -> w oknach testowych : {udzial_okien*100:5.1f}%")
print(f"  w oknach testowych  -> transakcji         : {udzial_transakcji*100:5.1f}%  (abstynencja 90,5%)")
print(f"  lacznie: {udzial_okien*udzial_transakcji*100:.2f}% swiec kandydujacych staje sie transakcja")

print()
print("=" * 86)
print("WYKONALNOSC per interwal — formulowanie BEZ BRAMKI (wszystkie swiece kandyduja)")
print("=" * 86)
print(f"  {'interwal':>8} | {'swiec':>7} | {'B mediana':>9} | {'B_eff':>8} | {'break-even':>10} | "
      f"{'n_req':>6} | {'n_szac':>7} | {'margines':>8}")
print("  " + "-" * 84)

PLIKI = [
    ("4h", "data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet"),
    ("1h", "data/raw/BTC-USDT-USDT_1h_20230701T000000Z_20260701T000000Z.parquet"),
    ("5m", "data/raw/BTC-USDT-USDT_5m_20230701T000000Z_20260701T000000Z.parquet"),
]
for nazwa, plik in PLIKI:
    df = pd.read_parquet(plik)
    df = df.assign(atr_14=compute_atr_14(df)).dropna(subset=["atr_14"])
    B = (ATR_M * df["atr_14"] / df["close"]).median()
    # konserwatywnie 60% timeoutow (zmierzone w Z5b), timeout wychodzi ~0,35 bariery
    B_eff = B * 0.4 + B * 0.35 * 0.6
    be = break_even_hit_rate(cost_fraction=cost, barrier_fraction=B_eff)
    n_req = required_trades(p_true=be, p_null=0.5, z_alpha=Z_TWO_SIDED_95, z_power=Z_POWER_80)
    n_szac = len(df) * udzial_okien * udzial_transakcji
    print(f"  {nazwa:>8} | {len(df):7d} | {B*100:8.4f}% | {B_eff*100:7.4f}% | {be*100:9.2f}% | "
          f"{n_req:6.0f} | {n_szac:7.0f} | {n_szac/n_req:7.2f}x")

print()
print("  n_req  = proba na wykrycie p=break-even wobec H0=50% przy mocy 80%")
print("  n_szac = liczba swiec x lejek z S1b (udzial okien x udzial transakcji)")
print("  Margines >= 1,0x = wykonalne. Ponizej = eksperyment nie moze rozstrzygnac.")
