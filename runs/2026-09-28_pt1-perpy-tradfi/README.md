# PT1 — perpetuale TradFi na Bybit i Binance: spis, funding, koszty, weekend, zgodność z rynkiem bazowym (2026-09-28)

> **STATUS: ZAMKNIĘTA (opisowo, 0 wariantów — POZA licznikami). Bramki 16a/16b: „Revision” → po poprawkach Caveats.**
> Perpetuale TradFi na obu giełdach mają w fundingu **stopę procentową 0** (Binance publikuje `interestRate` = 0 dla 202
> z 206; Bybit — wzór z I = 0 odtwarza 100 % odczytów). Nie ma więc **automatycznego carry** (w krypto długie płacą stałe
> 0,01 %/8 h); carry może przyjść tylko przez premię, którą arbitraż utrzyma poza martwą strefą ±0,05 %/8 h. Na 3 młodych
> parach walutowych Bybit (20 dni, obrót 28–670 tys. USDT/dobę) funding = 0 w 90–100 % odczytów: **różnica stóp dziś nie
> jest wypłacana — carry walutowe na tych parach dziś niewykonalne.** Surowce i obligacje — nierozstrzygnięte (funding złota
> ≈ r_USD, ropy ujemny — opis po przeglądzie, nie test). D1 dosłownie: „pozostały układ” → dalsze zbieranie fundingu. Najczęstszy
> odczyt fundingu to 0, ale długie w akcjach płacą w medianie 2,1–4,5 %/rok (popularne 10–16 %); mediana kosztu wejścia
> w rdzeniu ≤ 0,07 % (KO1), typowa akcja 0,067–0,087 %. Pre-rejestracja: commit `85365a0` (przed danymi).

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
- **Komenda:** `PYTHONUTF8=1 py -m data.fetch_tradfi_perps spis|funding|swiece|premia` (migawki: `migawka --co 1800 --do
  2026-09-29T00:10` w tle od 18:19 UTC), potem `PYTHONUTF8=1 py -m backtest.run_pt1_tradfi > raw_output.txt`; druga droga:
  `py runs/2026-09-28_pt1-perpy-tradfi/druga_droga.py > druga_droga.txt`.
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

- **Carry nie przychodzi „samo”.** Na krypto długie pozycje płacą stałą stopę 0,01 % co 8 h (~11 % rocznie) plus premię.
  Na TradFi giełdy ustawiły tę stopę na **zero**. Wzór fundingu ma „martwą strefę” ±0,05 % na 8 h (ok. ±55 % rocznie):
  dopóki średnia premia (różnica ceny kontraktu i indeksu) mieści się w tej strefie, funding wynosi dokładnie 0. Różnica stóp
  procentowych trafi więc do posiadacza kontraktu tylko wtedy, gdy arbitraż (np. kupno aktywa i sprzedaż kontraktu) wypchnie
  premię poza strefę.
- **Waluty: dziś różnica stóp nie jest wypłacana.** Trzy pary na Bybit istnieją 20 dni i mają mały obrót (28–670 tys. USDT
  na dobę). Funding jest tam równy 0 w 90–100 % odczytów. Długi USDJPY na zwykłym rynku walutowym zarabia ok. 2,8 % rocznie
  na różnicy stóp; na perpie 61 z 62 odczytów to zero. Przy EURUSD i GBPUSD różnica stóp jest mała (0–1,4 % rocznie), więc
  „carry przenoszone” i „zero” dają tam prawie to samo. Carry walutowe na tych parach jest dziś niewykonalne.
- **Tam, gdzie arbitraż działa, funding wygląda na koszt carry** — to opis dopisany po przeglądzie, nie test
  z pre-rejestracji. Długie w złocie płacą 3,6–4,0 % rocznie, prawie tyle co stopa dolarowa (3,6 %). W ropie długie dostają
  12–28 % rocznie. USDBRL: +16 % rocznie, w tę samą stronę co różnica stóp. Porównania pozostałych klas ze „stopa USD minus
  dochód aktywa” instrument po instrumencie nie wykonano — dla surowców i obligacji pytanie o carry zostaje otwarte.
- **Trzymanie pozycji nie jest darmowe.** Najczęstszy odczyt fundingu to 0 (u każdego z 459 instrumentów TradFi), ale
  długa pozycja w typowej akcji (mediana po instrumentach) płaci ok. 2,1 % rocznie (Bybit) i 4,5 % (Binance), a w popularnych
  akcjach 10–16 % (NVDA, MU, MSTR — dużo chętnych na długie pozycje). Ten sam instrument w tym samym okresie ma na obu
  giełdach prawie ten sam funding (np. złoto 4,0 i 3,6 %, MU 16,4 i 15,1 %). Różnice median całych klas między giełdami
  wynikają z innego składu klas i innego okresu (paradoks Simpsona), nie z giełdy. Wyraźny wyjątek: ropa WTI (funding −12 i −28 %
  rocznie — długie dostają).
- **Koszty wejścia (wstępnie, 2 migawki):** mediana rdzenia (waluty, surowce, główne ETF-y, 5 największych akcji) to ok.
  0,04 % za stronę, poniżej 0,07 % zakładanego w projekcie (KO1). Ale rdzeń wybrano regułą, nie płynnością: 7 z 23
  instrumentów rdzenia Bybit i 4 z 24 Binance kosztuje więcej niż 0,07 %. Typowa akcja: 0,087 % (Bybit) i 0,067 % (Binance);
  mediana spreadu klasy akcji to 5–12 pb (punktów bazowych, setnych procenta). Opłaty są promocyjne.
- **Weekend:** indeksy giełd przy zamkniętym rynku bazowym zwykle się ruszają (bez zmiany: Bybit 0–2,6 % godzin; Binance
  surowce 35 %, akcje 7,8 %, ETF-y 6,1 % — giełdy wyceniają je wtedy z własnej księgi zleceń albo z innych źródeł), a ruch
  perpa w weekend zapowiada poniedziałkową lukę rynku bazowego bez skrzywienia (β ≈ 0,9–1,0 w każdej klasie, dolna granica
  95 % przedziału ≥ 0,53), choć z szumem (R² 0,46–0,84). Wyjątki: miedź i pallad na Binance (β 0,54 i 0,63; przedział
  obejmuje próg 0,5) oraz waluty (tylko 3 weekendy) — tam handel tylko przy otwartym rynku bazowym.
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
  w dokumentacji, 14 dni; ten sam wariant ważenia i ta sama tolerancja 0,05 pb dla obu wartości I: **I = 0 → 100 % odczytów
  EURUSD, USDJPY i XAU zgodnych; I = 0,01 % → 2–53 %** (USDJPY 2 %, EURUSD 15 %, XAU 53 %). Kontrola: BTCUSDT z I = 0,01 %
  → 100 % zgodnych, z I = 0 → 12 %. Przyrząd czyta więc znaną stałą krypto i zero TradFi.
- Wartość modalna = 0 u **każdego** instrumentu TradFi obu giełd (poza „przed IPO”); kontrola BTCUSDT: modalna 0,01 %/8 h.
  Masa punktowa BTC jest jednak mała — 6,4 % (Bybit) i 7,2 % (Binance) odczytów, wobec 35,85 % w F1 — więc kontrola działa
  przez wartość modalną i wzór, nie przez wielkość masy.

**P2 — waluty (f̂ = funding roczny płacony przez długą, % rocznie; model A = 10,95, C = 0; B ze stóp FRED).** Kolumny
„N_eff”, „f̂ [95 % CI]” i „CI zawiera” poprawione po przeglądzie 16b (dopisek pod tabelą); f̂ i udział zer bez zmian.

| giełda | para | n | zera | N_eff | f̂ [95 % CI] | B | CI zawiera / co rozstrzyga |
|---|---|---|---|---|---|---|---|
| Bybit | EURUSD | 62 | 56 (90,3 %) | ≈ 31 | −2,28 [−10,0; +5,4] | +1,37 | B, C → „B albo C” |
| Bybit | GBPUSD | 62 | 62 (100 %) | — | 0,00 (przedział zdegenerowany) | +0,04 | „B albo C” (B ≈ C; do ~5 % odczytów może być niezerowych) |
| Bybit | USDJPY | 62 | 61 (98,4 %) | — | −0,055 | −2,80 | C — B wykluczone udziałem zer |
| Binance | USDBRL | 31 | 20 (64,5 %) | ≈ 24 | +16,24 [−0,5; +33,0] | +10,18 | A, B, C (C na krawędzi) — z góry poza decyzją |

Dopisek (16b). Pierwotnie tabela miała N_eff = n dla wszystkich par. To nie był dowód niezależności odczytów, tylko wartość
awaryjna kanonicznego estymatora (`checkpoint_lib`, suma autokorelacji do opóźnienia 50): przy 31–62 odczytach suma
zaszumionych autokorelacji wyszła ujemna (mianownik 1 + 2Σρ: EURUSD −0,30, USDBRL −0,60), a wtedy funkcja zwraca N_eff = n
(por. AU3). Tu N_eff z autokorelacji opóźnienia 1: n / (1 + 2ρ₁). EURUSD: ρ₁ ≈ 0,49 → N_eff ≈ 31, CI [−10,0; +5,4] (bootstrap
blokowy, blok 3 odczyty: [−10,6; +3,4]). USDBRL: ρ₁ ≈ 0,16 → N_eff ≈ 24, CI [−0,5; +33,0] — obejmuje C, ale na krawędzi
(bootstrap blokowy daje [+3,6; +32,6], już bez C). GBPUSD: 62 zera na 62 — przedział [0; 0] nic nie mówi; reguła trzech (3/n)
dopuszcza do ~5 % niezerowych odczytów, a B = +0,04 %/rok to prawie C, więc wynik brzmi „B albo C”, nie „C”. USDJPY: przy B
(−2,80 %/rok) średnia wymagałaby częstych odczytów niezerowych, a jest jeden na 62 (średnia −0,055 %/rok) — to wyklucza B;
przedział Walda z jednego niezerowego odczytu ([−0,16; +0,05]) nie jest tu argumentem. Wobec modelu A wynik bez zmian: 10,95
leży poza przedziałem każdej z trzech par Bybit.

**P2 — pozostałe klasy: mediana f̂ po instrumentach, średnia, [kwartyle] — % rocznie; w nawiasie liczba instrumentów.** Klasy
z 2–4 instrumentami: wartości zamiast kwartyli. Każdy instrument liczony na własnym oknie (od startu kontraktu).

| klasa | Bybit | Binance |
|---|---|---|
| akcje | mediana +2,08, średnia +1,84 [−0,22; +6,62] (196) | mediana +4,53, średnia +5,34 [+0,11; +12,02] (156) |
| ETF | mediana −0,45, średnia +0,77 [−2,79; +1,91] (51) | mediana +0,50, średnia −0,00 [−4,27; +4,30] (35) |
| ETF obligacyjne | TLT +26,0; TMF +4,6; TBT −12,8 (3) | TMF +6,2; TBT −47,6 (2; bez TLT) — TBT i TMF lewarowane |
| surowce | XAG +8,1; XAU +4,0; CL −9,7; BZ −20,8 (4) | mediana +15,25, średnia +9,35 [+3,14; +20,39] (8) |
| kontrola BTCUSDT (f̂ [95 % CI]) | +2,50 [+1,16; +3,85] | +3,14 [+1,01; +5,26] |

Najczęstszy odczyt to 0 w każdej klasie, ale średni koszt długiej pozycji nie jest zerowy: w typowej akcji (mediana po
instrumentach) ok. 2,1 %/rok (Bybit) i 4,5 % (Binance); popularne akcje 10–16 %/rok (Bybit: NVDA +10,4, MSTR +14,8, MU +16,4 —
popyt na długie pozycje); złoto ≈ r_USD; ropa — ujemny (długie dostają). Punkt odniesienia: finansowanie długiej pozycji
kontraktem terminowym ≈ r_USD − dochód aktywa; r_USD (DFF) ≈ 3,6 %. **Porównania z „r_USD − dochód aktywa” instrument po
instrumencie NIE WYKONANO** (dochodu aktywa — dywidend, kosztu składowania, korzyści z posiadania towaru — runda nie zbierała).
Niżej tylko opis.

**P2 — sprawdzenia opisowe po przeglądzie (post hoc, NIE pre-rejestrowane porównanie per instrument).**
- **Ten sam instrument, wspólne okno obu giełd** (od późniejszego pierwszego odczytu; funding roczny = suma stawek / długość
  okna; Bybit vs Binance, % rocznie): XAU +4,0 vs +3,6; XAG +8,1 vs +7,6; NVDA +10,4 vs +10,4; MU +16,4 vs +15,1; MSTR +14,8 vs
  +12,9; CL −12,0 vs −27,9; BZ −20,8 vs −26,5. Na 166 wspólnych instrumentach (okno ≥ 20 dni): mediana |różnicy| 2,2 pkt/rok,
  korelacja 0,85; różnicę > 10 pkt/rok ma 19 z nich (m.in. CL, IWM −31,7 vs −0,1, TBT −12,8 vs −39,9 i 9 instrumentów
  z Hongkongu) — bez stałego kierunku (13 razy więcej płaci długi na Binance, 6 razy na Bybit). Różnice median klas w tabeli
  wyżej (np. surowce −2,85 vs +15,25) to więc skutek innego składu klas i innego okresu (paradoks Simpsona: Binance ma też
  platynę, pallad, miedź i gaz, a złoto i srebro od grudnia–stycznia, gdy funding był wyższy — XAU na pełnym oknie +13,2),
  nie cecha giełdy.
- **Gdzie działa arbitraż, funding wygląda na koszt carry:** złoto na wspólnym oknie 3,6–4,0 %/rok ≈ r_USD 3,6 %; ropa — długie
  DOSTAJĄ 12–28 %/rok (CL i BZ na wspólnym oknie); USDBRL +16 %/rok, w tę samą stronę co B (+10,2). To obserwacje, nie test.

**P3 — koszty (WSTĘPNIE: 2 migawki 18:19 i 18:49 UTC, obie w sesji USA; ostateczne po 00:10 UTC).** Opłaty oficjalne TradFi
(promocja „do odwołania”): Bybit taker 0,0275 % / maker 0 (od 2026-06-16), Binance taker 0,04 % / maker 0 (od 2026-03-31);
standard: 0,055 % / 0,05 %. Rdzeń — mediana spreadu: Bybit 1,55 pb, Binance 1,10 pb; **koszt strony: Bybit 0,036 %
(0,51× KO1), Binance 0,046 % (0,65×)**; przy stawkach standardowych 0,063 % / 0,056 %. Mediana spreadu po wszystkich
instrumentach: Bybit akcje 11,8 pb, ETF 11,1, obligacyjne 26,4, waluty 1,2, surowce 1,1; Binance akcje 5,3, ETF 5,4, obligacyjne 13,3.

Zakres D2 (dopisek 16b; wstępnie, te same 2 migawki): rdzeń to reguła, nie płynność. Koszt strony powyżej 0,07 % ma 7 z 23
instrumentów rdzenia Bybit (EWJ, EWZ, GDX, XLE, TBT, TLT, TMF) i 4 z 24 Binance (GDX, XLE, TBT, TMF). Bybit EURUSD: obrót
~28 tys. USDT/dobę, spread ~4,5 pb. Mediana klasy akcji: 0,087 % za stronę na Bybit (60 % akcji powyżej KO1) i 0,067 % na
Binance (48 %); p90 spreadu akcji 13 pb (Binance) i 43 pb (Bybit). Werdykt „KO1 obowiązuje” dotyczy więc tylko MEDIANY rdzenia.

**P4 — zamknięty rynek bazowy (rdzeń, per klasa).**

| giełda | klasa | (a) indeks bez zmiany: otw. / zamk. | (b) p95 bazisu zamk./otw. | (c) weekend β [95 % CI] (R²; zamknięć) | noce β (R²) |
|---|---|---|---|---|---|
| Bybit | akcje (5) | 0 / 0,0 % | 1,58 | 0,98 [0,59; 1,37] (0,57; 22) | 0,95 (0,55) |
| Bybit | ETF (8) | 0 / 0,9 % | 1,20 | 0,98 [0,78; 1,18] (0,84; 21) | 0,97 (0,81) |
| Bybit | ETF oblig. (3) | 0 / 2,6 % | 1,16 | 1,04 [0,53; 1,55] (0,77; 9) | 1,02 (0,70) |
| Bybit | surowce (4) | 0 / 0,3 % | 1,32 | 0,90 [0,72; 1,08] (0,79; 29) | — |
| Bybit | waluty (3) | 0 / 0 % | 0,90 | 0,04 — bez przedziału (0,02; **3**) | — |
| Binance | akcje (5) | 0 / 7,8 % | 1,43 | 0,94 [0,57; 1,31] (0,46; 33) | 0,94 (0,54) |
| Binance | ETF (8) | 0 / 6,1 % | 1,80 | 0,95 [0,78; 1,13] (0,83; 28) | 0,94 (0,81) |
| Binance | ETF oblig. (2) | 0 / 0 % | 1,30 | 1,06 [0,55; 1,56] (0,78; 9) | 1,04 (0,68) |
| Binance | surowce (8) | 0,8 / 35,0 % | 1,43 | 0,88 [0,68; 1,08] (0,67; 42) | — |
| obie | kontrola BTC | 0 / 0 % | 0,93–0,98 | 1,03 [0,93; 1,13] (0,92; 45) | 1,06 (0,85) |

(c): G = luka indeksu od zamknięcia do pierwszej godziny po otwarciu, R = ruch perpa w czasie zamknięcia; β z MNK. Przedział
[95 % CI] dopisany po przeglądzie 16b: MNK łączny klasy, ale błąd standardowy liczony tak, jakby obserwacji było tyle, ile
różnych zamknięć (instrumenty jednej klasy dzielą ten sam weekend), rozkład t. Per instrument (42 instrumenty rdzenia bez walut
i BTC): β 0,54–1,64, R² 0,22–0,93. Binance miedź β 0,54 [0,22; 0,86] (30 weekendów) i pallad β 0,63 [0,21; 1,05] (35) — punkt
blisko progu 0,5 i przedział go obejmuje. Przedział obejmuje 0,5 także u 11 innych instrumentów (β 0,74–1,09, m.in. NVDA, SNDK,
CRCL, TBT, GDX) — tam przez małą liczbę weekendów albo niskie R², przy punkcie daleko od progu. Najwyższy stosunek (b) per
instrument: 2,90 (Binance XAG). (d) Funding rozliczany przy zamkniętym vs otwartym rynku (mediany rdzenia): bez stałego wzorca
(np. Bybit surowce −8,6 → +5,3 %/rok, Binance akcje +13,1 → +9,7) — `zamkniety_rynek.csv`.

**Przypis (przegląd 16c):** kalendarz surowców z pre-rejestracji nie zna świąt CME. 76 „otwartych” godzin z płaskim indeksem
Binance XAU (i 23 CL) to w całości święta (24–25.12, 1.01, 19.01, 16.02, 2–3.04) — komórka „Binance surowce (a) 0,8 %” to święta,
nie zamrożony indeks w godzinach handlu (na Bybit takich godzin 0). W (c) zamknięcie wielkanocne liczy się od piątku 21:00 (1 z 42
zamknięć), zamknięć 25.12 i 1.01 (c) nie mierzy, w (d) te godziny są „otwarte”. Kodu nie zmieniano (pre-rejestracja: święta tylko
NYSE); wpływ na D3 i wnioski — żaden.

**P5 — zgodność z niezależnym źródłem (FRED; korelacja dziennych zwrotów).**

| instrument | pora z pre-rejestracji (16:00 UTC) | zamknięcie NYSE (dodatkowo) | n zwrotów | mediana różnicy poziomu |
|---|---|---|---|---|
| EURUSD / GBPUSD / USDJPY (Bybit) | 0,997 / 0,997 / 0,998 | — | 8 | 0,005–0,009 % |
| SPY (Bybit / Binance) ↔ S&P 500 | 0,69 / 0,73 | **0,997 / 0,997** | 89 / 117 | — |
| QQQ ↔ Nasdaq-100 | 0,80 / 0,81 | **0,9996 / 0,9994** | 97 / 120 | — |
| WTI ↔ DCOILWTICO | 0,90 / 0,91 | — | 125 / 119 | 3,1 / 3,0 % |
| Brent ↔ DCOILBRENTEU | 0,82 / 0,83 | — | 92 / 119 | 4,3 / 5,1 % |
| USDBRL (Binance) | brak: FRED kończy się 09-18, kontrakt od 09-21 | | 0 | |

Ropa — sprawdzenie opisowe po przeglądzie (post hoc; ta sama metoda, indeks giełdy odczytany o innych godzinach UTC). WTI o
19:00 UTC: korelacja 0,956 (Bybit) i 0,958 (Binance) — dla WTI niską zgodność o 16:00 wyjaśnia pora odczytu. Brent: maksimum
0,894 i 0,879 (o 18:00 UTC), o żadnej godzinie nie dochodzi do 0,95; poziom perpa o każdej godzinie 3,3–5,3 % niżej niż FRED.
Flaga dla Brent zostaje; przyczyna (np. FRED = cena spot, perp = kontrakt terminowy) jest niesprawdzona.

## Decyzje z pre-rejestracji

- **D1 carry walutowe — dosłownie „pozostały układ” → opis + dalsze zbieranie fundingu (bez decyzji).** A (kopia krypto,
  10,95 %/rok) leży poza przedziałem każdej z trzech par Bybit. B od C nie da się odróżnić przy EURUSD i GBPUSD. Przy USDJPY B
  wykluczone udziałem zer: 61 z 62 odczytów = 0 wobec −2,80 %/rok w modelu B. Luka w regule (moja): z góry nazwałem
  „nieprzenoszone” tylko A, a model C (f = 0) to także brak carry. Opis w granicach danych: stopa w fundingu = 0 na obu
  giełdach, więc nie ma automatycznego carry; carry może przyjść tylko przez premię utrzymywaną arbitrażem poza martwą strefą
  ±0,05 %/8 h, a na 3 młodych parach (20 dni, obrót 28–670 tys. USDT/dobę) tego dziś nie widać — **carry walutowe na tych
  parach dziś niewykonalne.** Tam, gdzie arbitraż jest (złoto, ropa, USDBRL — opis post hoc), funding wygląda na koszt carry;
  surowce i obligacje — nierozstrzygnięte. Dalsze zbieranie fundingu jest tanie i w 1–4 miesiące może rozstrzygnąć B/C dla
  EURUSD i USDBRL (GBPUSD: B = +0,04 ≈ C — nie do rozróżnienia i bez znaczenia ekonomicznego).
- **D2 koszt — model KO1 obowiązuje dla MEDIANY rdzenia (wstępnie):** 0,036–0,046 % za stronę (≤ 0,07 %), także przy stawkach
  standardowych (0,056–0,063 %). Rdzeń to reguła, nie płynność: powyżej 0,07 % jest 7 z 23 instrumentów rdzenia Bybit i 4 z 24
  Binance, a typowa akcja kosztuje 0,087 % (Bybit) / 0,067 % (Binance). Strategia liczy więc koszt per instrument, nie
  z mediany. Do potwierdzenia na komplecie migawek.
- **D3 zamknięty rynek — bez twardego wymogu dla klas; wymóg dla walut oraz miedzi i palladu na Binance.** Decyzja opiera się
  tylko na (c). Miara (b) nie wykryje złej wyceny, gdy indeks w czasie zamknięcia pochodzi z księgi samego kontraktu — wtedy
  bazis jest mały z konstrukcji. β weekendu per klasa 0,88–1,06; 95 % CI przy n = liczbie zamknięć (9–42) ma dolne granice
  0,53–0,78 — nad progiem 0,5 w każdej klasie. Per instrument β 0,54–1,64 (R² 0,22–0,93). Binance miedź β 0,54 [0,22; 0,86]
  i pallad 0,63 [0,21; 1,05]: przedziały obejmują próg 0,5 → dla nich, jak dla walut (3 weekendy, β 0,04), wykonanie tylko
  w godzinach otwarcia rynku bazowego. R² 0,46–0,84 znaczy, że weekendowa cena perpa to przybliżenie poniedziałku, nie jego
  kopia.
- **D4 historia — strategii nie da się zmierzyć na samych perpach** (maks. 9,6 miesiąca). Zgodność: waluty i ETF-y ≥ 0,997
  (ETF-y przy porze zamknięcia NYSE — pora 16:00 z pre-rejestracji była dla nich błędem projektu: FRED podaje zamknięcia, więc
  16:00 porównywało cenę ze środka sesji z ceną zamknięcia). **Ropa 0,82–0,91 < 0,95 o 16:00 → flaga.** Po przeglądzie (opis,
  post hoc): WTI o 19:00 UTC 0,956–0,958 — dla WTI niską zgodność wyjaśnia pora; Brent maks. 0,88–0,89 o każdej godzinie przy
  stałej różnicy poziomu (3,3–5,3 %) → flaga dla Brent zostaje; hipoteza „FRED to spot, perp śledzi futures” niesprawdzona.

## Co na plus (+) / Co na minus (−)

**(+)** Dowód mechanizmu z dwóch niezależnych stron (parametr publikowany przez Binance; odtworzenie wzoru Bybit co do 0,05 pb)
i kontrola pozytywna na BTC (ta sama metoda czyta znaną stałą 0,01 % — przez wartość modalną i wzór; masa punktowa BTC to tylko
6–7 % odczytów, w F1 35,85 %). Druga droga (bramka 16a): udziały zer i średnie roczne walut, XAU i BTC przeliczone osobnym kodem
wprost z surowych plików — zgodne z reporterem (EURUSD −2,28 %, GBPUSD 0,00, USDJPY −0,055 — „−0,05” i „−0,06” to zaokrąglenia
tej samej liczby, XAU 4,04 %, BTC 2,50 %); `interestRate` policzony wprost z migawki: 202 × 0. Liczby dopisane po przeglądzie
(N_eff walut, wspólne okna, koszty, przedziały β, ropa o innych godzinach) przeliczone jeszcze raz osobnym kodem — zgodne
z recenzją (drobne różnice w „Bramki jakości”). Wynik NIE potwierdza idealnie założenia z rozmowy: przewidywałem „kopię krypto”
(długie płacą ~11 %/rok), a jest zero — brak automatycznego carry, a koszt trzymania zależy od popytu na długie pozycje. Dane bez
duplikatów i dziur godzinowych; 91 testów nowego kodu (70 + 21 z poprawek 16c), w tym właściwości stronicowania.
**(−)** Walut jest mało: 3 pary Bybit po 20 dniach i 3 weekendach, USDBRL tydzień; obrót par Bybit 28–670 tys. USDT/dobę —
wynik walutowy opisuje dzisiejszy stan młodego rynku, nie trwałą cechę kontraktu. Pierwsza wersja raportu mówiła za dużo
(poprawione po przeglądzie): „różnica stóp z konstrukcji wzoru nie może trafić do fundingu” (może — przez arbitraż premii),
„giełda ma znaczenie” (paradoks Simpsona), „trzymanie kosztuje zwykle ~0” (to wartość najczęstsza, nie średnia), N_eff = n dla
walut (wartość awaryjna estymatora), „ropa: FRED to spot” (niesprawdzone). Sprawdzenia dopisane po przeglądzie (wspólne okna,
złoto / ropa / USDBRL wobec carry, ropa o innych godzinach, przedziały β) są post hoc — opis, nie test. Stopa 0 to stan
dzisiejszy — giełda może ją zmienić (Binance zmienia `interestRate` per symbol). Opłaty są promocyjne. Migawki tylko
z poniedziałkowego wieczoru (bez weekendu), tylko najlepsza oferta (bez głębokości). Rdzeń P4 to 5 najpłynniejszych akcji, nie
cała klasa. **Kogo nie ma:** kontrakty już zdjęte; dywidendy (czy giełda koryguje za nie cenę perpa — nie sprawdzone); dochód
aktywa potrzebny do porównania z carry (dlatego porównania per instrument nie wykonano); płynność poza najlepszą ofertą — rdzeń
wybrano regułą, więc są w nim instrumenty z obrotem kilkudziesięciu tys. USDT na dobę (Bybit: EWJ ~23 tys., EURUSD ~28 tys.,
XLE i TBT ~41 tys.); VIP i rabaty; dźwignia Binance; okres przed startem kontraktów (to nie wpływa na opis, ale żadna liczba nie
mówi nic o stresie rynkowym na tych kontraktach).

## Bramki jakości (zasada 16)

- **16a walidacja (`data:validate-data`) i 16b statystyka (`data:statistical-analysis`): werdykt recenzenta „Revision” → po
  poprawkach Caveats.** Poprawione: (1) paradoks Simpsona — porównanie giełd po medianach klas zastąpione porównaniem tego
  samego instrumentu na wspólnym oknie; usunięte „giełda ma znaczenie” i preferencja Bybit; (2) zakres wniosku o carry — „brak
  automatycznego carry” zamiast „z konstrukcji nie może trafić”, waluty zawężone do 3 par i do „dziś”, surowce i obligacje
  nierozstrzygnięte, porównanie per instrument z „r_USD − dochód aktywa” jawnie „nie wykonano”; (3) statystyka walut — N_eff
  z autokorelacji opóźnienia 1, bootstrap blokowy, reguła trzech dla GBPUSD, USDJPY rozstrzygnięte udziałem zer; (4) zakres D2 —
  KO1 tylko dla mediany rdzenia; (5) przedziały β w D3 i wyjątki miedź / pallad; (6) ropa w P5 — sprawdzenie godzin zamiast
  niesprawdzonego „spot vs futures”. Liczby recenzji przeliczone osobnym kodem; różnice: XAU Binance na wspólnym oknie 3,58
  (recenzja 3,5); NVDA / MU Binance 10,40 / 15,07 (recenzja 10,5 / 15,2 — to samo z odczytem na granicy okna: 10,49 / 15,21);
  miedź [0,22; 0,86] z rozkładem t (recenzja [0,23; 0,85]); USDBRL w bootstrapie blokowym [+3,6; +32,6] — bez C. Ponad
  recenzję: różnicę > 10 pkt/rok między giełdami ma 19 ze 166 wspólnych instrumentów (nie tylko ropa), a przedział β obejmuje
  0,5 także u 11 instrumentów z β 0,74–1,09. Zostające zastrzeżenia: waluty to 20 dni (USDBRL 7); P3 z 2 migawek
  poniedziałkowego wieczoru (domknięcie po 00:10 UTC); sprawdzenia po przeglądzie oznaczone jako post hoc. Czerwona flaga
  „wynik idealnie potwierdza hipotezę” nie zachodzi: prognoza z rozmowy to A (kopia krypto), wynik dla walut to C (zero). Druga
  droga (`druga_droga.py` → `druga_droga.txt`) zgodna z reporterem.
- **16c przegląd diffu (`engineering:code-review`): Approve z uwagami.** Poprawki odporności kodu (stronicowanie, migawki,
  Retry-After / 418, zakres kalendarza) — commit `2522227` (91 testów nowego kodu, zielone). Kalendarz surowców nie zna świąt
  CME — przypis pod P4 (wpływ na D3 żaden).
- **Bezpieczeństwo (`security-review`, nowe połączenia sieciowe): Approve** — tylko https, stałe hosty, parametry przez
  urlencode, brak kluczy i sekretów. Opcjonalne utwardzenie: odrzucać przekierowania na adresy nie-https.

## Wniosek

**Prostym językiem:** perpetuale TradFi to w medianie tanie i przeważnie dobrze wyceniane miejsce, żeby zająć pozycję w kierunku
ruchu akcji, ETF-ów (także obligacyjnych) i surowców. Carry nie przychodzi tam „samo”: stopa w fundingu wynosi zero, więc różnica
stóp procentowych dociera do posiadacza kontraktu tylko wtedy, gdy arbitraż utrzymuje premię poza martwą strefą. Na trzech młodych
parach walutowych Bybit dziś tak nie jest — carry walutowe na nich jest dziś niewykonalne. Przy złocie, ropie i USDBRL funding
wygląda na koszt carry, ale to opis po przeglądzie, nie test — dla surowców i obligacji pytanie o carry zostaje otwarte. Dalsze
zbieranie fundingu jest tanie i to rozstrzygnie. Niezależnie od carry: strategię kierunkową trzeba badać na długich danych rynku
bazowego (TX1: sam trend po 2013 nie wystarcza), a perp traktować jako wykonanie — z kosztem liczonym per instrument i z fundingiem
po stronie popytu jako kosztem.

## Rekomendacja

1. **Carry walutowe na perpach — nie teraz** (D1: na 3 parach Bybit różnica stóp dziś nie jest wypłacana). Carry na surowcach
   i obligacjach — nierozstrzygnięte; hipoteza nie startuje bez pre-rejestrowanego porównania per instrument z „r_USD − dochód
   aktywa”. Tanie i bez decyzji: zbierać dalej funding. Jeśli odczyty EURUSD dalej będą zerowe, po ok. 3 miesiącach przedział
   wykluczy B; USDBRL przy obecnym rozrzucie wykluczy C po ok. 1 miesiącu (czysty podział B/C — ok. 4 miesiące); przy GBPUSD
   B = +0,04 ≈ C — nie do rozróżnienia żadną ilością danych. Carry przez inny instrument (broker z punktami swapowymi,
   kontrakty terminowe) — poza infrastrukturą projektu; decyzja użytkownika.
2. **Jeśli kierunek TradFi zostaje:** osobna sesja wybiera z `quant-strategy-catalog` JEDEN mechanizm kierunkowy z priorytetem po
   publikacji na tyle dużym, żeby przyrząd go widział (Sharpe ≥ ~0,5 na ~13 latach), i liczy moc na danych rynku bazowego.
   Wykonanie na perpach z kosztem liczonym per instrument (mediana rdzenia ≤ 0,07 %/stronę, typowa akcja 0,067–0,087 %; D2)
   i z fundingiem po stronie popytu jako kosztem w regule (popularne akcje 10–16 %/rok na obu giełdach na wspólnym oknie).
   Wyboru giełdy te dane nie uzasadniają: ten sam instrument ma prawie ten sam funding, a Bybit ma szersze spready akcji
   (mediana 11,8 vs 5,3 pb).
3. **Obserwacja do kartoteki, NIE rekomendacja:** ropa WTI ma na wspólnym oknie inny funding na dwóch giełdach
   (CL −12 vs −28 %/rok; Brent −21 vs −26). Podobnej wielkości różnice ma 19 ze 166 wspólnych instrumentów, bez stałego
   kierunku — to może być szum okna. Tylko jako hipoteza do pre-rejestracji na PRZYSZŁYCH danych; to ten sam typ produktu co
   carry COIN-M (niski zwrot z hedgem), czyli nie cel użytkownika.
4. **Przed realnymi pieniędzmi na TradFi:** dywidendy (czy giełda koryguje cenę perpa), stawki po promocji, depozyt i dźwignia na
   Binance, spready w weekend (migawka w sobotę), dla walut — więcej weekendów niż 3; waluty oraz miedź i pallad (Binance) — tylko
   przy otwartym rynku bazowym (D3).

## Użyte skille (CLAUDE.md zasada 19)

Wynik `PYTHONUTF8=1 py tools/skill_audit.py raport --galaz pt1-perpy-tradfi`:

### Użyte skille — gałąź `pt1-perpy-tradfi` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-09-28T18:13:38+00:00 | claude | `anthropic-skills:clas5-runda` |  |
| 2026-09-28T18:13:40+00:00 | claude | `anthropic-skills:clas5-quant` |  |
| 2026-09-28T18:13:54+00:00 | claude | `data:explore-data` |  |
| 2026-09-28T18:23:05+00:00 | claude (agent: general-purpose) | `engineering:testing-strategy` | Testy modułów PT1: data/fetch_tradfi_perps.py (pobieranie REST Bybit/Binance, stronicowanie wstecz/do przodu, ponowienia 429, zapis migawki — bez sieci, fałszywe get, właściwości hypothesis) i backte… |
| 2026-09-28T19:03:37+00:00 | claude (agent: general-purpose) | `engineering:code-review` |  |
| 2026-09-28T19:03:37+00:00 | claude (agent: general-purpose) | `data:validate-data` |  |
| 2026-09-28T19:03:40+00:00 | claude (agent: general-purpose) | `data:statistical-analysis` |  |
| 2026-09-28T19:03:40+00:00 | claude (agent: general-purpose) | `security-review` |  |

Razem: 8 wczytań, 8 różnych skilli: `anthropic-skills:clas5-quant`, `anthropic-skills:clas5-runda`, `data:explore-data`, `data:statistical-analysis`, `data:validate-data`, `engineering:code-review`, `engineering:testing-strategy`, `security-review`.

Co wniósł każdy: `clas5-runda` — pre-rejestracja przed danymi (commit `85365a0`), wiersz w rejestrze odczytów
(`runs/odczyty_historii.csv`) i wpis w INDEX; `clas5-quant` — masa punktowa fundingu z F1 → wartość modalna jako główna miara
i kontrola pozytywna na BTC; `data:explore-data` — profil nowego źródła: dziury, duplikaty, zmiany interwału fundingu, anomalia
SPCX; `engineering:testing-strategy` — testy bez sieci (fałszywe odpowiedzi REST) i właściwości `hypothesis` na stronicowaniu;
`data:validate-data` i `data:statistical-analysis` — bramki 16a/16b: paradoks Simpsona, zakres wniosku o carry, N_eff walut;
`engineering:code-review` i `security-review` — bramka 16c i nowe połączenia sieciowe. Momenty tabeli bez wpisu:
`quant-strategy-catalog` — runda nie tworzy hipotezy (potrzebny w kroku 2); `dataviz` — runda bez wykresu; `ta-toolkit`,
`lean-research` — nie dotyczy.
