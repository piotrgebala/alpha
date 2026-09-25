# KP1 — premia koreańska (Upbit) jako sygnał kierunku BTC na tydzień (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (zapisana przed zgodnością sygnałów i rachunkiem mocy; sekcje po
> przebiegu dopisane niżej). **Runda bez odczytu zysków (0 wariantów):** seria CP jest zamknięta
> regułą STOP, która zakazuje „innych giełd na tych samych danych” (`runs/INDEX.md`, liczniki).
> KP1 odpowiada tylko na dwa pytania: czy premia koreańska to NOWA informacja wobec CP1 i czy
> test na naszej historii w ogóle mógłby cokolwiek rozstrzygnąć (zasada 18).

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

_(sekcje poniżej po przebiegu `--moc`)_
