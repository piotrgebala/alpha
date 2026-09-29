---
id: 002
tytul: Hook audytowy wykonawców i plan izolacji na serwerze
typ: infra
status: w_toku
zlecil: cowork
decyzja_uzytkownika: "2026-09-29: kolejność tablica → izolacja → ewentualny harmonogram"
utworzono: 2026-09-29
zalezy_od: [000]
budzet: "Sonnet do kodu, Opus do przeglądu"
---

# 002 — Hook audytowy i izolacja wykonawców

## Po co

Wnioski z incydentu OpenAI/Hugging Face (lipiec 2026) i raportów OpenAI z 17.09:

- agenci znajdują boczne kanały w każdym wspólnym zasobie, do którego mogą pisać;
- przy przeszkodzie szukają obejścia (publiczne serwisy, zmyślone dane).

Zanim tablica zacznie działać bez nadzoru, potrzebujemy widoczności i granic.

## Zakres

1. **Hook audytowy** Claude Code (`PreToolUse` lub `PostToolUse`, obok istniejącego strażnika kontekstu
   `tools/straznik_kontekstu.py`). Zapisuje do `~/.clas5_audyt/RRRR-MM-DD.jsonl` i oznacza:
   - polecenia sieciowe (`curl`, `wget`, `git push`, `pip install`, `python -c` z `requests`/`urllib`) do hostów spoza
     listy dozwolonych w pliku konfiguracyjnym;
   - zapisy poza bieżącym worktree i poza `runs/`/`data/`;
   - odczyty `~/.ssh`, plików `.env`, kluczy i poświadczeń.

   Tryb pierwszy: **tylko oznacza, nie blokuje**. Blokowanie po tygodniu obserwacji, za decyzją użytkownika.
2. **Testy** hooka bez sieci (przypadki dozwolone i oznaczane).
3. **Plan izolacji**, tylko dokument (`docs/rag/13_izolacja_wykonawcow.md`):
   - osobny użytkownik systemu dla wykonawców, bez dostępu do `~/.ssh`, kluczy i katalogów danych kolektorów;
   - uprawnienia do katalogów;
   - lista dozwolonych hostów;
   - co wymaga `sudo`, czyli co musi zrobić użytkownik.

## Czego NIE robić

- Nie zmieniać uprawnień systemowych ani użytkowników (wymaga `sudo`, a więc decyzji i rąk użytkownika).
- Nie blokować niczego w pierwszej wersji.
- Nie ruszać kolektorów, dziennika ani crona.

## Kryteria odbioru (dowody)

- Testy hooka przechodzą.
- Przykładowy plik audytu z jednej sesji.
- `security-review` i `engineering:code-review` (bramki).
- Dokument planu izolacji z listą kroków dla użytkownika.

## Wynik

(dopisuje orkiestrator)
