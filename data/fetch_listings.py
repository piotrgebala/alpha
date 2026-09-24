"""
fetch_listings.py — kalendarz NOWYCH kontraktów USDT-M Binance i dane ich pierwszych tygodni
(runda NL1, rodzina G2 katalogu: zdarzenie „listing”), wyłącznie z publicznego archiwum
`data.binance.vision` (zawiera też kontrakty WYCOFANE → bez błędu przeżywalności) plus
`fapi/v1/exchangeInfo` do klasyfikacji (krypto / TradFi / indeks).

Data listingu d0 = dzień pierwszego DZIENNEGO pliku świec 1d w archiwum (point-in-time: plik
istnieje od pierwszego dnia notowań; nie data ogłoszenia). Okno zdarzenia: świece 1d i funding
z miesięcznych plików archiwum pokrywających [d0, d0 + WINDOW_DAYS].

Zapis: `data/raw/listings/{events.csv, klines.parquet, funding.parquet}`.

    PYTHONUTF8=1 py -m data.fetch_listings            # pełne pobranie (idempotentne)

Czyste funkcje (testy bez sieci: `tests/test_fetch_listings.py`): `parse_first_key_date`,
`normalized_base`, `classify_symbol`, `parse_archive_funding_csv`, `window_months`,
`select_events`.
"""

from __future__ import annotations

import io
import json
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from data.fetch_external import (
    ARCHIVE_FILE_URL,
    ARCHIVE_LIST_URL,
    http_get,
    parse_klines_csv,
    read_zip_csv,
)
from data.fetch_universe import STABLE_BASES, list_archive_symbols

OUT_DIR = "data/raw/listings"
DAILY_KLINES_PREFIX = "data/futures/um/daily/klines/"
EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
WINDOW_DAYS = 20  # zapas nad oknem 14 dni (d0+1 … d0+15)
FIRST_DAY_MIN = "2021-01-01"  # zasada 20
INDEX_SYMBOLS = frozenset({"BTCDOMUSDT", "DEFIUSDT", "FOOTBALLUSDT", "BLUEBIRDUSDT"})
QUOTE = "USDT"
WORKERS = 6
_DENOM_PREFIX = re.compile(r"^(1000000|100000|10000|1000|1M)(?=[A-Z])")


def parse_first_key_date(xml: str) -> pd.Timestamp | None:
    """Pierwszy klucz listingu S3 `…/SYM-1d-YYYY-MM-DD.zip` → dzień UTC (None, gdy brak)."""
    m = re.search(r"<Key>[^<]*-1d-(\d{4}-\d{2}-\d{2})\.zip</Key>", xml)
    return pd.Timestamp(m.group(1), tz="UTC") if m else None


def normalized_base(symbol: str) -> str:
    """Baza bez sufiksu USDT i bez prefiksu redenominacji (1000PEPE → PEPE, 1MBABYDOGE → BABYDOGE)."""
    base = symbol[: -len(QUOTE)] if symbol.endswith(QUOTE) else symbol
    return _DENOM_PREFIX.sub("", base)


def classify_symbol(symbol: str, info: dict | None) -> str:
    """
    CRYPTO / TRADIFI / INDEX / STABLE / NOT_USDT. `info` = wpis exchangeInfo albo None (kontrakt
    wycofany, nieobecny w exchangeInfo → traktowany jako krypto: TradFi pojawiło się w 2025 i nie
    było wycofywane w próbie).
    """
    if not symbol.endswith(QUOTE):
        return "NOT_USDT"
    if symbol in INDEX_SYMBOLS:
        return "INDEX"
    if normalized_base(symbol) in STABLE_BASES:
        return "STABLE"
    if info is None:
        return "CRYPTO"
    if info.get("contractType") == "TRADIFI_PERPETUAL":
        return "TRADIFI"
    if info.get("underlyingType") in ("COIN", "PREMARKET"):
        return "CRYPTO"
    return "INDEX" if info.get("underlyingType") == "INDEX" else "TRADIFI"


def parse_archive_funding_csv(text: str) -> pd.DataFrame:
    """CSV `calc_time,funding_interval_hours,last_funding_rate` → timestamp (UTC), funding_rate, interval_h."""
    df = pd.read_csv(io.StringIO(text))
    need = {"calc_time", "funding_interval_hours", "last_funding_rate"}
    if not need.issubset(df.columns):
        raise ValueError(f"funding archiwum: brak kolumn {sorted(need - set(df.columns))}")
    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(df["calc_time"].astype("int64"), unit="ms", utc=True),
            "funding_rate": df["last_funding_rate"].astype(float),
            "interval_h": df["funding_interval_hours"].astype(int),
        }
    )
    return out.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)


def window_months(d0: pd.Timestamp, days: int = WINDOW_DAYS) -> list[str]:
    """Miesiące `YYYY-MM` pokrywające [d0, d0 + days]."""
    months = pd.period_range(
        d0.tz_localize(None), (d0 + pd.Timedelta(days=days)).tz_localize(None), freq="M"
    )
    return [str(p) for p in months]


def select_events(
    first_days: dict[str, pd.Timestamp | None],
    infos: dict[str, dict],
    first_day_min: str = FIRST_DAY_MIN,
    last_day: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Zdarzenia: symbole krypto USDT, d0 ≥ `first_day_min` (i ≤ `last_day`), bez redenominacji —
    symbol, którego znormalizowana baza pojawiła się WCZEŚNIEJ (albo tego samego dnia pod inną
    nazwą, np. PEPE i 1000PEPE), jest wykluczony z powodem. Kolejność i powody jawne w wyniku.
    """
    rows = []
    for sym, d0 in first_days.items():
        cls = classify_symbol(sym, infos.get(sym))
        rows.append({"symbol": sym, "d0": d0, "cls": cls, "base": normalized_base(sym)})
    df = pd.DataFrame(rows).dropna(subset=["d0"]).sort_values(["d0", "symbol"])
    df["reason"] = ""
    df.loc[df["cls"] != "CRYPTO", "reason"] = "klasa:" + df["cls"]
    seen: set[str] = set()
    for i, r in df.iterrows():
        if r["reason"]:
            continue
        if r["base"] in seen:
            df.at[i, "reason"] = "redenominacja/duplikat bazy"
        seen.add(r["base"])
    lo = pd.Timestamp(first_day_min, tz="UTC")
    df.loc[(df["reason"] == "") & (df["d0"] < lo), "reason"] = "przed bazą (zasada 20)"
    if last_day is not None:
        df.loc[(df["reason"] == "") & (df["d0"] > last_day), "reason"] = "okno poza końcem danych"
    df["in_sample"] = df["reason"] == ""
    return df.reset_index(drop=True)


# ------------------------------------------------------------------------------------------
# Sieć (cienka warstwa)
# ------------------------------------------------------------------------------------------


def _q(symbol: str) -> str:
    return urllib.parse.quote(symbol, safe="")


def first_listing_day(symbol: str) -> pd.Timestamp | None:
    prefix = f"{DAILY_KLINES_PREFIX}{_q(symbol)}/1d/"
    xml = http_get(f"{ARCHIVE_LIST_URL}?prefix={prefix}&max-keys=1").decode("utf-8")
    return parse_first_key_date(xml)


def _archive_zip(path: str) -> str | None:
    try:
        return read_zip_csv(http_get(ARCHIVE_FILE_URL + path))
    except Exception as e:  # 404 = brak pliku w miesiącu (kontrakt nie notowany) → None
        if "404" in str(e):
            return None
        raise


def event_data(symbol: str, d0: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Świece 1d i funding z miesięcznych plików archiwum pokrywających okno zdarzenia."""
    k_parts, f_parts = [], []
    for ym in window_months(d0):
        k = _archive_zip(f"data/futures/um/monthly/klines/{_q(symbol)}/1d/{_q(symbol)}-1d-{ym}.zip")
        if k:
            k_parts.append(parse_klines_csv(k))
        f = _archive_zip(
            f"data/futures/um/monthly/fundingRate/{_q(symbol)}/{_q(symbol)}-fundingRate-{ym}.zip"
        )
        if f:
            f_parts.append(parse_archive_funding_csv(f))
    kl = pd.concat(k_parts, ignore_index=True) if k_parts else pd.DataFrame()
    fu = pd.concat(f_parts, ignore_index=True) if f_parts else pd.DataFrame()
    return kl, fu


def run(out_dir: str = OUT_DIR, last_day: str = "2026-06-15") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    syms = [s for s in list_archive_symbols(prefix=DAILY_KLINES_PREFIX) if s.endswith(QUOTE)]
    print(f"[listings] symboli USDT w archiwum dziennym: {len(syms)}")
    with ThreadPoolExecutor(WORKERS) as ex:
        firsts = dict(zip(syms, ex.map(first_listing_day, syms), strict=True))
    infos = {
        s["symbol"]: s for s in json.loads(http_get(EXCHANGE_INFO_URL).decode("utf-8"))["symbols"]
    }
    events = select_events(firsts, infos, last_day=pd.Timestamp(last_day, tz="UTC"))
    events["onboard"] = events["symbol"].map(
        lambda s: (
            pd.Timestamp(infos[s]["onboardDate"], unit="ms", tz="UTC") if s in infos else pd.NaT
        )
    )
    events.to_csv(out / "events.csv", index=False)
    sample = events[events["in_sample"]]
    print(
        f"[listings] zdarzeń w próbie: {len(sample)}; powody wykluczeń: {events['reason'].value_counts().to_dict()}"
    )

    def job(row):
        kl, fu = event_data(row.symbol, row.d0)
        if len(kl):
            kl.insert(0, "symbol", row.symbol)
        if len(fu):
            fu.insert(0, "symbol", row.symbol)
        return kl, fu

    with ThreadPoolExecutor(WORKERS) as ex:
        res = list(ex.map(job, sample.itertuples()))
    kl = pd.concat([r[0] for r in res if len(r[0])], ignore_index=True)
    fu = pd.concat([r[1] for r in res if len(r[1])], ignore_index=True)
    kl.to_parquet(out / "klines.parquet", index=False)
    fu.to_parquet(out / "funding.parquet", index=False)
    print(
        f"[listings] zapisano: świece {len(kl)} ({kl['symbol'].nunique()} symboli), funding {len(fu)} ({fu['symbol'].nunique()} symboli)"
    )


if __name__ == "__main__":
    run(*sys.argv[1:])
