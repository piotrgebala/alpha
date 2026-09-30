# Karta hipotezy ML1 — ML na rzadszym handlu (dni zamiast 4h), 11 cech zapisanych z góry (2026-09-30)

> **STATUS: KROK 0 — PAPIER (§0–§13) + §14: reguła progu i uzupełnienia PRZED uczeniem (2026-09-30, pre-rejestracja rundy ML1).** Krok 0: 0 odczytów zwrotu, 0 danych rynkowych.
> Zadanie `zadania/028-ml-wolny-horyzont-cechy-sw.md`, opcja A z decyzji użytkownika 2026-09-30.
> Szkielet z generatora `quant-strategy-catalog/scripts/hypothesis_card.py --family E2 --formula single`
> (rodzina E2 = proporcje long/short, najmocniejszy ślad SW; model łączy też D1, E1, E3, F1, H1, J1 i A2),
> wypełniony ręcznie. Hash repo w chwili zapisu karty: `fff7ce2cc96e3087073b974d825093860f26612f`
> (gałąź `claude/happy-dijkstra-hd1dv6`). Rachunek mocy z wydrukiem: `runs/DRAFT_028_moc.txt`.

## 0. Wynik kroku 0 prostym językiem (zasada 17)

- **Na historii (tor H) test nie ma sensu.** Po ~40 odczytach tych samych lat 2021–2026 nowy odczyt musi
  mieć t ≥ 3,84 (t — ile razy wynik jest większy od swojego szumu). Przy takim progu model na BTC musiałby
  trafiać kierunek w co najmniej 55,5 % transakcji (w najhojniejszym wariancie całej historii) albo 62,5 %
  (na samym 2026). Realny ślad z serii SW przeliczony na 7 dni to ok. 50,8–52,1 %. **NIEMIERZALNA — tor H
  zamknięty bez odczytu.**
- **Na nowych danych (tor P, od dnia zamrożenia modelu) test jest uczciwy, ale bardzo wolny.** Próg
  opłacalności p\* (trafność, przy której zysk pokrywa koszt) to 50,9 %. Żeby przyrząd odróżnił zakładane
  53 % od 50,9 %, potrzeba ok. 2 160 niezależnych transakcji. Na samym BTC (jedna decyzja dziennie, część dni
  bez transakcji, transakcje 7-dniowe nachodzą na siebie) to **ok. 19 lat**; przy hojnym 55 % — **ok. 5 lat**;
  przy realistycznym ≤ 52 % — **ponad 50 lat**.
- **Brama danych:** 5 z 11 cech (zmiana OI, proporcja kont long/short, przewaga kupujących, premia za zmienność,
  podaż na giełdach) **nie ma dziś zbieracza na żywo na serwerze**. Tor P nie mógłby ruszyć bez nowego procesu.
- **Rekomendacja: zamknięcie bez odczytu** (jak zadanie 013). Modelu nie uczyć i nie zamrażać, bo werdykt nie
  przyszedłby w rozsądnym czasie. Decyzja należy do użytkownika (typ `badawcze`).

## 1. Pięć pól katalogu (quant-strategy-catalog)

| Pole | Wartość |
|---|---|
| Zbiór informacyjny | OHLCV własne BTC (4 cechy REVERSION) + funding + pozycjonowanie (OI, proporcja kont long/short, przewaga agresywnych kupujących) + opcje (VRP z DVOL) + on-chain (podaż na giełdach) + sentyment (Fear & Greed) |
| Formuła | **(a) jednoaktywowa: BTC** (wybór w §7, przed danymi, z rachunku mocy) |
| Target | kierunek — etykieta triple-barrier (trzy bariery: zysk, strata, czas) na świecy 1d |
| Horyzont | dzienny: decyzja raz dziennie po zamknięciu świecy, pozycja do bariery, najdłużej 7 dni |
| Status CLAS-5 | cechy ZMIERZONE-odrzucone na 4h (SW, wniosek 90; A2/Y2 dla cech wykresu); horyzont 1d z tymi cechami NIETKNIĘTY. To nie powtórka: inny horyzont i inny koszt względem ruchu (bariera 4,5 % zamiast ~1,5 %). Ale na historii 2021–2026 = kolejny odczyt → próg t 3,84 (wniosek 107). Nowe dane (tor P) = własny licznik, próg 1,96 |

**Sprawdzenie równoważności (zasada 14):** najbliższe rundy: SW etap 2 (te same 7 cech spoza wykresu, XGBoost,
ale 4h, V = 3 świece = 12 h, walk-forward 365/28/28) i Y2 (model kontrolny z 4 cechami REVERSION na 1d, bez cech
spoza wykresu; wniosek 87b: niezmierzony). Równoważnego wariantu (11 cech × 1d × V = 7 dni) brak.

## 2. Mechanizm ekonomiczny — jedno zdanie

Tłum graczy na dźwigni (wysoki funding, szybko rosnące OI, przewaga kont long, chciwość w F&G) płaci
cierpliwszej stronie za zajęcie pozycji przeciwnej, a ten nacisk zanika w ciągu dni, nie godzin (cechy mają
autokorelację dzienną acf1 ≥ 0,98, wniosek 67) — więc na horyzoncie kilku dni koszt 0,08 % dzieli się na ruch
~4,5 % zamiast ~1,5 %.

## 3. Hipoteza (falsyfikowalna, z liczbą)

Jeden model XGBoost uczony na 11 cechach (lista w §4) na świecach 1d BTC od 2021-01-01 do 2025-12-31 i
zamrożony, wydający sygnały od dnia zamrożenia (tor P), ma średni zwrot netto na transakcję > 0 przy
t_neff > 1,96 (t z liczbą niezależnych obserwacji N_eff ≤ n) ORAZ dolny kraniec przedziału trafności powyżej
uogólnionego progu p\* = (L̄ + C)/(W̄ + L̄) (L̄, W̄ — średnia strata i wygrana, C — koszt).

## 4. Jedna zmienna i zamrożony zestaw (zasada 4)

**Zmienna rundy:** horyzont (świeca 1d, V = 7 dni) dla JEDNEGO, z góry zapisanego zestawu 11 cech =
**jeden wariant**. Każda cecha była mierzona osobno w SW (4h), więc zestaw nie wprowadza cech niezmierzonych.
Bez podzbiorów, bez rankingu ważności po wyniku, bez siatki parametrów.

### 4.1. Jedenaście cech (kolejność = kolejność usuwania duplikatów, §5.3)

Kontrakt dostępności: wartość cechy świecy `d` (otwarcie `d` 00:00 UTC, zamknięcie `d+1` 00:00) musi być znana
przed zamknięciem świecy, bo wejście jest po cenie zamknięcia. Źródła dzienne dopina się regułą
`agents/external_features.attach_daily` — wartość dnia `x` widoczna dla świec o `open ≥ x + opóźnienie`
(konserwatywnie: znana już przy OTWARCIU świecy), limit świeżości 7 dni.

| # | cecha (nazwa w kodzie) | źródło | opóźnienie dostępności | przeliczenie na świecę 1d |
|---|---|---|---|---|
| 1 | `return_lag_1` | świece 1d BTCUSDT perp Binance (natywne 1d, baza Y2) | 0 (znane przy zamknięciu) | ln(close_d / close_{d−1}) — `feature_registry.yaml` bez zmian |
| 2 | `volume_zscore_20` | jw., wolumen w BTC (nie w USDT) | 0 | (vol_d − średnia 20 dni) / odch. std 20 dni, trailing |
| 3 | `rsi_14` | jw. | 0 | RSI Wildera, 14 dni |
| 4 | `price_zscore_20` | jw. | 0 | (close_d − średnia 20 dni) / odch. std 20 dni, trailing |
| 5 | `funding_rate` | funding Binance USDT-M BTCUSDT (co 8 h) | rozliczenie znane w chwili rozliczenia | ostatnia stawka rozliczona ŚCIŚLE przed zamknięciem świecy (dla BTC: 16:00 UTC dnia `d`); rozliczenie o 00:00 `d+1` należy do świecy następnej |
| 6 | `oi_change_24h` | archiwum `data.binance.vision` `metrics` BTCUSDT, 5 min | ~1 dzień (archiwum); odczyt w świecy | ln(OI_d / OI_{d−1}), OI_d = ostatni odczyt w (open, open + 23 h 55 min]; OI ≤ 0 → brak (473 zerowe odczyty, P3) |
| 7 | `global_ls_log` | jw., `count_long_short_ratio` | jw. | ln(ostatni odczyt proporcji kont long/short w (open, open + 23 h 55 min]) |
| 8 | `taker_imbalance_24h` | jw., `sum_taker_long_short_vol_ratio` | jw. | średnia log(kupno / sprzedaż agresorów) ze WSZYSTKICH odczytów 5-min w świecy (jedna świeca = 24 h, bez okna kroczącego) |
| 9 | `vrp_30d` | Deribit DVOL BTC 1d | **+1 dzień** (DVOL dnia `x` od świecy `x+1`) | DVOL/100 − zmienność zrealizowana z 30 dziennych log-zwrotów × √365 (na 4h było 180 świec × √(365·6) — zmiana definicji wymuszona świecą, zapisana tu z góry) |
| 10 | `ex_supply_change_7d` | CoinMetrics community `SplyExNtv` | **+2 dni** (dzień `x` od świecy `x+2`) | ln(SplyExNtv_x / SplyExNtv_{x−7}) |
| 11 | `fng_level` | alternative.me Fear & Greed | +4 h → przy regule „znane przy otwarciu” wartość dnia `x` od świecy `x+1` | F&G / 100 |

**Wyłączona z góry:** `toptrader_ls_log` (dziura w archiwum 2021-12 → 2022-12, jak w SW etap 2). Bez likwidacji
(zbierane od 2026-09-25) i bez innych cech.

### 4.2. Test przecieku (zasada 2) — obowiązek PRZED uczeniem (kod jeszcze nie powstaje)

Dla KAŻDEJ z 11 cech na świecy 1d, w `agent_5_compliance/test_leakage.py` (wzorzec SW: 6 testów) i w rejestrze
`agents/feature_registry.yaml` (nowa sekcja 1d), przed pierwszym uczeniem:
1. shift-forward bit w bit: cecha policzona na danych uciętych w dniu `d` = cecha z pełnych danych w dniu `d`;
2. dopięcie odczytów 5-min: odczyt o `open` i o `open + 24 h` nie należy do świecy; późniejsze niewidoczne;
3. opóźnienia źródeł dziennych: DVOL dnia `x` niewidoczny przed świecą `x+1`, CoinMetrics przed `x+2`, F&G przed `x+1`;
4. funding: rozliczenie o 00:00 `d+1` niewidoczne dla świecy `d`;
5. zmienność zrealizowana i okna 20/14 dni wyłącznie wstecz (trailing);
6. etykieta: pierwsza bariera szukana w `d+1 … d+7`, nigdy w `d`.
Standalone przed rejestracją: `clas5-quant/scripts/leakage_check.py` na każdej funkcji `compute_*`.

## 5. Target, model, podział danych

### 5.1. Target i wyjście

- Triple-barrier na świecy 1d: bariery ±`labeling.ATR_MULTIPLIER` × ATR(14) = **±1,5 × ATR 1d** (zasada 3),
  bariera czasowa **V = 7 świec (7 dni)**. Stop-loss w silniku z tego samego mnożnika (`risk_controller.py`
  importuje `ATR_MULTIPLIER`) — bez zmian w `labeling.py` / `risk_controller.py`.
- Wykonanie jak SW (`run_sw_series._simulate`): `simulate_equity`, `candle_minutes = 1440`, wejście
  `ENTRY_LIMIT_CLOSE` (limit po cenie zamknięcia), ważność 1 świeca, `fill_model = FILL_MODEL_PATH`, pojedyncze
  wyjście TP/SL/czas, koszty i bramka kosztowa silnika (`MIN_BARRIER_TO_COST_RATIO = 2,0`), kill-switch domyślny.
  Koszt zakładany w rachunku: 0,08 % na transakcję (SW: 0,080–0,085 %).

### 5.2. Parametry XGBoost — DOKŁADNIE jak SW etap 2 (przepisane z kodu)

Źródło: `backtest/run_sw_series.py::_collect` → `backtest/engine.py::collect_signals` (wartości domyślne) →
`agents/ml_optimizer.py`:

| parametr | wartość | skąd |
|---|---|---|
| `max_depth` | 4 | `DEFAULT_XGB_PARAMS` |
| `eta` (learning_rate) | 0,05 | jw. |
| `objective` / `num_class` | `multi:softprob` / 3 (klasy −1, 0, +1) | jw. |
| `eval_metric` | `mlogloss` | jw. |
| `num_boost_round` | 200 | `NUM_BOOST_ROUND` |
| `early_stopping_rounds` | 20 | `EARLY_STOPPING_ROUNDS` |
| walidacja early stopping | chronologiczny ogon 20 % zbioru uczącego (`DEFAULT_VALIDATION_FRACTION = 0,2`, min. 30 wierszy) | Z17/Z21 |
| wagi klas | `balanced` (`DEFAULT_CLASS_WEIGHT_MODE`) | A1 |
| decyzja | `argmax3` (timeout → brak transakcji), pewność `class` | domyślne `collect_signals` |
| ziarno | 42 (`PRIMARY_SEED`) | `checkpoint_lib` |
| embargo | = V (7 świec) | `collect_signals`: `embargo_candles=None` → V |
| usuwanie duplikatów | \|Spearman\| > 0,9 na zbiorze uczącym → odpada cecha późniejsza w kolejności §4.1 | `DEDUP_ABS_RHO` SW |
| reżim | jeden (`REGIME_ALL`), progi reżimu z `config/settings.yaml` jak SW | SW |

### 5.3. Podział danych — opcja A (decyzja użytkownika 2026-09-30)

- **Jawne odstępstwo od zakresu zadania:** zakres opisywał walk-forward z oknem 365 dni. Decyzja użytkownika
  („model uczony na danych do 2026, od 2026 test”, wybór „a”) **zastępuje walk-forward jednym modelem uczonym
  raz i zamrożonym**. Zasada 1 jest zachowana: żadnego parametru nie dobiera się na danych testowych
  (parametry są przepisane z SW, early stopping patrzy tylko na ogon zbioru uczącego).
- **Uczenie:** świece 1d 2021-01-01 → 2025-12-31 (zasada 20: `data.min_start`), po rozbiegu cech
  (DVOL od 2021-03-24 → faktycznie od ~2021-04).
- **Purging i embargo ≥ 7 dni:** z uczenia wypadają wiersze, których okno etykiety (d+1 … d+7) wychodzi poza
  2025-12-31 (ostatnie 7 dni 2025); między ogonem walidacyjnym a częścią uczącą — embargo V = 7 świec.
- **Zamrożenie:** hash commita, parametry, lista cech, hash pliku modelu — zapisane przed pierwszym sygnałem.
- **2026-01-01 → dzień zamrożenia:** rozbieg bez werdyktu (tylko kontrola mechaniki: czy sygnały się liczą),
  bez zwrotów w raporcie werdyktowym.
- **Tor P:** sygnały dzień po dniu od dnia zamrożenia (nie wcześniej), własny licznik, próg t 1,96.
- Reguła kalendarzowa „średnia faz startu” (wniosek 89) nie dotyczy: decyzja codzienna, brak fazy tygodnia.

## 6. Przyrząd pomiaru i próg z kosztów

- `p` = udział transakcji z `gross_pnl > 0`; werdykt: `t_neff > 1,96` zwrotu netto ORAZ `ci_low(p) > p*`
  (uogólniony). N_eff ≤ n (wniosek 50).
- `break_even_hit_rate(0,0008; 1,5 × ATR)`: ATR 1d 2,5 / 3,0 / 3,5 % → B 3,75 / 4,50 / 5,25 % → **p\* 51,07 /
  50,89 / 50,76 %** (środek 50,89 %). To próg przy wypłacie ±B; przy timeoutach po 7 dniach wypłata nie jest
  symetryczna, więc w odczycie obowiązuje p\* uogólnione.
- Margines w jednostkach zwrotu `(2p−1)·B − C` przy B = 4,5 %: p 52 % → +0,10 %/tr; 53 % → +0,19 %/tr;
  55 % → +0,37 %/tr. (Margines w punktach trafności = p − p\*.)

## 7. Rachunek mierzalności (zasada 18) i wybór formuły

Pełny wydruk: `runs/DRAFT_028_moc.txt` (komendy, hash, kod skryptu). Funkcje: `backtest/metrics.py`
`expected_trades`, `measurability_report`, `wald_half_width`, `min_detectable_hit_rate`, `break_even_hit_rate`.

**Założenie o efekcie (jawne):** ślad SW przed kosztami +0,02 … +0,05 %/tr dotyczył horyzontu 12 h (4h × V 3).
Przeskalowanie na 7 dni (14× dłużej): przy stałej korelacji sygnału ze zwrotem ruch rośnie jak pierwiastek czasu
→ ×3,74 → +0,075 … +0,19 %/tr → **p ≈ 50,8–52,1 %** (realistyczne); liniowo (górna granica, sygnał żyje całe
7 dni bez zaniku) ×14 → p ≈ 53,1–57,8 %. Rachunek liczony przy 52 / 53 / 55 % — hojnie.

**Abstynencja** (udział dni, w które model nie daje kierunku): 0 %, 37,8 % (SW etap 2) i 50 %.
**Nakładanie:** przy V = 7 transakcje BTC nachodzą na siebie; niezależnych 1×, 2× lub 4× mniej niż decyzji.
**Panel:** top-20 ≈ 3 niezależne monety (wniosek 40; tam nawet ≈ 2) oraz wariant ZAWYŻONY 20 niezależnych.

### 7.1. Tor H — historia, próg t 3,84 (`python3 -m backtest.dsr --k 1`)

Wydruk DSR: rejestr 60 wierszy, N = 40 (metoda AU4) → z tą rundą 41: **t 3,84** (DSR 0,95), roczny SR ≥ 1,64
na 5,5 roku; wariant ostrożny N 52 → 53: t 3,94.

| okres | formuła | n (abst 37,8 %, nakł. 2×) | ± przy 1,96 / 3,84 | trafność potrzebna (3,84) | werdykt p 52/53/55 % |
|---|---|---|---|---|---|
| H-A: 2026-01-01 → 09-29 (272 dni; wg opcji A = rozbieg) | (a) BTC | 85 | ±10,7 / ±20,9 pp | 71,8 % | N / N / N |
| H-A | (b) panel ~3 | 254 | ±6,2 / ±12,1 pp | 62,9 % | N / N / N |
| H-WF: walk-forward 365 d, OOS 2022-01 → 2026-09 (1 733 dni) | (a) BTC | 539 | ±4,2 / ±8,3 pp | 59,2 % | N / N / N |
| H-WF | (b) panel ~3 | 1 617 | ±2,4 / ±4,8 pp | 55,7 % | N / N / N |
| H-WF | (b) panel 20 — ZAWYŻONE | 10 779 | ±0,9 / ±1,9 pp | 52,7 % | N / M / M |

Najhojniej na BTC (abstynencja 0, bez nakładania, cała historia): n 1 733, potrzebne 55,5 % → przy 52–55 %
NIEMIERZALNA. **Tor H: NIEMIERZALNA we wszystkich uczciwych wariantach → zamknięty bez odczytu.** Mierzalny
jest tylko panel liczony jak 20 niezależnych monet, a to założenie jest błędne (wniosek 40).

### 7.2. Tor P — prospektywnie od dnia zamrożenia, próg t 1,96

Miesiące do MIERZALNOŚCI (`measurability_report(p, 0,5089, n)`; n = `expected_trades(dni × monety / nakładanie,
abstynencja)`):

| formuła | abst | nakł. | p 52 % | p 53 % | p 55 % |
|---|---|---|---|---|---|
| (a) BTC | 0 | 1× | 256 mies. (~21 lat) | 71 mies. (~6 lat) | **19 mies.** |
| (a) BTC | 0 | 2× | 512 | 142 | 38 |
| (a) BTC | 37,8 % | 2× (**środek**) | > 600 | **228 (~19 lat)** | **61 (~5 lat)** |
| (a) BTC | 50 % | 4× | > 600 | 567 | 150 |
| (b) panel ~3 | 0 | 1× | 86 | 24 | 7 |
| (b) panel ~3 | 37,8 % | 2× (środek) | 274 | 76 (~6 lat) | 21 |
| (b) panel ~3 | 50 % | 4× | > 600 | 189 | 50 |
| (b) panel 20 — ZAWYŻONE | 37,8 % | 2× | 42 | 12 | 4 |

Potrzebne n niezależnych transakcji (ręcznie, `(0,98 / (p − p*))²`): **p 52 % → 7 779; 53 % → 2 155; 55 % → 568**.

**Druga droga kluczowej liczby:** `wald_half_width(n)` = 1,96·√(0,25/n): n 272 → 5,9420 pp (ręcznie 5,9421);
n 2 720 → 1,8790 pp (ręcznie 1,8791) — zgodne do 0,0002 pp (różnica z zaokrąglenia 1,95996 vs 1,96).
Porównanie z tabelą zadania 028 (plik `moc_028.txt` nie istnieje w repo — liczby wzięte z treści zadania):
±8,40 / 5,94 / 4,85 / 1,88 pp i trafności potrzebne 59,29 / 56,83 / 55,74 / 52,77 % — **zgodne co do 0,1 pp**.

### 7.3. Wybór formuły — przed danymi

Reguła wyboru (zapisana razem z rachunkiem, przed jakimkolwiek odczytem): panel (b) wybieram tylko, gdy
w środkowym wariancie (p 53 %, abstynencja 37,8 %, nakładanie 2×) jest szybszy od BTC o WIĘCEJ niż 3× (kara AU2,
wniosek 93: model ML traci ~2/3 mocy wobec prostego przyrządu) ORAZ jego brama danych nie jest gorsza.
Wynik: 76 wobec 228 miesięcy = dokładnie 3,0× (nie więcej), a brama danych panelu jest wyraźnie gorsza
(§8: pozycjonowanie alt dopiero od 2021-12 i bez zbieracza; VRP i podaż on-chain tylko dla BTC). **Wybór: (a) BTC.**

**Werdykt mierzalności:** tor H — NIEMIERZALNA. Tor P (a) BTC — mierzalność dopiero po ~5 latach przy hojnym
p 55 %, po ~19 latach przy p 53 %, nigdy w rozsądnym czasie przy realistycznym p ≤ 52 %.

## 8. Brama danych — pokrycie 11 cech (tor P wymaga danych dziennych na żywo)

Sesja chmurowa nie ma sieci do Binance / Deribit / alternative.me / CoinMetrics ani plików w `data/raw/`
(tylko katalogi dziennika); daty „do” i dziury uzupełnione na serwerze 2026-09-30 (§14.7, wydruk `pokrycie` w `runs/2026-09-30_ml1-wolny-horyzont/raw_output.txt`). Ustalone z kodu i `STATUS.md`:

| cecha | historia (od) — źródło informacji | do / dziury | zbieracz na żywo na serwerze |
|---|---|---|---|
| 1–4 (OHLCV 1d BTC) | od 2021-01-01 (zasada 20; baza Y2 w `data/raw`) | **serwer 2026-09-30:** 2021-01-01 → 2026-09-29, 0 dziur; zgodne z kopią repo głównego do 2026-06-30 co do bitu (§14.7) | **TAK** — `data/fetch_live.py` w przebiegu dziennika (cron serwera 02:30 UTC); **zastrzeżenie:** plik na żywo ma tylko `quote_volume` (USDT), a `volume_zscore_20` w bazie liczono z wolumenu w BTC → niezgodność definicji dla toru P |
| 5 `funding_rate` | historia: cache `get_funding_rate_history_cached` | **serwer:** 2021-01-01 → 2026-09-29 16:00, 0 dni bez rozliczenia | **TAK** — `fetch_live` pobiera funding BTC i członków koszyka od 2025-09-01, nadpisuje co przebieg |
| 6–8 (`oi_change_24h`, `global_ls_log`, `taker_imbalance_24h`) | archiwum `metrics` BTCUSDT 5 min od 2020-09-01, 2 213 dni bez luki, 473 zerowe OI (P3, `STATUS.md`) | **serwer:** OI 2021-01-01 → 2026-09-29, 0 dziur; `count_long_short_ratio` dziura 2021-12-31 → 2022-01-18 (19 d); `sum_taker_long_short_vol_ratio` dziury 2021-12-31 → 2022-01-29 (30 d) i 2022-01-31 → 2022-05-08 (98 d); 7 dni z < 276/288 odczytów | **NIE** — `data/fetch_external.py --only metrics` bez crona; `data/collect_positioning.py` (REST 1h, BTC/ETH/SOL/BNB, 30 dni wstecz) tylko w Harmonogramie Windows komputera użytkownika („Interactive only”), stan po 2026-09-23 nieznany |
| 9 `vrp_30d` | DVOL BTC od 2021-03-24, pokrycie 95,9 % (P3) | **serwer:** 2021-03-24 → 2026-09-30, 0 dziur | **NIE** — `fetch_external --only dvol` bez crona |
| 10 `ex_supply_change_7d` | CoinMetrics `SplyExNtv`, 0 braków (P3) | **serwer:** 2021-01-01 → 2026-09-29, 0 dziur | **NIE** — `fetch_external --only coinmetrics` bez crona |
| 11 `fng_level` | alternative.me (pełna historia) | **serwer:** 2021-01-01 → 2026-09-30, 1 dzień bez wartości (2024-10-26) | **TAK** — `fetch_live.fetch_fng_safe` (poprawka 8); awaria nie zatrzymuje dziennika → możliwe dziury |

Per moneta (formuła b, odrzucona w §7.3): funding i OHLCV 1d — TAK (`fetch_live`, koszyk); pozycjonowanie alt
z archiwum dopiero od 2021-12 (`data/fetch_oi_panel.py`, tylko OI), bez zbieracza na żywo; DVOL tylko BTC/ETH;
podaż on-chain tylko BTC (wniosek 98: darmowe on-chain 4–46 % koszyka); F&G wspólne dla rynku.

**Wynik bramy (BTC):** 6 z 11 cech ma zbieracza na żywo (z zastrzeżeniem wolumenu), **5 nie ma**. Tor P
wymagałby nowego, osobnego procesu (bez zmian w `backtest/live_journal.py`, `data/fetch_live.py` i ich importach
— poprawka dziennika = decyzja użytkownika).

**Komenda do uzupełnienia tabeli na serwerze** (tylko daty i dziury, bez cen i zwrotów):

```bash
cd ~/alpha && PYTHONUTF8=1 .venv/bin/python - <<'EOF'
import glob, pandas as pd
def rep(name, ts):
    t = pd.to_datetime(ts, utc=True).dt.floor("1D").drop_duplicates().sort_values()
    miss = pd.date_range(t.min(), t.max(), freq="1D", tz="UTC").difference(t)
    print(f"{name:60} od {t.min().date()} do {t.max().date()} dni {len(t)} dziury {len(miss)} {[str(x.date()) for x in miss[:10]]}")
m = pd.read_parquet("data/raw/external/binance_metrics_BTCUSDT_5m.parquet")
for c in ("sum_open_interest", "count_long_short_ratio", "sum_taker_long_short_vol_ratio"):
    rep(f"metrics {c}", m.loc[m[c] > 0, "timestamp"])
rep("dvol BTC", pd.read_parquet("data/raw/external/deribit_dvol_BTC_1d.parquet")["date"])
cm = pd.read_parquet("data/raw/external/coinmetrics_btc_1d.parquet"); rep("coinmetrics SplyExNtv", cm.loc[cm["SplyExNtv"].notna(), "date"])
rep("fng", pd.read_parquet("data/raw/external/alternative_fng_1d.parquet")["date"])
for f in sorted(glob.glob("data/raw/*funding*.parquet") + glob.glob("data/raw/live/BTCUSDT_*.parquet") + glob.glob("data/raw/live/*fng*.parquet")):
    d = pd.read_parquet(f); col = next(c for c in ("open_time", "timestamp", "date") if c in d.columns); rep(f, d[col])
EOF
```

## 9. Kryterium sukcesu / porażki i test w granicy dużego n

- **POZYTYWNY (tor P):** t_neff zwrotu netto > 1,96 ORAZ ci_low(p) > p\* uogólnione. Najpierw szukam przecieku,
  potem ogłaszam; dalej wg ADR-09 (spójność, dziennik), nigdy wprost kapitał.
- **NEGATYWNY:** t_neff < −1,96 przy n ≥ `required_trades(0,50; p*)`.
- **NIEROZSTRZYGNIĘTY:** pozostałe przypadki. Werdykt wolno czytać dopiero przy n niezależnych ≥ n z §7.2
  dla zakładanego p (daty odczytu ustala się z góry, jak w wniosku 107).
- **Granica dużego n:** oba warunki wymagają coraz mniejszego efektu przy rosnącym n; na czystym szumie t_neff
  → rozkład N(0,1), więc fałszywy alarm ≤ 2,5 %; brak warunku „przedział zawiera próg” (wniosek 28).

## 10. Warianty i licznik

Jeden wariant: model §4–§5, formuła (a) BTC. **Licznik: NOWA HIPOTEZA ML1, własny, 0/1** (krok 0 nie zużywa).
Tor H i tor P to dwa odczyty tego samego wariantu na różnych danych — tor H zamknięty bez odczytu.

## 11. Reguła STOP

Jeden odczyt toru P (w datach z góry). Zakazane: podzbiory cech, ranking ważności po wyniku, siatka
hiperparametrów, inne V lub mnożniki ATR, douczanie w trakcie testu, dokładanie cech (`toptrader_ls_log`,
likwidacje), odwrócenie kierunku po wyniku, wybór podokresu. Wynik NIEROZSTRZYGNIĘTY nie otwiera wariantu 2.

## 12. Poprzedzające wyniki (zasada 14)

- **SW (wniosek 90):** 7 cech spoza wykresu w modelu 365 dni na 4h: −0,050 %/tr [−0,091; −0,010], t −1,78;
  przed kosztami +0,01 … +0,05 %/tr, IC +0,02 … +0,03 w 5/8 — źródło założonego efektu (§7) i parametrów (§5.2).
- **67 / 87:** cechy dzienne czynią model 4h mniej pewnym; model 60 dni gubił ~85 % przewagi (dlatego uczenie ≥ 365 dni).
- **Y2 / 87b / mapa 007 (013):** BTC 1d z samymi cechami wykresu — niezmierzony, zamknięty bez odczytu (NIEMIERZALNA).
- **40:** 20 monet ≈ 2–3 niezależne. **93 (AU2):** ML traci ~2/3 mocy. **89:** średnia faz startu (tu nie dotyczy).
- **91:** na samym BTC dziennie przyrząd widzi dopiero SR ≥ ~0,86. **107:** próg t 3,84 dla 41. odczytu historii.

## 13. Ścieżka odwrotu

Krok 0 nie zmienia kodu ani konfiguracji. Odwrót: usunąć `runs/DRAFT_028.md`, `runs/DRAFT_028_moc.txt`, akapit ML1
w `docs/mapa_hipotez_2026-10.md`, wniosek 113 i linię licznika ML1 w `runs/INDEX.md`.

## 14. Uzupełnienie PRZED uczeniem (2026-09-30, gałąź `zadanie-028-ml1-wolny-horyzont`) — reguła progu pewności

Dopisane po decyzjach użytkownika 2026-09-30 (opcja A; „Dopisz” — reguła „mało transakcji, wysoka pewność”,
warunki 1–5; „Wykonaj zadanie 28”) i PRZED jakimkolwiek uczeniem modelu, predykcją i obejrzeniem etykiet.
Do chwili commita tej sekcji obejrzano wyłącznie daty i dziury w danych (tryb `pokrycie`) oraz rachunek
mierzalności bez danych rynkowych (tryb `moc`). **Commit z tą sekcją = pre-rejestracja rundy ML1**; jego hash
podaje README rundy `runs/2026-09-30_ml1-wolny-horyzont/` i manifest modelu. Od tego commita reguły z §4–§5
i §14 się nie zmieniają. Sekcje 0–13 zostają jako zapis kroku 0 (w tym rekomendacja zamknięcia, którą użytkownik
świadomie zastąpił decyzją „Wykonaj zadanie 28”).

Skrypt: `backtest/run_ml1_wolny_horyzont.py` (tryby `dane`, `pokrycie`, `moc` istnieją w tym commicie; tryby
`wf`, `zamroz`, `rozbieg` dochodzą po nim i realizują dokładnie §14.4–§14.6).

### 14.1. Reguła progu (warunek 1) — JEDNA wartość, jako udział sygnałów

- **Próg = górne 20 % pewności** wśród sygnałów z kierunkiem (górny kwintyl). Pewność = `signal_confidence`
  w trybie `class` silnika (prawdopodobieństwo wybranej klasy, jak SW etap 2 — bez zmiany trybu).
- **Wartość progu** = kwantyl 0,80 (`numpy.quantile`, interpolacja liniowa) pewności wszystkich sygnałów
  z kierunkiem z predykcji OOS walk-forward 2021-01-01 → 2025-12-31 (§14.4). Sygnał jest „ponad progiem”,
  gdy pewność ≥ wartości progu. Wartość zamraża się razem z modelem (manifest, §14.5).
- **Dlaczego 20 %, zapisane przed danymi:** (a) słowa użytkownika — „ograniczyć liczbę transakcji” i „skupić się
  na wyższym prawdopodobieństwie”; (b) 20 % = górny kubełek tabeli kalibracji (kwintyle, §14.6), więc próg i
  kontrola kalibracji to ta sama liczba, a nie dwa wybory; (c) jedyny precedens projektu (C2.13) użył górnego
  kwartyla (25 %) i dał trafność niższą niż bez progu — nie ma przesłanki, by szukać innej wartości; węższy
  udział (10 %) połowi i tak znikomą liczbę transakcji (§14.3), szerszy (33 %) przestaje być „wysoką pewnością”.
- **Warunek 2:** zero przeszukiwania progów — ani na walk-forward, ani na rozbiegu 2026, ani na torze P.
  Zmiana udziału = nowa hipoteza z nowym licznikiem.

### 14.2. Warianty i licznik (warunek 3)

Tor P raportuje DWA szeregi zapisane z góry: **(1) wszystkie sygnały z kierunkiem**, **(2) sygnały ponad
progiem**. **Licznik wariantów ML1 = 2** (liczony do DSR toru P; licznik własny, nowe dane, próg bazowy t 1,96
z poprawką na 2 warianty przy odczycie). Ta runda nie odczytuje żadnego z nich (brak zwrotu i werdyktu).

### 14.3. Rachunek mierzalności progu (warunek 4, zasada 18) — tor P

Komenda: `PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont moc`. Założenia jak §7: p\* 50,89 %, abstynencja
37,8 %, nakładanie 2×; n = `expected_trades(dni / 2, 0,378, udział)`, werdykt `measurability_report(p, p*, n)`.

| szereg | 6 mies. | 12 mies. | 24 mies. | 60 mies. |
|---|---|---|---|---|
| wszystkie sygnały: n niezależnych / ±Wald / trafność potrzebna | 56,9 / ±13,0 pp / 63,9 % | 113,5 / ±9,2 pp / 60,1 % | 227,0 / ±6,5 pp / 57,4 % | 567,9 / ±4,1 pp / 55,0 % |
| **ponad progiem (20 %)**: n niezależnych / ±Wald / trafność potrzebna | 11,4 / ±29,1 pp / **80,4 %** | 22,7 / ±20,6 pp / **71,3 %** | 45,4 / ±14,5 pp / **65,5 %** | 113,6 / ±9,2 pp / 60,1 % |

- **n rocznie ponad progiem: ~22,7 niezależnych** (227 decyzji z kierunkiem rocznie × 20 % / nakładanie 2).
- Werdykt przy zakładanej trafności 52 / 53 / 55 %: **NIEMIERZALNA** w każdym horyzoncie do 5 lat dla OBU
  szeregów; przy 60 % mierzalne są tylko „wszystkie sygnały” po ≥ 24 mies. Ponad progiem przy p 60 % potrzeba
  ~116 niezależnych = ~5,1 roku; przy 55 % ~25 lat; przy 53 % ~95 lat.
- Prostym językiem: reguła progu zmniejsza liczbę transakcji 5×, więc dowód wymaga 5× dłuższego czekania albo
  dużo wyższej trafności. Żeby po roku cokolwiek wykazać, transakcje ponad progiem musiałyby trafiać w ~71 %
  przypadków — nic w historii projektu tego nie zapowiada.
- **Druga droga (ręcznie, bez `metrics.py`):** ±Wald = 1,96·√(0,25/n): n 18,0 → 23,0988 pp (funkcja 23,0984);
  n 36,3 → 16,2657 (16,2654); n 72,5 → 11,5095 (11,5093) — zgodne do 0,0004 pp (1,96 vs 1,959964).
- **Zasada 18 a ta runda:** NIEMIERZALNA = żaden werdykt nie startuje. Runda ML1 NIE czyta zwrotu ani werdyktu:
  buduje i zamraża model (decyzja użytkownika „Wykonaj zadanie 28”, opcja A), a tor P jako proces i jego odczyt
  to osobne zadania i osobne decyzje użytkownika.

### 14.4. Walk-forward 2021-01-01 → 2025-12-31 (uzupełnienie §5.3; zasada 1)

- Dane: `fetch_window` (min_start 2021-01-01, zasada 20) na natywnych świecach 1d przedłużonych do 2026-09-29;
  ramka do walk-forward UCIĘTA na świecy 2025-12-31 PRZED liczeniem etykiet (etykiety ostatnich 7 świec = NaN
  → purging końca uczenia; 2026 nie wpływa na żadną etykietę).
- Okna **365 / 91 / 91 dni** (uczenie / test / krok), jak Y2 na 1d: przy 28-dniowym teście fold ma 28 wierszy,
  a bezpiecznik silnika `MIN_TRAIN_ROWS = 30` pominąłby każdy fold. Start foldów = pierwsza świeca ramki.
- Silnik bez zmian (`backtest.engine.collect_signals`, parametry §5.2): `REGIME_ALL`, V = 7, `candles_per_day = 1`,
  embargo = V = 7 świec (ogon uczenia przed testem), walidacja early stopping = chronologiczny ogon 20 % uczenia.
  **Sprostowanie §5.3 przed uczeniem:** silnik NIE robi przerwy między częścią uczącą a ogonem walidacyjnym
  (tak samo było w SW); zdanie „między ogonem walidacyjnym a częścią uczącą — embargo V” w §5.3 opisywało silnik
  błędnie. Zostaje silnik jak w SW (parametry „jak SW etap 2”); skutek: liczba drzew bywa wybrana na ogonie,
  którego pierwsze 7 etykiet dzieli ruch z końcem części uczącej — dotyczy tylko liczby drzew, nie danych testowych.
- **Usuwanie duplikatów (§5.2) raz, na pierwszym oknie uczenia** (pierwsza świeca + 365 dni, jak SW): |Spearman|
  > 0,9 → odpada cecha późniejsza w kolejności §4.1. **Ta sama lista cech** trafia do wszystkich foldów i do modelu
  zamrożonego — jedna lista = jeden wariant, a próg z OOS dotyczy tej samej struktury modelu.
- Wiersze z brakiem którejkolwiek cechy (dziury §8: L/S i taker 2021-12-31 → 2022-05-08; DVOL przed 2021-04)
  silnik pomija w uczeniu i w predykcji — raportowane liczbą, bez uzupełniania.
- Z predykcji OOS: wartość progu (§14.1) i tabela kalibracji (§14.6). **Bez zwrotu, t zwrotu i symulacji portfela.**

### 14.5. Model zamrożony (krok 3)

Jeden model: `train_regime_model` na świecach 2021-01-01 → 2025-12-31 z etykietą (purging jak §14.4), lista cech
z §14.4, parametry §5.2, embargo 7, walidacja ogon 20 %, ziarno 42. Zapis: `model_ml1.json` (XGBoost) +
`manifest.json` w katalogu rundy: sha256 pliku modelu, lista cech w kolejności, parametry, `best_iteration`,
wartość progu i udział, hash commita pre-rejestracji i commita kodu, wersje bibliotek, sha256 plików danych.
Bez douczania.

### 14.6. Kalibracja (warunek 5) i rozbieg (krok 4)

- **Kalibracja** na sygnałach OOS walk-forward 2022–2025: 5 kubełków = kwintyle pewności (granice z tych samych
  sygnałów); w każdym n i **trafność sygnału** = udział sygnałów, w których kierunek zgadza się ze znakiem ruchu
  ceny od zamknięcia świecy decyzji do pierwszej bariery ±1,5 × ATR albo do zamknięcia po 7 dniach (z etykiety
  triple-barrier; bez symulacji portfela, bez kosztów, bez zwrotu) + ±Wald. Przyrząd: przy ~800 sygnałach kubełek
  ma ~160 sygnałów → ±7,7 pp (a sygnały nachodzą na siebie — realnie szerzej); wykryje tylko duże różnice.
- **Brak rosnącej trafności** (trafność górnego kubełka ≤ trafność wszystkich sygnałów albo brak dodatniej
  korelacji rang kubełek–trafność) → zapis jako RYZYKO w README i tu; **reguły nie zmienia się** (precedens C2.13).
- **Odczyt historii (wniosek 107, `runs/odczyty_historii.csv`):** tabela kalibracji pokazuje związek sygnału modelu
  z ruchem ceny na historii 2022–2025 → to JEST odczyt programu. Wiersz: `opis-z-wynikiem`, `odczyt_programu = tak`,
  `wariantow = 0` (bez werdyktu i bez wyboru wariantu, jak D1/SZ1/PR1) — w metodzie „z odczytami 0-wariantowymi”
  liczy się za 1. Tor H pozostaje zamknięty: z tej tabeli nie wolno wyprowadzić werdyktu ani wyboru udziału.
- **Rozbieg 2026-01-01 → 2026-09-29:** model z pliku (sprawdzony sha256) → czy sygnały się liczą, ile z kierunkiem,
  jaki udział ponad progiem, ile dni z brakiem cech (per cecha). Bez etykiet, trafności, zwrotu i t.

### 14.7. Brama danych na serwerze (uzupełnienie §8)

Tryb `pokrycie` (2026-09-30 ~18:20 UTC; pliki w `data/raw/ml1`, poza gitem): wszystkie źródła od 2021-01-01
(DVOL od 2021-03-24) do 2026-09-29/30; dziury: `count_long_short_ratio` 19 dni (2021-12-31 → 2022-01-18),
`sum_taker_long_short_vol_ratio` 128 dni (2021-12-31 → 2022-01-29 i 2022-01-31 → 2022-05-08), F&G 1 dzień
(2024-10-26); pozostałe 0. `fetch_window`: 2 098 świec 1d od 2021-01-01 00:00 do 2026-09-29 (filtr zasady 20
działa). OHLCV i funding przedłużone zgodne z kopią repo głównego do 2026-06-30 co do bitu; DVOL różni się
w 1 dniu (ostatni dzień kopii z 2026-09-23 był niepełny), CoinMetrics i F&G bez różnic. Archiwum `metrics`:
kopia do 2026-09-22 + 8 dni z `data.binance.vision` (do 2026-09-29 23:55).
