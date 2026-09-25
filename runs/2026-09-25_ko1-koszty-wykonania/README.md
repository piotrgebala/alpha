# KO1 — koszty wykonania nóg dziennika: zlecenia rynkowe vs limitowe (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (przed przebiegiem). Opisowo, 0 wariantów — zwroty nóg już odczytane;
> KO1 zmienia tylko stawkę kosztu × obrót, żeby zmierzyć, ile zjadają koszty.

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

_(sekcje poniżej po przebiegu)_
