# CLAS-5 — Compliance-Led Agentic Trading System

Regime-gated system tradingowy dla BTC/ETH/SOL/BNB perpetual futures, budowany wokół jednej
zasady: **żadna architektura nie powstaje, dopóki nie ma dowodu na edge statystyczny.**

## Dlaczego ten projekt wygląda inaczej niż typowy "bot tradingowy"

Pierwotna koncepcja zakładała pełną, wieloagentową architekturę (5 agentów AI, dashboard, Docker,
Compliance Gate) budowaną od razu, w całości. Zmieniliśmy kolejność: nic z tamtej wizji nie
powstaje, dopóki minimalny, w pełni audytowalny system nie udowodni empirycznie, że hipoteza
tradingowa ma przewagę statystyczną po kosztach transakcyjnych. Architektura bez potwierdzonego
edge'u to tylko dopracowany system do tracenia pieniędzy.

Pełne uzasadnienie tej decyzji i wszystkich pozostałych: [`docs/rag/01_hipoteza_i_architektura.md`](docs/rag/01_hipoteza_i_architektura.md).

## Status

**Faza 0, checkpoint go/no-go (Commit 6) zakończony wynikiem NO-GO** na realnych danych
BTC/USDT:USDT (2025-07-01 → 2026-06-30), potwierdzonym serią pięciu niezależnych,
metodologicznie czystych testów pojedynczych zmian (Commity 2c–2.8: naprawa kill-switcha,
bramka kosztowa, kalibracja progów regime, odporność na timeframe 1h/4h, screening korelacji
cech, formalny test OOS `adx_14`) — wszystkie w paśmie "brak silnego sygnału". Commit 2.9
naprawił metodologię pomiaru (fold-jitter zamiast pustego sweepu seedów, t-stat/N_eff/pooled
Sharpe) i potwierdził NO-GO jako odporne na wyrównanie foldów (100% offsetów ujemne). Commit
2.10 (Backlog Z5) wydłużył historię danych do 3 lat (2023-07-01 → 2026-06-30, 315 648 świec 5m,
bez dziur) i ustanowił na niej NOWĄ bazę checkpointu — wyniki C6–C2.9 pozostają zamrożone na
starym oknie. Stan testów: 143/143. Surowe wyniki każdej rundy: katalog [`runs/`](runs/INDEX.md).
Otwarta decyzja strategiczna i backlog poprawek: `TASKS.md` (sekcja Backlog, Z1–Z15).

Pełny, aktualny status: [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).

## Hipoteza w skrócie

Regime-gated: deterministyczna reguła (nie model) rozdziela dane na reżim "trend" i "range".

- **Test 1 — Momentum:** w reżimie trend, cena kontynuuje ruch.
- **Test 2 — Mean-reversion:** w reżimie range, cena wraca do średniej po przegrzaniu.

Dwa osobne, niezależnie trenowane modele XGBoost — nie jeden połączony model. Walidacja najpierw
wyłącznie na BTC; ETH/SOL/BNB to test generalizacji tej samej hipotezy, nie równoległa walidacja
czterech strategii naraz.

## Struktura projektu

```
clas5_core/
├── README.md                     ← ten plik
├── CLAUDE.md                     — instrukcje dla Claude Code (czytane automatycznie)
├── IMPLEMENTATION_PLAN.md        — status commitów, żywy dokument
├── TASKS.md                      — zadania per commit + Backlog (Z1–Z15)
├── .github/workflows/tests.yml   — CI: pytest + spójność registry/kod
├── docs/rag/                     — pełne uzasadnienia decyzji (01–07), per temat
├── docs/INDEX.md                 — mapa całej dokumentacji
├── config/settings.yaml          — instrumenty, timeframe, progi regime
├── data/fetch_ohlcv.py           — pobieranie/cache OHLCV + resample (Binance USDS-M Futures)
├── agents/
│   ├── feature_miner.py          — 10 cech + regime classifier
│   ├── feature_registry.yaml     — manifest cech (wzór, źródło, rola)
│   ├── labeling.py               — triple-barrier target + walk-forward split
│   ├── ml_optimizer.py           — dwa modele XGBoost (momentum / reversion)
│   └── risk_controller.py        — sizing, kill-switch, bramka kosztowa
├── agent_5_compliance/           — formalne testy leakage
├── backtest/                     — silnik backtestu, koszty, metryki, checkpoint v2,
│                                    skrypty analityczne (zamrożone zapisy eksperymentów)
├── runs/                         — surowy output ciężkich przebiegów (INDEX.md = spis treści)
├── tests/                        — testy jednostkowe/integracyjne/property-based (139)
└── requirements.txt
```

## Szybki start

```bash
git clone <adres-repo>
cd clas5_core
pip install -r requirements.txt --break-system-packages   # lub w wirtualnym środowisku

pytest -v          # powinno dać 6 passed (stan na Commit 2)
```

Przed pierwszym pobraniem prawdziwych danych: zweryfikuj dokładny symbol ccxt na swojej maszynie
— `config/settings.yaml` zakłada `"BTC/USDT:USDT"` na Binance USDS-M Futures, ale nie było to
możliwe do zweryfikowania w środowisku, w którym ten kod powstał (brak dostępu do API giełdy).

```python
import ccxt
ex = ccxt.binanceusdm()
ex.load_markets()
print([s for s in ex.symbols if "BTC/USDT" in s])
```

## Mapa dokumentacji

Pełna, zawsze aktualna mapa wszystkich dokumentów: [`docs/INDEX.md`](docs/INDEX.md). Skrót poniżej:

| Plik | Dla kogo / po co |
|---|---|
| `README.md` | Ty jesteś tutaj — ogólny obraz |
| `CLAUDE.md` | Claude Code — krótkie, stabilne zasady, czytane na starcie każdej sesji |
| `IMPLEMENTATION_PLAN.md` | Aktualny status commitów, znane ryzyka, checklisty — zmienia się często |
| `TASKS.md` | Granularny, statusowalny rozkład planu na pojedyncze zadania z ID i statusem |
| `docs/rag/01_hipoteza_i_architektura.md` | Dlaczego regime-gated, dlaczego LLM offline, dlaczego nie deep learning |
| `docs/rag/02_cechy_i_leakage.md` | Definicje cech, metodologia testowania leakage, multi-repo extraction |
| `docs/rag/03_ryzyko_i_sizing.md` | Triple-barrier labeling, sizing, walk-forward, checkpoint go/no-go |
| `docs/rag/04_narzedzia_zewnetrzne.md` | Decyzje o freqtrade/LEAN/QuantConnect i frameworkach multi-agent LLM |
| `docs/rag/05_metodologia_wytwarzania_i_testow.md` | Piramida testów, Definition of Done, CI/CD |
| `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` | Projekt komponentów LLM offline/nadzorczo (Faza 2+) i `docs/rag/` jako baza wiedzy |
| `docs/rag/07_notatki_spotkania_i_szersza_wizja_systemu.md` | Rozbieżności między notatkami ze spotkania a dyscypliną Fazy 0 — otwarte pytania |

## Kluczowe zasady projektowe

Pełna, aktualna lista: [`CLAUDE.md`](CLAUDE.md). W skrócie:

1. Parametry kalibrowane tylko wewnątrz walk-forward, nigdy na całym zbiorze naraz.
2. Każda cecha ma test leakage przed wejściem do modelu.
3. Target (triple-barrier) i risk_controller używają tego samego mnożnika ATR (1.5×).
4. Feature set rozszerzany jedną cechą na raz, mierzoną na out-of-sample.
5. Leverage cap zawsze wygrywa nad fixed-fractional sizing.
6. LLM nigdy w hot-pathie decyzyjnym — offline/nadzorczo tylko.
7. Regime gate i sizing zostają regułami, dopóki minimalny system nie udowodni edge'u.
8. Zewnętrzne frameworki (freqtrade, LEAN) to katalog wzorców, nigdy zależność runtime w Fazie 0.

## Zastrzeżenie

Ten kod służy do celów badawczych i edukacyjnych. Nie stanowi porady inwestycyjnej. Trading
kontraktów perpetual futures z dźwignią wiąże się z wysokim ryzykiem utraty kapitału. Żadna
część tego repozytorium nie została zwalidowana na prawdziwym kapitale — checkpoint go/no-go
(`IMPLEMENTATION_PLAN.md`, Commit 6) jeszcze nie został osiągnięty. Nie uruchamiaj tego z
prawdziwymi środkami przed przejściem pełnej sekwencji: walidacja → paper trading → mały kapitał
w pełni tolerowalny do stracenia.

## Licencja

Do ustalenia przed publikacją repo.
