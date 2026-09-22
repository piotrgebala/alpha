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

*(do wypełnienia po przebiegu)*

## Co na plus (+) / Co na minus (−)

*(do wypełnienia po przebiegu)*

## Walidacja (zasada 16a)

*(do wypełnienia — werdykt Ready / Caveats / Revision)*

## Przegląd diffu (zasada 16c)

*(do wypełnienia przed merge)*

## Wniosek / Rekomendacja

*(do wypełnienia po przebiegu)*
