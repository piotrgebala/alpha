# Y2 — model kontrolny na interwale 1d: nowa baza, ten sam model, dłuższe okna (2026-09-23)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY (jak zapowiadano przy n ≈ 1 000):** trafność
> **50,20 % [47,07; 53,34]** wobec progu 51,70 %; zwrot netto −0,094 % [−0,344; +0,156] na
> transakcję, t_neff −0,60, n 978. Rok 2022 +92 %, 2024 −140 % — rozrzut roczny rzędu setek
> procent nominału, bo bariera to 6 % ceny. Pre-rejestracja + kod `e04ec02` → przebieg → wynik
> w commicie scalającym. **Seria Y2: 1/1, STOP.** Walidacja (16a): **READY**; przegląd diffu
> (16c): **Approve** (wspólny, w README Y1). Decyzja użytkownika 2026-09-23.

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Na świecach dziennych model trafia 50,2 % — jak rzut monetą — ale przy tysiącu transakcji
przedział niepewności (47,1–53,3 %) obejmuje i próg opłacalności (51,7 %), i zero.** Formalnie
nierozstrzygnięte; punktowo strata −0,09 % na transakcję. Największa różnica wobec 4h: tu
koszty prawie nie ważą (próg 51,7 % zamiast 53,6 %), więc gdyby model miał jakikolwiek sygnał,
tu miałby najłatwiej. Nie widać go: z pięciu lat dwa dodatnie (2022 duży, 2025 mały), trzy
ujemne. Żeby rozstrzygnąć, potrzeba ~4× więcej dni, których nie ma.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Ten sam model co zawsze, ale na świecach dziennych: decyzja raz dziennie, pozycja najwyżej
3 dni, bariera 1,5×ATR — na dziennych świecach to ok. 6 % ceny, więc koszty (0,08 %) prawie
nie ważą: próg opłacalności to tylko **50,7 %** trafności. Cena: mało obserwacji. Od 2021 mamy
2 007 dni, a po odjęciu pierwszego roku na trening zostaje ok. 1 640 dni, czyli ok. 970
transakcji. Rozdzielczość ±3,1 punktu — żeby uznać wynik za dodatni, trafność musiałaby
przekroczyć ok. 54 %. Okna uczenia są dłuższe (rok treningu, kwartał testu), bo 60 dni to
tylko 60 wierszy — model drzew nie ma się z czego uczyć.

## ID testu

**Y2** — nowa baza (interwał 1d), własny licznik 1/1, STOP. Inne okna walk-forward, V, bariery
na 1d — warianty tej bazy, zakazane po STOP bez decyzji użytkownika.

## Metadane

- Branch: `y-horyzont-1h-1d` (wspólny dla Y1/Y2).
- Dane: natywne świece 1d BTC/USDT:USDT (binanceusdm) pobrane 2026-09-23 od 2019-09-10 (warm-up)
  do 2026-07-01 → cache `BTC-USDT-USDT_1d_20190910T000000Z_20260701T000000Z.parquet`;
  `timeframe_start_overrides["1d"] = 2019-09-10`; `fetch_window` (zasada 20): **2 007 świec 1d**.
- Model i pipeline: jak Y1 (cechy, bariera, wejście, wyjście, koszty), `candles_per_day = 1`,
  V = 3 świece (3 dni), walk-forward **365/91/91 dni** (365 wierszy treningu ≈ 360 wierszy
  kontroli 4h; 60/28/28 dałoby 60 wierszy — parametr bazy dobrany PRZED danymi z liczby
  wierszy, nie strojony), seed `PRIMARY_SEED`. Model wypełnień jak w 4h (przybliżenie).
- Skrypt: `backtest/run_horizon_y.py 1d` (`--moc` = tylko rachunek ex ante); na `runs/ZAMROZONE.txt`.
  Komenda: `PYTHONUTF8=1 py -m backtest.run_horizon_y 1d > raw_output.txt` (1 s); druga droga
  wspólna z Y1: `runs/2026-09-23_y1-horyzont-1h/walidacja.py` → `walidacja.txt` tamże.

## Poprzedzające wyniki

Jak Y1 (wniosek 46, C2.6, wniosek 67, wniosek 12). Dodatkowo **wniosek 19/23**: przy małym n
sygnał opłacalny może być niewidzialny — na 1d luka 5,3 pp wobec half-width 3,1 pp jest
wystarczająca dla „obietnicy podręcznika" (56 %), ale efekt rzędu 52 % (1,3 pp nad progiem)
byłby NIEWIDZIALNY — zapisane z góry jako granica przyrządu.

## Pre-rejestracja

- **Hipoteza:** model kontrolny na 1d ma trafność powyżej progu 1d (50,66 %). Mechanizm jak
  Faza 0 (mean-reversion), na horyzoncie dni — gdzie literatura (LTW 2022) widzi raczej
  momentum tygodniowe; prior niski, ale koszt względem bariery jest najniższy w projekcie.
- **DOKŁADNIE JEDNA zmienna wobec kontroli 4h:** interwał (1d) — z koniecznym dostosowaniem okien
  walk-forward do liczby wierszy (365/91/91), zapisanym tu jako część definicji bazy.
- **Przyrząd i kryterium (jedno ramię, m = 1):** jak Y1.
- **Mierzalność (zasada 18, z danych 1d, przed treningiem):** ATR(14)/close mediana 4,105 %
  (p10 2,611 %, p90 6,994 %) → bariera **6,157 %** ceny; C = 0,0808 % → **próg ±B = 50,66 %**;
  OOS ≈ 1 642 świece → `expected_trades(1 642; 0,4038; 0,994)` = **973**; half-width **3,14 pp**;
  luka +5,34 pp > 3,14 → **MIERZALNA** (dla 56 %; efekty < ~54 % niewidzialne).
- **Oczekiwanie zapisane z góry:** NIEROZSTRZYGNIĘTY najbardziej prawdopodobny (mała próba);
  NEGATYWNY wymaga `t_neff < −1,96` przy n ≥ required(0,50; 50,66 %) — przy tak niskim progu
  required jest DUŻE (guard może nie być spełniony → NIEROZSTRZYGNIĘTY nawet przy ujemnym t).
- **Kontekst multiple testing:** jak Y1.
- **Czego runda NIE robi:** nie stroi okien po wyniku; nie zmienia cech; nie filtruje dni.

---

## Wynik

Pełny stdout: `raw_output.txt`. Zestawienie trzech baz (opisowe) — tabela w README Y1.

| miara | **Y2 (1d)** |
|---|---|
| n transakcji / N_eff | **978 / 643** |
| trafność `p` [CI95] | **50,20 % [47,07; 53,34]** |
| próg uogólniony `p*` / próg ±B ex post | 51,70 % / 51,41 % |
| luka `ci_high(p) − p*` | +1,64 pp (CI obejmuje próg I 50 %) |
| zwrot netto r̄ [CI95] na transakcję | **−0,094 % [−0,344; +0,156]** |
| mediana zwrotu netto | −0,054 % |
| t / t_neff | −0,74 / −0,60 |
| W̄ / L̄ / C | 3,135 % / 3,172 % / 0,0889 % |
| std zwrotu, p5/p95 | 3,98 %; [−6,67 %; +6,56 %] |
| abstynencja | 40,29 % |
| foldy aktywne / niewypełnione / stłumione | 18/18 / 0 / 0 |
| **werdykt** | **NIEROZSTRZYGNIĘTY** (wartość bezwzględna t_neff < 1,96; CI trafności obejmuje `p*`) |

**Grupy:**

| grupa | n | udział | `p` [CI95] | r̄ netto |
|---|---|---|---|---|
| cel (tp) | 155 | 15,8 % | 100 % | +5,685 % |
| stop (sl) | 181 | 18,5 % | 0 % | −5,702 % |
| timeout | 642 | 65,6 % | 52,34 % [48,47; 56,20] | +0,092 % |
| long | 535 | 54,7 % | 50,65 % [46,42; 54,89] | −0,233 % |
| short | 443 | 45,3 % | 49,66 % [45,01; 54,32] | +0,074 % |

Bariery dotykane na minus (155 tp wobec 181 sl = 46,1 % dotknięć), timeouty lekko na plus —
odwrotnie niż na 1h; wszystkie CI grup szerokie (±4 pp), żadna nie odstaje od 50 %.

**Per rok (n, `p`, Σ zwrotu netto w % nominału):**

| rok | n | `p` | Σ netto |
|---|---|---|---|
| 2022 | 233 | 48,5 % | **+92 %** |
| 2023 | 233 | 52,8 % | −40 % |
| 2024 | 212 | 47,6 % | **−140 %** |
| 2025 | 195 | 52,3 % | +8 % |
| 2026 (do 30.06) | 105 | 49,5 % | −12 % |

Pierwszy fold zaczyna się po roku treningu (2022-01), stąd brak 2021. Rok 2022 dodatni przy
trafności 48,5 % (kilka dużych wygranych tp w bessie), 2024 ujemny przy 47,6 % — przy barierze
6 % ceny pojedynczy rok ma rozrzut ±100 % nominału, więc roczne sumy są tu szumem, nie
sygnałem.

**Mierzalność ex ante vs ex post:**

| | ex ante | ex post |
|---|---|---|
| bariera | 6,157 % | tp +5,732 % / sl −5,602 % |
| próg ±B / `p*` | 50,66 % | 51,41 % / 51,70 % |
| świece OOS | ≈ 1 642 | 1 638 |
| abstynencja | 40,38 % (z 4h) | 40,29 % |
| n | 973 | 978 |
| half-width | 3,14 pp | 3,13 pp |

Zgodność ex ante/ex post co do 1 % — i dokładnie tak, jak zapowiedziano, przyrząd o
rozdzielczości ±3,1 pp nie rozstrzyga efektu rzędu ±1,5 pp wokół progu.

## Co na plus (+) / Co na minus (−)

**(+)**
- Najniższy próg opłacalności w projekcie (`p*` 51,7 %): to baza, na której sygnał — gdyby
  istniał — miałby najłatwiej. Wynik 50,2 % nie daje mu poparcia.
- Rachunek mocy z góry przewidział NIEROZSTRZYGNIĘTY (n ≈ 970, half-width 3,1 pp) i tak
  wyszło — runda nie „zaskoczyła" brakiem próby (wniosek 19 tym razem zastosowany przed).
- Okna 365/91/91 zapisane przed danymi z liczby wierszy; 18/18 foldów aktywnych; 0
  niewypełnionych, 0 stłumionych — „kogo nie ma" sprowadza się do warm-upu i abstynencji.
- Druga droga zgodna ze skryptem co do 4 miejsc.

**(−)**
- **n 978 przy half-width 3,1 pp** — pomiar nie odróżnia 50 % od 53 %; efekt „opłacalny,
  ale niewidzialny" (52–53 %) jest tu możliwy i NIE został wykluczony. Więcej danych 1d nie ma
  (zasada 20); pomiar 4× dłuższy = 20 lat.
- Model wypełnień 4h jako przybliżenie na 1d — ale 0 niewypełnionych (dzienny zakres zawsze
  dotyka wczorajszego close), więc bez wpływu.
- Rozrzut roczny ±100 % nominału przy barierze 6 % — każdy rok to ~200 transakcji po ±6 %;
  sumy roczne nie nadają się do wnioskowania (zapisane, żeby 2022 +92 % nie stało się
  „dowodem" w przyszłej rozmowie).
- Okna cech 14/20 świec = 14/20 DNI: model „mean-reversion 3-dniowej" konkuruje z literaturą
  momentum tygodniowego (LTW 2022) — prior był niski i wynik go nie zmienia.

## Walidacja (zasada 16a)

Skill `data:validate-data` wczytany PRZED walidacją. Werdykt: **READY**.

- **Druga droga** (`walidacja.py`, numpy z journalu): `p` 50,20 %, r̄ −0,0940 %, `p*` =
  (3,172 + 0,0889)/(3,135 + 3,172) = 3,2605/6,307 = 51,70 % ✓ — identycznie ze skryptem.
- **Dane:** 2 007 świec 1d, 0 duplikatów, 0 luk > 1 d, OHLC spójne.
- **Kogo nie ma:** 365 dni pierwszego treningu (2021 bez OOS), 40 % świec bez kierunku, warm-up
  cech; 0 niewypełnionych, 0 stłumionych.
- **Red-flagi:** „NIEROZSTRZYGNIĘTY przez guard n" — tu przyczyną jest |t_neff| 0,60 < 1,96
  i CI trafności obejmujące próg, nie guard (required(0,50; 51,41 %) nie był potrzebny do
  odczytu). Spójność: 155 + 181 + 642 = 978 ✓; 535 + 443 = 978 ✓; Σ lat = 978 ✓.
- **Bramka 16b:** CI z N_eff 643 ≤ n; mediana −0,054 % obok średniej −0,094 %; per rok
  opisowo z ostrzeżeniem o rozrzucie; kontekst ~22 odczytów dnia.

## Przegląd diffu (zasada 16c)

Wspólny dla Y1/Y2 — zapisany w README Y1. **Werdykt: Approve.**

## Wniosek

**Prostym językiem:** na świecach dziennych model trafia **50,2 %** — dokładnie jak rzut
monetą. Tu koszty prawie nie ważą (wystarczyłoby 51,7 %), więc gdyby model cokolwiek
„wiedział", byłoby to najłatwiejsze miejsce, żeby to zobaczyć. Nie widać. Ale próba to tylko
978 transakcji, więc niepewność (±3 punkty) jest za duża, żeby powiedzieć „na pewno nie":
wynik jest **nierozstrzygnięty**, tak jak zapowiedziano przed uruchomieniem. Dodatkowych dni
nie ma skąd wziąć.

**Technicznie:** NIEROZSTRZYGNIĘTY (t_neff −0,60; CI trafności [47,1; 53,3] obejmuje `p*` 51,7 %
i 50 %); ex ante/ex post zgodne co do 1 %; efekt 52–53 % niewykluczony i niewidzialny tym
przyrządem (wniosek 23).

## Rekomendacja

1. **Seria Y2: 1/1, STOP.** Warianty (inne okna, V w dniach, bariera) zakazane bez decyzji
   użytkownika; żaden nie zwiększy n, a n jest jedynym ograniczeniem tej bazy.
2. **Nie interpretować lat.** 2022 +92 % i 2024 −140 % to rozrzut bariery 6 %, nie reżimy.
3. Wniosek zbiorczy (69): model kontrolny na trzech bazach 1h/4h/1d — 48,3 / 49,6 / 50,2 %;
   1h rozstrzygnięte negatywnie z ogromnym zapasem, 4h negatywnie, 1d nierozstrzygnięte przez
   n. Zmiana horyzontu nie jest drogą; jeśli dzienny horyzont ma być badany dalej, to z INNYM
   zbiorem informacyjnym lub INNĄ formułą (przekrojową), nie tym modelem — decyzja użytkownika.

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
