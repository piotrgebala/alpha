"""
fetch_live.py — świeże dane do dziennika na żywo (`backtest/live_journal.py`, `dziennik/README.md`).

Osobny katalog `data/raw/live/` — zamrożone cache rund (`data/raw/universe`, …) zostają nietknięte.
Źródła (te same, co w rundach TS1/CP1, publiczne, bez klucza):
- Binance USDT-M: lista aktywnych perpetuali (`exchangeInfo`), świece 1d z open/high/low/close/obrót,
  funding — każdy przebieg nadpisuje pliki (dane na żywo, nie archiwum);
- Coinbase Exchange: BTC-USD 1d (`data.fetch_external.fetch_coinbase_daily`);
- Binance spot: BTC/USDT 8h (świeca 16:00 = zamknięcie o 24:00 UTC, jak `run_coinbase_cp1.daily_premium`).
Tylko świece ZAMKNIĘTE (open_time + 1 dzień ≤ teraz). Testy bez sieci: `tests/test_live_journal.py`.

    PYTHONUTF8=1 py -m data.fetch_live
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

from data.fetch_universe import (
    DAY_MS,
    KLINES_PAGE_LIMIT,
    REQUEST_PACING_S,
    STABLE_BASES,
    _call_with_retry,
    fetch_funding_raw,
)

LIVE_DIR = Path("data/raw/live")
LIVE_START = (
    "2025-06-01T00:00:00Z"  # rozbieg: składy miesięczne, sygnał 28 dni, σ̂ EWMA, budżet ryzyka
)


def active_usdt_perpetuals(
    exchange_info: dict, stable_bases: frozenset = STABLE_BASES
) -> list[str]:
    """Aktywne perpetuale `*USDT` (bez TRADIFI i stablecoinów jako bazy) z odpowiedzi `exchangeInfo`."""
    out = []
    for s in exchange_info.get("symbols", []):
        sym = s.get("symbol", "")
        if s.get("contractType") != "PERPETUAL" or s.get("status") != "TRADING":
            continue
        if s.get("quoteAsset") != "USDT" or not sym.endswith("USDT"):
            continue
        base = sym[: -len("USDT")]
        if base and base not in stable_bases:
            out.append(sym)
    return sorted(out)


def parse_klines_1d(rows: list[list], end_ms: int) -> pd.DataFrame:
    """Surowe świece Binance → open_time (UTC), open, high, low, close, quote_volume; tylko zamknięte."""
    cols = ["open_time", "open", "high", "low", "close", "quote_volume"]
    if not rows:
        return pd.DataFrame({c: pd.Series(dtype=float) for c in cols}).astype(
            {"open_time": "datetime64[ns, UTC]"}
        )
    df = pd.DataFrame(
        {
            "open_time": pd.to_datetime([int(r[0]) for r in rows], unit="ms", utc=True),
            "open": [float(r[1]) for r in rows],
            "high": [float(r[2]) for r in rows],
            "low": [float(r[3]) for r in rows],
            "close": [float(r[4]) for r in rows],
            "quote_volume": [float(r[7]) for r in rows],
        }
    )
    closed = df["open_time"] + pd.Timedelta(days=1) <= pd.Timestamp(end_ms, unit="ms", tz="UTC")
    return df[closed].drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def fetch_klines_1d(
    exchange, symbol: str, start_ms: int, end_ms: int, pacing_s: float = REQUEST_PACING_S
) -> pd.DataFrame:
    rows: list[list] = []
    since = start_ms
    while since < end_ms:
        page = _call_with_retry(
            exchange.fapiPublicGetKlines,
            {
                "symbol": symbol,
                "interval": "1d",
                "startTime": since,
                "endTime": end_ms - 1,
                "limit": KLINES_PAGE_LIMIT,
            },
        )
        if not page:
            break
        rows.extend(page)
        last_open = int(page[-1][0])
        if last_open < since or len(page) < KLINES_PAGE_LIMIT:
            break
        since = last_open + DAY_MS
        time.sleep(pacing_s)
    return parse_klines_1d(rows, end_ms)


def run(out_dir: Path = LIVE_DIR, start: str = LIVE_START) -> dict:
    import ccxt

    from data.fetch_external import fetch_coinbase_daily
    from data.fetch_ohlcv import get_ohlcv

    out_dir.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now(tz="UTC")
    end_ms = int(now.value // 1_000_000)
    start_ms = int(pd.Timestamp(start).value // 1_000_000)
    ex = ccxt.binanceusdm({"enableRateLimit": False})
    symbols = active_usdt_perpetuals(ex.fapiPublicGetExchangeInfo())
    print(f"[live] {len(symbols)} aktywnych perpetuali USDT", flush=True)
    for i, sym in enumerate(symbols, 1):
        kl = fetch_klines_1d(ex, sym, start_ms, end_ms)
        time.sleep(REQUEST_PACING_S)
        fu = fetch_funding_raw(ex, sym, start_ms, end_ms)
        time.sleep(REQUEST_PACING_S)
        kl.to_parquet(out_dir / f"{sym}_1d.parquet", index=False)
        fu.to_parquet(out_dir / f"{sym}_funding.parquet", index=False)
        if i % 50 == 0:
            print(f"[live] {i}/{len(symbols)}", flush=True)
    fetch_coinbase_daily("BTC-USD", start[:10], out_dir, force=True)
    spot = get_ohlcv("BTC/USDT", "8h", start, now.strftime("%Y-%m-%dT%H:%M:%SZ"), "binance")
    spot = spot[spot["timestamp"] + pd.Timedelta(hours=8) <= now]
    spot.to_parquet(out_dir / "spot_BTC-USDT_8h.parquet", index=False)
    return {"symbols": len(symbols), "fetched_at": now.isoformat()}


if __name__ == "__main__":
    info = run(Path(sys.argv[1]) if len(sys.argv) > 1 else LIVE_DIR)
    print(f"[live] koniec: {info}", flush=True)
