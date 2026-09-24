# TR1 / TP1 — trend tygodniowy (reguła TS1) poza próbą: inne monety i nowe miesiące (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „sprawdzasz
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

_(sekcje poniżej po przebiegu)_

## Wynik

_(po przebiegu)_

## Co na plus (+) / Co na minus (−)

_(po przebiegu)_

## Walidacja (zasada 16a)

_(po przebiegu)_

## Przegląd diffu (zasada 16c)

_(po przebiegu)_

## Wniosek

_(po przebiegu)_

## Rekomendacja

_(po przebiegu)_

## Użyte skille

_(po przebiegu — z `py tools/skill_audit.py raport --galaz ts-poza-proba`)_
