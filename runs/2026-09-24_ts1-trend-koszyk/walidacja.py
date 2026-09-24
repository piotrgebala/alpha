"""Walidacja TS1 drugą drogą (bramka 16a). Uruchomienie:
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_ts1-trend-koszyk/walidacja.py

(1) Faza 0 przeliczona NIEZALEŻNIE: pętla w pandas po słownikach pozycji (bez funkcji
    ts_momentum), własny sygnał, własne σ̂, własny dryf — porównanie z +12,1 %/rok z raw_output.
(2) CI średniej z bootstrapu blokowego (bloki 28 dni) — trzecia droga obok t i H0.
(3) Wrażliwość: bez 10 najlepszych dni; kogo nie ma (członkowie bez znaku/σ̂, wycofani).
"""

import numpy as np
import pandas as pd

from backtest.rebalance_premium import load_universe, monthly_members
from backtest.ts_momentum import portfolio
from backtest.xs_momentum import daily_funding_panel

U = "data/raw/universe"
FEE = 0.0005 + 0.0002
lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")
start = pd.Timestamp("2021-02-01", tz="UTC")
close, volume = load_universe(U)
close = close[(close.index >= lo) & (close.index < end)]
volume = volume[(volume.index >= lo) & (volume.index < end)]
fund = daily_funding_panel(U).reindex(index=close.index, columns=close.columns).fillna(0.0)
months = [m for m in pd.date_range("2021-02-01", "2026-07-01", freq="MS", tz="UTC") if m < end]
members = monthly_members(volume, months)

# (1) faza 0 niezależnie
ret = close.pct_change(fill_method=None)
days = list(close.index[close.index >= start])
forms = days[::7]
# jawna pętla: formowanie w dniu t, zwroty t+1..następne formowanie
pos: dict[str, float] = {}
rows = []
for k, t in enumerate(forms):
    m = max(x for x in months if x <= t)
    valid = []
    for s in members[m]:
        c = close[s]
        if not (
            np.isfinite(c.get(t, np.nan)) and np.isfinite(c.get(t - pd.Timedelta(days=28), np.nan))
        ):
            continue
        sig = np.sign(c[t] / c[t - pd.Timedelta(days=28)] - 1)
        r = ret[s].loc[:t].dropna()
        if sig == 0 or len(r) < 30:
            continue
        alpha = 1 / 61
        w_ = (1 - alpha) ** np.arange(len(r))[::-1]
        vol = np.sqrt(365 * np.sum(w_ * r.to_numpy() ** 2) / np.sum(w_))
        valid.append((s, sig, vol))
    new = {s: sig * min(3.0, 0.40 / vol) / len(valid) for s, sig, vol in valid}
    turnover = sum(abs(new.get(x, 0) - pos.get(x, 0)) for x in set(new) | set(pos))
    pos = dict(new)
    nxt = forms[k + 1] if k + 1 < len(forms) else close.index[-1]
    hold = close.index[(close.index > t) & (close.index <= nxt)]
    for j, d in enumerate(hold):
        g = sum(
            w * (0.0 if not np.isfinite(ret.at[d, s]) else ret.at[d, s]) for s, w in pos.items()
        )
        f = -sum(w * fund.at[d, s] for s, w in pos.items())
        c = FEE * turnover if j == 0 else 0.0
        rows.append((d, g + f - c))
        pos = {
            s: w * (1 + (0.0 if not np.isfinite(ret.at[d, s]) else ret.at[d, s])) / (1 + g)
            for s, w in pos.items()
        }
ph0 = pd.Series(dict(rows))
print(
    f"(1) faza 0 niezależnie: {len(ph0)} dni, średnia {100 * ph0.mean() * 365:+.2f}%/rok "
    f"(raw_output: +12.1%/rok)"
)

# (2) bootstrap blokowy dla portfela 7 faz
avg, phases = portfolio(close, fund, members, start, end, FEE)
avg = avg.dropna()
x = avg["net"].to_numpy()
rng = np.random.default_rng(0)
B, L = 5000, 28
nb = int(np.ceil(len(x) / L))
boots = np.empty(B)
for b in range(B):
    idx = np.concatenate([np.arange(s, s + L) % len(x) for s in rng.integers(0, len(x), nb)])[
        : len(x)
    ]
    boots[b] = x[idx].mean()
lo_b, hi_b = np.quantile(boots, [0.025, 0.975])
print(
    f"(2) bootstrap blokowy (bloki {L} dni, {B}): średnia {100 * x.mean() * 365:+.1f}%/rok, "
    f"CI 95% [{100 * lo_b * 365:+.1f}; {100 * hi_b * 365:+.1f}]%/rok; udział bootstrapów ≤ 0: {100 * (boots <= 0).mean():.1f}%"
)

# (3) wrażliwość i „kogo nie ma"
top10 = np.sort(x)[-10:]
print(
    f"(3) bez 10 najlepszych dni: {100 * (x.sum() - top10.sum()) / len(x) * 365:+.1f}%/rok; "
    f"bez 10 najgorszych: {100 * (x.sum() - np.sort(x)[:10].sum()) / len(x) * 365:+.1f}%/rok"
)
first_common = avg["date"].min()
print(f"    pierwszy dzień z pozycją wszystkich faz: {pd.Timestamp(first_common).date()}")
delisted = [
    s
    for s in set().union(*members.values())
    if close[s].loc[: end - pd.Timedelta(days=1)].last_valid_index() < end - pd.Timedelta(days=2)
]
print(
    f"    członkowie koszyka wycofani przed końcem próby (po wycofaniu = gotówka): {len(delisted)}: {sorted(delisted)[:12]}"
)
print(
    f"    dni z dodatnim netto: {100 * (x > 0).mean():.1f}%; mediana {100 * np.median(x):+.3f}%/dzień vs średnia {100 * x.mean():+.3f}%/dzień"
)
