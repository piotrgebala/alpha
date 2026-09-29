# FD1 — funding drugą drogą: dzienna suma × waga (silniki) wobec rozliczenia po rozliczeniu (2026-09-29)

> **STATUS: PRE-REJESTRACJA** (zapisana przed obejrzeniem jakiejkolwiek liczby różnicy; wynik dopisany niżej).

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

**Rejestr odczytów (`py -m backtest.dsr --k 0`):** 58 wierszy, 34 odczyty programu; N metodą AU4 = 40, z odczytami
0-wariantowymi 52. FD1: `opis-z-wynikiem`, `odczyt_programu = nie` (koszt fundingu nóg już odczytanych, bez związku
sygnału ze zwrotem), 0 wariantów.
