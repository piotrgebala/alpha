"""Tylko odczyt: liczniki LK0 (Binance) w oknie próby LB0 — porównanie opisowe."""

import json
from collections import Counter
from pathlib import Path

A, B = 1790534818743, 1790534998744  # okno próby LB0 (ms, z raw_output.txt)
path = Path("/home/dantey1/likwidacje/2026-09-27.jsonl")
rows = []
with open(path, encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        r = json.loads(line)
        if A <= int(r["E"]) <= B:
            rows.append(r)
n = len(rows)
um = [r for r in rows if r.get("st", 1) == 1]
print(f"plik: {path} (tylko odczyt); okno E w [{A}, {B}] ms = 180 s")
print(
    f"zdarzeń LK0: {n} ({60 * n / 180:.1f}/min); w tym UM (st=1): {len(um)}; symboli: {len({r['s'] for r in rows})}"
)
sell = sum(1 for r in rows if r["S"] == "SELL")
print(f"zlikwidowane longi (S=SELL): {sell}, shorty (S=BUY): {n - sell}")
print(f"nominał (q x ap) ≈ {sum(float(r['q']) * float(r['ap']) for r in rows):,.0f} USD")
print(
    "najczęstsze symbole: "
    + ", ".join(f"{s} {k}" for s, k in Counter(r["s"] for r in rows).most_common(5))
)
