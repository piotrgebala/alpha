# S1 — architektura jednoreżimowa na 4h: kryterium NIESPEŁNIONE, trafność poniżej 50% (2026-09-22)

## ID testu

**S1** — pierwsza runda NOWEJ serii hipotezowej (architektura jednoreżimowa).
Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/S1-single-regime-4h`
- **Poprzedzający stan (master):** `fb0dcb7` (Z5b — pre-rejestracja).
- **Komenda:** `py -m backtest.run_single_regime_4h`
- **Nowe pliki:** `backtest/run_single_regime_4h.py`
- **Zmiany (Z22, odblokowanie):** `backtest/engine.py` — `vertical_barrier_candles` jako
  parametr `run_backtest`; `embargo_candles=None` domyślnie **wiąże się z V**, żeby nie dało
  się ich rozjechać przez przeoczenie.
- **Dane:** `BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet` — 14 916 świec,
  6,8 roku, zero dziur (trwały cache).
- **Warianty:** **1/1 w nowej serii** (architektura jednoreżimowa to nowa hipoteza wobec
  dwureżimowej z `docs/rag/01`).
- **Testy:** **246/246** (242 + 4 dla Z22).

## Konfiguracja — zamrożona przed uruchomieniem

Pełna pre-rejestracja: `runs/2026-09-22_z5b-long-history-4h-preregistration.md`.
Świece 4h natywne, historia 2019-09-10 → 2026-07-01, reżim `range` (bez `trend`), `V = 3`
(12h), `ATR_MULTIPLIER = 1.5` (nietknięty), walk-forward 60/28/28 dni, koszty `maker_limit`,
`validation_fraction = 0.2`, `embargo = V`, seed 42.

- **Kryterium sukcesu:** dolny kraniec 95% CI trafności **> 54,60%**.
- **Klauzula nierozstrzygalności:** `n` < 925 ⇒ wynik nierozstrzygalny.
- **Reguła STOP:** wynik negatywny = koniec tej linii hipotezy.

## Wynik

**`n` = 1 037 > 925, więc klauzula nierozstrzygalności NIE wchodzi w grę — wynik jest
rozstrzygający.**

| miara | wartość |
|---|---|
| trafność kierunku | **48,60%** (z = −0,90) |
| 95% CI | **[45,56%; 51,64%]** |
| break-even (pre-rejestrowany) | 54,60% |
| break-even (zmierzony w przebiegu) | 53,07% |
| trzeba było zmierzyć | 57,64% |
| **margines** | **−4,47 pp** |
| klasyfikacja | NO-GO (59 ważnych foldów z 85) |
| pooled t-stat | −2,24 (po N_eff: −1,74) |
| udział timeoutów | 58,6% |
| trafność na barierach / timeoutach | 51,28% / 46,71% |
| sygnały odrzucone przez bramkę kosztową | **0** |

**Kryterium niespełnione, i to nie „o włos".** Górny kraniec przedziału ufności (51,64%)
leży **poniżej** zmierzonego progu opłacalności (53,07%). Można więc powiedzieć z 95%
pewnością, że trafność jest niższa od progu — to mocniejsze stwierdzenie niż „nie udało się
wykazać", które padało w poprzednich rundach.

## Co na plus (+)

- **Eksperyment zadziałał dokładnie tak, jak go zaprojektowano.** Moc wystarczyła (n = 1 037
  wobec wymaganych 925), klauzula nierozstrzygalności nie musiała być użyta, a wynik jest
  jednoznaczny w obie strony — dało się wykazać brak, a nie tylko nie wykazać obecności.
- **Bramka kosztowa odrzuciła ZERO sygnałów** (wobec 98% na 5m). To potwierdza mechanizm
  z Z9: na 4h bariera jest tak szeroka względem stałego kosztu, że wykonalność kosztowa
  przestaje być wiążąca. Geometria została naprawiona — i to nie pomogło.
- **Miary klasyfikacji wreszcie zachowują się sensownie:** `mean_sharpe` = −0,59 zamiast
  −60 (5m), 34% foldów powyżej progu, 41% o dodatnim znaku. Patologia per-fold Sharpe'a
  z C2.12 była, jak podejrzewano, artefaktem foldów o kilku transakcjach — przy 4h i oknie
  28-dniowym znika. To pośrednio potwierdza diagnozę z C2.12.
- Rozbicie per typ wyjścia zgodne z przewidywaniem Z5b (58,6% timeoutów wobec
  przewidzianych 60,8%) — model kalibracyjny okazał się trafny.
- Z22 odblokowane: horyzont etykiety jest teraz parametrem, a embargo **automatycznie**
  za nim podąża, więc nie da się ich rozjechać przez przeoczenie (ten sam typ zabezpieczenia,
  co CLAUDE.md zasada 3 dla mnożnika ATR).

## Co na minus (−)

- **Trafność wyszła PONIŻEJ 50%** (48,60%). To nie jest „brak edge'u" — to lekko ujemny
  edge, choć nieistotny statystycznie (z = −0,90, CI obejmuje 50%). Uczciwie: nie mam
  podstaw twierdzić, że model jest systematycznie odwrócony; mam podstawy twierdzić, że
  nie jest lepszy od monety.
- Konfiguracja zmieniała naraz pięć rzeczy (interwał, historię, horyzont, okna, liczbę
  reżimów), więc wynik negatywny **nie wskazuje, który element zawiódł**. To był świadomy
  kompromis (każdy element osobno był niewykonalny statystycznie — Z19), ale ogranicza
  wartość diagnostyczną porażki.
- `t_stat_neff` = −1,74 przy `N_eff` = 620 z 1 037 transakcji — autokorelacja zjada ~40%
  efektywnej próby. Rachunek mocy z Z5b zakładał niezależność, więc realna moc była niższa
  niż deklarowane 4,3×. Wynik i tak jest rozstrzygający (CI nie zahacza o próg), ale
  margines był cieńszy, niż sądziłem.
- 22 foldy z 85 pominięte — nadal jedna czwarta. Przy oknie 28-dniowym to mniej niż
  wcześniej, ale nie zero.

## Wniosek

Architektura jednoreżimowa na 4h ze spójnym horyzontem etykiety **nie wykazuje edge'u
kierunkowego**. Trafność 48,60% przy 95% CI [45,56%; 51,64%] i progu opłacalności 53,07%
oznacza, że hipoteza jest odrzucona z zapasem, a nie na granicy.

Ta runda usunęła **wszystkie** znane wady pomiaru naraz:

| co naprawiono | runda | efekt na `p` |
|---|---|---|
| przeciek early stopping | Z17 | 51,07% → 50,38% |
| brak embargo train/test | Z21 | (jw.) |
| niespójność bramka↔horyzont | Z16/S1 | 70,2% świec spójnych |
| zepsuty wolumen z resampla | Z9 | natywne świece |
| bariera zjadana przez koszt | Z9/S1 | bramka odrzuca 0% |
| za mała próba | Z5b | n = 1 037 > 925 |
| patologia per-fold Sharpe | S1 | mean_sharpe −60 → −0,59 |

Po usunięciu wszystkich tych wad trafność wynosi **48,60%**. Każda kolejna naprawa
pomiaru zostawiała `p` niezmienione albo nieznacznie gorsze — ani razu lepsze. To jest
spójny obraz braku sygnału kierunkowego, a nie serii pechowych konfiguracji.

## REGUŁA STOP — uruchomiona

Zgodnie z pre-rejestracją: wynik negatywny kończy tę linię hipotezy. **Nie testuję
kolejnego `V`, kolejnego interwału ani kolejnego reżimu.** Licznik nowej serii: **1/1**.

## Rekomendacja

Uczciwa rekomendacja to **Z10 opcja 1: udokumentowane zamknięcie Fazy 0 wynikiem
negatywnym**. Podstawa jest dziś nieporównanie mocniejsza niż przy pierwszym NO-GO
(Commit 6): 6,8 roku danych, trzy interwały, dwie architektury, realistyczne koszty
wykonania, pomiar bez znanych przecieków i specyfikacja spójna wewnętrznie.

Co zostaje otwarte i byłoby **nową hipotezą** (nie kontynuacją tej): inny driver niż
cena/zmienność — np. funding rate jako SYGNAŁ, a nie tylko koszt (`docs/rag/01` wskazuje go
jako kandydata na Fazę 1), inny instrument, albo inny target niż kierunek (np. zmienność).
Każda z nich wymaga własnej pre-rejestracji, własnego licznika i własnej reguły STOP —
i żadnej z nich nie uruchamiam bez wyraźnej decyzji użytkownika, bo reguła STOP właśnie
zadziałała.

## Pełny surowy output

```
================================================================================================
S1 — architektura jednoreżimowa na 4h (konfiguracja ZAMROŻONA w pre-rejestracji)
================================================================================================
dane: 14916 świec 4h, 2019-09-10 00:00:00+00:00 -> 2026-06-30 20:00:00+00:00
reżim: range (bez `trend`)  |  V = 3 (12h)  |  walk-forward 60/28/28 dni  |  seed 42
kryterium sukcesu: dolny kraniec 95% CI > 54.60%
klauzula nierozstrzygalności: n < 925

=== Klasyfikacja (kryteria docs/rag/03, NIEZMIENIONE) ===
{'classification': 'NO-GO', 'n_valid_folds': 59, 'n_total_folds': 85, 'fraction_above_threshold': 0.3389830508474576, 'fraction_le_zero': 0.5932203389830508, 'fraction_positive_sign': 0.4067796610169492, 'mean_sharpe': -0.5894676087080075}

=== Diagnostyka pooled ===
regime  n_trades  mean_return  std_return  sharpe_per_trade    t_stat     n_eff  t_stat_neff
 range      1037    -0.000178    0.002553         -0.069709 -2.244801 620.00031    -1.735739

=== Rozbicie edge'u ===
regime  n_trades  hit_rate    z_stat   ci_low  ci_high  share_timeout  hit_rate_barrier  hit_rate_timeout  barrier_pct  cost_pct  break_even_p    margin
 range      1037  0.486017 -0.900552 0.455597 0.516438       0.586307          0.512821          0.467105     0.012609  0.000775      0.530736 -0.044719

=== Foldy === łącznie=85, aktywne=63, pominięte=22
sygnały przepuszczone=1060, odrzucone przez koszt=0

================================================================================================
WERDYKT wobec PRE-REJESTROWANEGO kryterium
================================================================================================
  n                       = 1037
  trafność zmierzona      = 48.60%
  95% CI                  = [45.56%; 51.64%]
  break-even (pre-rej.)   = 54.60%
  break-even (zmierzone)  = 53.07%
  trzeba było zmierzyć    = 57.64%

  >>> KRYTERIUM NIESPEŁNIONE: dolny kraniec CI nie przekracza progu.
      Zgodnie z regułą STOP to koniec tej linii hipotezy.
```
