# N1 — nowy cel modelu: częściowe wyjście 50 % + stop na wejściu (2026-09-23)

> **STATUS: ZAMKNIĘTA — WYNIK NEGATYWNY.** Pre-rejestracja w commicie `fa1abdb` (przed kodem),
> kod + Poprawka 1 w `4683669` (przed uruchomieniem — kolejność dowodliwa z gita), wynik w commicie
> scalającym gałąź. W rozmowie runda nazywana była „W2"; dostaje ID **N1**, bo to NOWA HIPOTEZA
> (nowy cel), a seria W jest zamknięta regułą STOP. **Licznik N: 1/1 — WYCZERPANY, reguła STOP.**
> Walidacja (16a): **READY** (sekcja niżej).

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Prowadzenie pozycji „połowa zysku wcześniej, stop na wejście" nie zmienia pieniędzy.** Na tych
samych 6 736 transakcjach (ten sam model, te same wejścia) różnica wobec zwykłego wyjścia to
**+0,007 % na transakcji, w przedziale od −0,009 % do +0,024 %** — czyli zero. Oba sposoby tracą
średnio ok. 0,1 % nominału na transakcji (koszty 0,08 % + brak przewagi kierunkowej).

**Trafność za to skoczyła z 49,6 % na 53,3 %** — i gdyby czytać ją starym progiem (53,3 %), wyszłoby
„na styk opłacalne". To dokładnie iluzja z W1b w czystej postaci: wygrane zrobiły się mniejsze
(średnio 1,11 % zamiast 1,30 %), a straty zostały pełne (1,30 %). Przy takich wypłatach trzeba
trafiać w **57,2 %**, żeby wyjść na zero — nie 53,3 %. Dlatego werdykt tej rundy stoi na pieniądzach
z przedziałem ufności, tak jak zapisaliśmy przed uruchomieniem: **NEGATYWNY**.

**Skąd biorą się straty:** połowa transakcji (51 %) kończy się po czasie bez dojścia do pierwszego
zysku — i te transakcje przeciętnie tracą 0,26 %, bo sygnał, który w 12 h nie doszedł do +1,67 %,
zwykle dryfuje przeciw pozycji. Wszystko, co zarabia (32 % transakcji z pierwszym zyskiem), nie
pokrywa stopów (17 %, po −2,3 %).

**Dwie rzeczy, które ta runda dała poza werdyktem:** (1) nowa baza danych od 2021 (Twoja zasada 20)
jest dla modelu trudniejsza niż pełne 6,8 roku — trafność kontrolna 49,6 % wobec 50,4 %;
(2) testy przykładowe złapały wadę w mojej własnej regule 6 **zanim** cokolwiek uruchomiłem
(Poprawka 1 niżej) — mechanizm pre-rejestracji zadziałał tak, jak ma działać.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Skąd ta runda.** Użytkownik ustalił, jak będzie prowadził pozycję na żywo: przy dźwigni 3×
pierwszy zysk to **+5 % depozytu** (czyli ruch ceny o **+1,67 %**), wtedy **zamyka połowę pozycji
i przesuwa stop na cenę wejścia** („dalej nie mogę stracić"); druga połowa jedzie do
dotychczasowej bariery zysku (**1,5·ATR od wejścia**, średnio ok. 2,3 % ceny); stop przed
pierwszym zyskiem zostaje na 1,5·ATR; limit czasu **12 h** (3 świece 4h) dla całości. Do tego
nowa zasada: **dane tylko od 2021-01-01** (CLAUDE.md zasada 20).

**Co sprawdzamy.** Czy takie prowadzenie pozycji zmienia wynik pieniężny — na tych samych
sygnałach, tym samym modelu i tym samym wejściu (limit po cenie zamknięcia, jak w W1a). Jedna
zmiana: zarządzanie pozycją po wejściu.

**Czego się spodziewam — zapisane z góry.** Że nie zarobi. Model trafia kierunek jak moneta
(50,3 %), a zarządzanie pozycją nie tworzy informacji — może tylko przesunąć pieniądze między
typami wyjść. Konkretnie: pierwszy zysk leży bliżej niż stop (1,67 % wobec ~2,3 %), więc
**będzie padał częściej** — ale wygrana z połowy pozycji jest mała, a stop na wejściu zamienia
część pełnych wygranych w zera. Trafność (odsetek wygranych) prawie na pewno **wzrośnie**;
średni wynik pieniężny — zapisuję, że **nie**. To jest dokładnie pułapka z W1b i dlatego werdykt
tej rundy opiera się na **pieniądzach z przedziałem ufności**, a nie na trafności.

**Dlaczego to nie jest strojenie.** Wszystkie poziomy pochodzą z reguł użytkownika, są zapisane
przed uruchomieniem, jest jeden wariant i po nim reguła STOP — bez przesuwania progów po wyniku.

---

## ID testu

**N1** — pierwszy wariant **NOWEJ SERII N** („nowy cel"). Własny licznik od zera, własna reguła
STOP: **1 wariant**. **Nowa baza danych** (2021-01-01 → 2026-07-01, zasada 20) — wyniki nie
porównują się 1:1 z rundami na 6,8 roku; kontrola liczona na nowo w tej rundzie (0 wariantów).

## Metadane

- **Branch:** `w2-nowy-cel` (nazwa nadana, zanim ustalono ID rundy)
- **Poprzedzający stan (master):** `17b9d93` (merge W1)
- **Decyzje użytkownika (2026-09-23), które ustawiają tę rundę:** (1) najpierw naprawa
  wykonania (W1 — zrobione), potem nowy cel; (2) „TP = 5 % depozytu przy 3×"; (3) druga połowa
  do 1,5·ATR od wejścia, stop na cenę wejścia po pierwszym zysku; (4) limit czasu 12 h dla
  całości; (5) sizing bez zmian; (6) dane od 2021-01-01 (rok 2021 włącznie).
- **Komenda:** `py -m backtest.run_partial_tp_n1` (pełny output: `raw_output.txt`; skrypt na liście
  `runs/ZAMROZONE.txt`; buduje na `checkpoint_lib.fetch_window` + `execution.ManagedExitRule`).
  Czas przebiegu: 3 s.
- **Dane:** natywne świece 4h BTC/USDT perpetual, filtr `2021-01-01 →` z pełnego cache
  (12 042 świece, 5,49 roku, 69 okien walk-forward 60/28/28, 11 592 świece testowe); bez świec
  5m (część kalibracyjna W1 pokazała, że przybliżenie 4h myli się w 0,3–2,7 % transakcji
  i zawsze na niekorzyść strategii — obciążenie znane, konserwatywne).
- **Testy przed rundą:** 610/610.

## Poprzedzające wyniki (zasada 14)

- **W1** (`runs/2026-09-23_w1-wykonanie-po-cenie/`) — daje model wykonania (tryb `path`,
  `limit_close`, k = 1) i **lekcję, która rządzi tą rundą:** trafność 53,15 % nad progiem przy
  istotnie ujemnym zwrocie (t = −3,90), bo wzór progu zakłada wypłaty ±B. Tu wypłaty są
  asymetryczne Z DEFINICJI (połowa pozycji wychodzi wcześniej), więc trafność nie może być
  kryterium. Kryterium POZYTYWNE ma dwa warunki (CLAUDE.md, wytyczna): `ci_low(p) > próg`
  ORAZ `t_stat(zwrot) > 0` — z progiem UOGÓLNIONYM na asymetryczne wypłaty (niżej).
- **M1 / F1 / K3** — konfiguracja kanoniczna i abstynencja 43,84 % (do rachunku mocy).
- **Z10, wniosek 11** — model nie zna kierunku; zarządzanie pozycją nie dodaje informacji.
  Prior tej rundy: negatywny.
- **T1-diag** — funding jest pomijalny przy symetrycznych long/short; przy dłuższym trzymaniu
  drugiej połowy nadal liczony per noga.
- **Pomiar opisowy przed rundą** (bez modelu, bez etykiet; skrypt w scratchpadzie sesji):
  na oknie 2021+ pierwszy cel +1,67 % pada przed stopem 1,5·ATR w **31,1 %** świec, stop
  pierwszy w 16,2 %, żaden w 12 h w 52,4 % (obie bariery w jednej świecy 0,3 %); **w 20,6 %
  świec 1,5·ATR < 1,67 % ceny** (cele „odwrócone" — reguła porządkująca niżej); rozrzut zwrotu
  netto per trade w W1a na transakcjach od 2021: **std 1,85 % nominału** (n 6 627).

## Rozstrzygnięcia projektowe (zapisane PRZED przebiegiem)

### Jedna zmienna

**Zarządzanie pozycją po wejściu.** Wszystko inne jak w W1a: cechy `REVERSION_FEATURES`, bez
bramki reżimu, **etykieta bez zmian** (±1,5·ATR, V = 3), wagi klas `balanced`, walk-forward
60/28/28, seed 42, wejście limitem po `close` ważnym 1 świecę (tryb `path`), model kosztów
`maker_limit`, sizing 0,5 % ryzyka na odległości stopu 1,5·ATR z sufitem dźwigni 3×.

**Dlaczego etykieta zostaje symetryczna** (decyzja projektowa, nie użytkownika): stop = 1,5·ATR
= bariera etykiety (zasada 3 spełniona), druga połowa wychodzi dokładnie na barierze etykiety,
a pierwsze wyjście to nakładka zarządzania na TĘ SAMĄ prognozę. Dzięki temu (a) model i sygnały
są identyczne z kontrolą — porównanie parowane na tych samych transakcjach; (b) jest DOKŁADNIE
jedna zmienna. Przebudowa etykiety pod pierwszy cel (asymetryczna, +1,67 % / −1,5·ATR) to inny
model — jawnie NIE jest częścią tej rundy.

### Reguły prowadzenia pozycji (identyczne w kodzie i tutaj)

Po wypełnieniu po cenie `E` (kierunek `d`, `ATR` = `atr_14` świecy sygnału):

1. **Dwa cele:** `T_a = E·(1 + d·0,0167)` (5 % depozytu przy 3×) i `T_b = E + d·1,5·ATR`.
   **Bliższy** z nich = `T_near`, dalszy = `T_far`. (W 20,6 % świec 1,5·ATR < 1,67 % i wtedy
   `T_near = T_b` — tak działają dwa zlecenia limit spoczywające w księdze: bliższe wypełnia się
   pierwsze. Reguła zapisana, żeby nie wybierać po wyniku.)
2. **Stop początkowy** `S = E − d·1,5·ATR` na 100 % pozycji (taker).
3. **Na `T_near`:** wychodzi **50 %** pozycji (maker, limit), stop przesuwa się na **`E`**
   (break-even, stop-market → taker) dla pozostałych 50 %.
4. **Na `T_far`:** wychodzi pozostałe 50 % (maker).
5. **Timeout:** zamknięcie świecy `t + 3` (od sygnału) po rynku (taker) dla tego, co zostało.
6. **Kolejność w świecy (tryb 4h, jak W1):** w świecy wypełnienia liczy się tylko stop, chyba że
   wypełnienie na otwarciu. ~~W świecy zdarzenia `T_near` (gdy nie na otwarciu) po częściowym
   wyjściu liczy się w tej samej świecy **tylko stop na `E`**, `T_far` dopiero od następnej
   świecy.~~ **POPRAWKA 1 (2026-09-23, PRZED uruchomieniem, wykryta testami przykładowymi reguły
   6, zero spojrzeń na dane):** przy wejściu limitem minimum świecy wypełnienia leży PONIŻEJ ceny
   wejścia z samej konstrukcji wypełnienia (przebicie `low < E`), więc reguła „liczy się stop na
   `E`" zamykałaby drugą połowę mechanicznie w każdej transakcji, w której bliższy cel pada
   w świecy wypełnienia — to artefakt, nie ostrożność. Reguła zastępcza, ŚCIŚLEJSZA logicznie:
   bliższy cel pada w nieznanej chwili τ wewnątrz świecy; zdarzenie po τ jest dowiedzione
   wyłącznie przez **zamknięcie tej świecy** — `close` za `T_far` ⇒ dalszy cel padł po τ (ścieżka
   od `T_near` do `close` musiała przeciąć `T_far`); `close` za `E` ⇒ stop na wejściu padł po τ
   (ścieżka od `T_near` > `E` do `close` ≤ `E` przecięła `E`). Ekstrema świecy nie są dowodem.
   Nic niedowiedzionego = nic się nie stało w tej świecy; od następnej świecy normalnie.
   Gdy bliższy cel był spełniony już na otwarciu świecy (luka), liczy się cała jej ścieżka.
   Obie bariery w jednej świecy → reguła etykiety (bliższa otwarciu pierwsza).
7. **Koszty per noga:** wejście maker na 100 % nominału; `T_near`/`T_far` maker na 50 % każde;
   stop `S` taker na 100 %; stop `E` taker na 50 %; timeout taker na to, co zostało; funding za
   świece trzymania każdej połowy osobno. Zwrot netto transakcji = suma nóg / nominał wejścia.

### Kontrola (0 wariantów)

Te same sygnały, ten sam model (jeden trening na oknie 2021+), wykonanie W1a (`limit_close`,
k = 1, wyjście pojedyncze TP/SL/timeout). Dostarcza: liczby odniesienia na nowej bazie
(trafność, zwrot netto, próg) oraz **porównanie parowane** z N1 transakcja po transakcji.

### Kryterium — zapisane PRZED uruchomieniem

Niech `r_i` = zwrot netto transakcji `i` (% nominału wejścia), `p` = udział `gross_pnl > 0`,
`W̄` = średnia wygrana brutto, `L̄` = średnia strata brutto (moduł), `C` = średni koszt.
**Próg uogólniony** (nie zakłada ±B): `p* = (L̄ + C) / (W̄ + L̄)` — trafność, przy której
oczekiwana wypłata jest zerem dla ZMIERZONYCH wielkości wygranej i straty. Dla wypłat ±B redukuje
się do `0,5·(1 + C/B)`.

- **POZYTYWNY:** `t_neff(r̄) > 1,96` (średni zwrot netto dodatni, po korekcie N_eff)
  **ORAZ** `ci_low(p) > p*`. Pierwsza reakcja: szukaj przecieku; potem replikacja (zasada 9).
- **NEGATYWNY:** `t_neff(r̄) < −1,96` **oraz** `n ≥ 4 000` (moc: przy std 1,85 % i n = 4 000
  wykrywalny jest efekt |r̄| ≥ 0,08 % — rząd kosztu transakcji).
- **NIEROZSTRZYGNIĘTY:** w pozostałych przypadkach.
- **Porównanie parowane N1 − kontrola** (na tych samych transakcjach): średnia różnica zwrotu
  netto z 95 % CI — **obserwacja, nie kryterium** (mówi, CO zmieniło zarządzanie, nie czy
  strategia zarabia).
- **REGUŁA STOP:** jeden wariant; seria N zamknięta niezależnie od wyniku. Żadnego innego
  poziomu pierwszego zysku, udziału zamykanej części, trailing stopu ani limitu czasu.
- **Test kryterium w granicy dużego `n`** (zasada 18): przy `r̄ < 0` rosnące `n` prowadzi do
  NEGATYWNEGO, przy `r̄ > 0` do POZYTYWNEGO — kryterium nie karze celu rundy.

### Rachunek mierzalności (zasada 18)

`expected_trades(11 592 świec testowych, abstynencja 43,84 %, wypełnienia 99,4 %)` ≈ **6 470**
transakcji. Zwrot netto: `se = 1,85 % / √6 470 ≈ 0,023 %`, więc 95 % CI średniej ma półszerokość
**≈ 0,045 %** nominału, a efekt wykrywalny z mocą 80 % to **|r̄| ≥ 0,065 %** — mniejszy niż koszt
transakcji (0,081 %) i niż dotychczasowa strata per trade (−0,082 % w W1a). **MIERZALNA.**
Trafność (diagnostyka): pasmo `wald_half_width(6 470)` = 1,22 pp; `measurability_report(50,4 %,
52,9 %, 6 470)` → NIEMIERZALNA dla „czy jest edge" (jak zawsze w tym projekcie) — dlatego
kryterium główne jest na zwrocie, a trafność wchodzi tylko przez próg uogólniony.

### Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- Udział transakcji z pierwszym zyskiem: rzędu 30 % (opisowo 31 % dla całej populacji świec,
  po sygnałach modelu może być inaczej); trafność (`gross > 0`) **wzrośnie** wobec kontroli,
  bo część transakcji kończy się połową wygranej i stopem na wejściu (gross ≈ +0,8 % zamiast
  −2,3 % lub +2,3 %).
- Średni zwrot netto: spodziewam się **ujemnego**, zbliżonego do kontroli (rząd −0,05 … −0,10 %),
  bo zarządzanie pozycją przy trafności ~50 % obcina prawy ogon (wygrane) tak samo jak lewy
  (straty) — z dokładnością do asymetrii odległości celów.
- Koszt na transakcję **wzrośnie** (więcej nóg: 4 zamiast 2 przy pełnym scenariuszu).
- Wynik pozytywny traktuję z podejrzliwością proporcjonalną do jego niezwykłości — projekt
  złapał już trzy przecieki i jedną iluzję geometrii.

### Czego ta runda NIE raportuje i NIE interpretuje

- **Żadnych innych poziomów celów, udziałów ani limitów czasu** — nie ma sekcji wrażliwości
  (jeden wariant; wrażliwość byłaby strojeniem).
- `classification` z `metrics.classify_checkpoint` nie jest kryterium (wniosek 24);
  `break_even_p` z `summarize_edge_by_regime` (wzór ±B) podawane wyłącznie obok progu
  uogólnionego, z adnotacją.
- Nic o analizie technicznej i formacjach świecowych (następna runda po N1, `ta-toolkit`).

### Kogo NIE ma w zbiorze — zapisane z góry

(a) świece sprzed 2021-01-01 (zasada 20); (b) 43,84 % świec, na których model odmawia kierunku;
(c) ~0,6 % sygnałów niewypełnionych i stłumione kill-switchem; (d) kolejność zdarzeń wewnątrz
świecy 4h przybliżona (bez 5m) — obciążenie konserwatywne ≤ 1,4 pp (W1); (e) tylko BTC, jeden
seed; (f) pozycje nakładające się sizowane niezależnie; (g) brak księgi zleceń — „przebicie
poziomu = wypełnienie" dla wejścia i celów (optymistyczne dla limitów, rząd 0,5 % kosztu w W1).

## Definition of Done tej rundy

- `config/settings.yaml`: `data.min_start = "2021-01-01T00:00:00Z"` czytany przez
  `checkpoint_lib.fetch_native` (zasada 20 w JEDNYM miejscu) + test.
- `backtest/execution.py`: reguła wyjścia z dwoma celami i stopem na wejściu (czyste funkcje),
  wynik jako lista nóg; testy przykładowe reguł 1–7 i **własności `hypothesis`**: suma udziałów
  nóg = 1, nogi w porządku czasowym, stop na `E` tylko po `T_near`, brak lookaheadu, cena każdej
  nogi ∈ {T_near, T_far, S, E, close[t+V]}. Skill `engineering:testing-strategy` PRZED testami.
- `backtest/engine.py`: parametr reguły wyjścia w trybie `path` (domyślnie pojedyncze wyjście
  = zachowanie W1 bit w bit), P&L i koszty per noga, journal z kolumnami częściowego wyjścia.
- ADR w `docs/rag/03` (cel modelu vs zarządzanie pozycją; próg uogólniony `p*`), skill
  `engineering:architecture` PRZED pisaniem.
- Bramki: `data:validate-data` (16a: koszt z mieszanki nóg vs journal; zwrot parowany vs różnica
  średnich; `n` z `expected_trades`), `data:statistical-analysis` (16b), `engineering:code-review`
  (16c) — wczytane na tej gałęzi.
- `raw_output.txt`; wiersz w `runs/INDEX.md` + nowy licznik serii N + nowa baza danych; STATUS;
  README (kamień milowy); skrypt na `runs/ZAMROZONE.txt`; sekcja „Użyte skille" z rejestru.

---

## Wynik

### 0. Dane i lejek (nowa baza, zasada 20)

12 042 świece 4h, 2021-01-01 → 2026-06-30, **69 okien walk-forward** (wszystkie aktywne), 11 592
świece ocenione, abstynencja **40,38 %** (4 681), bramki 0, **6 911 sygnałów kandydujących** —
wspólnych dla kontroli i N1 (jeden trening). Niewypełnione 43 / 42, stłumione kill-switchem
79 / 74 (bilans: 6 789 + 43 + 79 = 6 911; 6 795 + 42 + 74 = 6 911).

### 1. Kryterium — zwrot netto per trade (% nominału wejścia)

| ramię | n | r̄ netto | CI 95 % | mediana | t | N_eff | t_neff | werdykt |
|---|---|---|---|---|---|---|---|---|
| kontrola (pojedyncze wyjście, jak W1a) | 6 789 | **−0,107 %** | [−0,149; −0,065] | −0,104 % | −5,01 | 4 919 | −4,26 | odniesienie (0 wariantów) |
| **N1** (50 % na bliższym celu, stop na wejściu, reszta do 1,5·ATR) | 6 795 | **−0,094 %** | [−0,131; −0,058] | **+0,002 %** | −5,03 | 4 474 | **−4,08** | **NEGATYWNY** (t_neff < −1,96, n ≥ 4 000) |

**Porównanie parowane N1 − kontrola** (6 736 wspólnych transakcji; 4 577 identycznych — bliższy cel
nie padł): średnia różnica **+0,0071 %** nominału, 95 % CI **[−0,0092; +0,0235]**, t = +0,85,
mediana różnicy 0. Zarządzanie pozycją nie zmienia wyniku pieniężnego w żadną stronę.

### 2. Trafność — diagnostyka z progiem uogólnionym

| ramię | p | CI 95 % | p* = (L̄ + C)/(W̄ + L̄) | „BE ±B" (0,5·(1 + C/B), diagnostyka) | W̄ | L̄ | C |
|---|---|---|---|---|---|---|---|
| kontrola | 49,58 % | [48,39; 50,77] | 53,64 % | 53,07 % | 1,303 % | 1,333 % | 0,0808 % |
| **N1** | **53,33 %** | [52,15; 54,52] | **57,24 %** | 53,32 % | **1,110 %** | 1,302 % | 0,0786 % |

Stary wzór dałby dla N1 „trafność 53,33 % przy progu 53,32 %" — margines +0,0001 pp, czyli
„na styk". Próg uogólniony mówi 57,24 %: wygrane zmalały o 0,19 pp (połowa pozycji wychodzi
wcześniej), straty nie. `ci_low(p)` = 52,15 % < p* → warunek pozytywny niespełniony także po
stronie trafności.

### 3. Ścieżki wyjścia N1 — skąd biorą się pieniądze

| ścieżka | n | udział | brutto śr. | netto śr. | wygrane |
|---|---|---|---|---|---|
| timeout całej pozycji (bliższy cel nie padł) | 3 489 | **51,3 %** | **−0,257 %** | −0,347 % | 41,5 % |
| stop całej pozycji | 1 131 | 16,6 % | −2,301 % | −2,391 % | 0 % |
| bliższy cel → dalszy cel | 841 | 12,4 % | +2,077 % | +2,037 % | 100 % |
| bliższy cel → timeout reszty | 807 | 11,9 % | +1,506 % | +1,441 % | 100 % |
| bliższy cel → stop na wejściu | 527 | 7,8 % | +0,818 % | +0,754 % | 100 % |

Bliższy cel pada w **32,0 %** transakcji (opis. 31,1 % dla populacji świec — zgodne). Po nim żadna
ścieżka nie traci (stop na wejściu = połowa zysku zatrzymana). Cała strata siedzi w 68 %
transakcji BEZ bliższego celu: timeouty ze średnią −0,26 % (sygnał, który nie doszedł do +1,67 %
w 12 h, przeciętnie dryfuje przeciw pozycji) i pełne stopy. Rozrzut zwrotu: std 1,54 % (kontrola
1,76 %), p5/p95 [−2,81 %; +2,10 %].

### 4. Mierzalność (zasada 18) — ex ante i ex post

`expected_trades` ex ante 6 471 (abstynencja 43,84 % z K3, wypełnienia 99,4 %), ex post 6 869
(abstynencja 40,38 % na nowej bazie), journal 6 795 — zgodne z dokładnością do stłumionych.
`se` zwrotu netto 0,0187 % → wykrywalny efekt (moc 80 %) |r̄| ≥ 0,052 %; zmierzony −0,094 % leży
1,8× dalej. Trafność: pasmo 1,19 pp; „czy jest edge" NIEMIERZALNE jak zawsze — dlatego kryterium
było na zwrocie.

## Co na plus (+)

- **Runda wyszła dokładnie tak, jak zapisano w „Arytmetyce oczekiwań":** trafność wzrosła (49,6 →
  53,3 %), zwrot netto ujemny i zbliżony do kontroli (−0,094 vs −0,107 %), koszt na transakcję —
  tu wbrew oczekiwaniu odrobinę NIŻSZY (0,0786 vs 0,0808 %: połowa pozycji częściej wychodzi
  limitem, czyli taniej). Pierwsza reakcja na „trafność nad starym progiem" to policzenie p*,
  nie ogłoszenie — i tak zrobiono.
- **Pre-rejestracja zadziałała jako bezpiecznik dwa razy:** (1) kryterium na zwrocie netto,
  zapisane przed wynikiem, jednoznacznie rozstrzyga rundę, której trafność wygląda „na styk";
  (2) testy przykładowe reguły 6 wykryły wadę mechaniczną PRZED uruchomieniem (Poprawka 1,
  commit `4683669` poprzedza wynik).
- **Porównanie parowane** na tych samych transakcjach daje przedział ±0,016 pp — pięć razy węższy
  niż porównanie dwóch niezależnych średnich; zero jest w środku.
- **Jedna zmienna, ten sam model:** 4 577 z 6 736 transakcji identycznych co do wiersza; różnią się
  tylko te, w których padł bliższy cel — i tam wszystkie ścieżki są zyskowne (nie ma „ukrytej"
  straty w zarządzaniu).
- **Zasada 20 wdrożona strukturalnie:** filtr daty w jednym miejscu (`fetch_window`), test pilnuje
  daty w konfiguracji, skrypty zamrożone nietknięte.

## Co na minus (−)

- **Nowa baza jest trudniejsza i mniejsza:** kontrola na 2021+ ma p 49,58 % i −0,107 % na
  transakcję (na 6,8 roku: 50,11 % i −0,082 %). Liczby serii W/N nie porównują się 1:1 z żadną
  wcześniejszą rundą — to koszt zasady 20, zapisany z góry.
- **Bez świec 5m:** kolejność zdarzeń wewnątrz świecy 4h przybliżona; W1 zmierzyło obciążenie
  ≤ 1,4 pp trafności w stronę konserwatywną, ale przy DWÓCH zdarzeniach w świecy (bliższy cel +
  stop/dalszy) przybliżenie jest grubsze. Poprawka 1 rozstrzyga tylko przypadki dowiedzione
  zamknięciem — reszta liczy się neutralnie („nic się nie stało"), co może zaniżać udział
  szybkich stopów na wejściu i dalszych celów w świecy celu.
- **Cele „odwrócone"** (21 % świec: 1,5·ATR < 1,67 %) obsłużone regułą porządkującą, ale nie
  rozbite osobno w wyniku — jeden wariant, bez podgrup (unikanie podziału po wyniku).
- **Poprawka 1 zmienia literę pre-rejestracji** — zapisana z powodem i przed uruchomieniem, ale
  pozostaje zmianą reguły po jej zapisaniu; test przykładowy, który ją wymusił, jest w repo.
- Jeden instrument, jeden seed, pozycje nakładające się sizowane niezależnie; „przebicie =
  wypełnienie" dla wejścia i celów (optymistyczne, rząd 0,5 % kosztu — W1).

## Walidacja (zasada 16a) — werdykt: **READY**

- **Kluczowe liczby drugą drogą** (z liczb wydrukowanych, poza `metrics.py`):
  p* = (L̄ + C)/(W̄ + L̄) = (1,3021 + 0,0786)/(1,1101 + 1,3021) = 1,3807/2,4122 = **57,24 %** ✔;
  zwrot netto N1 z mieszanki ścieżek: 0,513·(−0,2569) + 0,166·(−2,3008) + 0,124·2,0770 +
  0,119·1,5055 + 0,078·0,8176 = −0,0132 % brutto, minus koszt 0,0786 % = **−0,092 %** wobec
  −0,094 % z journalu (różnica = zaokrąglenie udziałów) ✔; próg ±B = 0,5·(1 + 0,000786/0,011823)
  = **53,32 %** ✔; bilans lejka 6 911 = n + niewypełnione + stłumione w obu ramionach ✔;
  `expected_trades` ex post 6 869 vs 6 795 (różnica = stłumione 74) ✔.
- **Kogo NIE ma w zbiorze:** 4 681 świec abstynencji (40,4 %); 42–43 niewypełnione; 74–79
  stłumione (i to one różnią zbiory kontroli i N1 — 6 736 wspólnych); świece sprzed 2021-01-01
  (zasada 20 — 2 874 świec z pełnego cache); kolejność wewnątrz świecy bez 5m.
- **Red flag „wynik potwierdza hipotezę":** oczekiwanie brzmiało „nie zarobi" i tak wyszło —
  sprawdzono, czy to nie artefakt Poprawki 1 (neutralne traktowanie niedowiedzionych zdarzeń):
  ścieżki po bliższym celu są wszystkie zyskowne, a strata siedzi w 68 % transakcji bez celu,
  na które Poprawka 1 nie ma wpływu. Trafność „na styk" starego progu — rozpoznana jako pułapka
  W1b, nie jako wynik.
- **Rząd wielkości:** trafności 49–53 %, próg ±B 53 %, koszt 0,08 %, std zwrotu 1,5–1,8 % —
  w zakresach z listy kontrolnej; udziały ścieżek sumują się do 100 %; N_eff ≤ n.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `git diff master...HEAD` — 14 plików, +1 582 / −22 (kod: `execution.py` +206, `costs.py` +77,
`engine.py` +57, `checkpoint_lib.py` +16; 4 nowe pliki testów, 40 testów; skrypt rundy 301 linii).

**Korektność**
- Faza 1 (`simulate_managed_exit`): pętla od świecy wypełnienia; w niej tylko stop, chyba że
  wypełnienie na otwarciu — identycznie jak `simulate_exit` z W1. ✔
- Poprawka 1 używa WYŁĄCZNIE `close[near_idx]` — zamknięcia świecy, w której padł bliższy cel;
  żadnej świecy przyszłej (brak lookaheadu). Kierunek short symetryczny: `c_near <= far` (far leży
  niżej), `c_near >= entry`; `near_at_open` dla short = `open <= near`. ✔ (testy przykładowe
  long/short + hypothesis)
- Faza 2 od `near_idx + 1`, albo od `near_idx` z PEŁNĄ świecą, gdy cel padł na otwarciu (wtedy
  τ = open i cała świeca jest „po celu"). ✔
- Koszt per noga: fee wejścia na całym nominale; fee/poślizg wyjścia i funding na
  `ułamek × nominał`; trzymanie per noga = `leg.idx − fill_idx + 1` (to samo co przy jednej
  nodze). Jedna noga → delegacja do `total_round_trip_cost` (test bit w bit). ✔
- Tryb intrabar: nogi mapowane `bar_of(sub_idx)` PRZED liczeniem offsetów i fundingu —
  jednostki spójne. ✔
- `fetch_window`: głośny błąd bez `min_start`, odporne na strefę czasową; skrypty zamrożone
  wołają `fetch_native` bez filtra (odtwarzalność zamkniętych rund). ✔

**Edge-case'y:** cele „odwrócone" (1,5·ATR < 1,67 %) — `managed_targets` porządkuje, przy
równości cel procentowy jako bliższy (udokumentowane); `far == near` (miara zero) — druga noga
po tej samej cenie, poprawnie; sygnał stłumiony → `n_legs = 0`; tryb „label" → `n_legs = 1`,
`legs = ()`; nogi zawsze sumują się do 1 (własność w hypothesis).

**Testy:** 650/650 zielone — 610 testów sprzed rundy bez zmian (regresja bit w bit W1 i trybu
„label"), 40 nowych: własności nóg (suma ułamków, porządek czasowy, cena ∈ {near, far, S, E,
close}), przykłady Poprawki 1 (long/short, cel na otwarciu i w środku świecy), koszt jednej nogi
≡ `total_round_trip_cost`, journal N1 vs kontrola na tych samych sygnałach, okno danych.

**Czytelność / uwagi (bez blokady):** (1) w gałęzi wielonogowej `simulate_equity` liczy najpierw
koszt jak dla jednej nogi, potem nadpisuje `multi_leg_cost` — podwójna praca, zero wpływu na
wynik; do uporządkowania przy następnym dotknięciu silnika. (2) `simulate_managed_exit` ma dwie
pętle i `continue` — komentarz wystarcza, ale przy kolejnej regule wyjścia fazę 2 wydzielić do
osobnej funkcji. (3) Ostrzeżenia wzorców `security-guidance`: brak (bez `pickle`, `shell=True`,
sieci).

**Werdykt jednym zdaniem:** diff jest poprawny, bez lookaheadu, z regresją bit w bit dla
wszystkich wcześniejszych trybów i pokryciem nowych reguł testami przykładowymi i własnościowymi —
**Approve**, do scalenia.

## Wniosek

Prowadzenie pozycji wybrane przez użytkownika (połowa zysku przy +1,67 %, stop na wejście,
reszta do 1,5·ATR) **nie zmienia wyniku pieniężnego** modelu: −0,094 % na transakcję wobec
−0,107 % bez zarządzania, różnica parowana +0,007 % [−0,009; +0,024]. Zmienia za to obraz:
trafność rośnie do 53,3 %, mediana zwrotu staje się dodatnia, a średnia pozostaje istotnie
ujemna (t_neff −4,08) — bo wygrane maleją, straty nie. To potwierdza wniosek skumulowany 11
z drugiej strony: **zarządzanie pozycją nie tworzy informacji**; przy trafności kierunku ~50 %
przesuwa tylko pieniądze między typami wyjść. Seria N zamknięta: 1/1, reguła STOP.

## Rekomendacja

1. **Nie testować kolejnych schematów prowadzenia pozycji** (inne poziomy, trailing, udziały) na
   modelu bez sygnału — każdy da to samo: inną trafność, te same pieniądze.
2. **W każdej przyszłej pre-rejestracji z wypłatami asymetrycznymi używać progu uogólnionego p***
   i kryterium na zwrocie netto — tak jak tu; `docs/rag/03` (ADR N1) i `bramki-jakosci.md` B3.
3. **Następna runda — decyzja użytkownika 2026-09-23: sygnały z analizy technicznej i formacji
   świecowych (`ta-toolkit`)** jako NOWA HIPOTEZA (nowy zbiór cech, ten sam zbiór informacyjny
   OHLCV — prior niski, wniosek 11), z własnym licznikiem, testem przecieku każdej cechy przed
   wejściem do modelu (zasada 2), jedną cechą na raz (zasada 4) i rachunkiem mocy; wykonanie
   i zarządzanie pozycją: jak w tej rundzie (limit po close, bez częściowego wyjścia —
   pojedyncze wyjście jest równie dobre i prostsze).

## Użyte skille

Rejestr gałęzi `w2-nowy-cel` (`py tools/skill_audit.py raport --galaz w2-nowy-cel`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: pre-rejestracja w osobnym commicie, rachunek mocy z abstynencji, bramki, DoD |
| `anthropic-skills:clas5-quant` | jedna zmienna (etykieta bez zmian), zasada 3, kryterium na zwrocie zamiast trafności, przypadek celów odwróconych |
| `anthropic-skills:quant-strategy-catalog` | pięć pól: ten sam zbiór informacyjny i formuła, inny target-wypłata → nowa hipoteza z własnym licznikiem; mechanizm „zarządzanie nie tworzy informacji" zapisany w oczekiwaniach |
| `engineering:architecture` | ADR w `docs/rag/03` (cel vs zarządzanie, p*, odrzucone alternatywy) |
| `engineering:testing-strategy` | plan testów: własności nóg (suma 1, porządek, dowód zamknięciem), bit w bit dla jednej nogi, regresje |
| `data:validate-data` | bramka 16a: p*, zwrot z mieszanki ścieżek, próg ±B, bilans lejka, red flag „na styk" |
| `data:statistical-analysis` | bramka 16b: CI zwrotu, mediana obok średniej, test parowany, N_eff |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Z tabeli zasady 19 pominięte: `dataviz` (bez wykresów), `update-config` (bez zmian w ustawieniach
Claude Code), `data:explore-data` (te same parquety co W1; filtr daty sprawdzony testem),
`ta-toolkit` (następna runda, nie ta).
