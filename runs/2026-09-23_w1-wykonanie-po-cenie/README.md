# W1 — wykonanie po konkretnej cenie: uczciwy model wypełnień w backteście (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed kodem).** Wszystko do sekcji „Czego ta runda NIE raportuje"
> włącznie zapisano **przed napisaniem linijki kodu produkcyjnego** i trafia do repo w osobnym
> commicie, który poprzedza commit z kodem. Sekcje od „Wynik" w dół dopisuje się po przebiegu.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Skąd ta runda.** Użytkownik ustalił zasadę, która obowiązuje też na żywo: pozycji nie otwiera
się ani nie zamyka „po cenie otwarcia lub zamknięcia świecy", tylko po **konkretnej cenie**
(zlecenie oczekujące na poziomie). Backtest liczy dziś wejście po cenie zamknięcia świecy
sygnału i **zakłada, że zlecenie zawsze się wypełni**. To jedyna optymistyczna część modelu
wykonania, o której wiemy od rundy C2.12, a której nigdy nie zmierzyliśmy.

**Co sprawdzamy.** Trzy sposoby wejścia, które użytkownik kazał sprawdzić wszystkie:
(1) limit dokładnie po cenie zamknięcia świecy sygnału, (2) limit na cofnięciu o pół ATR
(taniej, ale rzadziej), (3) zlecenie na wybiciu ponad szczyt / pod dołek świecy sygnału
(w kierunku ruchu, drożej). Zlecenie czeka **jedną świecę** (4 godziny) — bo tyle warta jest
prognoza modelu — a dłuższe czekanie (2–3 świece) mierzymy tylko opisowo. Wyjścia zostają
jak dziś: zysk i strata na poziomach ±1,5·ATR od ceny wypełnienia, limit czasu 3 świece.

**Czego się spodziewam — zapisane z góry.** Że żaden z trzech sposobów nie zmieni werdyktu.
Faza 0 zmierzyła trafność 50,27 % na 7 687 transakcjach — model nie zna kierunku. Uczciwy model
wypełnień może tylko **pogorszyć** liczby (część sygnałów przepada, a limit wypełnia się
częściej wtedy, gdy rynek idzie przeciw nam). Sens rundy: backtest ma mierzyć to, co będziesz
robić na żywo — bez tego żaden przyszły wynik (np. z nowym celem modelu, który użytkownik
zaplanował na osobną rundę) nie byłby wiarygodny.

**Dlaczego to nie jest „strojenie".** Sposoby wejścia i czas ważności zlecenia są zapisane
przed uruchomieniem, każdy sposób wejścia liczy się jako wariant w księdze budżetu, a po tych
trzech seria jest zamknięta — bez doboru lepszego cofnięcia, dłuższego czekania ani innej reguły
po obejrzeniu wyniku.

---

## ID testu

**W1** — pierwsza runda **NOWEJ SERII W** („wykonanie po cenie"). Własny licznik od zera
(wniosek skumulowany 13), własna reguła STOP. **3 warianty** (trzy reguły wejścia z werdyktem
na tych samych danych — precedens C2.12: raportowany werdykt = wariant). Część kalibracyjna
(5m wobec 4h) i wrażliwość na czas ważności: **0 wariantów** (bez werdyktów — reguła jak D5 w H3).

## Metadane

- **Branch:** `wykonanie-po-cenie`
- **Poprzedzający stan (master):** `a184ce9` (merge T10)
- **Decyzje użytkownika (2026-09-23), które ustawiają tę rundę:**
  1. sprawdzić **wszystkie trzy** sposoby wejścia;
  2. czas ważności zlecenia — **„sam sprawdź"** (delegacja; rozstrzygnięcie niżej, z horyzontu
     modelu, nie z wyniku);
  3. **najpierw naprawa wykonania przy dzisiejszym celu modelu** (TP/SL 1,5·ATR, 12 h); nowy cel
     (częściowe wyjście 50 % przy +5 % depozytu przy dźwigni 3×, stop na break-even, reszta
     dalej) to **osobna, późniejsza runda** — tu go nie ma;
  4. sizing **bez zmian** (ryzyko 0,5 % kapitału, dźwignia najwyżej 3× — zasada 5).
- **Skrypt rundy:** `backtest/run_execution_w1.py` (powstaje PO tej pre-rejestracji, buduje na
  `backtest/checkpoint_lib.py`; komenda w formie uruchamialnej trafi tu przy zamknięciu rundy,
  razem z wpisem skryptu na listę `runs/ZAMROZONE.txt`).
- **Dane:** natywne świece 4h BTC/USDT perpetual 2019-09-10 → 2026-07-01 (14 916 świec, 6,8 roku,
  zero dziur — Z5b); do części kalibracyjnej natywne 5m 2023-07-01 → 2026-07-01 (315 648 świec).
- **Testy przed rundą:** 570/570.

## Poprzedzające wyniki (zasada 14)

- **C2.12** (`runs/2026-09-21_c2.12-execution-cost-model/`) — wprowadziło model `maker_limit`
  i zapisało jawnie ograniczenie: *„noga maker zakłada, że zlecenie limit SIĘ WYPEŁNIA; pomija
  adverse selection"*. **Ta runda usuwa dokładnie to ograniczenie.**
- **H3** (`runs/2026-09-22_h3-noga-timeout-pasmo/`, ADR w `docs/rag/04`) — kryterium *„noga maker
  jest dobrze zdefiniowana tylko, gdy cena zlecenia jest znana przy składaniu"*. Wejście limitem
  i TP spełniają je; timeout NIE — dlatego wyjście po czasie **zostaje po rynku** (taker, po
  `close` świecy t+V). Nowa zasada użytkownika nie zmienia tego: przy wyjściu po czasie znamy
  moment, nie cenę. H3 zapisało też, że powrót do modelowania wypełnień wymaga **danych**, nie
  założenia — tutaj danymi są ścieżki cen (5m wewnątrz 4h), nie księga zleceń; to nadal
  przybliżenie i jest tak nazwane.
- **M1 / F1** (`runs/2026-09-22_m1-momentum-bez-bramki/`, `runs/2026-09-22_f1-funding-zmierzony/`)
  — konfiguracja kanoniczna i liczby odniesienia ramienia A: **n = 8 033, trafień 4 046,
  p = 50,37 % [49,27 %; 51,46 %], próg opłacalności 52,93 %**, abstynencja 43,84 %, świec
  ocenionych 14 448. Kontrola tej rundy musi je odtworzyć co do sztuki.
- **Z10** (`runs/2026-09-22_z10-zamkniecie-fazy-0/`) — dowód braku sygnału kierunkowego
  w cechach OHLCV. Obniża prior tej rundy do zera co do edge'u: mierzymy wykonanie, nie szukamy
  zysku.
- **K3** — `n` przeliczone z abstynencji przez `expected_trades` zgadzało się z journalem do
  0,3 transakcji — ta sama droga rachunku mocy tutaj.
- **Z9** (`runs/2026-09-22_z9-timeframe-geometry/`) — dane per interwał NATYWNE; resample psuł
  wolumen. Tu 5m służy WYŁĄCZNIE do rozstrzygania kolejności zdarzeń wewnątrz świecy 4h
  (ceny high/low/open/close), nie do liczenia cech ani wolumenu. Sprawdzone przed rundą:
  6 576 świec 4h z okna 2023–2026 ma komplet 48 świec 5m; high zgadza się co do grosza we
  wszystkich, a open/low/close różnią się w **jednej** świecy (44 / 91 / 26 USDT) — ta świeca
  zostanie nazwana w wyniku, a w trybie 5m prawdą jest ścieżka 5m.
- **Pomiar opisowy przed rundą** (skrypt w scratchpadzie sesji, wynik przepisany tu, bez
  modelu i bez etykiet — służy rachunkowi mocy): bariera 1,5·ATR to mediana **2,36 %** ceny
  (p10–p90: 1,43–4,20 %) na 6,8 roku; stopa dotknięcia poziomu zlecenia w 1 świecy (średnia
  long/short): limit po close **99,8 %**, cofnięcie 0,25·ATR 63,7 %, **0,5·ATR 35,3 %**,
  1,0·ATR 11,6 %, wybicie **45,2 %**; w 3 świecach odpowiednio 99,9 / 80,1 / 60,0 / 31,6 / 64,4 %.

## Rozstrzygnięcia projektowe (zapisane PRZED przebiegiem)

### Jedna zmienna

**Mechanika wypełnień i wyjść na ścieżce cen** zamiast odczytu z etykiety. Wszystko inne
zamrożone jak w M1/F1 (ramię A): cechy `REVERSION_FEATURES` (4), bez bramki reżimu
(`REGIME_ALL`), V = 3, wagi klas `balanced`, walk-forward 60/28/28, seed 42, model kosztów
`maker_limit`, noga timeout `taker`, ATR_MULTIPLIER = 1,5 (zasada 3 — ten sam mnożnik
w etykiecie i w symulowanym stopie). **Model jest trenowany RAZ na tych samych etykietach;
warianty różnią się wyłącznie symulacją wykonania po sygnale.** Dzięki temu lejek sygnałów
(ocenione świece, abstynencja, bramki) jest identyczny co do sztuki między wariantami
i kontrolą — porównanie „jabłka do jabłek" z konstrukcji, jak w H3.

### Warianty wejścia (3, każdy z werdyktem)

Zlecenie składane w chwili zamknięcia świecy sygnału `t`, ważne `k` świec; `d` = kierunek
sygnału (+1 long / −1 short), `ATR` = `atr_14[t]` (ten sam, którego użyła etykieta).

| wariant | rodzaj zlecenia | poziom P | noga wejścia |
|---|---|---|---|
| **W1a `limit_close`** | limit | `close[t]` | maker (bez poślizgu) |
| **W1b `limit_pullback`** | limit | `close[t] − d·0,5·ATR` | maker (bez poślizgu) |
| **W1c `stop_breakout`** | stop (aktywacja → rynek) | `high[t]` dla long, `low[t]` dla short | taker (fee + poślizg 2 bps) |

**Dlaczego 0,5·ATR, a nie inne cofnięcie:** jedna, z góry wybrana wartość = jedna trzecia
bariery; 0,25·ATR (64 % wypełnień) prawie nie odsiewa, 1,0·ATR (12 %) zagładza próbę.
Inne wartości NIE będą uruchamiane — to byłoby strojenie po wyniku.

**Czas ważności `k` — rozstrzygnięcie delegacji „sam sprawdź":** **k = 1 świeca** (4 h).
Nie z wyniku, tylko z horyzontu modelu: etykieta mówi „ruch ±1,5·ATR w ciągu 3 świec od
sygnału"; wypełnienie w 3. świecy zostawia z tej prognozy jedną świecę. k = 2 i k = 3 liczone
są **wyłącznie opisowo** (stopa wypełnień, udziały wyjść, B, C, próg — bez trafności i werdyktu).

### Reguły wypełnienia (identyczne w kodzie i tutaj)

1. **Wejście.** Świeca `j ∈ (t, t+k]`. Limit kupna po P wypełnia się, gdy `low[j] < P`
   (**ściśle** — cena musi PRZEBIĆ poziom, dotknięcie nie wystarcza; konserwatywnie), po cenie
   `min(open[j], P)` (gdy świeca otwiera się poniżej limitu, wypełnienie po otwarciu). Stop
   kupna po P aktywuje się, gdy `high[j] > P`, po cenie `max(open[j], P)` plus poślizg taker.
   Sprzedaż symetrycznie. Brak wypełnienia do końca świecy `t+k` = **brak transakcji**; sygnał
   trafia do osobnego dziennika `unfilled` (z etykietą) do diagnostyki selekcji.
2. **Poziomy wyjścia** od ceny wypełnienia `E`: TP = `E + d·1,5·ATR`, SL = `E − d·1,5·ATR`
   (na żywo TP/SL ustawia się od ceny wejścia, nie od zamknięcia świecy sygnału). Timeout:
   zamknięcie świecy `t+V` (V = 3, od sygnału — horyzont prognozy), po rynku (taker).
   Jeśli wypełnienie nastąpiło w świecy `t+V` (tylko przy k = 3), pozycja kończy się w tej świecy.
3. **Kolejność zdarzeń — tryb 4h (cała historia 6,8 roku):** w świecy wypełnienia, jeśli
   wypełnienie nastąpiło po cenie otwarcia (świeca otworzyła się za poziomem), cała ścieżka tej
   świecy liczy się jak w etykiecie; jeśli wypełnienie nastąpiło „gdzieś w środku", to w tej
   świecy **liczy się tylko SL** (mógł paść po wypełnieniu), a **TP nie** (mógł paść przed) —
   konserwatywnie. W kolejnych świecach: TP gdy `high ≥ TP`, SL gdy `low ≤ SL`; obie naraz →
   reguła etykiety (bliższa otwarciu pierwsza).
4. **Kolejność zdarzeń — tryb 5m (okno 2023-07 → 2026-07, część kalibracyjna):** te same reguły
   na świecach 5m wewnątrz świec 4h; obie bariery w jednej świecy 5m → **SL pierwszy**
   (konserwatywnie). Timeout = zamknięcie ostatniej świecy 5m świecy `t+V` (= `close[t+V]`).
5. **Koszty:** noga wejścia wg wariantu (tabela), wyjścia jak dziś (`tp` maker, `sl` taker,
   `timeout` taker); funding za świece od wypełnienia do wyjścia włącznie; sizing od ceny `E`.
6. **Bramka kosztowa** liczona RAZ przy zbieraniu sygnałów, kosztem `maker_limit` (0,0009),
   żeby lejek był wspólny; dla `stop_breakout` runda podaje osobno, ile transakcji nie
   przeszłoby bramki taker (0,0014) — diagnostyka, nie filtr. (Na 4h bramka odrzuca 0 % — S1.)

### Kontrola (0 wariantów)

Przebieg dzisiejszym silnikiem (odczyt wyjścia z etykiety) na tych samych danych i konfiguracji
— musi odtworzyć ramię A z M1/F1 **co do sztuki**: n = 8 033, trafień 4 046, p = 50,3672 %.
Bez tej zgodności wynik rundy jest nieważny (zmieniło się coś poza zmienną).

### Część kalibracyjna (0 wariantów): 4h ≈ 5m?

Na oknie 2023-07 → 2026-07 (jeden trening, 3 lata) każdy wariant przy k = 1 policzony **dwa
razy**: trybem 4h i trybem 5m. Raportowane: odsetek transakcji o innym powodzie wyjścia,
o innej cenie wyjścia, o innym statusie wypełnienia; kierunek i wielkość obciążenia trybu 4h
w B, C i udziale timeoutów. **Bez trafności i bez werdyktów** — to pomiar błędu przybliżenia,
którym obciążone są wyniki na pełnej historii (lata 2019–2023 nie mają świec 5m).

### Rachunek mierzalności (zasada 18)

`expected_trades(14 448 świec, abstynencja 43,84 %)` = 8 114 × stopa wypełnień (opisowa, k = 1):

| wariant | stopa wypełnień (opis.) | oczekiwane `n` | pasmo `wald_half_width` | wymagane `n` do negatywu (moc 80 %, 50,37 % vs 52,93 %) |
|---|---|---|---|---|
| W1a `limit_close` | ~99,8 % | ~8 100 | ±1,09 pp | 4 481 → **1,8×** |
| W1b `limit_pullback` | ~35 % | ~2 850 | ±1,84 pp | 4 481 → **0,64×** |
| W1c `stop_breakout` | ~45 % | ~3 650 | ±1,62 pp | 4 481 → **0,81×** |

Stopy wypełnień są **bezwarunkowe** (bez kierunku sygnału); warunkowe zmierzy runda.
Wniosek z tabeli, zapisany uczciwie: **pytanie „czy wykonanie odsłania edge" jest niemierzalne
dla każdego wariantu** (trafność musiałaby przekroczyć ~54 %, a projekt nigdy takiej nie
zmierzył — ten sam zapis co M1/F1). **Mierzalne jest pytanie odwrotne** (negatyw) dla W1a
z zapasem 1,8×; dla W1b/W1c moc do orzeczenia negatywu jest niepełna — ich werdykt może
wyjść NIEROZSTRZYGNIĘTY i tak zostanie zapisany. **Mierzalne z zapasem dla wszystkich trzech**
są wielkości, dla których ta runda istnieje: stopa wypełnień (dokładna), geometria B i C
(średnie z tysięcy transakcji), próg opłacalności, oraz **selekcja przez wypełnienie**
(różnica poprawności kierunku między sygnałami wypełnionymi a niewypełnionymi, z CI).
Dlatego runda startuje.

### Kryterium — zapisane PRZED uruchomieniem (per wariant)

- **POZYTYWNY:** `ci_low > break_even` tego wariantu. Pierwsza reakcja: **szukaj przecieku**
  (świece po `t` użyte tylko do wypełnień/wyjść — ale każdy taki wynik to najpierw podejrzenie),
  potem replikacja na innym instrumencie (zasada 9). Żadnego wdrożenia.
- **NEGATYWNY:** `ci_high < break_even` **i** `n ≥ required_trades(50,37 %, break_even wariantu)`.
- **NIEROZSTRZYGNIĘTY:** w pozostałych przypadkach — bez interpretacji w żadną stronę.
- **REGUŁA STOP:** trzy warianty i koniec serii W, niezależnie od wyniku. Żadnego innego
  cofnięcia, czasu ważności, reguły wejścia ani „mieszanki" wariantów.
- **Diagnostyka selekcji (nie kryterium):** wśród sygnałów z etykietą barierową (`label ≠ 0`)
  udział `direction·label > 0` osobno dla wypełnionych i niewypełnionych, różnica z 95 % CI.
  Oczekiwanie zapisane z góry: dla W1b wypełnione **gorsze** (adverse selection), dla W1c
  możliwe odwrotnie.

### Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **W1a ≈ kontrola:** wypełnienia ~100 %, różnice tylko z (a) ~0,2 % niewypełnionych, (b)
  wypełnień po lepszej cenie przy luce na otwarciu, (c) konserwatywnej obsługi świecy
  wypełnienia. Spodziewam się `p` w granicach ±0,3 pp od 50,37 %, progu ~52,9 %.
- **W1b:** `n` ~2,8 tys.; spodziewam się `p` **niższego** niż w kontroli (limit poniżej rynku
  wypełnia się, gdy cena spada dalej) — to byłby pierwszy zmierzony rozmiar adverse selection
  w projekcie. Bariera względem wejścia bez zmian (1,5·ATR/E), koszt bez zmian.
- **W1c:** koszt wejścia wyższy (taker: +0,03 % fee, +0,02 % poślizg) → próg wyżej o ~1 pp;
  `n` ~3,6 tys.
- **Wynik pozytywny w którymkolwiek wariancie traktuję z podejrzliwością proporcjonalną do jego
  niezwykłości** — projekt złapał już trzy przecieki (Z17, Z17b, Z9).

### Czego ta runda NIE raportuje i NIE interpretuje

- **k = 2, 3 oraz cała część kalibracyjna: bez `hit_rate`, `ci_*`, `z_stat`, `margin`,
  `classification`.** Liczby te trafią do `raw_output.txt` (zasada 11 jest bezwarunkowa)
  z adnotacją, że nie uczestniczą w decyzji — precedens H3/D5.
- **`classification` z `metrics.classify_checkpoint`** nie jest kryterium (wniosek 24).
- **Nic o nowym celu modelu** (TP 5 % depozytu, częściowe wyjścia) — osobna runda z własną
  pre-rejestracją.

### Kogo NIE ma w zbiorze — zapisane z góry

(a) sygnały niewypełnione (W1b ~65 %, W1c ~55 % — ich etykiety są w dzienniku `unfilled`
i wchodzą do diagnostyki selekcji, nie do trafności); (b) 43,84 % świec, na których model
odmawia kierunku; (c) lata 2019-09 → 2023-06 tylko w trybie 4h (bez rozstrzygania kolejności
świecami 5m) — obciążenie zmierzy część kalibracyjna na 3 latach; (d) tylko BTC, jeden seed
(XGBoost deterministyczny — sweep seedów nic nie mierzy); (e) brak księgi zleceń: „przebicie
poziomu = wypełnienie" to nadal założenie, tylko ostrzejsze niż dotąd; (f) pozycje nakładające
się w czasie sizowane niezależnie (uproszczenie Fazy 0, jak dotąd); (g) jedna świeca 4h
niezgodna z agregatem 5m.

## Definition of Done tej rundy

- Nowy moduł `backtest/execution.py` (czyste funkcje symulacji wypełnienia i wyjścia) +
  testy jednostkowe i **property-based (`hypothesis`)**: brak lookaheadu (wynik zależy tylko od
  świec `> t`), cena wypełnienia wewnątrz zakresu świecy, brak przebicia ⇒ brak transakcji,
  SL-first przy obu barierach w jednej świecy 5m, zgodność trybu 4h z 5m na ścieżce
  monotonicznej. Skill `engineering:testing-strategy` PRZED testami (zasada 19).
- `backtest/engine.py`: nowy tryb `fill_model="path"` z domyślnym `"label"` odtwarzającym
  dzisiejsze zachowanie **bit w bit** (test regresji), oraz rozdzielenie zbierania sygnałów od
  symulacji equity, żeby jeden trening obsłużył wszystkie warianty.
- ADR w `docs/rag/04` (symulacja wypełnień — co jest daną, co założeniem), skill
  `engineering:architecture` PRZED pisaniem (zasada 19).
- Bramki: `data:validate-data` (16a, przeliczenie ≥ 1 liczby drugą drogą: koszt z journalu
  vs z mieszanki nóg; `n` z `expected_trades` vs journal), `data:statistical-analysis` (16b),
  `engineering:code-review` (16c) — wszystkie wczytane na tej gałęzi.
- `raw_output.txt` pełny; wiersz w `runs/INDEX.md` + nowy licznik serii W; synteza w `STATUS.md`;
  skrypt rundy na `runs/ZAMROZONE.txt`; sekcja „Użyte skille" z rejestru gałęzi.

---

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz wykonanie-po-cenie`)_
