"""
collect_positioning.py — codzienne dopisywanie danych o POZYCJONOWANIU do trwałego archiwum.

Po co (P1, `runs/2026-09-22_p1-sonda-zrodel-danych/`): Binance udostępnia open interest
i proporcje long/short wyłącznie za ostatnie ~30 dni (`startTime` sprzed tego okna → HTTP 400).
Przy tej metodologii potrzeba ~3,4 roku historii, więc JEDYNA droga do tych danych to
zbieranie ich od dziś. Ten skrypt robi dokładnie to i nic więcej: nie liczy cech, nie dotyka
modelu. Uruchamiany codziennie (Harmonogram zadań Windows) — przy okresie 1h jedno zapytanie
oddaje 500 punktów (~20,8 dnia), więc nawet kilka dni przerwy nie tworzy dziury.

Zapis: `<out_dir>/<SYMBOL>_<endpoint>_<period>.parquet`, kolumny jak w odpowiedzi API
(liczby jako float) + `timestamp` (UTC). Kolejne uruchomienia dopisują i usuwają duplikaty.

Użycie:
    py -m data.collect_positioning [out_dir] [SYMBOL ...]

Harmonogram (Windows, raz dziennie o 09:00; uruchomić PO scaleniu do master, bo zadanie
wskazuje na główny katalog repo):
    schtasks /Create /SC DAILY /ST 09:00 /TN "CLAS5-positioning" /TR "cmd /c cd /d C:\\Users\\pitge\\GIT\\alpha && py -m data.collect_positioning >> data\\raw\\positioning\\collect.log 2>&1"
Wyłączenie: schtasks /Delete /TN "CLAS5-positioning" /F
"""

from __future__ import annotations

import sys
from pathlib import Path

import ccxt
import pandas as pd

ENDPOINTS = {
    "openInterestHist": "fapiDataGetOpenInterestHist",
    "topLongShortAccountRatio": "fapiDataGetTopLongShortAccountRatio",
    "topLongShortPositionRatio": "fapiDataGetTopLongShortPositionRatio",
    "globalLongShortAccountRatio": "fapiDataGetGlobalLongShortAccountRatio",
    "takerlongshortRatio": "fapiDataGetTakerlongshortRatio",
}
DEFAULT_SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
)  # config/settings.yaml → data.symbols
PERIOD = "1h"
LIMIT = 500


def records_to_df(records: list[dict]) -> pd.DataFrame:
    """Odpowiedź API -> DataFrame: `timestamp` (UTC), pola liczbowe jako float, `symbol` pominięty."""
    if not records:
        return pd.DataFrame({"timestamp": pd.Series(dtype="datetime64[ns, UTC]")})
    df = pd.DataFrame(records).drop(columns=["symbol", "pair"], errors="ignore")
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms", utc=True)
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def merge_append(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Dopisuje nowe wiersze; przy duplikacie znacznika wygrywa NOWSZY odczyt."""
    frames = [f for f in (existing, new) if f is not None and not f.empty]
    if not frames:
        return new
    out = pd.concat(frames, ignore_index=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)
    return (
        out.drop_duplicates("timestamp", keep="last")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def collect(
    out_dir: str | Path, symbols=DEFAULT_SYMBOLS, exchange=None, period: str = PERIOD
) -> dict:
    """
    Jeden przebieg zbierania. Błąd jednego endpointu nie przerywa pozostałych.

    Returns:
        {"<SYMBOL>_<endpoint>": liczba nowych wierszy} oraz "errors": lista komunikatów.
    """
    if exchange is None:
        exchange = ccxt.binanceusdm()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report: dict = {"errors": []}
    for sym in symbols:
        for name, method in ENDPOINTS.items():
            key = f"{sym}_{name}"
            try:
                recs = getattr(exchange, method)({"symbol": sym, "period": period, "limit": LIMIT})
            except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                report["errors"].append(f"{key}: {e!r}")
                continue
            path = out / f"{sym}_{name}_{period}.parquet"
            old = pd.read_parquet(path) if path.exists() else None
            merged = merge_append(old, records_to_df(recs))
            report[key] = len(merged) - (0 if old is None else len(old))
            merged.to_parquet(path, index=False)
    return report


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/raw/positioning"
    syms = tuple(sys.argv[2:]) or DEFAULT_SYMBOLS
    rep = collect(target, syms)
    added = sum(v for k, v in rep.items() if k != "errors")
    print(
        f"[positioning] {pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC: +{added} wierszy, bledow: {len(rep['errors'])}"
    )
    for e in rep["errors"]:
        print(f"  {e}")
    sys.exit(1 if rep["errors"] else 0)
