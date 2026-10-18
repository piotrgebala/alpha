---
id: 021
tytul: Kolektor likwidacji Binance — sprawdzanie zakresu czasu T przy zapisie (dziś sprawdza je dopiero indeks/kopia)
typ: naprawa
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Wykonaj wszystkie 3 punkty” (wpis pozycji backlogu z STATUS.md §17, ETAP 6, na tablicę)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Sonnet albo Opus medium, 1 wykonawca"
---

# 021 — Zakres T w kolektorze Binance

## Po co

`data/collect_liquidations.py` (LK0) rozkłada rekordy na pliki dzienne według czasu zdarzenia `E` i nie sprawdza
czasu transakcji `T`. Rekord z `T` spoza rozsądnego zakresu wychwytuje dopiero dzienny indeks lub kopia
(`data/liquidation_index.py`, `data/liquidation_backup.py`). Błąd powinien być widać przy zapisie, a nie dzień później.
Pozycja z backlogu `STATUS.md` §17, ETAP 6.

## Zakres

1. Przeczytać, jak indeks i kopia sprawdzają zakres `T`, i przy zapisie zastosować **tę samą** regułę (jedna funkcja
   wspólna, bez nowego progu).
2. Rekord poza zakresem **zapisać bez zmian** (nie gubić danych), ale zliczyć go w statusie kolektora i w logu.
   Sprawdzić też kolektor Bybit (`collect_liquidations_bybit.py`, klucz `T`): ta sama funkcja, jeśli pasuje.
3. Testy bez sieci: rekord poprawny, `T` z przyszłości, `T` z poprzedniego dnia przy `E` po północy, brak `T`.
4. Wdrożenie na serwerze: restart kolektora poza oknem 02:00–03:00 UTC (dziennik i kopia). Przerwę zanotować
   w wyniku (od–do, UTC), bo w danych będzie luka.

## Czego NIE robić

- Nie zmieniać formatu plików `~/likwidacje` ani manifestu kopii; nie przepisywać zebranych danych.
- Nie dotykać zamrożonych skryptów sond LK0/LB0/LH0 (`runs/ZAMROZONE.txt`).
- Bez nowych adresów sieciowych.

## Kryteria odbioru (dowody)

- `py -m pytest -q` zielony; nowe testy.
- Status kolektora po restarcie pokazuje licznik rekordów poza zakresem (0 albo liczba z przykładami).
- Następny poranny strażnik kopii (`trig_011sTHk1bPUsRtjbP4BSru9L`) kończy się „Kopia likwidacji OK”.

## Wynik

- **Kod scalony 2026-09-29, wdrożenie czeka na użytkownika.** Gałąź `zadanie-021-kolektor-binance-zakres-t`
  (`d9e8c8e`, `0431475`), scalona do master (`9d3ac8c`, wypchnięte). Nowy `data/liquidation_time.py` (jedna reguła T:
  2019-01-01…2100-01-01, przeniesiona z `data/liquidation_index.py:193-200`), używana przez indeks, kolektor Binance
  i Bybit. Rekord z T poza zakresem zapisany bez zmian, liczony w `status.json` (`t_out_of_range`) i w logu.
- **Dowody:** 31 nowych testów, 7/7 mutacji wykrytych; na 6 zamkniętych dniach (Binance 141 349, Bybit 27 211 rekordów)
  0 rekordów poza zakresem, indeks nowym kodem bajt w bajt taki sam jak stary i jak w kopii. Pełny pytest na master po
  scaleniu: 1 977 passed, 2 skipped, kod 0. Łańcuch dziennika i zamrożone nietknięte.
- **Zostało:** (1) **restart kolektora LK0 z nowym kodem** — próba orkiestratora zablokowana przez tryb auto (ingerencja
  w działający proces), więc robi go użytkownik (procedura niżej); przerwę od–do wpisać tutaj. (2) Poranny strażnik kopii
  („Kopia likwidacji OK”). (3) Rekordy bez T nadal pomijane (zapis zmieniłby format — decyzja użytkownika); Bybit bez
  licznika „zapisane bez zmian”. (4) Wykonawca znalazł niestabilny test `tests/test_audyt_hook.py` (hypothesis: znak
  `\ud800` → `UnicodeEncodeError` w `os.path.realpath` w `tools/audyt_hook.py`) — do osobnej naprawy.
- **Procedura restartu (z `~/alpha`, poza 02:00–03:00 UTC i poza minutami :x4–:x5, :x9–:x0):** zatrzymać pid kolektora
  `.venv/bin/python -m data.collect_liquidations --dir /home/dantey1/likwidacje` (`kill -INT`, po 15 s `kill -TERM`)
  i od razu uruchomić `bash tools/likwidacje.sh` z `~/alpha` (cron `*/5` z `~/alpha-dziennik` ma stary kod do 02:30).
  Sprawdzić: cwd nowego procesu = `/home/dantey1/alpha`, `--status` pokazuje „T poza zakresem 0”.
- **2026-10-05, zamknięcie (orkiestrator):** restart LK0 zrobił użytkownik (komenda z procedury). Nowy proces pid 1604604
  od 2026-10-05T17:40:19Z, cwd `/home/dantey1/alpha`, `--status`: „T poza zakresem 0 (zapisane bez zmian)”, rozłączeń 0,
  błąd None; `kolektor.log` 17:40:20 „połączono”. Przerwa w zbieraniu ≈ 17:40:00–17:40:20 UTC (≤ 20 s). Punkty (3) rekordy
  bez T / licznik Bybit i (4) niestabilny test `tests/test_audyt_hook.py` zostają poza tym zadaniem (osobne naprawy).
