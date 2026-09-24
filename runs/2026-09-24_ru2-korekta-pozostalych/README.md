# RU2 — korekta danych: pozostałe rundy na pełnym uniwersum (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed przeliczeniem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

RU1 pokazała, że koszyk „największych monet” liczyliśmy z niepełnego rynku (287 z 685 kontraktów)
i przeliczyła trzy najważniejsze wyniki. Tu przeliczamy pięć kolejnych rund, które stały na tych
samych danych — tymi samymi, zamrożonymi regułami — żeby żaden wniosek w projekcie nie opierał się
na dziurze w danych.

## ID testu

RU2 — korekta danych (nie nowa hipoteza), ciąg dalszy RU1.

## Metadane

- Branch `ru2-korekta-pozostalych`. Dane: `data/raw/universe_full` (RU1) + funding dociągnięty dla
  członków top-50 2021–2026 (`data/complete_universe.py … 50`: 378 monet, 103 brakujące dociągnięte),
  OHLC `data/raw/universe_ohlc_full/` (top-20).
- Skrypt `backtest/run_universe_fix_ru2.py` (tryby `tr1`, `x2`, `lq1`, `tf1`, `r1`) — podmienia
  katalog danych w module rundy w czasie wykonania; reguły, H0 i kryteria z zamrożonych plików.

## Poprzedzające wyniki (obcięte uniwersum)

| runda | wynik pierwotny | wniosek |
|---|---|---|
| TR1 trend, monety 21–50 | +14,1 %/rok [−3,0; +31,2], t_neff 1,62, NIEROZSTRZYGNIĘTY | 74 |
| X2 momentum top-50 | +15,9 %/rok [−12,3; +44,2], t 1,10, NIEROZSTRZYGNIĘTY | 68 |
| LQ1 trend z likwidacją 3× | +11,3 %/rok, koszt likwidacji −3,6 %/rok [−5,8; −1,4] | 76 |
| TF1 trend z filtrem tłoku | różnica −1,41 %/rok [−6,58; +3,77], NIEROZSTRZYGNIĘTY | 73 |
| R1 premia rebalansowa | −3,55 %/rok [−9,50; +2,40], NIEROZSTRZYGNIĘTY | 57 |

## Pre-rejestracja (przed przeliczeniem)

- **JEDNA zmienna:** zawartość uniwersum. Wszystko inne co do bajtu jak w rundach pierwotnych.
- **Kryteria:** te same co w rundach pierwotnych (drukowane przez ich kod).
- **Odczyt odporności (jak RU1):** „odporny”, gdy ten sam znak i ≥ ½ pierwotnej wielkości efektu;
  „zależał od błędu” — w przeciwnym razie. Dla LQ1 efektem jest koszt likwidacji (−3,6 %/rok), dla
  TF1 różnica względem TS1.
- **Czego runda nie może:** potwierdzić przewagi (ta sama historia); zmiana werdyktu na POZYTYWNY
  nie będzie cytowana jako potwierdzenie.
- **Poza zakresem:** TL1 (dane OI tylko dla starych członków — wymaga osobnego pobrania), NL1 i P2
  (nie korzystały z obciętego koszyka: NL1 — własne zdarzenia listingów, P2 — jawna lista symboli).
- **Liczniki:** 0 wariantów.

_(sekcje poniżej po przebiegu)_
