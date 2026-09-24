# SW — cechy spoza wykresu: reguły i jeden model (2026-09-24)

> **STATUS: ZAMKNIĘTA — seria SW 9/9 zużyta, reguła STOP.** Etap 1: wszystkie 8 reguł traci po kosztach
> (−0,03 … −0,11 %/tr); 4 NEGATYWNE (funding, duzi gracze, premia za zmienność, strach i chciwość),
> 4 NIEROZSTRZYGNIĘTE. Etap 2: model ze wszystkimi 7 cechami, okno 365 dni: −0,050 %/tr [−0,091; −0,010],
> t −1,78 — NIEROZSTRZYGNIĘTY. **Duża ukryta przewaga (≥ +0,06 %/tr) wykluczona dla każdej cechy.**
> Przed kosztami część cech ma mały sygnał w przewidzianym kierunku (+0,02 … +0,05 %/tr), ale koszt handlu
> co 4 godziny (~0,08 %/tr) jest 2–3× większy (wniosek 90).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Audyt AU1 pokazał, że dane spoza wykresu (funding, otwarte pozycje, proporcje graczy long/short,
przewaga kupujących, premia za zmienność z opcji, napływ BTC na giełdy, indeks strachu i chciwości)
sprawdzaliśmy przyrządem, który słabego sygnału nie widzi: model uczony na 60 dniach gubił ok. 85 %
przewagi takiej cechy. Ta seria mierzy je jeszcze raz, dwiema drogami (decyzja użytkownika):
**etap 1** — każda cecha osobno jako prosta reguła „graj w kierunku, w którym cecha odbiega od swojej
typowej wartości z ostatniego roku” (kierunek z mechanizmu, zapisany z góry); **etap 2** — jeden model
ze wszystkimi cechami naraz, uczony na 365 dniach.

Czego się spodziewamy (uczciwie): audyt szacuje realne efekty tych cech na ok. 0 do +0,03 % na
transakcję po kosztach. Tak małego efektu ta seria **nie zobaczy** — ona odpowiada na inne pytanie:
**czy przegapiliśmy coś dużego** (rzędu +0,06 % na transakcję i więcej). Jeśli nic nie wyjdzie, pytanie
„czy w tych danych jest ukryta duża przewaga” będzie zamknięte naprawdę, a nie pozornie.

## ID testu

**SW** — nowa seria, **nowy licznik** (wniosek 13): etap 1 = 8 wariantów (reguł), etap 2 = 1 wariant
(model). Razem **m = 9**. Decyzja użytkownika 2026-09-24: „Oba etapy (Recommended)”.

## Metadane

- Gałąź `worktree-sw-cechy` (osobny katalog roboczy, żeby nocny dziennik działał na `master`).
- Kod: `agents/sw_features.py` (3 nowe cechy pozycjonowania + reguła + składanie ramki),
  `backtest/run_sw_series.py` (tryby `profil` / `etap1` / `etap2`), rejestr `sw_positioning:`
  w `agents/feature_registry.yaml`, testy przecieku w `agent_5_compliance/test_leakage.py` (+6).
- Komendy: `PYTHONUTF8=1 py -m backtest.run_sw_series profil|etap1|etap2`.
- Dane: świece 4h BTCUSDT od 2021-01-01 (zasada 20, `fetch_window`), funding Binance, archiwum
  `metrics` 5 min (P3), DVOL Deribit, CoinMetrics, Fear & Greed (`data/raw/external/`).
- `profil.txt` — profil cech BEZ celu i zwrotów (przed pre-rejestracją; dozwolone: nie patrzy na wynik).
- Pre-rejestracja: commit `e03cfa4` (wypchnięty przed przebiegiem). Wyniki: `raw_output_etap1.txt`,
  `raw_output_etap2.txt`; walidacja i opis brutto/lata/IC: `walidacja.txt`.

## Poprzedzające wyniki

- **AU1 (wniosek 87):** F1, O1, L1, V1, G1 (cecha jako 5. cecha modelu 60 dni) — cechy niezmierzone;
  wyrocznia q = 0,2 jako reguła +0,20 %/tr (trafność 55,28 %), w modelu 60 dni t ≈ 0, w modelu 365 dni
  +0,10 %/tr (t 3,5–4,8). Najlepszy kwintyl in-sample realnych cech: +0,08 do +0,107 % brutto → ~0 do
  +0,03 % netto.
- **TF1/TL1 (wnioski 73, 75):** funding i L/S jako reguły na innym horyzoncie — bez skutku (TL1 na obciętym
  uniwersum). **CP1** (premia Coinbase) — osobna seria, nie wchodzi tu.
- **WF1 (85):** okno 365/730 dni nie pomaga cechom z wykresu — dlatego model etapu 2 ich NIE dostaje
  (tylko rozcieńczają; AU1).
- **A1 (wnioski 48–50):** wzorzec pomiaru reguły bez modelu (`build_rule_signals`), kontrola N1 jako
  test regresji potoku (n 6 789, p 49,58 %, r̄ −0,107 %).

## Pre-rejestracja

### Cechy i kierunki (zapisane przed danymi; `agents/sw_features.py::SW_FEATURES`)

| cecha | źródło | kierunek reguły | mechanizm (rodzina katalogu) |
|---|---|---|---|
| `funding_rate` | stawka funding rozliczona ≤ świeca | **przeciw** (−) | tłok longów na dźwigni → korekta (D1) |
| `oi_change_24h` | log-zmiana OI w 24h (O1) | **przeciw** (−) | narastająca dźwignia → rozładowanie (E1) |
| `toptrader_ls_log` | log proporcji pozycji long/short 20 % największych kont | **za** (+) | duzi gracze lepiej poinformowani (E2) |
| `global_ls_log` | log proporcji kont long/short (wszystkie) | **przeciw** (−) | tłok drobnych graczy (E2) |
| `taker_imbalance_24h` | średnia 24h z log(kupno/sprzedaż agresorów) | **za** (+) | przepływ zleceń → kontynuacja |
| `vrp_30d` | DVOL − zmienność zrealizowana 30 dni (V1) | **za** (+) | premia za ryzyko (H1) |
| `ex_supply_change_7d` | zmiana podaży BTC na giełdach 7 dni (L1) | **przeciw** (−) | napływ na giełdy poprzedza sprzedaż (F1) |
| `fng_level` | Fear & Greed / 100 (G1) | **przeciw** (−) | chciwość → gorsze zwroty |

Nowe cechy (3 pierwsze wiersze z archiwum `metrics` poza OI): odczyty ściśle wewnątrz świecy
(open, open + 3h55m], jak O1; testy przecieku PRZED użyciem (zasada 2): shift-forward bit w bit,
dopięcie ignoruje odczyty od zamknięcia świecy, reguła trailing — 6 testów zielonych.

### Etap 1 — reguły (8 wariantów)

- **Reguła:** kierunek = znak_mechanizmu × sign(cecha − mediana cechy z ostatnich 365 dni, trailing,
  min. 180 dni historii). Cecha równa medianie → brak transakcji (funding: masa punktowa 31 % na stawce
  bazowej). Pewność stała; zero parametrów dobieranych do danych (365 = okno modelu etapu 2).
- **Silnik:** jak A1 — populacja = okna testowe potoku kontrolnego 60/28/28 (od 2021-03-02),
  `build_rule_signals` → `simulate_equity` (4h, V = 3, wejście limit po close, k = 1, wypełnienia po
  ścieżce, pojedyncze wyjście TP/SL/timeout, koszty i bramka kosztowa silnika).
- **Regresja potoku:** kontrola (4 cechy wykresu) musi odtworzyć N1 (n 6 789, p 49,58 %, r̄ −0,107 %).

### Etap 2 — jeden model (1 wariant; wyjątek od zasady 4 z decyzji użytkownika)

- **Cechy:** 7 cech SW bez `toptrader_ls_log` (roczna dziura w archiwum 2021-12 → 2022-12; silnik
  odrzuca wiersze z brakami — wyłączenie z powodu dostępności danych, przed wynikiem). Usuwanie
  duplikatów: |Spearman| > 0,9 na PIERWSZYM oknie uczenia (2021) — profil: brak par > 0,9 (max 0,74),
  więc model dostaje wszystkie 7. Bez cech z wykresu.
- **Silnik:** `collect_signals` walk-forward **365/28/28**, XGBoost jak w rundach (wagi klas `balanced`,
  early stopping na 20 % okna), V = 3, wejście i wyjście jak etap 1. Pierwszy test 2022-03-25.
- **Kontrola opisowa (0 wariantów):** ten sam potok 365/28/28 z 4 cechami wykresu na tych samych świecach.

### Kryterium (dla każdego z 9 odczytów) i reguła STOP

- Próg serii: Bonferroni m = 9 → **z\* = 2,773**.
- **POZYTYWNY:** t_neff zwrotu netto > 2,773 **ORAZ** dolny kraniec trafności (przy z\*) > p\*.
  Najpierw szukam przecieku (protokół A1), potem dopiero ogłaszam.
- **NEGATYWNY:** t_neff < −2,773 (reguła traci istotnie). Odwrócenie kierunku po wyniku = NOWA hipoteza
  (wniosek 49), tylko decyzją użytkownika.
- **NIEROZSTRZYGNIĘTY:** pozostałe przypadki.
- **Test kryterium w granicy dużego n:** przy rosnącym n kryterium wymaga coraz mniejszego efektu
  i nie karze osiągnięcia celu (brak warunku „przedział zawiera próg”).
- **STOP:** seria kończy się na tych 9 odczytach. Zakazane: inne okna mediany, progi skrajności,
  kombinacje cech w regułach, podzbiory lat, inne kierunki. Wynik POZYTYWNY → dalej wg ADR-09
  (spójność w wycinkach, dziennik papierowy), nigdy wprost kapitał.

### Mierzalność (zasada 18; `profil.txt`)

| ramię | n oczekiwane | pasmo trafności (±1,96) | SE r̄ netto | efekt hipotezy | t hipotezy | werdykt |
|---|---|---|---|---|---|---|
| reguły (8) | 8 085 – 10 885 | 0,94 – 1,09 pp | 0,017 – 0,020 % | +0,20 %/tr (AU1, q = 0,2) | 10,2 – 11,8 | **MIERZALNA** |
| model | 5 370 (abstynencja 40,4 %) | — | 0,024 % | +0,10 %/tr (AU1, okno 365) | 4,16 | **MIERZALNA** (≥ z\* + 0,84 = 3,61) |

- `measurability_report(0,5528; 0,5307; n)` dla reguł: MIERZALNA (pasmo ≤ 1,09 pp < luka 2,21 pp).
- Model: na trafności NIEMIERZALNA (52,93 % wyroczni wobec progu ±B 53,07 %) — próg ±B jest tu tylko
  diagnostyczny; o zwrocie decyduje p\* (zwrot netto > 0 ⇔ p > p\*), a na zwrocie efekt jest mierzalny.
- **Najmniejszy wykrywalny efekt (moc 80 %, z\*):** reguła ok. **+0,06 %/tr**, model ok. **+0,09 %/tr**.
  Realistyczne +0,03 %/tr (AU1) — **poza zasięgiem**; wynik „nierozstrzygnięty” będzie znaczył „brak
  dużej przewagi”, nie „brak przewagi”.
- SE skalowane z kontroli N1; reguły handlują prawie na każdej świecy (nakładanie transakcji większe niż
  w N1) — N_eff może być niższe, t hipotezy ma zapas ~3× na ten efekt.

## Wynik

**Regresja potoku:** kontrola odtworzyła N1 co do sztuki (n 6 789, p 49,58 %, r̄ −0,1069 %) — ZGODNA.

### Etap 1 — reguły (populacja: okna testowe od 2021-03-02; kierunek z góry)

| reguła (kierunek) | n | netto %/tr [CI 95 %] | mediana | t_neff | p | p\* | brutto %/tr [CI 95 %] | odczyt |
|---|---|---|---|---|---|---|---|---|
| funding_rate (−) | 8 460 | −0,058 [−0,091; −0,024] | −0,069 | −2,91 | 50,85 % | 53,30 % | +0,027 [−0,006; +0,061] | **NEGATYWNY** |
| oi_change_24h (−) | 10 220 | −0,042 [−0,073; −0,011] | −0,062 | −1,82 | 51,23 % | 52,95 % | +0,040 [+0,008; +0,071] | NIEROZSTRZYGNIĘTY |
| toptrader_ls_log (+) | 7 255 | −0,108 [−0,144; −0,072] | −0,115 | −4,24 | 49,15 % | 53,65 % | −0,024 [−0,060; +0,013] | **NEGATYWNY** |
| global_ls_log (−) | 10 277 | −0,028 [−0,059; +0,004] | −0,078 | −1,22 | 50,44 % | 51,57 % | +0,054 [+0,023; +0,085] | NIEROZSTRZYGNIĘTY |
| taker_imbalance_24h (+) | 9 432 | −0,057 [−0,089; −0,025] | −0,077 | −2,59 | 50,33 % | 52,69 % | +0,024 [−0,008; +0,057] | NIEROZSTRZYGNIĘTY |
| vrp_30d (+) | 9 692 | −0,069 [−0,102; −0,037] | −0,081 | −3,42 | 50,21 % | 53,02 % | +0,010 [−0,022; +0,043] | **NEGATYWNY** |
| ex_supply_change_7d (−) | 10 139 | −0,062 [−0,094; −0,030] | −0,083 | −2,75 | 50,28 % | 52,77 % | +0,021 [−0,011; +0,053] | NIEROZSTRZYGNIĘTY |
| fng_level (−) | 9 772 | −0,110 [−0,141; −0,078] | −0,084 | −3,86 | 50,26 % | 54,78 % | −0,027 [−0,059; +0,005] | **NEGATYWNY** |

- Koszt na transakcję 0,080–0,085 % (taker + poślizg, obie strony). Lata z dodatnim wynikiem netto: 0–2 z 6
  w każdej regule (`walidacja.txt`).
- „NEGATYWNY” znaczy tu: reguła traci więcej, niż mógłby tłumaczyć przypadek — ale przed kosztami jest
  bliska zera. **Odwrotny kierunek nie pomaga**: płaci ten sam koszt, a traci ewentualny drobny sygnał
  (np. funding: brutto +0,027 → odwrotnie ok. −0,027 − 0,085 = −0,11 %/tr).

### Etap 2 — jeden model (7 cech, okno 365/28/28, pierwszy test 2022-04-23)

| ramię | n | netto %/tr [CI 95 %] | mediana | t_neff | p | p\* | brutto %/tr [CI 95 %] | odczyt |
|---|---|---|---|---|---|---|---|---|
| **model SW** | 5 521 | −0,050 [−0,091; −0,010] | −0,072 | −1,78 | 50,50 % | 52,67 % | +0,029 [−0,012; +0,069] | **NIEROZSTRZYGNIĘTY** |
| kontrola (4 cechy wykresu, te same świece; opis) | 5 407 | −0,094 [−0,136; −0,052] | −0,123 | −4,40 | 48,77 % | 52,67 % | −0,015 [−0,057; +0,028] | — |

Abstynencja modelu 37,8 % (zakładane 40,4 %), n 5 521 (zakładane 5 370). Lata netto dodatnie: 2/5
(2024 +0,024, 2026 +0,012 %/tr).

## Co na plus (+) / Co na minus (−)

**(+)** Pytanie z audytu AU1 („czy przyrząd ukrył dużą przewagę w danych spoza wykresu”) jest zamknięte:
górny kraniec przedziału zwrotu netto żadnej reguły nie przekracza +0,004 %/tr, a modelu −0,010 %/tr —
efekty rzędu +0,06 %/tr (reguły) i +0,09 %/tr (model), które seria umiała wykryć, są wykluczone. Pomiar
czysty: kontrola odtworzona co do sztuki, trzy nowe cechy z testami przecieku przed użyciem, kierunki z góry.
Druga droga niezależna od silnika mówi to samo.

**(−)** Małe efekty (+0,02 … +0,05 %/tr przed kosztami) są widoczne, ale mniejsze niż koszt — seria nie
rozstrzyga, czy wolniejsza strategia (mniej transakcji) by je zachowała; to byłaby NOWA hipoteza
(inny horyzont), nie wariant tej serii. Model bez `toptrader_ls_log` (dziura w danych 2022). Reguła
„za medianą” to jedna z wielu możliwych form — zapisana z góry, ale inne formy (skrajne wartości) nie
zostały zmierzone i nie mogą już być na tej historii (STOP).

## Walidacja (16a) — `data:validate-data`

- **Regresja:** kontrola = N1 (n 6 789, p 49,58 %, r̄ −0,1069 %).
- **Druga droga, niezależna od silnika:** korelacja rang kierunku reguły z log-zwrotem close→close za
  12 godzin (3 świece), bez barier i kosztów: IC −0,010 … +0,031; trafność kierunku 49,8–51,1 % — zgodna
  z silnikiem (p 49,2–51,2 %). 5 z 8 IC dodatnich w przewidzianym kierunku (+0,019 … +0,031), p nominalne
  0,002–0,07 — bez korekty na nakładanie się okien 12h i autokorelację cech, więc zawyżone.
- **Kogo nie ma:** pierwsze 180 dni każdej cechy (rozbieg mediany; reguły de facto od połowy 2021, VRP od
  jesieni 2021), dziura `toptrader` 2021-12 → 2022-12, model bez `toptrader` i od 2022-04. Funding: 22 %
  świec bez kierunku (rozbieg mediany + ok. 16 % świec ze stawką równą medianie — masa punktowa, zgodnie
  z projektem reguły).
- **Czerwona flaga „wynik idealnie potwierdza hipotezę”:** nie — wynik jest przeciw hipotezie „duża przewaga”.
- **Werdykt: Ready** — liczby potwierdzone drugą drogą; zastrzeżenia opisane wyżej nie zmieniają odczytu.

## Statystyka (16b) — `data:statistical-analysis`

Efekt z przedziałem i medianą (mediana netto niższa od średniej w 7 z 8 reguł i w modelu — rozkład z prawym ogonem:
rzadkie duże wygrane, typowa transakcja na minusie). Licznik: seria m = 9, z\* = 2,773; poza serią ~30
wcześniejszych odczytów na tej historii. Przed kosztami przedział powyżej zera w 2/8 regułach przy 95 %
(`global_ls_log`, `oi_change_24h`), w 1/8 przy z\* (`global_ls_log`: +0,054 − 2,773 × 0,016 = +0,010) —
opis, nie kryterium (kryterium dotyczy zwrotu netto). Moc: efekt netto +0,03 %/tr był poza zasięgiem
(zapisane z góry), więc „nierozstrzygnięty” = „brak dużej przewagi”.

## Przegląd kodu (16c) — `engineering:code-review`

Zakres: `agents/sw_features.py`, `backtest/run_sw_series.py`, rejestr `sw_positioning:`, 6 testów przecieku.
Sprawdzone: dopięcie odczytów — przynależność do świecy liczona z `(ts − 1 ns)` zaokrąglonego do 4h, odczyt
o `open` i o `open + 4h` wykluczony (test), strefy czasowe zgodne (ns UTC), dziura `toptrader` widoczna jako
15,9 % braków; reguła — mediana trailing z bieżącą wartością (bez przyszłości, test); ramka modelu —
usuwanie duplikatów na pierwszym oknie uczenia; brak sieci, kluczy i zapisów poza `runs/`. Uwagi drobne:
SE hipotezy skalowane z N1 (opisane w pre-rejestracji); `build_sw_frame` ma zbędny `assert`.
**Werdykt: zatwierdzone — kod liczy dokładnie to, co zapisano w pre-rejestracji, a nowe cechy mają testy
przecieku sprzed pierwszego użycia.**

## Wniosek

**Prostym językiem:** sprawdziliśmy osiem rodzajów danych spoza wykresu — każdy osobno jako prostą regułę
i wszystkie razem w jednym modelu uczonym na roku danych. Żaden sposób nie zarabia po kosztach. W danych
jest ślad informacji (część cech lekko wskazuje dobry kierunek), ale ten ślad jest 2–3 razy mniejszy niż
koszt handlu co 4 godziny. Audyt pytał, czy stary przyrząd nie ukrył czegoś dużego — odpowiedź brzmi:
nie, nic dużego tu nie ma.

## Rekomendacja

1. Zapis w INDEX (wniosek 90): cechy spoza wykresu na BTC 4h — zmierzone, duża przewaga wykluczona;
   zastępuje odczyt „niezmierzone” z wniosku 87 dla tych ośmiu cech.
2. Seria SW zamknięta regułą STOP. Jeśli kiedyś wracać — tylko jako NOWA hipoteza o **wolniejszym
   horyzoncie** (np. pozycja na kilka dni, mniej transakcji, koszt dzielony na większy ruch), z własną
   pre-rejestracją i decyzją użytkownika; najmocniejszy ślad przed kosztami: proporcja kont long/short
   (przeciw tłumowi).
3. Katalog strategii (skill `quant-strategy-catalog`) ma nieaktualne statusy D1/E1/E2/F1/H1 (dane z P3,
   wyniki AU1/SW) — do aktualizacji w chmurze (notka w STATUS).

## Użyte skille

```
### Użyte skille — gałąź `worktree-sw-cechy` (rejestr automatyczny)
| 2026-09-24T19:02:10+02:00 | claude | `anthropic-skills:clas5-runda` |
| 2026-09-24T19:02:16+02:00 | claude | `anthropic-skills:clas5-quant` |
| 2026-09-24T19:02:24+02:00 | claude | `anthropic-skills:quant-strategy-catalog` |
| 2026-09-24T19:06:56+02:00 | claude | `data:explore-data` |
| 2026-09-24T19:15:32+02:00 | claude | `data:validate-data` |
| 2026-09-24T19:15:38+02:00 | claude | `data:statistical-analysis` |
| 2026-09-24T19:16:47+02:00 | claude | `engineering:code-review` |
Razem: 7 wczytań, 7 różnych skilli.
```

- `clas5-runda` — procedura: osobna gałąź w katalogu roboczym, pre-rejestracja wypchnięta przed przebiegiem.
- `clas5-quant` — kryterium dwuwarunkowe, mierzalność z kalibracją „ile przewagi przenosi model” (AU1),
  zakaz odwracania kierunku po wyniku.
- `quant-strategy-catalog` — rodziny D1/E1/E2/F1/H1 i kierunki z mechanizmu; wykrył, że statusy katalogu
  są nieaktualne (Rekomendacja 3).
- `data:explore-data` — profil cech bez celu (braki, masa punktowa funding 31 %, korelacje ≤ 0,74), z niego
  wyłączenie `toptrader` z modelu i brak duplikatów.
- `data:validate-data` — druga droga niezależna od silnika (IC) i pytanie „kogo nie ma”.
- `data:statistical-analysis` — mediana obok średniej, przedziały brutto, poprawka „2 z 8, nie 3”.
- `engineering:code-review` — przegląd dopięcia i reguły.
- Pominięte: `engineering:testing-strategy` (nowy moduł, ale testy według istniejącego wzorca przecieku
  z O1/L1 — bez nowej strategii testów), `dataviz` (brak wykresu), `security-review` (brak sieci i kluczy).

