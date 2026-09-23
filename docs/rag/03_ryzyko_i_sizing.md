---
status: active
last_verified: 2026-09-22
depends_on: [01_hipoteza_i_architektura.md, 02_cechy_i_leakage.md]
---

# 03 — Ryzyko, sizing i metodologia walidacji

## Target: triple-barrier, ATR-scaled — nie forward return

```
upper barrier:    entry + 1.5 × atr_14
lower barrier:    entry − 1.5 × atr_14
vertical barrier: V świec — timeout (V=12 ≡ 1h na 5m; patrz uwaga o skalowaniu niżej)
label: która bariera trafiona pierwsza → +1 / −1 / 0
```

> **AKTUALIZACJA (2026-09-22, Z16/Z5b/S1):** `V` jest parametrem, nie stałą — `run_backtest`
> przyjmuje `vertical_barrier_candles` (Z22), a `embargo_candles` domyślnie podąża za nim.
> Dobór `V` podlega **twardemu ograniczeniu spójności**: nieprzerwany epizod reżimu musi być
> dłuższy niż okno etykiety, inaczej etykieta opisuje ruch spoza reżimu, który uzasadnił wejście.
> Zmierzone (Z16, 3 lata 5m): mediana epizodu `trend` = **2 świece**, `range` = **5**, przy
> V=12 → w `trend` tylko **0,49%** świec ma pełne okno wewnątrz reżimu. Na 4h spójny jest
> wyłącznie **V=3**. Narzędzie: `agents/regime_coherence.py::is_rule_admissible`.

Symetryczne progi na start w obu testach (asymetria — np. szerszy target dla momentum — to
Faza 1, nie teraz).

**Czemu nie forward return:** forward return (zwrot po N świecach) ignoruje, że w realnym
tradingu wychodzisz z pozycji przez stop-loss albo take-profit, nie po sztywnej liczbie świec.
Triple-barrier odwzorowuje faktyczny mechanizm wyjścia — trenujesz model na tym samym zdarzeniu,
na którym będziesz handlował.

**Krytyczne: ten sam mnożnik `1.5×ATR` jest używany w barierze (label) i w stop-lossie
risk_controllera.** To naprawia wcześniej zidentyfikowaną niespójność — jeśli te dwie liczby się
rozjadą, model jest trenowany na innym zdarzeniu niż to, na którym faktycznie handlujesz.
**Nie zmieniaj jednego bez zmiany drugiego.**

## Walk-forward split — zawsze chronologiczny, nigdy random

Okno: **skalowane per interwał** — na 5m 60 dni train / 14 test / krok 14; na 4h 60/28/28
(Z5b: przy 14 dniach fold ma ~22 świece `range`, poniżej `MIN_TRAIN_ROWS=30`, więc byłby
pomijany — to artefakt jednostek, bo okna są w DNIACH, a próg w ŚWIECACH). Na 6,8 roku danych
4h daje to **85 foldów**. Wartości startowe: `agents/labeling.py`. Test na tym samym zbiorze co train (random split) tworzy leakage czasowy —
model "widzi" przyszłość względem części danych treningowych.

**Diagnostyka efektywnej liczby próbek** (informuje interpretację wyniku, nie blokuje pipeline'u):
```
policz autokorelację return_lag_1 do lag ~50
N_eff ≈ N / (1 + 2·Σρ_k)
```
Jeśli N_eff jest o rząd wielkości mniejsze niż liczba wierszy — obniż próg pewności przy
interpretacji Sharpe'a z checkpointu.

## Dwa modele, osobno — nie jeden połączony

`model_momentum` (trenowany na danych Test 1 — świece "trend"), `model_reversion` (dane Test 2 —
świece "range"). Żadnego wspólnego modelu na tym etapie — uzasadnienie w
`01_hipoteza_i_architektura.md` (momentum i reversion to sprzeczne zakłady).

Start hiperparametrów (oba modele, na razie identyczne): `max_depth=4`, `learning_rate=0.05`,
`n_estimators=200`, `early_stopping_rounds=20` na **wydzielonym, chronologicznym OGONIE zbioru
treningowego** (`validation_fraction`, `agents/ml_optimizer.py`).

> **SPROSTOWANIE (2026-09-22, Z17+Z21+Z17b) — ta linia zakodowała buga.** Do 2026-09-22 stało
> tutaj: *„na foldzie OOS (nigdy na train — inaczej model dopasowuje się do szumu treningowego)"*.
> To **fałszywa alternatywa**: wybór nie jest między „OOS" a „cały train", bo istnieje trzecia
> opcja — wydzielony ogon treningu. Early stopping na foldzie OOS oznacza, że **liczba drzew jest
> dobierana na danych, na których mierzymy wynik**, czyli przeciek decyzji.
>
> **Zmierzony skutek (Z17):** `p` było ZAWYŻONE — `range` 51,07% → **50,38%**, a `z_stat`
> **+1,81 → +0,63**. Jedyny wynik w historii projektu wyglądający na „bliski istotności"
> (C2.12) okazał się artefaktem tej instrukcji.
>
> **Druga pułapka (Z17b):** samo wydzielenie ogona nie wystarczy, jeśli próg minimalnej wielkości
> walidacji wyłącza mechanizm po cichu. Przy `n_val = round(n·0,2)` i `MIN_VALIDATION_ROWS = 30`
> na świecach 4h **58 z 63 foldów (92,1%) trenowało się BEZ early stoppingu** — naprawa była
> formalnie w kodzie, ale martwa. Poprawka: `n_val = max(MIN_VALIDATION_ROWS, round(n·frac))`
> plus pole `early_stopping_used` w `folds_summary`, żeby ten stan nigdy nie był niewidoczny.
>
> **Konieczne uzupełnienie:** ogon treningu przylega do okna testowego, więc etykiety
> triple-barrier ostatnich `V` świec sięgają w test. Bez **embarga** (`embargo_candles = V`)
> walidacja jest skażona ruchem z okresu testowego i naprawa jest pozorna. Output: `predict_proba`, nie tylko klasa — potrzebne jako
`signal_confidence`.

**Dobór parametrów wskaźników i modelu — zasada:** zacznij od wartości branżowych/domyślnych
(Wilder RSI-14/ATR-14). Nie optymalizuj okien na całym zbiorze na raz — to data dredging. Jeśli
w ogóle optymalizujesz, rób to wewnątrz walk-forward, traktując okno wskaźnika jako hiperparametr
razem z hiperparametrami XGBoost, z tym samym rygorem antyprzeuczeniowym.

## Interfejs ml_optimizer → risk_controller

```
ml_optimizer emituje:
  { signal_direction: -1|0|1, signal_confidence: float,
    regime: "trend"|"range", atr_14: float, entry_price: float }

risk_controller zwraca:
  { position_size: float, stop_price: float, take_profit_price: float }
```

## Sizing — leverage cap zawsze wygrywa, jawnie

```
size_risk     = (equity × risk_per_trade) / (1.5 × atr_14)
size_leverage = (equity × max_leverage) / entry_price
position_size = min(size_risk, size_leverage)
```

- `risk_per_trade` = 0.5% equity (wartość startowa — fixed fractional, NIE Kelly na tym etapie:
  Kelly jest wrażliwy na błędy estymacji edge'u, co przy młodym modelu jest gwarantowane).
- `max_leverage` = 3x (wartość startowa, konserwatywnie).
- `signal_confidence` skaluje `risk_per_trade` liniowo — słabszy sygnał, mniejsza pozycja, nie
  próg odcięcia.
- Stop-loss z ATR (`1.5×atr_14`), nie ze stałego %: stały % ignoruje, że zmienność BTC zmienia
  się drastycznie między okresami.

**Dlaczego `min()`, nie któraś z formuł osobno:** bez jawnej reguły, w niskiej zmienności (mały
ATR → mały stop_distance) fixed-fractional może wypluć pozycję większą niż limit leverage. Reguła
musi być jawna, nie coś do odkrycia w runtime.

## Bramka kosztowa — GORNE oszacowanie kosztu, nigdy wartosc oczekiwana (H3, 2026-09-22)

`agents.risk_controller.is_cost_feasible` dziala PRZED wejsciem w pozycje, wiec **nie zna powodu
wyjscia** — a ten decyduje o typie nogi (limit czy market), czyli o koszcie. Musi wiec zalozyc
**najdrozszy osiagalny** powod wyjscia, i robi to przez `backtest.costs.gate_cost_fraction`,
ktora bierze `max` po wszystkich osiagalnych nogach.

**Dlaczego `max`, a nie wartosc oczekiwana.** Zadaniem bramki jest odrzucic swiece, na ktorych
nawet pelne trafienie bariery nie pokrywa kosztu (Commit 2d). Koszt oczekiwany jest tanszy, bo
`tp` wychodzi zleceniem limit (0,0004 wobec 0,0009 dla `sl`) — bramka liczaca go przepuszczalaby
swiece, na ktorych stop-out jest arytmetycznie nie do pokrycia. Czyli dokladnie ten blad, ktory
bramka ma lapac.

**Usterka strukturalna naprawiona w H3.** Do tej rundy bramka miala WLASNA, reczna kopie reguly
nog plus literal `exit_leg=TAKER` w `backtest/engine.py`. Nic nie wiazalo jej z kosztem liczonym
w journalu, wiec rozjazd byl kwestia czasu, nie dyscypliny — i faktycznie rozjechala sie
z kotwica testowa w `tests/test_risk_controller.py` (0,0014 vs produkcyjne 0,0009). Teraz bramka
**nie ma wlasnej wiedzy o nogach**: konsumuje wyjscie tej samej `execution_legs`, co journal.
Pelny ADR (kiedy noga jest maker, a kiedy taker): `docs/rag/04`.

**Funding poza bramka — zmierzone, nie zalozone.** Bramka swiadomie pomija funding, bo ten
zalezy od kierunku i czasu trzymania, wiec nie da sie go wyrazic jako staly ulamek nominalu.
H3 zmierzyl, ile to kosztuje na 4h/V=3: **-0,00243% nominalu, czyli 2,7% bramki, ze ZNAKIEM
UJEMNYM** (short OTRZYMUJE dodatni funding, a w probie sa obie strony). Pominiecie dziala wiec
w strone **konserwatywna**. Wczesniejsze oszacowanie "~17%, anty-konserwatywne" bylo bledne
co do znaku i rzedu wielkosci — zakladalo trzymanie przez pelne `V` swiec (bariera pada
wczesniej) i ignorowalo znak.

## Kill-switch

Prosta reguła, obecna już w backteście Fazy 0 (nie dopiero w Fazie 3): drawdown equity > X% od
peaku → zatrzymaj generowanie nowych sygnałów. Cel: zobaczyć historycznie, jak często by się
aktywował, zanim jest to komponent produkcyjny. Niezależny proces/wątek monitorujący konto — nie
część głównej pętli decyzyjnej (fail-safe, nie fail-soft).

## Checkpoint go/no-go — TRZY ścieżki, nie dwie

| Wynik | Kryterium (startowe) | Decyzja |
|---|---|---|
| **GO** | Sharpe po kosztach > 0.5 w >60% foldów, zgodny znak | Faza 1: regime router + funding rate |
| **WARUNKOWY** | Sharpe 0–0.5 lub niestabilny znak między foldami | Max 3 iteracje protokołu "jedna cecha na raz" (patrz `02_cechy_i_leakage.md`), potem decyzja ponownie |
| **NO-GO** | Sharpe ≤ 0 w większości foldów | Wróć do feature registry — inna hipoteza/cechy, NIE tuning tego samego zestawu |

Sprawdzić też: stabilność wyniku przy losowym seedzie modelu (sanity check overfittingu), wynik
osobno per reżim rynkowy (np. 2023 niska zmienność vs 2024-25 era ETF) — jedna liczba Sharpe
zagregowana po całym okresie maskuje niestabilność między reżimami.

**AKTUALIZACJA 2026-09-21 (Commit 2.9) — stabilność po seedach okazała się pusta poznawczo i
została zastąpiona.** XGBoost w konfiguracji Fazy 0 (`DEFAULT_XGB_PARAMS` bez
`subsample`/`colsample_bytree`) jest w pełni deterministyczny — seed nie zmienia ani jednego
drzewa, więc "std=0,0000 (STABILNY)" ze sweepu C6.3 mierzył dokładnie nic (empirycznie: wynik
identyczny do ostatniej cyfry w KAŻDYM eksperymencie C6→C2.8, ~10 niezależnych potwierdzeń).
Zamiennik (`backtest/checkpoint_lib.py::sweep_fold_offsets`, pierwszy użytkownik
`backtest/run_checkpoint_v2.py`): **fold-jitter** — przesunięcie startu okien walk-forward o
0–9 dni (`start_offset_days` w `generate_walk_forward_folds`). Perturbuje ARBITRALNY wybór
wyrównania granic foldów, nie model i nie hipotezę; offset=0 to dokładnie kanoniczny przebieg,
więc porównywalność historyczna zachowana. Świadomie BEZ nowego progu pass/fail (stary
std<0.2 dotyczył szumu seedów i nie przenosi się na realną perturbację podziału danych) —
raportowane są rozkład (std, zakres) i spójność znaku; interpretacja przy użytkowniku.
Dodatkowo od Commitu 2.9 raport checkpointu zawiera: per-fold `t_stat` (bez annualizacji —
annualizowany Sharpe przy 30–40 transakcjach na fold nadmuchiwał wartości do rzędów ±20–60),
zbiorczą diagnostykę pooled per regime oraz `N_eff`/`t_stat_neff` (efektywna liczba
niezależnych obserwacji z autokorelacji zwrotów — funkcja z C4.4, wpięta do raportu po raz
pierwszy). Kryteria klasyfikacji GO/WARUNKOWY/NO-GO z tabeli wyżej pozostają NIEZMIENIONE —
nowe miary są diagnostyką obok werdyktu, nie nowym werdyktem.

## PROG WYKRYWALNOSCI i degradacja `classify_checkpoint` (K1, 2026-09-22)

Pierwsza w projekcie KONTROLA POZYTYWNA aparatu pomiarowego: wstrzykniecie do prawdziwych
swiec syntetycznej cechy o ZNANEJ sile sygnalu i sprawdzenie, przy jakiej sile niezmieniony
pipeline zaczyna ja widziec. Pelny write-up: `runs/2026-09-22_k1-kontrola-pozytywna/`.

**Aparat dziala:** przy wyroczni doskonalej mierzy 100,00% trafnosci na 4 843 transakcjach —
lancuch cechy -> etykiety -> walk-forward -> trening -> bramki -> metryki przenosi sygnal
bez strat. **Kryterium `ci_low > break_even` jest uczciwe:** 0 falszywych alarmow na 6
losowaniach czystego szumu.

**Ale prog WYKRYWALNOSCI lezy POWYZEJ progu OPLACALNOSCI:**

| | trafnosc |
|---|---|
| prog oplacalnosci (ile trzeba, zeby zarabiac) | ~52,7% |
| prog wykrywalnosci (ile trzeba, zeby pipeline to UDOWODNIL) | ~58,2% |
| **luka** | **~5,5 pp** |

Hipoteza dajaca trafnosc 53-58% bylaby oplacalna i jednoczesnie NIEWIDZIALNA. Przyczyna nie
jest statystyczna, tylko behawioralna: przy slabym sygnale model **odmawia kierunku w 99,3%
swiec**, wiec proba spada do kilkudziesieciu transakcji. Przy q=0,20 trafnosc punktowa wyniosla
56,19% (powyzej progu oplacalnosci 51,90%), ale n=105 i CI siegalo 46,70%.

> **WYMOG DLA KAZDEJ PRZYSZLEJ RUNDY:** rachunek mocy przed eksperymentem musi podac, czy
> zakladana trafnosc hipotezy przekracza ~58%. Ponizej tego progu hipoteza jest **niemierzalna
> z gory**, niezaleznie od ilosci danych — i uruchamianie jej jest marnowaniem wariantu.

> **⚠ SPROSTOWANE W K2 (2026-09-22; notka dopisana 2026-09-23).** ~58,2% to trafnosc
> w pierwszym punkcie siatki `q`, w ktorym zapalilo sie kryterium — artefakt rozdzielczosci
> siatki, nie wlasciwosc przyrzadu. **Wymog „powyzej ~58%" UCHYLONY.** Obowiazuje
> `measurability_report(...)` z `backtest/metrics.py`; szerokosc pasma „oplacalne, ale
> niewidzialne" = `wald_half_width(n)`, zalezna wylacznie od `n` (CLAUDE.md zasada 18,
> `runs/2026-09-22_k2-naprawa-abstynencji/` §1). Tabela wyzej zostaje jako zapis pomiaru K1.

### `classify_checkpoint` — DIAGNOSTYKA, nie werdykt

K1 wykazal, ze `classify_checkpoint` zwraca **GO na czystym szumie** (q=0,10, zgodnosc cechy
z etykieta 40,3%) i **WARUNKOWY przy q=0** — czyli na danych, w ktorych z konstrukcji nie ma
czego znalezc. To ta sama patologia co per-fold `mean_sharpe` przy malym n (C2.12) i ten sam
efekt, ktory w H2.1 dal GO przy 3 i 11 waznych foldach.

**Kryteria GO/WARUNKOWY/NO-GO pozostaja formalnie w tym dokumencie jako zapis historyczny,
ale NIE SA kryterium werdyktu.** Werdykt orzeka sie na `ci_low > break_even` (przejscie
zapoczatkowane w C2.12, dowod dostarczony w K1). Zadnej wartosci GO/WARUNKOWY/NO-GO nie wolno
cytowac bez podania `n_valid_folds`.

### Abstynencja modelu — problem numer jeden

To ona, a nie brak sygnalu, ograniczyla S1b (n=345), H2.1 (n=98) i sama kontrole negatywna
K1 (n~37 na losowanie). **Przyrzad nie potrafi porzadnie zwalidowac sam siebie z dokladnie
tego samego powodu, dla ktorego nie widzi slabych sygnalow.** Kandydaci na osobna runde: wagi
klas w XGBoost, kalibracja `MIN_VALIDATION_ROWS`/`validation_fraction`, wymuszenie kierunku
zamiast trzeciej klasy "timeout".

**Stan kandydatow (2026-09-23):** wagi klas — PRZYJETE (ADR nizej, K2/A1); wymuszenie
kierunku — ODRZUCONE (K2: n rosnie, informacja nie); kalibracja `MIN_VALIDATION_ROWS`/
`validation_fraction` — ZBADANA w T4: early stopping dziala, prog 30 wierszy bezczynny przy
oknie 60 dni 4h, bez zmian w kodzie (`runs/2026-09-23_t4-kalibracja-early-stopping/`).

## Retraining modeli (temat dodany po przeglądzie szerszej wizji projektu)

Nie było w pierwotnym planie Fazy 0 — dodać w Fazie 1:
- Retraining na stałym harmonogramie (np. co miesiąc, spójnie z granulacją okna walk-forward)
  ORAZ wyzwalany retrening, jeśli live performance (rolling Sharpe/win-rate z ostatnich N
  transakcji) spadnie istotnie poniżej oczekiwań z backtestu — sygnał driftu reżimu, nie szumu.
- Nie retrenować częściej niż raz na okno testowe walk-forward — inaczej dopasowanie do
  najnowszego szumu zamiast trwałego wzorca.

## Ryzyko portfelowe przy wielu instrumentach (BTC/ETH/SOL/BNB)

Dotyczy Fazy 1+, po walidacji generalizacji hipotezy z BTC (patrz `01_hipoteza_i_architektura.md`).
Zapisane teraz, żeby nie zgubić przy projektowaniu `risk_controller.py` dla wielu instrumentów:

- **Kill-switch na poziomie CAŁEGO konta**, nie per instrument. Agregowany drawdown equity, nie
  cztery niezależne limity, które osobno wyglądają "w normie".
- **`risk_per_trade` i `max_leverage` muszą być świadome korelacji między pozycjami.** Cztery
  pozycje po 0.5% ryzyka każda dają 2% tylko przy zerowej korelacji — crypto altcoiny bywają
  silnie skorelowane z BTC, więc realne ryzyko portfela może być bliżej sumy niż dywersyfikacji.
  Rozważyć prosty limit na łączną ekspozycję (np. sumaryczny VaR portfela, nie suma VaR per
  instrument) zanim się skaluje na 4 instrumenty jednocześnie.
- **MPT Optimization i Correlation & Covariance** (odłożone wcześniej jako "nierelewantne przy
  jednym instrumencie") stają się relewantne dopiero na tym etapie — nie wcześniej.


## ADR — wagi klas WŁĄCZONE DOMYŚLNIE (adopcja ramienia A1 z K2, 2026-09-22)

**Decyzja.** `DEFAULT_CLASS_WEIGHT_MODE = CLASS_WEIGHT_BALANCED` w `backtest/engine.py`.
Model uczy się z wagami odwrotnymi do częstości klas, liczonymi **z części treningowej foldu**.
Wariant `CLASS_WEIGHT_NONE` zostaje jako nazwany wariant odtwarzający baseline sprzed K2.

**Status:** przyjęte decyzją użytkownika po rundzie K2
(`runs/2026-09-22_k2-naprawa-abstynencji/`).

### Problem

Klasa `timeout` (bariera pionowa, `label == 0`) ma **66,5% masy** w etykietach 4h przy V=3.
Model wielkoklasowy z celem `multi:softprob` i stratą `mlogloss` minimalizuje surową log-loss
na tym rozkładzie, więc **argmax na klasę większościową jest dla niego odpowiedzią optymalną**.
Skutkiem jest nie „słaby sygnał", tylko **odmowa działania**: przy słabym sygnale model nie
podawał kierunku w **99,6%** świec.

To nie jest problem teoretyczny — to on, a nie brak edge'u, ściął próbę w trzech rundach po
kolei: S1b (n=345), H2.1 (n=98), K1 (n≈37 na losowanie). Przy takim `n` pasmo „opłacalne, ale
niewidzialne" ma kilka do kilkunastu punktów procentowych, czyli **przyrząd nie widzi niczego,
co realnie moglibyśmy znaleźć**.

Ważne rozróżnienie, bez którego diagnoza jest błędna: **abstynencja sama w sobie NIE jest wadą.**
Przy doskonałej wyroczni wynosi 66,48% wobec 66,51% udziału timeoutów w etykietach — zgodność
do 0,03 pp. Model przewiduje prawdziwą klasę, a ta w dwóch trzecich świec jest timeoutem. Wadą
jest **zapaść przy słabym sygnale**: z 66,5% do 99,6%, gdy posterior kolapsuje do klasy
większościowej.

### Rozważone opcje i dlaczego ta

Zmierzone w K2 na tej samej krzywej wykrywalności (wyrocznia o znanej sile `q`), 12 losowań
przy q=0 i po 3 na punkt:

| opcja | abstynencja | n (q=0) | najsłabszy wykryty sygnał | werdykt |
|---|---|---|---|---|
| bez zmian (A0) | 99,6% | 644 | q = 0,40 | odrzucone — przyrząd zbyt gruboziarnisty |
| **wagi klas (A1)** | **43,6%** | **97 014** | **q = 0,30** | **PRZYJĘTE** |
| wymuszony kierunek (A2) | 0,0% | 167 160 | q = 0,40 | odrzucone — patrz niżej |

**Dlaczego nie A2 (wymuszenie kierunku).** Kusi, bo daje największą próbę (n ×260) i najwęższe
pasmo (0,24 pp). Ale kupuje `n` **bez informacji**: na świecach, których prawdziwa etykieta to
timeout, poprawny kierunek NIE ISTNIEJE, a wymuszony wygrywa tam w **48,33%** przypadków —
poniżej rzutu monetą. Te przegrane rozcieńczają sygnał: trafność spada do 50,33%, próg
opłacalności rośnie do 52,94%, a przy q=0,30 **margines robi się ujemny (−1,31 pp)** — sygnał
realnie informacyjny staje się nieopłacalny. **Więcej transakcji ≠ lepszy pomiar.**

**Dlaczego wagi, a nie `scale_pos_weight`.** `scale_pos_weight` to parametr celu BINARNEGO i przy
`multi:softprob` nie robi nic. Jedyną poprawną dźwignią jest wektor `weight` per wiersz na
`DMatrix`. Zapisane, bo każdy czytelnik sięgnie najpierw po `scale_pos_weight`.

**Dlaczego `w_c = N / (K·n_c)`.** Suma wag po wierszach wynosi `N`, więc skala hesjanów — a przez
nią `min_child_weight` i `eta` — jest ta sama co bez ważenia. Zmienia się **wyłącznie proporcja
między klasami**, nie ogólna siła sygnału uczącego. Bez tej normalizacji wagi ruszałyby dwie
rzeczy naraz i porównanie A0/A1 nie mówiłoby o wagach klas.

### Konsekwencje — w tym niewygodne

1. **Baseline projektu przesunął się.** Ta sama decyzja i ten sam koszt co przy C2.12
   (`DEFAULT_EXECUTION_MODEL` → `maker_limit`). Zamrożone skrypty rund (zasada 13) wołają
   `run_backtest` bez tego argumentu, więc **uruchomione dziś dadzą inne liczby** niż zapisane
   w ich katalogach `runs/`. Źródłem prawdy dla wyników historycznych pozostaje
   `runs/<katalog>/`; żeby odtworzyć je z kodu, trzeba podać jawnie
   `class_weight_mode=CLASS_WEIGHT_NONE`. Pilnuje tego test
   `test_class_weight_none_reproduces_pre_k2_baseline_exactly` (literały: 1 280 transakcji,
   `final_equity` 95 126,0168131146).

2. **Wagi są niedozwolone na ścieżce sprzed Z17** (`validation_fraction=None`, early stopping
   mierzony na foldzie OOS). Twardy błąd, nie ciche działanie — inaczej powstałby wariant
   „Z17 z wagami na wierzchu", wyglądający na ulepszenie, a będący regresją.

3. **Klasa nieobecna w części treningowej dostaje wagę neutralną 1,0.** Mapa wag powstaje
   z części uczącej, a stosuje się ją również do walidacyjnej; klasa, której w uczącej nie było,
   nie ma częstości do odwrócenia. Błąd `KeyError` na tej ścieżce **wystąpił realnie** przy
   adopcji (fold uczący wyłącznie z timeoutami) — patrz „Usterki wykryte przy adopcji" niżej.

4. **~~OTWARTE, NIEZMIERZONE~~ → ZMIERZONE w K3 (2026-09-22), patrz dopisek pod listą.** A1 schodzi **poniżej**
   podłogi abstynencji: 43,6% wobec 66,5% udziału timeoutów. Model otwiera więc pozycje również
   na świecach, które naprawdę kończą się niczym — czyli robi, w mniejszej skali, to samo, co
   dyskwalifikuje A2. Na wyroczni to nie szkodzi (sygnał jest idealnie zgodny z targetem), ale
   **realna cecha nie ma takiej struktury**. Do zmierzenia osobną rundą. Dopóki nie jest
   zmierzone, wynik każdej rundy na A1 trzeba czytać ze świadomością, że część próby to
   pozycje otwarte „na siłę".

5. **Co to NIE znaczy.** Adopcja A1 nie sprawia, że jakakolwiek hipoteza tradingowa zaczyna
   działać. Zmienia wyłącznie rozdzielczość przyrządu. Warunek z pre-rejestracji K2 pozostaje
   w mocy: **żadna liczba z K1/K2 nie może być cytowana jako wynik hipotezy tradingowej.**

### Dopisek po K3 (2026-09-22) — konsekwencja 4 jest ZMIERZONA

`runs/2026-09-22_k3-mierzalnosc-po-a1/` sprawdziło zastrzeżenie z punktu 4 na realnych cechach.
Wynik **potwierdza je w obie strony**, więc przestaje być ryzykiem, a staje się znaną
właściwością:

- **Działa tam, gdzie miało.** Abstynencja spada na realnych cechach nawet mocniej niż na
  wyroczni: 90,53% → 46,32% (z bramką reżimu) i 99,76% → 43,84% (bez niej). Próba rośnie
  z 345 do 1 955 i z 35 do 8 033, a rozdzielczość przyrządu z 5,28/16,56 pp do 2,22/1,09 pp.
- **Cena jest realna i zmierzona.** Model traci **selektywność**: przed adopcją brał świece
  kończące się na barierze (37,1% timeoutów wobec 66,5% w populacji), po adopcji bierze po
  równo z populacją (65,11%). Bariera na transakcję maleje, więc próg opłacalności rośnie
  o ~0,5 pp (52,43% → 52,93%).
- **Czego nadal nie wiemy:** czy utracona selektywność niosła informację. K3 z założenia nie
  patrzy na trafność (obie konfiguracje należą do serii zamkniętych), więc pytanie zostaje
  otwarte — ale jest teraz **konkretne i wykonalne** jako osobna runda na nowej hipotezie.

**Co to zmienia w praktyce:** wynik rundy prowadzonej na A1 należy czytać ze świadomością, że
próba jest mniej wyselekcjonowana niż przed adopcją, a poprzeczka opłacalności odpowiednio
wyższa. To nie jest powód, żeby A1 wycofać — to powód, żeby nie porównywać liczb sprzed
i po adopcji bez tej poprawki.

## ADR — cel modelu vs zarządzanie pozycją; próg opłacalności przy wypłatach asymetrycznych (N1, 2026-09-23)

**Status:** Accepted (decyzje użytkownika 2026-09-23: częściowe wyjście 50 % przy +5 % depozytu
przy dźwigni 3×, stop na cenę wejścia, reszta do 1,5·ATR, limit czasu 12 h).
**Pre-rejestracja i wynik:** `runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md`.

### Kontekst

Użytkownik prowadzi pozycję na żywo dwoma celami. Etykieta triple-barrier (±`ATR_MULTIPLIER`·ATR,
V świec) definiuje, czego model się uczy; zasada 3 wiąże stop z barierą etykiety. Pytanie: czy
nowy sposób prowadzenia pozycji to nowy TARGET (przebudowa etykiety, retrening), czy NAKŁADKA na
ścieżce cen po wejściu. W1b pokazało ponadto, że próg `0,5·(1 + C/B)` przestaje być progiem, gdy
wypłaty nie są ±B — a przy częściowym wyjściu asymetria jest wbudowana z definicji.

### Decyzja

1. **Etykieta zostaje symetryczna** (±1,5·ATR, V = 3). Stop początkowy = bariera etykiety (zasada 3
   spełniona), dalszy cel = bariera etykiety, a pierwsze, częściowe wyjście na bliższym celu jest
   **nakładką zarządzania** (`backtest/execution.py::ManagedExitRule`, `simulate_managed_exit`),
   liczoną na tej samej ścieżce cen co wypełnienia z W1. Model i sygnały są identyczne z kontrolą,
   więc porównanie jest parowane transakcja po transakcji i runda ma DOKŁADNIE jedną zmienną.
2. **Cele uporządkowane:** bliższy z (`E·(1 ± 1,67 %)`, `E ± 1,5·ATR`) zamyka 50 % i przesuwa stop
   na `E`; dalszy zamyka resztę. Tak działają dwa zlecenia limit w księdze; w ~21 % świec
   (`1,5·ATR < 1,67 %`) kolejność jest „odwrócona" i reguła to obsługuje bez wyboru po wyniku.
3. **Journal per noga:** `TradeOutcome.legs` (ułamek, świeca, cena, powód), nowe powody wyjścia
   `tp_partial` (maker) i `be_stop` (taker) w `costs.py`; koszt `multi_leg_cost` = noga wejścia na
   całym nominale + nogi wyjścia na ich ułamkach + funding per część; jedna noga deleguje do
   `total_round_trip_cost` (bit w bit — wszystkie wcześniejsze rundy odtwarzalne).
4. **Próg opłacalności uogólniony:** `p* = (L̄ + C) / (W̄ + L̄)` — trafność, przy której oczekiwana
   wypłata jest zerem dla ZMIERZONYCH średnich wygranej `W̄` i straty `L̄` (brutto, % nominału)
   i kosztu `C`. Dla ±B redukuje się do `0,5·(1 + C/B)`. **Kryterium POZYTYWNE = `t_neff(zwrot
   netto) > 1,96` ORAZ `ci_low(p) > p*`** — zwrot jest członem nośnym (wytyczna CLAUDE.md po W1b),
   trafność wchodzi wyłącznie przez próg dopasowany do rzeczywistych wypłat.

### Odrzucone alternatywy

| opcja | dlaczego nie |
|---|---|
| etykieta asymetryczna pod bliższy cel (+1,67 % / −1,5·ATR) | inny model i inne sygnały niż kontrola — dwie zmiany naraz; łamie zasadę 3 tylko pozornie (stop zostaje), ale zmienia proporcje klas i abstynencję, więc efekt zarządzania byłby nieodróżnialny od efektu retreningu |
| osobny model dla drugiej połowy (kiedy trzymać, kiedy wyjść) | nowa hipoteza z własnym licznikiem; nie ma czego uczyć, dopóki pierwsza nie pokaże sygnału |
| trailing stop zamiast stałego dalszego celu | użytkownik wybrał stały cel (1,5·ATR); trailing to inny wariant (nie w tej rundzie) |
| próg `0,5·(1 + C/B)` z `B` = średnia |wyjście − wejście| | W1b: przy wypłatach asymetrycznych daje „trafność nad progiem" przy stracie; nie jest progiem, tylko diagnostyką |

### Konsekwencje

- Łatwiejsze: każda przyszła reguła prowadzenia pozycji (trailing, kilka celów) to nowa
  `ManagedExitRule`, nie nowy silnik; koszty per noga są jawne w journalu.
- Trudniejsze: journal ma trzy nowe kolumny (`n_legs`, `partial_exit_price`,
  `partial_exit_bar_offset`); `summarize_edge_by_regime` liczy `barrier_pct` z OSTATNIEJ nogi,
  więc przy nogach wielu jest miarą diagnostyczną (adnotacja w raporcie rundy).
- Do rewizji: gdy pojawi się hipoteza z sygnałem, wrócić do pytania, czy etykieta ma kodować
  pierwszy cel (wtedy osobna runda z własnym licznikiem).
