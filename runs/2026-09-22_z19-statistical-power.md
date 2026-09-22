# Z19 — moc statystyczna: 4h jest NIEWYKONALNE, 1h jest jedyną testowalną konfiguracją (2026-09-22)

## ID testu

**Z19** (Backlog II) — patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/Z19-statistical-power`
- **Poprzedzający stan (master):** `d29ab0a` (Z9).
- **Komenda:** `py -m backtest.diagnose_statistical_power`
- **Nowe pliki:** `backtest/diagnose_statistical_power.py`
- **Zmiany:** `backtest/metrics.py` — `wald_half_width`, `min_detectable_hit_rate`,
  `required_trades`, stałe `Z_TWO_SIDED_95` / `Z_POWER_80`.
- **Dane:** trwały cache `data/raw/` (5m / 1h / 4h, 2023-07 → 2026-07).
- **Warianty hipotezy: 0** (rachunek wykonalności PRZED eksperymentem).
- **Testy:** **242/242** (231 + 11, w tym 2 property-based).

## Po co ta runda — i dlaczego PRZED eksperymentem

Z9 zakończył się rekomendacją: zmierzyć `p` w konfiguracji 4h / `V=3` / `range`, bo próg
opłacalności spada tam do 52,74% — pierwszy realistyczny próg w projekcie.

Ale niski próg jest bezużyteczny, jeśli próba jest za mała, żeby odróżnić „trafność powyżej
progu" od szumu. **Grubszy interwał daje jednocześnie lepszy próg i mniejszą próbę** (6 576
świec 4h wobec 315 648 świec 5m) — te dwa efekty idą w przeciwne strony. Zestawienie ich
musi nastąpić **przed** uruchomieniem, bo inaczej dostaniemy liczbę nierozstrzygalną
i będzie pokusa, żeby traktować ją jako przesłankę.

Kluczowa miara: `min_detectable_hit_rate` = trafność, którą trzeba **zmierzyć**, żeby dolny
kraniec 95% CI przekroczył próg opłacalności.

## Wynik

Szacunek `n` jest **górnym ograniczeniem**: zakłada, że każda świeca reżimu w oknie testowym
staje się transakcją. Realne `n` będzie mniejsze (brak sygnału kierunkowego, bramka kosztowa,
foldy poniżej `MIN_TRAIN_ROWS`). Jeśli nawet górne ograniczenie nie wystarcza — wniosek jest
rozstrzygający.

| interwał | reżim | świec reżimu | n (górne ogr.) | świec/fold | fold ≥ 30? | break-even | **trzeba zmierzyć** | n dla mocy 80% | wykonalne? |
|---|---|---|---|---|---|---|---|---|---|
| 5m | `range` | 66 996 | 62 105 | 862,6 | tak | 82,81% | **83,20%** | 16 | **tak** (ale próg absurdalny) |
| 5m | `trend` | 1 636 | 1 516 | 21,1 | **NIE** | 60,96% | 63,47% | 161 | nie |
| **1h** | **`range`** | **6 042** | **5 600** | **77,8** | **tak** | **56,77%** | **58,08%** | **425** | **TAK** |
| 1h | `trend` | 96 | 88 | 1,2 | **NIE** | 53,44% | 63,89% | 1 652 | nie |
| **4h** | **`range`** | 1 674 | 1 551 | **21,5** | **NIE** | 52,74% | 55,23% | **2 608** | **NIE** |
| 4h | `trend` | 28 | 25 | 0,3 | **NIE** | 52,11% | 71,71% | 4 423 | nie |

## Co na plus (+)

- **Rekomendacja z Z9 została zweryfikowana i OBALONA, zanim kosztowała eksperyment.**
  4h `range` wygląda najlepiej progiem (52,74%), ale jest niewykonalne z dwóch niezależnych
  powodów naraz: foldy mają 21,5 świec reżimu przy `MIN_TRAIN_ROWS = 30` (byłyby pomijane),
  a cała próba to co najwyżej 1 551 transakcji wobec 2 608 wymaganych dla mocy 80%.
  To dokładnie ten błąd, któremu rachunek mocy ma zapobiegać.
- **Zidentyfikowana jedyna konfiguracja jednocześnie wykonalna i o realistycznym progu:
  1h `range`** — 77,8 świec na fold (powyżej progu), n ≤ 5 600 przy wymaganych 425, próg
  56,77%, trzeba zmierzyć **58,08%**.
- Ujawniona nieoczywista zależność: `5m range` jest formalnie „wykonalne" (ogromna próba,
  n potrzebne = 16), ale wymaga zmierzenia **83,20%** trafności — czyli wykonalność
  statystyczna i sensowność merytoryczna to dwie różne rzeczy i trzeba patrzeć na obie.
- Funkcje mocy są teraz w `metrics.py` z testami (w tym niezmiennik: nigdy nie wolno orzec
  rentowności przy trafności równej progowi), więc kolejne rundy nie muszą liczyć tego ad hoc.

## Co na minus (−)

- **Szacunek `n` jest górnym ograniczeniem, nie prognozą.** Realne `n` na 1h będzie istotnie
  niższe — nie wiem o ile, bo zależy od udziału sygnałów kierunkowych i bramki kosztowej na
  tym interwale. Przy 5 600 wobec wymaganych 425 jest ogromny zapas, więc wniosek się
  nie zmieni; ale gdyby zapas był mały, ten szacunek byłby za słaby.
- **Werdykt „4h niewykonalne" jest częściowo artefaktem stałych okien walk-forward.** Okna
  60/14/14 są w DNIACH, więc na 4h dają 84 świec testowych na fold, z czego ~26% to `range`.
  Powiększenie okna testowego (np. do 28 dni) naprawiłoby kryterium foldów — ale NIE naprawi
  drugiego powodu, bo łączna liczba świec `range` w 3 latach danych 4h to twardy sufit.
- Rachunek zakłada niezależność transakcji. Przy nakładających się oknach etykiet faktyczna
  liczba niezależnych obserwacji jest mniejsza (`N_eff`, C2.9/Z3), więc **wymagane `n` jest
  w rzeczywistości WYŻSZE** niż podane. To działa przeciw wykonalności, nie za nią.
- `min_detectable_hit_rate` używa konserwatywnej wariancji (p=0,5). Przy p bliskim 0,5 to
  praktycznie dokładne; przy wyższym p byłoby nieco zbyt ostrożne.

## Wniosek

**Rekomendacja z Z9 była przedwczesna.** Konfiguracja 4h, choć ma najlepszy próg
opłacalności w całym projekcie, jest niewykonalna: foldy byłyby pomijane (21,5 < 30 świec),
a próba jest o 40% za mała (1 551 vs 2 608). Uruchomienie tego eksperymentu dałoby wynik
nierozstrzygalny niezależnie od tego, co pokaże model.

**Jedyna konfiguracja jednocześnie wykonalna i o realistycznym progu to 1h `range`:**
próba z ogromnym zapasem (5 600 wobec 425 wymaganych), foldy powyżej progu, próg 56,77%,
wymagana zmierzona trafność **58,08%**.

Skala wyzwania bez owijania: najczystszy dotychczasowy pomiar `p` (5m, po naprawie Z17+Z21)
to **50,38%**. Do orzeczenia rentowności na 1h trzeba **58,08%** — o **7,7 pp więcej**.
C2.6 mierzył na 1h ~49%, choć na danych z zepsutym wolumenem (Z9) i z nieproporcjonalnym
horyzontem (confound Z8).

## Rekomendacja

Dwie drogi, obie uczciwe — decyzja przy użytkowniku:

1. **Uruchomić pomiar `p` na 1h `range`** (natywne świece, `V` proporcjonalny, model kosztów
   z C2.12, pipeline po naprawach Z17+Z21). Jedyna konfiguracja, która może dać rozstrzygnięcie.
   To **nowa hipoteza** (inny interwał, inny horyzont, jeden reżim), więc własna
   pre-rejestracja, własny licznik i własna reguła STOP. Kryterium sukcesu z góry:
   dolny kraniec 95% CI trafności > 56,77%.
2. **Odblokować 4h przez dłuższą historię.** Binance ma 4h od 2019-09; ~6,8 roku dałoby
   ~3 600 świec `range` wobec wymaganych 2 608 — czyli 4h stałoby się wykonalne, przy progu
   **52,74%** zamiast 56,77%. Wymaga też powiększenia okna testowego (28 dni zamiast 14),
   żeby foldy przekraczały `MIN_TRAIN_ROWS`. Koszt: kilka minut pobierania (dane 4h są małe).
   **To unieważnia moje wcześniejsze odrzucenie Z5b** — odrzuciłem je, bo „nie domyka żadnego
   członu", co było prawdą na 5m, ale nie jest prawdą na 4h, gdzie wiążącym ograniczeniem
   jest właśnie liczebność próby.

Droga 2 jest merytorycznie lepsza (niższy próg = mniejsze wymaganie wobec modelu), ale
wymaga pobrania danych i zmiany okien walk-forward. Droga 1 jest natychmiastowa.

## Pełny surowy output

```
====================================================================================================
Z19 — czy eksperyment na grubszym interwale może cokolwiek rozstrzygnąć?
====================================================================================================
koszt C = 0.0900%  |  walk-forward 60/14/14 dni  |  MIN_TRAIN_ROWS = 30

interwał reżim  świec reżimu  n (górne ogr.)  na fold fold >= 30? break_even trzeba zmierzyć  n dla mocy 80% moc wystarcza?
      5m range         66996           62105    862.6         tak     82.81%           83.2%              16            tak
      5m trend          1636            1516     21.1         NIE     60.96%          63.47%             161            tak
      1h range          6042            5600     77.8         tak     56.77%          58.08%             425            tak
      1h trend            96              88      1.2         NIE     53.44%          63.89%            1652            NIE
      4h range          1674            1551     21.5         NIE     52.74%          55.23%            2608            NIE
      4h trend            28              25      0.3         NIE     52.11%          71.71%            4423            NIE

[legenda]
  n (górne ogr.)  - wszystkie świece reżimu w oknach testowych; REALNE n będzie MNIEJSZE
                    (odpadają brak sygnału, bramka kosztowa, foldy < MIN_TRAIN_ROWS)
  na fold         - średnio świec reżimu na jeden fold testowy; poniżej MIN_TRAIN_ROWS
                    fold jest POMIJANY przez backtest.engine
  trzeba zmierzyć - trafność, przy której DOLNY kraniec 95% CI przekracza break_even,
                    czyli minimum, by uczciwie orzec rentowność
  n dla mocy 80%  - liczba transakcji potrzebna, by odróżnić break_even od 50%

====================================================================================================
WNIOSEK — wykonalność per konfiguracja
====================================================================================================
  5m  range  -> WYKONALNE
      trzeba zmierzyć trafność >= 83.20% (break-even 82.81%)
  5m  trend  -> NIEWYKONALNE: foldy za małe (21.1 < 30 świec/fold)
      trzeba zmierzyć trafność >= 63.47% (break-even 60.96%)
  1h  range  -> WYKONALNE
      trzeba zmierzyć trafność >= 58.08% (break-even 56.77%)
  1h  trend  -> NIEWYKONALNE: foldy za małe (1.2 < 30 świec/fold); za mała próba (n<=88 vs wymagane 1652)
      trzeba zmierzyć trafność >= 63.89% (break-even 53.44%)
  4h  range  -> NIEWYKONALNE: foldy za małe (21.5 < 30 świec/fold); za mała próba (n<=1551 vs wymagane 2608)
      trzeba zmierzyć trafność >= 55.23% (break-even 52.74%)
  4h  trend  -> NIEWYKONALNE: foldy za małe (0.3 < 30 świec/fold); za mała próba (n<=25 vs wymagane 4423)
      trzeba zmierzyć trafność >= 71.71% (break-even 52.11%)
```
