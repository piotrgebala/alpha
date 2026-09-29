"""Ktore zbiory kluczowane symbolem zawieraja 5 monet (poprawna lub znieksztalcona nazwa)."""

import glob
import os
import sys

import pandas as pd

RAW = sys.argv[1]
T = ["币安人生", "我踏马来了", "牛来", "龙虾", "哈基米"]
G = [t.encode("utf-8").decode("cp866") for t in T]
for f in sorted(glob.glob(os.path.join(RAW, "**", "*.parquet"), recursive=True)):
    rel = os.path.relpath(f, RAW)
    if rel.startswith(("universe_full/", "universe_2026q3/", "live/", "universe/")):
        continue
    try:
        cols = pd.read_parquet(f).columns
    except Exception as e:  # noqa: BLE001
        print(rel, "BLAD", e)
        continue
    symc = [c for c in cols if c.lower() in ("symbol", "sym", "base", "asset")]
    if not symc:
        continue
    s = pd.read_parquet(f, columns=symc)[symc[0]].astype(str)
    hits = {t: int(s.str.contains(t, regex=False).sum()) for t in T}
    ghits = {g: int(s.str.contains(g, regex=False).sum()) for g in G}
    hits = {k: v for k, v in hits.items() if v}
    ghits = {k: v for k, v in ghits.items() if v}
    print(f"{rel}: kol={symc[0]} wierszy={len(s)} poprawne={hits} znieksztalcone={ghits}")
