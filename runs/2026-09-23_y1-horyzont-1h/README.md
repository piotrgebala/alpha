# Y1 — model kontrolny na interwale 1h: nowa baza, ten sam model (2026-09-23)

> **STATUS: ZAMKNIĘTA — NEGATYWNY z ogromnym zapasem:** trafność **48,34 % [47,70; 48,98]** —
> cały przedział PONIŻEJ rzutu monetą — wobec progu 54,01 %; zwrot netto −0,078 %
> [−0,090; −0,066] na transakcję, t_neff −11,74, n 23 334 (41× wymaganego). Ujemny w każdym
> z 6 lat. Pre-rejestracja + kod `e04ec02` (jeden commit dla Y1/Y2) → przebieg → wynik w commicie
> scalającym. **Seria Y1: 1/1, STOP.** Walidacja (16a): **READY**; przegląd diffu (16c):
> **Approve** (wspólny dla Y1/Y2, w tym README). Decyzja użytkownika 2026-09-23: „dla 2 sprawdź
> horyzont 1h oraz 1d".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Na świecach godzinowych ten sam model trafia GORZEJ niż rzut monetą: 48,3 % przy progu
opłacalności 54 %.** Próba jest ogromna (23 tysiące transakcji), więc to nie jest pech —
przedział niepewności (47,7–49,0 %) w całości leży poniżej 50 %. Model traci na 1h w każdym
roku, średnio −0,08 % na transakcję. Co to znaczy: krótszy horyzont nie pomaga; zaszkodził
podwójnie — koszty ważą więcej (bariera to tylko 0,7 % ceny), a cechy z wykresu na godzinowych
świecach wskazują kierunek raczej odwrotny niż właściwy. To jest najbardziej rozstrzygnięty
wynik negatywny w projekcie.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Do tej pory model decydował na świecach 4-godzinnych i trzymał pozycję najwyżej 12 godzin.
Sprawdzamy ten sam model (te same 4 cechy, ta sama bariera 1,5×ATR, to samo wejście i wyjście)
na świecach 1-godzinnych: decyzje co godzinę, pozycja najwyżej 3 godziny. Na tym horyzoncie
bariera jest wąska (ok. 1,1 % ceny), więc koszty ważą więcej: model musi trafiać w **53,6 %**
przypadków, żeby wyjść na zero (na 4h: 53,1 %). Za to próba jest ogromna — ok. 27 700
transakcji — więc odpowiedź będzie precyzyjna (±0,6 punktu). Oczekiwanie: jak na 4h,
trafność koło 50 % — ale to jest pomiar, nie założenie.

## ID testu

**Y1** — nowa baza (interwał 1h), własny licznik 1/1, STOP. Inne bariery, inne V, inne okna
walk-forward na 1h — warianty tej bazy, zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `y-horyzont-1h-1d` (wspólny dla Y1/Y2; rejestr skilli wspólny).
- Dane: natywne świece 1h BTC/USDT:USDT (binanceusdm) pobrane 2026-09-23 od 2020-12-01 (warm-up)
  do 2026-07-01 → cache `BTC-USDT-USDT_1h_20201201T000000Z_20260701T000000Z.parquet`;
  `config/settings.yaml` → `timeframe_start_overrides["1h"] = 2020-12-01` (jedno miejsce);
  `fetch_window` nakłada zasadę 20 (od 2021-01-01): **48 168 świec 1h**.
- Model i pipeline: `REVERSION_FEATURES` (okna w ŚWIECACH: `rsi_14`, `*_zscore_20`,
  `return_lag_1` — natywnie per interwał, Z9), bez bramki reżimu, wagi klas `balanced`,
  V = 3 świece (3 h), bariera 1,5·ATR, wejście limit po close k = 1, pojedyncze wyjście,
  koszty z config, `candles_per_day = 24`, walk-forward **60/28/28 dni** (jak 4h: 1 440 świec
  treningu), seed `PRIMARY_SEED`. Model wypełnień (`FILL_MODEL_PATH`) jak w 4h — kalibrowany
  na 5m dla świec 4h; na 1h przybliżenie (zapisane jako ograniczenie).
- Skrypt: `backtest/run_horizon_y.py 1h` (`--moc` = tylko rachunek ex ante); na
  `runs/ZAMROZONE.txt`. Komenda: `PYTHONUTF8=1 py -m backtest.run_horizon_y 1h > raw_output.txt`
  (7 s); druga droga: `PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-23_y1-horyzont-1h/walidacja.py`
  → `walidacja.txt` (obie bazy).

## Poprzedzające wyniki

- **Wniosek 46 / kontrola 4h (nowa baza):** p 49,58 % [48,39; 50,77], −0,107 % na transakcję,
  p* 53,64 %, abstynencja 40,4 %, n 6 789 — odniesienie (inna baza, nie porównanie 1:1).
- **C2.6 (stara baza, resample z 5m, V = 12 świec):** progi 5m 82,8 % → 1h 56,8 % → 4h 54,6 %
  przed modelem maker/taker; tam 1h było agregatem z 5m i miało V = 12 (12 h). Y1 to natywne 1h,
  V = 3 (3 h), model wykonania W1 — inna konstrukcja, nie powtórka.
- **Wniosek 67:** dokładanie cech nie wyprowadza modelu 4h ponad próg — Y1/Y2 zmieniają BAZĘ,
  nie cechy.
- **Wniosek 12:** Faza 0 nie wykazała nic o innych horyzontach po naprawach — Y1/Y2 to
  pierwsze pomiary innych interwałów na nowej metodologii.

## Pre-rejestracja

- **Hipoteza:** model kontrolny na 1h ma trafność powyżej progu opłacalności 1h. Mechanizm:
  ten sam co Faza 0 (mean-reversion krótkoterminowa: `rsi_14`, z-score ceny/wolumenu,
  `return_lag_1`) — na 1h reakcje są szybsze, ale koszt względem bariery wyższy.
- **DOKŁADNIE JEDNA zmienna wobec kontroli 4h:** interwał (1h). Wszystko inne bez zmian.
- **Przyrząd i kryterium (jedno ramię, m = 1):** POZYTYWNY `t_neff > 1,96` ORAZ `ci_low(p) > p*`;
  NEGATYWNY `t_neff < −1,96` przy `n ≥ required`; inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (zasada 18, z danych 1h, przed treningiem):** ATR(14)/close mediana 0,742 %
  (p10 0,353 %, p90 1,442 %) → bariera 1,5·ATR ≈ **1,112 %** ceny; C = 0,0808 % (ten sam model
  wykonania) → **próg ±B = 53,63 %**; OOS ≈ 46 728 świec → `expected_trades(46 728; 0,4038; 0,994)`
  = **27 692**; half-width **0,59 pp**; luka (0,56 − 0,5363) = +2,37 pp > 0,59 → **MIERZALNA**.
  Abstynencja 4h jako założenie ex ante — ex post raportowana.
- **Oczekiwanie zapisane z góry:** trafność ~50 % (jak na wszystkich dotychczasowych bazach);
  przy n ≈ 27 700 wynik będzie rozstrzygnięty NEGATYWNIE z ogromnym zapasem, chyba że 1h
  faktycznie niesie sygnał ≥ 53,6 %.
- **Kontekst multiple testing:** dwie bazy naraz (Y1, Y2) + ~20 odczytów dnia.
- **Czego runda NIE robi:** nie stroi V ani bariery pod 1h; nie zmienia cech; nie filtruje
  godzin/dni tygodnia; nie łączy z 4h.

---

## Wynik

Pełny stdout: `raw_output.txt`. Kryterium dwóch warunków, jedno ramię (m = 1).

| miara | **Y1 (1h)** | Y2 (1d, inna baza) | kontrola 4h (wniosek 46, inna baza) |
|---|---|---|---|
| n transakcji / N_eff | **23 334 / 19 977** | 978 / 643 | 6 789 / — |
| trafność `p` [CI95] | **48,34 % [47,70; 48,98]** | 50,20 % [47,07; 53,34] | 49,58 % [48,39; 50,77] |
| próg uogólniony `p*` | 54,01 % | 51,70 % | 53,64 % |
| luka `ci_high(p) − p*` | **−5,03 pp** | +1,64 pp | −2,87 pp |
| zwrot netto r̄ [CI95] na transakcję | **−0,0776 % [−0,0896; −0,0656]** | −0,094 % [−0,344; +0,156] | −0,107 % [−0,149; −0,065] |
| mediana zwrotu netto | −0,115 % | −0,054 % | — |
| t / t_neff | −12,69 / **−11,74** | −0,74 / −0,60 | — |
| W̄ / L̄ / C | 0,710 % / 0,659 % / 0,0801 % | 3,135 % / 3,172 % / 0,0889 % | — |
| abstynencja | 44,09 % | 40,29 % | 40,4 % |
| foldy aktywne | 69/69 | 18/18 | 69 |
| **werdykt** | **NEGATYWNY** (`n` 41× wymaganego 566) | NIEROZSTRZYGNIĘTY | NEGATYWNY |

Trzy bazy w jednej tabeli — **opisowo, nie jako ranking** (liczniki per baza; wytyczna o bazach).

**Grupy (Y1):**

| grupa | n | udział | `p` [CI95] | r̄ netto |
|---|---|---|---|---|
| cel (tp) | 4 547 | 19,5 % | 100 % | +1,148 % |
| stop (sl) | 4 022 | 17,2 % | 0 % | −1,272 % |
| **timeout** | **14 765** | **63,3 %** | **45,59 % [44,79; 46,40]** | **−0,130 %** |
| long | 11 096 | 47,6 % | 49,06 % [48,13; 49,99] | −0,080 % |
| short | 12 238 | 52,4 % | 47,68 % [46,79; 48,56] | −0,076 % |

Bariery same w sobie trafiają lekko na plus (4 547 tp wobec 4 022 sl = 53,1 % dotknięć), ale
63 % transakcji kończy się po 3 godzinach bez dotknięcia bariery i TAM model wskazuje kierunek
odwrotny (45,6 %, CI w całości poniżej 50 %). Long i short symetrycznie ujemne.

**Per rok (n, `p`, Σ zwrotu netto w % nominału):**

| rok | n | `p` | Σ netto |
|---|---|---|---|
| 2021 | 4 526 | 48,1 % | −313 % |
| 2022 | 4 555 | 49,1 % | −232 % |
| 2023 | 4 074 | 47,2 % | −318 % |
| 2024 | 4 393 | 48,6 % | −412 % |
| 2025 | 3 942 | 48,0 % | −399 % |
| 2026 (do 30.06) | 1 844 | 49,8 % | −137 % |

Sześć lat z sześciu ujemnych, trafność w każdym roku poniżej 50 %.

**Mierzalność ex ante vs ex post:**

| | ex ante (z danych, przed treningiem) | ex post |
|---|---|---|
| bariera | 1,112 % (1,5·mediana ATR/close) | tp +1,188 % / sl −1,182 % |
| próg ±B | 53,63 % | 55,86 % (B ex post = ½(W̄+L̄) = 0,68 %, bo timeouty zamykają się blisko zera); `p*` 54,01 % |
| świece OOS | ≈ 46 728 | 46 368 (−0,8 %: warm-up cech w foldach) |
| abstynencja | 40,38 % (założenie z 4h) | 44,09 % |
| n | 27 692 | 23 334 (25 903 kandydatów − 311 niewypełnionych − 2 258 stłumionych kill-switchem) |
| half-width | 0,59 pp | 0,64 pp |

Przyrząd zachował się jak zapowiedziano: rozdzielczość ±0,64 pp, wynik oddalony od progu
o ~9 half-width.

## Co na plus (+) / Co na minus (−)

**(+)**
- **Najbardziej rozstrzygnięty wynik w projekcie:** n 23 334 (41× wymaganego), oba warunki
  negatywu spełnione, CI trafności w całości poniżej 50 %, sześć lat z sześciu ujemnych,
  long/short symetrycznie. To nie jest „brak dowodu", to dowód braku — i to z zapasem.
- Rachunek ex ante zgodny z ex post (bariera +7 %, n −16 % przez wyższą abstynencję,
  half-width 0,59 → 0,64 pp) — zasada 18 działa jako przyrząd, nie rytuał.
- Dokładnie jedna zmienna (interwał); okna cech w świecach natywnie (Z9), bez strojenia
  czegokolwiek pod 1h; pre-rejestracja przed przebiegiem (`e04ec02`).
- Druga droga (`walidacja.py`, numpy wprost z journalu) daje te same `p`, r̄, `p*` co skrypt.

**(−)**
- **Model wypełnień kalibrowany na 5m dla świec 4h** — na 1h to przybliżenie. Kierunek
  możliwego błędu: gdyby wszystkie 311 niewypełnionych sygnałów (1,2 %) były wygranymi,
  `p` wzrosłoby do 49,0 % — nadal 5 pp poniżej progu. Wynik jest odporny na ten błąd.
- **Kogo nie ma:** 2 258 sygnałów (8,7 % kandydatów) stłumionych przez kill-switch
  (`kill_switch_active`) — na 4h ten mechanizm był zmierzony jako nieobciążający (C2c), na 1h
  nie mierzono osobno; wykluczone też świece warm-up cech i 44 % świec, w których model nie
  wskazał kierunku. Żadna z tych grup nie jest wybrana po wyniku.
- Trafność poniżej 50 % (jak A1: 46,4 %; jak wymuszony kierunek w Fazie 0: 48,3 %) — to
  trzeci raz, gdy cechy z wykresu wskazują na krótkim horyzoncie kierunek odwrotny.
  Odwrócenie znaku po wyniku to nowa hipoteza post hoc (wniosek 49), nie wariant; ekonomia ex
  ante: odwrócony sygnał dałby ~51,7 %, wciąż pod progiem 54 %. NIE testujemy.
- 63 % timeoutów: na 3-godzinnym horyzoncie większość pozycji nie dociera do bariery
  1,1 % — geometria wypłaty ±B nie opisuje tej bazy (BE ±B 55,9 % vs `p*` 54,0 %).

## Walidacja (zasada 16a)

Skill `data:validate-data` wczytany PRZED walidacją. Werdykt: **READY**.

- **Druga droga:** `walidacja.py` liczy `p`, r̄, medianę i `p*` wprost z journalu (numpy),
  z pominięciem `summarize_trade_returns` dla tych liczb — 48,34 % / −0,0776 % / 54,01 %,
  identycznie ze skryptem. `p* = (0,659 + 0,0801)/(0,710 + 0,659)` — ręcznie: 0,7391/1,3685
  = 54,01 % ✓.
- **Dane:** 48 168 świec 1h, 0 duplikatów, 0 luk > 1 h, OHLC spójne (high ≥ max(open, close),
  low ≤ min) na wszystkich wierszach. Natywne świece, bez resamplingu.
- **Kogo nie ma:** patrz (−) wyżej — warm-up, abstynencja 44 %, 311 niewypełnionych, 2 258
  stłumionych. Górne ograniczenie wpływu niewypełnionych: +0,7 pp.
- **Red-flagi:** „1h POZYTYWNY → szukać przecieku" — nie dotyczy (negatyw). „Wynik idealnie
  potwierdza oczekiwanie" — oczekiwanie brzmiało „~50 %", wyszło 48,3 % z CI poniżej 50 %:
  gorzej niż oczekiwano, nie „idealnie". Spójność: 4 547 + 4 022 + 14 765 = 23 334 ✓;
  11 096 + 12 238 = 23 334 ✓; Σ lat = 23 334 ✓; 25 903 − 311 − 2 258 = 23 334 ✓.
- **Bramka 16b** (`data:statistical-analysis`): efekt z CI z N_eff (t_neff, N_eff = 19 977 ≤ n),
  mediana obok średniej (−0,115 % vs −0,078 %: rozkład lewoskośny przez stopy), per rok
  opisowo, trzy bazy bez rankingu, ~22 odczyty dnia w liczniku.

## Przegląd diffu (zasada 16c)

Skill `engineering:code-review` wczytany PRZED przeglądem; przegląd wspólny dla Y1/Y2 (jeden
diff: `backtest/run_horizon_y.py`, `tests/test_run_horizon_y.py`, `config/settings.yaml`,
`runs/…/walidacja.py`, README ×2, `runs/ZAMROZONE.txt`).

- Korektność: `_ex_ante` liczy n_oos = świece − train·cpd (bez odejmowania warm-upu — ex post
  46 368 vs 46 728, różnica 0,8 %, nieistotna); `HORIZONS` z jawnym `candles_per_day` i oknami
  jako parametrem bazy; `fetch_window` (zasada 20) w obu skryptach.
- Edge-case'y: `_atr_fraction` NaN przez okno warm-up (test); 1d z 18 foldami przy 365/91/91
  działa (0 pominiętych); `--moc` nie trenuje.
- Testy: 3 nowe (773/773), ruff/black czyste; walidacja jako skrypt rundy (nie test).
- Czytelność: `raw_output.txt` sekcje 0–3 jak w A2/O1; README z tabelami ex ante/ex post.
- Config: `timeframe_start_overrides` 1h/1d z komentarzem — jedno miejsce; cache 4h bez zmian.

**Werdykt jednym zdaniem: Approve** — zmiana kodu jest cienka (runner + 3 testy + 2 wpisy
configu), nie dotyka silnika, etykiet ani kosztów, a skrypt trafia na listę zamrożonych.

## Wniosek

**Prostym językiem:** na świecach godzinowych ten sam model, który na 4h trafiał 49,6 %,
trafia **48,3 %** — i to przy tak dużej próbie, że przedział niepewności (47,7–49,0 %) w całości
leży poniżej rzutu monetą. Żeby zarabiać po kosztach, musiałby trafiać **54 %**. Brakuje więc
prawie 6 punktów, a rozdzielczość pomiaru to 0,6 punktu. Model traci na 1h w każdym z sześciu
lat, po ok. −0,08 % na transakcję; long i short tak samo. Skrócenie horyzontu **nie pomogło,
tylko zaszkodziło** — koszty ważą dwa razy więcej względem bariery (1,1 % zamiast 2,2 % ceny),
a sygnał nie stał się silniejszy, tylko słabszy niż moneta.

**Technicznie:** NEGATYWNY z oboma warunkami (t_neff −11,74; `ci_high(p)` 48,98 % < `p*`
54,01 %), n 41× wymaganego; ex ante/ex post zgodne; trafność < 50 % powtarza wzorzec A1 i
wymuszonego kierunku z Fazy 0 (trzeci raz). Wynik odporny na niedoskonałość modelu wypełnień
(górne ograniczenie +0,7 pp).

## Rekomendacja

1. **Seria Y1: 1/1, STOP.** Warianty tej bazy (inne V, inne bariery, inne okna, filtry godzin)
   zakazane bez decyzji użytkownika — i ŻADEN z nich nie ma jak zamknąć luki 5 pp przy
   rozdzielczości 0,6 pp: 1h jako baza dla tego modelu jest zamknięte.
2. **Nie odwracać znaku.** Pokusa „graj przeciw modelowi" (51,7 % ex ante, wciąż pod 54 %)
   to nowa hipoteza post hoc — zapisana tu, żeby nie wróciła jako „wariant".
3. Wniosek dla całego programu — w README Y2 i we wniosku skumulowanym 69: trzy bazy
   (1h / 4h / 1d) tego samego modelu, trafność 48–50 % na każdej; zmiana horyzontu nie jest
   drogą.

## Użyte skille

Rejestr `runs/skille/y-horyzont-1h-1d.jsonl` (wspólny dla Y1/Y2; `py tools/skill_audit.py raport
--galaz y-horyzont-1h-1d`): **7 wczytań, 7 różnych skilli**, wszystkie przez Claude'a, wszystkie
PRZED pracą, której dotyczyły.

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura rundy: gałąź przed skillami, pre-rejestracja obu baz w jednym commicie przed przebiegiem, katalog per baza, bramki 16a/16b/16c, DoD. |
| `anthropic-skills:clas5-quant` | pułapki zapisane z góry: próg 1h przy ogromnym n → negatyw z zapasem prawie pewny; na 1d guard `required_trades` może nie być spełniony; model wypełnień 4h jako przybliżenie; okna 1d = parametr bazy, nie strojenie; zestawienie baz tylko opisowe. |
| `anthropic-skills:quant-strategy-catalog` | pięć pól rodziny: zmienia się WYŁĄCZNIE horyzont; natywne 1h z V = 3 na nowej bazie było NIETKNIĘTE (C2.6 = resample z 5m, V = 12), 1d NIETKNIĘTE — nie powtórka; status rodziny po wyniku: „kierunek jednoaktywowy OHLCV" zmierzony na trzech bazach. |
| `engineering:testing-strategy` | plan 3 testów pomocników (`_atr_fraction`, `_ex_ante`, spójność `HORIZONS`), bez powielania testów silnika. |
| `data:validate-data` | bramka 16a: druga droga (`walidacja.py`), „kogo nie ma", red-flagi (1h POZYTYWNY → szukać przecieku; 1d przez guard), zgodność ex ante/ex post. |
| `data:statistical-analysis` | bramka 16b: efekt + CI z N_eff, mediana obok średniej, per rok opisowo, trzy bazy w jednej tabeli bez wyboru „najlepszej", kontekst ~22 odczytów dnia. |
| `engineering:code-review` | bramka 16c: przegląd diffu (runner, testy, config, walidacja) — werdykt niżej. |

**Pominięte z tabeli zasady 19 (z powodem):** `dataviz` — runda bez wykresu (tabele per rok
wystarczają); `engineering:debug` — bez błędu; `data:explore-data` — nowe cache 1h/1d to te same
świece Binance co 4h (ten sam kolektor, ten sam profil), sprawdzone w `walidacja.py` (duplikaty,
luki, spójność OHLC); `ta-toolkit`, `lean-research`, `security-review` — bez AT, LEAN, kluczy
i sieci (dane pobrane wcześniej istniejącym kolektorem).
