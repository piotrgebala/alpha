# NL1 — short na nowych kontraktach USDT-M przez 14 dni po listingu (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-23: „testuj dalej
> różne kombinacje" (futures, dźwignia 3×, longi i shorty). **NOWA SERIA NL (rodzina G2
> katalogu: zdarzenia „listing”), licznik 1/1, STOP.** Drugi kandydat panelu „co dalej”
> (po TS1): jedyny poza trendem, który przeszedł bramę danych i mierzalności.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Gdy Binance wprowadza kontrakt na nową monetę, w obiegu jest zwykle mało tokenów, a nad rynkiem
wisi duża przyszła podaż: airdropy, fundusze, odblokowania. Hipoteza mówi, że w pierwszych
tygodniach cena częściej spada, niż rośnie, więc **short od drugiego dnia notowań przez 14 dni**
powinien zarabiać. Sprawdzamy to na wszystkich 569 nowych kontraktach od 2021 roku, łącznie
z tymi, które potem zniknęły z giełdy. Liczymy realny funding i likwidację. Uczciwie z góry:
test zobaczy efekt rzędu 5–7 % na zdarzenie. Słabszego nie odróżni od szumu, bo nowe monety
potrafią w 14 dni zrobić ±50 %.

## ID testu

**NL1** — nowa seria NL, licznik 1/1, STOP. Inne okna (7/28 dni), opóźnienia wejścia, filtry
(np. tylko PREMARKET, tylko duże), hedge BTC jako kryterium, long zamiast short = warianty,
zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `nl1-nowe-listingi`.
- Dane (nowe źródło, pobrane 2026-09-24): `py -m data.fetch_listings` → `data/raw/listings/`
  (`events.csv`, `klines.parquet`, `funding.parquet`); log `pobranie.txt`, profil
  `profil_danych.txt`. Archiwum `data.binance.vision`: 887 symboli USDT w archiwum dziennym;
  data listingu d0 = pierwszy dzienny plik świec (point-in-time); klasyfikacja `exchangeInfo`
  (TradFi 199, indeksy 5, stablecoin 1 wykluczone), redenominacje (ta sama baza pod inną nazwą:
  1) wykluczone, d0 < 2021-01-01 (80) i okno poza końcem danych (12) wykluczone → 589; dalej
  PRZED przebiegiem: archiwum spóźnione względem `onboardDate` o > 1 dzień (17, głównie 2021 —
  pierwszy dzień w archiwum nie jest dniem listingu) i brak fundingu w archiwum (3) → **569
  zdarzeń**, 62 miesiące. Świece i funding z miesięcznych plików archiwum (wycofane włącznie):
  0 duplikatów, 0 cen ≤ 0, każde zdarzenie ≥ 21 świec; funding co 1/2/4/8 h (sumowane stawki).
- Kod: `data/fetch_listings.py` + `tests/test_fetch_listings.py` (10), `backtest/listing_events.py`
  + `tests/test_listing_events.py` (10, w tym `hypothesis`: P&L ≥ −1/L, monotoniczność względem
  maksimum ceny); skrypt `backtest/run_listings_nl1.py` (na `runs/ZAMROZONE.txt`).
- Komendy: `PYTHONUTF8=1 py -m backtest.run_listings_nl1 --moc` → `moc.txt` (przed przebiegiem);
  `PYTHONUTF8=1 py -m backtest.run_listings_nl1` → `raw_output.txt`.

## Poprzedzające wyniki

- **Wnioski 67, 69:** kolejne cechy i horyzonty BTC nie pomagają — potrzebny INNY zbiór
  informacyjny lub INNA formuła. NL1 zmienia oba: zbiór = kalendarz zdarzeń (listing), formuła =
  badanie zdarzeń na przekroju ~570 monet; nie ma tu BTC ani cech wykresu.
- **X1/X2 (B1):** ranking po zwrocie 28 dni — nowe monety w pierwszych 14 dniach nie mają
  jeszcze sygnału X, więc NL1 nie jest wariantem B1. W X1 zysk dawała noga short (wniosek 64)
  — spójne z hipotezą, ale to inna konstrukcja.
- **TS1 (wniosek 70):** trend tygodniowy na top-20; nowe listingi do top-20 zwykle nie wchodzą
  w pierwszych 30 dniach (warunek historii obrotu) — brak nakładania próby.
- **C1/D1/P2:** funding jako przepływ — tu funding jest KOSZTEM/PRZYCHODEM shorta, liczony realnie.

## Pre-rejestracja

- **Hipoteza:** short na nowym kontrakcie USDT-M przez 14 dni od pierwszego pełnego dnia notowań
  ma dodatni średni P&L po kosztach i realnym fundingu.
- **Mechanizm:** mały obieg i duża przyszła podaż (airdropy, farmerzy, fundusze, odblokowania)
  plus zakupy napędzane uwagą przy drogim shortowaniu (Miller 1977; Barber–Odean 2008; IPO
  underperformance Ritter 1991 — rynek akcji). Krypto: brak solidnego dowodu kierunku dryfu po
  listingu perpetuala — prior niepewny; ryzyko: spadek jest już wyceniony w fundingu.
- **DOKŁADNIE JEDNA zmienna:** reguła zdarzeniowa (short w oknie) wobec braku pozycji.
  Parametry z mechanizmu, bez siatki: wejście po otwarciu d0+1 (pierwszy pełny dzień; d0 bywa
  niepełny), wyjście po zamknięciu d0+14 (N = 14 dni — środek przedziału 7–28 z propozycji,
  ustalony PRZED danymi); koszt taker 0,05 % + poślizg 2 bps na stronę; funding realny z archiwum
  (short dostaje dodatnią stawkę); likwidacja izolowana przy wzroście ≥ 1/L − MMR (MMR 2,5 %,
  dzienne maksima); kontrakt wycofany w oknie = wyjście po ostatnim zamknięciu.
- **Przyrząd i kryterium (jedno ramię, m = 1)** — P&L shorta **1×** na zdarzenie (% nominału),
  średnia z błędem **odpornym na klastry** (miesiąc listingu; CR1):
  - **POZYTYWNY:** t > 1,96;
  - **NEGATYWNY:** górny kraniec CI 95 % < 0;
  - inaczej **NIEROZSTRZYGNIĘTY**.
  Kryterium w granicy dużego n: przy n → ∞ POZYTYWNY ⇔ prawdziwa średnia > 0 — nie jest
  anty-skorelowane z celem.
- **Mierzalność (zasada 18, `moc.txt`, tylko rozrzut):** reguła bez modelu → n = liczba zdarzeń
  = **569** (`expected_trades(569, 0, 1)`), 62 klastry; sd na zdarzenie 47,0 %; se klastrowe
  2,45 % (efekt klastrów ×1,55) → **half-width ±4,8 % nominału**, MDE (80 % mocy) ≈ 6,9 %.
  Obietnica mechanizmu (low float / high FDV — spadki rzędu kilkunastu % w tygodniach po
  debiucie w opisach branżowych, bez recenzowanego pomiaru): efekt ≥ ~7 % → **MIERZALNA**;
  efekty 2–5 % (skala IPO z rynku akcji) → **niewidoczne** — zapisane z góry.
- **Wrażliwość zapisana z góry (opisowo, bez werdyktu):** błąd klastrowy po KWARTAŁACH
  (okna 14 dni przecinają granice miesięcy, więc klastry miesięczne mogą zaniżać korelację).
- **Opisowo (0 wariantów):** 2× i 3× izolowane (udział likwidacji, P&L na nominał i na depozyt);
  short alt + long BTC w tym samym oknie (czy to tylko rynek); rozkład, funding, lata; liczba
  równoczesnych pozycji.
- **Kontekst multiple testing:** ~25 odczytów w dwa dni w różnych seriach; NL1 to jedno ramię.
- **Czego runda NIE robi:** nie wybiera N, opóźnienia ani filtra po wyniku; nie odwraca znaku
  (long po listingu to osobna hipoteza post hoc); nie wyklucza monet po zachowaniu ceny.

---

_(sekcje poniżej po przebiegu)_

## Wynik

_(po przebiegu)_

## Co na plus (+) / Co na minus (−)

_(po przebiegu)_

## Walidacja (zasada 16a)

_(po przebiegu)_

## Przegląd diffu (zasada 16c)

_(po przebiegu)_

## Wniosek

_(po przebiegu)_

## Rekomendacja

_(po przebiegu)_

## Użyte skille

_(po przebiegu — z `py tools/skill_audit.py raport --galaz nl1-nowe-listingi`)_
