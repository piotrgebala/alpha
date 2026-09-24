# Dziennik na żywo (papierowo) — trend tygodniowy + premia Coinbase

> **STATUS: DZIAŁA od 2026-09-24 (poprawka 1: start przesunięty z 25.09 na 24.09).** Reguły poniżej są zamrożone —
> każda zmiana = nowy dziennik od zera (inaczej wynik przestaje być „na danych, których nie
> oglądaliśmy”).

## Po co — prostym językiem

Na historii nie da się już uczciwie sprawdzić naszych dwóch kandydatów: wybraliśmy je spośród
~30 pomysłów na tych samych latach, a lata sprzed 2022 to inny rynek (decyzja użytkownika).
Dziennik liczy codziennie, jakie pozycje wziąłby portfel, i zapisuje je **zanim** poznamy wynik.
Przez pierwsze 2–3 miesiące sprawdzamy **mechanikę** (czy sygnał liczy się na czas, czy dane
przychodzą kompletne, czy nic nie zmienia się wstecz), a nie to, czy strategia zarabia — na to
2–3 miesiące to za mało (działająca strategia bywa po takim czasie na minusie w ~1 na 3 przypadki).

## Reguły (zamrożone)

| składowa | reguła | instrument | dźwignia (likwidacja izolowana) |
|---|---|---|---|
| trend tygodniowy (TS1, wnioski 70/74) | znak zwrotu 28 dni, waga ∝ 0,40/σ̂ (sufit 3), 7 faz tygodniowych | koszyk top-20 perpetuali po obrocie z ostatnich 30 dni, skład co miesiąc | 2× (LQ1, wniosek 76) |
| premia Coinbase (CP1, wniosek 72) | znak (średnia premii 7 dni − 90 dni) | BTCUSDT | 3× |
| łączenie (SZ1 R1, wniosek 77) | budżet ryzyka: wagi ∝ 1/σ, cel 20 %/rok, sufit mnożnika 2, przeliczane co 7 dni, **bez hamulca** | — | — |

- Koszt: taker 0,05 % + poślizg z `config/settings.yaml` × obrót; funding realny.
- Silnik identyczny z rundami: `backtest/live_journal.py` woła `ts_momentum.portfolio`,
  `run_coinbase_cp1.daily_premium/premium_signal`, `sizing.apply_rules` (bez kopii).
- Silnik startuje 2025-09-01 (rozbieg budżetu ryzyka ≥ 1 rok); **wynik papierowy liczy się od
  2026-09-24** (poprawka 1), kapitał początkowy = 1.
- Dane: `data/raw/live/` (poza gitem), pobierane od nowa przy każdym przebiegu z publicznych API
  Binance (perpetuale, spot BTC 8h) i Coinbase (BTC-USD 1d); tylko świece zamknięte.

## Poprawka 1 (2026-09-24, ok. 10:00 UTC — przed zamknięciem dnia, wynik nieznany)

Decyzja użytkownika: „dziennik niech działa już dzisiaj, a nie od jutra”. Start wyniku papierowego
przesunięty z 2026-09-25 na **2026-09-24**. Uczciwość zapisu: pozycje na 24.09 zostały policzone
z danych do zamknięcia 23.09 i zapisane w `sygnaly.csv` o 09:46 UTC 24.09 — przed poznaniem wyniku
dnia; sygnał nie zależy od cen z 24.09. Zastrzeżenie tylko dla pierwszego dnia: wynik liczony od
zamknięcia 23.09 (00:00 UTC), a realne wejście byłoby możliwe dopiero ok. 09:46 UTC — w odczycie
dzień 24.09 pokazywany osobno.

## Codziennie

```
PYTHONUTF8=1 py -m backtest.live_journal
```

Najlepiej zaraz po zamknięciu dnia UTC (od 02:00 czasu polskiego latem, od 01:00 zimą); pobranie trwa ~10 min.
Wydruk mówi: mnożniki R1, wynik od startu, obsunięcie i status progów, ekspozycję i depozyt każdej
składowej oraz zlecenia fazy formowanej dziś (kierunek i nominał jako % kapitału).

## Co zapisujemy (append-only, w gicie)

- `sygnaly.csv` — pozycje ogłoszone na dzień po `as_of` (ostatnia zamknięta świeca): składowa,
  faza, symbol, znak, waga, mnożnik, ekspozycja, depozyt. Raz zapisane — nigdy nie zmieniane.
- `wyniki.csv` — dzienny wynik papierowy: zwroty składowych, mnożniki, zwrot portfela, kapitał,
  obsunięcie. Istniejących wierszy przebieg nie zmienia; różnica przy przeliczeniu → „HISTORIA
  ZMIENIONA” w wydruku i w logu.
- `przebiegi.log` — czas przebiegu, ostatnia świeca każdego źródła, liczba dopisanych wierszy,
  status progów.

## Progi (zapisane z góry)

- **OSTRZEŻENIE:** obsunięcie ≥ **17,7 %** (największe obsunięcie R1 w historii 2021–2026, SZ1).
- **STOP:** obsunięcie ≥ **26,5 %** (1,5 × powyższe) — dziennik się nie wyłącza sam; decyzja
  o przerwaniu należy do użytkownika, a sygnał STOP trafia do raportu.

## Odczyt po ~3 miesiącach (ok. 2026-12-25) — kryteria mechaniki

1. **Kompletność:** sygnał policzony w ≥ 95 % dni (liczone z `przebiegi.log`).
2. **Spójność:** 0 niewyjaśnionych przypadków „HISTORIA ZMIENIONA”.
3. **Terminowość:** dane z poprzedniego dnia dostępne przy przebiegu w ≥ 95 % dni.
4. **Zgodność z założeniami SZ1:** depozyt w medianie 15–35 % kapitału, mnożniki w granicach sufitu.
5. **Wynik (opisowo, bez werdyktu):** zwrot z przedziałem, dopisany do wspólnego rachunku „poza
   próbą” razem z CP1P i TP1. Nie jest testem przewagi.

## Sprawdzian przed startem (2026-09-24)

- **Zgodność z backtestem** na wspólnym okresie 2025-10-15 → 2026-06-29 (258 dni), dane świeże vs
  zamrożone cache rund: premia Coinbase — korelacja dzienna **1,0000**, suma +69,6 % vs +69,2 %;
  trend — korelacja **0,981**, suma +10,5 % vs +12,8 % (różnica = uniwersum na żywo bez monet
  wycofanych; patrz niżej). Skrypt: sprawdzenie jednorazowe w sesji, liczby tutaj.
- **Idempotencja:** drugi przebieg tego samego dnia dopisał 0 wierszy, 0 zmian historii.
- **Przegląd bezpieczeństwa** (`security-review`): brak podatności z realną drogą ataku; wdrożona
  jedna sugestia — nazwa symbolu z odpowiedzi giełdy musi pasować do `[A-Z0-9]{1,40}USDT`, zanim
  trafi do nazwy pliku (test `test_symbol_names_are_safe_for_file_paths`).
- **Błąd znaleziony i poprawiony przed startem:** plik `coinbase_BTC-USD_1d.parquet` był wczytywany
  jak kolejna „moneta” (bez wpływu na pozycje — brak obrotu, poza koszykiem), a świeca Coinbase
  z bieżącego, niezamkniętego dnia trafiała do danych. Teraz: tylko pliki perpetuali i tylko
  zamknięte dni (test `test_coinbase_file_is_not_a_symbol`).
- Pobranie: świece wszystkich ~520 perpetuali, funding tylko dla członków koszyka od 2025-09
  (~75 monet) + BTC — ~10 min.

- **Przegląd kodu** (`engineering:code-review`): **Approve** — silnik bez kopii, zapis tylko dopisuje,
  zmiana historii wykrywana; poprawka: dzień `as_of` liczony z ostatniej świecy BTC, nie z dowolnej monety.

## Znane przybliżenia

- Wyświetlane pozycje to wagi z dnia formowania każdej fazy — bez dryfu cen w tygodniu i bez
  likwidacji w trakcie tygodnia. **Wynik** liczy silnik z dryfem i likwidacjami (jak w backteście).
- Uniwersum na żywo to aktywne perpetuale: moneta wycofana w trakcie miesiąca znika z danych
  (w backteście zostawała do końca notowań).
- Wynik zakłada wykonanie po cenie zamknięcia dnia; realne zlecenie złożone kilka godzin później
  będzie miało inną cenę — to jeden z celów sprawdzianu mechaniki.
