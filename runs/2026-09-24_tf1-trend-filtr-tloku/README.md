# TF1 — trend tygodniowy z filtrem tłoku (funding) (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „sprawdź 3 nowe
> hipotezy” — kombinacja zaproponowana jako najsensowniejsza (trend + informacja o tłoku spoza
> wykresu). Seria TS ma STOP; to wariant TS1 dopuszczony decyzją użytkownika i liczony w
> **nowej serii TF, 1/1, STOP**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

TS1 gra long monety w trendzie wzrostowym i short w spadkowym. Pomysł: nie wchodź w long, gdy
wszyscy już są long z dźwignią i płacą za to wysoki funding (i odwrotnie dla shortów), bo taki
tłok zwykle kończy się falą likwidacji. Filtr wyłączyłby ok. 9 % pozycji. Porównujemy ten sam
portfel z filtrem i bez niego, dzień po dniu. Test zobaczy różnicę rzędu 5 % rocznie; mniejszej
nie odróżni od przypadku.

## ID testu

**TF1** — nowa seria TF, 1/1, STOP. Inne progi, okna fundingu, OI zamiast fundingu = warianty.

## Metadane

- Branch: `tf1-trend-filtr-tloku`. Silnik `backtest/ts_momentum.py` z hakiem `keep_fn` (CP1).
- Dane: jak TS1 (`data/raw/universe`, top-20 point-in-time, 2021-02 → 2026-06, funding realny).
- Skrypt: `backtest/run_crowding_tf1.py` (na `runs/ZAMROZONE.txt`), testy
  `tests/test_crowding_tf1.py` (2). Komendy: `PYTHONUTF8=1 py -m backtest.run_crowding_tf1 --moc`
  → `moc.txt`; `PYTHONUTF8=1 py -m backtest.run_crowding_tf1` → `raw_output.txt`.

## Poprzedzające wyniki

- **TS1 (wniosek 70):** +14,8 %/rok, t 1,76. **TR1:** na miejscach 21–50 +14,1 %/rok, korelacja
  z TS1 0,86 (pre-rejestracja `40d604a`; zamknięcie w toku).
- **F1 (wniosek 38):** funding jako cecha modelu 4h — zero. Tu inny horyzont (tydzień) i inna
  rola (filtr tłoku na pozycji trendu), nie predykcja kierunku.
- **Katalog, sekcja I:** overlay nie tworzy informacji, gdy działa na szumie; TS1 jest najlepszym
  sygnałem projektu, a filtr wnosi informację spoza cen (funding).

## Pre-rejestracja

- **Hipoteza:** zerowanie pozycji trendu po stronie przeładowanej lewarem poprawia wynik TS1.
- **Mechanizm:** tłok lewarowanych longów (wysoki dodatni funding) kończy się likwidacjami
  i odwróceniem; trend zostaje, ale jego koniec jest przewidywalny z kosztu lewara.
- **DOKŁADNIE JEDNA zmienna:** filtr: long zerowany, gdy suma fundingu z 7 dni (dzień t włącznie)
  > **0,63 %** (3 × bazowa stawka 0,01 %/8h × 21 rozliczeń); short zerowany, gdy < −0,63 %.
  Próg ABSOLUTNY z góry (masa punktowa fundingu, wniosek 15). N w wagach bez zmian.
- **Kryterium (jedno ramię):** różnica parowana dziennego zwrotu netto TF1 − TS1: POZYTYWNY, gdy
  t_neff > 1,96; NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (`moc.txt`, bez średniej):** wyzerowanych 9,3 % pozycji (członek × dzień);
  sd różnicy 6,13 %/rok; **half-width ±5,17 %/rok**. Oczekiwany efekt mechanizmu: uniknięcie
  części strat w końcówkach trendów ~3–6 %/rok → **MIERZALNA na granicy**; efekty < 5 %/rok
  niewidoczne — zapisane z góry.
- **Kontekst multiple testing:** ~29 odczytów w dwa dni.
- **Czego runda NIE robi:** nie stroi progu, nie zmienia okna fundingu, nie renormalizuje wag.

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz tf1-trend-filtr-tloku`)_
