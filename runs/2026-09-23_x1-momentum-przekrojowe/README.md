# X1 — momentum przekrojowe: czy zwycięzcy ostatnich 4 tygodni wygrywają dalej? (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Hipoteza, jedna zmienna, kryterium, reguła
> STOP i rachunek mocy zapisane PRZED obejrzeniem wyniku. Rachunek mocy liczony z **symulacji
> losowych rankingów na tych samych danych** (wniosek 58 — nie z proxy analitycznego) i z
> kanonicznego N_eff (wniosek 63); `moc.txt` = pełny wydruk. **NOWA SERIA X, licznik od zera.**
> Decyzja użytkownika 2026-09-23: „sprawdź wszystkie warianty" (hipoteza odwrotna do R1,
> zgłoszona w rekomendacji R1 jako wymagająca decyzji — wniosek 49).

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
  `backtest/run_xs_momentum_x1.py` (`--moc` rachunek mocy; bez flagi — runda). Komendy przy
  zamknięciu; skrypt na `runs/ZAMROZONE.txt`. Przyrząd: `carry_hedged.summarize_pnl`
  (`periods_per_year = 365`, `capital_per_notional = 1`).

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

_(sekcje poniżej po przebiegu)_

## Wynik

_(po przebiegu)_

## Co na plus (+) / Co na minus (−)

_(po przebiegu)_

## Walidacja (zasada 16a)

_(po przebiegu)_

## Przegląd diffu (zasada 16c)

_(po przebiegu)_

## Wniosek

_(po przebiegu)_

## Rekomendacja

_(po przebiegu)_

## Użyte skille

_(po przebiegu — z `py tools/skill_audit.py raport --galaz x1-momentum-przekrojowe`)_
