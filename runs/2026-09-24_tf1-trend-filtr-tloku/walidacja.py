"""Walidacja TF1 (bramka 16a): faza 0 z filtrem przeliczona niezależnie (pętla pandas, bez
ts_momentum/keep_fn) i porównana z silnikiem; udział filtrowanych pozycji w fazie 0.
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_tf1-trend-filtr-tloku/walidacja.py
"""

import numpy as np
import pandas as pd

from backtest.run_crowding_tf1 import F_HI, _load, funding_sum, make_keep_fn
from backtest.ts_momentum import portfolio

fee, close, funding, members, start, end = _load()
fund = funding.reindex(index=close.index, columns=close.columns).fillna(0.0)
f7 = fund.rolling(7, min_periods=7).sum()
ret = close.pct_change(fill_method=None)
months = sorted(members)
forms = list(close.index[(close.index >= start) & (close.index < end)][::7])
pos, rows, n_all, n_cut = {}, [], 0, 0
for k, t in enumerate(forms):
    m = max(x for x in months if x <= t)
    valid = []
    for s in members[m]:
        a, b = close[s].get(t, np.nan), close[s].get(t - pd.Timedelta(days=28), np.nan)
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        sig = np.sign(a / b - 1)
        r = ret[s].loc[:t].dropna()
        if sig == 0 or len(r) < 30:
            continue
        wts = (1 - 1 / 61) ** np.arange(len(r))[::-1]
        valid.append((s, sig, np.sqrt(365 * np.sum(wts * r.to_numpy() ** 2) / np.sum(wts))))
    new = {}
    for s, sig, vol in valid:
        crowded = (sig > 0 and f7.at[t, s] > F_HI) or (sig < 0 and f7.at[t, s] < -F_HI)
        n_all += 1
        n_cut += int(crowded)
        new[s] = 0.0 if crowded else sig * min(3.0, 0.40 / vol) / len(valid)
    turnover = sum(abs(new.get(x, 0) - pos.get(x, 0)) for x in set(new) | set(pos))
    pos = dict(new)
    nxt = forms[k + 1] if k + 1 < len(forms) else close.index[-1]
    for j, d in enumerate(close.index[(close.index > t) & (close.index <= nxt)]):
        rr = {s: (0.0 if not np.isfinite(ret.at[d, s]) else ret.at[d, s]) for s in pos}
        g = sum(w * rr[s] for s, w in pos.items())
        rows.append(
            (
                d,
                g
                - sum(w * fund.at[d, s] for s, w in pos.items())
                - (fee * turnover if j == 0 else 0.0),
            )
        )
        pos = {s: w * (1 + rr[s]) / (1 + g) for s, w in pos.items()}
ph0 = pd.Series(dict(rows))
_, ph = portfolio(close, funding, members, start, end, fee, keep_fn=make_keep_fn(funding_sum(fund)))
print(
    f"faza 0 TF1 niezależnie: {100 * ph0.mean() * 365:+.2f}%/rok; silnik: {100 * ph[0]['net'].mean() * 365:+.2f}%/rok; "
    f"filtrowane pozycje w formowaniach fazy 0: {n_cut}/{n_all} ({100 * n_cut / n_all:.1f}%)"
)
