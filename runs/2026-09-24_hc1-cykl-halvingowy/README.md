# HC1 — cykl halvingowy BTC (opisowo) (2026-09-24)

> **STATUS: ZAMKNIĘTA (opisowo).** We wszystkich 3 cyklach BTC rósł przez pierwsze 18 miesięcy po
> halvingu (9/9 faz dodatnich), a w miesiącach 18–24 spadał za każdym razem (0/3; −31 do −59 %).
> Miesiące 24–30: 1/4 dodatnie, a reguła trendu traciła w tej fazie w każdym cyklu (0/4). Dziś: 29,1
> miesiąca od halvingu 2024 (koniec fazy 24–30). Trzy cykle to trzy obserwacje — opis, nie dowód.
> Pre-rejestracja w commicie przed wynikiem. Walidacja: **READY (Caveats)**; przegląd: **Approve**.
> Poprzednio: **PRE-REJESTRACJA (przed wynikiem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Użytkownik: „czy brałeś pod uwagę cykliczność BTC?”. Co ok. 4 lata nagroda za wydobycie BTC spada
o połowę (halving), a historycznie szczyty cen przychodziły 12–18 miesięcy później. Opisujemy, jak
BTC i nasza reguła trendu zachowywały się w kolejnych fazach cyklu. To opis, nie dowód: od 2014
mamy ok. 3 pełne cykle, czyli 3 obserwacje.

## ID testu

HC1 — opis (bez licznika wariantów); może posłużyć najwyżej jako zasada ryzyka (np. mniejsza dźwignia
w fazie historycznych bess), nie jako sygnał — i tylko decyzją użytkownika.

## Metadane

- Branch `wf1-okno-uczenia` (wspólny z WF1, jak Y1/Y2). Skrypt `backtest/run_halving_cycle_hc1.py`.
- Dane: FRED `CBBTCUSD` (Coinbase, dziennie) 2014-12-01 → 2026-09-23, 35 braków (przeniesienie
  ceny). **Wyjątek od zasady 20** zatwierdzony przez użytkownika 2026-09-24 („Tak, opisowo”, dane od 2014).
- **Start opisu 2015-03-01 (ustalony przed wynikiem):** błąd notowań Coinbase 2015-01-13/14
  (260 → 120 → 204 USD) nie może wejść do sygnału 28 dni. Skoki 2017-07-20 (+27 %) i 2020-03-12
  (−37 %) są prawdziwe i zostają.

## Poprzedzające wyniki

- TS1 (wnioski 70, 82): trend na koszyku po korekcie +11 %/rok, nieistotny.
- TX1 (wniosek 84): trend działa na zwykłych rynkach 1990–2012, po 2013 zanika.
- Nigdy nie opisywano cyklu halvingowego.

## Pre-rejestracja

- **Fazy** = miesiące od ostatniego halvingu (2012-11-28, 2016-07-09, 2020-05-11, 2024-04-20):
  0–6, 6–12, 12–18, 18–24, 24–30, 30–36, 36–48.
- **Opisowo per cykl i faza:** zwrot BTC, największy spadek w fazie; średnio po cyklach: zwrot roczny,
  zmienność, liczba cykli z BTC > 0; reguła TS1 na samym BTC (7 faz tygodniowych, koszt 0,07 %,
  bez fundingu) w każdej fazie.
- **Czego NIE robimy:** żadnego testu istotności (n = 3–4 cykle), żadnego doboru faz po wyniku,
  żadnej reguły handlowej z tego opisu bez osobnej decyzji użytkownika.

## Wynik

`raw_output.txt`.

**BTC w fazie cyklu (zwrot w fazie / największy spadek w fazie):**

| miesiące od halvingu | cykl 2012 | cykl 2016 | cykl 2020 | cykl 2024 |
|---|---|---|---|---|
| 0–6 | — | +36 % / 21 % | +75 % / 18 % | +8 % / 25 % |
| 6–12 | — | +176 % / 28 % | +270 % / 25 % | +27 % / 28 % |
| 12–18 | — | +545 % / 35 % | +18 % / 40 % | +26 % / 15 % |
| **18–24** | — | **−59 % / 61 %** | **−57 % / 56 %** | **−31 % / 44 %** |
| **24–30** | −9 % / 26 % | **−40 % / 62 %** | **−39 % / 50 %** | +4 % / 29 % (w toku) |
| 30–36 | +53 % / 32 % | +214 % / 18 % | +54 % / 19 % | — |
| 36–48 | +87 % / 23 % | −30 % / 59 % | +136 % / 20 % | — |

**Średnio po cyklach** (średnia dzienna × 365 — przybliżenie tempa, nie zwrot roczny z procentem składanym):

| faza | cykli z BTC > 0 | reguła trendu na BTC (%/rok) | cykli z trendem > 0 |
|---|---|---|---|
| 0–6 | 3/3 | +29,6 % | 2/3 |
| 6–12 | 3/3 | +87,0 % | 3/3 |
| 12–18 | 3/3 | +54,5 % | 3/3 |
| **18–24** | **0/3** | +15,7 % | 2/3 |
| **24–30** | **1/4** | **−23,2 %** | **0/4** |
| 30–36 | 3/3 | +67,3 % | 2/3 |
| 36–48 | 2/3 | +28,6 % | 2/3 |

Trend TS1 na samym BTC w całym okresie 2015-03 → 2026-08: +35,9 %/rok (zmienność 36,5 %) — głównie
z lat 2015–2020 (inny rynek, patrz zasada 20).

## Co na plus (+) / Co na minus (−)

**(+)** Wzór jest bardzo powtarzalny w 3 cyklach: 18 miesięcy wzrostów, potem ~6–12 miesięcy spadków.
Reguła trendu w fazie spadków 18–24 mies. radziła sobie nieźle (przechodziła na short), ale w fazie
24–30 mies. (dno, rynek „piłuje”) traciła w każdym cyklu.
**(−)** Trzy obserwacje. Wzór jest powszechnie znany, więc rynek może go wyprzedzać; bieżący cykl 2024
był wyraźnie słabszy (+8/+27/+26 % zamiast setek procent) i spadek w 18–24 mies. płytszy (−31 %).
Brak cyklu 2012 przed 24. miesiącem (dane od 2014-12). Średnie %/rok w krótkich fazach to przybliżenie.

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY (Caveats)**: ceny na granicach faz odczytane wprost, poza silnikiem —
cykl 2020, 18–24 mies.: 66 968 → 30 962 USD = −54 % (tabela −57 %); cykl 2016, 12–18 mies.: +532 %
(tabela +545 %); różnice = definicja dnia granicznego. Błąd notowań 2015-01 wykluczony przed wynikiem.
Caveat: tylko 3 cykle. `data:statistical-analysis`: bez testów (n = 3–4); raportowane liczby cykli
dodatnich zamiast średnich z przedziałami. `engineering:code-review` — **Approve**: fazy liczone od
ostatniego halvingu, silnik TS1 bez zmian, przeniesienie ceny tylko wstecz.

## Wniosek

**Prostym językiem:** w każdym z trzech ostatnich cykli BTC przez półtora roku po halvingu rósł, a potem
przez pół roku do roku mocno spadał. Nasza reguła trendu w fazie spadków trochę zarabiała (grała na
spadki), ale w okresie dołka, 2–2,5 roku po halvingu, traciła za każdym razem, bo rynek kręcił się w
miejscu. Jesteśmy teraz właśnie na końcu tej fazy (29 miesięcy po halvingu 2024). Trzy powtórzenia to za
mało, żeby traktować to jak prawo — ale wystarczy, żeby traktować to jako **ostrzeżenie o ryzyku**.

## Rekomendacja

1. Nie budować reguły handlowej na cyklu (3 obserwacje).
2. Jako **zasada ryzyka — do decyzji użytkownika**: w fazie 18–30 mies. po halvingu mniejsza dźwignia
   w strategii trendu (np. połowa). Dziennik NIE zmienia reguł bez takiej decyzji (pre-rejestracja).
3. Faza 30–36 mies. zaczyna się ok. 2026-10-20.

## Użyte skille

Rejestr `runs/skille/wf1-okno-uczenia.jsonl` (wspólny z WF1): `clas5-runda` (pre-rejestracja przed
wynikiem, start po błędzie danych), `clas5-quant` (bez testów przy n = 3), `data:validate-data`,
`data:statistical-analysis`, `engineering:code-review`. Pominięte: `dataviz` (tabele), `data:explore-data`
(profil jednej serii zrobiony w sesji: 4 315 dni, 35 braków, 3 skoki > 25 %).
