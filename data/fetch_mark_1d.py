"""
fetch_mark_1d.py — dzienne świece CENY MARK (markPriceKlines 1d) członków koszyka top-20 po obrocie
(zadanie 017, runda LP1). Źródło: publiczne archiwum `data.binance.vision`
(`data/futures/um/monthly/markPriceKlines/<SYM>/1d/`), bez klucza API. Te same pary (symbol, miesiąc)
co `data/fetch_universe_ohlc.py` (miesiące członkostwa + miesiąc wcześniej), więc szereg mark pokrywa
te same dni co cena ostatnia w `universe_ohlc_full`.

    PYTHONUTF8=1 py -m data.fetch_mark_1d <universe_dir> [out]
    # domyślnie: universe_dir=data/raw/universe_full, out=data/raw/mark_1d/mark_1d.parquet

Nie jest w łańcuchu importów dziennika. Kolumny volume/quote_volume w archiwum mark są zerami —
zapisujemy tylko OHLC.
"""

from __future__ import annotations

import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from data.fetch_external import ARCHIVE_FILE_URL, http_get, parse_klines_csv, read_zip_csv
from data.fetch_universe_ohlc import END, FIRST_MONTH, membership_months

OUT = "data/raw/mark_1d/mark_1d.parquet"
WORKERS = 8


def mark_path(sym: str, ym: str) -> str:
    q = urllib.parse.quote(sym, safe="")
    return f"data/futures/um/monthly/markPriceKlines/{q}/1d/{q}-1d-{ym}.zip"


def _one(job: tuple[str, str]) -> pd.DataFrame | None:
    sym, ym = job
    try:
        df = parse_klines_csv(read_zip_csv(http_get(ARCHIVE_FILE_URL + mark_path(sym, ym))))
    except Exception as e:  # 404 = brak pliku (symbol bez archiwum mark w tym miesiącu)
        if "404" in str(e):
            return None
        raise
    df.insert(0, "symbol", sym)
    return df[["symbol", "open_time", "open", "high", "low", "close"]]


def run(universe_dir: str = "data/raw/universe_full", out: str = OUT) -> None:
    from backtest.rebalance_premium import load_universe, monthly_members

    _, volume = load_universe(universe_dir)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    jobs = sorted(membership_months(monthly_members(volume, months)))
    print(f"[mark] par (symbol, miesiąc): {len(jobs)}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        results = list(ex.map(_one, jobs))
    missing = [j for j, r in zip(jobs, results, strict=True) if r is None]
    parts = [r for r in results if r is not None]
    df = pd.concat(parts, ignore_index=True).drop_duplicates(["symbol", "open_time"])
    df = df.sort_values(["symbol", "open_time"]).reset_index(drop=True)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(
        f"[mark] zapisano {len(df)} wierszy, {df['symbol'].nunique()} symboli; brak pliku: {len(missing)}"
    )
    for sym, ym in missing:
        print(f"[mark] BRAK {sym} {ym}")


if __name__ == "__main__":
    run(*sys.argv[1:])
