# 025, krok 1 — dziennik przy wycofaniu lub wstrzymaniu kontraktu: przegląd kodu

- **Gałąź:** `zadanie-025-dziennik-wycofanie`, baza `c383d2b` (origin/master 2026-09-30).
- **Zgoda:** decyzja użytkownika 2026-09-30 „25 zgoda” — tylko krok 1 (przegląd) i pytanie o częstość. Kod dziennika
  **bez zmian**. Wyników dziennika (`dziennik/*.csv`, `przebiegi.log`) nie czytałem.
- **Liczba wariantów:** 0 (opis mechaniki i częstości zdarzeń, bez zwrotów strategii).
- **Dowody:** `dowod_syntetyczny.py` → `dowod_syntetyczny.txt` (dane sztuczne, katalog tymczasowy);
  `czestosc.py` → `czestosc.txt` (część B, dane lokalne od 2021-01-01, tylko odczyt).
- **Skill:** `anthropic-skills:clas5-quant` (wczytany przed pracą; rejestr `runs/skille/zadanie-025-dziennik-wycofanie.jsonl`).

## Streszczenie (prostym językiem)

1. Gdy moneta znika z giełdy, dziennik **trzyma pozycję po ostatniej znanej cenie** i liczy jej zwrot jako 0 (jak
   gotówkę). Nie liczy likwidacji i nie zna ceny rozliczenia giełdy. Pozycja znika sama przy kolejnym przebudowaniu
   fazy, czyli najpóźniej po 7 dniach.
2. Gdy cena zamarza (świece są, ale płaskie i bez obrotu), jest gorzej: dziennik **dalej otwiera nowe pozycje** po
   zamrożonej cenie. Trend przez ok. 4 tygodnie, X1 nawet dłużej. Moneta może też **wejść** do koszyka na następny
   miesiąc (w archiwum tak było z FTT w 2022-12 i ALPACA w 2025-05).
3. Przebieg dziennika się **nie wywraca** (sprawdzone na danych sztucznych). Błędy widać tylko jako puste pola (NaN)
   w `transakcje.csv`. Nie ma żadnego ostrzeżenia w logu.
4. Zdarzenie jest rzadkie: **6 na 1 300** par moneta-miesiąc w koszyku (0,46 %, przedział 95 % 0,21–1,00 %). To
   mniej więcej raz w roku (5 z 65 miesięcy).
5. Ryzyko dla wyniku: **małe dla portfela R1** (trend ma wagi skalowane zmiennością i depozyt izolowany; premia
   Coinbase to tylko BTC). **Istotne dla X1**: każda moneta to 10 % kapitału X1, bez dźwigni i bez likwidacji.
   Pozycja wniesiona w wycofanie i rozliczona 90 % niżej to ok. −9 % kapitału X1 na jednej monecie. Taki ruch jest
   realny: cena mark ALPACA po zamrożeniu była od 42 % do 95 % niżej niż cena zamrożona. Dziennik by tego nie pokazał.

## 1. Które nogi trzymają monety spoza BTC/ETH

| noga | instrumenty | źródło w kodzie |
|---|---|---|
| trend (TS1, 2×, likwidacja izolowana) | każdy członek koszyka top-20 (alty) | `live_journal.py:238-240`, `:316` (fazy), `ts_momentum.py:223-259` |
| premia Coinbase (3×) | tylko BTCUSDT | `live_journal.py:241-254`, `:331-333` |
| portfel R1 = trend + premia (mnożniki `sizing.apply_rules`) | alty przez nogę trendu | `live_journal.py:274-283`, `:1173` |
| X1 (osobno, bez dźwigni) | 5 long + 5 short z koszyka top-20 | `live_journal.py:342-392`, `xs_momentum.py:67-77`, `:96-187` |
| carry COIN-M (osobno) | tylko BTCUSD_PERP | `journal_carry.py:34-37` |

ETH nie ma osobnej nogi. Pojawia się tylko jako członek koszyka top-20. Problem dotyczy więc **trendu (a przez niego
R1) i X1**.

## 2. Skąd dziennik ma świece i co się dzieje z plikiem wycofanej monety

- `fetch_live.run` pobiera świece **tylko kontraktów o statusie TRADING** (`fetch_live.py:55`, `:194-199`). Plików
  nie usuwa. Plik monety, która przestała być TRADING, zostaje taki, jaki był przy ostatnim pobraniu.
- `load_live` czyta **wszystkie** pliki `*_1d.parquet` (`live_journal.py:185-212`, `fetch_live.py:113-120`). Po
  ostatniej świecy stary plik daje w panelu NaN.
- Dzień `as_of` wyznaczają tylko BTC i premia Coinbase (`live_journal.py:1167-1171`). Brak świec altu nie opóźnia
  więc przebiegu i go nie zatrzymuje.
- Świeca ostatniego dnia notowania często **nie trafia do pliku**. Przebieg pobiera tylko świece zamknięte
  (`fetch_live.py:82`). Następny przebieg już nie pobiera monety, jeśli giełda zdjęła ją ze statusu TRADING.
  To bywa dzień najbardziej skrajny: w archiwum ALPACA 2025-04-30 zamknięcie 1,19 wobec 0,19 dzień wcześniej.
- Dziennik może wejść w jedną z dwóch ścieżek. **Ścieżka A:** status przestaje być TRADING i świece się kończą.
  **Ścieżka B:** status zostaje TRADING, a świece są płaskie (zamrożenie). Która wystąpi, zależy od statusu u giełdy
  w dniu pobrania. **BRAK DANYCH:** nie mamy historii statusów. W archiwum `data.binance.vision` wycofane kontrakty
  (FTT, ALPACA, BNX, TON) mają płaskie świece z obrotem 0 jeszcze przez miesiące. LUNA i EOS po prostu się kończą.

## 3. Ścieżka A: świece się kończą

| pytanie | odpowiedź | kod | dowód (sztuczny) |
|---|---|---|---|
| Czy pozycja zostaje? | Tak, do najbliższego formowania fazy (≤ 7 dni). Do tego czasu dziennik **ogłasza ją w `sygnaly.csv`**. | `ts_momentum.py:170-191` (waga trzymana), `live_journal.py:286-320`, `:1175-1194` | sekcja 2: w dniu D 6 faz z monetą, D+3 → 3, D+6 → 0 |
| Jaka cena do wyniku? | Ostatnie zamknięcie. Każdy kolejny dzień ma zwrot 0 (NaN → 0), funding 0. W kodzie opisane jako „wycofany = gotówka”. | `ts_momentum.py:329`, `:171-172`, `:330`, `:15`; `xs_momentum.py:114`, `:157-158`, `:116`, `:13` | — |
| Czy liczy likwidację? | Nie. Brak minimum i maksimum dnia zamienia się na 1,0, czyli „bez ruchu”. W liście transakcji porównanie z NaN daje fałsz. | `ts_momentum.py:173-179`; `live_journal.py:566-579` | sekcja 2: „krach” −90 % w dniu D daje 7 likwidacji i −2,69 % kapitału trendu; dziennik bez tej świecy: 0 likwidacji, −0,46 %, czyli **ukryte 2,23 pp** |
| Jak pozycja się zamyka? | Przy następnym formowaniu znak = NaN, więc waga = 0. Koszt obrotu liczony jak sprzedaż po ostatniej cenie. | `ts_momentum.py:56`, `:247-253`, `:163`, `:169`; X1: `xs_momentum.py:71` | sekcja 2 |
| Lista transakcji (poprawka 9) | Zamknięte: `cena_wyjscia` i `zwrot_pozycji_proc` = NaN. Otwarte: `cena_biezaca` i `zwrot_biezacy_proc` = NaN. | `live_journal.py:580-587`, `:646-658` | sekcja 2: 8 zamkniętych wierszy z NaN, 5 otwartych z NaN |
| Czy wypada z koszyka? | W bieżącym miesiącu zostaje członkiem, ale bez wagi. Pozostali dostają trochę więcej, bo N liczy się z ważnych znaków. Od następnego miesiąca wypada (potrzeba 30 notowań w 30 dniach). | `ts_momentum.py:56-61`; `rebalance_premium.py:82-86` | sekcja 2: 2026-08 True, 2026-09 False |
| Czy przebieg się wywraca? | Nie. | — | sekcja 1: 4 scenariusze OK, „historia zmieniona: 0” |

Dwa ryzyka poboczne:

- **Funding wycofanej monety.** Stary plik trzyma monetę w składzie przeszłych miesięcy, więc `funding_symbols` każe
  pobierać jej funding (`fetch_live.py:123-136`, `:202-210`). Ponawiane są tylko błędy sieci (`fetch_universe.py:119`).
  Każdy inny błąd giełdy przerwałby `fetch_live.run`, a przez to cały przebieg (`live_journal.py:1160-1163`, bez
  `try`). Pośredni dowód, że tak się nie stanie: tą samą funkcją (`complete_universe.py:78`) pobrano funding FTT
  i ALPACA długo po ich wycofaniu (`data/raw/universe_full`). Na żywo tego nie sprawdziłem (bez sieci).
- **Świeży katalog danych.** Nowa maszyna albo wyczyszczony `data/raw/live` nie ma pliku wycofanej monety. Dziennik
  liczy wszystko od `ENGINE_START`, więc moneta znika z całej historii. Przebieg zgłasza wtedy „HISTORIA ZMIENIONA”
  (w dowodzie 2 193 pola), a stary zapis zostaje (`live_journal.py:446-474`). To już się dzieje na serwerze.
  `data/raw/live` (pobrany 2026-09-24) nie ma IPUSDT ani TONUSDT. Skład z live różni się od archiwum w 2 z 10 miesięcy
  2025-09…2026-06 (`czestosc.txt`, sekcja 5). Katalogu dziennika na Windows nie sprawdzałem (BRAK DANYCH).

## 4. Ścieżka B: cena zamarza (świece płaskie, obrót 0)

- **Pozycja zostaje, zwrot 0, likwidacja niemożliwa.** Minimum = maksimum = zamknięcie
  (`ts_momentum.py:173-179`, `live_journal.py:566-579`). Dowód, sekcja 3: 34 zamknięcia przez rotację, 0 likwidacji.
  Cena mark w tym czasie potrafi się ruszać mocno. FTT 2022-12: od −59 % do +24 % wobec 1,59. ALPACA 2025-05: od −42 %
  do −95 % wobec 1,19 (`czestosc.txt`, sekcja 4).
- **Dziennik otwiera nowe pozycje po zamrożonej cenie.** Znak trendu to znak zwrotu z 28 dni (`ts_momentum.py:36-39`).
  Jest niezerowy, dopóki zamrożenie nie trwa 28 dni. Zmienność σ̂ maleje, bo zwroty są zerowe
  (`ts_momentum.py:46-47`), więc waga rośnie w stronę sufitu (`:61`). Dowód: 27 z 35 formowań po zamrożeniu ma wagę
  ≠ 0. Znak zmienił się z long na short, a |waga| wzrosła o 23 % (0,0355 → 0,0436).
- **X1 trzyma zamrożoną monetę jeszcze dłużej.** `rank_legs` odrzuca tylko NaN (`xs_momentum.py:71`), a sygnał
  zamrożonej monety po 28 dniach to dokładnie 0, nie NaN (`xs_momentum.py:47-49`). Moneta może więc trafiać do nogi,
  dopóki jest w koszyku. Dowód: 15 formowań po zamrożeniu z monetą w nodze short.
- **Koszyk: zamrożona moneta może do niego wejść.** Świece z obrotem 0 liczą się jako notowania
  (`rebalance_premium.py:85`). Średnią obniżają tylko proporcjonalnie (`:86`). Na danych prawdziwych FTT weszło do
  koszyka 2022-12, choć stało od 2022-11-15. ALPACA weszła 2025-05, choć stała od 2025-05-01. Obie za sprawą
  ogromnego obrotu tuż przed zatrzymaniem.
- **Funding na zamrożonej pozycji.** W archiwum giełda publikuje wtedy stałą stawkę domyślną (FTT 0,01 % na 8 h,
  ALPACA 0,0013 % na godzinę). Silnik ją nalicza (`ts_momentum.py:172`, `:184`). Efekt jest mały.

## 5. Czy to realne ryzyko dla wyniku

- **Częstość (część B, `czestosc.txt`):** 6 par na 1 300 (0,46 %; Wilson 95 % 0,21–1,00 %; Clopper–Pearson
  0,17–1,00 %). 5 z 65 miesięcy ma zdarzenie (7,7 %, 3,3–16,8 %), czyli mniej więcej raz w roku. Druga droga daje
  te same 6 par i ten sam skład.
- **Dwa różne szkody:**
  1. **Pozycja wniesiona w zdarzenie** (otwarta przed nim): wynik bez ceny rozliczenia i bez likwidacji na cenie mark.
     W archiwum: LUNA (trend 7 faz short, X1 4 fazy short), BNX (trend 7, X1 7 long), EOS (trend 7 long), TON (trend
     7 short). To 4 z 6 zdarzeń.
  2. **Pozycje-widma** otwierane po zamrożonej cenie (FTT, ALPACA, BNX, TON). Zwrot wychodzi 0, więc wynik się nie
     psuje wprost. Kapitał jednak stoi bezczynnie, nalicza się koszt i funding, a w X1 widmo **wypiera prawdziwą
     monetę z nogi** (ALPACA w nodze long w 27 z 31 formowań w 2025-05).
- **Wielkość jednej szkody:** trend ma wagi skalowane zmiennością. Na danych prawdziwych to 0,15–2 % kapitału fazy na
  monetę. Przy depozycie izolowanym 2× strata jest ograniczona do połowy wagi, czyli ≤ 1 % kapitału trendu na
  zdarzenie. Premia Coinbase nie ma altów. **X1:** 0,5/5 = 10 % kapitału na monetę, bez dźwigni i bez likwidacji
  (`live_journal.py:707`). Rozliczenie na −90 % to ok. −9 % kapitału X1, a dziennik pokazałby 0.
- **Kierunek nie jest z góry zły.** Short w monecie, której mark spada (FTT), ukrywa zysk. Reguła musi więc być
  symetryczna, a nie „zawsze strata”.
- **Brak alarmu.** Dziennik nie ma pola „moneta w pozycji bez ceny”. Jedyny ślad to NaN w `transakcje.csv`
  i `transakcje_otwarte.csv`. Obsunięcie i STOP (`live_journal.py:1305-1307`) liczą się z zaniżonego obrazu.

## 6. Propozycja reguły rozliczenia (tylko opis, bez kodu)

Zasady: cena, którą giełda naprawdę stosuje. Nigdy zamrożona cena ostatnia. Reguła symetryczna, mechaniczna,
zapisana przed zdarzeniem.

1. **Wykrycie (każdy przebieg).** Moneta trzymana przez fazę trendu lub X1, albo członek koszyka, jest „wstrzymana”
   od pierwszego dnia, w którym zachodzi jedno z trzech:
   - brak świecy, gdy BTC ma świecę;
   - obrót 0 albo open = high = low = close;
   - symbol nie ma statusu TRADING w `exchangeInfo`.

   Status `fetch_live` już pobiera, ale nie zapisuje (`fetch_live.py:194`).
2. **Cena rozliczenia**, w tej kolejności:
   - (i) oficjalna cena rozliczenia Binance z ogłoszenia o wycofaniu (reguły nie weryfikowałem, bez sieci; do
     sprawdzenia, czy da się ją pobrać automatycznie);
   - (ii) zamknięcie ceny **mark** z dnia wstrzymania (publiczne `markPriceKlines`, bez klucza; to samo źródło co
     w LP1);
   - (iii) gdy mark też nie ma: ostatnie normalne zamknięcie, z flagą „rozliczenie przybliżone” w logu.
3. **Likwidacja w oknie wstrzymania (trend):** ekstrema **mark** od wejścia do rozliczenia porównane z progiem 1/2 −
   1 %, jak w LP1 (Binance likwiduje na cenie mark). X1 bez likwidacji, bez zmian.
4. **Nowe pozycje:** wstrzymana moneta nie dostaje wagi w trendzie ani miejsca w nodze X1 od dnia wykrycia.
   Traktowana jest jak brak znaku, tak jak dziś NaN.
5. **Koszyk:** dni z obrotem 0 nie liczą się do 30 dni historii. To zatrzymuje wejście „FTT 2022-12”. Uwaga: to zmiana
   w funkcji wspólnej z rundami (`monthly_members`). Lepiej zrobić ją jako filtr w dzienniku, żeby nie zmienić liczb
   zamrożonych rund. Kosztem jest to, że dziennik przestaje być co do bajtu tym samym silnikiem co rundy. Do decyzji.
6. **Zapis:** w `transakcje.csv` `powod_wyjscia = "wycofanie"` i cena rozliczenia zamiast NaN. W `przebiegi.log` pole
   „wstrzymane: SYM od RRRR-MM-DD, cena X (mark/oficjalna/przybliżona)”, dopisywane tylko przy zdarzeniu (linia bez
   zdarzenia bez zmian, jak w poprawce 12).
7. **Ochrona przed zanikiem pliku:** symbol, który był w `koszyk.csv`, a nie ma pliku w `data/raw/live`, daje alarm
   w logu zamiast cichego przeliczenia historii.

### Szkic „Poprawki N” do `dziennik/README.md` (projekt, wymaga decyzji użytkownika)

> **Poprawka N (RRRR-MM-DD): rozliczenie monety wycofanej lub wstrzymanej.** Od dnia wejścia w życie moneta trzymana
> w trendzie albo X1, która nie ma świecy (przy świecy BTC), ma dzień bez obrotu lub z open = high = low = close
> albo straciła status TRADING, jest zamykana w dniu wykrycia. Cena zamknięcia to oficjalna cena rozliczenia Binance,
> a gdy jej nie ma, zamknięcie ceny mark tego dnia. W trendzie likwidacja izolowana jest sprawdzana na ekstremach ceny
> mark od wejścia do zamknięcia. Od dnia wykrycia moneta nie dostaje nowych pozycji. Dni bez obrotu nie liczą się do
> historii potrzebnej do koszyka. Wiersze sprzed Poprawki się nie zmieniają (append-only). Różnice przeliczenia
> dziennik zgłasza jako „historia zmieniona” z opisem. Kod: `fetch_live` (status i mark 1d dla trzymanych monet — nowe
> połączenie sieciowe, więc `security-review` według zasady 19), `live_journal` (wykrycie, rozliczenie, pola logu),
> testy na przypadkach z `zadania/025-dowody/dowod_syntetyczny.py` (wycofanie, krach, zamrożenie, zanik pliku).
> Poprawka nie zmienia progów, dźwigni ani sygnałów.

## 7. Czego nie sprawdziłem (BRAK DANYCH)

- Historii statusów kontraktów Binance. Nie wiadomo, którą ścieżką (A czy B) dziennik przeszedłby w przeszłych
  zdarzeniach.
- Oficjalnej reguły ceny rozliczenia przy wycofaniu perpetuala (brak sieci).
- Katalogu `data/raw/live` w klonie dziennika na Windows.
- Miesięcy 2026-07…2026-09, czyli okresu dziennika. Archiwum kończy się 2026-06-30, a `data/raw/live` nie ma
  wycofanych kontraktów.
- Wstrzymań krótszych niż 3 dni. Definicja z zadania (seria ≥ 3 dni) ich nie liczy.
- Wpływu na wyniki rund archiwalnych (TS1, X1, SZ1…). One też widziały FTT, ALPACA, BNX i TON jako zamrożonych
  członków. To osobne zadanie typu `badawcze`.
