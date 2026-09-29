---
id: 014
tytul: Odczyt dziennika papierowego ~2026-12-25 — TS1 + CP1 (+ X1 osobno), szczebel 3 drabiny dowodów
typ: dziennik
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: zgoda na wszystkie 008–014 („Wszystkie 008–014”); odczyty na historii startują tylko, jeśli mapa 007 uzna rodzinę za MIERZALNĄ"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus"
nie_wczesniej_niz: 2026-12-25
---

# 014 — Odczyt dziennika

## Po co

Trzy ślady (trend tygodniowy TS1, premia Coinbase CP1, momentum X1) są nierozstrzygnięte i historia ich już nie
rozstrzygnie (wniosek 96). Jedyną drogą jest dziennik prospektywny od 2026-09-24 / 2026-09-25. Odczyt trzeba
zaplanować teraz, żeby kryteria nie powstały po obejrzeniu wyniku.

## Zakres

- Przed 2026-12-25: zapisać kryteria odczytu (mechanika rozliczeń vs zwrot; co znaczy „zgodne z historią”), zanim
  ktokolwiek policzy wynik. Jeśli kryteria są już w `dziennik/README.md` / `docs/rag/09` — tylko je wskazać.
- Po 2026-12-25: odczyt, bramki 16a–c, raport dla użytkownika. Decyzja o szczeblu 4 (≤ 5 % kapitału) należy do użytkownika.

## Czego NIE robić

- Nie zaglądać w wynik dziennika przed datą. Nie zmieniać kodu dziennika (Poprawka = decyzja użytkownika).

## Kryteria odbioru (dowody)

Commit z kryteriami datowany przed 2026-12-25; katalog rundy z `raw_output.txt`.

## Wynik

- **Część 1 (kryteria przed odczytem) zrobiona 2026-09-29 przez wskazanie.** Nic nowego nie pisano. Kryteria stoją
  w `dziennik/README.md`: sekcja „Odczyt po ~3 miesiącach (ok. 2026-12-25) — kryteria mechaniki” i podsekcja
  „Zmiana kryteriów odczytu”. Wszystkie commity są sprzed 2026-12-25:
  - kryteria mechaniki 1–4 (kompletność, spójność, terminowość, zgodność z SZ1): `c3cbaa7` (2026-09-24);
  - kryterium 4b (zmienność R1 w paśmie [13; 31] %/rok) i kryterium 5 (próg obalenia μ − z·SE osobno dla TS1, CP1,
    R1 i X1; 3 odczyty wiążące przy 92, 182 i 365 dniach wyniku R1): `a28a481` (2026-09-27, decyzja użytkownika
    z 2026-09-27), razem ze skryptem `backtest/odczyt_dziennika.py`;
  - kryterium 6 (carry COIN-M, (a)–(c), tylko opisowo): `18cf6cc` (2026-09-28); w skrypcie od zadania 019
    (merge `dee873d`, 2026-09-29).
- Jak to pokrywa zakres zadania. „Mechanika rozliczeń” to kryteria 1–4 i 4b. „Zwrot” to kryterium 5. „Zgodne
  z historią” znaczy: średnia nogi leży nad progiem obalenia μ − z·SE, a μ i σ pochodzą z historii
  (`backtest/odczyt_dziennika_stale.py`). Brak obalenia nie jest potwierdzeniem przewagi.
- Wyniku dziennika nie oglądano.
- **Zostało (część 2, nie wcześniej niż 2026-12-25):** odczyt 1 komendą z `dziennik/README.md:598`
  (`py -m backtest.odczyt_dziennika --as-of 2026-12-24`; wiąże tylko wydruk z datą planu), katalog rundy
  z `raw_output.txt`, bramki 16a–c, raport dla użytkownika. Decyzja o szczeblu 4 należy do użytkownika.
