"""
fetch_funding.py

Pobieranie i cache'owanie historii FUNDING RATE z giełdy (Binance USDS-M Futures).

Dlaczego osobny moduł, a nie kolumna w `fetch_ohlcv`: funding ma **własną siatkę czasową**
(co 8h: 00:00 / 08:00 / 16:00 UTC), niezależną od interwału świec. Sklejanie go ze świecami
to decyzja modelowa (jak propagować wartość między rozliczeniami), a nie krok pobierania —
i należy do warstwy cech, nie do warstwy danych.

Kontekst projektowy (H2): do Fazy 0 funding istniał wyłącznie jako **stała kosztowa**
(`backtest/costs.py::FUNDING_RATE_8H = 0.0001`). Ten moduł po raz pierwszy w projekcie
ściąga go jako **szereg czasowy**, bo hipoteza H2 traktuje go jako źródło informacji
spoza OHLCV — patrz `runs/2026-09-22_z10-zamkniecie-fazy-0/README.md` (diagnoza: wąskie
gardło Fazy 0 było informacyjne, wszystkie 10 cech to transformacje ceny i wolumenu).

Dostępność zweryfikowana na maszynie użytkownika 2026-09-22: BTC/USDT:USDT ma funding
od **2019-09-10T08:00:00Z**, czyli od tego samego dnia co świece 4h w `data/raw/`.
"""

from __future__ import annotations

import time
from pathlib import Path

import ccxt
import pandas as pd

FUNDING_COLUMNS = ["timestamp", "funding_rate"]

# Binance USDS-M Futures rozlicza funding 3x/dobę. Ta stała opisuje SIATKĘ danych
# (co ile przychodzi rekord), nie parametr modelu.
FUNDING_PERIOD_HOURS = 8

# Te same wartości co w fetch_ohlcv — jeden model zachowania sieciowego w całym projekcie.
FETCH_MAX_RETRIES = 5
FETCH_BACKOFF_S = 1.0
FETCH_PAGE_LIMIT = 1000


def _fetch_funding_page_with_retry(
    exchange,
    symbol: str,
    since: int,
    limit: int = FETCH_PAGE_LIMIT,
    max_retries: int = FETCH_MAX_RETRIES,
    backoff_s: float = FETCH_BACKOFF_S,
) -> list[dict]:
    """
    Jedna strona `fetch_funding_rate_history` z retry na `ccxt.NetworkError`.

    Identyczna polityka jak `fetch_ohlcv._fetch_page_with_retry`: backoff wykładniczy
    `backoff_s * 2**k`, `ExchangeError` NIE jest retry'owany (to błąd konfiguracji,
    np. zły symbol, a nie chwilowy problem sieci).

    Przyjmuje dowolny obiekt z metodą `fetch_funding_rate_history`, żeby dało się
    testować stubem bez sieci.
    """
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return exchange.fetch_funding_rate_history(symbol, since=since, limit=limit)
        except ccxt.NetworkError as e:
            last_error = e
            wait = backoff_s * (2**attempt)
            print(
                f"[funding] błąd sieci (próba {attempt + 1}/{max_retries}): "
                f"{e!r} — czekam {wait:.0f}s"
            )
            time.sleep(wait)
    assert last_error is not None
    raise last_error


def _raw_funding_to_df(records: list[dict]) -> pd.DataFrame:
    """Surowe rekordy ccxt → DataFrame(timestamp UTC, funding_rate)."""
    if not records:
        return pd.DataFrame(columns=FUNDING_COLUMNS)
    df = pd.DataFrame(
        {
            "timestamp": [r["timestamp"] for r in records],
            "funding_rate": [float(r["fundingRate"]) for r in records],
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


def _clean_funding(df: pd.DataFrame, end: str) -> pd.DataFrame:
    """
    Porządkuje szereg: obcina do [.., end), deduplikuje, sortuje, zaokrągla znacznik czasu.

    Zaokrąglenie do pełnej sekundy jest konieczne: Binance zwraca znaczniki rozjechane
    o kilka milisekund (np. `2026-09-21T00:00:00.007Z`), co psułoby zarówno wykrywanie
    dziur, jak i późniejsze łączenie ze świecami.
    """
    if df.empty:
        return df
    end_ts = pd.Timestamp(end, tz="UTC") if not isinstance(end, pd.Timestamp) else end
    df = df.copy()
    df["timestamp"] = df["timestamp"].dt.round("s")
    df = df[df["timestamp"] < end_ts]
    df = df.drop_duplicates(subset="timestamp", keep="first")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df[FUNDING_COLUMNS]


def find_funding_gaps(
    df: pd.DataFrame, period_hours: int = FUNDING_PERIOD_HOURS, tolerance_minutes: int = 5
) -> pd.DataFrame:
    """
    Zwraca rekordy, przed którymi brakuje co najmniej jednego okresu rozliczeniowego.

    Odpowiednik `fetch_ohlcv.find_gaps` dla siatki 8-godzinnej. Tolerancja w minutach,
    bo znaczniki bywają przesunięte o sekundy względem pełnej godziny.
    """
    if len(df) < 2:
        return pd.DataFrame(columns=["timestamp", "gap_before"])
    diffs = df["timestamp"].diff()
    max_allowed = pd.Timedelta(hours=period_hours) + pd.Timedelta(minutes=tolerance_minutes)
    gap_mask = diffs > max_allowed
    return df.loc[gap_mask, ["timestamp"]].assign(gap_before=diffs[gap_mask])


def get_funding_rate_history(
    symbol: str,
    start: str,
    end: str,
    exchange_id: str = "binanceusdm",
) -> pd.DataFrame:
    """
    Pobiera pełną historię funding rate w zakresie [start, end) z paginacją.

    Args:
        symbol: symbol ccxt, np. "BTC/USDT:USDT" (perpetual swap)
        start: ISO 8601, np. "2019-09-10T00:00:00Z"
        end: ISO 8601, wyłącznie
        exchange_id: nazwa klasy ccxt

    Returns:
        DataFrame: timestamp (UTC, tz-aware), funding_rate — chronologicznie, bez duplikatów.
    """
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class()

    since = exchange.parse8601(start)
    end_ts = exchange.parse8601(end)

    all_records: list[dict] = []
    while since < end_ts:
        page = _fetch_funding_page_with_retry(exchange, symbol, since, limit=FETCH_PAGE_LIMIT)
        if not page:
            break
        all_records.extend(page)
        last_ts = page[-1]["timestamp"]
        if last_ts <= since:
            # zabezpieczenie przed nieskończoną pętlą, gdyby giełda zwróciła te same dane
            break
        since = last_ts + 1
        time.sleep((exchange.rateLimit or 0) / 1000)

    return _clean_funding(_raw_funding_to_df(all_records), end)


def _cache_path(cache_dir: str, symbol: str, start: str, end: str) -> Path:
    safe_symbol = symbol.replace("/", "-").replace(":", "-")
    safe_start = start.replace(":", "").replace("-", "")
    safe_end = end.replace(":", "").replace("-", "")
    return Path(cache_dir) / f"{safe_symbol}_funding_{safe_start}_{safe_end}.parquet"


def get_funding_rate_history_cached(
    symbol: str,
    start: str,
    end: str,
    cache_dir: str = "data/raw",
    exchange_id: str = "binanceusdm",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Jak get_funding_rate_history, ale z trwałym cache parquet w cache_dir."""
    cache_dir_path = Path(cache_dir)
    cache_dir_path.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(cache_dir, symbol, start, end)

    if cache_file.exists() and not force_refresh:
        return pd.read_parquet(cache_file)

    df = get_funding_rate_history(symbol, start, end, exchange_id)
    if not df.empty:
        df.to_parquet(cache_file, index=False)
    return df


if __name__ == "__main__":
    import yaml

    with open("config/settings.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)["data"]

    symbol = cfg["primary_symbol"]
    # Funding pobieramy na PEŁNYM oknie 4h (2019-09), bo to najdłuższa historia, jaką ma
    # ten instrument — a H2 jest ograniczone liczebnością próby, tak samo jak S1 (Z19).
    start = (cfg.get("timeframe_start_overrides") or {}).get("4h", cfg["start"])
    end = cfg["end"]

    cache_file = _cache_path(cfg["cache_dir"], symbol, start, end)
    cached = cache_file.exists()
    df = get_funding_rate_history_cached(
        symbol=symbol,
        start=start,
        end=end,
        cache_dir=cfg["cache_dir"],
        exchange_id=cfg["exchange_id"],
    )
    source = "z cache" if cached else "POBRANE z giełdy"
    gaps = find_funding_gaps(df)
    # Uwaga: konsola Windows bywa na cp1250, gdzie "→" wywala UnicodeEncodeError.
    # Komunikat diagnostyczny trzymamy w ASCII — to nie jest miejsce na typografię.
    print(
        f"[{symbol} funding] {len(df)} rekordow ({source}): "
        f"{df['timestamp'].min()} -> {df['timestamp'].max()}, dziur: {len(gaps)}"
    )
    if not gaps.empty:
        print(gaps.to_string(index=False))
