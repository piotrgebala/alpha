"""E — koszty (WSTĘPNIE, 2 migawki): własne przeliczenie spreadu z migawek + odczyt koszty.csv."""
import glob
import gzip
import json
import numpy as np
import pandas as pd
R = "data/raw/tradfi_perps"
k = pd.read_csv("runs/2026-09-28_pt1-perpy-tradfi/koszty.csv")
rd = k[k.w_rdzeniu & (k.klasa != "BTC_kontrola")]
for g, d in rd.groupby("gielda"):
    nad = d[d.koszt_strony_proc > 0.07]
    print(f"{g}: rdzeń bez BTC {len(d)}, koszt > 0,07 %: {len(nad)} ->", ", ".join(f"{s.replace('USDT','')} {c:.3f}" for s, c in zip(nad.symbol, nad.koszt_strony_proc)),
          f"| mediana rdzenia {d.koszt_strony_proc.median():.4f}")
    niska = d.sort_values("obrot24h_med_usdt").head(6)
    print("   najmniejszy obrót (tys. USDT/dobę; spread pb):", ", ".join(f"{s.replace('USDT','')} {o/1e3:.0f} ({sp:.1f})" for s, o, sp in zip(niska.symbol, niska.obrot24h_med_usdt, niska.spread_pb_med)))
for (g, kl), d in k.groupby(["gielda", "klasa"]):
    if kl not in ("akcje", "ETF", "ETF_oblig"): continue
    print(f"{g:8s} {kl:10s} n={len(d):3d} spread med {d.spread_pb_med.median():5.1f} p90 {d.spread_pb_med.quantile(.9):5.1f} pb | koszt strony med {d.koszt_strony_proc.median():.4f} % | udział > KO1 {(d.koszt_strony_proc > 0.07).mean():.1%}")
# niezależnie: spread z surowych migawek (2 pierwsze) dla akcji
pl = sorted(glob.glob(f"{R}/migawki/*.json.gz"))[:2]
sp = {"bybit": {}, "binance": {}}
for p in pl:
    s = json.load(gzip.open(p, "rt"))
    for r in s["bybit_tickers"]["result"]["list"]:
        b, a = float(r["bid1Price"] or 0), float(r["ask1Price"] or 0)
        if b > 0 and a >= b: sp["bybit"].setdefault(r["symbol"], []).append((a - b) / ((a + b) / 2) * 1e4)
    for r in s["binance_book"]:
        b, a = float(r["bidPrice"]), float(r["askPrice"])
        if b > 0 and a >= b: sp["binance"].setdefault(r["symbol"], []).append((a - b) / ((a + b) / 2) * 1e4)
kl = k.set_index(["gielda", "symbol"]).klasa
for g in ("bybit", "binance"):
    taker = 0.0275 if g == "bybit" else 0.04
    v = pd.Series({s: np.median(x) for s, x in sp[g].items() if kl.get((g, s)) == "akcje"})
    koszt = v / 2 / 100 + taker
    print(f"surowe migawki {g} akcje: n={len(v)} spread med {v.median():.1f} p90 {v.quantile(.9):.1f} pb; koszt med {koszt.median():.4f} %; udział > 0,07 %: {(koszt > 0.07).mean():.1%}")
