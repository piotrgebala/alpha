---
id: 011
tytul: E1 — karta pre-rejestracji kaskad likwidacji z rachunkiem mocy z realnej częstości zdarzeń (bez cen)
typ: badawcze
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: zgoda na wszystkie 008–014 („Wszystkie 008–014”); odczyty na historii startują tylko, jeśli mapa 007 uzna rodzinę za MIERZALNĄ"
utworzono: 2026-09-29
zalezy_od: [004]
nie_wczesniej_niz: 2026-09-30
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

**2026-09-29:** decyzja dopiero po wyniku pomiaru wag z zadania 004 (koniec ≈ 2026-09-30 10:33 UTC); wtedy orkiestrator przedstawi rekomendację (kolejność z mapy 007: E1 → sonda HL). Status bez zmian.
