# CP1P — premia Coinbase na nowych danych lipiec–wrzesień 2026 (odczyt prospektywny, 2026-09-24)

> **STATUS: PRE-REJESTRACJA (przed odczytem).** Rekomendacja 2 z CP1 (wniosek 72): ta sama reguła
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

_(sekcje poniżej po odczycie)_
