"""PR1 — bramka 16a: druga droga. (1) depozyt liczony z REALNEJ ekspozycji nóg (definicja SZ1:
k·nominał/dźwignia) zamiast górnego oszacowania Σ k/dźwignia; (2) ES95 tyg. z bootstrapem;
(3) max DD inną formułą (log-cumsum); (4) zgodność nóg z KR1 legs()."""

import numpy as np
import pandas as pd

from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.run_kr1_korelacje import FULL, legs
from backtest.run_pr1_portfel import LEVERAGE, margin_share, risk_metrics
from backtest.run_ts_momentum_ts1 import _load as load_ts
from backtest.sizing import apply_rules
from backtest.ts_momentum import portfolio

fee, close, funding, members, start, end = load_ts(FULL)
ts, _ = portfolio(close, funding, members, start, end, fee)
ts = ts.dropna().set_index("date")
fee_c, close_c, fund_c, mem_c, signs, _p, start_c, end_c = load_cp()
cp, _ = portfolio(close_c, fund_c, mem_c, start_c, end_c, fee_c, signs_override=signs)
cp = cp.dropna().set_index("date")
rets = pd.concat([ts["net"].rename("TS1"), cp["net"].rename("CP1")], axis=1).dropna()
expo = pd.concat([ts["gross_notional"].rename("TS1"), cp["gross_notional"].rename("CP1")], axis=1)
rets.index = pd.to_datetime(rets.index, utc=True)
expo.index = pd.to_datetime(expo.index, utc=True)
lg = legs()
rets = rets.reindex(lg.index)
expo = expo.reindex(lg.index)
print(
    f"okno {rets.index.min().date()} → {rets.index.max().date()}, dni {len(rets)}, braki {int(rets.isna().sum().sum())}"
)
print(
    "zgodność nóg z KR1 legs(): max |Δ| TS1 %.2e, CP1 %.2e"
    % ((rets["TS1"] - lg["TS1"]).abs().max(), (rets["CP1"] - lg["CP1"]).abs().max())
)
print(
    f"ekspozycja nóg (nominał/kapitał) mediana: TS1 {expo['TS1'].median():.2f}×, CP1 {expo['CP1'].median():.2f}×; "
    f"p90: TS1 {expo['TS1'].quantile(0.9):.2f}×, CP1 {expo['CP1'].quantile(0.9):.2f}×; max: TS1 {expo['TS1'].max():.2f}×, CP1 {expo['CP1'].max():.2f}×"
)
r1 = apply_rules(lg[["TS1", "CP1"]], "R1").set_index("date")
m = risk_metrics(r1["ret"])
print(
    f"R1 (KR1 legs): CAGR {100*m['cagr']:+.1f}%, DD {100*m['max_dd']:.1f}%, ES95 tyg {100*m['es95_week']:.1f}%, n_weeks {m['n_weeks']}"
)
up = margin_share(r1, ["TS1", "CP1"])
real = r1["k_TS1"] * expo["TS1"] / LEVERAGE["TS1"] + r1["k_CP1"] * expo["CP1"] / LEVERAGE["CP1"]
print(
    f"depozyt GÓRNE oszacowanie Σk/dźw.: mediana {100*up.median():.1f}% [p10 {100*up.quantile(.1):.0f}; p90 {100*up.quantile(.9):.0f}], max {100*up.max():.0f}%"
)
print(
    f"depozyt REALNY k·nominał/dźw.:     mediana {100*real.median():.1f}% [p10 {100*real.quantile(.1):.0f}; p90 {100*real.quantile(.9):.0f}], max {100*real.max():.0f}%, p99 {100*real.quantile(.99):.0f}%"
)
print(
    f"udział dni z realnym depozytem > 5%/10% kapitału strategii ≈ (skala 10%): >50%: {100*(real>0.5).mean():.1f}% dni; >100%: {100*(real>1.0).mean():.1f}% dni"
)
for label, ms in (
    ("górne", up.median()),
    ("realne", real.median()),
    ("realne p90", real.quantile(0.9)),
    ("realne max", real.max()),
):
    sc = 0.05 / ms
    print(
        f"  ADR-09 przez {label:<10} depozyt {100*ms:5.1f}% → kapitał strategii {100*sc:5.1f}% całego; max DD {100*m['max_dd']*sc:.1f}%, najg. tydz. {100*m['worst_week']*sc:.1f}%, ES95 {100*m['es95_week']*sc:.1f}%, CAGR {100*m['cagr']*sc:+.1f} pkt"
    )
# (2) bootstrap ES95 tygodniowego
x = r1["ret"].astype(float)
week = x.resample("W-FRI").sum()
q = week.quantile(0.05)
tail = week[week <= q]
print(
    f"tygodnie {len(week)}, w ogonie 5%: {len(tail)}, ES95 {100*tail.mean():.2f}%, najgorsze 3: {[round(100*v,1) for v in tail.nsmallest(3)]}"
)
rng = np.random.default_rng(0)
w = week.to_numpy()
bs = []
for _ in range(4000):
    s = rng.choice(w, size=len(w), replace=True)
    qq = np.quantile(s, 0.05)
    bs.append(s[s <= qq].mean())
bs = np.array(bs)
print(
    f"ES95 tyg. bootstrap 95%: [{100*np.quantile(bs,.025):.2f}%; {100*np.quantile(bs,.975):.2f}%]"
)
# max DD inną formułą
lr = np.log1p(x.to_numpy())
cum = np.cumsum(lr)
dd2 = 1 - np.exp(cum - np.maximum.accumulate(cum))
print(f"max DD (log-cumsum): {100*dd2.max():.2f}% vs summary {100*m['max_dd']:.2f}%")
# CAGR drugą drogą
yrs = (x.index[-1] - x.index[0]).days / 365.25
print(
    f"CAGR kalendarzowo ({yrs:.2f} lat): {100*(np.exp(cum[-1])**(1/yrs)-1):+.2f}% vs summary {100*m['cagr']:+.2f}%"
)
# rozkład tygodni
print(
    f"tygodnie: średnia {100*week.mean():+.2f}%, mediana {100*week.median():+.2f}%, sd {100*week.std():.2f}%, skośność {week.skew():.2f}, kurtoza {week.kurt():.2f}, ujemnych {100*(week<0).mean():.0f}%"
)
