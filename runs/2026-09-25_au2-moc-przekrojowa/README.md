# AU2 — moc przyrządu przekrojowego, krok 0: szerokość efektywna i szum rank IC (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (zapisana przed uruchomieniem). Kalibracja przyrządu — POZA licznikami
> hipotez, 0 wariantów (jak K1/K2/K3/T4/NC1). Żaden prawdziwy sygnał nie jest liczony.

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

_(sekcje poniżej po przebiegu)_
