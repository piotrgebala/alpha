# CLAS-5 — Plan Implementacji (Faza 0)

> Dokument roboczy do pracy w VS Code. Konsoliduje wszystkie decyzje z sesji planistycznej.
> Jeśli zaczynasz nową sesję Claude Code, podepnij ten plik jako kontekst — zastępuje potrzebę
> przewijania całej wcześniejszej rozmowy.
>
> Ostatnia aktualizacja: 2026-07-05. **Status: Commit 1 i Commit 2 zaimplementowane i przetestowane.**

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
│   ├── labeling.py                  TODO — Commit 4
│   ├── ml_optimizer.py              TODO — Commit 5
│   └── risk_controller.py           TODO — Commit 5.5
├── agent_5_compliance/
│   └── test_leakage.py              TODO — Commit 3 (następny krok)
├── backtest/
│   ├── engine.py                    TODO — Commit 5
│   └── costs.py                     TODO — Commit 5
└── tests/
    ├── __init__.py                  [DONE]
    └── test_fetch_ohlcv.py          [DONE, 6/6 testów przechodzi]
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

### Commit 3 — Test leakage `[NASTĘPNY KROK]`

`agent_5_compliance/test_leakage.py` — formalny, parametryzowany pytest dla wszystkich 9 funkcji.

- Metoda: policz cechę na `df[:T]` i `df[:T+k]`, sprawdź identyczność do T.
- **Priorytet:** `atr_pctrank_20d` — największe ryzyko (rolling window musi być trailing, nie
  centered).
- Nieformalna wersja tego testu już przeszła 9/9 na syntetycznych danych — to nie zastępuje
  formalnego pytest w CI.

### Commit 4 — Target + walk-forward split

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

### Commit 5 — Dwa modele, osobno

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

### Commit 5.5 — Risk controller + interfejs

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

### Commit 6 — Checkpoint go/no-go: TRZY ścieżki

| Wynik | Kryterium (startowe) | Decyzja |
|---|---|---|
| **GO** | Sharpe po kosztach > 0.5 w >60% foldów, zgodny znak | Faza 1: regime router + funding rate do Test 2 |
| **WARUNKOWY** | Sharpe 0–0.5 lub niestabilny znak między foldami | Max 3 iteracje protokołu "jedna cecha na raz", potem decyzja ponownie |
| **NO-GO** | Sharpe ≤ 0 w większości foldów | Wróć do Commit 2 — inna hipoteza/cechy, NIE tuning tego zestawu |

Sprawdzić też: stabilność wyniku przy losowym seedzie modelu (overfitting sanity check), wynik
osobno per reżim rynkowy (2023 niska zmienność vs 2024-25 era ETF).

---

## 6. Zweryfikowane empirycznie (nie tylko zaplanowane)

- TA-Lib (0.7.0) instaluje się i liczy ATR/RSI/EMA poprawnie (zweryfikowane na random walk).
- `pandas.Series.rolling().rank(pct=True)` daje poprawną, trailing (bez leakage) percentylową
  rangę ostatniej wartości okna — zweryfikowane ręcznym przeliczeniem. Szybkie: 0.097s na 105k
  wierszy przy oknie 5760.
- `compute_all_features()` na pełnym 12-miesięcznym syntetycznym zbiorze (105k wierszy): **0.23s**.
- Nieformalny leakage sanity check: 9/9 cech identyczne na `df[:T]` vs `df[:T+50]`.
- `tests/test_fetch_ohlcv.py`: 6/6 testów przechodzi (dedup, sortowanie, gap detection).

---

## 7. Znane ryzyka i otwarte pytania

- **Regime "trend" może być rzadki.** Na syntetycznych danych z progami 0.7/0.3, trend = <1%
  świec (ambiguous ~80%, range ~20%). To strukturalna właściwość AND-owania dwóch warunków, nie
  tylko artefakt syntetycznych danych. **Sprawdzić jako pierwsze po pobraniu prawdziwych danych**
  — jeśli się powtórzy, Test 1 może mieć za mało próbek na wiarygodny wynik; rozważ złagodzenie
  `trend_threshold`.
- **Symbol ccxt niezweryfikowany na żywo** — `"BTC/USDT:USDT"` to założenie, nie potwierdzony fakt.
- **Survivorship bias w pożyczonych wskaźnikach** — RSI/ATR/EMA przetrwały w publicznym obiegu
  (freqtrade i podobne) częściowo dlatego, że ktoś na nich pokazał dobry backtest. Stała czujność,
  nie coś do jednorazowego zamknięcia.
- **Koszt obliczeniowy pełnego tuningu** (walk-forward × hiperparametry × okna wskaźników)
  nieoszacowany — zmierzyć na małej próbce przed pełnym przeszukiwaniem, nawet na Ryzen 7950X3D.

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
