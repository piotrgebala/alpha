# TS1 — podążanie za trendem (momentum w czasie) na koszyku top-20 perpetuali (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-23: „testuj dalej
> różne kombinacje" oraz doprecyzowanie „kontrakty futures z dźwignią 3×, longi i shorty".
> **NOWA SERIA TS (rodzina A1 katalogu na horyzoncie tygodniowym, uniwersum wielu monet),
> licznik 1/1, STOP.** Kandydat wybrany przez panel „co dalej" (5 propozycji, 2026-09-23/24):
> jedyny, który pasuje do sposobu handlu użytkownika (zakład o kierunek, long i short,
> perpetuale) i przechodzi bramę danych oraz mierzalności.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Każda moneta z 20 największych dostaje co tydzień własny zakład: **long, jeśli przez ostatnie
4 tygodnie urosła, short, jeśli spadła**. Wielkość pozycji zależy od tego, jak bardzo moneta się
waha: spokojniejsza dostaje więcej, rozchwiana mniej. Nigdy więcej niż 3× na jedną monetę, bo
tak handlujesz. To klasyczne „podążanie za trendem” z rynków futures, które działało przez ponad
sto lat na surowcach i obligacjach. Nikt w projekcie go jeszcze nie sprawdzał na horyzoncie
tygodni. Wcześniej mierzyliśmy tylko ruchy do 4 godzin i model odwracania ruchu na świecach
dziennych.

Uczciwie z góry: pomiar rozstrzygnie tylko **silny** trend. Szum na 5,4 roku danych wynosi
±18 % rocznie. Jeśli trend w krypto jest tak dobry jak w podręcznikach, zobaczymy go na granicy.
Jeśli jest słabszy, wynik wyjdzie nierozstrzygnięty.

## ID testu

**TS1** — nowa seria TS (momentum w czasie), licznik 1/1, STOP. Nazwa „TS”, bo „T1” to już
diagnostyka fundingu z 2026-09-22. Inne okna sygnału, inne cele zmienności, inne rebalanse,
sam BTC, inne uniwersum = warianty tej serii, zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `t1-trend-tsmom`.
- Dane: `data/raw/universe` (P2: świece 1d i funding CAŁEGO uniwersum USDT-M, łącznie z
  wycofanymi kontraktami, więc bez błędu przeżywalności), obcięte do **2021-01-01 → 2026-06-30**
  (zasada 20): 281 symboli; skład miesięczny top-20 po średnim obrocie z 30 dni przed miesiącem
  (`rebalance_premium.monthly_members`, jak X1/R1): 65 koszyków, 119 różnych symboli.
- Kod: `backtest/ts_momentum.py` (czyste funkcje, numpy) + `tests/test_ts_momentum.py` (13 testów:
  sygnał, test przyszłości sygnału i σ̂, σ̂ na stałych zwrotach, wagi z sufitem, symetria znaku
  w `hypothesis`, P&L = 0 przy płaskich cenach, pierwszy zwrot dzień po formowaniu, znak fundingu,
  fazy, H0). Skrypt: `backtest/run_ts_momentum_ts1.py` (na `runs/ZAMROZONE.txt`).
- Komendy: `PYTHONUTF8=1 py -m backtest.run_ts_momentum_ts1 --moc 100` → `moc.txt` (przed
  przebiegiem); `PYTHONUTF8=1 py -m backtest.run_ts_momentum_ts1` → `raw_output.txt`.

## Poprzedzające wyniki

- **Wniosek 69 (Y1/Y2):** kierunek BTC z cech wykresu na 1h/4h/1d — 48–50 % trafności wszędzie;
  „dalsze badanie horyzontu dziennego wymaga INNEGO zbioru informacyjnego lub INNEJ formuły”.
  TS1 zmienia FORMUŁĘ (reguła bez modelu, portfel wielu monet, skalowanie zmiennością) i
  HORYZONT (sygnał 28 dni, trzymanie 7 dni). Zbiór informacyjny pozostaje ten sam (ceny) — to
  słabość zapisana z góry (wnioski 11 i 69).
- **M1 (wniosek 35):** momentum na 4h z horyzontem 12 h — 49,7 %. **A2 (wnioski 51–53):** stan
  średnich, wybicie, struktura trendu na 4h — reguły „z ruchem” poniżej monety. Oba mierzyły
  horyzont godzin, na którym działa odwracanie; literatura lokuje momentum w tygodniach.
- **X1/X2 (wnioski 64–68):** momentum PRZEKROJOWE (mocne monety kontra słabe, neutralne na
  rynek) — +22 %/rok i +16 %/rok, nierozstrzygnięte; X1 wrażliwe na dzień tygodnia rebalansu.
  TS1 pyta o coś innego: czy KAŻDA moneta (i cały rynek) trzyma kierunek przez tygodnie —
  ekspozycja netto na rynek jest tu dozwolona i jest częścią zakładu. Wniosek 68 wymusza
  **7 faz tygodniowych naraz** — mierzona jest ich średnia.
- **Audyt dźwigni 3× (2026-09-23/24, bez katalogu — pytanie użytkownika):** werdykty projektu są
  liczone na jednostkę pozycji i nie zależą od dźwigni; 3× mnoży zysk, stratę i koszty; przy
  stałej 3× wyłącznik awaryjny i likwidacje zmieniają obraz. TS1 raportuje przełożenie na
  dźwignię jawnie (sekcja 4 wyniku).

## Pre-rejestracja

- **Hipoteza:** portfel momentum w czasie na top-20 perpetuali ma dodatni średni zwrot netto
  (po opłatach, poślizgu i realnym fundingu).
- **Mechanizm:** opóźniona reakcja na informację i stadne dołączanie do ruchu (likwidacje,
  stopy, FOMO); po drugiej stronie grający przeciw trendowi i zabezpieczający się
  (Moskowitz–Ooi–Pedersen 2012; Hurst–Ooi–Pedersen 2017). Nie wiemy, czy efekt przetrwał
  instytucjonalizację krypto po 2021 — prior umiarkowany.
- **DOKŁADNIE JEDNA zmienna:** reguła znaku (momentum w czasie) wobec braku zakładu; wszystkie
  parametry z literatury, bez siatki: okno sygnału **28 dni** (to samo co X1, najkrótsze
  z literatury 1–4 tygodni dla krypto → najwięcej epizodów), **σ̂ = √(365·EWMA(r², com = 60))**
  z danych ≤ t, **cel 40 %/rok na pozycję**, **sufit 3×** na monetę (zasada 5, `min()`), wagi
  1/N, formowanie co 7 dni, **7 faz po 1/7 kapitału**; koszt taker 0,05 % + poślizg 2 bps
  × obrót; funding realny per symbol (long płaci przy dodatniej stawce); wycofany kontrakt =
  gotówka.
- **Przyrząd i kryterium (jedno ramię, m = 1)** na dziennym szeregu zwrotu netto portfela
  (średnia 7 faz, % kapitału), CI z N_eff (`carry_hedged.summarize_pnl`):
  - **POZYTYWNY:** `t_neff > 1,96` ORAZ średnia powyżej **97,5 percentyla H0**;
  - **NEGATYWNY:** górny kraniec CI 95 % średniej poniżej zera;
  - inaczej **NIEROZSTRZYGNIĘTY**.
  Trafność (udział dni na plusie) NIE jest przyrządem — zwroty trendu są skośne (mało trafień,
  duże wygrane).
- **H0 (kontrola, 0 wariantów):** 100 portfeli z PRAWDZIWYMI znakami przesuniętymi cyklicznie
  w czasie o losową liczbę tygodni (≥ 8 tygodni od zera) — ta sama trwałość i ta sama zgodność
  znaków między monetami, te same wagi, koszty i funding; zniszczone jest tylko trafienie
  w moment. **Zmiana przed pre-rejestracją, z powodem:** pierwsza wersja H0 (niezależne losowe
  znaki per moneta, trwałość p_flip 0,214) dawała zmienność portfela 3,2 %/rok zamiast ~21 %,
  bo niezależne znaki znoszą się w koszyku skorelowanych monet — kontrola byłaby za łagodna.
  Obie wersje w `moc.txt`.
- **Mierzalność (zasada 18, `moc.txt`, bez patrzenia na regułę):** 1 969 dni; zmienność H0
  ~21,3 %/rok; se średniej empiryczne 7,3 %/rok (analityczne 9,2 %/rok — kryterium bierze
  większe); **half-width 95 % = 17,9 %/rok = 0,84 jednostki Sharpe'a**; q97,5 H0 = +13,0 %/rok.
  Obietnica literatury: zdywersyfikowany trend ~1 SR (MOP 2012) → przy zmienności ~21 %
  ≈ +21 %/rok > 17,9 → **MIERZALNA dla efektu podręcznikowego**; efekty 0,3–0,5 SR
  (6–11 %/rok) są **niewidoczne** — zapisane z góry. Moc 80 % wymaga SR ≥ ~1,2.
- **Oczekiwanie zapisane z góry:** NIEROZSTRZYGNIĘTY najbardziej prawdopodobny. Rynek
  2021–2026 miał kilka wielkich trendów (hossa 2021, bessa 2022, hossa 2024), więc wynik może
  zależeć od 2–3 epizodów — raport roczny obowiązkowy.
- **Opisowo (0 wariantów, bez werdyktu):** (a) „zawsze long” z tymi samymi wagami i różnica
  parowana TS1 − long (czy zysk to tylko dryf rynku); (b) sam BTC tą samą regułą; (c) 7 faz
  osobno (rozrzut); (d) przełożenie na dźwignię: mnożnik wag do brutto 3× kapitału i dźwignia
  Kelly'ego — CAGR i maksymalne obsunięcie (bez likwidacji; likwidacja wymaga dziennych
  high/low, których cache dla monet spoza BTC nie ma).
- **Kontekst multiple testing:** ~23 odczyty z 2026-09-23/24 w różnych seriach; TS1 to jedno
  ramię z własnym licznikiem.
- **Czego runda NIE robi:** nie stroi okna, celu zmienności ani dnia rebalansu; nie filtruje
  monet po wyniku; nie odwraca znaku; nie łączy z X1.

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz t1-trend-tsmom`)_
