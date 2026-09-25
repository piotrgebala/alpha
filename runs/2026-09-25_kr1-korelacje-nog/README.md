# KR1 — korelacje nóg portfela: TS1, X1, CP1 (2026-09-25)

> **STATUS: ZAMKNIĘTA (opisowo, 0 wariantów).** Nogi zarabiają w dużej mierze w różnych chwilach:
> TS1–X1 tygodniowo 0,35 (zakres metod 0,28–0,39, ±0,11) → dywersyfikacja **częściowa**; premia Coinbase
> prawie niezależna od obu (0,24 / 0,16; X1–CP1 0,02–0,16). W najgorszych dniach trendu korelacje spadają.
> Dołożenie X1 obniża współczynnik dywersyfikacji portfela z 0,80 do 0,71. Walidacja: **Ready**; przegląd: **Approve**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Dziennik gra dwie strategie naraz (trend tygodniowy + premia Coinbase), z wagami z ryzyka. Portfel sam
„dopasowuje się do rynku” tylko wtedy, gdy nogi zarabiają w RÓŻNYCH momentach. Trend (TS1) i momentum
między monetami (X1) to obie odmiany „ceny trzymają kierunek” — mogą się pokrywać. Mierzymy, jak bardzo,
zanim X1 kiedykolwiek zostałby trzecią nogą.

## ID testu

**KR1** — kontekst: rozmowa o portfelu wielu strategii (ADR-09, dywersyfikacja zamiast przełączania reżimu).

## Metadane

- Branch `kr1-korelacje-nog` (z `master` `00764c3`). Skrypt `backtest/run_kr1_korelacje.py`, testy
  `tests/test_kr1_korelacje.py` (2). Komenda: `PYTHONUTF8=1 py -m backtest.run_kr1_korelacje` → `raw_output.txt`.
- Szeregi: TS1 i X1 (7 faz) na `universe_full` jak RU1/X1F; CP1 jak w CP1. Wspólne okno dni.

## Poprzedzające wyniki

TS1 +11 %/rok (RU1, 82), X1 7 faz +9,5 %/rok t 0,61 (X1F, 89), CP1 +32 %/rok t 2,09 (72); CP1 z trendem
28 dni na BTC: korelacja 0,36 (72); TS1 z rynkiem −0,19 (70); SZ1 (77): portfel trend + Coinbase.

## Pre-rejestracja

- **Miary:** korelacja Pearsona dziennych i tygodniowych (sumy 7 dni) zwrotów netto par nóg; korelacja
  w 10 % najgorszych dni TS1; współczynnik dywersyfikacji portfela 1/σ (zmienność portfela ÷ średnia
  ważona zmienności nóg) dla TS1+CP1 i TS1+CP1+X1.
- **Odczyt (zapisany z góry):** korelacja tygodniowa TS1–X1 ≥ 0,5 → X1 jako trzecia noga daje mało
  dywersyfikacji; < 0,3 → znaczną; pomiędzy → częściową. To samo kryterium dla par z CP1.
  Wynik nie zmienia dziennika (X1 i tak jest tylko papierowo, osobno — decyzja użytkownika).
- **Czego runda NIE robi:** nie liczy przewagi nóg ani portfela, nie stroi wag.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Trzy strategie nie są kopią siebie nawzajem. Trend i momentum między monetami chodzą razem tylko
umiarkowanie (korelacja ~0,35 — dla porównania: 1 = identyczne, 0 = niezależne), a premia Coinbase jest
od nich prawie niezależna. Co ważne, w najgorsze dni trendu pozostałe nogi NIE tracą razem z nim
(korelacje spadają do 0,04–0,24). To znaczy, że portfel złożony z tych nóg naprawdę by się „rozkładał”
ryzyko — jeśli każda z nich okaże się prawdziwa. KR1 nie mówi, CZY nogi zarabiają (to rozstrzyga drabina
dowodów), tylko że składanie ich razem ma sens.

## Wynik

Pełny stdout: `raw_output.txt`. Wspólne dni 1 880 (2021-05-08 → 2026-06-30).

| para | dzienne | tygodniowe (bloki 7 dni) | tyg. kalendarzowe Pearson / Spearman | 10 % najgorszych dni TS1 |
|---|---|---|---|---|
| TS1–X1 | +0,37 | **+0,35** | +0,28 / +0,39 | +0,24 |
| TS1–CP1 | +0,29 | **+0,24** | +0,31 / +0,27 | +0,09 |
| X1–CP1 | +0,09 | **+0,16** | +0,02 / +0,02 | +0,04 |

Zmienność: TS1 18,2 %/rok, X1 35,9 %, CP1 34,8 %. Portfel 1/σ: TS1+CP1 — 19,1 %/rok, współczynnik
dywersyfikacji 0,80; TS1+CP1+X1 — 19,0 %/rok, 0,71 (1 = brak korzyści). Niepewność korelacji tygodniowej
przy ~270 tygodniach: ±0,11 (95 %).

**Odczyt wg reguły:** TS1–X1 0,35 → między 0,3 a 0,5 → **częściowa** dywersyfikacja (druga droga 0,28–0,39 —
na granicy „znacznej”); TS1–CP1 0,24 i X1–CP1 0,16 → **znaczna**.

## Co na plus (+) / Co na minus (−)

**(+)** Te same funkcje co rundy nóg (bez nowych reguł); dwie drogi liczenia korelacji zgodne co do obrazu;
korelacje w złych dniach niższe niż przeciętnie — rzadki i korzystny układ.
**(−)** Korelacje historyczne na 5 latach, ±0,11; zmieniają się w czasie (nie badano okien kroczących).
Współczynnik dywersyfikacji liczony z σ całego okresu (opisowo, nie reguła). **Kogo nie ma:** styczeń–
kwiecień 2021 (rozbieg CP1), funding/likwidacje przy dźwigni (SZ1/LQ1 osobno). KR1 nie zmienia niczego
w ocenie przewagi X1 (t 0,61 — nadal tylko ślad).

## Walidacja (16a), statystyka (16b), przegląd (16c)

`data:validate-data`: druga droga (tygodnie kalendarzowe, Spearman) — TS1–X1 0,28–0,39, TS1–CP1 0,27–0,31,
X1–CP1 0,02 — obraz zgodny; **Ready**. `data:statistical-analysis`: zakresy zależne od metody zamiast jednej
liczby, ±0,11 dla korelacji tygodniowej. `engineering:code-review` (samodzielnie): szeregi z tych samych
funkcji co RU1/X1F/CP1, wspólne okno przez `dropna`, testy mieszanki 1/σ i współczynnika — **Approve**
(runda opisowa na gotowych funkcjach, bez nowej logiki handlowej).

## Wniosek

**Prostym językiem:** trzy kandydatki na strategie zarabiają i tracą w dużej mierze w różnych chwilach —
składanie ich w portfel ma sens. X1 dodałby trochę dywersyfikacji, ale sam jest najsłabszym kandydatem.

**Technicznie:** tygodniowo TS1–X1 0,35 [~0,24; 0,46], TS1–CP1 0,24, X1–CP1 0,16; dywersyfikacja 0,80 → 0,71 z X1.

## Rekomendacja

1. Dziennik bez zmian (X1 i tak liczony osobno, papierowo).
2. Przy ewentualnym szczeblu 4 (realna kwota) — trzecia noga X1 dopiero, gdy sama przejdzie drabinę; KR1
   pokazuje, że wtedy doda dywersyfikacji.
3. Etykieta stanu rynku w dzienniku (tylko zapis) — decyzja użytkownika (zmiana kodu dziennika = Poprawka 7).

## Użyte skille

Rejestr `runs/skille/kr1-korelacje-nog.jsonl`: `clas5-runda` (pre-rejestracja reguły 0,3/0,5 przed przebiegiem),
`clas5-quant` (bez nowego odczytu przewagi), `data:validate-data` (druga droga), `data:statistical-analysis`
(±0,11, zakresy), `engineering:code-review` (Approve). Pominięte: `engineering:testing-strategy` — dwa proste
testy funkcji opisowych według wzorca z AU2 (świadome pominięcie), `dataviz` (bez wykresu).
