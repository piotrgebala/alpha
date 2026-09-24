"""
run_ts_momentum_oos.py — reguła TS1 (momentum w czasie, `backtest/ts_momentum.py`, bez zmian)
poza próbą, na dwa sposoby (runda TS-poza-próbą, `runs/2026-09-24_ts-poza-proba/`):

- TR1 — INNE AKTYWA, ten sam okres: monety z miejsc 21–50 po obrocie (top-50 minus top-20,
  miesięcznie, point-in-time), 2021-05 → 2026-06. Kryterium jak TS1 (t_neff > 1,96 ORAZ
  średnia > q97,5 H0 ze znaków przesuniętych w czasie; NEGATYWNY: górny kraniec CI < 0).
- TP1 — NOWY CZAS, te same zasady: top-20 na danych 2026-07-01 → 2026-09-23 (cache
  `data/raw/universe_2026q3`, pobrany 2026-09-24, nieoglądany). Odczyt OPISOWY z progiem
  obalenia zapisanym z góry (3 miesiące nie potwierdzą niczego; mogą tylko obalić duży efekt).

    PYTHONUTF8=1 py -m backtest.run_ts_momentum_oos --moc     # rozrzut H0 dla TR1
    PYTHONUTF8=1 py -m backtest.run_ts_momentum_oos tr1
    PYTHONUTF8=1 py -m backtest.run_ts_momentum_oos tp1
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio
from backtest.xs_momentum import daily_funding_panel

UNIVERSE_DIR = "data/raw/universe"
UNIVERSE_Q3_DIR = "data/raw/universe_2026q3"
TS1_MEAN_ANNUAL = 0.148  # wynik TS1 (runs/2026-09-24_ts1-trend-koszyk), netto %/rok
TS1_SD_ANNUAL = 0.196
N_SIM = 100
Z95 = 1.959964
SEP = "=" * 104


def _fee() -> float:
    cfg = load_config()
    return cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0


def members_rank_band(volume, month_starts, lo: int = 20, hi: int = 50) -> dict:
    """Skład miesięczny z miejsc (lo, hi] po obrocie: top-hi minus top-lo (point-in-time)."""
    top_hi = monthly_members(volume, month_starts, top_n=hi)
    top_lo = monthly_members(volume, month_starts, top_n=lo)
    return {m: sorted(set(top_hi[m]) - set(top_lo[m])) for m in month_starts}


def _load_tr1():
    close, volume = load_universe(UNIVERSE_DIR)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range("2021-05-01", "2026-07-01", freq="MS", tz="UTC") if m < end]
    members = members_rank_band(volume, months)
    return (
        close,
        daily_funding_panel(UNIVERSE_DIR),
        members,
        pd.Timestamp("2021-05-01", tz="UTC"),
        end,
    )


def _shifts(n_days: int, n_sim: int) -> list[int]:
    rng = np.random.default_rng(0)
    weeks = n_days // 7
    return [int(7 * rng.integers(8, weeks - 8)) for _ in range(n_sim)]


def _null(close, funding, members, start, end, fee):
    out = []
    for k in _shifts(len(close), N_SIM):
        avg, _ = portfolio(close, funding, members, start, end, fee, sign_shift_days=k)
        avg = avg.dropna()
        out.append((float(avg["net"].mean()), float(avg["net"].std(ddof=1))))
    return np.array(out)


def _row(name, w):
    return (
        f"  {name:>14} | {w['n']:5d} | {100 * w['mean'] * DAYS_PER_YEAR:+7.1f}%/rok "
        f"[{100 * w['ci_low'] * DAYS_PER_YEAR:+6.1f}; {100 * w['ci_high'] * DAYS_PER_YEAR:+6.1f}] | "
        f"mediana/dzień {100 * w['median']:+.3f}% | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):5.1f}%/rok | "
        f"t_neff {w['t_neff']:+5.2f}"
    )


def run_moc() -> None:
    t0 = time.time()
    fee = _fee()
    close, funding, members, start, end = _load_tr1()
    print(SEP)
    print("TR1 — RACHUNEK MOCY: H0 (znaki TS1 przesunięte w czasie) na monetach z miejsc 21–50")
    print(SEP)
    n_syms = len({s for v in members.values() for s in v})
    print(
        f"  koszyki: {len(members)} miesięcy, {n_syms} różnych symboli, po {len(next(iter(members.values())))} monet"
    )
    arr = _null(close, funding, members, start, end, fee)
    avg, _ = portfolio(
        close, funding, members, start, end, fee, sign_shift_days=_shifts(len(close), 1)[0]
    )
    n = len(avg.dropna())
    means, sd = arr[:, 0], float(np.median(arr[:, 1]))
    se = max(float(means.std(ddof=1)), sd / np.sqrt(n))
    hw = Z95 * se * DAYS_PER_YEAR
    print(
        f"  dni {n}; sd H0 {100 * sd * np.sqrt(DAYS_PER_YEAR):.1f}%/rok; half-width 95% {100 * hw:.1f}%/rok "
        f"= {hw / (sd * np.sqrt(DAYS_PER_YEAR)):.2f} SR; q97,5 H0 {100 * np.quantile(means, 0.975) * DAYS_PER_YEAR:+.1f}%/rok"
    )
    print(f"  czas: {time.time() - t0:.0f}s")


def run_tr1() -> None:
    t0 = time.time()
    fee = _fee()
    close, funding, members, start, end = _load_tr1()
    print(SEP)
    print("TR1 — REGUŁA TS1 (zamrożona) NA MONETACH Z MIEJSC 21–50 PO OBROCIE, 2021-05 → 2026-06")
    print(SEP)
    avg, phases = portfolio(close, funding, members, start, end, fee)
    avg = avg.dropna()
    w = summarize_pnl(avg["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    null = _null(close, funding, members, start, end, fee)[:, 0]
    q975 = float(np.quantile(null, 0.975))
    print(_row("TR1 netto", w))
    print(
        f"  H0: średnia {100 * null.mean() * DAYS_PER_YEAR:+.1f}%/rok, q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok; "
        f"TR1 powyżej {100 * (null < w['mean']).mean():.0f}% portfeli H0"
    )
    if w["t_neff"] > Z95 and w["mean"] > q975:
        v = "POZYTYWNY — reguła TS1 powtarza się na innych monetach"
    elif w["ci_high"] < 0:
        v = "NEGATYWNY — górny kraniec CI < 0"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM TR1: {v}")
    print(
        f"  Σ brutto {100 * avg['gross'].sum():+.1f}% | funding {100 * avg['funding'].sum():+.1f}% | koszt {100 * avg['cost'].sum():.1f}% | "
        f"nominał brutto mediana {avg['gross_notional'].median():.2f}×, netto średnio {avg['net_notional'].mean():+.2f}×"
    )
    years = pd.to_datetime(avg["date"]).dt.year
    print(
        "  per rok (Σ netto): "
        + "; ".join(f"{y}: {100 * g['net'].sum():+.1f}%" for y, g in avg.groupby(years))
    )
    print(
        "  7 faz (%/rok): "
        + ", ".join(f"{100 * p['net'].mean() * DAYS_PER_YEAR:+.1f}" for p in phases)
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


def run_tp1() -> None:
    t0 = time.time()
    fee = _fee()
    close, volume = load_universe(UNIVERSE_Q3_DIR)
    end = pd.Timestamp("2026-09-24", tz="UTC")
    close, volume = close[close.index < end], volume[volume.index < end]
    months = [pd.Timestamp(m, tz="UTC") for m in ("2026-07-01", "2026-08-01", "2026-09-01")]
    members = monthly_members(volume, months)
    funding = daily_funding_panel(UNIVERSE_Q3_DIR)
    start = months[0]
    print(SEP)
    print("TP1 — REGUŁA TS1 (zamrożona) NA NOWYCH DANYCH 2026-07-01 → 2026-09-23 (top-20, 7 faz)")
    print(SEP)
    print(
        f"  dane: {close.shape[1]} symboli, {close.index.min().date()} → {close.index.max().date()} "
        f"(rozbieg σ̂ i sygnału przed 2026-07-01); składy: "
        + "; ".join(
            f"{m.date()}: {', '.join(s.replace('USDT', '') for s in members[m])}" for m in months
        )
    )
    avg, phases = portfolio(close, funding, members, start, end, fee)
    avg = avg.dropna()
    n = len(avg)
    mean_ann = float(avg["net"].mean()) * DAYS_PER_YEAR
    se_ann = TS1_SD_ANNUAL / np.sqrt(n / DAYS_PER_YEAR)
    floor = TS1_MEAN_ANNUAL - Z95 * se_ann
    cum = float(np.prod(1 + avg["net"]) - 1)
    print(
        f"  dni ze wszystkimi fazami: {n} ({avg['date'].min().date()} → {avg['date'].max().date()}); "
        f"zwrot netto skumulowany {100 * cum:+.2f}% (brutto {100 * avg['gross'].sum():+.2f}%, funding {100 * avg['funding'].sum():+.2f}%, koszt {100 * avg['cost'].sum():.2f}%)"
    )
    print(
        f"  średnia roczna {100 * mean_ann:+.1f}%/rok; zmienność zrealizowana {100 * avg['net'].std() * np.sqrt(DAYS_PER_YEAR):.1f}%/rok; "
        f"nominał netto średnio {avg['net_notional'].mean():+.2f}×"
    )
    print(
        f"  PRÓG OBALENIA (z góry): przy prawdziwym +{100 * TS1_MEAN_ANNUAL:.1f}%/rok i zmienności {100 * TS1_SD_ANNUAL:.1f}%/rok "
        f"średnia z {n} dni poniżej {100 * floor:+.1f}%/rok zdarza się w < 2,5% przypadków"
    )
    verdict = (
        "TS1 OBALONE na nowych danych"
        if mean_ann < floor
        else "brak obalenia (i brak potwierdzenia)"
    )
    print(f"  >>> ODCZYT TP1 (opisowy): {verdict}")
    print(
        "  7 faz (skumulowane netto): "
        + ", ".join(
            f"{100 * (np.prod(1 + p['net'][p.index >= avg['date'].min()]) - 1):+.1f}%"
            for p in phases
        )
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


def main(argv: list[str]) -> None:
    mode = argv[0] if argv else "tr1"
    {"--moc": run_moc, "tr1": run_tr1, "tp1": run_tp1}[mode]()


if __name__ == "__main__":
    main(sys.argv[1:])
