"""
run_x1_phases_x1f.py — runda X1F (zapis porządkowy, 0 wariantów): reguła X1 (momentum przekrojowe top-20,
sygnał 28 dni, nogi po 5, trzymanie 7 dni) jako ŚREDNIA 7 FAZ — siedem kopii tej samej reguły
startujących w kolejne dni tygodnia, każda z 1/7 kapitału. Pojedyncza faza zależy od dnia przebudowy
koszyka (wniosek 68; RU3 dla X2), a X1 w rundach X1/RU1 był liczony jedną fazą (poniedziałek).
Wynik służy też za odniesienie i progi dla X1 w dzienniku papierowym (poprawka 3, `dziennik/README.md`):
ostrzeżenie = największe obsunięcie średniej 7 faz w historii, STOP = 1,5 × ostrzeżenie (ta sama
reguła co dla portfela R1).

    PYTHONUTF8=1 py -m backtest.run_x1_phases_x1f
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.ts_momentum import DAYS_PER_YEAR, PHASES, formation_dates
from backtest.xs_momentum import daily_funding_panel, long_short_returns

FULL = "data/raw/universe_full"
START, END = "2021-02-01", "2026-07-01"
MYX_DAYS = ("2025-09-07", "2025-09-08")  # zdarzenie z RU1/AU1 (wniosek 82, 87)
SEP = "=" * 104


def _w(x: pd.Series) -> dict:
    return summarize_pnl(x, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)


def _row(name: str, x: pd.Series) -> str:
    a, w = DAYS_PER_YEAR, _w(x)
    return (
        f"  {name:<30} | {w['n']:5d} dni | {100 * w['mean'] * a:+6.1f}%/rok [{100 * w['ci_low'] * a:+6.1f}; "
        f"{100 * w['ci_high'] * a:+6.1f}] | mediana/dzień {100 * x.median():+.3f}% | t_neff {w['t_neff']:+5.2f}"
    )


def max_drawdown(r: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    """Największe obsunięcie kapitału (start = 1) i daty szczytu/dna — ta sama definicja co w dzienniku."""
    eq = np.cumprod(1.0 + r.to_numpy())
    dd = 1.0 - eq / np.maximum.accumulate(np.maximum(eq, 1.0))
    i = int(dd.argmax())
    peak = int(np.argmax(eq[: i + 1])) if eq[: i + 1].max() > 1.0 else 0
    return float(dd.max()), r.index[peak], r.index[i]


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
    members = monthly_members(volume, months)
    print(SEP)
    print(
        "X1F — X1 (top-20, sygnał 28 dni, nogi po 5, trzymanie 7 dni) jako średnia 7 faz; reguła bez zmian"
    )
    print(SEP)
    series = []
    for ph in range(PHASES):
        dates = formation_dates(close.index, start, end, ph)
        out = long_short_returns(close, funding, members, dates, fee)
        series.append(out.set_index("date")["r_net"].rename(ph))
    panel = pd.concat(series, axis=1)
    print("1. Każda faza osobno (pełny zakres fazy)")
    for ph in range(PHASES):
        day = (start + pd.Timedelta(days=ph)).day_name()
        print(_row(f"faza {ph} (start {day})", panel[ph].dropna()))
    common = panel[panel.index >= max(x.first_valid_index() for _, x in panel.items())]
    x1 = common.mean(axis=1)
    print("\n2. Średnia 7 faz (wspólne okno)")
    print(_row("X1 średnia 7 faz", x1))
    myx = x1.drop(pd.DatetimeIndex([pd.Timestamp(d, tz="UTC") for d in MYX_DAYS]), errors="ignore")
    print(_row("  bez dni MYX 7–8.09.2025", myx))
    print(_row("  od 2022 (opisowo)", x1[x1.index >= pd.Timestamp("2022-01-01", tz="UTC")]))
    yr = x1.groupby(x1.index.year).sum()
    print("  per rok (Σ): " + "; ".join(f"{y}: {100 * v:+.1f}%" for y, v in yr.items()))
    print(f"  lat dodatnich: {int((yr > 0).sum())}/{len(yr)}")
    dd, peak, trough = max_drawdown(x1)
    print(
        f"\n3. Progi dla dziennika: największe obsunięcie {100 * dd:.1f}% ({peak.date()} → {trough.date()})"
    )
    print(f"  OSTRZEŻENIE od {100 * dd:.1f}%, STOP od {100 * 1.5 * dd:.1f}% (1,5 ×)")
    print(SEP)


if __name__ == "__main__":
    main()
