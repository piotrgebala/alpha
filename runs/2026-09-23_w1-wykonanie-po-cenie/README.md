# W1 — wykonanie po konkretnej cenie: uczciwy model wypełnień w backteście (2026-09-23)

> **STATUS: ZAMKNIĘTA.** Wszystko do sekcji „Czego ta runda NIE raportuje" włącznie zapisano
> **przed napisaniem linijki kodu produkcyjnego** — commit `9b09177` zawiera wyłącznie
> pre-rejestrację i poprzedza commit z kodem. Sekcje od „Wynik" w dół dopisano po przebiegu.
> **Licznik W: 3/3 — WYCZERPANY, reguła STOP.** Werdykty: W1a **NEGATYWNY**, W1b
> **NIEROZSTRZYGNIĘTY** (wg pre-rejestrowanego kryterium trafności) przy **istotnie ujemnym
> zwrocie netto**, W1c **NEGATYWNY**. Walidacja (16a): **CAVEATS** (sekcja niżej).

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Backtest liczył wykonanie prawie tak, jak będzie na żywo.** Zlecenie po cenie zamknięcia świecy
wypełnia się w 99,4 % przypadków (52 z 8 114 sygnałów przepada), a trafność zmienia się
z 50,37 % na 50,11 % — czyli o tyle, ile daje utrata tych 52 transakcji. Założenie z rundy C2.12
(„limit zawsze się wypełnia") było na świecach 4h prawie prawdziwe.

**Tańsze wejście na cofnięciu wygląda lepiej, ale nie jest lepsze.** Limit pół ATR poniżej rynku
wypełnia się tylko w 35 % przypadków, a trafność wychodzi 53,15 % — po raz pierwszy w projekcie
punktowo powyżej progu opłacalności (52,81 %). Ale gdy zsumować pieniądze, a nie liczbę
wygranych, **średni wynik na transakcji jest stratą** (−0,096 % nominału; pewność, że to nie
przypadek: t = −3,9). Wygrane są małe (59 % timeoutów kończy się +0,17 % powyżej wejścia),
przegrane pełne (stop −2,45 %), a stopów jest więcej niż zysków (21 % wobec 16 %). Próg
opłacalności zakłada wygrane i przegrane tej samej wielkości — tu tak nie jest, więc trafność
przestaje być właściwą miarą. To pułapka, którą warto zapamiętać: **więcej wygranych ≠ więcej
pieniędzy.**

**Wejście na wybiciu jest gorsze na obu frontach:** droższe (zlecenie po rynku podnosi próg do
54,83 %) i trafia rzadziej (46,13 %) — kupujemy na lokalnym szczycie, po którym cena częściej
zawraca.

**Żaden sposób wejścia nie tworzy przewagi tam, gdzie model jej nie ma** — dokładnie tak, jak
zapisano z góry. Zysk z rundy jest inny: backtest ma teraz model wypełnień zgodny z zasadą „po
konkretnej cenie", zmierzyliśmy po raz pierwszy, jak wypełnienie wybiera gorsze sygnały, i wiemy,
że przybliżenie świecami 4h myli się rzadko (0,3–2,7 % transakcji) i na niekorzyść strategii.

---

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
- **Komenda:** `py -m backtest.run_execution_w1` (pełny output: `raw_output.txt`; skrypt na liście
  `runs/ZAMROZONE.txt`; buduje na `backtest/checkpoint_lib.py` i nowym `backtest/execution.py`).
  Pre-rejestracja: commit `9b09177`, kod i wynik: commit scalający tę gałąź. Czas przebiegu: 11 s
  (dane 4h są małe — 86 okien treningowych).
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

### 0. Kontrola — baseline nienaruszony

Tryb `label` na tych samych danych i konfiguracji: **n = 8 033, trafień 4 046, p = 50,3672 %** —
identycznie z ramieniem A z M1/F1 (co do sztuki). Lejek: 14 448 ocenionych świec, abstynencja
43,84 % (6 334), bramki 0, **8 114 sygnałów kandydujących** — wspólny dla wszystkich wariantów
(jeden trening, `collect_signals`).

### 1. Warianty z werdyktem (k = 1)

| wariant | n | niewypełnione | trafność `p` | CI 95 % | próg BE | margines (pkt trafności) | werdykt (pre-rejestracja) |
|---|---|---|---|---|---|---|---|
| kontrola (label) | 8 033 | — | 50,37 % | [49,27; 51,46] | 52,93 % | −2,57 pp | odniesienie, 0 wariantów |
| **W1a** limit po close | 7 978 | 52 (0,6 %) | **50,11 %** | [49,02; 51,21] | 52,96 % | −2,84 pp | **NEGATYWNY** (ci_high < próg, n ≥ 2 922) |
| **W1b** limit na cofnięciu 0,5·ATR | 2 858 | 5 233 (64,5 %) | **53,15 %** | [51,32; 54,98] | 52,81 % | **+0,34 pp** | **NIEROZSTRZYGNIĘTY** (CI przecina próg; n < 3 276) |
| **W1c** stop na wybiciu | 3 800 | 4 260 (52,5 %) | **46,13 %** | [44,55; 47,72] | 54,83 % | −8,70 pp | **NEGATYWNY** (ci_high < próg, n ≥ 980) |

Stłumione kill-switchem: 84 / 23 / 54 (bilans lejka domyka się: n + niewypełnione + stłumione
= 8 114 w każdym wariancie).

### 2. Zwrot netto per trade — statystyka nośna (zasada 12, wytyczna o pooled t)

| wariant | średnia (% equity) | mediana (% equity) | t_stat | N_eff | t_neff | średnia (% nominału) | mediana (% nominału) |
|---|---|---|---|---|---|---|---|
| kontrola | −0,0056 % | −0,0067 % | −4,09 | 3 859 | −2,83 | −0,081 % | −0,083 % |
| W1a | −0,0066 % | −0,0073 % | −4,84 | 4 092 | −3,46 | −0,082 % | −0,090 % |
| **W1b** | **−0,0092 %** | +0,0016 % | **−3,90** | 2 450 | **−3,61** | **−0,096 %** | **+0,017 %** |
| W1c | −0,0150 % | −0,0219 % | −7,55 | 2 439 | −6,05 | −0,204 % | −0,270 % |

**W1b: trafność powyżej progu przy stracie na transakcji.** Rozbicie wypłaty brutto per typ wyjścia
(% ceny wejścia):

| typ wyjścia | udział | średnia | wygrane |
|---|---|---|---|
| take-profit | 16,2 % | +2,44 % | 100 % |
| stop-loss | **21,2 %** | **−2,45 %** | 0 % |
| timeout | 62,6 % | **+0,17 %** | **59,1 %** |

Wygrane to w 79 % małe timeouty; straty to pełne stopy, częstsze niż zyski (SL:TP = 21:16).
Wzór progu `0,5·(1 + C/B)` zakłada wypłaty ±B — po wejściu oddalonym od kotwicy etykiety
przestaje być progiem opłacalności. Średnia brutto −0,015 %, netto −0,096 % nominału; mediana
dodatnia (+0,017 %) — klasyczny rozjazd średniej i mediany przy skośnych wypłatach (16b).

### 3. Wypełnienia i selekcja — kogo NIE ma w zbiorze

| wariant | wypełnienia (long / short) | poprawność kierunku wg ETYKIETY: wypełnione | niewypełnione | różnica, CI 95 % |
|---|---|---|---|---|
| W1a | 99,4 % (99,2 / 99,6) | 50,83 % (n 2 784) | 92,0 % (n 25) | −41 pp — n = 25, bez znaczenia |
| **W1b** | 35,5 % (34,5 / 36,5) | **21,29 %** (n 1 254) | **75,10 %** (n 1 570) | **−53,8 pp [−56,9; −50,7]**, z = −33,8 |
| **W1c** | 47,5 % (48,9 / 46,2) | **72,57 %** (n 1 469) | 28,19 % (n 1 341) | **+44,4 pp [+41,1; +47,7]**, z = +26,2 |

Pierwszy w projekcie pomiar selekcji przez wypełnienie. To w większości MECHANIKA, nie
informacja: limit poniżej rynku wypełnia się wtedy, gdy cena idzie przeciw pozycji, więc etykieta
liczona od `close` częściej mówi „zły kierunek"; stop na wybiciu — odwrotnie. Dlatego wynik
transakcji liczy się od ceny wypełnienia, a etykieta służy tylko jako diagnostyka selekcji.

### 4. Geometria, koszt, wrażliwość na czas ważności

| wariant | k | n | wypełnienia | tp / sl / timeout | B | C | próg BE | świec w pozycji |
|---|---|---|---|---|---|---|---|---|
| kontrola | — | 8 033 | 100 % | 17,9 / 17,0 / 65,1 | 1,382 % | 0,0811 % | 52,93 % | 3,66¹ |
| W1a | 1 | 7 978 | 99,4 % | 17,5 / 17,2 / 65,3 | 1,375 % | 0,0812 % | 52,96 % | 2,68 |
| W1b | 1 | 2 858 | 35,5 % | 16,2 / 21,2 / 62,6 | 1,446 % | 0,0813 % | 52,81 % | 2,68 |
| W1c | 1 | 3 800 | 47,5 % | 18,1 / 17,1 / 64,8 | 1,359 % | **0,1312 %** | **54,83 %** | 2,72 |
| W1b | 2 | 4 129 | 51,5 % | 13,6 / 18,8 / 67,6 | 1,330 % | 0,0828 % | 53,11 % | 2,46 |
| W1b | 3 | 4 840 | 60,3 % | 11,6 / 16,9 / 71,4 | 1,250 % | 0,0838 % | 53,35 % | 2,24 |
| W1c | 2 | 4 713 | 59,6 % | 16,2 / 16,7 / 67,1 | 1,326 % | 0,1322 % | 54,98 % | 2,56 |
| W1c | 3 | 5 218 | 66,1 % | 14,6 / 16,0 / 69,4 | 1,284 % | 0,1330 % | 55,18 % | 2,40 |

¹ w trybie `label` liczone od świecy sygnału (`exit_bar_offset`), w trybie `path` od wypełnienia.
Wiersze k = 2, 3 — wyłącznie opisowo (bez trafności i werdyktu, reguła H3/D5); dłuższa ważność
kupuje wypełnienia kosztem późniejszego wejścia (więcej timeoutów, węższa bariera, wyższy próg).
W1c: 0 z 3 800 transakcji nie przeszłoby bramki kosztowej liczonej nogą taker (0,0014) — wspólna
bramka maker nie zniekształciła lejka.

### 5. Kalibracja: tryb 4h ≈ tryb 5m (okno 2023-07 → 2026-07, 36 okien, 3 272 sygnały)

| wariant | tryb | n | niewyp. | tp / sl / timeout | próg BE | zgodność z trybem 4h (na wspólnych transakcjach) |
|---|---|---|---|---|---|---|
| W1a | 4h | 3 230 | 20 | 18,1 / 18,2 / 63,7 | 53,43 % | — |
| W1a | 5m | 3 234 | 19 | 18,4 / 18,2 / 63,4 | 53,41 % | powód wyjścia **99,7 %**, cena wyjścia 99,6 %, cena wejścia 100 %; tylko-4h 18, tylko-5m 22 |
| W1b | 4h | 1 266 | 2 006 | 18,9 / 20,6 / 60,5 | 53,33 % | — |
| W1b | 5m | 1 266 | 2 006 | 19,4 / 20,5 / 60,0 | 53,30 % | powód wyjścia **99,4 %**, cena wyjścia 99,4 %, wejścia 100 %; zbiory identyczne |
| W1c | 4h | 1 397 | 1 857 | 18,8 / 18,5 / 62,7 | 55,65 % | — |
| W1c | 5m | 1 404 | 1 868 | 20,3 / 16,7 / 63,0 | 55,66 % | powód wyjścia **97,3 %**, cena wyjścia 97,3 %, wejścia 100 %; tylko-5m 7 |

Kierunek rozbieżności (macierze w `raw_output.txt`): tryb 4h zamienia **wyłącznie** w stronę
gorszą — W1c: 16 × „SL" zamiast „timeout", 7 × „SL" zamiast „TP", 15 × „timeout" zamiast „TP";
ani jednej zamiany na korzyść. Przybliżenie 4h dla lat 2019–2023 jest więc **konserwatywne**;
różnice trafności między trybami (poza decyzją, sekcja 6 `raw_output.txt`): +0,24 / +0,32 /
+1,40 pp na korzyść trybu 5m. Świece 4h niezgodne z agregatem 5m: **2** (2023-11-10 12:00,
2024-10-28 20:00) — pre-rejestracja mówiła o jednej (tolerancja 0,01 USDT w pomiarze wstępnym);
w trybie 5m prawdą jest ścieżka 5m.

### 6. Mierzalność ex post (zasada 18)

`expected_trades(abstynencja, stopa wypełnień)` vs journal: 8 062 / 7 978, 2 881 / 2 858,
3 854 / 3 800 (różnica = stłumione kill-switchem + zaokrąglenie). Pasmo: 1,10 / 1,83 / 1,59 pp.
Próg wykrywalności edge'u 54,05 / 54,64 / 56,42 % → dla każdego wariantu pytanie „czy jest edge"
było NIEMIERZALNE (jak zapisano z góry); pytanie odwrotne rozstrzygnięte dla W1a i W1c z zapasem
(2,7× / 3,9× wymaganej próby), dla W1b bez zapasu (0,87×) — stąd NIEROZSTRZYGNIĘTY.

## Co na plus (+)

- **Pre-rejestracja dowodliwa z gita** (`9b09177` przed kodem), reguły 1–6 odtworzone w kodzie
  co do litery, każda z testem przykładowym; 6 własności w `hypothesis` (brak lookaheadu, cena
  w zakresie świecy, brak przebicia ⇒ brak transakcji, zgodność trybów na ścieżce monotonicznej).
- **Kontrola bit w bit** — ramię A z M1/F1 odtworzone co do sztuki (n, trafienia); domyślny tryb
  silnika nie zmienił się (regresje literałami w `test_engine.py`, 70/70).
- **Runda wyszła dokładnie tak, jak przewidziano** w „Arytmetyce oczekiwań" dla W1a (p w ±0,3 pp
  od kontroli) i W1c (próg +1 pp, n ~3,6 tys.) — i **inaczej niż przewidziano dla W1b**, gdzie
  spodziewano się NIŻSZEJ trafności, a wyszła wyższa. Rozbieżność została wyjaśniona pomiarem
  (asymetria wypłat), nie zignorowana.
- **Ograniczenie z C2.12 zmierzone po raz pierwszy:** adverse selection istnieje (W1b: −53,8 pp
  poprawności wg etykiety), ale na 4h jej koszt ekonomiczny przy limicie po close jest pomijalny
  (0,6 % niewypełnionych, +0,0004 % ceny optymizmu na otwarciu).
- **Jeden trening dla wszystkich wariantów** — lejek identyczny z konstrukcji; symulacje trwają
  ułamki sekund, więc przyszłe warianty wykonania są tanie.
- **Przybliżenie 4h skalibrowane:** myli się w 0,3–2,7 % transakcji i zawsze na niekorzyść.

## Co na minus (−)

- **Kryterium pre-rejestrowane dla W1b okazało się niewystarczające.** `ci_low > break_even`
  zakłada wypłaty ±B; przy wejściu oddalonym od kotwicy etykiety trafność rośnie, a pieniądze
  maleją. Werdykt „NIEROZSTRZYGNIĘTY" jest formalnie poprawny, ale to statystyka nośna z wytycznej
  (pooled t = −3,90) rozstrzyga ekonomicznie — i została dodana do skryptu PO obejrzeniu wyniku
  W1b (sekcja 3b). Zapisane uczciwie: to nie zmienia werdyktu żadnego wariantu, ale przyszłe
  pre-rejestracje muszą mieć t-stat w kryterium od początku.
- **„Przebicie = wypełnienie" to nadal założenie** (brak księgi zleceń): w rzeczywistości limit
  na poziomie, przez który cena przeszła wąskim knotem, może zostać niewypełniony. Kierunek:
  optymistyczny dla W1a/W1b. Kalibracja wymaga własnych filli z paper tradingu (Faza 3).
- **Cena wypełnienia `min(open, P)` dla limitu jest lekko optymistyczna** — zlecenie złożone
  przed otwarciem świecy realnie wypełnia się po P, nie po lepszym otwarciu. Zmierzone: W1a
  +0,00043 % ceny średnio (28 % transakcji, maks. +0,063 %), W1b/W1c 0 — 0,5 % kosztu, bez
  wpływu na werdykt; reguła zostaje, bo była pre-rejestrowana, a poprawka to zmiana po wyniku.
- **Lata 2019-09 → 2023-06 tylko w trybie 4h** — obciążenie zmierzone (≤ 1,4 pp, konserwatywne),
  ale nie zerowe.
- **W1b/W1c wycinają 52–65 % sygnałów** — ich wynik dotyczy wąskiej, mechanicznie wybranej
  próby; nie mówi nic o sygnałach niewypełnionych.
- Jeden instrument, jeden seed (XGBoost deterministyczny), pozycje nakładające się sizowane
  niezależnie (uproszczenie Fazy 0).

## Walidacja (zasada 16a) — werdykt: **CAVEATS**

- **Kluczowe liczby drugą drogą** (skrypt walidacyjny w scratchpadzie sesji, wprost z journalu,
  poza `metrics.py`): trafność 50,1128 / 53,1491 / 46,1316 % — zgodne z tabelą co do 4. miejsca;
  koszt policzony analitycznie z mieszanki nóg (fee + poślizg wg udziałów tp/sl/timeout) vs
  z journalu: 0,08126 vs 0,08125 %, 0,08190 vs 0,08133 %, 0,13093 vs 0,13122 % — różnica to
  funding (−0,00002 / −0,00057 / +0,00029 pp); bilans lejka 8 114 = n + niewypełnione +
  stłumione w każdym wariancie; `expected_trades` odtwarza n z dokładnością 1–1,4 %.
- **Kogo NIE ma w zbiorze:** (a) niewypełnione 0,6 / 64,5 / 52,5 % sygnałów — zmierzone wraz
  z ich etykietami (sekcja 3); (b) abstynencja 43,84 %; (c) stłumione kill-switchem 84 / 23 / 54;
  (d) 2019–2023 bez rozstrzygania świecami 5m (sekcja 5); (e) 2 świece niezgodne 5m/4h;
  (f) sygnały z etykietą 0 w diagnostyce selekcji (z definicji).
- **Red flag „wynik potwierdza hipotezę":** oczekiwanie brzmiało „żaden wariant nie zmieni
  werdyktu" — W1b wyszedł punktowo POWYŻEJ progu, czyli w stronę przeciwną do oczekiwanej;
  pierwszą reakcją było szukanie przecieku (świece po `t` używane wyłącznie do wypełnień/wyjść —
  własność testowana w `hypothesis`), drugą — rozbicie wypłat, które wyjaśnia efekt bez przecieku.
- **Rząd wielkości:** trafności 46–53 %, progi 52,8–55,2 %, koszt maker 0,081 %, taker 0,131 % —
  w zakresach z listy kontrolnej; udziały tp + sl + timeout = 100 %; N_eff ≤ n.
- **Zastrzeżenia (CAVEATS), które czytelnik MUSI znać:** (1) 53,15 % w W1b **nie jest edge'em**
  — średni zwrot netto istotnie ujemny; nie wolno cytować tej liczby bez t-statu; (2) kryterium
  trafności jest niekompletne dla wejść oddalonych od kotwicy etykiety; (3) „przebicie =
  wypełnienie" i `min(open, P)` są optymistyczne (rząd 0,5 % kosztu); (4) lata bez 5m — obciążenie
  konserwatywne ≤ 1,4 pp.

## Przegląd diffu (zasada 16c)

**Przegląd diffu (16c): Approve** — sprawdzono: brak lookaheadu (symulacja czyta wyłącznie świece
`> t` i nie dalej niż `t+V`; własność w `hypothesis`), off-by-one (ważność ≤ V wymuszona
walidacją, timeout na `close[t+V]` jak w etykiecie, świeca wypełnienia liczona od jej indeksu
włącznie), tie-break identyczny z `labeling.py` (test dla long i short), noga wejścia zależna od
rodzaju zlecenia tylko w trybie `path` przy `maker_limit`, tryb `label` bit w bit (regresje
literałami 1 280 / 95 126,0168 zielone), dziennik `unfilled` domyka lejek co do sztuki, skrypty
zamrożone nietknięte (import `_load` zastąpiony `fetch_native` w `checkpoint_lib`), 610/610
testów, ruff/black czyste. Uwagi niekrytyczne, zapisane do wiedzy: (a) kill-switch sprawdzany
PRZED próbą wypełnienia — sygnał stłumiony liczy się jako stłumiony, nawet gdyby się nie
wypełnił (bilans lejka pozostaje poprawny); (b) `build_intrabar_path` wyprowadza interwał świec
drobnych z dwóch pierwszych znaczników — poprawne przy danych bez dziur (sprawdzone), przy dziurze
na starcie rzuciłoby ValueError o liczbie świec, nie o interwale; (c) w trybie 4h dla stopu na
wybiciu SL w świecy wypełnienia bywa liczony, choć mógł paść przed wypełnieniem — obciążenie
konserwatywne, zmierzone w części kalibracyjnej (16 z 1 397).

## Wniosek

Backtest mierzy teraz wykonanie „po konkretnej cenie" i **nic w werdykcie projektu się nie
zmienia**: limit po zamknięciu świecy wypełnia się niemal zawsze (99,4 %), więc dotychczasowe
wyniki nie były zawyżone przez założenie wypełnienia; wejście na wybiciu jest droższe i trafia
gorzej; wejście na cofnięciu podnosi trafność do 53,15 %, ale **traci pieniądze** (−0,096 %
nominału na transakcję, t = −3,9), bo wygrywa małymi timeoutami, a przegrywa pełnymi stopami.
Trafność powyżej progu okazała się iluzją geometrii — w tym projekcie „istotne" znaczy dolny
kraniec CI trafności ponad progiem **i** dodatni zwrot netto; drugiego warunku W1b nie spełnia.
Seria W zamknięta: 3/3, reguła STOP.

## Rekomendacja

1. **Tryb `path` z regułą `limit_close` i k = 1 staje się domyślnym modelem wykonania dla
   PRZYSZŁYCH rund** (odzwierciedla zasadę użytkownika), a `label` zostaje nazwanym wariantem
   odtwarzającym historię — ta sama konwencja co C2.12 (decyzja do potwierdzenia przez
   użytkownika; do tej pory domyślnym w `engine.py` pozostaje `label`, więc skrypty zamrożone
   są nietknięte).
2. **Do kryterium każdej przyszłej pre-rejestracji dopisać `t_stat` zwrotu netto obok
   `ci_low > break_even`** — wniosek skumulowany 43; `docs/skills/bramki-jakosci.md` B3 uzupełniony.
3. **Nie testować kolejnych reguł wejścia ani czasów ważności** (STOP). Jedyna droga do lepszego
   modelu wypełnień to dane o własnych fillach (Faza 3, paper trading).
4. **Następna runda — nowy cel modelu** (decyzja użytkownika: częściowe wyjście 50 % przy +5 %
   depozytu przy dźwigni 3×, stop na break-even, reszta dalej) — osobna pre-rejestracja z własnym
   licznikiem; lekcja z W1b obowiązuje tam podwójnie: przy wypłatach asymetrycznych z definicji
   werdykt musi opierać się na zwrocie netto z CI, nie na trafności.

## Użyte skille

Rejestr gałęzi `wykonanie-po-cenie` (`py tools/skill_audit.py raport --galaz wykonanie-po-cenie`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-quant` | dyscyplina rundy: jedna zmienna, rachunek mocy z abstynencji i stopy wypełnień, ostrzeżenie o tautologii `hit_rate_barrier` |
| `anthropic-skills:clas5-runda` | procedura: gałąź → pre-rejestracja w osobnym commicie → skrypt na `checkpoint_lib` → bramki → INDEX/STATUS/README |
| `engineering:architecture` | ADR w `docs/rag/04` (symulacja wypełnień: dane vs założenia, odrzucone alternatywy) |
| `engineering:testing-strategy` | plan testów `execution.py`/`engine.py`: własności (lookahead, zakres ceny, brak przebicia), przykłady reguł, regresja bit w bit |
| `data:validate-data` | bramka 16a: przeliczenia drugą drogą, „kogo nie ma", red flag, werdykt CAVEATS |
| `data:statistical-analysis` | bramka 16b: mediana obok średniej, CI dla różnicy proporcji, pytanie o właściwą miarę przy skośnych wypłatach |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Wczytane bezpośrednio (odczyt plików, nie przez narzędzie Skill — zapoznanie na prośbę
użytkownika, poza momentami z tabeli zasady 19): `quant-strategy-catalog`, `ta-toolkit`,
`lean-research`. Z tabeli zasady 19 pominięte: `dataviz` (runda bez wykresów), `update-config`
(bez zmian w `.claude/settings.json`), `data:explore-data` (dane bez zmian — te same parquety co
Z5b/Z9, spójność 5m↔4h sprawdzona wprost w skrypcie).
