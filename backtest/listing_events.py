"""
listing_events.py — rozliczenie SHORTA na nowym kontrakcie (runda NL1): wejście po cenie
otwarcia dnia d0+1 (pierwszy pełny dzień po dniu listingu), wyjście po zamknięciu dnia d0+HOLD
(czyli HOLD pełnych świec 1d: d0+1 … d0+HOLD), P&L na jednostkę nominału.

- Likwidacja izolowana przy dźwigni L: gdy najwyższa cena w oknie ≥ wejście·(1 + 1/L − MMR),
  pozycja traci cały depozyt → P&L = −1/L (w jednostkach nominału), bez fundingu po tym dniu.
- Funding: short OTRZYMUJE dodatnią stawkę (i płaci ujemną) — suma stawek z rozliczeń
  w (wejście, wyjście]; przy likwidacji do końca dnia likwidacji.
- Koszt: `cost_per_side` × 2 (wejście i wyjście taker + poślizg), także przy likwidacji
  (konserwatywnie).
- Kontrakt wycofany w oknie (brak świec do d0+HOLD): wyjście po ostatnim zamknięciu.
Testy: `tests/test_listing_events.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HOLD_DAYS = 14
MMR = 0.025  # podtrzymujący depozyt świeżych kontraktów (exchangeInfo, ~2,5 %)


def liquidation_move(leverage: float, mmr: float = MMR) -> float:
    """Wzrost ceny (ułamek), przy którym izolowany short z dźwignią L jest likwidowany."""
    return 1.0 / leverage - mmr


def short_event_pnl(
    klines: pd.DataFrame,
    funding: pd.DataFrame,
    d0: pd.Timestamp,
    leverage: float = 1.0,
    cost_per_side: float = 0.0007,
    hold: int = HOLD_DAYS,
) -> dict | None:
    """
    `klines`: open_time (UTC, dzienne), open, high, low, close — jednego symbolu.
    `funding`: timestamp (UTC), funding_rate — jednego symbolu (może być pusty).
    Zwraca dict (pnl, price_ret, funding, cost, liquidated, days, entry, max_up) albo None,
    gdy brak świecy d0+1 (zdarzenie nierozliczalne).
    """
    k = klines.sort_values("open_time")
    start = d0 + pd.Timedelta(days=1)
    w = k[(k["open_time"] >= start) & (k["open_time"] < start + pd.Timedelta(days=hold))]
    if w.empty or w["open_time"].iloc[0] != start:
        return None
    entry = float(w["open"].iloc[0])
    if not np.isfinite(entry) or entry <= 0:
        return None
    ups = w["high"].to_numpy(dtype=float) / entry - 1.0
    liq = liquidation_move(leverage)
    hit = np.nonzero(ups >= liq)[0]
    cost = 2.0 * cost_per_side

    def _fund(lo: pd.Timestamp, hi: pd.Timestamp) -> float:
        if len(funding) == 0:
            return 0.0
        ts = funding["timestamp"]
        return float(funding.loc[(ts > lo) & (ts <= hi), "funding_rate"].sum())

    if len(hit):
        last_day = w["open_time"].iloc[hit[0]]
        end_t = last_day + pd.Timedelta(days=1)
        fund = _fund(start, end_t)
        return {
            "pnl": -1.0 / leverage + fund - cost,
            "price_ret": float(ups[hit[0]]),
            "funding": fund,
            "cost": cost,
            "liquidated": True,
            "days": int(hit[0]) + 1,
            "entry": entry,
            "max_up": float(ups.max()),
        }
    exit_ = float(w["close"].iloc[-1])
    end_t = w["open_time"].iloc[-1] + pd.Timedelta(days=1)
    fund = _fund(start, end_t)
    price_ret = exit_ / entry - 1.0
    return {
        "pnl": -price_ret + fund - cost,
        "price_ret": price_ret,
        "funding": fund,
        "cost": cost,
        "liquidated": False,
        "days": len(w),
        "entry": entry,
        "max_up": float(ups.max()),
    }


def cluster_mean_ci(values: pd.Series, clusters: pd.Series, z: float = 1.959964) -> dict:
    """
    Średnia z błędem odpornym na klastry (CR1: suma reszt w klastrze, korekta G/(G−1)).
    Zdarzenia z tego samego miesiąca listingu nakładają się w czasie i są skorelowane.
    """
    x = values.astype(float).to_numpy()
    g = clusters.to_numpy()
    n = len(x)
    mean = float(x.mean())
    resid = pd.Series(x - mean).groupby(g).sum().to_numpy()
    n_cl = len(resid)
    var = (n_cl / (n_cl - 1)) * float((resid**2).sum()) / n**2 if n_cl > 1 else float("nan")
    se = float(np.sqrt(var))
    se_iid = float(x.std(ddof=1) / np.sqrt(n))
    return {
        "n": n,
        "clusters": n_cl,
        "mean": mean,
        "median": float(np.median(x)),
        "sd": float(x.std(ddof=1)),
        "se": se,
        "se_iid": se_iid,
        "design_effect": (se / se_iid) ** 2 if se_iid > 0 else float("nan"),
        "t": mean / se if se > 0 else float("nan"),
        "ci_low": mean - z * se,
        "ci_high": mean + z * se,
    }
