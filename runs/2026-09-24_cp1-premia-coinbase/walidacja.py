"""Walidacja CP1 (bramka 16a) — pierwszy POZYTYWNY projektu, więc szukamy błędu. Uruchomienie:
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_cp1-premia-coinbase/walidacja.py

(1) Czas: premia z zamknięć o tej samej chwili? korelacja dziennych zmian Coinbase vs perp na
    lagach −1/0/+1 (maks. przy 0 = zgodne znaczniki).
(2) Test przecieku: sygnał opóźniony o 1 i 2 dni (gorsza informacja) — przy przecieku wynik
    zapada się do zera; bez przecieku zmienia się łagodnie.
(3) Faza 0 niezależnie (pętla pandas po dniach, własne σ̂, bez ts_momentum).
(4) Czy to trend: regresja dziennych zwrotów CP1 na trend-28 BTC (alfa, beta); przed/po 2024-01-11 (ETF).
(5) Koncentracja: bez 10 najlepszych dni; mediana.
"""

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.run_coinbase_cp1 import _load
from backtest.ts_momentum import portfolio

fee, close, funding, members, signs, prem, start, end = _load()
cb = pd.read_parquet("data/raw/external/coinbase_BTC-USD_1d.parquet")
cbc = cb.set_index(pd.to_datetime(cb["open_time"], utc=True))["close"].pct_change()
pr = close["BTCUSDT"].pct_change()
j = pd.concat([cbc.rename("cb"), pr.rename("perp")], axis=1).dropna()
print(
    "(1) korelacja zmian Coinbase(d) z perp(d+k): "
    + ", ".join(f"k={k}: {j['cb'].corr(j['perp'].shift(-k)):+.3f}" for k in (-1, 0, 1))
)


def run(sig):
    a, _ = portfolio(
        close, funding, members, start, end, fee, signs_override=pd.DataFrame({"BTCUSDT": sig})
    )
    return a.dropna()


base = run(signs["BTCUSDT"])
for lag in (1, 2):
    a = run(signs["BTCUSDT"].shift(lag))
    w = summarize_pnl(a["net"], periods_per_year=365, capital_per_notional=1.0)
    print(
        f"(2) sygnał opóźniony o {lag} d: {100 * w['mean'] * 365:+.1f}%/rok, t_neff {w['t_neff']:+.2f}"
    )

# (3) faza 0 niezależnie
r = close["BTCUSDT"].pct_change()
f = funding["BTCUSDT"].reindex(close.index).fillna(0.0)
s = signs["BTCUSDT"]
days = list(close.index[close.index >= start])
forms = set(days[::7])
w_pos, cost_next, out = 0.0, 0.0, []
for i, d in enumerate(days):
    if i > 0 and w_pos != 0.0 or cost_next:
        g = w_pos * (0.0 if np.isnan(r[d]) else r[d])
        out.append((d, g - w_pos * f[d] - cost_next))
        cost_next = 0.0
        w_pos = w_pos * (1 + (0.0 if np.isnan(r[d]) else r[d])) / (1 + g)
    elif i > 0:
        out.append((d, 0.0))
    if d in forms:
        hist = r.loc[:d].dropna()
        wts = (1 - 1 / 61) ** np.arange(len(hist))[::-1]
        vol = np.sqrt(365 * np.sum(wts * hist.to_numpy() ** 2) / np.sum(wts))
        new = 0.0 if not np.isfinite(s[d]) or s[d] == 0 else s[d] * min(3.0, 0.40 / vol)
        cost_next = fee * abs(new - w_pos)
        w_pos = new
ph0 = pd.Series(dict(out))
_, phases = portfolio(close, funding, members, start, end, fee, signs_override=signs)
print(
    f"(3) faza 0 niezależnie: {100 * ph0.mean() * 365:+.2f}%/rok; silnik: {100 * phases[0]['net'].mean() * 365:+.2f}%/rok"
)

# (4) trend
ts, _ = portfolio(close, funding, members, start, end, fee)
jj = base.set_index("date")[["net"]].join(
    ts.dropna().set_index("date")[["net"]], rsuffix="_ts", how="inner"
)
beta = np.cov(jj["net"], jj["net_ts"])[0, 1] / jj["net_ts"].var()
resid = jj["net"] - beta * jj["net_ts"]
wr = summarize_pnl(resid, periods_per_year=365, capital_per_notional=1.0)
print(
    f"(4) beta wobec trendu-28 BTC {beta:+.2f}; alfa (reszta) {100 * wr['mean'] * 365:+.1f}%/rok [{100 * wr['ci_low'] * 365:+.1f}; {100 * wr['ci_high'] * 365:+.1f}], t_neff {wr['t_neff']:+.2f}"
)
etf = pd.Timestamp("2024-01-11", tz="UTC")
for name, m in (("przed ETF", base["date"] < etf), ("po ETF", base["date"] >= etf)):
    w = summarize_pnl(base.loc[m, "net"], periods_per_year=365, capital_per_notional=1.0)
    print(
        f"    {name}: {w['n']} dni, {100 * w['mean'] * 365:+.1f}%/rok [{100 * w['ci_low'] * 365:+.1f}; {100 * w['ci_high'] * 365:+.1f}]"
    )

x = np.sort(base["net"].to_numpy())
print(
    f"(5) bez 10 najlepszych dni: {100 * x[:-10].mean() * 365:+.1f}%/rok; mediana dnia {100 * np.median(x):+.3f}% vs średnia {100 * x.mean():+.3f}%; dni > 0: {100 * (x > 0).mean():.1f}%"
)
