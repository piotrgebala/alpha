# P2 — carry przekrojowy: opłata pokrywa koszty, ale pełnego testu NIE DA SIĘ rozstrzygnąć (2026-09-22)

> **STATUS: ZAMKNIĘTA. Werdykt: NIEMIERZALNA** (D1 spełnione, D2 niespełnione — brakuje ~22×
> próby). Walidacja (16a): **CAVEATS** — patrz niżej.
>
> Sekcje od „ID testu" do „Ograniczenia znane z góry" to pre-rejestracja (commit 364e98d)
> i jej POPRAWKA 1 (commit c8afa31) — obie zapisane PRZED uruchomieniem, niezmienione.

## ID testu

**P2** — sonda wykonalności hipotezy **4A** (`STATUS.md` §17, ETAP 4): carry przekrojowy.
**0 wariantów, POZA licznikami hipotez** — ta sama rola co H2.0, Z19 i P1: rachunek
wykonalności PRZED wydaniem wariantu. Warunek utrzymania zera: **runda nie liczy i nie
drukuje średniego zwrotu z ruchu cen ani łącznego P&L strategii** (patrz „Czego ta runda NIE
liczy").

## Metadane

- Branch: `worktree-p2-carry-porzadki` (od `master` @ `c1f121a`).
- Decyzja użytkownika: 2026-09-22, „wykonaj powyższe" w odpowiedzi na propozycję
  „B — tania sonda carry przekrojowego (bez modelu, 0 wariantów)".
- Dane: Binance USDS-M, historia funding (`/fapi/v1/fundingRate`) i świece dzienne
  (`/fapi/v1/klines`, 1d) dla wszystkich symboli z publicznego archiwum
  `data.binance.vision` (952 symbole, w tym wycofane). Zakres **2020-01-01 → 2026-07-01**
  (koniec jak w bazie projektu).
- Komenda: `py -m backtest.run_carry_probe_p2 C:/Users/pitge/GIT/alpha/data/raw/universe`
  (kod: commity dcd0718, 841c1d3 + runner z poprawką 1). Dane: `data/raw/universe/<SYMBOL>_funding.parquet`
  i `<SYMBOL>_1d.parquet`, stan na 2026-07-01 (koniec zakresu). Pełny wydruk: `raw_output.txt`.

## Poprzedzające wyniki

- **H2.0** (`runs/2026-09-22_h2.0-funding-wykonalnosc/`) — carry na samym BTC: próg opłacalności
  spada **poniżej 50%** (48,13%), bo wypłata `(2p−1)·B + F > C` nie wymaga przewagi kierunkowej,
  gdy `F > C`. Ale moc 0,03–0,12×: w 6,8 roku mieści się tylko **1 240 nienakładających się
  okien 48h**. H2.0 zapisało: „żyje w formule PRZEKROJOWEJ, nie czasowej".
- **`STATUS.md` §17, rachunek mierzalności 4A** — przyjmował, że 20 instrumentów daje
  **160 660 transakcji** (20 × 8 033). **Ta runda sprawdza to założenie wprost i podejrzewa,
  że jest błędne:** koszyki monet w tym samym oknie czasowym są skorelowane (krypto chodzi
  razem, szczególnie w stresie — `docs/rag/01`, zasada 9, „4 instrumenty to nie 4× danych").
  Niezależną jednostką próby jest raczej **okno czasowe**, a przekrój zmniejsza ROZRZUT
  wyniku okna, a nie mnoży liczbę okien.
- **F1** — funding jako cecha KIERUNKOWA na BTC: 50,34%, brak efektu. To NIE przesądza o carry:
  carry nie przewiduje kierunku, tylko zbiera opłatę.
- **P1** — endpointy pozycjonowania mają 30 dni historii; **kontrola P1 potwierdziła, że
  `fundingRate` i `klines` mają historię od 2020** — to jest źródło danych tej rundy.
- **T1-diag** — funding nettuje się do zera przy long/short 50/50. Carry przekrojowy jest
  z założenia **strukturalnie niesymetryczny względem fundingu** (short tam, gdzie funding
  wysoki, long tam, gdzie niski), więc wyzwalacz z wniosku 33 jest tu aktywny: realny funding
  jest samą treścią hipotezy, nie poprawką kosztową.
- **H3** — realny koszt round-trip w modelu kosztów projektu: **0,0767%** (wejście maker,
  mieszanka wyjść). Użyty jako koszt podstawowy.

## Pytanie

Czy carry przekrojowy jest na tyle obiecujący i MIERZALNY, żeby wydać na niego wariant
(własną hipotezę z licznikiem od zera, pre-rejestracją i regułą STOP)?

## Konstrukcja (zamrożona)

**Uniwersum (bez błędu przeżywalności):** wszystkie symbole z archiwum `data.binance.vision`
kończące się na `USDT`, łącznie z wycofanymi. Wykluczone: kontrakty `TRADIFI_PERPETUAL`
(akcje/surowce — hipoteza dotyczy krypto) oraz stablecoiny jako aktywo bazowe
(`USDC`, `BUSD`, `TUSD`, `FDUSD`, `USDP`, `DAI`, `USDE`, `USD1`).

**Siatka okien:** nienakładające się okna 48h, start `t` = 2020-01-01 00:00 UTC + k·2 dni,
ostatnie okno kończy się ≤ 2026-07-01.

**Kwalifikacja symbolu w oknie `t` (wyłącznie dane sprzed `t`):**
- ≥ 30 dni historii funding przed `t`;
- istnieje świeca dzienna zamknięta dokładnie w `t` (cena wejścia).

**Uniwersum PODSTAWOWE — TOP50:** spośród zakwalifikowanych 50 symboli o największym obrocie
(suma `quote_volume` z 30 dni przed `t`). Powód: realnie handlowalny zbiór. **Wrażliwość —
ALL:** wszystkie zakwalifikowane.

**Sygnał (znany w `t`):** suma stawek funding z `[t − 48h, t)` — suma po CZASIE, bo część
symboli rozlicza się co 4h lub 1h, nie co 8h.

**Koszyki:** górny decyl sygnału → SHORT (otrzymuje dodatni funding), dolny decyl → LONG;
min. 2 symbole w koszyku; okno pominięte, gdy zakwalifikowanych < 20. Równe wagi.

**Wielkości per okno:**
- `F` = średnia z koszyka SHORT sumy funding w `[t, t+48h)` − średnia z koszyka LONG tej sumy
  (przychód z fundingu na jednostkę nominału każdej nogi);
- `C` = 2 nogi × `obrót` × `c_rt`, gdzie `obrót` = udział miejsc w koszyku zmienionych
  względem poprzedniego okna (pierwsze okno = 1), `c_rt` = **0,0767%** (podstawowy, H3);
  wrażliwość: `c_rt` = 0,14% (taker+poślizg na obu końcach) oraz `obrót` = 1;
- `R` = średni zwrot ceny koszyka LONG − średni zwrot ceny koszyka SHORT, zamknięcie→zamknięcie
  przez 48h; symbol wycofany w trakcie okna — zwrot do ostatniego dostępnego zamknięcia.

## Pomiary (zamrożone)

1. **Uniwersum i przeżywalność:** ile symboli, ile wycofanych, ile zakwalifikowanych okien;
   jaka część uniwersum istnieje TYLKO w archiwum (niewidoczna w bieżącej liście giełdy).
2. **Trwałość mechanizmu:** średnia po oknach korelacji rang (Spearman) sygnału z sumą funding
   w następnym oknie — czy wysoki funding dziś oznacza wysoki funding jutro.
3. **Ekonomia mechanizmu (górna granica):** `μ_net = średnia(F − C)` z CI95 (t-Studenta,
   błąd standardowy korygowany przez `N_eff` z autokorelacji szeregu `F − C`), mediana obok
   średniej. To jest zysk, GDYBY ruchy cen obu nóg się znosiły.
4. **Mierzalność pełnego testu:** `σ` = odchylenie standardowe szeregu `F − C + R` (bez
   drukowania jego średniej), `N_eff` z autokorelacji tego szeregu,
   `n_req = ((1,959964 + 0,841621) · σ / μ_net)²` okien (moc 80%, α = 5% dwustronnie).
   Porównanie `N_eff` dostępnych okien z `n_req`.
5. **Kontrola założenia z §17:** średnia korelacja zwrotów symboli w obrębie okna
   (przeciętna parowa korelacja w TOP50) i wynikająca z niej efektywna liczba niezależnych
   instrumentów `k_eff = k / (1 + (k − 1)·ρ̄)`.

## Kryteria decyzji (zamrożone przed uruchomieniem)

- **D1 — ekonomia:** dolny kraniec CI95 `μ_net` > 0 w uniwersum TOP50 przy koszcie podstawowym.
  Niespełnione ⇒ **NIEWYKONALNA ekonomicznie** (opłata nie pokrywa kosztów nawet przy
  założeniu, że ceny się znoszą — pełnego testu nie ma po co robić).
- **D2 — mierzalność:** `N_eff` dostępnych okien ≥ `n_req`. Niespełnione ⇒ **NIEMIERZALNA**
  (zasada 18: pełny test nie rozstrzygnąłby niczego).
- **Oba spełnione ⇒ WYKONALNA** — rekomendacja: postawić hipotezę **C** (carry przekrojowy)
  z licznikiem od zera, pre-rejestracją pełnego testu P&L i regułą STOP. **Decyzja bramkowa
  o jej uruchomieniu należy do użytkownika** (łamie zasadę 9 i wymaga nowej architektury).
- Wrażliwości (ALL, `c_rt` = 0,14%, `obrót` = 1) są raportowane opisowo i nie zmieniają werdyktu.

## Czego ta runda NIE liczy (warunek „0 wariantów")

- średniej `R` (zysku/straty z ruchu cen),
- średniej `F − C + R` (łącznego P&L), Sharpe'a ani krzywej kapitału.

`σ` i autokorelacja szeregu `F − C + R` są parametrami ubocznymi rachunku mocy (jak rozkład
etykiet w H2.0) — ich średnia jest liczona wewnątrz funkcji odchylenia standardowego, ale nie
jest zwracana ani drukowana. `F` jest liczone i raportowane, bo to mechanizm hipotezy (jak
„F realne" w H2.0).

## POPRAWKA 1 do pre-rejestracji (2026-09-22, PRZED uruchomieniem, osobny commit)

**Powód:** decyzja użytkownika w trakcie pobierania danych — „zatrzymaj pobieranie"
(pełne uniwersum 685 symboli wymagało ~1–1,5 h przy limicie API), a następnie „wybierz
20 symboli z największymi marketcapami na chwilę obecną, pomijając stablecoiny".
Żadna liczba sondy nie była policzona ani obejrzana przed tą poprawką (skrypt
`run_carry_probe_p2.py` nie był uruchomiony ani razu).

**Zmienione elementy (wszystko inne bez zmian, w tym kryteria D1/D2 i warunek „0 wariantów"):**

| element | pre-rejestracja | poprawka 1 |
|---|---|---|
| uniwersum | archiwum `data.binance.vision` (wszystkie, z wycofanymi) | **20 stałych symboli** — ranking kapitalizacji CoinGecko z 2026-09-22 (`coingecko_top100_2026-09-22.json`), pierwsze 20 pozycji mające perpetual USDT na Binance, bez stablecoinów (USDT, USDC, USDS, USDe, DAI, USD1) i tokenów złota (XAUT, PAXG); pominięte też pozycje bez perpetual (Figure Heloc, WBT, Rain, LEO) |
| symbole | — | BTC, ETH, BNB, XRP, SOL, TRX, ZEC, HYPE, DOGE, XMR, LINK, ADA, XLM, BCH, UNI, NEAR, AVAX, LTC, CC, HBAR (`*USDT`) |
| uniwersum podstawowe | TOP50 wg obrotu 30 d (w chwili `t`) | wszystkie zakwalifikowane z tych 20 (filtr TOP50 bezprzedmiotowy) |
| min. zakwalifikowanych w oknie | 20 | **10** (przy 20 stałych symbolach próg 20 oznaczałby okna dopiero od debiutu najmłodszego, CC) |
| koszyki | decyl, min. 2 | bez zmian ⇒ przy 10–20 symbolach **2 SHORT / 2 LONG** |
| wrażliwość ALL | wszystkie zakwalifikowane | **usunięta** (tożsama z podstawowym) |
| pomiar 1 | przeżywalność archiwum | zastąpiony opisem uniwersum stałego |

**Konsekwencja, którą czytelnik MUSI znać — wprowadzony BŁĄD PRZEŻYWALNOŚCI:** dobór według
DZISIEJSZEJ kapitalizacji to wybór zwycięzców z perspektywy 2026. Monety, które w latach
2020–2025 były duże i upadły (LUNA, FTT i podobne), są poza zbiorem, a z nimi najgorsze
epizody dla nogi LONG/SHORT. Pre-rejestracja celowo tego unikała; poprawka to wprowadza.
Skutek dla interpretacji: wynik opisuje **20 dzisiejszych największych monet**, a nie
„carry przekrojowy" w ogóle. **Kierunek obciążenia:** dla mechanizmu `F` (funding) — niejasny;
dla rozrzutu `F − C + R` — prawdopodobnie ZANIŻONY (brak upadłości), więc `n_req` może
wyjść optymistycznie. Werdykt WYKONALNA na tej próbie wymagałby potwierdzenia na uniwersum
bez błędu przeżywalności przed jakimkolwiek wariantem hipotezy C.

**Druga konsekwencja:** 20 symboli to dolna granica „~20+ instrumentów" z H2.0 — a koszyk
2 + 2 to cienka dywersyfikacja. Pomiar 5 (`k_eff`) pokaże, ile z tych 20 jest faktycznie
niezależnych.

## Ograniczenia znane z góry

- Koszt 0,0767% zmierzono dla BTC; altcoiny mają szersze spready — koszt realny wyższy
  (stąd wrażliwość 0,14%). Nie modelujemy wpływu na rynek przy małych monetach.
- Świece dzienne: cena wejścia/wyjścia z zamknięcia dnia, bez uwzględnienia momentu rozliczenia.
- Stablecoiny wykluczone listą stałą — rzadkie przypadki spoza listy mogą przeciec.

---

## Wynik

**Uniwersum (pomiar 1):** 20/20 symboli z danymi. 16 ma historię od 2020, HBAR od 2021-03,
HYPE od 2025-05, CC od 2025-10. Okien 48h: **1 186**, ważnych **1 161** (25 pominiętych — styczeń
i luty 2020, zanim 10 symboli miało 30 dni historii). Zakwalifikowanych w oknie: mediana 18.
Koszyki: zawsze 2 SHORT / 2 LONG.

| pomiar | TOP20, koszt bazowy 0,0767% (**PODSTAWOWY**) | koszt taker 0,14% | obrót = 1 |
|---|---|---|---|
| F — funding otrzymany na 48h (średnia / mediana) | **0,172% / 0,104%** | tak samo | tak samo |
| C — koszt na 48h | 0,075% | 0,137% | 0,153% |
| **μ_net = F − C** (średnia) | **0,097%**, CI95 **[0,051%; 0,143%]** | 0,035%, CI [−0,010%; 0,079%] | 0,019%, CI [−0,029%; 0,066%] |
| μ_net (mediana) | 0,033% | −0,021% | −0,050% |
| okna z F − C > 0 | 65,6% | 44,4% | 33,7% |
| σ(F − C + R) — rozrzut łącznego wyniku okna | **5,56%** | 5,56% | 5,55% |
| n_req — okna potrzebne do rozstrzygnięcia (moc 80%) | **25 850** | 201 371 | 696 308 |
| dostępne (N_eff) / potrzebne | **1 161 / 25 850 = 0,045×** | 0,006× | 0,002× |

**Trwałość mechanizmu (pomiar 2):** korelacja rang sygnału z fundingiem w następnym oknie
**0,563** — wysoki funding dziś zwykle oznacza wysoki funding przez następne 48h. Obrót koszyków:
~50% miejsc na okno.

**Kontrola założenia z `STATUS.md` §17 (pomiar 5):** przeciętna korelacja zwrotów 48h między
monetami **0,470** ⇒ 18 monet zachowuje się jak **k_eff = 2,0** niezależnych instrumentów,
koszyk 2-elementowy jak 1,36. **Założenie „20 instrumentów = 20× próby" (160 660 transakcji)
jest obalone** — przekrój NIE mnoży liczby niezależnych obserwacji, bo krypto chodzi razem.

**Kryteria:** D1 (ci_low μ_net > 0) — **SPEŁNIONE** (0,051%). D2 (N_eff ≥ n_req) —
**NIESPEŁNIONE** (1 161 wobec 25 850). **Werdykt: NIEMIERZALNA.**

### Opisowo, post hoc (NIE zmienia werdyktu, nie był pre-rejestrowany)

F − C (koszt bazowy) per rok — średnia / mediana: 2020 **0,154% / 0,077%**, 2021 0,164% / 0,081%,
2022 0,110% / 0,029%, 2023 **0,051% / 0,013%**, 2024 0,060% / 0,028%, 2025 0,076% / 0,018%,
2026 (pół roku) 0,044% / 0,029%. Mechanizm jest dodatni w każdym roku, ale **słabnie**: od 2023
jest 2–3× mniejszy niż w latach 2020–21, a mediana leży blisko zera.

## Walidacja (zasada 16a)

**A3 — przeliczenie drugą drogą:** `F` dla 6 losowo wybranych okien (2023-10 … 2026-02)
policzone od zera filtrami pandas na surowych parquetach (bez żadnej funkcji z
`backtest/carry_probe.py`): **zgodność co do 5. miejsca po przecinku** we wszystkich sześciu,
identyczna liczba zakwalifikowanych symboli i identyczny skład koszyków. `μ_net` z zapisanego
szeregu: 0,0968% (jak w raporcie). Kontrola rzędu wielkości CI: naiwne (bez N_eff) [0,076%;
0,118%] — węższe niż raportowane, zgodnie z oczekiwaniem (N_eff = 246 < n = 1 161).

**A2 — kogo NIE ma w zbiorze:**
1. **Monet, które upadły** (LUNA, FTT, …) — uniwersum dobrane wg DZISIEJSZEJ kapitalizacji
   (poprawka 1). Rozrzut σ jest więc raczej ZANIŻONY, czyli prawdziwe n_req jest raczej WIĘKSZE
   niż 25 850 — obciążenie działa na korzyść werdyktu NIEMIERZALNA, nie przeciw.
2. **Mniejszych monet** — tam funding bywa skrajny (większe F), ale i koszty, i rozrzut większe.
   Częściowo pobrane dane ~270 symboli leżą w `data/raw/universe/` (pobieranie przerwane decyzją
   użytkownika) — NIE zostały użyte.
3. **25 okien z początku 2020** (za mało symboli z historią) — 2% okien, bez wpływu na werdykt.

**Rozsądek:** F 0,172% na 48h ≈ 31% rocznie brutto spreadu funding między koszykami — wysoko,
ale mediana (0,104%) i rozkład per rok pokazują, że średnią ciągną epizody hossy 2020–21
(znany reżim skrajnego fundingu). σ 5,6% na 48h dla różnicy dwóch koszyków 2-elementowych przy
korelacji 0,47 — zgodne z rzędem zmienności altcoinów.

**A4 — czerwone flagi:** brak „idealnego potwierdzenia" — D1 przechodzi, D2 przepada o rząd
wielkości. Werdykt nie jest graniczny: żeby D2 przeszło, μ_net musiałoby wynosić ≥ 0,46% na
okno (4,7× więcej niż zmierzone) albo σ spaść ~4,7×.

**Przegląd diffu przed merge (zasada 16c):** gałąź `worktree-p2-carry-porzadki` — korektność
(granice okien bez podglądania, wycofane monety nie znikają z okna, sumy funding po czasie przy
siatkach 1h/4h/8h — HYPE 4h), edge-case'y (pominięte okna resetują koszyki, N_eff przycięte do
[1, n], błędy giełdy per symbol nie przerywają pobierania, błędy sieci są ponawiane), testy
(425/425, w tym hypothesis na przeciek + kontrola, że detektor łapie okno przyszłe), czytelność
(ruff + black czyste). **Werdykt: gotowe do scalenia, bez uwag blokujących.**

**Werdykt walidacji: CAVEATS.**
1. Uniwersum z błędem przeżywalności (poprawka 1) — wynik dotyczy 20 dzisiejszych największych
   monet; wpływ: werdykt NIEMIERZALNA raczej wzmocniony, D1 (ekonomia) może być zawyżone.
2. D1 zależy od kosztu: przy taker 0,14% albo pełnym obrocie CI μ_net obejmuje zero — dodatnia
   ekonomia mechanizmu wymaga wykonania zleceniami limit.
3. Liczby z sekcji „post hoc" są opisowe i nie uczestniczą w decyzji.

## Co na plus (+)

- **Pytanie rozstrzygnięte za 0 wariantów, zanim ktokolwiek zbudował silnik portfelowy.**
  Ta sama rola co H2.0 i P1: rachunek wykonalności oszczędził projekt, którego wynik i tak
  nie mógłby niczego pokazać.
- **Obalone założenie, na którym stał priorytet 4A w `STATUS.md` §17** („przekrój mnoży próbę").
  Zmierzone: 18 monet ≈ 2 niezależne. Bez tego pomiaru następna runda wystartowałaby z rachunkiem
  mocy zawyżonym ~10×.
- **Mechanizm jest prawdziwy i trwały** (D1, korelacja rang 0,56): funding przekrojowy płaci
  więcej, niż kosztuje handel limitami — to pierwszy w projekcie DODATNI i istotny człon ekonomii.
  Nie wystarcza, ale istnieje.
- **Niezależne przeliczenie zgodne co do 5. miejsca** i test przecieku (hypothesis) z kontrolą,
  że detektor łapie okno przyszłe.
- Infrastruktura wielokrotnego użytku: pobieranie uniwersum bez błędu przeżywalności
  (`data/fetch_universe.py`), gotowe do pełnego uniwersum.

## Co na minus (−)

- **Poprawka 1 wprowadziła błąd przeżywalności**, którego pre-rejestracja celowo unikała.
  Zapisany jawnie przed uruchomieniem; kierunek wpływu na werdykt — korzystny dla jego trwałości.
- **Koszt 0,0767% zmierzono dla BTC** — dla XMR, ZEC, CC realny koszt jest wyższy. Wrażliwość
  pokazuje, że przy 0,14% dodatnia ekonomia znika.
- **Świece dzienne** — cena z zamknięcia dnia, bez modelowania chwili rozliczenia i poślizgu
  przy rebalansie wielu monet naraz.
- Koszyk 2 + 2 to cienka dywersyfikacja; pełne uniwersum dałoby większe koszyki, ale przy
  k_eff ≈ 2 niewiele zmniejszyłoby σ.

## Wniosek

Prostym językiem (zasada 17).

**Pomysł był taki:** zamiast zgadywać, dokąd pójdzie cena, zarabiać na opłacie, którą na giełdzie
płacą sobie nawzajem gracze z kontraktami (funding). Bierzemy pozycję krótką na monetach, gdzie ta
opłata jest najwyższa (więc nam ją płacą), i długą tam, gdzie najniższa. Ruchy cen obu stron
miały się mniej więcej znosić.

**Co się okazało:**

1. **Sama opłata jest opłacalna.** Przez 6,5 roku na 20 największych monetach dawała średnio
   **0,17% na każde dwa dni**, a handel kosztował **0,075%**. Zostaje ~0,1% na dwa dni i z 95%
   pewnością jest to więcej niż zero. Ale to się kurczy: w latach 2020–21 było 2–3× więcej niż
   od 2023. I znika całkiem, jeśli handlować droższymi zleceniami rynkowymi.
2. **Ruchy cen się NIE znoszą.** Różnica między koszykami waha się o ±5,6% na dwa dni — to jest
   **57 razy więcej** niż zarobek z opłaty. Zysk z opłaty tonie w tym szumie.
3. **Żeby uczciwie sprawdzić, czy całość zarabia, trzeba by ~25 850 okien dwudniowych — czyli
   około 140 lat danych.** Mamy 6,5 roku (1 161 okien) — **4,5% potrzebnej próby**.
4. **Dołożenie większej liczby monet tego nie naprawia.** Te 18 monet zachowuje się jak **dwie**
   niezależne, bo kryptowaluty chodzą razem. Wcześniejszy plan zakładał, że 20 monet to 20 razy
   więcej danych — to było błędne założenie.

**Wniosek dla decyzji:** carry przekrojowy na kontraktach perpetual jest **nie do zweryfikowania**
tą metodą na dostępnej historii. Nie dlatego, że nie działa — mechanizm istnieje — tylko dlatego,
że ryzyko cenowe jest za duże w stosunku do zarobku, żeby wynik dało się odróżnić od szczęścia.

## Rekomendacja

1. **Nie stawiać hipotezy C (carry przekrojowy na samych perpetualach).** Werdykt NIEMIERZALNA
   ⇒ zasada 18: runda pełnego testu nie startuje.
2. **Skorygować `STATUS.md` §17 (4A):** rachunek „20 instrumentów = 160 660 transakcji" jest
   obalony (k_eff ≈ 2). 4A traci status „jedynej ścieżki z wykonalną arytmetyką".
3. **Jedyny sposób, żeby ten sam mechanizm STAŁ SIĘ mierzalny, to usunięcie szumu cenowego** —
   zabezpieczenie każdej pozycji przeciwną pozycją na rynku spot tej samej monety („cash-and-carry":
   kupujesz monetę, sprzedajesz kontrakt, zbierasz opłatę bez ryzyka kierunku). Wtedy σ spada
   o rzędy wielkości. **To jednak jest inny produkt** (spot + perpetual, depozyt na dwóch rynkach,
   inny model kosztów), dobrze znany i szeroko stosowany — zwrot jest bliższy oprocentowaniu niż
   przewadze. **Decyzja bramkowa użytkownika**, nie kolejna runda.
4. **Nie dokańczać pobierania pełnego uniwersum pod P2** — przy k_eff ≈ 2 większe koszyki nie
   zmienią werdyktu o rząd wielkości, a to jest brakujący rząd.
