# LH0 — brama danych Hyperliquid (likwidacje): krok 0, sonda wykonalności (2026-09-29)

> **STATUS: KROK 0 ZAKOŃCZONY — werdykt 0a: TYLKO PRÓBKA (darmowe API na żywo). STOP przed kolektorem, czeka na
> decyzję użytkownika.** Kolektora (krok 1+) NIE zbudowano.
> **0 wariantów — POZA licznikami.** To sprawdzenie źródła danych, nie pomiar. Żadnego odczytu E1: nie zestawiamy
> likwidacji z cenami. Jeden licznik E1 wspólny z LK0 i LB0 (stan: 0 odczytów).

## W skrócie — prostym językiem (zasada 17)

Hyperliquid nie ma publicznego strumienia likwidacji. Sprawdziliśmy trzy drogi.

1. **Adres likwidatora (HLP, skarbiec giełdy).** Działa, ale widzi tylko ostatnią deskę ratunku (likwidację „backstop”,
   gdy rynek nie przyjął zlecenia). Takich jest kilkadziesiąt na miesiąc. Zwykłe likwidacje idą na rynek jako zlecenia
   samego zlikwidowanego konta. To tylko **próbka**.
2. **Publiczne transakcje + sprawdzanie adresów.** Każdą zwykłą likwidację da się rozpoznać: zlikwidowane konto jest
   stroną aktywną transakcji (tą, która „zabiera” zlecenie z arkusza), a jego wypełnienia mają pole `liquidation`.
   W 44 minutach na BTC/ETH/SOL znaleźliśmy tak **91 likwidacji** (78 BTC, 13 ETH, 0 SOL). Kierunek zgadza się
   z Binance i Bybit: wszystkie to zlikwidowane shorty. Kłopot to koszt. Samo BTC/ETH/SOL zużyło **ok. 1 240 jednostek
   limitu na minutę**, a limit na jeden adres IP to **1 200**. Cała giełda wymagałaby 2,6–8,6× więcej, niż wolno.
   Na żywo, za darmo, dla całej giełdy — **nie da się**. Dla kilku monet albo z opóźnieniem (np. raz na dobę) —
   może tak, ale tego nie zmierzyliśmy.
3. **Własny węzeł Hyperliquid** (oprogramowanie dostępne bez zgody giełdy, zapisuje wszystkie wypełnienia) albo płatne
   archiwum S3. To pełne źródło, ale wymaga decyzji użytkownika (nowa infrastruktura albo opłata).

Co to znaczy dla decyzji: trzeciego pełnego źródła likwidacji za darmo i od ręki nie ma. Zadanie mówi w tym miejscu
STOP; wybór drogi (tryb ograniczony, węzeł, płatne S3 albo zamknięcie LH0) należy do użytkownika.

## Metadane

- **ID:** LH0 (zadanie 001 z `zadania/001-lh0-kolektor-hyperliquid.md`). Gałąź `zadanie-001-lh0-hyperliquid`
  od `master` `2e2bf05`. Decyzja użytkownika 2026-09-28: „trzeci kolektor likwidacji obok LK0 i LB0, tylko zbieranie,
  bez odczytu”.
- **Sieć:** wyłącznie `https://api.hyperliquid.xyz/info`, `wss://api.hyperliquid.xyz/ws` i dokumentacja
  `hyperliquid.gitbook.io` (strony pobrane 2026-09-29 ~06:10 UTC w wersji `.md`). Bez kluczy, portfeli, zleceń, bez
  MCP Liquid, bez płatnych źródeł.
- **Skrypty sondy (w tym katalogu, jednorazowe):** `sonda_hlp.py` (0a-i), `sonda_trades.py` (nasłuch 0a-ii),
  `sonda_weryfikacja.py` (0a-ii, prawda z `userFillsByTime`), `sonda_podsumowanie.py` (liczniki + druga droga),
  `sonda_skala.py` (skala całej giełdy, bez sieci), `sonda_budzet.py` (0b, 0c), `porownanie_lk0_lb0.py`
  (kontrola pozytywna: liczniki LK0 i LB0 w tym samym oknie, tylko odczyt `~/likwidacje`, `~/likwidacje_bybit`).
  Pełny stdout: `raw_output.txt`. Surowy zapis transakcji z nasłuchu leży POZA repo (katalog tymczasowy sesji) —
  w repo tylko liczniki.

## Poprzedzające wyniki

LK0 (Binance, próbka ≤ 1/s/symbol, wniosek 102), LB0 (Bybit, pełne, kontrola pozytywna 58 zdarzeń / 180 s, wniosek 106;
strona `S` o odwrotnym znaczeniu na obu giełdach), P3 (archiwum Binance bez likwidacji). Wnioski 102 i 106 mówią, że
źródło przyjmujemy dopiero po kontroli pozytywnej na żywo w tym samym oknie co inne źródła; z tego wynika projekt kroku 0
niżej (najpierw mechanizm z dokumentacji, potem liczniki na żywo, potem porównanie z LK0/LB0).

## Pre-rejestracja (0 wariantów)

- **[pre] Pytanie 0a:** czy likwidacje CAŁEJ giełdy Hyperliquid da się wykryć w pełni z publicznego, darmowego API?
  Trzy drogi z zadania: (i) znany adres likwidatora/HLP i jego `userFills`/`userEvents`; (ii) rozpoznanie w publicznym
  `trades` po adresach stron; (iii) inne udokumentowane.
- **[pre] Werdykt 0a (trzy możliwe):** **TAK pełne** — droga, która widzi każdą likwidację na wszystkich monetach
  w limitach darmowego API (udokumentowana albo sprawdzona na żywo wobec niezależnej prawdy); **TYLKO próbka** — widać
  tylko część (np. jeden typ likwidacji, część monet albo część adresów); **NIE** — brak drogi.
- **[pre] Kontrola pozytywna (jeśli jest droga):** 30–60 min na żywo; liczba likwidacji na BTC/ETH/SOL i przewaga strony
  zlikwidowanej wobec LK0 i LB0 w tym samym oknie UTC. „Zgodne co do rzędu wielkości” = liczby w obrębie ×10 i, gdy
  każde źródło ma ≥ 10 zdarzeń, ta sama strona przeważająca. Giełdy mają różne rynki, więc równych liczb nie oczekujemy.
- **[pre] 0b:** tylko oszacowanie (wagi Info API na IP, liczba adresów z pozycjami > 100 tys. USD, częstość odpytań
  `clearinghouseState`). Bez budowy.
- **[pre] 0c:** MB/dobę dla (a) i dla `metaAndAssetCtxs` co 60 s; wolne miejsce `df -h $HOME`; limit plików < 100 MB
  w kopii.
- **[pre] Czego NIE robimy:** żadnych cen po likwidacjach, żadnego odczytu E1, żadnego śledzenia pozycji (0b to
  rachunek), żadnych płatnych źródeł.
- **[implementacja] Prawda do kontroli (ii):** dla BTC/ETH/SOL odpytujemy `userFillsByTime` WSZYSTKICH stron aktywnych
  z okna; likwidacja = wypełnienie z polem `liquidation`, w którym zlikwidowanym jest ten adres. Jednostka porównania
  HL = zlecenie likwidacyjne (`user`, `oid`). Dopisane po przeczytaniu dokumentacji, przed uruchomieniem odpytań.
- **[implementacja] Próby dymne (nie są dowodem, nie w `raw_output.txt`):** 30 s nasłuchu `trades` (06:13, 178 monet,
  0 błędów) i odpytanie 150 stron aktywnych z tych 30 s (0 likwidacji; `crossed` zgodne 1 186 / 1 186).

## Wynik 0a — mechanizm z dokumentacji (cytaty; strony pobrane 2026-09-29)

- `trading/liquidations`: „the positions are first attempted to be entirely closed by sending market orders to the
  book”; „If the account equity drops below 2/3 of the maintenance margin without successful liquidation through the
  book, a backstop liquidation happens through the liquidator vault”; „the majority of liquidations on Hyperliquid are
  sent directly to the order book”; „Backstop liquidations … through the liquidator vault, which is a component strategy
  of HLP”. Pozycje > 100 tys. USDC: na rynek idzie 20 % pozycji, potem 30 s przerwy.
- `hypercore/vaults/protocol-vaults`: HLP „performs liquidations”. Dokumentacja **nie podaje** adresu skarbca
  likwidatora. Adres HLP `0xdfc24b077bc1425ad1dea75bcb6f8158e10df303` pochodzi z przykładu odpowiedzi `vaultDetails`
  w `for-developers/api/info-endpoint` (opis „… performs liquidations …”); na żywo zwraca nazwę „Hyperliquidity
  Provider (HLP)” i 7 adresów podrzędnych.
- `for-developers/api/websocket/subscriptions`: `WsTrade` = `coin, side, px, sz, hash, time, tid, users: [buyer,
  seller]` — **bez flagi likwidacji**. `WsFill.liquidation?: FillLiquidation {liquidatedUser?, markPx, method: "market" |
  "backstop"}`. `WsLiquidation` w `userEvents` i `WsLedgerLiquidation` w `userNonFundingLedgerUpdates` — strumienie per
  użytkownik.
- `for-developers/api/rate-limits-and-user-limits`: REST 1 200 wagi/min na IP; `clearinghouseState` waga 2; pozostałe
  `info` 20; `userFills`/`userFillsByTime` + waga za każde 20 zwróconych pozycji; WebSocket: maks. 10 połączeń,
  1 000 subskrypcji, **maks. 10 unikalnych użytkowników w subskrypcjach per użytkownik**.
- `historical-data`: S3 `hl-mainnet-node-data/node_fills_by_block` (wypełnienia z węzła, „`node_fills` matches the API
  format”, czyli z polem `liquidation`); „the requester of the data must pay for transfer costs” — **płatne, nie
  użyte**. `hyperliquid-archive` (asset_ctxs, l2Book, raz w miesiącu, „no guarantee”) — też płatny transfer.
- `for-developers/nodes/foundation-non-validating-node`: „running a non-validating node is permissionless”; lokalny
  węzeł „can record fills”. Wymagania sprzętowe są w repozytorium `hyperliquid-dex/node` — **poza dozwolonymi
  źródłami, nie sprawdzone (BRAK DANYCH)**. Dostęp do węzła Fundacji wymaga 10 000 HYPE w stakingu — nie dla nas.
- Płatni dostawcy (0xArchive, PurrData, Bitquery): dokumentacja Hyperliquid ich nie wymienia; nie sprawdzaliśmy ich
  (zakaz). Jedyna znana nam informacja pochodzi z treści zadania: 0xArchive — historia likwidacji od 2025-07-27.

## Wynik 0a — na żywo (pełny zapis `raw_output.txt`)

**(i) Adresy HLP** (`sonda_hlp.py`, ~06:12 UTC, ostatnie ≤ 2 000 wypełnień każdego adresu):

| adres podrzędny HLP | okno ostatnich wypełnień | wypełnień z `liquidation` |
|---|---|---|
| `0x0104…703a`, `0x31ca…974b` | ostatnie ~17 min (animatorzy rynku) | 0 |
| `0x2e3d…dd14` | 2026-05-18 .. 2026-08-22 | 2 (`backstop`) |
| `0x2ed5…8308` | 2026-01-19 .. 2026-09-04 | 16 (`backstop`) |
| `0x5e17…cb70` | 2026-08-22 .. 2026-09-23 | 46 (`backstop`) |
| `0xb0a5…9540` | 2026-08-19 (jeden dzień) | 223 (`backstop`) |
| HLP główny, `0x469f…d7d8` | — / 6 wypełnień ze stycznia | 0 |

Backstop to rzadkie zdarzenia (dziesiątki na miesiąc, setki w jeden dzień kaskady), rozłożone na kilka adresów — który
jest „likwidatorem”, dokumentacja nie mówi. W 45-min nasłuchu `userFills` 7 adresów HLP pojawiły się 2 wypełnienia
`method: "market"` (ICP, 06:15:08) — HLP był wtedy **kontrahentem** likwidacji rynkowej. Pole `liquidation` dostaje
więc także kontrahent, ale HLP jest kontrahentem tylko części likwidacji. Droga (i) = **próbka**.

**(ii) `trades` + `userFillsByTime` stron aktywnych.** Nasłuch 06:13:51–06:58:51 UTC, 178 monet głównej giełdy,
185/185 subskrypcji, 0 błędów, 118 867 transakcji. Okno analizy: **06:14:00–06:58:00 UTC (44 min)**. Na BTC/ETH/SOL:
14 726 transakcji, 2 506 unikalnych stron aktywnych; odpytano wszystkie (54 698 wagi w 3 242 s). 8 adresów uciętych na
2 000 wypełnień — ich likwidacje mogły umknąć, więc liczby niżej to **dolna granica**.

- Strona aktywna = `users[0]` przy `side: "B"`, `users[1]` przy `"A"`: potwierdzone polem `crossed` w 10 680 / 10 680
  dopasowanych wypełnień.
- Likwidacja rynkowa w `trades` **nie ma żadnej cechy odróżniającej** (zwykły `hash`, zwykły `tid`); zlikwidowany jest
  stroną aktywną; jedno zlecenie (`oid`) = kilka transakcji z tym samym `hash`.

| moneta | HL: zleceń likwidacyjnych (wypełnień) | HL kierunek | LK0 Binance (próbka) | LB0 Bybit (pełne) |
|---|---|---|---|---|
| BTC | **78** (109) | 78 shortów / 0 longów | 29 (0 L / 29 S) | 10 (0 L / 10 S) |
| ETH | **13** (17) | 13 S / 0 L | 61 (0 L / 61 S) | 21 (0 L / 21 S) |
| SOL | **0** | — | 13 (1 L / 12 S) | 4 (0 L / 4 S) |
| razem 3 monety | 91 (2,07/min) | 91 S / 0 L | 103 | 35 |

To samo okno 44 min, czas zdarzenia `T` we wszystkich źródłach (LK0 z symbolami USDT i USDC). Jednostka: HL = zlecenie
likwidacyjne (`user`, `oid`); LK0/LB0 = wiersz zdarzenia. Każde z 91 zleceń HL to inny adres. Wszystkie 126 wypełnień
to metoda `market` (0 backstop). Nominał HL: BTC ~336 tys. USD (średnio ~4,3 tys. na likwidację), ETH ~13 tys. USD.

**Kontrola pozytywna wobec pre-rejestracji:** BTC i ETH — liczby w obrębie ×10 (BTC 78 vs 29 vs 10: 7,8× do Bybit;
ETH 13 vs 61 vs 21: 4,7× do Binance) i ta sama przeważająca strona (wszędzie 100 % zlikwidowanych shortów) →
**zaliczone**. SOL — HL 0 wobec 13 (LK0) i 4 (LB0): warunek „×10” formalnie **niespełniony**, ale przy tak małych
liczbach nie rozstrzyga (gdyby HL miał średnio 1–2 likwidacje SOL na okno, zero wypada w ~15–35 % okien).
Kontrola **zaliczona z zastrzeżeniem**: jedno okno, spokojny rynek, jeden kierunek.

**Druga droga liczby 91 / 126:** `sonda_podsumowanie.py` dopasowuje wypełnienia do publicznego `trades` (ta sama
moneta, strona aktywna = zlikwidowany, ten sam czas i `hash`): 109 + 17 = 126 transakcji, 1:1 z wypełnieniami. To
sprawdza spójność dwóch źródeł Hyperliquid, nie pełność. Niezależnym sprawdzianem kierunku są LK0 i LB0 (zgodne).

**Skala drogi (ii) dla całej giełdy** (`sonda_skala.py`, 44 min, wszystkie 178 monet): 2 517 transakcji/min;
6 275 unikalnych stron aktywnych w oknie; **476 unikalnych stron aktywnych na minutę** (mediana; zakres 366–823).
Każda wymaga zapytania o wadze ≥ 21 (zmierzona średnia 21,8 na adres). Odpytywanie na bieżąco: 476 × 21,8 ≈
**10 400 wagi/min wobec limitu 1 200 (~8,6×)**. Jedno zapytanie na adres na 44 min: 6 275 × 21,8 / 44 ≈ **3 100
wagi/min (~2,6×)**. Sprawdzenie drugą drogą (z sumy wag, nie ze średniej): samo BTC/ETH/SOL zużyło 54 698 / 44 min ≈
**1 243 wagi/min** — już ponad limit. Tryb „raz na dobę” (jedno zapytanie na adres dziennie) może się zmieścić, ale
liczby unikalnych stron na dobę i kosztu adresów z > 2 000 wypełnień **nie zmierzono (BRAK DANYCH)**.

**Werdykt 0a (Claude, wykonawca gałęzi): TYLKO PRÓBKA** z darmowego API na żywo.
- (i) HLP: pełne tylko dla backstopu (mniejszość likwidacji; adres likwidatora nieudokumentowany).
- (ii) Mechanizm pełny — każda likwidacja rynkowa jest rozpoznawalna — ale dla całej giełdy koszt to 2,6–8,6× limitu
  jednego IP. Wykonalne dla kilku monet albo z opóźnieniem — niezmierzone.
- (iii) Pełne źródła: własny węzeł (zapis wypełnień) albo S3 `node_fills_by_block` (płaci pobierający). Oba wymagają
  decyzji użytkownika.

## Wynik 0b — stan pozycji przed kaskadą (tylko oszacowanie, `sonda_budzet.py`)

- Próba 400 losowych adresów spośród 7 832 stron transakcji z nasłuchu (`clearinghouseState`, waga 2): 323 ma pozycje,
  **36 ma łącznie > 100 tys. USD** (9,0 %; przedział Wilsona 95 % ≈ 6,6–12,2 %) → **~700 adresów (≈ 520–960)** wśród
  tych, które handlowały w oknie. Adresy, które nie handlowały, umykają — prawdziwa liczba jest większa. (Zbiór 7 832
  obejmuje też starsze transakcje z migawki przy subskrypcji — „okno 177 min” w `raw_output.txt`.)
- Limit: 1 200 / 2 = **600 zapytań `clearinghouseState`/min na IP**, jeśli nic innego nie działa. ~700 adresów →
  pełny obieg co ~1,2 min na całym limicie, co ~2,5 min na połowie. Subskrypcja WebSocket per adres odpada (maks.
  10 użytkowników). Odpowiedź daje `liquidationPx` per pozycja (przykład w dokumentacji `clearinghouseState`).
- Konflikt: 0b i droga (ii) biorą z tego samego limitu IP. Zbieranie 0b = osobna decyzja użytkownika. Nie budowano.

## Wynik 0c — budżet dysku

| strumień | MB/dobę | uwagi |
|---|---|---|
| (a) likwidacje | **BRAK DANYCH dla całej giełdy**; BTC+ETH: 91 zleceń / 44 min ≈ 3 000/dobę → < 1 MB (szacunek ~250 B/wiersz) | nawet ×10 to kilka MB/dobę, plik dobowy ≪ 100 MB |
| surowy `trades` (gdyby zapisywać cały strumień) | ~990 (JSON bez spacji) | nie do kopii w repo; droga (ii) potrzebuje go tylko w pamięci (lista stron aktywnych) |
| krok 2: `metaAndAssetCtxs` co 60 s | 104 surowo, **~19,4 gzip** | zrzut ~72 kB; plik dobowy `.jsonl.gz` ~19 MB < 100 MB |

Wolne miejsce (`df -h $HOME`): 1,4 TB z 1,8 TB (18 % zajęte). Dla porównania LK0 ~7–11 MB/dobę, LB0 ~0,8–2,6 MB/dobę
(rozmiary plików w `~/likwidacje*`). Limit kopii (`alpha-likwidacje`, pliki < 100 MB) spełniają (a) i krok 2.

## Bramka 16a (walidacja write-upu) — ręcznie według `docs/skills/bramki-jakosci.md`

- **Przeliczenie drugą drogą:** 126 wypełnień = 126 transakcji w publicznym `trades` (spójność); koszt 1 243 wagi/min
  z sumy wag wobec szacunku ze średniej (zgodny rząd). Kierunek — niezależnie z LK0/LB0.
- **Kogo nie ma w zbiorze:** SOL (0 zdarzeń — brak czy zguba, nie wiadomo); 8 adresów uciętych na 2 000 wypełnień;
  backstop (w oknie nie było); monety HIP-3 (osobne giełdy z `perpDexs`: xyz, flx, vntl i in. — nie subskrybowane);
  okno 44 min w spokojnym rynku (wtorek rano UTC).
- **Czerwona flaga „idealnie potwierdza”:** 100 % shortów we wszystkich trzech źródłach to cecha okna (rynek szedł
  w górę), nie dowód pełności.
- **Werdykt: Caveats** — mechanizm potwierdzony; pełność dla całej giełdy niewykonalna w limicie darmowego API na żywo;
  jedno krótkie okno.

## Co na plus (+) / Co na minus (−)

**(+)**
- Rozpoznanie likwidacji rynkowej jest pełne i sprawdzone na żywo: zlikwidowany = strona aktywna, jego wypełnienie ma
  pole `liquidation` z metodą i ceną mark; kierunek zgodny z Binance i Bybit.
- Hyperliquid podaje adres zlikwidowanego — łatwe usuwanie duplikatów (tu: 91 zleceń = 91 adresów).
- Stan rynku (krok 2) jest tani: ~19 MB/dobę gzip.
- 0b mieści się w limicie: ~700 dużych adresów co 1–3 min.

**(−)**
- **Brak pełnego, darmowego strumienia na żywo dla całej giełdy** — koszt 2,6–8,6× limitu IP.
- Adres likwidatora (backstop) nieudokumentowany; backstop rozłożony na kilka adresów HLP.
- Jedno okno 44 min, trzy monety, spokojny rynek; SOL 0 zdarzeń; wynik to dolna granica (8 uciętych adresów).
- Wymagania sprzętowe węzła i koszt S3 nie sprawdzone (poza dozwolonymi źródłami).
- Sonda zajęła limit IP serwera na ~55 min (bez błędów 429 w zapisie).

## Wniosek

Hyperliquid pokazuje każdą likwidację rynkową w danych publicznych, ale nie jako strumień. Trzeba sprawdzać wypełnienia
każdego adresu, który zawarł transakcję jako strona aktywna. Dla całej giełdy na żywo to 2,6–8,6× więcej zapytań, niż
pozwala darmowy limit jednego IP. Darmowo na żywo mamy więc tylko próbkę (backstop przez HLP albo wybrane monety).
Kontrola pozytywna na BTC/ETH (91 likwidacji w 44 min, same shorty, jak na Binance i Bybit) potwierdza, że mechanizm
działa. Nic nie odczytano; licznik E1 bez zmian (0 odczytów).

Proponowana linia do „Wniosków skumulowanych” (wpisuje orkiestrator przy scaleniu):
`[2026-09-29, LH0 krok 0] Hyperliquid nie ma strumienia likwidacji; likwidacja rynkowa jest rozpoznawalna (strona
aktywna + pole liquidation w userFillsByTime; kontrola 44 min: 78 BTC + 13 ETH, 100 % shortów jak LK0/LB0), ale pełne
pokrycie giełdy kosztuje 2,6–8,6× limitu 1 200 wagi/min IP → darmowo na żywo tylko próbka; pełne = własny węzeł albo
płatne S3 (decyzja użytkownika); 0 wariantów, licznik E1 bez zmian.`

## Rekomendacja

Zgodnie z zadaniem: **STOP przed krokiem 1**. Do decyzji użytkownika (przez orkiestratora):
1. **Tryb ograniczony (bez nowych kosztów):** kolektor na kilka głównych monet z odpytywaniem stron aktywnych —
   najpierw zmierzyć wagę/min dla tego zestawu na dłuższym oknie (BTC/ETH/SOL już dziś ~1 240/min, czyli trzeba rzadszych
   obiegów). Albo tryb „raz na dobę” dla całej giełdy — najpierw sonda: unikalne strony aktywne na dobę i koszt ciężkich
   adresów.
2. **Pełne źródło:** własny węzeł Hyperliquid (zapis wypełnień) — sprawdzić wymagania sprzętowe w repozytorium węzła;
   albo S3 `node_fills_by_block` (opłata za transfer).
3. **Tanie niezależnie od 1–2:** krok 2 (`metaAndAssetCtxs` co 60 s, ~19 MB/dobę gzip) — historia fundingu i otwartych
   pozycji; spadek OI to pośredni ślad likwidacji. Wymaga decyzji, bo zadanie wiąże krok 2 z pozytywnym 0a.
4. 0b (stan pozycji ~700 adresów co 1–3 min) — mieści się w limicie; osobna decyzja użytkownika.
5. Przy każdym kolektorze: `security-review` (nowe połączenie sieciowe) i `engineering:code-review` — nie robione teraz,
   bo sonda to skrypty jednorazowe.
6. Skrypty tej sondy do `runs/ZAMROZONE.txt` przy scaleniu (zasada 13) — robi orkiestrator.

## Użyte skille (CLAUDE.md zasada 19)

### Użyte skille — gałąź `zadanie-001-lh0-hyperliquid` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-09-29T06:10:06+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` | Zadanie 001 LH0 krok 0 — sonda wykonalności kolektora likwidacji Hyperliquid (0 wariantów, bez odczytu E1), gałąź zadanie-001-lh0-hyperliquid |
| 2026-09-29T06:10:07+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` | Zadanie 001 LH0 krok 0: nowe źródło danych (likwidacje Hyperliquid z publicznego API) — sonda wykonalności, kontrola pozytywna vs LK0/LB0, bez odczytu E1 |

Razem: 2 wczytania, 2 różne skille: `anthropic-skills:clas5-quant`, `anthropic-skills:clas5-runda`.

- **`anthropic-skills:clas5-runda`** — struktura README, oznaczenia [pre]/[implementacja], 0 wariantów, bramka 16a
  i proponowana linia wniosku skumulowanego (wpis do `runs/INDEX.md` robi orkiestrator).
- **`anthropic-skills:clas5-quant`** — nowe źródło danych: kontrola pozytywna przed kolektorem, żadnego odczytu E1,
  jeden licznik E1 dla LK0/LB0/LH0.
- Momenty z tabeli zasady 19 bez skilla: `security-review` — **do zrobienia przy kolektorze** (sonda to jednorazowe
  skrypty, adresy stałe, tylko `https://`/`wss://`, bez kluczy); `engineering:code-review` — przed scaleniem, robi
  orkiestrator; `data:validate-data` / `data:statistical-analysis` — nie wczytane (zakres zlecenia; 0 odczytów, jedyny
  przedział to Wilson w 0b), bramkę 16a zrobiono ręcznie według `docs/skills/bramki-jakosci.md`; `data:explore-data` —
  nie dotyczy (zbiór nie powstał).
