# AU4 — deflated Sharpe premii Coinbase (CP1): korekta na liczbę sprawdzonych pomysłów (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (przed przebiegiem). Audyt — 0 wariantów, POZA licznikami (CP1 odczytany
> w swojej rundzie; AU4 tylko przelicza jego istotność z uwzględnieniem liczby prób).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Premia Coinbase (CP1) ma najlepszy wynik w projekcie (t = 2,09), ale wybraliśmy ją spośród wielu
sprawdzonych pomysłów. Gdy sprawdza się dużo pustych pomysłów, najlepszy z nich i tak wygląda dobrze.
AU4 liczy jedną liczbę: jakie jest prawdopodobieństwo, że CP1 jest lepszy niż „najlepszy z N pustych”,
dla uczciwie policzonego N.

## Metadane

- Branch `au4-dsr-cp1` (z `master` `189622e`). Skrypt `backtest/run_au4_dsr.py`, testy `tests/test_au4_dsr.py` (2).
  Komenda: `PYTHONUTF8=1 py -m backtest.run_au4_dsr` → `raw_output.txt`.
- Szereg: dzienne zwroty netto CP1 (średnia 7 faz) tą samą drogą co `run_coinbase_cp1` (reguła zamrożona).

## Poprzedzające wyniki

CP1 (72): +32 %/rok, t_neff 2,09; README CP1: próg rodzinny Bonferroni t ≈ 2,9 przy ~28 odczytach.
ADR-09: CP1 bez realnego kapitału do nowego dowodu. AU3 (94): N_eff naprawiony — bez wpływu na CP1.

## Pre-rejestracja

- **Liczba prób (z `runs/INDEX.md`, przed obliczeniem):** odczyty zysku na bazie 2021–2026 (krypto):
  N1 1, W 3, A 7, R 1, C 2, X 1, O 1, L/V/G 3, X2 1, Y1/Y2 2, TS1 1, TR1/TP1 2, NL 1, CP 1, TF 1, TL 1, WF 2,
  SW 9 = **40** dziś; **~28 w chwili odczytu CP1** (README CP1). Rundy opisowe/kalibracyjne i niemierzalne = 0;
  TX1 (inne dane) poza liczeniem. Próby dzielą dane i są skorelowane → efektywne N mniejsze: siatka
  **N = 5, 10, 20, 28, 40**.
- **Metoda:** DSR (Bailey & López de Prado 2014), V[SR] = 1/T pod H0, skośność i kurtoza CP1, T = liczba dni
  oraz T = N_eff (autokorelacja). Przybliżenie oczekiwanego maksimum lekko zawyża próg (~2 % przy N = 10;
  test vs symulacja) — zachowawcze.
- **Odczyt (reguła z góry):** główna liczba = DSR przy **N = 28, T = N_eff**. DSR ≥ 0,95 → CP1 „przeżywa
  korektę na liczbę prób”; 0,80–0,95 → „na granicy”; < 0,80 → „po korekcie nieodróżnialny od najlepszego
  z pustych pomysłów”. Wynik NIE zmienia dziennika (CP1 i tak tylko papierowo) ani ADR-09.
- **Czego runda NIE robi:** nie zmienia reguły CP1, nie liczy nowych wariantów.

---

_(sekcje poniżej po przebiegu)_
