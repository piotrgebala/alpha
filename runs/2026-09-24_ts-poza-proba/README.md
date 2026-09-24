# TR1 / TP1 — trend tygodniowy (reguła TS1) poza próbą: inne monety i nowe miesiące (2026-09-24)

> **STATUS: ZAMKNIĘTA.** **TR1 (monety z miejsc 21–50): NIEROZSTRZYGNIĘTY, ale powtarza TS1** —
> +14,1 %/rok [−3,0; +31,2], t_neff 1,62, ponad 99 % H0, 6/6 lat i 7/7 faz dodatnich; dzienna
> korelacja z TS1 0,86 (w dużej mierze ten sam zakład). **TP1 (nowe dane 2026-07-08 → 09-23,
> 78 dni): +0,69 % (+4,6 %/rok) — brak obalenia, brak potwierdzenia.** Pre-rejestracja
> `40d604a`. Walidacja (16a): **READY (Caveats: niska niezależność TR1)**; przegląd (16c): **Approve**.
> Decyzja użytkownika 2026-09-24: „sprawdzasz
> hipotezę na danych z ostatnich dwóch miesięcy albo na innych przedziałach” — jawne zdjęcie
> STOP serii TS dla sprawdzenia POZA PRÓBĄ (nie dla nowych wariantów reguły). Reguła TS1
> zamrożona co do bajtu (`backtest/ts_momentum.py` z commitu `d066412`). **Seria TS: TR1 = 2/2
> (replikacja z werdyktem), TP1 = odczyt prospektywny, 0 wariantów.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

TS1 (trend tygodniowy na 20 największych monetach) zarobił +14,8 % rocznie, ale bez dowodu.
Najuczciwszy sprawdzian to dane, których reguła „nie widziała”. Reguła nie ma parametrów do
trenowania (wszystkie wzięte z literatury), więc „poza próbą” znaczy dwie rzeczy:

1. **Inne monety, ten sam czas (TR1):** ta sama reguła na monetach z miejsc 21–50 po obrocie.
   Tych monet w TS1 nie było. To prawdziwa replikacja z własnym werdyktem.
2. **Nowy czas, te same zasady (TP1):** ta sama reguła na 20 największych monetach od
   1 lipca do 23 września 2026. Tych danych projekt jeszcze nie pobierał. Trzy miesiące to za
   mało, żeby cokolwiek potwierdzić; mogą tylko obalić, jeśli wynik będzie bardzo zły.

## ID testu

**TR1** (replikacja na miejscach 21–50) i **TP1** (pierwszy odczyt prospektywny top-20).
Żadnych zmian okna, celu zmienności, faz, kosztów.

## Metadane

- Branch: `ts-poza-proba`.
- Skrypt: `backtest/run_ts_momentum_oos.py` (na `runs/ZAMROZONE.txt`): `--moc` → `moc.txt`;
  `tr1` → `raw_output_tr1.txt`; `tp1` → `raw_output_tp1.txt`. Komendy:
  `PYTHONUTF8=1 py -m backtest.run_ts_momentum_oos {--moc|tr1|tp1}`.
- Dane TR1: `data/raw/universe` (jak TS1), skład miesięczny = top-50 minus top-20 po średnim
  obrocie z 30 dni (point-in-time), **od 2021-05-01** (w lutym 2021 było tylko 41 monet z pełnym
  oknem obrotu — ten sam start co X2), 62 miesiące, 203 różne symbole, po 30 monet.
- Dane TP1: nowy cache `data/raw/universe_2026q3` (`py -m data.fetch_universe
  data/raw/universe_2026q3 2025-06-01T00:00:00Z 2026-09-24T00:00:00Z`, pobrany 2026-09-24;
  rozbieg σ̂ i sygnału przed lipcem), skład top-20 na lipiec/sierpień/wrzesień 2026.

## Poprzedzające wyniki

- **TS1 (wniosek 70):** +14,8 %/rok [−1,7; +31,3], t_neff 1,76, 6/6 lat, 7/7 faz dodatnich.
- **X1 → X2 (wniosek 68):** momentum przekrojowe osłabło przy poszerzeniu koszyka (+22 → +16 %/rok)
  — ta sama groźba dotyczy TR1: mniejsze monety to więcej szumu i inne zachowanie.
- **NL1 (wniosek 71):** nowe/małe monety mają ogony wystrzałów — miejsca 21–50 są w połowie drogi.

## Pre-rejestracja

- **TR1 — hipoteza:** reguła TS1 na monetach z miejsc 21–50 ma dodatni średni zwrot netto.
  **Kryterium (jak TS1):** POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0 (znaki przesunięte
  w czasie, 100 portfeli); NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
  **Mierzalność (`moc.txt`):** 1 880 dni, zmienność H0 20,8 %/rok, **half-width 18,0 %/rok
  = 0,86 SR**, q97,5 H0 +13,5 %/rok → MIERZALNA dla efektu rzędu TS1 (+15 %/rok) tylko na
  granicy; słabszy efekt niewidoczny. **Zastrzeżenie z góry:** miejsca 21–50 są silnie
  skorelowane z top-20 (ten sam rynek krypto, te same okresy hossy i bessy) — to replikacja na
  INNYCH aktywach, ale nie w pełni NIEZALEŻNA próba; zgodny wynik wzmacnia TS1 mniej, niż
  sugerowałaby liczba monet.
- **TP1 — odczyt prospektywny (0 wariantów, bez werdyktu dowodowego):** top-20, 7 faz, dni od
  pierwszego dnia ze wszystkimi fazami (~8 lipca) do 23 września (~78 dni). **Próg obalenia
  zapisany z góry:** jeśli TS1 jest prawdziwe (+14,8 %/rok, zmienność 19,6 %/rok), średnia
  roczna z n dni spada poniżej 14,8 − 1,96·19,6/√(n/365) %/rok (≈ −68 %/rok przy 78 dniach,
  czyli ok. −14 % skumulowanie) w mniej niż 2,5 % przypadków → taki wynik OBALA TS1. Każdy inny
  wynik = „brak obalenia”, nie potwierdzenie. **Mierzalność jako test: NIEMIERZALNA** —
  zapisane wprost; TP1 jest pierwszym wpisem dziennika prospektywnego, nie rundą z werdyktem.
- **Kontekst multiple testing:** ~27 odczytów w dwa dni; TR1 to replikacja reguły wybranej jako
  najlepsza z ~25 — dlatego jej werdykt waży więcej niż kolejny nowy pomysł.
- **Czego runda NIE robi:** nie zmienia reguły, nie wybiera podzbioru monet po wyniku, nie
  łączy TR1 z TS1 w jeden wynik.

---

## Wynik

**TR1** (`raw_output_tr1.txt`, 1 880 dni, 2021-05 → 2026-06, po 30 monet z miejsc 21–50):

| miara | TR1 | TS1 (odniesienie) |
|---|---|---|
| zwrot netto [CI 95 %] | **+14,1 %/rok [−3,0; +31,2]** | +14,8 %/rok [−1,7; +31,3] |
| t_neff | 1,62 | 1,76 |
| H0 q97,5 / pozycja | +13,5 %/rok / ponad 99 % | +13,0 / ponad 100 % |
| lata dodatnie | 6/6 (2021 +20,5 · 2022 +9,1 · 2023 +13,0 · 2024 +13,3 · 2025 +15,2 · 2026 +1,5 %) | 6/6 |
| 7 faz (%/rok) | +12,0 … +17,9, wszystkie dodatnie | +9,6 … +17,3 |
| nominał brutto / netto | 0,37× / −0,07× | 0,41× / −0,04× |
| **werdykt** | **NIEROZSTRZYGNIĘTY** | NIEROZSTRZYGNIĘTY |

**TP1** (`raw_output_tp1.txt`): 78 dni ze wszystkimi fazami (2026-07-08 → 09-23), top-20 z nowych
danych (m.in. nowe monety LAB, VELVET, AKE, TUT); zwrot netto skumulowany **+0,69 %** (brutto
+1,26 %, funding −0,04 %, koszt 0,23 %) = +4,6 %/rok; zmienność 17,0 %/rok; 7 faz od −4,4 % do
+8,4 %. Próg obalenia zapisany z góry: −68,3 %/rok → **brak obalenia**.

## Co na plus (+) / Co na minus (−)

**(+)** TR1 odtwarza TS1 niemal co do liczby na monetach, których TS1 nie widziało (0 wspólnych
w żadnym miesiącu), z tym samym profilem (wszystkie lata i fazy dodatnie, neutralny na rynek).
TP1 na zupełnie nowych danych nie obala reguły.
**(−)** **Niezależność TR1 jest niska:** korelacja dzienna z TS1 0,86 — oba portfele grają te
same trendy całego rynku krypto; TR1 wzmacnia TS1 mniej, niż sugeruje liczba monet. Samo TR1
nadal nierozstrzygnięte (t 1,62). TP1 z definicji nie rozstrzyga (78 dni, rozdzielczość ±80 %/rok).
**Kogo nie ma:** TR1 — luty–kwiecień 2021 (za mało monet z historią obrotu); TP1 — 32 symbole
puste przy pobraniu (wycofane/przemianowane; nie wchodziły do top-20 w lipcu–wrześniu).

## Walidacja (zasada 16a)

`data:validate-data`: **READY z zastrzeżeniem** (niska niezależność TR1). `walidacja.py` →
`walidacja_tr1.txt`: (1) faza 0 TR1 pętlą pandas bez `ts_momentum`: **+12,54 %/rok** = silnik ✓;
(2) TR1 ∩ top-20 = 0 w każdym miesiącu ✓; (3) korelacja TR1–TS1 0,86 na 1 880 dniach. Bramka 16b
(`data:statistical-analysis`): TR1 i TS1 NIE łączone w jeden wynik (prawie ta sama informacja);
TP1 opisowo z progiem z góry.

## Przegląd diffu (zasada 16c)

`engineering:code-review`: `members_rank_band` = top-50 minus top-20 point-in-time (test);
TR1 od 2021-05 (brak 50 kandydatów wcześniej — jawne); TP1 liczy próg obalenia z liczby dni;
H0 jak TS1. **Werdykt: Approve.**

## Wniosek

**Prostym językiem:** trend tygodniowy powtórzył się na innych monetach (+14 % rocznie, jak na
20 największych), a na nowych danych z lipca–września 2026 zarobił lekko na plus. To dobre
znaki, ale nie dowód: obie grupy monet poruszają się razem, więc druga grupa to prawie ten sam
zakład, a trzy miesiące to za mało, żeby cokolwiek przesądzić. Reguła przetrwała każdy
sprawdzian, jaki mogliśmy jej dać na historii.

## Rekomendacja

1. **Seria TS zamknięta na historii** (TS1 + TR1). Dalsze rozstrzygnięcie wyłącznie na żywo:
   `py -m backtest.run_ts_momentum_oos tp1` po dociągnięciu danych (ten sam cache, nowe dni)
   — dziennik prospektywny; kolejny odczyt co kwartał.
2. Grając regułę przed rozstrzygnięciem: ekspozycja ~0,4–0,8× kapitału (TS1), nie 3×.

## Użyte skille

Rejestr `runs/skille/ts-poza-proba.jsonl`: `clas5-runda`, `clas5-quant` (poza próbą = nowe aktywa
lub nowy czas, reguła bez treningu), `data:validate-data`, `data:statistical-analysis`,
`engineering:code-review`. **Pominięte:** `testing-strategy` (1 test pomocnika według wzorca TS1),
`dataviz` (bez wykresu), `data:explore-data` (nowy cache to ten sam kolektor uniwersum P2).
