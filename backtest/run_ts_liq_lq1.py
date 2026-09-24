"""
run_ts_liq_lq1.py — runda LQ1: POPRAWKA pomiaru TS1 o likwidacje. Reguła TS1 bez zmian; każda
pozycja stoi na izolowanym depozycie = ekspozycja/3 (dźwignia 3×, sposób handlu użytkownika);
likwidacja, gdy dzienne ekstremum odsunie cenę od wejścia o ≥ 1/3 − 1 % przeciw pozycji
(dzienne high/low z archiwum: `data/fetch_universe_ohlc.py`). Konfiguracja ZAMROŻONA
w `runs/2026-09-24_lq1-likwidacje/README.md`.

    PYTHONUTF8=1 py -m backtest.run_ts_liq_lq1

Kryterium jak TS1 (dla TS1 z likwidacją): POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0
(znaki przesunięte w czasie, liczone TYM SAMYM silnikiem z likwidacją); NEGATYWNY, gdy górny
kraniec CI < 0; inaczej NIEROZSTRZYGNIĘTY. Opisowo: różnica parowana z TS1 bez likwidacji.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.run_ts_momentum_ts1 import _load
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio

OHLC = "data/raw/universe_ohlc/ohlc_1d.parquet"
LEV = 3.0
MMR = 0.01
N_SIM = 100
Z95 = 1.959964
SEP = "=" * 104


def load_extremes(close: pd.DataFrame) -> dict:
    o = pd.read_parquet(OHLC)
    o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
    high = o.pivot(index="open_time", columns="symbol", values="high").reindex(index=close.index)
    low = o.pivot(index="open_time", columns="symbol", values="low").reindex(index=close.index)
    return {"high": high, "low": low, "lev": LEV, "mmr": MMR}


def _row(name, w):
    return (
        f"  {name:>18} | {100 * w['mean'] * DAYS_PER_YEAR:+6.1f}%/rok [{100 * w['ci_low'] * DAYS_PER_YEAR:+6.1f}; "
        f"{100 * w['ci_high'] * DAYS_PER_YEAR:+6.1f}] | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):5.1f}%/rok | t_neff {w['t_neff']:+5.2f}"
    )


def main() -> None:
    t0 = time.time()
    fee, close, funding, members, start, end = _load("data/raw/universe")
    liq = load_extremes(close)
    cov = []
    for m, syms in members.items():
        days = close.index[(close.index >= m) & (close.index < m + pd.offsets.MonthBegin(1))]
        cols = [s for s in syms if s in liq["high"].columns]
        cov.append(liq["high"].loc[days, cols].notna().to_numpy().sum() / (len(days) * len(syms)))
    print(SEP)
    print(
        "LQ1 — TS1 Z LIKWIDACJĄ IZOLOWANĄ PRZY 3× (depozyt = ekspozycja/3, próg 1/3 − 1 %); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"  pokrycie dziennych high/low u członków: średnio {100 * np.mean(cov):.2f}% (min miesiąc {100 * np.min(cov):.2f}%)"
    )
    base, _ = portfolio(close, funding, members, start, end, fee)
    lq, phases = portfolio(close, funding, members, start, end, fee, liq=liq)
    base, lq = base.dropna(), lq.dropna()
    wb = summarize_pnl(base["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    wl = summarize_pnl(lq["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    j = lq.set_index("date")[["net"]].join(
        base.set_index("date")[["net"]], rsuffix="_base", how="inner"
    )
    wd = summarize_pnl(
        j["net"] - j["net_base"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0
    )
    rng = np.random.default_rng(0)
    null = []
    for _ in range(N_SIM):
        k = int(7 * rng.integers(8, len(close) // 7 - 8))
        a, _ = portfolio(close, funding, members, start, end, fee, sign_shift_days=k, liq=liq)
        null.append(float(a.dropna()["net"].mean()))
    q975 = float(np.quantile(null, 0.975))
    print(_row("TS1 bez likwidacji", wb))
    print(_row("TS1 z likwidacją", wl))
    print(_row("różnica", wd))
    print(
        f"  H0 (z likwidacją): q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok; TS1-liq powyżej {100 * (np.array(null) < wl['mean']).mean():.0f}% H0"
    )
    if wl["t_neff"] > Z95 and wl["mean"] > q975:
        v = "POZYTYWNY"
    elif wl["ci_high"] < 0:
        v = "NEGATYWNY"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM TS1 z likwidacją: {v}")
    n_liq = int(sum(p["liquidations"].sum() for p in phases))
    n_pos = int(sum((p["turnover"] > 0).sum() for p in phases)) * 20
    print(
        f"  likwidacje: {n_liq} zdarzeń w 7 fazach (≈ {n_liq / 7:.0f} na fazę; rząd {100 * n_liq / max(n_pos, 1):.2f}% pozycji-tygodni); "
        f"średnia strata dnia likwidacji w portfelu: zob. walidacja"
    )
    print(
        f"  depozyt przy 3× = ekspozycja/3: mediana {lq['gross_notional'].median() / LEV:.3f} kapitału łącznie "
        f"(≈ {100 * lq['gross_notional'].median() / LEV / 20:.2f}% kapitału na monetę)"
    )
    years = pd.to_datetime(j.index).year
    print(
        "  różnica per rok (Σ): "
        + "; ".join(
            f"{y}: {100 * g.sum():+.2f}%" for y, g in (j["net"] - j["net_base"]).groupby(years)
        )
    )
    eq = np.cumprod(1 + lq["net"].to_numpy())
    print(
        f"  kapitał (k = 1, z likwidacją): CAGR {100 * (eq[-1] ** (DAYS_PER_YEAR / len(eq)) - 1):+.1f}%/rok, "
        f"max obsunięcie {100 * np.max(1 - eq / np.maximum.accumulate(eq)):.1f}%"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
