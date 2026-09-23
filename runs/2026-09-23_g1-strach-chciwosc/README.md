# G1 — indeks strachu i chciwości (Fear & Greed) jako cecha modelu 4h (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Jedna z trzech serii (L1 / V1 / G1)
> pre-rejestrowanych W JEDNYM COMMICIE przed jakimkolwiek przebiegiem. Decyzja użytkownika
> 2026-09-23: „wykonaj po kolei 3 warianty celem zebrania informacji na przyszłość".
> **NOWA SERIA G, licznik 1/1.** Wzorzec O1. Dane: P3 (alternative.me).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Indeks strachu i chciwości (0 = skrajny strach, 100 = skrajna chciwość) składa się z kilku
składników: zmienności, wolumenu, mediów społecznościowych, dominacji bitcoina, trendów
wyszukiwania. Podręcznik mówi: „kupuj, gdy inni się boją". Model dostaje poziom indeksu
(z opóźnieniem 4 h od publikacji) i sprawdzamy, czy trafia lepiej. Uwaga zapisana z góry:
część indeksu to zmienność i wolumen, które model już widzi — korelacja z cechami kontroli
będzie raportowana; jeśli jest wysoka, „nowa informacja" jest w dużej mierze stara.

## ID testu

**G1** — nowa hipoteza, rodzina „sentyment/zdarzenia jako cecha kierunkowa" (katalog:
zdarzenia/sentyment · jednoaktywowa · kierunek · 4h · NIETKNIĘTE → ZMIERZONE po G1).
**Licznik 1/1, STOP.** Zmiany indeksu, progi „skrajny strach/chciwość", inne indeksy
sentymentu to warianty tej samej rodziny — po STOP decyzja użytkownika.

## Metadane

- Branch: `lvg-cechy-zewnetrzne` (od `master` @ `28b96a5`); wspólny dla L1/V1/G1.
- Dane: świece 4h BTC (od 2021-01-01); `data/raw/external/alternative_fng_1d.parquet` (P3:
  od 2018-02-01, 99,95 % bazy, 2 luki po 1–3 dni), kolumna `value` (0–100).
- Cecha: `fng_level = value/100`, wartość dnia `d` dopięta do świec o `open ≥ d + 4h` (indeks
  publikowany ok. 00:00 UTC dnia `d`); staleness > 7 dni → NaN. Profil dzienny (P3/sanity):
  średnia 46,9, masa punktowa 3,2 % (wartość 50), acf1 0,96 — poziom, bez progów percentylowych.
- Pipeline i ramiona jak O1: kontrola = `REVERSION_FEATURES`; G1 = kontrola + `fng_level`.
- Kod: `agents/external_features.py` (`compute_fng_level`), rejestr `external:`, testy przecieku
  i jednostkowe (jak L1). Skrypt `backtest/run_external_features_lvg.py G1`.

## Poprzedzające wyniki

- **P3**: F&G od 2018-02-01, 2 006 / 2 007 dni bazy, masa punktowa 2,5 % (50).
- **O1** (wniosek 66), **F1**, **wniosek 46** — jak w L1. **Wniosek 15** (masa punktowa → bez
  progów percentylowych): cecha jako surowy poziom.
- **Katalog (families.md, sentyment):** mechanizm błędu behawioralnego (tłum w skrajności);
  pułapka: indeks złożony częściowo z ceny/wolumenu → redundancja z cechami kontroli
  (korelacja raportowana w skrypcie: `volume_zscore_20`, `rsi_14`, `price_zscore_20`).

## Pre-rejestracja

- **Hipoteza i mechanizm:** skrajny strach = wyprzedanie (kontrariańsko byczo), skrajna
  chciwość = wykupienie (niedźwiedzio); kto traci: tłum działający w skrajnościach.
  Kierunek uczy model z poziomu (nieliniowość: skrajności, nie środek).
- **DOKŁADNIE JEDNA zmienna:** dodanie `fng_level`. Alternatywy odrzucone przed danymi:
  zmiana indeksu (szum dnia), progi skrajności (stopnie swobody), składniki osobno (niedostępne).
- **Przyrząd i kryterium (jedno ramię, m = 1):** jak O1/L1.
- **Mierzalność (zasada 18):** `expected_trades(11 592; 0,4038; 0,994) ≈ 6 870`, half-width
  1,18 pp → **MIERZALNA** (jak O1; 2 luki po ≤ 3 dni mieszczą się w tolerancji staleness).
- **Kontekst multiple testing** i **czego runda NIE robi:** jak L1; dodatkowo: wysoka korelacja
  z cechami kontroli NIE jest powodem do zmiany definicji po fakcie — jest zapisywana jako wynik.

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
