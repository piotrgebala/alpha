# HS0 — Hyperliquid: brama danych dla fundingu i stanu rynku (sonda historii + kolektor `metaAndAssetCtxs`), 2026-10-05

> **STATUS: PRE-REJESTRACJA — zapisana PRZED pierwszym zapytaniem sondy.** Wynik, wniosek i rekomendacja zostaną
> dopisane w kolejnych commitach tej gałęzi.
> **0 wariantów — POZA licznikami.** To brama danych (zbieranie i sprawdzenie źródła), nie pomiar hipotezy. Żadnego
> zestawienia z cenami Binance ani z wynikami strategii.

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
