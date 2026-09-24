"""
run_trend_tradfi_tx1.py — runda TX1 (ADR-09, szczebel 1b): reguła TS1 CO DO BAJTU (znak zwrotu
28 dni, σ̂ EWMA com 60 · √365, w = s·min(3; 0,40/σ̂)/N, formowanie co 7 dni, 7 faz) na 19 rynkach
spoza krypto z FRED (`data/tradfi_panel.py`: 13 walut, Brent, Nasdaq, Nikkei, obligacje USA 2/10/30).
Dni kalendarzowe z przeniesieniem ceny → silnik bez zmian parametrów. Koszt 0,02 % × obrót,
bez fundingu/carry/dywidend (ceny spot — dowód MECHANIZMU, nie wynik do handlu).
Konfiguracja ZAMROŻONA w `runs/2026-09-24_tx1-trend-inne-rynki/README.md`.

    PYTHONUTF8=1 py -m backtest.run_trend_tradfi_tx1 --moc
    PYTHONUTF8=1 py -m backtest.run_trend_tradfi_tx1

Kryterium główne (1990-01 → 2026-08): POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0
(100 portfeli ze znakami przesuniętymi cyklicznie, jak TS1); NEGATYWNY, gdy górny kraniec CI < 0.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.run_ts_momentum_ts1 import _shifts
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio
from data.tradfi_panel import ASSET_CLASS, build_panel, load_raw

DATA_START, START, END = "1989-01-01", "1990-01-01", "2026-09-01"
POST = pd.Timestamp("2013-01-01", tz="UTC")  # po publikacji Moskowitz–Ooi–Pedersen (2012)
FEE = 0.0002
N_SIM = 100
Z95 = 1.959964
SEP = "=" * 104


def load(cols: list[str] | None = None):
    panel = build_panel(load_raw(), DATA_START, "2026-08-31")
    if cols is not None:
        panel = panel[cols]
    fund = pd.DataFrame(0.0, index=panel.index, columns=panel.columns)
    start, end = pd.Timestamp(START, tz="UTC"), pd.Timestamp(END, tz="UTC")
    members = {
        m: list(panel.columns) for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end
    }
    return panel, fund, members, start, end


def _w(x: pd.Series) -> dict:
    return summarize_pnl(x, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)


def _row(name: str, w: dict) -> str:
    a = DAYS_PER_YEAR
    return (
        f"  {name:<24} | {w['n']:5d} dni | {100 * w['mean'] * a:+6.2f}%/rok [{100 * w['ci_low'] * a:+6.2f}; "
        f"{100 * w['ci_high'] * a:+6.2f}] | sd {100 * w['sd'] * np.sqrt(a):5.1f}%/rok | t_neff {w['t_neff']:+5.2f}"
    )


def null_dist(close, fund, members, start, end) -> np.ndarray:
    """H0: (średnia całość, sd całość, średnia po 2013, sd po 2013) dla 100 przesunięć znaków."""
    out = []
    for k in _shifts(len(close), N_SIM):
        avg, _ = portfolio(close, fund, members, start, end, FEE, sign_shift_days=k)
        s = avg.dropna().set_index("date")["net"]
        p = s[s.index >= POST]
        out.append((s.mean(), s.std(ddof=1), p.mean(), p.std(ddof=1)))
    return np.array(out)


def main(argv: list[str]) -> None:
    t0 = time.time()
    moc = bool(argv) and argv[0] == "--moc"
    close, fund, members, start, end = load()
    null = null_dist(close, fund, members, start, end)
    a = DAYS_PER_YEAR
    print(SEP)
    print(
        ("TX1 — RACHUNEK MOCY" if moc else "TX1 — TREND TS1 NA 19 RYNKACH SPOZA KRYPTO")
        + "; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"  dane: {close.shape[1]} rynków, {close.index.min().date()} → {close.index.max().date()}; okres oceny {start.date()} → {end.date()}; "
        f"klasy: "
        + ", ".join(
            f"{k} {sum(v == k for v in ASSET_CLASS.values())}"
            for k in ("waluty", "energia", "akcje", "obligacje")
        )
    )
    n_full = (end - start).days
    n_post = (end - POST).days
    for lab, i_m, i_s, n in (
        ("całość 1990–2026", 0, 1, n_full),
        ("po publikacji 2013–2026", 2, 3, n_post),
    ):
        sd = float(np.median(null[:, i_s]))
        se = max(float(null[:, i_m].std(ddof=1)), sd / np.sqrt(n))
        hw = Z95 * se * a
        print(
            f"  H0 {lab}: zmienność {100 * sd * np.sqrt(a):.1f}%/rok; half-width 95% ±{100 * hw:.1f}%/rok = {hw / (sd * np.sqrt(a)):.2f} SR; "
            f"q97,5 {100 * np.quantile(null[:, i_m], 0.975) * a:+.1f}%/rok"
        )
    if moc:
        print(f"  czas: {time.time() - t0:.0f}s")
        return
    avg, phases = portfolio(close, fund, members, start, end, FEE)
    s = avg.dropna().set_index("date")
    w = _w(s["net"])
    q975 = float(np.quantile(null[:, 0], 0.975))
    print("\n1. KRYTERIUM GŁÓWNE — dzienny zwrot netto (średnia 7 faz, % kapitału), 1990–2026")
    print(_row("TX1 netto", w))
    print(_row("TX1 brutto", _w(s["gross"])))
    print(
        f"  H0 q97,5 {100 * q975 * a:+.2f}%/rok; TX1 powyżej {100 * (null[:, 0] < w['mean']).mean():.0f}% portfeli H0"
    )
    if w["t_neff"] > Z95 and w["mean"] > q975:
        v = "POZYTYWNY"
    elif w["ci_high"] < 0:
        v = "NEGATYWNY"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM TX1: {v}")
    post = s["net"][s.index >= POST]
    wp = _w(post)
    print("\n2. PO PUBLIKACJI (2013–2026) i per dekada — opisowo")
    print(_row("po publikacji 2013+", wp))
    print(
        f"  H0 po 2013: q97,5 {100 * np.quantile(null[:, 2], 0.975) * a:+.2f}%/rok; TX1 powyżej {100 * (null[:, 2] < wp['mean']).mean():.0f}%"
    )
    for lo, hi in (("1990", "2000"), ("2000", "2010"), ("2010", "2020"), ("2020", "2027")):
        x = s["net"][
            (s.index >= pd.Timestamp(lo, tz="UTC")) & (s.index < pd.Timestamp(hi, tz="UTC"))
        ]
        print(_row(f"dekada {lo}s", _w(x)))
    years = s.index.year
    yr = s["net"].groupby(years).sum()
    print(
        f"  lata dodatnie: {(yr > 0).sum()}/{len(yr)}; po 2013: {(yr[yr.index >= 2013] > 0).sum()}/{(yr.index >= 2013).sum()}"
    )
    print("  per rok (Σ netto %): " + "; ".join(f"{y}: {100 * v_:+.1f}" for y, v_ in yr.items()))
    print("  7 faz (%/rok): " + ", ".join(f"{100 * p['net'].mean() * a:+.2f}" for p in phases))
    print("\n3. PER KLASA AKTYWÓW (ta sama reguła, koszyk tylko z danej klasy) — opisowo")
    for cls in ("waluty", "energia", "akcje", "obligacje"):
        cols = [c for c, k in ASSET_CLASS.items() if k == cls]
        c2, f2, m2, s2, e2 = load(cols)
        av, _ = portfolio(c2, f2, m2, s2, e2, FEE)
        x = av.dropna().set_index("date")["net"]
        print(
            _row(f"{cls} ({len(cols)})", _w(x))
            + f" | po 2013 {100 * x[x.index >= POST].mean() * a:+.2f}%/rok"
        )
    nom = s["gross_notional"]
    print(
        f"\n  nominał brutto: mediana {nom.median():.2f}× kapitału; obrót średnio {s['turnover'].mean() * a:.1f} kapitału/rok"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
