---
id: 011
tytul: E1 — karta pre-rejestracji kaskad likwidacji z rachunkiem mocy z realnej częstości zdarzeń (bez cen)
typ: badawcze
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: [004]
budzet: "Opus"
---

# 011 — E1: karta z góry, odczyt po roku

## Po co

E1 to jedyna rodzina z mocnym mechanizmem („ktoś MUSI handlować”), którą blokowały tylko dane. Dane zbierają
LK0 (od 2026-09-25), LB0 (od 2026-09-27) i LH0. Kartę trzeba zapisać, ZANIM ktokolwiek zestawi likwidacje z cenami —
inaczej definicja „kaskady” dopasuje się do wyniku.

## Zakres

- Definicja kaskady (próg wolumenu, okno), kierunek, horyzont i reguła wyjścia — zapisane teraz.
- Rachunek mocy z liczby zdarzeń (same liczniki z plików dziennych, bez cen) i projekcja: kiedy `n` wystarczy.
- Data odczytu (najwcześniej ~2027-09) i jeden licznik E1 wspólny dla trzech giełd.
- Rola HL: stan pozycji przed kaskadą tylko jako opis, nie druga zmienna.

## Czego NIE robić

- Żadnych cen po likwidacjach, żadnej „próbki”. Liczniki zdarzeń tak, zwroty nie.

## Kryteria odbioru (dowody)

Karta w `runs/DRAFT_E1.md` z hashem commita (dowód, że powstała przed odczytem).

## Pytanie do użytkownika

Zgoda na zapisanie karty teraz (odczyt dopiero za rok)?

## Wynik

(dopisuje orkiestrator)
