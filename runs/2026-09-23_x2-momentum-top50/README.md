# X2 — momentum przekrojowe na szerszym koszyku (top-50, nogi po 10): większa próba, nie wariant (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-23 („wykonaj oba"
> po rekomendacji X1: rozstrzygnięcie tylko większą PRÓBĄ). **NOWA SERIA X2, własny licznik
> 1/1, STOP.** Ta sama reguła co X1 (sygnał 28 dni, trzymanie 7 dni, kwantyle 20 %, koszty,
> funding) — zmienia się WYŁĄCZNIE szerokość uniwersum (top-50 zamiast top-20, nogi po 10).
> Rachunek mocy z symulacji losowych rankingów PRZED wynikiem (`moc.txt`), z korektą ×1,3
> (wniosek 65). W katalogu rodzin: drugi wariant rodziny B1 (licznik rodziny 2) — uruchomiony
> na mocy decyzji użytkownika, nie z własnej inicjatywy (wniosek 49).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

X1 dało +22 % rocznie, ale z przedziałem od −5 do +49 % — za szeroki, żeby cokolwiek
rozstrzygnąć. Szerszy koszyk (50 monet zamiast 20, po 10 w każdej nodze zamiast 5) uśrednia
więcej niezależnych ruchów, więc szum powinien zmaleć o ok. 30 %. Cena: monety z miejsc 21–50
są mniej płynne (droższe w handlu, trudniej je shortować, częściej znikają z giełdy). Reguła
pozostaje ta sama — to test, czy efekt z X1 widać wyraźniej na większej próbie, nie nowy pomysł.

## ID testu

**X2** — seria X2 (rodzina B1, drugi wariant rodziny). **Licznik 1/1, STOP.** Po X2 rodzina B1
ma dwa odczyty (X1 top-20, X2 top-50); nie wolno ich sumować ani wybierać lepszego — raportowane
obok siebie. Kolejne szerokości (top-100), inne kwantyle, okna, trzymanie — zakazane bez decyzji.

## Metadane

- Branch: `x2-momentum-top50` (od `master` @ `a7af7da`).
- Dane: uniwersum P2 (281 symboli, wycofane zostają), funding per symbol; okno `2021-05-01 →
  2026-07-01` — **start w maju 2021, bo wcześniej brakuje 50 kandydatów** (luty–kwiecień 2021:
  41–46 symboli z ≥ 30 notowaniami w oknie obrotu; `monthly_members` fail loud). X1 zaczynało
  2021-02-01: X2 ma o 3 miesiące krótszą próbę (62 koszyki zamiast 65).
- Uniwersum point-in-time: `monthly_members(top_n=50)` (30 dni obrotu PRZED miesiącem).
- Koszty: 0,07 % na jednostkę obrotu (taker + poślizg 0,02 % — **dla monet 21–50 poślizg jest
  optymistyczny**, zapisane); funding per symbol (long płaci, short otrzymuje).
- Kod: `backtest/xs_momentum.py` bez zmian (parametry `leg_size`, `top_n`); skrypt
  `backtest/run_xs_momentum_x2.py` (kopia X1 z trzema stałymi; X1 zamrożony). Komendy przy
  zamknięciu; skrypt na `runs/ZAMROZONE.txt`.

## Poprzedzające wyniki

- **X1** (wniosek 64): +0,060 %/dzień [−0,015; +0,135], +22 %/rok netto, t 1,58, dodatni
  w 6/6 lat, 2025 = 52 % sumy, IC +0,028 [−0,007; +0,064], korelacja z BTC −0,13, obrót
  0,87/formowanie; rozdzielczość 27 %/rok; rozstrzygnięcie tylko większą próbą.
- **Wniosek 65**: symulacja losowych rankingów zaniża szum ~30 % (nogi z sygnału są bardziej
  zmienne) → half-width × 1,3.
- **R1** (wniosek 57): ruchy względne wewnątrz miesiąca trwają (mechanizm); **P2/wniosek 40**:
  przekrój nie mnoży próby liniowo (korelacja 0,47) — 50 monet to nie 2,5× informacji z 20.
- **families.md B1**: pułapki szerszego uniwersum — płynność ogona, dostępność shorta,
  wolumen wycofanych.

## Pre-rejestracja

- **Hipoteza:** ta sama co X1 (momentum względne 4 tygodnie → 1 tydzień), mierzona na szerszym
  koszyku; mechanizm bez zmian (przegrani tracą dalej — X1: efekt z nogi short).
- **DOKŁADNIE JEDNA zmienna wobec X1:** szerokość (top-50, nogi po 10). Kwantyl 20 % zachowany.
- **Przyrząd i kryterium:** jak X1 — dzienny szereg netto, CI z N_eff, POZYTYWNY `t_neff > 1,96`,
  NEGATYWNY `ci_high < 0`, inaczej NIEROZSTRZYGNIĘTY; wtórnie IC, korelacja z BTC, per rok,
  dni z nogą < 10 aktywnych (wycofania).
- **Oczekiwania zapisane z góry:** (a) szum nogi ~√2 mniejszy → half-width ~15–20 %/rok
  (po korekcie ×1,3); (b) jeśli efekt X1 jest realny i podobny na monetach 21–50, punktowo
  +15…+25 %/rok i t ≈ 2–3; (c) jeśli efekt mieszka tylko w memecoinach top-20, X2 rozcieńczy
  go — spadek punktowy poniżej X1; (d) koszty realnie wyższe niż w modelu.
- **Odczyt łączny X1 + X2 (zapisany PRZED X2):** dwa odczyty rodziny B1 raportowane obok siebie;
  „hipoteza z poparciem" tylko gdy oba punktowo dodatnie i X2 ma t_neff > 1,96; jeśli X2
  NIEROZSTRZYGNIĘTY z punktem dodatnim — rodzina zostaje „z poparciem, bez dowodu"; jeśli X2
  ujemny punktowo — X1 traktowany jako prawdopodobny fałszywy pozytyw (2025).
- **Rachunek mocy (zasada 18):** `py -m backtest.run_xs_momentum_x2 --moc 100` PRZED przebiegiem;
  liczby niżej; MIERZALNA, jeśli half-width × 1,3 < obietnica literatury (52 %/rok) — i osobno
  zapisane, czy < punkt X1 (22 %/rok), bo to jest realny cel rundy.

### Rachunek mocy — z symulacji, przed wynikiem (`moc.txt`)

`py -m backtest.run_xs_momentum_x2 --moc 100` (312 s): 100 losowych par nóg (10 + 10) spośród
członków z sygnałem, ta sama maszyneria, seed 0 — bez patrzenia na prawdziwy sygnał.

| wielkość | X2 (top-50) | X1 (top-20, dla porównania) |
|---|---|---|
| dni / formowań / koszyków / symboli | **1 886** / 270 / 62 / 218 | 1 975 / 283 / 65 / 119 |
| pod H0: koszt obrotu | 0,0163 %/dzień = **5,94 %/rok** | 5,62 %/rok |
| sd dzienna netto (typowa) | **1,108 %** | 1,302 % |
| empiryczne se średniej pod H0 | 0,0245 %/dzień | 0,0296 %/dzień |
| half-width 95 % | **17,5 %/rok** | 21,2 %/rok |
| half-width × 1,3 (wniosek 65) | **22,8 %/rok** | 27,3 % ex post |

**Werdykt mierzalności:** obietnica literatury (52 %/rok) = 2,3× skorygowanej rozdzielczości →
**MIERZALNA**. **Punkt X1 (22 %/rok) leży dokładnie na granicy rozdzielczości** (22,8 %): jeśli
prawdziwy efekt na top-50 jest taki jak punkt X1, oczekiwane t ≈ 1,9 — wynik może wyjść
zarówno POZYTYWNY, jak i NIEROZSTRZYGNIĘTY, i to zapisujemy z góry. Szum zmalał o 17 %
(1,108 vs 1,302 %), nie o 30 % — 50 monet to nie 2,5× informacji z 20 (wniosek 40).

### Czego runda NIE robi

Nie zmienia sygnału, trzymania, kwantyli ani kosztów; nie filtruje monet po płynności po
wyniku; nie sumuje X1 z X2; nie odwraca znaku.

---

_(sekcje poniżej po przebiegu)_

## Wynik

_(po przebiegu)_

## Co na plus (+) / Co na minus (−)

_(po przebiegu)_

## Walidacja (zasada 16a)

_(po przebiegu)_

## Przegląd diffu (zasada 16c)

_(po przebiegu)_

## Wniosek

_(po przebiegu)_

## Rekomendacja

_(po przebiegu)_

## Użyte skille

_(po przebiegu — z `py tools/skill_audit.py raport --galaz x2-momentum-top50`)_
