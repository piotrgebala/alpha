# T4 — early stopping działa (chroni przed przeuczeniem), próg 30 wierszy jest tu bezczynny; model i tak nie ma czego się nauczyć (2026-09-23)

> **Pre-rejestracja** (sekcje od „ID testu” do „Ścieżka odwrotu”) zapisana i zacommitowana
> PRZED kodem i przed obejrzeniem liczb (`9eb9345`). Nie była zmieniana po wyniku, poza
> tytułem. Wyniki są od sekcji „Wynik” w dół.

## ID testu

**T4** — zadanie z `STATUS.md` §17, ETAP 3 („PRIORYTET 1 po K1"). Diagnostyka przyrządu,
**0 wariantów** (poza licznikami hipotez — uzasadnienie niżej).

## Pytanie prostym językiem

Model uczy się w rundach. W każdej rundzie dokłada jedno małe „drzewo decyzyjne”, które
poprawia błędy poprzednich. Zbyt wiele rund prowadzi do tego, że model zaczyna uczyć się
przypadkowych zbiegów okoliczności z danych treningowych. **Early stopping** (wczesne
zatrzymanie) ma temu zapobiegać. Odkłada 20% najnowszych danych treningowych na bok,
po każdej rundzie sprawdza model na tym kawałku i przerywa naukę, gdy wynik przestaje
się poprawiać.

Ten mechanizm ma dwie ustawione na oko liczby: **20%** (`validation_fraction`) i
**co najmniej 30 wierszy** (`MIN_VALIDATION_ROWS`). Nikt ich nie sprawdzał. Wiemy już,
że potrafią szkodzić: próg 30 wierszy wyłączył kiedyś po cichu early stopping w 92% okien
(Z17b). Pytamy więc wprost: **w obecnej, kanonicznej konfiguracji, czy ten mechanizm wybiera
liczbę drzew, która naprawdę lepiej działa na nowych danych, czy losuje ją z szumu?**

## Poprzedzające wyniki (zasada 14)

- **Z17+Z21** — early stopping liczono na danych testowych (przeciek). Przeniesiony na ogon
  danych treningowych, z odcięciem `V` świec na granicy (embargo).
- **S1 → S1b (Z17b)** — przy formule `round(n·0,2)` próg 30 wierszy wyłączał early stopping
  w 58/63 oknach. Po naprawie `max(30, round(n·0,2))` działa w 53/63. Skutek uboczny:
  abstynencja modelu (odmowa zajęcia pozycji) wzrosła 70,9% → 90,5%. S1b zapisało wprost:
  *„Nie wiem, czy wzrost abstynencji to zdrowa ostrożność, czy artefakt zbyt agresywnego
  early stoppingu przy 30 wierszach walidacji. Rozstrzygnięcie wymagałoby zagnieżdżonego
  walk-forward”*. **To jest dokładnie to rozstrzygnięcie.**
- **K2/A1** — wagi klas `balanced` przyjęte jako domyślne. Walidacja jest ważona tą samą mapą
  co trening, więc early stopping optymalizuje ten sam cel co trening.
- **K3, M1, F1** — obecna konfiguracja kanoniczna: 4h, bez bramki reżimu, V=3, wagi
  `balanced`, walk-forward 60/28/28 dni. Okno treningowe to ~360 świec, więc część
  walidacyjna ma ~70 wierszy. **Taka mała próbka do oceny krzywej błędu to realne ryzyko,
  że decyzję o liczbie drzew podejmuje szum.**
- **Wniosek skumulowany 39** — zbiór informacyjny na BTC jest wyczerpany (M1, F1: trafność
  ~50% przy dużej próbie). **Ta runda nie reanimuje żadnej hipotezy.** Dotyczy przyrządu:
  wynik ma znaczenie dla każdego przyszłego pomiaru tym pipeline'em, również dla innego
  instrumentu albo innego celu (§17, ETAP 4).

Czego ta runda NIE powtarza: nie mierzy trafności na danych testowych dla żadnego zestawu
cech. M1 i F1 już to zrobiły, a ich serie są zamknięte regułą STOP.

## Projekt — zagnieżdżony podział wyłącznie wewnątrz danych treningowych

Dla każdego okna walk-forward biorę **dokładnie ten `train_df`**, który silnik podaje do
`train_regime_model`. Przechwytuję go opakowaniem funkcji, więc to ten sam przebieg, nie
kopia logiki. Konfiguracja: ramię A z F1/K3-C2, czyli 4 cechy reversion, 4h, bez bramki,
V=3, `balanced`, 60/28/28, seed 42.

Dalej, dla każdego okna:

1. `train_clean` = po `dropna` i po embargu `V`, tak jak w produkcji.
2. Podział produkcyjny: `n_val = max(30, round(0,2·n))`. Ogon produkcyjny (`val_part`)
   staje się **wewnętrznym zbiorem testowym**. Te wiersze nie biorą udziału w żadnym
   wyborze.
3. Z części `fit_part` odcinam ostatnie `V` wierszy (embargo względem wewnętrznego testu).
   Resztę dzielę tą samą regułą na **wewnętrzny trening** i **wewnętrzną walidację**,
   dla `f ∈ {0,1; 0,2; 0,3}`.
4. Trenuję 200 rund na wewnętrznym treningu i zapisuję krzywe ważonego `mlogloss` na
   walidacji i na wewnętrznym teście. Mapa wag pochodzi z wewnętrznego treningu, jak
   w produkcji.
5. Z krzywej walidacji odtwarzam decyzję early stoppingu: najlepsza runda i stop po 20
   rundach bez poprawy. Wyrocznię (runda najlepsza na wewnętrznym teście) liczę WYŁĄCZNIE
   jako punkt odniesienia; nigdy jej nie wybieram.

**Żadna etykieta z testowej części walk-forward nie jest czytana.** Skrypt nie wywołuje
`run_and_summarize`. Przebieg produkcyjny służy tylko do przechwycenia `train_df`
i `folds_summary`. Journal transakcji nie jest drukowany ani analizowany.

## Miary (zarejestrowane z góry)

**D0 — fakty o konfiguracji produkcyjnej** (z `folds_summary` i przechwyconych danych):
liczba okien aktywnych i pominiętych, rozkład `n_val`, **w ilu oknach `max(30, ·)` zmienia
wynik**, udział okien z early stoppingiem, rozkład `best_iteration`, udział okien z
`best_iteration` < 5 (model praktycznie = rozkład klas) i = 199 (early stopping nie zadziałał).

**D1 — MIARA GŁÓWNA.** Dla `f = 0,2`, w każdym oknie:
`Δ_200 = L_test(k_ES) − L_test(200)` oraz `Δ_1 = L_test(k_ES) − L_test(1)`, gdzie `L_test` to
ważony `mlogloss` na wewnętrznym teście. Raport: średnia, mediana i 95% CI średniej po
oknach (t-Student).

**D2** — rozkład `k_ES` vs `k_wyrocznia`: korelacja Spearmana i „żal”
`L_test(k_ES) − L_test(k_wyrocznia)` (≥ 0 z konstrukcji; to strata wobec idealnej decyzji).

**D3** — wrażliwość na `f ∈ {0,1; 0,2; 0,3}`: mediana `k_ES` i średnie `Δ_200`.
**Obserwacja, nie wybór.** Żadna wartość `f` nie zostaje w tej rundzie przyjęta.

**D4** — konsekwencja praktyczna: udział wierszy wewnętrznego testu, na których model
przewiduje „timeout” (abstynencja), przy `k_ES` vs przy 200 drzewach. To mechanizm z S1b.

## Kryteria interpretacji (zapisane PRZED wynikiem)

| wynik D1 (`Δ_200`, f=0,2) | czytanie |
|---|---|
| górny kraniec CI < 0 | early stopping **pomaga**: wybiera liczbę drzew lepszą niż „bez zatrzymania” na danych, których nie widział. Zostaje |
| CI obejmuje 0 | przy tej wielkości okna early stopping jest **nieodróżnialny od braku early stoppingu**. Liczba drzew to wtedy w praktyce wybór losowy (szum), ale nieszkodliwy dla straty |
| dolny kraniec CI > 0 | early stopping **szkodzi**: wybiera gorzej niż stała 200. To wada przyrządu do zgłoszenia jako osobne zadanie |

Analogicznie `Δ_1` odpowiada na pytanie, czy early stopping bije model zatrzymany po
pierwszej rundzie (praktycznie sam rozkład klas).

`MIN_VALIDATION_ROWS`: jeśli `max()` nie zmienia `n_val` w żadnym aktywnym oknie
kanonicznej konfiguracji, to stała jest tutaj **bezczynna**. Wtedy wniosek brzmi
„niegroźna w tej konfiguracji”, a nie „skalibrowana”.

**Reguła niezależna od wyniku:** ta runda **nie zmienia żadnej wartości w kodzie
produkcyjnym**. Zmiana `validation_fraction`, `EARLY_STOPPING_ROUNDS` albo
`MIN_VALIDATION_ROWS` zmieniłaby każdy przyszły pomiar. Byłaby więc osobną rundą z własną
pre-rejestracją, dla której ta runda jest tylko przesłanką. Dzięki temu D3 nie jest
przeszukiwaniem siatki parametrów, tylko opisem.

**Red flag zapisany z góry:** gdyby wynik wyglądał na „early stopping jest bezużyteczny,
więc S1b/H2.1 były artefaktem”, trzeba pamiętać, że K2/A1 już zmieniło mechanizm
abstynencji. Wniosek o S1b dotyczy konfiguracji `none`, a ta runda mierzy `balanced`.

## Dlaczego 0 wariantów i jak z mierzalnością (zasada 18)

- **0 wariantów:** runda nie porównuje żadnej hipotezy rynkowej z wynikiem na danych
  testowych. Liczy wyłącznie na danych treningowych każdego okna, czyli wewnątrz
  walk-forward (zasada 1). Ta sama kategoria co K1/K2/K3 (kalibracja przyrządu).
- **`measurability_report` nie ma tu zastosowania.** Ta funkcja dotyczy hipotez
  o trafności. Jednostką tutaj jest okno walk-forward, oczekiwane `n` ≈ 85 (F1: 85 okien,
  0 pominiętych). Precyzję D1 podam po fakcie jako połowę szerokości CI. Jeśli okaże się
  szersza niż sama różnica, którą chcemy zobaczyć, werdykt brzmi „nierozstrzygnięte”,
  a nie „brak efektu”.

## Ścieżka odwrotu

Runda nie zmienia kodu produkcyjnego. Dodaje jeden skrypt analityczny
(`backtest/diagnose_early_stopping_t4.py`) i ten katalog. Revert = `git revert` commitów
rundy.

---

## Metadane

- **Branch:** `worktree-t4-kalibracja-early-stopping` (od master `9b78238`)
- **Komenda:** `py -m backtest.diagnose_early_stopping_t4` (czas: 54 s)
- **Dane:** `data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet`,
  14 916 świec 4h, 2019-09-10 → 2026-06-30. Seed 42.
- **Konfiguracja:** ramię A z F1 / K3-C2 (4 cechy reversion, bez bramki, V=3, `balanced`,
  60/28/28). Produkcyjnie: `validation_fraction=0,2`, `MIN_VALIDATION_ROWS=30`,
  `EARLY_STOPPING_ROUNDS=20`, `num_boost_round=200`.
- **Warianty:** 0 (kalibracja przyrządu, poza licznikami hipotez).
- **Testy:** `tests/test_diagnose_early_stopping_t4.py`: 11 nowych testów, w tym zgodność
  odtworzonej decyzji early stoppingu z `best_iteration` XGBoost na 5 losowaniach.
  Wynik całego pakietu podaję w sekcji „Przegląd diffu”.

## Wynik

### D0 — jak jest dziś w konfiguracji kanonicznej

| miara | wartość | co to znaczy |
|---|---|---|
| okna aktywne / pominięte | 86 / 0 | nikogo nie brakuje |
| wiersze walidacji `n_val` | 68–71 (mediana 71) | 20% z ~357 wierszy |
| okna, w których `max(30, ·)` zmienia `n_val` | **0 / 86** | **`MIN_VALIDATION_ROWS` jest tu bezczynny**, bo 20% zawsze daje ≥ 68 |
| okna z działającym early stoppingiem | **86 / 86** | wada z S1 (martwy early stopping) tu nie występuje |
| liczba drzew w produkcji | min 1, kwartyle **1 / 2 / 8**, max 37 | model zatrzymuje się niemal od razu |
| okna z 1 drzewem / z < 5 drzewami | 38 / 86 · 58 / 86 | w dwóch trzecich okien model to prawie sam rozkład klas |
| kontrola: moja rekonstrukcja decyzji == silnik | **86 / 86** | analiza odtwarza produkcję co do drzewa |

### D1 — miara główna (f = 0,2, 86 okien): strata na danych, których wybór nie widział

Miarą jest ważony `mlogloss` (błąd prognozy prawdopodobieństw; mniej = lepiej). Ujemna
różnica oznacza, że early stopping jest lepszy.

| porównanie | średnia | mediana | 95% CI średniej | ES lepszy w |
|---|---|---|---|---|
| ES − 200 drzew (brak zatrzymania) | **−0,617** | −0,552 | **[−0,683; −0,552]** | **86 / 86** |
| ES − 50 drzew | −0,148 | −0,127 | [−0,175; −0,121] | 81 / 86 |
| ES − 10 drzew | +0,008 | −0,003 | [−0,007; +0,022] | 50 / 86 |
| ES − 1 drzewo | **+0,024** | 0,000 | **[+0,009; +0,039]** | 19 / 86 (34 remisy) |
| ES − wyrocznia (≥ 0 z konstrukcji) | +0,031 | +0,003 | [+0,017; +0,045] | — |

Średnie poziomy: 1 drzewo **1,0982**, wyrocznia **1,0912**, ES **1,1222**, 200 drzew
**1,7397**. Wartość odniesienia „zgaduję każdą klasę po równo” = ln 3 = **1,0986**.

### D2 — czy early stopping trafia w dobrą liczbę drzew

Korelacja Spearmana między liczbą drzew wybraną przez ES a najlepszą: **+0,28**
(p = 0,009, n = 86). To słaby, ale prawdziwy związek. Najlepsza liczba drzew na danych
niewidzianych to w **41 / 86** oknach jedno drzewo (kwartyle 1 / 2 / 6). ES wybiera
nieco więcej (kwartyle 1 / 4 / 17).

### D3 — wrażliwość na `validation_fraction` (obserwacja, nie wybór)

| f | wiersze walidacji (mediana) | drzewa ES (mediana) | ES − 200 (średnia, CI) | ES − wyrocznia |
|---|---|---|---|---|
| 0,1 | 30 | 6 | −0,539 [−0,601; −0,476] | +0,057 |
| 0,2 | 57 | 4 | −0,617 [−0,683; −0,552] | +0,031 |
| 0,3 | 85 | 1 | −0,721 [−0,793; −0,648] | +0,024 |

Większa część walidacyjna daje mniej drzew i mniejszą stratę wobec wyroczni. **Nie wolno
tego czytać jako „przestaw na 0,3”**, powód w sekcji Co na minus.

### D4 — abstynencja (odmowa zajęcia pozycji) na wewnętrznym teście

| | udział prognoz „timeout” |
|---|---|
| przy ES | **44,4%** [41,5%; 47,3%] |
| przy 200 drzewach | 62,0% [59,6%; 64,3%] |
| różnica ES − 200 | **−17,6 pp** [−20,1; −15,1] |
| faktyczny udział etykiety „timeout” | 64,8% |

Przy wagach `balanced` early stopping **obniża** abstynencję, nie podnosi. 44,4% zgadza się
z abstynencją zmierzoną w K3 na danych testowych (43,84%).

## Werdykt wobec kryteriów pre-rejestrowanych

- **D1 (`Δ_200`): górny kraniec CI = −0,552 < 0 → early stopping POMAGA.** Zostaje.
  Bez niego model przeucza się drastycznie: strata rośnie o 58% (1,74 wobec 1,10).
- **`Δ_1`: dolny kraniec CI = +0,009 > 0 → early stopping jest istotnie GORSZY od jednego
  drzewa.** Ma to prosty powód (Wniosek niżej). Nie jest to wada przyrządu do naprawy.
- **`MIN_VALIDATION_ROWS`: bezczynny (0 / 86).** Wniosek zgodnie z pre-rejestracją:
  „niegroźny w tej konfiguracji”, **nie** „skalibrowany”.

## Walidacja (16a): **Ready**

- **Niezależne przeliczenie kluczowej liczby:** średnia strata przy jednym drzewie (1,09822)
  odpowiada wartości teoretycznej ln 3 = 1,09861 (różnica −0,0004). Przy wagach `balanced`
  każda klasa ma tę samą wagę łączną, więc model „nic nie wiem” musi dać dokładnie ln 3.
  Ta droga nie przechodzi przez kod rundy, tylko przez rachunek. Dodatkowo średnie i CI D1
  przeliczone osobnym skryptem z tabeli per okno w `raw_output.txt`: zgodne co do
  5 miejsc. Test znaków rang dla `Δ_1` (bez 34 remisów): p = 0,0007.
- **Zgodność z produkcją:** decyzja ES odtworzona 86 / 86. Abstynencja 44,4% zgadza się
  z K3 (43,84%, inny zbiór: dane testowe).
- **Kogo NIE ma w zbiorze:** 0 okien pominiętych. Wewnętrzny test to ogon ~71 wierszy
  (~12 dni) każdego okna. Wynik dotyczy **tej** konfiguracji: 4h, okno 60 dni, cechy
  reversion. Nie przenosi się automatycznie na 5m (tam okna są ~50× większe) ani na dane,
  w których jest prawdziwy sygnał.
- **Red flag „wynik idealnie potwierdza”:** wynik D1 był przewidywalny (200 drzew na ~230
  wierszach musi się przeuczyć). Informacyjna jest część nieoczekiwana: ES przegrywa
  z jednym drzewem, a wyrocznia prawie nie bije ln 3. To zapisuję w Wniosku ostrożnie,
  jako potwierdzenie inną drogą, a nie jako nowy dowód.

## Przegląd diffu (16c)

**Approve.** Diff dodaje jeden skrypt analityczny, 11 testów i dokumentację. Nie dotyka kodu
produkcyjnego ani skryptów zamrożonych. Podmiana `engine.train_regime_model` jest cofana
w `finally`, a embargo i ważenie walidacji odtwarzają produkcję (86/86 zgodnych decyzji).
Jedna asercja-tautologia (sprawdzała stałą zamiast funkcji) została zastąpiona sprawdzeniem
własności: pierwsza runda przy wagach `balanced` daje stratę ≈ ln 3. Pełny pakiet: **436/436**,
`ruff` i `black` czyste na plikach rundy.

## Co na plus (+)

- **Wątpliwość z S1b rozstrzygnięta dla obecnej konfiguracji.** Pytanie brzmiało: czy wysoka
  abstynencja to zdrowa ostrożność, czy artefakt early stoppingu na 30 wierszach. Przy
  wagach `balanced` early stopping abstynencję **obniża** (−17,6 pp), a próg 30 wierszy nie
  bierze udziału (walidacja ma ≥ 68 wierszy).
- **Early stopping jest potrzebny, nie ozdobny:** bez niego strata rośnie o 58% w 86 z 86 okien.
- **Przyrząd przetestowany drugą drogą:** rekonstrukcja decyzji jest zgodna z XGBoost
  w teście jednostkowym i na 86 realnych oknach.
- **Zero zużytego budżetu wariantów:** żadna etykieta z danych testowych nie została
  przeczytana.

## Co na minus (−)

- **D3 NIE jest podstawą do zmiany `validation_fraction`.** Na danych bez sygnału najlepsza
  liczba drzew jest zawsze „jak najmniej”. Każde ustawienie, które skraca trening, wygląda
  wtedy lepiej. Przestawienie na 0,3 zoptymalizowałoby przyrząd pod brak sygnału, czyli
  osłabiłoby go dokładnie tam, gdzie sygnał by był. Kalibracja `f` ma sens tylko na danych
  ze znanym sygnałem (wyrocznia z K1/K2).
- **Early stopping kosztuje ~0,024 straty wobec jednego drzewa** (~2% od ln 3). Przyczyną jest
  szum przy 57 wierszach walidacji. Część okien dokłada 10–58 drzew dopasowanych do
  przypadku. Nie zmienia to werdyktów M1/F1, bo trafność mierzono tam na danych testowych
  z tymi samymi modelami. Oznacza to jednak, że przyrząd ma własny, niewielki szum.
- **Runda mierzy jedną konfigurację.** Zakres opisałem w „Kogo NIE ma w zbiorze”.
- **Wniosek o S1b dotyczy wag `balanced`.** Przy `none` (S1b) kierunek efektu mógł być inny.
  Tego nie mierzyłem, bo `none` nie jest już konfiguracją domyślną (K2/A1).

## Wniosek

Early stopping robi to, co ma robić. Bez niego model uczy się przypadkowych zbiegów
okoliczności i wypada znacznie gorzej na danych, których nie widział: błąd prognozy o 58%
większy, we wszystkich 86 oknach. Próg „co najmniej 30 wierszy” w obecnej konfiguracji
w ogóle nie działa, bo 20% danych zawsze daje około 70 wierszy. Ryzyko z Z17b (próg po
cichu wyłącza zabezpieczenie) tu nie występuje.

Wynik uboczny, ważniejszy od samego pytania: **najlepszy możliwy model jest ledwie lepszy
od zgadywania.** Na danych, których wybór nie widział, nawet idealnie dobrana liczba drzew
poprawia prognozę tylko o 0,7% wobec „każda z trzech możliwości po równo”. Najczęściej
najlepiej wypada model z jednym drzewem, czyli praktycznie bez nauki. To ten sam wniosek
co M1/F1 (trafność ~50%), osiągnięty inną drogą: przez jakość prognoz prawdopodobieństwa
na danych treningowych, a nie przez trafność transakcji na danych testowych. Cztery cechy
cenowe nie niosą informacji o tym, jak skończy się kolejne 12 godzin.

## Rekomendacja

1. **Nie zmieniać niczego w kodzie.** `validation_fraction = 0,2`, `EARLY_STOPPING_ROUNDS = 20`
   i `MIN_VALIDATION_ROWS = 30` zostają. T4 zamknięte.
2. **`MIN_VALIDATION_ROWS` zostaje jako zabezpieczenie**, nie jako parametr. Zadziała dopiero
   przy oknie treningowym poniżej ~150 wierszy.
3. **Jeśli kiedyś przyrząd będzie mierzył coś, w czym jest sygnał** (inny instrument, inny
   cel, §17 ETAP 4), `validation_fraction` należy skalibrować na wyroczni K1/K2 (znany
   sygnał), a nie na realnych danych BTC. Tutaj „mniej drzew = lepiej” wynika z braku
   sygnału. Zapis w backlogu, bez wariantu.
