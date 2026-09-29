---
id: 000
tytul: Wdrożenie tablicy zadań — reguła w CLAUDE.md i sposób pracy orkiestratora
typ: dokumentacja
status: zrobione
zlecil: cowork
decyzja_uzytkownika: "2026-09-29: tablica zadań w katalogu zadania/, Cowork pisze tylko w zadania/"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, krótko"
---

# 000 — Wdrożenie tablicy zadań

## Po co

Użytkownik zatwierdził tablicę zadań (`zadania/README.md`). Żeby każda przyszła sesja na serwerze o niej wiedziała,
musi być o niej reguła w `CLAUDE.md`. Cowork nie może edytować `CLAUDE.md`.

## Zakres

1. Dopisać do `CLAUDE.md` kolejną regułę (następny numer po ostatniej). Treść w skrócie:
   - tablica zadań to `zadania/`, zasady w `zadania/README.md`;
   - na polecenie „wykonaj zadania z tablicy” sesja staje się orkiestratorem;
   - orkiestrator bierze zadania `nowe` w kolejności numerów, z uwzględnieniem `zalezy_od`;
   - zadania `badawcze`, `dziennik` i `konto` bez zapisanej decyzji użytkownika przechodzą w `czeka_na_decyzje`;
   - scala tylko na dowodach;
   - Cowork pisze wyłącznie w `zadania/`.
2. Dopisać `zadania/` do sekcji o strukturze repo lub dokumentacji tam, gdzie repo ją opisuje (np. `docs/rag/10`).
3. Krótka notka w `STATUS.md`: „Tablica zadań od 2026-09-29”.

## Czego NIE robić

- Nie zmieniać innych reguł.
- Nie uruchamiać jeszcze automatu według harmonogramu. Najpierw ręcznie, potem izolacja (002), dopiero potem ewentualny
  harmonogram, za decyzją użytkownika.

## Kryteria odbioru (dowody)

- Diff `CLAUDE.md` z nową regułą.
- Przechodzi `py -m pytest` (sprawdzenie, że nic się nie zepsuło).
- Status tego pliku zmieniony na `zrobione` z sekcją **Wynik**.

## Wynik

- **Co zrobiono:** `CLAUDE.md` — zasada 21 (tablica zadań) i wiersz `zadania/` w „Strukturze projektu”; pełne brzmienie
  zasady 21 w `docs/rag/08_zasady_pelne_brzmienie.md` (ta sama numeracja, jak wymaga CLAUDE.md); sekcja „Tablica zadań”
  w `docs/rag/10_preferencje_uzytkownika.md`; notka „Tablica zadań od 2026-09-29” na końcu `STATUS.md`. Innych reguł nie
  zmieniano; harmonogramu nie uruchomiono.
- **Commity i gałęzie:** gałąź `zadanie-000-tablica`, scalona do `master` (hash w `git log --grep='zadanie 000'`).
- **Dowody:** `git diff master~1 -- CLAUDE.md`; `OMP_NUM_THREADS=4 py -m pytest -q` → 1768 passed, 2 skipped (250 s,
  kod wyjścia 0, 2026-09-29).
- **Co zostało:** nic w tym zadaniu. Kolejne kroki według decyzji: 002 (izolacja), harmonogram osobną decyzją.
