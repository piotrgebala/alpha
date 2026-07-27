# TASKS.md — Zadania implementacyjne CLAS-5 (status i podział na komponenty)

> Ten plik to granularny, statusowalny rozkład `IMPLEMENTATION_PLAN.md` (§4, §5, §9, §10, §12) i
> `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` na pojedyncze zadania. `IMPLEMENTATION_PLAN.md`
> zostaje dokumentem nadrzędnym (rationale, decyzje, Definition of Done) — ten plik służy tylko do
> śledzenia postępu na poziomie zadania. Aktualizuj status tutaj na bieżąco; nagłówek/status
> commitu w `IMPLEMENTATION_PLAN.md` aktualizuj przy zamknięciu całego commitu.
>
> Ostatnia aktualizacja: 2026-07-27.

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
| Commit 1 — Dane | 2 | 1 | 0 | 3 |
| Commit 2 — Feature registry | 4 | 0 | 1 | 5 |
| Commit 3 — Test leakage (NASTĘPNY KROK) | 0 | 3 | 0 | 3 |
| Commit 4 — Target + walk-forward split | 0 | 0 | 5 | 5 |
| Commit 5 — Dwa modele + backtest | 0 | 0 | 6 | 6 |
| Commit 5.5 — Risk controller | 0 | 0 | 5 | 5 |
| Commit 6 — Checkpoint go/no-go | 0 | 0 | 5 | 5 |
| Faza 1 — regime router, funding rate, Compliance Gate | 0 | 0 | 8 | 8 |
| Faza 2 — LLM offline Q&A + test_mathematics.py | 0 | 0 | 4 | 4 |
| Faza 3 — paper trading + post_trade_critic.py | 0 | 0 | 4 | 4 |
| Faza 4 — mały kapitał, skalowanie | 0 | 0 | 2 | 2 |
| Dokumentacja/workflow (niezależne od fazowania) | 0 | 4 | 1 | 5 |
| **RAZEM** | **6** | **8** | **41** | **55** |

---

## Faza 0 — dowód edge'u (aktywna faza)

### Commit 1 — Dane (`data/fetch_ohlcv.py`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C1.1 | Pobieranie OHLCV z Binance USDS-M Futures (perpetuals) przez ccxt, paginacja + cache parquet | ✅ | |
| C1.2 | `find_gaps()` — raportowanie dziur w danych bez blokowania pipeline'u | ✅ | |
| C1.3 | Weryfikacja dokładnego symbolu ccxt (`"BTC/USDT:USDT"`) przez `exchange.load_markets()` na żywym API | ⚠️ | Niepotwierdzone na żywo — zrobić PRZED pierwszym uruchomieniem na realnych danych |

### Commit 2 — Feature registry (`agents/feature_miner.py`, `agents/feature_registry.yaml`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.1 | 9 funkcji cech (`atr_14`, `atr_pctrank_20d`, `direction_persistence_10`, `return_lag_1`, `momentum_5`, `ema_diff_9_21`, `volume_zscore_20`, `rsi_14`, `price_zscore_20`) | ✅ | |
| C2.2 | `classify_regime()` | ✅ | |
| C2.3 | `split_by_regime()` | ✅ | |
| C2.4 | Nieformalny leakage sanity check (9/9 na danych syntetycznych) | ✅ | Nie zastępuje formalnego testu z Commitu 3 |
| C2.5 | Kalibracja progów regime rule (0.7/0.3) na realnych danych | ⏳ | Ryzyko z §7: reżim "trend" może być rzadki — sprawdzić po pobraniu prawdziwych danych. CLAUDE.md zasada 1: kalibracja WYŁĄCZNIE wewnątrz walk-forward (Commit 4), nigdy na całym zbiorze naraz |

### Commit 3 — Test leakage (`agent_5_compliance/test_leakage.py`) — NASTĘPNY KROK

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C3.1 | Formalny, parametryzowany pytest leakage dla wszystkich 9 funkcji cech (`df[:T]` vs `df[:T+k]`) | ⬜ | |
| C3.2 | Priorytet: `atr_pctrank_20d` — trailing, nie centered window | ⬜ | Największe ryzyko leakage |
| C3.3 | Integracja z CI (`.github/workflows/tests.yml`) | ⬜ | |

### Commit 4 — Target + walk-forward split (`agents/labeling.py`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C4.1 | Triple-barrier ATR-scaled (upper/lower = ±1.5×ATR, vertical = 12 świec/1h) | ⏳ | |
| C4.2 | Spójność mnożnika 1.5×ATR z przyszłym `risk_controller` (Commit 5.5) | ⏳ | CLAUDE.md zasada 3 — twarda zależność, nie zmieniać jednej strony bez drugiej |
| C4.3 | Walk-forward split (2 mies. train / 2 tyg. test, krok 2 tyg., chronologiczny) | ⏳ | |
| C4.4 | Diagnostyka efektywnej liczby próbek (autokorelacja `return_lag_1`, N_eff) | ⏳ | Informacyjne, nie blokuje |
| C4.5 | Test leakage dla `labeling.py` PRZED wejściem do modelu | ⏳ | CLAUDE.md zasada 2 |

### Commit 5 — Dwa modele, osobno (`agents/ml_optimizer.py`, `backtest/`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C5.1 | `model_momentum` + `model_reversion` — dwa niezależne XGBoosty | ⏳ | Żadnego wspólnego modelu na tym etapie |
| C5.2 | Hiperparametry startowe + `early_stopping_rounds=20` na foldzie OOS | ⏳ | |
| C5.3 | `predict_proba` (nie tylko klasa) jako `signal_confidence` | ⏳ | |
| C5.4 | `backtest/costs.py` — taker fee, funding rate, slippage | ⏳ | |
| C5.5 | `backtest/engine.py` — pętla sygnał → risk_controller → PnL z kosztami → equity curve | ⏳ | |
| C5.6 | Trade journal — logowanie transakcji w ustrukturyzowanym formacie już przy pierwszej implementacji | ⏳ | Heads-up z `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` — potrzebne dla Fazy 2/3, nie zmienia zakresu Commitu 5 |

### Commit 5.5 — Risk controller (`agents/risk_controller.py`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C5.5.1 | Kontrakt wejścia/wyjścia (`signal_direction`/`signal_confidence`/`regime`/`atr_14`/`entry_price` → `position_size`/`stop_price`/`take_profit_price`) | ⏳ | |
| C5.5.2 | Sizing: `size_risk`, `size_leverage`, `position_size = min(size_risk, size_leverage)` | ⏳ | Leverage cap zawsze wygrywa — CLAUDE.md zasada 5 |
| C5.5.3 | Parametry startowe: `risk_per_trade=0.5%`, `max_leverage=3x` | ⏳ | |
| C5.5.4 | `signal_confidence` skaluje `risk_per_trade` liniowo | ⏳ | |
| C5.5.5 | Kill-switch (drawdown > X% od peaku → stop nowych sygnałów) | ⏳ | |

### Commit 6 — Checkpoint go/no-go

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C6.1 | Policzyć Sharpe po kosztach per fold | ⏳ | |
| C6.2 | Klasyfikacja wyniku: GO / WARUNKOWY / NO-GO wg kryteriów z §5 | ⏳ | |
| C6.3 | Stabilność wyniku przy losowym seedzie modelu (overfitting sanity check) | ⏳ | |
| C6.4 | Wynik osobno per reżim rynkowy (2023 niska zmienność vs 2024-25 era ETF) | ⏳ | |
| C6.5 | Decyzja udokumentowana w `IMPLEMENTATION_PLAN.md` | ⏳ | |

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
| D.1 | YAML frontmatter (`status`, `last_verified`, `depends_on`) w każdym `docs/rag/*.md` | ⬜ | |
| D.2 | Plik-indeks (Mapa Treści) linkujący `CLAUDE.md` + `IMPLEMENTATION_PLAN.md` + `docs/rag/*.md` | ⬜ | |
| D.3 | Formalizacja roli `IMPLEMENTATION_PLAN.md` jako "Observational Memory" — rozdzielenie na "aktualny stan" vs "archiwum decyzji" | ⏳ | Dopiero gdy plik znacząco urośnie (np. po Fazie 1) |
| D.4 | Odpowiedzieć na otwarte pytania z `docs/rag/07`: czy spotkanie/zespoły (Data Engineering/Quantitative Research/Risk Management) są realne, kto ma finalną decyzyjność przy konflikcie z `CLAUDE.md` | ⬜ | Blokuje D.5 |
| D.5 | Eskalacja rozbieżności terminów action items ze spotkania (15.08/30.08/10.09.2026, `docs/rag/07`) PRZED 15.08.2026, jeśli zobowiązania zespołów są realne | ⬜ | Rekomendacja z `docs/rag/07`; warunkowe od odpowiedzi na D.4 |
