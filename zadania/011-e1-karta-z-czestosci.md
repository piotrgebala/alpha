---
id: 011
tytul: E1 — karta pre-rejestracji kaskad likwidacji z rachunkiem mocy z realnej częstości zdarzeń (bez cen)
typ: badawcze
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: zgoda na wszystkie 008–014 („Wszystkie 008–014”); odczyty na historii startują tylko, jeśli mapa 007 uzna rodzinę za MIERZALNĄ"
utworzono: 2026-09-29
zalezy_od: [004]
nie_wczesniej_niz: 2026-09-30
budzet: "Opus"
---

# 011 — E1: karta z góry, odczyt po roku

## Po co

E1 to jedyna rodzina z mocnym mechanizmem („ktoś MUSI handlować”), którą blokowały tylko dane. Dane zbierają
LK0 (od 2026-09-25), LB0 (od 2026-09-27) i LH0. Kartę trzeba zapisać, ZANIM ktokolwiek zestawi likwidacje z cenami —
inaczej definicja „kaskady” dopasuje się do wyniku.

## Zakres

- Definicja kaskady (próg wolumenu, okno), kierunek, horyzont i reguła wyjścia — zapisane teraz.
- Rachunek mocy z liczby zdarzeń (same liczniki z plików dziennych, bez cen) i projekcja: kiedy `n` wystarczy.
- Data odczytu (najwcześniej ~2027-09) i jeden licznik E1 wspólny dla trzech giełd.
- Rola HL: stan pozycji przed kaskadą tylko jako opis, nie druga zmienna.

## Czego NIE robić

- Żadnych cen po likwidacjach, żadnej „próbki”. Liczniki zdarzeń tak, zwroty nie.

## Kryteria odbioru (dowody)

Karta w `runs/DRAFT_E1.md` z hashem commita (dowód, że powstała przed odczytem).

## Pytanie do użytkownika

Zgoda na zapisanie karty teraz (odczyt dopiero za rok)?

## Wynik

**2026-09-29:** decyzja dopiero po wyniku pomiaru wag z zadania 004 (koniec ≈ 2026-09-30 10:33 UTC); wtedy orkiestrator przedstawi rekomendację (kolejność z mapy 007: E1 → sonda HL). Status bez zmian.

**2026-10-05 (wykonawca, gałąź `zadanie-011-e1-karta-z-czestosci`):** karta zapisana, rachunek mierzalności zrobiony —
**NIEMIERZALNA, odczyt nie startuje**. Czeka na przegląd 16c i scalenie przez orkiestratora.
- Co zrobiono: karta `runs/DRAFT_E1.md` (definicja kaskady: okno 60 min, próg 0,5 % dziennego obrotu z `dziennik/koszyk.csv`,
  24 h przeciw zlikwidowanym, blokada 24 h, jednostka = dzień; kryterium z progiem uogólnionym; licznik E1 0/1;
  odczyt najwcześniej 2027-09-27 i tylko po kontroli mocy) + wykonywalna definicja `backtest/e1_kaskady.py` + testy —
  **commit `580092c`, wypchnięty PRZED zliczeniem** (dowód kryterium odbioru). Potem częstość z samych liczników
  (bez cen) i rachunek: `backtest/run_e1k_czestosc.py`, runda `runs/2026-10-05_e1k-karta-kaskad/`.
- Wynik: Bybit 7,1 dnia — 0 kaskad (≤ 189 dni/rok, 95 %); próbka Binance 9 w 5 dniach. Przy μ 0,75 %, C 0,5 %, σ 5 %
  potrzeba 1 537 / 3 140 dni z kaskadą (moc 50 / 80 %) = ≥ 4,2 / 8,6 roku nawet przy kaskadzie każdego dnia.
- Dowody: `raw_output.txt`, druga droga `raw_output_druga_droga.txt` (zgodna co do minuty), testy
  `tests/test_e1_kaskady.py`, `tests/test_run_e1k_czestosc.py`; wiersz INDEX, wniosek 116, `runs/odczyty_historii.csv` nr 62.
- Co zostało: decyzja użytkownika — zbierać i kontrola mocy z liczników 2026-12-27 (rekomendacja) albo zamknąć E1 teraz.
- **2026-10-05, scalenie (orkiestrator):** przegląd 16c „Approve z uwagami” (README rundy), druga droga n50 ≈ 1 537 / n80 ≈ 3 140 zgodna, konflikt STATUS.md rozwiązany (obie linie). Status → `zrobione`. Do decyzji użytkownika: zbierać i powtórzyć rachunek 2026-12-27 albo zamknąć E1.
- **2026-10-05, decyzja użytkownika: „Zamknąć E1 teraz”.** E1 zamknięte bez odczytu (licznik E1 0/1 zamknięty), kontrola mocy
  2026-12-27 odwołana; dopiski w `runs/INDEX.md` (wiersz E1K, wniosek 116) i `runs/DRAFT_E1.md`. Kolektory LK0/LB0
  działają dalej (zatrzymanie = osobna decyzja). Zadanie 018 zamknięte tą samą decyzją.
