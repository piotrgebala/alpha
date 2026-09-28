# Dziennik na żywo (papierowo) — trend tygodniowy + premia Coinbase

> **STATUS: DZIAŁA od 2026-09-24 (poprawka 1: start przesunięty z 25.09 na 24.09).** Reguły poniżej są zamrożone —
> każda zmiana = nowy dziennik od zera (inaczej wynik przestaje być „na danych, których nie
> oglądaliśmy”).
> Osobno, poza portfelem R1: **X1** (poprawka 3, od 2026-09-25, `x1_sygnaly.csv` / `x1_wyniki.csv`) i **carry COIN-M
> do weryfikacji** (poprawka 12, od 2026-09-29, tylko zapis `carry_wyniki.csv`).

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

## Poprawka 6 (2026-09-25 — AU3): naprawa kanonicznego N_eff, bez wpływu na dziennik

Decyzja użytkownika: „tak” (naprawa w jednym miejscu + audyt AU3). `agents/labeling.py::effective_sample_size`
przy mianowniku `1 + 2Σρ ≤ 0` zwraca teraz N_eff = n zamiast liczby ujemnej. Dziennik importuje ten moduł
tylko pośrednio (`run_coinbase_cp1` → `carry_hedged`) i **nie liczy N_eff** — sygnały, wyniki i progi
bez zmian. Wpis dla porządku (CLAUDE.md: zmiana modułu importowanego przez dziennik = decyzja + poprawka).

## Poprawka 7 (2026-09-25 — etykieta stanu rynku, tylko zapis)

Decyzja użytkownika: „Zgoda” (po KR1, wniosek 95: dywersyfikacja zamiast przełączania strategii po reżimie).
Nowy plik `stan_rynku.csv` (append-only, jeden wiersz na dzień od 2026-09-24): zamknięcia BTC ≤ d →
`btc_vol30` (zmienność 30 dni, roczna), `vol_stan` (tercyl: niska < 42,8 % ≤ srednia < 60,14 % ≤ wysoka —
progi ZAMROŻONE z historii 2021-01-01 → 2026-06-30), `btc_r90` (zwrot 90 dni), `trend90` (jego znak).
**Nie wpływa na żadną pozycję ani wynik** — służy wyłącznie do odczytu po 6–12 miesiącach, który składnik
radzi sobie w jakich warunkach (dane z przyszłości, bez zaglądania w przyszłość). Błąd liczenia etykiety
nie zatrzymuje dziennika (zapis „stan rynku BŁĄD …” w `przebiegi.log`). Próba na kopii dziennika
2026-09-25: +1 wiersz (24.09: średnia, trend +1), istniejące pliki bez zmian.

## Poprawka 8 (2026-09-25 — etykieta Fear & Greed, tylko zapis)

Decyzja użytkownika 2026-09-25: „poprawka 8 tak” (STATUS ETAP 5, propozycja 8). Kontekst: F&G zmierzony
dwukrotnie na BTC 4h (G1, SW) nie daje przewagi, a tygodniowo jest niemierzalny — zostaje WYŁĄCZNIE jako
etykieta do odczytu po 6–12 miesiącach („strach a nogi dziennika”), obok `stan_rynku.csv` z poprawki 7.
Nowy plik `fng.csv` (append-only, jeden wiersz na dzień od 2026-09-24): `fng` (0–100) i `fng_etykieta`
(Extreme Fear / Fear / Neutral / Greed / Extreme Greed) **wprost z publikacji alternative.me** — bez własnych
progów, więc nie ma czego stroić. Pobranie: `data/fetch_live.py::fetch_fng_safe` (pełna historia przez
`fetch_external.fetch_fng`, to samo publiczne źródło bez klucza, które zasiliło P3/G1; tylko https, adres
stały w kodzie) do `data/raw/live/alternative_fng_1d.parquet`; zapis: `live_journal.run` → `fng_rows`
(dni ≥ 2026-09-24 i ≤ dziś) → `append_rows`. **Nie wpływa na żadną pozycję ani wynik.** Odporność:
awaria źródła nie zatrzymuje pobierania ani dziennika (`F&G BŁĄD …` / `F&G brak pliku` w `przebiegi.log`),
brakujące dni uzupełniają się przy następnym udanym przebiegu z pełnej historii, a rewizja już zapisanej
wartości to „historia zmieniona” (stary zapis zostaje) — jak w pozostałych plikach. Testy:
`tests/test_live_journal.py` (filtr dat i zaokrąglenie, uzupełnianie po przerwie, brak pliku, błąd sieci).
Próba na kopii dziennika 2026-09-25 (prawdziwe pobranie: 3 155 dni historii, ostatni 2026-09-25 = 71 Greed):
nowe tylko `fng.csv` (+2 wiersze: 24.09 i 25.09, oba 71 Greed) i linia w `przebiegi.log` („F&G +2”);
`sygnaly.csv`, `wyniki.csv`, `x1_*.csv` bez zmian. Przegląd bezpieczeństwa (skill `security-review`, nowe
połączenie sieciowe w dzienniku): 0 podatności; jedna uwaga niska (tekst klasy z serwera wprost do CSV) →
do pliku trafia tylko pięć znanych klas, inna = głośny błąd w logu, zapis pominięty. Przegląd kodu
(`engineering:code-review`): Approve — zmiana ograniczona do etykiety, wszystkie błędy zatrzymują się w logu.

## Poprawka 9 (2026-09-26 — lista transakcji, tylko zapis)

Decyzja użytkownika 2026-09-26: „Dodaj jeszcze do dziennika listę zawieranych transakcji — data wejścia, symbol, cena wejścia
i wyjścia, wielkość pozycji, data zamknięcia — i uaktualnij bieżący stan”.

**Co jest transakcją.** Każda składowa (trend, premia Coinbase, X1) to 7 faz. Faza co 7 dni kupuje swój koszyk po zamknięciu
dnia formowania i trzyma go do zamknięcia dnia kolejnego formowania tej fazy — albo krócej, gdy pozycja trafi w likwidację
izolowaną (trend 2×, premia 3×; X1 bez dźwigni i bez likwidacji). **Jeden wiersz = jedna moneta w jednej fazie przez jeden
tydzień.** Ta sama moneta w tym samym kierunku w następnym tygodniu to nowy wiersz (w praktyce zmiana wielkości, nie nowe
zlecenie). Pozycja netto w monecie = suma jej otwartych wierszy.

**Pliki:** `transakcje.csv` — transakcje ZAMKNIĘTE, dopisywane i nigdy nie zmieniane (klucz: składowa + faza + data wejścia +
symbol; inny wynik przeliczenia = „historia zmieniona”, stary zapis zostaje); `transakcje_otwarte.csv` — pozycje otwarte na
`as_of`, **nadpisywany** przy każdym przebiegu (widok bieżący, nie historia).

**Kolumny:** `skladowa` (trend / premia_coinbase / x1), `faza` (0–6), `symbol`, `kierunek` (long/short), `data_wejscia`
(zamknięcie świecy dziennej tej daty = cena wejścia `cena_wejscia`), `data_wyjscia` + `cena_wyjscia` (zamknięcie dnia kolejnego
formowania; przy likwidacji — dzień i cena likwidacji: wejście × (1 ∓ (1/dźwignia − 0,01))), `powod_wyjscia` (rotacja /
likwidacja), `dzwignia`, `waga` (część kapitału składowej, ze znakiem), `k` (mnożnik R1 z pierwszego dnia trzymania; X1: 1),
`wielkosc_proc_kapitalu` = |waga × k| w % kapitału portfela (trend i premia: portfel R1; X1: własny kapitał X1),
`depozyt_proc_kapitalu` = wielkość / dźwignia, `zwrot_pozycji_proc` (zmiana ceny z punktu widzenia pozycji; likwidacja =
−100 % / dźwignia, cały depozyt), `wynik_cenowy_proc_kapitalu` = wielkość × zwrot, `przed_startem` (pozycja otwarta przed
pierwszym dniem dziennika — odziedziczona z rozbiegu silnika). W pliku otwartych: `cena_biezaca` (zamknięcie `as_of`),
`planowane_wyjscie` (data wejścia + 7 dni), `zwrot_biezacy_proc`.

**Zakres:** pozycje, które żyły w okresie wyniku dziennika (wyjście ≥ 2026-09-24; X1 ≥ 2026-09-25), oraz wszystkie otwarte.
**Czego lista nie liczy:** fundingu i kosztów (są w `wyniki.csv` / `x1_wyniki.csv` — tam jest wynik portfela). Mnożnik k może
zmienić się w trakcie tygodnia, a X1 w silniku codziennie wyrównuje wartość nóg — suma `wynik_cenowy_proc_kapitalu` jest więc
bliska wynikowi, ale nie co do grosza. Ceny = dzienne zamknięcia Binance (to „cena odniesienia” dziennika wykonania, skill
`zarzadzanie-pozycja` E4). `sygnaly.csv` pokazuje pozycję zlikwidowaną do końca tygodnia fazy; lista transakcji — jako zamkniętą.

**Zgodność z silnikiem (testy `tests/test_live_journal.py`):** wynik każdej fazy trendu z silnika (z likwidacjami) =
Σ |waga × 7| × zwrot pozycji co do 1e-9; ręczny przykład z krachem (likwidacja long 2×) i rotacją short; otwarte pozycje =
pozycje z `sygnaly.csv` i `x1_sygnaly.csv` (poza zlikwidowanymi); transakcje zamknięte liczone dzień później mają te same
liczby; przebieg dopisuje zamknięte raz (powtórka: +0, bez „historia zmieniona”).

**Próba na kopii dziennika 2026-09-26** (dane z przebiegu 02:30, `as_of` 2026-09-25): nowe tylko `transakcje.csv` (52
zamknięte: trend 40, premia 2, X1 10 — wszystkie odziedziczone z rozbiegu; 1 likwidacja: SUI short, faza 4, 18.09 → 25.09,
maksimum 1,495× ceny wejścia przy progu 1,49×, strata = depozyt 0,13 % kapitału, uwzględniona już w wyniku 25.09)
i `transakcje_otwarte.csv` (216 otwartych: trend 139, premia 7, X1 70); pozostałe pliki bez zmian, historia zmieniona 0.
Lista nie wpływa na pozycje ani wynik; jej błąd nie zatrzymuje dziennika („transakcje BŁĄD …” w `przebiegi.log`).

## Poprawka 10 (2026-09-26 — opis i założenia każdej aktywnej strategii, tylko zapis)

Decyzja użytkownika 2026-09-26: „podaj dokładne założenia każdej strategii, dopisz je do raportu i niech każda aktywna
strategia ma zawsze opis”. **Jedno źródło:** `backtest/journal_strategies.py` — opisy TS1, CP1, R1 i X1 z liczbami brane ze
stałych silników (`ts_momentum`, `xs_momentum`, `run_coinbase_cp1`, `rebalance_premium`, domyślne parametry
`sizing.apply_rules`, koszty z `config/settings.yaml`) i z parametrów dziennika — opis nie może rozjechać się z kodem.
Z niego powstają:
- blok **„STRATEGIE AKTYWNE”** w każdym raporcie przebiegu (`ostatni_wydruk.txt`) — nazwa i jednozdaniowy opis każdej strategii;
- **`strategie.csv`** — pełne założenia, stan dowodów, od kiedy i gdzie jest wynik; nadpisywany w każdym przebiegu
  (automat go commituje razem z resztą plików dziennika), więc opis zawsze leży obok danych;
- **`STRATEGIE.md`** — ten sam opis do czytania (`PYTHONUTF8=1 py -m backtest.journal_strategies > dziennik/STRATEGIE.md`;
  plik generowany, nie edytować ręcznie).

**Zawsze:** test `tests/test_live_journal.py` sprawdza, że każda składowa pojawiająca się w `sygnaly.csv` i liście transakcji
ma opis, że opis zmienia się razem ze stałą silnika (np. okno sygnału), że `STRATEGIE.md` jest aktualny względem kodu
i że przebieg zapisuje `strategie.csv` oraz drukuje blok opisów (log: „opisy strategii 4”). Nowa strategia bez wpisu
w `journal_strategies.py` = czerwony test. Moduł jest odtąd częścią kodu dziennika — jego zmiana wymaga poprawki.
Próba na kopii dziennika 2026-09-26: nowe tylko `strategie.csv` (4 wiersze) i linia w `przebiegi.log`; reszta bez zmian,
historia zmieniona 0. Nie wpływa na pozycje ani wynik; błąd opisu nie zatrzymuje dziennika.

## Poprawka 11 (2026-09-27, decyzja użytkownika — rozbicie zwrotu, fazy, skład koszyka)

Decyzja użytkownika 2026-09-27: „wykonaj wszystkie” propozycje z przeglądu kandydatów (`docs/rag/11_przeglad_kandydatow_2026-09-27.md`,
sekcje 2 i 6, krok 3). **Trzy nowe pliki TYLKO DO ZAPISU.** Pozycje, mnożniki, wynik i progi — bez zmian.

**Po co.** Dziennik zapisywał dotąd tylko wynik netto każdej składowej. Silnik przy każdym przebiegu ma w pamięci więcej:
ile dała sama cena, ile funding (opłata co 8 h między longami i shortami), ile koszt transakcji i jaki był obrót (ile
kapitału wymieniono). `data/raw/live` jest nadpisywany co noc, więc tego, co dziennik faktycznie policzył, nie da się
później odtworzyć. Teraz zapisujemy to od razu.

**Pliki i kolumny** (append-only jak `wyniki.csv`: istniejących wierszy przebieg nie zmienia; inna wartość przy
przeliczeniu = „historia zmieniona”, stary zapis zostaje):
- **`rozbicie.csv`** — klucz `date` + `skladowa` (`trend`, `coinbase`, `x1`); zakres dat jak w wynikach (trend i premia od
  2026-09-24, X1 od 2026-09-25). Kolumny: `cena` (zwrot cenowy brutto; przy trendzie i premii zawiera też stratę
  z likwidacji), `funding`, `koszt` (**ujemny** — to wkład kosztu do zwrotu, = opłata × obrót), `netto`, `obrot` (w kapitale
  składowej, średnia 7 faz), `likwidacje` (liczba pozycji zlikwidowanych tego dnia we wszystkich fazach; X1: 0 z konstrukcji),
  dla X1 także `r_long` i `r_short` (zwrot nogi long i short na jednostkę nogi; `cena` X1 = 0,5 · (r_long − r_short)).
  Wszystko przy k = 1, czyli w jednostkach kapitału składowej — tak jak `r_trend` / `r_coinbase` w `wyniki.csv`.
  **Zasada:** `cena + funding + koszt = netto` i `netto` = `r_trend` / `r_coinbase` (`wyniki.csv`) albo `r_x1`
  (`x1_wyniki.csv`), oba do 1e-9 — sprawdzane w przebiegu PRZED zapisem; niezgodność = błąd w logu i brak zapisu
  tej składowej. **Dokładnie:** przebieg porównuje netto z wynikiem, który sam właśnie policzył (przy nowym dniu to ta sama
  liczba, którą dopisuje do `wyniki.csv`). Równość z zapisanym plikiem jest więc pewna, gdy log mówi „historia zmieniona: 0”;
  przy odczycie po 3 miesiącach porównujemy `rozbicie.csv` z `wyniki.csv` / `x1_wyniki.csv` wprost, dzień po dniu.
- **`fazy.csv`** — klucz `date` + `skladowa` + `faza` (0–6): `netto` jednej fazy (fazy = 7 kopii strategii startujących
  w kolejne dni tygodnia, każda z 1/7 kapitału). **Zasada:** średnia 7 faz = netto składowej (1e-9), sprawdzane przed zapisem.
- **`koszyk.csv`** — klucz `miesiac` + `symbol`, od miesiąca startu dziennika (2026-09): `pozycja` w rankingu obrotu 1–50
  (ta sama miara co skład koszyka: średni obrót z 30 dni przed początkiem miesiąca, co najmniej 30 dni notowań; remis →
  alfabetycznie), `sredni_obrot_30d` (USDT, zaokrąglony do 1 USDT), `czlonek_top20` (moneta w koszyku silnika), `funding_pobrany`
  (czy dane przebiegu mają choć jedno rozliczenie fundingu tej monety w tym 30-dniowym oknie). Skład top-20 jest **ten sam
  co do bajtu** co `rebalance_premium.monthly_members` (kontrola w przebiegu + testy). `funding_pobrany` opisuje stan pobrania
  w dniu zapisu (funding pobieramy tylko dla członków koszyka), więc jego późniejsza zmiana NIE liczy się jako „historia
  zmieniona”; pozostałe kolumny tak. **`funding_pobrany` = False znaczy „fundingu tej monety nie pobraliśmy”, a nie „moneta
  nie ma fundingu”** (każdy perpetual ma funding; np. w 2026-09 miejsce 21 BLESSUSDT ma False, miejsce 22 WLDUSDT True —
  z 50 monet True ma 35).

**Kod.** Nowy ranking `rebalance_premium.monthly_ranking` (obok `monthly_members`, która zostaje bez zmian — silnik dziennika
jej nie zmienia). `live_journal`: `components` / `positions` / `x1_component` / `run_x1` dostały opcjonalny argument, który
tylko zbiera ramki silnika z tego samego przeliczenia (domyślnie nic nie robi); nowe funkcje `ts_breakdown`, `x1_breakdown`,
`phase_rows`, `check_breakdown`, `check_phases`, `basket_rows`. W `przebiegi.log` przed „historia zmieniona” doszły pola
`rozbicie +N | fazy +N | koszyk +N`; błąd liczenia albo zapisu któregokolwiek pliku to „BŁĄD <typ>” w tym polu, a dziennik
idzie dalej (jak opisy strategii w poprawce 10). Wydruk ma nową linię „Rozbicie zwrotu, fazy, koszyk (poprawka 11…)”, a pod
nią po jednej linii na każdy błąd z pełnym komunikatem („BŁĄD koszyk: ValueError: …”) — log zostaje krótki, komunikat jest
w `ostatni_wydruk.txt`. Rozbicie i fazy liczy się **osobno dla każdej składowej**: błąd samego X1 nie blokuje zapisu trendu
i premii, a pole w logu wygląda wtedy tak: „rozbicie +6 (x1 BŁĄD ValueError)”. Brakujące dni dopisuje następny udany
przebieg (liczy całą historię od startu i dopisuje brakujące klucze). Takie wiersze trafiają na koniec pliku, więc **plików
nie czyta się „po kolei” — zawsze sortuje się je po kluczu** (`date`, `skladowa` [, `faza`]).
Parser strony (`tools/strona_dziennika.py`) czyta nowe pola bez zmian (test z nowym formatem).

**Testy** (`tests/test_live_journal.py`, `tests/test_rebalance_premium.py`, `tests/test_strona_dziennika.py`): suma składników
= netto = wynik dziennika; średnia faz = wynik; trend z rozbicia = drugie, niezależne wywołanie silnika (cena, funding, koszt,
likwidacje, każda faza); kontrole odrzucają każde zaburzenie > 1e-9 (test właściwości w `hypothesis`), brak dnia i brak fazy;
top-20 rankingu = `monthly_members` (test właściwości z remisami, dziurami i stablecoinami + prawdziwe panele: `data/raw/live`
dziennika od 2025-09 i archiwum `universe_full` 2021-02 → 2026-06, 65 miesięcy, co do bajtu); powtórka dopisuje 0 wierszy;
ręcznie zmieniony wiersz → „historia zmieniona: 1”, stary zapis zostaje; błąd rozbicia i koszyka → „BŁĄD RuntimeError”
w logu, a **wszystkie pozostałe pliki bajt w bajt takie same jak w przebiegu bez błędu**; komunikat błędu w wydruku,
nie w logu; błąd X1 → rozbicie tylko dla trendu i premii; błąd samego rozbicia X1 → trend i premia zapisane, w logu
„(x1 BŁĄD ValueError)”, a następny udany przebieg dopisuje X1 (zbiór wierszy jak bez błędu); `funding_pobrany` liczone tylko
z 30 dni przed początkiem miesiąca (funding usunięty wyłącznie w tym oknie → False).

**Próba na kopii dziennika 2026-09-27** (kopia `dziennik/` z klonu dziennika, dane `data/raw/live` z przebiegu 02:30,
`as_of` 2026-09-26, bez pobierania): nowe tylko `rozbicie.csv` (+8: trend 3, premia 3, X1 2), `fazy.csv` (+56 = 8 × 7) i
`koszyk.csv` (+50, miesiąc 2026-09: 20 w koszyku, 35 z fundingiem); w `przebiegi.log` nowa linia „… | rozbicie +8 | fazy +56 |
koszyk +50 | historia zmieniona: 0”. Wszystkie dotychczasowe pliki CSV **bajt w bajt bez zmian**, stare linie logu bez zmian.
Kontrole na prawdziwych danych: |cena + funding + koszt − netto| ≤ 9·10⁻¹⁷, |netto − wyniki.csv / x1_wyniki.csv| = 0,
|średnia faz − wynik| ≤ 5·10⁻¹⁷, top-20 = `monthly_members`. Druga droga: likwidacje w rozbiciu (trend: 1 w dniu 25.09,
2 w dniu 26.09) = likwidacje w `transakcje.csv` według daty wyjścia. Czas przebiegu 5,9 s (nowe pliki: ~0,1 s). Drugi przebieg
na tej samej kopii: „rozbicie +0 | fazy +0 | koszyk +0 | historia zmieniona: 0”. Próbę powtórzono po poprawkach
z przeglądu kodu (izolacja składowych, komunikat błędu w wydruku): te same liczby, czas 5,9 s, parser strony czyta nową linię.

**Co wolno odczytać i kiedy** (zapisane przed jakimkolwiek odczytem):
- **Rozbicie po ~3 miesiącach** (odczyt 25.12): tylko mechanika — czy obrót i koszt zgadzają się z założeniami KO1
  (jednorazowy pomiar kosztów wykonania z 2026-09-25, `runs/2026-09-25_ko1-koszty-wykonania/`; oczekiwany obrót trendu (TS1)
  ≈ 11, premii Coinbase (CP1) ≈ 21 i X1 ≈ 47 kapitałów na rok, czyli koszt w kwartale ≈ 0,2 / 0,4 / 0,8 %). Odchylenie > 30 % = błąd
  mechaniki do wyjaśnienia. **Po ~12 miesiącach:** poziom fundingu (dokładność ±2–3 pp/rok). Rozbicie **nie rozstrzyga**, skąd
  bierze się wynik X1 (cena X1 ma po roku rozrzut ±32 %/rok) — żadna decyzja o regule nie zapada na podstawie nóg X1.
- **Fazy — tylko diagnostyka:** różnica faz ≳ 3–5 % kapitału w tygodniu wskazuje błąd silnika albo jedno zdarzenie w jednej
  monecie. **Nigdy nie wybieramy fazy ani nie zmieniamy wag faz po wyniku** — mierzonym obiektem zostaje średnia 7 faz.
- **Koszyk — rejestr uniwersum:** do sprawdzianu „dane na żywo vs archiwum” (porównanie świec i fundingu pobranych przez
  dziennik z archiwum za te same dni — STATUS, ETAP 5 pkt 3, termin 22.10–05.11) i do odtworzenia, co było w top-50 danego
  miesiąca. Monety wycofane widać tylko od dnia startu, nie wstecz. Miejsca 21–50 nie są strategią (cień TR1 — czyli
  ten sam trend liczony na monetach z miejsc 21–50 — odtwarza się z archiwum; `docs/rag/11_przeglad_kandydatow_2026-09-27.md`).

## Poprawka 12 (2026-09-28, decyzja użytkownika — noga carry COIN-M do weryfikacji, tylko zapis)

Decyzja użytkownika 2026-09-28: „dodajemy do dziennika strategię carry do weryfikacji”. **Nowa noga, osobno i tylko do zapisu:**
jeden nowy plik `carry_wyniki.csv`. Trend, premia Coinbase, portfel R1 i X1 — reguły, pozycje, wynik, progi i dotychczasowe
pliki — **bez zmian**.

**Co i dlaczego.** Carry to zarabianie na opłacie funding (co 8 godzin płacą ją sobie strony kontraktu wieczystego; zwykle
longi płacą shortom). Zmierzyliśmy je w rundach C1 i D1 (wnioski 54, 61–63). 2026-09-23 użytkownik je odpuścił („nie o takie
zwroty mi chodzi”) i kierunek zamknięto bez produktu. Teraz carry wraca, ale **nie jako nowa hipoteza**, tylko do weryfikacji
na żywo: czy to, co policzyliśmy na historii, zgadza się z tym, co giełda rozlicza dzień po dniu.

**Konstrukcja — wiersz COIN-M z rundy D1, bez zmian i bez nowych parametrów (zasada 9).**

| noga | pozycja | kapitał | start wyniku | progi |
|---|---|---|---|---|
| carry COIN-M (D1, wniosek 61) | 1 BTC zabezpieczenia (kupione na spot przy starcie) + short `BTCUSD_PERP` (kontrakt COIN-M rozliczany w bitcoinie, tzw. odwrotny) o nominale równym wartości zabezpieczenia; zawsze w pozycji | 1× (wartość zabezpieczenia), bez dźwigni | **2026-09-29** | brak — noga tylko do zapisu |

- Wartość tej pary w dolarach jest stała, niezależnie od ceny BTC (tożsamość P + N·(1/P − 1/P₀)·P = P₀, sprawdzona w D1 testem
  `hypothesis`). Nie ma więc czego likwidować ani dopłacać, a jedynym wynikiem jest funding.
- Zawsze w pozycji — **bez** wychodzenia, gdy funding jest ujemny (przełączanie po znaku przegrywa z kosztami: C1b, wniosek 55).
- Dzień UTC = rozliczenia o 00:00, 08:00 i 16:00 tego dnia — ta sama konwencja co funding w silniku dziennika (wejście na
  zamknięciu dnia poprzedniego, czyli o 00:00 UTC). Stawka dodatnia — short dostaje, ujemna — płaci.
- **Start 2026-09-29:** pierwszy pełny dzień UTC po zapisaniu tej poprawki (ta sama zasada co start X1 w poprawce 3).
- **Księgowanie dokładnie jak w D1:** te same funkcje z `backtest/carry_product.py` (`floor_to_grid`, `inverse_carry_pnl`) i ten
  sam koszt `CarryCosts(...).switch_cost` z `config/settings.yaml`: **0,19 % nominału** (spot 0,10 % + kontrakt taker 0,05 % +
  poślizg 2 pb na każdej nodze), naliczony **raz, pierwszego dnia**. Wynik = suma stawek, bez procentu składanego (jak w D1).
- **Jedno odstępstwo od D1 (konieczne):** D1 liczył okres zamknięty, więc w ostatnim rozliczeniu doliczał też koszt wyjścia
  (drugie 0,19 %). Noga dziennika jest otwarta: koszt wyjścia siedziałby w ostatnim wierszu i przesuwał się co dzień, a plik jest
  append-only. Dlatego go nie ma. **Wynik liczony jak w D1 za okres od startu do dnia d = `netto_skum` z dnia d − 0,19 %.**
- Kod: `backtest/journal_carry.py` (czyste funkcje), `live_journal.run_carry` (zapis), `data/fetch_live.fetch_coinm_funding_safe`
  (pobieranie), opis w `backtest/journal_strategies.py` (piąta strategia w `strategie.csv` i `STRATEGIE.md`, skrót D1).

**Dane.** Historia funding COIN-M z Binance (`dapi/v1/fundingRate`, publiczna, bez klucza) — ta sama funkcja co w D1
(`fetch_external.fetch_coinm_funding`). Pobierana w każdym przebiegu od startu nogi i nadpisywana (jedno zapytanie; plik rośnie
o 3 rozliczenia dziennie). Dzięki temu późniejsza zmiana stawki po stronie giełdy wyjdzie jako „historia zmieniona”. Plik:
`data/raw/live/binance_cm_funding_BTCUSD_PERP.parquet` (poza gitem). Błąd pobrania nie zatrzymuje dziennika: stary plik zostaje,
a pozostałe nogi liczą się normalnie.

**Plik `carry_wyniki.csv`** — append-only jak `wyniki.csv` (istniejących wierszy przebieg nie zmienia; inna wartość przy
przeliczeniu = „historia zmieniona”, stary zapis zostaje). Jeden wiersz na każdy zamknięty dzień UTC od 2026-09-29. Dzień trafia
do pliku dopiero wtedy, gdy dane mają rozliczenie z dnia następnego — wtedy brak rozliczenia to prawdziwy brak, a nie „jeszcze
nie pobrane”. Kolumny:
- `date` — dzień UTC;
- `rozliczenia` — ile rozliczeń giełda opublikowała tego dnia (oczekiwane 3);
- `komplet` — `True`, gdy są 3 i wszystkie trzy weszły do wyniku. **Dzień z brakiem nie jest pomijany**, tylko oznaczony `False`
  (także dzień bez żadnego rozliczenia: 0 rozliczeń, netto 0). Gdyby giełda zmieniła rytm (np. co 4 h), liczba to pokaże —
  przygotowanie z D1 łączy wtedy rekordy na siatce 8 h;
- `suma_stawek` — funding otrzymany przez short tego dnia, ułamek nominału (0,0001 = 0,01 %); ujemna = zapłacony;
- `koszt` — koszt wejścia, **dodatni** (jak w D1; inaczej niż `koszt` w `rozbicie.csv`), tylko w pierwszym dniu;
- `netto` = `suma_stawek` − `koszt`; `netto_skum` — suma `netto` od startu.

**Log i wydruk.** Na ścieżce bez błędów linia `przebiegi.log` ma **te same pola** co przed tą poprawką — parser strony dziennika
jest wklejony w rutynę Cowork, a nowe pola psuły go przy poprawkach 8–10. Jedyna zmiana w treści: „opisy strategii 5” zamiast 4
(piąty opis, mechanizm poprawki 10). Pole „carry …” dochodzi przed „historia zmieniona” **tylko przy kłopocie**: „carry BŁĄD <typ>”
(błąd liczenia albo zapisu; pełny komunikat w wydruku), „carry brak pliku” (brak danych COIN-M), „carry spóźnione” (ostatni
zamknięty dzień w danych jest wcześniejszy niż dzień dziennika — zwykle nieudane pobranie). Różnice w `carry_wyniki.csv` liczą się
do „historia zmieniona: N”. Wydruk (`ostatni_wydruk.txt`) ma nową linię „Carry COIN-M (poprawka 12 …)”: ostatni dzień, liczba
rozliczeń, suma stawek, netto i netto skumulowane. Carry **nie** trafia do `wyniki.csv`, `rozbicie.csv`, `fazy.csv`, `koszyk.csv`
ani `x1_*` — ich kontrole sumują się do wyników innych nóg; rozbicie carry niesie sam `carry_wyniki.csv`.

**Czego się spodziewać — liczby z D1, bez nowych przeliczeń** (`runs/2026-09-23_d1-produkt-carry/README.md`, Q2 i Q4). Średnia D1
**+9,07 %/rok [5,88; 12,26]** na kapitale 1× (2021 → 2026 H1) jest **zawyżona przez 2021** (+22,2 % w tym jednym roku). Od 2022
rok po roku, obok stopy bonów skarbowych USA 3M (T-bill — praktycznie bezryzykowna lokata w dolarze):

| rok | carry COIN-M 1× | T-bill 3M | nadwyżka |
|---|---|---|---|
| 2022 | +1,8 % | 2,02 % | −0,2 pp |
| 2023 | +7,5 % | 5,07 % | +2,5 pp |
| 2024 | +12,2 % | 4,97 % | +7,2 pp |
| 2025 | +5,1 % | 4,07 % | +1,0 pp |
| 2026 H1 (annualizowane) | +2,1 % | 3,61 % | −1,5 pp |
| **średnia 2022 → 2026 H1** | **+5,7 %** | **3,95 %** | **+1,8 pp** |

To pięć obserwacji rocznych — opis, nie prognoza. Dla decyzji: nawet w dobrym roku carry ledwie wyprzedza lokatę w dolarze,
a w słabym (2022, 2026 H1) jest pod nią; stawka bywa ujemna (w D1 19,6 % rozliczeń).

**Co ta noga weryfikuje — mechanikę, nie przewagę.** Carry to kontraktowy przepływ (longi płacą za dźwignię), nie przewidywanie
ceny. Przewagi się tu nie sprawdza i nie ma progu obalenia (kryterium 5 tej nogi nie dotyczy).
1. **Kompletność rozliczeń:** 3 rozliczenia każdego dnia, bez dziur w datach.
2. **Zgodność zapisu z giełdą:** stawki w pliku = stawki w historii Binance, dzień po dniu.
3. **Brak likwidacji z konstrukcji:** przy 1× z zabezpieczeniem w BTC wartość w dolarach jest stała — noga nie ma depozytu, progu
   likwidacji ani dopłat i w zapisie nie ma zdarzenia, które by ich wymagało. Papier nie ma konta, więc to warunek do sprawdzenia
   na realnym koncie dopiero na szczeblu 4 (tryb izolowany, ziarno kontraktu 100 USD — D1, „Co na minus”).

**Kryterium odczytu po ~3 miesiącach** (razem z odczytem dziennika ok. 2026-12-25; zapisane przed pierwszym wierszem carry):
- **(a) terminowość:** pole „carry …” (spóźnione, brak pliku, BŁĄD) w ≤ 5 % przebiegów od 2026-09-30 (z `przebiegi.log`);
- **(b) kompletność:** `komplet = True` w ≥ 95 % dni od 2026-09-29, każdy dzień z `False` wyjaśniony (brak po stronie giełdy
  czy błąd pobierania). Dla skali: na historii D1 (2 007 dni, 2021-01-01 → 2026-06-30) niepełny był 1 dzień — 30.06.2026,
  brak rozliczenia 08:00 w historii Binance;
- **(c) zgodność z giełdą (druga droga):** przy odczycie jedno ponowne pobranie historii od 2026-09-29 i przeliczenie
  `journal_carry.carry_rows` daje te same wiersze co plik, do 1e-9; każda różnica wyjaśniona (to jednocześnie sprawdzian
  „historia zmieniona” = 0 dla `carry_wyniki.csv`);
- **wynik opisowo, bez werdyktu:** `netto_skum` i ta sama suma przeliczona na rok, obok tabeli powyżej.
Niespełnione (a)–(c) = błąd mechaniki do wyjaśnienia, nie ocena strategii.

**Ścieżka odwrotu.** Revert commita tej poprawki: dziennik wraca do 4 strategii, linia logu do „opisy strategii 4”, pobieranie
COIN-M znika. `carry_wyniki.csv` zostaje w gicie jako historia (danych nie kasujemy).

**Testy** (`tests/test_journal_carry.py`; zmienione oczekiwania w `tests/test_live_journal.py` i nowy format błędu
w `tests/test_strona_dziennika.py`): trzy rozliczenia dziennie sumują się do wiersza; koszt wejścia tylko pierwszego dnia;
dzień zapisany dopiero po rozliczeniu z dnia następnego, a nowy dzień nie zmienia starych wierszy; brakujące rozliczenie i dzień
bez rozliczeń oznaczone, nie pominięte; znaczniki z opóźnieniem 0–7 ms dają to samo co bez niego; zmiana rytmu na 4 h pokazana
w `rozliczenia`; rozliczenia przed startem nie liczą się; netto = wynik D1 (`inverse_carry_pnl` + okno z zamrożonego reportera)
minus koszt wyjścia, co do 1e-15; test właściwości w `hypothesis` (dowolna ścieżka stawek, braków i opóźnień: każdy dzień raz,
netto = suma stawek − jeden koszt wejścia); przebieg dziennika: append-only, powtórka +0, ręcznie zmieniony wiersz → „historia
zmieniona: 1”, stary zapis zostaje; **linia logu bez błędów pasuje dokładnie do formatu sprzed poprawki i jest identyczna
z przebiegiem, w którym carry nie ma nic do zapisania**; błąd carry → „carry BŁĄD RuntimeError” w logu, pozostałe pliki bajt
w bajt jak bez błędu, parser strony czyta linię; brak pliku i spóźnione dane → pole w logu; pobieranie łapie błąd sieci.

**Próba na kopii dziennika 2026-09-28** (kopia `dziennik/` i `data/raw/live` z klonu dziennika po przebiegu 02:30, `as_of`
2026-09-27, bez pobierania; wszystko w katalogu tymczasowym). Ten sam przebieg starym kodem (`master` 0bfeef5) i nowym:
wszystkie dotychczasowe pliki CSV **bajt w bajt** takie same; `strategie.csv` +1 wiersz (carry); linia `przebiegi.log` identyczna
poza czasem przebiegu i „opisy strategii 4” → „5”. Z prawdziwym startem (29.09) noga nie ma jeszcze zamkniętego dnia („dopisane
+0”, bez pola w logu). Ze startem przesuniętym na próbę na 21.09 i historią pobraną z `dapi` tego dnia: 7 dni (21–27.09), każdy
3/3, netto skumulowane −0,1073 % nominału (koszt wejścia 0,19 % jeszcze nieodrobiony). **Druga droga na danych D1**
(cache `binance_cm_funding_BTCUSD_PERP`, 2021-01-01 → 2026-06-30): suma stawek 50,2403 % i netto po koszcie wyjścia 49,8603 %
= liczby D1 (9,07 %/rok), różnica 6·10⁻¹⁵. Czas przebiegu bez zmian (5,9 s).

**Przegląd bezpieczeństwa** (`security-review`, 2026-09-28 — nowe połączenie sieciowe w ścieżce dziennika): brak podatności
z realną drogą ataku. Adres (`https://dapi.binance.com`, tylko https) i symbol są stałymi w kodzie, nie pochodzą z odpowiedzi;
publiczne API bez klucza; odpowiedź czytana tylko jako JSON i zamieniana na liczby (`parse_funding_records` odrzuca rekord bez
pól); nazwa pliku ze stałej; w `carry_wyniki.csv` same liczby i daty; do `przebiegi.log` trafia najwyżej nazwa typu błędu,
a komunikat tylko do wydruku (którego automat nie commituje).

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
2026-09-24): najlepiej raz ręcznie `bash ~/alpha-dziennik/dziennik/uruchom.sh` (zapis „(dantey1)” trafia na
GitHub i komputer nie liczy już ani razu), potem `crontab -e` → `30 2 * * * bash $HOME/alpha-dziennik/dziennik/uruchom.sh`.
Gdyby pierwszej nocy obie maszyny policzyły naraz: `przebiegi.log` łączy wpisy obu (`merge=union`
w `.gitattributes`), a gdy różnią się wiersze CSV, maszyna, która przegrała wyścig, przy następnym starcie
przyjmuje stan z GitHuba i dolicza bieżący dzień (`dziennik/aktualizuj.sh`, tylko gdy różnią się wyłącznie
pliki dziennika). Od następnej nocy liczy tylko serwer. Kontrola: `git log -1 --format='%cs %s'
--grep='^Dziennik: przebieg'` — w nawiasie nazwa serwera. Powrót na komputer: usunąć wpis crona i
`schtasks /change /tn "CLAS5 dziennik" /enable` (komputer policzy dopiero, gdy od ostatniego zapisu serwera
miną 3 dni — wcześniej sam się wyłączy).
- `uruchom.bat` działa z kopii w `%TEMP%` — `git pull` podmienia plik w trakcie, a cmd czyta `.bat` linia po linii.

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
- `stan_rynku.csv` — etykieta stanu rynku per dzień (poprawka 7): zmienność 30 dni BTC i jej tercyl,
  zwrot 90 dni i jego znak. Tylko zapis, bez wpływu na pozycje.
- `rozbicie.csv` (poprawka 11) — dzienny zwrot każdej składowej rozbity na cenę, funding, koszt i obrót
  (+ liczba likwidacji; X1 także noga long i short); suma składników = netto = wynik w `wyniki.csv` / `x1_wyniki.csv`.
- `fazy.csv` (poprawka 11) — dzienne netto każdej z 7 faz każdej składowej; średnia faz = wynik składowej.
- `koszyk.csv` (poprawka 11) — ranking obrotu 1–50 na początek każdego miesiąca od 2026-09: pozycja, średni obrót
  30 dni, członek top-20 (= skład koszyka silnika), czy jest funding. Wszystkie trzy tylko do zapisu, bez wpływu na pozycje.
- `carry_wyniki.csv` (poprawka 12) — noga carry COIN-M do weryfikacji, osobno: dzień UTC od 2026-09-29, liczba rozliczeń
  fundingu (oczekiwane 3) i znacznik `komplet`, suma stawek, koszt wejścia (tylko pierwszy dzień), netto, netto skumulowane.
  Tylko zapis, bez wpływu na inne nogi.

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
   próbą” razem z CP1P i TP1. Nie jest testem przewagi. *(Zastąpione 2026-09-27 progiem obalenia —
   patrz „Zmiana kryteriów odczytu” niżej.)*
6. **Carry COIN-M (poprawka 12, dopisane 2026-09-28 przed pierwszym wierszem carry):** terminowość, kompletność rozliczeń
   i zgodność z giełdą — kryteria (a)–(c) z sekcji „Poprawka 12”; wynik tylko opisowo, bez progu obalenia.

### Zmiana kryteriów odczytu (decyzja użytkownika 2026-09-27, przed pierwszym odczytem)

Decyzja użytkownika 2026-09-27: „wykonaj wszystkie” (propozycje z `docs/rag/11_przeglad_kandydatow_2026-09-27.md`,
sekcje 2 i 6). Zapis powstał **przed pierwszym odczytem**, przy 3 dniach wyniku R1 i 2 dniach X1 — liczby niżej
nie zależą od wyniku dziennika. Reguły handlu, pozycje i kod dziennika — bez zmian (to nie jest Poprawka N:
skrypt odczytu tylko czyta pliki). Kryteria 1–4 zostają jak wyżej.

**Nowe kryterium 4b — zmienność R1 w paśmie.** Zrealizowana zmienność portfela R1 od pierwszego wyniku
(odchylenie standardowe dziennego `r_port` × √365) po ~92 dniach mieści się w **[13; 31] %/rok** (granice
włącznie). Reguła R1 celuje w 20 %/rok, więc wynik poza pasmem oznacza raczej błąd mechaniki (np. zły mnożnik,
błąd rzędu ≥ 1,5×) niż pecha: na historii R1 poza pasmem leży 5,1 % okien 92-dniowych (sprawdzone drugą
drogą, `docs/rag/11` sekcja 8). Pasmo zapisano tylko dla ~92 dni; przy odczytach po 6 i 12 miesiącach
zmienność jest podawana opisowo (pasmo wiąże tylko w odczycie 1).

**Nowe brzmienie kryterium 5 — próg obalenia (szczebel 3 ADR-09), zamiast „opisowo”.** Dla każdej nogi osobno:
TS1 (`wyniki.csv: r_trend`), CP1 (`r_coinbase`), R1 (`r_port`) i X1 (`x1_wyniki.csv: r_x1`):

- średnia roczna = średnia dzienna × 365 z n dni wyniku (braki pomijane i liczone osobno);
- SE (błąd standardowy średniej) = σ / √(n/365), gdzie σ to zmienność **zakładana** (tabela niżej);
- **próg obalenia = μ − z·SE**; średnia poniżej progu = próg przekroczony, czyli noga obalona
  (ADR-09: obalenie wyłącza strategię z drabiny); średnia nad progiem = brak obalenia.
  **Brak obalenia nie jest potwierdzeniem przewagi** — przy tej długości danych próg odrzuca tylko wyniki
  wyraźnie gorsze od założeń;
- **odczyty wiążące: 3** — po ~3, 6 i 12 miesiącach, czyli przy 92, 182 i 365 dniach wyniku R1 (ostatni dzień
  wyniku 2026-12-24, 2027-03-24, 2027-09-23; odczyt dzień później). **Wiąże WYŁĄCZNIE wydruk z `--as-of` równym
  dacie planu**, gdy migawka dziennika zawiera wynik R1 za ten dzień. Okno 7 dni po planie to tylko zapas: gdy
  migawka na datę planu jest niepełna (przebieg nie doszedł), wiąże pierwsza data w oknie z pełną migawką —
  skrypt sprawdza to sam i pisze „NIE WIĄŻE” przy każdej innej dacie. Ta sama migawka daje ten sam wydruk:
  kolejne uruchomienia to kopie, nie nowe odczyty. Status liczy się raz, z kalendarza, i jest wspólny dla
  wszystkich nóg: X1 (start dzień później) i noga z brakami wiążą razem z R1, a braki zmniejszają tylko ich n
  w SE. Przed pierwszą datą planu skrypt pisze „ZA WCZEŚNIE — tylko podgląd”, bez `--as-of` i między
  odczytami — „podgląd”. Wydruk ostrzega („UWAGA”), gdy migawka nie sięga dnia `--as-of` albo gdy dziennik
  jest starszy niż 2 dni;
- **z = 2,31 na każdym z 3 odczytów** (jeden stały próg). Dobór: łączna jednostronna szansa fałszywego
  obalenia nogi, która naprawdę ma zakładane μ, przez wszystkie 3 odczyty = **2,5 %** — tyle, ile daje
  pojedynczy odczyt przy 1,96. Metoda: symulacja błądzenia losowego (kroki dzienne N(0, 1), statystyka
  odczytu k to suma po n_k dniach / √n_k; odczyty są zagnieżdżone, więc skorelowane: √(n_i/n_j)),
  `simulate_z()` w skrypcie, 10 mln powtórzeń, ziarno 20260927 → 2,3102; druga droga — dokładna całka
  normalna trójwymiarowa (`scipy.stats.multivariate_normal`) → 2,3113. Dla porównania: stałe 1,96 dałoby
  5,7 % fałszywych obaleń. Bonferroni 2,394 (liczba 2,39 z przeglądu) pomija korelację odczytów: łączna
  szansa fałszywego obalenia wyszłaby 2,0 % zamiast 2,5 %, czyli próg obalenia niższy (nogę trudniej obalić),
  niż wymaga założenie. Przy 4 nogach łączna szansa fałszywego obalenia którejkolwiek wynosi do ~10 %
  (nogi są skorelowane, bo R1 składa się z TS1 i CP1).

**Stałe μ i σ** (roczne, arytmetyczne: średnia dzienna × 365, σ dzienna × √365) — konfiguracja dziennika na
historii 2021–2026, zamrożone silniki, statystyka opisowa już raportowana (**0 wariantów, 0 nowych odczytów**).
Komenda: `PYTHONUTF8=1 py -m backtest.odczyt_dziennika_stale` (wydruk z 2026-09-27 poniżej); stałe
w `backtest/odczyt_dziennika.py::LEGS`, zgodność tabeli ze skryptem pilnuje test.

| noga | konfiguracja | μ %/rok | σ %/rok | okres, dni | sprawdzenie drugą drogą | próg obalenia %/rok (Σ za okres) przy 92 / 182 / 365 dniach | lata do wykrycia μ przy 2·SE |
|---|---|---|---|---|---|---|---|
| TS1 | trend 2× z likwidacją izolowaną, pełne uniwersum (silnik RU1 `run_sz1`) | 10,69 | 18,12 | 2021-02-08 → 2026-06-30, 1 969 | CAGR 9,47 %; w oknie wspólnym z CP1 (1 880 dni) CAGR 7,1 / zmienność 18,2 = `runs/2026-09-24_ru1-pelne-uniwersum/raw_output_sz1.txt` l. 5 | −72,7 (−18,3) / −48,6 (−24,2) / −31,2 (−31,2) | 11,5 |
| CP1 | premia Coinbase na BTC, 3× z likwidacją | 31,04 | 35,11 | 2021-05-08 → 2026-06-30, 1 880 | CAGR 28,2 / zmienność 35,1 = RU1 `raw_output_sz1.txt` l. 6 | −130,5 (−32,9) / −83,8 (−41,8) / −50,1 (−50,1) | 5,1 |
| R1 | portfel: budżet ryzyka 1/σ, cel 20 %/rok, sufit 2 | 18,17 | 21,66 | 2021-05-08 → 2026-06-30, 1 880 | CAGR 17,1 / zmienność 21,7 = RU1 `raw_output_sz1.txt` l. 8 | −81,5 (−20,5) / −52,7 (−26,3) / −31,9 (−31,9) | 5,7 |
| X1 | momentum przekrojowe, średnia 7 faz (silnik X1F) | 9,49 | 36,26 | 2021-02-08 → 2026-06-30, 1 969 | +9,5 %/rok = `runs/2026-09-24_x1f-siedem-faz/raw_output.txt` l. 14 | −157,3 (−39,7) / −109,1 (−54,4) / −74,3 (−74,3) | 58,4 |

- **Dlaczego R1 μ = 18,17, a nie 17,1:** 17,1 %/rok w RU1 to CAGR (średnia geometryczna). Próg obalenia porównuje
  średnią arytmetyczną, więc potrzebna jest arytmetyczna — ta sama historia daje 18,17 %. (18,6 z SZ1 to stary
  CAGR na obciętym uniwersum.) TS1 w dzienniku to trend **z likwidacją 2×** — dlatego 10,69, a nie 11,1 z RU1
  (bez likwidacji).
- **Przedział:** obok średniej wydruk podaje przedział 95 % zrealizowanej średniej (średnia ± 1,96 × zrealizowane
  odchylenie / √(n/365)) — opis efektu (bramka 16b), nie część progu.
- **Co to znaczy dla decyzji:** progi są bardzo niskie (np. R1 po kwartale −20,5 % sumy zwrotów), bo 3 miesiące
  to mało danych. Odczyt 25.12 rozstrzyga więc mechanikę (1–4b), a przewagi nie rozstrzyga. Szansa, że noga
  **bez żadnej przewagi** (prawdziwe μ = 0) zostanie obalona w którymś z 3 odczytów: TS1 ~7 %, CP1 ~11 %,
  R1 ~10 %, X1 ~4 % (ta sama symulacja). Potwierdzenie zakładanego zysku wymagałoby 5–58 lat (ostatnia kolumna).
- Założenie symulacji: dzienne zwroty niezależne, a średnia z ~90+ dni w przybliżeniu normalna. Grube ogony
  (np. X1) sprawiają, że rzeczywista szansa fałszywego obalenia może się nieco różnić od 2,5 %.

Wydruk komendy stałych (2026-09-27):

```
μ, σ nóg dziennika na historii 2021–2026 (arytmetycznie; opisowo, 0 wariantów)
  TS1 trend 2× (własne okno)          1969 dni 2021-02-08 → 2026-06-30 | μ +10.69 %/rok | σ 18.12 %/rok | CAGR  +9.47 %
  TS1 trend 2× (okno wspólne z CP1)   1880 dni 2021-05-08 → 2026-06-30 | μ  +8.50 %/rok | σ 18.20 %/rok | CAGR  +7.08 %
  CP1 premia Coinbase 3×              1880 dni 2021-05-08 → 2026-06-30 | μ +31.04 %/rok | σ 35.11 %/rok | CAGR +28.25 %
  R1 portfel (budżet ryzyka)          1880 dni 2021-05-08 → 2026-06-30 | μ +18.17 %/rok | σ 21.66 %/rok | CAGR +17.14 %
  X1 średnia 7 faz                    1969 dni 2021-02-08 → 2026-06-30 | μ  +9.49 %/rok | σ 36.26 %/rok | CAGR  +2.63 %
```

**Komenda odczytu** (czyta tylko `origin/master:dziennik/*`, niczego nie zapisuje; `--as-of` odtwarza stan
z ostatniego commita „Dziennik: przebieg” z datą ≤ as_of + 1 dzień; `git fetch` przed każdym wydrukiem, bo
skrypt czyta lokalny `origin/master`):

```
git fetch && PYTHONUTF8=1 py -m backtest.odczyt_dziennika --as-of 2026-12-24          # odczyt 1
git fetch && PYTHONUTF8=1 py -m backtest.odczyt_dziennika --as-of 2027-03-24          # odczyt 2
git fetch && PYTHONUTF8=1 py -m backtest.odczyt_dziennika --as-of 2027-09-23          # odczyt 3
git fetch && PYTHONUTF8=1 py -m backtest.odczyt_dziennika [--repo .] [--json]         # podgląd
```

Skrypt jest reporterem („próg przekroczony / nieprzekroczony”); werdykt o każdej nodze podpisuje Claude
w dokumentacji odczytu, a decyzja o szczeblu 4 należy do użytkownika. Kryteria 1–4 skrypt liczy tymi samymi
definicjami co strona dziennika (`tools/strona_dziennika.build_state`). Testy: `tests/test_odczyt_dziennika.py`.

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
