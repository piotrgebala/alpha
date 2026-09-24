"""Walidacja SZ1: (1) R0 przeliczone wprost numpy (średnia składowych, CAGR, max obsunięcie) bez
backtest.sizing; (2) zrealizowana zmienność R1 wobec celu 20 %; (3) epizody hamulca R2.
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-24_sz1-wielkosc-pozycji/walidacja.py
"""

import numpy as np

from backtest.run_sizing_sz1 import components
from backtest.sizing import apply_rules

rets, expo = components()
x = rets.to_numpy().mean(axis=1)
eq = np.cumprod(1 + x)
cagr = eq[-1] ** (365 / len(x)) - 1
dd = np.max(1 - eq / np.maximum.accumulate(eq))
print(f"(1) R0 niezależnie: CAGR {100 * cagr:+.1f}%, max obsunięcie {100 * dd:.1f}%")
r1 = apply_rules(rets, "R1")
print(
    f"(2) R1 zrealizowana zmienność po rozbiegu: {100 * r1['ret'].iloc[60:].std() * np.sqrt(365):.1f}%/rok (cel 20 %)"
)
r2 = apply_rules(rets, "R2").set_index("date")
b = r2["brake"].astype(int).diff().fillna(0)
on = list(r2.index[b == 1].date)
off = list(r2.index[b == -1].date)
print(f"(3) R2 włączenia hamulca: {on}; wyłączenia: {off}")
