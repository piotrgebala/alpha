# R1 — premia rebalansowa: czy codzienne wyrównywanie koszyka zarabia ponad trzymanie? (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Uniwersum sprofilowane (skill `data:explore-data`),
> rachunek mocy policzony z WARIANCJI PRZEKROJOWEJ dziennych zwrotów i OBROTU (własności danych) —
> **średnia premia ani żaden wynik strategii nie były liczone**. Kod pomiaru i przebieg następują
> PO commicie tego pliku. Punkt 2 zlecenia użytkownika 2026-09-23: „inny cel niż kierunek" —
> rodzina B2 katalogu (premia rebalansowa), status NIETKNIĘTE.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Pomysł:** weź koszyk 20 największych (po obrocie) kryptowalut w równych częściach. Ceny każdego
dnia rozjeżdżają się — jedne rosną, inne spadają. Jeśli **codziennie** wyrównujemy udziały
z powrotem do równych (sprzedajemy trochę tego, co urosło, dokupujemy tego, co spadło), to przy
ruchach, które się odwracają, zarabiamy więcej niż trzymając koszyk bez ruszania. Przy ruchach,
które trwają (zwycięzcy dalej wygrywają), tracimy. To znany efekt matematyczny, nie prognoza
kierunku rynku — **inny cel niż kierunek**, o który prosił użytkownik.

**Jak mierzymy:** ten sam koszyk (skład wybierany na początku każdego miesiąca wyłącznie
z danych sprzed tego miesiąca), dwie wersje: A — wyrównywana codziennie, B — wyrównana tylko
na początku miesiąca i trzymana. Premia dnia = zwrot A − zwrot B − koszt obrotu A (opłata spot
0,10 % od każdej przesuniętej złotówki). Beta koszyka (czy krypto rosło) się skraca — pytamy
tylko o to, ile daje samo wyrównywanie.

**Czego się spodziewamy (przed wynikiem):** przy ruchach niezależnych z dnia na dzień premia
brutto jest dodatnia (rząd kilku–kilkunastu procent rocznie przy tak zmiennych aktywach), koszt
obrotu to ok. 0,9 % rocznie. Ale krypto ma w środku miesiąca tendencję do kontynuacji ruchów
względnych, która może premię zjeść albo odwrócić. **Nie wiemy, który efekt wygra — o to pytamy.**

**Czym ten wynik NIE jest:** nie mówi, czy warto mieć koszyk krypto (to zależy od beta rynku,
poza pytaniem); mówi, czy — mając koszyk — warto go codziennie wyrównywać.

---

## ID testu

**R1** — nowa hipoteza (rodzina B2), własny licznik: **1 wariant** (rebalans codzienny vs brak
wewnątrz miesiąca). Po rundzie: **1/1, STOP** (niżej).

## Metadane

- **Gałąź:** `r1-premia-rebalansowa` (od master `087471f`).
- **Dane:** uniwersum z P2 (`data/raw/universe/<SYMBOL>_1d.parquet`, `data.binance.vision` +
  `/fapi/v1/klines` 1d, 2020-01 → 2026-06-30, **z wycofanymi**): 281 symboli z danymi,
  255 366 wierszy; kolumny `open_time` (dzień UTC), `close`, `quote_volume`. Ceny perpetuali
  jako **proxy cen spot** (baza ±0,05 %, C1) — koszyk modelowany jako spot (bez fundingu).
- **Zasada 20:** pomiar od **2021-02-01** (lookback obrotu 30 dni mieści się w 2021) do
  2026-06-30: 65 koszyków miesięcznych, 1 976 dni.
- **Uniwersum point-in-time:** na początku każdego miesiąca `m` symbole `*USDT` bez
  stablecoinów jako bazy (`fetch_universe.STABLE_BASES`; kontrakty TRADIFI wykluczone na etapie
  pobrania), z ≥ 30 dniami historii przed `m`, **top-20 po średnim obrocie z 30 dni przed `m`**
  (jak P2: poprawka 1 użytkownika — 20 monet; `VOLUME_LOOKBACK_DAYS = 30`, `MIN_HISTORY_DAYS = 30`).
  Skład trzymany do końca miesiąca; wycofanie w trakcie miesiąca = gotówka (zwrot 0) w obu
  strategiach (16 przypadków w całym zbiorze).
- **Koszty:** opłata spot 0,10 % (`costs.spot_fee_rate`) × obrót dzienny strategii A
  (`Σ|w'_i − 1/N|` po zwrotach dnia); obrót na starcie miesiąca (zmiana składu) jest wspólny dla
  A i B i się skraca; B nie płaci za reset dryfu na starcie miesiąca (założenie konserwatywne
  wobec A — pomijamy koszt, który obciążałby B).
- **Kod:** czyste funkcje w `backtest/rebalance_premium.py` z testami; skrypt
  `backtest/run_rebalance_premium_r1.py` (po tej pre-rejestracji; komenda przy zamknięciu, wpis
  na `runs/ZAMROZONE.txt`). N_eff z `agents.labeling.effective_sample_size` (≤ n).

## Profil danych (skill `data:explore-data`, przed pomiarem)

| co | wynik |
|---|---|
| pliki / symbole z danymi / wiersze | 287 / 281 / 255 366; 2020-01-01 → 2026-06-30 |
| duplikaty (symbol, dzień) / close ≤ 0 / NaN close | 0 / 0 / 0; siatka dzienna UTC 00:00 |
| symbole z danymi per rok | 2020: 41, 2021: 70, 2022: 82, 2023: 115, 2024: 162, 2025: 245, 2026: 265 |
| dziury wewnątrz szeregu | 0 symboli |
| szeregi zakończone przed końcem (wycofane) | 16, wszystkie w środku miesiąca → obsługa „gotówka" |
| `quote_volume == 0` | 14 424 wierszy (dni bez obrotu na małych kontraktach; nie wchodzą do top-20) |
| dni ze zwrotem > 100 % / < −80 % | 42 / 3 (realne pompki i krachy: np. +520 %, −93 %) — zostają; top-20 po obrocie może je zawierać |
| koszyki miesięczne 2021-02 → 2026-06 | 65, zawsze 20 członków; 119 różnych symboli |
| wariancja przekrojowa dzienna `CSV = mean_i (r_i − r_p)²` | średnio 0,157 %² → **½·CSV = 0,0785 %/dzień = 28,7 %/rok** — GÓRNA granica premii (wobec trzymania każdego aktywa osobno) |
| obrót dzienny `E|r_i − r_p|` (≈ Σ|Δw| przy równych wagach) | **2,38 %/dzień → koszt 0,0024 %/dzień = 0,87 %/rok** |
| szum: std(½·CSV) | 0,121 %/dzień → `se ≈ 0,0027 %/dzień` przy n = 1 976 (proxy) |

## Poprzedzające wyniki (zasada 14)

- **P2 (wniosek 40):** to samo uniwersum i te same reguły doboru; nauczyło, że 20 monet ≈ 2
  niezależne (ρ ≈ 0,47) — tu breadth nie mnoży próby, ale premia rebalansowa ŻYWI SIĘ dyspersją,
  więc korelacja obniża oczekiwaną premię (σ_p² bliżej σ̄²), nie próbę.
- **M1 (wniosek 35):** momentum czasowe na BTC 4h — brak. Tu chodzi o momentum PRZEKROJOWE
  wewnątrz miesiąca (czy relatywni zwycięzcy dalej wygrywają) — inna rzecz; literatura
  (Liu–Tsyvinski–Wu 2022) znajduje momentum przekrojowe na horyzoncie tygodni, co działa
  PRZECIW premii rebalansowej.
- **C1 (wnioski 54–56):** rachunek mocy musi brać autokorelację SYGNAŁU — tu szereg premii
  dziedziczy klastrowanie zmienności; N_eff liczone ex post.
- **Katalog B2:** post QuantConnect Research 2022 (FTX top-25, rebalans dzienny, bez OOS) —
  prior, nie wynik; „koszt obrotu zjada premię; próg z turnoveru PRZED" — policzony wyżej.

## Rozstrzygnięcia projektowe (zapisane PRZED przebiegiem)

### Pięć pól katalogu

| pole | wartość |
|---|---|
| zbiór informacyjny | OHLCV WIELU aktywów (ceny + obrót do doboru) |
| formuła | przekrojowa (koszyk równych wag) |
| target | **premia rebalansowa** (względna: A − B), nie kierunek |
| horyzont | dzienny rebalans, skład miesięczny |
| status | NIETKNIĘTE (B2) |

**Mechanizm jednym zdaniem:** wyrównywanie wag sprzedaje relatywnych zwycięzców i kupuje
przegranych — zarabia, gdy ruchy względne się odwracają (wariancja zamieniona w zysk), traci,
gdy trwają; po drugiej stronie nie ma „kontrahenta" — jest struktura procesu cen.

### Definicja (identyczna w kodzie i tutaj)

Dla miesiąca `m` ze składem `S_m` (N = 20) i dni `t` w miesiącu, `r_it` = zwrot zamknięcia
dnia `t` względem dnia `t − 1` (wycofany = 0 po ostatniej cenie):

```
r_A,t   = (1/N) Σ_i r_it                              (równe wagi codziennie)
r_B,t   = Σ_i w_i,t−1 · r_it ;  w_i,t = w_i,t−1 (1 + r_it) / (1 + r_B,t) ;  w_i,start = 1/N
turnover_t = Σ_i | (1 + r_it) / (N (1 + r_A,t)) − 1/N |
premium_gross_t = r_A,t − r_B,t ;   premium_net_t = premium_gross_t − fee · turnover_t
```

Jednostki: ułamek wartości koszyka na dzień; rocznie ×365.

### Kryterium — zapisane PRZED uruchomieniem (jedno ramię)

Statystyka nośna: średnia dzienna `premium_net` z CI 95 % (se z N_eff ≤ n) i `t_neff`; próg 0.

- **POZYTYWNY:** `t_neff > 1,96` (dolny kraniec CI nad zerem). Raport z roczną premią netto i CI;
  o materialności (czy kilka procent rocznie warte jest infrastruktury 20-monetowego koszyka spot)
  decyduje użytkownik.
- **NEGATYWNY:** górny kraniec CI 95 % poniżej zera (rebalans SZKODZI — momentum względne wygrywa).
- **NIEROZSTRZYGNIĘTY:** wszystko inne.
- **Granica dużego n:** monotoniczne; przy prawdziwym efekcie 0 zapala się ≤ α.
- **Obserwacje (nie kryteria):** premia brutto vs koszt; per rok; udział dni/miesięcy z premią
  netto > 0; skumulowany zwrot obu wersji koszyka (beta — opisowo); zależność premii od CSV.

### Rachunek mierzalności (zasada 18)

`n = 1 976` dni. Szum (proxy ½·CSV): se ≈ 0,0027 %/dzień → wykrywalny efekt (moc 80 %)
≈ 0,0076 %/dzień = **2,8 %/rok**; N_eff ex post może to pogorszyć (klastrowanie zmienności —
lekcja C1). Sygnał: górna granica 28,7 %/rok, koszt 0,87 %/rok. Werdykt: **MIERZALNA** dla
premii netto rzędu ≥ 3 %/rok; premia mniejsza byłaby niewidzialna — i zapisujemy to z góry.

### Reguła STOP (seria R)

Po R1: 1/1. Zakazane po wyniku: inne N, inny lookback obrotu, inna częstość rebalansu
(tygodniowa, progowa), wagi kapitalizacyjne, filtry składu (bez memecoinów), inne opłaty.
Pozytyw = decyzja użytkownika o produkcie koszykowym (inżynieria: dostępność spot, płynność
małych monet, podatki), nie runda.

### Arytmetyka oczekiwań

- Jeśli zwroty względne są niezależne z dnia na dzień: premia brutto wobec B (reset miesięczny)
  to ułamek górnej granicy — dryf wag narasta w miesiącu, więc rząd 20–40 % z 28,7 % ≈ 6–11 %/rok;
  netto ~5–10 %/rok → POZYTYWNY.
- Jeśli wewnątrz miesiąca dominuje momentum przekrojowe (LTW 2022 na tygodniach): premia
  bliska zeru lub ujemna → NIEROZSTRZYGNIĘTY/NEGATYWNY. **Prawdziwy prior: niepewny co do znaku.**
- Red flag zapisany z góry: premia > górnej granicy 28,7 %/rok = błąd (np. wycofane liczone jako
  −100 % w B, a 0 w A); premia dokładnie ≈ ½·CSV = błąd (B liczone jako średnia aktywów zamiast
  koszyka).

### Czego runda NIE raportuje i NIE interpretuje

Czy koszyk krypto jest dobrą inwestycją (beta); fundingu perpetuali (koszyk = spot); dostępności
spot dla każdej z 119 monet; poślizgu przy 2,4 % obrotu dziennie na małych monetach (opłata 0,10 %
+ 0 bp poślizgu — założenie optymistyczne, zapisane); podatków od 365 rebalansów.

### Kogo NIE ma w zbiorze

Symbole z < 30 dniami historii przed miesiącem; spoza top-20 obrotu; stablecoiny; TRADIFI;
dni sprzed 2021-02; wycofane po ostatniej cenie (gotówka); dni z `quote_volume = 0` w top-20
(nie występują z konstrukcji doboru).

## Definition of Done tej rundy

`backtest/rebalance_premium.py` (czyste funkcje) + testy (przykład dwuaktywowy z premią dokładnie
x², trend → B wygrywa, identyczne zwroty → 0, wycofanie w środku miesiąca, brak lookaheadu
w doborze, hypothesis: obrót ≥ 0, N = 1 → 0, tożsamość brutto; fail loud przy < top_n);
skrypt = neutralny reporter; bramki 16a–c; `raw_output.txt`; INDEX (wiersz, licznik R 1/1,
wnioski); STATUS; README (kamień milowy); ZAMROZONE; „Użyte skille".

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz r1-premia-rebalansowa`)_
