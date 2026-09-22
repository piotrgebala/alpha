# H3 — noga „timeout" w modelu kosztów: PASMO niepewności zamiast przerzucenia flagi (2026-09-22)

> **STATUS: ZAMKNIĘTA.** Wszystko od sekcji „Reguła decyzyjna" w górę zapisano **przed
> napisaniem linijki kodu produkcyjnego** — commit `707f7e0` zawiera wyłącznie pre-rejestrację
> i poprzedza commit z kodem `350e8b1`. **Kolejność jest dowodliwa z historii gita**, nie tylko
> zadeklarowana w tekście.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Skąd to się wzięło.** W poprzedniej rundzie napisałem, że prawdopodobnie przepłacamy
w rachunku kosztów. Gdy pozycja kończy się „z upływem czasu", zakładamy drogie wyjście po
cenie rynkowej — a przecież wiadomo z góry, kiedy to nastąpi, więc można by złożyć tańsze
zlecenie oczekujące. Oszacowałem oszczędność na 1 punkt procentowy poprzeczki.

**Sprawdziłem to dokładniej i moja teza się nie broni.** Z dwóch powodów:

1. **Pomyliłem się w rachunku.** Użyłem najdroższego możliwego kosztu zamiast tego, który
   naprawdę zmierzyliśmy. Prawdziwa poprzeczka to **52,66%**, a nie 53,12%. Czyli **prawie
   połowa rzekomej oszczędności nigdy nie istniała** — była moim błędem.

2. **Zlecenie oczekujące wymaga znajomości CENY, nie tylko czasu.** Przy wejściu i przy
   zyskownym wyjściu cenę znamy z góry. Przy wyjściu „z upływem czasu" znamy **moment**, ale
   nie cenę — a program liczy wyjście po cenie zamknięcia tej świecy. Żeby dostać *tę* cenę
   zleceniem oczekującym, trzeba by ją znać wcześniej. **Policzenie tańszej opłaty za cenę,
   którą można dostać wyłącznie drogo, to policzenie tej samej korzyści dwa razy.**

**Co wobec tego robimy.** Nie zmieniamy zachowania programu. Dokładamy przełącznik i puszczamy
ten sam test w obu wersjach — żeby sprawdzić, **czy to założenie w ogóle wpływa na decyzję**.
Przy okazji łatamy prawdziwą usterkę: koszt jest dziś liczony w dwóch miejscach niezależnie
i mogą się po cichu rozjechać.

**Czego ta runda NIE zrobi:** nie obniży poprzeczki. To jest zapisane z góry w regule D2 niżej,
żeby nie dało się tego zrobić po obejrzeniu wyniku.

---

## ID testu

**H3** — runda poprawności modelu kosztów. **0 wariantów** (pod warunkiem D5). Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/H3-noga-timeout`
- **Poprzedzający stan (master):** `c2ecd19` (merge H2.0)
- **Decyzja użytkownika 2026-09-22:** po przedstawieniu obu kontrargumentów — *„Zmierzyć, ile
  to zmienia"*, z zachowaniem domyślnego zachowania.
- **Komenda:** `py -m backtest.run_timeout_leg_band` (pełny output: `raw_output.txt`)
- **Warianty:** **0** — patrz reguła **D5**, która określa warunek utrzymania tego zera.
- **Testy przed rundą:** 265/265.

## Poprzedzające wyniki (zasada 14)

- **H2.0** (`runs/2026-09-22_h2.0-funding-wykonalnosc/`) — wniosek skumulowany nr 16 w INDEX
  zapisał podejrzenie „`timeout → taker` to prawdopodobnie błąd". **Ta runda je rozstrzyga —
  na niekorzyść podejrzenia** (sekcja „Rozstrzygnięcie merytoryczne").
- **C2.12 / Z6** (`runs/2026-09-21_c2.12-execution-cost-model/`) — wprowadziło model maker/taker
  i obecne mapowanie `exit_reason → noga`. Precedens metodologiczny: nazwany wariant
  (`execution_model`) zamiast pokrętła, i to on daje dziś regresję baseline'u.
- **S1b** (`runs/2026-09-22_s1b-early-stopping-naprawiony/`) — dostarcza **konfigurację pomiaru
  i liczby odniesienia**: `n=345`, `cost_pct=0,000767`, `barrier_pct=0,014276`,
  `break_even_p=0,526862`, `share_timeout=0,60`.
- **C2d** — bramka kosztowa i diagnoza `range`; `tests/test_risk_controller.py` trzyma jej
  historyczny zapis, którego nie wolno naruszyć (patrz „Pułapka" w sekcji Testy).
- **Z19** — rachunek mocy przed eksperymentem; tutaj w wersji: **reguła decyzyjna przed pomiarem**.

---

## Rozstrzygnięcie merytoryczne (zapisane PRZED przebiegiem)

Kryterium, które tłumaczy całą obecną mapę nóg naraz:

> **Noga „maker" jest dobrze zdefiniowana tylko wtedy, gdy CENA zlecenia jest znana w momencie
> jego składania.** Zlecenie limit to para (cena, czas ważności) — nie da się złożyć limitu
> „na tę świecę, po cenie jaka wyjdzie".

| noga | cena znana z góry? | wyjście przymusowe? | dziś | spójne? |
|---|---|---|---|---|
| wejście | TAK (bieżący `close`) | NIE — brak fill = nie wchodzimy | maker | ✔ |
| `tp` | TAK (`entry + 1,5·ATR`, znane w chwili wejścia) | NIE — brak fill = transakcja trwa | maker | ✔ |
| `sl` | TAK, ale wyjście obowiązkowe | TAK | taker | ✔ |
| **`timeout`** | **NIE — znamy CZAS (świeca `t+V`), nie cenę** | TAK | taker | ✔ |

**Obecna mapa nie jest niedbała — jest implementacją tej zasady.** Timeout jest jedyną nogą,
gdzie znamy czas, a nie cenę. To klasyczny trade-off egzekucji: **albo pewny czas i nieznana
cena (market/taker), albo pewna cena i nieznany czas (limit/maker)**. Nie da się mieć obu.

**Drugi, twardszy argument — wewnętrzna niespójność wariantu „maker":** `engine.py:407-408`
liczy cenę wyjścia timeoutu jako `close` świecy timeoutu. Żeby dostać *ten* `close` zleceniem
limit, trzeba by znać go z wyprzedzeniem (lookahead) albo skrosować księgę. Naliczenie stawki
maker za cenę osiągalną wyłącznie taker-em to **policzenie tej samej korzyści dwa razy**.
Realistyczne „timeout → maker" wymagałoby własnego modelu ceny wyjścia (limit na poziomie X,
fill tylko gdy rynek do X dojdzie, inaczej pościg), co zmieniłoby `gross_pnl`, a nie tylko
`cost` — i złamałoby zasadę 4.

**Konsekwencja:** kraniec „maker" jest optymistyczny **nie tylko na opłatach, ale i na cenie**,
więc prawda leży **bliżej krańca taker**, niż sugerowałaby naiwna mieszanka pół na pół.

### Sprostowanie własnego błędu z H2.0

H2.0 policzyło próg **53,12%** z kosztu **bramkowego** `round_trip_cost_fraction(MAKER, TAKER)
= 0,0900%` — czyli tak, jakby KAŻDA transakcja wychodziła najdroższą nogą. Journal liczy koszt
per transakcja, a `tp` kosztuje 0,0400%. Faktycznie zmierzony koszt w S1b to **0,0767%**, czyli
próg **52,66%**.

| | próg |
|---|---|
| H2.0, koszt bramkowy 0,0900% | 53,12% ❌ |
| **faktycznie zmierzony, koszt 0,0767%** | **52,66%** ✔ |
| Z10 („najniższy próg w projekcie") | 52,69% — zgodne ✔ |

**Około 0,45 z rzekomej dźwigni 1,04 pp było artefaktem mojego rachunku, nie efektem nogi
timeout.** Realny efekt zmiany nogi to ~0,96 pp — i to przy założeniu, które powyżej podważyłem.

---

## Reguła decyzyjna — zapisana PRZED uruchomieniem czegokolwiek

Zabezpieczenie przed obniżeniem poprzeczki po obejrzeniu wyniku.

- **D1. Domyślna produkcyjna pozostaje `timeout_leg = TAKER`.** Ta runda z założenia nie może
  jej zmienić: spór jest o mechanikę rynku i rozstrzyga go argument o znanej cenie, nie słupki
  z backtestu. Zmiana domyślnej to osobna decyzja użytkownika z zapisanym uzasadnieniem.
- **D2. Pre-rejestrowany próg H2.1 wolno zrewidować WYŁĄCZNIE w stronę pesymistyczną.**
  Sprostowanie 53,12% → 52,66% — **TAK** (dotyczy obu krańców, niezależne od nogi timeout).
  Zejście do ~51,70% — **NIE**, dopóki obowiązuje D1.
- **D3. Jeśli oba krańce dają ten sam werdykt** — niepewność jest nieistotna decyzyjnie i tak
  się to zapisuje. Temat zamknięty na stałe. To najbardziej prawdopodobny i najcenniejszy wynik.
- **D4. Jeśli krańce rozstrzelają werdykt** — wynik brzmi **„NIEROZSTRZYGNIĘTE: decyzja zależy
  od nieznanej stopy wypełnienia"**, próg zostaje pesymistyczny, a jedyną drogą dalej jest runda
  **mierząca** tę stopę na danych o fillach (których nie mamy) — nie kolejne założenie.
- **D5. Licznik multiple-testing: 0 wariantów**, pod jawnym warunkiem, że raport respektuje
  zakaz z sekcji „Czego ta runda NIE raportuje". Precedens: **C2.12 policzono jako 1 wariant**
  właśnie dlatego, że raportował werdykt klasyfikacyjny na tych samych danych. Jeśli ta runda
  zacznie raportować werdykt — **konsumuje wariant H2 (0/1 → 1/1) i zamyka H2 przed H2.1**.
  Ten koszt jest zapisany z góry i to on dyscyplinuje.

---

## Projekt pomiaru (zapisany PRZED przebiegiem)

**Konfiguracja: ZAMROŻONA konfiguracja S1b** (`backtest/run_single_regime_4h.py:47-56`) —
4h natywne 6,8 roku, reżim `range`, V=3, walk-forward 60/28/28, `seed=42`.

Trzy powody: (1) **na tej konfiguracji target już widzieliśmy** (S1b opublikowane), więc
ponowny przebieg nie zużywa nowego spojrzenia; pomiar na konfiguracji H2.1 spaliłby darmowe
spojrzenie na baseline hipotezy, której jeszcze nie uruchomiliśmy; (2) konfiguracja H2.1 dziś
**nie jest uruchamialna** — `engine.py:223` filtruje po `regime`, więc „brak bramki" wymaga
zmiany silnika, co należy do H2.1 (zasada 4); (3) jest do czego porównać co do cyfry.

**Trzy przebiegi:** `timeout_leg=TAKER`, `timeout_leg=MAKER`, oraz kontrolny **bez argumentu**
(dowód bit-identyczności z baseline'em na realnych danych).

**Lista raportowanych liczb — zamknięta:** `cost_pct` średnia **i mediana** (zasada 16b) ·
rozbicie kosztu na **fee / slippage / funding** · `share_timeout` z CI · rozkład `exit_reason`
w sztukach · `barrier_pct` (asercja: identyczny) · `break_even_p` per wariant + delta w pp ·
**5 liczników lejka (muszą być identyczne co do sztuki)** · sprostowana tabela geometrii z H2.0.

**Walidacja drugą drogą (zasada 16a, obowiązkowa):** średni `cost_pct` z journalu vs policzony
analitycznie z mieszanki wyjść `s_tp·0,0004 + s_sl·0,0009 + s_to·(0,0009|0,0004) + funding`.

### Czego ta runda NIE raportuje i NIE interpretuje

**`hit_rate`, `ci_low`/`ci_high`, `z_stat`, `margin`, `classification` nie są wynikiem tej
rundy.** Trafiają do `raw_output.txt` (zasada 11 jest bezwarunkowa), ale sekcja „Wynik"
i decyzja ich nie używają.

Powód mechaniczny: `gross_pnl` jest z definicji niezależne od kosztu (pilnuje tego test
`test_run_backtest_gross_pnl_identical_across_timeout_leg`), więc `p` może się tu ruszyć
**wyłącznie przez selekcję** — inna ścieżka equity → inny moment kill-switcha. To byłby szum
selekcyjny, nie sygnał.

---

## Wynik

### 0. Kontrola wstępna — baseline nienaruszony

| kontrola | wynik |
|---|---|
| `final_equity` bez argumentu vs `timeout_leg=TAKER` | **identyczne** |
| journal transakcji | **identyczny** |
| lejek sygnałów odtwarza S1b | **tak** — `n_rows_evaluated=3 642`, abstynencja 3 297, `n=345` |

Runda nie jest cichą zmianą pipeline'u. Wszystkie wcześniejsze wyniki pozostają porównywalne.

### 1. Lejek sygnałów IDENTYCZNY — porównanie „jabłka do jabłek" z konstrukcji

| licznik | TAKER | MAKER | zgodne |
|---|---|---|---|
| `n_rows_evaluated` | 3 642 | 3 642 | ✔ |
| `n_signals_no_direction` | 3 297 | 3 297 | ✔ |
| `n_signals_confidence_gated` | 0 | 0 | ✔ |
| `n_signals_cost_gated` | 0 | 0 | ✔ |
| `n_signals` | **345** | **345** | ✔ |

Bramka kosztowa = **0,000900** w obu wariantach. To nie zbieg okoliczności, tylko skutek tego,
że `gate_cost_fraction` bierze **maksimum** po powodach wyjścia, a maksimum realizuje `sl`
(maker/taker) — niezależnie od nogi timeout. Różnica między wariantami **nie może** pochodzić
z innego zbioru sygnałów.

**Więcej, niż zakładała pre-rejestracja:** na realnych danych 4h **trafność jest identyczna
w obu wariantach** (47,5362%, `n=345`, te same `ci_low`/`ci_high`). Ścieżkowa zależność
kill-switcha, którą zmierzyłem na fiksturze syntetycznej (152 vs 120 stłumień), **tutaj się
nie zmaterializowała** — kill-switch nie odpalił ani razu inaczej. Zbiór transakcji jest ten sam
co do wiersza, więc jedyną różnicą jest koszt.

### 2. Koszt — główny przedmiot rundy

| miara (% nominału) | TAKER | MAKER | delta |
|---|---|---|---|
| koszt średni | **0,07670%** | **0,04670%** | −0,03000% |
| koszt mediana | 0,07500% | 0,04500% | −0,03000% |
| w tym fee + slippage | 0,07913% | 0,04913% | −0,03000% |
| w tym funding | **−0,00243%** | −0,00243% | 0 |

Rozkład wyjść (identyczny w obu): **75 `tp` / 63 `sl` / 207 `timeout`** z 345.

> **Udział timeoutów = 60,00%** (95% CI [54,83%; 65,17%]) — to jest dźwignia całego efektu.
> 60% transakcji zmienia nogę, 40% nie zmienia nic.

### 3. Próg opłacalności — PASMO

`barrier_pct` (B) = **0,014276 w obu wariantach** (kontrola sanity: ruszył się wyłącznie koszt).

| wariant | koszt C | break-even `p` |
|---|---|---|
| **TAKER** (domyślny, konserwatywny) | 0,07670% | **52,69%** |
| **MAKER** (optymistyczny kraniec) | 0,04670% | **51,64%** |

> **PASMO PROGU: [51,64%; 52,69%], szerokość 1,05 pp.**

### 4. Walidacja drugą drogą (zasada 16a) — zgodność co do cyfry

Koszt z journalu vs policzony analitycznie z mieszanki wyjść
`s_tp·0,0004 + s_sl·0,0009 + s_to·(0,0009|0,0004)`:

| wariant | analitycznie | z journalu (fee+slip) | zgodne |
|---|---|---|---|
| TAKER | 0,00079130 | 0,00079130 | **✔** |
| MAKER | 0,00049130 | 0,00049130 | **✔** |

### 5. Sprostowanie mojego błędu z H2.0 — rozbicie rzekomej „dźwigni 1,04 pp"

| źródło progu | wartość |
|---|---|
| H2.0, koszt **bramkowy** 0,0900% | **53,12%** ← zawyżone |
| H3 TAKER, koszt **realny** 0,0767% | **52,66%** |
| H3 MAKER, koszt realny 0,0467% | 51,62% |

Rzekoma dźwignia 1,04 pp rozpada się na dwie **różne** rzeczy:

| składnik | wielkość | czym jest |
|---|---|---|
| 53,12% → 52,66% | **0,46 pp** | **mój błąd rachunkowy** — użyłem kosztu bramkowego zamiast realnego |
| 52,69% → 51,64% | **1,05 pp** | realny efekt nogi timeout — ale oparty na założeniu, które sam podważyłem |

(53,12/52,66 liczone z `B_eff = 0,014424` z geometrii H2.0; 52,69/51,64 z `barrier_pct
= 0,014276` zmierzonego przez silnik — stąd 0,03 pp różnicy między tymi dwiema ścieżkami.)

### 6. Drugie sprostowanie — tym razem mojego PLANU tej rundy

W planie ostrzegałem: *„bramka pomija funding; na 4h/V=3 to ~0,015% wobec bramki 0,090%,
czyli ~17% — bramka jest ANTY-konserwatywna na funding"*. **Pomiar to obala:**

| | moje oszacowanie | zmierzone |
|---|---|---|
| funding jako % nominału | +0,0150% | **−0,00243%** |
| udział w bramce | 16,7% | **2,7%** |
| znak | koszt | **przychód** |

Dwa powody, dla których się pomyliłem: (a) założyłem trzymanie przez pełne `V=3` świece,
a realnie bariera pada wcześniej; (b) **nie uwzględniłem znaku** — short OTRZYMUJE dodatni
funding, a w próbie są obie strony. **Bramka, pomijając funding, jest więc lekko
KONSERWATYWNA, nie anty-konserwatywna.** Kandydat na osobną rundę **odpada** — nie ma czego
naprawiać.

---

## Co na plus (+)

- **Pre-rejestracja jest dowodliwa z historii gita**, nie tylko zadeklarowana: commit `707f7e0`
  zawiera wyłącznie reguły D1–D5 i poprzedza commit z kodem (`350e8b1`).
- **Runda odrzuciła własną tezę.** Podejrzenie z H2.0 („`timeout → taker` to błąd") nie broni
  się wobec kryterium „maker ⇔ cena znana przy składaniu zlecenia", a mój rachunek dźwigni był
  zawyżony o 0,46 pp. Obie rzeczy są zapisane jako sprostowania, nie przemilczane.
- **Naprawiona realna usterka strukturalna.** Bramka kosztowa miała własną, ręczną kopię reguły
  nóg i literał `exit_leg=TAKER`; nic nie wiązało jej z journalem. Teraz konsumuje
  `gate_cost_fraction`, a test `test_cost_gate_value_equals_gate_cost_fraction` pęka
  natychmiast, gdyby ktoś wrócił do literału. **Rozjazd stał się niemożliwy, nie tylko
  zakazany.**
- **Whitelist zamiast `else`.** Do tej rundy `exit_leg_for_reason("TP")` cicho zwracało TAKER —
  każda literówka była błędem niewidocznym w wyniku. Teraz `ValueError`.
- **Porównanie uczciwe z konstrukcji, nie z deklaracji:** bramka jest niewrażliwa na przełącznik,
  więc lejek jest identyczny co do sztuki — i jest to zaasertowane, nie obiecane.
- **Walidacja drugą drogą zgodna co do ósmego miejsca** (0,00079130 obiema drogami).
- **Dwa własne błędne założenia wyłapane przez testy**, zanim trafiły do wniosków: `gross_pnl`
  NIE jest niezależne od kosztu (skaluje się z wielkością pozycji), a zbiór transakcji może się
  różnić przez kill-switch.

## Co na minus (−)

- **Runda nie zbliża projektu do GO ani o krok.** Jej wartość jest wyłącznie informacyjna:
  wiemy, że niepewność jest nieistotna decyzyjnie, i mamy o jedną usterkę mniej.
- **Pomiar nie rozstrzyga sporu mechanicznego** i nie mógł — spór jest o to, czy zlecenie limit
  na barierze pionowej by się wypełniło, a tego backtest nie widzi. Rozstrzyga go argument
  o znanej cenie, nie słupki.
- **Kraniec MAKER jest optymistyczny podwójnie** i to pozostaje niezmierzone: nie tylko na
  opłatach, ale i na CENIE (`_resolve_exit_price` bierze `close` świecy timeoutu, a tego `close`
  nie da się dostać limitem bez lookaheadu). Realna prawda leży bliżej krańca TAKER, niż
  sugeruje szerokość pasma — ale **o ile bliżej, nie wiemy**.
- **Adverse selection nadal niemodelowana w OBU krańcach** — to samo ograniczenie co od C2.12.
- **Pasmo zmierzone na JEDNEJ konfiguracji** (S1b: 4h, `range`, V=3). Przy innym `V` udział
  timeoutów byłby inny, a z nim szerokość pasma — przy V=12 timeouty to 20% (zmierzone w H2.0),
  więc pasmo byłoby ~3× węższe.
- Dwie moje liczby z poprzednich dokumentów okazały się błędne (próg 53,12% i ostrzeżenie
  o funding). Obie trafiły do repo, zanim je sprawdziłem.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Kluczowa liczba przeliczona drugą, niezależną drogą:** średni koszt z journalu vs policzony
  analitycznie z mieszanki wyjść — **zgodny co do ósmego miejsca po przecinku** w obu wariantach
  (sekcja 4). To nie jest ta sama ścieżka obliczeniowa: journal sumuje koszt per transakcja
  w silniku, walidacja mnoży udziały typów wyjść przez stawki z `costs.py`.
- **Kontrola bit-identyczności baseline'u na realnych danych** (nie tylko na fiksturze):
  `final_equity` i cały journal identyczne, lejek odtwarza S1b (`n=345`).
- **Kogo NIE ma w zbiorze:** (a) **3 297 z 3 642 ocenionych świec** to abstynencja modelu
  (90,5%) — pasmo obowiązuje na 345 transakcjach, nie na historii; (b) **22 pominięte foldy
  z 85** — w S1 ustalono, że to systematycznie okna szybkich ruchów (Mann-Whitney p=4,9e-03),
  więc **to ograniczenie przechodzi na tę rundę w całości**; (c) **tylko BTC, tylko `range`,
  tylko V=3** — przy innym `V` udział timeoutów, a więc szerokość pasma, byłby inny;
  (d) **krach COVID poza zbiorem**; (e) **adverse selection nie jest w żadnym z krańców** —
  pasmo mierzy niepewność co do OPŁAT, nie co do wypełnialności; (f) funding modelowany jedną
  stałą, nie pobranym szeregiem (mamy go od H2.0, ale użycie go tutaj byłoby drugą zmianą
  w jednej rundzie).
- **Red-flag „wynik idealnie potwierdza hipotezę":** nie zachodzi — runda **obala tezę, która
  ją zamówiła**, i prostuje dwie moje wcześniejsze liczby, obie w stronę niekorzystną dla
  pierwotnego pomysłu.
- **Ograniczenie werdyktu:** wniosek D3 („niepewność nieistotna decyzyjnie") opiera się na
  porównaniu obu końców pasma z **opublikowaną** trafnością zbiorczą projektu (50,27%, Z10),
  a **nie** z trafnością zmierzoną w tej rundzie — zgodnie z regułą D5.

## Przegląd diffu (zasada 16c)

Diff dotyka dwóch plików produkcyjnych i trzech testowych; nowy parametr ma domyślną wartość
baseline'u i jest przeprowadzony przez wszystkie warstwy bez rozgałęzień, bramka została
wyprowadzona z tej samej funkcji co journal (usuwając klasę błędu, a nie jej instancję),
walidacja wejść zamieniona z cichego `else` na `ValueError`, a regresja bit-identyczności jest
zaasertowana zarówno na fiksturze, jak i na realnych danych — **werdykt: gotowe do merge.**

## Wniosek

**Niepewność co do nogi „timeout" jest NIEISTOTNA DECYZYJNIE — reguła D3.**

Próg opłacalności mieści się w paśmie **[51,64%; 52,69%]**. Zbiorcza trafność projektu,
zmierzona na 7 687 transakcjach i opublikowana w Z10, wynosi **50,27%** (CI [49,15%; 51,38%]).
Wymagany przyrost trafności to:

| kraniec pasma | próg | wymagany przyrost nad 50,27% |
|---|---|---|
| MAKER (optymistyczny) | 51,64% | **+1,37 pp** |
| TAKER (domyślny) | 52,69% | **+2,39 pp** |

**Obie liczby są większe niż cokolwiek, co jakakolwiek pojedyncza cecha dała w tym projekcie**
(`adx_14`: ~0 — C2.8; wszystkie 17 kandydatek z C2.7: |korelacja| z targetem < 0,065). Werdykt
jest więc ten sam na obu końcach pasma, a wybór założenia go nie zmienia.

Co do samego sporu: **obecny model jest najprawdopodobniej poprawny.** Noga maker wymaga znanej
CENY, a przy barierze pionowej znamy tylko CZAS. Co gorsza, wariant maker byłby wewnętrznie
niespójny z tym, jak silnik liczy cenę wyjścia timeoutu (`close` tej świecy), więc naliczałby
tańszą opłatę za cenę osiągalną wyłącznie drogo.

## Rekomendacja

1. **`timeout_leg = TAKER` pozostaje domyślne (reguła D1).** Runda tego nie zmienia i nie mogła.
2. **Próg dla H2.1 sprostowany na 52,66% → 52,69%** (wartość zmierzona przez silnik, nie
   z geometrii przybliżonej). **Poprzeczka NIE zostaje obniżona do 51,64%** — reguła D2.
   Wymagany przyrost trafności dla H2.1: **+2,39 pp**, nie +2,85 pp jak zapisano w H2.0.
3. **Licznik H2 pozostaje 0/1** — runda nie raportowała werdyktu klasyfikacyjnego ani
   trafności jako wyniku (warunek D5 spełniony; liczby objęte zakazem są w `raw_output.txt`,
   sekcja 6, wraz z jawną adnotacją, że nie uczestniczą w decyzji).
4. **Temat nogi timeout ZAMKNIĘTY na stałe.** Powrót do niego wymaga ŹRÓDŁA DANYCH
   o wypełnieniach zleceń limit, nie kolejnego założenia (zapisane w `docs/rag/04`).
5. **Kandydat „bramka pomija funding" WYCOFANY** — pomiar pokazał, że pominięcie działa
   w stronę konserwatywną i waży 2,7% bramki, nie 17%.
6. **Następny krok: H2.1** — funding jako 11. cecha, bez bramki reżimu, 4h, próg `ci_low > 52,69%`.

## Pełny surowy output

[`raw_output.txt`](raw_output.txt). Skrypt: [`backtest/run_timeout_leg_band.py`](../../backtest/run_timeout_leg_band.py).
