# A1 — formacje świecowe jako sposób szukania pozycji (2026-09-23)

> **STATUS: ZAMKNIĘTA — OBA RAMIONA NEGATYWNE.** Pre-rejestracja w commicie `f514bcf` (przed
> kodem), kod w `26f187b` (przed uruchomieniem — kolejność dowodliwa z gita), wynik w commicie
> scalającym gałąź. Runda otworzyła i zamknęła **SERIĘ A — formacje świecowe: licznik 2/2,
> reguła STOP.** Walidacja (16a): **READY**; przegląd diffu (16c): **Approve**.
> **Poprawka 2 (po przebiegu, raportowa, bez wpływu na werdykt):** N_eff w statystykach per
> transakcja ograniczone do n, jak w kanonicznej tabeli pooled — szczegóły w „Walidacji".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Formacje świecowe z podręcznika nie znajdują na wykresie BTC 4h pozycji, które zarabiają —
znajdują raczej pozycje, które tracą.** Reguła „formacja bycza → kupuj, niedźwiedzia → sprzedaj"
dała na 2 477 transakcjach trafność **46,4 %** (przedział ufności od 44,4 % do 48,3 % — czyli
cały przedział leży **poniżej rzutu monetą**) i stratę **0,18 % na transakcji** (przedział od
−0,25 % do −0,11 %). To gorzej niż model bez formacji (49,6 %, −0,11 %).

**Dlaczego tak?** 84 % sygnałów to „objęcie" — duża świeca w kierunku sygnału. Na BTC 4h po
dużej świecy cena w ciągu 12 godzin częściej zawraca, niż idzie dalej. Podręcznik czyta objęcie
jako początek ruchu; dane mówią, że to raczej jego koniec. Dwie rzadkie formacje (gwiazdy: 26
i 60 przypadków) wyglądają lepiej, ale przy tak małej liczbie ich przedziały ufności są tak
szerokie, że nic z nich nie wynika — a przy sześciu podgrupach jedna–dwie „lepsze" wychodzą
z samego przypadku.

**Ta sama informacja podana modelowi jako dodatkowa cecha nic nie zmienia:** różnica wobec
modelu bez niej to −0,001 % na transakcję (przedział od −0,012 % do +0,010 %) — zero; 6 444
z 6 577 wspólnych transakcji jest identycznych.

**Pokusa, której nie ulegamy:** skoro formacje wskazują odwrotnie, „odwróćmy regułę". To nie
jest wniosek z tej rundy, tylko nowa hipoteza wymyślona po obejrzeniu wyniku — dokładnie ten
mechanizm, który produkuje fałszywe strategie. Rachunek pokazuje też, że odwrócona reguła
zarobiłaby około +0,01 % na transakcji (zysk brutto ≈ koszt), czyli nic — a informacja „po dużej
świecy cena zawraca" to ta sama, którą model już ma w cesze „zwrot z poprzedniej świecy"
i z którą trafia 49,6 %.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Pytanie:** czy klasyczne formacje świecowe z podręcznika analizy technicznej (objęcie, młot,
spadająca gwiazda, gwiazda poranna i wieczorna, trójka hossy/bessy) wskazują na wykresie BTC 4h
pozycje, które po kosztach zarabiają?

**Jak sprawdzamy — dwa ramiona, jedna informacja:**
1. **Reguła bez modelu (A1a):** formacja zamknięta na świecy → wchodzimy w jej kierunku
   (formacja bycza = long, niedźwiedzia = short) zleceniem po cenie zamknięcia, stop i cel
   jak dotąd (±1,5·ATR), limit 12 h. Żadnego uczenia maszynowego — sam podręcznik.
2. **Model + formacje (A1b):** ta sama informacja (liczba formacji byczych minus niedźwiedzich
   na świecy) jako **jedna dodatkowa cecha** dla dotychczasowego modelu XGBoost. Kontrola:
   ten sam model bez tej cechy (dokładnie kontrola z N1).

**Definicje formacji bierzemy gotowe z biblioteki TA-Lib** — zero parametrów do dobrania,
zero „rysowania na oko". Zestaw sześciu formacji jest zestawem z podręcznika (materiał XTB
w skillu `ta-toolkit`), zapisanym przed spojrzeniem na dane — nie wybranym z 61 dostępnych
po obejrzeniu wyników. Formacja **doji** jest wyłączona, bo nie ma kierunku (TA-Lib zwraca
tylko „jest / nie ma").

**Czego się spodziewamy (uczciwie, przed wynikiem):** trafności około 50 %, jak we wszystkich
poprzednich rundach na cenie i wolumenie (wnioski skumulowane 11, 35, 39). Literatura naukowa
(Marshall, Young, Rose 2006 — 28 formacji, brak wartości predykcyjnej po bootstrapie) też daje
niski prior. Runda ma sens jako **uczciwe zamknięcie konkretnego pomysłu użytkownika**, nie
jako polowanie na edge. Liczba, która o tym rozstrzygnie: **średni zwrot netto na transakcję
z przedziałem ufności** plus trafność wobec progu opłacalności — dwa warunki naraz.

**Ile zobaczymy:** reguła da ok. 2 500 transakcji. Przy tylu przedział ufności trafności ma
±1,95 punktu. Znaczy to: jeśli formacje trafiają w ≥ 55 %, runda to pokaże; jeśli trafiają
w 53–55 % (opłacalnie, ale słabo), runda tego **nie rozstrzygnie** — zapisujemy to z góry,
żeby nie „dobierać danych" po wyniku.

---

## ID testu

**A1** — seria A (analiza techniczna), wariant 1 = ramię A1a (reguła), wariant 2 = ramię A1b
(cecha w modelu). Licznik serii A po tej rundzie: **2/2, seria zamknięta regułą STOP** (niżej).

## Metadane

- **Gałąź:** `a1-analiza-techniczna` (od master `f5041c7`, po scaleniu N1).
- **Dane:** BTC/USDT perpetual, świece **4h natywne z cache**, **od 2021-01-01** (zasada 20,
  `checkpoint_lib.fetch_window`): 12 042 świece, 2021-01-01 → 2026-06-30.
- **Pipeline (wspólny z N1/W1a):** bez bramki reżimu (`REGIME_ALL`), etykieta triple-barrier
  ±1,5·ATR, V = 3 (12 h), walk-forward 60/28/28 dni, wagi klas `balanced`, seed 42,
  wykonanie `path`: wejście `limit_close` k = 1, pojedyncze wyjście TP/SL/timeout, model
  kosztów `maker_limit`, sizing 0,5 % ryzyka, dźwignia ≤ 3×, kill-switch jak dotąd.
- **Komenda:** `py -m backtest.run_ta_a1` (na Windows z `PYTHONUTF8=1`, bo raport zawiera znaki
  spoza strony kodowej konsoli; pełny output: `raw_output.txt`; skrypt na liście
  `runs/ZAMROZONE.txt`). Buduje na `checkpoint_lib` (`fetch_window`, `summarize_result`,
  nowe pomocniki `build_rule_signals` i `summarize_trade_returns`) i `engine.collect_signals` /
  `simulate_equity`. Czas przebiegu: 6 s (dwa treningi).
- **Nowa cecha:** `cdl_score_6` w `agents/feature_miner.py` + wpis w `feature_registry.yaml`
  + test przecieku (parametryzowany po `FEATURE_FUNCTIONS`) PRZED wejściem do modelu (zasada 2).
- **Biblioteka:** TA-Lib 0.7.1 (`talib.CDL*`).

## Poprzedzające wyniki (zasada 14)

- **Z10 / wniosek 11:** 10 cech z ceny i wolumenu → p = 50,27 % [49,15; 51,38], n = 7 687.
  Wąskie gardło informacyjne. Formacje świecowe są **kolejną transformacją OHLCV** — ten sam
  zbiór informacyjny; prior niski.
- **M1 (wniosek 35):** momentum 49,74 %; **F1 (37):** funding 50,34 %; **wniosek 39:**
  zbiór OHLCV „wyczerpany w tym, co da się zmierzyć" — z zastrzeżeniem, że formacje jako
  cechy były **NIETKNIĘTE** (`ta-toolkit` concepts §2: „CLAS-5: nietknięte jako cechy").
- **C2.7 / C2.8:** screening 8 kandydatek → `bb_pctb_20` ≡ `price_zscore_20` (powtórka pod inną
  nazwą), `adx_14` OOS — mały, niejednoznaczny efekt. Lekcja: jedna cecha na raz, na OOS,
  z jawnym licznikiem; **nie wybierać po wyniku**.
- **W1a / N1 (wnioski 42–46):** wykonanie `limit_close` k = 1 wypełnia się w 99,4 %; kontrola
  na nowej bazie 2021+: p = **49,58 %** [48,39; 50,77], zwrot netto **−0,107 %**
  [−0,149; −0,065], próg ±B **53,07 %**, abstynencja 40,38 %, 69 okien, 11 592 świece OOS.
  Te liczby są odniesieniem dla obu ramion (0 wariantów).
- **W1b / N1 (wnioski 43, 45):** trafność ponad progiem może być iluzją geometrii wypłaty →
  kryterium na zwrocie netto + trafność wobec progu uogólnionego p*, dwa warunki naraz.
- **`ta-toolkit` evidence §3:** Marshall–Young–Rose 2006 — 28 formacji na DJIA, brak wartości
  predykcyjnej; rzadkie formacje (gwiazdy ~0,2 %, trójka ~0,02 % świec 4h BTC) mają problem `n`
  z góry — dlatego formacje są ZSUMOWANE w jeden wskaźnik, nie testowane osobno.

## Rozstrzygnięcia projektowe (zapisane PRZED przebiegiem)

### Pięć pól katalogu (`quant-strategy-catalog`)

| pole | wartość | uwaga |
|---|---|---|
| zbiór informacyjny | OHLCV własne (BTC) | ten sam co Faza 0 → prior niski |
| formuła | jednoaktywowa | A1a: reguła deterministyczna; A1b: XGBoost |
| target | kierunek (±1,5·ATR, 12 h) | bez zmian (zasada 3) |
| horyzont | intraday 4h / 12 h | jak N1 |
| status | **NIETKNIĘTE** (formacje świecowe jako cecha/reguła) | ≠ powtórka: nowa transformacja, inna formuła (reguła) |

**Mechanizm ekonomiczny jednym zdaniem:** formacja odwrócenia (np. młot) miałaby wychwytywać
wyczerpanie presji sprzedających w obrębie jednej–trzech świec — kto traci po drugiej stronie,
to trader, który sprzedał na dole cienia; **słabość mechanizmu:** na 4h BTC ten sam cień jest
widoczny dla wszystkich w tej samej sekundzie, więc trudno wskazać, dlaczego przewaga miałaby
przetrwać koszt 0,08 % na transakcję.

### Jedna zmienna (per ramię)

- **A1a (reguła):** źródło sygnału = formacje zamiast modelu. Wszystko inne (etykieta, wejście
  po close, wyjście, koszty, sizing, okno danych, zakres OOS) identyczne z kontrolą N1.
- **A1b (cecha):** zestaw cech modelu = `REVERSION_FEATURES + ["cdl_score_6"]` (5 cech zamiast
  4). Wszystko inne identyczne z kontrolą (ta sama funkcja `collect_signals`, te same okna).
- **Kontrola (0 wariantów):** model z `REVERSION_FEATURES` (4 cechy) — dokładnie kontrola N1,
  przeliczona w tym samym skrypcie (kontrola spójności: musi dać 49,58 % / −0,107 %).

### Definicja wskaźnika `cdl_score_6` (identyczna w kodzie i tutaj)

```
cdl_score_6(t) = Σ_k sign(CDL_k(t)),  k ∈ {CDLENGULFING, CDLHAMMER, CDLSHOOTINGSTAR,
                                        CDLMORNINGSTAR, CDLEVENINGSTAR, CDLRISEFALL3METHODS}
```

- `sign(·)` normalizuje wyjście TA-Lib do {−1, 0, +1} — TA-Lib 0.7.1 zwraca dla objęcia także
  ±80 (wariant „słabszy"); **siła formacji NIE wchodzi do wskaźnika** (zero stopni swobody).
- Wartości: liczby całkowite w [−6; +6]; na danych 2021+ zaobserwowane {−2, −1, 0, +1, +2}.
- Doji (`CDLDOJI`) wyłączone: zwraca 100 = „formacja jest", bez kierunku (na danych: wartości
  tylko {0, 1}). Włączenie zawyżałoby stronę long mechanicznie.
- TA-Lib liczy formację w świecy `t` wyłącznie z barów ≤ t (brak przecieku w funkcji);
  test przecieku i tak obowiązuje (zasada 2).

### Reguła A1a (identyczna w kodzie i tutaj)

1. **Sygnał** w świecy `t`: `cdl_score_6(t) ≠ 0`; kierunek = `sign(cdl_score_6(t))`.
   Świece z równowagą formacji byczych i niedźwiedzich (score = 0 mimo formacji) → brak sygnału.
2. **Zakres oceny:** dokładnie świece OOS pipeline'u modelowego — od początku pierwszego okna
   testowego do końca ostatniego (pierwsze 60 dni to wyłącznie trening modelu i reguła też ich
   nie używa — ta sama populacja świec co kontrola), z etykietą nie-NaN, po bramce kosztowej
   silnika (`is_cost_feasible`, na 4h odrzuca ~0 %).
3. **Wejście:** limit po `close(t)`, ważne k = 1 świecę (W1a); brak wypełnienia → sygnał
   trafia do `unfilled`. **Wyjście:** TP/SL ±1,5·ATR(t) od ceny wypełnienia, timeout na close
   świecy t + 3. Tryb 4h (bez 5m), przybliżenie konserwatywne (W1).
4. **Sizing:** `signal_confidence = 1,0` (stała — reguła nie ma pewności), ryzyko 0,5 %
   kapitału, dźwignia ≤ 3×; kill-switch jak w silniku. Zwrot per transakcja liczony w %
   nominału, więc sizing nie wpływa na kryterium (poza stłumieniami kill-switcha, raportowanymi).
5. Pozycje mogą się nakładać (kolejne świece z formacją) — jak we wszystkich rundach: każda
   sizowana niezależnie; N_eff koryguje autokorelację.

### Kryterium — zapisane PRZED uruchomieniem (osobno dla A1a i A1b)

Statystyka nośna: **średni zwrot netto na transakcję** `r̄` (% nominału wejścia) z CI 95 %
i `t_neff` (t po korekcie N_eff), plus trafność `p = udział gross_pnl > 0` z CI Walda i próg
uogólniony `p* = (L̄ + C)/(W̄ + L̄)` (N1, ADR `docs/rag/03`).

- **POZYTYWNY:** `t_neff > 1,96` **i** `ci_low(p) > p*`. → najpierw szukać przecieku, nie ogłaszać;
  potem replikacja na innym instrumencie (zasada 9), nie kolejny wariant.
- **NEGATYWNY:** `t_neff < −1,96` **i** `n ≥ required_trades(0,50; BE ±B ramienia)` (ex ante
  2 076 dla BE 53,07 %). Guard na `n` bierze się z funkcji w `metrics.py`, nie ze stałej.
- **NIEROZSTRZYGNIĘTY:** wszystko inne. W szczególności reguła z trafnością w paśmie
  [BE; BE + 1,95 pp] jest z konstrukcji nierozstrzygalna — i nie wolno tego „ratować" ani
  dodatkowymi danymi (zasada 18), ani podzbiorem formacji (STOP).
- **Sprawdzenie w granicy dużego `n` (zasada 18):** oba warunki są monotoniczne w `n` przy
  ustalonym prawdziwym efekcie (t rośnie jak √n, CI się zwęża); guard na `n` blokuje tylko
  negatyw na małej próbie. Żaden warunek nie karze ramienia osiągającego cel.
- **Porównanie parowane A1b − kontrola** (te same świece i wypełnienia): obserwacja, nie
  kryterium — jak w N1.
- **Tabela per formacja** (n, p z CI, r̄): **wyłącznie opisowa**, żadnych werdyktów per
  formacja. Powód: 6 formacji × wybór najlepszej = loteria multiple-testing (STW 1999).

### Reguła STOP serii A (formacje świecowe)

Po A1 seria formacji świecowych jest **zamknięta (2/2) niezależnie od wyniku**, chyba że
werdykt POZYTYWNY (wtedy replikacja na ETH tą samą regułą, bez retuningu). Zakazane:
podzbiory formacji, wagi, progi na `|score|`, inne formacje z pozostałych 55 TA-Lib, filtry
kontekstu („młot na wsparciu", „po trendzie"), inne interwały, inne limity czasu. **Inne rodziny
AT ze skilla** (wsparcie/opór `sr_distance`, wybicie `breakout`, struktura trendu, podwójny
szczyt, przecięcia średnich, linia trendu, Fibonacci) NIE są objęte tym STOP-em — każda byłaby
osobną rundą z własną pre-rejestracją i rachunkiem mocy, i tylko na wyraźną decyzję użytkownika,
bo prior dla wszystkich jest ten sam (transformacja OHLCV).

### Rachunek mierzalności (zasada 18) — z częstości formacji, nie z liczby świec

Zliczenie na 12 042 świecach 4h od 2021 (bez spojrzenia na wyniki):

| formacja | TA-Lib | bycza (+) | niedźwiedzia (−) |
|---|---|---|---|
| objęcie | CDLENGULFING | 1 114 (9,25 %) | 1 181 (9,81 %) |
| młot | CDLHAMMER | 371 (3,08 %) | — |
| spadająca gwiazda | CDLSHOOTINGSTAR | — | 65 (0,54 %) |
| gwiazda poranna | CDLMORNINGSTAR | 27 (0,22 %) | — |
| gwiazda wieczorna | CDLEVENINGSTAR | — | 21 (0,17 %) |
| trójka hossy/bessy | CDLRISEFALL3METHODS | 2 | 1 |
| doji (wyłączone, informacyjnie) | CDLDOJI | 2 217 (18,4 %) bez kierunku | |

Świece z ≥ 1 formacją: 2 683; konflikt (+ i − naraz): 46 → **sygnał (score ≠ 0): 2 637 =
21,9 % świec** (long 1 429, short 1 208); rozkład score {−2: 14, −1: 1 194, +1: 1 390, +2: 39}.
Udział stabilny w latach 2021–2026 (20,6–23,4 %) — sygnał nie jest artefaktem jednego okresu.

- **A1a:** `expected_trades(2 637 × 0,963 [udział OOS] ≈ 2 538; abstynencja 0; wypełnienia
  0,994) ≈ 2 523`. `wald_half_width(2 523) = 1,95 pp`; `p_detectable = 53,07 + 1,95 = 55,02 %`.
  `measurability_report`: dla zakładanej trafności 56 % → **MIERZALNA** (margines +0,98 pp);
  55 % → NIEMIERZALNA (−0,02 pp); 54 % → NIEMIERZALNA (−1,02 pp). **Werdykt: MIERZALNA dla
  hipotezy „formacje trafiają ≥ ~55 %"** — czyli dla efektu, jaki obiecuje podręcznik; słabszy
  efekt (53–55 %) jest w paśmie niewidzialnym i tak zostanie nazwany. Negatyw:
  `required_trades(0,50; 0,5307) = 2 076 ≤ 2 523` → dowód braku możliwy, jeśli p ≈ 50 %.
  Zwrot: `se ≈ 0,034 %` (std 1,7 %) → wykrywalny |r̄| ≥ 0,095 % (moc 80 %); przy p ≈ 50 %
  oczekiwane r̄ ≈ −C ≈ −0,08 % — na granicy wykrywalności (t ≈ −2,4).
- **A1b:** `expected_trades(11 592; 0,4038; 0,994) ≈ 6 870`; pasmo 1,18 pp; `p_detectable`
  54,25 %; negatyw wymagany 2 076 — spełniony z zapasem 3,3×.

### Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- Prior: **p ≈ 50 % ± 2 pp** dla obu ramion (wnioski 11/35/39, MYR 2006). Oczekiwany werdykt:
  NEGATYWNY dla A1b (n duże), NEGATYWNY lub NIEROZSTRZYGNIĘTY dla A1a (n ≈ 2 500, t ≈ −2,4
  na granicy).
- Reguła A1a **nie ma abstynencji**, więc jej próba jest kompletna i zależy tylko od częstości
  formacji — to jedyny raz w projekcie, gdy „n" nie zależy od modelu (wniosek 19 tu nie gryzie).
- Objęcie to **87 %** wszystkich formacji w zestawie — wynik A1a jest de facto wynikiem objęcia;
  zapisujemy to z góry, żeby nie „odkrywać" tego po fakcie jako wyjaśnienia.
- Red flag zapisany z góry: jeśli A1a da p > 55 % i t_neff > 1,96 — pierwsze podejrzenie to
  przeciek w budowie sygnałów (np. użycie świecy t+1) albo błąd okna, nie edge.
- Oczekiwanie dla A1b: różnica parowana wobec kontroli w paśmie ±0,02 pp (jak N1: +0,007 %),
  bo cecha ma wartość ≠ 0 w 22 % świec i model bez sygnału nie ma z czego jej użyć.

### Czego ta runda NIE raportuje i NIE interpretuje

- Werdyktów per formacja, per rok, per kierunek (long/short) — tabele opisowe tak, werdykty nie.
- Optymalizacji zestawu formacji, wag, progów, kontekstu — STOP.
- Porównań z rundami sprzed zasady 20 (inna baza danych).
- „Skuteczności" w rozumieniu podręcznika (udział wygranych bez kosztów i geometrii wypłaty)
  — zawsze obok progu opłacalności i zwrotu netto.

### Kogo NIE ma w zbiorze — zapisane z góry

78 % świec bez formacji z zestawu (9 405); 46 świec z konfliktem; świece sprzed 2021-01-01;
pierwsze 60 dni (okno treningowe modelu, wykluczone też dla reguły — ta sama populacja);
niewypełnione (~0,6 %); stłumione kill-switchem; odrzucone bramką kosztową (~0); kolejność
zdarzeń wewnątrz świecy 4h bez 5m (konserwatywnie, W1).

## Definition of Done tej rundy

- Kod: `compute_cdl_score_6` w `agents/feature_miner.py` + `FEATURE_FUNCTIONS` + wpis
  w `feature_registry.yaml`; pomocnik `build_rule_signals` w `backtest/checkpoint_lib.py`;
  skrypt `backtest/run_ta_a1.py` (neutralny reporter; werdykt podpisuje Claude w README).
- Testy (zasada 10): przeciek `cdl_score_6` (test parametryzowany po `FEATURE_FUNCTIONS`,
  ZIELONY PRZED uruchomieniem rundy — zasada 2); jednostkowe: wartości całkowite w [−6; 6],
  doji-only → 0, konflikt → 0, syntetyczne objęcie bycze → +1, normalizacja ±80 → ±1;
  `build_rule_signals`: pola zgodne z silnikiem, tylko okno OOS, etykieta NaN odrzucona,
  bramka kosztowa, kierunek = sign(score), confidence 1,0; regresja: kontrola w skrypcie
  = liczby N1 (49,58 % / −0,107 %, n 6 789). Lint ruff + black na plikach rundy.
- Bramki: `data:validate-data` (16a), `data:statistical-analysis` (16b),
  `engineering:code-review` (16c) — wczytane na tej gałęzi. `raw_output.txt`; wiersz
  w `runs/INDEX.md` + **nowy licznik serii A (2/2, STOP)** + wnioski skumulowane; STATUS
  (sekcja serii A); README (kamień milowy); skrypt na `runs/ZAMROZONE.txt`; sekcja „Użyte
  skille" z rejestru (`py tools/skill_audit.py raport --galaz a1-analiza-techniczna`).

## Wynik

### 0. Dane i lejek

12 042 świece 4h, 2021-01-01 → 2026-06-30, 69 okien walk-forward (wszystkie aktywne), **11 592
świece OOS** — ta sama populacja dla modelu i dla reguły (sprawdzone: 11 592 = 11 592).
Kontrola: abstynencja 40,38 %, 6 911 kandydatów (= N1 co do sztuki). A1b: abstynencja 40,37 %,
6 912 kandydatów. **A1a (reguła):** 9 051 świec bez formacji z zestawu lub z konfliktem,
0 bez etykiety, 0 odrzuconych bramką kosztową, **2 541 sygnałów** (long 1 380, short 1 161);
rozkład wskaźnika w oknie OOS {−2: 13, −1: 1 161, +1: 1 353, +2: 39}. Wypełnione: 2 527
(14 niewypełnionych), stłumione kill-switchem 50 → **journal 2 477**.

### 1. Kryterium — zwrot netto per trade i trafność wobec p* (dwa warunki)

| ramię | n | r̄ netto | CI 95 % | mediana | t | N_eff | t_neff | p | CI 95 % (p) | p* | BE ±B | odczyt kryterium |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kontrola (model, 4 cechy) | 6 789 | −0,107 % | [−0,149; −0,065] | −0,104 % | −5,01 | 4 919 | −4,26 | 49,58 % | [48,39; 50,77] | 53,64 % | 53,07 % | odniesienie (= N1 co do cyfry) |
| **A1a — reguła z formacji** | 2 477 | **−0,177 %** | **[−0,245; −0,109]** | −0,188 % | −5,11 | 2 477 | **−5,11** | **46,35 %** | **[44,38; 48,31]** | 53,24 % | 53,23 % | **NEGATYWNY** (n ≥ 1 870) |
| **A1b — model + cecha** | 6 779 | **−0,113 %** | [−0,155; −0,071] | −0,109 % | −5,31 | 4 573 | **−4,36** | 49,39 % | [48,20; 50,58] | 53,70 % | 53,08 % | **NEGATYWNY** (n ≥ 2 057) |

Guard negatywu `required_trades(0,50; BE ramienia)`: A1a 1 870 (n 2 477 ✔), A1b 2 057
(n 6 779 ✔). **Regresja kontroli wobec N1: ZGODNA** (n 6 789, p 49,58 %, r̄ −0,1069 %).

**A1a trafia ISTOTNIE PONIŻEJ 50 %:** górny kraniec CI 48,31 % leży 1,7 pp pod rzutem monetą
i 4,9 pp pod progiem opłacalności. To nie „brak sygnału" — to sygnał o odwrotnym znaku wobec
podręcznika, na populacji 22 % świec.

### 2. Porównanie parowane A1b − kontrola (obserwacja, nie kryterium)

6 577 wspólnych transakcji; **6 444 identycznych** (ten sam kierunek, ten sam wynik); tylko
w kontroli 212, tylko w A1b 202. Średnia różnica **−0,0012 %** nominału, 95 % CI
**[−0,0120; +0,0096]**, t = −0,21, mediana 0. Cecha zmienia decyzję modelu w ~3 % świec
i nie zmienia wyniku.

### 3. A1a opisowo — skąd biorą się pieniądze (bez werdyktów na podzbiorach)

| grupa | n | udział | p | CI 95 % (p) | r̄ netto |
|---|---|---|---|---|---|
| wyjście: cel (tp) | 393 | 15,9 % | 100 % | — | +2,216 % |
| wyjście: stop (sl) | 445 | 18,0 % | 0 % | — | −2,427 % |
| wyjście: timeout | 1 639 | 66,2 % | 46,06 % | [43,65; 48,48] | −0,140 % |
| kierunek: long (formacje bycze) | 1 345 | 54,3 % | 47,43 % | [44,77; 50,10] | −0,178 % |
| kierunek: short (niedźwiedzie) | 1 132 | 45,7 % | 45,05 % | [42,15; 47,95] | −0,176 % |
| formacja: objęcie | 2 117 | 83,8 % | 45,68 % | [43,56; 47,80] | −0,171 % |
| formacja: młot | 303 | 12,0 % | 47,52 % | [41,90; 53,15] | −0,272 % |
| formacja: spadająca gwiazda | 60 | 2,4 % | 60,00 % | [47,60; 72,40] | +0,123 % |
| formacja: gwiazda poranna | 26 | 1,0 % | 61,54 % | [42,84; 80,24] | +0,200 % |
| formacja: gwiazda wieczorna | 19 | 0,8 % | 42,11 % | [19,90; 64,31] | −0,379 % |
| formacja: trójka | 2 | 0,1 % | 50 % | — | −0,508 % |
| \|score\| = 1 | 2 427 | 98,0 % | 46,31 % | [44,33; 48,30] | −0,181 % |
| \|score\| ≥ 2 | 50 | 2,0 % | 48,00 % | [34,15; 61,85] | +0,005 % |

Stopy przeważają nad celami (445 : 393), a timeouty (66 %) wygrywają w 46 %. Oba kierunki
tracą tyle samo — to nie jest błąd znaku w jedną stronę. **Objęcie (84 % sygnałów) ma CI
w całości pod 50 %**; gwiazdy (n 26–60) mają CI szerokie na 25–37 pp, obejmujące i 45 %, i 75 % —
przy 6 podgrupach 1–2 powyżej 50 % to oczekiwany szum, nie sygnał (pre-rejestracja: bez
werdyktów per formacja). W̄ = 1,286 %, L̄ = 1,286 %, C = 0,083 %, std zwrotu 1,73 %.

### 4. Mierzalność (zasada 18) — ex ante i ex post

A1a: `expected_trades` ex ante 2 523, ex post 2 527, journal 2 477 (różnica = 50 stłumionych);
pasmo trafności 1,95 / 1,97 pp; se zwrotu 0,0347 % → wykrywalny |r̄| ≥ 0,097 % (zmierzone
−0,177 %, czyli 1,8× dalej). A1b: 6 870 / 6 865 / 6 779; pasmo 1,18 / 1,19 pp; se 0,0213 % →
|r̄| ≥ 0,060 %. Rachunek ex ante zgadza się z ex post do 2 % w obu ramionach — pierwsza runda,
w której `n` nie zależało od abstynencji modelu (reguła), i pierwsza bez zaskoczenia próbą.

## Co na plus (+)

- **Runda rozstrzygnęła pytanie użytkownika na obu drogach naraz** (reguła i cecha), za dwa
  warianty, na tej samej populacji świec co kontrola — bez kolejnych rund „a może jako cecha".
- **Zero stopni swobody w definicji sygnału** (TA-Lib, zestaw z podręcznika zapisany przed
  danymi, doji wyłączone z podanym powodem) — wynik nie może być artefaktem doboru formacji.
- **Wynik jest silniejszy niż oczekiwanie:** prior brzmiał „p ≈ 50 %", a wyszło 46,4 % z CI
  pod 50 % — rzadki przypadek, w którym runda mówi coś więcej niż „brak sygnału": podręcznikowa
  interpretacja objęcia jest na 4h BTC odwrotna do danych.
- **Rachunek mocy z częstości formacji trafił w journal do 2 %** — wniosek 19 (n z abstynencji)
  ma teraz drugi wariant: n z częstości zdarzenia, gdy sygnał jest regułą.
- **Regresja kontroli = N1 co do cyfry** w tym samym skrypcie — aparat spójny między rundami.
- **Poprawka 2 wykryta przed publikacją** (N_eff > n) przez porównanie dwóch tabel tego samego
  raportu — dokładnie po to bramka 16a każe liczyć drugą drogą.

## Co na minus (−)

- **Tryb 4h bez świec 5m:** kolejność cel/stop wewnątrz świecy przybliżona (W1: ≤ 1,4 pp na
  niekorzyść strategii). Nie zmienia to znaku wyniku: nawet +1,4 pp daje p < 48 %.
- **Populacja reguły ≠ populacja kontroli** (22 % świec z formacją vs 60 % świec z decyzją
  modelu) — dlatego A1a ma kryterium absolutne, a nie porównanie z kontrolą; liczby obok siebie
  są kontekstem, nie testem różnicy.
- **Kill-switch stłumił 50 z 2 527 wypełnionych (2,0 %)** wobec 1,1 % w kontroli — reguła
  traci szybciej, więc częściej dobija do 15 % obsunięcia; stłumione świece nie są w journalu
  (raportowane, nie ukryte).
- **Objęcie dominuje (84 %)** — o pozostałych pięciu formacjach runda nie mówi prawie nic
  (n 2–303); zapisano to z góry i tak zostaje.
- **Poprawka 2 to zmiana biblioteki po obejrzeniu wyniku** — raportowa (cap N_eff ≤ n, jak
  w `metrics.py`), zawęża tylko wielkość pomocniczą; kryterium `t_neff < −1,96` spełnione
  przed i po (−7,61 → −5,11); test w repo.
- Jeden instrument, jeden seed, pozycje nakładające się sizowane niezależnie, przebicie =
  wypełnienie — jak we wszystkich rundach serii W/N.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Kluczowe liczby drugą drogą** (z liczb wydrukowanych, poza funkcjami skryptu):
  p* A1a = (L̄ + C)/(W̄ + L̄) = (1,2860 + 0,0832)/(1,2857 + 1,2860) = **53,24 %** ✔;
  zwrot netto A1a z mieszanki wyjść: 393/2 477 · 2,2164 + 445/2 477 · (−2,4274) + 1 639/2 477 ·
  (−0,1404) = 0,3517 − 0,4361 − 0,0929 = **−0,1773 %** wobec −0,1774 % ✔; trafność z podziału
  long/short: (1 345 · 0,4743 + 1 132 · 0,4505)/2 477 = **46,34 %** ✔; CI Walda: 0,4635 ± 1,96 ·
  √(0,4635 · 0,5365 / 2 477) = ±1,96 pp → **[44,38; 48,31]** ✔; lejek: 11 592 = 9 051 + 2 541,
  2 541 = 2 477 + 14 + 50, 1 380 + 1 161 = 2 541, 1 345 + 1 132 = 2 477 ✔; ex ante 2 523 vs
  journal 2 477 ✔.
- **Kogo NIE ma w zbiorze:** 9 051 świec OOS bez formacji (78 %); pierwsze 60 dni (trening);
  50 stłumionych kill-switchem (2,0 %); 14 niewypełnionych; świece sprzed 2021; kolejność
  wewnątrz świecy 4h.
- **Red flag odwrotny:** wynik NIE potwierdza oczekiwania (p ≈ 50 %) — jest istotnie niżej.
  Sprawdzono błąd znaku: TA-Lib +100 = formacja bycza → `signal_direction = +1` = long (jak
  etykieta +1 = górna bariera); gwiazda poranna (bycza) i spadająca gwiazda (niedźwiedzia)
  trafiają > 50 %, objęcie < 50 % — globalny błąd znaku odwróciłby wszystkie naraz. Oba kierunki
  tracą po równo (−0,178 % / −0,176 %). Sygnał na świecy `t` używa wyłącznie barów ≤ t
  (lookback TA-Lib), wejście od świecy t + 1 — bez przecieku.
- **Anomalia znaleziona i naprawiona przed publikacją:** N_eff 5 495 > n 2 477 w statystykach
  per transakcja (wzór N/(1 + 2Σρ) przy ujemnej autokorelacji) wobec 2 477 w tabeli pooled
  → Poprawka 2: cap jak w `metrics.summarize_pooled_by_regime`; t_neff −7,61 → −5,11; werdykt
  bez zmian; test `test_n_eff_is_capped_at_n…`; skrypt uruchomiony ponownie (wynik
  deterministyczny — pozostałe liczby identyczne).
- **Rząd wielkości:** trafności 45–50 %, progi 53 %, koszt 0,08 %, std 1,7 %, udziały sumują
  się do 100 % — w zakresach z listy kontrolnej.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `git diff master...HEAD` — `agents/feature_miner.py` (+cecha, +wpis; black scalił
4 wywołania sprzed rundy — kosmetyka), `feature_registry.yaml` (+wpis), `backtest/checkpoint_lib.py`
(+`build_rule_signals`, +`summarize_trade_returns`, Poprawka 2), `backtest/run_ta_a1.py` (nowy),
2 nowe pliki testów (15 testów, w tym hypothesis), README rundy.

**Korektność:** (1) brak lookaheadu — `compute_cdl_score_6` woła TA-Lib na całej serii, ale
każda funkcja CDL* używa barów ≤ t (test przecieku df[:T] vs df[:T+k] bit w bit — zielony);
sygnał na `close(t)`, wypełnienie od t + 1 (silnik). (2) Okno OOS = suma okien testowych
aktywnych foldów, półotwartych jak w `generate_walk_forward_folds`; parytet populacji
z modelem potwierdzony liczbą (11 592). (3) Pola sygnału = dokładnie zbiór czytany przez
`simulate_equity` (test na równość zbiorów); `original_index` pozycyjny — guard na RangeIndex.
(4) Bramka kosztowa woła tę samą `is_cost_feasible` z tym samym `gate_cost_fraction`, co silnik.
(5) Dodanie kolumny do `FEATURE_FUNCTIONS` nie zmienia starych wyników: listy cech modeli są
jawne, `dropna` po jawnych kolumnach — 650 testów sprzed rundy zielone, literały bit w bit.
(6) Poprawka 2: `min(n_eff, n)` — identyczna z `metrics.py`, test na monkeypatchu.

**Edge-case'y:** score NaN → brak sygnału (TA-Lib nie zwraca NaN, ale guard jest); konflikt
formacji → 0 → brak sygnału; brak aktywnych foldów / brak kolumny / zły indeks → `ValueError`;
`summarize_trade_returns` przy dwóch reżimach → `ValueError` (test).

**Czytelność / uwagi (bez blokady):** skrypt liczy formacje per świeca drugi raz (do tabeli 3c)
zamiast brać je z kolumny — świadomie, bo journal nie niesie `original_index`, a złączenie po
`timestamp` jest jednoznaczne (test: 1:1). `assert` w skrypcie na równość cechy między
treningami — dopuszczalny w skrypcie badawczym, nie w bibliotece. Ostrzeżenia `security-guidance`:
brak.

**Werdykt jednym zdaniem:** diff poprawny, bez przecieku, z regresją bit w bit i testami
własności — **Approve**, do scalenia.

## Wniosek

Sześć klasycznych formacji świecowych z podręcznika analizy technicznej, użytych dokładnie tak,
jak uczy podręcznik (bycza → long, niedźwiedzia → short, bez dobierania parametrów), **daje na
BTC 4h trafność 46,4 % [44,4; 48,3] i stratę 0,18 % [0,11; 0,25] na transakcję** — gorzej niż
moneta i gorzej niż model bez formacji. Winne jest objęcie (84 % sygnałów): duża świeca
w kierunku sygnału jest na tym rynku i horyzoncie częściej końcem ruchu niż jego początkiem.
Jako **dodatkowa cecha modelu** formacje nie zmieniają nic (−0,001 % [−0,012; +0,010]) — model
ma już tę informację w `return_lag_1`. Seria A (formacje świecowe) zamknięta: 2/2, STOP.
Prior z `ta-toolkit` („to zostało zmierzone") potwierdzony w mocniejszej formie: formacje nie
są ani nową informacją, ani nawet neutralną — na 4h BTC czytane po podręcznikowemu szkodzą.

## Rekomendacja

1. **Nie odwracać reguły.** „Formacje wskazują odwrotnie, więc grajmy przeciw nim" to nowa
   hipoteza wymyślona po wyniku (STW 1999 w czystej postaci), nie lustro tej rundy (wypełnienia
   limitem różnią się per kierunek), a jej ekonomia ex ante to ≈ +0,01 % na transakcję (brutto
   +0,094 % − koszt 0,083 %) — nieodróżnialne od zera i już zawarte w `return_lag_1`. Gdyby
   użytkownik mimo to chciał ją zmierzyć, to osobna runda z własną pre-rejestracją i decyzją
   bramkową, nie kontynuacja A.
2. **Nie testować podzbiorów formacji** (gwiazdy „wyglądają lepiej"): n 26–60, CI 25–37 pp,
   2 z 6 podgrup nad 50 % = oczekiwany szum. STOP obejmuje podzbiory, wagi, progi, konteksty.
3. **Pozostałe rodziny AT ze skilla** (wsparcie/opór, wybicie z zakresu, struktura trendu,
   podwójny szczyt, przecięcia średnich, linia trendu, Fibonacci) mają ten sam prior
   (transformacja OHLCV) i wymagają każda osobnej pre-rejestracji z rachunkiem mocy —
   **decyzja użytkownika, czy którąkolwiek uruchamiać**; z tej rundy nie wynika żadna
   rekomendacja „za". Najbardziej odrębny mechanizm (skupienie zleceń na pamiętanych
   poziomach — `sr_distance`) jest jedynym, dla którego `ta-toolkit` podaje wiarygodny
   mechanizm ekonomiczny; reszta go nie ma.
4. **Metodologicznie:** cap N_eff ≤ n obowiązuje w każdej statystyce per transakcja (Poprawka 2,
   już w bibliotece); rachunek mocy dla reguły liczy się z częstości zdarzenia — drugi wariant
   wniosku 19.

## Użyte skille

Rejestr gałęzi `a1-analiza-techniczna` (`py tools/skill_audit.py raport --galaz a1-analiza-techniczna`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:ta-toolkit` | mapa pojęć AT → funkcje deterministyczne, DoF per narzędzie, zestaw 6 formacji z podręcznika (CDL_MAP), status „nietknięte", literatura (MYR 2006, STW 1999) → prior; lista, gdzie AT leakuje (swingi) — dlatego pierwsza runda na formacjach (0 DoF, bez swingów) |
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → INDEX → pre-rejestracja w osobnym commicie → kod → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | kryterium dwóch warunków, rachunek mocy z częstości zdarzenia (nie z abstynencji — reguła jej nie ma), masa punktowa (score dyskretny → bez percentyli), „nie cytuj t_neff bez sprawdzenia" |
| `anthropic-skills:quant-strategy-catalog` | pięć pól: ten sam zbiór informacyjny, inna formuła (reguła), status NIETKNIĘTE → nowa seria z własnym licznikiem; mechanizm jednym zdaniem z jawną słabością |
| `engineering:testing-strategy` | plan testów: fixture TA-Lib z wariantem −80, doji, hypothesis na losowych świecach; lejek reguły domknięty, silnik end-to-end, arytmetyka statystyk, cap N_eff |
| `data:validate-data` | bramka 16a: p*, zwrot z mieszanki wyjść, p z podziału kierunków, CI Walda, lejek; red flag odwrotny (błąd znaku); wykrycie N_eff > n |
| `data:statistical-analysis` | bramka 16b: CI zwrotu i trafności, mediana obok średniej, test parowany, jak raportować 6 podgrup bez werdyktów |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Z tabeli zasady 19 pominięte: `dataviz` (bez wykresów), `data:explore-data` (te same parquety
co N1; nowa kolumna to funkcja istniejących), `engineering:architecture` (bez decyzji
architektonicznej — pomocniki w bibliotece są rozszerzeniem istniejącego wzorca W1/N1),
`update-config`, `security-review` (bez kluczy, zleceń i sieci), `lean-research` (bez LEAN).
