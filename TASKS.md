# TASKS.md — Zadania implementacyjne CLAS-5 (status i podział na komponenty)

> Ten plik to granularny, statusowalny rozkład `IMPLEMENTATION_PLAN.md` (§4, §5, §9, §10, §12) i
> `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` na pojedyncze zadania. `IMPLEMENTATION_PLAN.md`
> zostaje dokumentem nadrzędnym (rationale, decyzje, Definition of Done) — ten plik służy tylko do
> śledzenia postępu na poziomie zadania. Aktualizuj status tutaj na bieżąco; nagłówek/status
> commitu w `IMPLEMENTATION_PLAN.md` aktualizuj przy zamknięciu całego commitu.
>
> Ostatnia aktualizacja: 2026-09-21.

## Zasada pracy: osobny branch per zadanie

**Nadrzędne założenie dla całego tego pliku:** każde zadanie (dowolne ID: `C*`, `F*`, `D.*`) jest
realizowane na osobnym branchu utworzonym z `master`, np. `task/C3.1-leakage-test-atr-pctrank`.
Commit/merge do `master` następuje DOPIERO PO wykonaniu zadania i jego walidacji (testy
przechodzą, zgodność z Definition of Done z `05_metodologia_wytwarzania_i_testow.md` tam, gdzie
dotyczy) — nigdy w trakcie pracy nad zadaniem. Status w kolumnie "Status" zmienia się na ✅
dopiero po scaleniu do `master`, nie po samej lokalnej implementacji.

**Opis commita/mergu zawsze opisuje, co faktycznie zostało zrobione** — merge do `master` ma w
treści konkretną zmianę (np. "Commit 3: formalny pytest leakage dla 9 funkcji cech, priorytet
`atr_pctrank_20d` (C3.1–C3.3)"), nigdy ogólnik typu "merge branch" czy "update". Ta sama zasada
dotyczy każdej zmiany statusu w kolumnie "Status" w tym pliku — commit aktualizujący status
opisuje, co zostało zweryfikowane/wykonane, nie tylko samą zmianę ikony statusu.

## Zasada pracy: zarządzanie zużyciem Claude Code (limity Pro/Max)

**Nie przechodzić na wyższy plan (Max) prewencyjnie.** Start na Pro; decyzję o upgrade'zie
podejmować na podstawie realnego zużycia z komendy `/usage`, nie z góry. Commit 5 (dwa modele
XGBoost + `backtest/engine.py` + `backtest/costs.py` + trade journal, C5.1–C5.6) to najbardziej
prawdopodobny punkt, w którym limity Pro (rolling 5h + tygodniowy) mogą zacząć przeszkadzać —
długie sesje iteracyjne trening→metryki→debug windują zużycie kontekstu szybciej niż w Commitach
1–4.

**Nawyki ograniczające zużycie, zgodne z zasadą branch-per-task:**
- `/clear` po każdym scaleniu zadania do `master` — nie ciągnąć jednej sesji przez kilka zadań
  C5.x naraz.
- Monitorować `/usage` na bieżąco podczas pracy nad Commitem 5, zamiast dowiadywać się dopiero po
  odcięciu.
- Zrzucać verbose output (logi treningu, output testów) do subagentów zamiast wklejać go wprost do
  głównej konwersacji.

**Trafienie limitu to pauza (reset okna czasowego), nie utrata pracy** — można poczekać na reset,
dokupić usage credits na sporadyczne przekroczenia, albo przejść na Max 5x, jeśli limit łapany jest
systematycznie (nie okazjonalnie), dopiero gdy dane z `/usage` to potwierdzą.

## Zasada pracy: `runs/*.md` — surowy output ciężkich obliczeń

**Ustalone z użytkownikiem 2026-09-21, rozszerzone 2026-09-21 (C2.6).** Każde uruchomienie
skryptu analitycznego, które generuje dużo surowego outputu (kalibracja, sweep seedów,
diagnostyka na realnych danych — np. `backtest/calibrate_regime_thresholds.py`,
`backtest/checkpoint_timeframe_robustness.py`, `backtest/run_checkpoint.py`), zapisuje pełny
raw output do `runs/YYYY-MM-DD_<slug>.md`: **ID testu** (spójne z numeracją Commitów, gdzie
dotyczy), metadane (branch/commit/komenda/parametry/dane), pełny stdout w bloku kodu, oraz
(od C2.6) obowiązkowa sekcja **Co na plus (+) / Co na minus (-)** — krótkie, uczciwe
zestawienie tego, co wynik potwierdza/wzmacnia, i tego, co pozostaje słabe/niepewne/
niepełne (włącznie z ograniczeniami metodologicznymi danej rundy, nie tylko wynikiem
liczbowym). Plik trafia do repo (**commitowany**, nie `.gitignore` — "commitować wszystko",
decyzja użytkownika) — to trwały, odtwarzalny zapis, nie scratch.

**`runs/INDEX.md`** — spis treści całego katalogu: ID testu, data, link do pliku, jednozdaniowy
opis, wynik. Aktualizowany (nowy wiersz) przy każdym nowym pliku w `runs/`.

`IMPLEMENTATION_PLAN.md` i `TASKS.md` dostają tylko SYNTEZĘ (tabelę porównawczą + wniosek) i
link do pliku w `runs/`, nie kopię całego outputu — ten sam wzorzec co zwięzłe podsumowania
Commitu 2c/2d z pełną diagnozą w osobnym skrypcie analitycznym.

## Legenda statusów

| Status | Znaczenie |
|---|---|
| ✅ | Zrobione i zweryfikowane |
| ⚠️ | Zrobione częściowo — działa, ale ma otwarty punkt wymagający weryfikacji |
| ⬜ | Do zrobienia — aktywny zakres (bieżący commit) |
| ⏳ | Zaplanowane, poza aktywnym zakresem — czeka na checkpoint/gate opisany w sekcji |

## Podsumowanie postępu

| Sekcja | ✅ | ⚠️/⬜ | ⏳ | Razem |
|---|---|---|---|---|
| Commit 1 — Dane | 3 | 0 | 0 | 3 |
| Commit 2 — Feature registry | 5 | 0 | 0 | 5 |
| Commit 3 — Test leakage | 3 | 0 | 0 | 3 |
| Commit 4 — Target + walk-forward split | 5 | 1 | 0 | 6 |
| Commit 5 — Dwa modele + backtest | 6 | 0 | 0 | 6 |
| Commit 5.5 — Risk controller | 5 | 0 | 0 | 5 |
| Commit 6 — Checkpoint go/no-go (ZROBIONE — wynik NO-GO) | 5 | 0 | 0 | 5 |
| Commit 2b — Diagnoza NO-GO: przegląd cech `range` (W TRAKCIE — zablokowane) | 2 | 0 | 2 | 4 |
| Commit 2c — Kill-switch: przyczyna serii strat + cooldown/re-arm (ZROBIONE) | 3 | 0 | 0 | 3 |
| Commit 2d — Bramka wykonalności kosztowej (ZROBIONE — wynik NO-GO potwierdzony) | 4 | 0 | 0 | 4 |
| Commit 2.5 — Kalibracja progów regime (ZROBIONE — wynik NO-GO, hipoteza falsyfikowana) | 2 | 0 | 0 | 2 |
| Commit 2.6 — Odporność na timeframe 1h/4h (ZROBIONE — wynik NO-GO, hipoteza falsyfikowana) | 2 | 0 | 0 | 2 |
| Commit 2.7 — Przegląd kandydatek cech: korelacje (ZROBIONE — 1 cecha odrzucona, brak sygnału cecha-target) | 2 | 0 | 0 | 2 |
| Commit 2.8 — Formalny test OOS: adx_14 (ZROBIONE — NO-GO ogólnie, poprawa marginalna w trend) | 3 | 0 | 0 | 3 |
| Commit 2.9 — Naprawa metodologii pomiaru, Backlog Z1–Z4/Z11–Z15 (ZROBIONE — NO-GO odporne na fold-jitter) | 4 | 0 | 0 | 4 |
| Commit 2.10 — Historia danych 3 lata, Backlog Z5 (ZROBIONE — NO-GO na nowej bazie, niska liczba foldów strukturalna) | 3 | 0 | 0 | 3 |
| Commit 2.11 — Instrumentacja edge'u, Runda 1/4 „droga do GO" (ZROBIONE — blokada w geometrii wypłaty, nie w kierunku sygnału) | 1 | 0 | 0 | 1 |
| Commit 2.12 — Model wykonania maker/taker, Backlog Z6, Runda 2/4 (ZROBIONE — NO-GO, ale ok. połowa luki domknięta) | 1 | 0 | 0 | 1 |
| Faza 1 — regime router, funding rate, Compliance Gate | 0 | 0 | 12 | 12 |
| Faza 2 — LLM offline Q&A + test_mathematics.py | 0 | 0 | 4 | 4 |
| Faza 3 — paper trading + post_trade_critic.py | 0 | 0 | 4 | 4 |
| Faza 4 — mały kapitał, skalowanie | 0 | 0 | 2 | 2 |
| Dokumentacja/workflow (niezależne od fazowania) | 2 | 2 | 1 | 5 |
| **RAZEM** | **61** | **3** | **25** | **89** |

---

## Faza 0 — dowód edge'u (aktywna faza)

### Commit 1 — Dane (`data/fetch_ohlcv.py`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C1.1 | Pobieranie OHLCV z Binance USDS-M Futures (perpetuals) przez ccxt, paginacja + cache parquet | ✅ | |
| C1.2 | `find_gaps()` — raportowanie dziur w danych bez blokowania pipeline'u | ✅ | |
| C1.3 | Weryfikacja dokładnego symbolu ccxt (`"BTC/USDT:USDT"`) przez `exchange.load_markets()` na żywym API | ✅ | Potwierdzone 2026-08-01 na żywym API: `"BTC/USDT:USDT"` obecny w `exchange.symbols` (Binance USDS-M Futures), obok wariantów z datą wygaśnięcia (nieużywanych). Zgodne z `config/settings.yaml`, bez zmian |

### Commit 2 — Feature registry (`agents/feature_miner.py`, `agents/feature_registry.yaml`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.1 | 9 funkcji cech (`atr_14`, `atr_pctrank_20d`, `direction_persistence_10`, `return_lag_1`, `momentum_5`, `ema_diff_9_21`, `volume_zscore_20`, `rsi_14`, `price_zscore_20`) | ✅ | |
| C2.2 | `classify_regime()` | ✅ | |
| C2.3 | `split_by_regime()` | ✅ | |
| C2.4 | Nieformalny leakage sanity check (9/9 na danych syntetycznych) | ✅ | Nie zastępuje formalnego testu z Commitu 3 |
| C2.5 | Kalibracja progów regime rule (0.7/0.3) na realnych danych | ✅ | **ZROBIONE 2026-09-21 — wynik: NO-GO, hipoteza falsyfikowana.** Pełny opis pracy i wyniku: sekcja "Commit 2.5" niżej (po Commicie 2d), `runs/2026-09-21_c2.5-threshold-calibration.md`, IMPLEMENTATION_PLAN.md §5/§7 |

### Commit 3 — Test leakage (`agent_5_compliance/test_leakage.py`) — ✅ ZROBIONE

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C3.1 | Formalny, parametryzowany pytest leakage dla wszystkich 9 funkcji cech (`df[:T]` vs `df[:T+k]`) | ✅ | Zaimplementowane: `agent_5_compliance/test_leakage.py::test_feature_no_leakage`, 9/9 cech przechodzi |
| C3.2 | Priorytet: `atr_pctrank_20d` — trailing, nie centered window | ✅ | Dodatkowy dedykowany test `test_atr_pctrank_20d_trailing_not_centered` (mutacja przyszłych świec) — przechodzi |
| C3.3 | Zweryfikować, że istniejące CI (`.github/workflows/tests.yml`, auto-discovery `pytest -v`) podłapuje nowy `test_leakage.py` bez edycji configu | ✅ | Potwierdzone na GitHubie (nie tylko lokalnie): run `30383077052` na `master` — `success`, 17/17 przechodzi, bez żadnej edycji `tests.yml` po dodaniu pliku testów |

### Commit 4 — Target + walk-forward split (`agents/labeling.py`) — ✅ ZROBIONE (poza C4.6, odłożone do Commit 5)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C4.1 | Triple-barrier ATR-scaled (upper/lower = ±1.5×ATR, vertical = 12 świec/1h) | ✅ | Zaimplementowane: `agents/labeling.py::compute_triple_barrier_labels` — reużywa `compute_atr_14` z `feature_miner.py` (bez duplikacji). 7 testów scenariuszowych w `tests/test_labeling.py` (upper/lower hit, vertical timeout, tiebreak gdy obie bariery trafione w tej samej świecy ×2, ATR-warmup→NaN, niepełne okno na końcu datasetu→NaN) + 1 hypothesis property test — wszystkie przechodzą |
| C4.2 | Spójność mnożnika 1.5×ATR z przyszłym `risk_controller` (Commit 5.5) | ✅ | Jedyne źródło prawdy: `config/settings.yaml` sekcja `labeling.atr_multiplier: 1.5`, `agents/labeling.py::ATR_MULTIPLIER` matchuje. `risk_controller.py` (Commit 5.5) MUSI czytać tę samą wartość — CLAUDE.md zasada 3 |
| C4.3 | Walk-forward split (2 mies. train / 2 tyg. test, krok 2 tyg., chronologiczny) | ✅ | Zaimplementowane: `agents/labeling.py::generate_walk_forward_folds` — chronologiczne, przesuwane okna, half-open intervals (brak nakładania train/test wewnątrz foldu). 3 testy w `tests/test_labeling.py` (chronologia + brak nakładania, oczekiwana liczba foldów, zbyt mało danych → pusta lista) przechodzą |
| C4.4 | Diagnostyka efektywnej liczby próbek (autokorelacja `return_lag_1`, N_eff) | ✅ | Zaimplementowane: `agents/labeling.py::effective_sample_size` (N_eff = N/(1+2·Σρ_k), `pd.Series.autocorr`). 2 testy sanity (i.i.d. → N_eff≈N; silnie autoskorelowany → N_eff≪N) przechodzą |
| C4.5 | Test leakage dla `labeling.py` PRZED wejściem do modelu | ✅ | Zaimplementowane: `agent_5_compliance/test_leakage.py::test_triple_barrier_no_leakage` — metodologia truncate-vs-extend dostosowana do labeli (porównywalny region = wiersze, których pełne okno w przód mieści się w obciętych danych). Przechodzi |
| C4.6 | Zmierzyć koszt obliczeniowy pełnego tuningu (walk-forward × hiperparametry × okna wskaźników) na małej próbce PRZED pełnym przeszukiwaniem | ⚠️ | Pomiar częściowy wykonany w Commicie 5 (po dodaniu realnych hiperparametrów XGBoost): jedno `train_regime_model` (max_depth=4, 200 rund, early stopping wyłączony) na 30k wierszy × 4 cechy = **0.436s** (~2.2ms/rundę), Ryzen 7950X3D. Ekstrapolacja: walk-forward ~9 foldów × 2 reżimy = 18 treningów/kombinację hiperparametrów ≈ 7.9s najgorszy przypadek; grid search 20 kombinacji ≈ 158s — koszt obliczeniowy nie wygląda na blocker. Otwarte: pomiar NIE obejmuje jeszcze przeszukiwania okien wskaźników (`feature_miner.py`) razem z hiperparametrami XGBoost — do zrobienia przy faktycznej kalibracji (Commit 6 / Faza 1) |

### Commit 5 — Dwa modele, osobno (`agents/ml_optimizer.py`, `backtest/`) — ✅ ZROBIONE

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C5.1 | `model_momentum` + `model_reversion` — dwa niezależne XGBoosty | ✅ | Zaimplementowane: `agents/ml_optimizer.py::train_regime_model` (generyczny, wywoływany osobno dla `MOMENTUM_FEATURES`/`REVERSION_FEATURES` per reżim w `backtest/engine.py`) — natywne API `xgboost.train()`/`DMatrix`, nie sklearn-wrapper. Żadnego wspólnego modelu |
| C5.2 | Hiperparametry startowe + `early_stopping_rounds=20` na foldzie OOS | ✅ | `DEFAULT_XGB_PARAMS` (max_depth=4, eta=0.05) + `NUM_BOOST_ROUND=200` + `EARLY_STOPPING_ROUNDS=20`, źródło prawdy `config/settings.yaml` sekcja `model`. Early stopping mierzony na `test_df` (OOS), nigdy train — potwierdzone testem `test_train_regime_model_early_stopping_engages` |
| C5.3 | `predict_proba` (nie tylko klasa) jako `signal_confidence` | ✅ | `agents/ml_optimizer.py::predict_signal` — `signal_confidence` = predict_proba klasy argmax (nie surowa etykieta), `signal_direction` zdekodowany do {-1,0,1} przez `CLASS_TO_LABEL`. Testy: `test_predict_signal_returns_valid_direction_and_confidence`, `test_predict_signal_preserves_index_after_dropna` |
| C5.4 | `backtest/costs.py` — taker fee, funding rate, slippage | ✅ | `round_trip_fee_cost`, `funding_cost`, `slippage_cost`, `total_round_trip_cost`. Wartości startowe w `config/settings.yaml` sekcja `costs` (taker_fee_rate=0.0005, funding_rate_8h=0.0001, slippage_bps=2). 7/7 testów przechodzi (`tests/test_costs.py`) |
| C5.5 | `backtest/engine.py` — pętla sygnał → risk_controller → PnL z kosztami → equity curve | ✅ | Zaimplementowane: `run_backtest`. Prawdziwy `risk_controller` (Commit 5.5, `agents/risk_controller.py::compute_sizing`) wstrzyknięty jako domyślny `risk_controller_fn`, wymienny bez zmiany pętli. Reżim filtrowany własnym boolean maskiem (nie `split_by_regime()`) żeby zachować index do lookupu ceny wyjścia dla timeoutów. Sygnały z obu reżimów sortowane po `timestamp` przed sekwencyjną symulacją equity. Kill-switch (`check_kill_switch`) sprawdzany co sygnał przed sizingiem. 3/3 testy integracyjne przechodzi (`tests/test_engine.py`) |
| C5.6 | Trade journal — logowanie transakcji w ustrukturyzowanym formacie już przy pierwszej implementacji | ✅ | `run_backtest` zwraca `trades: pd.DataFrame` z `TRADE_COLUMNS` (entry/exit price, position_size, gross/net PnL, equity before/after) — ustrukturyzowany format od pierwszej implementacji |

### Commit 5.5 — Risk controller (`agents/risk_controller.py`) — ✅ ZROBIONE

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C5.5.1 | Kontrakt wejścia/wyjścia (`signal_direction`/`signal_confidence`/`regime`/`atr_14`/`entry_price` → `position_size`/`stop_price`/`take_profit_price`) | ✅ | Zaimplementowane: `agents/risk_controller.py::compute_sizing` — dokładnie ten kontrakt, drop-in replacement dla `risk_controller_fn` w `backtest/engine.py::run_backtest` (kwargs identyczne z docs/rag/03). Dwuwarstwowy design: `compute_position_size` (czysty numeryczny rdzeń, zwraca float) + `compute_sizing` (pełny kontrakt ze słownikiem) — pozwala hypothesis property testom trzymać się dokładnie szablonu z docs/rag/05 |
| C5.5.2 | Sizing: `size_risk`, `size_leverage`, `position_size = min(size_risk, size_leverage)` | ✅ | Leverage cap zawsze wygrywa — CLAUDE.md zasada 5. Zaimplementowane w `compute_position_size`. Test hypothesis `test_position_size_never_exceeds_leverage_cap` (property, adaptowany z szablonu docs/rag/05) potwierdza cap niezależnie od `equity`/`atr_14`/`entry_price` |
| C5.5.3 | Parametry startowe: `risk_per_trade=0.5%`, `max_leverage=3x` | ✅ | `RISK_PER_TRADE=0.005`, `MAX_LEVERAGE=3.0` w `agents/risk_controller.py` ("wartość startowa"), zdublowane w `config/settings.yaml` sekcja `risk` jako źródło prawdy do przyszłej kalibracji. `atr_multiplier` importowany z `agents.labeling.ATR_MULTIPLIER`, nigdy redefiniowany lokalnie — CLAUDE.md zasada 3 |
| C5.5.4 | `signal_confidence` skaluje `risk_per_trade` liniowo | ✅ | `compute_sizing`: `effective_risk_per_trade = risk_per_trade * signal_confidence`, skaluje WYŁĄCZNIE `size_risk` — `size_leverage` zostaje twardym sufitem niezależnym od confidence (inaczej cap z C5.5.2 przestałby być prawdziwym hard cap). Test `test_compute_sizing_scales_effective_risk_by_confidence` + hypothesis `test_position_size_monotonic_nondecreasing_in_confidence` |
| C5.5.5 | Kill-switch (drawdown > X% od peaku → stop nowych sygnałów) | ✅ | `check_kill_switch(equity, peak_equity, drawdown_threshold=0.15)` — próg **15%** (decyzja użytkownika, nie rekomendowane 20%), re-check **dynamiczny** przy każdym sygnale (nie permanentny latch — wznawia się, gdy equity odzyska się powyżej progu), fail-safe `peak_equity <= 0` → `True`. Wpięty w `backtest/engine.py::run_backtest`: sprawdzany PRZED sizingiem każdego sygnału, sygnały stłumione trafiają do `trades` z `kill_switch_active=True` (position_size=0.0, equity bez zmian) zamiast osobnej listy — jeden trade journal, nie dwa równoległe źródła prawdy. 5 testów jednostkowych + hypothesis `test_check_kill_switch_matches_drawdown_formula` + integracyjny `test_run_backtest_kill_switch_suppresses_signals_after_large_drawdown` (oversized stub risk_controller_fn wymusza drawdown deterministycznie) |

### Commit 6 — Checkpoint go/no-go — ✅ ZROBIONE (wynik: **NO-GO**)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C6.1 | Policzyć Sharpe po kosztach per fold | ✅ | Zaimplementowane: `backtest/metrics.py::compute_fold_metrics` (zwrot per trade = net_pnl/equity_before, wyklucza `kill_switch_active`; Sharpe annualizowany `sqrt(trades_per_year)`, `trades_per_year` z częstości transakcji per-fold; NaN gdy <2 transakcje lub zerowa wariancja). Realny przebieg (`backtest/run_checkpoint.py`, BTC/USDT:USDT 5m, 2025-07-01→2026-06-30, 105120 świec, brak dziur): tylko 1/40 foldów (regime×fold_idx) miało policzalny Sharpe = **-65.43** (range, fold_idx=0, 35 transakcji); pozostałe 39 NaN (brak transakcji albo fold pominięty przez `min_train_rows`) |
| C6.2 | Klasyfikacja wyniku: GO / WARUNKOWY / NO-GO wg kryteriów z §5 | ✅ | `classify_checkpoint`: **NO-GO** (fraction_le_zero=1.0 > 0.5 próg w jedynym policzalnym foldzie). Wg reguły routingu: wróć do Commit 2 (inna hipoteza/cechy), NIE tuning tego zestawu (§5). Pełna analiza przyczyn: IMPLEMENTATION_PLAN.md §6/§7 |
| C6.3 | Stabilność wyniku przy losowym seedzie modelu (overfitting sanity check) | ✅ | 10 seedów (42-51, ustalone z użytkownikiem) przez `backtest/run_checkpoint.py`: WSZYSTKIE dały identyczny mean_sharpe=-65.4333 (std=0.0000 < próg 0.2) → **stabilne** — głównie dlatego, że tylko 1 fold z 40 kiedykolwiek generuje transakcje, a jego wynik okazał się niezależny od seeda modelu w tym przebiegu |
| C6.4 | Wynik osobno per reżim rynkowy — zinterpretowane jako trend vs range (nie kalendarzowo, patrz Uwagi) | ✅ | Realny zakres danych (2025-07→2026-07) nie sięga 2023 — interpretacja kalendarzowa z opisu zadania nie pasowała, zamieniona (za zgodą użytkownika) na podział wg reżimu. Wynik `summarize_by_regime`: **trend = WARUNKOWY (0/20 foldów policzalnych — WSZYSTKIE pominięte przez `min_train_rows`, reżim empirycznie prawie nieobecny w 14-dniowych oknach testowych, potwierdza ryzyko z C2.5/§7 IMPLEMENTATION_PLAN.md)**; **range = NO-GO (1/20 foldów policzalnych, Sharpe=-65.43)** |
| C6.5 | Decyzja udokumentowana w `IMPLEMENTATION_PLAN.md` | ✅ | Udokumentowane w §5 (Commit 6) i §6/§7 — pełny opis liczb i przyczyn. Wynik: **NO-GO**. **Korekta (Commit 2b):** przyczyna "1/20 foldów z transakcjami" dla `range` opisana tu pierwotnie ("predict_signal zwraca wyłącznie direction=0") okazała się błędna — patrz Commit 2b niżej i IMPLEMENTATION_PLAN.md §5 |

### Commit 2b — Diagnoza NO-GO: przegląd cech modelu `range` (W TRAKCIE — zablokowane na nowej decyzji użytkownika)

> Zakres uzgodniony z użytkownikiem 2026-08-01: WYŁĄCZNIE przegląd/rewizja feature setu modelu
> `range` (`REVERSION_FEATURES`) — jawnie wykluczone: rekalibracja progów regime (C2.5), zmiana
> mnożnika ATR triple-barrier. Pełna diagnoza: `IMPLEMENTATION_PLAN.md` §5 Commit 2b.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2b.1 | Zbudować read-only diagnostykę: per fold `range`, rozkład triple-barrier label, feature importance (`gain`), pełny rozkład `signal_confidence` (nie tylko `direction != 0`) | ✅ | `backtest/diagnose_range_signal.py` (poza pytest, jak `run_checkpoint.py`) — zachowany jako trwałe narzędzie. WYNIK: pierwotna diagnoza Commit 6 ("`predict_signal` zwraca wyłącznie `direction=0` w 19/20 foldów") jest BŁĘDNA — model sygnalizuje w ~99-100% wierszy testowych w KAŻDYM z 20 foldów (17 989/17 989 z policzalnym labelem), z sensowną confidence (~0.44-0.50 vs 0.33 baseline) i niezerowym, zmiennym feature importance dla wszystkich 4 cech. Rozkład labeli train/test sensownie zbalansowany w każdym foldzie — brak strukturalnego braku zdarzeń +1/-1. Model NIE jest wąskim gardłem |
| C2b.1b | Zweryfikować rzeczywisty mechanizm "0 transakcji" w 19/20 foldów `range`, skoro model jednak sygnalizuje | ✅ | Zweryfikowano ad hoc na `run_backtest(seed=42)["trades"]`/`["folds_summary"]`: 18 135 sygnałów kandydujących łącznie, **18 100 (99,8%) stłumionych przez kill-switch**, tylko **35** realnych transakcji (dokładnie zgodne z Commit 6). Kill-switch uruchomił się 2025-09-27 (3. dzień fold_idx=0 `range`) i NIGDY nie wznówił działania do końca datasetu (2026-06-30) — equity zamrożone na 8469,93 (drawdown 15,30%) permanentnie, bo bez realnej transakcji (a tę właśnie blokuje kill-switch) equity nie może się poruszyć. `check_kill_switch` sam w sobie poprawny/bezstanowy/dynamiczny — to deadlock EMERGENTNY z resztą pętli `run_backtest`, nie błąd tej funkcji. Osobne, niezbadane pytanie: dlaczego pierwsze ~9-10 transakcji fold 0 straciło tak konsekwentnie — poza zakresem tej rundy |
| C2b.2 | Dodać jedną kandydującą cechę do `REVERSION_FEATURES` (np. Bollinger %B) | ⏳ | **WSTRZYMANE** — C2b.1/C2b.1b obalają przesłankę ("model rzadko sygnalizuje"). Rozszerzanie feature setu nie zaadresuje rzeczywistej przyczyny. Czeka na NOWĄ decyzję użytkownika o zakresie — prawdopodobnie `agents/risk_controller.py` (mechanizm odzyskiwania kill-switcha i/lub formuła sizingu), co wymaga własnego przeczytania docs/rag/03 przed zmianą (CLAUDE.md) i jest POZA uzgodnionym zakresem tej rundy |
| C2b.3 | Ponowny checkpoint (`run_checkpoint.py`) po C2b.2, porównanie z baseline Commit 6 | ⏳ | Zablokowane przez C2b.2 |

### Commit 2c — Kill-switch: przyczyna serii strat + mechanizm cooldown/re-arm — ✅ ZROBIONE

> Zakres zatwierdzony przez użytkownika 2026-08-01 ("1.yes 2.yes" + "Do both in one round" +
> "tak jak uważasz za najlepsze" dla wyboru mechanizmu): diagnoza przyczyny serii strat + naprawa
> deadlocka kill-switcha, jedną rundą. Pełna diagnoza i wyniki: `IMPLEMENTATION_PLAN.md` §5 Commit 2c.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2c.1 | Root-cause diagnostyka serii strat wywołującej kill-switch (`backtest/diagnose_kill_switch_trigger.py`) | ✅ | Read-only skrypt inspekcji 35 realnych transakcji — rozbija koszt na fee/funding/slippage. WYNIK: 100% transakcji `signal_direction=1.0` (long) podczas trwałego spadku ceny BTC (~-3,6% w 3 dni) sklasyfikowanego jako `range`; 26/35 (74%) genuinie zły kierunek, 9/35 koszt > zysk brutto. Kill-switch NIE był wadliwy — poprawnie wykrył realną serię strat. Przyczyna głębsza (jakość sygnału/klasyfikacja reżimu) POZA zakresem tej rundy |
| C2c.2 | Zaprojektować i zaimplementować mechanizm naprawy deadlocka kill-switcha | ✅ | Cooldown/re-arm: `agents.risk_controller.should_rearm_kill_switch` (nowa czysta funkcja, testowalna w izolacji) + `KILL_SWITCH_COOLDOWN_DAYS=7.0` (domyślnie, `config/settings.yaml` sekcja `risk`) — po N dni ciągłej suppresji, `backtest.engine.run_backtest` resetuje `peak_equity` do bieżącego equity. `check_kill_switch` sam w sobie niezmieniony (nadal czysty/bezstanowy). Testy: 4 jednostkowe + 3 hypothesis property tests w `tests/test_risk_controller.py`, 1 nowy integracyjny (`test_run_backtest_kill_switch_re_arms_after_cooldown`) w `tests/test_engine.py`. Pełny zestaw: **94/94 przechodzi** |
| C2c.3 | Ponowny checkpoint (`run_checkpoint.py`) po naprawie, porównanie z baseline Commit 6/2b | ✅ | Range: 1/20→**20/20** foldów z policzalnym Sharpe (35→**2 562** transakcji), mean_sharpe=-53,41 (fraction_le_zero=1,0). Trend: 0/20→**3/20** foldów (mean_sharpe=-7,15). Ogólnie: **NO-GO potwierdzone** (23/40 foldów ważnych, wcześniej 1/40), stabilne na 10 seedach (std=0,0000). Naprawa nie zmienia werdyktu, ale czyni go dużo bardziej wiarygodnym — patrz IMPLEMENTATION_PLAN.md §5/§6/§7 |

### Commit 2d — Bramka wykonalności kosztowej — ✅ ZROBIONE

> Zakres uzgodniony z użytkownikiem 2026-09-21. Runda miała być C2.5 (rekalibracja progów regime);
> read-only diagnostyka przed startem obaliła jej przesłankę, więc zakres zmieniono za zgodą
> użytkownika na bramkę kosztową, a C2.5 przesunięto na następną, osobną rundę (jedna zmiana na
> raz). Pełna diagnoza i liczby: `IMPLEMENTATION_PLAN.md` §5 Commit 2d.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2d.0 | Diagnostyka wykonalności kosztowej (`backtest/diagnose_cost_feasibility.py`) | ✅ | Read-only skrypt (3 bloki: rozkład reguły reżimu, bariera vs koszt, dekompozycja realnych transakcji), zachowany jako trwałe narzędzie. WYNIKI: (1) `direction_persistence_10` jest DYSKRETNA (`k/10`), próg 0,7 wpada w lukę rozkładu — to on, nie ATR, czyni `trend` prawie pustym (0,53%; przy 0,5 → 4,53%); (2) w `range` mediana bariery 1.5×ATR = **0,130% ceny** < koszt **0,140% nominału** → wymagana trafność break-even **103,9%, arytmetycznie nieosiągalna**, 56,8% świec nie pokrywa kosztu nawet przy pełnym trafieniu; (3) model `range` trafiał kierunek w **54,6%** transakcji, a mimo to 42% transakcji z dobrym kierunkiem kończyło netto ujemnie (gross -569 vs koszt 9 168). Wniosek: NO-GO Commitu 2c był w ~94% wynikiem arytmetycznym, nie statystycznym |
| C2d.1 | Czysta funkcja bramki + wpięcie w pipeline | ✅ | `agents.risk_controller.is_cost_feasible` (+ rdzeń `barrier_to_cost_ratio`): sygnał dopuszczony tylko gdy `(atr_multiplier*atr_14)/entry_price >= min_barrier_to_cost_ratio * cost_fraction`. Próg startowy **2.0** (`config/settings.yaml` sekcja `risk`) wyprowadzony z break-even `p=0.5*(1+1/ratio)` → 75%, NIE z przeszukiwania po Sharpe (CLAUDE.md zasada 1). `cost_fraction` z nowej `backtest.costs.round_trip_cost_fraction()` — te same stałe co `total_round_trip_cost`, zero duplikacji. Filtruje KANDYDATURĘ sygnału w `_collect_candidate_signals` (nie trafia do trade journalu — to właściwość świecy, nie zdarzenie w torze equity, w odróżnieniu od kill-switcha), licznik w `folds_summary["n_signals_cost_gated"]`; `backtest/metrics.py` bez zmian. NIE jest progiem na `signal_confidence` (docs/rag/03 świadomie taki odrzuca — bramka jest ortogonalna). `atr_multiplier` nietknięty (CLAUDE.md zasada 3) |
| C2d.2 | Testy jednostkowe + hypothesis + integracyjne (DoD docs/rag/05) | ✅ | 7 jednostkowych + **4 hypothesis** w `tests/test_risk_controller.py` (zgodność bramki ze stosunkiem, monotoniczność niemalejąca w `atr_14`, próg 0.0 przepuszcza wszystko, fail-safe dla `entry_price<=0`/`cost_fraction<=0`/NaN, reprodukcja diagnozy `range`), 3 w `tests/test_costs.py`, 2 integracyjne w `tests/test_engine.py` (księgowanie bez gubienia sygnałów, bramka domyślnie włączona). Trzy testy sprzed 2d dostały jawne `min_barrier_to_cost_ratio=0.0` — ich przedmiotem jest kill-switch. Pełny zestaw: **110/110 przechodzi** (94 + 16) |
| C2d.3 | Ponowny checkpoint po bramce, porównanie z baseline Commit 2c | ✅ | Bramka odcięła **17 547 z 18 135 sygnałów (96,8%)**, w `range` 97,5%. Foldy z policzalnym Sharpe 23/40→**6/40**, transakcje 2 625→**358**, mean_sharpe -47,38→**-14,31** (range -26,01, trend -8,46, przy czym trend ma teraz 25% foldów z Sharpe>0,5 wobec 0% wcześniej). **Łączny gross -593 → +166** — strata BYŁA kosztowa, diagnoza potwierdzona empirycznie. ALE: trafność kierunku w `range` spada 54,6%→**49,3%** na świecach przechodzących bramkę — edge mieszkał w świecach nieopłacalnych. **Werdykt: NO-GO**, stabilne na 10 seedach (std=0,0000). Regresja kontrolna `min_barrier_to_cost_ratio=0.0` odtwarza baseline Commitu 2c co do ostatniej cyfry (-47,377414474779975, 23/40) |

### Commit 2.5 — Kalibracja progów reguły regime — ✅ ZROBIONE (wynik: NO-GO, hipoteza falsyfikowana)

> Zakres uzgodniony z użytkownikiem 2026-09-21 ("comitować wszystko, Chcesz, żebym tak rozpisał i
> odpalił C2.5 tak"): bounded-autonomy — z góry zarejestrowany, mały, strukturalnie (nie z PnL)
> uzasadniony zestaw kandydatów progów regime, oceniony przez pełny walk-forward checkpoint, bez
> automatycznego wyboru zwycięzcy. Pełna diagnoza, tabela i surowy output:
> `IMPLEMENTATION_PLAN.md` §5 Commit 2.5, `runs/2026-09-21_c2.5-threshold-calibration.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.5.1 | Parametryzacja progów regime (`agents/feature_miner.py`, `backtest/engine.py`) + testy (DoD docs/rag/05) | ✅ | `DEFAULT_TREND_THRESHOLD=0.7`/`DEFAULT_RANGE_THRESHOLD=0.3` jako nazwane stałe (mirroring `config/settings.yaml`, wzorzec `ATR_MULTIPLIER`); `classify_regime`/`compute_all_features`/`run_backtest` przyjmują i przekazują progi dalej, bez zmiany domyślnego zachowania. Testy: 6 nowych jednostkowych w `tests/test_feature_miner.py` (nowy plik — dotąd `feature_miner.py` miał pokrycie tylko przez test leakage, nie testu POPRAWNOŚCI reguły progowej) + 1 integracyjny w `tests/test_engine.py` (próg nieosiągalny 0.99 ⇒ zero sygnałów trend, weryfikuje przekazanie parametru end-to-end). Pełny zestaw: **117/117 przechodzi** (110 + 7) |
| C2.5.2 | Skrypt kalibracyjny (`backtest/calibrate_regime_thresholds.py`) + uruchomienie na realnych danych, 4 kandydaci × 10-seed sweep | ✅ | 4 kandydaci z góry zarejestrowani ze STRUKTURY dyskretnego wsparcia `direction_persistence_10` (`{0,0.2,0.4,0.6,0.8,1.0}`), nie z podglądania Sharpe'a (CLAUDE.md zasada 1): `(0.7,0.3)` baseline, `(0.6,0.4)` kontrola, `(0.5,0.3)`, `(0.5,0.5)`. WYNIK: **wszystkie 4 NO-GO**, `mean_sharpe` POGARSZA SIĘ wraz z poluzowaniem progów (-14,31→-14,25→-18,00→-19,58, stabilne na 10 seedach każdy, std=0,0000). Poluzowanie zwiększa populację `trend` (0,50%→4,28%) i `range` (21,13%→44,18%), ale dodane świece są GORSZEJ jakości, nie lepszej — falsyfikuje hipotezę "brakujące świece kryją niewykorzystany edge". Kandydat kontrolny `(0.6,0.4)` NIE odtworzył populacji baseline (przewidywanie w docstringu było błędne — `atr_pctrank_20d` jest ciągła, więc próg zmienia populację nawet w "luce" rozkładu `persistence`), udokumentowana korekta własnej hipotezy. **Decyzja: `config/settings.yaml` pozostaje przy baseline (0,7/0,3)** — najlepszy (najmniej ujemny) z czterech wyników, zgodnie z regułą routingu checkpointu (docs/rag/03: NO-GO → rejestr cech, nie dalszy tuning) |

### Commit 2.6 — Odporność hipotezy na timeframe (1h, 4h) — ✅ ZROBIONE (wynik: NO-GO, hipoteza falsyfikowana)

> Zakres uzgodniony z użytkownikiem 2026-09-21: użytkownik zauważył krótki horyzont trzymania
> pozycji na 5m (max. 1h) i zapytał, czy NO-GO utrzymuje się na grubszych interwałach (1h, 4h),
> gdzie bariera ATR rośnie względem stałego kosztu. Zmieniona WYŁĄCZNIE granulacja danych +
> niezbędna konwersja jednostek (`candles_per_day`) — reszta pipeline'u (progi, ATR_MULTIPLIER,
> bramka kosztowa) niezmieniona. Pełna diagnoza: `IMPLEMENTATION_PLAN.md` §5 Commit 2.6,
> `runs/2026-09-21_c2.6-timeframe-robustness.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.6.1 | `resample_ohlcv` (`data/fetch_ohlcv.py`) + parametryzacja `candles_per_day` (`agents/feature_miner.py`, `backtest/engine.py`) + testy | ✅ | Sandbox nie ma dostępu do Binance (`fapi.binance.com` → 403 na proxy) — dane 1h/4h AGREGOWANE z bazy 5m (open/high/low/close/volumen, odrzucanie niepełnych bucketów brzegowych), jawnie odróżnione od potencjalnego natywnego fetcha. `candles_per_day` (288→24→6) sparametryzowane analogicznie do progów C2.5 — bez tego okno "20 dni" ATR percentile liczyłoby błędną liczbę dni na innym timeframe. Testy: 4 nowe w `tests/test_fetch_ohlcv.py` (agregacja OHLC/volumenu, spójność 5m→4h vs 5m→1h→4h, odrzucanie niepełnego bucketu, walidacja timeframe), 3 w `tests/test_feature_miner.py`, 1 integracyjny w `tests/test_engine.py`. Pełny zestaw: **125/125 przechodzi** (117 + 8) |
| C2.6.2 | Skrypt `backtest/checkpoint_timeframe_robustness.py` + uruchomienie na 5m (referencja)/1h/4h, 10-seed sweep każdy | ✅ | Dokładny bezresztowy podział z 105 120 świec 5m: 8 760 (1h), 2 190 (4h). WYNIK: **oba NO-GO** — 1h mean_sharpe=-15,57, 4h mean_sharpe=-8,75 (5m referencja: -14,31), stabilne na 10 seedach (std=0,0000 każdy). Diagnostyka bariera-vs-koszt (metodologia Commitu 2d) POTWIERDZA naprawę mechanizmu: 0% świec arytmetycznie niewykonalnych na 1h/4h (wobec 56,8% na 5m), wymagana trafność break-even spada z 103,9% do 54–61%. MIMO TO trafność kierunku pozostaje ~49,0% (1h, rzut monetą) albo spada do ~41,2% (4h, gorzej niż losowo). Regime `trend` praktycznie pusty na 1h/4h (0 transakcji) — `direction_persistence_10` pozostał na STAŁEJ liczbie 10 świec, nieprzeliczonej per timeframe (świadomy zakres tej rundy). **Trzeci niezależny test (po bramce kosztowej i progach regime) wskazujący, że problem jest w modelu/cechach, nie w koszcie/kalibracji/granulacji danych** |

### Commit 2.7 — Przegląd kandydatek nowych cech: korelacje — ✅ ZROBIONE (wynik: 1 cecha odrzucona, brak sygnału cecha-target)

> Zakres uzgodniony z użytkownikiem 2026-09-21 ("a czy nie lepiej zrobić X zmiennych i sprawdzić
> korelacje między nimi, a dopiero później zbudować model" → "tak zaproponuj i sporzać
> korelacje"): korelacja cecha-cecha (Spearman, cały zbiór) jako BEZPIECZNY krok redundancji;
> korelacja cecha-target dopuszczona WYŁĄCZNIE jako opisowa/eksploracyjna (nigdy jako bramka
> selekcji) — per `docs/rag/02_cechy_i_leakage.md` "Rozszerzanie feature setu — protokół" i
> CLAUDE.md zasada 4. Pełna diagnoza: `IMPLEMENTATION_PLAN.md` §5 Commit 2.7,
> `runs/2026-09-21_c2.7-feature-candidate-screening.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.7.1 | 8 nowych kandydatek cech (4 rodziny: volatility, momentum, mean-reversion, volume), świadomie nie-redundantnych z registry na podstawie definicji wzoru | ✅ | `backtest/screen_feature_candidates.py` (poza pytest, jak inne skrypty analityczne): `bb_width_20`, `realized_vol_20` (volatility, TA-Lib BBANDS/rolling std log-zwrotów); `roc_20`, `adx_14` (momentum/trend-strength, TA-Lib ADX); `bb_pctb_20`, `vwap_deviation_20` (mean-reversion, TA-Lib BBANDS/rolling VWAP); `obv_zscore_20`, `volume_roc_10` (volume, TA-Lib OBV). Ten sam kontrakt trailing-only co `agents/feature_miner.py`. NIE wchodzą do `FEATURE_FUNCTIONS`/`MOMENTUM_FEATURES`/`REVERSION_FEATURES` — screening przed-rejestracyjny, formalny test leakage dopiero przy promocji |
| C2.7.2 | Macierz korelacji Spearman cecha-cecha (17×17: 9 istniejących + 8 nowych), cały zbiór, próg redundancji opisowy `\|corr\|>0.7` | ✅ | WYNIK: 28 par powyżej progu. Najważniejsze: `bb_pctb_20` **PERFEKCYJNIE redundantny** z już używanym `price_zscore_20` (corr=+1,000, afiniczna transformacja tej samej wielkości) → **ODRZUCONY** bez potrzeby testu OOS. `adx_14` jedyny kandydat z niską korelacją do reszty registry (w tym +0,07 z `direction_persistence_10`, mimo że oba mają mierzyć "siłę trendu") → wyróżniony jako kandydat #1. Rodzina volatility (`bb_width_20`/`realized_vol_20`) silnie redundantna z istniejącymi `atr_14`/`atr_pctrank_20d` (corr 0,79–0,88). `obv_zscore_20` bliżej mean-reversion/momentum niż volume (corr 0,72–0,78 z `price_zscore_20`) |
| C2.7.3 | Korelacja Spearman cecha-target (label triple-barrier jako -1/0/1) per regime, jawnie oznaczona EKSPLORACYJNA (bez p-value, żeby nie sugerować istotności) | ✅ | WYNIK: żadna z 17 cech nie przekracza \|corr\|≈0,065 z targetem w żadnym reżimie (`trend`: n=523, max=-0,065 `volume_roc_10`; `range`: n=22 198, max=-0,035 `realized_vol_20`). Czwarty niezależny sygnał (po C2.5 progach, C2.6 timeframe) spójny z brakiem edge'u — tym razem metodą niezależną od modelu XGBoost. Żadna cecha nie wyróżnia się ponad poziom szumu — decyzja, którą (jeśli jakąkolwiek) testować formalnie w walk-forward, pozostaje przy użytkowniku |

### Commit 2.8 — Formalny test OOS: `adx_14` dodane do MOMENTUM_FEATURES — ✅ ZROBIONE (wynik: NO-GO ogólnie, poprawa marginalna w trend)

> Zakres uzgodniony z użytkownikiem 2026-09-21 ("sformalizować test OOS dla adx_14"):
> jedna cecha (CLAUDE.md zasada 4), DODANA do `MOMENTUM_FEATURES` (Test 1/trend),
> `REVERSION_FEATURES` (Test 2/range) niezmienione. Pełna diagnoza:
> `IMPLEMENTATION_PLAN.md` §5 Commit 2.8, `runs/2026-09-21_c2.8-adx14-oos-evaluation.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.8.1 | Promocja `compute_adx_14` do produkcyjnego registry (`agents/feature_miner.FEATURE_FUNCTIONS`, `agents/feature_registry.yaml`) + testy (DoD docs/rag/05) | ✅ | 10. cecha w `FEATURE_FUNCTIONS` — formalny test leakage (parametryzowany po kluczach) automatycznie objął `adx_14` (licznik 9→10, `agent_5_compliance/test_leakage.py`), + nowy jednostkowy test granic [0,100] w `tests/test_feature_miner.py`. Wpis w `feature_registry.yaml` z notatką o pochodzeniu (screening C2.7) i statusie (kandydat do MOMENTUM_FEATURES, nie jeszcze promowany) |
| C2.8.2 | Parametryzacja `regime_feature_sets` w `backtest/engine.py::run_backtest` (ten sam wzorzec threading co progi C2.5/candles_per_day C2.6) + test integracyjny | ✅ | Pozwala porównać warianty feature setu (baseline vs baseline+adx_14) przez identyczny pipeline, bez duplikacji logiki i bez trwałej zmiany `agents/ml_optimizer.py`. Nowy test `test_run_backtest_threads_regime_feature_sets_to_model_training` (dowód przez `KeyError` przy podaniu nieistniejącej kolumny cechy). Pełny zestaw: **128/128 przechodzi** (125 + 3: 1 unit adx_14 + 1 integracyjny + 1 nowa instancja parametryzowanego testu leakage) |
| C2.8.3 | Skrypt `backtest/evaluate_feature_candidate.py` (poza pytest) + uruchomienie: baseline (4 cechy) vs kandydat (+adx_14, 5 cech), pełny walk-forward + 10-seed sweep | ✅ | WYNIK: mean_sharpe -14,31→**-13,69** (poprawa), trend_sharpe -8,46→**-7,11** (poprawa, klasyfikacja NO-GO→**WARUNKOWY**), ale **klasyfikacja OGÓLNA pozostaje NO-GO** w obu wariantach (stabilne, std=0,0000 na 10 seedach). Poprawa w trend opiera się na JEDNYM foldzie (fold_idx=11) zmieniającym Sharpe z -2,40 na +0,09 (praktycznie zero) przy tylko 4 ważnych foldach trend — słaby, niejednoznaczny dowód. `range` (dominujący w werdykcie) kompletnie niezmieniony. **Piąty niezależny wynik w paśmie "brak silnego sygnału"** (po C2.5/C2.6/C2.7). Decyzja o promocji `adx_14` do `MOMENTUM_FEATURES` na stałe — przy użytkowniku; skrypt świadomie nie wybiera zwycięzcy. **Aktualizacja C2.9:** "std=0,0000 na 10 seedach" okazało się puste (deterministyczny XGBoost), a poprawa +0,61 to ~0,2σ zmierzonego szumu fold-jitter — nierozstrzygalna |

### Commit 2.9 — Naprawa metodologii pomiaru (Backlog Z1–Z4, Z11–Z15) — ✅ ZROBIONE (NO-GO odporne na fold-jitter; zwrot per trade istotnie ujemny w obu reżimach)

> Zakres: pierwsza transza backlogu z audytu 2026-09-21, na polecenie użytkownika ("Dopisz i
> wypchnij do repo a później zacznij realizować"). Zero zmian w hipotezie/cechach/progach/
> kosztach/modelu — wyłącznie metodologia pomiaru + higiena. Pełna diagnoza:
> `IMPLEMENTATION_PLAN.md` §5 Commit 2.9, `runs/2026-09-21_c2.9-measurement-methodology.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.9.1 | (Z1) Fold-jitter zamiast pustego sweepu seedów: `start_offset_days` w `generate_walk_forward_folds` + `fold_start_offset_days` w `run_backtest` + testy (unit + hypothesis, DoD Warstwa 3 dla labeling.py + integracyjny threading) | ✅ | Odkrycie audytu: XGBoost bez `subsample`/`colsample` jest deterministyczny — seed nie zmieniał NIC, każde dotychczasowe "std=0,0000 STABILNY" (C6→C2.8, ~10 rund) było puste poznawczo. Offset perturbuje ARBITRALNE wyrównanie granic foldów; offset=0 odtwarza baseline co do ostatniej cyfry. Świadomie bez nowego progu pass/fail — raport rozkładu + spójność znaku, interpretacja przy użytkowniku. docs/rag/03 zaktualizowane |
| C2.9.2 | (Z2+Z3) `compute_t_stat` + kolumna `t_stat` per fold + `summarize_pooled_by_regime` (pooled Sharpe/t-stat per regime) + `effective_sample_size` (C4.4, dotąd nieużywane) wpięte jako `n_eff`/`t_stat_neff` | ✅ | Bez annualizacji (sqrt(~800/rok) przy n=31–37 nadmuchiwał Sharpe do ±20–60). Kryteria klasyfikacji GO/WARUNKOWY/NO-GO NIEZMIENIONE — nowe miary to diagnostyka obok werdyktu. Guard: N_eff przycinany do (0, n], NaN przy n<10 albo zdegenerowanym estymatorze. 5 nowych testów w `tests/test_metrics.py` |
| C2.9.3 | (Z13) `backtest/checkpoint_lib.py` (wspólna biblioteka, FORWARD-LOOKING — historyczne skrypty zamrożone) + `backtest/run_checkpoint_v2.py` (kanoniczny checkpoint v2) + uruchomienie na realnych danych | ✅ | WYNIK: **NO-GO w 10/10 offsetów** (mean_sharpe zakres [-15,89; -6,20], std=3,09, znak ujemny 100%) — pierwsza REALNA weryfikacja odporności werdyktu. Pooled: `range` n=223, **t=-7,15**; `trend` n=135, **t=-2,91**, N_eff=110 → **t_neff=-2,63** — zwrot per trade istotnie ujemny w OBU reżimach. Zmierzony szum σ≈3,1 → porównania wariantów o Δ<~3 nierozstrzygalne na rocznych danych (→ priorytet Z5). `run_checkpoint.py` zostaje jako zamrożony zapis Commitu 6 |
| C2.9.4 | Higiena: (Z11) `candle_minutes` przewleczone do `total_round_trip_cost` + test integracyjny; (Z12) lint 0 błędów (unused numpy, 3×E741); (Z14) README odświeżone (status, struktura z `runs/`); (Z15) test spójności registry↔kod czyta YAML; (Z4) kolumna "Warianty" + suma w `runs/INDEX.md` | ✅ | Pełny zestaw: **139/139 testów przechodzi** (128 + 11: 2 labeling + 5 metrics + 3 engine + 1 zamiana testu registry) |

### Commit 2.10 — Wydłużenie historii danych do 3 lat (Backlog Z5) — ✅ ZROBIONE (NO-GO na nowej bazie; niska liczba ważnych foldów okazała się strukturalna)

> Zakres: Backlog Z5, wykonane na maszynie użytkownika (Binance dostępne). Decyzja użytkownika:
> **3 lata** (2023-07-01 → 2026-07-01), `end` bez zmian. Zero zmian w hipotezie/cechach/progach/
> kosztach/modelu — wyłącznie dane + utwardzenie fetchu. To NOWA BAZA checkpointu, nie porównanie
> 1:1 z C6–C2.9. Pełny wynik: `runs/2026-09-21_c2.10-extended-history-z5.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.10.1 | Utwardzenie `data/fetch_ohlcv.py`: `_fetch_page_with_retry` (backoff wykładniczy na `ccxt.NetworkError`, max 5 prób; `ExchangeError` bez retry) + log postępu; 4 testy (Warstwa 1, stub bez sieci) | ✅ | Powód: ~316 sekwencyjnych stron bez retry, zapis dopiero po pętli — jeden timeout tracił całość. Semantyka cache/nazwy pliku NIEZMIENIONA (nazwa koduje zakres → nowy zakres = nowy plik). Pełny zestaw: **143/143** (139 + 4). Ruff nieuruchomiony — brak na tej maszynie |
| C2.10.2 | `data.start` → 2023-07-01 w config; `py -m data.fetch_ohlcv`; weryfikacja integralności PRZED checkpointem | ✅ | **315 648 świec = 1096×288, zero dziur/duplikatów/NaN**, bez ani jednego retry (~2 min). Overlap 2025-07→2026-07 vs stary plik: 105 120 wierszy, max \|Δ\|=0 na wszystkich kolumnach, `equals=True`. Stary parquet ZOSTAJE jako zamrożone źródło C6–C2.9 |
| C2.10.3 | `py -m backtest.run_checkpoint_v2` (pełny sweep) na nowej bazie + diagnostyka udziału reżimów i bramki kosztowej z `folds_summary` | ✅ | WYNIK: **NO-GO, 21/144 ważnych foldów** (14,6% — jak 15,0% na roku), mean_sharpe -12,39. Pooled: `range` n=530 **t=-10,47** (N_eff=261, t_neff -7,34); `trend` n=395 **t=-5,51** (N_eff=213, t_neff -4,04) — istotnie ujemny zwrot per trade w obu reżimach z dużym zapasem. Fold-jitter 10/10 ujemne, σ≈2,5 bez outliera (offset 9: -189 — artefakt annualizowanego per-fold Sharpe przy n≈kilka; statystyką nośną są pooled t). **Odkrycie strukturalne:** `trend`=0,53% świec (jak na roku) → 61/72 foldów pominiętych; bramka kosztowa blokuje **98,0% sygnałów `range`** (61 313/62 553) → 60/72 foldów z zerem transakcji. Dłuższa historia tego nie naprawia → Z7 (reguła) / Z6 (koszty) / Z10 |

---

### Commit 2.11 — Instrumentacja edge'u (Runda 1/4 programu „droga do GO") — ✅ ZROBIONE (blokada w geometrii wypłaty, nie w kierunku sygnału)

> Zakres: pierwsza runda czterorundowego programu uzgodnionego z użytkownikiem 2026-09-21
> (instrumentacja → koszty Z6 → próg pewności → reguła reżimu Z7, z pre-rejestrowaną regułą
> STOP po Rundzie 3). Zero zmian w pipeline'ie — wyłącznie przyrząd pomiarowy. Pełny wynik:
> `runs/2026-09-21_c2.11-edge-instrumentation.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.11.1 | `break_even_hit_rate`, `compute_hit_rate`, `summarize_edge_by_regime` w `backtest/metrics.py` + wpięcie do `checkpoint_lib.run_and_summarize` / `run_checkpoint_v2` | ✅ | Motywacja: cały werdykt liczy się z `net_pnl`, a `gross_pnl` (jedyna miara jakości SYGNAŁU) było zapisywane i nigdy nieczytane przez `metrics.py`; trafność istniała tylko jako wyrażenia ad hoc w skryptach diagnostycznych, bez testów. Werdykt redukuje się do **(2p−1)·B > C** — raport pokazuje teraz wszystkie trzy człony + margines. Kryteria GO/NO-GO z docs/rag/03 **NIEZMIENIONE** (diagnostyka obok werdyktu, jak Z2/Z3). Testy: **157/157** (143 + 14: 11 unit + 3 `hypothesis`). WYNIK: werdykt bit-identyczny z C2.10 (regresja baseline'u); trafność **51,9%/50,6%** (z=+0,87/+0,25) vs wymagane **75,8%/64,9%** → luka **−23,9 pp / −14,2 pp** |

---

### Commit 2.12 — Realistyczny model wykonania maker/taker (Backlog Z6, Runda 2/4) — ✅ ZROBIONE (NO-GO, ale ok. połowa luki do opłacalności domknięta)

> Zakres: Runda 2 programu „droga do GO". Decyzja użytkownika: maker na wejściu i take-proficie,
> taker na stop-lossie i timeoucie; slippage tylko na nogach taker. Pełny wynik:
> `runs/2026-09-21_c2.12-execution-cost-model.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.12.1 | `backtest/costs.py`: `MAKER_FEE_RATE`, `leg_fee_rate`, `exit_leg_for_reason`, fee per noga + slippage tylko na nogach taker (domyślne taker/taker wstecznie zgodne) | ✅ | Motywacja: `costs.py` modelował WYŁĄCZNIE takera po obu stronach — to nie było założenie konserwatywne, tylko brak modelu. Asymetria TP=maker/SL=taker działa na NIEKORZYŚĆ strategii o niskiej trafności, więc jest konserwatywna wobec hipotezy. Testy: 9 nowych w `test_costs.py` |
| C2.12.2 | `backtest/engine.py`: kolumna `exit_reason` (z iloczynu `direction*label`), `_execution_legs`, parametr `execution_model`; bramka kosztowa dostaje konserwatywne założenie (wyjście taker) | ✅ | Blokada usunięta po drodze: `label` był konsumowany w `_resolve_exit_price` i nie trafiał do journalu, więc nogi wyjścia nie dało się wycenić. Sam `label` nie wystarcza — short na etykiecie −1 to TP, nie SL. Testy: 16 nowych w `test_engine.py`, w tym **regresja baseline'u** (`taker_only` odtwarza koszt sprzed C2.12 co do cyfry) |
| C2.12.3 | Pełny `run_checkpoint_v2` (kanoniczny + sweep fold-jitter) na 3 latach | ✅ | WYNIK: **NO-GO**, ale koszt **−52%**, foldy ważne **21→54**, transakcje `range` **530→7 155**, zwrot per trade **+35%/+39%**, margines **−23,9→−15,5 pp** / **−14,2→−9,1 pp**. `trend` t_neff = **−1,75** (\|t\|<2, nieodróżnialny od zera). Sprzężenie: tańszy koszt wpuszcza sygnały o węższej barierze (B −25%/−19%), więc break-even spadł tylko o 9,2/5,9 pp. **Ostrzeżenie:** `mean_sharpe` −12,4→−59,6 przy LEPSZEJ ekonomice per trade, fold-jitter σ 3,1→75,7, spójność znaku 100%→80% — per-fold Sharpe (podstawa kryteriów docs/rag/03) przestał być wiarygodnym przyrządem. Testy: **182/182** |

---

## Faza 1 — regime router, funding rate, Compliance Gate

> Start dopiero po wyniku GO/WARUNKOWY z Commitu 6.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F1.1 | Regime router (dispatcher) łączący Test 1 + Test 2 | ⏳ | |
| F1.2 | Funding rate jako cecha Test 2 — jedna cecha na raz, test leakage, OOS | ⏳ | CLAUDE.md zasada 4 |
| F1.3 | Compliance Gate budowany równolegle (nie po fakcie) | ⏳ | |
| F1.4 | Cadence retreningu — harmonogram + triggered retrain przy spadku live performance | ⏳ | Brakujący temat z diagramu Miro, §10 |
| F1.5 | Rozszerzenia cech pojedynczo na OOS: MACD, Bollinger, GMMA | ⏳ | Częściowo redundantne z istniejącymi cechami — testować pojedynczo |
| F1.6 | Onchain data jako kandydat cechy do Test 2 | ⏳ | |
| F1.7 | `Lean.DataSource.BinanceFundingRate` jako źródło danych funding rate | ⏳ | §10 |
| F1.8 | Rozszerzenie walidacji na ETH/SOL/BNB — te same progi i hiperparametry co BTC, bez retuningu | ⏳ | CLAUDE.md zasada 9 — test generalizacji tej samej hipotezy, nie równoległa walidacja 4 niezależnych strategii; start dopiero PO indywidualnej walidacji BTC do końca Commitu 6 |
| F1.9 | Multi-timeframe (Trend/Day/Hour) — potwierdzenie trendu z wyższego interwału | ⏳ | Dopiero po walidacji na 5m, §10 — osobny wymiar złożoności |
| F1.10 | Trailing Stop/Take Profit w `risk_controller.py` | ⏳ | Ulepszenie po walidacji statycznej wersji ATR (Commit 5.5), §10 |
| F1.11 | Expected Shortfall jako uzupełnienie VaR | ⏳ | Naturalne uzupełnienie ogona rozkładu strat, §10 |
| F1.12 | CatBoost / RandomForest jako porównanie/ensemble | ⏳ | Tylko PO potwierdzeniu edge'u XGBoostem (Commit 6 GO), nie zamiennik na start, §10 |

## Faza 2 — LLM offline/nadzorczo (Q&A) + test_mathematics.py

> Pełne uzasadnienie i wzorce: `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`. Nic z tej sekcji nie
> jest budowane przed checkpointem go/no-go Commitu 6.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F2.1 | `test_mathematics.py` — property-based testy niezmienników na realnych/backtestowych danych | ⏳ | Zostaje deterministyczny, bez LLM |
| F2.2 | `ai_interpreter.py` — narzędzia `get_fold_metrics`/`get_feature_definition`/`get_trade_journal`/`get_rag_doc` | ⏳ | Zero narzędzi zapisu/egzekucji |
| F2.3 | Observability/evals minimalny (structured JSON log, eval dataset 20-30 przykładów, human-graded) | ⏳ | |
| F2.4 | Bezpieczeństwo: zero narzędzi zapisu/egzekucji, system prompt traktowany jako publiczny | ⏳ | |

## Faza 3 — paper trading + post_trade_critic.py

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F3.1 | Paper trading / testnet, minimum kilka tygodni | ⏳ | |
| F3.2 | LEAN jako silnik paper tradingu (zamiast freqtrade) | ⏳ | Zaktualizowana rekomendacja, §10 |
| F3.3 | `post_trade_critic.py` — verbal-reinforcement po FinCon, raport markdown | ⏳ | Nigdy automatyczna zmiana parametrów/modelu — tylko raport |
| F3.4 | Weryfikacja formatu trade journal z Commitu 5 pod kątem realnych potrzeb `post_trade_critic.py` | ⏳ | |

## Faza 4 — mały kapitał, skalowanie

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F4.1 | Uruchomienie na małym kapitale (w pełni tolerowalna strata) | ⏳ | |
| F4.2 | Skalowanie po potwierdzeniu wyników | ⏳ | |

---

## Dokumentacja i workflow — niezależne od fazowania

> Można wykonać w dowolnym momencie, nie dotyka logiki tradingowej ani configu.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| D.1 | YAML frontmatter (`status`, `last_verified`, `depends_on`) w każdym `docs/rag/*.md` | ✅ | Dodane 7/7 plikom (`01`–`07`); legenda wartości `status` (`active`/`stale`/`superseded`) w `docs/INDEX.md` |
| D.2 | Plik-indeks (Mapa Treści) linkujący `CLAUDE.md` + `IMPLEMENTATION_PLAN.md` + `docs/rag/*.md` | ✅ | `docs/INDEX.md` — linkuje `CLAUDE.md`+`IMPLEMENTATION_PLAN.md`+`TASKS.md`+`README.md`+7 plików `docs/rag/*.md`, jednozdaniowy opis każdego. `README.md` "Mapa dokumentacji" rozszerzona o brakujące 06/07/`TASKS.md` i zlinkowana do `docs/INDEX.md` jako pełne źródło |
| D.3 | Formalizacja roli `IMPLEMENTATION_PLAN.md` jako "Observational Memory" — rozdzielenie na "aktualny stan" vs "archiwum decyzji" | ⏳ | Dopiero gdy plik znacząco urośnie (np. po Fazie 1) |
| D.4 | Odpowiedzieć na otwarte pytania z `docs/rag/07`: czy spotkanie/zespoły (Data Engineering/Quantitative Research/Risk Management) są realne, kto ma finalną decyzyjność przy konflikcie z `CLAUDE.md` | ⬜ | Blokuje D.5 |
| D.5 | Eskalacja rozbieżności terminów action items ze spotkania (15.08/30.08/10.09.2026, `docs/rag/07`) PRZED 15.08.2026, jeśli zobowiązania zespołów są realne | ⬜ | Rekomendacja z `docs/rag/07`; warunkowe od odpowiedzi na D.4 |

---

## Backlog — przegląd całego projektu 2026-09-21 (po serii C2.5–C2.8)

> Wynik pełnego audytu kodu, metodologii, dokumentacji i infrastruktury (2026-09-21, po pięciu
> rundach C2.5–C2.8 w paśmie "brak silnego sygnału"). Zadania pogrupowane wg wartości;
> rekomendowana kolejność: **Z1 → Z5 → Z10** (Z6 tuż za nimi). Statusy aktualizowane w miarę
> realizacji; szczegóły każdej rundy realizacyjnej trafiają jak zwykle do sekcji Commitów +
> `runs/`.
>
> **Stan po Commicie 2.10 (2026-09-21):** Z1–Z5 i Z11–Z15 zamknięte. **Z5 zrealizowane na
> Twojej maszynie** (3 lata, 315 648 świec, zero dziur): NO-GO z twardszymi pooled t-statami
> (range -10,47, trend -5,51), ale odsetek ważnych foldów NIE wzrósł (14,6%) — problem jest
> strukturalny: `trend`=0,53% świec, bramka kosztowa blokuje 98% sygnałów `range`. Otwarte:
> **Z6** (koszty — przy 98% blokady bramka jest werdyktem o kosztach), **Z7** (reguła reżimu —
> adresuje pusty `trend`), **Z8/Z9** (Z9 teraz wykonalne z tej maszyny) oraz **Z10** (decyzja
> strategiczna — przy Tobie; `runs/2026-09-21_c2.10-extended-history-z5.md`, sekcja Rekomendacja).

### A. Wiarygodność pomiaru

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z1 | **Naprawić sweep stabilności — obecnie mierzy NIC** | ✅ C2.9 | `DEFAULT_XGB_PARAMS` bez `subsample`/`colsample_bytree` ⇒ XGBoost w pełni deterministyczny ⇒ seed niczego nie zmienia. Stąd std=0,0000 w KAŻDYM eksperymencie od Commitu 6 (identyczne do ostatniej cyfry). Zastąpić perturbacją, która coś robi: jitter przesunięcia startu okien walk-forward (offset 0–9 dni) — perturbuje PODZIAŁ danych, nie model, więc baseline pozostaje porównywalny |
| Z2 | Per-fold t-stat + pooled Sharpe per regime (diagnostyka obok, nie zamiast klasyfikacji) | ✅ C2.9 | Annualizacja sqrt(~800/rok) przy n=31–37 transakcji daje Sharpe -22/-65 — statystycznie bez sensu. Dodać t-stat i zbiorczy (pooled po foldach) Sharpe per regime; rozważyć Deflated Sharpe Ratio |
| Z3 | Wpiąć `effective_sample_size` (labeling.py, C4.4) do raportu checkpointu | ✅ C2.9 | Funkcja istnieje, jest przetestowana i NIGDZIE nieużywana — caveat "N_eff ≪ N" z docs/rag/03 jest dziś czysto teoretyczny |
| Z4 | Licznik multiple-testing w `runs/INDEX.md` | ✅ C2.9 | Kolumna "ile wariantów przetestowano w tej rundzie" — jawna księga budżetu statystycznego (C2.5: 4, C2.6: 2, C2.7: screening, C2.8: 1) |

### B. Realne dźwignie na wynik hipotezy

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z5 | **Wydłużyć historię danych do 3–5 lat** | ✅ C2.10 | Zrealizowane na maszynie użytkownika (2026-09-21): decyzja użytkownika **3 lata** (2023-07-01 → 2026-07-01), `data.start` w config, `py -m data.fetch_ohlcv` → `data/raw/BTC-USDT-USDT_5m_20230701T000000Z_20260701T000000Z.parquet`, **315 648 świec = 1096×288, zero dziur**, overlap 2025-07→2026-07 identyczny co do bajtu ze starym plikiem (który ZOSTAJE jako zamrożone źródło C6–C2.9). Pętla fetch dostała retry/backoff na `ccxt.NetworkError` (+4 testy). Wynik checkpointu v2 na nowej bazie: sekcja Commit 2.10 + `runs/2026-09-21_c2.10-extended-history-z5.md` |
| Z6 | Zweryfikować założenia kosztowe (kandydat (c) z §7 IMPLEMENTATION_PLAN.md) | ✅ C2.12 | Koszty są OSIĄ werdyktu od Commitu 2d, a `taker=0.05%`/`slippage=2bps`/`funding=0.01%/8h` to wartości startowe. Realny tier fee, udział maker (0.02%), realne dane funding |
| Z7 | Reguła regime na `adx_14` zamiast/obok dyskretnej `direction_persistence_10` | ⏳ | Osobny, z góry zarejestrowany eksperyment NA REGULE (nie modelu). Motywacja z trzech niezależnych rund: dyskretność persistence (C2.5), corr adx↔persistence=+0,07 (C2.7), błędna klasyfikacja trendu spadkowego jako `range` (C2c) |
| Z8 | Rozdzielić timeframe od horyzontu trzymania | ⏳ | Nierozdzielony confound C2.6: `VERTICAL_BARRIER_CANDLES=12` = 1h @ 5m, ale 48h @ 4h. Przeliczyć proporcjonalnie jako jawnie nazwany eksperyment |
| Z9 | Walidacja natywnych świec 1h/4h vs resample z 5m | ⏳ | Wymaga maszyny użytkownika (dostęp do Binance); sprawdza, czy agregacja z 5m nie zniekształca wyniku C2.6 |
| Z10 | **DECYZJA STRATEGICZNA: rewizja hipotezy czy domknięcie Fazy 0** | ⬜ | Po pięciu wynikach w paśmie szumu — decyzja UŻYTKOWNIKA, nie zadanie implementacyjne. Opcje: inna definicja reżimu / inny driver (funding rate) / inny instrument — albo udokumentowany wynik negatywny jako poprawne zamknięcie Fazy 0 |

### C. Poprawność jednostek / drobne bugi

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z11 | Przewlec `candle_minutes` przez `run_backtest` → koszty | ✅ C2.9 | `costs.CANDLE_MINUTES=5` zahardkodowane — funding przy 1h/4h liczony jak dla 5m (12×/48× zaniżony; materialnie mały, ~0,0004%, ale ten sam typ buga jednostek co naprawiony `candles_per_day`) |
| Z12 | Lint: nieużywany `import numpy` w engine.py, 3× E741 (`l`) w test_engine.py | ✅ C2.9 | Istniały przed C2.5–C2.8; opcjonalnie ruff/black w CI |

### D. Higiena kodu i procesu

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z13 | Wspólna biblioteka checkpointu (`backtest/checkpoint_lib.py`) — FORWARD-LOOKING | ✅ C2.9 | `_load_config`/`_fetch_data`/`_run_and_summarize`/sweep/stabilność skopiowane 4× (run_checkpoint, calibrate, timeframe, evaluate). UWAGA: historycznych skryptów NIE refaktorować wstecz — są zamrożonymi zapisami eksperymentów, odtwarzalnymi komendą z `runs/` ("Metadane"); biblioteka obowiązuje od nowych skryptów |
| Z14 | Odświeżyć README.md | ✅ C2.9 | Status "Commit 6, 86/86 testów" nieaktualny (128/128, seria C2.5–C2.8), struktura bez `runs/` |
| Z15 | Test spójności registry↔kod jako pytest czytający YAML | ✅ C2.9 | `test_feature_functions_covers_all_ten` hardkoduje listę zamiast czytać `feature_registry.yaml`; check inline w tests.yml zostaje jako belt-and-suspenders |
