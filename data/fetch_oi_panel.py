"""
fetch_oi_panel.py — dzienny panel otwartych pozycji (open interest, OI) dla członków koszyka
top-20 po obrocie (runda TL1 — tłok przekrojowy), z publicznego archiwum
`data.binance.vision/data/futures/um/daily/metrics/<SYM>/` (5 min; dla altcoinów od 2021-12).

Wartość dnia t = OSTATNI odczyt pliku dnia t (≈ 23:55 UTC), czyli stan znany przy zamknięciu
świecy dziennej t (point-in-time, bez zaglądania w dzień t+1). Pobierane są tylko dni, w których
symbol jest członkiem koszyka, plus `LOOKBACK_PAD` dni rozbiegu przed miesiącem.

    PYTHONUTF8=1 py -m data.fetch_oi_panel            # → data/raw/oi_panel/oi_daily.parquet

Czysta funkcja `last_snapshot` testowana bez sieci (`tests/test_fetch_oi_panel.py`).
"""

from __future__ import annotations

import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from data.fetch_external import ARCHIVE_FILE_URL, http_get, parse_metrics_csv, read_zip_csv

OUT = "data/raw/oi_panel/oi_daily.parquet"
FIRST_MONTH = "2021-12-01"
END = "2026-07-01"
LOOKBACK_PAD = 10
WORKERS = 8


def last_snapshot(metrics: pd.DataFrame) -> dict | None:
    """Ostatni wiersz dnia z dodatnim OI → {timestamp, oi, oi_value}; None, gdy brak."""
    ok = metrics[metrics["sum_open_interest"] > 0]
    if ok.empty:
        return None
    r = ok.sort_values("timestamp").iloc[-1]
    return {
        "timestamp": r["timestamp"],
        "oi": float(r["sum_open_interest"]),
        "oi_value": float(r["sum_open_interest_value"]),
    }


def needed_days(members: dict[pd.Timestamp, list[str]]) -> set[tuple[str, pd.Timestamp]]:
    """(symbol, dzień) potrzebne: dni miesięcy członkostwa + rozbieg `LOOKBACK_PAD` dni."""
    months = sorted(members)
    out = set()
    for i, m in enumerate(months):
        nxt = months[i + 1] if i + 1 < len(months) else m + pd.offsets.MonthBegin(1)
        days = pd.date_range(
            m - pd.Timedelta(days=LOOKBACK_PAD), nxt - pd.Timedelta(days=1), freq="D"
        )
        for s in members[m]:
            out.update((s, d) for d in days)
    return out


def _one(job: tuple[str, pd.Timestamp]) -> dict | None:
    sym, day = job
    q = urllib.parse.quote(sym, safe="")
    path = f"data/futures/um/daily/metrics/{q}/{q}-metrics-{day.date()}.zip"
    try:
        snap = last_snapshot(parse_metrics_csv(read_zip_csv(http_get(ARCHIVE_FILE_URL + path))))
    except Exception as e:  # 404 = brak pliku (symbol nie notowany / przed startem archiwum)
        if "404" in str(e):
            return None
        raise
    return {"symbol": sym, "date": day, **snap} if snap else None


def missing_jobs(
    jobs: list[tuple[str, pd.Timestamp]], existing: pd.DataFrame | None
) -> list[tuple[str, pd.Timestamp]]:
    """Pary (symbol, dzień) bez wiersza w istniejącym panelu — tylko je trzeba pobrać."""
    if existing is None or existing.empty:
        return list(jobs)
    have = set(zip(existing["symbol"], pd.to_datetime(existing["date"], utc=True), strict=True))
    return [j for j in jobs if (j[0], pd.Timestamp(j[1])) not in have]


def run(out: str = OUT, universe_dir: str = "data/raw/universe", reuse: str | None = None) -> None:
    """
    Panel OI dla członków koszyka z `universe_dir`. `reuse` = istniejący panel, którego wiersze
    są brane bez pobierania (RU4: pełne uniwersum na bazie panelu z obciętego).
    """
    from backtest.rebalance_premium import load_universe, monthly_members

    _, volume = load_universe(universe_dir)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, months)
    jobs = sorted(needed_days(members))
    old = pd.read_parquet(reuse) if reuse else None
    todo = missing_jobs(jobs, old)
    print(
        f"[oi] miesięcy {len(months)}, par (symbol, dzień): {len(jobs)}, do pobrania: {len(todo)}",
        flush=True,
    )
    rows = []
    if old is not None:
        keep = set(jobs)
        old_d = pd.to_datetime(old["date"], utc=True)
        mask = [(s, d) in keep for s, d in zip(old["symbol"], old_d, strict=True)]
        rows = old[mask].to_dict("records")
    jobs = todo
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, r in enumerate(ex.map(_one, jobs), 1):
            if r:
                rows.append(r)
            if i % 2000 == 0:
                print(f"[oi] {i}/{len(jobs)}", flush=True)
    df = pd.DataFrame(rows).sort_values(["symbol", "date"]).reset_index(drop=True)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(
        f"[oi] zapisano {len(df)} wierszy, {df['symbol'].nunique()} symboli; pobieranych: {len(jobs)}"
    )


if __name__ == "__main__":
    run(*sys.argv[1:])
