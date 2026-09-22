"""
SONDA: ile historii Binance faktycznie oddaje dla danych pozycjonowania?

Pytanie decyzyjne: zasada 18 wymaga ~4 500 transakcji, czyli na 4h/V=3 okolo 6,8 roku
danych. Jesli endpointy pozycjonowania oddaja tylko 30 dni, cala klasa zrodel
(open interest, long/short ratio) odpada MECHANICZNIE, niezaleznie od jakosci mechanizmu.

Sprawdzamy DWIE rzeczy per endpoint:
  1. jak daleko wstecz siega odpowiedz BEZ parametru startTime (ile punktow max),
  2. co zwraca przy jawnym startTime sprzed lat.

Zero zapisu do repo, zero zmian w kodzie. Tylko odczyt.
"""
from datetime import datetime, timezone

import requests

BASE = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"
PERIOD = "4h"

ENDPOINTY = {
    "openInterestHist": "/futures/data/openInterestHist",
    "topLongShortAccountRatio": "/futures/data/topLongShortAccountRatio",
    "topLongShortPositionRatio": "/futures/data/topLongShortPositionRatio",
    "globalLongShortAccountRatio": "/futures/data/globalLongShortAccountRatio",
    "takerlongshortRatio": "/futures/data/takerlongshortRatio",
}

# Dla porownania: to samo pytanie dla danych, ktore JUZ mamy.
POROWNANIE = {
    "klines (OHLCV)": "/fapi/v1/klines",
    "fundingRate": "/fapi/v1/fundingRate",
}


def _ts(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def _pierwszy_ostatni(dane):
    def czas(rekord):
        for klucz in ("timestamp", "openTime", "fundingTime"):
            if isinstance(rekord, dict) and klucz in rekord:
                return int(rekord[klucz])
        if isinstance(rekord, list):
            return int(rekord[0])
        return None
    return czas(dane[0]), czas(dane[-1])


def sprawdz(nazwa, sciezka, dodatkowe=None):
    params = {"symbol": SYMBOL, "limit": 500}
    if dodatkowe:
        params.update(dodatkowe)
    else:
        params["period"] = PERIOD
    try:
        r = requests.get(BASE + sciezka, params=params, timeout=30)
        if r.status_code != 200:
            print(f"  {nazwa:>30} | HTTP {r.status_code}: {r.text[:90]}")
            return None
        dane = r.json()
        if not dane:
            print(f"  {nazwa:>30} | pusta odpowiedz")
            return None
        pierwszy, ostatni = _pierwszy_ostatni(dane)
        dni = (ostatni - pierwszy) / 1000 / 86400
        print(f"  {nazwa:>30} | {len(dane):4d} pkt | {_ts(pierwszy)} -> {_ts(ostatni)} | {dni:7.1f} dni")
        return pierwszy
    except Exception as e:
        print(f"  {nazwa:>30} | BLAD: {type(e).__name__}: {e}")
        return None


def sprawdz_glebokosc(nazwa, sciezka, start_rok, dodatkowe=None):
    """Czy da sie siegnac po dane sprzed lat jawnym startTime?"""
    start_ms = int(datetime(start_rok, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    params = {"symbol": SYMBOL, "limit": 500, "startTime": start_ms}
    if dodatkowe:
        params.update(dodatkowe)
    else:
        params["period"] = PERIOD
    try:
        r = requests.get(BASE + sciezka, params=params, timeout=30)
        if r.status_code != 200:
            print(f"  {nazwa:>30} | startTime={start_rok} -> HTTP {r.status_code}")
            return
        dane = r.json()
        if not dane:
            print(f"  {nazwa:>30} | startTime={start_rok} -> PUSTO (brak danych z tego okresu)")
            return
        pierwszy, ostatni = _pierwszy_ostatni(dane)
        print(f"  {nazwa:>30} | startTime={start_rok} -> {len(dane)} pkt od {_ts(pierwszy)}")
    except Exception as e:
        print(f"  {nazwa:>30} | startTime={start_rok} -> BLAD: {type(e).__name__}")


print("=" * 100)
print("SONDA API — ile historii oddaja endpointy POZYCJONOWANIA (okres 4h, limit 500)")
print("=" * 100)
print("\n1. NAJSTARSZY PUNKT W DOMYSLNEJ ODPOWIEDZI\n")
for nazwa, sciezka in ENDPOINTY.items():
    sprawdz(nazwa, sciezka)

print("\n2. PROBA SIEGNIECIA WSTECZ JAWNYM startTime\n")
for nazwa, sciezka in ENDPOINTY.items():
    sprawdz_glebokosc(nazwa, sciezka, 2020)

print("\n3. DLA POROWNANIA — dane, ktore JUZ MAMY\n")
sprawdz("klines (OHLCV) 4h", POROWNANIE["klines (OHLCV)"], {"interval": "4h"})
sprawdz_glebokosc("klines (OHLCV) 4h", POROWNANIE["klines (OHLCV)"], 2020, {"interval": "4h"})
sprawdz("fundingRate", POROWNANIE["fundingRate"], {})
sprawdz_glebokosc("fundingRate", POROWNANIE["fundingRate"], 2020, {})
