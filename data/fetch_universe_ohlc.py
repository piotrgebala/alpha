"""
fetch_universe_ohlc.py — dzienne OHLC (z maksimami i minimami) członków koszyka top-20 po obrocie
(runda LQ1: likwidacje przy dźwigni 3× na izolowanym depozycie wymagają dziennych high/low, a cache
uniwersum P2 ma tylko zamknięcia). Źródło: miesięczne pliki `klines/1d` archiwum
`data.binance.vision` (wycofane kontrakty włącznie). Pobierane są tylko miesiące członkostwa
(plus miesiąc wcześniejszy — rozbieg).

    PYTHONUTF8=1 py -m data.fetch_universe_ohlc     # → data/raw/universe_ohlc/ohlc_1d.parquet

Czysta funkcja `membership_months` testowana bez sieci (`tests/test_fetch_universe_ohlc.py`).
"""

from __future__ import annotations

import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from data.fetch_external import ARCHIVE_FILE_URL, http_get, parse_klines_csv, read_zip_csv

OUT = "data/raw/universe_ohlc/ohlc_1d.parquet"
FIRST_MONTH = "2021-02-01"
END = "2026-07-01"
WORKERS = 8


def membership_months(members: dict[pd.Timestamp, list[str]]) -> set[tuple[str, str]]:
    """(symbol, 'YYYY-MM') potrzebne: miesiąc członkostwa i miesiąc przed nim."""
    out = set()
    for m, syms in members.items():
        prev = (m - pd.offsets.MonthBegin(1)).strftime("%Y-%m")
        for s in syms:
            out.add((s, m.strftime("%Y-%m")))
            out.add((s, prev))
    return out


def _one(job: tuple[str, str]) -> pd.DataFrame | None:
    sym, ym = job
    q = urllib.parse.quote(sym, safe="")
    path = f"data/futures/um/monthly/klines/{q}/1d/{q}-1d-{ym}.zip"
    try:
        df = parse_klines_csv(read_zip_csv(http_get(ARCHIVE_FILE_URL + path)))
    except Exception as e:  # 404 = brak pliku (symbol nie notowany w miesiącu)
        if "404" in str(e):
            return None
        raise
    df.insert(0, "symbol", sym)
    return df[["symbol", "open_time", "open", "high", "low", "close"]]


def run(out: str = OUT) -> None:
    from backtest.rebalance_premium import load_universe, monthly_members

    _, volume = load_universe("data/raw/universe")
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    jobs = sorted(membership_months(monthly_members(volume, months)))
    print(f"[ohlc] par (symbol, miesiąc): {len(jobs)}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        parts = [p for p in ex.map(_one, jobs) if p is not None]
    df = pd.concat(parts, ignore_index=True).drop_duplicates(["symbol", "open_time"])
    df = df.sort_values(["symbol", "open_time"]).reset_index(drop=True)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(
        f"[ohlc] zapisano {len(df)} wierszy, {df['symbol'].nunique()} symboli; brak pliku: {len(jobs) - len(parts)}"
    )


if __name__ == "__main__":
    run(*sys.argv[1:])
