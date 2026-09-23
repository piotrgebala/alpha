# V1 — premia za ryzyko zmienności (DVOL − zrealizowana) jako cecha modelu 4h (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Jedna z trzech serii (L1 / V1 / G1)
> pre-rejestrowanych W JEDNYM COMMICIE przed jakimkolwiek przebiegiem. Decyzja użytkownika
> 2026-09-23: „wykonaj po kolei 3 warianty celem zebrania informacji na przyszłość".
> **NOWA SERIA V, licznik 1/1.** Wzorzec O1. Dane: P3 (Deribit DVOL).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

DVOL to „cena strachu" z rynku opcji: ile zmienności bitcoina na najbliższe 30 dni wyceniają
kupujący ubezpieczenie. Gdy wycena jest dużo wyższa niż zmienność faktycznie zrealizowana
w ostatnim miesiącu, rynek płaci wysoką premię za ochronę — podręcznik mówi, że to typowe
dla strachu i sprzyja odbiciu; gdy premia jest ujemna, rynek jest „za spokojny". Model dostaje
jedną liczbę: DVOL minus zrealizowana zmienność z ostatnich 30 dni (liczona z naszych świec 4h),
z jednodniowym opóźnieniem. Porównanie parami z modelem bez tej liczby.

## ID testu

**V1** — nowa hipoteza, rodzina „opcje/vol jako cecha kierunkowa" (katalog: opcje/vol ·
jednoaktywowa · kierunek · 4h · NIETKNIĘTE → ZMIERZONE po V1). **Licznik 1/1, STOP.** Inne
definicje (sam poziom DVOL, zmiana DVOL, skew, term structure, VRP jako TARGET) to warianty
tej samej rodziny — po STOP decyzja użytkownika.

## Metadane

- Branch: `lvg-cechy-zewnetrzne` (od `master` @ `28b96a5`); wspólny dla L1/V1/G1.
- Dane: świece 4h BTC (od 2021-01-01); `data/raw/external/deribit_dvol_BTC_1d.parquet`
  (P3: od **2021-03-24**, 95,9 % bazy), kolumna `close` (świeca 1D, zamknięcie dnia).
- Cecha: `vrp_30d = DVOL_d/100 − rv_30d`, gdzie `rv_30d` = odchylenie std log-zwrotów 4h w oknie
  180 świec (30 dni), annualizowane `× sqrt(2 190)`; DVOL dnia `d` dopięty do świec o
  `open ≥ d + 1 dzień 00:00 UTC`; staleness > 7 dni → NaN. Profil (sanity): drukowany w nagłówku
  skryptu (kwantyle, masa punktowa, acf1) — bez patrzenia na zwroty.
- Pipeline i ramiona jak O1: kontrola = `REVERSION_FEATURES`; V1 = kontrola + `vrp_30d`.
- Kod: `agents/external_features.py` (`compute_realized_vol_30d`, `compute_vrp_30d`), rejestr
  `external:`, testy przecieku i jednostkowe (jak L1). Skrypt `backtest/run_external_features_lvg.py V1`.

## Poprzedzające wyniki

- **P3**: DVOL BTC/ETH od 2021-03-24 (1 925 / 2 007 dni bazy); brama G1 „częściowo".
- **O1** (wniosek 66), **F1**, **wniosek 46** — jak w L1. **Faza 0:** `atr_pctrank_20d` (zmienność
  zrealizowana) była cechą reżimu, nie modelu; zrealizowana zmienność sama w sobie to
  transformacja OHLCV — nowa informacja w V1 to WYCENA opcyjna (DVOL), stąd cecha = różnica.
- **Katalog (families.md, opcje/vol):** mechanizm premii za ubezpieczenie; pułapka: DVOL to
  horyzont 30 dni, model ma horyzont 12 h — cecha działa jako STAN rynku, nie prognoza ruchu
  na 12 h (zapisane jako ograniczenie).

## Pre-rejestracja

- **Hipoteza i mechanizm:** wysoka premia (DVOL ≫ zrealizowana) = kupujący ubezpieczenie płacą
  za strach → asymetria: po strachu częściej odbicie; ujemna premia = samozadowolenie → ryzyko
  spadku. Kto traci: kupujący ochronę za drogo. Kierunek uczy model (interakcja z `return_lag_1`).
- **DOKŁADNIE JEDNA zmienna:** dodanie `vrp_30d`. Alternatywy odrzucone przed danymi: sam poziom
  DVOL (miesza reżim zmienności z premią), zmiana DVOL (szum), okno realized inne niż 30 dni
  (musi odpowiadać horyzontowi DVOL).
- **Przyrząd i kryterium (jedno ramię, m = 1):** jak O1/L1.
- **Mierzalność (zasada 18):** cecha NaN do ~2021-04-24 (DVOL od 03-24 + realized 30 dni → NaN
  w pierwszych ~1,5 foldach OOS); oczekiwane świece OOS ≈ 11 592 × 0,96 ≈ 11 100 →
  `expected_trades(11 100; 0,4038; 0,994) ≈ 6 580`, half-width 1,21 pp,
  `measurability_report(0,56; 0,5307; 6 580)` → **MIERZALNA**. Populacja świec V1 mniejsza niż
  kontroli o ~4 % — porównanie parowane na wspólnych świecach; różnica populacji raportowana.
- **Kontekst multiple testing** i **czego runda NIE robi:** jak L1.

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz lvg-cechy-zewnetrzne`)_
