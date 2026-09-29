---
id: 005
tytul: Hook audytowy — przegląd tygodnia obserwacji i propozycja, co blokować
typ: przeglad
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: dodać zadanie „po tygodniu obserwacji decyzja, czy hook ma zacząć blokować”"
utworzono: 2026-09-29
zalezy_od: [002, 003]
budzet: "Opus medium, krótko"
nie_wczesniej_niz: 2026-10-06
---

# 005 — Tydzień obserwacji hooka audytowego

## Po co

Hook `tools/audyt_hook.py` od 2026-09-29 tylko oznacza podejrzane działania w `~/.clas5_audyt/`. Po tygodniu
użytkownik decyduje, czy ma zacząć blokować (plan „oznacza → blokuje” w `docs/rag/13_izolacja_wykonawcow.md`).
To zadanie przygotowuje materiał do tej decyzji. **Nie startuje przed 2026-10-06.**

## Zakres

1. Zestawienie dzienników `~/.clas5_audyt/2026-09-29.jsonl` … `2026-10-05.jsonl`: liczba wywołań, liczba i odsetek
   oznaczonych per flaga, per narzędzie, per sesja/agent.
2. Każdy oznaczony wiersz przypisz do jednej z grup: prawdziwy powód do uwagi / fałszywy alarm (codzienna praca) /
   niejasne. Lista fałszywych alarmów z propozycją poprawki listy hostów albo reguły.
3. Propozycja dla każdej flagi: blokować / dalej tylko oznaczać / zmienić regułę. Przy każdej: ile wywołań z tygodnia
   zostałoby zablokowanych i czy coś z codziennej pracy (dziennik, kolektory, pytest, git) by się zepsuło.
4. Raport w `docs/rag/13` (sekcja „Tydzień obserwacji”) albo w osobnym pliku obok.

## Czego NIE robić

- Nie włączać blokowania. To decyzja użytkownika po raporcie.
- Nie przepisywać do repo poleceń z dziennika bez maskowania; w raporcie tylko zliczenia i skrócone, zamaskowane przykłady.

## Kryteria odbioru (dowody)

- Zliczenia z komendą, którą da się powtórzyć; jedna liczba przeliczona drugą drogą (np. `jq` i Python).
- Status `czeka_na_decyzje` z listą decyzji dla użytkownika.

## Wynik

(dopisuje orkiestrator)
