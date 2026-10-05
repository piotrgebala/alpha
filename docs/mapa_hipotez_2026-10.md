---
status: active
last_verified: 2026-09-29
depends_on: [rag/09_drabina_dowodow.md, rag/11_przeglad_kandydatow_2026-09-27.md]
zadanie: 007
---

# Mapa hipotez 2026-10: co jeszcze ma szansę być mierzalne

> **To nie jest runda i nie jest odczyt.** Nie pobrano żadnej ceny, nie uruchomiono backtestu, nie obejrzano
> żadnego wyniku strategii. Wszystkie liczby mocy (szansy, że prawdziwy efekt zostanie wykryty) policzono
> z parametrów, które już są w repo: wniosków w `runs/INDEX.md`, przeglądu `docs/rag/11` i znanych rozmiarów
> prób. Zużyte odczyty historii: **0**. Wiersza w `runs/odczyty_historii.csv` nie dopisano.

## 1. Odpowiedź w skrócie

1. Sprawdziłem 10 rodzin. **Żadna nie jest dziś MIERZALNA** na danych, które mamy. Sześć jest NIEMIERZALNYCH
   już na papierze, cztery mają status BRAK DANYCH.
2. Sześć rodzin na historii 2021–2026 (B3, B4, C1, D3, G1, Y2) przegrywa z tym samym progiem. Następny odczyt
   tej historii byłby 41. Dowód (DSR 0,95, czyli Sharpe skorygowany o liczbę prób) wymaga wtedy t ≈ 3,84,
   a to roczny SR (zysk na jednostkę ryzyka) ok. 1,64. Żadna z tych rodzin nie ma w repo ani w skillu źródła,
   które obiecywałoby taki efekt po publikacji.
3. Nawet przy zwykłym progu t 1,96, bez korekty na liczbę prób, moc tych sześciu rodzin wynosi 0–56 %.
   Nawet przy hojnych założeniach, które sam dopisałem, żadna nie przechodzi.
4. Cztery rodziny z BRAK DANYCH to E1 (likwidacje, dane zbierane od 2026-09-25), dwie rodziny z Hyperliquid
   oraz PT1 (surowce, obligacje). Działają na **nowych** danych albo na innej bazie. Mają więc własny licznik
   i niższy próg: t 1,96 zamiast 3,84 (na bazie tradfi t 2,16).
5. **Proponowana kolejność:** (1) karta E1 teraz, odczyt za rok (zadanie 011); (2) sonda historii
   Hyperliquid (010); (3) PT1 tylko wtedy, gdy użytkownik potrzebuje sprawdzianu mechanizmu, i tylko na
   pełnej bazie 1990–2026 (012); (4) Y2, G1, B3, B4, C1 i D3 zamknąć na papierze bez odczytu (013, 009, 008).

Co to znaczy dla decyzji: **żadne z zadań 008, 009 i 013 nie powinno dostać odczytu historii.** Jedyne
kroki, które mogą coś kiedyś rozstrzygnąć, to nowe dane (E1, HL) i czas.

## 2. Jak czytać tabele

- **Pięć pól** (katalog `quant-strategy-catalog`): zbiór informacyjny (z czego sygnał), formuła (jedno aktywo,
  przekrój rynku albo para), target (na co zakład), horyzont, status.
- **Filtr (a)–(f)** (ranking priorytetów katalogu): (a) na samym BTC efekt z badań po publikacji SR ≥ ~0,9;
  (b) przekrojowo IC ≥ 0,025 na top-50 (IC = korelacja rang sygnału ze zwrotem); (c) jedna reguła zapisana
  z góry; (d) średnia 7 dni startu przy rebalansie tygodniowym; (e) licznik odczytów programu do DSR;
  (f) kontrola pozytywna źródła danych (strumień albo plik, który na pewno nadaje).
  ✓ = spełnia, ✗ = nie spełnia, — = nie dotyczy, ? = nie wiadomo.
- **Moc, droga 1 / droga 2.** Droga 1 to funkcja projektu (`measurability_report`, `wald_half_width`)
  albo wzór analityczny. Droga 2 to wzór Walda przepisany ręcznie albo symulacja Monte Carlo (20 000 prób,
  stałe ziarno). Pełny wydruk: [`mapa_hipotez_2026-10_moc.txt`](mapa_hipotez_2026-10_moc.txt).
- **MDE** = najmniejszy efekt wykrywalny z mocą 80 %.
- **„Hojne założenie”** oznacza liczbę, której nie ma w literaturze w repo. Wpisałem ją celowo wyżej niż
  realistyczną. Jeśli rodzina przegrywa nawet z nią, werdykt nie zależy od brakującego źródła.
- **Korelacja oczekiwana** z obecnymi nogami (TS1 trend, CP1 premia Coinbase; X1 osobno w dzienniku).
  Wniosek 101 wymaga ≤ ~0,35. Zmierzone w repo są tylko: TS1–X1 0,35, TS1–CP1 0,24, X1–CP1 0,16 (wn. 95),
  nogi dziennika z rynkami tradycyjnymi |ρ| ≤ 0,15 (wn. 100), TR1–TS1 0,86 (wn. 74), premia ETH–BTC 0,95
  (wn. 80). Wszystko inne w tej kolumnie to **oszacowanie z analogii, nie pomiar**.

## 3. Tabela A — pięć pól i mechanizm

| Rodzina | Zbiór informacyjny | Formuła | Target | Horyzont | Status (katalog / INDEX) | Mechanizm jednym zdaniem |
|---|---|---|---|---|---|---|
| **B3** momentum resztowe | OHLCV wielu monet, po odjęciu czynnika rynku | przekrojowa top-50 | kierunek względny | tydzień | NIETKNIĘTE; wariant B1 pod STOP (X1, X2) | Informacja własna monety rozchodzi się wolno, więc jej względny ruch trwa dalej. |
| **B4** powrót reszty po PCA | OHLCV wielu monet, reszta po PCA | przekrojowa (koszyk) | powrót reszty | dzień–tydzień | NIETKNIĘTE; odrzucone w przeglądzie `docs/rag/11` §5 | Presja płynnościowa odsuwa monetę od koszyka, a market makerzy ją odwracają. |
| **C1** pary na kointegracji | ceny dwóch monet | parowa | spread | dni–tygodnie | NIETKNIĘTE; odrzucone w `docs/rag/11` §5 | Dwa aktywa o wspólnym czynniku wracają do stałej relacji cen. |
| **D3** basis kwartalny | basis perp vs kontrakt kwartalny | jednoaktywowa (BTC) | carry | kwartał | ZMIERZONE opisowo (D1, wn. 62); kierunek carry zamknięty decyzją użytkownika (wn. 61) | Kontrakt zamyka na wejściu stopę, którą perp płaci zmiennym fundingiem. |
| **G1** cykl fundingu 8h | zegar rozliczeń 00/08/16 UTC + znak fundingu | jednoaktywowa (BTC) | kierunek | 1 h przez rozliczenie | NIETKNIĘTE jako reguła | Płacący funding zamyka pozycję tuż przed rozliczeniem i na chwilę przesuwa cenę. |
| **Y2** kierunek BTC 1d | OHLCV własne BTC | jednoaktywowa | kierunek | dzień | niezmierzony (Y2: n 978, NIEROZSTRZYGNIĘTY przez n; wn. 69) | Opóźniona reakcja na informację daje trend dzienny. |
| **PT1** surowce, obligacje | dane rynku bazowego (krzywa terminowa, ceny) | przekrojowa / jednoaktywowa | carry albo trend | tydzień–miesiąc | nierozstrzygnięte (PT1 wn. 109; TX1 wn. 84) | Ktoś płaci za ubezpieczenie ceny (hedging producentów), więc carry z krzywej niesie premię. |
| **E1** kaskady likwidacji | likwidacje (Bybit pełne, Binance próbka, HL) | zdarzeniowa | powrót ceny po kaskadzie | 4 h – 3 dni | ZBIERANE dane (LK0 od 09-25, LB0 od 09-27; wn. 102, 106) | Likwidowany MUSI zamknąć po każdej cenie, więc cena przestrzeliwuje i wraca. |
| **HL-P** premia / funding HL vs Binance | ceny i funding tej samej monety na dwóch giełdach | jednoaktywowa (BTC) albo przekrojowa | kierunek | tydzień | NOWE; brak danych (zadanie 010) | Inna populacja traderów (portfele on-chain) zdradza popyt, jak premia Coinbase (C2). |
| **HL-L** mapa cen likwidacji | pozycje dużych adresów HL i ich ceny likwidacji | zdarzeniowa | kierunek do skupiska likwidacji albo powrót po nim | godziny–dzień | NOWE; brak danych (wn. 110: ~700 adresów możliwe, osobna decyzja) | Widoczne skupiska wymuszonych zamknięć przyciągają ruch, a po ich wyczyszczeniu cena wraca. |

## 4. Tabela B — filtr, efekt, moc, korelacja, DSR, werdykt

| Rodzina | Filtr a / b / c / d / e / f | Efekt po publikacji (źródło) | Kluczowa liczba mocy: droga 1 / droga 2 | Korelacja oczekiwana | Odczyt i próg t | **Werdykt** |
|---|---|---|---|---|---|---|
| **B3** | — / ✗ / ✓ / wymagane / 41. / ✓ | **BRAK ŹRÓDŁA** dla krypto po publikacji. Założenie projektu IC 0,010–0,015 (`docs/rag/11` §5); pomiar surowego momentum top-50 IC −0,006 (X2, wn. 68) | se IC 0,0078 (AU2); MDE 0,0219 przy t 1,96 i **0,0365 przy t 3,84**. Moc przy IC 0,015: wzór 0,485 / symulacja 0,484 (t 1,96); 0,027 / 0,029 (t 3,84). se drugą drogą: 0,143/√1971 × 2,1–2,4 = 0,0068–0,0077 | wysoka do X1 (ta sama rodzina, katalog błąd 3); do TS1 rzędu X1 (0,35) — analogia | 41. odczyt → t 3,84 (ostrożnie 53. → 3,94) | **NIEMIERZALNA** |
| **B4** | — / ✗ / ✓ / — / 41. / ✓ | **BRAK ŹRÓDŁA** po publikacji dla krypto. Założenie SR 0,5–0,9 (`docs/rag/11` §5) | Moc przy SR 0,9 na 5,5 roku: wzór 0,560 / symulacja 0,559 (t 1,96); **0,042 / 0,044 (t 3,84)**. Lat do mocy 80 %: 9,7 (t 1,96), 27,1 (t 3,84) | prawdopodobnie ujemna do TS1 i X1 (R1 tracił, gdy trend wygrywał, wn. 57) — analogia | 41. → t 3,84 | **NIEMIERZALNA** |
| **C1** | — / — / ✓ / — / 41. / ✓ | **BRAK ŹRÓDŁA**. Hojne założenie trafność 0,70 | n 29 transakcji na parę (`docs/rag/11`); 10 par przy ρ 0,86 to 1,14 pary efektywnej → n ≈ 33. `measurability_report(0.70, 0.625, 33)`: p_det 0,7956 / ręcznie 0,7951, **margines −9,6 pp**; symulowana moc 0,18 | nieznana; przy parach BTC/ETH blisko zera z konstrukcji (neutralna rynkowo) | 41. → t 3,84 | **NIEMIERZALNA** |
| **D3** | ✗ / — / ✓ / — / 41. / ✓ | **BRAK ŹRÓDŁA**. Hojne założenie P(basis > funding) = 0,60 | n 22 kontrakty (D1). `measurability_report(0.60, 0.50, 22)`: p_det 0,7089 / ręcznie 0,7089, **margines −10,9 pp**; symulowana moc 0,156 | nieznana (carry rośnie w hossie, jak trend) | 41. → t 3,84 | **NIEMIERZALNA** (i kierunek zamknięty decyzją, wn. 61) |
| **G1** | ✗ / — / ✓ / — / 41. / ✓ | **BRAK ŹRÓDŁA** w literaturze. Założenie przeglądu p 0,509 (`docs/rag/11` §5, bez podanego źródła) | n 6 022 zdarzeń, σ 1 h 0,70 % (wn. 108), koszt 0,08 % → p* 0,5716. `measurability_report(0.509, 0.5716, 6022)`: p_det 0,5842 / ręcznie 0,5842, **margines −7,5 pp**; moc symulowana 0,000. Forma zwrotu: brutto potrzeba 0,105 % na zdarzenie (se 0,0090 %, symulacja 0,0089 %) | bliska zera (pozycja 1 h, 3 razy dziennie) — analogia | 41. → t 3,84 | **NIEMIERZALNA**; nieopłacalna przy każdym n (p 0,509 < p* 0,572) |
| **Y2** | ✗ / — / ✓ / — / 41. / ✓ | Trend po publikacji SR ~0,3–0,5 na portfelu wielu rynków (Hurst–Ooi–Pedersen 2017 wg `runs/2026-09-24_tx1-trend-inne-rynki/README.md`); dla samego BTC 1d **BRAK ŹRÓDŁA** | Forma zwrotu 5,5 roku: MDE SR 1,19 (t 1,96), **2,00 (t 3,84)**; moc przy SR 0,5: wzór 0,216 / symulacja 0,218 (t 1,96), 0,004 / 0,003 (t 3,84). Forma trafności: `measurability_report(0.5104, 0.5170, 978)` p_det 0,5483 / ręcznie 0,5483, margines −3,8 pp | wysoka do TS1 i CP1, jeśli reguła trendowa (obie trzymają BTC w hossie) — analogia | 41. → t 3,84 | **NIEMIERZALNA** |
| **PT1** | — / — / ? / ? / własny (tradfi N = 2) / ✗ | Trend po publikacji SR ~0,3–0,5 (jak Y2). Carry surowców i obligacji po publikacji: **BRAK ŹRÓDŁA** | 1990–2026: MDE SR 0,467 (t 1,96), 0,501 (t 2,16); moc przy SR 0,5: wzór 0,851 / symulacja 0,845. **Po 2013: MDE 0,757**; moc przy SR 0,5: 0,456 / 0,455 | ≤ 0,15 (nogi dziennika vs rynki tradycyjne, wn. 100) — tylko jeśli PT1 byłby nogą, a nie sprawdzianem | baza tradfi: 2. odczyt → t 2,16 | **BRAK DANYCH** (krzywej terminowej nie ma w repo) |
| **E1** | ? / — / ✓ (karta 011) / — / własny (N = 1) / ✓ Bybit, próbka Binance | Mechanizm jakościowo (Coval–Stafford 2007, Brunnermeier–Pedersen 2009 wg `docs/rag/11`); liczby efektu dla krypto: **BRAK ŹRÓDŁA** | σ 5 % na 24 h, 150–300 epizodów/rok (założenie do sprawdzenia z liczników): **MDE po 1 roku 0,93–1,32 %** (symulacja 0,91–1,29 %), po 3 latach 0,49–0,69 %. Koszt w kaskadzie 0,3–1 % | bliska zera do nóg tygodniowych (zdarzenia godzin–dni) — analogia | nowe dane: t 1,96 (DSR 0,95 przy N = 1 daje 1,64) | **BRAK DANYCH** (zbierane; odczyt ≥ 2027-09) |
| **HL-P** | ✗ / ? / ✓ / wymagane / własny / ✗ | **BRAK ŹRÓDŁA**. Najbliższy analog CP1: SR 0,89 w próbie, po DSR 0,52 (wn. 96) — górna granica | Na nowych danych MDE SR 2,80 / 1,98 / 1,62 po 1 / 2 / 3 latach; moc przy SR 0,89: wzór 0,142 / 0,242 / 0,338, symulacja 0,151 / 0,248 / 0,343. Przekrój top-50: MDE IC 0,051 / 0,036 / 0,029 (symulowana moc przy MDE 0,800 / 0,795 / 0,800) | nieznana; do CP1 zmierzyć zgodność znaku przed czymkolwiek (lekcja KP1, wn. 91) | własny licznik: t 1,96 | **BRAK DANYCH** (głębokość historii HL nieznana — sonda 010) |
| **HL-L** | ? / — / ? / — / własny / ✗ | **BRAK ŹRÓDŁA** | Nie da się policzyć: nieznana częstość zdarzeń („cena dotyka skupiska”). Wzór jak E1: MDE = 2,80·σ/√n | prawdopodobnie wysoka do E1 (ta sama klasa zdarzeń) | własny licznik: t 1,96 | **BRAK DANYCH** (brak kolektora pozycji) |

## 5. Rodzina po rodzinie — krótko i prostym językiem

### B3 — momentum resztowe (zadanie 008)

Karta 008 wymaga efektu z badań po publikacji IC ≥ 0,025. Takiego źródła nie ma ani w repo, ani w skillu.
Jedyne liczby to założenie przeglądu (IC 0,010–0,015) i pomiar zwykłego momentum na top-50: IC −0,006.
Przyrząd AU2 widzi IC 0,022 przy zwykłym progu. Po korekcie na 41 odczytów potrzeba IC 0,0365, czyli 2,4× więcej
niż górne założenie. Przy IC 0,015 szansa wykrycia z korektą to ok. 3 %.
**Wniosek dla decyzji:** odczyt B3 zużyłby próbę i podniósł próg dla wszystkich następnych, a prawie na pewno nic by nie rozstrzygnął.

### B4 — powrót reszty po PCA

Założony SR 0,5–0,9 daje na 5,5 roku moc 22–56 % przy t 1,96 i 0,4–4 % przy t 3,84. Do mocy 80 % trzeba 10–88 lat.
Do tego R1 i X1 pokazały, że ruchy względne w krypto trwają, a nie wracają (wn. 57, 64).
**Wniosek:** nie startuje.

### C1 — pary na kointegracji

Na jedną parę przypada 16–29 transakcji w 5,5 roku. Dziesięć par to przy korelacji 0,86 nieco ponad jedna para
niezależna. Przedział trafności ma wtedy ±17 pp. Nawet hojna trafność 70 % nie wystarcza, bo trzeba ok. 80 %.
**Wniosek:** nie startuje; wersja koszykowa to B4 (też nie).

### D3 — basis kwartalny

W repo są 22 kontrakty. Pytanie „czy basis bije funding” ma przy n = 22 przedział ±21 pp, a hojne założenie
to 60 % wobec wymaganych 71 %. Użytkownik zamknął kierunek carry (wn. 61: „nie o takie zwroty mi chodzi”).
**Wniosek:** nie startuje.

### G1 — cykl fundingu 8h (zadanie 009)

Zdarzeń jest dużo (6 022), więc sam przyrząd jest dokładny: ±1,26 pp. Problem jest gdzie indziej. Koszt 0,08 %
wobec typowego ruchu w godzinie 0,56 % daje próg opłacalności 57,2 % trafności. Założenie z przeglądu to 50,9 %.
To kryterium sprawdziłem też w granicy dużego n (zasada 18): nawet przy nieskończonej próbie 50,9 % < 57,2 %,
więc reguła traci niezależnie od liczby zdarzeń. W jednostkach zwrotu: ruch na zdarzenie musiałby wynosić
brutto ≥ 0,105 % (0,122 % z korektą DSR).
**Wniosek:** zamknąć bez odczytu (zgodnie z kartą 009: „jeśli NIEMIERZALNA po kosztach → zamknąć”).

### Y2 — kierunek BTC na świecy dziennej (zadanie 013)

To akapit, o który prosi karta 013.
Filtr (a) wymaga efektu po publikacji SR ≥ ~0,9. Najlepsze źródło w repo to trend na wielu rynkach po publikacji:
SR 0,3–0,5, i to dla zdywersyfikowanego portfela, a nie jednego aktywa. Na 5,5 roku przyrząd widzi SR 1,19 przy
zwykłym progu i SR 2,00 po korekcie na 41 odczytów. Przy SR 0,5 szansa wykrycia to 22 % bez korekty i 0,4 % z nią.
W formie trafności wynik jest ten sam: SR 0,5 odpowiada trafności ok. 51,0 %. Próg opłacalności Y2 to 51,7 %,
a wykrywalne jest dopiero 54,8 % (n 978) lub 53,9 % (reguła bez modelu, n 2 007).
**Wniosek:** NIEMIERZALNA; formalnie domknąć bez odczytu (0 odczytów, wniosek do `runs/INDEX.md` dopisuje orkiestrator
przy scaleniu 013).

### PT1 — surowce i obligacje (zadanie 012)

Nie ma danych krzywej terminowej, więc carry surowców ma BRAK DANYCH. Rachunek warunkowy na bazie tradfi:
na pełnych 36 latach przyrząd widzi SR ≈ 0,47–0,50, a na samym okresie po 2013 dopiero SR 0,76.
Szczebel 1 drabiny pyta, czy mechanizm żyje **po publikacji**. Przy SR 0,3–0,5 odpowiedź po 2013 ma moc tylko 20–46 %.
**Wniosek:** sama brama danych ma sens tylko wtedy, gdy użytkownikowi potrzebny jest ten sprawdzian. Jeśli tak,
to z góry trzeba przyjąć, że okres po 2013 prawdopodobnie znów wyjdzie „nierozstrzygnięty”, jak w TX1.

### E1 — kaskady likwidacji (zadanie 011)

Tylko ta rodzina ma mocny mechanizm i dane, które przybywają. Po roku (po odjęciu 90 dni rozbiegu) przyrząd widzi
ruch 0,9–1,3 % na epizod przy rozrzucie 5 % i 1,5–2,1 % przy rozrzucie 8 %. Koszt w kaskadzie to 0,3–1 %.
Rodzina jest więc mierzalna po 1–3 latach tylko przy efekcie ≥ ok. 1 %. Liczbę epizodów (150–300 rocznie) trzeba
potwierdzić z samych liczników zdarzeń, bez cen.
**Wniosek:** zapisać kartę teraz (zadanie 011), zanim ktokolwiek zestawi likwidacje z cenami.

### HL-P — premia i funding Hyperliquid vs Binance (zadanie 010)

Nie wiemy, ile historii daje API Hyperliquid. Bez historii przyrząd na nowych danych widzi po roku dopiero SR 2,8.
Nawet analog CP1 (SR 0,89, zawyżony, bo wybrany z wielu prób) daje po 3 latach moc 34 %. W wersji przekrojowej
po 3 latach potrzeba IC 0,029 — i to tylko wtedy, gdy HL pokrywa top-50, czego nie wiemy.
**Wniosek:** najpierw tania sonda historii (010). Werdykt MIERZALNA jest możliwy tylko wtedy, gdy historia ma ≥ 3 lata
i pokrywa koszyk.

### HL-L — mapa cen likwidacji

Brak kolektora pozycji i nieznana częstość zdarzeń. Nie ma z czego liczyć mocy.
**Wniosek:** BRAK DANYCH; ewentualnie dołączyć jako opis do E1 (tak mówi karta 011: „stan pozycji przed kaskadą
tylko jako opis, nie druga zmienna”).

### ML1 — ML na rzadszym handlu, 11 cech (zadanie 028, krok 0, dopisane 2026-09-30)

Jeden model XGBoost (parametry jak SW etap 2) na 11 cechach zapisanych z góry: 4 cechy wykresu (REVERSION) i 7 cech
spoza wykresu z SW, na świecy dziennej BTC, pozycja do bariery 1,5 × ATR albo 7 dni. Opcja A użytkownika: uczenie
2021–2025, model zamrożony, 2026 do dnia zamrożenia = rozbieg, test prospektywny (tor P) od dnia zamrożenia.
Próg opłacalności p\* (trafność, przy której zysk pokrywa koszt 0,08 %) to 50,9 %. Ślad z SW przeliczony z 12 godzin
na 7 dni daje realnie ok. 50,8–52,1 % trafności (założenie: ruch rośnie jak pierwiastek czasu).
Na historii (tor H, próg t 3,84) potrzeba co najmniej 55,5 % trafności nawet w najhojniejszym wariancie — NIEMIERZALNA.
Na nowych danych (próg 1,96) BTC staje się mierzalny po ok. 19 latach przy trafności 53 % i po ok. 5 latach przy 55 %
(środkowe założenia: 37,8 % dni bez transakcji, transakcje 7-dniowe nachodzą na siebie → niezależnych 2× mniej).
Panel top-20 (~3 niezależne monety) jest dokładnie 3× szybszy, ale nie pokonuje kary AU2 za model i ma gorszą bramę
danych — wybrana formuła: BTC. 5 z 11 cech (OI, proporcja kont long/short, przewaga kupujących, VRP, podaż
na giełdach) nie ma dziś zbieracza na żywo na serwerze. Karta: `runs/DRAFT_028.md`, wydruk: `runs/DRAFT_028_moc.txt`.
**Wniosek:** tor H zamknięty bez odczytu; tor P formalnie uczciwy, ale werdykt nie przyjdzie w rozsądnym czasie →
rekomendacja: zamknąć bez odczytu (jak 013), modelu nie uczyć. Decyzja użytkownika.

## 6. Proponowana kolejność

| Krok | Rodzina / zadanie | Dlaczego | Odczyty historii |
|---|---|---|---|
| 1 | E1 — karta pre-rejestracji (011) | dane rosną z czasem; kartę trzeba zapisać przed zestawieniem z cenami | 0 |
| 2 | HL-P — sonda historii (010) | tania; rozstrzyga BRAK DANYCH w jedną albo drugą stronę | 0 |
| 3 | PT1 — brama danych (012), tylko na życzenie | sprawdzian mechanizmu, nie noga; po 2013 moc < 50 % | 0 na krypto; 1 na bazie tradfi |
| 4 | Y2 (013), G1 (009), B3 (008), B4, C1, D3 | NIEMIERZALNE na papierze — zamknąć bez odczytu | 0 |
| — | HL-L | czeka na decyzję o kolektorze pozycji (wn. 110) | 0 |

Statusów zadań 008–013 nie zmieniałem. To decyzja użytkownika.

## 7. Czego nie dało się ustalić

- **BRAK ŹRÓDŁA** (efekt z badań po publikacji): B3, B4, C1, D3, G1, Y2 na samym BTC, carry surowców i obligacji,
  liczby efektu E1 dla krypto, HL-P, HL-L. Nie szukałem w sieci (zadanie jej nie wymaga). Źródło może istnieć poza repo.
  Werdykty NIEMIERZALNA nie zależą jednak od tej luki, bo rodziny przegrywają nawet z hojnymi założeniami.
- **BRAK DANYCH:** krzywa terminowa surowców (PT1), głębokość historii i pokrycie koszyka Hyperliquid (HL-P),
  pozycje dużych adresów HL (HL-L), realna częstość kaskad (E1 — po 4–6 tygodniach z liczników).
- **Korelacje** nowych rodzin z nogami są oszacowaniami z analogii. Żadnej nie zmierzono.
- Założenie p 0,509 dla G1 pochodzi z `docs/rag/11` §5 bez podanego źródła.

## 8. Bramki jakości (16a, 16b)

- **Druga droga każdej liczby mocy:** każdy wiersz ma dwie wartości (funkcja projektu / Wald ręcznie albo wzór /
  symulacja). Różnice ≤ 0,01 w mocy i ≤ 0,0005 w progu wykrywalności. Wyjątek: przy n 33 dla C1 `measurability_report`
  zaokrągla n do liczby całkowitej (33), a wzór ręczny używa 32,98 — różnica 0,0005.
- **Kogo nie ma w zbiorze:** rodzin wykluczonych danymi (on-chain i sentyment per moneta, J2/F1 — decyzja
  „płatne: nie”), rodzin zamkniętych STOP (A1–A5, B1, B2, D1, D2, E2, G2, H1, J1). Mapa ich nie ocenia ponownie.
- **Czerwona flaga „wynik idealnie potwierdza hipotezę”:** wynik „nic nie jest mierzalne na historii” zgadza się
  z oczekiwaniem (wn. 96, 107). Dlatego sprawdziłem go z hojnymi założeniami i przy progu t 1,96 bez korekty.
  Werdykt się nie zmienia. Powód jest strukturalny: 5,5 roku danych i 40 odczytów, a nie dobór parametrów.
- **Zakresy, nie punkty:** moc podaję dla dolnej i górnej wartości założeń (np. IC 0,010 / 0,015 / 0,025,
  σ 5 / 8 %, 150 / 300 epizodów).
- **Licznik:** 0 wariantów, 0 odczytów; N programu bez zmian (40 metodą AU4, 52 ostrożnie).
- **Werdykt bramki 16a: Caveats.** Rachunek jest powtarzalny i sprawdzony drugą drogą. Założenia efektów pochodzą
  jednak z przeglądu projektu, a nie z literatury po publikacji (BRAK ŹRÓDŁA), a korelacje są z analogii.

## 9. Jak powtórzyć

Z katalogu głównego klonu, bez sieci (ok. 5 s):

```
.venv/bin/python docs/mapa_hipotez_2026-10_moc.py > docs/mapa_hipotez_2026-10_moc.txt
md5sum docs/mapa_hipotez_2026-10_moc.txt     # a06740ba26468648cd9f6781c0e7b29b (numpy/scipy z requirements-lock.txt)
.venv/bin/python -m backtest.dsr --k 1       # próg t 3,84 (N 41) i 3,94 (N 53)
```

Pojedyncze wywołania z tabeli (to samo, co drukuje skrypt):

```
.venv/bin/python -c "from backtest.metrics import measurability_report as m; \
print(m(0.5104, 0.5170, 978)); print(m(0.509, 0.5716, 6022)); \
print(m(0.70, 0.625, 33)); print(m(0.60, 0.50, 22))"
```

Skąd wejścia: p* 0,5170 i n 978 — Y2 (wn. 69); σ 1 h 0,70 % — OS1 (wn. 108); koszt 0,08 % — SW (wn. 90);
se IC 0,0078 i sd IC dziennego 0,143 — AU2 (wn. 92, README AU2); n 22 kontrakty — D1 (README D1, Q3);
16–29 transakcji na parę, IC 0,010–0,015, SR 0,5–0,9, σ i częstość epizodów E1, p 0,509 — `docs/rag/11`;
ρ 0,86 — TR1 vs TS1 (wn. 74); SR 0,89 — CP1 t 2,09 / √5,5 (wn. 72); SR po publikacji 0,3–0,5 —
README TX1; progi t — `backtest/dsr.py` (wn. 107).
