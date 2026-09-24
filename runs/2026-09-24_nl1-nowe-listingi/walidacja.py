"""Walidacja NL1 drugą drogą (bramka 16a). Uruchomienie:
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_nl1-nowe-listingi/walidacja.py

(1) P&L 1× wszystkich zdarzeń WEKTOROWO z surowych plików (merge + groupby, bez listing_events).
(2) Błąd klastrowy po KWARTAŁACH (wrażliwość zapisana z góry) i po tygodniach.
(3) Rozkład: udział likwidacji 1×, wkład ogona, bez 5 % najgorszych.
"""

import numpy as np

from backtest.listing_events import cluster_mean_ci
from backtest.run_listings_nl1 import load_events

ev, kl, fu, _ = load_events()
COST = 2 * (0.0005 + 0.0002)
kl = kl.merge(ev[["symbol", "d0"]], on="symbol")
kl["day"] = (kl["open_time"] - kl["d0"]).dt.days
w = kl[(kl["day"] >= 1) & (kl["day"] <= 14)].sort_values(["symbol", "day"])
g = w.groupby("symbol")
entry = g["open"].first()
first_day = g["day"].first()
last_close = g["close"].last()
max_up = g["high"].max() / entry - 1
# dzień likwidacji 1× (wzrost ≥ 97,5 %) — pierwszy dzień, w którym high/entry − 1 ≥ 0,975
w = w.join(entry.rename("entry"), on="symbol")
w["liq"] = w["high"] / w["entry"] - 1 >= 0.975
liq_day = w[w["liq"]].groupby("symbol")["day"].min()
last_day = g["day"].last()
end_day = liq_day.reindex(last_day.index).fillna(last_day)
fu = fu.merge(ev[["symbol", "d0"]], on="symbol")
fu["h"] = (fu["timestamp"] - fu["d0"]).dt.total_seconds() / 86400
fu = fu.join(end_day.rename("end_day"), on="symbol")
fwin = fu[(fu["h"] > 1) & (fu["h"] <= fu["end_day"] + 1)].groupby("symbol")["funding_rate"].sum()
price = -(last_close / entry - 1)
price[liq_day.index] = -1.0
pnl = (price + fwin.reindex(price.index).fillna(0.0) - COST).rename("pnl")
assert (first_day == 1).all()
print(
    f"(1) wektorowo: n {len(pnl)}, średnia {100 * pnl.mean():+.2f}% (raw_output +2.12%), mediana {100 * pnl.median():+.2f}% (raw +13.54%), "
    f"likwidacje 1×: {len(liq_day)} ({100 * len(liq_day) / len(pnl):.1f}%)"
)

d = ev.set_index("symbol").loc[pnl.index, "d0"]
for name, cl in (
    ("miesiąc", d.dt.strftime("%Y-%m")),
    ("kwartał", d.dt.to_period("Q").astype(str)),
    ("rok", d.dt.year.astype(str)),
):
    r = cluster_mean_ci(pnl, cl.reset_index(drop=True).set_axis(pnl.index))
    print(
        f"(2) klastry {name}: {r['clusters']} klastrów, CI [{100 * r['ci_low']:+.2f}; {100 * r['ci_high']:+.2f}], t {r['t']:+.2f}"
    )

x = np.sort(pnl.to_numpy())
k = int(0.05 * len(x))
print(
    f"(3) bez 5% najgorszych ({k}): średnia {100 * x[k:].mean():+.2f}%; bez 5% najlepszych: {100 * x[:-k].mean():+.2f}%; "
    f"zdarzenia ≤ −50%: {int((x <= -0.5).sum())}, ich suma {100 * x[x <= -0.5].sum():+.0f}% vs suma reszty {100 * x[x > -0.5].sum():+.0f}%"
)
