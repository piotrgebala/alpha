"""Porownanie tresci plikow o znieksztalconej nazwie z niezaleznymi danymi (tylko odczyt)."""

import os
import sys

import pandas as pd

RAW = sys.argv[1]
kl = pd.read_parquet(os.path.join(RAW, "listings/klines.parquet"))
fu = pd.read_parquet(os.path.join(RAW, "listings/funding.parquet"))
oh = pd.read_parquet(os.path.join(RAW, "universe_ohlc_full/ohlc_1d.parquet"))


def fix(n):
    return n.encode("cp866").decode("utf-8")


for d in ["universe_full", "universe_2026q3", "live"]:
    full = os.path.join(RAW, d)
    for n in sorted(os.listdir(full)):
        if n.isascii():
            continue
        stem, kind = fix(n)[: -len(".parquet")].rsplit("_", 1)
        df = pd.read_parquet(os.path.join(full, n))
        rng = f"{df.iloc[:, 0].min()}..{df.iloc[:, 0].max()}" if len(df) else "pusty"
        out = f"{d:16s} {stem:14s} {kind:8s} wiersze={len(df):4d} kol={list(df.columns)} {rng}"
        if kind == "1d":
            for name, ref in [("listings/klines", kl), ("ohlc_full", oh)]:
                r = ref[ref.symbol == stem][["open_time", "close"]]
                if len(r) == 0:
                    out += f" | {name}: brak"
                    continue
                m = df.merge(r, on="open_time", suffixes=("", "_ref"))
                eq = int((m["close"] == m["close_ref"]).sum())
                out += f" | {name}: wspolne={len(m)} rowne={eq}"
        else:
            r = fu[fu.symbol == stem]
            if len(r) == 0:
                out += " | listings/funding: brak"
            else:
                tcol = [c for c in df.columns if "time" in c.lower()][0]
                vcol = [c for c in df.columns if "rate" in c.lower()][0]
                a = df.rename(columns={tcol: "t", vcol: "v"})[["t", "v"]]
                b = r.rename(columns={"timestamp": "t", "funding_rate": "v_ref"})[["t", "v_ref"]]
                m = a.merge(b, on="t")
                eq = int((m["v"] == m["v_ref"]).sum())
                out += f" | listings/funding: wspolne={len(m)} rowne={eq}"
        print(out)
