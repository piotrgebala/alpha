# AU1 — audyt: czy nasze testy mogły ukryć prawdziwą przewagę (2026-09-24)

> **STATUS: ZAMKNIĘTA — odpowiedź: CZĘŚCIOWO.** Brak błędu w obliczeniach, który po cichu zjadałby
> zysk (silnik zgodny z niezależną wersją co do 1e-17, oddaje wbudowany zysk +10,4 → +10,1 %/rok).
> Trzy ślepe miejsca: (1) model uczony na 60 dniach przenosi tylko ~15–17 % przewagi słabej 5. cechy,
> więc cechy spoza wykresu (F1, O1, L1, V1, G1) NIE zostały naprawdę zmierzone; (2) data startu TR1/X2
> została po obciętych danych — TR1 od 2021-02: +15,5 %/rok, t 1,99 (formalnie ponad 1,96, poniżej progu
> rodzinnego ~2,9; wynik znany z audytu, nie jest potwierdzeniem); (3) „nierozstrzygnięty” w strategiach
> tygodniowych = za mało lat (moc ~25 % dla +10 %/rok). Kilka opisów w INDEX było mocniejszych niż dowody
> — poprawione we wniosku 87. 0 wariantów.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Użytkownik: „nie chce mi się wierzyć, że nic nie znaleźliśmy”. Pięciu niezależnych agentów sprawdziło
koszty, kryteria statystyczne, dane, silnik liczenia zysków i przyrząd Fazy 0, a każde znalezisko
sprawdził osobny „adwokat diabła”. Wynik: obliczenia są poprawne, ale w trzech miejscach test był
ślepy albo za słaby, a kilka naszych zdań było zbyt kategorycznych. Nie ma za to śladu dużej, ukrytej
przewagi — tam, gdzie test był ślepy, prawdziwe sygnały są ok. trzy razy słabsze od tego, czego nie
potrafił zobaczyć.

## ID testu

AU1 — audyt metodologii (przegląd, bez nowego pomiaru przewagi); 0 wariantów.

## Metadane

- Przepływ wieloagentowy (18 agentów: 5 audytorów po jednej soczewce, 12 weryfikatorów, synteza),
  tylko do odczytu repo; skrypty i przeliczenia w scratchpadzie sesji (`scratchpad/audyt`).
- Pełny zapis: `raw_output.txt` (synteza, 5 raportów, 12 werdyktów weryfikacji — wszystkie CZĘŚCIOWO).

## Poprzedzające wyniki

Wnioski 39, 41, 50, 67, 70, 81–86; RU1/RU2 (korekta uniwersum); NC1 (kontrola negatywna).

## Pre-rejestracja

Zakres zapisany w poleceniu przepływu przed startem: pięć soczewek (koszty i wykonanie, kryteria
i statystyka, dobór próby i dane, silnik zwrotów z kontrolą pozytywną, przyrząd Fazy 0); kierunek każdego
znaleziska („ukrywa”/„zawyża”/„neutralne”) i dowód liczbą lub miejscem w kodzie; każde istotne
znalezisko weryfikowane przeciwniczo; zakaz zmian w repo.

## Wynik

| # | problem | kierunek | wpływ |
|---|---|---|---|
| P1 | model 60 dni + 4 cechy gubi ~83–85 % przewagi słabej 5. cechy (wyrocznia +0,20 %/transakcję jako reguła → w modelu 51,05 %, NEGATYWNY w 2/3 losowań; okno 365 dni już ją widzi) | ukrywa | F1, O1, L1, V1, G1, M1, A1b, A2.5 — cechy NIEZMIERZONE, nie „dowód braku”; realne efekty tych cech ~0 do +0,03 %/tr. po kosztach |
| P2 | start TR1/X2 = 2021-05 z obciętego katalogu | ukrywa (TR1) | TR1 od 2021-02: +15,5 %/rok [+0,2; +30,8], t 1,99; X2: dodane miesiące −4,0 pkt, średnia 7 dni +21,9 %, t 1,59 — bez zmian |
| P3 | 5,4 roku za mało dla strategii tygodniowych | czułość | moc przy +10 %/rok: 25 % (z 1,96), 5 % (z 2,9); przy +20 %: 73 % / 37 % |
| P4 | N_eff przycinany tylko w dół | ukrywa (mało) | t niższe o 4–5 %; Newey-West (auto) nie zmienia żadnego werdyktu; brak `max(1, …)` w `carry_hedged.py:130` — **naprawione** + test |
| P5 | opisy mocniejsze niż dowody | — | Y2 niezmierzony; TL1 na obciętych danych; wnioski 41, 67, 70, 84; M1 „1,9×” → ~1,3–1,4×; CP1P = brak informacji |
| P6 | co ZAWYŻA kandydatów | zawyża | X1: bez dnia MYX t 1,83, bez 5 najlepszych dni 1,30; funding to +49 pkt z +226 (w 2026 cały wynik X1/X2); TX1 z kosztem finansowania obligacji +4,3–4,5 %/rok, t 2,34–2,40; TS1+X1+CP1 razem t 2,44 — przy wyborze 3 z ~30 prób szansa przypadku 36–78 % |

**Sprawdzone i w porządku:** silnik (niezależna implementacja 1e-17, kontrola pozytywna), brak zaglądania
w przyszłość (opóźnienie 1–2 dni obniża TS1 łagodnie: 11,1 → 10,3 → 9,3 %), koszty realistyczne (modele
na świecach nie zarabiają nawet przed kosztami: najlepszy +0,041 %/tr., t 1,15), dane czyste (0 braków
fundingu w 1 300 miejscach top-20), portfele kontrolne poprawne, CP1 odporny na metodę (t 2,07–2,18).

## Co na plus (+) / Co na minus (−)

**(+)** Twarde „nie działa” dla kierunku BTC z wykresu (1h–3 dni), AT i zarządzania pozycją jest uczciwe —
test był mocny. Obliczenia są poprawne. Znaleziono i naprawiono realny drobny błąd w kodzie.
**(−)** Część zamknięć (cechy spoza wykresu) była zbyt pochopna — przyrząd był za gruby. TR1 formalnie
przechodzi 1,96 po poprawce daty, ale to wynik oglądany po fakcie i blisko progu.

## Walidacja (16a)

`data:validate-data` nie wczytany w tej rundzie: weryfikację zapewnił przepływ (12 niezależnych
weryfikatorów przeciwniczych, wszystkie werdykty CZĘŚCIOWO — potwierdzone fakty, osłabione tezy).
Claude sprawdził osobno: brak `max(1, …)` w `carry_hedged.py:130` (odtworzony testem), plik roboczy
audytu `x1_fee0.parquet` pozostawiony w repo przez agenta — usunięty. Werdykt: **Caveats** (przeliczenia
agentów niepowtórzone w całości).

## Wniosek

**Prostym językiem:** nasze liczenie jest poprawne, a „nic nie działa” jest prawdą tam, gdzie test był
mocny: przewidywanie kierunku BTC z samego wykresu nie działa. Ale dwa pytania zamknęliśmy za szybko.
Po pierwsze, dane spoza wykresu (funding, pozycjonowanie, sentyment) sprawdzaliśmy przyrządem, który słabego
sygnału po prostu nie widzi — więc nie wiemy, czy coś tam jest (uczciwe oczekiwanie: bardzo mało). Po drugie,
„nierozstrzygnięty” przy trendzie i momentum znaczy „za mało lat, żeby zmierzyć”, a nie „nic nie ma”.

## Rekomendacja

1. Opisy poprawione we wniosku 87 i w „Stanie wiedzy” (ta runda).
2. Do decyzji użytkownika: (a) zmierzyć cechy spoza wykresu jako proste reguły albo model z oknem 365 dni
   (nowa seria, rachunek mocy z kalibracją „ile przewagi przenosi model”); (b) runda korekty RU3 — start
   TR1/X2 od 2021-02 (X2 jako średnia 7 dni tygodnia); (c) X1 jako osobna reguła w dzienniku na żywo.
3. W nowych rundach: Newey-West z automatycznym oknem zapisany z góry; przedział trafności z uwzględnieniem
   nakładających się transakcji.

## Użyte skille

Rejestr `runs/skille/au1-audyt-metodologii.jsonl`. W tej rundzie Claude nie wczytywał skilli zasady 19 —
pracę wykonali agenci przepływu (bez narzędzia Skill, zgodnie z poleceniem). Pominięte z powodem:
`data:validate-data`, `data:statistical-analysis` (weryfikacja przeciwnicza w przepływie),
`engineering:code-review` (zmiana kodu: jedna linia + test, przegląd w sesji).
