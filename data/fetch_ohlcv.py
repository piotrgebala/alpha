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

# Commit 2.10 (Z5): retry z wykładniczym backoffem na błędy sieciowe. Przy 3 latach 5m
# (~316 sekwencyjnych stron po 1000 świec) pojedynczy timeout bez retry wyrzucał całość
# (zapis do parquet dopiero po zakończeniu pętli). Wartości startowe, nie strojone.
FETCH_MAX_RETRIES = 5
FETCH_BACKOFF_S = 1.0
FETCH_PROGRESS_EVERY_PAGES = 50


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



# Interwały docelowe wspierane przez `resample_ohlcv` (Commit 2.6) — mapowanie na alias
# `pandas.DataFrame.resample`. Celowo mały, zamknięty zbiór (nie ogólny parser interwałów) —
# to narzędzie dla JEDNEGO, z góry określonego eksperymentu (walidacja hipotezy na 1h/4h),
# nie ogólna funkcja "zmień timeframe na cokolwiek".
RESAMPLE_TARGET_TIMEFRAMES = {"1h": "1h", "4h": "4h"}

# Z9: długość świecy w minutach per interwał — potrzebne, bo `find_gaps` i koszty funding
# liczą się z realnego czasu, nie z liczby świec. Zamknięty zbiór, jak RESAMPLE_TARGET_TIMEFRAMES.
TIMEFRAME_MINUTES = {"5m": 5, "1h": 60, "4h": 240}


def resample_ohlcv(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
    """
    Agreguje świece OHLCV do grubszego interwału (np. 5m -> 1h/4h) standardową agregacją
    OHLC/wolumenu: open=pierwszy, high=max, low=min, close=ostatni, volume=suma.

    UŻYCIE (Commit 2.6, 2026-09-21): to środowisko nie ma dostępu sieciowego do Binance
    (`fapi.binance.com` blokowane przez proxy), więc natywny fetch 1h/4h przez
    `get_ohlcv_cached` nie jest tu możliwy. Ta funkcja jest ŚWIADOMYM ZASTĘPSTWEM: agreguje
    z tego samego, już zweryfikowanego (Commit 1, `find_gaps` = zero dziur) źródła 5m, zamiast
    pobierać niezależnie z giełdy. To NIE jest identyczne z natywnym fetchem 1h/4h (patrz
    ograniczenia niżej) — traktuj wynik jako "resampled from 5m", jawnie odróżnione w nazwie
    pliku cache od potencjalnego przyszłego natywnego fetcha (ten sam `symbol`/`timeframe`
    dałby inną nazwę pliku przez `get_ohlcv_cached._cache_path`).

    Wymaga (odpowiedzialność WYWOŁUJĄCEGO, nie tej funkcji): `df` bez dziur (`find_gaps`) i
    posortowany chronologicznie — inaczej `resample` cicho wypełni brakujące okna NaN-ami
    zamiast zgłosić błąd. `timestamp` = LEWA krawędź okna (etykieta = początek świecy),
    zgodnie z konwencją ccxt/Binance dla natywnie pobranych świec.

    Ograniczenia względem natywnego fetcha z giełdy (świadome, do udokumentowania w wynikach,
    nie do "naprawienia" tutaj): (1) giełda może liczyć swoje natywne świece 1h/4h z danych
    o wyższej rozdzielczości niż 5m (np. z tickowych), więc high/low mogą się nieznacznie różnić
    od agregacji z 5m, jeśli ekstremum ceny wypadło WEWNĄTRZ jednej świecy 5m, a nie na jej
    granicy — agregacja z 5m jest wtedy identyczna z natywną TYLKO gdy ekstremum pokrywa się
    z granicą 5m, co w praktyce jest bliskim przybliżeniem, nie gwarancją identyczności;
    (2) wolumen sumowany z 5m powinien być identyczny z natywnym (addytywny, bez utraty
    precyzji ponad zaokrąglenie giełdy).

    Args:
        df: DataFrame [timestamp, open, high, low, close, volume], bez dziur, posortowany.
        target_timeframe: jeden z kluczy `RESAMPLE_TARGET_TIMEFRAMES` (obecnie "1h", "4h").

    Returns:
        DataFrame w tym samym schemacie OHLCV_COLUMNS, zagregowany, posortowany chronologicznie.
    """
    if target_timeframe not in RESAMPLE_TARGET_TIMEFRAMES:
        raise ValueError(
            f"target_timeframe={target_timeframe!r} nieobsługiwany — dozwolone: "
            f"{sorted(RESAMPLE_TARGET_TIMEFRAMES)}"
        )
    rule = RESAMPLE_TARGET_TIMEFRAMES[target_timeframe]
    indexed = df.set_index("timestamp").sort_index()
    grouper = indexed.resample(rule, label="left", closed="left")
    resampled = grouper.agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )

    # Odrzuć bucket brzegowy (pierwszy/ostatni), jeśli nie ma PEŁNEJ liczby świec źródłowych —
    # inaczej niepełny bucket (np. dane zaczynające/kończące się w środku godziny przy resample
    # do 1h) dostałby poprawne, ale MYLĄCE OHLC policzone tylko z części okna, nieodróżnialne od
    # pełnego bucketu. `expected_count` liczone z medianowego kroku źródła — odporne na
    # pojedyncze duplikaty/braki, których i tak nie powinno być (Commit 1, find_gaps).
    source_step = df["timestamp"].sort_values().diff().median()
    target_delta = pd.Timedelta(rule)
    expected_count = round(target_delta / source_step)
    counts = grouper.size()
    resampled = resampled.loc[counts == expected_count]

    resampled = resampled.dropna(how="any").reset_index()
    return resampled[OHLCV_COLUMNS]


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


def _fetch_page_with_retry(
    exchange,
    symbol: str,
    timeframe: str,
    since: int,
    limit: int = 1000,
    max_retries: int = FETCH_MAX_RETRIES,
    backoff_s: float = FETCH_BACKOFF_S,
) -> list[list[float]]:
    """
    Jedna strona `fetch_ohlcv` z retry na `ccxt.NetworkError` (RequestTimeout,
    ExchangeNotAvailable, RateLimitExceeded, DDoSProtection — wszystkie dziedziczą po nim).
    Backoff wykładniczy: backoff_s * 2**k. Po wyczerpaniu prób re-raise ostatniego błędu.
    `ExchangeError` (np. zły symbol) NIE jest retry'owany — to błąd konfiguracji, nie sieci.

    Przyjmuje dowolny obiekt z metodą `fetch_ohlcv`, żeby dało się testować stubem bez sieci.
    """
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        except ccxt.NetworkError as e:
            last_error = e
            wait = backoff_s * (2**attempt)
            print(f"[fetch] błąd sieci (próba {attempt + 1}/{max_retries}): {e!r} — czekam {wait:.0f}s")
            time.sleep(wait)
    assert last_error is not None
    raise last_error


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
    n_pages = 0
    while since < end_ts:
        candles = _fetch_page_with_retry(exchange, symbol, timeframe, since, limit=1000)
        if not candles:
            break
        all_candles.extend(candles)
        n_pages += 1
        last_ts = candles[-1][0]
        if last_ts <= since:
            # zabezpieczenie przed nieskończoną pętlą, gdyby giełda zwróciła te same dane
            break
        if n_pages % FETCH_PROGRESS_EVERY_PAGES == 0:
            print(f"[fetch] {len(all_candles)} świec, ostatnia: {exchange.iso8601(last_ts)}")
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

    with open("config/settings.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)["data"]

    # Faza 0: pobierz TYLKO primary_symbol (BTC) — walidacja hipotezy najpierw na jednym
    # instrumencie. Pozostałe symbole w cfg["symbols"] to przygotowanie na Fazę 1 (test
    # generalizacji), nie równoległa walidacja teraz.
    symbols_to_fetch = [cfg["primary_symbol"]]

    # Z9: pobieraj WSZYSTKIE interwały z `cfg["timeframes"]` (domyślnie tylko podstawowy).
    # Cache jest trwały i kluczowany po (symbol, timeframe, start, end), więc raz pobrany
    # interwał nie jest ściągany ponownie — `data/raw/` to jedno miejsce na komplet danych.
    timeframes = cfg.get("timeframes") or [cfg["timeframe"]]

    # Z5b: niektóre interwały potrzebują DŁUŻSZEJ historii niż podstawowa. Powód nie jest
    # "więcej danych = lepiej" (to odrzucono w audycie), tylko konkretny: na 4h wiążącym
    # ograniczeniem eksperymentu jest LICZEBNOŚĆ PRÓBY (Z19: 1 551 świec `range` wobec
    # wymaganych 2 608). Nadpisanie dotyczy więc tylko tych interwałów, gdzie to ogranicza.
    start_overrides = cfg.get("timeframe_start_overrides") or {}

    for symbol in symbols_to_fetch:
        for timeframe in timeframes:
            start = start_overrides.get(timeframe, cfg["start"])
            cache_file = _cache_path(cfg["cache_dir"], symbol, timeframe, start, cfg["end"])
            cached = cache_file.exists()
            df = get_ohlcv_cached(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=cfg["end"],
                cache_dir=cfg["cache_dir"],
                exchange_id=cfg["exchange_id"],
            )
            source = "z cache" if cached else "POBRANE z giełdy"
            print(
                f"[{symbol} {timeframe}] {len(df)} świec ({source}): "
                f"{df['timestamp'].min()} -> {df['timestamp'].max()}"
            )
            print(f"    -> {cache_file}")

            minutes = TIMEFRAME_MINUTES.get(timeframe)
            if minutes is None:
                print(f"    [uwaga] nieznana długość świecy dla {timeframe} — pomijam raport dziur")
                continue
            gaps = find_gaps(df, timeframe_minutes=minutes)
            if len(gaps) > 0:
                print(f"    [uwaga] {len(gaps)} dziur w danych:")
                print(gaps)
            else:
                print("    brak dziur.")
