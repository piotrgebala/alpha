"""
complete_universe.py — uzupełnienie uniwersum (runda RU1) szybciej niż `data.fetch_universe`:
świece 1d dla KAŻDEGO brakującego symbolu (potrzebne do rankingu obrotu), funding tylko dla tych,
którzy choć raz weszli do koszyka top-20 (tylko ich pozycje płacą funding). Te same funkcje
pobierające i ten sam format plików co `data.fetch_universe` (P2); te same daty.

Pozostali symbole bez pliku `*_funding.parquet` nigdy nie są trzymani, więc ich funding nie wchodzi
do żadnego wyniku (`daily_funding_panel` → 0 tylko dla nieobecnych kolumn).

    PYTHONUTF8=1 py -m data.complete_universe data/raw/universe_full
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ccxt
import pandas as pd

from data.fetch_universe import (
    _empty_klines,
    cache_paths,
    fetch_funding_raw,
    fetch_klines_1d_raw,
    list_archive_symbols,
    list_tradifi_ids,
    select_universe,
)

START, END = "2020-01-01T00:00:00Z", "2026-07-01T00:00:00Z"
KLINE_THREADS, KLINE_PACING_S = 2, 0.5  # ~4 zapytania/s × waga 10 < 2400/min
FUNDING_PACING_S = 0.7


def _ms(ts: str) -> int:
    return int(pd.Timestamp(ts).value // 1_000_000)


def _klines_job(sym: str, cache_dir: Path) -> tuple[str, int]:
    ex = ccxt.binanceusdm({"enableRateLimit": False})
    _, k_path = cache_paths(cache_dir, sym)
    try:
        kl = fetch_klines_1d_raw(ex, sym, _ms(START), _ms(END), KLINE_PACING_S)
    except ccxt.ExchangeError:
        kl = _empty_klines()
    kl.to_parquet(k_path, index=False)
    time.sleep(KLINE_PACING_S)
    return sym, len(kl)


def run(cache_dir: str, top_n: int = 20) -> None:
    from backtest.rebalance_premium import load_universe, monthly_members

    d = Path(cache_dir)
    ex = ccxt.binanceusdm({"enableRateLimit": False})
    universe = select_universe(list_archive_symbols(), list_tradifi_ids(ex))
    missing = [s for s in universe if not cache_paths(d, s)[1].exists()]
    print(f"[uzup] uniwersum {len(universe)}, brak świec: {len(missing)}", flush=True)
    with ThreadPoolExecutor(KLINE_THREADS) as pool:
        for i, _ in enumerate(pool.map(lambda s: _klines_job(s, d), missing), 1):
            if i % 50 == 0:
                print(f"[uzup] świece {i}/{len(missing)}", flush=True)
    _, volume = load_universe(d)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range("2021-02-01", END[:10], freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, months, top_n=top_n)
    need = sorted({s for v in members.values() for s in v} | {"BTCUSDT"})
    todo = [s for s in need if not cache_paths(d, s)[0].exists()]
    print(
        f"[uzup] członkowie top-{top_n} 2021–2026: {len(need)}, brak fundingu: {len(todo)}",
        flush=True,
    )
    for sym in todo:
        fu = fetch_funding_raw(ex, sym, _ms(START), _ms(END), FUNDING_PACING_S)
        fu.to_parquet(cache_paths(d, sym)[0], index=False)
        time.sleep(FUNDING_PACING_S)
    print(
        f"[uzup] koniec: świece {len(list(d.glob('*_1d.parquet')))}, funding {len(list(d.glob('*_funding.parquet')))}",
        flush=True,
    )


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20)
