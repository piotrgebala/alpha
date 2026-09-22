# Z5b — pełna historia 4h + wybór specyfikacji: PRE-REJESTRACJA eksperymentu (2026-09-22)

## ID testu

**Z5b** (Backlog II) — patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/Z5b-long-history-4h`
- **Poprzedzający stan (master):** `ccc376a` (Z19).
- **Komendy:** `py -m data.fetch_ohlcv`, `py -m backtest.diagnose_statistical_power`
- **Zmiany:** `data/fetch_ohlcv.py` — `timeframe_start_overrides` (per-interwałowy start);
  `config/settings.yaml` — override 4h na 2019-09-10; `backtest/diagnose_timeframe_geometry.py`
  — `_load` respektuje override; `backtest/diagnose_statistical_power.py` — `WALK_FORWARD`
  skalowane per interwał.
- **Nowe dane (trwały cache):** `BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet`
  — **14 916 świec, 6,8 roku (2019-09-10 → 2026-06-30), zero dziur.**
- **Warianty hipotezy: 0** (pozyskanie danych + wybór specyfikacji; eksperyment NIE uruchomiony).
- **Testy:** 242/242 (bez zmian — zmiany dotyczą skryptów fetch/diagnostyki).

## Dlaczego pełna historia 4h — i dlaczego to NIE jest „więcej danych = lepiej"

Audyt odrzucił Z5b jako „nie domyka żadnego członu". Na 5m to prawda: mamy tam 7 043
transakcje przy progu 82,81% — więcej danych niczego nie zmieni, bo problemem jest próg,
nie próba. **Na 4h jest odwrotnie**: próg jest najniższy w projekcie, a wiążącym
ograniczeniem jest liczebność próby (Z19: 1 551 świec `range` wobec wymaganych 2 608).
Dłuższa historia adresuje więc **konkretne, zmierzone ograniczenie**, a nie ogólną intuicję.

Dodatkowo okna walk-forward są zdefiniowane w DNIACH (60/14/14), więc na 4h dawały 84 świece
testowe na fold (~22 `range`) — poniżej `MIN_TRAIN_ROWS=30`, czyli foldy byłyby pomijane.
To artefakt jednostek, nie właściwość rynku, więc okno testowe na 4h rośnie do 28 dni
(168 świec, ~44 `range`). Okno treningowe zostaje 60 dni (360 świec, ~94 `range`).

## Wynik 1 — wykonalność po wydłużeniu historii

| interwał | lat | okno test | reżim | świec `range` | n (górne ogr.) | świec/fold | wykonalne? |
|---|---|---|---|---|---|---|---|
| 5m | 3,0 | 14 | `range` | 66 996 | 62 105 | 862,6 | tak (próg 83,20% — absurd) |
| 1h | 3,0 | 14 | `range` | 6 042 | 5 600 | 77,8 | tak (próg 58,08%) |
| **4h** | **6,8** | **28** | **`range`** | **4 212** | **4 076** | **48,0** | **TAK** |
| 4h | 6,8 | 28 | `trend` | 85 | 82 | 1,0 | nie |

4h przeszło z „niewykonalne" na „wykonalne" — obie przyczyny usunięte (foldy 21,5 → 48,0;
próba 1 551 → 4 076). `trend` pozostaje niewykonalny na każdym interwale, zgodnie z Z16.

## Wynik 2 — konflikt: spójność kontra ekonomia (nowy pomiar)

Z9 rekomendował `V = 3`, bo to jedyny horyzont, przy którym `range` jest spójny. Ale
krótszy horyzont oznacza, że cena **nie zdąża** dotrzeć do bariery — transakcja kończy się
timeoutem po węższym ruchu. Efektywne `B` spada, a próg opłacalności **rośnie**. Zmierzone:

**4h, reżim `range`:**

| V | timeouty | efektywne B (mediana) | break-even | trzeba zmierzyć | spójne? |
|---|---|---|---|---|---|
| **3** | **60,8%** | **0,9779%** | **54,60%** | **56,15%** | **tak (70,2%)** |
| 6 | 34,4% | 1,5181% | 52,96% | 54,51% | nie (44,5%) |
| 12 | 10,7% | 1,8224% | 52,47% | 54,02% | nie (19,5%) |

**1h, reżim `range`:**

| V | timeouty | efektywne B | break-even | trzeba zmierzyć | spójne? |
|---|---|---|---|---|---|
| 3 | 63,7% | 0,3067% | 64,67% | 65,97% | tak (71,3%) |
| 12 | 17,9% | 0,5934% | 57,58% | 58,88% | nie (18,9%) |

**To koryguje liczbę z Z19.** Raportowałem tam próg 52,30% dla 4h — zawyżony optymistycznie,
bo liczony z `B = 1,5 × ATR` przy założeniu, że każda transakcja trafia barierę. Z realnym
udziałem timeoutów przy `V = 3` próg wynosi **54,60%**.

## Wybór specyfikacji — i jego uzasadnienie

**Wybieram `V = 3`** mimo wyższego progu (56,15% vs 54,02% przy `V = 12`).

Uzasadnienie: **spójność jest wymogiem poprawności, nie preferencją**. Pomiar `p` na sygnale,
którego bramka trwa krócej niż horyzont etykiety, to dokładnie to, co unieważniło wszystkie
wcześniejsze pomiary (Z16: w `trend` tylko 0,49% świec miało etykietę opisującą ruch wewnątrz
własnego reżimu). Wybranie `V = 12` dla niższego progu byłoby kupowaniem lepszej liczby za
cenę powrotu do znanego błędu — i dokładnie tym rodzajem decyzji, przed którym chroni
pre-rejestracja.

Moc przy tym wyborze: `n` ≤ 4 001, wymagane **925** (próg 54,60% wobec 50%) — **margines 4,3×**.
Paradoksalnie wyższy próg ułatwia wykrycie, bo efekt do odróżnienia od 50% jest większy.

## PRE-REJESTRACJA — eksperyment do uruchomienia w następnej rundzie

Zapisane **przed** uruchomieniem czegokolwiek, zgodnie z CLAUDE.md zasadami 1 i 4.

- **Hipoteza:** model osiąga trafność kierunku przekraczającą próg opłacalności w reżimie
  `range` na świecach 4h przy spójnym horyzoncie etykiety.
- **Konfiguracja (zamrożona):** natywne świece 4h, historia 2019-09-10 → 2026-07-01,
  reżim `range` (jeden, bez `trend` — Z16 wykazał, że jest niewykonalny), `V = 3`,
  `ATR_MULTIPLIER = 1.5` (bez zmian, CLAUDE.md zasada 3), walk-forward 60/28/28 dni,
  model kosztów `maker_limit` (C2.12), `validation_fraction = 0.2` i `embargo_candles = V`
  (Z17+Z21), seed 42.
- **KRYTERIUM SUKCESU:** dolny kraniec 95% CI trafności kierunku **> 54,60%**, czyli
  zmierzona trafność **≥ 56,15%**.
- **KLAUZULA NIEROZSTRZYGALNOŚCI:** jeśli realne `n` < **925**, wynik ogłaszam
  **nierozstrzygalnym** niezależnie od wartości `p` — bez interpretowania go jako przesłanki
  w którąkolwiek stronę.
- **REGUŁA STOP:** wynik negatywny = koniec tej linii hipotezy. Nie testuję kolejnego `V`,
  kolejnego interwału ani kolejnego reżimu po zobaczeniu wyniku.
- **Koszt:** 1 wariant w nowej serii (architektura jednoreżimowa to NOWA hipoteza wobec
  dwureżimowej z docs/rag/01 — własny licznik, zaczyna się od 1).

## Co na minus (−)

- Konfiguracja zmienia naraz interwał, historię, horyzont, okna walk-forward i liczbę
  reżimów. To **nowa specyfikacja**, nie wariant obecnej — ale oznacza, że wynik negatywny
  nie wskaże, **który** element zawiódł. Świadomy kompromis: testowanie ich pojedynczo
  jest niewykonalne (każdy osobno jest niewykonalny statystycznie, co pokazał Z19).
- `n` ≤ 4 001 to górne ograniczenie; realne będzie niższe po bramce kosztowej i świecach
  bez sygnału kierunkowego. Stąd jawna klauzula nierozstrzygalności.
- Rachunek mocy zakłada niezależność transakcji; przy nakładających się oknach etykiet
  `N_eff` jest mniejsze, więc realna moc jest niższa niż 4,3× (o ile — pokaże `N_eff`
  w raporcie z przebiegu).
- 6,8 roku obejmuje bardzo różne reżimy rynkowe (COVID 2020, hossa 2021, bessa 2022,
  ETF 2024). Uśrednienie po nich może maskować niestabilność — per-fold rozbicie to pokaże.

## Wniosek

Pełna historia 4h pobrana i odłożona trwale. Konfiguracja **4h / `range` / `V = 3`** jest
pierwszą w projekcie, która jest **jednocześnie**: spójna specyfikacyjnie (70,2% świec
z pełnym oknem etykiety wewnątrz reżimu), wykonalna statystycznie (margines mocy 4,3×)
i o realistycznym progu (56,15%).

Eksperyment jest pre-zarejestrowany i **nie został uruchomiony** w tej rundzie — celowo,
żeby wybór specyfikacji był zapisany przed zobaczeniem jakiegokolwiek wyniku.

## Pełny surowy output

```
--- wykonalnosc po wydluzeniu historii ---
====================================================================================================
Z19 — czy eksperyment na grubszym interwale może cokolwiek rozstrzygnąć?
====================================================================================================
koszt C = 0.0900%  |  walk-forward 60/14/14 dni  |  MIN_TRAIN_ROWS = 30

interwał  lat  okno test reżim  świec reżimu  n (górne ogr.)  na fold fold >= 30? break_even trzeba zmierzyć  n dla mocy 80% moc wystarcza?
      5m  3.0         14 range         66996           62105    862.6         tak     82.81%           83.2%              16            tak
      5m  3.0         14 trend          1636            1516     21.1         NIE     60.96%          63.47%             161            tak
      1h  3.0         14 range          6042            5600     77.8         tak     56.77%          58.08%             425            tak
      1h  3.0         14 trend            96              88      1.2         NIE     53.44%          63.89%            1652            NIE
      4h  6.8         28 range          4212            4076     48.0         tak      52.3%          53.84%            3700            tak
      4h  6.8         28 trend            85              82      1.0         NIE     51.27%           62.1%           12079            NIE

[legenda]
  n (górne ogr.)  - wszystkie świece reżimu w oknach testowych; REALNE n będzie MNIEJSZE
                    (odpadają brak sygnału, bramka kosztowa, foldy < MIN_TRAIN_ROWS)
  na fold         - średnio świec reżimu na jeden fold testowy; poniżej MIN_TRAIN_ROWS
                    fold jest POMIJANY przez backtest.engine
  trzeba zmierzyć - trafność, przy której DOLNY kraniec 95% CI przekracza break_even,
                    czyli minimum, by uczciwie orzec rentowność
  n dla mocy 80%  - liczba transakcji potrzebna, by odróżnić break_even od 50%

====================================================================================================
WNIOSEK — wykonalność per konfiguracja
====================================================================================================
  5m  range  -> WYKONALNE
      trzeba zmierzyć trafność >= 83.20% (break-even 82.81%)
  5m  trend  -> NIEWYKONALNE: foldy za małe (21.1 < 30 świec/fold)
      trzeba zmierzyć trafność >= 63.47% (break-even 60.96%)
  1h  range  -> WYKONALNE
      trzeba zmierzyć trafność >= 58.08% (break-even 56.77%)
  1h  trend  -> NIEWYKONALNE: foldy za małe (1.2 < 30 świec/fold); za mała próba (n<=88 vs wymagane 1652)
      trzeba zmierzyć trafność >= 63.89% (break-even 53.44%)
  4h  range  -> WYKONALNE
      trzeba zmierzyć trafność >= 53.84% (break-even 52.30%)
  4h  trend  -> NIEWYKONALNE: foldy za małe (1.0 < 30 świec/fold); za mała próba (n<=82 vs wymagane 12079)
      trzeba zmierzyć trafność >= 62.10% (break-even 51.27%)

--- konflikt spojnosc vs ekonomia per horyzont ---
koszt C = 0.0900%

==============================================================================================
1h — reżim range: 6042 świec, 26304 łącznie
==============================================================================================
 horizon_candles  median_length  share_windows_inside  coherent
               3            4.0              0.712512      True
               6            4.0              0.448361     False
              12            4.0              0.188679     False

  V  timeout%  |ruch| med   B_efekt  break-even  trzeba zmierz.
  3     63.7%     0.3067%   0.3067%      64.67%          65.97%
  6     39.2%     0.4869%   0.4869%      59.24%          60.54%
 12     17.9%     0.5934%   0.5934%      57.58%          58.88%

==============================================================================================
4h — reżim range: 4212 świec, 14916 łącznie
==============================================================================================
 horizon_candles  median_length  share_windows_inside  coherent
               3            3.0              0.701804      True
               6            3.0              0.445157     False
              12            3.0              0.195394     False

  V  timeout%  |ruch| med   B_efekt  break-even  trzeba zmierz.
  3     60.8%     0.9779%   0.9779%      54.60%          56.15%
  6     34.4%     1.5181%   1.5181%      52.96%          54.51%
 12     10.7%     1.8224%   1.8224%      52.47%          54.02%

```
