# OS1 — otwarcia sesji (Tokio, Londyn, Nowy Jork) na BTC perp: rachunek mierzalności (2026-09-28)

> **STATUS: PRE-REJESTRACJA** (wynik poniżej po przebiegu).

## Metadane

- ID: **OS1**. Pomysł użytkownika 2026-09-28: „czy na momentach otwarcia sesji w Nowym Jorku, Europie czy Azji
  można zarobić”. Rodzina katalogu: **G1 — efekty kalendarzowe** (zbiór informacyjny: zegar + OHLCV własne;
  formuła jednoaktywowa, reguła bez modelu; target: kierunek; horyzont: godziny).
- Branch `os1-otwarcia-sesji` (z `master` `0bfeef5`). Kod: `backtest/run_os1_otwarcia.py` (tylko rachunek ex ante),
  `tests/test_os1_otwarcia.py`. Komenda: `PYTHONUTF8=1 py -m backtest.run_os1_otwarcia --moc` → `raw_output.txt`.
- Dane: natywne świece **30m** BTCUSDT perp (Binance USDT-M) od 2021-01-01 (zasada 20) do końca bazy
  (`data.end` 2026-07-01). Siatka 30 min trafia dokładnie w każde otwarcie, także 13:30/14:30 UTC.

## Poprzedzające wyniki

Przeczytane: skrót stanu wiedzy, wnioski 12/39/69/85 (kierunek BTC z wykresu na 5m/1h/4h ≈ 50 % na dużych
próbach), 53 (rzadkie zdarzenia — test rodziny zamiast losów), 81 (SH1: godzina fixingu ETF NIEMIERZALNA,
±0,047 %/dzień wobec 0,01–0,03 %), 99 (KO1: koszty), 104 (MX2: filtr „sesja USA 13–21 UTC” NIEMIERZALNY),
96 (DSR: ~40 odczytów na tej historii). **Wynika z nich:** godzinowy kierunek BTC to prior bliski monecie, a koszt
jednego obrotu jest duży wobec ruchu w ciągu kilku godzin — runda ma sens tylko wtedy, gdy rachunek mierzalności
przejdzie z priorem z literatury; sesje łączymy w jeden test rodziny, a nie trzy losy.

Literatura (przegląd 2026-09-28, subagent z wyszukiwaniem; liczby niezweryfikowane u źródła oznaczone):
- Brak recenzowanego, istotnego efektu KIERUNKOWEGO przypisanego do otwarcia jednej sesji.
- Momentum dnia w krypto (Shen, Urquhart, Wang 2022, *Financial Review*): pierwsza półgodzina doby UTC
  przewiduje ostatnią, R² ≈ 1,44 % w próbie (liczba z agregatorów — **niezweryfikowana** w tekście).
- Kraken 2016–2025 (MDPI 2025/26): 25 reguł momentum/odwrotu × 12 granic sesji — test SPA Hansena i bootstrap
  **nie odrzucają** zerowej hipotezy (najlepsza reguła nieodróżnialna od przypadku).
- K33 (2026, dane minutowe 2025–26): mit „wyprzedaży o 10:00 w Nowym Jorku” obalony; na otwarciu szczytuje
  zmienność, nie kierunek. Baur i in. (2019): wzorce zwrotów w ciągu doby nietrwałe, trwały tylko wolumen.
- Największa znana „godzina” (Padysak–Vojtko, Quantpedia 2022/2024): 22:00 UTC ≈ +0,07 %/h — wybrana z 24 godzin
  i NIE jest otwarciem sesji; reguła 21–23 UTC ~33 %/rok przed kosztami, które przy codziennym obrocie ją zjadają.

## Pre-rejestracja (zapisana przed jakąkolwiek liczbą tej rundy)

**Hipoteza:** na otwarciu sesji BTC perp ma ruch kierunkowy, który prosta reguła zamienia na zysk po kosztach.
**Mechanizm (kandydat):** zlecenia zebrane poza godzinami regionu trafiają na rynek przy otwarciu (w USA dodatkowo
dane makro 08:30 ET) — impuls ceny, potem kontynuacja (momentum dnia) albo odwrót (premia dla dostarczającego
płynność). Literatura na krypto nie rozstrzyga znaku.

**Jedna zmienna:** zakotwiczenie wejścia w momencie otwarcia sesji. Wszystko inne ustalone z góry:
- Otwarcia (strefy IANA, czas letni/zimowy automatycznie): Tokio 09:00 JST (00:00 UTC), Londyn 08:00 czasu
  lokalnego (07:00/08:00 UTC), Nowy Jork 09:30 ET (13:30/14:30 UTC). Dni pon–pt, bez kalendarza świąt (~4 % dni
  bez sesji rozmywa efekt — uproszczenie zapisane z góry).
- **F1 „dryf otwarcia”:** pozycja w oknie [otwarcie, +60 min]; kierunek = znak średniej tego samego okna z poprzednich
  365 dni (bez przyszłości; min. 65 obserwacji, czyli start ~kwiecień 2021).
- **F2 „momentum otwarcia”:** kierunek z ruchu [otwarcie, +30 min]; pozycja [+30 min, +4 h] (3,5 h); okna trzech
  sesji się nie nakładają.
- Ramiona: **2 łączne** (F1-razem, F2-razem; każdy dzień daje do 3 transakcji). Wyniki per sesja tylko opisowo.
- Koszt obrotu: główny **taker/taker 0,14 %** (`round_trip_cost_fraction()`: wejście o konkretnej godzinie wymaga
  zlecenia rynkowego); wrażliwość: wejście limitem 0,09 %.
- Kryterium POZYTYWNY (gdyby ramię ruszyło): `t_neff > 2,241` (z dla 2 ramion) zwrotu netto ORAZ `ci_low(p) > p*`.
  NEGATYWNY: `t_neff < −1,96` przy `n ≥ required_trades`. W granicy dużego `n` kryterium tylko łagodnieje — nie karze celu.

**Rachunek mierzalności (zasada 18):** `measurability_report(prior, p*, n)`, `p* = break_even_hit_rate(C, B)`,
`B` = średni ruch bez znaku w oknie pozycji (rozrzut — bez kierunku), `n` = dni robocze z pełnym oknem (dla reguły
bez modelu: częstość zdarzenia = 1 na sesję i dzień), N_eff przyjęte = n (górna granica, korzystna dla hipotezy).
Priory — górne granice, nie oczekiwania: **F2** ρ = 0,12 (R² 1,44 %, w próbie) → trafność 0,5 + arcsin(ρ)/π;
**F1** dryf 0,07 %/h (najlepsza z 24 godzin) → trafność Φ(0,0007/σ okna). Dodatkowo konwencja projektu 56 %.
Filtr katalogu G1: efekt z badań ≥ 1,4 × niepewność. **Decyzja:** ramię NIEMIERZALNE z priorem z literatury nie
startuje; ramię MIERZALNE z tym priorem — jeden przebieg w osobnym commicie.

**Reguła STOP (seria OS):** najwyżej 2 ramiona. Inne okna, czasy trzymania, sesje, odwrócenie znaku albo filtry —
tylko decyzją użytkownika i nową pre-rejestracją.
