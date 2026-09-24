# TL1 — tłok lewara na przekroju monet (open interest × kierunek ruchu) (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „sprawdź 3 nowe
> hipotezy” — trzecia hipoteza (po CP1 i TF1). **NOWA SERIA TL (zbiór informacyjny:
> pozycjonowanie/OI na przekroju), 1/1, STOP.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Otwarte pozycje (open interest, OI) mówią, ile lewara siedzi w danej monecie. Jeśli przez tydzień
moneta rośnie, a OI rośnie jeszcze szybciej, to znaczy, że gracze gonią ruch na dźwigni — taki
tłok często kończy się falą likwidacji. Co tydzień: **short 5 monet z największym „tłokiem za
ruchem”, long 5 z najmniejszym** (lewar ucieka albo tłok stoi po stronie spadku). Portfel jest
neutralny na rynek jak X1. Test zobaczy efekt rzędu 8 % rocznie lub większy.

## Metadane

- Branch: `tl1-tlok-przekrojowy`.
- **Nowe źródło danych:** `data/fetch_oi_panel.py` → `data/raw/oi_panel/oi_daily.parquet`
  (archiwum `data.binance.vision` metrics, ostatni odczyt dnia ≈ 23:55 UTC, dni członkostwa
  w top-20 + 10 dni rozbiegu): 35 745 dni-symboli, 114 symboli, 2021-11-21 → 2026-06-30; profil
  `profil_danych.txt` (0 duplikatów, 0 OI ≤ 0, Δlog OI 7 dni p1/p99 −0,47/+0,46, brak masy
  punktowej, 5 skoków > 4,5×). Pokrycie crowd u członków 99,7 % (min miesiąc 93,4 %).
- Kod: `backtest/run_crowding_tl1.py` (na `runs/ZAMROZONE.txt`), testy `tests/test_crowding_tl1.py`
  (4: znak crowd i brak przyszłości, nogi, ostatni odczyt, dni potrzebne). Komendy:
  `PYTHONUTF8=1 py -m backtest.run_crowding_tl1 --moc` → `moc.txt`;
  `PYTHONUTF8=1 py -m backtest.run_crowding_tl1` → `raw_output.txt`.

## Poprzedzające wyniki

- **O1 (wniosek 66):** zmiana OI 24h jako 5. cecha modelu 4h BTC — ≈ 0. TL1: inny horyzont
  (tydzień), inna formuła (ranking przekrojowy 20 monet), OI łączone z kierunkiem ruchu.
- **X1/X2 (B1):** ranking po zwrocie 28 dni; TL1 rankuje po lewarze dokładanym za ruchem 7-dniowym
  — pokrewne przez znak zwrotu; korelacja z X1 do raportu opisowego.
- **TF1 (wniosek 73):** funding jako filtr trendu — zero. TL1 używa OI, nie fundingu.

## Pre-rejestracja

- **Hipoteza:** portfel long niski crowd / short wysoki crowd ma dodatni zwrot netto.
- **Mechanizm:** przymusowe zamykanie przelewarowanych pozycji (likwidacje, stopy) po okresie,
  w którym lewar gonił ruch.
- **DOKŁADNIE JEDNA zmienna:** sygnał crowd = Δlog(OI, 7 dni) · znak(zwrot 7 dni), dane ≤ t;
  reszta = silnik X1 (`xs_momentum.long_short_returns`: kapitał 0,5 + 0,5, 5 + 5 monet, trzymanie
  7 dni, koszt 0,07 % × obrót, funding per symbol), **7 faz**, top-20 point-in-time, start
  2021-12-15 (OI altcoinów w archiwum od 2021-12).
- **Kryterium:** POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0 (crowd przesunięty
  cyklicznie o losową liczbę tygodni, 50 portfeli); NEGATYWNY, gdy górny kraniec CI < 0;
  inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (`moc.txt`):** 1 652 dni; zmienność H0 8,4 %/rok; **half-width 7,7 %/rok =
  0,92 SR**; q97,5 H0 +5,7 %/rok → MIERZALNA dla efektu ≥ ~8 %/rok; słabsze niewidoczne.
- **Kontekst multiple testing:** ~31 odczytów w dwa dni.
- **Czego runda NIE robi:** nie stroi okna 7 dni, liczby monet w nogach ani nie odwraca znaku.

---

_(sekcje poniżej po przebiegu)_
