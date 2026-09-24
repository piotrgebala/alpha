"""
run_sizing_sz1.py — runda SZ1: reguły wielkości pozycji (R0/R1/R2, `backtest/sizing.py`) dla
portfela dwóch kandydatów — trend TS1 (likwidacja izolowana 2× na altcoinach, wniosek 76) i premia
Coinbase CP1 (likwidacja izolowana 3× na BTC). Opisowo, 0 wariantów przewagi, bez werdyktu.
Konfiguracja ZAMROŻONA w `runs/2026-09-24_sz1-wielkosc-pozycji/README.md`.

    PYTHONUTF8=1 py -m backtest.run_sizing_sz1
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.run_ts_liq_lq1 import load_extremes
from backtest.run_ts_momentum_ts1 import _load as load_ts
from backtest.sizing import DAYS_PER_YEAR, apply_rules, summary
from backtest.ts_momentum import portfolio

LEV_TS, LEV_CP = 2.0, 3.0
SEP = "=" * 104


def components() -> tuple[pd.DataFrame, pd.DataFrame]:
    fee, close, funding, members, start, end = load_ts("data/raw/universe")
    liq = load_extremes(close)
    liq["lev"] = LEV_TS
    ts, _ = portfolio(close, funding, members, start, end, fee, liq=liq)
    ts = ts.dropna().set_index("date")
    fee_c, close_c, fund_c, mem_c, signs, _prem, start_c, end_c = load_cp()
    liq_c = load_extremes(close_c)
    liq_c["lev"] = LEV_CP
    cp, _ = portfolio(
        close_c, fund_c, mem_c, start_c, end_c, fee_c, signs_override=signs, liq=liq_c
    )
    cp = cp.dropna().set_index("date")
    rets = pd.concat([ts["net"].rename("trend"), cp["net"].rename("coinbase")], axis=1).dropna()
    expo = pd.concat(
        [ts["gross_notional"].rename("trend"), cp["gross_notional"].rename("coinbase")], axis=1
    ).reindex(rets.index)
    return rets, expo


def main() -> None:
    t0 = time.time()
    rets, expo = components()
    print(SEP)
    print(
        "SZ1 — REGUŁY WIELKOŚCI POZYCJI: trend (likwidacja 2×) + premia Coinbase (likwidacja 3×); opisowo"
    )
    print(SEP)
    print(
        f"  okres wspólny: {rets.index.min().date()} → {rets.index.max().date()} ({len(rets)} dni); "
        f"korelacja dzienna składowych {rets.corr().iloc[0, 1]:+.2f}"
    )
    for c in rets.columns:
        s = summary(rets[c])
        print(
            f"  składowa {c:>8} (k=1): CAGR {100 * s['cagr']:+6.1f}%, zmienność {100 * s['vol']:5.1f}%, "
            f"max obsunięcie {100 * s['max_dd']:5.1f}%, najgorszy miesiąc {100 * s['worst_month']:+.1f}%, "
            f"ekspozycja mediana {expo[c].median():.2f}×"
        )
    print(
        f"\n  {'reguła':>6} | {'CAGR':>7} | {'zmienn.':>7} | {'max obs.':>8} | {'Calmar':>6} | {'najg. mies.':>11} | "
        f"{'k trend':>7} | {'k coinb.':>8} | {'ekspozycja':>10} | {'depozyt':>7} | {'hamulec':>7}"
    )
    for rule in ("R0", "R1", "R2"):
        out = apply_rules(rets, rule).set_index("date")
        s = summary(out["ret"])
        exp_total = out["k_trend"] * expo["trend"] + out["k_coinbase"] * expo["coinbase"]
        margin = (
            out["k_trend"] * expo["trend"] / LEV_TS + out["k_coinbase"] * expo["coinbase"] / LEV_CP
        )
        print(
            f"  {rule:>6} | {100 * s['cagr']:+6.1f}% | {100 * s['vol']:6.1f}% | {100 * s['max_dd']:7.1f}% | "
            f"{s['calmar']:6.2f} | {100 * s['worst_month']:+10.1f}% | {out['k_trend'].median():7.2f} | "
            f"{out['k_coinbase'].median():8.2f} | {exp_total.median():9.2f}× | {100 * margin.median():6.1f}% | "
            f"{100 * out['brake'].mean():6.1f}%"
        )
        years = pd.to_datetime(out.index).year
        print(
            "         per rok: "
            + "; ".join(
                f"{y}: {100 * (np.prod(1 + g['ret']) - 1):+.1f}%" for y, g in out.groupby(years)
            )
        )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s (zwroty roczne: {DAYS_PER_YEAR} dni)")


if __name__ == "__main__":
    main()
