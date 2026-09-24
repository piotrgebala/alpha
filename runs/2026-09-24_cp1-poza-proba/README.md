# CP1P — premia Coinbase na nowych danych lipiec–wrzesień 2026 (odczyt prospektywny, 2026-09-24)

> **STATUS: ZAMKNIĘTY ODCZYT — brak obalenia, brak potwierdzenia:** 78 dni (07-08 → 09-23),
> **+0,13 %** netto (+5,4 %/rok) przy BTC +33 %; fazy od −30 % do +30 %.
> Poprzednio: **PRE-REJESTRACJA (przed odczytem).** Rekomendacja 2 z CP1 (wniosek 72): ta sama reguła
> na danych nieoglądanych. **0 wariantów** (seria CP bez zmian; reguła zamrożona co do bajtu:
> `run_coinbase_cp1.py` z commitu `3871a83`). Odczyt opisowy — pierwszy wpis dziennika CP.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

CP1 zarobiło na historii +32 % rocznie, ale przy wielu testach to mogło być szczęście. Ten odczyt
sprawdza tę samą regułę na ok. 80 dniach od lipca 2026, których nie oglądaliśmy. Tyle dni nie
potwierdzi niczego; może tylko obalić regułę, gdyby wynik był bardzo zły.

## Metadane

- Branch: `cp1-poza-proba`. Skrypt: `backtest/run_coinbase_cp1_oos.py` (na `runs/ZAMROZONE.txt`);
  komenda `PYTHONUTF8=1 py -m backtest.run_coinbase_cp1_oos` → `raw_output.txt`.
- Dane: Coinbase do 2026-09-23 (cache P3); spot Binance 8h 2026-03-01 → 09-23 (pobrane
  2026-09-24, `get_ohlcv_cached`, rozbieg 90 dni normy premii); perpetual BTCUSDT 1d i funding
  z `data/raw/universe_2026q3`.

## Pre-rejestracja

- **Reguła:** jak CP1, bez zmian; okres 2026-07-01 → 2026-09-23, 7 faz (pierwszy dzień ze
  wszystkimi fazami ok. 07-08).
- **Próg obalenia (z góry):** jeśli CP1 jest prawdziwe (+32 %/rok, zmienność 34,8 %/rok), średnia
  roczna z n dni spada poniżej 32 − 1,96·34,8/√(n/365) %/rok (≈ −110 %/rok przy ~78 dniach)
  w < 2,5 % przypadków → taki wynik OBALA CP1. Inny wynik = „brak obalenia”, nie potwierdzenie.
- **Mierzalność jako test: NIEMIERZALNA** (±~150 %/rok) — zapisane wprost; to wpis dziennika.

---

## Wynik

`raw_output.txt`: 78 dni ze wszystkimi fazami; zwrot netto skumulowany **+0,13 %** (brutto +2,25 %,
funding −0,47 %, koszt 0,64 %) = +5,4 %/rok; zmienność 31,2 %/rok. Sygnał long w 64 % dni,
6 zmian znaku. BTC w tym czasie +33,2 % (perp) — niezależnie z Coinbase +32,5 % ✓
(`walidacja.txt`). 7 faz: +25,9 / +29,8 / +23,7 / −29,0 / −30,4 / −26,6 / +25,4 %. Próg obalenia
−116 %/rok → **brak obalenia**.

## Co na plus (+) / Co na minus (−)

**(+)** Reguła nie została obalona na danych nieoglądanych; odczyt pre-rejestrowany, kontrola
krzyżowa ruchu BTC z drugiego źródła zgodna.
**(−)** Strategia prawie nic nie zarobiła w okresie, w którym BTC urósł o 33 % — sygnał przez
jedną trzecią dni był short. Rozrzut faz ±30 % pokazuje, jak duży jest szum zakładu na jednym
instrumencie w 11 tygodniach: wynik zależy od dnia tygodnia formowania. 78 dni nie rozstrzyga.

## Walidacja, statystyka, przegląd (zasady 16a–c)

`data:validate-data`: **READY** (kontrola krzyżowa BTC z Coinbase; odczyt opisowy, bez werdyktu).
Statystyka: rozdzielczość ~±150 %/rok zapisana z góry; brak interpretacji punktowej. Przegląd
kodu: skrypt importuje zamrożone funkcje CP1 bez zmian, łączy stary i nowy cache spot bez
duplikatów znaczników — **Approve**.

## Wniosek

**Prostym językiem:** na nowych danych z lata 2026 premia Coinbase zarobiła ~0 %, choć BTC urósł
o jedną trzecią. To nie obala reguły (za krótko), ale też nie daje jej żadnego wsparcia. CP1
pozostaje kandydatem do dłuższego testu na żywo, a nie strategią do grania.

## Rekomendacja

Kolejny odczyt tej samej reguły co kwartał (dociągnąć Coinbase, spot i perp); żadnych zmian
reguły. Użyte skille (rejestr `runs/skille/cp1-poza-proba.jsonl`): `clas5-runda`,
`data:validate-data`; pominięte `clas5-quant` (reguła bez zmian, pułapki opisane w CP1).
