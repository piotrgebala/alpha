# LQ1 — trend tygodniowy (TS1) z likwidacją przy 3× na izolowanym depozycie (2026-09-24)

> **STATUS: ZAMKNIĘTA — likwidacje przy 3× kosztują trend −3,6 %/rok [−5,8; −1,4] (t −3,16):**
> TS1 z likwidacją +11,3 %/rok [−5,3; +27,8], t 1,34 — NIEROZSTRZYGNIĘTY; 4,75 % pozycji-tygodni
> likwidowanych. Opisowo przy 2×: +13,2 %/rok. Pre-rejestracja `5dceb16`. Walidacja: **READY**;
> przegląd: **Approve**.
> Poprzednio: **PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „wykonaj wszystkie
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

## Wynik

`raw_output.txt` (105 s), 1 969 dni, 7 faz; pokrycie high/low u członków 99,9 %.

| wersja | zwrot netto [CI 95 %] | t_neff | CAGR / max obsunięcie |
|---|---|---|---|
| TS1 bez likwidacji | +14,8 %/rok [−1,7; +31,3] | 1,76 | +13,8 % / 17,9 % |
| **TS1 z likwidacją 3× (izolowany depozyt)** | **+11,3 %/rok [−5,3; +27,8]** | **1,34** | +9,8 % / 19,2 % |
| różnica (koszt likwidacji) | **−3,6 %/rok [−5,8; −1,4]** | −3,16 | — |
| opisowo: likwidacja przy 2× (próg 49 %) | +13,2 %/rok | 1,55 | — |

Likwidacji: 1 875 w 7 fazach (≈ 268 na fazę, ≈ 4,75 % pozycji-tygodni). H0 z likwidacją: q97,5
+10,6 %/rok, TS1-liq ponad 97 % H0. Depozyt przy 3×: mediana 13,5 % kapitału łącznie ≈ 0,68 %
na monetę. Różnica per rok: 2021 −7,5 · 2022 −2,6 · 2023 +1,3 · 2024 −2,9 · 2025 −6,8 · 2026 −0,7 %.
**Werdykt TS1 z likwidacją: NIEROZSTRZYGNIĘTY.**

## Co na plus (+) / Co na minus (−)

**(+)** Pierwszy pomiar realnego kosztu sposobu handlu użytkownika; dane kompletne; wynik
potwierdzony niezależnie. **(−)** Likwidacje zabierają ok. ćwierć zysku trendu; najwięcej w latach
dużych wystrzałów altów (2021, 2025). Model konserwatywny: knoty ceny ostatniej (giełda liczy od
mark) i MMR 1 % — realny koszt może być nieco niższy.

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY**: likwidacje fazy 0 policzone niezależnie (pandas, ekstremum tygodnia
wobec ceny wejścia) **267** vs silnik **269** (0,7 %, różne traktowanie pojedynczych braków);
zamknięcia z archiwum = cache uniwersum (48 186 par, 0 różnic). `data:statistical-analysis`:
koszt istotny (t −3,16), sam trend nadal nierozstrzygnięty; poprawka, nie wariant — liczniki bez
zmian. `engineering:code-review`: `phase_returns_liq` bez likwidacji = `phase_returns` co do 1e-12
(test), strata likwidowanej pozycji = depozyt (test `hypothesis`), funding tylko żywych, kolektor
przez `http_get` — **Approve**.

## Wniosek

**Prostym językiem:** przy Twoim sposobie handlu (3× na każdej pozycji z osobnym depozytem)
mniej więcej co dwudziesta pozycja w tygodniu zostałaby zlikwidowana, bo altcoiny potrafią
w tydzień ruszyć się o ponad 30 %. To kosztuje ok. **3,6 punktu procentowego rocznie** — trend
zarabia wtedy ok. +11 % zamiast +15 %. Przy dźwigni 2× (większy depozyt, ta sama pozycja) koszt
spada do ok. 1,6 punktu.

## Rekomendacja

Do reguł wielkości pozycji (SZ1): na altcoinach **2× zamiast 3×** (ta sama ekspozycja, większy
depozyt), na BTC 3× (tygodniowe ruchy > 32 % rzadkie). Użyte skille: rejestr
`runs/skille/lq1-likwidacje.jsonl` (`clas5-runda`, `clas5-quant`, `testing-strategy`,
`data:validate-data`, `data:statistical-analysis`, `engineering:code-review`); pominięte
`security-review` (bez nowego hosta), `dataviz`.
