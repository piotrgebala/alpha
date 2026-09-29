---
id: 018
tytul: Brama danych — rozkład pozycji Hyperliquid według wielkości z Liquid (kohorty, „blisko likwidacji”), 0 odczytów
typ: konto
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, główna sesja (nie w roju)"
---

# 018 — Brama danych: kohorty pozycji z Liquid

## Po co

MCP Liquid (sprawdzony 2026-09-29 dwoma wywołaniami tylko do odczytu: `help`, `analyze_market BTC`) nie ma historii.
Do backtestów nic nie wnosi. Jedna rzecz jest jednak nowa. `analyze_market` zwraca rozkład pozycji na Hyperliquid
według wielkości: 10 grup od < 1 tys. do > 2,5 mln USD. Dla każdej grupy podaje:

- `positionCount`, `totalPositionValue`, `totalPositionValueLong`;
- `bias` (sprawdzone: udział longów w wartości);
- `valueCloseToLiquidation`;
- poprzednią migawkę (`past*`) i `createdAt`.

Przykład BTC z 2026-09-29 08:50 UTC: 22 797 pozycji poniżej 1 tys. USD (bias 0,670), 155 pozycji powyżej 2,5 mln USD
(bias 0,459); blisko likwidacji ≈ 2,60 mln USD, w całości w grupach poniżej 1 mln USD.

Darmowe API Hyperliquid pozwala śledzić tylko ~700 dużych adresów. Pełne pokrycie przekracza limit 8,6× (wniosek 110).
Liquid pokazuje całą giełdę, więc może dać „stan tuż przed kaskadą” do przyszłej karty E1. Zanim cokolwiek zbierzemy,
trzeba przejść bramę danych.

Wpis na tablicę: użytkownik, 2026-09-29, „dopisz”. To zgoda na wpis, nie na wykonanie. Typ `konto`, bo tablica tak
klasyfikuje każdą pracę z Liquid (`zadania/README.md`).

## Zakres (brama danych, 0 odczytów)

1. **Definicje pól:** co znaczy `valueCloseToLiquidation` (jaka odległość od ceny likwidacji); co to `past*` i jak
   dawno ją zrobiono; jak często dane się odświeżają; czy są point-in-time, czyli nie są poprawiane wstecz. Źródła:
   dokumentacja Liquid. Pytanie do obsługi Liquid zadaje użytkownik.
2. **Dostęp poza MCP:** czy Liquid ma zwykłe API (REST lub WebSocket) albo eksport historii. Do ustalenia: klucz,
   koszt, limity i czy regulamin pozwala zapisywać dane. **Brak API = STOP.** Kolektor przez LLM odpada: jest drogi,
   zawodny i nie do audytu.
3. **Kontrola pozytywna:** w tym samym oknie porównać grupy ≥ 100 tys. USD z migawką z publicznego API Hyperliquid
   (`clearinghouseState` dużych adresów; narzędzia z zadania 004, jeśli gotowe). Sprawdzić zgodność liczby pozycji
   i wartości. Tak się dowiemy, czy Liquid mierzy to, co deklaruje.
4. **Pokrycie:** które rynki mają te dane (`get_positioning_pulse`, `analyze_markets_batch`); co najmniej BTC, ETH
   i SOL dla E1.
5. **Odświeżanie:** co najmniej dwie migawki BTC w odstępie ≥ 1 h, zapisane w całości do `raw_output.txt`.

## Czego NIE robić

- Nie łączyć danych z przyszłym zwrotem ceny. To brama danych, 0 odczytów, licznik E1 bez zmian.
- Z Liquid używać tylko narzędzi do odczytu: `help`, `analyze_market`, `analyze_markets_batch`,
  `get_positioning_pulse`, `search_markets`. Nie zmieniać trybu konta (paper lub live). Nie włączać handlu
  automatycznego. Żadnych zleceń.
- Nie zlecać wykonawcom z roju. Praca z Liquid zostaje w głównej sesji (`zadania/README.md`).
- Nie budować kolektora przez MCP ani LLM. Nic nie kupować bez decyzji użytkownika.

## Kryteria odbioru (dowody)

- Katalog rundy według `clas5-runda`. ID nadaje procedura; LQ1 jest zajęte. Do tego `raw_output.txt` z pełnymi JSON
  migawek, wynik kontroli pozytywnej i hash commita.
- Tabela „brama zaliczona / niezaliczona” dla każdego punktu 1–5, z powodem.
- Wiersz w `runs/INDEX.md` (0 wariantów) i wniosek jednym zdaniem: czy te dane nadają się do zbierania pod kartę E1.
- Jeśli brama jest zaliczona, kolektor to osobne zadanie typu `zbieranie_danych`: decyzja użytkownika plus
  `security-review` (nowe połączenie i klucz).
- Skille: `clas5-quant` (nowe źródło danych), `clas5-runda`, `data:explore-data`, `data:validate-data`.

## Wynik

(dopisuje orkiestrator)
