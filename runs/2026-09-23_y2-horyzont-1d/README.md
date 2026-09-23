# Y2 — model kontrolny na interwale 1d: nowa baza, ten sam model, dłuższe okna (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-23: „wykonaj oba,
> a dla 2 sprawdź horyzont 1h oraz 1d". **NOWA SERIA Y2 (nowa BAZA DANYCH: świece 1d od
> 2021-01-01), licznik 1/1, STOP.** Rachunek mierzalności PRZED treningiem z danych 1d.
> Y1 i Y2 pre-rejestrowane razem, przed jakimkolwiek przebiegiem.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Ten sam model co zawsze, ale na świecach dziennych: decyzja raz dziennie, pozycja najwyżej
3 dni, bariera 1,5×ATR — na dziennych świecach to ok. 6 % ceny, więc koszty (0,08 %) prawie
nie ważą: próg opłacalności to tylko **50,7 %** trafności. Cena: mało obserwacji. Od 2021 mamy
2 007 dni, a po odjęciu pierwszego roku na trening zostaje ok. 1 640 dni, czyli ok. 970
transakcji. Rozdzielczość ±3,1 punktu — żeby uznać wynik za dodatni, trafność musiałaby
przekroczyć ok. 54 %. Okna uczenia są dłuższe (rok treningu, kwartał testu), bo 60 dni to
tylko 60 wierszy — model drzew nie ma się z czego uczyć.

## ID testu

**Y2** — nowa baza (interwał 1d), własny licznik 1/1, STOP. Inne okna walk-forward, V, bariery
na 1d — warianty tej bazy, zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `y-horyzont-1h-1d` (wspólny dla Y1/Y2).
- Dane: natywne świece 1d BTC/USDT:USDT (binanceusdm) pobrane 2026-09-23 od 2019-09-10 (warm-up)
  do 2026-07-01 → cache `BTC-USDT-USDT_1d_20190910T000000Z_20260701T000000Z.parquet`;
  `timeframe_start_overrides["1d"] = 2019-09-10`; `fetch_window` (zasada 20): **2 007 świec 1d**.
- Model i pipeline: jak Y1 (cechy, bariera, wejście, wyjście, koszty), `candles_per_day = 1`,
  V = 3 świece (3 dni), walk-forward **365/91/91 dni** (365 wierszy treningu ≈ 360 wierszy
  kontroli 4h; 60/28/28 dałoby 60 wierszy — parametr bazy dobrany PRZED danymi z liczby
  wierszy, nie strojony), seed `PRIMARY_SEED`. Model wypełnień jak w 4h (przybliżenie).
- Skrypt: `backtest/run_horizon_y.py 1d` (`--moc` = tylko rachunek ex ante); na `runs/ZAMROZONE.txt`.

## Poprzedzające wyniki

Jak Y1 (wniosek 46, C2.6, wniosek 67, wniosek 12). Dodatkowo **wniosek 19/23**: przy małym n
sygnał opłacalny może być niewidzialny — na 1d luka 5,3 pp wobec half-width 3,1 pp jest
wystarczająca dla „obietnicy podręcznika" (56 %), ale efekt rzędu 52 % (1,3 pp nad progiem)
byłby NIEWIDZIALNY — zapisane z góry jako granica przyrządu.

## Pre-rejestracja

- **Hipoteza:** model kontrolny na 1d ma trafność powyżej progu 1d (50,66 %). Mechanizm jak
  Faza 0 (mean-reversion), na horyzoncie dni — gdzie literatura (LTW 2022) widzi raczej
  momentum tygodniowe; prior niski, ale koszt względem bariery jest najniższy w projekcie.
- **DOKŁADNIE JEDNA zmienna wobec kontroli 4h:** interwał (1d) — z koniecznym dostosowaniem okien
  walk-forward do liczby wierszy (365/91/91), zapisanym tu jako część definicji bazy.
- **Przyrząd i kryterium (jedno ramię, m = 1):** jak Y1.
- **Mierzalność (zasada 18, z danych 1d, przed treningiem):** ATR(14)/close mediana 4,105 %
  (p10 2,611 %, p90 6,994 %) → bariera **6,157 %** ceny; C = 0,0808 % → **próg ±B = 50,66 %**;
  OOS ≈ 1 642 świece → `expected_trades(1 642; 0,4038; 0,994)` = **973**; half-width **3,14 pp**;
  luka +5,34 pp > 3,14 → **MIERZALNA** (dla 56 %; efekty < ~54 % niewidzialne).
- **Oczekiwanie zapisane z góry:** NIEROZSTRZYGNIĘTY najbardziej prawdopodobny (mała próba);
  NEGATYWNY wymaga `t_neff < −1,96` przy n ≥ required(0,50; 50,66 %) — przy tak niskim progu
  required jest DUŻE (guard może nie być spełniony → NIEROZSTRZYGNIĘTY nawet przy ujemnym t).
- **Kontekst multiple testing:** jak Y1.
- **Czego runda NIE robi:** nie stroi okien po wyniku; nie zmienia cech; nie filtruje dni.

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz y-horyzont-1h-1d`)_
