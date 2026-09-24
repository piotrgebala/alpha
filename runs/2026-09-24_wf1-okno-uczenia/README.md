# WF1 — dłuższe okno uczenia modelu 4h (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed wynikiem).** Rachunek mocy w `moc.txt`.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Użytkownik: „może okno jest za wąskie — BTC porusza się w dłuższych cyklach”. Model kierunku na
świecach 4h uczył się dotąd tylko na 60 ostatnich dniach. Sprawdzamy, czy uczenie na roku albo
dwóch latach historii daje lepsze przewidywania. Wszystko inne zostaje bez zmian.

## ID testu

WF1 — seria WF (okno uczenia), otwarta decyzją użytkownika 2026-09-24 dla tej jednej zmiennej
(seria modeli Fazy 0 była zamknięta regułą STOP).

## Metadane

- Branch `wf1-okno-uczenia`. Skrypt `backtest/run_train_window_wf1.py` (buduje na zamrożonym
  `run_horizon_y`: te same cechy, wejście, model wypełnień, koszty).
- Dane: natywne świece 4h BTC/USDT:USDT od 2021-01-01 (zasada 20), 12 042 świece.

## Poprzedzające wyniki

- Kontrola 4h (wniosek 46): p 49,58 % [48,39; 50,77], r̄ netto −0,107 %/transakcję, n 6 789, abstynencja 40,4 %.
- T4 (wniosek 41): najlepsza możliwa liczba drzew poprawia stratę tylko o 0,7 % → cechy niosą mało informacji.
- Y2 (1d, okno 365 dni): p 50,2 % [47,1; 53,3], n ≈ 1 000 — nierozstrzygnięty (za mało transakcji).
- Długości okna uczenia na 4h nigdy nie badano jako zmiennej.

## Pre-rejestracja (przed wynikiem)

- **Hipoteza:** dłuższe okno uczenia (więcej różnych stanów rynku) poprawia trafność i zwrot netto
  modelu kontrolnego 4h.
- **JEDNA zmienna:** `train_days` ∈ {60 (kontrola, 0 wariantów), 365, 730}; test/krok 28/28 dni.
- **Wspólny okres oceny:** sygnały z `timestamp` ≥ 2023-01-01 (pierwszy dzień testu ramienia 730
  przy danych od 2021-01-01) — ten sam zbiór świec dla wszystkich ramion; filtr czasu, nie wyniku.
- **Kryterium per ramię (m = 2, z = 2,241):** POZYTYWNY, gdy t_neff zwrotu netto > 2,241 ORAZ
  ci_low(p) > p*; NEGATYWNY, gdy t_neff < −2,241 przy n ≥ required_trades(0,50; BE); inaczej
  NIEROZSTRZYGNIĘTY. Kontrola 60 dni: odczyt przy z = 1,96, bez licznika.
- **Opisowo:** ramiona na pełnym okresie każdego z nich (kontrola na pełnym okresie powinna
  odtworzyć znane liczby: n 6 789, p 49,58 % — sprawdzian odtwarzalności).
- **Mierzalność (`moc.txt`):** wspólne 7 662 świece → oczekiwane n ≈ 4 541 na ramię, half-width
  1,66 pp (z 2,241), próg ±B ≈ 51,7 %; `measurability_report(0,56; 0,5174; 4 541)` → **MIERZALNA**.
- **Licznik:** nowa seria WF 2/2 (365, 730), STOP po tej rundzie.

_(sekcje poniżej po przebiegu)_
