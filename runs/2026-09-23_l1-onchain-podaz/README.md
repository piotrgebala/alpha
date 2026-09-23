# L1 — on-chain: zmiana podaży BTC na giełdach (7 dni) jako cecha modelu 4h (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Jedna z trzech serii (L1 / V1 / G1)
> pre-rejestrowanych W JEDNYM COMMICIE przed jakimkolwiek przebiegiem — kolejność uruchomień
> L1 → V1 → G1 nie wpływa na projekt żadnej z nich. Decyzja użytkownika 2026-09-23: „wykonaj
> po kolei 3 warianty celem zebrania informacji na przyszłość". **NOWA SERIA L, licznik 1/1.**
> Wzorzec O1 (kontrola vs kontrola + jedna cecha, parowo). Dane: P3 (CoinMetrics community).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Gdy posiadacze bitcoina przenoszą monety na giełdy, zwykle chcą je sprzedać — a sprzedaż idzie
z opóźnieniem po przelewie. Sprawdzamy, czy liczba bitcoinów trzymanych na giełdach (z danych
łańcucha, CoinMetrics) i jej zmiana w ostatnim tygodniu pomagają modelowi 4h trafiać lepiej.
Model dostaje jedną liczbę — o ile procent zmieniła się podaż na giełdach przez 7 dni — z dwoma
dniami opóźnienia (tyle konserwatywnie zakładamy na publikację danych). Porównanie parami z tym
samym modelem bez tej liczby. Oczekiwanie: jak O1 — informacja spoza wykresu może istnieć, ale
prior na próg 53,1 % trafności jest niski (F1 50,3 %, O1 50,3 %).

## ID testu

**L1** — nowa hipoteza, rodzina „on-chain jako cecha kierunkowa" (katalog: on-chain ·
jednoaktywowa · kierunek · 4h · NIETKNIĘTE → ZMIERZONE po L1). **Licznik 1/1, STOP.** Inne
metryki CoinMetrics (przepływy dzienne, MVRV, adresy aktywne, opłaty), inne okna (1/3/14/30 dni),
inne opóźnienia to warianty tej samej rodziny — po STOP decyzja użytkownika.

## Metadane

- Branch: `lvg-cechy-zewnetrzne` (od `master` @ `28b96a5`); wspólny dla L1/V1/G1 — rejestr
  skilli gałęzi obejmuje trzy serie (zapisane w „Użyte skille").
- Dane: świece 4h BTC (`fetch_window`, od 2021-01-01); `data/raw/external/coinmetrics_btc_1d.parquet`
  (P3: 2 822 dni, 0 braków w bazie), kolumna `SplyExNtv` (podaż BTC na adresach giełdowych wg
  heurystyk CoinMetrics; 2,56–3,18 mln BTC w bazie).
- Cecha: `ex_supply_change_7d = log(SplyExNtv_d / SplyExNtv_{d−7})` liczona na ramce dziennej,
  dopięta do świec o `open ≥ d + 2 dni 00:00 UTC` (opóźnienie publikacji, konserwatywnie);
  staleness > 7 dni → NaN. Profil dzienny (P3/sanity, bez patrzenia na zwroty): p05 −1,1 %,
  p50 −0,02 %, p95 +1,1 %; masa punktowa 0,15 %; acf1 0,88.
- Pipeline i ramiona jak O1: kontrola = `REVERSION_FEATURES`; L1 = kontrola + `ex_supply_change_7d`.
- Kod: `agents/external_features.py` (`load_daily`, `daily_log_change`, `attach_daily`,
  `compute_ex_supply_change_7d`, rejestr `EXTERNAL_FEATURE_FUNCTIONS`), sekcja `external:`
  w `agents/feature_registry.yaml`, testy przecieku (`agent_5_compliance/test_leakage.py`:
  rejestr + shift-forward), `tests/test_external_features.py` (dopięcie: dni późniejsze
  niewidoczne, opóźnienie, staleness). Skrypt `backtest/run_external_features_lvg.py L1`
  (komenda przy zamknięciu; na `runs/ZAMROZONE.txt`).

## Poprzedzające wyniki

- **P3**: CoinMetrics community 14 metryk 1d, 100 % bazy, 0 braków; brama G2: publikacja po
  zamknięciu dnia → `shift` (tu 2 dni).
- **O1** (wniosek 66): pierwsza cecha spoza OHLCV poruszająca model (+0,024 pp [−0,019; +0,067]),
  NEGATYWNA; wzorzec dopięcia i porównania parowanego; **F1**: funding 50,34 %; **wniosek 46**:
  kontrola p 49,58 %, −0,107 %, p* 53,07 %, abstynencja 40,4 %.
- **Katalog (families.md, on-chain):** mechanizm opóźnionej reakcji; pułapki: heurystyki adresów
  giełdowych i rewizje historyczne CoinMetrics (nieweryfikowalne; zapisane), publikacja z opóźnieniem.

## Pre-rejestracja

- **Hipoteza i mechanizm:** wzrost podaży na giełdach w ostatnim tygodniu = monety przygotowane do
  sprzedaży → presja podażowa w kolejnych dniach (opóźniona reakcja); spadek = akumulacja poza
  giełdami. Kto traci: sprzedający z opóźnieniem po przelewie.
- **DOKŁADNIE JEDNA zmienna:** dodanie `ex_supply_change_7d` (5 cech zamiast 4). Alternatywy
  odrzucone przed danymi: przepływ dzienny netto (szum dnia), MVRV (wycena, nie przepływ),
  inne okna.
- **Przyrząd i kryterium (jedno ramię, m = 1):** jak O1 — POZYTYWNY `t_neff > 1,96` ORAZ
  `ci_low(p) > p*`; NEGATYWNY `t_neff < −1,96` przy `n ≥ required`; inaczej NIEROZSTRZYGNIĘTY.
  Porównanie parowane L1 − kontrola: obserwacja (skala O1: +0,024 pp; A1b: −0,001 pp).
- **Mierzalność (zasada 18):** `expected_trades(11 592; 0,4038; 0,994) ≈ 6 870`, half-width
  1,18 pp, `measurability_report(0,56; 0,5307; 6 870)` → **MIERZALNA** (jak O1; cecha bez NaN
  w bazie poza pierwszymi 9 dniami warm-up 7 + 2, przed pierwszym foldem OOS).
- **Kontekst multiple testing:** trzy serie tego samego dnia z tym samym przyrządem + ~17
  wcześniejszych odczytów; każda seria ma własny licznik, a czytelnik musi liczyć wszystkie.
- **Czego runda NIE robi:** nie stroi okna, nie dodaje drugiej metryki, nie liczy SHAP jako
  dowodu, nie odwraca znaku, nie wybiera podokresów.

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
