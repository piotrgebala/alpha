---
id: 033
tytul: HP1 — trzy cechy z pozycji traderów Hyperliquid (po jednej, z mechanizmem); model dopiero po pozytywnej cesze
typ: badawcze
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "2026-10-18: „dodaj Propozycja na tablicę wszystkie 3 opcje” — zgoda na wpis, nie na wykonanie"
utworzono: 2026-10-18
zalezy_od: [031, 032]
budzet: "Opus; start dopiero przy werdykcie MIERZALNA"
---

# 033 — HP1: cechy z pozycji traderów Hyperliquid, potem model

## Po co

Użytkownik chce 2026-10-18 sprawdzić pozycje traderów, poszukać zależności i nauczyć model wzorców. Hyperliquid daje
coś, czego nie ma Binance:
- pozycje pojedynczych portfeli;
- ich ceny likwidacji;
- podział na traderów sprawdzonych w teście 032 i resztę.

Wniosek 90 z Binance pokazuje, że pozycjonowanie niesie tylko mały ślad informacji:
- przed kosztami +0,01…+0,05 % na transakcję, najwięcej L/S wszystkich kont: +0,054 % [+0,023; +0,085];
- XGBoost na 7 takich cechach po kosztach: −0,050 % na transakcję [−0,091; −0,010].

Model nie stworzy przewagi, której nie mają pojedyncze cechy. Dlatego najpierw testujemy cechy po jednej, a model
na końcu.

## Zakres

1. **Trzy cechy z mechanizmem, zapisane z góry.** Kolejność na liście to kolejność testów (zasada 4).
   - **C1 „za sprawdzonymi”:** pozycja netto portfeli, które przeszły test 032. Tylko jeśli wynik 032 jest dodatni.
     Mechanizm: lepsza informacja albo umiejętność.
   - **C2 „tłum kontra duzi”:** rozjazd pozycji netto małych i dużych portfeli. Mechanizm: małe konta wchodzą późno
     i z dużą dźwignią. Cecha jest bliska SW „L/S wszystkich kont” (wniosek 90) i karcie ML1 (zadanie 028). README
     musi jawnie uzasadnić, czym się różni (pojedyncze portfele, inna giełda), zgodnie z zasadą 14.
   - **C3 „mapa likwidacji”:** udział wartości dużych pozycji w odległości ≤ X od ceny likwidacji, X zapisane z góry.
     Mechanizm: wymuszone zamknięcia. E1 jako zdarzenie jest niemierzalne w ≤ 3 lata (wniosek 116). Tu cecha działa
     na zwykłej etykiecie dziennej. Jeśli jej efekt działa tylko w kaskadach, okaże się niemierzalna.
2. **Każda cecha:**
   - test leakage przed wejściem do modelu (zasada 2);
   - pomiar walk-forward (zasada 1);
   - etykieta triple-barrier z `ATR_MULTIPLIER` 1,5× (zasada 3);
   - świece dzienne, koszyk top-20 dostępny na HL (wniosek 117: 20 z 26 symboli);
   - jeden wariant na bazie „HL-pozycje”, z własnym licznikiem i progiem t 1,96.
3. **Model:** XGBoost (deterministyczny; nie LLM, zasada 6), tylko z cech, które przeszły pojedynczo. Jeden wariant.
4. **Mierzalność przed startem (zasada 18).** Rachunek z rozmowy 2026-10-18 funkcjami z `backtest/metrics.py`.
   Założenia: świece dzienne, abstynencja 0,665 (podłoga z K1), top-20 liczone jako 8,6 niezależnych monet, próg
   opłacalności 52 %, zakładana trafność 55 %.

   | Część testowa | Transakcje | ± (Wald) | Trafność potrzebna do dowodu | Przy 55 % |
   |---|---|---|---|---|
   | BTC, 1 rok | ~122 | 8,9 pp | ≥ 60,9 % | NIEMIERZALNA |
   | BTC, 2 lata | ~245 | 6,3 pp | ≥ 58,3 % | NIEMIERZALNA |
   | top-20, 1 rok | ~1 052 | 3,0 pp | ≥ 55,0 % | NIEMIERZALNA (granica) |
   | top-20, 2 lata | ~2 103 | 2,1 pp | ≥ 54,1 % | MIERZALNA |

   Do tego dochodzi okno uczące walk-forward (w SW 365 dni), więc w sumie potrzeba ok. 3 lat danych:
   - z darmowego kolektora 031: jesień 2029 r.;
   - z płatnego archiwum S3, jeśli zaczyna się od 2025-07-28 i ma adresy portfeli: lato 2028 r.

   Zakup archiwum to decyzja użytkownika. W pre-rejestracji rachunek liczy się od nowa na prawdziwej abstynencji
   i progu (dzienny ATR, koszty z `config/settings.yaml`).
5. **Wynik dodatni:** korelacja z nogami dziennika (TS1, X1, CP1) ≤ ~0,35, potem drabina dowodów (dziennik papierowy
   ≥ 3 miesiące).

Skille (zasada 19): `clas5-quant`, `quant-strategy-catalog`, `clas5-runda`, `engineering:testing-strategy`,
`data:statistical-analysis`, `data:validate-data`, `engineering:code-review`. Gdy skill jest niedostępny:
„niedostępny w sesji” i procedura z repo.

## Czego NIE robić

- Żadnego przeszukiwania kombinacji cech, okien i progów (zasada 4: grid search zakazany). X, okna i progi są zapisane
  z góry i nie są strojone na całym zbiorze (zasada 1).
- Nie wybierać „najlepszych portfeli” na podstawie danych z dnia decyzji ani późniejszych. Test leakage musi wyłapać
  taki przeciek.
- Nie startować przy werdykcie NIEMIERZALNA. Nie kupować archiwum bez decyzji użytkownika.
- LLM poza ścieżką decyzji. Żadnych zleceń, kluczy ani MCP Liquid.

## Kryteria odbioru (dowody)

- Pre-rejestracja (cechy, X, okna, etykieta, rachunek mierzalności) w commicie przed wynikiem.
- Test leakage każdej cechy, testy jednostkowe i test `hypothesis` (zasada 10). `py -m pytest -q` zielone.
- Katalog rundy z README (zasada 11) i `raw_output.txt`; wiersz w `runs/INDEX.md` z licznikiem „HL-pozycje”.
- Checkpoint v2 (zasada 12): t / t_neff i rozbicie przewagi. Kluczowa liczba przeliczona drugą drogą. Werdykt
  Ready / Caveats / Revision.

## Wynik

(dopisuje orkiestrator)
