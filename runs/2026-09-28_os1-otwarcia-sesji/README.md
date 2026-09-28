# OS1 — otwarcia sesji (Tokio, Londyn, Nowy Jork) na BTC perp: rachunek mierzalności (2026-09-28)

> **STATUS: ZAMKNIĘTA — NIEMIERZALNA, nie startuje (0 wariantów zużytych).** Wszystkie ramiona (2 łączne + 6 per
> sesja, oba koszty) wymagają trafności 56,5–70 %, a najlepszy prior z literatury daje 52,8–54,0 %; nawet konwencja
> projektu 56 % nie przechodzi. Kolejność w gicie: pre-rejestracja + kod `ad1bd0d` → przebieg → wynik.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Pytanie: czy da się zarabiać na BTC w chwili otwarcia giełd w Tokio, Londynie albo Nowym Jorku. Zanim cokolwiek
policzyliśmy na zyskach, sprawdziliśmy, czy nasz „przyrząd” (5,5 roku danych, około 1 430 dni roboczych na sesję)
w ogóle jest w stanie taki zarobek zobaczyć. Odpowiedź brzmi: **nie**.
- Jedna transakcja (wejście i wyjście zleceniem rynkowym) kosztuje 0,14 % wartości pozycji. BTC w ciągu godziny
  po otwarciu rusza się przeciętnie o 0,4–0,7 %, a w ciągu 3,5 godziny o 0,7–1,1 %. Koszt zjada więc dużą część
  typowego ruchu. Reguła musiałaby trafiać kierunek w 56–64 % przypadków tylko po to, żeby wyjść na zero.
- Do tego dochodzi niepewność pomiaru: ±1,5 pkt proc. dla trzech sesji razem. Żeby wynik był rozstrzygający, reguła
  musiałaby trafiać w 59–65 % przypadków, a z wejściem zleceniem z limitem ceny (tańszym, ale nie zawsze się
  wykonuje) w 56,5–60 %.
- Badania dają najwyżej około 54 %, i to w wersji najbardziej optymistycznej: liczba z próby, której nie udało się
  sprawdzić u źródła. Nowsza praca (Kraken 2016–2025) po korekcie na liczbę sprawdzonych reguł nie odróżnia
  najlepszej reguły od przypadku. Otwarcie w Nowym Jorku wyróżnia się tylko **zmiennością**: ruch jest
  o ~40 % większy niż na otwarciu w Tokio czy Londynie. To zgadza się z literaturą, ale zmienność nie mówi, w którą
  stronę pójdzie cena.

**Decyzja:** runda nie startuje, żaden wariant nie został zużyty. Wynik to „nie da się rozstrzygnąć na tych danych”,
a nie „nie działa”. Dla decyzji oznacza to jedno: otwarcia sesji nie są kandydatem na strategię w tym projekcie.

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

## Wynik — rachunek mierzalności (`raw_output.txt`)

Dane: 96 336 świec 30m (2021-01-01 → 2026-06-30), **0 brakujących** w siatce; 1 433 dni robocze na sesję
(F1: 1 368 po 65 dniach rozbiegu). Czas letni/zimowy zadziałał: Londyn 832 × 07:00 + 601 × 08:00 UTC, Nowy Jork
932 × 13:30 + 501 × 14:30 UTC, Tokio 1 433 × 00:00 UTC.

**Ramiona łączne (główne; `p*` = próg opłacalności przy wypłacie ±B, „wymagana” = p* + niepewność przyrządu):**

| ramię | n | B = średni ruch bez znaku | p* taker / limit | ± (95 %) | wymagana taker / limit | prior (literatura) | werdykt |
|---|---|---|---|---|---|---|---|
| F1 dryf 60 min, 3 sesje | 4 104 | 0,52 % | 63,4 % / 58,6 % | 1,53 pp | **65,0 % / 60,2 %** | 53,6 % | NIEMIERZALNA |
| F2 momentum 3,5 h, 3 sesje | 4 299 | 0,89 % | 57,9 % / 55,1 % | 1,49 pp | **59,4 % / 56,5 %** | 53,8 % | NIEMIERZALNA |

Per sesja (opisowo, n 1 368 / 1 433, ± 2,6 pp): wymagana trafność F1 — Tokio 67,3 / 62,0 %, Londyn 70,4 / 64,1 %,
Nowy Jork 62,8 / 59,2 %; F2 — Tokio 60,9 / 57,9 %, Londyn 62,6 / 59,0 %, Nowy Jork 58,8 / 56,6 % (taker / limit).
Konwencja 56 % nie przechodzi w żadnym z 16 wierszy.

**Rozrzut na otwarciach (opis zmienności, nie kierunku):** okno 60 min — odchylenie Tokio 0,73 %, Londyn 0,69 %,
**Nowy Jork 0,99 %**; trzymanie 3,5 h — 1,29 / 1,13 / **1,63 %**. Mediana ruchu bez znaku jest o 35–40 % niższa
od średniej (np. F2 Tokio 0,51 % wobec 0,84 %): grube ogony, czyli kilka dużych ruchów niesie średnią.

**Druga miara (zwrot, przybliżenie gaussowskie):** F2 łącznie z priorem ρ 0,12 daje brutto ~0,131 %/transakcję.
Do t = 1,96 potrzeba 0,181 % (taker) albo 0,131 % (limit), a do mocy 80 % (filtr G1: 1,4 × niepewność) 0,198 / 0,148 %.
Z wejściem limitem najbardziej optymistyczny prior daje więc rzut monetą, czy przyrząd efekt zobaczy, a filtr G1
nie przechodzi. Obie miary różnią się, bo przy grubych ogonach średni ruch bez znaku (0,89 %) jest mniejszy niż
σ·√(2/π) (~1,09 %). Werdykt opiera się na mierze kanonicznej (trafność, zasada 18); druga go nie zmienia.

## Co na plus (+) / Co na minus (−)

(+) Rachunek przed pomiarem: żaden średni zwrot ani trafność reguły nie zostały policzone, historia 2021–2026 nie
dostała kolejnego odczytu (DSR, 96). (+) Czas letni/zimowy ze stref IANA, siatka 30m bez dziur, testy dat przejść.
(+) Prior z literatury, nie z konwencji, a mimo to werdykt odporny: nie przechodzi też konwencja 56 %.
(−) Prior F2 to jedna liczba z próby (R² 1,44 %), niezweryfikowana w tekście i dla innego okna (pierwsza/ostatnia
półgodzina doby UTC); prior F1 to najlepsza z 24 godzin, nie otwarcie. Oba są górnymi granicami, więc błąd działa
na korzyść hipotezy. (−) Bez kalendarza świąt giełdowych (~4 % dni). (−) N_eff = n przyjęte bez pomiaru — górna
granica; realna próba może być tylko mniejsza. (−) Wejście limitem 0,09 % jest optymistyczne: tuż po impulsie
otwarcia wypełnienia są niekorzystnie wybrane (W1, KO1).

## Wniosek

Otwarcia sesji na BTC perp są **niemierzalne** na bazie 2021–2026 w obu formułach i we wszystkich sesjach.
Koszt jednego obrotu (0,14 %) to 16–36 % typowego ruchu w oknie pozycji, więc próg opłacalności leży na 55–68 %
trafności, a przyrząd dokłada ±1,5–2,6 pkt proc. Literatura po publikacji nie daje efektu bliskiego progowi.
Otwarcie w Nowym Jorku wyróżnia się zmiennością (+40 %), nie kierunkiem.

## Rekomendacja

1. Nie uruchamiać reguł na otwarciach sesji; seria OS zamknięta regułą STOP (0/2 zużyte).
2. Jedyne drogi do mierzalności to zmiany z decyzją użytkownika i nową pre-rejestracją. Pierwsza to wiele monet
   naraz, ale korelacja w ciągu dnia jest wysoka, więc zysk mocy jest mały (40). Druga to dużo dłuższa historia,
   której nie ma. Rekomendacja Claude: nie. Prior jest niski, a projekt ma ~40 odczytów na tej historii.
3. Wiedza użyteczna gdzie indziej: zlecenia nóg dziennika warto składać **poza** oknem 13:30–15:30 UTC.
   Większa zmienność na otwarciu w Nowym Jorku to większy poślizg zleceń rynkowych. To uwaga o wykonaniu, nie strategia.
