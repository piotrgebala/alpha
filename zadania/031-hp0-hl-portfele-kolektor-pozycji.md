---
id: 031
tytul: HP0 — Hyperliquid, brama danych portfeli traderów i darmowy kolektor pozycji od dziś; wycena archiwum S3 bez zakupu, 0 odczytów
typ: zbieranie_danych
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-10-18: „dodaj Propozycja na tablicę wszystkie 3 opcje” — wpis 031–033 z propozycji w rozmowie (brama danych, kolektor pozycji od dziś, wycena S3 bez zakupu); start kolektora na stałe (krok 2) po potwierdzeniu użytkownika"
utworzono: 2026-10-18
zalezy_od: []
budzet: "Opus do projektu i odbioru, Sonnet do kodu kolektora; 1–2 sesje + pomiar wag ≥ 24 h"
---

# 031 — HP0: brama danych portfeli Hyperliquid i kolektor pozycji

> Zadanie z tablicy (`zadania/README.md`); gałąź wykonawcy `zadanie-031-hp0-pozycje-hl` od `master`.

## Po co

Użytkownik zapytał 2026-10-18, czy da się znaleźć zapisy traderów, sprawdzić ich pozycje i nauczyć na tym model.
Na Hyperliquid widać pozycję każdego portfela: wielkość, dźwignię, cenę wejścia i cenę likwidacji. Binance pokazuje
tylko zbiorczy stosunek longów do shortów. API Hyperliquid daje jednak tylko stan bieżący, więc historii pozycji nie
ma za darmo. Każdy dzień bez kolektora przesuwa o dzień pierwszy odczyt zadań 032 i 033. Według rachunku z rozmowy
model z 033 potrzebuje ok. 2 lat części testowej na koszyku top-20. Z oknem uczącym to ok. 3 lat danych.

## Zakres

**Krok 1 — brama danych (0 odczytów; orkiestrator może ruszyć sam):**

1. **Ranking** `https://stats-data.hyperliquid.xyz/Mainnet/leaderboard`. To nieoficjalny adres strony giełdy, więc
   najpierw trzeba potwierdzić, że działa. Do sprawdzenia: liczba wierszy, pola, okna wyniku. Pytanie bramki 16a:
   **kogo NIE ma w zbiorze**? Czy są konta z ujemnym wynikiem i małą wartością? Czy znikają konta wyzerowane? Które
   wiersze to skarbce (vaults), podkonta i animatorzy rynku (np. HLP)?
2. **Historia wyniku** `portfolio` (POST `https://api.hyperliquid.xyz/info`). Próba ≥ 30 adresów różnej wielkości,
   także ze stratą. Dla każdego okna: liczba punktów i odstęp w `accountValueHistory` i `pnlHistory`, data pierwszego
   punktu. Czy historia `allTime` jest dzienna, rzadsza czy przycięta? Od tego zależy, czy test 032 może ruszyć na
   historii, czy tylko na danych zbieranych od startu kolektora.
3. **Pozycje** `clearinghouseState`. Pola pozycji (`szi`, `entryPx`, `leverage`, `liquidationPx`, `positionValue`,
   `marginUsed`) i konta (`accountValue`). Wagę zapytania wziąć z dokumentacji i potwierdzić pomiarem.
4. **Źródło adresów:** ranking oraz strony transakcji z kanału `trades` (`wss://api.hyperliquid.xyz/ws`).
   Do ustalenia: ile adresów zmieści migawka co godzinę przy budżecie z punktu 5.
5. **Budżet wag (zapisany z góry):** razem z kolektorem HS0 (`data/collect_hl_stan.py`) średnio ≤ 600 i p95
   ≤ 1 200 wagi/min na IP serwera. To ten sam próg co w LH0 (wniosek 115). Pomiar trwa ≥ 24 h. Druga droga: suma wag
   z dziennika zapytań.
6. **Archiwum S3, tylko wycena:** `s3://hl-mainnet-node-data/node_fills_by_block` oraz starsze `node_fills`
   i `node_trades`. Transfer opłaca pobierający. Z dokumentacji Hyperliquid i stron dostawców ustalić:
   - datę początku;
   - format;
   - czy wypełnienia mają adres portfela, czyli czy da się odtworzyć dawne pozycje;
   - rozmiar na dobę i koszt transferu.

   Zewnętrzny dostawca (Hydromancer) podaje pełne dane od 2025-07-28; trzeba to potwierdzić. Listowanie bucketa wymaga
   konta AWS, więc robi je użytkownik, jeśli zechce. Komendę wpisać do README rundy:
   `aws s3 ls s3://hl-mainnet-node-data/node_fills_by_block/ --request-payer requester`.
7. **Kod kolektora** `data/collect_hl_pozycje.py` z testami (zasada 10):
   - migawka pozycji co godzinę do `~/hl_pozycje/YYYY-MM-DD.jsonl.gz` (czas pobrania UTC, adres, moneta, pola pozycji
     i konta);
   - raz na dobę migawka rankingu i `portfolio` całej populacji;
   - plik-wyłącznik `~/hl_pozycje/WYLACZONY`, jak przy kolektorze Bybit;
   - przełącznik `--status`, jak w HS0.

**Krok 2 — start kolektora na serwerze (wymaga potwierdzenia użytkownika):** orkiestrator zadaje jedno pytanie
z wynikami kroku 1: wagi/min (średnio i p95), MB na dobę, liczba adresów. Po „tak”: cron jak w HS0 (blok
w `tools/likwidacje.sh`), nadzór z `~/alpha-dziennik`. Kopia zapasowa danych to osobna decyzja przy odbiorze
(prywatne repo jak przy likwidacjach albo R2).

Skille (zasada 19): `clas5-runda` (start rundy), `clas5-quant` (nowe źródło danych), `data:explore-data` (nowy zbiór),
`security-review` (nowe połączenie sieciowe), `engineering:code-review` (przed scaleniem). Gdy skill jest niedostępny:
w README „niedostępny w sesji” i procedura z repo.

## Czego NIE robić

- Nie łączyć pozycji ani wyników portfeli z przyszłym zwrotem ceny. To brama danych: 0 wariantów, 0 odczytów.
- Nie liczyć zależności między oknami wyniku z rankingu (np. miesiąc a cały okres). To byłby podgląd testu 032.
- Sieć tylko do `api.hyperliquid.xyz` (REST i WebSocket), `stats-data.hyperliquid.xyz`, dokumentacji
  `hyperliquid.gitbook.io` i stron dostawców danych z punktu 6.
- Bez kluczy, portfeli i zleceń. Bez MCP Liquid. Bez dostępu do `~/.ssh`.
- Nic nie kupować i nic nie pobierać z S3. Płatne źródła tylko z decyzją użytkownika.
- Nie przekraczać budżetu wag z punktu 5. Kolektor HS0 ma pierwszeństwo.

## Kryteria odbioru (dowody)

- Katalog `runs/2026-10-XX_hp0-pozycje-hl/` (zasada 11): README z 0 wariantów, „kogo NIE ma w zbiorze”, werdyktem
  bramki 16a i sekcją „Użyte skille”; `raw_output.txt` z pełnym wyjściem sondy; wiersz w `runs/INDEX.md` i wniosek.
- Liczby z nazwą źródła:
  - liczba wierszy rankingu i udział kont z ujemnym wynikiem `allTime`;
  - gęstość i początek historii `portfolio` (mediana i zakres);
  - wagi/min z pomiaru ≥ 24 h i z drugiej drogi;
  - liczba adresów w migawce i MB na dobę.
- Kontrola pozytywna: dla 5 adresów migawka kolektora zgadza się z bezpośrednim `clearinghouseState` z tej samej minuty.
- Testy jednostkowe parsera i zapisu oraz test właściwości (`hypothesis`) schematu migawki. `py -m pytest -q` zielone;
  ruff i black na dotykanych plikach.
- Wycena S3 w tabeli (początek, format, adres w wypełnieniu, GB na dobę, koszt) ze źródłami albo „BRAK DANYCH”.

## Wynik

(dopisuje orkiestrator)
