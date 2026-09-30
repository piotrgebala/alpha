# ML1 — model XGBoost na świecy dziennej BTC (11 cech, V = 7 dni) nauczony na 2021–2025 i zamrożony; rozbieg 2026 tylko jako kontrola mechaniki (2026-09-30)

> **STATUS: ZAMKNIĘTA — model zamrożony, 0 werdyktów, 0 zwrotów.** Zadanie 028, opcja A użytkownika z regułą progu
> pewności („Dopisz”). Pre-rejestracja: karta `runs/DRAFT_028.md` §14, commit **`e99dc82`** (przed uczeniem).
> Model: `model_ml1.json`, sha256 **`d1a39ee4…b165195c`**, 10 cech (dedup odrzucił `price_zscore_20`), próg pewności
> **0,424963** (= górne 20 % sygnałów walk-forward). Kalibracja 2022–2025: **trafność NIE rośnie z pewnością**
> (górny kubełek 49,5 % wobec 52,8 % wszystkich sygnałów) — zapisane jako ryzyko, reguła bez zmian. Rozbieg 2026:
> 111 sygnałów z kierunkiem w 272 dniach, **10 ponad progiem (9 %, a nie zapisane 20 %)**. Rachunek mierzalności
> progu: NIEMIERZALNA do 5 lat przy trafności ≤ 55 %. Bramki: 16a **Caveats**, 16b tak, 16c **Approve z uwagami**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Zbudowaliśmy jeden model, który raz dziennie ocenia, czy BTC w ciągu najbliższych 7 dni pójdzie w górę, w dół, czy nic
się nie wydarzy. Model patrzy na 10 liczb: cztery z wykresu ceny oraz sześć spoza wykresu (opłata funding, zmiana liczby
otwartych kontraktów, proporcja kont grających na wzrost do grających na spadek, przewaga agresywnych kupujących, premia
za zmienność z opcji, podaż BTC na giełdach i indeks strachu i chciwości). Nauczyliśmy go na latach 2021–2025 i
zamroziliśmy: plik modelu ma odcisk (hash), więc później da się sprawdzić, że nikt go nie poprawiał.

Użytkownik chciał mniej transakcji i tylko te „najpewniejsze”. Zapisaliśmy z góry jedną regułę: handlujemy tylko
górnymi 20 % sygnałów według pewności modelu. Wartość tej granicy (0,425) policzyliśmy na danych 2021–2025.

Trzy rzeczy wyszły źle albo słabo i trzeba je znać przed jakąkolwiek dalszą decyzją:

- **Najpewniejsze sygnały nie trafiały lepiej.** Na latach 2022–2025 górne 20 % sygnałów trafiało kierunek w 49,5 %
  przypadków, a wszystkie sygnały w 52,8 %. Obie liczby mają błąd ±8–14 punktów, więc to nie jest dowód ani za, ani
  przeciw. Ale reguła „wysoka pewność” nie ma w historii żadnego oparcia.
- **Pewność modelu mierzy głównie to, ile model się nauczył w danym okresie, a nie jak mocny jest sygnał.** W 10 z 15
  okresów testowych model zatrzymywał się po jednym drzewie i żaden sygnał nie sięgał progu. 92 % sygnałów „ponad
  progiem” pochodzi z 4 okresów.
- **Na 2026 próg przepuszcza 9 % sygnałów, nie 20 %.** To około 13 transakcji rocznie (połowa z nich nachodzi na
  siebie). Żeby taki strumień cokolwiek udowodnił po roku, musiałby trafiać w ~88 % przypadków (po 2 latach ~78 %, po 5 latach ~68 %). Przy realistycznej
  trafności 52–55 % dowód przyszedłby po dziesiątkach lat.

Nie liczyliśmy żadnych zysków ani strat — ani na latach 2021–2025, ani na 2026. Tak zdecydował użytkownik (opcja A).

## ID i metadane

| pole | wartość |
|---|---|
| ID | **ML1** (nowa hipoteza, własny licznik) |
| zadanie | `zadania/028-ml-wolny-horyzont-cechy-sw.md` (decyzje użytkownika 2026-09-30: opcja A, „Dopisz”, „Wykonaj zadanie 28”) |
| gałąź | `zadanie-028-ml1-wolny-horyzont` (od `master` 94eaa89) |
| commity | karta/pre-rejestracja **`e99dc82`** → kod cech i testów `35cd2c7` → wynik WF `ea073a6` → model `6ff7960` → rozbieg `32df748` → dokumentacja (ten commit) |
| skrypt | `backtest/run_ml1_wolny_horyzont.py` (tryby `dane`, `pokrycie`, `moc`, `wf`, `zamroz`, `rozbieg`, `foldy`) |
| moduł cech | `agents/ml1_features.py` (+ sekcja `ml1_1d` w `agents/feature_registry.yaml`) |
| komendy | `PYTHONUTF8=1 OMP_NUM_THREADS=4 py -m backtest.run_ml1_wolny_horyzont <tryb>`; druga droga: `PYTHONUTF8=1 py runs/2026-09-30_ml1-wolny-horyzont/druga_droga.py` |
| dane | natywne świece 1d BTCUSDT perp od 2021-01-01 (`fetch_window`, zasada 20) do 2026-09-29; funding, archiwum `metrics` 5 min, DVOL, CoinMetrics, F&G — pliki w `data/raw/ml1/` (poza gitem; sha256 w `manifest.json`), pobrane 2026-09-30 ~18:20 UTC |
| model | XGBoost 3.2.0, parametry SW etap 2 (`max_depth` 4, `eta` 0,05, 200 rund, early stopping 20 na ogonie 20 %, wagi `balanced`, ziarno 42), V = 7, `ATR_MULTIPLIER` 1,5, embargo 7 |
| walk-forward | 365 / 91 / 91 dni (jak Y2 na 1d), ramka ucięta na 2025-12-31 przed etykietami |
| artefakty | `raw_output.txt`, `wf_prog.json`, `kalibracja_wf.csv`, `sygnaly_oos_wf.csv`, `model_ml1.json`, `manifest.json`, `sygnaly_rozbieg_2026.csv`, `druga_droga.py` |
| środowisko | serwer Linux, Python 3.12.3, pandas 3.0.2, numpy 2.4.4 |
| testy | `OMP_NUM_THREADS=4 py -m pytest -q` (pipefail): **2099 passed, 3 skipped, kod 0** (w tym 16 testów przecieku ML1 i 11 jednostkowych); ruff + black na dotykanych plikach czyste |

## Poprzedzające wyniki

- **SW (wniosek 90):** te same cechy spoza wykresu na 4h — ślad przed kosztami +0,01…+0,05 %/transakcję, koszt zjada go
  2–3×; jedyna otwarta droga to wolniejszy horyzont. Stąd świeca 1d i V = 7 dni oraz parametry XGBoost z etapu 2.
- **Y2 (wniosek 87b):** model kontrolny na 1d (365/91/91) — niezmierzony; stąd okna walk-forward.
- **C2.13:** próg pewności (górny kwartyl) dał trafność NIŻSZĄ niż bez progu — precedens ryzyka, które się powtórzyło.
- **107:** 41. odczyt historii wymaga t ≈ 3,84 — tor H zamknięty, tabela kalibracji jest tylko opisem.
- **113 (krok 0):** tor H NIEMIERZALNY, tor P mierzalny dopiero po latach; brama danych: 5 z 11 cech bez zbieracza na żywo.
- Równoważnego wariantu (11 cech × 1d × V = 7) projekt nie mierzył (karta §1).

## Pre-rejestracja (przed obejrzeniem wyniku)

Karta `runs/DRAFT_028.md`: §4–§5 (cechy, target, parametry; z kroku 0, commit `fff7ce2`) i **§14 (reguła progu i
uzupełnienia; commit `e99dc82`, przed uczeniem)**. Najważniejsze punkty §14:

- próg = kwantyl 0,80 pewności sygnałów OOS walk-forward 2021–2025, JEDNA wartość, bez przeszukiwania;
- licznik wariantów ML1 = 2 (wszystkie sygnały / ponad progiem) — liczony na torze P;
- walk-forward 365/91/91, dedup |ρ| > 0,9 RAZ na pierwszym oknie, ta sama lista cech w modelu zamrożonym;
- kalibracja w kwintylach pewności; „brak rosnącej trafności” = górny kubełek ≤ wszystkie albo korelacja rang ≤ 0 → ryzyko, reguła bez zmian;
- tabela kalibracji = odczyt historii (`opis-z-wynikiem`, `tak`, 0 wariantów);
- rozbieg 2026 bez etykiet, trafności, zwrotu i t.

Sprostowanie zapisane PRZED uczeniem (§14.4): silnik nie robi przerwy między częścią uczącą a ogonem walidacyjnym (tak
samo w SW) — §5.3 opisywał to błędnie; zostaje silnik jak w SW.

**Rachunek mierzalności reguły progu (§14.3, tryb `moc`):** p\* 50,89 %, abstynencja 37,8 %, nakładanie 2×.

| szereg | 6 mies. | 12 mies. | 24 mies. | 60 mies. |
|---|---|---|---|---|
| wszystkie sygnały: n niezależnych / trafność potrzebna | 56,9 / 63,9 % | 113,5 / 60,1 % | 227,0 / 57,4 % | 567,9 / 55,0 % |
| ponad progiem (20 %): n niezależnych / trafność potrzebna | 11,4 / 80,4 % | 22,7 / 71,3 % | 45,4 / 65,5 % | 113,6 / 60,1 % |

Werdykt przy 52 / 53 / 55 %: NIEMIERZALNA w każdym horyzoncie do 5 lat dla obu szeregów. Ponad progiem ~22,7 niezależnych
transakcji rocznie (założenie ex ante; rozbieg pokazał ~6,7 — niżej).

## Wynik

### Krok 1 — brama danych (tryb `pokrycie`)

Wszystkie źródła od 2021-01-01 (DVOL od 2021-03-24) do 2026-09-29/30. Dziury: proporcja kont long/short 19 dni
(2021-12-31 → 2022-01-18), przewaga kupujących 128 dni (2021-12-31 → 2022-05-08), F&G 1 dzień (2024-10-26), reszta 0.
Przedłużone OHLCV i funding zgodne z kopią repo głównego co do bitu (2 486 / 7 457 wspólnych wierszy). `fetch_window`:
2 098 świec od 2021-01-01 (zasada 20 działa).

### Krok 2 — walk-forward 2021-01-01 → 2025-12-31 (tryb `wf`)

- Świece z kompletem 11 cech: 1 615 z 1 826. Dedup: `price_zscore_20` odpada (ρ = 0,91 z `rsi_14`) → **10 cech**.
- Foldy: 15/16 aktywnych (fold 0, test 2022-01 → 2022-04, pominięty: 1 ważna świeca przez dziurę taker). Świece
  ocenione 1 328, abstynencja 31,4 %, **910 sygnałów** (long 343 / short 567), bramka kosztowa 0.
- Early stopping: w 7 z 15 foldów `best_iteration` = 0 (jedno drzewo), w 4 foldach 15–36.
- **Próg = 0,424963** (kwantyl 0,80 z 910 pewności); ponad progiem 182 sygnały (long 29 / short 153).

**Tabela kalibracji (trafność sygnału: kierunek zgodny z ruchem do pierwszej bariery ±1,5·ATR albo do zamknięcia po
7 dniach; bez kosztów; ±Wald z n sygnałów i — w nawiasie — z n nienakładających się, odstęp ≥ 7 dni):**

| kubełek pewności | n | pewność od–do | trafność | ±Wald (n) | n nienakł. | ±Wald (nienakł.) |
|---|---|---|---|---|---|---|
| 1 (najniższy) | 182 | 0,3336–0,3409 | 44,5 % | ±7,2 pp | 59 | ±12,7 pp |
| 2 | 182 | 0,3409–0,3452 | 47,3 % | ±7,3 pp | 63 | ±12,3 pp |
| 3 | 182 | 0,3453–0,3540 | 59,9 % | ±7,1 pp | 59 | ±12,5 pp |
| 4 | 182 | 0,3540–0,4249 | 62,6 % | ±7,0 pp | 59 | ±12,3 pp |
| **5 = ponad progiem** | 182 | 0,4253–0,6883 | **49,5 %** | ±7,3 pp | 46 | ±14,4 pp |
| wszystkie | 910 | — | **52,8 %** | ±3,2 pp | 166 | ±7,6 pp |

Mediana pewności 0,3487 — rozkład skupiony tuż nad 1/3 (trzy klasy). Korelacja rang kubełek–trafność +0,70, ale
górny kubełek < wszystkie → **warunek „rosnąca trafność” NIESPEŁNIONY → RYZYKO** (§14.6). Reguły nie zmieniono.

**Diagnostyka po fakcie (tryb `foldy`, niepre-rejestrowana, tylko pewność — bez etykiet):** w 10 z 15 foldów żaden
sygnał nie sięga progu (maksymalna pewność 0,349–0,407); foldy 5, 6, 9, 15 dają 92,3 % sygnałów ponad progiem. Foldy
bez sygnałów ponad progiem to te z `best_iteration` 0–8. Wniosek mechaniczny: pewność w trybie `class` przy
wczesnym zatrzymaniu mierzy przede wszystkim liczbę drzew danego foldu, a górny kubełek to w praktyce „okresy
2022-04 → 2022-07, 2023-04 → 2023-09, 2024-04 → 2024-06 i 2025-09 → 2025-12”, a nie „najsilniejsze sygnały”.

### Krok 3 — model zamrożony (tryb `zamroz`)

| pole | wartość |
|---|---|
| plik / sha256 | `model_ml1.json` / `d1a39ee440dcea6a490d3b86181d8f8d7a9dd6172fec46c0b808cbb5b165195c` (drugą drogą: `sha256sum` — zgodny) |
| cechy (kolejność) | `return_lag_1, volume_zscore_20, rsi_14, funding_rate, oi_change_24h, global_ls_log, taker_imbalance_24h, vrp_30d, ex_supply_change_7d, fng_level` |
| uczenie | 2021-01-01 → 2025-12-31; 1 608 świec z etykietą i cechami, 1 601 po embargo; etykiety −1 / 0 / +1: 484 / 595 / 529 |
| drzewa | `best_iteration` 23 (early stopping zadziałał) |
| próg | 0,424963480 (udział 20 %) |
| commity | pre-rejestracja `e99dc82`, kod `35cd2c7` (czysty katalog `backtest`/`agents`) |
| kontrola | predykcje z pliku == z pamięci (1 608 świec); `.gitattributes`: `runs/*/model_*.json binary` |

Pełny manifest z sha256 sześciu plików danych: `manifest.json`.

### Krok 4 — rozbieg 2026-01-01 → 2026-09-29 (tryb `rozbieg`; tylko mechanika)

- Model z pliku, sha256 zgodny z manifestem. 272/272 świec z kompletem cech, 0 dziur w cechach.
- Long 58, short 53, bez kierunku 161 (abstynencja **59,2 %**, w walk-forward 31,4 %).
- **Ponad progiem 10 z 111 sygnałów z kierunkiem (9,0 %)** — zapisany udział 20 %. Pewność: min 0,337, mediana 0,370,
  max 0,522. Per miesiąc ponad progiem: I 3, VI 1, VIII 4, IX 2, pozostałe 0.
- Ostatnia świeca 2026-09-29: long, pewność 0,444, ponad progiem.
- Skala: ~149 decyzji z kierunkiem i ~13 ponad progiem rocznie (założenie ex ante: 227 i 45). Etykiet, trafności i
  zwrotu nie liczono.
- Mierzalność przy tempie z rozbiegu (ponad progiem ~6,7 niezależnych rocznie, nakładanie 2×; `measurability_report`,
  p\* 50,89 %): trafność potrzebna **87,9 % po roku, 78,1 % po 2 latach, 67,7 % po 5 latach** — NIEMIERZALNA przy ≤ 55 %.

## Co poszło inaczej niż w planie (wprost)

1. **Nazwa katalogu:** zlecenie podało `2026-09-30_ML1-wolny-horyzont`; strażnik `tests/test_runs_index_guard.py`
   wymaga małych liter → `2026-09-30_ml1-wolny-horyzont`.
2. **Okno testowe 91 dni zamiast 28 (SW):** na 1d fold 28-dniowy ma 28 wierszy < `MIN_TRAIN_ROWS` 30 — zapisane w §14.4
   przed uczeniem, jak Y2.
3. **Sprostowanie §5.3 karty** (brak przerwy fit/walidacja w silniku) — zapisane przed uczeniem.
4. **Tryb `foldy`** — diagnostyka dopisana po wyniku, bez etykiet; nie zmienia żadnej reguły.
5. **Dane przedłużone** do 2026-09-29 w `data/raw/ml1` (kopie z repo głównego tylko do odczytu + pobranie z publicznych
   źródeł już używanych w repo); DVOL różni się od kopii w 1 dniu (ostatni, niepełny dzień kopii).

## Bramki jakości (zasada 16)

**16a — walidacja (`data:validate-data`): Caveats.**
- Druga droga (`druga_droga.py`, bez `agents/ml1_features` i `agents/labeling`): próg ręczną interpolacją 0,424963480
  (różnica 5,6·10⁻¹⁷); trafność każdego z 910 sygnałów z własnej pętli barier na surowych świecach i ATR z TA-Lib —
  **910/910 zgodnych**; trafność wszystkich 52,75 %, ponad progiem 49,45 %, kubełki co do 0,01 pp; rozbieg z CSV
  58/53/161/10 — zgodne. sha256 modelu przez `sha256sum` — zgodny. Wald ręcznie (krok 1): zgodny do 0,0004 pp.
- Kogo NIE ma w zbiorze: fold 0 (2022-01 → 2022-04, dziura taker) i 211 świec bez kompletu cech (w tym 128 dni dziury
  taker i rozbieg DVOL); ostatnie 4 dni 2025 poza foldami testowymi; 417 świec bez kierunku (abstynencja). Kalibracja
  mówi tylko o sygnałach z kierunkiem.
- Czerwona flaga „wynik idealnie potwierdza hipotezę”: nie — wynik jej przeczy (górny kubełek najsłabszy z górnych).
- Kontrola negatywna A6: nowy moduł cech, silnik bez zmian; przeciek sprawdzony testami + kontrolą mutacyjną (przesunięcie
  klucza funding i okna odczytów na zamknięcie świecy wywraca 6 z 16 testów ML1).
- Zastrzeżenia (obowiązkowe przy cytowaniu): pewność zależy od liczby drzew foldu; próg z walk-forward nie przenosi się
  na model zamrożony (9 % zamiast 20 %); trafność bez kosztów i bez zwrotu.

**16b — statystyka (`data:statistical-analysis`):** każda trafność z ±Wald i z przybliżeniem N_eff (sygnały
nienakładające się); licznik wariantów 2 (tor P), na historii 0 (opis). Różnice między kubełkami (44,5 → 62,6 → 49,5 %)
mieszczą się w ±12–14 pp przedziałów z N_eff — nie wolno z nich wybierać „lepszego progu” (wniosek 49, zasada 1).

**16c — przegląd diffu (`engineering:code-review`): Approve z uwagami.** Dopięcia cech zgodne z kartą i testowane
(granice świecy, opóźnienia, funding o zamknięciu); brak nowych adresów sieciowych (używa `data/fetch_external` i
`fetch_ohlcv`/`fetch_funding`). Uwagi: `attach_funding_1d` nie ma limitu świeżości (przy torze P brak nowych rozliczeń
dałby starą stawkę — dodać limit w procesie toru P); `daily_log_change` liczy 7 wierszy, nie 7 dni (CoinMetrics 0 dziur
— bez skutku dziś).

## Co na plus (+) / Co na minus (−)

**+**
- Model zamrożony i odtwarzalny: hash pliku, lista cech, parametry, próg, hashe commitów i danych; predykcje z pliku
  identyczne z pamięcią.
- Pre-rejestracja przed uczeniem, jedna wartość progu, zero przeszukiwania; każda z 11 cech z testem przecieku na świecy 1d
  (kontrola mutacyjna działa).
- Zero odczytu zwrotu — zgodnie z decyzją użytkownika i z zasadą 18.
- Brama danych domknięta na serwerze: daty i dziury wszystkich źródeł.

**−**
- Reguła „wysoka pewność” nie ma oparcia w historii: górny kubełek 49,5 % wobec 52,8 %.
- Pewność modelu jest w dużej mierze artefaktem wczesnego zatrzymania (1 drzewo w 7 z 15 foldów) — próg dzieli okresy,
  a nie sygnały.
- Próg nie przenosi się na model zamrożony: 9 % zamiast 20 % na rozbiegu; ~13 transakcji ponad progiem rocznie.
- Tor P pozostaje NIEMIERZALNY w horyzoncie lat; 5 z 11 cech (6 z 10 w modelu: OI, L/S, taker, VRP, podaż) nie ma zbieracza na żywo.
- Tabela kalibracji zużyła spojrzenie na historię 2022–2025 (wiersz w rejestrze odczytów).

## Wniosek

Model ML1 istnieje, jest zamrożony i liczy sygnały na nowych danych bez dziur. To wszystko, co ta runda mogła pokazać.
Reguła użytkownika „mało transakcji, wysoka pewność” w tej postaci nie ma oparcia: najpewniejsze sygnały z lat
2022–2025 nie trafiały lepiej od pozostałych, a sama „pewność” zależy głównie od tego, ile drzew model zdążył zbudować.
Na 2026 próg przepuszcza 9 % sygnałów, czyli ok. 13 rocznie — za mało, żeby w rozsądnym czasie cokolwiek udowodnić.
Szereg „wszystkie sygnały” (~149 rocznie) też potrzebuje lat (przy trafności 55 % ~5 lat, przy 52–53 % dziesiątek).

## Rekomendacja

1. **Nie uruchamiać toru P jako procesu na tym modelu bez nowej decyzji użytkownika**, znając trzy liczby: kalibracja
   nie rośnie, próg daje 9 % zamiast 20 %, mierzalność za lata. Jeśli użytkownik mimo to chce toru P (tanio: model
   jest gotowy), to jako osobne zadania: (a) kolektory 5 cech (OI, L/S kont, taker z archiwum `metrics` dziennie; DVOL;
   CoinMetrics) z limitem świeżości, typ `zbieranie_danych`; (b) proces papierowy toru P poza `live_journal.py`, z datą
   zamrożenia = dzień uruchomienia, dwoma szeregami i progami odczytu z góry; wpięcie w harmonogram = decyzja użytkownika.
2. **Nie zmieniać progu ani trybu pewności na tym modelu** — każda zmiana (inny udział, pewność `conditional`, bez
   early stoppingu) to nowa hipoteza z nowym licznikiem i nową pre-rejestracją; kalibracja z tej rundy nie może jej wybrać.
3. Najuczciwsza alternatywa to zamknięcie ML1 bez toru P (jak 013) — rekomendacja z kroku 0 nadal obowiązuje; ta runda
   jej nie osłabiła, a raczej wzmocniła.

## Użyte skille (CLAUDE.md zasada 19)

### Użyte skille — gałąź `zadanie-028-ml1-wolny-horyzont` (rejestr automatyczny)

| czas | kto | skill | argumenty (skrót) |
|---|---|---|---|
| 2026-09-30T18:14:36+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-quant` |  |
| 2026-09-30T18:14:37+00:00 | claude (agent: general-purpose) | `anthropic-skills:quant-strategy-catalog` |  |
| 2026-09-30T18:18:47+00:00 | claude (agent: general-purpose) | `anthropic-skills:clas5-runda` |  |
| 2026-09-30T18:24:02+00:00 | claude (agent: general-purpose) | `engineering:testing-strategy` | Testy nowego modułu agents/ml1_features.py (cechy 1d: dopięcie funding, odczytów 5-min, źródeł dziennych; test przecieku shift-forward, hypothesis) |
| 2026-09-30T18:31:58+00:00 | claude (agent: general-purpose) | `data:validate-data` | Write-up rundy ML1 (runs/2026-09-30_ml1-wolny-horyzont): próg pewności z WF, tabela kalibracji, rozbieg 2026 — przeliczenie drugą drogą, kto wypada ze zbioru |
| 2026-09-30T18:31:59+00:00 | claude (agent: general-purpose) | `data:statistical-analysis` | Przedziały dla trafności w kubełkach kalibracji ML1 (n 182 na kubełek, sygnały nakładające się), liczba wariantów |
| 2026-09-30T18:32:54+00:00 | claude (agent: general-purpose) | `engineering:code-review` | git diff master...zadanie-028-ml1-wolny-horyzont: agents/ml1_features.py, backtest/run_ml1_wolny_horyzont.py, testy przecieku |

Razem: 7 wczytań, 7 różnych skilli.

Co wniósł każdy: `clas5-quant` — dyscyplina przecieku, abstynencja w `expected_trades`, dwa znaczenia marginesu, zakaz
wyboru progu po wyniku; `quant-strategy-catalog` — sprawdzenie równoważności z SW/Y2 i tor P jako jedyna droga poza
wyczerpaną historią; `clas5-runda` — kolejność pre-rejestracja → przebieg → dokumentacja i domknięcie pamięci (INDEX,
rejestr odczytów); `testing-strategy` — podział testów: jednostkowe + przeciek + właściwości (`hypothesis`) + kontrola
mutacyjna; `validate-data` — druga droga niezależna od modułu i silnika, pytanie „kogo nie ma w zbiorze”;
`statistical-analysis` — przedziały z N_eff zamiast z liczby nakładających się sygnałów; `code-review` — uwagi o limicie
świeżości funding i o `daily_log_change`.

Pominięte z tabeli zasady 19: `data:explore-data` (nowy zbiór = te same źródła co SW; profil dziur w trybie `pokrycie`),
`dataviz` (bez wykresu), `security-review` (brak kluczy API, zleceń i nowych adresów sieciowych — tylko istniejące
publiczne pobieracze repo).
