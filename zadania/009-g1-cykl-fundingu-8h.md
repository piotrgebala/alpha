---
id: 009
tytul: G1 — reguła cyklu fundingu 8h (godziny przed i po rozliczeniu), rachunek mocy przed kartą
typ: badawcze
status: odrzucone
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „wykonaj tak jak uwazasz” (akceptacja rekomendacji orkiestratora po zadaniu 007)"
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

**Zamknięte bez odczytu 2026-09-29** decyzją użytkownika. Powód: `docs/mapa_hipotez_2026-10.md` (zadanie 007) — rodzina NIEMIERZALNA nawet przy hojnych założeniach; odczyt nic by nie rozstrzygnął, a jako 41. odczyt historii podniósłby próg dla kolejnych hipotez. 0 odczytów, 0 wierszy w `runs/odczyty_historii.csv`. Powrót tylko przy nowym źródle danych poza historią 2021–2026 albo nowym mechanizmie — jako nowe zadanie.
