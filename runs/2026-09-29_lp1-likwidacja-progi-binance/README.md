# LP1 — cena likwidacji: płaski próg dziennika wobec progów depozytu Binance i ceny mark (2026-09-29)

> **STATUS: ZAKOŃCZONA — Poprawki NIE proponujemy.** Przy nominale 10 tys. USDT na monetę model Binance (progi
> depozytu z migawki + cena mark) daje prawie tyle samo likwidacji co dziennik: **2× +1,4 %** (1 530 → 1 552;
> 95 % [−2,4; +6,5]), **3× −2,1 %** (4 578 → 4 482; 95 % [−4,6; +0,5]) — daleko od progu 10 % z pre-rejestracji.
> Efekty się znoszą: shortów Binance likwiduje więcej (+3…+4 %), longów mniej (−5…−9 %: łagodniejszy próg
> i cena mark bez knotów).
> Post hoc: przy 100 tys. USDT na monetę różnica rośnie do +14…+17 %. Pre-rejestracja `fe2a98d`.
> **0 wariantów — POZA licznikami**, 0 odczytów zwrotu. Walidacja: **Caveats**; przegląd kodu: **Approve**.
> Zadanie 017 tablicy, typ `przeglad`, decyzja użytkownika 2026-09-29: „tak wrzuć na tablicę z zadaniami”.

## W skrócie — prostym językiem (zasada 17)

Dziennik liczy likwidację najprościej: pozycja z dźwignią 2× znika, gdy cena pójdzie przeciw niej o 49 %, a przy 3× —
o 32,3 %. To „płaski próg” (1/dźwignia − 1 %). Binance liczy inaczej w dwóch miejscach:

1. **Wymagany depozyt zależy od monety i wielkości pozycji** (tabela progów; „MMR” to procent pozycji, który musi
   zostać na koncie). Dla BTC to 0,4 %, dla małych altów 2–5 %, a dla dużych pozycji na małych altach nawet 10–17 %.
   Do tego wzór Binance liczy depozyt od ceny w chwili likwidacji. Przez to **short** jest likwidowany trochę
   wcześniej, niż zakłada dziennik. Mediana przy 10 tys. USDT: 30,8 % zamiast 32,3 % (3×). **Long** jest likwidowany
   trochę później: 32,7 % zamiast 32,3 %.
2. **Likwidację wyzwala cena mark** (wygładzona cena z indeksu kilku giełd), a nie ostatnia transakcja. Krótkie knoty
   (gwałtowne, chwilowe spadki ceny) na jednej giełdzie liczą się słabiej.

Sprawdziliśmy oba efekty na koszyku top-20 od 2021 roku (195 monet, 65 miesięcy). Wynik: przy pozycji rzędu
10 tys. USDT na monetę **oba efekty prawie się znoszą**. Łączna liczba likwidacji różni się o −2 % do +1,4 %.
Dziennik ma więc właściwy rząd wielkości: **nie warto proponować Poprawki**. Zmienia się tylko podział. Dziennik
trochę zawyża likwidacje longów (o 5–9 %) i trochę zaniża likwidacje shortów (o 3–4 %).

Zastrzeżenie na przyszłość: przy pozycjach **ok. 100 tys. USDT na monetę** progi Binance są wyraźnie ostrzejsze. Model
Binance daje wtedy o **14–17 % więcej** likwidacji niż dziennik. Tego nie było w pre-rejestracji; policzono to
na dzisiejszych progach. Przy takim kapitale sprawa wraca.

## Metadane

- **ID:** LP1 (zadanie 017, `zadania/017-likwidacja-progi-binance.md`). Gałąź `zadanie-017-likwidacja-progi-binance`
  od `master` `43bbe4a`.
- **Sieć:** wyłącznie (1) `raw.githubusercontent.com` — migawka `freqtrade/exchange/binance_leverage_tiers.json`
  z kopii `piotrgebala/freqtrade`, commit `84b4628`; (2) `data.binance.vision` — publiczne archiwum
  `markPriceKlines` 1d. Bez `leverageBracket`, bez kluczy, bez narzędzi handlowych, bez importu freqtrade.
- **Kod (nowy, poza łańcuchem dziennika):** `backtest/liq_binance.py` (wzór Binance przepisany samodzielnie + liczniki
  przekroczeń), `data/fetch_mark_1d.py` (kolektor mark), `backtest/run_lp1_likwidacja_progi.py` (skrypt rundy),
  testy `tests/test_liq_binance.py`. Nie zmienia `backtest/live_journal.py`, `backtest/ts_momentum.py` ani MMR.
- **Dane:** skład koszyka top-20 point-in-time z `data/raw/universe_full` (`rebalance_premium.monthly_members`,
  miesiące 2021-02 … 2026-06); cena ostatnia (high/low/close 1d) z `data/raw/universe_ohlc_full/ohlc_1d.parquet`
  (ten sam kolektor co RU1); cena mark z `data/raw/mark_1d/mark_1d.parquet` (nowy). Dane od 2021-01-01 (zasada 20).
  Nie czytamy `dziennik/*.csv`. Moduły dziennika są tylko IMPORTOWANE do odczytu (`rebalance_premium.load_universe`,
  `monthly_members`; `fetch_external.http_get` i parsery), bez zmian.
- **Komenda (z katalogu głównego repo; przebieg ok. 5 s, pobranie mark kilka minut):**

  ```
  gzip -dc runs/2026-09-29_lp1-likwidacja-progi-binance/binance_leverage_tiers.json.gz \
      > data/raw/binance_tiers/binance_leverage_tiers.json          # migawka progów (albo pobranie z hashe.txt)
  PYTHONUTF8=1 py -m data.fetch_mark_1d data/raw/universe_full        # cena mark 1d → data/raw/mark_1d/
  PYTHONUTF8=1 py -m backtest.run_lp1_likwidacja_progi               # → raw_output.txt, *.csv w tym katalogu
  ```

  Przebieg rundy szedł w worktree, więc ścieżki do danych, których worktree nie ma, podano jawnie:
  `--universe-dir /home/dantey1/alpha/data/raw/universe_full --ohlc
  /home/dantey1/alpha/data/raw/universe_ohlc_full/ohlc_1d.parquet`. Dwa kolejne przebiegi dały bajt w bajt ten sam
  `raw_output.txt` (`cmp`).
- **Hashe (pełna lista: `hashe.txt`):** migawka progów sha256 `5db817c14ee5fc077d7ae9f325a93c87cd032d3ba24c1ae5ea47c98417608353`
  (2 694 759 B; kopia `binance_leverage_tiers.json.gz` w tym katalogu). Plik mark `09047a88…`, treść `40ec6acb…`.
  Cena ostatnia `0ed37974…`, treść `0e421807…`.
- **Commity:** pre-rejestracja `fe2a98d` (przed krokiem 2), log pobrania mark `eea3049`, wyniki `924ea7d`, write-up —
  commit tej wersji README.
- **Artefakty:** `raw_output.txt` (pełny stdout), `progi_per_moneta.csv` (krok 1: 187 monet × 3 nominały),
  `przekroczenia.csv` (krok 2: każda komórka z przekroczeniem w którymkolwiek z 4 modeli, 7 327 wierszy),
  `fetch_mark_output.txt` (log kolektora), `hashe.txt`, `binance_leverage_tiers.json.gz`.

## Poprzedzające wyniki

- **LQ1 (wniosek 76):** likwidacja izolowana przy 3× kosztuje trend ~3,6 pkt/rok, 4,75 % pozycji-tygodni; przy 2×
  ~1,6 pkt. Model LQ1 zapisał z góry dwa uproszczenia: MMR 1 % dla wszystkich monet („konserwatywnie dla altów; BTC
  ma 0,4 %”) i ekstrema ceny OSTATNIEJ („knoty — konserwatywnie wobec ceny mark”). LP1 sprawdza właśnie te dwa
  słowa „konserwatywnie” — nic więcej.
- **RU1/RU2:** pełne uniwersum (`universe_full`) i OHLC członków — z nich bierzemy skład i ceny ostatnie.
- **Wniosek 107 / `runs/odczyty_historii.csv`:** każdy nowy odczyt zwrotu podnosi poprzeczkę; dlatego LP1 nie liczy
  zwrotu, a wiersza do rejestru odczytów nie dopisujemy (liczba przekroczeń progu to nie odczyt zwrotu strategii).
  **Korekta po pomiarze:** strażnik `tests/test_odczyty_guard.py` wymaga wiersza dla KAŻDEGO katalogu rundy, więc
  dopisano wiersz 59: `opis-z-wynikiem`, `odczyt_programu = nie`, 0 wariantów (N się nie zmienia).
  Skrypt `backtest/dsr.py` z `--k 0`: N = 40 (AU4) / 52, próg t dla DSR 0,95 przy N + 1: 3,84 / 3,94 — bez znaczenia dla
  LP1, bo runda nie ocenia przewagi.
- Wnioski skumulowane dotyczące tej rundy: 76 (koszt likwidacji w trendzie) i 83 (RU2: werdykty odporne na korektę
  danych) — z nich wynika, że LP1 ma powiedzieć, czy uproszczenia LQ1 przesuwają LICZBĘ likwidacji, a nie przeliczać
  wyniku trendu.

## Pre-rejestracja (0 wariantów; zapisana przed krokiem 2)

**Wzór Binance** (izolowana, jedna pozycja, tryb jednokierunkowy; `backtest/liq_binance.py`):
odległość do likwidacji jako ułamek ceny wejścia = `(1/L + cum/N − MMR) / (1 ∓ MMR)` (− long, + short), gdzie MMR
i `cum` (maintenance amount) pochodzą z progu, do którego wpada nominał N. Nasz próg: `1/L − 1 %` (2× → 49 %,
3× → 32,33 %).

**Krok 1 (progi):** zbiór monet = suma składów top-20 z miesięcy 2021-02 … 2026-06. Dla każdej monety, N ∈ {1 tys.,
10 tys., 100 tys. USDT}, L ∈ {2, 3}, long i short: MMR, cum, odległość Binance, różnica wobec naszego progu (w pkt
procentowych). Monety bez progów w migawce (wycofane) → „BRAK W MIGAWCE”, liczone osobno, nie zgadywane.
Ograniczenie: migawka to progi z 2026-06-18, nie historyczne.

**Krok 2 (przekroczenia):** komórka = (moneta, dzień wejścia t), moneta w koszyku w miesiącu dnia t. Wejście po
zamknięciu dnia t po cenie ostatniej. Okno h ∈ {1 dzień, 7 dni} (7 = trzymanie trendu TS1, `HOLD_DAYS`), dni t+1…t+h.
Long „likwidowany”, gdy min(low)/wejście − 1 ≤ −próg; short, gdy max(high)/wejście − 1 ≥ próg. Cztery zestawy na
każde (h, L, strona): próg {nasz płaski, Binance przy N = 10 tys.} × ekstremum {ostatnia, mark}. Raport: tabela 2×2
„tylko ostatnia / tylko mark / obie / żadna” dla każdego progu, liczba dni i monet, plus braki mark.
Komórki bez pełnego okna w którymkolwiek szeregu wypadają (raportowane).

**Reguła decyzji (z góry):** porównujemy liczbę likwidacji „model dziennika” (próg płaski, cena ostatnia) z „model
Binance” (próg Binance N = 10 tys., cena mark), sumarycznie long + short, przy h = 7. Jeśli różnica względna
≥ 10 % przy 2× LUB 3× — rekomendujemy użytkownikowi rozważenie Poprawki (decyzja i tak należy do niego). Poniżej 10 %
— nie warto. Kierunek (zawyża / zaniża) raportujemy zawsze. Mierzalność (zasada 18): nie dotyczy — brak trafności
i zwrotu; liczymy zdarzenia, nie estymujemy przewagi.

**Druga droga (bramka 16a):** trzy przypadki przeliczone ręcznie w README (odległość z ceny LP, ekstrema z surowych
wierszy) + przeliczenie łącznej liczby przekroczeń inną drogą (pętla po wierszach zamiast macierzy).

---

## Wynik — krok 1: progi depozytu (migawka z 2026-06-18)

Zbiór: **195 monet** było w koszyku top-20 w którymś z 65 miesięcy (2021-02 … 2026-06). **187 ma progi w migawce.**
Odległość do likwidacji (ruch ceny przeciw pozycji, % ceny wejścia) według wzoru Binance. Nasz próg to 49,00 % (2×)
i 32,33 % (3×), taki sam dla longa i shorta. Pełna tabela: `progi_per_moneta.csv` i `raw_output.txt`.

| moneta (mies. w top-20) | nominał USDT | MMR % | cum USDT | 2× long | 2× short | 3× long | 3× short |
|---|---|---|---|---|---|---|---|
| **dziennik (płaski)** | dowolny | 1,00 | 0 | **49,00** | **49,00** | **32,33** | **32,33** |
| BTC (65) | 1 tys. / 10 tys. / 100 tys. | 0,40 | 0 | 49,80 | 49,40 | 33,07 | 32,80 |
| ETH (65) | 1 tys. / 10 tys. / 100 tys. | 0,40 | 0 | 49,80 | 49,40 | 33,07 | 32,80 |
| SOL (62) | 1 tys. / 10 tys. | 0,50 | 0 | 49,75 | 49,25 | 33,00 | 32,67 |
| SOL | 100 tys. | 0,65 | 75 | 49,75 | 49,11 | 32,97 | 32,55 |
| XRP (65) | 1 tys. / 10 tys. | 0,50 | 0 | 49,75 | 49,25 | 33,00 | 32,67 |
| XRP | 100 tys. | 1,00 | 360 | 49,86 | 48,87 | 33,02 | 32,37 |
| DOGE (61) | 1 tys. / 10 tys. | 0,65 | 0 | 49,67 | 49,03 | 32,90 | 32,47 |
| DOGE | 100 tys. | 1,00 | 280 | 49,78 | 48,79 | 32,94 | 32,29 |
| 1000PEPE (33) | 1 tys. / 10 tys. | 0,65 | 0 | 49,67 | 49,03 | 32,90 | 32,47 |
| 1000PEPE | 100 tys. | 1,00 | 70 | 49,57 | 48,58 | 32,73 | 32,08 |
| WIF (16) | 1 tys. | 1,00 | 0 | 49,49 | 48,51 | 32,66 | 32,01 |
| WIF | 10 tys. | 2,00 | 75 | 49,74 | 47,79 | 32,74 | 31,45 |
| WIF | 100 tys. | 3,33 | 1 155 | 49,47 | 46,28 | 32,23 | 30,15 |
| AXS (10) | 10 tys. | 2,00 | 75 | 49,74 | 47,79 | 32,74 | 31,45 |
| AXS | 100 tys. | 5,00 | 1 450 | 48,89 | 44,24 | 31,35 | 28,37 |

Przekrój 187 monet — mediana odległości Binance (%) i liczba monet, dla których Binance likwiduje **wcześniej** niż
dziennik (odległość mniejsza od płaskiego progu):

| nominał | 2× long | 2× short | 3× long | 3× short |
|---|---|---|---|---|
| 1 tys. | 49,24 (39 monet wcześniej) | 47,78 (161) | 32,32 (97) | 31,36 (161) |
| 10 tys. | 49,74 (17) | 47,07 (172) | 32,74 (35) | 30,81 (166) |
| 100 tys. | 48,74 (118) | 43,48 (183) | 31,19 (143) | 27,60 (182) |

Najdalej od progu: shorty przy 100 tys. na monetach, których dzisiejsze progi są małe (np. ARC, ARIA, 1000RATS: MMR
16,7 %, odległość 2× short 32,8–34,5 % zamiast 49 %; różnica do −16,2 pp). Co z tego wynika: **dla shortów płaski
próg dziennika jest za łagodny prawie zawsze** (w mianowniku wzoru Binance jest 1 + MMR). Dla longów przy
1–10 tys. jest lekko za surowy. Każda dopuszczalna dźwignia progu to co najmniej 3× (najniższa: 3× u 26 monet
przy 100 tys.), więc 2× i 3× są wszędzie dozwolone.

**BRAK W MIGAWCE (8 monet; progów nie zgadujemy ani nie podstawiamy następców):** MATIC (29 mies. w top-20; migawka
ma POL), EOS (14), LUNA (9; LUNA2 to inna moneta), TOMO (3), FRONT (1), HNT (1), RNDR (1; migawka ma RENDER)
i 币安人生 (1). Ta ostatnia ma w `data/raw/universe_full` na serwerze nazwę pliku w złym kodowaniu (cp866,
„х╕БхоЙф║║чФЯUSDT”; dotyczy 4 plików z chińskimi nazwami). Skład koszyka ma więc zniekształcony symbol. Nie znalazł
go ani kolektor mark (404), ani migawka, a z ceną ostatnią (poprawna nazwa w `universe_ohlc_full`) się nie łączy.
Skutek dla LP1: 1 moneta × 1 miesiąc wypada z kroku 2. **BRAK DANYCH — zgłaszam, nie naprawiam** (to plik
wspólnych danych, poza zakresem zadania).

## Wynik — krok 2: przekroczenia progu, cena ostatnia wobec mark

**Profil nowego archiwum (`data:explore-data`, sekcja 0 w `raw_output.txt`):** mark 50 506 wierszy, 194 symbole,
2021-01-01 … 2026-06-30, 0 duplikatów, 0 braków, 0 wartości ≤ 0, 0 świec z high < low. Cena ostatnia: 50 636 wierszy,
195 symboli. Wspólnych (symbol, dzień): 50 431. Tylko w cenie ostatniej: 205 (w tym 币安人生 61 dni, reszta to
pojedyncze dni z dziurami archiwum mark, np. 2021-07-01, 2022-10-02, 2023-02-24, 2026-06-29). Tylko w mark: 75.
Mark/ostatnia (zamknięcie): mediana 1,00000, p1–p99 0,9985–1,0015. Ogony (p0,1 = 0,775, min 0,006) to kontrakty
**wstrzymane albo wycofywane**, gdzie cena ostatnia stoi, a mark dalej się rusza: LUNA 2022-05-13, FTT 2022-12,
ALPACA 2025-05. Minimum ceny ostatniej jest niżej niż minimum mark w **96 % dni** (48 318 z 50 431; mediana o 0,077 %).
Maksimum ceny ostatniej jest wyżej niż maksimum mark w 85 % dni (mediana o 0,048 %). Knot ceny ostatniej jest więc
prawie zawsze, ale zwykle mniejszy niż 0,1 %.

Komórka = (moneta w koszyku, dzień wejścia). Okno 1 dzień: 38 982 ważne komórki (37 278 z progami). Okno 7 dni:
36 654 (35 070). Liczby poniżej: próg PŁASKI, wszystkie monety (`tylko last` = knot ceny ostatniej przekracza próg,
mark nie; `tylko mark` = odwrotnie). W nawiasie liczba różnych monet i dni.

| okno | dźwignia, strona | tylko last | tylko mark | oba | żadne |
|---|---|---|---|---|---|
| 1 d | 2× long | 7 (7 monet, 4 dni) | 32 (3 monety, 32 dni) | 44 | 38 899 |
| 1 d | 2× short | 3 (3, 3) | 0 | 67 | 38 912 |
| 1 d | 3× long | 32 (27 monet, 18 dni) | 46 (3 monety, 46 dni) | 136 | 38 768 |
| 1 d | 3× short | 10 (8, 10) | 2 (2, 2) | 210 | 38 760 |
| 7 d | 2× long | 29 (18, 21) | 31 (2, 31) | 444 | 36 150 |
| 7 d | 2× short | 34 (21, 32) | 1 (1, 1) | 1 071 | 35 548 |
| 7 d | 3× long | 156 (59 monet, 101 dni) | 39 (2, 39) | 1 903 | 34 556 |
| 7 d | 3× short | 56 (39, 54) | 8 (3, 8) | 2 683 | 33 907 |

Jak to czytać: „tylko last” to prawdziwy efekt knotów, rozłożony na wiele monet i skupiony w dniach krachu (3× long
1 d: 32 komórki, ale tylko 18 dni). „Tylko mark” to prawie wyłącznie **2–3 monety z zamrożoną ceną ostatnią**
(ALPACA, FTT, LUNA). Dziennik nie zobaczyłby tam żadnej likwidacji, bo cena ostatnia stoi w miejscu. To nie jest
knot, tylko wstrzymany handel (patrz post hoc).

**Reguła decyzji (pre-rejestracja): okno 7 dni, long + short, próg Binance przy 10 tys. USDT, 187 monet z progami:**

| dźwignia | dziennik (płaski, ostatnia) | tylko próg Binance | tylko cena mark | **model Binance (próg + mark)** | różnica | 95 % (bootstrap po miesiącach) |
|---|---|---|---|---|---|---|
| 2× | 1 530 (2,18 % okien) | 1 579 (+49) | 1 501 (−29) | **1 552** (2,21 %) | **+1,4 %** | [−2,4; +6,5] |
| 3× | 4 578 (6,53 % okien) | 4 627 (+49) | 4 435 (−143) | **4 482** (6,39 %) | **−2,1 %** | [−4,6; +0,5] |

Per strona (to samo okno, te same komórki): 2× long 461 → 440 (−4,6 %), 2× short 1 069 → 1 112 (+4,0 %);
3× long 1 967 → 1 785 (−9,3 %), 3× short 2 611 → 2 697 (+3,3 %). Rozkład 3× long: sama cena mark −5,1 %
(1 967 → 1 866), sam próg −3,6 %. Rozkład 3× short: sam próg +4,6 % (2 611 → 2 730), sama cena −1,6 %.
Po latach (3×): 2021 −7,2 %, 2022 −1,1 %, 2023 −0,9 %, 2024 −3,1 %, 2025 +3,5 %, 2026 +1,8 %. Po latach (2×):
od −5,4 % (2021) do +10,6 % (2025) — jedyny rok powyżej 10 %, przy małych liczbach (303 → 335).
P(|różnica| ≥ 10 %) w bootstrapie: 0,1 % (2×), 0,0 % (3×). **Wynik: poniżej progu decyzji przy obu dźwigniach.**

Uwaga o liczbach: okna 7-dniowe się nakładają, a jeden dzień krachu trafia do wielu komórek (do 7 dni × 20 monet).
Liczby to więc „pozycjo-okna”, a nie niezależne zdarzenia. Dlatego przedział liczę bootstrapem po miesiącach, a nie
po komórkach.

**Kontrola krzyżowa z LQ1:** LQ1 dał 4,75 % likwidowanych pozycjo-tygodni przy 3× dla pozycji trendu. Tutaj 6,5 %
dla wszystkich dni i obu stron naraz. Rząd wielkości się zgadza. Pozycje trendu częściej stoją po „dobrej” stronie
ruchu, więc niższa liczba w LQ1 jest spodziewana. To nie jest ten sam zbiór i nie ma być.

## Post hoc (dopisane po obejrzeniu wyniku, POZA regułą decyzji)

- **(a) Okna z zamrożoną ceną ostatnią** (high = low w którymś dniu okna): 67 komórek na ALPACA, BNX, FTT i TON.
  Bez nich, przy 10 tys.: 2× −0,7 % (1 525 → 1 515), 3× −3,0 % (4 571 → 4 436). Efekt ceny mark po wyłączeniu:
  −60 (2×) i −182 (3×) likwidacji, czyli −3,9 % i −4,0 %. Knoty ceny ostatniej zawyżają więc liczbę likwidacji
  w dzienniku o ok. 4 %. Osobna sprawa: w dniach wstrzymanego handlu dziennik nie widzi ani likwidacji, ani
  rozliczenia przy wycofaniu kontraktu. To inna luka niż MMR, poza zakresem zadania.
- **(b) Inny nominał** (bez zamrożonych okien): przy **1 tys.** 2× −2,2 %, 3× −3,6 %. Przy **100 tys.**
  **2× +15,0 %** (1 525 → 1 753), **3× +13,8 %** (4 571 → 5 203). Efekt progu przy 100 tys. to +286 i +822
  likwidacji, prawie całe po stronie shortów (3× short, sam próg: 2 605 → 3 244). Przy nominale ok. 100 tys. USDT na monetę
  płaski próg zaniżałby liczbę likwidacji o ok. 14–15 %. To ponad próg 10 %. Zastrzeżenie: to dzisiejsze progi.
  Monety, które były duże w 2021, a dziś są małe (AXS, 1INCH, ALICE…), miały wtedy łagodniejsze progi, więc ta
  liczba jest raczej górną granicą.

## Trzy przypadki przeliczone ręcznie (druga droga, surowe wiersze archiwów)

1. **Knot ceny ostatniej — GRTUSDT, wejście 2021-02-21, 3× long.** Zamknięcie 2,30699. Następny dzień: minimum ceny
   ostatniej 1,53575 → ruch 1 − 1,53575/2,30699 = **33,43 %** ≥ 32,33 % (płaski) i ≥ 32,74 % (Binance: MMR 2 %,
   cum 75 → (1/3 + 75/10 000 − 0,02)/0,98 = 0,320833/0,98 = **32,738 %**) → likwidacja. Minimum mark 1,5805762 →
   **31,49 %** < obu progów → brak likwidacji. Flagi w pliku: płaski/last TAK, płaski/mark NIE, Binance/last TAK,
   Binance/mark NIE. Zgadza się.
2. **Zamrożona cena ostatnia — FTTUSDT, wejście 2022-12-21, 2× long.** Cena ostatnia stoi na 1,59 (open = high =
   low = close) → ruch 0 %. Minimum mark następnego dnia 0,64420543 → 1 − 0,64420543/1,59 = **59,48 %** ≥ 49 %
   i ≥ 48,72 % (Binance: MMR 2,5 %, cum 0 → 0,475/0,975 = **48,718 %**). Flagi: tylko mark TAK. Zgadza się.
3. **Efekt progu — WAVESUSDT, wejście 2022-05-03, 3× short.** Zamknięcie 11,96. Maksimum ceny ostatniej następnego
   dnia 15,746 → 15,746/11,96 − 1 = **31,66 %**: poniżej płaskiego progu 32,33 % (dziennik: brak likwidacji),
   powyżej progu Binance (MMR 2,5 %, cum 50 → (1/3 + 0,005 − 0,025)/1,025 = 0,313333/1,025 = **30,569 %**).
   Maksimum mark 15,748269 → 31,67 % → Binance likwiduje także na mark. Flagi: Binance/last i Binance/mark TAK,
   płaskie NIE. Zgadza się.

Wzór kroku 1, ręcznie: BTC 10 tys. 2× long = (0,5 − 0,004)/(1 − 0,004) = 0,496/0,996 = **49,80 %** (tabela 49,80).
WIF 10 tys. 3× short = (1/3 + 75/10 000 − 0,02)/1,02 = 0,320833/1,02 = **31,45 %** (tabela 31,45). AXS 100 tys. 2× short =
(0,5 + 1 450/100 000 − 0,05)/1,05 = 0,4645/1,05 = **44,24 %** (tabela 44,24). Test jednostkowy
`tests/test_liq_binance.py` ma BTC ręcznie (2×, próg 1: 0,49799197 long, 0,49402390 short; 3×, próg 2 z cum 300:
0,33058626). Test `hypothesis` porównuje odległość z wprost policzoną ceną likwidacji. Osobny test sprawdza
z definicji, że w cenie likwidacji kapitał pozycji równa się wymaganemu depozytowi (N_mark·MMR − cum).

**Druga droga dla łącznych liczb** (pętla po surowych wierszach, własny wybór progu i wzór bez funkcji modułu):
h = 7 2× 1 530 / 1 552, h = 7 3× 4 578 / 4 482, h = 1 3× 371 / 414. Wszystkie **ZGODNE** z macierzami.

## Bramka 16a — walidacja (`data:validate-data`)

**Werdykt: Caveats** (do pokazania z zastrzeżeniami; błędów w rachunku nie ma).

- Przeliczenia drugą drogą: 3 przypadki ręcznie + 3 wzory + pętla po wierszach — wszystko zgodne; dwa przebiegi dały
  identyczny `raw_output.txt`.
- **Kogo nie ma w zbiorze:** 8 monet bez progów, w tym MATIC (29 miesięcy w top-20); 1 moneta z nazwą w złym
  kodowaniu. Wypadają też okna bez pełnych danych: przy 7 dniach 2 296 komórek bez pełnego okna ceny ostatniej i 471
  bez mark. To głównie ostatnie dni członkostwa, bo kolektory pobierają tylko miesiące członkostwa i miesiąc przed.
  Te okna mogą być ruchliwe (moneta wypada z top-20), więc liczba likwidacji jest raczej trochę zaniżona po obu
  stronach porównania jednakowo. Dni wstrzymanego handlu są w danych, ale z zamrożoną ceną (post hoc a).
- **Czerwona flaga „wynik idealnie potwierdza hipotezę”:** nie dotyczy. Przed pomiarem nie było kierunku oczekiwań.
  Wynik to dwa przeciwne efekty po ~4 %, które się znoszą. Znoszenie to zbieg liczb, nie prawo: przy 100 tys. już
  nie zachodzi.
- **Zastrzeżenia, które muszą iść z wynikiem:** (1) progi to migawka z 2026-06-18, nie historia; (2) próg Binance
  liczony dla stałego nominału przy wejściu (w rzeczywistości depozyt liczy się od nominału po cenie mark, a longowi
  w spadku nominał maleje); (3) pominięte opłaty i funding w depozycie izolowanym (jak w dzienniku); (4) wszystkie dni
  i obie strony, a nie pozycje dziennika — to przegląd progów, nie wynik strategii; (5) reguła decyzji tylko dla 10 tys.

## Co na plus (+) / Co na minus (−)

**(+)**
- Oba uproszczenia dziennika („MMR 1 %” i „cena ostatnia”) zmierzone osobno i razem, na tych samych komórkach,
  z przedziałem. Wynik jednoznaczny wobec progu zapisanego z góry.
- Kierunek per strona jest czytelny: dziennik zawyża likwidacje longów (knoty + za surowy próg), a zaniża likwidacje
  shortów (mianownik 1 + MMR). Przy 3× short Binance likwiduje od 30,8 % zamiast 32,3 % (mediana, 10 tys.).
- Wzór przepisany samodzielnie, z testem ręcznym, testem `hypothesis` i testem definicji; migawka zapisana z hashem.
- Przy okazji wykryto dwie luki danych: zamrożoną cenę ostatnią przy wstrzymaniu i wycofaniu kontraktu oraz złe
  kodowanie 4 nazw plików w `universe_full` na serwerze.

**(−)**
- Progi są dzisiejsze. Dla monet, które urosły albo zmalały, historyczne progi były inne. Nie ma darmowego źródła
  historii progów bez klucza API.
- MATIC (29 miesięcy w koszyku) bez progów. Krok 2 liczy go tylko w wersji z progiem płaskim (tabela „wszystkie
  monety”), a w regule decyzji go nie ma.
- Świece dzienne: przekroczenie stałego poziomu nie zależy od kolejności ruchów w ciągu dnia, ale przy wejściu
  po zamknięciu dnia pomijamy knot w samym dniu wejścia (tak samo robi dziennik).
- Wynik przy 100 tys. jest post hoc (poza regułą decyzji) i liczony na dzisiejszych progach.

## Wniosek

**Nie warto proponować Poprawki.** Przy nominale ok. 10 tys. USDT na monetę płaski próg 1 % i cena ostatnia
przesuwają łączną liczbę likwidacji w oknie tygodniowym o **+1,4 % przy 2×** (95 % [−2,4; +6,5]) i **−2,1 % przy 3×**
([−4,6; +0,5]). To daleko od progu 10 %, bo dodatkowe likwidacje shortów (sam próg Binance: +4,6…+7,1 %)
równoważą brakujące likwidacje longów (sam próg: −3,6…−5,9 %; sama cena mark bez knotów: do −5,1 %). Wraca to dopiero przy pozycjach rzędu 100 tys. USDT na monetę: post hoc, na dzisiejszych progach,
+14…+15 % likwidacji.

## Rekomendacja

1. **Bez zmian w dzienniku** (MMR 1 %, cena ostatnia). Decyzja o Poprawce należy do użytkownika; wynik jej nie
   uzasadnia przy obecnej skali.
2. **Warunek powrotu** (do zapisania w STATUS): jeśli nominał pozycji na jedną monetę przekroczy ok. 50–100 tys.
   USDT albo dziennik zacznie handlować małymi altami (MMR ≥ 2,5 %), trzeba zmierzyć próg per moneta i per nominał
   z migawki (`backtest/liq_binance.py` jest gotowy). Wtedy najpierw shorty.
3. **Do orkiestratora (luki danych, osobne zadania, nie ta runda):** (a) 4 pliki w `data/raw/universe_full` na
   serwerze mają nazwy w kodowaniu cp866 zamiast UTF-8; skład koszyka dostaje zniekształcony symbol; (b) dni
   wstrzymanego handlu i wycofania kontraktu (FTT 2022-12, ALPACA 2025-05, LUNA 2022-05): dziennik widzi zamrożoną
   cenę ostatnią i nie rozlicza ani likwidacji, ani ceny rozliczenia.
4. Ścieżka odwrotu: runda niczego nie zmienia w dzienniku. Usunięcie trzech nowych modułów i katalogu rundy przywraca
   stan sprzed zadania.

## Przegląd kodu (bramka 16c) — `engineering:code-review`

**Werdykt: Approve.** Nowy kod jest opisowy, poza łańcuchem dziennika, z testami. Po przeglądzie poprawiono trzy
rzeczy: `bracket` na pustej liście progów daje czytelny błąd; skrypt sprawdza ciągłość indeksu dni, bo okno liczy się
w wierszach; doszły 2 testy (`flagged_cells`, pusta lista progów). Wyniki po poprawkach bajt w bajt te same.
`security-review` (nowy kolektor sieciowy): brak podatności o pewności ≥ 8. Adres ma stały host i protokół
`https`, a symbol trafia do niego przez `quote(safe="")`. Zip jest czytany w pamięci, bez `eval` i `pickle`,
bez kluczy. Analiza bez subagentów (zasada tokenów, docs/rag/12).

## Użyte skille (CLAUDE.md zasada 19)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-09-29T09:20:54+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` |  |
| 2026-09-29T09:20:56+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` |  |
| 2026-09-29T10:01:56+00:00 | claude (agent: general-purpose) | `data:explore-data` |  |
| 2026-09-29T10:26:51+00:00 | claude (agent: general-purpose) | `data:validate-data` |  |
| 2026-09-29T10:27:06+00:00 | claude (agent: general-purpose) | `data:statistical-analysis` |  |
| 2026-09-29T10:29:07+00:00 | claude (agent: general-purpose) | `engineering:code-review` |  |
| 2026-09-29T10:30:55+00:00 | claude (agent: general-purpose) | `security-review` |  |

Razem: 7 wczytań, 7 różnych skilli (wynik `py tools/skill_audit.py raport --galaz zadanie-017-likwidacja-progi-binance`).

- `clas5-runda` — kolejność: gałąź → skille → pre-rejestracja z regułą decyzji przed krokiem 2 → katalog, INDEX, wniosek.
- `clas5-quant` — ryzyko i sizing: likwidacja izolowana jako model depozytu, LQ1 jako punkt odniesienia, „0 wariantów,
  bez odczytu zwrotu”.
- `data:explore-data` — profil archiwum mark: pokrycie, dziury, ogony stosunku mark/ostatnia → wykrycie zamrożonych cen
  (FTT, ALPACA, LUNA).
- `data:validate-data` — „kogo nie ma w zbiorze” (8 monet bez progów, zła nazwa, ucięte okna), druga droga, werdykt Caveats.
- `data:statistical-analysis` — przedział bootstrapem po miesiącach (okna się nakładają), rozkład po latach zamiast
  jednej liczby.
- `engineering:code-review` — 3 poprawki (pusta lista progów, ciągłość indeksu, 2 testy), werdykt Approve.
- `security-review` — nowy kolektor sieciowy (moment z tabeli zasady 19), brak podatności.

Pominięte z tabeli: `quant-strategy-catalog` (brak nowej hipotezy), `dataviz` (brak wykresu),
`engineering:testing-strategy` (testy małego modułu pisane według wzoru z repo; moment „testy nowego modułu” był —
świadome pominięcie dla oszczędności kontekstu, testy pokrywają wzór ręcznie, `hypothesis` i definicją).
