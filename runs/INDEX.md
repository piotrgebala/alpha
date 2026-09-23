# runs/ — spis treści

Katalog na surowy output ciężkich obliczeń (kalibracje, sweepy, testy odporności na realnych
danych). **Konwencja od 2026-09-22 (CLAUDE.md zasada 11): każdy run ma WŁASNY KATALOG**
`runs/YYYY-MM-DD_<id>-<slug>/` zawierający:

- `README.md` — pełny write-up: **ID testu**, **Metadane** (branch/komenda/parametry/dane),
  **Poprzedzające wyniki** (które wcześniejsze runy motywują/ograniczają projekt tej rundy —
  obowiązkowe dla nowych rund, CLAUDE.md zasada 14), **Wynik**, **Co na plus (+) / Co na minus
  (-)**, **Wniosek**, **Rekomendacja**;
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
- **Sonda wykonalnosci carry przekrojowego (P2) — POZA licznikami: 0 wariantow.** Liczy tylko mechanizm (funding − koszt) i rozrzut do rachunku mocy; srednia zwrotu z cen i P&L NIE policzone. Werdykt NIEMIERZALNA ⇒ hipoteza C (carry przekrojowy na perpetualach) NIE dostaje licznika.
- **Kalibracja przyrzadu (Z9, Z19, K1, K2, K3, T4) — POZA licznikami hipotez: 0 wariantow.** Te rundy nie testuja zadnej hipotezy rynkowej: mierza, czy aparat pomiarowy dziala. `oracle` ma sile sygnalu ZNANA Z KONSTRUKCJI, wiec nie ma czego p-hackowac. **Warunek utrzymania zera, zapisany w pre-rejestracji K2: zadna liczba z K1/K2 nie moze byc cytowana jako wynik hipotezy tradingowej.**
- **Model kosztow / wykonanie — POZA licznikami hipotez: 0 wariantow.** C2.12 policzono jako **1 wariant**, bo raportowal werdykt klasyfikacyjny na tych samych danych. H3 **nie** — pre-rejestracja (regula D5) zakazala raportowania trafnosci, CI, z_stat, marginesu i klasyfikacji jako wyniku; liczby te sa w `raw_output.txt` z jawna adnotacja, ze nie uczestnicza w decyzji. Uzasadnienie mechaniczne: koszt moze ruszyc trafnosc WYLACZNIE przez selekcje (inny moment kill-switcha), czyli bylby to szum selekcyjny.
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
41. **EARLY STOPPING DZIALA — A MODEL NIE MA CZEGO SIE NAUCZYC (T4).** W konfiguracji kanonicznej
   (4h, okno 60 dni, `balanced`) ES chroni przed przeuczeniem w 86/86 oknach, a `MIN_VALIDATION_ROWS`
   jest bezczynny (walidacja ~70 wierszy) — ryzyko z Z17b tu nie wystepuje. Ale na danych, ktorych wybor
   nie widzial, nawet idealnie dobrana liczba drzew poprawia strate tylko o 0,7% wobec zgadywania po rowno,
   a najczesciej najlepsze jest 1 drzewo. **Lekcja metodologiczna:** na danych bez sygnalu kazda kalibracja
   hiperparametru „regularyzujacego” (mniej drzew, wieksza walidacja) wyglada jak poprawa, bo optimum to
   „nie ucz sie”. Kalibracja przyrzadu musi sie odbywac na danych ze ZNANYM sygnalem (wyrocznia K1/K2),
   nigdy na realnych danych, na ktorych sygnalu nie ma — inaczej stroimy przyrzad pod slepote.

## Jak dodać nowy wpis (procedura rundy — CLAUDE.md zasady 11 i 14)

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
   pliku) i `raw_output.txt` (pełny stdout, nieskrócony).
4. Dodaj wiersz do tabeli (z licznikiem **Warianty**), zaktualizuj WŁAŚCIWY licznik pod tabelą
   (per baza/hipoteza) ORAZ sekcję **"Wnioski skumulowane"**.
5. Zsynchronizuj syntezę w `STATUS.md` §5/§7 i `STATUS.md` — te dokumenty dostają
   TYLKO syntezę i link do katalogu, nie kopię outputu.
