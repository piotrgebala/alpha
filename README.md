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

### 🔴 FAZA 0 ZAMKNIĘTA WYNIKIEM NEGATYWNYM (decyzja użytkownika, 2026-09-22 — [Z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md))

Hipoteza, dla której Faza 0 powstała — **regime-gated momentum/mean-reversion na cechach
OHLCV** — nie ma edge'u kierunkowego wystarczającego do pokrycia kosztów transakcyjnych.

To **dowód braku, a nie brak dowodu**:

| | |
|---|---|
| pooled trafność kierunku (3 najczystsze pomiary, n = 7 687) | **50,27%**, CI95 [49,15%; **51,38%**], z = +0,47 |
| najniższy próg opłacalności zmierzony w projekcie | **52,69%** |
| górny kraniec CI vs ten próg | **−1,30 pp — przedział ufności nie sięga progu** |
| moc statystyczna | **2,8×** próby wymaganej do wykrycia p = 52,69% |

Wąskie gardło okazało się **informacyjne, nie inżynieryjne**: projekt naprawił po kolei
geometrię wypłaty, model kosztów, spójność bramki z horyzontem etykiety, jakość danych,
przeciek w treningu i metodologię pomiaru — i po **każdej** z tych napraw trafność pozostawała
przy 50%. Wszystkie 10 cech to transformacje tej samej informacji: ceny i wolumenu.

**Czego Faza 0 NIE wykazała** (czytać razem z powyższym): momentum pozostaje
**nieprzetestowane** (bramka reżimu zagłodziła próbę do 0,53% świec), ETH/SOL/BNB — **zero
testów**, funding rate jako sygnał — **nigdy nie zaimplementowany**, ekonomia dźwigni —
**niezbadana**. Pełna lista: [Z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md).

Budżet zużyty: **10 wariantów**, 17 rund, 2 uruchomione reguły STOP. Stan testów: **265/265**.
Surowe wyniki każdej rundy: [`runs/`](runs/INDEX.md) (tabela + wnioski skumulowane).
Backlog i zasady pracy: [`STATUS.md`](STATUS.md).

### 🔵 Otwarta: hipoteza H2 — funding rate (decyzja użytkownika, 2026-09-22)

Pierwsze w projekcie źródło informacji **spoza OHLCV**. Własny licznik od zera (**0/1 zużytych**), własna reguła STOP, rachunek mocy **przed** eksperymentem.

[H2.0](runs/2026-09-22_h2.0-funding-wykonalnosc/README.md) pobrał dane (7 457 rekordów funding, 6,8 roku, zero dziur) i **odrzucił 2 z 3 sformułowań za 0 wariantów**. Wykonalne zostaje jedno: **funding jako 11. cecha, bez bramki reżimu, 4h** — pre-rejestrowane jako **H2.1**, kryterium `ci_low > 53,12%`, wymagany przyrost trafności **+2,85 pp**. Uczciwy prior: **niski** — żadna pojedyncza cecha w tym projekcie nie dała takiego efektu.

Pełny, aktualny status: [`STATUS.md`](STATUS.md).

## Kamienie milowe

> Aktualizowane przy każdym zamkniętym kamieniu (CLAUDE.md, zasada 15). Pełne wyniki — linki.

| Kamień | Data | Wynik (jedno zdanie) | Szczegóły |
|---|---|---|---|
| Commit 6 — checkpoint go/no-go | 2026-08-01 | **NO-GO** na BTC 5m (2025-07→2026-07); tylko 1/40 foldów policzalnych | `STATUS.md` §5 |
| C2c — kill-switch | 2026-08-01 | Deadlock naprawiony (cooldown/re-arm); NO-GO potwierdzone na 23/40 foldów — werdykt uwiarygodniony | `STATUS.md` §5 |
| C2d — bramka kosztowa | 2026-09-21 | Strata była w ~94% arytmetyczna (bariera<koszt); po bramce pozorny edge 54,6% spada do 49,3% | `STATUS.md` §5 |
| C2.5–C2.8 — seria falsyfikacji | 2026-09-21 | Progi regime, timeframe 1h/4h i cecha `adx_14` wyczerpane jako kierunki naprawy (wszystko NO-GO/nierozstrzygalne) | [runs/](runs/INDEX.md) |
| C2.9 — naprawa metodologii pomiaru | 2026-09-21 | Sweep seedów był pusty (deterministyczny XGBoost); NO-GO odporne na fold-jitter 10/10; strata per trade istotna w OBU reżimach | [runs/c2.9](runs/2026-09-21_c2.9-measurement-methodology/README.md) |
| C2.10 — nowa baza 3 lata (Z5) | 2026-09-21 | NO-GO strukturalne, nie ilościowe: bramka kosztowa blokuje 98% sygnałów `range`, `trend`=0,53% świec | [runs/c2.10](runs/2026-09-21_c2.10-extended-history-z5/README.md) |
| C2.11 — instrumentacja edge'u | 2026-09-21 | Blokada leży w geometrii wypłaty (2p−1)·B>C, nie w kierunku sygnału (p≈51%, wymagane 65–76%) | [runs/c2.11](runs/2026-09-21_c2.11-edge-instrumentation/README.md) |
| C2.12 — model wykonania maker/taker (Z6) | 2026-09-21 | Koszt −52%, ~połowa luki do opłacalności domknięta — nadal NO-GO; per-fold Sharpe przestał być wiarygodnym przyrządem | [runs/c2.12](runs/2026-09-21_c2.12-execution-cost-model/README.md) |
| C2.13 — próg pewności | 2026-09-21 | Hipoteza SFALSYFIKOWANA (trafność spadła zamiast wzrosnąć) — **reguła STOP programu "droga do GO" uruchomiona** | [runs/c2.13](runs/2026-09-21_c2.13-confidence-threshold/README.md) |
| Z16–Z21 — diagnostyka strukturalna + naprawy pomiaru | 2026-09-22 | Reżim `trend` strukturalnie niespójny z horyzontem etykiety (nie do naprawienia barierą); przeciek early stopping naprawiony — najczystsze p=50,38% (brak edge'u kierunkowego) | [runs/z16](runs/2026-09-22_z16-regime-coherence/README.md), [runs/z17+z21](runs/2026-09-22_z17-z21-early-stopping-leak/README.md) |
| Z9/Z19/Z5b — pivot na 4h | 2026-09-22 | Natywne dane 1h/4h (resample psuł wolumen!), rachunek mocy przed eksperymentem, **pre-rejestracja hipotezy jednoreżimowej 4h** (6,8 roku, kryterium: trafność ≥ 56,15%) | [runs/z5b](runs/2026-09-22_z5b-long-history-4h-preregistration/README.md) |
| S1 — eksperyment jednoreżimowy 4h | 2026-09-22 | **Kryterium NIESPEŁNIONE** (trafność 48,60%, CI [45,56%; 51,64%] wobec pre-rejestrowanego progu >54,60% — przepada o 9,04 pp) — **reguła STOP: seria zamknięta**. Walidacja (zasada 16a): **CAVEATS** — liczby potwierdzone co do cyfry, werdykt odporny, ale wynik obowiązuje na **6,95% historii** (krach COVID i szybkie ruchy poza zbiorem). Rekomendacja: zamknięcie Fazy 0 wynikiem negatywnym (Z10 opcja 1, decyzja przy użytkowniku) | [runs/s1](runs/2026-09-22_s1-single-regime-4h/README.md) |
| S1b — S1 po naprawie early stoppingu | 2026-09-22 | **NIEROZSTRZYGALNY** (klauzula `n<925`): naprawa podniosła foldy z early stoppingiem 5/63→53/63, ale ścięła próbę 1 037→345 (abstynencja modelu 70,9%→90,5%). Konfiguracja 4h/V=3 jest przy poprawnym pipelinie **nietestowalna** — brakuje 11,4 lat danych | [runs/s1b](runs/2026-09-22_s1b-early-stopping-naprawiony/README.md) |
| **Z10 — ZAMKNIĘCIE FAZY 0** | 2026-09-22 | **DECYZJA BRAMKOWA UŻYTKOWNIKA: Faza 0 zamknięta wynikiem negatywnym.** Pooled trafność **50,27%** (n=7 687, CI95 [49,15%; 51,38%]) — górny kraniec **1,30 pp poniżej** najniższego progu opłacalności (52,69%) przy mocy **2,8×**: dowód braku, nie brak dowodu. Wąskie gardło **informacyjne, nie inżynieryjne** — wszystkie 10 cech to transformacje ceny i wolumenu. Jawnie NIEPRZETESTOWANE: momentum, ETH/SOL/BNB, funding-jako-sygnał, ekonomia dźwigni | [runs/z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md) |
| **H2.0 — wykonalność nowej hipotezy (funding)** | 2026-09-22 | **Rachunek mocy odrzucił 2 z 3 sformułowań ZA 0 WARIANTÓW.** Bramka na skrajny funding — moc 0,05–0,44× (zagładza próbę jak `trend`). Carry — moc 0,03–0,12×, choć próg opłacalności spada **poniżej 50%** (48,13%): ogranicza liczba nienakładających się okien 48h, więc żyje w formule przekrojowej. Zostaje **funding jako 11. cecha bez bramki na 4h** — pre-rejestrowane jako H2.1 (1 wariant, reguła STOP) | [runs/h2.0](runs/2026-09-22_h2.0-funding-wykonalnosc/README.md) |

## Hipoteza w skrócie

**Hipoteza pierwotna (sfalsyfikowana w Fazie 0, patrz Kamienie milowe):** regime-gated —
deterministyczna reguła (nie model) rozdziela dane na reżim "trend" i "range".

- **Test 1 — Momentum:** w reżimie trend, cena kontynuuje ruch.
- **Test 2 — Mean-reversion:** w reżimie range, cena wraca do średniej po przegrzaniu.

Dwa osobne, niezależnie trenowane modele XGBoost — nie jeden połączony model. Walidacja najpierw
wyłącznie na BTC; ETH/SOL/BNB to test generalizacji tej samej hipotezy, nie równoległa walidacja
czterech strategii naraz.

**Hipoteza druga (pre-zarejestrowana w Z5b, sfalsyfikowana w S1):** architektura jednoreżimowa
na natywnych świecach 4h, pełna historia 6,8 roku, wygładzona bramka `range` (V=3), kryterium
sukcesu: trafność kierunku ≥ 56,15%. Wynik: **48,60%** wobec pre-rejestrowanego progu >54,60% —
kryterium przepadło o **9,04 pp**; reguła STOP zamknęła serię po pierwszym (jedynym
pre-zarejestrowanym) wariancie. **Sformułowanie „odrzucona z zapasem” zostało WYCOFANE
w walidacji zasady 16a** — odporne jest kryterium pre-rejestrowane, nie zapas wobec progu
liczonego z tych samych danych. Powtórzenie po naprawie early stoppingu (S1b) wyszło
**nierozstrzygalne** (n=345 < 925).

## Struktura projektu

```
clas5_core/
├── README.md                     ← ten plik
├── CLAUDE.md                     — instrukcje dla Claude Code (czytane automatycznie)
├── STATUS.md        — status commitów, żywy dokument
├── STATUS.md                      — zadania per commit + zasady pracy + Backlog (Z1–Z25)
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
├── tests/                        — testy jednostkowe/integracyjne/property-based (265)
└── requirements.txt
```

## Szybki start

```bash
git clone <adres-repo>
cd clas5_core
pip install -r requirements.txt --break-system-packages   # lub w wirtualnym środowisku

pytest -v          # 265 passed (stan na H2.0, 2026-09-22)
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
| `STATUS.md` | Plan, historia rund, ryzyka, zadania z ID i statusem, backlog — zmienia się często |
| `runs/INDEX.md` | Księga eksperymentów: co uruchomiono, z jakim wynikiem, ile wariantów zużyto |
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
(`STATUS.md`, Commit 6) **nie został osiągnięty — Faza 0 zamknięta wynikiem NEGATYWNYM**
(Z10, 2026-09-22): hipoteza Fazy 0 nie ma edge'u pokrywającego koszty. Nie uruchamiaj tego z
prawdziwymi środkami przed przejściem pełnej sekwencji: walidacja → paper trading → mały kapitał
w pełni tolerowalny do stracenia.

## Licencja

Do ustalenia przed publikacją repo.
