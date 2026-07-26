# CLAS-5 — Instrukcje projektowe (Claude Code)

## Projekt
System tradingowy BTC/ETH perpetual futures. Regime-gated: deterministyczna reguła (nie model)
rozdziela dane na reżim "trend" (momentum) i "range" (mean-reversion) — dwa osobne, niezależnie
trenowane modele XGBoost, nie jeden połączony.

**Cel Fazy 0:** udowodnić edge statystyczny minimalnym, audytowalnym systemem, zanim dobuduje się
cokolwiek z oryginalnego PRD (5 agentów, dashboard, Docker). Status commitów, checkpointy,
otwarte ryzyka → `IMPLEMENTATION_PLAN.md` (zmienia się często, traktuj jako aktualny stan, nie
jako źródło stałych zasad).

## Nienaruszalne zasady

1. **Nigdy nie optymalizuj parametrów** (okna wskaźników, progi regime, hiperparametry) na całym
   zbiorze danych naraz — tylko wewnątrz walk-forward. Uzasadnienie: `docs/rag/03_ryzyko_i_sizing.md`.
2. **Każda nowa cecha dostaje test leakage PRZED wejściem do modelu**, nie po.
   Metodologia: `docs/rag/02_cechy_i_leakage.md`.
3. **Target (triple-barrier) i risk_controller (stop-loss) używają TEGO SAMEGO mnożnika ATR
   (1.5×).** Rozjazd między nimi = trenujesz na czymś innym niż handlujesz.
4. **Rozszerzanie feature setu: jedna cecha na raz, mierzona na out-of-sample.** Nigdy grid search
   po wielu kombinacjach naraz. Powód: `docs/rag/02_cechy_i_leakage.md` (multiple testing).
5. **Leverage cap zawsze wygrywa nad fixed-fractional sizing** — jawna reguła `min()`, nie coś do
   odkrycia w runtime.
6. **LLM nigdy w hot-pathie decyzyjnym.** Offline/nadzorczo tylko (recenzja modeli, raporty
   post-trade). Powód: `docs/rag/01_hipoteza_i_architektura.md`.
7. **Regime gate i sizing zostają regułami (nie ML), dopóki minimalny system nie udowodni
   edge'u.** Zamiana na HMM/RL to eksperyment PO ustaleniu baseline'u.
8. **freqtrade / LEAN / QuantConnect = katalog wzorców, nigdy zależność runtime w Fazie 0.**
   Szczegóły per narzędzie: `docs/rag/04_narzedzia_zewnetrzne.md`.
9. **Multi-instrument (BTC/ETH/SOL/BNB): waliduj BTC samodzielnie do końca Commitu 6 PRZED
   testowaniem pozostałych.** Rozszerzanie na inne instrumenty to test generalizacji tej samej
   hipotezy (te same progi, bez retuningu), nie równoległa walidacja czterech niezależnych
   strategii naraz. Uzasadnienie: `docs/rag/01_hipoteza_i_architektura.md`.
10. **Commit nie jest "zrobiony" bez testów jednostkowych + (jeśli dotyczy) testu leakage +
    (jeśli dotyczy) property-based testu w `hypothesis`.** Pełna checklista Definition of Done:
    `docs/rag/05_metodologia_wytwarzania_i_testow.md`.

## Struktura projektu

```
data/, agents/, agent_5_compliance/, backtest/, tests/   — kod produkcyjny
docs/rag/                                                 — PEŁNE uzasadnienia decyzji (czytaj
                                                             przed zmianą architektury, nie tylko
                                                             kodu)
IMPLEMENTATION_PLAN.md                                    — status commitów, żywy dokument
config/settings.yaml, agents/feature_registry.yaml        — źródło prawdy dla parametrów
```

## Zanim zmienisz coś w `risk_controller.py`, `labeling.py` lub `feature_miner.py`

Przeczytaj odpowiedni plik w `docs/rag/` — te decyzje mają konkretne, przetestowane uzasadnienie
(nie są arbitralne), i zmiana jednej wartości bez sprawdzenia drugiej strony (np. mnożnika ATR)
łamie spójność, którą specjalnie budowaliśmy.
