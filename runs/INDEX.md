# runs/ — spis treści

Katalog na surowy output ciężkich obliczeń (kalibracje, sweepy, testy odporności na
realnych danych) — konwencja ustalona 2026-09-21 (patrz TASKS.md, "Zasada pracy: `runs/*.md`").
Każdy plik ma unikalne ID testu (powiązane z numeracją Commitów w `IMPLEMENTATION_PLAN.md`/
`TASKS.md`, gdzie to dotyczy), metadane uruchomienia, pełny surowy output, sekcję **Co na plus
(+) / Co na minus (-)**, i syntezę. Ten plik jest aktualizowany przy każdym nowym pliku w
katalogu — nie duplikuje treści, tylko wskazuje na nią.

Kolumna **Warianty** (Z4, od 2026-09-21) to jawna księga budżetu statystycznego (multiple
testing): ile WARIANTÓW HIPOTEZY porównano z wynikiem na tych samych danych w danej rundzie.
"0 (diagnostyka)" = runda opisowa/metodologiczna, bez testowania wariantu hipotezy. Suma tej
kolumny rośnie z każdą rundą — im większa, tym ostrożniej trzeba traktować pojedynczy
"obiecujący" wynik (docs/rag/02, protokół rozszerzania feature setu, punkt 1).

| ID | Data | Plik | Krótki opis | Warianty | Wynik |
|---|---|---|---|---|---|
| C2.5 | 2026-09-21 | [2026-09-21_c2.5-threshold-calibration.md](2026-09-21_c2.5-threshold-calibration.md) | Kalibracja progów reguły regime (`trend_threshold`/`range_threshold`) — 4 kandydaci wybrani ze struktury dyskretnego wsparcia `direction_persistence_10`, pełny walk-forward + 10-seed sweep | 4 | **NO-GO** (wszyscy 4 kandydaci) — hipoteza "zła kalibracja progów" falsyfikowana; baseline (0.7/0.3) zostaje bez zmian |
| C2.6 | 2026-09-21 | [2026-09-21_c2.6-timeframe-robustness.md](2026-09-21_c2.6-timeframe-robustness.md) | Test odporności hipotezy na timeframe danych (5m referencja vs 1h vs 4h, agregowane z 5m) — czy szersza bariera ATR-vs-koszt na grubszych świecach przywraca edge | 2 | **NO-GO** (1h i 4h) — mechanizm bariera-vs-koszt naprawiony (0% świec arytmetycznie niewykonalnych), ale edge kierunkowy nadal nieobecny (~49% trafności) albo ujemny (~41% na 4h) |
| C2.7 | 2026-09-21 | [2026-09-21_c2.7-feature-candidate-screening.md](2026-09-21_c2.7-feature-candidate-screening.md) | Przegląd 8 kandydatek nowych cech (4 rodziny) PRZED testem OOS: macierz korelacji Spearman cecha-cecha (redundancja) + korelacja cecha-target per regime (opisowa/eksploracyjna) | 0 (screening opisowy; 34 korelacje cecha-target obejrzane bez selekcji) | **Redundancja:** `bb_pctb_20` odrzucony (corr=1,000 z `price_zscore_20`); `adx_14` jedyny kandydat nisko skorelowany z resztą registry. **Target:** brak sygnału w żadnej z 17 cech (\|corr\|<0,065) — spójne z NO-GO C2.5/C2.6, decyzja o dalszym kroku przy użytkowniku |
| C2.8 | 2026-09-21 | [2026-09-21_c2.8-adx14-oos-evaluation.md](2026-09-21_c2.8-adx14-oos-evaluation.md) | Formalny test OOS: `adx_14` dodane do `MOMENTUM_FEATURES` (Test 1/trend), `REVERSION_FEATURES` niezmienione — pełny walk-forward + 10-seed sweep, baseline vs kandydat | 1 | **NO-GO (ogólnie, oba warianty)** — `trend` poprawia się z NO-GO do WARUNKOWY (mean_sharpe -8,46→-7,11), ale efekt opiera się na 1 foldzie ledwo przekraczającym zero (n_valid_folds=4); `range` bez zmian. Decyzja o promocji do `MOMENTUM_FEATURES` przy użytkowniku. **Aktualizacja C2.9:** poprawa +0,61 to ~0,2σ zmierzonego szumu fold-jitter — nierozstrzygalna |
| C2.9 | 2026-09-21 | [2026-09-21_c2.9-measurement-methodology.md](2026-09-21_c2.9-measurement-methodology.md) | Naprawa metodologii pomiaru (Backlog Z1–Z4+Z13): sweep fold-jitter (offset startu okien walk-forward 0–9 dni) ZAMIAST pustego sweepu seedów (XGBoost deterministyczny — std=0,0000 nic nie mierzył), per-fold t-stat, pooled Sharpe per regime, N_eff wpięte do raportu | 0 (diagnostyka/metodologia) | **NO-GO odporne na fold-jitter: 10/10 offsetów ujemne** (zakres [-15,9; -6,2], σ≈3,1). Pooled: zwrot per trade **istotnie ujemny w OBU reżimach** (range t=-7,15; trend t=-2,91, po N_eff -2,63). Zmierzony szum σ≈3,1 czyni porównania wariantów o Δ<~3 nierozstrzygalnymi na rocznych danych → priorytet Z5 (dłuższa historia) |

| C2.10 | 2026-09-21 | [2026-09-21_c2.10-extended-history-z5.md](2026-09-21_c2.10-extended-history-z5.md) | Backlog Z5: historia danych wydłużona do 3 lat (2023-07-01→2026-07-01, 315 648 świec 5m, zero dziur, overlap ze starym oknem identyczny co do bajtu) — NOWA BAZA checkpointu v2 (kanoniczny przebieg + sweep fold-jitter); pipeline niezmieniony | 0 (nowa baza danych) | **NO-GO, 21/144 ważnych foldów** (odsetek 14,6% — jak na roku: strukturalnie, nie ilościowo). Pooled t-stat **range -10,47 / trend -5,51** (N_eff: -7,34 / -4,04) — istotnie ujemny zwrot per trade w obu reżimach z dużym zapasem. Fold-jitter 10/10 ujemne, σ≈2,5 bez outliera (offset 9: -189, artefakt per-fold Sharpe przy n≈kilka). Odkrycie: bramka kosztowa blokuje **98% sygnałów `range`**, `trend`=0,53% świec → 61/72 foldów pominiętych — dłuższa historia tego nie naprawi (→ Z7/Z6/Z10) |

**Suma wariantów hipotezy przetestowanych na tych samych danych (2025-07→2026-07 BTC 5m): 7**
(4 progi + 2 timeframe'y + 1 cecha), plus 34 obejrzane korelacje opisowe (C2.7).

| C2.11 | 2026-09-21 | [2026-09-21_c2.11-edge-instrumentation.md](2026-09-21_c2.11-edge-instrumentation.md) | Instrumentacja edge'u (Runda 1/4 programu „droga do GO"): rozbicie werdyktu na człony nierówności **(2p−1)·B > C** — `compute_hit_rate` (trafność kierunku z `gross_pnl`, z-stat, CI), `break_even_hit_rate`, `summarize_edge_by_regime` wpięte do kanonicznego raportu. Pipeline nietknięty | 0 (instrumentacja pomiaru) | **Werdykt bit-identyczny z C2.10** (regresja baseline'u). Diagnoza zmienia się jakościowo: trafność **51,9% / 50,6%** (z=+0,87 / +0,25 — nieistotnie powyżej monety, ale NIE odwrócona) vs wymagane **75,8% / 64,9%**. Luka **−23,9 pp** (`range`) i **−14,2 pp** (`trend`) → NO-GO jest przesądzone **geometrią wypłaty**, nie błędnym kierunkiem sygnału |

| C2.12 | 2026-09-21 | [2026-09-21_c2.12-execution-cost-model.md](2026-09-21_c2.12-execution-cost-model.md) | Backlog Z6 (Runda 2/4 „droga do GO"): realistyczny model wykonania — maker na wejściu i TP, taker na SL/timeout, slippage tylko na nogach taker; kolumna `exit_reason` w journalu; `execution_model` = `taker_only` / `maker_limit` | 1 | **NO-GO (nadal), ale mechanizm zadziałał:** koszt **−52%** (0,140%→0,067%), foldy ważne **21→54**, transakcje `range` **530→7 155**, zwrot per trade **+35%/+39%**, margines **−23,9→−15,5 pp** (`range`) i **−14,2→−9,1 pp** (`trend`) — ok. połowa luki domknięta. Efekt tłumiony sprzężeniem: tańszy koszt wpuszcza sygnały o **węższej barierze** (B −25%/−19%). **Ostrzeżenie pomiarowe:** `mean_sharpe` rozjechał się (−12,4→−59,6 przy LEPSZEJ ekonomice per trade), fold-jitter σ 3,1→75,7, spójność znaku 100%→80% — per-fold Sharpe przestał być wiarygodnym przyrządem; nośne są pooled t i margin |

| C2.13 | 2026-09-21 | [2026-09-21_c2.13-confidence-threshold.md](2026-09-21_c2.13-confidence-threshold.md) | Runda 3/4 „droga do GO": pre-rejestrowany próg pewności `q=0,75` liczony na foldzie TRENINGOWYM, stosowany OOS (`_train_fold_confidence_threshold`, `confidence_quantile`); baseline vs kandydat przez `evaluate_confidence_threshold.py` | 1 | **HIPOTEZA SFALSYFIKOWANA — reguła STOP uruchomiona.** `range` margin −15,5→−14,7 pp (z_margin **−17,1**), `trend` trafność **49,9%→45,5%** (−4,3 pp, w stronę PRZECIWNĄ do przewidywanej), margin −9,1→−13,2 pp (z_margin **−2,66**). Kryterium `z_margin>2` niespełnione w żadnym reżimie, klasyfikacja NO-GO→NO-GO. Monotoniczny „skill" z pomiaru przed programem okazał się **artefaktem selekcji post hoc** (kwartyl wybrany po zobaczeniu wyniku, na danych zpoolowanych). **Runda 4 (Z7) NIE uruchomiona** — zgodnie z regułą STOP. Decyzja Z10 przy użytkowniku |

| Z16 | 2026-09-22 | [2026-09-22_z16-regime-coherence.md](2026-09-22_z16-regime-coherence.md) | Backlog II/Z16: pomiar SPÓJNOŚCI bramki reżimu z horyzontem etykiety — `agents/regime_coherence.py` (`regime_episodes`, `windows_fully_inside`, `coherence_table`, `is_rule_admissible`) + przesiew 6 kandydatów na regułę reżimu. Bez uruchamiania modelu | 0 (pomiar specyfikacji) | **Hipoteza wyjaśniająca POTWIERDZONA:** w `trend` tylko **0,49%** świec ma etykietę opisującą ruch wewnątrz własnego reżimu (mediana epizodu **2 świece** vs horyzont **12**); w `range` 21,1% (mediana 5). **Z8 DOMKNIĘTY za 0 wariantów:** wymagane B = **4,21%** ceny (30,7×) => horyzont **~39 dni** vs najdłuższy epizod **5h15m**; w `trend` `2p−1 < 0`, więc żadna bariera nie pomaga. **Kluczowa asymetria:** `range` daje się uspójnić (wygładzanie 12 => mediana **39** świec przy udziale **46,9%**), `trend` NIE (wygładzanie wydłuża epizody, ale udział zapada do 0,05–1,5%) |

**Suma wariantów na nowej bazie (2023-07→2026-07 BTC 5m, od C2.10): 0** — licznik rozwidla się
per zbiór danych; wyniki C6–C2.9 pozostają zamrożone na starym oknie i nie są porównywalne 1:1.
C2.11 to instrumentacja (0 wariantów); C2.12 to +1 wariant (model kosztów); C2.13 to +1 wariant
(próg pewności) => **licznik = 2**. Z16 to pomiar specyfikacji (0 wariantów) — licznik nadal **2**.

## Jak dodać nowy wpis

1. Uruchom skrypt analityczny (poza pytest; od C2.9 nowe skrypty budują na
   `backtest/checkpoint_lib.py` — patrz `backtest/run_checkpoint_v2.py`), przechwyć pełny stdout.
2. Zapisz `runs/YYYY-MM-DD_<slug>.md`: sekcje **ID testu**, **Metadane** (branch/commit/komenda/
   parametry/dane), **Metodologia** (jeśli dotyczy), **Wynik** (tabela), **Co na plus (+)**,
   **Co na minus (-)**, **Wniosek**, **Rekomendacja** (bez automatycznego wyboru "zwycięzcy" —
   decyzja zawsze przy użytkowniku), **Pełny surowy output** (blok kodu).
3. Dodaj wiersz do tabeli w tym pliku (ID, data, link, krótki opis, **Warianty** — ile wariantów
   hipotezy porównano z wynikiem w tej rundzie, wynik) i zaktualizuj sumę wariantów pod tabelą.
4. Zsynchronizuj skrót w `IMPLEMENTATION_PLAN.md`/`TASKS.md` z linkiem do pliku w `runs/` —
   te dokumenty dostają TYLKO syntezę, nie kopię pełnego outputu.
