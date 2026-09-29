---
id: 008
tytul: B3 — momentum resztowe (po odjęciu rynku) na top-50, karta i rachunek mocy
typ: badawcze
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: [007]
budzet: "Opus"
---

# 008 — B3: momentum resztowe

## Po co

Rodzina NIETKNIĘTA. Formalnie wariant zamkniętej B1 (X1, X2), więc odczyt wymaga decyzji użytkownika.
Prior niski: zysk B1 mieszka w ogonach i nodze short (wniosek 68). AU2 daje gotowy przyrząd: top-50 widzi IC ≈ 0,022 (92).

## Zakres

- Karta hipotezy (`hypothesis_card.py --family B3 --formula cross`): JEDNA reguła zapisana z góry, średnia 7 faz startu (89),
  próg IC z kosztu i turnoveru, własny licznik i STOP.
- Wejście tylko, jeśli mapa 007 daje MIERZALNA i efekt z badań po publikacji ≥ IC 0,025.

## Czego NIE robić

- Bez ML i przeszukiwania okien (wniosek 93). Bez odczytu przed decyzją użytkownika.

## Kryteria odbioru (dowody)

Procedura `clas5-runda`: katalog `runs/`, `raw_output.txt`, wiersz w `runs/odczyty_historii.csv`, DSR z licznikiem programu.

## Pytanie do użytkownika

Czy robimy ten odczyt, wiedząc, że podnosi próg dla wszystkich kolejnych (DSR)?

## Wynik

(dopisuje orkiestrator)
