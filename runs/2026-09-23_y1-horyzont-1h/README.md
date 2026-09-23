# Y1 — model kontrolny na interwale 1h: nowa baza, ten sam model (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-23: „wykonaj oba,
> a dla 2 sprawdź horyzont 1h oraz 1d". **NOWA SERIA Y1 (nowa BAZA DANYCH: świece 1h od
> 2021-01-01), licznik 1/1, STOP.** Wyniki na 1h NIE porównują się 1:1 z 4h (inna baza —
> wytyczna o licznikach); raportowane obok kontroli 4h jako odniesienie. Rachunek mierzalności
> policzony PRZED treningiem z własności danych 1h (bariera z ATR, próg, n z abstynencji 4h).
> Y1 i Y2 pre-rejestrowane razem, przed jakimkolwiek przebiegiem.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Do tej pory model decydował na świecach 4-godzinnych i trzymał pozycję najwyżej 12 godzin.
Sprawdzamy ten sam model (te same 4 cechy, ta sama bariera 1,5×ATR, to samo wejście i wyjście)
na świecach 1-godzinnych: decyzje co godzinę, pozycja najwyżej 3 godziny. Na tym horyzoncie
bariera jest wąska (ok. 1,1 % ceny), więc koszty ważą więcej: model musi trafiać w **53,6 %**
przypadków, żeby wyjść na zero (na 4h: 53,1 %). Za to próba jest ogromna — ok. 27 700
transakcji — więc odpowiedź będzie precyzyjna (±0,6 punktu). Oczekiwanie: jak na 4h,
trafność koło 50 % — ale to jest pomiar, nie założenie.

## ID testu

**Y1** — nowa baza (interwał 1h), własny licznik 1/1, STOP. Inne bariery, inne V, inne okna
walk-forward na 1h — warianty tej bazy, zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `y-horyzont-1h-1d` (wspólny dla Y1/Y2; rejestr skilli wspólny).
- Dane: natywne świece 1h BTC/USDT:USDT (binanceusdm) pobrane 2026-09-23 od 2020-12-01 (warm-up)
  do 2026-07-01 → cache `BTC-USDT-USDT_1h_20201201T000000Z_20260701T000000Z.parquet`;
  `config/settings.yaml` → `timeframe_start_overrides["1h"] = 2020-12-01` (jedno miejsce);
  `fetch_window` nakłada zasadę 20 (od 2021-01-01): **48 168 świec 1h**.
- Model i pipeline: `REVERSION_FEATURES` (okna w ŚWIECACH: `rsi_14`, `*_zscore_20`,
  `return_lag_1` — natywnie per interwał, Z9), bez bramki reżimu, wagi klas `balanced`,
  V = 3 świece (3 h), bariera 1,5·ATR, wejście limit po close k = 1, pojedyncze wyjście,
  koszty z config, `candles_per_day = 24`, walk-forward **60/28/28 dni** (jak 4h: 1 440 świec
  treningu), seed `PRIMARY_SEED`. Model wypełnień (`FILL_MODEL_PATH`) jak w 4h — kalibrowany
  na 5m dla świec 4h; na 1h przybliżenie (zapisane jako ograniczenie).
- Skrypt: `backtest/run_horizon_y.py 1h` (`--moc` = tylko rachunek ex ante); komenda przy
  zamknięciu; na `runs/ZAMROZONE.txt`.

## Poprzedzające wyniki

- **Wniosek 46 / kontrola 4h (nowa baza):** p 49,58 % [48,39; 50,77], −0,107 % na transakcję,
  p* 53,64 %, abstynencja 40,4 %, n 6 789 — odniesienie (inna baza, nie porównanie 1:1).
- **C2.6 (stara baza, resample z 5m, V = 12 świec):** progi 5m 82,8 % → 1h 56,8 % → 4h 54,6 %
  przed modelem maker/taker; tam 1h było agregatem z 5m i miało V = 12 (12 h). Y1 to natywne 1h,
  V = 3 (3 h), model wykonania W1 — inna konstrukcja, nie powtórka.
- **Wniosek 67:** dokładanie cech nie wyprowadza modelu 4h ponad próg — Y1/Y2 zmieniają BAZĘ,
  nie cechy.
- **Wniosek 12:** Faza 0 nie wykazała nic o innych horyzontach po naprawach — Y1/Y2 to
  pierwsze pomiary innych interwałów na nowej metodologii.

## Pre-rejestracja

- **Hipoteza:** model kontrolny na 1h ma trafność powyżej progu opłacalności 1h. Mechanizm:
  ten sam co Faza 0 (mean-reversion krótkoterminowa: `rsi_14`, z-score ceny/wolumenu,
  `return_lag_1`) — na 1h reakcje są szybsze, ale koszt względem bariery wyższy.
- **DOKŁADNIE JEDNA zmienna wobec kontroli 4h:** interwał (1h). Wszystko inne bez zmian.
- **Przyrząd i kryterium (jedno ramię, m = 1):** POZYTYWNY `t_neff > 1,96` ORAZ `ci_low(p) > p*`;
  NEGATYWNY `t_neff < −1,96` przy `n ≥ required`; inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (zasada 18, z danych 1h, przed treningiem):** ATR(14)/close mediana 0,742 %
  (p10 0,353 %, p90 1,442 %) → bariera 1,5·ATR ≈ **1,112 %** ceny; C = 0,0808 % (ten sam model
  wykonania) → **próg ±B = 53,63 %**; OOS ≈ 46 728 świec → `expected_trades(46 728; 0,4038; 0,994)`
  = **27 692**; half-width **0,59 pp**; luka (0,56 − 0,5363) = +2,37 pp > 0,59 → **MIERZALNA**.
  Abstynencja 4h jako założenie ex ante — ex post raportowana.
- **Oczekiwanie zapisane z góry:** trafność ~50 % (jak na wszystkich dotychczasowych bazach);
  przy n ≈ 27 700 wynik będzie rozstrzygnięty NEGATYWNIE z ogromnym zapasem, chyba że 1h
  faktycznie niesie sygnał ≥ 53,6 %.
- **Kontekst multiple testing:** dwie bazy naraz (Y1, Y2) + ~20 odczytów dnia.
- **Czego runda NIE robi:** nie stroi V ani bariery pod 1h; nie zmienia cech; nie filtruje
  godzin/dni tygodnia; nie łączy z 4h.

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
