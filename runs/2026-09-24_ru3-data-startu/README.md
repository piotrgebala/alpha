# RU3 — korekta daty startu TR1 i X2 (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed przebiegiem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Audyt AU1 znalazł ostatni ślad dziury w danych: dwie rundy (trend na monetach 21–50 i momentum na
top-50) zaczynały się od maja 2021, bo w obciętym katalogu brakowało monet na luty–kwiecień. W pełnych
danych monet jest dość, więc przeliczamy obie rundy od lutego 2021 — tymi samymi regułami.

## ID testu

RU3 — korekta danych (ciąg RU1/RU2), 0 wariantów; decyzja użytkownika 2026-09-24 („RU3: poprawna data startu”).

## Metadane

- Branch `ru3-data-startu`. Skrypt `backtest/run_start_fix_ru3.py`; dane `data/raw/universe_full`.

## Poprzedzające wyniki

- TR1 na pełnym uniwersum od 2021-05 (RU2): +13,0 %/rok, t 1,63. X2 (RU2): +23,1 %/rok, t 1,60 (jedna faza).
- **AU1 (wniosek 87) policzył już oba warianty w audycie:** TR1 od 2021-02 +15,5 %/rok, t 1,99; X2
  średnia 7 faz +21,9 %/rok, t 1,59. **Wyniki są więc znane przed tą rundą** — RU3 porządkuje zapis,
  a jej wynik NIE może być cytowany jako potwierdzenie (oglądany po fakcie).

## Pre-rejestracja

- **JEDNA zmienna:** data startu 2021-05-01 → 2021-02-01 (pełne uniwersum pozwala).
- **TR1:** reguła TS1 na miejscach 21–50 po obrocie, 7 faz, H0 z TS1 (100 przesunięć); kryterium jak TR1:
  POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0.
- **X2:** top-50, nogi po 10, trzymanie 7 dni — **średnia 7 faz** (różne dni startu tygodnia), bo pojedyncza
  faza zależy od dnia rebalansu (wniosek 68; AU1: zmiana dnia z soboty na poniedziałek dawała fałszywe t 2,52);
  kryterium X2: POZYTYWNY, gdy t_neff > 1,96.
- **Odczyt:** zapis porządkowy; próg rodzinny ~2,9 (~30 odczytów) pozostaje punktem odniesienia.

_(sekcje poniżej po przebiegu)_
