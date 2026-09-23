# X1 — momentum przekrojowe: czy zwycięzcy ostatnich 4 tygodni wygrywają dalej? (2026-09-23)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY wg kryterium, punktowo WYRAŹNIE DODATNI: +22,0 %/rok
> netto [−5,3; +49,3], t_neff 1,58; dodatni w każdym z 6 lat, ale 2025 daje połowę sumy.**
> Pierwszy wynik w projekcie z dodatnim punktowo odczytem zakładu o KIERUNEK (relatywny).
> Obietnica literatury (52 %/rok) na granicy wykluczenia (CI brutto [−3,0; +51,5]). Rachunek
> mocy z symulacji losowych rankingów (wniosek 58) trafił w rząd wielkości (21 vs 27 %/rok
> ex post). Kolejność w gicie: pre-rejestracja + kod + moc `dfca77b` → przebieg → wynik
> w commicie scalającym. **Seria X: 1/1, STOP.** Walidacja (16a): **READY**; przegląd diffu
> (16c): **Approve**. Decyzja użytkownika 2026-09-23: „sprawdź wszystkie warianty".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Kupowanie co tydzień pięciu monet, które przez ostatnie 4 tygodnie rosły najmocniej,
i granie na spadek pięciu, które spadały najmocniej, dało przez 5,4 roku +119 % kapitału po
kosztach — średnio +22 % rocznie.** Ale przedział niepewności sięga od −5 % do +49 % rocznie,
więc formalnie **nie udowodniliśmy, że to nie jest szczęście**: potrzeba ~4× dłuższej historii
(albo dużo szerszego koszyka), żeby taki efekt odróżnić od zera.

**Co za tym przemawia:** zysk był dodatni w każdym roku (od +8 % do +62 %), nie zależy od
kierunku całego rynku (korelacja z bitcoinem −0,13), nie pochodzi z kilku dni (bez 20
najbardziej skrajnych dni średnia jest taka sama), a niezależne przeliczenie tygodniami daje ten
sam wynik. Zysk bierze się głównie z nogi „na spadek": monety, które już spadały, spadały
dalej (w 2025 noga short straciła 109 % wartości — czyli zarobiła tyle dla nas).

**Co osłabia:** rok 2025 daje 62 z 119 punktów; bez niego to ~13 % rocznie. Koszty (3 %/rok)
i funding (+1 %/rok) są drugorzędne. To jeden wariant (1/1) w dniu, w którym projekt zamknął
kilka innych serii — pojedynczy dodatni punkt nie jest jeszcze dowodem.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

R1 pokazało, że w koszyku 20 największych kryptowalut te, które rosły w ostatnich tygodniach,
raczej rosły dalej (dlatego codzienne wyrównywanie koszyka traciło). X1 sprawdza to wprost:
co tydzień kupujemy pięć monet z najlepszym zwrotem z ostatnich 4 tygodni i jednocześnie
gramy na spadek pięciu z najgorszym. Taki portfel nie zależy od tego, czy cały rynek rośnie
czy spada — mierzy tylko, czy „zwycięzcy" dalej wygrywają z „przegranymi". Liczymy zysk po
kosztach: prowizji za co-tygodniową wymianę składu i opłacie funding (za pozycje na wzrost
trzeba płacić, gdy monety są „gorące").

**Czego się spodziewamy (przed wynikiem):** literatura (Liu–Tsyvinski–Wu 2022) obiecuje na
szerokim uniwersum 1–3 % tygodniowo brutto. Na 20 największych monetach po obrocie i po
kosztach zakładamy ostrożnie **1 %/tydzień ≈ 52 %/rok** jako „obietnicę podręcznika"; rachunek
mocy (niżej) mówi, czy taka wielkość jest w ogóle odróżnialna od zera na 5,4 roku.

## ID testu

**X1** — nowa hipoteza, rodzina **B1** katalogu (momentum przekrojowe). Pięć pól: OHLCV wielu
aktywów · formuła PRZEKROJOWA · target: kierunek RELATYWNY (long top / short bottom) · horyzont
tygodniowy · status: NIETKNIĘTE → po X1 ZMIERZONE. **Własny licznik: 1 wariant. Reguła STOP:
1/1** — inne okna sygnału (7/14/21/56 dni), inne trzymanie, inne kwantyle, inne N, wagi
kapitalizacyjne, wersja long-only to WARIANTY TEJ SAMEJ rodziny (families.md B1) i po STOP są
zakazane bez nowej decyzji użytkownika.

## Metadane

- Branch: `x1-momentum-przekrojowe` (od `master` @ `b700754`).
- Dane: uniwersum P2 (`data/raw/universe/*_1d.parquet`, 287 symboli z wycofanymi; funding
  `*_funding.parquet` per symbol, sumowany do dnia UTC); okno bazy `2021-02-01 → 2026-07-01`
  (pierwszy miesiąc z pełnym oknem obrotu wewnątrz 2021, jak R1; zasada 20).
- Uniwersum point-in-time: `rebalance_premium.monthly_members` (top-20 po średnim obrocie
  z 30 dni PRZED początkiem miesiąca, ≥ 30 notowań) — bez zmian względem R1 (nie strojone).
- Koszty (config): taker 0,05 % + poślizg 0,02 % = **0,07 % na jednostkę obrotu** (obie nogi na
  perpetualach — short wymaga perp); funding per symbol: long PŁACI, short OTRZYMUJE stawkę.
- Kod: `backtest/xs_momentum.py` (czyste funkcje, 12 testów, hypothesis) +
  `backtest/run_xs_momentum_x1.py`. **Komendy:** `py -m backtest.run_xs_momentum_x1 --moc 100`
  (rachunek mocy → `moc.txt`, 322 s) i `py -m backtest.run_xs_momentum_x1` (runda →
  `raw_output.txt`, 5,5 s); Windows: `PYTHONUTF8=1`; skrypt na `runs/ZAMROZONE.txt`.
  Przyrząd: `carry_hedged.summarize_pnl` (`periods_per_year = 365`, `capital_per_notional = 1`).
  Walidacja drugą drogą: `walidacja.py` → `walidacja.txt`.

## Poprzedzające wyniki

- **R1** (`runs/2026-09-23_r1-premia-rebalansowa/`, wniosek 57): rebalans dzienny do równych wag
  traci −3,55 %/rok [−9,50; +2,40] wobec trzymania w miesiącu; scenariusz „ruchy względne
  niezależne" wykluczony → ruchy względne wewnątrz miesiąca TRWAJĄ. X1 to hipoteza odwrotna,
  zgłoszona tam jako nowa (nie wariant), z własnym licznikiem.
- **M1** (momentum CZASOWE BTC 4h: 49,74 %) — inna formuła (jednoaktywowa) i inny target
  (kierunek absolutny); X1 nie jest jej powtórką (pięć pól różne w dwóch).
- **P2 / wniosek 40**: przekrój nie mnoży próby — 20 monet ≈ 2 niezależne (korelacja 0,47);
  dlatego jednostką próby są DNI szeregu portfela (n ≈ 1 950), a szum liczy się z symulacji.
- **Wniosek 58** (R1): proxy analityczne szumu różnicy strategii zaniżyło go 3× → tu szum
  z 100 losowych rankingów; **wniosek 63** (D1): N_eff tylko kanoniczny.
- **families.md B1**: pułapki — koszt shorta = funding netto; obrót tygodniowy do 2,0 kapitału;
  wolumen wycofanych bywa fikcyjny (uniwersum po obrocie, wycofane = gotówka).

## Pre-rejestracja

### Hipoteza i mechanizm

W koszyku top-20 po obrocie względny zwrot z ostatnich 28 dni przewiduje względny zwrot
kolejnych 7 dni (momentum przekrojowe). Mechanizm: opóźniona reakcja i kaskady uwagi
w altcoinach (kapitał detaliczny płynie do „gorących" monet z opóźnieniem); po drugiej stronie
tracą ci, którzy sprzedają zwycięzców za wcześnie (R1: rebalans do równych wag). Kontrargument
zapisany z góry: zwycięzcy płacą wysoki funding (long kosztuje), a tygodniowa wymiana składu
kosztuje do 0,14 % kapitału tygodniowo — hipoteza może być prawdziwa brutto i fałszywa netto.

### DOKŁADNIE JEDNA zmienna

Ranking po zwrocie 28 dni (vs brak rankingu). Wszystko inne zamrożone: uniwersum jak R1,
trzymanie 7 dni, nogi po 5 (kwartyle z 20), równe wagi na formowaniu, dryf w oknie, koszty
z config, funding z cache.

### Przyrząd

Dzienny szereg zwrotu netto portfela long-short (kapitał 1 = 0,5 long + 0,5 short):
`r_net = 0,5·(r_long − r_short) + funding_net − koszt`. Średnia z CI 95 % z N_eff ≤ n
(`effective_sample_size`, pełna funkcja autokorelacji), `t_neff`, annualizacja ×365.
Wtórnie (opisowo, NIE do werdyktu): rank IC tygodniowe (Spearman sygnał ↔ zwrot 7 dni wśród
członków; n ≈ 280) z CI; korelacja dziennego zwrotu netto z BTC (neutralność); rozbicie
brutto / funding / koszty; per rok.

### Kryterium (zapisane przed wynikiem; jedno ramię, m = 1)

- **POZYTYWNY:** `t_neff > 1,96` średniego dziennego zwrotu netto.
- **NEGATYWNY:** górny kraniec CI 95 % zwrotu netto < 0.
- **NIEROZSTRZYGNIĘTY:** CI obejmuje zero. Wtedy dodatkowo: czy CI **brutto** wyklucza
  obietnicę literatury (52 %/rok) i ostrożną połowę (26 %/rok) — odczyt informacyjny, jak w R1.
- Test w granicy dużego n: kryterium zależy tylko od średniej i N_eff — im większe n, tym
  łatwiej o POZYTYWNY przy prawdziwym efekcie i o NEGATYWNY przy ujemnym; nie karze celu rundy.

### Rachunek mocy (zasada 18) — z symulacji, przed wynikiem (`moc.txt`)

`py -m backtest.run_xs_momentum_x1 --moc 100` (322 s): 100 losowych, rozłącznych par nóg
(5 + 5) spośród członków z sygnałem, ta sama maszyneria (dryf wag, obrót, funding, koszty),
seed 0 — **bez patrzenia na prawdziwy sygnał.**

| wielkość | wartość |
|---|---|
| dni w szeregu / formowań | **1 975** / 283 (2021-02-01 → 2026-06-29), 65 koszyków, 119 symboli |
| pod H0: średnia dzienna netto | −0,0142 % (brutto +0,0010 %, funding +0,0002 %, **koszt 0,0154 %/dzień = 5,62 %/rok** przy pełnej wymianie składu co tydzień) |
| sd dzienna netto (typowa) | 1,30 % ; acf1 −0,02 → N_eff ≈ n |
| **empiryczne se średniej pod H0** (sd średnich między symulacjami) | **0,0296 %/dzień** (analitycznie sd/√n: 0,0293 % — zgodne, bo acf1 ≈ 0) |
| **half-width 95 %** | **0,058 %/dzień = 21,2 %/rok** |

**Werdykt mierzalności:** obietnica literatury (52 %/rok) = **2,5×** half-width → **MIERZALNA**;
ostrożna połowa (26 %/rok) = 1,2× → na granicy (wynik takiej wielkości dałby t ≈ 2,4). Efekty
poniżej ~20 %/rok netto są NIEWIDZIALNE dla tego przyrządu i tak zostanie zapisane, jeśli
CI obejmie zero. Próg kosztowy z góry: strategia musi zarobić brutto > 5,6 %/rok (obrót
losowy; przy trwałym rankingu obrót mniejszy, więc koszt niższy — sam obrót jest wynikiem
opisowym) plus funding netto o nieznanym znaku (pod H0 ≈ 0).

### Czego runda NIE robi

Nie stroi okna ani kwantyli; nie odwraca znaku po wyniku (wniosek 49); nie wybiera podokresów;
nie liczy wersji long-only ani kapitalizacyjnej; nie testuje innych uniwersów. Wynik ujemny
netto przy dodatnim brutto NIE jest podstawą do „zmniejszmy koszty" — koszty są z config.

---

## Wynik

Dane: 281 symboli, 65 koszyków (119 różnych symboli), 283 formowań 2021-02-01 → 2026-06-29,
1 975 dni szeregu.

### 1. Kryterium (jedno ramię, próg 0)

| | n | średnia / dzień | CI 95 % (N_eff) | mediana | t_neff | N_eff | **rocznie ×365** |
|---|---|---|---|---|---|---|---|
| **netto** | 1 975 | **+0,0602 %** | [−0,0146; +0,1351] | +0,0638 % | **+1,58** | 1 975 | **+22,0 % [−5,3; +49,3]** |
| brutto | 1 975 | +0,0664 % | [−0,0083; +0,1411] | +0,0756 % | +1,74 | 1 975 | +24,2 % [−3,0; +51,5] |

**Odczyt kryterium: NIEROZSTRZYGNIĘTY** (CI netto obejmuje zero; t_neff 1,58 < 1,96).
Obietnica literatury 52 %/rok: górny kraniec CI brutto 51,5 % — **na granicy wykluczenia**;
ostrożna połowa (26 %/rok) — wewnątrz CI. Rozdzielczość ex post: half-width 0,0748 %/dzień =
**27,3 %/rok** (ex ante z symulacji 21,2 % — sd dzienna 1,68 % wobec 1,30 % pod losowym
rankingiem: nogi momentum skupiają monety bardziej zmienne niż losowe).

### 2. Dekompozycja (sumy za 5,4 roku, % kapitału)

Σ brutto **+131,1 %**, Σ funding netto **+5,1 %** (short otrzymuje więcej, niż long płaci),
Σ koszty **17,2 %** (obrót 246 kapitału = **0,87 na formowanie**, nie 2,0 — rankingi są trwałe
z tygodnia na tydzień), **Σ netto +119,0 %.** Noga long: +0,0797 %/dzień; noga short:
−0,0531 %/dzień (short zarabia, gdy przegrani dalej spadają). Dni z zwrotem netto > 0: 52,1 %.

| rok | dni | Σ netto | Σ brutto | Σ funding | Σ koszt | sd / dzień | noga long Σ | noga short Σ |
|---|---|---|---|---|---|---|---|---|
| 2021 (od lutego) | 333 | +8,0 % | +8,6 % | +2,5 % | 3,2 % | 2,18 % | +182 % | +165 % |
| 2022 | 365 | +15,1 % | +22,4 % | −4,3 % | 3,0 % | 1,51 % | −124 % | −169 % |
| 2023 | 365 | +12,0 % | +9,7 % | +5,3 % | 3,0 % | 1,33 % | +91 % | +72 % |
| 2024 | 366 | +13,8 % | +16,9 % | +0,3 % | 3,4 % | 1,42 % | +47 % | +13 % |
| **2025** | 365 | **+61,7 %** | +67,5 % | −2,8 % | 3,0 % | 1,79 % | +26 % | **−109 %** |
| 2026 H1 | 181 | +8,5 % | +6,0 % | +4,1 % | 1,7 % | 2,00 % | −65 % | −77 % |

Dodatni w każdym roku (opisowo, bez werdyktów per rok); **2025 = 52 % sumy** — bez 2025:
+57 % w 4,4 roku ≈ 13 %/rok. Efekt pochodzi głównie z nogi short w latach spadków altów
(2022, 2025): przegrani tracą dalej.

### 3. Wtórnie — IC, neutralność, ogony

- **Rank IC tygodniowe:** n = 282, średnia **+0,028 [−0,007; +0,064]**, sd 0,30, ICIR +0,09,
  IC > 0 w 55,3 % tygodni, 20 par na tydzień. Ten sam odczyt co kryterium: dodatni, nie
  odróżnialny od zera.
- **Neutralność do BTC:** korelacja dziennego zwrotu netto z BTC **−0,13** — portfel nie jest
  ukrytym zakładem o rynek.
- **Ogony:** p05 −2,6 %, p50 +0,06 %, p95 +2,7 %, min −11,4 %, max +9,3 %; 34 dni z |r| > 5 %
  sumują się do +7,0 % z +119 % (6 %); **bez 20 najbardziej skrajnych dni średnia +0,0636 %
  vs +0,0602 %** — wynik nie mieszka w ogonach.

## Co na plus (+)

- **Pierwszy zakład o kierunek (relatywny) w projekcie z dodatnim punktowo odczytem**, na
  uniwersum bez błędu przeżywalności, z kosztami i fundingiem, jedną zmienną i bez wyboru po
  wyniku; dodatni w 6 z 6 lat, neutralny do BTC, odporny na ogony.
- **Rachunek mocy z symulacji trafił w rząd wielkości** (21 → 27 %/rok, 1,3×; w R1 proxy
  analityczne pomyliło się 3×) — wniosek 58 działa.
- **Mechanizm spójny z R1** (wniosek 57): ruchy względne trwają, i to głównie po stronie
  przegranych (wycofania, spirale memecoinów) — spójne z tym, że rebalans do równych wag
  w R1 tracił, dokupując spadające.
- **Obrót 0,87/formowanie zamiast 2,0** — rankingi są trwałe, więc koszty (3 %/rok) nie zjadają
  efektu; funding netto dodatni (+1 %/rok): shorty przegranych otrzymują więcej, niż longi
  zwycięzców płacą.

## Co na minus (−)

- **Nierozstrzygnięty:** t 1,58; żeby +22 %/rok odróżnić od zera przy tej zmienności, trzeba
  ~4× próby (n ≈ 7 900 dni ≈ 22 lata) — tej próby nie ma i nie będzie.
- **Połowa wyniku z jednego roku (2025)**; z 6 obserwacji rocznych nie da się orzec
  stabilności. Skośność „jeden wielki rok" to typowy kształt fałszywego pozytywu.
- **Short na przegranych w praktyce:** dostępność shorta na wycofywanych monetach, ADL,
  wysoki funding w spiralach — model przyjmuje, że short zawsze da się utrzymać (wycofanie =
  gotówka po ostatniej cenie, czyli **korzystnie** dla shorta, który realnie musiałby zamknąć
  pozycję przed delistingiem po gorszej cenie); poślizg 0,02 % dla memecoinów optymistyczny.
- **Ceny perp jako spot (uniwersum P2)** — tu właściwe, bo obie nogi na perpach; ale funding
  w dniu wejścia liczony od t+1 (3 rozliczenia/dzień sumowane) — przybliżenie.
- **Kontekst multiple testing:** 1/1 w serii X, ale tego dnia zamknięto serie A (7), C (2),
  R (1), N (1), W (3) i analizy D1/P3 — czytelnik powinien pamiętać, że dodatni punkt jest
  jednym z ~15 odczytów dnia (wszystkie pre-rejestrowane, ale licznik globalny rośnie).

## Walidacja (zasada 16a) — werdykt: **READY** (`walidacja.txt`)

- **Tożsamość sum:** +131,112 + 5,094 − 17,221 = **+118,985** = Σ netto ✔; dni 1 975 = dni bazy
  od pierwszego formowania + 1 ✔; formowań 283, wszystkie z obrotem ✔.
- **Drugą drogą, bez maszynerii dryfu wag:** średni 7-dniowy zwrot top-5 minus bottom-5 na
  datach formowania = **+0,464 %/tydzień** (se 0,254 %) → ×52 = +24,1 %/rok; z szeregu
  dziennego Σ brutto / 283 tygodnie = +0,463 %/tydzień ✔ (zgodność do 0,001 pp).
- **Kogo NIE ma:** symbole spoza top-20 po obrocie (162 z 281); pierwsze 28 dni każdego
  notowania (brak sygnału; członków z sygnałem: min 19, mediana 20, tygodni z < 10: 0);
  106 dni (5,4 %) z nogą < 5 aktywnych (wycofanie → gotówka); rynki spot (wszystko perp);
  Bybit/OKX; koszt maker; ADL.
- **Red flag „idealnie potwierdza":** nie — kryterium NIEROZSTRZYGNIĘTE, IC nie odróżnialne od
  zera; dodatni w każdym roku, ale z 6 lat.
- **Red flag „ujemne netto przy dodatnim brutto":** nie występuje (koszty 13 % brutto).
- **Red flag „jeden rok robi wynik":** TAK — 2025 = 52 % sumy; zapisane w minusach.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `backtest/xs_momentum.py` (nowy), `backtest/run_xs_momentum_x1.py` (nowy),
`tests/test_xs_momentum.py` (12), README rundy. Bez zmian w kodzie produkcyjnym;
`rebalance_premium.monthly_members`/`load_universe` użyte bez modyfikacji.

**Korektność:** (1) brak lookaheadu — `signal.loc[t]` z `close/close.shift(28)` (tylko ≤ t),
zwroty z `returns.index > t` (test: pierwszy zwrot w t+1); (2) `_month_of` — ostatni miesiąc
≤ t; daty formowania zaczynają się od 2021-02-01 = pierwszy koszyk, więc zawsze istnieje;
(3) `legs is None` → pozycja pusta, obrót = zamknięcie starej (liczony przy tym formowaniu),
dni bez pozycji zapisane z zerami (w danych: 0 takich dni); (4) dryf wag: `w ← w(1+r)`,
znormalizowany do stałej wartości nogi 0,5 — zachowuje PROPORCJE dryfu (buy-and-hold między
członkami nogi), a stała wartość nogi to konwencja „kapitał 1 przez cały tydzień" (leg P&L
liczone jako zwrot nogi, nie jako zmiana wartości kapitału) — zamierzone, opisane; (5) koszt
tylko w pierwszym dniu po formowaniu (test); (6) funding: `Σ w_S f − Σ w_L f` (test znaku);
(7) wycofani: `fillna(0)` = gotówka (test); (8) `random_legs` losuje z tej samej populacji
(członkowie z sygnałem) co `rank_legs` — właściwe H0.
**Edge-case'y:** < 2·leg z sygnałem → tydzień bez pozycji; pusty katalog → `ValueError`;
remisy → nazwa (test). **Usterka w teście** (nie w kodzie): oczekiwany obrót 2,0 przy
pierwszym wejściu z gotówki — poprawnie 1,0 (2,0 = pełna wymiana istniejącego portfela);
poprawione przed przebiegiem. **Czytelność:** stałe i konwencje w docstringu modułu.
**Uwagi (bez blokady):** pętla dzienna w Pythonie — 5,5 s runda, 322 s symulacja mocy; OK.
**Werdykt jednym zdaniem:** kod poprawny, bez lookaheadu, przetestowany na tożsamościach
i drugą drogą — **Approve**.

## Wniosek

**Momentum przekrojowe na 20 największych monetach dało +22 %/rok netto [−5; +49] przez 5,4
roku, dodatnio w każdym roku, neutralnie do bitcoina — ale nie odróżnialnie od zera** (t 1,58),
bo rozdzielczość przyrządu to 27 %/rok, a połowa wyniku pochodzi z 2025. Obietnica literatury
(52 %/rok) leży na granicy wykluczenia. Mechanizm: przegrani tracą dalej (noga short robi
wynik w latach spadków altów) — spójne z R1. To pierwszy wynik kierunkowy (relatywny)
w projekcie z dodatnim punktowo odczytem, ale przy tej próbie **jest to hipoteza z poparciem,
nie dowód**. Seria X zamknięta 1/1 (STOP).

## Rekomendacja

1. **Nie uruchamiać wariantów** (inne okna, kwantyle, trzymanie, long-only) — reguła STOP;
   każdy z nich na tych samych danych to szukanie potwierdzenia w szumie.
2. **Jedyna droga do rozstrzygnięcia to WIĘKSZA PRÓBA, nie lepszy wariant.** Dwie opcje, obie
   = nowa pre-rejestracja z decyzją użytkownika (wniosek 49): (a) **szerokość** — uniwersum
   top-50 z nogami po 10 (szum nogi maleje ~√2, ale monety 21–50 mają gorszą płynność i
   dostępność shorta — koszt realny wyższy); (b) **czas** — pomiar na żywo (paper) od dziś:
   przy +22 %/rok i sd 1,7 %/dzień każdy rok dodaje t ≈ 0,7; po 3 latach t ≈ 2,7, jeśli
   efekt się utrzyma. Opcja (b) nie zużywa licznika i nie ma post hoc — to prospektywny test.
3. **Jeśli użytkownik chciałby zaryzykować kapitał na tym wyniku** (decyzja bramkowa):
   prawdopodobieństwo, że prawdziwy efekt jest ≤ 0, wynosi ok. 6 % (t 1,58, jednostronnie),
   a realne koszty shorta na przegranych (delisting, ADL, funding w spiralach) są wyższe niż
   w modelu — liczby do decyzji, nie rekomendacja.
4. **Metodologicznie (wniosek 65):** rachunek mocy z symulacji losowych rankingów trafia
   w rząd wielkości, ale zaniża szum o ~30 %, bo nogi wybrane sygnałem są bardziej zmienne
   niż losowe; w kolejnych rundach przekrojowych symulować H0 z dopasowaniem zmienności
   (losowanie wśród monet o podobnej sd) albo mnożyć half-width przez 1,3.

## Użyte skille

Rejestr gałęzi `x1-momentum-przekrojowe` (`py tools/skill_audit.py raport --galaz x1-momentum-przekrojowe`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → pre-rejestracja z mocą z symulacji → commit → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | przyrząd przekrojowy (dzienny szereg LS, N_eff kanoniczny), H0 z symulacji, IC jako miara wtórna, test kryterium w granicy dużego n |
| `anthropic-skills:quant-strategy-catalog` | rodzina B1 (pięć pól), mechanizm i „kto traci", pułapki (koszt shorta, obrót, wycofani), reguła STOP dla wariantów tej samej rodziny |
| `engineering:testing-strategy` | plan testów PRZED kodem: brak lookaheadu, tożsamość 0,5(r_L − r_S) (hypothesis), znak fundingu, obrót, wycofani |
| `data:validate-data` | bramka 16a: tożsamość sum, niezależny rachunek tygodniowy, „kogo nie ma", trzy red flagi |
| `data:statistical-analysis` | bramka 16b: CI z N_eff, mediana i ogony, per rok bez werdyktów, ex ante vs ex post half-width, nazwanie wyniku |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu"; wykrycie błędnego oczekiwania w teście obrotu) |

Z tabeli zasady 19 pominięte: `security-review` (bez kodu sieciowego), `dataviz` (bez wykresów),
`engineering:architecture`, `update-config`, `ta-toolkit`, `lean-research`.
