# RU4 — TL1 (tłok lewara) na pełnym uniwersum i pełnym panelu OI (2026-09-25)

> **STATUS: ZAMKNIĘTA — werdykt TL1 bez zmian: NIEROZSTRZYGNIĘTY.** Na pełnym uniwersum i pełnym panelu OI:
> +8,1 %/rok [−17,5; +33,7], t_neff 0,62 (było −10,5 %/rok, t −1,39) — znak się odwrócił, 7 faz od −44 do +35 %/rok:
> szum. Pokrycie sygnału 99,6 %. Korekta danych, 0 wariantów; seria TL zamknięta (STOP). Walidacja: **Caveats**; przegląd: **Approve**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

TL1 sprawdzał, czy „tłok lewara” (szybki wzrost otwartych pozycji w kierunku ruchu ceny) zapowiada
odwrót. Liczony był jednak na obciętej liście monet (287 z 685 — błąd wykryty w RU1), więc część koszyka
była inna niż naprawdę. Inne rundy przeliczyliśmy już w RU2; TL1 czekał na dane o otwartych pozycjach
dla brakujących monet. Teraz je dociągamy i liczymy tę samą regułę jeszcze raz.

## Metadane

- Branch `tl1-pelne-oi` (z `master` `56ebb58`).
- Dane: `data/fetch_oi_panel.py` z nowym parametrem `universe_dir` i ponownym użyciem istniejącego panelu
  (`missing_jobs`, test w `tests/test_crowding_tl1.py`) → `data/raw/oi_panel/oi_daily_full.parquet`
  (archiwum `data.binance.vision`, jak TL1; stary panel nietknięty dla odtwarzalności TL1).
- Skrypt: `backtest/run_tl1_full_ru4.py` — zamrożony `run_crowding_tl1` bez zmian, podmienione
  `UNIVERSE_DIR = universe_full` i `OI_PANEL = oi_daily_full`. Komendy:
  `PYTHONUTF8=1 py -m backtest.run_tl1_full_ru4 --moc` → `moc.txt`; `PYTHONUTF8=1 py -m backtest.run_tl1_full_ru4` → `raw_output.txt`.

## Poprzedzające wyniki

TL1 (75): −10,5 %/rok [−25,2; +4,2], NIEROZSTRZYGNIĘTY, IC ≈ 0 — na obciętym uniwersum (AU1 87c: „nie czwarty
dowód”). RU1 (82) / RU2 (83): korekta uniwersum nie zmieniła żadnego werdyktu innych rund.

## Pre-rejestracja

- **Reguła i kryterium bez zmian (z README TL1):** crowd = Δlog(OI, 7 dni) · znak(zwrot 7 dni); short 5 z największym,
  long 5 z najmniejszym; 7 faz; POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0 (50 portfeli, crowd przesunięty
  cyklicznie); NEGATYWNY, gdy górny kraniec CI < 0; inaczej NIEROZSTRZYGNIĘTY.
- **Warunek danych:** pokrycie sygnału u członków (wypisuje TL1) ≥ 90 % średnio — inaczej wynik z zastrzeżeniem.
- **Odczyt:** nowe liczby zastępują TL1 we wniosku 75 (dopisek „[korekta RU4]”); werdykt wg kryterium TL1.
- **Czego runda NIE robi:** nie zmienia okna, nóg ani znaku; nie otwiera serii TL.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Po uzupełnieniu brakujących monet wynik „tłoku lewara” zmienił znak: z −10 % rocznie na +8 %. To samo
w sobie mówi najwięcej — reguła jest tak niestabilna, że dołożenie kilku monet do koszyka odwraca wynik,
a zależnie od dnia tygodnia startu waha się od −44 % do +35 % rocznie. Werdykt zostaje ten sam:
**nic nie wiadomo** — i nie ma sensu badać tego dalej na tej historii (seria zamknięta).

## Wynik

Pełny stdout: `raw_output.txt` (315 s), rachunek mocy: `moc.txt`. Panel OI (`data:explore-data`): 36 357 dni-symboli,
185 symboli (było 114), 0 duplikatów, 0 OI ≤ 0, Δlog OI 7 dni p1/p99 −0,52/+0,72, 43 skoki > 4,5× (było 5 — więcej
małych monet); 10 838 dni dociągniętych z archiwum, reszta z panelu TL1.

| | TL1 (obcięte uniwersum) | **RU4 (pełne)** |
|---|---|---|
| zwrot netto | −10,5 %/rok [−25,2; +4,2] | **+8,1 %/rok [−17,5; +33,7]** |
| t_neff | −1,39 | **+0,62** |
| sd | 16,0 %/rok | 27,8 %/rok |
| Σ brutto / funding / koszt | −31,2 / +7,5 / 23,6 % | +38,7 / +22,0 / 24,0 % |
| 7 faz (%/rok) | −27,7 … +8,5 | −43,8 … +35,4 |
| per rok | 2022 −25, 2024 −30 | 2022 −37, 2023 +36, 2024 −13, 2025 +43 |
| **werdykt** | NIEROZSTRZYGNIĘTY | **NIEROZSTRZYGNIĘTY** |

## Co na plus (+) / Co na minus (−)

**(+)** Luka danych z RU2 zamknięta; pokrycie 99,6 %; stary panel nietknięty (TL1 odtwarzalny); średnia 7 faz
przeliczona drugą drogą z wydruku faz (7,76 %/rok vs 8,1 — różnica ze wspólnego okna faz).
**(−)** **Zastrzeżenie do przyrządu TL1 (dotyczy też oryginału):** portfele H0 (sygnał przesunięty w czasie) mają
zmienność 4,6 %/rok wobec 27,8 %/rok prawdziwej strategii (w TL1: 8,4 vs 16) — przesunięty sygnał trafia na mniej
członków z danymi, więc q97,5 H0 i „powyżej 100 % H0” są tu mało warte; werdykt opiera się na t_neff (0,62), który
kryterium i tak blokuje. Funding (+22 %) niesie dużą część brutto. **Kogo nie ma:** OI przed 2021-12 (archiwum altów),
monety bez pliku metrics w dniu członkostwa (0,4 % dni).

## Walidacja (16a), przegląd (16c)

`data:validate-data`: druga droga (średnia faz) zgodna; zastrzeżenie H0 jak wyżej — **Caveats**. `engineering:code-review`
(samodzielnie): `fetch_oi_panel.run` — domyślne zachowanie bez zmian (`universe_dir` = obcięte, `reuse` = brak), nowy plik
wyjściowy; `missing_jobs` z testem; RU4 podmienia tylko stałe zamrożonego modułu (wzorzec RU1). Pre-rejestracja zapisana,
zanim wczytano skille procedury na tej gałęzi (skille wczytane przed przebiegiem, po zapisie kodu — przeoczenie kolejności).
**Werdykt jednym zdaniem: Approve** — zmiana pobieracza jest wstecznie zgodna i przetestowana, a przeliczenie używa
zamrożonej reguły bez kopii.

## Wniosek

**Prostym językiem:** tłok lewara na koszyku monet — nadal nic; po poprawieniu danych wynik skacze na drugą stronę zera,
co potwierdza, że to szum. **Technicznie:** +8,1 %/rok [−17,5; +33,7], t 0,62, NIEROZSTRZYGNIĘTY; seria TL zamknięta.

## Rekomendacja

1. TL1 zamknięty ostatecznie (dane kompletne). Wniosek 75 z dopiskiem [korekta RU4].
2. Pełny panel OI (`oi_daily_full.parquet`) gotowy dla ewentualnych przyszłych reguł przekrojowych (AU2: przyrząd widzi IC ≥ 0,022).
3. Przy przyszłych testach przekrojowych: H0 z przesunięciem sygnału sprawdzać pod kątem zmienności (tu 6× niższa niż strategia).

## Użyte skille

Rejestr `runs/skille/tl1-pelne-oi.jsonl`: `clas5-runda`, `clas5-quant` (wczytane przed przebiegiem, ale po zapisie kodu),
`data:explore-data` (profil panelu OI), `data:validate-data` (druga droga, zastrzeżenie H0), `engineering:code-review` (Approve).
Pominięte: `engineering:testing-strategy` — jeden test pomocniczej funkcji według wzorca (świadomie); `data:statistical-analysis` —
runda odtwarza zamrożone liczenie TL1 bez nowych statystyk; `security-review` — połączenie sieciowe to istniejące archiwum
Binance z `fetch_external.http_get` (sprawdzone w P3/TL1), bez nowego hosta.
