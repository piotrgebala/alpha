# CP2 — premia Coinbase na ETH i SOL (replikacja CP1) (2026-09-24)

> **STATUS: ZAMKNIĘTA — NIEMIERZALNA, runda NIE wystartowała (zasada 18).** Rachunek mocy
> (`moc.txt`, tylko rozrzut portfeli H0, bez oglądania wyniku): przy korekcie na dwa ramiona test
> rozróżnia dopiero efekty ±36 %/rok (ETH) i ±37 %/rok (SOL) — więcej niż cały wynik CP1 na BTC
> (+32 %/rok, sam zawyżony wyborem z ~31 odczytów). Moc nawet przy efekcie jak w CP1: 34–39 %.
> Do tego sygnał ETH jest TYM SAMYM sygnałem co BTC w **94 %** dni, SOL w **89 %** — premia
> Coinbase to jeden wspólny czynnik dla wszystkich monet. **0 wariantów; odczytu wyniku brak.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Premia Coinbase (o ile drożej kupuje się na amerykańskiej giełdzie niż na Binance) dała na BTC
jedyny dodatni wynik projektu. Chcieliśmy sprawdzić, czy ta sama reguła działa na ETH i SOL —
to byłby niezależny dowód, że nie trafiliśmy na przypadek. Przed policzeniem wyniku okazało się,
że to nie jest niezależny dowód: premia na ETH i SOL porusza się prawie tak samo jak na BTC,
więc sygnał kupna/sprzedaży jest ten sam w 9 na 10 dni. Do tego na jednej monecie test jest tak
mało czuły, że nawet efekt tak duży jak na BTC wykryłby tylko w ~4 na 10 przypadków. Wynik nie
rozstrzygnąłby niczego, więc go nie liczymy. **Premię Coinbase może rozstrzygnąć tylko czas
(dziennik na żywo na BTC), nie inne monety.**

## ID testu

CP2 — generalizacja CP1 na inne instrumenty (CLAUDE.md zasada 9: te same progi, bez retuningu).

## Metadane

- Branch `cp2-replikacja-eth-sol`. Skrypt `backtest/run_coinbase_cp2.py` (na `runs/ZAMROZONE.txt`);
  reguła importowana z zamrożonego `run_coinbase_cp1.py` (`daily_premium`, `premium_signal`,
  `_shifts`) — bez kopii. Komenda rachunku mocy:
  `PYTHONUTF8=1 py -m backtest.run_coinbase_cp2 --moc` → `moc.txt` (94 s). Tryb pełny istnieje,
  ale **nie został uruchomiony**.
- Dane: Coinbase `ETH-USD` / `SOL-USD` 1d (`data/raw/external/`, pobrane 2026-09-24), spot Binance
  `ETH-USDT` / `SOL-USDT` 8h (świeca 16:00 = zamknięcie o 24:00 UTC), perpetuale
  `ETHUSDT` / `SOLUSDT` 1d + funding z `data/raw/universe/`. Okno do 2026-06-30 (jak CP1).
- Ramiona: ETH od 2021-05-01 (jak CP1), SOL od 2021-10-01 (Coinbase SOL-USD od 2021-06-17 + 90 dni
  rozbiegu średniej).

## Poprzedzające wyniki

- **CP1** (wniosek 72): +32 %/rok [+2; +62], t_neff 2,09 — POZYTYWNY wg kryterium, ale nie
  przechodzi korekty na ~28–31 odczytów; beta 0,36 wobec trendu 28 dni.
- **CP1P** (poza próbą, lip–wrz 2026): +0,13 % na 78 dni — brak obalenia, brak potwierdzenia.
- **SC1** (wniosek 78): precedens rachunku mocy przed wynikiem — NIEMIERZALNE, 0 wariantów.
- **P2** (wniosek 40): liczba instrumentów to nie liczba obserwacji (20 monet ≈ 2 niezależne).
- Zasada 9: rozszerzenie na inne monety = test generalizacji tej samej hipotezy, bez retuningu.

## Pre-rejestracja (zapisana przed rachunkiem mocy)

- **Hipoteza:** reguła CP1 bez zmian (znak średniej premii 7 dni − 90 dni, silnik TS1, 7 faz,
  koszt z config, realny funding) zarabia na ETH i SOL.
- **DOKŁADNIE JEDNA zmienna:** instrument (premia i perpetual tej samej monety).
- **Kryterium per ramię (m = 2, Bonferroni z = 2,241):** POZYTYWNY, gdy t_neff > 2,241 ORAZ średnia
  > q97,5 H0 (100 portfeli ze znakiem przesuniętym cyklicznie o losową liczbę tygodni); NEGATYWNY,
  gdy górny kraniec < 0; inaczej NIEROZSTRZYGNIĘTY.
- **Założony efekt:** jak CP1, SR ≈ 0,9 (+32 %/rok przy zmienności ~35 %) — górna granica, bo
  wynik CP1 jest zawyżony selekcją.
- **Opisowo (bez zwrotów):** zgodność znaku z sygnałem CP1 BTC i z trendem 28 dni danej monety.
- **Mierzalność (`moc.txt`):**

  | ramię | dni | zmienność H0 | half-width (z 2,241) | w jednostkach SR | q97,5 H0 |
  |---|---|---|---|---|---|
  | ETH | 1 880 | 34,9 %/rok | **±36,2 %/rok** | 1,04 | +34,3 %/rok |
  | SOL | 1 727 | 33,4 %/rok | **±37,2 %/rok** | 1,11 | +33,8 %/rok |

  Moc (prawdopodobieństwo wykrycia) przy efekcie jak w CP1 (SR 0,91): **39 % (ETH), 34 % (SOL)**;
  przy efekcie skurczonym do SR 0,6 (typowa korekta na selekcję): ~17 %. Half-width > założony
  efekt → **NIEMIERZALNA na obu ramionach.**
- **Niezależność ramion (z samych sygnałów):** znak ETH = znak BTC w **94,4 %** dni, SOL = BTC
  w **89,3 %**; korelacja poziomu premii ETH z BTC **0,95**, zmian dziennych 0,76 (SOL: 0,82 / 0,45).
  Nawet POZYTYWNY wynik byłby w ~90 % powtórką sygnału BTC na mocno skorelowanej monecie, a nie
  niezależnym potwierdzeniem.

## Profil danych (`data:explore-data`)

| zbiór | wiersze | zakres | luki / duplikaty | premia p1 / mediana / p99 | max zmiana dzienna premii |
|---|---|---|---|---|---|
| Coinbase ETH-USD 1d | 2 824 | 2019-01-01 → 2026-09-24 | 0 / 0 | −0,169 % / +0,011 % / +0,238 % | 0,40 pp |
| Coinbase SOL-USD 1d | 1 926 | 2021-06-17 → 2026-09-24 | 0 / 0 | −0,184 % / +0,005 % / +0,202 % | 0,78 pp |
| (odniesienie) BTC-USD 1d | 2 823 | 2019-01-01 → 2026-09-23 | 0 / 0 | −0,173 % / +0,013 % / +0,239 % | 0,57 pp |

Świece Coinbase otwierane o 00:00 UTC; spot 8h ma 2 007 świec 16:00 (pełne pokrycie). Zero dni
z |premią| > 2 % — brak błędnych notowań. Kogo nie ma w zbiorze: SOL przed 2021-06-17.

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY**: zgodność sygnałów przeliczona NIEZALEŻNIE (złączenie po dacie
tekstowej, ręczny wybór świecy 16:00, średnie przez sumy skumulowane numpy — bez `daily_premium`
i `premium_signal`): **94,4 % na 1 887 dniach i 89,3 % na 1 734 dniach** — identycznie jak
w `moc.txt`. `data:statistical-analysis`: moc z rozkładu normalnego P(Z > 2,241 − SR/se), se =
half-width/2,241; efekt CP1 traktowany jako górna granica (klątwa zwycięzcy). `engineering:code-review`
— **Approve**: reguła importowana z zamrożonego CP1 (brak kopii do rozjechania), start po rozbiegu
90 dni, funding per symbol; poprawiony jeden błąd przed przebiegiem (strefa czasowa w `date_range`).

## Wniosek

**Prostym językiem:** sprawdzenie premii Coinbase na ETH i SOL nie może niczego rozstrzygnąć,
i to z dwóch powodów. Po pierwsze, sygnał na tych monetach jest prawie zawsze taki sam jak na BTC
— premia to w dużej części kurs dolara do USDT i ogólny popyt z USA, wspólny dla całego rynku.
Po drugie, test na jednej monecie przez 5 lat jest za mało czuły: nawet gdyby efekt był tak duży
jak na BTC, wykrylibyśmy go mniej więcej w 1 na 3 próby. Dlatego wyniku nie liczymy. Premia
Coinbase pozostaje **kandydatem**; rozstrzygnąć może ją tylko dłuższy czas obserwacji na żywo.

## Rekomendacja

1. Nie szukać potwierdzenia premii Coinbase na innych monetach — to ta sama informacja.
2. Kontynuować dziennik prospektywny CP na BTC (CP1P: pierwszy odczyt lip–wrz 2026); decyzja
   o realnym kapitale należy do użytkownika i wymaga dłuższej próby.
3. Seria CP: licznik bez zmian (1/1, STOP); CP2 = 0 wariantów, 0 odczytów wyniku.

## Użyte skille

Rejestr `runs/skille/cp2-replikacja-eth-sol.jsonl` (`py tools/skill_audit.py raport --galaz
cp2-replikacja-eth-sol`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | kolejność: profil i rachunek mocy przed jakimkolwiek wynikiem; katalog rundy |
| `anthropic-skills:clas5-quant` | zasada 9 i wniosek 40: kolejne instrumenty to nie kolejne obserwacje — stąd pomiar zgodności sygnałów |
| `data:explore-data` | profil Coinbase ETH/SOL: luki, duplikaty, rozkład premii, korelacja z premią BTC 0,95 |
| `data:validate-data` | niezależne przeliczenie zgodności sygnałów (94,4 % / 89,3 %, identycznie) |
| `data:statistical-analysis` | moc 34–39 % przy efekcie CP1, ~17 % przy efekcie skurczonym |
| `engineering:code-review` | Approve; reguła importowana, nie kopiowana |
| `anthropic-skills:lean-research` | wczytany na tej gałęzi wcześniej przy przeglądzie projektu SIGMA (przed pauzą użytkownika) — nie dotyczy CP2 |

Pominięte z tabeli zasady 19: `quant-strategy-catalog` (to nie nowa hipoteza, tylko generalizacja
CP1), `dataviz` (brak wyniku do pokazania).
