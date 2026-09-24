# NL1 — short na nowych kontraktach USDT-M przez 14 dni po listingu (2026-09-24)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY:** średni P&L shorta 1× **+2,12 % na zdarzenie
> [−2,68; +6,93]**, t 0,87 (n 569, 62 klastry). Mediana +13,5 %, 66 % zdarzeń zyskownych, ale
> 12 % nowych monet podwoiło cenę w 14 dni (likwidacja nawet przy 1×) i ten ogon zjada zysk.
> Przy 3× zlikwidowanych 41,5 % pozycji, +0,95 % na nominał. Pre-rejestracja `47e196d` →
> przebieg → wynik w commicie scalającym. **Seria NL: 1/1, STOP.** Walidacja (16a): **READY**;
> przegląd diffu (16c): **Approve**.
> Decyzja użytkownika 2026-09-23: „testuj dalej
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

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Short na nowych monetach wygrywa często, ale przegrywa dużo.** Dwie na trzy nowe monety
rzeczywiście spadły w pierwszych dwóch tygodniach, typowo o kilkanaście procent. Co ósma jednak
podwoiła cenę, a wtedy short traci całą stawkę. Po zsumowaniu zostaje średnio +2 % na zdarzenie,
z niepewnością od −3 % do +7 %. To nie odróżnia się od zera. **Przy Twojej dźwigni 3× to
szczególnie zły pomysł:** 42 % pozycji zostałoby zlikwidowanych, bo wystarczy wzrost o 31 %,
a nowe monety robią takie ruchy bardzo często.

---

_(sekcje poniżej po przebiegu)_

## Wynik

Pełny stdout: `raw_output.txt` (2 s). P&L shorta na zdarzenie w % nominału, po kosztach
(0,14 %) i realnym fundingu.

| miara (1×) | wartość |
|---|---|
| n zdarzeń / klastrów (miesiąc) | 569 / 62 |
| **średnia [CI 95 % klastrowe]** | **+2,12 % [−2,68; +6,93]**, t +0,87 (iid +1,08; efekt klastrów ×1,55) |
| mediana | +13,54 % |
| udział zdarzeń z zyskiem | 65,6 % |
| percentyle | p05 −100,5 %, p25 −10,8 %, p75 +33,7 %, p95 +57,8 %; min −122,8 %, max +80,3 % |
| rozkład składowych (średnio) | cena +3,41 %, funding −1,15 %, koszt 0,14 % |
| funding w oknie | mediana +0,31 %; short płaci netto w 41,1 % zdarzeń; p05 −12,0 % |
| likwidacje przy 1× (wzrost ≥ 97,5 % w 14 dni) | 67 zdarzeń (11,8 %) |
| **werdykt** | **NIEROZSTRZYGNIĘTY** |

**Per rok (opisowo):**

| rok | n | średnia | mediana | % zyskownych |
|---|---|---|---|---|
| 2021 | 47 | −3,5 % | +3,7 % | 59,6 % |
| 2022 | 22 | +11,5 % | +16,0 % | 77,3 % |
| 2023 | 91 | +2,0 % | +11,2 % | 69,2 % |
| 2024 | 131 | −1,3 % | +10,0 % | 59,5 % |
| 2025 | 239 | +4,5 % | +17,3 % | 68,6 % |
| 2026 (do 06) | 39 | +1,1 % | +22,0 % | 59,0 % |

**Opisowo (0 wariantów):**

| wersja | likwidacje | P&L na nominał [CI] | na depozyt |
|---|---|---|---|
| 2× izolowane (likwidacja przy +47,5 %) | 27,9 % | +2,31 % [−2,05; +6,67] | +4,6 % (mediana +22,5 %) |
| 3× izolowane (likwidacja przy +30,8 %) | **41,5 %** | +0,95 % [−2,23; +4,13] | +2,9 % (mediana +10,9 %) |
| short alt + long BTC, równy nominał | — | +3,57 % [−0,53; +7,66] | — |

BTC w tych samych oknach średnio +1,44 %. Równoczesnych pozycji: mediana 3, p90 10, max 19.

## Co na plus (+) / Co na minus (−)

**(+)**
- Pełna, point-in-time populacja: wszystkie pierwsze listingi krypto USDT-M 2021–2026 z archiwum,
  razem z wycofanymi kontraktami; funding realny z archiwum co do rozliczenia.
- Mechanizm częściowo widać: 66 % zdarzeń zyskownych, mediana +13,5 % — typowa nowa moneta
  rzeczywiście spada w pierwszych dwóch tygodniach.
- Przyrząd zachował się jak zapowiedziano (half-width ±4,8 %); druga droga identyczna.

**(−)**
- **Średnia nie odróżnia się od zera** — ogon wystrzałów (79 zdarzeń ≤ −50 %, razem −7 703 %
  wobec +8 911 % reszty) zjada prawie cały zysk typowego zdarzenia.
- **Dźwignia pogarsza wynik:** przy 3× 41,5 % pozycji likwiduje się na +31 %, średnia na
  nominał spada do +0,95 %.
- **Funding jest kosztem tej samej skali co efekt:** short płaci netto w 41 % zdarzeń, średnio
  −1,15 %, w 5 % zdarzeń ponad −12 % — rynek częściowo wycenia spadek w fundingu.
- **Likwidacja liczona z dziennych maksimów, bez fundingu zmniejszającego depozyt** — przy
  ujemnym fundingu realna likwidacja przychodzi wcześniej; wynik 2×/3× jest raczej zawyżony.
- **Kogo nie ma:** TradFi (199), indeksy (5), stablecoin (1), listingi sprzed 2021 (80),
  okna poza końcem danych (12), redenominacja (1: BOBUSDT), archiwum spóźnione względem
  `onboardDate` (17, prawie wszystkie z 2021), brak fundingu w archiwum (3: BNX, ICP, TLM —
  ponowne listingi). Żadna grupa nie była wybrana po wyniku.

## Walidacja (zasada 16a)

Skill `data:validate-data` wczytany PRZED walidacją. Werdykt: **READY**.

- **Druga droga (niezależna):** `walidacja.py` liczy P&L wszystkich 569 zdarzeń wektorowo
  (merge + groupby na surowych plikach, bez `listing_events`): średnia **+2,12 %**, mediana
  **+13,54 %**, 67 likwidacji 1× — identycznie ze skryptem ✓.
- **Wrażliwość zapisana z góry (klastry):** kwartały (22) CI [−3,47; +7,72], t 0,74; lata (6)
  [−0,89; +5,14], t 1,38 — werdykt bez zmian w każdej wersji.
- **Ogon:** bez 5 % najgorszych zdarzeń średnia +7,81 %, bez 5 % najlepszych −1,18 % — wynik
  zależy od ogona obu stron; średnia jest właściwym przyrządem, bo to ona płaci.
- **Spójność:** cena + funding − koszt = 3,41 − 1,15 − 0,14 = 2,12 ✓; lata sumują się do n ✓.
- **Red flag:** mediana ≠ średnia o 11 pp — opisane jako skośność, nie błąd; min −122,8 %
  to likwidacja 1× plus ujemny funding (~−22 %) w oknie.
- **Bramka 16b** (`data:statistical-analysis`): efekt z CI klastrowym, mediana obok średniej,
  wersje z dźwignią i hedge jako opisowe, kontekst ~25 odczytów.

## Przegląd diffu (zasada 16c)

Skill `engineering:code-review` wczytany PRZED przeglądem. Diff: `data/fetch_listings.py`,
`backtest/listing_events.py`, `backtest/run_listings_nl1.py`, 20 testów, katalog rundy.

- Bezpieczeństwo sieci: wyłącznie stałe hosty (`data.binance.vision`, jego listing S3,
  `fapi.binance.com/exchangeInfo`) przez `http_get` (tylko https, przegląd P3); symbol z listingu
  kodowany `urllib.parse.quote`; adres nigdy z odpowiedzi serwera; 404 = brak pliku, inne błędy
  przerywają.
- Korektność: wejście dokładnie open d0+1 (brak świecy d0+1 → zdarzenie nierozliczalne, 0 takich),
  wyjście close d0+14, likwidacja z maksimów z obcięciem fundingu do dnia likwidacji (test),
  znak fundingu (test), wycofanie w oknie (test), CR1 = iid przy klastrach jednoelementowych (test).
- Znane uproszczenie: depozyt nie maleje od ujemnego fundingu przed likwidacją — opisane w (−).
- Testy 806/806, ruff/black czyste.

**Werdykt jednym zdaniem: Approve** — kolektor jest cienki i odtwarzalny, silnik zdarzenia
przetestowany na granicach, a wynik potwierdzony niezależną wektorową drogą.

## Wniosek

**Prostym językiem:** nowe monety na Binance zwykle tanieją w pierwszych dwóch tygodniach
(2 na 3 przypadki, typowo o kilkanaście procent), ale **co ósma podwaja cenę** i wtedy short
traci wszystko. Po uwzględnieniu tych wystrzałów i opłat funding zostaje ok. +2 % na zdarzenie,
czego nie da się odróżnić od zera. Dla Ciebie przy 3× to przegrana gra: prawie połowa pozycji
kończy się likwidacją.

**Technicznie:** NIEROZSTRZYGNIĘTY (t 0,87; CI [−2,7; +6,9]); rozkład o skrajnej skośności
(mediana +13,5 %, 11,8 % likwidacji przy 1×); funding częściowo wycenia spadek. Efekt, jeśli
istnieje, jest < ~7 % na zdarzenie — poniżej rozdzielczości przyrządu.

## Rekomendacja

1. **Seria NL: 1/1, STOP.** Warianty (krótsze okno, stop-loss na wystrzał, filtry „dużych”
   listingów, hedge BTC jako kryterium) na tych samych 569 zdarzeniach zakazane bez decyzji
   użytkownika — każdy byłby dopasowaniem do znanego już ogona.
2. **Nie grać tego z dźwignią 3×** — 41,5 % likwidacji to nie jest parametr do strojenia, tylko
   natura nowych monet.
3. Otwarte dla użytkownika (osobna hipoteza, nie wariant): short z twardym stopem na wystrzał to
   inny produkt (zmienia rozkład wypłat); wymagałby własnej karty i rachunku mocy.

## Użyte skille

Rejestr `runs/skille/nl1-nowe-listingi.jsonl` (`py tools/skill_audit.py raport --galaz
nl1-nowe-listingi`): **8 wczytań, 8 różnych skilli**, wszystkie przez Claude'a, przed pracą.

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź przed skillami, pre-rejestracja przed przebiegiem, katalog, bramki, DoD. |
| `anthropic-skills:clas5-quant` | pułapki: point-in-time data listingu, wycofane w zbiorze, redenominacje, błąd klastrowy, funding jako koszt tej samej skali, zakaz wyboru N po wyniku. |
| `engineering:testing-strategy` | 20 testów bez sieci, w tym `hypothesis` (P&L ≥ −1/L, monotoniczność względem maksimum). |
| `data:explore-data` | profil nowego zbioru: zgodność d0 z `onboardDate` → wykluczenie 17 spóźnionych okien PRZED przebiegiem; funding 1/2/4/8 h; brak fundingu dla 3 ponownych listingów. |
| `data:validate-data` | druga, wektorowa droga, wrażliwość klastrów, „kogo nie ma”. |
| `data:statistical-analysis` | średnia jako przyrząd przy skrajnej skośności, mediana opisowo, wersje z dźwignią opisowo. |
| `engineering:code-review` | przegląd diffu z bezpieczeństwem sieci — werdykt wyżej. |

**Pominięte (z powodem):** `security-review` — kolektor nie dodaje nowego hosta ani kluczy;
używa `http_get` (tylko https) i tych samych hostów Binance co P3, gdzie przegląd bezpieczeństwa
był wykonany; kontrola sieci w przeglądzie 16c wyżej. `dataviz` — bez wykresu;
`engineering:debug` — bez błędu wymagającego diagnozy (poprawiono oczekiwanie w teście).
