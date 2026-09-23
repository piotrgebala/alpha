"""
run_rebalance_premium_r1.py — runda R1: premia rebalansowa koszyka top-20 (point-in-time po obrocie),
rebalans dzienny vs buy-and-hold w miesiącu. Pre-rejestracja (PRZED tym skryptem):
runs/2026-09-23_r1-premia-rebalansowa/README.md.

Uruchomienie:  py -m backtest.run_rebalance_premium_r1   (Windows: PYTHONUTF8=1)

Czyta wyłącznie cache (data/raw/universe) i config — bez sieci. Neutralny reporter: drukuje odczyt
kryterium z pre-rejestracji (jedno ramię, t_neff > 1,96); werdykt podpisuje Claude w README rundy.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import (
    TOP_N,
    cumulative_growth,
    daily_premium,
    load_universe,
    monthly_members,
)

FIRST_MONTH = "2021-02-01"  # zasada 20 + lookback 30 dni wewnątrz 2021
LAST_MONTH = "2026-06-01"
Z95 = 1.959964
DAYS_PER_YEAR = 365
SEP = "=" * 104
# liczby z pre-rejestracji (ex ante)
HALF_CSV_EX_ANTE = 0.000785  # ½·CSV/dzień — górna granica premii
COST_EX_ANTE = 0.000024  # opłata × obrót /dzień
SE_EX_ANTE = 0.0000271  # proxy szumu /dzień


def _verdict(w: dict) -> str:
    if w["t_neff"] > Z95:
        return "POZYTYWNY — t_neff > 1,96 (dolny kraniec CI nad zerem)"
    if w["ci_high"] < 0:
        return "NEGATYWNY — górny kraniec CI 95% poniżej zera (rebalans SZKODZI)"
    return "NIEROZSTRZYGNIĘTY — CI obejmuje zero"


def main() -> None:
    t0 = time.time()
    cfg = load_config()
    fee = cfg["costs"]["spot_fee_rate"]
    universe_dir = Path(cfg["data"]["cache_dir"]) / "universe"
    close, volume = load_universe(universe_dir)
    months = list(pd.date_range(FIRST_MONTH, LAST_MONTH, freq="MS", tz="UTC"))
    members = monthly_members(volume, months, top_n=TOP_N)
    out = daily_premium(close, members, fee)
    print(SEP)
    print(
        "R1 — PREMIA REBALANSOWA: koszyk top-20 po obrocie, rebalans dzienny (A) vs buy-and-hold w miesiącu (B); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    uniq = sorted({s for m in members.values() for s in m})
    print(
        f"dane      : uniwersum {close.shape[1]} symboli, {close.index.min().date()} → {close.index.max().date()}; "
        f"koszyki {len(members)} (od {FIRST_MONTH} do {LAST_MONTH}), po {TOP_N} członków, {len(uniq)} różnych symboli; "
        f"dni {len(out)}: {out['date'].min().date()} → {out['date'].max().date()}\n"
        f"koszty    : opłata spot {100 * fee:.2f}% × obrót dzienny A; obrót na starcie miesiąca wspólny (skrócony)\n"
        f"kryterium : jedno ramię; POZYTYWNY t_neff > 1,96; NEGATYWNY górny kraniec CI < 0\n"
    )

    w = summarize_pnl(out["premium_net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    g = summarize_pnl(
        out["premium_gross"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0
    )
    print(
        "1. KRYTERIUM — średnia dzienna premia NETTO (ułamek wartości koszyka), CI z N_eff, rocznie ×365"
    )
    print(
        f"  netto : {100 * w['mean']:+.5f}%/dzień  CI [{100 * w['ci_low']:+.5f}; {100 * w['ci_high']:+.5f}]  mediana {100 * w['median']:+.5f}%  "
        f"t {w['t']:+.2f}  N_eff {w['n_eff']:.0f}/{w['n']}  t_neff {w['t_neff']:+.2f}  → rocznie {100 * w['annual_notional']:+.2f}% "
        f"[{100 * w['annual_notional_ci'][0]:+.2f}; {100 * w['annual_notional_ci'][1]:+.2f}]"
    )
    print(
        f"  brutto: {100 * g['mean']:+.5f}%/dzień  CI [{100 * g['ci_low']:+.5f}; {100 * g['ci_high']:+.5f}]  t_neff {g['t_neff']:+.2f}  "
        f"→ rocznie {100 * g['annual_notional']:+.2f}%; koszt obrotu {100 * out['cost'].mean():.5f}%/dzień = {100 * out['cost'].mean() * DAYS_PER_YEAR:.2f}%/rok"
    )
    print(f"  >>> ODCZYT KRYTERIUM R1: {_verdict(w)}")

    print("\n2. DEKOMPOZYCJA I KONTEKST (obserwacje)")
    print(
        f"  Σ premia brutto {100 * out['premium_gross'].sum():+.2f}%, Σ koszty {100 * out['cost'].sum():.2f}%, "
        f"Σ premia netto {100 * out['premium_net'].sum():+.2f}% (sumy dziennych ułamków)\n"
        f"  obrót dzienny A: średnia {100 * out['turnover'].mean():.2f}%, mediana {100 * out['turnover'].median():.2f}%, p95 {100 * out['turnover'].quantile(0.95):.2f}%\n"
        f"  koszyk A skumulowany zwrot {100 * cumulative_growth(out['r_rebal']):+.1f}%, koszyk B {100 * cumulative_growth(out['r_bh']):+.1f}% "
        f"(beta rynku — poza pytaniem; różnica wzrostu skumulowanego {100 * (cumulative_growth(out['r_rebal']) - cumulative_growth(out['r_bh'])):+.1f} pp)\n"
        f"  dni z premią netto > 0: {100 * (out['premium_net'] > 0).mean():.1f}%; "
        f"miesiące z Σ premii netto > 0: {int((out.groupby('month')['premium_net'].sum() > 0).sum())}/{out['month'].nunique()}"
    )
    csv = (out["premium_gross"]).abs()
    print(
        f"  |premia brutto| p50/p95/max: {100 * csv.quantile(0.5):.4f}% / {100 * csv.quantile(0.95):.4f}% / {100 * csv.max():.3f}%  "
        f"(red flag: premia > ½·CSV 0,0785%/dzień średnio = błąd; średnia brutto {100 * g['mean']:+.5f}%)"
    )

    print("\n3. PER ROK (OPISOWO, bez werdyktów)")
    out["rok"] = pd.to_datetime(out["date"], utc=True).dt.year
    print(
        f"  {'rok':>4} | {'dni':>4} | {'netto/dzień':>11} | {'rocznie':>8} | {'brutto/rok':>10} | {'koszt/rok':>9} | {'obrót/dzień':>11} | {'koszyk A':>9} | {'koszyk B':>9}"
    )
    print("  " + "-" * 100)
    for yr, grp in out.groupby("rok"):
        print(
            f"  {yr:>4} | {len(grp):4d} | {100 * grp['premium_net'].mean():+10.5f}% | {100 * grp['premium_net'].mean() * DAYS_PER_YEAR:+7.2f}% | "
            f"{100 * grp['premium_gross'].mean() * DAYS_PER_YEAR:+9.2f}% | {100 * grp['cost'].mean() * DAYS_PER_YEAR:8.2f}% | "
            f"{100 * grp['turnover'].mean():10.2f}% | {100 * cumulative_growth(grp['r_rebal']):+8.1f}% | {100 * cumulative_growth(grp['r_bh']):+8.1f}%"
        )

    print("\n4. MIERZALNOŚĆ (zasada 18) — ex ante vs ex post")
    print(
        f"  ex ante: n {len(out)}, se ≈ {100 * SE_EX_ANTE:.5f}%/dzień → wykrywalny efekt {100 * 2.8 * SE_EX_ANTE * DAYS_PER_YEAR:.2f}%/rok; "
        f"górna granica ½·CSV {100 * HALF_CSV_EX_ANTE * DAYS_PER_YEAR:.1f}%/rok; koszt {100 * COST_EX_ANTE * DAYS_PER_YEAR:.2f}%/rok\n"
        f"  ex post: sd premii netto {100 * w['sd']:.5f}%/dzień, N_eff {w['n_eff']:.0f}/{w['n']}, se_neff {100 * w['se_neff']:.5f}% → "
        f"wykrywalny efekt {100 * 2.8 * w['se_neff'] * DAYS_PER_YEAR:.2f}%/rok"
    )
    print(f"\n  czas całkowity: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
