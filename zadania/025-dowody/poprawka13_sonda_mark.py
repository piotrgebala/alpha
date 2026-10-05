"""
Zadanie 025 / Poprawka 13 — sonda do reguły R2 (cena rozliczenia monety wstrzymanej lub wycofanej).

Pytania: czy publiczne API Binance USDT-M (bez klucza) zwraca dla kontraktu wycofanego albo zamrożonego
(i) OFICJALNĄ cenę rozliczenia (`/futures/data/delivery-price`), (ii) dzienne świece ceny MARK
(`/fapi/v1/markPriceKlines`), oraz jaki status i typ kontraktu ma taki symbol w `exchangeInfo`.
Przypadki z `czestosc.txt` (zdarzenia w koszyku top-20) + BTCUSDT jako kontrola.

Tylko odczyt, jeden host: fapi.binance.com (ccxt `binanceusdm`, ten sam obiekt co `data/fetch_live.run`).
Wyników dziennika nie czyta.

    PYTHONUTF8=1 /home/dantey1/alpha/.venv/bin/python zadania/025-dowody/poprawka13_sonda_mark.py \
        > zadania/025-dowody/poprawka13_sonda_mark.txt
"""

from __future__ import annotations

import time
from collections import Counter

import ccxt
import pandas as pd

# (symbol, początek okna, koniec okna, opis z czestosc.txt)
CASES = [
    (
        "ALPACAUSDT",
        "2025-04-27",
        "2025-05-05",
        "zamrożenie od 2025-05-01 (ostatnia normalna 04-30)",
    ),
    ("FTTUSDT", "2022-11-12", "2022-11-19", "zamrożenie od 2022-11-15 (ostatnia normalna 11-14)"),
    ("BNXUSDT", "2025-03-15", "2025-03-21", "zamrożenie od 2025-03-18 (ostatnia normalna 03-17)"),
    ("TONUSDT", "2026-06-21", "2026-06-28", "zamrożenie od 2026-06-24 (ostatnia normalna 06-23)"),
    ("EOSUSDT", "2025-05-18", "2025-05-23", "koniec świec 2025-05-21"),
    ("LUNAUSDT", "2022-05-10", "2022-05-15", "koniec świec 2022-05-13"),
    ("BTCUSDT", "2025-04-27", "2025-04-30", "kontrola: kontrakt notowany"),
]
PACING_S = 0.7  # jak data.fetch_universe.REQUEST_PACING_S
DAY = pd.Timedelta(days=1)


def ms(day: str) -> int:
    return int(pd.Timestamp(day, tz="UTC").value // 1_000_000)


def call(fn, params: dict):
    """Wywołanie API → (wynik, None) albo (None, „Typ: komunikat”)."""
    time.sleep(PACING_S)
    try:
        return fn(params), None
    except Exception as exc:  # noqa: BLE001 — sonda raportuje każdy błąd
        return None, f"{type(exc).__name__}: {str(exc)[:200]}"


def show_klines(name: str, rows, err) -> None:
    if err is not None:
        print(f"    {name}: BŁĄD {err}")
        return
    print(f"    {name}: {len(rows)} świec")
    for r in rows:
        day = pd.Timestamp(int(r[0]), unit="ms", tz="UTC").date()
        vol = f" obrót {float(r[7]):.0f}" if len(r) > 7 and name.startswith("klines") else ""
        print(f"      {day}: O {r[1]} H {r[2]} L {r[3]} C {r[4]}{vol}")


def main() -> None:
    ex = ccxt.binanceusdm({"enableRateLimit": False})
    print(f"ccxt {ccxt.__version__}; host {ex.urls['api']['fapiPublic']}")
    print(f"czas sondy (UTC): {pd.Timestamp.now(tz='UTC').isoformat(timespec='seconds')}")
    info, err = call(lambda p: ex.fapiPublicGetExchangeInfo(), {})
    if err is not None:
        print(f"exchangeInfo: BŁĄD {err}")
        info = {"symbols": []}
    syms = {s.get("symbol"): s for s in info.get("symbols", [])}
    usdt = [s for s in info.get("symbols", []) if s.get("quoteAsset") == "USDT"]
    print("=" * 100)
    print("1. exchangeInfo — symbole z kwotowaniem USDT: liczba wg (contractType, status)")
    for (ct, stt), n in sorted(
        Counter((s.get("contractType"), s.get("status")) for s in usdt).items()
    ):
        print(f"   contractType={ct!r:<22} status={stt!r:<12} {n}")
    print("=" * 100)
    for sym, a, b, what in CASES:
        print(f"2. {sym} — {what}; okno {a} … {b}")
        s = syms.get(sym)
        if s is None:
            print("    exchangeInfo: BRAK symbolu")
        else:
            keys = ("status", "contractType", "deliveryDate", "onboardDate", "pair")
            desc = ", ".join(f"{k}={s.get(k)!r}" for k in keys)
            dd = s.get("deliveryDate")
            if dd:
                desc += f" (deliveryDate = {pd.Timestamp(int(dd), unit='ms', tz='UTC')})"
            print(f"    exchangeInfo: {desc}")
        params = {
            "symbol": sym,
            "interval": "1d",
            "startTime": ms(a),
            "endTime": ms(b) + 86_400_000 - 1,
        }
        rows, err = call(ex.fapiPublicGetMarkPriceKlines, params)
        show_klines("markPriceKlines 1d (cena mark)", rows, err)
        rows, err = call(ex.fapiPublicGetKlines, params)
        show_klines("klines 1d (cena ostatnia)", rows, err)
        now = pd.Timestamp.now(tz="UTC").normalize()
        recent = {
            "symbol": sym,
            "interval": "1d",
            "startTime": int((now - 5 * DAY).value // 1_000_000),
            "endTime": int(now.value // 1_000_000) - 1,
        }
        rows, err = call(ex.fapiPublicGetMarkPriceKlines, recent)
        show_klines("markPriceKlines 1d — ostatnie 5 dni", rows, err)
        res, err = call(ex.fapiDataGetDeliveryPrice, {"pair": s.get("pair", sym) if s else sym})
        if err is not None:
            print(f"    delivery-price (oficjalna cena rozliczenia): BŁĄD {err}")
        else:
            print(
                f"    delivery-price (oficjalna cena rozliczenia): {len(res)} rekordów; pierwsze 3: {res[:3]}"
            )
        print("-" * 100)


if __name__ == "__main__":
    main()
