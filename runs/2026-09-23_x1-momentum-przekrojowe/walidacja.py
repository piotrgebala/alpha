"""Walidacja X1 drugą drogą (bramka 16a). Uruchomienie: PYTHONPATH=. PYTHONUTF8=1 py runs/.../walidacja.py"""

import numpy as np
import pandas as pd

from backtest.rebalance_premium import load_universe, monthly_members
from backtest.xs_momentum import (
    HOLD_DAYS,
    LEG_SIZE,
    SIGNAL_LOOKBACK_DAYS,
    daily_funding_panel,
    long_short_returns,
    rank_legs,
    rebalance_dates,
    signal_panel,
)

FIRST, END = "2021-02-01", "2026-07-01"
FEE = 0.0005 + 0.0002

close, volume = load_universe("data/raw/universe")
funding = daily_funding_panel("data/raw/universe")
end = pd.Timestamp(END, tz="UTC")
close = close[close.index < end]
months = [m for m in pd.date_range(FIRST, END, freq="MS", tz="UTC") if m < end]
members = monthly_members(volume, months)
dates = rebalance_dates(close.index, pd.Timestamp(FIRST, tz="UTC"), end, HOLD_DAYS)
out = long_short_returns(close, funding, members, dates, FEE)

print("== A. tożsamość sum: Σ netto = Σ brutto + Σ funding − Σ koszty ==")
s = out[["r_ls_gross", "funding_net", "cost", "r_net"]].sum()
print(f"  {100*s['r_ls_gross']:+.3f} + {100*s['funding_net']:+.3f} − {100*s['cost']:.3f} = {100*(s['r_ls_gross']+s['funding_net']-s['cost']):+.3f} vs Σ netto {100*s['r_net']:+.3f}")
print(f"  dni {len(out)}; dni bazy od pierwszego formowania+1: {int(((close.index > dates[0]) & (close.index < end)).sum())}")
print(f"  formowań {len(dates)}, z obrotem > 0: {int((out['turnover'] > 0).sum())}, obrót łączny {out['turnover'].sum():.1f}, średni na formowanie {out.loc[out['turnover']>0,'turnover'].mean():.3f} (max 2,0)")

print("== B. NIEZALEŻNY rachunek tygodniowy (bez dryfu wag): średni zwrot 7-dniowy top-5 minus bottom-5, po formowaniach ==")
sig = signal_panel(close, SIGNAL_LOOKBACK_DAYS)
fwd = close.shift(-HOLD_DAYS) / close - 1.0
month_starts = sorted(members)
rows = []
for t in dates:
    m = [x for x in month_starts if x <= t]
    if not m:
        continue
    legs = rank_legs(sig.loc[t], members[m[-1]], None, LEG_SIZE)
    if legs is None:
        continue
    fl = fwd.loc[t, legs[0]].fillna(0.0).mean()
    fs = fwd.loc[t, legs[1]].fillna(0.0).mean()
    rows.append({"t": t, "ls_week": 0.5 * (fl - fs)})
wk = pd.DataFrame(rows)
print(f"  tygodni {len(wk)}; średni tygodniowy zwrot brutto LS {100*wk['ls_week'].mean():+.3f}% (se {100*wk['ls_week'].std(ddof=1)/np.sqrt(len(wk)):.3f}%) → ×52 = {100*52*wk['ls_week'].mean():+.1f}%/rok")
print(f"  z szeregu dziennego: Σ brutto / liczba tygodni = {100*s['r_ls_gross']/len(wk):+.3f}%/tydzień (różnica = dryf wag i zwroty proste vs złożone)")

print("== C. kogo nie ma ==")
n_members = pd.Series({m: len(v) for m, v in members.items()})
sig_ok = pd.Series({t: int(sig.loc[t].reindex(members[[x for x in month_starts if x <= t][-1]]).notna().sum()) for t in dates})
print(f"  członków z sygnałem na formowanie: min {sig_ok.min()}, mediana {sig_ok.median():.0f}, tygodni z < 10: {int((sig_ok < 10).sum())}")
delisted_days = int(((out['n_long'] < LEG_SIZE) | (out['n_short'] < LEG_SIZE)).sum())
print(f"  dni, w których któraś noga miała < {LEG_SIZE} aktywnych (wycofanie/brak ceny → gotówka): {delisted_days}")
print(f"  symboli w uniwersum {close.shape[1]}, w koszykach {len({s for v in members.values() for s in v})}")

print("== D. neutralność i ogony ==")
btc = close["BTCUSDT"].pct_change().reindex(out["date"]).to_numpy()
print(f"  korelacja netto vs BTC {np.corrcoef(np.nan_to_num(btc), out['r_net'])[0,1]:+.3f}; |r_net| > 5 %: {int((out['r_net'].abs() > 0.05).sum())} dni, suma tych dni {100*out.loc[out['r_net'].abs() > 0.05, 'r_net'].sum():+.2f}% z Σ netto {100*s['r_net']:+.2f}%")
print(f"  bez 20 najbardziej skrajnych dni: średnia {100*out['r_net'].drop(out['r_net'].abs().nlargest(20).index).mean():+.4f}%/dzień vs pełna {100*out['r_net'].mean():+.4f}%")
