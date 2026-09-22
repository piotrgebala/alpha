# C2.6 — odporność hipotezy na timeframe (1h, 4h) vs 5m (2026-09-21)

## ID testu

**C2.6** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.6-timeframe-robustness` (do utworzenia)
- **Poprzedzający stan (master):** Commit 2.5 — kalibracja progów regime, NO-GO, baseline
  (0.7/0.3) pozostaje bez zmian
- **Komenda:** `python3 -m backtest.checkpoint_timeframe_robustness` (pełny sweep, bez `--quick`)
- **Źródło danych:** `data/raw/BTC-USDT-USDT_5m_20250701T000000Z_20260701T000000Z.parquet`
  (105 120 świec 5m, bez dziur) — **1h i 4h AGREGOWANE z tego źródła** przez nową funkcję
  `data.fetch_ohlcv.resample_ohlcv`, NIE pobrane natywnie z giełdy (patrz "Ograniczenie
  środowiska" niżej)
- **Parametry stałe:** `trend_threshold=0.7`/`range_threshold=0.3` (baseline C2.5),
  `ATR_MULTIPLIER=1.5`, `min_barrier_to_cost_ratio=2.0` (bramka kosztowa aktywna, Commit 2d),
  `VERTICAL_BARRIER_CANDLES=12` (**NIEZMIENIONE — patrz "Co na minus"**), `train_days=60/
  test_days=14/step_days=14`, seed sweep 42–51
- **Zmienna eksperymentu:** timeframe danych wejściowych (5m→1h→4h) + `candles_per_day`
  (288→24→6, WYŁĄCZNIE konwersja jednostek dla okna `atr_pctrank_20d`, nie parametr hipotezy)

## Ograniczenie środowiska (ważne dla interpretacji wyniku)

To środowisko (cloud sandbox) **nie ma dostępu sieciowego do Binance** —
`curl https://fapi.binance.com/...` zwraca `403 Forbidden` na poziomie proxy (zweryfikowane
przed uruchomieniem). Natywny fetch danych 1h/4h przez `data.fetch_ohlcv.get_ohlcv_cached` był
więc niemożliwy. Zamiast tego dane 1h/4h zostały **zagregowane z tego samego pliku 5m**
(open=pierwszy, high=max, low=min, close=ostatni, volume=suma; niepełne buckety brzegowe
odrzucone). To NIE jest identyczne z natywnym fetchem — patrz pełne ograniczenia w docstringu
`resample_ohlcv` (`data/fetch_ohlcv.py`). W praktyce: dokładny podział bez reszty
(105 120 / 12 = 8 760 świec 1h; / 48 = 2 190 świec 4h) potwierdza brak przesunięcia granic.

## Co jest zmieniane, a co celowo nie

| Zmienione | Niezmienione (świadomie) |
|---|---|
| timeframe danych (5m→1h→4h) | `trend_threshold`/`range_threshold` = 0.7/0.3 |
| `candles_per_day` (288→24→6) — konwersja jednostek | `ATR_MULTIPLIER` = 1.5 |
| | `min_barrier_to_cost_ratio` = 2.0 |
| | **`VERTICAL_BARRIER_CANDLES` = 12** — patrz "Co na minus" |
| | `direction_persistence_10` — nadal 10 ŚWIEC (nie 10 x timeframe) |

## Wynik — tabela porównawcza (checkpoint)

| timeframe | n_candles | mean_sharpe (seed=42) | klasyfikacja | n_valid_folds/total | stabilność (10 seed) |
|---|---|---|---|---|---|
| 5m (referencja, C2.5 baseline) | 105 120 | -14.31 | NO-GO | 6/40 | std=0,0000 |
| **1h** | 8 760 | **-15.57** | NO-GO | 15/37 | std=0,0000 |
| **4h** | 2 190 | **-8.75** | NO-GO | 7/31 | std=0,0000 |

Rozbicie per reżim (seed=42):

| timeframe | range: mean_sharpe | range: n_valid | trend: mean_sharpe | trend: n_valid |
|---|---|---|---|---|
| 5m | -26,01 | 2/20 | -8,46 | 4/20 |
| 1h | -15,57 | 15/19 | brak (0 transakcji) | 0/18 |
| 4h | -8,75 | 7/19 | brak (0 transakcji) | 0/12 |

## Diagnostyka uzupełniająca: czy bariera-vs-koszt faktycznie się poprawiła?

Powtórzono metodologię Commitu 2d (`diagnose_cost_feasibility.py`, blok 2) na wszystkich trzech
timeframe'ach, per reżim:

| timeframe | regime | mediana bariery (% ceny) | ratio bariera/koszt | wymagana trafność break-even | % świec arytmetycznie nieopłacalnych |
|---|---|---|---|---|---|
| 5m | range | 0,130% | 0,93 | **103,9%** (nieosiągalne) | 56,8% |
| 1h | range | 0,627% | 4,48 | 61,2% | **0,0%** |
| 4h | range | 1,576% | 11,26 | 54,4% | **0,0%** |
| 5m | trend | 0,385% | 2,75 | 68,2% | 0,0% |
| 1h | trend | 1,194% | 8,53 | 55,9% | 0,0% |
| 4h | trend | 2,610% | 18,65 | 52,7% | 0,0% |

Trafność kierunku (udział transakcji z gross_pnl > 0) na realnych transakcjach po bramce
kosztowej (seed=42, regime=`range`, jedyny reżim z transakcjami):

| timeframe | n transakcji | trafność (gross>0) | gross | koszt | net |
|---|---|---|---|---|---|
| 5m (Commit 2d) | 358 | 49,3% | +38 (range) | — | — |
| **1h** | 1 294 | **49,0%** | -567 | 4 315 | -4 882 |
| **4h** | 260 | **41,2%** | -1 186 | 521 | -1 707 |

## Co na plus (+)

- **Mechanizm bariera-vs-koszt DZIAŁA DOKŁADNIE jak przewidziano.** Arytmetyczna
  niewykonalność z Commitu 2d (103,9% wymaganej trafności w `range` na 5m, 56,8% świec
  niewykonalnych) **znika całkowicie** na 1h/4h (0,0% świec niewykonalnych, wymagana trafność
  spada do 54–61%). To bezpośrednio potwierdza diagnozę z Commitu 2d — problem barier-vs-koszt
  jest realny i strukturalnie rozwiązywalny zmianą timeframe.
- Wyniki są **w pełni stabilne** — std=0,0000 na 10 seedach dla obu timeframe'ów, tak jak przy
  każdym poprzednim checkpoincie (5m/2c/2d/2.5). Metodologia trzyma się spójnie.
- `resample_ohlcv` (nowa funkcja, `data/fetch_ohlcv.py`) dała dokładny, bezresztowy podział
  (8 760 i 2 190 świec) — potwierdza brak przesunięcia granic/dziur przy agregacji.
- Skrypt (`backtest/checkpoint_timeframe_robustness.py`) uruchamia identyczny pipeline co
  Commit 6/2c/2d/2.5 bez duplikacji logiki — pełna porównywalność metodologiczna między
  rundami.

## Co na minus (-)

- **Werdykt pozostaje NO-GO na obu timeframe'ach** — naprawienie bariery-vs-kosztu NIE
  przełożyło się na dodatni Sharpe. To rozstrzyga otwarte pytanie z Commitu 2d na niekorzyść
  hipotezy: problem NIE był (wyłącznie) kosztowy, tylko brakiem edge'u kierunkowego.
- **Trafność kierunku w `range` pozostaje na poziomie rzutu monetą (1h: 49,0%) albo GORSZA
  (4h: 41,2%, czyli statystycznie systematycznie zły kierunek, nie tylko brak edge'u).** To
  bezpośrednio potwierdza wniosek z Commitu 2d na nowych danych: edge kierunkowy modelu
  `range` nie istnieje niezależnie od tego, czy transakcja jest arytmetycznie opłacalna.
- **Regime `trend` jest PRAKTYCZNIE PUSTY na 1h/4h (0 transakcji na obu) — gorzej niż na 5m.**
  `direction_persistence_10` pozostał policzony na STAŁEJ liczbie 10 świec (świadoma decyzja,
  patrz tabela wyżej), więc przy 1h oznacza to wymóg 10 GODZIN tego samego znaku zwrotu, a przy
  4h — 40 GODZIN (1,67 dnia) — coraz rzadsze zdarzenie w miarę grubienia timeframe. Test
  odporności na timeframe niechcący pogłębił, nie złagodził, problem z C2.5.
- **`VERTICAL_BARRIER_CANDLES=12` NIE zostało przeliczone** — pozycja jest trzymana 12 świec
  niezależnie od timeframe, co oznacza 1h na 5m, ale **12h na 1h i 48h na 4h**. To świadomy,
  ale realny efekt uboczny: część różnicy w wyniku między timeframe'ami może pochodzić z
  DŁUŻSZEGO czasu trzymania pozycji, nie (tylko) z grubszej granulacji danych. Te dwie zmienne
  (timeframe danych vs horyzont trzymania) NIE zostały rozdzielone w tej rundzie.
- **Dane 4h są bardzo małe (2 190 świec, 524 sklasyfikowane jako `range`)** — przy tak małej
  próbie wynik -8,75/41,2% trafności może częściowo odzwierciedlać szum małej próby, nie
  stabilny efekt. Ostrożna interpretacja: 4h ma NAJMNIEJ wiarygodne dane spośród trzech
  timeframe'ów, mimo najmniej ujemnego Sharpe'a.
- **Dane 1h/4h to agregacja z 5m, nie natywny fetch** — patrz "Ograniczenie środowiska" wyżej;
  nie jest to walidowane względem prawdziwych świec 1h/4h z giełdy.

## Wniosek

Hipoteza "problem jest tylko kosztowy, timeframe 5m jest za drobny" — **FALSYFIKOWANA**.
Naprawienie stosunku bariera/koszt (potwierdzone empirycznie, mechanizm działa) nie przywraca
edge'u kierunkowego w `range`, a `trend` staje się jeszcze rzadszy. To przesuwa ciężar dowodu
dalej w stronę hipotezy "model/cechy nie mają edge'u niezależnie od granulacji danych" — trzeci
niezależny test (po C2.5 progach i teraz timeframe) wskazujący na ten sam kierunek.

## Rekomendacja (nie decyzja)

Zgodnie z regułą routingu checkpointu, dalsze przeszukiwanie parametrów (progi, timeframe)
wygląda na wyczerpane jako kierunek. Do rozważenia przez użytkownika: (a) powrót do rejestru
cech (nowa cecha dla `range`, jedna na raz, OOS); (b) jeśli timeframe ma być badany dalej —
rozdzielić go od `VERTICAL_BARRIER_CANDLES` (przeliczyć horyzont trzymania proporcjonalnie,
zamiast zostawiać 12 świec) jako osobny, jawnie nazwany eksperyment; (c) zdobyć natywne dane
1h/4h (np. przez użytkownika lokalnie, gdzie dostęp do Binance może nie być blokowany) do
walidacji, czy resampling z 5m wprowadza jakiekolwiek zniekształcenie wyniku.

## Pełny surowy output

```
[data] baza 5m: 105120 świec, 2025-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00

========================================================================================
TIMEFRAME: 1h
========================================================================================
[data] 1h: 8760 świec (oczekiwane 8760), 2025-07-01 00:00:00+00:00 -> 2026-06-30 23:00:00+00:00

=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 15, 'n_total_folds': 37, 'fraction_above_threshold': 0.2, 'fraction_le_zero': 0.8, 'fraction_positive_sign': 0.2, 'mean_sharpe': -15.568358111173119}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO             15             19                       0.2               0.8                     0.2   -15.568358
 trend      WARUNKOWY              0             18                       NaN               NaN                     NaN          NaN

std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
TIMEFRAME: 4h
========================================================================================
[data] 4h: 2190 świec (oczekiwane 2190), 2025-07-01 00:00:00+00:00 -> 2026-06-30 20:00:00+00:00

=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 7, 'n_total_folds': 31, 'fraction_above_threshold': 0.2857142857142857, 'fraction_le_zero': 0.7142857142857143, 'fraction_positive_sign': 0.2857142857142857, 'mean_sharpe': -8.7548815434854}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              7             19                  0.285714          0.714286                0.285714    -8.754882
 trend      WARUNKOWY              0             12                       NaN               NaN                     NaN          NaN

std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
TABELA PORÓWNAWCZA — 5m (referencja, Commit 2.5) vs 1h vs 4h
========================================================================================
timeframe  n_candles  mean_sharpe(seed=42) klasyfikacja(seed=42)  n_valid_folds  n_total_folds  stability_std(10 seed)  stabilny
       1h       8760              -15.5684                 NO-GO             15             37                     0.0      True
       4h       2190               -8.7549                 NO-GO              7             31                     0.0      True

[REFERENCJA] 5m (Commit 2.5, baseline 0.7/0.3): mean_sharpe(seed=42)=-14.3078, NO-GO, 6/40 foldów ważnych, std(10 seed)=0.0000.
```

(Pełny plik z per-fold Sharpe dla wszystkich foldów obu timeframe'ów × 10 seedów — output
skryptu jest deterministyczny i odtwarzalny komendą z sekcji "Metadane"; skrócony tu do
klasyfikacji + rozbicia per reżim dla czytelności, zgodnie z konwencją poprzednich rund.)
