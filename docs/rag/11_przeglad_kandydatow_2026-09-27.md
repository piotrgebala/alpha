---
status: active
last_verified: 2026-09-27
depends_on: [09_drabina_dowodow.md, 10_preferencje_uzytkownika.md]
---

# Przegląd: co jeszcze przetestować i co dopisać do dziennika (stan 2026-09-27)

> **To jest przegląd, nie runda.** Nie uruchomiono żadnego testu strategii i nie obejrzano żadnego wyniku, więc przegląd zużył 0 odczytów. Weryfikatorzy otwierali pliki tylko po to, żeby sprawdzić kompletność, zakresy dat, zgodność sygnałów między sobą i zmienność opisową. Żaden z nich nie liczył związku sygnału z przyszłym zwrotem.

**Jak czytać liczby mierzalności.** Przy każdej liczbie w nawiasie kwadratowym piszę, o jaki szum chodzi:

- **[IC]** — rozrzut średniego IC (information coefficient, czyli korelacji rang sygnału ze zwrotem następnego tygodnia). Przyrząd AU2 dla top-50 ma błąd standardowy 0,0078 (wn. 92).
- **[zwrot]** — rozrzut średniego rocznego zwrotu strategii. W jednostkach Sharpe'a (SR, zwrot na jednostkę ryzyka) połowa szerokości przedziału 95 % wynosi ±1,96/√(liczba lat).
- **[zdarzenie]** — rozrzut zwrotu po jednym zdarzeniu, np. po kaskadzie likwidacji.
- **[trafność]** — losowość odsetka trafnych zakładów (pasmo z `measurability_report`).
- **[mechanika]** — rozrzut wielkości, które sprawdzają działanie dziennika (zmienność, obrót, funding), a nie przewagę.

Pozostałe skróty:

- **MDE** (najmniejszy wykrywalny efekt) liczę przy mocy 80 %. Moc to szansa, że efekt, który naprawdę istnieje, zostanie wykryty.
- **DSR** (Sharpe skorygowany o liczbę prób) mówi, czy najlepszy wynik nie jest tylko najszczęśliwszym z wielu pustych pomysłów.
- **STOP** to seria zamknięta w `runs/INDEX.md`. Kolejny wariant takiej serii wymaga decyzji użytkownika.

---

## 1. Odpowiedź w skrócie

1. Przegląd sprawdził 35 kandydatów. Przeszły 3, 18 jest wątpliwych (wymagają decyzji użytkownika albo poprawek), a 14 odrzucono.
2. Żaden z trzech, które przeszły, nie jest testem na historii. To kolektor pełnych likwidacji z Bybit, dzienny indeks likwidacji z kopią zapasową i rozbicie zwrotu dziennika na cenę, funding i koszt.
3. Historia 2021–2026 nie rozstrzygnie już żadnej nowej hipotezy. Następny odczyt byłby 41. Przy 41 pustych pomysłach najlepszy i tak ma t ≈ 2,2, czyli DSR 0,5, a to rzut monetą.
4. Dowód (DSR 0,95) wymaga t ≈ 3,84, czyli rocznego SR ok. 1,6 na 5,5 roku [zwrot]. Żaden kandydat nie zapowiada takiego efektu. Odczyt historii może więc dać najwyżej „kandydata do dziennika”, nigdy dowód.
5. Niezauważone kombinacje są. Każda z nich albo wpada w serię pod STOP-em, albo jest niemierzalna. Realistyczne IC kandydatów przekrojowych to 0,00–0,015, a zysk netto wymaga IC ≥ ~0,034 [IC].
6. Przewaga leży teraz w czasie: w danych, których nie da się odtworzyć wstecz (likwidacje zbierane od 25.09), i w uczciwie przygotowanym odczycie dziennika ~25.12.
7. Do dziennika proponuję wyłącznie zapisy tylko do odczytu. Nowej nogi nie proponuję, bo żadna nie przeszła filtra.
8. Odczyt 25.12 sprawdzi mechanikę dziennika (kompletność, depozyt, zmienność, koszty). Przewagę obali tylko przy katastrofie. Najpilniejsza decyzja użytkownika dotyczy kopii zapasowej likwidacji, bo dziś nie istnieje żadna.

---

## 2. Do dziennika papierowego

„Poprawka N” to wpis w `dziennik/README.md`, wymagany przy każdej zmianie kodu, z którego korzysta dziennik. Ostatnia to Poprawka 10, więc następna będzie Poprawką 11. Żaden zapis poniżej nie zmienia pozycji.

| Co | Rodzaj | Poprawka N / decyzja użytkownika | Co rozstrzygnie i kiedy | Koszt pracy | Status |
|---|---|---|---|---|---|
| **Rozbicie zwrotu** na cenę, funding, koszt i obrót (`rozbicie.csv`; TS1, CP1, X1 z nogą long i short) | zapis tylko do odczytu | Poprawka 11: tak. Decyzja: tak | **Po 3 mies.:** czy obrót i koszt zgadzają się z KO1. Oczekiwany obrót to TS1 ≈ 11, CP1 ≈ 21 i X1 ≈ 47 kapitałów na rok, czyli koszt w kwartale ≈ 0,2 / 0,4 / 0,8 %. Błąd średniego obrotu wynosi ~8 % [mechanika], więc odchylenie powyżej 30 % będzie widać jako błąd mechaniki. **Po 12 mies.:** poziom fundingu z dokładnością ±2–3 pp/rok [mechanika: funding silnie zależny dzień po dniu]. **Nie rozstrzygnie**, skąd bierze się wynik X1, bo cena X1 ma po roku rozrzut ±32 %/rok [zwrot]. | mały (~30–50 linii + test, że składniki sumują się do netto) | **ok** |
| **Wyniki per faza** (`fazy.csv`; faza to jeden z 7 dni startu tygodniowej przebudowy) | zapis diagnostyczny | Poprawka 11: tak. Decyzja: tak | Od pierwszego tygodnia pokaże błąd silnika albo jedno zdarzenie w jednej monecie (jak MYX): różnicę faz ≳ 3–5 % kapitału w tygodniu [mechanika]. Jako wycinek szczebla 2 nic nie doda, bo fazy dzielą ten sam sygnał; po 2 latach t jednej fazy ≈ 0,78 [zwrot]. Cena per faza jest już w `transakcje.csv` (Poprawka 9). Nowe jest dzienne netto z fundingiem i kosztem, a `data/raw/live` jest nadpisywany, więc później tego nie odtworzymy. | mały | wątpliwy (częściowo pokryte) |
| **Skład koszyka i liczniki pobrania** (`koszyk.csv` + pola w `przebiegi.log`) | rejestr | Poprawka 11: tak. Decyzja: tak. Zmiana w `rebalance_premium` wymaga testu, że skład top-20 zostaje co do bajtu taki sam | Działa od pierwszego przebiegu. Do 25.12 da ~90 wierszy liczników i 3–4 składy miesięczne. Ułatwi zaplanowany sprawdzian „dane na żywo vs archiwum” (STATUS, propozycja 3; termin 22.10–05.11). Wycofane monety zobaczy tylko od dnia startu, nie wstecz. Szumu brak, to rejestr. | mały | wątpliwy (tylko formalnie: kod dziennika) |
| **Kryterium 4b: zmienność R1 w paśmie** | dopisek do `dziennik/README.md`, bez nowego pliku i bez zmiany kodu | Poprawka kodu: nie. Decyzja: tak (zmiana umowy odczytu, zapisana przed odczytem) | Przewidywana zmienność R1 to z konstrukcji 20 %/rok, więc wystarczą pliki, które już istnieją. Pasmo po 92 dniach: **[13; 31] %/rok**. Węższe [15; 25] dałoby dużo fałszywych alarmów: w historii R1 (PR1, 1 729 okien 92-dniowych) poza nim leży 32 % okien, a poza [13; 31] tylko 5 % [mechanika: skupiska zmienności]. Wykryje tylko błąd rzędu ≥ 1,5×. Po 12 mies. pasmo zwęża się do [17; 26]. | bardzo mały | wątpliwy (karta chciała nowych plików, które są zbędne) |
| **Skrypt odczytu 25.12** (`backtest/odczyt_dziennika.py`) | narzędzie, które tylko czyta pliki dziennika | Poprawka: nie. Decyzja: tak, bo kryterium 5 zmienia się z „opisowo” na „próg obalenia” (zgodnie z ADR-09) | W 3 mies. rozstrzygnie mechanikę (kryteria 1–4b). Przewagi nie rozstrzygnie. Progi obalenia w kwartale: TS1 −14,9 %, CP1 −26 %, R1 −17 %, X1 −33 % [zwrot]. Szansa obalenia pustej strategii po roku to tylko 3–15 %. Wykrycie zakładanego zysku zajęłoby: TS1 ~10,5 roku, CP1 ~4,7, R1 ~6,4, X1 ~57 lat. | mały (~80–120 linii + test) | wątpliwy (poprawki niżej) |
| **Ślad wykonania** (cena kilka godzin po przebiegu wobec zamknięcia dnia) | zapis albo jednorazowy pomiar opisowy | W dzienniku: Poprawka 11, decyzja i security-review. Na historii: bez Poprawki, 0 wariantów (jak KO1) | Na historii (darmowe archiwum 1h od 2020): ±0,6–0,9 %/rok dla TS1 [mechanika: ruch ceny w pierwszych godzinach]. W dzienniku po 12 mies. ±1,3–2,0 %/rok, co nie rozstrzygnie, czy koszt spóźnienia mieści się w 0,8 %/rok. Godzina 08:00 UTC to 10:00 w Polsce, a nie „po pracy”. Wiersz powstałby dopiero przy przebiegu następnego dnia. | średni | wątpliwy (lepiej na historii, przed szczeblem 4) |
| **Kolektor pełnych likwidacji Bybit** | kolektor poza dziennikiem | Poprawka: nie, bo dziennik go nie importuje. Security-review: tak. Linię crona dodaje użytkownik | Tylko zbiera dane. Pierwsza karta E1 najwcześniej 2027-09 (szczegóły w sekcji 3). | średni | **ok** |
| **Dzienny indeks likwidacji LK0 + kopia zapasowa** | rejestr poza dziennikiem | Poprawka: nie. Decyzja: tak (gdzie trzymać kopię; nowe połączenie wymaga security-review) | Chroni jedyny zbiór likwidacji, który dziś nie ma żadnej kopii (sekcja 3). | mały | **ok** |

**Poprawki do skryptu odczytu, zanim trafi do pre-rejestracji:**

- Kryteria 1–4 liczy już `tools/strona_dziennika.py`, który leży na gałęzi `strona-dziennika` i nie jest jeszcze scalony. Skrypt ma użyć tych samych definicji, a nie pisać ich od nowa.
- `summarize_pnl` trzeba wywołać z `periods_per_year=365` i `capital_per_notional=1`. Inaczej średnia roczna wyjdzie błędna o czynnik 3/2.
- μ i σ trzeba zapisać dla konfiguracji dziennika (trend 2× z likwidacją). Dla R1 μ = 17,1 %/rok (RU1), a nie 18,6.
- Odczyty po 3, 6 i 12 mies. przy z = 1,96 dają ~5,7 % fałszywego obalenia na nogę, a dla 4 nóg do ~20 %. Trzeba z góry wybrać jedną z dwóch dróg: stały próg z ≈ 2,39 na każdy odczyt albo próg wiążący dopiero po 12 miesiącach.
- Pozycję (4b) i pliki `ryzyko.csv`, `fazy.csv`, `rozbicie.csv` oznaczyć jako warunkowe, bo dziś nie istnieją.

**Czego nie dodawać do dziennika:**

- **Nowej nogi z pakietu przekrojowego.** Żadna nie przeszła filtra.
- **Cienia celu zysku (TP).** Da się go policzyć wstecz w dniu odczytu z `transakcje.csv`, `sygnaly.csv` i high/low z archiwum, bez zmiany kodu.
- **Cienia TR1 (miejsca 21–50).** Da się go odtworzyć z archiwum.
- **Etykiety premii koreańskiej.** To powtórka KP1.
- **DVOL jako kolejnej etykiety** ani **dziennej etykiety kaskad likwidacji.** Obie zapraszają do odczytu po wyniku.
- **Porównania „3 papierowe likwidacje vs dni kaskad”.** To n = 3, dwie są tą samą monetą ACE i wszystkie otwarto przed startem, więc informacja jest zerowa.

---

## 3. Testy na historii 2021–2026, które przechodzą filtr

**Żaden.** Wszyscy kandydaci, którzy chcieli czytać historię 2021–2026, odpadli albo czekają na decyzję użytkownika (sekcje 4–5). Powód jest jeden: to byłby 41. odczyt tej samej historii, a żaden realistyczny efekt nie sięga progu t ≈ 3,84.

Trzej kandydaci ze statusem ok działają poza historią:

| Nazwa | Pięć pól | Mechanizm | Dane w repo | Mierzalność (z rodzajem szumu) | Koszt pracy | DSR |
|---|---|---|---|---|---|---|
| **Kolektor pełnych likwidacji Bybit** (+ kopia LK0 i Bybit poza serwerem; OKX: nie teraz) | pełne likwidacje Bybit × zdarzeniowa, per moneta × kierunek (powrót ceny po kaskadzie, przyszła karta E1) × godziny–doba × **zbieranie, 0 odczytów** | Likwidowany **musi** zamknąć pozycję po każdej cenie. Cena przestrzeliwuje, a zarabia ten, kto przejmie ruch i poczeka na powrót. Dowód spoza naszych danych jest tylko jakościowy (Coval–Stafford 2007, Brunnermeier–Pedersen 2009). Liczby efektu dla krypto brak. | Brak. Dane są darmowe tylko od dnia uruchomienia, a historia jest płatna (Tardis; decyzja „płatne: nie”). LK0 z Binance to próbka ≤ 1 zdarzenie/s/symbol, więc najsłabiej widzi właśnie kaskady. | Dotyczy przyszłej karty. Horyzont 24 h, rozrzut 5 % [zdarzenie]: MDE 0,99 % na epizod po roku i 0,70 % po 2 latach. Przy rozrzucie 8 %: 1,58 / 1,12 %. Horyzont 4 h, rozrzut 2,5 %: 196 epizodów, czyli ~0,7–1,3 roku. Efekt 0,5 % przy rozrzucie 4 %: 502 epizody, czyli **1,7–3,4 roku**. Liczba 150–300 niezależnych epizodów rocznie to założenie, które trzeba potwierdzić po 4–6 tyg. z samych liczników, bez cen. Realny koszt w kaskadzie na małych monetach to 0,3–1 % za wejście i wyjście, więc efekt musi przekraczać ~1 %. | średni (~200–250 linii, testy bez sieci, security-review, przegląd kodu) | 0 dziś. Przyszły odczyt będzie na nowych danych, więc nie dokłada się do ~40 odczytów historii. **Jeden licznik E1** dla LK0 i Bybit. |
| **Dzienny indeks likwidacji LK0 + kopia zapasowa** | likwidacje LK0 × rejestr × brak targetu × dzienny × 0 odczytów | Brak zakładu. To higiena danych przed kartą E1. | Dane leżą poza repo w `~/likwidacje`: ~68 tys. zdarzeń od 25.09, 0 rozłączeń, 0 pominiętych, **zero kopii**. Rozmiar ~0,9 MB na dobę po gzip, czyli ~330 MB na rok. | Teraz nie dotyczy. Dla przyszłej karty: 196 epizodów przy efekcie 1 % i rozrzucie 5 % [zdarzenie] to ~6,5 mies.; 502 epizody przy rozrzucie 8 % to ~1,4 roku, jeśli epizody są niezależne, ale **~9,7 roku, jeśli kaskady skupiają się w tych samych dniach**. Kolumna „maks. w oknie 5 min” ma sufit z próbkowania, więc nadaje się tylko do rang. | mały (~40 linii + test; skrypt osobno od pętli kolektora, bo kolektor działa z klonu dziennika) | 0 |
| **Rozbicie zwrotu dziennika** | własne szeregi dziennika × zapis × składniki zwrotu × dzienny × 0 odczytów | Brak zakładu. Sprawdza założenia kosztów KO1 przed szczeblem 4 (mała realna kwota). | Wszystko jest w pamięci silnika przy każdym przebiegu (`ts_momentum.portfolio`, `xs_momentum.long_short_returns`), a dziennik zapisuje tylko netto. | Jak w sekcji 2: koszt i obrót po 3 mies. [mechanika], funding ±2–3 pp/rok po 12 mies.; źródło wyniku X1 nierozstrzygalne. | mały | 0, pod warunkiem że żadna decyzja o regule nie zapadnie na podstawie nóg X1 |

---

## 4. Wymagają decyzji użytkownika (zdjęcie STOP / zakazany wariant / nowe źródło)

**(A) Historia 2021–2026, serie pod STOP-em**

| Kandydat | Pięć pól (skrót) | Dlaczego wątpliwy | Mierzalność | Decyzja użytkownika | Moja rada |
|---|---|---|---|---|---|
| `xs-funding-kierunek-top50-1w` + jego rozstrzygnięcie | suma fundingu z 7 dni (funding to opłata między longami a shortami) × przekrój top-50 × kierunek relatywny × tydzień | Komórka jest formalnie nietknięta, bo P2 liczyło carry, a nie cenę. Wskaźnik i mechanizm są jednak te same co w TF1: −1,41 %/rok [−6,58; +3,77] (wn. 73). Rekomendacja TF1 brzmi „nie wracać bez nowego mechanizmu”. Literatura nie podaje IC dla przekroju. Plus: funding top-50 jest kompletny, a ranking fundingu prawie nie pokrywa się z momentum (ρ −0,04). | MDE 0,022 [IC], a realnie 0,029–0,035, bo szum prawdziwego sygnału jest ×1,3–1,55 większy. Przy priorze z TL1 (IC 0,008) moc to 18 % przy progu 1,96 i 3 % przy progu rodzinnym 2,9. Przy IC 0,025 moc to 89 % / 62 %. Zysk netto ma rozrzut ±28 %/rok [zwrot], a t 1,96 wymaga IC ≈ 0,034. | nowa seria + 41. odczyt | **nie** |
| `xs-ls-konta-top50-1w` | proporcja kont long/short × przekrój top-50 × kierunek przeciw tłumowi × tydzień (od 2021-12) | Wpada w STOP serii O („kolejna kolumna”) i SW („wolniejszy horyzont”). Jedyny ślad to SW na BTC (IC +0,028), ale była to najlepsza z 8 cech, a zysk netto wyszedł tylko w 2 z 6 lat. Poziom L/S może być stałą cechą monety, a nie sygnałem tygodniowym. Danych L/S dla altów nie ma w repo. | MDE 0,020–0,024 na 4,6 roku [IC]. Moc: 84 % przy IC 0,025, 61 % przy 0,019, 43 % przy 0,015. Jeśli sygnał jest trwały, MDE rośnie do 0,027–0,030 i runda nie startuje. Zysk netto ±30 %/rok [zwrot]; t 2,2 wymaga ~+34 %/rok. | zdjęcie STOP O/SW, nowa seria, 41. odczyt | nie teraz. Jeśli tak, najpierw bez zwrotów zmierzyć autokorelację rankingu (0 odczytów). |
| `xs-niska-zmiennosc-bab-top50-1w` | vol30/beta90 × przekrój top-50 × kierunek × tydzień | Rozstrzygnięcie w uzupełnieniu: **odrzucić** (sekcja 5). | — | — | odrzucić |
| `xs-reversal-7d-top50-1w` | zwrot 7 dni, znak odwrotny × przekrój × kierunek × tydzień | Rozstrzygnięcie: **odrzucić** (sekcja 5). | — | — | odrzucić |
| `xs-dzienny-top50-1d-3d` | zwrot 1–3 dni × przekrój × kierunek × dzień | Rozstrzygnięcie: **odrzucić**. Wersja (b) przechodzi do B4, a B4 też odpada (sekcja 5). | — | — | odrzucić |
| `xs-budzet-1-odczyt-prog-t22` | reguła: cały pakiet przekrojowy dostaje łącznie 1 odczyt, wybrany przed danymi, próg t > 2,2, najwyżej „kandydat do dziennika” | Reguła wybrała niską zmienność. Ta leży pod STOP-em B1, a weryfikacja tej komórki ją odrzuciła. Publikacji, na której opiera się wybór (Pyo & Jang 2026), nie przeczytano, bo serwer zwrócił błąd 403. Liczby mocy w karcie były za optymistyczne. | Przy prawdziwym +10–13 %/rok szansa na t > 2,2 to 7–22 %, a na t > 3,85 poniżej 1 % [zwrot]. 80 % mocy przy progu 2,2 wymaga +27–43 %/rok netto. | zdjęcie STOP B1; bez tego budżet = 0 | przyjąć jako zasadę: **pakiet przekrojowy na historii = 0 odczytów**, dopóki użytkownik nie zdejmie STOP |
| `xs-pakiet-holdout-po-dacie` | 1 reguła zamrożona dziś, odczyt tylko na danych po dacie odcięcia | To nowa procedura, a nie hipoteza. Reguły są wariantami serii pod STOP-em, a STOP dotyczy wariantu, nie okresu. Dla dzisiejszych zwrotów wartość jest zerowa. | Dziś NIEMIERZALNA. IC jednej reguły stanie się widoczne po 4,1 / 7,0 / 9,9 roku (szum ×1 / ×1,3 / ×1,55) [IC], czyli najwcześniej ~2031. Zysk netto (t 1,96): 6,8–10,7 roku, a przy mocy 80 % 13,9–21,8 roku [zwrot]. Wersję z sześcioma regułami trzeba skreślić. | zapisać czy uznać pakiet za zamknięty | jeśli już, to jedna reguła z mechanizmem i publikacją; inaczej zamknąć |

**(B) Inna baza danych**

| Kandydat | Pięć pól | Dlaczego wątpliwy | Mierzalność | Decyzja użytkownika | Moja rada |
|---|---|---|---|---|---|
| `xt1-momentum-przekroj-tradfi-1990` | 19 rynków FRED × przekrój × kierunek relatywny × tydzień, 1990–2026 | Ma być dowodem mechanizmu dla X1 (szczebel 1(b)), a nie nogą. Wymaga dwóch decyzji: nowej serii XT mimo STOP-u X „inne uniwersum” i wyjątku od zasady 20. Wagi bez skalowania zmiennością sprawiają, że liczą się głównie Brent, Nasdaq i Nikkei. Wynik może więc w dużej części powtarzać TX1. Koszyk rośnie z 16 do 19 rynków w latach 1990–1999. Wynik nie zmieni decyzji o kapitale, bo X1 jest poza portfelem realnym (wn. 101). | MDE (moc 80 %) = SR 0,46 na 36,7 roku, a SR 0,51, bo to 2. odczyt tej bazy po TX1 [zwrot]. Realistycznie SR 0,2–0,4, co daje moc 23–44 %; przy SR 0,3 szansa na wynik nierozstrzygnięty wynosi ~56 %. Po 2013 roku ±0,53 SR, więc tylko opis. | seria XT + wyjątek od zasady 20 | nie teraz. Jeśli tak, najpierw bez zwrotów zmierzyć zgodność pozycji z TX1. |

**(C) Nowe źródła danych lub wykonanie automatyczne**

| Kandydat | Pięć pól | Dlaczego wątpliwy | Mierzalność | Decyzja użytkownika | Moja rada |
|---|---|---|---|---|---|
| `e1-kaskady-likwidacji-dzienna` | likwidacje × (a) zdarzeniowa albo (b) ranking × kierunek × 1–3 dni | Na razie tylko zbieranie; karta najwcześniej 2027-09. Karta miesza dwie formuły naraz. Wersja (b) może być przebranym odwróceniem 1-dniowym, a to zakazany wariant serii X. Potrzebne ramię kontrolne. | Pierwsze 90 dni to rozbieg, więc po roku zostaje ~275 użytecznych dni. (a): MDE 1,25–2,2 % na zdarzenie po roku i 0,66–1,14 % po 3 latach [zdarzenie]. (b): moc przy IC 0,025 wynosi 49 % po roku, 78 % po 2 latach i 92 % po 3 [IC]; koszt ~17 %/rok. Rozstrzygalne ~2028–2029 przy efekcie ≥ ~1 %; przy < ~0,7 % niemierzalne nawet po 3 latach. | kopia danych; jedna formuła wybrana przed odczytem | zbierać. Formułę zapisać po rachunku mocy z realnej częstości (za 4–6 tyg., bez cen). |
| `e1-kaskady-likwidacji-intraday-1h-24h` | likwidacje × zdarzeniowa × kierunek × 1–24 h | Koszt 0,19–0,29 % za wejście i wyjście (taker + poślizg) zjada 60–100 % zakładanego efektu 0,3 %. Wymaga automatu intraday poza dziennikiem. | Rozrzut 3–5 % na epizod [zdarzenie]. Przy efekcie brutto 0,5 % trzeba 735–4 449 epizodów, a przy 0,3 % 5 838–16 217. Niezależnych epizodów jest ~200–500 rocznie. W 1–3 lata mierzalny jest tylko efekt brutto ≥ 0,5 %. | automat intraday | zbierać i wrócić do tego w 2027 |
| `xs-uwaga-google-trends-1w` | uwaga per moneta × przekrój × kierunek × tydzień | Wersja z Wikipedią to UW1/UW2 z SH1. Pokrywa 40 z 79 monet, czyli mniej niż wymagane 70 %, więc brama danych jest niezaliczona. Nowy jest tylko Google Trends: indeks przeskalowywany przy każdym pobraniu, niepowtarzalny, z wieloznacznymi nazwami. | MDE przy progu t ≈ 3 (41. odczyt): 0,031 / 0,037 / 0,043 dla 50 / 35 / 25 monet [IC]. Zbieranie od dziś zajęłoby 4,4–9,9 roku. | nowe źródło, security-review, zgoda na odczyt uznawany za wariant B1/obrotu | nie. Jeśli tak, tylko brama danych z warunkiem stopu zapisanym przed nią. |

**(D) Dziennik** — `ryzyko-pvol-zapis`, `skrypt-odczytu-25-12`, `slad-wykonania-1h`, `wyniki-per-faza`, `koszyk-sklad-i-liczniki`. Są wątpliwe z powodów formalnych (zmiana kodu dziennika wymaga Poprawki i decyzji użytkownika) albo dlatego, że karty obiecywały za dużą precyzję. Poprawione liczby i zakres są w sekcji 2.

**(E) Narzędzie**

| Kandydat | Co to jest | Dlaczego wątpliwy | Liczby | Decyzja użytkownika | Moja rada |
|---|---|---|---|---|---|
| `rejestr-odczytow-prog-t-n` | plik `runs/odczyty_historii.csv` + funkcja `required_t(N, dsr)` + strażnik w testach | Tylko błędy w karcie. (1) Moduł ma być nowy (`backtest/dsr.py`), bo `metrics.py` leży w łańcuchu importów dziennika (`live_journal` → `checkpoint_lib` → `metrics`). (2) Funkcje trzeba skopiować z zamrożonego `run_au4_dsr.py` i sprawdzić testem; import wciągałby kod dziennika. (3) Strażnik ma wymagać wiersza także dla rund z 0 wariantów, które drukują zwrot lub t (X1F, RU1–RU4, CP1P, TR1 RU3). | N = 41 → oczekiwane maksimum t pustych pomysłów 2,20; t dla DSR 0,80 = 3,04; dla DSR 0,95 = 3,84. Na 5,5 roku oznacza to minimalny roczny SR ~1,3 i ~1,6. Wzór sprawdzony symulacją (2,17 wobec 2,20). | niepotrzebna | **zrobić** (2–3 h, 0 wariantów) |

---

## 5. Sprawdzone i odrzucone w tym przeglądzie

Ta lista jest po to, żeby nikt nie proponował tych pomysłów ponownie.

- **TX2 — trend na kontraktach futures po 2013:** niemierzalny. Szerokość przedziału Sharpe'a zależy od liczby lat, a nie rynków: ±0,53 SR na 13,7 roku [zwrot]. Moc to 20–60 % przy SR 0,3–0,6, a 80 % mocy wymaga 39–87 lat. Futures nie ma w repo, a seria TX ma STOP. Zamiast tego weryfikatorzy wskazują dowód 1(a) z opublikowanych indeksów funduszy trendowych po 2013, bez licznika.
- **Reszta po becie do BTC (momentum reszty / opóźnienie altów):** jedna karta miała dwa przeciwne znaki. Prior jest poniżej progu (X2: IC −0,006). Moc to 24–47 % przy IC 0,01–0,015 [IC], a DSR 0,95 wymagałby IC ≈ 0,038. To wariant B1 pod STOP-em.
- **Nadzwyczajny wolumen:** mechanizm odwraca cytowaną pracę. Bianchi–Babiak–Dickerson opisują odwrócenie ceny przy **niskim** wolumenie i w małych monetach. DSR 0,95 wymagałby IC ≈ 0,056 [IC].
- **Pary na kointegracji (C1):** relacja ETH/BTC nie jest stała (0,025 → 0,088 → 0,018 → 0,027). Rozrzut na parę to ±38 %/rok [zwrot], a w 5,5 roku zbiera się tylko 16–29 transakcji na parę. Wersja koszykowa to B4.
- **Powrót reszty po PCA (B4):** zysk niemierzalny, ±11–17 %/rok [zwrot]. Po korekcie DSR potrzebny jest SR brutto 1,7–2,3, a przy realistycznym SR 0,5–0,9 trzeba 10–31 lat. Koszty 5–34 %/rok. R1 i X1 mówią, że ruchy względne trwają. Jeśli kiedyś, to tylko rachunek mocy bez odczytu (2 h).
- **Premia koreańska per moneta:** ta sama komórka co KU1 z SH1 (NIEMIERZALNY). MDE 0,030–0,039 przy ~30 monetach [IC]. Brak 19 wycofanych rynków daje błąd przeżywalności, którego nie da się usunąć.
- **Pakiet sygnałów BTC na tydzień spoza wykresu** (DVOL, MVRV, basis, VIX/Nasdaq, wolumen giełd): sam BTC to ±0,84 SR [zwrot], a 80 % mocy pojawia się dopiero przy SR 1,2. Odczyt przez trafność wymaga 646 tygodni, czyli ~12,4 roku. Filtr DVOL ma moc ~7 % przy efekcie 2 pp.
- **Kalendarz** (rozliczenie fundingu co 8 h, wygaśnięcia opcji i CME, weekend): odróżnienie trafności 50,9 % od 50 % wymaga 25 320 zdarzeń, czyli ~23 lat [trafność]. Przy 3 zakładach dziennie koszt to ~150 % nominału rocznie. Deribit ma pasmo ±5,8 pp, CME ±12,1 pp.
- **Etykieta premii koreańskiej w dzienniku:** powtórka KP1. Wykrycie wymagałoby ~178 lat (2 błędy standardowe) albo ~348 lat (moc 80 %) [zwrot]. Doszłyby dwa nowe hosty i kurs DEXKOUS opóźniony o 7–10 dni.
- **Cień celu zysku (TP) w dzienniku:** zawężenie przedziału różnicy do ±5 pp wymaga 41–51 lat [zwrot, różnica wersji]. Cień da się policzyć wstecz bez zmiany kodu. Dokłada ~6–8 pp/rok kosztów.
- **Cień TR1 (miejsca 21–50):** korelacja z TS1 wynosi 0,86, więc własnej informacji jest tylko ~26 %. t > 1,96 przyszłoby po 12,8 roku [zwrot]. Szczebel 2 jest już spełniony na historii, a wynik da się odtworzyć z archiwum.
- **Rozstrzygnięcie: niska zmienność / BAB (zakład przeciw becie):** to wariant BB1, odrzuconego już w SH1. Na perpetualach dźwignia jest tania, więc mechanizm BAB się nie przenosi. Literatura krypto wskazuje raczej znak przeciwny. Przy IC 0,01 wykrycie wymaga 26–46 lat [IC].
- **Rozstrzygnięcie: odwrócenie 7 dni:** zakazany wariant serii X (inne okno) i X2 (trzeci odczyt B1). R1 i X1 mówią, że ruchy względne trwają. Rachunek trafności: wykrywalne 50,7 % wobec zakładanych 50,3–50,5 % [trafność], więc NIEMIERZALNA. Koszt 5,8–11,6 %/rok.
- **Rozstrzygnięcie: przekrój dzienny:** w wersji (a) koszt obrotu 41–88 %/rok jest nie mniejszy niż zysk brutto. Wersja (b) przeszła do B4, a B4 też odpadło.

---

## 6. Kolejność, którą proponuję

Decyzje bramkowe oznaczam **[DECYZJA UŻYTKOWNIKA]**. Żaden krok nie dotyka realnego kapitału.

1. **Teraz: zabezpieczyć dane, których nie da się odtworzyć.**
   - Co zrobić: kopia `~/likwidacje` poza serwerem, potem kolektor Bybit i dzienny indeks LK0.
   - **[DECYZJA UŻYTKOWNIKA]:** gdzie trzymać kopię (osobne prywatne repo GitHub, komputer z Windows albo chmura); zgoda na nowe połączenia (security-review); dodanie linii crona.
   - Dlaczego: to jedyna dźwignia, która zależy od czasu. Każdy dzień bez kolektora to doba próby stracona na zawsze. Utrata serwera oznacza dziś utratę całego LK0.
   - Kiedy dalej: za 4–6 tyg. rachunek mocy z realnej częstości kaskad i kontrola Bybit wobec LK0, bez oglądania cen.
   - Ścieżka odwrotu: wyłączyć cron i usunąć kopię. Dziennik się nie zmienia, zużyte odczyty: 0.

2. **Do połowy października: przygotować odczyt 25.12.**
   - Co zrobić: skrypt odczytu z poprawkami z sekcji 2, kryterium 4b (pasmo [13; 31] %/rok) i reguła wielokrotnego odczytu.
   - **[DECYZJA UŻYTKOWNIKA]:** czy kryterium 5 zmienia się z „opisowo” na „próg obalenia”; wybór korekty (z ≈ 2,39 na każdy odczyt albo próg wiążący dopiero po 12 mies.).
   - Dlaczego: bez liczb zapisanych przed grudniem odczyt będzie ręczny, a to pokusa ustalania reguły po wyniku.
   - Ścieżka odwrotu: skrypt tylko czyta pliki. Jeśli użytkownik odmówi, kryterium 5 zostaje opisowe.

3. **Poprawka 11 dziennika.**
   - **[DECYZJA UŻYTKOWNIKA]:** zgoda na zmianę kodu dziennika.
   - Rekomenduję `rozbicie.csv` (status ok). Opcjonalnie, każdy z własnym testem: `fazy.csv` z tych samych danych w pamięci oraz `koszyk.csv`.
   - Dlaczego: `data/raw/live` jest nadpisywany co noc, więc tego, co dziennik faktycznie policzył, nie da się odtworzyć później. Kontrola kosztów KO1 jest też potrzebna przed szczeblem 4. `koszyk.csv` pomoże w sprawdzianie 22.10–05.11.
   - Ścieżka odwrotu: pliki są tylko do dopisywania i nie wpływają na pozycje. Cofnięcie commita przywraca dziennik; test „historia zmieniona: 0” pilnuje, że liczby się nie ruszyły.

4. **Rejestr odczytów i zasada „pakiet przekrojowy = 0 odczytów”.**
   - Co zrobić: rejestr i `required_t(N, dsr)` (2–3 h, 0 wariantów, bez decyzji użytkownika). Każda przyszła pre-rejestracja wydrukuje wtedy próg t dla aktualnego N.
   - **[DECYZJA UŻYTKOWNIKA]** potrzebna tylko wtedy, gdy użytkownik mimo wszystko chce wydać jeden odczyt historii: zdjęcie STOP B1 albo nowa seria D1/E2. Moja rada: nie.
   - Ścieżka odwrotu: rejestr to plik i test. Nie zmienia żadnego wyniku.

5. **Później, przed szczeblem 4.**
   - Jednorazowy, opisowy pomiar kosztu spóźnionego wejścia na archiwum 1h (0 wariantów, wzorem KO1).
   - XT1 i L/S kont zostają jako pytania do użytkownika, bez pośpiechu. Żadne z nich nie zmienia decyzji o kapitale.

---

## 7. Jak powstał ten przegląd

Przegląd zaczął od map projektu: dane w repo, dziennik, silniki, katalog rodzin i rzeczy zapisane, ale nieuruchomione. Kandydatów szukano przez kilka soczewek (luki siatki pięciu pól, dane w repo, za mocno zamknięte serie, literatura, niezależna noga, dziennik) i przez trzy uzupełnienia po uwagach krytyka. Każdego kandydata sprawdziły trzy weryfikacje: powtórka (czy to już było), mierzalność (liczby) oraz mechanizm i dane; na końcu krytyk ocenił kompletność całości. Pięciu pierwszych kandydatów oceniły trzy osobne agenty, a pozostałych jeden agent w trzech osobnych soczewkach, bo przegląd dwa razy zatrzymał limit sesji. Krytyk wskazał 6 luk; uzupełniono 3 pierwsze (kolizje z zamknięciami, budżet odczytów pakietu przekrojowego, kolektory zależne od czasu), a z 11 nowych kandydatów zweryfikowano 8. Nieuzupełnione luki: sprawdzian danych na żywo wobec archiwum (już w STATUS.md, ETAP 5 pkt 3), czynnik wielkości i płynności (Amihud) oraz komórki: horyzont miesięczny, zmienność zmienności, BTC→ETH na 4h.

**Licznik: 35 kandydatów — ok 3, wątpliwych 18, odrzuconych 14.** Przegląd zużył 0 odczytów historii.

**Ograniczenia (według krytyka):**

- Czynnik wielkości, horyzont miesięczny, zmienność zmienności i para BTC→ETH na 4h nie mają własnych wpisów. Pojawiają się tylko na marginesie innych kart (wielkość: efekt w mikro-monetach; miesięcznie: n ≈ 66; BTC→ETH 4h: zamknięte kosztem, wn. 90).
- U 26 pierwszych kandydatów brakuje porządkowego pola „soczewka”.

**Przy okazji wykryte błędy w dokumentach** (poprawić bez licznika, notka w STATUS.md; zmiany w skillu przygotowuję ja, a wgrywa je użytkownik):

- `docs/rag/09` w wierszu X1 pisze „poza dziennikiem”, a X1 jest w dzienniku papierowym od 2026-09-25 (Poprawka 3).
- Mapa DANE twierdzi, że brakuje fundingu dla top-50 spoza koszyka. Sprawdzenie pokazało, że funding jest kompletny (378 symboli, 0 braków; RU2). Braki dotyczą tylko high/low dla miejsc 21–50.
- `families.md` nie ma rodziny low-vol/BAB, więc cytaty kart z tej rodziny nie istnieją. B3 to momentum rezydualne. D1 liczy TL1 jako „formę fundingu”, choć TL1 używał OI. Etykiety „LUKA-SIATKI-*” nie występują w repo.
- `required_windows` jest w `backtest/carry_probe.py`, a nie w `backtest/metrics.py`.

## 8. Sprawdzenie drugą drogą (Claude, po przeglądzie, 2026-09-27)

Kluczowe liczby przeliczone niezależnie od agentów przeglądu:

| Liczba z raportu | Sprawdzenie | Wynik |
|---|---|---|
| Oczekiwane maksimum t pustych pomysłów przy 41 odczytach 2,20; t dla DSR 0,95 = 3,84; DSR 0,80 = 3,04 | wzór Baileya–López de Prado na oczekiwane maksimum N rozkładów normalnych | 2,199; 3,84; 3,04; SR roczny na 5,5 roku 1,64 — **zgodne** |
| Pasmo zmienności R1 na odczyt po 92 dniach [13; 31] %/rok | kroczące okna 92 dni na historii portfela R1 (TS1 + CP1, reguła R1 z `sizing.apply_rules`, dane KR1 jak w PR1), po rozbiegu 60 dni | p2,5 12,3 %, mediana 21,6 %, p97,5 28,6 %; poza [13; 31] 5,1 % okien — **pasmo zgodne**; poza [15; 25] 32,2 % okien — raport zaniżał wadę węższego pasma (poprawione w sekcji 2) |
| LK0: ~68 tys. zdarzeń, 0 rozłączeń, brak kopii | `~/likwidacje/status.json` i przeszukanie dysku | 68 294 zdarzeń, 0 pominiętych, 0 rozłączeń; innej kopii brak — **zgodne** |
| `required_windows` leży w `backtest/carry_probe.py` | grep | **zgodne** |
| `docs/rag/09` opisuje X1 jako „poza dziennikiem” | odczyt wiersza X1 i Poprawki 3 w `dziennik/README.md` | **zgodne** — wiersz poprawiony w tym samym commicie |

Pasmo zmienności liczone na tej samej historii, na której ustalono regułę R1, więc jest odrobinę optymistyczne; na odczycie liczy się przede wszystkim błąd rzędu 1,5× (np. zły mnożnik), który pasmo [13; 31] wychwyci.
