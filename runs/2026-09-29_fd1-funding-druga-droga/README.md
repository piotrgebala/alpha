# FD1 — skrót silników w liczeniu fundingu jest pomijalny; liczba X1 z planu mierzy ruinę pozycji, nie funding (2026-09-29)

> **STATUS: ZAMKNIĘTA (opisowo, 0 wariantów).** Funding liczony rozliczenie po rozliczeniu wobec silnika
> (dzienna suma stawek × waga z początku dnia): **TS1 −0,004 %/rok [−0,042; +0,033]** — pomijalne (0,5 % kosztu
> wykonania z KO1). **X1:** liczba z pre-rejestracji **+23,6 %/rok [−0,4; +71,3]** — według reguły nierozstrzygnięta,
> w 99 % z jednego epizodu (MYX, wrzesień 2025), w którym pozycja o stałej ilości traci cały kapitał fazy;
> **na wagach silnika (diagnostyka po wyniku) −0,17 %/rok [−0,62; +0,22]** — 5 % kosztu KO1. Wzoru fundingu
> w silnikach nie trzeba poprawiać. Do decyzji użytkownika: model pozycji X1 (silnik co dzień przywraca nogi, dziennik
> handluje raz w tygodniu). Bramki: 16a **Caveats**, 16c — sekcja „Bramki jakości”.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Funding to opłata, którą co 8 godzin (u części monet co 4 godziny albo co godzinę) płacą sobie kupujący i sprzedający
kontrakt wieczysty. Nasze silniki liczą ją w skrócie: sumują stawki z całego dnia i mnożą przez wielkość pozycji
z początku dnia. Giełda liczy każde rozliczenie osobno, od wartości pozycji w chwili rozliczenia. Sprawdziliśmy, ile ten
skrót zmienia w dwóch nogach dziennika: trendzie TS1 i momentum X1.

- **Trend TS1:** skrót przesuwa funding o 0,004 punktu procentowego rocznie. To 200 razy mniej niż koszt zleceń z KO1
  (0,8 %/rok). Skrót jest bezpieczny.
- **Momentum X1, sam wzór fundingu:** ok. 0,17 punktu rocznie, czyli 5 % kosztu zleceń X1 (3,3 %/rok). Też bez znaczenia.
- **Momentum X1, liczba z planu:** +23,6 punktu rocznie. Tu plan zmienił dwie rzeczy naraz: wzór fundingu i sposób
  trzymania pozycji (stała ilość przez tydzień, jak w dzienniku, zamiast codziennego przywracania nóg do połowy kapitału,
  jak w silniku). We wrześniu 2025 moneta MYX, na której X1 miał krótką pozycję, podrożała 12 razy w trzy dni, a stawka
  fundingu sięgała limitu −2 % na godzinę. Pozycja trzymana cały tydzień straciłaby cały kapitał tej części portfela,
  a opłaty liczone od kapitału bliskiego zera przestają mieć sens. To nie jest sprawa fundingu, tylko ryzyko ruiny,
  którego codzienne przywracanie nóg w silniku X1 nie pokazuje.
- **Trzy miejsca ryzyka:** rozliczenie o północy w dniu zmiany pozycji silnik liczy raz, tylko przypisuje je nowej
  pozycji zamiast starej (różnica 0,006–0,015 punktu rocznie); monety z rozliczeniem co 4 h lub co godzinę silnik liczy
  poprawnie (sumuje wszystkie rozliczenia dnia); brakujące stawki dotyczą 0,03 % dni pozycji i mogą zmienić wynik
  najwyżej o 0,001 punktu rocznie.

**Co z tego wynika dla decyzji:** wzoru fundingu w silnikach i w dzienniku nie trzeba zmieniać. Osobna sprawa do decyzji
użytkownika: czy silnik X1 ma nadal zakładać codzienne przywracanie nóg, skoro dziennik wykonuje X1 raz w tygodniu.

## ID i metadane

- **ID:** FD1. Zadanie 016 tablicy (`zadania/016-funding-druga-droga.md`, typ `przeglad`, decyzja użytkownika
  2026-09-29: „tak wrzuć na tablicę z zadaniami”). **0 wariantów** — nie odczytuje przewagi, tylko składową kosztu.
- **Gałąź:** `zadanie-016-funding-druga-droga` (z `master` `43bbe4a`).
- **Kod:** `backtest/funding_settlement.py` (czyste funkcje, testy `tests/test_funding_settlement.py`),
  `backtest/run_fd1_funding.py` (przebieg). Silniki `ts_momentum` / `xs_momentum` (łańcuch importów dziennika)
  **bez zmian** — importowane tylko do odczytu.
- **Dane (tylko z repo, bez sieci, od 2021-01-01 — zasada 20):** `data/raw/universe_full/*_1d.parquet` (zamknięcia dzienne),
  `*_funding.parquet` (każde rozliczenie osobno), `data/raw/universe_ohlc_full/ohlc_1d.parquet` (ekstrema dnia do
  likwidacji TS1), `data/raw/BTC-USDT-USDT_1h_…` i `_4h_…` (ceny w ciągu dnia — tylko BTC). Koniec bazy 2026-07-01.
- **Komenda:** `PYTHONUTF8=1 OMP_NUM_THREADS=4 py -m backtest.run_fd1_funding > runs/2026-09-29_fd1-funding-druga-droga/raw_output.txt`
  (ok. 4 min; w worktree bez danych potrzebne dowiązania `data/raw/universe_full`, `universe_ohlc_full` i dwóch plików BTC
  do katalogu danych głównego klonu — przebieg tylko czyta).
- **Commity:** pre-rejestracja `ab6ab0e` (przed jakąkolwiek liczbą różnicy); skrypt przebiegu `ffa13fa`; `raw_output.txt`
  `767a6b8` (SHA-256 `e1640941…c5b6ed4`). Okno: 7 faz wspólnie od 2021-02-08 do 2026-06-30 (1 969 dni), 675 symboli,
  504 pliki fundingu, 1 882 539 rozliczeń w oknie danych.

## Poprzedzające wyniki

- **KO1 (wniosek 99):** koszt wykonania taker: TS1 0,8 %/rok, CP1 1,5 %/rok, X1 3,3 %/rok — to jest skala, z którą
  porównujemy różnicę fundingu.
- **T1-diag (2026-09-22):** model fundingu „dyskretnie po rozliczeniach” wobec „ułamkowo” przesunął próg opłacalności
  BTC 4h o 0,022 pp — pomijalnie, ALE z zastrzeżeniem, że strategia jednostronna unieważnia wniosek. TS1 i X1 mają
  netto ekspozycję niezerową w wielu tygodniach, więc T1-diag nie przenosi się na nogi dziennika.
- **RU1 / LQ1 / X1F:** konfiguracja nóg jak w dzienniku (TS1 7 faz, dźwignia 2× z likwidacją izolowaną; X1 średnia 7 faz).
- Wnioski skumulowane dotyczące tej rundy: 99 (koszty KO1) i 61 (carry: funding jest realnym strumieniem pieniędzy);
  z nich wynika, że różnicę trzeba podać w %/rok kapitału nogi, w tych samych jednostkach co KO1.
- Runda nie powtarza żadnego wariantu: pierwszy pomiar sposobu liczenia fundingu w silnikach tygodniowych.

## Pre-rejestracja (przed obejrzeniem wyniku)

**Pytanie.** Czy uproszczenie silników (funding dnia = −w_początek_dnia · Σ stawek dnia) przesuwa koszt fundingu nóg
TS1 i X1 o wielkość porównywalną z kosztami wykonania z KO1?

**Dwie drogi (jedna noga = jeden szereg dzienny, średnia 7 faz jak w dzienniku):**

- **(a) silnik:** −Σ_i w_{d,i} · f_{d,i}, f = suma rozliczeń z `floor("D")` = d, NaN → 0 (dokładnie `phase_returns_liq`
  i `long_short_returns`; kontrola: odtworzenie kolumny funding silnika do 1e-12).
- **(b) rozliczenie po rozliczeniu (wzór giełdy i freqtrade: stawka × cena × ilość):** ilość stała od formowania
  (zlecenie raz na tydzień), opłata −q_i · P_i(s) · f_i(s) w chwili s, w jednostkach kapitału fazy z początku dnia.
  Granica 00:00 w konwencji **(wejście, wyjście]** — zlecenie dziennika składane jest po 00:00 UTC, więc rozliczenie
  o 00:00 w dniu zmiany płaci STARA pozycja. To jest liczba główna.
- **Ceny w chwili rozliczenia (przybliżenie ceny mark):** 00:00 = zamknięcie dnia (dokładnie). Poza północą:
  BTC — zamknięcie świecy 1h kończącej się w chwili s; pozostałe monety — **BRAK DANYCH** o cenie w ciągu dnia w repo,
  więc przybliżenie (1 + r_dnia)^(część doby) (geometryczna interpolacja zamknięć). Przybliżenie sprawdzone na BTC:
  1h wobec 4h wobec interpolacji.

**Rozbicie (b) − (a) na składowe (sumują się dokładnie):** (0) kontrola zerowa: wagi silnika, cena stała w dniu,
konwencja silnika → musi dać 0; (1) model ilości (X1: noga przywracana co dzień do 0,5 w silniku wobec stałej ilości;
TS1: 0 z konstrukcji); (2) dryf ceny w ciągu dnia; (3) przypisanie rozliczenia 00:00 (stara wobec nowej pozycji).

**Trzy miejsca ryzyka:**

1. Rozliczenie dokładnie o 00:00 w dniu zmiany pozycji: silnik liczy je RAZ (nowej pozycji); (b) liczy je RAZ (starej);
   wzór z przedziałem domkniętym [wejście, wyjście] liczy je DWA RAZY; „wcale” — sprawdzone, czy któraś droga je gubi.
   Podaję sumy obu przypisań w %/rok.
2. Monety z interwałem 4 h / 1 h: klasyfikacja per symbol-miesiąc po medianie odstępu rozliczeń; udział dni pozycji,
   udział |fundingu| (a) i udział różnicy (b) − (a) z takich monet.
3. Brakujące stawki: dni pozycji bez żadnego rozliczenia (silnik: 0), monety bez pliku fundingu, dni z mniejszą liczbą
   rozliczeń niż wynika z interwału, stawki NaN. Wartości brakujących stawek nie uzupełniam (BRAK DANYCH) — podaję
   liczbę i ograniczenie z góry: brakujące rozliczenia × mediana |stawki| × |waga|.

**Statystyka.** Różnica (b) − (a) w %/rok kapitału nogi = średnia dzienna × 365; przedział 95 % z bootstrapu blokowego
po tygodniach (bloki 7 kolejnych dni, 10 000 losowań, ziarno 20260929); mediana i zakres per rok kalendarzowy
(2021–2026, 2026 = I półrocze) i per moneta (wkład monety w %/rok kapitału). Druga droga liczby głównej: niezależna
implementacja w pandas w jednostkach „dolarowych” (ilość × cena, kapitał fazy z kolumny `gross` silnika, kolumna
funding wprost z silnika) wobec implementacji numpy na wagach.

**Reguła odczytu (z góry).** Próg porównywalności = 25 % kosztu KO1 danej nogi (TS1: 0,2 %/rok; X1: 0,83 %/rok).
- **Pomijalna:** cały przedział 95 % różnicy leży w ±progu.
- **Porównywalna z KO1:** |średnia| ≥ próg i przedział 95 % nie obejmuje zera.
- W pozostałych przypadkach: **nierozstrzygnięta** (z podaniem szerokości przedziału).
Ta sama reguła osobno dla wersji „dwa razy” (przedział domknięty) — jako ryzyko implementacji, nie realny koszt.

**Czego nie robię:** nie drukuję zwrotu netto, t ani Sharpe'a nóg; nie czytam `dziennik/*.csv`; nie importuję freqtrade
(wzór przepisany po swojemu); nie poprawiam silników. Rachunek mierzalności z zasady 18 nie dotyczy — runda nie
odczytuje przewagi; przyrządem jest przedział bootstrapu różnicy (jego szerokość raportuję).

**Rejestr odczytów (wspólne narzędzie `backtest/dsr.py` z `--k 0`, nie skrypt rundy):** 58 wierszy, 34 odczyty programu; N metodą AU4 = 40, z odczytami
0-wariantowymi 52. FD1: `opis-z-wynikiem`, `odczyt_programu = nie` (koszt fundingu nóg już odczytanych, bez związku
sygnału ze zwrotem), 0 wariantów.

---

## Wynik

Jednostka wszędzie: % kapitału nogi na rok (średnia dzienna × 365), portfel = średnia 7 faz na wspólnym oknie. Znak
składowej funding: + = noga otrzymuje, − = płaci. Przedziały: 95 %, bootstrap blokowy po tygodniach (10 000 losowań).
Pełny wydruk: `raw_output.txt`.

### Kontrole przyrządu (przed odczytem)

| kontrola | TS1 | X1 |
|---|---|---|
| (a) odtwarza kolumnę funding silnika (7 faz), max różnica dzienna | 6,5·10⁻¹⁹ | 6,9·10⁻¹⁸ |
| odtworzenie zwrotu brutto silnika (te same wagi), max różnica | 0 | 2,2·10⁻¹⁶ |
| kontrola zerowa: wagi silnika, cena stała w dniu, konwencja silnika − (a) | 0,000 %/rok (max 2·10⁻¹⁹) | 0,000 %/rok (max 1,4·10⁻¹⁷) |
| przypisanie rozliczeń do dnia: zaokrąglenie do minuty wobec `floor("D")` silnika | 0 różnych komórek | 0 |
| zamknięcie dnia BTC = zamknięcie świecy 1h o 24:00 | różnica 0 (n = 2 007) | — |
| druga droga liczby głównej (ilość × cena × stawka w pandas, (a) wprost z silnika) | −0,003956 = −0,003956 %/rok | +23,561394 = +23,561394 %/rok |
| druga droga D1 (złączenia pandas zamiast rozrzutu numpy) | −0,003956 = −0,003956 | −0,166246 = −0,166246 |

### Liczba główna (z pre-rejestracji) i rozbicie

| | TS1 | X1 |
|---|---|---|
| (a) silnik: dzienna suma × waga | −1,131 | +6,306 |
| (b) rozliczenie po rozliczeniu, (wejście, wyjście], stała ilość | −1,135 | +29,868 |
| **(b) − (a)** | **−0,004 [−0,042; +0,033]** | **+23,561 [−0,395; +71,321]** |
| (0) kontrola zerowa | 0,000 | 0,000 |
| (1) model ilości: stała ilość − waga silnika | 0,000 (z konstrukcji) | +23,233 [−0,279; +70,143] |
| (2) dryf ceny w ciągu dnia | −0,010 [−0,031; +0,010] | +0,583 [−0,180; +1,995] |
| (3) rozliczenie 00:00: stara zamiast nowej pozycji | +0,006 [−0,023; +0,035] | −0,255 [−0,871; +0,112] |
| (b2) − (a): przedział domknięty [wejście, wyjście] (granica dwa razy) | −0,076 [−0,127; −0,028] | +23,692 [−0,268; +71,439] |
| mediana dzienna × 365 | +0,005 | +0,033 |
| per rok: mediana; zakres | −0,009; [−0,054; +0,053] | +0,171; [−2,650; +127,523] |
| per faza (każda osobno): mediana; zakres | −0,002; [−0,028; +0,011] | +47,7; [−152,8; +115,4] |
| per moneta (195 z pozycją): mediana; zakres | 0,000; [−0,008; +0,004] | 0,000; [−0,204; +23,365] |

Lata (2021 od 8 lutego, 2026 = I półrocze) TS1: 2021 −0,054, 2022 +0,053, 2023 −0,005, 2024 −0,028, 2025 −0,012, 2026 (I półrocze) +0,040.
Lata X1: 2021 −0,050, 2022 +0,392, 2023 +0,700, 2024 −0,153, **2025 +127,523**, 2026 −2,650. Największy wkład X1:
**MYXUSDT +23,365 z +23,561** (61 dni pozycji); TS1: LAYERUSDT −0,008, BNBUSDT −0,006.

### Czerwona flaga X1 — co się stało (diagnoza przed interpretacją)

2025-09-06 → 09-08 MYX podrożał z 1,31 do 13,89 (×10,6; 09-08 +298 % w jednym dniu; od formowania ok. ×12), a 09-09
suma 24 rozliczeń godzinnych wyniosła −16,68 % (najniższe na limicie −2 %; sprawdzone ręcznie w pliku parquet). Fazy 1–5
X1 trzymały MYX w nodze krótkiej. W modelu stałej ilości kapitał fazy = 1 + Σ w·(cena/cena wejścia − 1) spada do zera
i niżej (minimum −0,39); wagi W = w·cena/kapitał wybuchają i zmieniają znak (Σ|W| do 977 kapitału). Opłata dzielona
przez kapitał bliski zera to artefakt, nie funding. Silnik X1 co dzień przywraca każdą nogę do 0,5 kapitału (waga
silnika MYX −0,2 do −0,37 zamiast rosnącej), więc takiego przejścia przez zero nie modeluje. Obie implementacje (numpy i dolarowa) dają tę samą liczbę — to nie błąd kodu,
tylko model pozycji, który w tym epizodzie przestaje obowiązywać (realne konto zostałoby wcześniej zlikwidowane).

### Diagnostyka PO WYNIKU (nie była w pre-rejestracji; nie zastępuje liczby głównej)

Dopisana po pierwszym przebiegu (commit `ffa13fa`), bo liczba główna X1 mieszała dwie rzeczy: wzór fundingu i model
pozycji. Dwie diagnozy, obie wydrukowane dla obu nóg:

| | TS1 | X1 |
|---|---|---|
| okresy trzymania z ruiną stałej ilości (kapitał ≤ 0 na koniec dnia); dni faz w nich | 0; 0 z 13 783 (min kapitału +0,859) | **5; 35 z 13 783** (min −0,388) |
| **(D1) każde rozliczenie osobno na WAGACH SILNIKA: (b′) − (a)** | **−0,004 [−0,042; +0,033]** | **−0,166 [−0,620; +0,221]** |
| — dryf ceny w ciągu dnia | −0,010 [−0,031; +0,010] | −0,181 [−0,579; +0,149] |
| — rozliczenie 00:00: stara zamiast nowej | +0,006 [−0,023; +0,035] | +0,015 [−0,131; +0,166] |
| — per rok: mediana; zakres | −0,009; [−0,054; +0,053] | −0,049; [−1,022; +0,223] |
| — mediana dzienna × 365 | +0,005 | +0,017 |
| — per moneta: mediana; zakres | 0,000; [−0,008; +0,004] | 0,000; [−0,124 MYX; +0,067] |
| (D2) liczba główna bez okresów ruiny (dni faz w ruinie wyzerowane w obu drogach) | −0,004 [−0,042; +0,033] | +0,120 [−0,423; +0,841] |
| — per rok: mediana; zakres | −0,009; [−0,054; +0,053] | +0,171; [−2,650; +1,066] |

D1 odpowiada wprost na pytanie zadania (czy skrót „dzienna suma × waga” przesuwa koszt fundingu) — model pozycji
silnika zostaje bez zmian, zmienia się tylko sposób liczenia opłaty. D2 zostawia stałą ilość, ale wyrzuca tylko okresy
z kapitałem ≤ 0; okresy z kapitałem bliskim zera (np. 2026: −2,65) nadal pompują wagi, więc D2 jest mniej czysta.

### Miejsce ryzyka nr 1 — rozliczenie dokładnie o 00:00 w dniu zmiany pozycji

Formowanie jest po zamknięciu dnia, czyli o 00:00 UTC — w tej samej chwili co rozliczenie. Liczba rozliczeń (suma 7 faz)
i ich wartość w %/rok:

| moneta w starej / nowej pozycji | TS1: n | silnik (nowa) | (b) (stara) | X1: n | silnik (nowa) | (b) stała ilość (stara) | D1 wagi silnika (stara) |
|---|---|---|---|---|---|---|---|
| w obu | 36 191 | −0,072 | −0,063 | 12 115 | +0,086 | +0,433 | +0,100 |
| tylko w nowej (silnik liczy, giełda nie) | 3 100 | +0,000 | 0 | 7 561 | +0,044 | 0 | 0 |
| tylko w starej (silnik: **wcale**, giełda liczy) | 2 410 | 0 | −0,000 | 7 559 | 0 | +0,082 | +0,041 |

- **Silnik liczy każde takie rozliczenie dokładnie RAZ** — ale od nowej pozycji. Monety wchodzące płacą w silniku
  rozliczenie, którego na giełdzie nie zapłacą (zlecenie idzie po 00:00), a monety wychodzące nie płacą w silniku
  rozliczenia, które na giełdzie zapłacą („wcale”). Netto: TS1 +0,006 %/rok, X1 (D1) +0,015 %/rok.
- **Dwa razy** liczyłby wzór z przedziałem domkniętym po obu stronach (każde formowanie = zamknięcie i ponowne otwarcie).
  Nadwyżka z podwójnego liczenia: TS1 −0,072 %/rok (razem (b2) − (a) = −0,076 [−0,127; −0,028] — istotnie różne od zera,
  bo TS1 na ogół płaci funding), X1 na wagach silnika +0,130 %/rok (suma opłat „nowej pozycji” z tabeli). Poniżej progu
  porównywalności, ale to realne ryzyko przy przepisywaniu wzoru z bibliotek.

### Miejsce ryzyka nr 2 — monety z rozliczeniem co 4 h albo co 1 h

Klasa dnia z liczby rozliczeń moneta×dzień (3 = 8 h, 6 = 4 h, 24 = 1 h; „inne” = dzień zmiany interwału lub dziura):

| klasa | TS1 dni pozycji | udział |(a)| | (b)−(a) %/rok | X1 dni pozycji | udział |(a)| | (b)−(a) stała ilość | D1 |
|---|---|---|---|---|---|---|---|
| 8 h | 84,2 % | 79,1 % | −0,006 | 77,5 % | 50,6 % | +0,107 | +0,068 |
| 4 h | 15,0 % | 15,7 % | +0,007 | 21,0 % | 24,9 % | +0,456 | +0,041 |
| 1 h | 0,65 % | 3,4 % | −0,002 | 1,3 % | **20,9 %** | +23,008 | −0,240 |
| inne | 0,10 % | 1,7 % | −0,003 | 0,20 % | 3,5 % | −0,009 | −0,035 |

Silnik sumuje wszystkie rozliczenia dnia, więc interwał 4 h / 1 h nie gubi ani nie dubluje opłat (kontrola zerowa = 0
do 10⁻¹⁷, 0 różnych przypisań do dnia). Różnica w tych klasach to tylko dryf ceny w ciągu dnia. Uwaga dla X1: monety
z rozliczeniem co godzinę to 1,3 % dni pozycji, ale 21 % sumy bezwzględnej fundingu X1 — to monety w stanie skrajnym (squeeze),
gdzie stawka stoi na limicie.

### Miejsce ryzyka nr 3 — brakujące stawki (silnik: NaN → 0)

| | TS1 | X1 |
|---|---|---|
| dni pozycji (moneta × dzień × faza) | 273 546 | 137 830 |
| bez żadnego rozliczenia | 77 (0,028 %) | 37 (0,027 %) |
| — moneta bez pliku fundingu | 0 | 0 |
| — brak ceny dnia (moneta wycofana / dziura w cenach) | 28 | 25 |
| — dziura w fundingu przy istniejącej cenie | 49 | 12 |
| dni z nietypową liczbą rozliczeń (≠ 0, 3, 6, 24) | 278 | 269 |
| stawki NaN w plikach (od początku okna) | 0 | 0 |
| ograniczenie z góry wpływu dziur (3 × mediana |stawki| 0,0091 % × |waga|) | 0,0007 %/rok | 0,0009 %/rok |

**BRAK DANYCH** dla 49 / 12 dni-dziur — wartości nie uzupełniano; ich możliwy wpływ jest o 3 rzędy wielkości mniejszy
od progu porównywalności.

### Przybliżenie ceny mark (sprawdzenie na BTC)

Cena mark niedostępna w repo — zastępuje ją cena ostatniej transakcji (zamknięcie świecy). Świece w ciągu dnia są tylko
dla BTC; dla pozostałych monet interpolacja geometryczna zamknięć dnia (zapisana w pre-rejestracji). Na BTC (4 014
rozliczeń poza północą, wszystkie ze świecą 1h i 4h): dryf całej nogi identyczny przy cenach z interpolacji, 4h i 1h
(TS1 −0,010; X1 +0,583 w modelu stałej ilości); błąd ceny z interpolacji w chwili rozliczenia: mediana 0,63 %, 95. percentyl
2,77 %, średnia ze znakiem +0,01 % — przybliżenie bez obciążenia na BTC. Dla monet w squeezie (klasa 1 h X1) ścieżka ceny
w ciągu dnia jest dzika i interpolacja może się mylić bardziej — dryf D1 w tej klasie (−0,24) niesie tę niepewność.

### Porównanie z KO1 (reguła z pre-rejestracji: próg = 25 % kosztu KO1 nogi)

| noga | KO1 %/rok | próg | (b) − (a) | |średnia| / KO1 | przedział w ±progu | odczyt według reguły |
|---|---|---|---|---|---|---|
| TS1 | 0,8 | 0,200 | −0,004 [−0,042; +0,033] | 0,005 | tak | **pomijalna** |
| X1 (liczba główna) | 3,3 | 0,825 | +23,561 [−0,395; +71,321] | 7,14 | nie (obejmuje 0) | **nierozstrzygnięta** (artefakt ruiny) |
| X1 D1 (po wyniku) | 3,3 | 0,825 | −0,166 [−0,620; +0,221] | 0,050 | tak | pomijalna — *po wyniku* |
| X1 D2 (po wyniku) | 3,3 | 0,825 | +0,120 [−0,423; +0,841] | 0,036 | nie (o 0,016) | nierozstrzygnięta — *po wyniku* |

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Sposób, w jaki silniki liczą funding (suma dnia razy pozycja z rana), zmienia koszt o setne części punktu rocznie
na trendzie i o ok. 0,2 punktu na X1. To dużo mniej niż koszty zleceń z KO1, które i tak nie blokowały strategii.
Poprawka wzoru nic by nie zmieniła w decyzjach. Duża liczba X1 z planu (+23,6 punktu) nie mówi nic o fundingu: pokazuje,
że pozycja trzymana cały tydzień bez zabezpieczenia straciłaby w epizodzie MYX (wrzesień 2025) cały kapitał kilku faz.
Silnik X1 tego nie widzi, bo zakłada codzienne wyrównywanie nóg.

## Co poszło inaczej niż w planie (wprost)

1. **Diagnostyka po wyniku (D1, D2) dopisana po pierwszym przebiegu.** Pierwszy przebieg (do pliku roboczego, nie
   `raw_output.txt`) pokazał X1 +23,6 %/rok — czerwoną flagę (bramka A4). Liczba z pre-rejestracji zostaje bez zmian
   i jest w tabeli jako główna; D1 i D2 są oznaczone „po wyniku” w wydruku i tutaj. Sekcje 1–8 wydruku są identyczne
   w obu przebiegach (przebieg jest deterministyczny).
2. **Ceny w ciągu dnia dla monet innych niż BTC — BRAK DANYCH w repo.** Interpolacja zamknięć (zapisana w planie);
   świece 1h/4h tylko dla BTC.
3. **Źródła freqtrade nie czytano** (brak klonu na serwerze, praca bez sieci). Wzór „stawka × cena × ilość w chwili
   rozliczenia” przepisany z opisu w zadaniu; konwencja przedziału domkniętego (b2) jest wariantem ryzyka, nie
   sprawdzonym cytatem z kodu freqtrade.
4. **Błąd znaleziony testem przed przebiegiem:** pliki parquet mają znaczniki czasu w ms, a `astype("int64")` dawał
   nie-nanosekundy — druga droga nie widziała żadnego rozliczenia. Naprawione w `fc628e7` z testem.
5. **Skill `engineering:testing-strategy` wczytany po napisaniu testów** (zasada 19 wymaga go przy testach nowego
   modułu); po wczytaniu dopisano 3 testy brzegów (rozliczenie poza danymi, opłata po likwidacji, za mało bloków
   bootstrapu).
6. **Zasada 18 (mierzalność)** — nie dotyczy (runda nie odczytuje przewagi), zapisane w pre-rejestracji.

## Bramki jakości (zasada 16)

**16a — walidacja write-upu (`data:validate-data`): Caveats.**
- Druga droga: liczba główna policzona niezależnie „dolarowo” w pandas (ilość × cena × stawka, kapitał z kolumny `gross`
  silnika, (a) wprost z kolumny funding silnika) — zgodność do 10⁻¹⁹ dziennie (TS1) i 10⁻¹⁴ (X1); D1 — złączenia pandas
  wobec rozrzutu numpy, zgodność do 10⁻¹⁷. Zgodność testowana też na danych syntetycznych z likwidacjami, monetą co 4 h,
  jitterem i NaN (`tests/test_funding_settlement.py`).
- Ręczne sprawdzenie rekordu: MYXUSDT 2025-09-09 — 24 rozliczenia, suma −16,68 %, minimum −2 % (limit giełdy).
- Kogo nie ma w zbiorze: żadna trzymana moneta nie jest bez pliku fundingu; 28 / 25 dni pozycji w monetach bez ceny
  (wycofane — silnik traktuje jak gotówkę); 2026 = pół roku; ceny w ciągu dnia tylko BTC.
- Czerwona flaga: X1 +23,6 %/rok — zbadana (ruina stałej ilości, MYX), nie błąd kodu.
- Zgodność z wcześniejszymi rundami: RU1 (inna konfiguracja i okno) — funding TS1 Σ −7,4 % (ok. −1,4 %/rok), X1 jednej
  fazy Σ +49 % (ok. +9 %/rok); tu (a) −1,13 i +6,31 %/rok — ten sam znak i rząd wielkości.
- A6 (nowy przyrząd): kontrola zerowa (wagi silnika, cena stała w dniu, konwencja silnika) daje 0,000 %/rok, max 10⁻¹⁷
  dziennie; kontrola czułości — testy z ręcznie policzoną różnicą (−0,0068 wobec −0,006; −0,0108).
- **Zastrzeżenia, które czytelnik musi znać:** (1) liczba X1 z pre-rejestracji jest artefaktem ruiny — odpowiedź na
  pytanie zadania dla X1 pochodzi z diagnostyki po wyniku (D1); (2) ceny w ciągu dnia dla altów z interpolacji
  (na BTC bez obciążenia); (3) cena ostatniej transakcji zamiast ceny mark; (4) dzień likwidacji TS1: rozliczenia
  w ciągu dnia liczone w całości (godzina likwidacji nieznana), jak w silniku.

**16b — statystyka (`data:statistical-analysis`):** efekt + przedział 95 % z bootstrapu blokowego po tygodniach
(10 000 losowań, ziarno 20260929), mediana obok średniej (dzienna × 365, per rok, per faza, per moneta), zakresy per rok
i per moneta. 0 wariantów; dwie diagnozy po wyniku (D1, D2) nazwane jako takie. Rozkład różnicy X1 skrajnie skośny
(średnia +23,6 wobec mediany dziennej +0,03 %/rok) — średnia niesiona przez 35 dni faz z 13 783.

**16c — przegląd diffu (`engineering:code-review`):** Przegląd diffu (16c): **Approve** — sprawdzono zgodność pętli z silnikami (odtworzenie funding i zwrotu brutto do 10⁻¹⁸ bez zmiany silników), konwencje granicy 00:00, likwidację, jednostki znaczników, niezależność drugiej drogi i testy (17/17); cztery sugestie bez wpływu na liczby, zostawione w kodzie takim, jaki dał `raw_output.txt`: nieużywana stała `MIDNIGHT_TOL`; bootstrap losuje pełne tygodnie i pomija ostatnie 2 dni z 1 969 (średnia z całości); ograniczenie wpływu dziur zakłada 3 rozliczenia na dzień (dla monet co 1 h niedoszacowane, nadal ≤ 0,01 %/rok); `engine_avg` ustawiane poza polami dataclass `Leg`. Bez kluczy, sieci i zapisu poza katalogiem rundy.

## Co na plus (+) / Co na minus (−)

**+**
- Dwie niezależne implementacje (numpy na wagach i „dolarowa” w pandas) dają tę samą liczbę do 10⁻¹⁴; silniki odtworzone
  do 10⁻¹⁸ bez ich zmiany.
- Rozbicie różnicy na składowe sumuje się dokładnie; każde miejsce ryzyka ma liczbę i kategorię (raz / dwa razy / wcale).
- Dane kompletne: 0 trzymanych monet bez fundingu, 0 stawek NaN, 0 błędów przypisania do dnia.
- Wykryte ryzyko modelu pozycji X1 (ruina przy stałej ilości w squeezie), którego wcześniejsze rundy nie opisywały.

**−**
- Liczba X1 z pre-rejestracji nie odpowiada na pytanie zadania — plan zmienił naraz wzór fundingu i model pozycji
  (błąd projektu: dwie zmienne naraz, wbrew „jednej zmianie na raz”). Odpowiedź dla X1 jest diagnozą po wyniku.
- Ceny w ciągu dnia dla altów z interpolacji; cena ostatniej transakcji zamiast mark.
- Wzór freqtrade przepisany z opisu, bez wglądu w źródło.
- D2 wyrzuca tylko okresy z kapitałem ≤ 0; okresy z kapitałem bliskim zera nadal pompują wagi (2026: −2,65).

## Wniosek

**Skrót silników (dzienna suma stawek × waga z początku dnia) zmienia koszt fundingu nóg dziennika o wielkość
pomijalną wobec kosztów wykonania z KO1: TS1 −0,004 %/rok [−0,042; +0,033] (0,5 % z 0,8 %/rok), X1 −0,17 %/rok
[−0,62; +0,22] na wagach silnika (5 % z 3,3 %/rok; diagnoza po wyniku), a liczba X1 z pre-rejestracji (+23,6 %/rok
[−0,4; +71,3], według reguły nierozstrzygnięta) mierzy ruinę pozycji o stałej ilości w epizodzie MYX 2025-09, nie
funding.**

Trzy miejsca ryzyka: granica 00:00 — silnik liczy raz, ale nowej pozycji (netto +0,006 / +0,015 %/rok); przedział
domknięty z obu stron liczyłby ją dwa razy (TS1 −0,08 %/rok); interwały 4 h / 1 h — liczone poprawnie; brakujące stawki —
0,03 % dni pozycji, wpływ ≤ 0,001 %/rok.

## Rekomendacja

1. **Nie poprawiać wzoru fundingu w `ts_momentum` / `xs_momentum`** — różnica ≤ 5 % kosztów KO1; poprawka byłaby
   Poprawką dziennika bez wpływu na decyzje. Ścieżka odwrotu: nic nie zmieniono w silnikach.
2. **Przy dzienniku wykonania (szczebel 4 ADR-09)** księgować funding po rozliczeniach giełdy, a do porównania
   z papierem pamiętać, że papier przypisuje rozliczenie 00:00 w dniu zmiany nowej pozycji (różnica rzędu 0,01 %/rok).
3. **Nie przenosić z bibliotek konwencji [otwarcie, zamknięcie] domkniętej z obu stron** — dubluje rozliczenie graniczne
   (TS1 −0,08 %/rok).
4. **Do decyzji użytkownika (osobne zadanie, ewentualnie Poprawka N dziennika): model pozycji X1.** Silnik X1 co dzień
   przywraca nogi do 0,5 kapitału; dziennik wykonuje X1 raz w tygodniu. W squeezie (MYX 2025-09) pozycja o stałej ilości
   bez likwidacji traci cały kapitał fazy (5 okresów faz). Możliwe drogi: zostawić (X1 tylko w dzienniku papierowym, nie
   kandydat), liczyć X1 ze stałą ilością i likwidacją izolowaną jak TS1, albo wyrównywać nogi codziennie także
   w wykonaniu. Ta runda niczego z tego nie wybiera ani nie mierzy zwrotu X1.

## Użyte skille (CLAUDE.md zasada 19)

Wynik `py tools/skill_audit.py raport --galaz zadanie-016-funding-druga-droga`:

### Użyte skille — gałąź `zadanie-016-funding-druga-droga` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-09-29T09:20:54+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` |  |
| 2026-09-29T09:20:54+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` |  |
| 2026-09-29T10:30:42+00:00 | claude (agent: general-purpose) | `data:statistical-analysis` |  |
| 2026-09-29T10:38:25+00:00 | claude (agent: general-purpose) | `data:validate-data` |  |
| 2026-09-29T10:43:06+00:00 | claude (agent: general-purpose) | `engineering:testing-strategy` | Przegląd testów nowego modułu backtest/funding_settlement.py (zadanie 016, FD1): tests/test_funding_settlement.py — czy pokrywają dwie drogi fundingu, granice 00:00, likwidację, ruinę, jitter znaczni… |
| 2026-09-29T10:47:37+00:00 | claude (agent: general-purpose) | `engineering:code-review` | Przegląd diffu gałęzi zadanie-016-funding-druga-droga wobec master 43bbe4a: backtest/funding_settlement.py, backtest/run_fd1_funding.py, tests/test_funding_settlement.py (bramka 16c CLAS-5). |

Razem: 6 wczytań, 6 różnych skilli: `anthropic-skills:clas5-quant`, `anthropic-skills:clas5-runda`, `data:statistical-analysis`, `data:validate-data`, `engineering:code-review`, `engineering:testing-strategy`.

Co wniósł każdy: `clas5-runda` — pre-rejestracja przed liczbą (`ab6ab0e`), wiersz w rejestrze odczytów, wpis w INDEX
i wniosek 111; `clas5-quant` — dyscyplina „nie zmieniać silników, odtworzyć je i porównać”, próg kosztów z KO1, kontrola
zerowa (A6); `data:statistical-analysis` — bootstrap blokowy po tygodniach, mediana obok średniej, zakresy per rok, faza
i moneta (skośność X1); `data:validate-data` — czerwona flaga X1 potraktowana jako błąd do zbadania przed interpretacją,
ręczne sprawdzenie rekordu MYX, pytanie „kogo nie ma w zbiorze”, werdykt Caveats; `engineering:testing-strategy`
(wczytany spóźniony, po napisaniu testów) — trzy testy brzegów; `engineering:code-review` — bramka 16c, werdykt Approve
z czterema sugestiami. Momenty tabeli bez wpisu: `quant-strategy-catalog` — runda nie tworzy hipotezy; `dataviz` — bez
wykresu; `data:explore-data` — nie nowe źródło (pliki fundingu używane od F1/X1), profil danych zrobiony w przebiegu
(godziny rozliczeń, dziury, NaN); `security-review` — kod bez kluczy, zleceń i połączeń sieciowych; `ta-toolkit`,
`lean-research`, `engineering:architecture`, `engineering:debug` — nie dotyczy (przyczynę czerwonej flagi wskazała
diagnostyka w przebiegu, nie debugowanie błędu).
