---
id: 022
tytul: Nowa wersja skilla `quant-strategy-catalog` — rodzina low-vol/BAB, poprawka opisu D1 vs TL1, statusy po mapie 007
typ: dokumentacja
status: zrobione
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

- **Przygotowane 2026-09-29, czeka na wgranie przez użytkownika.** Gałąź `zadanie-022-skill-katalog-lowvol-d1-tl1`
  (`822e18f`), scalona do master. W repo: `docs/skille/quant-strategy-catalog_2026-09-29.diff` (+273 / −89, 4 pliki
  skilla, sumy w nagłówku) i notka w `STATUS.md` (lista „czeka na użytkownika”, punkt 10).
- **Paczka:** `~/pakiety_skilli/quant-strategy-catalog_2026-09-29.skill`, sha256 `11daffd2b77a161fe395793d5913febe04860963910e07daee4c6da20ff8517b`
  (4 pliki, `name: quant-strategy-catalog`; walidator skill-creatora przeszedł; kopia synced + diff = paczka bajt w bajt).
- **Zmiany:** nowa rodzina B5 niska zmienność / BAB (NIEMIERZALNE-bez-odczytu; `docs/rag/11` §5, wnioski 81, 92, 107);
  D1: TL1 to open interest, nie funding → nowa rodzina E3 (66, 75, 90, 97); statusy z mapy 007 (B3, G1, Y2, B4, C1, D3,
  HL-P, HL-L), K1 rynki tradycyjne (84, 109), próg t 3,84 dla 41. odczytu (107). 22 z 22 zmienionych statusów
  z odnośnikiem. Wniosek 111 (LP1) nieujęty — zakres „do 110”, statusu rodziny nie zmienia.
- **Dowody (sprawdził orkiestrator):** hash paczki zgodny, zawartość (SKILL.md, nazwa) sprawdzona; diff gałęzi = 3 pliki
  dokumentacji; pytest wykonawcy 1 927 passed, kod 0; strażniki dokumentacji na master po scaleniu zielone.
- **Zostało:** użytkownik wgrywa paczkę na claude.ai jako zamiennik `quant-strategy-catalog`; potem orkiestrator
  porównuje sumy w `~/.claude/skills/synced/` z nagłówkiem diffu, zmienia status na `zrobione` i usuwa punkt 10
  ze `STATUS.md`.
- **2026-09-30 ~05:45 UTC:** użytkownik: „skill załadowany” (paczkę wysłano mu jeszcze raz, sha256 `11daffd2…`).
  Sumy w `~/.claude/skills/synced/` o 05:47 UTC nadal stare: kopia lokalna odświeża się przy starcie sesji,
  a `/reload-skills` jej nie pobiera. Zostało: porównanie sum w następnej sesji, potem `zrobione` i usunięcie
  punktu 10 ze `STATUS.md`.
- **2026-09-30 ~06:00 UTC: sprawdzone.** Sumy 4 plików w `~/.claude/skills/synced/…/quant-strategy-catalog/` = nagłówek diffu (`bbed5a95…`, `c8ad4dcf…`, `5d67c8e1…`, `061309c7…`); opis skilla w sesji: „stan 2026-09-29, wnioski 1–110”. Punkt 10 usunięty ze `STATUS.md`.
