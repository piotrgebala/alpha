# RU1 — korekta danych: pełne uniwersum perpetuali (2026-09-24)

> **STATUS: ZAMKNIĘTA — oba ślady ODPORNE na błąd danych, oba nadal NIEROZSTRZYGNIĘTE.**
> Pełne uniwersum (685 kontraktów zamiast 287; skład top-20 inny średnio na 5,1 z 20 miejsc):
> **TS1 +11,1 %/rok** [−4,2; +26,3], t 1,43 (było +14,8, t 1,76); **X1 +41,7 %/rok** [−2,2; +85,6],
> t_neff 1,86 (było +22,0) — z czego ~83 pkt z 226 dało jedno zdarzenie (MYX, 7–8.09.2025);
> bez tych 2 dni +26,3 %/rok. **SZ1 R1 +17,1 %/rok, obsunięcie 18,4 %** (było +18,6 / 17,7).
> Pre-rejestracja `d2316cc`. Walidacja: **READY (Caveats)**; przegląd: **Approve**. 0 wariantów.
> Poprzednio: **PRE-REJESTRACJA (przed przeliczeniem).**

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

## Wynik

Pliki: `raw_output_sklad.txt`, `raw_output_ts1.txt`, `raw_output_x1.txt`, `raw_output_sz1.txt`.

**Skład koszyka** (bez zwrotów): średnio **5,1 z 20** miejsc inaczej (26 %), od 2022 5,5/20, maks. 9;
najczęściej brakowały MATIC (29 miesięcy), SUI (27), WLD (16), WIF (16), OP (13), SAND (11), ORDI (11),
LUNA (9). Z 685 kontraktów 10 bez danych; przez top-20 w 2021–2026 przeszło 195 monet (funding
dociągnięty dla 98 brakujących).

| | stare uniwersum | pełne uniwersum | odczyt kryterium | odporność (z góry: ten sam znak i ≥ ½) |
|---|---|---|---|---|
| **TS1** netto | +14,8 %/rok [−1,7; +31,3], t 1,76 | **+11,1 %/rok [−4,2; +26,3], t 1,43**; H0 q97,5 +12,0 (TS1 ponad 93 % H0) | NIEROZSTRZYGNIĘTY | **odporny** (75 % pierwotnej) |
| TS1 od 2022 (opisowo) | — | +9,0 %/rok [−8,0; +25,9], t 1,03 | — | — |
| **X1** netto | +22,0 %/rok, t_neff 1,58 | **+41,7 %/rok [−2,2; +85,6], t_neff 1,86**; mediana/dzień +0,117 % | NIEROZSTRZYGNIĘTY | **odporny** (190 %) |
| X1 od 2022 (opisowo) | — | +48,7 %/rok [−0,5; +98,0], t_neff 1,94 | — | — |
| X1 bez 7–8.09.2025 (opisowo, **po obejrzeniu**) | — | +26,3 %/rok, t 1,66, mediana/dzień +0,116 % | — | — |
| **SZ1 R1** | +18,6 %/rok, obs. 17,7 % | **+17,1 %/rok, obs. 18,4 %**; od 2022 +21,1 % / 18,4 % | opisowo | — |
| SZ1 R0 / R2 | +19,9 % / +10,3 % | +18,9 % (obs. 19,5 %) / +9,5 % | opisowo | — |

TS1 per rok (pełne): 2021 +19,5 · 2022 +8,2 · 2023 +12,4 · 2024 +2,6 · 2025 +16,6 · 2026 (pół) +0,6 %;
7 faz od +7,4 do +14,8 %/rok. X1 per rok: +6,5 · +12,9 · +23,8 · +8,4 · **+166,2** · +7,9 %; funding netto
X1 +49 pkt w 5,5 roku (short na przegrzanych monetach otrzymuje opłatę).

**Czerwona flaga X1 (zbadana):** dzień 2025-09-08 dał +65 % portfela, 2025-09-07 +18 %. Przyczyna:
MYXUSDT +167 % i +298 % dziennie (prawdziwe notowania Binance; moneta była w nodze long, bo już rosła
najszybciej w koszyku). Stary cache nie miał litery M, więc tego zdarzenia nie widział.

## Co na plus (+) / Co na minus (−)

**(+)** Oba ślady przetrwały usunięcie błędu danych: znak ten sam, TS1 zachował 75 % wyniku, X1 go
wzmocnił. Dziennik liczony na świeżych danych zgadza się z pełnym backtestem prawie idealnie
(korelacja 0,9990). Portfel SZ1 praktycznie bez zmian (+17 %/rok, spadek 18 %).
**(−)** Nic nie stało się istotne — oba wyniki nadal w granicach szumu. Wzrost X1 wisi w dużej części
na jednym wystrzale jednej monety; mediana dziennego zwrotu się nie zmieniła, a bez tych 2 dni
zostaje +26 %/rok (t 1,66). W 2024–2026 TS1 słabnie (+2,6 %, +16,6 %, +0,6 %). Inne rundy liczone na
starym cache (X2, R1, TF1, TL1, LQ1, NL1, P2, TR1) nadal czekają na przeliczenie. PAXG (token złota)
wchodzi do koszyka w 2026 — zostawiony zgodnie z regułą (nie decydowano o tym z góry w TS1).

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY (Caveats)**: (1) składowa trend dziennika liczona NIEZALEŻNIE na świeżych
danych Binance (`data/raw/live`, inny pobieracz) vs backtest na pełnym uniwersum, 258 wspólnych dni:
**korelacja 0,9990** (na starym uniwersum 0,9814) — to potwierdza nowe dane i koryguje opis
w `dziennik/README.md` (różnica 0,981 brała się z obciętego uniwersum, nie z monet wycofanych);
(2) X1 bez 2 dni przeliczony prostą średnią poza `summarize_pnl`; (3) zdarzenie MYX sprawdzone na
cenach. Caveat: TR1, X2 i pozostałe rundy nieprzeliczone. `data:statistical-analysis`: mediana obok
średniej przy skośnym X1 (max +65 %/dzień, p95 +3,1 %); odczyt odporności zapisany z góry; wynik
wyższy niż pierwotny NIE jest potwierdzeniem (~33 odczyty). `engineering:code-review` — **Approve**:
podmiana katalogu w zamrożonym module w czasie wykonania (plik nietknięty), pobieracz z tymi samymi
funkcjami co P2, parametr `universe_dir` z domyślną wartością bez zmian.

## Wniosek

**Prostym językiem:** dziura w danych była prawdziwa — co czwarte miejsce w koszyku „20 największych
monet” było obsadzone źle. Po jej załataniu nasze dwa najlepsze ślady **nie zniknęły**: trend
tygodniowy daje ok. +11 % rocznie zamiast +15 %, momentum przekrojowe nawet więcej niż wcześniej, ale
w dużej części dzięki jednemu wystrzałowi jednej monety. Żaden z nich nadal nie jest dowodem — to wciąż
może być szczęście. Portfel do dziennika (trend + premia Coinbase) wygląda prawie tak samo jak przed
poprawką, więc dziennik działa dalej bez zmian reguł; tylko próg ostrzeżenia rośnie z 17,7 % do 18,4 %.

## Rekomendacja

1. Dziennik bez zmian reguł; progi według zapisanej z góry reguły: ostrzeżenie 18,4 %, STOP 27,6 %
   (poprawka 2, przed pierwszym wynikiem).
2. Nowe rundy na koszykach — tylko na `data/raw/universe_full`; stary cache oznaczony jako obcięty.
3. Przeliczyć kolejno TR1, X2, TF1, TL1, LQ1, NL1, R1, P2 (backlog w STATUS) — każda jako korekta
   danych, 0 wariantów.
4. Do bramki A2 („kogo nie ma w zbiorze”): przy każdym nowym uniwersum liczyć pokrycie liter/symboli
   wobec listy źródła — ten błąd przetrwał ~10 rund.

## Użyte skille

Rejestr `runs/skille/ru1-pelne-uniwersum.jsonl` (`py tools/skill_audit.py raport --galaz ru1-pelne-uniwersum`).

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | pre-rejestracja przed przeliczeniem, nowy katalog danych zamiast nadpisania (zasada 13) |
| `anthropic-skills:clas5-quant` | „kogo nie ma w zbiorze”; odczyt odporności zamiast „potwierdzenia” |
| `data:explore-data` | profil składu: 5,1/20 miejsc, lista brakujących monet |
| `data:validate-data` | niezależne porównanie z dziennikiem (0,9990) i zbadanie dnia +65 % |
| `data:statistical-analysis` | mediana obok średniej przy skośnym X1, wynik bez zdarzenia jako opis |
| `engineering:code-review` | Approve |

Pominięte: `dataviz` (tabele wystarczą), `engineering:testing-strategy` (bez nowego modułu biblioteki).
