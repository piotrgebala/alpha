"""
sizing.py — reguły wielkości pozycji dla portfela strategii (runda SZ1). Wejście: dzienne zwroty
netto składowych przy mnożniku k = 1 (kolumny DataFrame). Wyjście: dzienny zwrot portfela
Σ k_s · r_s z mnożnikami k_s ustalanymi co `step` dni WYŁĄCZNIE z danych sprzed dnia ustalenia.

Reguły (zapisane z góry w `runs/2026-09-24_sz1-wielkosc-pozycji/README.md`):
- R0: k = 1/S dla każdej z S składowych (równy podział kapitału);
- R1: budżet ryzyka — wagi ∝ 1/σ_s, potem skala tak, by przewidywana zmienność portfela
  (kowariancja EWMA) = `target_vol`; każdy k_s ≤ `cap` (zasada 5: sufit wygrywa, `min()`);
  przed zebraniem `warmup` dni — jak R0;
- R2: R1 + hamulec obsunięcia z histerezą: gdy obsunięcie kapitału portfela > `dd_on`,
  mnożniki × `brake_factor` do czasu, aż obsunięcie spadnie poniżej `dd_off`.
Testy: `tests/test_sizing.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DAYS_PER_YEAR = 365


def _ewma_cov(x: pd.DataFrame, com: float) -> np.ndarray:
    return x.ewm(com=com).cov().iloc[-len(x.columns) :].to_numpy()


def apply_rules(
    returns: pd.DataFrame,
    rule: str,
    target_vol: float = 0.20,
    cap: float = 2.0,
    com: float = 45.0,
    warmup: int = 60,
    step: int = 7,
    dd_on: float = 0.15,
    dd_off: float = 0.075,
    brake_factor: float = 0.5,
) -> pd.DataFrame:
    """Dzienny szereg portfela wg reguły R0/R1/R2 + mnożniki i stan hamulca."""
    r = returns.fillna(0.0)
    n, s = r.shape
    k = np.full(s, 1.0 / s)
    brake = False
    equity, peak = 1.0, 1.0
    rows = []
    for i in range(n):
        if i % step == 0:
            if rule in ("R1", "R2") and i >= warmup:
                cov = _ewma_cov(r.iloc[:i], com)
                sig = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
                w = (1.0 / sig) / (1.0 / sig).sum()
                pvol = float(np.sqrt(w @ cov @ w) * np.sqrt(DAYS_PER_YEAR))
                k = np.minimum(cap, w * target_vol / pvol) if pvol > 0 else np.zeros(s)
            elif rule == "R0" or i < warmup:
                k = np.full(s, 1.0 / s)
            if rule == "R2":
                dd = 1.0 - equity / peak
                if not brake and dd > dd_on:
                    brake = True
                elif brake and dd < dd_off:
                    brake = False
        k_eff = k * (brake_factor if (rule == "R2" and brake) else 1.0)
        ret = float(k_eff @ r.iloc[i].to_numpy())
        equity *= 1.0 + ret
        peak = max(peak, equity)
        rows.append((r.index[i], ret, *k_eff, brake))
    cols = ["date", "ret"] + [f"k_{c}" for c in r.columns] + ["brake"]
    return pd.DataFrame(rows, columns=cols)


def summary(ret: pd.Series) -> dict:
    """CAGR, zmienność, maksymalne obsunięcie, Calmar, najgorszy miesiąc."""
    x = ret.to_numpy(dtype=float)
    eq = np.cumprod(1.0 + x)
    years = len(x) / DAYS_PER_YEAR
    cagr = eq[-1] ** (1 / years) - 1 if eq[-1] > 0 else -1.0
    dd = float(np.max(1.0 - eq / np.maximum.accumulate(eq)))
    idx = ret.index if isinstance(ret.index, pd.DatetimeIndex) else pd.RangeIndex(len(x))
    monthly = (
        (1 + pd.Series(x, index=idx))
        .groupby((idx.tz_localize(None) if idx.tz is not None else idx).to_period("M"))
        .prod()
        - 1
        if isinstance(idx, pd.DatetimeIndex)
        else pd.Series([np.nan])
    )
    return {
        "cagr": float(cagr),
        "vol": float(x.std(ddof=1) * np.sqrt(DAYS_PER_YEAR)),
        "max_dd": dd,
        "calmar": float(cagr / dd) if dd > 0 else float("nan"),
        "worst_month": float(monthly.min()),
    }
