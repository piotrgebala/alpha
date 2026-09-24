"""Walidacja TR1 drugą drogą (bramka 16a). Uruchomienie:
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_ts-poza-proba/walidacja.py

(1) Faza 0 TR1 przeliczona niezależnie (pętla w pandas po słownikach pozycji, bez ts_momentum).
(2) Rozłączność składów TR1 i top-20 w każdym miesiącu.
(3) Korelacja dziennych szeregów netto TS1 i TR1 (jak bardzo to NIEZALEŻNA replikacja).
"""

import numpy as np
import pandas as pd

from backtest.rebalance_premium import load_universe, monthly_members
from backtest.run_ts_momentum_oos import members_rank_band
from backtest.ts_momentum import portfolio
from backtest.xs_momentum import daily_funding_panel

U = "data/raw/universe"
FEE = 0.0007
lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")
close, volume = load_universe(U)
close = close[(close.index >= lo) & (close.index < end)]
volume = volume[(volume.index >= lo) & (volume.index < end)]
fund = daily_funding_panel(U).reindex(index=close.index, columns=close.columns).fillna(0.0)
months = [m for m in pd.date_range("2021-05-01", "2026-07-01", freq="MS", tz="UTC") if m < end]
band = members_rank_band(volume, months)
top20 = monthly_members(volume, months)
start = months[0]

ret = close.pct_change(fill_method=None)
forms = list(close.index[close.index >= start][::7])
pos: dict[str, float] = {}
rows = []
for k, t in enumerate(forms):
    m = max(x for x in months if x <= t)
    valid = []
    for s in band[m]:
        c = close[s]
        a, b = c.get(t, np.nan), c.get(t - pd.Timedelta(days=28), np.nan)
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        sig = np.sign(a / b - 1)
        r = ret[s].loc[:t].dropna()
        if sig == 0 or len(r) < 30:
            continue
        wts = (1 - 1 / 61) ** np.arange(len(r))[::-1]
        vol = np.sqrt(365 * np.sum(wts * r.to_numpy() ** 2) / np.sum(wts))
        valid.append((s, sig, vol))
    new = {s: sig * min(3.0, 0.40 / vol) / len(valid) for s, sig, vol in valid}
    turnover = sum(abs(new.get(x, 0) - pos.get(x, 0)) for x in set(new) | set(pos))
    pos = dict(new)
    nxt = forms[k + 1] if k + 1 < len(forms) else close.index[-1]
    for j, d in enumerate(close.index[(close.index > t) & (close.index <= nxt)]):
        rr = {s: (0.0 if not np.isfinite(ret.at[d, s]) else ret.at[d, s]) for s in pos}
        g = sum(w * rr[s] for s, w in pos.items())
        f = -sum(w * fund.at[d, s] for s, w in pos.items())
        rows.append((d, g + f - (FEE * turnover if j == 0 else 0.0)))
        pos = {s: w * (1 + rr[s]) / (1 + g) for s, w in pos.items()}
ph0 = pd.Series(dict(rows))
_, phases = portfolio(close, fund, band, start, end, FEE)
print(
    f"(1) TR1 faza 0 niezależnie: {100 * ph0.mean() * 365:+.2f}%/rok; silnik: {100 * phases[0]['net'].mean() * 365:+.2f}%/rok"
)
overlap = sum(len(set(band[m]) & set(top20[m])) for m in months)
print(f"(2) wspólne monety TR1 ∩ top-20 łącznie po miesiącach: {overlap} (oczekiwane 0)")
tr1, _ = portfolio(close, fund, band, start, end, FEE)
ts1, _ = portfolio(close, fund, monthly_members(volume, months), start, end, FEE)
j = (
    tr1.dropna()
    .set_index("date")[["net"]]
    .join(ts1.dropna().set_index("date")[["net"]], rsuffix="_ts1", how="inner")
)
rho = float(np.corrcoef(j["net"], j["net_ts1"])[0, 1])
print(
    f"(3) korelacja dzienna TR1 z TS1 (ten sam okres od 2021-05, top-20): {rho:+.2f} na {len(j)} dniach; "
    f"TS1 w tym okresie {100 * j['net_ts1'].mean() * 365:+.1f}%/rok; różnica TR1 − TS1 {100 * (j['net'] - j['net_ts1']).mean() * 365:+.1f}%/rok"
)
