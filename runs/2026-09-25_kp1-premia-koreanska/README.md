# KP1 — premia koreańska (Upbit) jako sygnał kierunku BTC na tydzień (2026-09-25)

> **STATUS: ZAMKNIĘTA — NIEMIERZALNA, zysków nie liczono (zasada 18); 0 wariantów.** Sygnał
> koreański to NIE ten sam sygnał co CP1 (zgodność znaku 52,8 %, przedział ~[46; 60] %, przypadek
> dałby 50,1 %), ale test na 5,1 roku BTC widzi dopiero efekty ≥ ±30,9 %/rok (0,86 SR), a uczciwy
> efekt z badań to ~+5 %/rok (SR 0,15) → moc 5 % (= szansa fałszywego alarmu). Pre-rejestracja
> `d909076` → `--moc` w tym samym poleceniu. Walidacja (16a): **Caveats**; przegląd diffu (16c):
> **Approve**. Premia koreańska wypada z listy „Otwarte”.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Na koreańskiej giełdzie Upbit bitcoin zwykle kosztuje trochę więcej niż na świecie („premia
kimchi”), bo Koreańczycy nie mogą swobodnie wywozić pieniędzy za granicę. Premia Coinbase (CP1,
popyt z USA) dała nam jedyny dodatni wynik w projekcie, więc pytanie brzmi: czy ta sama reguła na
premii koreańskiej coś mówi o następnym tygodniu BTC? Zanim policzymy cokolwiek na zyskach,
sprawdzamy dwie rzeczy: (1) czy sygnał koreański nie jest po prostu tym samym sygnałem co CP1
(jak ETH/SOL w CP2), (2) czy przy uczciwie założonym efekcie test w ogóle byłby w stanie go
zobaczyć. Przegląd badań mówi: kierunku nikt nie zmierzył, premia raczej podąża za ceną, niż ją
wyprzedza, a od 2024 r. mierzy ogólny napływ wonów do krypto, nie popyt na BTC. Stąd założony
efekt jest mały — około 6 razy mniejszy od tego, co nasz przyrząd potrafi zobaczyć.

## ID testu

**KP1** — rodzina „popyt spoza Binance”, seria CP (CP1 zapisał z góry: „inne giełdy = warianty”).
Seria CP: 1/1, STOP — KP1 **nie zużywa** wariantu, bo nie odczytuje zysków; odczyt wymagałby
decyzji użytkownika o zdjęciu STOP (nowa seria KP z własnym licznikiem).

## Metadane

- Branch: `kp1-premia-koreanska` (z `master` 2026-09-25, po `16cb1b6`).
- Dane (lokalne, zasada 20 — od 2021-01-01): Upbit KRW-BTC 1d (`data/raw/external/upbit_KRW-BTC_1d.parquet`,
  pobrane 2026-09-25 przez `py -m data.fetch_korea`), FRED `DEXKOUS` (kurs USD/KRW, noon New York,
  dni robocze USA; tym samym poleceniem), spot Binance BTC-USDT 8h i perpetual BTCUSDT 1d + funding
  jak w CP1. Okno i start jak w CP1: premia od 2021-01-01, ocena 2021-05-01 → 2026-06-30.
- Kod: `data/fetch_korea.py` (nowy moduł — `fetch_external.py` używa dziennik, więc bez zmian w nim),
  `backtest/run_upbit_kp1.py` (importuje zamrożone `daily_premium`, `premium_signal`, `_shifts` z CP1;
  premia = cena Upbit przeliczona na dolary kursem z dnia ≤ d, potem wzór CP1), testy
  `tests/test_fetch_korea.py` (5) + `tests/test_upbit_kp1.py` (6, w tym test właściwości `hypothesis`
  „kurs bez przyszłości”; mutacja „kurs z następnego dnia” łapana przez 3 testy).
- Komendy: `PYTHONUTF8=1 py -m backtest.run_upbit_kp1 --profil` → `profil.txt`;
  `PYTHONUTF8=1 py -m backtest.run_upbit_kp1 --moc` → `raw_output.txt`. Tryb bez flagi (zyski)
  istnieje w kodzie, **nie jest uruchamiany** w tej rundzie.
- Środowisko: serwer Linux, `.venv` z `requirements-lock.txt` (XGBoost 3.2 — przebudowany 2026-09-25,
  wcześniej 3.4; ta runda XGBoost nie używa).

## Poprzedzające wyniki

- **CP1** (wniosek 72): premia Coinbase 7 vs 90 dni → +32 %/rok [+2; +62], t_neff 2,09; po korekcie
  na ~28–31 odczytów nieistotna; half-width tego przyrządu na BTC ±31,5 %/rok (0,90 SR).
- **CP2** (wniosek 80): na ETH/SOL sygnał = sygnał BTC w 94 % / 89 % dni → NIEMIERZALNA; lekcja:
  przed replikacją zmierz zgodność SYGNAŁÓW.
- **SH1** (wniosek 81): na 5,5 roku danych dziennych nowe zakłady kierunkowe zwykle niemierzalne;
  filtr: efekt z badań PO publikacji ≥ 1,4 × niepewność. KU1 (udział Korei w obrocie jako ranking)
  NIEMIERZALNY — to inna formuła (przekrojowa) niż KP1 (znak premii na BTC).
- **ADR-09:** KP1 NIE jest szczeblem 1(b) dla CP1 (tamten wymaga danych niezależnych od krypto) —
  sprostowanie planu z 2026-09-24.
- `runs/INDEX.md`, liczniki: seria CP STOP — „zakazane: inne okna, progi, giełdy na tych samych danych”.

## Przegląd badań (przed pre-rejestracją) — `literatura.md`

Workflow: 3 niezależne kierunki (badania akademickie, praktycy i dostawcy danych, zmiany
regulacyjne i fakty o danych) → osobny weryfikator źródeł per kierunek → synteza tylko ze źródeł
potwierdzonych. 28 źródeł zweryfikowanych, 18 odrzuconych lub poprawionych. Najważniejsze:
- **Nikt nie zmierzył, czy premia koreańska przewiduje globalny BTC** w horyzoncie dzień–miesiąc
  (poza jednym artykułem CryptoSlate 2025: przejścia przez zero → +1,7 % w 7 dni, bez liczby
  zdarzeń i testu, w środku naszej próby).
- Mechanizm przemawia raczej przeciw „popyt koreański wyprzedza”: premia rośnie PO wzrostach BTC
  (Choi, Lehar & Stauffer: +0,135 × wczorajszy zwrot), Korea ma mały udział w ustalaniu ceny
  (Makarov & Schoar 2019).
- Od 2024-06-07 (USDT za wony na Upbit) premia BTC ≈ premia USDT (korelacja ~0,999, własne
  sprawdzenie agenta, niezweryfikowane) — sygnał mierzy ogólny napływ wonów, nie popyt na BTC.
- Co najmniej 3–4 zmiany reżimu w próbie (2021 SFTA, 2022 travel rule, 2024 USDT, 2026 przewaga
  dni z ujemną premią).
- **Kontaminacja (jawnie):** agenci widzieli ruchy BTC po znanych epizodach premii (np. −40 % po
  kwietniu 2021) i średni zwrot BTC w oknie artykułu 2025; **zysków reguły KP1 nikt nie liczył.**

## Pre-rejestracja

- **Hipoteza (do zmierzenia tylko po zdjęciu STOP):** znak(średnia premii koreańskiej z 7 dni −
  średnia z 90 dni) przewiduje kierunek BTC w następnym tygodniu.
- **Kierunek:** `DIRECTION = +1` (jak CP1: premia ponad normą → long). Badania kierunku nie
  ustalają; odwrotny znak („kontrariański”) byłby osobną hipotezą, nie wariantem. Rachunek mocy
  nie zależy od kierunku.
- **Mechanizm (jednym zdaniem):** koreański popyt detaliczny zamknięty kontrolą kapitału podnosi
  lokalną cenę, zanim arbitraż przeniesie go na rynek światowy — prior SŁABY (patrz wyżej).
- **DOKŁADNIE JEDNA zmienna wobec CP1:** źródło premii (Upbit + USD/KRW zamiast Coinbase USD).
  Reszta = CP1 co do bajtu (okna 7/90, silnik TS1, 7 faz, koszt z config, realny funding).
- **Założony efekt:** `ASSUMED_SR = 0,15` (zakres 0–0,3; ≈ +5 %/rok przy zmienności reguły ~35 %/rok),
  z syntezy badań; wynik CP1 (SR ~0,9) traktowany jako górna granica z klątwy zwycięzcy.
- **Kryterium mierzalności (zasada 18, jak CP1/CP2):** MIERZALNA, gdy założony efekt (%/rok) ≥
  half-width 95 % (z 1,96) z rozrzutu 100 portfeli H0 (sygnał przesunięty cyklicznie o losową
  liczbę tygodni); inaczej NIEMIERZALNA. Dodatkowo moc przy SR 0,15 i przy SR 0,9.
  **Granica dużego n:** half-width → 0, więc każdy efekt > 0 staje się mierzalny — kryterium nie
  karze celu rundy.
- **Kryterium nowej informacji (zgodność znaku KP1 z CP1, dni wspólne):** ≥ 80 % = ta sama
  informacja co CP1 (jak CP2); < 65 % = nowa informacja; pomiędzy = częściowo wspólna.
  Opisowo: zgodność z trendem 28 dni na BTC.
- **Reguła decyzji:**
  - NIEMIERZALNA → runda zamknięta, 0 wariantów, zysków nie liczymy; premia koreańska wypada
    z listy „Otwarte” w `runs/INDEX.md`.
  - MIERZALNA i nowa informacja → rekomendacja dla użytkownika: zdjęcie STOP dla jednego odczytu
    (nowa seria KP 1/1) albo dopisanie do dziennika papierowego (wymaga źródła kursu na bieżąco —
    `DEXKOUS` publikowany raz w tygodniu).
  - MIERZALNA i ta sama informacja → zamknięta jak CP2.
- **Czego runda NIE robi:** nie liczy zysków, nie stroi okien ani progów, nie łączy z CP1/TS1.

## Profil danych (`data:explore-data`) — `profil.txt`

| zbiór | wiersze | zakres | luki / duplikaty | uwagi |
|---|---|---|---|---|
| Upbit KRW-BTC 1d | 2 824 | 2019-01-01 → 2026-09-24 | 0 / 0 | świeca 00:00–24:00 UTC (09:00 KST), jak Coinbase/Binance; 0 dni z wolumenem 0 |
| FRED DEXKOUS | 2 013 dni roboczych | 2019-01-02 → 2026-09-18 | 85 pustych (święta USA) | 1 081,6–1 556,0 KRW/USD; max zmiana dzienna 3,64 % (2022-11-14, po CPI USA — prawdziwy ruch) |
| kurs dla dni 2021-01 → 2026-06 | — | — | 0 dni bez kursu | wiek obserwacji: mediana 0 d, max 3 d (weekend + święto) |

**Premia koreańska** (2 007 dni, 2021-01-01 → 2026-06-30): p1 / p5 / mediana / p95 / p99 =
−2,27 / −1,10 / **+1,66** / +6,82 / +12,48 %; min −6,13 % (2021-02-03, kilka tygodni „odwrotnej
premii” z rzędu), max +21,71 % (2021-05-19, krach, szczyt fali 9–17 % z maja 2021); 39 dni
|premia| > 10 % (wszystkie w 2021); mediana per rok: 2021 +3,33 %, 2022 +1,54 %, 2023 +1,47 %,
2024 +2,17 %, 2025 +1,42 %, 2026 +0,16 %. Oba skrajne dni przeliczone ręcznie (cena Upbit,
spot Binance 16:00, kurs z tego dnia) — zgodne.
**Wobec premii Coinbase** (2 007 wspólnych dni): korelacja poziomów **+0,11**, zmian dziennych
−0,14 — w przeciwieństwie do CP2 (0,95) to w dużej mierze inny szereg.

## Przegląd bezpieczeństwa (zasada 19: nowe połączenie sieciowe)

`security-review` (wbudowany) na diffie gałęzi: **brak znalezisk.** HTTPS z weryfikacją
certyfikatu (`http_get` odrzuca inne schematy), stały host, parametry przez `urlencode`,
`json.loads` bez wykonywania kodu, stała nazwa pliku wyjściowego, brak kluczy i sekretów.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Premia koreańska **nie jest** tym samym sygnałem co premia Coinbase: w ~53 % dni oba wskazują
ten sam kierunek, czyli tyle, ile dałby przypadek. Ale nasza historia (5 lat BTC) jest za krótka,
żeby sprawdzić, czy ten sygnał cokolwiek przewiduje. Test widzi dopiero przewagę rzędu ±31 %
rocznie, a to, czego uczciwie można się spodziewać po badaniach, to ok. +5 % rocznie. Szansa, że
test wykryje taki efekt, wynosi 5 % — tyle samo, ile szansa fałszywego alarmu. **Wynik zysków nic
by nie rozstrzygnął, więc go nie liczymy.** To samo wiedzieliśmy ogólnie z SH1 (wniosek 81);
KP1 potwierdza to na konkretnym, porządnie przygotowanym źródle.

## Wynik

Pełny stdout: `raw_output.txt` (33 s). Okno oceny 2021-05-01 → 2026-06-30.

| miara | wartość | co z tego wynika |
|---|---|---|
| dni premii / braki w sygnale | 2 007 / 0 | dane kompletne |
| sygnał: long / zmiana znaku | 44,0 % dni / 4,3 % dni (~81 zmian, średnio ~23 dni jednego znaku) | sygnał wolny, ~80 niezależnych „epizodów” |
| **zgodność znaku z CP1** | **52,8 %** na 1 887 dniach; przypadek przy tych udziałach long: 50,1 %; przedział 95 % (bootstrap blokowy, bloki 30–180 dni) ~[45,8; 60,2] % | NIE ta sama informacja co CP1 (80 % daleko poza przedziałem); zgodność nieodróżnialna od niezależności |
| zgodność z trendem 28 dni na BTC | 45,9 % (CP1: 63,7 %) | sygnał koreański NIE jest ukrytym trendem; lekko przeciw niemu |
| zmienność H0 | 35,8 %/rok | jak CP1 (35,1 %) |
| **half-width 95 %** | **±30,9 %/rok = 0,86 SR** | najmniejszy efekt, który test w ogóle odróżnia od zera |
| q97,5 H0 (100 przesunięć) | +22,8 %/rok | — |
| **moc przy SR 0,15 (≈ +5,4 %/rok)** | **5 %** | = poziom fałszywego alarmu → **NIEMIERZALNA** |
| moc przy SR 0,9 (wynik CP1, górna granica) | 53 % | nawet efekt jak CP1 — rzut monetą |
| moc w całym zakresie z badań (SR 0–0,3) | ≤ ~10 % | werdykt nie zależy od wyboru 0,15 w tym zakresie |

**Werdykt wg pre-rejestracji: NIEMIERZALNA** (+5,4 %/rok < 30,9 %/rok). Kryterium nowej
informacji: 52,8 % < 65 % → „nie ta sama informacja co CP1”. Tryb z zyskami nie był uruchamiany.

**Sprostowania do opisu w pre-rejestracji (bez zmiany kryteriów):**
- Half-width to w praktyce dolna granica `1,96 · σ / √n` (0,358 · √(365/1880) · 1,96 = 30,92 %/rok),
  a nie rozrzut 100 portfeli H0 — ten był mniejszy (wszystkie przesunięcia dzielą tę samą ścieżkę
  BTC), więc skrypt bierze `max(...)`. Tak samo w CP1/CP2. Przy trwałych pozycjach błąd z korektą
  na autokorelację byłby raczej większy — to tylko wzmacnia NIEMIERZALNA.
- „Nowa informacja” w pre-rejestracji = „nie ta sama informacja co CP1”. Zgodność mówi, że sygnały
  się różnią, a nie że koreański niesie informację o BTC.
- Liczba źródeł: 30 zweryfikowanych, 19 odrzuconych lub poprawionych (nie 28/18).
- Progi 80/65 % zapisano po obejrzeniu profilu (korelacja poziomów premii +0,11) — przy wyniku
  52,8 % z przedziałem ~[46; 60] % nie ma to wpływu na odczyt.

## Co na plus (+) / Co na minus (−)

**(+)**
- Rachunek mocy przed wynikiem — zero odczytów zysków, zero zużytych wariantów, precedens CP2/SC1.
- Nowe, czyste źródło: 2 824 dni Upbit bez luk, kurs z dnia ≤ d (test właściwości + mutacje),
  oba skrajne dni przeliczone ręcznie, liczby odtworzone niezależnie (16a) co do 0,3 pp.
- Sprawdzona odrębność od CP1 z uwzględnieniem trwałości sygnału (bootstrap blokowy), nie
  naiwnym przedziałem dwumianowym (~3× za wąskim).
- Przegląd badań z weryfikacją źródeł — założony efekt ma źródło, nie jest liczbą z głowy.

**(−)**
- **Werdykt był przesądzony przed przebiegiem:** synteza badań porównała swój prior z znaną
  czułością przyrządu (0,9 SR z CP1) i napisała „NOT MEASURABLE” przed zamrożeniem SR 0,15.
  To zgodne z zasadą 18 (prior z niezależnego źródła), ale przebieg nie dodaje dowodu ponad SH1.
- **Kontaminacja (pełna):** agenci przeglądu badań widzieli znak sygnału KP1 w kwietniu–sierpniu
  2021 (long w maju, short w czerwcu–sierpniu) i ścieżkę BTC w tym czasie — to nieformalny odczyt
  zysku w epizodzie, który sam może przesądzić wynik. Kierunek odwrotny („kontrariański”,
  `DIRECTION = −1`) na 2021–2026 jest przez to **spalony** (post hoc). Zysków reguły nikt nie liczył.
- Zdanie „premia raczej podąża za ceną” opiera się na próbie sprzed 2019 (Choi, Lehar & Stauffer,
  średnie dzienne ceny); nasze dane w horyzoncie reguły tego nie pokazują (zgodność z trendem 45,9 %).
- Ujęcie serii: KP1 to wariant serii CP z definicji CP1 („inne giełdy = warianty”), zablokowany
  STOP-em; niezależnie od tego odczyt blokuje już sama zasada 18 (NIEMIERZALNA).

**Kogo nie ma w zbiorze (16a):**
- styczeń–kwiecień 2021: rozbieg średniej 90 dni (w tym tygodnie „odwrotnej premii” do −6 %) —
  pierwsze oceniane tygodnie to artefakt bazy, wzrost z kwietnia 2021 poza oceną;
- od 2024-06-07 (~25 z 62 miesięcy): premia BTC ≈ premia USDT na Upbit (korelacja ~0,999 wg agenta,
  **niesprawdzona u nas** — wymaga świec KRW-USDT) → sygnał mierzy napływ wonów, nie popyt na BTC;
- tylko Upbit (bez Bithumb, Coinone, Korbit; Upbit ~85 % obrotu wg Kaiko 2023);
- kurs `DEXKOUS`: noon New York, weekend = piątek (do ~56 h), artefakt ~−2 pp w dniu stanu wojennego
  (3.12.2024); publikowany raz w tygodniu → **reguły nie da się policzyć na bieżąco** tym kursem.

## Walidacja (16a) i statystyka (16b)

`data:validate-data` + niezależny agent (bez importu kodu rundy, własne skrypty z surowych plików):
dni wspólne 1 887, zgodność 52,84 %, z trendem 45,89 %, long 43,99 %, zmiana znaku 4,29 %,
mediana premii +1,66 %, korelacja poziomów +0,111, half-width 30,93 %/rok — **wszystko zgodne**.
Przesunięcia cykliczne sygnału CP1 (≥ 30 dni): zgodność mediana 49,6 % [42,0; 59,5] — 27 %
przesunięć daje ≥ 52,8 %. Sceptyk werdyktu: **werdykt się broni, ocena Caveats** (zastrzeżenia
wpisane wyżej). **Werdykt 16a: Caveats.**
`data:statistical-analysis`: efekt i przedziały zamiast samego p; moc z rozkładu normalnego
`P(Z > 1,96 − SR/se)`, `se = hw / 1,96 / σ`; przedział zgodności z bootstrapu blokowego i z
efektywnej próby AR(1) (~197 dni, ±7 pp) — zbieżne. Licznik: 0 wariantów (seria CP 1/1 bez zmian).

## Przegląd diffu (16c)

`engineering:code-review` wczytany PRZED przeglądem; przegląd agenta + osobny sceptyk dla każdego
znaleziska. Bez błędów w kodzie produkcyjnym (czas kursu, świeca 16:00, stronicowanie, formuła mocy,
użycie zamrożonych funkcji CP1 — sprawdzone, w tym ręcznie 4 dni). Poprawione po przeglądzie:
- test premii miał stały kurs → nie łapał kursu z przyszłości podanego przez `korea_premium`
  (potwierdzone mutacją) — teraz kurs zmienia się codziennie + ręczny dzień weekendowy; mutacja
  „kurs z d+1” łapana przez 3 testy;
- test stronicowania nie sprawdzał wczesnego stopu ani filtra daty startu (potwierdzone mutacją) —
  nowy test, obie mutacje łapane;
- zabezpieczenie: kursor stronicowania musi się cofać, inaczej `ValueError` (test).
Odrzucone przez sceptyków: „zgodność bez poziomu przypadku” (sugestia wydruku — poziom przypadku
podany w README), „czerwone strażniki na gałęzi” (stan zamierzony do zamknięcia rundy).
Testy: 13/13 nowych; ruff/black czyste.
**Werdykt jednym zdaniem: Approve** — nowy kod liczy premię bez zaglądania w przyszłość i używa
zamrożonych funkcji CP1 bez kopii, a luki testowe wskazane w przeglądzie są zamknięte i sprawdzone mutacjami.

## Wniosek

**Prostym językiem:** premia koreańska to inny sygnał niż premia Coinbase, ale na naszych pięciu
latach danych nie da się sprawdzić, czy działa — nawet gdyby działała tak, jak sugerują badania,
test by tego nie zauważył. Nie liczymy więc zysków i nie dopisujemy tego sygnału do niczego.

**Technicznie:** NIEMIERZALNA (moc 5 % przy SR 0,15; half-width 0,86 SR); zgodność z CP1 52,8 %
[~46; 60] — sygnał prawie niezależny od CP1 i od trendu 28 dni. Kierunek odwrotny spalony
(kontaminacja w przeglądzie badań). Od 2024-06 sygnał mierzy napływ wonów (USDT), nie popyt na BTC.

## Rekomendacja

1. **Zamknąć KP1: 0 wariantów, seria CP bez zmian (1/1, STOP).** Premia koreańska wypada z listy
   „Otwarte” w `runs/INDEX.md`.
2. **Nie dopisywać premii koreańskiej do dziennika papierowego.** Przy efekcie ~SR 0,15 dziennik
   nie rozstrzygnąłby niczego przez lata, a `DEXKOUS` nie daje kursu na bieżąco.
3. Wniosek ogólny (do wniosku 81): kolejne sygnały kierunkowe na samym BTC z 5 lat danych
   dziennych wymagają priorytetu SR ≥ ~0,9 z badań PO publikacji — inaczej rachunek mocy zamyka
   je przed startem. Przed kolejnym „nowym źródłem popytu” najpierw ten filtr, bez pobierania danych.

## Użyte skille

Rejestr `runs/skille/kp1-premia-koreanska.jsonl` (`py tools/skill_audit.py raport --galaz
kp1-premia-koreanska`): **10 wczytań, 9 różnych skilli.**

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | kolejność: profil i moc przed wynikiem; pre-rejestracja w osobnym commicie przed `--moc` |
| `anthropic-skills:clas5-quant` | zasada 18 dla portfela dziennego (rozrzut szeregu), pułapki czasu kursu, „nowa cecha = nowa hipoteza” |
| `anthropic-skills:quant-strategy-catalog` | pięć pól (ta sama rodzina co CP1, inna giełda = wariant), mechanizm przed danymi, brama danych |
| `data:explore-data` | profil Upbit / `DEXKOUS` / premii: luki, duplikaty, skrajne dni sprawdzone ręcznie |
| `engineering:testing-strategy` | plan testów bez sieci + test właściwości „kurs bez przyszłości” + mutacje |
| `security-review` | nowe połączenie (Upbit): brak znalezisk |
| `data:validate-data` | niezależne przeliczenie (inny kod), „kogo nie ma w zbiorze”, pełne ujawnienie kontaminacji |
| `data:statistical-analysis` | przedział zgodności przy trwałym sygnale (bootstrap blokowy zamiast dwumianu), moc w zakresie priorytetu |
| `engineering:code-review` | Approve + 2 luki testowe zamknięte (mutacje), zabezpieczenie kursora |

Pominięte z tabeli zasady 19: `dataviz` (bez wykresu), `ta-toolkit` / `lean-research` (nie dotyczy),
`engineering:debug` (brak błędu o niejasnej przyczynie).
