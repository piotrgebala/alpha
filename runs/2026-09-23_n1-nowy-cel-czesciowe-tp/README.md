# N1 — nowy cel modelu: częściowe wyjście 50 % + stop na wejściu (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed kodem).** Wszystko do sekcji „Czego ta runda NIE raportuje"
> włącznie zapisano **przed napisaniem linijki kodu produkcyjnego** i trafia do repo w osobnym
> commicie, który poprzedza commit z kodem. Sekcje od „Wynik" w dół dopisuje się po przebiegu.
> W rozmowie runda nazywana była „W2"; dostaje ID **N1**, bo to NOWA HIPOTEZA (nowy cel), a seria
> W (wykonanie) jest zamknięta regułą STOP — własny licznik od zera (wniosek skumulowany 13).

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
- **Skrypt rundy:** `backtest/run_partial_tp_n1.py` (powstaje PO tej pre-rejestracji; komenda
  w formie uruchamialnej trafi tu przy zamknięciu, razem z wpisem na `runs/ZAMROZONE.txt`).
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
   wypełnienie na otwarciu; w świecy zdarzenia `T_near` (gdy nie na otwarciu) po częściowym
   wyjściu liczy się w tej samej świecy **tylko stop na `E`**, `T_far` dopiero od następnej
   świecy — konserwatywnie, tak jak dla wypełnienia. Obie bariery w jednej świecy → reguła
   etykiety (bliższa otwarciu pierwsza).
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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz w2-nowy-cel`)_
