# K2 — naprawa abstynencji, pochodzenie obciążenia na szumie, egzekwowalny wymóg mierzalności (2026-09-22)

> **STATUS: PRE-REJESTRACJA.** Sekcje „Wynik" i dalsze są celowo puste. Wszystko do sekcji
> „Arytmetyka oczekiwań" włącznie zapisano **przed napisaniem linijki kodu produkcyjnego**.

## ID testu

**K2** — kalibracja i naprawa przyrządu. **0 wariantów, POZA wszystkimi licznikami hipotez**
(ta sama rola co K1, Z19, Z9). Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/K2-naprawa-abstynencji`
- **Poprzedzający stan (master):** `3becd0b` (merge K1)
- **Zlecenie użytkownika:** naprawa abstynencji (wagi klas, wymuszenie kierunku), sprawdzenie
  kill-switcha jako źródła obciążenia, twardy wymóg mierzalności dla przyszłych rund.
- **Warianty:** **0** — patrz „Dlaczego to 0 wariantów".
- **Testy przed rundą:** 319/319.

## Poprzedzające wyniki (zasada 14)

- **K1** (`runs/2026-09-22_k1-kontrola-pozytywna/`) — aparat działa, kryterium uczciwe, ale
  abstynencja 99,3–99,7% przy słabym sygnale. **Ta runda prostuje dwie liczby z K1** (niżej).
- **Z19** — `wald_half_width`, `min_detectable_hit_rate`, `required_trades`. **Projekt miał te
  funkcje trzy rundy i nie połączył ich z K1.**
- **Z17 / Z17b / Z21** — przeciek early stopping i martwy próg walidacji. K2 **nie ma prawa**
  wejść na tę ścieżkę (strażnik w kodzie, niżej).
- **H2.1** — rozkład klasy timeout 66,58% bez bramki reżimu; `n=98`.
- **H3** — precedens: pre-rejestracja w osobnym commicie przed kodem; reguła D5.
- **C2.12** — precedens nazwanych wariantów (`execution_model`) zamiast pokręteł.

---

## Dwa SPROSTOWANIA do K1, bez których K2 mierzyłby artefakt

### 1. „Próg wykrywalności ~58,2%" to artefakt siatki `q`, nie właściwość przyrządu

58,20% to trafność zmierzona w **pierwszym punkcie siatki**, gdzie `ci_low > break_even`
(q=0,40). Przy siatce zawierającej q=0,30 ta sama konfiguracja podałaby inną liczbę — bez
jednej zmiany w kodzie. Właściwość przyrządu jest zamkniętą formułą:

```
kryterium:            ci_low > BE,  gdzie ci_low = p − z·√(p(1−p)/n)
warunek opłacalności: p > BE
⇒ pasmo „opłacalne, ale NIEWIDZIALNE" = (BE, BE + z·√(0.25/n))
⇒ SZEROKOŚĆ pasma = z·√(0.25/n)   — zależy WYŁĄCZNIE od n
```

Zweryfikowane na `krzywa_wykrywalnosci.csv` z K1:

| punkt | n | szerokość pasma |
|---|---|---|
| K1 q=0,00 | 50 | 13,86 pp |
| H2.1 | 98 | 9,90 pp |
| K1 q=0,20 | 105 | 9,56 pp |
| K1 kontrola negatywna (pooled) | 220 | 6,61 pp |
| S1b | 345 | 5,28 pp |
| K1 q=0,40 | 787 | 3,49 pp |
| K1 q=1,00 | 4 843 | 1,41 pp |
| **Z10 (liczba zamykająca Fazę 0)** | **7 687** | **1,12 pp** |

**Ta funkcja JEST W REPO od Z19** (`metrics.py::wald_half_width`). Nie wolno dokładać trzeciej
kopii w postaci stałej `0.582` — projekt ma już dwa trupy po zamrożonych progach
(`MIN_VALIDATION_ROWS = 30` wyłączył early stopping w 92% foldów; `std < 0.2` ze sweepu seedów).

**Skutek wsteczny: żaden.** Przy n=7 687 pasmo Z10 wynosiło 1,12 pp — zamknięcie Fazy 0 stało
na przyrządzie ostrym w tym punkcie.

### 2. Abstynencja przy doskonałej wyroczni to POPRAWNE zachowanie, nie wada

| | |
|---|---|
| abstynencja przy q=1,00 (K1) | **66,48%** |
| udział klasy timeout w etykietach (H2.1, bez bramki) | **66,58%** |

Zgodność do **0,1 pp**. Model przewiduje prawdziwą klasę, a ta w 2/3 świec jest timeoutem.
**Wadą jest zapaść przy SŁABYM sygnale: z 66,6% do 99,7%** — posterior kolapsuje do klasy
większościowej.

> **Cel naprawy jest liczbą, nie życzeniem:** sprowadzić abstynencję przy słabym sygnale
> z ~99,5% w okolice podłogi wyznaczonej przez rozkład etykiet (66,6%) — albo poniżej, jeśli
> świadomie rezygnujemy z abstynencji.

---

## Trzy ramiona (ZAMROŻONE)

| ramię | zmiana | mechanizm |
|---|---|---|
| **A0 baseline** | brak | dzisiejszy kod; regresja bit-identyczności + odniesienie |
| **A1 wagi klas** | `class_weight_mode="balanced"` | odwrotność częstości z foldu TRENINGOWEGO; model **nadal może** odmówić — naprawa miękka |
| **A2 wymuszenie** | `direction_policy="forced"` + `confidence_mode="conditional"` | argmax po `{−1,+1}`; abstynencja z konstrukcji = 0% |

**K2 świadomie NIE uruchamia A1+A2** — byłoby czwarte ramię i realne przeszukiwanie (zasada 4).
**Nie rusza T4** (`MIN_VALIDATION_ROWS`/`validation_fraction`) — inny mechanizm, byłby
confounderem; ciąg S1→S1b pokazał, że sam zmienia `n` trzykrotnie.

## Siatka i replikacja

K1 miał **jedno losowanie wyroczni na punkt** — porównanie trzech ramion na takich krzywych
porównywałoby trzy szumy.

| q | losowań | po co |
|---|---|---|
| 0,00 | **12** | specyficzność (veto) + baza T6 |
| 0,10 / 0,20 / 0,30 / 0,40 | **3** | krzywa z rozrzutem, nie punktem |
| 1,00 | 1 | integralność łańcucha |

Wypada q=0,05 (K1: nic nie wniosło), dochodzi q=0,30 (rozdzielczość tam, gdzie leży próg A0).

**Bramka kosztowa, decyzja PRZED obejrzeniem wyniku:** zmierzyć czas jednego przebiegu A0;
przy >4 min/przebieg zejść do 3 losowań przy q=0 i 2 na punkt.

---

## Reguła decyzji — trzy bramki (zapisana PRZED uruchomieniem)

1. **SPECYFICZNOŚĆ — bramka NADRZĘDNA, veto.** Na 12 losowaniach czystego szumu kryterium
   `ci_low > break_even` może wystrzelić **najwyżej raz**, a pooled CI trafności musi
   **zawierać `break_even`**. Ramię kupujące `n` kosztem fałszywych alarmów jest odrzucone
   **bez patrzenia na resztę**. To jedyna bramka, która może zabić kandydata.
2. **INTEGRALNOŚĆ przy q=1,00** — sformułowana **warunkowo na etykiecie, symetrycznie dla
   wszystkich ramion**: trafność na transakcjach o prawdziwej etykiecie ≠ 0 musi wynosić ~100%.
   Bez tego zastrzeżenia A2 oblewałby sanity-check **mechanicznie** (wymusza kierunek na
   świecach timeout, gdzie poprawny kierunek nie istnieje), a ratowanie go po fakcie byłoby
   dorabianiem uzasadnienia. **Dlatego jest zapisane z góry.**
3. **METRYKA WYBORU:** najmniejsze `wald_half_width(n)` przy q=0, raportowane **z rozrzutem**
   po losowaniach, nie jako punkt.

**Rozstrzygnięcie zerowe jest dopuszczalne i zapisane z góry:** jeśli żadne ramię nie przejdzie
bramki 1, K2 kończy się **„brak adopcji"** i to pełnoprawny wynik.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy" (zasada 16a)

- **A2 MUSI podnieść `n`. To tautologia, nie odkrycie.** Abstynencja spada do 0, `n` rośnie
  z ~105 do ~14 000. **Zaraportowanie tego jako sukcesu byłoby oszustwem wobec samego siebie.**
- **A2 jednocześnie MUSI obniżyć `p` i PODNIEŚĆ `break_even`.** Do populacji wchodzą świece
  timeout: ich trafność ≈ rzut monetą, a `|exit−entry|` jest ~3× mniejsze (S1: 0,714% vs
  2,036%), więc `barrier_pct` spada i `BE = 0,5(1+C/B)` rośnie. Szacunek z liczb S1/H2.1:
  **BE z ~52,0% do ~53,4%**, `p` przy q=0,20 z 56,2% do ~53,3%.
- **Dlatego wynik NIE jest przesądzony:** pasmo zwęża się z 9,56 pp do ~0,83 pp, ale
  **przesuwa się w górę**. Czy `ci_low > BE` zapali się przy niższym `q` — to jest przedmiot
  pomiaru, i to odróżnia K2 od rundy napisanej z góry.

## Dlaczego to 0 wariantów

`oracle` ma **znaną z konstrukcji** siłę sygnału — nie ma hipotezy rynkowej do potwierdzenia,
więc nie ma czego p-hackować. Wybór ramienia odbywa się na **syntetycznym** sygnale i jest
podporządkowany bramce specyficzności, która może odrzucić wszystkie. **Warunek utrzymania
zera: żadna liczba z K2 nie może być cytowana jako wynik hipotezy tradingowej.**

## T6 — kill-switch jako źródło obciążenia (ZERO zmian w kodzie)

Niezmiennik: `_collect_candidate_signals` biegnie **przed** pętlą equity i nie przyjmuje
żadnego argumentu zależnego od equity; kill-switch żyje wyłącznie w pętli. Dodatkowo `hit_rate`
jest **niewrażliwa na sizing** (`gross_pnl = direction·(exit−entry)·position_size`,
`position_size > 0` ⇒ znak niezależny). **Kill-switch może więc ruszyć trafność WYŁĄCZNIE przez
skład populacji** — czysty eksperyment selekcyjny.

**Dwie asercje OBOWIĄZKOWE w skrypcie** (bez nich „0,99 znaczy wyłączony" jest cichą konwencją —
klasą błędu, na którą projekt wpadł trzy razy: Z17b, Z9, H3):
1. `trades["kill_switch_active"].sum() == 0` w ramieniu off;
2. klucz `(regime, fold_idx, timestamp)` daje **identyczny zbiór** w obu ramionach.

**Rachunek mocy PRZED uruchomieniem:**

| ramię | n kandydatów (szac.) | wykrywalna różnica (80%) | werdykt z góry |
|---|---|---|---|
| A0, q=0, 12 losowań | ~500–700 | ~9 pp | **NIE ROZSTRZYGNIE** podejrzenia o ~4 pp |
| **A2, q=0, 12 losowań** | **~168 000** | **~0,3 pp** | **ROZSTRZYGNIE** |

**Ograniczenie zapisane z góry:** A2 mierzy mechanizm **w konfiguracji A2**, gdzie przy n≈14 000
krzywa equity jest gładsza. Ramię A0 daje dekompozycję odczytu 54,09% z szerokim CI i wolno je
czytać **wyłącznie jako ograniczenie z góry**. Jeśli A2 pokaże obciążenie nieodróżnialne od zera,
hipoteza „kill-switch jest źródłem" zostaje odrzucona **jako mechanizm**, a 54,09% z K1
przypisane szumowi przy n=220 — i **tak trzeba to napisać, bez awansowania na „udowodniliśmy"**.

---

## Wynik

**Metadane przebiegu**

- **Komenda:** `py -m backtest.run_abstention_fix_k2` (skrypt: `backtest/run_abstention_fix_k2.py`)
- **Walidacja:** `runs/2026-09-22_k2-naprawa-abstynencji/k2_walidacja.py` (kopiowany do korzenia repo)
- **Branch:** `task/K2-naprawa-abstynencji`
- **Siatka:** **PEŁNA** — bramka kosztowa z pre-rejestracji nie uruchomiła się (jeden przebieg
  A0 = **2,9 s** wobec progu 240 s), więc 12 losowań przy q=0 i po 3 na punkt. **75 przebiegów**
  krzywej + 24 przebiegi T6.
- **Dane:** 14 916 świec 4h, 2019-09-10 → 2026-06-30; 14 899 etykiet nie-NaN; udział klasy
  timeout **66,51%**.
- **Pełny stdout:** `raw_output.txt` (wraz z outputem walidacji).
- **Uwaga o odtwarzalności:** po przebiegu funkcja `_pooled` w skrypcie została przepięta na
  `metrics.observed_wald_ci` (usunięcie drugiej kopii wzoru na przedział Walda — lekcja H3).
  Zmiana jest **neutralna dla wyniku**: skrypt uruchomiono ponownie po refaktorze, a output
  porównano z zapisanym `raw_output.txt` (patrz „Przegląd diffu").

### 1. Krzywe wykrywalności — trzy ramiona na tej samej wyroczni

Pooled po losowaniach. „Margines" = trafność − próg opłacalności, w punktach procentowych;
„pasmo" = `wald_half_width(n)`, czyli szerokość obszaru „opłacalne, ale niewidzialne".

| q | ramię | abstynencja | n | trafność | próg BE | **margines** | pasmo | wykryte? |
|---|---|---|---|---|---|---|---|---|
| 0,00 | A0 | 99,63% | 644 | 51,71% | 52,29% | −0,58 pp | 3,86 pp | nie |
| 0,00 | A1 | 43,55% | 97 014 | 50,48% | 52,94% | −2,46 pp | 0,31 pp | nie |
| 0,00 | A2 | 0,00% | 167 160 | 50,33% | 52,94% | −2,60 pp | 0,24 pp | nie |
| 0,10 | A0 | 99,52% | 207 | 53,62% | 51,99% | +1,63 pp | 6,81 pp | nie |
| 0,10 | A1 | 43,93% | 24 158 | 50,79% | 52,93% | −2,14 pp | 0,63 pp | nie |
| 0,10 | A2 | 0,00% | 41 832 | 50,26% | 52,92% | −2,66 pp | 0,48 pp | nie |
| 0,20 | A0 | 99,27% | 315 | 51,43% | 52,22% | −0,79 pp | 5,52 pp | nie |
| 0,20 | A1 | 45,72% | 23 456 | 51,05% | 52,84% | −1,79 pp | 0,64 pp | nie |
| 0,20 | A2 | 0,00% | 42 000 | 50,19% | 52,92% | −2,73 pp | 0,48 pp | nie |
| 0,30 | A0 | 97,78% | 961 | 54,84% | 52,33% | +2,51 pp | 3,16 pp | nie |
| **0,30** | **A1** | **49,47%** | **21 900** | **53,57%** | **52,66%** | **+0,91 pp** | **0,66 pp** | **TAK** |
| 0,30 | A2 | 0,00% | 42 840 | 51,61% | 52,92% | **−1,31 pp** | 0,47 pp | nie |
| 0,40 | A0 | 93,87% | 2 659 | 59,23% | 52,20% | +7,03 pp | 1,90 pp | TAK |
| 0,40 | A1 | 52,53% | 20 575 | 57,25% | 52,34% | +4,91 pp | 0,68 pp | TAK |
| 0,40 | A2 | 0,00% | 43 218 | 53,85% | 52,88% | +0,97 pp | 0,47 pp | TAK |
| 1,00 | A0 | 66,48% | 4 843 | 100,00% | 50,80% | +49,20 pp | 1,41 pp | TAK |
| 1,00 | A1 | 66,48% | 4 843 | 100,00% | 50,80% | +49,20 pp | 1,41 pp | TAK |
| 1,00 | A2 | 0,00% | 14 448 | 65,65% | 52,63% | +13,02 pp | 0,82 pp | TAK |

**Najsłabszy wykryty sygnał: A1 przy q = 0,30; A0 i A2 dopiero przy q = 0,40.** Przy siatce
o kroku 0,10 to jedyne rozróżnienie, jakie wolno z tych danych zrobić — sama wartość „0,30"
jest punktem siatki, nie właściwością przyrządu (to dokładnie poprawka nr 1 z tej
pre-rejestracji, zastosowana do własnego wyniku).

### 2. Bramka 1 (specyficzność, veto) — dwa odczyty, przeciwne werdykty

**Żadne ramię nie podniosło fałszywego alarmu: 0/12 losowań w każdym.** Rozjazd bierze się
wyłącznie z drugiego członu („pooled CI musi zawierać próg"):

| ramię | fałszywe alarmy | pooled n | pooled CI | próg | odczyt DOSŁOWNY | odczyt WG CELU |
|---|---|---|---|---|---|---|
| A0 | 0/12 | 644 | [47,85%; 55,57%] | 52,29% | **ZDANA** | ZDANA |
| A1 | 0/12 | 97 014 | [50,16%; 50,79%] | 52,94% | **ODRZUCONE** | ZDANA |
| A2 | 0/12 | 167 160 | [50,09%; 50,57%] | 52,94% | **ODRZUCONE** | ZDANA |

### 3. Bramka 2 (integralność przy q=1,00) — zdana przez wszystkie trzy

| ramię | n wszystkich | n (etykieta ≠ 0) | trafność **warunkowa** | trafność bezwarunkowa |
|---|---|---|---|---|
| A0 | 4 843 | 4 843 | **100,00%** | 100,00% |
| A1 | 4 843 | 4 843 | **100,00%** | 100,00% |
| A2 | 14 448 | 4 843 | **100,00%** | 65,65% |

Zastrzeżenie warunkowe zapisane w pre-rejestracji **zadziałało dokładnie tak, jak
przewidziano**: A2 wymusza kierunek również na świecach timeout, gdzie poprawny kierunek nie
istnieje, więc jego trafność bezwarunkowa (65,65%) nie jest porażką łańcucha.

### 4. Bramka 3 (metryka wyboru) — najmniejsze pasmo ma A2

| ramię | n na losowanie (min/mediana/max) | pasmo pp (min/mediana/max) | pooled n | pasmo pooled |
|---|---|---|---|---|
| A0 | 24 / 52,5 / 90 | 10,33 / 13,53 / 20,00 | 644 | 3,86 pp |
| A1 | 8 004 / 8 090 / 8 169 | 1,08 / 1,09 / 1,10 | 97 014 | 0,31 pp |
| A2 | 13 860 / 13 944 / 13 944 | 0,83 / 0,83 / 0,83 | 167 160 | **0,24 pp** |

### 5. Abstynencja — cel rundy wyrażony liczbą

Podłoga wyznaczona rozkładem etykiet: **66,51%**.

| ramię | q=0,00 | q=0,10 | q=0,20 | q=0,30 | q=0,40 | q=1,00 |
|---|---|---|---|---|---|---|
| A0 | 99,6% | 99,5% | 99,3% | 97,8% | 93,9% | **66,5%** |
| A1 | 43,6% | 43,9% | 45,7% | 49,5% | 52,5% | **66,5%** |
| A2 | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |

**A0 przy doskonałej wyroczni trafia w podłogę co do 0,03 pp** — potwierdzenie poprawki nr 2
z pre-rejestracji na nowych danych. **A1 schodzi POD podłogę** (43,6% wobec 66,5%), czyli
otwiera pozycje na świecach, które naprawdę są timeoutami.

### 6. T6 — kill-switch NIE jest źródłem obciążenia

| ramię | n (ON) | p (ON) | n (OFF) | p (OFF) | różnica ON−OFF | 95% CI różnicy | werdykt |
|---|---|---|---|---|---|---|---|
| A0 | 644 | 51,71% | 644 | 51,71% | **+0,00 pp** | ±5,46 pp | nierozstrzygające (jak przewidziano) |
| A2 | 167 160 | 50,33% | 173 376 | 50,29% | **+0,04 pp** | ±0,34 pp | **NIEODRÓŻNIALNE OD ZERA** |

Obie asercje obowiązkowe **zdane we wszystkich 24 przebiegach**. W ramieniu A0 kill-switch nie
uruchomił się ani razu (0 stłumionych) — przy ~54 transakcjach na losowanie equity nie zdąży
się poruszyć, więc A0 nie mógł tu niczego rozstrzygnąć, dokładnie jak zapisano z góry.

**A2, które MIAŁO rozstrzygnąć (rozdzielczość ±0,34 pp), rozstrzygnęło: obciążenia nie ma.**
Zgodnie z pre-rejestracją zapisuję to bez awansowania na „udowodniliśmy": hipoteza
„kill-switch jest źródłem" zostaje **odrzucona jako mechanizm**, a odczyt 54,09% z K1
przypisany szumowi przy n=220.

## Co na plus (+) / Co na minus (−)

**(+) Trzy przewidywania z pre-rejestracji sprawdziły się co do mechanizmu.** A2 musiało
podnieść `n` (tautologia — i tak zapisana), obniżyć `p` i podnieść próg opłacalności. Podniosło
`n` 260×, obniżyło `p` z 51,71% do 50,33% i podniosło próg z 52,29% do 52,94%. Kierunek
i rząd wielkości zgadzają się z rachunkiem zrobionym **przed** uruchomieniem.

**(+) Zastrzeżenie warunkowe w bramce 2 uratowało uczciwość porównania.** Gdyby bramkę
sformułowano bezwarunkowo, A2 oblałoby ją mechanicznie (65,65%), a ratowanie go po fakcie
byłoby dorabianiem uzasadnienia. Zapisane z góry — zadziałało.

**(+) Odczyt przyrządu przestał być niemonotoniczny.** Trafność A0 w funkcji siły sygnału idzie
51,71 → 53,62 → 51,43 → 54,84 → 59,23: **niemonotonicznie**, bo przy n rzędu 200–900 dominuje
szum. A1 daje 50,48 → 50,79 → 51,05 → 53,57 → 57,25, czyli ściśle rosnąco. To **nie jest**
kryterium pre-rejestrowane i nie uczestniczy w werdykcie — ale jest najmocniejszą przesłanką,
że A1 mierzy, a A0 zgaduje.

**(+) T6 rozstrzygnięte definitywnie**, i to ramieniem, które pre-rejestracja wskazała jako
zdolne to zrobić.

**(−) DWIE z trzech pre-rejestrowanych bramek okazały się wadliwie sformułowane.** Opis niżej.
To jest główny minus tej rundy i nie da się go zrzucić na dane.

**(−) A2 jest gorsze, niż sugeruje metryka wyboru.** Bramka 3 (najmniejsze pasmo) wskazuje A2,
ale przy q=0,30 A2 ma margines **−1,31 pp**, czyli sygnał realnie informacyjny staje się
nieopłacalny. Pasmo mierzy precyzję, a nie to, czy jest co mierzyć.

**(−) A1 schodzi pod podłogę abstynencji** (43,6% wobec 66,5%). Nie jest więc „kalibracją do
rozkładu etykiet", tylko słabszą wersją tego samego rozcieńczenia, które psuje A2. Różnica jest
ilościowa, nie jakościowa.

**(−) Siatka `q` o kroku 0,10 nie rozróżni A0 od A2** — oba wykrywają dopiero przy 0,40.
Twierdzenie „A2 nie jest lepsze od baseline'u" jest więc słabsze, niż wygląda: wiadomo tylko,
że nie jest lepsze **o co najmniej jeden krok siatki**.

**(−) Wynik dotyczy sygnału SYNTETYCZNEGO.** Wyrocznia jest cechą doskonale zgodną z targetem
w ułamku `q` przypadków — realna cecha nie ma takiej struktury. Przenoszenie „A1 wykrywa q=0,30"
na „A1 wykryje realną cechę o sile X" jest nieuprawnione.

## Walidacja (zasada 16a)

**Werdykt: READY.**

**Przeliczenie kluczowej liczby drugą, niezależną drogą.** Trafność bezwarunkowa A2 przy q=1
(65,65%) pochodzi z journalu. Policzyłem ją niezależnie z **rozkładu etykiet**:
`p = udział_kierunkowych · p_kierunkowe + udział_timeoutów · p_na_timeoutach`.
Wynik: **65,6492% przewidziane vs 65,6492% zmierzone — zgodne co do czwartego miejsca**.
Przy okazji ujawnia mechanizm: **wymuszony kierunek na świecach timeout wygrywa w 48,33%**
przypadków, czyli nieco PONIŻEJ rzutu monetą. To jest liczba, przez którą A2 rozcieńcza sygnał.

Kontrola spójności: udział świec o etykiecie ≠ 0 wśród transakcji A2 wynosi 33,52%, a udział
timeoutów w całym zbiorze etykiet 66,51% — sumują się do 100,03%, czyli zgadzają się w granicach
zaokrąglenia okna walk-forward.

**„Kogo NIE ma w zbiorze" (q=0, losowanie 0, 14 448 ocenionych świec):**

| ramię | ocenione świece | odpadło na abstynencji | bramka pewności | bramka kosztowa | sygnały | stłumione kill-switchem | w próbie |
|---|---|---|---|---|---|---|---|
| A0 | 14 448 | **14 408** | 0 | 0 | 40 | 0 | 40 |
| A1 | 14 448 | 6 255 | 0 | 0 | 8 193 | 69 | 8 124 |
| A2 | 14 448 | 0 | 0 | 0 | 14 448 | 546 | 13 902 |

Bilans lejka domyka się w każdym ramieniu, **zero pominiętych foldów** (0 z 86). Istotne:
**bramka kosztowa i bramka pewności odrzuciły ZERO świec** we wszystkich ramionach, więc
abstynencja jest tu jedynym filtrem o znaczeniu — czyli runda mierzy dokładnie to, co miała
mierzyć, a nie skutek uboczny innego filtra. To jest ten sam rodzaj pytania, który w C2d
ujawnił, że pozorny edge mieszkał w świecach odfiltrowanych.

**Red flag „wynik idealnie potwierdza hipotezę": NIE występuje.** Runda miała pokazać, że
naprawa abstynencji poprawia przyrząd. Wyszło, że jedna naprawa pomaga (A1), druga nie (A2),
a dwie z trzech własnych reguł decyzyjnych są wadliwe. To jest wynik niewygodny, nie wygodny.

**Sprawdzenie podejrzanej równości.** A0 i A1 przy q=1 podają identyczne liczby (n=4 843,
100,00%, abstynencja 66,48%), co mogłoby znaczyć, że wagi klas nie docierają do modelu.
Porównanie journali: **NIE są identyczne** — różnią się `signal_confidence` i wszystkim, co od
niej zależy (wielkość pozycji, PnL, equity). Przy doskonałej wyroczni oba modele wybierają te
same kierunki, ale z inną pewnością. Równość jest więc prawdziwa i wyjaśniona.

## Usterka w dwóch pre-rejestrowanych regułach decyzji

Zgłaszam to jako wynik rundy, nie jako obejście niewygodnego werdyktu.

### Bramka 1, człon B: mierzy nieprecyzyjność, nie specyficzność

Pre-rejestracja żąda, by pooled CI trafności **zawierało** próg opłacalności. Na czystym szumie
prawdziwa trafność to ~50%, a próg ~52,9% — te wielkości są **różne z założenia**. Przedział
zawiera próg wyłącznie wtedy, gdy jest dostatecznie **szeroki**, a szerokość zależy wyłącznie
od `n`. Warunek jest więc równoważny nierówności:

```
z·√(0,25/n) ≥ |p − próg| ≈ 0,029   ⟺   n ≤ ~1 142
```

**To nie jest stwierdzenie o specyficzności ramienia, tylko o jego liczebności** — i można je
wyprowadzić **bez patrzenia na jakiekolwiek dane**. Tak zapisany człon B odrzuca mechanicznie
każde ramię, które ma więcej niż ~1 100 transakcji na szumie, czyli **karze dokładnie to, co jest
celem rundy**. A0 przechodzi go wyłącznie dlatego, że jego CI ma 7,72 pp szerokości.

Cel bramki jest w pre-rejestracji napisany wprost: *„ramię kupujące `n` kosztem fałszywych
alarmów jest odrzucone"*. Fałszywy alarm to `ci_low > break_even`. **Tego nie zrobiło żadne
ramię: 0/12 w każdym.**

### Bramka 3: metryka wyboru ignoruje, czy jest co mierzyć

Najmniejsze pasmo ma A2 (0,24 pp), ale A2 przy q=0,30 ma margines ujemny. Pasmo to połowa
równania — druga połowa to odległość trafności od progu, a ona przy wymuszaniu kierunku maleje.
Pre-rejestracja **przewidziała ten efekt** w sekcji „Arytmetyka oczekiwań", ale nie wpisała go
do metryki wyboru. Wskazanie bramki 3 jest więc formalnie poprawne i merytorycznie mylące.

### Dlaczego poprawienie tego NIE jest p-hackingiem

Obie usterki są **wyprowadzalne a priori**: pierwsza z samej definicji przedziału ufności,
druga z arytmetyki zapisanej w tej samej pre-rejestracji. Żadna nie wymaga znajomości wyniku.
Gdyby ktoś przeczytał te reguły uważnie przed uruchomieniem, zgłosiłby je tak samo. Mimo to
**nie zmieniam reguł po fakcie jednostronnie** — decyzja jest niżej, w Rekomendacji, i wymaga
zgody użytkownika.

## Odstępstwo od pre-rejestracji — T6 (odnotowane, nie ukryte)

Pre-rejestracja mówi: **„T6 — kill-switch jako źródło obciążenia (ZERO zmian w kodzie)"**,
z założeniem, że wyłączenie kill-switcha załatwi `kill_switch_drawdown_pct=0.99`.
Implementacja poszła inaczej: `run_backtest` dostał jawny przełącznik `kill_switch_enabled`.

**Odstępstwo jest zgodne z intencją pre-rejestracji, i dlatego zostało przyjęte.** Ten sam
akapit nazywa konwencję „0,99 znaczy wyłączony" **klasą błędu, na którą projekt wpadł trzy
razy** (Z17b, Z9, H3) — cicha umowa zamiast jawnego przełącznika. Wybór między „zero zmian
w kodzie" a „brak cichej konwencji" rozstrzygnięto na korzyść tego drugiego; przy 0,99
kill-switch nadal *mógłby* zadziałać przy drawdownie > 99%, więc ramię „off" nie byłoby
ściśle wyłączone, tylko bardzo mało prawdopodobne.

**Ścieżka odwrotu:** usunąć parametr `kill_switch_enabled` z `run_backtest` i wrócić do
`kill_switch_drawdown_pct=0.99` w skrypcie rundy. Jedna linia w silniku, dwa testy.

## Przegląd diffu (zasada 16c)

**Stan: implementacja i testy gotowe, przebieg NIE uruchomiony.** Runda ma kod ramion A0/A1/A2
i T6 oraz komplet testów, ale **nie ma jeszcze skryptu uruchomieniowego** (`backtest/run_*k2*.py`),
więc sekcje „Wynik" i dalsze pozostają puste zgodnie z pre-rejestracją.

**Werdykt jednym zdaniem: diff jest poprawny i gotowy do merge'u; zamknięto jedną lukę
(walidacja nazw wariantów dopiero po treningu) i potwierdzono niezależnie bit-identyczność
ramienia A0.**

Co sprawdzono:

- **Bit-identyczność baseline'u (warunek ramienia A0) — zweryfikowana DRUGĄ DROGĄ**, nie samą
  asercją w teście. `run_backtest` z domyślnymi argumentami uruchomiono w drzewie **sprzed K2**
  (`b79795b`) i po K2, a pełne journale porównano bajt po bajcie: **1 280 transakcji,
  `final_equity = 95 126,0168131146`, identyczne MD5**. Kod K2 nie przesunął baseline'u.
- **Zamknięta luka: fail fast.** `direction_policy` i `confidence_mode` były walidowane dopiero
  w `predict_signal`, czyli **po wytrenowaniu pierwszego modelu** — na danych 4h to kilkanaście
  minut do komunikatu o literówce. Silnik waliduje je teraz w tym samym miejscu i z tego samego
  powodu co `timeout_leg` od H3. Reguły **nie zostały skopiowane** do silnika: wydzielono
  `validate_signal_policy` / `validate_class_weight_mode` w `agents/ml_optimizer.py`, z których
  korzystają oba miejsca (lekcja H3: usuwamy klasę błędu, nie instancję).
- **Obie asercje OBOWIĄZKOWE dla T6 są w testach**, nie tylko w planie: ramię „off" ma
  `kill_switch_active.sum() == 0`, a klucz `(regime, fold_idx, timestamp)` daje identyczny zbiór
  w obu ramionach. Dołożony trzeci test pilnuje drugiego filaru interpretacji T6 — że cena
  wejścia/wyjścia i kierunek są identyczne na wierszach wykonanych w obu ramionach, więc
  kill-switch może ruszyć trafność wyłącznie przez skład populacji.
- **Tabela z sprostowania 1 zakotwiczona w teście** (`wald_half_width`: 13,86 pp przy n=50 →
  1,12 pp przy n=7 687). Liczby cytowane w tej pre-rejestracji zgadzają się z kodem co do
  0,01 pp — i od teraz nie mogą się po cichu rozjechać.
- **Strażnik `validation_fraction`** (wagi klas niedozwolone na przeciekającej ścieżce sprzed
  Z17) dostał własny test wraz z kontrolą, że baseline na tej ścieżce **nadal działa** — inaczej
  wyniki C6–C2.13 przestałyby być odtwarzalne.

Czego przegląd NIE obejmuje: jakości samych ramion jako kandydatów do adopcji (to rozstrzyga
przebieg wg trzech bramek), oraz `ruff`/`black` — niedostępne na maszynie (zadanie T2).

### Uzupełnienie po przebiegu

- **Usunięta druga kopia wzoru na przedział Walda.** Skrypt rundy liczył pooled CI własnym
  `z·√(p(1−p)/n)`, identycznym z tym w `compute_hit_rate` — dwie kopie tej samej algebry,
  które mogą się rozjechać bez śladu w diffie. Wzór wydzielony jako
  `metrics.observed_wald_ci`; korzystają z niego oba miejsca. Docstring rozróżnia go od
  `wald_half_width` (ex ante, konserwatywnie przy p=0,5), bo walidacja S1 złapała już raz
  dwie różne stałe na ten sam kwantyl w tym module.
- **Refaktor zweryfikowany jako neutralny dla wyniku:** skrypt uruchomiony ponownie po zmianie,
  output porównany z zapisanym `raw_output.txt` — **142 linie identyczne co do bajtu**
  (ta sama suma MD5). Jedyna pominięta w porównaniu linia to zmierzony czas przebiegu.
- **Nowe testy:** zgodność `observed_wald_ci` z `compute_hit_rate` (dowód jednego źródła),
  zbieżność z `wald_half_width` dokładnie przy p=0,5 i tylko tam, kotwica na opublikowany
  wiersz A2 z tabeli wyżej (50,33% / [50,09%; 50,57%]) oraz NaN dla pustej próby.

Testy: **369/369**.

## Wniosek

Prostym językiem (zasada 17).

**Model milczał, bo milczenie było dla niego opłacalne.** Dwie trzecie świec kończy się
„niczym" (bariera czasowa), więc model, który zawsze mówi „nic się nie wydarzy", myli się
rzadko. Przy słabym sygnale odmawiał kierunku w **99,6%** przypadków — i dlatego wcześniejsze
rundy dostawały po kilkadziesiąt transakcji zamiast tysięcy.

**Sprawdziliśmy dwa sposoby rozruszania go.**

**Pierwszy — wagi klas (A1) — działa.** Polega na tym, że rzadsze odpowiedzi „w górę" i „w dół"
liczą się przy uczeniu więcej, więc model przestaje uciekać w milczenie. Liczba transakcji rośnie
z 644 do 97 tysięcy, a przyrząd zaczyna widzieć **słabszy sygnał niż dotąd**: wykrywa wyrocznię
o sile 0,30, podczas gdy dotychczasowy kod potrzebuje 0,40. Mówiąc wprost: **to samo zjawisko,
którego wcześniej byśmy nie zauważyli, teraz da się zmierzyć.**

**Drugi — wymuszenie kierunku (A2) — nie działa.** Tu model nie ma prawa milczeć: zawsze
obstawia górę albo dół. Transakcji jest 260 razy więcej, ale to złudzenie postępu. Na świecach,
które naprawdę kończą się niczym, wymuszony kierunek wygrywa w **48,33%** przypadków, czyli
nieco gorzej niż rzut monetą. Te przegrane rozcieńczają wynik: trafność spada w stronę 50%,
a próg opłacalności rośnie. Efekt netto: **A2 wykrywa tak samo słabo jak kod sprzed naprawy**,
a przy sile sygnału 0,30 zamienia zjawisko opłacalne w nieopłacalne.

**Osobne pytanie zamknięte: kill-switch nie zawyża trafności.** Podejrzewaliśmy, że mechanizm
awaryjny, odcinający handel po serii strat, może sztucznie podnosić wynik, bo zostawia w próbie
tylko te transakcje, które przetrwały. Pomiar na 12 losowaniach czystego szumu przy 167 tysiącach
transakcji: różnica **+0,04 pp przy dokładności ±0,34 pp**, czyli nieodróżnialna od zera.
Odczyt 54,09% z rundy K1 był po prostu szumem przy małej próbie.

**Rundę psuje własny regulamin.** Dwie z trzech reguł decyzyjnych, spisanych przed
uruchomieniem, okazały się źle sformułowane — w sposób, który dało się wykryć **bez patrzenia
na wyniki**. Pierwsza, literalnie czytana, odrzuca każde ramię mające więcej niż ~1 100
transakcji, czyli karze dokładnie to, co runda miała osiągnąć. Druga wybiera ramię o najwęższym
przedziale pomiaru, nie sprawdzając, czy jest jeszcze co mierzyć — i dlatego wskazuje A2, czyli
ramię najgorsze.

## Rekomendacja

1. **Kandydatem do adopcji jest A1 (wagi klas), nie A2.** Dowody: jako jedyne obniża próg
   wykrywalności o krok siatki, jako jedyne daje monotoniczny odczyt przyrządu, nie podnosi
   fałszywych alarmów (0/12) i zachowuje integralność łańcucha (100% przy doskonałej wyroczni).

2. **DECYZJA DO PODJĘCIA PRZEZ UŻYTKOWNIKA — nie podejmuję jej sam.** Formalny werdykt zależy
   od odczytu bramki 1, a ja wykryłem, że jest ona wadliwie sformułowana:
   - **odczyt dosłowny** → A1 i A2 odrzucone, wynik rundy: **„brak adopcji"** (dopuszczalny
     i zapisany z góry);
   - **odczyt wg celu bramki** („ramię nie może podnosić fałszywych alarmów") → wszystkie trzy
     ramiona czyste, adopcja A1 uzasadniona.

   Rekomenduję **odczyt wg celu, zapisany jawnie jako odstępstwo od litery pre-rejestracji**,
   z uzasadnieniem: usterka jest wyprowadzalna a priori i nie wymaga znajomości wyniku.
   Świadomie NIE proponuję „K3 z poprawionymi bramkami" — przy tych samych ziarnach dałoby
   identyczne liczby, więc byłoby to przepisywanie reguł po fakcie w przebraniu nowej rundy.

3. **Gdyby A1 zostało przyjęte — czego to NIE znaczy.** Nie znaczy, że jakakolwiek hipoteza
   tradingowa zaczyna działać. Znaczy tylko, że przyrząd widzi słabsze zjawiska niż dotąd.
   Warunek utrzymania „0 wariantów" pozostaje w mocy: **żadna liczba z K2 nie może być cytowana
   jako wynik hipotezy tradingowej.**

4. **Bramka 3 do wycofania z użycia jako metryka wyboru.** Samo `wald_half_width(n)` nie
   wystarcza — decyduje relacja marginesu do pasma. Następna runda kalibracyjna powinna
   pre-rejestrować kryterium „najniższe `q`, przy którym `ci_low > break_even`", a pasmo
   raportować obok, jako wielkość opisową.

5. **T6 zamknięte.** Kill-switch skreślony z listy podejrzanych o obciążenie pomiaru. Zadanie
   **T6** w `STATUS.md` (ETAP 3) można zamknąć; 54,09% z K1 przypisane szumowi przy n=220.

6. **Otwarte, niezmierzone:** czy A1 schodzące POD podłogę abstynencji (43,6% wobec 66,5%)
   szkodzi na realnych cechach. Na wyroczni nie szkodzi, ale wyrocznia jest sygnałem
   idealnie zgodnym z targetem — realna cecha nie ma takiej struktury. To pytanie na osobną
   rundę, jeśli A1 wejdzie do użytku.
