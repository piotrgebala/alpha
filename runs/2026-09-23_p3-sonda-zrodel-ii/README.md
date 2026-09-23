# P3 — sonda źródeł danych II: co da się podłączyć i ile ma historii (2026-09-23)

> **STATUS: ZAMKNIĘTA. Wynik: 8 źródeł (13 zbiorów) podłączonych do `data/raw/external/`;
> 7 przechodzi bramę danych w całości, DVOL częściowo (96 %), FRED tylko jako tło.**
> **Najważniejsze: archiwum plików Binance ma dane o pozycjonowaniu (open interest, proporcje
> long/short) co 5 minut od 2020-09-01 — 6 lat, nie 30 dni.** P1 sprawdzało wyłącznie REST
> API i na tej podstawie skreśliło całą klasę źródeł; ta sonda to koryguje (wniosek 59).
> Sonda odczytowa: **0 wariantów, POZA licznikami hipotez** — nie policzono żadnej korelacji
> ze zwrotami, sygnału, trafności ani P&L. Walidacja (16a): **READY**; przegląd diffu (16c):
> **Approve** (po poprawce z przeglądu bezpieczeństwa). Kolejność w gicie: pre-rejestracja +
> kolektor `1e61613` → pobranie → profil → wynik w commicie zamykającym.
> Decyzja użytkownika 2026-09-23: „sprawdź wszystkie warianty, myślę też o podpięciu
> dodatkowych danych".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Podłączyliśmy osiem nowych źródeł danych, wszystkie darmowe i bez klucza. Najważniejsze
z nich to dane o tym, ilu graczy stoi po której stronie rynku i ile mają otwartych pozycji
(pozycjonowanie): okazało się, że giełda publikuje je w archiwum plików za sześć lat wstecz,
a nie za miesiąc, jak wynikało z poprzedniej sondy.** To zmienia listę rzeczy do zbadania:
pozycjonowanie było skreślone jako „nie da się zmierzyć", a teraz da się — na tej samej
próbie co wszystkie inne cechy.

Oprócz tego mamy: funding perpetuala rozliczanego w bitcoinie (do wariantu carry bez ryzyka
likwidacji), ceny 24 kontraktów kwartalnych (do wariantu carry z góry znaną stopą), zmienność
implikowaną z opcji (DVOL), 14 wskaźników z łańcucha bitcoina (m.in. ile monet płynie na giełdy),
indeks strachu i chciwości, stopy amerykańskie i dolara (do porównania carry ze stopą wolną
od ryzyka) oraz ceny z Coinbase (premia amerykańska).

**Zastrzeżenia:** proporcje long/short największych graczy mają roczną dziurę (grudzień 2021 →
grudzień 2022, 16 % bazy); open interest ma 473 zerowe odczyty do odfiltrowania; kontrakty
kwartalne mają 330 pustych świec po wygaśnięciu. Sonda niczego nie mierzy — każde źródło
dostanie własną rundę z pre-rejestracją i rachunkiem mocy.

---

## ID testu

**P3** — sonda wykonalności NOWYCH źródeł danych + podłączenie tych, które przechodzą bramę
danych (kolektor `data/fetch_external.py`, cache `data/raw/external/`). Motywacja: po
zamknięciu serii A/C/R/W/N jedynym otwartym kierunkiem z realnym priorem jest **inny zbiór
informacyjny** (wniosek 11), a lista P1 skreśliła pozycjonowanie na podstawie **REST API**
(30 dni). Ta sonda sprawdza **archiwa** (pliki, nie API) i źródła spoza Binance.

## Metadane

- Branch: `p3-zrodla-danych` (od `master` @ `0dbd4e3`).
- Sondy wstępne (bez zapisu do repo): dwa skrypty odczytowe w scratchpadzie
  (listing S3 archiwum, po jednym zapytaniu do każdego API publicznego) — wyniki
  w sekcji „Sonda wstępna".
- Komenda pobrania: `py -m data.fetch_external` (Windows: `PYTHONUTF8=1`; bez kluczy API;
  pełny stdout → `raw_output.txt`). Profil: `py -m data.profile_external` → `profil.txt`.
- Zakres pobrania: od `2019-01-01` (zapas na warmupy przed bazą z zasady 20) do dziś;
  pomiary (przyszłe rundy) i tak filtrują `2021-01-01 → 2026-07-01` przez `fetch_window`.

## Poprzedzające wyniki

- **P1** (`runs/2026-09-22_p1-sonda-zrodel-danych/`): pięć endpointów `futures/data/*`
  oddaje **30,8 dnia**; przy potrzebie ~4 481 transakcji (3,4 roku) → pozycjonowanie
  NIEMIERZALNE; jedyna droga = zbierać od dziś (kolektor `data/collect_positioning.py`,
  aktywny od 2026-09-23). **P1 sprawdzało REST API, nie archiwum plików** — ta sonda
  sprawdza archiwum.
- **P2** (`runs/2026-09-22_p2-sonda-carry-przekrojowy/`): uniwersum point-in-time 287 symboli
  z archiwum `data.binance.vision` (funding + 1d) — wzorzec listingu S3 i pobierania z
  archiwum, na którym buduje kolektor P3.
- **C1** (`runs/2026-09-23_c1-cash-and-carry/`): carry z hedgem POZYTYWNY jako przepływ;
  otwarte pytania produktu: depozyt/likwidacja krótkiej nogi, porównanie ze stopą wolną od
  ryzyka, alternatywne konstrukcje (COIN-M, kontrakty kwartalne) — wymagają danych, których
  repo nie ma (funding COIN-M, ceny kontraktów kwartalnych, T-bill).
- **R1** (`runs/2026-09-23_r1-premia-rebalansowa/`): momentum względne wewnątrz miesiąca
  (wniosek 57) — hipoteza odwrotna B1 potrzebuje funding per symbol (jest w cache P2).
- **Wniosek 11** (INDEX): wąskie gardło Fazy 0 było informacyjne; **zasada 18**: nowe źródło
  przechodzi rachunek mocy ZE SWOJĄ historią.

## Pre-rejestracja: brama danych (kryteria zapisane PRZED pobraniem)

Źródło „przechodzi" bramę, gdy spełnia wszystkie cztery:

- **G1 — historia:** pokrywa bazę z zasady 20 (`2021-01-01 → 2026-07-01`, 5,5 roku) w co
  najmniej **90 %** dni; źródło z krótszą historią dostaje status „częściowe" z podanym
  ułamkiem, a rachunek mocy przyszłej rundy liczy się z JEGO `n`, nie z bazy.
- **G2 — point-in-time:** wartość na dzień `t` była znana w dniu `t` (archiwum = pliki
  publikowane raz, bez rewizji) LUB źródło ma znane opóźnienie publikacji, które przyszła cecha
  uwzględni przesunięciem (`shift`) — zapisane w tabeli.
- **G3 — koszt:** publiczne, bez klucza, bez opłat. Źródła płatne (Glassnode, Coinglass,
  Kaiko) tylko do listy „na potem" — koszt uzasadnia się PO rachunku mocy, nie przed.
- **G4 — ziarno:** natywne ziarno ≤ potrzebnemu (4h dla cechy modelu jednoaktywowego, 1d dla
  formuł przekrojowych/dziennych; Z9: bez resamplingu z grubszego ziarna).

Dla każdego źródła, które przejdzie: **jakie rodziny katalogu odblokowuje** (pięć pól) i
**szkic mierzalności** przyszłej rundy — ale **żadnego pomiaru sygnału w tej rundzie**.

### Kandydaci (lista zamknięta przed pobraniem)

| # | źródło | co | mechanizm, który ma odblokować |
|---|---|---|---|
| 1 | archiwum Binance `futures/um/daily/metrics` | open interest, proporcje long/short (top traderzy: konta i pozycje; wszystkie konta), proporcja taker buy/sell — 5 min | pozycjonowanie: tłok po jednej stronie → likwidacje kaskadowe (ograniczenie strukturalne) |
| 2 | REST `dapi` (COIN-M) `fundingRate` | funding perpetuala rozliczanego w BTC | wariant produktu carry bez ryzyka likwidacji krótkiej nogi (zabezpieczenie w BTC) |
| 3 | archiwum Binance `futures/um/monthly/klines/BTCUSDT_<YYMMDD>` | świece 8h kontraktów kwartalnych (24 kontrakty) | basis trade: różnica ceny kontraktu i spotu znana NA WEJŚCIU (przepływ zamknięty w chwili wejścia) |
| 4 | Deribit `get_volatility_index_data` | DVOL (zmienność implikowana 30 dni) BTC/ETH, 1d | opcje/vol: premia za ryzyko zmienności (variance risk premium) jako cecha i jako target |
| 5 | CoinMetrics community | on-chain 1d: adresy aktywne, transakcje, MVRV, przepływy na/z giełd, podaż na giełdach, hashrate, opłaty | on-chain: ruch monet na giełdy = podaż do sprzedaży (opóźniona reakcja) |
| 6 | alternative.me | Fear & Greed 1d | sentyment złożony (zdarzenia/kalendarz; kontrariańsko) |
| 7 | FRED | DTB3, DGS3MO, SOFR, DTWEXBGS (dolar), SP500 — 1d | stopa wolna od ryzyka do porównania carry; makro jako cecha |
| 8 | Coinbase Exchange | BTC-USD 1d | premia Coinbase (popyt z USA vs Binance) |
| 9 | archiwum `liquidationSnapshot` | likwidacje | (sprawdzić dostępność) |
| 10 | OKX / Bybit funding | funding innych giełd | rozproszenie fundingu między giełdami |

## Czego ta runda NIE liczy (warunek zera wariantów)

Żadnej korelacji z przyszłym zwrotem, żadnej trafności, żadnego P&L, żadnego rankingu
symboli po zwrocie. Profil danych = zakres, luki, duplikaty, kwantyle, masa punktowa,
autokorelacja SAMEJ zmiennej (nie ze zwrotem).

---

## Sonda wstępna (dwa skrypty odczytowe, wyniki w `sonda_wstepna.txt`)

| # | źródło | co sonda pokazała |
|---|---|---|
| 1 | archiwum `metrics` BTCUSDT | **2 213 plików dziennych 2020-09-01 → 2026-09-22, zero brakujących dni**, 288 wierszy/dzień (5 min), 8 kolumn = dokładnie wielkości pięciu endpointów z P1; pierwsze pliki (2020-09) mają zdublowane wiersze. ETH/SOL/BNB od 2021-12-01 |
| 2 | REST `dapi` funding COIN-M | historia od **2020-08-10** (archiwum plików cm tylko od 2022-07 — REST sięga dalej) |
| 3 | kontrakty kwartalne um | **24 kontrakty** `BTCUSDT_210326 → _261225`, 15 interwałów (8h, 1d…); cm od `BTCUSD_200925` |
| 4 | Deribit DVOL | BTC i ETH od **2021-03-24**, 1d, ≤ 1000 punktów na zapytanie |
| 5 | CoinMetrics community | 31 metryk btc 1d, w tym `FlowInExUSD`/`FlowOutExUSD`/`SplyExNtv` (od 2011), `CapMVRVCur` (2010), `AdrActCnt`/`TxCnt`/`HashRate` (2009) |
| 6 | alternative.me F&G | od **2018-02-01**, 1d |
| 7 | FRED | `DTB3`, `DGS3MO`, `SOFR`, `DTWEXBGS`, `SP500` — CSV bez klucza, dni robocze |
| 8 | Coinbase Exchange | świece 1d BTC-USD od 2021 (i wcześniej), 300 na zapytanie |
| 9 | archiwum `liquidationSnapshot` | **prefiks istnieje, plików brak** — niedostępne |
| 10 | OKX / Bybit funding | OKX: brak historii sprzed ~2026 (0 rekordów za 2021); Bybit: historia od 2021-01 — nieużyte w tej rundzie (rozproszenie fundingu między giełdami to osobna hipoteza) |
| + | `premiumIndexKlines` / `indexPriceKlines` / `markPriceKlines` | od 2020-01 (indeks premii = składnik fundingu) — zanotowane, nie pobrane |
| + | `bookDepth` / `bookTicker` | od 2023-01 / 2023-05 — za krótko (G1), nie pobrane |

## Wynik: co przeszło bramę danych (profil w `profil.txt`, przeliczenia w `walidacja.txt`)

| zbiór (`data/raw/external/`) | ziarno | zakres | pokrycie bazy 2021-01-01→2026-07-01 (G1) | G2 point-in-time | G3 | G4 | werdykt |
|---|---|---|---|---|---|---|---|
| `binance_metrics_BTCUSDT_5m` | 5 min | 2020-09-01 → 2026-09-22 | **577 415 / 578 016 = 99,90 %** (156 luk, 634 punkty) | pliki archiwum publikowane raz; snapshot na chwilę `t` | darmowe | 5 min ≤ 4h | **PRZECHODZI** |
| `binance_cm_funding_BTCUSD_PERP` | 8h | 2020-08-10 → dziś | 6 020 / 6 021 = 99,98 % | stawka znana w chwili rozliczenia | darmowe | 8h | **PRZECHODZI** |
| `binance_um_dated_BTCUSDT_8h` | 8h | 24 kontrakty, 2021-02-03 → 2026-08-31 | 5 921 / 6 021 unikalnych znaczników = 98,3 % (od 2023-09 dwa kontrakty naraz) | świece archiwum | darmowe | 8h | **PRZECHODZI** (filtr: `open_time < expiry` i `volume > 0`) |
| `deribit_dvol_BTC_1d` / `_ETH_1d` | 1d | 2021-03-24 → dziś | **1 925 / 2 007 = 95,9 %** | indeks liczony na bieżąco z opcji | darmowe | 1d (jako cecha 4h: `shift` 1 dzień) | **PRZECHODZI (częściowo: start 2021-03-24)** |
| `coinmetrics_btc_1d` | 1d | 2019-01-01 → dziś | 2 007 / 2 007 = 100 %, **0 braków w 14 metrykach** | wartość dnia `t` publikowana po zamknięciu dnia (opóźnienie ~godziny, sporadyczne rewizje) → cecha używa `shift(1)` | darmowe (community) | 1d | **PRZECHODZI** |
| `alternative_fng_1d` | 1d | 2018-02-01 → dziś | 2 006 / 2 007 = 99,95 % | wartość dnia publikowana rano UTC | darmowe | 1d | **PRZECHODZI** |
| `coinbase_BTC-USD_1d` | 1d | 2019-01-01 → dziś | 2 007 / 2 007 = 100 % | świece | darmowe | 1d | **PRZECHODZI** |
| `fred_*_1d` (5 serii) | dni robocze | 2019-01-02 → dziś | 71,4 % dni kalendarzowych = wszystkie dni robocze (74–86 świąt jako brak) | wartości dnia publikowane następnego dnia roboczego | darmowe | 1d | **TŁO** (porównanie carry ze stopą, nie cecha) |

### Własności danych, które przyszłe rundy MUSZĄ uwzględnić

- **Pozycjonowanie (`metrics`):** (a) `count_toptrader_long_short_ratio` i
  `sum_toptrader_long_short_ratio` mają **92 226 braków = 16,0 % bazy, w sześciu blokach
  między 2021-12-30 a 2022-12-14** (praktycznie cały 2022) — cecha na tych kolumnach ma
  n ≈ 84 % bazy; `count_long_short_ratio` (wszystkie konta) braki 1,0 %, `sum_taker_long_short_vol_ratio`
  5,9 %; (b) **473 zerowych odczytów OI** (0,07 %) skupionych w 2022-03-07 i 2024-07-11…14 —
  błędy do zamaskowania, nie wartości; (c) autokorelacja lag-1 przy 5 min: OI 0,995,
  proporcje L/S 0,9998 (poziomy — N_eff liczyć z epizodów, wniosek 56), taker ratio 0,087
  (niemal niezależne odczyty); (d) `sum_open_interest_value / (OI × close)`: mediana odchylenia
  0,5 %, p99 4,6 % — spójne (mark vs close).
- **Funding COIN-M:** masa punktowa **42,7 % na 0,0001** (stawka domyślna; wniosek 15 — progi
  tylko absolutne), 18,4 % stawek ujemnych, acf1 0,67; znaczniki z jitterem ≤ 0,1 s wokół
  siatki 8h → `floor("8h")` przed łączeniem (tabela „luk" w profilu to artefakt jittera).
- **Kontrakty kwartalne:** **356 świec po dacie wygaśnięcia, 330 z zerowym wolumenem**
  (placeholdery archiwum) — filtrować; do 2023-06 jeden kontrakt naraz (~100 dni notowań),
  od 2023-09 dwa (~182 dni); `BTCUSDT_210326` zaczyna się 2021-02-03 (styczeń 2021 bez
  kontraktu w archiwum).
- **DVOL:** brak stycznia–marca 2021 (4,1 % bazy); acf1 dzienna wysoka (poziom).
- **F&G:** masa punktowa 2,5 % (wartość 50), acf1 0,957; dwie luki (4 dni łącznie).
- **FRED:** tylko dni robocze — do porównań rocznych (`DTB3` średnia roczna), nie jako cecha 4h.

### Jakie rodziny katalogu odblokowuje każde źródło (pięć pól; statusy z `families.md`)

| źródło | zbiór informacyjny | rodziny (status przed P3 → po P3) | mechanizm jednym zdaniem |
|---|---|---|---|
| `metrics` (OI, L/S, taker) | pozycjonowanie/OI | pozycjonowanie jako cecha modelu kierunkowego 4h (WYKLUCZONE-danymi → **NIETKNIĘTE**); OI × funding jako filtr tłoku (jw.) | tłok po jednej stronie + dźwignia → kaskady likwidacji w przeciwną stronę (ograniczenie strukturalne: ktoś MUSI zamknąć) |
| funding COIN-M | funding/basis | carry z hedgem w wariancie COIN-M (NIETKNIĘTE) | jak C1, ale zabezpieczenie w BTC = brak ryzyka likwidacji krótkiej nogi; inna stawka |
| kontrakty kwartalne | funding/basis | **basis trade** (NIETKNIĘTE) | stopa znana NA WEJŚCIU (cena kontraktu − spot), zamykana w dniu wygaśnięcia — przepływ, nie prognoza |
| DVOL | opcje/vol | premia za ryzyko zmienności (VRP: DVOL² − zrealizowana) jako cecha lub target (NIETKNIĘTE) | kupujący opcje płacą za ubezpieczenie ponad realizowaną zmienność |
| CoinMetrics | on-chain | przepływy na giełdy / MVRV / aktywność jako cechy (NIETKNIĘTE) | monety płynące NA giełdy = podaż do sprzedaży (opóźniona reakcja) |
| F&G | zdarzenia/sentyment | sentyment kontrariański (NIETKNIĘTE) | błąd behawioralny (skrajny strach = wyprzedanie) |
| FRED | makro | stopa wolna od ryzyka do wyceny carry; dolar/S&P jako cechy (NIETKNIĘTE) | koszt kapitału; korelacja BTC z ryzykiem |
| Coinbase | OHLCV innych rynków | premia Coinbase (NIETKNIĘTE) | popyt instytucjonalny z USA (opóźniona reakcja) |

### Szkic mierzalności przyszłych rund (BEZ patrzenia na sygnał; formalny rachunek w pre-rejestracji każdej z nich)

- **Cecha modelu 4h (pozycjonowanie, DVOL, on-chain, F&G, premia Coinbase):** ta sama próba co
  każda cecha na nowej bazie — 11 592 świec OOS, przy abstynencji ~40 % (wagi klas)
  **n ≈ 6 950 transakcji**, `wald_half_width(6 950)` ≈ **1,2 pp**, próg ±B 53,07 %; P1 wymagało
  4 481 → dostępne **1,55×**. Kolumny top-trader (dziura 2022): n ≈ 5 850 → 1,3×. DVOL: n ≈ 6 660.
  Rachunek `measurability_report(0,56; 0,5307; n)` z `expected_trades` w pre-rejestracji O1.
- **Basis trade (kontrakty kwartalne):** stopa jest ZNANA na wejściu, więc pytanie nie brzmi
  „czy jest edge", lecz „ile średnio wynosiła i jak zmienna była między kontraktami" — jednostka
  niezależna = kontrakt (22 wygasłe w danych), plus szereg dzienny bazy do N_eff z autokorelacji
  (jak C1: 1 095 okien → N_eff 286). Analiza opisowa + ryzyko depozytu; nie test hipotezy.
- **Carry COIN-M:** ten sam przyrząd co C1 (`carry_hedged.summarize_pnl`), 6 020 rozliczeń,
  N_eff z autokorelacji stawki (acf1 0,67 → mniejsza korekta niż w USDT-M).

## Co na plus (+)

- **Cała klasa źródeł wraca do gry przy tej samej próbie co reszta cech:** 6 lat pozycjonowania
  co 5 minut, zero brakujących dni, wartości zgodne z kolektorem REST za wspólne 505 godzin
  (mediana różnicy 0,02–0,1 %).
- **Osiem źródeł jednym poleceniem, odtwarzalnie, bez kluczy** — `py -m data.fetch_external`,
  idempotentnie, 4,5 minuty; profil jednym poleceniem.
- **Brama danych zapisana PRZED pobraniem** (G1–G4) i zastosowana mechanicznie; lista
  kandydatów zamknięta przed sondą, wyniki negatywne (likwidacje, OKX, bookDepth) też zapisane.
- **Przegląd bezpieczeństwa złapał realny błąd** (adres kolejnej strony brany z odpowiedzi
  serwera) — poprawiony PRZED scaleniem; `http_get` przyjmuje wyłącznie `https`.

## Co na minus (−)

- **P1 skreśliło pozycjonowanie po sprawdzeniu JEDNEGO kanału** (REST) — jeden dzień pracy
  kolektora i wniosek 39 w INDEX oparte na niepełnej sondzie. Lekcja: wniosek 59.
- **Pobrano tylko BTC** (`metrics`, kontrakty, funding COIN-M) — zgodnie z zasadą 9; ETH/SOL/BNB
  `metrics` dostępne od 2021-12-01 (jedno polecenie więcej).
- **Roczna dziura w proporcjach top traderów (2022)** ogranicza te dwie kolumny do 84 % bazy;
  `count_long_short_ratio` i OI są pełne.
- **Pierwsze pobranie CoinMetrics odbyło się kodem sprzed poprawki bezpieczeństwa** (adres
  z odpowiedzi — w praktyce ten sam host); dane identyczne, poprawka dotyczy przyszłych
  przebiegów; test pokrywa nową ścieżkę.
- **Zero pomiaru sygnału** — celowo; runda nie mówi NIC o tym, czy te dane niosą informację.
  Prior dla pozycjonowania jest wyższy niż dla transformacji ceny (inny zbiór informacyjny,
  mechanizm strukturalny), ale prior to nie wynik.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Drugą drogą:** 2 213 plików × 288 odczytów = 637 344; wiersze 636 710; różnica **634 =
  suma brakujących punktów z tabeli luk (634)** ✔. Pokrycie bazy DVOL: 1 925 dni = dokładnie
  liczba dni 2021-03-24 → 2026-07-01 ✔. Kontrakty: 356 świec po `expiry`, 330 z zerowym
  wolumenem = wszystkie zerowe świece zbioru ✔.
- **To te same wielkości co w P1:** kolumny archiwum ↔ endpointy (`sum_open_interest` ↔
  `openInterestHist`, `count_toptrader…` ↔ `topLongShortAccountRatio`, `sum_toptrader…` ↔
  `topLongShortPositionRatio`, `count_long_short_ratio` ↔ `globalLongShortAccountRatio`);
  za wspólne 505 godzin 2026-09-01 → 09-22: mediana |różnicy względnej| 0,02 % (OI) – 0,1 %
  (proporcje), max 0,8 % (OI) – 8 % (proporcja kont top traderów; REST = agregat okresu 1h,
  archiwum = snapshot na pełną godzinę) — bez dokładnej równości, ta sama wielkość ✔.
- **Kogo NIE ma:** symbole poza BTC; likwidacje (archiwum puste); pozycje per giełda inna niż
  Binance; głębokość księgi przed 2023; styczeń–marzec 2021 w DVOL; top-trader 2022; dni
  wolne w FRED; grudzień 2021 → kontrakt `_211231` jest, ale styczeń 2021 bez kontraktu.
- **Red flag „6 lat, a P1 mówiło 30 dni":** sprawdzone u źródła — P1 pytało `fapi.binance.com/
  futures/data/*` (HTTP 400 przy `startTime` sprzed 30 dni), archiwum to inny kanał
  (`data.binance.vision`, pliki S3); wartości zgodne (wyżej). Nie artefakt.
- **Red flag „wszystko przeszło":** nie wszystko — likwidacje, OKX, bookDepth/bookTicker
  odpadły; FRED tylko jako tło; DVOL częściowo.

## Przegląd diffu (zasada 16c) — werdykt: **Approve** (po poprawce z przeglądu bezpieczeństwa)

Zakres: `data/fetch_external.py` (nowy, ~690 linii), `data/profile_external.py` (nowy),
`tests/test_fetch_external.py` (16), `tests/test_profile_external.py` (6), README rundy.

**Bezpieczeństwo (skill `security-review`, przed przeglądem):** jedno znalezisko Medium
8/10 — `fetch_coinmetrics` brał `next_page_url` z odpowiedzi serwera i podawał go do
`urlopen` (obsługującego też `file://`, `ftp://`, `data:`). **Poprawione:** stronicowanie
tokenem (`next_page_token`) dopisywanym do STAŁEGO adresu (`coinmetrics_page_url`), twardy
limit 1 000 stron, a `http_get` odrzuca każdy schemat poza `https` (test bez sieci na
`http://`, `file://`, `ftp://`, `data:`; test, że adres drugiej strony zawiera token i nie
zawiera hosta z odpowiedzi). Odrzucone jako niewykonalne: klucze S3 w URL (host stały),
zip (jeden plik do pamięci, bez ekstrakcji na dysk), ścieżki zapisu (literały + zaufany `out_dir`).

**Korektność:** (1) `parse_metrics_csv` — nagłówek wymagany, brak kolumny → `ValueError`,
duplikat znacznika → ostatni (test); (2) `parse_klines_csv` — z nagłówkiem i bez, µs → ms
przez próg 10¹⁴ (test), 12 kolumn wymagane; (3) `date_chunks` — pokrycie bez dziur i nakładania
(hypothesis, 0–3 000 dni, max_days 1–1 000); (4) `s3_list` — paginacja markerem, klucze `.zip`
i podkatalogi osobno (test ze stubem); (5) `fetch_dated_contracts` — dedupe po
`(contract, open_time)`, `expiry` z sufiksu (test); (6) `run()` łapie `Exception` szeroko
— świadomie (jedno źródło nie zatrzymuje reszty), błąd drukowany i kod wyjścia 1.
**Brak lookaheadu:** moduł nie liczy nic poza pobraniem; profiler nie dotyka zwrotów.
**Edge-case'y:** pusta odpowiedź → pusta ramka (funding, F&G, CoinMetrics); brak plików → `ValueError`;
plik istnieje → pominięty (test `_skip_existing`); nieznane źródło → `ValueError` (test).
**Uwagi (bez blokady):** `fetch_coinm_funding` nie zaokrągla jittera ms (zostawione surowe —
zaokrąglenie należy do warstwy analizy, jak w `carry_probe`); profil FRED raportuje pokrycie
kalendarzowe (71 %) — czytelnik musi wiedzieć, że to dni robocze (zapisane w tabeli).
**Werdykt jednym zdaniem:** kod poprawny i przetestowany bez sieci, jedno realne ryzyko
bezpieczeństwa usunięte przed scaleniem — **Approve**.

## Wniosek

**Dane o pozycjonowaniu są dostępne za 6 lat (2020-09 → dziś), co 5 minut, bez luk w dniach,
za darmo** — P1 sprawdziło tylko REST API i skreśliło całą klasę źródeł na podstawie jednego
kanału. Przy nowej bazie (zasada 20) pozycjonowanie ma tę samą próbę co każda inna cecha
(~6 950 transakcji, 1,55× wymaganej), więc jest MIERZALNE. Do tego siedem innych źródeł
przechodzi bramę danych (funding COIN-M, 24 kontrakty kwartalne, DVOL od 2021-03, 14 metryk
on-chain bez braków, Fear & Greed, FRED jako tło, Coinbase). Każde z nich odblokowuje rodzinę
hipotez, która dotąd miała status „wykluczone danymi" albo „nietknięte" — i każde wymaga
własnej pre-rejestracji z rachunkiem mocy, bo ta runda niczego nie zmierzyła.

## Rekomendacja

1. **Kolejność następnych rund (jedna hipoteza na raz, każda z własnym licznikiem):**
   (a) **D1 — produkt carry** na nowych danych: depozyt/likwidacja krótkiej nogi z historii
   cen, carry COIN-M tym samym przyrządem co C1, basis kontraktów kwartalnych jako stopa znana
   na wejściu, porównanie ze stopą T-bill (FRED) — analiza ryzyka wyniku dodatniego C1a,
   nie nowy test edge'u (bez licznika hipotez; COIN-M i basis jako generalizacja C1a na inny
   instrument z jawnym odnotowaniem, że seria C była STOP);
   (b) **O1 — pozycjonowanie jako cecha modelu 4h** (nowa seria, licznik od zera): jedna
   cecha z `metrics` wybrana PRZED danymi po mechanizmie (zmiana OI × kierunek ceny albo
   proporcja taker), test przecieku, `measurability_report` z abstynencji, kryterium dwóch
   warunków;
   (c) **X1 — momentum przekrojowe** (odwrotność R1) na uniwersum P2 z fundingiem per symbol;
   (d) dalsze (DVOL/VRP, on-chain, F&G, premia Coinbase) — po wynikach (a)–(c), każde osobno.
2. **Kolektor REST (`CLAS5-positioning`) staje się zbędny dla historii** — archiwum daje to
   samo z opóźnieniem ~1 dnia. Zostawić (koszt zerowy) do czasu, aż O1 potwierdzi, że archiwum
   uzupełnia się codziennie; wyłączenie = decyzja użytkownika (zadanie na jego maszynie).
3. **ETH/SOL/BNB `metrics`** — pobrać dopiero, gdy O1 da wynik na BTC (zasada 9).
4. **Metodologicznie (wniosek 59):** sonda źródła sprawdza WSZYSTKIE kanały dystrybucji
   (REST, archiwum plików, dumpy), nie jeden — P1 skreśliło klasę danych po jednym.

## Użyte skille

Rejestr gałęzi `p3-zrodla-danych` (`py tools/skill_audit.py raport --galaz p3-zrodla-danych`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura sondy: gałąź → skille → pre-rejestracja bramy → pobranie → profil → bramki → DoD |
| `anthropic-skills:clas5-quant` | rozróżnienie: co jest nową hipotezą z licznikiem (O1, X1, VRP…), a co analizą ryzyka wyniku dodatniego (D1); rachunek mocy ze SWOJĄ historią; masa punktowa (wniosek 15) |
| `anthropic-skills:quant-strategy-catalog` | mapa „źródło → rodzina" (pięć pól), brama danych G1–G4, mechanizm „kto traci" dla każdej rodziny |
| `engineering:testing-strategy` | plan testów PRZED kodem: parsery bez sieci, µs/ms, dedupe keep-last, `date_chunks` (hypothesis), idempotencja, fail loud |
| `security-review` | nowe połączenia sieciowe: 1 znalezisko Medium (adres z odpowiedzi serwera) → poprawka + 2 testy PRZED scaleniem |
| `data:explore-data` | profil 13 zbiorów: ziarno, luki, duplikaty, pokrycie bazy, masa punktowa, acf1, spójność OI×cena |
| `data:validate-data` | bramka 16a: 634 = luki, zgodność archiwum↔REST, „kogo nie ma", oba red flagi |
| `data:statistical-analysis` | bramka 16b: pokrycia jako licznik/mianownik, acf1 jako wskazówka N_eff, szkic mierzalności bez sygnału |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Z tabeli zasady 19 pominięte: `dataviz` (bez wykresów), `engineering:architecture` (bez
decyzji architektonicznej — nowy katalog cache to konwencja `data/raw/`), `update-config`,
`ta-toolkit`, `lean-research`.
