---
id: 005
tytul: Hook audytowy — przegląd tygodnia obserwacji i propozycja, co blokować
typ: przeglad
status: czeka_na_decyzje
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

- **2026-10-06 (orkiestrator): raport gotowy → `czeka_na_decyzje`.** Gałąź `zadanie-005-audyt-tydzien-obserwacji`
  (`fffed60`) scalona w `5c6ceab`. Raport: [`docs/rag/13_tydzien_obserwacji.md`](../docs/rag/13_tydzien_obserwacji.md),
  sekcja „Decyzje dla użytkownika”.
  - **Liczby:** 2797 wywołań, 364 z flagą (13 %). 4 prawdziwe zdarzenia (pomiar LH0 w `~/likwidacje_hl`, zgodny
    z kartami 001/004), 7 niejasnych (polecenia ucięte na 300 znakach), 359 fałszywych alarmów. Dni 10-02…10-04 bez
    sesji (nie dziura w zapisie). Przy rekomendacji z raportu w tygodniu nie zostałoby zablokowane żadne wywołanie.
  - **Dowody:** komendy w sekcji „Jak powtórzyć” (jq i Python, obie drogi: 364 i 46 `siec_poza_lista`). Druga droga
    orkiestratora: 364 na 2797 (Python). Skan maskowania raportu bez trafień. 16c: Approve (tylko dokumentacja). Testy
    wykonawcy: 268 passed, kod 0. Pełny pytest na scalonym master: 2239 passed, 2 skipped, kod 0.
  - **Decyzje dla użytkownika** (rekomendacje z raportu; każda blokada osobno):
    1. `poswiadczenia` — blokować teraz tylko w narzędziach plikowych (0 odmów na 535 wywołań; wymaga R7); w Bash
       dalej oznaczać.
    2. `siec_poza_lista` — dalej tylko oznaczać (46 z 46 to przegląd literatury, zad. 026 — dane przeciw kolejności
       z ADR-13).
    3. `zapis_poza_repo` — oznaczać; najpierw R2, R4, R6 (z 27 zostają 4), potem ewentualnie blokada tylko dla
       subagentów.
    4. `zapis_tmp` — nie blokować; R5 (własny scratchpad sesji bez flagi) → 0 flag w tygodniu.
    5. `siec_host_nieznany` — nie blokować; R1, R2, R4 (m.in. błąd hooka przy `2>&1`) → 13–20 flag.
    6. `dziennik_audytu` — R8 (osobno odczyt i zapis), potem blokować tylko zapis (0 zapisów w tygodniu).
    7. `wejscie_nieczytelne`, `blad_analizy` — nie blokować.
    8. Lista hostów bez zmian.
    9. Zasięg blokad: na razie tylko serwer (zmienna środowiskowa w ustawieniach użytkownika), bo z Windows, Cowork
       i chmury nie ma dzienników.
  - **Zostało:** po decyzji — zadanie typu `naprawa`: poprawki R1–R6 i R8 (niczego nie blokują, z testami) i wybrane
    blokady (R7, `blokuj:`), potem drugi tydzień obserwacji i powtórka przeglądu tymi samymi komendami. Skill
    `data:explore-data` był w sesji wykonawcy niedostępny („Unknown skill”); procedurę przeczytano z pamięci
    podręcznej wtyczki.
