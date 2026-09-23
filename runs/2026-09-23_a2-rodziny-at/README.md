# A2 — pozostałe rodziny analizy technicznej jako reguły szukania pozycji (2026-09-23)

> **STATUS: ZAMKNIĘTA — TRZY RAMIONA NEGATYWNE, DWA NIEROZSTRZYGNIĘTE, ŻADNE POZYTYWNE.**
> Kolejność w gicie: kod cech i reguł `adfe13e` (potrzebny do zliczenia częstości; żaden wynik
> transakcji nie był liczony) → pre-rejestracja `f9805fa` → skrypt pomiaru `d80b621` → przebieg
> → wynik w commicie scalającym. **Seria A po A2: licznik 7/7 — wszystkie rodziny AT ze skilla
> `ta-toolkit` zamknięte regułą STOP.** Walidacja (16a): **READY**; przegląd diffu (16c):
> **Approve**. Decyzja użytkownika 2026-09-23: „wykonaj" — pozostałe rodziny AT.

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Żadne narzędzie klasycznej analizy technicznej z podręcznika nie znajduje na BTC 4h pozycji,
które po kosztach zarabiają.** Pięć ramion, jedna populacja świec (od 2021), ten sam sposób
wejścia i wyjścia co model:

| ramię | trafność | pieniądze na transakcji | werdykt |
|---|---|---|---|
| model bez AT (kontrola) | 49,6 % | −0,107 % | odniesienie |
| struktura trendu HH/HL („graj z trendem") | **48,2 %** [47,0; 49,4] | **−0,127 %** [−0,170; −0,084] | NEGATYWNY |
| zniesienie Fibonacciego 38–62 % | 51,5 % [49,4; 53,6] | −0,041 % [−0,110; +0,028] | nierozstrzygnięty |
| wsparcie/opór (przy poziomie, w stronę poziomu) | 49,9 % [48,9; 50,9] | **−0,080 %** [−0,114; −0,045] | NEGATYWNY |
| zdarzenia AT razem (wybicie, podwójny szczyt/dno, RGR, przecięcie EMA, linia trendu) | 48,3 % [46,2; 50,5] | −0,103 % [−0,182; −0,024] | nierozstrzygnięty (próba o 10 % za mała na „dowód braku") |
| model + wszystkie 10 cech AT | 49,6 % | −0,099 % [−0,141; −0,056] | NEGATYWNY; różnica wobec kontroli +0,005 % [−0,055; +0,066] |

**Co to znaczy:**
- **„Graj z trendem" traci najwięcej:** struktura wyższych szczytów i dołków trafia w 48,2 %,
  cały przedział poniżej rzutu monetą — jak w A1 (objęcie) i W1c (wybicie): na 4h BTC ruch
  częściej zawraca, niż trwa.
- **Wsparcie/opór** — jedyne narzędzie z wiarygodnym mechanizmem — w deterministycznej wersji
  z parametrami skilla daje sygnał w 83 % świec i trafia jak moneta. Pułapkę (gęsty zbiór
  poziomów) zapisaliśmy przed wynikiem; zawężanie parametrów po wyniku byłoby nowym losem.
- **Fibonacci** to jedyne ramię, którego nie da się nazwać: trafność 51,5 % z przedziałem
  obejmującym i monetę, i próg opłacalności (53,2 %), strata 0,04 % nieodróżnialna od zera.
  Przy 2 223 transakcjach to jest granica rozdzielczości, zapisana przed uruchomieniem.
- **Zdarzenia AT** (formacje domykane w jednej świecy) razem tracą istotnie (przedział poniżej
  zera), ale próba (2 133) nie sięga wymaganej do orzeczenia „dowodu braku" (2 366) — więc
  według litery pre-rejestracji: nierozstrzygnięte. Osobno żadna z pięciu reguł nie była mierzalna.
- **Model z dziesięcioma cechami AT** zmienia decyzje w 35 % świec i częściej milczy
  (abstynencja 40,4 → 42,7 %), a wynik ma taki sam. Więcej cech = więcej szumu, nie informacji.

**Bilans serii A (7 ramion, trzy rundy):** A1 formacje świecowe 46,4 %; A2 struktura trendu
48,2 %, S/O 49,9 %, Fibonacci 51,5 %, zdarzenia 48,3 %; jako cechy modelu dwa razy zero. Analiza
techniczna na 4h BTC jest zamknięta jako kierunek.

---

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
  kosztowa silnika). **Komenda:** `py -m backtest.run_ta_rules_a2` (Windows: `PYTHONUTF8=1`;
  pełny output `raw_output.txt`; skrypt na `runs/ZAMROZONE.txt`). Czas przebiegu: 8 s.

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

### 0. Dane i lejek

12 042 świece 4h od 2021-01-01, 69 okien, **11 592 świece OOS** dla każdego ramienia (parytet
populacji potwierdzony liczbą). Kontrola: abstynencja 40,38 %, 6 911 kandydatów (= N1/A1).
A2.5: abstynencja **42,70 %**, 6 642 kandydatów. Reguły (sygnały OOS → journal; niewypełnione /
stłumione kill-switchem): A2.1 6 778 → 6 423 (28 / **327**); A2.2 2 250 → 2 223 (15 / 12);
A2.3 9 602 → 9 204 (36 / **362**); A2.4 2 167 → 2 133 (13 / 21). Pięć reguł zdarzeniowych osobno:
zliczone (988 / 305 / 86 / 434 / 710), nie symulowane.

### 1. Kryterium (dwa warunki; pozytyw przy z_5 = 2,576)

| ramię | n | r̄ netto | CI 95 % | mediana | t | N_eff | t_neff | p | CI 95 % (p) | ci_low z_5 | p* | odczyt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kontrola | 6 789 | −0,107 % | [−0,149; −0,065] | −0,104 % | −5,01 | 4 919 | −4,26 | 49,58 % | [48,39; 50,77] | 48,02 % | 53,64 % | odniesienie (= N1/A1 co do cyfry) |
| **A2.1** struktura trendu | 6 423 | **−0,127 %** | [−0,170; −0,084] | −0,142 % | −5,83 | 2 875 | **−3,90** | **48,20 %** | [46,98; 49,42] | 46,60 % | 53,07 % | **NEGATYWNY** (n ≥ 1 959) |
| **A2.2** Fibonacci | 2 223 | −0,041 % | [−0,110; +0,028] | −0,052 % | −1,16 | 1 787 | −1,04 | 51,51 % | [49,43; 53,58] | 48,78 % | 53,18 % | **NIEROZSTRZYGNIĘTY** |
| **A2.3** wsparcie/opór | 9 204 | **−0,080 %** | [−0,114; −0,045] | −0,097 % | −4,52 | 7 300 | **−4,03** | 49,87 % | [48,85; 50,89] | 48,53 % | 53,01 % | **NEGATYWNY** (n ≥ 1 895) |
| **A2.4** grupa zdarzeń | 2 133 | −0,103 % | [−0,182; −0,024] | −0,142 % | −2,56 | 2 133 | −2,56 | 48,34 % | [46,21; 50,46] | 45,55 % | 52,00 % | **NIEROZSTRZYGNIĘTY** (guard n: 2 133 < 2 366) |
| **A2.5** model + 10 cech AT | 6 525 | **−0,099 %** | [−0,141; −0,056] | −0,098 % | −4,57 | 3 839 | **−3,51** | 49,59 % | [48,38; 50,81] | 48,00 % | 53,42 % | **NEGATYWNY** (n ≥ 1 949) |

Żadne ramię nie zbliża się do warunków pozytywu (`t_neff > 2,576` i `ci_low(p; z_5) > p*`):
najwyższy `ci_low z_5` to 48,78 % wobec p* 53,18 %. **Regresja kontroli wobec N1/A1: ZGODNA.**

**A2.4 wg litery:** kryterium negatywne wymaga `n ≥ required_trades(0,50; BE ramienia)`; BE grupy
wyszło niżej (52,88 %) niż ex ante (53,07 %), więc próg próby wzrósł do 2 366, a n = 2 133 jest
o 10 % za małe. Odczyt: NIEROZSTRZYGNIĘTY. Nie zmieniamy tego po fakcie — ale zapisujemy, że
zwrot netto grupy jest istotnie ujemny przy 1,96 (CI [−0,18; −0,02] poniżej zera): to nie jest
„brak informacji", tylko „za mała próba na formalny dowód braku".

### 2. Porównanie parowane A2.5 − kontrola (obserwacja)

Tylko **4 374** wspólnych transakcji (kontrola 6 789, A2.5 6 525): 2 415 tylko w kontroli, 2 151
tylko w A2.5, identycznych 2 867. Dziesięć dodatkowych cech zmienia decyzję modelu w ~35 % świec
i podnosi abstynencję o 2,3 pp. Średnia różnica na wspólnych: **+0,005 % [−0,055; +0,066]**,
t = 0,18 — zero; ramiona niezależnie: −0,107 % vs −0,099 %.

### 3. Opisowo — skąd biorą się pieniądze (bez werdyktów na podzbiorach)

| ramię / grupa | n | p | CI 95 % (p) | r̄ netto |
|---|---|---|---|---|
| A2.1 long / short | 3 425 / 2 998 | 48,23 % / 48,17 % | [46,6; 49,9] / [46,4; 50,0] | −0,171 % / −0,077 % |
| A2.1 timeouty (66,5 %) | 4 271 | 47,20 % | [45,70; 48,70] | −0,150 % |
| A2.2 long / short | 1 053 / 1 170 | 52,99 % / 50,17 % | [50,0; 56,0] / [47,3; 53,0] | −0,061 % / −0,023 % |
| A2.2 timeouty (70,4 %) | 1 564 | 51,47 % | [48,99; 53,95] | −0,084 % |
| A2.3 long / short | 4 568 / 4 636 | 50,53 % / 49,22 % | [49,1; 52,0] / [47,8; 50,7] | −0,089 % / −0,070 % |
| A2.4 timeouty (62,8 %) | 1 340 | 44,40 % | [41,74; 47,06] | −0,227 % |
| A2.4: wybicie z zakresu | 963 | 48,49 % | [45,34; 51,65] | −0,053 % |
| A2.4: podwójny szczyt/dno | 289 | 44,98 % | [39,25; 50,72] | −0,317 % |
| A2.4: głowa z ramionami | 82 | 47,56 % | [36,75; 58,37] | +0,013 % |
| A2.4: przecięcie EMA 10/30 | 415 | 43,61 % | [38,84; 48,39] | −0,122 % |
| A2.4: przełamanie linii trendu | 680 | 52,21 % | [48,45; 55,96] | −0,051 % |

Wszystkie ramiona regułowe mają stopy ≈ cele (A2.1 1 072 : 1 080; A2.3 1 496 : 1 560) i strata
siedzi w timeoutach (66–70 % transakcji, wygrane 44–51 %). W grupie zdarzeń pięć podgrup ma CI
szerokie na 6–22 pp; przecięcie EMA (43,6 %, CI pod 50 %) i linia trendu (52,2 %) to skrajne
z pięciu — oczekiwany rozrzut, bez werdyktów. W̄/L̄/C: A2.1 1,308/1,303/0,083 %; A2.2
1,225/1,217/0,082 %; A2.3 1,271/1,261/0,081 %; A2.4 1,430/1,381/0,081 %; A2.5 1,279/1,292/0,082 %.

### 4. Mierzalność — ex ante vs ex post

| ramię | n ex ante | journal | pasmo ex ante / ex post | required_trades | se → wykrywalny |r̄| |
|---|---|---|---|---|---|
| A2.1 | 6 806 | 6 423 (−5,6 %: 327 stłumionych) | 1,19 / 1,22 pp | 1 959 ✔ | 0,0218 % → 0,061 % |
| A2.2 | 2 267 | 2 223 | 2,06 / 2,08 pp | 1 759 ✔ | 0,0352 % → 0,099 % |
| A2.3 | 9 606 | 9 204 (−4,2 %: 362 stłumionych) | 1,00 / 1,02 pp | 1 895 ✔ | 0,0176 % → 0,049 % |
| A2.4 | 2 174 | 2 133 | 2,10 / 2,12 pp | 2 366 ✗ | 0,0402 % → 0,113 % |
| A2.5 | 6 870 | 6 525 | 1,18 / 1,21 pp | 1 949 ✔ | 0,0215 % → 0,060 % |

Rachunek z częstości zdarzenia trafił w journal do 2–6 %; odchylenia to stłumienia kill-switcha
(reguły stanowe) i wyższa abstynencja (A2.5).

## Co na plus (+)

- **Cały skill AT rozstrzygnięty w dwóch rundach, za 7 wariantów**, z jednym parametrem na
  narzędzie (domyślne skilla) i bez wyboru po wyniku; próg pozytywu skorygowany na pięć ramion.
- **Rachunek mocy przed pomiarem zadziałał jako bezpiecznik:** pięć reguł zdarzeniowych nie dostało
  fałszywych „wyników" na 86–988 sygnałach; test rodziny dał im mierzalny sprawdzian.
- **Parytet populacji potwierdzony liczbą** (11 592 świece OOS w każdym ramieniu), regresja kontroli
  co do cyfry, lejek domknięty per ramię.
- **Przewidywanie z góry sprawdziło się co do znaku:** reguły „z ruchem" poniżej 50 % (struktura
  trendu 48,2 %, wybicie 48,5 %), reszta przy 50 %.
- **Reguły stanowe ujawniły efekt uboczny warty zapisania:** nakładające się pozycje z kolejnych
  świec pogłębiają obsunięcia — kill-switch tłumi 3,8–4,8 % wypełnień wobec 1,1 % w kontroli.

## Co na minus (−)

- **Dwa ramiona nierozstrzygnięte** (Fibonacci, grupa zdarzeń) — z konstrukcji: pasmo 2,1 pp przy
  n ≈ 2 200. Dłuższa historia jest wykluczona zasadą 20, inny interwał = nowa hipoteza.
- **Wsparcie/opór zmierzone w wersji zdegenerowanej** (83 % pokrycia): mechanizm „skupienia zleceń"
  wymagałby wyróżnienia poziomów (klastry, liczba dotknięć) — to nowe parametry, których świadomie
  nie dobieraliśmy. Wynik dotyczy wersji ze skilla, nie idei.
- **Stłumienia kill-switcha nie są losowe** (następują po seriach strat): wykluczone transakcje
  reguł stanowych mogły być gorsze niż średnia — kierunek obciążenia raczej na korzyść reguł,
  nie przeciw; werdykt się od tego nie zmienia.
- **A2.5 z 14 cechami na oknach 60-dniowych** — więcej cech niż uzasadnia próba; wzrost
  abstynencji to sygnał przeuczenia, nie informacji. Test grupowy odpowiada na pytanie
  „czy model ma z czego skorzystać", nie „która cecha".
- **Tryb 4h bez 5m** (W1: ≤ 1,4 pp na niekorzyść); jeden instrument, jeden seed; przebicie =
  wypełnienie.
- **Skill `engineering:testing-strategy` wczytany po napisaniu testów** (zasada 19: „przed") —
  jego przegląd dołożył trzy testy (podwójne dno na ręcznej formacji, jawny poziom S/O z wygasaniem,
  końce impulsu Fibonacciego), wszystkie zielone; kolejność odnotowana uczciwie.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Drugą drogą (z liczb wydrukowanych):** p* A2.1 = (1,3027 + 0,0825)/(1,3077 + 1,3027) =
  **53,07 %** ✔; r̄ A2.1 z mieszanki wyjść: 1 080/6 423 · 2,2840 + 1 072/6 423 · (−2,4656) +
  4 271/6 423 · (−0,1496) = 0,3841 − 0,4115 − 0,0995 = **−0,1269 %** wobec −0,1270 % ✔; p A2.1
  z kierunków: (3 425 · 0,4823 + 2 998 · 0,4817)/6 423 = **48,20 %** ✔; lejki: 11 592 = 4 814 +
  6 778, 6 778 = 6 423 + 28 + 327 (A2.1); 9 602 = 9 204 + 36 + 362 (A2.3); 2 167 = 2 133 + 13 + 21
  (A2.4) ✔; guard A2.4: (1,96 · 0,5 + 0,8416 · 0,5)²/(0,5288 − 0,5)² = 1,962/0,000829 = **2 366** ✔;
  z_5: Φ⁻¹(0,995) = 2,576 ✔.
- **Kogo NIE ma:** 60 dni treningu; świece bez sygnału (41 / 80 / 17 / 81 % OOS); pięć reguł
  osobno (nie startowały); stłumione kill-switchem 327 / 12 / 362 / 21 / 78 — nielosowe (po
  stratach), raportowane; niewypełnione 13–39; kolejność w świecy 4h.
- **Red flag „wynik potwierdza hipotezę":** oczekiwanie „≈ 50 %, z ruchem niżej" spełnione —
  sprawdzono, czy to nie artefakt jednej konstrukcji: A2.1 (sygnał stanowy, N_eff 2 875) i A2.4
  (zdarzenia, N_eff = n) dają ten sam obraz różnymi drogami; kontrola niezmieniona; cechy AT
  mają 0 NaN w OOS (populacja A2.5 = 11 592, nie zmalała).
- **Rząd wielkości:** trafności 48–52 %, progi 52–53,6 %, koszt 0,081–0,083 %, std 1,66–1,86 %,
  udziały wyjść sumują się do 100 % — w zakresach z listy kontrolnej.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `agents/ta_rules.py` (nowy, 10 cech + 8 reguł + grupa), sekcja `ta_rules:` rejestru,
`agent_5_compliance/test_leakage.py` (+2 testy: rejestr, przeciek parametryzowany),
`tests/test_ta_rules.py` (15 testów, w tym hypothesis), `backtest/run_ta_rules_a2.py`, README rundy.

**Korektność:** (1) swingi: okno `rolling(2·confirm+1)` kończy się w t, kandydat `shift(confirm)` —
ekstremum z bara t − confirm znane dopiero w t; test przykładowy sprawdza NaN w 20–24 i wartość
w 25; test przecieku df[:T] vs df[:T+k] bit w bit dla 10 cech. (2) Pętle O(n): `low[p1+1:p0]`
z p0 ≤ t − confirm (potwierdzone pozycje), `cpos < t + 1` w S/O — nic z przyszłości. (3)
`_fib_impulse_frame` przy pustych `pos_h`/`pos_l`: `np.clip` na pustej tablicy chroniony
warunkiem `if len(...)`, `valid` wymaga obu swingów. (4) `_event` przy NaN: `fillna(0)` przed
porównaniem — pierwsza wartość niezerowa po NaN liczy się jako zdarzenie (świadomie; w OOS bez
NaN). (5) Skrypt: cechy AT liczone na surowym df PRZED `collect_signals` (kopiowane do df
kontroli), reguły na df kontroli, `build_rule_signals` z guardem RangeIndex, `merge(...,
validate="one_to_one")` chroni tabelę 3 przed duplikacją. (6) Stare testy: 665 → 688 zielone,
literały bit w bit; `FEATURE_FUNCTIONS` produkcyjne nietknięte.

**Edge-case'y:** monotoniczny szereg → brak swingów → NaN w cechach swingowych (test); `ATR = 0`
→ NaN w S/O i podwójnym szczycie; `lookback` wygasza poziomy (test); konflikt zdarzeń → 0 (test).

**Czytelność / wydajność (bez blokady):** trzy pętle w Pythonie (podwójny szczyt, linia trendu,
S/O) — 0,3 s na 12 k świec, wystarczające; przy 5m (100 k+) do wektoryzacji. `_atr` powiela
`feature_miner.compute_atr_14` (ten sam TA-Lib ATR 14) — świadomie bez importu, żeby moduł nie
zależał od produkcyjnego zestawu cech.

**Werdykt jednym zdaniem:** diff poprawny, bez przecieku (test parametryzowany + przykłady na
swingach), z regresją bit w bit i rozdzieleniem od produkcyjnych cech — **Approve**, do scalenia.

## Wniosek

Klasyczna analiza techniczna z podręcznika — użyta dosłownie, deterministycznie, bez dobierania
parametrów — **nie znajduje na BTC 4h pozycji, które po kosztach zarabiają**. Trzy ramiona mają
istotnie ujemny zwrot netto z próbą wystarczającą na dowód braku (struktura trendu −0,127 %,
S/O −0,080 %, model + cechy AT −0,099 %); dwa są nierozstrzygnięte przez rozdzielczość, przy
czym ich estymaty też są ujemne (Fibonacci −0,041 %, zdarzenia −0,103 % z CI pod zerem).
Kierunek „z ruchem" jest na tym rynku i horyzoncie konsekwentnie poniżej monety (A1 46,4 %,
W1c 46,1 %, A2.1 48,2 %, wybicie 48,5 %). **Seria A zamknięta: 7/7, wszystkie rodziny AT ze
skilla.** Wniosek 11 (wąskie gardło informacyjne) po raz kolejny potwierdzony: transformacje ceny
nie tworzą informacji, a dziesięć naraz tylko zwiększa szum.

## Rekomendacja

1. **Zamknąć analizę techniczną na BTC 4h jako kierunek** — bez wyjątków dla „innych parametrów"
   (każdy zestaw = kolejny los; STW 1999) i bez odwracania znaków (wniosek 49).
2. **Nie testować pięciu reguł zdarzeniowych osobno** na tych danych — niemierzalne z konstrukcji;
   ich ewentualny test na 1h (więcej zdarzeń) to nowa hipoteza z własnym rachunkiem mocy i decyzją
   użytkownika, o niskim priorze (te same transformacje).
3. **Ideę wsparcia/oporu (skupienie zleceń) zostawić otwartą, ale nie jako AT:** wymagałaby
   danych o księdze zleceń / likwidacjach (zbiór informacyjny E), nie kolejnej definicji poziomu
   z samych świec.
4. **Metodologicznie:** rachunek mocy z częstości zdarzenia + test rodziny dla rzadkich zdarzeń
   (wniosek 53); reguły stanowe wymagają raportowania stłumień kill-switcha (wniosek 52).
5. **Następny krok = punkt 2 zlecenia użytkownika** (kierunki spoza ceny i wolumenu): inny cel niż
   kierunek, cash-and-carry z hedgem spot, pozycjonowanie (kolektor już działa).

## Użyte skille

Rejestr gałęzi `a2-rodziny-at` (`py tools/skill_audit.py raport --galaz a2-rodziny-at`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → INDEX → kod cech → zliczenie → pre-rejestracja → skrypt → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | rachunek mocy z częstości zdarzenia per ramię, „NIEMIERZALNA = nie startuje" bez zamrożonej stałej (assumed p = konwencja podręcznika z A1), N_eff ≤ n, test rodziny, korekta na m ramion |
| `anthropic-skills:ta-toolkit` | 10 funkcji deterministycznych z parametrami domyślnymi, DoF per narzędzie, gdzie AT leakuje (swingi), statusy i literatura (BLL/STW, LMW) |
| `anthropic-skills:quant-strategy-catalog` | pięć pól, rodzina A5, „nowa nazwa ≠ nowa hipoteza" (wybicie vs W1c, EMA vs `ema_diff`), plan punktu 2 |
| `data:validate-data` | bramka 16a: druga droga dla p*, r̄, p, lejków, guardu i z_5; „kogo nie ma" (stłumienia nielosowe) |
| `data:statistical-analysis` | bramka 16b: CI zamiast p/z, mediana obok średniej, Bonferroni, jak raportować 5 podgrup i A2.4 bez łamania litery |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |
| `engineering:testing-strategy` | przegląd testów (PO ich napisaniu — odstępstwo zapisane w „minusach"): +3 testy luk |

Z tabeli zasady 19 pominięte: `dataviz` (bez wykresów), `data:explore-data` (te same parquety),
`engineering:architecture` (bez ADR — moduł reguł to rozszerzenie wzorca A1), `update-config`,
`security-review` (bez kluczy, zleceń i sieci), `lean-research`.
