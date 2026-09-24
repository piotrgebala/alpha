"""
run_negative_control_nc1.py — runda NC1: kontrola negatywna przyrządów na danych syntetycznych bez
informacji o przyszłości (`backtest/negative_control.py`: t-Student df = 3, GARCH, czynnik
rynkowy ρ = 0,5; 20 monet × 2 000 dni ≈ 5,5 roku, jak baza od 2021). Na każdym z `N_SEEDS`
niezależnych losowań uruchamia silniki projektu w ich kanonicznej konfiguracji:
- TS1 (trend tygodniowy, `ts_momentum.portfolio`);
- X1 (momentum przekrojowe, `xs_momentum.long_short_returns`);
- CP1 (reguła znaku z zewnętrznego szeregu: losowa „premia” AR(1) niezależna od cen, 7 vs 90 dni);
oraz KONTROLĘ CZUŁOŚCI: silnik TS1 z celowym zajrzeniem w przyszłość (znak zwrotu z NASTĘPNYCH
7 dni) — ona MUSI dać ogromne t, inaczej kontrola negatywna niczego by nie wykryła.

Oczekiwanie (zapisane przed przebiegiem w `runs/2026-09-24_nc1-kontrola-negatywna/README.md`):
t_neff zwrotu BRUTTO ~ N(0, 1): średnia |·| < 0,5, odsetek |t| > 1,96 w granicach dwumianu
wokół 5 % (przy 40 losowaniach: 0–5 z 40); zwrot NETTO ujemny (koszty). Kontrola czułości: t > 5.

    PYTHONUTF8=1 py -m backtest.run_negative_control_nc1
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.negative_control import all_members, synthetic_returns
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio
from backtest.xs_momentum import long_short_returns, rebalance_dates

N_SEEDS = 40
N_DAYS = 2_000
N_COINS = 20
FEE = 0.0009  # taker 0,05 % + poślizg 4 pb — rząd wielkości jak w config (dokładna liczba bez znaczenia)
SEP = "=" * 104


def _t(x: pd.Series) -> tuple[float, float]:
    w = summarize_pnl(x, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    return w["t_neff"], w["mean"] * DAYS_PER_YEAR


def fake_premium_signs(index: pd.DatetimeIndex, seed: int) -> pd.DataFrame:
    """Losowa premia AR(1) (φ = 0,9) niezależna od cen → znak (średnia 7 dni − średnia 90 dni)."""
    rng = np.random.default_rng(seed + 20_000)
    e = rng.standard_normal(len(index))
    p = np.empty(len(index))
    p[0] = e[0]
    for i in range(1, len(index)):
        p[i] = 0.9 * p[i - 1] + e[i]
    s = pd.Series(p, index=index)
    sig = np.sign(s.rolling(7).mean() - s.rolling(90).mean())
    return pd.DataFrame({"C00USDT": sig})


def one_seed(seed: int) -> dict:
    r = synthetic_returns(N_DAYS, N_COINS, seed=seed)
    close = 100.0 * (1.0 + r).cumprod()
    fund = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    start = close.index[120].normalize()
    end = close.index[-1] + pd.Timedelta(days=1)
    members = all_members(close, start, end)
    out = {}
    ts, _ = portfolio(close, fund, members, start, end, FEE)
    ts = ts.dropna()
    out["TS1 brutto"], out["TS1 netto"] = _t(ts["gross"]), _t(ts["net"])
    xs = long_short_returns(close, fund, members, rebalance_dates(close.index, start, end), FEE)
    out["X1 brutto"], out["X1 netto"] = _t(xs["r_ls_gross"]), _t(xs["r_net"])
    c1 = close[["C00USDT"]]
    m1 = {k: ["C00USDT"] for k in members}
    cp, _ = portfolio(
        c1,
        fund[["C00USDT"]],
        m1,
        start,
        end,
        FEE,
        signs_override=fake_premium_signs(close.index, seed),
    )
    cp = cp.dropna()
    out["CP1 brutto"], out["CP1 netto"] = _t(cp["gross"]), _t(cp["net"])
    peek = np.sign(close.shift(-7) / close - 1.0)  # CELOWY błąd: znak przyszłego tygodnia
    pk, _ = portfolio(close, fund, members, start, end, FEE, signs_override=peek)
    out["CZUŁOŚĆ (zajrzenie 7 dni)"] = _t(pk.dropna()["gross"])
    return out


def main() -> None:
    t0 = time.time()
    rows = {}
    for s in range(N_SEEDS):
        for k, v in one_seed(s).items():
            rows.setdefault(k, []).append(v)
    print(SEP)
    print(
        f"NC1 — KONTROLA NEGATYWNA: {N_SEEDS} losowań × {N_COINS} monet × {N_DAYS} dni "
        "(t-Student df 3, GARCH 0,08/0,90, ρ 0,5, średnia zmienność 4 %/dzień); funding 0"
    )
    print(SEP)
    print(
        f"  {'silnik':<28} | {'śr. t_neff':>10} | {'sd t':>5} | {'śr. |t|':>7} | {'|t|>1,96':>8} | "
        f"{'min t':>6} | {'max t':>6} | {'śr. zwrot %/rok':>15}"
    )
    for k, v in rows.items():
        t = np.array([x[0] for x in v])
        m = np.array([x[1] for x in v])
        print(
            f"  {k:<28} | {t.mean():+10.2f} | {t.std(ddof=1):5.2f} | {np.abs(t).mean():7.2f} | "
            f"{int((np.abs(t) > 1.96).sum()):>3}/{len(t):<4} | {t.min():+6.2f} | {t.max():+6.2f} | "
            f"{100 * m.mean():+15.2f}"
        )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
