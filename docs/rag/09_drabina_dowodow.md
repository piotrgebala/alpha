---
status: active
last_verified: 2026-09-24
depends_on: [01_hipoteza_i_architektura.md, 03_ryzyko_i_sizing.md, 08_zasady_pelne_brzmienie.md]
---

# ADR-09: Drabina dowodów zamiast „dowodu na naszej historii”

**Status:** Accepted
**Data:** 2026-09-24
**Decyzja:** użytkownik (decyzja bramkowa, droga „B + C”); zapis: Claude

## Kontekst

Faza 0 miała cel: „udowodnić przewagę statystyczną minimalnym, audytowalnym systemem”. Kryterium
dowodu to t > 1,96 zwrotu netto na historii 2021–2026 (zasada 20), plus pre-rejestracja
i korekta na liczbę testów.

Po ~33 odczytach i korekcie danych (RU1/RU2) stan jest taki:

- Kierunek z modeli na świecach BTC: dowód braku (Faza 0, M1, F1, Y1/Y2).
- Zostały strategie tygodniowe na koszykach: trend (TS1/TR1), momentum między monetami
  (X1/X2) i premia Coinbase (CP1). Każda jest punktowo dodatnia, ale żadna nie przekracza progu.
- **Kryterium jest dla nich strukturalnie nieosiągalne.** Przy zmienności strategii ~18–35 %/rok
  i 5,5 roku danych połowa przedziału 95 % wynosi ±16–30 %/rok. Wykrywalne są więc tylko efekty
  ≥ 20–25 %/rok (wniosek 81), a tak silnych przewag nie mają nawet strategie, które naprawdę działają.
- Dłuższej historii krypto nie ma: sprzed 2022 to według użytkownika inny rynek, a 2019–2020
  zostało odrzucone. Obserwacja na żywo rozstrzygnęłaby sprawę dopiero po ~5 latach.

Utrzymanie kryterium oznaczałoby w praktyce zamknięcie projektu bez możliwości odróżnienia
„nie działa” od „nie da się zmierzyć”.

## Decyzja

Decyzję o kapitale podejmujemy według **drabiny dowodów**. Strategia wchodzi na kolejny szczebel
dopiero po spełnieniu poprzedniego. **Obalenie na dowolnym szczeblu wyłącza strategię.**

| szczebel | warunek | kto decyduje |
|---|---|---|
| **1. Mechanizm poza naszymi danymi** | Mechanizm ekonomiczny jednym zdaniem. Do tego oba poniższe: (a) oparcie w badaniach z innych rynków lub okresów; (b) nasz własny test tej samej reguły, bez strojenia, na danych niezależnych od krypto (np. trend na surowcach, walutach i indeksach w okresie PO publikacji badań). Test jest zwykłą rundą: pre-rejestracja, zasada 18, licznik. | Claude (runda) |
| **2. Spójność w niezależnych wycinkach naszych danych** | Wycinki ustalone z góry: pełne lata kalendarzowe 2021–2025, 7 faz tygodniowych oraz, dla koszyków, pasma monet top-20 i 21–50. Warunek: ≥ 80 % wycinków dodatnich i żaden z t < −1,96. **Uwaga:** dla strategii już oglądanych to sprawdzenie jest częściowo post hoc, więc sam szczebel 2 nie niesie decyzji. | Claude (odczyt) |
| **3. Dziennik papierowy** | ≥ 3 miesiące: kryteria mechaniki z `dziennik/README.md` spełnione, a wynik nie gorszy niż próg obalenia (średnia poniżej zakładanej minus 2 × błąd standardowy dla tej długości). | Claude (odczyt) |
| **4. Mała realna kwota** | Najwyżej 5 % kapitału jako depozyt, dźwignie jak w dzienniku (trend 2×, BTC 3×), STOP portfela 27,6 % spadku. | **użytkownik** |
| **5. Skalowanie** | ≥ 12 miesięcy realnie bez obalenia; zwiększanie najwyżej ×2 na krok. | **użytkownik** |

Bez zmian zostaje dyscyplina zasad 1–20: pre-rejestracja, liczniki wariantów, zasada 18 dla
każdego eksperymentu, zamrożone skrypty, bramki jakości. Zmienia się **tylko kryterium decyzji
o kapitale**. Nie zmienia się sposób mierzenia.

## Stan kandydatów w dniu decyzji

| strategia | szczebel 1 | szczebel 2 (post hoc) | dalej |
|---|---|---|---|
| Trend tygodniowy (TS1/TR1) | (a) mocne: trend na wielu rynkach od dekad (Moskowitz–Ooi–Pedersen 2012, Hurst–Ooi–Pedersen 2017); (b) **TX1 w toku** | lata 2021–2025: 5/5 dodatnich; fazy 7/7; pasma 2/2 → spełniony | jeśli TX1 nie obali → szczebel 3 (dziennik trwa) |
| Premia Coinbase (CP1) | (a) słabe: praktyka rynkowa, brak badań; (b) brak niezależnego testu (CP2: inne monety to ten sam sygnał) | lata 3/5 (2021 −11,6 %, 2024 −8,9 %) → **niespełniony** | zostaje w dzienniku papierowym, **bez realnego kapitału** do czasu nowego dowodu |
| Momentum między monetami (X1/X2) | (a) umiarkowane (badania nad momentum w krypto, mieszane); (b) brak | X1: lata 5/5, ale X2 2022 −10 % i wrażliwość na dzień rebalansu (wniosek 68) | poza dziennikiem; kandydat na później |

## Rozważane opcje

### A: bez zmian — dowód na historii

- **Plusy:** najwyższa ochrona przed przypadkiem.
- **Minusy:** strategie tygodniowe są niemierzalne, rozstrzygnięcie po latach, projekt stoi.

### B: drabina dowodów (wybrana, z C)

- **Plusy:** decyzja w miesiącach. Każdy szczebel ogranicza stawkę. Dowody spoza naszej historii
  (szczebel 1) i z przyszłości (szczebel 3) są niezależne od ~33 odczytów.
- **Minusy:** możliwa gra strategią, która okaże się szczęściem. Ogranicza to mała kwota
  i twardy STOP.

### C: nowe dane zamiast nowych teorii (wybrana jako część B)

- **Plusy:** dużo niezależnych obserwacji dla tego samego mechanizmu.
- **Minusy:** inne rynki to nie krypto 1:1. Dowodzą mechanizmu, nie wyniku na perpetualach.

## Konsekwencje

- **Łatwiej:** przejść od badań do małej, kontrolowanej ekspozycji. Kryteria są zapisane z góry,
  więc „przesuwanie bramki” po wyniku jest widoczne.
- **Trudniej:** trzeba prowadzić dziennik i odczyty terminowo. Decyzje na szczeblach 4–5 zawsze
  należą do użytkownika.
- **Do rewizji:** progi szczebla 2 (80 %), limit 5 % i próg obalenia w szczeblu 3, po pierwszym
  odczycie dziennika (~2026-12-25).

## Działania

1. [x] Zapis ADR, cel projektu w `CLAUDE.md`, synteza w `STATUS.md`, `README.md`, `runs/INDEX.md`.
2. [ ] TX1 — trend TS1 (parametry zamrożone) na innych rynkach, okres po publikacji; pre-rejestracja
   z rachunkiem mocy.
3. [ ] Odczyt dziennika ~2026-12-25 (szczebel 3), potem decyzja użytkownika o szczeblu 4.
