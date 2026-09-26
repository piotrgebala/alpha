# Strategie dziennika — dokładne założenia

> Plik GENEROWANY z `backtest/journal_strategies.py` (poprawka 10) — nie edytuj ręcznie:
> `PYTHONUTF8=1 py -m backtest.journal_strategies > dziennik/STRATEGIE.md`. Liczby pochodzą ze stałych
> silników i parametrów dziennika; test pilnuje, że plik jest aktualny względem kodu.

## Wspólne

- Dane: kontrakty wieczyste Binance USDT-M, świece dzienne UTC, tylko zamknięte; dzień odczytu (`as_of`) = ostatnia zamknięta świeca wspólna dla Binance i premii Coinbase; pozycje ogłaszane na następny dzień.
- Dziennik papierowy: bez realnych pieniędzy; wynik w `wyniki.csv` / `x1_wyniki.csv`, pozycje w `sygnaly.csv` / `x1_sygnaly.csv`, lista transakcji w `transakcje.csv` / `transakcje_otwarte.csv` (poprawka 9); etykiety `stan_rynku.csv` i `fng.csv` tylko zapisywane (poprawki 7–8), nie wpływają na pozycje.
- O realnym kapitale decyduje drabina dowodów (ADR-09) i użytkownik; odczyt dziennika ~2026-12-25.

## TS1 — Trend tygodniowy na koszyku top-20

**Opis:** Gra z kierunkiem ostatnich 28 dni na 20 najpłynniejszych kontraktach: moneta rosła → long, spadała → short.

**Założenia:**

1. Koszyk: 20 kontraktów wieczystych USDT-M Binance o największym średnim obrocie z 30 dni przed początkiem miesiąca (min. 30 dni notowań), bez stablecoinów (BUSD, DAI, FDUSD, TUSD, USD1, USDC, USDE, USDP) i kontraktów na akcje/surowce (TRADIFI); skład stały przez cały miesiąc.
2. Sygnał: znak zmiany ceny z 28 dni (zamknięcie dziś / zamknięcie 28 dni temu − 1): plus → long, minus → short, brak danych → bez pozycji.
3. Wielkość: znak × min(3; 40 % / zmienność roczna monety), w koszyku dzielone przez liczbę monet z sygnałem; zmienność = EWMA kwadratów dziennych zmian ceny (środek masy 60 dni, min. 30 dni).
4. Harmonogram: 7 faz, każda przebudowuje swój koszyk co 7 dni (każda w inny dzień tygodnia) i ma 1/7 kapitału składowej; wejście po zamknięciu dnia przebudowy (00:00 UTC, cena zamknięcia), trzymanie 7 dni.
5. Dźwignia: izolowany depozyt 2× na każdą pozycję; likwidacja, gdy cena odejdzie od wejścia o ≥ 49 % przeciw pozycji — tracony cały depozyt pozycji.
6. Koszty: 0,07 % od obrotu (opłata taker 0,05 % + poślizg 2 pb); funding naliczany codziennie (long płaci dodatni, short dostaje).
7. Bez stop-lossów, celów zysku i zarządzania w trakcie tygodnia (N1, TP1).

**Stan dowodów:** Ślad bez dowodu: +11 %/rok [−4; +26] na historii 2021–2026 (t 1,43), dodatni 6/6 lat i 7/7 faz; rozstrzygnie dziennik.

**Wynik w dzienniku:** od 2026-09-24 — `wyniki.csv (r_trend; w portfelu R1)`

## CP1 — Premia Coinbase → BTC

**Opis:** Gdy kupujący na Coinbase (USA) płacą za BTC relatywnie więcej niż zwykle, long BTC; gdy mniej — short BTC.

**Założenia:**

1. Premia dnia = zamknięcie Coinbase BTC-USD / zamknięcie spot Binance BTC/USDT (świeca 8h 16:00–24:00 UTC) − 1.
2. Sygnał: znak(średnia premii z 7 dni − średnia premii z 90 dni): plus → long, minus → short kontraktu BTCUSDT.
3. Wielkość w fazie: znak × min(3; 40 % / zmienność roczna BTC) (zmienność jak w trendzie).
4. Harmonogram: 7 faz, każda przebudowuje pozycję BTC co 7 dni (każda w inny dzień tygodnia) i ma 1/7 kapitału składowej; wejście po zamknięciu dnia przebudowy (00:00 UTC, cena zamknięcia), trzymanie 7 dni.
5. Dźwignia: izolowany depozyt 3×; likwidacja przy ruchu ≥ 32,3 % przeciw pozycji.
6. Koszty: 0,07 % od obrotu (opłata taker 0,05 % + poślizg 2 pb); funding naliczany codziennie (long płaci dodatni, short dostaje).
7. Bez stop-lossów, celów zysku i zarządzania w trakcie tygodnia.

**Stan dowodów:** Jedyny odczyt spełniający kryterium (+32 %/rok, t 2,09), ale po korekcie na ~28–40 prób (DSR 0,52) nieodróżnialny od szczęścia; rozstrzygnie dziennik.

**Wynik w dzienniku:** od 2026-09-24 — `wyniki.csv (r_coinbase; w portfelu R1)`

## R1 — Portfel dziennika: trend + premia Coinbase

**Opis:** Łączy obie nogi tak, żeby każda wnosiła podobne ryzyko, a cały portfel miał zmienność ok. 20 % rocznie.

**Założenia:**

1. Mnożniki k (osobno dla trendu i premii): wagi ∝ 1/zmienność nogi (kowariancja EWMA, środek masy 45 dni, tylko dane sprzed dnia), skalowane do zmienności portfela 20 %/rok; sufit k ≤ 2 na nogę (zasada 5).
2. Przeliczenie co 7 dni; pierwsze 60 dni po równo.
3. Bez hamulca po stracie (runda SZ1: szkodził) i bez przełączania nóg po stanie rynku.
4. Progi obsunięcia od szczytu: ostrzeżenie 18,4 %, STOP 27,6 % (1,5 × największe historyczne); STOP = żadnych nowych pozycji.
5. Realne pieniądze (szczebel 4 ADR-09, decyzja użytkownika): depozyt ≤ 5 % całego kapitału → strategia ≈ 10 % kapitału (runda PR1).

**Stan dowodów:** Przy dwóch nogach wagi z korelacjami = wagi 1/σ (PR1); wynik papierowy liczony od startu.

**Wynik w dzienniku:** od 2026-09-24 — `wyniki.csv (r_port, equity, drawdown)`

## X1 — Momentum przekrojowe top-20 (osobno, tylko papier)

**Opis:** Co tydzień long 5 monet, które najbardziej zyskały przez 28 dni, i short 5 najsłabszych — zakład, że liderzy dalej wygrywają z maruderami.

**Założenia:**

1. Koszyk: 20 kontraktów wieczystych USDT-M Binance o największym średnim obrocie z 30 dni przed początkiem miesiąca (min. 30 dni notowań), bez stablecoinów (BUSD, DAI, FDUSD, TUSD, USD1, USDC, USDE, USDP) i kontraktów na akcje/surowce (TRADIFI); skład stały przez cały miesiąc.
2. Sygnał: zmiana ceny z 28 dni; ranking wśród członków (min. 10 z sygnałem): long 5 najlepszych, short 5 najgorszych (remis → alfabetycznie).
3. Kapitał fazy: 50 % na nogę long i 50 % na nogę short (po 10 % na monetę); bez dźwigni i bez likwidacji; wartość nóg wyrównywana codziennie.
4. Harmonogram: 7 faz, przebudowa co 7 dni, trzymanie 7 dni.
5. Koszty: 0,07 % od obrotu (opłata taker 0,05 % + poślizg 2 pb); funding naliczany codziennie (long płaci dodatni, short dostaje).
6. Progi obsunięcia od szczytu: ostrzeżenie 55,0 %, STOP 82,5 %.

**Stan dowodów:** Ślad słaby: +9,5 %/rok [−21; +40] (t 0,61) jako średnia 7 faz; poza portfelem R1 (decyzja użytkownika), tylko papier.

**Wynik w dzienniku:** od 2026-09-25 — `x1_wyniki.csv`
