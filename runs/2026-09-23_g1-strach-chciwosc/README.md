# G1 — indeks strachu i chciwości (Fear & Greed) jako cecha modelu 4h (2026-09-23)

> **STATUS: ZAMKNIĘTA — NEGATYWNY** (zwrot netto −0,102 % [−0,144; −0,059] na transakcję,
> t_neff −3,48; trafność 49,90 % [48,66; 51,13] wobec progu 53,86 %). Wobec kontroli
> **+0,002 pp [−0,045; +0,049]** — nic; kierunek zmieniony w 22,4 % wspólnych transakcji,
> abstynencja 45,1 % (kontrola 40,4 %). Indeks jest częściowo przebraniem cech kontroli
> (korelacja z `rsi_14` +0,29, z `price_zscore_20` +0,14), jak zapisano z góry. Jedna z trzech
> serii pre-rejestrowanych w jednym commicie (`3278442`). **Seria G: 1/1, STOP.** Walidacja
> (16a): **READY**; przegląd diffu (16c): **Approve** (wspólny, w README L1).

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Indeks strachu i chciwości nie pomaga modelowi 4h:** trafność 49,9 % (bez cechy 49,6 %),
strata −0,102 % na transakcję (bez cechy −0,107 %), różnica parami +0,002 punktu — zero.
Indeks w jednej trzeciej powtarza to, co model już wie z ceny i wolumenu (jego korelacja
z RSI to 0,29), a reszta nie niesie informacji o ruchu w najbliższych 12 godzinach. Próg
opłacalności 53,9 % jest daleko poza przedziałem. **Wynik negatywny.**

---

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

## Wynik

Komenda: `py -m backtest.run_external_features_lvg G1` (`PYTHONUTF8=1`; 6 s; `raw_output.txt`).
Cecha: NaN 0 / 12 042; rozkład p05 0,12, p50 0,49, p95 0,79; masa punktowa 3,24 % (wartość 50);
acf1 0,994. Korelacja z kontrolą: `rsi_14` **+0,289**, `price_zscore_20` +0,142, reszta ≈ 0 —
częściowa redundancja (zapisana w pre-rejestracji jako oczekiwana pułapka).

| ramię | n | r̄ netto | CI 95 % | mediana | t_neff | N_eff | p | CI 95 % (p) | p* | abstynencja |
|---|---|---|---|---|---|---|---|---|---|---|
| kontrola | 6 789 | −0,1069 % | [−0,1487; −0,0650] | −0,1036 % | −4,26 | 4 919 | 49,58 % | [48,39; 50,77] | 53,64 % | 40,38 % |
| **G1** | 6 277 | **−0,1017 %** | [−0,1443; −0,0591] | −0,0967 % | **−3,48** | 3 482 | **49,90 %** | [48,66; 51,13] | 53,86 % | 45,06 % |

**Odczyt kryterium: NEGATYWNY** (t_neff −3,48 przy n 6 277 ≥ 1 902). Regresja kontroli: ZGODNA.
**Parowo:** wspólnych 4 956 transakcji (tylko w kontroli 1 833, tylko w G1 1 321); ten sam
kierunek 77,6 %; różnica netto **+0,0022 % [−0,0449; +0,0493]**, mediana 0. Populacja świec
identyczna. Geometria: W̄ 1,266 %, L̄ 1,299 %, C 0,082 %. Mierzalność: ex ante 6 870, ex post
6 331, journal 6 277; half-width 1,24 pp — MIERZALNA; NEGATYWNY z zapasem 3,3×.

## Co na plus (+)

- Pełna baza (0 NaN), dopięcie z opóźnieniem 4h i trzema testami lookaheadu; poziom bez progów
  (masa punktowa 3,2 % nie przeszkadza modelowi drzew).
- Redundancja z kontrolą zmierzona i zgodna z zapowiedzią — wynik nie zaskakuje.

## Co na minus (−)

- Różnica parowana ≈ 0; wzrost abstynencji (+4,7 pp) jak w L1/V1 — dodatkowa cecha o skali dni
  czyni model 4h mniej pewnym, nie lepszym.
- Indeks złożony (składniki niedostępne osobno), acf1 0,994 — wartość praktycznie stała przez
  dzień; nie ma czego przewidywać na 12 h.

## Walidacja (zasada 16a) — werdykt: **READY** (`../2026-09-23_l1-onchain-podaz/walidacja.txt`)

- Drugą drogą: p 49,90 % ✔, r̄ −0,1017 % ✔, p* = (1,2991 + 0,0823)/(1,2656 + 1,2991) = 53,86 % ✔;
  regresja kontroli ✔.
- Lookahead: opóźnienie 4h vs 0 różni się w 1 766 świec (pierwsza świeca każdego dnia — jak
  powinno); podmiana dni po 2026-06-30 → 0 zmian ✔.
- Kogo NIE ma: 2 luki źródła (≤ 3 dni, w tolerancji); 63 stłumionych, 29 niewypełnionych.

## Przegląd diffu (zasada 16c) — werdykt: **Approve** (wspólny dla trzech serii — README L1)

## Wniosek

Fear & Greed jako cecha 4h: **NEGATYWNY**, różnica parowana +0,002 pp [−0,045; +0,049], częściowo
redundantny z RSI (0,29). Trzecia z trzech dziennych cech zewnętrznych bez informacji
kierunkowej na 12 h (wniosek 67). Seria G zamknięta 1/1.

## Rekomendacja

1. Nie mierzyć wariantów (zmiany indeksu, progi skrajności) bez decyzji użytkownika (STOP).
2. Sentyment dzienny nie pasuje do horyzontu 12 h; ewentualny powrót tylko na horyzoncie
   dziennym/tygodniowym jako nowa baza.

## Użyte skille

Rejestr gałęzi wspólny dla L1/V1/G1 — tabela i pominięcia w README L1.
