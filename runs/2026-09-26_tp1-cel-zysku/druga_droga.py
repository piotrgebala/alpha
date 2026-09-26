"""TP1 — bramka 16a: druga droga NIEZALEŻNA od backtest/take_profit.py.

(1) Ile pozycji premii Coinbase (BTC, 7 faz) dotyka celu +1 % / +2 % w oknie trzymania — liczone
    wprost z dziennych maksimów/minimów (bez silnika), porównanie z `moc.txt` (1 659 / 1 470);
    różnica może wynikać tylko z likwidacji przed celem (moc: 4–7) i skróconego ostatniego okna.
(2) Szum różnicy przy równym ryzyku analitycznie: sd ≈ σ·√(2(1 − ρ)) z korelacji z `moc.txt`
    i zmienności docelowej 20 %/rok — rząd wielkości ± (z_4) bez silnika.

    PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-26_tp1-cel-zysku/druga_droga.py
"""

import numpy as np
import pandas as pd

from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.ts_momentum import PHASES, formation_dates

fee, close, fund, members, signs, _p, start, end = load_cp()
close = close[close.index < end]["BTCUSDT"]
o = pd.read_parquet("data/raw/universe_ohlc_full/ohlc_1d.parquet")
o = o[o["symbol"] == "BTCUSDT"].copy()
o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
o = o.set_index("open_time").reindex(close.index)
sig = signs["BTCUSDT"].reindex(close.index)
for tp in (0.01, 0.02):
    lots = hits = 0
    for ph in range(PHASES):
        dates = formation_dates(close.index, start, end, ph)
        for k, t in enumerate(dates):
            s = sig.loc[t]
            if not np.isfinite(s) or s == 0:
                continue
            lots += 1
            t_end = dates[k + 1] if k + 1 < len(dates) else close.index[-1]
            win = o.loc[(o.index > t) & (o.index <= t_end)]
            entry = close.loc[t]
            if s > 0 and (win["high"] >= entry * (1 + tp)).any():
                hits += 1
            elif s < 0 and (win["low"] <= entry * (1 - tp)).any():
                hits += 1
    print(f"CP1 cel {100 * tp:.0f}%: pozycji {lots}, dotyka celu {hits} ({100 * hits / lots:.0f}%)")
z4, years = 2.498, None
for name, tp, rho, n in (
    ("TS1", 1, 0.55, 1969),
    ("TS1", 2, 0.64, 1969),
    ("CP1", 1, 0.60, 1880),
    ("CP1", 2, 0.66, 1880),
):
    sd = 0.20 * np.sqrt(2 * (1 - rho))
    print(
        f"{name} cel {tp}%: sd różnicy ≈ {100 * sd:.1f}%/rok → ± (z_4) ≈ {100 * z4 * sd / np.sqrt(n / 365):.1f} pp/rok"
    )
