# E1K — karta E1 (kaskady likwidacji) i rachunek mierzalności z realnej częstości, bez cen (2026-10-05)

> **Werdykt: NIEMIERZALNA. Runda (odczyt E1) nie startuje.** 0 wariantów zużytych, 0 odczytów E1. Licznik E1: 0/1.
> Karta: [`runs/DRAFT_E1.md`](../DRAFT_E1.md). Definicja kaskady i karta zostały zapisane w commicie `580092c`,
> PRZED policzeniem pierwszego zdarzenia (gałąź wypchnięta od razu, na dowód kolejności).

## W skrócie — prostym językiem (zasada 17)

- **Co to kaskada.** Kaskada to sytuacja, w której giełda w ciągu godziny przymusowo zamyka pozycje jednej strony
  (same longi albo same shorty) danej monety z koszyka top-20 za co najmniej 0,5 % jej średniego dziennego obrotu.
  Wtedy gramy przeciw zlikwidowanym (po wyprzedaży longów kupujemy) i trzymamy pozycję 24 godziny. Liczby progów
  zapisałem, zanim cokolwiek policzyłem, i już ich nie zmieniam.
- **Ile ich było.** Na Bybit (pełne dane, 7,1 dnia od 2026-09-27) **ani jednej**. Najbliżej progu był SUI: 53 %
  progu. Na Binance (tylko próbka, więc zaniżona) było 9 kaskad w 5 dniach z 9,4. Jeden spokojny tydzień niewiele
  mówi o roku, bo kaskady skupiają się w okresach paniki. Statystycznie z 0 w 7 dniach wynika najwyżej ok. 189 dni
  z kaskadą rocznie (górna granica 95 %).
- **Dlaczego to i tak nie wystarczy.** Badania (zadanie 026) sugerują odbicie ok. 0,75 % na epizod. Koszt wejścia
  i wyjścia w kaskadzie to ok. 0,5 %, więc na czysto zostaje 0,25 %. Ruch ceny w ciągu doby to ok. 5 %, czyli 20 razy
  więcej niż ten zysk. Żeby taki zysk odróżnić od przypadku, potrzeba ok. **1 540 dni z kaskadą** (przy szansie 50 %,
  że test go wykryje) albo **3 140** (szansa 80 %). Rok ma 365 dni. **Nawet gdyby kaskada była każdego dnia,
  wychodzi 4,2 roku (50 %) albo 8,6 roku (80 %). Przy górnej granicy częstości to 8,1 i 16,6 roku.**
- **Co z tego wynika.** W rozsądnym horyzoncie (3 lata) E1 nie da rozstrzygnięcia, więc odczytu nie robimy.
  Mierzalna w 3 lata byłaby tylko wtedy, gdyby odbicie było większe niż w badaniach (≥ 1,0–1,3 %) i kaskad było
  dużo (od ok. 50 do 260 dni w roku). Dziś tego nie wiemy. Zbieranie danych nic nie kosztuje, więc
  **rekomenduję zbierać dalej i powtórzyć rachunek z samych liczników 2026-12-27 (bez cen)**. Decyzja należy do
  użytkownika.

## Metadane

- **ID:** E1K. Zadanie tablicy 011 (typ `badawcze`); zgoda użytkownika 2026-09-29 „Wszystkie 008–014”; zależność 004
  zamknięta jako STOP (wn. 115). Gałąź `zadanie-011-e1-karta-z-czestosci` od `fe07a6e`.
- **Commity:** A `580092c`: karta (część A), `backtest/e1_kaskady.py`, testy, żadnego zdarzenia. B: rachunek,
  dokumentacja.
- **Komenda:**
  `PYTHONUTF8=1 py -m backtest.run_e1k_czestosc --bybit ~/likwidacje_bybit --binance ~/likwidacje --koszyk dziennik/koszyk.csv --do 2026-10-05`
  → `raw_output.txt`. Druga droga: `PYTHONUTF8=1 py runs/2026-10-05_e1k-karta-kaskad/druga_droga.py` →
  `raw_output_druga_droga.txt`.
- **Dane (tylko liczniki: czas, symbol, strona, nominał):** Bybit `~/likwidacje_bybit` dni zamknięte 2026-09-27 … 10-04
  (okres 2026-09-27 20:48 → 10-05 00:00 UTC = 7,133 dnia, 99 577 likwidacji, 0 złych linii); Binance `~/likwidacje`
  2026-09-25 … 10-04 (9,434 dnia, 333 011 liniowych, 1 501 COIN-M pominiętych). Uniwersum `dziennik/koszyk.csv`
  (2026-09 i 2026-10, po 20 monet). **Żadnej ceny po likwidacji, żadnych świec, żadnego zwrotu** (pole `p` tylko do
  nominału jednej likwidacji).
- **sha256 (16 znaków):** `backtest/e1_kaskady.py` `3ad100b9e8f1b815`, `backtest/run_e1k_czestosc.py` `b4f8f34cedc53778`.
- **Testy:** `tests/test_e1_kaskady.py` (16 testów, m.in. właściwość `hypothesis`: implementacja = niezależna naiwna
  O(n²) z tekstu karty), `tests/test_run_e1k_czestosc.py` (10 testów: tożsamość p > p\* ⇔ μ > C w `hypothesis`,
  granica dużego n, przebieg end-to-end na syntetycznych plikach). Bez sieci.

## Poprzedzające wyniki

- **LK0 (wn. 102), LB0 (wn. 106):** Bybit pełne, Binance próbka. Stąd sygnał z Bybit, Binance tylko jako dolna
  granica, jeden licznik E1.
- **LH0 (wn. 110, 115):** Hyperliquid bez kolektora, więc stan pozycji przed kaskadą może być tylko opisem.
- **Mapa 007 (`docs/mapa_hipotez_2026-10.md`):** E1 BRAK DANYCH. Najmniejszy efekt widoczny po roku (MDE) to 0,9–1,3 %
  przy σ 5 %, przy założonych 150–300 epizodach rocznie. Tu to założenie zastępuje częstość z liczników.
- **Zadanie 026 (`docs/przeglad_literatury_cp1_e1.md`):** efekt 0,75 % (0–1,3 %), koszt 0,3–1 %, liczby
  Miralles-Quirós tylko z indeksu wyszukiwarki (**niepewne**).
- **Wn. 96/107:** historia 2021–2026 wymaga t ≈ 3,84, ale E1 to nowe dane, więc własny licznik i t 1,96.
- Wariant równoważny nie istnieje: żadna runda nie mierzyła likwidacji jako zdarzenia (LQ1 i LP1 to likwidacje
  WŁASNYCH pozycji dziennika).

## Pre-rejestracja

Pełna treść: [`runs/DRAFT_E1.md`](../DRAFT_E1.md) §1–§12 (commit `580092c`). Skrót:
- **Definicja:** okno 60 min, próg θ = 0,5 % `sredni_obrot_30d`, horyzont i blokada monety 24 h, kierunek przeciw
  zlikwidowanym, wejście `floor_min(t*) + 2 min`. Obie strony naraz → pominięte. **3 wolne parametry z góry, 1 wariant.**
- **Kryterium:** t_neff > 1,96 średniego zwrotu netto dnia ORAZ ci_low(p) > p\* (próg uogólniony (L̄ + C)/(W̄ + L̄));
  C = 0,5 %; jednostka = dzień UTC wejścia.
- **Mierzalność (karta §9):** scenariusz rozstrzygający μ 0,75 %, σ 5 %, C 0,5 %, ρ 0,6; horyzont rozsądny ≤ 3 lata;
  test granicy dużego n.

## Wynik

### Częstość (bez cen)

| | Bybit (pełne, sygnał) | Binance (próbka, dolna granica) |
|---|---|---|
| okres | 7,133 dnia | 9,434 dnia |
| likwidacje w uniwersum | 12 754 (09) + 13 483 (10) | 40 519 + 25 500 |
| monety uniwersum bez żadnej likwidacji | PUMPUSDT (oba miesiące) | — |
| przerwy > 15 min (cały rynek) | 0 | 0 |
| **kaskady** | **0** (95 % Poisson: 0–3,7) | 9 (4,1–17,1) |
| dni z ≥ 1 kaskadą | 0 → **≤ 189 / rok** (górna granica 95 %) | 5 → 193 / rok [63; 451] |
| kaskady na miesiąc (30 d) | 0 (≤ 16) | 29 |
| najbliżej progu (suma w oknie / próg) | SUI long 0,526; XRP 0,482; LINK 0,470 | SUI 1,76; ZEC 1,65; DOGE 1,49 |
| strona | — | 8 long, 1 short |

Druga droga (niezależny kod: własne czytanie JSON, cumsum + searchsorted): Bybit 0, Binance 9 kaskad o tych samych
minutach i monetach. **Zgodne.** Zgodność Bybit z Binance (±60 min): 0/0, czyli nie da się ocenić.

**Dlaczego Bybit ma 0, a próbka Binance 9:** próg liczy się od obrotu na **Binance** (`koszyk.csv`), a Bybit jest
mniejszy. Likwidacje Bybit w tej samej godzinie to ok. 1/3 sumy z próbki Binance (SUI 0,53 wobec 1,76 progu).
Definicja jest więc na Bybit rzadka i łapie tylko duże kaskady. Zmiana źródła albo progu po tym wyniku to nowa karta,
czyli wariant 2 (karta §11). Nie zmienia też werdyktu poniżej, bo wąskim gardłem nie jest częstość.

### Mierzalność (scenariusz rozstrzygający: μ 0,75 %, σ 5 %, C 0,5 % → netto 0,25 %)

| częstość dni z kaskadą | n po 3 l. | `wald_half_width` | p / p\* / p_wykr | MDE netto (50 %) | werdykt |
|---|---|---|---|---|---|
| zmierzona (Bybit 0 / 7 d) | 0 | — | — | — | NIEMIERZALNA (brak n) |
| górna granica 95 % (189 / rok) | 566 | 4,12 pp | 0,560 / 0,528 / 0,570 | 0,41 % | **NIEMIERZALNA** (oba warunki) |
| każdy dzień (365 / rok, sufit jednostki) | 1 095 | 2,96 pp | 0,560 / 0,528 / 0,558 | 0,30 % | **NIEMIERZALNA** (zwrot; trafność tak) |

- `expected_trades(n_dni = 1 095, abstynencja = 1,0)` = 0 przy zmierzonej częstości. Dla górnej granicy:
  `expected_trades(1 095, 1 − 189/365)` = 566.
- **Potrzebne n:** 1 537 dni z kaskadą (moc 50 %), 3 140 (moc 80 %). Ręcznie: (1,96 · 5 % / 0,25 %)² = 1 537. Żeby
  zdążyć w 3 lata, trzeba by 512 albo 1 047 dni z kaskadą rocznie, a rok ma 365 dni. **W 3 lata nieosiągalne przy
  żadnej częstości.**
- **Po ilu latach:** przy 365 / rok 4,2 roku (50 %) / 8,6 roku (80 %). Przy 189 / rok 8,1 / 16,6 roku. Przy
  zmierzonej częstości (0) nie da się podać czasu; trzeba częstości z dłuższego okna (kontrola 2026-12-27).
- **Scenariusze opisowe** (pełna tabela w `raw_output.txt`; to nie warianty):
  - μ 1,3 %, C 0,5 %, σ 5 %: n50 150, n80 307, czyli wystarczy ≥ 50 / 102 dni z kaskadą rocznie.
  - μ 1,0 %: n50 384 / n80 785, czyli 128 / 262 dni rocznie.
  - Przy C 1 % i μ 0,75 % albo μ ≤ C: nigdy, bo zwrot netto jest ≤ 0.
  - σ 8 % (rozrzut po kaskadzie) mnoży n przez 2,56.
- **Granica dużego n (n = 10⁶, σ 5 %, C 0,5 %):** próg uogólniony przepuszcza wtedy i tylko wtedy, gdy μ > C
  (μ 0,45 %: nie; 0,55 %: tak), czyli nie karze celu rundy. **Uproszczony** 0,5(1 + C/B) wymagałby μ > 0,789 %
  = 1,577 × C (≈ π/2), czyli karałby każdą opłacalną regułę z μ między C a 1,58 C. Dlatego karta go nie używa.
  Tożsamość p > p\* ⇔ μ > C sprawdza test własności (300 przypadków).

## Co na plus (+) / Co na minus (−)

**+**
- Definicja kaskady i kryterium zapisane i wypchnięte PRZED pierwszym zliczeniem (`580092c`). Częstość nie mogła
  wpłynąć na progi, a ceny nie były oglądane wcale (licznik odczytów E1 = 0).
- Werdykt nie zależy od niepewnej częstości. Nawet kaskada każdego dnia nie daje mierzalności w 3 lata, bo blokuje
  stosunek zysku netto (0,25 %) do dobowego rozrzutu (5 %).
- Druga droga (niezależny kod) zgadza się co do minuty. Kolektor Bybit bez przerw > 15 min. 0 złych linii.
- Pokazany i przetestowany problem progu uproszczonego w granicy dużego n.

**−**
- Częstość z 7 dni spokojnego rynku: 0 zdarzeń daje tylko górną granicę. Prawdziwy roczny rozkład kaskad (paniki
  skupione w czasie) jest nieznany.
- Próg liczony od obrotu Binance przy sygnale z Bybit. To mój błąd projektu karty: na Bybit definicja jest ok. 3×
  ostrzejsza, niż wynika z jej opisu („12 % obrotu godziny”). Nie poprawiam go, bo karta zakazuje zmian po zliczeniu.
- σ (5 % / 8 %), ρ (0,6), rozkład normalny i N_eff = n to założenia, nie pomiary (ceny zakazane). Kolejne dni
  z kaskadą nachodzą na siebie (24 h), więc N_eff < n i liczby lat są **optymistyczne**.
- PUMPUSDT z koszyka nie ma na Bybit pod tą nazwą (bez mapowania nazw). Uniwersum ma tam 19 monet.

## Bramki jakości

- **16a (`data:validate-data`): Caveats.**
  - Druga droga: liczba kaskad (0 / 9, te same minuty) policzona niezależnym kodem; n50 = 1 537 policzone ręcznie.
  - Kogo nie ma w zbiorze: PUMPUSDT na Bybit, dni sprzed 2026-09-27 20:48 (Bybit), okresy paniki (próba
    z jednego spokojnego tygodnia), kontrakty COIN-M (pominięte), Hyperliquid (brak źródła).
  - Czerwona flaga „wynik idealnie potwierdza hipotezę”: nie dotyczy. Wynik jest negatywny dla odczytu, a 0 zdarzeń
    sprawdziłem drugą drogą i ilorazem najbliższym progu (0,53).
  - Zastrzeżenia: częstość tylko jako górna granica; σ i efekt to założenia; lata optymistyczne (N_eff = n).
- **16b (`data:statistical-analysis`):** liczności z przedziałem Poissona 95 %; zakresy scenariuszy (μ 0–1,3 %,
  σ 5–8 %, C 0,3–1 %) w całości w `raw_output.txt`; dla Binance mediana ilorazu do progu 1,012 (min 1,004,
  maks 1,126) — kaskady ledwo nad progiem. Licznik wariantów 0/1 przy każdej liczbie.
- **16c:** przegląd diffu przed scaleniem robi orkiestrator.

## Wniosek

E1 w tej definicji jest **NIEMIERZALNA** w rozsądnym horyzoncie. Przy efekcie z badań (0,75 %) i koszcie 0,5 % trzeba
1 537–3 140 dni z kaskadą, czyli co najmniej 4,2 roku, i to tylko wtedy, gdyby kaskada była każdego dnia. Przy
górnej granicy częstości z Bybit (189 dni / rok) to 8–17 lat. Na Bybit w 7 dniach nie było żadnej kaskady. Mierzalność
w 3 lata wymagałaby efektu ≥ 1,0–1,3 % i dziesiątek do setek dni z kaskadą rocznie. **Runda (odczyt) nie startuje.**
Licznik E1 zostaje 0/1, a wariant nie jest zużyty.

## Rekomendacja

1. **Nie robić odczytu E1** (zestawienia z cenami) według karty §10.
2. **Zbierać dalej** (LK0 + LB0, koszt ~0) i 2026-12-27 powtórzyć `run_e1k_czestosc` na 3 miesiącach liczników, bez
   cen. Jeśli wymagany czas w scenariuszu rozstrzygającym przekroczy 5 lat od startu LB0, rekomendacja brzmi:
   **zamknąć E1 bez odczytu** (karta §10). Przy dzisiejszych liczbach (≥ 4,2 roku nawet przy 365 dniach) to
   najbardziej prawdopodobny wynik.
3. Inne źródło sygnału (np. próbka Binance, częstsza) albo inny próg to **nowa karta = wariant 2**, wyłącznie decyzją
   użytkownika. Nie ratuje to scenariusza rozstrzygającego, bo blokadą jest stosunek zysku netto do rozrzutu, nie
   częstość.
4. **Decyzja użytkownika:** (a) zbierać i kontrola 2026-12-27 — rekomenduję; albo (b) zamknąć E1 już teraz.

## Użyte skille

### Użyte skille — gałąź `zadanie-011-e1-karta-z-czestosci` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-10-05T17:50:06+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` |  |
| 2026-10-05T17:50:07+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` |  |
| 2026-10-05T17:50:08+00:00 | claude (agent: general-purpose) | `anthropic-skills:quant-strategy-catalog` |  |
| 2026-10-05T18:06:54+00:00 | claude (agent: general-purpose) | `data:validate-data` |  |
| 2026-10-05T18:06:54+00:00 | claude (agent: general-purpose) | `data:statistical-analysis` |  |

Razem: 5 wczytań, 5 różnych skilli: `anthropic-skills:clas5-quant`, `anthropic-skills:clas5-runda`, `anthropic-skills:quant-strategy-catalog`, `data:statistical-analysis`, `data:validate-data`.

- `clas5-runda`: kolejność „karta → commit → zliczenie”, katalog rundy, wiersz w INDEX, wniosek, rejestr odczytów.
- `clas5-quant`: `oczekiwane_n` z częstości zdarzenia (reguła bez modelu), dwa warunki kryterium, sprawdzenie
  w granicy dużego n (wykryło karanie celu przez próg uproszczony), N_eff ≤ n.
- `quant-strategy-catalog`: pięć pól karty, mechanizm „ktoś MUSI handlować”, własny licznik nowych danych (t 1,96).
- `data:validate-data`: druga droga liczby kaskad, „kogo nie ma w zbiorze”, werdykt Caveats.
- `data:statistical-analysis`: przedziały Poissona dla liczności, zakresy scenariuszy zamiast jednej liczby.
- Pominięte z tabeli zasady 19: `data:explore-data`, bo zbiory LK0/LB0 profilowały już rundy LK0/LB0 (tu tylko
  przerwy i złe linie); `engineering:testing-strategy`, bo testy budowałem według wzorca `tests/test_liquidation_index.py`;
  `engineering:code-review` należy do orkiestratora (16c); `dataviz`, bo nie ma wykresu.
