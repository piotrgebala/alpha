# M1 — momentum po raz pierwszy na próbie zdolnej cokolwiek rozstrzygnąć (2026-09-22)

> **STATUS: ZAMKNIĘTA — WYNIK NEGATYWNY.** Wszystko do sekcji „Czego ta runda NIE
> rozstrzygnie" włącznie zapisano **przed napisaniem linijki kodu** (osobny commit `97a7936`).
> Sekcje od „Wynik" w dół dopisano po przebiegu. **Licznik M: 1/1 — WYCZERPANY, reguła STOP.**

## ID testu

**M1** — pierwszy wariant **NOWEJ HIPOTEZY M**. Własny licznik od zera (wniosek skumulowany 13),
własna reguła STOP, własna pre-rejestracja. **Nie dziedziczy budżetu ani progów po Fazie 0
ani po H2.**

## Metadane

- **Branch:** `task/M1-momentum-bez-bramki`
- **Poprzedzający stan (master):** `9296650`
- **Warianty:** **1** — wyczerpuje licznik M (0/1 → 1/1).
- **Testy przed rundą:** 390/390. Bramka leakage: **19/19 zielona** (`momentum_5`
  i `ema_diff_9_21` objęte testem sparametryzowanym po `FEATURE_FUNCTIONS` — zasada 2
  spełniona, żadna cecha nie jest nowa).

## Skąd ta hipoteza — rachunek z plików indeksowych, nie z pomysłu

**Wniosek skumulowany 12** wymienia momentum na liście rzeczy, których Faza 0 **NIE wykazała**:
*„próba zagłodzona przez samą bramkę: 0,53% świec — **niewykonalność pomiaru, nie brak
edge'u**"*. Z10 pisze to samo prostym językiem: *„momentum nigdy nie dostało uczciwego testu"*.

Rozbicie liczby zamykającej Fazę 0 pokazuje, dlaczego:

| pomiar | cechy | `n` | trafność | CI | pasmo |
|---|---|---|---|---|---|
| 5m `range` (Z17+Z21) | **reversion** | 7 043 | 50,38% | [49,21%; 51,54%] | 1,17 pp |
| 5m `trend` (Z17+Z21) | **momentum** | **299** | 50,84% | **[45,17%; 56,50%]** | **5,67 pp** |
| 4h `range` (S1b) | reversion | 345 | 47,54% | [42,27%; 52,81%] | 5,28 pp |
| **POOLED (Z10)** | — | **7 687** | **50,27%** | [49,15%; 51,38%] | 1,12 pp |

**96% liczby zamykającej Fazę 0 to cechy mean-reversion.** Momentum zmierzono na 299
transakcjach z przedziałem szerokim na **11 punktów** — obejmującym zarówno „bezużyteczne",
jak i „bardzo dochodowe".

**SPROSTOWANIE WPISU 4C w `STATUS.md` (ETAP 4).** Stoi tam: *„Bez bramki »momentum« to po
prostu predykcja kierunku z cech OHLCV — czyli dokładnie to, co Faza 0 obaliła na 7 687
transakcjach"*. To jest **za mocne i sprzeczne z wnioskiem 12**: tamte 7 687 transakcji to
w 96% inny zestaw cech. Wpis zostaje sprostowany w tej rundzie.

**Co się zmieniło, że to jest dziś wykonalne** — dwie rzeczy, obie zmierzone:
1. **Zdjęcie bramki reżimu** (H2.1a) — to ona głodziła próbę do 0,53% świec.
2. **Adopcja A1** (K2 → K3) — abstynencja 99,76% → 43,84%, próba **35 → 8 033** na tej
   konfiguracji, pasmo 16,56 pp → **1,09 pp**.

## Co przemawia PRZECIW — zapisane z góry, żeby nie zniknęło po wyniku

**Wniosek skumulowany 11 mówi wprost:** *„zmianą zdolną ruszyć `p` jest **nowy zbiór
informacyjny**, nie kolejna transformacja OHLCV ani nowa architektura nad tymi samymi
cechami"*. Momentum to **transformacja OHLCV**. Ten wniosek obniża prior tej rundy i nie
wolno go pomijać w interpretacji wyniku.

Napięcie między wnioskami 11 i 12 jest realne i rozstrzygam je tak: **wniosek 11 jest
uogólnieniem zbudowanym na powtarzalnych porażkach cech mean-reversion, a momentum to
jedyna gałąź OHLCV, na której tego uogólnienia nigdy nie sprawdzono.** Wniosek 12 istnieje
dokładnie po to, żeby nie cytować 11 jako dowodu w tej sprawie. Runda zamyka tę lukę —
w którąkolwiek stronę.

## Konfiguracja (ZAMROŻONA) i ramiona

Wszystko poza zestawem cech jest identyczne z konfiguracją zmierzoną w K3 (C2):

- **interwał** 4h, **V** = 3, **bramka reżimu** BRAK (`REGIME_ALL`)
- **wagi klas** `balanced` (A1, przyjęte 2026-09-22)
- walk-forward **60/28/28**, seed **42**, historia **6,8 roku** (14 916 świec)

| ramię | cechy | warianty | rola |
|---|---|---|---|
| **A** (odniesienie) | `REVERSION_FEATURES` (4) | **0** | punkt odniesienia w tej samej konfiguracji |
| **B** (kandydat) | `MOMENTUM_FEATURES` (4) | **1 — WYCZERPUJE licznik M** | przedmiot rundy |

**Dokładnie JEDNA zmienna** (zasada 4): zestaw cech. Ramię A liczy się za 0 wariantów wg tego
samego uzasadnienia, które zapisano w H2.1: **próg opłacalności pochodzi z geometrii kosztu,
a nie z obejrzanej trafności**, więc pomiar odniesienia nie może przesunąć poprzeczki.

## Rachunek mierzalności (zasada 18) — i uczciwe postawienie pytania

`expected_trades(14 448 świec, abstynencja 43,84%)` = **8 114**; pasmo = **1,09 pp**;
próg opłacalności **52,93%** (K3).

| założona trafność | skąd to założenie | werdykt |
|---|---|---|
| 50,84% | punktowy pomiar 5m/`trend` (n=299) | **NIEMIERZALNA** |
| 52,93% | dokładnie próg opłacalności | **NIEMIERZALNA** |
| **54,02%** | dolna granica wykrywalności przy tym `n` | MIERZALNA |
| 56,50% | górny kraniec CI pomiaru 5m/`trend` | MIERZALNA |

**To znaczy rzecz, którą trzeba powiedzieć wprost: tej rundzie NIE wolno obiecywać odpowiedzi
„momentum działa".** Żeby to orzec, momentum musiałoby dowozić ≥ 54,02% — więcej niż
cokolwiek, co ten projekt kiedykolwiek zmierzył.

**Ale pytanie odwrotne JEST mierzalne, i to z zapasem.**
`required_trades(50,84% wobec progu 52,93%)` = **4 481**, a mamy **8 114** — czyli **1,8×
wymaganej próby przy mocy 80%**. Runda ma więc moc orzec, że **momentum NIE dobija do progu
opłacalności** — dokładnie tym samym standardem („dowód braku, nie brak dowodu"), którym
Z10 zamknęło Fazę 0.

**Dlatego runda startuje.** Nie po to, żeby znaleźć edge, tylko żeby **zamknąć lukę z wniosku
12** liczbą zamiast przypisem.

## Kryterium — zapisane PRZED uruchomieniem

- **POZYTYWNY:** `ci_low(p_B) > break_even_B`. Byłby to **pierwszy dodatni wynik w historii
  projektu** i nie uruchamia niczego poza **replikacją na innym instrumencie** (zasada 9).
  Żadnego wdrożenia, żadnego kolejnego wariantu w tej serii.
- **NEGATYWNY:** `ci_high(p_B) < break_even_B` — momentum nie dobija do progu. Zamyka
  momentum jako kierunek i domyka pozycję z wniosku 12.
- **NIEROZSTRZYGNIĘTY:** `n_B < 4 481` (poniżej próby wymaganej do orzeczenia negatywu przy
  mocy 80%) **albo** CI przecina próg. Wtedy **nie interpretujemy w żadną stronę** — precedens
  S1b i H2.1.
- **REGUŁA STOP:** jeden wariant. Po nim seria M jest zamknięta **niezależnie od wyniku**.
  Żadnego drugiego `V`, interwału ani wariantu cech.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **Spodziewam się wyniku negatywnego.** Prior jest niski i opiera się na wniosku 11 oraz na
  tym, że każda naprawa pomiaru w Fazie 0 zostawiała `p` przy 50% — ani razu wyżej.
- **Jedyny pomiar momentum (50,84%) NIE jest przenośny co do poziomu:** pochodzi z 5m, gdzie
  próg opłacalności wynosił 82,81%, a nie 52,93%. Traktuję go jako słaby prior co do
  **rzędu wielkości**, nie jako prognozę.
- **`n` w ramieniu B może się różnić od 8 114**, bo abstynencja zależy od cech. Jeśli spadnie
  poniżej 4 481 — werdykt NIEROZSTRZYGNIĘTY, i tak to zaraportuję.
- **Wynik pozytywny traktuję z podejrzliwością proporcjonalną do jego niezwykłości.**
  Pierwsza reakcja na `ci_low > break_even` to **nie ogłoszenie**, tylko sprawdzenie, czy nie
  mamy przecieku — projekt złapał już trzy (Z17, Z17b, Z9), wszystkie ręcznie.

## Czego ta runda NIE rozstrzygnie

- **ETH/SOL/BNB** — zero testów, zero danych na dysku (tylko BTC).
- **Inny target niż kierunek** — inna definicja wypłaty, próg do policzenia od zera.
- **Carry przekrojowy (4A)** — wymaga silnika portfelowego, którego Faza 0 nie ma.
- **Czy utracona selektywność niosła informację** (otwarte pytanie z K3) — inny mechanizm,
  byłby confounderem. Osobna runda, jeśli w ogóle.
- **Wniosku 11 w ogólności** — negatywny wynik M1 go **wzmacnia**, ale go nie dowodzi dla
  cech spoza OHLCV.

---

## Wynik

**Komenda:** `py -m backtest.run_momentum_m1`. Dane: 14 916 świec 4h (2019-09-10 → 2026-06-30).
Pełny stdout: `raw_output.txt`.

### Trafność wobec progu opłacalności

| ramię | cechy | abstynencja | `n` | trafność | CI 95% | próg BE | margines |
|---|---|---|---|---|---|---|---|
| **A** (odniesienie) | reversion | 43,84% | 8 033 | 50,37% | [49,27%; 51,46%] | 52,93% | −2,57 pp |
| **B** (kandydat) | **momentum** | 40,23% | **8 512** | **49,74%** | **[48,68%; 50,80%]** | 52,94% | **−3,20 pp** |

### Geometria — skąd bierze się próg (wielkości niezależne od trafności)

| ramię | bariera B | koszt C | C/B | udział timeoutów |
|---|---|---|---|---|
| A | 1,3824% | 0,0811% | 0,0587 | 65,11% |
| B | 1,3711% | 0,0806% | 0,0588 | 64,91% |

Geometria obu ramion jest praktycznie identyczna, więc **różnica w marginesie pochodzi
wyłącznie z trafności**, a nie z innego progu.

### Werdykt wg kryterium zapisanego PRZED uruchomieniem

| | |
|---|---|
| wymagane `n` do orzeczenia negatywu (moc 80%) | 4 481 |
| zmierzone `n` w ramieniu B | **8 512 — 1,90× wymaganej próby** |
| pasmo przy tym `n` | 1,06 pp |
| górny kraniec CI ramienia B | **50,80%** |
| próg opłacalności | **52,94%** |

> ### ❌ **M1: WYNIK NEGATYWNY**
>
> `ci_high(50,80%) < break_even(52,94%)` — **górny kraniec przedziału ufności leży 2,14 pp
> poniżej progu opłacalności**, przy próbie prawie dwukrotnie większej niż wymagana.
> To jest **dowód braku, nie brak dowodu** — ten sam standard, którym Z10 zamknęło Fazę 0.
>
> **Licznik M: 1/1 wyczerpany. Reguła STOP uruchomiona — seria M zamknięta.**

## Co na plus (+) / Co na minus (−)

**(+) Luka z wniosku skumulowanego 12 zamknięta liczbą, nie przypisem.** Momentum miało
przedział ufności szeroki na 11 punktów (n=299). Teraz ma 2,1 punktu przy n=8 512.
Zdanie „momentum nigdy nie dostało uczciwego testu" przestaje być prawdziwe.

**(+) Ramię odniesienia odtworzyło historyczny pomiar projektu co do 0,01 pp.** 50,3672%
wobec 50,38% z 5m/`range` (Z17+Z21) — a to **zupełnie inna konfiguracja**: 4h zamiast 5m,
bez bramki zamiast z bramką, z wagami klas zamiast bez. Przedziały ufności nakładają się
również z pooled 50,27% z Z10. Aparat mierzy to samo, co mierzył.

**(+) Runda dostarczyła dokładnie to, co obiecała — i nic ponadto.** Pre-rejestracja mówiła
wprost, że odpowiedzi „momentum działa" tej rundzie nie wolno obiecywać, bo wykrywalność
zaczyna się od 54,02%. Dostarczyła odpowiedź negatywną, na którą miała moc 1,90×.

**(+) Wniosek 11 wzmocniony na jedynej gałęzi, na której go nie sprawdzono.** Teza
„`p` może ruszyć nowy zbiór informacyjny, nie kolejna transformacja OHLCV" przeszła test
na cechach momentum.

**(−) Momentum NIE jest gorsze od mean-reversion — jest tak samo nieobecne.** Różnica
B−A = **−0,63 pp**, 95% CI **[−2,15; +0,90]**, z = −0,80. Nieistotna. Kuszące zdanie
„momentum wypadło gorzej" byłoby **nadinterpretacją szumu** i świadomie go nie stawiam.

**(−) Runda nie umiałaby wykryć edge'u mniejszego niż 4 punkty.** Wykrywalność przy tym `n`
zaczyna się od 54,00%. Gdyby momentum dawało 53% — realnie opłacalne przy niższym koszcie
albo szerszej barierze — **ta runda by tego nie zobaczyła**. Zapisane w pre-rejestracji, nie
dopisane po wyniku.

**(−) Wynik dotyczy BTC, 4h, V=3, tej definicji momentum.** `momentum_5` i `ema_diff_9_21`
to dwie konkretne transformacje. „Momentum" jako idea ma ich nieskończenie wiele — runda
zamyka te dwie, w tej geometrii.

**(−) Abstynencja 40,23% jest PONIŻEJ podłogi 66,51%**, jak w ramieniu A. Część próby to
pozycje otwarte na świecach, które naprawdę kończą się niczym — znane ograniczenie A1
(ADR `docs/rag/03`), tu odziedziczone.

## Walidacja (zasada 16a)

**Werdykt: READY.**

**Trafność przeliczona DRUGĄ DROGĄ** — zliczeniem `gross_pnl > 0` wprost z journalu, zamiast
wzięcia z `summarize_edge_by_regime`:

| ramię | trafień | `n` | z journalu | z tabeli | różnica |
|---|---|---|---|---|---|
| A | 4 046 | 8 033 | 50,3672% | 50,3672% | **0,000000 pp** |
| B | 4 234 | 8 512 | 49,7415% | 49,7415% | **0,000000 pp** |

**Zgodność z archiwum jako niezależna ścieżka.** Ramię A jest inną konfiguracją niż
cokolwiek w Z10, a mimo to jego CI **nakłada się** zarówno z 5m/`range` (50,38%), jak
i z pooled Fazy 0 (50,27%). Gdyby konfiguracja albo aparat były popsute, ta zgodność
by się nie pojawiła.

**„Kogo NIE ma w zbiorze":** z 14 448 ocenionych świec odpada **wyłącznie abstynencja**
(6 334 / 5 813). **Bramka kosztowa i bramka pewności odrzuciły ZERO świec**, **zero
pominiętych foldów** (0/86 w obu ramionach), bilans lejka domyka się. Kill-switch stłumił
81 / 123 transakcje. Żaden filtr poza abstynencją nie wpływa na wynik.

**Red flag „wynik idealnie potwierdza hipotezę": NIE występuje** — runda potwierdziła
**oczekiwanie zapisane z góry** (spodziewałem się negatywu), a nie hipotezę, którą testowała.
Gdyby wyszła pozytywnie, pre-rejestracja nakazywała najpierw szukać przecieku.

## Przegląd diffu (zasada 16c)

**Werdykt jednym zdaniem: diff poprawny, gotowy do merge'u — jeden skrypt rundy plus skrypt
walidacyjny, zero zmian w kodzie produkcyjnym.**

`backtest/run_momentum_m1.py` buduje na `checkpoint_lib`, konsumuje `measurability_report`,
`required_trades` i `wald_half_width` bez własnych kopii wzorów. Progi pre-rejestrowane
(`N_WYMAGANE_DO_NEGATYWU = 4481`) są **wpisane, nie liczone po wyniku**. `m1_walidacja.py`
liczy trafność drugą drogą, wprost z journalu. Testy: **390/390** (bez zmian — kod
produkcyjny nietknięty). Ruff: czysty.

## Wniosek

Prostym językiem (zasada 17).

**Momentum dostało wreszcie uczciwy test i go nie przeszło.**

„Momentum" to założenie, że gdy cena rośnie, będzie rosła dalej. Projekt nigdy go porządnie
nie sprawdził — nie dlatego, że zapomniał, tylko dlatego, że **filtr reżimu przepuszczał takie
momenty przez pół procenta czasu**. Zostawało 299 transakcji, a przy takiej liczbie wynik
mieścił się w przedziale od „bezużyteczne" do „bardzo dochodowe". Nie dało się nic orzec.

Dwie naprawy z ostatnich dni to zmieniły: zdjęcie filtra i nauczenie modelu, żeby nie milczał.
Momentum dostało **8 512 transakcji** zamiast 299.

**Wynik: trafia w 49,74%.** Żeby wyjść na zero po opłatach, musiałoby trafiać w **52,94%**.
Nawet najbardziej optymistyczny odczyt pomiaru — górny kraniec marginesu błędu — to **50,80%**,
czyli **ponad dwa punkty poniżej progu**. Próba była prawie dwukrotnie większa, niż trzeba było
do takiego orzeczenia.

To jest **dowód braku, a nie brak dowodu** — ten sam standard, którym zamykaliśmy Fazę 0.

**Czego NIE wolno z tego wyciągnąć:** że momentum jest gorsze od tego, co testowaliśmy wcześniej.
Różnica wobec ramienia odniesienia to −0,63 punktu przy marginesie błędu ±1,5 — czyli **szum**.
Momentum nie wypadło gorzej. Wypadło **tak samo nieobecnie**.

**Sprawdzian wiarygodności:** ramię odniesienia dało 50,37%, podczas gdy historyczny pomiar
projektu na zupełnie innej konfiguracji dawał 50,38%. Zgodność co do jednej setnej punktu.
Aparat mierzy to samo, co mierzył.

## Rekomendacja

1. **Zamknąć momentum jako kierunek.** Pozycja z wniosku skumulowanego 12 („momentum nigdy
   nie dostało uczciwego testu") przestaje być otwarta — dostało i nie przeszło.
   Licznik M wyczerpany 1/1, reguła STOP aktywna.

2. **Sprostować wpis 4C w `STATUS.md`** — dwukrotnie. Był za mocny (twierdził, że Faza 0 to
   obaliła na 7 687 transakcjach, a to w 96% inne cechy), a teraz jest **nieaktualny**, bo
   sprawa została rozstrzygnięta pomiarem.

3. **Wniosek 11 wzmocniony, ale nie udowodniony.** Teza „`p` ruszy nowy zbiór informacyjny,
   nie kolejna transformacja OHLCV" przeszła test na jedynej gałęzi, na której jej nie
   sprawdzono. Nadal **nie jest dowiedziona** dla cech spoza OHLCV — bo takich prawie nie
   testowaliśmy (funding raz, nierozstrzygnięty).

4. **Co zostaje na mapie po tej rundzie.** Z listy „czego Faza 0 nie wykazała" ubywa momentum.
   Zostają: **inny target niż kierunek**, **carry przekrojowy** (wymaga silnika portfelowego),
   **ETH/SOL/BNB** (test generalizacji — nadal nie ma czego generalizować) oraz **ekonomia
   dźwigni** (mnoży zero). Plus otwarte pytanie z K3 o utraconą selektywność.

5. **Nie proponuję kolejnej rundy z automatu.** Po M1 obraz jest taki: **dwa niezależne
   zestawy cech OHLCV, obie architektury, obie zmierzone na próbie z zapasem mocy — i obie
   przy 50%.** Kolejna kombinacja cech OHLCV byłaby czwartym podejściem do tej samej ściany.
   Decyzja, czy iść w stronę innego źródła informacji, innego targetu, czy zamknąć program,
   jest bramkowa i należy do użytkownika.
