# S1b — S1 powtórzony po naprawie Z17b: wynik NIEROZSTRZYGALNY, hipoteza NIETESTOWALNA na 4h (2026-09-22)

## ID testu

**S1b** — powtórzenie S1 na naprawionym pipelinie. Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/Z17b-early-stopping-martwy`
- **Poprzedzający stan (master):** `d05445d`
- **Komenda:** ten sam przebieg co `backtest/run_single_regime_4h.py`, z naprawionym
  `train_regime_model` (`raw_output.txt`)
- **Zmiany:** `agents/ml_optimizer.py` — `n_val = max(MIN_VALIDATION_ROWS, round(n·frac))`;
  `backtest/engine.py` — pole `early_stopping_used` w `folds_summary`.
- **Warianty:** **0** — naprawa poprawnościowa, nie nowy wariant. Kryterium sukcesu
  NIEZMIENIONE, pre-rejestrowane w Z5b.
- **Testy:** **251/251** (248 + 3 regresyjne na Z17b).

## Poprzedzające wyniki (zasada 14)

- **S1** (`runs/2026-09-22_s1-single-regime-4h/`) — ten sam eksperyment, wynik negatywny
  rozstrzygający: n=1 037, trafność 48,60%, kryterium przepadło o 9,04 pp.
- **Walidacja S1** (zasada 16a) wykryła, że **early stopping nie załączał się na 4h**:
  `n_val = round(n·0,2)` dawało medianę 21 < `MIN_VALIDATION_ROWS = 30`, więc **58 z 63
  foldów (92,1%) trenowało się bez early stoppingu**, do pełnych 200 rund boostingu.
  Naprawa Z17+Z21 była tam formalnie obecna, ale martwa.
- **Z19/Z5b** — rachunek mocy: klauzula nierozstrzygalności przy `n < 925`.

## Pre-deklaracja (zapisana PRZED uruchomieniem)

Naprawa mogła zadziałać **na korzyść hipotezy** (bez early stoppingu modele trenują do pełnych
200 rund, więc prawdopodobnie przeuczają się i zaniżają OOS), więc wymagała większej ostrożności
niż Z17. Zadeklarowano: **adopcja bezwarunkowa**, nowa liczba **zastępuje** S1 i nie jest z nim
porównywana jako „lepsza/gorsza", kryterium pozostaje pre-rejestrowane (`ci_low > 54,60%`),
klauzula nierozstrzygalności (`n < 925`) i reguła STOP obowiązują bez zmian.

## Wynik

**Naprawa zadziałała:** foldy z early stoppingiem **5/63 (7,9%) → 53/63 (84,1%)**.

Ale pociągnęła za sobą skutek, którego nie przewidziałem:

| miara | S1 (early stopping martwy) | **S1b (naprawiony)** |
|---|---|---|
| foldy z early stoppingiem | 5/63 (7,9%) | **53/63 (84,1%)** |
| abstynencja modelu | 2 582 / 3 642 (70,9%) | **3 297 / 3 642 (90,5%)** |
| **n transakcji** | 1 037 | **345** |
| trafność | 48,60% | 47,54% |
| 95% CI | [45,56%; 51,64%] | **[42,27%; 52,81%]** |
| pooled t (t_neff) | −2,24 (−1,74) | −1,32 (−1,02) |
| foldy z policzalnym Sharpe | 59 | 18 |

**Mechanizm:** early stopping zatrzymuje boosting wcześniej, więc model jest ostrożniejszy —
częściej przewiduje klasę „timeout" i nie zajmuje pozycji. Abstynencja rośnie z 70,9% do
**90,5%**, a liczba transakcji spada trzykrotnie.

## WERDYKT: NIEROZSTRZYGALNY (klauzula pre-rejestrowana)

`n = 345 < 925` → **klauzula nierozstrzygalności z Z5b wchodzi w grę.** Zgodnie z tym, co
zadeklarowano przed uruchomieniem, **wyniku nie interpretuję w żadną stronę** — ani jako
potwierdzenia, ani jako zaprzeczenia hipotezy. Trafność 47,54% przy CI [42,27%; 52,81%] jest
nieodróżnialna od rzutu monetą i od progu jednocześnie.

## Co to robi z werdyktem S1

Trzeba to powiedzieć wprost: **S1 orzekał na pipelinie, o którym teraz wiemy, że miał wadę.**
Werdykt S1 („kryterium niespełnione, przepada o 9,04 pp") był poprawny **względem tego, co
faktycznie policzono**, ale policzono to modelami trenowanymi bez early stoppingu w 92% foldów.

Po naprawie **nie da się tego rozstrzygnąć** przy dostępnych danych:

| | |
|---|---|
| transakcji na rok (po naprawie) | 50,7 |
| lat potrzebnych na `n = 925` | **18,2** |
| dostępne (BTC perp na Binance od 2019-09) | 6,8 |
| **brakuje** | **11,4 lat danych, których nie ma** |

**Wniosek: hipoteza jednoreżimowa 4h jest przy poprawnym pipelinie NIETESTOWALNA na dostępnych
danych.** To inny stan niż „sfalsyfikowana" — i uczciwość wymaga tego rozróżnienia.

## Co na plus (+)

- **Wada wykryta w walidacji została naprawiona i naprawa jest zweryfikowana liczbowo**
  (7,9% → 84,1% foldów z early stoppingiem), a nie tylko zadeklarowana w kodzie.
- **Klauzula nierozstrzygalności zadziałała dokładnie tak, jak miała.** Bez niej pokusa
  odczytania „47,54%, czyli jeszcze gorzej niż w S1" byłaby duża — a to odczyt bezpodstawny
  przy `n=345`.
- **Pole `early_stopping_used` w `folds_summary`** sprawia, że ten typ wady nigdy więcej nie
  będzie niewidoczny. Wcześniej fakt, że naprawa jest martwa, dało się wykryć wyłącznie
  instrumentując kod ręcznie.
- Na dużych foldach `max()` jest operacją pustą, więc **wyniki na 5m pozostają nienaruszone** —
  potwierdzone testem regresyjnym.

## Co na minus (−)

- **Runda nie rozstrzyga niczego** i zostawia projekt w gorszym stanie informacyjnym niż przed
  nią: wcześniej mieliśmy negatywny werdykt na wadliwym pipelinie, teraz mamy brak werdyktu
  na poprawnym.
- **Nie przewidziałem, że naprawa zetnie próbę trzykrotnie.** Rachunek mocy z Z19/Z5b zakładał
  liczbę transakcji zmierzoną na pipelinie z martwym early stoppingiem, więc margines 4,3×
  był fikcją — realnie mamy 0,37× wymaganej próby.
- Nie wiem, czy wzrost abstynencji do 90,5% to zdrowa ostrożność modelu, czy artefakt zbyt
  agresywnego early stoppingu przy 30 wierszach walidacji. Rozstrzygnięcie wymagałoby
  zagnieżdżonego walk-forward — poza zakresem Fazy 0.
- `MIN_VALIDATION_ROWS = 30` i `validation_fraction = 0.2` pozostają wartościami startowymi,
  nieskalibrowanymi.

## Wniosek

Naprawa jest poprawna i zweryfikowana, ale odsłania, że **konfiguracja 4h/V=3/`range` nie daje
się zmierzyć przy poprawnym pipelinie i dostępnej historii** — brakuje 11,4 lat danych.
Hipoteza nie zostaje zrehabilitowana (nic w tych liczbach nie sugeruje edge'u: 47,54%, CI
obejmujące 50%), ale też **nie została uczciwie sfalsyfikowana na poprawnym pipelinie**.

## Rekomendacja

Reguła STOP dla serii jednoreżimowej **pozostaje aktywna** — nie testuję kolejnego `V`,
interwału ani reżimu. Ten wynik jest natomiast materiałem do decyzji **Z10**, i zmienia jej
treść: dokument zamykający Fazę 0 musi mówić „hipoteza wyczerpana i częściowo nietestowalna
przy dostępnych danych", a nie „sfalsyfikowana", bo to drugie byłoby mocniejsze, niż liczby
pozwalają.

## Pełny surowy output

```
==========================================================================================
S1b — ten sam eksperyment po naprawie Z17b (early stopping faktycznie zalacza sie)
==========================================================================================
foldy aktywne z early stoppingiem: 53/63 (84.1%)
  [przed naprawa bylo 5/63 = 7,9%]
abstynencja modelu: 3297 z 3642 ocenionych swiec

{'classification': 'NO-GO', 'n_valid_folds': 18, 'n_total_folds': 85, 'fraction_above_threshold': 0.2777777777777778, 'fraction_le_zero': 0.6111111111111112, 'fraction_positive_sign': 0.3888888888888889, 'mean_sharpe': -0.811894939800959}
regime  n_trades  mean_return  std_return  sharpe_per_trade    t_stat      n_eff  t_stat_neff
 range       345    -0.000167    0.002354          -0.07084 -1.315802 207.606603    -1.020709
regime  n_trades  hit_rate    z_stat   ci_low  ci_high  share_timeout  hit_rate_barrier  hit_rate_timeout  barrier_pct  cost_pct  break_even_p    margin
 range       345  0.475362 -0.915249 0.422666 0.528059            0.6          0.543478          0.429952     0.014276  0.000767      0.526862 -0.051499

==========================================================================================
WERDYKT wobec PRE-REJESTROWANEGO kryterium (Z5b, niezmienione)
==========================================================================================
  n                     = 345
  trafnosc              = 47.54%
  95% CI                = [42.27%; 52.81%]
  prog pre-rejestrowany = 54.60%
  trzeba bylo zmierzyc  = 59.88%
  >>> NIEROZSTRZYGALNE: n=345 < 925
```
