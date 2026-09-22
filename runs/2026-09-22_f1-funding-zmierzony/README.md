# F1 — funding po raz pierwszy na próbie zdolnej cokolwiek rozstrzygnąć (2026-09-22)

> **STATUS: ZAMKNIĘTA — WYNIK NEGATYWNY.** Wszystko do sekcji „Czego ta runda NIE
> rozstrzygnie" włącznie zapisano **przed napisaniem linijki kodu** (osobny commit `dbd92bc`).
> **Licznik F: 1/1 — WYCZERPANY, reguła STOP.**

## ID testu

**F1** — pierwszy wariant **NOWEJ HIPOTEZY F**. Własny licznik od zera (wniosek skumulowany 13),
własna reguła STOP, własna pre-rejestracja. **Nie dziedziczy budżetu ani progów po Fazie 0,
po H2, ani po M.**

## Metadane

- **Branch:** `task/F1-funding-zmierzony`
- **Poprzedzający stan (master):** `2abca35` (merge M1)
- **Warianty:** **1** — wyczerpuje licznik F (0/1 → 1/1).
- **Testy przed rundą:** 390/390. **Bramka leakage dla funding: 6/6 ZIELONA**
  (`test_funding_feature_no_leakage_truncate_vs_extend` i pokrewne) — zasada 2 spełniona
  PRZED wejściem cechy do modelu.

## Dlaczego H2 zostaje zamknięte, a to jest NOWA hipoteza

Licznik H2 jest **wyczerpany 1/1**, a serię zamknęła reguła STOP. **Nie obchodzę tego i nie
wznawiam H2.** Pytanie wraca jako nowa hipoteza z własnym licznikiem — dokładnie tą drogą,
którą kilka godzin temu przeszło momentum (hipoteza M).

Uzasadnienie jest to samo i opiera się na czterech faktach z archiwum:

1. **H2.1 nie odpowiedziało na pytanie.** Werdykt brzmiał **NIEROZSTRZYGNIĘTY**, z jednego
   konkretnego powodu: `n = 98 < 1 000`. Własna reguła projektu mówi wtedy: *„nie
   interpretujemy w żadną stronę"*. **Nierozstrzygnięcie nie jest negatywem.**
2. **Przeszkoda była instrumentalna, nie informacyjna.** Model odmawiał kierunku
   w **99,32%** świec. To nie funding zawiódł — zawiódł przyrząd.
3. **Przeszkoda została zmierzona i usunięta.** K2 → adopcja A1 → K3: na tej samej
   konfiguracji abstynencja 99,76% → 43,84%, próba **35 → 8 033**, pasmo 16,56 pp → 1,09 pp.
4. **Precedens M1 jest świeży i jednoznaczny.** Momentum było w identycznej sytuacji
   (niewykonalność pomiaru, nie brak edge'u), dostało nową hipotezę z licznikiem od zera
   i **zostało rozstrzygnięte**.

## Dlaczego akurat funding — i dlaczego to ostatni taki kandydat

**Wniosek skumulowany 11** wskazuje kierunek: `p` może ruszyć **nowy zbiór informacyjny**, a nie
kolejna transformacja OHLCV. **M1 ten wniosek wzmocnił** — momentum, ostatnia nieprzetestowana
gałąź OHLCV, wypadło przy 50%.

**P1** (`runs/2026-09-22_p1-sonda-zrodel-danych/`) sprawdziło, co jeszcze jest do wzięcia.
Wszystkie pięć endpointów pozycjonowania Binance — open interest, long/short ratio, pozycje
top traderów — oddaje **30,8 dnia** historii, a jawny `startTime` sprzed lat zwraca **HTTP 400**.
To **112 transakcji** wobec wymaganych 4 481: brakuje **40×**.

**Funding zostaje jako jedyne źródło spoza OHLCV, które projekt ma z wystarczającą historią**
(7 457 rozliczeń, 6,8 roku, zero dziur) — i którego nigdy nie zmierzył.

## Konfiguracja (ZAMROŻONA) i ramiona

Identyczna z H2.1, **z jedną różnicą: wagi klas `balanced`** (A1, przyjęte 2026-09-22).
To właśnie ta różnica czyni pomiar wykonalnym.

- **interwał** 4h, **V** = 3, **bramka reżimu** BRAK (`REGIME_ALL`)
- walk-forward **60/28/28**, seed **42**, historia **6,8 roku**
- funding doklejany przez `attach_funding_rate` (`merge_asof(direction="backward")`)

| ramię | cechy | warianty | rola |
|---|---|---|---|
| **A** (odniesienie) | `REVERSION_FEATURES` (4) | **0** | punkt odniesienia w tej samej konfiguracji |
| **B** (kandydat) | 4 + **`funding_rate`** | **1 — WYCZERPUJE licznik F** | przedmiot rundy |

**Dokładnie JEDNA zmienna** (zasada 4): obecność cechy `funding_rate`. Ramię A za 0 wariantów
wg uzasadnienia z H2.1 i M1: **próg opłacalności pochodzi z geometrii kosztu, a nie z obejrzanej
trafności**, więc pomiar odniesienia nie może przesunąć poprzeczki.

## Rachunek mierzalności (zasada 18)

Oczekiwane `n` ≈ **8 000** (K3 i M1 zmierzyły 8 033 i 8 512 na tej konfiguracji); próg
opłacalności ≈ **52,93%**; pasmo ≈ **1,09 pp**.

**Powtarzam ograniczenie z M1, bo obowiązuje tak samo:** wykrywalność zaczyna się od
**≈ 54,0%**. **Tej rundzie NIE wolno obiecywać odpowiedzi „funding działa"** — żeby to orzec,
funding musiałby wynieść trafność powyżej czegokolwiek, co ten projekt kiedykolwiek zmierzył.

**Pytanie odwrotne jest mierzalne z zapasem:** `required_trades` wobec progu przy trafności
rzędu 50–51% daje ~4 500, a mamy ~8 000 — **około 1,8× wymaganej próby przy mocy 80%**.
Runda ma moc orzec, że **funding nie wynosi trafności do progu opłacalności**.

**Dlatego runda startuje:** żeby zamienić „nie wiadomo" na liczbę — nie żeby znaleźć edge.

## Kryterium — zapisane PRZED uruchomieniem

- **POZYTYWNY:** `ci_low(p_B) > break_even_B`. Byłby to **pierwszy dodatni wynik w historii
  projektu**. Nie uruchamia niczego poza **szukaniem przecieku**, a dopiero potem replikacją
  na innym instrumencie (zasada 9). Żadnego wdrożenia.
- **NEGATYWNY:** `ci_high(p_B) < break_even_B` — funding nie wynosi trafności do progu.
- **NIEROZSTRZYGNIĘTY:** `n_B < 4 481` **albo** CI przecina próg. Wtedy **nie interpretujemy
  w żadną stronę** — precedens S1b, H2.1.
- **REGUŁA STOP:** jeden wariant. Po nim seria F zamknięta **niezależnie od wyniku**.

**Dodatkowo raportuję — jako obserwację, NIE kryterium:** różnicę `p_B − p_A` z przedziałem
ufności. M1 pokazało, dlaczego to konieczne: bez tego kusi napisać „funding wypadł lepiej",
gdy różnica jest szumem.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **Spodziewam się wyniku negatywnego.** Prior jest niski: wniosek 11 mówi, że nowy zbiór
  informacyjny **może** ruszyć `p`, a nie że ruszy. Funding jest **następny w kolejce**,
  a nie **rokujący**.
- **Jedyne ustalenie H2.1 dotyczyło LICZBY DECYZJI, nie trafności:** funding potroił je
  z 35 do 98. Model uznał go za informacyjny — ale „model chętniej działa" **nie znaczy**
  „model działa lepiej". Gdyby F1 znów pokazało wzrost `n` i nic więcej, byłoby to
  **powtórzeniem tego samego nieustalenia**, a nie wynikiem.
- **Wzrost `n` w ramieniu B jest więc SPODZIEWANY i sam w sobie nie jest odkryciem.**
  Zaraportowanie go jako sukcesu byłoby powtórzeniem błędu, przed którym K2 ostrzegało przy A2.
- **Świece sprzed pierwszego rozliczenia funding mają NaN** i wypadają jak rozbieg każdego
  wskaźnika. Liczbę odrzuconych świec raportuję jawnie w lejku.
- **Wynik pozytywny traktuję z podejrzliwością proporcjonalną do niezwykłości.** Funding to
  dana o **własnej siatce czasowej** (co 8h wobec świec 4h), więc jest to dokładnie ten typ
  cechy, przy którym przeciek jest najłatwiejszy. Bramka leakage jest zielona, ale przy
  wyniku pozytywnym pierwszym krokiem jest **ponowne sprawdzenie przyczynowości**, nie
  ogłoszenie.

## Czego ta runda NIE rozstrzygnie

- **Funding jako carry** (4A) — inne sformułowanie, odrzucone w H2.0 rachunkiem mocy na
  jednym instrumencie; żyje wyłącznie w wymiarze przekrojowym.
- **Funding jako bramka** (skrajne stawki) — odrzucony w H2.0, zagładza próbę.
- **Inne transformacje funding** (z-score, okna) — H2.0 zawęziło do surowej stawki
  z trzech powodów; reguła STOP zamyka serię po jednym wariancie.
- **ETH/SOL/BNB, inny target, dźwignia** — poza zakresem.

---

## Wynik

**Komenda:** `py -m backtest.run_funding_measured_f1`. Dane: 14 916 świec 4h, 7 457 rozliczeń
funding, 2 świece z NaN (sprzed pierwszego rozliczenia). Pełny stdout: `raw_output.txt`.

| ramię | cechy | `n` | trafność | CI 95% | próg BE | margines |
|---|---|---|---|---|---|---|
| **A** (odniesienie) | 4 OHLCV | 8 033 | 50,37% | [49,27%; 51,46%] | 52,93% | −2,57 pp |
| **B** (kandydat) | 4 + **funding** | **8 127** | **50,34%** | **[49,25%; 51,43%]** | 52,94% | **−2,60 pp** |

### Werdykt wg kryterium zapisanego PRZED uruchomieniem

| | |
|---|---|
| wymagane `n` do orzeczenia negatywu (moc 80%) | 4 481 |
| zmierzone `n` w ramieniu B | **8 127 — 1,81× wymaganej** |
| górny kraniec CI ramienia B | **51,43%** |
| próg opłacalności | **52,94%** |

> ### ❌ **F1: WYNIK NEGATYWNY**
>
> `ci_high(51,43%) < break_even(52,94%)` — górny kraniec przedziału leży **1,51 pp poniżej
> progu opłacalności**, przy próbie 1,81× wymaganej. **Dowód braku, nie brak dowodu.**
>
> **Licznik F: 1/1 wyczerpany. Reguła STOP — seria F zamknięta.**

### Obserwacja (NIE kryterium): różnica między ramionami

**B − A = −0,03 pp**, 95% CI **[−1,57; +1,51]**, z = **−0,04**. Nieistotna.
Funding **nie zmienia trafności w żadną stronę**.

### Lejek

| etap | ramię A | ramię B |
|---|---|---|
| ocenione świece | 14 448 | 14 448 |
| odpadło na abstynencji | 6 334 | 6 252 |
| bramka pewności / kosztowa | 0 / 0 | 0 / 0 |
| sygnały | 8 114 | 8 196 |
| stłumione kill-switchem | 81 | 69 |
| **w próbie** | **8 033** | **8 127** |

Zero pominiętych foldów (0/86) w obu ramionach, bilans lejka domyka się.

## Runda OBALA jedyne ustalenie, jakie zgłosiło H2.1

H2.1 nie rozstrzygnęło pytania o trafność, ale zgłosiło jedno ustalenie:
**„funding POTROIŁ liczbę decyzji modelu (35 → 98) — czyli został uznany za informacyjny"**.
Trafiło ono do `runs/INDEX.md` i do `STATUS.md`.

**Nie odtwarza się.**

| przyrząd | ramię A | ramię B | krotność |
|---|---|---|---|
| przed A1 (H2.1) | 35 sygnałów | 98 | **2,80×** |
| **po A1 (F1)** | **8 114** | **8 196** | **1,01×** |

**Wyjaśnienie mechaniczne:** przy abstynencji 99,3% model podejmował 35 decyzji. Przy takiej
liczbie **każde drobne zaburzenie posteriora mnoży ją wielokrotnie** — dołożenie dowolnej
cechy, która cokolwiek zmienia, daje „potrojenie". Przy 8 000 decyzji ten sam funding zmienia
ją o **jeden procent**.

„Potrojenie" było **artefaktem zagłodzonej próby**, a nie miarą informacyjności cechy.
To ten sam rodzaj pułapki co „A2 kupuje `n`" z K2 i „liczba obserwacji to nie liczba
transakcji" z wniosku 19 — trzeci wariant tego samego błędu.

## Co na plus (+) / Co na minus (−)

**(+) Pytanie postawione w H2.0 wreszcie ma odpowiedź.** Funding jako cecha nie wynosi
trafności do progu opłacalności — zmierzone na 8 127 transakcjach zamiast 98.

**(+) Wycofane fałszywe ustalenie.** „Funding potraja liczbę decyzji" było jedyną rzeczą,
którą H2 zostawiło po sobie jako pozytywną, i okazało się artefaktem. Bez tej rundy zostałoby
w księdze jako fakt.

**(+) Potrójna kontrola odtwarzalności.** Ramię A dało `n = 8 033`, trafień `4 046`,
`p = 50,3672%` — **identycznie** jak w M1 i identycznie niezależnie od tego, czy do ramki
doklejono nieużywaną kolumnę funding. Dwa niezależne skrypty, trzy przebiegi, ta sama liczba
co do czwartego miejsca po przecinku.

**(+) Runda dostarczyła dokładnie to, co obiecała.** Pre-rejestracja mówiła, że odpowiedzi
„funding działa" obiecywać nie wolno i że wzrost `n` nie będzie wynikiem. Drugi zapis wręcz
uratował przed powtórzeniem błędu H2.1.

**(−) Wykrywalność nadal zaczyna się od ~54%.** Gdyby funding dawał +1 pp trafności, ta runda
by tego nie zobaczyła. Zapisane w pre-rejestracji, nie dopisane po wyniku.

**(−) To jedno sformułowanie funding, nie „funding" w ogóle.** Surowa stawka jako cecha.
H2.0 odrzuciło rachunkiem mocy bramkę na skrajny funding i carry; ten ostatni żyje wyłącznie
w wymiarze przekrojowym (4A).

**(−) BTC, 4h, V=3.** Jak wszystko w tym projekcie.

## Walidacja (zasada 16a)

**Werdykt: READY.**

- **Trafność przeliczona wprost z journalu** (zliczenie `gross_pnl > 0`) wobec wartości
  z `summarize_edge_by_regime`: **różnica 0,000000 pp** w obu ramionach.
- **Kontrola determinizmu:** ramię A policzone na ramce **bez** kolumny funding i **z** nią
  (nieużywaną) daje identyczne `n = 8 033` i `trafienia = 4 046`. Dołożenie niewykorzystanej
  kolumny nie wpływa na pipeline — warunek konieczny, żeby porównanie ramion mierzyło JEDNĄ
  zmienną (zasada 4).
- **Zgodność z M1:** ta sama konfiguracja w innym skrypcie dała tę samą liczbę.
- **„Kogo NIE ma w zbiorze":** bramka kosztowa i bramka pewności odrzuciły **zero** świec,
  zero pominiętych foldów, 2 świece z NaN funding wypadły jak rozbieg wskaźnika.
- **Red flag:** runda potwierdziła oczekiwanie zapisane z góry i **obaliła** ustalenie
  z poprzedniej rundy. To nie jest wynik wygodny.

## Przegląd diffu (zasada 16c)

**Werdykt: diff poprawny — dwa skrypty analityczne, zero zmian w kodzie produkcyjnym.**
`run_funding_measured_f1.py` buduje na `checkpoint_lib`, konsumuje `measurability_report`,
`required_trades` i `wald_half_width` bez własnych kopii wzorów; próg `N_WYMAGANE_DO_NEGATYWU`
wpisany, nie liczony po wyniku. Testy 390/390, ruff czysty.

## Wniosek

Prostym językiem (zasada 17).

**Opłata za utrzymanie pozycji nie pomaga przewidzieć kierunku.**

Funding to jedyna informacja w tym projekcie, która nie pochodzi z wykresu ceny — giełda
publikuje ją co osiem godzin, mamy jej prawie siedem lat. Dołożyliśmy ją do modelu już raz
i **nie dowiedzieliśmy się niczego**, bo model podjął wtedy 98 decyzji. Dziś podejmuje 8 127.

**Trafia w 50,34%. Musiałby w 52,94%.** Najbardziej optymistyczny odczyt to 51,43% — półtora
punktu poniżej progu. Różnica wobec modelu bez funding: **trzy setne punktu**, przy marginesie
błędu półtora punktu w każdą stronę. Czyli **zero**.

**Przy okazji trzeba wycofać rzecz, którą zapisaliśmy wcześniej jako ustalenie.** H2.1
stwierdziło, że funding „potroił liczbę decyzji modelu", i uznaliśmy to za dowód, że model
uznał go za informacyjny. To był artefakt: przy 35 decyzjach dowolna zmiana mnoży tę liczbę
wielokrotnie. Przy 8 000 decyzji funding zmienia ją o procent. **Nie potroił niczego — po
prostu było za mało danych, żeby cokolwiek zobaczyć.**

## Rekomendacja

1. **Zamknąć funding jako sygnał kierunkowy.** Licznik F wyczerpany, reguła STOP.

2. **Wycofać ustalenie „funding potraja liczbę decyzji"** z `runs/INDEX.md` (wniosek 14
   i wiersz H2.1) oraz ze `STATUS.md`. Nie jest prawdziwe.

3. **Stan zbioru informacyjnego po M1, P1 i F1 — do zapisania wprost.** Projekt zmierzył
   z zapasem mocy: **obie rodziny cech OHLCV** (mean-reversion 50,37%, momentum 49,74%)
   i **jedyne dostępne źródło spoza OHLCV** (funding 50,34%). Wszystkie przy 50%, wszystkie
   przy próbie ~8 000. Dane o pozycjonowaniu są **niemierzalne** (P1: 30 dni historii).
   **To nie jest brak pomysłów — to wyczerpanie tego, co da się zmierzyć tą metodologią
   na tych danych.**

4. **Co pozostaje otwarte i wymaga decyzji bramkowej:** inny target niż kierunek (nowa
   definicja wypłaty), carry przekrojowy (silnik portfelowy — inny projekt), ETH/SOL/BNB
   (nadal nie ma czego generalizować), zbieranie danych pozycjonowania od dziś na przyszłość
   (~3,4 roku do użyteczności).

5. **Nie proponuję kolejnej rundy.** Po F1 każda hipoteza na obecnych danych i obecnym
   targecie byłaby czwartym podejściem do tej samej ściany. **Decyzja o kierunku — albo
   o zamknięciu programu — jest bramkowa i należy do użytkownika.**
