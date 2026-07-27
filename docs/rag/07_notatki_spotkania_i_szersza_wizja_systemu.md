# 07 — Notatki ze spotkania: szersza wizja systemu vs dyscyplina Fazy 0

## Kontekst i status

Ten dokument to adnotowany zapis konkretnego spotkania (notatki dostarczone 2026-07-27, diagram
Miro — **ten sam board**, który już raz zmapowano węzeł-po-węźle w `IMPLEMENTATION_PLAN.md` §10
"Mapowanie wizji z diagramu (Miro) na fazy planu"). Nie jest to nowa mapa zadań ani zmiana
zakresu Fazy 0 — to zapis rozbieżności między tym, co notatki ze spotkania przedstawiają jako
zatwierdzone decyzje i zadania z terminami, a tym, co faktycznie obowiązuje wg `CLAUDE.md` i
`IMPLEMENTATION_PLAN.md`. Szczegółowe mapowanie poszczególnych elementów diagramu na fazy — patrz
`IMPLEMENTATION_PLAN.md` §10, nie duplikowane tutaj.

**Nieznana geneza:** nie wiadomo, czy to notatki z realnego spotkania z zewnętrznymi
interesariuszami, czy ćwiczenie planistyczne. Analiza poniżej dotyczy treści, nie zakłada
odpowiedzi na to pytanie — patrz "Otwarte pytania".

## Notatki źródłowe (streszczenie)

**Agenda:** przegląd architektury systemu, źródła danych i wskaźniki techniczne, modele ML i
metody ilościowe do generowania sygnału, zarządzanie ryzykiem i optymalizacja portfela,
monitoring wykonania i protokoły retreningu.

**Decyzje podjęte (wg notatek):**
1. Zatwierdzono wielo-źródłowe zbieranie danych: market data, onchain data, volume, Twitter
   sentiment, Forex Factory news.
2. Uzgodniono trzywarstwowy framework analizy: wskaźniki techniczne (RSI, MACD, Bollinger, ATR,
   GMMA), modele ML (XGBoost, CatBoost, LSTM, GRU, RandomForest), metody ilościowe (Monte Carlo,
   Black-Scholes, Brownian Motion).
3. Potwierdzono conviction-based position sizing z VaR, Expected Shortfall, Max Drawdown, MPT
   optimization.

**Action items (wg notatek):**
- Implementacja data pipeline — Data Engineering Team — do 15.08.2026
- Konfiguracja technical analysis + modeli ML — Quantitative Research Team — do 30.08.2026
- Wdrożenie risk management framework — Risk Management Team — do 10.09.2026

## Analiza zgodności z obecnym planem (CLAS-5, Faza 0)

| Element notatek | Zgodność z obecnym planem | Uzasadnienie |
|---|---|---|
| Market data, volume | ✅ Zgodne | Commit 1 (`data/fetch_ohlcv.py`) |
| Onchain data | 🟡 Zgodne jako przyszłość | Kandydat do Test 2 w Fazie 1, nie Faza 0 (§10) |
| Twitter sentiment, Forex Factory news | 🔴 Przedwczesne | Explicite Faza 2+/3 w §10, nie "teraz" |
| RSI, ATR | ✅ Zgodne | Commit 2 (`agents/feature_miner.py`) |
| MACD, Bollinger, GMMA | 🟡 Zgodne warunkowo | Częściowo redundantne z istniejącymi cechami — testować pojedynczo na OOS (§10, F1.5 w `TASKS.md`), nie hurtowo |
| XGBoost | ✅ Zgodne | Dwa niezależne modele, Commit 5 |
| CatBoost, RandomForest | 🟡 Zgodne warunkowo | Tylko jako porównanie/ensemble PO potwierdzeniu edge'u XGBoostem (§10), nie równolegle od startu |
| LSTM, GRU | 🔴 Niezgodne | Świadomie odrzucone — CLAUDE.md zasada 7, §8 pkt 7: dane tabelaryczne + ograniczona efektywna liczba próbek faworyzują drzewa |
| Monte Carlo | 🟡 Niejasne | Nie ma dziś zdefiniowanego zastosowania w Fazie 0 — do doprecyzowania, jeśli ktoś wskaże konkretny cel |
| Black-Scholes | 🔴 Niezgodne | Model wyceny opcji — handlujemy perpetual futures, nie opcjami (§10 "Nie pasuje do obecnego zakresu") |
| Brownian Motion | 🔴 Niezgodne | Proces do symulacji/wyceny instrumentów pochodnych, nie model predykcyjny klasyfikacji kierunku (§10) |
| Conviction-based sizing | ✅ Zgodne | `signal_confidence` skaluje `risk_per_trade`, Commit 5.5 |
| VaR, Max Drawdown | ✅ Zgodne | Kill-switch w `risk_controller.py`, Commit 5.5 |
| Expected Shortfall | 🟡 Zgodne jako przyszłość | Naturalne uzupełnienie VaR, ale nie Faza 0 (§10) |
| Correlation & Covariance, MPT Optimization | 🔴 Niezgodne dziś | Dotyczy alokacji między wieloma instrumentami — nierelewantne przy jednym instrumencie w Fazie 0 (§10) |
| Retraining / Retrain Models? | 🟡 Trafna uwaga, brakująca w planie | Już dodane jako zadanie do Fazy 1 (§10, F1.4 w `TASKS.md`) |
| Action items: terminy 15.08 / 30.08 / 10.09.2026 | 🔴 Niezgodne z rzeczywistym stanem | Zakładają równoległą budowę pełnego systemu, ale checkpoint Commitu 6 (go/no-go) jeszcze się nie wydarzył — wg `TASKS.md` Commit 3 (test leakage) to dopiero następny krok (6/52 zadań zrobionych) |

## Kluczowe rozbieżności

1. **Sekwencja pracy.** Notatki zakładają trzy zespoły pracujące równolegle nad pełnym systemem
   (data, modele, risk) z twardymi terminami. Obecny plan wymaga sekwencyjnego dowodu edge'u
   (Commit 1→6) PRZED jakąkolwiek pracą z Części II PRD — patrz `IMPLEMENTATION_PLAN.md` §1: "nic
   z Części II PRD (5 agentów, dashboard, Docker) nie jest budowane, dopóki Faza 0 nie udowodni
   empirycznie, że istnieje jakikolwiek edge statystyczny po kosztach transakcyjnych".
2. **Wielość modeli/metod naraz.** CLAUDE.md zasada 4: "Rozszerzanie feature setu: jedna cecha na
   raz, mierzona na out-of-sample. Nigdy grid search po wielu kombinacjach naraz." Notatki
   proponują 5 modeli ML i 3 metody ilościowe jednocześnie, bez rozróżnienia kolejności ani
   kryteriów wyboru.
3. **Regime gate i sizing jako reguły, nie ML.** CLAUDE.md zasada 7: zostają regułami, "dopóki
   minimalny system nie udowodni edge'u". Notatki nie wspominają w ogóle regime-gated hipotezy
   (Test 1 momentum / Test 2 mean-reversion), która jest rdzeniem obecnego podejścia — sugeruje
   to, że opisują architekturę sprzed decyzji o Fazie 0, nie po niej.
4. **Brak wzmianki o rygorze empirycznym Fazy 0** — walk-forward, test leakage, go/no-go
   checkpoint, property-based testing. To nie są szczegóły implementacyjne do dodania później —
   to warunek konieczny, żeby cokolwiek z notatek było w ogóle wiarygodne (patrz
   `05_metodologia_wytwarzania_i_testow.md`).

## Ocena i rekomendacja

Notatki ze spotkania w dużej mierze odtwarzają pierwotny, ambitny zakres PRD (Część II) — dokładnie
to, co `CLAUDE.md` i `IMPLEMENTATION_PLAN.md` świadomie odłożyły do czasu udowodnienia edge'u.
Realizacja action items na podanych terminach (15.08, 30.08, 10.09.2026) byłaby wprost sprzeczna z
zasadami 4 i 7 z `CLAUDE.md` oraz z zasadą nadrzędną z §1.

**Rekomendacja:** nie traktować "Decisions Taken" i "Action Items" z notatek jako zatwierdzonego,
równoległego toru pracy. Terminy powinny być warunkowe od wyniku Commitu 6 (GO/WARUNKOWY/NO-GO),
nie ustalone z góry. Jeśli to realne zobowiązanie zespołów (Data Engineering, Quantitative
Research, Risk Management) z rzeczywistymi terminami — rozbieżność z dyscypliną Fazy 0 powinna być
eskalowana i rozstrzygnięta PRZED 15 sierpnia, nie odkrywana po fakcie, gdy zespoły już zaczną
pracę niezgodną z zasadami projektu.

## Otwarte pytania

- Czy to notatki z realnego spotkania z zespołami/interesariuszami, czy wewnętrzne ćwiczenie
  planistyczne? Wpływa na to, czy rozbieżność wymaga pilnej eskalacji, czy jest tylko materiałem
  do przemyślenia.
- Jeśli terminy są realne — kto ma finalną decyzję w razie konfliktu między tym spotkaniem a
  regułami z `CLAUDE.md`?
- Czy Data Engineering Team / Quantitative Research Team / Risk Management Team to istniejące,
  odrębne zespoły, czy jedna osoba/rola opisana w trzech kapeluszach? Wpływa na to, jak dosłownie
  traktować "równoległość" pracy z notatek.

## Źródła

- Notatki ze spotkania i diagram Miro dostarczone w konwersacji 2026-07-27 (ten sam diagram co w
  `IMPLEMENTATION_PLAN.md` §10).
- `CLAUDE.md` — zasady 4 i 7 (jedna cecha na raz; regime/sizing jako reguły do czasu edge'u).
- `IMPLEMENTATION_PLAN.md` §1 (zasada nadrzędna), §8 (zasady pracy), §10 (mapowanie tego samego
  diagramu na fazy).
- `TASKS.md` — rzeczywisty stan postępu (6/52 zadań, Commit 3 jako następny krok).
