# AU2 kroki 1–2 — SZKIC karty (NIE pre-rejestracja; czeka na 3 decyzje użytkownika)

Źródło: projekt użytkownika z 2026-09-25 (rozmowa na claude.ai) + wynik kroku 0 (`README.md`).
Kalibracja przyrządu — poza licznikami hipotez; wariant ML, jeśli kiedyś powstanie, dostaje WŁASNĄ
pre-rejestrację i licznik.

## Cel
Zmierzyć krzywą mocy przyrządu „ranking przekrojowy + model ML + budżet przeszukiwania” na PRAWDZIWYCH
danych top-50: (1) ile fałszywych alarmów daje przy braku sygnału, (2) jaki odsetek zaszytych
sygnałów o znanej sile wykrywa. Porównać z przyrządem prostym (AU1 / krok 0: MDE IC 0,022).

## Decyzje użytkownika PRZED startem (bez nich karta nie jest zamrożona)
1. **Zbiór cech (lista zamrożona na piśmie).** Propozycja A (tania, zgodna z wnioskiem 11 jako
   ostrzeżeniem): ~10 cech z danych już w repo — zwroty 7/28/90 dni, zmienność 30 dni, obrót, zmiana
   obrotu, funding 7 dni, zmiana OI 7 dni, beta do BTC 90 dni, odległość od maksimum 90 dni.
   Propozycja B: A + nowe dane (np. on-chain per moneta) — dłużej, droższe dane.
2. **Budżet przeszukiwania** — tyle konfiguracji, ile zamierzasz naprawdę próbować w projekcie ML.
   Propozycja: 8 zestawów cech × 3 konfiguracje modelu (XGBoost ranking / regresja rang / liniowy)
   = 24; wybór najlepszej na walidacji wewnątrz walk-forward — ten sam w ramieniu negatywnym i pozytywnym.
3. **Drugi warunek werdyktu dla koszyka** (pierwszy: t_neff > 1,96 zwrotu netto long/short).
   Propozycja: `ci_low(średni rank IC) > 0` (se jak w kroku 0 — z rozrzutu, nie dwumianu).

## Konstrukcja (po decyzjach)
- Walk-forward: trening 365 dni, retrening co kwartał, purging 7 dni + embargo 7 dni na granicy
  train/test (precedens Z17/Z21), cel = ranga zwrotu 7-dniowego w przekroju, 7 faz.
- **Krok 1 — ramię negatywne:** cel permutowany między monetami w obrębie każdej daty (zachowuje
  przekrój, daty, korelacje; niszczy cecha → zwrot); S = 20 powtórzeń × pełny budżet. Oczekiwane
  ≈ 5 % werdyktów POZYTYWNYCH (górna granica 95 % z S = 20: ~20 %). Istotnie więcej → pipeline
  przecieka, **twardy STOP**.
- **Krok 2 — ramię pozytywne:** do zwrotu 7-dniowego dodany składnik z jednej z cech (+ realistyczny
  szum), skalowany tak, by wyrocznia zarabiała +5 / +10 / +15 / +20 / +30 %/rok netto; S = 20 na siłę.
  Moc = odsetek werdyktów POZYTYWNYCH; wykres z krzywą przyrządu prostego (`dataviz`).
- Rachunek czasu: 20 × (1 + 5) × 24 konfiguracje × ~21 kwartałów ≈ 60 tys. treningów — na serwerze
  (32 rdzenie) rząd kilku–kilkunastu godzin; przy budżecie 1 konfiguracja — minuty.

## Odczyt (reguła zapisana przed startem; decyzja bramkowa użytkownika)
- ramię negatywne ponad nominał → pipeline zepsuty, koniec;
- moc przy realistycznych siłach niższa niż przyrządu prostego → ML gorszym przyrządem, projekt ML nie startuje;
- krzywa widzi efekty o sile a priori prawdopodobnej → wariant ML dostaje własną pre-rejestrację i licznik.
Bez progu „moc ≥ X % = GO” (lekcja K1/K2).
