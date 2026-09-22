# H2.0 — Wykonalność hipotezy „funding rate": dwa z trzech sformułowań ODRZUCONE przed eksperymentem (2026-09-22)

## ID testu

**H2.0** — runda wykonalności otwierająca nową hipotezę. **ZERO wariantów** (żadnego
porównania z targetem). Patrz `runs/INDEX.md`.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Co robiliśmy:** Faza 0 sprawdzała, czy da się przewidzieć kierunek ceny bitcoina na podstawie
samej ceny i obrotu. Nie da się. Więc szukamy **innego rodzaju informacji**. Wybraliśmy
**funding rate** — opłatę, którą co 8 godzin płacą sobie nawzajem posiadacze pozycji długich
i krótkich na giełdzie. Mówi ona, w którą stronę tłum jest przechylony. **To pierwsza w tym
projekcie informacja, która nie jest po prostu przetworzoną ceną.**

**Co zrobiliśmy w tej rundzie:** ściągnęliśmy tę opłatę za ostatnie 6,8 roku (7 457 zapisów,
żadnego braku) i **policzyliśmy, czy pomysł ma szansę zadziałać — ZANIM go uruchomiliśmy.**

**Wynik: pomysł można wykorzystać na trzy sposoby i dwa z nich odpadają.**

1. **„Handluj tylko wtedy, gdy opłata jest wyjątkowo wysoka"** — ❌ **odpada.** Takich chwil jest
   za mało (od 14 do 130 rocznie). Przy tak małej liczbie transakcji wynik będzie
   nieodróżnialny od przypadku, cokolwiek policzymy. To dokładnie ten sam błąd, który zabił
   Fazę 0: filtr odsiewa tyle danych, że nie zostaje nic do zmierzenia.

2. **„Nie zgaduj kierunku — po prostu inkasuj opłatę"** — ❌ **odpada, ale ciekawie.**
   Tu jest rzecz, której wcześniej nie widzieliśmy: gdy stajesz po stronie, która **dostaje**
   opłatę zamiast ją płacić, **zarabiasz nawet trafiając rzadziej niż w połowie przypadków**
   (próg spada z 53% do 48%). Zwykle trzeba trafiać *lepiej* niż moneta — tu wystarczy *gorzej*.
   Niestety: pozycję trzeba trzymać 2 dni, a w 6,8 roku mieści się tylko 1 240 takich okienek,
   z czego opłata jest wysoka w garstce. **Za mało, żeby cokolwiek udowodnić** — brakuje
   nie kilkunastu procent, tylko dziesięciokrotności.

3. **„Dodaj opłatę jako jedenastą informację dla modelu, bez żadnego filtra"** — ✅ **jedyne
   wykonalne.** Na świecach 4-godzinnych. Ale margines jest cienki.

**Czy to obiecujące?** Uczciwie: **raczej nie.** Żeby zarobić, trafność musi wzrosnąć z 50,3%
do 53,1% — czyli o **2,85 punktu procentowego**. W całej historii tego projektu **żadna
pojedyncza nowa informacja nie dała takiego skoku**. Uruchamiamy to nie dlatego, że
spodziewamy się sukcesu, tylko dlatego, że **to ostatnia nieprzetestowana możliwość**,
a sprawdzenie kosztuje jedno podejście.

**Czego ta runda NIE zrobiła:** nie sprawdziliśmy ani razu, czy opłata faktycznie przewiduje
cenę. Celowo. Gdybyśmy najpierw popatrzyli, a potem ustalili kryterium sukcesu, oszukiwalibyśmy
samych siebie — raz już się na tym przejechaliśmy (runda C2.13).

**Znaleziona przy okazji rzecz warta osobnego sprawdzenia:** prawdopodobnie **przepłacamy
w rachunku kosztów**. Gdy pozycja kończy się „z upływem czasu", zakładamy drogie wyjście po
cenie rynkowej — a przecież **wiadomo z góry, kiedy to nastąpi**, więc można złożyć tańsze
zlecenie oczekujące. Poprawka obniżyłaby wymagany wzrost trafności z 2,85 do 1,81 punktu —
to największa pojedyncza poprawa dostępna w tym projekcie.

---

## Metadane

- **Branch:** `task/H2-funding-hipoteza`
- **Poprzedzający stan (master):** `5978451` (merge Z10)
- **Nowy kod:** `data/fetch_funding.py` + `tests/test_fetch_funding.py` (14 testów)
- **Dane (NOWE, cache trwały):** `data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet`
  — **7 457 rekordów, 2019-09-10T08:00Z → 2026-06-30T16:00Z, ZERO dziur** (6,80 roku;
  1 096 rekordów/rok wobec teoretycznych 1 095,75)
- **Komenda:** `py -m data.fetch_funding`, następnie 6 skryptów analitycznych z tego katalogu
  (pełny output: `raw_output.txt`)
- **Warianty:** **0** — mierzone wyłącznie rozkład, trwałość, liczebność, geometria i moc.
  **Związek funding→zwrot NIE był liczony ani razu**, celowo (patrz „Dyscyplina" niżej).
- **Testy:** **265/265** (251 + 14 nowych).

## Poprzedzające wyniki (zasada 14)

- **Z10** (`runs/2026-09-22_z10-zamkniecie-fazy-0/`) — zamknięcie Fazy 0. Diagnoza, która
  wybrała kierunek tej rundy: **wąskie gardło jest informacyjne, nie inżynieryjne**;
  wszystkie 10 cech to transformacje ceny i wolumenu. Rekomendacja 4: rachunek mocy
  **przed** eksperymentem.
- **Z19** — precedens: rachunek mocy obalił rekomendację Z9, **zanim kosztowała rundę**.
  Ta runda jest jego bezpośrednim zastosowaniem.
- **C2.5** — pułapka dyskretnego rozkładu w `direction_persistence_10` (progi wpadały
  w lukę nośnika). Powtórzyła się tutaj, w funding — patrz Wynik 1.
- **Z5b/S1b** — zmierzony lejek świeca→transakcja (8,03%) i udział timeoutów (60,8%),
  użyte tu jako jedyne realne odniesienie dla estymaty próby.
- **Z16** — wymóg spójności bramki z horyzontem etykiety.
- **C2.12** — model wykonania maker/taker; `round_trip_cost_fraction` = **0,0900%**.

## Dlaczego funding, a nie „momentum bez bramki"

Użytkownik wskazał dwóch kandydatów. Wybór wynika wprost z diagnozy Z10, nie z preferencji:

| kandydat | zbiór informacyjny | co mówi o nim historia projektu |
|---|---|---|
| momentum bez bramki reżimu | **ten sam** (OHLCV) | zmiany architektury nad tymi samymi cechami nie ruszyły `p` ani razu w 10 wariantach |
| **funding rate** | **NOWY** — pozycjonowanie publikowane przez giełdę, niewyprowadzalne z OHLCV | **nigdy nie testowany**; w Fazie 0 istniał wyłącznie jako **stała kosztowa** `FUNDING_RATE_8H = 0.0001` |

Skoro Z10 orzekł, że gardło jest informacyjne, to jedyną zmianą, która może ruszyć `p`, jest
**nowy zbiór informacyjny**. Momentum bez bramki byłoby jedenastą próbą wyciśnięcia sygnału
z ceny i wolumenu.

## Dyscyplina tej rundy (zaostrzona wobec Fazy 0)

**Nie policzyłem ani jednej korelacji funding↔zwrot, ani jednej trafności.** To zaostrzenie
wobec precedensu C2.7, gdzie „opisowy screening" obejrzał 34 korelacje cecha-target. Powód:
**C2.13**. Tam monotoniczny wzrost trafności z `signal_confidence`, wyglądający na sygnał
w dwóch niezależnych reżimach, okazał się **artefaktem selekcji post hoc** — a pre-rejestracja
oparta na nim doprowadziła do wyniku odwrotnego do przewidywanego.

Kryterium H2.1 będzie więc pre-rejestrowane na **mechanizmie ekonomicznym i rachunku mocy**,
nie na obejrzanej zależności.

---

# Wyniki

## 1. Funding ma MASĘ PUNKTOWĄ — progi percentylowe są tu nieużywalne

**35,85% wszystkich obserwacji to dokładnie +0,0100%** — stawka bazowa Binance, do której
mechanizm wraca, gdy premia perp-spot jest w pasmie neutralnym.

Skutek: percentyle `p20` i `p80` **obie** wypadają w tej masie, więc maska
`(r ≥ p80) | (r ≤ p20)` łapie **70,2% obserwacji** zamiast 20%.

> **To ten sam błąd, który C2.5 wykrył w `direction_persistence_10`** — próg wpadający w lukę
> dyskretnego nośnika. Gdyby H2 pre-zarejestrowało „górny/dolny decyl funding", eksperyment
> testowałby coś zupełnie innego, niż zapisano. **Wniosek wiążący dla H2.1: próg musi być
> ABSOLUTNY** (odchylenie od stawki bazowej), nigdy percentylowy.

Rozkład (za 8h): mediana **+0,0100%**, średnia +0,0107%, σ 0,0209%, **ujemnych 14,64%**,
p99 = +0,1057%. Annualizowany funding przy medianie: **+10,96%/rok** — czyli stała kosztowa
z Fazy 0 była akurat dobrze dobrana jako *mediana*, ale ignorowała 64,15% obserwacji, które
od niej odbiegają.

**Trwałość:** autokorelacja lag=1 (8h) = **+0,797**, lag=3 (24h) = +0,693, lag=21 (7 dni) =
+0,459. Funding jest **silnie trwały** — to nie jest szum 8-godzinny, tylko wolnozmienny stan
rynku. To argument ZA, jedyny mocny, jaki ta runda znalazła.

## 2. Sformułowanie „bramka na skrajny funding" — ODRZUCONE (moc 0,05–0,44×)

Pierwsze, najbardziej naturalne sformułowanie: handluj tylko wtedy, gdy funding jest skrajny.

| próg \|f\| | zdarzeń | % obs. | na rok | margines mocy |
|---|---|---|---|---|
| 0,020% | 884 | 11,9% | 130 | **0,44×** |
| 0,030% | 656 | 8,8% | 96 | 0,33× |
| 0,050% | 346 | 4,6% | 51 | 0,17× |
| 0,080% | 158 | 2,1% | 23 | 0,08× |
| 0,100% | 92 | 1,2% | 14 | **0,05×** |

Wymagane ≥ 1,0×. **Każda komórka odpada, najlepsza o ponad połowę** — a to jest **górna
granica**, przed abstynencją modelu (90,5% w S1b) i foldami poniżej `MIN_TRAIN_ROWS`.

> Mechanizm porażki jest **dokładnie ten sam co w Fazie 0**: bramka zagłodziła próbę. Reżim
> `trend` dawał 0,53% świec; bramka skrajnego funding daje 1,2–11,9%. Powtórzyłbym błąd,
> który właśnie udokumentowałem w Z10.

## 3. Sformułowanie bez bramki (funding jako 11. cecha) — krzywa wykonalności per interwał

Pytanie postawione właściwie: **czy próg opłacalności leży w zasięgu tego, co przy dostępnej
próbie da się w ogóle odróżnić od monety** (`min_detectable_hit_rate < break_even_p`)?

| interwał | świec / 6,8 roku | B_eff | break-even | n szac. | min. wykrywalna | zapas | wymagany przyrost `p` |
|---|---|---|---|---|---|---|---|
| 1h | 59 590 | 0,5747% | 57,83% | 4 784 | 51,42% | +6,41 pp | +7,56 pp |
| 2h | 29 779 | 0,8278% | 55,44% | 2 391 | 52,00% | +3,43 pp | +5,17 pp |
| 3h | 19 842 | 1,0219% | 54,40% | 1 593 | 52,46% | +1,95 pp | +4,13 pp |
| **4h** | **14 902** | **1,4424%** | **53,12%** | **1 196** | **52,83%** | **+0,29 pp** | **+2,85 pp** |
| 8h | 7 444 | 2,1245% | 52,12% | 598 | 54,01% | −1,89 pp | — |
| 1d | 2 472 | 3,8721% | 51,16% | 198 | 56,96% | −5,79 pp | — |
| 3d | 815 | 6,6316% | 50,68% | 65 | 62,11% | −11,44 pp | — |

Dwa przeciwstawne efekty i jedno optimum:

- **grubszy interwał** → większa bariera → **niższy próg opłacalności** (51,16% na 1d), ale
  **mniejsza próba** → od 8h w górę progu nie da się odróżnić od monety;
- **cieńszy interwał** → duża próba, ale próg rośnie do absurdu (57,83% na 1h wobec zmierzonych
  w projekcie 50,27%).

> **4h jest jedyną komórką dobrą na obu osiach naraz**: najmniejszy wymagany przyrost trafności
> (**+2,85 pp**) przy zapasie mocy nadal dodatnim (+0,29 pp). Zapas jest **cienki** i to jest
> główne ryzyko H2.1.

## 4. Funding jako PRZYCHÓD — zmiana rządzącej nierówności

Najważniejsze ustalenie koncepcyjne tej rundy. **Cała Faza 0 modelowała funding jednostronnie
— jako koszt.** Ale strona, która go OTRZYMUJE (short przy dodatnim, long przy ujemnym),
dostaje go jako przychód, więc nierówność rządząca zmienia się:

```
    Faza 0:   (2p − 1)·B  >  C                    ⇒  p* = 0,5·(1 + C/B)
    H2:       (2p − 1)·B  +  F  >  C              ⇒  p* = 0,5·(1 + (C − F)/B)
```

**Gdy `F > C`, próg opłacalności spada PONIŻEJ 50%** — czyli przewaga kierunkowa przestaje być
potrzebna. To stan jakościowo inny niż cokolwiek w Fazie 0, gdzie `p* ∈ [52,7%; 82,8%]`.

### Kontrola falsyfikacyjna: bariera ucina zbieranie funding

Naiwny rachunek zakłada `F = |f| × liczba_okresów`. Ale triple-barrier zamyka pozycję, gdy cena
dotknie ±1,5×ATR — i funding przestaje się naliczać. Zmierzyłem realne trwanie pozycji:

| V | horyzont | mediana trwania | średnio okresów funding | timeoutów |
|---|---|---|---|---|
| 3 | 12h | 3,0 świec | 1,34 | 77,9% |
| 6 | 24h | 5,0 świec | 2,20 | 48,3% |
| 12 | 48h | 5,0 świec | **3,10** | 20,0% |
| 18 | 72h | 5,0 świec | 3,47 | 8,2% |

**Trwanie się nasyca** — mediana to 5 świec niezależnie od `V ≥ 6`, bo bariera pada wcześniej.
Wydłużanie horyzontu powyżej 48h nie dokłada już funding.

Skutek dla arytmetyki — i **wniosek przeżył własną kontrolę**:

| próg \|f\| | V | p* naiwne | **p\* realne** |
|---|---|---|---|
| 0,020% | 12 | 44,33% | **48,13%** |
| 0,030% | 12 | 42,84% | **47,36%** |
| 0,050% | 12 | 39,58% | **45,67%** |

Ucięcie zabrało ~4 pp, ale **próg nadal leży poniżej 50%**.

## 5. …i mimo to carry jest NIEWYKONALNY (moc 0,03–0,12×)

Pytanie rozstrzygające: ile transakcji trzeba, żeby **pokazać** opłacalność — czyli żeby dolny
kraniec CI95 przebił `p*` przy prawdziwym `p = 50%` (bez żadnej przewagi kierunkowej)?

| próg \|f\| | zdarzeń | F realne | p* | zapas do 50% | n bez nakładania | n wymagane | margines |
|---|---|---|---|---|---|---|---|
| 0,010% | 3 932 | 0,0629% | 50,66% | −0,66 pp | 655 | — | 0,00× |
| 0,015% | 1 046 | 0,1495% | 48,55% | +1,45 pp | 174 | 4 599 | 0,04× |
| 0,020% | 884 | 0,1671% | 48,13% | +1,87 pp | 147 | 2 736 | 0,05× |
| 0,030% | 656 | 0,1987% | 47,36% | +2,64 pp | 109 | 1 375 | 0,08× |
| 0,050% | 346 | 0,2679% | 45,67% | +4,33 pp | 58 | 513 | 0,11× |
| 0,080% | 158 | 0,3579% | 43,49% | +6,51 pp | 26 | 226 | **0,12×** |

Margines **rośnie** z progiem (0,04× → 0,12×), bo `p*` spada szybciej, niż topnieje próba —
ale **nigdzie nie zbliża się do 1,0×**. Brakuje rzędu wielkości.

> **Dlaczego: pozycja trzymana 48h blokuje 6 okresów funding.** Przy 7 457 okresach w całej
> historii daje to maksymalnie 1 240 nienakładających się pozycji, z których skrajny funding
> ma 2–12%. Ograniczeniem jest **liczba nienakładających się okien w 6,8 roku**, a tego nie
> naprawi żaden dobór progu.

**Obserwacja, która wskazuje, gdzie ta strategia ŻYJE:** brakuje próby w wymiarze **czasu**, nie
w wymiarze zdarzeń. Sformułowanie **przekrojowe** — ten sam mechanizm na kilkudziesięciu
instrumentach naraz — mnoży próbę przez liczbę instrumentów i staje się wykonalne przy ~20+
instrumentach. To jednak **inny projekt**: wymaga silnika portfelowego, którego Faza 0 nie ma,
i łamie zasadę 9 (BTC samodzielnie do końca). **Odnotowuję jako kierunek, nie jako propozycję
rundy.**

---

## Co na plus (+)

- **Rachunek mocy przed eksperymentem odrzucił DWA z trzech sformułowań za 0 wariantów.**
  Dokładnie ten proces, którego brak Z10 nazwał najdroższym błędem Fazy 0 (Z19 powstał po
  zużyciu 9 z 10 wariantów). Tutaj zadziałał, zanim cokolwiek kosztował.
- **Kontrola falsyfikacyjna własnego, atrakcyjnego wyniku.** Rachunek carry wyglądał
  przełomowo (`p*` poniżej 50%!) — natychmiast go sprawdziłem pod kątem ucięcia barierą.
  Wniosek przeżył, ale **to kontrola, a nie entuzjazm, ustaliła realną liczbę**.
- **Pułapka dyskretna wyłapana PRZED pre-rejestracją**, a nie po fakcie jak w C2.5.
- **Nowy, trwały zbiór danych** — 7 457 rekordów funding, zero dziur, cache w `data/raw/`
  zgodnie z poleceniem „pobrane dane leżą w jednym miejscu".
- **Zaostrzona dyscyplina:** zero spojrzeń na target, mimo że precedens C2.7 by je dopuszczał.

## Co na minus (−)

- **Estymata próby opiera się na JEDNYM pomiarze lejka** (8,03% z S1b). Ten lejek pochodzi
  z konfiguracji z bramką reżimu i agresywnym early stoppingiem na małych zbiorach walidacyjnych
  (90,5% abstynencji). Bez bramki foldy są ~3,5× większe, więc **realny lejek może być inny
  w obie strony**. To największa niepewność tej rundy i wprost przekłada się na `n_szac`.
- **`B_eff` liczone z jednej korekty** (60% timeoutów, timeout wychodzi po ~0,35 bariery) —
  wartości z S1/Z5b, nieprzeliczone dla konfiguracji bez bramki.
- **Zapas mocy dla 4h wynosi +0,29 pp** i jest obliczony, nie zmierzony. Jeśli lejek okaże się
  gorszy niż w S1b, H2.1 skończy się **nierozstrzygalnie**, jak S1b.
- **Nie sprawdziłem, czy założenie `timeout → taker` w `exit_leg_for_reason` jest poprawne.**
  Timeout to wyjście **zaplanowane** (świeca znana z góry), więc dałoby się je obsłużyć zleceniem
  limit (maker). Przy 60% timeoutów obniżyłoby to koszt 0,0900% → ~0,0600% i próg na 4h
  **53,12% → 52,08%**, czyli wymagany przyrost `p` z 2,85 na 1,81 pp. **Nie włączam tego do H2.1**
  — to zmiana modelu kosztów, a mieszanie jej z testem nowej cechy łamie zasadę 4 (jedna zmiana
  na raz) i zaciera, co dało efekt. Odnotowuję jako **najwyżej dźwigniowy kandydat na osobną rundę**.
- **Runda nie zbliżyła projektu do GO.** Odrzuciła dwie ścieżki i zostawiła jedną z cienkim
  marginesem. To wartość informacyjna, nie postęp.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Kluczowa liczba przeliczona drugą drogą:** liczba rekordów funding sprawdzona przez
  niezależny rachunek kalendarzowy — 6,80 roku × 365,25 × 3 = **7 451** wobec pobranych
  **7 457** (różnica 6 = zaokrąglenie granic okna), przy `find_funding_gaps` = **0 dziur**.
  Rozkład zweryfikowany niezależnie: mediana = stawka bazowa 0,0100%, co zgadza się
  z `FUNDING_RATE_8H = 0.0001` przyjętym w Fazie 0 jako wartość typowa.
- **Kogo NIE ma w zbiorze:** (a) **tylko BTC** — ETH/SOL/BNB mają własny funding i własne
  progi, żaden wniosek tej rundy nie przenosi się na nie automatycznie; (b) **okres przed
  2019-09-10** — Binance nie ma wcześniejszych perpetuali, więc bessa 2018 i cały cykl
  2017 są poza zbiorem **dla każdej hipotezy w tym projekcie**; (c) `n_szac` **nie odejmuje**
  foldów poniżej `MIN_TRAIN_ROWS` ani rozbiegu wskaźników — jest **górną granicą**;
  (d) rachunek carry zakłada, że zlecenie limit na wejściu się wypełnia — **pomija adverse
  selection**, to samo ograniczenie co w C2.12; (e) **geometria liczona z resample'u** 4h→8h/1d
  i 1h→2h/3h, dopuszczalnego tylko dlatego, że ATR używa cen, a nie wolumenu (Z9: resample
  psuje wyłącznie wolumen) — **eksperyment wymagałby danych natywnych**.
- **Red-flag „wynik idealnie potwierdza hipotezę":** zachodziłby przy sekcji 4 (`p*` poniżej
  50% to wynik zbyt dobry), dlatego natychmiast uruchomiłem kontrolę ucięcia barierą i **rachunek
  mocy, który to sformułowanie odrzucił**. Runda kończy się odrzuceniem 2 z 3 własnych ścieżek
  — to przeciwieństwo potwierdzenia.
- **Ograniczenie werdyktu:** wszystkie liczby `n_szac` i `B_eff` są **estymatami z lejka S1b**,
  nie pomiarami na konfiguracji H2. Werdykty „NIEWYKONALNE" dla sekcji 2 i 5 są odporne
  (marginesy 0,05× i 0,12× — brakuje rzędu wielkości, nie kilkunastu procent). Werdykt
  „wykonalne" dla 4h w sekcji 3 **NIE jest odporny** (+0,29 pp) i to jest jawnie zapisane
  w klauzuli nierozstrzygalności H2.1.

## Wniosek

Hipoteza „funding rate" rozpada się na **trzy różne sformułowania**, a rachunek mocy przed
eksperymentem rozstrzygnął dwa z nich **na nie**, za zero wariantów:

| sformułowanie | werdykt | powód |
|---|---|---|
| bramka na skrajny funding (kierunek) | **ODRZUCONE** | moc 0,05–0,44× — bramka zagładza próbę, dokładnie jak reżim `trend` w Fazie 0 |
| funding carry (przychód > koszt, bez przewagi kierunkowej) | **ODRZUCONE** | moc 0,03–0,12× — ograniczeniem jest liczba nienakładających się okien 48h w 6,8 roku; żyje w formule **przekrojowej**, nie czasowej |
| **funding jako 11. cecha, BEZ bramki, 4h** | **JEDYNE WYKONALNE** | zapas mocy +0,29 pp, wymagany przyrost `p` = **+2,85 pp** |

## Rekomendacja — pre-rejestracja H2.1

**Konfiguracja ZAMROŻONA poniżej, zapisana PRZED uruchomieniem czegokolwiek:**

| element | wartość | uzasadnienie |
|---|---|---|
| interwał | **4h natywne**, 2019-09→2026-07 (14 916 świec) | jedyna komórka dobra na obu osiach (sekcja 3) |
| bramka reżimu | **BRAK** — wszystkie świece kandydują | bramkowanie zagładza próbę: udokumentowane dwa razy (Faza 0, sekcja 2) |
| cecha | **jedna nowa:** funding rate + `funding_zscore` liczony w oknie **rozszerzającym się wstecz** | zasada 4 (jedna cecha na raz); okno wsteczne, bo zwykłe `rolling` na szeregu o autokorelacji 0,80 jest podatne na przeciek |
| próg | **ABSOLUTNY**, nigdy percentylowy | masa punktowa 35,85% (sekcja 1) |
| `V` | **3** (12h) | spójność (Z16) + zmierzone trwanie pozycji |
| model kosztów | **NIEZMIENIONY** (0,0900%, maker/taker) | zmiana kosztu w tej samej rundzie zaciera, co dało efekt (zasada 4) |
| **kryterium sukcesu** | **`ci_low(p) > 53,12%`** | pre-rejestrowane, break-even z geometrii, nie z danych po fakcie |
| **klauzula nierozstrzygalności** | **`n < 1 000` ⇒ NIEROZSTRZYGNIĘTE**, bez interpretacji w żadną stronę | zapas mocy to tylko +0,29 pp; S1b pokazał, jak łatwo próba zapada się 3× |
| **reguła STOP** | **1 wariant. Wynik negatywny ⇒ koniec serii**, bez drugiego progu, drugiego `V` i drugiego interwału | licznik H2 startuje od zera i wyczerpuje się na pierwszym |

**Uczciwa prognoza, zapisana przed uruchomieniem:** wymagany przyrost trafności to **+2,85 pp**
(z 50,27% do 53,12%). Żadna pojedyncza cecha w historii tego projektu nie dała takiego efektu —
`adx_14` dała ~0 (C2.8), a wszystkie 17 kandydatek z C2.7 miały |korelację| z targetem poniżej
0,065. **Prior jest niski.** Uzasadnieniem uruchomienia nie jest oczekiwany sukces, tylko to, że
jest to **jedyny nieprzetestowany zbiór informacyjny**, a koszt rozstrzygnięcia wynosi 1 wariant.

**Dwa kandydaci na osobne rundy, jawnie NIE włączone do H2.1:**
1. **`timeout → maker`** w `exit_leg_for_reason` — najwyżej dźwigniowa pojedyncza zmiana
   w projekcie: próg 53,12% → 52,08%, wymagany przyrost `p` 2,85 → 1,81 pp.
2. **Carry przekrojowy** na wielu instrumentach — wykonalny statystycznie, ale wymaga silnika
   portfelowego i łamie zasadę 9.

## Pełny surowy output

[`raw_output.txt`](raw_output.txt) — 6 skryptów, wszystkie w tym katalogu.
