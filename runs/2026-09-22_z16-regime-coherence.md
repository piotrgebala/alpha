# Z16 — spójność bramki reżimu z horyzontem etykiety: `range` naprawialny, `trend` nie (2026-09-22)

## ID testu

**Z16** (Backlog II) — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/Z16-regime-coherence`
- **Poprzedzający stan (master):** `23abd2e` (audyt po programie „droga do GO").
- **Komenda:** `py -m backtest.diagnose_regime_coherence`
- **Nowe pliki:** `agents/regime_coherence.py` (czyste, przetestowane funkcje),
  `backtest/diagnose_regime_coherence.py` (skrypt, poza pytest),
  `tests/test_regime_coherence.py`.
- **Źródło danych:** `data/raw/BTC-USDT-USDT_5m_20230701T000000Z_20260701T000000Z.parquet`
  (315 648 świec, bez dziur; 309 875 z policzalnymi cechami).
- **Warianty hipotezy: 0** — pomiar poprawności SPECYFIKACJI, bez uruchamiania modelu
  i bez oceniania czegokolwiek PnL-em. Kryteria definicyjne, nie strojone.
- **Testy:** **214/214** (190 + 24 nowych: 20 jednostkowych + 4 property-based).

## Po co ta runda

Program C2.11–C2.13 pokazał, że człon `p` nierówności `(2p−1)·B > C` jest nieruchomy: dwie
niezależne, pre-rejestrowane próby jego podniesienia dały wynik negatywny (C2.13 wręcz
odwrotny do przewidywanego). Audyt po regule STOP postawił hipotezę **wyjaśniającą**: `p`
był mierzony na sygnale o wewnętrznie niespójnej specyfikacji, bo bramka kwalifikuje świecę
do reżimu trwającego kilka świec, a etykieta ocenia ruch przez 12 świec (60 min). Ta runda
tę hipotezę **mierzy**, a nie zakłada.

Zabezpieczenie metodologiczne w kodzie: `regime_episodes` liczy epizody po POZYCJACH,
więc dziura w środku serii zlepiłaby dwa epizody i **zawyżyła** dokładnie tę wielkość,
którą runda mierzy. Stąd `assert_contiguous_timestamps`, wołane przez skrypt zarówno na
pełnej serii, jak i po odcięciu warmupu wskaźników (odcięcie jest prefiksem, więc ciągłość
zachowana) — oraz test jednostkowy na dziurę w środku.

## Wynik — Blok 1: obecna reguła jest niespójna w OBU reżimach

| reżim | epizodów | mediana | p90 | max | świec |
|---|---|---|---|---|---|
| `trend` | 728 | **2 (10 min)** | 5 | 15 (75 min) | 1 636 |
| `range` | 9 717 | **5 (25 min)** | 16 | 63 (5h15m) | 66 996 |
| `ambiguous` | 10 445 | 3 | 67 | 1 167 (97h) | 241 243 |

Przy `VERTICAL_BARRIER_CANDLES = 12` (60 min):

| reżim | horyzont | epizodów ≥ horyzont | świec z pełnym oknem w reżimie | udział | spójna? |
|---|---|---|---|---|---|
| `trend` | 12 | **4 / 728** | **8** | **0,49%** | NIE |
| `trend` | 48 | 0 / 728 | 0 | 0% | NIE |
| `range` | 12 | 1 729 / 9 717 | 14 123 | **21,1%** | NIE |
| `range` | 48 | 20 / 9 717 | 105 | 0,16% | NIE |
| oba | 144 / 576 | 0 | 0 | 0% | NIE |

**Hipoteza potwierdzona.** W `trend` etykieta opisuje ruch wyłącznie wewnątrz reżimu dla
**0,49%** świec — czyli 99,5% transakcji `trend` było etykietowanych ruchem, który
w większości dział się poza reżimem uzasadniającym wejście. W `range` to 21,1%.

## Wynik — Blok 2: człon B jest zamknięty (domyka Backlog Z8 za 0 wariantów)

Koszt `C = 0,0900%` (maker-wejście + taker-wyjście — konserwatywne założenie bramki z C2.12).

| reżim | p | 2p−1 | B obecne | **B wymagane** | krotność | implikowany horyzont | max epizod |
|---|---|---|---|---|---|---|---|
| `range` | 0,5107 | +0,0214 | 0,1372% | **4,2088%** | **30,7×** | **11 299 świec (~39 dni)** | 63 świece |
| `trend` | 0,4986 | −0,0028 | 0,4107% | — | — | **żaden nie pomaga** | 15 świec |

`range` wymagałby horyzontu **~39 dni**, przy najdłuższym zmierzonym epizodzie **5h15m** —
rozbieżność o trzy rzędy wielkości. W `trend` `2p−1 < 0`, więc **szersza bariera pogarsza
wynik**: nie istnieje żadna szerokość rozwiązująca problem.

**Backlog Z8 (rozdzielenie timeframe od horyzontu) jest więc niewykonalny przy obecnej
definicji reżimu** — i zostaje zamknięty jako taki, nie jako „zmierzony negatywnie"
(hipoteza bez uruchomienia nie jest zmierzona). Koszt domknięcia: 0 wariantów.

## Wynik — Blok 3: `range` jest naprawialny, `trend` nie (najważniejsze ustalenie)

| reguła | `trend`: mediana / udział | `range`: mediana / udział | dopuszczalna |
|---|---|---|---|
| obecna (0,7/0,3) | 2,0 / 0,53% | 5,0 / 21,62% | nie |
| luźniejsza (0,5/0,5) | 2,0 / 4,67% | 10,0 / 45,67% | nie |
| luźniejsza (0,4/0,4) | 2,0 / 5,50% | 5,0 / 28,51% | nie |
| obecna + wygładzenie 12 | 7,0 / 0,08% | 17,0 / 21,02% | nie |
| **0,5/0,5 + wygładzenie 12** | 7,0 / 1,52% | **39,0 / 46,90%** | nie |
| **0,5/0,5 + wygładzenie 48** | 10,0 / 0,05% | **89,0 / 48,18%** | nie |

Formalnie żadna reguła nie przechodzi — ale **blokerem jest wyłącznie `trend`**, i widać
tu asymetrię, której wcześniej nie mierzyliśmy:

- **`range` daje się uspójnić.** Wygładzanie modą w oknie 12 świec (tylko przeszłość, zero
  leakage'u) podnosi medianę epizodu 5 → **39 świec** przy zachowanym udziale **46,9%**.
  To spełnia kryterium spójności z nadwyżką (39 ≥ 12) i ma ogromną próbę.
- **`trend` jest strukturalnie niemożliwy do uspójnienia.** Wygładzanie wydłuża epizody
  (2 → 7 → 10), ale **udział reżimu zapada się do 0,05–1,5%** — czyli dokładnie do stanu,
  w którym 61/72 foldów było pomijanych w C2.10. Dwa warunki (długie epizody, dość próbek)
  są w `trend` po prostu sprzeczne przy `direction_persistence_10` na 5m.

## Co na plus (+)

- Hipoteza wyjaśniająca z audytu **potwierdzona pomiarem**, nie założona. „Nie ma edge'u"
  zamienia się w „bramka i target mierzyły różne horyzonty" — z liczbą 0,49% dla `trend`.
- **Z8 domknięty za 0 wariantów budżetu.** Trzy rzędy wielkości rozbieżności to nie jest
  wynik wymagający uruchomienia eksperymentu.
- Nowe, ponownie użyteczne narzędzie: `is_rule_admissible` daje kryterium przesiewu reguł
  reżimu **bez dotykania modelu i bez wydawania budżetu** — to bezpośrednio przeformułowuje
  Backlog Z7 z „kolejnego wariantu po negatywnym wyniku" na mierzalny warunek konieczny.
- Zabezpieczenie na nieciągłość serii (guard + test) chroni pomiar od błędu, który
  zawyżałby mierzoną wielkość.
- Asymetria `range` vs `trend` to nowa, konkretna informacja o architekturze, nie o modelu.

## Co na minus (−)

- **Runda nie przybliża do GO ani o krok** i nie było to jej celem. Diagnostyka.
- `trend` z wygładzaniem 48 ma medianę 10 świec, więc nawet nie spełnia kryterium spójności
  przy V=12 — a udział 0,05% oznacza ~150 świec w 3 latach. Ten reżim po prostu nie istnieje
  w użytecznej formie przy tej definicji na 5m.
- **Nawet uspójniony `range` nie domyka arytmetyki.** B wymagane = 4,21%, a wygładzenie nie
  poszerza bariery — `B = ATR_MULTIPLIER × ATR_14`, więc nie rośnie z horyzontem. Dłuższe
  V daje tylko więcej czasu na trafienie TEJ SAMEJ bariery (mniej timeoutów), nie szerszą
  barierę. Uspójnienie jest warunkiem **koniecznym** wiarygodnego pomiaru `p`, nie
  wystarczającym dla GO.
- Wygładzanie modą jest jednym z wielu możliwych sposobów wydłużenia epizodów (alternatywy:
  histereza progów, minimalny czas trwania reżimu, reguła na wolniejszej cesze). Blok 3
  celowo nie przeszukuje tej przestrzeni — to byłoby dobieranie reguły, a nie pomiar.
- `MEASURED_HIT_RATE` jest wpisane jako stała z C2.12; gdyby `p` zmieniło się w kolejnej
  rundzie, blok 2 wymaga aktualizacji (świadomy kompromis — alternatywą był pełny backtest
  w skrypcie diagnostycznym).

## Wniosek

Niespójność bramki z horyzontem jest **zmierzona i duża**: w `trend` tylko 0,49% świec ma
etykietę opisującą ruch wewnątrz własnego reżimu. To wyjaśnia nieruchomość członu `p`
w C2.13 — mierzyliśmy trafność sygnału, którego definicja jest wewnętrznie sprzeczna.

Jednocześnie runda **zamyka dwie drogi i otwiera jedną**:
- **zamknięta:** człon B (Z8) — wymagany horyzont ~39 dni vs epizod 5h15m; w `trend`
  dodatkowo `2p−1 < 0`, więc żadna bariera nie pomaga;
- **zamknięta:** reżim `trend` przy `direction_persistence_10` na 5m — warunki „długie
  epizody" i „dość próbek" są w nim sprzeczne;
- **otwarta:** reżim `range` daje się uspójnić (mediana 5 → 39 świec przy udziale 46,9%),
  więc pomiar `p` w `range` da się po raz pierwszy wykonać na sygnale spójnym z targetem.

## Rekomendacja

Decyzja przy użytkowniku. Materiał wskazuje jedną drogę merytoryczną i jedną porządkową:

1. **Architektura jednoreżimowa (`range`) z uspójnioną bramką** — jedyna droga, w której
   pomiar `p` jest w ogóle interpretowalny. Uwaga: to **nowa hipoteza**, nie wariant obecnej
   (porzucamy dwureżimowość, która jest rdzeniem hipotezy z docs/rag/01), więc własna
   pre-rejestracja, własny licznik wariantów i własna reguła STOP.
2. **Przed jakimkolwiek pomiarem `p`: Z17 i Z21.** `p` jest dziś **zawyżone** przecieku
   early stopping (`ml_optimizer.py:130` dobiera liczbę drzew na foldzie OOS), a purge/embargo
   nie istnieje w repo — przy dłuższym horyzoncie (wygładzanie 12–48) przeciek etykiet
   rośnie liniowo z V i przestaje być pomijalny. Mierzenie `p` na uspójnionym sygnale bez
   tych napraw dałoby liczbę równie niewiarygodną, tylko z innego powodu.

Trzeźwo: nawet przy `p` zmierzonym poprawnie na spójnym sygnale luka do domknięcia wynosi
**B 0,137% wobec wymaganych 4,21%**. Uspójnienie może podnieść `p`, ale żeby zamknąć
nierówność przy `B ≈ 0,14%`, `p` musiałoby wynieść ~83%. Realistycznie GO wymagałoby
JEDNOCZEŚNIE wyższego `p` i radykalnie innej relacji B/C — czyli grubszego interwału
(Backlog Z9, teraz wykonalny) z proporcjonalnie przeskalowanym horyzontem i szerszym
mnożnikiem ATR. To kierunek, nie obietnica.

## Pełny surowy output

```
[data] 315648 świec: 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] brak dziur.
[data] seria ciągła, 315648 świec

[regime] świec z policzalnymi cechami: 309875

================================================================================================
BLOK 1 — spójność OBECNEJ reguły reżimu z horyzontem etykiety
================================================================================================
VERTICAL_BARRIER_CANDLES = 12 świec = 60 min (horyzont, na którym liczona jest etykieta)

-- długości nieprzerwanych epizodów reżimu (świece 5m) --
trend      epizodów=   728  mediana=   2.0  p90=   5.0  max=   15 (    75 min)  świec=   1636
range      epizodów=  9717  mediana=   5.0  p90=  16.0  max=   63 (   315 min)  świec=  66996
ambiguous  epizodów= 10445  mediana=   3.0  p90=  67.0  max= 1167 (  5835 min)  świec= 241243

-- tabela spójności: ile świec ma CAŁE okno etykiety wewnątrz epizodu --
regime  horizon_candles  horizon_minutes  median_length  n_episodes_ge_horizon  n_episodes  n_windows_inside  share_windows_inside  coherent
 trend               12               60            2.0                      4         728                 8              0.004890     False
 trend               48              240            2.0                      0         728                 0              0.000000     False
 trend              144              720            2.0                      0         728                 0              0.000000     False
 trend              576             2880            2.0                      0         728                 0              0.000000     False
 range               12               60            5.0                   1729        9717             14123              0.210804     False
 range               48              240            5.0                     20        9717               105              0.001567     False
 range              144              720            5.0                      0        9717                 0              0.000000     False
 range              576             2880            5.0                      0        9717                 0              0.000000     False

[interpretacja] coherent = mediana długości epizodu >= horyzont etykiety.
share_windows_inside = ułamek świec reżimu, dla których etykieta opisuje ruch
WYŁĄCZNIE wewnątrz reżimu, który zakwalifikował wejście. Niskie wartości znaczą,
że bramka i target mierzą różne rzeczy — i że `p` nie jest interpretowalne.

================================================================================================
BLOK 2 — konsekwencja dla członu B (domknięcie Backlog Z8 bez wydawania wariantu)
================================================================================================
koszt round-trip C = 0.0900% nominału (model maker_limit, C2.12)

reżim            p      2p-1   B_obecne  B_wymagane  krotność  implik. horyzont  max epizod
range       0.5107   +0.0214    0.1372%     4.2088%     30.7x       11299 św.       63 św.
trend       0.4986   -0.0028    0.4107%           —         —  ŻADEN nie pomaga       15 św.

[interpretacja] B_wymagane = C/(2p-1) — szerokość bariery, przy której wartość
oczekiwana transakcji przestaje być ujemna PRZY NIEZMIENIONEJ trafności. Implikowany
horyzont z przeskalowania ~sqrt(t). Jeśli przekracza NAJDŁUŻSZY zmierzony epizod
reżimu, to poszerzanie bariery jest niewykonalne przy tej definicji reżimu —
bariera i tak byłaby testowana poza reżimem, który uzasadnił wejście.
Gdy 2p-1 <= 0 (trend), ŻADNA szerokość nie pomaga: szersza bariera pogarsza wynik.

================================================================================================
BLOK 3 — przesiew kandydatów na regułę reżimu (kryterium dopuszczalności, 0 wariantów)
================================================================================================
Kryterium: mediana epizodu >= 12 świec (horyzont etykiety)
ORAZ udział reżimu >= 5% świec. Oba warunki definicyjne, żaden nie oceniany PnL-em.

reguła                           trend: med/udz     range: med/udz  dopuszczalna
obecna (0.7/0.3)                  2.0 /  0.53%      5.0 / 21.62%           nie
luźniejsza (0.5/0.5)              2.0 /  4.67%     10.0 / 45.67%           nie
luźniejsza (0.4/0.4)              2.0 /  5.50%      5.0 / 28.51%           nie
obecna + wygładzenie 12           7.0 /  0.08%     17.0 / 21.02%           nie
0.5/0.5 + wygładzenie 12          7.0 /  1.52%     39.0 / 46.90%           nie
0.5/0.5 + wygładzenie 48         10.0 /  0.05%     89.0 / 48.18%           nie

[interpretacja] Reguła niedopuszczalna NIE jest 'zła' — jest niespójna z targetem
o tym horyzoncie. Dopuszczalność to warunek KONIECZNY, by pomiar `p` cokolwiek
znaczył; nie jest warunkiem wystarczającym istnienia edge'u. Wybór reguły do testu
OOS to osobna runda i osobny wariant w księdze (Backlog Z7) — ten blok go NIE wybiera.
```
