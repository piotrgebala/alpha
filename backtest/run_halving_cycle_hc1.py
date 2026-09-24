"""
run_halving_cycle_hc1.py — runda HC1 (OPISOWA, 0 wariantów, bez werdyktu): zachowanie BTC i reguły
trendu TS1 na samym BTC w fazach cyklu halvingowego. Dane: FRED CBBTCUSD (Coinbase, dziennie od
2014-12-01; wyjątek od zasady 20 zatwierdzony przez użytkownika 2026-09-24 — cykl wymaga lat
sprzed 2021). Halvingi: 2012-11-28, 2016-07-09, 2020-05-11, 2024-04-20.
Fazy = miesiące od ostatniego halvingu: 0–6, 6–12, 12–18, 18–24, 24–30, 30–36, 36–48.
Trzy–cztery cykle to trzy–cztery obserwacje: żadnych testów istotności, tylko opis.
Konfiguracja ZAMROŻONA w `runs/2026-09-24_hc1-cykl-halvingowy/README.md`.

    PYTHONUTF8=1 py -m backtest.run_halving_cycle_hc1
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.ts_momentum import DAYS_PER_YEAR, portfolio
from data.tradfi_panel import calendar_ffill

SRC = "data/raw/tradfi/fred_CBBTCUSD_1d.parquet"
HALVINGS = [
    pd.Timestamp(d, tz="UTC") for d in ("2012-11-28", "2016-07-09", "2020-05-11", "2024-04-20")
]
BUCKETS = [(0, 6), (6, 12), (12, 18), (18, 24), (24, 30), (30, 36), (36, 48)]
FEE = 0.0007
SEP = "=" * 104


def load_btc() -> pd.Series:
    df = pd.read_parquet(SRC)
    s = df.set_index(pd.to_datetime(df["date"]))["value"].astype(float)
    return calendar_ffill(s, "2014-12-01", "2026-09-22")


def phase_of(day: pd.Timestamp) -> tuple[int, float]:
    """(numer cyklu 0..3, miesiące od ostatniego halvingu)."""
    k = max(i for i, h in enumerate(HALVINGS) if h <= day)
    return k, (day - HALVINGS[k]).days / 30.4375


def bucket(months: float) -> str | None:
    for lo, hi in BUCKETS:
        if lo <= months < hi:
            return f"{lo:02d}–{hi:02d}"
    return None


def main() -> None:
    btc = load_btc().dropna()
    close = pd.DataFrame({"BTC": btc})
    fund = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    start, end = pd.Timestamp("2015-03-01", tz="UTC"), pd.Timestamp(
        "2026-09-01", tz="UTC"
    )  # po błędzie notowań 2015-01-13/14
    members = {m: ["BTC"] for m in pd.date_range(start, end, freq="MS", tz="UTC") if m < end}
    ts, _ = portfolio(close, fund, members, start, end, FEE)
    ts = ts.dropna().set_index("date")["net"]
    r = btc.pct_change().dropna()
    r = r[(r.index >= start) & (r.index < end)]
    info = pd.DataFrame({"r": r, "ts": ts.reindex(r.index)})
    ph = [phase_of(d) for d in info.index]
    info["cycle"] = [h.year for h in (HALVINGS[k] for k, _ in ph)]
    info["bucket"] = [bucket(m) for _, m in ph]
    info = info.dropna(subset=["bucket"])
    print(SEP)
    print(
        "HC1 — CYKL HALVINGOWY BTC (opisowo, 3–4 cykle; bez testów istotności); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"  dane: CBBTCUSD {btc.index.min().date()} → {btc.index.max().date()}; okres opisu {start.date()} → {end.date()}"
    )
    print(
        "\n1. BTC: zwrot w fazie (Π(1+r)−1), zmienność roczna, największy spadek w fazie — per cykl"
    )
    print(f"  {'faza (mies.)':>12} | " + " | ".join(f"cykl {h.year:>4}" for h in HALVINGS))
    for lab in [f"{lo:02d}–{hi:02d}" for lo, hi in BUCKETS]:
        cells = []
        for h in HALVINGS:
            g = info[(info["bucket"] == lab) & (info["cycle"] == h.year)]["r"]
            if len(g) < 60:
                cells.append(f"{'—':>9}")
                continue
            eq = np.cumprod(1 + g.to_numpy())
            dd = float(np.max(1 - eq / np.maximum.accumulate(eq)))
            cells.append(f"{100 * (eq[-1] - 1):+6.0f}%/{100 * dd:2.0f}%")
        print(f"  {lab:>12} | " + " | ".join(cells))
    print("  (komórka: zwrot w fazie / największy spadek w fazie; — = brak danych lub < 60 dni)")
    print("\n2. ŚREDNIO po cyklach: BTC i reguła trendu TS1 na samym BTC (netto, %/rok w fazie)")
    print(
        f"  {'faza':>6} | {'dni':>5} | {'cykli':>5} | {'BTC %/rok':>9} | {'BTC zmienn.':>11} | {'cykli z BTC > 0':>15} | {'trend %/rok':>11} | {'cykli z trendem > 0':>19}"
    )
    for lab in [f"{lo:02d}–{hi:02d}" for lo, hi in BUCKETS]:
        g = info[info["bucket"] == lab]
        per = g.groupby("cycle")
        btc_c = per["r"].apply(lambda x: np.prod(1 + x) - 1)
        ts_c = per["ts"].sum()
        print(
            f"  {lab:>6} | {len(g):5d} | {g['cycle'].nunique():5d} | {100 * g['r'].mean() * DAYS_PER_YEAR:+8.0f}% | "
            f"{100 * g['r'].std() * np.sqrt(DAYS_PER_YEAR):10.0f}% | {int((btc_c > 0).sum()):>7}/{len(btc_c):<7} | "
            f"{100 * g['ts'].mean() * DAYS_PER_YEAR:+10.1f}% | {int((ts_c > 0).sum()):>9}/{len(ts_c):<9}"
        )
    print(
        f"\n  trend TS1 na BTC, cały okres: {100 * ts.mean() * DAYS_PER_YEAR:+.1f}%/rok, zmienność {100 * ts.std() * np.sqrt(DAYS_PER_YEAR):.1f}%/rok"
    )
    today = pd.Timestamp("2026-09-24", tz="UTC")
    k, m = phase_of(today)
    print(
        f"  dziś ({today.date()}): {m:.1f} mies. od halvingu {HALVINGS[k].date()} → faza {bucket(m)}"
    )
    print(SEP)


if __name__ == "__main__":
    main()
