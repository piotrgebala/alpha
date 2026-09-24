# LQ1 — trend tygodniowy (TS1) z likwidacją przy 3× na izolowanym depozycie (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „wykonaj wszystkie
> 3 punkty” (punkt 1). **POPRAWKA pomiaru TS1, nie wariant** — reguła bez zmian; zmienia się
> tylko rozliczenie: sposób handlu użytkownika (dźwignia 3× na części kapitału) dodaje ryzyko
> likwidacji pojedynczych pozycji, którego TS1 nie liczyło (cache miał tylko zamknięcia).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Każda moneta w trendzie dostaje depozyt równy jednej trzeciej swojej pozycji (dźwignia 3×).
Jeśli w ciągu tygodnia cena pójdzie przeciw pozycji o ok. 32 %, giełda ją likwiduje i depozyt
przepada. Liczymy TS1 jeszcze raz, z prawdziwymi dziennymi maksimami i minimami, żeby zobaczyć,
ile to kosztuje.

## Metadane

- Branch `lq1-likwidacje`. Nowe dane: `data/fetch_universe_ohlc.py` → `data/raw/universe_ohlc/
  ohlc_1d.parquet` (archiwum klines 1d, miesiące członkostwa top-20 + miesiąc wcześniej):
  48 186 wierszy, 119 symboli, 0 brakujących plików.
- Kod: `backtest/ts_momentum.py::phase_returns_liq` (+ parametr `liq` w `portfolio`; testy:
  równoważność z `phase_returns` bez likwidacji, likwidacja longa/shorta, strata = depozyt
  w `hypothesis`), `backtest/run_ts_liq_lq1.py` (na `runs/ZAMROZONE.txt`),
  `tests/test_fetch_universe_ohlc.py`. Komenda: `PYTHONUTF8=1 py -m backtest.run_ts_liq_lq1`.

## Pre-rejestracja

- **Model likwidacji (z góry):** dźwignia 3, MMR 1 % (konserwatywnie dla altów; BTC ma 0,4 %)
  → próg 32,3 % ruchu przeciw pozycji od ceny wejścia (tygodniowe formowanie), liczony z dziennych
  high/low ceny ostatniej (knoty — konserwatywnie wobec ceny mark); strata = cały depozyt |w|/3,
  pozycja wyłączona do następnego formowania; funding tylko dla żywych pozycji.
- **Kryterium:** jak TS1 dla TS1 z likwidacją (t_neff > 1,96 ORAZ > q97,5 H0 liczonego tym samym
  silnikiem z likwidacją; NEGATYWNY: CI < 0). Opisowo: różnica parowana z TS1 bez likwidacji,
  liczba likwidacji, depozyt.
- **Oczekiwanie:** przy ~2 % ekspozycji na monetę i tygodniowych ruchach > 30 % w ~3–4 %
  pozycji-tygodni różnica rzędu −1 do −3 %/rok.

---

_(sekcje poniżej po przebiegu)_
