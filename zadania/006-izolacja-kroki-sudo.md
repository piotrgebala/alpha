---
id: 006
tytul: Izolacja wykonawców — kroki z sudo (użytkownik) i sprawdzenie po nich (orkiestrator)
typ: infra
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: dodać zadanie „kroki z sudo z docs/rag/13, które możesz wykonać tylko Ty”"
utworzono: 2026-09-29
zalezy_od: [002]
budzet: "Opus medium do sprawdzenia"
---

# 006 — Izolacja wykonawców: kroki z `sudo`

## Po co

`docs/rag/13_izolacja_wykonawcow.md` opisuje osobnego użytkownika systemu dla wykonawców (bez `~/.ssh`, kluczy
i danych kolektorów), uprawnienia katalogów, zaporę z listą hostów i repozytorium pośrednie z bramką `pre-receive`.
Kroki z `sudo` może wykonać tylko użytkownik. Orkiestrator ich nie robi.

## Podział pracy

1. **Użytkownik** wykonuje kroki z `sudo` z `docs/rag/13` po kolei, etapami. Po każdym etapie zmienia w tym pliku
   linię „Postęp” poniżej (albo mówi o tym w sesji).
2. **Orkiestrator**, gdy zobaczy postęp, sprawdza etap bez `sudo`: testy z dokumentu (np. czy `clas5wyk` nie czyta
   `~/.ssh`, czy push na `master` dostaje odmowę, czy host spoza listy jest zablokowany przez zaporę), i dopisuje wynik.
   Jeśli czegoś nie da się sprawdzić bez `sudo`, podaje użytkownikowi jedną komendę do uruchomienia.
3. Po ostatnim etapie orkiestrator proponuje zmianę w `zadania/README.md` (wykonawcy jako `clas5wyk`). Zmiana wymaga
   decyzji użytkownika.

Postęp: etap 1 — nie rozpoczęty; etap 2 — nie rozpoczęty; etap 3 — nie rozpoczęty.

## Czego NIE robić

- Orkiestrator nie uruchamia `sudo` i nie zmienia użytkowników ani uprawnień systemowych.
- Nie ruszać kolektorów, dziennika ani crona.

## Kryteria odbioru (dowody)

- Dla każdego etapu wynik sprawdzenia (komenda + wynik) w sekcji **Wynik**.
- Ścieżka odwrotu z `docs/rag/13` sprawdzona na sucho (czy komendy są kompletne).

## Wynik

(dopisuje orkiestrator)
