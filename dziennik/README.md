# Dziennik na żywo (papierowo) — trend tygodniowy + premia Coinbase

> **STATUS: DZIAŁA od 2026-09-24 (poprawka 1: start przesunięty z 25.09 na 24.09).** Reguły poniżej są zamrożone —
> każda zmiana = nowy dziennik od zera (inaczej wynik przestaje być „na danych, których nie
> oglądaliśmy”).

## Po co — prostym językiem

Na historii nie da się już uczciwie sprawdzić naszych dwóch kandydatów: wybraliśmy je spośród
~30 pomysłów na tych samych latach, a lata sprzed 2022 to inny rynek (decyzja użytkownika).
Dziennik liczy codziennie, jakie pozycje wziąłby portfel, i zapisuje je **zanim** poznamy wynik.
Przez pierwsze 2–3 miesiące sprawdzamy **mechanikę** (czy sygnał liczy się na czas, czy dane
przychodzą kompletne, czy nic nie zmienia się wstecz), a nie to, czy strategia zarabia — na to
2–3 miesiące to za mało (działająca strategia bywa po takim czasie na minusie w ~1 na 3 przypadki).

## Reguły (zamrożone)

| składowa | reguła | instrument | dźwignia (likwidacja izolowana) |
|---|---|---|---|
| trend tygodniowy (TS1, wnioski 70/74) | znak zwrotu 28 dni, waga ∝ 0,40/σ̂ (sufit 3), 7 faz tygodniowych | koszyk top-20 perpetuali po obrocie z ostatnich 30 dni, skład co miesiąc | 2× (LQ1, wniosek 76) |
| premia Coinbase (CP1, wniosek 72) | znak (średnia premii 7 dni − 90 dni) | BTCUSDT | 3× |
| łączenie (SZ1 R1, wniosek 77) | budżet ryzyka: wagi ∝ 1/σ, cel 20 %/rok, sufit mnożnika 2, przeliczane co 7 dni, **bez hamulca** | — | — |

- Koszt: taker 0,05 % + poślizg z `config/settings.yaml` × obrót; funding realny.
- Silnik identyczny z rundami: `backtest/live_journal.py` woła `ts_momentum.portfolio`,
  `run_coinbase_cp1.daily_premium/premium_signal`, `sizing.apply_rules` (bez kopii).
- Silnik startuje 2025-09-01 (rozbieg budżetu ryzyka ≥ 1 rok); **wynik papierowy liczy się od
  2026-09-24** (poprawka 1), kapitał początkowy = 1.
- Dane: `data/raw/live/` (poza gitem), pobierane od nowa przy każdym przebiegu z publicznych API
  Binance (perpetuale, spot BTC 8h) i Coinbase (BTC-USD 1d); tylko świece zamknięte.

## Poprawka 1 (2026-09-24, ok. 10:00 UTC — przed zamknięciem dnia, wynik nieznany)

Decyzja użytkownika: „dziennik niech działa już dzisiaj, a nie od jutra”. Start wyniku papierowego
przesunięty z 2026-09-25 na **2026-09-24**. Uczciwość zapisu: pozycje na 24.09 zostały policzone
z danych do zamknięcia 23.09 i zapisane w `sygnaly.csv` o 09:46 UTC 24.09 — przed poznaniem wyniku
dnia; sygnał nie zależy od cen z 24.09. Zastrzeżenie tylko dla pierwszego dnia: wynik liczony od
zamknięcia 23.09 (00:00 UTC), a realne wejście byłoby możliwe dopiero ok. 09:46 UTC — w odczycie
dzień 24.09 pokazywany osobno.

## Poprawka 2 (2026-09-24, ok. 11:40 UTC — przed pierwszym wynikiem)

Runda RU1 wykryła, że backtest SZ1 liczono na obciętym uniwersum (287 z 685 kontraktów). Dziennik
od początku ma pełne dane, więc **reguły się nie zmieniają**. Progi liczone tą samą, zapisaną z góry
regułą (ostrzeżenie = największe obsunięcie R1 w historii, STOP = 1,5 × to) z poprawionego backtestu:
**ostrzeżenie 18,4 % (było 17,7 %), STOP 27,6 % (było 26,5 %)**.

## Poprawka 3 (2026-09-24, ok. 17:00 UTC — X1 osobno, przed pierwszym wynikiem X1)

Decyzja użytkownika (2026-09-24, po audycie AU1): **X1 jako osobna reguła papierowa**, poza portfelem R1.
Reguły trendu i premii Coinbase oraz portfel R1 — **bez zmian**.

| reguła | sygnał i skład | kapitał | start wyniku | progi |
|---|---|---|---|---|
| X1 — momentum przekrojowe (wnioski 64, 68, 89) | koszyk top-20 jak w trendzie; zwrot 28 dni; long 5 najmocniejszych, short 5 najsłabszych; trzymanie 7 dni; **7 faz** (siedem kopii startujących w kolejne dni tygodnia, każda z 1/7 kapitału) | 1 = 0,5 long + 0,5 short, wagi równe w nodze, bez dźwigni i bez likwidacji (jak w backteście) | **2026-09-25** | ostrzeżenie **55,0 %**, STOP **82,5 %** |

- Dlaczego 7 faz: w wersji z jednym dniem wynik zależał od dnia tygodnia (poniedziałek +41,7 %/rok,
  pozostałe dni od −1 do +22 %; runda X1F). Średnia 7 faz na historii: +9,5 %/rok, t 0,61 — słaby ślad.
- Dlaczego start 25.09, a nie 24.09: reguła zapisana ok. 17:00 UTC 24.09, czyli w trakcie dnia; pierwszy
  cały dzień ogłoszony przed wynikiem to 25.09.
- Progi tą samą regułą co R1: ostrzeżenie = największe obsunięcie średniej 7 faz w historii 2021–2026
  (55,0 %, 04.2025 → 03.2026), STOP = 1,5 × (82,5 %). Decyzja przy STOP należy do użytkownika.
- Silnik: `xs_momentum.long_short_returns` (ten sam co w rundach X1/X1F), `live_journal.x1_component`.
- Zapis: `x1_sygnaly.csv` (nogi ostatniego formowania każdej fazy, wagi ±0,5/5/7), `x1_wyniki.csv`
  (zwrot, kapitał, obsunięcie) — append-only jak reszta; linia X1 w `przebiegi.log`.

## Poprawka 4 (2026-09-24, ok. 17:00 UTC — przed pierwszym wynikiem): monety z nazwą spoza ASCII

Sprawdzian X1 (dziennik vs backtest, 258 dni) wykrył, że filtr nazw symboli `[A-Z0-9]{1,40}USDT`
(przegląd bezpieczeństwa) po cichu odrzucał kontrakty z nazwą w innym alfabecie — `币安人生USDT` był
w koszyku top-20 w 2026-05. Reguła mówi „top-20 po obrocie”, więc to usterka wykonania, nie reguła.
Filtr dopuszcza teraz litery spoza ASCII (`(?:[A-Z0-9]|(?![\x00-\x7f])\w){1,40}USDT`); nadal odrzuca
kropki, ukośniki, dwukropki, spacje, znaki sterujące i małe litery ASCII (test
`test_symbol_names_are_safe_for_file_paths`). Wynik papierowy nie miał jeszcze żadnego wiersza.

## Poprawka 5 (2026-09-24, wieczór — przed pierwszym wynikiem): zapis wyników do gita

Decyzja użytkownika przy przenosinach pracy na serwer: „Tak, auto-commit i push”. Do tej pory automat
niczego nie commitował, więc wyniki leżały tylko na dysku komputera. Teraz po każdym udanym przebiegu
pliki dziennika trafiają do gita (szczegóły w „Codziennie”). Reguły handlu i liczenia — bez zmian.

## Przeniesienie na serwer (2026-09-24, decyzja użytkownika: „tak, przenosimy dziennik”)

Reguły, kod i pliki — bez zmian; zmienia się tylko maszyna (serwer Linux w Polsce działa całą dobę).
Opis commita zawiera nazwę maszyny („Dziennik: przebieg RRRR-MM-DD (host)”), więc `git log --grep='^Dziennik: przebieg'`
pokazuje, gdzie dziennik faktycznie liczy. **Nigdy w dwóch miejscach naraz.**

**Przekazanie jest automatyczne (decyzja użytkownika: „praca dzieje się już na serwerze”):** komputer liczy
dalej jako zabezpieczenie, dopóki serwer nic nie zapisał. Przed każdym przebiegiem `uruchom.bat` woła
`dziennik/przejete.sh`: jeśli w ostatnich 3 dniach na `origin/master` jest zapis dziennika z nazwą INNEJ
maszyny, komputer wyłącza swoje zadanie (`schtasks /change /disable`) i nie liczy
(„===== dziennik przejęty przez inną maszynę” w `ostatni_wydruk.txt` klonu dziennika). Testy:
`tests/test_zapis_dziennika.py`.

Na serwerze (jednorazowo; kopia `~/alpha-dziennik` z `setup_serwer.sh` i dostępem SSH do GitHuba — gotowe
2026-09-24): `crontab -e` → `30 2 * * * bash $HOME/alpha-dziennik/dziennik/uruchom.sh`. Pierwszej nocy
mogą policzyć obie maszyny naraz (wygra pierwszy push, drugi zostawi commit lokalnie — dane te same);
od następnej nocy liczy tylko serwer. Kontrola: `git log -1 --format='%cs %s' --grep='^Dziennik: przebieg'` —
w nawiasie nazwa serwera. Powrót na komputer: usunąć wpis crona i `schtasks /change /tn "CLAS5 dziennik" /enable`.

## Codziennie

```
PYTHONUTF8=1 py -m backtest.live_journal
```

Najlepiej zaraz po zamknięciu dnia UTC (od 02:00 czasu polskiego latem, od 01:00 zimą); pobranie trwa ~10 min.
Wydruk mówi: mnożniki R1, wynik od startu, obsunięcie i status progów, ekspozycję i depozyt każdej
składowej oraz zlecenia fazy formowanej dziś (kierunek i nominał jako % kapitału).

**Automat (Harmonogram zadań Windows, zadanie „CLAS5 dziennik”):** codziennie 02:30 czasu lokalnego
uruchamia `dziennik/uruchom.bat` w **osobnym klonie `C:\Users\pitge\GIT\alpha-dziennik`** (zawsze
`master`; nikt w nim nie pracuje — od 2026-09-24 wieczór, po przeglądzie). Kolejno:
1. aktualizacja kodu: `git pull --rebase --no-autostash origin master` (nieudana → przebieg na dotychczasowym kodzie);
2. przebieg z **ponowieniami w pliku startowym: 3 próby co 30 min** — akcja `conhost.exe --headless`
   (bez okna) zawsze zwraca Harmonogramowi kod 0, więc ponowienia Harmonogramu nie działają;
3. **zapis do gita (poprawka 5):** `dziennik/zapisz_do_gita.sh` (Git Bash) commituje wyłącznie
   `dziennik/*.csv` i `przebiegi.log` i wypycha na `master`; nie chowa niczyich zmian, nie wypycha cudzej
   pracy, przy konflikcie przerywa rebase i zostawia commit lokalnie (testy `tests/test_zapis_dziennika.py`).
Wydruk i każdy wynik zapisu („===== zapis do gita: …”) → `dziennik/ostatni_wydruk.txt` klonu dziennika.
Ustawienia zadania: start przy najbliższej okazji po przegapionym terminie, budzenie komputera, praca na
baterii, limit 3 h, jedna instancja naraz. Przebieg jest idempotentny — ponowienie tego samego dnia nic nie dubluje.
- **Czy zapis działa — sprawdzenie z dowolnej maszyny:** `git log -1 --format=%cs --grep='^Dziennik: przebieg'` po
  `git pull`. Data starsza niż 2 dni = dziennik nie zapisuje (komputer wyłączony, wygasłe logowanie do GitHuba,
  konflikt) — zajrzyj do `ostatni_wydruk.txt` w klonie dziennika.
- **Pierwszy próbny start (24.09, 18:36)** otwierał czarne okno konsoli i skończył się po minucie kodem
  0xC000013A (okno zamknięte / Ctrl+C) — stąd akcja bez okna.
- **Logowanie:** zadanie działa, gdy użytkownik jest zalogowany (także przy zablokowanym ekranie). Tryb
  „bez logowania” (S4U) **odcina zapisane hasła** (Menedżer poświadczeń), więc push do GitHuba by nie działał —
  nie włączać przy zapisie do gita.
- **Dzień przegapiony w całości** (komputer wyłączony przez dobę) zostaje pusty w `sygnaly.csv` — sygnału nie
  dopisuje się po fakcie; liczy się do kryterium kompletności (≥ 95 % dni).
- Sprawdzenie zadania: `Get-ScheduledTaskInfo -TaskName "CLAS5 dziennik"`; wyłączenie:
  `schtasks /delete /tn "CLAS5 dziennik" /f`.
- **Dziennik działa tylko w jednym miejscu naraz.** Przeniesienie na serwer (decyzja użytkownika): wyłączyć
  zadanie na komputerze, na serwerze osobny klon `~/alpha-dziennik` (`bash tools/setup_serwer.sh`), cron
  `30 2 * * * bash $HOME/alpha-dziennik/dziennik/uruchom.sh` (02:30 czasu serwera; ponowienia i blokada
  jednej instancji są w skrypcie).
- Pliki dziennika zapisuje wyłącznie automat — w pracy badawczej ich nie edytujemy.

## Co zapisujemy (append-only, w gicie)

- `sygnaly.csv` — pozycje ogłoszone na dzień po `as_of` (ostatnia zamknięta świeca): składowa,
  faza, symbol, znak, waga, mnożnik, ekspozycja, depozyt. Raz zapisane — nigdy nie zmieniane.
- `wyniki.csv` — dzienny wynik papierowy: zwroty składowych, mnożniki, zwrot portfela, kapitał,
  obsunięcie. Istniejących wierszy przebieg nie zmienia; różnica przy przeliczeniu → „HISTORIA
  ZMIENIONA” w wydruku i w logu.
- `przebiegi.log` — czas przebiegu, ostatnia świeca każdego źródła, liczba dopisanych wierszy,
  status progów.

## Progi (zapisane z góry)

- **OSTRZEŻENIE:** obsunięcie ≥ **18,4 %** (największe obsunięcie R1 w historii 2021–2026, SZ1 po RU1).
- **STOP:** obsunięcie ≥ **27,6 %** (1,5 × powyższe) — dziennik się nie wyłącza sam; decyzja
  o przerwaniu należy do użytkownika, a sygnał STOP trafia do raportu.

## Odczyt po ~3 miesiącach (ok. 2026-12-25) — kryteria mechaniki

1. **Kompletność:** sygnał policzony w ≥ 95 % dni (liczone z `przebiegi.log`).
2. **Spójność:** 0 niewyjaśnionych przypadków „HISTORIA ZMIENIONA”.
3. **Terminowość:** dane z poprzedniego dnia dostępne przy przebiegu w ≥ 95 % dni.
4. **Zgodność z założeniami SZ1:** depozyt w medianie 15–35 % kapitału, mnożniki w granicach sufitu.
5. **Wynik (opisowo, bez werdyktu):** zwrot z przedziałem, dopisany do wspólnego rachunku „poza
   próbą” razem z CP1P i TP1. Nie jest testem przewagi.

## Sprawdzian przed startem (2026-09-24)

- **Zgodność z backtestem** na wspólnym okresie 2025-10-15 → 2026-06-29 (258 dni), dane świeże vs
  zamrożone cache rund: premia Coinbase — korelacja dzienna **1,0000**, suma +69,6 % vs +69,2 %;
  trend — korelacja **0,981**, suma +10,5 % vs +12,8 %. **Sprostowanie (RU1):** różnica brała się
  głównie z OBCIĘTEGO uniwersum backtestu, nie z monet wycofanych — wobec pełnego uniwersum
  korelacja **0,9990**, suma +10,5 % vs +11,8 %. Skrypt: sprawdzenie jednorazowe w sesji, liczby tutaj.
- **Idempotencja:** drugi przebieg tego samego dnia dopisał 0 wierszy, 0 zmian historii.
- **Przegląd bezpieczeństwa** (`security-review`): brak podatności z realną drogą ataku; wdrożona
  jedna sugestia — nazwa symbolu z odpowiedzi giełdy musi pasować do `[A-Z0-9]{1,40}USDT`, zanim
  trafi do nazwy pliku (test `test_symbol_names_are_safe_for_file_paths`).
- **Błąd znaleziony i poprawiony przed startem:** plik `coinbase_BTC-USD_1d.parquet` był wczytywany
  jak kolejna „moneta” (bez wpływu na pozycje — brak obrotu, poza koszykiem), a świeca Coinbase
  z bieżącego, niezamkniętego dnia trafiała do danych. Teraz: tylko pliki perpetuali i tylko
  zamknięte dni (test `test_coinbase_file_is_not_a_symbol`).
- Pobranie: świece wszystkich ~520 perpetuali, funding tylko dla członków koszyka od 2025-09
  (~75 monet) + BTC — ~10 min.

- **Przegląd kodu** (`engineering:code-review`): **Approve** — silnik bez kopii, zapis tylko dopisuje,
  zmiana historii wykrywana; poprawka: dzień `as_of` liczony z ostatniej świecy BTC, nie z dowolnej monety.

## Znane przybliżenia

- Wyświetlane pozycje to wagi z dnia formowania każdej fazy — bez dryfu cen w tygodniu i bez
  likwidacji w trakcie tygodnia. **Wynik** liczy silnik z dryfem i likwidacjami (jak w backteście).
- Uniwersum na żywo to aktywne perpetuale: moneta wycofana w trakcie miesiąca znika z danych
  (w backteście zostawała do końca notowań).
- Wynik zakłada wykonanie po cenie zamknięcia dnia; realne zlecenie złożone kilka godzin później
  będzie miało inną cenę — to jeden z celów sprawdzianu mechaniki.
- **X1 bez likwidacji** (jak w backteście): nominał = kapitał, strata na jednej monecie nieograniczona
  depozytem. Przy dźwigni izolowanej 3× skok monety w nodze short o +33 % kończy się likwidacją, więc
  realna strata byłaby MNIEJSZA niż papierowa (np. MYX 7–8.09.2025: −44 pkt w średniej 7 faz).
- **Skład koszyka a monety wycofane:** dziennik liczy rozbieg z aktywnych dziś kontraktów, więc moneta
  wycofana później znika z historii (X1F: 2 z 3 różnic składu na 258 dniach — IPUSDT, TONUSDT). X1 jest
  na to wrażliwszy niż trend: trzy zamiany po jednej monecie przesunęły sumę o ~10 pkt w 258 dniach.
