# Przegląd badań: premia Coinbase (CP1, szczebel 1a) i wielkość efektu kaskad likwidacji (E1)

Zadanie 026, 2026-10-05. Praca biurkowa: **0 odczytów na danych projektu** (nie liczono niczego na naszych cenach ani
likwidacjach; licznik E1 = 0; licznik DSR bez zmian). Kontekst: mapa hipotez 007 §7 („BRAK ŹRÓDŁA”, nie szukano
w sieci), ADR-09 (drabina dowodów), karta E1 w zadaniu 011.

## 1. Odpowiedź w skrócie

- **CP1, szczebel 1(a): SŁABE — bez zmian.** Nie znalazłem żadnej publikacji, która mierzy sam sygnał CP1, czyli
  „premia Coinbase wobec Binance przewiduje zwrot BTC w następnym tygodniu”. Dla tego sygnału: **BRAK ŹRÓDŁA**.
  Badania potwierdzają mechanizm pokrewny: popyt z USA i przepływy pieniędzy przesuwają cenę BTC (napływy do ETF-ów,
  premia funduszu GBTC, wolumen z przewagą kupujących). Dwa wyniki mówią jednak przeciw temu, że to Coinbase
  „prowadzi” cenę. Po pierwsze, cenę BTC ustala głównie Binance, a Coinbase dostosowuje się wolniej. Po drugie,
  premie między giełdami rosną razem ze wzrostami BTC albo po nich, a nie przed nimi.
- **E1: przyjąć do rachunku mocy karty 011 efekt brutto ok. 0,5–1,0 % na epizod w 24 h (środek 0,75 %; zakres
  skrajny 0–1,3 %).** Nie znalazłem badania, które mierzy zwrot ceny po kaskadzie zdefiniowanej **wolumenem
  likwidacji** na krypto. Dla tego pomiaru: **BRAK ŹRÓDŁA**. Najbliższy pomiar to odbicie po gwałtownym spadku BTC
  (≥ 5 % w godzinę): +2,4 % po 6 h i +3,1 % po 24 h. Dane pochodzą jednak z lat 2016–2021 i z rynku spot, więc to
  górna granica. Zakres 0,5–1,0 % to **moja interpretacja**, nie liczba ze źródła (rachunek w §4.3).
- **Co z tego wynika dla decyzji.** Przed odczytem dziennika około 2026-12-25 status CP1 się nie zmienia: zostaje
  dziennik papierowy bez realnego kapitału. Dla E1 środek przedziału (0,75 %) leży poniżej progu wykrywalności po
  roku (0,9–1,3 %). Po odjęciu kosztu w kaskadzie (0,3–1 %) zysk netto może być bliski zera. Karta 011 powinna to
  zapisać przed zestawieniem likwidacji z cenami.

## 2. Jak szukałem i czego nie ma w zbiorze

- **Narzędzia:** wyszukiwarka (~35 zapytań, po angielsku) i otwieranie stron (arXiv, RePEc/IDEAS, EconPapers,
  NBER, Semantic Scholar, strony autorów, blogi firm). Każde źródło z tabel otworzyłem. Gdy strona odmawiała
  automatowi (kod 403: SSRN, Wiley, Taylor & Francis, ScienceDirect, ResearchGate), tytuł, autorów i rok
  potwierdziłem **drugą stroną**. Kolumna „sprawdzenie” w tabelach mówi, którą.
- **Pliki PDF:** pełny tekst przeczytałem tylko tam, gdzie PDF dało się pobrać: NBER w11357 (Coval–Stafford),
  NBER w25040 (Bian i in.), EIEF (Borri–Shakhnov), AEA (Gornall i in.). Liczby z tych prac są cytatami z tekstu.
- **Kogo NIE ma w zbiorze (bramka 16a):** literatury po chińsku i koreańsku; pełnych tekstów za paywallem (np.
  pełnej tabeli Miralles-Quirós); raportów płatnych dostawców (Kaiko, Glassnode, K33 — widać tylko skróty
  medialne); prac nieopublikowanych z wynikiem zerowym (skrzywienie publikacyjne: brak efektu rzadziej trafia
  do druku). Brak źródła w tym przeglądzie znaczy „nie znalazłem w tych kanałach”, a nie „nie istnieje”.
- **Rozróżnienie:** kolumna „co mówi źródło” zawiera tylko treść źródła. Moje wnioski są w kolumnie „ten sam
  sygnał?” i w sekcjach 3.3, 4.3 i 5.

## 3. CP1 — premia Coinbase

### 3.1 Tabela źródeł

Jakość: **R** = recenzowane (czasopismo), **WP** = working paper lub preprint, **B** = blog lub analiza praktyka.
„Po publikacji” = czy ktoś sprawdził efekt na danych późniejszych niż próba autorów.

| # | Cytat i link | Rynek, okres | Co mówi źródło (liczba z jednostką) | Po publikacji | Ten sam sygnał co CP1? | Jakość, sprawdzenie |
|---|---|---|---|---|---|---|
| C1 | Makarov I., Schoar A. (2020), *Trading and arbitrage in cryptocurrency markets*, Journal of Financial Economics 135(2), 293–319. [IDEAS](https://ideas.repec.org/a/eee/jfinec/v135y2020i2p293-319.html) | giełdy w wielu krajach (m.in. USA, Korea, Japonia, Europa); dokładny okres i liczba giełd w pełnym tekście — nieodczytane | Różnice cen między krajami są dużo większe niż w obrębie kraju. „Otwierają się w czasie dużych wzrostów BTC”. Wspólny składnik wolumenu z przewagą kupujących wyjaśnia **80 %** zwrotów BTC (ta sama chwila, nie prognoza). | nie | **nie** — premia porusza się razem ze zwrotem; brak testu prognozy | R; abstrakt otwarty na IDEAS |
| C2 | Huang L., Lin T.-C., Lu F., Sun J. (2021, wersja 2025), *The Financialization of Cryptocurrencies*, SSRN 3948407. [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3948407) | GBTC (fundusz w USA) i giełdy BTC; okres nie podany w streszczeniu | Zmiana premii GBTC to „najistotniejszy predyktor dziennego zwrotu BTC”; „odzwierciedla nadwyżkę popytu tradycyjnych inwestorów”. Strategia long-short: **alfa 40 pb dziennie**. | **słabo, przeciw:** replikacja serwisu Paperswithbacktest (okres 2015–2026) daje SR −0,02, −2,3 %/rok ([strona](https://paperswithbacktest.com/strategies/the-financialization-of-cryptocurrencies); B, metoda nieopisana). Od 01.2024 GBTC to ETF bez stałej premii. | **pokrewny** — premia popytu z USA → BTC, ale horyzont dzienny i inny instrument | WP; SSRN 403 → tytuł i autorzy potwierdzeni na Paperswithbacktest i w wynikach wyszukiwarki |
| C3 | Lawant D. (FalconX, 11.10.2024), *What Can Spot ETF Flows Tell Us About the Trajectory of Bitcoin Prices?* [FalconX](https://www.falconx.io/newsroom/what-can-spot-etf-flows-tell-us-about-the-trajectory-of-bitcoin-prices-a-preliminary-statistical-investigation) | ETF-y spot w USA, 01–10.2024, dziennie | Model VAR: napływy z poprzedniego dnia podnoszą dzisiejszy zwrot (współczynnik **0,027**). Test Grangera F 8,48, **p 0,004**. Impuls przepływu daje szczyt ok. **+1,2 %** ceny po 3–4 dniach. | nie (10 miesięcy) | **pokrewny** — przepływy z USA, nie premia; horyzont dni | B; strona otwarta |
| C4 | Lim B. C. (2025/26), *The Price Impact of Spot Bitcoin ETF Flows*, SSRN 6592830. [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6592830) | 5 ETF-ów, 01.2024–04.2025, 313 dni | **53 pb na 100 mln USD** napływu w tym samym dniu (IV 74 pb). Wpływ każdego dnia jest przejściowy, a skumulowany dochodzi do 96 pb po 10 dniach, bo przepływy się powtarzają. | nie | **pokrewny** | WP; SSRN 403 → treść tylko z wyników wyszukiwarki; **niezweryfikowane**, nie wchodzi do werdyktu |
| C5 | Mazur M., Polyzos E. (2025), *Spot Bitcoin ETFs: The Effect of Fund Flows on Bitcoin Price Formation*, Journal of Alternative Investments 27(4), 110–123, doi 10.3905/jai.2025.1.239. [ZU Scholars](https://zuscholars.zu.ac.ae/works/7267/) | ETF-y spot w USA, pierwsze miesiące 2024 | Napływy „silnie przewidują **poziom** ceny BTC, R² 95 %”. Większość zmian ceny zachodzi poza godzinami handlu ETF-ów. | nie | **pokrewny**; R² na poziomach dwóch rosnących szeregów grozi regresją pozorną (moja uwaga) | R; strona uczelni otwarta |
| C6 | Cosenza R., Stalder S. (2024), *Where is the Price of Bitcoin Determined? Price Discovery in a Fragmented Market*, SSRN 4983566. [omówienie](https://mlquants.substack.com/p/where-is-the-price-of-bitcoin-determined) | spot i perpetuale, giełdy regulowane i nie, dane transakcyjne | Głównym źródłem odkrywania ceny jest **Binance** (spot i perpetual). Coinbase zyskuje na znaczeniu tylko przy fixingu NY 16:00. | nie | **przeciw mechanizmowi** „Coinbase prowadzi cenę” w krótkim horyzoncie | WP; SSRN 403 → potwierdzone w omówieniu (substack) i wyszukiwarce |
| C7 | Choi K. J., Lehar A., Stauffer R., *Bitcoin Microstructure and the Kimchi Premium*, SSRN 3189051 (R&R w JFQA). [strona autora](https://sites.google.com/site/kyoungjinchoiecon/teaching-exp) | Korea vs świat; okres w pełnym tekście — nieodczytany | Premia rośnie wraz z kosztami transakcji sieci i zmiennością (tarcia). Według przeglądu KP1 (`runs/2026-09-25_kp1-premia-koreanska/README.md`): premia rośnie **po** wzrostach BTC (+0,135 × wczorajszy zwrot). | nie | **nie** — premia jako skutek, nie przyczyna | WP; status potwierdzony na stronie autora |
| C8 | Borri N., Shakhnov K. (2018), *Cryptomarket Discounts*, SSRN 3124394. [PDF EIEF](https://www.eief.it/eief/images/shakhnov.pdf) | 32 giełdy, 10.02.2015–24.01.2018 | Dyskonta między giełdami trwają (połowa wygasa po ok. 1 dniu). Portfele „tanich” par wobec „drogich”: „spread **486 pb dziennie**, SR 85 %” (cytat; jednostka w tekście niejasna). | nie | **nie** — przekrój giełd, cel = zwrot pary, nie kierunek BTC | WP; PDF przeczytany |
| C9 | Vo N. Q. H. (2026), *USDT premium as an empirical signal for crisis regime identification: evidence from the stablecoin market 2019–2026*, Digital Finance 8(3), 1–32. [IDEAS](https://ideas.repec.org/a/spr/digfin/v8y2026i3d10.1007_s42521-026-00219-x.html) | USDT/USD, 2019–2026 | **Zwrot BTC przewiduje premię USDT** (współczynnik −58,9 w OLS), a nie odwrotnie. | — | **nie, ale istotne:** premia CP1 = Coinbase USD / Binance USDT, więc zawiera kurs USDT/USD, który reaguje na BTC | R; streszczenie otwarte |
| C10 | Griffin J. M., Shams A. (2020), *Is Bitcoin Really Untethered?*, Journal of Finance 75(4), 1913–1964. [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:75:y:2020:i:4:p:1913-1964) | Tether i BTC, boom 2017 | Zakupy za Tether po spadkach dają „spore wzrosty ceny BTC” (przepływ → cena). | nie | **nie** — inny przepływ; tylko kanał „przepływ przesuwa cenę” | R; streszczenie otwarte |
| C11 | Stephanie O. (crypto.news, 06.07.2026), *What is the Coinbase Premium Index? Full 2026 guide*. [crypto.news](https://crypto.news/what-is-the-coinbase-premium-index/) | 2026, przykłady | „Seria dodatnich odczytów towarzyszyła wzrostom albo je poprzedzała” (przykład z 04.2026). Na pytanie, czy premia sama przewiduje cenę: „**nie sama**”. Brak testu i liczb. | — | ten sam wskaźnik, **bez pomiaru** | B; strona otwarta |

**Dla samego sygnału CP1 (premia 7 vs 90 dni → BTC na tydzień): BRAK ŹRÓDŁA.** Nie znalazłem testu w czasopiśmie,
w working paper ani na blogu z liczbą zdarzeń i statystyką.

### 3.2 Szczebel 1(b) — propozycja na papierze (bez danych, bez testu)

Szukamy rynku spoza krypto, na którym lokalna premia popytu miałaby przewidywać cenę globalną.

| kandydat | mechanizm jak w CP1? | co mówią badania | dane, długość | moc na papierze |
|---|---|---|---|---|
| **Fundusze krajowe zamknięte notowane w USA** (cena funduszu w USA vs wartość aktywów na rynku lokalnym) | premia = popyt Amerykanów ponad wartość aktywów | Lee, Shleifer, Thaler (1991), *Investor Sentiment and the Closed-End Fund Puzzle*, JF 46(1), 75–109 ([IDEAS](https://ideas.repec.org/a/bla/jfinan/v46y1991i1p75-109.html)): dyskonta to nastroje inwestorów indywidualnych. Hwang (2011), *Country-specific sentiment and security prices*, JFE 100(2), 382–401 ([EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:100:y:2011:i:2:p:382-401)): popularność kraju wśród Amerykanów odsuwa ceny od fundamentów. Frankel, Schmukler (1996), Open Economies Review 7(1), 511–534 ([IDEAS](https://ideas.repec.org/a/kap/openec/v7y1996i1p511-534.html)): w 1994 **wartość lokalna wyprzedzała** cenę funduszu w USA (przyczynowość w sensie Grangera: lokalni → USA). | tygodniowe ceny i NAV funduszy; historia ok. 1990–2026 (~36 lat), ok. 10–20 funduszy; źródło płatne (CRSP lub Morningstar) = decyzja użytkownika; fundusze zlikwidowane trzeba mieć w próbie | jeden fundusz, 36 lat: wykrywalny SR ≥ **0,33** (moc 50 %; 0,47 przy mocy 80 %). Koszyk 20 funduszy przy korelacji 0,3–0,5 (N_eff 1,9–3,0): SR ≥ **0,19–0,24** (0,27–0,34 przy 80 %). Przy 20 latach: 0,25–0,32. |
| ADR vs akcja na giełdzie macierzystej | podobny | BRAK ŹRÓDŁA zweryfikowanego w tej sesji (Gagnon i Karolyi 2010, JFE 97(1) — strony 403, liczb nie potwierdziłem) | dane śróddzienne, płatne | nie liczono |
| Premia ETF / GBTC do NAV | ten sam rynek (krypto) | C2 | — | **nie jest niezależny** od krypto, więc nie spełnia 1(b) |

Rachunek: wykrywalny SR = 1,96 · √(ρ + (1 − ρ)/n) / √T, gdzie T = lata, n = fundusze, ρ = korelacja wyników
(skrypt jednorazowy, wydruk w §6). **Uwaga do mechanizmu:** literatura funduszy zamkniętych mówi raczej, że premia
**wraca do zera przez cenę w USA** albo że rynek lokalny prowadzi (Frankel–Schmukler). To kierunek przeciwny do CP1
(„popyt z USA ciągnie cenę globalną”). Taki test 1(b) mógłby więc CP1 raczej obalić niż potwierdzić. Warto go
rozważyć właśnie z tego powodu, ale tylko po decyzji użytkownika o płatnych danych.

### 3.3 Werdykt szczebla 1(a) dla CP1: **SŁABE** (bez zmian wobec ADR-09)

- **Za mechanizmem (umiarkowanie):** przepływy z USA przesuwają cenę BTC. Dowodzą tego C2, C3 i C5 (C4
  niezweryfikowane) oraz kanał wolumenu (C1, C10). To oparcie dla zdania „popyt z USA porusza ceną”.
- **Przeciw temu, że premia coś zapowiada:** cenę ustala Binance (C6). Premie rosną razem ze zwrotami albo po nich
  (C1, C7). Część premii CP1 to kurs USDT/USD, który reaguje na BTC (C9).
- **Sam sygnał:** BRAK ŹRÓDŁA. Najbliższy krewny (C2: premia GBTC, horyzont dzienny) w jedynej znalezionej
  replikacji po publikacji nie zarabia (słaba replikacja ze strony B).
- **Zmiana wobec ADR-09:** opis „praktyka rynkowa, brak badań” można doprecyzować tak: „mechanizm pokrewny
  umiarkowany (przepływy ETF, premia GBTC); sam sygnał bez badań; dwa wyniki przeciw roli prowadzącej Coinbase”.
  Status w `docs/rag/09` i w dzienniku zmienia tylko użytkownik — **tu nic nie zmieniam**.

## 4. E1 — wielkość efektu kaskad likwidacji

### 4.1 Tabela źródeł — krypto

| # | Cytat i link | Rynek, okres | Co mówi źródło (liczba z jednostką) | Po publikacji | Ten sam sygnał co E1? | Jakość, sprawdzenie |
|---|---|---|---|---|---|---|
| E-a | Miralles-Quirós J. L., Miralles-Quirós M. M. (2022), *Intraday Bitcoin price shocks: when bad news is good news*, Journal of Applied Economics 25(1), 1294–1313, doi 10.1080/15140326.2022.2151253. [IDEAS](https://ideas.repec.org/a/taf/recsxx/v25y2022i1p1294-1313.html) | BTC spot, Kraken, ceny godzinowe, 01.03.2016–30.06.2021 | „Wyraźne przereagowanie po szokach ujemnych”, największe 6–24 h po zdarzeniu. Po szoku **−5 % w godzinę**: średni skumulowany zwrot **+2,394 % po 6 h i +3,132 % po 24 h**. Przedziału ani liczby zdarzeń nie odczytałem. | nie | **pokrewny** — warunek to spadek ceny, nie wolumen likwidacji; okres sprzed naszego | R; strona wydawcy 403 → tytuł, autorzy i abstrakt w IDEAS i Semantic Scholar; **liczby i okres tylko z indeksu pełnego tekstu w wyszukiwarce** (dwa niezależne zapytania) |
| E-b | Caporale G. M., Plastun A. (2020), *Momentum effects in the cryptocurrency market after one-day abnormal returns*, Financial Markets and Portfolio Management 34(3), 251–266. [IDEAS](https://ideas.repec.org/a/kap/fmktpm/v34y2020i3d10.1007_s11408-020-00357-1.html) | BTC, ETH, LTC, dziennie, 2015–09.2019 | Po dniu z nietypowym zwrotem ceny **idą dalej w tę samą stronę** (momentum) w tym i następnym dniu. Wyjątki z odwróceniem: BTC po dniach dodatnich i ETH po ujemnych. | nie | **pokrewny, przeciwny znak** dla BTC po spadku na horyzoncie dnia | R; streszczenie otwarte |
| E-c | Kitron N. A., Wengrowicz J. M. (2026), *Short-horizon mean reversion in cryptocurrency markets: a matched cross-market measurement*, arXiv 2608.21888. [arXiv](https://arxiv.org/abs/2608.21888) | 183 pary Binance, od 2021, świece 15 min; próba kontrolna 6 mies. | Odwrócenie po ruchu napędzanym agresywnymi zleceniami rynkowymi („taker”) rośnie z intensywnością przepływu. Zysk brutto ok. **1,3 pb na transakcję** wobec kosztu 5 pb. | tak (próba zamrożona 6 mies.) | **pokrewny** — wymuszone przepływy w małej skali; efekt mniejszy niż koszt | WP; abstrakt otwarty |
| E-d | Garcia Seuma R. M. (2026), *Where does the criticality live? …seven crypto-perpetual liquidation cascades*, arXiv 2607.27070; oraz (2026) *Measuring the engine of a liquidation cascade…*, arXiv 2608.03616. [arXiv 1](https://arxiv.org/abs/2607.27070), [arXiv 2](https://arxiv.org/abs/2608.03616) | 7 kaskad BTC 2022–2025, w tym 10.10.2025 (19 mld USD); dane minutowe, Hyperliquid | Kaskady bywają dwóch typów: narastające i z nagłej wiadomości. **88 %** wymuszonej sprzedaży mieści się w 30 min od startu. OI spada o **25–70 %**. Brak liczb o ruchu ceny **po** kaskadzie. | — | opis przebiegu kaskady; do definicji okna w karcie 011, nie do wielkości efektu | WP; abstrakty otwarte |
| E-e | Gornall W., Rinaldi M., Xiao Y. (2025), *Perpetual Futures and Basis Risk: Evidence from Cryptocurrency*, AEA 2026 (wersja wstępna). [AEA](https://www.aeaweb.org/conference/2026/program/paper/ByyFEfr4) | perpetuale vs kwartalne | Obsunięcia bazy perpetuali są ok. 1/3 obsunięć kwartalnych i „szybko wracają”. | — | **nie** — dotyczy bazy, nie ceny | WP; PDF przeczytany |

**Dla zwrotu po kaskadzie zdefiniowanej wolumenem likwidacji na krypto: BRAK ŹRÓDŁA** (brak liczby z jednostką
i przedziałem). Raporty Kaiko i opisy pojedynczych zdarzeń (np. 10.10.2025) to studia przypadków bez statystyki.

### 4.2 Tabela źródeł — rynki tradycyjne (wymuszona sprzedaż)

| # | Cytat i link | Rynek, okres | Co mówi źródło (liczba z jednostką) | Po publikacji | Jakość, sprawdzenie |
|---|---|---|---|---|---|
| T-a | Coval J., Stafford E. (2007), *Asset Fire Sales (and Purchases) in Equity Markets*, Journal of Financial Economics 86(2), 479–512; NBER WP 11357. [NBER](https://www.nber.org/papers/w11357) | akcje USA, sprzedaż funduszy z odpływami, 1980–2003, kwartalnie | Kwartał sprzedaży wymuszonej: nienormalny zwrot **−10,1 %** (t −11,52), w kolejnym miesiącu **−1,4 %**. W miesiącach 4–12 odbicie **+7,74 %** (t 4,43), czyli ok. 77 % spadku. | — | R; PDF NBER przeczytany (liczby z wersji WP; wersja w JFE może się różnić) |
| T-b | Bian J., He Z., Shue K., Zhou H. (2018), *Leverage-Induced Fire Sales and Stock Market Crashes*, NBER WP 25040. [NBER](https://www.nber.org/papers/w25040) | Chiny, rachunki z depozytem zabezpieczającym, 05–07.2015 | Akcje z najwyższego decyla ekspozycji na wezwania do uzupełnienia depozytu tracą wobec najniższego ok. **5 pp w 10–15 dni sesyjnych**. Różnica **wraca do zera w 30–40 dni**. | — | WP (NBER); PDF przeczytany |
| T-c | McLean R. D., Pontiff J. (2016), *Does Academic Research Destroy Stock Return Predictability?*, Journal of Finance 71(1), 5–31. [streszczenie](https://scixindex.com/external-research-anthology/r-david-mclean-jeffrey-pontiff-2016/does-academic-research-destroy-stock-return-predictability/) | 97 anomalii akcji USA | Zwroty **26 % niższe** poza próbą i **58 % niższe po publikacji** | — | R; streszczenie otwarte (Wiley 403) |

### 4.3 Przedział efektu dla karty 011 (moja interpretacja, nie liczba ze źródła)

1. **Górna granica bez korekt:** +3,1 % w 24 h (E-a). Warunek to jednak spadek ≥ 5 % w godzinę. Takich zdarzeń
   jest dużo mniej, a ruch jest większy niż w typowym epizodzie E1 (mapa 007 zakłada 150–300 epizodów na rok).
   Dane pochodzą z lat 2016–2021, z rynku spot, sprzed dominacji perpetuali.
2. **Korekta na publikację i upływ czasu:** × 0,42 (spadek o 58 %, T-c; to miara z akcji, na krypto to analogia)
   → **+1,3 % po 24 h** i +1,0 % po 6 h. Tę liczbę przyjmuję za skrajny optymistyczny wariant.
3. **Typowy epizod jest mniejszy:** odwrócenia na rynkach tradycyjnych odrabiają ok. 77–100 % spadku, ale
   w tygodniach i miesiącach (T-a, T-b). W 24 h na krypto (E-a) odbija ok. 60 % spadku ≥ 5 %. Typowa kaskada E1
   ma mniejszy ruch początkowy, więc **środek przyjmuję na 0,5–1,0 %** (punkt 0,75 %).
4. **Dolna granica 0 (a nawet znak ujemny):** E-b pokazuje kontynuację spadku na horyzoncie dnia, a E-c pokazuje
   efekt mniejszy niż koszt w skali minut.

**Do rachunku mocy karty 011:** efekt brutto **0,75 % na epizod w 24 h (zakres 0–1,3 %)**. Porównanie z mapą 007
(σ 5 % na 24 h): wykrywalny ruch po roku to 0,9–1,3 %, po 3 latach 0,5–0,7 %; koszt w kaskadzie 0,3–1 %.
**Wniosek:** przy środku przedziału E1 jest **niemierzalna po roku**. Po 3 latach mierzalna jest najwyżej
**brutto**, a netto po kosztach efekt może zniknąć. To argument, żeby w karcie 011 zapisać datę odczytu
najwcześniej po 3 latach (~2029-09) albo regułę: „po roku tylko kontrola mocy, bez werdyktu”. Decyzja należy do
zadania 011 i do użytkownika.

## 5. Raport dla użytkownika (prostym językiem)

Sprawdziłem, czy ktoś naukowo zbadał premię Coinbase. Odpowiedź brzmi: nie w tej postaci, w jakiej jej używamy.
Nikt nie zmierzył, czy „Coinbase drożej niż Binance” zapowiada wzrost BTC w następnym tygodniu. Badania potwierdzają
tylko rzecz ogólniejszą: kiedy Amerykanie kupują (np. przez ETF-y), cena BTC rośnie przez kilka dni. Dwa wyniki mówią
jednak przeciw temu, że to Coinbase prowadzi cenę. Cenę ustala głównie Binance, a różnice cen między giełdami
pojawiają się zwykle razem ze wzrostami albo po nich. Dlatego dowód „spoza naszych danych” dla premii Coinbase
pozostaje słaby. Odczyt dziennika około 25 grudnia jest więc jedynym nowym sprawdzianem, a realnego kapitału na tę
nogę nadal nie ma. Dla kaskad likwidacji badania sugerują odbicie rzędu 0,5–1 % na epizod. To mniej niż 1 %, przy
którym rok danych coś by rozstrzygnął, więc na rzetelny wynik trzeba będzie czekać około 3 lat.

## 6. Bramki jakości (16a, 16b) i druga droga

- **Werdykt bramki 16a: Caveats** (do publikacji z zastrzeżeniami poniżej).
- **Druga droga (zamiast przeliczania liczb z danych):** każde źródło z tabel otworzyłem. Przy kodzie 403 tytuł,
  autorów i rok potwierdziłem drugą stroną (kolumna „sprawdzenie”). Liczby z PDF-ów (T-a, T-b, C8, E-e) to cytaty
  z tekstu. Przeliczenie: 7,74 / 10,1 = 0,766, czyli odbicie ok. 77 % w T-a; 3,132 × 0,42 = 1,32 %, czyli wariant
  optymistyczny E1.
- **Rachunek mocy 1(b)** (jednorazowy, wydruk z `python3 -c`): T = 36 lat: n = 1 → SR 0,327; n = 20, ρ = 0,3 →
  0,189; n = 20, ρ = 0,5 → 0,237. T = 20 lat: 0,438 / 0,254 / 0,318. Moc 50 %; przy mocy 80 % mnożnik 1,43.
- **Zastrzeżenia wymagane przy cytowaniu:**
  1. Liczby E-a (+2,394 % / +3,132 %) i okres próby znam tylko z indeksu pełnego tekstu w wyszukiwarce. Strona
     wydawcy odmówiła dostępu, więc przed wpisaniem do karty 011 warto je sprawdzić w PDF z przeglądarki.
  2. C4 (Lim) jest niezweryfikowane i nie wchodzi do werdyktu.
  3. Przedział E1 (0–1,3 %, środek 0,75 %) to moja interpretacja złożona z czterech źródeł o innych warunkach.
     Nie jest to pomiar.
  4. Korekta 58 % pochodzi z anomalii akcji i jest dla krypto tylko analogią.
- **Czerwona flaga „wynik idealnie potwierdza hipotezę”:** nie występuje. Przegląd nie wzmacnia CP1, a dla E1
  obniża zakładany efekt poniżej progu po roku.
- **Licznik wariantów:** bez zmian (0 odczytów; E1 = 0; DSR N bez zmian).

## 7. Czego nie zrobiono

- Nie pobrano żadnych cen ani likwidacji. Nie zestawiono premii ani likwidacji z cenami.
- Nie zmieniono statusu CP1 w `docs/rag/09` ani w dzienniku. Nie zmieniono kodu dziennika ani konfiguracji.
- Nie przeczytano pełnych tekstów za paywallem (Miralles-Quirós, Huang i in., Cosenza–Stalder).

## 8. Użyte skille

### Użyte skille — gałąź `zadanie-026-przeglad-literatury-cp1-e1` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-10-05T17:30:00+00:00 | claude (agent: general-purpose) | `anthropic-skills:quant-strategy-catalog` |  |
| 2026-10-05T17:30:00+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` |  |
| 2026-10-05T17:41:09+00:00 | claude (agent: general-purpose) | `data:validate-data` |  |

Razem: 3 wczytania, 3 różne skille: `anthropic-skills:clas5-quant`, `anthropic-skills:quant-strategy-catalog`, `data:validate-data`.

- `quant-strategy-catalog`: wpisy C2 (premie między giełdami, KP1 z założonym SR 0,15) i E1 (moc z mapy 007).
  Na tej podstawie rozdzieliłem „ten sam sygnał” od „pokrewnego” i porównałem przedział E1 z progiem wykrywalności.
- `clas5-quant`: dyscyplina wielkości efektu i mocy. Efekt podaję z zakresem, rachunek 1(b) podaję z N_eff dla
  skorelowanych funduszy, a korektę po publikacji traktuję jak klątwę zwycięzcy.
- `data:validate-data`: bramka 16a. Pytanie „kogo nie ma w zbiorze” (§2), druga droga przy kodach 403, lista
  zastrzeżeń i werdykt Caveats (§6).
- Pominięte z tabeli zasady 19: `clas5-runda`, bo to nie jest runda (0 odczytów, dokument w `docs/`, jak zadanie
  007); `data:statistical-analysis`, bo przegląd nie liczy statystyk z danych, a przedziały pochodzą ze źródeł.
