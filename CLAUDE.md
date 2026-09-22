# CLAS-5 — Instrukcje projektowe (Claude Code)

## Projekt
System tradingowy BTC/ETH/SOL/BNB perpetual futures. Regime-gated: deterministyczna reguła (nie
model) rozdziela dane na reżim "trend" (momentum) i "range" (mean-reversion) — dwa osobne,
niezależnie trenowane modele XGBoost, nie jeden połączony.

**Cel Fazy 0:** udowodnić edge statystyczny minimalnym, audytowalnym systemem, zanim dobuduje się
cokolwiek z oryginalnego PRD (5 agentów, dashboard, Docker). Status commitów, checkpointy,
otwarte ryzyka → `IMPLEMENTATION_PLAN.md`; zadania i backlog (Z1–Z15) → `TASKS.md`; surowe
wyniki rund → `runs/INDEX.md`. Te pliki zmieniają się często — traktuj jako aktualny stan, nie
jako źródło stałych zasad.

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
11. **Każdy ciężki przebieg na realnych danych** (checkpoint, kalibracja, sweep, screening)
    **kończy się plikiem `runs/YYYY-MM-DD_<slug>.md`** (ID testu, metadane, sekcja "Co na plus
    (+) / Co na minus (-)", pełny surowy output) **+ wierszem w `runs/INDEX.md` z licznikiem
    wariantów** (jawna księga budżetu multiple-testing). Pełna konwencja: `TASKS.md`, sekcja
    "Zasada pracy: `runs/*.md`".
12. **Wyniki raportuje się metodologią checkpointu v2** (`backtest/run_checkpoint_v2.py` /
    `backtest/checkpoint_lib.py`: sweep fold-jitter, per-fold t-stat, pooled per regime, N_eff).
    **Nigdy nie cytuj "stabilności na 10 seedach"** — XGBoost w konfiguracji Fazy 0 jest
    deterministyczny, więc ten sweep nie mierzy niczego (`docs/rag/03`, aktualizacja 2026-09-21).
13. **Historyczne skrypty analityczne są ZAMROŻONE** — to odtwarzalne zapisy zakończonych
    eksperymentów (komenda w sekcji "Metadane" ich plików `runs/`), nie kod do refaktoryzacji
    wstecz. Nowe skrypty budują na `backtest/checkpoint_lib.py`.

## Wytyczne (miękkie — do rewizji, gdy zmienią się dane)

- **Zmierzony szum wyrównania foldów na rocznych danych 5m: σ≈3,1 mean_sharpe** (C2.9). Różnicy
  między wariantami Δ<~3 nie traktuj jako rozstrzygniętej — odnotuj i wróć do niej po wydłużeniu
  historii danych (Backlog Z5). Zmierz σ ponownie po każdej istotnej zmianie datasetu.
- Lint/format: `ruff` + `black` na plikach dotykanych w rundzie; plików zamrożonych (zasada 13)
  nie reformatuj. Różnice CRLF/LF między repo (Windows) a środowiskiem pracy są normalne.

## Podział ról i autonomia (uzgodnione 2026-09-22)

**Użytkownik:** operacje git (commit/merge/push — Claude zapisuje pliki do katalogu repo, ale nie
ma shella na maszynie), pobieranie danych z Binance (sandbox nie ma dostępu sieciowego do
giełdy), decyzje bramkowe faz (przejście do Fazy 1, zamknięcie Fazy 0, jakikolwiek realny
kapitał) i wszystko nieodwracalne (usuwanie danych/historii).

**Claude — pełna autonomia badawcza W RAMACH zasad 1–13:** samodzielnie wybiera i uruchamia
kolejne eksperymenty (w tym z backlogu w `TASKS.md`), może wprowadzać wynikające z wyników
zmiany parametrów/cech/configu — **raportując po fakcie, w tej samej rundzie** (plik `runs/` +
`IMPLEMENTATION_PLAN.md` §5/§7 + `TASKS.md`). Autonomia nie uchyla dyscypliny: jedna zmiana na
raz, warianty rejestrowane z góry (przed obejrzeniem wyniku), licznik multiple-testing
aktualizowany, każda decyzja udokumentowana z uzasadnieniem i ścieżką odwrotu (co i jak
zrevertować). Skrypty pozostają neutralnymi reporterami — decyzję podejmuje i podpisuje w
dokumentacji Claude, nigdy "automat w skrypcie".

## Struktura projektu

```
data/, agents/, agent_5_compliance/, backtest/, tests/   — kod produkcyjny
backtest/checkpoint_lib.py + run_checkpoint_v2.py        — kanoniczna metodologia pomiaru (zasada 12)
runs/ (+ runs/INDEX.md)                                  — surowe wyniki rund (zasada 11)
docs/rag/ (01–07) + docs/INDEX.md                        — PEŁNE uzasadnienia decyzji (czytaj
                                                            przed zmianą architektury, nie tylko kodu)
IMPLEMENTATION_PLAN.md                                    — status commitów i ryzyka, żywy dokument
TASKS.md                                                  — zadania, backlog Z1–Z15, zasady pracy
                                                            (branch-per-task, runs/, zużycie)
config/settings.yaml, agents/feature_registry.yaml        — źródło prawdy dla parametrów
```

## Zanim zmienisz coś w `risk_controller.py`, `labeling.py`, `feature_miner.py` lub metodologii pomiaru

Przeczytaj odpowiedni plik w `docs/rag/` (dla metodologii pomiaru: `docs/rag/03`, sekcja
checkpointu + aktualizacja 2026-09-21) — te decyzje mają konkretne, przetestowane uzasadnienie
(nie są arbitralne), i zmiana jednej wartości bez sprawdzenia drugiej strony (np. mnożnika ATR)
łamie spójność, którą specjalnie budowaliśmy.
