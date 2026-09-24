# X1F — X1 w wersji 7 faz + X1 w dzienniku papierowym (2026-09-24)

> **STATUS: ZAMKNIĘTA — zapis porządkowy, 0 wariantów.** X1 liczony jako średnia 7 faz (siedem kopii
> startujących w kolejne dni tygodnia): **+9,5 %/rok [−21,1; +40,1], t_neff 0,61** — dawne +41,7 %/rok
> (t 1,86) to jedna faza z siedmiu (poniedziałek); pozostałe dni: od −1,3 do +21,6 %/rok. X1 traci status
> kandydata na historii (wniosek 89). Decyzją użytkownika X1 (7 faz) trafia mimo to do dziennika papierowego
> jako osobna reguła od 2026-09-25 (poprawka 3). Przy sprawdzianie wykryta i poprawiona usterka dziennika:
> filtr nazw odrzucał monety z nazwą spoza ASCII (poprawka 4).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

X1 to reguła „co tydzień kup 5 monet, które najmocniej rosły przez ostatnie 4 tygodnie, i sprzedaj
5 najsłabszych”. Dotąd liczyliśmy ją z przebudową koszyka zawsze w poniedziałek. Wyszło +42 % rocznie.
Ten sam test z przebudową w każdy z pozostałych 6 dni tygodnia daje od −1 do +22 % rocznie. Uczciwa
wersja, czyli średnia ze wszystkich 7 dni, to ok. +9,5 % rocznie przy bardzo szerokim przedziale
(od −21 do +40 %). To wynik nieodróżnialny od zera. Poniedziałkowe +42 % było więc w dużej mierze
szczęśliwym wyborem dnia, a nie siłą reguły. Użytkownik zdecydował, że X1 w tej uczciwej wersji i tak
idzie do dziennika papierowego, bo nic to nie kosztuje, a zbiera dane z przyszłości.

## ID testu

X1F — zapis porządkowy (ciąg X1 → RU1 → AU1), 0 wariantów: ta sama reguła X1, uśrednienie po dniu startu
tygodnia — wymóg metodyczny z wniosku 68 i RU3 (dla X2), zastosowany do X1. Plus poprawki 3 i 4 dziennika.

## Metadane

- Branch `x1-dziennik`. Komenda: `PYTHONUTF8=1 py -m backtest.run_x1_phases_x1f` → `raw_output.txt`.
- Dane: `data/raw/universe_full` (świece 1d, funding), 2021-01-01 → 2026-06-30; ocena od 2021-02-01.
- Reguła X1 bez zmian (`xs_momentum`): koszyk top-20 po obrocie (skład co miesiąc), sygnał = zwrot 28 dni,
  long 5 / short 5, kapitał 0,5 + 0,5, trzymanie 7 dni, koszt taker + poślizg 0,07 % obrotu, funding realny.
- Fazy: `ts_momentum.formation_dates(start + faza)`, faza 0 = poniedziałek 2021-02-01 (= X1/RU1).
- Kod dziennika: `backtest/live_journal.py` (`x1_component`, `x1_rows`, `summarize_x1`),
  `data/fetch_live.py` (`SYMBOL_RE`), testy `tests/test_live_journal.py` (+5 testów X1, test filtra nazw).
- `walidacja.txt` — bramka 16a (niezależna implementacja, zgodność dziennik vs backtest, rozbicie różnic).

## Poprzedzające wyniki

- X1 (2026-09-24, wniosek 64): +22 %/rok na obciętym uniwersum; RU1 (82): +41,7 %/rok, t_neff 1,86,
  ~83 pkt z jednego zdarzenia (MYX); AU1 (87): bez dnia MYX t 1,83, bez 5 najlepszych dni 1,30.
- Wniosek 68 i RU3 (88): X2 zależy od dnia przebudowy (fazy 12–39 %/rok) — pojedynczej fazy nie cytować.
- Decyzja użytkownika 2026-09-24 (po AU1): „X1 do dziennika na żywo”, w wersji z 7 fazami.

## Pre-rejestracja

Nie było osobnego commitu przed przebiegiem — odczyt powstał jako kalibracja progu dziennika. Konfiguracja
była jednak przesądzona z góry: reguła X1 zamrożona od rundy X1, a wersja „7 faz” wybrana decyzją użytkownika
przed obejrzeniem liczb (propozycja AU1: „X1 jako osobna reguła, najlepiej w wersji z 7 fazami”). Zero
parametrów wybieranych po wyniku. Progi dziennika wynikają z reguły zapisanej wcześniej dla R1 (ostrzeżenie =
największe obsunięcie w historii, STOP = 1,5 ×). Reguła X1 w dzienniku jest zamrożona w `dziennik/README.md`
(poprawka 3) i zapisana w gicie przed pierwszym dniem wyniku (2026-09-25).

## Wynik

| wersja | dni | zwrot netto %/rok [CI 95 %] | mediana/dzień | t_neff |
|---|---|---|---|---|
| faza 0 — poniedziałek (= X1/RU1) | 1 975 | +41,7 [−2,2; +85,6] | +0,117 % | 1,86 |
| faza 1 — wtorek | 1 974 | +4,9 [−34,6; +44,5] | +0,055 % | 0,24 |
| faza 2 — środa | 1 973 | +0,7 [−41,5; +42,9] | +0,071 % | 0,03 |
| faza 3 — czwartek | 1 972 | +4,4 [−35,6; +44,3] | +0,097 % | 0,21 |
| faza 4 — piątek | 1 971 | +2,1 [−39,1; +43,2] | +0,064 % | 0,10 |
| faza 5 — sobota | 1 970 | −1,3 [−40,1; +37,5] | +0,060 % | −0,07 |
| faza 6 — niedziela | 1 969 | +21,6 [−10,6; +53,7] | +0,059 % | 1,32 |
| **średnia 7 faz** | **1 969** | **+9,5 [−21,1; +40,1]** | +0,091 % | **0,61** |
| średnia 7 faz bez dni MYX (7–8.09.2025) | 1 967 | +17,6 [−10,4; +45,5] | +0,093 % | 1,23 |
| średnia 7 faz od 2022 (opisowo) | 1 642 | +7,5 [−26,3; +41,3] | +0,076 % | 0,44 |

- **Per rok (średnia 7 faz):** 2021 +17,4 · 2022 −14,5 · 2023 +29,0 · 2024 +9,2 · 2025 +4,2 · 2026 (pół roku) +5,9 %
  → 5/6 lat dodatnich.
- **Zdarzenie MYX:** 7–8.09.2025 cena MYX wzrosła z 1,31 do 13,89 USD (10,6×). W fazie poniedziałkowej była w nodze long
  (+~83 pkt), w pięciu fazach (wt–sob) w nodze short, w niedzielnej w żadnej. Średnia 7 faz straciła na tych dwóch dniach ok. 44 pkt.
  Jedno zdarzenie decyduje o znaku różnicy między fazami.
- **Największe obsunięcie** średniej 7 faz: **55,0 %** (2025-04-22 → 2026-03-09) → progi dziennika X1:
  ostrzeżenie 55,0 %, STOP 82,5 %.

**Jak czytać „%/rok”:** średni dzienny zwrot netto × 365, w % kapitału X1 (0,5 long + 0,5 short).
Przedział 95 % z N_eff (tu N_eff = n).

## Dziennik — sprawdzian przed startem X1

- **Zgodność z backtestem** (2025-10-15 → 2026-06-29, 258 dni; te same ceny co do 1·10⁻⁹): przed poprawką 4
  korelacja dzienna 0,9875, suma −1,2 % wobec +8,7 %. Cała różnica pochodziła ze składu koszyka — trzy miesiące
  z jedną inną monetą: `IPUSDT` (2026-02) i `TONUSDT` (2026-06) są dziś nieaktywne na Binance, więc dziennik
  ich nie widzi; `币安人生USDT` (2026-05) odrzucał filtr nazw plików `[A-Z0-9]{1,40}USDT`. Te same ceny ze
  składem backtestu dają +8,7 %, ze składem dziennika −1,2 % — skład tłumaczy różnicę w całości.
- **Poprawka 4:** filtr dopuszcza litery spoza ASCII (nadal odrzuca kropki, ukośniki, dwukropki, spacje,
  znaki sterujące, małe litery ASCII — test). Po świeżym pobraniu: korelacja **0,9986**, suma +5,3 % wobec
  +8,7 % (reszta = monety nieaktywne dziś — znane przybliżenie dziennika).
- **Skutek dla dziennika głównego:** `币安人生USDT` był w koszyku trendu w 2026-05, więc zmienia się historia
  budżetu ryzyka R1: mnożnik trendu ogłoszony za 23.09 to 0,5709, po poprawce 0,5700 (premia Coinbase
  0,34263 → 0,34262); znaki i wagi wszystkich 147 pozycji identyczne. Zapis w `sygnaly.csv` zostaje bez zmian
  (append-only); przebieg z danymi do 23.09 zgłosi „historia zmieniona: 147” (pole `k`) — wyjaśnione tutaj.
  Pierwszy wiersz wyniku (24.09) liczy się już po poprawce.
- **Przebieg próbny** (katalog tymczasowy): 70 wierszy `x1_sygnaly.csv` (7 faz × 10 nóg), ekspozycja brutto
  X1 po skompensowaniu faz 0,94× kapitału X1, netto 0,00×; główny zapis bez nowych wierszy.
- Testy: +5 testów X1 (średnia 7 silników, nogi i wagi, brak zaglądania w przyszłość, zapis osobny,
  progi) i rozszerzony test filtra nazw; cały zestaw zielony.

## Co na plus (+) / Co na minus (−)

**(+)** Uczciwa wersja X1 zmierzona, zanim trafiła do dziennika — bez tego dziennik porównywałby się z liczbą
zawyżoną wyborem dnia. Niezależna implementacja potwierdza silnik co do 1·10⁻¹⁶. Sprawdzian wykrył realną
usterkę dziennika (filtr nazw), którą poprawiono przed pierwszym wynikiem.

**(−)** Odczyt bez osobnego commitu pre-rejestracji (konfiguracja przesądzona z góry, ale zapis po fakcie).
X1 nie ma modelu likwidacji — papierowa strata na skoku monety w nodze short jest większa niż przy dźwigni
izolowanej. Wynik bardzo zależny od pojedynczych zdarzeń (MYX) i od składu koszyka (jedna zamiana monety
przesuwa wynik o kilka punktów).

## Walidacja (16a) — `data:validate-data`

- **Druga droga:** niezależna implementacja zwrotu brutto fazy 3 (pętla na słownikach, bez
  `long_short_returns`) zgodna z silnikiem co do 1,1·10⁻¹⁶ na 1 972 dniach (suma +13,70 % w obu). Faza
  poniedziałkowa odtwarza X1/RU1 co do zera (+41,7 %, t 1,86), dwiema funkcjami dat.
- **Kogo nie ma w zbiorze:** w backteście — nikogo spoza reguły (pełne uniwersum, funding kompletny, RU3);
  w dzienniku — monet nieaktywnych dziś (IP, TON) i do poprawki 4 monet z nazwą spoza ASCII. Obie luki
  zmierzone (rozbicie w `walidacja.txt`).
- **Czerwona flaga „wynik idealnie potwierdza hipotezę”:** odwrotnie — runda osłabia wcześniejszy wynik.
  Czerwoną flagą był wcześniejszy odczyt: najlepsza z 7 faz, wybrana nieświadomie (dzień startu 2021-02-01).
- **Werdykt: Caveats** — liczby potwierdzone; zastrzeżenia: brak osobnego commitu pre-rejestracji, brak
  modelu likwidacji w X1, wrażliwość na pojedyncze zdarzenia i skład koszyka.

## Statystyka (16b) — `data:statistical-analysis`

Efekt z przedziałem: +9,5 %/rok [−21,1; +40,1] — przedział obejmuje zero z obu stron szeroko; mediana dzienna
+0,091 % przy średniej +0,026 %/dzień (większość dni lekko na plus, średnią ciągną w dół rzadkie duże straty
— skok MYX). Rozrzut faz od −1,3 do +41,7 %/rok przy tej samej regule to miara szumu: dawny odczyt był
najlepszym z siedmiu równoprawnych. Odczyty „bez MYX” (+17,6 %, t 1,23) i „od 2022” (+7,5 %, t 0,44) są
opisowe, bez kryterium. Licznik: 0 nowych wariantów (ta sama reguła); próg rodzinny ~2,9 dla ~30 odczytów.

## Przegląd kodu (16c) — `engineering:code-review`

Zakres: `live_journal.py` (X1: `x1_component`, `x1_rows`, `run_x1`, `summarize_x1`; `stop_status` z progami
jako parametrami), `fetch_live.py` (`SYMBOL_RE`), `uruchom.bat`, testy (+6), skrypt rundy.
- **Poprawione w przeglądzie:** błąd w X1 przerywał cały przebieg — dziennik główny nie dopisałby linii do
  `przebiegi.log`, z którego liczy się jego kompletność. Teraz X1 działa w osobnym bloku: błąd trafia do logu
  i wydruku („X1: BŁĄD …”), dziennik główny zapisuje się normalnie (test `test_x1_error_does_not_stop_main_journal`).
- **Bezpieczeństwo filtra nazw:** luzowanie kontroli z wcześniejszego przeglądu bezpieczeństwa — dopuszczone
  tylko litery/cyfry spoza ASCII (`\w` bez zakresu ASCII); test odrzuca ukośnik, kropkę, dwukropek, myślnik,
  podkreślnik, znak sterujący U+202E i pełnoszeroki ukośnik U+FF0F. Nazwa trafia tylko do nazwy pliku
  w `data/raw/live/` (bez powłoki, bez URL-i poza zapytaniem ccxt).
- `uruchom.bat`: zapasowa pełna ścieżka do `py` (Python zainstalowany dla użytkownika), znacznik startu/końca,
  kod wyjścia przekazany Harmonogramowi (ponowienia przy błędzie).
- Drobne: import prywatnego `_month_of` z `xs_momentum` — akceptowalny (ta sama logika co silnik).
**Werdykt: zatwierdzone po poprawce — X1 liczy dokładnie silnik rund, jest odizolowany od dziennika głównego,
a filtr nazw pozostaje bezpieczny dla ścieżek.**

## Wniosek

**Prostym językiem:** X1 nie był tak dobry, jak wyglądał. Wynik +42 % rocznie zależał od tego, że koszyk
przebudowywaliśmy w poniedziałek. Uczciwa średnia ze wszystkich dni tygodnia to ok. +9,5 % rocznie, co przy
tak dużych wahaniach jest nie do odróżnienia od zera. Na historii X1 przestaje być kandydatem. Zostaje
w dzienniku papierowym jako tani test na przyszłość, z zastrzeżeniem, że papier liczy go bez dźwigni
i bez likwidacji. Przy okazji sprawdzian wyłapał błąd w dzienniku, który pomijał monety z chińskimi
nazwami — poprawiony przed pierwszym wynikiem.

## Rekomendacja

1. W `runs/INDEX.md` zastąpić opis X1 liczbą 7 faz (wniosek 89); X1 z listy kandydatów przenieść do
   „śladów bez dowodu”.
2. Każdą strategię z przebudową co tydzień liczyć odtąd od razu jako średnią 7 faz (tak liczą już TS1 i R1).
3. X1 w dzienniku: odczyt mechaniki razem z resztą (~2026-12-25); bez decyzji kapitałowych.

## Harmonogram (prośba użytkownika 2026-09-24: „dziennik musi się uruchamiać codziennie”)

Zadanie „CLAS5 dziennik” istniało (02:30), ale w ustawieniach domyślnych: nie nadrabiało przegapionego
terminu, nie budziło komputera, nie startowało na baterii. Zmienione: start przy najbliższej okazji,
budzenie, praca na baterii, limit 2 h, 3 ponowienia co 30 min, jedna instancja. Komputer to desktop, na
zasilaniu nie usypia, budziki systemowe włączone. Tryb „bez logowania” (S4U) wymaga administratora —
polecenie dla użytkownika w `dziennik/README.md` („Codziennie”). Szczegóły i test przebiegu z Harmonogramu:
`STATUS.md`.

## Użyte skille

```
### Użyte skille — gałąź `x1-dziennik` (rejestr automatyczny)
| 2026-09-24T18:06:39+02:00 | claude | `anthropic-skills:clas5-runda` |
| 2026-09-24T18:06:44+02:00 | claude | `anthropic-skills:clas5-quant` |
| 2026-09-24T18:28:36+02:00 | claude | `data:validate-data` |
| 2026-09-24T18:28:40+02:00 | claude | `data:statistical-analysis` |
| 2026-09-24T18:30:16+02:00 | claude | `engineering:code-review` |
Razem: 5 wczytań, 5 różnych skilli.
```

- `clas5-runda` — procedura rundy i DoD. `clas5-quant` — zasada „najpierw uczciwa wersja, potem dziennik”,
  kryteria, próg rodzinny. Oba wczytane przed skryptem rundy (odczyt kalibracyjny sprzed gałęzi — w scratchpadzie
  — opisany w Pre-rejestracji).
- `data:validate-data` — niezależna implementacja, rozbicie różnicy dziennik/backtest na skład koszyka
  (to wykryło usterkę filtra nazw).
- `data:statistical-analysis` — mediana obok średniej (rozkład lewoskośny), rozrzut faz jako miara szumu.
- `engineering:code-review` — wykrył brak izolacji X1 od dziennika głównego (poprawione).
- Pominięte: `security-review` (brak nowego połączenia sieciowego i kluczy; zmiana filtra nazw oceniona
  w przeglądzie z testami złośliwych nazw), `engineering:testing-strategy` (rozszerzenie istniejącego modułu,
  wzorzec testów dziennika bez zmian), `dataviz` (brak wykresu).
