"""
run_listings_nl1.py — runda NL1: short na nowych kontraktach USDT-M Binance przez 14 dni od
pierwszego pełnego dnia notowań (rodzina G2 katalogu). Konfiguracja ZAMROŻONA w pre-rejestracji
(`runs/2026-09-24_nl1-nowe-listingi/README.md`). Dane: `py -m data.fetch_listings`.

    PYTHONUTF8=1 py -m backtest.run_listings_nl1 --moc   # tylko rozrzut (rachunek mocy)
    PYTHONUTF8=1 py -m backtest.run_listings_nl1         # pełny przebieg

Kryterium (jedno ramię, m = 1): średni P&L shorta 1× na zdarzenie (% nominału, po kosztach
i realnym fundingu) z błędem odpornym na klastry (miesiąc listingu): POZYTYWNY, gdy t > 1,96;
NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import load_config
from backtest.listing_events import (
    HOLD_DAYS,
    MMR,
    cluster_mean_ci,
    liquidation_move,
    short_event_pnl,
)

DATA_DIR = "data/raw/listings"
BTC_1D = "data/raw/universe/BTCUSDT_1d.parquet"
ONBOARD_LAG_MAX_DAYS = 1  # archiwum spóźnione względem onboardDate o > 1 dzień → wyklucz
LEVERAGES = (1.0, 2.0, 3.0)
Z95 = 1.959964
SEP = "=" * 104


def load_events() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    ev = pd.read_csv(f"{DATA_DIR}/events.csv")
    ev["d0"] = pd.to_datetime(ev["d0"], utc=True, format="ISO8601")
    ev["onboard"] = pd.to_datetime(ev["onboard"], utc=True, format="ISO8601")
    kl = pd.read_parquet(f"{DATA_DIR}/klines.parquet")
    fu = pd.read_parquet(f"{DATA_DIR}/funding.parquet")
    s = ev[ev["in_sample"]].copy()
    lag = (s["d0"] - s["onboard"].dt.normalize()).dt.days
    reasons = {}
    late = lag > ONBOARD_LAG_MAX_DAYS
    reasons["archiwum spóźnione względem onboardDate (> 1 dzień)"] = int(late.sum())
    s = s[~late]
    no_fund = ~s["symbol"].isin(set(fu["symbol"]))
    reasons["brak fundingu w archiwum"] = int(no_fund.sum())
    s = s[~no_fund]
    return s.reset_index(drop=True), kl, fu, reasons


def compute(events, kl, fu, cost_side, leverage):
    kg = dict(tuple(kl.groupby("symbol")))
    fg = dict(tuple(fu.groupby("symbol")))
    rows, missing = [], 0
    for e in events.itertuples():
        r = short_event_pnl(
            kg[e.symbol], fg.get(e.symbol, pd.DataFrame()), e.d0, leverage, cost_side
        )
        if r is None:
            missing += 1
            continue
        rows.append({"symbol": e.symbol, "d0": e.d0, **r})
    out = pd.DataFrame(rows)
    out["month"] = out["d0"].dt.strftime("%Y-%m")
    return out, missing


def _btc_window(d0s: pd.Series) -> pd.Series:
    b = pd.read_parquet(BTC_1D)
    close = b.set_index(pd.to_datetime(b["open_time"], utc=True))["close"]
    opens = close.shift(1)
    vals = []
    for d0 in d0s:
        a, z = d0 + pd.Timedelta(days=1), d0 + pd.Timedelta(days=HOLD_DAYS)
        vals.append(close.get(z, np.nan) / opens.get(a, np.nan) - 1.0)
    return pd.Series(vals, index=d0s.index)


def header(events, reasons, cost_side):
    print(
        f"dane   : {len(events)} zdarzeń (pierwsze listingi krypto USDT-M z archiwum data.binance.vision, "
        f"d0 {events['d0'].min().date()} → {events['d0'].max().date()}, wycofane włącznie)\n"
        f"         dodatkowe wykluczenia (przed przebiegiem): {reasons}\n"
        f"reguła : short po open d0+1, wyjście po close d0+{HOLD_DAYS}; koszt {100 * cost_side:.3f}% × 2; funding realny (short dostaje dodatni); "
        f"likwidacja izolowana przy wzroście ≥ 1/L − {MMR:.3f} (dzienne maksima)\n"
        f"klastry: miesiąc listingu (zdarzenia nakładają się i są skorelowane)\n"
    )


def run_power() -> None:
    t0 = time.time()
    cfg = load_config()
    cost_side = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    events, kl, fu, reasons = load_events()
    print(SEP)
    print("NL1 — RACHUNEK MOCY: tylko ROZRZUT P&L (średnia i znak nie są drukowane)")
    print(SEP)
    header(events, reasons, cost_side)
    for lev in LEVERAGES:
        out, missing = compute(events, kl, fu, cost_side, lev)
        w = cluster_mean_ci(out["pnl"], out["month"])
        hw = Z95 * w["se"]
        print(
            f"  {lev:.0f}×: n {w['n']} (nierozliczalne {missing}), klastrów {w['clusters']}, sd na zdarzenie {100 * w['sd']:.1f}%, "
            f"se klastrowe {100 * w['se']:.2f}% (iid {100 * w['se_iid']:.2f}%, efekt klastrów ×{w['design_effect']:.2f}) → "
            f"half-width 95% ±{100 * hw:.1f}% nominału; MDE (80% mocy) ≈ {100 * 2.8 * w['se']:.1f}%"
        )
    print(f"  czas: {time.time() - t0:.0f}s")


def _verdict(w: dict) -> str:
    if w["t"] > Z95:
        return "POZYTYWNY — t (klastrowe) > 1,96: short po listingu zarabia po kosztach i fundingu"
    if w["ci_high"] < 0:
        return "NEGATYWNY — górny kraniec CI 95% poniżej zera"
    return "NIEROZSTRZYGNIĘTY — CI obejmuje zero"


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--moc":
        run_power()
        return
    t0 = time.time()
    cfg = load_config()
    cost_side = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    events, kl, fu, reasons = load_events()
    print(SEP)
    print("NL1 — SHORT NA NOWYCH KONTRAKTACH USDT-M PRZEZ 14 DNI; konfiguracja ZAMROŻONA")
    print(SEP)
    header(events, reasons, cost_side)
    res = {}
    for lev in LEVERAGES:
        res[lev] = compute(events, kl, fu, cost_side, lev)
    one, missing = res[1.0]
    w = cluster_mean_ci(one["pnl"], one["month"])
    print(
        "1. KRYTERIUM — średni P&L shorta 1× na zdarzenie (% nominału), CI klastrowe (miesiąc listingu)"
    )
    print(
        f"  n {w['n']} (nierozliczalne {missing}), klastrów {w['clusters']} | średnia {100 * w['mean']:+.2f}% "
        f"[{100 * w['ci_low']:+.2f}; {100 * w['ci_high']:+.2f}] | mediana {100 * w['median']:+.2f}% | sd {100 * w['sd']:.1f}% | "
        f"t {w['t']:+.2f} (iid {w['mean'] / w['se_iid']:+.2f}, efekt klastrów ×{w['design_effect']:.2f})"
    )
    print(f"  >>> ODCZYT KRYTERIUM NL1: {_verdict(w)}")

    print("\n2. DEKOMPOZYCJA (1×) i rozkład")
    print(
        f"  średnio: cena {100 * (one['pnl'] - one['funding'] + one['cost']).mean():+.2f}% "
        f"(short zyskuje na spadku), funding {100 * one['funding'].mean():+.2f}%, koszt {100 * one['cost'].mean():.2f}%\n"
        f"  udział zdarzeń z zyskiem {100 * (one['pnl'] > 0).mean():.1f}% | p05 {100 * one['pnl'].quantile(0.05):+.1f}%, "
        f"p25 {100 * one['pnl'].quantile(0.25):+.1f}%, p75 {100 * one['pnl'].quantile(0.75):+.1f}%, p95 {100 * one['pnl'].quantile(0.95):+.1f}%, "
        f"min {100 * one['pnl'].min():+.1f}%, max {100 * one['pnl'].max():+.1f}%\n"
        f"  funding w oknie: mediana {100 * one['funding'].median():+.2f}%, udział zdarzeń, w których short PŁACI netto: "
        f"{100 * (one['funding'] < 0).mean():.1f}%, p05 {100 * one['funding'].quantile(0.05):+.2f}%"
    )
    years = one["d0"].dt.year
    print(f"  {'rok':>6} | {'n':>4} | {'średnia':>8} | {'mediana':>8} | {'% zysk.':>7} | {'Σ':>8}")
    for y, g in one.groupby(years):
        print(
            f"  {y:6d} | {len(g):4d} | {100 * g['pnl'].mean():+7.2f}% | {100 * g['pnl'].median():+7.2f}% | "
            f"{100 * (g['pnl'] > 0).mean():6.1f}% | {100 * g['pnl'].sum():+7.0f}%"
        )

    print(
        "\n3. OPISOWO (0 wariantów) — dźwignia izolowana 2× i 3×, rynek (BTC) w tych samych oknach"
    )
    for lev in (2.0, 3.0):
        o, _ = res[lev]
        wl = cluster_mean_ci(o["pnl"], o["month"])
        print(
            f"  {lev:.0f}×: likwidacja przy wzroście ≥ {100 * liquidation_move(lev):.1f}% — zlikwidowanych {100 * o['liquidated'].mean():.1f}% zdarzeń; "
            f"P&L na nominał {100 * wl['mean']:+.2f}% [{100 * wl['ci_low']:+.2f}; {100 * wl['ci_high']:+.2f}] → na depozyt ×{lev:.0f}: "
            f"{100 * lev * wl['mean']:+.1f}%, mediana na depozyt {100 * lev * wl['median']:+.1f}%"
        )
    btc = _btc_window(one["d0"])
    hedged = one["pnl"] + btc.to_numpy()
    wh = cluster_mean_ci(pd.Series(hedged), one["month"])
    print(
        f"  BTC w tych samych oknach: średnio {100 * np.nanmean(btc):+.2f}%; short alt + long BTC (równy nominał): "
        f"{100 * wh['mean']:+.2f}% [{100 * wh['ci_low']:+.2f}; {100 * wh['ci_high']:+.2f}]"
    )
    conc = []
    for d in pd.date_range(one["d0"].min(), one["d0"].max(), freq="D"):
        conc.append(
            int(
                (
                    (one["d0"] + pd.Timedelta(days=1) <= d)
                    & (one["d0"] + pd.Timedelta(days=HOLD_DAYS) >= d)
                ).sum()
            )
        )
    conc = np.array(conc)
    print(
        f"  równoczesne pozycje: mediana {np.median(conc):.0f}, p90 {np.quantile(conc, 0.9):.0f}, max {conc.max()} "
        f"(przy równym nominale na zdarzenie kapitał dzieli się na tyle pozycji)"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
