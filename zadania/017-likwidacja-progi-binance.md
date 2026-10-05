---
id: 017
tytul: Cena likwidacji — płaski próg 1/dźwignia − 1 % wobec progów depozytu Binance i ceny mark, 0 wariantów
typ: przeglad
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „tak wrzuć na tablicę z zadaniami” (po przeglądzie bibliotek)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus do metodologii, Sonnet do mechaniki"
---

# 017 — Cena likwidacji wobec progów Binance

## Po co

Dziennik liczy likwidację izolowaną płaskim progiem 1/dźwignia − MMR, gdzie MMR (wymagany depozyt podtrzymujący) to
1 % (`backtest/live_journal.py:108`, `backtest/ts_momentum.py:158`). Trend 2× jest więc likwidowany przy ruchu 49 %
przeciw pozycji, a premia Coinbase 3× przy 32,3 %. Binance liczy inaczej w dwóch miejscach:

1. wymagany depozyt zależy od monety i wielkości pozycji (progi, „maintenance amount”);
2. likwidację wyzwala cena mark (wygładzona, z indeksu kilku giełd), a nie ostatnia cena, więc knoty świec liczą się
   słabiej.

freqtrade ma wzór Binance (`freqtrade/exchange/binance.py:299` `dry_run_liquidation_price`;
`freqtrade/exchange/exchange.py:4113` `get_maintenance_ratio_and_amt`) i migawkę progów
(`freqtrade/exchange/binance_leverage_tiers.json`, stan 2026-06-18). Zadanie mówi, czy nasz model zawyża, czy zaniża
liczbę likwidacji, szczególnie na altach bez stopa. Źródło: przegląd bibliotek z 2026-09-29.

## Zakres

- **Krok 1 (sieć tylko do github.com, jednorazowo):** pobrać migawkę progów z repo freqtrade (kopia
  `piotrgebala/freqtrade`, commit 84b4628) i zapisać ją w katalogu rundy z hashem pliku. Dla BTC i monet, które były
  w koszyku top-20 point-in-time od 2021 (z `data/raw/universe_full`, nie z plików dziennika), policzyć MMR
  i maintenance amount przy nominale pozycji 1 tys., 10 tys. i 100 tys. USDT. Porównać odległość do likwidacji
  według wzoru Binance z naszym progiem, w tabeli per moneta. Ograniczenie do zapisania: migawka to dzisiejsze
  progi, nie historyczne.
- **Krok 2 (sieć tylko do data.binance.vision, archiwum `markPriceKlines` 1d albo 1h):** policzyć, jak często dzienne
  ekstremum ostatniej ceny przekracza próg, a ekstremum ceny mark nie (i odwrotnie). Podać liczbę dni i monet.
  Wczytać `data:explore-data` przy nowym archiwum.
- Katalog `runs/RRRR-MM-DD_<id>-likwidacja-progi-binance/` z `raw_output.txt`, 0 wariantów, opis, wiersz
  w `runs/INDEX.md`.

## Czego NIE robić

- Nie liczyć wpływu na zwrot strategii, bo to byłby kolejny odczyt historii. Tylko progi i liczba przekroczeń.
- Nie zmieniać MMR w dzienniku. To Poprawka N i decyzja użytkownika; wynik ma dać tylko podstawę do tej decyzji.
- Nie używać endpointu `leverageBracket`, bo wymaga klucza API. Tylko migawka z freqtrade i publiczne archiwum.
- Nie importować freqtrade (zasada 8; licencja GPL-3.0). Wzór przepisać po swojemu, z testem.

## Kryteria odbioru (dowody)

- Test jednostkowy wzoru: jedna moneta, jeden próg, wynik policzony ręcznie w teście. W README trzy przypadki
  przeliczone ręcznie (druga droga).
- `raw_output.txt`, powtarzalna komenda, hash commita i hash pliku z progami.
- Bramki 16a–c; skille `clas5-quant` (ryzyko i sizing), `clas5-runda`, `data:validate-data`, `data:explore-data`.
- Wniosek w jednym zdaniu: czy płaski próg 1 % i ostatnia cena przesuwają liczbę likwidacji na tyle, by warto było
  proponować Poprawkę.

## Wynik

- **Zrobione 2026-09-29.** Runda LP1: `runs/2026-09-29_lp1-likwidacja-progi-binance/` (README, `raw_output.txt`,
  `progi_per_moneta.csv`, `przekroczenia.csv`, migawka progów `.json.gz`, `hashe.txt`). Kod: `backtest/liq_binance.py`,
  `data/fetch_mark_1d.py`, `backtest/run_lp1_likwidacja_progi.py` (zamrożony), testy `tests/test_liq_binance.py`.
  Wniosek 111 w `runs/INDEX.md`, wiersz 59 w `runs/odczyty_historii.csv` (opis z wynikiem, nie odczyt programu,
  0 wariantów), zdanie w `STATUS.md`. Gałąź `zadanie-017-likwidacja-progi-binance` (`fe2a98d`, `eea3049`, `924ea7d`,
  `340a4ae`), scalona do master (`54a6ca3`).
- **Wynik:** przy 10 tys. USDT na monetę i oknie 7 dni płaski próg z ceny ostatniej daje prawie tyle likwidacji co progi
  Binance z ceny mark: 2× 1 530 wobec 1 552 (+1,4 %, 95 % [−2,4; +6,5]), 3× 4 578 wobec 4 482 (−2,1 %, [−4,6; +0,5]).
  Próg decyzji ±10 % → **Poprawki MMR nie proponować**. Błędy się znoszą: longi zawyżone o 5–9 %, shorty zaniżone
  o 3–4 %. Przy 100 tys. na monetę różnica +14…+17 % (post hoc, dzisiejsze progi). Bramka 16a: Caveats (migawka
  z 2026-06-18, nominał stały od wejścia, 8 monet bez progów, ucięte okna); 16c: Approve.
- **Dowody (sprawdził orkiestrator):** przebieg odtworzony — oba CSV bajt w bajt, stdout różni się tylko ścieżką zapisu
  (4 linie); sha256 progów `5db817c1…608353` zgodny po rozpakowaniu; liczby z okna 7 dni przeliczone awk z surowych cen
  w `przekroczenia.csv` (te same 1 530 / 1 552 / 4 578 / 4 482); wzór sprawdzony ręcznie (BTC, MMR 0,40 %:
  49,80 / 49,40 / 33,07 / 32,80; ADA 10 tys., MMR 1 %, cum 50 → 50,00 dla 2× long). Pełny pytest na master po scaleniu:
  1 928 passed, 2 skipped, kod 0. Dane `data/raw/mark_1d` i `data/raw/binance_tiers` skopiowane z worktree do
  `data/raw/` (poza gitem), żeby komenda z README działała z katalogu repo.
- **Zostało:** dwie luki danych z raportu wykonawcy, do decyzji użytkownika: (1) 4 pliki w `data/raw/universe_full`
  mają nazwy w kodowaniu cp866 (symbol 币安人生 wypada z kroku 2 na 1 miesiąc) — `naprawa`; (2) przy wstrzymaniu lub
  wycofaniu kontraktu cena ostatnia zamarza, a dziennik nie rozlicza wtedy likwidacji ani ceny rozliczenia (FTT 2022-12,
  LUNA 2022-05, ALPACA 2025-05) — typ `dziennik`, zmiana tylko jako Poprawka. Temat MMR wraca przy pozycjach rzędu
  100 tys. USDT na monetę.
