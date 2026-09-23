# V1 — premia za ryzyko zmienności (DVOL − zrealizowana) jako cecha modelu 4h (2026-09-23)

> **STATUS: ZAMKNIĘTA — NEGATYWNY** (zwrot netto −0,076 % [−0,120; −0,031] na transakcję,
> t_neff −2,60; trafność 50,49 % [49,21; 51,77] wobec progu 53,42 %). Wobec kontroli na tych
> samych świecach **+0,018 pp [−0,037; +0,074]** — nieodróżnialne od zera; cecha zmienia
> kierunek w 25,7 % wspólnych transakcji i podnosi abstynencję z 40,4 % do 47,7 %. Punktowo
> najlepsza z trzech serii dnia (i porównywalna z O1), ale nadal 1,7 pp poniżej progu górnym
> krańcem CI. Jedna z trzech serii pre-rejestrowanych w jednym commicie (`3278442`).
> **Seria V: 1/1, STOP.** Walidacja (16a): **READY**; przegląd diffu (16c): **Approve**
> (wspólny, w README L1). Decyzja użytkownika 2026-09-23: „wykonaj po kolei 3 warianty".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**„Cena strachu" z rynku opcji (DVOL) porównana ze zmiennością faktycznie zrealizowaną daje
modelowi 4h trochę lepsze wyniki — trafność 50,5 % zamiast 49,6 %, strata −0,076 % zamiast
−0,107 % na transakcję — ale to wciąż strata, a poprawa parami (+0,018 punktu) mieści się
w przedziale z zerem.** Model z tą cechą częściej odmawia decyzji (48 % świec zamiast 40 %),
co samo w sobie poprawia średnią, bo odpadają najsłabsze decyzje. Próg opłacalności 53,4 %
jest poza przedziałem. **Wynik negatywny**, choć spośród pięciu źródeł spoza wykresu
sprawdzonych dziś (OI, on-chain, DVOL, F&G, wcześniej funding) DVOL i OI są jedynymi, które
w ogóle coś poruszają.

---

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

## Wynik

Komenda: `py -m backtest.run_external_features_lvg V1` (`PYTHONUTF8=1`; 6 s; `raw_output.txt`).
Cecha: NaN 498 / 12 042 świec (do 2021-03-24; pierwszy fold OOS pominięty → 68 aktywnych);
rozkład p05 −0,080, p50 +0,072, p95 +0,271 (premia zwykle dodatnia: DVOL wyżej niż zrealizowana);
masa punktowa 0,03 %; acf1 0,99. Korelacja z kontrolą: wszystkie |r| ≤ 0,02 — informacja
niezależna od cech ceny/wolumenu.

| ramię | n | r̄ netto | CI 95 % | mediana | t_neff | N_eff | p | CI 95 % (p) | p* | abstynencja |
|---|---|---|---|---|---|---|---|---|---|---|
| kontrola | 6 789 | −0,1069 % | [−0,1487; −0,0650] | −0,1036 % | −4,26 | 4 919 | 49,58 % | [48,39; 50,77] | 53,64 % | 40,38 % |
| **V1** | 5 868 | **−0,0756 %** | [−0,1199; −0,0313] | −0,0772 % | **−2,60** | 3 556 | **50,49 %** | [49,21; 51,77] | 53,42 % | 47,71 % |

**Odczyt kryterium: NEGATYWNY** (t_neff −2,60 przy n 5 868 ≥ 2 025). Regresja kontroli: ZGODNA.
**Parowo:** wspólnych 4 430 transakcji (tylko w kontroli 2 359, tylko w V1 1 438); ten sam
kierunek 74,3 %; różnica netto **+0,0182 % [−0,0372; +0,0735]**, mediana 0. Populacja świec
V1 11 424 vs kontrola 11 592 (−168, warm-up DVOL). Geometria: W̄ 1,286 %, L̄ 1,302 %, C 0,080 %.
Mierzalność: ex ante 6 870 (pre-rejestracja szacowała 6 580), ex post 5 938, journal 5 868;
half-width 1,28 pp — MIERZALNA; NEGATYWNY z zapasem 2,9×.

## Co na plus (+)

- Pierwsza cecha z rynku opcji w projekcie; niezależna od cech ceny (|r| ≤ 0,02); dopięcie
  z opóźnieniem 1 dnia i trzema testami lookaheadu; punktowo najlepsza z trzech serii.
- Kierunek efektu zgodny z mechanizmem (premia jako stan rynku), ale za słaby.

## Co na minus (−)

- Poprawa parowana +0,018 pp [−0,037; +0,074] — nie do odróżnienia od zera; większa część
  poprawy średniej wynika z WYŻSZEJ abstynencji (47,7 %), czyli mniejszej liczby transakcji,
  nie z lepszych decyzji na tych samych świecach.
- Horyzont DVOL (30 dni) wobec horyzontu modelu (12 h) — cecha to stan, nie prognoza ruchu.
- Jedna definicja; poziom DVOL, zmiana, skew, VRP jako TARGET — warianty po STOP.

## Walidacja (zasada 16a) — werdykt: **READY** (`../2026-09-23_l1-onchain-podaz/walidacja.txt`)

- Drugą drogą: p 50,49 % ✔, r̄ −0,0756 % ✔, p* = (1,3015 + 0,0804)/(1,2856 + 1,3015) = 53,42 % ✔;
  regresja kontroli ✔.
- Lookahead: opóźnienie 1 dnia vs 0 różni się w 11 526 z 12 042 świec (reszta = NaN/NaN);
  podmiana dni po 2026-06-30 → 0 zmian ✔.
- Kogo NIE ma: 498 świec przed 2021-03-25 (DVOL) — pierwszy fold OOS; 68 stłumionych,
  38 niewypełnionych; ETH DVOL; skew/term structure.
- Red flag „dodatni → przeciek": różnica parowana z zerem w CI; dopięcie sprawdzone.

## Przegląd diffu (zasada 16c) — werdykt: **Approve** (wspólny dla trzech serii — README L1)

## Wniosek

Premia za ryzyko zmienności z opcji **nie wystarcza modelowi 4h**: NEGATYWNY (−0,076 %
[−0,120; −0,031], 50,49 % [49,21; 51,77] vs 53,42 %), poprawa parowana +0,018 pp [−0,037; +0,074].
Razem z O1 to dwie cechy spoza wykresu, które przesuwają model punktowo w dobrą stronę — obie
o rząd wielkości za mało (wniosek 67). Seria V zamknięta 1/1.

## Rekomendacja

1. Nie mierzyć wariantów DVOL bez decyzji użytkownika (STOP).
2. Jeśli zmienność implikowana miałaby wrócić, to jako TARGET (sprzedaż/kupno zmienności —
   inny produkt, rynek opcji), nie jako cecha kierunkowa 4h — nowa pre-rejestracja z własnym
   rachunkiem mocy i danymi opcyjnymi (Deribit), poza obecnym zakresem.

## Użyte skille

Rejestr gałęzi wspólny dla L1/V1/G1 — tabela i pominięcia w README L1.
