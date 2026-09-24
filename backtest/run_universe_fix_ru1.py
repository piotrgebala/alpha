"""
run_universe_fix_ru1.py — runda RU1: korekta danych. Cache `data/raw/universe` (rundy P2 → SZ1) ma
287 z 685 kontraktów z archiwum (monety A–G + 12 z H–Z: pobranie przerwane w połowie alfabetu),
więc koszyk top-20 był liczony z niepełnego rynku. Uzupełniony cache: `data/raw/universe_full`
(ten sam pobieracz `data.fetch_universe`, te same daty); stary zostaje dla odtwarzalności.

Reguły ZAMROŻONE co do bajtu — skrypt tylko podmienia katalog danych:
- `sklad`  — porównanie składu top-20 (stary vs pełny), miesiąc po miesiącu (bez zwrotów);
- `ts1`    — `run_ts_momentum_ts1.main` z `UNIVERSE_DIR` = pełny (kryterium i H0 jak w TS1)
             + opisowo okres od 2022 (preferencja użytkownika);
- `x1`     — `run_xs_momentum_x1.main([pełny])` + opisowo od 2022;
- `sz1`    — reguły R0/R1/R2 (SZ1) na składowych z pełnego uniwersum (likwidacje z OHLC pełnego).
Pre-rejestracja: `runs/2026-09-24_ru1-pelne-uniwersum/README.md`.

    PYTHONUTF8=1 py -m backtest.run_universe_fix_ru1 sklad|ts1|x1|sz1
"""

from __future__ import annotations

import sys
from collections import Counter

import numpy as np
import pandas as pd

from backtest import run_ts_momentum_ts1 as ts1
from backtest import run_xs_momentum_x1 as x1
from backtest.carry_hedged import summarize_pnl
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.sizing import DAYS_PER_YEAR, apply_rules, summary
from backtest.ts_momentum import portfolio
from backtest.xs_momentum import long_short_returns

OLD = "data/raw/universe"
FULL = "data/raw/universe_full"
OHLC_FULL = "data/raw/universe_ohlc_full/ohlc_1d.parquet"
FROM_2022 = pd.Timestamp("2022-01-01", tz="UTC")
LEV_TS, LEV_CP, MMR = 2.0, 3.0, 0.01
SEP = "=" * 104


def _members(universe_dir: str) -> dict:
    _, volume = load_universe(universe_dir)
    lo, end = pd.Timestamp(ts1.DATA_START, tz="UTC"), pd.Timestamp(ts1.END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(ts1.FIRST_MONTH, ts1.END, freq="MS", tz="UTC") if m < end]
    return monthly_members(volume, months)


def sklad() -> None:
    old, full = _members(OLD), _members(FULL)
    print(SEP)
    print("RU1 — SKŁAD TOP-20: stary cache (A–G + 12) vs pełne uniwersum; bez zwrotów")
    print(SEP)
    diff, missing = [], Counter()
    for m in full:
        miss = sorted(set(full[m]) - set(old[m]))
        diff.append(len(miss))
        missing.update(miss)
        print(f"  {m.date()}: {len(miss):2d}/20 innych; brakowało: {', '.join(miss) or '—'}")
    d = np.array(diff)
    print(
        f"  średnio {d.mean():.1f}/20 miejsc inaczej ({100 * d.mean() / 20:.0f} %), od 2022 {d[[m >= FROM_2022 for m in full]].mean():.1f}/20; "
        f"max {d.max()}; najczęściej brakujące: {', '.join(f'{s} ({n})' for s, n in missing.most_common(15))}"
    )


def _from_2022(series: pd.Series, name: str) -> None:
    s = series[series.index >= FROM_2022]
    w = summarize_pnl(s, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    print(
        f"  OPISOWO od 2022 ({name}): {w['n']} dni, {100 * w['mean'] * DAYS_PER_YEAR:+.1f}%/rok "
        f"[{100 * w['ci_low'] * DAYS_PER_YEAR:+.1f}; {100 * w['ci_high'] * DAYS_PER_YEAR:+.1f}], t_neff {w['t_neff']:+.2f}"
    )


def run_ts1() -> None:
    ts1.UNIVERSE_DIR = FULL
    ts1.main([])
    fee, close, funding, members, start, end = ts1._load(FULL)
    avg, _ = portfolio(close, funding, members, start, end, fee)
    _from_2022(avg.dropna().set_index("date")["net"], "TS1 netto")


def run_x1() -> None:
    x1.main([FULL])
    fee, close, funding, members, dates = x1._load(FULL)
    out = long_short_returns(close, funding, members, dates, fee)
    _from_2022(out.set_index("date")["r_net"], "X1 netto")


def _extremes(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    o = pd.read_parquet(OHLC_FULL)
    o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
    hi = o.pivot(index="open_time", columns="symbol", values="high").reindex(index=close.index)
    lo = o.pivot(index="open_time", columns="symbol", values="low").reindex(index=close.index)
    return hi, lo


def run_sz1() -> None:
    fee, close, funding, members, start, end = ts1._load(FULL)
    hi, lo = _extremes(close)
    tr, _ = portfolio(
        close,
        funding,
        members,
        start,
        end,
        fee,
        liq={"high": hi, "low": lo, "lev": LEV_TS, "mmr": MMR},
    )
    fee_c, close_c, fund_c, mem_c, signs, _p, start_c, end_c = load_cp()
    hc, lc = _extremes(close_c)
    cp, _ = portfolio(
        close_c,
        fund_c,
        mem_c,
        start_c,
        end_c,
        fee_c,
        signs_override=signs,
        liq={"high": hc, "low": lc, "lev": LEV_CP, "mmr": MMR},
    )
    rets = pd.concat(
        [
            tr.dropna().set_index("date")["net"].rename("trend"),
            cp.dropna().set_index("date")["net"].rename("coinbase"),
        ],
        axis=1,
    ).dropna()
    print(SEP)
    print("RU1 — SZ1 NA PEŁNYM UNIWERSUM: trend (likwidacja 2×) + premia Coinbase (3×); opisowo")
    print(SEP)
    print(
        f"  okres {rets.index.min().date()} → {rets.index.max().date()} ({len(rets)} dni); korelacja {rets.corr().iloc[0, 1]:+.2f}"
    )
    for c in rets.columns:
        s = summary(rets[c])
        print(
            f"  składowa {c:>8}: CAGR {100 * s['cagr']:+6.1f}%, zmienność {100 * s['vol']:5.1f}%, "
            f"max obsunięcie {100 * s['max_dd']:5.1f}%"
        )
    for rule in ("R0", "R1", "R2"):
        out = apply_rules(rets, rule).set_index("date")
        s = summary(out["ret"])
        s22 = summary(out["ret"][out.index >= FROM_2022])
        print(
            f"  {rule}: CAGR {100 * s['cagr']:+6.1f}%, zmienność {100 * s['vol']:5.1f}%, max obsunięcie {100 * s['max_dd']:5.1f}%, "
            f"najgorszy miesiąc {100 * s['worst_month']:+.1f}% | od 2022: CAGR {100 * s22['cagr']:+.1f}%, obsunięcie {100 * s22['max_dd']:.1f}%"
        )


if __name__ == "__main__":
    {"sklad": sklad, "ts1": run_ts1, "x1": run_x1, "sz1": run_sz1}[sys.argv[1]]()
