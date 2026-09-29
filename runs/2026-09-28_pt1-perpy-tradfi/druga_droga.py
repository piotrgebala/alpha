"""PT1 — druga droga (bramka 16a): udziały zer i średnie roczne fundingu oraz `interestRate` Binance policzone
wprost z surowych plików, bez modułów rundy. Uruchom z katalogu repo: `py runs/2026-09-28_pt1-perpy-tradfi/druga_droga.py`.
"""

import glob
import gzip
import json
import pandas as pd

root = "data/raw/tradfi_perps"
fb = pd.read_parquet(glob.glob(f"{root}/funding_bybit*.parquet")[0])
print("kolumny funding_bybit:", list(fb.columns))
sym = [c for c in fb.columns if "sym" in c.lower()][0]
rate = [c for c in fb.columns if "rate" in c.lower()][0]
for s in ("EURUSDUSDT", "GBPUSDUSDT", "USDJPYUSDT", "XAUUSDT", "BTCUSDT"):
    x = fb.loc[fb[sym] == s, rate].astype(float)
    print(
        f"{s:12s} n={len(x):4d} udział_zer={(x == 0).mean():.3f} udział_0.0001={(x == 0.0001).mean():.3f} "
        f"średnia×odczyty/rok (8h→1095, XAU 4h→2190)={x.mean() * (2190 if s == 'XAUUSDT' else 1095) * 100:.2f}%"
    )
last = sorted(glob.glob(f"{root}/migawki/*.json.gz"))[-1]
snap = json.load(gzip.open(last, "rt"))
sb = pd.read_parquet(glob.glob(f"{root}/spis_binance*.parquet")[0])
tf = set(sb["symbol"]) - {"BTCUSDT"}
ir = pd.Series(
    {
        r["symbol"]: float(r["interestRate"])
        for r in snap["binance_premium"]
        if r["symbol"] in tf | {"BTCUSDT"}
    }
)
print(
    "migawka",
    last[-26:],
    "Binance interestRate TradFi:",
    ir.drop("BTCUSDT").value_counts().to_dict(),
    "BTC:",
    ir["BTCUSDT"],
)
