# CP1 — premia Coinbase jako sygnał kierunku BTC na tydzień (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „sprawdź 3 nowe
> hipotezy”. **NOWA SERIA CP (zbiór informacyjny: cena na innej giełdzie — popyt z USA),
> licznik 1/1, STOP.** Pierwsza z trzech nowych hipotez tej sesji (CP1, TF1, TL1).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Gdy Amerykanie (fundusze, ETF-y, instytucje) kupują bitcoina, robią to głównie na Coinbase za
dolary. Wtedy cena na Coinbase bywa trochę wyższa niż na Binance. Hipoteza: jeśli przez ostatni
tydzień ta nadwyżka była większa niż zwykle, cena BTC w następnym tygodniu częściej rośnie
(i odwrotnie). Gramy long albo short BTC na perpetualu, co tydzień, z tą samą wielkością pozycji
co w TS1. Uczciwie z góry: jeden instrument to dużo szumu, więc test zobaczy tylko bardzo silny
sygnał. Sygnał w 64 % dni pokrywa się z trendem z 4 tygodni, więc może się okazać, że to ten
sam trend w przebraniu — to sprawdzimy.

## ID testu

**CP1** — nowa seria CP, 1/1, STOP. Inne okna (7/90), inne progi, inne giełdy = warianty.

## Metadane

- Branch: `cp1-premia-coinbase` (utworzony z `ts-poza-proba` po commicie haków silnika
  `signs_override`/`keep_fn` w `backtest/ts_momentum.py`).
- Dane (lokalne, zasada 20 — od 2021-01-01): Coinbase BTC-USD 1d (`data/raw/external`, P3),
  spot Binance BTC-USDT 8h (C1; zamknięcie dnia = świeca 16:00), perpetual BTCUSDT 1d i funding
  (`data/raw/universe`). 2 007 dni premii, 0 braków w sygnale od startu.
- Skrypt: `backtest/run_coinbase_cp1.py` (na `runs/ZAMROZONE.txt`), testy
  `tests/test_coinbase_cp1.py` (3). Komendy: `PYTHONUTF8=1 py -m backtest.run_coinbase_cp1 --moc`
  → `moc.txt`; `PYTHONUTF8=1 py -m backtest.run_coinbase_cp1` → `raw_output.txt`.

## Poprzedzające wyniki

- **Wniosek 69:** kierunek BTC z cech wykresu na 1h/4h/1d — ~50 %. CP1 używa innego zbioru
  informacji (cena na innej giełdzie w innej walucie).
- **TS1 (wniosek 70):** trend tygodniowy; sam BTC tą regułą +21,4 %/rok [−7,7; +50,5] opisowo —
  punkt odniesienia; CP1 porównany opisowo z trendem na BTC (korelacja).
- **F1, O1, L1, V1, G1:** dane spoza wykresu jako 5. cecha modelu 4h — zero. CP1 to reguła
  tygodniowa, nie cecha modelu 4h.

## Pre-rejestracja

- **Hipoteza:** znak (średnia premii z 7 dni − średnia z 90 dni) przewiduje kierunek BTC
  w następnym tygodniu.
- **Mechanizm:** popyt spot z USA (instytucje, ETF-y po 2024) płynie przez Coinbase i wyprzedza
  arbitraż i ruch ceny na rynku globalnym; odchylenie od 90-dniowej normy usuwa stały składnik
  kursu USDT/USD. Prior: umiarkowany, bez recenzowanego pomiaru na tym horyzoncie.
- **DOKŁADNIE JEDNA zmienna:** sygnał znaku z premii zamiast znaku zwrotu 28 dni; cała reszta
  = silnik TS1 (σ̂ EWMA, cel 40 %/rok, sufit 3×, 7 faz tygodniowych, koszt 0,07 % × obrót,
  realny funding). Okna 7/90 ustalone z góry (tydzień decyzji / kwartał normy), bez siatki.
- **Kryterium (jedno ramię):** dzienny zwrot netto (średnia 7 faz): POZYTYWNY, gdy t_neff > 1,96
  ORAZ średnia > q97,5 H0 (sygnał CP1 przesunięty cyklicznie o losową liczbę tygodni, 100
  portfeli); NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (`moc.txt`):** 1 880 dni od 2021-05-01; zmienność H0 35,1 %/rok; **half-width
  31,5 %/rok = 0,90 SR**; q97,5 H0 +28,1 %/rok. Założony efekt SR ≈ 1 (≈ +35 %/rok) >
  31,5 → **MIERZALNA na granicy**; efekty SR ≤ 0,8 niewidoczne — zapisane z góry.
- **Opisowo:** zgodność znaku z trendem 28 dni (ex ante 63,7 % dni), korelacja CP1 z trendem na
  BTC, lata, fazy.
- **Kontekst multiple testing:** ~28 odczytów w dwa dni.
- **Czego runda NIE robi:** nie stroi okien, nie dodaje progu martwej strefy, nie łączy z TS1.

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz cp1-premia-coinbase`)_
