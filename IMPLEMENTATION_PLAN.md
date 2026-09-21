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

### Commit 2d — Bramka wykonalności kosztowej `[ZROBIONE]`

**Kontekst i uzgodniony zakres (2026-09-21):** runda miała być C2.5 (rekalibracja progów regime).
Przed jej rozpoczęciem wykonano read-only diagnostykę, która obaliła przesłankę — i użytkownik
zatwierdził zmianę zakresu na bramkę wykonalności kosztowej, z C2.5 przesuniętym na osobną,
następną rundę (jedna zmiana na raz, CLAUDE.md zasada 4). Przeczytano `docs/rag/03_ryzyko_i_sizing.md`
i `docs/rag/05_metodologia_wytwarzania_i_testow.md` w całości przed zmianą (CLAUDE.md) — potwierdzono,
że docs NIE opisują żadnej bramki wykonalności kosztowej, więc jest to nowa przestrzeń projektowa,
nie nadpisanie istniejącej decyzji.

**C2d.0 — Diagnostyka (`backtest/diagnose_cost_feasibility.py`, poza pytest, jak
`run_checkpoint.py`/`diagnose_range_signal.py`/`diagnose_kill_switch_trigger.py`):** trzy bloki
read-only na realnych danych BTC/USDT:USDT 5m (2025-07→2026-07, 105 120 świec) — rozkład reguły
reżimu, porównanie szerokości bariery triple-barrier z kosztem round-trip, oraz dekompozycja
realnych transakcji na gross vs koszt.

**Wynik C2d.0 — trzy ustalenia, z których drugie przewraca dotychczasową diagnozę:**

1. **`direction_persistence_10` jest zmienną DYSKRETNĄ** — z definicji `|sum(sign(return))|/10`
   przyjmuje tylko wartości `k/10`. Realny rozkład: 0,0 → 26%, 0,2 → 42%, 0,4 → 22%, 0,6 → 7%,
   0,8 → 1,3%, 1,0 → 0,1%. Próg `trend_threshold=0.7` wpada w LUKĘ rozkładu (między 0,6 a 0,8),
   więc `trend` = 0,53% świec. To próg persistence, nie `atr_pctrank_20d`, czyni ten reżim prawie
   pustym — doprecyzowanie ryzyka z §7 i C2.5. Przesunięcie 0,7→0,5 daje `trend` = 4,53%. **Implikacja
   dla C2.5: progi nie są ciągłym pokrętłem — muszą snapować do osiągalnych wartości rozkładu.**
2. **W reżimie `range` bariera zysku jest WĘŻSZA NIŻ KOSZT.** Mediana `1.5×ATR` w `range` = **0,130%
   ceny** przy koszcie round-trip = **0,140% nominału** (2× taker 0,05% + 2× slippage 2 bps; funding
   ~0,0004%, pomijalny). Wymagana trafność kierunku na break-even, `p = 0.5*(1 + koszt/bariera)`,
   wynosi tam **103,9% — arytmetycznie nieosiągalna**. W **56,8%** świec `range` nawet PEŁNE
   trafienie bariery nie pokrywa kosztu. Dla porównania: `trend` = 68,2%, `ambiguous` = 77,5%.
3. **Model `range` MA edge kierunkowy** — trafiał kierunek w **54,6%** z 2 562 realnych transakcji
   Commitu 2c. Mimo to **42%** transakcji z POPRAWNYM kierunkiem kończyło netto pod kreską, łączny
   gross wyniósł **-569** przy koszcie **9 168** (net -9 737).

**Wniosek C2d.0:** NO-GO Commitu 2c był w ~94% wynikiem ARYTMETYCZNYM, nie statystycznym. Hipoteza
mean-reversion nie została uczciwie przetestowana — została przetestowana na oknach, w których nie
mogła wygrać. Sama rekalibracja progów (C2.5) nie zaadresowałaby tego: przesunęłaby tylko, które
świece nazywamy `range`, nie zmieniając faktu, że definicja reżimu (niski percentyl ATR) z
konstrukcji wybiera świece o najgorszym stosunku ruchu do stałego kosztu.

**C2d.1 — Mechanizm (`agents/risk_controller.py`):** czysta funkcja
`is_cost_feasible(atr_14, entry_price, cost_fraction, atr_multiplier, min_barrier_to_cost_ratio)`
(+ jej rdzeń `barrier_to_cost_ratio`) — sygnał wchodzi do gry tylko, gdy
`(atr_multiplier * atr_14) / entry_price >= min_barrier_to_cost_ratio * cost_fraction`. Wartość
startowa **`MIN_BARRIER_TO_COST_RATIO = 2.0`** (`config/settings.yaml` sekcja `risk`) wyprowadzona
z arytmetyki break-even `p = 0.5*(1 + 1/ratio)` — ratio 2.0 ⇒ wymagana trafność 75% — a NIE z
przeszukiwania po Sharpe (CLAUDE.md zasada 1). `cost_fraction` liczony przez nową
`backtest.costs.round_trip_cost_fraction()` z tych samych stałych co `total_round_trip_cost` (zero
duplikacji literałów, docs/rag/05) i przekazywany jawnie — `agents/` nie zależy od `backtest/`.

Decyzje projektowe:
- **Bramka filtruje KANDYDATURĘ sygnału (`backtest.engine._collect_candidate_signals`), nie trafia
  do trade journalu** — inaczej niż kill-switch. Kill-switch jest zdarzeniem zależnym od equity i
  historii, więc jego moment ma znaczenie w torze transakcji; bramka kosztowa jest deterministyczną
  właściwością POJEDYNCZEJ świecy, niezależną od equity. Licznik odrzuceń trafia do
  `folds_summary["n_signals_cost_gated"]`. Dzięki temu `backtest/metrics.py` nie wymaga ŻADNEJ
  zmiany ani nowego wyjątku w filtrze realnych transakcji.
- **To NIE jest próg odcięcia po `signal_confidence`** — docs/rag/03 świadomie odrzuca taki próg
  („słabszy sygnał, mniejsza pozycja, nie próg odcięcia"). Bramka jest ortogonalna: dotyczy
  geometrii bariera-vs-koszt, nie pewności modelu.
- **`atr_multiplier` nietknięty** — CLAUDE.md zasada 3 nienaruszona (bariera triple-barrier i
  stop-loss nadal dzielą tę samą stałą).
- **`min_barrier_to_cost_ratio=0.0` wyłącza bramkę** — używane przez testy sprzed Commitu 2d oraz
  do odtworzenia baseline'u Commitu 2c.

**C2d.2 — Testy (DoD, docs/rag/05):** 7 testów jednostkowych + 4 hypothesis property tests w
`tests/test_risk_controller.py` (zgodność bramki ze stosunkiem; monotoniczność niemalejąca w
`atr_14`; próg 0.0 przepuszcza wszystko; fail-safe dla `entry_price<=0`/`cost_fraction<=0`/NaN;
reprodukcja diagnozy reżimu `range`), 3 jednostkowe w `tests/test_costs.py`, 2 integracyjne w
`tests/test_engine.py` (bramka odcina sygnały i księguje je bez gubienia:
`n_signals_on + n_gated_on == n_signals_off`; bramka domyślnie WŁĄCZONA). Trzy testy sprzed Commitu
2d dostały jawne `min_barrier_to_cost_ratio=0.0` — ich przedmiotem jest kill-switch, a syntetyczny
segment `range` ma z konstrukcji wąską barierę. Pełny zestaw: **110/110 przechodzi** (94 + 16).

**C2d.3 — Ponowny checkpoint po bramce (realne dane, `min_barrier_to_cost_ratio=2.0`):**

| Metryka | Przed (Commit 2c) | Po (Commit 2d, seed=42) |
|---|---|---|
| Sygnały odrzucone przez bramkę | — | **17 547 z 18 135 (96,8%)** — w tym 17 537/17 989 (97,5%) w `range` |
| Foldy z policzalnym Sharpe | 23/40 | **6/40** (range 2/20, trend 4/20) |
| Realne transakcje | 2 625 | **358** (range 223, trend 135) |
| `mean_sharpe` (ogółem) | -47,38 | **-14,31** |
| Range: mean_sharpe | -53,41 | **-26,01** |
| Trend: mean_sharpe | -7,15 | **-8,46** (ale 25% foldów ma Sharpe > 0,5, wcześniej 0%) |
| Łączny gross | **-593** (range -569, trend -24) | **+166** (range +38, trend +128) |
| Łączny koszt | 9 354 | **2 953** |
| Trafność kierunku (range) | 54,6% | **49,3%** |
| Klasyfikacja | NO-GO | **NO-GO** |
| Stabilność (10 seedów, 42-51) | std=0,0000 | **std=0,0000 — identyczny mean_sharpe na wszystkich 10** |

Regresja kontrolna: `min_barrier_to_cost_ratio=0.0` odtwarza baseline Commitu 2c **co do ostatniej
cyfry** (`mean_sharpe=-47,377414474779975`, 23/40 foldów) — bramka jest jedyną zmianą zachowania.

**Wniosek C2d.3 — dwa wyniki, jeden dobry i jeden zły:**
- **Potwierdzone: strata BYŁA kosztowa.** Łączny gross przeszedł z **-593 na +166** — po odcięciu
  świec, na których wygrana była arytmetycznie niemożliwa, strategia przestaje tracić brutto.
  Diagnoza C2d.0 jest empirycznie potwierdzona, nie tylko prawdopodobna.
- **Nowe, niewygodne ustalenie: edge kierunkowy ZNIKA dokładnie tam, gdzie transakcja jest
  opłacalna.** Trafność w `range` spada z 54,6% (wszystkie świece) do **49,3%** (tylko świece
  przechodzące bramkę) — czyli te 54,6% mieszkało w świecach wąskobarierowych, niskozmiennych,
  na których i tak nie dało się zarobić. Na świecach szerokobarierowych model jest nieodróżnialny
  od rzutu monetą. Przy wymaganych 75% to przepaść, nie luka do zasypania tuningiem.
- **Werdykt pozostaje NO-GO**, ale jego PRZYCZYNA jest teraz inna i dużo lepiej określona: nie
  „koszty zjadają zysk", tylko „na świecach, gdzie koszt da się pokryć, model nie ma kierunku".

**Status:** ZROBIONE. Następna runda (uzgodniona z góry): **C2.5 — rekalibracja progów regime
wewnątrz walk-forward**, z uwzględnieniem dyskretności `direction_persistence_10` (C2d.0 pkt 1).
Otwarte pytanie do rozstrzygnięcia przy okazji: czy przy trafności ~49% na świecach opłacalnych
hipoteza w obecnym kształcie (5m, `REVERSION_FEATURES`) nie wymaga raczej zmiany horyzontu/cech niż
progów — patrz §7.

### Commit 2.5 — Kalibracja progów reguły regime `[ZROBIONE — wynik: NO-GO, hipoteza falsyfikowana]`

**Zakres:** sprawdzić, czy poluzowanie progów `classify_regime` (uwzględniając dyskretność
`direction_persistence_10`, C2d.0 pkt 1) usuwa/łagodzi NO-GO, bez zmiany żadnego innego elementu
pipeline'u (bramka kosztowa Commitu 2d pozostaje AKTYWNA, `min_barrier_to_cost_ratio=2.0`).

**C2.5.1 — Parametryzacja (`agents/feature_miner.py`, `backtest/engine.py`):**
`DEFAULT_TREND_THRESHOLD=0.7`/`DEFAULT_RANGE_THRESHOLD=0.3` jako nazwane stałe (mirroring
`config/settings.yaml` sekcja `regime_rule`, wzorzec `ATR_MULTIPLIER` z `agents/labeling.py`,
docs/rag/05 — zero magic numbers poza registry/configiem). `classify_regime` i
`compute_all_features` przyjmują `trend_threshold`/`range_threshold` jako parametry (domyślnie
te stałe); `run_backtest` przyjmuje i przekazuje je dalej, żeby skrypt kalibracyjny mógł
porównywać kandydatów przez dokładnie ten sam pipeline bez duplikacji logiki. Testy: 6 nowych
jednostkowych w `tests/test_feature_miner.py` (równoważność domyślne/jawne progi, rozłączność
trend/range, niezmienniki monotoniczności populacji względem progów, przekazanie progów przez
`compute_all_features` do kolumny `regime`) + 1 nowy integracyjny w `tests/test_engine.py`
(próg nieosiągalny 0.99 ⇒ zero sygnałów trend, weryfikacja end-to-end przekazania parametru przez
`run_backtest`). Pełny zestaw: **117/117 przechodzi**.

**C2.5.2 — Kalibracja (`backtest/calibrate_regime_thresholds.py`, poza pytest, jak inne skrypty
analityczne):** 4 kandydaci `(trend_threshold, range_threshold)`, wybrani z góry WYŁĄCZNIE ze
STRUKTURY formuły `persistence` (dyskretne wsparcie {0, 0.2, 0.4, 0.6, 0.8, 1.0}), nie z
podglądania Sharpe'a na tym zbiorze (CLAUDE.md zasada 1): `(0.7, 0.3)` baseline, `(0.6, 0.4)`
kontrola (przewidywanie: ta sama "luka" rozkładu co baseline), `(0.5, 0.3)` przecina pierwszą
granicę masy na osi trend, `(0.5, 0.5)` przecina granicę na obu osiach. Każdy oceniony przez
identyczny pipeline co Commit 6 (10-seedowy sweep stabilności, seed 42-51), bez automatycznego
wyboru zwycięzcy. Pełny wynik + surowy output: `runs/2026-09-21_c2.5-threshold-calibration.md`.

**Wynik C2.5.2:**

| trend_thr | range_thr | %trend | %range | mean_sharpe (seed=42) | klasyfikacja | stabilność (10 seed) |
|---|---|---|---|---|---|---|
| 0.7 | 0.3 (baseline) | 0.50% | 21.13% | **-14.31** | NO-GO | std=0,0000 |
| 0.6 | 0.4 | 0.63% | 27.72% | **-14.25** | NO-GO | std=0,0000 |
| 0.5 | 0.3 | 4.28% | 21.13% | **-18.00** | NO-GO | std=0,0000 |
| 0.5 | 0.5 | 4.28% | 44.18% | **-19.58** | NO-GO | std=0,0000 |

**Wniosek C2.5 — hipoteza CZĘŚCIOWO potwierdzona co do mechanizmu, ale FALSYFIKOWANA co do
wniosku:**
- Poluzowanie progów faktycznie zwiększa populację `trend` (0,50%→4,28%, 8,5×) — mechanizm
  działa zgodnie z diagnozą C2d.0.
- Kandydat kontrolny `(0.6, 0.4)` NIE odtworzył identycznej populacji co baseline — przewidywanie
  było błędne, bo `atr_pctrank_20d` jest CIĄGŁA: nawet przesunięcie progu w "luce" rozkładu
  `persistence` samo w sobie zmienia próg na drugiej, ciągłej osi reguły AND. Uczciwa korekta:
  "luka rozkładu" nie jest jedynym czynnikiem sterującym populacją regime.
- **Główny wynik: więcej świec `trend`/`range` = GORSZY wynik, nie lepszy.** `mean_sharpe`
  pogarsza się monotonicznie wraz z poluzowaniem progów (-14,31 → -14,25 → -18,00 → -19,58).
  Świece DODANE przez poluzowanie progu są NIE LEPSZEJ jakości niż te już objęte przy 0,7/0,3 —
  to odrzuca hipotezę, że "brakujące" (odrzucone jako `ambiguous`) świece kryją niewykorzystany
  edge, który regime rule przez pomyłkę odcina. Wszystkie 4 kandydatów: **NO-GO**, stabilnie.

**Status:** ZROBIONE. Zgodnie z regułą routingu checkpointu (docs/rag/03: NO-GO → powrót do
rejestru cech, NIE dalszy tuning tej samej reguły), **rekalibracja progów regime jest wyczerpana
jako kierunek — `config/settings.yaml` pozostaje przy baseline (0.7, 0.3)**, bo jest w
rzeczywistości najlepszym (najmniej ujemnym) z czterech przetestowanych wyników. Ciężar dowodu
dla otwartego pytania "dlaczego model `range` stawiał na long podczas trendu spadkowego" przesuwa
się z hipotezy (a) "zła kalibracja progów" (WYCZERPANA) na hipotezę (b) "model/cechy nie mają
edge'u" — patrz §7. Decyzja o następnym kroku (nowa cecha vs głębsza diagnoza modelu) należy do
użytkownika.

### Commit 2.6 — Odporność hipotezy na timeframe (1h, 4h) `[ZROBIONE — wynik: NO-GO, hipoteza falsyfikowana]`

**Zakres:** użytkownik zauważył, że cały pipeline (Commit 1-2.5) działał WYŁĄCZNIE na 5m, i że
pozycja jest trzymana max. 1h (12 świec 5m) — bardzo krótki horyzont względem stałego kosztu
transakcyjnego. Zapytał, czy wynik (NO-GO, Commit 2d/2.5) utrzymuje się na grubszych interwałach
(1h, 4h), gdzie bariera ATR-owa naturalnie rośnie względem kosztu. Uzgodniony zakres: PRZELICZYĆ
cały checkpoint na 1h i 4h, zmieniając WYŁĄCZNIE timeframe danych (+ `candles_per_day` jako
wymuszona konwersja jednostek, nie parametr hipotezy) — wszystko inne (progi 0.7/0.3,
`ATR_MULTIPLIER`, bramka kosztowa 2.0) niezmienione (CLAUDE.md zasada 1/4).

**Ograniczenie środowiska (odkryte przy starcie, nie wcześniej znane):** cloud sandbox nie ma
dostępu sieciowego do Binance (`fapi.binance.com` → `403 Forbidden` na poziomie proxy,
zweryfikowane przed startem). Natywny fetch 1h/4h przez `data.fetch_ohlcv.get_ohlcv_cached` był
więc niemożliwy — dane 1h/4h zostały zamiast tego **zagregowane z tego samego, zweryfikowanego
źródła 5m** przez nową funkcję `data.fetch_ohlcv.resample_ohlcv` (open/high/low/close/volumen,
odrzucanie niepełnych bucketów brzegowych; 7 nowych testów jednostkowych). To świadome
zastępstwo, jawnie odróżnione nazwą w dokumentacji od potencjalnego przyszłego natywnego fetcha —
pełne ograniczenia w docstringu funkcji.

**C2.6.1 — Kod:** `resample_ohlcv` (`data/fetch_ohlcv.py`, + testy w `tests/test_fetch_ohlcv.py`).
`candles_per_day` sparametryzowane przez `classify_regime`/`compute_all_features`/`run_backtest`
(ten sam wzorzec co progi w C2.5) — BEZ tego atr_pctrank_20d na 1h/4h liczyłby okno "20 dni" z
literałem 288 zakładającym 5m, co dałoby okno o BŁĘDNEJ długości kalendarzowej (np. przy 1h:
288*20=5760 świec = 240 dni zamiast 20). To poprawka jednostek, nie tuning. 4 nowe testy w
`tests/test_feature_miner.py` + 1 integracyjny w `tests/test_engine.py`. Pełny zestaw: **125/125
przechodzi** (117 + 8: 4 resample + 3 feature_miner + 1 engine).

**C2.6.2 — Skrypt (`backtest/checkpoint_timeframe_robustness.py`, poza pytest):** identyczny
pipeline co Commit 6/2c/2d/2.5, uruchomiony na 5m (referencja), 1h (8 760 świec), 4h (2 190
świec) — dokładny, bezresztowy podział z 105 120 świec 5m potwierdza brak przesunięcia
granic/dziur przy resample. Pełny wynik: `runs/2026-09-21_c2.6-timeframe-robustness.md`.

**Wynik C2.6.2:**

| timeframe | mean_sharpe (seed=42) | klasyfikacja | trend: n_valid_folds | stabilność (10 seed) |
|---|---|---|---|---|
| 5m (referencja) | -14,31 | NO-GO | 4/20 | std=0,0000 |
| **1h** | **-15,57** | NO-GO | **0/18** | std=0,0000 |
| **4h** | **-8,75** | NO-GO | **0/12** | std=0,0000 |

Diagnostyka uzupełniająca (metodologia Commitu 2d, powtórzona per timeframe) potwierdza, że
mechanizm bariera-vs-koszt **DZIAŁA jak przewidziano**: w `range` wymagana trafność break-even
spada z niemożliwych 103,9% (5m) do 61,2% (1h) i 54,4% (4h), a odsetek świec arytmetycznie
niewykonalnych z 56,8% (5m) do **0,0%** (1h i 4h). Mimo to trafność kierunku na realnych
transakcjach po bramce pozostaje na poziomie rzutu monetą: **49,0%** (1h) albo wypada GORZEJ:
**41,2%** (4h, systematycznie zły kierunek, nie tylko brak edge'u).

**Wniosek C2.6 — trzeci niezależny test wskazujący ten sam kierunek:** naprawienie stosunku
bariera/koszt (potwierdzone empirycznie) NIE przywraca edge'u kierunkowego. Hipoteza "problem
jest tylko kosztowy/za krótki timeframe" jest FALSYFIKOWANA — dokłada się do wniosku z C2.5
("problem jest w modelu/cechach, nie w kalibracji reguły regime czy granulacji danych").
Dodatkowo: regime `trend` staje się PRAKTYCZNIE PUSTY na 1h/4h (0 transakcji), bo
`direction_persistence_10` pozostał liczony na STAŁEJ liczbie 10 świec (świadoma decyzja tej
rundy) — przy 1h/4h oznacza to wymóg 10h/40h tego samego znaku zwrotu, coraz rzadsze zjawisko.

**Ograniczenia do uwzględnienia przy interpretacji (jawnie udokumentowane, nie ukryte):**
1. `VERTICAL_BARRIER_CANDLES=12` NIE zostało przeliczone — pozycja trzymana 12h (1h) / 48h (4h)
   zamiast 1h (5m). Timeframe danych i horyzont trzymania NIE są rozdzielone w tej rundzie.
2. Dane 4h są małe (2 190 świec, 524 `range`) — wynik -8,75/41,2% może częściowo odzwierciedlać
   szum małej próby.
3. Dane 1h/4h to agregacja z 5m (ograniczenie środowiska), nie natywny fetch z giełdy.

**Status:** ZROBIONE. Kierunek "zmiana timeframe naprawia problem" wyczerpany na tym etapie —
patrz §7 dla zaktualizowanego stanu najważniejszego otwartego ryzyka.

---

### Commit 2.7 — Przegląd kandydatek nowych cech: korelacje `[ZROBIONE — wynik: 1 cecha odrzucona, brak sygnału cecha-target]`

**Zakres:** użytkownik zapytał, czy zamiast dalszego tuningu parametrów lepiej najpierw
zbudować szerszy zestaw kandydatek cech i sprawdzić korelacje między nimi, zanim wybierze się
którąś do formalnego testu. Uzgodniona metodologia (docs/rag/02, CLAUDE.md zasada 4): korelacja
cecha-cecha (Spearman, cały zbiór) jest BEZPIECZNA — nie dotyka etykiety, więc służy tylko do
wykrycia redundancji. Korelacja cecha-target jest z definicji podglądaniem etykiety na całym
zbiorze, więc dopuszczona WYŁĄCZNIE jako opisowa/eksploracyjna (nigdy jako bramka selekcji) —
jedyny krok o wadze dowodowej pozostaje formalny walk-forward jednej wybranej cechy.

**Kod:** nowy `backtest/screen_feature_candidates.py` (poza pytest, jak inne skrypty
analityczne) + 8 nowych, czystych funkcji cech (4 rodziny: volatility, momentum,
mean-reversion, volume), świadomie zaprojektowanych jako nie-redundantne z 9 cechami w
`agents/feature_miner.FEATURE_FUNCTIONS` NA PODSTAWIE definicji wzoru. Nie wchodzą do
registry produkcyjnego na tym etapie (screening przed-rejestracyjny, formalny test leakage
dopiero przy promocji jednej cechy). Pełny wynik: `runs/2026-09-21_c2.7-feature-candidate-screening.md`.

**Wynik — blok 2 (korelacja cecha-cecha, redundancja):**

| Znalezisko | Szczegóły |
|---|---|
| `bb_pctb_20` **ODRZUCONY** | corr=+1,000 z `price_zscore_20` (już w modelu Test 2) — afiniczna transformacja tej samej informacji, nie nowa cecha |
| `adx_14` **wyróżniony** | jedyny kandydat z niską korelacją do reszty registry (corr z `direction_persistence_10` = +0,07, mimo że oba mierzą "siłę trendu") — sensowny kandydat #1 do formalnego testu OOS |
| rodzina volatility (`bb_width_20`, `realized_vol_20`) | silnie redundantna z istniejącymi `atr_14`/`atr_pctrank_20d` (corr 0,79–0,88) |
| `obv_zscore_20` | etykieta "volume" myląca — w praktyce bliżej mean-reversion/momentum (corr 0,72–0,78 z `price_zscore_20`/`bb_pctb_20`), bo OBV odziedzicza znak zwrotu ceny |

**Wynik — blok 3 (korelacja cecha-target, opisowa/eksploracyjna):** żadna z 17 zbadanych cech
(9 istniejących + 8 kandydatek) nie przekracza |corr| ≈ 0,065 z targetem w żadnym reżimie
(`trend`: n=523, max=-0,065 `volume_roc_10`; `range`: n=22 198, max=-0,035 `realized_vol_20`).
Czwarty niezależny sygnał (po C2.5 progach, C2.6 timeframe) wskazujący, że problem nie jest w
doborze konkretnej cechy z tego zestawu.

**Wniosek:** krok bezpieczny dał jeden konkretny wynik praktyczny (odrzucenie `bb_pctb_20`,
wyróżnienie `adx_14`); krok opisowy nie dał przesłanki faworyzującej żadną cechę ponad szum —
spójne z NO-GO C2.5/C2.6. Decyzja, czy testować `adx_14` formalnie w walk-forward (i czy
osobno rozważyć go jako zamiennik `direction_persistence_10` w regule regime — otwarty wątek
z Commitu 2c o błędnej klasyfikacji trendu spadkowego jako `range`), należy do użytkownika.

**Status:** ZROBIONE. Zero zmian w `agents/feature_miner.FEATURE_FUNCTIONS`/
`agents/ml_optimizer.py`/config — czysty screening, żadna decyzja architektoniczna
nie została podjęta automatycznie.

---

### Commit 2.8 — Formalny test OOS: `adx_14` dodane do MOMENTUM_FEATURES `[ZROBIONE — wynik: NO-GO ogólnie, poprawa marginalna w trend]`

**Zakres:** użytkownik poprosił o sformalizowanie testu OOS dla `adx_14` (kandydat
wyróżniony w Commicie 2.7 jako jedyny nisko skorelowany z resztą registry). Zgodnie z
CLAUDE.md zasada 4 (jedna cecha na raz, mierzona OOS): `adx_14` DODANE (nie zamiana) do
`MOMENTUM_FEATURES` (Test 1/trend), `REVERSION_FEATURES` (Test 2/range) niezmienione —
porównanie baseline vs kandydat przez identyczny pipeline walk-forward.

**Kod:** `compute_adx_14` promowane z `backtest/screen_feature_candidates.py` (screening)
do produkcyjnego `agents/feature_miner.FEATURE_FUNCTIONS` (10. cecha) + wpis w
`agents/feature_registry.yaml` + jednostkowy test granic [0,100]
(`tests/test_feature_miner.py`) + formalny test leakage automatycznie objął nową cechę
(parametryzacja `agent_5_compliance/test_leakage.py`, licznik 9→10). Nowy parametr
`regime_feature_sets` w `backtest/engine.py::run_backtest` (ten sam wzorzec threading co
`trend_threshold`/`candles_per_day` z C2.5/C2.6) pozwala porównać warianty feature setu
bez duplikacji pipeline'u i bez trwałej zmiany `agents/ml_optimizer.py` — nowy test
integracyjny weryfikuje przekazanie parametru. Nowy skrypt
`backtest/evaluate_feature_candidate.py` (poza pytest): baseline (4 cechy) vs kandydat
(5 cech), pełny walk-forward + 10-seed sweep. Pełny zestaw: **128/128 przechodzi**
(125 + 3: 1 unit test adx_14 + 1 integracyjny regime_feature_sets + 1 nowa instancja
parametryzowanego testu leakage). Pełny wynik: `runs/2026-09-21_c2.8-adx14-oos-evaluation.md`.

**Wynik:**

| wariant | mean_sharpe (seed=42) | trend_sharpe | klasyfikacja ogólna | klasyfikacja trend | stabilność (10 seed) |
|---|---|---|---|---|---|
| baseline (4 cechy) | -14,3078 | -8,4560 | NO-GO | NO-GO | std=0,0000 |
| **+adx_14 (5 cech)** | **-13,6943** | **-7,1116** | **NO-GO** | **WARUNKOWY** | std=0,0000 |

Poprawa w `trend` wynika w praktyce z JEDNEGO foldu (fold_idx=11, seed=42) zmieniającego
Sharpe z -2,40 na +0,09 — wartość ledwo powyżej zera, przy tylko 4 ważnych foldach trend w
całym przebiegu (ten sam problem małej próby co C2.5/C2.6). `range` (2/2 ważne foldy
ujemne w obu wariantach, Sharpe ~-26/-27) pozostaje kompletnie niezmieniony i nadal
dominuje ogólny werdykt NO-GO.

**Wniosek C2.8 — piąty niezależny wynik w tym samym paśmie:** mała, konsekwentna (nie
losowa) poprawa w `trend`, niewystarczająca do zmiany ogólnego werdyktu i oparta na
efekcie pojedynczego foldu przy bardzo małej próbie. Spójne z C2.7 (korelacja
`adx_14`-target w `trend` = -0,0279, w paśmie szumu). Decyzja o promocji `adx_14` do
`MOMENTUM_FEATURES` na stałe należy do użytkownika — skrypt świadomie nie wybiera
zwycięzcy.

**Status:** ZROBIONE. `compute_adx_14` zostaje w registry (obliczana, przetestowana),
`MOMENTUM_FEATURES` w `agents/ml_optimizer.py` NIEZMIENIONE do czasu decyzji użytkownika.

---

### Commit 2.9 — Naprawa metodologii pomiaru (Backlog Z1–Z4, Z11–Z15) `[ZROBIONE — NO-GO odporne na fold-jitter; zwrot per trade istotnie ujemny w obu reżimach]`

**Zakres:** realizacja pierwszej transzy backlogu z pełnego audytu projektu (TASKS.md, sekcja
"Backlog — przegląd 2026-09-21"), na polecenie użytkownika ("Dopisz i wypchnij do repo a
później zacznij realizować"). Runda zmienia WYŁĄCZNIE metodologię pomiaru i higienę — zero
zmian w hipotezie, cechach, progach, kosztach czy modelu.

**Kluczowe odkrycie audytu (Z1):** sweep stabilności po seedach (C6.3) mierzył dokładnie
nic — `DEFAULT_XGB_PARAMS` bez `subsample`/`colsample_bytree` czyni XGBoost w pełni
deterministycznym, więc seed nie zmieniał ani jednego drzewa. Stąd std=0,0000 identyczne do
ostatniej cyfry w KAŻDYM eksperymencie C6→C2.8 (~10 pustych "potwierdzeń stabilności").

**Zrealizowane:**
- **Z1:** `start_offset_days` w `generate_walk_forward_folds` (labeling.py; + unit test +
  hypothesis property test, DoD Warstwa 3) → `fold_start_offset_days` w `run_backtest` →
  sweep fold-jitter (offsety 0–9 dni) w nowej wspólnej bibliotece. Perturbuje ARBITRALNE
  wyrównanie granic foldów, nie model — offset=0 odtwarza historyczny baseline co do
  ostatniej cyfry. Świadomie BEZ nowego progu pass/fail (stary std<0,2 dotyczył pustego
  szumu seedów) — raportowany rozkład + spójność znaku.
- **Z2:** `compute_t_stat` + kolumna `t_stat` per fold (bez annualizacji — annualizowany
  Sharpe przy n=31–37/fold nadmuchiwał wartości do ±20–60) + `summarize_pooled_by_regime`
  (wszystkie transakcje reżimu połączone między foldami). Kryteria klasyfikacji
  GO/WARUNKOWY/NO-GO NIEZMIENIONE — nowe miary są diagnostyką obok werdyktu.
- **Z3:** `effective_sample_size` (C4.4, dotąd NIGDZIE nieużywane) wpięte do raportu:
  `n_eff` + konserwatywny `t_stat_neff` w pooled summary.
- **Z4:** kolumna "Warianty" (księga multiple-testing) w `runs/INDEX.md` + suma pod tabelą
  (dotychczas: 7 wariantów hipotezy na tych samych danych).
- **Z13 (forward-looking):** `backtest/checkpoint_lib.py` — wspólne load/fetch/summarize/
  sweep; historyczne skrypty NIE refaktoryzowane (zamrożone zapisy eksperymentów). Pierwszy
  użytkownik: `backtest/run_checkpoint_v2.py` (kanoniczny checkpoint v2; `run_checkpoint.py`
  zostaje jako zapis Commitu 6).
- **Higiena:** Z11 (`candle_minutes` przewleczone do kosztów — funding liczony z realnego
  czasu trzymania, nie liczby świec; test integracyjny), Z12 (lint: ruff 0 błędów), Z14
  (README zaktualizowane: status, struktura z `runs/`), Z15 (test spójności registry↔kod
  czyta `feature_registry.yaml` zamiast hardkodować listę). docs/rag/03 zaktualizowane
  (sekcja stabilności). Pełny zestaw: **139/139 testów przechodzi** (128 + 11).

**Wynik na realnych danych (`runs/2026-09-21_c2.9-measurement-methodology.md`):**

| Miara | Wartość |
|---|---|
| Fold-jitter (10 offsetów) | **NO-GO w 10/10**, mean_sharpe zakres [-15,89; -6,20], std=3,09, znak ujemny 100% |
| Pooled `range` (n=223) | mean/trade=-0,00108, **t=-7,15** (N_eff zdegenerowany → NaN, uczciwie) |
| Pooled `trend` (n=135) | mean/trade=-0,00063, **t=-2,91**, N_eff=110 → **t_neff=-2,63** |

**Wniosek C2.9:** (a) NO-GO jest po raz pierwszy potwierdzone REALNĄ perturbacją — nie jest
artefaktem wyrównania foldów; (b) zwrot per trade jest **istotnie ujemny w obu reżimach**
(najtwardsze dotąd sformułowanie stanu hipotezy); (c) zmierzona skala szumu fold-jitter
(σ≈3,1 mean_sharpe) czyni porównania wariantów o Δ<~3 nierozstrzygalnymi na rocznych danych
— retrospektywnie: "poprawa" C2.8 (+0,61) to ~0,2σ tego szumu, co wzmacnia tamtejszą
rekomendację niepromowania `adx_14`; (d) **Z5 (3–5 lat historii, fetch na maszynie
użytkownika) jest teraz najważniejszym odblokowaniem** dalszej pracy hipotezowej.

**Status:** ZROBIONE. Backlog: Z1–Z4, Z11–Z15 zamknięte; Z5 zrealizowane w Commicie 2.10
(poniżej); otwarte pozostają Z6–Z9 i decyzja Z10.

---

### Commit 2.10 — Wydłużenie historii danych do 3 lat (Backlog Z5) `[ZROBIONE — NO-GO na nowej bazie; niska liczba ważnych foldów okazała się strukturalna, nie ilościowa]`

**Kontekst i zakres (2026-09-21):** Z5 czekało na maszynę użytkownika (sandbox bez dostępu do
Binance). Wykonane na niej: dostęp potwierdzony (ccxt 4.5.48, ~0,35 s/stronę). Decyzja
użytkownika: **3 lata, 2023-07-01 → 2026-07-01** (z opcji 3 lat / 5 lat / maks od 2019-09-10);
`end` bez zmian, więc stare okno jest ścisłym sufiksem nowego. Zero zmian w hipotezie/cechach/
progach/kosztach/modelu. **Nowa baza checkpointu — nie porównanie 1:1 z C6–C2.9**; licznik
multiple-testing w `runs/INDEX.md` rozwidlony per zbiór danych (stary: 7, nowy: 0).

**Co zrobiono:**
- **C2.10.1 — utwardzenie fetchu** (`data/fetch_ohlcv.py`): `_fetch_page_with_retry` — retry z
  wykładniczym backoffem na `ccxt.NetworkError` (max 5 prób), `ExchangeError` celowo bez retry;
  log postępu co 50 stron. Semantyka cache niezmieniona (nazwa pliku koduje zakres → nowy zakres
  = nowy plik, stary parquet ZOSTAJE jako zamrożone źródło C6–C2.9). 4 testy (stub, bez sieci).
  Pełny zestaw: **143/143** (139 + 4).
- **C2.10.2 — fetch + integralność:** `data.start=2023-07-01`; **315 648 świec = 1096×288, zero
  dziur/duplikatów/NaN**, bez ani jednego retry. Overlap 2025-07→2026-07 ze starym plikiem:
  105 120 wierszy, max |Δ|=0 na wszystkich kolumnach OHLCV, `equals=True`.
- **C2.10.3 — checkpoint v2** (`run_checkpoint_v2`, pełny sweep) + diagnostyka udziału reżimów i
  bramki kosztowej z `folds_summary`.

**Wynik na realnych danych (`runs/2026-09-21_c2.10-extended-history-z5.md`):**

| Miara | Stare okno (C2.9, 1 rok) | **Nowe okno (C2.10, 3 lata)** |
|---|---|---|
| Foldy ważne / łącznie | 6 / 40 (15,0%) | **21 / 144 (14,6%)** |
| Klasyfikacja, mean_sharpe | NO-GO, -14,31 | **NO-GO, -12,39** |
| Pooled `range`: n, t_stat, t_neff | 223, -7,15, NaN | **530, -10,47, -7,34** (N_eff=261) |
| Pooled `trend`: n, t_stat, t_neff | 135, -2,91, -2,63 | **395, -5,51, -4,04** (N_eff=213) |
| Fold-jitter | 10/10 ujemne, σ=3,09 | **10/10 ujemne**, σ≈2,5 bez outliera (offset 9: -189) |
| Udział `trend` / `range` | 0,55% / 22,25% | **0,53% / 21,62%** |
| Bramka kosztowa `range`: % zablokowanych | — | **98,0%** (61 313 / 62 553) |

**Wniosek C2.10:** (a) werdykt NO-GO jest twardszy — zwrot per trade istotnie ujemny w obu
reżimach z dużym zapasem (t≈-10 / -5,5), odporny na fold-jitter również na 3 latach; (b) **odsetek
ważnych foldów nie wzrósł** — 3× więcej danych dało liniowo więcej foldów, ale przyczyna jest
strukturalna: pusty reżim `trend` (0,53% świec, dyskretność persistence — C2.5/Z7) i bramka
kosztowa blokująca 98% sygnałów `range` (Commit 2d/Z6). Dłuższa historia tego nie naprawi;
(c) outlier offset=9 (mean_sharpe -189) to znana słabość annualizowanego per-fold Sharpe przy
n≈kilka (C2.9/Z2) — statystyką nośną są pooled t; (d) dalsze dźwignie: Z7 (reguła reżimu), Z6
(koszty — przy 98% blokady bramka jest werdyktem o kosztach, nie o modelu), Z10 (decyzja).

**Status:** ZROBIONE. Backlog: Z1–Z5, Z11–Z15 zamknięte; otwarte Z6–Z9 (Z9 teraz wykonalne z
maszyny użytkownika) i decyzja Z10.

---

### Commit 2.11 — Instrumentacja edge'u `[ZROBIONE — blokada jest w geometrii wypłaty, nie w kierunku sygnału]`

**Kontekst (2026-09-21):** Runda 1 z czterorundowego programu „droga do GO" uzgodnionego
z użytkownikiem (instrumentacja → koszty Z6 → próg pewności → reguła reżimu Z7; pre-rejestrowana
reguła STOP po Rundzie 3). Powód rundy: werdykt C2.10 („brak edge'u") **mieszał dwie różne
rzeczy**. Cała klasyfikacja liczy się z `net_pnl`, a `gross_pnl` — jedyna kolumna mówiąca
o jakości samego sygnału — była zapisywana w journalu i **nigdy nieczytana przez `metrics.py`**.

Bariery triple-barrier są symetryczne (±`ATR_MULTIPLIER`×ATR, odtwarzane przez
`engine._resolve_exit_price`), więc wypłata jest w pełni określona przez zgodność kierunku
z etykietą, a werdykt redukuje się do jednej nierówności:

```
(2p − 1) · B  >  C     p = trafność kierunku, B = szerokość bariery, C = koszt round-trip
```

**Co zrobiono:** `backtest/metrics.py` — `break_even_hit_rate` (= 0,5·(1+C/B)), `compute_hit_rate`
(trafność z `gross_pnl`, z-stat wobec H0: p=0,5, CI Walda, próg raportowania
`MIN_TRADES_FOR_HIT_RATE_CI=20`), `summarize_edge_by_regime` (rozbicie na człony + margines);
wpięte do `checkpoint_lib.run_and_summarize` (`edge_per_regime`) i `run_checkpoint_v2`.
**Kryteria GO/WARUNKOWY/NO-GO NIEZMIENIONE** — nowe miary to diagnostyka obok werdyktu,
dokładnie jak Z2/Z3 w C2.9. Testy: **157/157** (143 + 14: 11 unit + 3 `hypothesis`).

**Wynik (`runs/2026-09-21_c2.11-edge-instrumentation.md`)** — werdykt bit-identyczny z C2.10
(`mean_sharpe = -12,392006781796571`, 21/144), co jest regresją baseline'u potwierdzającą, że
runda jest czysto addytywna:

| regime | n | hit_rate | z | B | C | break_even_p | **margin** |
|---|---|---|---|---|---|---|---|
| `range` | 530 | 51,89% | +0,87 | 0,2707% | 0,1399% | **75,83%** | **−23,94 pp** |
| `trend` | 395 | 50,63% | +0,25 | 0,4719% | 0,1402% | **64,86%** | **−14,23 pp** |

**Wniosek C2.11:** trafność kierunku jest nieistotnie różna od rzutu monetą, ale **dodatnia
w obu reżimach — model nie jest odwrócony**. Jednocześnie wymagana trafność to 75,8%/64,9%,
więc nawet górny kraniec CI (56,1%/55,6%) zostawia ~20 pp / ~9 pp pod progiem opłacalności.
**NO-GO jest przesądzone arytmetycznie geometrią wypłaty, nie błędem kierunku** — to rozróżnienie
zmienia kierunek dalszej pracy: domknąć lukę może tylko zmiana C (koszt), B (geometria) albo
selekcja podzbioru o wyższym p, a nie „lepszy model" w realistycznym zakresie.

**Status:** ZROBIONE. Następna: Runda 2 (C2.12 / Backlog Z6) — realistyczny model wykonania.

---

### Commit 2.12 — Realistyczny model wykonania maker/taker (Backlog Z6) `[ZROBIONE — NO-GO, ale ok. połowa luki do opłacalności domknięta]`

**Kontekst (2026-09-21):** Runda 2/4 programu „droga do GO". C2.11 pokazał, że koszt jest członem
dominującym nierówności (2p−1)·B > C: 0,14% nominału wobec **1,47 bps** średniego edge'u brutto.
Tymczasem `costs.py` modelował **wyłącznie takera po obu stronach** — to nie było założenie
konserwatywne, tylko brak modelu (realna egzekucja limitem kosztuje 0,02%, nie 0,05%).
Decyzja użytkownika: maker na wejściu i take-proficie, taker na stop-lossie i timeoucie,
slippage tylko na nogach taker.

**Co zrobiono:** `backtest/costs.py` — `MAKER_FEE_RATE`, `leg_fee_rate`, `exit_leg_for_reason`,
fee liczone per noga (domyślne taker/taker wstecznie zgodne); `backtest/engine.py` — kolumna
**`exit_reason`** (z iloczynu `direction * label`; sam `label` nie wystarcza, bo short na
etykiecie −1 to TP, nie SL), `_execution_legs`, parametr `execution_model`
(`taker_only` | `maker_limit`). Bramka kosztowa działa przed wejściem, więc nie zna powodu
wyjścia — dostaje założenie konserwatywne (wyjście taker). Testy: **182/182** (+25), w tym
regresja baseline'u: `taker_only` odtwarza koszt sprzed C2.12 co do cyfry.

**Wynik (`runs/2026-09-21_c2.12-execution-cost-model.md`):**

| Miara | C2.11 | **C2.12** |
|---|---|---|
| Klasyfikacja | NO-GO | **NO-GO** |
| Foldy ważne / łącznie | 21 / 144 | **54 / 144** |
| Transakcje `range` / `trend` | 530 / 395 | **7 155 / 355** |
| Koszt C | 0,140% | **0,067%** (−52%) |
| break_even_p (`range` / `trend`) | 75,83% / 64,86% | **66,59% / 58,94%** |
| **margin (`range` / `trend`)** | −23,94 / −14,23 pp | **−15,52 / −9,08 pp** |
| Zwrot per trade | −0,001001 / −0,000712 | **−0,000686 / −0,000432** |

**Wniosek C2.12:** (a) mechanizm zadziałał zgodnie z przewidywaniem — koszt spadł o połowę,
bramka przestała blokować 98% sygnałów `range`, liczba ważnych foldów wzrosła 2,6×, a margines
poprawił się o **+8,4 pp / +5,1 pp**, czyli ok. **połowę** luki; (b) efekt jest tłumiony
sprzężeniem zwrotnym: tańszy koszt przepuszcza sygnały o **węższej barierze** (B −25%/−19%),
więc break-even spadł mniej niż proporcjonalnie do kosztu; (c) w `trend` zwrot per trade
przestał być istotnie ujemny po korekcie N_eff (t_neff = −1,75); (d) **ostrzeżenie pomiarowe:**
`mean_sharpe` rozjechał się (−12,4 → −59,6 przy JEDNOCZEŚNIE lepszej ekonomice per trade),
sweep fold-jitter dał σ=75,7 i dwa offsety **dodatnie**, spójność znaku 100%→80%. Per-fold
Sharpe — podstawa kryteriów z docs/rag/03 — przestał być wiarygodnym przyrządem przy dużej
liczbie transakcji; nośne są pooled t-staty i margin. Kryteriów NIE zmieniano (docs je zamrażają).

**Status:** ZROBIONE. Backlog: Z1–Z6, Z11–Z15 zamknięte. Następna: Runda 3 (C2.13) — próg
pewności kalibrowany wewnątrz walk-forward, atakujący człon `p`.

---

### Commit 2.13 — Próg pewności kalibrowany wewnątrz walk-forward `[ZROBIONE — hipoteza SFALSYFIKOWANA, reguła STOP uruchomiona]`

**Kontekst (2026-09-21):** Runda 3/4 programu „droga do GO", atakująca człon `p` nierówności
(2p−1)·B > C. Hipoteza, próg i kryterium sukcesu **zarejestrowane przed uruchomieniem**:
trafność w górnym kwartylu `signal_confidence` (zmierzona przed programem: 57,1% `range`,
63,3% `trend`) miała wobec progów break-even z C2.12 dać po raz pierwszy dodatni margines
w `trend`. Kryterium: `z_margin > 2` w co najmniej jednym reżimie + poprawa klasyfikacji.

**Metodologia:** próg = kwantyl `signal_confidence` z foldu **treningowego**, stosowany OOS;
JEDNA pre-rejestrowana wartość `q=0.75`, zero sweepu. Reszta pipeline'u bez zmian.

**Wynik (`runs/2026-09-21_c2.13-confidence-threshold.md`) — kryterium NIESPEŁNIONE:**

| | baseline (C2.12) | kandydat (q=0,75) |
|---|---|---|
| `range`: hit / margin / z_margin | 51,07% / −15,52 pp / −26,25 | 51,41% / −14,73 pp / **−17,11** |
| `trend`: hit / margin / z_margin | 49,86% / −9,08 pp / −3,42 | **45,54%** / −13,24 pp / **−2,66** |
| Klasyfikacja | NO-GO | NO-GO |

**Wniosek C2.13:** efekt, na którym opierała się hipoteza, **nie istnieje poza próbą, na
której go zmierzono**. Monotoniczną zależność trafności od pewności zmierzono post hoc, na
danych zpoolowanych z 3 lat, wybierając górny kwartyl PO zobaczeniu wyniku; uczciwa wersja
(próg w foldzie treningowym, ocena OOS) nie odtwarza jej wcale, a w `trend` daje wynik
**przeciwny** (−4,32 pp). To podręcznikowy przykład złudzenia z selekcji post hoc.
Po trzech rundach: koszt dał się obniżyć o połowę, ale **człon `p` nie daje się ruszyć** —
trafność pozostaje nieodróżnialna od rzutu monetą (`range` z=+1,64, `trend` z=−0,90).

**REGUŁA STOP — URUCHOMIONA.** Warunek (`z_margin ≤ 2` w każdym reżimie) spełniony, więc
**Runda 4 (C2.14 / Z7) NIE została uruchomiona** — jej uruchomienie po zobaczeniu
negatywnego wyniku byłoby dokładnie tym, czemu reguła zapobiega. Budżet multiple-testing
na nowej bazie: **2**.

**Status:** ZROBIONE. Program „droga do GO" zatrzymany zgodnie z regułą. Otwarta decyzja
**Z10** (przy użytkowniku): (a) udokumentowane zamknięcie Fazy 0 wynikiem negatywnym,
(b) świadome nadpisanie STOP i Runda 4 (Z7 — inna definicja reżimu), (c) nowa hipoteza na
członie `B` (Z8 — geometria wypłaty, jedyny człon nietknięty przez program). Niezależnie
od kierunku: **`mean_sharpe` jako raportowana liczba nagłówkowa wymaga rewizji**
(patrz ostrzeżenie pomiarowe z C2.12).

**SPROSTOWANIE (2026-09-21, weryfikacja kodu):** sformułowanie „kryteria opierają się na
`mean_sharpe`" było NIEPRECYZYJNE. `classify_checkpoint` (`backtest/metrics.py:301-307`)
podejmuje decyzję na `fraction_above_threshold` i `fraction_le_zero` — **`mean_sharpe` jest
liczone i zwracane, ale NIE wchodzi do gałęzi decyzyjnej**. Fold o Sharpe −189 liczy się
w tych ułamkach dokładnie tak samo jak fold o Sharpe −0,1, więc patologia annualizowanego
per-fold Sharpe'a **nie podważa werdyktu NO-GO** (C2.12: `fraction_le_zero` = 0,870 przy
54 ważnych foldach). Niestabilna jest raportowana liczba nagłówkowa, nie klasyfikacja.
Realna luka w bramce jest inna i węższa: `fraction_positive_sign` (`metrics.py:296,312`)
jest liczone i zwracane, ale **nigdy nieczytane** — warunek „zgodny znak" z `docs/rag/03:103`
nie jest zaimplementowany, więc bramka GO jest ściśle słabsza niż udokumentowana.

---

### Audyt po programie „droga do GO" (2026-09-21) — ustalenie przewodnie: bramka reżimu i target mierzą RÓŻNE HORYZONTY

**Kontekst:** po uruchomieniu reguły STOP (C2.13) wykonano audyt — 5 niezależnych diagnoz
+ 15 adwersarialnych weryfikacji. **Wszystkie 5 zaproponowanych rund zostało odrzuconych**
(po 2–3 głosy na każdą, m.in. za pre-rejestrację po zobaczeniu liczb, za kryteria
niefalsyfikowalne z konstrukcji i za test kodujący tautologię). Wartość audytu leży więc
nie w nowych rundach, tylko w **jednym pomiarze, którego wcześniej nikt nie zrobił**.

**Pomiar (zweryfikowany niezależnie, 315 648 świec, `classify_regime` + długości nieprzerwanych
epizodów):**

| reżim | epizodów | mediana | p90 | max | epizodów ≥ 12 świec (okno etykiety) |
|---|---|---|---|---|---|
| `trend` | 728 | **2 świece (10 min)** | 5 | 15 (75 min) | **4 (0,55%)** |
| `range` | 9 717 | **5 świec (25 min)** | 16 | 63 (5h15m) | 1 729 (17,8%) |

`VERTICAL_BARRIER_CANDLES = 12` = **60 min**. Czyli mediana epizodu reżimu jest **2–6× krótsza
niż horyzont etykiety**. Praktycznie każda transakcja `trend` jest etykietowana ruchem ceny,
który w większości dzieje się POZA reżimem, który uzasadnił wejście.

**Co to zmienia w interpretacji C2.10–C2.13:** dotychczasowy wniosek brzmiał „nie ma edge'u
kierunkowego". Dokładniejszy jest: **człon `p` był mierzony na sygnale o wewnętrznie
niespójnej specyfikacji** — bramka kwalifikuje świecę do reżimu trwającego ~10–25 minut,
a target ocenia, co stanie się przez 60 minut. To wyjaśnia, dlaczego `p` okazał się nieruchomy
w dwóch niezależnych, pre-rejestrowanych próbach: nie było czego ruszać.

**Co to zamyka (człon B):** wymagane B = C/(2p−1) = **3,15% ceny** (15,5× obecnego), co
implikuje horyzont rzędu dni. Maksymalny epizod `range` w 3 latach to 5h15m, a okien 12h/48h
w całości wewnątrz reżimu jest **zero**. Backlog **Z8 jest więc niewykonalny przy obecnej
definicji reżimu** — nie „za mało danych". W `trend` dodatkowo p=49,86% < 50%, więc (2p−1) < 0
i żadna szerokość bariery nie pomaga (szersza bariera pogarsza wynik).

**Sprostowanie do C2.12/C2.13:** teza, że „werdykt opiera się na zepsutym przyrządzie", była
nieprecyzyjna — `classify_checkpoint` decyduje na `fraction_above_threshold`/`fraction_le_zero`,
nie na `mean_sharpe`. Werdykt NO-GO jest odporny na patologię per-fold Sharpe'a i pozostaje
w mocy. Realna luka jest węższa: warunek „zgodny znak" z `docs/rag/03:103` nie jest
zaimplementowany (`fraction_positive_sign` liczone, nigdy nieczytane) → bramka GO jest ściśle
słabsza niż udokumentowana (osłabia GO, nie NO-GO).

**Długi techniczne potwierdzone w kodzie** (pełna lista: TASKS.md, Backlog II, Z16–Z23):
przeciek early stopping (`ml_optimizer.py:130` — dobór liczby drzew na foldzie OOS, **zawyża
`p`**); brak purge/embargo w całym repo (`test_start == train_end`, rośnie liniowo z V);
`run_backtest` bez parametrów geometrii (blokada dla eksperymentów typu Z8); trzy niekompatybilne
definicje `p` w obiegu (różnica 6–14 pp).

**Następny krok:** Z16 — diagnostyka spójności bramki z horyzontem (0 wariantów budżetu),
która formalizuje powyższy pomiar i zamyka Z8 bez wydawania wariantu. **Z16 nie zdejmuje
reguły STOP** — zdejmuje ją wyłącznie decyzja użytkownika (Z10).

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
- **Bariera `range` jest węższa niż koszt round-trip (Commit 2d, 2026-09-21).** Zmierzone na
  realnych danych (`backtest/diagnose_cost_feasibility.py`): mediana `1.5×ATR` w reżimie `range` =
  **0,130% ceny** wobec kosztu **0,140% nominału** → wymagana trafność break-even **103,9%**,
  arytmetycznie nieosiągalna; 56,8% świec `range` nie pokrywa kosztu nawet przy pełnym trafieniu
  bariery. `trend` = 68,2%, `ambiguous` = 77,5%.
- **`direction_persistence_10` jest zmienną dyskretną (Commit 2d).** `|sum(sign)|/10` przyjmuje
  tylko wartości `k/10`; realny rozkład to 0,0 → 26%, 0,2 → 42%, 0,4 → 22%, 0,6 → 7%, 0,8 → 1,3%.
  Próg 0,7 wpada w lukę rozkładu — to on, nie `atr_pctrank_20d`, czyni reżim `trend` prawie pustym
  (0,53% świec; przy progu 0,5 → 4,53%).
- **Model `range` ma edge kierunkowy, ale w niewłaściwych świecach (Commit 2d).** 54,6% trafności
  na wszystkich 2 562 transakcjach Commitu 2c, ale **49,3%** po odfiltrowaniu świec, na których
  bariera nie pokrywa kosztu. Łączny gross przeszedł z -593 (bez bramki) na **+166** (z bramką) —
  strata Commitu 2c była w ~94% kosztowa, co bramka potwierdziła empirycznie.
- **Bramka wykonalności kosztowej nie zmienia werdyktu (Commit 2d).** Po odcięciu 96,8% sygnałów:
  mean_sharpe -47,38 → **-14,31**, nadal **NO-GO**, stabilne na 10 seedach (std=0,0000). Regresja
  kontrolna z `min_barrier_to_cost_ratio=0.0` odtwarza baseline Commitu 2c co do ostatniej cyfry.

---

## 7. Znane ryzyka i otwarte pytania

- **Regime "trend" jest rzadki — POTWIERDZONE, a poluzowanie progów NIE POMAGA (Commit 6 →
  Commit 2.5, 2026-09-21).** Na realnych danych BTC/USDT:USDT 5m trend = 0,50% świec przy
  progach 0,7/0,3. Commit 2.5 poluzował progi do (0,5, 0,3)/(0,5, 0,5), zwiększając populację
  trend do 4,28% (8,5×) — ale `mean_sharpe` POGORSZYŁ SIĘ (-14,31 → -18,00/-19,58), wszystkie
  warianty NO-GO. Rzadkość regime `trend` NIE jest już otwartym ryzykiem do "naprawienia
  kalibracją" — jest zamkniętym eksperymentem z wynikiem: więcej świec trend/range nie poprawia
  wyniku, bo dodane świece nie mają lepszej jakości sygnału. Pełny wynik:
  `runs/2026-09-21_c2.5-threshold-calibration.md`.
- **Regime "trend" jest jeszcze rzadszy na grubszych timeframe'ach (Commit 2.6, 2026-09-21).**
  Przy STAŁEJ liczbie 10 świec dla `direction_persistence_10` (świadomie nieprzeliczonej per
  timeframe), regime `trend` dał **ZERO transakcji** na 1h i 4h (0/18 i 0/12 foldów), gorzej niż
  na 5m (4/20). Zmiana timeframe pogłębiła, nie złagodziła, problem z rzadkością trend — jeśli
  timeframe ma być badany dalej, `direction_persistence_10`/inne okna candle-based wymagałyby
  przeliczenia analogicznie do `candles_per_day` (Commit 2.6), co NIE zostało zrobione w tej
  rundzie (świadomy zakres: zmienić TYLKO timeframe + niezbędną konwersję jednostek ATR).
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
  rework modelu/cech `range`) — **doprecyzowane przez Commit 2d**: reguła reżimu faktycznie jest
  współwinna (dyskretność `direction_persistence_10`, próg 0,7 w luce rozkładu), ale nie jest
  całą przyczyną — patrz ryzyko niżej.
- **NAJWAŻNIEJSZE OTWARTE RYZYKO (Commit 2d→2.5→2.6, 2026-09-21) — brak edge'u kierunkowego,
  kandydaci (a) i (b) WYCZERPANE.** Po włączeniu bramki wykonalności kosztowej trafność
  kierunku modelu `range` spada z 54,6% do **49,3%** na 5m, przy wymaganych ~75% (ratio=2.0).
  Commit 2.5 przetestował kandydata (a) — rekalibrację progów regime — i go ODRZUCIŁ (4 z góry
  zarejestrowani kandydaci, wszyscy NO-GO, wynik pogarsza się wraz z poluzowaniem progów).
  **Commit 2.6 przetestował kandydata (b) — zmianę timeframe (1h, 4h) — i również go ODRZUCIŁ:**
  mechanizm bariera-vs-koszt naprawiony empirycznie (0% świec arytmetycznie niewykonalnych na
  1h/4h, wobec 56,8% na 5m), ale trafność kierunku pozostaje ~49% (1h) albo spada do ~41% (4h,
  gorzej niż rzut monetą) — patrz Commit 2.6 wyżej i
  `runs/2026-09-21_c2.6-timeframe-robustness.md`. Trzy niezależne testy (bramka kosztowa,
  progi regime, timeframe) wskazują teraz zgodnie na TEN SAM wniosek: problem nie jest ani
  kosztowy, ani kalibracyjny, ani granulacyjny — jest w samym modelu/cechach. Pozostają
  kandydaci: (c) weryfikacja założeń kosztowych (taker 0,05%/stronę to wartość startowa; przy
  maker 0,02% koszt spada do 0,08%) — coraz mniej prawdopodobne, żeby to zmieniło wniosek, skoro
  problem przetrwał nawet przy koszcie efektywnie ~11× mniejszym niż bariera na 4h; (d) powrót
  do rejestru cech per docs/rag/02, jedna cecha na raz, mierzona OOS (reguła routingu
  checkpointu, docs/rag/03: NO-GO → rejestr cech, nie dalszy tuning) — **Commit 2.7 rozpoczął
  ten kierunek** screeningiem korelacji (patrz niżej), formalny test OOS jednej cechy wciąż nie
  wykonany. Dodatkowy, nierozdzielony wątek z Commitu 2.6: `VERTICAL_BARRIER_CANDLES=12`
  nieprzeliczone przy zmianie timeframe (1h/4h oznacza 12h/48h trzymania pozycji) — jeśli
  timeframe ma być badany dalej, to osobny, jawnie nazwany eksperyment (rozdzielić timeframe
  danych od horyzontu trzymania).
- **Screening korelacji (Commit 2.7, 2026-09-21) — czwarty niezależny sygnał w tym samym
  kierunku, plus jeden konkretny wniosek praktyczny.** Korelacja Spearman cecha-target
  (opisowa/eksploracyjna, cały zbiór) na 17 cechach (9 istniejących + 8 nowych kandydatek,
  4 rodziny) nie pokazała ŻADNEJ korelacji przekraczającej |corr| ≈ 0,065 z targetem w
  żadnym reżimie — spójne z brakiem edge'u z C2.5/C2.6, tym razem metodą niezależną od modelu
  XGBoost. Praktyczny efekt uboczny: korelacja cecha-cecha ujawniła, że kandydat `bb_pctb_20`
  jest matematycznie redundantny z już używanym `price_zscore_20` (corr=1,000) — odrzucony bez
  potrzeby testu OOS. `adx_14` wyróżnia się jako jedyny kandydat nisko skorelowany z resztą
  registry (w tym, zaskakująco, z dyskretnym `direction_persistence_10` — corr=+0,07) — kandydat
  do ewentualnego formalnego testu OOS i/lub do osobnej dyskusji jako zamiennik
  `direction_persistence_10` w regule regime (dotyczy otwartego wątku o błędnej klasyfikacji
  trendu spadkowego jako `range`, Commit 2c). Żadna decyzja o promocji cechy nie została
  podjęta — pełny wynik: `runs/2026-09-21_c2.7-feature-candidate-screening.md`.
- **Formalny test OOS `adx_14` (Commit 2.8, 2026-09-21) — piąty niezależny wynik w tym samym
  paśmie "brak silnego sygnału".** Dodanie `adx_14` do `MOMENTUM_FEATURES` (Test 1, Test 2
  niezmieniony) daje małą, konsekwentną poprawę w `trend` (mean_sharpe -8,46→-7,11,
  klasyfikacja NO-GO→WARUNKOWY), ale werdykt OGÓLNY pozostaje NO-GO w obu wariantach
  (stabilne, std=0,0000 na 10 seedach). Poprawa opiera się na JEDNYM foldzie zmieniającym
  Sharpe z -2,40 na +0,09 (praktycznie zero) przy tylko 4 ważnych foldach trend — zbyt słaby i
  zbyt zależny od pojedynczego przypadku dowód, by uzasadnić promocję do produkcyjnego feature
  setu. `range` (dominujący udział w werdykcie NO-GO) kompletnie niezmieniony. `compute_adx_14`
  zostaje w registry (formalnie przetestowana pod kątem leakage), `MOMENTUM_FEATURES`
  NIEZMIENIONE do czasu decyzji użytkownika. Pełny wynik:
  `runs/2026-09-21_c2.8-adx14-oos-evaluation.md`.
- **Naprawiona metodologia pomiaru zaostrzyła obraz (Commit 2.9, 2026-09-21).** Sweep
  stabilności po seedach mierzył nic (deterministyczny XGBoost — każde dotychczasowe
  "std=0,0000 STABILNY" było puste); zastąpiony fold-jitterem: **NO-GO w 10/10 offsetów**,
  a pooled t-stat pokazuje **istotnie ujemny zwrot per trade w OBU reżimach** (range
  t=-7,15; trend t=-2,91/-2,63 po N_eff). Zmierzony szum wyrównania foldów (σ≈3,1
  mean_sharpe) czyni porównania wariantów o Δ<~3 nierozstrzygalnymi na rocznych danych 5m —
  **kolejne rundy hipotezowe bez dłuższej historii danych (Backlog Z5) mają ograniczoną moc
  rozstrzygania**. Pełny wynik: `runs/2026-09-21_c2.9-measurement-methodology.md`.
  **Aktualizacja C2.10 (Z5 zrobione, 3 lata danych):** werdykt twardszy (range t=-10,47, trend
  t=-5,51), ale odsetek ważnych foldów bez zmian (14,6%) — ograniczenie jest strukturalne
  (`trend`=0,53% świec; bramka kosztowa blokuje 98% sygnałów `range`), nie do naprawienia
  dłuższą historią. Pełny wynik: `runs/2026-09-21_c2.10-extended-history-z5.md`.
- **Założenia kosztowe są wartościami startowymi, a teraz decydują o werdykcie.** Dopóki koszt był
  jednym z wielu składników, jego przybliżony charakter nie miał znaczenia. Po Commicie 2d koszt
  jest osią diagnozy, więc `taker_fee_rate=0.0005` / `slippage_bps=2` / `funding_rate_8h=0.0001`
  z `config/settings.yaml` warto zweryfikować wobec realnych tierów fee i realistycznego udziału
  zleceń maker, zanim odrzuci się hipotezę na ich podstawie.

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
