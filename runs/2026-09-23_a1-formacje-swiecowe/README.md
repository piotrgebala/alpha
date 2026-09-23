# A1 — formacje świecowe jako sposób szukania pozycji (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed kodem).** Wszystko do sekcji „Definition of Done" włącznie
> zapisano **przed napisaniem linijki kodu produkcyjnego** i trafia do repo w osobnym commicie,
> który poprzedza commit z kodem. Sekcje od „Wynik" w dół dopisuje się po przebiegu.
> Runda otwiera **NOWĄ SERIĘ A (analiza techniczna)** z własnym licznikiem — decyzja użytkownika
> 2026-09-23: „szukamy pozycji na podstawie analizy technicznej i formacji świecowych" (skill
> `ta-toolkit`). Liczby przed kodem pochodzą wyłącznie z ZLICZENIA formacji na świecach
> (ile razy występują) — bez spojrzenia na jakikolwiek wynik transakcji.

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
- **Skrypt rundy:** `backtest/run_ta_a1.py` (powstaje PO tej pre-rejestracji; komenda
  uruchamialna trafi tu przy zamknięciu razem z wpisem na `runs/ZAMROZONE.txt`). Buduje na
  `checkpoint_lib` (`fetch_window`, `summarize_result`, nowy pomocnik `build_rule_signals`)
  i `engine.collect_signals` / `simulate_equity`.
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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz a1-analiza-techniczna`)_
