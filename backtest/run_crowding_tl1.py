"""
run_crowding_tl1.py — runda TL1: TŁOK PRZEKROJOWY na top-20. Wynik tłoku monety i na zamknięciu t:
    crowd_i = Δlog(OI_i, 7 dni) · znak(zwrot_i z 7 dni)
czyli nowy lewar dokładany W KIERUNKU ostatniego ruchu. Portfel long-short (silnik X1:
kapitał 1 = 0,5 + 0,5, trzymanie 7 dni, koszty obrotu, funding per symbol): SHORT 5 monet
z najwyższym crowd (tłok za ruchem w górę / goniący), LONG 5 z najniższym (lewar ucieka albo
tłok po stronie spadku). 7 faz tygodniowych naraz (wniosek 68). OI: `data/raw/oi_panel`
(archiwum metrics, ostatni odczyt dnia, od 2021-12).
Konfiguracja ZAMROŻONA w `runs/2026-09-24_tl1-tlok-przekrojowy/README.md`.

    PYTHONUTF8=1 py -m backtest.run_crowding_tl1 --moc   # H0: crowd przesunięty w czasie
    PYTHONUTF8=1 py -m backtest.run_crowding_tl1

Kryterium: POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0; NEGATYWNY, gdy górny kraniec
CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.xs_momentum import daily_funding_panel, long_short_returns

UNIVERSE_DIR = "data/raw/universe"
OI_PANEL = "data/raw/oi_panel/oi_daily.parquet"
FIRST_MONTH = "2021-12-01"
START = "2021-12-15"  # 7 dni zmiany OI + rozbieg 10 dni w panelu
END = "2026-07-01"
WINDOW = 7
LEG = 5
PHASES = 7
N_SIM = 50
Z95 = 1.959964
DAYS_PER_YEAR = 365
SEP = "=" * 104


def crowd_panel(oi: pd.DataFrame, close: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    """crowd = Δlog(OI, window) · znak(zwrot z window dni); dane ≤ t; brak OI → NaN."""
    oi_w = oi.pivot(index="date", columns="symbol", values="oi").sort_index()
    oi_w.index = pd.to_datetime(oi_w.index, utc=True)
    oi_w = oi_w.reindex(index=close.index, columns=close.columns)
    d_oi = np.log(oi_w) - np.log(oi_w.shift(window))
    ret = close / close.shift(window) - 1.0
    return d_oi * np.sign(ret)


def make_legs_fn(crowd: pd.DataFrame):
    """long = LEG najniższych crowd, short = LEG najwyższych (wśród członków z wartością)."""

    def legs(signal_row, members, rng, leg_size):
        t = signal_row.name
        row = crowd.loc[t, [s for s in members if s in crowd.columns]].dropna()
        if len(row) < 2 * leg_size:
            return None
        ranked = row.sort_values(kind="mergesort")
        return sorted(ranked.index[:leg_size]), sorted(ranked.index[-leg_size:])

    return legs


def _dates(index, start, end, phase):
    first = start + pd.Timedelta(days=phase)
    days = index[(index >= first) & (index < end)]
    return list(days[::7])


def portfolio_phases(close, funding, members, crowd, start, end, fee):
    per = []
    for ph in range(PHASES):
        out = long_short_returns(
            close,
            funding,
            members,
            _dates(close.index, start, end, ph),
            fee,
            legs_fn=make_legs_fn(crowd),
            leg_size=LEG,
        )
        per.append(out.set_index("date"))
    first = max(p.index.min() for p in per)
    cols = ["r_ls_gross", "funding_net", "cost", "r_net", "r_long", "r_short"]
    avg = sum(p.loc[p.index >= first, cols] for p in per) / PHASES
    return avg.dropna(), per


def _load():
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, volume = load_universe(UNIVERSE_DIR)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, months)
    oi = pd.read_parquet(OI_PANEL)
    return (
        fee,
        close,
        daily_funding_panel(UNIVERSE_DIR),
        members,
        oi,
        pd.Timestamp(START, tz="UTC"),
        end,
    )


def run(moc: bool) -> None:
    t0 = time.time()
    fee, close, funding, members, oi, start, end = _load()
    crowd = crowd_panel(oi, close)
    cov = []
    for m, syms in members.items():
        days = crowd.index[
            (crowd.index >= max(m, start))
            & (crowd.index < m + pd.offsets.MonthBegin(1))
            & (crowd.index < end)
        ]
        if len(days):
            cov.append(crowd.loc[days, syms].notna().mean().mean())
    print(SEP)
    print(
        (
            "TL1 — RACHUNEK MOCY (H0: crowd przesunięty w czasie)"
            if moc
            else "TL1 — TŁOK PRZEKROJOWY NA TOP-20 (OI × kierunek ruchu)"
        )
        + "; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"  OI: {oi['symbol'].nunique()} symboli, {len(oi)} dni-symboli; pokrycie crowd u członków od {start.date()}: "
        f"średnio {100 * np.mean(cov):.1f}% (min miesiąc {100 * np.min(cov):.1f}%)"
    )
    rng = np.random.default_rng(0)
    n_days = len(close.index[close.index >= start])
    null = []
    for _ in range(N_SIM):
        k = int(7 * rng.integers(8, n_days // 7 - 8))
        shifted = pd.DataFrame(
            np.roll(crowd.to_numpy(), k, axis=0), index=crowd.index, columns=crowd.columns
        )
        a, _ = portfolio_phases(close, funding, members, shifted, start, end, fee)
        null.append((float(a["r_net"].mean()), float(a["r_net"].std(ddof=1))))
    null = np.array(null)
    q975 = float(np.quantile(null[:, 0], 0.975))
    if moc:
        sd = float(np.median(null[:, 1]))
        se = max(float(null[:, 0].std(ddof=1)), sd / np.sqrt(len(a)))
        hw = Z95 * se * DAYS_PER_YEAR
        print(
            f"  dni {len(a)}; zmienność H0 {100 * sd * np.sqrt(DAYS_PER_YEAR):.1f}%/rok; half-width 95% {100 * hw:.1f}%/rok "
            f"= {hw / (sd * np.sqrt(DAYS_PER_YEAR)):.2f} SR; q97,5 H0 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok"
        )
        print(f"  czas: {time.time() - t0:.0f}s")
        return
    avg, per = portfolio_phases(close, funding, members, crowd, start, end, fee)
    w = summarize_pnl(avg["r_net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    print(
        f"  TL1 netto | {w['n']} dni | {100 * w['mean'] * DAYS_PER_YEAR:+.1f}%/rok [{100 * w['ci_low'] * DAYS_PER_YEAR:+.1f}; "
        f"{100 * w['ci_high'] * DAYS_PER_YEAR:+.1f}] | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):.1f}%/rok | t_neff {w['t_neff']:+.2f}; "
        f"H0 q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok, TL1 powyżej {100 * (null[:, 0] < w['mean']).mean():.0f}% H0"
    )
    if w["t_neff"] > Z95 and w["mean"] > q975:
        v = "POZYTYWNY"
    elif w["ci_high"] < 0:
        v = "NEGATYWNY"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM TL1: {v}")
    print(
        f"  Σ brutto {100 * avg['r_ls_gross'].sum():+.1f}% | funding {100 * avg['funding_net'].sum():+.1f}% | koszt {100 * avg['cost'].sum():.1f}% | "
        f"noga long {100 * avg['r_long'].mean() * DAYS_PER_YEAR:+.1f}%/rok, noga short (zwrot monet) {100 * avg['r_short'].mean() * DAYS_PER_YEAR:+.1f}%/rok"
    )
    years = pd.to_datetime(avg.index).year
    print(
        "  per rok (Σ netto): "
        + "; ".join(f"{y}: {100 * g['r_net'].sum():+.1f}%" for y, g in avg.groupby(years))
    )
    print(
        "  7 faz (%/rok): "
        + ", ".join(f"{100 * p['r_net'].mean() * DAYS_PER_YEAR:+.1f}" for p in per)
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    run(bool(sys.argv[1:]) and sys.argv[1] == "--moc")
