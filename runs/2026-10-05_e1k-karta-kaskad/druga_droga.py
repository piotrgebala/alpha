"""E1K — druga droga (bramka 16a): niezależne zliczenie kaskad bez `backtest/e1_kaskady.py`
i bez `data/liquidation_index.py` — własne czytanie JSON (float), sumy przez cumsum + searchsorted
(numpy), blokada w osobnej pętli; plus ręczny rachunek n50/n80 dla scenariusza rozstrzygającego.
0 cen po likwidacjach (cena z rekordu tylko do nominału jednej likwidacji).

    PYTHONUTF8=1 py runs/2026-10-05_e1k-karta-kaskad/druga_droga.py
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HOME = Path.home()
SRC = {"bybit": HOME / "likwidacje_bybit", "binance": HOME / "likwidacje"}
KOSZYK = Path(__file__).resolve().parents[2] / "dziennik" / "koszyk.csv"
UNTIL = "2026-10-05"
W = 3_600_000
HOLD = 86_400_000


def month(t):
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m")


def read(g):
    rows = []
    for p in sorted(SRC[g].glob("*.jsonl")):
        if p.stem >= UNTIL:
            continue
        for line in p.open(encoding="utf-8"):
            r = json.loads(line)
            if g == "bybit":  # kontrakty odwrotne (BTCUSD…) odpadają filtrem koszyka USDT
                side = "long" if r["S"] == "Buy" else "short"
                nom = float(r["v"]) * float(r["p"])
            else:
                if str(r.get("st")) == "2" or "USD_" in r["s"]:
                    continue
                side = "long" if r["S"] == "SELL" else "short"
                ap = float(r["ap"]) if r.get("ap") not in (None, "") else 0.0
                nom = float(r["q"]) * (ap if ap > 0 else float(r["p"]))
            rows.append((r["s"], int(r["T"]), side, nom))
    return rows


def main():
    thr = {}
    for r in csv.DictReader(KOSZYK.open(encoding="utf-8")):
        if r["czlonek_top20"] == "True":
            thr[(r["miesiac"], r["symbol"])] = 0.005 * float(r["sredni_obrot_30d"])
    for g in ("bybit", "binance"):
        rows = [x for x in read(g) if (month(x[1]), x[0]) in thr]
        found = []
        for sym in sorted({x[0] for x in rows}):
            xs = sorted((x for x in rows if x[0] == sym), key=lambda x: x[1])
            t = np.array([x[1] for x in xs], dtype=np.int64)
            sums = {}
            for side in ("long", "short"):
                v = np.array([x[3] if x[2] == side else 0.0 for x in xs])
                c = np.concatenate([[0.0], np.cumsum(v)])
                lo = np.searchsorted(t, t - W, side="right")  # pierwsze z t > t_i − W
                sums[side] = c[np.arange(1, len(t) + 1)] - c[lo]
            blocked = -1
            for i, x in enumerate(xs):
                if x[1] < blocked:
                    continue
                lim = thr[(month(x[1]), sym)]
                oth = "short" if x[2] == "long" else "long"
                if sums[x[2]][i] >= lim * (1 - 1e-12) and sums[oth][i] < lim:
                    found.append((x[1], sym, x[2]))
                    blocked = x[1] + HOLD
        found.sort()
        print(
            f"{g}: kaskad {len(found)}, dni {len({month(f[0]) + str(f[0] // 86_400_000) for f in found})}"
        )
        for f in found:
            print(
                f"  {datetime.fromtimestamp(f[0] / 1000, tz=timezone.utc):%Y-%m-%d %H:%M} {f[1]} {f[2]}"
            )
    # ręcznie: n = ((z_a + z_b) σ / (μ − C))², μ 0,75 %, σ 5 %, C 0,5 %
    for zb, lab in ((0.0, "50 %"), (0.8416, "80 %")):
        n = ((1.96 + zb) * 0.05 / (0.0075 - 0.005)) ** 2
        print(f"moc {lab}: n = {n:,.0f} dni z kaskadą; przy 365/rok {n / 365:.1f} l.")
    # przybliżenie granicy dla progu uproszczonego: μ/C → π/2 przy małym μ/σ
    print(f"π/2 = {math.pi / 2:.3f}")


if __name__ == "__main__":
    main()
