# TX1 — trend tygodniowy (reguła TS1) na 19 rynkach spoza krypto (2026-09-24)

> **STATUS: ZAMKNIĘTA — kryterium główne POZYTYWNE, szczebel 1(b) ADR-09 NIEROZSTRZYGNIĘTY.**
> 1990–2026: **+5,1 %/rok [+1,4; +8,7], t_neff 2,73**, ponad 100 % portfeli H0. Ale **po publikacji
> (2013–2026): −0,2 %/rok [−6,0; +5,6]**, 4/14 lat dodatnich — cały wynik to lata 1990–2012 (próba
> literatury). Po 2013 trend trzyma się na ropie (+22,9 %) i akcjach (+7,6 %), znika na walutach
> (−3,4 %), które stanowią 13 z 19 rynków. Pre-rejestracja `6532994`. Walidacja: **READY (Caveats)**;
> przegląd: **Approve**. Seria TX 1/1, STOP.
> Poprzednio: **PRE-REJESTRACJA (przed wynikiem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Według nowego kryterium (ADR-09) trend musi mieć oparcie **poza naszymi danymi krypto**. Sprawdzamy
więc naszą regułę trendu, bez żadnej zmiany, na walutach, ropie, indeksach giełdowych i obligacjach
od 1990 roku. Jeśli trend to prawdziwe zjawisko rynkowe, a nie przypadek na 5 latach krypto,
powinien być widoczny także tam.

## ID testu

TX1 — szczebel 1(b) drabiny dowodów (ADR-09, `docs/rag/09_drabina_dowodow.md`).

## Metadane

- Branch `tx1-trend-inne-rynki`. Dane: FRED (bez klucza) → `data/raw/tradfi/` (`py -m data.tradfi_panel`);
  panel `data/tradfi_panel.py` + testy `tests/test_tradfi_panel.py`. Skrypt `backtest/run_trend_tradfi_tx1.py`.
- **Wyjątek od zasady 20** (dane od 2021) — zatwierdzony wyborem użytkownika 2026-09-24 (droga C:
  „trend na surowcach, walutach, indeksach, dziesiątki lat”); zasada 20 dotyczy świec krypto.

## Poprzedzające wyniki

- TS1/TR1 po RU1/RU2 (wnioski 70, 74, 82, 83): trend na krypto +11–13 %/rok, nieistotny, dodatni w każdym
  roku; ADR-09 szczebel 2 spełniony (post hoc).
- Literatura: Moskowitz–Ooi–Pedersen (2012), 58 kontraktów 1985–2009, Sharpe ~1; Hurst–Ooi–Pedersen
  (2017), 100 lat. Po publikacji słabiej (Sharpe ~0,3–0,5, „susza trendu” 2012–2019).

## Pre-rejestracja (przed wynikiem)

- **Hipoteza:** reguła TS1 daje dodatni zwrot na rynkach spoza krypto.
- **JEDNA zmienna:** rynki (krypto → 19 rynków FRED). Reguła co do bajtu: znak zwrotu 28 dni,
  σ̂ EWMA (com 60) · √365, w = s·min(3; 0,40/σ̂)/N, formowanie co 7 dni, 7 faz.
- **Dane (ustalone przed wynikiem):** 13 walut względem USD (odwrócone do „USD za jednostkę”), ropa
  Brent, Nasdaq Composite, Nikkei 225, obligacje USA 2/10/30 lat (zwrot z rentowności: −D·Δy + y/365,
  D = 1,9 / 8,5 / 18). **Wykluczone przed wynikiem:** WTI (cena ujemna 2020-04-20), gaz Henry Hub
  (dzienny spot fizyczny, skoki do +319 %/dzień, 90 dni > 20 %). Dni kalendarzowe z przeniesieniem
  ceny (zwrot 0 w dni wolne) — silnik bez zmian parametrów.
- **Koszt:** 0,02 % × obrót; bez carry walut, rolowania ropy i dywidend — dowód mechanizmu, nie wynik do handlu.
- **Kryterium główne (1990-01 → 2026-08):** POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0
  (100 portfeli ze znakami przesuniętymi w czasie); NEGATYWNY, gdy górny kraniec CI 95 % < 0.
- **Mapowanie na ADR-09 szczebel 1(b):** SPEŁNIONY, gdy kryterium główne POZYTYWNE i średnia po 2013
  > 0; OBALONY, gdy kryterium główne NEGATYWNE albo górny kraniec CI po 2013 < 0; inaczej
  NIEROZSTRZYGNIĘTY.
- **Mierzalność (`moc.txt`):** całość: zmienność H0 9,4 %/rok, half-width **±3,1 %/rok = 0,33 SR**,
  q97,5 +2,9 %; założony efekt (koszyk 19 rynków, głównie waluty) SR 0,5–0,8 → **MIERZALNA**.
  Po 2013: half-width ±5,1 %/rok = 0,53 SR wobec efektu SR 0,3–0,5 → **tylko opisowo**.
- **Opisowo:** dekady, lata dodatnie, 7 faz, klasy aktywów osobno, nominał i obrót.
- **Licznik:** nowa seria TX (1/1, STOP); w projekcie ~34. odczyt.

## Wynik

`raw_output.txt` (6,5 min).

| okres / wycinek | zwrot netto %/rok [CI 95 %] | t_neff |
|---|---|---|
| **całość 1990–2026** (kryterium) | **+5,08 [+1,43; +8,72]**; H0 q97,5 +2,87 → **POZYTYWNY** | 2,73 |
| **po publikacji 2013–2026** | **−0,20 [−5,97; +5,57]**; ponad 51 % H0 | −0,07 |
| lata 90. | +10,50 [+4,65; +16,35] | 3,52 |
| lata 2000. | +8,62 [−0,83; +18,07] | 1,79 |
| lata 2010. | −1,37 [−8,43; +5,70] | −0,38 |
| lata 2020. | +1,31 [−7,86; +10,48] | 0,28 |

Lata dodatnie 21/37, po 2013 tylko 4/14. 7 faz: +4,3 … +6,3 %/rok (wszystkie dodatnie). Brutto +6,4 %/rok,
koszt ~1,3 %/rok (obrót 65 kapitału/rok — duże pozycje na spokojnych walutach, nominał mediana 2,8×).

| klasa aktywów (osobny koszyk) | 1990–2026 | po 2013 |
|---|---|---|
| waluty (13) | +2,2 %/rok, t 1,00 | **−3,4 %** |
| energia: Brent (1) | +17,1 %, t 2,48 | **+22,9 %** |
| akcje: Nasdaq, Nikkei (2) | +12,7 %, t 2,88 | **+7,6 %** |
| obligacje USA (3) | +7,1 %, t 2,31 | +0,2 % |

**Odczyt ADR-09, szczebel 1(b) (reguła z góry):** kryterium główne POZYTYWNE, ale średnia po 2013 < 0 →
nie SPEŁNIONY; górny kraniec CI po 2013 (+5,6 %) > 0 → nie OBALONY → **NIEROZSTRZYGNIĘTY**.

## Co na plus (+) / Co na minus (−)

**(+)** Ta sama reguła, bez żadnego strojenia, działa na 19 rynkach spoza krypto przez 37 lat — istotnie
(t 2,73) i lepiej niż każdy z 100 portfeli losowych. Każda z 7 faz dodatnia. Mechanizm trendu istnieje.
**(−)** Prawie cały wynik pochodzi z lat 1990–2012, czyli z okresu, na którym trend został opisany
w badaniach. Po publikacji znika na koszyku zdominowanym przez waluty. To klasyczny wzór „efekt słabnie po
publikacji”. Ceny spot: brak carry walut, kosztu rolowania ropy i dywidend. Wynik ropy po 2013 to jedna
seria spot, więc nie da się nim handlować 1:1.

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY (Caveats)**: faza 0 silnika przeliczona NIEZALEŻNIE prostą pętlą numpy
(formowanie co 7 dni, wagi stałe, bez funkcji silnika): **korelacja 0,9996**, +4,29 vs +4,36 %/rok;
średnia 7 faz +5,09 = wynik główny +5,08. Kogo nie ma: WTI i gaz HH (wykluczone przed wynikiem), carry,
rolowanie, dywidendy, rynki spoza FRED (metale, zboża, Europa). Caveat: przewaga walut (13/19) steruje
wynikiem po 2013. `data:statistical-analysis`: przedziały 95 % dla każdego wycinka; skośność wyniku w
czasie (dekady) raportowana wprost; ~34 odczyty w projekcie — kryterium główne t 2,73 powyżej 2,24
(Bonferroni m = 2), poniżej progu rodzinnego ~2,9. `engineering:code-review` — **Approve**: przeniesienie
ceny tylko wstecz (test), odwrócenie walut i indeks obligacji z testami, silnik TS1 bez zmian.

## Wniosek

**Prostym językiem:** nasza reguła trendu działa na zwykłych rynkach — przez 37 lat dawała ok. 5 % rocznie,
i to na pewno nie przypadek. Ale po 2013 roku, gdy ta strategia stała się powszechnie znana, na tym koszyku
(głównie waluty) przestała zarabiać; trzymała się jeszcze na ropie i akcjach. To znaczy: mechanizm jest
prawdziwy, ale bywa „wyjadany”, kiedy dużo pieniędzy go gra. Dla krypto to ostrzeżenie, nie wyrok — rynek
krypto jest młodszy i mniej zatłoczony, ale nie wiemy, jak długo tak zostanie.

## Rekomendacja

1. ADR-09: trend — szczebel 1(a) spełniony, 1(b) **nierozstrzygnięty**. Dziennik papierowy trwa bez zmian;
   decyzja o realnej kwocie (szczebel 4) po odczycie ~2026-12-25 należy do użytkownika i musi uwzględnić
   ten wynik (trend zanika na dojrzałych rynkach).
2. Nie dobierać teraz rynków „które działają po 2013” (ropa, akcje) — to wybór po obejrzeniu wyniku.
3. Seria TX: 1/1, STOP.

## Użyte skille

Rejestr `runs/skille/tx1-trend-inne-rynki.jsonl`: `clas5-runda` (pre-rejestracja z mapowaniem na ADR),
`clas5-quant` (mierzalność z H0 przed wynikiem, przeniesienie ceny), `quant-strategy-catalog` (rodzina A1,
okres po publikacji jako czysty), `data:explore-data` (profil 20 serii → wykluczenie gazu HH przed wynikiem),
`data:validate-data` (numpy 0,9996), `data:statistical-analysis` (wycinki z CI), `engineering:code-review`
(Approve). Pominięte: `dataviz` (tabele).
