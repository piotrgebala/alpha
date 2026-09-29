---
id: 017
tytul: Cena likwidacji — płaski próg 1/dźwignia − 1 % wobec progów depozytu Binance i ceny mark, 0 wariantów
typ: przeglad
status: nowe
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

(dopisuje orkiestrator)
