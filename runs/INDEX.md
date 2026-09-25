# runs/ — spis treści

## Stan wiedzy — skrót (czytaj najpierw; stan na 2026-09-25)

Krótka mapa dla kogoś, kto wchodzi do projektu. Pełne liczby i uzasadnienia: tabela niżej
i „Wnioski skumulowane” (numery w nawiasach). Aktualizuj, gdy runda zmienia obraz — nie przy
każdej rundzie; limit ~40 linii (dłuższe = przenieś do wniosków).

**Zamknięte — nie wracać bez NOWEJ informacji:**
- Przewidywanie kierunku BTC z cech wykresu na świecach 5m / 1h / 4h: trafność ~50 % na dużych
  próbach — dowód braku (Faza 0, M1, Y1, WF1; wnioski 12, 39, 69, 85). 1d (Y2) niezmierzony.
- Klasyczna analiza techniczna na BTC 4h — 7 rodzin (48–53). Wykonanie i zarządzanie pozycją nie
  tworzą przewagi (42–45).
- Dane spoza wykresu (funding, OI, L/S, przewaga kupujących, VRP, podaż na giełdach, F&G) na BTC 4h — zmierzone
  (SW, 90): jako reguły i jako model 365 dni tracą po kosztach; duża przewaga wykluczona; ślad przed kosztami
  +0,02 … +0,05 %/tr, mniejszy niż koszt 0,08 %.
- Carry przekrojowy (niemierzalny), przełączanie carry po znaku, premia rebalansowa, short nowych
  listingów (40, 55, 57, 71). Carry z hedgem działa (COIN-M ~+9 %/rok, 61), ale to nie cel
  użytkownika (zwroty rzędu zakładu o kierunek).
- Skalowanie pozycji siłą sygnału — niemierzalne na 5 latach (78).

**Kandydaci — ślady, nie dowody (każdy wybrany spośród ~30 odczytów na tej samej historii):**
- Premia Coinbase → BTC na tydzień (CP1): jedyny POZYTYWNY, ~+32 %/rok, t 2,09; po korekcie na ~28 prób DSR 0,52
  (AU4, 96) — tyle co najlepszy z pustych; poza próbą (lip–wrz 2026) bez potwierdzenia (72). Na ETH/SOL niesprawdzalna — ten sam sygnał (CP2, 80).
- Trend tygodniowy na koszyku top-20 (TS1): po korekcie danych ~+11 %/rok [−4; +26], nadal
  nieistotny (70, 74, 82). Momentum przekrojowe top-20 (X1): jako średnia 7 dni startu tygodnia
  +9,5 %/rok, t 0,61 — dawne +42 % to najlepszy z 7 dni (89); tylko dziennik papierowy od 2026-09-25.
  Trend na miejscach 21–50 (TR1) od 2021-02: +15,5 %/rok, t 1,99 — formalnie ponad 1,96, ale znany z góry
  i niesiony przez hossę 02–04.2021; od 2022 t 1,32 (88).

**Ryzyko i wielkość pozycji (opisowo, na historii):**
- Dźwignia 3× na altach kosztuje trend ~3,6 pkt/rok w likwidacjach, 2× ~1,6 pkt (76).
- Trend + premia Coinbase razem (po RU1): ~+17 %/rok, największy spadek ~18 %, depozyt ~23 %
  kapitału; hamulec „pół pozycji po −15 %” szkodzi (77, 82). Dziennik na żywo od 2026-09-24.
- Portfel pod realne pieniądze (PR1, 101): wagi z korelacjami = obecne 1/σ przy 2 nogach; przy depozycie 5 % kapitału
  (limit trzymany każdego dnia) zły tydzień ≈ −1 %, najgorsza seria ≈ −2 % całego kapitału; X1 jako 3. noga pogarsza (obsunięcie 28 %).

**Przyrząd — dlaczego ufamy liczbom:**
- „Nierozstrzygnięty” = za mało lat: przy prawdziwym +10 %/rok test na 5,4 roku wykrywa go w ~25 %
  przypadków, przy +20 % w ~73 % (AU1, 87). Obliczenia sprawdzone niezależnie (AU1).
- Kontrola pozytywna K1 (przyrząd widzi znany sygnał) i negatywna NC1 (silniki TS1 / X1 / CP1
  nie wymyślają zysku z szumu o grubych ogonach) (79).
- Werdykt ma dwa warunki: zwrot netto t_neff > 1,96 i — przy regułach z trafnością — dolny
  kraniec trafności nad progiem (43); N_eff ≤ n (50); rachunek mocy przed rundą (zasada 18).
- Większość serii zamknięta regułą STOP: kolejne odczyty na tej samej historii tylko zwiększają
  szansę przypadkowego sukcesu. Rozstrzygnąć może test prospektywny (dziennik na żywo).

**Uwaga danych (RU1):** `data/raw/universe` jest obcięty (287/685) — nowe rundy tylko na `universe_full`;
RU2 przeliczyła TR1, X2, LQ1, TF1, R1 (werdykty bez zmian, 83), RU3 poprawiła start TR1/X2 na 2021-02 (88);
TL1 przeliczony w RU4 (97); NL1 i P2 nie dotyczy.

**Kryterium od 2026-09-24 (ADR-09):** o kapitale decyduje drabina dowodów (`docs/rag/09`); ten plik nadal
księguje każdy odczyt. Trend: szczebel 2 spełniony (post hoc); szczebel 1(b) TX1 NIEROZSTRZYGNIĘTY — działa 1990–2012, zanika po 2013 (84).

**Otwarte:** dziennik prospektywny trend + Coinbase (jedyna droga do rozstrzygnięcia CP1). Likwidacje zbierane od
2026-09-25 (LK0, 102) — odczyt E1 po ≥ 1 roku. Nowe źródła
popytu: premia koreańska NIEMIERZALNA (KP1, 91; sygnał inny niż CP1, ale efekt z badań ~SR 0,15 wobec
progu 0,86); stablecoiny i ETF — NIEMIERZALNE w SH1 (81). Kolejne sygnały kierunkowe na samym BTC
wymagają priorytetu SR ≥ ~0,9 z badań po publikacji — inaczej nie startują (filtr przed pobraniem danych).
Przekrój top-50 (long/short) widzi już IC ≈ 0,022 (AU2, 92), ale ML z przeszukiwaniem traci ~2/3 mocy — ML przekrojowe nie startuje (93).
**Błąd N_eff (93) naprawiony w AU3 (94):** audyt 59 przebiegów — żaden dawny werdykt się nie zmienia.

## Konwencja katalogów

Katalog na surowy output ciężkich obliczeń (kalibracje, sweepy, testy odporności na realnych
danych). **Konwencja od 2026-09-22 (CLAUDE.md zasada 11): każdy run ma WŁASNY KATALOG**
`runs/YYYY-MM-DD_<id>-<slug>/` zawierający:

- `README.md` — pełny write-up: **ID testu**, **Metadane** (branch/komenda/parametry/dane),
  **Poprzedzające wyniki** (które wcześniejsze runy motywują/ograniczają projekt tej rundy —
  obowiązkowe dla nowych rund, CLAUDE.md zasada 14), **Wynik**, **Co na plus (+) / Co na minus
  (-)**, **Wniosek**, **Rekomendacja**, **Użyte skille** (od 2026-09-23, CLAUDE.md zasada 19 —
  tabela z `py tools/skill_audit.py raport --galaz <gałąź rundy>`);
- `raw_output.txt` — pełny, nieskrócony stdout przebiegu (obowiązkowy dla nowych rund;
  historyczne runy mają output w README, C2.7–C2.9 uzupełnione wstecznie);
- ewentualne artefakty (CSV, wykresy).

Ten plik jest aktualizowany przy każdym nowym katalogu — nie duplikuje treści, tylko wskazuje
na nią. Kolumna **Warianty** to jawna księga budżetu multiple-testing: ile WARIANTÓW HIPOTEZY
porównano z wynikiem na tych samych danych w danej rundzie ("0 (diagnostyka)" = runda opisowa/
metodologiczna/naprawcza). **Liczniki rozwidlają się per baza danych i per hipoteza** — patrz
podsumowanie pod tabelą.

| ID | Data | Katalog | Krótki opis | Warianty | Wynik |
|---|---|---|---|---|---|
| C2.5 | 2026-09-21 | [c2.5-threshold-calibration](2026-09-21_c2.5-threshold-calibration/README.md) | Kalibracja progów reguły regime (`trend_threshold`/`range_threshold`) — 4 kandydaci wybrani ze struktury dyskretnego wsparcia `direction_persistence_10`, pełny walk-forward + 10-seed sweep | 4 | **NO-GO** (wszyscy 4 kandydaci) — hipoteza "zła kalibracja progów" falsyfikowana; baseline (0.7/0.3) zostaje bez zmian |
| C2.6 | 2026-09-21 | [c2.6-timeframe-robustness](2026-09-21_c2.6-timeframe-robustness/README.md) | Test odporności hipotezy na timeframe danych (5m referencja vs 1h vs 4h, agregowane z 5m) — czy szersza bariera ATR-vs-koszt na grubszych świecach przywraca edge | 2 | **NO-GO** (1h i 4h) — mechanizm bariera-vs-koszt naprawiony (0% świec arytmetycznie niewykonalnych), ale edge kierunkowy nadal nieobecny (~49% trafności) albo ujemny (~41% na 4h). **Uwaga (Z9):** resample z 5m psuł WOLUMEN (11% świec 1h), a `volume_zscore_20` jest cechą obu modeli |
| C2.7 | 2026-09-21 | [c2.7-feature-candidate-screening](2026-09-21_c2.7-feature-candidate-screening/README.md) | Przegląd 8 kandydatek nowych cech (4 rodziny) PRZED testem OOS: macierz korelacji Spearman cecha-cecha (redundancja) + korelacja cecha-target per regime (opisowa/eksploracyjna) | 0 (screening opisowy; 34 korelacje obejrzane bez selekcji) | **Redundancja:** `bb_pctb_20` odrzucony (corr=1,000 z `price_zscore_20`); `adx_14` jedyny kandydat nisko skorelowany z resztą registry. **Target:** brak sygnału w żadnej z 17 cech (\|corr\|<0,065) |
| C2.8 | 2026-09-21 | [c2.8-adx14-oos-evaluation](2026-09-21_c2.8-adx14-oos-evaluation/README.md) | Formalny test OOS: `adx_14` dodane do `MOMENTUM_FEATURES` (Test 1/trend) — pełny walk-forward, baseline vs kandydat | 1 | **NO-GO (oba warianty)** — `trend` NO-GO→WARUNKOWY (-8,46→-7,11), ale efekt = 1 fold ledwo nad zerem; po C2.9: poprawa +0,61 to ~0,2σ szumu fold-jitter — nierozstrzygalna. `adx_14` zostaje w registry, NIE w modelu |
| C2.9 | 2026-09-21 | [c2.9-measurement-methodology](2026-09-21_c2.9-measurement-methodology/README.md) | Naprawa metodologii pomiaru (Z1–Z4+Z13): fold-jitter zamiast pustego sweepu seedów (XGBoost deterministyczny), per-fold t-stat, pooled Sharpe per regime, N_eff | 0 (diagnostyka/metodologia) | **NO-GO odporne na fold-jitter: 10/10 offsetów ujemne** (zakres [-15,9; -6,2], σ≈3,1). Pooled: zwrot per trade **istotnie ujemny w OBU reżimach** (range t=-7,15; trend t=-2,91/-2,63 po N_eff) |
| C2.10 | 2026-09-21 | [c2.10-extended-history-z5](2026-09-21_c2.10-extended-history-z5/README.md) | Backlog Z5: historia wydłużona do 3 lat (2023-07→2026-07, 315 648 świec 5m, zero dziur, overlap ze starym oknem identyczny co do bajtu) — NOWA BAZA checkpointu v2; pipeline niezmieniony | 0 (nowa baza danych) | **NO-GO, 21/144 ważnych foldów** (14,6% — jak na roku: strukturalnie). Pooled t: **range -10,47 / trend -5,51** (N_eff: -7,34 / -4,04). Odkrycie: bramka kosztowa blokuje **98% sygnałów `range`**, `trend`=0,53% świec — dłuższa historia tego nie naprawia (→ Z7/Z6/Z10) |
| C2.11 | 2026-09-21 | [c2.11-edge-instrumentation](2026-09-21_c2.11-edge-instrumentation/README.md) | Instrumentacja edge'u (Runda 1/4 „droga do GO"): rozbicie werdyktu na człony **(2p−1)·B > C** — `compute_hit_rate` (z-stat, CI), `break_even_hit_rate`, `summarize_edge_by_regime` w kanonicznym raporcie | 0 (instrumentacja pomiaru) | **Werdykt bit-identyczny z C2.10** (regresja baseline'u). Trafność **51,9% / 50,6%** (z=+0,87 / +0,25) vs wymagane **75,8% / 64,9%** → luka **−23,9 pp / −14,2 pp**: NO-GO przesądzone **geometrią wypłaty**, nie kierunkiem sygnału |
| C2.12 | 2026-09-21 | [c2.12-execution-cost-model](2026-09-21_c2.12-execution-cost-model/README.md) | Backlog Z6 (Runda 2/4): realistyczny model wykonania — maker na wejściu/TP, taker na SL/timeout, slippage tylko na nogach taker; `exit_reason` w journalu; `execution_model` | 1 | **NO-GO (nadal), ale ~połowa luki domknięta:** koszt **−52%**, foldy 21→54, transakcje `range` 530→7 155, margines **−23,9→−15,5 pp / −14,2→−9,1 pp**. **Ostrzeżenie pomiarowe:** per-fold `mean_sharpe` rozjechał się (σ 3,1→75,7) — nośne są pooled t i margin |
| C2.13 | 2026-09-21 | [c2.13-confidence-threshold](2026-09-21_c2.13-confidence-threshold/README.md) | Runda 3/4: pre-rejestrowany próg pewności `q=0,75` liczony na foldzie treningowym, stosowany OOS — baseline vs kandydat | 1 | **HIPOTEZA SFALSYFIKOWANA — reguła STOP uruchomiona.** `trend` trafność 49,9%→45,5% (kierunek PRZECIWNY do przewidywanego), kryterium `z_margin>2` niespełnione nigdzie. Monotoniczny „skill" sprzed programu = artefakt selekcji post hoc. **Runda 4 (Z7) NIE uruchomiona** |
| Z16 | 2026-09-22 | [z16-regime-coherence](2026-09-22_z16-regime-coherence/README.md) | Pomiar SPÓJNOŚCI bramki reżimu z horyzontem etykiety — `agents/regime_coherence.py` + przesiew 6 kandydatów na regułę reżimu, bez uruchamiania modelu | 0 (pomiar specyfikacji) | **Hipoteza wyjaśniająca POTWIERDZONA:** w `trend` tylko **0,49%** świec ma etykietę wewnątrz własnego reżimu (mediana epizodu 2 świece vs horyzont 12). **Z8 domknięty za 0 wariantów** (wymagane B=4,21% ceny → horyzont ~39 dni vs epizody 5h). **Asymetria:** `range` daje się uspójnić, `trend` NIE |
| Z17+Z21 | 2026-09-22 | [z17-z21-early-stopping-leak](2026-09-22_z17-z21-early-stopping-leak/README.md) | Naprawa przecieku early stopping (liczba drzew dobierana na OOS) + embargo na granicy train/test; adopcja zadeklarowana bezwarunkowo PRZED uruchomieniem | 0 (naprawa błędu) | **`p` było ZAWYŻONE przez przeciek:** `range` 51,07%→**50,38%**, z_stat +1,81→+0,63 — jedyny „bliski istotności" wynik projektu (C2.12) był artefaktem. **Najczystszy pomiar `p` — brak edge'u kierunkowego w obu reżimach** |
| Z18 | 2026-09-22 | [z18-unify-hit-rate](2026-09-22_z18-unify-hit-rate/README.md) | Kanoniczna definicja `p` = `gross_pnl>0` + rozbicie trafności per typ wyjścia (`share_timeout`, `hit_rate_barrier/timeout`) | 0 (ujednolicenie definicji) | Rozjazd definicji zmierzony (naiwna zaniżała o +5,6/+8,0 pp). **Zamknięta hipoteza ucieczkowa:** trafność na samych barierach = 50,50%/50,20% — edge nie chowa się w żadnej składowej |
| Z9 | 2026-09-22 | [z9-timeframe-geometry](2026-09-22_z9-timeframe-geometry/README.md) | Natywne świece 1h/4h z Binance do trwałego cache + walidacja resample vs natywne + relacja B/C per interwał | 0 (walidacja danych) | **Resample psuje WOLUMEN** (11% świec 1h, błędy do 284%) — C2.6 dostawał zepsute wejście. **Grubszy interwał obniża próg opłacalności bez dotykania `p`:** `range` 82,81% (5m) → 56,77% (1h) → **52,74% (4h)**. Przy V=3 `range` spójny na każdym interwale |
| Z19 | 2026-09-22 | [z19-statistical-power](2026-09-22_z19-statistical-power/README.md) | Rachunek MOCY STATYSTYCZNEJ przed eksperymentem — `wald_half_width`, `min_detectable_hit_rate`, `required_trades` + tabela wykonalności per interwał/reżim | 0 (wykonalność przed eksperymentem) | **Rekomendacja z Z9 OBALONA zanim kosztowała eksperyment:** 4h `range` na 3 latach niewykonalne (foldy 21,5 świec < 30; n≤1 551 < wymagane 2 608). Jedyna wykonalna konfiguracja na 3 latach: **1h `range`** (trzeba zmierzyć 58,08% vs dzisiejsze 50,38%) |
| Z5b | 2026-09-22 | [z5b-long-history-4h-preregistration](2026-09-22_z5b-long-history-4h-preregistration/README.md) | Pełna historia 4h (2019-09→2026-07, **14 916 świec, 6,8 roku**, zero dziur) + okna walk-forward skalowane per interwał + pomiar konfliktu spójność↔ekonomia per horyzont. **PRE-REJESTRACJA** eksperymentu (nieuruchomionego) | 0 (dane + wybór specyfikacji) | **4h przeszło z „niewykonalne" na WYKONALNE** (foldy 21,5→48,0; próba 1 551→4 076). Korekta Z19: przy V=3 **60,8% transakcji to timeouty** → próg 52,30%→**54,60%**. Wybrano V=3 (spójność = wymóg poprawności). Margines mocy 4,3×. **Kryterium sukcesu: trafność ≥ 56,15%** |
| S1 | 2026-09-22 | [s1-single-regime-4h](2026-09-22_s1-single-regime-4h/README.md) | **NOWA SERIA:** architektura jednoreżimowa (`range`, bez `trend`) na natywnych świecach 4h, historia 6,8 roku, V=3, walk-forward 60/28/28. Konfiguracja ZAMROŻONA w pre-rejestracji Z5b przed uruchomieniem | 1 (nowa seria) | **KRYTERIUM NIESPEŁNIONE, rozstrzygająco.** n=1 037 (>925, klauzula nierozstrzygalności nie weszła). Trafność **48,60%**, CI [45,56%; 51,64%] — **górny kraniec PONIŻEJ progu 53,07%**, więc z 95% pewnością trafność jest niższa od progu opłacalności. Bramka kosztowa odrzuciła **0%** sygnałów (geometria naprawiona — nie pomogło). `mean_sharpe` −0,59 zamiast −60, co potwierdza, że patologia z C2.12 była artefaktem małych foldów. **REGUŁA STOP URUCHOMIONA** — koniec tej linii hipotezy. **Walidacja (zasada 16a, po fakcie): CAVEATS** — liczby potwierdzone co do cyfry przez 3 niezależne przeliczenia, werdykt odporny (kryterium przepada o 9,04 pp), ale „z zapasem"/„z 95% pewnością" WYCOFANE; `48,60%` to trafność na **6,95% historii** (22 pominięte foldy to systematycznie okna szybkich ruchów, p=4,9e-03; krach COVID poza zbiorem) |
| S1b | 2026-09-22 | [s1b-early-stopping-naprawiony](2026-09-22_s1b-early-stopping-naprawiony/README.md) | Powtórzenie S1 po naprawie Z17b (early stopping faktycznie załącza się: 5/63 → 53/63 foldów). Konfiguracja i kryterium NIEZMIENIONE, adopcja zadeklarowana bezwarunkowo przed uruchomieniem | 0 (naprawa błędu) | **WYNIK NIEROZSTRZYGALNY** — klauzula pre-rejestrowana (`n < 925`) weszła w grę: **n spadło 1 037 → 345**, bo early stopping czyni model ostrożniejszym (abstynencja 70,9% → **90,5%**). Trafność 47,54%, CI [42,27%; 52,81%] — nieodróżnialna i od monety, i od progu. **Konsekwencja:** werdykt S1 zapadł na pipelinie z martwym early stoppingiem; po naprawie konfiguracja 4h/V=3 jest **NIETESTOWALNA** — na `n=925` brakuje **11,4 lat danych, których nie ma** (18,2 potrzebne vs 6,8 dostępne) |
| **Z10** | 2026-09-22 | [z10-zamkniecie-fazy-0](2026-09-22_z10-zamkniecie-fazy-0/README.md) | **DECYZJA BRAMKOWA UŻYTKOWNIKA: zamknięcie Fazy 0 wynikiem negatywnym.** Liczba zbiorcza policzona od zera z `raw_output.txt` wszystkich rund (nie z syntez w write-upach) | 0 (decyzja + synteza) | **DOWÓD BRAKU, nie brak dowodu.** Pooled `p` na 3 najczystszych pomiarach (po naprawie Z17+Z21): **50,27%**, n=**7 687**, CI95 **[49,15%; 51,38%]**, z=+0,47 — nieodróżnialne od monety. **Górny kraniec CI leży 1,30 pp PONIŻEJ najniższego progu opłacalności zmierzonego w projekcie (52,69%)** przy mocy **2,8×** wymaganej próby. Obalone: specyfikacja dwureżimowa + jednoreżimowa `range`. **NIEPRZETESTOWANE (jawnie): momentum, ETH/SOL/BNB, funding-jako-sygnał, ekonomia dźwigni, target≠kierunek, informacja spoza OHLCV.** Walidacja (16a): **READY** |
| **H2.0** | 2026-09-22 | [h2.0-funding-wykonalnosc](2026-09-22_h2.0-funding-wykonalnosc/README.md) | **NOWA HIPOTEZA (H2): wykonalność funding rate.** Nowe dane (7 457 rekordów funding, 0 dziur, 6,8 roku) + 5 analiz: rozkład, trwałość, liczebność, geometria, moc. **ZERO spojrzeń na target** (zaostrzenie wobec C2.7 — powód: C2.13) | 0 (wykonalność przed eksperymentem) | **RACHUNEK MOCY ODRZUCIŁ 2 z 3 SFORMUŁOWAŃ ZA 0 WARIANTÓW.** (a) **bramka na skrajny funding — ODRZUCONA**, moc 0,05–0,44× (bramka zagładza próbę, jak `trend` w Fazie 0); (b) **funding carry — ODRZUCONY**, moc 0,03–0,12%, choć próg opłacalności spada **poniżej 50%** (`p*`=48,13% po kontroli ucięcia barierą) — ogranicza liczba nienakładających się okien 48h, nie próg; żyje w formule PRZEKROJOWEJ; (c) **funding jako 11. cecha bez bramki, 4h — JEDYNE WYKONALNE**, zapas mocy +0,29 pp, wymagany przyrost `p` **+2,85 pp**. **Odkrycia:** masa punktowa 35,85% obserwacji na stawce bazowej ⇒ progi percentylowe nieużywalne (pułapka C2.5 powtórzona); autokorelacja funding lag=1 **+0,797** (sygnał trwały, nie szum); `timeout→taker` w modelu kosztów może być błędem — naprawa dałaby próg 53,12%→52,08%. Walidacja (16a): **READY** |
| **H3** | 2026-09-22 | [h3-noga-timeout-pasmo](2026-09-22_h3-noga-timeout-pasmo/README.md) | Analiza WRAZLIWOSCI na noge wyjscia `timeout` (pasmo maker/taker) + naprawa usterki strukturalnej: bramka kosztowa miala wlasna kopie reguly nog i literal, nic nie wiazalo jej z journalem. Pre-rejestracja w OSOBNYM commicie PRZED kodem | 0 (poprawnosc modelu kosztow, warunek D5) | **RUNDA OBALILA TEZE, KTORA JA ZAMOWILA.** Podejrzenie z H2.0 (`timeout->taker` to blad) NIE broni sie: **noga maker wymaga znanej CENY, a przy barierze pionowej znamy tylko CZAS**; wariant maker bylby tez niespojny z `_resolve_exit_price` (`close` swiecy timeoutu nieosiagalny limitem bez lookaheadu). **Pasmo progu [51,64%; 52,69%], szerokosc 1,05 pp** przy 60,00% timeoutow. **D3: niepewnosc NIEISTOTNA decyzyjnie** — oba krance wymagaja przyrostu trafnosci (+1,37/+2,39 pp nad 50,27% z Z10) wiekszego niz cokolwiek, co dala kiedykolwiek pojedyncza cecha. **Domyslna `TAKER` bez zmian (D1), poprzeczka NIE obnizona (D2), licznik H2 nadal 0/1 (D5).** Walidacja (16a): **READY** — koszt z journalu = policzony z mieszanki wyjsc co do 8. miejsca |
| **H2.1** | 2026-09-22 | [h2.1-funding-jako-cecha](2026-09-22_h2.1-funding-jako-cecha/README.md) | **JEDYNY EKSPERYMENT HIPOTEZY H2:** funding jako cecha (pierwsze zrodlo informacji SPOZA OHLCV), bez bramki rezimu, 4h, V=3, 6,8 roku. Dwa ramiona (4 cechy vs 4+funding) | **1 — LICZNIK H2 WYCZERPANY (1/1)** | **NIEROZSTRZYGNIETY** (klauzula `n < 1 000`): **n = 98**. Przyczyna NIE jest funding ani dlugosc historii, tylko STRUKTURA ZADANIA UCZENIA: zdjecie bramki podnioslo udzial klasy dominujacej (timeout) **60,83% -> 66,58%**, wiec model z dzialajacym early stoppingiem **odmawia kierunku w 99,32%** swiec. Zdjecie bramki zadzialalo (ocenionych swiec 4x wiecej, **zero pominietych foldow** wobec 22/85 w S1), ale proba spadla 345 -> 98. ~~**Jedyne ustalenie:** funding POTROIL liczbe decyzji modelu (35 -> 98), czyli zostal uznany za informacyjny~~ **⚠ WYCOFANE 2026-09-22 (F1): nie odtwarza sie.** Na naprawionym przyrzadzie funding zmienia liczbe decyzji o **1%** (8 114 -> 8 196), nie trzykrotnie — „potrojenie” bylo artefaktem zagladzonej proby. H2.1 nie zostawilo po sobie ZADNEGO ustalenia pozytywnego. **UWAGA: `classify_checkpoint` zwrocil GO dla obu ramion — to ARTEFAKT** `mean_sharpe` przy 3 i 11 waznych foldach (21,3 przy skali 1-3), patologia z C2.12. Walidacja (16a): **CAVEATS** |
| **K1** | 2026-09-22 | [k1-kontrola-pozytywna](2026-09-22_k1-kontrola-pozytywna/README.md) | **KONTROLA POZYTYWNA APARATU** — pierwsza w projekcie. Wstrzykniecie syntetycznej cechy o znanej sile sygnalu do PRAWDZIWYCH swiec BTC 4h + niezmieniony pipeline. Szesc poziomow sily + kontrola negatywna na 6 losowaniach czystego szumu | 0 (kalibracja przyrzadu, POZA licznikami hipotez) | **APARAT DZIALA, ale jest GRUBOZIARNISTY.** (a) Przy wyroczni doskonalej mierzy **100,00%** trafnosci na 4 843 transakcjach — caly lancuch przenosi sygnal bez strat. (b) **Kryterium `ci_low > break_even` jest UCZCIWE: 0 falszywych alarmow na 6 losowaniach szumu** — to uwiarygodnia WSZYSTKIE werdykty projektu. (c) **PROG WYKRYWALNOSCI ~58% trafnosci wobec progu OPLACALNOSCI ~52,7% — luka 5,5 pp, w ktorej sygnal bylby oplacalny i NIEWIDZIALNY.** Przyczyna: abstynencja modelu 99,3-99,7% przy slabym sygnale. (d) **`classify_checkpoint` wystawil GO CZYSTEMU SZUMOWI** — potwierdzenie podejrzenia z H2.1 w mocniejszej formie. (e) Otwarte: trafnosc na szumie 54,09% (z=+1,21, nieistotne, ale n=220 nie wyklucza obciazenia ~7 pp). Walidacja (16a): **CAVEATS** |
| **K2** | 2026-09-22 | [k2-naprawa-abstynencji](2026-09-22_k2-naprawa-abstynencji/README.md) | **NAPRAWA ABSTYNENCJI + domkniecie T6.** Trzy ramiona na tej samej wyroczni co K1 (A0 baseline / A1 wagi klas / A2 wymuszony kierunek), siatka z REPLIKACJA (12 losowan przy q=0, po 3 na punkt) — K1 mial jedno losowanie na punkt, wiec porownywal szumy. Pre-rejestracja w OSOBNYM commicie PRZED kodem | 0 (kalibracja przyrzadu, POZA licznikami hipotez) | **A1 DZIALA, A2 NIE — i DWIE Z TRZECH WLASNYCH BRAMEK OKAZALY SIE WADLIWE.** (a) **A1 (wagi klas) obniza prog wykrywalnosci o krok siatki** (wykrywa q=0,30 wobec q=0,40 dla A0), podnosi n 644 -> 97 014 i **jako jedyne daje MONOTONICZNY odczyt** przyrzadu (A0: 51,71 -> 53,62 -> 51,43 -> 54,84 -> 59,23 — niemonotonicznie, czyli zgaduje). (b) **A2 (wymuszony kierunek) kupuje n bez zysku informacyjnego** — n rosnie 260x, ale trafnosc spada do 50,33% i prog rosnie do 52,94%; przy q=0,30 margines **-1,31 pp**, czyli sygnal informacyjny staje sie NIEOPLACALNY. Mechanizm zmierzony: wymuszony kierunek na swiecach timeout wygrywa **48,33%** (ponizej rzutu moneta). (c) **T6 ZAMKNIETE: kill-switch NIE jest zrodlem obciazenia** — roznica ON-OFF **+0,04 pp przy CI +/-0,34 pp** na 167 160 transakcjach; 54,09% z K1 przypisane szumowi przy n=220. (d) **Bramka 1 (veto) mierzy NIEPRECYZYJNOSC, nie specyficznosc** — literalnie odrzuca kazde ramie o n > ~1 142, czyli karze cel rundy; usterka wyprowadzalna A PRIORI. Zadne ramie nie podnioslo falszywego alarmu (0/12). (e) **Bramka 3 wskazuje A2**, bo mierzy samo pasmo, ignorujac margines. **DECYZJA O ADOPCJI A1 CZEKA NA UZYTKOWNIKA** (wybor odczytu bramki 1). Walidacja (16a): **READY** — 65,6492% przewidziane z rozkladu etykiet = 65,6492% z journalu |
| **K3** | 2026-09-22 | [k3-mierzalnosc-po-a1](2026-09-22_k3-mierzalnosc-po-a1/README.md) | **Czy adopcja A1 przenosi sie z syntetycznej wyroczni na REALNE cechy.** Dwie zamrozone konfiguracje, ktore dostaly werdykt 'nierozstrzygniety' z powodu wielkosci proby (C1 = S1b, C2 = H2.1 ramie A), kazda w dwoch ramionach (none/balanced). REGULA D: runda NIE raportuje trafnosci, bo obie konfiguracje naleza do serii ZAMKNIETYCH. Pre-rejestracja w OSOBNYM commicie PRZED kodem | 0 (kalibracja przyrzadu, POZA licznikami hipotez) | **OBIE KONFIGURACJE WRACAJA DO GRY JAKO MIERZALNE.** C1: abstynencja 90,53% -> 46,32%, n **345 -> 1 955**, pasmo **5,28 -> 2,22 pp**. C2: abstynencja 99,76% -> 43,84%, n **35 -> 8 033**, pasmo **16,56 -> 1,09 pp**. Oba ponizej kotwicy 2,42 pp (luka 52,69% H3 minus 50,27% Z10), czyli przyrzad widzialby efekt zamykajacy znana luke. **Wynik negatywny byl mozliwy i nie wystapil** - abstynencja spadla na realnych cechach mocniej niz na wyroczni. **CENA, zmierzona:** przed adopcja model WYBIERAL swiece konczace sie na barierze (C2: 37,1% timeoutow wobec 66,5% w populacji), po adopcji bierze je po rowno - **selektywnosc znika**, bariera maleje, prog oplacalnosci rosnie o ~0,5 pp. **Czy ta selektywnosc niosla informacje - RUNDA NIE MA JAK ROZSTRZYGNAC** (regula D), i to ograniczenie bylo zapisane z gory. Walidacja (16a): **READY** - `n` przeliczone z abstynencji przez `expected_trades` zgodne do 0,3 transakcji, a ramie `none` odtworzylo liczby opublikowane w S1b (345) i H2.1 (35) CO DO SZTUKI |
| **T1-diag** | 2026-09-22 | [t1-diag-realny-funding](2026-09-22_t1-diag-realny-funding/README.md) | **Czy realny funding w modelu kosztow cokolwiek zmienia.** Trzy modele funding na TEJ SAMEJ populacji 8 033 transakcji: stala+ulamkowo (obecny), realne+ulamkowo, realne+dyskretnie (poprawny). Diagnostyka, zero zmian w kodzie | 0 (diagnostyka poprawnosciowa) | **NIEZASADNE — i PREMISA ZADANIA BYLA BLEDEM KATEGORII.** Przejscie na model poprawny przesuwa prog oplacalnosci o **+0,022 pp** (52,933% -> 52,954%), przy niepewnosci pomiaru 1,09 pp i szukanym efekcie 2,42 pp — zmiana 50x mniejsza od niepewnosci. **Stala 0,0001 jest DOKLADNIE MEDIANA** realnego rozkladu (srednia 0,000107, +7,1%), wiec dobrano ja trafnie. **Kierunek ODWROTNY do sugerowanego w zadaniu:** realny funding jest odrobine DROZSZY, nie tanszy. Premisa „−0,00243% = przychod" myli signowany koszt per transakcja (policzony JUZ ta stala, dla proby z przewaga shortow) ze stawka za okres. Tutaj long/short 49,96/50,04%, wiec funding nettuje sie do zera NIEZALEZNIE od stawki. **Warunek waznosci: strategia jednostronna uniewaznilaby wniosek.** Walidacja (16a): **READY** |
| **M1** | 2026-09-22 | [m1-momentum-bez-bramki](2026-09-22_m1-momentum-bez-bramki/README.md) | **NOWA HIPOTEZA M, licznik od zera.** Momentum po raz pierwszy na probie zdolnej cokolwiek rozstrzygnac. Dwa ramiona w konfiguracji K3/C2 (bez bramki, 4h, V=3, wagi klas): A reversion (odniesienie, 0 wariantow), B momentum (kandydat). JEDNA zmienna: zestaw cech. Pre-rejestracja w OSOBNYM commicie PRZED kodem | **1 — LICZNIK M WYCZERPANY (1/1)** | **NEGATYWNY — dowod braku, nie brak dowodu.** Momentum: **n = 8 512, trafnosc 49,74%, CI [48,68%; 50,80%]** wobec progu **52,94%** — gorny kraniec CI lezy **2,14 pp PONIZEJ progu**, przy probie **1,90x** wymaganej do orzeczenia negatywu (moc 80%). Zamyka pozycje z wniosku 12. **NIE wolno czytac jako 'momentum gorsze od reversion':** roznica B-A = **-0,63 pp, CI [-2,15; +0,90], z = -0,80** — nieistotna. Momentum nie jest gorsze, jest TAK SAMO nieobecne. **Ramie odniesienia odtworzylo historyczny pomiar projektu CO DO 0,01 pp** (50,3672% wobec 50,38% z 5m/range) na ZUPELNIE INNEJ konfiguracji — niezalezne potwierdzenie, ze aparat mierzy to samo. Ograniczenie zapisane z gory: wykrywalnosc zaczyna sie od 54,00%, wiec edge rzedu 53% bylby niewidoczny. Walidacja (16a): **READY** — trafnosc przeliczona wprost z journalu, roznica 0,000000 pp |
| **P1** | 2026-09-22 | [p1-sonda-zrodel-danych](2026-09-22_p1-sonda-zrodel-danych/README.md) | **Sonda wykonalnosci zrodel danych** przed wydaniem jakiegokolwiek wariantu (rola jak Z19). Ile historii Binance oddaje dla danych POZYCJONOWANIA: open interest, long/short ratio, pozycje top traderow. Odczyt, zero zmian w repo | 0 (diagnostyka wykonalnosci) | **CALA KLASA ZRODEL ODPADA MECHANICZNIE.** Wszystkie piec endpointow `futures/data/*` oddaje **30,8 dnia** (186 swiec 4h), a jawny `startTime` z 2020 zwraca **HTTP 400** — to granica tego, co gielda przechowuje, nie limit zapytania. **KONTROLA:** `klines` i `fundingRate` przy tym samym `startTime` oddaja dane od 2020-01-01, wiec ograniczenie lezy w TYCH endpointach, nie w sondzie. Rachunek: 186 swiec -> ~112 transakcji wobec wymaganych 4 481, **brakuje 40x**; potrzeba 3,4 roku, jest 0,084 roku. Jedyna droga: zbieranie od dzis, wynik za ~3,4 roku |
| **F1** | 2026-09-22 | [f1-funding-zmierzony](2026-09-22_f1-funding-zmierzony/README.md) | **NOWA HIPOTEZA F, licznik od zera.** Funding jako cecha — pytanie z H2.1, ktore tam zostalo NIEROZSTRZYGNIETE przy n=98, zadane ponownie na przyrzadzie po adopcji A1. H2 pozostaje zamkniete; F to nowa hipoteza, ta sama droga co M. Pre-rejestracja w OSOBNYM commicie PRZED kodem | **1 — LICZNIK F WYCZERPANY (1/1)** | **NEGATYWNY — dowod braku, nie brak dowodu.** Funding: **n = 8 127, trafnosc 50,34%, CI [49,25%; 51,43%]** wobec progu **52,94%** — gorny kraniec CI **1,51 pp PONIZEJ progu**, przy probie **1,81x** wymaganej. Roznica wobec ramienia bez funding: **-0,03 pp, CI [-1,57; +1,51], z = -0,04** — zero. **RUNDA OBALA JEDYNE USTALENIE H2.1:** „funding potraja liczbe decyzji” nie odtwarza sie (2,80x -> **1,01x**) — bylo artefaktem zagladzonej proby. **Potrojna kontrola odtwarzalnosci:** ramie odniesienia dalo n=8 033, trafien=4 046, p=50,3672% identycznie jak w M1 i niezaleznie od doklejenia nieuzywanej kolumny. Walidacja (16a): **READY** |
| **P2** | 2026-09-22 | [p2-sonda-carry-przekrojowy](2026-09-22_p2-sonda-carry-przekrojowy/README.md) | **Sonda wykonalnosci carry przekrojowego (hipoteza 4A)** przed wydaniem wariantu: 20 najwiekszych monet wg kapitalizacji (POPRAWKA 1 do pre-rejestracji, decyzja uzytkownika — jawny blad przezywalnosci), okna 48h 2020-01→2026-07, koszyki 2 SHORT (najwyzszy funding) / 2 LONG (najnizszy). Runda nie liczy sredniego zwrotu z cen ani P&L. Pre-rejestracja i poprawka w OSOBNYCH commitach PRZED kodem/uruchomieniem | 0 (wykonalnosc przed eksperymentem) | **NIEMIERZALNA.** D1 spelnione: funding pokrywa koszt — F−C = **0,097% na 48h, CI [0,051%; 0,143%]** (przy koszcie taker CI obejmuje zero; mechanizm slabnie: 2020–21 ~0,16%, od 2023 ~0,05%). **D2 niespelnione:** rozrzut wyniku okna σ = **5,56%** (57× zysk z oplaty) ⇒ potrzeba **25 850 okien (~140 lat)**, jest **1 161 (0,045×)**. **Obalone zalozenie ze STATUS §17:** 18 monet ≈ **k_eff = 2,0** niezaleznych (korelacja 0,47) — przekroj NIE mnozy proby. Walidacja (16a): **CAVEATS** — F przeliczone od zera w 6 oknach, zgodnosc do 5. miejsca |
| **T4** | 2026-09-23 | [t4-kalibracja-early-stopping](2026-09-23_t4-kalibracja-early-stopping/README.md) | **Kalibracja early stoppingu** (`validation_fraction`, `MIN_VALIDATION_ROWS`) w konfiguracji kanonicznej (4h, bez bramki, V=3, `balanced`, 60/28/28): zagniezdzony podzial WYLACZNIE wewnatrz danych treningowych kazdego okna (86 okien) — decyzja ES oceniana na ogonie, ktorego nie widziala. Pre-rejestracja w OSOBNYM commicie PRZED kodem | 0 (kalibracja przyrzadu, POZA licznikami hipotez; zero etykiet z danych testowych) | **EARLY STOPPING DZIALA, PROG 30 WIERSZY BEZCZYNNY, ZMIAN BRAK.** ES bije 200 drzew w **86/86** oknach (strata −0,617, CI [−0,683; −0,552]; bez ES +58%). `max(30, ·)` zmienia `n_val` w **0/86** oknach (walidacja ma 68–71 wierszy). Przy wagach `balanced` ES **obniza** abstynencje (44,4% vs 62,0% przy 200 drzewach) — watpliwosc z S1b nie dotyczy obecnej konfiguracji. **Wynik uboczny:** najlepsza mozliwa liczba drzew (wyrocznia) poprawia strate tylko o **0,7%** wobec ln 3 (zgadywanie po rowno), w 41/86 oknach najlepsze jest 1 drzewo, a ES jest istotnie GORSZY od 1 drzewa (+0,024, CI [+0,009; +0,039]) — cechy nie niosa informacji; potwierdzenie wniosku 39 inna droga. D3 (`f`=0,3 „lepsze”) NIE jest podstawa zmiany: na danych bez sygnalu kazde skrocenie treningu wyglada lepiej. Walidacja (16a): **READY** |
| **W1** | 2026-09-23 | [w1-wykonanie-po-cenie](2026-09-23_w1-wykonanie-po-cenie/README.md) | **NOWA SERIA W: wykonanie po konkretnej cenie** (decyzja użytkownika, zasada obowiązująca też na żywo). Symulacja wypełnień na ścieżce cen zamiast odczytu z etykiety (`backtest/execution.py`, tryb `fill_model="path"` w silniku): 3 reguły wejścia (limit po close / limit na cofnięciu 0,5·ATR / stop na wybiciu), ważność 1 świeca z horyzontu modelu, TP/SL od ceny wypełnienia, kolejność wewnątrz świecy 4h rozstrzygana świecami 5m (2023–26). Jeden trening dla wszystkich wariantów; kontrola = ramię A M1/F1 co do sztuki. Pre-rejestracja w OSOBNYM commicie PRZED kodem | **3 — LICZNIK W WYCZERPANY (3/3)** | **W1a NEGATYWNY:** limit po close wypełnia się w 99,4 %, p 50,11 % [49,02; 51,21] vs próg 52,96 % — założenie C2.12 było prawie prawdziwe. **W1b NIEROZSTRZYGNIĘTY wg kryterium trafności** (53,15 % [51,32; 54,98] vs 52,81 %, n 2 858 < 3 276) — **ale zwrot netto istotnie ujemny (t −3,90)**: iluzja geometrii, małe wygrane na timeoutach (+0,17 %) i pełne straty na SL (−2,45 %), SL:TP 21:16. **W1c NEGATYWNY** (46,13 % vs 54,83 %, noga taker). Przybliżenie 4h vs 5m: zgodność 97–99,7 %, rozbieżności wyłącznie konserwatywne. **Adverse selection z C2.12 po raz pierwszy ZMIERZONA** (−53,8 pp poprawności wg etykiety dla cofnięcia). Walidacja (16a): **CAVEATS** — 53,15 % nie wolno cytować bez t-statu |
| **N1** | 2026-09-23 | [n1-nowy-cel-czesciowe-tp](2026-09-23_n1-nowy-cel-czesciowe-tp/README.md) | **NOWA SERIA N: nowy cel modelu** (decyzje użytkownika: 50 % pozycji na +5 % depozytu przy 3× = +1,67 % ceny, stop na cenę wejścia, reszta do 1,5·ATR, 12 h) — jako NAKŁADKA zarządzania na ścieżce (`ManagedExitRule`), etykieta bez zmian, ten sam model i wejście (limit po close). **NOWA BAZA DANYCH: od 2021-01-01 (zasada 20)**, 69 okien, 6 911 sygnałów. Kontrola = pojedyncze wyjście na tych samych sygnałach. Kryterium na zwrocie netto (t_neff) z progiem uogólnionym p*. Pre-rejestracja `fa1abdb`, Poprawka 1 (reguła 6) + kod `4683669` PRZED uruchomieniem | **1 — LICZNIK N WYCZERPANY (1/1)** | **NEGATYWNY.** Zwrot netto −0,094 % [−0,131; −0,058] na transakcję, t_neff −4,08 (kontrola −0,107 %); **różnica parowana +0,007 % [−0,009; +0,024]** — zero. Trafność 49,6 → **53,3 %** [52,2; 54,5] przy progu ±B 53,32 % („na styk") — iluzja W1b w czystej postaci: próg uogólniony **p\* = 57,24 %** (W̄ 1,11 % vs L̄ 1,30 %). Strata siedzi w 68 % transakcji bez bliższego celu (timeouty −0,26 %, stopy −2,3 %). Walidacja (16a): **READY** |
| **A1** | 2026-09-23 | [a1-formacje-swiecowe](2026-09-23_a1-formacje-swiecowe/README.md) | **NOWA SERIA A: analiza techniczna — formacje świecowe** (decyzja użytkownika, skill `ta-toolkit`). Wskaźnik `cdl_score_6` = suma znaków 6 formacji z podręcznika (TA-Lib: objęcie, młot, spadająca gwiazda, gwiazda poranna/wieczorna, trójka; 0 stopni swobody, doji wyłączone). Dwa ramiona na tej samej populacji świec co kontrola N1 (2021+, 69 okien): **A1a** reguła bez modelu (kierunek = sign(score), limit po close k=1, ±1,5·ATR, 12 h), **A1b** ta sama informacja jako 5. cecha modelu. Kryterium dwóch warunków; pre-rejestracja `f514bcf`, kod `26f187b` | **2 — LICZNIK A (formacje) WYCZERPANY (2/2)** | **OBA NEGATYWNE.** A1a: p **46,35 %** [44,38; 48,31] — cały CI PONIŻEJ 50 %; zwrot netto **−0,177 %** [−0,245; −0,109], t −5,11, n 2 477. Objęcie (84 % sygnałów) 45,7 % [43,6; 47,8]: duża świeca w kierunku sygnału jest na 4h BTC częściej końcem ruchu. A1b: −0,113 % [−0,155; −0,071], p 49,39 %; **różnica parowana wobec kontroli −0,001 % [−0,012; +0,010]** (6 444/6 577 identycznych). Rachunek mocy z częstości formacji trafił do 2 %. Poprawka 2 (raportowa): cap N_eff ≤ n. Walidacja (16a): **READY** |
| **A2** | 2026-09-23 | [a2-rodziny-at](2026-09-23_a2-rodziny-at/README.md) | **Pozostałe rodziny AT ze skilla `ta-toolkit` jako reguły** (decyzja użytkownika „wykonaj"): 10 cech deterministycznych (`agents/ta_rules.py`, parametry domyślne skilla, test przecieku), populacja kontroli N1 (2021+, 69 okien). Rachunek mocy z częstości sygnału: 3 reguły stanowe osobno (**A2.1** struktura trendu HH/HL, **A2.2** Fibonacci 38–62 %, **A2.3** wsparcie/opór ≤ 0,5·ATR), 5 zdarzeniowych osobno NIEMIERZALNE (86–988 sygnałów) → jedna grupa **A2.4** (sign sumy), **A2.5** model + 10 cech AT. Pozytyw przy z_5 = 2,576 (Bonferroni). Pre-rejestracja `f9805fa`, skrypt `d80b621` | **5 — LICZNIK A = 7/7, WSZYSTKIE RODZINY AT ZAMKNIĘTE (STOP)** | **3 NEGATYWNE, 2 NIEROZSTRZYGNIĘTE, 0 POZYTYWNYCH.** A2.1 p **48,20 %** [46,98; 49,42], −0,127 % [−0,170; −0,084] (t_neff −3,90; N_eff 2 875/6 423); A2.3 49,87 %, −0,080 % [−0,114; −0,045]; A2.5 −0,099 % [−0,141; −0,056], parowane z kontrolą +0,005 % [−0,055; +0,066] przy 35 % zmienionych decyzji i abstynencji 40,4 → 42,7 %; A2.2 51,5 % [49,4; 53,6], −0,041 % [−0,110; +0,028] — rozdzielczość; A2.4 48,3 %, −0,103 % [−0,182; −0,024] — guard n 2 133 < 2 366. Reguły „z ruchem" znów pod monetą. Kill-switch tłumi 3,8–4,8 % wypełnień reguł stanowych. Walidacja (16a): **READY** |
| **C1** | 2026-09-23 | [c1-cash-and-carry](2026-09-23_c1-cash-and-carry/README.md) | **NOWA SERIA C — cash-and-carry z hedgem spot na BTC** (punkt 2 zlecenia użytkownika; kierunek otwarty po P2): long spot + short perp, P&L per okres 8h = funding otrzymany + (r_spot − r_perp) − koszty przełączeń (0,19 % na wejście/wyjście: spot 0,10 % + perp 0,05 % + poślizg). **Nowe źródło: świece 8h spot Binance** (6 021, 0 dziur, znaczniki = perp = funding). Target: **carry (przepływ), nie kierunek**; próg 0; N_eff z autokorelacji; z_2 = 2,241. Ramiona: C1a zawsze w pozycji, C1b po dodatnim ostatnim fundingu. Pre-rejestracja `a8ce150`, kod `ae169f4` | **2 — LICZNIK C WYCZERPANY (2/2)** | **C1a POZYTYWNY — pierwszy w projekcie, ale to przepływ kontraktowy, nie prognoza:** +0,0099 %/8h [+0,0063; +0,0135], t_neff **+5,40** przy **N_eff 286** (funding lag-1 0,84); rocznie **+10,9 % nominału [6,9; 14,8] = +5,4 % kapitału [3,5; 7,4]**; Σ funding 60,2 %, Σ hedge −0,13 %, koszty 0,38 %, obsunięcie 0,64 %. **Połowa z 2021** (15 %/rok kapitału); 2022–2026: 0,4–6 %/rok; ostatnie 3 lata 3,6 % brutto. **C1b NEGATYWNY:** 875 przełączeń = 166 % kosztów, −9,3 %/rok kapitału. Nie mierzone: likwidacja shorta (+90 %/30 dni w 2021), ryzyko giełdy, koszt kapitału. Walidacja (16a): **READY** |
| **R1** | 2026-09-23 | [r1-premia-rebalansowa](2026-09-23_r1-premia-rebalansowa/README.md) | **NOWA SERIA R — premia rebalansowa (B2), „inny cel niż kierunek"**: koszyk top-20 po 30-dniowym obrocie, skład point-in-time miesięcznie (uniwersum P2 z wycofanymi, 281 symboli), od 2021-02 (zasada 20), 65 koszyków, 1 976 dni; A = równe wagi codziennie vs B = równe wagi na starcie miesiąca; premia = r_A − r_B − 0,10 % × obrót. Próg 0, jedno ramię. Pre-rejestracja `fb18d98`, kod `f4569bd` + naprawa testu `db16af7` | **1 — LICZNIK R WYCZERPANY (1/1)** | **NIEROZSTRZYGNIĘTY, punktowo UJEMNY:** netto **−3,55 %/rok [−9,50; +2,40]**, brutto −2,68 %, koszt 0,87 %; wartość A względem B **−12,1 %** przez 5,4 roku; 36/65 miesięcy dodatnich. Scenariusz „ruchy niezależne" (6–11 %/rok brutto, zapisany przed wynikiem) POZA CI (górny kraniec +3,3 %) → momentum względne wewnątrz miesiąca zjada premię. Rozdzielczość 8,5 %/rok (3× gorsza niż proxy ex ante — ogony dyspersji). Walidacja (16a): **READY** |
| **P3** | 2026-09-23 | [p3-sonda-zrodel-ii](2026-09-23_p3-sonda-zrodel-ii/README.md) | **Sonda źródeł danych II + podłączenie** (decyzja użytkownika: „podpięcie dodatkowych danych"): brama G1–G4 zapisana PRZED pobraniem; kolektor `data/fetch_external.py` (8 źródeł, bez kluczy, idempotentny) + profil `data/profile_external.py`; przegląd bezpieczeństwa (1 znalezisko poprawione) | **0 — POZA licznikami** (0 korelacji ze zwrotem) | **Archiwum `data.binance.vision` ma pozycjonowanie (OI, L/S top traderów i wszystkich kont, taker ratio) co 5 min od 2020-09-01: 2 213 dni, zero brakujących, pokrycie bazy 99,90 % — P1 sprawdziło tylko REST (30 dni).** Przechodzą też: funding COIN-M od 2020-08 (masa 42,7 % na 0,0001), 24 kontrakty kwartalne 8h (330 pustych świec po wygaśnięciu), DVOL od 2021-03-24 (95,9 %), CoinMetrics 14 metryk on-chain (0 braków), F&G, Coinbase; FRED jako tło. Dziura: top-trader L/S 2021-12→2022-12 (16 % bazy). Odpadły: likwidacje (archiwum puste), OKX, bookDepth (od 2023). Walidacja (16a): **READY** |
| **D1** | 2026-09-23 | [d1-produkt-carry](2026-09-23_d1-produkt-carry/README.md) | **Produkt cash-and-carry po C1a — cztery otwarte pytania:** Q1 depozyt/likwidacja USDT-M (siatka 4 × 4, run-up), Q2 COIN-M (zabezpieczenie w BTC, kapitał 1×, wartość USD stała — tożsamość), Q3 basis 24 kontraktów kwartalnych vs funding zrealizowany, Q4 T-bill (FRED). Pre-rejestracja + kod `93b3c6e`; Poprawka 1 (koszt uzupełnień depozytu) przed zamrożeniem | **0 — POZA licznikami** (0 reguł; COIN-M i basis = generalizacja C1a na inny instrument) | **COIN-M: +9,07 %/rok [5,88; 12,26] na kapitale 1×, bez likwidacji z konstrukcji** (stawka niższa od USDT-M o 1,82 pp [0,53; 3,11], N_eff 153). USDT-M: M = 1,0 + uzupełnianie miesięczne → 0 likwidacji, +5,29 % na kapitale 2×; tanie depozyty (0,25–0,5) mają zapas kilku pp po `high` i koszt uzupełnień do 1,43 %/rok. Basis kwartalny ≈ funding (różnica median +1,8 / −0,9 pp, rozstęp ±17). Ponad T-bill od 2022: COIN-M **+1,8 pp/rok** (−1,5…+7,2), USDT-M 2× −1,0 pp. Walidacja (16a): **READY** |
| **X1** | 2026-09-23 | [x1-momentum-przekrojowe](2026-09-23_x1-momentum-przekrojowe/README.md) | **NOWA SERIA X — momentum przekrojowe (B1), hipoteza odwrotna do R1:** top-20 point-in-time, sygnał = zwrot 28 dni, long top-5 / short bottom-5, trzymanie 7 dni, koszty 0,07 % × obrót + funding per symbol; rachunek mocy ze 100 losowych rankingów (half-width 21,2 %/rok, koszt pod H0 5,6 %/rok) → MIERZALNA; pre-rejestracja `dfca77b` | **1 — LICZNIK X WYCZERPANY (1/1)** | **NIEROZSTRZYGNIĘTY, punktowo WYRAŹNIE DODATNI:** netto **+22,0 %/rok [−5,3; +49,3]**, t_neff 1,58, Σ +119 % w 5,4 roku, dodatni w 6/6 lat (2025 = 52 % sumy), korelacja z BTC −0,13, odporny na ogony; IC +0,028 [−0,007; +0,064]; obrót 0,87/formowanie, koszty 3 %/rok, funding +1 %/rok; efekt głównie z nogi short (przegrani tracą dalej). Obietnica literatury 52 % na granicy CI brutto. Rozdzielczość 27 %/rok — trzeba ~4× próby. Walidacja (16a): **READY** |
| **O1** | 2026-09-23 | [o1-pozycjonowanie](2026-09-23_o1-pozycjonowanie/README.md) | **NOWA SERIA O — pozycjonowanie (archiwum P3) jako 5. cecha modelu 4h:** `oi_change_24h` = log(OI_t/OI_t−6) z ostatniego odczytu 5-min WEWNĄTRZ świecy (bez lookaheadu: test jednostkowy + shift-forward + walidacja na realnych danych); jedna cecha po mechanizmie (dźwignia → kaskady likwidacji); kontrola vs O1 parowo, kryterium dwóch warunków, m = 1; pre-rejestracja `faa11e1` | **1 — LICZNIK O WYCZERPANY (1/1)** | **NEGATYWNY:** −0,074 % [−0,116; −0,032] na transakcję, t_neff −2,90, p 50,25 % [49,06; 51,44] vs p* 53,07 %. **Ale pierwsza cecha spoza OHLCV, która porusza model:** wobec kontroli +0,024 pp [−0,019; +0,067], inny kierunek w 20,6 % transakcji, trafność +0,67 pp, korelacja z wolumenem 0,045; kontrola odtworzona co do sztuki. Walidacja (16a): **READY** |
| **L1** | 2026-09-23 | [l1-onchain-podaz](2026-09-23_l1-onchain-podaz/README.md) | **NOWA SERIA L — on-chain:** `ex_supply_change_7d` (log-zmiana podaży BTC na giełdach 7 dni, CoinMetrics, dostępność +2 dni) jako 5. cecha modelu 4h; jedna z trzech serii pre-rejestrowanych w jednym commicie `3278442` (wzorzec O1) | **1 — LICZNIK L WYCZERPANY (1/1)** | **NEGATYWNY:** −0,097 % [−0,140; −0,054], t_neff −4,23, p 49,79 % [48,56; 51,02] vs p* 53,51 %; parowo +0,003 pp [−0,047; +0,052]; abstynencja 40,4 → 44,3 %; korelacje z kontrolą ≤ 0,08. Walidacja: **READY** |
| **V1** | 2026-09-23 | [v1-premia-zmiennosci](2026-09-23_v1-premia-zmiennosci/README.md) | **NOWA SERIA V — opcje/vol:** `vrp_30d` = DVOL/100 − zrealizowana 30 dni (Deribit, +1 dzień; od 2021-03-24) jako 5. cecha modelu 4h | **1 — LICZNIK V WYCZERPANY (1/1)** | **NEGATYWNY:** −0,076 % [−0,120; −0,031], t_neff −2,60, p 50,49 % [49,21; 51,77] vs p* 53,42 %; parowo +0,018 pp [−0,037; +0,074]; abstynencja 47,7 %; punktowo najlepsza z trzech (jak O1), za mało o rząd wielkości. Walidacja: **READY** |
| **G1** | 2026-09-23 | [g1-strach-chciwosc](2026-09-23_g1-strach-chciwosc/README.md) | **NOWA SERIA G — sentyment:** `fng_level` = Fear & Greed / 100 (alternative.me, +4h) jako 5. cecha modelu 4h | **1 — LICZNIK G WYCZERPANY (1/1)** | **NEGATYWNY:** −0,102 % [−0,144; −0,059], t_neff −3,48, p 49,90 % [48,66; 51,13] vs p* 53,86 %; parowo +0,002 pp [−0,045; +0,049]; korelacja z `rsi_14` 0,29 (częściowo przebranie kontroli). Walidacja: **READY** |
| **X2** | 2026-09-23 | [x2-momentum-top50](2026-09-23_x2-momentum-top50/README.md) | **NOWA SERIA X2 — momentum przekrojowe (B1) na szerszym koszyku** (decyzja użytkownika „wykonaj oba"): top-50 point-in-time, nogi po 10, od 2021-05-01 (wcześniej < 50 kandydatów), reszta jak X1; moc z symulacji: half-width 17,5 %/rok (×1,3 = 22,8) → MIERZALNA; pre-rejestracja `5293346` | **1 — LICZNIK X2 WYCZERPANY (1/1)** | **NIEROZSTRZYGNIĘTY, słabszy niż X1:** +0,044 %/dzień [−0,034; +0,121], t 1,10, **+15,9 %/rok [−12,3; +44,2]**; IC **−0,006 [−0,033; +0,022]**; 33 skrajne dni = 52 % sumy; 2022 −20 %; korelacja z BTC −0,11. **Walidacja krzyżowa: reguła X1 na siatce X2 daje +0,024 %/dzień (Σ +46 %) zamiast +0,060 — X1 wrażliwe na fazę tygodniowego rebalansu.** Walidacja: **READY** |
| **Y1** | 2026-09-23 | [y1-horyzont-1h](2026-09-23_y1-horyzont-1h/README.md) | **NOWA BAZA 1h (decyzja użytkownika „dla 2 sprawdź horyzont 1h oraz 1d"): model kontrolny (4 cechy REVERSION, V = 3 świece, 60/28/28) na natywnych 1h od 2021-01-01 (1/1)** | **NEGATYWNY z ogromnym zapasem:** p **48,34 % [47,70; 48,98]** (CI w całości < 50 %) vs p* 54,01 %; r̄ netto −0,078 % [−0,090; −0,066], t_neff −11,74, n 23 334 (41× wymaganego); 6/6 lat ujemnych; timeout 63 % z p 45,6 %. Ex ante/ex post zgodne (hw 0,59 → 0,64 pp). Walidacja: **READY** |
| **Y2** | 2026-09-23 | [y2-horyzont-1d](2026-09-23_y2-horyzont-1d/README.md) | **NOWA BAZA 1d: ten sam model, okna 365/91/91 (parametr bazy), natywne 1d od 2021-01-01 (1/1)** | **NIEROZSTRZYGNIĘTY (jak zapowiedziano przy n ≈ 1 000):** p 50,20 % [47,07; 53,34] vs p* 51,70 %; r̄ netto −0,094 % [−0,344; +0,156], t_neff −0,60, n 978, half-width 3,1 pp; lata 2022 +92 % / 2024 −140 % = rozrzut bariery 6 %, nie sygnał. Walidacja: **READY** |
| **TS1** | 2026-09-24 | [ts1-trend-koszyk](2026-09-24_ts1-trend-koszyk/README.md) | **NOWA SERIA TS — momentum w czasie (trend) na koszyku top-20** (decyzja użytkownika „testuj dalej różne kombinacje”; kandydat z panelu 5 propozycji): znak zwrotu 28 dni per moneta, σ̂ EWMA, cel 40 %/rok, sufit 3×, 7 faz tygodniowych, realny funding; H0 = prawdziwe znaki przesunięte w czasie; pre-rejestracja `d066412` (1/1) | **NIEROZSTRZYGNIĘTY, najsilniejszy ślad w projekcie:** +14,8 %/rok netto [−1,7; +31,3], t_neff **1,76**; ponad 100/100 portfeli H0 (q97,5 +13,0); bootstrap blokowy [+1,1; +29,3]; 6/6 lat i 7/7 faz dodatnich; zawsze-long +1,5 %/rok, korelacja −0,19; bez 10 najlepszych dni +6,1 %; 3× kapitału → CAGR +4,9 %, obsunięcie 90 %. Walidacja: **READY (Caveats)** |
| **NL1** | 2026-09-24 | [nl1-nowe-listingi](2026-09-24_nl1-nowe-listingi/README.md) | **NOWA SERIA NL — short na nowych kontraktach USDT-M przez 14 dni** (rodzina G2, zdarzenia; nowe źródło: archiwum listingów `data/fetch_listings.py`): 569 pierwszych listingów krypto 2021–2026 (wycofane włącznie), wejście open d0+1, wyjście close d0+14, realny funding, likwidacja izolowana; kryterium t klastrowe (miesiąc); pre-rejestracja `47e196d` (1/1) | **NIEROZSTRZYGNIĘTY:** +2,12 % na zdarzenie [−2,68; +6,93], t 0,87; mediana +13,5 %, 66 % zyskownych, ale 11,8 % zdarzeń to podwojenie ceny w 14 dni (likwidacja przy 1×); funding −1,15 % średnio (short płaci w 41 %); 3× → 41,5 % likwidacji, +0,95 % na nominał. Walidacja: **READY** |
| **CP1** | 2026-09-24 | [cp1-premia-coinbase](2026-09-24_cp1-premia-coinbase/README.md) | **NOWA SERIA CP — premia Coinbase → kierunek BTC na tydzień** (decyzja użytkownika „sprawdź 3 nowe hipotezy”): znak(średnia premii 7 dni − 90 dni), perpetual BTCUSDT silnikiem TS1 (σ̂, 40 %, 7 faz, realny funding); pre-rejestracja (1/1) | **POZYTYWNY wg pre-rejestracji (PIERWSZY w projekcie), nieistotny po korekcie rodzinnej:** +32,0 %/rok [+2,0; +62,1], t_neff 2,09, ponad 98 % H0; alfa ponad trend 28 dni +24,0 %/rok, t 1,67; test opóźnienia bez śladu przecieku (+27,5 / +20,9 %/rok przy 1/2 dniach); bez 10 najlepszych dni +16 %/rok; 3× kapitału → obsunięcie 94 %. Walidacja: **Caveats** |
| **TF1** | 2026-09-24 | [tf1-trend-filtr-tloku](2026-09-24_tf1-trend-filtr-tloku/README.md) | **NOWA SERIA TF — trend TS1 z filtrem tłoku** (decyzja użytkownika „sprawdź 3 nowe hipotezy”): pozycja zerowana, gdy jej strona płaci Σ funding 7 dni > 0,63 %; kryterium różnica parowana z TS1; pre-rejestracja `4762d86` (1/1) | **NIEROZSTRZYGNIĘTY, punktowo gorzej:** TF1 − TS1 −1,41 %/rok [−6,58; +3,77], t_neff −0,53; 9,3 % pozycji wyzerowanych; 4/6 lat ujemnych. Walidacja: **READY** |
| **TR1 / TP1** | 2026-09-24 | [ts-poza-proba](2026-09-24_ts-poza-proba/README.md) | **Reguła TS1 poza próbą** (decyzja użytkownika „sprawdź na innych przedziałach”): TR1 = monety z miejsc 21–50 (inne aktywa, 2021-05 → 2026-06, werdykt), TP1 = top-20 na nowych danych 2026-07 → 09 (opisowo, próg obalenia z góry); pre-rejestracja `40d604a` (seria TS 2/2) | **TR1 NIEROZSTRZYGNIĘTY, powtarza TS1:** +14,1 %/rok [−3,0; +31,2], t 1,62, ponad 99 % H0, 6/6 lat, 7/7 faz; korelacja z TS1 0,86. **TP1:** 78 dni, +0,69 % (+4,6 %/rok) — brak obalenia. Walidacja: **READY (Caveats)** |
| **CP1P** | 2026-09-24 | [cp1-poza-proba](2026-09-24_cp1-poza-proba/README.md) | Odczyt prospektywny CP1 (reguła zamrożona) na danych 2026-07 → 09, 0 wariantów, próg obalenia z góry | **Brak obalenia, brak potwierdzenia:** 78 dni, +0,13 % przy BTC +33 %; fazy ±30 %. Walidacja: **READY** |
| **TL1** | 2026-09-24 | [tl1-tlok-przekrojowy](2026-09-24_tl1-tlok-przekrojowy/README.md) | **NOWA SERIA TL — tłok lewara na przekroju top-20** (nowe źródło: dzienny OI z archiwum, `data/fetch_oi_panel.py`): crowd = Δlog OI 7 dni × znak zwrotu 7 dni, long 5 najniższych / short 5 najwyższych, 7 faz; pre-rejestracja `3983e3a` (1/1) | **NIEROZSTRZYGNIĘTY, punktowo ujemny:** −10,5 %/rok [−25,2; +4,2], t_neff −1,39; IC +0,008 [−0,024; +0,040] — brak informacji, koszty 23,6 %. Walidacja: **Caveats** |
| **LQ1** | 2026-09-24 | [lq1-likwidacje](2026-09-24_lq1-likwidacje/README.md) | **POPRAWKA TS1: likwidacja izolowana przy 3×** (depozyt = ekspozycja/3, próg 1/3 − 1 %, dzienne high/low z archiwum — nowy kolektor `data/fetch_universe_ohlc.py`); 0 wariantów | **Koszt likwidacji −3,6 %/rok [−5,8; −1,4], t −3,16;** TS1 z likwidacją +11,3 %/rok [−5,3; +27,8], t 1,34 — NIEROZSTRZYGNIĘTY; 4,75 % pozycji-tygodni likwidowanych; opisowo 2× +13,2 %/rok. Walidacja: **READY** |
| **SZ1** | 2026-09-24 | [sz1-wielkosc-pozycji](2026-09-24_sz1-wielkosc-pozycji/README.md) | **Reguły wielkości pozycji (opisowo, 0 wariantów przewagi)** dla portfela trend (likwidacja 2×) + premia Coinbase (3×): R0 po połowie, R1 budżet ryzyka (1/σ, cel 20 %, sufit 2), R2 = R1 + hamulec 15 %/7,5 %; pre-rejestracja `a635c8c` | Korelacja składowych 0,30; **R0 +19,9 %/rok, obsunięcie 18,9 %; R1 +18,6 % / 17,7 %; R2 +10,3 % / 17,7 % (hamulec 36 % czasu — szkodzi)**; depozyt ~23 % kapitału. Składowe in-sample. Walidacja: **READY (Caveats)** |
| **SC1** | 2026-09-24 | [sc1-sila-sygnalu](2026-09-24_sc1-sila-sygnalu/README.md) | Wielkość pozycji ∝ sile sygnału (trend, premia Coinbase), ekspozycja wyrównana stałą z sygnałów; kryterium różnica parowana z wersją znakową (m = 2) | **NIEMIERZALNA — nie wystartowała (zasada 18):** half-width różnicy ±13,2 %/rok (trend), ±16,7 %/rok (Coinbase) wobec oczekiwanego efektu kilku %/rok. 0 wariantów |
| **NC1** | 2026-09-24 | [nc1-kontrola-negatywna](2026-09-24_nc1-kontrola-negatywna/README.md) | **Kontrola NEGATYWNA silników dziennych** (wytyczna SIGMA 2): TS1, X1, reguła znaku CP1 na 40 losowaniach danych bez informacji o przyszłości (t-Student df 3, GARCH, ρ 0,5, 20 monet × 2 000 dni) + kontrola czułości (celowe zajrzenie w przyszły tydzień); pre-rejestracja `433505a` | **0 — POZA licznikami** (kalibracja przyrządu) | **ZALICZONA:** brutto średnie t −0,12 / +0,17 / −0,20, fałszywe alarmy 4/120 = 3,3 % [1,3; 8,3]; netto ≤ brutto; czułość t +13…+30 w 40/40. Ogon X1 (dopisane po przebiegu): 20/400 = 5,00 % przy \|t\| > 1,96 — kalibracja poprawna. Walidacja: **READY** (niezależne przeliczenie X1, korelacja 0,998) |
| **CP2** | 2026-09-24 | [cp2-premia-coinbase-eth-sol](2026-09-24_cp2-premia-coinbase-eth-sol/README.md) | Replikacja CP1 na ETH i SOL (zasada 9: ta sama reguła, bez retuningu), m = 2, z 2,241; tylko rachunek mocy i profil danych | **0 — NIEMIERZALNA, nie wystartowała** | Half-width ±36,2 (ETH) / ±37,2 %/rok (SOL) > efekt CP1 (+32 %); moc 34–39 % przy efekcie CP1. Sygnał ETH = sygnał BTC w **94,4 %** dni, SOL w **89,3 %** (premia ETH/BTC skorelowana 0,95) — inne monety nie są niezależnym potwierdzeniem. Walidacja: **READY** (zgodność przeliczona niezależnie) |
| **SH1** | 2026-09-24 | [sh1-sonda-hipotez](2026-09-24_sh1-sonda-hipotez/README.md) | Sonda 15 nowych hipotez (popyt spoza Binance, makro, kalendarz, on-chain/uwaga), 10 zweryfikowanych przeciwniczo z pobraniem danych | **0 — POZA licznikami** | **0 kandydatów: 9 NIEMIERZALNYCH, 1 słaby mechanizm** (niepewność 2–5× większa od realistycznego efektu). Znalezisko: uniwersum obcięte → RU1. Walidacja: **Caveats** |
| **RU1** | 2026-09-24 | [ru1-pelne-uniwersum](2026-09-24_ru1-pelne-uniwersum/README.md) | **Korekta danych:** `data/raw/universe` miał 287 z 685 kontraktów (A–G + 12); pełne `universe_full`, reguły TS1/X1/SZ1 zamrożone co do bajtu; pre-rejestracja `d2316cc` | **0 — korekta danych** | Skład top-20 inny na 5,1/20 miejsc. **TS1 +11,1 %/rok [−4,2; +26,3] t 1,43 (było +14,8); X1 +41,7 %/rok t_neff 1,86 (było +22), z tego ~83 pkt z jednego zdarzenia (MYX), bez niego +26,3 %; SZ1 R1 +17,1 % / obs. 18,4 %.** Oba ślady odporne, oba NIEROZSTRZYGNIĘTE. Walidacja: **READY (Caveats)** — dziennik vs pełny backtest kor. 0,9990 |
| **RU2** | 2026-09-24 | [ru2-korekta-pozostalych](2026-09-24_ru2-korekta-pozostalych/README.md) | Korekta danych dla TR1, X2, LQ1, TF1, R1 (pełne uniwersum, reguły zamrożone); pre-rejestracja `1d00e7a` | **0 — korekta danych** | Wszystkie odporne, werdykty bez zmian: **TR1 +13,0 %/rok t 1,63; X2 +23,1 % t 1,60; koszt likwidacji 3× −2,4 %/rok; TF1 −1,3 pkt; R1 −10,6 %/rok.** TL1 nieprzeliczony (OI). Walidacja: **READY (Caveats)** |
| **TX1** | 2026-09-24 | [tx1-trend-inne-rynki](2026-09-24_tx1-trend-inne-rynki/README.md) | **ADR-09 szczebel 1(b):** reguła TS1 bez zmian na 19 rynkach FRED (13 walut, Brent, Nasdaq, Nikkei, obligacje USA) 1990–2026; pre-rejestracja `6532994`; moc 0,33 SR | **1 — seria TX 1/1, STOP** | **Kryterium POZYTYWNE: +5,1 %/rok [+1,4; +8,7], t 2,73; po 2013 −0,2 %/rok [−6,0; +5,6] (4/14 lat)** — wynik z lat 1990–2012; po 2013 ropa +23 %, akcje +8 %, waluty −3 %. Szczebel 1(b) NIEROZSTRZYGNIĘTY. Walidacja: **READY (Caveats)**, numpy 0,9996 |
| **WF1** | 2026-09-24 | [wf1-okno-uczenia](2026-09-24_wf1-okno-uczenia/README.md) | Okno uczenia modelu 4h: 60 (kontrola) / 365 / 730 dni, wspólne świece od 2023; decyzja użytkownika; pre-rejestracja `eb56d55` | **2 — seria WF 2/2, STOP** | **Oba NEGATYWNE:** 365 dni p 49,6 %, −0,061 %/tr., t −2,59; 730 dni p 48,5 %, −0,084 %, t −3,53 (kontrola 50,1 %). Dłuższa historia nie pomaga. Walidacja: **READY** |
| **AU1** | 2026-09-24 | [au1-audyt-metodologii](2026-09-24_au1-audyt-metodologii/README.md) | Audyt wieloagentowy: czy testy mogły ukryć przewagę (koszty, kryteria, dane, silnik, przyrząd Fazy 0), 12 weryfikacji przeciwniczych | **0 — przegląd** | **CZĘŚCIOWO:** obliczenia poprawne; model 60 dni gubi ~85 % słabej 5. cechy (F1/O1/L1/V1/G1 niezmierzone); TR1 od 2021-02 t 1,99 (po fakcie); „nierozstrzygnięty” = za mało lat (moc ~25 % przy +10 %/rok). Naprawiony `max(1, N_eff)`. Walidacja: **Caveats** |
| **RU3** | 2026-09-24 | [ru3-data-startu](2026-09-24_ru3-data-startu/README.md) | Korekta daty startu TR1 i X2 (2021-05 → 2021-02, pełne uniwersum; X2 jako średnia 7 faz); pre-rejestracja `e4c2350`; wynik znany z AU1 | **0 — korekta danych** | **TR1 +15,5 %/rok [+0,2; +30,8], t 1,99 — formalnie POZYTYWNY, ale znany z góry, poniżej progu rodzinnego ~2,9, a cały przyrost to 82 dni hossy 02–04.2021 (od 2022: +11,4 %, t 1,32). X2 +21,9 % t 1,59 — NIEROZSTRZYGNIĘTY** (fazy 12–39 %/rok). Walidacja: **Caveats** (RU2 odtworzone co do 1e-17) |
| **X1F** | 2026-09-24 | [x1f-siedem-faz](2026-09-24_x1f-siedem-faz/README.md) | X1 (momentum przekrojowe top-20) jako średnia 7 faz (dni startu tygodnia) + X1 w dzienniku papierowym od 2026-09-25 (poprawka 3) + poprawka filtra nazw dziennika (poprawka 4) | **0 — zapis porządkowy** | **X1 7 faz: +9,5 %/rok [−21,1; +40,1], t 0,61 — dawne +41,7 % (t 1,86) to najlepsza z 7 faz (poniedziałek); pozostałe od −1,3 do +21,6. Kandydat skreślony na historii.** MYX: long w 1 fazie, short w 5 (−44 pkt średniej). Dziennik vs backtest X1: kor. 0,9875 → 0,9986 po poprawce filtra (币安人生USDT). Walidacja: **Caveats** |
| **SW** | 2026-09-24 | [sw-cechy-spoza-wykresu](2026-09-24_sw-cechy-spoza-wykresu/README.md) | **NOWA SERIA SW:** 8 cech spoza wykresu (funding, OI, L/S dużych graczy i wszystkich kont, przewaga kupujących, VRP, podaż na giełdach, F&G) — etap 1: każda jako reguła „za/przeciw odchyleniu od mediany 365 dni” (kierunek z mechanizmu); etap 2: jeden XGBoost na 7 cechach, okno 365 dni (wyjątek od zasady 4, decyzja użytkownika); pre-rejestracja `e03cfa4` | **9/9 — seria zamknięta (STOP)**, z\* 2,773 | **Wszystkie 8 reguł tracą po kosztach (−0,03 … −0,11 %/tr; 4 NEGATYWNE, 4 NIEROZSTRZ.); model −0,050 % [−0,091; −0,010], t −1,78 — NIEROZSTRZ. Duża przewaga (≥ +0,06 %/tr) wykluczona.** Przed kosztami +0,02 … +0,05 %/tr (L/S kont +0,054 [+0,023; +0,085]) — 2–3× mniej niż koszt 0,08 %. Walidacja: **Ready** (IC niezależne od silnika zgodne) |
| **KP1** | 2026-09-25 | [kp1-premia-koreanska](2026-09-25_kp1-premia-koreanska/README.md) | Premia koreańska (Upbit KRW-BTC ÷ spot Binance × USD/KRW `DEXKOUS`) w regule CP1 (7 vs 90 dni, silnik TS1) — wariant serii CP pod STOP-em, więc tylko profil, zgodność z CP1 i rachunek mocy; założony efekt SR 0,15 z przeglądu badań (30 źródeł zweryfikowanych); pre-rejestracja `d909076` | **0 — NIEMIERZALNA, nie wystartowała** | **Half-width ±30,9 %/rok (0,86 SR); moc 5 % przy SR 0,15, 53 % nawet przy efekcie CP1.** Zgodność znaku z CP1 52,8 % [~46; 60] (przypadek 50,1 %) — sygnał inny niż CP1, z trendem 28 dni 45,9 %. Od 2024-06 premia BTC ≈ premia USDT (napływ wonów). Kierunek odwrotny spalony (kontaminacja w przeglądzie badań). Walidacja: **Caveats** (liczby odtworzone niezależnie) |
| **AU2** (krok 0) | 2026-09-25 | [au2-moc-przekrojowa](2026-09-25_au2-moc-przekrojowa/README.md) | Kalibracja przyrządu przekrojowego (projekt użytkownika): szerokość efektywna top-20/50/100 z rozkładu własnego korelacji + szum rank IC z 200 losowych sygnałów AR(1) na prawdziwych zwrotach 7-dniowych (7 faz) + prawo fundamentalne; reguła: IC* ≥ 0,10 zamyka ML przekrojowe, ≤ 0,05 → karta kroków 1–2; pre-rejestracja `f5f269d` | **0 — kalibracja, POZA licznikami** | **Top-50 po odjęciu rynku ≈ 17,7 niezależnych zakładów (surowo 3,2); najmniejsze wykrywalne IC 0,022 (moc 80 %), na IR 0,75 trzeba IC 0,025 brutto → IC\* 0,025: ML przekrojowe NIE wykluczone przez przyrząd; kroki 1–2 = szkic karty, 3 decyzje użytkownika.** Top-20: szerokość 8,6, MDE 0,040. H0 wycentrowane, sd IC = 1/√(N−1). Walidacja: **Ready** |
| **AU2** (kroki 1–2) | 2026-09-25 | [au2-kroki-1-2](2026-09-25_au2-kroki-1-2/README.md) | Kalibracja ML przekrojowego (decyzje użytkownika: cechy A, budżet 8×3, drugi warunek ci_low(IC) > 0): walk-forward kwartalny z purgingiem/embargo; ramię negatywne (cel permutowany, S = 40), siatka sił +5…+30 %/rok przez nośnik (S = 20); obok ranking po nośniku bez ML; pre-rejestracja `91cbfae`, odstępstwo `eca7ad8` | **0 — kalibracja, POZA licznikami** | **Negatywne 0/40 [0; 9 %]; moc ML 0/25/35/80/100 % vs ranking po cesze 10/80/85/95/100 % → przeszukiwanie kosztuje ~2/3 mocy; ML nie lepszy niż AU1 → ML przekrojowe NIE startuje.** Znalezisko: błąd kanonicznego N_eff (mianownik 1+2Σρ < 0 → N_eff = 1 / NaN) — decyzja użytkownika. Walidacja: **Caveats** |
| **AU3** | 2026-09-25 | [au3-audyt-neff](2026-09-25_au3-audyt-neff/README.md) | Naprawa kanonicznego N_eff (`effective_sample_size`: mianownik 1+2Σρ ≤ 0 → N_eff = n; decyzja użytkownika) + audyt 59 przebiegów zamrożonych rund (licznik zdarzeń old/new w osobnej kopii roboczej, `tools/au3_audit.py`); pre-rejestracja `d7e321a` | **0 — audyt, POZA licznikami** | **0 zmienionych werdyktów.** Zdarzenia tylko w K2 (19/99) i K3 (1/4), wydruki przed/po identyczne. Rundy od W2 odtwarzają się na serwerze 100 % (A1/A2/W1/N1/T4 96–99 %); Faza 0 sprzed W2 — nie (filtr danych od 2021). Poprawka 6 dziennika (bez wpływu). Walidacja: **Ready** |
| **KR1** | 2026-09-25 | [kr1-korelacje-nog](2026-09-25_kr1-korelacje-nog/README.md) | Korelacje nóg portfela TS1 / X1 (7 faz) / CP1 na wspólnym oknie (te same funkcje co RU1/X1F/CP1), dziennie, tygodniowo, w złych dniach TS1; dywersyfikacja 1/σ; reguła 0,3/0,5 z góry | **0 — opisowo** | **TS1–X1 tyg. 0,35 (0,28–0,39) → częściowa; TS1–CP1 0,24, X1–CP1 0,16 → znaczna; w 10 % najgorszych dni TS1 korelacje spadają (0,24 / 0,09 / 0,04).** Dywersyfikacja portfela 0,80 → 0,71 z X1. Walidacja: **Ready** |
| **AU4** | 2026-09-25 | [au4-dsr-cp1](2026-09-25_au4-dsr-cp1/README.md) | Deflated Sharpe CP1 (Bailey & LdP 2014): N odczytów zysku z liczników INDEX (28 w chwili CP1, 40 dziś), siatka N 5–40, poprawka na skośność/kurtozę; pre-rejestracja z regułą 0,95/0,80 | **0 — audyt** | **DSR 0,52 przy N = 28 (0,46 przy 40, 0,82 przy 5) → CP1 po korekcie nieodróżnialny od najlepszego z pustych pomysłów;** przy 28 pustych najlepszy ma t ≥ 2,09 w 40 % (symulacja = wzór). Walidacja: **Ready** |
| **RU4** | 2026-09-25 | [ru4-tl1-pelne-oi](2026-09-25_ru4-tl1-pelne-oi/README.md) | Korekta danych TL1: pełne uniwersum (RU1) + pełny panel OI (`oi_daily_full`, 10 838 dni dociągniętych), zamrożony `run_crowding_tl1` z podmienionymi ścieżkami | **0 — korekta danych** | **TL1: +8,1 %/rok [−17,5; +33,7], t 0,62 (było −10,5 %, t −1,39) — NIEROZSTRZYGNIĘTY bez zmian;** znak odwrócony, 7 faz −44 … +35 %/rok. Zastrzeżenie: H0 TL1 ma 6× niższą zmienność niż strategia. Walidacja: **Caveats** |
| **P4** | 2026-09-25 | [p4-pokrycie-onchain](2026-09-25_p4-pokrycie-onchain/README.md) | Brama danych on-chain: pokrycie katalogu CoinMetrics community (przepływy/podaż na giełdach, adresy, MVRV, transakcje) dla koszyków top-20/top-50 point-in-time | **0 — brama danych** | **Przepływy i podaż na giełdach: tylko BTC i ETH (4–10 % koszyka); adresy/MVRV/transakcje 34–46 % i spada — ranking on-chain na darmowych danych niewykonalny.** Brakuje SOL, AVAX, PEPE, SUI, MATIC… Płatni dostawcy — do sprawdzenia przez użytkownika. |
| **KO1** | 2026-09-25 | [ko1-koszty-wykonania](2026-09-25_ko1-koszty-wykonania/README.md) | Koszty wykonania nóg dziennika (TS1, X1 7 faz, CP1): ten sam silnik, stawka taker 0,07 % vs maker 90 %/100 % wypełnień | **0 — opisowo** | **Koszt taker: TS1 0,8 %/rok, CP1 1,5 %, X1 3,3 %; limity oddałyby +0,5 / +1,0 / +2,2 pkt/rok (przed niekorzystną selekcją).** Koszty nie są wąskim gardłem trendu ani CP1. |
| **KR2** | 2026-09-25 | [kr2-korelacje-tradfi](2026-09-25_kr2-korelacje-tradfi/README.md) | Korelacje tygodniowe BTC/ETH i nóg dziennika z S&P 500, Nasdaq, Nikkei, złotem (PAXG), ropą, dolarem, rentownościami USA, VIX | **0 — opisowo** | **BTC–Nasdaq 0,30 (2-tyg. 0,43), rośnie: 2026 0,58; z dolarem −0,16, VIX −0,22; złoto/ropa/stopy ≈ 0. Nogi dziennika niezależne od tradfi (|ρ| ≤ 0,15; trend −0,15 do akcji).** |
| **PR1** | 2026-09-25 | [pr1-portfel](2026-09-25_pr1-portfel/README.md) | Reguły portfela nóg dziennika pod szczebel 4 ADR-09: R0 równo / R1 dziennik (1/σ) / ERC (równy wkład ryzyka z korelacjami) dla {TS1, CP1} i {TS1, CP1, X1}; ES95 tyg., ES99 dz., obsunięcia, depozyt, przełożenie na 5 % depozytu; pre-rejestracja `7f647f2` | **0 — opisowo** | **2 nogi: ERC ≡ 1/σ (\|Δk\| 0,0000) — dziennik bez zmian. R1: +18,3 %/rok, obsunięcie 18,2 %, najg. tydzień −9,7 %, ES95 tyg. −5,7 % [−6,5; −4,7]; przy 5 % depozytu (limit trzymany każdego dnia) strategia ≈ 10 % kapitału → obsunięcie ≈ 1,9 %, zły tydzień ≈ −1 % całego kapitału. X1 jako 3. noga: obsunięcie 28 %, tydzień −27,5 % (jedno zdarzenie).** Nogi in-sample, bez modelu likwidacji. Walidacja: **Ready (Caveats)** — depozyt realny (druga droga) mediana 24 %, max 45 %; 4 liczby zgodne |
| **LK0** | 2026-09-25 | [lk0-kolektor-likwidacji](2026-09-25_lk0-kolektor-likwidacji/README.md) | Kolektor likwidacji Binance USDT-M (strumień `!forceOrder@arr`, próbkowany ≤ 1 zdarzenie/s/symbol) od 2026-09-25 do `$HOME/likwidacje` (poza repo) — brama danych rodziny E1; decyzja użytkownika („kolektor tak”) | **0 — POZA licznikami** (zbieranie danych, 0 odczytów) | **Uruchomiony. Dokumentowany adres `/ws/` odpowiada, ale milczy; nadaje `/market/ws/` (jak ccxt 4.5.48). Próba 90 s: 56 zdarzeń, 29 symboli (w tym XAUUSDT, jeden symbol COIN-M), ≈ 3,7 mln USD nominału; `ps`/`st` wewnątrz `o`.** Odczyt E1 najwcześniej po ~roku (rachunek mocy z realnej częstości PRZED). Przegląd bezpieczeństwa: 0 podatności, 2 uwagi niskie wdrożone. Walidacja: n/d (bez wyniku) |
| **HC1** | 2026-09-24 | [hc1-cykl-halvingowy](2026-09-24_hc1-cykl-halvingowy/README.md) | Opis cyklu halvingowego BTC (FRED CBBTCUSD od 2015-03, 3–4 cykle), fazy 0–48 mies., trend TS1 na BTC per faza; decyzja użytkownika | **0 — opisowo** | 0–18 mies.: BTC dodatni 9/9; 18–24 mies.: 0/3 (−31…−59 %); 24–30 mies.: 1/4, trend 0/4. Dziś 29 mies. po halvingu 2024. Opis, nie dowód. Walidacja: **READY (Caveats)** |

## Liczniki budżetu multiple-testing (per baza danych / per hipoteza)

- **Stara baza (2025-07→2026-07 BTC 5m), hipoteza dwureżimowa: 7 wariantów**
  (4 progi C2.5 + 2 timeframe'y C2.6 + 1 cecha C2.8), plus 34 obejrzane korelacje opisowe
  (C2.7). Wyniki C6–C2.9 zamrożone na tym oknie — nieporównywalne 1:1 z nową bazą.
- **Nowa baza (2023-07→2026-07 BTC 5m, od C2.10), hipoteza dwureżimowa: 2 warianty**
  (C2.12 model kosztów + C2.13 próg pewności). C2.10/C2.11 i Z16–Z21/Z9/Z19 to 0 wariantów
  (baza/instrumentacja/pomiar/naprawa/walidacja/wykonalność/dane).
- **Nowa hipoteza — architektura jednoreżimowa 4h (Z5b → S1): 1/1 — ZUŻYTY, seria
  ZAMKNIĘTA.** NOWA hipoteza wobec dwureżimowej z docs/rag/01, więc własny licznik. Wynik S1
  negatywny ⇒ **reguła STOP uruchomiona** — żadnych kolejnych wariantów w tej serii.
  **Korekta po S1b:** werdykt S1 zapadł na pipelinie z martwym early stoppingiem; po jego
  naprawie pomiar jest NIEROZSTRZYGALNY (n=345 < 925), a konfiguracja okazuje się
  **nietestowalna** przy dostępnej historii (brakuje 11,4 lat). Reguła STOP pozostaje
  aktywna — to doprecyzowanie, czego NIE wykazano, nie zaproszenie do kolejnych prób.

- **NOWA HIPOTEZA M — momentum bez bramki rezimu (od M1, 2026-09-22): 1/1 ZUZYTY — SERIA ZAMKNIETA REGULA STOP.** Licznik startowal OD ZERA i nie dziedziczy niczego po Fazie 0 ani po H2. M1 zuzyl jedyny wariant i wyszedl **NEGATYWNY** (ci_high 50,80% < prog 52,94% przy n = 8 512, 1,90x wymaganej proby). Ramie A (reversion) liczone za **0 wariantow** — to samo uzasadnienie co w H2.1: prog oplacalnosci pochodzi z geometrii kosztu, a nie z obejrzanej trafnosci, wiec pomiar odniesienia nie moze przesunac poprzeczki.
- **NOWA HIPOTEZA F — funding jako cecha, zmierzony (od F1, 2026-09-22): 1/1 ZUZYTY — SERIA ZAMKNIETA REGULA STOP.** Licznik od zera; H2 pozostaje zamkniete i NIE zostalo wznowione. F1 wyszedl **NEGATYWNY** (ci_high 51,43% < prog 52,94%, n = 8 127 = 1,81x wymaganej proby). Ramie A liczone za **0 wariantow** — to samo uzasadnienie co w H2.1 i M1.
- **Diagnostyka wykonalnosci zrodel (P1) — POZA licznikami: 0 wariantow.** Odczyt API, zero spojrzen na target.
- **NOWA SERIA TL — tłok przekrojowy (od TL1, 2026-09-24): 1/1 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** Zakazane: inne okna/nogi, odwrócenie znaku (post hoc).
- **SERIA TS — uzupełnienie (TR1/TP1, 2026-09-24, decyzja użytkownika): 2/2 ZUŻYTE — zamknięta na historii.** Dalej tylko dziennik prospektywny tej samej reguły (0 wariantów).
- **NOWA SERIA TF — trend z filtrem tłoku (od TF1, 2026-09-24): 1/1 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** Zakazane: inne progi/okna fundingu, OI jako filtr trendu bez nowego mechanizmu.
- **NOWA SERIA CP — premia Coinbase (od CP1, 2026-09-24): 1/1 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** Zakazane: inne okna, progi, giełdy na tych samych danych. Dozwolone bez nowego licznika: ta sama reguła poza próbą (dane od 2026-07-01, prospektywnie). CP2 (ETH/SOL, 2026-09-24): NIEMIERZALNA, 0 wariantów, 0 odczytów wyniku. KP1 (premia koreańska = „inna giełda”, 2026-09-25): NIEMIERZALNA, 0 wariantów, 0 odczytów wyniku; kierunek odwrotny spalony.
- **NOWA SERIA NL — nowe listingi (od NL1, 2026-09-24): 1/1 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** Własny licznik (rodzina G2, zbiór informacyjny: kalendarz zdarzeń). Zakazane bez decyzji użytkownika: inne okna/opóźnienia, filtry listingów, stop-loss na wystrzał (inny rozkład wypłat = nowa hipoteza), long po listingu (post hoc).
- **NOWA SERIA WF — okno uczenia modelu 4h (WF1, 2026-09-24, decyzja użytkownika): 2/2 ZUŻYTE — STOP.** Oba NEGATYWNE.
- **NOWA SERIA TX — trend TS1 na rynkach spoza krypto (TX1, 2026-09-24, ADR-09): 1/1 ZUŻYTE — STOP.** Zakazane: dobór rynków lub okresów po wyniku (np. „tylko ropa i akcje”).
- **NOWA SERIA SW — cechy spoza wykresu (od SW, 2026-09-24): 9/9 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** 8 reguł + 1 model, Bonferroni m = 9 (z\* 2,773). Zakazane na tej historii: inne okna mediany, progi skrajności, kombinacje cech w regułach, podzbiory lat, odwrócone kierunki. Wolniejszy horyzont = NOWA hipoteza (decyzja użytkownika).
- **NOWA SERIA TS — momentum w czasie na koszyku (od TS1, 2026-09-24): 1/1 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** Własny licznik (rodzina A1 katalogu na horyzoncie tygodniowym, uniwersum wielu monet; nie B1). Zakazane bez decyzji użytkownika: inne okna, cele zmienności, uniwersa (top-50), sam BTC, łączenie z X1 — każdy kolejny odczyt na tej samej historii zwiększa szansę przypadkowego sukcesu. Rozstrzygnąć może tylko test prospektywny.
- **NOWE BAZY Y1 (1h) / Y2 (1d) — model kontrolny na innych interwałach (od Y1/Y2, 2026-09-23, decyzja użytkownika): każda 1/1 ZUŻYTE — OBIE ZAMKNIĘTE REGUŁĄ STOP.** Osobne liczniki per baza (wytyczna o bazach); wyników nie porównuje się 1:1 z 4h. Y1 NEGATYWNY (48,3 %, n 23 334), Y2 NIEROZSTRZYGNIĘTY (50,2 %, n 978). Zakazane bez decyzji użytkownika: inne V/bariery/okna na 1h i 1d, filtry godzin/dni, odwrócenie znaku na 1h (hipoteza post hoc, wniosek 49).
- **NOWA SERIA X2 — momentum przekrojowe na top-50 (od X2, 2026-09-23, decyzja użytkownika): 1/1 ZUŻYTE — ZAMKNIĘTA REGUŁĄ STOP.** Rodzina B1 ma teraz DWA odczyty (X1 top-20, X2 top-50) — raportowane obok siebie, bez sumowania i wyboru; trzeci odczyt na tych danych zakazany; pozostaje wyłącznie pomiar prospektywny z regułą zamrożoną.
- **NOWE SERIE L / V / G — cechy dzienne spoza OHLCV jako 5. cecha modelu 4h (L1 on-chain, V1 DVOL/VRP, G1 Fear & Greed; 2026-09-23): każda 1/1 ZUŻYTE — ZAMKNIĘTE REGUŁĄ STOP.** Pre-rejestrowane razem (jeden commit, bez dobierania po wyniku poprzedniej). Zakazane bez decyzji użytkownika: inne metryki CoinMetrics, inne okna, poziom/zmiana DVOL, skew, VRP jako target, zmiany F&G, progi skrajności, inne horyzonty.
- **NOWA SERIA O — pozycjonowanie jako cecha modelu 4h (od O1, 2026-09-23): 1/1 ZUŻYTE — SERIA ZAMKNIĘTA REGUŁĄ STOP.** Zakazane bez decyzji użytkownika: pozostałe kolumny archiwum (top-trader L/S konta/pozycje, global L/S, taker ratio, OI w USD), inne okna (8h/72h), reguły z progiem na OI, inne bazy (1h/5m). Kolejna kolumna = kolejny wariant tej samej rodziny.
- **NOWA SERIA X — momentum przekrojowe, rodzina B1 (od X1, 2026-09-23): 1/1 ZUŻYTE — SERIA ZAMKNIĘTA REGUŁĄ STOP.** Zakazane bez decyzji użytkownika: inne okna sygnału, trzymanie, kwantyle, N, wagi, long-only, inne uniwersum (families.md B1: warianty tej samej rodziny). Rozstrzygnięcie tylko przez WIĘKSZĄ PRÓBĘ (szerokość top-50 = nowa pre-rejestracja; czas = pomiar prospektywny), nie przez wariant.
- **Analiza produktu carry (D1, 2026-09-23) — POZA licznikami: 0 wariantów reguł.** Siatka depozytu = zakres inżynierski (raportowany w całości); COIN-M i basis kwartalny = ta sama reguła „zawsze w pozycji" na innym instrumencie (generalizacja C1a, jak zasada 9), nie warianty serii C (STOP dla reguł bez zmian).
- **Sonda źródeł II + podłączenie (P3, 2026-09-23) — POZA licznikami: 0 wariantów.** Pobranie i profil 13 zbiorów, zero korelacji ze zwrotem. Każda hipoteza na nowych danych (O1 pozycjonowanie, VRP z DVOL, on-chain, F&G, premia Coinbase, basis/COIN-M) = NOWA SERIA z własnym licznikiem.
- **Sonda wykonalnosci carry przekrojowego (P2) — POZA licznikami: 0 wariantow.** Liczy tylko mechanizm (funding − koszt) i rozrzut do rachunku mocy; srednia zwrotu z cen i P&L NIE policzone. Werdykt NIEMIERZALNA ⇒ hipoteza C (carry przekrojowy na perpetualach) NIE dostaje licznika.
- **Kalibracja przyrzadu (Z9, Z19, K1, K2, K3, T4, NC1, AU2 kroki 0–2, AU3, AU4) — POZA licznikami hipotez: 0 wariantow.** Korekta danych RU1/RU2/RU3, zapis porządkowy X1F (2026-09-24) i sonda SH1 — również 0 wariantów. Te rundy nie testuja zadnej hipotezy rynkowej: mierza, czy aparat pomiarowy dziala. `oracle` ma sile sygnalu ZNANA Z KONSTRUKCJI, wiec nie ma czego p-hackowac. **Warunek utrzymania zera, zapisany w pre-rejestracji K2: zadna liczba z K1/K2 nie moze byc cytowana jako wynik hipotezy tradingowej.**
- **Model kosztow / wykonanie — POZA licznikami hipotez: 0 wariantow.** C2.12 policzono jako **1 wariant**, bo raportowal werdykt klasyfikacyjny na tych samych danych. H3 **nie** — pre-rejestracja (regula D5) zakazala raportowania trafnosci, CI, z_stat, marginesu i klasyfikacji jako wyniku; liczby te sa w `raw_output.txt` z jawna adnotacja, ze nie uczestnicza w decyzji. Uzasadnienie mechaniczne: koszt moze ruszyc trafnosc WYLACZNIE przez selekcje (inny moment kill-switcha), czyli bylby to szum selekcyjny.
- **NOWA SERIA W — wykonanie po konkretnej cenie (od W1, 2026-09-23): 3/3 ZUŻYTE — SERIA ZAMKNIĘTA REGUŁĄ STOP.** Licznik od zera (decyzja użytkownika: zasada obowiązująca też na żywo). Trzy reguły wejścia z werdyktem na tych samych danych = 3 warianty (precedens C2.12). Kontrola w trybie `label` za **0** (odtworzyła ramię A z M1/F1 co do sztuki), część kalibracyjna 5m vs 4h i wrażliwość na czas ważności k = 2, 3 za **0** (bez werdyktów, reguła H3/D5). Wynik: W1a NEGATYWNY, W1b NIEROZSTRZYGNIĘTY wg kryterium trafności przy istotnie ujemnym zwrocie netto (t = −3,90), W1c NEGATYWNY. Żadnej kolejnej reguły wejścia, cofnięcia ani czasu ważności.
- **NOWA BAZA DANYCH od N1 (2026-09-23): 2021-01-01 → 2026-06-30 (CLAUDE.md zasada 20).** Wszystkie liczniki poniżej i wyżej dotyczą baz WCZEŚNIEJSZYCH; wyniki na nowej bazie (od N1) nie porównują się 1:1 z żadną wcześniejszą rundą. Kontrola N1 na nowej bazie: p 49,58 % [48,39; 50,77], zwrot netto −0,107 % — liczby odniesienia dla przyszłych rund (0 wariantów).
- **NOWA SERIA N — nowy cel modelu (od N1, 2026-09-23): 1/1 ZUŻYTY — SERIA ZAMKNIĘTA REGUŁĄ STOP.** Jeden wariant (schemat użytkownika), kontrola za 0. Wynik NEGATYWNY na zwrocie netto; trafność 53,3 % to iluzja geometrii (p\* 57,2 %). Żadnego innego poziomu celu, udziału, trailing stopu ani limitu czasu.
- **NOWA SERIA R — premia rebalansowa koszyka (od R1, 2026-09-23): 1/1 ZUŻYTE — SERIA ZAMKNIĘTA REGUŁĄ STOP.** Zakazane: inne N, lookback, częstość rebalansu (tygodniowa, progowa), wagi kapitalizacyjne, filtry składu („blue chip"), inne opłaty. Momentum przekrojowe (B1) jako hipoteza odwrotna = nowa pre-rejestracja z decyzją użytkownika (wniosek 49), nie wariant.
- **NOWA SERIA C — cash-and-carry z hedgem spot (od C1, 2026-09-23): 2/2 ZUŻYTE — SERIA ZAMKNIĘTA REGUŁĄ STOP.** C1a (zawsze w pozycji) POZYTYWNY, C1b (przełączanie) NEGATYWNY. Zakazane warianty pomiarowe: progi na stawkę, histereza, inne interwały rebalansu, zniżki opłat, noga maker, inne monety. Pozytyw C1a otwiera DECYZJĘ UŻYTKOWNIKA o produkcie (zarządzanie depozytem, ryzyko giełdy, porównanie z lokatą USD) — inżynieria, nie kolejna runda pomiarowa.
- **SERIA A PO A2 (2026-09-23): 7/7 ZUŻYTE — WSZYSTKIE RODZINY AT ZE SKILLA `ta-toolkit` ZAMKNIĘTE REGUŁĄ STOP.** A1 formacje świecowe (2), A2 struktura trendu, Fibonacci, wsparcie/opór, grupa zdarzeń (wybicie, podwójny szczyt/dno, RGR, przecięcie EMA, linia trendu), model + 10 cech AT (5). Zakazane: inne parametry (okna, `τ`, `lookback`, `confirm`, tolerancje, pasma), podzbiory grupy zdarzeń, filtry kontekstu, odwrócenie znaku. Pięć reguł zdarzeniowych osobno NIE zostało zmierzonych (niemierzalne na 5,5 roku 4h) — nie wracają na BTC 4h; inny interwał = nowa hipoteza z decyzją użytkownika. Analiza techniczna na BTC 4h zamknięta jako kierunek.
- **NOWA SERIA A — analiza techniczna, rodzina FORMACJE ŚWIECOWE (od A1, 2026-09-23): 2/2 ZUŻYTE — RODZINA ZAMKNIĘTA REGUŁĄ STOP.** A1a (reguła) i A1b (cecha), kontrola za 0. Oba NEGATYWNE; reguła trafia istotnie PONIŻEJ 50 %. Zakazane: podzbiory formacji, wagi, progi na |score|, pozostałe 55 formacji TA-Lib, filtry kontekstu, odwrócenie znaku (nowa hipoteza post hoc — wniosek 49). **Inne rodziny AT ze skilla `ta-toolkit`** (wsparcie/opór, wybicie, struktura trendu, podwójny szczyt, średnie, linia trendu, Fibonacci) NIE są objęte tym STOP-em, ale każda = osobna pre-rejestracja z rachunkiem mocy i decyzja użytkownika; prior dla wszystkich ten sam (transformacja OHLCV).
- **NOWA HIPOTEZA H2 — funding rate (od H2.0, decyzja użytkownika 2026-09-22): 1/1 ZUŻYTY — SERIA ZAMKNIĘTA REGUŁĄ STOP.** Licznik startował OD ZERA i nie dziedziczy niczego po Fazie 0. H2.0 to **0 wariantów** (wykonalność, zero spojrzeń na target). **H2.1 zużył ten wariant i wyszedł NIEROZSTRZYGNIĘTY** (`n = 98 < 1 000`) — wariant jest zużyty niezależnie od tego, bo porównanie wykonano na tych danych. Reguła STOP zamyka serię: żadnego drugiego `V`, interwału ani wariantu cechy.

> **ZAMKNIĘCIE FAZY 0 (Z10, decyzja użytkownika 2026-09-22).** Suma budżetu zużytego w Fazie 0:
> **10 wariantów** (7 + 2 + 1). Oba liczniki są **ZAMKNIĘTE NA STAŁE** — żadna przyszła runda
> nie dopisuje się do nich ani ich nie wznawia. Nowa hipoteza (H2) zakłada **osobny licznik
> od zera** i nie dziedziczy niczego po powyższych: ani budżetu, ani progów, ani kryteriów.

## Wnioski skumulowane (stan wiedzy — aktualizowany po KAŻDEJ rundzie)

> Czytane PRZED projektowaniem każdej nowej rundy (CLAUDE.md zasada 14). Każdy punkt ma źródło
> w konkretnym runie — nie powtarzaj przetestowanych wariantów.

1. **Hipoteza dwureżimowa (trend/range, 5m) jest po serii C2.5–C2.13 wyczerpana jako kierunek.**
   NO-GO na starej bazie (5 niezależnych testów, odporne na fold-jitter — C2.9) i na nowej,
   3-letniej bazie (C2.10, pooled t: range −10,47 / trend −5,51). Reguła STOP programu
   „droga do GO" uruchomiona po sfalsyfikowaniu progu pewności (C2.13).
2. **Blokada leży w geometrii wypłaty, nie w kierunku sygnału** (C2.11): trafność ~50–52%
   (po naprawie przecieku early stopping: **50,38%** w `range` — najczystszy pomiar, Z17+Z21)
   wobec wymaganych 75,8%/64,9% na 5m. **SPROSTOWANE (walidacja S1, 2026-09-22):** wcześniejsze
   brzmienie „edge nie istnieje w ŻADNEJ składowej (Z18)" było **za mocne** — opierało się na
   `hit_rate_barrier`, mierze **tautologicznej** (cena wyjścia dla `tp`/`sl` jest rekonstruowana
   z tej samej etykiety, która nadaje typ wyjścia, więc `hit_rate_barrier` ≡ udział `tp`).
   Niezależną informację niosą **wyłącznie timeouty**: 46,71% na 608 transakcjach (S1),
   49,38% na 804 (C2.12/5m). Brak edge'u jest więc udokumentowany na timeoutach i na
   trafności łącznej — nie na barierach.
3. **Reżim `trend` jest strukturalnie niespójny z horyzontem etykiety** (Z16): mediana epizodu
   2 świece vs horyzont 12; żadna bariera tego nie naprawia (`2p−1<0`). `range` daje się
   uspójnić wygładzaniem. To zamyka Z7 (reguła reżimu dla `trend`) jako kierunek na 5m.
4. **Koszty: model maker/taker (C2.12) domknął ~połowę luki** (koszt −52%, margines
   −23,9→−15,5 pp w `range`) — mechanizm potwierdzony, ale niewystarczający. Tańszy koszt
   wpuszcza węższe bariery (sprzężenie), więc zysk progu jest mniejszy niż liniowy.
5. **Grubszy interwał obniża próg opłacalności bez dotykania `p`** (Z9): próg `range`
   82,81% (5m) → 56,77% (1h) → 52,74% (4h, skorygowane w Z5b na 54,60% po uwzględnieniu
   timeoutów przy V=3). Ta ścieżka została rozstrzygnięta w S1 — mechanizm potwierdzony
   (bramka kosztowa odrzuca 0% sygnałów na 4h), ale edge'u to nie ujawniło.
6. **Rachunek mocy PRZED eksperymentem jest obowiązkowy** (Z19: rekomendacja Z9 obalona zanim
   kosztowała rundę; Z5b: dane 6,8 roku 4h czynią konfigurację wykonalną, margines mocy 4,3×).
7. **Pomiar:** per-fold `mean_sharpe` nie jest nośną statystyką (C2.12, σ→75,7); nośne są
   pooled t/t_neff i margines `(2p−1)·B−C` z z_margin. Seed-sweep nic nie mierzy (C2.9).
   Resample z 5m psuje wolumen → do eksperymentów per interwał używać danych natywnych (Z9).
   Early stopping bez wydzielonej walidacji zawyżał `p` (Z17) — naprawione, z embargo (Z21).
8. **Definicja kanoniczna trafności:** `p` = udział transakcji z `gross_pnl>0` (Z18).
9. **Hipoteza jednoreżimowa 4h ODRZUCONA rozstrzygająco (S1):** po usunięciu WSZYSTKICH
   znanych wad pomiaru naraz (przeciek ES, embargo, spójność bramka↔horyzont, natywne dane,
   geometria bariera-vs-koszt, moc statystyczna, patologia per-fold Sharpe) trafność =
   **48,60%**, CI [45,56%; 51,64%] — górny kraniec poniżej progu 53,07%. Każda kolejna
   naprawa pomiaru zostawiała `p` niezmienione albo gorsze — ani razu lepsze: spójny obraz
   braku sygnału kierunkowego. Reguła STOP uruchomiona (licznik 1/1).
10. **FAZA 0 ZAMKNIĘTA wynikiem negatywnym — decyzja użytkownika 2026-09-22 (Z10).**
   Liczba zamykająca, policzona od zera ze źródeł: pooled `p` = **50,27%** (n=7 687,
   CI95 [49,15%; 51,38%], z=+0,47) na trzech najczystszych pomiarach projektu. **Górny kraniec
   CI leży 1,30 pp poniżej najniższego progu opłacalności (52,69%), przy mocy 2,8× wymaganej
   próby** — to **dowód braku**, nie brak dowodu. Obie architektury (dwureżimowa 5m/1h/4h
   i jednoreżimowa 4h) zamknięte na stałe; obie reguły STOP pozostają aktywne.
11. **Wąskie gardło Fazy 0 było INFORMACYJNE, nie inżynieryjne** (Z10). Projekt naprawił po
   kolei geometrię wypłaty, model kosztów, spójność bramki z horyzontem, jakość danych,
   przeciek w treningu i metodologię pomiaru — po każdej naprawie `p` zostawało przy 50%.
   **Wszystkie 10 cech to transformacje ceny i wolumenu**; projekt nigdy nie sprawdził innego
   zbioru informacyjnego. To kieruje H2: zmianą zdolną ruszyć `p` jest **nowy zbiór
   informacyjny**, nie kolejna transformacja OHLCV ani nowa architektura nad tymi samymi cechami.
12. **Czego Faza 0 NIE wykazała** (Z10, lista jawna — nie wolno cytować zamknięcia jako
   dowodu w tych sprawach): **momentum** (próba zagłodzona przez samą bramkę: 0,53% świec,
   0,49% z etykietą wewnątrz reżimu — niewykonalność pomiaru, nie brak edge'u),
   **konfiguracja 4h po naprawie** (nietestowalna, brak 11,4 lat danych), **ETH/SOL/BNB**
   (zero testów), **funding rate jako sygnał** (nigdy nie zaimplementowany — tylko stała
   kosztowa), **ekonomia dźwigni/sizingu**, **target inny niż kierunek**.
13. **NOWE hipotezy startują od zera:** własna pre-rejestracja, **własny licznik wariantów**,
   własna reguła STOP i **rachunek mocy PRZED uruchomieniem**. Nie dziedziczą budżetu ani
   progów po Fazie 0. Trzy wymogi przeniesione z minusów Z10, bo w Fazie 0 zawiodły: moc
   przed eksperymentem, walidacja write-upu **przed** publikacją (zasada 16a), aktualizacja
   `docs/rag` **w tej samej rundzie** co zmiana w kodzie (DoD punkt 6).
14. **Hipoteza funding rozpada się na TRZY sformułowania, nie jedno** (H2.0) — i rachunek
   mocy odrzucił dwa **przed** eksperymentem, za 0 wariantów. Bramkowanie na skrajny funding
   powtarza błąd Fazy 0 (zagładza próbę: 1,2–11,9% obserwacji). Carry zmienia rządzącą
   nierówność na `(2p−1)·B + F > C` i przy `F > C` spycha próg **poniżej 50%** (48,13% po
   kontroli ucięcia barierą) — ale ogranicza go **liczba nienakładających się okien 48h
   w 6,8 roku** (maks. 1 240), więc żyje w formule PRZEKROJOWEJ (20+ instrumentów), nie
   czasowej. Wykonalne zostaje jedno: **funding jako 11. cecha, bez bramki, 4h**.
15. **Funding ma MASĘ PUNKTOWĄ: 35,85% obserwacji to dokładnie stawka bazowa 0,0100%** (H2.0)
   ⇒ progi percentylowe są nieużywalne (maska p20/p80 łapie 70,2% obserwacji). To ta sama
   pułapka, którą C2.5 wykrył w `direction_persistence_10`. **Progi na funding muszą być
   ABSOLUTNE.** Sygnał jest za to silnie trwały: autokorelacja lag=1 (8h) = **+0,797**.
16. **Noga `timeout` ROZSTRZYGNIETA NA STALE (H3) — `taker` jest POPRAWNE, nie bledne.**
   Podejrzenie zapisane tu po H2.0 zostalo obalone przez runde, ktora je testowala. Kryterium:
   **noga maker jest dobrze zdefiniowana tylko wtedy, gdy CENA zlecenia jest znana przy
   skladaniu** — przy wejsciu i `tp` jest, przy `timeout` znamy CZAS, a nie cene. Dodatkowo
   wariant maker bylby niespojny z `_resolve_exit_price`, ktory liczy wyjscie timeoutu jako
   `close` tej swiecy — nieosiagalny limitem bez lookaheadu, wiec naliczanie stawki maker
   liczyloby te sama korzysc dwa razy. Zmierzone pasmo progu: **[51,64%; 52,69%]**, szerokosc
   1,05 pp, **niepewnosc NIEISTOTNA decyzyjnie**. Powrot do tematu wymaga ZRODLA DANYCH
   o wypelnieniach zlecen limit, nie kolejnego zalozenia (ADR: `docs/rag/04`).
17. **Bramka kosztowa jest WYPROWADZANA z tej samej funkcji co journal** (H3) — `gate_cost_fraction`
   = `max` po osiagalnych powodach wyjscia. Do H3 bramka miala WLASNA, reczna kopie reguly nog
   plus literal `exit_leg=TAKER`; nic nie wiazalo jej z kosztem w journalu, wiec rozjazd byl
   kwestia czasu, nie dyscypliny. **Usunieta zostala klasa bledu, nie jej instancja.** Skutek
   uboczny czyniacy analizy wrazliwosci uczciwymi: maksimum realizuje `sl` niezaleznie od nogi
   timeout, wiec lejek sygnalow jest identyczny co do sztuki miedzy wariantami.
18. **SPROSTOWANIE dwoch wlasnych liczb (H3):** (a) prog **53,12% z H2.0 byl ZAWYZONY** — liczony
   kosztem BRAMKOWYM (0,0900%, najdrozsza noga dla kazdej transakcji) zamiast realnym (0,0767%);
   poprawnie **52,69%**. Z rzekomej dzwigni 1,04 pp okolo **0,46 pp bylo bledem rachunkowym**,
   nie efektem nogi. (b) Ostrzezenie, ze bramka pomijajac funding jest ANTY-konserwatywna
   (~17% bramki), jest **bledne co do znaku i rzedu wielkosci**: zmierzone **-0,00243%** = 2,7%
   bramki, ze znakiem UJEMNYM (short otrzymuje funding). Bramka jest lekko KONSERWATYWNA.


19. **Liczba OBSERWACJI to nie liczba TRANSAKCJI — trzeci raz ten sam blad** (H2.1).
   Rachunki mocy w tym projekcie szacowaly probe z liczby swiec, a decyduje to, ile z nich
   model uzna za warte dzialania. Ciag: S1 -> S1b (1 037 -> 345, naprawa early stoppingu),
   S1b -> H2.1 (345 -> 98, zdjecie bramki). **Za kazdym razem zaskoczenie, mimo ze precedens
   byl juz w repo.** WYMOG na przyszlosc: rachunek mocy PRZED eksperymentem musi obejmowac
   **rozklad klasy docelowej**, nie tylko liczebnosc danych.
20. **Zdjecie bramki rezimu POGARSZA proporcje klas** (H2.1): przy V=3 na 4h udzial timeoutow
   rosnie **60,83% -> 66,58%**, bo `range` to swiece o niskim ATR (waskie bariery, czesciej
   dotykane), a bez bramki wchodza swiece o barierach zbyt szerokich na 12h. Skutek: model
   z dzialajacym early stoppingiem uczy sie przewidywac klase wiekszosciowa i **odmawia
   kierunku w 99,3%** przypadkow. Bramka zagladza probe PRZEZ FILTR, brak bramki zagladza ja
   PRZEZ NIERONOWAGE KLAS — oba konce tego kompromisu sa teraz zmierzone.
21. **`classify_checkpoint` potrafi zwrocic GO na smieciach** (H2.1): oba ramiona dostaly GO
   przy 3 i 11 waznych foldach i `mean_sharpe` = 21,3 (typowa skala 1-3). To ta sama patologia
   co w C2.12. **Zadnego werdyktu klasyfikacyjnego nie wolno cytowac bez podania
   `n_valid_folds`** — inaczej runda nierozstrzygnieta daje sie przeczytac jako sukces.

22. **APARAT POMIAROWY DZIALA — zweryfikowane (K1).** Przy wyroczni doskonalej pipeline
   mierzy 100,00% trafnosci; kryterium `ci_low > break_even` dalo **0 falszywych alarmow na
   6 losowaniach czystego szumu**. To jest dowod, ktorego projekt nie mial przez 15 rund
   i ktory uwiarygodnia wszystkie dotychczasowe werdykty oparte na tym kryterium — w tym Z10.
23. **PROG WYKRYWALNOSCI (~58%) LEZY POWYZEJ PROGU OPLACALNOSCI (~52,7%)** — luka 5,5 pp (K1).
   **⚠ LICZBA I WYMOG SPROSTOWANE W K2 — notka na koncu tego punktu.**
   Hipoteza dajaca trafnosc 53-58% bylaby OPLACALNA i jednoczesnie NIEWIDZIALNA dla tego
   pipeline'u. Przyczyna: przy slabym sygnale model odmawia kierunku w 99,3-99,7% swiec, wiec
   proba nie pozwala niczego dowiesc (przy q=0,20 trafnosc punktowa 56,19% > prog 51,90%,
   ale n=105 i CI siega 46,70%). **WYMOG: kazda przyszla runda musi podac, czy jej hipoteza
   miesci sie powyzej ~58% zakladanej trafnosci — inaczej jest niemierzalna Z GORY.**
   Skutek dla wynikow wstecz: Z10/Z17+Z21 (n=7 687 / 7 043) NIETKNIETE; S1b (345) i H2.1 (98)
   byly ponizej progu wykrywalnosci, wiec ich werdykty "nierozstrzygniety" byly SLUSZNE
   z powodu, ktorego wtedy nie znalismy.
   **⚠ SPROSTOWANE W K2 (2026-09-22; notka dopisana 2026-09-23):** ~58% (dokladnie 58,20%) to
   trafnosc w PIERWSZYM punkcie siatki `q` (q=0,40), w ktorym zapalilo sie kryterium —
   artefakt rozdzielczosci siatki, nie wlasciwosc przyrzadu; przy siatce z q=0,30 ta sama
   konfiguracja podalaby inna liczbe. **WYMOG „powyzej ~58%" UCHYLONY.** Obowiazuje
   `measurability_report(...)`, a szerokosc pasma „oplacalne, ale niewidzialne" to
   `wald_half_width(n)`, zalezna WYLACZNIE od `n` (CLAUDE.md zasada 18; K2 README §1). Aktualne
   pozostaje sedno: takie pasmo istnieje i przy malym `n` jest szerokie (n=98: 9,90 pp;
   n=7 687: 1,12 pp).
24. **`classify_checkpoint` WYSTAWIL GO CZYSTEMU SZUMOWI** (K1) — i WARUNKOWY przy q=0.
   Podejrzenie z H2.1 potwierdzone na danych, w ktorych Z KONSTRUKCJI nie ma czego znalezc.
   **Ta miara nie jest i nigdy nie byla kryterium werdyktu**; projekt slusznie przeszedl na
   `ci_low > break_even` (C2.12), a K1 dostarcza dowodu, ktorego wtedy nie bylo. Zadnej
   wartosci GO/WARUNKOWY/NO-GO nie wolno cytowac bez `n_valid_folds`.
25. **ABSTYNENCJA MODELU jest problemem numer jeden tego projektu** (K1). To ona, a nie brak
   sygnalu, ograniczyla S1b (n=345), H2.1 (n=98) i sama kontrole negatywna (n~37 na losowanie —
   **przyrzad nie potrafi porzadnie zwalidowac sam siebie z tego samego powodu, dla ktorego
   nie widzi slabych sygnalow**). Kandydaci na osobna runde: wagi klas w XGBoost, kalibracja
   MIN_VALIDATION_ROWS/validation_fraction, wymuszenie kierunku zamiast trzeciej klasy.
26. **ABSTYNENCJE NAPRAWIAJA WAGI KLAS, NIE WYMUSZENIE KIERUNKU (K2).** Dwa sposoby na to samo
   daja przeciwne wyniki. **Wagi klas (`class_weight_mode="balanced"`) obnizaja prog
   wykrywalnosci** o krok siatki `q` i **prostuja odczyt przyrzadu do monotonicznego** —
   baseline czyta sile sygnalu niemonotonicznie, bo przy n rzedu 200-900 dominuje szum.
   **Wymuszenie kierunku (`direction_policy="forced"`) NIE pomaga**: n rosnie 260x, ale sygnal
   jest rozcienczany swiecami, na ktorych poprawny kierunek NIE ISTNIEJE — tam wymuszony
   kierunek wygrywa **48,33%**, czyli ponizej rzutu moneta. Trafnosc spada do 50,33%, prog
   oplacalnosci rosnie do 52,94%, a przy q=0,30 margines robi sie **ujemny (-1,31 pp)**.
   **Wiecej transakcji != lepszy pomiar** — to czwarty przypadek w tym projekcie, gdy liczba
   obserwacji mylona jest z iloscia informacji (por. wniosek 19).
27. **KILL-SWITCH NIE JEST ZRODLEM OBCIAZENIA POMIARU (K2, T6) — sprawa zamknieta.** Podejrzenie
   z K1 (trafnosc 54,09% na czystym szumie) zostalo rozstrzygniete ramieniem o rozdzielczosci
   **+/-0,34 pp**: roznica ON-OFF wynosi **+0,04 pp** na 167 160 transakcjach, czyli jest
   nieodroznialna od zera. Odczyt 54,09% byl szumem przy n=220. Mechanizm jest czysto
   SELEKCYJNY (zbior kandydatow identyczny w obu ramionach — asercja w skrypcie), wiec nie ma
   trzeciej drogi, ktora trzeba by jeszcze sprawdzic.
28. **PRE-REJESTRACJA NIE CHRONI PRZED ZLA REGULA — chroni przed jej ZMIANA PO FAKCIE (K2).**
   Dwie z trzech bramek K2 okazaly sie wadliwe, i to w sposob **wyprowadzalny a priori**:
   (a) zadanie, by CI trafnosci ZAWIERALO prog oplacalnosci, jest na czystym szumie rownowazne
   warunkowi `n <= ~1 142` — mierzy wiec nieprecyzyjnosc, nie specyficznosc, i mechanicznie
   karze kazde ramie osiagajace cel rundy; (b) metryka wyboru oparta na samym
   `wald_half_width(n)` ignoruje, czy jest jeszcze co mierzyc, i dlatego wskazuje ramie
   o UJEMNYM marginesie. **WYMOG na przyszlosc: pre-rejestrujac kryterium, sprawdz, co ono
   robi w granicy duzego `n` i czy nie jest anty-skorelowane z celem rundy.** Kryterium
   kalibracyjne powinno brzmiec "najnizsze `q`, przy ktorym `ci_low > break_even`", a pasmo
   raportowac obok, opisowo.

29. **WAGI KLAS PRZYJETE DOMYSLNIE (adopcja A1 po K2, decyzja uzytkownika 2026-09-22).**
   `DEFAULT_CLASS_WEIGHT_MODE = balanced` w silniku; `none` zostaje jako nazwany wariant
   odtwarzajacy baseline sprzed K2 co do cyfry (test z literalami: 1 280 transakcji,
   final_equity 95 126,0168131146). **Baseline projektu przesunal sie** — ta sama decyzja
   i ten sam koszt co przy C2.12: **zamrozone skrypty rund uruchomione DZIS dadza inne liczby**
   niz zapisane w ich katalogach. Zrodlem prawdy dla wynikow historycznych pozostaje
   `runs/<katalog>/`; odtworzenie z kodu wymaga jawnego `class_weight_mode="none"`.
   Pelne uzasadnienie i konsekwencje: ADR w `docs/rag/03`. **Odstepstwo od litery
   pre-rejestracji K2 zapisane jawnie** — czlon B bramki 1 NIE zostal spelniony przez A1
   i nie udajemy, ze zostal; podstawa decyzji jest czlon A (0/12 falszywych alarmow) plus
   dowod, ze czlon B mierzy nieprecyzyjnosc.
30. **ADOPCJA KODEM ZNAJDUJE BLEDY, KTORYCH RUNDA NIE ZNAJDZIE (2026-09-22).** Wlaczenie wag
   klas domyslnie natychmiast wywalilo trzy testy `KeyError`-em: mapa wag powstaje z czesci
   TRENINGOWEJ, a stosowana jest rowniez do WALIDACYJNEJ, wiec fold, w ktorym uczaca miala
   wylacznie klase `timeout`, a walidacyjna zawierala kierunek, wywracal caly przebieg.
   Runda tego nie mogla zobaczyc — wyrocznia ma wszystkie trzy klasy w kazdym foldzie.
   **Na realnych danych to przypadek SPODZIEWANY** (przy `min_train_rows`=30 fold potrafi nie
   zawierac wszystkich klas; rezim `trend` to 0,53% swiec). Wniosek proceduralny: **wariant
   przyjety do uzytku trzeba wlaczyc DOMYSLNIE i przepuscic przez pelny pytest**, a nie
   zostawiac jako opcje — opcja nie jest testowana tam, gdzie jej nikt nie podaje.

31. **ADOPCJA A1 PRZENOSI SIE NA REALNE CECHY - i ma zmierzona cene (K3).** Dwie konfiguracje
   odlozone jako niemierzalne (S1b n=345, H2.1 n=35) daja po adopcji **1 955** i **8 033**
   transakcje, a rozdzielczosc przyrzadu poprawia sie z **5,28 / 16,56 pp** do **2,22 / 1,09 pp**
   - po raz pierwszy **lepsza niz luka, ktorej szukamy** (2,42 pp). Cena: model przestaje
   WYBIERAC swiece. Przed adopcja bral takie, ktore koncza sie wyraznym ruchem (C2: 37,1%
   timeoutow wobec 66,5% w populacji); po adopcji bierze po rowno z populacja, wiec bariera
   maleje, a prog oplacalnosci rosnie o ~0,5 pp. **Czy ta selektywnosc niosla informacje, nie
   wiadomo** - K3 z zalozenia nie patrzy na trafnosc, bo obie konfiguracje naleza do serii
   zamknietych. **To jest realne pytanie projektowe na osobna runde, nie usterka.**
32. **MIERZALNOSC NIE JEST POWODEM DO WZNAWIANIA ZAMKNIETYCH SERII (K3).** To, ze S1b i H2.1
   staly sie mierzalne, **nie wznawia** ich: obie serie zamyka regula STOP i wyczerpany licznik.
   Jest to natomiast powod, zeby PRZYSZLE hipotezy projektowac na tym przyrzadzie - z realnym
   `n` rzedu 2 000 (z bramka rezimu) i 8 000 (bez niej) na BTC 4h, V=3. Wznowienie wymagaloby
   decyzji bramkowej uzytkownika i wlasnego licznika od zera, jak kazda hipoteza w ETAPIE 4.

33. **STALA FUNDING 0,0001 JEST TRAFNA — sprawdzone, nie zalozone (T1-diag).** Realna mediana
   stawki to DOKLADNIE 0,0001, srednia 0,000107. Przejscie na realne stawki z dyskretnym
   harmonogramem rozliczen przesuwa prog oplacalnosci o **+0,022 pp** — 50x mniej niz
   niepewnosc pomiaru. **Prawdziwy powod, dla ktorego stawka nie ma znaczenia, nie jest
   jednak jej trafnosc, tylko SYMETRIA KIERUNKOW:** przy long/short po polowie signowany
   funding nettuje sie do zera niezaleznie od stawki. **WYZWALACZ na przyszlosc: strategia
   jednostronna (same longi albo same shorty) uniewaznia ten wniosek** i wtedy realny funding
   trzeba wprowadzic.
34. **UZASADNIENIE ZADANIA TEZ TRZEBA WALIDOWAC, nie tylko wynik rundy (T1-diag).** Zadanie T1
   stalo w backlogu z uzasadnieniem, ktore bylo BLEDEM KATEGORII: porownywalo signowany koszt
   per transakcja (-0,00243%, policzony JUZ ze stala i dla proby z przewaga shortow) ze stawka
   za okres 8h (+0,01%). Dwie rozne wielkosci. Gdyby nikt tego nie sprawdzil, projekt
   przebudowalby model kosztow i przesunal baseline po raz kolejny — za 0,022 pp, w dodatku
   w strone PRZECIWNA do oczekiwanej. **Liczba zacytowana w backlogu ma ten sam status co
   liczba w write-upie rundy: dopoki nikt jej nie przeliczyl, jest hipoteza.**

35. **MOMENTUM DOSTALO UCZCIWY TEST I GO NIE PRZESZLO (M1) — pozycja z wniosku 12 ZAMKNIETA.**
   n = 8 512 (wobec 299 w Fazie 0), trafnosc **49,74%**, CI [48,68%; 50,80%], prog 52,94%.
   Gorny kraniec CI **2,14 pp ponizej progu**, proba **1,90x** wymaganej do orzeczenia negatywu.
   **KLUCZOWE ZASTRZEZENIE, ktorego nie wolno pomijac przy cytowaniu:** momentum NIE jest gorsze
   od mean-reversion. Roznica B-A = -0,63 pp, CI [-2,15; +0,90], z = -0,80 — **nieistotna**.
   Momentum jest TAK SAMO nieobecne. Zdanie "momentum wypadlo gorzej" byloby nadinterpretacja
   szumu. Ograniczenie zapisane z gory: wykrywalnosc zaczyna sie od 54,00%, wiec edge rzedu 53%
   — realny przy nizszym koszcie albo szerszej barierze — byłby dla tej rundy niewidoczny.
36. **RAMIE ODNIESIENIA ODTWORZYLO HISTORYCZNY POMIAR CO DO 0,01 pp (M1) — aparat jest spojny
   miedzy konfiguracjami.** Reversion bez bramki na 4h z wagami klas dalo **50,3672%**, podczas
   gdy 5m/`range` z bramka i bez wag dawalo **50,38%** (Z17+Z21), a pooled Fazy 0 **50,27%** (Z10).
   CI wszystkich trzech sie nakladaja. To NIE byla kontrola zaprojektowana — wyszla z ramienia,
   ktore istnialo jako punkt odniesienia. **Wartosc metodologiczna: zgodnosc miedzy niezaleznymi
   konfiguracjami jest tania i mocna forma walidacji** — jesli aparat albo konfiguracja sa
   popsute, ta zgodnosc sie nie pojawia. Warto ja planowac w kolejnych rundach.

37. **FUNDING JAKO CECHA ZMIERZONY I ODRZUCONY (F1) — pytanie z H2.1 ma odpowiedz.**
   n = 8 127 (wobec 98 w H2.1), trafnosc **50,34%**, CI [49,25%; 51,43%], prog 52,94%.
   Gorny kraniec CI **1,51 pp ponizej progu**, proba **1,81x** wymaganej. Roznica wobec
   ramienia bez funding: **-0,03 pp, CI [-1,57; +1,51], z = -0,04** — funding nie zmienia
   trafnosci w ZADNA strone. H2 pozostaje zamkniete; F bylo nowa hipoteza z licznikiem od zera.
38. **"FUNDING POTRAJA LICZBE DECYZJI" BYLO ARTEFAKTEM — ustalenie H2.1 WYCOFANE (F1).**
   Przed A1: 35 -> 98 sygnalow (2,80x). Po A1: 8 114 -> 8 196 (**1,01x**). Mechanizm: przy
   abstynencji 99,3% model podejmowal 35 decyzji, wiec KAZDE drobne zaburzenie posteriora
   mnozylo te liczbe wielokrotnie. **To trzeci wariant tego samego bledu** (por. wniosek 19
   "liczba obserwacji to nie liczba transakcji" i wniosek 26 "A2 kupuje n bez informacji"):
   **wielkosc policzona na zaglodzonej probie nie jest miara niczego.** WYMOG na przyszlosc:
   zanim zapiszesz "ustalenie" z rundy NIEROZSTRZYGNIETEJ, sprawdz, czy nie jest funkcja
   samej wielkosci proby.
39. **ZBIOR INFORMACYJNY WYCZERPANY W TYM, CO DA SIE ZMIERZYC (M1 + P1 + F1).** Projekt
   zmierzyl z zapasem mocy, kazde przy probie ~8 000 i pasmie ~1,1 pp:
     cechy mean-reversion (OHLCV)  -> 50,37%
     cechy momentum      (OHLCV)  -> 49,74%   (M1)
     funding (jedyne spoza OHLCV) -> 50,34%   (F1)
   Wszystkie przy 50%, wszystkie ponizej progu 52,9%. Dane o pozycjonowaniu sa NIEMIERZALNE
   przy tej metodologii (P1: 30,8 dnia historii, brakuje 40x). **To nie jest brak pomyslow —
   to wyczerpanie tego, co da sie zmierzyc ta metodologia na tych danych.** Otwarte pozostaja
   WYLACZNIE kierunki wymagajace zmiany zalozen: inny target niz kierunek (nowa ekonomia
   wyplaty), carry przekrojowy (silnik portfelowy), ETH/SOL/BNB (brak czego generalizowac),
   zbieranie danych pozycjonowania od dzis (~3,4 roku do uzytecznosci).
   **AKTUALIZACJA P3 (2026-09-23): zdanie o pozycjonowaniu jest NIEAKTUALNE** — P1 sprawdziło
   REST API, a archiwum plików Binance ma te same wielkości co 5 min od 2020-09-01 (wniosek 59).
   Pozycjonowanie jest MIERZALNE na nowej bazie (n ≈ 6 950 transakcji, 1,55× wymaganych);
   reszta wniosku (OHLCV, funding jako cecha) bez zmian.
40. **CARRY PRZEKROJOWY NA PERPETUALACH JEST NIEMIERZALNY — a przekroj NIE mnozy proby (P2).**
   Na 20 najwiekszych monetach (2020–2026, 1 161 okien 48h) sam funding pokrywa koszt handlu
   limitami: F − C = 0,097% na okno, CI [0,051%; 0,143%] — **pierwszy w projekcie dodatni
   i istotny czlon ekonomii**, choc slabnacy (od 2023 ~2–3× mniejszy niz w 2020–21) i znikajacy
   przy koszcie taker. Ale ruchy cen koszykow sie NIE znosza: σ = 5,56% na okno, 57× wiecej niz
   zysk z oplaty, wiec pelny test wymaga ~25 850 okien (~140 lat) wobec 1 161. **Zalozenie
   z STATUS §17, ze 20 instrumentow daje 20× probe (160 660), bylo bledne:** korelacja zwrotow 0,47
   ⇒ 18 monet ≈ 2 niezalezne. Czwarty wariant bledu z wnioskow 19/26/38 — **liczba instrumentow
   to nie liczba niezaleznych obserwacji.** Jedyna droga do mierzalnosci tego mechanizmu to usuniecie
   ryzyka cenowego (zabezpieczenie spot: cash-and-carry) — inny produkt, decyzja bramkowa.
41. **EARLY STOPPING DZIALA — A MODEL NIE MA CZEGO SIE NAUCZYC (T4).** W konfiguracji kanonicznej **[korekta AU1: wniosek 87]**
   (4h, okno 60 dni, `balanced`) ES chroni przed przeuczeniem w 86/86 oknach, a `MIN_VALIDATION_ROWS`
   jest bezczynny (walidacja ~70 wierszy) — ryzyko z Z17b tu nie wystepuje. Ale na danych, ktorych wybor
   nie widzial, nawet idealnie dobrana liczba drzew poprawia strate tylko o 0,7% wobec zgadywania po rowno,
   a najczesciej najlepsze jest 1 drzewo. **Lekcja metodologiczna:** na danych bez sygnalu kazda kalibracja
   hiperparametru „regularyzujacego” (mniej drzew, wieksza walidacja) wyglada jak poprawa, bo optimum to
   „nie ucz sie”. Kalibracja przyrzadu musi sie odbywac na danych ze ZNANYM sygnalem (wyrocznia K1/K2),
   nigdy na realnych danych, na ktorych sygnalu nie ma — inaczej stroimy przyrzad pod slepote.

42. **UCZCIWY MODEL WYPEŁNIEŃ NIE ZMIENIA WERDYKTU (W1).** Zlecenie limit po `close` świecy
    sygnału wypełnia się na 4h w **99,4 %** (52 z 8 114 sygnałów przepada), trafność 50,11 %
    [49,02; 51,21] przy progu 52,96 % — NEGATYWNY. Założenie C2.12 „limit zawsze się wypełnia"
    było prawie prawdziwe, a optymizm ceny wypełnienia (`min(open, P)`) to +0,0004 % ceny (0,5 %
    kosztu). Przybliżenie kolejności zdarzeń świecami 4h wobec ścieżki 5m: powód wyjścia zgodny
    w **97–99,7 %** transakcji, wszystkie rozbieżności na NIEKORZYŚĆ strategii (≤ 1,4 pp
    trafności) — lata bez świec 5m są obciążone konserwatywnie.
43. **TRAFNOŚĆ POWYŻEJ PROGU MOŻE BYĆ ILUZJĄ GEOMETRII WYPŁATY (W1b).** Limit na cofnięciu
    0,5·ATR daje p = **53,15 %** [51,32; 54,98] wobec progu 52,81 % — punktowo pierwszy „dodatni
    margines" w projekcie — a jednocześnie **średni zwrot netto istotnie ujemny** (t = −3,90,
    t_neff = −3,61; −0,096 % nominału na transakcję). Wygrane to w 79 % małe timeouty (+0,17 %
    ceny, 59 % z nich powyżej wejścia), straty to pełne stopy (−2,45 %), SL:TP = 21:16.
    `break_even_hit_rate = 0,5·(1 + C/B)` zakłada wypłaty ±B — gdy wejście jest oddalone od
    kotwicy etykiety, PRZESTAJE być progiem. **Statystyka nośna to pooled t zwrotu netto**
    (wytyczna CLAUDE.md); kryterium `ci_low > break_even` w pre-rejestracjach uzupełniać o
    warunek `t_stat > 0`. Pierwszy zmierzony rozmiar selekcji przez wypełnienie: sygnały
    wypełnione mają etykietę „zły kierunek" w 79 % (cofnięcie) / „dobry" w 73 % (wybicie) —
    mechanika zlecenia, nie informacja.
44. **WEJŚCIE NA WYBICIU JEST GORSZE NA OBU CZŁONACH (W1c).** Noga taker podnosi próg do 54,83 %,
    a trafność spada do 46,13 % [44,55; 47,72] (t = −7,55): kupno na lokalnym szczycie, po którym
    cena częściej zawraca (timeouty wygrywają w 43 %). **Seria W zamknięta (3/3, reguła STOP):
    żadna reguła wejścia nie tworzy edge'u tam, gdzie model go nie ma.** Zysk rundy: backtest
    mierzy wykonanie zgodne z zasadą „po konkretnej cenie" (tryb `path` w `engine.py`), a lekcja
    z W1b obowiązuje w każdej przyszłej rundzie z wypłatami asymetrycznymi (np. częściowe TP).
45. **ZARZĄDZANIE POZYCJĄ NIE TWORZY INFORMACJI (N1):** częściowe wyjście 50 % na +1,67 %, stop na
    wejściu i reszta do 1,5·ATR dają na tych samych 6 736 transakcjach różnicę zwrotu netto
    **+0,007 % [−0,009; +0,024]** (t = +0,85) wobec pojedynczego wyjścia — zero. Trafność rośnie
    z 49,6 % do **53,3 %** [52,2; 54,5] i ląduje „na styk" starego progu ±B (53,32 %), a zwrot netto
    jest istotnie ujemny (−0,094 %, t_neff −4,08) — iluzja W1b w czystej postaci. **Próg
    uogólniony `p* = (L̄ + C)/(W̄ + L̄)`** (57,24 %: wygrane zmalały do 1,11 %, straty zostały 1,30 %)
    jest od N1 obowiązkowym odczytem przy wypłatach asymetrycznych (ADR `docs/rag/03`). Strata
    siedzi w 68 % transakcji BEZ bliższego celu: timeouty całej pozycji (51 %) mają średnią
    −0,26 % — sygnał, który w 12 h nie doszedł do +1,67 %, przeciętnie dryfuje przeciw pozycji.
    Seria N zamknięta (1/1, STOP): żadnego kolejnego schematu prowadzenia pozycji na modelu bez
    sygnału.
46. **NOWA BAZA 2021+ JEST TRUDNIEJSZA (N1, zasada 20):** kontrola (limit po close, pojedyncze
    wyjście) na 2021-01 → 2026-06: p **49,58 %** [48,39; 50,77], zwrot netto **−0,107 %**
    [−0,149; −0,065] na transakcję, próg ±B 53,07 %, abstynencja 40,4 % (niżej niż 43,8 % na
    6,8 roku), 69 okien. Na pełnej historii ten sam pipeline dawał 50,11 % i −0,082 % (W1a).
    Liczby sprzed N1 i po N1 nie porównują się 1:1.
47. **EKSTREMUM ŚWIECY NIE DOWODZI KOLEJNOŚCI ZDARZEŃ PO ZDARZENIU WEWNĄTRZ ŚWIECY — DOWODZI
    TYLKO ZAMKNIĘCIE (Poprawka 1 do N1, przed uruchomieniem):** przy wejściu limitem minimum świecy
    wypełnienia leży poniżej wejścia z samej konstrukcji wypełnienia, więc reguła „po celu w tej
    świecy liczy się stop na wejściu, gdy `low ≤ E`" zamykałaby drugą połowę mechanicznie.
    Rygorystyczny odczyt: zdarzenie po chwili τ wewnątrz świecy jest dowiedzione wyłącznie przez
    `close` (close za dalszym celem ⇒ cel padł po τ; close za wejściem ⇒ stop padł po τ);
    niedowiedzione = nie liczy się. Wykryte testami przykładowymi reguły, zero spojrzeń na dane.
48. **FORMACJE ŚWIECOWE Z PODRĘCZNIKA WSKAZUJĄ NA 4h BTC KIERUNEK ODWROTNY (A1):** reguła
    „bycza → long, niedźwiedzia → short" na 6 formacjach TA-Lib (0 stopni swobody, zestaw
    zapisany przed danymi) daje **p = 46,35 % [44,38; 48,31]** — cały CI poniżej rzutu monetą —
    i zwrot netto **−0,177 % [−0,245; −0,109]** na transakcję (n 2 477, t −5,11). 84 % sygnałów
    to objęcie (45,7 % [43,6; 47,8]): duża świeca w kierunku sygnału jest w 12 h częściej końcem
    ruchu niż początkiem. Oba kierunki tracą po równo (nie błąd znaku). Jako 5. cecha modelu —
    nic: różnica parowana **−0,001 % [−0,012; +0,010]**, 6 444/6 577 transakcji identycznych
    (model ma tę informację w `return_lag_1`). Rodzina formacji zamknięta 2/2, STOP.
49. **„ODWRÓĆMY REGUŁĘ" TO NOWA HIPOTEZA, NIE WNIOSEK (A1):** zmiana znaku po obejrzeniu wyniku
    jest selekcją post hoc (STW 1999); odwrotna reguła nie jest lustrem (zlecenie limit po close
    wypełnia się inaczej dla kupna i sprzedaży — W1b: selekcja przez wypełnienie), a jej ekonomia
    ex ante to ≈ +0,01 % na transakcję (brutto +0,094 % − koszt 0,083 %) — nieodróżnialne od zera
    przy se 0,035 %. Gdyby miała być mierzona: osobna pre-rejestracja, własny licznik, decyzja
    bramkowa użytkownika. To samo dotyczy podgrup „które wyglądają lepiej" (gwiazdy: n 26–60,
    CI szerokie na 25–37 pp; 2 z 6 podgrup nad 50 % = oczekiwany szum).
50. **N_eff ≤ n TAKŻE W STATYSTYKACH PER TRANSAKCJA (Poprawka 2, A1):** wzór N/(1 + 2Σρ) przy
    ujemnej autokorelacji zwrotów kolejnych transakcji (nakładające się pozycje z sąsiednich świec
    z formacją) dał N_eff 5 495 > n 2 477 i t_neff −7,61 zamiast −5,11. Korekta na autokorelację
    może tylko ODEJMOWAĆ pewność — cap jak w `metrics.summarize_pooled_by_regime`, teraz też
    w `checkpoint_lib.summarize_trade_returns` (test). Werdykt bez zmian; liczby −7,61 nie wolno
    cytować. Wykryte porównaniem dwóch tabel tego samego raportu (bramka 16a: druga droga).
    Drugi wariant wniosku 19: gdy sygnał jest REGUŁĄ, `oczekiwane_n` liczy się z częstości
    zdarzenia (tu 21,9 % świec) — rachunek ex ante trafił w journal do 2 %.
51. **KLASYCZNA ANALIZA TECHNICZNA NA BTC 4h ZAMKNIĘTA (A2, seria A 7/7):** reguły z podręcznika
    użyte dosłownie (parametry domyślne skilla, bez dobierania) — struktura trendu HH/HL
    **48,20 % [46,98; 49,42]**, −0,127 % [−0,170; −0,084]; wsparcie/opór (≤ 0,5·ATR od
    potwierdzonego poziomu) 49,87 %, −0,080 % [−0,114; −0,045]; Fibonacci 38–62 % 51,5 %
    [49,4; 53,6], −0,041 % [−0,110; +0,028] (nierozstrzygnięte: pasmo 2,1 pp); grupa zdarzeń
    (wybicie, podwójny szczyt/dno, RGR, przecięcie EMA, linia trendu) 48,3 %, −0,103 %
    [−0,182; −0,024] (nierozstrzygnięte wg litery: n 2 133 < guard 2 366, choć CI zwrotu pod zerem);
    model + 10 cech AT: −0,099 %, parowane z kontrolą +0,005 % [−0,055; +0,066] przy 35 %
    zmienionych decyzji i abstynencji 40,4 → 42,7 % — więcej cech = więcej szumu. Reguły
    „z ruchem" na 4h BTC są konsekwentnie POD monetą: A1 46,4 %, W1c 46,1 %, A2.1 48,2 %,
    wybicie 48,5 %. Wniosek 11 potwierdzony po raz kolejny; dalsze parametry/podzbiory = losy.
52. **REGUŁY STANOWE NAKŁADAJĄ POZYCJE I POGŁĘBIAJĄ OBSUNIĘCIA (A2):** sygnał trwający przez
    epizod (struktura trendu: 412 epizodów po 16,6 świecy; S/O: 83 % świec) otwiera pozycję
    w każdej świecy — kill-switch tłumi 4,8 % (A2.1) i 3,8 % (A2.3) wypełnień wobec 1,1 % kontroli,
    N_eff spada do 2 875/6 423. Stłumienia są NIELOSOWE (po seriach strat) — raportować je
    zawsze obok n; kierunek obciążenia raczej na korzyść reguły. Reguła stanowa bez zarządzania
    ekspozycją to nie strategia, tylko ciągła ekspozycja z etykietą.
53. **RZADKIE ZDARZENIA AT SĄ NIEMIERZALNE NA 5,5 ROKU 4h — TEST RODZINY ZAMIAST PIĘCIU LOSÓW
    (A2):** 86 (RGR) – 988 (wybicie) sygnałów → half-width 3–11 pp; osobno żadna reguła nie
    startuje (zasada 18; wybicie przegrało o 0,20 pp — granica przyjęta, nie negocjowana).
    Grupa (sign sumy) daje 2 174 i mierzalny sprawdzian; werdykt dotyczy grupy, rozbicie jest
    opisowe (5 podgrup, CI 6–22 pp, skrajne 43,6 % i 52,2 % = oczekiwany rozrzut). Pięć ramion
    naraz = pozytyw przy `z_5 = Φ⁻¹(1 − 0,025/5) = 2,576`. Guard negatywu liczy się z BE
    RAMIENIA ex post (A2.4: 52,88 % → 2 366 > 2 133) — pre-rejestracja tak mówi i tak zostaje,
    nawet gdy CI zwrotu leży pod zerem.
54. **CASH-AND-CARRY Z HEDGEM SPOT ZBIERA FUNDING BEZ RYZYKA KIERUNKU — PIERWSZY POZYTYW, ALE INNEGO
    RODZAJU (C1):** long spot + short perp BTC od 2021: **+0,0099 %/8h [+0,0063; +0,0135]**, t_neff
    5,40, rocznie **+10,9 % nominału = +5,4 % kapitału [3,5; 7,4]**; Σ funding 60,2 %, Σ hedge
    −0,13 % (baza mean-reverting: tożsamość +0,10 % minus człon wariancji −0,22 %), koszty 0,38 %,
    obsunięcie 0,64 %. To NIE jest edge w sensie projektu (żadnej prognozy) — to kontraktowy
    przepływ za dostarczanie dźwigni. **Niestacjonarny:** 2021 daje 30,6 z 60,2 pp (15 %/rok
    kapitału), 2022–2026 0,4–6 %/rok, ostatnie 3 lata 3,6 % brutto; CI średniej z 5,5 roku nie
    jest prognozą. Nie wyceniono: likwidacji shorta (perp +90 % w 30 dni w 2021 — bez
    przenoszenia zysków spot na depozyt pozycja pada), ryzyka giełdy, kosztu kapitału. Decyzja
    o produkcie = decyzja użytkownika, nie runda.
55. **PRZEŁĄCZANIE POZYCJI CARRY PO ZNAKU FUNDINGU PRZEGRYWA Z ARYTMETYKĄ (C1b):** funding zmienia
    znak 874 razy w 5,5 roku (epizody ≤ 0 trwają średnio 16 h), każde przełączenie kosztuje obie
    nogi (0,19 %) → 166 % nominału kosztów za 61 % opłat; −9,3 %/rok kapitału [−13,9; −4,7].
    Każda reguła „wychodź, gdy przestają płacić" musi porównać koszt przełączenia z oczekiwaną
    stratą w epizodzie (0,19 % vs ~2 × 0,01 %) — a to rozstrzyga się przed pomiarem.
56. **RACHUNEK MOCY MUSI BRAĆ AUTOKORELACJĘ SYGNAŁU, NIE TYLKO SZUMU (C1):** ex ante `se` liczono
    ze std hedgu (N_eff = n), a szereg P&L dziedziczy trwałość fundingu (lag-1 0,84, lag-30 0,52)
    → N_eff 286 z 6 019 i `se` 5,6× większe niż zakładano (werdykt przetrwał: 5,40 > 2,24).
    Wariant trzeci wniosku 19: dla targetu-przepływu liczba niezależnych obserwacji to liczba
    EPIZODÓW stawki, nie liczba rozliczeń.
57. **PREMIA REBALANSOWA KOSZYKA KRYPTO NIE ISTNIEJE W TYM UNIWERSUM — RUCHY WZGLĘDNE TRWAJĄ (R1):**
    top-20 po obrocie, rebalans dzienny vs trzymanie w miesiącu: netto **−3,55 %/rok
    [−9,50; +2,40]**, brutto −2,68 %, koszt obrotu 0,87 %; wartość A względem B **−12,1 %** przez
    5,4 roku (2021-02 → 2026-06), premia dodatnia w 36/65 miesięcy, najgorzej w hossach alt-ów
    (2021 −12,7 %, 2026 H1 −8 %), dodatnio tylko w bessie 2022 (+3 %). Formalnie NIEROZSTRZYGNIĘTY
    (CI obejmuje zero), ale scenariusz „ruchy względne niezależne z dnia na dzień" (6–11 %/rok
    brutto; zapisany przed wynikiem) leży poza CI (górny kraniec brutto +3,3 %): wewnątrz miesiąca
    zwycięzcy w krypto dalej wygrywają, rebalans „do równych wag" sprzedaje ich za wcześnie.
    Z dwóch celów nie-kierunkowych: carry z hedgem (C1) daje kontraktowy przepływ, premia
    rebalansowa nie daje nic. Seria R zamknięta 1/1.
58. **RACHUNEK MOCY DLA RÓŻNICY DWÓCH STRATEGII Z PROXY ANALITYCZNEGO NIEDOSZACOWUJE SZUMU (R1):**
    proxy ½·CSV (wariancja przekrojowa) dało se 0,0027 %/dzień, ex post sd premii 0,370 %/dzień →
    se 0,0083 % (3×) i wykrywalny efekt 8,5 %/rok zamiast 2,8. Premia dnia to różnica dwóch
    koszyków z dryfującymi wagami, której rozrzut rośnie z dyspersją (pompki +520 %), nie
    z ½·CSV. Czwarty wariant wniosku 19 (po 56): szum RÓŻNICY strategii liczyć z symulowanego
    szeregu różnic na danych (bez patrzenia na średnią), nie z wzoru. Procesowo: `pytest | tail`
    maskuje kod wyjścia — kod R1 trafił do commita z padającym testem; `set -o pipefail`
    w każdym łańcuchu z testami (naprawa `db16af7` przed przebiegiem końcowym).
59. **SONDA ŹRÓDŁA SPRAWDZA WSZYSTKIE KANAŁY DYSTRYBUCJI, NIE JEDEN (P3 koryguje P1):** P1
    (2026-09-22) skreśliło całą klasę danych o pozycjonowaniu po sprawdzeniu REST API
    (`fapi.binance.com/futures/data/*`, 30,8 dnia, HTTP 400 dalej) i uruchomiło kolektor
    „na 3,4 roku". Publiczne ARCHIWUM PLIKÓW (`data.binance.vision`, `futures/um/daily/metrics`)
    ma te same wielkości co 5 minut od **2020-09-01**: 2 213 dni bez luki, 636 710 odczytów,
    pokrycie bazy z zasady 20 **99,90 %**, wartości zgodne z kolektorem REST za wspólne 505 godzin
    (mediana różnicy 0,02–0,1 %). Koszt pomyłki: jeden dzień, kolektor i błędny wniosek 39
    (zaktualizowany). Reguła: zanim źródło dostanie status „niemierzalne danymi", sprawdź REST
    **i** archiwum plików **i** dumpy; zapisz, co sprawdzono, a czego nie.
60. **OSIEM ŹRÓDEŁ SPOZA OHLCV JEST DOSTĘPNYCH ZA DARMO Z HISTORIĄ ≥ 96 % BAZY (P3):**
    pozycjonowanie 5 min (99,9 %; top-trader L/S z dziurą 2022 = 84 %), funding COIN-M 8h od
    2020-08 (99,98 %; masa punktowa 42,7 % na 0,0001 — progi absolutne, wniosek 15), 24 kontrakty
    kwartalne 8h (98,3 %; 330 pustych świec po wygaśnięciu do odfiltrowania), DVOL BTC/ETH 1d
    od 2021-03-24 (95,9 %), CoinMetrics 14 metryk on-chain 1d (100 %, 0 braków; `shift(1)`
    przez opóźnienie publikacji), Fear & Greed 1d (99,95 %), Coinbase 1d (100 %), FRED 5 serii
    (dni robocze; tło do carry, nie cecha). Odpadły: likwidacje (archiwum puste), OKX (bez
    historii), księga zleceń (od 2023). Każde źródło = nowa seria z własną pre-rejestracją
    i rachunkiem mocy; cecha 4h na tej bazie ma n ≈ 6 950 transakcji, half-width ≈ 1,2 pp.
    Kolektor REST `CLAS5-positioning` zbędny dla historii (archiwum, opóźnienie ~1 dnia).
61. **CASH-AND-CARRY MA SENS TYLKO W KONSTRUKCJI COIN-M (D1):** 1 BTC zabezpieczenia + short
    inverse 1× ma STAŁĄ wartość USD (P + N(1/P − 1/P₀)·P = P₀ — tożsamość, test hypothesis),
    więc nie ma likwidacji ani uzupełnień, a kapitał to 1×. Stawka COIN-M jest niższa od USDT-M
    o **1,82 pp/rok [0,53; 3,11]** (korelacja 0,70; masa punktowa 41,7 % na 0,01 %), ale na
    kapitale wychodzi **+9,07 %/rok [5,88; 12,26]** wobec +5,44 % [3,44; 7,45] dla USDT-M 2×.
    Ponad T-bill 3M od 2022 (5 obserwacji rocznych): COIN-M +1,8 pp/rok (od −1,5 do +7,2),
    USDT-M 2× −1,0 pp, basis kwartalny 2× −0,9 pp. Nadal przepływ za dźwignię innych z ryzykiem
    giełdy; decyzja o produkcie = użytkownik. **Decyzja użytkownika 2026-09-23: carry
    odpuszczone („nie o takie zwroty mi chodzi") — kierunek C/D zamknięty bez produktu.**
62. **DEPOZYT KRÓTKIEJ NOGI USDT-M: 1× Z MIESIĘCZNYM UZUPEŁNIANIEM PRZEŻYWA 5,5 ROKU BEZ
    LIKWIDACJI (D1):** run-up 30 dni max +89,6 % (p99 58,5 %), 90 dni +112 %; siatka 4 × 4:
    M = 1,0 / 30 dni → 0 likwidacji, max wykorzystanie 70,9 % (po `high` 70,0 %), +5,29 %
    na kapitale; M = 0,5 / 7 dni → 0, ale po `high` 46,3 % z 49,5 %; M = 0,25 / 1 dzień → 0,
    ale koszt uzupełnień 1,43 %/rok (obrót 41×) i skok 21 %/dzień o 3 pp od progu. Uzupełnienie
    depozytu = przycięcie obu nóg (obrót × 0,19 %) — koszt pominięty w pre-rejestracji
    (Poprawka 1); bez niego siatka faworyzowała najtańszy depozyt. Basis kontraktów kwartalnych
    (mediana frontu 5,9 %/rok; 2022: 16 % dni ujemnych) ≈ funding zrealizowany (różnica median
    +1,8 pp przy 30 dniach, −0,9 pp przy 90; rozstęp ±17 pp na 21–22 kontraktach) — kontrakt
    zamyka stopę, nie podnosi jej.
63. **N_EFF Z SAMEJ AUTOKORELACJI LAG-1 ZAWYŻA PRÓBĘ 8× DLA SZEREGÓW O DŁUGIEJ PAMIĘCI (D1):**
    funding COIN-M acf1 0,675 → `n(1−ρ)/(1+ρ)` = 1 169, kanoniczny `effective_sample_size`
    (suma całej funkcji autokorelacji) = 149; half-width 3,2 %/rok zamiast pre-rejestrowanych
    1,2 %. Piąty wariant wniosku 19 (po 56 i 58): rachunek mocy dla PRZEPŁYWU liczy N_eff
    kanoniczną funkcją na własnościach danych, nigdy z proxy lag-1.
64. **MOMENTUM PRZEKROJOWE NA TOP-20: +22 %/ROK NETTO, DODATNI W 6/6 LAT, ALE NIEROZSTRZYGNIĘTY
    (X1):** long top-5 / short bottom-5 po zwrocie 28 dni, trzymanie 7 dni, 2021-02 → 2026-06:
    **+0,060 %/dzień [−0,015; +0,135]**, t 1,58, Σ +119 % (brutto +131 %, funding +5 %, koszty
    −17 % przy obrocie 0,87/formowanie — rankingi trwałe), rok po roku +8/+15/+12/+14/**+62**/+8
    (2025 = 52 % sumy; bez 2025 ≈ 13 %/rok), korelacja z BTC −0,13, bez 20 skrajnych dni średnia
    bez zmian, IC +0,028 [−0,007; +0,064]. Efekt siedzi w nodze SHORT (przegrani tracą dalej —
    noga short −109 % w 2025), spójnie z R1 (wniosek 57). Pierwszy zakład o kierunek (relatywny)
    z dodatnim punktowo odczytem w projekcie — hipoteza z poparciem, nie dowód: rozdzielczość
    27 %/rok, do rozstrzygnięcia trzeba ~4× próby (szerokość albo czas), nie wariantu. Obietnica
    literatury (52 %/rok) na granicy wykluczenia. Seria X 1/1 STOP.
65. **RACHUNEK MOCY Z LOSOWYCH RANKINGÓW TRAFIA W RZĄD WIELKOŚCI, ALE ZANIŻA SZUM O ~30 % (X1):**
    100 symulacji dało half-width 21,2 %/rok, ex post 27,3 % (sd dzienna 1,68 % vs 1,30 % pod
    H0) — nogi wybrane sygnałem skupiają monety bardziej zmienne niż losowe. W R1 proxy
    analityczne myliło się 3× (wniosek 58), tu 1,3× — symulacja jest właściwym narzędziem,
    ale H0 trzeba losować z dopasowaniem zmienności (albo mnożyć half-width przez 1,3).
66. **POZYCJONOWANIE (ZMIANA OI 24H) JAKO CECHA 4H: NEGATYWNE, ALE PIERWSZA CECHA SPOZA OHLCV,
    KTÓRA W OGÓLE PORUSZA MODEL (O1):** kontrola + `oi_change_24h` → −0,074 % [−0,116; −0,032]
    na transakcję (kontrola −0,107 %), t_neff −2,90, trafność 50,25 % [49,06; 51,44] (kontrola
    49,58 %) wobec progu 53,07 % — NEGATYWNY z zapasem n 3,2×. Parowo na tych samych świecach:
    +0,024 pp [−0,019; +0,067], inny kierunek w **20,6 %** transakcji (A1b/A2.5: ~0 %),
    poprawa w nodze long (50,96 %) i w nodze timeout (brutto −0,032 % → 0); korelacja cechy
    z `volume_zscore_20` 0,045 — informacja niezależna od ceny/wolumenu. Odczyt: pozycjonowanie
    to prawdopodobnie słaba, realna informacja, za słaba dla modelu 4h z barierą 1,5·ATR
    i kosztem 0,08 %. Wzorzec dopięcia snapshotu z wnętrza świecy (trzy testy lookaheadu)
    gotowy dla DVOL/on-chain/F&G. Seria O 1/1 STOP; kolejne kolumny archiwum = decyzja
    użytkownika (jedna na rundę).
67. **PIĘĆ ŹRÓDEŁ SPOZA WYKRESU JAKO CECHY MODELU 4H — ŻADNE NIE PRZEKRACZA PROGU, DWA LEKKO **[korekta AU1: wniosek 87]**
    PORUSZAJĄ MODEL (F1, O1, L1, V1, G1):** ten sam przyrząd (kontrola 4 cechy REVERSION vs
    kontrola + 1 cecha, parowo, próg p* ≈ 53,1–53,9 %):

      | seria | cecha | p | r̄ netto | parowo O − kontrola | abstynencja |
      | F1 | funding | 50,34 % | — | — | — |
      | O1 | zmiana OI 24h | 50,25 % [49,06; 51,44] | −0,074 % | +0,024 pp [−0,019; +0,067] | 40,9 % |
      | L1 | podaż na giełdach 7d | 49,79 % [48,56; 51,02] | −0,097 % | +0,003 pp [−0,047; +0,052] | 44,3 % |
      | V1 | DVOL − zrealizowana | 50,49 % [49,21; 51,77] | −0,076 % | +0,018 pp [−0,037; +0,074] | 47,7 % |
      | G1 | Fear & Greed | 49,90 % [48,66; 51,13] | −0,102 % | +0,002 pp [−0,045; +0,049] | 45,1 % |
      (kontrola: 49,58 % [48,39; 50,77], −0,107 %, abstynencja 40,4 %)

    Wzorzec: cechy o skali dni (acf1 ≥ 0,98) czynią model 4h mniej pewnym (abstynencja +4–7 pp),
    a nie lepszym; jedyne cechy, które przesuwają decyzje na tych samych świecach, to te o skali
    godzin (OI 24h) albo z innego rynku (DVOL) — i to o +0,02 pp przy potrzebie ~+0,15 pp do progu.
    Odczyt: **model kierunkowy 4h z barierą 1,5·ATR i kosztem 0,08 % nie wyjdzie ponad próg
    przez dokładanie pojedynczych cech spoza wykresu** — nawet realna, niezależna informacja
    (O1, V1: |r| z kontrolą ≤ 0,05) jest o rząd wielkości za słaba. Kolejne cechy z tych źródeł
    = decyzje użytkownika; obiecujący sygnał tego dnia (X1 momentum przekrojowe, +22 %/rok
    nierozstrzygnięte) mieszka w INNEJ formule (przekrój, tygodnie), nie w tym modelu.
68. **MOMENTUM PRZEKROJOWE NA TOP-50 SŁABSZE NIŻ NA TOP-20, A X1 BYŁO WRAŻLIWE NA FAZĘ REBALANSU
    (X2):** top-50 / nogi po 10, 2021-05 → 2026-06: **+0,044 %/dzień [−0,034; +0,121]**, t 1,10,
    +15,9 %/rok, Σ +82 %; rank IC **−0,006 [−0,033; +0,022]** (sygnał nie porządkuje 50 monet);
    33 dni z |r| > 5 % = 52 % sumy; 2022 −20 %; noga short robi wynik. **Druga droga: reguła X1
    (top-20/5) tym samym kodem na siatce formowań X2 (start 2021-05-01) daje +0,024 %/dzień
    (Σ +46 %) zamiast +0,060 (Σ +119 %)** — różnica ≈ 13 %/rok pochodzi z trzech miesięcy
    luty–kwiecień 2021 i z INNEJ FAZY tygodniowego kalendarza rebalansów; CI z jednej fazy
    zaniża niepewność (analog fold-jitter, C2.12). Rodzina B1 po dwóch odczytach: hipoteza ze
    SŁABYM poparciem, bez dowodu; zysk w ogonach i w nodze short, nie w monotonicznym rankingu.
    Metodologicznie: (a) strategie z rebalansem kalendarzowym raportować z rozrzutem po fazach;
    (b) szum nóg z sygnału vs losowych: ×1,55 na top-50 (×1,3 na top-20) — korekta z wniosku 65
    rośnie z szerokością koszyka. Trzeci odczyt na tych danych zakazany; tylko pomiar
    prospektywny (7 faz naraz, ≥ 2 lata) mógłby rozstrzygnąć.
69. **ZMIANA HORYZONTU NIE JEST DROGĄ: MODEL KONTROLNY NA TRZECH BAZACH (1h / 4h / 1d) TRAFIA
    48–50 % NA KAŻDEJ (Y1/Y2, 2026-09-23).** Ten sam model (4 cechy REVERSION w oknach
    natywnych, V = 3 świece, 1,5·ATR, limit po close), zmieniony WYŁĄCZNIE interwał:
    1h → p 48,34 % [47,70; 48,98] vs p* 54,01 %, n 23 334, t_neff −11,74 — NEGATYWNY
    z ogromnym zapasem (41× wymaganego n; 6/6 lat ujemnych; CI w całości PONIŻEJ 50 %);
    4h → 49,58 % vs 53,64 % (wniosek 46); 1d → 50,20 % [47,07; 53,34] vs 51,70 %, n 978 —
    NIEROZSTRZYGNIĘTY przez n, dokładnie jak policzono PRZED przebiegiem (half-width 3,1 pp).
    Trzy obserwacje: (a) krótszy horyzont podnosi próg (koszt/bariera) i NIE wzmacnia sygnału
    — na 1h 63 % timeoutów z p 45,6 %, cechy wskazują kierunek odwrotny (trzeci raz po A1
    i wymuszonym kierunku z Fazy 0); (b) dłuższy horyzont obniża próg do 51,7 % (koszty
    prawie nie ważą), ale próba maleje do ~1 000 i przyrząd traci rozdzielczość — efekt
    52–53 % byłby tam niewidzialny (wniosek 23), a przy barierze 6 % sumy roczne (+92 %/
    −140 %) to szum, nie reżimy; (c) rachunek ex ante zgadzał się z ex post na obu bazach
    (1h: n −16 % przez wyższą abstynencję, hw 0,59 → 0,64 pp; 1d: co do 1 %). Konsekwencja:
    rodzina „kierunek jednoaktywowy z OHLCV" jest zmierzona na trzech interwałach i zamknięta
    na każdym; dalsze badanie horyzontu dziennego wymaga INNEGO zbioru informacyjnego lub
    INNEJ formuły (przekrojowej), nie tego modelu. Odwrócenie znaku na 1h (~51,7 % ex ante,
    pod progiem 54 %) zapisane jako hipoteza post hoc — nie wariant.
70. **TREND TYGODNIOWY NA KOSZYKU TO NAJSILNIEJSZY ŚLAD PROJEKTU — I NADAL NIE DOWÓD (TS1, **[korekta AU1: wniosek 87]**
    2026-09-24).** Momentum w czasie (znak zwrotu 28 dni per moneta, skalowanie zmiennością,
    7 faz) na top-20: +14,8 %/rok netto [−1,7; +31,3], t_neff 1,76 — kryterium niespełnione;
    ponad wszystkimi 100 portfelami H0 (znaki przesunięte w czasie), bootstrap blokowy CI > 0,
    6/6 lat i 7/7 faz dodatnich, bez bety (zawsze-long ~0, korelacja −0,19). Razem z X1 (+22 %/rok,
    t 1,58) to druga konstrukcja „ceny trzymają kierunek przez tygodnie” z dodatnim punktem —
    rodzina tygodniowego momentum na koszyku ma najlepsze poparcie w projekcie, a horyzonty
    godzinowe (Faza 0, M1, A2, Y1) konsekwentnie przeczą. Hamulce: ~24 odczyty w dwa dni
    (Bonferroni → t ~3,0), bez 10 najlepszych dni zostaje +6 %/rok, zbiór informacyjny wciąż
    tylko ceny. Metodologicznie: (a) H0 z niezależnych losowych znaków per moneta jest ZA WĄSKI
    dla portfeli skorelowanych monet (zmienność 3 % zamiast 21 %) — kanoniczne H0 dla reguł
    znakowych na koszyku to prawdziwe znaki przesunięte w czasie; (b) dla użytkownika z 3×:
    pełna dźwignia 3× kapitału na strategii o zmienności ~20 % × 7 daje drag, który zjada zysk
    (CAGR +4,9 %, obsunięcie 90 %) — dźwignię wyznacza cel zmienności, nie sufit giełdy.
    Rozstrzygnąć może tylko test prospektywny na danych od 2026-07-01.
71. **NOWE MONETY ZWYKLE TANIEJĄ, ALE SHORT NA NICH NIE ZARABIA (NL1, 2026-09-24).** Na 569
    pierwszych listingach USDT-M 2021–2026 short 1× przez 14 dni: mediana +13,5 %, 66 % zdarzeń
    zyskownych — typowa nowa moneta spada — ale średnia +2,1 % [−2,7; +6,9], bo 11,8 % zdarzeń
    to podwojenie ceny (likwidacja nawet przy 1×), a funding częściowo wycenia spadek (short
    płaci netto w 41 % okien). Rozkład skrajnie skośny: bez 5 % najgorszych +7,8 %, bez 5 %
    najlepszych −1,2 %. Dźwignia pogarsza: 3× → 41,5 % likwidacji. Lekcja ogólna: gdy
    „zwykle działa” (mediana, trafność), a średnia stoi w miejscu, strategia sprzedaje
    ubezpieczenie od wystrzału — przy dźwigni ogon staje się regułą. Nowe źródło danych
    (archiwum listingów, point-in-time, z wycofanymi) zostaje w repo (`data/fetch_listings.py`).
72. **PIERWSZY POZYTYWNY WYNIK PROJEKTU — I DLACZEGO TO JESZCZE NIE DOWÓD (CP1, 2026-09-24).**
    Premia Coinbase (7 vs 90 dni) jako znak pozycji BTC na tydzień: +32 %/rok [+2; +62], t_neff
    2,09, ponad 98 % H0 — oba pre-rejestrowane warunki spełnione. Przecieku brak (sygnał spóźniony
    o 1/2 dni traci łagodnie: +27,5 / +20,9 %/rok). Ale: (a) ~28 odczytów w dwa dni — próg rodzinny
    t ≈ 2,9 niespełniony; (b) beta 0,36 wobec trendu 28 dni, alfa ponad trend t 1,67; (c) bez 10
    najlepszych dni +16 %/rok. Lekcja metodologiczna: przy licznym programie testów pierwszy
    „POZYTYWNY” wymaga potwierdzenia na danych nieoglądanych, zanim cokolwiek pójdzie do
    kapitału; test opóźnienia sygnału (łagodny spadek vs zapaść) to tani i skuteczny detektor
    przecieku czasowego — stosować przy każdym sygnale z zewnętrznego źródła.
73. **TŁOK NA FUNDINGU NIE ZAPOWIADA KOŃCA TRENDU TYGODNIOWEGO (TF1, 2026-09-24).** Zerowanie
    pozycji trendu po stronie płacącej skrajny funding (Σ 7 dni > 0,63 %, 9,3 % pozycji):
    TF1 − TS1 −1,41 %/rok [−6,58; +3,77] — bez poprawy, punktowo gorzej. Razem z F1 (funding jako
    cecha 4h ≈ 0): funding nie niesie informacji o kierunku ani o końcu ruchu na horyzontach
    4h–tydzień w tych danych.
74. **TREND TYGODNIOWY PRZETRWAŁ OBA SPRAWDZIANY POZA PRÓBĄ, ALE NIEZALEŻNOŚĆ JEST MAŁA (TR1/TP1,
    2026-09-24).** Ta sama reguła na monetach z miejsc 21–50: +14,1 %/rok [−3,0; +31,2], t 1,62 —
    niemal kopia TS1 (+14,8 %), lecz korelacja dzienna 0,86: w krypto „inne monety” to prawie ten
    sam czynnik rynku, więc replikacja przekrojowa daje mało nowej informacji. Na nowych danych
    (78 dni) +0,7 % — brak obalenia. Metodologicznie: replikację w krypto trzeba mierzyć
    korelacją szeregów, nie liczbą monet; jedynym naprawdę niezależnym sprawdzianem jest czas.
75. **POZYCJONOWANIE (OI, FUNDING) NIE WSKAZUJE KIERUNKU NA HORYZONCIE TYGODNIA — TRZECI RAZ
    (TL1, 2026-09-24).** Lewar dokładany za ruchem 7-dniowym na przekroju top-20: IC +0,008
    [−0,024; +0,040], portfel −10,5 %/rok (koszty obrotu). Razem z O1 (OI jako cecha 4h), F1
    (funding jako cecha) i TF1 (funding jako filtr): dane o pozycjonowaniu z Binance nie niosą
    informacji kierunkowej w żadnej z czterech zmierzonych form. Uwaga metodologiczna: H0 z
    sygnałem przesuniętym w czasie może mieć niższą zmienność niż portfel realny (inna
    dywersyfikacja faz) — przy rozbieżności zmienności rozstrzyga t_neff, nie pozycja wobec H0. **[korekta RU4, wniosek 97: na pełnych danych +8,1 %/rok, t 0,62 — nadal NIEROZSTRZYGNIĘTY]**
76. **DŹWIGNIA 3× NA POZYCJI ALTCOINA KOSZTUJE TREND ~3,6 PKT/ROK W LIKWIDACJACH (LQ1, 2026-09-24).**
    Przy izolowanym depozycie = ekspozycja/3 ok. 4,75 % pozycji-tygodni w top-20 kończy się
    likwidacją (ruch > 32 % przeciw pozycji w tygodniu); TS1 spada z +14,8 do +11,3 %/rok.
    Przy 2× (ta sama ekspozycja, depozyt połowa pozycji) koszt ~1,6 pkt. Wniosek dla przełożeń:
    „ta sama ekspozycja” nie znaczy „ten sam wynik” — dźwignia na pozycji zmienia rozkład
    przez likwidacje, zwłaszcza na altcoinach; backtesty na zamknięciach zawyżają wynik.
77. **DWIE SŁABO SKORELOWANE STRATEGIE RAZEM > KAŻDA OSOBNO; HAMULEC PO STRACIE SZKODZI (SZ1,
    2026-09-24).** Trend (2×) i premia Coinbase (3×), korelacja 0,30: po połowie kapitału +19,9 %/rok
    przy obsunięciu 18,9 % (składowe osobno 18,2 % i 34,5 %); budżet ryzyka (cel 20 %) podobnie.
    Hamulec „pół pozycji po −15 %” obciął zwrot do +10,3 % bez zmniejszenia obsunięcia — w
    strategiach trendowych obsunięcie ~15–20 % jest typowe i poprzedza odbicie. Opisowo,
    składowe in-sample.
78. **SKALOWANIA POZYCJI SIŁĄ SYGNAŁU NIE DA SIĘ ZMIERZYĆ NA 5 LATACH (SC1, 2026-09-24).** Różnica
    „siła − znak” przy tej samej średniej ekspozycji ma szum ±13–17 %/rok — przesuwanie pozycji
    między sygnałami samo generuje zmienność; realistyczna poprawa (kilka %/rok) byłaby niewidoczna.
    Rachunek mocy przed obejrzeniem wyniku oszczędził kolejnego odczytu na tych samych danych;
    zostaje prostsza reguła znaku (bez koncentracji ryzyka w skrajnych sygnałach).
79. **SILNIKI DZIENNE NIE WYMYŚLAJĄ ZYSKU Z SZUMU — KONTROLA NEGATYWNA ZALICZONA (NC1, 2026-09-24).**
    TS1, X1 i reguła znaku CP1 na 40 losowaniach cen bez informacji o przyszłości (grube ogony,
    GARCH, czynnik rynkowy): t brutto ≈ 0, fałszywe alarmy 3,3 % [1,3; 8,3]; ten sam silnik z celowym
    zajrzeniem w przyszłość: t ≥ 13 w 40/40. Dodatnie wyniki TS1/CP1 nie są artefaktem kodu (co nie
    czyni ich dowodem). Ogon X1 na 400 losowaniach: dokładnie 5,00 % |t| > 1,96, ale jedno t = 3,62
    — pojedyncze t ≈ 3 na 5,5 roku bywa przypadkiem (~1 na 300–400 przebiegów szumu).
80. **PREMIA COINBASE TO JEDEN CZYNNIK DLA CAŁEGO RYNKU — INNE MONETY JEJ NIE POTWIERDZĄ (CP2,
    2026-09-24).** Premia ETH koreluje z premią BTC 0,95 (poziom), a znak sygnału ETH = BTC w 94 %
    dni (SOL 89 %). Przy korekcie na 2 ramiona test na jednej monecie ma rozdzielczość ±36–37 %/rok,
    czyli moc 34–39 % nawet przy efekcie jak w CP1. Replikacja „wszerz” jest tu pozorna; CP1
    rozstrzygnie tylko czas (dziennik prospektywny BTC). Ogólniej: przed replikacją na innym
    instrumencie zmierz zgodność SYGNAŁÓW — wysoka zgodność = brak nowej informacji.
81. **NA 5,5 ROKU DANYCH DZIENNYCH NOWE ZAKŁADY KIERUNKOWE SĄ ZWYKLE NIEMIERZALNE (SH1, 2026-09-24).**
    10 hipotez spoza OHLCV (Korea, stablecoiny, ETF, FOMC/CPI, odblokowania, Wikipedia, adresy,
    funding, listingi): niepewność 2–5× większa niż realistyczny efekt. Wykrywalne są tylko efekty
    ≥ 20–25 %/rok na koszyku albo kilku % na zdarzenie przy setkach zdarzeń. Filtr wstępny: efekt
    z badań PO publikacji ≥ 1,4 × niepewność — przed kosztowną sondą.
82. **UNIWERSUM BYŁO OBCIĘTE W POŁOWIE ALFABETU — OBA ŚLADY PRZETRWAŁY KOREKTĘ (RU1, 2026-09-24).**
    `data/raw/universe` miał 287 z 685 kontraktów (A–G + 12 z H–Z); koszyk top-20 był inny na
    ~5 z 20 miejsc (brak MATIC, SUI, WLD, OP…). Na pełnych danych: TS1 +11,1 %/rok (było +14,8), X1
    +41,7 % (było +22; ~83 pkt z jednego wystrzału MYX, bez niego +26 %), SZ1 R1 +17 % / spadek 18 %.
    Oba nadal NIEROZSTRZYGNIĘTE. Lekcja: przy każdym nowym uniwersum porównać listę plików z listą
    źródła — błąd przeszedł przez ~10 rund, NC1 go nie łapie (dane syntetyczne).
83. **KOREKTA DANYCH NIE ZMIENIŁA ŻADNEGO WERDYKTU (RU2, 2026-09-24).** TR1 +13,0 %/rok (dodatni 6/6
    lat), X2 +23,1 % (2026 głównie z fundingu), koszt likwidacji 3× −2,4 %/rok, TF1 −1,3 pkt, R1
    −10,6 %/rok — znaki bez zmian. Liczby we wnioskach 57, 64, 68, 70, 73, 74, 76 zastępują RU1/RU2.
84. **TREND DZIAŁA NA ZWYKŁYCH RYNKACH, ALE ZANIKA PO PUBLIKACJI (TX1, 2026-09-24).** Reguła TS1 bez zmian **[korekta AU1: wniosek 87]**
    na 19 rynkach FRED: 1990–2026 +5,1 %/rok, t 2,73 (POZYTYWNY); po 2013 −0,2 %/rok (4/14 lat) — na
    walutach −3,4 %, na ropie +22,9 %, akcjach +7,6 %. Mechanizm istnieje, ale jest „wyjadany” na dojrzałych
    rynkach. ADR-09 szczebel 1(b) dla trendu krypto: NIEROZSTRZYGNIĘTY.
85. **DŁUŻSZE OKNO UCZENIA NIE RATUJE MODELU KIERUNKU (WF1, 2026-09-24).** 365 i 730 dni zamiast 60:
    trafność 49,6 % i 48,5 % (kontrola 50,1 %) przy n ≈ 4 500, oba NEGATYWNE na zwrocie netto. Porażka
    Fazy 0 nie wynikała z krótkiego okna, tylko z braku informacji w cechach z wykresu (wniosek 39).
86. **CYKL HALVINGOWY: WZÓR POWTARZALNY, ALE TO 3 OBSERWACJE (HC1, 2026-09-24).** 0–18 mies. po halvingu
    BTC rósł w 9/9 faz, 18–24 mies. spadał 3/3, w 24–30 mies. trend TS1 tracił 4/4. Opis, nie dowód;
    możliwy użytek jako zasada ryzyka (mniejsza dźwignia 18–30 mies.) — tylko decyzją użytkownika.
87. **AUDYT AU1 — CO BYŁO ZA MOCNO POWIEDZIANE (2026-09-24).** (a) Cechy spoza wykresu (funding, OI,
    DVOL, podaż on-chain, F&G — F1, O1, L1, V1, G1, też M1, A1b, A2.5) dokładane jako 5. cecha do modelu
    60-dniowego NIE zostały zmierzone: ten przyrząd przenosi ~15–17 % przewagi słabej cechy (wyrocznia
    +0,20 %/tr. → 51 % trafności); poprawnie „model z cechą nie zarabia, cecha niezmierzona” (koryguje 67;
    wniosek 85 dotyczy tylko cech z wykresu; 41 nie jest niezależnym potwierdzeniem). (b) Y2 (1d) —
    niezmierzony, nie dowód braku. (c) TL1 liczony na obciętym uniwersum — nie „czwarty dowód”. (d) TS1:
    „bootstrap powyżej zera” (70) nieaktualne po RU1 — przedział ok. −3…+26 %/rok. (e) TX1 (84): po 2013
    „wyraźnie słabnie” (różnica przed/po +8,4 pkt, z 2,17), zera nie da się ani potwierdzić, ani wykluczyć;
    z kosztem finansowania obligacji +4,3–4,5 %/rok, t 2,34–2,40. (f) M1: realny zapas próby ~1,3–1,4×, nie
    1,9×. (g) CP1P = brak informacji, nie informacja przeciw. (h) TR1 od 2021-02 (start z obciętych danych
    był błędny): +15,5 %/rok, t 1,99 — oglądane po fakcie, poniżej progu rodzinnego ~2,9. (i) X1: bez dnia
    MYX t 1,83, bez 5 najlepszych 1,30; funding +49 pkt z +226. „Nierozstrzygnięty” w strategiach
    tygodniowych = za mało lat: moc przy +10 %/rok 25 % (z 1,96).
88. **POPRAWNA DATA STARTU NIE ZMIENIA OBRAZU (RU3, 2026-09-24).** TR1 (trend na miejscach 21–50) od
    2021-02: +15,5 %/rok [+0,2; +30,8], t 1,99, ponad 100 % losowań H0 — kryterium TR1 formalnie spełnione,
    ale: wynik znany z AU1 przed rundą, poniżej progu rodzinnego ~2,9 (~30 odczytów), a cały przyrost
    wobec RU2 (t 1,63) to 82 dni lutego–kwietnia 2021 (Σ +14,0 %); od 2022 opisowo +11,4 %/rok, t 1,32.
    Dodatni 6/6 lat i 7/7 faz (spójność — szczebel 2 ADR-09). X2 jako średnia 7 faz: +21,9 %/rok, t 1,59,
    fazy od +12 do +39 %/rok zależnie od dnia tygodnia — pojedynczej fazy nie cytować. Liczby TR1/X2
    z 83 zastępuje RU3. Nie cytować TR1 jako potwierdzenia; rozstrzyga dziennik prospektywny.
89. **X1 ZALEŻAŁ OD DNIA TYGODNIA (X1F, 2026-09-24).** Ta sama reguła X1 startowana w każdy z 7 dni: pon
    +41,7 %/rok (= X1/RU1, t 1,86), wt +4,9, śr +0,7, czw +4,4, pt +2,1, sob −1,3, nd +21,6; średnia 7 faz
    **+9,5 %/rok [−21,1; +40,1], t 0,61** (bez MYX +17,6, t 1,23; od 2022 +7,5, t 0,44). Dawny wynik był
    najlepszym z siedmiu równoprawnych odczytów, wybranym nieświadomie datą startu 2021-02-01 (poniedziałek).
    Jedno zdarzenie (MYX 7–8.09.2025, cena ×10,6) było w nodze long tylko w fazie poniedziałkowej, w pięciu
    innych w nodze short. Zasada na przyszłość: strategie z przebudową co tydzień liczyć od razu jako
    średnią 7 faz (TS1, R1 i X2/RU3 już tak liczone). X1 — z kandydatów do „śladów bez dowodu”; w dzienniku
    papierowym od 2026-09-25 decyzją użytkownika (bez dźwigni i likwidacji, progi 55,0 / 82,5 %). Przy okazji:
    filtr nazw dziennika pomijał monety z nazwą spoza ASCII (`币安人生USDT` w top-20 2026-05) — poprawione
    przed pierwszym wynikiem (poprawka 4); mnożnik R1 z 23.09: 0,5709 → 0,5700.
90. **DANE SPOZA WYKRESU: ŚLAD JEST, ALE MNIEJSZY NIŻ KOSZT (SW, 2026-09-24).** Osiem cech na BTC 4h, kierunki
    z mechanizmu zapisane z góry, m = 9 (z\* 2,773). Reguły „za/przeciw odchyleniu od mediany 365 dni”: netto
    −0,028 … −0,110 %/tr, górne krańce CI ≤ +0,004 % → efekty ≥ +0,06 %/tr wykluczone; NEGATYWNE: funding,
    L/S dużych graczy („za nimi”), VRP, F&G. Model XGBoost na 7 cechach, okno 365 dni: −0,050 % [−0,091; −0,010],
    t −1,78 (kontrola z cechami wykresu −0,094 %). Przed kosztami: +0,01 … +0,05 %/tr w 6/8 regułach (L/S wszystkich
    kont +0,054 [+0,023; +0,085]), IC niezależne od silnika +0,02 … +0,03 w 5/8 — koszt handlu co 4h ~0,08 %/tr
    zjada to 2–3×. Zastępuje „niezmierzone” z wniosku 87 dla tych cech. Odwrócenie kierunku nie ratuje (płaci ten
    sam koszt). Jedyna otwarta droga: wolniejszy horyzont (mniej transakcji) — NOWA hipoteza, decyzja użytkownika.
91. **PREMIA KOREAŃSKA: INNY SYGNAŁ NIŻ CP1, ALE NIEMIERZALNY (KP1, 2026-09-25).** Upbit KRW-BTC ÷ (spot Binance
    × `DEXKOUS`) w regule CP1: zgodność znaku z CP1 52,8 % [~46; 60] (bootstrap blokowy; przypadek 50,1 %),
    z trendem 28 dni 45,9 % — nie kopia CP1 ani trendu. Przegląd badań (30 źródeł zweryfikowanych): nikt nie
    zmierzył, czy premia przewiduje globalny BTC; kierunek nieznany; od 2024-06 premia BTC ≈ premia USDT
    (mierzy napływ wonów). Założony efekt SR 0,15 wobec progu przyrządu 0,86 SR (±30,9 %/rok) → moc 5 %,
    zysków nie liczono. Ogólnie: na samym BTC z 5 lat danych dziennych przyrząd widzi dopiero SR ≥ ~0,86 —
    filtr „efekt z badań po publikacji ≥ próg” stosować PRZED pobieraniem danych (uzupełnia 81).
92. **PRZYRZĄD PRZEKROJOWY JEST DUŻO CZULSZY NIŻ JEDNOAKTYWOWY (AU2 krok 0, 2026-09-25).** Koszyk top-50 po
    odjęciu średniej przekroju ma ~17,7 niezależnych zakładów tygodniowo [p10 12; p90 21] (surowo 3,2; top-20:
    8,6 vs 2,8) — wniosek 40 („20 monet ≈ 2”) dotyczy ekspozycji kierunkowej, nie koszyka long/short. Szum
    rank IC na prawdziwych zwrotach: se średniego (7 faz, 5,4 roku) 0,008 (top-50) / 0,014 (top-20) → najmniejsze
    wykrywalne IC 0,022 / 0,040; na IR 0,75 trzeba IC ≈ 0,025 brutto (top-50). Dla porównania momentum top-50
    miało IC −0,006 (X2). Użyć jako rachunku mocy każdej strategii przekrojowej (zasada 18). Kroki 1–2 (ML:
    permutacja + siatka sił) — szkic karty, decyzje użytkownika: zbiór cech, budżet przeszukiwania, drugi warunek.
93. **ML NA RANKINGU MONET: UCZCIWY, ALE MAŁO CZUŁY (AU2 kroki 1–2, 2026-09-25).** Pełny pipeline (10 cech + nośnik,
    8 zestawów × 3 modele, walk-forward kwartalny, purging/embargo) na permutowanych zwrotach top-50: 0/40 fałszywych
    alarmów [0; 9 %]. Moc przy sygnale o znanej sile +5/10/15/20/30 %/rok: ML 0/25/35/80/100 %, ranking wprost po
    właściwej cesze 10/80/85/95/100 % — przeszukiwanie kosztuje ~2/3 mocy w zakresie realistycznym; ML nie lepszy niż
    prosty przyrząd tygodniowy (AU1) → ML przekrojowe na tych danych nie startuje. Hipotezy przekrojowe formułować
    jako JEDNĄ regułę z góry. **Błąd przyrządu kanonicznego:** `effective_sample_size` sumuje 50 autokorelacji; suma
    < −0,5 → N_eff ujemne → `summarize_pnl` daje N_eff = 1 (t ≈ 0,4), `summarize_trade_returns` NaN. Błąd tylko
    zaniża pewność (fałszywe „nierozstrzygnięte”, nigdy fałszywe „pozytywne”) **[naprawione w AU3 — wniosek 94]**.
94. **NAPRAWA N_eff NIE ZMIENIA ŻADNEGO DAWNEGO WERDYKTU (AU3, 2026-09-25).** `effective_sample_size`: przy mianowniku
    1 + 2Σρ ≤ 0 zwraca n (zamiast liczby ujemnej, którą `summarize_pnl` zamieniał na 1, a `summarize_trade_returns`
    na NaN). Audyt 59 przebiegów zamrożonych rund (licznik zdarzeń, wydruki przed/po): zdarzenia tylko w K2 i K3,
    wydruki identyczne → 0 zmian. Błąd groził głównie krótkim szeregom (tygodniowe, ~200 obs. — AU2). Rundy od W2
    odtwarzają się na serwerze co do liczby; Faza 0 sprzed W2 — nie (dane od 2021, nie porównywać 1:1).
    Każda przyszła zmiana kanonicznego pomiaru → ten sam audyt (`tools/au3_audit.py`).
95. **NOGI PORTFELA ZARABIAJĄ W RÓŻNYCH CHWILACH (KR1, 2026-09-25).** Tygodniowe korelacje zwrotów netto: TS1–X1 0,35
    (0,28–0,39 zależnie od metody, ±0,11), TS1–CP1 0,24, X1–CP1 0,16; w 10 % najgorszych dni trendu spadają do 0,24 / 0,09 /
    0,04. Portfel 1/σ: współczynnik dywersyfikacji 0,80 (TS1+CP1) → 0,71 z X1. Dywersyfikacja (a nie przełączanie po
    reżimie) jest tu realnym mechanizmem dopasowania do rynku; X1 doda jej, jeśli sam przejdzie drabinę dowodów.
96. **CP1 PO KOREKCIE NA LICZBĘ PRÓB = RZUT MONETĄ (AU4, 2026-09-25).** Deflated Sharpe premii Coinbase: 0,52 przy
    N = 28 odczytach (w chwili CP1), 0,46 przy 40 (dziś), 0,82 nawet przy N = 5 — w całej siatce poniżej 0,95.
    Przy 28 pustych pomysłach najlepszy osiąga t ≥ 2,09 w 40 % przypadków. Historia 2021–2026 nie odróżni CP1 od
    szczęścia; dowód może dać tylko dziennik (dane od 2026-09-24) — zgodnie z ADR-09.
97. **TŁOK LEWARA NA PEŁNYCH DANYCH ODWRACA ZNAK — SZUM (RU4, 2026-09-25).** TL1 na pełnym uniwersum i pełnym panelu OI:
    +8,1 %/rok [−17,5; +33,7], t 0,62 (na obciętych danych −10,5 %, t −1,39); 7 faz od −44 do +35 %/rok. Werdykt bez zmian
    (NIEROZSTRZYGNIĘTY), seria TL zamknięta. Uwaga przyrządu: H0 z przesunięciem sygnału miało tu 6× niższą zmienność niż
    strategia — porównanie z q97,5 H0 było mało warte; decyduje t_neff. Pełny panel OI (185 monet) gotowy w repo danych.
98. **DARMOWE DANE ON-CHAIN NIE POKRYWAJĄ KOSZYKA (P4, 2026-09-25).** CoinMetrics community: przepływy i podaż na giełdach tylko
    dla BTC i ETH (4–10 % koszyka top-20/50), aktywne adresy / MVRV / transakcje 34–46 % koszyka i maleje (2025–26: 30–43 %).
    Brakuje najczęstszych członków (SOL, AVAX, PEPE, SUI, MATIC). Ranking on-chain na darmowych danych — niewykonalny;
    płatny dostawca ma sens tylko przy ≥ ~70 % pokrycia 2021–2026 (sprawdzić przed zakupem).
99. **KOSZTY NIE BLOKUJĄ STRATEGII TYGODNIOWYCH (KO1, 2026-09-25).** Przy zleceniach rynkowych koszt zjada trendowi 0,8 %/rok,
    premii Coinbase 1,5 %, X1 3,3 % (większy obrót). Zlecenia limitowe (90 % wypełnień) oddałyby +0,5 / +1,0 / +2,2 pkt/rok,
    realnie mniej (niekorzystna selekcja wypełnień, C2.12/W1). Obniżka kosztów ma znaczenie dla strategii o dużym obrocie
    (4h — SW, TL1), nie dla nóg dziennika; limity stosować przy realnych pieniądzach, mierząc wypełnienia.
100. **BTC JAK AKCJE TECHNOLOGICZNE, NOGI DZIENNIKA NIEZALEŻNE (KR2, 2026-09-25).** Tygodniowo BTC–Nasdaq 0,30 (2-tygodniowo 0,43),
    rosnąco: 2022 0,43, 2025 0,41, 2026 0,58; z dolarem −0,16, z VIX −0,22; ze złotem, ropą i stopami ≈ 0. Nogi dziennika (trend, X1,
    premia Coinbase) z rynkami tradycyjnymi |ρ| ≤ 0,15 — trend lekko przeciw akcjom (−0,15). Sam BTC nie dywersyfikuje portfela
    akcyjnego; strategie z dziennika tak. Opis, nie prognoza (wyprzedzanie = nowa hipoteza).
101. **PORTFEL DWÓCH NÓG: WAGI Z KORELACJAMI = OBECNE 1/σ; PRZY 5 % DEPOZYTU RYZYKO ≈ 2 % CAŁEGO KAPITAŁU; X1 JAKO TRZECIA NOGA
    POGARSZA (PR1, 2026-09-25).** Dla dwóch nóg równy wkład ryzyka (ERC) to tożsamość z 1/σ (|Δk| 0,0000, z konstrukcji) — dziennik
    bez zmian. Profil R1 na 100 % kapitału strategii (in-sample, bez likwidacji, 2021-05 → 2026-06): +18 %/rok, obsunięcie 18 %,
    najgorszy tydzień −9,7 %, ES95 tygodniowy −5,7 % [−6,5; −4,7] z 14 tygodni ogona. Limit „≤ 5 % kapitału jako depozyt” trzymany
    każdego dnia (Σ k/dźwignia, mediana 49 %; realny depozyt mediana 24 %, max 45 %) → strategia ≈ 10 % całego kapitału → zły
    tydzień ≈ −1 %, najgorsza seria ≈ −1,9 %, zysk ≈ +1,9 pkt/rok całego kapitału. Dołożenie X1: obsunięcie 28 %, tydzień −27,5 %
    (jeden wystrzał MYX), zysk 13 % — X1 tylko w dzienniku papierowym. Punkt odniesienia dla każdej przyszłej reguły
    przełączania lub ważenia: stała mieszanka R1 z tymi liczbami (każdy taki odczyt = nowy wariant).
102. **LIKWIDACJE ZBIERANE OD 2026-09-25 (LK0).** Jedyne darmowe źródło likwidacji to strumień na żywo (próbka: ≤ 1 zdarzenie/s/symbol,
    w kaskadach zaniżony wolumen); archiwum ich nie ma (P3), REST zniknął w 2021, płatni dostawcy nie dokumentują głębokości.
    Dokumentowany adres `wss://fstream.binance.com/ws/…` odpowiada handshake'iem i milczy — nadaje `/market/ws/…` (Binance rozdzielił
    strumienie futures na kategorie; tak łączy się ccxt 4.5.48). Rząd wielkości: ~40 zdarzeń/min, ~30 symboli/90 s, ~2–3 mln USD/min.
    Rodzina E1 (kaskady likwidacji) przestaje być wykluczona danymi dopiero po ≥ 1 roku zbierania; do tego czasu tylko nadzór
    (`--status`, cron co 5 min wznawia proces). Karta hipotezy E1 = rachunek mocy z realnej częstości zdarzeń PRZED odczytem.

## Jak dodać nowy wpis (procedura rundy — CLAUDE.md zasady 11, 14 i 19)

0. **Najpierw gałąź rundy, potem skille** (`clas5-runda`, `clas5-quant` i pozostałe z tabeli
   w zasadzie 19). Rejestr zapisuje każde użycie do pliku bieżącej gałęzi
   `runs/skille/<gałąź>.jsonl`, więc skill wczytany jeszcze na master nie trafi do raportu
   rundy.
1. **PRZED projektowaniem rundy:** przeczytaj tabelę + liczniki + "Wnioski skumulowane" +
   README runów powiązanych z planowaną zmianą. W README nowej rundy wypełnij sekcję
   **"Poprzedzające wyniki"** — które runy motywują/ograniczają projekt i dlaczego runda nie
   powtarza niczego już przetestowanego. Przy pracy z dwóch środowisk (chmura + maszyna
   lokalna) najpierw zsynchronizuj świeży stan repo.
2. Zarejestruj warianty i kryterium sukcesu Z GÓRY (przed obejrzeniem wyniku); dla
   eksperymentu policz MOC statystyczną (Z19: `required_trades`, `min_detectable_hit_rate`).
   Uruchom skrypt (nowe budują na `backtest/checkpoint_lib.py`; raport metodologią checkpointu
   v2 + rozbicie edge'u — CLAUDE.md zasada 12), przechwyć pełny stdout.
3. Utwórz katalog `runs/YYYY-MM-DD_<id>-<slug>/` z `README.md` (sekcje jak w nagłówku tego
   pliku) i `raw_output.txt` (pełny stdout, nieskrócony). Sekcja **„Użyte skille”**: wynik
   `py tools/skill_audit.py raport --galaz <gałąź rundy>` + jedno zdanie, co wniósł każdy
   skill + pominięte skille z tabeli zasady 19 z powodem. Plik `runs/skille/<gałąź>.jsonl`
   commituj razem z rundą.
4. Dodaj wiersz do tabeli (z licznikiem **Warianty**), zaktualizuj WŁAŚCIWY licznik pod tabelą
   (per baza/hipoteza) ORAZ sekcję **"Wnioski skumulowane"**.
5. Zsynchronizuj syntezę w `STATUS.md` §5/§7 i `STATUS.md` — te dokumenty dostają
   TYLKO syntezę i link do katalogu, nie kopię outputu.
