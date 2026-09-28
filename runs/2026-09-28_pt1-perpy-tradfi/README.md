# PT1 — perpetuale TradFi na Bybit i Binance: spis, funding, koszty, weekend, zgodność z rynkiem bazowym (2026-09-28)

> **STATUS: ZAMKNIĘTA (opisowo, 0 wariantów — POZA licznikami).** Perpetuale TradFi na obu giełdach mają w fundingu
> **stopę procentową 0** (Binance publikuje `interestRate` = 0 dla 202 z 206; Bybit — wzór z I = 0 odtwarza 100 % odczytów).
> Funding jest więc zerem, dopóki premia nie wyjdzie poza ±0,05 %/8 h: **różnica stóp procentowych (carry) nie jest
> przenoszona** — hipoteza „carry na kilku klasach” jest na tych kontraktach niewykonalna. Za to trzymanie pozycji kosztuje
> zwykle ~0, koszty wejścia są niższe niż model KO1, a cena w weekend dobrze zapowiada poniedziałkowe otwarcie.
> Pre-rejestracja: commit `85365a0` (przed danymi).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Użytkownik chce rozszerzyć strategie na waluty, akcje, obligacje i surowce. Bybit i Binance mają od kilku miesięcy
**perpetuale TradFi** (kontrakty bez terminu wygaśnięcia na aktywa spoza krypto: akcje, ETF-y, złoto, ropę, waluty),
rozliczane w USDT, na tym samym koncie co dziennik. Zanim zbudujemy na nich jakąkolwiek hipotezę, trzeba wiedzieć,
**czym te kontrakty naprawdę są**:

1. co jest dostępne i od kiedy (ile historii);
2. czy funding (okresowa opłata między długimi i krótkimi) przenosi „carry” rynku bazowego — np. różnicę stóp
   procentowych dwóch walut — czy jest kopią fundingu krypto (stała stopa + premia);
3. ile kosztuje wejście i wyjście (spread + opłata);
4. co robi cena, gdy rynek bazowy jest zamknięty (noc, weekend) i czy w poniedziałek robi się luka;
5. czy cena indeksu giełdy zgadza się z niezależnym źródłem (FRED).

To pomiar przyrządu, nie strategii — jak KO1 dla kosztów. Wynik ustala, jakie hipotezy w ogóle da się na tych
kontraktach wykonać (krok 2 planu z rozmowy 2026-09-28).

## Metadane

- **ID:** PT1. Branch `pt1-perpy-tradfi` (z `master` `4bf7827`). Decyzja: rozmowa 2026-09-28 — plan „(1) sprawdzenie
  perpów TradFi bez testowania strategii, (2) jedna pre-rejestrowana hipoteza z mechanizmem, którego krypto nie ma”;
  użytkownik przekazał plan sesji na serwerze.
- **Kod:** `data/fetch_tradfi_perps.py` (pobieranie: spis, funding, świece 1h ceny / indeksu / mark, migawki tickerów),
  `backtest/run_pt1_tradfi.py` (neutralny reporter). Testy: `tests/test_fetch_tradfi_perps.py`, `tests/test_pt1_tradfi.py`.
- **Źródła:** publiczne REST bez klucza — Bybit `https://api.bybit.com/v5/market/*` (category=linear,
  `symbolType ∈ {stock, ETF, commodity, forex}`), Binance `https://fapi.binance.com/fapi/v1/*`
  (`contractType = TRADIFI_PERPETUAL`); FRED (`data.fetch_external.fetch_fred`, bez klucza) do drugiej drogi i stóp.
- **Dane POZA repo:** `data/raw/tradfi_perps/` (migawki `migawki/*.json.gz`, funding, świece). Artefakty rundy (CSV) w tym katalogu.
- **Spis w chwili pre-rejestracji (tylko lista instrumentów, bez cen):** Bybit 257 (196 akcji, 54 ETF, 4 surowce: XAU, XAG od
  2026-03-09, CL od 03-24, BZ od 05-13; 3 waluty: EURUSD, GBPUSD, USDJPY od 2026-09-08); Binance 206 (168 akcji USA,
  15 HK, 8 KR, 2 CN, 8 surowców — złoto od 2025-12-11, 4 „przed IPO”, 1 waluta: USDBRL od 2026-09-21). Obligacje tylko jako
  ETF-y na Bybit (TLT, TBT, TMF).

## Poprzedzające wyniki

- **TX1 (wniosek 84):** trend TS1 na 19 rynkach FRED działa 1990–2012, zanika po 2013 (waluty −3,4 %/rok) — noga TradFi
  potrzebowałaby innego mechanizmu niż sam trend; stąd pytanie, czy perpy w ogóle przenoszą carry.
- **KR2 (wniosek 100):** nogi dziennika prawie nieskorelowane z rynkami tradycyjnymi (|ρ| ≤ 0,15) — to jest powód, dla
  którego noga TradFi byłaby cenna (niezależność).
- **P2 / F1 / carry COIN-M (wnioski 40, 61):** funding perpów krypto = premia + stała stopa 0,01 %/8 h, z masą punktową
  (F1: 35,85 % odczytów na jednej wartości). Jeśli TradFi dziedziczy ten wzór, różnice stóp rzędu kilku %/rok giną
  w „zacisku” wzoru (±0,05 %/8 h wokół stałej stopy).
- **KO1:** model kosztu projektu = 0,07 % za stronę (taker) — punkt odniesienia dla kosztów TradFi.
- **LB0:** wzorzec kodu Bybit (spis z kursorem stron, tylko https, stałe adresy).
- **Wnioski dotyczące rundy jednym zdaniem:** 84 i 100 mówią, po co noga TradFi (niezależność) i czego nie powtarzać
  (trend po 2013), a 40/61 każą sprawdzić mechanizm fundingu, zanim ktokolwiek policzy carry — runda niczego nie
  powtarza, bo żaden wynik strategii nie jest odczytywany.

## Pre-rejestracja (zapisana przed danymi)

**Zbiór:** wszystkie perpetuale TradFi obu giełd w stanie z 2026-09-28 + BTCUSDT na obu giełdach jako **kontrola** (znany
funding krypto: przyrząd musi odczytać jego masę punktową i stałą stopę). **Rdzeń** (świece 1 h i analiza weekendu),
reguła bez patrzenia na wyniki: wszystkie waluty i surowce + ETF-y z listy {SPY, QQQ, IWM, EWJ, EWZ, EWY, TLT, TBT, TMF,
XLE, GDX} obecne na giełdzie + 5 akcji USA o największym obrocie 24 h w pierwszej migawce + BTCUSDT.

**P1 — spis:** liczba instrumentów per klasa i giełda, data startu, dni historii, interwał i limity fundingu, maks. dźwignia.

**P2 — funding (główne pytanie):** per instrument: liczba odczytów, średnia roczna płacona przez długą pozycję
(średnia × odczyty/rok) z 95 % CI (N_eff z autokorelacji, N_eff ≤ n), mediana, **wartość modalna i jej udział (masa
punktowa)**; per klasa: mediana po instrumentach. Dowód mechanizmu ma pierwszeństwo przed statystyką: stopa procentowa
publikowana przez giełdę (Binance `interestRate` w `premiumIndex`; Bybit — dokumentacja wzoru fundingu) i odtworzenie
fundingu ze wzoru. **Waluty — trzy modele rocznego fundingu płaconego przez długą pozycję:**
- **A „kopia krypto”:** f = stała stopa (modalna wartość BTCUSDT, oczekiwane 0,01 %/8 h = 10,95 %/rok) — niezależnie od pary;
- **B „carry przenoszone”:** f = r(waluty kwotowanej) − r(waluty bazowej): EURUSD r_USD − r_EUR, GBPUSD r_USD − r_GBP,
  USDJPY r_JPY − r_USD, USDBRL r_BRL − r_USD;
- **C „zero”:** f = 0 (sama premia, bez stopy).
Stopy: FRED `DFF` (USD), `ECBDFR` (EUR), `IUDSOIA` (GBP), `IRSTCI01JPM156N` (JPY), `IRSTCI01BRM156N` (BRL), średnia z okna
fundingu danej pary; seria nieaktualna > 3 mies. → zamiennik `IR3TIB01{EZ,GB,JP,BR}M156N`. **Reguła:** model wybrany, gdy
95 % CI średniej zawiera tylko jego wartość; CI zawiera kilka → „nierozstrzygnięte między …”; żadnej → „żaden”. USDBRL nie
rozróżnia A i B (r_BRL − r_USD ≈ 11 %/rok ≈ stała krypto) — raportowany, nie liczony do decyzji.
**Pozostałe klasy:** średnia roczna fundingu wobec kosztu finansowania długiej pozycji kontraktem terminowym
(≈ r_USD − dochód aktywa; tu r_USD z `DFF`, dochód omówiony opisowo).

**P3 — koszty:** z migawek (co 30 min, 18:17–00:10 UTC; godziny sesji USA i po niej): pełny spread w pb (punkty bazowe,
setne procenta), mediana po migawkach, osobno sesja USA otwarta / zamknięta; obrót 24 h. Koszt jednej strony = połowa
spreadu + opłata taker (standard: Bybit 0,055 %, Binance 0,05 % — do sprawdzenia w oficjalnym cenniku TradFi; inna stawka →
oficjalna). Porównanie z modelem KO1 (0,07 %/stronę).

**P4 — zamknięty rynek bazowy:** kalendarz stały per klasa (akcje/ETF USA: pn–pt 13:30–20:00 UTC w czasie letnim USA,
14:30–21:00 w zimowym, święta NYSE 2025–2026 wyłączone; waluty: zamknięte pt 21:00 → nd 21:00 UTC latem, 22:00 zimą;
surowce CME/ICE: zamknięte pt 21:00 → nd 22:00 UTC + codzienna przerwa 21:00–22:00 latem, +1 h zimą). Miary: (a) udział
godzin z niezmienionym indeksem — otwarty vs zamknięty; (b) |bazis| = |cena ostatnia / indeks − 1|: mediana i p95, otwarty
vs zamknięty; (c) luka po weekendzie: zwrot perpa w czasie zamknięcia R vs luka indeksu przy otwarciu G — nachylenie β
(G na R), R², n weekendów; osobno noce dni roboczych dla akcji; (d) średni funding w odczytach przy zamkniętym vs otwartym rynku.

**P5 — zgodność z niezależnym źródłem (druga droga):** dzienne serie FRED vs indeks giełdy o 16:00 UTC (południe w Nowym
Jorku latem; zimą 17:00): EURUSD↔DEXUSEU, GBPUSD↔DEXUSUK, USDJPY↔DEXJPUS, USDBRL↔DEXBZUS, Brent↔DCOILBRENTEU,
WTI↔DCOILWTICO, SPY↔SP500, QQQ↔NASDAQ100. Miary: korelacja dziennych zwrotów, mediana |poziom / FRED − 1| (waluty, ropa).

**Rachunek rozdzielczości (zasada 18 w wersji dla średniej — runda nie ma reguły z trafnością):** waluty Bybit ≈ 20 dni ×
3 = 60 odczytów. Przy założonej zmienności 0,01 %/8 h na odczyt i N_eff ≥ 15: SE średniej rocznej = 0,0001 × 1095 / √15
≈ 2,8 pkt → połowa CI ≈ 5,5 pkt/rok. Luka A–B (przy stopach rzędu USD 3,6 %, EUR 2,0 %, GBP 3,7 %, JPY 0,8 %) = 9–14
pkt/rok > 5,5 → **A odróżnialne od B i C: MIERZALNE.** Luka B–C = 0–3 pkt/rok < 5,5 → **B od C odróżnialne tylko przy
fundingu przypiętym (mała zmienność); inaczej wynik „B albo C — nierozstrzygnięte” jest z góry dopuszczony.**

**Decyzje (z góry, konsekwencje dla kroku 2):**
- **D1 carry walutowe:** A dla ≥ 2 z 3 par głównych i B dla żadnej → carry NIE przenoszone przez perpy → hipoteza „carry na
  kilku klasach” niewykonalna na tych kontraktach (potrzebny inny instrument — decyzja użytkownika). B dla 3/3 → carry
  przenoszone → krok 2 może użyć perpów. Pozostałe układy → opis + dalsze zbieranie fundingu (bez decyzji).
- **D2 koszt:** mediana kosztu strony w rdzeniu ≤ 0,07 % → model kosztów KO1 obowiązuje także dla TradFi; wyżej → podać
  mnożnik i uwzględnić w kroku 2.
- **D3 zamknięcie rynku:** p95 |bazisu| przy zamkniętym rynku > 3× p95 przy otwartym LUB β < 0,5 → wymóg dla każdej
  strategii: wykonanie tylko w godzinach otwarcia rynku bazowego; inaczej perp handlowalny 24/7 bez dodatkowego błędu.
- **D4 historia:** żaden instrument nie ma > 10 miesięcy historii → strategii NIE da się zmierzyć na samych perpach (przy
  SR 0,5 i 0,8 roku t ≈ 0,45); badanie na danych rynku bazowego, perp tylko jako wykonanie, a różnice z P2–P4 wchodzą
  jako koszt. Zgodność P5 < 0,95 (korelacja zwrotów) → flaga: indeks giełdy ≠ rynek bazowy.

**Kogo nie ma w zbiorze:** kontrakty już zdjęte z giełd (spis pokazuje tylko handlowane — tu bez znaczenia, bo nie mierzymy
zwrotów); weekendowe spready (migawki tylko pn wieczór); opłaty VIP i rabaty; płynność głębsza niż najlepsza oferta.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

- **Carry nie przechodzi przez te kontrakty.** Na krypto długie pozycje płacą stałą stopę 0,01 % co 8 h (~11 % rocznie)
  plus premię. Na TradFi giełdy ustawiły tę stopę na **zero**. Wzór fundingu ma „martwą strefę” ±0,05 % na 8 h (ok. ±55 %
  rocznie): dopóki cena kontraktu nie odjedzie od indeksu tak daleko, funding wynosi dokładnie 0. Różnica stóp procentowych
  dwóch walut to 0–4 % rocznie — **nie ma jak się pojawić w fundingu.** Długi USDJPY na prawdziwym rynku zarabia ~2,8 %
  rocznie na różnicy stóp; na perpie dostaje 0 (98 % odczytów to równe zero).
- **Dobra strona tego samego:** trzymanie pozycji kosztuje zwykle ~0 (u każdego z 459 instrumentów TradFi najczęstsza
  wartość fundingu to 0). Wyjątki są po stronie popytu: popularne akcje i surowce na Binance — długie płacą tam 5–15 %
  rocznie; te same surowce na Bybit prawie nic. Giełda ma znaczenie.
- **Koszty są małe w płynnym rdzeniu** (waluty, surowce, główne ETF-y, 5 największych akcji): ok. 0,04 % za stronę, poniżej
  0,07 % zakładanego w projekcie (KO1). Ale to stawki promocyjne; ogon mniej płynnych akcji ma spread 5–12 pb (punktów
  bazowych, setnych procenta).
- **Weekend:** indeksy giełd nie zamierają (giełdy wyceniają je wtedy z własnej księgi zleceń albo z innych źródeł), a ruch
  perpa w weekend zapowiada poniedziałkową lukę rynku bazowego bez skrzywienia (β ≈ 0,9–1,0), choć z szumem (R² 0,46–0,84).
- **Historia jest za krótka na test jakiejkolwiek strategii** (najdłużej złoto na Binance: 9,6 miesiąca). Strategię trzeba
  badać na długich danych rynku bazowego, a perp traktować tylko jako miejsce wykonania.

## Wynik

Pełny stdout: `raw_output.txt`; tabele: `spis.csv`, `funding.csv`, `funding_wzor.csv`, `koszty.csv`, `zamkniety_rynek.csv`,
`zgodnosc.csv`. Dane: funding Bybit 60 853 odczytów / 258 symboli, Binance 70 524 / 207 (od startu każdego instrumentu, BTC od
2025-12-01); świece 1 h (cena, indeks, mark) rdzenia: Bybit 24, Binance 25 instrumentów.

**P1 — spis (2026-09-28).**

| giełda | akcje | ETF (w tym obligacyjne) | surowce | waluty | inne | najdłuższa historia |
|---|---|---|---|---|---|---|
| Bybit | 196 (USA 168, HK 19, KR 7, CN 2) | 54 (TLT, TBT, TMF) | 4 (XAU, XAG, WTI, Brent) | 3 (EURUSD, GBPUSD, USDJPY — od 09-08) | — | XAU 204 dni |
| Binance | 156 | 37 (TBT, TMF; bez TLT) | 8 (+ platyna, pallad, miedź, gaz) | 1 (USDBRL — od 09-21) | 4 „przed IPO” | XAU 291 dni |

Interwał fundingu prawie wszędzie 8 h (4 h: Binance surowce i akcje HK/KR/CN, Bybit XAU/XAG). Dźwignia Bybit: akcje zwykle
25×, waluty 100× (Binance nie publikuje jej bez klucza).

**P2 — funding: mechanizm (ma pierwszeństwo przed statystyką).**
- Binance `interestRate` (migawka 18:49 UTC): **0 dla 202 instrumentów TradFi**, 0,00005 dla 4 „przed IPO”, 0,0001 dla BTCUSDT.
- Bybit (dokumentacja nie podaje I dla TradFi) — odtworzenie ze wzoru F = P̄ + clamp(I − P̄, ±0,05 %), P̄ ważone liniowo jak
  w dokumentacji, 14 dni: **I = 0 → 100 % odczytów EURUSD, USDJPY i XAU zgodnych w 0,05 pb**; I = 0,01 % → 2–61 % (zwykła
  średnia). Kontrola: BTCUSDT z I = 0,01 % → 100 % zgodnych. Przyrząd czyta więc znaną stałą krypto i zero TradFi.
- Wartość modalna = 0 u **każdego** instrumentu TradFi obu giełd (poza „przed IPO”); kontrola BTCUSDT: modalna 0,01 %/8 h.

**P2 — waluty (f̂ = funding roczny płacony przez długą, % rocznie; model A = 10,95, C = 0; B ze stóp FRED).**

| giełda | para | n | N_eff | f̂ [95 % CI] | zero (udział) | B | CI zawiera |
|---|---|---|---|---|---|---|---|
| Bybit | EURUSD | 62 | 62 | −2,28 [−7,72; +3,17] | 90,3 % | +1,37 | B, C |
| Bybit | GBPUSD | 62 | 62 | 0,00 [0,00; 0,00] | 100 % | +0,04 | C |
| Bybit | USDJPY | 62 | 62 | −0,06 [−0,16; +0,05] | 98,4 % | −2,80 | C |
| Binance | USDBRL | 31 | 31 | +16,24 [+1,65; +30,82] | 64,5 % | +10,18 | A, B (nie rozróżnia — z góry poza decyzją) |

**P2 — pozostałe klasy: mediana f̂ po instrumentach [kwartyle], % rocznie; w nawiasie liczba instrumentów.**

| klasa | Bybit | Binance |
|---|---|---|
| akcje | +2,08 [−0,22; +6,62] (196) | +4,53 [+0,11; +12,02] (156) |
| ETF | −0,45 [−2,79; +1,91] (51) | +0,50 [−4,27; +4,30] (35) |
| ETF obligacyjne | +4,61 [−4,07; +15,29] (3) | −20,71 [−34,16; −7,26] (2: TBT, TMF — lewarowane) |
| surowce | −2,85 [−12,50; +5,07] (4) | +15,25 [+3,14; +20,39] (8) |
| kontrola BTCUSDT (f̂ [95 % CI]) | +2,50 [+1,16; +3,85] | +3,14 [+1,01; +5,26] |

Punkt odniesienia: finansowanie długiej pozycji kontraktem terminowym ≈ r_USD − dochód aktywa; r_USD (DFF) ≈ 3,6 %.

**P3 — koszty (WSTĘPNIE: 2 migawki 18:19 i 18:49 UTC, obie w sesji USA; ostateczne po 00:10 UTC).** Opłaty oficjalne TradFi
(promocja „do odwołania”): Bybit taker 0,0275 % / maker 0 (od 2026-06-16), Binance taker 0,04 % / maker 0 (od 2026-03-31);
standard: 0,055 % / 0,05 %. Rdzeń — mediana spreadu: Bybit 1,55 pb, Binance 1,10 pb; **koszt strony: Bybit 0,036 %
(0,51× KO1), Binance 0,046 % (0,65×)**; przy stawkach standardowych 0,063 % / 0,056 %. Mediana spreadu po wszystkich
instrumentach: Bybit akcje 11,8 pb, ETF 11,1, obligacyjne 26,4, waluty 1,2, surowce 1,1; Binance akcje 5,3, ETF 5,4, obligacyjne 13,3.

**P4 — zamknięty rynek bazowy (rdzeń, per klasa).**

| giełda | klasa | (a) indeks bez zmiany: otw. / zamk. | (b) p95 bazisu zamk./otw. | (c) weekend β (R²; zamknięć) | noce β (R²) |
|---|---|---|---|---|---|
| Bybit | akcje (5) | 0 / 0,0 % | 1,58 | 0,98 (0,57; 22) | 0,95 (0,55) |
| Bybit | ETF (8) | 0 / 0,9 % | 1,20 | 0,98 (0,84; 21) | 0,97 (0,81) |
| Bybit | ETF oblig. (3) | 0 / 2,6 % | 1,16 | 1,04 (0,77; 9) | 1,02 (0,70) |
| Bybit | surowce (4) | 0 / 0,3 % | 1,32 | 0,90 (0,79; 29) | — |
| Bybit | waluty (3) | 0 / 0 % | 0,90 | 0,04 (0,02; **3**) | — |
| Binance | akcje (5) | 0 / 7,8 % | 1,43 | 0,94 (0,46; 33) | 0,94 (0,54) |
| Binance | ETF (8) | 0 / 6,1 % | 1,80 | 0,95 (0,83; 28) | 0,94 (0,81) |
| Binance | ETF oblig. (2) | 0 / 0 % | 1,30 | 1,06 (0,78; 9) | 1,04 (0,68) |
| Binance | surowce (8) | 0,8 / 35,0 % | 1,43 | 0,88 (0,67; 42) | — |
| obie | kontrola BTC | 0 / 0 % | 0,93–0,98 | 1,03 (0,92; 45) | 1,06 (0,85) |

(c): G = luka indeksu od zamknięcia do pierwszej godziny po otwarciu, R = ruch perpa w czasie zamknięcia; β z MNK. Najwyższy
stosunek (b) per instrument: 2,90 (Binance XAG). (d) Funding rozliczany przy zamkniętym vs otwartym rynku (mediany rdzenia): bez
stałego wzorca (np. Bybit surowce −8,6 → +5,3 %/rok, Binance akcje +13,1 → +9,7) — `zamkniety_rynek.csv`.

**P5 — zgodność z niezależnym źródłem (FRED; korelacja dziennych zwrotów).**

| instrument | pora z pre-rejestracji (16:00 UTC) | zamknięcie NYSE (dodatkowo) | n zwrotów | mediana różnicy poziomu |
|---|---|---|---|---|
| EURUSD / GBPUSD / USDJPY (Bybit) | 0,997 / 0,997 / 0,998 | — | 8 | 0,005–0,009 % |
| SPY (Bybit / Binance) ↔ S&P 500 | 0,69 / 0,73 | **0,997 / 0,997** | 89 / 117 | — |
| QQQ ↔ Nasdaq-100 | 0,80 / 0,81 | **0,9996 / 0,9994** | 97 / 120 | — |
| WTI ↔ DCOILWTICO | 0,90 / 0,91 | — | 125 / 119 | 3,1 / 3,0 % |
| Brent ↔ DCOILBRENTEU | 0,82 / 0,83 | — | 92 / 119 | 4,3 / 5,1 % |
| USDBRL (Binance) | brak: FRED kończy się 09-18, kontrakt od 09-21 | | 0 | |

## Decyzje z pre-rejestracji

- **D1 carry walutowe — carry NIE jest przenoszone.** Uczciwie: dosłownie reguła daje „pozostały układ” (C, C oraz „B albo C”),
  bo z góry nazwałem tylko A jako „nieprzenoszone”, a model C (f = 0) to z definicji także brak carry — luka w regule, moja.
  Rozstrzyga dowód mechanizmu, któremu pre-rejestracja dała pierwszeństwo: I = 0 na obu giełdach i martwa strefa ±0,05 %/8 h
  sprawiają, że różnica stóp 0–4 %/rok z konstrukcji wzoru nie może trafić do fundingu. EURUSD („B albo C”) ma 90 % zer; jego
  średnia −2,28 % pochodzi z kilku odczytów spoza strefy, nie z różnicy stóp (B = +1,37 ma przeciwny znak).
- **D2 koszt — model KO1 obowiązuje (zachowawczo):** 0,036–0,046 % za stronę w rdzeniu (≤ 0,07 %), także przy stawkach
  standardowych (0,056–0,063 %). Wstępnie — do potwierdzenia na komplecie migawek.
- **D3 zamknięty rynek — bez twardego wymogu:** p95 bazisu przy zamkniętym rynku ≤ 1,8× otwartego w każdej klasie (próg 3×),
  β weekendu 0,88–1,06 (próg 0,5). Wyjątek: waluty — 3 weekendy, β 0,04 — nierozstrzygnięte; do czasu pomiaru waluty tylko
  w godzinach otwarcia. R² 0,46–0,84 znaczy, że weekendowa cena perpa to przybliżenie poniedziałku, nie jego kopia.
- **D4 historia — strategii nie da się zmierzyć na samych perpach** (maks. 9,6 miesiąca). Zgodność: waluty i ETF-y ≥ 0,997
  (ETF-y przy porze zamknięcia NYSE — pora 16:00 z pre-rejestracji była dla nich błędem projektu: FRED podaje zamknięcia, więc
  16:00 porównywało cenę ze środka sesji z ceną zamknięcia). **Ropa 0,82–0,91 < 0,95 → flaga, ale nie indeksu:** FRED ma ceny
  spot (Brent Europe, WTI Cushing), a perpy śledzą najbliższy kontrakt terminowy — różnica 3–5 % poziomu to bazis spot–futures
  i inna godzina wyceny; zgodności z rynkiem futures ta runda nie sprawdziła.

## Co na plus (+) / Co na minus (−)

**(+)** Dowód mechanizmu z dwóch niezależnych stron (parametr publikowany przez Binance; odtworzenie wzoru Bybit co do 0,05 pb)
i kontrola pozytywna na BTC (ta sama metoda czyta znaną stałą 0,01 %). Druga droga (bramka 16a): udziały zer i średnie roczne
walut, XAU i BTC przeliczone osobnym kodem wprost z surowych plików — zgodne z reporterem (EURUSD −2,28 %, GBPUSD 0,00, USDJPY
−0,05 vs −0,06 — zaokrąglenie interwału, BTC 2,50 %); `interestRate` policzony wprost z migawki: 202 × 0. Wynik NIE potwierdza
idealnie założenia z rozmowy: przewidywałem „kopię krypto” (długie płacą ~11 %/rok), a jest zero — wniosek dla carry ten sam,
ale koszt trzymania odwrotny. Dane bez duplikatów i dziur godzinowych; 70 testów nowego kodu, w tym właściwości stronicowania.
**(−)** Walut jest mało: 3 pary Bybit po 20 dniach i 3 weekendach, USDBRL tydzień. Stopa 0 to stan dzisiejszy — giełda może ją
zmienić (Binance zmienia `interestRate` per symbol). Opłaty są promocyjne. Migawki tylko z poniedziałkowego wieczoru (bez
weekendu), tylko najlepsza oferta (bez głębokości). P5 dla ropy porównuje futures ze spotem. Rdzeń P4 to 5 najpłynniejszych akcji,
nie cała klasa. **Kogo nie ma:** kontrakty już zdjęte; dywidendy (czy giełda koryguje za nie cenę perpa — nie sprawdzone); VIP
i rabaty; dźwignia Binance; okres przed startem kontraktów (to nie wpływa na opis, ale żadna liczba nie mówi nic o stresie
rynkowym na tych kontraktach).

## Wniosek

**Prostym językiem:** perpetuale TradFi to tanie i dobrze wyceniane miejsce, żeby zająć pozycję w kierunku ruchu akcji, ETF-ów
(także obligacyjnych) i surowców — ale nie źródło carry. Funding ma tam stopę zero i szeroką martwą strefę, więc różnica stóp
procentowych nie trafia do posiadacza kontraktu. Pomysł „carry na kilku klasach” (krok 2 z rozmowy) odpada w tej infrastrukturze.
Zostaje pytanie, jaki mechanizm kierunkowy na rynkach tradycyjnych przetrwał publikację — to trzeba badać na długich danych rynku
bazowego (TX1: sam trend po 2013 nie wystarcza), a perp traktować jako wykonanie.

## Rekomendacja

1. **Krok 2 w wersji „carry: waluty + obligacje na perpach” nie startuje** (mechanizm, D1). Carry wymagałoby innego instrumentu
   (broker z punktami swapowymi albo kontrakty terminowe) — poza infrastrukturą projektu; decyzja użytkownika, moja rekomendacja: nie.
2. **Jeśli kierunek TradFi zostaje:** osobna sesja wybiera z `quant-strategy-catalog` JEDEN mechanizm kierunkowy z priorytetem po
   publikacji na tyle dużym, żeby przyrząd go widział (Sharpe ≥ ~0,5 na ~13 latach), i liczy moc na danych rynku bazowego. Wykonanie
   na perpach z kosztem ≤ 0,07 %/stronę (D2) i z ryzykiem fundingu po stronie popytu: na Binance długie w popularnych instrumentach
   płacą 5–15 %/rok — wykonanie raczej na Bybit albo z limitem fundingu w regule.
3. **Obserwacja do kartoteki, NIE rekomendacja:** ten sam surowiec ma inny funding na dwóch giełdach (mediana surowców: Binance
   +15 %/rok, Bybit −3 %/rok). To możliwe „carry z hedgem” między giełdami — odczytane z tej rundy, więc tylko jako hipoteza do
   pre-rejestracji na PRZYSZŁYCH danych; ten sam typ produktu co carry COIN-M (niski zwrot z hedgem), czyli nie cel użytkownika.
4. **Przed realnymi pieniędzmi na TradFi:** dywidendy (czy giełda koryguje cenę perpa), stawki po promocji, depozyt i dźwignia na
   Binance, spready w weekend (migawka w sobotę), a dla walut — więcej weekendów niż 3.

