# O1 — pozycjonowanie graczy (zmiana open interest) jako cecha modelu 4h: czy dane spoza wykresu niosą informację? (2026-09-23)

> **STATUS: ZAMKNIĘTA — NEGATYWNY wg kryterium** (zwrot netto −0,074 % [−0,116; −0,032] na
> transakcję, t_neff −2,90; trafność 50,25 % [49,06; 51,44] wobec progu 53,07 %). **Ale cecha
> niesie odrobinę informacji:** wobec kontroli na tych samych świecach +0,024 pp [−0,019; +0,067]
> na transakcję, zmienia kierunek w 20,6 % wspólnych transakcji, korelacja z wolumenem 0,045
> (nie jest przebraniem wolumenu) — pierwsza cecha w projekcie, która w ogóle porusza wynik
> modelu (A1b/A2.5: ±0,001 pp). Za mało, by przekroczyć próg opłacalności. Kolejność w gicie:
> pre-rejestracja + kod `faa11e1` → przebieg → wynik w commicie scalającym. **Seria O: 1/1,
> STOP.** Walidacja (16a): **READY**; przegląd diffu (16c): **Approve**.

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Model dostał jedną nową liczbę spoza wykresu — o ile zmienił się open interest przez 24 h —
i trafia trochę lepiej: 50,25 % zamiast 49,58 %, a średnia strata na transakcję maleje z −0,107 %
do −0,074 %.** To pierwszy raz w projekcie, gdy dodatkowa cecha w ogóle zmienia decyzje modelu
(w 21 % transakcji wybiera inny kierunek). Ale próg, powyżej którego handel zarabia po kosztach,
to 53,1 % trafności — a górny kraniec przedziału dla nowego modelu to 51,4 %. **Wynik jest
NEGATYWNY: model z tą cechą nadal traci pieniądze**, tylko trochę wolniej. Poprawa wobec
kontroli (+0,024 punktu procentowego na transakcję) sama w sobie nie jest odróżnialna od zera.

**Co to znaczy dla dalszej pracy:** dane o pozycjonowaniu to prawdopodobnie realna, słaba
informacja, nie szum — ale na 4-godzinnych świecach BTC z tym modelem nie wystarcza. Kolejne
kolumny z tego samego archiwum (proporcje long/short, przepływ taker) to warianty tej samej
rodziny — po regule STOP wymagają Twojej decyzji.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Do tej pory model widział tylko wykres ceny i wolumenu — i na tym trafiał jak rzut monetą
(Faza 0). Sonda P3 dała nam sześć lat danych o tym, ile pozycji z dźwignią jest otwartych na
rynku (open interest). Pomysł: gdy liczba otwartych pozycji szybko rośnie, rynek ma w sobie
coraz więcej „dźwigni", a każdy większy ruch ceny zmusza część graczy do zamknięcia pozycji
(likwidacja), co wzmacnia ruch. Dajemy modelowi jedną nową liczbę — o ile procent zmienił się
open interest przez ostatnie 24 godziny — i sprawdzamy, czy jego decyzje stają się lepsze niż
bez niej. Porównujemy parami: ten sam model, te same świece, z cechą i bez.

**Czego się spodziewamy (przed wynikiem):** przyjmujemy „obietnicę podręcznika" (56 % trafności),
jak w A1, i sprawdzamy, czy próba pozwala ją odróżnić od progu opłacalności (53,1 %). Prior jest
wyższy niż dla kolejnej transformacji ceny (inny zbiór informacyjny, mechanizm strukturalny), ale
F1 (funding — też spoza wykresu) dało 50,34 %, więc bez złudzeń.

## ID testu

**O1** — nowa hipoteza, rodzina „pozycjonowanie/OI jako cecha kierunkowa" (katalog: zbiór
informacyjny pozycjonowanie/OI · jednoaktywowa · kierunek · 4h · status po P3: NIETKNIĘTE,
wcześniej WYKLUCZONE-danymi przez P1). **Własny licznik: 1 wariant. Reguła STOP: 1/1** — inne
kolumny archiwum (proporcje top traderów, global L/S, taker ratio), inne okna (8h/72h), OI w USD,
progi/reguły bez modelu to WARIANTY TEJ SAMEJ rodziny i po STOP wymagają decyzji użytkownika.

## Metadane

- Branch: `o1-pozycjonowanie` (od `master` @ `4e3bb5e`).
- Dane: świece 4h BTC z `fetch_window` (zasada 20: od 2021-01-01, 12 042 świece); archiwum
  `data/raw/external/binance_metrics_BTCUSDT_5m.parquet` (P3: 636 710 odczytów 2020-09-01 →
  2026-09-22, pokrycie bazy 99,90 %, 473 zerowe OI → NaN).
- Cecha: `oi_change_24h = log(oi_close_t / oi_close_{t−6})`, `oi_close` = `sum_open_interest`
  (w BTC — bez efektu ceny) z **ostatniego odczytu 5-min WEWNĄTRZ świecy** `(open, open+3h55m]`
  (odczyt o `open+4h` należy do następnej świecy); brak odczytu w świecy → NaN.
- Pipeline jak kontrola N1/A1/A2: bez bramki reżimu, V = 3, wagi klas `balanced`, walk-forward
  60/28/28, seed `PRIMARY_SEED`, wejście limit po close k = 1, pojedyncze wyjście, koszty z config.
- Ramiona: **kontrola** = `REVERSION_FEATURES` (4 cechy); **O1** = kontrola + `oi_change_24h`.
- Kod: `agents/positioning_features.py` (`load_metrics`, `attach_positioning`,
  `compute_oi_change_24h`, rejestr `POSITIONING_FEATURE_FUNCTIONS`), sekcja `positioning:`
  w `agents/feature_registry.yaml`, testy przecieku w `agent_5_compliance/test_leakage.py`
  (dopięcie bez lookaheadu + shift-forward bit w bit), `tests/test_positioning_features.py`;
  skrypt `backtest/run_positioning_o1.py`. **Komenda:** `py -m backtest.run_positioning_o1`
  (Windows: `PYTHONUTF8=1`; dwa treningi, 6 s; pełny stdout `raw_output.txt`; skrypt na
  `runs/ZAMROZONE.txt`). Walidacja drugą drogą: `walidacja.py` → `walidacja.txt`.

## Poprzedzające wyniki

- **P1** (skreślenie pozycjonowania po REST API) → **P3** (archiwum 6 lat, wniosek 59):
  pozycjonowanie MIERZALNE na tej samej próbie co każda cecha (n ≈ 6 870 transakcji).
- **F1** (funding jako cecha, jedyna dotąd spoza OHLCV): 50,34 % — bez sygnału; **wniosek 11**:
  wąskie gardło Fazy 0 informacyjne; **A1b/A2.5**: dodatkowe cechy z OHLCV/AT nie zmieniają
  nic (różnice parowane w paśmie ±0,01 pp) — to wzorzec porównania i skala „nic".
- **Wniosek 46** (kontrola na nowej bazie): p = 49,58 % [48,39; 50,77], −0,107 % na transakcję,
  p* 53,07 %, abstynencja 40,4 %, n 6 789 — regresja kontroli sprawdzana w skrypcie.
- **Wniosek 15** (masa punktowa): OI zmiana jest ciągła (sprawdzone w sanity: masa punktowa
  < 1 %); żadnych progów percentylowych — model dostaje wartość surową.
- **Czy to nie wolumen?** `volume_zscore_20` jest już w kontroli; OI to pozycje otwarte NETTO
  (stan), wolumen to obrót BRUTTO (przepływ) — różne wielkości; korelacja liczona w skrypcie
  jako kontrola (wysoka korelacja = cecha redundantna, nie „nowa informacja").

## Pre-rejestracja

### Hipoteza i mechanizm

Zmiana open interest w ostatnich 24 h niesie informację o kierunku zwrotu w horyzoncie
V = 3 świec 4h ponad to, co niosą cechy ceny/wolumenu. Mechanizm: narastanie OI = narastanie
dźwigni po jednej stronie → ruch przeciwny wymusza likwidacje (ograniczenie strukturalne: ktoś
MUSI zamknąć), co wzmacnia ruch; spadek OI = delewarowanie po ruchu. Kierunek zależy od
kombinacji z ceną (OI rośnie + cena rośnie = tłok longów), więc cecha trafia do modelu obok
`return_lag_1`, nie jako reguła z progiem.

### DOKŁADNIE JEDNA zmienna

Dodanie `oi_change_24h` do zestawu cech (5 zamiast 4). Alternatywy odrzucone PRZED danymi:
proporcje top traderów (dziura 2021-12 → 2022-12 = 16 % bazy), taker buy/sell ratio (acf1 0,09
przy 5 min — szum bez agregacji, a agregacja = kolejny stopień swobody), global L/S kont
(kontrariańska, bez mechanizmu dźwigni), OI w USD (miesza cenę), okna inne niż 24 h.

### Przyrząd i kryterium (jedno ramię, m = 1 — bez Bonferroniego)

Kanoniczny checkpoint v2: journal transakcji OOS, `p` = udział `gross_pnl > 0`, zwrot netto
per transakcja, N_eff ≤ n, `p* = (L̄ + C)/(W̄ + L̄)`.
- **POZYTYWNY:** `t_neff > 1,96` zwrotu netto ORAZ `ci_low(p) > p*` → najpierw szukać przecieku.
- **NEGATYWNY:** `t_neff < −1,96` przy `n ≥ required_trades(0,50; BE)`.
- **NIEROZSTRZYGNIĘTY:** inaczej.
- **Porównanie parowane O1 − kontrola** (te same świece i wypełnienia): obserwacja, nie
  kryterium; skala „nic" z A1b: −0,001 % [−0,012; +0,010]. Oczekiwanie: różnica w paśmie
  ±0,02 pp, chyba że cecha realnie zmienia decyzje (udział zmienionych kierunków — raportowany).
- Test w granicy dużego n: oba warunki pozytywu rosną z n przy prawdziwym efekcie; negatyw
  wymaga n ≥ required — nie karze celu rundy.

### Rachunek mierzalności (zasada 18) — przed wynikiem

`expected_trades(11 592; 0,4038; 0,994) ≈ 6 870` (świece OOS × (1 − abstynencja) × wypełnienia,
jak A1b); `wald_half_width(6 870) ≈ 1,18 pp`; `measurability_report(p = 0,56; BE = 0,5307;
n = 6 870)` → luka 2,93 pp > 1,18 pp → **MIERZALNA** (ta sama próba i ten sam werdykt co A1b;
skrypt drukuje raport ex ante i ex post). Cecha nie ma NaN w bazie poza ewentualnymi świecami
bez odczytu (P3: luki ≤ 85 min → 0 świec), więc populacja świec O1 = populacja kontroli
(sprawdzane: „świece ocenione O1 vs kontrola").

### Czego runda NIE robi

Nie stroi okna; nie dodaje drugiej kolumny archiwum; nie buduje reguły z progiem na OI; nie
liczy SHAP/importance jako dowodu (wniosek: „feature importance to filtr, nie dowód"); nie
odwraca znaku; nie wybiera podokresów. Wynik NIEROZSTRZYGNIĘTY z różnicą parowaną ≈ 0 czyta
się jak A1b: „ta informacja nie zmienia decyzji modelu".

---

## Wynik

Dane: 12 042 świece 4h (2021-01-01 → 2026-06-30), 636 237 odczytów OI (po masce zer); cecha
NaN w 16 świecach (5 bez odczytu wewnętrznego + warm-up); rozkład p05 −6,4 %, p50 +0,12 %,
p95 +6,6 %; masa punktowa 0,03 %; acf1 0,81. Korelacja z `volume_zscore_20` **+0,045**,
z `return_lag_1` +0,033, z `rsi_14` +0,14 — nowa informacja, nie przebranie starych cech.

### 1. Kryterium (jedno ramię, z = 1,96)

| ramię | n | r̄ netto | CI 95 % | mediana | t_neff | N_eff | p | CI 95 % (p) | p* |
|---|---|---|---|---|---|---|---|---|---|
| kontrola | 6 789 | −0,1069 % | [−0,1487; −0,0650] | −0,1036 % | −4,26 | 4 919 | 49,58 % | [48,39; 50,77] | 53,64 % |
| **O1** | 6 748 | **−0,0738 %** | [−0,1155; −0,0320] | −0,0860 % | **−2,90** | 4 727 | **50,25 %** | [49,06; 51,44] | 53,07 % |

**Odczyt kryterium: NEGATYWNY** (`t_neff` −2,90 < −1,96 przy n 6 748 ≥ 2 078). Regresja
kontroli wobec N1/A1/A2: ZGODNA (n 6 789, p 49,58 %, r̄ −0,1069 %). Lejek O1: 11 584 świec
ocenionych (kontrola 11 592 — 8 świec z NaN cechy), abstynencja 40,85 % (kontrola 40,38 %).

### 2. Porównanie parowane O1 − kontrola (obserwacja, nie kryterium)

Wspólnych transakcji **5 322** (kontrola 6 789, O1 6 748; tylko w kontroli 1 467, tylko w O1
1 426); **ten sam kierunek w 79,4 %** (cecha zmienia decyzję w 20,6 %); średnia różnica netto
**+0,0242 % [−0,0188; +0,0671]**, mediana 0, różnic ≠ 0: 3 423. Skala „nic" z A1b: −0,001 %
[−0,012; +0,010] — tu efekt jest 20× większy punktowo, ale CI obejmuje zero.

### 3. Opis — powód wyjścia, kierunek

| | cel (tp) | stop (sl) | timeout | timeout: p | timeout: r̄ brutto | long: p | short: p |
|---|---|---|---|---|---|---|---|
| kontrola | 17,7 % | 17,4 % | 64,9 % | 49,17 % | −0,032 % | 49,49 % | 49,67 % |
| O1 | 17,9 % | 16,9 % | 65,2 % | 49,58 % | −0,0005 % | **50,96 %** | 49,62 % |

Geometria bez zmian (W̄ 1,307 %, L̄ 1,308 %, C 0,080 %). Poprawa mieszka w nodze long (50,96 %
[49,22; 52,70]) i w nodze timeout (brutto z −0,032 % do 0) — opisowo, bez werdyktów per grupa.

### 4. Mierzalność — ex ante vs ex post

`expected_trades` ex ante 6 870, ex post 6 811, journal 6 748; half-width 1,18 / 1,19 pp;
`measurability_report` → MIERZALNA (jak zapisano). Kryterium negatywne rozstrzygnięte
z zapasem (n 3,2× wymaganego).

## Co na plus (+)

- **Pierwsza cecha spoza OHLCV, która w ogóle zmienia decyzje modelu** (20,6 % transakcji; A1b:
  ~0) i poprawia oba wskaźniki punktowo (+0,67 pp trafności, +0,033 pp na transakcję), przy
  korelacji z wolumenem 0,045 — informacja niezależna od cech ceny/wolumenu.
- **Dopięcie bez lookaheadu udowodnione trzema drogami:** test jednostkowy (odczyt o `open+4h`
  nie wchodzi), test shift-forward (bit w bit), walidacja na realnych danych (podmiana odczytów
  granicznych ×10 nie zmienia żadnej świecy; przesunięcie odczytów o +4h zmienia 12 029 świec).
- **Populacja świec = kontrola** (11 584 vs 11 592; 8 świec z NaN), więc porównanie parowane
  jest „jabłka do jabłek"; kontrola odtworzona co do sztuki.
- Jedna cecha, jedno okno, bez progów, bez wyboru po wyniku; rachunek mocy potwierdzony ex post.

## Co na minus (−)

- **Nadal NEGATYWNY:** model z cechą traci −0,074 % na transakcję; górny kraniec CI trafności
  51,4 % jest 1,7 pp poniżej progu. Informacja jest, ale za słaba dla tego modelu i horyzontu.
- **Poprawa parowana nie jest odróżnialna od zera** (+0,024 pp [−0,019; +0,067]); przy jednej
  próbie nie wolno jej cytować jako „cecha działa".
- **Jedna kolumna z sześciu w archiwum** — proporcje long/short (top traderzy, wszystkie
  konta), taker ratio, OI w USD nie zostały zmierzone; każda to wariant tej samej rodziny
  (STOP 1/1 → decyzja użytkownika). Kolumny top-trader mają dziurę 2022.
- **acf1 cechy 0,81** — 24-godzinna zmiana na świecach 4h nakłada się (6 świec), więc kolejne
  wartości są zależne; dla modelu to nie problem, ale cecha „mówi" to samo przez ~6 świec.
- **Kontekst:** ~17 odczytów tego dnia (serie A, C, R, N, W, X, D1, P3, O1) — pojedyncze
  punktowe poprawy na tym tle są oczekiwane z samego szumu.

## Walidacja (zasada 16a) — werdykt: **READY** (`walidacja.txt`)

- **Drugą drogą (numpy z journalu):** p = 50,25 % ✔, r̄ netto −0,0738 % ✔, t (bez N_eff) −3,46 ✔,
  p* = (1,3075 + 0,0802)/(1,3073 + 1,3075) = 53,07 % ✔ — wszystkie zgodne ze skryptem.
- **Brak lookaheadu na realnych danych:** przesunięcie odczytów o +4h zmienia `oi_close`
  w 12 029 z 12 042 świec (wersja użyta bierze odczyty z wnętrza świecy); podmiana odczytów
  dokładnie o `open+4h` (×10) **nie zmienia żadnej świecy** (pierwszy wydruk pokazał „5" —
  to były pary NaN≠NaN w 5 świecach bez odczytu; porównanie poprawione i powtórzone: 0).
- **Regresja kontroli:** n/p/r̄ identyczne z N1/A1/A2 ✔.
- **Kogo NIE ma:** 8 świec OOS z NaN cechy (5 bez odczytu wewnętrznego + propagacja), 3 z NaN
  etykiety, 68 sygnałów stłumionych, 36 niewypełnionych; pozostałe 5 kolumn archiwum; okno
  inne niż 24 h; ETH/SOL/BNB (archiwum od 2021-12).
- **Red flag „idealnie potwierdza":** nie — negatywny. **Red flag „dodatni → szukaj przecieku":**
  poprawa parowana +0,024 pp mieści się w CI z zerem, a dopięcie sprawdzone trzema drogami.
- **Red flag „redundancja z wolumenem":** korelacja 0,045 — nie.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `agents/positioning_features.py` (nowy), `agents/feature_registry.yaml` (sekcja
`positioning:`), `agent_5_compliance/test_leakage.py` (+2 testy: rejestr, shift-forward),
`tests/test_positioning_features.py` (5), `backtest/run_positioning_o1.py` (reporter, wzorzec A2),
README rundy. Bez zmian w `feature_miner`, `engine`, `ml_optimizer`.

**Korektność:** (1) `attach_positioning` — `merge_asof(direction="backward", tolerance=offset)`
na kluczu `open + offset` daje ostatni odczyt w `[open, open + offset]`; odczyt dokładnie o `open`
wykluczony jawnie (`_snap > _open`), więc okno to `(open, open + 3h55m]` (test: odczyt o 04:00
nie wchodzi do świecy 00:00 ani jako jedyny odczyt do 04:00); kolejność wierszy przywrócona
przez `_order`; brak mutacji `df` (test); (2) `load_metrics` — OI ≤ 0 → NaN i `dropna`, więc
asof bierze poprzedni ważny odczyt (test); (3) `compute_oi_change_24h` — `log(oi/oi.shift(6))`,
NaN propaguje na t i t+6 (test), `ValueError` bez kolumny; (4) skrypt — kopia wzorca A2 z jednym
ramieniem, `_verdict` bez Bonferroniego (m = 1, jak w pre-rejestracji), porównanie parowane
przez `join` na `timestamp` (inner) z licznikami „tylko w"; (5) rejestr 1:1 z kodem (test).
**Edge-case'y:** świeca bez odczytu → NaN → wiersz odpada z train/test (`dropna` w silniku) —
8 świec, zapisane; metrics puste → merge daje NaN wszędzie (fail loud pośrednio: 100 % NaN
cechy → silnik zgłosi brak wierszy).
**Czytelność:** konwencje w docstringu modułu; stałe nazwane.
**Uwagi (bez blokady):** `acf1` cechy 0,81 opisany; `walidacja.py` importuje `_collect`/`_simulate`
ze skryptu rundy (prywatne nazwy) — akceptowalne dla skryptu walidacji.
**Werdykt jednym zdaniem:** kod poprawny, dopięcie bez lookaheadu udowodnione trzema drogami,
rejestr i testy przecieku na miejscu PRZED wejściem cechy do modelu — **Approve**.

## Wniosek

**Zmiana open interest z 24 h jako piąta cecha modelu 4h daje wynik NEGATYWNY: −0,074 % na
transakcję [−0,116; −0,032], trafność 50,25 % [49,06; 51,44] wobec progu 53,07 %.** To jednak
pierwsza cecha spoza wykresu, która realnie zmienia decyzje modelu (20,6 % transakcji) i
przesuwa wynik w dobrą stronę (+0,024 pp [−0,019; +0,067] wobec kontroli; trafność +0,67 pp)
przy korelacji z wolumenem 0,045 — słaba, ale niezależna informacja. Za słaba, żeby na 4h BTC
z tym modelem wyjść ponad koszty. Seria O zamknięta 1/1 (STOP); pozostałe kolumny archiwum
to warianty tej samej rodziny i wymagają decyzji użytkownika.

## Rekomendacja

1. **Nie mierzyć kolejnych kolumn archiwum bez decyzji użytkownika** (STOP). Jeśli decyzja
   będzie „tak": jedna kolumna na rundę, ta sama procedura; kandydat z najlepszym mechanizmem
   po OI to proporcja pozycji top traderów (`sum_toptrader_long_short_ratio` — z dziurą 2022,
   n ≈ 84 % bazy), potem taker ratio agregowany do świecy (jeden sposób agregacji, zapisany
   przed danymi).
2. **Nie łączyć O1 z X1 ani z czymkolwiek „bo obie punktowo dodatnie"** — kombinacje po wyniku
   to loteria multiple-testing (wniosek 49; rozmowa 2026-09-23 o kombinacjach wniosków).
3. **Jeśli wracać do pozycjonowania, to z innym targetem/horyzontem, nie z innym oknem OI:**
   mechanizm kaskad likwidacji działa na godzinach, nie dniach — ale 1h/5m to inne bazy
   (progi kosztowe 56,8 %/82,8 %), więc to nowa pre-rejestracja z własnym rachunkiem mocy,
   nie wariant.
4. **Metodologicznie:** wzorzec „dopięcie snapshotu z wnętrza świecy + trzy testy lookaheadu"
   jest gotowy do ponownego użycia dla DVOL, on-chain (z `shift(1)` dnia) i F&G — każde jako
   osobna seria.

## Użyte skille

Rejestr gałęzi `o1-pozycjonowanie` (`py tools/skill_audit.py raport --galaz o1-pozycjonowanie`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → pre-rejestracja (cecha, kryterium, moc) → test przecieku PRZED modelem → commit → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | wybór jednej cechy po mechanizmie PRZED danymi, rachunek mocy z abstynencji, masa punktowa, kryterium dwóch warunków, „feature importance to nie dowód" |
| `anthropic-skills:quant-strategy-catalog` | pięć pól rodziny (status WYKLUCZONE-danymi → NIETKNIĘTE po P3), mechanizm „kto traci" (likwidowani), OI w BTC vs USD, OI ≠ wolumen |
| `engineering:testing-strategy` | plan testów PRZED kodem: odczyt graniczny wykluczony, luka w świecy, maska zer, propagacja NaN, rejestr 1:1, shift-forward |
| `data:validate-data` | bramka 16a: numpy z journalu, trzy drogi lookaheadu (w tym wykrycie NaN≠NaN w pierwszym wydruku), regresja kontroli, „kogo nie ma", red flagi |
| `data:statistical-analysis` | bramka 16b: efekt z CI, różnica parowana z CI i udziałem zmienionych kierunków, mediana obok średniej, opis grup bez werdyktów, kontekst ~17 odczytów |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Z tabeli zasady 19 pominięte: `security-review` (bez kodu sieciowego), `dataviz` (bez wykresów),
`engineering:architecture`, `update-config`, `ta-toolkit`, `lean-research`, `data:explore-data`
(profil archiwum wykonany w P3).
