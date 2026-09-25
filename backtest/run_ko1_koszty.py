"""
run_ko1_koszty.py — runda KO1 (opisowo, 0 wariantów): ile zwrotu nóg dziennika (TS1 trend, X1 7 faz,
CP1 premia Coinbase) zjadają koszty wykonania przy zleceniach rynkowych (taker) i limitowych (maker)?

Te same silniki i dane co KR1 / RU1 / X1F / CP1; zmienia się TYLKO stawka kosztu × obrót:
- taker: prowizja 0,05 % + poślizg 0,02 % = 0,07 % za stronę (config — dziś we wszystkich rundach);
- maker 90 %: 0,9 · 0,02 % + 0,1 · 0,07 % = 0,025 % (niewypełnione dokupione rynkowo);
- maker 100 %: 0,02 % (granica optymistyczna).
Niemodelowane: niekorzystna selekcja wypełnień (C2.12, W1) — realny zysk z limitów jest NIŻSZY.

    PYTHONUTF8=1 py -m backtest.run_ko1_koszty
"""

from __future__ import annotations

import pandas as pd

from backtest import run_ts_momentum_ts1 as ts1
from backtest import run_xs_momentum_x1 as x1
from backtest.checkpoint_lib import load_config
from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.ts_momentum import DAYS_PER_YEAR, PHASES, formation_dates, portfolio
from backtest.xs_momentum import long_short_returns

FULL = "data/raw/universe_full"
SEP = "=" * 104


def scenarios() -> dict[str, float]:
    c = load_config()["costs"]
    taker = c["taker_fee_rate"] + c["slippage_bps"] / 10_000.0
    maker = c["maker_fee_rate"]
    return {"taker": taker, "maker 90%": 0.9 * maker + 0.1 * taker, "maker 100%": maker}


def legs_at(fee: float) -> pd.DataFrame:
    """Dzienne zwroty netto trzech nóg przy danej stawce kosztu (wspólne okno)."""
    _, close, funding, members, start, end = ts1._load(FULL)
    ts, _ = portfolio(close, funding, members, start, end, fee)
    ts = ts.dropna().set_index("date")["net"]
    _, close_x, fund_x, mem_x, _ = x1._load(FULL)
    s, e = pd.Timestamp(x1.FIRST_MONTH, tz="UTC"), pd.Timestamp(x1.END, tz="UTC")
    ph = [
        long_short_returns(
            close_x, fund_x, mem_x, formation_dates(close_x.index, s, e, p), fee
        ).set_index("date")["r_net"]
        for p in range(PHASES)
    ]
    panel = pd.concat(ph, axis=1)
    xs = panel[panel.index >= max(q.first_valid_index() for _, q in panel.items())].mean(axis=1)
    _, close_c, fund_c, mem_c, signs, _p, start_c, end_c = load_cp()
    cp, _ = portfolio(close_c, fund_c, mem_c, start_c, end_c, fee, signs_override=signs)
    cp = cp.dropna().set_index("date")["net"]
    df = pd.concat({"TS1": ts, "X1": xs, "CP1": cp}, axis=1).dropna()
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def main() -> None:
    sc = scenarios()
    res = {name: legs_at(fee).mean() * DAYS_PER_YEAR for name, fee in sc.items()}
    zero = legs_at(0.0).mean() * DAYS_PER_YEAR
    print(SEP)
    print(
        "KO1 — koszty wykonania nóg dziennika: taker vs maker (ten sam silnik, tylko stawka × obrót)"
    )
    print(SEP)
    print("  stawki za stronę: " + ", ".join(f"{k} {100 * v:.3f}%" for k, v in sc.items()))
    print(
        f"  {'noga':<5} | bez kosztów | "
        + " | ".join(f"{k:>11}" for k in sc)
        + " | koszt taker | zysk maker 90% vs taker"
    )
    for leg in ("TS1", "X1", "CP1"):
        cost_t = zero[leg] - res["taker"][leg]
        gain = res["maker 90%"][leg] - res["taker"][leg]
        print(
            f"  {leg:<5} | {100 * zero[leg]:+10.1f}% | "
            + " | ".join(f"{100 * res[k][leg]:+10.1f}%" for k in sc)
            + f" | {100 * cost_t:10.1f}% | {100 * gain:+.1f} pkt/rok"
        )
    print(
        "  (zwroty %/rok z dziennych średnich; zmienność nóg bez zmian — koszt przesuwa tylko średnią)"
    )
    print(SEP)


if __name__ == "__main__":
    main()
