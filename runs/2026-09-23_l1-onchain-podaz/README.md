# L1 — on-chain: zmiana podaży BTC na giełdach (7 dni) jako cecha modelu 4h (2026-09-23)

> **STATUS: ZAMKNIĘTA — NEGATYWNY** (zwrot netto −0,097 % [−0,140; −0,054] na transakcję,
> t_neff −4,23; trafność 49,79 % [48,56; 51,02] wobec progu 53,51 %). Wobec kontroli na tych
> samych świecach **+0,003 pp [−0,047; +0,052]** — nic; cecha zmienia kierunek w 26,8 %
> wspólnych transakcji i podnosi abstynencję z 40,4 % do 44,3 % (model mniej pewny, nie lepszy).
> Jedna z trzech serii (L1 / V1 / G1) pre-rejestrowanych w jednym commicie (`3278442`) przed
> jakimkolwiek przebiegiem. **Seria L: 1/1, STOP.** Walidacja (16a): **READY**; przegląd diffu
> (16c): **Approve** (wspólny dla trzech serii, sekcja niżej). Decyzja użytkownika 2026-09-23:
> „wykonaj po kolei 3 warianty celem zebrania informacji na przyszłość".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Wiedza o tym, ile bitcoinów przypłynęło na giełdy w ostatnim tygodniu, nie pomaga modelowi 4h.**
Trafność 49,8 % (bez cechy 49,6 %), strata na transakcję −0,097 % (bez cechy −0,107 %), a różnica
parami między modelem z cechą i bez niej to +0,003 punktu procentowego — dokładnie zero. Jedyne,
co cecha zmienia: model częściej odmawia decyzji (44 % zamiast 40 % świec). Próg opłacalności
(53,5 % trafności) jest poza zasięgiem przedziału. **Wynik negatywny; informacja z łańcucha
o podaży na giełdach — w tej definicji i na tym horyzoncie — nie niesie sygnału kierunkowego.**

---

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

## Wynik

Komenda: `py -m backtest.run_external_features_lvg L1` (`PYTHONUTF8=1`; 6 s; `raw_output.txt`).
Cecha: NaN 0 / 12 042 świec; rozkład p05 −1,13 %, p50 −0,02 %, p95 +1,10 %; masa punktowa 0,15 %;
acf1 0,98 (wartość dzienna powtarzana na 6 świec). Korelacja z kontrolą: `return_lag_1` −0,03,
`volume_zscore_20` 0,00, `rsi_14` −0,08, `price_zscore_20` −0,06 — informacja niezależna.

| ramię | n | r̄ netto | CI 95 % | mediana | t_neff | N_eff | p | CI 95 % (p) | p* | abstynencja |
|---|---|---|---|---|---|---|---|---|---|---|
| kontrola | 6 789 | −0,1069 % | [−0,1487; −0,0650] | −0,1036 % | −4,26 | 4 919 | 49,58 % | [48,39; 50,77] | 53,64 % | 40,38 % |
| **L1** | 6 343 | **−0,0973 %** | [−0,1401; −0,0544] | −0,0975 % | **−4,23** | 5 730 | **49,79 %** | [48,56; 51,02] | 53,51 % | 44,25 % |

**Odczyt kryterium: NEGATYWNY** (t_neff −4,23 przy n 6 343 ≥ 1 977). Regresja kontroli: ZGODNA.
**Parowo:** wspólnych 4 805 transakcji (tylko w kontroli 1 984, tylko w L1 1 538); ten sam kierunek
73,2 %; różnica netto **+0,0026 % [−0,0470; +0,0522]**, mediana 0. Populacja świec identyczna
(11 592). Geometria: W̄ 1,297 %, L̄ 1,316 %, C 0,082 %. Mierzalność: ex ante 6 870, ex post 6 424,
journal 6 343; half-width 1,23 pp — MIERZALNA, rozstrzygnięte z zapasem 3,2×.

## Co na plus (+)

- Pierwsza cecha on-chain w projekcie; dopięcie z jawnym opóźnieniem publikacji (2 dni) i trzema
  testami lookaheadu; kontrola odtworzona co do sztuki; populacja świec = kontrola.
- Cecha niezależna od ceny/wolumenu (korelacje |r| ≤ 0,08) — wynik mówi o INFORMACJI, nie
  o redundancji.

## Co na minus (−)

- Różnica parowana ≈ 0 z CI ±0,05 pp; efekt cechy = wyższa abstynencja (+3,9 pp), nie lepsze
  decyzje. Jedna metryka z 14 CoinMetrics, jedno okno — po STOP kolejne to decyzja użytkownika.
- Heurystyki adresów giełdowych CoinMetrics i możliwe rewizje historyczne — nieweryfikowalne.
- Horyzont: cecha zmienia się w skali dni (acf1 0,98), model decyduje o 12 h — niedopasowanie
  skal zapisane z góry; wynik go potwierdza, nie rozstrzyga, czy inny horyzont by pomógł.

## Walidacja (zasada 16a) — werdykt: **READY** (`walidacja.txt`, wspólna dla L1/V1/G1)

- Drugą drogą (numpy z journalu): p 49,79 % ✔, r̄ −0,0973 % ✔, p* = (1,3155 + 0,0822)/(1,2965 +
  1,3155) = 53,51 % ✔. Regresja kontroli ✔.
- Lookahead: dopięcie z opóźnieniem 2 dni vs bez opóźnienia różni się we WSZYSTKICH 12 042
  świecach (wersja użyta czeka); podmiana wartości dni po 2026-06-30 zmienia 0 świec ✔.
- Kogo NIE ma: 0 świec z NaN cechy; 81 stłumionych, 39 niewypełnionych; pozostałe metryki
  CoinMetrics; inne okna. Red flag „idealnie potwierdza": nie (negatywny, jak oczekiwano).

## Przegląd diffu (zasada 16c) — werdykt: **Approve** (wspólny dla L1/V1/G1)

Zakres gałęzi: `agents/external_features.py` (nowy), sekcja `external:` rejestru,
`agent_5_compliance/test_leakage.py` (+2 testy), `tests/test_external_features.py` (5),
`backtest/run_external_features_lvg.py` (reporter z argumentem serii), trzy README.
**Korektność:** `attach_daily` — `merge_asof(direction="backward", tolerance=7 dni)` na kluczu
`open − available_after` daje największy dzień `d` z `d + lag ≤ open` (test: wartość dnia widoczna
dopiero od `d + lag`; dni późniejsze niewidoczne; staleness → NaN); jednostki czasu ujednolicone
do ns (parquet 4h ma µs — pierwsza wersja rzuciła `MergeError`, poprawiona przed przebiegiem);
kolejność wierszy przywrócona przez `_order`; `daily_log_change` na ramce dziennej (NaN warm-up);
`compute_realized_vol_30d` — `rolling(180).std(ddof=1) × sqrt(2 190)`, trailing; `compute_vrp_30d`
= DVOL/100 − rv; `compute_fng_level` = /100; rejestr 1:1 z kodem (test). Skrypt — kopia wzorca
O1 z argumentem serii, bez decyzji. **Edge-case'y:** brak kolumn → `ValueError`; NaN cechy → wiersz
odpada w silniku (V1: 498 świec, fold 1 pominięty). **Usterki naprawione przed przebiegiem:**
`MergeError` jednostek czasu; B007 w teście. **Werdykt jednym zdaniem:** kod poprawny,
dopięcie z opóźnieniem publikacji przetestowane trzema drogami — **Approve**.

## Wniosek

Zmiana podaży BTC na giełdach z ostatnich 7 dni **nie niesie informacji kierunkowej dla modelu
4h**: NEGATYWNY z zapasem, różnica parowana +0,003 pp [−0,047; +0,052], jedyny efekt to wyższa
abstynencja. Razem z V1 i G1 (ten sam dzień, ten sam przyrząd): trzy dzienne źródła spoza
wykresu, trzy wyniki negatywne (wniosek 67). Seria L zamknięta 1/1.

## Rekomendacja

1. Nie mierzyć kolejnych metryk CoinMetrics jako cech 4h bez decyzji użytkownika (STOP); jeśli
   decyzja: jedna na rundę, ale z niższym priorem niż O1 (on-chain = skala dni).
2. Jeśli on-chain miałoby wrócić, to na horyzoncie dziennym/tygodniowym (inna baza, nowy rachunek
   mocy) — nie jako cecha 4h.

## Użyte skille

Rejestr gałęzi `lvg-cechy-zewnetrzne` (wspólny dla L1/V1/G1; `py tools/skill_audit.py raport
--galaz lvg-cechy-zewnetrzne`): `anthropic-skills:clas5-runda` (procedura trzech serii z jedną
pre-rejestracją), `anthropic-skills:clas5-quant` (jedna cecha per seria po mechanizmie, moc
z abstynencji, N_eff, kontekst ~20 odczytów), `anthropic-skills:quant-strategy-catalog` (pięć pól
rodzin on-chain/vol/sentyment, pułapki: rewizje, horyzont DVOL, redundancja F&G),
`engineering:testing-strategy` (plan testów PRZED kodem: opóźnienie, staleness, dni późniejsze),
`data:validate-data` (16a: numpy z journalu, trzy drogi lookaheadu), `data:statistical-analysis`
(16b: trzy serie w jednej tabeli bez wyboru, CI, mediany, kontekst 0,15 fałszywego pozytywu),
`engineering:code-review` (16c). Pominięte: `security-review` (bez sieci), `dataviz`,
`engineering:architecture`, `update-config`, `ta-toolkit`, `lean-research`, `data:explore-data`
(profil źródeł w P3).
