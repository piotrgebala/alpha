# AU2 — moc przyrządu przekrojowego, krok 0: szerokość efektywna i szum rank IC (2026-09-25)

> **STATUS: ZAMKNIĘTA — krok 0 NIE zamyka ML przekrojowego:** `IC* = 0,025` (≤ 0,05) → kroki 1–2
> dostają osobną kartę (`karta_krokow_1_2.md`, SZKIC — 3 decyzje użytkownika przed startem).
> Koszyk top-50 po odjęciu rynku ≈ 18 niezależnych zakładów (surowo ≈ 3); przyrząd widzi średnie
> rank IC ≥ 0,022 (moc 80 %); na IR 0,75 trzeba IC ≈ 0,025 brutto. Kalibracja — POZA licznikami
> hipotez, 0 wariantów. Pre-rejestracja `f5f269d`. Walidacja (16a): **Ready**; przegląd (16c): **Approve**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Pomysł użytkownika (projekt karty z rozmowy na claude.ai, 2026-09-25): zanim zbudujemy model ML,
który układa ranking monet (long najlepsze / short najgorsze), trzeba wiedzieć, czy nasz przyrząd
w ogóle zobaczy przewagę, jaką taki model realnie mógłby mieć. Krok 0 jest najtańszy: bez żadnego
modelu mierzymy (1) ile naprawdę niezależnych zakładów jest w koszyku 20 / 50 / 100 monet — bo
monety chodzą razem — i (2) jak dużą „trafność rankingu” (IC) test na 5 latach odróżnia od zera.
Jeśli potrzebne IC jest nierealnie duże, temat ML przekrojowego zamyka się bez trenowania czegokolwiek.

## ID testu

**AU2 krok 0** — rozszerzenie K1 (kontrola przyrządu) i AU1 (moc strategii tygodniowych) na przyrząd
przekrojowy. Kroki 1 (ramię negatywne: permutacja celu w przekroju, pełny pipeline z budżetem
przeszukiwania) i 2 (ramię pozytywne: siatka sił +5…+30 %/rok, krzywa mocy) — **osobna
pre-rejestracja**, tylko jeśli pozwoli reguła decyzji niżej.

## Metadane

- Branch `au2-moc-przekrojowa` (z `master` po scaleniu KP1, `c9c2dd6`).
- Dane: `data/raw/universe_full` (685 kontraktów USDT-M, RU1), dzienne zamknięcia i obrót; skład
  koszyka co miesiąc z danych sprzed miesiąca (`rebalance_premium.monthly_members`, jak X1/X2):
  top-20 / top-50 / top-100 po średnim obrocie 30 dni. Okno 2021-02-01 → 2026-06-30 (zasada 20),
  formowanie codzienne, zwrot 7-dniowy (= średnia 7 faz tygodniowych, wniosek 89).
- Skrypt `backtest/run_au2_szerokosc.py`, testy `tests/test_au2_szerokosc.py` (7, w tym kontrola
  pozytywna: wstrzyknięte IC 0,10 odzyskane). Komenda: `PYTHONUTF8=1 py -m backtest.run_au2_szerokosc`
  → `raw_output.txt`.
- Parametry zamrożone: okno korelacji 90 dni, pokrycie ≥ 90 %, 200 losowych sygnałów AR(1) na
  półtrwanie 7 i 28 dni, IR docelowe 0,5 / 0,75 / 1,0, moc 80 % przy α = 5 % dwustronnie.

## Poprzedzające wyniki

- **Wniosek 40 (P2):** 20 monet przy korelacji 0,47 ≈ 2 niezależne — liczba instrumentów to nie
  liczba obserwacji. AU2 mierzy to wprost, po odjęciu rynku (tak widzi koszyk long/short).
- **Wniosek 68 (X2):** rank IC momentum na top-50 −0,006 [−0,033; +0,022] — punkt odniesienia dla
  szerokości przedziału IC na tej bazie (liczony dla jednej fazy).
- **Wnioski 87 (AU1) i 81 (SH1):** strategie tygodniowe na 5 latach wykrywają dopiero duże efekty
  (moc 25 % przy +10 %/rok). AU2 pyta o to samo dla przyrządu z rankingiem.
- **K1/K2, wniosek 41 (T4):** kalibracja tylko na danych ze ZNANYM sygnałem albo bez sygnału —
  stąd losowe sygnały i kontrola pozytywna, żadnego prawdziwego sygnału.
- **Wniosek 11:** ML na tych samych danych OHLCV to czwarte podejście do tej samej ściany — AU2
  mierzy przyrząd, nie pomysł; ewentualny wariant ML ma sens głównie z NOWYMI danymi.

## Pre-rejestracja

- **Pytanie:** jakie najmniejsze średnie rank IC (tygodniowe, 7 faz) przyrząd przekrojowy odróżnia
  od zera na 2021-02 → 2026-06 i jakie IC trzeba mieć na IR 0,5 / 0,75 / 1,0 przy zmierzonej
  szerokości?
- **Miary:** (a) współczynnik uczestnictwa macierzy korelacji (surowej i po odjęciu średniej
  przekroju) — mediana po miesiącach; (b) `se` średniego IC = rozrzut średnich między 200
  losowymi sygnałami AR(1) (sygnał losowy o realistycznej trwałości na PRAWDZIWYCH zwrotach —
  zachowuje korelacje, grube ogony i nakładanie się okien); najmniejsze wykrywalne IC
  `MDE = (1,96 + 0,84) · se`; (c) `IC_IR = IR / √(szerokość_po_odjęciu_rynku × 52)` — brutto, przed
  kosztami (koszty tylko podnoszą wymagane IC).
- **Wielkość decyzyjna:** `IC* = max(MDE, IC_IR przy IR 0,75)` dla koszyka top-50 i sygnału
  o półtrwaniu 28 dni (typowa trwałość cech tygodniowych; top-20/top-100 i półtrwanie 7 dni opisowo).
  IR 0,75 ≈ zwrot +20–25 %/rok przy zmienności ~30 %/rok — cel użytkownika (zwroty rzędu zakładu
  o kierunek, `docs/rag/10`).
- **Reguła decyzji (zapisana przed wynikiem):**
  - `IC* ≥ 0,10` → temat ML przekrojowego **zamknięty** bez trenowania (takie IC nie występuje
    na płynnych rynkach; X2 zmierzył −0,006);
  - `IC* ≤ 0,05` → projekt kroków 1–2 (karta z zamrożoną listą cech, purging i embargo, budżet
    przeszukiwania taki sam w ramieniu negatywnym i pozytywnym, drugi warunek werdyktu dla koszyka
    ustalony z góry) — osobna pre-rejestracja;
  - pomiędzy → decyzja użytkownika (z liczbami z tej rundy).
  Bez progu „moc ≥ X % = GO” — krok 0 niczego nie ogłasza jako sukces.
- **Granica dużego n:** przy dłuższej historii `se` → 0, więc `MDE` maleje — kryterium nie karze
  celu rundy.
- **Znane ograniczenie z góry:** przy N ≈ 100 i oknie 90 dni macierz korelacji ma rząd ≤ 89 (szum
  próby Marčenko–Pastur) — uczestnictwo top-100 jest zaniżone; decyzja stoi na top-50.
- **Czego runda NIE robi:** nie liczy IC żadnej prawdziwej cechy, nie trenuje modelu, nie wybiera cech.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Monety w koszyku 50 największych chodzą razem tak mocno, że „surowo” to jak ~3 niezależne zakłady.
Ale koszyk long/short odejmuje ruch całego rynku — po odjęciu zostaje ~18 niezależnych zakładów
co tydzień. Przy takiej szerokości wystarczy, żeby ranking modelu był trafny w bardzo małym
stopniu (IC ≈ 0,025, czyli korelacja rankingu z przyszłym zwrotem 2,5 %), by dać zysk rzędu
+20 %/rok przed kosztami — i nasz test na 5 latach taki poziom już widzi (najmniejsze wykrywalne
IC 0,022). **Wniosek: przyrząd przekrojowy jest znacznie czulszy niż jednoaktywowy** (tam przyrząd
widział dopiero Sharpe ≈ 0,86), więc sensownie jest zmierzyć, czy ML w ogóle potrafi taki sygnał
wydobyć — kroki 1–2. Uwaga: momentum na top-50 miało IC −0,006 (X2), więc 0,025 to nadal więcej,
niż dotąd widzieliśmy na tych danych.

## Wynik

Pełny stdout: `raw_output.txt` (140 s). Mediana po miesiącach [p10; p90].

| koszyk | śr. korelacja par | szerokość surowa | **szerokość po odjęciu rynku** | IC na IR 0,5 / 0,75 / 1,0 (brutto) | sd IC dziennego | se średniego IC (półtrwanie 7 / 28 d) | **najmniejsze wykrywalne IC** (moc 80 %; 7 / 28 d) |
|---|---|---|---|---|---|---|---|
| top-20 (65 mies.) | 0,52 [0,34; 0,65] | 2,8 [2,1; 4,9] | 8,6 [4,3; 11,6] | 0,024 / 0,035 / 0,047 | 0,229 | 0,0115 / 0,0144 | 0,032 / 0,040 |
| **top-50** (65 mies.) | 0,51 [0,34; 0,64] | 3,2 [2,2; 5,9] | **17,7** [12,1; 21,4] | 0,016 / **0,025** / 0,033 | 0,143 | 0,0067 / 0,0078 | 0,019 / **0,022** |
| top-100 (62 mies.*) | 0,53 [0,35; 0,68] | 3,1 [2,1; 6,0] | 25,7 [17,8; 32,6]** | 0,014 / 0,021 / 0,027 | 0,100 | 0,0049 / 0,0062 | 0,014 / 0,017 |

\* 3 pierwsze miesiące 2021 bez 100 kandydatów pominięte (poprawka po pierwszym przebiegu, który
się na tym zatrzymał — tylko część opisowa; top-20/top-50 identyczne w obu przebiegach).
\*\* przy N ≈ 93 i oknie 90 dni macierz ma rząd ≤ 89 — zaniżone (zapisane z góry).
Średnie IC pod H0 we wszystkich wariantach −0,0010 … +0,0006 (≈ 0, bez skrzywienia przyrządu).

**Decyzja wg pre-rejestracji:** `IC* = max(0,022; 0,025) = 0,025 ≤ 0,05` → **kroki 1–2 dostają
osobną kartę**; temat nie jest zamknięty.

## Co na plus (+) / Co na minus (−)

**(+)**
- Bez żadnego prawdziwego sygnału — zero ryzyka dopasowania; kontrola pozytywna w testach
  (wstrzyknięte IC 0,10 odzyskane), średnie pod H0 ≈ 0.
- Przeliczenie drugą drogą (wzór, nie kod): sd dziennego IC pod H0 ≈ 1/√(N−1) = 0,229 / 0,143 / 0,100
  — identycznie; se średniego 2,1–2,4× większe niż dla niezależnych dni (nakładanie 7-dniowych
  okien, górna granica √7 ≈ 2,6) — spójne; szerokość surowa top-20 2,8 ≈ wniosek 40 (~2) i wzór
  dla równej korelacji 0,52 (3,3).
- Liczba ważna dla całego projektu: przekrój po odjęciu rynku daje ~18 niezależnych zakładów
  tygodniowo (top-50) — wniosek 40 („20 monet ≈ 2”) dotyczy pozycji z ekspozycją na rynek, nie
  koszyka long/short.

**(−)**
- **IC_IR jest brutto** — koszty obrotu (tygodniowa wymiana części nóg, 0,07 %) podniosą wymagane IC;
  przy obrocie ~50 %/tydz. to ~1,8 %/rok kapitału, czyli IR o ~0,06–0,1 mniej — rząd 0,003–0,004 IC.
- Prawo fundamentalne zakłada równe, niezależne zakłady i stałe IC; realne IC jest zmienne
  (sd IC dziennego 0,14), a korelacje zmieniają się w czasie (p10–p90 szerokości 12–21).
- Szerokość z okna 90 dni jest zaniżona szumem próby (Marčenko–Pastur; przy 47/90 czynnik do ~1,5)
  — to działa NA NIEKORZYŚĆ pomysłu (zawyża wymagane IC), więc decyzja jest ostrożna.
- **Kogo nie ma w zbiorze:** monety wycofane w trakcie tygodnia (brak ceny za 7 dni → para
  pominięta, lekki survivorship w obrębie tygodnia); luty–kwiecień 2021 dla top-100; kontrakty
  spoza Binance USDT-M.
- Krok 0 nie mówi nic o tym, czy ML ZNAJDZIE IC 0,025 — tylko że gdyby je znalazł, test by to
  zobaczył. Wniosek 11 nadal obowiązuje: te same dane OHLCV przemielone nieliniowo to czwarte
  podejście do tej samej ściany (X2: momentum IC −0,006).

## Walidacja (16a), statystyka (16b), przegląd (16c)

`data:validate-data`: przeliczenia jak wyżej — **Ready**. `data:statistical-analysis`: zakresy p10–p90
zamiast punktów, MDE = 2,80 · se z rozrzutu 200 symulacji, H0 wycentrowane. `engineering:code-review`
(samodzielnie, lista kontrolna): losowy sygnał, maska członków, okno korelacji przed miesiącem —
poprawne; `feasible_members` dodane po pre-rejestracji, dotyczy tylko opisowego top-100; drobiazg:
martwa lista `ns` w `ic_noise` (bez wpływu, kod zostawiony jak uruchomiony). **Werdykt jednym zdaniem:
Approve** — skrypt mierzy przyrząd bez prawdziwego sygnału, a testy (w tym kontrola pozytywna) pokrywają
wszystkie funkcje liczące.

## Wniosek

**Prostym językiem:** przyrząd do rankingów monet jest dużo czulszy, niż się obawialiśmy — zobaczyłby
nawet bardzo słabą, ale opłacalną przewagę. Dlatego warto zmierzyć następny krok: czy model ML na tym
przyrządzie nie „wymyśla” zysków z szumu (krok 1) i jak słaby sygnał potrafi znaleźć (krok 2).

**Technicznie:** top-50 po odjęciu rynku ≈ 17,7 niezależnych zakładów; MDE IC 0,022 (półtrwanie 28 d),
IC_IR(0,75) 0,025 brutto → `IC* = 0,025 ≤ 0,05`: ML przekrojowe nie jest wykluczone przez przyrząd.

## Rekomendacja

1. Kroki 1–2 — **karta `karta_krokow_1_2.md` (SZKIC)**; przed startem trzy decyzje użytkownika:
   zbiór cech (informacyjny), budżet przeszukiwania, drugi warunek werdyktu dla koszyka.
2. Przy każdej przyszłej strategii przekrojowej używać tych liczb jako rachunku mocy (zasada 18):
   `se` średniego IC ≈ 0,008 (top-50), ≈ 0,014 (top-20).
3. Do wniosku 40: „20 monet ≈ 2 niezależne” dotyczy ekspozycji kierunkowej; koszyk long/short ma ~9 (top-20).

## Użyte skille

Rejestr `runs/skille/au2-moc-przekrojowa.jsonl` (`py tools/skill_audit.py raport --galaz au2-moc-przekrojowa`):
**6 wczytań, 6 skilli.**

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | kolejność: pre-rejestracja z regułą decyzji w osobnym commicie przed przebiegiem |
| `anthropic-skills:clas5-quant` | przyrząd przekrojowy ≠ p/break-even (methodology §9); kalibracja tylko bez sygnału albo ze znanym (wniosek 41) |
| `engineering:testing-strategy` | testy funkcji liczących + kontrola pozytywna (wstrzyknięte IC) |
| `data:validate-data` | przeliczenie drugą drogą (1/√(N−1), wzór dla równej korelacji), „kogo nie ma w zbiorze” |
| `data:statistical-analysis` | zakresy p10–p90, MDE z rozrzutu symulacji, IC_IR jawnie brutto |
| `engineering:code-review` | przegląd przed scaleniem: Approve |

Pominięte z tabeli zasady 19: `quant-strategy-catalog` (kalibracja przyrządu, nie nowa hipoteza —
wczytany przy kroku 1–2, gdy powstanie karta hipotezy ML), `dataviz` (bez wykresu; krzywa mocy
przy krokach 1–2), `data:explore-data` (`universe_full` sprofilowany w RU1).
