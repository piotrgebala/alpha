# RU1 — korekta danych: pełne uniwersum perpetuali (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed przeliczeniem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Sonda hipotez (2026-09-24) znalazła błąd w danych, który jest ważniejszy niż każda nowa hipoteza.
Katalog `data/raw/universe`, z którego liczyliśmy koszyk „20 największych monet”, ma tylko
**287 z 685** kontraktów z archiwum Binance: monety na litery A–G prawie w komplecie, a z H–Z tylko
12 (HBAR, HYPE, LINK, LTC, NEAR, SOL, TRX, UNI, XLM, XMR, XRP, ZEC). Pobieranie 22.09 najwyraźniej
przerwało się w połowie alfabetu i nikt tego nie zauważył — to dokładnie pytanie „kogo NIE ma
w zbiorze” z bramki A2, które tym razem nie zadziałało. Przez to koszyk top-20 w rundach trendu,
momentum i sizingu pomijał m.in. SUI, TON, OP, MATIC, WLD, TAO. Ta runda uzupełnia dane
i przelicza najważniejsze wyniki **tymi samymi, zamrożonymi regułami**.

## ID testu

RU1 — korekta danych (nie nowa hipoteza).

## Metadane

- Branch `ru1-pelne-uniwersum`. Dane: nowy katalog `data/raw/universe_full` (stary zostaje nietknięty
  — zamrożone rundy muszą dać się odtworzyć, zasada 13): pliki A–G skopiowane ze starego cache
  (ten sam pobieracz, te same daty 2020-01-01 → 2026-07-01), brakujące świece dociągnięte przez
  `data/complete_universe.py` (funkcje `data.fetch_universe`), funding tylko dla członków top-20
  2021–2026 (tylko ich pozycje płacą funding). OHLC do likwidacji: `data/fetch_universe_ohlc.py`
  z parametrem `universe_dir` → `data/raw/universe_ohlc_full/`.
- Skrypt `backtest/run_universe_fix_ru1.py` (tryby `sklad`, `ts1`, `x1`, `sz1`) — podmienia tylko
  katalog danych; reguły, H0 i kryteria pochodzą z zamrożonych `run_ts_momentum_ts1`,
  `run_xs_momentum_x1` i funkcji SZ1.

## Poprzedzające wyniki (na obciętym uniwersum)

| runda | wynik | wniosek |
|---|---|---|
| TS1 trend tygodniowy | +14,8 %/rok [−1,7; +31,3], t_neff 1,76; H0 q97,5 +13,0 → NIEROZSTRZYGNIĘTY | 70 |
| TR1/TP1 poza próbą | przetrwał oba sprawdziany | 74 |
| X1 momentum przekrojowe | +22,0 %/rok (+0,060 %/dzień [−0,015; +0,135]), t_neff 1,58 → NIEROZSTRZYGNIĘTY | 64 |
| X2 top-50, R1, TF1, TL1, LQ1, NL1, P2 | różne | 40, 57, 68, 71, 73, 75, 76 |
| SZ1 portfel | R0 +19,9 %/obs. 18,9 %; R1 +18,6 %/17,7 %; R2 +10,3 % | 77 |

Z nich wziął się dziennik na żywo (`dziennik/`): progi 17,7 % / 26,5 % pochodzą z SZ1 R1.

## Pre-rejestracja (przed przeliczeniem)

- **Pytanie:** czy ślady TS1 i X1 (i profil SZ1) przetrwają na pełnym uniwersum point-in-time?
- **JEDNA zmienna:** zawartość uniwersum (stary cache → pełny). Reguły co do bajtu: okno 28 dni,
  7 faz, top-20 po obrocie z 30 dni, X1: nogi po 5, trzymanie 7 dni; koszty i funding jak w rundach.
- **Kryteria — te same co w rundach pierwotnych:** TS1 POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia >
  q97,5 H0 (100 portfeli ze znakami przesuniętymi w czasie); X1 POZYTYWNY, gdy t_neff > 1,96;
  NEGATYWNY, gdy górny kraniec CI 95 % < 0.
- **Odczyt odporności (opisowy, zapisany z góry):** „ślad odporny na błąd danych”, gdy wynik na
  pełnym uniwersum ma ten sam znak i co najmniej połowę pierwotnej średniej; „ślad zależał od
  błędu”, gdy spada poniżej połowy albo zmienia znak.
- **Czego runda NIE może:** potwierdzić przewagi. To ta sama historia i ~33 odczyty w projekcie;
  wynik wyższy niż pierwotny NIE jest potwierdzeniem i nie będzie tak cytowany.
- **Mierzalność:** rozdzielczość jak w rundach pierwotnych — TS1 ±16,5 %/rok, X1 ±27 %/rok;
  runda rozstrzyga pytanie o błąd danych (przesunięcie średniej), nie o przewagę.
- **Opisowo:** skład koszyka stary vs pełny miesiąc po miesiącu; okres od 2022 (preferencja
  użytkownika); SZ1 R0/R1/R2 na pełnym uniwersum.
- **Konsekwencje dla dziennika (zapisane z góry):** reguły dziennika się nie zmieniają (dziennik
  i tak ma pełne dane). Jeśli największe obsunięcie R1 na pełnym uniwersum różni się od 17,7 %,
  progi dziennika zostaną przeliczone tą samą regułą (ostrzeżenie = max obsunięcie R1, STOP =
  1,5 × to) jako poprawka 2 — przed pierwszym wynikiem dziennika (koniec dnia 24.09 UTC).
- **Liczniki:** 0 nowych wariantów — powtórka uzasadniona błędem danych (zasada 14); serie TS i X
  pozostają zamknięte regułą STOP (decyzja użytkownika 2026-09-24: „wykonaj kolejne kroki, jakie
  proponujesz” — sonda wskazała RU1 jako krok 1).
- **Poza zakresem (oznaczone do przeliczenia w STATUS):** X2, R1, TF1, TL1, LQ1, NL1, P2, TR1.

_(sekcje poniżej po przebiegu)_
