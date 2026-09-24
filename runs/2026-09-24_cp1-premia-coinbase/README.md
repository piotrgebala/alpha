# CP1 — premia Coinbase jako sygnał kierunku BTC na tydzień (2026-09-24)

> **STATUS: ZAMKNIĘTA — POZYTYWNY wg kryterium pre-rejestrowanego (PIERWSZY w projekcie), ale
> NIE przechodzi korekty na liczbę testów:** +32,0 %/rok netto [+2,0; +62,1], t_neff 2,09,
> ponad 98 % portfeli H0 (q97,5 +28,1 %/rok). Przy ~28 odczytach w dwa dni próg rodzinny
> (Bonferroni) to t ≈ 2,9. Po odjęciu udziału trendu 28 dni zostaje +24 %/rok, t 1,67.
> Pre-rejestracja `3871a83` → przebieg → wynik w commicie scalającym. **Seria CP: 1/1, STOP.**
> Walidacja (16a): **Caveats**; przegląd diffu (16c): **Approve**.
> Decyzja użytkownika 2026-09-24: „sprawdź 3 nowe
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

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Pierwszy raz w projekcie strategia przeszła własne, zapisane z góry kryterium sukcesu.**
Granie BTC long albo short według tego, czy Amerykanie na Coinbase przepłacają ostatnio bardziej
niż zwykle, zarabiało po kosztach ok. **+32 % rocznie** (niepewność od +2 % do +62 %). Wszystkie
kontrole błędów przeszły: daty się zgadzają, a spóźniony sygnał traci powoli, co oznacza, że
wynik nie bierze się z zaglądania w przyszłość. **Ale:** w dwa dni sprawdziliśmy ~28 pomysłów,
a przy tylu próbach jeden taki wynik może wyjść przypadkiem. Część zysku to zwykły trend. Bez 10
najlepszych dni zostaje +16 % rocznie. To mocny kandydat do testu na nowych danych, a nie jeszcze
dowód. **Dźwignia:** rozsądnie ok. 1× kapitału na BTC; pełne 3× kapitału to obsunięcie 94 %.

---

_(sekcje poniżej po przebiegu)_

## Wynik

Pełny stdout: `raw_output.txt` (53 s). Dzienny zwrot netto, średnia 7 faz, % kapitału,
1 880 dni (2021-05 → 2026-06).

| miara | wartość |
|---|---|
| **średni zwrot netto [CI 95 %, N_eff]** | **+32,0 %/rok [+2,0; +62,1]** |
| t_neff | **+2,09** (próg 1,96) |
| H0 (100 portfeli, sygnał przesunięty w czasie) | q97,5 +28,1 %/rok; CP1 ponad **98 %** portfeli H0 |
| zmienność | 34,8 %/rok |
| **werdykt pre-rejestrowany** | **POZYTYWNY** (oba warunki) |
| próg rodzinny (~28 odczytów, Bonferroni jednostronny) | t ≈ 2,9 — **niespełniony** |

**Per rok (Σ netto):** 2021 −11,6 % · 2022 +35,1 % · 2023 +84,0 % · 2024 −8,9 % · 2025 +8,1 % ·
2026 (do 06) +58,3 %. **7 faz (%/rok):** +39,1 / +39,9 / +14,3 / +22,1 / +19,6 / +39,6 / +50,2 —
wszystkie dodatnie.

**Czy to trend w przebraniu (walidacja):** znak CP1 zgadza się z trendem 28 dni w 63,7 % dni;
korelacja dzienna 0,36; beta 0,36; **alfa po odjęciu trendu +24,0 %/rok [−4,1; +52,0], t 1,67**.
Przed ETF (do 2024-01-11): +43,1 %/rok [−5,0; +91,2]; po ETF: +20,0 %/rok [−23,7; +63,8].

**Przełożenie na dźwignię (opisowo, bez likwidacji):** reguła trzyma medianowo 0,76× kapitału
w BTC.

| dźwignia | CAGR | max obsunięcie |
|---|---|---|
| reguła (k = 1) | +29,7 %/rok | 34,3 % |
| ½ Kelly (k = 1,33, in-sample) | +37,6 %/rok | 44,0 % |
| Kelly (k = 2,65, in-sample) | +53,2 %/rok | 77,8 % |
| brutto 3× kapitału (k = 3,92) | +38,8 %/rok | **93,7 %** |

## Co na plus (+) / Co na minus (−)

**(+)**
- **Pierwszy wynik projektu spełniający oba pre-rejestrowane warunki** (t_neff > 1,96 i ponad
  q97,5 H0); wszystkie 7 faz dodatnie; dodatni przed i po ETF.
- **Brak śladu przecieku:** znaczniki zgodne (korelacja zmian Coinbase–perp 1,000 w tym samym
  dniu, ≈ 0 z przesunięciem); sygnał spóźniony o 1/2 dni daje +27,5 / +20,9 %/rok — łagodny
  spadek, a nie zapaść, której wymagałby przeciek.
- Nowy zbiór informacji (cena na innej giełdzie w innej walucie), mechanizm spójny (popyt USA).
- Niezależne przeliczenie fazy 0 identyczne (+39,10 %/rok).

**(−)**
- **Multiple testing:** ~28 odczytów w dwa dni; przy globalnej hipotezie zerowej jeden wynik
  t ≈ 2,1 jest spodziewany. Próg rodzinny (t ≈ 2,9) nie jest spełniony.
- **Część zysku to trend:** beta 0,36 wobec trendu 28 dni; sama alfa ma t 1,67.
- **Koncentracja:** bez 10 najlepszych dni +16 %/rok; 2 z 6 lat ujemne; 2023 niesie dużą część.
- **Jeden instrument:** szum ±31 %/rok; mediana dnia +0,016 % wobec średniej +0,088 %.
- **Kogo nie ma:** styczeń–kwiecień 2021 (rozbieg 90 dni); dni bez świecy Coinbase lub spot
  (0 braków w sygnale od startu). Wybór okien 7/90 z góry, bez siatki.

## Walidacja (zasada 16a)

Skill `data:validate-data` wczytany PRZED walidacją. Werdykt: **Caveats** — liczby poprawne,
przecieku brak; wymagane zastrzeżenia: multiple testing (~28), udział trendu, koncentracja.
Szczegóły: `walidacja.py` → `walidacja.txt` (czas, test opóźnienia, faza 0 niezależnie, trend,
koncentracja, dźwignia). **Bramka 16b** (`data:statistical-analysis`): efekt z CI, próg rodzinny
jawnie, mediana obok średniej, lata i fazy opisowo, Kelly oznaczony jako in-sample.

## Przegląd diffu (zasada 16c)

Skill `engineering:code-review` wczytany PRZED przeglądem. Diff względem master obejmuje też
commity bazowej gałęzi `ts-poza-proba` (pre-rejestracja TR1/TP1, `run_ts_momentum_oos.py`,
haki silnika) — przejrzane razem.
- Haki `signs_override` / `keep_fn` w `ts_momentum.portfolio`: domyślnie None → TS1 odtworzone
  co do liczby (+14,8 %/rok, t 1,76); testy: filtr zeruje pozycję bez renormalizacji, override
  równy sygnałowi daje identyczny wynik.
- `daily_premium`: zamknięcie spot = świeca 8h z 16:00 (zamyka się o 24:00, jak świeca dzienna
  Coinbase) — test; `premium_signal` bez przyszłości — test na dwóch cięciach.
- H0: przesunięcie cykliczne sygnału o wielokrotność 7 dni ≥ 8 tygodni.
- Testy 812/812, ruff/black czyste.

**Werdykt jednym zdaniem: Approve** — zmiana silnika jest wstecznie zgodna i przetestowana,
skrypt CP1 cienki, a moment czasowy sygnału sprawdzony testem i walidacją.

## Wniosek

**Prostym językiem:** premia Coinbase to **pierwszy sygnał, który przeszedł nasz z góry zapisany
test**: ok. +32 % rocznie po kosztach, bez śladu błędu w danych. Nie ogłaszamy jednak sukcesu,
bo w ciągu dwóch dni sprawdziliśmy prawie 30 pomysłów. Przy tylu próbach jeden taki wynik może
być szczęściem. Rozstrzygnie to dopiero test na danych, których jeszcze nie widzieliśmy.

**Technicznie:** POZYTYWNY wg pre-rejestracji (t_neff 2,09; > q97,5 H0); po korekcie rodzinnej
nieistotny; alfa ponad trend t 1,67; brak przecieku (test opóźnienia).

## Rekomendacja

1. **Seria CP: 1/1, STOP.** Żadnych wariantów okien/progów na tych samych danych.
2. **Test poza próbą (następny krok, bez decyzji bramkowej — ta sama reguła):** CP1 na
   danych 2026-07-01 → 2026-09-23 (Coinbase do 09-23 jest w cache; spot i perp dociągnąć) jako
   odczyt prospektywny z progiem obalenia z góry, jak TP1; potem dziennik na żywo.
3. Jeśli użytkownik chce grać tę regułę przed rozstrzygnięciem: najwyżej ~1× kapitału w BTC
   (½ Kelly in-sample to 1,33× wag reguły ≈ 1× kapitału), nigdy 3× kapitału (obsunięcie 94 %).

## Użyte skille

Rejestr `runs/skille/cp1-premia-coinbase.jsonl` (`py tools/skill_audit.py raport --galaz
cp1-premia-coinbase`): **5 wczytań, 5 różnych skilli** — `clas5-runda` (procedura),
`clas5-quant` (pułapki: składnik USDT/USD, zgodność zamknięć, trend w przebraniu),
`data:validate-data` (test opóźnienia jako test przecieku, alfa ponad trend),
`data:statistical-analysis` (próg rodzinny, zakres zamiast punktu), `engineering:code-review`
(przegląd razem z bazową gałęzią). **Pominięte:** `engineering:testing-strategy` — nowe testy to
3 pomocniki skryptu według planu z TS1 (ten sam wzorzec, wczytany w TS1); `quant-strategy-catalog`
— wczytany przy wyborze hipotez na master (2026-09-24); `dataviz` — bez wykresu.
