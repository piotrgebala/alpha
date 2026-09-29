---
id: 021
tytul: Kolektor likwidacji Binance — sprawdzanie zakresu czasu T przy zapisie (dziś sprawdza je dopiero indeks/kopia)
typ: naprawa
status: nowe
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

(dopisuje orkiestrator)
