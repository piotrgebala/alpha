# runs/ — spis treści

Katalog na surowy output ciężkich obliczeń (kalibracje, sweepy seedów, testy odporności na
realnych danych) — konwencja ustalona 2026-09-21 (patrz STATUS.md §13 (zasady pracy operacyjne)).
Każdy plik ma unikalne ID testu (powiązane z numeracją Commitów w `STATUS.md`, gdzie to dotyczy), metadane uruchomienia, pełny surowy output, sekcję **Co na plus
(+) / Co na minus (-)**, i syntezę. Ten plik jest aktualizowany przy każdym nowym pliku w
katalogu — nie duplikuje treści, tylko wskazuje na nią.

| ID | Data | Plik | Krótki opis | Wynik |
|---|---|---|---|---|
| C2.5 | 2026-09-21 | [2026-09-21_c2.5-threshold-calibration.md](2026-09-21_c2.5-threshold-calibration.md) | Kalibracja progów reguły regime (`trend_threshold`/`range_threshold`) — 4 kandydaci wybrani ze struktury dyskretnego wsparcia `direction_persistence_10`, pełny walk-forward + 10-seed sweep | **NO-GO** (wszyscy 4 kandydaci) — hipoteza "zła kalibracja progów" falsyfikowana; baseline (0.7/0.3) zostaje bez zmian |
| C2.6 | 2026-09-21 | [2026-09-21_c2.6-timeframe-robustness.md](2026-09-21_c2.6-timeframe-robustness.md) | Test odporności hipotezy na timeframe danych (5m referencja vs 1h vs 4h, agregowane z 5m) — czy szersza bariera ATR-vs-koszt na grubszych świecach przywraca edge | **NO-GO** (1h i 4h) — mechanizm bariera-vs-koszt naprawiony (0% świec arytmetycznie niewykonalnych), ale edge kierunkowy nadal nieobecny (~49% trafności) albo ujemny (~41% na 4h) |

## Jak dodać nowy wpis

1. Uruchom skrypt analityczny (poza pytest, np. `backtest/calibrate_regime_thresholds.py`,
   `backtest/checkpoint_timeframe_robustness.py`), przechwyć pełny stdout.
2. Zapisz `runs/YYYY-MM-DD_<slug>.md`: sekcje **ID testu**, **Metadane** (branch/commit/komenda/
   parametry/dane), **Metodologia** (jeśli dotyczy), **Wynik** (tabela), **Co na plus (+)**,
   **Co na minus (-)**, **Wniosek**, **Rekomendacja** (bez automatycznego wyboru "zwycięzcy" —
   decyzja zawsze przy użytkowniku), **Pełny surowy output** (blok kodu).
3. Dodaj wiersz do tabeli w tym pliku (ID, data, link, krótki opis, wynik).
4. Zsynchronizuj skrót w `STATUS.md` z linkiem do pliku w `runs/` —
   te dokumenty dostają TYLKO syntezę, nie kopię pełnego outputu.
