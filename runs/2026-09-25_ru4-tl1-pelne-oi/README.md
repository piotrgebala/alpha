# RU4 — TL1 (tłok lewara) na pełnym uniwersum i pełnym panelu OI (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (przed przebiegiem). Korekta danych jak RU1/RU2 — 0 wariantów; seria TL
> zostaje zamknięta (1/1, STOP), zmienia się tylko to, na jakich danych liczona była jej jedyna reguła.

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

_(sekcje poniżej po przebiegu)_
