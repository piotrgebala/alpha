---
id: 001
tytul: LH0 — brama danych Hyperliquid (likwidacje), tylko zbieranie
typ: zbieranie_danych
status: w_toku
zlecil: cowork
decyzja_uzytkownika: "2026-09-28: trzeci kolektor likwidacji obok LK0 i LB0, tylko zbieranie, bez odczytu"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Sonnet do kodu i sondy, Opus do przeglądu i README"
---

# 001 — LH0: brama danych Hyperliquid (likwidacje), tylko zbieranie

> Decyzja użytkownika z 2026-09-28: „trzeci kolektor likwidacji obok LK0 i LB0, tylko zbieranie, bez odczytu”.
> Zadanie z tablicy (`zadania/README.md`); gałąź wykonawcy `zadanie-001-lh0-hyperliquid` od `master`.

## Po co

Rodzina E1 (kaskady likwidacji) to jedyna rodzina z mocnym mechanizmem („ktoś MUSI handlować”), którą blokują
wyłącznie dane. Mamy już dwa kolektory:

- LK0 (Binance) daje tylko próbkę, najwyżej jedną likwidację na sekundę na symbol.
- LB0 (Bybit) daje pełne dane.

Hyperliquid jest giełdą on-chain: każda pozycja i każda transakcja są publiczne. Otwarte pozycje na BTC to ok. 3,1 mld USD
(migawka 2026-09-28). Trzecia giełda z pełnymi danymi wzmacnia przyszłą kartę E1. Hyperliquid daje też coś, czego
Binance i Bybit nie mają: stan pozycji PRZED kaskadą (cena likwidacji każdej pozycji).

## Najważniejsze zastrzeżenie: brak publicznego strumienia likwidacji

Według dokumentacji Hyperliquid (WebSocket → Subscriptions) wygląda to tak:

- publiczny temat `trades` ma pole `users: [kupujący, sprzedający]`, ale **nie ma flagi likwidacji**;
- **nie ma publicznego strumienia likwidacji**;
- likwidacje widać tylko w strumieniach konkretnego użytkownika: `userEvents` (typ `liquidation`, `WsLiquidation`),
  `userFills` (pole `liquidation` w `WsFill`) i `userNonFundingLedgerUpdates`;
- `activeAssetCtx` / `metaAndAssetCtxs` dają funding, otwarte pozycje, cenę mark i oracle.

Dlatego **krok 0 rozstrzyga, czy zadanie ma sens**. Nie zakładaj żadnego adresu likwidatora ani mechanizmu z pamięci.
Sprawdź je w dokumentacji i na żywo.

## Zasady

- **0 wariantów, poza licznikami.** To zbieranie danych, a nie pomiar. Żadnego odczytu hipotezy E1 ani innej.
  Nie zestawiaj likwidacji z cenami. Jeden licznik E1 wspólny z LK0 i LB0.
- Procedura `clas5-runda`: katalog `runs/2026-09-2X_lh0-kolektor-hyperliquid/`. W README oznacz, co zapisano
  przed kodem [pre], a co przy implementacji [implementacja], tak jak w LB0.
- **Wzór techniczny: LB0.**
  - `DayWriter` z `time_key`, plik JSONL per dzień UTC;
  - `status.json`, `kolektor.log`, `--status`, `--probe` (próba bez zapisu);
  - ping, strażnik ciszy (pong nie liczy się jako znak życia), rosnące odczekanie po błędzie;
  - odświeżanie listy monet (`meta`) raz na dobę.
- Dane **poza repo**, w `$HOME/likwidacje_hl/`. Nadzór w `tools/likwidacje.sh`: ta sama linia crona, własny
  `flock`, wyłącznik `WYLACZONY`, podwójny fork jak w LB0. Działanie LK0 i LB0 bez zmian, `tests/test_likwidacje_sh.py`
  musi przechodzić.
- **Tylko publiczne API bez klucza:** `https://api.hyperliquid.xyz/info` i `wss://api.hyperliquid.xyz/ws`, adresy
  stałe w kodzie. Żadnych kluczy, portfeli ani zleceń. Nie używaj MCP Liquid, bo to narzędzie z konta handlowego
  użytkownika.
- **Płatne źródła: NIE bez decyzji użytkownika.** Dotyczy 0xArchive (historia likwidacji od 2025-07-27 dla
  pierwszych symboli), PurrData, Bitquery i S3 `node_fills` z płatnością po stronie pobierającego. W README tylko wypisz,
  co oferują.
- Dziennik: bez zmian i bez Poprawki, bo dziennik tego kodu nie importuje.
- Bramki:
  - testy bez sieci, w tym właściwości w `hypothesis` tam, gdzie LB0 je ma;
  - `security-review` (nowe połączenie sieciowe);
  - `engineering:code-review`;
  - `black`;
  - rejestr skilli gałęzi.

## Kroki

**0. Sonda wykonalności (najpierw, 1–2 h pracy, bez kolektora).**

a) **Czy likwidacje da się wykryć z danych publicznych w pełni, a nie jako próbkę?** Sprawdź w dokumentacji i na żywo:

- (i) czy likwidacje całej giełdy przechodzą przez znany, udokumentowany adres (np. skarbiec likwidatora lub HLP).
  Jeśli tak, `userEvents`/`userFills` tego adresu dają pełny strumień;
- (ii) czy da się je rozpoznać w publicznym `trades` po adresach stron;
- (iii) inne udokumentowane drogi.

**Kontrola pozytywna** (jak w LB0 i wniosku 102): 30–60 min na żywo w tym samym oknie co LK0 i LB0. Liczba zdarzeń na
głównych monetach i przewaga strony zlikwidowanej mają się zgadzać co do rzędu wielkości. Bez zaliczonej kontroli nie
ma kolektora.

b) **Czy da się zbierać stan pozycji przed kaskadą?** Chodzi o `clearinghouseState` per adres (cena likwidacji)
i zbiór adresów z `trades.users`. Sprawdź limity Info API (wagi na minutę na IP). Oszacuj, ile adresów i jak często
dałoby się odpytać, np. pozycje > 100 tys. USD. **Tylko oszacowanie, bez budowy.** Zbieranie tego wymaga osobnej
decyzji użytkownika.

c) **Budżet dysku:** MB na dobę dla (a) i dla zrzutów z kroku 2, wobec wolnego miejsca na serwerze i limitów GitHuba
dla kopii (`alpha-likwidacje`, pliki < 100 MB).

**Jeśli (a) wypadnie negatywnie:** STOP. Raport do użytkownika i decyzja, czy iść w (b), źródło płatne, czy zamknąć LH0.

**1. Kolektor likwidacji** (`data/collect_liquidations_hl.py`), tylko po pozytywnym (a).

- Wiersz = jedna likwidacja: `T` (ms), `coin`, `pos` (kierunek ZLIKWIDOWANEJ pozycji), wielkość, cena, surowe pola
  źródła, `ts` (czas źródła) i `rcv` (czas odbioru).
- Adres zlikwidowanego zapisuj tylko wtedy, gdy jest potrzebny do usuwania duplikatów. Uzasadnij to w README.

**2. (Zalecane, tanie) Stan rynku co 60 s:** `metaAndAssetCtxs` dla wszystkich monet (funding, otwarte pozycje, mark,
oracle, premium), zapis do `$HOME/likwidacje_hl/stan/YYYY-MM-DD.jsonl.gz`. Spadek otwartych pozycji to niezależny
sprawdzian likwidacji z kroku 1. Na przyszłość to też historia fundingu Hyperliquid, której nie ma nigdzie za darmo
w tej rozdzielczości.

**3. Nadzór i kopia.**

- Wpięcie w `tools/likwidacje.sh`.
- Katalog w `data/liquidation_backup.py` i `data/liquidation_index.py`, jeśli budżet z kroku 0c na to pozwala.
  Dzienny indeks per giełda × symbol, jak dla LK0 i LB0.

**4. Dokumentacja.**

- README rundy z wynikiem próby: liczba zdarzeń, błędy, porównanie z LK0/LB0, MB na dobę.
- Wniosek w `runs/INDEX.md` (kolejny numer po 108) i wpis w `STATUS.md`.
- Katalog `quant-strategy-catalog` (E1): trzecie źródło, status ZBIERANE-dane. Aktualizacja przy następnej wersji
  skilla.

## Czego NIE robić

- Żadnego odczytu E1: bez cen po likwidacjach i bez „sprawdźmy tylko na próbce”.
- Nie budować śledzenia pozycji z kroku 0b bez decyzji użytkownika.
- Nie zmieniać LK0 ani LB0 poza wspólnym nadzorem i kopią.
- Nie kupować danych i nie zakładać kont (AWS, 0xArchive itp.).

## Raport końcowy do użytkownika (prostym językiem, 5–8 zdań)

Raport ma powiedzieć:

- czy Hyperliquid pokazuje likwidacje w pełni;
- ile ich jest na minutę wobec Binance i Bybit;
- ile miejsca zajmuje doba danych;
- czy działa kopia;
- co wymaga decyzji użytkownika (śledzenie pozycji przed kaskadą, ewentualne źródło płatne).
