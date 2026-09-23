"""
fetch_external.py — pobieranie ZEWNĘTRZNYCH źródeł danych (runda P3) do `data/raw/external/`.

Po co (P3, `runs/2026-09-23_p3-sonda-zrodel-ii/`): P1 skreśliło dane o pozycjonowaniu na
podstawie REST API (30 dni historii), ale publiczne ARCHIWUM `data.binance.vision`
(`futures/um/daily/metrics`) ma te same wielkości co 5 minut od 2020-09-01. Do tego źródła
spoza Binance: Deribit (DVOL), CoinMetrics community (on-chain), alternative.me (Fear & Greed),
FRED (stopy, dolar, S&P), Coinbase (spot BTC-USD), plus funding COIN-M i świece kontraktów
kwartalnych Binance. Wszystko publiczne, bez klucza, bez opłat.

Zasady modułu:
- czyste funkcje `parse_*` (testowane bez sieci, `tests/test_fetch_external.py`), osobno
  cienka warstwa sieciowa `http_get` z ponawianiem;
- fail loud: nieznany nagłówek/schemat → `ValueError`, nie ciche pominięcie kolumn;
- idempotencja: plik docelowy istnieje → pomijany (`--force` nadpisuje);
- zapis parquet, znaczniki czasu UTC (tz-aware), rosnąco, bez duplikatów;
- moduł NICZEGO nie liczy poza pobraniem i zapisem — profil (`data/profile_external.py`)
  i pomiary są osobno.

Użycie:
    py -m data.fetch_external [out_dir] [--force] [--only metrics,dvol,...]
Źródła: metrics, dated, coinm_funding, dvol, coinmetrics, fng, fred, coinbase.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ARCHIVE_LIST_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ARCHIVE_FILE_URL = "https://data.binance.vision/"
DAPI_FUNDING_URL = "https://dapi.binance.com/dapi/v1/fundingRate"
DERIBIT_DVOL_URL = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
COINMETRICS_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
FNG_URL = "https://api.alternative.me/fng/?limit=0&format=json"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products/{product}/candles"

DEFAULT_OUT_DIR = "data/raw/external"
DEFAULT_START = "2019-01-01"  # zapas na warmupy przed bazą 2021-01-01 (CLAUDE.md zasada 20)

USER_AGENT = "clas5-fetch-external/1.0"
HTTP_TIMEOUT_S = 60
HTTP_MAX_RETRIES = 5
HTTP_BACKOFF_S = 1.0
ARCHIVE_WORKERS = 6
REST_PACING_S = 0.25

METRICS_COLUMNS = [
    "sum_open_interest",
    "sum_open_interest_value",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "sum_taker_long_short_vol_ratio",
]
KLINES_RAW_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
]
KLINES_KEEP = ["open_time", "open", "high", "low", "close", "volume", "quote_volume", "count"]
COINMETRICS_METRICS = [
    "AdrActCnt",
    "TxCnt",
    "TxTfrCnt",
    "CapMVRVCur",
    "CapMrktCurUSD",
    "FlowInExUSD",
    "FlowOutExUSD",
    "SplyExNtv",
    "HashRate",
    "FeeTotNtv",
    "IssTotNtv",
    "PriceUSD",
    "volume_reported_spot_usd_1d",
    "SplyCur",
]
FRED_SERIES = ["DTB3", "DGS3MO", "SOFR", "DTWEXBGS", "SP500"]
DVOL_MAX_POINTS = 1000  # limit Deribit na jedno zapytanie
COINBASE_MAX_CANDLES = 300  # limit Coinbase Exchange na jedno zapytanie
DAY_MS = 86_400_000
MICROSECOND_THRESHOLD = 10**14  # ms sięgają ~10^12–10^13; µs to ~10^15


# --------------------------------------------------------------------------------------
# Warstwa sieciowa (cienka; wszystko poniżej jest czyste)
# --------------------------------------------------------------------------------------


def http_get(
    url: str,
    timeout: float = HTTP_TIMEOUT_S,
    max_retries: int = HTTP_MAX_RETRIES,
    backoff_s: float = HTTP_BACKOFF_S,
) -> bytes:
    """GET z ponawianiem na błędach sieci / 5xx / 429 (backoff wykładniczy). 4xx inne → od razu."""
    last: Exception | None = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        wait = backoff_s * (2**attempt)
        print(
            f"[external] błąd sieci (próba {attempt + 1}/{max_retries}): {last!r} — czekam {wait:.0f}s"
        )
        time.sleep(wait)
    assert last is not None
    raise last


def _fetch_text(url: str) -> str:
    return http_get(url).decode("utf-8")


# --------------------------------------------------------------------------------------
# Listing archiwum S3 (paginacja markerem) — czyste względem `fetch`
# --------------------------------------------------------------------------------------


def s3_list(prefix: str, fetch=None) -> tuple[list[str], list[str]]:
    """
    Wszystkie klucze `.zip` i podkatalogi (CommonPrefixes) pod `prefix` (delimiter `/`).

    `fetch(url) -> str` podmienialne w testach. Paginacja: `marker` = ostatni klucz strony.
    """
    fetch = fetch or _fetch_text
    keys: list[str] = []
    prefixes: list[str] = []
    marker = ""
    while True:
        url = f"{ARCHIVE_LIST_URL}?delimiter=/&prefix={prefix}&max-keys=1000"
        if marker:
            url += f"&marker={marker}"
        xml = fetch(url)
        page_keys = re.findall(r"<Key>([^<]+)</Key>", xml)
        prefixes.extend(re.findall(r"<Prefix>([^<]+/)</Prefix>", xml))
        keys.extend(page_keys)
        if "<IsTruncated>true</IsTruncated>" in xml and page_keys:
            marker = page_keys[-1]
        else:
            break
    zips = sorted({k for k in keys if k.endswith(".zip")})
    subdirs = sorted({p for p in prefixes if p != prefix and p.startswith(prefix)})
    return zips, subdirs


def read_zip_csv(blob: bytes) -> str:
    """Pierwszy plik z archiwum zip jako tekst (archiwum Binance: jeden CSV na zip)."""
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise ValueError(f"oczekiwano jednego pliku w zip, jest {len(names)}: {names}")
        return zf.read(names[0]).decode("utf-8")


# --------------------------------------------------------------------------------------
# Parsery (czyste funkcje)
# --------------------------------------------------------------------------------------


def parse_metrics_csv(text: str) -> pd.DataFrame:
    """
    `futures/um/daily/metrics/<SYMBOL>/<SYMBOL>-metrics-YYYY-MM-DD.csv` → DataFrame.

    Nagłówek obowiązkowy; wymagane kolumny METRICS_COLUMNS + `create_time`. Pierwsze pliki
    archiwum (2020-09) mają zdublowane wiersze — duplikaty znacznika: zostaje OSTATNI.
    Returns: timestamp (UTC) + METRICS_COLUMNS (float), rosnąco.
    """
    df = pd.read_csv(io.StringIO(text))
    missing = {"create_time", *METRICS_COLUMNS} - set(df.columns)
    if missing:
        raise ValueError(f"metrics: brak kolumn {sorted(missing)}; są {list(df.columns)}")
    out = pd.DataFrame({"timestamp": pd.to_datetime(df["create_time"], utc=True)})
    for col in METRICS_COLUMNS:
        out[col] = pd.to_numeric(df[col], errors="raise").astype(float)
    return (
        out.drop_duplicates("timestamp", keep="last")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def _normalize_epoch_ms(values: pd.Series) -> pd.Series:
    """Znaczniki w ms albo µs (archiwum Binance od 2025 miewa µs) → ms."""
    v = pd.to_numeric(values, errors="raise").astype("int64")
    return v.where(v < MICROSECOND_THRESHOLD, v // 1000)


def parse_klines_csv(text: str) -> pd.DataFrame:
    """
    CSV świec z archiwum Binance (12 kolumn, nagłówek opcjonalny) → KLINES_KEEP.

    Returns: open_time (UTC), open, high, low, close, volume, quote_volume (float), count (int);
    rosnąco, bez duplikatów `open_time`.
    """
    first = text.split("\n", 1)[0]
    has_header = first.split(",")[0].strip() == "open_time"
    df = pd.read_csv(io.StringIO(text), header=0 if has_header else None)
    if df.shape[1] != len(KLINES_RAW_COLUMNS):
        raise ValueError(f"klines: oczekiwano {len(KLINES_RAW_COLUMNS)} kolumn, jest {df.shape[1]}")
    df.columns = KLINES_RAW_COLUMNS
    out = pd.DataFrame(
        {"open_time": pd.to_datetime(_normalize_epoch_ms(df["open_time"]), unit="ms", utc=True)}
    )
    for col in ("open", "high", "low", "close", "volume", "quote_volume"):
        out[col] = pd.to_numeric(df[col], errors="raise").astype(float)
    out["count"] = pd.to_numeric(df["count"], errors="raise").astype("int64")
    return out.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def parse_funding_records(records: list[dict]) -> pd.DataFrame:
    """REST `fundingRate` (dapi/fapi): [{fundingTime, fundingRate, ...}] → timestamp, funding_rate."""
    if not records:
        return pd.DataFrame(
            {
                "timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
                "funding_rate": pd.Series(dtype=float),
            }
        )
    for r in records:
        if "fundingTime" not in r or "fundingRate" not in r:
            raise ValueError(f"funding: rekord bez fundingTime/fundingRate: {r}")
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [int(r["fundingTime"]) for r in records], unit="ms", utc=True
            ),
            "funding_rate": [float(r["fundingRate"]) for r in records],
        }
    )
    return df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)


def parse_dvol(data: list[list]) -> pd.DataFrame:
    """Deribit `get_volatility_index_data` → date (UTC, 00:00), open, high, low, close (float)."""
    if any(len(row) != 5 for row in data):
        raise ValueError("dvol: oczekiwano wierszy [ts, open, high, low, close]")
    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close"])
    out = pd.DataFrame({"date": pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)})
    for col in ("open", "high", "low", "close"):
        out[col] = df[col].astype(float)
    return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def parse_coinmetrics(rows: list[dict], metrics: list[str]) -> pd.DataFrame:
    """CoinMetrics `timeseries/asset-metrics` (data: [{time, <metric>: str|None}]) → date + metryki (float)."""
    if not rows:
        return pd.DataFrame({"date": pd.Series(dtype="datetime64[ns, UTC]")})
    df = pd.DataFrame(rows)
    missing = {"time", *metrics} - set(df.columns)
    if missing:
        raise ValueError(f"coinmetrics: brak kolumn {sorted(missing)}")
    out = pd.DataFrame({"date": pd.to_datetime(df["time"], utc=True)})
    for m in metrics:
        out[m] = pd.to_numeric(df[m], errors="raise").astype(float)
    return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def parse_fng(data: list[dict]) -> pd.DataFrame:
    """alternative.me Fear & Greed (data: [{value, value_classification, timestamp(s)}]) → date, value, label."""
    if not data:
        return pd.DataFrame({"date": pd.Series(dtype="datetime64[ns, UTC]")})
    for r in data:
        if "value" not in r or "timestamp" not in r:
            raise ValueError(f"fng: rekord bez value/timestamp: {r}")
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([int(r["timestamp"]) for r in data], unit="s", utc=True),
            "value": [float(r["value"]) for r in data],
            "label": [str(r.get("value_classification", "")) for r in data],
        }
    )
    return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def parse_fred_csv(text: str, series: str) -> pd.DataFrame:
    """FRED `fredgraph.csv` (observation_date,<SERIES>; `.` = brak) → date, value (NaN przy braku)."""
    df = pd.read_csv(io.StringIO(text))
    if list(df.columns) != ["observation_date", series]:
        raise ValueError(f"fred: nieoczekiwane kolumny {list(df.columns)} dla {series}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df["observation_date"], utc=True),
            "value": pd.to_numeric(df[series].replace(".", None), errors="coerce"),
        }
    )
    return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def parse_coinbase_candles(rows: list[list]) -> pd.DataFrame:
    """Coinbase Exchange candles ([time(s), low, high, open, close, volume], malejąco) → rosnąco."""
    if any(len(r) != 6 for r in rows):
        raise ValueError("coinbase: oczekiwano wierszy [time, low, high, open, close, volume]")
    df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"])
    out = pd.DataFrame(
        {"open_time": pd.to_datetime(df["time"].astype("int64"), unit="s", utc=True)}
    )
    for col in ("open", "high", "low", "close", "volume"):
        out[col] = df[col].astype(float)
    return out.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def date_chunks(start: dt.date, end: dt.date, max_days: int) -> list[tuple[dt.date, dt.date]]:
    """
    Podział `[start, end]` (końce włącznie) na kolejne przedziały ≤ max_days dni, bez nakładania
    i bez dziur. `start > end` → []. `max_days ≥ 1`.
    """
    if max_days < 1:
        raise ValueError("max_days musi być ≥ 1")
    out: list[tuple[dt.date, dt.date]] = []
    cur = start
    while cur <= end:
        stop = min(cur + dt.timedelta(days=max_days - 1), end)
        out.append((cur, stop))
        cur = stop + dt.timedelta(days=1)
    return out


def contract_expiry(contract: str) -> pd.Timestamp:
    """`BTCUSDT_220325` → 2022-03-25 (UTC). Suffix YYMMDD po ostatnim `_`."""
    m = re.fullmatch(r"[A-Z0-9]+_(\d{6})", contract)
    if not m:
        raise ValueError(f"nie kontrakt datowany: {contract}")
    return pd.Timestamp(dt.datetime.strptime(m.group(1), "%y%m%d"), tz="UTC")


# --------------------------------------------------------------------------------------
# Zapis (idempotentny)
# --------------------------------------------------------------------------------------


def target_path(out_dir: str | Path, name: str) -> Path:
    return Path(out_dir) / f"{name}.parquet"


def save_parquet(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def _skip_existing(path: Path, force: bool) -> bool:
    if path.exists() and not force:
        print(f"[external] {path.name}: istnieje — pomijam (użyj --force, by nadpisać)")
        return True
    return False


# --------------------------------------------------------------------------------------
# Pobieranie per źródło
# --------------------------------------------------------------------------------------


def fetch_binance_metrics(
    symbol: str, out_dir: str | Path, force: bool = False, workers: int = ARCHIVE_WORKERS
) -> Path | None:
    """Wszystkie dzienne pliki `metrics` symbolu → jeden parquet (5 min, od pierwszego pliku)."""
    path = target_path(out_dir, f"binance_metrics_{symbol}_5m")
    if _skip_existing(path, force):
        return None
    keys, _ = s3_list(f"data/futures/um/daily/metrics/{symbol}/")
    if not keys:
        raise ValueError(f"metrics: brak plików dla {symbol}")
    print(
        f"[external] metrics {symbol}: {len(keys)} plików dziennych ({keys[0][-14:-4]} → {keys[-1][-14:-4]})"
    )

    def one(key: str) -> pd.DataFrame:
        return parse_metrics_csv(read_zip_csv(http_get(ARCHIVE_FILE_URL + key)))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(one, keys))
    df = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("timestamp", keep="last")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    return save_parquet(df, path)


def fetch_dated_contracts(
    pair: str,
    interval: str,
    out_dir: str | Path,
    force: bool = False,
    workers: int = ARCHIVE_WORKERS,
) -> Path | None:
    """Świece wszystkich kontraktów datowanych `<pair>_<YYMMDD>` (USDS-M) → jeden parquet."""
    path = target_path(out_dir, f"binance_um_dated_{pair}_{interval}")
    if _skip_existing(path, force):
        return None
    _, subdirs = s3_list(f"data/futures/um/monthly/klines/{pair}_")
    contracts = [s.rstrip("/").split("/")[-1] for s in subdirs]
    contracts = [c for c in contracts if re.fullmatch(rf"{pair}_\d{{6}}", c)]
    if not contracts:
        raise ValueError(f"dated: brak kontraktów dla {pair}")
    print(
        f"[external] dated {pair} {interval}: {len(contracts)} kontraktów ({contracts[0]} → {contracts[-1]})"
    )
    jobs: list[tuple[str, str]] = []
    for c in contracts:
        keys, _ = s3_list(f"data/futures/um/monthly/klines/{c}/{interval}/")
        jobs.extend((c, k) for k in keys)

    def one(job: tuple[str, str]) -> pd.DataFrame:
        c, key = job
        df = parse_klines_csv(read_zip_csv(http_get(ARCHIVE_FILE_URL + key)))
        df.insert(0, "contract", c)
        df.insert(1, "expiry", contract_expiry(c))
        return df

    with ThreadPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(one, jobs))
    df = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(["contract", "open_time"])
        .sort_values(["expiry", "open_time"])
        .reset_index(drop=True)
    )
    return save_parquet(df, path)


def fetch_coinm_funding(
    symbol: str,
    start: str,
    out_dir: str | Path,
    force: bool = False,
    pacing_s: float = REST_PACING_S,
) -> Path | None:
    """Historia funding COIN-M (`dapi/v1/fundingRate`, 1000 na stronę) od `start` do dziś."""
    path = target_path(out_dir, f"binance_cm_funding_{symbol}")
    if _skip_existing(path, force):
        return None
    since = int(pd.Timestamp(start, tz="UTC").value // 1_000_000)
    end_ms = int(pd.Timestamp.now(tz="UTC").value // 1_000_000)
    records: list[dict] = []
    while since < end_ms:
        q = urllib.parse.urlencode(
            {"symbol": symbol, "startTime": since, "endTime": end_ms, "limit": 1000}
        )
        page = json.loads(http_get(f"{DAPI_FUNDING_URL}?{q}"))
        if not page:
            break
        records.extend(page)
        last_ts = int(page[-1]["fundingTime"])
        if last_ts < since or len(page) < 1000:
            break
        since = last_ts + 1
        time.sleep(pacing_s)
    df = parse_funding_records(records)
    print(f"[external] coinm funding {symbol}: {len(df)} rekordów")
    return save_parquet(df, path)


def fetch_dvol(currency: str, start: str, out_dir: str | Path, force: bool = False) -> Path | None:
    """DVOL dzienny (Deribit) od `start` do dziś, w kawałkach ≤ DVOL_MAX_POINTS dni."""
    path = target_path(out_dir, f"deribit_dvol_{currency}_1d")
    if _skip_existing(path, force):
        return None
    frames = []
    for a, b in date_chunks(pd.Timestamp(start).date(), dt.date.today(), DVOL_MAX_POINTS - 50):
        q = urllib.parse.urlencode(
            {
                "currency": currency,
                "resolution": "1D",
                "start_timestamp": int(pd.Timestamp(a, tz="UTC").value // 1_000_000),
                "end_timestamp": int(pd.Timestamp(b, tz="UTC").value // 1_000_000) + DAY_MS - 1,
            }
        )
        res = json.loads(http_get(f"{DERIBIT_DVOL_URL}?{q}"))
        if "result" not in res or "data" not in res["result"]:
            raise ValueError(f"dvol: nieoczekiwana odpowiedź {str(res)[:200]}")
        frames.append(parse_dvol(res["result"]["data"]))
        time.sleep(REST_PACING_S)
    df = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    print(f"[external] dvol {currency}: {len(df)} dni")
    return save_parquet(df, path)


def fetch_coinmetrics(
    asset: str, metrics: list[str], start: str, out_dir: str | Path, force: bool = False
) -> Path | None:
    """On-chain 1d (CoinMetrics community) od `start`; paginacja `next_page_url`."""
    path = target_path(out_dir, f"coinmetrics_{asset}_1d")
    if _skip_existing(path, force):
        return None
    q = urllib.parse.urlencode(
        {
            "assets": asset,
            "metrics": ",".join(metrics),
            "frequency": "1d",
            "start_time": start,
            "page_size": 10000,
        }
    )
    url: str | None = f"{COINMETRICS_URL}?{q}"
    rows: list[dict] = []
    while url:
        res = json.loads(http_get(url))
        if "data" not in res:
            raise ValueError(f"coinmetrics: nieoczekiwana odpowiedź {str(res)[:200]}")
        rows.extend(res["data"])
        url = res.get("next_page_url")
        time.sleep(REST_PACING_S)
    df = parse_coinmetrics(rows, metrics)
    print(f"[external] coinmetrics {asset}: {len(df)} dni, {len(metrics)} metryk")
    return save_parquet(df, path)


def fetch_fng(out_dir: str | Path, force: bool = False) -> Path | None:
    """Fear & Greed (alternative.me), cała historia."""
    path = target_path(out_dir, "alternative_fng_1d")
    if _skip_existing(path, force):
        return None
    res = json.loads(http_get(FNG_URL))
    if "data" not in res:
        raise ValueError(f"fng: nieoczekiwana odpowiedź {str(res)[:200]}")
    df = parse_fng(res["data"])
    print(f"[external] fng: {len(df)} dni")
    return save_parquet(df, path)


def fetch_fred(series: str, start: str, out_dir: str | Path, force: bool = False) -> Path | None:
    """Jedna seria FRED (CSV bez klucza) od `start`."""
    path = target_path(out_dir, f"fred_{series}_1d")
    if _skip_existing(path, force):
        return None
    q = urllib.parse.urlencode({"id": series, "cosd": start})
    df = parse_fred_csv(_fetch_text(f"{FRED_URL}?{q}"), series)
    print(
        f"[external] fred {series}: {len(df)} obserwacji ({int(df['value'].isna().sum())} braków)"
    )
    return save_parquet(df, path)


def fetch_coinbase_daily(
    product: str,
    start: str,
    out_dir: str | Path,
    force: bool = False,
    pacing_s: float = REST_PACING_S,
) -> Path | None:
    """Świece dzienne Coinbase Exchange od `start` do dziś (≤ 300 na zapytanie)."""
    path = target_path(out_dir, f"coinbase_{product}_1d")
    if _skip_existing(path, force):
        return None
    frames = []
    for a, b in date_chunks(pd.Timestamp(start).date(), dt.date.today(), COINBASE_MAX_CANDLES - 1):
        q = urllib.parse.urlencode(
            {
                "granularity": 86400,
                "start": f"{a.isoformat()}T00:00:00Z",
                "end": f"{b.isoformat()}T00:00:00Z",
            }
        )
        rows = json.loads(http_get(COINBASE_CANDLES_URL.format(product=product) + "?" + q))
        if not isinstance(rows, list):
            raise ValueError(f"coinbase: nieoczekiwana odpowiedź {str(rows)[:200]}")
        frames.append(parse_coinbase_candles(rows))
        time.sleep(pacing_s)
    df = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("open_time")
        .sort_values("open_time")
        .reset_index(drop=True)
    )
    print(f"[external] coinbase {product}: {len(df)} dni")
    return save_parquet(df, path)


# --------------------------------------------------------------------------------------
# Orkiestracja
# --------------------------------------------------------------------------------------

SOURCES = ("metrics", "dated", "coinm_funding", "dvol", "coinmetrics", "fng", "fred", "coinbase")


def describe(path: Path) -> str:
    df = pd.read_parquet(path)
    tcol = next((c for c in ("timestamp", "open_time", "date") if c in df.columns), None)
    span = f"{df[tcol].min()} → {df[tcol].max()}" if tcol is not None and len(df) else "-"
    return f"{path.name}: {len(df)} wierszy, {df.shape[1]} kolumn, {span}"


def run(
    out_dir: str | Path = DEFAULT_OUT_DIR,
    only=None,
    force: bool = False,
    start: str = DEFAULT_START,
) -> dict:
    """Pobiera wybrane źródła; błąd jednego nie przerywa pozostałych. Zwraca {źródło: ścieżka|błąd}."""
    only = set(only) if only else set(SOURCES)
    unknown = only - set(SOURCES)
    if unknown:
        raise ValueError(f"nieznane źródła: {sorted(unknown)}; dostępne: {SOURCES}")
    plan = {
        "metrics": lambda: [fetch_binance_metrics("BTCUSDT", out_dir, force)],
        "dated": lambda: [fetch_dated_contracts("BTCUSDT", "8h", out_dir, force)],
        "coinm_funding": lambda: [fetch_coinm_funding("BTCUSD_PERP", start, out_dir, force)],
        "dvol": lambda: [fetch_dvol(c, start, out_dir, force) for c in ("BTC", "ETH")],
        "coinmetrics": lambda: [
            fetch_coinmetrics("btc", COINMETRICS_METRICS, start, out_dir, force)
        ],
        "fng": lambda: [fetch_fng(out_dir, force)],
        "fred": lambda: [fetch_fred(s, start, out_dir, force) for s in FRED_SERIES],
        "coinbase": lambda: [fetch_coinbase_daily("BTC-USD", start, out_dir, force)],
    }
    results: dict = {}
    for name in SOURCES:
        if name not in only:
            continue
        t0 = time.time()
        try:
            paths = [p for p in plan[name]() if p is not None]
            results[name] = paths
            for p in paths:
                print(f"[external] OK  {describe(p)}  ({time.time() - t0:.0f}s)")
        except Exception as e:  # noqa: BLE001 — jeden błąd nie ma zatrzymać reszty źródeł
            results[name] = e
            print(f"[external] BŁĄD {name}: {e!r}")
    return results


def main(argv: list[str]) -> int:
    out_dir = DEFAULT_OUT_DIR
    only = None
    force = False
    it = iter(argv)
    for a in it:
        if a == "--force":
            force = True
        elif a == "--only":
            only = next(it).split(",")
        else:
            out_dir = a
    results = run(out_dir, only=only, force=force)
    failed = [k for k, v in results.items() if isinstance(v, Exception)]
    print(
        f"[external] gotowe: {len(results) - len(failed)} źródeł OK, {len(failed)} z błędem {failed}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
