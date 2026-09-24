# NC1 — kontrola negatywna przyrządów na danych bez informacji o przyszłości (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed przebiegiem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Sprawdzamy nie strategię, tylko **nasze narzędzia pomiarowe**. Generujemy sztuczne ceny, które
wyglądają jak krypto (duże skoki, spokojne i nerwowe okresy, monety chodzące razem), ale w których
**z definicji nie da się przewidzieć kierunku**. Jeśli nasze silniki (trend tygodniowy, momentum
przekrojowe, reguła znaku premii Coinbase) pokażą na takich danych „zysk”, to znaczy, że gdzieś
w kodzie zaglądają w przyszłość albo źle liczą — a nie, że znalazły przewagę. Dodatkowo psujemy
silnik celowo (każemy mu znać przyszły tydzień), żeby upewnić się, że sprawdzian w ogóle umie
taki błąd złapać.

## Metadane

- Branch `metodyka-kontrole`. Moduł `backtest/negative_control.py` (+ `tests/test_negative_control.py`,
  8 testów); skrypt `backtest/run_negative_control_nc1.py`; komenda
  `PYTHONUTF8=1 py -m backtest.run_negative_control_nc1` → `raw_output.txt`.
- Dane: WYŁĄCZNIE syntetyczne (zasada 20 nie dotyczy — brak świec rynkowych). 40 losowań
  (ziarna 0–39) × 20 monet × 2 000 dni (≈ 5,5 roku, jak baza od 2021).
- Model zwrotów: t-Student df = 3 (grube ogony), GARCH(1,1) α = 0,08, β = 0,90 (grupowanie
  zmienności), wspólny czynnik rynkowy ρ = 0,5, średnia zmienność 4 %/dzień, średnia 0; funding 0;
  koszt 0,09 % obrotu.

## Poprzedzające wyniki

- **K1 (2026-09-22)** — kontrola POZYTYWNA modelu 4h (wyrocznia ze znanym sygnałem) + 6 losowań
  czystego szumu: 0 fałszywych alarmów. Dotyczyła tylko ścieżki model 4h → trafność; silniki
  portfelowe dziennych rund (TS1, X1, CP1, LQ1, SZ1 — wnioski 60–77) takiej kontroli nie miały.
- **TS1 / X1 / CP1** — H0 tych rund to przesunięte w czasie PRAWDZIWE sygnały na PRAWDZIWYCH cenach:
  test „czy ten sygnał jest lepszy od przypadkowego”, ale nie „czy silnik na danych bez żadnej
  informacji daje zero” (np. błąd w dryfie wag zawyżałby oba ramiona po równo).
- **Przegląd SIGMA** (`docs/rag/Repo lessons i sigma — co przydatne dla alpha.md`, wytyczna 2):
  tam brak kontroli negatywnej przepuścił AUC 0,84 z etykiety liczonej z przyszłego wygładzonego
  wskaźnika.

## Pre-rejestracja (zapisana przed przebiegiem)

- **Mierzone:** t_neff (`carry_hedged.summarize_pnl`, N_eff ≤ n) dziennego zwrotu BRUTTO i NETTO
  każdego silnika na każdym losowaniu.
- **Silniki:** TS1 (`ts_momentum.portfolio`, 7 faz), X1 (`xs_momentum.long_short_returns`,
  top/bottom 5 z 20), CP1 (reguła znaku z zewnętrznego szeregu: losowa premia AR(1), φ = 0,9,
  NIEZALEŻNA od cen, średnia 7 − średnia 90 dni, jedna moneta). Model 4h pominięty — kontrolę
  negatywną ma z K1 (6 losowań szumu, 0 alarmów).
- **Kryterium ZALICZENIA (każdy silnik, zwrot brutto):** |średnia t_neff z 40 losowań| < 0,5
  (se średniej ≈ 0,16 przy t ~ N(0,1)) ORAZ liczba losowań z |t| > 1,96 ≤ 5 z 40 (dwumian
  n = 40, p = 0,05: P(X ≥ 6) ≈ 4 %). Netto: średni zwrot ≤ brutto (koszty tylko odejmują).
- **Kontrola CZUŁOŚCI:** TS1 ze znakiem zwrotu NASTĘPNYCH 7 dni (celowe zajrzenie w przyszłość) —
  zaliczenie, gdy t_neff > 5 na każdym losowaniu. Jeśli nie — kontrola negatywna jest ślepa i
  jej zaliczenie nic nie znaczy.
- **Niezaliczenie** = błąd przyrządu do znalezienia PRZED jakąkolwiek dalszą rundą na tym silniku;
  wyniki rund opartych na nim (TS1/TR1/TP1/X1/X2/CP1/LQ1/SZ1) dostają adnotację „do ponownej
  weryfikacji”.
- **Liczniki:** 0 wariantów — test przyrządu, POZA licznikami hipotez (jak K1–K3, T4).

_(sekcje poniżej po przebiegu)_
