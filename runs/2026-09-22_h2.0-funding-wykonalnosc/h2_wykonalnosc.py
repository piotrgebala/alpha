# -*- coding: utf-8 -*-
"""
H2.0 — WYKONALNOSC hipotezy funding-jako-sygnal. ZERO spojrzen na target.

Mierzy wylacznie: rozklad funding, trwalosc (autokorelacja + epizody), liczebnosc proby
przy kandydujacych progach, geometrie bariera-vs-koszt na 4h i moc statystyczna.
Zwiazek funding->zwrot NIE jest tu liczony celowo (C2.13: "monotoniczny skill" okazal sie
artefaktem selekcji post hoc; Z10 przenosi rachunek mocy PRZED eksperyment).
"""
import numpy as np
import pandas as pd

from agents.feature_miner import compute_atr_14
from agents.regime_coherence import regime_episodes
from backtest.costs import round_trip_cost_fraction, MAKER, TAKER
from backtest.metrics import break_even_hit_rate, required_trades, Z_TWO_SIDED_95, Z_POWER_80

pd.set_option("display.width", 200)

CANDLES = "data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet"
FUNDING = "data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet"
ATR_MULTIPLIER = 1.5

c = pd.read_parquet(CANDLES)
f = pd.read_parquet(FUNDING)

print("=" * 88)
print("1. DANE")
print("=" * 88)
print(f"  swiece 4h : {len(c):6d}  {c['timestamp'].min()} -> {c['timestamp'].max()}")
print(f"  funding   : {len(f):6d}  {f['timestamp'].min()} -> {f['timestamp'].max()}")
lata = (f["timestamp"].max() - f["timestamp"].min()).days / 365.25
print(f"  historia  : {lata:.2f} lat;  funding/rok = {len(f)/lata:.0f} (oczekiwane 1095,75)")

print()
print("=" * 88)
print("2. ROZKLAD FUNDING RATE (opisowy, bez targetu)")
print("=" * 88)
r = f["funding_rate"]
print(f"  srednia   = {r.mean()*100:+.5f}%   mediana = {r.median()*100:+.5f}%   sd = {r.std()*100:.5f}%")
print(f"  udzial ujemnych = {(r < 0).mean()*100:.2f}%   |  dokladnie 0,01% (stawka bazowa) = {(r == 0.0001).mean()*100:.2f}%")
print("  percentyle (w % za 8h):")
for q in (0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9):
    print(f"    p{q:<5} = {np.percentile(r, q)*100:+.5f}%")
print()
print("  ZAKOTWICZENIE KOSZTOWE: stala uzywana w Fazie 0 jako koszt = +0,01000%")
print(f"    -> udzial obserwacji ODBIEGAJACYCH od niej: {(r != 0.0001).mean()*100:.2f}%")
print(f"    -> annualizowany funding przy medianie: {r.median()*3*365.25*100:+.2f}%/rok")

print()
print("=" * 88)
print("3. TRWALOSC SYGNALU (czy funding jest informacja, czy szumem 8-godzinnym)")
print("=" * 88)
for lag in (1, 2, 3, 6, 21):
    print(f"  autokorelacja lag={lag:2d} ({lag*8:3d}h): {r.autocorr(lag):+.4f}")

print()
print("=" * 88)
print("4. MASA PUNKTOWA — pulapka dyskretna (jak direction_persistence_10 w C2.5)")
print("=" * 88)
BAZA = 0.0001
print(f"  udzial obserwacji DOKLADNIE rownych stawce bazowej {BAZA*100:.2f}%: {(r == BAZA).mean()*100:.2f}%")
print(f"  -> percentyle p20 i p80 obie wynosza {np.percentile(r,20)*100:+.5f}% / {np.percentile(r,80)*100:+.5f}%")
print("  -> PROGI PERCENTYLOWE SA TU NIEUZYWALNE: maska (r>=p80)|(r<=p20) lapie 70,2% obserwacji.")
print("     To dokladnie ten sam blad, ktory C2.5 wykryl w `direction_persistence_10`.")
print("     Wniosek dla H2: prog musi byc ABSOLUTNY (odchylenie od stawki bazowej), nie percentylowy.")

print()
print("=" * 88)
print("4b. LICZEBNOSC PROBY PRZY PROGACH ABSOLUTNYCH (dwustronnie)")
print("=" * 88)
print(f"  {'prog |f|':>12} | {'n zdarzen':>9} | {'% obs':>6} | {'na rok':>7} | {'dodatnie':>9} | {'ujemne':>7} | {'mediana epizodu':>15}")
print("  " + "-" * 92)
progi = {}
for thr in (0.0002, 0.0003, 0.0005, 0.0008, 0.0010):
    mask = (r >= thr) | (r <= -thr)
    n = int(mask.sum())
    npos, nneg = int((r >= thr).sum()), int((r <= -thr).sum())
    ep = regime_episodes(pd.Series(np.where(mask, "extreme", "normal")))
    ep_e = ep[ep["regime"] == "extreme"]["length"]
    med = ep_e.median() if len(ep_e) else 0
    progi[thr] = n
    print(f"  {thr*100:11.3f}% | {n:9d} | {n/len(r)*100:5.1f}% | {n/lata:7.0f} | "
          f"{npos:9d} | {nneg:7d} | {med:15.1f}")

print()
print("=" * 88)
print("5. GEOMETRIA BARIERA-vs-KOSZT na 4h (ta sama metodologia co Z9/Z5b)")
print("=" * 88)
c = c.copy()
c["atr_14"] = compute_atr_14(c)
c = c.dropna(subset=["atr_14"])
barrier_frac = (ATR_MULTIPLIER * c["atr_14"] / c["close"]).median()
print(f"  mediana bariery B = {ATR_MULTIPLIER} x ATR_14 / cena = {barrier_frac*100:.4f}% ceny")
print()
print(f"  {'V (swiec 4h)':>13} | {'horyzont':>9} | {'okresow funding':>15} | {'koszt C':>9} | {'break-even p':>12}")
print("  " + "-" * 74)
cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
print(f"  koszt round-trip C (maker wejscie / taker wyjscie, jak bramka kosztowa) = {cost*100:.4f}%")
print("  UWAGA: C nie zalezy od V (funding celowo poza ta funkcja, backtest/costs.py:126).")
print("  Od V zalezy EFEKTYWNE B: im krotszy horyzont, tym wiekszy udzial timeoutow,")
print("  ktore wychodza po cenie rynkowej, a nie na barierze (Z5b: przy V=3 to 60,8%).")
print()
be_full = break_even_hit_rate(cost_fraction=cost, barrier_fraction=barrier_frac)
print(f"  break-even p przy PELNEJ barierze B={barrier_frac*100:.4f}%: {be_full*100:.2f}%")
print()
print(f"  {'udzial timeoutow':>17} | {'efektywne B':>11} | {'break-even p':>12}")
print("  " + "-" * 48)
for share_to in (0.0, 0.3, 0.6, 0.8):
    # timeout wychodzi srednio po ~1/3 bariery (Z5b/S1: 0,714% vs 2,036%)
    b_eff = barrier_frac * (1 - share_to) + barrier_frac * 0.35 * share_to
    print(f"  {share_to*100:16.0f}% | {b_eff*100:10.4f}% | "
          f"{break_even_hit_rate(cost_fraction=cost, barrier_fraction=b_eff)*100:11.2f}%")

print()
print("=" * 88)
print("6. MOC STATYSTYCZNA (Z19 / Z10 pkt 4: liczone PRZED eksperymentem)")
print("=" * 88)
# Konserwatywnie: zakladamy udzial timeoutow 60% (zmierzony w Z5b przy V=3 na 4h)
b_eff = barrier_frac * 0.4 + barrier_frac * 0.35 * 0.6
be = break_even_hit_rate(cost_fraction=cost, barrier_fraction=b_eff)
n_req = required_trades(p_true=be, p_null=0.5, z_alpha=Z_TWO_SIDED_95, z_power=Z_POWER_80)
print(f"  Zalozenie konserwatywne: 60% timeoutow (zmierzone w Z5b), B_eff = {b_eff*100:.4f}%")
print(f"  break-even p = {be*100:.2f}%")
print(f"  Wymagana proba na wykrycie p=break-even wobec H0=50% przy mocy 80%: {n_req:.0f}")
print()
print(f"  {'prog |f|':>12} | {'n zdarzen':>9} | {'margines mocy':>13} | {'werdykt':>16}")
print("  " + "-" * 60)
for thr, n in progi.items():
    m = n / n_req
    print(f"  {thr*100:11.3f}% | {n:9d} | {m:12.2f}x | "
          f"{'WYKONALNE' if m >= 1.0 else 'NIEWYKONALNE':>16}")
print()
print("  UWAGA: powyzsze n to liczba ZDARZEN funding, nie transakcji. Realna proba bedzie")
print("  MNIEJSZA o abstynencje modelu (w S1b siegala 90,5%) i o foldy pominiete przez")
print("  MIN_TRAIN_ROWS. To gorna granica, nie prognoza.")
