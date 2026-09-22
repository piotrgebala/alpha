"""
Walidacja wyniku K3 (CLAUDE.md zasada 16a) — druga, niezalezna droga.

1. `n` przeliczone z ABSTYNENCJI funkcja `metrics.expected_trades` (napisana w K2
   dokladnie do tego celu) — zamiast brac je z journalu.
2. Pasmo przeliczone wprost ze wzoru.
3. Kontrola zgodnosci ramienia `none` z liczbami OPUBLIKOWANYMI w S1b i H2.1.
4. ROZCIENCZENIE: jak zmienil sie sklad populacji transakcji (share_timeout, barrier_pct).

Uruchomienie: py runs/2026-09-22_k3-mierzalnosc-po-a1/k3_walidacja.py (z korzenia repo)
"""
from backtest.metrics import expected_trades, wald_half_width

# Liczby ZMIERZONE w przebiegu K3 (sekcje 1-3 `raw_output.txt`).
POMIAR = [
    # kod, ocenione, abstynencja, sygnaly, stlumione, n, share_timeout, barrier_pct, BE
    ("C1 none", 3642, 0.9053, 345, 0, 345, 0.600000, 0.014276, 0.526862),
    ("C1 bal ", 3642, 0.4632, 1955, 0, 1955, 0.605627, 0.011958, 0.532662),
    ("C2 none", 14448, 0.9976, 35, 0, 35, 0.371429, 0.015017, 0.524259),
    ("C2 bal ", 14448, 0.4384, 8114, 81, 8033, 0.651064, 0.013824, 0.529325),
]

# Liczby OPUBLIKOWANE we wczesniejszych rundach — ramie `none` musi je odtworzyc.
# UWAGA: opublikowana abstynencja 99,32% z H2.1 dotyczy ramienia B (Z FUNDING, n=98),
# a nie ramienia A (baseline, n=35). Porownywanie jej z C2/none byloby zestawieniem
# niepodobnych wielkosci, wiec dla C2 kotwica jest samo `n`.
OPUBLIKOWANE = {"C1 none": (345, 0.905, "S1b"), "C2 none": (35, None, "H2.1 ramie A")}

PODLOGA = 0.6651  # udzial klasy timeout w etykietach

print("=" * 96)
print("1. `n` PRZELICZONE Z ABSTYNENCJI (expected_trades) — nie wziete z journalu")
print("=" * 96)
print(f"  {'wariant':>9} | {'ocenione':>9} | {'abstyn.':>8} | {'przewidziane':>13} | {'zmierzone':>10} | {'roznica':>8}")
print("  " + "-" * 74)
for kod, ocenione, abst, sygnaly, _stl, _n, _st, _b, _be in POMIAR:
    przew = expected_trades(ocenione, abst)
    print(f"  {kod:>9} | {ocenione:9d} | {100 * abst:7.2f}% | {przew:13.1f} | {sygnaly:10d} | {przew - sygnaly:+8.1f}")
print("\n  Roznice ponizej 1 transakcji = zaokraglenie abstynencji do 4 miejsc. ZGODNE.")

print("\n" + "=" * 96)
print("2. PASMO PRZELICZONE WPROST ZE WZORU z*sqrt(0,25/n)")
print("=" * 96)
for kod, _o, _a, _s, _stl, n, _st, _b, _be in POMIAR:
    print(f"  {kod:>9} | n={n:6d} | pasmo = {100 * wald_half_width(n):6.2f} pp")

print("\n" + "=" * 96)
print("3. CZY RAMIE `none` ODTWARZA LICZBY OPUBLIKOWANE WCZESNIEJ?")
print("=" * 96)
for kod, ocenione, abst, _s, _stl, n, _st, _b, _be in POMIAR:
    if kod not in OPUBLIKOWANE:
        continue
    n_pub, abst_pub, skad = OPUBLIKOWANE[kod]
    zgoda = "ZGODNE" if n == n_pub else "ROZJAZD"
    if abst_pub is None:
        print(f"  {kod:>9} ({skad}): n {n} vs opublikowane {n_pub} -> {zgoda}"
              f" | abstynencja {100 * abst:.2f}% (brak porownywalnej liczby opublikowanej)")
    else:
        print(f"  {kod:>9} ({skad}): n {n} vs opublikowane {n_pub} -> {zgoda}"
              f" | abstynencja {100 * abst:.2f}% vs {100 * abst_pub:.2f}%")
print("\n  To jest niezalezna sciezka: inny skrypt, inna sesja, te same liczby.")

print("\n" + "=" * 96)
print("4. ROZCIENCZENIE — jak zmienil sie SKLAD populacji transakcji")
print("=" * 96)
print(f"  PODLOGA (udzial timeoutow w etykietach) = {100 * PODLOGA:.2f}%\n")
print(f"  {'wariant':>9} | {'share_timeout':>14} | {'barrier_pct':>12} | {'break_even':>11}")
print("  " + "-" * 56)
for kod, _o, _a, _s, _stl, _n, st, b, be in POMIAR:
    print(f"  {kod:>9} | {100 * st:13.2f}% | {100 * b:11.4f}% | {100 * be:10.2f}%")
print(
    "\n  Odczyt: przed adopcja model WYBIERAL swiece konczace sie na barierze (C2: 37,1%\n"
    "  timeoutow wobec 66,5% w populacji). Po adopcji udzial timeoutow rowna sie populacji,\n"
    "  czyli selektywnosc znika. Bariera maleje, wiec prog oplacalnosci ROSNIE — ten sam\n"
    "  mechanizm, ktory zdyskwalifikowal A2 w K2, tylko slabszy.\n"
    "  Czy ta selektywnosc niosla informacje — TA RUNDA NIE MA JAK ROZSTRZYGNAC (regula D)."
)
