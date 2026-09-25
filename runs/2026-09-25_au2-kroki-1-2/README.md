# AU2 kroki 1–2 — moc przyrządu przekrojowego z ML: ramię negatywne i siatka sił (2026-09-25)

> **STATUS: ZAMKNIĘTA — ML przekrojowe NIE startuje (reguła z pre-rejestracji).** Pipeline uczciwy: 0/40
> fałszywych alarmów [0; 9 %]. Ale przy realistycznych siłach ML wykrywa sygnał rzadko: +10 %/rok → 25 %
> [11; 47], +15 %/rok → 35 % [18; 57] — nie więcej niż prosty przyrząd tygodniowy (AU1: 25 % / ~50 %),
> a ranking wprost po właściwej cesze wykrywa to samo w 80–85 %. **Przeszukiwanie 24 konfiguracji
> kosztuje ~2/3 mocy.** Przy okazji: **błąd kanonicznego N_eff** (ujemny mianownik → N_eff = 1) —
> decyzja użytkownika. Kalibracja — 0 wariantów. Walidacja (16a): **Caveats**; przegląd (16c): **Approve**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Krok 0 pokazał, że test rankingu monet jest czuły. Teraz sprawdzamy, czy **model ML z szerokim
przeszukiwaniem** nie oszukuje: (1) na danych, w których z góry zniszczyliśmy każdy związek cech
z przyszłym zwrotem (zwroty przemieszane między monetami w każdym dniu), nie powinien „znajdować”
zysku częściej niż w ~5 % prób; (2) na danych, do których dołożyliśmy sygnał o znanej sile
(+5 … +30 %/rok dla kogoś, kto zna go idealnie), mierzymy, jak często ten sygnał wykrywa. Obok
liczymy prosty ranking po tej jednej cesze, która niesie sygnał — to górna granica (ktoś, kto wie,
gdzie szukać). Różnica = koszt szukania po 24 konfiguracjach.

## ID testu

**AU2 kroki 1–2** — ciąg dalszy AU2 kroku 0 (wniosek 92). Decyzje użytkownika 2026-09-25
(„wykonaj to jak zaproponowałeś”, szkic `runs/2026-09-25_au2-moc-przekrojowa/karta_krokow_1_2.md`):
zbiór cech A, budżet 8 zestawów × 3 modele, drugi warunek werdyktu `ci_low(średnie IC) > 0`.

## Metadane

- Branch `au2-kroki-1-2` (z `master` `401832f`). Skrypt `backtest/run_au2_ml.py`, testy
  `tests/test_au2_ml.py` (9: przeciek cech — obcięcie danych po t nie zmienia cech t; permutacja;
  koszyk; fazy; werdykt; kwartały; modele). Komenda: `PYTHONUTF8=1 py -m backtest.run_au2_ml`
  → `raw_output.txt` + `przebiegi.csv`.
- Dane: `universe_full`, top-50 miesięcznie (skład z danych sprzed miesiąca, jak krok 0), funding
  per symbol, `oi_panel` (OI wartość). Dni 2021-02-01 → 2026-06-23 (1 969), test 2022-04-01 →
  (17 kwartałów), par/dzień ~50. Koszt `taker_fee + slippage` z `config/settings.yaml` × obrót.
- **Cechy (lista A, zamrożona):** r7, r28, r90 (zwroty), vol30 (zmienność), turn30 (log obrotu 30 d),
  dturn (log obrót 7 d / 30 d), fund7 (suma fundingu 7 d), doi7 (log zmiany OI 7 d), beta90 (do BTC),
  dist90 (odległość od maksimum 90 d) + **nośnik x** (losowy AR(1), półtrwanie 28 d; w ramieniu
  negatywnym bez związku, w pozytywnym niesie sygnał). Wszystkie jako ranga w przekroju członków.
  Pokrycie komórek: 100 % poza r90 91 %, beta90/dist90 96 %, **doi7 34 %** (panel OI niepełny — TL1).
- **Budżet przeszukiwania (24):** 8 zestawów (S1 wszystkie; S2 cena; S3 ryzyko; S4 płynność;
  S5 pozycjonowanie; S6 cena+ryzyko; S7 cena+płynność+pozycjonowanie; S8 bez beta/dist) — każdy + x —
  × 3 modele (ridge numpy α=1; XGBoost regresja rangi; XGBoost ranking pairwise; 100 drzew,
  głębokość 3, eta 0,05). W każdym kwartale wybór 1 z 24 po średnim dziennym IC na walidacji
  (ostatnie 90 dni okna), refit na całym oknie 365 dni. **Purging 7 + embargo 7 dni** na granicy
  trening/test i trening/walidacja (precedens Z17/Z21).
- Koszyk: long 10 / short 10 z ~50, trzymanie 7 dni, formowanie codzienne (7 faz), koszt × obrót
  względem portfela tej samej fazy tydzień wcześniej. Funding pominięty (kalibracja przyrządu).
- **Ramiona:** negatywne S = 40 (cel permutowany); pozytywne 5 sił × S = 20: cel permutowany +
  a · z(x), `a` tak, by wyrocznia (ranking po x, po kosztach) miała +5 / +10 / +15 / +20 / +30 %/rok.
  Ziarna 1000+i (neg), 2000+100·siła+i (pos). Próba techniczna: ziarno 999999.

## Poprzedzające wyniki

- **AU2 krok 0 (92):** top-50 ~17,7 niezależnych zakładów; MDE IC 0,022; na IR 0,75 potrzeba IC 0,025.
- **K1/K2 (kontrola pozytywna aparatu), wniosek 41:** kalibracja tylko na danych ze znanym sygnałem —
  stąd permutacja i wstrzyknięcie przez nośnik (siła znana z konstrukcji).
- **AU1 (87):** przyrząd prosty (strategie tygodniowe na 5,4 roku): moc 25 % przy +10 %/rok, 73 % przy
  +20 %/rok — punkt odniesienia z innego ustawienia.
- **Z17/Z21:** early stopping / walidacja bez embargo zawyżały p → purging i embargo tutaj.
- **Wniosek 11:** nawet dobry przyrząd nie pomoże, jeśli cechy nie niosą informacji — AU2 mierzy
  przyrząd, nie cechy.

## Pre-rejestracja

- **Werdykt pojedynczego przebiegu (dla ML i dla prostego):** POZYTYWNY, gdy t_neff tygodniowego
  zwrotu netto (średnia 7 faz) > 1,96 ORAZ dolny kraniec CI 95 % średniego dziennego rank IC
  (se z N_eff) > 0.
- **Krok 1 — odczyt:** odsetek POZYTYWNYCH w ramieniu negatywnym (ML). Nominał ≤ ~2,5–5 %.
  **Twardy STOP (pipeline przecieka): ≥ 6/40** (P ≤ 0,05 przy prawdziwych 5 %). Wtedy nic z kroku 2
  się nie liczy.
- **Krok 2 — odczyt:** moc = odsetek POZYTYWNYCH przy każdej sile; ML obok prostego (górna granica
  z wiedzą o cesze) i obok AU1 (25 % przy +10, 73 % przy +20). Siły realistyczne a priori: +10 … +15 %/rok
  (krok 0: IC ~0,025 ≈ +20 %/rok brutto to już więcej niż cokolwiek widziane na tych danych).
- **Reguła decyzji (bramkowa — użytkownik; zapisana z góry):**
  - ramię negatywne ≥ 6/40 → pipeline zepsuty, koniec;
  - moc ML przy +10 i +15 %/rok nie wyższa niż AU1 w tych siłach (≈ 25 % / ~50 %) → ML nie jest
    lepszym przyrządem niż prosty tygodniowy — projekt ML nie startuje;
  - wyższa → wariant ML może dostać własną pre-rejestrację i licznik (z zaleceniem NOWYCH danych,
    wniosek 11).
  Bez progu „moc ≥ X % = GO”.
- **Granica dużego n:** więcej lat → wyższa moc i niezmienny nominał — kryterium nie karze celu.
- **Czego runda NIE robi:** nie mierzy prawdziwych cech (cel permutowany w obu ramionach), nie stroi
  budżetu po wyniku, nie dotyka dziennika.

## Odstępstwo po przebiegu 1 (zapisane PRZED przebiegiem 2)

Przebieg 1 (`raw_output_przebieg1_kanoniczny.txt`, `przebiegi_przebieg1.csv`) ujawnił błąd przyrządu
kanonicznego: przy tym samym zysku t_neff wychodzi 3–8 albo ~0,4. Przyczyna (odtworzona, `engineering:debug`):
`agents/labeling.py::effective_sample_size` sumuje 50 zaszumionych autokorelacji; gdy suma < −0,5,
mianownik `1 + 2Σρ` < 0 → N_eff ujemne → `carry_hedged.summarize_pnl` przycina do **1**
(`checkpoint_lib.summarize_trade_returns` daje wtedy NaN). Błąd tylko zaniża pewność (fałszywe
„nierozstrzygnięte”), nigdy nie tworzy fałszywego sukcesu.
**Przebieg 2** = te same ziarna i ten sam kod ML (wyniki ML identyczne), do każdego werdyktu dopisany
werdykt z `n_eff_guarded` (mianownik ≤ 0 → N_eff = n, czyli bez korekty; ujemna autokorelacja czyni
zwykły błąd zachowawczym). **Odczyt główny: werdykt poprawiony; kanoniczny raportowany obok.**
Reguła decyzji bez zmian. Kanonicznego kodu nie zmieniono (decyzja użytkownika — metodologia pomiaru
i moduł importowany pośrednio przez dziennik). Przebieg 2: 24 procesy, 1 wątek numeryczny na proces
(przebieg 1 przeciążał serwer).

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Dobra wiadomość: model ML z szerokim przeszukiwaniem **nie wymyśla zysków** — na danych, w których
nie ma żadnego sygnału, ani razu na 40 prób nie ogłosił sukcesu. Zła wiadomość: gdy sygnał jest,
ale realistycznej wielkości (+10–15 % rocznie dla kogoś, kto zna go idealnie), model wykrywa go
tylko w co czwartej – co trzeciej próbie. Ktoś, kto wie, na którą cechę patrzeć, wykrywa ten sam
sygnał w 8 na 10 prób. Różnica to cena szukania „na ślepo” po 24 konfiguracjach: model gubi się
wśród cech bez informacji i wybiera złe konfiguracje. Wniosek dla projektu: **ML na rankingach monet
nie jest lepszym przyrządem niż proste reguły tygodniowe** — nie budujemy go na tych danych.

## Wynik

Pełny stdout: `raw_output.txt` (przebieg 2, 773 s); przebieg 1 (werdykt kanoniczny): `raw_output_przebieg1_kanoniczny.txt`.
Wyniki per przebieg: `przebiegi.csv`, surowe: `przebiegi_surowe.pkl`. Odczyt główny = werdykt z poprawionym N_eff.
Przedziały 95 % Wilsona.

| ramię / siła wyroczni | ML (24 konfiguracje) — moc | prosty (ranking po nośniku) — moc | ML: IC / netto (mediany) | prosty: IC / netto |
|---|---|---|---|---|
| negatywne (S = 40) | **0/40 = 0 % [0; 9]** | 0/40 = 0 % | −0,0005 / −4,9 %/rok | −0,0007 / −2,7 %/rok |
| +5 %/rok (S = 20) | 0 % | 10 % | +0,008 / +0,0 % | +0,018 / +7,4 % |
| **+10 %/rok** | **25 % [11; 47]** | 80 % [58; 92] | +0,018 / +7,2 % | +0,028 / +13,1 % |
| **+15 %/rok** | **35 % [18; 57]** | 85 % [64; 95] | +0,027 / +10,6 % | +0,037 / +17,7 % |
| +20 %/rok | 80 % [58; 92] | 95 % | +0,041 / +14,2 % | +0,047 / +20,4 % |
| +30 %/rok | 100 % | 100 % | +0,064 / +28,5 % | +0,069 / +30,9 % |

Werdykt kanoniczny (błędny N_eff) dawał moc ML 0 / 25 / 20 / 65 / 65 % i prostego 10 / 50 / 70 / 75 / 70 % —
nasycenie ~70 % przy +30 %/rok zdradziło błąd. Ramię negatywne: 0/40 w obu wersjach.
Wybory przeszukiwania (konfiguracja × kwartał): najczęściej ridge na zestawach pozycjonowanie / ryzyko /
płynność (309 / 267 / 249 z 2 380) — każdy zestaw zawiera nośnik, więc wybór zestawu decyduje, ile szumu
model dostaje razem z sygnałem.

**Odczyt wg reguły:** ramię negatywne 0/40 (< 6/40) → pipeline OK; moc ML przy +10 / +15 %/rok = 25 / 35 %
— nie wyższa niż AU1 (25 % / ~50 %) → **ML nie jest lepszym przyrządem; projekt ML przekrojowego nie startuje.**

## Błąd kanonicznego N_eff (znalezisko uboczne, ważne dla całego projektu)

`agents/labeling.py::effective_sample_size`: `N_eff = N / (1 + 2·Σρ_k, k = 1..50)` bez ucinania sumy.
Na krótkich szeregach (np. 221 tygodni) suma 50 zaszumionych autokorelacji spada czasem poniżej −0,5 →
mianownik ujemny → N_eff ujemne (odtworzone: −990; test regresji: −6 080). `carry_hedged.summarize_pnl`
robi wtedy `max(1, min(N_eff, n))` = **1** (t_neff ≈ średnia/sd ≈ 0,4), a
`checkpoint_lib.summarize_trade_returns` — `sqrt(ujemne)` = **NaN**. Tu dotknęło ~25–30 % przebiegów.
**Kierunek błędu:** tylko zaniża pewność → możliwe fałszywe „NIEROZSTRZYGNIĘTY”, nigdy fałszywe
„POZYTYWNY”. Korzysta z niego ~25 skryptów rund. Naprawa kanoniczna + audyt dawnych werdyktów =
**decyzja użytkownika** (metodologia pomiaru; moduł pośrednio importowany przez dziennik). W tej rundzie:
lokalne `n_eff_guarded` (mianownik ≤ 0 → N_eff = n), test regresji w `tests/test_au2_ml.py`.

## Co na plus (+) / Co na minus (−)

**(+)**
- Kontrola, której projekt nie miał: pełny pipeline ML z przeszukiwaniem, purgingiem i embargo — 0/40
  fałszywych alarmów; siła sygnału znana z konstrukcji (permutacja + nośnik), zero kontaminacji prawdziwymi cechami.
- Przeliczenie drugą drogą: moc prostego przy +10 %/rok (80 %) zgodna z MDE z kroku 0 przeskalowanym na
  4,2 roku testu (~0,025 wobec mediany IC 0,028); przebiegi 1 i 2 identyczne co do liczby (deterministyczne ziarna).
- Wykryty błąd przyrządu kanonicznego — tym właśnie jest kalibracja.

**(−)**
- S = 20 na siłę → szerokie przedziały (±20 pp); różnica ML vs prosty przy +10 %/rok pewna (przedziały
  rozłączne), ML vs AU1 — nie (AU1 z innego ustawienia: strategie tygodniowe na 5,4 roku, nie koszyk).
- Sygnał wstrzyknięty liniowo w jedną cechę — ML nie ma przewagi nieliniowej, którą mógłby pokazać;
  sygnał nieliniowy lub rozproszony po cechach mógłby wypaść inaczej (ale to też trudniejsze do znalezienia).
- Wyrocznia skalowana w oczekiwaniu — prosty w konkretnych ziarnach zarabia +13 % przy „+10 %” (rozrzut ścieżek).
- Funding pominięty; OI 34 % pokrycia (tylko szum w tej kalibracji).
- **Kogo nie ma w zbiorze:** pierwsze ~14 miesięcy (rozbieg okna 365 dni — test od 2022-04), monety
  wycofane w trakcie tygodnia (para pominięta), konfiguracje spoza budżetu 24 (np. sieci neuronowe).
- Odstępstwa od pre-rejestracji jawne: werdykt z poprawionym N_eff jako główny (zapis przed przebiegiem 2),
  24 procesy z 1 wątkiem (przebieg 1 przeciążał serwer), raport w osobnej funkcji po utracie wydruku.

## Walidacja (16a), statystyka (16b), przegląd (16c)

`data:validate-data` — przeliczenia wyżej; czerwona flaga „wynik idealnie potwierdza” nie dotyczy
(wynik obala użyteczność ML); **Caveats** (S = 20, sygnał liniowy, AU1 z innego ustawienia).
`data:statistical-analysis` — przedziały Wilsona, mediany IC i zwrotu obok odsetków, licznik 0.
`engineering:code-review` (samodzielnie): granice okien (etykiety treningu kończą się przed testem: tr1 = q0 − 14),
walidacja wewnętrzna z purgingiem, wybór na walidacji bez dostępu do testu, koszt względem fazy t−7,
tylko dni testu w werdykcie — poprawne; testy 10 (w tym przeciek cech i regresja N_eff). **Werdykt jednym
zdaniem: Approve** — pipeline nie przecieka (0/40) i mierzy siłę znaną z konstrukcji, a jedyny błąd
dotyczył kanonicznego N_eff, obsłużony jawnie obok wersji kanonicznej.

## Wniosek

**Prostym językiem:** model ML jest uczciwy, ale mało czuły — przy realnych, niedużych przewagach
najczęściej ich nie znajduje, bo gubi się w szukaniu. Proste reguły tygodniowe widzą tyle samo albo
więcej. Nie budujemy ML na rankingach monet na tych danych.

**Technicznie:** negatywne 0/40; moc ML 0 / 25 / 35 / 80 / 100 % przy +5 / 10 / 15 / 20 / 30 %/rok vs
ranking po nośniku 10 / 80 / 85 / 95 / 100 %; koszt przeszukiwania ~2/3 mocy w zakresie realistycznym.

## Rekomendacja

1. **ML przekrojowe na tych danych — nie startuje** (reguła). Gdyby wracać: najpierw NOWE dane (wniosek 11)
   i mniejszy budżet (1–3 konfiguracje z góry), bo przeszukiwanie jest tu głównym kosztem mocy.
2. **Decyzja użytkownika: naprawa kanonicznego N_eff** (`effective_sample_size`: ucięcie sumy przy pierwszej
   ujemnej autokorelacji albo mianownik ≤ 0 → N_eff = n) + runda audytu AU3: przeliczenie dawnych
   NIEROZSTRZYGNIĘTYCH z t_neff ≪ t (tylko one mogą się zmienić). Poprawka w dzienniku — jeśli dotyczy.
3. Prosty ranking po jednej, z góry wybranej cesze ma moc 80 % przy +10 %/rok (4,2 roku) — przyszłe hipotezy
   przekrojowe formułować jako jedną regułę, nie przeszukiwanie.

## Użyte skille

Rejestr `runs/skille/au2-kroki-1-2.jsonl` (`py tools/skill_audit.py raport --galaz au2-kroki-1-2`): **7 wczytań, 7 skilli.**

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | pre-rejestracja z regułą odczytu przed przebiegiem; odstępstwo zapisane przed przebiegiem 2 |
| `anthropic-skills:clas5-quant` | kalibracja tylko ze znanym sygnałem (permutacja + nośnik), purging/embargo (Z17/Z21), N_eff ≤ n |
| `anthropic-skills:quant-strategy-catalog` | rodzina ML przekrojowe: zbiór informacyjny A to wciąż OHLCV + funding/OI (wniosek 11 jako ograniczenie) |
| `engineering:debug` | odtworzenie i przyczyna zapadania t_neff (ujemny mianownik N_eff), test regresji |
| `data:validate-data` | przeliczenie mocy prostego z MDE kroku 0; przebiegi 1 = 2; kogo nie ma w zbiorze |
| `data:statistical-analysis` | przedziały Wilsona dla mocy przy S = 20/40 |
| `engineering:code-review` | przegląd granic okien i walidacji wewnętrznej — Approve |

Pominięte z tabeli zasady 19: **`engineering:testing-strategy` — nie wczytany, choć moment (testy nowego
modułu) runda obejmowała: przeoczenie procesu** (testy napisane według wzorca z kroku 0, gdzie skill był
wczytany); `dataviz` — bez wykresu (brak biblioteki wykresów w `requirements-lock.txt`; tabela mocy zamiast krzywej).
