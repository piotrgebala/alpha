"""
run_au4_dsr.py — runda AU4 (audyt, 0 wariantów): deflated Sharpe ratio premii Coinbase (CP1).

Pytanie: czy Sharpe CP1 jest wyższy, niż dałby najlepszy z N pustych pomysłów sprawdzonych na tych
samych danych? Wzór Bailey & López de Prado (2014):
    SR0 = √V · ((1 − γ) Φ⁻¹(1 − 1/N) + γ Φ⁻¹(1 − 1/(N e)))      (oczekiwane maksimum N Sharpe'ów pod H0)
    DSR = Φ( (SR − SR0) √(T − 1) / √(1 − g3·SR + (g4 − 1)/4 · SR²) )
SR, V, SR0 w jednostkach dziennych; V = 1/T (wariancja estymatora Sharpe'a pod H0, próby o tej samej
długości); g3 skośność, g4 kurtoza (nie nadwyżkowa) dziennych zwrotów netto CP1. T = liczba dni albo
N_eff (autokorelacja). Szereg CP1 tą samą drogą co `run_coinbase_cp1` (reguła zamrożona).
Siatka N i reguła odczytu ZAMROŻONE w `runs/2026-09-25_au4-dsr-cp1/README.md`.

    PYTHONUTF8=1 py -m backtest.run_au4_dsr
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

from backtest.carry_hedged import summarize_pnl
from backtest.run_coinbase_cp1 import _load
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio

EULER_GAMMA = 0.5772156649
N_GRID = (5, 10, 20, 28, 40)
SEP = "=" * 104


def expected_max_sr(n_trials: int, var_sr: float) -> float:
    """Oczekiwane maksimum N niezależnych Sharpe'ów o wariancji `var_sr` przy prawdziwym SR = 0."""
    if n_trials <= 1:
        return 0.0
    g = EULER_GAMMA
    return float(
        np.sqrt(var_sr)
        * ((1 - g) * norm.ppf(1 - 1 / n_trials) + g * norm.ppf(1 - 1 / (n_trials * np.e)))
    )


def deflated_sharpe(sr: float, sr0: float, t: float, g3: float, g4: float) -> float:
    """P(prawdziwy SR > SR0) z poprawką na długość próby, skośność i kurtozę (Bailey & LdP 2014)."""
    den = np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr**2)
    return float(norm.cdf((sr - sr0) * np.sqrt(t - 1) / den))


def cp1_daily() -> pd.Series:
    """Dzienne zwroty netto CP1 (średnia 7 faz), dokładnie jak w rundzie CP1."""
    fee, close, funding, members, signs, _prem, start, end = _load()
    avg, _ = portfolio(close, funding, members, start, end, fee, signs_override=signs)
    return avg.dropna().set_index("date")["net"]


def main() -> None:
    x = cp1_daily()
    t = len(x)
    sr = float(x.mean() / x.std(ddof=1))
    g3, g4 = float(skew(x)), float(kurtosis(x, fisher=False))
    w = summarize_pnl(x, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    t_eff = float(w["n_eff"])
    print(SEP)
    print("AU4 — deflated Sharpe premii Coinbase (CP1); reguła CP1 bez zmian")
    print(SEP)
    print(
        f"  CP1: {t} dni, średnia {100 * x.mean() * DAYS_PER_YEAR:+.1f}%/rok, SR dzienny {sr:.4f} "
        f"(roczny {sr * np.sqrt(DAYS_PER_YEAR):.2f}), t = SR·√T {sr * np.sqrt(t):.2f}, t_neff {w['t_neff']:.2f}, "
        f"N_eff {t_eff:.0f}; skośność {g3:+.2f}, kurtoza {g4:.1f}"
    )
    print(
        "  N prób | próg SR0 (roczny) | oczekiwane max t pod H0 | DSR (T = dni) | DSR (T = N_eff)"
    )
    for n in N_GRID:
        for tt, lab in ((t, "dni"), (t_eff, "neff")):
            sr0 = expected_max_sr(n, 1.0 / tt)
            d = deflated_sharpe(sr, sr0, tt, g3, g4)
            if lab == "dni":
                row = f"  {n:6d} | {sr0 * np.sqrt(DAYS_PER_YEAR):17.2f} | {sr0 * np.sqrt(tt):23.2f} | {d:13.3f}"
            else:
                row += f" | {d:15.3f}"
        print(row)
    print(SEP)


if __name__ == "__main__":
    main()
