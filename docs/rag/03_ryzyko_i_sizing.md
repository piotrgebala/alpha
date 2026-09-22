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
