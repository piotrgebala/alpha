# SW — cechy spoza wykresu: reguły i jeden model (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed przebiegiem etapów 1 i 2).**

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

_(sekcje Wynik, Co na plus/minus, bramki, Wniosek, Rekomendacja, Użyte skille — po przebiegu)_
