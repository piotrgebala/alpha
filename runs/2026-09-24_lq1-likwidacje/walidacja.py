"""Walidacja LQ1: (1) liczba likwidacji fazy 0 policzona niezależnie (pandas: ruch przeciw pozycji
od zamknięcia dnia formowania z dziennych ekstremów do końca tygodnia, bez ts_momentum);
(2) zgodność zamknięć archiwum OHLC z cache uniwersum; (3) opisowo: dźwignia 2× (próg 49 %).
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_lq1-likwidacje/walidacja.py
"""

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.run_ts_liq_lq1 import load_extremes
from backtest.run_ts_momentum_ts1 import _load
from backtest.ts_momentum import build_formations, ewma_vol, formation_dates, portfolio, signal_sign

fee, close, funding, members, start, end = _load("data/raw/universe")
liq = load_extremes(close)
o = pd.read_parquet("data/raw/universe_ohlc/ohlc_1d.parquet")
o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
oc = o.pivot(index="open_time", columns="symbol", values="close").reindex(index=close.index, columns=close.columns)
both = (oc.notna() & close.notna()).to_numpy()
rel = np.abs(oc.to_numpy()[both] / close.to_numpy()[both] - 1)
print(
    f"(2) zamknięcia archiwum vs cache uniwersum: {both.sum()} par, max |różnica| {rel.max():.2e}, > 1e-6: {(rel > 1e-6).sum()}"
)

# (1) niezależne liczenie likwidacji fazy 0
dates = formation_dates(close.index, start, end, 0)
forms = build_formations(signal_sign(close), ewma_vol(close), members, dates)
thr = 1 / 3 - 0.01
n_liq = 0
for k, (t_pos, w) in enumerate(forms):
    t_next = forms[k + 1][0] if k + 1 < len(forms) else len(close) - 1
    entry = close.iloc[t_pos]
    win = slice(t_pos + 1, t_next + 1)
    for j in np.nonzero(w)[0]:
        s = close.columns[j]
        lo = liq["low"][s].iloc[win].min() / entry[s] - 1
        hi = liq["high"][s].iloc[win].max() / entry[s] - 1
        if (w[j] > 0 and -lo >= thr) or (w[j] < 0 and hi >= thr):
            n_liq += 1
_, ph = portfolio(close, funding, members, start, end, fee, liq=liq)
print(f"(1) likwidacje fazy 0: niezależnie {n_liq}, silnik {int(ph[0]['liquidations'].sum())}")

# (3) opisowo: 2x
liq2 = dict(liq, lev=2.0)
a2, _ = portfolio(close, funding, members, start, end, fee, liq=liq2)
w2 = summarize_pnl(a2.dropna()["net"], periods_per_year=365, capital_per_notional=1.0)
n2 = int(a2.dropna()["liquidations"].sum() * 7)
print(
    f"(3) opisowo 2x (depozyt = ekspozycja/2, próg 49 %): {100 * w2['mean'] * 365:+.1f}%/rok, t_neff {w2['t_neff']:+.2f}"
)
