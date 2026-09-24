# RU2 — korekta danych: pozostałe rundy na pełnym uniwersum (2026-09-24)

> **STATUS: ZAMKNIĘTA — wszystkie 5 wyników ODPORNE na błąd danych, żaden werdykt się nie zmienia.**
> TR1 +13,0 %/rok (było +14,1), X2 +23,1 % (było +15,9), koszt likwidacji 3× −2,4 %/rok (było −3,6),
> TF1 −1,3 pkt (było −1,4), R1 −10,6 %/rok (było −3,6). Pre-rejestracja `1d00e7a`. Walidacja: **READY
> (Caveats)**; przegląd: **Approve**. 0 wariantów.
> Poprzednio: **PRE-REJESTRACJA (przed przeliczeniem).**

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

## Wynik

Pliki: `raw_output_tr1.txt`, `raw_output_x2.txt`, `raw_output_lq1.txt`, `raw_output_tf1.txt`, `raw_output_r1.txt`.

| runda | obcięte uniwersum | pełne uniwersum | odczyt kryterium | odporność |
|---|---|---|---|---|
| TR1 trend, monety 21–50 | +14,1 %/rok, t 1,62 | **+13,0 %/rok [−2,6; +28,7], t 1,63**; ponad 99 % H0; 6/6 lat i 7/7 faz dodatnich | NIEROZSTRZYGNIĘTY | odporny (92 %) |
| X2 momentum top-50 | +15,9 %/rok, t 1,10 | **+23,1 %/rok [−5,2; +51,5], t 1,60**; IC +0,001 | NIEROZSTRZYGNIĘTY | odporny (145 %) |
| LQ1 koszt likwidacji 3× | −3,6 %/rok [−5,8; −1,4] | **−2,4 %/rok [−4,8; 0,0]**, t −1,96; trend z likwidacją 3× +8,7 %/rok; 5,6 % pozycji-tygodni likwidowanych | NIEROZSTRZYGNIĘTY (TS1-liq) | odporny (67 %) |
| TF1 filtr tłoku (różnica) | −1,41 %/rok | **−1,30 %/rok [−6,31; +3,71]** | NIEROZSTRZYGNIĘTY | odporny |
| R1 premia rebalansowa | −3,55 %/rok [−9,5; +2,4] | **−10,6 %/rok [−24,5; +3,3]**; 34/65 miesięcy dodatnich | NIEROZSTRZYGNIĘTY | odporny (silniej ujemny) |

X2 per rok (Σ netto): 2021 +42,7 · 2022 −10,3 · 2023 +28,0 · 2024 +5,3 · 2025 +27,0 · 2026 (pół) +26,7 % —
w 2026 prawie cały wynik to funding (+27,8 pkt), który otrzymują shorty na przegrzanych monetach.
TR1 per rok: +15,7 · +14,3 · +13,1 · +9,4 · +13,2 · +1,3 %.

## Co na plus (+) / Co na minus (−)

**(+)** Żaden wniosek projektu nie opierał się wyłącznie na dziurze w danych: znaki bez zmian, wielkości
w granicach ±50 %. Trend na monetach 21–50 wygląda niemal identycznie jak na top-20 (dodatni w każdym roku).
**(−)** Nadal nic istotnego; X2 wzrósł głównie dzięki fundingowi w 2026 (mała, ostatnia część próby).
TL1 nieprzeliczony (brak danych OI dla nowych członków). Koszt likwidacji 3× (−2,4 %/rok) wciąż wyraźny.

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY (Caveats)**: sumy roczne zgodne z wynikiem rocznym (TR1 67,0 pkt / 5,15
roku = +13,0 %; X2 119,5 pkt / 5,17 roku = +23,1 %); funding dla członków top-50 kompletny (512 plików);
czerwona flaga R1 — maks. dzienna premia 22 % (dzień krachu pojedynczej monety w koszyku rebalansowanym
codziennie) — nie zmienia średniej (wbudowany test skryptu R1: średnia |premii| w normie). Caveat: TL1.
`data:statistical-analysis`: przedziały 95 % podane; żaden wynik nie przekracza progu; ~33 odczyty
na tej historii. `engineering:code-review` — **Approve**: podmiana w czasie wykonania, pliki rund nietknięte.

## Wniosek

**Prostym językiem:** po naprawie danych pozostałe rundy mówią to samo, co wcześniej. Trend na mniejszych
monetach (miejsca 21–50) daje ok. +13 % rocznie i był dodatni w każdym roku — ale to wciąż za mało, by
odróżnić go od szczęścia. Dźwignia 3× nadal kosztuje trend ok. 2–4 % rocznie w likwidacjach (dlatego
w dzienniku trend gra z 2×). Filtry tłoku i premia rebalansowa dalej nie działają.

## Rekomendacja

1. Wnioski 57, 64, 68, 70, 73, 74, 76 obowiązują z liczbami z RU1/RU2 (odnośnik w INDEX).
2. TL1 — przeliczyć tylko, jeśli wrócimy do pozycjonowania (wymaga pobrania OI nowych członków).
3. Stary cache `data/raw/universe` — tylko do odtwarzania zamrożonych rund.

## Użyte skille

Rejestr `runs/skille/ru2-korekta-pozostalych.jsonl`: `clas5-runda` (pre-rejestracja, zakres), `clas5-quant`
(odczyt odporności), `data:validate-data` (sumy roczne, kogo nie ma), `data:statistical-analysis`
(przedziały, licznik), `engineering:code-review` (Approve). Pominięte: `dataviz` (tabela), `data:explore-data`
(profil uniwersum zrobiony w RU1).
