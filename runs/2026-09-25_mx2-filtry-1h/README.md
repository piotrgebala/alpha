# MX2 — pięć filtrów na sygnale MACD → EMA 10/30, BTC 1h (2026-09-25)

> **STATUS: WSZYSTKIE PIĘĆ NIEMIERZALNE — runda NIE wystartowała** (CLAUDE.md zasada 18). Decyzja użytkownika po MX1:
> „odfiltrujmy część przecięć — zrób wersję w tych 4 wariantach i jeszcze RSI” (filtry zaproponowane przez Claude:
> trend wyższego interwału, ADX, wolumen, godziny sesji USA; RSI dodany przez użytkownika). Policzono WYŁĄCZNIE liczbę
> sygnałów po każdym filtrze, barierę, próg i moc — żadnej transakcji nie zasymulowano. **0 wariantów zużytych.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Każdy filtr zostawia tylko część z 1 254 sygnałów MX1. Mniej przykładów w historii oznacza, że trudniej odróżnić dobrą
regułę od szczęścia, więc poprzeczka rośnie. Przy pięciu filtrach naraz rośnie jeszcze trochę, bo sprawdzając pięć
rzeczy, łatwiej o przypadkowy „sukces”. Wynik:

| filtr | zostaje sygnałów | trzeba zmierzyć (przy 5 filtrach) | szansa potwierdzenia, gdyby filtr naprawdę trafiał 56 % / 60 % / 65 % |
|---|---|---|---|
| trend 28 dni zgodny z kierunkiem | 585 (47 %) | ≥ 59,4 % | 6 % / 64 % / 99,8 % |
| ADX(14) > 25 (silny trend) | 302 (24 %) | ≥ 61,3 % | 4 % / 34 % / 92 % |
| wolumen powyżej średniej 20 świec | 684 (55 %) | ≥ 59,0 % | 6 % / 72 % / 100 % |
| sesja USA (13–21 UTC) | 502 (40 %) | ≥ 59,7 % | 5 % / 57 % / 99 % |
| RSI(14) po stronie 50 | 1 254 (100 %) | ≥ 57,6 % | 13 % / 96 % / 100 % |

Żeby którykolwiek filtr dało się uczciwie potwierdzić, musiałby podnieść trafność do **60–65 %**. Samo przecięcie EMA
10/30 na 4h trafiało w 43,6 % (A2), a żadna cecha w projekcie nie przesunęła trafności nawet o punkt. **RSI nie odfiltrował
ani jednego sygnału.** Przy każdym przecięciu średnich potwierdzonym przez MACD RSI jest już po właściwej stronie 50.
Trzeci wskaźnik z tej samej ceny mówi to samo co dwa pierwsze.

## Metadane

- Branch `mx2-filtry-1h` (z `master` `7f92e1b`). Kod: `agents/mx_filters.py` (filtry), `tests/test_mx_filters.py` (6),
  `backtest/run_mx2_filtry.py` (tylko rachunek ex ante). Komenda: `PYTHONUTF8=1 py -m backtest.run_mx2_filtry --moc`
  → `moc.txt` (8 s). Druga droga: `PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-25_mx2-filtry-1h/druga_droga.py`
  → `druga_droga.txt`.
- Dane, przyrząd i populacja bez zmian wobec MX1 (1h BTC od 2021-01-01, 48 168 świec; reguły jak A2 na bazie Y1;
  populacja 46 368 świec — zgodna z Y1/MX1; sygnał bazowy MX1 1 254 — zgodny).

## Poprzedzające wyniki

- **MX1 (wniosek 103):** MACD, potem EMA 10/30 na 1h — 1 254 sygnały, trzeba ≥ 56,8 %, NIEMIERZALNE; MACD przepuszcza
  77 % przecięć EMA.
- **A1 (A1: 22 % × S/O 20 % ≈ 4 % świec):** kombinacja filtrów = przecięcie zbiorów, n maleje geometrycznie.
- **Faza 0 (wniosek 20):** filtr reżimu zagłodził próbę, nie poprawił trafności; C2d — pozorny zysk mieszkał
  w świecach odfiltrowanych.
- **Faza 0 / C2.7:** RSI, ADX i z-score wolumenu były już cechami modelu 4h (`rsi_14`, `adx_14`, `volume_zscore_20`) —
  model trafiał ~50 %.

## Pre-rejestracja (zapisana przed jakimkolwiek wynikiem transakcji)

**Pięć pól:** jak MX1 (OHLCV własne BTC; reguła bez modelu; kierunek; 1h; rodzina A5). Filtry = 5 wariantów tej samej
reguły (licznik serii MX), jeden zestaw parametrów każdy, bez strojenia:
- `trend28` — znak zwrotu z 28 dni zgodny z kierunkiem (definicja trendu TS1 z dziennika; 672 świece 1h wstecz);
- `adx25` — ADX(14) > 25 (Wilder, podręcznikowe „rynek w trendzie”);
- `wolumen` — wolumen świecy powyżej średniej 20 świec (`volume_zscore_20 > 0`);
- `sesja_usa` — świeca sygnału otwarta 13:00–20:59 UTC (stałe okno, bez korekty czasu letniego);
- `rsi50` — RSI(14) > 50 dla long, < 50 dla short (potwierdzenie momentum; wariant „wykupienia” 70/30 NIE mierzony).
Wszystkie wejścia z danych ≤ t, na ciągłym szeregu (test przecieku na 4 cięciach).

**Kryterium (gdyby startowała):** POZYTYWNY przy `t_neff > z_5` ORAZ `ci_low(p; z_5) > p*`, z_5 = 2,576 (pięć ramion naraz,
jak A2); NEGATYWNY przy `t_neff < −1,96` i `n ≥ required_trades(0,50; BE)`. **Mierzalność (zasada 18):** jak MX1 — zakładana
trafność 56 %, próg odniesienia = max(wzór 0,5(1 + C/B) na świecach sygnału, p* Y1 54,01 %), bramka przy z = 1,96.
Zapisane z góry: skoro cały zbiór MX1 był NIEMIERZALNY przy 56 %, każdy jego podzbiór też będzie (mniej sygnałów →
szerszy przedział) — rachunek pokazuje, JAK mocny musiałby być każdy filtr. **NIEMIERZALNA → nie startuje.**

## Wynik — rachunek mierzalności (`moc.txt`)

| filtr | sygnały | bramka kosztowa | long / short | bariera (mediana) | half-width | trzeba (z = 1,96) | trzeba (z_5) | zasada 18 |
|---|---|---|---|---|---|---|---|---|
| MX1 bez filtra (odniesienie) | 1 254 | 2 | 616 / 638 | 1,079 % | 2,78 pp | 56,79 % | 57,62 % | NIEMIERZALNA |
| trend 28 dni zgodny | 585 | 0 | 287 / 298 | 1,049 % | 4,07 pp | 58,08 % | 59,38 % | NIEMIERZALNA |
| ADX(14) > 25 | 302 | 0 | 172 / 130 | 1,294 % | 5,66 pp | 59,67 % | 61,33 % | NIEMIERZALNA |
| wolumen > średnia 20 | 684 | 1 | 315 / 369 | 1,090 % | 3,76 pp | 57,77 % | 58,97 % | NIEMIERZALNA |
| sesja USA 13–21 UTC | 502 | 0 | 229 / 273 | 1,114 % | 4,39 pp | 58,40 % | 59,72 % | NIEMIERZALNA |
| RSI(14) po stronie 50 | 1 254 | 2 | 616 / 638 | 1,079 % | 2,78 pp | 56,79 % | 57,62 % | NIEMIERZALNA |

Próg odniesienia we wszystkich wierszach 54,01 % (p* Y1 wyższe niż wzór na świecach sygnału). Dokładna moc (dwumian, wymóg
z_5) przy prawdziwej trafności 56 / 58 / 60 / 62 / 65 %: trend 5,5 / 26,4 / 63,7 / 91,0 / 99,8 %; ADX 3,5 / 13,3 / 34,1 /
61,9 / 91,7 %; wolumen 6,4 / 31,8 / 72,2 / 95,2 / 100 %; sesja USA 5,1 / 23,2 / 57,0 / 86,3 / 99,4 %; RSI 13,0 / 61,7 / 95,9 /
99,9 / 100 %. Strona negatywna wymagałaby n ≥ 1 215 — spełnia ją tylko RSI (= MX1).

## Co na plus (+) / Co na minus (−)

**(+)** pięć pomysłów sprawdzonych w 8 sekund bez jednego odczytu wyniku (żaden nie powiększył licznika prób na historii
2021–2026); liczby potwierdzone niezależną drogą co do sztuki; czerwona flaga (RSI 100 %) wyjaśniona rozkładem, a nie
założeniem; odpowiedź „jak dobry musiałby być filtr” jest liczbą (60–65 %), nie opinią.

**(−)** runda nie mówi, czy filtry działają — mówi, że historia 1h BTC 2021–2026 nie pozwala tego uczciwie rozstrzygnąć;
zakładane 56 % to konwencja projektu (A1/A2/Y1/MX1), nie pomiar; okno sesji USA bez korekty czasu letniego (latem sesja
kasowa to 13:30–20:00 UTC, zimą 14:30–21:00 — okno 13–21 obejmuje oba); filtr trendu użył definicji z dziennika (28 dni),
nie np. średniej 200 — inna definicja to inny wariant.

**Kogo nie ma:** jak w MX1 (pierwsze 60 dni i ostatnie 15 dni czerwca 2026 poza populacją; sygnały odcięte bramką kosztową
wyliczone w tabeli: 0–2).

## Wniosek

Filtry nie naprawiają problemu MX1. Każdy odcina od 45 % do 76 % sygnałów i podnosi wymaganą trafność do 58–61 %.
Jedyny filtr, który nic nie odcina (RSI), nic też nie wnosi, bo przy przecięciu potwierdzonym przez MACD RSI zawsze już
„potwierdza”. Kombinowanie wskaźników liczonych z tej samej ceny zmniejsza liczbę przykładów szybciej, niż może dodać
informacji. Na jednym aktywie i 5,4 roku świec godzinowych nie da się tego rozstrzygnąć w żadną stronę.

## Rekomendacja

1. Zamknąć serię MX (MX1 + MX2: 6 pomysłów, 0 odczytów wyniku). Dalsze filtry i kombinacje na BTC — nie: każda kolejna
   odcina sygnały, a wymagana trafność rośnie.
2. Jeśli użytkownik chce jednak odpowiedzi „czy MACD + EMA działa”: jedyna mierzalna droga to ta sama reguła (bez filtrów)
   na kilkunastu monetach naraz — najpierw rachunek, ile niezależnych sygnałów to daje (monety ruszają się razem); osobna
   decyzja i pre-rejestracja. Rekomendacja Claude: nie — prior niski (A2 43,6 %, M1, Y1, STW 1999), a projekt ma ~41
   odczytów na tej historii (DSR, wniosek 96).

## Bramki jakości (CLAUDE.md zasada 16)

- **16a walidacja (`data:validate-data`): Ready.** Druga droga (TA-Lib + numpy, bez kodu `agents/`): MX1 1 256 = 1 254 + 2,
  trend 585 = 585 + 0, ADX 302 = 302 + 0, wolumen 685 = 684 + 1, sesja 502 = 502 + 0, RSI 1 256 = 1 254 + 2 — co do sztuki.
  Czerwona flaga „RSI przepuszcza 100 %”: RSI na świecach sygnału long min 50,6 (mediana 58,3), short max 49,6 (mediana
  41,5) — własność sygnału, nie błąd.
- **16b statystyka (`data:statistical-analysis`):** pięć ramion → Bonferroni z_5 = 2,576 w wymogu pozytywu; moc dokładna
  (dwumian) zamiast samego half-width; zapisane z góry, że podzbiór zbioru niemierzalnego przy tej samej zakładanej
  trafności nie może być mierzalny.
- **16c przegląd diffu (`engineering:code-review`): Approve** — filtry jako czyste funkcje z danych ≤ t, NaN = „nie
  przechodzi”, granice nieostre zgodnie z definicją (ADX 25 i RSI 50 nie przechodzą); skrypt tylko ex ante (bez
  nieprzetestowanej ścieżki symulacji — lekcja z MX1). Testy: brak przecieku na 4 cięciach, granice każdego filtra,
  filtrowany sygnał = podzbiór MX1 w tym samym kierunku.

## Użyte skille (CLAUDE.md zasada 19)

Wynik `py tools/skill_audit.py raport --galaz mx2-filtry-1h` — 8 wczytań, 8 skilli:

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → MX1/A1/Faza 0 → mierzalność przed startem → bramki → DoD |
| `anthropic-skills:clas5-quant` | filtry = przecięcie zbiorów (n maleje), pięć ramion → Bonferroni, NIEMIERZALNA = nie startuje |
| `anthropic-skills:ta-toolkit` | definicje ADX/RSI/wolumenu/trendu bez przecieku; RSI 50 jako potwierdzenie, nie 70/30 |
| `anthropic-skills:quant-strategy-catalog` | filtry = warianty tej samej rodziny A5 w liczniku; zakaz wyboru najlepszego po wyniku |
| `engineering:testing-strategy` | granice filtrów i NaN jako przypadki testowe; własność „podzbiór MX1” |
| `data:validate-data` | druga droga co do sztuki; wyjaśnienie czerwonej flagi RSI 100 % |
| `data:statistical-analysis` | moc dokładna z korektą na 5 ramion; granica „podzbiór niemierzalnego” |
| `engineering:code-review` | przegląd modułu, testów i skryptu — Approve |

Bez użycia: `dataviz` (tabela wystarcza), `data:explore-data` (dane 1h znane z Y1/MX1).
