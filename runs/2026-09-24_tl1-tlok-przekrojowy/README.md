# TL1 — tłok lewara na przekroju monet (open interest × kierunek ruchu) (2026-09-24)

> **STATUS: ZAMKNIĘTA — NIEROZSTRZYGNIĘTY (punktowo ujemny):** −10,5 %/rok [−25,2; +4,2],
> t_neff −1,39; IC tygodniowe +0,008 [−0,024; +0,040] — sygnał bez informacji, stratę robią koszty
> obrotu (23,6 % w 4,5 roku). Pre-rejestracja `3983e3a`. **Seria TL: 1/1, STOP.** Walidacja:
> **Caveats** (H0 węższe niż portfel realny); przegląd: **Approve**.
> Poprzednio: **PRE-REJESTRACJA (przed pomiarem).** Decyzja użytkownika 2026-09-24: „sprawdź 3 nowe
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

## Wynik

`raw_output.txt` (669 s): 1 652 dni (2021-12-15 → 2026-06-30), 7 faz.

| miara | wartość |
|---|---|
| **zwrot netto [CI 95 %]** | **−10,5 %/rok [−25,2; +4,2]**, t_neff −1,39 |
| H0 (50 portfeli, crowd przesunięty) | q97,5 +5,7 %/rok; TL1 poniżej wszystkich (zastrzeżenie niżej) |
| Σ brutto / funding / koszt | −31,2 % / +7,5 % / 23,6 % |
| noga long / zwrot monet nogi short | −36,4 %/rok / −22,6 %/rok |
| per rok (Σ netto) | 2021 +2,5 · 2022 −25,1 · 2023 +6,0 · 2024 −30,0 · 2025 −8,1 · 2026 +7,3 % |
| 7 faz (%/rok) | −12,7 / −9,5 / −20,6 / −27,7 / −15,4 / +8,5 / +1,3 |
| **werdykt** | **NIEROZSTRZYGNIĘTY** |

## Co na plus (+) / Co na minus (−)

**(+)** Nowe źródło danych w repo (dzienny OI z archiwum, point-in-time, 99,7 % pokrycia); test
czysty, pre-rejestrowany.
**(−)** Sygnał nie niesie informacji (IC ≈ 0), a obrót jest wysoki — koszty 23,6 % w 4,5 roku.
**Zastrzeżenie do H0:** zmienność portfeli H0 (8,4 %/rok) jest o połowę mniejsza niż portfela
realnego (16,0 %/rok) — przesunięty sygnał daje fazom bardziej różne nogi, więc średnia 7 faz
bardziej się dywersyfikuje; stwierdzenie „poniżej wszystkich portfeli H0” nie jest wiarygodne,
rozstrzyga t_neff. **Kogo nie ma:** rozbieg XI–XII 2021, 0,3 % braków OI u członków.

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data`: **Caveats** (H0). Druga droga bez silnika (`walidacja.py`): IC tygodniowe
Spearmana crowd vs zwrot 7 dni, 236 tygodni: **+0,008 [−0,024; +0,040]**, 51,7 % dodatnich —
brak informacji, zgodne z brutto ≈ −7 %/rok w granicach szumu. `data:statistical-analysis`:
odwrócenie znaku (long tłok) to hipoteza post hoc (wniosek 49) — IC ≈ 0 i tak jej nie wspiera.
`engineering:code-review`: kolektor tylko przez `http_get` (https, stałe hosty, symbol kodowany,
404 = brak pliku); crowd z danych ≤ t (test); nogi z `signal_row.name` (test). **Approve.**

## Wniosek

**Prostym językiem:** to, że na monecie przybywa lewara w kierunku ostatniego ruchu, nie
mówi nic o tym, co zrobi w następnym tygodniu. Strategia na tym sygnale straciła ok. 10 %
rocznie, głównie na prowizjach za częste przebudowy. Tłok z otwartych pozycji, podobnie jak
funding (TF1), nie wyznacza końca ruchu w tych danych.

## Rekomendacja

Seria TL: 1/1, STOP; nie odwracać znaku. Dane OI zostają w repo (`data/fetch_oi_panel.py`) jako
źródło do ewentualnych przyszłych hipotez z nowym mechanizmem. Użyte skille (rejestr
`runs/skille/tl1-tlok-przekrojowy.jsonl`): `clas5-runda`, `clas5-quant`, `data:explore-data`
(profil panelu OI), `data:validate-data`, `data:statistical-analysis`, `engineering:code-review`.
Pominięte: `testing-strategy` (4 testy według wzorca TS1/NL1), `security-review` (bez nowego hosta
ani kluczy — ten sam `http_get` co P3), `dataviz`.
