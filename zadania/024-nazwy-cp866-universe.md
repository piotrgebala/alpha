---
id: 024
tytul: Nazwy plików w data/raw/universe_full w kodowaniu cp866 — naprawa nazw bez zmiany treści
typ: naprawa
status: zrobione
zlecil: orkiestrator
decyzja_uzytkownika: "2026-09-29: „Wykonaj” (zgoda na dopisanie luk danych z LP1 i wykonanie zadań z tablicy)"
utworzono: 2026-09-29
zalezy_od: [017]
budzet: "Opus, 1 wykonawca"
---

# 024 — Nazwy plików koszyka w złym kodowaniu

## Po co

Runda LP1 (zadanie 017, `runs/2026-09-29_lp1-likwidacja-progi-binance/README.md`) znalazła na serwerze 4 pliki
w `data/raw/universe_full` z nazwą w cp866 zamiast UTF-8. Skład koszyka dostaje przez to zniekształcony symbol
(币安人生), który w LP1 wypada z kroku 2 na 1 miesiąc. Inne skrypty czytające koszyk mogą gubić go tak samo.

## Zakres

1. Wypisać pliki w `data/raw/universe_full` (i w innych katalogach `data/raw`, jeśli dotyczy) z nazwą spoza UTF-8
   albo zniekształconą; dla każdego: obecna nazwa (bajty), poprawna nazwa, sha256 treści.
2. Sprawdzić, czy plik o poprawnej nazwie już istnieje (duplikat) i czy treść jest ta sama.
3. Skrypt naprawy z trybem `--sprawdz` (tylko plan) i `--wykonaj` (zmiana nazw, bez zmiany treści), z testem na
   sztucznym katalogu. Zmianę nazw w katalogu głównym repo wykonuje orkiestrator po przeglądzie.
4. Wypisać skrypty, które czytają te pliki (także zamrożone rundy), i czy zmiana może zmienić ich wynik na serwerze.

## Czego NIE robić

- Nie zmieniać treści plików, nie pobierać ich ponownie, nie usuwać.
- Nie pisać w `data/raw` katalogu głównego repo (tylko odczyt); nie dotykać klonu dziennika ani kodu dziennika.

## Kryteria odbioru (dowody)

- Plan zmian (stara → nowa nazwa, sha256 treści), testy zielone, powtarzalna komenda.
- Po wykonaniu przez orkiestratora: te same sumy sha256 treści, poprawne nazwy, lista skryptów, których to dotyczy.

## Wynik

- **Zrobione 2026-09-29.** Narzędzie `tools/napraw_nazwy_cp866.py` (`--sprawdz` / `--wykonaj`, test
  `tests/test_napraw_nazwy_cp866.py`); dowody wykonawcy w `zadania/024-dowody/` (plan, próba na kopii, druga droga,
  lista skryptów). Gałąź `zadanie-024-nazwy-cp866-universe` (`5c4aaf7`), merge do master `9e78436`. pełny `pytest -q` po scaleniu 019 + 020 + 024 (master `9e78436`, OMP_NUM_THREADS=4): 2 065 passed, 2 skipped, kod 0, 256 s; `ruff check .` czysto; `black --check .` — jedyny plik do przeformatowania to `data/fetch_ohlcv.py` (sprzed zadań, łańcuch dziennika, czeka na decyzję użytkownika).
- **Zmiana nazw (orkiestrator, 2026-09-29 ~12:05 UTC):** 20 plików w `data/raw/universe_full` (6),
  `data/raw/universe_2026q3` (8) i `data/raw/live` (6); treść bez zmian. Log z komendami:
  `zadania/024-dowody/wykonanie_2026-09-29.txt` (przed: DO_ZMIANY 20; po: POPRAWNA 20, DO_ZMIANY 0).
- **Druga droga (niezależna od narzędzia):** posortowana lista sha256 treści 3 202 plików trzech katalogów przed i po
  jest identyczna (`f4342855…`). Testy czytające te katalogi po zmianie: `tests/test_rebalance_premium.py`
  + `tests/test_napraw_nazwy_cp866.py` — 33 passed.
- **Dziennik nie jest dotknięty:** klon `~/alpha-dziennik/data/raw/live` (tylko odczyt) ma 6 nazw spoza ASCII i wszystkie
  są poprawne; to osobny katalog (inny i-węzeł). Poprawka niepotrzebna. `data/raw/live` w katalogu głównym włączono do
  naprawy po tym sprawdzeniu: ma teraz te same nazwy co klon dziennika i Windows.
- **Zostało (decyzje użytkownika, poza tym zadaniem):** TP1 i LP1 uruchomione ponownie mogą dać trochę inne liczby
  (1 moneta × 1 miesiąc, `zadania/024-dowody/skrypty.txt` sekcja C); zapisanych wyników nie przeliczano.
  `mark_1d.parquet` i `oi_daily_full.parquet` nie mają 币安人生USDT (kolektor pytał o zniekształcony symbol) —
  uzupełnienie to osobne zadanie `zbieranie_danych`.
