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
| S1 | 2026-09-22 | [s1-single-regime-4h](2026-09-22_s1-single-regime-4h/README.md) | **NOWA SERIA:** architektura jednoreżimowa (`range`, bez `trend`) na natywnych świecach 4h, historia 6,8 roku, V=3, walk-forward 60/28/28. Konfiguracja ZAMROŻONA w pre-rejestracji Z5b przed uruchomieniem | 1 (nowa seria) | **KRYTERIUM NIESPEŁNIONE, rozstrzygająco.** n=1 037 (>925, klauzula nierozstrzygalności nie weszła). Trafność **48,60%**, CI [45,56%; 51,64%] — **górny kraniec PONIŻEJ progu 53,07%**, więc z 95% pewnością trafność jest niższa od progu opłacalności. Bramka kosztowa odrzuciła **0%** sygnałów (geometria naprawiona — nie pomogło). `mean_sharpe` −0,59 zamiast −60, co potwierdza, że patologia z C2.12 była artefaktem małych foldów. **REGUŁA STOP URUCHOMIONA** — koniec tej linii hipotezy |

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

## Wnioski skumulowane (stan wiedzy — aktualizowany po KAŻDEJ rundzie)

> Czytane PRZED projektowaniem każdej nowej rundy (CLAUDE.md zasada 14). Każdy punkt ma źródło
> w konkretnym runie — nie powtarzaj przetestowanych wariantów.

1. **Hipoteza dwureżimowa (trend/range, 5m) jest po serii C2.5–C2.13 wyczerpana jako kierunek.**
   NO-GO na starej bazie (5 niezależnych testów, odporne na fold-jitter — C2.9) i na nowej,
   3-letniej bazie (C2.10, pooled t: range −10,47 / trend −5,51). Reguła STOP programu
   „droga do GO" uruchomiona po sfalsyfikowaniu progu pewności (C2.13).
2. **Blokada leży w geometrii wypłaty, nie w kierunku sygnału** (C2.11): trafność ~50–52%
   (po naprawie przecieku early stopping: **50,38%** w `range` — najczystszy pomiar, Z17+Z21)
   wobec wymaganych 75,8%/64,9% na 5m. Edge kierunkowy nie istnieje w żadnej składowej
   (bariery vs timeouty rozbite w Z18).
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
10. **STAN PO S1: obie architektury (dwureżimowa 5m/1h/4h i jednoreżimowa 4h) wyczerpane.**
   Rekomendacja: **Z10 opcja 1 — udokumentowane zamknięcie Fazy 0 wynikiem negatywnym**
   (decyzja bramkowa przy użytkowniku). Ewentualne NOWE hipotezy (funding rate jako sygnał,
   inny instrument, target inny niż kierunek — np. zmienność) wymagają własnej pre-rejestracji,
   własnego licznika i własnej reguły STOP — żadna nie startuje bez decyzji użytkownika,
   bo reguła STOP właśnie zadziałała.

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
5. Zsynchronizuj syntezę w `IMPLEMENTATION_PLAN.md` §5/§7 i `TASKS.md` — te dokumenty dostają
   TYLKO syntezę i link do katalogu, nie kopię outputu.
