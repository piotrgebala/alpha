# TX1 — trend tygodniowy (reguła TS1) na 19 rynkach spoza krypto (2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed wynikiem).** Rachunek mocy w `moc.txt` (tylko rozrzut H0).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Według nowego kryterium (ADR-09) trend musi mieć oparcie **poza naszymi danymi krypto**. Sprawdzamy
więc naszą regułę trendu, bez żadnej zmiany, na walutach, ropie, indeksach giełdowych i obligacjach
od 1990 roku. Jeśli trend to prawdziwe zjawisko rynkowe, a nie przypadek na 5 latach krypto,
powinien być widoczny także tam.

## ID testu

TX1 — szczebel 1(b) drabiny dowodów (ADR-09, `docs/rag/09_drabina_dowodow.md`).

## Metadane

- Branch `tx1-trend-inne-rynki`. Dane: FRED (bez klucza) → `data/raw/tradfi/` (`py -m data.tradfi_panel`);
  panel `data/tradfi_panel.py` + testy `tests/test_tradfi_panel.py`. Skrypt `backtest/run_trend_tradfi_tx1.py`.
- **Wyjątek od zasady 20** (dane od 2021) — zatwierdzony wyborem użytkownika 2026-09-24 (droga C:
  „trend na surowcach, walutach, indeksach, dziesiątki lat”); zasada 20 dotyczy świec krypto.

## Poprzedzające wyniki

- TS1/TR1 po RU1/RU2 (wnioski 70, 74, 82, 83): trend na krypto +11–13 %/rok, nieistotny, dodatni w każdym
  roku; ADR-09 szczebel 2 spełniony (post hoc).
- Literatura: Moskowitz–Ooi–Pedersen (2012), 58 kontraktów 1985–2009, Sharpe ~1; Hurst–Ooi–Pedersen
  (2017), 100 lat. Po publikacji słabiej (Sharpe ~0,3–0,5, „susza trendu” 2012–2019).

## Pre-rejestracja (przed wynikiem)

- **Hipoteza:** reguła TS1 daje dodatni zwrot na rynkach spoza krypto.
- **JEDNA zmienna:** rynki (krypto → 19 rynków FRED). Reguła co do bajtu: znak zwrotu 28 dni,
  σ̂ EWMA (com 60) · √365, w = s·min(3; 0,40/σ̂)/N, formowanie co 7 dni, 7 faz.
- **Dane (ustalone przed wynikiem):** 13 walut względem USD (odwrócone do „USD za jednostkę”), ropa
  Brent, Nasdaq Composite, Nikkei 225, obligacje USA 2/10/30 lat (zwrot z rentowności: −D·Δy + y/365,
  D = 1,9 / 8,5 / 18). **Wykluczone przed wynikiem:** WTI (cena ujemna 2020-04-20), gaz Henry Hub
  (dzienny spot fizyczny, skoki do +319 %/dzień, 90 dni > 20 %). Dni kalendarzowe z przeniesieniem
  ceny (zwrot 0 w dni wolne) — silnik bez zmian parametrów.
- **Koszt:** 0,02 % × obrót; bez carry walut, rolowania ropy i dywidend — dowód mechanizmu, nie wynik do handlu.
- **Kryterium główne (1990-01 → 2026-08):** POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0
  (100 portfeli ze znakami przesuniętymi w czasie); NEGATYWNY, gdy górny kraniec CI 95 % < 0.
- **Mapowanie na ADR-09 szczebel 1(b):** SPEŁNIONY, gdy kryterium główne POZYTYWNE i średnia po 2013
  > 0; OBALONY, gdy kryterium główne NEGATYWNE albo górny kraniec CI po 2013 < 0; inaczej
  NIEROZSTRZYGNIĘTY.
- **Mierzalność (`moc.txt`):** całość: zmienność H0 9,4 %/rok, half-width **±3,1 %/rok = 0,33 SR**,
  q97,5 +2,9 %; założony efekt (koszyk 19 rynków, głównie waluty) SR 0,5–0,8 → **MIERZALNA**.
  Po 2013: half-width ±5,1 %/rok = 0,53 SR wobec efektu SR 0,3–0,5 → **tylko opisowo**.
- **Opisowo:** dekady, lata dodatnie, 7 faz, klasy aktywów osobno, nominał i obrót.
- **Licznik:** nowa seria TX (1/1, STOP); w projekcie ~34. odczyt.

_(sekcje poniżej po przebiegu)_
