# AU2 kroki 1–2 — moc przyrządu przekrojowego z ML: ramię negatywne i siatka sił (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (zapisana przed przebiegiem; próba techniczna jednego przebiegu z ziarnem
> spoza planu — tylko czas i brak błędów, wyników nie oglądano). Kalibracja przyrządu — POZA
> licznikami hipotez, 0 wariantów. Prawdziwy związek cech ze zwrotami NIE jest mierzony (cel permutowany).

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

_(sekcje poniżej po przebiegu)_
