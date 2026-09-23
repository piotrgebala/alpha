# O1 — pozycjonowanie graczy (zmiana open interest) jako cecha modelu 4h: czy dane spoza wykresu niosą informację? (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Hipoteza, DOKŁADNIE JEDNA cecha wybrana po
> mechanizmie PRZED danymi, kryterium, reguła STOP i rachunek mierzalności zapisane PRZED
> obejrzeniem wyniku. Test przecieku cechy i dopięcia snapshotu PRZED wejściem do modelu
> (zasada 2). **NOWA SERIA O, licznik od zera.** Pierwsza cecha spoza OHLCV od F1 (funding).
> Decyzja użytkownika 2026-09-23: „realizuj dalej" (po odpuszczeniu carry); dane z P3.

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
  skrypt `backtest/run_positioning_o1.py` (komenda przy zamknięciu; na `runs/ZAMROZONE.txt`).

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz o1-pozycjonowanie`)_
