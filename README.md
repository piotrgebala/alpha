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

Budżet zużyty (stan na Z10): **10 wariantów**, 17 rund, 2 uruchomione reguły STOP.
Surowe wyniki każdej rundy: [`runs/`](runs/INDEX.md) (tabela + wnioski skumulowane).
Backlog i zasady pracy: [`STATUS.md`](STATUS.md).

### 🔴 Po Fazie 0: wszystko, co da się zmierzyć, zmierzone (M1 + P1 + F1, 2026-09-22)

Po zamknięciu Fazy 0 sprawdziliśmy jeszcze dwie rzeczy, których Faza 0 nie zmierzyła, tym razem
na próbie ok. 8 000 transakcji (wystarczająco dużej, żeby rozstrzygnąć):

| co | trafność | próg opłacalności | wynik |
|---|---|---|---|
| momentum — „co rośnie, rośnie dalej” ([M1](runs/2026-09-22_m1-momentum-bez-bramki/README.md)) | 49,74% | 52,94% | brak przewagi |
| funding — opłata za trzymanie pozycji, jedyna informacja spoza wykresu ceny ([F1](runs/2026-09-22_f1-funding-zmierzony/README.md)) | 50,34% | 52,94% | brak przewagi |
| dane o pozycjach graczy ([P1](runs/2026-09-22_p1-sonda-zrodel-danych/README.md)) | — | — | nie da się zmierzyć: giełda daje tylko 30 dni historii |

**Co to znaczy:** przewidywanie KIERUNKU ceny BTC na tych danych nie daje przewagi — w każdym
wariancie model trafia jak rzut monetą. Otwarte zostały tylko kierunki, które zmieniają samo
założenie projektu (`STATUS.md` §17, ETAP 4). Pierwszy z nich — **carry przekrojowy**
(zarabianie na samej opłacie funding na wielu parach naraz, bez zgadywania kierunku) — jest
sprawdzany sondą wykonalności P2 (`runs/INDEX.md`).

Stan testów: **392/392** (2026-09-22).

### ⚪ Hipoteza H2 (funding) — ZAMKNIĘTA bez rozstrzygnięcia (2026-09-22)

Pierwsze w projekcie źródło informacji **spoza OHLCV**. Licznik wyczerpany (**1/1**), reguła STOP
zamknęła serię.

[H2.0](runs/2026-09-22_h2.0-funding-wykonalnosc/README.md) pobrał dane (7 457 rekordów, 6,8 roku,
zero dziur) i **rachunkiem mocy odrzucił 2 z 3 sformułowań za 0 wariantów**.
[H3](runs/2026-09-22_h3-noga-timeout-pasmo/README.md) sprostował próg (53,12% → **52,69%**)
i naprawił usterkę w liczeniu kosztów.
[H2.1](runs/2026-09-22_h2.1-funding-jako-cecha/README.md) — jedyny eksperyment — wyszedł
**NIEROZSTRZYGNIĘTY**: `n = 98` wobec wymaganych 1 000.

**Dlaczego:** zdjęcie bramki reżimu miało powiększyć próbę i powiększyło liczbę ocenianych świec
czterokrotnie (**zero pominiętych foldów** wobec 22 z 85 w S1). Ale przy okazji podniosło udział
klasy „nic się nie wydarzyło” z **60,83% na 66,58%** — a model uczy się przewidywać właśnie ją
i **przestaje handlować w 99,3% przypadków**.

**⚠ To, co runda rzekomo pokazała, zostało WYCOFANE 2026-09-22** (patrz kamień milowy F1): ~~funding potroił liczbę decyzji modelu (35 → 98), czyli został~~
uznany za informacyjny. O trafności tych decyzji nie mówi nic — próbka jest za mała.

*(Historyczne: po H2.1 następnym krokiem był wymiar przekrojowy. Funding jako cecha został
potem zmierzony osobno w F1 — patrz sekcja wyżej.)*

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
| **H3 — noga „timeout” w modelu kosztów** | 2026-09-22 | **Runda obaliła tezę, która ją zamówiła.** Podejrzenie z H2.0 nie broni się: **zlecenie oczekujące wymaga znanej CENY, a przy wyjściu „z upływem czasu” znamy tylko MOMENT**. Zmierzone pasmo progu **[51,64%; 52,69%]** — niepewność **nieistotna decyzyjnie**, poprzeczka NIE obniżona. Przy okazji: naprawiona usterka (koszt liczony w dwóch miejscach niezależnie) i sprostowany mój błąd rachunkowy z H2.0 (53,12% → **52,69%**) | [runs/h3](runs/2026-09-22_h3-noga-timeout-pasmo/README.md) |
| **H2.1 — funding jako cecha (jedyny eksperyment H2)** | 2026-09-22 | **NIEROZSTRZYGNIĘTY** (`n = 98 < 1 000`). Przyczyną nie jest funding ani długość historii, tylko **struktura zadania uczenia**: zdjęcie bramki podniosło udział klasy dominującej 60,83% → 66,58%, więc model **odmawia kierunku w 99,3%** świec. ~~Jedyne ustalenie: funding potroił liczbę decyzji (35 → 98).~~ **⚠ USTALENIE WYCOFANE 2026-09-22 (F1):** „potrojenie” NIE odtwarza się na naprawionym przyrządzie — przy n ~8 000 funding zmienia liczbę decyzji o **1%** (8 114 → 8 196), a nie trzykrotnie. Był to artefakt zagłodzonej próby: przy 35 decyzjach dowolne zaburzenie posteriora mnoży tę liczbę wielokrotnie → [runs/f1](runs/2026-09-22_f1-funding-zmierzony/README.md). **Licznik H2 wyczerpany (1/1), reguła STOP zamknęła serię** | [runs/h2.1](runs/2026-09-22_h2.1-funding-jako-cecha/README.md) |
| **K1 — kontrola pozytywna aparatu** | 2026-09-22 | **Pierwsze w projekcie sprawdzenie, czy przyrzad pomiarowy w ogole widzi sygnal.** Odpowiedz: **TAK** — przy podpowiedzi doskonalej mierzy 100,00% trafnosci, a kryterium werdyktu **nie dalo ani jednego falszywego alarmu na czystym szumie** (0/6). **ALE:** zaczyna widziec dopiero sygnal dajacy **~58%** trafnosci, podczas gdy do zarabiania wystarcza **~53%** — **luka 5,5 pp, w ktorej sygnal bylby oplacalny i niewidzialny**. Przyczyna: model odmawia dzialania w 99,3% swiec. Przy okazji: wbudowany werdykt GO/NO-GO **wystawil GO czystemu szumowi** | [runs/k1](runs/2026-09-22_k1-kontrola-pozytywna/README.md) |
| **K2 — naprawa abstynencji + kill-switch oczyszczony** | 2026-09-22 | **Model milczał, bo milczenie było dla niego opłacalne** — dwie trzecie świec kończy się „niczym", więc przy słabym sygnale odmawiał kierunku w **99,6%** przypadków. Sprawdzono dwa sposoby rozruszania go. **Wagi klas DZIAŁAJĄ:** liczba transakcji 644 → 97 tys., przyrząd zaczyna widzieć **słabszy sygnał niż dotąd**, a jego odczyt staje się monotoniczny (dotychczasowy kod czyta siłę sygnału chaotycznie). **Wymuszenie kierunku NIE DZIAŁA:** transakcji 260× więcej, ale na świecach kończących się niczym wymuszony kierunek wygrywa **48,33%** — gorzej niż rzut monetą — więc rozcieńcza sygnał aż do **ujemnego** marginesu. **Osobno zamknięte: kill-switch NIE zawyża trafności** (+0,04 pp przy ±0,34 pp) — podejrzenie z K1 było szumem. **Runda wykryła też, że dwie z trzech jej własnych reguł decyzyjnych są źle sformułowane** — decyzja o adopcji czeka na użytkownika | [runs/k2](runs/2026-09-22_k2-naprawa-abstynencji/README.md) |
| **A1 — wagi klas przyjęte do użytku** | 2026-09-22 | **Decyzja użytkownika: przyjmujemy naprawę, która wyszła lepiej w K2.** Model uczy się teraz z wagami odwrotnymi do częstości odpowiedzi, więc przestaje uciekać w milczenie. Stary sposób zostaje pod nazwą `none` i **nadal odtwarza dawne wyniki co do cyfry** (przypięte testem). **Uwaga praktyczna:** stare skrypty rund uruchomione dziś dadzą inne liczby niż zapisane — źródłem prawdy dla historii pozostają katalogi `runs/`. Sama adopcja natychmiast ujawniła **realny błąd**, którego runda nie mogła zobaczyć (przebieg wywracał się, gdy fold uczący nie zawierał wszystkich odpowiedzi) — naprawiony. **Otwarte:** model otwiera teraz pozycje także na świecach kończących się niczym; czy to szkodzi na realnej cesze — niezmierzone | [docs/rag/03 (ADR)](docs/rag/03_ryzyko_i_sizing.md) |
| **K3 — dwa odłożone pytania znów da się zmierzyć** | 2026-09-22 | **Przyrząd po raz pierwszy jest dokładniejszy niż to, czego szukamy.** Dwa badania zamknięto kiedyś werdyktem „nie da się rozstrzygnąć” — nie dlatego, że coś wyszło źle, tylko dlatego, że model podjął **345** i **35** decyzji. Po włączeniu wag klas te same konfiguracje dają **1 955** i **8 033** decyzje, a dokładność pomiaru poprawia się z 5,3 i 16,6 punktu do **2,2 i 1,1** — przy szukanym efekcie **2,4 punktu**. Sprawdzian wiarygodności: stan „sprzed zmiany” odtworzył liczby z archiwum co do sztuki. **Cena, powiedziana wprost:** model przestał wybierać świece kończące się wyraźnym ruchem, więc poprzeczka opłacalności podniosła się o pół punktu; czy ta selektywność coś wnosiła — ta runda z założenia nie sprawdza | [runs/k3](runs/2026-09-22_k3-mierzalnosc-po-a1/README.md) |
| **M1 — momentum dostało uczciwy test i go nie przeszło** | 2026-09-22 | **Pierwsza hipoteza postawiona po zamknięciu Fazy 0.** „Momentum” to założenie, że gdy cena rośnie, będzie rosła dalej. Projekt nigdy go porządnie nie sprawdził — filtr przepuszczał takie momenty przez **pół procenta czasu**, zostawało 299 transakcji i nie było czego mierzyć. Po naprawach z ostatnich dni momentum dostało **8 512 transakcji**. **Trafia w 49,74%, a musiałoby w 52,94%** — nawet najbardziej optymistyczny odczyt (50,80%) jest ponad dwa punkty poniżej progu, przy próbie dwukrotnie większej niż wymagana. **Czego NIE wolno z tego wyciągnąć:** że momentum jest gorsze od tego, co testowaliśmy wcześniej — różnica to szum. Jest **tak samo nieobecne**. Sprawdzian wiarygodności: ramię odniesienia odtworzyło historyczny pomiar co do jednej setnej punktu | [runs/m1](runs/2026-09-22_m1-momentum-bez-bramki/README.md) |
| **P1 + F1 — ostatnie mierzalne źródło informacji sprawdzone** | 2026-09-22 | **Najpierw sprawdziliśmy, co jeszcze da się zmierzyć.** Dane o pozycjonowaniu (ilu graczy stoi po której stronie) to najbardziej oczywisty kandydat na informację spoza wykresu ceny — ale giełda udostępnia je **tylko za 30 dni**, czyli ~112 transakcji wobec potrzebnych 4 500. **Cała klasa źródeł odpada, bo nie ma czego mierzyć.** Został funding — opłata za utrzymanie pozycji, jedyna informacja spoza ceny, którą mamy z siedmioletnią historią. **Trafia w 50,34%, a musiałby w 52,94%**; różnica wobec modelu bez niej to **trzy setne punktu**. **Przy okazji wycofaliśmy własne wcześniejsze ustalenie:** „funding potroił liczbę decyzji modelu” okazało się artefaktem małej próby — na poprawionym pomiarze zmienia ją o procent | [runs/f1](runs/2026-09-22_f1-funding-zmierzony/README.md) |

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
├── tests/                        — testy jednostkowe/integracyjne/property-based (319)
└── requirements.txt
```

## Szybki start

```bash
git clone <adres-repo>
cd clas5_core
pip install -r requirements.txt --break-system-packages   # lub w wirtualnym środowisku

pytest -v          # 319 passed (stan na H2.1, 2026-09-22)
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
