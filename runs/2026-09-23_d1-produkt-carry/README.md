# D1 — produkt cash-and-carry: depozyt, likwidacja, COIN-M, basis kwartalny, stopa T-bill (2026-09-23)

> **STATUS: ZAMKNIĘTA. Wynik: konstrukcja COIN-M (zabezpieczenie w BTC) daje +9,1 %/rok
> [5,9; 12,3] na kapitale 1× BEZ ryzyka likwidacji i bez uzupełnień; USDT-M z depozytem 1×
> i miesięcznym uzupełnianiem: 0 likwidacji, +5,3 % na kapitale 2×; od 2022 tylko COIN-M
> wychodzi ponad T-bill (średnio ~+1,8 pp/rok, od −1,5 do +7,2); basis kwartalny ≈ funding
> (zamyka stopę, nie dodaje zwrotu).** 0 wariantów reguł, poza licznikami hipotez; pomiary COIN-M
> i basis = generalizacja C1a na inny instrument (seria C pozostaje STOP dla wariantów REGUŁ).
> Kolejność w gicie: pre-rejestracja + kod `93b3c6e` → przebieg → **Poprawka 1** (koszt
> uzupełnień depozytu, brakujący w pre-rejestracji; pierwszy wydruk zachowany jako
> `raw_output_przed_poprawka1.txt`) → przebieg końcowy → wynik w commicie scalającym.
> Walidacja (16a): **READY**; przegląd diffu (16c): **Approve**. Decyzja o produkcie (realny
> kapitał) należy do użytkownika. Decyzja użytkownika 2026-09-23: „sprawdź wszystkie warianty".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Cztery pytania z C1 mają odpowiedzi:**

1. **Depozyt.** Przy depozycie równym wartości pozycji (kapitał 2×) i uzupełnianiu go raz
   w miesiącu przez 5,5 roku **nie doszłoby do żadnej likwidacji** (największe wykorzystanie
   depozytu 71 % z 99,5 %). Mniejszy depozyt oznacza częstsze dopłaty, a te kosztują (przycinanie
   obu nóg): przy depozycie 0,25× i dopłatach codziennych koszt 1,4 % rocznie, a jednodniowy
   skok o 21 % (największy w próbie) zbliża się do progu 24,5 %. Bezpieczna wersja USDT-M to
   depozyt 1×, dopłaty miesięczne: **+5,3 % rocznie na kapitale**.
2. **Wersja w bitcoinie (COIN-M) rozwiązuje problem depozytu.** Zabezpieczeniem jest sam
   bitcoin, wartość pozycji w dolarach jest stała (tożsamość algebraiczna, sprawdzona testem),
   więc nie ma czego likwidować ani dopłacać, a kapitał to 1×. Opłata jest tam trochę niższa
   (o 1,8 pp rocznie), ale na kapitale wychodzi **+9,1 % rocznie [5,9; 12,3]** zamiast 5,4 %.
3. **Kontrakt kwartalny nie daje więcej** — stopa zamknięta na wejściu (mediana 5,9 % rocznie)
   jest z grubsza tym, co potem i tak płaci funding (różnica mediany +1,8 pp przy wejściu 30 dni
   przed wygaśnięciem, −0,9 pp przy 90 dniach; rozrzut od −19 do +17 pp). Zyskuje się pewność
   stopy, nie jej wysokość.
4. **Ponad lokatę w dolarze** (bony 3M: 2022 2,0 %, 2023 5,1 %, 2024 5,0 %, 2025 4,1 %):
   wersja USDT-M z kapitałem 2× od 2022 **nie wychodzi** ponad bony (średnio −1,0 pp rocznie);
   wersja COIN-M wychodzi **średnio o +1,8 pp rocznie**, ale z rozrzutem od −1,5 (2026 H1)
   do +7,2 (2024) — to pięć obserwacji rocznych, nie prognoza.

**Czego to nie zmienia:** ryzyko giełdy (kapitał i coiny na Binance), podatki, koszt operacyjny
nadzoru pozycji i to, że w 2021 opłaty były 3–10× wyższe niż później — poza pomiarem. Decyzja
o produkcie należy do użytkownika.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

C1 pokazało, że trzymanie bitcoina i jednoczesna krótka pozycja na kontrakcie wieczystym
zbiera opłatę funding (odsetki, które płacą gracze z dźwignią). Ale C1 zostawiło cztery
pytania, bez których nie da się podjąć decyzji o produkcie:

1. **Ile depozytu trzeba trzymać pod krótką pozycję i jak często by ją zlikwidowano?**
   Krótka pozycja traci, gdy cena rośnie; jeśli strata przekroczy depozyt, giełda zamyka
   pozycję (likwidacja). Sprawdzamy na historii cen od 2021: przy jakim depozycie i jak
   częstych dopłatach nie doszłoby do likwidacji.
2. **Czy wersja rozliczana w bitcoinie (COIN-M) nie rozwiązuje problemu likwidacji?** W tej
   wersji zabezpieczeniem jest sam bitcoin, a wartość całej pozycji w dolarach jest stała
   — nie ma czego likwidować, a kapitał to 1× zamiast 2×. Pytanie: czy opłata jest tam
   podobna.
3. **Czy kontrakt kwartalny nie jest lepszy?** Tam stopę zna się z góry (różnica ceny
   kontraktu i spotu, „basis") i zamyka w dniu wygaśnięcia. Porównujemy stopę zamkniętą na
   wejściu z tym, co w tym samym oknie faktycznie wypłacił funding.
4. **Ile z tego zostaje ponad bezpieczną lokatę w dolarze?** Porównanie rok po roku ze stopą
   amerykańskich bonów skarbowych (T-bill 3M).

Wynik to tabele i przedziały, nie „werdykt" — decyzja o produkcie (realny kapitał) należy
do użytkownika.

## ID testu

**D1** — analiza produktu; **0 wariantów reguł, POZA licznikami hipotez.** Warunek: żadna
reguła wejścia/wyjścia poza „zawsze w pozycji" (C1a); pomiary COIN-M i basis raportowane
jako generalizacja C1a (inny instrument, ta sama reguła), z jawnym odnotowaniem w INDEX.

## Metadane

- Branch: `d1-produkt-carry` (od `master` @ `71797d2`).
- Dane (wyłącznie cache, zasada 20: `2021-01-01 → 2026-07-01`): perp USDT-M 8h i spot 8h
  (cache C1), funding USDT-M (cache), **funding COIN-M** `BTCUSD_PERP` (P3, `floor("8h")`),
  **kontrakty kwartalne** `binance_um_dated_BTCUSDT_8h` (P3; filtr `open_time < expiry + 8h`
  i `volume > 0`), **FRED DTB3** (P3).
- Koszty (config, jak C1): spot 0,10 %, perp taker 0,05 %, poślizg 0,02 % na nogę →
  0,19 % nominału na wejście i tyle samo na wyjście (COIN-M: ta sama stawka perp).
  Likwidacja: opłata 1,25 % nominału (Binance USDT-M, górna stawka) + ponowne wejście nogi
  perp 0,07 %.
- Kod: czyste funkcje w `backtest/carry_product.py` z testami (12, w tym hypothesis:
  tożsamość wartości USD pozycji COIN-M dla dowolnej ścieżki cen). **Komenda:**
  `py -m backtest.run_carry_product_d1` (Windows: `PYTHONUTF8=1`; czyta tylko cache; 0,3 s;
  pełny stdout `raw_output.txt`; skrypt na `runs/ZAMROZONE.txt`).
  Przyrząd statystyczny dla Q2: `backtest/carry_hedged.summarize_pnl` (jak C1).
- **Poprawka 1 (po pierwszym przebiegu, przed zamrożeniem):** pre-rejestracja Q1 pominęła
  koszt UZUPEŁNIEŃ depozytu — uzupełnienie to przycięcie obu nóg do nominału USD sprzed ruchu
  (obrót `|P_t/P_ref − 1|` × 0,19 %). Dodane do `liquidation_events`/`margin_grid` (kolumny
  „obrót uzup." i „koszt uzup./rok"), test, przebieg powtórzony (deterministyczny); pierwszy
  wydruk zachowany jako `raw_output_przed_poprawka1.txt`. Zmiana dotyczy tylko kolumny
  „rocznie na kapitale" w siatce Q1 (o 0,05–1,43 pp w dół); Q2–Q4 bez zmian.

## Poprzedzające wyniki

- **C1** (`runs/2026-09-23_c1-cash-and-carry/`): C1a +0,0099 %/8h [+0,0063; +0,0135] →
  +10,9 %/rok nominału, +5,4 % kapitału (2×); Σ funding 60,2 %, hedge −0,13 %, koszty 0,38 %;
  połowa z 2021; nie mierzone: depozyt/likwidacja (run-up +90 %/30 dni), ryzyko giełdy,
  koszt kapitału. Ta runda domyka trzy z tych czterech (giełda pozostaje poza pomiarem).
- **P3** (`runs/2026-09-23_p3-sonda-zrodel-ii/`): funding COIN-M od 2020-08 (masa punktowa
  42,7 % na 0,0001, acf1 0,67), 24 kontrakty kwartalne (330 pustych świec po wygaśnięciu),
  FRED DTB3 (dni robocze).
- **P2 / wniosek 40**: przekrój nie mnoży próby; **wniosek 56**: N_eff dla przepływu = liczba
  epizodów stawki, nie rozliczeń (acf1 fundingu USDT-M 0,84 → N_eff 286 z 1 095).
- **H2.0**: carry na BTC z samym fundingiem żyje tylko z hedgem — C1 to potwierdziło.

## Pre-rejestracja: pytania i wyjścia (zapisane przed wynikiem)

### Q1 — depozyt i likwidacja krótkiej nogi USDT-M (z cen perp 8h, 2021 → 2026-07)

- **Run-up:** największy wzrost ceny w oknie 1 / 7 / 30 / 90 dni oraz kwantyle p95/p99
  rozkładu „wzrost w oknie" — bez interpretacji, sam rozkład.
- **Symulacja depozytu:** short perp z depozytem `M` nominału (w USDT) i maintenance `mm = 0,5 %`;
  likwidacja, gdy wzrost ceny od ostatniego uzupełnienia ≥ `M − mm`; po likwidacji pozycja
  odtwarzana od razu po bieżącej cenie (koszt 1,25 % + 0,07 %). Uzupełnienie depozytu do `M`
  (z rezerwy) co `reset` ∈ {nigdy, 30 dni, 7 dni, 1 dzień}. Siatka `M` ∈ {0,25; 0,5; 1,0; 1,5}.
  **Wyjście:** liczba likwidacji, łączny koszt likwidacji (% nominału), maksymalne wykorzystanie
  depozytu między uzupełnieniami, zwrot C1a na kapitale `(1 + M)` po odjęciu kosztów
  likwidacji. Siatka to zakres inżynierski, nie strojenie — nic nie jest „wybierane".
- **Oczekiwanie (przed wynikiem):** przy `M = 1,0` bez uzupełnień likwidacja w 2021 (+330 %
  od dołka); z uzupełnieniem miesięcznym 0 likwidacji (max 30-dniowy run-up +90 % < 99,5 %);
  przy `M = 0,5` miesięczne uzupełnienia nie wystarczą w 2021 (wzrosty > 49,5 %/30 dni).

### Q2 — carry COIN-M (inverse perp, zabezpieczenie w BTC)

- **Konstrukcja:** 1 BTC jako zabezpieczenie + short `N = P₀` USD kontraktów inverse. Wartość
  USD pozycji = `P + N(1 − P/P₀) = P₀` — stała, więc **brak nogi hedge i brak likwidacji przy
  1×** (własność algebraiczna, zapisana jako test). Kapitał = 1× nominał. P&L per 8h =
  funding COIN-M (w USD na nominał); koszty 0,19 % na wejście i wyjście (raz).
- **Przyrząd:** `summarize_pnl(pnl, capital_per_notional=1.0)` — średnia, CI z N_eff ≤ n, per
  rok; obok: to samo dla USDT-M (C1a bez hedge'u, dla porównania stawek) na tym samym oknie.
- **Mierzalność (zasada 18, przed wynikiem):** n = 6 020 rozliczeń; acf1 stawki 0,67 (P3) →
  N_eff ≈ n(1−ρ)/(1+ρ) ≈ 1 190; sd stawki ≈ 0,02 %/8h (P3: p05 −0,009 %, p95 +0,035 %) →
  se ≈ 0,0006 %/8h → half-width ≈ 0,0011 %/8h ≈ **1,2 %/rok**. Pytanie „czy stawka COIN-M różni
  się od USDT-M o więcej niż ~1,5 %/rok" jest **MIERZALNE**; różnice mniejsze — nie, i tak
  zostanie zapisane.
- **Oczekiwanie:** stawki obu rynków są arbitrażowane, więc średnie podobne (rzędu 10 %/rok
  w 2021, 2–6 % później); COIN-M bywa niższy (mniej dźwigni detalicznej).

### Q3 — basis kontraktów kwartalnych (stopa znana na wejściu)

- **Definicja:** dla każdej świecy 8h kontraktu (`open_time < expiry + 8h`, `volume > 0`,
  `days_to_expiry ≥ 7`): `basis = (F − S)/S`, `S` = spot 8h na ten sam znacznik;
  `annualized = basis × 365 / days_to_expiry`. **Front** = kontrakt o najkrótszym czasie
  do wygaśnięcia ≥ 7 dni.
- **Wyjścia:** rozkład annualizowanej bazy frontu per rok (mediana, p25–p75, p05–p95);
  udział dni z bazą ujemną; **porównanie ex post:** dla wejść 90 / 60 / 30 dni przed
  wygaśnięciem — baza zamknięta na wejściu (annualizowana) vs suma fundingu USDT-M
  zrealizowana w tym samym oknie (annualizowana), per kontrakt; mediana i rozstęp różnicy.
  Koszty obu konstrukcji te same (0,19 % wejście + wyjście), depozyt: kontrakty USDT-M —
  jak Q1 (2×).
- **Oczekiwanie:** basis annualizowany zbliżony do fundingu (arbitraż), z mniejszą zmiennością
  w oknie (zamknięty) i sporadycznymi ujemnymi bazami w bessie 2022.

### Q4 — porównanie ze stopą wolną od ryzyka

- Per rok 2021 → 2026 H1: średnia `DTB3` (% p.a., z dni roboczych) obok zwrotu na kapitale:
  C1a USDT-M (2×, z Q1 przy `M = 1,0`, uzupełnienia 30 dni), COIN-M (1×), basis front (2×).
  Kolumna „nadwyżka nad T-bill" = różnica. Bez werdyktu; liczba dla decyzji użytkownika.

### Czego runda NIE robi

Nie wybiera „najlepszego wariantu" po wyniku (siatki są raportowane w całości); nie testuje
reguł przełączania (C1b: NEGATYWNY, seria C STOP); nie modeluje ryzyka giełdy, ADL, podatków,
ani dostępności depozytu w BTC dla USDT-M (tryb multi-asset — zanotowany jako opcja, nie
mierzony). Nie liczy niczego z sygnałem kierunkowym.

---

## Wynik

Dane: 6 021 okresów 8h 2021-01-01 → 2026-07-01 (5,50 roku); C1a odtworzone: +10,87 %/rok
nominału [6,92; 14,81], +5,43 % kapitału 2×.

### Q1 — depozyt i likwidacja krótkiej nogi USDT-M

Run-up ceny perp (największy wzrost w oknie, % ceny startowej, po `close` 8h):

| okno | max | p99 | p95 | udział okien > 50 % | > 100 % |
|---|---|---|---|---|---|
| 1 dzień | +21,1 % | +9,5 % | +5,2 % | 0 % | 0 % |
| 7 dni | +39,9 % | +25,2 % | +16,5 % | 0 % | 0 % |
| 30 dni | **+89,6 %** | +58,5 % | +40,6 % | 2,1 % | 0 % |
| 90 dni | +112,4 % | +91,2 % | +71,9 % | 17,6 % | 0,5 % |

Siatka (wszystkie 16 komórek — zakres inżynierski, nic nie jest wybierane po wyniku):

| M | uzupełnienie | likwidacje | max wykorzystanie | koszt likw./rok | obrót uzup. | koszt uzup./rok | **rocznie na kapitale (1+M)** |
|---|---|---|---|---|---|---|---|
| 0,25 | nigdy | 6 | 28,5 % | 1,44 % | 156 % | 0,05 % | +7,50 % |
| 0,25 | 30 dni | 12 | 31,7 % | 2,88 % | 919 % | 0,32 % | +6,13 % |
| 0,25 | 7 dni | 3 | 29,9 % | 0,72 % | 1 620 % | 0,56 % | +7,67 % |
| 0,25 | 1 dzień | **0** | 18,2 % (high: 19,5 %) | 0 | 4 127 % | 1,43 % | +7,55 % |
| 0,50 | nigdy | 3 | 52,9 % | 0,72 % | 156 % | 0,05 % | +6,73 % |
| 0,50 | 30 dni | 2 | 54,0 % | 0,48 % | 886 % | 0,31 % | +6,72 % |
| 0,50 | 7 dni | **0** | 35,7 % (high: **46,3 %**) | 0 | 1 621 % | 0,56 % | +6,87 % |
| 0,50 | 1 dzień | **0** | 18,2 % | 0 | 4 127 % | 1,43 % | +6,29 % |
| 1,00 | nigdy | 2 | 105,4 % | 0,48 % | 211 % | 0,07 % | +5,16 % |
| **1,00** | **30 dni** | **0** | 70,9 % (high: 70,0 %) | 0 | 851 % | 0,29 % | **+5,29 %** |
| 1,00 | 7 dni | 0 | 35,7 % | 0 | 1 621 % | 0,56 % | +5,15 % |
| 1,00 | 1 dzień | 0 | 18,2 % | 0 | 4 127 % | 1,43 % | +4,72 % |
| 1,50 | nigdy | 1 | 150,7 % | 0,24 % | 151 % | 0,05 % | +4,23 % |
| 1,50 | 30 dni | 0 | 70,9 % | 0 | 851 % | 0,29 % | +4,23 % |
| 1,50 | 7 dni | 0 | 35,7 % | 0 | 1 621 % | 0,56 % | +4,12 % |
| 1,50 | 1 dzień | 0 | 18,2 % | 0 | 4 127 % | 1,43 % | +3,78 % |

Próg likwidacji = M − 0,5 %. Oczekiwania z pre-rejestracji potwierdzone: M = 1,0 bez uzupełnień
→ 2 likwidacje; M = 1,0 z miesięcznymi → 0; M = 0,5 z miesięcznymi → 2. Odczyt: konfiguracje
bez likwidacji z depozytem ≤ 0,5 mają cienki zapas po cenach `high` (46,3 % z 49,5 % przy
M = 0,5 / 7 dni; 19,5 % z 24,5 % przy M = 0,25 / 1 dzień — a największy jednodniowy skok to
21,1 %) i wyższy koszt uzupełnień. **Solidna konfiguracja USDT-M: M = 1,0, uzupełnianie
miesięczne — 0 likwidacji, zapas 29 pp, +5,29 %/rok na kapitale 2×.**

### Q2 — carry COIN-M (zabezpieczenie w BTC, kapitał 1×) vs USDT-M

| rynek | n | średnia / 8h | CI 95 % (N_eff) | mediana | N_eff | t_neff | rocznie nominał | **rocznie na kapitale** |
|---|---|---|---|---|---|---|---|---|
| **COIN-M** | 6 020 | +0,00828 % | [+0,00537; +0,01119] | +0,0100 % | **153** | +5,58 | +9,07 % [5,88; 12,26] | **+9,07 % [5,88; 12,26] (1×)** |
| USDT-M | 6 019 | +0,00994 % | [+0,00628; +0,01361] | +0,0079 % | 113 | +5,32 | +10,89 % [6,87; 14,90] | +5,44 % [3,44; 7,45] (2×) |

Różnica stawek COIN-M − USDT-M na 6 018 wspólnych rozliczeniach: **−1,82 %/rok [−3,11; −0,53]**
(N_eff 596) — COIN-M płaci mniej (mniej dźwigni detalicznej), ale bez depozytu wychodzi więcej
na kapitale. Masa punktowa COIN-M na 0,0100 %: 41,7 %; stawki ujemne 19,6 %; korelacja stawek
0,70. **Half-width ex post 3,19 %/rok wobec 1,2 % z pre-rejestracji** — N_eff 153, nie 1 190:
proxy `n(1−ρ)/(1+ρ)` z samej autokorelacji lag-1 (0,675 → 1 169) zawyża N_eff 8×, bo funding
ma długą pamięć (kanoniczny `effective_sample_size` sumuje całą funkcję autokorelacji → 149).
Zapisane jako wniosek 63 (kolejny wariant wniosku 19/56/58).

### Q3 — basis kontraktów kwartalnych

Front (najkrótszy ≥ 7 dni), 5 880 świec 8h, 24 kontrakty, 2021-02-03 → 2026-06-30, annualizowany:

| rok | n | mediana | p25 | p75 | p05 | p95 | udział < 0 | średnia |
|---|---|---|---|---|---|---|---|---|
| 2021 | 982 | +12,9 % | +7,3 % | +25,1 % | +3,5 % | +48,7 % | 0,8 % | +18,0 % |
| 2022 | 1 078 | +2,3 % | +1,1 % | +3,7 % | −2,4 % | +6,9 % | 16,4 % | +2,3 % |
| 2023 | 1 084 | +5,5 % | +4,3 % | +7,9 % | +2,3 % | +11,7 % | 0,1 % | +6,4 % |
| 2024 | 1 098 | +11,2 % | +8,8 % | +14,5 % | +6,1 % | +25,5 % | 0 % | +12,9 % |
| 2025 | 1 095 | +5,7 % | +4,7 % | +7,2 % | +3,7 % | +11,7 % | 0 % | +6,3 % |
| 2026 H1 | 543 | +2,5 % | +1,6 % | +3,7 % | +0,6 % | +4,6 % | 0,6 % | +2,6 % |
| razem | 5 880 | **+5,9 %** | +3,6 % | +10,1 % | +0,8 % | +25,5 % | 3,2 % | +8,4 % |

Ex post (22 kontrakty wygasłe do 2026-07-01; baza zamknięta na wejściu vs funding USDT-M
zrealizowany do wygaśnięcia, oba annualizowane):

| wejście przed wygaśnięciem | n | baza: mediana | funding: mediana | różnica: mediana | min | max | baza > funding |
|---|---|---|---|---|---|---|---|
| 30 dni | 22 | +6,7 % | +5,2 % | **+1,8 pp** | −19,4 | +6,8 | 64 % |
| 60 dni | 21 | +6,3 % | +5,1 % | +1,4 pp | −16,8 | +9,8 | 62 % |
| 90 dni | 21 | +6,1 % | +5,4 % | **−0,9 pp** | −11,7 | +16,9 | 48 % |

Per kontrakt (wejście 90 dni) w `raw_output.txt`. Odczyt: basis i funding to ta sama stopa
z dwóch stron arbitrażu; kontrakt zamyka ją na wejściu (zero zmienności w oknie), ale nie
podnosi jej oczekiwania. Z rozrzutem ±17 pp na 21 kontraktach żadna z różnic median nie jest
odróżnialna od zera — i nie o to pytano.

### Q4 — per rok: T-bill 3M obok zwrotu na kapitale (lata niepełne annualizowane)

| rok | T-bill | C1a USDT-M 2× | nadwyżka | **COIN-M 1×** | **nadwyżka** | basis front 2× (stopa na wejściu) | nadwyżka |
|---|---|---|---|---|---|---|---|
| 2021 | 0,05 % | +15,2 % | +15,2 | +22,2 % | +22,1 | +9,0 % | +9,0 |
| 2022 | 2,02 % | +2,1 % | +0,0 | +1,8 % | −0,2 | +1,2 % | −0,9 |
| 2023 | 5,07 % | +3,9 % | −1,2 | +7,5 % | +2,5 | +3,2 % | −1,9 |
| 2024 | 4,97 % | +6,0 % | +1,0 | +12,2 % | +7,2 | +6,4 % | +1,5 |
| 2025 | 4,07 % | +2,6 % | −1,5 | +5,1 % | +1,0 | +3,1 % | −0,9 |
| 2026 H1 | 3,61 % | +0,4 % | −3,2 | +2,1 % | −1,5 | +1,3 % | −2,3 |
| **średnia 2022–2026 H1** | 3,95 % | +3,0 % | **−1,0 pp** | **+5,7 %** | **+1,8 pp** | +3,0 % | −0,9 pp |

Pięć obserwacji rocznych — opis, nie prognoza; „nadwyżka" to różnica średnich stóp, bez CI.

## Co na plus (+)

- **Cztery otwarte pytania C1 dostały liczby na TYCH SAMYCH danych i przyrządzie** (C1a
  odtworzone co do 0,01 pp), bez nowej reguły i bez wyboru po wyniku (pełne siatki).
- **Konstrukcja COIN-M jest algebraicznie wolna od likwidacji przy 1×** (test hypothesis na
  dowolnej ścieżce cen) — to własność kontraktu inverse, nie wynik z danych; danymi jest tylko
  stawka (+9,1 % [5,9; 12,3] na kapitale).
- **Depozyt USDT-M zmierzony z zapasem:** M = 1,0 z miesięcznym uzupełnianiem przetrwał
  +90 %/30 dni i +112 %/90 dni bez likwidacji także po cenach `high`.
- **Poprawka 1 wykryta i wprowadzona przed zamrożeniem:** koszt uzupełnień (do 1,43 %/rok przy
  dziennych) zmienia ranking tanich konfiguracji — bez niej siatka faworyzowałaby M = 0,25/1 dzień.
- **T-bill w tabeli obok** — pierwsza runda projektu, która stawia wynik przy koszcie alternatywnym.

## Co na minus (−)

- **Pre-rejestracja pominęła koszt uzupełnień** (Poprawka 1) i **zaniżyła szum COIN-M 2,7×**
  (proxy lag-1 dla N_eff — wniosek 63). Oba wykryte po pierwszym przebiegu; oba zapisane.
- **Likwidacje symulowane po świecach 8h** (`close`; `high` jako druga droga) — bez knotów
  intraday i bez ADL; maintenance 0,5 % jako stała (Binance ma progi rosnące z nominałem);
  opłata likwidacyjna 1,25 % jako górna stawka.
- **COIN-M w praktyce:** zabezpieczenie w BTC na koncie COIN-M, kontrakty po 100 USD (ziarno
  nominału), funding wypłacany w BTC (ekspozycja na odsetki, nie na nominał), tryb izolowany
  vs cross — nie modelowane; ryzyko giełdy w całości na Binance.
- **Basis front to „stopa na wejściu", nie P&L** — w Q4 kolumna basis nie jest zrealizowanym
  zwrotem (zaznaczone w tabeli); porównanie ex post (Q3) ma n = 21–22 i ogony ±17 pp.
- **Pięć lat = pięć obserwacji rocznych** w Q4; średnia „+1,8 pp ponad T-bill" ma rozrzut od
  −1,5 do +7,2 i nie jest prognozą.
- Kontrakty COIN-M datowane (`BTCUSD_YYMMDD`, od 2020-09) — konstrukcja „stopa zamknięta +
  brak likwidacji" — istnieją w archiwum, ale nie zostały pobrane (poza listą P3); zanotowane
  jako opcja, nie zmierzone.

## Walidacja (zasada 16a) — werdykt: **READY** (`walidacja.txt`)

- **Drugą drogą:** Σ funding COIN-M 2021→2026-07 = 50,24 % nominału − 0,38 % kosztów = 49,86 %
  / 5,50 roku = **9,07 %/rok** ✔ (skrypt 9,07); USDT-M Σ 60,28 % → 10,89 % ✔; różnica sum/rok
  −1,83 % ✔ (skrypt −1,82); run-up 30 dni 89,6 % ✔ (C1: 90 %); T-bill średnie vs mediany
  (2023: 5,07 / 5,23; 2024: 4,97 / 5,22) ✔; basis front z perp jako S zamiast spot: mediana 2024
  11,26 % vs 11,23 % ✔, razem 6,33 % vs 5,88 % (baza perp–spot ±0,05 %/8h przy 7 dniach do
  wygaśnięcia annualizuje się do ±2,6 pp — stąd różnica; kierunek zgodny).
- **Likwidacje po `high`:** konfiguracje z 0 likwidacji po `close` mają 0 także po `high`;
  wykorzystanie depozytu rośnie do 46,3 % (M = 0,5 / 7 dni) i 19,5 % (M = 0,25 / 1 dzień) —
  zapisane w tabeli jako ostrzeżenie.
- **N_eff:** proxy lag-1 1 169 vs kanoniczny 149 — rozbieżność wyjaśniona (długa pamięć), nie
  błąd; CI w tabeli z kanonicznego.
- **Kogo NIE ma:** świece kontraktów po wygaśnięciu (334), z zerowym wolumenem (330), < 7 dni
  do wygaśnięcia (774 — annualizacja wybucha), po 2026-07-01 (372), dwa kontrakty niewygasłe
  w porównaniu ex post; knoty intraday; ADL; opłaty maker (wszystko taker).
- **Red flag „COIN-M lepszy":** wynik na kapitale wynika z ZAŁOŻENIA kapitału 1× (własność
  kontraktu, test), a stawka COIN-M jest NIŻSZA niż USDT-M (−1,8 pp/rok, CI poza zerem) —
  dane nie faworyzują COIN-M, faworyzuje go konstrukcja. Zapisane wprost.
- **Red flag „idealnie potwierdza":** nie — pre-rejestracja oczekiwała podobnych stawek
  (są różne: −1,8 pp) i basis ≈ funding (tak, ale z ogonami ±17 pp).

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `backtest/carry_product.py` (nowy), `backtest/run_carry_product_d1.py` (nowy, reporter),
`tests/test_carry_product.py` (12), README rundy. Bez zmian w kodzie produkcyjnym; `carry_hedged`
użyty bez modyfikacji.

**Korektność:** (1) `forward_runup` — okno w przód `max_{1..k} P_{t+k}/P_t − 1` z obcięciem do
0 (pierwszy przebieg testu wykrył ujemne „run-upy" po szczycie — poprawione przed przebiegiem);
(2) `liquidation_events` — reset co `reset_periods` przez `t % reset_periods == 0` (pierwszy
reset po dokładnie `reset_periods` okresach; test: 7 resetów na 8 punktach przy co-okres),
likwidacja → `P_ref = P_t`, koszt stały, obrót `|usage|`; kolejność: reset PRZED sprawdzeniem
likwidacji w tym samym okresie (uzupełnienie ratuje pozycję w chwili uzupełnienia — zamierzone,
konserwatywne o jeden okres na korzyść pozycji; przy reset = 1 dzień i skoku 21 %/8h to
3 okresy ekspozycji); (3) `margin_grid` — `reset_days × 3`; koszt uzupełnień = obrót × 0,19 %
(test: 1,1³ − 1 przy reset dziennym na 4 punktach); (4) `inverse_position_usd_value` — tożsamość
(hypothesis 50 ścieżek); (5) `annualized_basis` — inner join na `open_time`, filtr
`open_time < expiry + 8h` (rozliczenie 08:00 UTC), `volume > 0`, `days ≥ 7`; test odtwarza
`r` dokładnie; (6) `basis_vs_funding` — świeca najbliżej `d` (pierwsza wersja brała pierwszą
w tolerancji → 61 zamiast 60 rozliczeń w teście; poprawione), okno `(start, delivery]`;
(7) `yearly_fraction` — annualizacja lat niepełnych przez liczbę okresów / 1 095.

**Edge-case'y:** pusta cena → zera; `margin ≤ maintenance` → `ValueError`; brak kolumn →
`ValueError`; kontrakt bez świec w tolerancji → pominięty (n = 21 dla 60/90 dni).
**Czytelność:** stałe nazwane z komentarzem źródła (maintenance, opłata likwidacyjna, 08:00 UTC).
**Uwagi (bez blokady):** skrypt nie drukuje `raw_output_przed_poprawka1` — różnica opisana
w Metadanych; `_yearly_annualized` dzieli przez ułamek roku także dla 2021 (od 01-01, pełny).
**Werdykt jednym zdaniem:** kod poprawny, trzy usterki (ujemny run-up, wybór świecy, koszt
uzupełnień) wykryte przez testy i pierwszy przebieg i naprawione PRZED zamrożeniem — **Approve**.

## Wniosek

**Produkt cash-and-carry ma sensowną konstrukcję tylko w wersji rozliczanej w bitcoinie
(COIN-M):** zabezpieczenie w BTC czyni pozycję algebraicznie wolną od likwidacji przy 1×,
kapitał to 1× zamiast 2×, i mimo niższej stawki (o 1,8 pp/rok) wychodzi **+9,1 %/rok
[5,9; 12,3] na kapitale za 5,5 roku, a od 2022 średnio +5,7 % wobec 3,95 % bonów
skarbowych (nadwyżka ~+1,8 pp, od −1,5 do +7,2)**. Wersja USDT-M z depozytem 1× i miesięcznym
uzupełnianiem jest bezpieczna (0 likwidacji, zapas 29 pp), ale od 2022 nie wychodzi ponad
T-bill (−1,0 pp). Kontrakt kwartalny zamyka stopę, nie podnosi jej. To nadal przepływ za
dźwignię innych, nie przewidywanie — i nadal z ryzykiem giełdy w całości.

## Rekomendacja

1. **Decyzja bramkowa użytkownika:** czy uruchomić produkt COIN-M (1 BTC zabezpieczenia +
   short inverse 1×, „zawsze w pozycji"). Liczby do decyzji: ~+2 pp/rok ponad T-bill od 2022
   przy rozrzucie rocznym ±4 pp, zero likwidacji z konstrukcji, ryzyko giełdy 100 % kapitału.
   Nie proponuję rundy pomiarowej „czy to wyjdzie" — to nie jest pytanie o edge.
2. **Jeśli produkt:** minimalny zakres inżynierski, nie badawczy — konto COIN-M, ziarno
   kontraktów 100 USD, tryb izolowany, wypłata fundingu w BTC (sprzedaż okresowa albo
   akumulacja — decyzja), monitor stawki (ujemna 19,6 % rozliczeń), limit ekspozycji na giełdę.
   Kolektor stawek COIN-M już działa (`fetch_external --only coinm_funding`).
3. **Opcja do sprawdzenia tanio, jeśli użytkownik chce stopę zamkniętą:** kontrakty COIN-M
   datowane (`BTCUSD_YYMMDD` w archiwum od 2020-09) — konstrukcja bez likwidacji ze stopą
   znaną na wejściu; jedno pobranie + ten sam `annualized_basis`. Nie mierzone tu (poza
   listą P3), nie jest to nowa hipoteza.
4. **Metodologicznie (wniosek 63):** N_eff dla szeregów o długiej pamięci (funding) liczyć
   wyłącznie kanonicznym `effective_sample_size`, nigdy z lag-1; pre-rejestracja rachunku
   mocy podaje N_eff z tej funkcji na własnościach danych, nie z wzoru.
5. Seria C pozostaje STOP dla wariantów reguł; D1 nie otwiera żadnego licznika.

## Użyte skille

Rejestr gałęzi `d1-produkt-carry` (`py tools/skill_audit.py raport --galaz d1-produkt-carry`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → pre-rejestracja (Q1–Q4, siatki, koszty) → kod → run → Poprawka 1 → bramki → DoD |
| `anthropic-skills:clas5-quant` | rozróżnienie „analiza wyniku dodatniego bez licznika" vs „generalizacja C1a"; N_eff kanoniczny; ryzyko/sizing (depozyt, likwidacja) |
| `anthropic-skills:quant-strategy-catalog` | rodzina D2: trzy konstrukcje, mechanizm „kto płaci", pułapki perp (likwidacja shorta, ADL, konwergencja basis, różnice COIN-M) |
| `engineering:testing-strategy` | plan testów PRZED kodem (tożsamość COIN-M jako hypothesis, `r` odtworzone dokładnie, likwidacja dokładnie raz, resety) |
| `data:validate-data` | bramka 16a: sumy fundingu, likwidacje po `high`, N_eff proxy vs kanoniczny, basis z perp jako S, „kogo nie ma", oba red flagi |
| `data:statistical-analysis` | bramka 16b: pełne siatki bez wyboru, CI z N_eff, mediany i rozstępy przy ogonach, „5 lat = 5 obserwacji", bez fałszywej precyzji |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Z tabeli zasady 19 pominięte: `security-review` (bez nowego kodu sieciowego — tylko cache),
`dataviz` (bez wykresów), `engineering:architecture`, `update-config`, `ta-toolkit`,
`lean-research`.
