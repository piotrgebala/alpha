---
id: 016
tytul: Funding drugą drogą — dzienna suma × waga (nasze silniki) wobec rozliczenia po rozliczeniu (wzór freqtrade), 0 wariantów
typ: przeglad
status: nowe
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

(dopisuje orkiestrator)
