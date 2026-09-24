"""Walidacja TL1 drugą drogą: tygodniowa korelacja rang (Spearman) crowd vs zwrot następnych 7 dni
wśród członków top-20 — bez silnika X1. Znak średniego IC powinien zgadzać się ze znakiem wyniku
(strata strategii long-niski/short-wysoki ⇔ IC > 0).
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_tl1-tlok-przekrojowy/walidacja.py
"""

import numpy as np
import pandas as pd

from backtest.run_crowding_tl1 import _load, crowd_panel

fee, close, funding, members, oi, start, end = _load()
crowd = crowd_panel(oi, close)
fwd = close.shift(-7) / close - 1.0
ics = []
for t in close.index[(close.index >= start) & (close.index < end - pd.Timedelta(days=7))][::7]:
    m = max(x for x in members if x <= t)
    syms = [s for s in members[m] if s in crowd.columns]
    a = pd.concat([crowd.loc[t, syms], fwd.loc[t, syms]], axis=1).dropna()
    if len(a) >= 10:
        ics.append(a.iloc[:, 0].rank().corr(a.iloc[:, 1].rank()))
ics = np.array(ics)
se = ics.std(ddof=1) / np.sqrt(len(ics))
print(
    f"IC tygodniowe (faza 0): n {len(ics)}, średnia {ics.mean():+.4f} [{ics.mean() - 1.96 * se:+.4f}; {ics.mean() + 1.96 * se:+.4f}], udział > 0 {100 * (ics > 0).mean():.1f}%"
)
