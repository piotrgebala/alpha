# Z17+Z21 — przeciek early stopping i brak embargo: `p` było ZAWYŻONE (2026-09-22)

## ID testu

**Z17+Z21** (Backlog II) — patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/Z17-early-stopping-leak`
- **Poprzedzający stan (master):** `11f8b75` (Z16).
- **Komenda:** porównanie dwóch przebiegów `checkpoint_lib.run_and_summarize` na 3 latach
  (`validation_fraction=None, embargo_candles=0` vs `0.2 / 12`).
- **Zmiany:** `agents/ml_optimizer.py` — `validation_fraction`, `embargo_candles`,
  `best_iteration_or_last`, `DEFAULT_VALIDATION_FRACTION=0.2`, `MIN_VALIDATION_ROWS=30`;
  `backtest/engine.py` + `backtest/diagnose_range_signal.py` — guard na `best_iteration`,
  przewleczenie parametrów, **nowe wartości domyślne**; `config/settings.yaml` — sprostowanie
  komentarza, który opisywał buga jako decyzję.
- **Warianty hipotezy: 0** — naprawa błędu poprawnościowego, nie wariant. Warunek
  uczciwości zadeklarowany PRZED uruchomieniem: **adopcja bezwarunkowa** (przyjmujemy wynik
  także gorszy), a nowe `p` **zastępuje** C2.11–C2.13, nie jest z nimi porównywane jako
  „lepsze/gorsze".
- **Testy:** **226/226** (214 + 12).

## Na czym polegał błąd

`train_regime_model` wołało `xgb.train(..., evals=[(dtest, "test")], early_stopping_rounds=...)`,
czyli **liczba drzew była dobierana na foldzie OOS** — tym samym, na którym mierzymy wynik.
`predict_signal` używało potem `booster.best_iteration` pochodzącego z tego wyboru. Docstringi
(`ml_optimizer.py:25,63,102,147`) i `config/settings.yaml:48` opisywały to jako decyzję
projektową („na foldzie OOS (test), nigdy na train"), co utrwalało buga jako wybór.

**Dlaczego razem z Z21:** naprawa Z17 wycina walidację z ogona foldu treningowego — a to
dokładnie te wiersze, których etykieta triple-barrier sięga w okno testowe
(`test_start == train_end`, zero purge w całym repo). Walidacja byłaby więc skażona ruchem
z okresu testowego, czyli **Z17 bez Z21 nie naprawiałby niczego**. Oba dotyczą tej samej
granicy i muszą być jedną zmianą.

## Wynik — kierunek obciążenia potwierdzony: `p` było zawyżone

| miara | PRZED (przeciek) | **PO (naprawione)** | zmiana |
|---|---|---|---|
| Klasyfikacja | NO-GO | **NO-GO** | bez zmian |
| Foldy ważne | 54 / 144 | 54 / 144 | — |
| `fraction_le_zero` | 0,870 | **0,907** | gorzej |
| `range`: n | 7 155 | 7 043 | −112 |
| **`range`: hit_rate** | 51,07% | **50,38%** | **−0,69 pp** |
| **`range`: z_stat** | **+1,81** | **+0,63** | **kolaps** |
| `range`: margin | −15,52 pp | −16,32 pp | −0,8 pp |
| `trend`: n | 355 | 299 | −56 |
| `trend`: hit_rate | 49,86% | 50,84% | +0,98 pp |
| `trend`: z_stat | −0,05 | +0,29 | szum |
| `trend`: margin | −9,08 pp | −7,25 pp | +1,8 pp |
| `trend`: t_neff | −1,75 | −1,96 | — |

## Co na plus (+)

- **Przewidywany kierunek obciążenia potwierdzony ilościowo.** Audyt twierdził, że przeciek
  ZAWYŻA `p`; po naprawie `p` w `range` spadło o 0,69 pp. Predykcja postawiona przed
  pomiarem i trafiona — to podnosi zaufanie do reszty listy długów technicznych.
- **Najważniejszy skutek: z-stat w `range` zapadł się z +1,81 do +0,63.** W C2.12 zapisałem,
  że trafność „po raz pierwszy ociera się o istotność". To było **artefaktem przecieku**.
  Po naprawie żaden reżim nie zbliża się do istotności (+0,63 i +0,29).
- Test rozstrzygający: szpieg na `xgb.train` sprawdza, że walidacja ma 38 wierszy z ogona
  treningu, a nie 100 wierszy foldu testowego — rozmiary dobrane tak, by jednoznacznie
  odróżnić obie implementacje.
- Guard `best_iteration_or_last` odblokowuje wariant bez early stoppingu (xgboost ≥ 2.0
  podnosił `AttributeError` w 3 miejscach).
- Fold za mały na uczciwy podział trenuje teraz **bez** early stoppingu zamiast przeciekać
  — świadomie gorszy model, ale bez skażenia.

## Co na minus (−)

- **Naprawa oddala od GO, nie przybliża.** `fraction_le_zero` 0,870 → 0,907, margines
  w `range` −15,5 → −16,3 pp. To był oczekiwany koszt uczciwości, nie niespodzianka.
- `trend` poprawił się pozornie (margines −9,1 → −7,25 pp), ale przy n=299 i z=+0,29 to
  szum; dodatkowo Z16 pokazał, że ten reżim ma 0,49% świec ze spójną etykietą, więc jego
  liczby i tak są nieinterpretowalne.
- `embargo_candles=12` jest poprawne dla `VERTICAL_BARRIER_CANDLES=12`, ale przy dłuższym
  horyzoncie musi rosnąć razem z nim — dziś to dwa niezależne parametry, które trzeba
  pamiętać zsynchronizować (ten sam typ ryzyka co mnożnik ATR, CLAUDE.md zasada 3).
- `validation_fraction=0.2` to wartość startowa, nie kalibrowana. Kalibracja wymagałaby
  zagnieżdżonego walk-forward — poza zakresem Fazy 0.
- Wyniki C6–C2.13 pozostają policzone ze ścieżką przeciekającą. Nie przeliczam ich wstecz
  (byłoby to przepisywanie historii); ścieżka legacy zostaje wyłącznie do ich odtworzenia.

## Wniosek

Przeciek był realny i działał w przewidzianą stronę. Po jego usunięciu **żaden reżim nie
wykazuje trafności odróżnialnej od rzutu monetą**: `range` z=+0,63 (n=7 043), `trend`
z=+0,29 (n=299). Jedyny wynik, który w całym projekcie wyglądał na „bliski istotności"
(z=+1,81 w C2.12), okazał się artefaktem doboru liczby drzew na zbiorze testowym.

To jest teraz **najczystszy pomiar `p`, jaki projekt miał** — bez przecieku early stoppingu,
z embargo na granicy train/test, po realistycznych kosztach, na 3 latach danych. I pokazuje
brak edge'u kierunkowego.

## Rekomendacja

Zgodnie z kolejnością z Backlog II: pozostaje **Z18** (jedna definicja `p` — trzy
niekompatybilne w obiegu). Potem jedyny nietknięty pomiar merytoryczny: `p` na sygnale
**spójnym** (Z16 pokazał, że `range` da się uspójnić: mediana epizodu 5 → 39 świec przy
udziale 46,9%) i przy relacji B/C zmienionej przez grubszy interwał (Z9).

Trzeźwo: przy `B = 0,20%` i `C = 0,068%` próg opłacalności w `range` to **66,7%**, a mierzymy
50,4%. Uspójnienie i grubszy interwał mogą ten próg obniżyć (na 4h szacunkowo do ~55%),
ale muszą JEDNOCZEŚNIE podnieść `p` o kilkanaście punktów procentowych. Żaden dotychczasowy
pomiar nie wskazuje, że `p` w ogóle da się ruszyć.

## Pełny surowy output

```
[data] 315648 świec: 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] brak dziur.
==========================================================================================
PRZED Z17 (early stopping na OOS, bez embargo)
==========================================================================================
{'classification': 'NO-GO', 'n_valid_folds': 54, 'n_total_folds': 144, 'fraction_above_threshold': 0.09259259259259259, 'fraction_le_zero': 0.8703703703703703, 'fraction_positive_sign': 0.12962962962962962, 'mean_sharpe': -59.639681477704926}
regime  n_trades  hit_rate    z_stat   ci_low  ci_high  barrier_pct  cost_pct  break_even_p    margin
 range      7155  0.510692  1.808784 0.499109 0.522275     0.002031  0.000674      0.665873 -0.155181
 trend       355  0.498592 -0.053074 0.446579 0.550604     0.003834  0.000685      0.589387 -0.090796
regime  n_trades  mean_return  std_return  sharpe_per_trade     t_stat       n_eff  t_stat_neff
 range      7155    -0.000686    0.002500         -0.274276 -23.200278 2348.959930   -13.293097
 trend       355    -0.000432    0.002743         -0.157399  -2.965616  123.418175    -1.748600

==========================================================================================
PO Z17+Z21 (walidacja z ogona train, embargo=12)
==========================================================================================
{'classification': 'NO-GO', 'n_valid_folds': 54, 'n_total_folds': 144, 'fraction_above_threshold': 0.09259259259259259, 'fraction_le_zero': 0.9074074074074074, 'fraction_positive_sign': 0.09259259259259259, 'mean_sharpe': -78.81612177344358}
regime  n_trades  hit_rate   z_stat   ci_low  ci_high  barrier_pct  cost_pct  break_even_p    margin
 range      7043  0.503763 0.631534 0.492086 0.515440     0.002024  0.000676      0.666961 -0.163199
 trend       299  0.508361 0.289157 0.451694 0.565028     0.004246  0.000687      0.580843 -0.072482
regime  n_trades  mean_return  std_return  sharpe_per_trade     t_stat       n_eff  t_stat_neff
 range      7043    -0.000726    0.002530         -0.286996 -24.085472 2293.839060   -13.745413
 trend       299    -0.000517    0.003934         -0.131467  -2.273270  221.680993    -1.957401

```
