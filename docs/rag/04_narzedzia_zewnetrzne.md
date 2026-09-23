---
status: active
last_verified: 2026-09-22
depends_on: [01_hipoteza_i_architektura.md, 02_cechy_i_leakage.md]
---

# 04 — Narzędzia zewnętrzne: decyzje i uzasadnienia

Zasada wspólna dla wszystkich poniższych: **katalog wzorców do przeczytania i selektywnego
przepisania, nigdy zależność runtime w `requirements.txt` silnika produkcyjnego Fazy 0.**

## ADR — model wykonania: kiedy noga jest „maker", a kiedy „taker" (H3, 2026-09-22)

> **To jest odpowiedź na pytanie „czy `timeout → taker` to bug" NA ZAWSZE, nie na jedną rundę.**
> Pytanie wracało dwa razy (C2.12 przy projektowaniu modelu, H2.0 jako „podejrzenie") — tutaj
> jest kryterium, które rozstrzyga je raz.

### Kryterium

**Noga „maker" jest dobrze zdefiniowana tylko wtedy, gdy CENA zlecenia jest znana w momencie
jego składania.** Zlecenie limit to para *(cena, czas ważności)* — nie da się złożyć limitu
„na tę świecę, po cenie jaka wyjdzie".

Sprawdzenie na czterech nogach modelu:

| noga | cena znana z góry? | wyjście przymusowe? | noga | spójne? |
|---|---|---|---|---|
| wejście | **TAK** (bieżący `close`) | NIE — brak wypełnienia = nie wchodzimy | maker | ✔ |
| `tp` | **TAK** (`entry ± ATR_MULTIPLIER × ATR_14`, znane w chwili wejścia) | NIE — brak wypełnienia = nie było TP, transakcja trwa | maker | ✔ |
| `sl` | TAK, ale wyjście **obowiązkowe** | TAK | taker | ✔ |
| **`timeout`** | **NIE — znamy CZAS (świeca `t+V`), nie cenę** | TAK | **taker** | ✔ |

Obecna mapa nie jest przypadkowa ani niedbała — **jest dokładną implementacją tej zasady.**
`timeout` to jedyna noga, gdzie znamy czas, a nie cenę. To klasyczny trade-off egzekucji:
**albo pewny czas i nieznana cena (market/taker), albo pewna cena i nieznany czas (limit/maker).**
Nie da się mieć obu.

### Dlaczego wariant „timeout → maker" jest wewnętrznie NIESPÓJNY

Twardszy argument niż powyższy. `backtest/engine.py::_resolve_exit_price` liczy cenę wyjścia
timeoutu jako **`close` świecy timeoutu**. Żeby dostać *ten* `close` zleceniem limit, trzeba by:

- znać go z wyprzedzeniem — czyli **lookahead**, albo
- złożyć zlecenie dopiero w tej chwili — czyli **skrosować księgę** (taker).

**Naliczenie stawki maker za cenę osiągalną wyłącznie taker-em to policzenie tej samej korzyści
dwa razy.** Realistyczne „timeout → maker" wymagałoby WŁASNEGO modelu ceny wyjścia (limit na
poziomie X, wypełnienie tylko gdy rynek do X dojdzie, inaczej pościg za ceną), co zmieniłoby
`gross_pnl`, a nie tylko `cost`.

**Konsekwencja, którą trzeba nieść dalej:** kraniec `timeout_leg=MAKER` jest optymistyczny
**nie tylko na opłatach, ale i na CENIE**. Prawda leży więc **bliżej krańca `TAKER`**, niż
sugerowałaby naiwna mieszanka pół na pół.

### Dlaczego PASMO (dwie wartości), a nie ciągła stopa wypełnienia

Pytanie „a może φ = 0,6 timeoutów wypełnia się jako maker?" ma odpowiedź: **nie w tym repo.**

1. **Ciągły parametr nie dodaje informacji.** Koszt jest AFINICZNY w φ:
   `C(φ) = C_taker − φ · s_timeout · 0,0005`. Dwa krańce dają całą prostą — φ=0,6 policzysz
   interpolacją, bez uruchamiania czegokolwiek. Jedyne, co φ dokłada, to **stopień swobody**.
2. **Nie mamy czym go skalibrować.** φ to empiryczna stopa wypełnienia zleceń limit — wymaga
   danych o księdze zleceń / fillach, których Faza 0 nie ma. Jedyne dostępne źródło kalibracji
   to **wynik backtestu**, czyli strojenie po obejrzeniu wyniku (CLAUDE.md zasady 1 i 4).
3. **Każdy wiersz journalu musi być fizycznie realizowalny.** Przy φ=0,6 pojedyncza transakcja
   płaci stawkę, której nie płaci żaden realny fill.
4. **Przy dwóch krańcach raport ZAWSZE podaje oba.** Przy φ podaje jedną liczbę, a „φ dobrane
   rozsądnie" jest nieodróżnialne od φ dobranego pod wynik.
5. **Precedens:** `execution_model` rozwiązał identyczny problem dokładnie tak samo (C2.12/Z6)
   i to on daje dziś regresję baseline'u.

> **ZAPIS BLOKUJĄCY:** trzecia wartość `timeout_leg` albo parametr ciągły wymaga **ŹRÓDŁA
> DANYCH o wypełnieniach**. Bez niego nie wchodzi do repo. Powrót do tematu bez takiego
> źródła jest powtórzeniem sporu, nie jego rozstrzygnięciem.

### Bramka kosztowa = MAKSIMUM po osiągalnych nogach, nigdy wartość oczekiwana

Bramka (`agents.risk_controller.is_cost_feasible`) działa PRZED wejściem w pozycję, więc nie zna
powodu wyjścia. Musi więc założyć **najdroższy osiągalny** — i robi to przez
`backtest.costs.gate_cost_fraction`, która bierze `max` po `VALID_EXIT_REASONS`.

Gdyby liczyła koszt **oczekiwany** (tańszy, bo `tp` kosztuje 0,0004), przepuszczałaby świece,
na których stop-out jest arytmetycznie nie do pokrycia — dokładnie ten błąd, który bramka ma
łapać (Commit 2d).

**Usterka strukturalna naprawiona w H3:** do tej rundy bramka miała WŁASNĄ, ręczną kopię reguły
nóg (`entry_leg_for_gate = MAKER if ... else TAKER`) plus literał `exit_leg=TAKER`. Dwie kopie
tej samej wiedzy w dwóch modułach — rozjazd z journalem był kwestią czasu, nie dyscypliny.
Teraz bramka **nie ma własnej wiedzy o nogach**: konsumuje wyjście tej samej `execution_legs`,
co journal. Dodanie czwartego powodu wyjścia albo zmiana mapowania automatycznie ją przesuwa.
Pilnuje tego `tests/test_engine.py::test_cost_gate_value_equals_gate_cost_fraction`.

**Skutek uboczny, który czyni analizę wrażliwości uczciwą:** maksimum dla `maker_limit`
realizuje `sl` = 0,0009 **niezależnie od `timeout_leg`**, więc bramka przepuszcza dokładnie te
same sygnały w obu wariantach pasma. Porównanie „jabłka do jabłek" jest wymuszone konstrukcją,
nie deklaracją.

### Co zmierzono (H3, konfiguracja S1b: 4h, `range`, V=3, 6,8 roku)

| | TAKER (domyślne) | MAKER |
|---|---|---|
| koszt średni | 0,07670% | 0,04670% |
| break-even `p` | **52,69%** | **51,64%** |

**Pasmo progu: [51,64%; 52,69%], szerokość 1,05 pp.** Udział timeoutów 60,00%
(CI [54,83%; 65,17%]) — to jest dźwignia całego efektu.

**Werdykt: niepewność NIEISTOTNA DECYZYJNIE.** Oba krańce wymagają przyrostu trafności nad
opublikowaną wartość zbiorczą projektu (50,27%, Z10) większego (+1,37 pp / +2,39 pp) niż
cokolwiek, co jakakolwiek pojedyncza cecha dała w tym projekcie. **Domyślna pozostaje `TAKER`.**

### Ograniczenia, które NIE zniknęły

- **Adverse selection nadal niemodelowana w OBU krańcach.** Noga maker zakłada, że limit się
  wypełnia; realnie wypełnia się częściej, gdy rynek idzie przeciw pozycji. Pasmo mierzy
  niepewność co do OPŁAT, nie co do wypełnialności — to dwie różne rzeczy.
- Pasmo zmierzone przy `V=3`. Przy `V=12` timeouty to 20% (H2.0), więc pasmo byłoby ~3× węższe.
- Funding modelowany jedną stałą, mimo że od H2.0 mamy pobrany szereg (7 457 rekordów).

### Sprostowanie: bramka pomijająca funding NIE jest anty-konserwatywna

Plan H3 ostrzegał, że bramka pomija funding i że na 4h/V=3 to ~0,015% wobec bramki 0,090%
(~17%), czyli działa na niekorzyść. **Pomiar to obalił:** zmierzony funding to **−0,00243%**
nominału, czyli **2,7% bramki i ze ZNAKIEM UJEMNYM** (przychód, nie koszt). Dwa powody błędu
oszacowania: (a) zakładało trzymanie przez pełne `V` świec, a realnie bariera pada wcześniej;
(b) nie uwzględniało znaku — **short OTRZYMUJE dodatni funding**, a w próbie są obie strony.
Bramka, pomijając funding, jest więc **lekko konserwatywna**. Kandydat na osobną rundę wycofany.

Pełny write-up: `runs/2026-09-22_h3-noga-timeout-pasmo/README.md`.

## ADR — symulacja wypełnień na ścieżce cen zamiast odczytu z etykiety (W1, 2026-09-23)

**Status:** Accepted (decyzja użytkownika 2026-09-23: „pozycji nie otwieramy ani nie zamykamy
po cenie otwarcia/zamknięcia świecy, tylko po konkretnej cenie” — obowiązuje też na żywo).
**Pre-rejestracja i wynik:** `runs/2026-09-23_w1-wykonanie-po-cenie/README.md`.

### Kontekst

Do W1 silnik liczył wejście po `close` świecy sygnału i ZAKŁADAŁ, że zlecenie się wypełni, a cenę
wyjścia odczytywał z etykiety triple-barrier (`engine._resolve_exit_price`). C2.12 zapisało to
jako jawne ograniczenie („noga maker zakłada, że limit się wypełnia; pomija adverse selection”),
H3 dodało, że powrót do tematu wymaga DANYCH, nie kolejnego założenia. Zasada użytkownika czyni
z tego ograniczenia rozjazd między backtestem a handlem: backtest mierzył coś, czego na żywo nie
będzie.

### Decyzja

1. **Nowy moduł `backtest/execution.py`** — czyste funkcje na tablicach OHLC: wypełnienie zlecenia
   wejścia (limit / stop, ważność `k` świec, cena `min|max(open, P)`, brak przebicia = brak
   transakcji) i wyjście (TP/SL ±`ATR_MULTIPLIER`·ATR od CENY WYPEŁNIENIA, timeout po `close`
   świecy `t+V`). Dane to ścieżki cen; założeniem pozostaje „ścisłe przebicie poziomu = wypełnienie”
   (brak księgi zleceń) — nazwane tak w kodzie i w pre-rejestracji.
2. **Tryb `fill_model` w `engine.py`:** `"label"` (domyślny, dotychczasowe zachowanie bit w bit —
   regresja literałami w `test_engine.py`) i `"path"` (symulacja). Nazwany wariant, nie pokrętło —
   konwencja `execution_model`/`timeout_leg`.
3. **Rozdzielenie `run_backtest` na `collect_signals` (trening) i `simulate_equity` (wykonanie):**
   jeden trening obsługuje wszystkie warianty wykonania, więc lejek sygnałów jest identyczny
   między wariantami Z KONSTRUKCJI (lekcja H3: „jabłka do jabłek” wymuszone kodem, nie deklaracją).
4. **Trzy nazwane reguły wejścia** (`EntryRule`): `limit_close`, `limit_pullback` (0,5·ATR — jedna
   wartość, zero sweepu), `stop_breakout` (noga taker). **Ważność `k = 1` świeca** — z horyzontu
   prognozy modelu (etykieta mówi o 3 świecach od sygnału; wypełnienie w 3. zostawia jedną), nie
   z wyniku; `k ≤ V` wymuszone walidacją.
5. **Kolejność zdarzeń wewnątrz świecy:** tam, gdzie są świece 5m (2023-07 → 2026-07), rozstrzyga
   ścieżka 5m (obie bariery w jednej świecy 5m → SL pierwszy); na samych świecach 4h — w świecy
   wypełnienia liczy się tylko SL (TP mógł paść przed wypełnieniem), w kolejnych reguła etykiety.
   Kierunek obciążenia trybu 4h: NA NIEKORZYŚĆ strategii (test przykładowy w `test_execution.py`).
6. **Timeout zostaje po rynku** (taker, `close[t+V]`) — kryterium H3 („maker wymaga znanej CENY”)
   nie zmieniło się: przy wyjściu po czasie znamy moment, nie cenę.
7. **Sygnały niewypełnione** trafiają do osobnego dziennika `unfilled` z etykietą — do pomiaru
   selekcji przez wypełnienie (czy wypełniają się gorsze sygnały), nie do journalu equity.

### Odrzucone alternatywy

| opcja | dlaczego nie |
|---|---|
| zostać przy etykiecie | backtest mierzyłby wykonanie, którego na żywo nie będzie; ograniczenie z C2.12 nigdy nie zostałoby zmierzone |
| ciągła stopa wypełnień φ | odrzucona w H3: stopień swobody bez danych do kalibracji; jedyne źródło kalibracji = wynik backtestu = strojenie po wyniku |
| pełna symulacja księgi zleceń | brak danych o księdze/fillach w Fazie 0; nie da się zamodelować kolejki bez założeń gorszych niż „ścisłe przebicie” |
| ważność dobrana ze stopy wypełnień | dobór parametru po obejrzeniu danych; horyzont modelu daje kryterium niezależne od wyniku |

### Konsekwencje

- Łatwiejsze: każda przyszła hipoteza mierzona jest tak, jak będzie handlowana; dziennik `unfilled`
  daje pierwszy w projekcie pomiar adverse selection; kalibracja 4h≈5m mówi, ile ufać latom bez 5m.
- Trudniejsze: journal ma nową kolumnę `fill_bar_offset`; skrypty zamrożone (zasada 13) nadal
  wołają tryb `"label"` i pozostają odtwarzalne; koszt obliczeń symulacji jest pomijalny wobec
  treningu.
- Do rewizji: gdyby pojawiło się ŹRÓDŁO DANYCH o wypełnieniach (fille własnych zleceń z paper
  tradingu w Fazie 3), założenie „przebicie = wypełnienie” należy skalibrować, nie zakładać.

## freqtrade

Otwarty framework do tradingu krypto z wbudowanym FreqAI (feature engineering + ML). Powody, dla
których NIE jest zależnością:

- Wnosi cały swój bagaż (event loop, DataProvider, Telegram, sqlite, webserver) do systemu, który
  ma być odizolowany i audytowalny.
- Liczy wskaźniki przez TA-Lib — stąd nasza decyzja o TA-Lib jako jedynej bibliotece dla
  wszystkich cech (spójność z tym, co i tak jest tam popularne).
- Użyteczny jako: (a) katalog do przeglądania `populate_indicators()` konkretnych strategii i
  przepisywania logiki jako czystych funkcji z testem leakage, (b) opcjonalny silnik do paper
  tradingu w Fazie 3 (dry-run/testnet ma to wbudowane) — ale LEAN jest tu mocniejszym kandydatem
  (patrz niżej), konkretnie dla perpetual futures.

## QuantConnect / LEAN

**Rozróżnienie ważne:** QuantConnect to firma/platforma chmurowa; LEAN to jej silnik, open-source,
w pełni self-hostowalny (`pip install lean`, Docker) — to LEAN, nie QuantConnect-jako-cloud, jest
tu relewantny dla wymogu "100% lokalne" z oryginalnego PRD.

**Zweryfikowane researchem (nie założenie):**
- `AddCryptoFuture("BTCUSDT")` — natywne wsparcie perpetual futures na Binance, nie generyczny
  spot crypto.
- `BinanceFutureMarginInterestRateModel` — wbudowana symulacja funding rate (long płaci short przy
  dodatnim funding i odwrotnie), rozliczana 3x dziennie (12AM/8AM/4PM), zgodnie z rzeczywistym
  mechanizmem Binance.
- Dedykowane źródło danych: `Lean.DataSource.BinanceFundingRate` (GitHub, QuantConnect).
- Architektura event-driven (`OnData`) zaprojektowana specyficznie przeciwko look-ahead bias —
  bezpośrednio służy naszemu Compliance Gate.
- Oryginalny PRD miał `config/lean.json` w drzewie plików — prawdopodobnie pierwotny zamysł, nie
  przypadkowa nazwa.

**Mimo mocniejszego dopasowania niż freqtrade, NIE w Commit 5 (Faza 0):** już napisane i
przetestowane `fetch_ohlcv.py`/`feature_miner.py` nie są zbudowane pod strukturę `QCAlgorithm`
(Initialize/OnData/Portfolio/Slice). Przejście na LEAN teraz oznacza naukę nowego frameworka
zamiast odpowiedzi na pytanie, czy Test 1/Test 2 mają edge — ta sama pułapka sekwencji, której
unikamy od początku projektu.

**Gdzie LEAN faktycznie wchodzi:**
- **Faza 1:** `Lean.DataSource.BinanceFundingRate` jako źródło prawdziwych danych funding rate
  zamiast pisania własnego fetchera do Binance API.
- **Faza 3 (paper trading):** LEAN, nie freqtrade — mocniejszy kandydat konkretnie dla perpetual
  futures z realistycznym modelowaniem funding/marginu/lot size.

## Multi-agentowe frameworki LLM (TradingAgents, FinCon, HedgeAgents, FinAgent)

Aktywna, legalna dziedzina badań — nie fantazja. Kluczowy konflikt z naszą architekturą: większość
z nich ma **LLM W pętli decyzyjnej** (analiza sentymentu/newsów → decyzja tradingowa przez
rozumowanie językowe) — dokładnie to, czego się wyrzekliśmy (LLM offline/nadzorczo, patrz
`01_hipoteza_i_architektura.md`). Wzięcie takiej architektury wholesale byłoby cofnięciem się z
tej decyzji.

Dodatkowo: te systemy są budowane pod akcje (sentyment, fundamenty, earnings) — BTC/ETH perpetual
futures na 5m mają inną strukturę relewantnych danych (funding rate, open interest, likwidacje),
więc "wstaw i działa" i tak by nie zadziałało.

**Wzorce faktycznie warte wzięcia (przeczytania i przepisania, nie importu):**
- **FinCon** — mechanizm "verbal reinforcement" (agenty krytykujące się nawzajem w języku
  naturalnym po transakcji) — pasuje do `post_trade_critic.py` z Fazy 3 (LLM offline, analiza po
  fakcie), nie do decyzji real-time.
- **HedgeAgents** — "balance-aware" alokacja ryzyka między pozycjami — potencjalnie użyteczne do
  rozbudowy `risk_controller.py` w Fazie 1+, jeśli projekt kiedyś obejmie wiele instrumentów.
