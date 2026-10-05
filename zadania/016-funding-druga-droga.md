---
id: 016
tytul: Funding drugą drogą — dzienna suma × waga (nasze silniki) wobec rozliczenia po rozliczeniu (wzór freqtrade), 0 wariantów
typ: przeglad
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „tak wrzuć na tablicę z zadaniami” (po przeglądzie bibliotek)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus do metodologii, Sonnet do mechaniki"
---

# 016 — Funding drugą drogą

## Po co

Funding to opłata co 8 h (u części monet co 4 h albo 1 h) między longami a shortami. Nasze silniki liczą ją
w uproszczeniu: dzienna suma stawek × waga pozycji (`backtest/ts_momentum.py:12`, `:105`;
`backtest/xs_momentum.py:31-39`). freqtrade liczy każde rozliczenie osobno: stawka × cena mark × ilość w chwili
rozliczenia (`freqtrade/exchange/exchange.py:3946` `calculate_funding_fees`; łączenie stawek z ceną mark:
`combine_funding_and_mark`, l. 3902). Sprawdzamy drugą drogą, czy uproszczenie nie przesuwa kosztu fundingu nóg
dziennika. Źródło: przegląd bibliotek z 2026-09-29.

## Zakres

- Historia od 2021-01-01 (zasada 20), dane z repo (`data/raw/universe_full`, funding per rozliczenie), bez sieci.
- Dla TS1 (7 faz, reguła jak w dzienniku, 2×) i X1 policzyć samą składową funding na dwa sposoby:
  - (a) jak silnik: Σ po dniach w · f_dzień;
  - (b) jak freqtrade: każde rozliczenie osobno, nominał pozycji w chwili rozliczenia (waga dryfuje z ceną).
    Cena zamknięcia świecy 1h lub 4h zastępuje cenę mark; zapisać to jako przybliżenie.
- Sprawdzić trzy miejsca ryzyka:
  1. rozliczenie dokładnie w chwili wejścia i wyjścia (00:00 UTC): liczone raz, dwa razy czy wcale;
  2. monety z interwałem fundingu 4 h albo 1 h zamiast 8 h;
  3. brakujące stawki (NaN zamieniane na 0).
- Podać różnicę (b) − (a) w %/rok kapitału z przedziałem (bootstrap blokowy po tygodniach), z medianą i zakresem per
  rok i per moneta. Porównać ją z kosztem wykonania z KO1 (0,8 / 1,5 / 3,3 %/rok; wniosek 99).
- Katalog `runs/RRRR-MM-DD_<id>-funding-druga-droga/` z `raw_output.txt`, 0 wariantów, wiersz w `runs/INDEX.md`.

## Czego NIE robić

- Nie drukować zwrotu netto, t ani Sharpe'a strategii. Tylko składowa funding i różnica, bo to nie jest odczyt
  przewagi.
- Nie zaglądać w wyniki dziennika (`dziennik/*.csv`); zob. 014.
- Nie poprawiać silników w tym zadaniu. `ts_momentum` i `xs_momentum` są w łańcuchu importów dziennika, więc zmiana to
  Poprawka N i decyzja użytkownika. Jeśli różnica jest istotna, opisać ją w Wyniku z propozycją poprawki.
- Nie importować freqtrade (zasada 8; licencja GPL-3.0). Wzór przepisać po swojemu, z testem.

## Kryteria odbioru (dowody)

- Test jednostkowy: na sztucznym przykładzie (1 moneta, 3 rozliczenia, znana ścieżka ceny) obie drogi dają liczbę
  policzoną ręcznie w teście.
- `raw_output.txt`, powtarzalna komenda, hash commita. Różnicę %/rok przeliczyć drugim sposobem (np. pandas wobec numpy).
- Bramki 16a–c; skille `clas5-quant`, `clas5-runda`, `data:validate-data`, `data:statistical-analysis`.
- Wniosek w jednym zdaniu: czy uproszczenie zmienia koszt fundingu o wielkość porównywalną z kosztami z KO1.

## Wynik

- **Zrobione 2026-09-29.** Runda FD1: `runs/2026-09-29_fd1-funding-druga-droga/` (README, `raw_output.txt`
  sha256 `e1640941…`). Kod: `backtest/funding_settlement.py`, `backtest/run_fd1_funding.py` (zamrożony), testy
  `tests/test_funding_settlement.py`. Wniosek 112 w `runs/INDEX.md`, wiersz 60 w `runs/odczyty_historii.csv`, zdanie
  w `STATUS.md`. Gałąź `zadanie-016-funding-druga-droga` (HEAD `2badf9e`), scalona do master (`ec0afa5`).
- **Wynik:** (b) − (a) w %/rok kapitału nogi, 95 % z bootstrapu po tygodniach. **TS1: −0,004 [−0,042; +0,033]** —
  pomijalne wobec kosztu wykonania KO1 (0,8 %/rok). **X1 z pre-rejestracji: +23,56 [−0,40; +71,32]** — czerwona flaga:
  to ruina pozycji o stałej ilości (MYX, wrzesień 2025, cena ×12 w 3 dni), nie funding; reguła z pre-rejestracji daje
  „nierozstrzygnięte”. X1 na wagach silnika (diagnostyka po wyniku): −0,166 [−0,620; +0,221]. Trzy miejsca ryzyka:
  rozliczenie 00:00 liczone raz, ale od nowej pozycji (netto TS1 +0,006, X1 +0,015 %/rok); interwały 4 h / 1 h
  poprawnie sumowane (kontrola zerowa 0 do 1e-17); NaN → 0 nie występuje, dni dziur to BRAK DANYCH (wpływ
  ≤ 0,001 %/rok). **Poprawki wzoru w silnikach nie proponować.** Bramki: 16a Caveats, 16b spełniona, 16c Approve.
- **Dowody (sprawdził orkiestrator):** przebieg odtworzony — liczby identyczne, różnią się tylko czasy przebiegu
  (linie 53 i 137); druga droga (numpy wobec pandas, „dolarowo”) w `raw_output.txt` zgodna do 1e-14; łańcuch importów
  dziennika nietknięty; `runs/ZAMROZONE.txt` tylko dopisany. Pełny pytest na master po scaleniu: 1 946 passed, 2 skipped, kod 0.
- **Zostało:** do decyzji użytkownika model pozycji X1 — silnik co dzień przywraca wagi, a dziennik handluje raz
  w tygodniu (wniosek 112). Źródła freqtrade wykonawca nie czytał (brak klonu i sieci); wzór przepisany z opisu
  zadania. Ceny w ciągu dnia dla altów z interpolacji (BRAK DANYCH 1 h poza BTC); zamiast ceny mark cena ostatnia.
