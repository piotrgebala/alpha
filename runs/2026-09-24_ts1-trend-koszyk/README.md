# TS1 — podążanie za trendem (momentum w czasie) na koszyku top-20 perpetuali (2026-09-24)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY, ale NAJSILNIEJSZY ŚLAD W PROJEKCIE:** +14,8 %/rok
> netto [−1,7; +31,3], t_neff 1,76 (wymagane 1,96) — kryterium niespełnione o włos; ponad
> WSZYSTKIMI 100 portfelami kontrolnymi; bootstrap blokowy [+1,1; +29,3]; dodatni w 6/6 lat
> i 7/7 faz; średnio neutralny na rynek (korelacja z „zawsze long” −0,19). Pre-rejestracja
> `d066412` → przebieg → wynik w commicie scalającym. **Seria TS: 1/1, STOP.** Walidacja
> (16a): **READY z zastrzeżeniami (Caveats)**; przegląd diffu (16c): **Approve**.
> Decyzja użytkownika 2026-09-23: „testuj dalej
> różne kombinacje" oraz doprecyzowanie „kontrakty futures z dźwignią 3×, longi i shorty".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Reguła „graj z trendem każdej monety” zarabiała po kosztach ok. 15 % rocznie przez 5,4 roku,
w każdym roku na plusie.** To najlepszy wynik w całym projekcie. Formalnie jednak nie wystarcza:
przedział niepewności sięga od −2 % do +31 % rocznie, więc zero nie jest wykluczone. Test
wymagał t powyżej 1,96, wyszło 1,76. Dwa inne sposoby liczenia niepewności mówią „ponad zerem”.
Przy ~24 testach z ostatnich dwóch dni jeden taki „prawie sukces” mógł też wyjść z przypadku.
**Dźwignia:** przy pozycjach dobranych regułą portfel zużywa średnio tylko 0,4× kapitału.
Podbicie go do 3× kapitału dałoby **gorszy** wynik (ok. +5 %/rok) z obsunięciem 90 %, bo duże
wahania zjadają zysk. Rozsądna dźwignia dla takiej strategii to ok. 1,5–2× kapitału, nie 3×.

---
> **NOWA SERIA TS (rodzina A1 katalogu na horyzoncie tygodniowym, uniwersum wielu monet),
> licznik 1/1, STOP.** Kandydat wybrany przez panel „co dalej" (5 propozycji, 2026-09-23/24):
> jedyny, który pasuje do sposobu handlu użytkownika (zakład o kierunek, long i short,
> perpetuale) i przechodzi bramę danych oraz mierzalności.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Każda moneta z 20 największych dostaje co tydzień własny zakład: **long, jeśli przez ostatnie
4 tygodnie urosła, short, jeśli spadła**. Wielkość pozycji zależy od tego, jak bardzo moneta się
waha: spokojniejsza dostaje więcej, rozchwiana mniej. Nigdy więcej niż 3× na jedną monetę, bo
tak handlujesz. To klasyczne „podążanie za trendem” z rynków futures, które działało przez ponad
sto lat na surowcach i obligacjach. Nikt w projekcie go jeszcze nie sprawdzał na horyzoncie
tygodni. Wcześniej mierzyliśmy tylko ruchy do 4 godzin i model odwracania ruchu na świecach
dziennych.

Uczciwie z góry: pomiar rozstrzygnie tylko **silny** trend. Szum na 5,4 roku danych wynosi
±18 % rocznie. Jeśli trend w krypto jest tak dobry jak w podręcznikach, zobaczymy go na granicy.
Jeśli jest słabszy, wynik wyjdzie nierozstrzygnięty.

## ID testu

**TS1** — nowa seria TS (momentum w czasie), licznik 1/1, STOP. Nazwa „TS”, bo „T1” to już
diagnostyka fundingu z 2026-09-22. Inne okna sygnału, inne cele zmienności, inne rebalanse,
sam BTC, inne uniwersum = warianty tej serii, zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `t1-trend-tsmom`.
- Dane: `data/raw/universe` (P2: świece 1d i funding CAŁEGO uniwersum USDT-M, łącznie z
  wycofanymi kontraktami, więc bez błędu przeżywalności), obcięte do **2021-01-01 → 2026-06-30**
  (zasada 20): 281 symboli; skład miesięczny top-20 po średnim obrocie z 30 dni przed miesiącem
  (`rebalance_premium.monthly_members`, jak X1/R1): 65 koszyków, 119 różnych symboli.
- Kod: `backtest/ts_momentum.py` (czyste funkcje, numpy) + `tests/test_ts_momentum.py` (13 testów:
  sygnał, test przyszłości sygnału i σ̂, σ̂ na stałych zwrotach, wagi z sufitem, symetria znaku
  w `hypothesis`, P&L = 0 przy płaskich cenach, pierwszy zwrot dzień po formowaniu, znak fundingu,
  fazy, H0). Skrypt: `backtest/run_ts_momentum_ts1.py` (na `runs/ZAMROZONE.txt`).
- Komendy: `PYTHONUTF8=1 py -m backtest.run_ts_momentum_ts1 --moc 100` → `moc.txt` (przed
  przebiegiem); `PYTHONUTF8=1 py -m backtest.run_ts_momentum_ts1` → `raw_output.txt`.

## Poprzedzające wyniki

- **Wniosek 69 (Y1/Y2):** kierunek BTC z cech wykresu na 1h/4h/1d — 48–50 % trafności wszędzie;
  „dalsze badanie horyzontu dziennego wymaga INNEGO zbioru informacyjnego lub INNEJ formuły”.
  TS1 zmienia FORMUŁĘ (reguła bez modelu, portfel wielu monet, skalowanie zmiennością) i
  HORYZONT (sygnał 28 dni, trzymanie 7 dni). Zbiór informacyjny pozostaje ten sam (ceny) — to
  słabość zapisana z góry (wnioski 11 i 69).
- **M1 (wniosek 35):** momentum na 4h z horyzontem 12 h — 49,7 %. **A2 (wnioski 51–53):** stan
  średnich, wybicie, struktura trendu na 4h — reguły „z ruchem” poniżej monety. Oba mierzyły
  horyzont godzin, na którym działa odwracanie; literatura lokuje momentum w tygodniach.
- **X1/X2 (wnioski 64–68):** momentum PRZEKROJOWE (mocne monety kontra słabe, neutralne na
  rynek) — +22 %/rok i +16 %/rok, nierozstrzygnięte; X1 wrażliwe na dzień tygodnia rebalansu.
  TS1 pyta o coś innego: czy KAŻDA moneta (i cały rynek) trzyma kierunek przez tygodnie —
  ekspozycja netto na rynek jest tu dozwolona i jest częścią zakładu. Wniosek 68 wymusza
  **7 faz tygodniowych naraz** — mierzona jest ich średnia.
- **Audyt dźwigni 3× (2026-09-23/24, bez katalogu — pytanie użytkownika):** werdykty projektu są
  liczone na jednostkę pozycji i nie zależą od dźwigni; 3× mnoży zysk, stratę i koszty; przy
  stałej 3× wyłącznik awaryjny i likwidacje zmieniają obraz. TS1 raportuje przełożenie na
  dźwignię jawnie (sekcja 4 wyniku).

## Pre-rejestracja

- **Hipoteza:** portfel momentum w czasie na top-20 perpetuali ma dodatni średni zwrot netto
  (po opłatach, poślizgu i realnym fundingu).
- **Mechanizm:** opóźniona reakcja na informację i stadne dołączanie do ruchu (likwidacje,
  stopy, FOMO); po drugiej stronie grający przeciw trendowi i zabezpieczający się
  (Moskowitz–Ooi–Pedersen 2012; Hurst–Ooi–Pedersen 2017). Nie wiemy, czy efekt przetrwał
  instytucjonalizację krypto po 2021 — prior umiarkowany.
- **DOKŁADNIE JEDNA zmienna:** reguła znaku (momentum w czasie) wobec braku zakładu; wszystkie
  parametry z literatury, bez siatki: okno sygnału **28 dni** (to samo co X1, najkrótsze
  z literatury 1–4 tygodni dla krypto → najwięcej epizodów), **σ̂ = √(365·EWMA(r², com = 60))**
  z danych ≤ t, **cel 40 %/rok na pozycję**, **sufit 3×** na monetę (zasada 5, `min()`), wagi
  1/N, formowanie co 7 dni, **7 faz po 1/7 kapitału**; koszt taker 0,05 % + poślizg 2 bps
  × obrót; funding realny per symbol (long płaci przy dodatniej stawce); wycofany kontrakt =
  gotówka.
- **Przyrząd i kryterium (jedno ramię, m = 1)** na dziennym szeregu zwrotu netto portfela
  (średnia 7 faz, % kapitału), CI z N_eff (`carry_hedged.summarize_pnl`):
  - **POZYTYWNY:** `t_neff > 1,96` ORAZ średnia powyżej **97,5 percentyla H0**;
  - **NEGATYWNY:** górny kraniec CI 95 % średniej poniżej zera;
  - inaczej **NIEROZSTRZYGNIĘTY**.
  Trafność (udział dni na plusie) NIE jest przyrządem — zwroty trendu są skośne (mało trafień,
  duże wygrane).
- **H0 (kontrola, 0 wariantów):** 100 portfeli z PRAWDZIWYMI znakami przesuniętymi cyklicznie
  w czasie o losową liczbę tygodni (≥ 8 tygodni od zera) — ta sama trwałość i ta sama zgodność
  znaków między monetami, te same wagi, koszty i funding; zniszczone jest tylko trafienie
  w moment. **Zmiana przed pre-rejestracją, z powodem:** pierwsza wersja H0 (niezależne losowe
  znaki per moneta, trwałość p_flip 0,214) dawała zmienność portfela 3,2 %/rok zamiast ~21 %,
  bo niezależne znaki znoszą się w koszyku skorelowanych monet — kontrola byłaby za łagodna.
  Obie wersje w `moc.txt`.
- **Mierzalność (zasada 18, `moc.txt`, bez patrzenia na regułę):** 1 969 dni; zmienność H0
  ~21,3 %/rok; se średniej empiryczne 7,3 %/rok (analityczne 9,2 %/rok — kryterium bierze
  większe); **half-width 95 % = 17,9 %/rok = 0,84 jednostki Sharpe'a**; q97,5 H0 = +13,0 %/rok.
  Obietnica literatury: zdywersyfikowany trend ~1 SR (MOP 2012) → przy zmienności ~21 %
  ≈ +21 %/rok > 17,9 → **MIERZALNA dla efektu podręcznikowego**; efekty 0,3–0,5 SR
  (6–11 %/rok) są **niewidoczne** — zapisane z góry. Moc 80 % wymaga SR ≥ ~1,2.
- **Oczekiwanie zapisane z góry:** NIEROZSTRZYGNIĘTY najbardziej prawdopodobny. Rynek
  2021–2026 miał kilka wielkich trendów (hossa 2021, bessa 2022, hossa 2024), więc wynik może
  zależeć od 2–3 epizodów — raport roczny obowiązkowy.
- **Opisowo (0 wariantów, bez werdyktu):** (a) „zawsze long” z tymi samymi wagami i różnica
  parowana TS1 − long (czy zysk to tylko dryf rynku); (b) sam BTC tą samą regułą; (c) 7 faz
  osobno (rozrzut); (d) przełożenie na dźwignię: mnożnik wag do brutto 3× kapitału i dźwignia
  Kelly'ego — CAGR i maksymalne obsunięcie (bez likwidacji; likwidacja wymaga dziennych
  high/low, których cache dla monet spoza BTC nie ma).
- **Kontekst multiple testing:** ~23 odczyty z 2026-09-23/24 w różnych seriach; TS1 to jedno
  ramię z własnym licznikiem.
- **Czego runda NIE robi:** nie stroi okna, celu zmienności ani dnia rebalansu; nie filtruje
  monet po wyniku; nie odwraca znaku; nie łączy z X1.

---

## Wynik

Pełny stdout: `raw_output.txt` (63 s). Dzienny szereg netto, średnia 7 faz, % kapitału,
1 969 dni (2021-02-08 → 2026-06-30).

| miara | wartość |
|---|---|
| średni zwrot netto | **+14,8 %/rok [−1,7; +31,3]** (CI z N_eff; N_eff = n = 1 969) |
| średni zwrot brutto | +17,4 %/rok [+0,9; +34,0] |
| t / t_neff | **+1,76 / +1,76** (próg 1,96) |
| H0 (100 portfeli, znaki przesunięte w czasie) | średnia −1,3 %/rok, q97,5 +13,0 %/rok; **TS1 ponad 100 % portfeli H0** |
| zmienność | 19,6 %/rok; mediana dnia +0,021 % vs średnia +0,041 %; skośność +0,13 |
| nominał brutto / netto | mediana 0,41× kapitału (p10 0,28, p90 0,52) / średnio −0,04× (dni netto-long 42 %) |
| Σ brutto / funding / koszt / netto | +94,1 % / −9,4 % / 4,6 % / +80,0 % (obrót 12,3 kapitału/rok) |
| **werdykt** | **NIEROZSTRZYGNIĘTY** (t_neff < 1,96; drugi warunek — ponad q97,5 H0 — spełniony) |

**Per rok:**

| rok | dni | Σ netto | Σ funding | zmienność | nominał netto |
|---|---|---|---|---|---|
| 2021 (od 8.02) | 327 | +23,9 % | −4,3 % | 17,7 % | +0,02× |
| 2022 | 365 | +10,2 % | −1,3 % | 20,8 % | −0,14× |
| 2023 | 365 | +13,6 % | −0,7 % | 20,2 % | −0,01× |
| 2024 | 366 | +9,4 % | −2,6 % | 19,1 % | +0,03× |
| 2025 | 365 | +20,1 % | −0,4 % | 20,7 % | −0,08× |
| 2026 (do 30.06) | 181 | +2,8 % | −0,1 % | 17,3 % | −0,09× |

**7 faz osobno (%/rok):** +12,1 / +9,6 / +16,0 / +17,2 / +17,3 / +16,2 / +17,3 — rozrzut 7,7 pp,
wszystkie dodatnie (X1 miało rozrzut +9 do +22 i zależało od fazy — tu mniej).

**Opisowo (0 wariantów):**

| portfel | zwrot netto [CI] | t_neff |
|---|---|---|
| zawsze long, te same wagi | +1,5 %/rok [−23,0; +26,1] | +0,12 |
| TS1 − zawsze long (parowo) | +13,3 %/rok [−18,8; +45,4] | +0,81 |
| sam BTC tą regułą | +21,4 %/rok [−7,7; +50,5] | +1,44 |

Korelacja TS1 z „zawsze long” −0,19: zysk NIE pochodzi z dryfu rynku (koszyk top-20 jako całość
zarobił w tym okresie ~0).

**Przełożenie na dźwignię** (mnożnik k wag reguły, z kapitalizacją, BEZ likwidacji):

| dźwignia | CAGR | max obsunięcie |
|---|---|---|
| k = 1 (reguła, ~0,4× kapitału brutto) | +13,8 %/rok | 17,9 % |
| k = 7,33 (brutto **3× kapitału**) | **+4,9 %/rok** | **90,2 %** |
| k Kelly = 3,88 (in-sample, optymistyczny) | +33,3 %/rok | 59,0 % |

Pełna dźwignia 3× niszczy wynik: zmienność ~145 %/rok zjada średnią (drag σ²/2). Kelly liczony
na tej samej próbie jest górnym ograniczeniem, nie zaleceniem — praktyka to ½ Kelly lub mniej
na skurczonej estymacie (~1,5–2× wag reguły, czyli ~0,6–0,8× kapitału brutto).

## Co na plus (+) / Co na minus (−)

**(+)**
- Najbliżej sukcesu w projekcie: t 1,76; ponad wszystkimi 100 portfelami kontrolnymi;
  bootstrap blokowy (28 dni) daje CI [+1,1; +29,3] — dwie z trzech dróg mówią „ponad zerem”.
- Spójność: 6/6 lat dodatnich, 7/7 faz dodatnich (rozrzut 7,7 pp), w bessie 2022 też plus.
- Nie jest to beta rynku: zawsze-long ~0, korelacja −0,19, nominał netto średnio −0,04×.
- Koszty i funding policzone realnie (−9,4 % i 4,6 % za 5,4 roku) — nie są wąskim gardłem.
- Pre-rejestracja przed przebiegiem, parametry z literatury bez siatki, H0 poprawione PRZED
  rejestracją (z powodem zapisanym).

**(−)**
- **Kryterium pre-rejestrowane NIESPEŁNIONE** (t_neff 1,76 < 1,96). Bootstrap i H0 to drogi
  opisowe; nie wolno po wyniku zmienić przyrządu na ten, który „przechodzi”.
- **Multiple testing:** ~24 odczyty w dwa dni. Przy tylu testach jeden wynik z t ≈ 1,8 jest
  spodziewany z przypadku (p ≈ 0,04 jednostronnie; Bonferroni dla 24 → próg ~3,0).
- **Zależność od ogonów:** bez 10 najlepszych dni +6,1 %/rok (bez 10 najgorszych +22,6 %).
- **Ten sam zbiór informacyjny co wszystkie porażki** (ceny) — nowa jest formuła, nie wiedza.
- **Kogo nie ma:** styczeń 2021 (rozgrzewka), członkowie bez 28 dni historii lub bez σ̂
  (świeże listingi — pomijane), 2 wycofane kontrakty (EOS, FRONT — gotówka po ostatniej cenie).
  Brak modelu likwidacji dla monet spoza BTC (cache ma tylko zamknięcia) — przy k = 1 (~0,1×
  na monetę) nieistotne; przy 3× kapitału istotne i pominięte, czyli wynik 3× jest ZAWYŻONY.
- Sam BTC +21 %/rok, ale CI [−8; +51] — pojedyncza moneta nie wystarcza.

## Walidacja (zasada 16a)

Skill `data:validate-data` wczytany PRZED walidacją. Werdykt: **READY z zastrzeżeniami
(Caveats)** — liczby się zgadzają; zastrzeżenia do komunikacji: kryterium niespełnione,
multiple testing, zależność od ogonów, 3× bez likwidacji.

- **Druga droga (niezależna):** `walidacja.py` liczy fazę 0 pętlą w pandas po słownikach pozycji,
  z własnym sygnałem, własną EWMA i własnym dryfem, bez funkcji `ts_momentum` — **+12,14 %/rok**
  wobec +12,1 %/rok ze skryptu ✓.
- **Trzecia droga dla niepewności:** bootstrap blokowy 5 000 × bloki 28 dni: [+1,1; +29,3] %/rok,
  1,9 % bootstrapów ≤ 0 (opisowo; kryterium pozostaje t_neff).
- **Spójność:** Σ brutto + funding − koszt = 94,1 − 9,4 − 4,6 = 80,1 ≈ Σ netto 80,0 ✓
  (zaokrąglenia); lata sumują się do Σ netto (23,9 + 10,2 + 13,6 + 9,4 + 20,1 + 2,8 = 80,0) ✓.
- **Kogo nie ma:** jak w (−). **Red flag „wynik idealnie potwierdza”:** nie — kryterium
  niespełnione; spójność lat i faz jest mocna, ale zależność od ogonów i multiple testing
  hamują wniosek.
- **Bramka 16b** (`data:statistical-analysis`): efekt z CI, mediana obok średniej, trzy drogi
  niepewności opisane jako takie, per rok/faza opisowo, Kelly oznaczony jako in-sample,
  kontekst ~24 odczytów.

## Przegląd diffu (zasada 16c)

Skill `engineering:code-review` wczytany PRZED przeglądem. Diff: `backtest/ts_momentum.py`,
`backtest/run_ts_momentum_ts1.py`, `tests/test_ts_momentum.py` (13), `runs/ZAMROZONE.txt`, katalog rundy.

- Korektność: sygnał i σ̂ z danych ≤ t (test przyszłości na 3 cięciach); pierwszy zwrot dzień po
  formowaniu (test); funding ze znakiem wagi (test: long płaci, short dostaje); dryf wag
  w·(1+r)/(1+g) poprawny także dla shortów (w < 0); wycofany = zwrot 0 i funding 0.
- Edge-case'y: brak ważnych członków → wagi 0; `1 + g ≤ 0` → pozycje zerowane; końcowe dni,
  w których nie wszystkie fazy mają pozycję, odcięte (`dropna`).
- Drobne: dryf ignoruje funding w mianowniku (efekt rzędu 0,01 %/dzień, bez znaczenia);
  `MarkovSigns` zostaje tylko dla `--moc` (udokumentowane odrzucenie).
- Testy 786/786, ruff/black czyste.

**Werdykt jednym zdaniem: Approve** — silnik jest mały, przetestowany na własnościach, które
decydują o wyniku (brak lookaheadu, znak fundingu, sufit), i potwierdzony niezależną pętlą.

## Wniosek

**Prostym językiem:** to pierwszy pomysł w projekcie, który przez ponad 5 lat zarabiał w każdym
roku: **ok. +15 % rocznie po kosztach**, grając każdą z 20 największych monet w kierunku jej
trendu z ostatnich 4 tygodni. Nie jest to zasługa hossy, bo sam „zawsze long” na tych monetach
nie zarobił nic. Ale dowodem to jeszcze nie jest: niepewność jest duża (od −2 % do +31 %),
test wymagany przed startem nie przeszedł minimalnie, a przy tylu próbach z ostatnich dni jeden
taki wynik mógł wyjść przypadkiem. Ważne dla Ciebie: **3× dźwigni na tej strategii to zły
pomysł** — przy 3× kapitału wynik spada do ok. +5 % rocznie z obsunięciem 90 %.

**Technicznie:** NIEROZSTRZYGNIĘTY (t_neff 1,76; q97,5 H0 przekroczone; bootstrap CI > 0).
Rodzina „momentum w czasie na koszyku” ma najsilniejsze poparcie w projekcie, obok X1 (momentum
przekrojowe, t 1,58). Obie są wariantami „ceny trzymają kierunek przez tygodnie”.

## Rekomendacja

1. **Seria TS: 1/1, STOP.** Warianty (okno 12 tygodni, inny cel zmienności, top-50, sam BTC)
   na tych samych danych są zakazane bez decyzji użytkownika — każdy kolejny odczyt na tej
   samej historii tylko zwiększa szansę przypadkowego „sukcesu”.
2. **Jedyna uczciwa droga rozstrzygnięcia: test na żywo bez pieniędzy (paper trading)**, reguła
   zamrożona co do bajtu, 7 faz, od 2026-07-01 (dane jeszcze nieoglądane) — przy obecnym szumie
   ~2 lata na odróżnienie +15 %/rok od zera tylko przy dobrym przebiegu; to decyzja użytkownika.
3. Jeśli użytkownik chce grać tę regułę realnym kapitałem mimo braku dowodu: najwyżej 1–2× wag
   reguły (≈ 0,4–0,8× kapitału brutto), marża izolowana, nie 3× kapitału.

## Użyte skille

Rejestr `runs/skille/t1-trend-tsmom.jsonl` (`py tools/skill_audit.py raport --galaz
t1-trend-tsmom`): **6 wczytań, 6 różnych skilli**, wszystkie przez Claude'a, przed pracą.

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź przed skillami, pre-rejestracja w commicie przed przebiegiem, katalog, bramki, DoD. |
| `anthropic-skills:clas5-quant` | pułapki: ten sam zbiór informacyjny, beta w hossie (→ porównanie z zawsze-long), 7 faz (wniosek 68), trafność jako zły przyrząd dla skośnych zwrotów, σ̂ bez lookaheadu. |
| `engineering:testing-strategy` | plan 13 testów: test przyszłości, własności w `hypothesis`, znak fundingu, P&L przy płaskich cenach. |
| `data:validate-data` | druga, naprawdę niezależna droga (pętla pandas), „kogo nie ma”, red-flagi, werdykt Caveats. |
| `data:statistical-analysis` | trzy drogi niepewności opisane uczciwie (kryterium ≠ bootstrap), multiple testing, Kelly in-sample. |
| `engineering:code-review` | przegląd diffu — werdykt wyżej. |

`quant-strategy-catalog` wczytany przy wyborze kandydata na master (rejestr `master.jsonl`,
commit przed gałęzią). **Pominięte (z powodem):** `dataviz` — bez wykresu; `engineering:debug`
— bez błędu (chwilowa blokada DLL TA-Lib przez Windows ustąpiła sama); `data:explore-data` —
dane uniwersum z P2 już profilowane.
