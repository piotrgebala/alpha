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
- **Bramka 16c (orkiestrator, `engineering:code-review`, przy scaleniu 2026-09-29): Approve** — jednorazowe skrypty sondy
  łączą się wyłącznie z `https://api.hyperliquid.xyz/info` i `wss://api.hyperliquid.xyz/ws`, bez kluczy i zmiennych
  środowiskowych, zapisują tylko do ścieżek z argumentów (katalog tymczasowy); zamrożone w `runs/ZAMROZONE.txt`. Liczby
  kontroli pozytywnej sprawdzone w `raw_output.txt` (BTC 109 wypełnień = 78 zleceń, ETH 17 = 13, razem 91).


---

# Krok 1 — tryb ograniczony (zadanie 004)

> **STATUS: KROK 1 ZAMKNIĘTY — werdykt A: STOP (nic się nie mieści). LH0 zamknięte decyzją użytkownika 2026-10-05
> („tak zamknij 004”).** Kolektora (kroki B–D) NIE zbudowano. **0 wariantów — POZA licznikami**, bez odczytu E1
> (nie zestawiamy likwidacji z cenami; licznik E1 wspólny z LK0/LB0, stan: 0 odczytów).

## Metadane (krok 1)

- Zadanie `zadania/004-lh0-tryb-ograniczony.md`; decyzja użytkownika 2026-09-29: „Tryb ograniczony, bez kosztów:
  kolektor tylko na kilka głównych monet. Najpierw trzeba zmierzyć na dłuższym oknie, czy zmieści się w limicie.”
- Gałąź `zadanie-004-lh0-tryb-ograniczony` od `master` `283749c`.
- Sieć: wyłącznie `https://api.hyperliquid.xyz/info` i `wss://api.hyperliquid.xyz/ws`. Bez kluczy, portfeli, zleceń, MCP.

## Poprzedzające wyniki (krok 1)

Krok 0 tej rundy (wniosek 110): trójka BTC/ETH/SOL odpytywana w całości kosztowała 1 243 wagi/min przy limicie
1 200 na IP; średnio 21,8 wagi na zapytanie `userFillsByTime`; 91 likwidacji w 44 min (78 BTC, 13 ETH, 0 SOL), każda
z metodą `market`, zlikwidowany zawsze stroną aktywną. Wnioski 102 i 106 (LK0, LB0): źródło przyjmujemy po kontroli
pozytywnej na żywo. **Co z tego wynika dla projektu kroku 1 (jedno zdanie):** skoro pełne odpytanie trójki już
przekracza limit, koszt sposobów liczymy z darmowych zliczeń strumienia `trades` (bez wag), a prawdziwe zapytania
robimy tylko na losowej próbce pod twardym sufitem wag, i na tej samej próbce sprawdzamy, czy filtr gubi likwidacje.

## Pre-rejestracja kroku A (zapisana PRZED pomiarem; 0 wariantów, pomiar kosztu, nie strategii)

- **[pre] Zestawy monet:** S1 = {BTC}, S2 = {BTC, ETH}, S3 = {BTC, ETH, SOL}. Tylko perpetuale głównej giełdy.
- **[pre] Strona aktywna** (taker) = `users[0]` przy `side: "B"`, `users[1]` przy `"A"` (potwierdzone w kroku 0:
  10 680 / 10 680). **Zlecenie aktywne** = grupa transakcji o tym samym (moneta, strona aktywna, `hash`).
- **[pre] Sposoby odpytywania** (zapytanie = `userFillsByTime` dla adresu i okna; waga wg dokumentacji
  „Rate limits”: 20 + 1 za każde rozpoczęte 20 zwróconych wypełnień, każda strona wyników osobno):
  - **M1 — pełny, co minutę:** każdy unikalny adres strony aktywnej w zestawie w danej minucie → 1 zapytanie za tę minutę.
  - **M2 — tylko strony aktywne z ruchem ceny**, co minutę. Dwie definicje ruchu ceny (obie liczone, obie raportowane):
    **F1** = zlecenie aktywne zmiotło ≥ 2 poziomy ceny (≥ 2 różne `px` w zleceniu);
    **F2** = pierwsza cena zlecenia jest „dalej” w kierunku agresora niż cena poprzedniej transakcji w tej monecie
    (kupno powyżej, sprzedaż poniżej) albo F1. Adres wchodzi do M2, jeśli w oknie ma ≥ 1 zlecenie spełniające filtr.
  - **M3 — obiegi co N min z `startTime`:** jedno zapytanie na unikalny adres strony aktywnej na okno N minut,
    N ∈ {5, 15, 60}; zapytania rozłożone równomiernie w następnym oknie (koszt/min = koszt okna / N).
  - **M4 — pomijanie adresów bez pozycji:** zapytanie jest zbędne, jeśli adres na początku okna nie miał pozycji
    w żadnej monecie zestawu, w której handlował, i w oknie ma w tych monetach tylko jedno zlecenie (`oid`) — wtedy
    likwidacja jest niemożliwa (likwidacja zamyka istniejącą pozycję i jest osobnym zleceniem). Mierzone jako
    **górna granica oszczędności** (zakłada pełną wiedzę o pozycji na starcie okna, ustaloną tu z samych wypełnień);
    realne źródło tej wiedzy nie jest dziś wskazane, więc M4 raportujemy jako oszczędność potencjalną i **nie
    przyznajemy mu samodzielnie „mieści się”**.
- **[pre] Jak liczony koszt:** darmowe zliczenia z WebSocket `trades` (unikalne adresy na minutę / na okno N, dla
  każdego zestawu i filtra) × średnia zmierzona waga zapytania `w̄` z próbki (osobno dla każdej długości okna 1/5/15/60
  min, z adresów, które handlowały w danym zestawie). Obok: dolna granica 20 wagi/zapytanie (bez `w̄`).
  Statystyki na szeregu minut (M1, M2) i okien (M3, podzielone przez N): **średnia, mediana, p95, maks.**
- **[pre] Próg (z zadania, bez zmian):** sposób × zestaw „mieści się”, jeśli **średnie zużycie ≤ 600 wagi/min**
  (50 % limitu 1 200; reszta to zapas i ewentualne 0b) **ORAZ p95 ≤ 1 200 wagi/min** (drugi warunek: w godzinach
  ruchu kolektor nie może stale zderzać się z limitem; dopisany teraz, przed wynikiem). Dla M2 dodatkowo filtr musi
  nie gubić likwidacji (niżej). Jeśli żaden sposób × zestaw nie mieści się — **STOP, raport do użytkownika**.
- **[pre] Czy filtr gubi likwidacje (M2):** prawda = losowa próbka stron aktywnych każdego okna, odpytana w całości;
  likwidacja = wypełnienie z polem `liquidation`, w którym zlikwidowanym jest ten adres (jednostka: zlecenie
  (adres, `oid`)), tylko w monetach zestawu. Likwidacja jest „zgubiona” przez filtr, jeśli jej adres w tym oknie nie
  przeszedł filtra. Filtr **nie gubi**, jeśli górna granica 95 % (dokładna, Cloppera–Pearsona) udziału zgubionych
  ≤ 5 % (np. 0 zgubionych przy ≥ 59 likwidacjach). W przeciwnym razie raportujemy udział z przedziałem, a filtr daje
  tylko **próbkę** (decyzja użytkownika). Dodatkowo co 60 min jedno okno 1-min zestawu S3 odpytane w całości
  (porównanie z pełnym odpytaniem na krótkim oknie).
- **[pre] M3 a gubienie:** M3 czyta te same dane później, więc gubi tylko przez obcięcie wyników (2 000 wypełnień na
  stronę) — liczymy adresy, które wymagały stronicowania albo zostały ucięte (limit 5 stron).
- **[pre] Opóźnienie wykrycia:** czas odebrania odpowiedzi − czas `T` wypełnienia likwidacyjnego, per N (mediana, p95).
- **[pre] Okno:** ≥ 24 h ciągłego pomiaru (plan 26 h), obejmuje porę azjatycką, europejską i amerykańską. Okresu
  kaskady nie da się zaplanować — jeśli wystąpi, opiszemy; jeśli nie, zapiszemy jako ograniczenie.
- **[pre] Budżet samego pomiaru:** próbkowanie celuje w ≤ 700 wagi/min (okno przesuwne 60 s), **twardy sufit 900**;
  przy 429 rosnące odczekanie (10 s → 300 s), nigdy obchodzenie (bez dodatkowych IP/proxy). Liczba 429 w wyniku.
- **[pre] Czego NIE robimy:** żadnych cen po likwidacjach, żadnego odczytu E1, żadnego stanu pozycji (0b),
  żadnego `metaAndAssetCtxs`.
- **Hash pre-rejestracji:** `6f7e10c` (commit samej pre-rejestracji, przed napisaniem skryptu i przed pomiarem).
- **[implementacja] Skrypt:** `data/measure_hl_weights.py` (commit `c9cd2bd`), testy bez sieci
  `tests/test_measure_hl_weights.py` (w tym `hypothesis`: ogranicznik nigdy nie przekracza sufitu 900 w żadnym oknie
  60 s; F1 ⇔ ≥ 2 różne ceny; reguła M4 nie pomija adresu z likwidacją; przedział CP). Kwoty próbki na okno:
  N=1: 10, N=5: 30, N=15: 45, N=60: 90 adresów; zapytania okien N > 1 rozłożone na 0,9·N min; minuta liczy się tylko,
  gdy połączenie WebSocket trwało przez całą minutę; zadanie próbki starsze niż 2N + 5 min od planowanego startu jest
  porzucane i liczone. Stronicowanie `startTime = max(time) + 1` (wyniki rosnąco — sprawdzone na żywo), najwyżej
  5 stron.
- **[implementacja] Próba dymna (nie jest dowodem, nie w `raw_output.txt`):** 6 min 08:27–08:33 UTC do katalogu
  tymczasowego sesji — 86 zapytań, 0 × 429, waga samego pomiaru ≤ 700/min, 4 pełne minuty; mechanika działa.
- **[implementacja] Uruchomienie:** kopia skryptu poza repo, żeby przeżyła usunięcie worktree:
  `$HOME/likwidacje_hl/pomiar_krok1/measure_hl_weights.py` (sha256 `3bf50945f0c2…84bbe1`, identyczna z `c9cd2bd`),
  start `bash $HOME/likwidacje_hl/pomiar_krok1/start.sh` (`setsid nohup`, 26 h, interpreter `~/alpha/.venv`).
  Wyniki w tym samym katalogu: `minuty.jsonl`, `zapytania.jsonl`, `status.json`, `pomiar.log`, `stdout.txt`.
  Postęp: `~/alpha/.venv/bin/python ~/likwidacje_hl/pomiar_krok1/measure_hl_weights.py --status`.
  Po końcu: `… --podsumuj` dopisane do `raw_output.txt` pod nagłówkiem „KROK 1A — pomiar wag” (krok 0 zostaje
  nad nim bez zmian).
- **[implementacja] Stan uruchomienia:** PID `1387584`, start 2026-09-29 08:33:37 UTC, koniec planowany
  2026-09-30 10:33 UTC (proces kończy się sam). Pierwsze odczyty z `pomiar.log`: waga samego pomiaru w ostatnich
  60 s = 211 / 357 / 353 (08:38 / 08:43 / 08:48 UTC), 0 × 429, 188 zapytań do 08:48. Pełny `pytest`: 1 935 passed,
  3 skipped, kod 0.
- **Co zostaje po końcu pomiaru (następna sesja):** dopisać `--podsumuj` do `raw_output.txt`; wynik A z werdyktem
  per zestaw i sposób (próg wyżej), druga droga kluczowej liczby, bramka 16a; potem — tylko jeśli coś się mieści —
  kroki B–D. Jeśli nic się nie mieści: STOP i raport do użytkownika.

## W skrócie — krok 1 prostym językiem (zasada 17)

Przez 26 godzin mierzyliśmy, ile kosztuje wyłapywanie likwidacji z Hyperliquid na samym BTC, na BTC+ETH i na
BTC+ETH+SOL. Koszt liczy się w jednostkach limitu zapytań (giełda daje 1 200 na minutę z jednego adresu IP; na
kolektor przeznaczyliśmy z góry połowę). Wynik jest jednoznaczny:

- **Sposoby, które niczego nie gubią, są za drogie** — nawet dla samego BTC średnio ~1 210 jednostek na minutę
  (2× za dużo), a odpytywanie raz na godzinę wciąż ~630 przy szczytach ~1 730.
- **Jedyny tani sposób (filtr „zlecenie zmiotło ≥ 2 poziomy ceny”) mieści się w budżecie, ale gubi ~93 % likwidacji**
  (65 z 70 w próbce). Takie dane nie nadają się do badania kaskad.

Co to znaczy dla decyzji: trzeciego kolektora likwidacji z darmowego API Hyperliquid nie da się zbudować w zapisanych
granicach. Użytkownik zdecydował 2026-10-05: zamknąć LH0. Likwidacje dalej zbierają LK0 (Binance) i LB0 (Bybit).

## Wynik kroku A (pełny zapis: `raw_output.txt`, sekcja „KROK 1A — pomiar wag”)

- **Okno:** 2026-09-29 08:32 → 2026-09-30 10:32 UTC (1 561 minut, 1 546 pełnych — połączenie bez przerwy; 10 rozłączeń).
  Pora azjatycka, europejska i amerykańska objęte; **kaskady w oknie nie było** (ograniczenie — zob. 16a).
- **Pomiar sam:** 33 048 zapytań, **0 × 429**, waga własna średnio 451 / mediana 424 / p95 693 / maks. 796 wagi/min
  (twardy sufit 900 dotrzymany). 237 zadań próbki porzuconych jako przeterminowane (zapisane w `status.json`).
- **Średnia waga zapytania `w̄`:** 20,9 (N = 1 min) … 23,1 (N = 60 min) — prawie zawsze minimalne 20 + 1.
- **Dane surowe poza repo** (`$HOME/likwidacje_hl/pomiar_krok1/`): `minuty.jsonl` 9 629 254 B
  (sha256 `5406a4fa…ddee63`), `zapytania.jsonl` 11 405 788 B (`08dadba1…7f4c`), `status.json`, `pomiar.log`
  (pełne hashe w nagłówku sekcji `raw_output.txt`). Skrypt sha256 `3bf50945…84bbe1` = commit `c9cd2bd`.
  Podsumowanie powtórzone drugi raz — wydruk identyczny bajt w bajt.

**Koszt [wagi/min] — próg: średnia ≤ 600 ORAZ p95 ≤ 1 200 (pre-rejestracja):**

| zestaw | sposób | średnia | mediana | p95 | maks. | budżet |
|---|---|---|---|---|---|---|
| S1 {BTC} | M1 pełny co 1 min | 1 209 | 1 005 | 2 449 | 9 692 | NIE |
| S1 | M2 F1 co 1 min | 231 | 209 | 480 | 1 107 | mieści się |
| S1 | M2 F2 co 1 min | 690 | 587 | 1 362 | 4 821 | NIE |
| S1 | M3 co 60 min | 628 | 565 | 1 727 | 1 727 | NIE |
| S2 {BTC, ETH} | M2 F1 co 1 min | 403 | 372 | 765 | 1 901 | mieści się |
| S3 {BTC, ETH, SOL} | M1 pełny co 1 min | 2 196 | 1 819 | 4 412 | 15 955 | NIE |
| S3 | M2 F1 co 1 min | 459 | 414 | 869 | 2 171 | mieści się |
| S3 | M3 co 60 min | 1 014 | 935 | 2 689 | 2 689 | NIE |

(Pozostałe 10 wierszy — wszystkie „NIE” — w `raw_output.txt`. M4, czyli pomijanie adresów bez pozycji, daje górną
granicę oszczędności 21–70 %; nawet z nią M3 N=60 S1 ma p95 ≈ 1 727 × 0,75 ≈ 1 290 > 1 200, a samodzielnego
„mieści się” M4 nie dostaje z pre-rejestracji, bo wymaga wiedzy o pozycjach, której źródła nie ma.)

**Czy filtr gubi likwidacje** (próg: górna granica 95 % Cloppera–Pearsona udziału zgubionych ≤ 5 %):

| zestaw | filtr | likwidacji | zgubionych | udział | przedział 95 % (CP) | werdykt |
|---|---|---|---|---|---|---|
| S1 | F1 | 40 | 37 | 92,5 % | do 98,4 % | gubi |
| S2 | F1 | 56 | 51 | 91,1 % | do 97,0 % | gubi |
| S3 | F1 | 70 | 65 | 92,9 % | do 97,6 % | gubi |
| S3 | F2 | 70 | 61 | 87,1 % | do 93,9 % | gubi |

Na poziomie samego zlecenia likwidacyjnego F1 nie złapał żadnego (0 z 21 dopasowanych w S3). Powód jest prosty:
likwidacja na Hyperliquid to zwykle małe zlecenie rynkowe, które bierze jeden poziom ceny. 25 pełnych okien 1-min
(2 923 adresy, 61 364 wagi) nie miało ani jednej likwidacji — porównanie z pełnym odpytaniem nic nie dodaje.
Opóźnienie wykrycia: mediana 75 s (N = 1) … 3 483 s (N = 60).

**Werdykt A (według pre-rejestracji): żaden sposób × zestaw nie spełnia łącznie progu kosztu i progu „nie gubi”.**
Jedyne „mieści się” (M2 F1) gubi ~9 z 10 likwidacji, więc dawałoby tylko próbkę. Pre-rejestracja oddaje ten wybór
użytkownikowi; użytkownik 2026-10-05 wybrał STOP („tak zamknij 004”). Kroki B–D nie są wykonywane.

## Bramka 16a (walidacja write-upu, skill `data:validate-data`)

- **Druga droga liczby:** własny krótki kod (bez importu skryptu pomiaru) z `minuty.jsonl` i `zapytania.jsonl`:
  M1 S1 — 1 546 pełnych minut, `w̄` 20,93 (n = 8 472) → **średnia 1 209, mediana 1 005, p95 2 449** — zgodne z
  wydrukiem (1 209 / 1 005 / 2 449). S3 F1 — **65 z 70 zgubionych (92,9 %)** — zgodne. Dodatkowo po deduplikacji
  (ta sama likwidacja bywa w próbce kilku okien N): **63 z 67 unikalnych zleceń (94,0 %, przedział 95 % CP
  85,4–97,6 % dwustronnie; skrypt drukuje jednostronną górną granicę 97,9 %)** — wniosek bez zmian.
  Komenda: `~/alpha/.venv/bin/python runs/2026-09-29_lh0-kolektor-hyperliquid/druga_droga_krok1.py` (wydruk
  w `raw_output.txt`, sekcja „KROK 1A — druga droga”).
- **Kogo NIE ma w zbiorze:** okresu kaskady (dzień spokojny; w kaskadzie stron aktywnych i likwidacji jest więcej,
  więc koszt M1/M3 byłby WYŻSZY — STOP tylko się wzmacnia); monet spoza S3; likwidacji „backstop” przez HLP (z kroku 0);
  237 porzuconych zadań próbki (porzucenie zależy od kolejki, nie od tego, czy adres miał likwidację).
- **Czerwona flaga „wynik idealnie potwierdza hipotezę”:** nie dotyczy — hipotezą było „mieści się”, wynik ją obala.
  Dlaczego F1 gubi, wyjaśnia mechanizm (małe zlecenie rynkowe, jeden poziom ceny), nie przypadek.
- **Werdykt: Caveats** — jedno okno 26 h bez kaskady, 3 monety; zastrzeżenie działa przeciw kolektorowi, nie za nim.

## Bramka 16b (statystyka, skill `data:statistical-analysis`)

Efekt podany z przedziałem (udział zgubionych, CP 95 %), mediana obok średniej we wszystkich tabelach kosztu
(rozkład prawoskośny: maks. do 8× średniej przy odpytywaniu co minutę). Licznik wariantów: **0 — POZA licznikami**, bez odczytu E1 (licznik E1
wspólny z LK0/LB0: 0 odczytów). To pomiar kosztu źródła danych, nie test strategii — nie ma `t`, `N_eff` ani zwrotu.

## Co na plus (+) / Co na minus (−) — krok 1

- (+) Pre-rejestracja (`6f7e10c`) przed skryptem i pomiarem; próg nieruszony po wyniku.
- (+) 26 h, 0 × 429, sufit wag dotrzymany; wydruk odtwarzalny bajt w bajt; druga droga zgodna.
- (+) Jasny mechanizm porażki taniego filtra (likwidacja = małe zlecenie rynkowe).
- (−) Brak kaskady w oknie; nie sprawdzono innych sposobów (węzeł własny, płatne S3) — to osobne decyzje.
- (−) Jednostka „zlecenie” w próbce liczona per rekord, nie unikalnie (różnica 70 vs 67, bez wpływu na werdykt).

## Wniosek — krok 1

Z darmowego API Hyperliquid nie da się zbudować kolektora likwidacji w granicach połowy limitu zapytań: pełne
odpytanie jest 2× za drogie już dla samego BTC, a tani filtr gubi ~93 % likwidacji (przedział 85–98 %). LH0 zamknięte
(wniosek 115 w `runs/INDEX.md`).

## Rekomendacja — krok 1

- LH0 zamknięte; skrypt pomiaru zamrożony (`runs/ZAMROZONE.txt`). LK0 i LB0 działają dalej bez zmian; E1 korzysta z nich.
- Zadanie 010 (`metaAndAssetCtxs` co 60 s — funding i premia HL vs Binance) **nie zależy od likwidacji** i jest tanie
  (~1 zapytanie/min); start wymaga osobnej decyzji użytkownika.
- Zadanie 018 (kohorty pozycji z Liquid) czekało na 004 — wraca do decyzji użytkownika.
- Pełne źródło likwidacji HL (własny węzeł albo płatne S3) — tylko na wyraźną decyzję użytkownika (nowa infrastruktura
  albo koszt); dziś bez rekomendacji.

## Bramka 16c (przegląd diffu przed scaleniem, skill `engineering:code-review`)

Diff gałęzi wobec `master`: `data/measure_hl_weights.py` (869 linii), `tests/test_measure_hl_weights.py` (359), README,
`raw_output.txt`, skrypt drugiej drogi, `runs/INDEX.md`, `STATUS.md`, `runs/ZAMROZONE.txt`, karta zadania 004.
Sieć wyłącznie `wss://api.hyperliquid.xyz/ws` i `https://api.hyperliquid.xyz/info` (stałe w kodzie), bez kluczy,
zmiennych środowiskowych, `subprocess` i `eval`; zapis tylko do katalogu z `--dir` (dopisywanie `jsonl`/log). Uwagi
drobne, bez wpływu na wynik: `open(path)` przy odczycie bez jawnego `encoding` (na Windows inne kodowanie domyślne —
pliki są ASCII/JSON, więc bez skutku); jednostka „zlecenie” w teście gubienia liczona per rekord próbki, nie unikalnie
(opisane w 16a). `black`/`ruff` czyste. **Werdykt: Approve — kod pomiaru jest zamrożony i łączy się tylko z publicznym
API Hyperliquid, liczby wyniku odtwarzają się bajt w bajt i drugą drogą.**

## Użyte skille — krok 1 (CLAUDE.md zasada 19)

### Użyte skille — gałąź `zadanie-004-lh0-tryb-ograniczony` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-09-29T08:18:35+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` | Zadanie 004 LH0 krok 1 A — pomiar wag Hyperliquid (tryb ograniczony), gałąź zadanie-004-lh0-tryb-ograniczony |
| 2026-09-29T08:18:35+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` | Zadanie 004 LH0 krok 1 A: nowe źródło danych (likwidacje Hyperliquid) — pomiar kosztu wag odpytywania, 0 wariantów, bez odczytu E1 |

Razem: 2 wczytania, 2 różne skille: `anthropic-skills:clas5-quant`, `anthropic-skills:clas5-runda`.

- **`anthropic-skills:clas5-runda`** — pre-rejestracja kroku A przed pomiarem, struktura sekcji, 0 wariantów.
- **`anthropic-skills:clas5-quant`** — próg „nie gubi” z przedziałem CP zamiast samej średniej; żadnego odczytu E1.
- **`data:validate-data`**, **`data:statistical-analysis`**, **`engineering:code-review`** — wczytane 2026-10-05
  (17:24:13, 17:25:11, 17:27:33 UTC) PRZED bramkami 16a, 16b, 16c w sesji orkiestratora (wykonawca-fork). Hook zapisał
  je do `runs/skille/master.jsonl`, bo katalog roboczy sesji to główny klon na `master`, a nie worktree tej gałęzi;
  `skill_audit.py zarejestruj` odmówił (wczytanie nie w głównej rozmowie). Plików rejestru nie edytowano ręcznie.
  Wniosły: druga droga z dedup (70 → 67) i pytanie „kogo nie ma” (brak kaskady); mediana obok średniej i przedział CP;
  przegląd sieci i zapisu w diffie.
- Pominięte z tabeli: `security-review` — kolektora z nowym połączeniem nie zbudowano (skrypt pomiaru był
  jednorazowy, adresy stałe, bez kluczy); `data:explore-data` — nie dotyczy (zbiór kolektora nie powstał); `dataviz` —
  bez wykresu.
