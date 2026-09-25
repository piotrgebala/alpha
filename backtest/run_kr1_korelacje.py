"""
run_kr1_korelacje.py — runda KR1 (opisowo, 0 wariantów): czy trzy nogi — trend tygodniowy TS1,
momentum przekrojowe X1 i premia Coinbase CP1 — zarabiają w różnych chwilach?

Szeregi dziennych zwrotów netto tymi samymi funkcjami co RU1/X1F/CP1 (bez zmian reguł):
TS1 = `ts_momentum.portfolio` na `universe_full` (średnia 7 faz w silniku), X1 = średnia 7 faz
`long_short_returns` (jak X1F), CP1 = `portfolio` z sygnałem premii (jak CP1). Wspólne okno dni.
Korelacje: dzienne, tygodniowe (sumy 7 dni bez nakładania), w 10 % najgorszych dni TS1;
dywersyfikacja: zmienność portfela 1/σ wobec średniej zmienności nóg. Zwroty nóg są już
odczytane w swoich rundach — KR1 nie ocenia przewagi. Reguła odczytu w README (pre-rejestracja).

    PYTHONUTF8=1 py -m backtest.run_kr1_korelacje
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import run_ts_momentum_ts1 as ts1
from backtest import run_xs_momentum_x1 as x1
from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.ts_momentum import DAYS_PER_YEAR, PHASES, formation_dates, portfolio
from backtest.xs_momentum import long_short_returns

FULL = "data/raw/universe_full"
SEP = "=" * 104


def legs() -> pd.DataFrame:
    """Dzienne zwroty netto trzech nóg (indeks = dzień), wspólne okno bez braków."""
    fee, close, funding, members, start, end = ts1._load(FULL)
    ts, _ = portfolio(close, funding, members, start, end, fee)
    ts = ts.dropna().set_index("date")["net"]
    fee_x, close_x, fund_x, mem_x, _ = x1._load(FULL)
    start_x, end_x = pd.Timestamp(x1.FIRST_MONTH, tz="UTC"), pd.Timestamp(x1.END, tz="UTC")
    ph = [
        long_short_returns(
            close_x, fund_x, mem_x, formation_dates(close_x.index, start_x, end_x, p), fee_x
        ).set_index("date")["r_net"]
        for p in range(PHASES)
    ]
    panel = pd.concat(ph, axis=1)
    xs = panel[panel.index >= max(s.first_valid_index() for _, s in panel.items())].mean(axis=1)
    fee_c, close_c, fund_c, mem_c, signs, _p, start_c, end_c = load_cp()
    cp, _ = portfolio(close_c, fund_c, mem_c, start_c, end_c, fee_c, signs_override=signs)
    cp = cp.dropna().set_index("date")["net"]
    df = pd.concat({"TS1": ts, "X1": xs, "CP1": cp}, axis=1).dropna()
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def inverse_vol_mix(df: pd.DataFrame) -> pd.Series:
    """Portfel z wagami ∝ 1/σ (σ z całego okna — opisowo, nie reguła handlowa)."""
    w = 1.0 / df.std()
    return (df * (w / w.sum())).sum(axis=1)


def diversification(df: pd.DataFrame) -> float:
    """Zmienność portfela 1/σ ÷ średnia ważona zmienności nóg (1 = zero korzyści)."""
    w = 1.0 / df.std()
    w = w / w.sum()
    return float(inverse_vol_mix(df).std() / (w * df.std()).sum())


def main() -> None:
    df = legs()
    print(SEP)
    print(
        "KR1 — korelacje nóg: TS1 (trend), X1 (momentum przekrojowe, 7 faz), CP1 (premia Coinbase)"
    )
    print(SEP)
    print(f"  wspólne dni: {len(df)} ({df.index.min().date()} → {df.index.max().date()})")
    ann = np.sqrt(DAYS_PER_YEAR)
    for c in df:
        print(f"  {c:<4}: zmienność {100 * df[c].std() * ann:.1f}%/rok")
    week = df.groupby(np.arange(len(df)) // 7).sum()
    worst = df["TS1"] <= df["TS1"].quantile(0.10)
    for name, d in (("dzienne", df), ("tygodniowe", week), ("10% najgorszych dni TS1", df[worst])):
        c = d.corr()
        print(
            f"  korelacja {name:<24}: TS1–X1 {c.loc['TS1', 'X1']:+.2f} | TS1–CP1 {c.loc['TS1', 'CP1']:+.2f} | "
            f"X1–CP1 {c.loc['X1', 'CP1']:+.2f}"
        )
    for cols in (["TS1", "CP1"], ["TS1", "CP1", "X1"]):
        d = df[cols]
        print(
            f"  portfel 1/σ {'+'.join(cols):<12}: zmienność {100 * inverse_vol_mix(d).std() * ann:.1f}%/rok, "
            f"współczynnik dywersyfikacji {diversification(d):.2f} (1 = brak korzyści)"
        )
    print(SEP)


if __name__ == "__main__":
    main()
