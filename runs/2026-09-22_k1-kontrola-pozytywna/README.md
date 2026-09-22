# K1 — KONTROLA POZYTYWNA: aparat działa, ale widzi dopiero sygnał trzykrotnie silniejszy, niż trzeba do zarabiania (2026-09-22)

## W skrócie — prostym językiem (zasada 17)

**Po co ta runda.** Ten projekt wyprodukował **15 wyników negatywnych albo nierozstrzygniętych
i ani razu nie sprawdził, czy jego własny przyrząd pomiarowy w ogóle potrafi zobaczyć sygnał,
o którym wiadomo, że tam jest.** To jak wielokrotne mierzenie gorączki termometrem, którego
nikt nie przyłożył do wrzątku.

**Jak to sprawdziliśmy.** Do prawdziwych danych BTC dorzuciliśmy sztuczną podpowiedź, która
z zadaną skutecznością zdradza przyszłość. Potem puściliśmy **niezmieniony program** i sprawdzili,
przy jakiej sile podpowiedzi zaczyna ją widzieć.

**Trzy odpowiedzi, wszystkie ważne:**

**1. Przyrząd działa.** Przy podpowiedzi doskonałej program znalazł ją bezbłędnie — trafność
100,00% na 4 843 transakcjach. Nic po drodze nie gubi sygnału. **To był główny powód tej rundy
i wynik jest dobry.**

**2. Nasze kryterium oceny jest uczciwe.** Reguła, której używaliśmy we wszystkich werdyktach,
**ani razu nie dała fałszywego alarmu na czystym szumie** (0 na 6 losowań). Wszystkie
dotychczasowe wnioski, które się na niej opierały, są wiarygodne.

**3. Ale przyrząd jest gruboziarnisty — i to jest nowa wiedza.** Zaczyna widzieć dopiero
podpowiedź trafiającą w **59%** przypadków. Przy słabszej **model przestaje handlować**
(odmawia w 99,3–99,7% świec), więc transakcji jest kilkadziesiąt i nic nie da się udowodnić.

> **Najważniejsze zdanie tej rundy:** żeby zarabiać, wystarczy trafność **~53%**. Żeby nasz
> program to **zobaczył**, potrzeba sygnału dającego **~58%**. **Między tymi liczbami jest
> luka, w której sygnał byłby opłacalny, ale dla nas niewidzialny.**

**Co to znaczy dla wcześniejszych wyników.** Nie unieważnia ich — zawęża. Nasze „nie ma
sygnału" znaczy dokładnie: „nie ma sygnału dość silnego, żeby ten program go zobaczył".
Zamknięcie Fazy 0 pozostaje mocne, bo jego liczba pochodziła z **7 687 transakcji**, gdzie
przyrząd jest dokładny. Słabiej stoją te wyniki, gdzie transakcji było kilkaset.

**I jeszcze jedno, znalezione przy okazji:** wbudowany „werdykt GO/NO-GO" **wystawił ocenę
GO czystemu szumowi**. Potwierdza to, co podejrzewałem w H2.1. Tej miary nie wolno cytować.

---

## ID testu

**K1** — kalibracja przyrządu. **0 wariantów, poza wszystkimi licznikami hipotez** (to nie jest
test hipotezy tradingowej, tak samo jak Z19 czy Z9). Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/K1-kontrola-pozytywna`
- **Poprzedzający stan (master):** `e1d5b63` (merge H2.1)
- **Komenda:** `py -m backtest.run_positive_control_k1` + `k1_null.py` (`raw_output.txt`)
- **Dane:** prawdziwe BTC 4h, 14 916 świec — **te same, na których biegły S1/S1b/H2.1**
- **Pipeline:** **NIEZMIENIONY** — bez bramki reżimu, V=3, 60/28/28, seed 42
- **Warianty:** **0** — kalibracja aparatu, nie test hipotezy
- **Testy:** 319/319

## Poprzedzające wyniki (zasada 14)

- **Z17 / Z17b / Z9** — trzy udokumentowane przypadki, w których pipeline **po cichu psuł
  pomiar**: przeciek early stopping (zawyżał `p` o 0,7 pp), martwy próg walidacji (wyłączał
  mechanizm w 92% foldów), resample psujący wolumen (11% świec 1h). **Wszystkie trzy wykryto
  ręcznym audytem albo przypadkiem — żadnej przez test.** To jest bezpośrednia motywacja K1.
- **H2.1** — `classify_checkpoint` zwrócił GO przy 3 i 11 ważnych foldach; podejrzenie, że ta
  miara jest niewiarygodna. **K1 je potwierdza w mocniejszej formie.**
- **Z10** — liczba zamykająca Fazę 0 (pooled `p` = 50,27% na n=7 687). K1 określa, **na ile tę
  liczbę można było w ogóle zmierzyć**.
- **C2.12** — patologia per-fold `mean_sharpe` przy małym n.

## Metoda

Do prawdziwych świec wstrzykujemy jedną syntetyczną cechę `oracle`:

```
z prawdopodobieństwem q:    oracle = prawdziwa etykieta triple-barrier
z prawdopodobieństwem 1−q:  oracle = losowa etykieta z {−1, 0, +1}
```

`q = 0` to **kontrola negatywna** — cecha bez informacji (zgodność z etykietą ~33% przez
przypadek). Aparat **nie ma prawa** niczego tam znaleźć. `q = 1` to wyrocznia doskonała.

`oracle` **nie wchodzi** do `feature_registry.yaml` i nie ma prawa pojawić się w żadnej
rundzie hipotezowej — istnieje wyłącznie w tym skrypcie.

---

## Wynik 1 — krzywa wykrywalności

| q | zgodność cechy z etykietą | abstynencja | n transakcji | trafność | CI_low | próg | margines | `classify_checkpoint` |
|---|---|---|---|---|---|---|---|---|
| **0,00** | 33,7% (szum) | 99,7% | 50 | 54,00% | 40,19% | 51,37% | +2,63 pp | ⚠️ **WARUNKOWY** |
| 0,05 | 36,7% | 99,5% | 69 | 47,83% | 36,04% | 51,57% | −3,74 pp | ⚠️ WARUNKOWY |
| 0,10 | 40,3% | 99,5% | 69 | 55,07% | 43,34% | 51,85% | +3,23 pp | ⚠️ **GO** |
| 0,20 | 46,3% | 99,3% | 105 | 56,19% | 46,70% | 51,90% | +4,29 pp | ⚠️ WARUNKOWY |
| **0,40** | **59,4%** | 94,6% | **787** | **58,20%** | **54,75%** | 52,08% | **+6,12 pp** | **GO** ✔ |
| 1,00 | 99,9% | 66,5% | 4 843 | **100,00%** | 100,00% | 50,80% | +49,20 pp | GO ✔ |

### Co z tego wynika

**Aparat DZIAŁA.** Przy wyroczni doskonałej mierzy **100,00%** trafności na 4 843
transakcjach. Cały łańcuch — cechy, etykiety, walk-forward, trening, próg pewności, bramka
kosztowa, kill-switch, metryki, werdykt — **przenosi sygnał bez strat**. To był główny powód
tej rundy i odpowiedź jest twierdząca.

**Próg wykrywalności to `q = 0,40`, czyli zgodność cechy z etykietą 59,4%.** Poniżej tej siły
kryterium pre-rejestrowane nie przebija progu opłacalności.

**Wąskim gardłem jest ABSTYNENCJA, nie brak sygnału.** Przy `q = 0,20` (zgodność 46,3% — sygnał
realny i spory) trafność punktowa wyniosła **56,19%**, czyli **powyżej progu opłacalności
51,90%**. Ale `n = 105`, więc przedział ufności sięga 46,70% i nic nie da się orzec.
**Sygnał tam BYŁ i był ekonomicznie wystarczający — aparat go nie udowodnił.**

> ### Luka, której projekt nie znał
>
> | | trafność |
> |---|---|
> | próg opłacalności (ile trzeba, żeby zarabiać) | **~52,7%** |
> | próg wykrywalności (ile trzeba, żeby ten pipeline to udowodnił) | **~58,2%** |
> | **luka** | **~5,5 pp** |
>
> **Sygnał w tej luce byłby opłacalny, a dla nas niewidzialny.** To nie jest wada pomiaru
> „w ogóle" — to wada TEGO pipeline'u przy TEJ abstynencji.

## Wynik 2 — kontrola negatywna (6 niezależnych losowań czystego szumu)

| losowanie | n | trafność | próg | margines | kryterium pre-rejestrowane przebite? |
|---|---|---|---|---|---|
| 0 | 54 | 46,30% | 51,28% | −4,98 pp | NIE |
| 1 | 21 | 52,38% | 52,47% | −0,09 pp | NIE |
| 2 | 40 | 62,50% | 52,70% | +9,80 pp | NIE |
| 3 | 31 | 54,84% | 52,56% | +2,28 pp | NIE |
| 4 | 47 | 53,19% | 52,89% | +0,31 pp | NIE |
| 5 | 27 | 59,26% | 52,19% | +7,07 pp | NIE |

**Pooled: n = 220, trafność 54,09%, z = +1,214 wobec H₀ = 50% → NIEISTOTNE.**
95% CI [47,48%; 60,70%] zawiera 50%.

### Odczyt — dwie rzeczy, jedna dobra i jedna niepokojąca

**DOBRA: kryterium pre-rejestrowane nie dało ani jednego fałszywego alarmu — 0 na 6.**
To jest reguła (`ci_low > break_even`), na której opierają się WSZYSTKIE werdykty w tym
projekcie. **Jest uczciwa.** To bezpośrednio uwiarygodnia Z10, S1, C2.13 i całą serię.

**NIEPOKOJĄCA: punktowa trafność na czystym szumie wyniosła średnio 54,09%, nie 50%.**
Formalnie nieistotne (z = +1,21), ale **próba jest za mała, żeby obciążenie wykluczyć** —
przy n=220 dopiero różnica ~7 pp byłaby wykrywalna. Kandydat na wyjaśnienie: **kill-switch
jest selekcją zależną od ścieżki** — transakcje, które przegrywają najmocniej, wyzwalają go
i tłumią kolejne, co podnosi trafność wśród tych, które przeżyły. Walidacja S1 zmierzyła
ten efekt jako +0,30 pp przy n=1 037; przy n≈37 mógłby być wielokrotnie większy.

**To jest niedokończone i tak to zapisuję.** Rozstrzygnięcie wymaga przebiegu z wyłączonym
kill-switchem — osobna runda.

## Wynik 3 — `classify_checkpoint` wystawił GO czystemu szumowi

| q | zgodność | `n_valid_folds` | werdykt |
|---|---|---|---|
| 0,00 (czysty szum) | 33,7% | — | **WARUNKOWY** |
| 0,10 (prawie szum) | 40,3% | — | **GO** |

Podejrzenie z H2.1 potwierdzone w mocniejszej formie: tam GO powstało przy 3 i 11 ważnych
foldach na realnych danych; tutaj powstaje **na danych, w których z konstrukcji nie ma czego
znaleźć**.

> **Wniosek wiążący: `classify_checkpoint` NIE JEST kryterium werdyktu i nigdy nim nie był.**
> Projekt słusznie przeszedł na `ci_low > break_even` (C2.12, wytyczna miękka CLAUDE.md).
> K1 dostarcza dowodu, którego wtedy nie było. **Żadnej wartości GO/WARUNKOWY/NO-GO nie wolno
> cytować bez podania `n_valid_folds`.**

---

## Co to robi z 15 poprzednimi wynikami

**Nie unieważnia ich. Zawęża ich treść — i trzeba to powiedzieć precyzyjnie.**

| runda | n transakcji | czy K1 podważa? |
|---|---|---|
| Z17+Z21 (5m, `range`) | **7 043** | **NIE** — przy tym n aparat jest dokładny |
| Z10 (liczba zamykająca) | **7 687** | **NIE** — to jest fundament zamknięcia Fazy 0 |
| C2.10–C2.13 (5m) | tysiące | NIE |
| S1 (4h) | 1 037 | **Częściowo** — blisko progu wykrywalności |
| S1b (4h) | 345 | **TAK** — poniżej progu; werdykt „nierozstrzygnięty" był słuszny |
| H2.1 | 98 | **TAK** — głęboko poniżej; „nierozstrzygnięty" był słuszny |

**Zamknięcie Fazy 0 pozostaje mocne**, bo jego liczba pochodzi z 7 687 transakcji. Wszystkie
werdykty „nierozstrzygnięty" okazują się **trafne z powodu, którego wtedy nie znaliśmy**:
nie tylko próba była za mała na istotność, ale była poniżej progu wykrywalności aparatu.

**Nowe, czego nie wiedzieliśmy:** hipoteza dająca trafność 53–58% zostałaby przez ten pipeline
**odrzucona jako „brak sygnału"**, mimo że byłaby opłacalna. Żadna z przebadanych hipotez nie
zbliżyła się do tego pasma (wszystkie ~50%), więc **praktycznie nic nam to nie zmienia
wstecz** — ale zmienia, co wolno mówić o przyszłych rundach.

## Co na plus (+)

- **Pytanie, które powinno paść pierwsze, w końcu padło** — i odpowiedź jest w większości dobra:
  aparat działa, kryterium jest uczciwe.
- **Krzywa zamiast zaliczone/niezaliczone.** Wiemy nie tylko ŻE działa, ale **od jakiej siły
  sygnału** — a to jest liczba użyteczna przy projektowaniu każdej następnej rundy.
- **Kontrola negatywna wbudowana w projekt rundy**, nie dopisana po fakcie: `q = 0` był
  w zestawie od początku, a przy podejrzanym odczycie (+2,63 pp) natychmiast powtórzyłem go
  na 6 niezależnych losowaniach, zamiast uznać za szum.
- **Dowód na `classify_checkpoint`**, którego projekt nie miał, gdy tę miarę odstawiał.
- **Kosztowało 0 wariantów** i nie dotknęło żadnego licznika hipotez.

## Co na minus (−)

- **Ta runda powinna była być pierwsza, nie siedemnasta.** Piętnaście wyników negatywnych
  powstało na przyrządzie, którego nikt nie skalibrował. Że wyszło dobrze, jest szczęściem,
  nie zasługą procesu.
- **Obciążenie na szumie (54,09%) pozostaje NIEROZSTRZYGNIĘTE** — z = +1,21 nie wyklucza
  obciążenia do ~7 pp. Ironia jest podwójna: **kontrola negatywna cierpi na dokładnie tę samą
  chorobę co badane hipotezy** — abstynencja modelu daje n≈37 na losowanie, więc przyrząd nie
  potrafi porządnie zwalidować sam siebie.
- **`oracle` jest wyrocznią wobec ETYKIETY, nie wobec rynku.** Mierzy więc tor
  „cecha → model → transakcja → metryka", a **nie** to, czy etykieta triple-barrier dobrze
  opisuje zarabianie. Ta druga sprawa pozostaje niesprawdzona.
- **Jedna konfiguracja** (4h, V=3, bez bramki). Próg wykrywalności przy innym `V` albo
  interwale będzie inny i nie został zmierzony.
- **Nie sprawdziłem hipotezy o kill-switchu** jako źródle obciążenia — to najbardziej naturalne
  wyjaśnienie i zostaje otwarte.

## Walidacja (zasada 16a) — werdykt: **CAVEATS**

- **Kluczowa liczba przeliczona drugą drogą:** podejrzany odczyt przy `q = 0` (+2,63 pp
  marginesu) **nie został przyjęty ani odrzucony na oko** — powtórzony na 6 niezależnych
  losowaniach szumu i zbadany testem istotności (pooled n=220, z=+1,214, CI zawiera 50%).
- **Kogo NIE ma w zbiorze:** (a) przy słabych sygnałach **99,3–99,7% świec** nie daje
  transakcji — krzywa opisuje zachowanie aparatu na **garstce** przypadków, które przeszły;
  (b) tylko BTC, tylko 4h, tylko V=3, tylko `REVERSION_FEATURES` + `oracle`; (c) `oracle` jest
  wyrocznią wobec etykiety, nie wobec rynku; (d) kontrola negatywna ma **n=220 łącznie**, co
  wykrywa dopiero obciążenie ~7 pp — mniejszego **nie wyklucza**; (e) sześć losowań szumu to
  mała próba na ocenę rozkładu.
- **Red-flag „wynik idealnie potwierdza hipotezę":** **zachodzi i jest obsłużony.** Runda
  miała pokazać, że aparat działa — i pokazała. Dlatego szukałem dowodów PRZECIW: kontrola
  negatywna, test istotności obciążenia, jawne wypisanie luki wykrywalności i fałszywego GO.
  **Runda kończy się trzema zastrzeżeniami wobec własnego pipeline'u**, nie czystym zaliczeniem.
- **Dlaczego CAVEATS:** główne pytanie ma odpowiedź twardą (aparat działa, kryterium uczciwe),
  ale dwa poboczne zostają otwarte — obciążenie na szumie i jego przyczyna.

## Wniosek

**Aparat pomiarowy tego projektu działa, a kryterium, na którym opierają się jego werdykty,
jest uczciwe.** Przy wyroczni doskonałej pipeline mierzy 100,00% trafności; na czystym szumie
kryterium `ci_low > break_even` nie dało ani jednego fałszywego alarmu na 6 prób.

**Ale aparat jest gruboziarnisty w sposób, którego projekt nie znał:** zaczyna widzieć sygnał
dopiero przy trafności około **58%**, podczas gdy do zarabiania wystarcza **~53%**. W tej
pięciopunktowej luce mieści się hipoteza opłacalna i dla nas niewidzialna. Przyczyną jest
**abstynencja modelu** — przy słabym sygnale odmawia działania w 99,3% świec, więc próba nie
pozwala niczego dowieść.

To nie unieważnia dotychczasowych wyników — **Z10 stoi na 7 687 transakcjach, gdzie aparat
jest dokładny**. Ale ustawia granicę tego, co wolno twierdzić: nasze „nie ma sygnału" znaczy
**„nie ma sygnału dość silnego, by ten pipeline go zobaczył"**.

## Rekomendacja

1. **Zapisać próg wykrywalności jako stałą projektu.** Każda przyszła runda musi podać, czy
   jej hipoteza mieści się powyżej ~58% zakładanej trafności — inaczej jest niemierzalna
   z góry, niezależnie od ilości danych.
2. **`classify_checkpoint` formalnie zdegradowany do diagnostyki.** Wystawił GO czystemu
   szumowi. Nie wolno go cytować bez `n_valid_folds`; wpis do `docs/rag/03` i `runs/INDEX.md`.
3. **Abstynencja awansuje na problem numer jeden.** To ona, a nie brak sygnału, ograniczyła
   S1b (345), H2.1 (98) i samą kontrolę negatywną (n≈37). Kandydaci na osobną rundę:
   wagi klas w XGBoost, kalibracja `MIN_VALIDATION_ROWS`/`validation_fraction` (zadanie T4),
   wymuszenie kierunku zamiast trzeciej klasy.
4. **Zbadać kill-switch jako źródło obciążenia** na szumie (przebieg z wyłączonym
   kill-switchem) — najbardziej naturalne wyjaśnienie odczytu 54,09%, dziś niepotwierdzone.
5. **Decyzja o kierunku projektu pozostaje przy użytkowniku** i K1 jej nie zmienia — zmienia
   natomiast jej podstawę: zamknięcie Fazy 0 jest teraz **lepiej uzasadnione**, bo wiemy, że
   przyrząd, który je wyprodukował, działa.

## Pełny surowy output

[`raw_output.txt`](raw_output.txt) · dane krzywej: [`krzywa_wykrywalnosci.csv`](krzywa_wykrywalnosci.csv) ·
skrypty: [`backtest/run_positive_control_k1.py`](../../backtest/run_positive_control_k1.py), [`k1_null.py`](k1_null.py)
