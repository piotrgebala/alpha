# R1 — premia rebalansowa: czy codzienne wyrównywanie koszyka zarabia ponad trzymanie? (2026-09-23)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTA wg kryterium, punktowo UJEMNA; oczekiwanie z modelu
> „ruchy niezależne" wykluczone.** Kolejność w gicie: pre-rejestracja `fb18d98` → kod `f4569bd`
> (scommitowany z jednym padającym testem — kod wyjścia `pytest` zamaskowany potokiem; naprawa
> testu i etykiety `db16af7` PRZED przebiegiem końcowym) → przebieg → wynik w commicie scalającym.
> Seria R: **1/1, STOP.** Walidacja (16a): **READY**; przegląd diffu (16c): **Approve**.

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Codzienne wyrównywanie koszyka 20 największych kryptowalut nie zarabia ponad zwykłe trzymanie —
raczej traci.** Przez 5,4 roku (65 miesięcy) wersja wyrównywana codziennie skończyła o **12 %
niżej** niż ta sama, trzymana bez ruszania w miesiącu. W przeliczeniu na rok: **−3,6 % netto,
przedział od −9,5 % do +2,4 %** — przedział obejmuje zero, więc formalnie „nierozstrzygnięte",
ale wyklucza to, czego uczy podręcznik: przy ruchach niezależnych z dnia na dzień wyrównywanie
powinno dawać 6–11 % rocznie brutto (górny kraniec przedziału brutto to +3,3 %).

**Dlaczego:** wyrównywanie sprzedaje to, co urosło, i dokupuje to, co spadło. To zarabia, gdy ruchy
względne się odwracają, a traci, gdy trwają. W krypto w skali dni–tygodni **ruchy względne raczej
trwają** (zwycięzcy dalej wygrywają) — i to zjada całą premię z „handlu zmiennością", a nawet
więcej. Koszty obrotu (0,9 % rocznie) są tu drugorzędne.

**Zastrzeżenia:** wynik dotyczy koszyka 20 monet po obrocie (od 2021 w tym koszyku jest dużo monet
spekulacyjnych: 119 różnych symboli, pompki +520 % w jeden dzień), rebalansu dziennego i opłaty
0,10 %. Dni z ogromną dyspersją dają duży szum (rozdzielczość 8,5 % rocznie zamiast planowanych
2,8 %), więc małej dodatniej premii (do ~2 % rocznie) wykluczyć nie umiemy — ale takiej nie warto
zbierać przy 2,4 % obrotu dziennie na 20 monetach spot.

---

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
- **Kod:** czyste funkcje w `backtest/rebalance_premium.py` z testami (7, w tym hypothesis).
  **Komenda:** `py -m backtest.run_rebalance_premium_r1` (Windows: `PYTHONUTF8=1`; czyta tylko
  cache i config; pełny output `raw_output.txt`; skrypt na `runs/ZAMROZONE.txt`; czas 1 s).
  N_eff z `agents.labeling.effective_sample_size` (≤ n), przez `carry_hedged.summarize_pnl`
  z parametrami `periods_per_year = 365`, `capital_per_notional = 1`.

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

### 1. Kryterium (jedno ramię, próg 0)

| miara | netto | brutto |
|---|---|---|
| średnia dzienna premia | **−0,00973 %** | −0,00736 % |
| CI 95 % (N_eff = n = 1 976) | [−0,02604; +0,00657] | [−0,02366; +0,00895] |
| mediana | −0,00186 % | 0,00000 % |
| t / t_neff | −1,17 / −1,17 | −0,88 |
| rocznie ×365 | **−3,55 % [−9,50; +2,40]** | −2,68 % [−8,64; +3,27] |
| koszt obrotu | 0,00238 %/dzień = **0,87 %/rok** | |

**Odczyt kryterium: NIEROZSTRZYGNIĘTY** (CI netto obejmuje zero). **Ale scenariusz 1 z arytmetyki
oczekiwań** (ruchy względne niezależne → 6–11 %/rok brutto) **leży poza CI brutto** (górny kraniec
+3,3 %/rok) — zapisany przed wynikiem, więc wolno powiedzieć: dane odrzucają model „volatility
pumping" dla tego koszyka; realizuje się scenariusz 2 (momentum względne wewnątrz miesiąca).

### 2. Dekompozycja i kontekst

Σ premia brutto −14,53 %, Σ koszty 4,70 %, Σ netto −19,23 % (sumy dziennych ułamków). Obrót
dzienny A: średnia 2,38 %, mediana 2,06 %, p95 4,88 %. Koszyk A skumulowany −79,7 %, koszyk B
−76,9 % (beta rynku — poza pytaniem); **wartość A względem B: −12,13 %** przez 5,4 roku. Dni
z premią netto > 0: 48,2 %; miesiące z dodatnią sumą: 36 z 65. Rozkład ciężkoogonowy:
|premia| p50 0,076 %, p95 0,67 %, max 5,1 % (pompki); 39 dni z |premią| > 1 % sumują się do
−2,64 % z −14,53 % — ogony nie robią wyniku, robi go masa zwykłych dni.

### 3. Per rok (opisowo)

| rok | dni | netto/rok | brutto/rok | koszt/rok | obrót/dzień | koszyk A | koszyk B |
|---|---|---|---|---|---|---|---|
| 2021 (od lutego) | 334 | −12,7 % | −11,6 % | 1,1 % | 3,04 % | +143 % | +167 % |
| 2022 | 365 | +3,0 % | +3,7 % | 0,8 % | 2,10 % | −82 % | −83 % |
| 2023 | 365 | −4,4 % | −3,7 % | 0,7 % | 1,92 % | +75 % | +80 % |
| 2024 | 366 | −1,1 % | −0,2 % | 0,9 % | 2,42 % | +24 % | +24 % |
| 2025 | 365 | −1,1 % | −0,2 % | 0,9 % | 2,46 % | −52 % | −52 % |
| 2026 (do 30.06) | 181 | −8,0 % | −7,1 % | 0,9 % | 2,37 % | −54 % | −53 % |

W latach hossy alt-ów (2021, 2023) rebalans traci najwięcej — zwycięzcy trwają; w 2022 (bessa)
premia dodatnia. Bez werdyktów per rok.

### 4. Mierzalność — ex ante vs ex post

Ex ante: se 0,0027 %/dzień (proxy ½·CSV) → wykrywalne 2,8 %/rok. Ex post: sd premii netto
**0,370 %/dzień** (3× proxy), N_eff = n (autokorelacja lag-1 −0,17), se 0,0083 % → wykrywalne
**8,5 %/rok**. Proxy z wariancji przekrojowej niedoszacowało szumu: premia dnia to różnica dwóch
koszyków z dryfującymi wagami, której rozrzut rośnie z dyspersją, nie ½·CSV. Werdykt
„nierozstrzygnięty" jest w połowie skutkiem tej rozdzielczości — zapisane jako lekcja
(wniosek 58); przewidywanie i.i.d. i tak jest wykluczone.

## Co na plus (+)

- **Pytanie „inny cel niż kierunek" dostało odpowiedź na własnym przyrządzie** (różnica dwóch
  wersji tego samego koszyka — beta skrócona), z jednym wariantem, bez dobierania N/lookbacku.
- **Uniwersum bez błędu przeżywalności** (wycofane obecne do ostatniej ceny, skład point-in-time
  z testem braku lookaheadu), 65 koszyków, 119 symboli.
- **Definicja premii jest czystą funkcją z testami:** x² na ruchach odwracających się, trend →
  b&h wygrywa, identyczne zwroty → 0, gotówka po wycofaniu, hypothesis.
- **Scenariusze zapisane przed wynikiem rozstrzygają interpretację:** nie „nic nie wyszło", tylko
  „model niezależnych ruchów odrzucony, momentum względne potwierdzone" — spójne z literaturą
  (momentum przekrojowe w krypto na tygodniach, LTW 2022).

## Co na minus (−)

- **Rozdzielczość 8,5 %/rok** (3× gorsza niż planowana): premia ≤ ~2 %/rok netto nie jest
  wykluczona; ale przy 2,4 % obrotu dziennie na 20 monetach spot taka premia nie ma sensu
  operacyjnego.
- **Ceny perp jako proxy spot** (baza ±0,05 %) i **poślizg 0 bp** — optymistyczne wobec realnego
  handlu memecoinami; kierunek obciążenia na korzyść rebalansu, więc wynik ujemny by się pogłębił.
- **Koszyk „top-20 po obrocie" to od 2024 w dużej mierze monety spekulacyjne** — wynik nie
  przenosi się automatycznie na koszyk „blue chip"; inny skład = nowa hipoteza (STOP).
- **Proces:** kod trafił do commita z padającym testem (asercja z błędną wartością oczekiwaną),
  bo `pytest -q | tail` zamaskował kod wyjścia; naprawa w osobnym commicie PRZED przebiegiem
  końcowym, przebieg powtórzony (deterministyczny). Lekcja: `set -o pipefail` w łańcuchach.
- Skrypt drukował „różnicę wzrostu skumulowanego −2,8 pp" (różnica zwrotów) — mylące; zmienione
  na iloraz wartości (−12,13 %) przed zamrożeniem.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Drugą drogą:** `ln(W_A/W_B)` = **−12,93 %** wobec Σ premii brutto (−14,53 %) minus człon
  wariancji ½Σ(r_A² − r_B²) (−1,83 %) = −12,71 % ✔ (reszta = wyrazy trzeciego rzędu; W_A 0,2032,
  W_B 0,2312, iloraz 0,8787 → −12,13 %); Σ netto = −14,53 − 4,70 = **−19,23 %** ✔; rocznie
  = −0,00973 % × 365 = **−3,55 %** ✔; koszt = 0,10 % × 2,38 % × 365 = **0,87 %** ✔; ogony:
  39 dni > 1 % → −2,64 % (18 % sumy) ✔.
- **Znak definicji:** test „ruchy odwracające się → rebalans wygrywa o x²" i „trend → b&h wygrywa"
  przechodzą; górna granica ½·CSV (28,7 %/rok) nie została przekroczona (średnia brutto ujemna);
  premia ≠ ½·CSV (B liczone jako koszyk z dryfem, nie średnia aktywów) ✔ — oba red flagi z
  pre-rejestracji nie zapaliły się.
- **Kogo NIE ma:** symbole spoza top-20 (162 z 281), < 30 dni historii przed miesiącem,
  stablecoiny, TRADIFI (odsiane przy pobraniu), styczeń 2021, wycofane po ostatniej cenie
  (gotówka — symetrycznie), poślizg.
- **Red flag „idealnie potwierdza":** nie — prior był niepewny co do znaku; wynik ujemny.
  Sprawdzono, czy to nie artefakt kilku dni: bez 39 dni |premia| > 1 % suma nadal −11,9 %.
- **Rząd wielkości:** obrót 2,4 %/dzień jak ex ante (2,38 %), koszt 0,87 % jak ex ante, koszyki
  −80 % (alt-y 2021→2026) plausible.

## Przegląd diffu (zasada 16c) — werdykt: **Approve** (po naprawie testu)

Zakres: `backtest/rebalance_premium.py` (nowy), `tests/test_rebalance_premium.py` (7),
`backtest/run_rebalance_premium_r1.py`, `backtest/carry_hedged.py` (`summarize_pnl` z parametrami
annualizacji — wartości domyślne = C1, zgodność wsteczna; testy C1 zielone), README rundy.

**Korektność:** (1) `monthly_members`: okno `[m − 30 dni, m)` — żadnych danych z `m` ani później
(test z „przyszłym" obrotem 10¹²); ≥ 30 notowań; ranking (−obrót, nazwa) deterministyczny; fail
loud < top_n. (2) `daily_premium`: `r_A = mean`, `r_B = w·r` z dryfem `w ← w(1+r)/(1+r_B)`;
turnover po zwrotach dnia; NaN → 0 (gotówka) symetrycznie; `n_active` z surowych NaN. (3)
Skrypt: tylko cache; annualizacja arytmetyczna ×365 (zapisana); iloraz A/B zamiast różnicy
zwrotów. (4) Stare testy: 701 → 708.

**Edge-case'y:** N = 1 → premia i obrót 0 (hypothesis); brak plików → `ValueError`; duplikaty
(symbol, dzień) → `ValueError`; wycofanie w 1. dniu miesiąca → 0 zwrot od razu (gotówka).

**Uwagi (bez blokady):** pętla dzienna w Pythonie (1 976 × 20) — 1 s, OK; `eligible_symbols`
nie odsiewa TRADIFI (odsiane przy pobraniu — zapisane w docstringu); przy innym źródle uniwersum
trzeba to dodać.

**Werdykt jednym zdaniem:** kod poprawny, definicja z pre-rejestracji odtworzona w testach, bez
lookaheadu w doborze składu — **Approve**, do scalenia; usterka testu i proces `pipefail`
odnotowane.

## Wniosek

Codzienne wyrównywanie koszyka top-20 kryptowalut **nie zarabia ponad trzymanie w miesiącu:
−3,6 %/rok netto [−9,5; +2,4], −12 % wartości względnej przez 5,4 roku**, dodatnia premia tylko
w 36 z 65 miesięcy. Wynik jest formalnie nierozstrzygnięty (rozdzielczość 8,5 %/rok przez ciężkie
ogony dyspersji), ale wyklucza podręcznikową premię z „handlu zmiennością" (6–11 %/rok brutto
przy ruchach niezależnych): w krypto ruchy względne wewnątrz miesiąca **trwają**, a wyrównywanie
sprzedaje zwycięzców za wcześnie. Inny cel niż kierunek — premia rebalansowa — zamknięty
(seria R 1/1). Razem z C1: z dwóch celów „nie-kierunkowych" jeden (carry z hedgem) daje
kontraktowy przepływ, drugi (premia z rebalansu) nie daje nic.

## Rekomendacja

1. **Nie budować koszyka z dziennym rebalansem** na tym uniwersum; nie testować wariantów
   (tygodniowy rebalans, top-10 „blue chip", wagi kapitalizacyjne, progi) — każdy to nowy los,
   a mechanizm (momentum względne) działa przeciw wszystkim wersjom rebalansu „do równych wag".
2. **Jeśli momentum przekrojowe wewnątrz miesiąca jest realne, to jest to ODWROTNA hipoteza
   (rodzina B1 katalogu: ranking i trzymanie zwycięzców)** — ale to nowa hipoteza post hoc
   względem tej rundy (wniosek 49) i wymaga własnej pre-rejestracji, uniwersum point-in-time,
   modelu kosztów shorta i decyzji użytkownika; prior z literatury (LTW 2022) jest umiarkowanie
   dodatni na horyzoncie tygodni.
3. **Metodologicznie (wniosek 58):** rachunek mocy dla RÓŻNICY dwóch strategii z proxy
   analitycznego niedoszacowuje szumu 3×; liczyć z symulowanego szeregu różnic na danych
   (bez patrzenia na średnią) albo z ogonów dyspersji. Procesowo: `set -o pipefail` przy
   `pytest | tail`.
4. **Punkt 2 zlecenia zamknięty:** carry (C1), inny cel (R1), pozycjonowanie (kolektor aktywny).
   Następny ruch należy do użytkownika: produkt cash-and-carry (decyzja bramkowa) albo nowe
   źródło informacji (pozycjonowanie za ~3 lata, on-chain — brama danych).

## Użyte skille

Rejestr gałęzi `r1-premia-rebalansowa` (`py tools/skill_audit.py raport --galaz r1-premia-rebalansowa`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → profil → pre-rejestracja → kod → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | przyrząd dla targetu względnego (różnica strategii), próg 0, N_eff, „kto traci" dla premii strukturalnej, jedna zmienna |
| `anthropic-skills:quant-strategy-catalog` | rodzina B2, pięć pól, pułapki (post 2022 bez OOS, obrót zjada premię, próg z turnoveru PRZED), związek z B1 |
| `data:explore-data` | profil panelu uniwersum przed pomiarem (dziury, duplikaty, wycofania, pompki, siatka UTC) |
| `engineering:testing-strategy` | plan testów PRZED kodem (x², trend, identyczne, wycofanie, lookahead składu, hypothesis, fail loud) |
| `data:validate-data` | bramka 16a: tożsamość ln(W_A/W_B), sumy, koszt, ogony, red flagi znaku; wykrycie mylącej etykiety |
| `data:statistical-analysis` | bramka 16b: mediana obok średniej, ogony, per rok, jak nazwać „nierozstrzygnięty z wykluczonym scenariuszem" |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu"; wychwycenie padającego testu i maskowania kodu wyjścia) |

Z tabeli zasady 19 pominięte: `dataviz` (bez wykresów), `security-review` (dane z cache, bez
sieci, bez sekretów), `engineering:architecture` (bez decyzji architektonicznej), `ta-toolkit`,
`lean-research`, `update-config`.
