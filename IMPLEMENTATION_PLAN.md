# CLAS-5 — Plan Implementacji (Faza 0)

> Dokument roboczy do pracy w VS Code. Konsoliduje wszystkie decyzje z sesji planistycznej.
> Jeśli zaczynasz nową sesję Claude Code, podepnij ten plik jako kontekst — zastępuje potrzebę
> przewijania całej wcześniejszej rozmowy.
>
> Ostatnia aktualizacja: 2026-08-01. **Status: Commity 1–6 zaimplementowane i przetestowane
> (86/86 testów). Commit 6 (checkpoint go/no-go) na realnych danych BTC/USDT:USDT: wynik
> **NO-GO**. Commit 2b (diagnoza, zakres uzgodniony: przegląd cech modelu `range`) wykazała, że
> pierwotna przyczyna NO-GO leży gdzie indziej niż sądzono w Commit 6 (kill-switch, nie
> model/cechy) — patrz §5 Commit 2b. Następny krok: NOWA decyzja z użytkownikiem o dalszym
> zakresie (poza cechami — prawdopodobnie `agents/risk_controller.py`).**

---

## 1. Cel i zasada nadrzędna

Oryginalny PRD (CLAS-5, system 5-agentowy do tradingu BTC/ETH perpetual futures) zakładał, że
wszystkie wymagania funkcjonalne — autonomia, Compliance Gate, kill-switch, audytowalność,
dashboard — budowane są równolegle jako gotowa architektura.

**Zasada, którą stosujemy zamiast tego:** nic z Części II PRD (5 agentów, dashboard, Docker) nie
jest budowane, dopóki Faza 0 nie udowodni empirycznie, że istnieje jakikolwiek edge statystyczny
po kosztach transakcyjnych. Architektura bez potwierdzonej hipotezy to precyzyjnie zbudowany
system do tracenia pieniędzy.

---

## 2. Co zmienia się względem oryginalnego PRD

| Element PRD | Problem | Zmiana |
|---|---|---|
| Autonomia od startu | Brak zdefiniowanego edge'u | Faza 0-1 dowodzi edge najpierw, agenci potem |
| LLM w pętli decyzyjnej (150ms) | Wywołanie API LLM to sekundy, nie ms | LLM tylko offline/nadzorczo (recenzja modeli, raporty post-trade) |
| "100% lokalne" + API LLM | Sprzeczność | Hot-path w 100% lokalny; LLM poza hot-pathem |
| 100% pokrycia testami | Nie mówi nic o poprawności finansowej | Property-based testing konkretnych właściwości (leakage, VaR) |
| Multi-repo feature extraction | Ryzyko niekonsystencji + leakage | Jedna biblioteka (TA-Lib), każda cecha przepisana i przetestowana osobno |
| Regime/sizing jako coś do "wyuczenia" | Zużywa ograniczony budżet statystyczny, trudne do audytu | Reguły deterministyczne na start; ML tam, gdzie faktycznie się opłaca (patrz §8) |

---

## 3. Hipoteza tradingowa

**Regime-gated: dwie sprzeczne tezy, rozdzielone regułą, nie połączone w jednym modelu.**

- **Test 1 — Momentum:** w reżimie "trend" (wysoka zmienność + wysoka persystencja kierunku),
  cena kontynuuje ruch.
- **Test 2 — Mean-reversion:** w reżimie "range" (niska zmienność + oscylacja), cena wraca do
  średniej po przegrzaniu.
- **Regime gate:** reguła deterministyczna (nie model), bo (a) w 100% audytowalna dla Compliance
  Gate, (b) nie zużywa dodatkowego budżetu statystycznego z już ograniczonej efektywnej liczby
  próbek.
- **Funding rate:** kandydat na cechę do Test 2 w Fazie 1 — mechanistycznie pasuje do tezy
  "przegrzane pozycjonowanie → odwrócenie". Nie w Fazie 0.
- Test 1 i Test 2 przechodzą przez **cały pipeline osobno** — własny leakage test, własny
  walk-forward, własny go/no-go. Router łączący je to Faza 1, warunkowa na tym, że przynajmniej
  jeden test przejdzie.

---

## 4. Struktura projektu (stan docelowy Fazy 0)

```
clas5_core/
├── README.md                     [DONE] — wejście do repo dla ludzi (GitHub)
├── CLAUDE.md                     [DONE] — krótkie, stabilne instrukcje dla Claude Code
├── IMPLEMENTATION_PLAN.md        ← ten dokument (status commitów, zmienia się często)
├── .github/
│   └── workflows/
│       └── tests.yml              [DONE] — minimalne CI: pytest + spójność registry/kod
├── docs/
│   └── rag/                      [DONE] — pełne uzasadnienia decyzji, per temat
│       ├── 01_hipoteza_i_architektura.md
│       ├── 02_cechy_i_leakage.md
│       ├── 03_ryzyko_i_sizing.md
│       ├── 04_narzedzia_zewnetrzne.md
│       └── 05_metodologia_wytwarzania_i_testow.md
├── requirements.txt              [DONE]
├── config/
│   └── settings.yaml             [DONE]
├── data/
│   ├── __init__.py                [DONE]
│   ├── fetch_ohlcv.py             [DONE]
│   └── raw/                       (cache parquet, generowany przy pierwszym uruchomieniu)
├── agents/
│   ├── __init__.py                 [DONE]
│   ├── feature_miner.py            [DONE]
│   ├── feature_registry.yaml       [DONE]
│   ├── labeling.py                  [DONE, 14/14 testów przechodzi (13 w tests/test_labeling.py + 1 leakage w agent_5_compliance/)]
│   ├── ml_optimizer.py              [DONE, 8/8 testów przechodzi (tests/test_ml_optimizer.py)]
│   └── risk_controller.py           [DONE, 17/17 testów przechodzi (tests/test_risk_controller.py)]
├── agent_5_compliance/
│   └── test_leakage.py              [DONE, 12/12 testów przechodzi]
├── backtest/
│   ├── __init__.py                  [DONE]
│   ├── engine.py                    [DONE, 3/3 testów przechodzi (tests/test_engine.py)]
│   └── costs.py                     [DONE, 7/7 testów przechodzi (tests/test_costs.py)]
└── tests/
    ├── __init__.py                  [DONE]
    ├── test_fetch_ohlcv.py          [DONE, 6/6 testów przechodzi]
    ├── test_labeling.py             [DONE, 13/13 testów przechodzi]
    ├── test_ml_optimizer.py         [DONE, 8/8 testów przechodzi]
    ├── test_costs.py                [DONE, 7/7 testów przechodzi]
    ├── test_engine.py               [DONE, 3/3 testów przechodzi]
    └── test_risk_controller.py      [DONE, 17/17 testów przechodzi]
```

---

## 5. Plan Fazy 0 — commit po commicie

### Commit 1 — Dane `[ZROBIONE]`

`data/fetch_ohlcv.py` — pobieranie OHLCV z Binance USDS-M Futures (perpetuals, nie spot) przez
ccxt, z paginacją i cache w parquet.

- Zakres: **BTCUSDT, 5m, 2025-07-01 → 2026-07-01** (ostatnie ~12 miesięcy). Jeden instrument,
  jeden timeframe.
- `find_gaps()` — raportuje dziury w danych, nie blokuje pipeline'u (fault tolerance z PRD).
- **DO ZROBIENIA PRZED PIERWSZYM URUCHOMIENIEM:** zweryfikować dokładny symbol ccxt przez
  `exchange.load_markets()`. W kodzie jest `"BTC/USDT:USDT"` jako założenie — sandbox, w którym
  to pisałem, nie ma dostępu do API giełdy, więc to nie jest potwierdzone na żywo.

### Commit 2 — Feature registry `[ZROBIONE]`

`agents/feature_miner.py` + `agents/feature_registry.yaml` — 9 czystych funkcji +
`classify_regime()` + `split_by_regime()`.

| Cecha | Wzór | Rola |
|---|---|---|
| `atr_14` | ATR, Wilder, 14 (TA-Lib) | baza |
| `atr_pctrank_20d` | percentyl `atr_14` w trailing 20 dniach (5760 świec) | regime_filter |
| `direction_persistence_10` | \|Σsign(return)\|/10, ostatnie 10 świec | regime_filter |
| `return_lag_1` | ln(close_t/close_t-1) | signal, shared |
| `momentum_5` | ln(close_t/close_t-5) | signal, trend |
| `ema_diff_9_21` | (EMA9-EMA21)/close_t | signal, trend |
| `volume_zscore_20` | (volume-mean20)/std20 | signal, shared |
| `rsi_14` | RSI, Wilder, 14 (TA-Lib) | signal, range |
| `price_zscore_20` | (close-mean20)/std20 | signal, range |

**Regime rule (startowa, do kalibracji):**
```
trend:    atr_pctrank_20d > 0.7  AND  persistence > 0.7
range:    atr_pctrank_20d < 0.3  AND  persistence < 0.3
inaczej:  ambiguous → wyklucz z obu testów
```

### Commit 3 — Test leakage `[ZROBIONE]`

`agent_5_compliance/test_leakage.py` — formalny, parametryzowany pytest dla wszystkich 9 funkcji.

- Metoda: policz cechę na `df[:T]` i `df[:T+k]`, sprawdź identyczność do T.
- **Priorytet:** `atr_pctrank_20d` — największe ryzyko (rolling window musi być trailing, nie
  centered) — pokryty dodatkowym dedykowanym testem (mutacja świec po punkcie odcięcia).
- Nieformalna wersja tego testu już przeszła 9/9 na syntetycznych danych — formalny pytest
  (11 testów: 9 parametryzowanych + 1 dedykowany dla `atr_pctrank_20d` + 1 sanity na zestaw
  cech) potwierdza to empirycznie, 11/11 przechodzi lokalnie.

### Commit 4 — Target + walk-forward split `[ZROBIONE — poza C4.6, odłożone do Commit 5]`

`agents/labeling.py`

**Triple-barrier, ATR-scaled** (nie forward return — odwzorowuje faktyczny mechanizm wyjścia,
zgodny z risk_controllerem):
```
upper barrier:    entry + 1.5 × atr_14
lower barrier:    entry − 1.5 × atr_14
vertical barrier: 12 świec (1h) — timeout
label: która bariera trafiona pierwsza → +1 / −1 / 0
```
Symetryczne progi na start w obu testach (asymetria to Faza 1). Ten sam mnożnik `1.5×ATR` jak w
stop-lossie risk_controllera (Commit 5.5) — musi być skonsystentny.

**Walk-forward split:** okno 2 miesiące train / 2 tygodnie test, przesuwane co 2 tygodnie → ok.
kilkanaście foldów na 12 miesiącach danych. Chronologiczny split ZAWSZE, nigdy random.

**Diagnostyka efektywnej liczby próbek** (nie blokuje, tylko informuje interpretację wyniku z
Commitu 6):
```
policz autokorelację return_lag_1 do lag ~50
N_eff ≈ N / (1 + 2·Σρ_k)
```

**Zaimplementowane i zweryfikowane empirycznie:** `compute_triple_barrier_labels` (reużywa
`compute_atr_14` z `feature_miner.py`, nie duplikuje), `generate_walk_forward_folds`,
`effective_sample_size` — 14/14 testów przechodzi (7 scenariuszy triple-barrier + 3 walk-forward
+ 2 N_eff w `tests/test_labeling.py`, + 1 hypothesis property test wymagany przez DoD dla
`labeling.py`, + 1 formalny test leakage w `agent_5_compliance/test_leakage.py` — C4.5). Mnożnik
ATR i vertical barrier są teraz jedynym źródłem prawdy w `config/settings.yaml` sekcja
`labeling` (C4.2), które `risk_controller.py` będzie musiał czytać w Commicie 5.5. **C4.6
(koszt obliczeniowy pełnego tuningu) celowo NIE zrobione teraz** — wymaga realnych
hiperparametrów XGBoost (Commit 5) do sensownego pomiaru; przeniesione tam.

### Commit 5 — Dwa modele, osobno `[ZROBIONE]`

`agents/ml_optimizer.py`

- **Dwa niezależne XGBoosty**: `model_momentum` (dane Test 1 — świece "trend"),
  `model_reversion` (dane Test 2 — świece "range"). Żadnego wspólnego modelu na tym etapie.
- Start: `max_depth=4`, `learning_rate=0.05`, `n_estimators=200`, `early_stopping_rounds=20` na
  foldzie OOS (nigdy na train).
- Output: `predict_proba`, nie tylko klasa — potrzebne jako `signal_confidence`.
- Okna wskaźników kalibrowane WEWNĄTRZ walk-forward, nigdy na całym zbiorze na raz.

`backtest/costs.py` — taker fee Binance Futures (~0.04–0.05%), funding rate (średnia
historyczna), slippage jako stały bps.
`backtest/engine.py` — pętla: sygnał → risk_controller → PnL z kosztami → equity curve.

**Zaimplementowane i zweryfikowane empirycznie:** `agents/ml_optimizer.py::train_regime_model`
(natywne `xgboost.train()`/`DMatrix`, nie sklearn-wrapper) + `predict_signal` (argmax +
confidence z `predict_proba`, tylko drzewa do `best_iteration`) — 8/8 testów przechodzi
(`tests/test_ml_optimizer.py`). `backtest/costs.py` (fee/funding/slippage, wartości startowe
teraz też w `config/settings.yaml` sekcja `costs`) — 7/7 testów przechodzi
(`tests/test_costs.py`). `backtest/engine.py::run_backtest` — pełny pipeline cechy→labels→
regime→walk-forward→trening/predykcja→sizing→koszty→equity curve — 2/2 testy integracyjne
przechodzi (`tests/test_engine.py`, syntetyczny OHLCV z jawnie odseparowanymi segmentami
trend/range, bo czysto losowe dane dają regime="range" dużo częściej niż "trend", C2.5).

**Decyzja — `_placeholder_risk_controller` (tymczasowy, w `backtest/engine.py`) — ZASTĄPIONY w
Commicie 5.5:** `agents/risk_controller.py` to osobny Commit 5.5 (kontrakt formalny + kill-switch
+ hypothesis property testy, wymagane DoD). Ponieważ `run_backtest` potrzebował jakiegoś sizingu,
żeby policzyć PnL już w Commicie 5, `_placeholder_risk_controller` implementował TĘ SAMĄ formułę
z `docs/rag/03_ryzyko_i_sizing.md` (`size_risk`/`size_leverage`/`min()` + `signal_confidence`
skalujące `risk_per_trade`) — wstrzykiwany przez parametr `risk_controller_fn`. W Commicie 5.5
ten placeholder został usunięty, a `risk_controller_fn` domyślnie wskazuje na prawdziwy
`agents.risk_controller.compute_sizing` — bez żadnej zmiany w pętli `run_backtest`, dokładnie
jak planowano.

**Decyzja — brak modyfikacji `agents/labeling.py`:** PnL wymaga ceny wyjścia z pozycji; dla
timeoutów (label=0.0) to lookup do `close` w świecy `t + exit_bar_offset` w PEŁNYM df.
`agents.feature_miner.split_by_regime()` robi `reset_index(drop=True)`, co gubi tę możliwość —
`backtest/engine.py` świadomie NIE wywołuje `split_by_regime()`, filtruje reżim własnym boolean
maskiem zachowującym oryginalny index (plus defensywny `reset_index(drop=True)` na starcie
`run_backtest`, żeby zagwarantować czysty `RangeIndex`). Zero zmian w już scalonym Commicie 4.

**Decyzja — chronologia ponad reżimy:** modele trenowane per-regime per-fold niezależnie, ale
equity liczone w JEDNYM sekwencyjnym przebiegu po wszystkich sygnałach z obu reżimów, sortowanych
po `timestamp` — inaczej trades z trend/range (przeplatające się w czasie) dałyby błędną
chronologię compoundingu equity.

**C4.6 — pomiar częściowy (patrz TASKS.md):** jedno `train_regime_model` (produkcyjne
hiperparametry, 200 rund, early stopping wyłączony) na 30k wierszy × 4 cechy: **0.436s**
(~2.2ms/rundę) na Ryzen 7950X3D. Pełny grid search pozostaje niezmierzony — do zrobienia przy
faktycznej kalibracji hiperparametrów (Commit 6 / Faza 1).

### Commit 5.5 — Risk controller + interfejs `[ZROBIONE]`

`agents/risk_controller.py`

**Kontrakt (ml_optimizer → risk_controller):**
```
ml_optimizer emituje:
  { signal_direction: -1|0|1, signal_confidence: float,
    regime: "trend"|"range", atr_14: float, entry_price: float }

risk_controller zwraca:
  { position_size: float, stop_price: float, take_profit_price: float }
```

**Sizing (leverage cap zawsze wygrywa, jawnie):**
```
size_risk     = (equity × risk_per_trade) / (1.5 × atr_14)
size_leverage = (equity × max_leverage) / entry_price
position_size = min(size_risk, size_leverage)
```
- `risk_per_trade` = 0.5% equity (wartość startowa)
- `max_leverage` = 3x (wartość startowa, konserwatywnie)
- `signal_confidence` skaluje `risk_per_trade` liniowo (słabszy sygnał → mniejsza pozycja)

**Kill-switch:** prosta reguła już w backteście Fazy 0 — drawdown equity > X% od peaku →
zatrzymaj generowanie nowych sygnałów. Cel: zobaczyć historycznie, jak często by się aktywował.

**Zaimplementowane i zweryfikowane empirycznie:** `agents/risk_controller.py` — dwuwarstwowy
design: `compute_position_size` (czysty numeryczny rdzeń: `equity`, `atr_14`, `entry_price` →
`float`, matchuje dokładnie szablon hypothesis z `docs/rag/05_metodologia_wytwarzania_i_testow.md`)
+ `compute_sizing` (pełny kontrakt dict, drop-in replacement dla `risk_controller_fn` w
`backtest/engine.py::run_backtest`) + `check_kill_switch`. 17/17 testów przechodzi
(`tests/test_risk_controller.py`: 13 jednostkowych + 4 hypothesis property, w tym adaptacja
1:1 szablonu `test_position_size_never_exceeds_leverage_cap` z docs/rag/05).

**Trzy decyzje podjęte podczas planowania (zamiast rekomendowanych domyślnych wartości):**

1. **Próg kill-switcha = 15% drawdown od peaku equity** (nie rekomendowane 20%) —
   `KILL_SWITCH_DRAWDOWN_PCT = 0.15` w `agents/risk_controller.py`, zdublowane w
   `config/settings.yaml` sekcja `risk.kill_switch_drawdown_pct`. Konserwatywniejszy próg =
   kill-switch aktywuje się wcześniej, spójne z ogólnym duchem Fazy 0 (minimalizować ryzyko przed
   udowodnieniem edge'u).
2. **Re-check dynamiczny, nie permanentny latch** — `check_kill_switch` jest wywoływane PRZED
   sizingiem KAŻDEGO sygnału (nie tylko raz), więc kill-switch wznawia normalną pracę, gdy equity
   odzyska się z powrotem powyżej progu. Alternatywa (permanentny latch, wymagający ręcznego
   resetu) odrzucona — w Fazie 0 backtest ma pokazać, JAK CZĘSTO próg by się aktywował, a
   permanentny latch zniekształciłby ten pomiar (jedna aktywacja ubijałaby resztę okresu testowego).
3. **Sygnały stłumione przez kill-switch trafiają do `trades` DataFrame** (kolumna
   `kill_switch_active: bool`, `position_size=0.0`, `exit_price=NaN`, `equity_before==equity_after`)
   zamiast do osobnej listy `kill_switch_events` — jeden ustrukturyzowany trade journal, nie dwa
   równoległe źródła prawdy o tym, co działo się w czasie. Audytowalność: `trades[trades["kill_switch_active"]]`
   pokazuje dokładnie, kiedy i jak często kill-switch by się aktywował.

Integracja w `backtest/engine.py::run_backtest`: `peak_equity` (running max equity) śledzony w
pętli PRZED każdym sygnałem (bez lookahead — tylko przeszłość/teraźniejszość), `check_kill_switch`
sprawdzany przed wywołaniem `risk_controller_fn`. Nowy parametr `kill_switch_drawdown_pct`
(domyślnie `KILL_SWITCH_DRAWDOWN_PCT`) — nadpisywalny, analogicznie do innych parametrów silnika.
Dodatkowy test integracyjny `test_run_backtest_kill_switch_suppresses_signals_after_large_drawdown`
(`tests/test_engine.py`) — oversized stub `risk_controller_fn` (~50x normalnego stosunku
notional/equity, celowo ignorujący normalny cap 3x) deterministycznie wymusza drawdown > 15% bez
zależności od jakości predykcji modelu (gross_pnl i cost skalują się liniowo z position_size, więc
samo powiększenie position_size nie zmienia proporcji zysk/koszt — ale w połączeniu z choćby
jedną naturalnie występującą błędną predykcją kierunku daje duży wystarczający swing equity).

### Commit 6 — Checkpoint go/no-go: TRZY ścieżki `[ZROBIONE — wynik: NO-GO]`

| Wynik | Kryterium (startowe) | Decyzja |
|---|---|---|
| **GO** | Sharpe po kosztach > 0.5 w >60% foldów, zgodny znak | Faza 1: regime router + funding rate do Test 2 |
| **WARUNKOWY** | Sharpe 0–0.5 lub niestabilny znak między foldami | Max 3 iteracje protokołu "jedna cecha na raz", potem decyzja ponownie |
| **NO-GO** | Sharpe ≤ 0 w większości foldów | Wróć do Commit 2 — inna hipoteza/cechy, NIE tuning tego zestawu |

Sprawdzić też: stabilność wyniku przy losowym seedzie modelu (overfitting sanity check), wynik
osobno per reżim rynkowy (2023 niska zmienność vs 2024-25 era ETF).

**Metodologia (ustalona z użytkownikiem, brak w docs/rag — trzeba było doprecyzować przed
implementacją):** Sharpe per trade (risk-free=0, zwrot = net_pnl/equity_before, wyklucza
kill-switch), annualizacja `sqrt(trades_per_year)` z częstości transakcji per-fold (nie stała
globalna). C6.4 zinterpretowane jako podział wg REŻIMU (trend vs range), nie kalendarzowo —
realny zakres danych (2025-07→2026-07) nie sięga 2023. C6.3: 10 seedów (42-51), stabilny =
std zagregowanego Sharpe < 0.2. Implementacja: `backtest/metrics.py` (czyste funkcje, testy w
`tests/test_metrics.py`) + `backtest/run_checkpoint.py` (orkiestracja na realnych danych, poza
pytest).

**Wynik na realnych danych** (BTC/USDT:USDT 5m, Binance USDS-M Futures, 2025-07-01→2026-06-30,
105 120 świec, zero dziur — pierwsze rzeczywiste dane w tym projekcie, C1.3 potwierdzone przy
okazji):

- **C6.1/C6.2 — klasyfikacja ogólna: NO-GO.** Tylko 1 z 40 foldów (regime×fold_idx, 20 trend +
  20 range) miał policzalny Sharpe (≥2 transakcje, niezerowa wariancja): `range`, `fold_idx=0`,
  35 transakcji, Sharpe = **-65.43**. Pozostałe 39 foldów: NaN (brak transakcji albo fold
  pominięty przez `min_train_rows=30`).
- **C6.3 — stabilność:** 10 seedów (42-51) dały IDENTYCZNY mean_sharpe=-65.4333 na każdym
  (std=0.0000 < próg 0.2) → formalnie stabilne, ale głównie dlatego, że tylko ten jeden fold
  kiedykolwiek generuje transakcje i jego wynik okazał się w tym przebiegu niezależny od seeda
  modelu (płytkie drzewa, mały feature set — mało miejsca na wariancję od samego seeda).
- **C6.4 — per reżim:**
  - `trend`: **WARUNKOWY** w praktyce nieoceniony — WSZYSTKIE 20 foldów pominięte przez
    `min_train_rows`, bo 14-dniowe okno testowe konsekwentnie miało <30 świec sklasyfikowanych
    jako `trend` (typowo 6-29, patrz TASKS.md C6.1 Uwagi). To empiryczne potwierdzenie ryzyka z
    §7 ("regime trend może być rzadki"), nie nowe odkrycie — ale teraz na realnych danych, nie
    tylko syntetycznych.
  - `range`: **NO-GO** — model wygenerował sygnał tylko w 1 z 20 foldów; w pozostałych 19
    `predict_signal` zwracał wyłącznie `direction=0` (brak transakcji). **[BŁĘDNE — patrz korekta
    poniżej i Commit 2b.]**
- **Interpretacja (ważne dla decyzji o Commit 2):** Sharpe=-65.43 z pojedynczego foldu (35
  transakcji, mean_return/std_return≈-2.17 przed annualizacją) to artefakt małej próby — N_eff
  effektywnie bardzo mały (docs/rag/03 caveat), więc dosłowna wartość liczbowa niesie mało
  informacji. Bardziej wiarygodny sygnał to STRUKTURALNY: model `range` prawie nigdy nie handluje,
  a `trend` prawie nigdy nie ma wystarczających danych do wytrenowania/oceny w obecnej strukturze
  walk-forward. To sugeruje, że powrót do Commit 2 powinien objąć w szczególności C2.5 (kalibracja
  progów 0.7/0.3) i/lub przegląd feature setu pod kątem modelu `range`, a nie tylko "inne cechy"
  ogólnikowo — ostateczny zakres do ustalenia z użytkownikiem przed startem.
- **KOREKTA (Commit 2b, 2026-08-01):** oba powyższe zdania okazały się mylące co do przyczyny —
  sugerowały problem z modelem/cechami `range`. Diagnoza C2b.1/C2b.1b (patrz Commit 2b niżej)
  pokazuje, że `predict_signal` faktycznie zwraca `direction != 0` w ~99-100% wierszy testowych w
  KAŻDYM z 20 foldów `range` (nie tylko 1). Prawdziwa przyczyna "1/20 foldów z transakcjami" to
  kill-switch (`agents/risk_controller.py::check_kill_switch`), permanentnie stłumiony od
  2025-09-27 (3 dni w fold_idx=0) do końca datasetu (2026-06-30) po serii wczesnych strat.
  Rekomendacja "C2.5 i/lub przegląd cech `range`" z powyższego akapitu jest nieaktualna — patrz
  Commit 2b dla poprawionej rekomendacji zakresu.

### Commit 2b — Diagnoza NO-GO: przegląd cech modelu `range` `[W TRAKCIE — zablokowane na nowej decyzji użytkownika]`

**Kontekst i uzgodniony zakres (ustalony z użytkownikiem przed startem, 2026-08-01):** powrót do
Commit 2 ograniczony WYŁĄCZNIE do przeglądu/rewizji feature setu modelu `range`
(`REVERSION_FEATURES`) — jawnie WYKLUCZONE tej rundy: rekalibracja progów regime (C2.5) i zmiana
mnożnika ATR triple-barrier. Plan: (1) diagnoza przyczyny [C2b.1], (2) jeśli diagnoza wskaże na
niewystarczające cechy — dodać JEDNĄ kandydującą cechę [C2b.2], (3) ponowny checkpoint [C2b.3].

**C2b.1 — Diagnostyka (`backtest/diagnose_range_signal.py`, poza pytest, jak
`run_checkpoint.py`):** read-only skrypt reprodukujący dokładnie trening/predykcję
`backtest.engine._collect_candidate_signals` per fold `range` (te same domyślne
train/test/step_days, `train_regime_model`/`predict_signal`, seed=42), ale raportujący dodatkowo:
rozkład klas triple-barrier label (train/test), `booster.get_score(importance_type="gain")`, i
PEŁNY rozkład `signal_confidence` (nie tylko wiersze z `direction != 0`, w odróżnieniu od
`_collect_candidate_signals`, który je odrzuca).

**Wynik C2b.1 (nieoczekiwany):** model `model_reversion` sygnalizuje (`direction != 0`) w
~99-100% wierszy testowych w KAŻDYM z 20 foldów `range` (nie w 1 na 20, jak zapisano pierwotnie w
Commit 6) — łącznie 17 989 sygnałów spośród 17 989 wierszy testowych z policzalnym labelem.
Confidence umiarkowana, ale sensowna (~0.44-0.50, baseline losowy dla 3 klas = 0.33). Feature
importance (gain) niezerowa i zmienna między foldami dla wszystkich 4 cech (`rsi_14` najsilniejsza,
0.9-4.7 w zależności od foldu; `return_lag_1` najsłabsza, ale nigdy zero). Rozkład labeli
train/test w każdym foldzie sensownie zbalansowany (~45% +1, ~45% -1, ~9-13% timeout/0) — brak
strukturalnego problemu z brakiem zdarzeń +1/-1.

**Wniosek C2b.1:** model NIE jest wąskim gardłem. Hipoteza "cechy `range` są za słabe, model rzadko
sygnalizuje" — którą ta runda miała zweryfikować — jest FAŁSZYWA. Dodanie nowej cechy do
`REVERSION_FEATURES` (C2b.2) nie zaadresowałoby rzeczywistej przyczyny "1/20 foldów z
transakcjami" w Commit 6.

**C2b.1b — Weryfikacja rzeczywistego mechanizmu "0 transakcji":** bezpośrednia inspekcja
`run_backtest(raw_ohlcv, seed=42)["trades"]`/`["folds_summary"]` (ad hoc, bez zmian w kodzie
pipeline'u):
- `folds_summary` potwierdza C2b.1: KAŻDY z 20 foldów `range` ma dziesiątki-tysiące sygnałów
  kandydujących (`n_signals`, PRZED sizingiem/kill-switchem), od 71 (fold 9) do 1713 (fold 10).
- Łącznie **18 135** wierszy w `trades` (obie strategie/foldy razem) — z czego **18 100 (99,8%)**
  ma `kill_switch_active=True`, tylko **35** to realne transakcje (`kill_switch_active=False`) —
  dokładnie zgodne z liczbą "35 transakcji" zaraportowaną w Commit 6 dla `range` fold_idx=0.
- Kill-switch uruchamia się pierwszy raz **2025-09-27 01:55 UTC** — w fold_idx=0 dla `range`, ~3
  dni w 14-dniowe okno testowe tego foldu, po ok. 9-10 stratnych transakcjach pod rząd (każda
  -0,5% do -0,6% equity). Equity spada z 10 000 do **8469,93** (drawdown 15,30%, tuż nad progiem
  15%) i **zamraża się na tej wartości DO KOŃCA datasetu** (2026-06-30) — kill-switch pozostaje
  aktywny przez pozostałe ~9 miesięcy backtestu, bez jednego wyjątku.
- Mechanizm: `check_kill_switch` jest poprawnie bezstanowy i "dynamiczny" (nie permanentny latch —
  wznawia się, gdy equity wróci powyżej progu, zgodnie z docstringiem i C5.5.5). Problem to
  DEADLOCK EMERGENTNY z interakcji z resztą pętli `run_backtest`: gdy sygnał jest stłumiony,
  `position_size=0.0` → `net_pnl=0.0` → equity się NIE zmienia → `peak_equity` też się nie zmienia
  → drawdown zostaje dokładnie tam, gdzie było w momencie stłumienia. Equity może wrócić ponad próg
  WYŁĄCZNIE dzięki realnej transakcji — a realna transakcja jest właśnie tym, co jest stłumione.
  W obecnej architekturze Fazy 0 (brak mark-to-market otwartych pozycji, brak żadnego innego
  źródła ruchu equity) ten deadlock jest matematycznie nieunikniony, gdy tylko drawdown raz
  przekroczy próg wystarczająco wcześnie w backteście.
- Osobne, jeszcze niezbadane pytanie: DLACZEGO pierwsze ~9-10 transakcji `range` fold 0 straciło
  tak konsekwentnie (jakość sygnału na starcie datasetu, koszty transakcyjne, formuła sizingu,
  czy zbieg okoliczności) — to POZA zakresem tej rundy (tylko przegląd cech), zostawione jako
  input do decyzji poniżej.

**Status i decyzja wymagana:** C2b.2 (dodanie cechy) WSTRZYMANE — jego przesłanka jest obalona
przez C2b.1/C2b.1b. Wymagana NOWA decyzja z użytkownikiem o zakresie dalszej pracy — prawdopodobnie
dotyczy `agents/risk_controller.py` (mechanizm odzyskiwania kill-switcha i/lub formuła sizingu
powodująca wczesną serię strat), co jest OSOBNYM zakresem od "przeglądu cech modelu `range`"
uzgodnionego na tę rundę i wymaga własnego przeczytania docs/rag/03 przed jakąkolwiek zmianą
(CLAUDE.md, sekcja "Zanim zmienisz coś w risk_controller.py"). Diagnostyczny skrypt
`backtest/diagnose_range_signal.py` zachowany jako trwałe narzędzie (nie jednorazowy scratch) —
przydatny niezależnie od tego, jaki zakres zostanie wybrany dalej.

### Commit 2c — Kill-switch: przyczyna serii strat + mechanizm cooldown/re-arm `[ZROBIONE]`

**Kontekst i uzgodniony zakres (2026-08-01):** użytkownik zatwierdził ("1.yes 2.yes") rozszerzenie
zakresu na `agents/risk_controller.py`/`backtest/engine.py`, jedną rundą: (1) diagnoza PRZYCZYNY
wczesnej serii strat wywołującej kill-switch, (2) naprawa mechanizmu deadlocka. Wybór konkretnego
mechanizmu naprawy delegowany do decyzji inżynierskiej ("tak jak uważasz za najlepsze"). Przeczytano
`docs/rag/03_ryzyko_i_sizing.md` w całości przed zmianą (CLAUDE.md) — potwierdzono, że kill-switch
Fazy 0 ma cel WYŁĄCZNIE obserwacyjny ("zobaczyć historycznie, jak często by się aktywował") i docs
NIE przepisują żadnego konkretnego mechanizmu odzyskiwania — to była faktycznie otwarta przestrzeń
projektowa, nie nadpisanie istniejącej decyzji.

**C2c.1 — Diagnostyka przyczyny serii strat (`backtest/diagnose_kill_switch_trigger.py`, poza
pytest, jak `run_checkpoint.py`/`diagnose_range_signal.py`):** read-only skrypt inspekcji 35
realnych transakcji sprzed permanentnego zadziałania kill-switcha — rozbija zlumpowany koszt
(`cost`) z powrotem na `fee`/`funding`/`slippage`, klasyfikuje każdą transakcję jako
`gross_pnl_negative` (zły kierunek) albo `cost_ate_gain` (dobry kierunek, ale koszt > zysk brutto).

**Wynik C2c.1:** 100% z 35 transakcji miało `signal_direction=1.0` (wyłącznie long) w okresie
2025-09-24→2025-09-27, gdy cena BTC trendowała W DÓŁ (~113 047→~109 400, ok. -3,6%), sklasyfikowanym
jako reżim `range`. **26/35 (74%)** miało `gross_pnl < 0` (genuinie zły kierunek — model obstawiał
long podczas trwałego spadku). **9/35** miało `gross_pnl >= 0`, ale koszt transakcyjny (~28-38 na
transakcję) przewyższał zysk brutto (~21-23) — też netto ujemne. Średni koszt jako % nominału:
fee≈0,100%, funding≈0,0004%, slippage≈0,040%, razem≈0,140%.

**Wniosek C2c.1:** kill-switch NIE działał wadliwie — poprawnie wykrył realną, trwałą serię strat.
Głębsza przyczyna (dlaczego model konsekwentnie obstawiał long podczas trwałego spadku
sklasyfikowanego jako `range`, i dlaczego zyski były mniejsze niż koszty) to osobne pytanie o
jakość sygnału/klasyfikację reżimu — jawnie POZA zakresem tej rundy (wymagałoby C2.5 albo rework
modelu/cech, oba explicite wykluczone z wcześniejszych ustaleń).

**C2c.2 — Mechanizm naprawy deadlocka (decyzja inżynierska, delegowana przez użytkownika):**
**cooldown/re-arm** — `backtest.engine.run_backtest` śledzi `kill_switch_tripped_at` (moment
pierwszego nieprzerwanego zadziałania) i po `kill_switch_cooldown_days` (nowy parametr, domyślnie
**7.0**, `agents.risk_controller.KILL_SWITCH_COOLDOWN_DAYS`, zdublowany w `config/settings.yaml`)
ciągłej suppresji resetuje `peak_equity` do bieżącego (zamrożonego) equity, dając strategii kolejną
szansę. `check_kill_switch` sam w sobie NIE zmienia się (nadal czysty/bezstanowy) — decyzja "czy
już czas na re-arm" wydzielona jako osobna czysta, testowalna funkcja
`agents.risk_controller.should_rearm_kill_switch(kill_switch_tripped_at, current_timestamp,
cooldown_days)`, wywoływana z pętli `run_backtest` PRZED `check_kill_switch` w każdej iteracji.
Odrzucone alternatywy: mark-to-market otwartych pozycji (zbyt duża zmiana architektury Fazy 0 na tę
rundę), zmiana formuły sizingu (nie adresuje deadlocka, tylko wielkość pojedynczej straty).

**Testy (DoD, docs/rag/05):** `tests/test_risk_controller.py` — 4 testy jednostkowe + 3 hypothesis
property tests dla `should_rearm_kill_switch` (m.in. `kill_switch_tripped_at=None` → zawsze False
niezależnie od pozostałych argumentów; dla dowolnego `cooldown_days`+`extra_days>=0` → zawsze True;
dla dowolnego elapsed < cooldown_days → zawsze False). `tests/test_engine.py` — nowy integracyjny
`test_run_backtest_kill_switch_re_arms_after_cooldown` (oversized `risk_controller_fn` wymusza trip
deterministycznie, `kill_switch_cooldown_days=0.01` wymusza szybki re-arm, asercja że przynajmniej
jedna PÓŹNIEJSZA transakcja ma `kill_switch_active=False`). Pełny zestaw: **94/94 przechodzi**.

**C2c.3 — Ponowny checkpoint po naprawie (`backtest/run_checkpoint.py`, realne dane, domyślny
`kill_switch_cooldown_days=7.0`):**

| Metryka | Przed (Commit 6/2b, deadlock) | Po (Commit 2c, cooldown/re-arm, seed=42) |
|---|---|---|
| Range: foldy z policzalnym Sharpe | 1/20 | **20/20** |
| Range: łączna liczba realnych transakcji | 35 | **2 562** (34–272/fold) |
| Range: mean_sharpe | -65,43 (1 fold) | **-53,41** |
| Range: fraction_le_zero | 1,0 (1/1) | **1,0 (20/20)** |
| Trend: foldy z policzalnym Sharpe | 0/20 (WARUNKOWY — brak danych) | **3/20** |
| Trend: łączna liczba realnych transakcji | 0 | **63** |
| Trend: mean_sharpe | NaN | **-7,15** |
| Klasyfikacja ogólna (`classify_checkpoint`) | NO-GO (1/40 foldów ważnych) | **NO-GO (23/40 foldów ważnych, mean_sharpe=-47,38)** |
| Stabilność między 10 seedami (42-51) | stabilne, ale n=1 fold | **stabilne — identyczny mean_sharpe=-47,3774, std=0,0000 na WSZYSTKICH 10 seedach, teraz na 23/40 foldach ważnych** |

**Wniosek C2c.3:** naprawa deadlocka NIE zmienia werdyktu (nadal NO-GO), ale czyni go dużo bardziej
wiarygodnym — zamiast 1 foldu z 35 transakcjami, teraz WSZYSTKIE 20 foldów `range` handlują (2 562
transakcji łącznie), wszystkie ze średnim Sharpe głęboko ujemnym (-53,41, fraction_le_zero=1,0) i
identycznym wynikiem między 10 seedami modelu. To potwierdza (nie tylko sugeruje, jak poprzednio na
próbie n=1 fold), że model `range` ma systematycznie ujemny edge po kosztach na całym datasecie, nie
tylko w jednym oknie. `trend` przeszedł z "brak danych" (0/20) do 3/20 foldów z realnymi
transakcjami — też ujemny (-7,15), ale wyraźnie mniej negatywny niż `range`, i wciąż zbyt mało
foldów, żeby cokolwiek stanowczo wnioskować o `trend` osobno.

**Status:** ZROBIONE — mechanizm zaimplementowany, przetestowany (94/94), zweryfikowany na realnych
danych. Otwarta decyzja z użytkownikiem: czy następna runda skupia się na jakości sygnału/
klasyfikacji reżimu (C2.5 — rekalibracja progów 0.7/0.3, ujawniona przez C2c.1 jako prawdopodobna
przyczyna 100%-long-only podczas spadku sklasyfikowanego jako `range`) — POZA zakresem tej rundy, do
ustalenia osobno.

---

## 6. Zweryfikowane empirycznie (nie tylko zaplanowane)

- TA-Lib (0.7.0) instaluje się i liczy ATR/RSI/EMA poprawnie (zweryfikowane na random walk).
- `pandas.Series.rolling().rank(pct=True)` daje poprawną, trailing (bez leakage) percentylową
  rangę ostatniej wartości okna — zweryfikowane ręcznym przeliczeniem. Szybkie: 0.097s na 105k
  wierszy przy oknie 5760.
- `compute_all_features()` na pełnym 12-miesięcznym syntetycznym zbiorze (105k wierszy): **0.23s**.
- Nieformalny leakage sanity check: 9/9 cech identyczne na `df[:T]` vs `df[:T+50]`.
- `tests/test_fetch_ohlcv.py`: 6/6 testów przechodzi (dedup, sortowanie, gap detection).
- `xgboost` 3.2.0 instaluje się bez problemu na Python 3.14 (`pip install xgboost>=2.0`) — ryzyko
  braku prebuilt wheela (oflagowane przy planowaniu Commitu 5) nie zmaterializowało się.
- `agents/ml_optimizer.py::train_regime_model`: jedno pełne trenowanie (200 rund, early stopping
  wyłączony, `max_depth=4`) na 30k wierszy × 4 cechy — **0.436s** na Ryzen 7950X3D
  (~2.2ms/rundę). Patrz też C4.6 w `TASKS.md`.
- Pełny zestaw testów po Commicie 5: **48/48 przechodzi** (31 z Commitów 1–4 + 17 nowych: 7
  `tests/test_costs.py` + 8 `tests/test_ml_optimizer.py` + 2 `tests/test_engine.py`).
- `agents/risk_controller.py::compute_position_size`/`compute_sizing`/`check_kill_switch` — sizing
  formula i kill-switch zweryfikowane zar\u00f3wno jednostkowo, jak i property-based (hypothesis):
  `position_size` nigdy nie przekracza leverage cap niezale\u017cnie od losowych `equity`/`atr_14`/
  `entry_price` (`test_position_size_never_exceeds_leverage_cap`), jest niemalej\u0105ce w
  `signal_confidence` (`test_position_size_monotonic_nondecreasing_in_confidence`),
  `check_kill_switch` matchuje r\u0119czn\u0105 formu\u0142\u0119 drawdown dla dowolnych losowych warto\u015bci
  (`test_check_kill_switch_matches_drawdown_formula`).
- Pełny zestaw testów po Commicie 5.5: **66/66 przechodzi** (48 z Commit\u00f3w 1\u20135 + 17 nowych w
  `tests/test_risk_controller.py` + 1 nowy integracyjny w `tests/test_engine.py`).- **Pierwsze realne dane w projekcie** (Commit 6): `data/fetch_ohlcv.py` __main__ miał
  nieużywany dotąd błąd — `open("config/settings.yaml")` bez `encoding="utf-8"` crashował
  (`UnicodeDecodeError`) na tej maszynie (locale cp1250, nie UTF-8), mimo że plik jest czystym
  UTF-8 z polskimi znakami w komentarzach. Naprawione jednym słowem kluczowym. Po naprawie:
  fetch BTC/USDT:USDT 5m 2025-07-01→2026-06-30 przez ccxt/binanceusdm = **105 120 świec, zero
  dziur**, bez interwencji ręcznej.
- `exchange.load_markets()` na żywym API (binanceusdm) potwierdza `"BTC/USDT:USDT"` jako
  poprawny symbol (C1.3, wcześniej tylko założenie) — obok wariantów z datą wygaśnięcia,
  nieużywanych tutaj.
- Pełny zestaw testów po Commicie 6: **86/86 przechodzi** (66 z Commitów 1–5.5 + 20 nowych w
  `tests/test_metrics.py`, w tym 1 hypothesis property test).
- Checkpoint go/no-go (`backtest/run_checkpoint.py`) na realnych danych: wynik **NO-GO**, patrz
  §5 Commit 6 dla pełnych liczb i interpretacji.
- **Kill-switch deadlock (Commit 2b, 2026-08-01):** zweryfikowano bezpośrednio na `run_backtest`
  (realne dane, seed=42) — 18 100/18 135 (99,8%) sygnałów kandydujących stłumionych przez
  kill-switch, permanentnie od 2025-09-27 (3. dzień foldu 0 `range`) do końca datasetu
  (2026-06-30). Model sam w sobie sygnalizuje w ~99-100% wierszy testowych w każdym foldzie
  `range` — pierwotna diagnoza Commit 6 ("model rzadko sygnalizuje") była błędna. Patrz §5 Commit
  2b dla pełnej diagnozy.
- **Kill-switch deadlock NAPRAWIONY (Commit 2c, 2026-08-01):** cooldown/re-arm
  (`agents.risk_controller.should_rearm_kill_switch` + `KILL_SWITCH_COOLDOWN_DAYS=7.0`)
  zweryfikowany na realnych danych — checkpoint po naprawie: **20/20** foldów `range` mają teraz
  policzalny Sharpe (**2 562** realnych transakcji łącznie, wcześniej 1/20 foldów, 35 transakcji),
  mean_sharpe=-53,41 (fraction_le_zero=1,0), stabilne na 10 seedach (std=0,0000). `trend` przeszedł
  z 0/20 do 3/20 foldów z transakcjami (mean_sharpe=-7,15). Werdykt ogólny pozostaje **NO-GO**, ale
  teraz oparty na 23/40 foldów ważnych (wcześniej 1/40) — znacznie bardziej wiarygodny. Root-cause
  diagnostyka (`backtest/diagnose_kill_switch_trigger.py`) pokazała, że pierwotna seria strat to
  100% sygnałów long podczas trwałego spadku ceny sklasyfikowanego jako `range` (74% genuinie zły
  kierunek, 26% koszt > zysk brutto) — patrz §5 Commit 2c.

---

## 7. Znane ryzyka i otwarte pytania

- **Regime "trend" może być rzadki — POTWIERDZONE na realnych danych (Commit 6, 2026-08-01).**
  Na syntetycznych danych z progami 0.7/0.3, trend = <1% świec. Na realnych danych BTC/USDT:USDT
  5m (2025-07→2026-07): WSZYSTKIE 20 foldów walk-forward dla `trend` pominięte przez
  `min_train_rows` — 14-dniowe okno testowe konsekwentnie miało <30 świec sklasyfikowanych jako
  `trend`. To NIE artefakt syntetycznych danych — strukturalna właściwość AND-owania dwóch
  warunków przy obecnych progach. Wymaga decyzji: złagodzić `trend_threshold` (C2.5) przy
  powrocie do Commit 2, zamiast dalszego "sprawdzania".
- **Symbol ccxt zweryfikowany na żywo (C1.3, 2026-08-01)** — `"BTC/USDT:USDT"` potwierdzony przez
  `exchange.load_markets()`, zgodny z `config/settings.yaml`. Ryzyko zamknięte.
- **Survivorship bias w pożyczonych wskaźnikach** — RSI/ATR/EMA przetrwały w publicznym obiegu
  (freqtrade i podobne) częściowo dlatego, że ktoś na nich pokazał dobry backtest. Stała czujność,
  nie coś do jednorazowego zamknięcia.
- **Koszt obliczeniowy pełnego tuningu** (walk-forward × hiperparametry × okna wskaźników)
  nieoszacowany — zmierzyć na małej próbce przed pełnym przeszukiwaniem, nawet na Ryzen 7950X3D.
- **Kill-switch deadlock — NAPRAWIONE (Commit 2c, 2026-08-01).** Poprzednio: `check_kill_switch`
  poprawnie zaprojektowany jako bezstanowy/dynamiczny, ale w pętli `run_backtest` equity mogło się
  poruszyć WYŁĄCZNIE przez realną transakcję — więc po pierwszym zadziałaniu blokował sam siebie
  do końca backtestu. Naprawione cooldown/re-arm mechanizmem: po `kill_switch_cooldown_days` (domyślnie
  7.0) ciągłej suppresji, `peak_equity` resetuje się do bieżącego equity. Zweryfikowane na realnych
  danych (§5 Commit 2c) — ryzyko zamknięte.
- **NOWE ryzyko (Commit 2c, 2026-08-01) — jakość sygnału/klasyfikacja reżimu podczas trwałych
  trendów.** Root-cause diagnostyka (`backtest/diagnose_kill_switch_trigger.py`) pokazała, że seria
  strat wywołująca kill-switch to 100% sygnałów `long` podczas trwałego spadku ceny BTC (~-3,6% w
  3 dni) sklasyfikowanego jako reżim `range` — model `model_reversion` konsekwentnie obstawiał
  zły kierunek. Sugeruje to, że reguła klasyfikacji reżimu (progi 0.7/0.3, C2.5) może błędnie
  etykietować trwałe trendy jako `range`, albo że `model_reversion` nie ma wystarczającego edge'u,
  żeby to skompensować. Jawnie POZA zakresem Commitu 2c (wymaga C2.5 rekalibracji progów i/lub
  rework modelu/cech `range`) — kandydat na następną rundę, do ustalenia z użytkownikiem.

---

## 8. Zasady pracy — pamiętać przy każdym kolejnym kroku

1. **Nigdy nie optymalizuj parametrów** (okna wskaźników, progi regime, hiperparametry) na całym
   zbiorze danych na raz. Tylko wewnątrz walk-forward.
2. **Każda nowa cecha dostaje test leakage PRZED wejściem do modelu**, nie po.
3. **Target (triple-barrier) i risk_controller (stop-loss) muszą używać tego samego mnożnika
   ATR.** Rozjazd między nimi = trenujesz na czymś innym niż handlujesz.
4. **Rozszerzanie feature setu: jedna cecha na raz, mierzona na out-of-sample**, nigdy grid
   search po wielu kombinacjach naraz.
5. **Leverage cap wygrywa zawsze** nad fixed-fractional sizing — jawna reguła `min()`.
6. **LLM nigdy w hot-pathie decyzyjnym.** Offline/nadzorczo tylko.
7. **Regime gate i sizing zostają regułami, dopóki minimalny system nie udowodni edge'u.** Zamiana
   na ML (HMM, RL) to eksperyment PO ustaleniu baseline'u, nie punkt startowy.
8. **freqtrade i inne repo = katalog do przeglądania, nigdy zależność w requirements.txt** silnika
   produkcyjnego.

---

## 9. Fazy po Fazie 0 (skrót)

- **Faza 1:** regime router (dispatcher), dodanie funding rate do Test 2 metodycznie, Compliance
  Gate budowany równolegle (nie po fakcie).
- **Faza 2:** `test_mathematics.py` (zostaje deterministyczny, bez LLM — rozszerzenie Warstwy 3
  property-based testów na dane realne/backtestowe), `ai_interpreter.py` (LLM offline, on-demand
  read-only Q&A o systemie). Pełny projekt: `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`.
- **Faza 3:** paper trading / testnet, minimum kilka tygodni. freqtrade jako silnik wykonawczy
  (dry-run) to sensowna opcja tutaj — nie trzeba pisać order management od zera. Równolegle:
  `post_trade_critic.py` (LLM offline, verbal-reinforcement po FinCon — patrz
  `04_narzedzia_zewnetrzne.md` i `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`) — potrzebuje
  realnych/paper trade'ów do krytykowania, stąd Faza 3, nie 2.
- **Faza 4:** mały kapitał (w pełni tolerowalna strata), potem skalowanie.

---

## 10. Mapowanie wizji z diagramu (Miro) na fazy planu

Diagram (Miro, "My First Board") pokrywa znacznie szerszy zakres niż Faza 0 — wiele źródeł
danych, wiele modeli, pełny cykl monitoring/retraining. Poniżej: co już jest w planie (inaczej
nazwane), co pasuje do konkretnej przyszłej fazy, co nie pasuje do obecnego zakresu wcale, i co
było brakującym tematem.

### Już zrobione / już zaplanowane (ta sama rzecz, inna nazwa)

| Element z diagramu | Gdzie już jest w planie |
|---|---|
| Market Data, Volume | Commit 1 (OHLCV) |
| RSI, ATR | Commit 2 |
| Market / Entry Condition / Signal valid? | `classify_regime` → `predict_proba` → `signal_confidence` |
| Conviction-Based Sizing | `signal_confidence` skaluje `risk_per_trade` (Commit 5.5) |
| Stop Loss / Take Profit Strategy | Triple-barrier + risk_controller (Commit 4, 5.5) |
| VAR, Max Drawdown | risk_controller + kill-switch (Commit 5.5) |
| Backtest Optimization | Walk-forward (Commit 4–6) |
| VS Code, GitHub | Już nasz workflow |

### Legalne rozszerzenia — Faza 1+, dodawane metodycznie (jedna cecha na raz)

| Element | Kiedy i jak |
|---|---|
| MACD, MACROSS, Bollinger, GMMA | Częściowo redundantne z tym, co mamy (Bollinger ~ `price_zscore_20`, GMMA ~ `ema_diff_9_21`) — testować pojedynczo na OOS, nie dodawać hurtowo |
| Onchain Data | Dobry kandydat do Test 2 razem z funding rate — krypto-specyficzny sygnał pozycjonowania |
| Multi-timeframe (Trend/Day/Hour) | Po walidacji na 5m — potwierdzenie trendu z wyższego interwału, osobny wymiar złożoności |
| Trailing Stop/Take Profit | Ulepszenie risk_controllera po walidacji statycznej wersji ATR |
| Expected Shortfall | Naturalne uzupełnienie VaR o ogon rozkładu strat |
| CatBoost, RandomForest | Tylko jako porównanie/ensemble PO potwierdzeniu edge'u XGBoostem, nie zamiennik na start |

### Faza 2+/3 — dotyczy dopiero po skalowaniu

| Element | Powód odłożenia |
|---|---|
| Twitter Sentiment | Osobna modalność (NLP), koszt/jakość danych API, wymaga własnego pipeline'u walidacji |
| Forex Factory News | Lepiej jako filtr "nie handluj wokół newsa" niż cecha predykcyjna |
| Correlation & Covariance, MPT Optimization | Dotyczy alokacji między wieloma instrumentami — nierelewantne przy jednym instrumencie w Fazie 0 |
| QuantConnect / LEAN | **Zaktualizowane po researchu:** LEAN (open-source silnik pod QuantConnect) ma natywne wsparcie `AddCryptoFuture("BTCUSDT")` + `BinanceFutureMarginInterestRateModel` (symulacja funding rate) + architekturę anty-leakage. Mocniejszy kandydat niż freqtrade konkretnie dla perpetuals. Mimo to NIE w Commit 5 (mismatch z już napisanym kodem) — `Lean.DataSource.BinanceFundingRate` jako źródło danych w Fazie 1, LEAN jako silnik paper tradingu w Fazie 3 zamiast freqtrade. Oryginalny PRD miał `config/lean.json` — to prawdopodobnie był pierwotny zamysł. |
| LM Studio / RAG | Pasuje do `ai_interpreter.py` z oryginalnego PRD — LLM offline, nie na start. Pełny projekt (narzędzia, pamięć, evals, bezpieczeństwo): `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` |

### Nie pasuje do obecnego zakresu

| Element | Dlaczego |
|---|---|
| Black-Scholes | Model wyceny **opcji** — nie handlujemy opcjami, tylko perpetual futures. Zastosowanie tylko, jeśli zakres kiedyś obejmie opcje. |
| Brownian Motion | Proces stochastyczny do symulacji cen/wyceny instrumentów pochodnych — nie jest to model predykcyjny do klasyfikacji kierunku |
| LSTM/GRU | Świadomie odrzucone, nie brakujące — dane tabelaryczne + ograniczona efektywna liczba próbek faworyzują drzewa (XGBoost) nad deep learning (patrz §8, zasada 7) |

### Brakujący temat — dobra uwaga z diagramu, dodać do Fazy 1

**"Retrain Models?"** — cadence retreningu. Tego faktycznie nie było w planie.

- Retraining na stałym harmonogramie (np. co miesiąc, spójnie z granulacją okna walk-forward)
  ORAZ wyzwalany retrening, jeśli live performance (rolling Sharpe/win-rate z ostatnich N
  transakcji) spadnie istotnie poniżej oczekiwań z backtestu — to sygnał driftu reżimu, nie tylko
  szumu.
- Nie retrenować częściej niż raz na okno testowe walk-forward — inaczej dopasowujesz się do
  najnowszego szumu zamiast do trwałego wzorca.

---

## 11. Pliki już wygenerowane

W `clas5_core/`, gotowe do wklejenia w VS Code:

- `README.md` — wejście do repo dla ludzi (GitHub), niezależne od `CLAUDE.md`
- `CLAUDE.md` — instrukcje dla Claude Code (czytane automatycznie na starcie sesji)
- `.github/workflows/tests.yml` — minimalne CI (pytest + spójność registry/kod)
- `requirements.txt`, `config/settings.yaml`
- `data/fetch_ohlcv.py`
- `agents/feature_miner.py`, `agents/feature_registry.yaml`
- `tests/test_fetch_ohlcv.py` (6/6 przechodzi)
- `docs/rag/01_hipoteza_i_architektura.md`
- `docs/rag/02_cechy_i_leakage.md`
- `docs/rag/03_ryzyko_i_sizing.md`
- `docs/rag/04_narzedzia_zewnetrzne.md`
- `docs/rag/05_metodologia_wytwarzania_i_testow.md`
- `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` — planistyczny, Faza 2+ (patrz §12)

---

## 12. Faza 2 pogłębiona — LLM offline/nadzorczo (na podstawie kursu 4th-devs)

> Pełne uzasadnienie i wzorce: `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`. Nic z listy poniżej
> nie jest budowane przed checkpointem go/no-go Commitu 6 — to planowanie, nie kod.

### Zadania fazowane (Faza 2 / Faza 3)

- [ ] **`test_mathematics.py` (Faza 2):** rozstrzygnięte — zostaje w 100% deterministyczny, bez
  LLM. Weryfikacja matematycznych niezmienników (leverage cap, monotoniczność sizing względem
  `signal_confidence`) na realnych/backtestowych danych, rozszerzenie Warstwy 3 z
  `05_metodologia_wytwarzania_i_testow.md`.
- [ ] **`ai_interpreter.py` (Faza 2):** on-demand, read-only Q&A o systemie. Narzędzia:
  `get_fold_metrics`, `get_feature_definition`, `get_trade_journal`, `get_rag_doc` — zero narzędzi
  zapisu/egzekucji. Tożsamość/protokół/głos wg wzorca Identity-Protocol-Voice-Tools-Knowledge.
- [ ] **`post_trade_critic.py` (Faza 3, nie Faza 2):** scheduled, batch, verbal-reinforcement po
  FinCon. Analiza zamkniętych (realnych/paper) transakcji, raport markdown. Nigdy automatyczna
  zmiana parametrów/modelu — tylko raport, człowiek decyduje.
- [ ] **Heads-up dla Commitu 5 (`backtest/engine.py`, wciąż Faza 0):** logować transakcje w
  ustrukturyzowanym formacie (trade journal) już przy pierwszej implementacji, żeby Faza 2/3 nie
  wymagały przebudowy. Nie zmienia zakresu Commitu 5 dzisiaj — tylko do uwzględnienia przy jego
  specyfikacji.
- [ ] **Observability/evals minimalny:** structured JSON log każdej interakcji LLM (uproszczona
  taksonomia Session/Trace/Span/Tool), eval dataset ~20-30 przykładów z oczekiwanymi faktami,
  ocena human-graded na start.
- [ ] **Bezpieczeństwo:** zero narzędzi zapisu/egzekucji jako główna linia obrony przed prompt
  injection; system prompt traktowany jako publiczny; "firewall"-prompt przed głównym wątkiem
  dopiero, gdy pojawi się zewnętrzny nieufny input (dziś brak takiego źródła).
- [ ] **Świadomie wykluczone z Fazy 2/3:** autonomiczne triggery/cron/webhooks, multi-agent
  orchestration, MCP server — jeden wąski, ręcznie uruchamiany agent wystarcza na start.

### Zadania niezależne od fazowania (dokumentacja/workflow — można wykonać kiedykolwiek, nie dotyka trading logic)

- [ ] Dodać YAML frontmatter (`status`, `last_verified`, `depends_on`) do każdego `docs/rag/*.md`.
- [ ] Dodać jeden plik-indeks (Mapa Treści) linkujący `CLAUDE.md` + `IMPLEMENTATION_PLAN.md` +
  wszystkie `docs/rag/*.md` z jednozdaniowym opisem każdego.
- [ ] Nazwać formalnie już istniejącą rolę `IMPLEMENTATION_PLAN.md` jako "Observational Memory"
  sesji Claude Code; rozważyć rozdzielenie na "aktualny stan" vs "archiwum decyzji", gdy plik
  znacząco urośnie (np. po Fazie 1).
