---
status: active
last_verified: 2026-09-24
depends_on: [../rag/03_ryzyko_i_sizing.md, ../rag/05_metodologia_wytwarzania_i_testow.md]
---

# Bramki jakości rundy — pełna ściąga (rozwinięcie CLAUDE.md, zasada 16)

**Po co ten plik.** Zasada 16 w `CLAUDE.md` to krótkie przypomnienie: „zwaliduj write-up,
raportuj statystykę porządnie, przejrzyj kod przed merge". Ten plik mówi **jak dokładnie** to
zrobić — krok po kroku, z przykładami z naszych własnych rund. Treść pochodzi z trzech skilli
(`data:validate-data`, `data:statistical-analysis`, `engineering:code-review`), przepisanych na
potrzeby CLAS-5. Dzięki temu działa w każdym środowisku, także tam, gdzie pluginy nie są
zainstalowane — jedzie z repo.

**Kiedy czytać.** Trzy momenty, każdy ma swoją sekcję:

| Moment | Sekcja | Zasada |
|---|---|---|
| Kończysz opis rundy (README w `runs/`) i chcesz go opublikować | A. Walidacja write-upu | 16a |
| Piszesz liczby do tabeli wyników albo do rozmowy z użytkownikiem | B. Standard statystyk | 16b |
| Masz gotowy diff i chcesz go scalić do master | C. Przegląd kodu | 16c |

Język: prosty (zasada 17). Fachowe pojęcie wyjaśniamy w nawiasie przy pierwszym użyciu.

---

## A. Walidacja write-upu przed publikacją (zasada 16a)

Cel: zanim ktokolwiek przeczyta wynik rundy, sprawdzamy, czy liczby są prawdziwe, czy
metoda była uczciwa i czy wniosek naprawdę wynika z danych. Efekt: werdykt
**Ready / Caveats / Revision** zapisany w README rundy.

### A1. Lista kontrolna — przejdź po kolei

**Dane**

- [ ] **Źródło nazwane.** Który plik parquet, jaki interwał (5m/1h/4h), jaki zakres dat. Bez
  tego nikt nie odtworzy wyniku. Wpisz do sekcji *Metadane*.
- [ ] **Świeżość.** „Stan na" jest w README (data końca danych).
- [ ] **Kompletność.** Zero dziur w szeregu świec? (Sprawdzamy to od Z5: liczba świec =
  dni × świece/dzień.) Jeśli są dziury — napisz ile i gdzie.
- [ ] **Braki (NaN).** Ile wierszy odpada na rozgrzewce wskaźników (np. pierwsze 5760 świec dla
  `atr_pctrank_20d`)? Czy to jest odjęte od mianownika?
- [ ] **Duplikaty.** Brak podwójnych znaczników czasu (test `test_clean_ohlcv_removes_duplicate_timestamps`).
- [ ] **Filtry nazwane.** Które świece/sygnały odpadły i dlaczego: reżim `ambiguous`, bramka
  kosztowa, kill-switch, próg pewności, klauzula nierozstrzygalności. **To jest najważniejszy
  punkt tej listy — patrz A2.**

**Obliczenia**

- [ ] **Mianownik.** Trafność liczona z *transakcji* (n_trades), nie z sygnałów ani świec.
  Break-even liczony z tych samych transakcji. Jeśli w tabeli są trzy „n" — nazwij każde.
- [ ] **Definicja `p`.** Kanoniczna: udział transakcji z `gross_pnl > 0` (Z18). Inna definicja
  = inny wynik o 5–8 pp. Nie porównuj `p` liczonego dwiema definicjami.
- [ ] **Poziom agregacji.** Pooled (wszystkie transakcje razem) albo per fold — ale nigdy
  „średnia ze średnich per fold" bez ważenia liczbą transakcji. C2.12 pokazał, że per-fold
  `mean_sharpe` przy kilku transakcjach na fold produkuje wartości typu −60. Nośne są pooled
  t-stat i margines.
- [ ] **Okresy pełne.** Foldy pominięte (za mało transakcji) są policzone i wymienione
  („22 z 85 pominięte"). Fold niepełny na końcu danych — wykluczony, nie liczony jako pełny.
- [ ] **Ta sama baza danych.** Wyniki na starej bazie (2025-07→2026-07) i nowej
  (2023-07→2026-07) to osobne liczniki — nie porównuj ich 1:1 (C2.10).
- [ ] **Wersja pipeline'u.** Wynik sprzed naprawy (np. przeciek early stopping, Z17) i po
  naprawie to dwa różne pomiary. Napisz, którą wersją mierzono.

**Rozsądek**

- [ ] **Rząd wielkości.** Trafność kierunku w okolicach 45–55% (nie 80%). Break-even między
  50% a 85% (5m ma wysoki, 4h niski — Z9). Koszt na transakcję maker ≈ 0,04–0,08%, taker
  wyżej. Jeśli coś wystaje — szukaj błędu, nie ciesz się.
- [ ] **Ciągłość.** Wynik pasuje do poprzednich rund w `runs/INDEX.md`? Jeśli `p` skoczyło o
  5 pp między rundami, musi być jasna przyczyna (zmiana danych, naprawa buga) — inaczej to
  podejrzane.
- [ ] **Krzyżowe sprawdzenie.** Kluczowa liczba zgadza się z inną drogą (patrz A3).
- [ ] **Brzegi.** Co się dzieje w foldzie z 1 transakcją? W reżimie z 0 świec? Kod nie wypluwa
  tam NaN/inf jako „wyniku".

**Prezentacja**

- [ ] **Tytuł = wniosek**, nie nazwa metryki („trafność poniżej progu", nie „wyniki S1").
- [ ] **Formatowanie.** Przecinek dziesiętny po polsku, spójna liczba miejsc, pp (punkty
  procentowe) tam, gdzie porównujesz procenty.
- [ ] **Zastrzeżenia jawne** — sekcja *Co na minus (−)* pisana uczciwie, nie na siłę krótko.
- [ ] **Odtwarzalność.** Komenda + plik danych + seed + gałąź w *Metadane*; `raw_output.txt`
  obok README.

### A2. „Kogo NIE ma w zbiorze" — pytanie obowiązkowe

To pytanie zadajemy zawsze, bo dwa razy w tym projekcie odpowiedź zmieniła wniosek:

- **C2d:** pozorny edge 54,6% mieszkał w świecach, które bramka kosztowa potem odfiltrowała.
  Po bramce: 49,3%. Edge „istniał" tylko w transakcjach, których nie dało się wykonać.
- **S1:** wynik obowiązywał na **6,95% historii** — model wstrzymywał się od decyzji przez
  resztę czasu. Krach COVID i najszybsze ruchy były poza zbiorem. Werdykt zmieniono na *Caveats*.

Konkretnie sprawdź:

1. **Ile z całości trafiło do pomiaru?** Świece → po rozgrzewce → po reżimie → po bramce
   kosztowej → po progu pewności → transakcje. Napisz ten lejek liczbami. Jeśli ostatni
   krok to < 10% pierwszego, wynik opisuje wąski wycinek rynku i tak trzeba go nazwać.
2. **Czy odfiltrowane świece różnią się od zatrzymanych?** Jeśli filtr wycina np. wszystkie
   okresy wysokiej zmienności, wynik nie mówi nic o wysokiej zmienności.
3. **Czy reżim nie zagłodził próby?** `trend` = 0,53% świec (C2.10). Werdykt NO-GO na
   takiej próbie to „nie dało się zmierzyć", nie „zmierzono i nie działa". Rozróżniaj.
4. **Foldy pominięte** — ile i czy pomijanie nie koreluje z jakimś okresem rynku.
5. **Klauzula nierozstrzygalności** — jeśli n spadło poniżej progu mocy (S1b: 345 < 925),
   wynik jest *nierozstrzygalny*, nie „negatywny".

### A3. Przelicz jedną liczbę drugą drogą

Wybierz **co najmniej jedną** kluczową liczbę z README i policz ją niezależnie od skryptu —
ręcznie, w Pythonie, z surowego outputu. Sprawdzone wzory (na przykładzie S1):

```
p = 0,486017, n = 1037, B = 0,012609 (bariera jako % ceny), C = 0,000775 (koszt jako % ceny)

półszerokość CI (95%)  = 1,96 · sqrt(p·(1−p)/n)        = 0,0304  → CI [45,6%; 51,6%]
z względem monety       = (p − 0,5) / sqrt(0,25/n)        = −0,90
break-even p            = 0,5 + C / (2·B)                 = 0,5307
margines (pkt trafności)= p − break-even                  = −0,0447  (−4,5 pp)
margines (zwrot)        = (2p − 1)·B − C                  = −0,00113 (−0,11% na transakcję)
```

Uwaga: **dwie wielkości noszą nazwę „margines"** — w punktach trafności (kolumna `margin` w
`metrics.py`) i w jednostkach zwrotu (wzór z zasady 12). Zawsze napisz, o którą chodzi.

Inne szybkie sprawdzenia: suma transakcji po foldach = n pooled; udział timeoutów + udział
barier = 100%; liczba foldów aktywnych + pominiętych = łączna; n_eff ≤ n.

### A4. Czerwone flagi — jeśli widzisz, zatrzymaj się

- Wynik zmienił się o > 50% między rundami bez oczywistej przyczyny.
- Okrągłe liczby (dokładnie 1000 transakcji, dokładnie 50,00%) — często ślad filtra albo
  wartości domyślnej.
- Dokładnie 0% albo 100% czegokolwiek (np. 0 odrzuceń przez bramkę) — może być prawdziwe
  (S1 na 4h: geometria naprawiona), ale trzeba to wyjaśnić, nie przemilczeć.
- **Wynik idealnie potwierdza hipotezę.** Rzeczywistość jest brudniejsza. Szukaj przecieku
  (wzorzec: Z17 — „bliskość istotności" była artefaktem early stoppingu).
- Identyczne wartości w dwóch reżimach/foldach — skrypt ignoruje jakiś wymiar.
- Sweep seedów daje std = 0 — XGBoost bez subsamplingu jest deterministyczny, sweep nic nie
  mierzy (C2.9). Nigdy nie cytuj tego jako „stabilności".

### A5. Werdykt — co wpisać do README

| Werdykt | Znaczenie | Co dopisać |
|---|---|---|
| **Ready** | Metoda w porządku, liczby sprawdzone, zastrzeżenia nazwane. Drobne sugestie, nic blokującego. | Zdanie: „Walidacja (16a): Ready — przeliczono X drugą drogą, zgodność do N miejsc." |
| **Caveats** | Wynik prawidłowy, ale obowiązuje z ograniczeniem, które czytelnik MUSI znać. | Lista zastrzeżeń numerowana, każde jednym zdaniem + wpływ na wniosek. (Wzorzec: S1 — 6,95% historii.) |
| **Revision** | Znaleziono błąd, złą metodę albo brakujący pomiar. | Lista poprawek z priorytetem. Nie publikuj wniosku, dopóki nie naprawione. |

### A6. Kontrola negatywna — nowy silnik albo nowy przyrząd (od NC1, 2026-09-24)

**Kiedy obowiązkowa:** runda wprowadza NOWY silnik pomiaru (nowy `portfolio`/`*_returns`, nowy
model, nowy sposób liczenia zwrotu) albo zmienia istniejący w miejscu, które dotyka rachuby
zwrotów, wag lub dat. Nie dotyczy rund, które tylko podają inny sygnał do przetestowanego silnika.

**Co zrobić:** uruchomić silnik na danych BEZ informacji o przyszłości z
`backtest/negative_control.py` (`synthetic_returns`: t-Student df 3, GARCH, czynnik rynkowy —
wygląda jak krypto, ale kierunku nie da się przewidzieć) i sprawdzić, że wynik brutto ≈ 0:
|średnie t| < 0,5 na ≥ 20 losowaniach, |t| > 1,96 w ~5 % losowań (dwumian), netto ≤ brutto.
Do tego **kontrola czułości:** ten sam silnik z celowym zajrzeniem w przyszłość MUSI dać
ogromne t — inaczej kontrola negatywna jest ślepa. Wzorzec: `backtest/run_negative_control_nc1.py`
i test `tests/test_negative_control.py::test_trend_engine_finds_nothing_on_noise`.

**Dlaczego:** kontrola pozytywna (K1: wyrocznia) mówi, że przyrząd WIDZI sygnał; negatywna —
że nie WYMYŚLA go z szumu. W projekcie SIGMA brak tej drugiej przepuścił AUC 0,84, które
pochodziło z etykiety liczonej z przyszłego wskaźnika (przegląd w
`docs/rag/Repo lessons i sigma — co przydatne dla alpha.md`, wytyczna 2). Na losowym spacerze
takie AUC spada do 0,5 tylko wtedy, gdy etykieta jest uczciwa — dlatego test na szumie wyłapuje
przeciek, którego nie widać na prawdziwych danych.

**Uwaga — szum musi mieć grube ogony i grupowanie zmienności.** Gaussowski szum bez GARCH jest
za łagodny: nie odtwarza sytuacji, w których silnik może się „zachłysnąć” (skoki > 20 %
dziennie, długie nerwowe okresy, skalowanie zmiennością). Stąd df = 3 i GARCH w generatorze.

---

## B. Standard raportowania statystyk (zasada 16b)

Cel: liczba w raporcie ma mówić prawdę o niepewności i o tym, co z niej wynika dla decyzji.
Nie sama wartość, tylko wartość + zakres + znaczenie.

### B1. Środek i rozrzut — którą miarę wybrać

| Sytuacja | Użyj | Dlaczego |
|---|---|---|
| Zwroty per transakcja | **mediana I średnia** obok siebie | Zwroty są skośne (kilka dużych strat/zysków ciągnie średnią). Rozjazd między nimi mówi, jak bardzo. |
| Trafność (0/1 per transakcja) | udział + CI Walda | To proporcja — mediana nie ma sensu. |
| Rozrzut zwrotów | **IQR** (rozstęp ćwiartkowy — między 25. a 75. percentylem) obok std | Std jest wrażliwe na ogony; IQR nie. |
| Porównanie rozrzutu między reżimami | CV = std / średnia | Skale się różnią. |

Przy per-trade PnL warto podać percentyle p5 / p50 / p95 — pokazują, jak wygląda typowa
transakcja i jak wygląda ogon. Jedna średnia to za mało.

### B2. Efekt + przedział, nie samo p/z

**Przedział ufności** (CI — zakres, w którym z 95% pewnością leży prawdziwa wartość) jest
obowiązkowy przy każdej trafności i każdym marginesie. Sam z-score albo p-value mówi tylko
„różni się od zera czy nie" — nie mówi, o ile.

Źle: „trafność 48,6%, z = −0,90, nieistotne."
Dobrze: „trafność 48,6% (CI 45,6–51,6%) przy progu opłacalności 53,1% — nawet górny kraniec
przedziału nie sięga progu, czyli strategia trafia za rzadko, żeby pokryć koszty."

Zakresy zamiast fałszywej precyzji: „około 48–49%", nie „48,6017%". Zaokrąglaj do 0,1 pp w
tekście; pełna precyzja zostaje w tabeli i `raw_output.txt`.

### B3. Istotność statystyczna ≠ znaczenie praktyczne

Przy dużej próbie nawet 0,3 pp różnicy wyjdzie „istotne". Zawsze podaj:

- **Wielkość efektu** — o ile pp trafność przekracza (albo nie) próg opłacalności.
- **Przedział** — patrz B2.
- **Znaczenie dla decyzji** — czy to zmienia werdykt GO/WARUNKOWY/NO-GO; czy margines jest
  dodatni z zapasem, czy tylko formalnie.

W tym projekcie „istotne" znaczy: **dolny kraniec CI trafności > break-even ORAZ średni zwrot
netto per trade dodatni (pooled `t_stat > 0`)**. Nic innego.

**Dlaczego dwa warunki, nie jeden (W1b, 2026-09-23):** próg `break_even = 0,5·(1 + C/B)` zakłada,
że wygrana i przegrana są tej samej wielkości (±B). Gdy wejście jest oddalone od kotwicy etykiety
(limit na cofnięciu), wygrane rozjeżdżają się na małe (timeout tuż nad wejściem, +0,17 % ceny)
i pełne (TP), a straty zostają pełne (SL −2,45 %). Trafność wyszła 53,15 % przy progu 52,81 %,
a średni zwrot netto był istotnie UJEMNY (t = −3,90). **Więcej wygranych ≠ więcej pieniędzy.**
Każda pre-rejestracja wpisuje oba warunki do kryterium POZYTYWNEGO; przy wypłatach
asymetrycznych z definicji (częściowe TP, trailing) werdykt opiera się na zwrocie netto z CI.

### B4. Wielkość próby i moc — PRZED eksperymentem

- Rachunek mocy (ile transakcji trzeba, żeby wykryć efekt danej wielkości) robi się przed
  uruchomieniem, nie po (Z19: `required_trades`, `min_detectable_hit_rate` w `metrics.py`).
- **N_eff** — efektywna liczba niezależnych obserwacji. Transakcje po sobie są skorelowane,
  więc realna próba jest mniejsza (S1: 1037 transakcji → N_eff 620, czyli −40%). Raportuj
  `t_stat_neff` obok `t_stat`.
- Mała próba = powiedz to wprost: „przy n = 345 wykrywamy tylko efekty > X pp; wynik
  nierozstrzygalny".

### B5. Wielokrotne testowanie

Każdy wariant przetestowany na tych samych danych to losowanie — przy 20 wariantach jeden
„wygra" przypadkiem. Dlatego:

- **Licznik wariantów** w `runs/INDEX.md` to jawna księga tego ryzyka. Każda runda go
  aktualizuje.
- Przy k wariantach oczekuj ~k × 5% fałszywych „sukcesów". Przy 10 wariantach na starej bazie
  jeden pozorny sukces byłby normą, nie sygnałem.
- Reguła STOP i pre-rejestracja (kryterium zapisane PRZED wynikiem) to nasza obrona. Bez
  pre-rejestracji wynik pozytywny nie jest dowodem.
- Nie wybieraj okna czasowego po obejrzeniu wyniku. Fold-jitter (przesunięcie granic foldów
  o 0–9 dni, C2.9) sprawdza, czy wynik nie zależy od arbitralnego podziału.

### B6. Pułapki interpretacji

- **Korelacja ≠ przyczyna.** C2.7: 17 cech, 34 korelacje z targetem, |corr| < 0,065 — to
  screening, nie dowód. Nawet gdyby coś wyszło, byłoby kandydatem do testu OOS, nie wynikiem.
- **Paradoks Simpsona** — wynik zagregowany może odwracać się per reżim/per okres. Zawsze
  pokaż rozbicie per reżim (docs/rag/03: osobno niska zmienność 2023 vs era ETF 2024–25).
- **Survivorship** — patrz A2.
- **Przeciek z przyszłości (look-ahead)** — na trzech poziomach: cecha (test shift-forward),
  model (early stopping na foldzie testowym — Z17), podział (brak embarga na granicy
  train/test — Z21). Test leakage per cecha łapie TYLKO pierwszy poziom.
- **Cherry-picking okresu** — wynik na 6,8 roku i wynik na najlepszym roku to dwa różne
  twierdzenia. Raportuj cały zakres.

### B6a. Wytyczne z przeglądu SIGMA (2026-09-24) — gdzie mieszkają

Przegląd drugiego projektu użytkownika (QuantConnect, `docs/rag/Repo lessons i sigma — co
przydatne dla alpha.md`) dał siedem wytycznych. Mapowanie na nasze bramki:

| # | Wytyczna | Gdzie u nas |
|---|---|---|
| 1 | Etykieta tylko z przyszłej CENY, nigdy z przyszłego wygładzonego wskaźnika | C1 (pierwszy punkt) |
| 2 | Kontrola negatywna na losowych danych z grubymi ogonami | A6 |
| 3 | Parametry etykiety i kryterium w pre-rejestracji; nie nagradzać samego wysokiego AUC/trafności | niżej + B3 |
| 4 | Zbiór testowy użyty raz | niżej |
| 5 | Minimalna liczba transakcji / N_eff przed werdyktem | B4, zasada 18 |
| 6 | Przewaga = dodatni wynik PO kosztach z przedziałem | B2, B3 (dwa warunki) |
| 7 | Człowiek zatwierdza zmiany, bez automatycznego wdrożenia | CLAUDE.md, „Podział ról” |

- **(3) Wysoka miara jakości modelu to sygnał alarmowy, nie sukces.** AUC 0,84 albo trafność
  > 60 % na dziennych/4h danych krypto jest mało prawdopodobne; najpierw szukaj przecieku
  (A4, A6). Parametry etykiety (bariery, horyzont, wygładzanie) zapisuje się w pre-rejestracji
  i nie zmienia po obejrzeniu wyniku — bramka nagradzająca wysokie AUC sama wybiera etykietę
  z przeciekiem.
- **(4) Zbiór testowy użyty raz.** Okres „poza próbą” (np. TP1: lipiec–wrzesień 2026) po
  jednym odczycie staje się próbą — kolejna reguła sprawdzana na tym samym okresie nie jest
  już testem poza próbą. Zapisuj w README, który okres został „zużyty”.
- **Dla rund opisowych o ryzyku (sizing, dźwignia):** obok maksymalnego obsunięcia podawaj
  historyczny Expected Shortfall (średnia z 5 % najgorszych dni) i rozrzut z losowania
  ścieżki (Monte Carlo/bootstrap bloków) — jedna historyczna ścieżka to jedna realizacja
  (wskazówka Tokenomii z tego samego przeglądu).

### B7. Język liczb (zasada 17)

Każda kluczowa liczba w rozmowie i w sekcjach *Wniosek*/*Rekomendacja* dostaje tłumaczenie:

> „margines −4,5 pp" → „strategia trafia o 4,5 punktu procentowego rzadziej, niż musiałaby,
> żeby wyjść na zero po kosztach"

> „N_eff = 620 z 1037" → „transakcje są ze sobą powiązane, więc realnie mamy tyle informacji,
> ile z 620 niezależnych, nie 1037 — przedział ufności jest przez to szerszy"

Pełne tabele i wzory zostają w sekcjach technicznych — prosty język je tłumaczy, nie zastępuje.

---

## C. Przegląd kodu przed merge (zasada 16c)

Cel: zanim gałąź rundy trafi do master, ktoś (Claude w innej roli albo użytkownik) patrzy na
diff pod kątem czterech rzeczy: poprawność, testy, spójność z zasadami, czytelność. Efekt:
**werdykt jednym zdaniem w README rundy**.

### C1. Poprawność — pytania specyficzne dla CLAS-5

- **Etykieta tylko z przyszłej CENY (SIGMA, wytyczna 1).** Target/etykieta liczona z
  przyszłego zwrotu, przyszłego high/low albo barier na cenie — tak. Z PRZYSZŁEJ wartości
  wygładzonego wskaźnika (ADX, średnia, RSI za k świec) — nie: wskaźnik wygładzony w chwili
  t + k zawiera ceny z okna, które częściowo nakłada się na cechy z chwili t, więc model
  „przewiduje” coś, co w dużej części już widzi. SIGMA: AUC 0,84 z etykiety „przyszły ADX”.
- **Przeciek na poziomie cechy.** Nowa funkcja `compute_*` liczy tylko z danych do świecy t
  włącznie? Rolling window jest trailing (kończy się na bieżącej świecy), nigdy centered?
  Jest test w `agent_5_compliance/test_leakage.py`?
- **Przeciek na poziomie modelu.** Early stopping używa `validation_fraction` z ogona zbioru
  treningowego, nie foldu testowego (Z17). Guard na `best_iteration` obecny.
- **Przeciek na poziomie podziału.** `embargo_candles` = V (horyzont etykiety) na granicy
  train/test (Z21/Z22). Domyślne `None` wiąże embargo z V automatycznie — nie nadpisuj.
- **Spójność geometrii.** Mnożnik ATR w barierze = mnożnik w stop-lossie (zasada 3). Zmiana
  jednego bez drugiego = błąd, nawet jeśli testy przechodzą.
- **Determinizm.** Seed jawnie ustawiony i zalogowany. Dwa uruchomienia = ten sam wynik do
  ostatniej cyfry.
- **Brzegi.** Fold z 0 lub 1 transakcją nie wywala się i nie produkuje inf. Reżim bez świec
  zwraca NaN, nie 0 (0 wygląda jak wynik). Rozgrzewka wskaźników nie wchodzi do mianownika.
- **Off-by-one.** Bariera pionowa: V świec od wejścia — 12 czy 13? Etykieta ostatnich V świec
  zbioru treningowego sięga w test — czy embargo to obejmuje?
- **Strefa czasowa.** Wszystko w UTC; nowe źródło danych (np. funding rate) ma ten sam
  znacznik czasu co świece.
- **Wolumen po resample.** Nigdy nie resampluj z 5m do 1h/4h — użyj natywnych świec (Z9).

### C2. Zasady projektu, których diff nie może złamać

- Skrypty historyczne w `backtest/` **zamrożone** (zasada 13) — diff ich nie dotyka. Nowy
  skrypt buduje na `checkpoint_lib.py`.
- Żadnych magic numbers — nowy parametr trafia do `config/settings.yaml` albo
  `feature_registry.yaml` z komentarzem „wartość startowa, do kalibracji".
- Nowa cecha → wpis w `feature_registry.yaml` (wzór, źródło, rola, ryzyko leakage) + test
  spójności registry↔kod.
- Kryteria GO/WARUNKOWY/NO-GO z docs/rag/03 niezmienione — nowe miary to diagnostyka obok
  werdyktu, nie nowy werdykt.

### C3. Testy

- [ ] `pytest` zielony w całości (nie tylko nowe testy).
- [ ] Nowa cecha → test leakage PRZED wejściem do modelu (zasada 2).
- [ ] Zmiana w `labeling.py` / `risk_controller.py` → co najmniej jedna właściwość w
  `hypothesis` (zasada 10).
- [ ] Naprawa buga → test, który **przed** naprawą padał, a **po** przechodzi. (Wzorzec Z17:
  test „próg z train, nie z test".)
- [ ] Test nie jest tautologią (nie sprawdza, że funkcja zwraca to, co zwraca).

### C4. Wydajność — tylko gdy dotyczy

Walk-forward na 315 tys. świec × 85 foldów: pętla w Pythonie po świecach to minuty zamiast
sekund. Sprawdź: operacje wektorowe (pandas/numpy) w hot-pathie; brak O(n²) po świecach; brak
ponownego liczenia cech per fold, jeśli można raz. Nie optymalizuj na zapas — tylko gdy runda
realnie czeka.

### C5. Czytelność i utrzymanie

- Docstring = co liczy + wzór + skąd (biblioteka/artykuł/repo), nie tylko „liczy X".
- Type hints, `from __future__ import annotations`.
- Nazwy mówią, co jest czym: `hit_rate_barrier` vs `hit_rate_timeout`, nie `hr1`/`hr2`.
- Jedna odpowiedzialność na funkcję. Jeśli funkcja liczy i drukuje — rozdziel.
- Duplikacja: ta sama liczba w dwóch miejscach = jedna stała importowana w obu.
- `ruff` + `black` przeszły na plikach dotykanych.

### C6. Bezpieczeństwo — minimum dla tego repo

Kluczy API nie ma w repo (env/`.gitignore`). Żadnych `eval`/`exec` na danych z zewnątrz.
`.claude/settings.json` i inne artefakty narzędzi nie wchodzą do commitów.

### C7. Format werdyktu

Krótko, do README rundy:

```
Przegląd diffu (16c): [Approve | Request changes | Needs discussion] —
<jedno zdanie: co sprawdzono, co znaleziono>.
```

Jeśli *Request changes* — lista: plik, linia, problem, waga (krytyczny / sugestia). Krytyczne
blokują merge. Sugestie można odłożyć do backlogu z numerem Z.

---

## Jak tego używać w praktyce

1. Przy końcu rundy otwórz ten plik i przejdź sekcję **A** po kolei. Wpisz werdykt do README.
2. Pisząc tabelę wyników i wnioski — sekcja **B**, zwłaszcza B2 (przedziały) i B7 (język).
3. Przed merge — sekcja **C**, wpisz werdykt jednym zdaniem.
4. Skille `data:validate-data` (A), `data:statistical-analysis` (B) i `engineering:code-review`
   (C) są od 2026-09-23 OBOWIĄZKOWE w swoich momentach (`CLAUDE.md` zasada 19) — dają
   dodatkowe listy ogólne, a ich użycie widać w rejestrze `runs/skille/<gałąź>.jsonl`. Ten plik
   pozostaje wersją dopasowaną do projektu i ma pierwszeństwo tam, gdzie się różnią.

Ten plik aktualizuj, gdy runda odkryje nową pułapkę (tak jak C2d, Z17, S1 trafiły tutaj) —
to żywa lista, nie stała.
