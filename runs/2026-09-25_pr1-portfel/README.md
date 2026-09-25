# PR1 — reguły portfela nóg dziennika pod szczebel 4 (mała realna kwota) (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (przed przebiegiem). Opisowo, 0 wariantów — zwroty nóg są już odczytane;
> PR1 nie mierzy przewagi, tylko profil ryzyka portfela przy zapisanych z góry regułach alokacji.
> Decyzja o realnym kapitale (szczebel 4 ADR-09) należy do użytkownika po odczycie dziennika ~2026-12-25.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Dziennik dzieli ryzyko między trend i premię Coinbase według zmienności (1/σ), z celem 20 %/rok. Przy
realnych pieniądzach trzeba wiedzieć z góry: ile można stracić w zły tydzień, w zły miesiąc i w najgorszej
serii, oraz jak przełożyć „najwyżej 5 % kapitału jako depozyt” na wielkość strategii. PR1 liczy to na
historii nóg i sprawdza, czy wagi liczące korelacje (ERC — każda noga wnosi tyle samo ryzyka do portfela)
zmieniałyby coś wobec obecnych 1/σ. Uczciwie z góry: przy DWÓCH nogach ERC i 1/σ to matematycznie to samo;
różnica może się pojawić dopiero przy trzech (gdyby X1 kiedyś dołączył).

## Metadane

- Branch `pr1-portfel` (z `master` `042dceb`). Skrypt `backtest/run_pr1_portfel.py`, testy `tests/test_pr1_portfel.py` (5).
  Komenda: `PYTHONUTF8=1 py -m backtest.run_pr1_portfel` → `raw_output.txt`.
- Dane: dzienne zwroty netto nóg przy k = 1 z `run_kr1_korelacje.legs()` (TS1 i X1 na `universe_full`, CP1 jak CP1;
  wspólne okno 2021-05-08 → 2026-06-30, 1 880 dni). Reguły R0/R1 z `sizing.apply_rules` bez zmian (parametry
  dziennika: cel 20 %/rok, sufit 2, EWMA com 45, krok 7 dni, rozbieg 60 — SZ1); ERC nowa funkcja z tymi samymi
  parametrami; dźwignie nóg jak w dzienniku: trend 2×, CP1 3×, X1 1×.

## Poprzedzające wyniki

SZ1 (77): R1 (budżet ryzyka) ~+19 %/rok, obsunięcie ~18–19 %, depozyt ~23 %; hamulec po stracie szkodzi.
KR1 (95): korelacje nóg 0,16–0,35, w złych dniach niższe. KO1 (99): koszty nie są wąskim gardłem. ADR-09:
szczebel 4 = ≤ 5 % kapitału jako depozyt, dźwignie jak w dzienniku, STOP portfela 27,6 %.

## Pre-rejestracja (opisowo)

- **Zestawy nóg:** {TS1, CP1} (dziennik) i {TS1, CP1, X1} (gdyby X1 dołączył).
- **Reguły:** R0 równo; R1 = dziennik (1/σ); ERC (równy wkład ryzyka z korelacjami). Bez hamulca (SZ1: szkodzi).
- **Miary (na 100 % kapitału strategii):** CAGR, zmienność, max obsunięcie, najgorszy dzień/tydzień/miesiąc,
  ES 95 % tygodniowy (średnia 5 % najgorszych tygodni), ES 99 % dzienny; mediany i p10–p90 mnożników; depozyt
  jako udział kapitału (Σ k/dźwignia).
- **Przełożenie ADR-09:** depozyt 5 % całego kapitału → kapitał strategii = 5 % / medianowy udział depozytu;
  straty w % CAŁEGO kapitału.
- **Odczyt:** opisowy; żadna reguła nie jest „wybierana” po wyniku. Oczekiwanie zapisane z góry: dla 2 nóg
  |k R1 − k ERC| ≈ 0; dla 3 nóg ERC przesuwa wagę ku nodze najmniej skorelowanej. Punkt odniesienia dla każdej
  przyszłej reguły przełączania = stała mieszanka R1 (liczby z tej rundy).
- **Czego runda NIE robi:** nie zmienia dziennika, nie stroi celu zmienności ani sufitu, nie mierzy przewagi
  (składowe in-sample — liczby to profil ryzyka, nie prognoza).

---

_(sekcje poniżej po przebiegu)_
