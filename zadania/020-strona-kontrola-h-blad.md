---
id: 020
tytul: Strona dziennika — kontrola (h): alarm, gdy ostatnia linia `przebiegi.log` ma pole z „BŁĄD”
typ: infra
status: w_toku
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

(dopisuje orkiestrator)
