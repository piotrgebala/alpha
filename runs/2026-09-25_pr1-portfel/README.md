# PR1 — reguły portfela nóg dziennika pod szczebel 4 (mała realna kwota) (2026-09-25)

> **STATUS: ZAKOŃCZONA** (2026-09-25; pre-rejestracja `7f647f2` przed przebiegiem). Opisowo, 0 wariantów — zwroty nóg są już odczytane;
> PR1 nie mierzy przewagi, tylko profil ryzyka portfela przy zapisanych z góry regułach alokacji.
> Decyzja o realnym kapitale (szczebel 4 ADR-09) należy do użytkownika po odczycie dziennika ~2026-12-25.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Dziennik dzieli ryzyko między trend i premię Coinbase według zmienności (1/σ), z celem 20 %/rok. Przy
realnych pieniądzach trzeba wiedzieć z góry: ile można stracić w zły tydzień, w zły miesiąc i w najgorszej
serii, oraz jak przełożyć „najwyżej 5 % kapitału jako depozyt” na wielkość strategii. PR1 liczy to na
historii nóg i sprawdza, czy wagi liczące korelacje (ERC — każda noga wnosi tyle samo ryzyka do portfela)
zmieniałyby coś wobec obecnych 1/σ. Uczciwie z góry: przy DWÓCH nogach ERC i 1/σ to matematycznie to samo;
różnica może się pojawić dopiero przy trzech (gdyby X1 kiedyś dołączył).

## Metadane

- Branch `pr1-portfel` (z `master` `042dceb`). Skrypt `backtest/run_pr1_portfel.py`, testy `tests/test_pr1_portfel.py` (5).
  Po przebiegu jedna poprawka odporności (przegląd 16c): brak zbieżności optymalizatora ERC podnosi błąd zamiast po cichu
  zwracać wagi 1/σ; ponowny przebieg po poprawce daje `raw_output.txt` identyczny co do bajtu (kontrola w `druga_droga.txt`).
  Komenda: `PYTHONUTF8=1 py -m backtest.run_pr1_portfel` → `raw_output.txt`.
- Dane: dzienne zwroty netto nóg przy k = 1 z `run_kr1_korelacje.legs()` (TS1 i X1 na `universe_full`, CP1 jak CP1;
  wspólne okno 2021-05-08 → 2026-06-30, 1 880 dni). Reguły R0/R1 z `sizing.apply_rules` bez zmian (parametry
  dziennika: cel 20 %/rok, sufit 2, EWMA com 45, krok 7 dni, rozbieg 60 — SZ1); ERC nowa funkcja z tymi samymi
  parametrami; dźwignie nóg jak w dzienniku: trend 2×, CP1 3×, X1 1×.

## Poprzedzające wyniki

SZ1 (77): R1 (budżet ryzyka) ~+19 %/rok, obsunięcie ~18–19 %, depozyt ~23 %; hamulec po stracie szkodzi.
KR1 (95): korelacje nóg 0,16–0,35, w złych dniach niższe. KO1 (99): koszty nie są wąskim gardłem. ADR-09:
szczebel 4 = ≤ 5 % kapitału jako depozyt, dźwignie jak w dzienniku, STOP portfela 27,6 %.

## Pre-rejestracja (opisowo)

- **Zestawy nóg:** {TS1, CP1} (dziennik) i {TS1, CP1, X1} (gdyby X1 dołączył).
- **Reguły:** R0 równo; R1 = dziennik (1/σ); ERC (równy wkład ryzyka z korelacjami). Bez hamulca (SZ1: szkodzi).
- **Miary (na 100 % kapitału strategii):** CAGR, zmienność, max obsunięcie, najgorszy dzień/tydzień/miesiąc,
  ES 95 % tygodniowy (średnia 5 % najgorszych tygodni), ES 99 % dzienny; mediany i p10–p90 mnożników; depozyt
  jako udział kapitału (Σ k/dźwignia).
- **Przełożenie ADR-09:** depozyt 5 % całego kapitału → kapitał strategii = 5 % / medianowy udział depozytu;
  straty w % CAŁEGO kapitału.
- **Odczyt:** opisowy; żadna reguła nie jest „wybierana” po wyniku. Oczekiwanie zapisane z góry: dla 2 nóg
  |k R1 − k ERC| ≈ 0; dla 3 nóg ERC przesuwa wagę ku nodze najmniej skorelowanej. Punkt odniesienia dla każdej
  przyszłej reguły przełączania = stała mieszanka R1 (liczby z tej rundy).
- **Czego runda NIE robi:** nie zmienia dziennika, nie stroi celu zmienności ani sufitu, nie mierzy przewagi
  (składowe in-sample — liczby to profil ryzyka, nie prognoza).

---

## Wynik w skrócie — prostym językiem

1. **Przy dwóch nogach dziennika (trend + premia Coinbase) wagi „z korelacjami” (ERC) to dokładnie obecne wagi 1/σ** —
   największa różnica mnożników na 1 880 dniach: 0,0000. To nie jest wynik pomiaru, tylko tożsamość matematyczna: przy
   dwóch składnikach równy wkład ryzyka oznacza w₁σ₁ = w₂σ₂ niezależnie od korelacji. **Dziennika nie ma po co zmieniać.**
2. **Profil ryzyka portfela dziennika (R1) na 100 % kapitału strategii** (in-sample, 2021-05 → 2026-06): ≈ +18 %/rok,
   zmienność 22 %, największe obsunięcie 18 %, najgorszy tydzień −9,7 %, najgorszy miesiąc −7,8 %, ES95 tygodniowy
   (średnia z 5 % najgorszych tygodni, 14 tygodni z 269) −5,7 % [bootstrap 95 %: −6,5; −4,7]. To profil, nie prognoza —
   nogi zostały wybrane na tej samej historii.
3. **Przełożenie na „najwyżej 5 % kapitału jako depozyt” (ADR-09):** przy depozycie liczonym tak, żeby limit trzymał się
   KAŻDEGO dnia (Σ k/dźwignia = wszystkie nogi w pełni w rynku; mediana 49 %), strategia dostaje **≈ 10 % całego kapitału**.
   Wtedy zły tydzień to ≈ −1,0 % całego kapitału, najgorsza seria ≈ −1,9 %, ES95 ≈ −0,6 %, a zysk ≈ +1,9 pkt/rok całego
   kapitału. Realny depozyt (nogi nie zawsze są w rynku) ma medianę 24 % i maksimum 45 % — limit liczony po dniu
   największego realnego depozytu daje ten sam wynik (≈ 11 % kapitału). Liczenie po MEDIANIE realnego depozytu (≈ 21 %
   kapitału) łamałoby limit 5 % w połowie dni — dlatego nie jest wariantem do wyboru.
4. **X1 jako trzecia noga pogarsza profil:** obsunięcie 18 → 28 %, najgorszy tydzień −9,7 → −27,5 % (jeden tydzień X1:
   −50,7 %, wystrzał MYX z RU1), zysk 18 → 13 %/rok. ERC przesuwa wagę ku X1 (najmniej skorelowana noga) i nic nie
   naprawia — ryzyko X1 siedzi w ogonie, nie w zmienności. **X1 zostaje w dzienniku papierowym, nie w portfelu na pieniądze.**

## Wynik

Wspólne okno 1 880 dni (2021-05-08 → 2026-06-30); parametry dziennika: cel 20 %/rok, sufit k ≤ 2, EWMA com 45, krok 7 dni,
rozbieg 60. Pełny wydruk: `raw_output.txt`. Wszystkie liczby na 100 % kapitału strategii, o ile nie zaznaczono inaczej.

**Nogi osobno (k = 1):**

| noga | CAGR | zmienność | max obsunięcie | najg. dzień | najg. tydzień | najg. miesiąc | ES95 tyg. | ES99 dz. |
|---|---|---|---|---|---|---|---|---|
| TS1 (trend) | +7,5 % | 18,2 % | 19,4 % | −6,2 % | −7,2 % | −7,6 % | −5,0 % | −3,5 % |
| X1 (momentum przekrojowe, 7 faz) | +0,5 % | 35,9 % | 55,0 % | −32,6 % | −50,7 % | −35,7 % | −11,7 % | −8,7 % |
| CP1 (premia Coinbase) | +29,7 % | 34,8 % | 34,3 % | −9,0 % | −14,7 % | −12,0 % | −9,1 % | −6,4 % |

**Portfele:**

| zestaw | reguła | CAGR | zmienność | max obs. | najg. dzień | najg. tydzień | najg. miesiąc | ES95 tyg. | ES99 dz. |
|---|---|---|---|---|---|---|---|---|---|
| TS1+CP1 | R0 równo | +19,8 % | 21,8 % | 19,3 % | −6,0 % | −9,9 % | −7,0 % | −5,5 % | −4,3 % |
| TS1+CP1 | **R1 dziennik (1/σ)** | **+18,3 %** | **21,6 %** | **18,2 %** | **−6,4 %** | **−9,7 %** | **−7,8 %** | **−5,7 %** | **−4,4 %** |
| TS1+CP1 | ERC (korelacje) | +18,3 % | 21,6 % | 18,2 % | −6,4 % | −9,7 % | −7,8 % | −5,7 % | −4,4 % |
| TS1+CP1+X1 | R0 równo | +14,9 % | 20,8 % | 19,7 % | −11,6 % | −19,4 % | −15,7 % | −6,4 % | −4,4 % |
| TS1+CP1+X1 | R1 dziennik (1/σ) | +13,4 % | 22,5 % | 28,0 % | −16,7 % | −27,5 % | −25,2 % | −7,1 % | −5,0 % |
| TS1+CP1+X1 | ERC (korelacje) | +12,6 % | 22,7 % | 28,3 % | −16,7 % | −27,5 % | −25,4 % | −7,2 % | −5,0 % |

**Mnożniki i depozyt** (mediana [p10; p90]):

| zestaw | reguła | k TS1 | k CP1 | k X1 | \|k R1 − k ERC\| max | depozyt Σ k/dźwignia |
|---|---|---|---|---|---|---|
| TS1+CP1 | R1 = ERC | 0,73 [0,50; 1,02] | 0,37 [0,28; 0,51] | — | **0,0000** | 49 % [36; 67] |
| TS1+CP1+X1 | R1 | 0,56 [0,35; 0,77] | 0,28 [0,21; 0,38] | 0,33 [0,19; 0,47] | 0,0965 | 68 % [48; 96] |
| TS1+CP1+X1 | ERC | 0,54 [0,33; 0,77] | 0,29 [0,22; 0,42] | 0,32 [0,20; 0,47] | | 67 % [48; 96] |

**Przełożenie ADR-09 (R1, depozyt 5 % całego kapitału, limit trzymany każdego dnia — Σ k/dźwignia):**

| zestaw | kapitał strategii (% całego) | max obsunięcie | najg. tydzień | ES95 tyg. | CAGR (pkt/rok całego kapitału) |
|---|---|---|---|---|---|
| TS1+CP1 | ≈ 10 % | 1,9 % | −1,0 % | −0,6 % | +1,9 |
| TS1+CP1+X1 | ≈ 7 % | 2,1 % | −2,0 % | −0,5 % | +1,0 |

### Druga droga (bramka 16a) — `druga_droga.py` → `druga_droga.txt`

Skrypt niezależny od `run_pr1_portfel.main()`: nogi TS1 i CP1 zbudowane wprost z `ts_momentum.portfolio` (z kolumną
`gross_notional`, jak w SZ1), potem reguła R1 na tych samych 1 880 dniach.

- **Nogi:** identyczne z `run_kr1_korelacje.legs()` co do bajtu (max |Δ| = 0 dla TS1 i CP1).
- **Depozyt REALNY** (k · nominał / dźwignia, definicja SZ1): mediana **23,9 %** [p10 14; p90 37], p99 44 %, **max 45 %** — zgodne
  z SZ1 (23,2 %). Górne oszacowanie z pre-rejestracji (Σ k/dźwignia, nogi w pełni w rynku): mediana 48,9 %, max 82 %. Różnica to
  ekspozycja nóg (mediana nominału: trend 0,38×, CP1 0,76× kapitału), nie błąd. Limit 5 % liczony po realnym MAKSIMUM (45,5 %) daje
  kapitał strategii 11,0 % (wobec 10,2 % z pre-rejestracji) — obie drogi zgodne do 1 pkt.
- **ES95 tygodniowy:** −5,68 % z 14 tygodni ogona (269 tygodni); bootstrap 4 000 losowań: **[−6,52 %; −4,69 %]**. Trzy najgorsze
  tygodnie: −9,7 %, −6,4 %, −6,3 %. Rozkład tygodni: średnia +0,37 %, mediana +0,24 %, sd 2,95 %, skośność +0,79, kurtoza 3,2,
  43 % tygodni ujemnych.
- **Max obsunięcie** inną formułą (log-cumsum): 18,19 % = 18,19 %. **CAGR** kalendarzowo (5,14 roku): +18,37 % wobec +18,35 %
  (dni/365 w `summary`).
- **ERC ≡ 1/σ dla dwóch nóg** — analitycznie: wkłady ryzyka w₁(Σw)₁ = w₁²σ₁² + w₁w₂ρσ₁σ₂ i w₂(Σw)₂ = w₂²σ₂² + w₁w₂ρσ₁σ₂ są równe
  wtedy i tylko wtedy, gdy w₁σ₁ = w₂σ₂; test jednostkowy sprawdza to dla ρ ∈ {−0,5; 0; 0,7}.

## Co na plus (+) / Co na minus (−)

**(+)**
- Oczekiwanie zapisane z góry spełnione bez „dopasowania”: |k R1 − k ERC| = 0,0000 przy 2 nogach; przy 3 nogach ERC przesuwa wagę
  ku nodze najmniej skorelowanej (X1: 0,33 → 0,32 mediana, ale w środku okna do +0,10) — jak przewidziano.
- Cztery kluczowe liczby przeliczone niezależnie (nogi, depozyt, ES95, obsunięcie/CAGR) — zgodne.
- Profil ryzyka zapisany PRZED jakimkolwiek realnym kapitałem; punkt odniesienia (stała mieszanka R1) istnieje.
- Reguła R1 nie była zmieniana ani strojona; żadna reguła nie została „wybrana po wyniku”.

**(−)**
- **Nogi in-sample:** TS1/CP1 wybrane spośród ~30 odczytów na tej samej historii (AU4: DSR CP1 0,52). Profil ryzyka na tych nogach
  jest raczej optymistyczny — zysk i obsunięcie prawdziwej przyszłości mogą być gorsze.
- **Bez modelu likwidacji:** `legs()` z KR1 nie zawiera kosztu likwidacji izolowanej (SZ1: ~1,2 pkt/rok na trendzie przy 2×) — stąd
  R1 +18,3 % tutaj wobec +17,1 % w RU1/SZ1. Ogon obsunięcia z likwidacją wewnątrz tygodnia jest niezmierzony.
- **ES95 z 14 tygodni** — przedział ±0,9 pp; „najgorszy tydzień” to jedna obserwacja, nie parametr rozkładu.
- **Tygodnie W-FRI** — pierwszy (1 dzień) i ostatni (2 dni) tydzień niepełne; wpływ na ogon pomijalny (zaniżają, nie zawyżają).
- **X1:** ogon z jednego zdarzenia (MYX); ES95 X1 −11,7 % nie oddaje tygodnia −50,7 % — dla nóg z grubym ogonem ES na 5 latach
  jest miarą niewystarczającą.

**Kogo NIE ma w zbiorze:** lat 2018–2020 (bessa 2018, marzec 2020) — okno zaczyna się 2021-05 (zasada 20 + rozbieg); dni po
2026-06-30 (dziennik na żywo); likwidacji wewnątrz dnia/tygodnia; kosztu poślizgu przy większym kapitale (KO1: koszty ~1–3 %/rok
przy zleceniach rynkowych na małej kwocie); zdarzeń giełdowych (awaria, delisting w trakcie tygodnia).

**Czerwona flaga „wynik idealnie potwierdza hipotezę”:** tożsamość ERC ≡ 1/σ jest wynikiem z konstrukcji, nie z danych — więc
„idealna” zgodność jest oczekiwana i nie jest sygnałem ostrzegawczym; różnica przy 3 nogach (0,0965) pokazuje, że kod ERC działa.

## Wniosek

Dla portfela dziennika (trend + premia Coinbase) reguła 1/σ z celem 20 %/rok jest już tym, co dałyby wagi z korelacjami — nie
ma czego poprawiać w alokacji. Przy limicie „5 % kapitału jako depozyt” liczonym tak, żeby trzymał się każdego dnia, strategia
zajmuje ≈ 10 % całego kapitału i w najgorszej historycznej serii kosztuje ≈ 2 % całego kapitału (zły tydzień ≈ 1 %) — to
skala straty, jakiej należy się spodziewać na szczeblu 4, jeśli przyszłość wygląda jak przeszłość (a nogi są in-sample, więc
raczej gorzej). Dołożenie X1 zwiększa obsunięcie o połowę i wprowadza ogon jednego zdarzenia — nie na pieniądze.

## Rekomendacja

1. **Dziennik bez zmian** (R1 = 1/σ, cel 20 %, sufit 2). ERC wraca na stół dopiero przy trzeciej nodze, która przejdzie drabinę.
2. **Szczebel 4 (decyzja użytkownika po odczycie ~2026-12-25):** depozyt ≤ 5 % całego kapitału liczony górnym oszacowaniem
   (Σ k/dźwignia) → kapitał strategii ≈ 10 % całego; budżet straty do zapisania z góry: zły tydzień −1 %, seria −2 % całego
   kapitału; STOP portfela 27,6 % z ADR-09 (na kapitale strategii) odpowiada ≈ −2,8 % całego kapitału.
3. **X1 tylko w dzienniku papierowym.** Warunek wejścia do portfela: przejście drabiny ADR-09 + ogon tygodniowy poniżej −20 % na
   100 % kapitału strategii nie może pochodzić z jednego zdarzenia (do zapisania w pre-rejestracji, gdy przyjdzie czas).
4. **Punkt odniesienia dla każdej przyszłej reguły przełączania/ważenia:** stała mieszanka R1 z liczbami z tej rundy; nowa reguła
   musi pokazać poprawę ES95 lub obsunięcia przy niepogorszonym CAGR — a każdy taki odczyt na tej historii to nowy wariant.

## Bramki jakości (CLAUDE.md zasada 16)

- **16a walidacja (`data:validate-data`): Ready (Caveats).** Druga droga wyżej (4 liczby zgodne, definicja depozytu wyjaśniona);
  „kogo nie ma” wyżej. Caveats do przekazania: nogi in-sample, bez likwidacji, ES95 z 14 obserwacji, limit 5 % liczony
  po górnym oszacowaniu (świadomie konserwatywnie).
- **16b statystyka (`data:statistical-analysis`):** efekt z przedziałem (ES95 bootstrap), mediana obok średniej (tygodnie +0,24 %
  vs +0,37 %), zakresy p10–p90 mnożników, licznik wariantów 0 (opisowo, 6 odczytów profilu bez wyboru reguły). Bez testów
  istotności — runda nie mierzy przewagi.
- **16c przegląd diffu (`engineering:code-review`): Approve.** `apply_erc` odwzorowuje `sizing.apply_rules` R1 (k = min(sufit,
  w·cel/σ_portfela), dane sprzed dnia, krok 7, rozbieg 60 — potwierdzone tożsamością 0,0000); jedna poprawka po przeglądzie:
  brak zbieżności SLSQP podnosi `RuntimeError` zamiast cichej podmiany wag (reporter neutralny), przebieg po poprawce identyczny
  co do bajtu. Testy: 5 (tożsamość 2 nóg dla trzech ρ, ERC 3 nóg = równe wkłady, brak zaglądania w przyszłość + rozbieg + sufit,
  miary na znanym szeregu, arytmetyka depozytu). Bez testu dymnego `main()` (wymaga danych) — jak w SZ1/KR1.

## Użyte skille (CLAUDE.md zasada 19)

Wynik `py tools/skill_audit.py raport --galaz pr1-portfel`:

| czas (UTC) | skill | co wniósł |
|---|---|---|
| 12:21:31 | `anthropic-skills:clas5-runda` | procedura rundy: gałąź → skille → INDEX/README powiązane → pre-rejestracja w osobnym commicie → bramki → DoD |
| 12:21:33 | `anthropic-skills:clas5-quant` | sizing: sufit jawnym `min()`, cel zmienności z danych sprzed dnia, ES/obsunięcie jako profil in-sample (nie prognoza), N_eff nie dotyczy (bez werdyktu) |
| 12:21:35 | `engineering:testing-strategy` | plan testów: tożsamości analityczne (2 nogi, nieskorelowane 3), brak zaglądania w przyszłość przez zmianę przyszłości, znany szereg dla miar |
| 12:24:40 | `data:validate-data` | bramka 16a: druga droga (depozyt realny vs górne oszacowanie, ES95 bootstrap, DD/CAGR inną formułą), „kogo nie ma”, czerwona flaga |
| 12:24:40 | `data:statistical-analysis` | bramka 16b: przedział bootstrap dla ES z 14 obserwacji, mediana obok średniej, zakresy zamiast fałszywej precyzji |
| 12:24:40 | `engineering:code-review` | bramka 16c: przegląd `erc_weights`/`apply_erc`/`risk_metrics`/`margin_share` + testów; poprawka odporności ERC |

Razem 6 wczytań, 6 skilli. Skille z tabeli zasady 19, których moment runda obejmowała, a których nie ma w rejestrze:
`dataviz` — bez wykresu (tabele wystarczają; profil ryzyka to 6 wierszy liczb); `quant-strategy-catalog` — bez nowej hipotezy
(reguły alokacji, nie strategia); `data:explore-data` — bez nowego zbioru danych (nogi z KR1); `security-review` — bez kluczy,
zleceń i sieci. `discernment-nudge` niedostępny w sesji (jak w poprzednich rundach) — pytania kontrolne zastąpione sekcją
„kogo nie ma” i czerwoną flagą wyżej.
