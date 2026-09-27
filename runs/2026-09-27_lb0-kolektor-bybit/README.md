# LB0 — kolektor PEŁNYCH likwidacji Bybit: druga brama danych rodziny E1 (2026-09-27)

> **STATUS: KOD GOTOWY, KONTROLA POZYTYWNA ZALICZONA (2026-09-27).** Kolektor na stałe (cron) uruchamia koordynator po
> scaleniu. **0 wariantów — POZA licznikami:** to zbieranie danych, nie pomiar. Żadnej hipotezy nie odczytano i nie wolno
> jej odczytać, dopóki rachunek mocy na REALNEJ częstości zdarzeń nie powie „mierzalna”. **Jeden licznik E1** dla LK0 i LB0.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Likwidacja to przymusowe zamknięcie przez giełdę pozycji z dźwignią, gdy strata zjada depozyt. Od 2026-09-25 zbieramy
likwidacje z Binance (runda LK0). Binance pokazuje jednak tylko **próbkę**: najwyżej jedną likwidację na sekundę na monetę.
W kaskadzie (seria likwidacji w krótkim czasie) giną więc właśnie te zdarzenia, o które chodzi w hipotezie E1.

Bybit publikuje **wszystkie** likwidacje, za darmo, ale tylko na żywo. Historia jest płatna (decyzja użytkownika: płatne —
nie). Każdy dzień bez kolektora to dzień danych straconych na zawsze. Dlatego ten kolektor.

Próba 180 s (niedziela wieczór, spokojny rynek): **58 likwidacji z 16 monet, 78 z 78 subskrypcji przyjętych, 0 błędów.**
Źródło działa. W tym samym oknie Binance pokazał 62 zdarzenia z tych samych głównych monet i z tą samą przewagą
zlikwidowanych shortów. To potwierdza, że kierunek likwidacji czytamy dobrze (w Bybit pole strony znaczy coś odwrotnego niż
w Binance — szczegóły niżej).

## Metadane

- **ID:** LB0. Branch `etap6-bybit` (z `etap6-wykonanie` `3d30118`). Źródło decyzji: `docs/rag/11_przeglad_kandydatow_2026-09-27.md`
  (sekcja 3, „Kolektor pełnych likwidacji Bybit”, status **ok**; sekcja 6, krok 1) + decyzja użytkownika „wykonaj wszystkie”.
- **Kod:** `data/collect_liquidations_bybit.py`; nadzór: `tools/likwidacje.sh` (ten sam cron co LK0, osobna blokada `flock`
  w katalogu Bybit); `DayWriter` z LK0 dostał parametr `time_key` (domyślnie `"E"`, więc LK0 działa bez zmian).
- **Testy:** `tests/test_collect_liquidations_bybit.py` (44, bez sieci: parser i mapowanie strony, odrzucanie złych symboli,
  liczb i czasów, plan subskrypcji — właściwości w `hypothesis`: ≤ 10 tematów na żądanie, limit znaków, żaden symbol nie ginie
  ani się nie powtarza; lista instrumentów z paginacją; pętla z fałszywym połączeniem: zapis per dzień UTC, liczniki, ping,
  ponowne łączenie po ciszy, rosnące odczekanie, odświeżenie listy symboli, kilka połączeń naraz; próba bez zapisu na dysk)
  + `tests/test_likwidacje_sh.py` (5, skrypt nadzoru na katalogach tymczasowych z fałszywym pythonem).
- **Źródło:** `wss://stream.bybit.com/v5/public/linear`, temat `allLiquidation.{symbol}` (push co 500 ms, wszystkie likwidacje).
  Lista monet: `https://api.bybit.com/v5/market/instruments-info?category=linear` (status `Trading`, `LinearPerpetual`,
  rozliczenie USDT; kursor stron). Publiczne, bez klucza, adresy stałe w kodzie, tylko `wss://` i `https://`.
- **Dane POZA repo:** `$HOME/likwidacje_bybit/YYYY-MM-DD.jsonl` (dzień UTC czasu likwidacji `T`), `status.json` (liczniki,
  co ≥ 30 s), `kolektor.log` (połączenia, rozłączenia, pominięte, nieudane subskrypcje, zmiany listy monet), `kolektor.out`.
- **Wiersz = jedna likwidacja:** `T` (ms), `s` symbol, `S` strona (surowo, jak w JSON), `v` wielkość w monetach, `p` cena
  upadłości (tekst, bez przeliczeń), `pos` — kierunek ZLIKWIDOWANEJ pozycji (`long`/`short`), `ts` — czas wysłania
  wiadomości przez Bybit (ms), `rcv` — czas odbioru na serwerze (ms). Odczyt: `collect_liquidations_bybit.load_day`.
- **Plan połączeń (2026-09-27):** 777 monet → 2 połączenia (688 + 89 tematów), 78 żądań subskrypcji. Limit Bybit to
  21 000 znaków tematów na połączenie; nasz budżet to 18 000 (zapas ~14 %), liczony ostrożnie — z cudzysłowami
  i przecinkami. Tak liczone 777 tematów to ~20 300 znaków; same nazwy to ~17 900, czyli jedno połączenie zmieściłoby się
  tuż pod limitem Bybit, bez zapasu na nowe listingi. Stąd dwa połączenia.
- **Pętla:** ping co 20 s; lista monet co 24 h (nowe listingi — wtedy oba połączenia otwierane od nowa); cisza > 15 min bez
  likwidacji na połączeniu = ponowne połączenie; błąd = odczekanie 1 → 60 s (zeruje się dopiero po cyklu > 60 s, żeby nie
  zbliżyć się do limitu 500 połączeń na 5 min z jednego IP).

## Poprzedzające wyniki

LK0 (kolektor Binance, próbka ≤ 1/s/symbol, od 2026-09-25; wniosek 102), P3 (archiwum Binance nie ma likwidacji), katalog
`quant-strategy-catalog` E1 = WYKLUCZONE-danymi, `docs/rag/11` sekcja 3 (rachunek mocy przyszłej karty E1, patrz niżej)
i sekcja 6 krok 1 („zabezpieczyć dane, których nie da się odtworzyć”).

## Pre-rejestracja (treść z `docs/rag/11`, zapisana PRZED napisaniem kodu; 0 wariantów)

- **Co zbieramy:** wszystkie likwidacje z tematu `allLiquidation` dla wszystkich perpetuali liniowych USDT na Bybit, surowo,
  plik per dzień UTC.
- **Czego NIE robimy:** żadnego odczytu hipotezy E1 (ani innej) na tych danych. Najpierw, za 4–6 tygodni, rachunek mocy
  z realnej częstości kaskad — **z samych liczników, bez cen**. Założenie z `docs/rag/11` do sprawdzenia: 150–300
  niezależnych epizodów rocznie. Liczone przez `expected_trades` z częstości zdarzeń (zasada 18), nie ze świec.
- **Rachunek mierzalności przyszłej karty (z `docs/rag/11`, sekcja 3):** horyzont 24 h, rozrzut 5 % na zdarzenie →
  najmniejszy wykrywalny efekt (MDE) 0,99 % na epizod po roku, 0,70 % po 2 latach; przy rozrzucie 8 %: 1,58 / 1,12 %.
  Koszt wejścia i wyjścia w kaskadzie na małych monetach to 0,3–1 %, więc efekt musi przekraczać ~1 %. Wniosek dla decyzji:
  pierwsza karta E1 najwcześniej ~2027-09; dziś nie ma czego mierzyć.
- **Jeden licznik E1** dla LK0 i LB0: przyszły odczyt obu źródeł to jedna hipoteza, nie dwie. Stan licznika: 0 odczytów.
- **Porównanie z LK0** tylko opisowe (liczby zdarzeń w tym samym oknie), bez cen i bez żadnego wniosku o hipotezie.
- **Kryterium „działa”:** kontrola pozytywna > 0 likwidacji i 0 nieudanych subskrypcji; potem proces żyje 24/7 (cron co
  5 min), `--status` pokazuje ostatnią likwidację sprzed minut, dziury tylko przy restartach.
- **Ścieżka odwrotu:** usunąć część Bybit z `tools/likwidacje.sh` (albo zabić proces) i skasować `$HOME/likwidacje_bybit`.
  Kod nie wpływa na żadną rundę ani na dziennik papierowy (dziennik go nie importuje — poprawka dziennika niepotrzebna).

## Wynik — kontrola pozytywna (pełny zapis w `raw_output.txt`)

Polecenie: `PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations_bybit --probe 180` (serwer Linux, commit `557d8fb`).
Próba łączy się, subskrybuje wszystko, liczy likwidacje przez 180 s i nic nie zapisuje na dysk.

| wielkość | Bybit (LB0, pełne) | Binance (LK0, próbka), to samo okno |
|---|---|---|
| okno (UTC) | 2026-09-27 18:46:58 – 18:49:58 | to samo (po czasie zdarzenia `E`) |
| likwidacji | **58** (19,3/min) | 62 (20,7/min; 61 z rynku UM) |
| monet | 16 | 26 |
| zlikwidowane longi / shorty | 14 / 44 | 10 / 52 |
| nominał | ≈ 55 tys. USD (v × cena upadłości) | ≈ 417 tys. USD (q × cena wykonania) |
| najczęstsze monety | ENA 25, QNT 7, ARX 5, ETH 4, ZEC 2 | ENA 13, QNT 6, ZEC 5, ARX 5, NEAR 4 |
| subskrypcje | 78 / 78 udane, 0 nieudanych; 16 odpowiedzi na ping | — |
| pominięte wiadomości | 0 | — |

Co z tego wynika:

1. **Źródło działa pod adresem z dokumentacji.** Inaczej niż w LK0 (tam dokumentowany adres milczał), tu 0 zdarzeń nie
   wymagało diagnozy: adres i temat z dokumentacji nadają od pierwszej sekundy. 20-sekundowa próba dymna przed testami
   dała 2 likwidacje; próba właściwa — 58.
2. **Kierunek czytamy dobrze — sprawdzone drugą drogą.** W Bybit `S = "Buy"` znaczy „zlikwidowano pozycję LONG” (strona
   pozycji). W Binance `S = "SELL"` znaczy to samo (strona zlecenia likwidacyjnego). Po naszym mapowaniu oba źródła pokazują
   w tym oknie wyraźną przewagę zlikwidowanych shortów (44 z 58 i 52 z 62) i te same główne monety (ENA, QNT, ZEC, ARX).
   Gdyby mapowanie było odwrócone, źródła pokazywałyby przeciwne kierunki. To słaby sprawdzian (jedno okno 3 min), ale
   zgodny z dokumentacją obu giełd.
3. **Próbkowanie Binance widać na jednej monecie.** ENAUSDT: Bybit 25 likwidacji, Binance 13 w tym samym oknie. Binance
   pokazuje najwyżej jedną na sekundę — przy gęstej serii gubi resztę. To dokładnie powód istnienia LB0.
4. **Liczby Bybit i Binance nie są porównywalne 1:1.** Binance ma kilkukrotnie większy rynek (nominał ~8× większy), a jego
   liczba zdarzeń jest zaniżona próbkowaniem. Dlatego podobna liczba zdarzeń (58 vs 62) nic nie mówi o „pokryciu” — to tylko
   znak, że oba źródła widzą ten sam rynek w tym samym czasie.
5. **Rozmiar danych (szacunek z próby):** wiersz ~120 bajtów, ~20 likwidacji/min w spokojnym oknie → ~3–4 MB na dobę bez
   kompresji. W dniach kaskad wielokrotnie więcej. To jedno okno w niedzielę wieczorem — częstości z niego nie wolno
   uogólniać; realny profil dopiero po 4–6 tygodniach.

**Werdykt bramki 16a (Claude, agent gałęzi): Caveats** — źródło potwierdzone kontrolą pozytywną, mapowanie strony zgodne
z drugim źródłem; zastrzeżenia: jedno krótkie okno, przegląd bezpieczeństwa i przegląd kodu (bramka 16c) robi koordynator
przed scaleniem.

## Co na plus (+) / Co na minus (−)

**(+)**
- **Pełna lista, nie próbka** — pierwsze źródło, które widzi kaskadę w całości. Darmowe, bez klucza.
- Adres i temat zgodne z dokumentacją, potwierdzone doświadczalnie (kontrola pozytywna), a nie tylko przepisane.
- Surowe pola bez przeliczeń + jawny kierunek `pos` — przy łączeniu z LK0 nie da się pomylić, kto został zlikwidowany.
- Lista monet odświeżana co 24 h — nowe listingi (często najbardziej lewarowane) wchodzą same.
- Ten sam format plików, statusu i nadzoru co LK0; osobna blokada i katalog — awaria jednego nie rusza drugiego.

**(−)**
- **Zero historii.** Rodzina E1 pozostaje wykluczona danymi aż do ~roku zbierania. Pierwsza karta najwcześniej ~2027-09.
- **Kogo nie ma w zbiorze:** likwidacji sprzed 2026-09-27; kontraktów USDC, kwartalnych futures i inverse (tylko perpetuale
  USDT); innych giełd poza Binance (LK0, próbka) i Bybit (OKX — „nie teraz”, `docs/rag/11`); minut, gdy proces nie żył
  (restart serwera, błąd — dziury widać w `status.json` i logu); monet wprowadzonych w ciągu doby przed najbliższym
  odświeżeniem listy (do 24 h opóźnienia).
- **`p` to cena upadłości, nie cena wykonania.** Nominał `v × p` jest przybliżeniem; do analizy „przestrzelenia” ceny trzeba
  będzie cen z rynku (osobne źródło).
- **Jeden proces, dwa połączenia.** Błąd jednego połączenia otwiera od nowa oba (kilka sekund dziury także na zdrowym).
  To świadome uproszczenie — w zamian jedna prosta pętla.
- **Dane rosną szybciej niż LK0** (pełna lista) — rozmiar i kopia zapasowa do sprawdzenia po pierwszym tygodniu
  (kopia LK0 i LB0 poza serwerem — osobne zadanie z `docs/rag/11`, decyzja użytkownika o miejscu kopii).

## Nadzór i uruchomienie

- Stan: `PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations_bybit --status` — „ostatnie” powinno być sprzed minut;
  „subskrypcje nieudane” = 0; „symboli … w 2 połączeniach”.
- Cron — ta sama linia co dla LK0 (`*/5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje.sh`); po scaleniu do `master`
  i pobraniu w klonie dziennika skrypt sam wystartuje kolektor Bybit w tle przy najbliższym przebiegu crona.
- Ręczny start z dowolnego klonu: `nohup bash tools/likwidacje.sh >/dev/null 2>&1 &` (blokady wspólne — druga instancja
  żadnego kolektora nie wystartuje; działający kolektor Binance nie jest dotykany).
- Katalog danych: `$HOME/likwidacje_bybit` (zmiana: zmienna `CLAS5_LIKWIDACJE_BYBIT_DIR`).

## Wniosek

Pełne likwidacje Bybit da się zbierać za darmo pod adresem z dokumentacji; kontrola pozytywna dała 58 likwidacji w 3 minuty
przy 0 błędach, a kierunek zgadza się z Binance. To druga — i pierwsza pełna — brama danych rodziny E1. Nic nie odczytano;
odczyt E1 najwcześniej po ~roku, po rachunku mocy z realnej częstości kaskad.

## Rekomendacja

1. Scalić po przeglądzie kodu i bezpieczeństwa; kolektor wystartuje z crona (ta sama linia co LK0).
2. Po tygodniu: `--status` + rozmiar plików; potem kopia LK0 i LB0 poza serwerem (decyzja użytkownika o miejscu).
3. Po 4–6 tygodniach: profil danych (`data:explore-data`) z samych liczników — zdarzeń na dobę, epizody kaskad, dziury,
   porównanie z LK0 — i rachunek mocy przyszłej karty E1. Bez cen, bez odczytu hipotezy.
4. Kartę E1 (`quant-strategy-catalog`) pisać dopiero z tym rachunkiem; jeden licznik dla LK0 i LB0.

## Użyte skille (CLAUDE.md zasada 19)

UZUPEŁNIA KOORDYNATOR (agent gałęzi `etap6-bybit` nie wczytywał skilli — zrobił to koordynator na gałęzi `etap6-wykonanie`;
do uzupełnienia: wynik `py tools/skill_audit.py raport --galaz …`, `security-review` dla nowego połączenia sieciowego,
`engineering:code-review` przed scaleniem).
