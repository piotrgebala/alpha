"""MX2 — bramka 16a: druga droga NIEZALEŻNA od agents/ta_macd.py, agents/mx_filters.py
i agents/feature_miner.py: sygnały MX1 i pięć filtrów liczone wprost (TA-Lib + numpy/pandas)
w oknie populacji [2021-03-02, 2026-06-16); porównanie z `moc.txt` (sygnały + bramka kosztowa).
Czerwona flaga: filtr RSI przepuścił 100 % — rozkład RSI na świecach sygnału pokazuje, czy to
błąd, czy własność sygnału.

    PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-25_mx2-filtry-1h/druga_droga.py
"""

import numpy as np
import pandas as pd
import talib

from backtest.checkpoint_lib import fetch_window, load_config

df = fetch_window(load_config()["data"], "1h")
ts = pd.to_datetime(df["timestamp"], utc=True)
c, h, lo, v = (df[k].to_numpy(float) for k in ("close", "high", "low", "volume"))
win = (
    (ts >= pd.Timestamp("2021-03-02", tz="UTC")) & (ts < pd.Timestamp("2026-06-16", tz="UTC"))
).to_numpy()

s = np.sign(talib.EMA(c, 10) - talib.EMA(c, 30))
prev = np.r_[np.nan, s[:-1]]
cross = (s != prev) & ~np.isnan(s) & ~np.isnan(prev) & (s != 0)
_, _, hist = talib.MACD(c, 12, 26, 9)
hs = np.sign(hist)
mx = cross & (hs == s) & (np.r_[np.nan, hs[:-1]] == s) & win

ret28 = np.full(len(c), np.nan)
ret28[672:] = c[672:] / c[:-672] - 1
adx = talib.ADX(h, lo, c, 14)
vol_avg = pd.Series(v).rolling(20).mean().to_numpy()
rsi = talib.RSI(c, 14)
hour = ts.dt.hour.to_numpy()

filters = {
    "trend 28 dni zgodny": np.sign(ret28) == s,
    "ADX(14) > 25": adx > 25,
    "wolumen > średnia 20": v > vol_avg,
    "sesja USA 13–21 UTC": (hour >= 13) & (hour <= 20),
    "RSI(14) po stronie 50": ((s > 0) & (rsi > 50)) | ((s < 0) & (rsi < 50)),
}
print(f"MX1 w oknie (TA-Lib): {mx.sum()} (moc: 1254 + bramka)")
for name, f in filters.items():
    print(f"  {name:>24}: {(mx & f).sum():5d} (moc: sygnały + bramka)")
lr, sr = rsi[mx & (s > 0)], rsi[mx & (s < 0)]
print(
    f"RSI(14) na świecach sygnału: long min {lr.min():.1f} / mediana {np.median(lr):.1f}; "
    f"short max {sr.max():.1f} / mediana {np.median(sr):.1f}"
)
