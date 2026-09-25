"""MX1 — bramka 16a/16b: druga droga NIEZALEŻNA od agents/ta_macd.py i agents/ta_rules.py.

(1) sygnały przez TA-Lib (EMA/MACD z innym startem niż pandas) w oknie populacji
    [2021-03-02, 2026-06-16) = 69 okien testowych po 28 dni; porównanie z `moc.txt`
    (sygnały + odrzucone przez bramkę kosztową: MX1 1 254 + 2, samo EMA 1 623 + 3);
(2) mediana bariery 1,5·ATR(14, Wilder) na świecach sygnału i próg ±B = 0,5(1 + C/B);
(3) moc sprawdzianu: szansa potwierdzenia przy prawdziwej trafności 56/58/60 % i fałszywego
    pozytywu przy trafności równej progowi — dokładnie (dwumian), nie przybliżeniem.

    PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-25_mx1-macd-ema-1h/druga_droga.py
"""

import numpy as np
import pandas as pd
import talib
from scipy.stats import binom

from backtest.checkpoint_lib import fetch_window, load_config

df = fetch_window(load_config()["data"], "1h")
ts = pd.to_datetime(df["timestamp"], utc=True)
c = df["close"].to_numpy(float)
start, end = pd.Timestamp("2021-03-02", tz="UTC"), pd.Timestamp("2026-06-16", tz="UTC")
win = ((ts >= start) & (ts < end)).to_numpy()
print(f"świece w oknie populacji: {win.sum()} (moc.txt: 46368)")

s = np.sign(talib.EMA(c, 10) - talib.EMA(c, 30))
prev = np.r_[np.nan, s[:-1]]
cross = (s != prev) & ~np.isnan(s) & ~np.isnan(prev) & (s != 0)
_, _, hist = talib.MACD(c, 12, 26, 9)
h = np.sign(hist)
hp = np.r_[np.nan, h[:-1]]
mx = cross & (h == s) & (hp == s)
n_ema, n_mx = int((cross & win).sum()), int((mx & win).sum())
print(
    f"TA-Lib: przecięcia EMA 10/30 w oknie {n_ema} (moc: 1623 + 3 = 1626); MX1 {n_mx} (moc: 1254 + 2 = 1256)"
)
print(f"MACD przepuszcza {100 * n_mx / n_ema:.1f}% przecięć (moc: 77.3%)")

atr = talib.ATR(df["high"].to_numpy(float), df["low"].to_numpy(float), c, 14)
b = 1.5 * atr / c
b_med = float(np.nanmedian(b[mx & win]))
print(
    f"mediana bariery na świecach MX1: {100 * b_med:.3f}% (moc: 1.079%); próg ±B = {100 * 0.5 * (1 + 0.000808 / b_med):.2f}% (moc: 53.75%)"
)

n, p_ref = 1246, 0.5401
k_min = next(k for k in range(n + 1) if k / n - 1.96 * np.sqrt(k / n * (1 - k / n) / n) > p_ref)
print(
    f"potwierdzenie wymaga ≥ {k_min} trafień z {n} = {100 * k_min / n:.2f}% (Wald, jak kryterium)"
)
for p in (0.54, 0.5401, 0.56, 0.58, 0.60):
    print(
        f"  prawdziwa trafność {100 * p:5.2f}% → szansa potwierdzenia {100 * binom.sf(k_min - 1, n, p):5.1f}%"
    )
