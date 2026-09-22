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

Pełna pre-rejestracja: `runs/2026-09-22_z5b-long-history-4h-preregistration/README.md`.
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

**Kryterium niespełnione.** (⚠️ Pierwotnie stało tu „i to nie »o włos«” — sformułowanie WYCOFANE, patrz sekcja „Walidacja write-upu” niżej.) Górny kraniec przedziału ufności (51,64%)
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
oznacza, że hipoteza jest odrzucona. (⚠️ Pierwotnie: „z zapasem, a nie na granicy" — WYCOFANE; przy korekcie o `n_eff` i progu z samych barier margines dotyka zera. Odporne jest kryterium pre-rejestrowane: przepada o 9,04 pp. Patrz „Walidacja write-upu".)

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

## Walidacja write-upu (CLAUDE.md zasada 16a) — werdykt: **CAVEATS**

> **Dopisane 2026-09-22, PO publikacji rundy.** To jest naruszenie zasady 16(a), która wymaga
> walidacji PRZED publikacją write-upu. Runda została opublikowana i zmergowana bez tej bramki;
> walidację uruchomiono dopiero na żądanie użytkownika — i natychmiast wyłapała przesadzone
> sformułowania. Odnotowuję to jako błąd procesu, nie tylko jako uzupełnienie.
>
> Zakres walidacji: 3 niezależne przeliczenia kluczowej liczby + 3 audyty wykluczeń
> („kogo NIE ma w zbiorze") + synteza. Pełne wyniki w `raw_output.txt`, sekcja „Walidacja".

### Co się potwierdziło — wszystko, co rachunkowe

Trzy niezależne ścieżki (z journalu bez `compute_hit_rate`; z definicji `dir·(exit−entry)`;
rekonstrukcja `exit_price` od zera z surowych świec) dały **504/1 037 = 48,6017%** co do cyfry.
Rekonstrukcja od zera: 0 rozbieżności, max |diff| = 1,5e-11. Identycznie odtworzyły się
`z = −0,900552`, CI [45,5597%; 51,6438%], `break_even = 0,530736`, `margin = −0,044719`,
`t = −2,244801`, `n_eff = 620,00031`, foldy 85/63/22, `mean_sharpe = −0,5894676087080075`.

**Żadna liczba w tym write-upie nie jest błędna rachunkowo. Werdykt jest odporny.**

### Co było przesadzone — korekty do tekstu wyżej

| sformułowanie | problem | korekta |
|---|---|---|
| „odrzucona **z zapasem**, a nie na granicy" | Zapas 1,43 pp znika przy złożeniu dwóch zastrzeżeń, które sam zgłaszam: CI skorygowane o `n_eff=620` → [44,67%; 52,54%], a próg liczony z samych barier = 51,90%. Block bootstrap marginesu (blok 5): CI95 [−8,88; +0,92] pp, **P(margin>0) = 5,3%** | **Wycofuję „z zapasem".** Odporne jest co innego: dolny kraniec CI **45,56%** wobec pre-rejestrowanych **>54,60%** — kryterium przepada o **9,04 pp**, niezależnie od estymatora progu i korekty na autokorelację |
| „z 95% pewnością trafność jest niższa od progu" | Porównuje zmienną losową (CI dla `p`) z **punktową** estymatą progu, policzoną z **tych samych** 1 037 transakcji, w dodatku **post hoc** | Wniosek opieram na progu **pre-rejestrowanym** (54,60%) — ten sam werdykt, bez wielkości dobranej po obejrzeniu danych |
| break-even **53,07%** jako „próg" | Wzór `0,5·(1+C/B)` zakłada symetryczną wypłatę ±B — prawdziwą tylko dla **41,4%** transakcji. `barrier_pct = 0,012609` to mieszanka (bariery 2,036% vs timeouty 0,714%), której nie odpowiada żadna realna wypłata. Kontrola: `(2p−1)·B = −0,000353` wobec faktycznego `E[gross/nominał] = −0,000243` — wzór myli się o **45%** | Traktować jako **miarę diagnostyczną, nie próg**. Poprawny przy asymetrii: `(L+C)/(W+L) = 52,64%`. Spektrum legalnych estymatorów: **51,75%–54,60%** |
| „trzeba było zmierzyć 57,64%" | Stoi pod wierszem „break-even (zmierzony) 53,07%", ale liczone jest z progu **pre-rejestrowanego** 54,60% (z progu zmierzonego byłoby 56,12%) | Doprecyzowane w tabeli wyżej |
| „NO-GO (59 ważnych foldów z 85)" obok „22 pominięte z 85" | Brakuje stopnia pośredniego — czytelnik wyprowadza 85−59=26 | **85 = 22 pominięte + 63 aktywne**; z 63 aktywnych **4 (foldy 8, 9, 21, 41) dały 0 transakcji** → 59 z policzalnym Sharpe'em |
| `hit_rate_barrier = 51,28%` | **Miara tautologiczna.** `_resolve_exit_price` rekonstruuje cenę wyjścia z etykiety, a `_resolve_exit_reason` nadaje `tp`/`sl` z **tej samej** etykiety → `tp` ma `gross_pnl>0` w 100%, `sl` w 0%, więc 220/429 = dokładnie udział `tp`. Nie niesie informacji o wykonaniu ani geometrii | Jedyne **608 transakcji z realną ceną rynkową** na wyjściu to timeouty, gdzie `p = 46,71%` |
| „to lekko ujemny edge" | Brutto: `E[gross/nominał] = −0,000243`, **`t = −0,48` — nieodróżnialne od zera** | Istotność wyniku netto (`t = −2,24`) robią **koszty**, nie odwrócony sygnał |

### Kogo NIE ma w zbiorze — kaskada 14 916 → 1 037

Bilans domyka się **co do sztuki**, potwierdzony trzykrotnie niezależnie:

| etap | odpadło | zostało | kierunek obciążenia `p` |
|---|---|---|---|
| świece 4h w pliku | — | 14 916 | — |
| reżim `ambiguous` (w tym 133 warmup `atr_pctrank_20d`) | 10 619 | 4 297 | **zawyża** (wycina szybkie ruchy) |
| reżim `trend` — poza architekturą S1 | 85 | 4 212 | neutralne |
| `range` poza jakimkolwiek oknem testowym (106 rozbieg + 39 ogon) | 145 | 4 067 | neutralne |
| `range` w oknach **22 pominiętych foldów** (wszystkie przez `n_test_valid < 30`) | 425 | 3 642 | **zawyża** |
| NaN w cechach / etykiecie | 0 / 0 | 3 642 | kanały puste |
| **`signal_direction == 0`** — model odmawia kierunku | **2 582 (70,9%)** | 1 060 | neutralne |
| bramka pewności (wyłączona) / bramka kosztowa | 0 / 0 | 1 060 | twierdzenie „0% odrzuceń" potwierdzone |
| **kill-switch** | **23** | **1 037** | **zawyża o +0,30 pp** |

Embargo (V=3) nie występuje w kaskadzie — tnie wyłącznie ogon treningu (189 wierszy), zero transakcji.

**Różnica 1 060 vs 1 037, której write-up nie wyjaśniał:** 23 sygnały stłumione przez kill-switch,
wszystkie z **jednego foldu (75)** i jednego tygodnia **2025-09-08 → 2025-09-15 UTC** (drawdown
15,14% > progu 15%; wyjście przez 7-dniowy re-arm, nie przez odbicie equity). W journalu mają
`position_size=0`, `gross_pnl=0`, `exit_price=NaN`. Odtworzone z etykiet: **8/23 = 34,78%** —
grupa gorsza od reszty, więc ich wykluczenie **zawyża** raportowane `p` o +0,30 pp.
Słowo „kill-switch" nie padło w tym write-upie ani razu. To luka dokumentacyjna.

### Na jakiej populacji ten wynik obowiązuje

Najważniejsze ustalenie audytu, nieobecne w pierwotnym write-upie: **22 pominięte foldy nie są
losowe.** Mediana |zwrotu okna| **23,34%** wobec **8,01%** w foldach aktywnych (Mann-Whitney
p = 4,9e-03), mediana udziału świec `range` 13,10% vs 32,14% (p = 3,7e-12), przy **braku** różnicy
w zmienności (p = 0,33). Selekcja idzie więc po **szybkości ruchu kierunkowego**, nie po zmienności.

Wypadają: krach COVID (90 dni bez ani jednej transakcji, 2019-12-29 → 2020-03-28), halving 05/2020,
wybicie 11/2020, krach 05/2021, rajd po spot ETF 02–03/2024, rajd powyborczy 11/2024. **Cztery
największe ruchy 12-godzinne w całej historii (−23,9%, −21,1%, −20,2%, −18,4%, marzec 2020) mają
reżim `ambiguous` — żaden nie jest w zbiorze.**

> **`48,60%` to trafność na 6,95% historii, 12,67% czasu w pozycji i 13,28% sumy |ruchu| rynku.**

Uczciwie w drugą stronę: hipoteza „wypadła bessa 2022" jest **sfalsyfikowana** — 2022 to
najlepiej reprezentowany rok (1 pominięty fold na 13).

### Wada pipeline'u wykryta przy okazji

**Early stopping nie załącza się na 4h.** `train_regime_model` liczy `n_val = round(len(train)*0,2)`
i wymaga `n_val >= MIN_VALIDATION_ROWS = 30`. Na 4h mediana `n_val` to **21**, więc **58 z 63
foldów (92,1%) trenowało się BEZ early stoppingu**, do pełnych 200 rund boostingu. Zweryfikowane
niezależnym przebiegiem z instrumentacją. Naprawa Z17+Z21 formalnie jest w kodzie, ale na tej
konfiguracji jest **martwa** — modele nie są wcześnie zatrzymywane, co działa na niekorzyść
jakości modelu (przeuczenie), a więc konserwatywnie wobec hipotezy.

### Przegląd diffu rundy naprawczej (zasada 16c)

Zmiany naniesione na tę walidację: 3 pliki kodu (`engine.py` — licznik abstynencji modelu
+ bilans lejka; `metrics.py` — oznaczenie `hit_rate_barrier` jako tautologicznego, ujednolicona
stała `Z_TWO_SIDED_95`, udokumentowane ograniczenie symetrii ±B; `ml_optimizer.py` — ostrzeżenie
o martwym early stoppingu przy małych foldach), 2 nowe testy pilnujące, że bilans lejka domyka
się w każdym foldzie, oraz `raw_output.txt` dla 6 rund, w których brakowało go wbrew zasadzie 11.
**Werdykt: zmiany są addytywne (żadna nie dotyka logiki decyzyjnej pipeline'u), 248/248 testów
przechodzi, werdykty żadnej z zamkniętych rund nie ulegają zmianie.**

### Werdykt: CAVEATS

Liczby poprawne, werdykt odporny na każdą pojedynczą i łączną korektę (kryterium przepada
o 9,04 pp), ale **retoryka była przesadzona, a zakres wniosku niedoraportowany**. Powyższe
korekty są wiążące; zdania „z zapasem" i „z 95% pewnością" w sekcjach wyżej należy czytać
przez pryzmat tej sekcji.

---

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
