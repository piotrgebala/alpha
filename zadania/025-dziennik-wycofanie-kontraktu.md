---
id: 025
tytul: Dziennik przy wstrzymaniu lub wycofaniu kontraktu — zamarzła cena ostatnia, brak rozliczenia likwidacji i zamknięcia
typ: dziennik
status: w_toku
zlecil: orkiestrator
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: [017]
---

# 025 — Wycofanie kontraktu a rozliczenie w dzienniku

## Po co

LP1 (zadanie 017) pokazało, że przy wstrzymaniu lub wycofaniu kontraktu (FTT 2022-12, LUNA 2022-05, ALPACA 2025-05)
cena ostatnia zamarza, a cena mark dalej się zmienia. Według wykonawcy LP1 dziennik nie rozlicza wtedy ani likwidacji,
ani ceny zamknięcia (orkiestrator tego jeszcze nie sprawdzał na kodzie). Pozycja w wycofywanej monecie mogłaby zostać
w dzienniku z wynikiem niemożliwym do uzyskania. Użytkownik zgodził się 2026-09-29 dopisać to na tablicę („Wykonaj”);
zmiana dziennika wymaga osobnej decyzji.

## Zakres (po decyzji)

1. Sprawdzić na kodzie (`backtest/live_journal.py` i jego importy), co dziennik robi, gdy świece monety przestają się
   zmieniać albo znikają — bez oglądania wyników dziennika.
2. Opisać regułę rozliczenia (np. cena rozliczenia Binance przy wycofaniu, cena mark) i propozycję Poprawki N.

## Czego NIE robić

- Nie zmieniać kodu dziennika przed decyzją użytkownika i wpisem „Poprawka N” w `dziennik/README.md`.
- Nie zaglądać w wyniki dziennika (`dziennik/*.csv`); zob. 014.

## Kryteria odbioru (dowody)

- Opis zachowania dziennika z odnośnikami do kodu i testem na sztucznym przypadku zamarzniętej ceny.

## Wynik

- **2026-09-30, decyzja użytkownika: „25 zgoda”.** Krok 1 (przegląd kodu, bez zmian i bez wyników dziennika) zlecony wykonawcy razem z policzeniem, jak często moneta z koszyka top-20 była wstrzymana lub wycofana. Poprawka dziennika = osobna decyzja.
