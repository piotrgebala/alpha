# AU4 — deflated Sharpe premii Coinbase (CP1): korekta na liczbę sprawdzonych pomysłów (2026-09-25)

> **STATUS: ZAMKNIĘTA — CP1 po korekcie na liczbę prób NIEODRÓŻNIALNY od najlepszego z pustych pomysłów.**
> DSR = 0,52 przy N = 28 (T = N_eff = 1 880); nawet przy N = 5 tylko 0,82. Przy 28 pustych pomysłach najlepszy
> osiąga t ≥ 2,09 w 40 % przypadków (symulacja = wzór). Audyt — 0 wariantów. Walidacja: **Ready**; przegląd: **Approve**.

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

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Premia Coinbase wygląda dokładnie tak, jak wyglądałby najlepszy z ~28 pomysłów, z których żaden nie działa.
Szansa, że jest lepsza niż taki „najlepszy przypadek”, wynosi ~50 % — rzut monetą. Nawet gdybyśmy liczyli
bardzo łagodnie (jakby sprawdzonych pomysłów było tylko 5), wychodzi 82 %, poniżej zwykłego progu 95 %.
**Sama historia nie rozstrzygnie, czy CP1 działa** — dokładnie to założył ADR-09, przenosząc dowód na
dziennik papierowy. Teraz jest to policzone jedną liczbą.

## Wynik

Pełny stdout: `raw_output.txt`. CP1: 1 880 dni, +32,0 %/rok, SR dzienny 0,0482 (roczny 0,92), t 2,09,
t_neff 2,09 (N_eff = 1 880 — brak korekty na autokorelację), skośność +0,31, kurtoza 7,8.

| N prób | próg SR0 (roczny) | oczekiwane max t pod H0 | P(max t ≥ 2,09) (symulacja) | **DSR** |
|---|---|---|---|---|
| 5 | 0,53 | 1,19 | 9 % | 0,82 |
| 10 | 0,69 | 1,57 | 17 % | 0,70 |
| 20 | 0,84 | 1,90 | — | 0,58 |
| **28** | 0,90 | 2,04 | **40 %** | **0,52** |
| 40 | 0,96 | 2,19 | 52 % | 0,46 |

(T = dni i T = N_eff dają to samo, bo N_eff = n.) **Odczyt wg reguły:** DSR 0,52 < 0,80 → **po korekcie
nieodróżnialny od najlepszego z pustych pomysłów.**

## Co na plus (+) / Co na minus (−)

**(+)** Jedna liczba zamiast przybliżonego „progu rodzinnego t ≈ 2,9”; dwie drogi zgodne (wzór vs symulacja:
oczekiwane max 2,04 vs 2,01; P ≥ 2,09: 40 % = 40 %); poprawka na grube ogony (kurtoza 7,8) wbudowana.
**(−)** Próby nie są niezależne (wspólne dane) — efektywne N nieznane; stąd siatka 5–40: werdykt ten sam
w całej siatce (DSR ≤ 0,82). Liczenie prób z liczników INDEX pomija nieformalne podglądy w sesjach — prawdziwe
N może być wyższe (tylko pogarsza). Wzór na oczekiwane maksimum lekko zawyża próg (~2 %) — zachowawczo.
**Kogo nie ma:** TX1 (inne dane), rundy opisowe i niemierzalne (0 odczytów zysku).

## Walidacja (16a), statystyka (16b), przegląd (16c)

`data:validate-data`: druga droga — symulacja 200 000 × N normalnych t: oczekiwane max 2,01 (N = 28) vs wzór 2,04;
P(max ≥ 2,09) 40 % zgodne z 1 − Φ(2,09)^28. **Ready.** `data:statistical-analysis`: siatka N zamiast jednej liczby.
`engineering:code-review` (samodzielnie): wzory zgodne z Bailey & LdP (2014) — mianownik z SR² także przy
normalności (test); szereg CP1 z zamrożonych funkcji rundy CP1. **Werdykt jednym zdaniem: Approve** — dwie czyste
funkcje z testami przeciw symulacji i wzorowi zamkniętemu, bez nowej logiki handlowej.

## Wniosek

**Prostym językiem:** premia Coinbase na historii to tyle, ile daje szczęście przy ~30 próbach. Nie jest to dowód
przeciw niej — ale na pewno nie dowód za. Rozstrzygnie tylko dziennik.

**Technicznie:** DSR(CP1) = 0,52 przy N = 28 (0,46 przy N = 40, 0,82 przy N = 5).

## Rekomendacja

1. CP1 zostaje w dzienniku papierowym bez realnego kapitału (ADR-09) — AU4 to potwierdza liczbowo.
2. Przy odczycie dziennika (~2026-12-25) CP1 oceniać WYŁĄCZNIE na nowych danych (od 2026-09-24).
3. Każdy przyszły „najlepszy z historii” — ten sam rachunek DSR z aktualnym N (skrypt gotowy).

## Użyte skille

Rejestr `runs/skille/au4-dsr-cp1.jsonl`: `clas5-runda` (pre-rejestracja N i reguły przed liczeniem), `clas5-quant`
(liczenie prób z liczników per baza), `data:statistical-analysis` (siatka N, nienormalność), `data:validate-data`
(symulacja jako druga droga), `engineering:code-review` (Approve). Pominięte: `engineering:testing-strategy` — dwa
testy funkcji wzorów według wzorca (świadomie), `dataviz` — bez wykresu.
