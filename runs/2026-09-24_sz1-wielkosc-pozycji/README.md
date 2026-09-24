# SZ1 — reguły wielkości pozycji dla portfela trend + premia Coinbase (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „wykonaj wszystkie
> 3 punkty” (punkt 2). Runda **opisowa, 0 wariantów przewagi, bez werdyktu** — reguły wielkości
> pozycji nie tworzą informacji (wniosek 45), mogą tylko zmienić profil ryzyka. Zasada 7:
> wielkość pozycji zostaje regułą (nie modelem ML).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Mamy dwóch kandydatów (trend tygodniowy i premia Coinbase), obu bez dowodu. Zanim ktokolwiek
postawi na nich pieniądze, trzeba zdecydować, ile kapitału dać każdemu i co robić po stracie.
Sprawdzamy trzy proste reguły ustalone z góry: (R0) po połowie kapitału, (R1) więcej dla
spokojniejszej strategii i całość ustawiona na wahania ok. 20 % rocznie, (R2) jak R1, ale po
spadku kapitału o 15 % zmniejszamy pozycje o połowę, aż strata zmaleje do 7,5 %.

## Metadane

- Branch `sz1-wielkosc-pozycji`. Kod: `backtest/sizing.py` + `tests/test_sizing.py` (5 testów:
  R0 = średnia, sufit i odwrotność zmienności, brak przyszłości, hamulec z histerezą, podsumowanie),
  `backtest/run_sizing_sz1.py` (na `runs/ZAMROZONE.txt`). Komenda:
  `PYTHONUTF8=1 py -m backtest.run_sizing_sz1` → `raw_output.txt`.
- Składowe (k = 1, dzienne zwroty netto): **trend** = TS1 z likwidacją izolowaną **2×** na każdej
  monecie (rekomendacja LQ1), **premia Coinbase** = CP1 z likwidacją izolowaną **3×** na BTC
  (high/low BTC z `data/raw/universe_ohlc`). Okres wspólny od 2021-05 (rozbieg CP1).

## Pre-rejestracja (reguły i parametry z góry, z uzasadnieniem)

- **R0:** k = ½ dla każdej składowej (równy podział — punkt odniesienia).
- **R1 (budżet ryzyka):** co 7 dni wagi ∝ 1/σ_s z kowariancji EWMA (com 45 ≈ 3 miesiące) liczonej
  z danych **sprzed** dnia ustalenia; skala tak, by przewidywana zmienność portfela = **20 %/rok**
  (poziom, przy którym obsunięcia rzędu 30–40 % zdarzają się raz na kilka lat — akceptowalny dla
  użytkownika z celem zwrotów „kierunkowych”); **sufit k ≤ 2** na składową (zasada 5); przed 60
  dniami danych — R0.
- **R2:** R1 + hamulec: obsunięcie > **15 %** → mnożniki × **0,5**, powrót, gdy obsunięcie
  < **7,5 %** (histereza, żeby nie przełączać co tydzień).
- **Raport (opisowo):** CAGR, zmienność, maksymalne obsunięcie, Calmar, najgorszy miesiąc,
  mediany mnożników, ekspozycja (nominał/kapitał) i **depozyt** = ekspozycja trendu/2 +
  ekspozycja Coinbase/3; per rok; udział czasu z hamulcem.
- **Czego runda NIE robi:** nie wybiera celu zmienności, progu hamulca ani sufitu po wyniku;
  nie ogłasza „najlepszej” reguły — składowe są in-sample (najlepsze z ~31 testów), więc liczby
  są opisem profilu ryzyka, nie prognozą.

---

_(sekcje poniżej po przebiegu)_
