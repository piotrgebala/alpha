# C2.10 — wydłużenie historii danych do 3 lat (Backlog Z5): nowa baza checkpointu (2026-09-21)

## ID testu

**C2.10** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.10-extended-history-z5`
- **Poprzedzający stan (master):** Commit 2.9 (`378ad3f`). Ta runda realizuje **Backlog Z5** —
  po C2.9 wskazane jako najważniejsze odblokowanie (zmierzony szum fold-jitter σ≈3,1 na rocznych
  danych czynił porównania wariantów o Δ<~3 nierozstrzygalnymi; 6/40 ważnych foldów).
- **Maszyna:** użytkownika (Windows, dostęp do Binance USDS-M potwierdzony: ccxt 4.5.48,
  `rateLimit=50 ms`, ~0,35 s/stronę 1000 świec). Sandbox nie miał dostępu — stąd zadanie czekało.
- **Decyzja użytkownika (zakres):** **3 lata, 2023-07-01 → 2026-07-01** (opcje: 3 lata / 5 lat /
  maks od 2019-09-10). `end` bez zmian, więc stare okno 2025-07→2026-07 jest ścisłym sufiksem
  nowego — to daje twardy test integralności (patrz niżej) i pozwala zachować stary parquet.
- **Komendy:** `py -m data.fetch_ohlcv` (fetch + cache), następnie
  `py -m backtest.run_checkpoint_v2` (kanoniczny przebieg + pełny sweep fold-jitter 10 offsetów).
- **Zmiany w kodzie:** `config/settings.yaml` (`data.start` 2025-07-01 → **2023-07-01**);
  `data/fetch_ohlcv.py` — `_fetch_page_with_retry` (retry z wykładniczym backoffem na
  `ccxt.NetworkError`, max 5 prób; `ExchangeError` celowo NIE retry'owany) + log postępu co 50
  stron. Powód: ~316 sekwencyjnych żądań bez retry, zapis do parquet dopiero po pętli — jeden
  timeout wyrzucał całość. 4 nowe testy w `tests/test_fetch_ohlcv.py` (retry→sukces, wyczerpanie
  prób, brak retry na `BadSymbol`, nazwa pliku cache koduje zakres). Pełny zestaw: **143/143**
  (139 + 4). Lint (ruff) nieuruchomiony — brak ruff na tej maszynie (C2.9 uruchamiał w sandboxie).
- **Źródło danych:** `data/raw/BTC-USDT-USDT_5m_20230701T000000Z_20260701T000000Z.parquet`
  (**315 648 świec 5m = 1096 dni × 288, zero dziur**, zero duplikatów, zero NaN). Stary plik
  `..._20250701T000000Z_20260701T000000Z.parquet` ZOSTAJE nietknięty jako zamrożone źródło C6–C2.9.
- **Parametry stałe:** CAŁY pipeline niezmieniony (progi 0.7/0.3, ATR_MULTIPLIER=1.5, bramka
  kosztowa 2.0, MOMENTUM_FEATURES bez `adx_14`, seed=42, walk-forward 60/14/14, offsety 0–9).
- **Zmienna "eksperymentu":** wyłącznie DŁUGOŚĆ HISTORII DANYCH. Zero zmian w hipotezie.

## Weryfikacja integralności danych (przed checkpointem)

Skrypt jednorazowy (poza repo): overlap nowego pliku z oknem 2025-07-01→2026-07-01 vs stary plik:
105 120 wierszy w obu, timestampy identyczne, **max |Δ| = 0,0 dla open/high/low/close/volume,
`DataFrame.equals` = True**. Świec per rok: 2023: 52 992, 2024: 105 408 (rok przestępny),
2025: 105 120, 2026: 52 128. Fetch przebiegł bez ani jednego retry.

## Metodologia

Identyczna z C2.9 (`backtest/run_checkpoint_v2.py`): kanoniczny przebieg (offset=0) + sweep
fold-jitter 0–9 dni; klasyfikacja wg docs/rag/03 (kryteria NIEZMIENIONE); per-fold Sharpe/t-stat,
pooled Sharpe/t-stat per reżim z N_eff. Dodatkowo (skrypt jednorazowy, read-only) policzono udział
reżimów i liczbę sygnałów zablokowanych przez bramkę kosztową z `folds_summary`.

**To jest NOWA BAZA, nie porównanie 1:1 z C6–C2.9** — tamte wyniki (i 7 wariantów z licznika
multiple-testing) dotyczą okna rocznego. Kolumna "stare okno" poniżej służy TYLKO orientacji.

## Wynik

| Miara | Stare okno (C2.9, 1 rok) | **Nowe okno (C2.10, 3 lata)** |
|---|---|---|
| Świec 5m | 105 120 | **315 648** |
| Foldy ważne / łącznie | 6 / 40 (15,0%) | **21 / 144 (14,6%)** |
| Klasyfikacja | NO-GO | **NO-GO** |
| mean_sharpe (offset=0) | -14,31 | **-12,39** |
| fraction_le_zero / positive_sign | 1,00 / 0,00 | 0,952 / 0,048 (1 fold: range #12, n=3, Sharpe +0,44) |
| `range`: foldy ważne, mean_sharpe | — | **10/72, -14,95**, NO-GO (9/10 ujemne) |
| `trend`: foldy ważne, mean_sharpe | — | **11/72, -10,07**, NO-GO (11/11 ujemne) |
| Pooled `range`: n, t_stat, N_eff, t_neff | 223, **-7,15**, NaN, NaN | **530, -10,47, 261, -7,34** |
| Pooled `trend`: n, t_stat, N_eff, t_neff | 135, **-2,91**, 110, -2,63 | **395, -5,51, 213, -4,04** |
| Fold-jitter: znak ujemny | 10/10 | **10/10** |
| Fold-jitter: zakres mean_sharpe | [-15,89; -6,20] | offsety 0–8: **[-13,83; -7,28]**; offset 9: **-188,96** (outlier) |
| Fold-jitter: σ(mean_sharpe) | 3,09 | **σ≈2,5 bez offsetu 9** (średnia -11,16); 56,3 z outlierem |
| Udział świec `trend` / `range` / `ambiguous` | 0,55% / 22,25% / 77,20% | **0,53% / 21,62% / 77,85%** |
| Bramka kosztowa `range`: zablokowane / przepuszczone | — | **61 313 / 1 240 (98,0% zablokowanych)** |
| Bramka kosztowa `trend`: zablokowane / przepuszczone | — | 51 / 418 (10,9%) |
| Foldy `trend` pominięte (`n_test_valid<30`) | — | **61/72** |
| Foldy `range` niepominięte z 0 sygnałów po bramce | — | **60/72** |

## Co na plus (+)

- **Z5 zrobione i odtwarzalne:** dane z Binance na maszynie użytkownika, plik zweryfikowany co do
  bajtu na overlapie ze starym oknem, zero dziur. Fetch odporny na chwilowe błędy sieci.
- **Pooled t-staty przestały być "na granicy":** `trend` t=-2,91 → **-5,51** (po N_eff -4,04),
  `range` -7,15 → **-10,47** (N_eff policzalne: 261, t_neff -7,34). Przy 2,4–2,9× większej
  liczbie transakcji zwrot per trade jest **istotnie ujemny w obu reżimach z dużym zapasem** —
  to najtwardsze dotąd sformułowanie stanu hipotezy i najlepszy materiał do decyzji Z10.
- **NO-GO odporne na fold-jitter również na 3 latach** (10/10 ujemne), szum bez outliera
  σ≈2,5 (vs 3,09) — porównania wariantów o Δ≈3 stały się nieco bardziej rozstrzygalne, ale
  nie jakościowo (patrz minus).
- Trzy lata pokrywają hossę 2023-24 (halving 04/2024, ATH 2025), korektę 2025 i 2026 — wynik
  nie jest artefaktem jednego reżimu rynkowego rocznego okna.

## Co na minus (-)

- **Odsetek ważnych foldów NIE wzrósł (14,6% vs 15,0%)** — 3× więcej danych dało liniowo
  3,5× więcej ważnych foldów, ale problem jest STRUKTURALNY, nie ilościowy:
  (a) `trend` = 0,53% świec na 3 latach, identycznie jak na roku → 61/72 foldów `trend` pomijane
  z braku ≥30 obserwacji testowych (to dyskretność `direction_persistence_10`, C2.5/Z7);
  (b) w `range` bramka kosztowa (Commit 2d) blokuje **98% sygnałów** → 60/72 foldów kończy z zerem
  transakcji. Dłuższa historia nie naprawi ani (a), ani (b) — to potwierdza, że kolejne
  dźwignie to Z7 (reguła reżimu) i Z6 (koszty), nie kolejne lata danych.
- **Outlier offset=9 (mean_sharpe -189)** to znana słabość annualizowanego per-fold Sharpe przy
  n≈kilka transakcji (C2.9/Z2): jeden fold z prawie zerowym std dominuje średnią. Statystyką
  nośną pozostają pooled t-staty, nie mean_sharpe. Miara stabilności powinna docelowo używać
  mediany lub pooled t per offset (kandydat do backlogu, nie zmieniano w tej rundzie).
- Nowa baza unieważnia porównywalność 1:1 z 7 wariantami z licznika multiple-testing —
  ewentualne powtórki C2.5–C2.8 na nowych danych to nowe warianty (nowy licznik w INDEX.md).
- Zakres 3 lat nie obejmuje bessy 2022 (decyzja użytkownika; opcja 5 lat/maks pozostaje
  dostępna — fetch to ~4–6 min).

## Wniosek

Hipoteza regime-gated w obecnej definicji (progi 0.7/0.3, bariera 1,5×ATR, bramka kosztowa 2.0)
na 3 latach BTC 5m: **NO-GO, istotnie ujemny zwrot per trade w obu reżimach (range t=-10,5,
trend t=-5,5), 10/10 offsetów ujemnych**. Dłuższa historia zwiększyła moc statystyczną
(werdykt twardszy), ale odsłoniła, że niska liczba ważnych foldów jest strukturalna
(pusty reżim `trend` + bramka kosztowa blokująca 98% `range`) — nie do naprawienia danymi.

## Rekomendacja

Bez automatycznego wyboru — decyzja przy użytkowniku (Z10). Materiał z tej rundy wskazuje, że
kolejne rundy hipotezowe w OBECNEJ definicji reżimu mają małe szanse: (1) Z7 (reguła reżimu na
`adx_14` zamiast dyskretnej persistence) adresuje przyczynę (a); (2) Z6 (weryfikacja kosztów,
udział maker) adresuje (b) — przy 98% blokady bramka jest de facto werdyktem o kosztach, nie o
modelu; (3) alternatywnie udokumentowane zamknięcie Fazy 0 wynikiem negatywnym. Z9 (natywne
1h/4h) jest teraz wykonalne z tej maszyny tym samym mechanizmem.

## Pełny surowy output

`py -m backtest.run_checkpoint_v2` (kanoniczny przebieg + sweep fold-jitter):

```
[data] 315648 świec: 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] brak dziur.

[seed=42] kanoniczny przebieg (offset=0)...

=== Sharpe + t-stat per fold (seed=42) ===
regime  fold_idx                test_start                  test_end  n_trades  mean_return  std_return     sharpe    t_stat                                            skip_reason
 trend         0 2023-09-21 19:10:00+00:00 2023-10-05 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=73, n_test_valid=28 < min_train_rows=30
 trend         1 2023-10-05 19:10:00+00:00 2023-10-19 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=89, n_test_valid=8 < min_train_rows=30
 trend         2 2023-10-19 19:10:00+00:00 2023-11-02 19:10:00+00:00        33    -0.000586    0.002032  -8.460495 -1.656398                                                    NaN
 trend         3 2023-11-02 19:10:00+00:00 2023-11-16 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=97, n_test_valid=24 < min_train_rows=30
 trend         4 2023-11-16 19:10:00+00:00 2023-11-30 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=113, n_test_valid=8 < min_train_rows=30
 trend         5 2023-11-30 19:10:00+00:00 2023-12-14 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=93, n_test_valid=25 < min_train_rows=30
 trend         6 2023-12-14 19:10:00+00:00 2023-12-28 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=104, n_test_valid=9 < min_train_rows=30
 trend         7 2023-12-28 19:10:00+00:00 2024-01-11 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=76, n_test_valid=13 < min_train_rows=30
 trend         8 2024-01-11 19:10:00+00:00 2024-01-25 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=65, n_test_valid=9 < min_train_rows=30
 trend         9 2024-01-25 19:10:00+00:00 2024-02-08 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=56, n_test_valid=16 < min_train_rows=30
 trend        10 2024-02-08 19:10:00+00:00 2024-02-22 19:10:00+00:00        45    -0.000093    0.002979  -1.071695 -0.209817                                                    NaN
 trend        11 2024-02-22 19:10:00+00:00 2024-03-07 19:10:00+00:00        38    -0.001165    0.002617 -14.017164 -2.744284                                                    NaN
 trend        12 2024-03-07 19:10:00+00:00 2024-03-21 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=127, n_test_valid=19 < min_train_rows=30
 trend        13 2024-03-21 19:10:00+00:00 2024-04-04 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=132, n_test_valid=9 < min_train_rows=30
 trend        14 2024-04-04 19:10:00+00:00 2024-04-18 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=127, n_test_valid=16 < min_train_rows=30
 trend        15 2024-04-18 19:10:00+00:00 2024-05-02 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=91, n_test_valid=11 < min_train_rows=30
 trend        16 2024-05-02 19:10:00+00:00 2024-05-16 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=66, n_test_valid=8 < min_train_rows=30
 trend        17 2024-05-16 19:10:00+00:00 2024-05-30 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=49, n_test_valid=8 < min_train_rows=30
 trend        18 2024-05-30 19:10:00+00:00 2024-06-13 19:10:00+00:00        11    -0.000735    0.002508  -4.966592 -0.972361                                                    NaN
 trend        19 2024-06-13 19:10:00+00:00 2024-06-27 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=64, n_test_valid=2 < min_train_rows=30
 trend        20 2024-06-27 19:10:00+00:00 2024-07-11 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=62, n_test_valid=26 < min_train_rows=30
 trend        21 2024-07-11 19:10:00+00:00 2024-07-25 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=70, n_test_valid=29 < min_train_rows=30
 trend        22 2024-07-25 19:10:00+00:00 2024-08-08 19:10:00+00:00        43    -0.000337    0.002516  -4.486360 -0.878341                                                    NaN
 trend        23 2024-08-08 19:10:00+00:00 2024-08-22 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=117, n_test_valid=27 < min_train_rows=30
 trend        24 2024-08-22 19:10:00+00:00 2024-09-05 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=125, n_test_valid=11 < min_train_rows=30
 trend        25 2024-09-05 19:10:00+00:00 2024-09-19 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=125, n_test_valid=24 < min_train_rows=30
 trend        26 2024-09-19 19:10:00+00:00 2024-10-03 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=110, n_test_valid=25 < min_train_rows=30
 trend        27 2024-10-03 19:10:00+00:00 2024-10-17 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=115, n_test_valid=28 < min_train_rows=30
 trend        28 2024-10-17 19:10:00+00:00 2024-10-31 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=94, n_test_valid=18 < min_train_rows=30
 trend        29 2024-10-31 19:10:00+00:00 2024-11-14 19:10:00+00:00        73    -0.000903    0.002545 -15.493527 -3.033327                                                    NaN
 trend        30 2024-11-14 19:10:00+00:00 2024-11-28 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=157, n_test_valid=9 < min_train_rows=30
 trend        31 2024-11-28 19:10:00+00:00 2024-12-12 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=135, n_test_valid=25 < min_train_rows=30
 trend        32 2024-12-12 19:10:00+00:00 2024-12-26 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=141, n_test_valid=21 < min_train_rows=30
 trend        33 2024-12-26 19:10:00+00:00 2025-01-09 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=137, n_test_valid=19 < min_train_rows=30
 trend        34 2025-01-09 19:10:00+00:00 2025-01-23 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=111, n_test_valid=25 < min_train_rows=30
 trend        35 2025-01-23 19:10:00+00:00 2025-02-06 19:10:00+00:00        36    -0.000420    0.002472  -5.208518 -1.019725                                                    NaN
 trend        36 2025-02-06 19:10:00+00:00 2025-02-20 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=111, n_test_valid=6 < min_train_rows=30
 trend        37 2025-02-20 19:10:00+00:00 2025-03-06 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=92, n_test_valid=25 < min_train_rows=30
 trend        38 2025-03-06 19:10:00+00:00 2025-03-20 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=105, n_test_valid=5 < min_train_rows=30
 trend        39 2025-03-20 19:10:00+00:00 2025-04-03 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=80, n_test_valid=7 < min_train_rows=30
 trend        40 2025-04-03 19:10:00+00:00 2025-04-17 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=60, n_test_valid=24 < min_train_rows=30
 trend        41 2025-04-17 19:10:00+00:00 2025-05-01 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=62, n_test_valid=9 < min_train_rows=30
 trend        42 2025-05-01 19:10:00+00:00 2025-05-15 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=56, n_test_valid=25 < min_train_rows=30
 trend        43 2025-05-15 19:10:00+00:00 2025-05-29 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=65, n_test_valid=16 < min_train_rows=30
 trend        44 2025-05-29 19:10:00+00:00 2025-06-12 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=80, n_test_valid=16 < min_train_rows=30
 trend        45 2025-06-12 19:10:00+00:00 2025-06-26 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=71, n_test_valid=28 < min_train_rows=30
 trend        46 2025-06-26 19:10:00+00:00 2025-07-10 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=85, n_test_valid=27 < min_train_rows=30
 trend        47 2025-07-10 19:10:00+00:00 2025-07-24 19:10:00+00:00        13    -0.002718    0.001757 -28.491757 -5.578124                                                    NaN
 trend        48 2025-07-24 19:10:00+00:00 2025-08-07 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=110, n_test_valid=19 < min_train_rows=30
 trend        49 2025-08-07 19:10:00+00:00 2025-08-21 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=123, n_test_valid=18 < min_train_rows=30
 trend        50 2025-08-21 19:10:00+00:00 2025-09-04 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=109, n_test_valid=21 < min_train_rows=30
 trend        51 2025-09-04 19:10:00+00:00 2025-09-18 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=110, n_test_valid=16 < min_train_rows=30
 trend        52 2025-09-18 19:10:00+00:00 2025-10-02 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=81, n_test_valid=25 < min_train_rows=30
 trend        53 2025-10-02 19:10:00+00:00 2025-10-16 19:10:00+00:00        32    -0.001747    0.002227 -22.661828 -4.436739                                                    NaN
 trend        54 2025-10-16 19:10:00+00:00 2025-10-30 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=106, n_test_valid=16 < min_train_rows=30
 trend        55 2025-10-30 19:10:00+00:00 2025-11-13 19:10:00+00:00        40    -0.000308    0.002842  -3.496492 -0.684544                                                    NaN
 trend        56 2025-11-13 19:10:00+00:00 2025-11-27 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=133, n_test_valid=16 < min_train_rows=30
 trend        57 2025-11-27 19:10:00+00:00 2025-12-11 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=116, n_test_valid=28 < min_train_rows=30
 trend        58 2025-12-11 19:10:00+00:00 2025-12-25 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=124, n_test_valid=11 < min_train_rows=30
 trend        59 2025-12-25 19:10:00+00:00 2026-01-08 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=101, n_test_valid=22 < min_train_rows=30
 trend        60 2026-01-08 19:10:00+00:00 2026-01-22 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=98, n_test_valid=29 < min_train_rows=30
 trend        61 2026-01-22 19:10:00+00:00 2026-02-05 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=90, n_test_valid=26 < min_train_rows=30
 trend        62 2026-02-05 19:10:00+00:00 2026-02-19 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=95, n_test_valid=28 < min_train_rows=30
 trend        63 2026-02-19 19:10:00+00:00 2026-03-05 19:10:00+00:00        31    -0.000198    0.002350  -2.397221 -0.469329                                                    NaN
 trend        64 2026-03-05 19:10:00+00:00 2026-03-19 19:10:00+00:00         0          NaN         NaN        NaN       NaN n_train_valid=133, n_test_valid=17 < min_train_rows=30
 trend        65 2026-03-19 19:10:00+00:00 2026-04-02 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=119, n_test_valid=6 < min_train_rows=30
 trend        66 2026-04-02 19:10:00+00:00 2026-04-16 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=92, n_test_valid=16 < min_train_rows=30
 trend        67 2026-04-16 19:10:00+00:00 2026-04-30 19:10:00+00:00         0          NaN         NaN        NaN       NaN   n_train_valid=73, n_test_valid=7 < min_train_rows=30
 trend        68 2026-04-30 19:10:00+00:00 2026-05-14 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=65, n_test_valid=13 < min_train_rows=30
 trend        69 2026-05-14 19:10:00+00:00 2026-05-28 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=47, n_test_valid=13 < min_train_rows=30
 trend        70 2026-05-28 19:10:00+00:00 2026-06-11 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=49, n_test_valid=26 < min_train_rows=30
 trend        71 2026-06-11 19:10:00+00:00 2026-06-25 19:10:00+00:00         0          NaN         NaN        NaN       NaN  n_train_valid=62, n_test_valid=16 < min_train_rows=30
 range         0 2023-09-19 04:15:00+00:00 2023-10-03 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         1 2023-10-03 04:15:00+00:00 2023-10-17 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         2 2023-10-17 04:15:00+00:00 2023-10-31 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         3 2023-10-31 04:15:00+00:00 2023-11-14 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         4 2023-11-14 04:15:00+00:00 2023-11-28 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         5 2023-11-28 04:15:00+00:00 2023-12-12 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         6 2023-12-12 04:15:00+00:00 2023-12-26 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         7 2023-12-26 04:15:00+00:00 2024-01-09 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         8 2024-01-09 04:15:00+00:00 2024-01-23 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range         9 2024-01-23 04:15:00+00:00 2024-02-06 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        10 2024-02-06 04:15:00+00:00 2024-02-20 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        11 2024-02-20 04:15:00+00:00 2024-03-05 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        12 2024-03-05 04:15:00+00:00 2024-03-19 04:15:00+00:00         3     0.000131    0.002624   0.442014  0.086538                                                    NaN
 range        13 2024-03-19 04:15:00+00:00 2024-04-02 04:15:00+00:00       105    -0.001012    0.002235 -23.694129 -4.638843                                                    NaN
 range        14 2024-04-02 04:15:00+00:00 2024-04-16 04:15:00+00:00        73    -0.000453    0.002147  -9.212123 -1.803552                                                    NaN
 range        15 2024-04-16 04:15:00+00:00 2024-04-30 04:15:00+00:00        66    -0.000876    0.001984 -18.311149 -3.584962                                                    NaN
 range        16 2024-04-30 04:15:00+00:00 2024-05-14 04:15:00+00:00        34    -0.001247    0.002218 -16.751311 -3.279576                                                    NaN
 range        17 2024-05-14 04:15:00+00:00 2024-05-28 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        18 2024-05-28 04:15:00+00:00 2024-06-11 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        19 2024-06-11 04:15:00+00:00 2024-06-25 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        20 2024-06-25 04:15:00+00:00 2024-07-09 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        21 2024-07-09 04:15:00+00:00 2024-07-23 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        22 2024-07-23 04:15:00+00:00 2024-08-06 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        23 2024-08-06 04:15:00+00:00 2024-08-20 04:15:00+00:00        18    -0.001192    0.002175 -11.877392 -2.325359                                                    NaN
 range        24 2024-08-20 04:15:00+00:00 2024-09-03 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        25 2024-09-03 04:15:00+00:00 2024-09-17 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        26 2024-09-17 04:15:00+00:00 2024-10-01 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        27 2024-10-01 04:15:00+00:00 2024-10-15 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        28 2024-10-15 04:15:00+00:00 2024-10-29 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        29 2024-10-29 04:15:00+00:00 2024-11-12 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        30 2024-11-12 04:15:00+00:00 2024-11-26 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        31 2024-11-26 04:15:00+00:00 2024-12-10 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        32 2024-12-10 04:15:00+00:00 2024-12-24 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        33 2024-12-24 04:15:00+00:00 2025-01-07 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        34 2025-01-07 04:15:00+00:00 2025-01-21 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        35 2025-01-21 04:15:00+00:00 2025-02-04 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        36 2025-02-04 04:15:00+00:00 2025-02-18 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        37 2025-02-18 04:15:00+00:00 2025-03-04 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        38 2025-03-04 04:15:00+00:00 2025-03-18 04:15:00+00:00        44    -0.000920    0.002269 -13.741389 -2.690293                                                    NaN
 range        39 2025-03-18 04:15:00+00:00 2025-04-01 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        40 2025-04-01 04:15:00+00:00 2025-04-15 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        41 2025-04-15 04:15:00+00:00 2025-04-29 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        42 2025-04-29 04:15:00+00:00 2025-05-13 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        43 2025-05-13 04:15:00+00:00 2025-05-27 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        44 2025-05-27 04:15:00+00:00 2025-06-10 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        45 2025-06-10 04:15:00+00:00 2025-06-24 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        46 2025-06-24 04:15:00+00:00 2025-07-08 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        47 2025-07-08 04:15:00+00:00 2025-07-22 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        48 2025-07-22 04:15:00+00:00 2025-08-05 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        49 2025-08-05 04:15:00+00:00 2025-08-19 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        50 2025-08-19 04:15:00+00:00 2025-09-02 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        51 2025-09-02 04:15:00+00:00 2025-09-16 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        52 2025-09-16 04:15:00+00:00 2025-09-30 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        53 2025-09-30 04:15:00+00:00 2025-10-14 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        54 2025-10-14 04:15:00+00:00 2025-10-28 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        55 2025-10-28 04:15:00+00:00 2025-11-11 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        56 2025-11-11 04:15:00+00:00 2025-11-25 04:15:00+00:00        47    -0.001253    0.002280 -19.251564 -3.769076                                                    NaN
 range        57 2025-11-25 04:15:00+00:00 2025-12-09 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        58 2025-12-09 04:15:00+00:00 2025-12-23 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        59 2025-12-23 04:15:00+00:00 2026-01-06 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        60 2026-01-06 04:15:00+00:00 2026-01-20 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        61 2026-01-20 04:15:00+00:00 2026-02-03 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        62 2026-02-03 04:15:00+00:00 2026-02-17 04:15:00+00:00       133    -0.001238    0.002239 -32.567114 -6.375998                                                    NaN
 range        63 2026-02-17 04:15:00+00:00 2026-03-03 04:15:00+00:00         7    -0.000845    0.002529  -4.516335 -0.884209                                                    NaN
 range        64 2026-03-03 04:15:00+00:00 2026-03-17 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        65 2026-03-17 04:15:00+00:00 2026-03-31 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        66 2026-03-31 04:15:00+00:00 2026-04-14 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        67 2026-04-14 04:15:00+00:00 2026-04-28 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        68 2026-04-28 04:15:00+00:00 2026-05-12 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        69 2026-05-12 04:15:00+00:00 2026-05-26 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        70 2026-05-26 04:15:00+00:00 2026-06-09 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN
 range        71 2026-06-09 04:15:00+00:00 2026-06-23 04:15:00+00:00         0          NaN         NaN        NaN       NaN                                                    NaN

=== Klasyfikacja (kryteria docs/rag/03, NIEZMIENIONE) ===
{'classification': 'NO-GO', 'n_valid_folds': 21, 'n_total_folds': 144, 'fraction_above_threshold': 0.0, 'fraction_le_zero': 0.9523809523809523, 'fraction_positive_sign': 0.047619047619047616, 'mean_sharpe': -12.392006781796571}

=== Rozbicie per reżim ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO             10             72                       0.0               0.9                     0.1   -14.948049
 trend          NO-GO             11             72                       0.0               1.0                     0.0   -10.068332

=== Diagnostyka pooled per reżim (Commit 2.9/Z2+Z3) ===
regime  n_trades  mean_return  std_return  sharpe_per_trade     t_stat      n_eff  t_stat_neff
 range       530    -0.001001    0.002202         -0.454610 -10.465919 260.911565    -7.343213
 trend       395    -0.000712    0.002566         -0.277329  -5.511796 212.635627    -4.044014
[interpretacja] |t_stat| < ~2 => średni zwrot per trade nieodróżnialny od zera
przy tej liczbie obserwacji; t_stat_neff dodatkowo koryguje za autokorelację.

[sweep] fold-jitter: offsety startu okien walk-forward 0..9 dni
  ... fold_start_offset_days=0
  ... fold_start_offset_days=1
  ... fold_start_offset_days=2
  ... fold_start_offset_days=3
  ... fold_start_offset_days=4
  ... fold_start_offset_days=5
  ... fold_start_offset_days=6
  ... fold_start_offset_days=7
  ... fold_start_offset_days=8
  ... fold_start_offset_days=9

=== Stabilność fold-jitter (Commit 2.9/Z1 — zamiast pustego sweepu seedów) ===
 offset_days  mean_sharpe classification  n_valid_folds  n_total_folds
         0.0   -12.392007          NO-GO             21            144
         1.0    -7.501256          NO-GO             24            144
         2.0    -7.281113          NO-GO             25            144
         3.0   -10.123605          NO-GO             26            144
         4.0   -10.352946          NO-GO             27            143
         5.0   -13.195094          NO-GO             28            143
         6.0   -12.955231          NO-GO             23            143
         7.0   -13.830869          NO-GO             23            143
         8.0   -12.773724          NO-GO             25            142
         9.0  -188.963994          NO-GO             27            142

std(mean_sharpe) po 10 offsetach = 56.2759; zakres = [-188.9640, -7.2811]; spójność znaku (ujemny) = 100%
[UWAGA] Celowo BEZ progu pass/fail — stary próg std<0.2 dotyczył (pustego) szumu
seedów i nie przenosi się na realną perturbację podziału danych. Interpretacja
rozkładu należy do użytkownika (patrz backtest/checkpoint_lib.py, docstring).
```

Diagnostyka jednorazowa (udział reżimów + bramka kosztowa z `folds_summary`, read-only, poza repo). UWAGA: kolumna `gated_pct` w tym bloku dzieli przez `signals` (= sygnały PO bramce), więc jest myląca — poprawny odsetek zablokowanych to cost_gated/(cost_gated+signals): range 98,0%, trend 10,9%.

```
[data] 315648 świec
[regime share, progi 0.7/0.3] ambiguous=77.85%, range=21.62%, trend=0.53%
[regime share, tylko stare okno 2025-07+] ambiguous=77.20%, range=22.25%, trend=0.55%
[folds_summary per regime]
        folds  skipped  signals  cost_gated  gated_pct
regime                                                
range      72        0     1240       61313     4944.6
trend      72       61      418          51       12.2
[foldy nie-pominięte z 0 sygnałów po bramce] 
[foldy nie-pominięte z 0 sygnałów PRZED bramką (model milczy)] range=60
```
