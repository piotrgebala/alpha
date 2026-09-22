# K3 — czy adopcja A1 przenosi się z wyroczni na REALNE cechy (2026-09-22)

> **STATUS: ZAMKNIĘTA.** Wszystko do sekcji „Arytmetyka oczekiwań" włącznie zapisano
> **przed napisaniem linijki kodu** (osobny commit `a335a51`). Sekcje od „Wynik" w dół
> dopisano po przebiegu.

## ID testu

**K3** — kalibracja przyrządu. **0 wariantów, POZA wszystkimi licznikami hipotez** (ta sama
rola co K1, K2, Z19, Z9). Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/K3-mierzalnosc-po-A1`
- **Poprzedzający stan (master):** `ab50fa0` (merge A1 — wagi klas przyjęte domyślnie)
- **Warianty:** **0** — patrz „Dlaczego to 0 wariantów".
- **Testy przed rundą:** 371/371.

## Poprzedzające wyniki (zasada 14)

- **K2** (`runs/2026-09-22_k2-naprawa-abstynencji/`) — zmierzyła, że wagi klas obniżają próg
  wykrywalności **na syntetycznej wyroczni**. Ta runda sprawdza, czy to samo dzieje się na
  realnych cechach. K2 sama zapisała to jako otwarte zastrzeżenie w Rekomendacji punkt 6.
- **Adopcja A1** (ADR w `docs/rag/03`) — `DEFAULT_CLASS_WEIGHT_MODE = balanced`. ADR zawiera
  jawne zastrzeżenie: A1 schodzi **poniżej** podłogi abstynencji, a na realnej cesze nie jest
  to zmierzone.
- **S1b** (`runs/2026-09-22_s1b-early-stopping-naprawiony/`) — `n = 345`, werdykt
  **NIEROZSTRZYGALNY** przy klauzuli `n < 925`.
- **H2.1** (`runs/2026-09-22_h2.1-funding-jako-cecha/`) — `n = 98`, werdykt
  **NIEROZSTRZYGNIĘTY** przy klauzuli `n < 1 000`, abstynencja **99,32%**.
- **K1** — próg wykrywalności; **jego liczba „~58%" została sprostowana w K2** jako artefakt
  siatki. Właściwością przyrządu jest `wald_half_width(n)`.
- **Z10** — pooled trafność projektu **50,27%** (n = 7 687). **H3** — próg opłacalności
  **52,69%**.

---

## Pytanie rundy

Dwie konfiguracje dostały werdykt „nierozstrzygnięty" **wyłącznie dlatego, że próba była za
mała** — nie dlatego, że coś zmierzono i wyszło źle. Obie mierzono modelem, który odmawiał
kierunku w 90,5% (S1b) i 99,32% (H2.1) świec.

Po adopcji A1 model tak już nie robi — **na wyroczni**. Pytanie brzmi: **czy na realnych
cechach też?**

To nie jest pytanie o zarabianie. To pytanie o to, czy wolno nam jeszcze cokolwiek mierzyć.

## Konfiguracje (ZAMROŻONE, obie odtworzone bez zmian)

| ID | konfiguracja | skąd | co dała przed A1 |
|---|---|---|---|
| **C1** | bramka reżimu `range`, 4h, V=3, `REVERSION_FEATURES` (4 cechy), walk-forward 60/28/28 | S1b (`run_single_regime_4h.py`) | `n = 345`, abstynencja 90,5% |
| **C2** | **bez bramki reżimu** (`REGIME_ALL`), reszta identyczna z C1 | H2.1 ramię A (`run_funding_feature_h21.py`) | `n = 98`, abstynencja 99,32% |

Każda konfiguracja biegnie w **dwóch ramionach**: `class_weight_mode="none"` (stan sprzed
adopcji) i `"balanced"` (stan po adopcji). Cztery przebiegi, zero nowych parametrów.

**Świadomie NIE dokładam ramienia z funding** (H2.1 ramię B) — licznik H2 jest wyczerpany
i seria zamknięta regułą STOP. Ta runda nie ma prawa go dotykać.

## Czego ta runda NIE raportuje — reguła D (wzorzec z H3, reguła D5)

**Trafność, `ci_low`/`ci_high`, `z_stat`, margines i klasyfikacja NIE są wynikiem tej rundy.**
Trafiają do `raw_output.txt` (zasada 11 jest bezwarunkowa), ale sekcja „Wynik" i decyzja ich
nie używają.

Powód nie jest kosmetyczny. Obie konfiguracje należą do **serii zamkniętych**: C1 do hipotezy
jednoreżimowej 4h (reguła STOP), C2 do hipotezy H2 (licznik 1/1 wyczerpany). Zaraportowanie ich
trafności byłoby **ponownym spojrzeniem na target w zamkniętej serii** — czyli wznowieniem
serii tylnymi drzwiami, bez pre-rejestracji i bez licznika. Runda pyta wyłącznie **„ile decyzji
podejmuje model"**, a to jest wielkość niezależna od tego, czy te decyzje są trafne.

**Jeśli ta runda zacznie raportować trafność — konsumuje wariant w zamkniętej serii, czego
reguła STOP zabrania. Wtedy runda jest nieważna, nie „ciekawa".**

## Co runda raportuje

Wielkości niezależne od targetu:

1. **Lejek w komplecie** — świece ocenione, odpadłe na abstynencji, na bramce pewności, na
   bramce kosztowej, sygnały, stłumione kill-switchem, w próbie (pytanie „kogo NIE ma
   w zbiorze", zasada 16a).
2. **Abstynencja** wobec podłogi wyznaczonej rozkładem etykiet.
3. **`n`** oraz **`wald_half_width(n)`** — szerokość pasma „opłacalne, ale niewidzialne".
4. **`break_even_p`** — wielkość czysto geometryczno-kosztowa (`0,5·(1+C/B)`), niezależna od
   trafności; potrzebna, żeby policzyć punkt 5.
5. **`min_detectable_hit_rate(break_even, n)`** — najniższa PRAWDZIWA trafność, którą przy tej
   próbie dałoby się odróżnić od progu opłacalności.

## Reguła odczytu — zapisana PRZED uruchomieniem

Kotwica nie jest wymyślona, tylko złożona z dwóch **zmierzonych** liczb projektu:

```
luka do zamknięcia = próg opłacalności − zmierzona trafność projektu
                   = 52,69% (H3) − 50,27% (Z10)
                   = 2,42 pp
```

Pasmo `wald_half_width(n)` mówi, czy w ogóle **zobaczylibyśmy** efekt tej wielkości:

| pasmo po A1 | odczyt |
|---|---|
| **< 2,42 pp** | przyrząd widziałby efekt dokładnie zamykający znaną lukę ⇒ konfiguracje wracają do gry **jako mierzalne** |
| **≥ 2,42 pp** | mimo poprawy nadal nie zobaczylibyśmy efektu zamykającego lukę ⇒ poprawa realna, ale niewystarczająca; priorytetem zostaje **T4** |
| **abstynencja nie spada** | **adopcja A1 NIE przenosi się z wyroczni na realne cechy** ⇒ do dopisania jako ograniczenie w ADR (`docs/rag/03`) |

To są **etykiety odczytu, nie bramki** — żadna z nich niczego nie zabija i nie ma tu
zamrożonego progu do przyszłego użytku (lekcja K2: projekt ma już dwa trupy po zamrożonych
progach). Liczba 2,42 pp obowiązuje w tej rundzie i wynika z dwóch opublikowanych pomiarów;
gdy którykolwiek się zmieni, zmieni się i ona.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **`n` MUSI wzrosnąć. To jest bliskie tautologii, nie odkrycie.** Wagi klas obniżają
  abstynencję z konstrukcji, a każda świeca, na której model przestaje milczeć, jest
  kandydatem na transakcję. **Zaraportowanie samego wzrostu `n` jako sukcesu byłoby
  oszustwem wobec samego siebie** — dokładnie ten błąd popełniłoby A2 w K2, gdyby nie
  zapisana z góry arytmetyka.
- **Wynik NIE jest przesądzony**, bo nie wiadomo, **o ile**. Na wyroczni model miał cechę,
  która zna prawdziwą etykietę w ułamku `q` przypadków; przy czterech cechach OHLCV posterior
  może pozostać skolapsowany mimo wag. **Możliwy jest wynik (c) — i byłby ważnym negatywem**,
  bo oznaczałby, że A1 kupiliśmy na syntetyku i nie działa tam, gdzie miało.
- **Więcej transakcji NIE znaczy lepszy pomiar** (wniosek skumulowany 26). Wąskie pasmo przy
  rozcieńczonym sygnale to dokładnie pułapka, w którą wpadło A2. Ta runda nie ma jak tego
  wykryć, bo nie patrzy na trafność — i **to ograniczenie jest zapisane z góry**, a nie
  dopisane po wyniku.
- **Ta runda nie może stwierdzić, że cokolwiek zarabia.** Może stwierdzić najwyżej, że
  pewne pytania wolno znów zadać.

## Dlaczego to 0 wariantów

Runda nie porównuje wariantów hipotezy i **nie patrzy na target**: raportuje liczebność,
abstynencję i geometrię kosztu. Ramiona `none`/`balanced` to stan sprzed i po zmianie, która
**już zapadła** (ADR), a nie dwaj kandydaci do wyboru. **Warunek utrzymania zera: żadna liczba
z K3 nie może być cytowana jako wynik hipotezy tradingowej ani jako powód wznowienia serii
zamkniętej regułą STOP.**

---

## Wynik

**Metadane:** `py -m backtest.run_measurability_k3`, cztery przebiegi, dane 14 916 świec 4h
(2019-09-10 → 2026-06-30), podłoga abstynencji **66,51%**. Pełny stdout: `raw_output.txt`.

### 1. Lejek — kogo NIE ma w zbiorze

| etap | C1 none | C1 balanced | C2 none | C2 balanced |
|---|---|---|---|---|
| ocenione świece | 3 642 | 3 642 | 14 448 | 14 448 |
| **odpadło na abstynencji** | **3 297** | **1 687** | **14 413** | **6 334** |
| bramka pewności | 0 | 0 | 0 | 0 |
| bramka kosztowa | 0 | 0 | 0 | 0 |
| sygnały | 345 | 1 955 | 35 | 8 114 |
| stłumione kill-switchem | 0 | 0 | 0 | 81 |
| **w próbie (`n`)** | **345** | **1 955** | **35** | **8 033** |
| foldy pominięte | 22/85 | 22/85 | 0/86 | 0/86 |

Bilans lejka domyka się we wszystkich czterech przebiegach. **Bramka kosztowa i bramka
pewności odrzuciły ZERO świec** — abstynencja jest jedynym filtrem o znaczeniu, więc runda
mierzy dokładnie to, co miała.

### 2. Abstynencja wobec podłogi (66,51%)

| konfiguracja | runda | zapisane wcześniej | none | balanced | zmiana |
|---|---|---|---|---|---|
| C1 (bramka `range`) | S1b | 90,50% | 90,53% | **46,32%** | −44,21 pp |
| C2 (bez bramki) | H2.1 | — | 99,76% | **43,84%** | −55,92 pp |

### 3. Mierzalność

| konfiguracja | ramię | `n` | próg BE | **pasmo** | min. wykrywalna trafność |
|---|---|---|---|---|---|
| C1 | none | 345 | 52,69% | 5,28 pp | 57,96% |
| **C1** | **balanced** | **1 955** | 53,27% | **2,22 pp** | **55,48%** |
| C2 | none | 35 | 52,43% | 16,56 pp | 68,99% |
| **C2** | **balanced** | **8 033** | 52,93% | **1,09 pp** | **54,03%** |

### 4. Odczyt wg reguły zapisanej PRZED uruchomieniem

Kotwica: luka do zamknięcia = 52,69% − 50,27% = **2,42 pp**.

| konfiguracja | pasmo po A1 | odczyt |
|---|---|---|
| C1 | 2,22 pp | **(a) MIERZALNE** — pasmo węższe niż luka |
| C2 | 1,09 pp | **(a) MIERZALNE** — pasmo węższe niż luka |

**Obie konfiguracje wracają do gry jako mierzalne.** Wynik (c) — „A1 nie przenosi się
z wyroczni" — **nie wystąpił**: abstynencja spadła na realnych cechach jeszcze mocniej niż
na syntetycznych.

## Co na plus (+) / Co na minus (−)

**(+) Ramię `none` odtworzyło liczby opublikowane w dwóch wcześniejszych rundach CO DO SZTUKI.**
C1 dało `n = 345` (S1b: 345) i abstynencję 90,53% (S1b: 90,5%); C2 dało `n = 35` (H2.1 ramię A:
35). To nie było sprawdzane przez porównanie z zapisem — konfiguracje odtworzono z parametrów,
a liczby wyszły same. Mocna kontrola, że mierzymy te same konfiguracje, o których mowa
w archiwum.

**(+) Największy zysk tam, gdzie było najgorzej.** C2 miało pasmo 16,56 pp — czyli sygnał
musiałby dawać ~69% trafności, żeby go w ogóle zobaczyć. Po A1 pasmo to 1,09 pp. Konfiguracja
przeszła z „beznadziejnie niemierzalnej" do „najostrzejszej, jaką projekt kiedykolwiek miał
poza Z10".

**(+) Wynik negatywny był realnie możliwy i nie wystąpił.** Pre-rejestracja dopuszczała, że
przy czterech cechach OHLCV posterior pozostanie skolapsowany mimo wag — bo na wyroczni model
miał cechę znającą odpowiedź. Nie pozostał.

**(−) ROZCIENCZENIE JEST REALNE I ZMIERZONE — to główny minus tej rundy.**

| wariant | udział timeoutów | bariera (`barrier_pct`) | próg opłacalności |
|---|---|---|---|
| C2 none | **37,14%** | 1,5017% | 52,43% |
| C2 balanced | **65,11%** | 1,3824% | 52,93% |

Przed adopcją model **wybierał** świece kończące się na barierze: 37,1% timeoutów wobec 66,5%
w populacji. Po adopcji udział timeoutów równa się populacji — **selektywność znika**. Bariera
maleje, więc próg opłacalności rośnie. To ten sam mechanizm, który zdyskwalifikował A2 w K2,
tylko słabszy.

**(−) Czy ta selektywność niosła informację — TA RUNDA NIE MA JAK ROZSTRZYGNĄĆ.** Reguła D
zakazuje patrzenia na trafność, i słusznie, bo obie konfiguracje należą do serii zamkniętych.
Ale to znaczy, że **nie wiemy, czy 8 033 transakcje są lepszą próbą niż 35, czy tylko większą**.
Ograniczenie było zapisane z góry i nie zostało dopisane po wyniku.

**(−) C1 nadal pomija 22 z 85 foldów.** Bramka reżimu `range` głodzi foldy niezależnie od
abstynencji, a A1 tego nie naprawia — to inny mechanizm. Poprawa dotyczy wyłącznie liczby
decyzji w foldach, które w ogóle ruszyły.

**(−) Próg opłacalności podniósł się w obu konfiguracjach** (52,69→53,27 i 52,43→52,93).
Poprzeczka jest wyżej niż w zapisach S1b/H2.1; pasmo zwęziło się jednak nieporównanie bardziej,
więc netto wychodzi na plus — ale nie jest to czysty zysk.

**(−) Wynik dotyczy dwóch konkretnych konfiguracji na BTC 4h.** Nic nie mówi o innych
interwałach, instrumentach ani zestawach cech.

## Walidacja (zasada 16a)

**Werdykt: READY.**

**Przeliczenie drugą, niezależną drogą.** `n` wzięte NIE z journalu, tylko policzone
z abstynencji funkcją `metrics.expected_trades` — napisaną w K2 dokładnie do tego celu:

| wariant | przewidziane z abstynencji | zmierzone w journalu | różnica |
|---|---|---|---|
| C1 none | 344,9 | 345 | −0,1 |
| C1 balanced | 1 955,0 | 1 955 | 0,0 |
| C2 none | 34,7 | 35 | −0,3 |
| C2 balanced | 8 114,0 | 8 114 | 0,0 |

Różnice poniżej jednej transakcji to zaokrąglenie abstynencji do czterech miejsc. **Domyka to
pętlę z wniosku skumulowanego 19** („liczba obserwacji to nie liczba transakcji"): funkcja,
która powstała, żeby tego błędu nie powtórzyć, właśnie przewidziała próbę z dokładnością do
jednej transakcji.

**Druga kontrola — zgodność z archiwum.** Ramię `none` odtworzyło `n` opublikowane w S1b (345)
i H2.1 ramię A (35). Inny skrypt, inna sesja, te same liczby.

**„Kogo NIE ma w zbiorze":** patrz tabela lejka. Istotne: **bramka kosztowa i bramka pewności
odrzuciły zero świec**, więc żaden filtr poza abstynencją nie wpływa na wynik. C1 pomija
22 z 85 foldów — jednakowo w obu ramionach, więc nie zaburza porównania.

**Red flag „wynik idealnie potwierdza hipotezę": SPRAWDZONY.** Obie konfiguracje wyszły
mierzalne, co wygląda na wynik zbyt czysty. Trzy rzeczy każą go jednak przyjąć: (1) wzrost `n`
był zapisany z góry jako tautologia, więc nie jest odkryciem; (2) runda **znalazła** rzecz
niewygodną — rozcieńczenie populacji i wzrost progu opłacalności; (3) ramię `none` odtworzyło
archiwum, co wyklucza pomyłkę w konfiguracji. Gdyby liczby były zbyt dobre z powodu błędu,
ramię `none` też by się rozjechało.

**Czego walidacja NIE obejmuje:** jakości nowej próby. Reguła D wyklucza to z zakresu rundy.

## Przegląd diffu (zasada 16c)

**Werdykt jednym zdaniem: diff jest poprawny i gotowy do merge'u — jeden nowy skrypt rundy plus
skrypt walidacyjny, zero zmian w kodzie produkcyjnym.**

- `backtest/run_measurability_k3.py` — nowy, buduje na `checkpoint_lib` (zasada 13). Konsumuje
  `metrics.wald_half_width` i `metrics.min_detectable_hit_rate`, **nie ma własnej kopii żadnego
  wzoru** (lekcja H3).
- `runs/2026-09-22_k3-mierzalnosc-po-a1/k3_walidacja.py` — druga ścieżka; liczby wejściowe
  wpisane literałami z `raw_output.txt`, żeby walidacja nie przechodziła przez ten sam kod, co
  wynik.
- **Zero zmian w silniku, metrykach i konfiguracji** — runda tylko mierzy. Testy: **371/371**
  (bez zmian, bo nie zmieniono kodu produkcyjnego).
- `ruff`/`black` — nadal niedostępne na maszynie (zadanie **T2**).

## Wniosek

Prostym językiem (zasada 17).

**Dwa pytania, które odłożyliśmy jako „nie da się zmierzyć", znów da się zmierzyć.**

S1b i H2.1 skończyły się werdyktem „nierozstrzygnięty" nie dlatego, że coś wyszło źle, tylko
dlatego, że model podjął **345** i **35** decyzji. Przy takiej liczbie transakcji przyrząd ma
rozdzielczość 5,3 i 16,6 punktu procentowego — a szukamy efektu wielkości **2,4 punktu**.
To jak ważenie listu na wadze samochodowej.

Po włączeniu wag klas te same konfiguracje dają **1 955** i **8 033** decyzje, a rozdzielczość
poprawia się do **2,2** i **1,1 punktu**. Po raz pierwszy jest **lepsza niż to, czego szukamy**.

**Sprawdzian wiarygodności wypadł pomyślnie.** Ramię „stan sprzed zmiany" odtworzyło liczby
zapisane w archiwum co do sztuki — 345 dla S1b i 35 dla H2.1. Nie porównywałem ich z zapisem
przy liczeniu; wyszły same. To znaczy, że mierzymy naprawdę te konfiguracje, o których mowa.

**Ale jest cena, i trzeba ją powiedzieć wprost.** Przed zmianą model **wybierał** świece: brał
takie, które kończą się wyraźnym ruchem (37% „nierozstrzygniętych" wobec 66,5% w całym
zbiorze). Po zmianie bierze je po równo z populacją — **selektywność zniknęła**. Ruch ceny na
transakcję zmalał, więc próg opłacalności podniósł się o pół punktu.

**Czego ta runda NIE mówi:** czy te 8 033 transakcje są lepszą próbą niż tamte 35, czy tylko
większą. Reguła zapisana przed uruchomieniem zabrania jej patrzeć na trafność — obie
konfiguracje należą do serii zamkniętych i zaglądanie im w wynik byłoby wznowieniem ich
tylnymi drzwiami. **To ograniczenie było znane z góry, nie jest wymówką po fakcie.**

## Rekomendacja

1. **Zapisać jako zamknięte: adopcja A1 przenosi się na realne cechy.** Otwarte zastrzeżenie
   z ADR (`docs/rag/03`, konsekwencja 4) jest **zmierzone i potwierdzone w obie strony**:
   abstynencja spada (dobrze), ale schodzi poniżej podłogi i zabiera selektywność (źle).
   Do dopisania w ADR jako fakt, nie jako ryzyko.

2. **NIE wznawiać S1b ani H2.1.** Obie serie są zamknięte regułą STOP i wyczerpanym licznikiem.
   Fakt, że stały się mierzalne, **nie jest powodem do ich wznowienia** — jest powodem, żeby
   **przyszłe** hipotezy projektować na tym przyrządzie. Wznowienie wymagałoby decyzji
   bramkowej użytkownika i nowego licznika od zera, dokładnie jak każda hipoteza w ETAPIE 4.

3. **Priorytet T4 spada.** Był uzasadniony tym, że próba jest za mała; próba przestała być za
   mała. `MIN_VALIDATION_ROWS`/`validation_fraction` nadal są nieskalibrowane, ale to już nie
   jest wąskie gardło pomiaru.

4. **Nowy, konkretny kandydat na rundę: czy selektywność niosła informację.** Pytanie postawione
   przez tę rundę i przez nią nierozstrzygalne. Można je zadać uczciwie tylko na **nowej**
   hipotezie z własnym licznikiem — porównując na tych samych danych model wybierający świece
   z modelem biorącym wszystkie. To jest realny wybór projektowy, nie usterka.

5. **Zaktualizować rachunek mocy w mapie drogowej.** Każda przyszła runda liczy
   `measurability_report` przed uruchomieniem (sprostowane brzmienie w `STATUS.md`). Od teraz
   ma do tego realne `n`: rzędu 2 000 (z bramką reżimu) i 8 000 (bez niej) na BTC 4h, V=3.
