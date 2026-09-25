"""
fetch_live.py — świeże dane do dziennika na żywo (`backtest/live_journal.py`, `dziennik/README.md`).

Osobny katalog `data/raw/live/` — zamrożone cache rund (`data/raw/universe`, …) zostają nietknięte.
Źródła (te same, co w rundach TS1/CP1, publiczne, bez klucza):
- Binance USDT-M: lista aktywnych perpetuali (`exchangeInfo`), świece 1d z open/high/low/close/obrót,
  funding — każdy przebieg nadpisuje pliki (dane na żywo, nie archiwum);
- Coinbase Exchange: BTC-USD 1d (`data.fetch_external.fetch_coinbase_daily`);
- Binance spot: BTC/USDT 8h (świeca 16:00 = zamknięcie o 24:00 UTC, jak `run_coinbase_cp1.daily_premium`);
- alternative.me: Fear & Greed dzienny (`data.fetch_external.fetch_fng`, poprawka 8) — TYLKO etykieta do
  zapisu; awaria tego źródła nie zatrzymuje pobierania ani dziennika (`fetch_fng_safe`).
Tylko świece ZAMKNIĘTE (open_time + 1 dzień ≤ teraz). Testy bez sieci: `tests/test_live_journal.py`.

    PYTHONUTF8=1 py -m data.fetch_live
"""

from __future__ import annotations

import re
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

ENGINE_START = pd.Timestamp("2025-09-01", tz="UTC")  # = backtest.live_journal.ENGINE_START (test)

LIVE_DIR = Path("data/raw/live")
# nazwa pliku z odpowiedzi giełdy: A–Z, 0–9 albo litery spoza ASCII (np. 币安人生USDT — był w top-20
# w 2026-05, X1F); żadnych kropek, ukośników, dwukropków, spacji ani małych liter ASCII
SYMBOL_RE = re.compile(r"(?:[A-Z0-9]|(?![\x00-\x7f])\w){1,40}USDT")
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
        if s.get("quoteAsset") != "USDT" or not SYMBOL_RE.fullmatch(sym):
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


def symbol_files(live_dir: Path) -> dict[str, Path]:
    """Pliki świec perpetuali `<SYMBOL>_1d.parquet` — bez `coinbase_BTC-USD_1d.parquet` i innych."""
    out = {}
    for f in sorted(Path(live_dir).glob("*_1d.parquet")):
        sym = f.name[: -len("_1d.parquet")]
        if SYMBOL_RE.fullmatch(sym):
            out[sym] = f
    return out


def funding_symbols(live_dir: Path, now: pd.Timestamp) -> list[str]:
    """Funding potrzebny silnikowi: członkowie koszyka w każdym miesiącu od `ENGINE_START` + BTC."""
    from backtest.rebalance_premium import monthly_members

    volume = pd.concat(
        {
            s: d.set_index(pd.to_datetime(d["open_time"], utc=True))["quote_volume"]
            for s, d in ((s, pd.read_parquet(f)) for s, f in symbol_files(live_dir).items())
            if len(d)
        },
        axis=1,
    ).sort_index()
    members = monthly_members(volume, list(pd.date_range(ENGINE_START, now, freq="MS")))
    return sorted({s for syms in members.values() for s in syms} | {"BTCUSDT"})


def fetch_fng_safe(out_dir: Path) -> Path | None:
    """
    Fear & Greed (alternative.me) do `out_dir` (poprawka 8): pełna historia, nadpisywana przy każdym
    przebiegu. Błąd sieci/schematu → wydruk i `None`; dziennik ma liczyć bez etykiety.
    """
    from data.fetch_external import fetch_fng

    try:
        return fetch_fng(out_dir, force=True)
    except Exception as exc:  # noqa: BLE001 — etykieta pomocnicza, nie może zatrzymać przebiegu
        print(
            f"[live] Fear & Greed BŁĄD {type(exc).__name__}: {str(exc)[:120]} — etykieta bez aktualizacji",
            flush=True,
        )
        return None


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
        kl.to_parquet(out_dir / f"{sym}_1d.parquet", index=False)
        if i % 100 == 0:
            print(f"[live] świece {i}/{len(symbols)}", flush=True)
    need = funding_symbols(out_dir, now)
    print(
        f"[live] funding dla {len(need)} członków koszyka od {ENGINE_START.date()} + BTC",
        flush=True,
    )
    for sym in need:
        fu = fetch_funding_raw(ex, sym, start_ms, end_ms)
        time.sleep(REQUEST_PACING_S)
        fu.to_parquet(out_dir / f"{sym}_funding.parquet", index=False)
    fetch_coinbase_daily("BTC-USD", start[:10], out_dir, force=True)
    spot = get_ohlcv("BTC/USDT", "8h", start, now.strftime("%Y-%m-%dT%H:%M:%SZ"), "binance")
    spot = spot[spot["timestamp"] + pd.Timedelta(hours=8) <= now]
    spot.to_parquet(out_dir / "spot_BTC-USDT_8h.parquet", index=False)
    fetch_fng_safe(out_dir)
    return {"symbols": len(symbols), "fetched_at": now.isoformat()}


if __name__ == "__main__":
    info = run(Path(sys.argv[1]) if len(sys.argv) > 1 else LIVE_DIR)
    print(f"[live] koniec: {info}", flush=True)
