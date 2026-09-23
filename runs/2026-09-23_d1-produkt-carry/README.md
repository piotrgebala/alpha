# D1 — produkt cash-and-carry: depozyt, likwidacja, COIN-M, basis kwartalny, stopa T-bill (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed uruchomieniem).** Pytania Q1–Q4, siatki parametrów, koszty
> i tabele wyjściowe zapisane PRZED obejrzeniem jakiegokolwiek wyniku. **To nie jest test
> hipotezy:** 0 nowych reguł, żadnego sygnału, żadnej trafności. Analiza RYZYKA i KONSTRUKCJI
> produktu po dodatnim C1a (rodzina D2 katalogu) na danych podłączonych w P3. Dwa pomiary
> opisowe na innych instrumentach (funding COIN-M, basis kontraktów kwartalnych) są
> **generalizacją C1a** (ta sama reguła „zawsze w pozycji", inny instrument — jak zasada 9 dla
> ETH/SOL/BNB), NIE nowymi wariantami serii C, która pozostaje STOP dla wariantów REGUŁ.
> Decyzja użytkownika 2026-09-23: „sprawdź wszystkie warianty".

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
- Kod: czyste funkcje w `backtest/carry_product.py` z testami; skrypt
  `backtest/run_carry_product_d1.py` (komenda przy zamknięciu; na `runs/ZAMROZONE.txt`).
  Przyrząd statystyczny dla Q2: `backtest/carry_hedged.summarize_pnl` (jak C1).

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

_(sekcje poniżej po przebiegu)_

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

_(po przebiegu — z `py tools/skill_audit.py raport --galaz d1-produkt-carry`)_
