# X2 — momentum przekrojowe na szerszym koszyku (top-50, nogi po 10): większa próba, nie wariant (2026-09-23)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY, punktowo dodatni, ale SŁABSZY i mniej wiarygodny niż
> X1:** +0,044 %/dzień [−0,034; +0,121], t 1,10, **+15,9 %/rok [−12,3; +44,2]**; rank IC
> **−0,006 [−0,033; +0,022]** (zero); połowa sumy w 33 skrajnych dniach; 2022 −20 %. Dodatkowo
> walidacja wykryła **wrażliwość na fazę tygodniowego rebalansu**: reguła X1 (top-20/5) liczona
> na siatce formowań X2 (od 2021-05-01) daje +0,024 %/dzień zamiast +0,060 — X1 było
> częściowo szczęściem kalendarza. Odczyt łączny rodziny B1 (zapisany przed X2): „z poparciem,
> bez dowodu" — ale poparcie po X2 jest **słabsze**, nie mocniejsze. Kolejność w gicie:
> pre-rejestracja + moc `5293346` → przebieg → wynik w commicie scalającym. **Seria X2: 1/1,
> STOP.** Walidacja (16a): **READY**; przegląd diffu (16c): **Approve**. Decyzja użytkownika
> 2026-09-23: „wykonaj oba".

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Na szerszym koszyku (50 monet) momentum dało +16 % rocznie po kosztach, ale przedział
niepewności sięga od −12 do +44 %, więc znowu nie da się tego odróżnić od szczęścia — a kilka
rzeczy wygląda gorzej niż w X1.** Zdolność sygnału do porządkowania monet (IC) jest równa zeru;
połowa zysku pochodzi z 33 dni z ekstremalnymi ruchami; rok 2022 stracił 20 %. Najważniejsze
odkrycie jest uboczne: gdy tę samą regułę co w X1 (20 monet) policzyć na kalendarzu X2 (start
w maju zamiast w lutym 2021, więc tygodniowe rebalanse wypadają w inne dni), wynik spada
z +22 % do +9 % rocznie. **Wynik X1 zależał od tego, w które dni tygodnia wypadały rebalanse
— to znak, że duża część tamtego +22 % była przypadkiem, nie regułą.** Momentum przekrojowe
w krypto pozostaje hipotezą ze słabym poparciem; kolejne warianty nic tu nie rozstrzygną.

---

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

X1 dało +22 % rocznie, ale z przedziałem od −5 do +49 % — za szeroki, żeby cokolwiek
rozstrzygnąć. Szerszy koszyk (50 monet zamiast 20, po 10 w każdej nodze zamiast 5) uśrednia
więcej niezależnych ruchów, więc szum powinien zmaleć o ok. 30 %. Cena: monety z miejsc 21–50
są mniej płynne (droższe w handlu, trudniej je shortować, częściej znikają z giełdy). Reguła
pozostaje ta sama — to test, czy efekt z X1 widać wyraźniej na większej próbie, nie nowy pomysł.

## ID testu

**X2** — seria X2 (rodzina B1, drugi wariant rodziny). **Licznik 1/1, STOP.** Po X2 rodzina B1
ma dwa odczyty (X1 top-20, X2 top-50); nie wolno ich sumować ani wybierać lepszego — raportowane
obok siebie. Kolejne szerokości (top-100), inne kwantyle, okna, trzymanie — zakazane bez decyzji.

## Metadane

- Branch: `x2-momentum-top50` (od `master` @ `a7af7da`).
- Dane: uniwersum P2 (281 symboli, wycofane zostają), funding per symbol; okno `2021-05-01 →
  2026-07-01` — **start w maju 2021, bo wcześniej brakuje 50 kandydatów** (luty–kwiecień 2021:
  41–46 symboli z ≥ 30 notowaniami w oknie obrotu; `monthly_members` fail loud). X1 zaczynało
  2021-02-01: X2 ma o 3 miesiące krótszą próbę (62 koszyki zamiast 65).
- Uniwersum point-in-time: `monthly_members(top_n=50)` (30 dni obrotu PRZED miesiącem).
- Koszty: 0,07 % na jednostkę obrotu (taker + poślizg 0,02 % — **dla monet 21–50 poślizg jest
  optymistyczny**, zapisane); funding per symbol (long płaci, short otrzymuje).
- Kod: `backtest/xs_momentum.py` bez zmian (parametry `leg_size`, `top_n`); skrypt
  `backtest/run_xs_momentum_x2.py` (kopia X1 z trzema stałymi; X1 zamrożony). Komendy przy
  zamknięciu; skrypt na `runs/ZAMROZONE.txt`.

## Poprzedzające wyniki

- **X1** (wniosek 64): +0,060 %/dzień [−0,015; +0,135], +22 %/rok netto, t 1,58, dodatni
  w 6/6 lat, 2025 = 52 % sumy, IC +0,028 [−0,007; +0,064], korelacja z BTC −0,13, obrót
  0,87/formowanie; rozdzielczość 27 %/rok; rozstrzygnięcie tylko większą próbą.
- **Wniosek 65**: symulacja losowych rankingów zaniża szum ~30 % (nogi z sygnału są bardziej
  zmienne) → half-width × 1,3.
- **R1** (wniosek 57): ruchy względne wewnątrz miesiąca trwają (mechanizm); **P2/wniosek 40**:
  przekrój nie mnoży próby liniowo (korelacja 0,47) — 50 monet to nie 2,5× informacji z 20.
- **families.md B1**: pułapki szerszego uniwersum — płynność ogona, dostępność shorta,
  wolumen wycofanych.

## Pre-rejestracja

- **Hipoteza:** ta sama co X1 (momentum względne 4 tygodnie → 1 tydzień), mierzona na szerszym
  koszyku; mechanizm bez zmian (przegrani tracą dalej — X1: efekt z nogi short).
- **DOKŁADNIE JEDNA zmienna wobec X1:** szerokość (top-50, nogi po 10). Kwantyl 20 % zachowany.
- **Przyrząd i kryterium:** jak X1 — dzienny szereg netto, CI z N_eff, POZYTYWNY `t_neff > 1,96`,
  NEGATYWNY `ci_high < 0`, inaczej NIEROZSTRZYGNIĘTY; wtórnie IC, korelacja z BTC, per rok,
  dni z nogą < 10 aktywnych (wycofania).
- **Oczekiwania zapisane z góry:** (a) szum nogi ~√2 mniejszy → half-width ~15–20 %/rok
  (po korekcie ×1,3); (b) jeśli efekt X1 jest realny i podobny na monetach 21–50, punktowo
  +15…+25 %/rok i t ≈ 2–3; (c) jeśli efekt mieszka tylko w memecoinach top-20, X2 rozcieńczy
  go — spadek punktowy poniżej X1; (d) koszty realnie wyższe niż w modelu.
- **Odczyt łączny X1 + X2 (zapisany PRZED X2):** dwa odczyty rodziny B1 raportowane obok siebie;
  „hipoteza z poparciem" tylko gdy oba punktowo dodatnie i X2 ma t_neff > 1,96; jeśli X2
  NIEROZSTRZYGNIĘTY z punktem dodatnim — rodzina zostaje „z poparciem, bez dowodu"; jeśli X2
  ujemny punktowo — X1 traktowany jako prawdopodobny fałszywy pozytyw (2025).
- **Rachunek mocy (zasada 18):** `py -m backtest.run_xs_momentum_x2 --moc 100` PRZED przebiegiem;
  liczby niżej; MIERZALNA, jeśli half-width × 1,3 < obietnica literatury (52 %/rok) — i osobno
  zapisane, czy < punkt X1 (22 %/rok), bo to jest realny cel rundy.

### Rachunek mocy — z symulacji, przed wynikiem (`moc.txt`)

`py -m backtest.run_xs_momentum_x2 --moc 100` (312 s): 100 losowych par nóg (10 + 10) spośród
członków z sygnałem, ta sama maszyneria, seed 0 — bez patrzenia na prawdziwy sygnał.

| wielkość | X2 (top-50) | X1 (top-20, dla porównania) |
|---|---|---|
| dni / formowań / koszyków / symboli | **1 886** / 270 / 62 / 218 | 1 975 / 283 / 65 / 119 |
| pod H0: koszt obrotu | 0,0163 %/dzień = **5,94 %/rok** | 5,62 %/rok |
| sd dzienna netto (typowa) | **1,108 %** | 1,302 % |
| empiryczne se średniej pod H0 | 0,0245 %/dzień | 0,0296 %/dzień |
| half-width 95 % | **17,5 %/rok** | 21,2 %/rok |
| half-width × 1,3 (wniosek 65) | **22,8 %/rok** | 27,3 % ex post |

**Werdykt mierzalności:** obietnica literatury (52 %/rok) = 2,3× skorygowanej rozdzielczości →
**MIERZALNA**. **Punkt X1 (22 %/rok) leży dokładnie na granicy rozdzielczości** (22,8 %): jeśli
prawdziwy efekt na top-50 jest taki jak punkt X1, oczekiwane t ≈ 1,9 — wynik może wyjść
zarówno POZYTYWNY, jak i NIEROZSTRZYGNIĘTY, i to zapisujemy z góry. Szum zmalał o 17 %
(1,108 vs 1,302 %), nie o 30 % — 50 monet to nie 2,5× informacji z 20 (wniosek 40).

### Czego runda NIE robi

Nie zmienia sygnału, trzymania, kwantyli ani kosztów; nie filtruje monet po płynności po
wyniku; nie sumuje X1 z X2; nie odwraca znaku.

---

## Wynik

Komendy: `py -m backtest.run_xs_momentum_x2 --moc 100` (`moc.txt`, 312 s) i
`py -m backtest.run_xs_momentum_x2` (`raw_output.txt`, 5,6 s); `PYTHONUTF8=1`. Dane: 62 koszyki
top-50 (218 symboli), 270 formowań 2021-05-01 → 2026-06-27, 1 886 dni.

### 1. Kryterium (jedno ramię, próg 0)

| | n | średnia / dzień | CI 95 % (N_eff) | mediana | t_neff | rocznie ×365 |
|---|---|---|---|---|---|---|
| **netto** | 1 886 | **+0,0436 %** | [−0,0338; +0,1210] | +0,0008 % | **+1,10** | **+15,9 % [−12,3; +44,2]** |
| brutto | 1 886 | +0,0471 % | [−0,0306; +0,1248] | +0,0075 % | +1,19 | +17,2 % [−11,2; +45,5] |

**Odczyt kryterium: NIEROZSTRZYGNIĘTY.** Half-width ex post 0,0774 %/dzień = **28,3 %/rok**
(ex ante 17,5 %, po korekcie ×1,3: 22,8 % — szum nóg z sygnału znów wyższy: sd 1,715 % wobec
1,108 % pod H0 → współczynnik 1,55, nie 1,3; wniosek 68).

### 2. Dekompozycja

Σ brutto +88,8 %, Σ funding netto **+10,0 %**, Σ koszty 16,6 % (obrót 0,88/formowanie),
**Σ netto +82,2 %** (5,2 roku). Noga long −0,022 %/dzień, noga short −0,116 %/dzień (short
robi wynik). Dni z nogą < 10 aktywnych: **268** (14 % — wycofania w ogonie płynności). Dni > 0: 50,1 %.

| rok | dni | Σ netto | Σ brutto | Σ funding | Σ koszt | sd / dzień | noga long | noga short |
|---|---|---|---|---|---|---|---|---|
| 2021 (od maja) | 244 | +33,8 % | +33,9 % | +2,0 % | 2,2 % | 1,93 % | +96 % | +29 % |
| **2022** | 365 | **−20,5 %** | −15,1 % | −2,2 % | 3,2 % | 1,22 % | −157 % | −127 % |
| 2023 | 365 | +12,8 % | +11,5 % | +4,5 % | 3,2 % | 1,24 % | +76 % | +53 % |
| 2024 | 366 | +20,0 % | +21,8 % | +1,4 % | 3,2 % | 1,52 % | +44 % | +1 % |
| 2025 | 365 | +30,8 % | +36,6 % | −2,7 % | 3,1 % | 2,05 % | −41 % | −114 % |
| 2026 H1 | 181 | +5,4 % | +0,1 % | +7,1 % | 1,8 % | 2,55 % | −62 % | −62 % |

Dodatni w 5 z 6 lat (X1: 6/6); 2022 ujemny, gdy przegrani (short) spadli MNIEJ niż zwycięzcy.

### 3. Wtórnie

- **Rank IC tygodniowe: −0,006 [−0,033; +0,022]**, IC > 0 w 50,9 % tygodni, 50 par — sygnał
  NIE porządkuje 50 monet (X1 na 20: +0,028 [−0,007; +0,064]). Zysk portfela przy zerowym IC =
  zysk z ogonów (skrajne nogi), nie z monotonicznej zależności.
- **Korelacja z BTC:** −0,11 (neutralny).
- **Ogony:** p05 −2,4 %, p50 +0,001 %, p95 +2,6 %, min −10,0 %, max +13,9 %; **33 dni z |r| > 5 %
  sumują się do +43,1 % z +82,2 %** (52 %); bez 20 skrajnych dni średnia +0,024 % vs +0,044 %
  — wynik mieszka w ogonach (X1: nie).

### 4. Walidacja krzyżowa z X1 na wspólnym oknie (zapisana jako druga droga, nie kryterium)

Reguła X1 (top-20/5) tym samym kodem na siatce formowań X2 (od 2021-05-01, co 7 dni):
**+0,0243 %/dzień [−0,0505; +0,0991], Σ +45,8 %** wobec X2 +0,0436 % [−0,034; +0,121], Σ +82,2 %;
korelacja dziennych zwrotów obu 0,60. Ta sama reguła na siatce X1 (od 2021-02-01) dawała
+0,0602 %/dzień — różnica wobec +0,0243 % to (a) trzy miesiące luty–kwiecień 2021 i (b) **inna
faza tygodniowego rebalansu** (inne dni formowań). Rozmiar tej różnicy (+0,036 %/dzień ≈ 13 %/rok)
jest porównywalny z samym efektem — **wrażliwość na fazę kalendarza to niezmierzony dotąd
składnik niepewności X1** (analog fold-jitter z checkpointu v2).

## Co na plus (+)

- Punktowo dodatni na innym, szerszym koszyku (218 symboli), neutralny do BTC, funding netto
  dodatni (+1,9 %/rok), obrót 0,88 — mechanika portfela taka sama jak w X1.
- Rachunek mocy z symulacji i korektą ×1,3 był PRZED wynikiem; walidacja krzyżowa z X1 zapisana
  jako druga droga PRZED obejrzeniem X2 (skrypt `walidacja.py` w commicie pre-rejestracji).
- Uczciwie wykryta wrażliwość na fazę rebalansu — lepiej wiedzieć teraz niż po wpłacie kapitału.

## Co na minus (−)

- **IC = 0 na top-50** — sygnał nie porządkuje monet; zysk portfela to ogony (33 dni = 52 % sumy),
  nie systematyczna zależność. To jest kształt fałszywego pozytywu.
- **2022: −20 %** — momentum przekrojowe traci, gdy cały rynek spada, a przegrani spadają mniej.
- **Wrażliwość na fazę:** ta sama reguła, inny dzień tygodnia formowań → +9 % zamiast +22 %/rok.
  CI z pre-rejestracji nie obejmuje tego źródła niepewności.
- **Płynność ogona:** 268 dni z niepełną nogą (wycofania = gotówka po ostatniej cenie —
  korzystnie dla shorta); poślizg 0,02 % dla monet 21–50 optymistyczny.
- Szum ex post 1,55× symulacji pod H0 (nie 1,3×) — korekta z wniosku 65 zbyt mała dla
  szerszego koszyka.

## Walidacja (zasada 16a) — werdykt: **READY** (`walidacja.txt`)

- **Tożsamość sum:** +88,788 + 10,013 − 16,613 = +82,187 = Σ netto ✔; dni 1 886 = dni bazy od
  pierwszego formowania + 1 ✔; formowań 270, obrót łączny 237,3 (0,879) ✔.
- **Drugą drogą (bez dryfu wag):** średni 7-dniowy zwrot top-10 − bottom-10 = +0,376 %/tydzień
  (se 0,264 %) → +19,6 %/rok; z szeregu dziennego Σ brutto/270 = +0,329 %/tydzień — zgodność
  co do rzędu (różnica = dryf wag + zwroty proste vs złożone przy większej zmienności ogona) ✔.
- **X1 na wspólnym oknie:** +0,0243 %/dzień (tym samym kodem, inna siatka) — wykryta wrażliwość
  na fazę; korelacja X1-okno/X2 0,60 ✔ (ten sam mechanizm, częściowo te same monety).
- **Kogo NIE ma:** symbole 51+ (63 z 281), luty–kwiecień 2021 (41–46 kandydatów), pierwsze
  28 dni notowań, 268 dni z nogą < 10 (gotówka); członków z sygnałem min 48, mediana 50.
- **Red flagi:** „idealnie potwierdza" — nie (słabszy, IC 0, 2022 ujemny); „dodatni → ogony" —
  TAK, zapisane; „wybór lepszego z X1/X2" — nie, oba raportowane obok siebie.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `backtest/run_xs_momentum_x2.py` (kopia zamrożonego X1 z TOP_N = 50, LEG_SIZE = 10,
FIRST_MONTH = 2021-05-01; `monthly_members(top_n=)`, `long_short_returns(leg_size=)`,
`simulate_null_means(leg_size=)`, `weekly_ic` na wszystkich członkach — jak X1), `walidacja.py`,
README. Bez zmian w `xs_momentum.py` (parametry istniały od X1; testy X1 pokrywają `leg_size`).
**Korektność:** każde wywołanie maszynerii dostaje `LEG_SIZE`; licznik „dni z nogą < LEG_SIZE"
w wydruku; korekta ×1,3 tylko w wydruku mocy (nie zmienia kryterium). **Werdykt jednym
zdaniem:** skrypt jest reporterem z trzema stałymi, bez decyzji — **Approve**.

## Wniosek

Na szerszym koszyku momentum przekrojowe jest **nierozstrzygnięte i słabsze niż w X1**:
+15,9 %/rok [−12,3; +44,2], t 1,10, IC równe zeru, połowa sumy w 33 dniach, 2022 −20 %. Walidacja
krzyżowa pokazała, że reguła X1 liczona na innej siatce tygodniowej daje +9 %/rok zamiast +22 %:
**X1 zależało od fazy kalendarza rebalansów** — niezmierzony wcześniej składnik niepewności.
Odczyt rodziny B1 po dwóch odczytach: „hipoteza ze słabym poparciem, bez dowodu; sygnał
w ogonach i w nodze short, nie w monotonicznym rankingu" (wniosek 68). Seria X2 zamknięta 1/1.

## Rekomendacja

1. **Zamknąć rodzinę B1 (momentum przekrojowe) na tych danych** — trzeci odczyt (inna szerokość,
   inne okno) nic nie rozstrzygnie; jedyna uczciwa droga to pomiar prospektywny (paper) z regułą
   zamrożoną dziś i wszystkimi fazami tygodnia naraz (7 równoległych portfeli), przez ≥ 2 lata.
2. **Metodologicznie (wniosek 68):** dla strategii z rebalansem kalendarzowym raportować
   rozrzut po fazach (jak fold-jitter) obok CI — CI z jednej fazy zaniża niepewność; korekta
   szumu z symulacji H0: ×1,5 dla szerokich koszyków, nie ×1,3.
3. Nie łączyć X1/X2 z cechami modelu 4h ani z O1 (kombinacje po wyniku — wniosek 49).

## Użyte skille

Rejestr gałęzi `x2-momentum-top50` (`py tools/skill_audit.py raport --galaz x2-momentum-top50`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → pre-rejestracja z mocą (symulacja ×1,3) → commit → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | „szerokość zamiast wariantu", odczyt łączny X1+X2 zapisany PRZED X2 (bez sumowania/wyboru), test w granicy dużego n |
| `anthropic-skills:quant-strategy-catalog` | rodzina B1: drugi wariant rodziny na mocy decyzji użytkownika; pułapki ogona płynności, breadth efektywna |
| `data:validate-data` | bramka 16a: tożsamość sum, rachunek tygodniowy bez dryfu, X1 na wspólnym oknie (wykrycie wrażliwości na fazę), „kogo nie ma", ogony |
| `data:statistical-analysis` | bramka 16b: X1 i X2 obok siebie, CI z N_eff, mediana i ogony, IC z CI, nazwanie stanu rodziny wg pre-rejestracji |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Pominięte: `engineering:testing-strategy` (bez nowego modułu — skrypt to reporter z trzema
stałymi; maszyneria przetestowana w X1), `security-review` (bez sieci), `dataviz`,
`engineering:architecture`, `update-config`, `ta-toolkit`, `lean-research`.
