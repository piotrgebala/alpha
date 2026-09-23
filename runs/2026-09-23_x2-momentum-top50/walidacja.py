"""Walidacja X2 drugą drogą (bramka 16a). Uruchomienie: PYTHONPATH=. PYTHONUTF8=1 py runs/.../walidacja.py"""

import numpy as np
import pandas as pd

from backtest.rebalance_premium import load_universe, monthly_members
from backtest.run_xs_momentum_x2 import END, FIRST_MONTH, LEG_SIZE, TOP_N
from backtest.xs_momentum import (
    HOLD_DAYS,
    SIGNAL_LOOKBACK_DAYS,
    daily_funding_panel,
    long_short_returns,
    rank_legs,
    rebalance_dates,
    signal_panel,
)

FEE = 0.0005 + 0.0002
close, volume = load_universe("data/raw/universe")
funding = daily_funding_panel("data/raw/universe")
end = pd.Timestamp(END, tz="UTC")
close = close[close.index < end]
months = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
members = monthly_members(volume, months, top_n=TOP_N)
dates = rebalance_dates(close.index, pd.Timestamp(FIRST_MONTH, tz="UTC"), end, HOLD_DAYS)
out = long_short_returns(close, funding, members, dates, FEE, leg_size=LEG_SIZE)

print("== A. tożsamość sum ==")
s = out[["r_ls_gross", "funding_net", "cost", "r_net"]].sum()
print(
    f"  {100*s['r_ls_gross']:+.3f} + {100*s['funding_net']:+.3f} − {100*s['cost']:.3f} = {100*(s['r_ls_gross']+s['funding_net']-s['cost']):+.3f} vs Σ netto {100*s['r_net']:+.3f}"
)
print(
    f"  dni {len(out)}; dni bazy od pierwszego formowania+1: {int(((close.index > dates[0]) & (close.index < end)).sum())}; formowań {len(dates)}, obrót łączny {out['turnover'].sum():.1f}, średni {out.loc[out['turnover']>0,'turnover'].mean():.3f}"
)

print(
    "== B. NIEZALEŻNY rachunek tygodniowy (bez dryfu wag): średni zwrot 7 dni top-10 minus bottom-10 =="
)
sig = signal_panel(close, SIGNAL_LOOKBACK_DAYS)
fwd = close.shift(-HOLD_DAYS) / close - 1.0
month_starts = sorted(members)
rows = []
for t in dates:
    m = [x for x in month_starts if x <= t]
    legs = rank_legs(sig.loc[t], members[m[-1]], None, LEG_SIZE) if m else None
    if legs is None:
        continue
    rows.append(
        0.5 * (fwd.loc[t, legs[0]].fillna(0.0).mean() - fwd.loc[t, legs[1]].fillna(0.0).mean())
    )
wk = pd.Series(rows)
print(
    f"  tygodni {len(wk)}; średni tygodniowy zwrot brutto LS {100*wk.mean():+.3f}% (se {100*wk.std(ddof=1)/np.sqrt(len(wk)):.3f}%) → ×52 = {100*52*wk.mean():+.1f}%/rok; z szeregu dziennego Σ brutto / tygodnie = {100*s['r_ls_gross']/len(wk):+.3f}%/tydzień"
)

print("== C. X1 vs X2 na WSPÓLNYM oknie (od 2021-05-01): top-20/5 tym samym kodem ==")
members20 = monthly_members(volume, months, top_n=20)
out20 = long_short_returns(close, funding, members20, dates, FEE, leg_size=5)
for name, o in (("X1-okno-X2 (top-20/5)", out20), ("X2 (top-50/10)", out)):
    se = o["r_net"].std(ddof=1) / np.sqrt(len(o))
    print(
        f"  {name:>22}: dni {len(o)}, średnia {100*o['r_net'].mean():+.4f}%/dzień [{100*(o['r_net'].mean()-1.96*se):+.4f}; {100*(o['r_net'].mean()+1.96*se):+.4f}], Σ {100*o['r_net'].sum():+.1f}%, sd {100*o['r_net'].std():.3f}%"
    )
both = (
    out20.set_index("date")["r_net"]
    .to_frame("x1")
    .join(out.set_index("date")["r_net"].to_frame("x2"), how="inner")
)
print(f"  korelacja dziennych zwrotów X1-okno vs X2: {both['x1'].corr(both['x2']):+.3f}")

print("== D. kogo nie ma / ogony ==")
sig_ok = pd.Series(
    {
        t: int(sig.loc[t].reindex(members[[x for x in month_starts if x <= t][-1]]).notna().sum())
        for t in dates
    }
)
print(
    f"  członków z sygnałem na formowanie: min {sig_ok.min()}, mediana {sig_ok.median():.0f}; dni z nogą < {LEG_SIZE}: {int(((out['n_long'] < LEG_SIZE) | (out['n_short'] < LEG_SIZE)).sum())}"
)
btc = close["BTCUSDT"].pct_change().reindex(out["date"]).to_numpy()
print(
    f"  korelacja netto vs BTC {np.corrcoef(np.nan_to_num(btc), out['r_net'])[0,1]:+.3f}; |r_net| > 5 %: {int((out['r_net'].abs() > 0.05).sum())} dni, suma {100*out.loc[out['r_net'].abs() > 0.05, 'r_net'].sum():+.2f}%; bez 20 skrajnych dni średnia {100*out['r_net'].drop(out['r_net'].abs().nlargest(20).index).mean():+.4f}% vs {100*out['r_net'].mean():+.4f}%"
)
