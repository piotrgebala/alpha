"""
fetch_universe.py

Pobieranie historii funding rate i świec dziennych dla CAŁEGO uniwersum perpetuali
Binance USDS-M — łącznie z kontraktami WYCOFANYMI (runda P2, carry przekrojowy).

Dlaczego osobny moduł, a nie `fetch_funding`/`fetch_ohlcv`:
- tamte idą przez `ccxt` po symbolu z `load_markets()`, a lista rynków giełdy zawiera
  wyłącznie kontrakty dziś notowane lub w trakcie rozliczania. Uniwersum zbudowane z niej
  to klasyczny błąd przeżywalności: monety, które upadły (LUNA, SRM, HNT…), znikają ze
  zbioru, a razem z nimi najgorsze epizody;
- surowe endpointy `/fapi/v1/fundingRate` i `/fapi/v1/klines` oddają historię także dla
  symboli spoza listy rynków (zweryfikowane 2026-09-22 na LUNAUSDT, SRMUSDT, HNTUSDT);
- spis wszystkich symboli, łącznie z wycofanymi, daje publiczne archiwum
  `data.binance.vision` (listing S3).

Stawki funding NIE są na wspólnej siatce 8h — część symboli rozlicza się co 4h lub 1h
(`/fapi/v1/fundingInfo`). Moduł zapisuje surowe rekordy; sumowanie po czasie należy do
warstwy analizy (`backtest/carry_probe.py`).
"""

from __future__ import annotations

import re
import sys
import time
import urllib.request
from pathlib import Path

import ccxt
import pandas as pd

ARCHIVE_LIST_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ARCHIVE_FUNDING_PREFIX = "data/futures/um/monthly/fundingRate/"

# Aktywa bazowe będące stablecoinami — kontrakt na nie nie jest ekspozycją na krypto.
STABLE_BASES = frozenset({"USDC", "BUSD", "TUSD", "FDUSD", "USDP", "DAI", "USDE", "USD1"})

FETCH_MAX_RETRIES = 5
FETCH_BACKOFF_S = 1.0
FUNDING_PAGE_LIMIT = 1000
KLINES_PAGE_LIMIT = 1500
# Limit `fundingRate` to 500 zapytań / 5 min / IP (0,6 s) — z zapasem.
REQUEST_PACING_S = 0.7

DAY_MS = 86_400_000


def parse_archive_listing(xml: str, prefix: str = ARCHIVE_FUNDING_PREFIX) -> list[str]:
    """Wyciąga nazwy symboli z jednej strony listingu S3 (`<Prefix>…/SYMBOL/</Prefix>`)."""
    pattern = re.escape(prefix) + r"([^/<]+)/</Prefix>"
    return re.findall(r"<Prefix>" + pattern, xml)


def list_archive_symbols(prefix: str = ARCHIVE_FUNDING_PREFIX, fetch=None) -> list[str]:
    """
    Wszystkie symbole, dla których archiwum ma miesięczne pliki funding — łącznie z wycofanymi.

    `fetch(url) -> str` można podmienić w testach.
    """
    if fetch is None:

        def fetch(url: str) -> str:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return resp.read().decode("utf-8")

    symbols: list[str] = []
    marker = ""
    while True:
        url = f"{ARCHIVE_LIST_URL}?delimiter=/&prefix={prefix}"
        if marker:
            url += f"&marker={marker}"
        xml = fetch(url)
        page = parse_archive_listing(xml, prefix)
        symbols.extend(page)
        if "<IsTruncated>true</IsTruncated>" in xml and page:
            marker = f"{prefix}{page[-1]}/"
        else:
            break
    return sorted(set(symbols))


def select_universe(
    archive_symbols: list[str],
    tradifi_ids: set[str],
    stable_bases: frozenset[str] = STABLE_BASES,
) -> list[str]:
    """
    Uniwersum P2: symbole `*USDT` z archiwum, bez kontraktów TRADIFI i bez stablecoinów jako
    aktywa bazowego. Wycofane symbole ZOSTAJĄ — o to właśnie chodzi.
    """
    out = []
    for sym in archive_symbols:
        if not sym.endswith("USDT"):
            continue
        base = sym[: -len("USDT")]
        if not base or sym in tradifi_ids or base in stable_bases:
            continue
        out.append(sym)
    return sorted(out)


def list_tradifi_ids(exchange) -> set[str]:
    """Id kontraktów `TRADIFI_PERPETUAL` (akcje/surowce) z bieżącej listy giełdy."""
    info = exchange.fapiPublicGetExchangeInfo()
    return {
        s["symbol"] for s in info.get("symbols", []) if s.get("contractType") == "TRADIFI_PERPETUAL"
    }


def _call_with_retry(
    func, params: dict, max_retries: int = FETCH_MAX_RETRIES, backoff_s: float = FETCH_BACKOFF_S
):
    """Retry na `ccxt.NetworkError` z backoffem wykładniczym — ta sama polityka co fetch_ohlcv."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return func(params)
        except ccxt.NetworkError as e:
            last_error = e
            wait = backoff_s * (2**attempt)
            print(
                f"[universe] błąd sieci (próba {attempt + 1}/{max_retries}): {e!r} — czekam {wait:.0f}s"
            )
            time.sleep(wait)
    assert last_error is not None
    raise last_error


def _empty_funding() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
            "funding_rate": pd.Series(dtype=float),
        }
    )


def _empty_klines() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open_time": pd.Series(dtype="datetime64[ns, UTC]"),
            "close": pd.Series(dtype=float),
            "quote_volume": pd.Series(dtype=float),
        }
    )


def fetch_funding_raw(
    exchange, symbol_id: str, start_ms: int, end_ms: int, pacing_s: float = REQUEST_PACING_S
) -> pd.DataFrame:
    """
    Pełna historia funding dla surowego id symbolu, `[start_ms, end_ms)`, z paginacją.

    Returns:
        DataFrame: timestamp (UTC, tz-aware), funding_rate — rosnąco, bez duplikatów.
    """
    records: list[dict] = []
    since = start_ms
    while since < end_ms:
        page = _call_with_retry(
            exchange.fapiPublicGetFundingRate,
            {
                "symbol": symbol_id,
                "startTime": since,
                "endTime": end_ms - 1,
                "limit": FUNDING_PAGE_LIMIT,
            },
        )
        if not page:
            break
        records.extend(page)
        last_ts = int(page[-1]["fundingTime"])
        if last_ts < since or len(page) < FUNDING_PAGE_LIMIT:
            break
        since = last_ts + 1
        time.sleep(pacing_s)

    if not records:
        return _empty_funding()
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [int(r["fundingTime"]) for r in records], unit="ms", utc=True
            ),
            "funding_rate": [float(r["fundingRate"]) for r in records],
        }
    )
    df = df[df["timestamp"] < pd.Timestamp(end_ms, unit="ms", tz="UTC")]
    return df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)


def fetch_klines_1d_raw(
    exchange, symbol_id: str, start_ms: int, end_ms: int, pacing_s: float = REQUEST_PACING_S
) -> pd.DataFrame:
    """
    Świece dzienne dla surowego id symbolu. Zapisuje tylko to, czego potrzebuje P2.

    Returns:
        DataFrame: open_time (UTC), close, quote_volume — rosnąco, tylko świece ZAMKNIĘTE
        przed `end_ms` (open_time + 1 dzień <= end_ms).
    """
    rows: list[list] = []
    since = start_ms
    while since < end_ms:
        page = _call_with_retry(
            exchange.fapiPublicGetKlines,
            {
                "symbol": symbol_id,
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

    if not rows:
        return _empty_klines()
    df = pd.DataFrame(
        {
            "open_time": pd.to_datetime([int(r[0]) for r in rows], unit="ms", utc=True),
            "close": [float(r[4]) for r in rows],
            "quote_volume": [float(r[7]) for r in rows],
        }
    )
    closed = df["open_time"] + pd.Timedelta(days=1) <= pd.Timestamp(end_ms, unit="ms", tz="UTC")
    return df[closed].drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def cache_paths(cache_dir: str | Path, symbol_id: str) -> tuple[Path, Path]:
    d = Path(cache_dir)
    return d / f"{symbol_id}_funding.parquet", d / f"{symbol_id}_1d.parquet"


def fetch_universe_cached(
    symbols: list[str],
    start: str,
    end: str,
    cache_dir: str | Path,
    exchange=None,
    pacing_s: float = REQUEST_PACING_S,
) -> dict:
    """
    Pobiera funding + świece 1d dla każdego symbolu, pomijając te, które już są w cache.
    Symbol bez danych dostaje pusty plik — żeby ponowne uruchomienie go nie odpytywało.

    Returns:
        {"fetched": int, "cached": int, "empty": list[str]}
    """
    if exchange is None:
        exchange = ccxt.binanceusdm({"enableRateLimit": False})
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    start_ms = int(pd.Timestamp(start).value // 1_000_000)
    end_ms = int(pd.Timestamp(end).value // 1_000_000)

    fetched, cached, empty = 0, 0, []
    for i, sym in enumerate(symbols, 1):
        f_path, k_path = cache_paths(cache_dir, sym)
        if f_path.exists() and k_path.exists():
            cached += 1
            continue
        try:
            fund = fetch_funding_raw(exchange, sym, start_ms, end_ms, pacing_s)
            time.sleep(pacing_s)
            kl = fetch_klines_1d_raw(exchange, sym, start_ms, end_ms, pacing_s)
            time.sleep(pacing_s)
        except ccxt.BadSymbol:
            # Symbol z archiwum, którego giełda nie rozpoznaje (np. przemianowany) — zapisany
            # jako pusty, żeby było widać, kogo NIE ma w zbiorze.
            print(f"[universe] {sym}: giełda nie rozpoznaje symbolu — pusty", flush=True)
            fund, kl = _empty_funding(), _empty_klines()
        fund.to_parquet(f_path, index=False)
        kl.to_parquet(k_path, index=False)
        fetched += 1
        if fund.empty or kl.empty:
            empty.append(sym)
        if i % 25 == 0:
            print(
                f"[universe] {i}/{len(symbols)} (pobrane {fetched}, z cache {cached})", flush=True
            )
    return {"fetched": fetched, "cached": cached, "empty": empty}


if __name__ == "__main__":
    # Użycie: py -m data.fetch_universe <cache_dir> [start] [end]
    cache = sys.argv[1] if len(sys.argv) > 1 else "data/raw/universe"
    start = sys.argv[2] if len(sys.argv) > 2 else "2020-01-01T00:00:00Z"
    end = sys.argv[3] if len(sys.argv) > 3 else "2026-07-01T00:00:00Z"
    ex = ccxt.binanceusdm({"enableRateLimit": False})
    archive = list_archive_symbols()
    universe = select_universe(archive, list_tradifi_ids(ex))
    print(f"[universe] archiwum: {len(archive)} symboli, uniwersum P2: {len(universe)}", flush=True)
    result = fetch_universe_cached(universe, start, end, cache, ex)
    print(
        f"[universe] koniec: {result['fetched']} pobranych, {result['cached']} z cache, "
        f"{len(result['empty'])} pustych: {result['empty'][:20]}",
        flush=True,
    )
