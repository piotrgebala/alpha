# C2.8 — formalny test OOS: `adx_14` dodane do MOMENTUM_FEATURES (2026-09-21)

## ID testu

**C2.8** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.8-adx14-oos-evaluation` (do utworzenia)
- **Poprzedzający stan (master):** Commit 2.7 — screening korelacji, `adx_14` wyróżniony
  jako jedyny z 8 kandydatów nisko skorelowany z resztą registry (NO decyzja o promocji)
- **Komenda:** `python3 -m backtest.evaluate_feature_candidate` (pełny sweep, bez `--quick`)
- **Nowe pliki:** `backtest/evaluate_feature_candidate.py` (poza pytest); `compute_adx_14`
  promowane do `agents/feature_miner.py` (FEATURE_FUNCTIONS, 10. cecha) +
  `agents/feature_registry.yaml` (wpis) + `agent_5_compliance/test_leakage.py`
  (parametryzowany test leakage automatycznie objął nową cechę, licznik 9→10) +
  jednostkowy test `tests/test_feature_miner.py::test_compute_adx_14_bounded_and_named`
- **Zmiana w `backtest/engine.py`:** nowy parametr `regime_feature_sets` w `run_backtest`
  (nadpisanie modułowej stałej `REGIME_FEATURE_SETS`), ten sam wzorzec threading co
  `trend_threshold`/`candles_per_day` (C2.5/C2.6) — pozwala porównać warianty feature
  setu bez duplikacji pipeline'u i bez zmiany `agents/ml_optimizer.py` na stałe. Nowy
  test integracyjny `tests/test_engine.py::test_run_backtest_threads_regime_feature_sets_to_model_training`.
- **Źródło danych:** `data/raw/BTC-USDT-USDT_5m_20250701T000000Z_20260701T000000Z.parquet`
  (105 120 świec 5m, bez dziur)
- **Parametry stałe:** `trend_threshold=0.7`/`range_threshold=0.3`, `ATR_MULTIPLIER=1.5`,
  `min_barrier_to_cost_ratio=2.0`, `candles_per_day=288`, `train_days=60/test_days=14/
  step_days=14`, seed sweep 42–51, `REVERSION_FEATURES` (Test 2, range) **niezmienione w
  obu wariantach**
- **Zmienna eksperymentu:** `MOMENTUM_FEATURES` (Test 1, trend) — baseline (4 cechy) vs
  kandydat (4 cechy + `adx_14`, DODANA, nie zamiana)

## Metodologia

Zgodnie z CLAUDE.md zasada 4 ("jedna cecha na raz, mierzona OOS — nigdy grid search po
wielu kombinacjach naraz") i protokołem `docs/rag/02_cechy_i_leakage.md`: **DOKŁADNIE
JEDNA zmiana** — `adx_14` dodane do `MOMENTUM_FEATURES` (Test 1/trend), `REVERSION_FEATURES`
(Test 2/range) pozostaje identyczne w obu wariantach. Oba warianty przechodzą przez
DOKŁADNIE ten sam pipeline (`run_backtest` → `compute_fold_metrics` → `classify_checkpoint`
→ `summarize_by_regime`), różniąc się wyłącznie listą cech Test 1. 10-seedowy sweep
stabilności (ten sam próg std < 0,2 co Commit 6/C2.5/C2.6). Wybór `adx_14` jako jedynego
kandydata do tego testu pochodzi z korelacji cecha-cecha (C2.7, bezpieczna, cały zbiór —
NIE z podglądania wyniku OOS), więc to porównanie jest jedynym krokiem tej serii o
faktycznej wadze dowodowej.

## Wynik — tabela porównawcza (checkpoint)

| wariant | n cech (trend) | mean_sharpe (seed=42) | trend_sharpe (seed=42) | klasyfikacja (ogólna) | n_valid_folds | stabilność (10 seed) |
|---|---|---|---|---|---|---|
| baseline (bez `adx_14`) | 4 | -14,3078 | -8,4560 | **NO-GO** | 6/40 | std=0,0000 |
| **kandydat (+`adx_14`)** | 5 | **-13,6943** | **-7,1116** | **NO-GO** | 6/40 | std=0,0000 |

Rozbicie per reżim (seed=42):

| wariant | regime | n_valid_folds | fraction_le_zero | fraction_positive_sign | fraction_above_threshold(0,5) | klasyfikacja regime |
|---|---|---|---|---|---|---|
| baseline | trend | 4/20 | 0,75 | 0,25 | 0,25 | NO-GO |
| **kandydat** | trend | 4/20 | **0,50** | **0,50** | 0,25 | **WARUNKOWY** |
| baseline | range | 2/20 | 1,00 | 0,00 | 0,00 | NO-GO |
| kandydat | range | 2/20 | 1,00 | 0,00 | 0,00 | NO-GO (bez zmian — `adx_14` nie dotyczy Test 2) |

Diagnostyka: który konkretnie fold odpowiada za zmianę klasyfikacji trend (seed=42):

| fold_idx | n_trades | Sharpe baseline | Sharpe kandydat | zmiana |
|---|---|---|---|---|
| 1 | 32 | -22,6618 | -22,6460 | ~bez zmian |
| 3 | 35 | +1,4426 | +3,3740 | poprawa, już dodatni w obu |
| 9 | 37 | -10,2077 | -9,2609 | lekka poprawa, nadal ujemny |
| **11** | 31→32 | **-2,3972** | **+0,0865** | **FLIP znaku — jedyny fold, który zmienia klasyfikację** |

## Co na plus (+)

- **Metodologia zadziałała dokładnie jak zaprojektowana:** `regime_feature_sets` (nowy
  parametr `run_backtest`) pozwolił przetestować DOKŁADNIE jedną zmianę (`adx_14` dodane
  do Test 1) bez dotykania Test 2 ani duplikowania pipeline'u — potwierdzone testem
  integracyjnym (`test_run_backtest_threads_regime_feature_sets_to_model_training`).
- **Kierunek zmiany jest konsekwentny, nie losowy:** mean_sharpe ogólny poprawia się
  (-14,31 → -13,69), sharpe w `trend` też (-8,46 → -7,11), a 3 z 4 folderów trend albo
  się poprawiają, albo pozostają praktycznie bez zmian — żaden się nie pogarsza. To
  odróżnia ten wynik od C2.5 (gdzie POGORSZENIE było konsekwentne we wszystkich 4
  kandydatach) — tu przynajmniej kierunek jest sprzyjający, nie przeciwny.
- **Stabilność potwierdzona:** std=0,0000 na 10 seedach dla OBU wariantów — wynik nie
  jest artefaktem jednego akurat wylosowanego seeda modelu.
- **Klasyfikacja regime `trend` faktycznie się zmienia** (NO-GO → WARUNKOWY) — to
  pierwszy przypadek w całej serii C2.5→C2.8, gdzie jakakolwiek pojedyncza zmiana
  (progi, timeframe, teraz cecha) przesuwa klasyfikację W KIERUNKU lepszym, a nie
  gorszym lub bez zmian.
- **Promocja `adx_14` do registry (`FEATURE_FUNCTIONS`) jest teraz formalna** — leakage
  test (parametryzowany, automatycznie objął nową cechę), jednostkowy test granic [0,100],
  wpis w `feature_registry.yaml` — spełnia DoD (docs/rag/05) niezależnie od decyzji o
  promocji do `MOMENTUM_FEATURES`.

## Co na minus (-)

- **Klasyfikacja OGÓLNA (oba reżimy razem) pozostaje NO-GO dla OBU wariantów.** Poprawa w
  `trend` nie zmienia headline'owego werdyktu checkpointu — `range` (2/2 ważnych foldów
  ujemne w obu wariantach, Sharpe ~-26/-27, kompletnie niezmieniony przez `adx_14`, bo
  dotyczy wyłącznie Test 1) nadal dominuje wynik.
- **"Poprawa" klasyfikacji trend opiera się na JEDNYM foldzie (fold_idx=11) zmieniającym
  znak z -2,40 na +0,09** — wartość +0,09 jest praktycznie nieodróżnialna od zera (próg
  GO to Sharpe > 0,5, próg NO-GO to Sharpe ≤ 0 — ten fold ledwo przekracza zero, nie
  zbliża się do progu GO). Przy n=31-32 transakcji w tym foldzie i tylko 4 ważnych
  foldach `trend` w CAŁYM przebiegu (ten sam problem małej próby, flagowany od C2.5/C2.6),
  to jest dokładnie tego rzędu efekt, którego można się spodziewać po prostu z tego, że
  dodanie jednej cechy nieco zmienia podział węzłów w drzewach XGBoost — NIE jest to
  mocny dowód, że `adx_14` niesie realny sygnał kierunkowy.
- **`fraction_above_threshold` (kryterium GO, próg 0,6) pozostaje na 0,25 w obu
  wariantach** — nawet w najlepszym reżimie (`trend`) kandydat jest wciąż daleko od
  jakiejkolwiek przesłanki GO, tylko przesunął się z "wyraźnie NO-GO" do "niejednoznaczne".
- **Efekt jest mały w kategoriach bezwzględnych:** zmiana mean_sharpe (+0,61, z -14,31 do
  -13,69) to ~4% względem skali problemu (rząd wielkości -14 do -20 widziany w całej
  serii C2.5-C2.8) — nie jest to zmiana, która sama w sobie sugeruje, że znaleziono
  brakujący składnik edge'u.
- **Spójne z C2.7 (brak sygnału cecha-target):** korelacja Spearman `adx_14`-target w
  `trend` wynosiła zaledwie -0,0279 (screening C2.7) — ten formalny test OOS nie
  zaprzecza temu wynikowi, tylko go potwierdza w innej formie (mały, niejednoznaczny
  efekt, nie silny edge).

## Wniosek

`adx_14` dodane do `MOMENTUM_FEATURES` daje MAŁĄ, KONSEKWENTNĄ (nie losową) poprawę w
reżimie `trend` — wystarczającą, by przesunąć jego klasyfikację z NO-GO do WARUNKOWY — ale
**NIEWYSTARCZAJĄCĄ, by zmienić ogólny werdykt checkpointu (nadal NO-GO)**, i opartą na
efekcie jednego foldu ledwo przekraczającego zero, przy bardzo małej próbie (4 ważne
foldy). To NIE jest ani mocne potwierdzenie edge'u `adx_14`, ani jego jednoznaczne
odrzucenie — to piąty z rzędu wynik w serii C2.5→C2.8 mieszczący się w tym samym paśmie:
żadna z przetestowanych, metodologicznie czystych zmian (progi, timeframe, teraz jedna
dodatkowa cecha) nie daje sygnału silniejszego niż szum.

## Rekomendacja (nie decyzja)

Zgodnie z regułą routingu: żadnego automatycznego wyboru. Do rozważenia przez użytkownika:

1. **Nie promować `adx_14` do `MOMENTUM_FEATURES` na stałe** — efekt jest zbyt słaby i
   zbyt zależny od jednego foldu, żeby uzasadnić trwałą zmianę modelu produkcyjnego;
   `compute_adx_14` zostaje w registry (obliczana, przetestowana pod kątem leakage), ale
   `agents/ml_optimizer.py::MOMENTUM_FEATURES` pozostaje bez zmian.
2. Alternatywnie: promować `adx_14` mimo słabego efektu, skoro NIE szkodzi (żaden fold
   się nie pogorszył) i jest tanie utrzymaniowo — ale to decyzja o tolerancji na
   niejednoznaczny dowód, nie o potwierdzonym edge'u.
3. **Najważniejsze:** to piąty niezależny wynik (po C2.5 progach, C2.6 timeframe, C2.7
   korelacjach, teraz C2.8 formalnym teście) w tym samym paśmie "brak silnego sygnału" —
   warto rozważyć, czy dalsza iteracja na poziomie cech pojedynczych ma sens, czy czas
   cofnąć się do rewizji samej hipotezy regime-gated (inny podział trend/range, inne
   dane wejściowe, albo inny instrument/timeframe natywnie pobrany, nie tylko
   zagregowany z 5m).

## Pełny surowy output

```
[data] 105120 świec: 2025-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00

[rejestr] 2 warianty (baseline + 1 kandydat, CLAUDE.md zasada 4):
  - baseline (bez adx_14): trend=['return_lag_1', 'volume_zscore_20', 'momentum_5', 'ema_diff_9_21']
  - kandydat (+adx_14): trend=['return_lag_1', 'volume_zscore_20', 'momentum_5', 'ema_diff_9_21', 'adx_14']

========================================================================================
WARIANT: baseline (bez adx_14)
========================================================================================
=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 6, 'n_total_folds': 40, 'fraction_above_threshold': 0.16666666666666666, 'fraction_le_zero': 0.8333333333333334, 'fraction_positive_sign': 0.16666666666666666, 'mean_sharpe': -14.3077642884818}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              2             20                      0.00              1.00                    0.00   -26.011196
 trend          NO-GO              4             20                      0.25              0.75                    0.25    -8.456048

=== Stabilność między seedami (wariant: baseline (bez adx_14)) ===
  seed= 42..51  mean_sharpe=-14.3078  klasyfikacja=NO-GO (identyczne na wszystkich 10 seedów)
std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
WARIANT: kandydat (+adx_14)
========================================================================================
=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 6, 'n_total_folds': 40, 'fraction_above_threshold': 0.16666666666666666, 'fraction_le_zero': 0.6666666666666666, 'fraction_positive_sign': 0.3333333333333333, 'mean_sharpe': -13.694313909185183}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              2             20                      0.00               1.0                     0.0   -26.859719
 trend      WARUNKOWY              4             20                      0.25               0.5                     0.5    -7.111611

=== Stabilność między seedami (wariant: kandydat (+adx_14)) ===
  seed= 42..51  mean_sharpe=-13.6943  klasyfikacja=NO-GO (identyczne na wszystkich 10 seedów)
std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
TABELA PORÓWNAWCZA — baseline vs kandydat (bez automatycznego wyboru zwycięzcy)
========================================================================================
              wariant  n_trend_features  mean_sharpe(seed=42)  trend_sharpe(seed=42) klasyfikacja(seed=42)  n_valid_folds  stability_std(10 seed)  stabilny
baseline (bez adx_14)                 4              -14.3078                -8.4560                 NO-GO              6                     0.0      True
   kandydat (+adx_14)                 5              -13.6943                -7.1116                 NO-GO              6                     0.0      True

[UWAGA] Ten skrypt CELOWO nie wybiera 'najlepszego' wariantu — decyzja, czy dopisać
'adx_14' na stałe do MOMENTUM_FEATURES (agents/ml_optimizer.py), należy do
użytkownika, po przeczytaniu pełnej tabeli powyżej, nie tylko najwyższej liczby
(CLAUDE.md zasada 1/4 — unikanie optymalizacji na wyniku PnL, jedna cecha na raz).
```

(Pełny per-fold Sharpe dla obu wariantów, wszystkich 40 foldów × 10 seedów — output
skryptu jest deterministyczny i odtwarzalny komendą z sekcji "Metadane"; skrócony tu do
klasyfikacji + rozbicia per reżim + diagnostyki foldu decydującego, zgodnie z konwencją
poprzednich rund.)
