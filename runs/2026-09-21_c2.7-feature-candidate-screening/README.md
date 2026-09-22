# C2.7 — przegląd kandydatek nowych cech: korelacje cecha-cecha i cecha-target (2026-09-21)

## ID testu

**C2.7** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.7-feature-candidate-screening` (do utworzenia)
- **Poprzedzający stan (master):** Commit 2.6 — odporność na timeframe (1h/4h), NO-GO,
  edge kierunkowy nieobecny/ujemny niezależnie od granulacji danych
- **Komenda:** `python3 -m backtest.screen_feature_candidates`
- **Nowy plik:** `backtest/screen_feature_candidates.py` (poza pytest, jak inne skrypty
  analityczne — `diagnose_cost_feasibility.py`, `calibrate_regime_thresholds.py`,
  `checkpoint_timeframe_robustness.py`)
- **Źródło danych:** `data/raw/BTC-USDT-USDT_5m_20250701T000000Z_20260701T000000Z.parquet`
  (105 120 świec 5m, bez dziur) — CAŁY zbiór, bez walk-forward (uzasadnienie niżej)
- **Kontekst pytania użytkownika:** "czy nie lepiej zrobić X zmiennych i sprawdzić korelacje
  między nimi, a dopiero później zbudować model" — odpowiedź metodologiczna: TAK dla
  korelacji cecha-cecha (bezpieczne), korelacja cecha-target WYŁĄCZNIE opisowa/eksploracyjna
  (nigdy jako bramka selekcji) — patrz `docs/rag/02_cechy_i_leakage.md`, sekcja "Rozszerzanie
  feature setu — protokół", i CLAUDE.md zasada 4.

## Metodologia

1. **8 nowych kandydatek, 4 rodziny**, każda świadomie zaprojektowana jako NIE-redundantna
   z 9 cechami już w `agents/feature_miner.FEATURE_FUNCTIONS` NA PODSTAWIE DEFINICJI wzoru
   (nie podglądania wyniku na tych danych — CLAUDE.md zasada 1):

   | Rodzina | Kandydatka | Definicja | Model docelowy |
   |---|---|---|---|
   | volatility | `bb_width_20` | (upper-lower)/middle, TA-Lib BBANDS okno 20 | oba (diagnostyczna) |
   | volatility | `realized_vol_20` | rolling std log-zwrotów, okno 20 | oba (diagnostyczna) |
   | momentum | `roc_20` | log-return t vs t-20 (dłuższy horyzont niż `momentum_5`) | Test 1 (trend) |
   | trend-strength | `adx_14` | TA-Lib ADX, 14-period | Test 1 (trend) |
   | mean-reversion | `bb_pctb_20` | (close-lower)/(upper-lower), TA-Lib BBANDS okno 20 | Test 2 (range) |
   | mean-reversion | `vwap_deviation_20` | (close-vwap)/vwap, rolling VWAP okno 20 | Test 2 (range) |
   | volume | `obv_zscore_20` | rolling z-score skumulowanego OBV, okno 20 | oba (diagnostyczna) |
   | volume | `volume_roc_10` | volume[t]/volume[t-10] - 1 | oba (diagnostyczna) |

   Wszystkie: czyste, bezstanowe, trailing-only (ten sam kontrakt co `agents/feature_miner.py`
   — zero `.shift(-n)`, zero normalizacji po całym zbiorze). NIE wchodzą do
   `FEATURE_FUNCTIONS`/`MOMENTUM_FEATURES`/`REVERSION_FEATURES` na tym etapie — formalny test
   leakage (CLAUDE.md zasada 2) ma sens dopiero przy promocji JEDNEJ wybranej cechy.

2. **Blok 2 — korelacja Spearman cecha-cecha, 17×17 (9 istniejących + 8 kandydatek), CAŁY
   zbiór.** BEZPIECZNE: nie dotyka etykiety, więc nie ma ryzyka data dredging/leakage — służy
   wyłącznie do wykrycia redundancji (próg opisowy `|corr| > 0.7`).

3. **Blok 3 — korelacja Spearman cecha-target (label triple-barrier jako -1/0/1 porządkowe),
   osobno dla `regime=trend` i `regime=range`, CAŁY zbiór.** JAWNIE oznaczone jako
   OPISOWE/EKSPLORACYJNE — to podglądanie etykiety na całym zbiorze, więc podlega dokładnie
   ryzyku (1) z protokołu (`docs/rag/02`): multiple testing / data dredging. Brak p-value w
   output (świadomie — żeby nie sugerować istotności, której to porównanie nie ustala). Jedyny
   krok o wadze dowodowej: formalny walk-forward JEDNEJ wybranej cechy (przyszły Commit, poza
   tym skryptem).

## Wynik — blok 2: redundancja cecha-cecha (|corr| > 0,7, 28 par na 136 możliwych)

Najważniejsze pary (pełna lista w "Pełny surowy output"):

| Para | corr | Interpretacja |
|---|---|---|
| `price_zscore_20` <-> `bb_pctb_20` | **+1,000** | **Identyczne co do rangi.** `bb_pctb_20` to afiniczna transformacja `price_zscore_20` przy tym samym oknie=20 i bandach ±2 std — matematycznie ta sama informacja, nie nowa cecha. |
| `rsi_14` <-> `price_zscore_20` | +0,917 | Znana zależność — RSI i z-score ceny przy tym samym oknie mierzą podobny sygnał mean-reversion. |
| `ema_diff_9_21` <-> `roc_20` | +0,891 | Momentum krótko- i długoterminowe silnie skorelowane na tym instrumencie/timeframe. |
| `atr_14` <-> `atr_pctrank_20d` | +0,884 | Oczekiwane (jedna liczona z drugiej). |
| `atr_14` <-> `realized_vol_20` | +0,880 | Dwie różne bazy (high-low range vs close-to-close) dają prawie tę samą informację na tym zbiorze. |
| `bb_width_20` <-> `realized_vol_20` | +0,850 | Kandydatki volatility silnie redundantne między sobą. |
| `volume_zscore_20` <-> `volume_roc_10` | +0,747 | Graniczna redundancja (chwilowy z-score vs 10-świecowe ROC wolumenu). |

Cecha o NAJNIŻSZEJ korelacji ze wszystkim poza rodziną volatility: **`adx_14`**
(corr z `direction_persistence_10` = tylko +0,07; z resztą cech momentum/reversion/volume:
|corr| < 0,05) — jedyny kandydat, który wygląda na GENUINE niezależny wymiar informacji, nie
przemalowaną wersję czegoś już w registry.

## Wynik — blok 3: korelacja cecha-target (EKSPLORACYJNE, nie selekcja)

| regime | n (z etykietą) | najsilniejsza cecha | corr | uwaga |
|---|---|---|---|---|
| `trend` | 523 | `volume_roc_10` (KANDYDAT) | -0,0647 | próbka bardzo mała (patrz C2.5/C2.6 — trend rzadki) |
| `range` | 22 198 | `realized_vol_20` (KANDYDAT) | -0,0346 | próbka duża, ale corr jest szumem |

Pełne rankingi (17 cech × 2 reżimy) w "Pełny surowy output". Żadna cecha — istniejąca ani
kandydat — nie przekracza |corr| ≈ 0,065 w żadnym reżimie.

## Co na plus (+)

- **Korelacja cecha-cecha złapała realną redundancję, którą trudno było przewidzieć z samej
  definicji wzoru:** `bb_pctb_20` (kandydat) okazał się PERFEKCYJNIE (corr=1,000) redundantny z
  już istniejącą `price_zscore_20` — to dokładnie ten typ diagnostycznej wartości, dla którego
  użytkownik zaproponował ten krok. Bez tego testu `bb_pctb_20` mógłby zostać przetestowany OOS
  jako "nowa" cecha i "potwierdzić" edge, który w rzeczywistości już jest w modelu pod inną
  nazwą.
- **`adx_14` wyróżnia się jako jedyny kandydat z niską korelacją do wszystkiego poza własną
  rodziną (volatility)** — w tym, zaskakująco, niską korelacją (+0,07) do
  `direction_persistence_10`, mimo że oba mają być miarą "siły trendu". To sugeruje, że `adx_14`
  niesie GENUINE odrębną informację, a nie duplikat już znanego (i, jak wiemy z C2.5, wadliwego
  — dyskretnego) `direction_persistence_10`. Naturalny kandydat #1 do formalnego testu OOS.
- **Metodologia zadziałała zgodnie z założeniem: krok bezpieczny (cecha-cecha) i krok opisowy
  (cecha-target) zostały jawnie rozdzielone w kodzie i w output** — brak p-value w bloku 3 był
  świadomą decyzją, żeby nie sugerować istotności statystycznej.
- **Wynik bloku 3 jest spójny z C2.5/C2.6, niezależną metodą:** żadna cecha (istniejąca ani
  kandydat) nie pokazuje korelacji z targetem większej niż szum (~0,065 max na 523 próbkach w
  `trend`, ~0,035 max na 22 198 próbkach w `range`) — to NIEZALEŻNE od modelu XGBoost
  potwierdzenie, że problem nie jest "model nie widzi sygnału w danych", tylko "sygnału
  praktycznie nie ma w żadnej z 17 zbadanych cech".

## Co na minus (-)

- **Żadna z 8 kandydatek nie pokazuje obiecującej korelacji z targetem** — najlepszy wynik to
  -0,0647 (`volume_roc_10`, `trend`, n=523). To nie jest dowód braku edge'u (to tylko korelacja
  liniowa/monotoniczna na całym zbiorze, model może wychwycić nieliniowe interakcje), ale nie
  daje też żadnej przesłanki, KTÓRĄ cechę faworyzować do kolejnego, kosztownego testu OOS.
- **Próbka `trend` (n=523) jest zbyt mała, żeby jakakolwiek korelacja tutaj miała wagę
  diagnostyczną** — przy silnej autokorelacji świec 5m (patrz `effective_sample_size` w
  `agents/labeling.py`) efektywna liczba niezależnych obserwacji jest prawdopodobnie rzędu
  dziesiątek, nie setek. Ranking cech w `trend` należy traktować jako czysty szum.
  Rankingi w `range` (n=22 198) są liczebnie solidniejsze, ale nadal pokazują korelacje bliskie
  zeru.
  - **Korelacja w bloku 3 jest liczona na CAŁYM zbiorze, nie OOS** — to jest dokładnie ryzyko
  (1) z protokołu `docs/rag/02` (multiple testing / data dredging) na 17 cechach × 2 reżimy =
  34 porównania. Żaden wynik stąd nie powinien być traktowany jako "cecha X ma edge" — tylko
  jako (bardzo słaba) wskazówka do priorytetyzacji KOLEJNEGO, formalnego testu OOS.
- **Rodzina volatility (`bb_width_20`, `realized_vol_20`) jest silnie redundantna z już
  istniejącymi cechami regime-gate (`atr_14`, `atr_pctrank_20d`, corr 0,79–0,88)** — nawet że
  te ostatnie nie są obecnie w `MOMENTUM_FEATURES`/`REVERSION_FEATURES` (są tylko regime-gate),
  dodanie kandydatek volatility do modelu prawdopodobnie doda mało nowej informacji ponad to,
  co regime gate już koduje pośrednio przez klasyfikację `trend`/`range`.
- **`obv_zscore_20` (rodzina "volume") jest w praktyce bliżej rodziny mean-reversion/momentum
  niż volume** — corr z `price_zscore_20`/`bb_pctb_20` = 0,776–0,78, bo OBV kumuluje
  wolumen×znak zwrotu, więc odziedzicza dużą część sygnału kierunkowego ceny. Etykieta "rodzina
  volume" w `FAMILY_ASSIGNMENT` jest myląca dla tej konkretnej cechy — do poprawienia, jeśli
  `obv_zscore_20` przejdzie dalej.

## Wniosek

Krok bezpieczny (korelacja cecha-cecha) dał jeden konkretny, praktyczny wynik: **`bb_pctb_20`
odrzucony jako redundantny** (perfekcyjna korelacja z `price_zscore_20`), a **`adx_14`
wyróżniony jako jedyny kandydat z niską korelacją do reszty registry** — sensowny kandydat #1
do formalnego testu. Krok opisowy (korelacja cecha-target) nie dał żadnej przesłanki
faworyzującej konkretną cechę ponad inne — wszystkie korelacje są w paśmie szumu, spójnie z
NO-GO z C2.5/C2.6. To NIE zamyka wątku cech — tylko potwierdza, że wybór KTÓREJ cechy testować
dalej nie może się opierać na tym screeningu (za słaby sygnał), tylko na uzasadnieniu
merytorycznym (np. `adx_14` jako ciągła, niezredukowana do dyskretnych kroków alternatywa dla
`direction_persistence_10` w kontekście otwartego wątku "dlaczego `range` konsekwentnie stawiał
na long podczas trendu spadkowego" — patrz STATUS.md §7).

## Rekomendacja (nie decyzja)

Zgodnie z regułą routingu: żadnego automatycznego wyboru "zwycięzcy". Do rozważenia przez
użytkownika:

1. **Usunąć `bb_pctb_20` z dalszych rozważań** (perfekcyjnie redundantny z `price_zscore_20`
   już w modelu) — to jedyny jednoznaczny wniosek tej rundy.
2. **Przetestować `adx_14` formalnie w walk-forward jako JEDNĄ nową cechę** (CLAUDE.md zasada
   4) — najsilniejszy kandydat na "genuine nową informację", i bezpośrednio istotny dla
   otwartego wątku o błędnej klasyfikacji regime (może zastąpić lub uzupełnić
   `direction_persistence_10` w regule regime — to byłby jednak osobny, jawnie nazwany
   eksperyment na regule, nie na modelu, i wymaga własnej decyzji użytkownika).
3. Jeśli użytkownik chce kontynuować ścieżkę cech mimo słabego sygnału w bloku 3: rozważyć
   `volume_roc_10` (najsilniejsza korelacja w `trend`, ale n=523 — ostrożnie) jako kandydata #2.
4. Alternatywnie: potraktować wynik bloku 3 (brak sygnału w 17 cechach × 2 reżimy) jako czwarty
   niezależny sygnał (po C2.5 progach, C2.6 timeframe, teraz korelacjach) wspierający hipotezę,
   że problem leży głębiej niż w doborze konkretnych cech — i rozważyć rewizję samej hipotezy
   regime-gated (nie tylko jej parametryzacji), zamiast kolejnej rundy inżynierii cech.

## Pełny surowy output

```
[data] 105120 świec, 2025-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00

[blok 1] 9 cech istniejących + 8 kandydatek = 17 razem
  Istniejące (agents/feature_miner.FEATURE_FUNCTIONS): ['atr_14', 'atr_pctrank_20d', 'direction_persistence_10', 'return_lag_1', 'momentum_5', 'ema_diff_9_21', 'volume_zscore_20', 'rsi_14', 'price_zscore_20']
  Nowe kandydatki (ten skrypt, poza registry):         ['bb_width_20', 'realized_vol_20', 'roc_20', 'adx_14', 'bb_pctb_20', 'vwap_deviation_20', 'obv_zscore_20', 'volume_roc_10']
  W modelu Test 1 (MOMENTUM_FEATURES, agents/ml_optimizer.py): ['return_lag_1', 'volume_zscore_20', 'momentum_5', 'ema_diff_9_21']
  W modelu Test 2 (REVERSION_FEATURES, agents/ml_optimizer.py): ['return_lag_1', 'volume_zscore_20', 'rsi_14', 'price_zscore_20']

  Liczba NaN per cecha (warmup wskaźnika, oczekiwane na początku serii):
    atr_14                           14 / 105120
    atr_pctrank_20d                5773 / 105120
    direction_persistence_10         10 / 105120
    return_lag_1                      1 / 105120
    momentum_5                        5 / 105120
    ema_diff_9_21                    20 / 105120
    volume_zscore_20                 19 / 105120
    rsi_14                           14 / 105120
    price_zscore_20                  19 / 105120
    bb_width_20                      19 / 105120
    realized_vol_20                  20 / 105120
    roc_20                           20 / 105120
    adx_14                           27 / 105120
    bb_pctb_20                       19 / 105120
    vwap_deviation_20                19 / 105120
    obv_zscore_20                    19 / 105120
    volume_roc_10                    10 / 105120

[blok 2] Macierz korelacji Spearman cecha-cecha (cały zbiór, zaokrąglone do 2 miejsc):
                          atr_14  atr_pctrank_20d  direction_persistence_10  return_lag_1  momentum_5  ema_diff_9_21  volume_zscore_20  rsi_14  price_zscore_20  bb_width_20  realized_vol_20  roc_20  adx_14  bb_pctb_20  vwap_deviation_20  obv_zscore_20  volume_roc_10
atr_14                      1.00             0.88                      0.01         -0.01       -0.00          -0.04             -0.03   -0.04            -0.02         0.79             0.88   -0.03    0.24       -0.02               0.00          -0.02          -0.02
atr_pctrank_20d             0.88             1.00                      0.02         -0.01       -0.01          -0.05             -0.03   -0.05            -0.02         0.73             0.79   -0.04    0.25       -0.02              -0.00          -0.02          -0.02
direction_persistence_10    0.01             0.02                      1.00         -0.01       -0.01          -0.01              0.13   -0.01            -0.01         0.10            -0.01   -0.01    0.07       -0.01              -0.02          -0.01           0.12
return_lag_1               -0.01            -0.01                     -0.01          1.00        0.37           0.06             -0.01    0.31             0.38        -0.01            -0.00    0.18   -0.00        0.38               0.34           0.29          -0.01
momentum_5                 -0.00            -0.01                     -0.01          0.37        1.00           0.38             -0.04    0.65             0.74        -0.00             0.00    0.43   -0.01        0.74               0.72           0.56          -0.03
ema_diff_9_21              -0.04            -0.05                     -0.01          0.06        0.38           1.00             -0.04    0.87             0.72        -0.03            -0.03    0.89   -0.04        0.72               0.71           0.60          -0.03
volume_zscore_20           -0.03            -0.03                      0.13         -0.01       -0.04          -0.04              1.00   -0.04            -0.04         0.02            -0.05   -0.04    0.05       -0.04              -0.05          -0.03           0.75
rsi_14                     -0.04            -0.05                     -0.01          0.31        0.65           0.87             -0.04    1.00             0.92        -0.03            -0.03    0.84   -0.02        0.92               0.86           0.74          -0.03
price_zscore_20            -0.02            -0.02                     -0.01          0.38        0.74           0.72             -0.04    0.92             1.00        -0.01            -0.01    0.74   -0.01        1.00               0.92           0.78          -0.04
bb_width_20                 0.79             0.73                      0.10         -0.01       -0.00          -0.03              0.02   -0.03            -0.01         1.00             0.85   -0.02    0.43       -0.01               0.01          -0.01          -0.00
realized_vol_20             0.88             0.79                     -0.01         -0.00        0.00          -0.03             -0.05   -0.03            -0.01         0.85             1.00   -0.03    0.27       -0.01               0.01          -0.01          -0.04
roc_20                     -0.03            -0.04                     -0.01          0.18        0.43           0.89             -0.04    0.84             0.74        -0.02            -0.03    1.00   -0.03        0.74               0.74           0.63          -0.03
adx_14                      0.24             0.25                      0.07         -0.00       -0.01          -0.04              0.05   -0.02            -0.01         0.43             0.27   -0.03    1.00       -0.01              -0.02          -0.02           0.02
bb_pctb_20                 -0.02            -0.02                     -0.01          0.38        0.74           0.72             -0.04    0.92             1.00        -0.01            -0.01    0.74   -0.01        1.00               0.92           0.78          -0.04
vwap_deviation_20           0.00            -0.00                     -0.02          0.34        0.72           0.71             -0.05    0.86             0.92         0.01             0.01    0.74   -0.02        0.92               1.00           0.72          -0.04
obv_zscore_20               -0.02            -0.02                     -0.01          0.29        0.56           0.60             -0.03    0.74             0.78        -0.01            -0.01    0.63   -0.02        0.78               0.72           1.00          -0.03
volume_roc_10               -0.02            -0.02                      0.12         -0.01       -0.03          -0.03              0.75   -0.03            -0.04        -0.00            -0.04   -0.03    0.02       -0.04              -0.04          -0.03           1.00

[blok 2] Pary cecha-cecha z |Spearman corr| > 0.7 (potencjalna redundancja):
  price_zscore_20              <-> bb_pctb_20                    corr=+1.000   [mean-reversion (Test 2, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  price_zscore_20              <-> vwap_deviation_20             corr=+0.919   [mean-reversion (Test 2, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  bb_pctb_20                   <-> vwap_deviation_20             corr=+0.919   [mean-reversion (KANDYDAT, Test 2)] / [mean-reversion (KANDYDAT, Test 2)]
  rsi_14                       <-> price_zscore_20               corr=+0.917   [mean-reversion (Test 2, w modelu)] / [mean-reversion (Test 2, w modelu)]
  rsi_14                       <-> bb_pctb_20                    corr=+0.917   [mean-reversion (Test 2, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  ema_diff_9_21                <-> roc_20                        corr=+0.891   [momentum (Test 1, w modelu)] / [momentum (KANDYDAT, Test 1)]
  atr_14                       <-> atr_pctrank_20d               corr=+0.884   [volatility (regime gate)] / [volatility (regime gate)]
  atr_14                       <-> realized_vol_20               corr=+0.880   [volatility (regime gate)] / [volatility (KANDYDAT)]
  ema_diff_9_21                <-> rsi_14                        corr=+0.872   [momentum (Test 1, w modelu)] / [mean-reversion (Test 2, w modelu)]
  rsi_14                       <-> vwap_deviation_20             corr=+0.860   [mean-reversion (Test 2, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  bb_width_20                  <-> realized_vol_20               corr=+0.850   [volatility (KANDYDAT)] / [volatility (KANDYDAT)]
  rsi_14                       <-> roc_20                        corr=+0.839   [mean-reversion (Test 2, w modelu)] / [momentum (KANDYDAT, Test 1)]
  atr_pctrank_20d              <-> realized_vol_20               corr=+0.794   [volatility (regime gate)] / [volatility (KANDYDAT)]
  atr_14                       <-> bb_width_20                   corr=+0.792   [volatility (regime gate)] / [volatility (KANDYDAT)]
  price_zscore_20              <-> obv_zscore_20                 corr=+0.776   [mean-reversion (Test 2, w modelu)] / [volume (KANDYDAT)]
  bb_pctb_20                   <-> obv_zscore_20                 corr=+0.776   [mean-reversion (KANDYDAT, Test 2)] / [volume (KANDYDAT)]
  volume_zscore_20             <-> volume_roc_10                 corr=+0.747   [volume (Test 1 + Test 2, wspólna, w modelu)] / [volume (KANDYDAT)]
  price_zscore_20              <-> roc_20                        corr=+0.743   [mean-reversion (Test 2, w modelu)] / [momentum (KANDYDAT, Test 1)]
  roc_20                       <-> bb_pctb_20                    corr=+0.743   [momentum (KANDYDAT, Test 1)] / [mean-reversion (KANDYDAT, Test 2)]
  roc_20                       <-> vwap_deviation_20             corr=+0.740   [momentum (KANDYDAT, Test 1)] / [mean-reversion (KANDYDAT, Test 2)]
  momentum_5                   <-> bb_pctb_20                    corr=+0.738   [momentum (Test 1, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  momentum_5                   <-> price_zscore_20               corr=+0.738   [momentum (Test 1, w modelu)] / [mean-reversion (Test 2, w modelu)]
  rsi_14                       <-> obv_zscore_20                 corr=+0.737   [mean-reversion (Test 2, w modelu)] / [volume (KANDYDAT)]
  atr_pctrank_20d              <-> bb_width_20                   corr=+0.728   [volatility (regime gate)] / [volatility (KANDYDAT)]
  momentum_5                   <-> vwap_deviation_20             corr=+0.722   [momentum (Test 1, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  vwap_deviation_20            <-> obv_zscore_20                 corr=+0.719   [mean-reversion (KANDYDAT, Test 2)] / [volume (KANDYDAT)]
  ema_diff_9_21                <-> price_zscore_20               corr=+0.716   [momentum (Test 1, w modelu)] / [mean-reversion (Test 2, w modelu)]
  ema_diff_9_21                <-> bb_pctb_20                    corr=+0.716   [momentum (Test 1, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]
  ema_diff_9_21                <-> vwap_deviation_20             corr=+0.709   [momentum (Test 1, w modelu)] / [mean-reversion (KANDYDAT, Test 2)]

[blok 3] Korelacja Spearman cecha-target (label triple-barrier jako -1/0/1)
  UWAGA: to jest OPISOWE/EKSPLORACYJNE na CAŁYM zbiorze (nie OOS) — patrz
  docs/rag/02_cechy_i_leakage.md 'Rozszerzanie feature setu — protokół', punkt 1
  (multiple testing / data dredging). NIE jest to bramka selekcji ani dowód edge'u.
  Jedyny krok o wadze dowodowej: formalny walk-forward JEDNEJ wybranej cechy (przyszły Commit).
  Cechy dopasowane do modelu docelowego regime'u (patrz FAMILY_ASSIGNMENT):

  regime='trend': n=523 świec z etykietą (po odrzuceniu warmup/NaN label)
    volume_roc_10                spearman=-0.0647   [volume (KANDYDAT)] <- KANDYDAT
    volume_zscore_20             spearman=-0.0621   [volume (Test 1 + Test 2, wspólna, w modelu)]
    direction_persistence_10     spearman=+0.0479   [trend-strength (regime gate)]
    realized_vol_20              spearman=+0.0433   [volatility (KANDYDAT)] <- KANDYDAT
    atr_14                       spearman=+0.0372   [volatility (regime gate)]
    adx_14                       spearman=-0.0279   [trend-strength (KANDYDAT, Test 1)] <- KANDYDAT
    obv_zscore_20                spearman=+0.0220   [volume (KANDYDAT)] <- KANDYDAT
    bb_width_20                  spearman=+0.0184   [volatility (KANDYDAT)] <- KANDYDAT
    rsi_14                       spearman=+0.0167   [mean-reversion (Test 2, w modelu)]
    price_zscore_20              spearman=+0.0160   [mean-reversion (Test 2, w modelu)]
    bb_pctb_20                   spearman=+0.0160   [mean-reversion (KANDYDAT, Test 2)] <- KANDYDAT
    vwap_deviation_20            spearman=+0.0159   [mean-reversion (KANDYDAT, Test 2)] <- KANDYDAT
    ema_diff_9_21                spearman=+0.0112   [momentum (Test 1, w modelu)]
    roc_20                       spearman=-0.0085   [momentum (KANDYDAT, Test 1)] <- KANDYDAT
    momentum_5                   spearman=+0.0070   [momentum (Test 1, w modelu)]
    return_lag_1                 spearman=+0.0064   [momentum (Test 1 + Test 2, wspólna)]
    atr_pctrank_20d              spearman=-0.0058   [volatility (regime gate)]

  regime='range': n=22198 świec z etykietą (po odrzuceniu warmup/NaN label)
    realized_vol_20              spearman=-0.0346   [volatility (KANDYDAT)] <- KANDYDAT
    atr_14                       spearman=-0.0291   [volatility (regime gate)]
    bb_width_20                  spearman=-0.0269   [volatility (KANDYDAT)] <- KANDYDAT
    atr_pctrank_20d              spearman=-0.0254   [volatility (regime gate)]
    momentum_5                   spearman=-0.0207   [momentum (Test 1, w modelu)]
    obv_zscore_20                spearman=-0.0206   [volume (KANDYDAT)] <- KANDYDAT
    vwap_deviation_20            spearman=-0.0164   [mean-reversion (KANDYDAT, Test 2)] <- KANDYDAT
    rsi_14                       spearman=-0.0158   [mean-reversion (Test 2, w modelu)]
    return_lag_1                 spearman=-0.0125   [momentum (Test 1 + Test 2, wspólna)]
    price_zscore_20              spearman=-0.0095   [mean-reversion (Test 2, w modelu)]
    bb_pctb_20                   spearman=-0.0095   [mean-reversion (KANDYDAT, Test 2)] <- KANDYDAT
    roc_20                       spearman=-0.0094   [momentum (KANDYDAT, Test 1)] <- KANDYDAT
    volume_roc_10                spearman=+0.0082   [volume (KANDYDAT)] <- KANDYDAT
    ema_diff_9_21                spearman=-0.0074   [momentum (Test 1, w modelu)]
    direction_persistence_10     spearman=-0.0065   [trend-strength (regime gate)]
    volume_zscore_20             spearman=+0.0063   [volume (Test 1 + Test 2, wspólna, w modelu)]
    adx_14                       spearman=+0.0020   [trend-strength (KANDYDAT, Test 1)] <- KANDYDAT

[koniec] Ten skrypt nie wybiera 'zwycięskiej' cechy i nie modyfikuje registry/configu.
  Decyzja, którą JEDNĄ cechę testować formalnie w walk-forward, należy do użytkownika.
```
