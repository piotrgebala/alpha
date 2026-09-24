"""
run_start_fix_ru3.py — runda RU3 (korekta danych, 0 wariantów): TR1 i X2 z datą startu 2021-02-01 na pełnym
uniwersum. Start 2021-05 wziął się z OBCIĘTEGO katalogu (za mało kandydatów do top-50 w lutym–kwietniu
2021); w `universe_full` jest ich 77–88 (audyt AU1, wniosek 87). Reguły jak w rundach pierwotnych:
- TR1: TS1 na monetach z miejsc 21–50 (`run_ts_momentum_oos.members_rank_band`), 7 faz, H0 z TS1;
- X2: momentum przekrojowe top-50, nogi po 10, trzymanie 7 dni — jako ŚREDNIA 7 faz (7 dni startu
  tygodnia), bo pojedyncza faza jest wrażliwa na dzień rebalansu (wniosek 68; AU1).
Konfiguracja ZAMROŻONA w `runs/2026-09-24_ru3-data-startu/README.md`.

    PYTHONUTF8=1 py -m backtest.run_start_fix_ru3
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.run_ts_momentum_oos import members_rank_band
from backtest.run_ts_momentum_ts1 import _null
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio
from backtest.xs_momentum import daily_funding_panel, long_short_returns, rebalance_dates

FULL = "data/raw/universe_full"
START, END = "2021-02-01", "2026-07-01"
Z95 = 1.959964
SEP = "=" * 104


def _row(name: str, w: dict) -> str:
    a = DAYS_PER_YEAR
    return (
        f"  {name:<26} | {w['n']:5d} dni | {100 * w['mean'] * a:+6.1f}%/rok [{100 * w['ci_low'] * a:+6.1f}; "
        f"{100 * w['ci_high'] * a:+6.1f}] | sd {100 * w['sd'] * np.sqrt(a):5.1f}%/rok | t_neff {w['t_neff']:+5.2f}"
    )


def _w(x: pd.Series) -> dict:
    return summarize_pnl(x, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)


def main() -> None:
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, volume = load_universe(FULL)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    funding = daily_funding_panel(FULL)
    start = pd.Timestamp(START, tz="UTC")
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    print(SEP)
    print("RU3 — KOREKTA DATY STARTU TR1 i X2 (2021-02-01, pełne uniwersum); reguły zamrożone")
    print(SEP)

    band = members_rank_band(volume, months)
    avg, phases = portfolio(close, funding, band, start, end, fee)
    s = avg.dropna().set_index("date")["net"]
    w = _w(s)
    null = _null(close, funding, band, start, end, fee, 100)[:, 0]
    q975 = float(np.quantile(null, 0.975))
    v = (
        "POZYTYWNY"
        if (w["t_neff"] > Z95 and w["mean"] > q975)
        else ("NEGATYWNY" if w["ci_high"] < 0 else "NIEROZSTRZYGNIĘTY")
    )
    print("1. TR1 (miejsca 21–50, TS1, 7 faz)")
    print(_row("TR1 netto od 2021-02", w))
    print(
        f"  H0 q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok; TR1 ponad {100 * (null < w['mean']).mean():.0f}% H0 → >>> {v}"
    )
    yr = s.groupby(s.index.year).sum()
    print("  per rok (Σ): " + "; ".join(f"{y}: {100 * x:+.1f}%" for y, x in yr.items()))
    print(
        "  7 faz (%/rok): "
        + ", ".join(f"{100 * p['net'].mean() * DAYS_PER_YEAR:+.1f}" for p in phases)
    )

    top50 = monthly_members(volume, months, top_n=50)
    series = []
    for k in range(7):
        dates = rebalance_dates(close.index, start + pd.Timedelta(days=k), end, 7)
        out = long_short_returns(close, funding, top50, dates, fee, leg_size=10)
        series.append(out.set_index("date")["r_net"].rename(k))
    panel = pd.concat(series, axis=1)
    first_common = max(x.first_valid_index() for _, x in panel.items())
    x2 = panel[panel.index >= first_common].mean(axis=1).dropna()
    w2 = _w(x2)
    v2 = (
        "POZYTYWNY"
        if w2["t_neff"] > Z95
        else ("NEGATYWNY" if w2["ci_high"] < 0 else "NIEROZSTRZYGNIĘTY")
    )
    print("\n2. X2 (top-50, nogi po 10) — średnia 7 faz")
    print(_row("X2 netto od 2021-02", w2) + f" → >>> {v2}")
    print(
        "  7 faz osobno (%/rok): "
        + ", ".join(f"{100 * panel[k].mean() * DAYS_PER_YEAR:+.1f}" for k in range(7))
    )
    yr2 = x2.groupby(x2.index.year).sum()
    print("  per rok (Σ): " + "; ".join(f"{y}: {100 * x:+.1f}%" for y, x in yr2.items()))
    print(SEP)


if __name__ == "__main__":
    main()
