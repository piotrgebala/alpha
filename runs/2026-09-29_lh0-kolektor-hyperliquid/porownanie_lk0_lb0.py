"""Tylko odczyt: liczniki LK0 (Binance, próbka) i LB0 (Bybit, pełne) w oknie kontroli pozytywnej LH0.

Czas zdarzenia: pole `T` (ms) w obu źródłach. Kierunek ZLIKWIDOWANEJ pozycji: LK0 `S`=SELL -> long (wniosek 106),
LB0 pole `pos`. Monety: symbol bez przyrostka USDT/USDC. Bez cen po likwidacjach, bez odczytu E1.

Uruchomienie: python porownanie_lk0_lb0.py <t0_ms> <t1_ms> [BTC,ETH,SOL]
"""

import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

HOME = Path.home()


def days(t0, t1):
    d0 = dt.datetime.fromtimestamp(t0 / 1000, dt.timezone.utc).date()
    d1 = dt.datetime.fromtimestamp(t1 / 1000, dt.timezone.utc).date()
    while d0 <= d1:
        yield d0.isoformat()
        d0 += dt.timedelta(days=1)


def base(sym):
    for q in ("USDT", "USDC"):
        if sym.endswith(q):
            return sym[: -len(q)]
    return sym


def read(dirname, t0, t1, side_fn):
    rows = []
    for d in days(t0, t1):
        p = HOME / dirname / f"{d}.jsonl"
        if not p.exists():
            print(f"BRAK PLIKU {p}")
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if t0 <= int(r["T"]) < t1:
                    rows.append((base(r["s"]), side_fn(r), r["s"]))
    return rows


def report(name, rows, coins, minutes):
    print(
        f"\n{name}: zdarzen razem={len(rows)} ({len(rows) / minutes:.1f}/min), monet={len({r[0] for r in rows})}"
    )
    for c in coins:
        sel = [r for r in rows if r[0] == c]
        lg = sum(1 for r in sel if r[1] == "long")
        print(
            f"  {c}: {len(sel)} (zlikwidowane longi {lg} / shorty {len(sel) - lg}); symbole {dict(Counter(r[2] for r in sel))}"
        )
    lg = sum(1 for r in rows if r[1] == "long")
    print(f"  wszystkie monety: longi {lg} / shorty {len(rows) - lg}")


def main():
    t0, t1 = int(sys.argv[1]), int(sys.argv[2])
    coins = (sys.argv[3] if len(sys.argv) > 3 else "BTC,ETH,SOL").split(",")
    minutes = (t1 - t0) / 60000
    print(
        f"okno T w [{t0}, {t1}) ms = {minutes:.1f} min (tylko odczyt ~/likwidacje, ~/likwidacje_bybit)"
    )
    lk0 = read("likwidacje", t0, t1, lambda r: "long" if r["S"] == "SELL" else "short")
    lb0 = read("likwidacje_bybit", t0, t1, lambda r: r["pos"])
    report("LK0 Binance (probka <= 1/s/symbol)", lk0, coins, minutes)
    report("LB0 Bybit (pelne)", lb0, coins, minutes)


if __name__ == "__main__":
    main()
