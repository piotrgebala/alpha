---
id: 022
tytul: Nowa wersja skilla `quant-strategy-catalog` — rodzina low-vol/BAB, poprawka opisu D1 vs TL1, statusy po mapie 007
typ: dokumentacja
status: w_toku
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Wykonaj wszystkie 3 punkty” (wpis pozycji backlogu z STATUS.md §17, ETAP 6, na tablicę)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, główna sesja albo 1 wykonawca"
---

# 022 — Skill katalogu strategii: nowa wersja

## Po co

Przegląd kandydatów z 2026-09-27 (`STATUS.md` §17, ETAP 6) wskazał dwa błędy skilla: w `families.md` brakuje rodziny
low-vol/BAB, a opis D1 nazywa TL1 „formą fundingu”, choć TL1 używał open interest. Od ostatniej wersji doszły też
wnioski 103–110 i mapa hipotez z zadania 007 (008, 009 i 013 zamknięte bez odczytu).

## Zakres

1. Wczytać skill `anthropic-skills:skill-creator` (zasada 19) i bieżącą wersję `quant-strategy-catalog` z konta.
2. Dopisać rodzinę low-vol/BAB (mechanizm, dane, formuła, status wobec projektu — bez nowych pomiarów).
3. Poprawić opis D1: TL1 = tłok lewara z open interest, nie funding.
4. Zaktualizować statusy rodzin do wniosku 110 i mapy 007 (`docs/mapa_hipotez_2026-10.md`), z odnośnikami.
5. Paczka `.skill` do wgrania przez użytkownika na claude.ai; jednozdaniowa notka w `STATUS.md`.

## Czego NIE robić

- Nie trzymać kopii skilla w repo (`.claude/skills/` zostaje puste).
- Nie liczyć niczego na danych — to zmiana dokumentacji, 0 odczytów.
- Nie łączyć z odchudzeniem `clas5-quant` (osobna decyzja, `STATUS.md` „Lista wykonania”).

## Kryteria odbioru (dowody)

- Różnica tekstu nowej i starej wersji (diff w gałęzi zadania, poza katalogiem skilli).
- Każdy nowy lub zmieniony status ma odnośnik do wniosku w `runs/INDEX.md` albo do mapy 007.
- Status `czeka_na_decyzje` do chwili wgrania paczki przez użytkownika.

## Wynik

(dopisuje orkiestrator)
