---
id: 009
tytul: G1 — reguła cyklu fundingu 8h (godziny przed i po rozliczeniu), rachunek mocy przed kartą
typ: badawcze
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: [007]
budzet: "Opus"
---

# 009 — G1: cykl fundingu 8h

## Po co

Jedyny efekt kalendarzowy NIETKNIĘTY jako reguła (makro-zdarzenia są NIEMIERZALNE, wniosek 81). Mechanizm: ktoś
MUSI zapłacić funding o 00/08/16 UTC, więc może zamykać pozycję tuż przed rozliczeniem. To zdarzenie częste
(3 na dobę × 5,4 roku ≈ 5 900), więc `n` jest duże — ale efekt na zdarzenie jest mały wobec kosztu 0,08 % (wniosek 90).

## Zakres

- `measurability_report` z `expected_trades` liczonym z częstości zdarzenia; efekt z literatury po publikacji.
- Test kryterium w granicy dużego `n` (zasada 18). Jeśli NIEMIERZALNA po kosztach → zamknąć bez odczytu.

## Czego NIE robić

- Nie przeszukiwać godzin wejścia/wyjścia. Jedna para godzin zapisana z góry.

## Kryteria odbioru (dowody)

Jak 008. Rachunek mocy przeliczony drugą drogą.

## Pytanie do użytkownika

Zgoda na rachunek mocy i — jeśli wyjdzie MIERZALNA — na jeden odczyt?

## Wynik

(dopisuje orkiestrator)
