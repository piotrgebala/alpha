---
id: 007
tytul: Mapa strategii nierozstrzygniętych i niesprawdzonych — filtr (a)–(f) i rachunek mocy bez danych
typ: dokumentacja
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „zaplanuj zadania na strategie nierozstrzygnięte i niesprawdzone”"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, 1 sesja; bez pobierania danych"
---

# 007 — Mapa hipotez: co jeszcze ma szansę być mierzalne

## Po co

Historia 2021–2026 jest wyczerpana jako sędzia (wniosek 96: po ~40 odczytach DSR najlepszego = 0,52; każdy nowy
odczyt podnosi próg, wniosek 107: t ≈ 3,84). Zanim użytkownik zdecyduje o zadaniach 008–013, potrzebna jest jedna
tabela: która rodzina w ogóle przechodzi filtr przed danymi, a która jest NIEMIERZALNA już na papierze.

## Zakres

- Rodziny ze statusem NIETKNIĘTE lub nierozstrzygniętym w `quant-strategy-catalog` (`references/families.md`)
  i w `runs/INDEX.md` („Stan wiedzy — skrót”): B3, B4, C1, D3, G1 (reguła 8h), Y2 (BTC 1d), PT1 (surowce, obligacje),
  E1 (likwidacje), oraz nowe z Hyperliquid (premia/funding HL vs Binance; mapa cen likwidacji).
- Dla każdej: pięć pól (zbiór informacyjny, formuła, target, horyzont, status), mechanizm jednym zdaniem,
  filtr (a)–(f) z rankingu priorytetów katalogu, efekt z badań PO publikacji (źródło), rachunek mocy
  `measurability_report` / half-width IC **z parametrów literatury i znanych rozmiarów prób, bez odczytu wyniku**,
  korelacja oczekiwana do obecnych nóg (≤ ~0,35, wniosek 101), liczba odczytów programu do DSR.
- Werdykt per rodzina: MIERZALNA / NIEMIERZALNA / BRAK DANYCH, i propozycja kolejności.

## Czego NIE robić

- Żadnego pobierania cen, żadnego backtestu, żadnego „szybkiego zerknięcia”. To nie jest odczyt.
- Nie wpisywać wiersza do `runs/odczyty_historii.csv` (0 odczytów).
- Nie zmieniać statusu zadań 008–013 — to robi użytkownik decyzją.

## Kryteria odbioru (dowody)

- Plik `docs/mapa_hipotez_2026-10.md` z tabelą i komendami `measurability_report(...)` do powtórzenia.
- Każda liczba mocy przeliczona drugą drogą (wzór Walda ręcznie albo symulacja) — bramka 16a.
- Wpis jednym zdaniem + link w `STATUS.md` (backlog).

## Wynik

- **Zrobione 2026-09-29.** `docs/mapa_hipotez_2026-10.md` + skrypt `docs/mapa_hipotez_2026-10_moc.py` i wydruk `.txt`;
  wiersz w `docs/INDEX.md`, zdanie w `STATUS.md`. Gałąź `zadanie-007-mapa-hipotez`, commit `439b9f3`, scalone do master.
- **Wynik:** 10 rodzin, żadna dziś mierzalna. NIEMIERZALNE: B3, B4, C1, D3, G1, Y2 (jako 41. odczyt historii próg t ≈ 3,84).
  BRAK DANYCH: PT1, E1, HL-premia/funding, HL-mapa likwidacji. Proponowana kolejność: E1 (011) → sonda HL (010) →
  PT1 (012) tylko na życzenie → zamknąć 008, 009, 013 bez odczytu.
- **Dowody:** pytest 1 914 passed, 3 skipped, kod 0; wydruk mocy odtworzony przez orkiestratora (md5 `a06740ba…` identyczne);
  `measurability_report(0.70, 0.625, 33)` → 0,7956 i `(0.509, 0.5716, 6022)` → 0,5842 przeliczone ponownie; skrypt bez sieci
  i danych; 0 wierszy w `runs/odczyty_historii.csv`.
- **Zostało:** BRAK ŹRÓDŁA efektu po publikacji dla większości rodzin (użyte założenia z `docs/rag/11`, oznaczone);
  korelacje nowych rodzin z nogami tylko z analogii. Decyzje o 008–013 — użytkownik.
