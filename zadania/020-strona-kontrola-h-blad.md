---
id: 020
tytul: Strona dziennika — kontrola (h): alarm, gdy ostatnia linia `przebiegi.log` ma pole z „BŁĄD”
typ: infra
status: do_przegladu
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Wykonaj wszystkie 3 punkty” (wpis pozycji backlogu z STATUS.md §17, ETAP 6, na tablicę)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Sonnet albo Opus medium, 1 wykonawca"
---

# 020 — Kontrola (h) na stronie dziennika

## Po co

Skrypt strony `tools/strona_dziennika.py` sprawdza kontrole (a)–(g). Błąd źródła pobocznego (np. X1, stan rynku, F&G,
transakcje) zapisuje się w polu linii `przebiegi.log`, ale nie wywołuje „UWAGA” w powiadomieniu. Kontrola (h) ma to
wychwycić. Pozycja z backlogu `STATUS.md` §17, ETAP 6.

## Zakres

1. W `checks()` dopisać (h): pole ostatniego przebiegu zawierające „BŁĄD” → „(h) <pole>: <treść>”. Pola carry
   pomijać — obsługuje je już (f).
2. Testy: linia bez błędu, linia z błędem X1, z błędem F&G, wieloliniowy błąd doklejony przez `log_records`, błąd carry
   (ma dać tylko (f), bez (h)). Wszystkie linie z obecnego `dziennik/przebiegi.log` muszą dalej dawać zero alarmów.
3. Zmiana skryptu zmienia jego sumę SHA-256, więc po scaleniu trzeba odświeżyć instrukcję rutyny: przebudować
   `tools/rutyna_dziennika.md` przez `tools/pulpit_clas5.py` i wstawić ją do rutyny `trig_013XEDboNXSkb6CF17K1eSGf`
   (rutyna założona przez agenta, więc `update_trigger` jest możliwe; inaczej wkleja użytkownik). Nie w oknie
   06:30–06:50 UTC, gdy rutyna działa.

## Czego NIE robić

- Nie zmieniać kontroli (a)–(g), formatu `stan.json` ani kodu dziennika (`backtest/live_journal.py` i jego importy).
- Nie zmieniać, co i jak dziennik zapisuje w `przebiegi.log`.

## Kryteria odbioru (dowody)

- `py -m pytest -q` zielony, w tym `tests/test_strona_dziennika.py` z nowymi przypadkami.
- Wydruk `python3 tools/strona_dziennika.py <klon> stan.json` na obecnym `master`: ostatnia linia bez „UWAGA”.
- Nowa suma SHA-256 w `tools/rutyna_dziennika.md` = suma skryptu; potwierdzenie, że rutyna ma nową instrukcję
  (odczyt `get_trigger` albo słowo użytkownika) i następny przebieg rutyny zakończony „Dziennik odświeżony”.

## Wynik

- **Kod scalony 2026-09-29; instrukcja rutyny czeka na wklejenie przez użytkownika.** Kontrola (h) w
  `tools/strona_dziennika.py::checks()`, testy `tests/test_strona_dziennika.py`, instrukcja przebudowana
  `tools/rutyna_dziennika.md` (suma skryptu `1a9934a2…40f5`; `tests/test_pulpit_clas5.py` zielony na master).
- Gałąź `zadanie-020-strona-kontrola-h-blad` (`3a61a82`), merge do master `1dfb400`.
- Dowody: pełny `pytest -q` po scaleniu 019 + 020 + 024 (master `9e78436`, OMP_NUM_THREADS=4): 2 065 passed, 2 skipped, kod 0, 256 s; `ruff check .` czysto; `black --check .` — jedyny plik do przeformatowania to `data/fetch_ohlcv.py` (sprzed zadań, łańcuch dziennika, czeka na decyzję użytkownika).
- Punkt 3 (podmiana instrukcji w rutynie `trig_013XEDboNXSkb6CF17K1eSGf`) **nie wykonany przez agenta**: w sesji
  wykonawcy nie ma narzędzia RemoteTrigger (sprawdzone 2026-09-29 11:57 UTC; rutyna nietknięta). W głównej sesji
  podmiana wymagałaby przepisania całej konfiguracji (~120 KB, prompty Cowork) — ryzyko przekłamań, więc nie.
- **Zostało:** użytkownik wkleja w Cowork całą treść `tools/rutyna_dziennika.md` jako instrukcję rutyny (nie w oknie
  06:30–06:50 UTC). Potem orkiestrator sprawdza, że przebieg rutyny kończy się „Dziennik odświeżony”, i zmienia status
  na `zrobione`. Do tego czasu rutyna działa na starej wersji skryptu (bez (h)).
- **2026-09-30 ~05:45 UTC:** użytkownik: „rutyna dziennika dodana” — nowa instrukcja w rutynie (słowo użytkownika
  wystarcza według kryteriów odbioru). Zostało: przebieg 06:30 UTC zakończony „Dziennik odświeżony” — sprawdzić
  `RemoteTrigger list_runs` / `get_run_log` w następnej sesji orkiestratora i wtedy zmienić status na `zrobione`.
