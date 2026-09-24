# HC1 — cykl halvingowy BTC (opisowo) (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed wynikiem).** Runda opisowa, 0 wariantów, bez werdyktu.

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

_(sekcje poniżej po przebiegu)_
