# HS0 — Hyperliquid: funding od 2023-05-12 (BTC/ETH/SOL 3,4 roku), krótkie świece tylko ~5 000 wstecz, kolektor stanu rynku gotowy (19 MB/dobę), 2026-10-05

> **STATUS: ZAKOŃCZONA NA GAŁĘZI `zadanie-010-hl-stan-rynku`; przegląd 16c (orkiestrator, 2026-10-06): Approve
> z uwagami — uwagi 1–6 poprawione; czeka na scalenie.** Sonda wykonana według pre-rejestracji `a6f0fbc`; kontrola
> pozytywna **ZALICZONA** (20 z 20 monet); kolektor gotowy (dwie krótkie próby). **Scalenie do `master` = start
> kolektora** (cron klonu dziennika, jak LB0).
> **0 wariantów — POZA licznikami.** To brama danych (zbieranie i sprawdzenie źródła), nie pomiar hipotezy. Żadnego
> zestawienia z cenami Binance ani z wynikami strategii.

## W skrócie — prostym językiem (zasada 17)

Hyperliquid (HL) to giełda kontraktów perpetual (kontrakt bez daty wygaśnięcia; co godzinę jedna strona płaci drugiej
opłatę „funding”). Handlują tam inni ludzie niż na Binance. Chcieliśmy wiedzieć dwie rzeczy: ile historii da się
pobrać za darmo i czy da się tanio zapisywać stan rynku co minutę od dziś.

1. **Funding — historia jest, ale krótsza niż na Binance.** BTC, ETH i SOL: od 2023-05-12, czyli **3,4 roku**.
   Pozostałe 17 monet koszyka: od dnia wejścia monety na HL, **1,0–3,4 roku** (mediana 3,15; dla wszystkich 20 — 3,25). Przez pierwsze ~4 tygodnie
   (2023-05-12 → ~06-08) funding liczono co 8 godzin; potem co godzinę, prawie bez dziur (3 brakujące godziny w 3 latach).
2. **Świece — dzienne tak, krótsze tylko z ostatnich miesięcy.** Publiczne API oddaje najwyżej ~5 000 ostatnich
   świec danego interwału i nie pozwala sięgnąć głębiej: minutowe — **3,5 dnia**, godzinowe — **208 dni**,
   4-godzinne — **2,3 roku**. Dzienne — całość, ale uwaga: przed wejściem monety na HL API dokleja do ~1 000 dni
   świec **bez żadnej transakcji** (liczba transakcji 0, wolumen 0). To nie jest handel na HL i trzeba je odfiltrować.
3. **Koszyk top-20:** 20 z 26 symboli oznaczonych w pliku koszyka jako top-20 jest na HL (brak: TUT, CYS, AKE, BTW,
   LSK, QNT). **Monety wycofane z HL zachowują historię** (40 z 40 sprawdzonych; funding i świece urywają się
   razem, w okolicy dnia wycofania).
   Danych brakujących (BRAK DANYCH): **zero** w 415 zapytaniach.
4. **Kontrola pozytywna zaliczona:** stawka fundingu z historii i świeca minutowa zgadzają się z tym, co było widać
   na żywo tuż przed pełną godziną — **20 z 20 monet w obu testach**.
5. **Kolektor stanu rynku gotowy.** Co minutę zapisuje pełną odpowiedź `metaAndAssetCtxs` (stawka fundingu, cena
   mark/oracle/mid, premia, otwarte pozycje, obrót — 234 monety). Dwie próby po 3 migawki, 0 błędów,
   **18,7–19,0 MB na dobę**. Ruszy sam po scaleniu.

**Co to znaczy dla decyzji:** funding i premię HL da się badać na historii najwyżej **3,4 roku** (baza Binance ma
5,5 roku), a minutowy stan rynku (mark, oracle, otwarte pozycje) — dopiero od startu kolektora. Każdy pomysł na tych
danych to NOWA hipoteza z rachunkiem mocy przed odczytem. Ten raport niczego nie mierzy o zyskach.

## Metadane

- **ID:** HS0 (wolne w `runs/INDEX.md` 2026-10-05). Zadanie 010 tablicy (`zadania/010-hl-brama-danych-funding-premia.md`),
  typ `zbieranie_danych`. Decyzja użytkownika 2026-09-29: „Wszystkie 008–014”; 2026-10-05 orkiestrator: brama nie zależy
  od wyniku 004 (wniosek 115) i może startować.
- **Gałąź:** `zadanie-010-hl-stan-rynku` od `master` `7d085e6` (worktree wykonawcy). Bez push.
- **Sieć:** wyłącznie `https://api.hyperliquid.xyz/info` (POST, publiczne, bez klucza). Bez MCP Liquid, bez płatnych
  źródeł, bez dokumentacji z innych adresów (fakty o API w tym README pochodzą z cytatów LH0 albo z pomiaru tej sondy).
- **Plan kodu:** sonda jednorazowa `runs/2026-10-05_hs0-hl-stan-rynku/sonda_historii.py` (pełny stdout →
  `raw_output.txt`); kolektor `data/collect_hl_stan.py` (stan rynku co 60 s) + blok nadzoru w `tools/likwidacje.sh`;
  testy bez sieci. Dane kolektora POZA repo: `$HOME/likwidacje_hl/stan/` (zmienna `CLAS5_HL_STAN_DIR`).
- **Commity:** pre-rejestracja `a6f0fbc` (19:21:45 UTC — przed pierwszym zapytaniem sondy o 19:31:04); kod sondy
  i kolektora `2f1a6b1` (sonda uruchomiona na tym commicie, `sonda_historii.py` sha256 `ff8a6b9e…bcb57385`); testy,
  nadzór i próba kolektora `07c5b54`; wynik i dokumentacja `9d68835`; poprawki po przeglądzie 16c (kod) `f9e34ff` —
  powtórzona próba kolektora na tym commicie (`data/collect_hl_stan.py` sha256 `d4db539d…a745db6676b`); dokumentacja
  poprawek — commit zamykający gałąź.
- **Komendy** (z katalogu repo; w worktree wykonawcy interpreter `/home/dantey1/alpha/.venv/bin/python`):
  - `PYTHONUTF8=1 .venv/bin/python runs/2026-10-05_hs0-hl-stan-rynku/sonda_historii.py > runs/2026-10-05_hs0-hl-stan-rynku/raw_output.txt 2>&1`
    — 2026-10-05 19:31:04 → 20:41:34 UTC (z czekaniem na pełną godzinę dla kontroli pozytywnej);
  - `PYTHONUTF8=1 .venv/bin/python -m data.collect_hl_stan --dir "$(mktemp -d)" --max-cycles 3` — próba 1:
    2026-10-05 19:37:40 → 19:40:00 (kod roboczy sprzed `07c5b54`, bez zapisanego hasha); próba 2 po poprawkach 16c:
    2026-10-06 06:44:49 → 06:47:00 (commit `f9e34ff`, sha256 w pliku); oględziny katalogu (gzip -t, zcat, człony,
    `status.json`, `--status`) → `raw_output_kolektor.txt` (obie próby);
  - `PYTHONUTF8=1 .venv/bin/python runs/2026-10-05_hs0-hl-stan-rynku/druga_droga.py <plik dnia z próby kolektora>`
    — 20:42:55 → 20:55:30 UTC → `raw_output_druga_droga.txt` (bramka 16a).
- **Budżet wag sondy:** 18 809 wagi (liczonej ostrożnie: 20 + ⌈n/20⌉) w 415 zapytaniach, **0 × HTTP 429, 0 × 5xx,
  0 × BRAK DANYCH**; tempo z konstrukcji ≤ 500 wagi/min (odstęp 0,12 s na jednostkę wagi). Druga droga: ~140 zapytań
  co 5 s (≤ 480 wagi/min), uruchomiona po zakończeniu sondy.
- **Testy:** `tests/test_collect_hl_stan.py` (52 po poprawkach 16c, bez sieci, w tym 7 właściwości `hypothesis`),
  `tests/test_likwidacje_sh.py` (14; 6 nowych dla bloku HL, 1 rozszerzony).
- **Koszyk:** `dziennik/koszyk.csv` czytany przez `pd.read_csv(usecols=["symbol", "czlonek_top20"])`. Uwaga uczciwości:
  przy pierwszym oglądaniu nagłówka pliku (`head -3`) wykonawca zobaczył też 2 pierwsze wiersze wszystkich kolumn
  (miesiąc, pozycja, obrót, flaga fundingu dla BTCUSDT i ETHUSDT); żadna z tych wartości nie weszła do sondy ani do
  wniosków.

## Poprzedzające wyniki

- **Wniosek 110 (LH0 krok 0):** stan rynku `metaAndAssetCtxs` co 60 s ≈ 19 MB/dobę gzip (zrzut ~72 kB surowo,
  ~13,5 kB gzip; trzy zrzuty razem 40,1 kB — kompresja między zrzutami prawie nic nie daje) — wskazany jako tani krok.
- **Wniosek 115 (LH0 krok 1, zadanie 004):** darmowy kolektor likwidacji HL nie mieści się w limicie 1 200 wagi/min/IP;
  LH0 zamknięte. Funding i premia HL od tego nie zależą (osobna decyzja — ta runda). Z 115 bierzemy próg budżetu:
  średnio ≤ 600 wagi/min.
- **LB0 (wniosek 106):** wzór kolektora (plik per dzień UTC, `status.json`, `--status`, `flock` w katalogu danych,
  wyłącznik `WYLACZONY`, nadzór w `tools/likwidacje.sh`) i wzór README.
- **Wnioski 102 i 106:** źródło przyjmujemy dopiero po kontroli pozytywnej na żywo.
- **Jednym zdaniem, co z tego wynika dla projektu rundy:** runda nie dotyka likwidacji (E1 zamknięte, 116) ani cen
  Binance; sprawdza tylko, ile historii fundingu i świec daje publiczne API HL i czy zgadza się ono z tym, co widać na
  żywo, oraz uruchamia tani kolektor wskazany w 110 — w budżecie wag z 115.

## Pre-rejestracja (0 wariantów; zapisana przed pierwszym zapytaniem)

### Co mierzy sonda (pytania)

- **P1 — spis.** Liczba perpetuali w `meta` głównej giełdy (bez rynków HIP-3 z `perpDexs`), w tym z `isDelisted: true`.
- **P2 — funding (`fundingHistory`).** Dla każdej monety z zestawu S (niżej): najstarszy rekord (zapytanie od
  `startTime = 0`), najnowszy rekord (zapytanie od „teraz − 2 dni”), liczba rekordów w jednej odpowiedzi (limit strony),
  odstęp między kolejnymi rekordami (rozdzielczość). Dla BTC, ETH i SOL dodatkowo **pełne stronicowanie** całej historii
  (następny `startTime` = czas ostatniego rekordu + 1 ms): liczba rekordów, duplikaty, dziury (odstęp > 1,5 h), największa
  dziura, odstępy inne niż 1 h.
- **P3 — świece (`candleSnapshot`).** BTC, interwały 1m, 5m, 15m, 1h, 4h, 1d: zapytanie o okno [0, teraz] → liczba świec,
  pierwsza i ostatnia; zapytanie o okno starsze niż 5 000 świec danego interwału → czy cokolwiek wraca (czy da się
  stronicować wstecz, czy jest twardy limit głębokości). Dla każdej monety z S: świece 1d [0, teraz] → pierwsza
  i ostatnia (data startu notowań i koniec historii).
- **P4 — monety wycofane** (`isDelisted: true` w `meta`): czy funding i świece 1d nadal zwracają ich historię (pierwszy
  i ostatni rekord). Jeśli wycofanych jest > 40 — 40 pierwszych alfabetycznie (liczba wszystkich podana).
- **P5 — pokrycie koszyka top-20.** Symbole z `dziennik/koszyk.csv` z `czlonek_top20 = True` — czytane WYŁĄCZNIE kolumny
  `symbol` i `czlonek_top20`. Reguła nazwy (zapisana z góry, bez ręcznego dobierania po wyniku): `XUSDT` → `X`;
  `1000X` (X z samych liter) → `kX` (konwencja HL dla kPEPE, kSHIB, kBONK); inaczej brak dopasowania. Moneta jest „na HL”,
  gdy nazwa jest w `meta` (notowana albo wycofana). Wynik: ile z koszyka jest na HL i ile lat historii ma każda.
- **Zestaw S** = BTC, ETH, SOL + koszyk top-20 na HL + monety wycofane z P4.
- **„Lata historii”** = (najnowszy − najstarszy rekord) / 365,25 dnia, osobno funding i świece 1d; dla 1m i 1h —
  głębokość w dniach.

### Kontrola pozytywna (zgodność z odczytem na żywo; tolerancje z góry)

Zestaw kontroli: BTC, ETH, SOL + monety koszyka top-20 obecne (notowane) na HL. Jedna migawka `metaAndAssetCtxs`
w oknie [HH:59:00, HH:59:40] UTC.

- **K1 — funding.** Z migawki pole `funding` (r_ctx). Po pełnej godzinie H (od H + 30 s, ponawiane do H + 5 min)
  `fundingHistory` [H − 10 min, H + 10 min] → rekord z czasem w [H − 60 s, H + 60 s] (r_hist). Moneta zgodna, gdy
  **|r_hist − r_ctx| ≤ 1·10⁻⁶ + 0,25·|r_ctx|**. Uzasadnienie tolerancji: wychwytuje pomyłkę jednostek (×8 — stawka
  ośmiogodzinna zamiast godzinnej, ×100 — procenty), monety albo godziny; dopuszcza ruch premii w ostatniej minucie godziny.
- **K2 — świeca.** Z tej samej migawki `midPx` (gdy brak — `markPx`) w minucie M (minuta czasu odbioru odpowiedzi). Po
  zamknięciu minuty M świeca 1m o otwarciu M. Moneta zgodna, gdy **l·(1 − 0,002) ≤ midPx ≤ h·(1 + 0,002)** (pasmo
  20 pb na spread i ruch po migawce). Opisowo (bez progu): |c / midPx − 1| — mediana i maksimum.
- **Kontrola ZALICZONA**, gdy BTC, ETH i SOL są zgodne w K1 i w K2 ORAZ ≥ 80 % pozostałych monet zestawu jest zgodnych
  osobno w K1 i w K2. Inaczej NIEZALICZONA: historia z API nie jest przyjęta jako zgodna z tym, co widać na żywo (raport
  mówi, co się nie zgadza). Kolektor stanu może działać niezależnie od K1/K2 — zapisuje surową odpowiedź na żywo.

### Budżet wag i braki

- Średnio **≤ 500 wagi/min** (próg z 115: ≤ 600; limit HL 1 200/min/IP). Waga liczona ostrożnie: 20 + ⌈n/20⌉, gdzie
  n = liczba zwróconych pozycji, dla `fundingHistory` i `candleSnapshot` (dla świec HL dolicza mniej — przeszacowanie jest
  bezpieczne). Po każdym zapytaniu odstęp w·0,12 s. HTTP 429 i 5xx: odczekanie 5·2^k s (k = 0…4), potem BRAK DANYCH dla
  tej pozycji. Licznik wag i liczba 429 w `raw_output.txt`.
- **BRAK DANYCH** = brak odpowiedzi albo pusta lista tam, gdzie moneta jest na HL. Bez podmiany źródła, bez
  uzupełniania, bez szacowania braków.

### Kolektor stanu rynku (`metaAndAssetCtxs` co 60 s)

- **Co zapisuje:** pełną odpowiedź `metaAndAssetCtxs` (bez parametru `dex` = główna giełda) i czas: wysłania zapytania
  (`wyslano_ms`) i odbioru (`czas_ms`, ms UTC; `czas_utc` tekstem). JSON w ASCII. Odpowiedź sprawdzona przed zapisem:
  lista `[meta, konteksty]`, `meta.universe` to lista rekordów z nazwą, liczba kontekstów = liczba monet; czas odbioru
  w zakresie 2019–2100 (ta sama reguła co w zadaniu 021: `data/liquidation_time.event_time_ms`). Zła odpowiedź = nie
  zapisana, policzona w `status.json`.
- **Format (wybrany przed kodem):** plik dzienny `YYYY-MM-DD.jsonl.gz` (dzień UTC czasu odbioru). Każda migawka to
  osobny człon gzip z jedną linią JSON. Standard gzip dopuszcza wiele członów w jednym pliku: `zcat`, `gzip -dc`
  i Pythonowy `gzip.open` czytają je jako jeden ciągły tekst. Dlaczego tak: (1) plik dzienny bez dobowej kompresji
  i bez 1 440 plików na dobę; (2) awaria traci najwyżej bieżącą migawkę — człon dopisywany jednym zapisem + `fsync`,
  a przy starcie i po błędzie zapisu plik jest przycinany do końca ostatniego pełnego członu (urwany ogon nie psuje
  kolejnych migawek); (3) rozmiar jak w szacunku 110: ~13,5 kB na migawkę, ~19–20 MB na dobę.
- **Rytm:** co 60 s, wyrównane do pełnej minuty zegara UTC; błąd jednej migawki nie przerywa pętli (ponowienia po 429/5xx
  i błędach sieci z rosnącym odczekaniem, ale nie dłużej niż do następnej migawki); waga 20 na minutę = 1,7 % limitu IP.
- **Bezpieczeństwo:** tylko `https://` na stały adres, weryfikacja certyfikatu, bez przekierowań, limit rozmiaru
  odpowiedzi; `status.json` zapisywany atomowo; `--status`; jedna instancja (`flock` w katalogu danych — wspólna dla
  klonów `~/alpha` i `~/alpha-dziennik`); wyłącznik `WYLACZONY`.
- **Kryterium „gotowy”:** krótki przebieg `--max-cycles 3` do katalogu tymczasowego (`mktemp -d`; NIE do
  `$HOME/likwidacje_hl/stan`): 3 migawki, 0 błędów, plik przechodzi `gzip -t`, `zcat | wc -l` = 3, rozmiar migawki
  × 1 440 ≤ ~20 MB/dobę. Przekroczenie → zapisane jako minus, decyzja orkiestratora.
- **Start na stałe:** dopiero po scaleniu (cron klonu dziennika — jak LB0); robi orkiestrator, nie wykonawca.

### Czego NIE robimy

Żadnych cen Binance, żadnych zestawień HL vs Binance, żadnych wyników strategii, żadnej premii HL−Binance (to byłby
odczyt — osobna karta i decyzja). Żadnych likwidacji. Licznik wariantów: **0, POZA licznikami**; rejestr odczytów
historii: `bez-wyniku`, `odczyt_programu = nie`.

### Ścieżka odwrotu

Plik `$HOME/likwidacje_hl/stan/WYLACZONY` (cron przestaje startować kolektor, działający kończy się przy najbliższej
migawce), usunięcie bloku HL z `tools/likwidacje.sh`. Dane leżą poza repo — ich kasowanie to decyzja użytkownika.

## Wynik — sonda historii (pełny zapis: `raw_output.txt`)

### P1 — spis

- `meta` głównej giełdy: **234 perpetuale — 178 notowanych, 56 wycofanych** (`isDelisted`).
- `perpDexs`: 11 pozycji — główna giełda (`null`) i **10 rynków HIP-3** (osobne giełdy budowane na HL przez innych:
  xyz, flx, vntl, hyna, km, abcd, cash, para, mkts, io). Te rynki są POZA sondą i poza kolektorem (zapytanie bez
  parametru `dex` zwraca tylko główną giełdę).

### P5 — pokrycie koszyka top-20

W pliku koszyka **26 różnych symboli** ma `czlonek_top20 = True`. Jeden skład ma 20 monet, więc plik obejmuje więcej niż
jeden skład; kolumny miesiąca zgodnie z poleceniem nie czytano — to suma składów, nie jeden skład.

| wynik | symbole |
|---|---|
| na HL, notowane (**20**) | BTC, ETH, SOL, XRP, ZEC, HYPE, DOGE, BNB, TRUMP, ENA, kPEPE (← 1000PEPEUSDT), PUMP, ACE, SUI, ADA, LINK, NEAR, UNI, ARB, WLD |
| na HL, wycofane | 0 |
| brak na HL (**6**) | TUTUSDT, CYSUSDT, AKEUSDT, BTWUSDT, LSKUSDT, QNTUSDT |

Pokrycie **20/26 = 77 %**. Reguła „1000X → kX” zadziałała raz (kPEPE); innych symboli „1000…” w koszyku nie ma.

### P2 — funding (`fundingHistory`)

- **Rekord** = jedno rozliczenie: `coin`, `fundingRate` (stawka godzinowa, tekst), `premium` (premia, tekst), `time` (ms;
  pełna godzina + kilkadziesiąt ms). **Limit strony: 500 rekordów**; stronicowanie „następny `startTime` = ostatni
  czas + 1 ms” działa.
- **Rozdzielczość (druga droga, okna półmiesięczne):** maj 2023 — 60 rekordów, wszystkie co **8 h**; czerwiec 2023 —
  21 odstępów 8 h, potem co godzinę (przejście ~2023-06-08); **od lipca 2023 co godzinę**.
- **BTC, ETH, SOL — pełne stronicowanie:** po **29 259 rekordów** na 60 stronach, **2023-05-12 00:00 → 2026-10-05 20:00
  UTC = 3,40 roku**; 0 duplikatów. Godzin w tym okresie jest 29 829, więc brakuje 570 (1,9 %): **567 to okres
  8-godzinny** (maj–czerwiec 2023), 3 to pojedyncze brakujące godziny (2023-07, 2023-08, 2024-08); 5 rozliczeń ma czas
  przesunięty o 2–24 min (2023-05, 2023-09, 2023-12, 2× 2025-07). Liczby są identyczne dla trzech monet, bo rozliczenie
  jest wspólne dla całej giełdy; stawki są różne (pierwszy rekord: BTC −0,000613, ETH +0,000086, SOL −0,000237).
- **Koszyk (20 monet na HL):** funding od dnia wejścia monety na HL.

| moneta | pierwszy funding | lata | moneta | pierwszy funding | lata |
|---|---|---|---|---|---|
| BTC, ETH, SOL | 2023-05-12 | 3,40 | ACE | 2023-12-18 | 2,80 |
| DOGE, BNB, kPEPE, SUI, ARB | 2023-05-12 | 3,40 | ADA | 2023-10-22 | 2,96 |
| LINK | 2023-05-18 | 3,39 | NEAR | 2023-11-01 | 2,93 |
| XRP | 2023-06-18 | 3,30 | ENA | 2024-04-02 | 2,51 |
| WLD | 2023-07-24 | 3,20 | HYPE | 2024-12-05 | 1,83 |
| UNI | 2023-08-11 | 3,15 | TRUMP | 2025-01-18 | 1,71 |
| | | | PUMP | 2025-07-10 | 1,24 |
| | | | ZEC | 2025-10-02 | 1,01 |

  Podsumowanie: ≥ 3 lata — 12 z 20 monet; 2–3 lata — 4 (ACE, ADA, NEAR, ENA); < 2 lata — 4 (HYPE, TRUMP, PUMP, ZEC).
  17 monet poza BTC/ETH/SOL: min 1,01 / **mediana 3,15** / maks 3,40 roku (wszystkie 20 z BTC/ETH/SOL: mediana 3,25). Wszystkie kończą się na 2026-10-05 20:00.

### P3 — świece (`candleSnapshot`, BTC)

| interwał | świec dla okna [0, teraz] | najstarsza (UTC) | głębokość | okno starsze niż 5 000 świec |
|---|---|---|---|---|
| 1m | 5 113 | 2026-10-02 06:50 | **3,5 dnia** | 0 świec |
| 5m | 5 023 | 2026-09-18 09:30 | 17,4 dnia | 0 |
| 15m | 5 008 | 2026-08-14 16:15 | 52,2 dnia | 0 |
| 1h | 5 002 | 2026-03-11 11:00 | **208 dni** | 0 |
| 4h | 5 001 | 2024-06-24 12:00 | **2,3 roku** | 0 |
| 1d | 2 239 | 2020-08-19 | 6,1 roku (z doklejką, niżej) | nie dotyczy |

API oddaje **~5 000 ostatnich świec** (od 5 001 do 5 113 — granica nie jest dokładnie 5 000; nie badaliśmy dlaczego)
i ma **twardy limit głębokości**: okno starsze zwraca 0, więc stronicowania wstecz nie ma. Krótkich świec HL nie da się odzyskać później —
trzeba by je zbierać na bieżąco (kolektor stanu tego nie robi: zapisuje migawki, nie świece).

**Świece 1d sprzed wejścia monety na HL** (druga droga, punkt 4 — dopisany PO obejrzeniu wyniku, opisowo): BTC ma 996
świec dziennych sprzed pierwszego fundingu; **921 z nich (2020-08-19 → ~2023-02) ma 0 transakcji i 0 wolumenu**,
a ostatnie ~75 dni to już handel na HL (np. 2023-05-10: 3 110 transakcji) — HL handlował BTC przed pierwszym
zapisanym fundingiem. ZEC i ADA: po **999** świec sprzed fundingu, **wszystkie** z 0 transakcji. Dlatego kolumny „lata
świec 1d” w `raw_output.txt` (BTC 6,13; mediana koszyka 3,54; maks. wycofanych 4,86 — MKR) są **zawyżone** o doklejoną
historię bez handlu. Prawdziwa historia handlu zaczyna się mniej więcej przy pierwszym fundingu. Każde użycie świec HL
musi odfiltrować `n = 0`.

### P4 — monety wycofane

Sprawdzono **40 z 56** (pierwsze alfabetycznie: AI … PROMPT; poza próbą: RDNT, REQ, RLB, RNDR, SCR, SHIA, STG, STRAX,
TON, TST, UNIBOT, USTC, VINE, YZY, ZEREBRO, kDOGS). **40 z 40 ma funding i świece 1d** (0 BRAK DANYCH). Funding: min 0,16
roku (JELLY) / **mediana 1,33** / maks 2,72 (ARK); funding i świece urywają się razem w okolicy wycofania (np. MATIC
2024-09-11, FTM 2025-01-13, AI 2025-04-12). Wniosek: historia HL nie jest „tylko ocaleni” — monety wycofane są w API
(mniejsze ryzyko obciążenia ocalałych, czyli patrzenia wyłącznie na monety, które przetrwały).

### Kontrola pozytywna K1/K2 (migawka 2026-10-05 19:59:05.383 UTC, pełna godzina H = 20:00 UTC)

Zestaw: BTC, ETH, SOL + 17 notowanych monet koszyka = 20 monet.

- **K1 (funding): 20/20 zgodnych.** 14 monet ma po obu stronach dokładnie 0,0000125 (stawka bazowa HL — sama część
  odsetkowa, gdy premia jest mała). 6 pozostałych (SOL, ZEC, ENA, PUMP, NEAR, UNI) różni się o 2·10⁻⁸ … 3,8·10⁻⁷
  (0,08–4,6 % stawki; największa różnica NEAR: 4,875·10⁻⁵ na żywo, 4,913·10⁻⁵ rozliczone) przy tolerancji
  1,9·10⁻⁶ … 1,3·10⁻⁵. Rekord rozliczenia ma czas H + 65 ms. Wniosek: `fundingRate` z historii to ta sama godzinowa
  stawka, którą `metaAndAssetCtxs` pokazuje na żywo w polu `funding` (bez mnożnika 8 i bez procentów).
- **K2 (świeca 1m): 20/20 zgodnych.** `midPx` z migawki (5. sekunda minuty 19:59) leży w zakresie świecy 19:59 (± 20 pb)
  u wszystkich monet. Opisowo |zamknięcie / midPx − 1|: mediana 4,9 pb, maks. 64,7 pb (SUI — skok ceny pod koniec
  minuty; mid i tak w zakresie świecy).
- **Werdykt według pre-rejestracji: KONTROLA ZALICZONA** (BTC, ETH, SOL zgodne w K1 i K2; pozostałe 100 % i 100 %
  wobec progu 80 %).

### Budżet wag

18 809 wagi (liczonej ostrożnie) w 415 zapytaniach; **0 × 429, 0 × 5xx, 0 × BRAK DANYCH**; tempo ≤ 500 wagi/min
z konstrukcji (średnia z całego przebiegu 267/min, razem z czekaniem na pełną godzinę).

## Wynik — kolektor stanu rynku (próba; `raw_output_kolektor.txt`)

- **Format** jak w pre-rejestracji: plik `YYYY-MM-DD.jsonl.gz` (dzień UTC czasu odbioru), człon gzip na migawkę,
  linia JSON w ASCII: `czas_ms`, `czas_utc`, `wyslano_ms`, `odpowiedz` = pełne `[meta, konteksty]`. Meta: `universe`,
  `marginTables`, `collateralToken`. Kontekst monety: `dayBaseVlm`, `dayNtlVlm`, `funding`, `impactPxs`, `markPx`,
  `midPx`, `openInterest`, `oraclePx`, `premium`, `prevDayPx`.
- **Próba 3 cykli** (19:38, 19:39, 19:40 UTC, katalog z `mktemp -d`): 3 migawki; 0 błędów sieci, 0 odrzuconych,
  0 błędów zapisu, 0 ponowień; człony **13 145 / 13 186 / 13 244 B** gzip (72,3–72,5 kB surowo); średnio **13 192 B →
  19,0 MB/dobę** (kryterium „≤ ~20 MB” spełnione, zapas ~5 %); `gzip -t` OK; `zcat | wc -l` = 3; 0 bajtów spoza ASCII;
  234 monety w każdej migawce; czas odpowiedzi 333–817 ms (pierwsze zapytanie dłużej — nowe połączenie TLS).
- `status.json`, `kolektor.log` i `--status` działają (wydruk w `raw_output_kolektor.txt`). SIGTERM sprawdzony ręcznie
  (przed pierwszą migawką, bez zapytania do sieci): czyste wyjście, w logu „koniec: przerwanie”, status zapisany.
- **Wzrost:** ~56 B gzip na monetę na migawkę, czyli każda nowa moneta HL dokłada ~0,08 MB/dobę; 20 MB/dobę wypada przy
  ~246 monetach (dziś 234).
- **Próba 2 — po poprawkach z przeglądu 16c** (2026-10-06 06:45, 06:46, 06:47 UTC; commit `f9e34ff`, sha256 pliku
  kolektora `d4db539d6f9c4011c7f28f9dd52dcfbe40478e38b425e1e208fc1a745db6676b`): 3 migawki, 0 błędów, 0 ponowień,
  0 kopii ogona; człony **12 964 / 13 020 / 13 017 B** gzip, średnio **13 000 B → 18,7 MB/dobę**; `gzip -t` OK,
  3 linie, 0 bajtów spoza ASCII, `czytaj_dzien` bez ostrzeżenia; w logu „przy starcie sprawdzono: 2026-10-06.jsonl.gz”;
  `--status` pokazuje dziś i wczoraj. Próba 1 szła na kodzie roboczym bez zapisanego hasha — dlatego powtórzona.
- **Kryterium „gotowy” z pre-rejestracji: spełnione** (obie próby).

## Bramka 16a — walidacja write-upu (skill `data:validate-data` + `docs/skills/bramki-jakosci.md`)

**Przeliczenie drugą drogą (A3)** — `druga_droga.py`, osobny kod i inne zapytania niż sonda
(`raw_output_druga_droga.txt`):

| liczba | sonda | druga droga | zgodność |
|---|---|---|---|
| najstarszy funding BTC | 2023-05-12 00:00:00.048 (`startTime = 0`; pełne stronicowanie; okno 60 dni wcześniej puste) | 2023-05-12 00:00:00.048 (okna miesięczne od 2022-01) | ✓ co do ms |
| najstarszy funding ETH, SOL | 2023-05-12 | 2023-05-12 | ✓ |
| rekordów fundingu BTC do 2026-10-05 20:02:23 | 29 259 (pełne stronicowanie) | 29 259 (suma 83 okien półmiesięcznych) | ✓ co do sztuki |
| pokrycie koszyka | 20/26 (endpoint `meta`, reguła w kodzie) | 20/26 (meta z pliku kolektora — `metaAndAssetCtxs`; reguła jako wyrażenia regularne) | ✓, te same 6 poza HL |
| rozmiar dobowy | migawka z sondy 13 187 B gzip (własny kod) → 19,0 MB | średnio 13 192 B z pliku kolektora (rozmiar / linie) → 19,0 MB | ✓ |

**Kogo NIE ma w zbiorze (A2):**

1. **10 rynków HIP-3** — poza sondą i poza kolektorem.
2. **6 z 26 symboli koszyka** nie ma na HL (TUT, CYS, AKE, BTW, LSK, QNT).
3. **16 z 56 monet wycofanych** nie sprawdzono (poza próbą 40) — „wycofane mają historię” to 40/40, nie 56/56.
4. **Pierwsze tygodnie HL:** funding co 8 h do ~2023-06-08; handel BTC na HL przed 2023-05-12 (~75 dni) nie ma rekordów
   fundingu.
5. **Świece 1d sprzed notowania** (do ~1 000 dni, 0 transakcji) — to nie handel na HL; do odfiltrowania.
6. **Krótkie świece starsze niż ~5 000 interwałów** — niedostępne wcale (nie da się ich odzyskać później).
7. **Kolektor:** tylko główna giełda, tylko co 60 s (co dzieje się między migawkami, ginie), bez spotu, bez historii
   sprzed startu; minuty, gdy proces nie żyje (restart serwera — cron wznawia w ≤ 5 min).

**Czerwone flagi (A4):**

- *Identyczne liczby dla BTC, ETH i SOL* (29 259 rekordów, te same dziury) — sprawdzone: rozliczenie jest wspólne dla
  giełdy, a stawki są różne (pierwszy rekord BTC −0,000613, ETH +0,000086, SOL −0,000237), więc zapytania nie gubią
  wymiaru monety.
- *„Wynik idealnie potwierdza”* — 20/20 w K1 i K2. Tolerancje celowo łapią błąd jednostek, czasu albo monety, a nie drobny
  ruch premii; 14 z 20 monet ma po obu stronach stawkę bazową, więc dla nich K1 sprawdza tylko jednostki i czas. To
  słaby test treści, mocny test zgodności formatu — tak go czytamy.
- *Okrągłe liczby* — 500 (limit strony), ~5 000 (limit świec), 999 (świece bez handlu przed notowaniem ZEC i ADA) — to
  granice API, opisane wyżej.

**Werdykt 16a (Claude, wykonawca gałęzi): Caveats.** Zastrzeżenia, które czytelnik musi znać:

1. Świece 1d zawierają doklejoną historię bez handlu — „lata świec” z tabel sondy są zawyżone; historia handlu zaczyna
   się mniej więcej przy pierwszym fundingu.
2. Funding w maju–czerwcu 2023 co 8 h — szereg godzinowy zaczyna się ~2023-06-08 (~3,3 roku, nie 3,4).
3. Pokrycie koszyka liczone na 26 symbolach z kilku składów (bez kolumny miesiąca).
4. Kontrola pozytywna to jedna godzina i jedna minuta; próba kolektora — 3 minuty.
5. Kolektor ~19 MB/dobę, blisko progu 20 MB, i rośnie z nowymi monetami (~0,08 MB/dobę na monetę).

## Co na plus (+) / Co na minus (−)

**(+)**

- Funding HL ma **3,4 roku** historii (co godzinę od czerwca 2023), w każdym rekordzie także premię (`premium`); monety
  wycofane zostają w API — przyszła karta nie musi patrzeć tylko na „ocalałych”.
- Kontrola pozytywna 20/20 — historia to te same liczby co na żywo (jednostki, czas, moneta).
- Kolektor tani i odporny: 20 wagi/min (1,7 % limitu IP), 19 MB/dobę, bez kluczy; człon gzip na migawkę z naprawą
  urwanego ogona (uszkodzenia w środku pliku — do kopii `*.ogon-*`, nic nie znika), jedna instancja (`flock` w katalogu
  danych), wyłącznik, status; 52 testy bez sieci + 6 testów nadzoru.
- 0 × 429, 0 × BRAK DANYCH w 415 zapytaniach sondy.

**(−)**

- **Krótsza historia niż Binance** (3,4 wobec 5,5 roku bazy) — każda karta na historii HL ma mniejszą moc.
- **Brak historii stanu minutowego** (mark, oracle, mid, otwarte pozycje) — tylko prospektywnie, od startu kolektora.
- Świece 1m / 1h tylko 3,5 dnia / 208 dni wstecz; świece dzienne z doklejoną historią bez handlu.
- **Kopii poza serwerem brak — RYZYKO.** ~19 MB/dobę to ~7 GB/rok; to za dużo do repo kopii likwidacji (git).
  Awaria dysku serwera = utrata całej zebranej historii stanu, której nie da się pobrać ponownie. Miejsce kopii
  (dysk zewnętrzny, chmura) to decyzja użytkownika.
- Rozmiar blisko progu ~20 MB/dobę i rośnie z każdą nową monetą.
- Tylko główna giełda (bez HIP-3) i tylko co 60 s.

## Nadzór i uruchomienie

- **Start = scalenie do `master` + cron klonu dziennika.** Linia crona już istnieje (LK0/LB0):
  `*/5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje.sh`. Gdy klon dziennika pobierze `master`, najbliższy przebieg
  crona sam uruchomi kolektor HL w tle (blok 1c skryptu). Nikt nie robi osobnego kroku. Kto chce scalić bez startu:
  najpierw `mkdir -p ~/likwidacje_hl/stan && touch ~/likwidacje_hl/stan/WYLACZONY`.
- **Ręczny start** z dowolnego klonu: `nohup bash tools/likwidacje.sh >/dev/null 2>&1 &` (blokady w katalogach danych
  są wspólne — druga instancja żadnego kolektora nie wystartuje; działające kolektory Binance i Bybit nie są dotykane).
- **Stan:** `PYTHONUTF8=1 .venv/bin/python -m data.collect_hl_stan --status` — „ostatnia … s temu” poniżej ~120 s,
  błędy ~0, „pełnych migawek” rośnie o 60 na godzinę; powyżej 5 min bez migawki wydruk mówi „UWAGA”. Pokazuje plik
  dzisiejszy i wczorajszy (z nieczytelnym ogonem, jeśli jest) oraz pliki `*.ogon-*`.
- **Pliki `<dzień>.jsonl.gz.ogon-<ms>`:** powstają tylko, gdy przy naprawie za ostatnim pełnym członem leży coś innego
  niż urwana ostatnia migawka (uszkodzenie w środku pliku, śmieci). Zawierają odcięte bajty w całości — także poprawne
  migawki stojące za uszkodzeniem. Kolektor ich nie kasuje; co z nimi zrobić, decyduje użytkownik.
- **Wyłącznik:** plik `$HOME/likwidacje_hl/stan/WYLACZONY` — cron nie startuje kolektora, a działający kończy się przed
  następną migawką (≤ 60 s).
- **Katalog danych:** `$HOME/likwidacje_hl/stan` (zmiana: `CLAS5_HL_STAN_DIR`): `YYYY-MM-DD.jsonl.gz`, `status.json`,
  `kolektor.log`, `kolektor.out`, `.lock`. Odczyt: `zcat <plik> | head -1` albo `data.collect_hl_stan.czytaj_dzien`.

## security-review (zasada 19 — nowe połączenie sieciowe)

**0 podatności wysokich i średnich.** Przejrzane: `data/collect_hl_stan.py`, blok 1c w `tools/likwidacje.sh`,
`sonda_historii.py`, `druga_droga.py`. Sprawdzone: adres stały (`sprawdz_adres`: tylko `https`, host
`api.hyperliquid.xyz`, port 443, ścieżka `/info`, bez danych logowania — test na 8 złych adresach); TLS z weryfikacją
certyfikatu i nazwy hosta (`ssl.create_default_context`, test); przekierowania wyłączone, zmienne `*_proxy` ignorowane;
limit odpowiedzi 4 MB; parsowanie tylko `json.loads` (bez `eval`, `pickle`, YAML), `NaN`/`Infinity` odrzucane; nazwy
plików wyłącznie z lokalnego zegara po regule 2019–2100 — dane z sieci nie wpływają na ścieżki; zapis JSON w ASCII —
odpowiedź serwera nie rozbije linii pliku; w powłoce `$1` w cudzysłowach, katalog z zaufanej zmiennej środowiska;
`git rev-parse` w sondzie przez `subprocess` z listą argumentów; brak kluczy i sekretów. Przegląd zrobiony w tej sesji
bez podzadań (oszczędność tokenów, `docs/rag/12`: workflow wieloagentowe tylko na wyraźne życzenie). Poprawki po 16c
(2026-10-06) nie zmieniają warstwy sieciowej poza krótszym limitem czasu próby; nowe pliki `*.ogon-*` dostają nazwę
wyłącznie z nazwy pliku dnia i lokalnego zegara (dane z sieci nie wpływają na ścieżki).

## Bramka 16c (przegląd diffu przed scaleniem)

**16c (orkiestrator, 2026-10-06): Approve z uwagami — uwagi 1–6 poprawione** (na tej gałęzi, commit kodu `f9e34ff`):

1. **Ponowienia przesuwały migawki o minutę.** Termin ograniczał tylko START ponowienia, a próba trwała do 20 s —
   przy przeciążonym API migawki wypadały w minutach M, M+2, M+4. Teraz limit czasu KAŻDEJ próby to
   `min(20 s, czas do terminu)`, a próby krótszej niż 3 s (`MIN_PROBA_S`) się nie zaczyna; cała migawka kończy się
   przed terminem (start + 50 s). Test `test_przeciazone_api_nie_przesuwa_migawek` żąda minut M, M+1, M+2 i prób
   (+0 s, 20), (+22 s, 20), (+46 s, 4); test `test_klient_nie_zaczyna_proby_bez_czasu_na_nia`. Mutant bez przycinania
   limitu — oba testy czerwone.
2. **Naprawa ogona kasowała poprawne migawki za uszkodzeniem.** Teraz bez śladu odcinany jest tylko urwany początek
   JEDNEGO członu (`urwany_czlon`); każdy inny ogon najpierw trafia do `<plik>.ogon-<ms>` (zapis atomowy, kolejna kopia
   w tej samej milisekundzie nie nadpisuje poprzedniej), z wpisem „UWAGA” w logu, licznikiem `kopie_ogona` w statusie
   i ostrzeżeniem w `--status`. Testy: zły bajt w 2. z 5 członów — 3 poprawne człony zachowane w kopii; rozpoznanie
   urwanego członu; właściwość `hypothesis` (kopia = dokładnie odcięte bajty, albo brak kopii tylko dla urwanego członu).
3. **Wczorajszy plik z urwanym ogonem.** Przy starcie naprawiany jest plik dzisiejszy i najnowszy starszy (awaria o 23:59,
   serwer wyłączony przez północ albo kilka dni); `czytaj_dzien` czyta pełne człony i ostrzega `UrwanyOgon` zamiast
   rzucać `EOFError` dla całego dnia; `--status` pokazuje dziś i wczoraj. Testy: start naprawia najnowszy starszy plik
   (sprzed 3 dni), czytanie pliku z urwanym ogonem, status z wczorajszym nieczytelnym ogonem.
4. **Cofnięty zegar usypiał pętlę na godzinę.** Czekanie śpi najwyżej `okres_s` naraz, a gdy do terminu zostaje więcej
   niż okres (zegar cofnięty), termin liczy się od nowa. Test z zegarem cofniętym o 1 h: żaden sen > 60 s, 3 migawki
   w ~3,5 min. Mutant bez granicy snu — test czerwony.
5. **Test blokady Bybit przepuszczał błąd.** `test_hl_outliving_binance_keeps_only_its_own_lock` sprawdza teraz blokadę
   Bybit bez czekania: po wyjściu procesu Bybit (pid z piaskownicy), póki HL jeszcze żyje.
6. **Mediana i hash próby.** „Mediana 3,15” dotyczy 17 monet bez BTC/ETH/SOL (dla wszystkich 20 — 3,25) — dopisane
   w `runs/INDEX.md` (wiersz HS0, wniosek 117) i w tym README. Próba kolektora powtórzona po poprawkach na commicie
   `f9e34ff`, z sha256 pliku kolektora (`raw_output_kolektor.txt`, „PRÓBA 2”).

Po poprawkach: pełny pytest (OMP_NUM_THREADS=4, pipefail) — **2206 passed, 3 skipped, kod 0**; ruff + black czyste.

## Wniosek

Publiczne API Hyperliquid daje **godzinowy funding od czerwca 2023** (rekordy od 2023-05-12, pierwsze tygodnie co 8 h):
3,4 roku dla BTC, ETH i SOL i 1,0–3,4 roku dla pozostałych monet koszyka; 20 z 26 symboli koszyka jest na HL, a monety
wycofane zachowują historię. Historia zgadza się z tym, co widać na żywo (kontrola 20/20). Krótkich świec nie da się
odzyskać wstecz (~5 000 ostatnich), a dzienne trzeba czyścić z doklejonych dni bez handlu. Stanu rynku minuta po minucie
API nie przechowuje — dlatego kolektor `metaAndAssetCtxs` co 60 s: gotowy, przetestowany, ~19 MB/dobę, startuje po
scaleniu. Nic nie odczytano: żadnej premii HL−Binance, żadnego zwrotu.

## Rekomendacja

1. **Scalić po przeglądzie 16c, świadomie: scalenie = start kolektora.** Przy scaleniu (orkiestrator): zdanie w
   `STATUS.md` (kolektor HL od dnia scalenia, ryzyko braku kopii), sprawdzenie `--status` po kilku minutach.
2. **Kopia poza serwerem — decyzja użytkownika** (miejsce na ~7 GB/rok). Do tego czasu dane HL są tylko na serwerze.
3. **Przed jakąkolwiek kartą „funding/premia HL”:** rachunek mocy na ≤ 3,3 roku godzinowej historii (zasada 18), nowa
   seria z własnym licznikiem i progiem t z rejestru odczytów; świece HL tylko z `n > 0`.
4. **Opcjonalnie, osobna decyzja:** krótkie świece HL znikają po ~5 000 interwałach — gdyby były potrzebne, trzeba je
   zbierać na bieżąco (np. 1m raz na dobę dla 178 notowanych monet: ~180 zapytań po ~44 wagi, ~8 tys. wagi na dobę,
   średnio ~5–6 wagi/min).
5. Po tygodniu: `--status`, rozmiar plików, 1 440 migawek na dobę.

## Użyte skille (zasada 19)

### Użyte skille — gałąź `zadanie-010-hl-stan-rynku` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-10-05T19:13:22+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` |  |
| 2026-10-05T19:13:22+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` |  |
| 2026-10-05T19:13:23+00:00 | claude (agent: general-purpose) | `data:explore-data` |  |
| 2026-10-05T19:21:49+00:00 | claude (agent: general-purpose) | `engineering:testing-strategy` | data/collect_hl_stan.py — kolektor metaAndAssetCtxs Hyperliquid co 60 s (POST https, plik dzienny z członami gzip, przycinanie urwanego ogona, status.json, flock, WYLACZONY); testy bez sieci z wstrzy… |
| 2026-10-05T19:41:37+00:00 | claude (agent: general-purpose) | `security-review` |  |
| 2026-10-05T20:02:36+00:00 | claude (agent: general-purpose) | `data:validate-data` | HS0 (zadanie 010): sonda historii API Hyperliquid (fundingHistory, candleSnapshot: lata historii, pokrycie koszyka top-20, monety wycofane, BRAK DANYCH) + kontrola pozytywna K1/K2 + próba kolektora m… |

Razem: 6 wczytań, 6 różnych skilli: `anthropic-skills:clas5-quant`, `anthropic-skills:clas5-runda`, `data:explore-data`, `data:validate-data`, `engineering:testing-strategy`, `security-review`.

- **`anthropic-skills:clas5-runda`** — procedura rundy: pre-rejestracja przed pierwszym zapytaniem, 0 wariantów,
  katalog rundy, wiersz w INDEX, wniosek 117, rejestr odczytów historii.
- **`anthropic-skills:clas5-quant`** — nowe źródło danych: bez odczytu (żadnej premii HL−Binance), kontrola pozytywna
  źródła, a długość historii (3,4 roku) zapisana jako wejście przyszłego rachunku mocy.
- **`data:explore-data`** — profil nowego zbioru: rozdzielczość i dziury fundingu (8 h na starcie, 570 brakujących
  godzin), duplikaty, limity API, doklejone świece bez handlu (`n = 0`).
- **`engineering:testing-strategy`** — plan testów bez sieci (fałszywe `post`/`sleep`/`clock`, właściwości
  `hypothesis` — jedna znalazła przepełnienie w odczekaniu, poprawione) i testów nadzoru w piaskownicy.
- **`security-review`** — przegląd nowego połączenia sieciowego; wynik wyżej.
- **`data:validate-data`** — bramka 16a: druga droga pięciu liczb, „kogo nie ma w zbiorze”, czerwone flagi, werdykt
  Caveats.
- **`engineering:code-review`** (16c) — przegląd diffu przez recenzenta orkiestratora 2026-10-06 (wczytanie
  w `runs/skille/master.jsonl`, 06:22 UTC, bo recenzent pracował z głównego checkoutu); werdykt i uwagi 1–6
  w sekcji „Bramka 16c”.
- Momenty z tabeli zasady 19 bez skilla: `data:statistical-analysis` (16b) — runda nie ma efektów ani przedziałów
  (tylko daty, liczby rekordów i rozmiary), więc moment nie zachodzi; `quant-strategy-catalog` — brak nowej
  hipotezy; `dataviz` — brak wykresów.
