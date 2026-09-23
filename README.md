# CLAS-5 — Compliance-Led Agentic Trading System

Regime-gated system tradingowy dla BTC/ETH/SOL/BNB perpetual futures, budowany wokół jednej
zasady: **żadna architektura nie powstaje, dopóki nie ma dowodu na edge statystyczny.**

## Dlaczego ten projekt wygląda inaczej niż typowy "bot tradingowy"

Pierwotna koncepcja zakładała pełną, wieloagentową architekturę (5 agentów AI, dashboard, Docker,
Compliance Gate) budowaną od razu, w całości. Zmieniliśmy kolejność: nic z tamtej wizji nie
powstaje, dopóki minimalny, w pełni audytowalny system nie udowodni empirycznie, że hipoteza
tradingowa ma przewagę statystyczną po kosztach transakcyjnych. Architektura bez potwierdzonego
edge'u to tylko dopracowany system do tracenia pieniędzy.

Pełne uzasadnienie tej decyzji i wszystkich pozostałych: [`docs/rag/01_hipoteza_i_architektura.md`](docs/rag/01_hipoteza_i_architektura.md).

## Status

### 🔴 FAZA 0 ZAMKNIĘTA WYNIKIEM NEGATYWNYM (decyzja użytkownika, 2026-09-22 — [Z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md))

Hipoteza, dla której Faza 0 powstała — **regime-gated momentum/mean-reversion na cechach
OHLCV** — nie ma edge'u kierunkowego wystarczającego do pokrycia kosztów transakcyjnych.

To **dowód braku, a nie brak dowodu**:

| | |
|---|---|
| pooled trafność kierunku (3 najczystsze pomiary, n = 7 687) | **50,27%**, CI95 [49,15%; **51,38%**], z = +0,47 |
| najniższy próg opłacalności zmierzony w projekcie | **52,69%** |
| górny kraniec CI vs ten próg | **−1,30 pp — przedział ufności nie sięga progu** |
| moc statystyczna | **2,8×** próby wymaganej do wykrycia p = 52,69% |

Wąskie gardło okazało się **informacyjne, nie inżynieryjne**: projekt naprawił po kolei
geometrię wypłaty, model kosztów, spójność bramki z horyzontem etykiety, jakość danych,
przeciek w treningu i metodologię pomiaru — i po **każdej** z tych napraw trafność pozostawała
przy 50%. Wszystkie 10 cech to transformacje tej samej informacji: ceny i wolumenu.

**Czego Faza 0 NIE wykazała** (czytać razem z powyższym): momentum pozostaje
**nieprzetestowane** (bramka reżimu zagłodziła próbę do 0,53% świec), ETH/SOL/BNB — **zero
testów**, funding rate jako sygnał — **nigdy nie zaimplementowany**, ekonomia dźwigni —
**niezbadana**. Pełna lista: [Z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md).

Budżet zużyty (stan na Z10): **10 wariantów**, 17 rund, 2 uruchomione reguły STOP.
Surowe wyniki każdej rundy: [`runs/`](runs/INDEX.md) (tabela + wnioski skumulowane).
Backlog i zasady pracy: [`STATUS.md`](STATUS.md).

### 🔴 Po Fazie 0: wszystko, co da się zmierzyć, zmierzone (M1 + P1 + F1, 2026-09-22)

Po zamknięciu Fazy 0 sprawdziliśmy jeszcze dwie rzeczy, których Faza 0 nie zmierzyła, tym razem
na próbie ok. 8 000 transakcji (wystarczająco dużej, żeby rozstrzygnąć):

| co | trafność | próg opłacalności | wynik |
|---|---|---|---|
| momentum — „co rośnie, rośnie dalej” ([M1](runs/2026-09-22_m1-momentum-bez-bramki/README.md)) | 49,74% | 52,94% | brak przewagi |
| funding — opłata za trzymanie pozycji, jedyna informacja spoza wykresu ceny ([F1](runs/2026-09-22_f1-funding-zmierzony/README.md)) | 50,34% | 52,94% | brak przewagi |
| dane o pozycjach graczy ([P1](runs/2026-09-22_p1-sonda-zrodel-danych/README.md)) | — | — | ~~nie da się zmierzyć: giełda daje tylko 30 dni historii~~ **sprostowane w [P3](runs/2026-09-23_p3-sonda-zrodel-ii/README.md): archiwum plików giełdy ma 6 lat historii — da się zmierzyć, pomiar w przygotowaniu** |

**Co to znaczy:** przewidywanie KIERUNKU ceny BTC na tych danych nie daje przewagi — w każdym
wariancie model trafia jak rzut monetą. Otwarte zostały tylko kierunki, które zmieniają samo
założenie projektu (`STATUS.md` §17, ETAP 4). Pierwszy z nich — **carry przekrojowy**
(zarabianie na samej opłacie funding na wielu parach naraz, bez zgadywania kierunku) — został
sprawdzony sondą [P2](runs/2026-09-22_p2-sonda-carry-przekrojowy/README.md): **sama opłata
pokrywa koszty, ale ruchy cen są 57× większe od zarobku, więc uczciwy test wymagałby ~140 lat
danych. Niemierzalne.** Jedyną drogą zostaje wariant z zabezpieczeniem na rynku spot
(cash-and-carry) — inny produkt, decyzja użytkownika.

Stan testów: **773/773** (2026-09-23).

### ⚪ Wykonanie „po konkretnej cenie" — W1 (2026-09-23): backtest dopasowany do handlu na żywo

Użytkownik ustalił zasadę, która obowiązuje też na żywo: pozycje otwiera się i zamyka **po
konkretnej cenie** (zlecenie oczekujące na poziomie), nie „po cenie zamknięcia świecy". Backtest
zakładał dotąd, że zlecenie po cenie zamknięcia zawsze się wypełni. [W1](runs/2026-09-23_w1-wykonanie-po-cenie/README.md)
dołożyło symulację wypełnień na ścieżce cen i sprawdziło trzy sposoby wejścia:

| sposób wejścia | ile sygnałów wchodzi | trafność | próg opłacalności | pieniądze na transakcji |
|---|---|---|---|---|
| limit po cenie zamknięcia | 99,4 % | 50,11 % | 52,96 % | strata (jak dotąd) |
| limit na cofnięciu o pół ATR | 35,5 % | **53,15 %** | 52,81 % | **strata** (t = −3,9) |
| zlecenie na wybiciu | 47,5 % | 46,13 % | 54,83 % | strata, największa |

**Co to znaczy:** dotychczasowe wyniki nie były zawyżone przez założenie wypełnienia (99,4 % to
prawie „zawsze"). Wejście na cofnięciu **wygląda** lepiej — pierwszy raz trafność ponad progiem —
ale gdy zsumować pieniądze, jest stratą: wygrane są małe (pozycja zamykana po czasie tuż nad
wejściem), a przegrane pełne. **Więcej wygranych ≠ więcej pieniędzy** — od teraz każdy werdykt
wymaga i trafności ponad progiem, i dodatniego zwrotu netto.

### ⚪ Nowy cel modelu — N1 (2026-09-23): połowa zysku wcześniej i stop na wejście nie zmieniają pieniędzy

Użytkownik prowadzi pozycję tak: przy +5 % depozytu (dźwignia 3× → +1,67 % ceny) zamyka połowę
i przesuwa stop na cenę wejścia; reszta jedzie do dotychczasowej bariery zysku; limit 12 h. Od tej
rundy obowiązuje też zasada: **dane tylko od 2021 roku**. [N1](runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md)
sprawdziło ten schemat na tych samych sygnałach i wejściach co zwykłe wyjście:

| | trafność | pieniądze na transakcji | różnica wobec zwykłego wyjścia (te same transakcje) |
|---|---|---|---|
| zwykłe wyjście (kontrola, dane od 2021) | 49,6 % | −0,107 % | — |
| połowa zysku wcześniej + stop na wejście | **53,3 %** | **−0,094 %** (strata, t = −4,1) | **+0,007 %**, przedział [−0,009; +0,024] — zero |

**Co to znaczy:** trafność rośnie, bo częściej „coś się wygrywa", ale wygrane stają się mniejsze,
a straty zostają pełne — żeby wyjść na zero, trzeba by trafiać w 57 %, nie 53 %. **Prowadzenie
pozycji nie tworzy informacji** — gdy model nie zna kierunku, żaden schemat wyjść tego nie
naprawi. Uwaga przy okazji: na danych od 2021 model radzi sobie gorzej niż na pełnej historii.

### ⚪ Formacje świecowe — A1 (2026-09-23): podręcznik wskazuje kierunek odwrotny

Na życzenie użytkownika sprawdziliśmy klasyczną analizę techniczną: sześć formacji świecowych
z podręcznika (objęcie, młot, spadająca gwiazda, gwiazdy poranna i wieczorna, trójka), liczonych
gotową biblioteką bez żadnych parametrów do dobrania. [A1](runs/2026-09-23_a1-formacje-swiecowe/README.md)
użyło ich na dwa sposoby, na tych samych świecach co dotychczasowy model:

| | trafność | pieniądze na transakcji | uwaga |
|---|---|---|---|
| model bez formacji (kontrola) | 49,6 % | −0,107 % | jak w N1 |
| **reguła z formacji** (bycza → kup, niedźwiedzia → sprzedaj) | **46,4 %** [44,4; 48,3] | **−0,177 %** [−0,245; −0,109] | cały przedział poniżej rzutu monetą |
| model + formacje jako dodatkowa cecha | 49,4 % | −0,113 % | różnica wobec kontroli −0,001 % [−0,012; +0,010] — zero |

**Co to znaczy:** formacje nie tylko nie pomagają — czytane po podręcznikowemu wskazują częściej
zły kierunek. Winne jest objęcie (84 % sygnałów): duża świeca w górę jest na BTC 4h częściej
końcem ruchu niż jego początkiem. **Odwrócenie reguły nie jest wnioskiem** — to pomysł
wymyślony po wyniku, a rachunek daje mu ok. +0,01 % na transakcję, czyli nic. Rodzina formacji
świecowych zamknięta (2/2). Co dalej z analizą techniczną — decyzja użytkownika.

### ⚪ Reszta analizy technicznej — A2 (2026-09-23): nic nie zarabia, kierunek zamknięty

Na zlecenie użytkownika sprawdziliśmy pozostałe narzędzia z podręcznika, każde jako
deterministyczną regułę z parametrami ze skilla (bez dobierania): strukturę trendu, wybicie
z zakresu, podwójny szczyt/dno, głowę z ramionami, przecięcie średnich, przełamanie linii trendu,
zniesienia Fibonacciego, strefy wsparcia i oporu. [A2](runs/2026-09-23_a2-rodziny-at/README.md):

| reguła | trafność | pieniądze na transakcji | werdykt |
|---|---|---|---|
| struktura trendu („graj z trendem") | **48,2 %** [47,0; 49,4] | −0,127 % | NEGATYWNY |
| wsparcie/opór | 49,9 % [48,9; 50,9] | −0,080 % | NEGATYWNY |
| zniesienie Fibonacciego | 51,5 % [49,4; 53,6] | −0,041 % [−0,110; +0,028] | nierozstrzygnięty (za mało sygnałów) |
| zdarzenia AT razem (wybicie, formacje, średnie, linia trendu) | 48,3 % [46,2; 50,5] | −0,103 % [−0,182; −0,024] | nierozstrzygnięty (próba o 10 % za mała na „dowód braku") |
| model + wszystkie 10 cech AT | 49,6 % | −0,099 % | NEGATYWNY; różnica wobec modelu bez AT +0,005 % [−0,055; +0,066] |

**Co to znaczy:** żadne z tych narzędzi nie wskazuje pozycji, które zarabiają. Rzadkie formacje
(np. głowa z ramionami: 86 przypadków w 5,5 roku) były za rzadkie, żeby je mierzyć osobno, więc
policzyliśmy je jako grupę. „Graj z trendem" jest na BTC 4h konsekwentnie gorsze od rzutu monetą.
Analiza techniczna na BTC 4h jest zamknięta jako kierunek (7 wariantów w trzech rundach).

### 🟢 Cash-and-carry z hedgem spot — C1 (2026-09-23): pierwszy dodatni wynik, ale to odsetki, nie prognoza

Co 8 godzin posiadacze pozycji na wzrost na kontrakcie wieczystym płacą opłatę („funding") tym,
którzy mają pozycję na spadek — na BTC od 2021 w 85 % rozliczeń. Kupując tyle samo BTC na
zwykłym rynku spot, zdejmujemy ryzyko kierunku i zostaje sama opłata. [C1](runs/2026-09-23_c1-cash-and-carry/README.md)
zmierzyło to na 5,5 roku:

| | rocznie na zaangażowanym kapitale | uwaga |
|---|---|---|
| zawsze w pozycji | **+5,4 %** [3,5; 7,4] | połowa zysku z 2021 (15 %); 2022–2026: 0,4–6 %; ostatnie 3 lata 3,6 % |
| tylko gdy ostatnia opłata dodatnia | −9,3 % | 875 przełączeń, koszty 166 % — przegrywa z arytmetyką |

**Co to znaczy:** to działa, ale jest czymś innym niż wszystko wcześniej: nie przewiduje rynku,
tylko pobiera opłatę za dostarczanie dźwigni. Wynik w ostatnich latach jest porównywalny
z bezpieczną lokatą w dolarze, a dochodzą ryzyka, których pomiar nie obejmuje: krótka pozycja
wymaga depozytu, a BTC potrafi urosnąć o 90 % w miesiąc; pieniądze leżą na giełdzie. **Czy z tego
budować produkt — to decyzja użytkownika**, nie kolejna runda.

### ⚪ Premia rebalansowa koszyka — R1 (2026-09-23): codzienne wyrównywanie nie zarabia

Drugi „inny cel niż kierunek": koszyk 20 największych (po obrocie) kryptowalut w równych
częściach, wyrównywany codziennie, porównany z tym samym koszykiem trzymanym przez miesiąc.
Podręcznik obiecuje premię z „handlu zmiennością" (sprzedaj to, co urosło, dokup to, co spadło).
[R1](runs/2026-09-23_r1-premia-rebalansowa/README.md): **−3,6 % rocznie**, przedział od −9,5 %
do +2,4 %; przez 5,4 roku wersja wyrównywana skończyła o 12 % niżej. Premia obiecywana przez
podręcznik (6–11 % rocznie) leży poza przedziałem. **Co to znaczy:** w krypto ruchy względne
trwają — zwycięzcy dalej wygrywają — więc wyrównywanie sprzedaje ich za wcześnie. Zamknięte (1/1).

### 🟢 Nowe dane podłączone — P3 (2026-09-23): pozycjonowanie ma 6 lat historii, nie 30 dni

Na prośbę o „podpięcie dodatkowych danych" sprawdziliśmy, co jeszcze da się pobrać za darmo
i z długą historią. [P3](runs/2026-09-23_p3-sonda-zrodel-ii/README.md): **osiem źródeł**, w tym
dane o tym, ilu graczy stoi po której stronie i ile mają otwartych pozycji — giełda publikuje
je w archiwum plików **co 5 minut od września 2020**, choć jej API oddaje tylko 30 dni
(sonda P1 sprawdziła tylko API). Do tego: funding kontraktu rozliczanego w bitcoinie, ceny 24
kontraktów kwartalnych, zmienność z opcji (DVOL), 14 wskaźników z łańcucha bitcoina, indeks
strachu i chciwości, stopy amerykańskie, ceny z Coinbase. **Co to znaczy:** wraca do gry
kierunek, który był skreślony jako „nie da się zmierzyć". Sonda niczego nie mierzy — każde
źródło dostanie własną rundę z rachunkiem mocy.

### 🟢 Produkt carry policzony do końca — D1 (2026-09-23): sens ma tylko wersja w bitcoinie

Cztery pytania, które zostawiło C1. [D1](runs/2026-09-23_d1-produkt-carry/README.md):
**depozyt** — przy depozycie równym pozycji i dopłacie raz w miesiącu przez 5,5 roku nie
byłoby ani jednej likwidacji, ale ta wersja od 2022 nie wychodzi ponad lokatę w dolarze.
**Wersja rozliczana w bitcoinie (COIN-M)** nie ma czego likwidować (wartość pozycji w dolarach
jest stała) i potrzebuje kapitału 1× zamiast 2×: **+9,1 % rocznie** [5,9; 12,3], a od 2022
średnio o ok. 2 punkty procentowe ponad bony skarbowe (w jednym roku +7, w dwóch poniżej).
**Kontrakt kwartalny** zamyka stopę z góry, ale nie daje jej więcej. **Co to znaczy:** jeśli
produkt, to COIN-M; czy w ogóle — to decyzja użytkownika (realny kapitał, ryzyko giełdy).

### 🟡 Momentum przekrojowe — X1 (2026-09-23): +22 % rocznie, ale jeszcze nie dowód

Hipoteza odwrotna do R1: co tydzień kupujemy pięć monet z najlepszym zwrotem z ostatnich
4 tygodni i gramy na spadek pięciu z najgorszym (koszyk 20 największych, koszty i funding
wliczone). [X1](runs/2026-09-23_x1-momentum-przekrojowe/README.md): **+22 % rocznie po
kosztach**, przedział od −5 % do +49 %; zysk w każdym z sześciu lat, niezależny od kierunku
bitcoina, nie z kilku dni — ale rok 2025 daje połowę całości, a przedział obejmuje zero.
**Co to znaczy:** pierwszy zakład o kierunek w tym projekcie, który wygląda obiecująco, ale przy
5,4 roku danych nie da się go odróżnić od szczęścia. Rozstrzygnięcie wymaga większej próby
(szerszy koszyk albo pomiar na żywo), nie kolejnego wariantu — to decyzja użytkownika.

### 🔴 Pozycjonowanie jako cecha modelu — O1 (2026-09-23): informacja jest, ale za słaba

Pierwsze użycie nowych danych z P3: model 4h dostał jedną liczbę spoza wykresu — o ile zmienił
się open interest (liczba otwartych pozycji z dźwignią) przez 24 h.
[O1](runs/2026-09-23_o1-pozycjonowanie/README.md): trafność 50,25 % zamiast 49,58 %, strata na
transakcję −0,074 % zamiast −0,107 %; model zmienia decyzję w co piątej transakcji. **Co to
znaczy:** to pierwsza dodatkowa cecha w historii projektu, która w ogóle porusza model — ale
próg opłacalności to 53,1 %, a górny kraniec przedziału to 51,4 %. Wynik negatywny; pozostałe
kolumny tych danych (proporcje long/short, przepływ taker) czekają na decyzję użytkownika.

### 🔴 Trzy kolejne źródła spoza wykresu — L1, V1, G1 (2026-09-23): trzy razy negatywnie

Na prośbę „wykonaj po kolei 3 warianty" model 4h dostał kolejno: ile bitcoinów przypłynęło
na giełdy w tygodniu (dane z łańcucha), „cenę strachu" z rynku opcji minus faktyczną
zmienność, i indeks strachu i chciwości. Wszystkie trzy pre-rejestrowane naraz, każde jako
osobna seria. [L1](runs/2026-09-23_l1-onchain-podaz/README.md),
[V1](runs/2026-09-23_v1-premia-zmiennosci/README.md),
[G1](runs/2026-09-23_g1-strach-chciwosc/README.md): trafność 49,8 %, 50,5 % i 49,9 % przy
progu ~53,5 %; różnice wobec modelu bez cechy to zero w granicach błędu. **Co to znaczy:**
po pięciu źródłach spoza wykresu (funding, pozycjonowanie, on-chain, opcje, sentyment) wiemy,
że dokładanie pojedynczych cech do modelu 4h nie wyprowadzi go ponad koszty. Jedyny obiecujący
ślad tego dnia to momentum przekrojowe (X1), które jest inną konstrukcją.

### 🟡 Momentum na szerszym koszyku — X2 (2026-09-23): słabiej, i X1 zależało od kalendarza

Ta sama reguła co w X1, ale na 50 monetach zamiast 20 (większa próba).
[X2](runs/2026-09-23_x2-momentum-top50/README.md): **+16 % rocznie**, przedział od −12 do +44 %;
sygnał w ogóle nie porządkuje 50 monet (IC równe zeru), połowa zysku pochodzi z 33 dni,
rok 2022 stracił 20 %. Odkrycie uboczne: reguła z X1 policzona na kalendarzu z rebalansami
w inne dni tygodnia daje +9 % zamiast +22 % rocznie. **Co to znaczy:** wynik X1 był w dużej
części dziełem przypadku (kalendarza), momentum przekrojowe w krypto zostaje hipotezą ze
słabym poparciem. Kolejne warianty na tych samych danych nic nie rozstrzygną; jedyna droga
to pomiar na żywo przez co najmniej dwa lata.

### ⚪ Inne horyzonty — Y1 (1h) i Y2 (1d), 2026-09-23: zmiana interwału nie pomaga

Ten sam model co zawsze, tylko na świecach godzinowych i dziennych (decyzja użytkownika).
[Y1](runs/2026-09-23_y1-horyzont-1h/README.md): na 1h trafność **48,3 %** przy progu 54 %,
23 tysiące transakcji, przedział niepewności w całości poniżej rzutu monetą, straty w każdym
z sześciu lat — najbardziej rozstrzygnięty wynik negatywny w projekcie.
[Y2](runs/2026-09-23_y2-horyzont-1d/README.md): na 1d trafność **50,2 %** przy progu 51,7 %,
ale tylko 978 transakcji, więc niepewność (±3 punkty) nie pozwala powiedzieć „na pewno nie" —
nierozstrzygnięte, dokładnie jak policzono przed uruchomieniem. **Co to znaczy:** model
kontrolny zmierzono na trzech interwałach (1h / 4h / 1d) i na każdym trafia 48–50 %.
Krótszy horyzont podnosi koszty i nie wzmacnia sygnału; dłuższy obniża koszty, ale zostawia
za mało danych. Zmiana horyzontu tego modelu jest zamknięta.

### ⚪ Hipoteza H2 (funding) — ZAMKNIĘTA bez rozstrzygnięcia (2026-09-22)

Pierwsze w projekcie źródło informacji **spoza OHLCV**. Licznik wyczerpany (**1/1**), reguła STOP
zamknęła serię.

[H2.0](runs/2026-09-22_h2.0-funding-wykonalnosc/README.md) pobrał dane (7 457 rekordów, 6,8 roku,
zero dziur) i **rachunkiem mocy odrzucił 2 z 3 sformułowań za 0 wariantów**.
[H3](runs/2026-09-22_h3-noga-timeout-pasmo/README.md) sprostował próg (53,12% → **52,69%**)
i naprawił usterkę w liczeniu kosztów.
[H2.1](runs/2026-09-22_h2.1-funding-jako-cecha/README.md) — jedyny eksperyment — wyszedł
**NIEROZSTRZYGNIĘTY**: `n = 98` wobec wymaganych 1 000.

**Dlaczego:** zdjęcie bramki reżimu miało powiększyć próbę i powiększyło liczbę ocenianych świec
czterokrotnie (**zero pominiętych foldów** wobec 22 z 85 w S1). Ale przy okazji podniosło udział
klasy „nic się nie wydarzyło” z **60,83% na 66,58%** — a model uczy się przewidywać właśnie ją
i **przestaje handlować w 99,3% przypadków**.

**⚠ To, co runda rzekomo pokazała, zostało WYCOFANE 2026-09-22** (patrz kamień milowy F1): ~~funding potroił liczbę decyzji modelu (35 → 98), czyli został~~
uznany za informacyjny. O trafności tych decyzji nie mówi nic — próbka jest za mała.

*(Historyczne: po H2.1 następnym krokiem był wymiar przekrojowy. Funding jako cecha został
potem zmierzony osobno w F1 — patrz sekcja wyżej.)*

Pełny, aktualny status: [`STATUS.md`](STATUS.md).

## Kamienie milowe

> Aktualizowane przy każdym zamkniętym kamieniu (CLAUDE.md, zasada 15). Pełne wyniki — linki.

| Kamień | Data | Wynik (jedno zdanie) | Szczegóły |
|---|---|---|---|
| Commit 6 — checkpoint go/no-go | 2026-08-01 | **NO-GO** na BTC 5m (2025-07→2026-07); tylko 1/40 foldów policzalnych | `STATUS.md` §5 |
| C2c — kill-switch | 2026-08-01 | Deadlock naprawiony (cooldown/re-arm); NO-GO potwierdzone na 23/40 foldów — werdykt uwiarygodniony | `STATUS.md` §5 |
| C2d — bramka kosztowa | 2026-09-21 | Strata była w ~94% arytmetyczna (bariera<koszt); po bramce pozorny edge 54,6% spada do 49,3% | `STATUS.md` §5 |
| C2.5–C2.8 — seria falsyfikacji | 2026-09-21 | Progi regime, timeframe 1h/4h i cecha `adx_14` wyczerpane jako kierunki naprawy (wszystko NO-GO/nierozstrzygalne) | [runs/](runs/INDEX.md) |
| C2.9 — naprawa metodologii pomiaru | 2026-09-21 | Sweep seedów był pusty (deterministyczny XGBoost); NO-GO odporne na fold-jitter 10/10; strata per trade istotna w OBU reżimach | [runs/c2.9](runs/2026-09-21_c2.9-measurement-methodology/README.md) |
| C2.10 — nowa baza 3 lata (Z5) | 2026-09-21 | NO-GO strukturalne, nie ilościowe: bramka kosztowa blokuje 98% sygnałów `range`, `trend`=0,53% świec | [runs/c2.10](runs/2026-09-21_c2.10-extended-history-z5/README.md) |
| C2.11 — instrumentacja edge'u | 2026-09-21 | Blokada leży w geometrii wypłaty (2p−1)·B>C, nie w kierunku sygnału (p≈51%, wymagane 65–76%) | [runs/c2.11](runs/2026-09-21_c2.11-edge-instrumentation/README.md) |
| C2.12 — model wykonania maker/taker (Z6) | 2026-09-21 | Koszt −52%, ~połowa luki do opłacalności domknięta — nadal NO-GO; per-fold Sharpe przestał być wiarygodnym przyrządem | [runs/c2.12](runs/2026-09-21_c2.12-execution-cost-model/README.md) |
| C2.13 — próg pewności | 2026-09-21 | Hipoteza SFALSYFIKOWANA (trafność spadła zamiast wzrosnąć) — **reguła STOP programu "droga do GO" uruchomiona** | [runs/c2.13](runs/2026-09-21_c2.13-confidence-threshold/README.md) |
| Z16–Z21 — diagnostyka strukturalna + naprawy pomiaru | 2026-09-22 | Reżim `trend` strukturalnie niespójny z horyzontem etykiety (nie do naprawienia barierą); przeciek early stopping naprawiony — najczystsze p=50,38% (brak edge'u kierunkowego) | [runs/z16](runs/2026-09-22_z16-regime-coherence/README.md), [runs/z17+z21](runs/2026-09-22_z17-z21-early-stopping-leak/README.md) |
| Z9/Z19/Z5b — pivot na 4h | 2026-09-22 | Natywne dane 1h/4h (resample psuł wolumen!), rachunek mocy przed eksperymentem, **pre-rejestracja hipotezy jednoreżimowej 4h** (6,8 roku, kryterium: trafność ≥ 56,15%) | [runs/z5b](runs/2026-09-22_z5b-long-history-4h-preregistration/README.md) |
| S1 — eksperyment jednoreżimowy 4h | 2026-09-22 | **Kryterium NIESPEŁNIONE** (trafność 48,60%, CI [45,56%; 51,64%] wobec pre-rejestrowanego progu >54,60% — przepada o 9,04 pp) — **reguła STOP: seria zamknięta**. Walidacja (zasada 16a): **CAVEATS** — liczby potwierdzone co do cyfry, werdykt odporny, ale wynik obowiązuje na **6,95% historii** (krach COVID i szybkie ruchy poza zbiorem). Rekomendacja: zamknięcie Fazy 0 wynikiem negatywnym (Z10 opcja 1, decyzja przy użytkowniku) | [runs/s1](runs/2026-09-22_s1-single-regime-4h/README.md) |
| S1b — S1 po naprawie early stoppingu | 2026-09-22 | **NIEROZSTRZYGALNY** (klauzula `n<925`): naprawa podniosła foldy z early stoppingiem 5/63→53/63, ale ścięła próbę 1 037→345 (abstynencja modelu 70,9%→90,5%). Konfiguracja 4h/V=3 jest przy poprawnym pipelinie **nietestowalna** — brakuje 11,4 lat danych | [runs/s1b](runs/2026-09-22_s1b-early-stopping-naprawiony/README.md) |
| **Z10 — ZAMKNIĘCIE FAZY 0** | 2026-09-22 | **DECYZJA BRAMKOWA UŻYTKOWNIKA: Faza 0 zamknięta wynikiem negatywnym.** Pooled trafność **50,27%** (n=7 687, CI95 [49,15%; 51,38%]) — górny kraniec **1,30 pp poniżej** najniższego progu opłacalności (52,69%) przy mocy **2,8×**: dowód braku, nie brak dowodu. Wąskie gardło **informacyjne, nie inżynieryjne** — wszystkie 10 cech to transformacje ceny i wolumenu. Jawnie NIEPRZETESTOWANE: momentum, ETH/SOL/BNB, funding-jako-sygnał, ekonomia dźwigni | [runs/z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md) |
| **H2.0 — wykonalność nowej hipotezy (funding)** | 2026-09-22 | **Rachunek mocy odrzucił 2 z 3 sformułowań ZA 0 WARIANTÓW.** Bramka na skrajny funding — moc 0,05–0,44× (zagładza próbę jak `trend`). Carry — moc 0,03–0,12×, choć próg opłacalności spada **poniżej 50%** (48,13%): ogranicza liczba nienakładających się okien 48h, więc żyje w formule przekrojowej. Zostaje **funding jako 11. cecha bez bramki na 4h** — pre-rejestrowane jako H2.1 (1 wariant, reguła STOP) | [runs/h2.0](runs/2026-09-22_h2.0-funding-wykonalnosc/README.md) |
| **H3 — noga „timeout” w modelu kosztów** | 2026-09-22 | **Runda obaliła tezę, która ją zamówiła.** Podejrzenie z H2.0 nie broni się: **zlecenie oczekujące wymaga znanej CENY, a przy wyjściu „z upływem czasu” znamy tylko MOMENT**. Zmierzone pasmo progu **[51,64%; 52,69%]** — niepewność **nieistotna decyzyjnie**, poprzeczka NIE obniżona. Przy okazji: naprawiona usterka (koszt liczony w dwóch miejscach niezależnie) i sprostowany mój błąd rachunkowy z H2.0 (53,12% → **52,69%**) | [runs/h3](runs/2026-09-22_h3-noga-timeout-pasmo/README.md) |
| **H2.1 — funding jako cecha (jedyny eksperyment H2)** | 2026-09-22 | **NIEROZSTRZYGNIĘTY** (`n = 98 < 1 000`). Przyczyną nie jest funding ani długość historii, tylko **struktura zadania uczenia**: zdjęcie bramki podniosło udział klasy dominującej 60,83% → 66,58%, więc model **odmawia kierunku w 99,3%** świec. ~~Jedyne ustalenie: funding potroił liczbę decyzji (35 → 98).~~ **⚠ USTALENIE WYCOFANE 2026-09-22 (F1):** „potrojenie” NIE odtwarza się na naprawionym przyrządzie — przy n ~8 000 funding zmienia liczbę decyzji o **1%** (8 114 → 8 196), a nie trzykrotnie. Był to artefakt zagłodzonej próby: przy 35 decyzjach dowolne zaburzenie posteriora mnoży tę liczbę wielokrotnie → [runs/f1](runs/2026-09-22_f1-funding-zmierzony/README.md). **Licznik H2 wyczerpany (1/1), reguła STOP zamknęła serię** | [runs/h2.1](runs/2026-09-22_h2.1-funding-jako-cecha/README.md) |
| **K1 — kontrola pozytywna aparatu** | 2026-09-22 | **Pierwsze w projekcie sprawdzenie, czy przyrzad pomiarowy w ogole widzi sygnal.** Odpowiedz: **TAK** — przy podpowiedzi doskonalej mierzy 100,00% trafnosci, a kryterium werdyktu **nie dalo ani jednego falszywego alarmu na czystym szumie** (0/6). **ALE:** zaczyna widziec dopiero sygnal dajacy **~58%** trafnosci, podczas gdy do zarabiania wystarcza **~53%** — **luka 5,5 pp, w ktorej sygnal bylby oplacalny i niewidzialny**. *(Liczbe ~58% sprostowano w K2: byla przypadkowym skutkiem sposobu pomiaru. Szerokosc tej „niewidzialnej" luki zalezy od liczby transakcji — im wiecej, tym wezsza.)* Przyczyna: model odmawia dzialania w 99,3% swiec. Przy okazji: wbudowany werdykt GO/NO-GO **wystawil GO czystemu szumowi** | [runs/k1](runs/2026-09-22_k1-kontrola-pozytywna/README.md) |
| **K2 — naprawa abstynencji + kill-switch oczyszczony** | 2026-09-22 | **Model milczał, bo milczenie było dla niego opłacalne** — dwie trzecie świec kończy się „niczym", więc przy słabym sygnale odmawiał kierunku w **99,6%** przypadków. Sprawdzono dwa sposoby rozruszania go. **Wagi klas DZIAŁAJĄ:** liczba transakcji 644 → 97 tys., przyrząd zaczyna widzieć **słabszy sygnał niż dotąd**, a jego odczyt staje się monotoniczny (dotychczasowy kod czyta siłę sygnału chaotycznie). **Wymuszenie kierunku NIE DZIAŁA:** transakcji 260× więcej, ale na świecach kończących się niczym wymuszony kierunek wygrywa **48,33%** — gorzej niż rzut monetą — więc rozcieńcza sygnał aż do **ujemnego** marginesu. **Osobno zamknięte: kill-switch NIE zawyża trafności** (+0,04 pp przy ±0,34 pp) — podejrzenie z K1 było szumem. **Runda wykryła też, że dwie z trzech jej własnych reguł decyzyjnych są źle sformułowane** — decyzja o adopcji czeka na użytkownika | [runs/k2](runs/2026-09-22_k2-naprawa-abstynencji/README.md) |
| **A1 — wagi klas przyjęte do użytku** | 2026-09-22 | **Decyzja użytkownika: przyjmujemy naprawę, która wyszła lepiej w K2.** Model uczy się teraz z wagami odwrotnymi do częstości odpowiedzi, więc przestaje uciekać w milczenie. Stary sposób zostaje pod nazwą `none` i **nadal odtwarza dawne wyniki co do cyfry** (przypięte testem). **Uwaga praktyczna:** stare skrypty rund uruchomione dziś dadzą inne liczby niż zapisane — źródłem prawdy dla historii pozostają katalogi `runs/`. Sama adopcja natychmiast ujawniła **realny błąd**, którego runda nie mogła zobaczyć (przebieg wywracał się, gdy fold uczący nie zawierał wszystkich odpowiedzi) — naprawiony. **Otwarte:** model otwiera teraz pozycje także na świecach kończących się niczym; czy to szkodzi na realnej cesze — niezmierzone | [docs/rag/03 (ADR)](docs/rag/03_ryzyko_i_sizing.md) |
| **K3 — dwa odłożone pytania znów da się zmierzyć** | 2026-09-22 | **Przyrząd po raz pierwszy jest dokładniejszy niż to, czego szukamy.** Dwa badania zamknięto kiedyś werdyktem „nie da się rozstrzygnąć” — nie dlatego, że coś wyszło źle, tylko dlatego, że model podjął **345** i **35** decyzji. Po włączeniu wag klas te same konfiguracje dają **1 955** i **8 033** decyzje, a dokładność pomiaru poprawia się z 5,3 i 16,6 punktu do **2,2 i 1,1** — przy szukanym efekcie **2,4 punktu**. Sprawdzian wiarygodności: stan „sprzed zmiany” odtworzył liczby z archiwum co do sztuki. **Cena, powiedziana wprost:** model przestał wybierać świece kończące się wyraźnym ruchem, więc poprzeczka opłacalności podniosła się o pół punktu; czy ta selektywność coś wnosiła — ta runda z założenia nie sprawdza | [runs/k3](runs/2026-09-22_k3-mierzalnosc-po-a1/README.md) |
| **M1 — momentum dostało uczciwy test i go nie przeszło** | 2026-09-22 | **Pierwsza hipoteza postawiona po zamknięciu Fazy 0.** „Momentum” to założenie, że gdy cena rośnie, będzie rosła dalej. Projekt nigdy go porządnie nie sprawdził — filtr przepuszczał takie momenty przez **pół procenta czasu**, zostawało 299 transakcji i nie było czego mierzyć. Po naprawach z ostatnich dni momentum dostało **8 512 transakcji**. **Trafia w 49,74%, a musiałoby w 52,94%** — nawet najbardziej optymistyczny odczyt (50,80%) jest ponad dwa punkty poniżej progu, przy próbie dwukrotnie większej niż wymagana. **Czego NIE wolno z tego wyciągnąć:** że momentum jest gorsze od tego, co testowaliśmy wcześniej — różnica to szum. Jest **tak samo nieobecne**. Sprawdzian wiarygodności: ramię odniesienia odtworzyło historyczny pomiar co do jednej setnej punktu | [runs/m1](runs/2026-09-22_m1-momentum-bez-bramki/README.md) |
| **P1 + F1 — ostatnie mierzalne źródło informacji sprawdzone** | 2026-09-22 | **Najpierw sprawdziliśmy, co jeszcze da się zmierzyć.** Dane o pozycjonowaniu (ilu graczy stoi po której stronie) to najbardziej oczywisty kandydat na informację spoza wykresu ceny — ale giełda udostępnia je **tylko za 30 dni**, czyli ~112 transakcji wobec potrzebnych 4 500. **Cała klasa źródeł odpada, bo nie ma czego mierzyć.** Został funding — opłata za utrzymanie pozycji, jedyna informacja spoza ceny, którą mamy z siedmioletnią historią. **Trafia w 50,34%, a musiałby w 52,94%**; różnica wobec modelu bez niej to **trzy setne punktu**. **Przy okazji wycofaliśmy własne wcześniejsze ustalenie:** „funding potroił liczbę decyzji modelu” okazało się artefaktem małej próby — na poprawionym pomiarze zmienia ją o procent | [runs/f1](runs/2026-09-22_f1-funding-zmierzony/README.md) |
| **P2 — carry przekrojowy: niemierzalny** | 2026-09-22 | **Sprawdziliśmy ostatni kierunek z mapy, który nie wymaga zgadywania ceny:** zarabianie na opłacie funding — pozycja krótka tam, gdzie opłata najwyższa, długa tam, gdzie najniższa. Na 20 największych monetach z 6,5 roku **sama opłata pokrywa koszty** (~0,1% na dwa dni, pewnie powyżej zera — pierwszy taki wynik w projekcie), ale **ruchy cen są 57 razy większe od tego zarobku**. Żeby odróżnić zysk od szczęścia, trzeba by ~140 lat danych; mamy 6,5. Przy okazji obaliliśmy własne założenie z planu: 18 monet chodzi razem jak **dwie** niezależne, więc dokładanie monet nie pomaga. Pobieranie pełnego uniwersum przerwane na polecenie użytkownika — wynik dotyczy 20 dzisiejszych największych monet (jawny błąd przeżywalności) | [runs/p2](runs/2026-09-22_p2-sonda-carry-przekrojowy/README.md) |
| **T4 — kalibracja early stoppingu** | 2026-09-23 | **Sprawdziliśmy, czy zabezpieczenie przed „uczeniem się na pamięć” (early stopping) działa na naszych małych oknach danych.** Działa: bez niego model myli się w prognozach o 58% bardziej, we wszystkich 86 oknach. Próg „co najmniej 30 wierszy”, który kiedyś po cichu wyłączał to zabezpieczenie, dziś w ogóle nie bierze udziału. Niczego w kodzie nie zmieniamy. Przy okazji wyszło to samo co w M1/F1, tylko inną drogą: nawet najlepiej ustawiony model prognozuje zaledwie o 0,7% lepiej niż zgadywanie | [runs/t4](runs/2026-09-23_t4-kalibracja-early-stopping/README.md) |
| **W1 — wykonanie po konkretnej cenie: backtest dopasowany do handlu na żywo** | 2026-09-23 | **Backtest symuluje teraz wypełnienia zleceń tak, jak będą działać na żywo** (zlecenie oczekujące po konkretnej cenie, TP/SL od ceny wypełnienia, kolejność zdarzeń wewnątrz świecy 4h rozstrzygana świecami 5-minutowymi). Trzy sposoby wejścia: **limit po cenie zamknięcia wypełnia się w 99,4 %** i nic nie zmienia (50,11 % wobec progu 52,96 %) — dotychczasowe wyniki nie były zawyżone; **limit na cofnięciu** daje 53,15 % trafności, pierwszy raz ponad progiem, **ale traci pieniądze** (wygrane małe, przegrane pełne — t = −3,9); **zlecenie na wybiciu** jest droższe i trafia gorzej (46,13 %). Lekcja na stałe: więcej wygranych ≠ więcej pieniędzy — werdykt wymaga dodatniego zwrotu netto, nie tylko trafności. Seria zamknięta (3/3) | [runs/w1](runs/2026-09-23_w1-wykonanie-po-cenie/README.md) |
| **N1 — połowa zysku wcześniej i stop na wejście: pieniądze bez zmian** | 2026-09-23 | **Pierwsza runda na danych tylko od 2021 roku** (nowa zasada). Schemat prowadzenia pozycji użytkownika (50 % przy +1,67 %, stop na wejście, reszta do bariery) sprawdzony na tych samych sygnałach co zwykłe wyjście: różnica **+0,007 % na transakcji w przedziale od −0,009 do +0,024** — zero. Trafność skoczyła z 49,6 % na **53,3 %**, ale to iluzja: wygrane zmalały, straty nie, a próg opłacalności dla takich wypłat to 57 %. **Prowadzenie pozycji nie tworzy informacji.** Przy okazji: testy wykryły wadę w mojej własnej regule zanim cokolwiek uruchomiono (poprawka przed wynikiem). Seria zamknięta (1/1) | [runs/n1](runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md) |
| **A1 — formacje świecowe: podręcznik wskazuje kierunek odwrotny** | 2026-09-23 | Sześć formacji z podręcznika (bez parametrów do dobrania) jako reguła: trafność **46,4 %** w przedziale [44,4; 48,3] — **cały przedział poniżej rzutu monetą**, strata 0,18 % na transakcji. Jako dodatkowa cecha modelu: zero zmiany (−0,001 % [−0,012; +0,010]). Winne objęcie (84 % sygnałów): duża świeca jest częściej końcem ruchu. Odwracanie reguły = pomysł po wyniku, wart ok. +0,01 %, nie testujemy. Rodzina zamknięta (2/2) | [runs/a1](runs/2026-09-23_a1-formacje-swiecowe/README.md) |
| **A2 — reszta analizy technicznej: nic nie zarabia** | 2026-09-23 | Struktura trendu, wsparcie/opór, Fibonacci, zdarzenia AT (wybicie, podwójny szczyt/dno, głowa z ramionami, przecięcie średnich, linia trendu) jako reguły z parametrami ze skilla oraz wszystkie 10 cech AT w modelu — na tych samych świecach co model. Trzy ramiona NEGATYWNE (struktura trendu **48,2 %**, wsparcie/opór 49,9 %, model + AT bez zmian), dwa nierozstrzygnięte przez za małą liczbę sygnałów (Fibonacci 51,5 %, zdarzenia 48,3 %), żadne pozytywne. „Graj z trendem" konsekwentnie gorsze od monety. **Analiza techniczna na BTC 4h zamknięta (7/7)** | [runs/a2](runs/2026-09-23_a2-rodziny-at/README.md) |
| **C1 — cash-and-carry: pierwszy dodatni wynik, ale to odsetki za dźwignię, nie prognoza** | 2026-09-23 | Long spot + short kontrakt na BTC zbiera opłatę funding bez ryzyka kierunku: **+5,4 % rocznie na kapitale** w przedziale [3,5; 7,4] za 5,5 roku, z czego połowa z 2021; ostatnie 3 lata 3,6 %. Hedge działa (rozjazdy ≈ 0, obsunięcie 0,64 %). Przełączanie po znaku opłaty przegrywa z kosztami (−9,3 %). Nie wyceniono: depozyt i likwidacja krótkiej nogi (BTC +90 % w 30 dni), ryzyko giełdy. **Decyzja o produkcie należy do użytkownika.** Seria zamknięta (2/2) | [runs/c1](runs/2026-09-23_c1-cash-and-carry/README.md) |
| **R1 — premia rebalansowa: codzienne wyrównywanie koszyka nie zarabia** | 2026-09-23 | Koszyk 20 największych kryptowalut wyrównywany codziennie vs trzymany w miesiącu: **−3,6 % rocznie** w przedziale [−9,5; +2,4], o 12 % niżej po 5,4 roku; obiecywana premia 6–11 % poza przedziałem. Ruchy względne w krypto trwają, wyrównywanie sprzedaje zwycięzców za wcześnie. Z dwóch celów „nie-kierunkowych" tylko carry z hedgem (C1) daje przepływ. Seria zamknięta (1/1) | [runs/r1](runs/2026-09-23_r1-premia-rebalansowa/README.md) |
| **P3 — nowe dane: pozycjonowanie ma 6 lat historii, nie 30 dni** | 2026-09-23 | Podłączono 8 darmowych źródeł spoza wykresu ceny. Archiwum plików Binance ma dane o pozycjach graczy co 5 minut od 2020-09 (P1 sprawdziło tylko API z 30 dniami) — kierunek „nie da się zmierzyć" wraca do gry. Do tego funding COIN-M, kontrakty kwartalne, DVOL, on-chain, Fear & Greed, FRED, Coinbase. Zero pomiaru sygnału; następne rundy: produkt carry (D1), pozycjonowanie jako cecha (O1), momentum przekrojowe (X1) | [runs/p3](runs/2026-09-23_p3-sonda-zrodel-ii/README.md) |
| **D1 — produkt carry: tylko wersja COIN-M ma sens** | 2026-09-23 | Depozyt 1× z miesięczną dopłatą: 0 likwidacji w 5,5 roku, ale od 2022 poniżej bonów skarbowych. Wersja rozliczana w bitcoinie: bez likwidacji z konstrukcji, kapitał 1×, **+9,1 % rocznie [5,9; 12,3]**, od 2022 ok. +2 pp ponad bony (od −1,5 do +7,2). Kontrakt kwartalny ≈ funding. **Decyzja użytkownika: carry odpuszczone — nie o takie zwroty chodzi; kierunek zamknięty** | [runs/d1](runs/2026-09-23_d1-produkt-carry/README.md) |
| **X1 — momentum przekrojowe: +22 %/rok, ale nierozstrzygnięte** | 2026-09-23 | Long zwycięzcy / short przegrani ostatnich 4 tygodni w koszyku top-20, trzymanie tydzień: **+22 %/rok netto [−5; +49]**, dodatni w 6/6 lat (2025 = połowa), neutralny do BTC, koszty 3 %/rok. Pierwszy obiecujący zakład o kierunek — hipoteza z poparciem, nie dowód (potrzeba ~4× próby). Seria zamknięta (1/1); dalsze kroki = decyzja użytkownika | [runs/x1](runs/2026-09-23_x1-momentum-przekrojowe/README.md) |
| **O1 — pozycjonowanie jako cecha: informacja jest, ale za słaba** | 2026-09-23 | Zmiana open interest 24 h jako 5. cecha modelu 4h: trafność 50,25 % (kontrola 49,58 %), strata −0,074 % na transakcję (kontrola −0,107 %), próg 53,07 % — **negatywny**, ale pierwsza cecha spoza wykresu, która zmienia decyzje modelu (21 % transakcji). Seria zamknięta (1/1); kolejne kolumny danych = decyzja użytkownika | [runs/o1](runs/2026-09-23_o1-pozycjonowanie/README.md) |
| **L1 / V1 / G1 — on-chain, opcje, sentyment: trzy razy negatywnie** | 2026-09-23 | Podaż na giełdach (7 dni), premia za zmienność z opcji i Fear & Greed jako 5. cecha modelu 4h: trafność 49,8 / 50,5 / 49,9 % przy progu ~53,5 %, różnice wobec kontroli zero w granicach błędu. Po pięciu źródłach spoza wykresu: dokładanie cech do modelu 4h nie wyprowadzi go ponad koszty (wniosek 67). Serie zamknięte (1/1 każda) | [l1](runs/2026-09-23_l1-onchain-podaz/README.md) · [v1](runs/2026-09-23_v1-premia-zmiennosci/README.md) · [g1](runs/2026-09-23_g1-strach-chciwosc/README.md) |
| **X2 — momentum na top-50: słabiej, a X1 zależało od kalendarza** | 2026-09-23 | Ta sama reguła na 50 monetach: **+16 %/rok [−12; +44]**, nierozstrzygnięte; IC zero, połowa zysku w 33 dniach, 2022 −20 %. Reguła X1 na innym kalendarzu rebalansów: +9 % zamiast +22 %/rok. Momentum przekrojowe = hipoteza ze słabym poparciem; kolejne warianty zakazane, zostaje pomiar na żywo | [runs/x2](runs/2026-09-23_x2-momentum-top50/README.md) |
| **Y1 / Y2 — ten sam model na 1h i 1d: horyzont nie pomaga** | 2026-09-23 | Na 1h trafność **48,3 %** przy progu 54 % (23 334 transakcje, przedział w całości poniżej 50 %, 6/6 lat ujemnych) — negatywnie z ogromnym zapasem; na 1d **50,2 %** przy progu 51,7 %, ale 978 transakcji — nierozstrzygnięte, jak policzono przed przebiegiem. Model kontrolny zmierzony na trzech interwałach, na każdym 48–50 %. | [y1-horyzont-1h](runs/2026-09-23_y1-horyzont-1h/README.md), [y2-horyzont-1d](runs/2026-09-23_y2-horyzont-1d/README.md) |

## Hipoteza w skrócie

**Hipoteza pierwotna (sfalsyfikowana w Fazie 0, patrz Kamienie milowe):** regime-gated —
deterministyczna reguła (nie model) rozdziela dane na reżim "trend" i "range".

- **Test 1 — Momentum:** w reżimie trend, cena kontynuuje ruch.
- **Test 2 — Mean-reversion:** w reżimie range, cena wraca do średniej po przegrzaniu.

Dwa osobne, niezależnie trenowane modele XGBoost — nie jeden połączony model. Walidacja najpierw
wyłącznie na BTC; ETH/SOL/BNB to test generalizacji tej samej hipotezy, nie równoległa walidacja
czterech strategii naraz.

**Hipoteza druga (pre-zarejestrowana w Z5b, sfalsyfikowana w S1):** architektura jednoreżimowa
na natywnych świecach 4h, pełna historia 6,8 roku, wygładzona bramka `range` (V=3), kryterium
sukcesu: trafność kierunku ≥ 56,15%. Wynik: **48,60%** wobec pre-rejestrowanego progu >54,60% —
kryterium przepadło o **9,04 pp**; reguła STOP zamknęła serię po pierwszym (jedynym
pre-zarejestrowanym) wariancie. **Sformułowanie „odrzucona z zapasem” zostało WYCOFANE
w walidacji zasady 16a** — odporne jest kryterium pre-rejestrowane, nie zapas wobec progu
liczonego z tych samych danych. Powtórzenie po naprawie early stoppingu (S1b) wyszło
**nierozstrzygalne** (n=345 < 925).

## Struktura projektu

```
clas5_core/
├── README.md                     ← ten plik
├── CLAUDE.md                     — instrukcje dla Claude Code (czytane automatycznie)
├── STATUS.md        — status commitów, żywy dokument
├── STATUS.md                      — zadania per commit + zasady pracy + Backlog (Z1–Z25)
├── .github/workflows/tests.yml   — CI: pytest + spójność registry/kod
├── docs/rag/                     — pełne uzasadnienia decyzji (01–07), per temat
├── docs/INDEX.md                 — mapa całej dokumentacji
├── config/settings.yaml          — instrumenty, timeframe, progi regime
├── data/fetch_ohlcv.py           — pobieranie/cache OHLCV + resample (Binance USDS-M Futures)
├── agents/
│   ├── feature_miner.py          — 10 cech + regime classifier
│   ├── feature_registry.yaml     — manifest cech (wzór, źródło, rola)
│   ├── labeling.py               — triple-barrier target + walk-forward split
│   ├── ml_optimizer.py           — dwa modele XGBoost (momentum / reversion)
│   └── risk_controller.py        — sizing, kill-switch, bramka kosztowa
├── agent_5_compliance/           — formalne testy leakage
├── backtest/                     — silnik backtestu, koszty, metryki, checkpoint v2,
│                                    skrypty analityczne (zamrożone zapisy eksperymentów)
├── runs/                         — surowy output ciężkich przebiegów (INDEX.md = spis treści)
├── tests/                        — testy jednostkowe/integracyjne/property-based (319)
└── requirements.txt
```

## Szybki start

```bash
git clone <adres-repo>
cd clas5_core
pip install -r requirements.txt --break-system-packages   # lub w wirtualnym środowisku

pytest -v          # 319 passed (stan na H2.1, 2026-09-22)
```

Przed pierwszym pobraniem prawdziwych danych: zweryfikuj dokładny symbol ccxt na swojej maszynie
— `config/settings.yaml` zakłada `"BTC/USDT:USDT"` na Binance USDS-M Futures, ale nie było to
możliwe do zweryfikowania w środowisku, w którym ten kod powstał (brak dostępu do API giełdy).

```python
import ccxt
ex = ccxt.binanceusdm()
ex.load_markets()
print([s for s in ex.symbols if "BTC/USDT" in s])
```

## Mapa dokumentacji

Pełna, zawsze aktualna mapa wszystkich dokumentów: [`docs/INDEX.md`](docs/INDEX.md). Skrót poniżej:

| Plik | Dla kogo / po co |
|---|---|
| `README.md` | Ty jesteś tutaj — ogólny obraz |
| `CLAUDE.md` | Claude Code — krótkie, stabilne zasady, czytane na starcie każdej sesji |
| `STATUS.md` | Plan, historia rund, ryzyka, zadania z ID i statusem, backlog — zmienia się często |
| `runs/INDEX.md` | Księga eksperymentów: co uruchomiono, z jakim wynikiem, ile wariantów zużyto |
| `docs/rag/01_hipoteza_i_architektura.md` | Dlaczego regime-gated, dlaczego LLM offline, dlaczego nie deep learning |
| `docs/rag/02_cechy_i_leakage.md` | Definicje cech, metodologia testowania leakage, multi-repo extraction |
| `docs/rag/03_ryzyko_i_sizing.md` | Triple-barrier labeling, sizing, walk-forward, checkpoint go/no-go |
| `docs/rag/04_narzedzia_zewnetrzne.md` | Decyzje o freqtrade/LEAN/QuantConnect i frameworkach multi-agent LLM |
| `docs/rag/05_metodologia_wytwarzania_i_testow.md` | Piramida testów, Definition of Done, CI/CD |
| `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` | Projekt komponentów LLM offline/nadzorczo (Faza 2+) i `docs/rag/` jako baza wiedzy |
| `docs/rag/07_notatki_spotkania_i_szersza_wizja_systemu.md` | Rozbieżności między notatkami ze spotkania a dyscypliną Fazy 0 — otwarte pytania |

## Kluczowe zasady projektowe

Pełna, aktualna lista: [`CLAUDE.md`](CLAUDE.md). W skrócie:

1. Parametry kalibrowane tylko wewnątrz walk-forward, nigdy na całym zbiorze naraz.
2. Każda cecha ma test leakage przed wejściem do modelu.
3. Target (triple-barrier) i risk_controller używają tego samego mnożnika ATR (1.5×).
4. Feature set rozszerzany jedną cechą na raz, mierzoną na out-of-sample.
5. Leverage cap zawsze wygrywa nad fixed-fractional sizing.
6. LLM nigdy w hot-pathie decyzyjnym — offline/nadzorczo tylko.
7. Regime gate i sizing zostają regułami, dopóki minimalny system nie udowodni edge'u.
8. Zewnętrzne frameworki (freqtrade, LEAN) to katalog wzorców, nigdy zależność runtime w Fazie 0.

## Zastrzeżenie

Ten kod służy do celów badawczych i edukacyjnych. Nie stanowi porady inwestycyjnej. Trading
kontraktów perpetual futures z dźwignią wiąże się z wysokim ryzykiem utraty kapitału. Żadna
część tego repozytorium nie została zwalidowana na prawdziwym kapitale — checkpoint go/no-go
(`STATUS.md`, Commit 6) **nie został osiągnięty — Faza 0 zamknięta wynikiem NEGATYWNYM**
(Z10, 2026-09-22): hipoteza Fazy 0 nie ma edge'u pokrywającego koszty. Nie uruchamiaj tego z
prawdziwymi środkami przed przejściem pełnej sekwencji: walidacja → paper trading → mały kapitał
w pełni tolerowalny do stracenia.

## Licencja

Do ustalenia przed publikacją repo.
