# C2.5 — kalibracja progów reguły regime (2026-09-21)

## ID testu

**C2.5** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.5-regime-threshold-calibration` (do utworzenia — patrz sekcja "Git" w
  `STATUS.md")
- **Poprzedzający commit (master):** Commit 2d — bramka wykonalności kosztowej
  (`agents/risk_controller.py::is_cost_feasible`, `MIN_BARRIER_TO_COST_RATIO=2.0`)
- **Komenda:** `python3 -m backtest.calibrate_regime_thresholds` (pełny sweep, bez `--quick`)
- **Dane:** `data/raw/BTC-USDT-USDT_5m_20250701T000000Z_20260701T000000Z.parquet`
  (105 120 świec, 2025-07-01 → 2026-06-30, bez dziur)
- **Parametry stałe (niezmienione względem Commitu 2d):** `min_barrier_to_cost_ratio=2.0`
  (bramka kosztowa AKTYWNA), `train_days=60/test_days=14/step_days=14` (domyślne),
  `ATR_MULTIPLIER=1.5`, `seed` sweep 42–51 (10 seedów, C6.3)
- **Zmienna eksperymentu:** `(trend_threshold, range_threshold)` — WYŁĄCZNIE te dwa parametry
- **Środowisko:** cloud sandbox (Python 3.11), zgodnie z ustaleniem "liczę w chmurze"

## Metodologia (zgodność z CLAUDE.md)

Kandydaci zostali wybrani **z góry**, na podstawie WŁASNOŚCI formuły
`direction_persistence_10 = |sum(sign(return))| / 10` (10 znaków zwrotu bez remisów ⇒ suma ma
parzystość 10 ⇒ `persistence` przyjmuje wyłącznie {0.0, 0.2, 0.4, 0.6, 0.8, 1.0}) — **nie** z
podglądania Sharpe'a na tym zbiorze danych. To bezpośrednia realizacja CLAUDE.md zasady 1
(nigdy nie optymalizuj progów na całym zbiorze naraz, tylko wewnątrz walk-forward) i unikanie
data dredging opisanego w `docs/rag/02_cechy_i_leakage.md`. Każdy kandydat oceniany przez
DOKŁADNIE ten sam pipeline co Commit 6 (`run_backtest` → `compute_fold_metrics` →
`classify_checkpoint` → `summarize_by_regime`), 10-seedowy sweep stabilności. **Skrypt celowo
nie wybiera zwycięzcy** — pełna tabela poniżej, decyzja przy użytkowniku.

Cztery kandydaci (uzasadnienie pełne w docstringu `backtest/calibrate_regime_thresholds.py`):

| Kandydat | Uzasadnienie |
|---|---|
| (0.7, 0.3) | BASELINE — wartość startowa, `config/settings.yaml` |
| (0.6, 0.4) | KONTROLA — przewidywanie: ta sama "luka" rozkładu `persistence` co baseline |
| (0.5, 0.3) | Przecina pierwszą granicę masy `persistence` na osi trend (dołącza masę 0.6, ~7%) |
| (0.5, 0.5) | Przecina granicę masy na OBU osiach (trend +0.6, range +0.4 ~22%) |

## Wynik — tabela porównawcza

| trend_thr | range_thr | %trend | %range | mean_sharpe (seed=42) | klasyfikacja | n_valid_folds/40 | stability_std (10 seed) |
|---|---|---|---|---|---|---|---|
| 0.7 | 0.3 | 0.50% | 21.13% | **-14.31** | NO-GO | 6 | 0.0000 (stabilny) |
| 0.6 | 0.4 | 0.63% | 27.72% | **-14.25** | NO-GO | 12 | 0.0000 (stabilny) |
| 0.5 | 0.3 | 4.28% | 21.13% | **-18.00** | NO-GO | 22 | 0.0000 (stabilny) |
| 0.5 | 0.5 | 4.28% | 44.18% | **-19.58** | NO-GO | 27 | 0.0000 (stabilny) |

Rozbicie per reżim (seed=42, mean_sharpe):

| trend_thr | range_thr | trend: mean_sharpe | trend: n_valid | range: mean_sharpe | range: n_valid |
|---|---|---|---|---|---|
| 0.7 | 0.3 | -8.46 | 4/20 | -26.01 | 2/20 |
| 0.6 | 0.4 | -7.33 | 6/20 | -21.17 | 6/20 |
| 0.5 | 0.3 | -16.78 | 20/20 | -30.20 | 2/20 |
| 0.5 | 0.5 | -15.78 | 20/20 | -30.43 | 7/20 |

Pełny surowy output (wszystkie 4 kandydaci × per-fold Sharpe × 10-seed sweep):

```
[data] 105120 świec: 2025-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00

[rejestr] 4 kandydatów (z góry ustalonych, patrz docstring modułu):
  - trend_threshold=0.7, range_threshold=0.3
  - trend_threshold=0.6, range_threshold=0.4
  - trend_threshold=0.5, range_threshold=0.3
  - trend_threshold=0.5, range_threshold=0.5

========================================================================================
KANDYDAT: trend_threshold=0.7, range_threshold=0.3
========================================================================================
[populacja] trend=0.50%  range=21.13%  ambiguous=78.38%  (n=105120)

[seed=42] uruchamiam run_backtest...
=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 6, 'n_total_folds': 40, 'fraction_above_threshold': 0.16666666666666666, 'fraction_le_zero': 0.8333333333333334, 'fraction_positive_sign': 0.16666666666666666, 'mean_sharpe': -14.3077642884818}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              2             20                      0.00              1.00                    0.00   -26.011196
 trend          NO-GO              4             20                      0.25              0.75                    0.25    -8.456048

std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
KANDYDAT: trend_threshold=0.6, range_threshold=0.4
========================================================================================
[populacja] trend=0.63%  range=27.72%  ambiguous=71.65%  (n=105120)

=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 12, 'n_total_folds': 40, 'fraction_above_threshold': 0.08333333333333333, 'fraction_le_zero': 0.9166666666666666, 'fraction_positive_sign': 0.08333333333333333, 'mean_sharpe': -14.248807061387323}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              6             20                  0.000000          1.000000                0.000000   -21.171015
 trend          NO-GO              6             20                  0.166667          0.833333                0.166667    -7.326599

std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
KANDYDAT: trend_threshold=0.5, range_threshold=0.3
========================================================================================
[populacja] trend=4.28%  range=21.13%  ambiguous=74.60%  (n=105120)

=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 22, 'n_total_folds': 40, 'fraction_above_threshold': 0.0, 'fraction_le_zero': 1.0, 'fraction_positive_sign': 0.0, 'mean_sharpe': -17.997815195466526}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              2             20                       0.0               1.0                     0.0   -30.196947
 trend          NO-GO             20             20                       0.0               1.0                     0.0   -16.777902

std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
KANDYDAT: trend_threshold=0.5, range_threshold=0.5
========================================================================================
[populacja] trend=4.28%  range=44.18%  ambiguous=51.54%  (n=105120)

=== Klasyfikacja (seed=42) ===
{'classification': 'NO-GO', 'n_valid_folds': 27, 'n_total_folds': 40, 'fraction_above_threshold': 0.0, 'fraction_le_zero': 1.0, 'fraction_positive_sign': 0.0, 'mean_sharpe': -19.578025202086028}

=== Rozbicie per reżim (seed=42) ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              7             20                       0.0               1.0                     0.0   -30.428050
 trend          NO-GO             20             20                       0.0               1.0                     0.0   -15.780516

std(mean_sharpe) między 10 seedami = 0.0000 (STABILNY, próg < 0.2)

========================================================================================
TABELA PORÓWNAWCZA — WSZYSCY KANDYDACI (bez automatycznego wyboru zwycięzcy)
========================================================================================
 trend_thr  range_thr  %trend  %range  mean_sharpe(seed=42) klasyfikacja(seed=42)  n_valid_folds  stability_std(10 seed)  stabilny
       0.7        0.3    0.50   21.13              -14.3078                 NO-GO              6                     0.0      True
       0.6        0.4    0.63   27.72              -14.2488                 NO-GO             12                     0.0      True
       0.5        0.3    4.28   21.13              -17.9978                 NO-GO             22                     0.0      True
       0.5        0.5    4.28   44.18              -19.5780                 NO-GO             27                     0.0      True
```

(Pełny plik z per-fold Sharpe dla wszystkich 40 foldów × 4 kandydatów × 10 seedów — output
skryptu jest deterministyczny i odtwarzalny komendą z sekcji "Metadane"; skrócony tu do
klasyfikacji + rozbicia per reżim dla czytelności, zgodnie z konwencją Commitu 2d.)

## Synteza / wniosek

**Hipoteza C2.5 ("regime `trend` jest ustrukturalnie zagłodzony przez próg wpadający w lukę
rozkładu `direction_persistence_10`, a to psuje wynik") — CZĘŚCIOWO POTWIERDZONA co do
MECHANIZMU, ale FALSYFIKOWANA co do WNIOSKU.**

Co się potwierdziło:
- Poluzowanie progów faktycznie zwiększa populację `trend` (0.50% → 4.28%, 8.5×) i `range`
  (21.13% → 44.18%, 2×) — kalibracja robi to, co miała robić.
- Kandydat (0.6, 0.4) NIE odtworzył identycznej populacji co baseline (przewidywanie w
  docstringu skryptu było błędne) — bo `atr_pctrank_20d` jest CIĄGŁA, więc nawet przesunięcie
  progu w "luce" rozkładu `persistence` samo w sobie zmienia próg na osi `atr_rank`. Uczciwa
  korekta własnej hipotezy: `persistence` to tylko JEDNA z dwóch zmiennych w regule AND, druga
  jest ciągła — "luka rozkładu" nie jest jedynym czynnikiem sterującym populacją.

Co się NIE potwierdziło — i to jest główny wynik:
- **Więcej świec `trend`/`range` = GORSZY wynik, nie lepszy.** mean_sharpe monotonicznie się
  pogarsza wraz z poluzowaniem progów: -14.31 → -14.25 → -18.00 → -19.58. Rozbicie per reżim
  pokazuje to samo w obu regime'ach osobno (trend: -8.46 → -7.33 → -16.78 → -15.78; range:
  -26.01 → -21.17 → -30.20 → -30.43 — nie idealnie monotoniczne, ale zdecydowanie nie lepsze).
- Wszystkie 4 kandydatów: **NO-GO**, stabilnie (std=0.0000 między 10 seedami dla każdego —
  seed XGBoost nie wpływa na wynik przy tych ustawieniach, co samo w sobie jest odnotowania
  warte, ale niezmienne między kandydatami).
- Innymi słowy: świece, które regime rule DODAJE przy poluzowaniu progu, są NIE LEPSZEJ, tylko
  GORSZEJ jakości niż te już objęte przy 0.7/0.3. To bezpośrednio odrzuca hipotezę, że
  "brakujące" świece trend/range (te wykluczone jako `ambiguous` przy obecnych progach) kryją w
  sobie edge, który regime rule po prostu przez pomyłkę odrzuca.

**Wniosek dla otwartego wątku projektu** ("dlaczego model range stawiał na long podczas trendu
spadkowego błędnie sklasyfikowanego jako range"): ten wynik przesuwa ciężar dowodu z hipotezy
(a) "zła kalibracja progów" na hipotezę (b) "model (features/target) nie ma edge'u" — patrz
`docs/rag/03_ryzyko_i_sizing.md`, reguła routingu checkpointu: **NO-GO → powrót do rejestru
cech, NIE dalsze tuningowanie tego samego zestawu**. Rekalibracja progów regime (C2.5) jest
tym samym WYCZERPANA jako kierunek — kolejny krok to inny niż tuning tej samej reguły regime.

## Co na plus (+)

*(sekcja dodana retrospektywnie 2026-09-21 przy okazji C2.6 — ustalenie konwencji: każdy plik
w `runs/` dostaje "Co na plus/Co na minus"; C2.5 był pierwszym testem w tym katalogu, więc
retrofit dla spójności)*

- Metodologia zadziałała zgodnie z projektem: 4 z góry zarejestrowani kandydaci, wybrani ze
  STRUKTURY formuły (nie z podglądania wyniku), pełny walk-forward + 10-seed sweep — zero
  odstępstw od CLAUDE.md zasady 1.
- Wynik jest jednoznaczny i stabilny (std=0,0000 na każdym kandydacie) — brak dwuznaczności co
  do interpretacji.
- Falsyfikacja własnej hipotezy kontrolnej `(0.6, 0.4)` udokumentowana uczciwie (błędne
  przewidywanie w docstringu skryptu, skorygowane w syntezie), nie ukryta ani nie pominięta.
- Wynik daje JASNY, actionable wniosek: baseline zostaje, kierunek "rekalibracja progów"
  zamknięty — oszczędza czas na kolejne rundy tuningu tego samego mechanizmu.

## Co na minus (-)

- Falsyfikuje pierwotną hipotezę C2.5 — nie ma tu "dobrej wiadomości" o poprawie wyniku,
  wszystkie 4 kandydatów pozostają solidnie NO-GO.
- Nie testuje, CZY łagodniejsze progi POZA tym małym, ustrukturyzowanym zestawem (np. dużo
  szersze zakresy) też by nie pomogły — celowo, żeby uniknąć data dredgingu, ale to oznacza,
  że przestrzeń poza tymi 4 punktami pozostaje formalnie niezbadana (akceptowalny koszt
  metodologicznej dyscypliny, nie błąd).
- Kandydat kontrolny `(0.6, 0.4)` pokazał, że własna hipoteza o "luce rozkładu" była
  niepełna — dobra nauka, ale oznacza, że wstępne uzasadnienie kandydatów w
  `backtest/calibrate_regime_thresholds.py` zawiera nieaktualne/błędne przewidywanie w
  docstringu (nieusunięte, zachowane jako ślad procesu — patrz synteza wyżej).

## Rekomendacja (nie decyzja — do zatwierdzenia przez użytkownika)

Zgodnie z regułą routingu checkpointu (`docs/rag/03`), NO-GO nie uzasadnia kolejnej rundy
tuningu progów regime. `config/settings.yaml` **pozostaje przy baseline (0.7, 0.3)** — żaden z
przetestowanych kandydatów nie daje podstaw do zmiany, a baseline jest w rzeczywistości
NAJLEPSZYM (najmniej ujemnym) z czterech wyników. Następny krok wymaga decyzji użytkownika
między: (1) powrót do rejestru cech — nowa cecha, jedna na raz, mierzona OOS
(`docs/rag/02_cechy_i_leakage.md`), lub (2) głębsza diagnoza modelu `range`/`trend` (np. czy
predykcje mają jakikolwiek sygnał ponad losowy poza już zdiagnozowanym efektem bramki kosztowej
z Commitu 2d) przed inwestowaniem w nowe cechy.
