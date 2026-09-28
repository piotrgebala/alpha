# PT1 — perpetuale TradFi na Bybit i Binance: spis, funding, koszty, weekend, zgodność z rynkiem bazowym (2026-09-28)

> **STATUS: W TOKU — pre-rejestracja zapisana 2026-09-28 ok. 18:40 UTC, PRZED pobraniem historii fundingu i cen
> oraz przed obejrzeniem migawek.** 0 wariantów — POZA licznikami: runda opisuje instrument wykonawczy, nie testuje
> żadnej strategii.

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

## Wynik

_(uzupełniane po przebiegu)_
