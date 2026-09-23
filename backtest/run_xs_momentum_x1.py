"""
run_xs_momentum_x1.py — runda X1: momentum przekrojowe (rodzina B1) na uniwersum point-in-time
top-20 po obrocie; sygnał = zwrot 28 dni, long top-5 / short bottom-5, trzymanie 7 dni, koszty
obrotu obu nóg + funding per symbol. Pre-rejestracja (PRZED tym skryptem):
runs/2026-09-23_x1-momentum-przekrojowe/README.md.

Uruchomienie:  py -m backtest.run_xs_momentum_x1 [universe_dir]   (Windows: PYTHONUTF8=1)
               py -m backtest.run_xs_momentum_x1 --moc [n_sim]      # rachunek mocy (losowe rankingi)

Skrypt czyta WYŁĄCZNIE cache i config — bez sieci. Neutralny reporter: drukuje odczyt kryterium
z pre-rejestracji; werdykt podpisuje Claude w README rundy.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.xs_momentum import (
    HOLD_DAYS,
    LEG_SIZE,
    SIGNAL_LOOKBACK_DAYS,
    daily_funding_panel,
    long_short_returns,
    rebalance_dates,
    simulate_null_means,
    weekly_ic,
)

UNIVERSE_DIR = "data/raw/universe"
FIRST_MONTH = "2021-02-01"  # jak R1: pierwszy miesiąc z pełnym oknem obrotu wewnątrz 2021
END = "2026-07-01"  # koniec bazy (zasada 20)
DAYS_PER_YEAR = 365
Z95 = 1.959964
N_SIM_DEFAULT = 100
SEP = "=" * 104


def _verdict(w: dict) -> str:
    if w["t_neff"] > Z95:
        return "POZYTYWNY — t_neff > 1,96 (dolny kraniec CI 95% średniego zwrotu netto nad zerem)"
    if w["ci_high"] < 0:
        return "NEGATYWNY — górny kraniec CI 95% średniego zwrotu netto poniżej zera"
    return "NIEROZSTRZYGNIĘTY — CI obejmuje zero"


def _load(universe_dir: str):
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, volume = load_universe(universe_dir)
    funding = daily_funding_panel(universe_dir)
    end = pd.Timestamp(END, tz="UTC")
    close = close[close.index < end]
    month_starts = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, month_starts)
    dates = rebalance_dates(close.index, pd.Timestamp(FIRST_MONTH, tz="UTC"), end, HOLD_DAYS)
    return fee, close, funding, members, dates


def _print_header(fee: float, close, members, dates) -> None:
    n_syms = len({s for v in members.values() for s in v})
    print(
        f"dane   : uniwersum {close.shape[1]} symboli 1d ({close.index.min().date()} → {close.index.max().date()}), "
        f"{len(members)} koszyków miesięcznych po obrocie ({n_syms} różnych symboli), "
        f"{len(dates)} formowań co {HOLD_DAYS} dni od {dates[0].date()} do {dates[-1].date()}\n"
        f"reguła : sygnał = zwrot {SIGNAL_LOOKBACK_DAYS} dni (zamknięcia ≤ t), long top-{LEG_SIZE} / short bottom-{LEG_SIZE}, "
        f"kapitał 1 = 0,5 + 0,5, wagi dryfują {HOLD_DAYS} dni; koszt {100 * fee:.2f}% × obrót obu nóg; funding: long płaci, short otrzymuje\n"
    )


def run_power(universe_dir: str, n_sim: int) -> None:
    t0 = time.time()
    fee, close, funding, members, dates = _load(universe_dir)
    print(SEP)
    print(
        f"X1 — RACHUNEK MOCY Z SYMULACJI: {n_sim} losowych rankingów na realnym panelu (bez patrzenia na sygnał)"
    )
    print(SEP)
    _print_header(fee, close, members, dates)
    sims = simulate_null_means(close, funding, members, dates, fee, n_sim=n_sim, seed=0)
    se_emp = float(sims["mean_net"].std(ddof=1))
    n_days = int(sims["n_days"].iloc[0])
    print(f"  dni w szeregu: {n_days}; symulacji: {len(sims)}")
    print(
        f"  pod H0 (losowy ranking): średnia dzienna netto {100 * sims['mean_net'].mean():+.4f}% "
        f"(brutto {100 * sims['mean_gross'].mean():+.4f}%, funding {100 * sims['mean_funding'].mean():+.4f}%, "
        f"koszt {100 * sims['mean_cost'].mean():.4f}% = {100 * sims['mean_cost'].mean() * DAYS_PER_YEAR:.2f}%/rok)"
    )
    print(
        f"  sd dzienna netto (typowa): {100 * sims['sd_net'].median():.3f}% ; acf1: {sims['acf1_net'].median():+.3f}"
    )
    print(
        f"  EMPIRYCZNE se średniej dziennej pod H0 = sd(średnich między symulacjami) = {100 * se_emp:.4f}%/dzień "
        f"→ half-width 95% = {100 * Z95 * se_emp:.4f}%/dzień = {100 * Z95 * se_emp * DAYS_PER_YEAR:.1f}%/rok"
    )
    print(
        f"  se analityczne (sd/√n): {100 * sims['sd_net'].median() / np.sqrt(n_days):.4f}%/dzień "
        f"→ half-width {100 * Z95 * sims['sd_net'].median() / np.sqrt(n_days) * DAYS_PER_YEAR:.1f}%/rok"
    )
    print(f"  czas: {time.time() - t0:.0f}s")


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--moc":
        run_power(
            argv[2] if len(argv) > 2 else UNIVERSE_DIR,
            int(argv[1]) if len(argv) > 1 else N_SIM_DEFAULT,
        )
        return
    universe_dir = argv[0] if argv else UNIVERSE_DIR
    t0 = time.time()
    fee, close, funding, members, dates = _load(universe_dir)
    print(SEP)
    print(
        "X1 — MOMENTUM PRZEKROJOWE (B1): long top-5 / short bottom-5 po zwrocie 28 dni, trzymanie 7 dni; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    _print_header(fee, close, members, dates)
    out = long_short_returns(close, funding, members, dates, fee)
    w = summarize_pnl(out["r_net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    wg = summarize_pnl(out["r_ls_gross"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)

    print(
        "1. KRYTERIUM — średni dzienny zwrot netto portfela long-short (% kapitału), CI z N_eff, annualizacja ×365"
    )
    print(
        f"  {'':>6} | {'n':>5} | {'średnia/dzień':>13} | {'CI 95% (N_eff)':>23} | {'mediana':>9} | {'t':>6} | {'N_eff':>6} | {'t_neff':>7} | {'rocznie':>22}"
    )
    print("  " + "-" * 120)
    for name, ww in (("netto", w), ("brutto", wg)):
        print(
            f"  {name:>6} | {ww['n']:5d} | {100 * ww['mean']:+12.4f}% | [{100 * ww['ci_low']:+8.4f}; {100 * ww['ci_high']:+8.4f}] | "
            f"{100 * ww['median']:+8.4f}% | {ww['t']:+6.2f} | {ww['n_eff']:6.0f} | {ww['t_neff']:+7.2f} | "
            f"{100 * ww['annual_notional']:+6.1f}% [{100 * ww['annual_notional_ci'][0]:+.1f}; {100 * ww['annual_notional_ci'][1]:+.1f}]"
        )
    print(f"  >>> ODCZYT KRYTERIUM (netto): {_verdict(w)}")

    print("\n2. DEKOMPOZYCJA — sumy za całą próbę (% kapitału) i obrót")
    n_form = int((out["turnover"] > 0).sum())
    print(
        f"  Σ brutto {100 * out['r_ls_gross'].sum():+.2f}% | Σ funding netto {100 * out['funding_net'].sum():+.2f}% | "
        f"Σ koszty {100 * out['cost'].sum():.2f}% | Σ netto {100 * out['r_net'].sum():+.2f}% | "
        f"obrót łączny {out['turnover'].sum():.1f} kapitału ({out['turnover'][out['turnover'] > 0].mean():.2f} na formowanie, {n_form} formowań z obrotem)\n"
        f"  noga long: średnia dzienna {100 * out['r_long'].mean():+.4f}% | noga short: {100 * out['r_short'].mean():+.4f}% | "
        f"dni bez pozycji: {int((out['n_long'] == 0).sum())} | dni z zwrotem netto > 0: {100 * (out['r_net'] > 0).mean():.1f}%"
    )
    years = out["date"].dt.year
    print(
        f"  {'rok':>6} | {'dni':>4} | {'Σ netto':>8} | {'Σ brutto':>9} | {'Σ funding':>10} | {'Σ koszt':>8} | {'sd/dzień':>8} | {'long':>8} | {'short':>8}"
    )
    print("  " + "-" * 92)
    for y, g in out.groupby(years):
        print(
            f"  {y:6d} | {len(g):4d} | {100 * g['r_net'].sum():+7.2f}% | {100 * g['r_ls_gross'].sum():+8.2f}% | {100 * g['funding_net'].sum():+9.2f}% | "
            f"{100 * g['cost'].sum():7.2f}% | {100 * g['r_net'].std():7.3f}% | {100 * g['r_long'].sum():+7.1f}% | {100 * g['r_short'].sum():+7.1f}%"
        )

    print(
        "\n3. WTÓRNIE — rank IC tygodniowe (Spearman: sygnał vs zwrot 7 dni wśród członków) i neutralność do BTC"
    )
    ic = weekly_ic(close, members, dates)
    ic_mean, ic_se = float(ic["ic"].mean()), float(ic["ic"].std(ddof=1) / np.sqrt(len(ic)))
    print(
        f"  IC: n = {len(ic)} tygodni, średnia {ic_mean:+.4f} [{ic_mean - Z95 * ic_se:+.4f}; {ic_mean + Z95 * ic_se:+.4f}], "
        f"sd {ic['ic'].std(ddof=1):.3f}, ICIR {ic_mean / ic['ic'].std(ddof=1):+.3f}, udział IC > 0: {100 * (ic['ic'] > 0).mean():.1f}%, "
        f"średnio {ic['n'].mean():.1f} par"
    )
    if "BTCUSDT" in close.columns:
        btc = close["BTCUSDT"].pct_change().reindex(out["date"]).to_numpy()
        corr = float(np.corrcoef(np.nan_to_num(btc), out["r_net"].to_numpy())[0, 1])
        print(f"  korelacja dziennego zwrotu netto z BTC: {corr:+.3f}")
    print(
        f"  rozkład dziennego zwrotu netto: p05 {100 * out['r_net'].quantile(0.05):+.2f}%, p50 {100 * out['r_net'].median():+.3f}%, "
        f"p95 {100 * out['r_net'].quantile(0.95):+.2f}%, min {100 * out['r_net'].min():+.2f}%, max {100 * out['r_net'].max():+.2f}%"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
