# P3 — sonda źródeł danych II: co da się podłączyć i ile ma historii (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pobraniem i profilem).** Sonda odczytowa jak P1/P2:
> **0 wariantów, POZA licznikami hipotez.** Warunek utrzymania zera: runda **nie liczy żadnej
> korelacji ze zwrotami, żadnego sygnału, trafności ani P&L** — wyłącznie własności danych
> (zakres, luki, duplikaty, rozkłady, masa punktowa). Decyzja użytkownika 2026-09-23:
> „sprawdź wszystkie warianty, myślę też o podpięciu dodatkowych danych".

## ID testu

**P3** — sonda wykonalności NOWYCH źródeł danych + podłączenie tych, które przechodzą bramę
danych (kolektor `data/fetch_external.py`, cache `data/raw/external/`). Motywacja: po
zamknięciu serii A/C/R/W/N jedynym otwartym kierunkiem z realnym priorem jest **inny zbiór
informacyjny** (wniosek 11), a lista P1 skreśliła pozycjonowanie na podstawie **REST API**
(30 dni). Ta sonda sprawdza **archiwa** (pliki, nie API) i źródła spoza Binance.

## Metadane

- Branch: `p3-zrodla-danych` (od `master` @ `0dbd4e3`).
- Sondy wstępne (bez zapisu do repo): dwa skrypty odczytowe w scratchpadzie
  (listing S3 archiwum, po jednym zapytaniu do każdego API publicznego) — wyniki
  w sekcji „Sonda wstępna".
- Komenda pobrania: `py -m data.fetch_external` (Windows: `PYTHONUTF8=1`; bez kluczy API;
  pełny stdout → `raw_output.txt`). Profil: `py -m data.profile_external` → `profil.txt`.
- Zakres pobrania: od `2019-01-01` (zapas na warmupy przed bazą z zasady 20) do dziś;
  pomiary (przyszłe rundy) i tak filtrują `2021-01-01 → 2026-07-01` przez `fetch_window`.

## Poprzedzające wyniki

- **P1** (`runs/2026-09-22_p1-sonda-zrodel-danych/`): pięć endpointów `futures/data/*`
  oddaje **30,8 dnia**; przy potrzebie ~4 481 transakcji (3,4 roku) → pozycjonowanie
  NIEMIERZALNE; jedyna droga = zbierać od dziś (kolektor `data/collect_positioning.py`,
  aktywny od 2026-09-23). **P1 sprawdzało REST API, nie archiwum plików** — ta sonda
  sprawdza archiwum.
- **P2** (`runs/2026-09-22_p2-sonda-carry-przekrojowy/`): uniwersum point-in-time 287 symboli
  z archiwum `data.binance.vision` (funding + 1d) — wzorzec listingu S3 i pobierania z
  archiwum, na którym buduje kolektor P3.
- **C1** (`runs/2026-09-23_c1-cash-and-carry/`): carry z hedgem POZYTYWNY jako przepływ;
  otwarte pytania produktu: depozyt/likwidacja krótkiej nogi, porównanie ze stopą wolną od
  ryzyka, alternatywne konstrukcje (COIN-M, kontrakty kwartalne) — wymagają danych, których
  repo nie ma (funding COIN-M, ceny kontraktów kwartalnych, T-bill).
- **R1** (`runs/2026-09-23_r1-premia-rebalansowa/`): momentum względne wewnątrz miesiąca
  (wniosek 57) — hipoteza odwrotna B1 potrzebuje funding per symbol (jest w cache P2).
- **Wniosek 11** (INDEX): wąskie gardło Fazy 0 było informacyjne; **zasada 18**: nowe źródło
  przechodzi rachunek mocy ZE SWOJĄ historią.

## Pre-rejestracja: brama danych (kryteria zapisane PRZED pobraniem)

Źródło „przechodzi" bramę, gdy spełnia wszystkie cztery:

- **G1 — historia:** pokrywa bazę z zasady 20 (`2021-01-01 → 2026-07-01`, 5,5 roku) w co
  najmniej **90 %** dni; źródło z krótszą historią dostaje status „częściowe" z podanym
  ułamkiem, a rachunek mocy przyszłej rundy liczy się z JEGO `n`, nie z bazy.
- **G2 — point-in-time:** wartość na dzień `t` była znana w dniu `t` (archiwum = pliki
  publikowane raz, bez rewizji) LUB źródło ma znane opóźnienie publikacji, które przyszła cecha
  uwzględni przesunięciem (`shift`) — zapisane w tabeli.
- **G3 — koszt:** publiczne, bez klucza, bez opłat. Źródła płatne (Glassnode, Coinglass,
  Kaiko) tylko do listy „na potem" — koszt uzasadnia się PO rachunku mocy, nie przed.
- **G4 — ziarno:** natywne ziarno ≤ potrzebnemu (4h dla cechy modelu jednoaktywowego, 1d dla
  formuł przekrojowych/dziennych; Z9: bez resamplingu z grubszego ziarna).

Dla każdego źródła, które przejdzie: **jakie rodziny katalogu odblokowuje** (pięć pól) i
**szkic mierzalności** przyszłej rundy — ale **żadnego pomiaru sygnału w tej rundzie**.

### Kandydaci (lista zamknięta przed pobraniem)

| # | źródło | co | mechanizm, który ma odblokować |
|---|---|---|---|
| 1 | archiwum Binance `futures/um/daily/metrics` | open interest, proporcje long/short (top traderzy: konta i pozycje; wszystkie konta), proporcja taker buy/sell — 5 min | pozycjonowanie: tłok po jednej stronie → likwidacje kaskadowe (ograniczenie strukturalne) |
| 2 | REST `dapi` (COIN-M) `fundingRate` | funding perpetuala rozliczanego w BTC | wariant produktu carry bez ryzyka likwidacji krótkiej nogi (zabezpieczenie w BTC) |
| 3 | archiwum Binance `futures/um/monthly/klines/BTCUSDT_<YYMMDD>` | świece 8h kontraktów kwartalnych (24 kontrakty) | basis trade: różnica ceny kontraktu i spotu znana NA WEJŚCIU (przepływ zamknięty w chwili wejścia) |
| 4 | Deribit `get_volatility_index_data` | DVOL (zmienność implikowana 30 dni) BTC/ETH, 1d | opcje/vol: premia za ryzyko zmienności (variance risk premium) jako cecha i jako target |
| 5 | CoinMetrics community | on-chain 1d: adresy aktywne, transakcje, MVRV, przepływy na/z giełd, podaż na giełdach, hashrate, opłaty | on-chain: ruch monet na giełdy = podaż do sprzedaży (opóźniona reakcja) |
| 6 | alternative.me | Fear & Greed 1d | sentyment złożony (zdarzenia/kalendarz; kontrariańsko) |
| 7 | FRED | DTB3, DGS3MO, SOFR, DTWEXBGS (dolar), SP500 — 1d | stopa wolna od ryzyka do porównania carry; makro jako cecha |
| 8 | Coinbase Exchange | BTC-USD 1d | premia Coinbase (popyt z USA vs Binance) |
| 9 | archiwum `liquidationSnapshot` | likwidacje | (sprawdzić dostępność) |
| 10 | OKX / Bybit funding | funding innych giełd | rozproszenie fundingu między giełdami |

## Czego ta runda NIE liczy (warunek zera wariantów)

Żadnej korelacji z przyszłym zwrotem, żadnej trafności, żadnego P&L, żadnego rankingu
symboli po zwrocie. Profil danych = zakres, luki, duplikaty, kwantyle, masa punktowa,
autokorelacja SAMEJ zmiennej (nie ze zwrotem).

---

_(sekcje poniżej po pobraniu i profilu)_

## Sonda wstępna

_(po przebiegu)_

## Wynik: co przeszło bramę danych

_(po przebiegu)_

## Co na plus (+) / Co na minus (−)

_(po przebiegu)_

## Walidacja (zasada 16a)

_(po przebiegu)_

## Przegląd diffu (zasada 16c)

_(po przebiegu)_

## Wniosek

_(po przebiegu)_

## Rekomendacja

_(po przebiegu)_

## Użyte skille

_(po przebiegu — z `py tools/skill_audit.py raport --galaz p3-zrodla-danych`)_
