# TF1 — trend tygodniowy z filtrem tłoku (funding) (2026-09-24)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY (punktowo gorzej):** różnica TF1 − TS1 **−1,41 %/rok
> [−6,58; +3,77]**, t_neff −0,53; filtr wyzerował 9,3 % pozycji i nie poprawił wyniku (TF1
> +13,4 %/rok vs TS1 +14,8 %/rok). Pre-rejestracja `4762d86` → przebieg → wynik w commicie
> scalającym. **Seria TF: 1/1, STOP.** Walidacja (16a): **READY**; przegląd (16c): **Approve**.
> Decyzja użytkownika 2026-09-24: „sprawdź 3 nowe
> hipotezy” — kombinacja zaproponowana jako najsensowniejsza (trend + informacja o tłoku spoza
> wykresu). Seria TS ma STOP; to wariant TS1 dopuszczony decyzją użytkownika i liczony w
> **nowej serii TF, 1/1, STOP**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

TS1 gra long monety w trendzie wzrostowym i short w spadkowym. Pomysł: nie wchodź w long, gdy
wszyscy już są long z dźwignią i płacą za to wysoki funding (i odwrotnie dla shortów), bo taki
tłok zwykle kończy się falą likwidacji. Filtr wyłączyłby ok. 9 % pozycji. Porównujemy ten sam
portfel z filtrem i bez niego, dzień po dniu. Test zobaczy różnicę rzędu 5 % rocznie; mniejszej
nie odróżni od przypadku.

## ID testu

**TF1** — nowa seria TF, 1/1, STOP. Inne progi, okna fundingu, OI zamiast fundingu = warianty.

## Metadane

- Branch: `tf1-trend-filtr-tloku`. Silnik `backtest/ts_momentum.py` z hakiem `keep_fn` (CP1).
- Dane: jak TS1 (`data/raw/universe`, top-20 point-in-time, 2021-02 → 2026-06, funding realny).
- Skrypt: `backtest/run_crowding_tf1.py` (na `runs/ZAMROZONE.txt`), testy
  `tests/test_crowding_tf1.py` (2). Komendy: `PYTHONUTF8=1 py -m backtest.run_crowding_tf1 --moc`
  → `moc.txt`; `PYTHONUTF8=1 py -m backtest.run_crowding_tf1` → `raw_output.txt`.

## Poprzedzające wyniki

- **TS1 (wniosek 70):** +14,8 %/rok, t 1,76. **TR1:** na miejscach 21–50 +14,1 %/rok, korelacja
  z TS1 0,86 (pre-rejestracja `40d604a`; zamknięcie w toku).
- **F1 (wniosek 38):** funding jako cecha modelu 4h — zero. Tu inny horyzont (tydzień) i inna
  rola (filtr tłoku na pozycji trendu), nie predykcja kierunku.
- **Katalog, sekcja I:** overlay nie tworzy informacji, gdy działa na szumie; TS1 jest najlepszym
  sygnałem projektu, a filtr wnosi informację spoza cen (funding).

## Pre-rejestracja

- **Hipoteza:** zerowanie pozycji trendu po stronie przeładowanej lewarem poprawia wynik TS1.
- **Mechanizm:** tłok lewarowanych longów (wysoki dodatni funding) kończy się likwidacjami
  i odwróceniem; trend zostaje, ale jego koniec jest przewidywalny z kosztu lewara.
- **DOKŁADNIE JEDNA zmienna:** filtr: long zerowany, gdy suma fundingu z 7 dni (dzień t włącznie)
  > **0,63 %** (3 × bazowa stawka 0,01 %/8h × 21 rozliczeń); short zerowany, gdy < −0,63 %.
  Próg ABSOLUTNY z góry (masa punktowa fundingu, wniosek 15). N w wagach bez zmian.
- **Kryterium (jedno ramię):** różnica parowana dziennego zwrotu netto TF1 − TS1: POZYTYWNY, gdy
  t_neff > 1,96; NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (`moc.txt`, bez średniej):** wyzerowanych 9,3 % pozycji (członek × dzień);
  sd różnicy 6,13 %/rok; **half-width ±5,17 %/rok**. Oczekiwany efekt mechanizmu: uniknięcie
  części strat w końcówkach trendów ~3–6 %/rok → **MIERZALNA na granicy**; efekty < 5 %/rok
  niewidoczne — zapisane z góry.
- **Kontekst multiple testing:** ~29 odczytów w dwa dni.
- **Czego runda NIE robi:** nie stroi progu, nie zmienia okna fundingu, nie renormalizuje wag.

---

## Wynik

Pełny stdout: `raw_output.txt` (5 s). Dzienne zwroty netto, 1 969 dni, % kapitału.

| portfel | zwrot netto [CI 95 %] | zmienność | t_neff |
|---|---|---|---|
| TF1 (z filtrem) | +13,43 %/rok [−1,54; +28,39] | 17,7 %/rok | +1,76 |
| TS1 (bez filtra) | +14,83 %/rok [−1,68; +31,34] | 19,6 %/rok | +1,76 |
| **TF1 − TS1 (kryterium)** | **−1,41 %/rok [−6,58; +3,77]** | 6,1 %/rok | **−0,53** |

Różnica per rok (Σ): 2021 −4,8 % · 2022 −1,2 % · 2023 +2,2 % · 2024 −2,7 % · 2025 −2,1 % ·
2026 +0,9 %. Nominał brutto TF1 mediana 0,40× (TS1 0,41×). **Werdykt: NIEROZSTRZYGNIĘTY.**

## Co na plus (+) / Co na minus (−)

**(+)** Filtr obniża zmienność proporcjonalnie do zysku (ten sam t_neff) — nie szkodzi jakości
sygnału; test czysty (parowany, ten sam silnik, próg z góry).
**(−)** Brak poprawy: punktowo −1,4 %/rok, 4 z 6 lat ujemne. Usunięcie wyzerowanych pozycji
obniżyło wynik, więc średnio one zarabiały — wysoki funding NIE wskazywał końca trendu na
horyzoncie tygodnia. Efekt
< 5 %/rok byłby niewidoczny (rozdzielczość ±5,2 %/rok). **Kogo nie ma:** pierwsze 7 dni
fundingu (rozbieg) — filtr nieaktywny; członkowie bez znaku/σ̂ jak w TS1.

## Walidacja (zasada 16a)

`data:validate-data`: **READY**. Faza 0 TF1 przeliczona niezależnie (pętla pandas, własny filtr,
bez `keep_fn`): **+11,05 %/rok** = silnik +11,05 %/rok ✓; udział filtrowanych w formowaniach
fazy 0: 9,2 % (skrypt: 9,3 % na wszystkich dniach) ✓. Bramka 16b (`data:statistical-analysis`):
efekt z CI, lata opisowo, rozdzielczość jawnie.

## Przegląd diffu (zasada 16c)

`engineering:code-review`: suma fundingu z 7 dni do dnia t włącznie (rozliczenia 00/08/16 UTC są
znane przed zamknięciem dnia) — test; filtr zeruje tylko stronę tłoku — test; silnik bez zmian.
**Werdykt: Approve** — cienki skrypt na przetestowanym haku, wynik potwierdzony niezależnie.

## Wniosek

**Prostym językiem:** wyłączanie pozycji, gdy „wszyscy już są po tej samej stronie i płacą za
dźwignię”, **nie poprawiło** trendu tygodniowego: wynik wyszedł nawet trochę gorszy (−1,4 %
rocznie), choć w granicach przypadku. Wysoki funding nie zapowiadał końca trendu. Trend
tygodniowy zostaje bez filtra.

## Rekomendacja

1. **Seria TF: 1/1, STOP.** Inne progi/okna zakazane — to byłoby strojenie po wyniku.
2. Informacja o tłoku (funding) na horyzoncie tygodnia nie pomaga ani jako cecha (F1), ani jako
   filtr (TF1) — nie wracać do niej bez nowego mechanizmu.

## Użyte skille

Rejestr `runs/skille/tf1-trend-filtr-tloku.jsonl`: `clas5-runda`, `clas5-quant` (próg absolutny,
filtr jako nośnik nowej informacji, a nie overlay na szumie), `data:validate-data`,
`data:statistical-analysis`, `engineering:code-review`. **Pominięte:** `testing-strategy`
(2 testy pomocników według wzorca TS1), `dataviz` (bez wykresu).
