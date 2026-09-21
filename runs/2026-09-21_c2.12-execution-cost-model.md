# C2.12 — realistyczny model wykonania maker/taker (Backlog Z6) (2026-09-21)

## ID testu

**C2.12** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.12-execution-cost-model`
- **Poprzedzający stan (master):** Commit 2.11 (`4be6a95`). Runda 2/4 programu „droga do GO".
- **Komenda:** `py -m backtest.run_checkpoint_v2` (pełny, ze sweepem fold-jitter)
- **Decyzja użytkownika (2026-09-21):** model wykonania = **maker na wejściu i take-proficie,
  taker na stop-lossie**; slippage tylko na nogach taker.
- **Zmiany:** `backtest/costs.py` — `MAKER_FEE_RATE=0.0002`, `leg_fee_rate`,
  `exit_leg_for_reason`, `total_round_trip_cost`/`round_trip_cost_fraction` liczą fee PER NOGA
  i slippage tylko dla nóg taker (domyślne taker/taker = wstecznie zgodne);
  `backtest/engine.py` — `_resolve_exit_reason`, `_execution_legs`, kolumna **`exit_reason`**
  w journalu, parametr `execution_model` (`taker_only` | `maker_limit`, domyślnie `maker_limit`);
  `config/settings.yaml` — `costs.maker_fee_rate` + opis założenia.
- **Źródło danych:** ta sama baza co C2.10/C2.11 (315 648 świec 5m, bez dziur).
- **Warianty hipotezy: 1** (zmiana modelu kosztów zmienia werdykt — liczona konserwatywnie).
- **Testy:** **182/182** (157 + 25 nowych: 9 w `test_costs.py`, 16 w `test_engine.py`).

## Dlaczego ta runda powstała

C2.11 pokazał, że werdykt jest przesądzony arytmetycznie: trafność 51,9%/50,6% wobec wymaganych
75,8%/64,9%. Koszt jest w tej nierówności członem dominującym — 0,14% nominału wobec **1,47 bps**
średniego edge'u brutto. Tymczasem `costs.py` modelował **wyłącznie takera po obu stronach**
(`round_trip_fee_cost` = `2.0 * notional * taker`), bez żadnej stałej maker. To nie było
założenie konserwatywne, tylko brak modelu: realna egzekucja limitem kosztuje 0,02%, nie 0,05%.

**Blokada usunięta po drodze:** żeby wycenić nogę wyjścia, trzeba wiedzieć, czy to TP czy SL —
a `label` był konsumowany w `_resolve_exit_price` i nie trafiał do journalu. Stąd nowa kolumna
`exit_reason`, wyprowadzona z **iloczynu** `direction * label` (sam `label` nie wystarcza: short
na etykiecie −1 to TP, nie SL).

## Metodologia

`exit_leg_for_reason`: `tp` → maker (take-profit spoczywa w księdze), `sl` i `timeout` → taker
(stop-loss musi być market, inaczej nie ma gwarancji wyjścia). **Asymetria jest celowa i działa
na niekorzyść strategii o niskiej trafności** — wygrana jest tańsza niż przegrana, więc model
jest konserwatywny wobec naszej hipotezy, nie pobłażliwy.

Bramka kosztowa (Commit 2d) działa PRZED wejściem w pozycję, więc nie zna powodu wyjścia —
dostaje więc założenie konserwatywne: wejście maker, **wyjście taker**. Zaniżenie kosztu w tym
miejscu przepuszczałoby sygnały, których bariera go nie pokrywa — dokładnie ten błąd, który
bramka ma łapać.

**ZAŁOŻENIE JAWNE (ograniczenie modelu, nie wynik):** noga maker zakłada, że zlecenie limit
**się wypełnia**. Model pomija adverse selection — limit wypełnia się częściej wtedy, gdy rynek
idzie przeciw pozycji, a nie wypełnia, gdy cena od razu ucieka w korzystną stronę. Realny koszt
maker jest więc wyższy niż modelowany tutaj o składnik, którego backtest Fazy 0 nie mierzy.

## Wynik

| Miara | C2.11 (taker_only) | **C2.12 (maker_limit)** | zmiana |
|---|---|---|---|
| Klasyfikacja | NO-GO | **NO-GO** | bez zmian |
| Foldy ważne / łącznie | 21 / 144 | **54 / 144** | **+157%** |
| Transakcje `range` / `trend` | 530 / 395 | **7 155 / 355** | **×13,5** / −10% |
| Koszt C (`range` / `trend`) | 0,1399% / 0,1402% | **0,0674% / 0,0685%** | **−52%** |
| Bariera B (`range` / `trend`) | 0,2707% / 0,4719% | 0,2031% / 0,3834% | **−25% / −19%** |
| break_even_p (`range` / `trend`) | 75,83% / 64,86% | **66,59% / 58,94%** | −9,2 pp / −5,9 pp |
| hit_rate (`range` / `trend`) | 51,89% / 50,63% | 51,07% / 49,86% | −0,8 pp / −0,8 pp |
| **margin (`range` / `trend`)** | −23,94 pp / −14,23 pp | **−15,52 pp / −9,08 pp** | **+8,4 pp / +5,1 pp** |
| Zwrot per trade (`range` / `trend`) | −0,001001 / −0,000712 | **−0,000686 / −0,000432** | **+35% / +39%** |
| pooled t (`range` / `trend`) | −10,47 / −5,51 | −23,20 / **−2,97** | — |
| pooled t po N_eff (`trend`) | −4,04 | **−1,75** | \|t\| < 2 |
| mean_sharpe | −12,39 | **−59,64** | patrz „Co na minus" |
| Fold-jitter: spójność znaku | 10/10 (100%) | **8/10 (80%)** | pogorszenie |
| Fold-jitter: σ / zakres | 3,09 / [−15,9; −6,2] | **75,74 / [−59,6; +155,7]** | pogorszenie |

## Co na plus (+)

- **Mechanizm zadziałał dokładnie tak, jak przewidziano w planie.** Koszt spadł o połowę,
  bramka kosztowa przestała blokować 98% sygnałów `range` (530 → 7 155 transakcji), a liczba
  ważnych foldów wzrosła 21 → **54**. To wprost atakuje problem strukturalny zdiagnozowany
  w C2.10 („niska liczba foldów jest strukturalna").
- **Ekonomika pojedynczej transakcji poprawiła się istotnie:** zwrot per trade −0,001001 →
  −0,000686 (`range`, +35%) i −0,000712 → −0,000432 (`trend`, +39%).
- **Margines — wspólny licznik postępu z C2.11 — poprawił się w obu reżimach**: +8,4 pp
  (`range`) i +5,1 pp (`trend`). To ok. **połowa** luki, którą trzeba domknąć.
- W `trend` zwrot per trade przestał być istotnie ujemny po korekcie N_eff (t_neff = **−1,75**,
  \|t\| < 2) — przy 355 transakcjach jest teraz nieodróżnialny od zera, a nie wyraźnie ujemny.
- `range` hit rate z n=7 155 daje z=**+1,81** — po raz pierwszy trafność ociera się o istotność
  (choć nadal jej nie osiąga).

## Co na minus (−)

- **Nadal NO-GO i nadal ujemny margines** (−15,5 pp / −9,1 pp). Obniżenie kosztu dało ok. połowy
  potrzebnej poprawy — zgodnie z policzonym wcześniej kontrfaktem, który przewidywał, że sama
  ta zmiana nie wystarczy.
- **Efekt jest mniejszy, niż wynikałoby z samego spadku kosztu — i wiadomo dlaczego.** Koszt
  spadł o 52%, ale **bariera też spadła** (−25% / −19%): tańszy koszt przepuszcza przez bramkę
  sygnały o węższej barierze, które wcześniej odpadały. `break_even_p` spadł więc tylko o 9,2 pp
  / 5,9 pp, nie proporcjonalnie do kosztu. To sprzężenie zwrotne, o którym warto pamiętać przy
  każdej kolejnej zmianie kosztu.
- **`mean_sharpe` przestał być użytecznym przyrządem** (−12,39 → −59,64 przy JEDNOCZEŚNIE
  lepszej ekonomice per trade), a sweep fold-jitter dał σ=75,7 i dwa offsety z wynikiem
  **dodatnim** (+134, +155) przy spójności znaku 80%. Przyczyna to znana z C2.9/Z2 patologia
  annualizowanego per-fold Sharpe'a: fold z kilkoma transakcjami o niemal zerowym std daje
  wartość dowolnie dużą. **Statystyką nośną są pooled t-staty i margin, nie mean_sharpe** —
  a kryteria klasyfikacji z docs/rag/03 opierają się właśnie na per-fold Sharpe. To dziś
  najsłabsze ogniwo pomiaru i kandydat do osobnej rundy (nie zmieniano tu kryteriów — docs
  je zamrażają).
- Model maker pomija adverse selection (patrz założenie wyżej) — realny koszt byłby wyższy.
- `trend` stracił 10% transakcji (395 → 355) mimo tańszej bramki; przyczyna nie została zbadana
  w tej rundzie (prawdopodobnie interakcja bramki z sizingiem/kill-switchem przy zmienionej
  ścieżce equity).

## Wniosek

Realistyczny model wykonania **zmniejszył lukę do opłacalności o około połowę** (margines
+8,4 pp / +5,1 pp) i usunął blokadę strukturalną, która dławiła próbę (foldy 21 → 54,
transakcje ×13,5 w `range`). Werdykt pozostaje **NO-GO**: do domknięcia brakuje jeszcze
**15,5 pp** trafności w `range` i **9,1 pp** w `trend`.

Runda ujawniła przy okazji, że **instrument klasyfikacji jest dziś mniej wiarygodny niż
mierzona wielkość**: per-fold Sharpe przy dużej liczbie transakcji rozjeżdża się do wartości
bez interpretacji (σ fold-jitter 3,1 → 75,7, dwa offsety dodatnie), podczas gdy pooled t-stat
i margines zachowują się stabilnie i spójnie.

## Rekomendacja

Zgodnie z programem — **Runda 3 (C2.13): próg pewności kalibrowany wewnątrz walk-forward**,
atakująca człon `p`. Z pomiaru sprzed programu (na populacji taker) trafność w górnym kwartylu
`signal_confidence` wynosiła 57,1% (`range`) i 63,3% (`trend`). Wobec NOWYCH progów break-even
(66,6% / 58,9%) oznaczałoby to −9,5 pp w `range`, ale **+4,4 pp w `trend`** — czyli pierwszy
dodatni margines w całym projekcie. Zastrzeżenie: tamte kwartyle mierzono na populacji 13×
mniejszej i inaczej przefiltrowanej, więc relacja musi zostać zmierzona od nowa — dokładnie
to robi Runda 3, z progiem pre-rejestrowanym (`q=0.75`, liczony na foldzie treningowym).

Przypomnienie reguły STOP: jeśli po Rundzie 3 pooled hit rate nie przekroczy istotnie
break-even w żadnym reżimie — stop i raport negatywny (Z10), bez dalszego szukania wariantów.

## Pełny surowy output

```
[data] 315648 świec: 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] brak dziur.

[seed=42] kanoniczny przebieg (offset=0)...

[tabela 144 wierszy per fold pominieta dla czytelnosci]

=== Klasyfikacja (kryteria docs/rag/03, NIEZMIENIONE) ===
{'classification': 'NO-GO', 'n_valid_folds': 54, 'n_total_folds': 144, 'fraction_above_threshold': 0.09259259259259259, 'fraction_le_zero': 0.8703703703703703, 'fraction_positive_sign': 0.12962962962962962, 'mean_sharpe': -59.639681477704926}

=== Rozbicie per reżim ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO             43             72                  0.023256          0.953488                0.046512   -73.794770
 trend          NO-GO             11             72                  0.363636          0.545455                0.454545    -4.306155

=== Diagnostyka pooled per reżim (Commit 2.9/Z2+Z3) ===
regime  n_trades  mean_return  std_return  sharpe_per_trade     t_stat       n_eff  t_stat_neff
 range      7155    -0.000686    0.002500         -0.274276 -23.200278 2348.959930   -13.293097
 trend       355    -0.000432    0.002743         -0.157399  -2.965616  123.418175    -1.748600
[interpretacja] |t_stat| < ~2 => średni zwrot per trade nieodróżnialny od zera
przy tej liczbie obserwacji; t_stat_neff dodatkowo koryguje za autokorelację.

=== Rozbicie edge'u: (2p-1)*B vs C (Commit 2.11) ===
regime  n_trades  hit_rate    z_stat   ci_low  ci_high  barrier_pct  cost_pct  break_even_p    margin
 range      7155  0.510692  1.808784 0.499109 0.522275     0.002031  0.000674      0.665873 -0.155181
 trend       355  0.498592 -0.053074 0.446579 0.550604     0.003834  0.000685      0.589387 -0.090796
[interpretacja] hit_rate = trafność kierunku PRZED kosztami (gross_pnl>0);
break_even_p = 0.5*(1 + C/B) = trafność wymagana, żeby wyjść na zero przy tej
szerokości bariery i tym koszcie; margin = hit_rate - break_even_p. Margin <= 0
oznacza, że werdykt jest przesądzony arytmetycznie, niezależnie od jakości modelu.
z_stat wobec H0: p=0.5 — |z| < ~2 => trafność nieodróżnialna od rzutu monetą.

[sweep] fold-jitter: offsety startu okien walk-forward 0..9 dni
  ... fold_start_offset_days=0
  ... fold_start_offset_days=1
  ... fold_start_offset_days=2
  ... fold_start_offset_days=3
  ... fold_start_offset_days=4
  ... fold_start_offset_days=5
  ... fold_start_offset_days=6
  ... fold_start_offset_days=7
  ... fold_start_offset_days=8
  ... fold_start_offset_days=9

=== Stabilność fold-jitter (Commit 2.9/Z1 — zamiast pustego sweepu seedów) ===
 offset_days  mean_sharpe classification  n_valid_folds  n_total_folds
         0.0   -59.639681          NO-GO             54            144
         1.0   -41.443063          NO-GO             56            144
         2.0   -46.170848          NO-GO             57            144
         3.0   -35.866491          NO-GO             59            144
         4.0   -13.586784          NO-GO             62            143
         5.0   -14.725307          NO-GO             61            143
         6.0   -15.627070          NO-GO             58            143
         7.0   -15.926748          NO-GO             59            143
         8.0   134.162784          NO-GO             60            142
         9.0   155.742263          NO-GO             61            142

std(mean_sharpe) po 10 offsetach = 75.7386; zakres = [-59.6397, 155.7423]; spójność znaku (ujemny) = 80%
[UWAGA] Celowo BEZ progu pass/fail — stary próg std<0.2 dotyczył (pustego) szumu
seedów i nie przenosi się na realną perturbację podziału danych. Interpretacja
rozkładu należy do użytkownika (patrz backtest/checkpoint_lib.py, docstring).
```
