# SZ1 — reguły wielkości pozycji dla portfela trend + premia Coinbase (2026-09-24)

> **STATUS: ZAMKNIĘTA (opisowo):** połączenie trendu i premii Coinbase ma lepszy profil niż każda
> osobno (korelacja 0,30): R0 (po połowie) CAGR +19,9 %, max obsunięcie 18,9 %; R1 (budżet ryzyka)
> +18,6 % / 17,7 %; **R2 (hamulec) gorzej: +10,3 % / 17,7 %** — hamulec włączony 36 % czasu.
> Depozyt przy tych regułach ~18–23 % kapitału. Pre-rejestracja `a635c8c`. Walidacja: **READY
> (Caveats: składowe in-sample)**; przegląd: **Approve**.
> Poprzednio: **PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „wykonaj wszystkie
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

## Wynik

`raw_output.txt` (6 s). Okres wspólny 2021-05-08 → 2026-06-30 (1 880 dni); korelacja dzienna
składowych **+0,30**.

| składowa (k = 1) | CAGR | zmienność | max obsunięcie | najgorszy miesiąc | ekspozycja |
|---|---|---|---|---|---|
| trend (likwidacja 2×) | +8,8 % | 19,7 % | 18,2 % | −8,2 % | 0,41× |
| premia Coinbase (likwidacja 3×) | +28,2 % | 35,1 % | 34,5 % | −13,9 % | 0,76× |

| reguła | CAGR | zmienność | max obsunięcie | Calmar | najgorszy miesiąc | k trend / k Coinbase | ekspozycja | depozyt | hamulec |
|---|---|---|---|---|---|---|---|---|---|
| **R0** po połowie | **+19,9 %** | 22,6 % | **18,9 %** | 1,06 | −6,9 % | 0,50 / 0,50 | 0,59× | 23,3 % | — |
| **R1** budżet ryzyka | **+18,6 %** | 21,7 % | **17,7 %** | 1,05 | −6,9 % | 0,66 / 0,36 | 0,56× | 23,2 % | — |
| **R2** R1 + hamulec | +10,3 % | 18,1 % | 17,7 % | 0,58 | −6,9 % | 0,53 / 0,31 | 0,42× | 17,9 % | 36,1 % czasu |

Per rok — R0: 2021 (od 05) −7,5 · 2022 +21,6 · 2023 +58,8 · 2024 −2,4 · 2025 +9,6 · 2026 +33,6 %;
R1: −4,0 · +11,2 · +50,1 · +8,5 · +7,6 · +28,9 %; R2: −4,0 · +11,2 · +23,8 · +1,9 · −0,6 · +23,5 %.

## Co na plus (+) / Co na minus (−)

**(+)** Połączenie dwóch słabo skorelowanych strategii obniża największe obsunięcie poniżej każdej
z osobna (18,9 % wobec 18,2 % i 34,5 %) przy zwrocie pomiędzy nimi; budżet ryzyka daje najłagodniejszy
rok (brak roku gorszego niż −4 %). Reguły ustalone z góry, estymaty tylko z przeszłości (test).
**(−)** **Składowe są in-sample** (najlepsze z ~31 testów), więc zwroty są zawyżone; wynik opisuje
PROFIL RYZYKA, nie prognozę. Hamulec R2 szkodzi: włącza się po typowym obsunięciu (~15–18 %),
a potem przez miesiące trzyma pół pozycji w czasie odbicia (4 włączenia, 36 % czasu). Okres od
2021-05 pomija mocne miesiące trendu I–IV 2021 (trend 8,8 % zamiast 13,8 %).

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY (Caveats)**: R0 przeliczone niezależnie numpy — CAGR **+19,9 %**,
obsunięcie **18,9 %** ✓; zrealizowana zmienność R1 21,6 %/rok przy celu 20 % ✓; hamulec R2:
włączenia 2023-01-14, 2023-08-12, 2024-11-09, 2025-10-11. `data:statistical-analysis`: różnice
R0 vs R1 w granicach szumu (5 lat → rozrzut CAGR ±20 pp); bez werdyktu. `engineering:code-review`:
kowariancja EWMA z danych < dnia ustalenia (test), sufit `min()`, hamulec z histerezą (test) — **Approve**.

## Wniosek

**Prostym językiem:** jeśli kiedyś grać te dwie strategie, to **razem**, bo słabo się ze sobą
wiążą i ich złe okresy rzadko się pokrywają. Najprostsza reguła — po połowie kapitału (albo trochę
więcej dla spokojniejszego trendu) — dawała na historii ok. **+19 % rocznie przy największym spadku
ok. 19 %**, z depozytem ok. **23 % kapitału** (trend 2× na altach, Coinbase 3× na BTC). **Hamulec
po stracie zaszkodził**: zmniejszał pozycje akurat przed odbiciem. Te liczby są z historii,
na której strategie wybraliśmy — rzeczywistość będzie gorsza.

## Rekomendacja

1. Do dziennika na żywo: portfel R1 (budżet ryzyka, cel 20 %, sufit 2) — bez hamulca R2.
2. Depozyt: trend 2× na każdej monecie, premia Coinbase 3× na BTC; łącznie ~23 % kapitału.
3. Nie stroić celu zmienności ani progów po tym wyniku (in-sample). Użyte skille: rejestr
   `runs/skille/sz1-wielkosc-pozycji.jsonl` (`clas5-runda`, `clas5-quant`, `testing-strategy`,
   `data:validate-data`, `data:statistical-analysis`, `engineering:code-review`); pominięte `dataviz`.
