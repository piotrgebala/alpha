# RU3 — korekta daty startu TR1 i X2 (2026-09-24)

> **STATUS: ZAMKNIĘTA — korekta danych, 0 wariantów.** TR1 od 2021-02: +15,5 %/rok [+0,2; +30,8],
> t_neff 1,99, ponad 100 % losowań H0 → formalnie **POZYTYWNY** według kryterium TR1. **Nie jest to
> potwierdzenie:** wynik był znany z audytu AU1 przed rundą, leży poniżej progu rodzinnego ~2,9, a cały
> przyrost wobec RU2 pochodzi z 82 dni hossy altcoinów w lutym–kwietniu 2021 (od 2022: +11,4 %/rok, t 1,32).
> X2 (średnia 7 faz): +21,9 %/rok [−5,1; +48,9], t 1,59 → **NIEROZSTRZYGNIĘTY**, bez zmian.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Audyt AU1 znalazł ostatni ślad dziury w danych: dwie rundy (trend na monetach 21–50 i momentum na
top-50) zaczynały się od maja 2021, bo w obciętym katalogu brakowało monet na luty–kwiecień. W pełnych
danych monet jest dość, więc przeliczamy obie rundy od lutego 2021 — tymi samymi regułami.

**Wynik:** trend na monetach z miejsc 21–50 przekracza teraz formalną poprzeczkę (t 1,99 przy progu
1,96). Wygląda to lepiej, niż jest. Trzy powody: (1) liczbę znaliśmy już z audytu, więc runda niczego
nie „przewidziała”; (2) sprawdziliśmy już ok. 30 pomysłów na tej samej historii, a przy tylu próbach
uczciwa poprzeczka to ok. 2,9, nie 1,96; (3) cała poprawa to trzy miesiące szalonej hossy altcoinów
z początku 2021 r. — rynku, który użytkownik sam uważa za inny niż dzisiejszy. Od 2022 r. ta sama
reguła daje ok. +11 % rocznie z przedziałem od −5 do +28 %, czyli „może coś jest, ale nie wiadomo”.
Momentum na top-50 bez zmian: nierozstrzygnięte.

## ID testu

RU3 — korekta danych (ciąg RU1/RU2), 0 wariantów; decyzja użytkownika 2026-09-24 („RU3: poprawna data startu”).

## Metadane

- Branch `ru3-data-startu`; pre-rejestracja + skrypt w commicie `e4c2350` (przed przebiegiem).
- Komenda: `PYTHONUTF8=1 py -m backtest.run_start_fix_ru3` → `raw_output.txt`.
- Dane: `data/raw/universe_full` (685 kontraktów, w tym wycofane), świece 1d i funding, 2021-01-01 → 2026-06-30
  (styczeń 2021 tylko jako rozbieg sygnałów; ocena od 2021-02-01).
- Koszt: taker + poślizg z `config/settings.yaml` (0,07 % obrotu), funding zrealizowany.
- `walidacja.txt` — wynik bramki 16a/16b (skrypt walidacyjny w scratchpadzie sesji; te same funkcje silnika
  co runda, sprawdzone niezależnie w AU1 co do 1e-17).

## Poprzedzające wyniki

- TR1 na pełnym uniwersum od 2021-05 (RU2): +13,0 %/rok, t 1,63. X2 (RU2): +23,1 %/rok, t 1,60 (jedna faza).
- **AU1 (wniosek 87) policzył już oba warianty w audycie:** TR1 od 2021-02 +15,5 %/rok, t 1,99; X2
  średnia 7 faz +21,9 %/rok, t 1,59. **Wyniki są więc znane przed tą rundą** — RU3 porządkuje zapis,
  a jej wynik NIE może być cytowany jako potwierdzenie (oglądany po fakcie).

## Pre-rejestracja

- **JEDNA zmienna:** data startu 2021-05-01 → 2021-02-01 (pełne uniwersum pozwala).
- **TR1:** reguła TS1 na miejscach 21–50 po obrocie, 7 faz, H0 z TS1 (100 przesunięć); kryterium jak TR1:
  POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0.
- **X2:** top-50, nogi po 10, trzymanie 7 dni — **średnia 7 faz** (różne dni startu tygodnia), bo pojedyncza
  faza zależy od dnia rebalansu (wniosek 68; AU1: zmiana dnia z soboty na poniedziałek dawała fałszywe t 2,52);
  kryterium X2: POZYTYWNY, gdy t_neff > 1,96.
- **Odczyt:** zapis porządkowy; próg rodzinny ~2,9 (~30 odczytów) pozostaje punktem odniesienia.

## Wynik

| reguła | okres | dni | zwrot netto %/rok [CI 95 %] | mediana/dzień | t_neff | kryterium |
|---|---|---|---|---|---|---|
| TR1 (miejsca 21–50) | 2021-02 → 2026-06 | 1 969 | **+15,5** [+0,2; +30,8] | +0,013 % | **1,99** | **POZYTYWNY** (H0 q97,5 +11,2 %; TR1 ponad 100 % losowań) |
| TR1 — dla porównania RU2 | 2021-05 → 2026-06 | 1 880 | +13,0 [−2,6; +28,7] | +0,010 % | 1,63 | NIEROZSTRZYGNIĘTY |
| TR1 — opisowo, po fakcie | 2022-01 → 2026-06 | 1 642 | +11,4 [−5,5; +28,4] | +0,008 % | 1,32 | (brak — odczyt opisowy) |
| X2 (top-50, średnia 7 faz) | 2021-02 → 2026-06 | 1 969 | +21,9 [−5,1; +48,9] | +0,047 % | 1,59 | NIEROZSTRZYGNIĘTY |
| X2 — opisowo, po fakcie | 2022-01 → 2026-06 | 1 642 | +17,2 [−10,9; +45,2] | +0,047 % | 1,20 | (brak) |

- **TR1 per rok (suma):** 2021 +32,2 % (w tym luty–kwiecień +14,0 % w 82 dniach) · 2022 +14,3 · 2023 +13,1 ·
  2024 +9,4 · 2025 +13,2 · 2026 (pół roku) +1,3. Dodatni w 6/6 latach. 7 faz: +14,6…+18,4 %/rok — zgodne.
- **X2, 7 faz na wspólnym oknie:** pon +38,8 · wt +22,8 · śr +13,0 · czw +24,8 · pt +12,2 · sob +16,9 · nd +25,2 %/rok.
  Rozrzut 12–39 %/rok tylko od dnia tygodnia — dlatego odczyt pojedynczej fazy jest niewiarygodny (wniosek 68).
  (W `raw_output.txt` linia „7 faz osobno” liczy każdą fazę na jej pełnym zakresie, łącznie z 0–6 dniami przed
  wspólnym oknem — stąd różnice ≤ 1 pkt wobec tej listy; średnia 7 faz liczona jest na wspólnym oknie.)
- **X2 per rok:** 2021 +41,2 · 2022 −0,3 · 2023 +11,7 · 2024 +9,9 · 2025 +27,6 · 2026 (pół roku) +28,2 %.

**Jak czytać „%/rok”:** średni dzienny zwrot netto × 365 (bez procentu składanego), w % kapitału portfela.
Przedział 95 % z N_eff (korekta na zależność kolejnych dni; tu N_eff = n).

## Co na plus (+) / Co na minus (−)

**(+)** Poprawiony błąd danych: obie rundy liczone od właściwej daty, na pełnym uniwersum (koszyki w dodanych
miesiącach pełne: 30 i 50 monet). TR1 dodatni w każdym roku i w każdej z 7 faz — to spójność, której szczebel 2
drabiny dowodów (ADR-09) wymaga. Odtworzenie RU2 co do 1e-17 potwierdza, że zmieniła się tylko data startu.

**(−)** Wynik znany przed rundą (AU1) — pre-rejestracja chroni tu tylko przed zmianą reguły, nie przed wyborem
po fakcie. Poprawa t 1,63 → 1,99 pochodzi w całości z 82 dni lutego–kwietnia 2021 (hossa altcoinów). Przy
~30 odczytach na tej samej historii poprzeczka rodzinna to ~2,9 — TR1 jej nie osiąga. X2 bez zmian, szeroki
przedział i duża wrażliwość na dzień tygodnia.

## Walidacja (16a) — `data:validate-data`

- **Niezależne odtworzenie:** TR1 od 2021-05 w tym samym kodzie = RU2 (1 880 dni, +13,0 %, t 1,63);
  różnica dzienna RU3 vs RU2 na wspólnych dniach po tygodniu rozruchu max 1,4·10⁻¹⁷ (1 873 dni). X2 faza
  sobotnia = RU2 co do 0 (1 851 dni po rozruchu; 1 886 dni, +23,1 %, t 1,60). t policzone ręcznie (numpy)
  = t_neff z `summarize_pnl` (1,99 / 1,59). Średnia 7 faz X2 = średnia średnich faz (21,95 %), 0 braków w panelu.
  Silnik (`portfolio`, `long_short_returns`) sprawdzony niezależną implementacją w AU1.
- **Kogo nie ma / kto doszedł:** doszły 82 dni lutego–kwietnia 2021 (Σ TR1 +14,0 %) — rynek sprzed 2022,
  który użytkownik uważa za odmienny. Funding kompletny: każdy członek top-50 w każdym miesiącu (także
  luty–kwiecień 2021) ma plik fundingu — 0 braków. Styczeń 2021 służy tylko jako rozbieg sygnałów (28 dni).
- **Red flag „wynik idealnie potwierdza hipotezę”:** tak — liczba przekracza 1,96 dokładnie o włos i była znana
  z góry; opisane w werdykcie.
- **Werdykt: Caveats** — obliczenia potwierdzone; zastrzeżenia: znany wynik, próg rodzinny, zależność od 2021.

## Statystyka (16b) — `data:statistical-analysis`

Efekt z przedziałem zamiast samego t; mediana obok średniej (TR1 +0,013 %/dzień przy średniej +0,042 %;
X2 +0,047 % przy +0,060 % — rozkład prawoskośny, średnią ciągną duże dni). Licznik: RU3 = 0 nowych wariantów,
ale TR1 i X2 należą do ~30 odczytów na tej samej historii — Bonferroni daje próg ~2,9; TR1 1,99 i X2 1,59
leżą poniżej. Moc (AU1): przy prawdziwym +10 %/rok test na 5,4 roku wykrywa efekt w ~25 % przypadków —
„nierozstrzygnięty” oznacza za mało lat, nie brak zjawiska. Odczyt od 2022 jest opisowy, dopisany po obejrzeniu
wyniku (bo użytkownik uważa rynek sprzed 2022 za inny), i nie ma kryterium.

## Przegląd kodu (16c) — `engineering:code-review`

Jeden nowy skrypt (`backtest/run_start_fix_ru3.py`), składany z przetestowanych funkcji silnika; bez sieci,
kluczy i zapisu plików. Uwagi: (1) linia „7 faz osobno” liczy fazy na pełnym zakresie zamiast na wspólnym oknie —
tylko opis, bez wpływu na kryterium, wyjaśnione w Wyniku; (2) import `_null` z zamrożonego `run_ts_momentum_ts1`
— akceptowalny, bo plik zamrożony się nie zmienia. **Werdykt: zatwierdzone — kod liczy to, co zapisano
w pre-rejestracji, odtwarza RU2 co do 1e-17, uwagi dotyczą wyłącznie opisu.**

## Wniosek

**Prostym językiem:** po naprawieniu daty startu trend na średnich monetach (miejsca 21–50) formalnie
przechodzi próg istotności, ale to zasługa trzech miesięcy hossy z 2021 r., a liczbę znaliśmy z góry.
Nie traktujemy tego jako dowodu. Obraz jest ten sam co wcześniej: trend tygodniowy na koszyku monet daje
na historii ok. +10–15 % rocznie, zawsze na granicy tego, co da się odróżnić od przypadku. Momentum
przekrojowe (kupuj najmocniejsze, sprzedawaj najsłabsze) — bez zmian, nierozstrzygnięte.

## Rekomendacja

1. Zapis TR1 i X2 w INDEX zastąpić liczbami RU3 (wniosek 88); werdykty opisywać jako „ślad, nie dowód”.
2. Żadnej nowej reguły na tej historii — rozstrzyga dziennik prospektywny (ADR-09, szczebel 3).
3. Dalej zgodnie z decyzją użytkownika: X1 do dziennika na żywo (osobna reguła papierowa), potem seria
   „cechy spoza wykresu jako reguły”.

## Użyte skille

```
### Użyte skille — gałąź `ru3-data-startu` (rejestr automatyczny)
| 2026-09-24T17:55:02+02:00 | claude | `anthropic-skills:clas5-runda` |
| 2026-09-24T17:55:06+02:00 | claude | `anthropic-skills:clas5-quant` |
| 2026-09-24T17:56:38+02:00 | claude | `data:validate-data` |
| 2026-09-24T17:56:44+02:00 | claude | `data:statistical-analysis` |
| 2026-09-24T17:57:33+02:00 | claude | `engineering:code-review` |
Razem: 5 wczytań, 5 różnych skilli.
```

- `clas5-runda` — procedura: katalog, INDEX, bramki, DoD. **Wczytany po commicie pre-rejestracji i po
  przebiegu** (odstępstwo od zasady 19: skill przed pracą). Wpływ ograniczony — konfiguracja była w całości
  przesądzona przez AU1 i RU2 (0 decyzji projektowych), ale odstępstwo odnotowuję.
- `clas5-quant` — przypomnienie kryteriów i zakazu cytowania wyniku oglądanego po fakcie; też po przebiegu.
- `data:validate-data` — odtworzenie RU2 i pytanie „kto doszedł” (82 dni 2021 niosą cały przyrost).
- `data:statistical-analysis` — mediana obok średniej, próg rodzinny, odczyt od 2022 oznaczony jako opisowy.
- `engineering:code-review` — przegląd skryptu; jedna uwaga o opisie faz.
- Pominięte: `quant-strategy-catalog` (brak nowej hipotezy), `data:explore-data` (brak nowego zbioru danych),
  `dataviz` (brak wykresu).
