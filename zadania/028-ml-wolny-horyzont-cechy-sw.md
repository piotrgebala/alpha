---
id: 028
tytul: ML na rzadszym handlu (dni zamiast 4h) z pełnym zestawem cech spoza wykresu — krok 0 na papierze, odczyt tylko prospektywny
typ: badawcze
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-30: „Zaplanuj zadanie do wykonania z powrotem do ml z rzadszym handlem i większą liczbą cech”; 2026-09-30: „Zrób tak niech model uczynię na danych do 2026 a od 2026 niech leci backtest strategii”; 2026-09-30: wybór „a” — opcja A (uczenie do 2025-12-31, model zamrożony, 2026-01…09 rozbieg bez werdyktu, tor P prospektywny)"
utworzono: 2026-09-30
zalezy_od: []
budzet: "Opus, 1 wykonawca na krok 0 (metodologia); bez sieci poza danymi już w repo"
---

# 028 — ML z rzadszym handlem i większą liczbą cech

## Po co

Seria SW (wniosek 90) pokazała ślad w cechach spoza wykresu: +0,01…+0,05 % na transakcję przed kosztami,
IC (korelacja rang sygnału ze zwrotem) +0,02…+0,03 w 5 z 8 cech. Koszt handlu co 4 godziny (~0,08 % na
transakcję) zjada ten ślad 2–3 razy. README SW (Rekomendacja 2) zostawia jedną otwartą drogę: **wolniejszy
horyzont**, czyli mniej transakcji i koszt dzielony na większy ruch. To NOWA hipoteza, nie wariant SW.

Hipoteza jednym zdaniem: model uczony na stałym, z góry zapisanym zestawie cech z wykresu i spoza wykresu,
trzymający pozycję kilka dni, ma zwrot netto > 0, bo koszt spada 5–40 razy, a informacja o pozycjonowaniu
tłumu i fundingu żyje dniami (acf1 ≥ 0,98, wniosek 67).

## Dwie przeszkody do nazwania z góry

1. **Historia 2021–2026 jest wyczerpana jako sędzia.** Rejestr ma 60 odczytów (`runs/odczyty_historii.csv`),
   a kolejny odczyt tej historii potrzebuje t ≈ 3,84 (wniosek 107; `py -m backtest.dsr`). Na samym BTC
   z danych dziennych przyrząd widzi dopiero SR ≥ ~0,86 (wnioski 87, 91). Zadanie 013 (BTC 1d) zamknięto
   z tego powodu bez odczytu. Najbardziej prawdopodobny wynik kroku 0 na historii to **NIEMIERZALNA**.
2. **„Więcej cech” a zasada 4** (jedna cecha na raz, bez przeszukiwania kombinacji). Rozwiązanie: **jeden
   zestaw cech zapisany z góry = jeden wariant**, bez podzbiorów i bez strojenia. Każda cecha spoza wykresu
   była już mierzona osobno w SW, więc zestaw nie wprowadza cech niezmierzonych. Bez siatki
   hiperparametrów: parametry XGBoost jak w SW etap 2.

## Zakres

### Krok 0 — papier, 0 odczytów (ten krok obejmuje decyzja z 2026-09-30)

Wykonawca wczytuje skille `clas5-quant` i `quant-strategy-catalog` (zasada 19) i przygotowuje kartę
pre-rejestracji `runs/DRAFT_028.md` (generator: `scripts/hypothesis_card.py` ze skilla katalogu):

- **Cechy (stałe, 11):** 4 cechy REVERSION modelu kontrolnego + 7 cech SW etapu 2 (bez `toptrader_ls_log`,
  dziura 2021-12 → 2022-12). Wszystkie przeliczone na świecę dzienną. Test przecieku każdej cechy na nowej
  świecy przed wejściem do modelu (zasada 2); dostępność danych jak w SW (on-chain +2 dni, VRP +1 dzień).
- **Target:** triple-barrier na świecy 1d, bariery 1,5 × ATR (zasada 3, `labeling.ATR_MULTIPLIER`),
  bariera czasowa V = 7 dni. Stop-loss w silniku z tego samego mnożnika.
- **Formuła — policzyć moc dla dwóch i wybrać jedną PRZED danymi:**
  - (a) jednoaktywowa: BTC, decyzja raz dziennie, pozycja do bariery;
  - (b) panel: ten sam model na koszyku top-20 z `universe_full`, jeśli cechy spoza wykresu istnieją per
    moneta (funding i archiwum pozycjonowania Binance — sprawdzić pokrycie; VRP, podaż i F&G są tylko
    dla BTC/rynku → w panelu wspólne dla wszystkich monet). Uwaga: AU2 (wniosek 93) — ML przekrojowe
    traci ~2/3 mocy; panel liczy się tylko wtedy, gdy rachunek mocy to przetrzyma.
- **Walk-forward:** okno uczenia 365 dni (jak SW), purging i embargo ≥ V; reguła z kalendarzem →
  średnia wszystkich faz startu (wniosek 89).
- **Rachunek mierzalności (zasada 18):** `expected_trades(n_świec, abstynencja, admission_rate)` →
  `measurability_report(zakładana_trafność, p*, oczekiwane_n)`. Zakładany efekt z SW przed kosztami
  (+0,02…+0,05 %/tr na 4h, przeskalowany do 7 dni — przeskalowanie zapisać jawnie jako założenie), koszt
  0,08 % na transakcję. Plus próg DSR: `py -m backtest.dsr --k 1` dla bieżącego N odczytów.
- **Dwa tory odczytu — policzyć oba:**
  - **Tor H (historia 2021–2026):** próg t ≈ 3,84. Jeśli NIEMIERZALNA → tor H zamknięty bez odczytu.
  - **Tor P (prospektywny):** model uczony na historii i **zamrożony** (hash commita, parametry, cechy)
    przed 2026-10-01; sygnały zapisywane dzień po dniu jako dziennik papierowy. Nowe dane = własny licznik,
    próg t 1,96 (mapa 007 §1). Policzyć, po ilu miesiącach tor P osiąga mierzalność przy zakładanym efekcie.
- **Brama danych:** czy zbieracze funding / OI / L/S / taker / VRP / podaż / F&G działają na żywo i dają
  dane dzienne bez dziur (tor P ich wymaga). Braki zgłaszać jako BRAK DANYCH.
- **Wynik kroku 0:** akapit w `docs/mapa_hipotez_2026-10.md`, wniosek w `runs/INDEX.md` (0 odczytów),
  rekomendacja: tor H / tor P / zamknięcie.

### Krok 1 — tor H, runda na historii (TYLKO po decyzji użytkownika i gdy krok 0 = MIERZALNA)

Procedura `clas5-runda`, katalog `runs/2026-MM-DD_ML1-wolny-horyzont/`, wiersz w `runs/odczyty_historii.csv`.

### Krok 2 — tor P, dziennik prospektywny (TYLKO po decyzji użytkownika)

To typ `dziennik`: Poprawka N w `dziennik/README.md`, bez zmian w nogach TS1/CP1. Odczyt z progami z góry,
jak dla dziennika trend + Coinbase (wniosek 107).

## Czego NIE robić

- Żadnego odczytu zwrotu w kroku 0 — ani na historii, ani „na próbę”.
- Bez podzbiorów cech, bez rankingu ważności cech po wyniku, bez siatki hiperparametrów, bez innych V ani
  mnożników ATR (zasady 1, 3, 4).
- Bez dokładania cech spoza listy 11 (np. `toptrader_ls_log`, likwidacje — zbierane dopiero od 2026-09-25).
- Bez zmian w kodzie, z którego korzysta dziennik papierowy (CLAUDE.md, „Dziennik papierowy”).
- Bez LLM w ścieżce decyzji (zasada 6).

## Kryteria odbioru (dowody)

- `runs/DRAFT_028.md` z wypełnioną kartą: cechy, target, formuła, walk-forward, licznik wariantów = 1.
- Wydruk `measurability_report` i `backtest.dsr` dla obu formuł i obu torów, z komendą i hashem commita.
  Druga droga kluczowej liczby (połowa szerokości przedziału z `wald_half_width` przeliczona ręcznie).
- Tabela pokrycia danych dziennych dla 11 cech (od, do, dziury) — dla BTC i, przy formule (b), per moneta.
- Akapit w mapie 007 + wniosek w `runs/INDEX.md`; 0 nowych wierszy w `runs/odczyty_historii.csv`.
- `py -m pytest -q` zielone.

## Decyzja użytkownika 2026-09-30 (druga) i rachunek mocy

Słowa użytkownika: „Zrób tak niech model uczynię na danych do 2026 a od 2026 niech leci backtest strategii”.
Czyli: **jeden model uczony na danych 2021-01-01 → 2025-12-31, zamrożony; test 2026-01-01 → 2026-09-29**
(272 dni), bez douczania w trakcie testu.

Rachunek mierzalności (zasada 18) policzony w sesji chmurowej 2026-09-30, `backtest/metrics.py`, bez danych
rynkowych. Wejścia: koszt 0,08 %, ATR 1d BTC ~3 % → bariera 4,5 % → p* ≈ 50,9 % (dla ATR 2,5–3,5 %: 50,8–51,1 %).
Zakładana trafność 52–55 % jest hojna: ślad z SW (+0,02…+0,05 % na transakcję przed kosztami) odpowiada
~50,5–51 %.

| wariant | oczekiwane n | ± przedział | trafność potrzebna do dowodu | werdykt przy p 53 % |
|---|---|---|---|---|
| BTC, abstynencja 50 % | 136 | ±8,4 pp | 59,3 % | NIEMIERZALNA |
| BTC, bez abstynencji | 272 | ±5,9 pp | 56,8 % | NIEMIERZALNA |
| panel top-20, ~3 niezależne monety (wniosek 40) | 408 | ±4,9 pp | 55,7 % | NIEMIERZALNA |
| panel top-20 liczony jak 20 niezależnych (zawyżone) | 2 720 | ±1,9 pp | 52,8 % | na styk (tylko przy p 53 %) |

Liczby n są optymistyczne. Przy trzymaniu pozycji do 7 dni transakcje BTC nakładają się i niezależnych jest
~2–4 razy mniej. Dodatkowo lata 2026 były już czytane przez inne rundy (SW na 4h z tymi samymi cechami,
CP1, TS1), więc test jest odczytem historii z progiem t ≈ 3,84 (wniosek 107), a nie świeżym sprawdzianem.

**Werdykt: NIEMIERZALNA we wszystkich uczciwych wariantach → runda na samym 2026 nie startuje (zasada 18).**
Status `czeka_na_decyzje`. Opcje dla użytkownika:

- **A (rekomendacja):** podział zostaje (uczenie do 2025-12-31, model zamrożony), ale 2026-01 → 2026-09
  jest tylko rozruchem bez werdyktu, a test biegnie DALEJ prospektywnie od 2026-10-01 jako dziennik
  papierowy (tor P). Werdykt dopiero, gdy rachunek mocy pokaże mierzalność — krok 0 policzy kiedy.
- **B:** przebieg na 2026 jako opis bez werdyktu. To odstępstwo od zasady 18, więc wymaga wpisu decyzji
  w `STATUS.md` z powodem.
- **C:** zamknąć zadanie bez odczytu, jak 013.

Dowód: `moc_028.txt` (wydruk `measurability_report` wszystkich wariantów), wklejony do README rundy, jeśli
ruszy. Uwaga środowiskowa: sesja chmurowa nie ma dostępu do Binance / Deribit / alternative.me / CoinMetrics
(polityka sieci), więc przebieg z danymi musi iść na serwerze.

## Wynik

(dopisuje orkiestrator)

- **2026-09-30, decyzja użytkownika: opcja A** (słowa: „wybrałem decyzję a”, potem „przejdź do zadania z realizacją ML
  uczenie do końca 2025, a później test na 2026”). Przenumerowane 027 → 028 (kolizja z `027-audyt-hook-surogat.md`).
  Kolejność dla orkiestratora na serwerze (sesja chmurowa nie ma dostępu do źródeł danych):
  1. Krok 0 (papier + brama danych) i karta `runs/DRAFT_028.md` z hashem commita **przed** uczeniem modelu.
  2. Jeden model uczony na 2021-01-01 → 2025-12-31, zamrożony (hash commita, parametry, lista cech, hash pliku modelu).
  3. 2026-01-01 → dzień zamrożenia: rozbieg bez werdyktu. Wynik tego okresu nie wchodzi do testu i nie zmienia modelu.
     Można go opisać tylko jako kontrolę mechaniki (czy sygnały się liczą), bez zwrotów w raporcie werdyktowym.
  4. Tor P: sygnały dzień po dniu **od dnia zamrożenia** (nie wcześniej, nawet jeśli to po 2026-10-01), własny licznik,
     próg t 1,96, werdykt dopiero, gdy krok 0 pokaże mierzalność.
  5. Tor P to nowy, osobny proces papierowy. Nie wolno zmieniać `backtest/live_journal.py` ani jego importów; wpięcie
     w harmonogram serwera = osobna decyzja użytkownika.
