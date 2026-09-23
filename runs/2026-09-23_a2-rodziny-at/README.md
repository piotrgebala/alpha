# A2 — pozostałe rodziny analizy technicznej jako reguły szukania pozycji (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Kod cech i reguł (`agents/ta_rules.py`, testy,
> rejestr) powstał PRZED tą pre-rejestracją, bo był potrzebny do ZLICZENIA częstości sygnałów
> (rachunek mocy) — **żaden wynik transakcji nie był oglądany**. Skrypt pomiaru i przebieg
> następują PO commicie tego pliku (kolejność dowodliwa z gita). Sekcje od „Wynik" w dół
> dopisuje się po przebiegu. Decyzja użytkownika 2026-09-23: „wykonaj" — pozostałe rodziny AT
> ze skilla `ta-toolkit`, każda z osobną pre-rejestracją i rachunkiem mocy.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Pytanie:** czy klasyczne narzędzia analizy technicznej z podręcznika — struktura trendu
(coraz wyższe szczyty i dołki), wybicie z zakresu, podwójny szczyt/dno, głowa z ramionami,
przecięcie średnich, przełamanie linii trendu, zniesienia Fibonacciego, strefy wsparcia i oporu —
użyte dokładnie tak, jak uczy podręcznik, wskazują na BTC 4h pozycje, które po kosztach
zarabiają?

**Jak sprawdzamy:** każde narzędzie zamieniamy na deterministyczną regułę (bez „rysowania na
oko"; parametry takie, jak w skillu — jeden zestaw, bez dobierania) i sprawdzamy na tych samych
świecach, na których działa dotychczasowy model (dane od 2021). Reguła mówi „long" albo „short"
albo nic; wejście po cenie zamknięcia, stop i cel jak dotąd, limit 12 h.

**Rachunek mocy PRZED pomiarem zadecydował, co da się zmierzyć:**
- Trzy reguły „stanowe" (sygnał trwa, dopóki trwa warunek) dają tysiące transakcji —
  **mierzone osobno**: struktura trendu, zniesienie Fibonacciego, wsparcie/opór.
- Pięć reguł „zdarzeniowych" (sygnał tylko w świecy, w której formacja się domyka) daje od 85
  (głowa z ramionami) do 982 (wybicie) sygnałów na 5,5 roku — **każda osobno jest
  niemierzalna**: nawet gdyby trafiała w 56 %, przedział ufności byłby za szeroki, żeby to
  odróżnić od monety. Zgodnie z zasadą 18 osobno nie startują. **Razem, jako jedna grupa
  „zdarzenia AT"**, dają 2 174 sygnały i są mierzalne — werdykt będzie dotyczył grupy.
- Piąte ramię: **wszystkie dziesięć cech AT naraz jako dodatkowe cechy modelu** (test rodziny
  z `docs/rag/02`), kontrola = model bez nich.

**Czego się spodziewamy (przed wynikiem):** około 50 % dla wszystkich, jak we wszystkich rundach
na cenie i wolumenie; dla reguł „graj z ruchem" (struktura trendu, wybicie) nawet poniżej —
A1 (objęcie) i W1c (wejście na wybiciu, 46,1 %) pokazały, że na 4h BTC duży ruch częściej
zawraca. Jedyna reguła z wiarygodnym mechanizmem to wsparcie/opór (skupienie zleceń na
pamiętanych poziomach) — ale jej deterministyczna wersja ma pułapkę zapisaną niżej.

**Pięć ramion naraz = pięć losów.** Żeby wynik „pozytywny" nie był wygraną na loterii,
próg dla pozytywu jest surowszy (korekta Bonferroniego, opisana niżej).

---

## ID testu

**A2** — seria A (analiza techniczna), ramiona **A2.1** struktura trendu, **A2.2** zniesienie
Fibonacciego, **A2.3** wsparcie/opór, **A2.4** grupa zdarzeń (wybicie + podwójny szczyt/dno +
głowa z ramionami + przecięcie EMA + przełamanie linii trendu), **A2.5** model + 10 cech AT.
Licznik serii A po tej rundzie: **2 (A1) + 5 = 7**; każda rodzina AT ze skilla zamknięta regułą
STOP (niżej). Kontrola za 0.

## Metadane

- **Gałąź:** `a2-rodziny-at` (od master `5e3d0d0`).
- **Dane:** BTC/USDT perpetual, 4h natywne z cache, **od 2021-01-01** (zasada 20): 12 042 świece;
  okna OOS jak w N1/A1: 69 okien walk-forward 60/28/28, 11 592 świece OOS.
- **Pipeline (wspólny z A1/N1):** bez bramki reżimu, etykieta ±1,5·ATR, V = 3 (12 h), wagi klas
  `balanced`, seed 42, wykonanie `path`: limit po `close` k = 1, pojedyncze wyjście, model kosztów
  `maker_limit`, sizing 0,5 % / dźwignia ≤ 3×, kill-switch jak dotąd.
- **Kod:** `agents/ta_rules.py` (10 cech ze skilla + 8 reguł + grupa zdarzeń; parametry domyślne
  skilla), sekcja `ta_rules:` w `agents/feature_registry.yaml`, test przecieku parametryzowany
  po `TA_FEATURE_FUNCTIONS` (zasada 2 — zielony PRZED pomiarem), `tests/test_ta_rules.py`.
  Sygnały reguł: `checkpoint_lib.build_rule_signals` (populacja = okna OOS modelu, bramka
  kosztowa silnika). Skrypt rundy `backtest/run_ta_rules_a2.py` powstaje PO tej pre-rejestracji;
  komenda trafi tu przy zamknięciu razem z wpisem na `runs/ZAMROZONE.txt`.

## Poprzedzające wyniki (zasada 14)

- **A1 (wnioski 48–50):** formacje świecowe jako reguła 46,35 % [44,38; 48,31] — kierunek
  odwrotny do podręcznika; jako cecha modelu 0; rachunek mocy z częstości zdarzenia trafił do
  2 %; N_eff ≤ n; odwrócenie znaku po wyniku = hipoteza post hoc.
- **W1c (wniosek 44):** wejście stop na wybiciu 46,13 % [44,55; 47,72] — kupno na lokalnym
  szczycie, po którym cena częściej zawraca. Prior dla reguł „z ruchem" (wybicie, struktura
  trendu) jest przez to poniżej 50 %, nie tylko „przy 50 %".
- **M1 (wniosek 35):** cechy momentum w modelu 49,74 % — ta sama informacja co struktura trendu
  i wybicie, inna formuła (model vs reguła). Nie powtórka co do wariantu, ale ten sam zbiór
  informacyjny (wniosek 11).
- **Faza 0:** reżim `trend` (ATR-percentyl + persystencja) był FILTREM zagładzającym próbę
  (wniosek 20), nie sygnałem kierunkowym; `ema_diff_9_21` była cechą modelu (C2.7: skorelowana
  0,87 z `rsi_14`). Przecięcie EMA 10/30 jako zdarzenie to inna formuła i inne okna — jeden
  zestaw, bez wariantów (pięć par okien = pięć losów, `ta-toolkit` §5).
- **N1/W1 (wnioski 42–46):** kontrola na bazie 2021+: p 49,58 % [48,39; 50,77], zwrot netto
  −0,107 % [−0,149; −0,065], próg ±B 53,07 % — odniesienie (0 wariantów).
- **`ta-toolkit` evidence:** BLL 1992 vs STW 1999 (średnie kroczące: efekt znika po korekcie na
  snooping), LMW 2000 (formacje: informacja ≠ zysk), brak literatury z edge'em dla linii trendu
  i Fibonacciego; wsparcie/opór — mechanizm wiarygodny, niezmierzone.

## Rozstrzygnięcia projektowe (zapisane PRZED przebiegiem)

### Pięć pól katalogu (wspólne dla ramion A2.1–A2.4; A2.5 = rodzina A4 katalogu)

| pole | wartość | uwaga |
|---|---|---|
| zbiór informacyjny | OHLCV własne (BTC) | ten sam co Faza 0 → prior niski |
| formuła | jednoaktywowa, reguła bez modelu (A2.1–A2.4) / XGBoost (A2.5) | |
| target | kierunek (±1,5·ATR, 12 h) | bez zmian (zasada 3) |
| horyzont | intraday 4h / 12 h | |
| status | NIETKNIĘTE (rodzina A5 katalogu, poza formacjami świecowymi) | |

### Wspólne dla wszystkich ramion regułowych

- **Populacja:** dokładnie świece OOS pipeline'u modelowego (jak A1a), etykieta i ATR nie-NaN,
  bramka kosztowa silnika. Sygnał w świecy `t` używa wyłącznie barów ≤ t (swingi POTWIERDZONE
  `confirm = 5` barów po ekstremum — test przecieku). Wejście od świecy t + 1.
- **Sizing:** `signal_confidence = 1,0`; sygnały stanowe dają nakładające się pozycje z kolejnych
  świec — każda sizowana niezależnie; N_eff (≤ n) koryguje autokorelację.
- **Parametry:** domyślne skilla (`confirm=5`, `tol_atr=0,5`, `bounce_atr=2`, ramiona RGR
  `1,0/1,0` ATR, EMA `10/30`, regresja przez `k=3` dołki, `lookback=500`, wybicie `n=20`,
  pasmo Fibonacciego `0,382–0,618`, „przy poziomie" = `|d| ≤ 0,5·ATR`). Jeden zestaw — żadnych
  wariantów; każdy inny zestaw byłby osobnym wariantem w liczniku.

### A2.1 — struktura trendu HH/HL (STAN)

- **Reguła:** `trend_structure = +1` (dwa ostatnie potwierdzone szczyty rosną I dołki rosną) →
  long w każdej takiej świecy; `−1` (LH+LL) → short; 0 → nic. Podręcznik: „graj z trendem".
- **Mechanizm (deklarowany):** opóźniona reakcja / herding — trend trwa. Kontr-prior: M1, W1c, A1.
- **Powtórka?** Nie co do wariantu (reguła vs model, inne wejście); ten sam zbiór informacyjny.
- **Częstość (OOS, 11 682 świece):** 6 847 sygnałów (58,6 % świec; long 3 620, short 3 227)
  w **412 epizodach** o średniej długości 16,6 świecy.
- **Mierzalność:** `expected_trades(6 847; 0; 0,994) = 6 806`; half-width 1,19 pp;
  `p_detectable` 54,26 % → dla zakładanej 56 % **MIERZALNA**. Zastrzeżenie zapisane z góry:
  sygnały w epizodzie nakładają się (horyzont 3 świece), więc N_eff będzie znacznie niższe niż n —
  dolna granica jednostek niezależnych to 412 epizodów (half-width 4,83 pp). Werdykt liczy się
  na `t_neff`, nie na n.

### A2.2 — zniesienie Fibonacciego (STAN)

- **Reguła:** `fib_position ∈ [0,382; 0,618]` (close w paśmie zniesienia ostatniego potwierdzonego
  impulsu) → kierunek = kierunek impulsu (wzrostowy → long, spadkowy → short). Podręcznik:
  „korekta do 38–62 % i powrót do impulsu".
- **Mechanizm (deklarowany):** punkt skupienia zleceń (self-fulfilling); brak innego mechanizmu
  (`evidence.md` §4). Jeśli działa, to jako „pamiętany poziom", nie jako złoty podział.
- **Częstość:** 2 281 sygnałów (19,5 %; long 1 076, short 1 205) w 1 058 epizodach (śr. 2,2).
- **Mierzalność:** n ex ante 2 267; half-width 2,06 pp; `p_detectable` 55,13 % → **MIERZALNA**.

### A2.3 — strefy wsparcia i oporu (STAN)

- **Reguła:** `sr_distance = (close − najbliższy potwierdzony poziom z 500 barów)/ATR`;
  `|d| ≤ 0,5` → „przy poziomie": cena NAD poziomem (wsparcie) → long, POD (opór) → short.
  Podręcznik: „odbicie od strefy, odwrócenie biegunowości".
- **Mechanizm:** skupienie zleceń limit na pamiętanych poziomach — jedyny w tej rundzie
  wiarygodny mechanizm ekonomiczny (`ta-toolkit` concepts §8).
- **Pułapka zapisana z góry:** przy `lookback = 500` i `confirm = 5` zbiór poziomów jest gęsty
  (dziesiątki poziomów), więc cena jest „przy poziomie" w **82,7 % świec** — reguła degeneruje
  do „strona najbliższego poziomu", nie „odbicie od wyróżnionej strefy". To jest wynik
  deterministycznej wersji z parametrami skilla; runda mierzy TĘ wersję. Zawężanie `τ`,
  `lookback` albo „poziomy dotknięte ≥ 2 razy" po wyniku = nowe warianty (STOP).
- **Częstość:** 9 664 sygnały (82,7 %; long 4 816, short 4 848), 4 801 epizodów (śr. 2,0).
- **Mierzalność:** n ex ante 9 606; half-width 1,00 pp; `p_detectable` 54,07 % → **MIERZALNA**.

### A2.4 — grupa zdarzeń AT (ZDARZENIA: sign sumy pięciu reguł)

Pięć reguł zdarzeniowych, każda jako sygnał tylko w świecy domknięcia:

| reguła | definicja | sygnały OOS | n ex ante | half-width | p_detectable | osobno |
|---|---|---|---|---|---|---|
| wybicie z zakresu | close poza max/min 20 barów (bez bieżącego) → kierunek wybicia | 988 | 982 | 3,13 pp | 56,20 % | **NIEMIERZALNA** (−0,20 pp) |
| podwójny szczyt/dno | potwierdzenie formacji (tolerancja 0,5·ATR, odbicie ≥ 2·ATR) → dno long / szczyt short | 305 | 303 | 5,63 pp | 58,70 % | NIEMIERZALNA |
| głowa z ramionami | potwierdzenie RGR → short / odwróconej → long | 86 | 85 | 10,63 pp | 63,70 % | NIEMIERZALNA |
| przecięcie EMA 10/30 | świeże przecięcie (wiek 0) → znak (EMA10 − EMA30) | 434 | 431 | 4,72 pp | 57,79 % | NIEMIERZALNA |
| przełamanie linii trendu | zmiana znaku (close − linia przez 3 dołki) → nowy znak | 710 | 706 | 3,69 pp | 56,76 % | NIEMIERZALNA |

**Żadna z nich nie startuje osobno (zasada 18)** — ich wynik nie rozstrzygnąłby niczego
niezależnie od tego, co by wyszło. Wybicie przegrywa o 0,20 pp i to jest granica, którą
uznajemy, nie negocjujemy.

- **Reguła grupowa:** `sign(Σ pięciu sygnałów)`, konflikt → 0 — dokładnie tak jak `cdl_score_6`
  w A1 (test rodziny, `docs/rag/02`). Werdykt dotyczy GRUPY „zdarzenia AT z podręcznika";
  rozbicie per reguła w wyniku jest wyłącznie opisowe.
- **Częstość:** świece z ≥ 1 zdarzeniem 2 204, konflikty 17 → **2 187 sygnałów** (long 1 183,
  short 1 004).
- **Mierzalność:** n ex ante 2 174; half-width 2,10 pp; `p_detectable` 55,17 % → **MIERZALNA**.
- **Powtórka?** Wybicie ≈ W1c (stop na wybiciu jako WEJŚCIE do sygnału modelu; tu wybicie jest
  samym sygnałem) — nie ten sam wariant, ten sam prior (46,1 %).

### A2.5 — model + wszystkie cechy AT (test rodziny cech)

- **Jedna zmienna:** zestaw cech = `REVERSION_FEATURES + 10 cech z ta_rules` (14 zamiast 4);
  wszystko inne = kontrola (te same okna, wagi klas, wejście). Jak A1b, ale dla całej rodziny
  naraz — `docs/rag/02` dopuszcza test grupowy zamiast dziesięciu osobnych (kontrola multiple
  comparisons). Cechy mają 0 NaN w oknie OOS (sprawdzone), więc populacja modelu nie zmaleje.
- **Mierzalność:** jak A1b — `expected_trades(11 592; 0,4038; 0,994) ≈ 6 870`; half-width
  1,18 pp; `p_detectable` 54,25 % → MIERZALNA. Porównanie parowane z kontrolą (obserwacja).

### Kryterium — zapisane PRZED uruchomieniem (pięć ramion → korekta Bonferroniego)

Statystyka nośna jak w A1: średni zwrot netto per transakcja `r̄` (% nominału) z CI i `t_neff`
(N_eff ≤ n), trafność `p` z CI Walda, próg uogólniony `p* = (L̄ + C)/(W̄ + L̄)`.

- **Pięć ramion pre-rejestrowanych naraz = pięć testów.** Dla werdyktu POZYTYWNEGO
  `z_5 = Φ⁻¹(1 − 0,025/5) = 2,576` zamiast 1,96 (Bonferroni, α = 0,05 dwustronnie na całą rundę).
- **POZYTYWNY (ramię):** `t_neff > 2,576` **i** `ci_low(p; z_5) > p*` (CI trafności liczone przy
  z = 2,576). → najpierw szukać przecieku, potem replikacja na ETH tą samą regułą.
- **NEGATYWNY (ramię):** `t_neff < −1,96` **i** `n ≥ required_trades(0,50; BE ramienia)`
  (ex ante 2 076 dla BE 53,07 %). Guard z funkcji, nie ze stałej. Bez korekty na m — negatyw
  jest wnioskiem konserwatywnym dla projektu; zapisane jawnie.
- **NIEROZSTRZYGNIĘTY:** wszystko inne (w tym trafność w paśmie [BE; p_detectable]).
- **Granica dużego n (zasada 18):** oba warunki monotoniczne w n; guard blokuje tylko negatyw na
  małej próbie; korekta Bonferroniego podnosi próg pozytywu, nie karze ramienia osiągającego cel.
- **Parowane A2.5 − kontrola** i **rozbicia** (per reguła w grupie, per kierunek, per powód
  wyjścia): obserwacje, nie kryteria.

### Reguła STOP serii A (po A2 obejmuje wszystkie rodziny ze skilla)

Po A2 **każda rodzina AT ze skilla `ta-toolkit` jest zamknięta** niezależnie od wyniku, chyba że
werdykt POZYTYWNY (→ replikacja na ETH bez retuningu). Zakazane: inne parametry (okna EMA, `τ`,
`lookback`, `confirm`, tolerancje, pasma), podzbiory grupy zdarzeń, filtry kontekstu
(„wybicie + trend", „S/O + formacja" — przecięcie zbiorów, n maleje geometrycznie), odwrócenie
znaku po wyniku (wniosek 49). Reguły NIEMIERZALNE osobno **nie zostały zmierzone** — nie
wracają na BTC 4h; ich test wymagałby innego interwału albo dłuższej historii (obie rzeczy =
nowa hipoteza z decyzją użytkownika, a zasada 20 wyklucza dłuższą historię).

### Arytmetyka oczekiwań

- Prior: p ≈ 50 % ± 2 pp dla wszystkich; dla A2.1 i wybicia w A2.4 raczej < 50 % (W1c 46,1 %,
  A1 objęcie 45,7 %: duży ruch na 4h BTC częściej zawraca). Oczekiwany werdykt: NEGATYWNY dla
  A2.3, A2.5 (n duże) i A2.1 (n duże, ale t_neff obcięte przez epizody — może NIEROZSTRZYGNIĘTY);
  NEGATYWNY lub NIEROZSTRZYGNIĘTY dla A2.2 i A2.4 (n ≈ 2 200: przy p ≈ 50 % t ≈ −2,3).
- **Red flag zapisany z góry:** pozytyw w którymkolwiek ramieniu → najpierw przeciek (swingi
  potwierdzone? `confirm` w regule identyczny z testem?), potem sprawdzenie, czy reguła nie jest
  równoważna czemuś zmierzonemu (np. A2.3 przy 83 % pokrycia ≈ „strona ostatniego swingu").
- A2.5: oczekiwanie jak A1b — różnica parowana w paśmie ±0,02 pp; XGBoost z 14 cechami na 60-dniowych
  oknach może szumieć bardziej (więcej cech, ta sama próba) — kierunek różnicy raczej ujemny.

### Czego runda NIE raportuje i NIE interpretuje

Werdyktów per reguła w grupie zdarzeń, per kierunek, per rok; „skuteczności" bez kosztów i
geometrii; porównań z rundami sprzed zasady 20; optymalizacji parametrów.

### Kogo NIE ma w zbiorze (zapisane z góry)

Pierwsze 60 dni (trening); świece bez sygnału danej reguły (A2.1: 41 %, A2.2: 80 %, A2.3: 17 %,
A2.4: 81 % świec OOS); pięć reguł zdarzeniowych osobno (niemierzalne — obecne tylko w grupie);
niewypełnione (~0,6 %); stłumione kill-switchem (raportowane per ramię); kolejność zdarzeń
w świecy 4h bez 5m (konserwatywnie).

## Definition of Done tej rundy

- Kod (już w repo, przed tym plikiem): `agents/ta_rules.py`, sekcja `ta_rules:` rejestru, testy
  jednostkowe + hypothesis + przeciek (42 zielone). Po pre-rejestracji: `backtest/run_ta_rules_a2.py`
  (neutralny reporter) — odczyt kryterium w skrypcie, werdykt podpisuje Claude w README.
- Regresja: kontrola w skrypcie = N1/A1 co do cyfry (n 6 789, p 49,58 %, r̄ −0,1069 %).
- Bramki 16a–c ze skillami na tej gałęzi; `raw_output.txt`; INDEX (wiersz, licznik A = 7, STOP
  wszystkich rodzin, wnioski); STATUS (seria A); README (kamień milowy); ZAMROZONE; „Użyte skille".

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz a2-rodziny-at`)_
