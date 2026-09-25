# KR2 — krypto i nogi dziennika a rynki tradycyjne: akcje, złoto, ropa, dolar, stopy USA, VIX (2026-09-25)

> **STATUS: ZAMKNIĘTA (opisowo, 0 wariantów).** BTC chodzi umiarkowanie z akcjami USA (tygodniowo 0,27–0,30,
> 2-tygodniowo 0,43), coraz mocniej w latach 2025–26 (Nasdaq 0,41 → 0,58), przeciwnie do dolara (−0,16) i VIX (−0,22);
> ze złotem, ropą i stopami prawie nic. **Nogi dziennika (trend, X1, premia Coinbase) są praktycznie niezależne od
> rynków tradycyjnych (|ρ| ≤ 0,15; trend lekko przeciw akcjom −0,15).** Korelacja z tego samego tygodnia — nie prognoza.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Sam bitcoin zachowuje się coraz bardziej jak akcje technologiczne: gdy Nasdaq spada, BTC zwykle też (w 2026 już
wyraźnie, korelacja 0,58). Nie chroni więc przed spadkiem giełdy — przeciwnie. Złoto, ropa i stopy procentowe
prawie się z nim nie wiążą. Inaczej nasze strategie z dziennika: one zarabiają i tracą niezależnie od akcji, a trend
nawet lekko „w drugą stronę”. Dla kogoś, kto ma też akcje (np. IKE), to one — a nie samo trzymanie krypto — byłyby
realną dywersyfikacją. To opis, nie sygnał: korelacja z tego samego tygodnia nie mówi, co będzie jutro.

## Metadane

- Branch `kr2-korelacje-tradfi` (z `master` `c2f7c30`). Skrypt `backtest/run_kr2_tradfi.py`, test `tests/test_kr2_tradfi.py`.
  Komenda: `PYTHONUTF8=1 py -m backtest.run_kr2_tradfi` → `raw_output.txt`.
- Dane: FRED (S&P 500, Nasdaq, Nikkei, Brent, indeks dolara DTWEXBGS, rentowność 2/10 lat, bony 3M, **VIX — dociągnięty**
  `fetch_external.fetch_fred("VIXCLS")`), **złoto = PAXG spot Binance 1d od 2020-10** (`data.fetch_ohlcv.get_ohlcv`, FRED
  wycofał notowania LBMA), BTC/ETH perp 1d, nogi dziennika jak KR1 (TS1, X1 7 faz, CP1).
- Zwroty tygodniowe piątek→piątek (krypto 24:00 UTC, USA ~21:00 UTC); stopy i VIX — zmiana poziomu.

## Poprzedzające wyniki

KR1 (95): nogi dziennika między sobą 0,16–0,35; TS1 z rynkiem krypto −0,19 (70); TX1 (84): trend na rynkach FRED.

## Pre-rejestracja (opisowo)

Miary i okno zapisane w skrypcie przed uruchomieniem (korelacja Pearsona tygodniowa, per rok dla BTC, beta BTC do Nasdaq);
bez reguły decyzji — runda nie ocenia żadnej strategii i nie zmienia dziennika.

## Wynik

Pełny stdout: `raw_output.txt`. 268 tygodni (2021-05 → 2026-06); ±0,12 = szerokość 95 % przy korelacji zero.

| | S&P500 | Nasdaq | Nikkei | złoto | ropa | dolar | USA 10 l. | USA 2 l. | bony 3M | VIX |
|---|---|---|---|---|---|---|---|---|---|---|
| **BTC** | **+0,27** | **+0,30** | +0,09 | +0,09 | −0,01 | **−0,16** | −0,01 | −0,04 | −0,21 | **−0,22** |
| ETH | +0,34 | +0,36 | +0,19 | +0,02 | −0,02 | −0,18 | −0,06 | −0,06 | −0,13 | −0,28 |
| noga TS1 (trend) | **−0,15** | −0,15 | −0,04 | −0,08 | −0,09 | +0,05 | 0,00 | +0,08 | +0,07 | +0,06 |
| noga X1 | −0,03 | −0,02 | −0,03 | +0,02 | −0,14 | −0,04 | +0,03 | +0,03 | 0,00 | +0,06 |
| noga CP1 | −0,08 | −0,04 | −0,09 | +0,05 | −0,08 | −0,02 | +0,04 | −0,05 | −0,09 | +0,05 |

**BTC per rok (Nasdaq / dolar / VIX):** 2021 +0,04 / −0,04 / −0,03 · 2022 +0,43 / −0,30 / −0,43 · 2023 +0,26 / −0,07 / −0,17 ·
2024 +0,08 / −0,06 / −0,21 · 2025 +0,41 / −0,33 / −0,27 · 2026 (26 tyg.) +0,58 / −0,24 / −0,37. Beta BTC do Nasdaq 0,78.

## Co na plus (+) / Co na minus (−)

**(+)** Druga droga (BTC–Nasdaq): Spearman 0,33, zwroty 2-tygodniowe 0,43 / 0,46 — obraz zgodny, na dłuższym oknie wyraźniejszy
(asynchronia zamknięć i opóźnienia zaniżają tygodniową liczbę). Złoto z PAXG zamiast brakującego FRED.
**(−)** Korelacje zmienne w czasie (2021 ≈ 0, 2026 ≈ 0,6) — średnia z całego okresu ukrywa trend; lata po ~52 tygodnie → ±0,27.
Nogi dziennika liczone na historii (backtest), nie na żywo. PAXG ≠ złoto giełdowe (drobne premie tokena). **Kogo nie ma:**
obligacje jako zwrot (mamy tylko rentowności), surowce rolne, rynki wschodzące; tygodnie ze świętami USA (poziom z ostatniego dnia).

## Przegląd (16c)

`engineering:code-review` (samodzielnie): tygodnie W-FRI z ostatniego poziomu, stopy/VIX jako różnica (test), nogi z KR1 bez zmian;
**Approve** — skrypt opisowy na istniejących loaderach, bez logiki handlowej.

## Wniosek

**Prostym językiem:** BTC nie jest „bezpieczną przystanią” — w złych tygodniach na giełdzie zwykle też traci, coraz wyraźniej.
Strategie z dziennika są natomiast niezależne od akcji — to one niosą wartość dywersyfikacji.

## Rekomendacja

1. Dziennik bez zmian. 2. Przy decyzji o realnym kapitale (szczebel 4) traktować sam BTC jako część ryzyka akcyjnego portfela
użytkownika; nogi dziennika — jako osobne ryzyko. 3. Wyprzedzanie (czy Nasdaq/VIX dziś mówi coś o krypto jutro) — nowa hipoteza,
nie badana tutaj (licznik prób, AU4).

## Użyte skille

Rejestr `runs/skille/kr2-korelacje-tradfi.jsonl`: `clas5-runda`, `clas5-quant` (asynchronia zamknięć → tygodnie; korelacja ≠ prognoza),
`engineering:code-review` (Approve). Pominięte: `data:explore-data` (dwie nowe serie — PAXG bez dziur 2 099 dni, VIX 41 braków = święta,
sprawdzone przy pobraniu), `data:validate-data`/`statistical-analysis` (druga droga i ±0,12 w README; runda opisowa).
