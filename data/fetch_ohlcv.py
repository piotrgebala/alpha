"""
fetch_ohlcv.py

Pobieranie i cache'owanie świec OHLCV z giełdy (domyślnie Binance USDS-M Futures,
tj. rynek perpetual futures, nie spot).

UWAGA: dokładny format symbolu w ccxt zależy od wersji biblioteki i giełdy.
Przed pierwszym użyciem zweryfikuj na swojej maszynie:

    import ccxt
    ex = ccxt.binanceusdm()
    ex.load_markets()
    print([s for s in ex.symbols if "BTC/USDT" in s])

i popraw `symbol` w config/settings.yaml, jeśli się nie zgadza.
"""

from __future__ import annotations

import time
from pathlib import Path

import ccxt
import pandas as pd

OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def _raw_candles_to_df(candles: list[list[float]]) -> pd.DataFrame:
    """Konwertuje listę świec z ccxt (ms epoch) na DataFrame z tz-aware timestampem UTC."""
    df = pd.DataFrame(candles, columns=OHLCV_COLUMNS)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


def _clean_ohlcv(df: pd.DataFrame, end: str) -> pd.DataFrame:
    """
    Dedup (po timestampie, zostaw ostatni), sortowanie chronologiczne,
    odcięcie do granicy `end` (wyłącznie).

    Wydzielone z get_ohlcv, żeby dało się testować bez sieci/ccxt (patrz tests/).
    """
    df = df.drop_duplicates(subset="timestamp", keep="last")
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df[df["timestamp"] < pd.Timestamp(end, tz="UTC")].reset_index(drop=True)
    return df


def find_gaps(df: pd.DataFrame, timeframe_minutes: int, tolerance: int = 1) -> pd.DataFrame:
    """
    Raportuje (NIE rzuca wyjątku) miejsca, gdzie odstęp między świecami przekracza
    (tolerance + 1) * timeframe_minutes. Giełdy krypto mają legalne przerwy
    (maintenance, itp.) — to diagnostyka, nie hard-fail.

    Returns:
        DataFrame z kolumnami [timestamp, gap_before] dla wierszy z dziurą.
    """
    diffs = df["timestamp"].diff()
    max_allowed = pd.Timedelta(minutes=timeframe_minutes * (tolerance + 1))
    gap_mask = diffs > max_allowed
    return df.loc[gap_mask, ["timestamp"]].assign(gap_before=diffs[gap_mask])


def get_ohlcv(
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    exchange_id: str = "binanceusdm",
) -> pd.DataFrame:
    """
    Pobiera świece OHLCV z giełdy w zakresie [start, end) z paginacją.

    Args:
        symbol: symbol w formacie ccxt, np. "BTC/USDT:USDT" (perpetual swap)
        timeframe: np. "5m", "1h"
        start: ISO 8601, np. "2025-07-01T00:00:00Z"
        end: ISO 8601, wyłącznie
        exchange_id: nazwa klasy ccxt, domyślnie Binance USDS-M Futures

    Returns:
        DataFrame: timestamp (UTC, tz-aware), open, high, low, close, volume.
        Sortowany chronologicznie, bez duplikatów timestampów.
    """
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class()

    since = exchange.parse8601(start)
    end_ts = exchange.parse8601(end)

    all_candles: list[list[float]] = []
    while since < end_ts:
        candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not candles:
            break
        all_candles.extend(candles)
        last_ts = candles[-1][0]
        if last_ts <= since:
            # zabezpieczenie przed nieskończoną pętlą, gdyby giełda zwróciła te same dane
            break
        since = last_ts + 1
        time.sleep((exchange.rateLimit or 0) / 1000)

    if not all_candles:
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    df = _raw_candles_to_df(all_candles)
    return _clean_ohlcv(df, end)


def _cache_path(cache_dir: str, symbol: str, timeframe: str, start: str, end: str) -> Path:
    safe_symbol = symbol.replace("/", "-").replace(":", "-")
    safe_start = start.replace(":", "").replace("-", "")
    safe_end = end.replace(":", "").replace("-", "")
    filename = f"{safe_symbol}_{timeframe}_{safe_start}_{safe_end}.parquet"
    return Path(cache_dir) / filename


def get_ohlcv_cached(
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    cache_dir: str = "data/raw",
    exchange_id: str = "binanceusdm",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Jak get_ohlcv, ale z lokalnym cache w formacie parquet w cache_dir."""
    cache_dir_path = Path(cache_dir)
    cache_dir_path.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(cache_dir, symbol, timeframe, start, end)

    if cache_file.exists() and not force_refresh:
        return pd.read_parquet(cache_file)

    df = get_ohlcv(symbol, timeframe, start, end, exchange_id)
    if not df.empty:
        df.to_parquet(cache_file, index=False)
    return df


if __name__ == "__main__":
    import yaml

    with open("config/settings.yaml") as f:
        cfg = yaml.safe_load(f)["data"]

    # Faza 0: pobierz TYLKO primary_symbol (BTC) — walidacja hipotezy najpierw na jednym
    # instrumencie. Pozostałe symbole w cfg["symbols"] to przygotowanie na Fazę 1 (test
    # generalizacji), nie równoległa walidacja teraz.
    symbols_to_fetch = [cfg["primary_symbol"]]

    for symbol in symbols_to_fetch:
        df = get_ohlcv_cached(
            symbol=symbol,
            timeframe=cfg["timeframe"],
            start=cfg["start"],
            end=cfg["end"],
            cache_dir=cfg["cache_dir"],
            exchange_id=cfg["exchange_id"],
        )
        print(f"[{symbol}] Pobrano {len(df)} świec: {df['timestamp'].min()} -> {df['timestamp'].max()}")

        gaps = find_gaps(df, timeframe_minutes=5)
        if len(gaps) > 0:
            print(f"[{symbol}] UWAGA: znaleziono {len(gaps)} dziur w danych:")
            print(gaps)
