"""Przeliczenie D (statystyka walut) i A (udział zer, obrót) — własny kod, surowe pliki."""
import glob
import gzip
import json
import numpy as np
import pandas as pd

R = "data/raw/tradfi_perps"
fb = pd.read_parquet(f"{R}/funding_bybit.parquet")
fn = pd.read_parquet(f"{R}/funding_binance.parquet")

def seria(df, s):
    x = df[df.symbol == s].sort_values("czas")
    return x["czas"].reset_index(drop=True), x["fundingRate"].astype(float).reset_index(drop=True)

def acf1(x):
    x = np.asarray(x, float); d = x - x.mean()
    return float((d[:-1] * d[1:]).sum() / (d * d).sum()) if (d * d).sum() > 0 else float("nan")

def mbb(x, k, blok, B=20000, seed=1):
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / blok))
    st = rng.integers(0, n - blok + 1, size=(B, nb))
    idx = (st[:, :, None] + np.arange(blok)[None, None, :]).reshape(B, -1)[:, :n]
    m = x[idx].mean(axis=1) * k * 100
    return np.percentile(m, [2.5, 97.5])

for g, df, s in [("bybit", fb, "EURUSDUSDT"), ("bybit", fb, "GBPUSDUSDT"), ("bybit", fb, "USDJPYUSDT"), ("binance", fn, "USDBRLUSDT")]:
    t, x = seria(df, s)
    n = len(x); k = 8760 / ((t.iloc[-1] - t.iloc[0]).total_seconds() / 3600 / (n - 1))
    m = x.mean(); sd = x.std(ddof=1); zer = int((x == 0).sum())
    r1 = acf1(x)
    neff = n / (1 + 2 * r1) if np.isfinite(r1) and r1 > 0 else n
    hw = 1.959964 * sd / np.sqrt(neff) * k * 100
    bb = {b: mbb(x.to_numpy(), k, b) for b in (3, 5, 8)} if sd > 0 else {}
    print(f"{g} {s}: n={n} zer={zer}/{n} ({zer/n:.1%}) niezer={n-zer} k={k:.1f} f={m*k*100:+.4f}%/rok "
          f"rho1={r1:.3f} Neff(n/(1+2rho1))={neff:.1f} CI=[{m*k*100-hw:+.2f}; {m*k*100+hw:+.2f}] "
          + " ".join(f"MBB(b={b})=[{v[0]:+.2f}; {v[1]:+.2f}]" for b, v in bb.items()))
    if zer == n:
        print(f"   reguła trzech: górna granica udziału niezerowych ≈ 3/n = {3/n:.1%}")
    nz = x[x != 0]
    print("   niezerowe odczyty (%/8h):", (nz * 100).round(4).tolist()[:20])

# obrót 24 h walut Bybit z migawek (pierwsze 2 = te, na których stoi koszty.csv; potem wszystkie)
pl = sorted(glob.glob(f"{R}/migawki/*.json.gz"))
for zakres, lista in (("2 pierwsze", pl[:2]), (f"wszystkie {len(pl)}", pl)):
    ob = {}
    for p in lista:
        sn = json.load(gzip.open(p, "rt"))
        for r in sn["bybit_tickers"]["result"]["list"]:
            if r["symbol"] in ("EURUSDUSDT", "GBPUSDUSDT", "USDJPYUSDT"):
                ob.setdefault(r["symbol"], []).append(float(r["turnover24h"]))
    print(zakres, {k: f"{np.median(v)/1e3:.0f} tys." for k, v in ob.items()})
