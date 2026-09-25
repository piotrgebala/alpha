# MX1 — przecięcie MACD, a potem EMA 10/30, na świecach 1h BTC (2026-09-25)

> **STATUS: NIEMIERZALNA — runda NIE wystartowała** (CLAUDE.md zasada 18). Decyzja użytkownika: „połączenie przecięcia
> MACD z późniejszym EMA cross 10/30 — sprawdź na interwale 1h”. Nowa hipoteza z własnym licznikiem (seria MX). Policzono
> WYŁĄCZNIE częstość sygnałów, barierę i próg — żadnej transakcji nie zasymulowano, żadnego wyniku nie obejrzano.
> **0 wariantów zużytych.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Reguła: kupuj, gdy średnia z 10 godzin przetnie od dołu średnią z 30 godzin, ale tylko wtedy, gdy MACD przeciął swoją linię
sygnału w górę już wcześniej. Sprzedaj krótko w lustrzanej sytuacji. Na 5,4 roku świec godzinowych BTC daje to **1 254
sygnały** (ok. 230 rocznie). Żeby z takiej liczby uczciwie wykazać zysk po kosztach, reguła musiałaby trafiać w **co najmniej
56,8 %** przypadków. Podręcznik obiecuje ok. 56 %. Nawet gdyby ta obietnica była prawdziwa, sprawdzian potwierdziłby ją tylko
z szansą **29 %**. Sprawdzian, który w dobrym scenariuszu częściej nie wie niż wie, niczego nie rozstrzyga, więc zgodnie
z zasadą 18 nie startuje. Przy okazji wyszło, że MACD przepuszcza **77 %** przecięć średnich. Kombinacja to w trzech
czwartych samo przecięcie EMA. Na świecach 4h samo przecięcie EMA 10/30 trafiało w 43,6 % [38,8; 48,4], czyli poniżej
rzutu monetą (A2).

## Metadane

- Branch `mx1-macd-ema-1h` (z `master` `a7356fb`). Kod: `agents/ta_macd.py` (MACD, reguła), `tests/test_ta_macd.py` (15),
  `backtest/run_mx1_macd_ema.py` (tylko rachunek ex ante). Komenda: `PYTHONUTF8=1 py -m backtest.run_mx1_macd_ema --moc`
  → `moc.txt` (6 s). Druga droga: `PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-25_mx1-macd-ema-1h/druga_droga.py`
  → `druga_droga.txt`.
- Dane: natywne świece 1h BTC/USDT:USDT (cache Y1), od 2021-01-01 (zasada 20) do 2026-06-30: 48 168 świec, 0 przerw.
- Przyrząd (zamrożony, bez zmian): reguły jak A2 (`checkpoint_lib.build_rule_signals` — populacja = okna OOS pipeline'u
  modelowego, bramka kosztowa silnika, wejście limit po close k = 1, bariera 1,5·ATR, V = 3 świece, pojedyncze wyjście)
  na bazie 1h jak Y1 (walk-forward 60/28/28 dni, 24 świece na dzień). Populacja 46 368 świec — **identyczna z Y1**.

## Poprzedzające wyniki

- **A2 (wnioski 51, 53):** przecięcie EMA 10/30 na 4h osobno NIEMIERZALNE (434 sygnały); w grupie zdarzeń 415 transakcji,
  43,6 % [38,8; 48,4], −0,12 %/tr. Seria A 7/7 STOP — nowe reguły AT tylko decyzją użytkownika (jest).
- **M1 / Faza 0:** `ema_diff_9_21` (linia MACD z oknami 9/21) jako cecha modelu: 49,74 %, n 8 512 — dowód braku.
- **Y1 (wniosek 69):** baza 1h — model trafia 48,3 % [47,7; 49,0], p* 54,01 %; cechy z wykresu na 1h wskazują raczej
  kierunek odwrotny. Baza 1h zamknięta STOP — nowy pomiar tylko decyzją użytkownika (jest).
- **Literatura (`ta-toolkit` evidence):** reguły średnich (BLL 1992) tracą przewagę po korekcie na przeszukiwanie (STW 1999).
- **Liczba odczytów na historii 2021–2026 ≈ 41** (wniosek 96) — nawet dodatni wynik wymagałby korekty (DSR).

## Pre-rejestracja (zapisana przed jakimkolwiek wynikiem transakcji)

**Pięć pól katalogu:** zbiór informacyjny = OHLCV własne BTC (jak Faza 0 — prior niski); formuła = jednoaktywowa, reguła
bez modelu; target = kierunek (±1,5·ATR, V = 3 h); horyzont = intraday 1h; status = rodzina A5, kombinacja niezmierzona.
**Mechanizm (deklarowany):** potwierdzenie momentum dwoma wskaźnikami ma odsiać fałszywe przecięcia („whipsaw”). Kontr-prior:
oba wskaźniki to ważone średnie tych samych przeszłych zmian ceny — drugi wskaźnik niewiele dodaje (sprawdzone niżej: 77 %).

**Definicja (parametry podręcznikowe, jeden zestaw, bez wariantów; `agents/ta_macd.py`):**
- linia MACD = EMA12 − EMA26 (zamknięcia), linia sygnału = EMA9 linii MACD, histogram = MACD − sygnał;
  EMA jak w A2: `ewm(span, adjust=False, min_periods=span)`;
- sygnał w świecy t: świeże przecięcie EMA 10/30 (jak A2) w kierunku d ORAZ histogram MACD ma znak d w świecy t−1 i t
  (MACD przeciął linię sygnału w kierunku d **wcześniej** i nie zawrócił; przecięcie w tej samej świecy nie liczy się
  jako „wcześniej”); wejście od t+1; liczone na ciągłym szeregu świec (bez zaglądania w przyszłość — test na 6 cięciach).

**Ramiona:** MX1 = kandydat (1 wariant, m = 1). „Samo przecięcie EMA 10/30” = odniesienie opisowe (0 wariantów, bez werdyktu).
**Kryterium (bez zmian od W1b):** POZYTYWNY `t_neff > 1,96` ORAZ `ci_low(p) > p*`; NEGATYWNY `t_neff < −1,96` przy
`n ≥ required_trades(0,50; BE)`; inaczej NIEROZSTRZYGNIĘTY. Pozytyw i tak wymagałby korekty na ~41 odczytów (DSR).
**Mierzalność (zasada 18):** `oczekiwane_n` z częstości sygnału (reguła — bez abstynencji), `expected_trades(n; 0; 0,994)`;
próg odniesienia = wyższy z dwóch: wzór 0,5(1 + C/B) na świecach sygnału (C = 0,0808 %) i p* zmierzone w Y1 (54,01 %);
zakładana trafność 56 % („obietnica podręcznika” — konwencja A1/A2/Y1). **NIEMIERZALNA → runda nie startuje.**
**Reguła STOP serii MX:** 1 wariant. Zakazane bez nowej decyzji użytkownika: inne okna MACD/EMA, okno czasu między
przecięciami, wersja „stan” zamiast „zdarzenia”, inne interwały, inne V/bariery, odwrócenie znaku, podzbiory (np. tylko long).

## Wynik — rachunek mierzalności (`moc.txt`)

| ramię | sygnały OOS (long / short) | bariera (mediana) | próg ±B ze wzoru | próg odniesienia | n oczekiwane | half-width | trzeba zmierzyć | werdykt dla 56 % |
|---|---|---|---|---|---|---|---|---|
| **MX1: MACD, potem EMA 10/30** | **1 254** (616 / 638) | 1,079 % | 53,75 % | 54,01 % | 1 246 | 2,78 pp | **≥ 56,79 %** | **NIEMIERZALNA** |
| odniesienie: samo EMA 10/30 | 1 623 (812 / 811) | 1,067 % | 53,78 % | 54,01 % | 1 613 | 2,44 pp | ≥ 56,45 % | NIEMIERZALNA |

- Populacja: 69/69 okien, 46 368 świec — zgodna z Y1 co do sztuki; bramka kosztowa odrzuciła 2 sygnały MX1 (3 EMA);
  przecięć MACD w oknie: 3 560. **MACD przepuszcza 77,3 % przecięć EMA 10/30.**
- **Moc (dokładnie, dwumian; `druga_droga.txt`):** potwierdzenie wymaga ≥ 708 trafień z 1 246 (56,82 %). Szansa potwierdzenia
  przy prawdziwej trafności: 54 % (próg) → 2,4 % (fałszywy alarm, jak zaprojektowano); **56 % → 28,9 %**; 58 % → 80,8 %;
  60 % → 99,0 %. Strona negatywna byłaby mierzalna (n 1 246 ≥ 1 215) — sprawdzian mógłby regułę tylko „zabić”, nie potwierdzić.

## Co na plus (+) / Co na minus (−)

**(+)** rachunek przed jakimkolwiek wynikiem uchronił kolejny odczyt na tej samej historii (~41. z kolei); definicja zapisana
jako czysta funkcja z testem przecieku; populacja i liczby potwierdzone niezależną drogą co do sztuki; odpowiedź na pytanie
„czy MACD coś dodaje do przecięcia EMA” jest liczbą (77 % tych samych sygnałów), a nie opinią.

**(−)** runda nie mówi, czy reguła działa — mówi, że na 1h BTC 2021–2026 nie da się tego uczciwie rozstrzygnąć; próg
odniesienia 54,01 % pochodzi z Y1 (inny sygnał, ten sam silnik i baza) — wzór na świecach sygnału daje 53,75 %; przy nim
potrzebne 56,53 %, werdykt ten sam; zakładane 56 % to konwencja, nie pomiar.

**Kogo nie ma w populacji:** pierwszych 60 dni (styczeń–luty 2021 — tylko trening modelu wyznaczającego okna), ostatnich
15 dni czerwca 2026 (poza pełnym oknem testowym), 2 sygnałów odciętych bramką kosztową; danych sprzed 2021 (zasada 20).

## Wniosek

Połączenie „najpierw przecięcie MACD, potem przecięcie EMA 10/30” na świecach godzinowych BTC daje za mało sygnałów, żeby
z 5,4 roku wykazać zysk: potrzebna trafność (≥ 56,8 %) jest wyższa niż obietnica podręcznika (56 %), a przy tej obietnicy
sprawdzian potwierdziłby regułę tylko w 29 % przypadków. MACD jako „potwierdzenie” zostawia 77 % przecięć EMA — to w dużej
mierze ten sam sygnał, a samo przecięcie EMA 10/30 na 4h trafiało poniżej rzutu monetą (A2). Runda nie startuje; seria MX
zamknięta bez zużycia wariantu.

## Rekomendacja

1. Nie wracać do kombinacji średnich/MACD na BTC — ani na 1h, ani na 4h (4h ma jeszcze mniej sygnałów). Ten sam zbiór
   informacyjny co Faza 0 (wniosek 11), a trend tygodniowy z tej rodziny (znak zmiany ceny z 28 dni) jest już w dzienniku.
2. Jedyna droga do mierzalności: ta sama reguła na kilku–kilkunastu monetach naraz (więcej sygnałów; monety ruszają się
   razem, więc realny przyrost próby trzeba policzyć przed startem). To osobna decyzja użytkownika i nowa pre-rejestracja.
   Moja rekomendacja: nie — prior niski (A2, M1, Y1, STW 1999), a każdy kolejny odczyt obniża wiarygodność wszystkich
   dotychczasowych (DSR, wniosek 96).

## Bramki jakości (CLAUDE.md zasada 16)

- **16a walidacja (`data:validate-data`): Ready.** Druga droga przez TA-Lib (inny start EMA/MACD, niezależny kod): przecięcia
  EMA 1 626 = 1 623 + 3, sygnały MX1 1 256 = 1 254 + 2 (co do sztuki), 77,2 % vs 77,3 % (ta sama liczba przed/po bramce),
  mediana bariery 1,077 % vs 1,079 %, próg 53,75 % = 53,75 %; populacja = Y1 (46 368). Czerwona flaga „wynik idealnie
  potwierdza hipotezę” — nie dotyczy (wyniku nie liczono).
- **16b statystyka (`data:statistical-analysis`):** moc policzona dokładnie (dwumian), nie tylko przybliżeniem; przedział
  zamiast punktu; licznik: 0 wariantów, ~41 odczytów programu (DSR) zapisane jako warunek nawet dla pozytywu.
- **16c przegląd diffu (`engineering:code-review`): Approve** — czysta funkcja reguły (tylko dane ≤ t, `shift(1)` na
  ciągłym szeregu), osobny moduł, żeby nie ruszać `TA_FEATURE_FUNCTIONS` zamrożonej A2; po przeglądzie usunięta
  nieosiągalna ścieżka pełnego przebiegu (nieprzetestowany kod w zamrożonym skrypcie) — wydruk `--moc` identyczny przed
  i po. Testy: MACD niezależną pętlą, brak przecieku na 6 cięciach, 6 przypadków semantyki, NaN, właściwość (hypothesis).

## Użyte skille (CLAUDE.md zasada 19)

Wynik `py tools/skill_audit.py raport --galaz mx1-macd-ema-1h` — 8 wczytań, 8 skilli:

| czas (UTC) | skill | co wniósł |
|---|---|---|
| 17:04:53 | `anthropic-skills:clas5-runda` | procedura: gałąź → skille → poprzednie rundy (A2, Y1, M1) → mierzalność przed startem → bramki → DoD |
| 17:04:55 | `anthropic-skills:clas5-quant` | `oczekiwane_n` z częstości zdarzenia (reguła), przecięcie warunków zmniejsza n, NIEMIERZALNA = nie startuje |
| 17:04:56 | `anthropic-skills:ta-toolkit` | definicja MACD/EMA jako czysta funkcja bez przecieku; „przecięcie w tej samej świecy ≠ wcześniej”; evidence (STW 1999) |
| 17:04:58 | `anthropic-skills:quant-strategy-catalog` | pięć pól, rodzina A5, „nowa nazwa ≠ nowa hipoteza” (77 % wspólnych sygnałów z samym EMA), liczba odczytów do DSR |
| 17:10:18 | `engineering:testing-strategy` | plan testów: niezależna implementacja, cięcia przecieku, przypadki brzegowe semantyki, właściwość |
| 17:10:19 | `data:validate-data` | druga droga przez TA-Lib, populacja vs Y1, „kogo nie ma” |
| 17:10:20 | `data:statistical-analysis` | moc dokładna (dwumian) zamiast samego half-width; ryzyko fałszywego alarmu przy progu |
| 17:10:21 | `engineering:code-review` | przegląd modułu, testów i skryptu; usunięcie nieosiągalnej ścieżki |

Skille z tabeli zasady 19 bez użycia: `dataviz` — bez wykresu (tabela wystarcza); `data:explore-data` — dane 1h znane
z Y1 (0 przerw sprawdzone w `moc.txt`).
