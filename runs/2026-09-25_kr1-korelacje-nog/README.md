# KR1 — korelacje nóg portfela: TS1, X1, CP1 (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (przed przebiegiem). Opisowo, 0 wariantów — zwroty nóg są już odczytane
> w ich rundach; KR1 nie ocenia przewagi, tylko to, czy nogi zarabiają w różnych chwilach.

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

_(sekcje poniżej po przebiegu)_
