# KO1 — koszty wykonania nóg dziennika: zlecenia rynkowe vs limitowe (2026-09-25)

> **STATUS: ZAMKNIĘTA (opisowo, 0 wariantów).** Koszty wykonania są małe dla nóg dziennika: trend 0,8 %/rok,
> premia Coinbase 1,5 %/rok; większe dla X1 (3,3 %/rok). Zlecenia limitowe (90 % wypełnień) oddałyby +0,5 / +1,0 /
> +2,2 pkt/rok — przed niekorzystną selekcją wypełnień. Koszty nie są wąskim gardłem trendu ani CP1.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Wszystkie wyniki projektu liczone są tak, jakby każde zlecenie było rynkowe (drożej, ale na pewno się
wykona). Zlecenia z limitem są ~3,5× tańsze, ale nie zawsze się wypełniają. KO1 pokazuje, ile rocznie
kosztuje dziś wykonanie trendu, momentum X1 i premii Coinbase i ile dałoby się oszczędzić limitami.

## Metadane

- Branch `ko1-koszty-wykonania` (z `master` `041fb49`). Skrypt `backtest/run_ko1_koszty.py`, test `tests/test_ko1_koszty.py`.
  Komenda: `PYTHONUTF8=1 py -m backtest.run_ko1_koszty` → `raw_output.txt`.
- Silniki i dane jak KR1 (TS1 i X1 na `universe_full`, CP1 jak w CP1).

## Poprzedzające wyniki

C2.12: model maker/taker na BTC 4h domknął ~połowę luki (NO-GO bez zmian); W1: limit po zamknięciu wypełnia się w 99,4 %,
wejście „na cofnięciu” traci (t −3,9) — niekorzystna selekcja wypełnień; SW (90): ślad przed kosztami < koszt 0,08 %;
KR1 (95): korelacje nóg; RU4 (97): koszty TL1 ~5 %/rok.

## Pre-rejestracja

- **Scenariusze (z góry):** taker 0,07 % / maker 90 % wypełnień 0,025 % / maker 100 % 0,02 % za stronę; dodatkowo „bez kosztów”
  jako punkt odniesienia.
- **Miary:** średni zwrot netto %/rok każdej nogi w każdym scenariuszu; koszt taker = zwrot bez kosztów − zwrot taker;
  zysk z limitów = maker 90 % − taker.
- **Odczyt:** opisowy; liczba ta NIE zmienia werdyktów nóg ani dziennika (dziennik zostaje przy taker — konserwatywnie).
  Realny zysk z limitów niższy niż policzony (niemodelowana niekorzystna selekcja) — zmierzy go dopiero dziennik wykonania.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Strategie tygodniowe handlują rzadko, więc koszty zjadają im mało: trend traci na kosztach mniej niż 1 % rocznie,
premia Coinbase 1,5 %. Zlecenia z limitem oddałyby z tego pół punktu i punkt rocznie — miło, ale to nie zmienia
obrazu. Więcej (ok. 2 punkty) dałyby tylko X1, który obraca koszykiem częściej. **Wcześniejszy szacunek z rozmowy
(„2–4 punkty rocznie”) był za wysoki dla trendu i CP1** — liczył się z kosztów TL1, który handluje dużo częściej.

## Wynik

Pełny stdout: `raw_output.txt`. Wspólne okno trzech nóg (od 2021-05-08, jak KR1 — stąd TS1 +8,9 %/rok zamiast
+11 % z RU1 na własnym oknie).

| noga | bez kosztów | taker 0,07 % | maker 90 % (0,025 %) | maker 100 % (0,02 %) | koszt taker | zysk maker 90 % |
|---|---|---|---|---|---|---|
| TS1 (trend) | +9,7 % | +8,9 % | +9,4 % | +9,5 % | 0,8 %/rok | **+0,5 pkt/rok** |
| X1 (7 faz) | +10,6 % | +7,2 % | +9,4 % | +9,6 % | 3,3 %/rok | **+2,2 pkt/rok** |
| CP1 | +33,6 % | +32,0 % | +33,0 % | +33,1 % | 1,5 %/rok | **+1,0 pkt/rok** |

## Co na plus (+) / Co na minus (−)

**(+)** Ten sam silnik, zmienia się jedna liczba (stawka); druga droga: koszt liniowy w stawce — oczekiwany zysk
maker 100 % = koszt taker × (1 − 0,02/0,07): TS1 0,57 vs zmierzone 0,6, X1 2,36 vs 2,4 — zgodne.
**(−)** Niemodelowana niekorzystna selekcja wypełnień (limit częściej wypełnia się, gdy rynek idzie przeciw) —
realny zysk mniejszy; założenie 90 % wypełnień bez danych o fillach. Opisowo, bez przedziałów (różnice są
deterministyczne dla danych — niepewność wyników nóg bez zmian). **Kogo nie ma:** funding bez zmian we wszystkich
scenariuszach; dźwignia 2×/3× dziennika mnożyłaby koszty proporcjonalnie.

## Przegląd (16c)

`engineering:code-review` (samodzielnie, skrypt opisowy): stawki z config (test), te same loadery co KR1 — **Approve**.

## Wniosek

**Prostym językiem:** koszty nie są tym, co blokuje trend i premię Coinbase — to mniej niż 1–1,5 % rocznie.
Limity warto stosować przy realnych pieniądzach, ale nie zmienią oceny strategii.

## Rekomendacja

1. Dziennik bez zmian (taker — konserwatywnie).
2. Szczebel 4 (realne pieniądze, decyzja użytkownika): przebudowy tygodniowe zleceniami limitowymi na płynnych
   monetach; dziennik wykonania mierzy odsetek wypełnień i selekcję — pierwszy pomiar realnego zysku z limitów.
3. Sprostowanie do rozmowy: „2–4 pkt/rok” dotyczy tylko strategii z dużym obrotem (X1, TL1), nie trendu i CP1.

## Użyte skille

Rejestr `runs/skille/ko1-koszty-wykonania.jsonl`: `clas5-runda` (pre-rejestracja scenariuszy przed przebiegiem),
`clas5-quant` (niekorzystna selekcja z C2.12/W1 jako zastrzeżenie). Pominięte: `data:validate-data` / `data:statistical-analysis`
(druga droga w README; runda opisowa bez wnioskowania), `engineering:code-review` — przegląd samodzielny według listy (skill
nie wczytany na tej gałęzi — przeoczenie), `engineering:testing-strategy` (jeden test stawek według wzorca).
