---
id: 023
tytul: Porządki formatu — `black --check .` czerwony na 15 starych plikach (9 zamrożonych poza `extend-exclude`)
typ: naprawa
status: w_toku
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Wykonaj wszystkie 3 punkty” (wpis pozycji backlogu z STATUS.md na tablicę)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Sonnet albo Opus medium, 1 wykonawca"
---

# 023 — `black --check .` na zielono

## Po co

`py -m black --check .` (komenda z `CLAUDE.md`) jest czerwony na 15 starych plikach, więc nie odróżnia nowych
błędów formatu od starych. Pozycja z backlogu w nagłówku `STATUS.md`.

## Zakres

1. Uruchomić `py -m black --check .` i wypisać pliki z błędem.
2. **Zamrożone** (`runs/ZAMROZONE.txt`, `py tools/frozen_guard.py lista`): nie formatować — dopisać do `extend-exclude`
   w `pyproject.toml` (sekcje black i ruff, tak jak pozostałe zamrożone).
3. **Pliki, z których korzysta dziennik** (lista w `CLAUDE.md`, „Dziennik papierowy”: `backtest/live_journal.py` i jego
   importy, `data/fetch_live.py` i jego importy): **nie formatować** — zmiana tych plików wymaga decyzji użytkownika
   i Poprawki N. Wypisać je w wyniku jako osobną pozycję do decyzji.
4. Pozostałe: `black` bez żadnej zmiany logiki; osobny commit „tylko format”.

## Czego NIE robić

- Nie edytować zamrożonych skryptów (hook `tools/frozen_guard.py` i tak odmówi).
- Nie łączyć formatowania ze zmianami treści.

## Kryteria odbioru (dowody)

- `py -m black --check .` i `py -m ruff check .` zielone (albo lista plików z punktu 3 jako jedyny wyjątek).
- `py -m pytest -q` zielony, ta sama liczba testów co przed zmianą.
- `git diff --stat` commitu formatu; `git diff -w` bez zmian logiki (przegląd 16c jednym zdaniem).

## Wynik

(dopisuje orkiestrator)
