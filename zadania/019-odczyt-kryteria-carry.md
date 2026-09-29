---
id: 019
tytul: Odczyt dziennika — kryteria carry (a)–(c) z Poprawki 12 w `backtest/odczyt_dziennika.py`, przed odczytem 1
typ: infra
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Wykonaj wszystkie 3 punkty” (wpis pozycji backlogu z STATUS.md §17, ETAP 6, na tablicę)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, 1 wykonawca"
---

# 019 — Kryteria carry w skrypcie odczytu

## Po co

Poprawka 12 (`dziennik/README.md`, „Kryterium odczytu po ~3 miesiącach”) zapisała z góry trzy kryteria mechaniki nogi
carry: (a) terminowość, (b) kompletność, (c) zgodność z giełdą. Skrypt odczytu `backtest/odczyt_dziennika.py` liczy dziś
tylko kryteria 1–4, 4b i próg obalenia nóg TS1/CP1/R1/X1. Bez tego zadania odczyt 1 (wynik do 2026-12-24, odczyt dzień
później) nie ma dla carry reguł w kodzie. Pozycja z backlogu `STATUS.md` §17, ETAP 6.

## Zakres

1. Dopisać do wydruku odczytu sekcję „Carry COIN-M (Poprawka 12)” z kryteriami **dokładnie w brzmieniu z README**
   (progi: (a) ≤ 5 % przebiegów z kłopotem od 2026-09-30; (b) `komplet = True` w ≥ 95 % dni od 2026-09-29, lista dni
   z `False`; (c) ponowne pobranie historii funding COIN-M od 2026-09-29, przeliczenie `journal_carry.carry_rows`,
   zgodność z plikiem do 1e-9 i zero pól „carry zmiany” w `przebiegi.log`).
2. (a) i (b) liczyć tymi samymi definicjami co strona: `tools/strona_dziennika.carry_state` (tak jak kryteria 1–4
   biorą definicje z `build_state`). Nie powielać logiki.
3. (c) jako osobny, jawny krok z siecią (flaga, np. `--carry-sprawdz-gielde`), bo odczyt bez flagi ma zostać czystym
   odczytem plików. Pobranie przez istniejącą funkcję (`data/fetch_live.fetch_coinm_funding_safe`). Brak sieci lub
   danych → „BRAK DANYCH”, nie „zgodne”.
4. Wynik carry wyłącznie opisowo (`netto_skum` i ta sama suma w skali roku), bez werdyktu i bez progu obalenia.
   Niespełnione (a)–(c) opisane jako błąd mechaniki do wyjaśnienia.
5. Testy jednostkowe bez sieci (atrapa pobrania), w tym przypadki brzegowe: brak `carry_wyniki.csv`, dzień
   z `komplet = False`, pole „carry zmiany” w logu, różnica 1e-8 w przeliczeniu.

## Czego NIE robić

- Nie zmieniać progów, dat ani brzmienia kryteriów z README — tylko je zakodować. Rozbieżność README ↔ kod zgłosić,
  nie rozstrzygać samemu.
- Nie ruszać kodu, z którego korzysta dziennik (`live_journal` i jego importy, w tym `journal_carry`, `carry_product`,
  `fetch_live`) — tylko import funkcji. Zmiana tamtych plików = Poprawka N i decyzja użytkownika.
- Nie uruchamiać odczytu wiążącego; wolno podgląd („ZA WCZEŚNIE — tylko podgląd”).

## Kryteria odbioru (dowody)

- `py -m pytest -q` zielony (liczba testów przed i po), nowe testy w `tests/`.
- Wydruk podglądu `py -m backtest.odczyt_dziennika` z sekcją carry (zapis do logu w gałęzi zadania).
- Test pilnujący, że progi carry w skrypcie = progi w `dziennik/README.md` (jak test zgodności tabeli `LEGS`).
- `ruff` + `black --check` na dotkniętych plikach.

## Wynik

- **Zrobione 2026-09-29.** Kryterium 6 (carry COIN-M, (a)–(c) z Poprawki 12) w `backtest/odczyt_dziennika.py`;
  krok (c) z siecią tylko na żądanie (`--carry-sprawdz-gielde`). Kod dziennika bez zmian.
- Gałąź `zadanie-019-odczyt-kryteria-carry` (`ea10b72`), merge do master `dee873d`.
- Dowody: testy `tests/test_odczyt_dziennika_carry.py`, w tym `test_carry_criteria_wording_and_thresholds_match_readme`
  (progi skryptu = `dziennik/README.md`); podgląd bez sieci `zadania/logi/019-podglad-odczytu.txt`; pełny `pytest -q` po scaleniu 019 + 020 + 024 (master `9e78436`, OMP_NUM_THREADS=4): 2 065 passed, 2 skipped, kod 0, 256 s; `ruff check .` czysto; `black --check .` — jedyny plik do przeformatowania to `data/fetch_ohlcv.py` (sprzed zadań, łańcuch dziennika, czeka na decyzję użytkownika).
- **Zostało (decyzja użytkownika):** czy dopisać `--carry-sprawdz-gielde` do komend odczytów wiążących
  w `dziennik/README.md:598–600`.
