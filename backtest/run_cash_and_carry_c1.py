"""
run_cash_and_carry_c1.py — runda C1: cash-and-carry z hedgem spot na BTC (long spot + short perp),
ramiona C1a (zawsze w pozycji) i C1b (w pozycji po dodatnim ostatnim fundingu). Pre-rejestracja
(PRZED tym skryptem): runs/2026-09-23_c1-cash-and-carry/README.md.

Uruchomienie:  py -m backtest.run_cash_and_carry_c1   (Windows: PYTHONUTF8=1)

Skrypt czyta WYŁĄCZNIE cache (data/raw) i config — bez sieci. Neutralny reporter: drukuje odczyt
kryterium z pre-rejestracji (z_2 = 2,241 dla pozytywu); werdykt podpisuje Claude w README rundy.
"""

from __future__ import annotations

import time
from statistics import NormalDist

import pandas as pd

from backtest.carry_hedged import (
    CAPITAL_PER_NOTIONAL,
    PERIODS_PER_YEAR,
    CarryCosts,
    align_carry_frame,
    hedged_carry_pnl,
    max_drawdown,
    max_runup,
    state_after_positive_funding,
    state_always_on,
    summarize_pnl,
)
from backtest.checkpoint_lib import load_config
from data.fetch_funding import get_funding_rate_history_cached
from data.fetch_ohlcv import get_ohlcv_cached

SPOT_SYMBOL = "BTC/USDT"
PERP_SYMBOL = "BTC/USDT:USDT"
TIMEFRAME = "8h"
START = "2021-01-01T00:00:00Z"  # zasada 20
Z95 = 1.959964
M_ARMS = 2
Z_BONF = NormalDist().inv_cdf(1 - 0.025 / M_ARMS)
SEP = "=" * 104
SIGMA_DELTA_EX_ANTE = 0.000255  # std hedgu z profilu danych (pre-rejestracja)
FUNDING_MEAN_EX_ANTE = 0.000100


def _verdict(w: dict) -> str:
    if w["t_neff"] > Z_BONF:
        return f"POZYTYWNY — t_neff > z_2 = {Z_BONF:.3f} (dolny kraniec CI przy z_2 nad zerem)"
    if w["ci_high"] < 0:
        return "NEGATYWNY — górny kraniec CI 95% średniego P&L netto poniżej zera"
    return "NIEROZSTRZYGNIĘTY — CI obejmuje zero"


def _fmt_ci(ci: tuple[float, float], scale: float = 100.0, digits: int = 2) -> str:
    return f"[{scale * ci[0]:+.{digits}f}; {scale * ci[1]:+.{digits}f}]"


def _print_arm(name: str, w: dict) -> None:
    print(
        f"  {name:>4} | {w['n']:5d} | {100 * w['mean']:+8.5f}% | [{100 * w['ci_low']:+8.5f}; {100 * w['ci_high']:+8.5f}] | "
        f"{100 * w['median']:+8.5f}% | {w['t']:+7.2f} | {w['n_eff']:6.0f} | {w['t_neff']:+7.2f} | "
        f"{100 * w['annual_notional']:+6.2f}% {_fmt_ci(w['annual_notional_ci'])} | "
        f"{100 * w['annual_capital']:+6.2f}% {_fmt_ci(w['annual_capital_ci'])}"
    )


def main() -> None:
    t0 = time.time()
    cfg = load_config()
    data_cfg, cost_cfg = cfg["data"], cfg["costs"]
    costs = CarryCosts(
        spot_fee=cost_cfg["spot_fee_rate"],
        perp_fee=cost_cfg["taker_fee_rate"],
        slippage=cost_cfg["slippage_bps"] / 10_000.0,
    )
    print(SEP)
    print(
        "C1 — CASH-AND-CARRY Z HEDGEM SPOT (BTC): C1a zawsze w pozycji, C1b po dodatnim fundingu; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    spot = get_ohlcv_cached(
        SPOT_SYMBOL, TIMEFRAME, START, data_cfg["end"], data_cfg["cache_dir"], "binance"
    )
    perp = get_ohlcv_cached(
        PERP_SYMBOL, TIMEFRAME, START, data_cfg["end"], data_cfg["cache_dir"], "binanceusdm"
    )
    funding = get_funding_rate_history_cached(
        PERP_SYMBOL,
        data_cfg["timeframe_start_overrides"]["4h"],
        data_cfg["end"],
        data_cfg["cache_dir"],
        data_cfg["exchange_id"],
    )
    funding = funding[funding["timestamp"] >= pd.Timestamp(START)].reset_index(drop=True)
    frame = align_carry_frame(spot, perp, funding)
    print(
        f"dane      : spot {len(spot)} / perp {len(perp)} / funding {len(funding)} od {START} (zasada 20); "
        f"okresów po wyrównaniu {len(frame)}: {frame['timestamp'].min()} → {frame['timestamp'].max()}\n"
        f"koszty    : spot {100 * costs.spot_fee:.2f}% + perp {100 * costs.perp_fee:.2f}% + poślizg 2×{100 * costs.slippage:.2f}% "
        f"= {100 * costs.switch_cost:.2f}% nominału na wejście i tyle samo na wyjście; kapitał = {CAPITAL_PER_NOTIONAL:.0f}× nominał\n"
        f"kryterium : pozytyw t_neff > z_2 = {Z_BONF:.3f} (Bonferroni m = {M_ARMS}); negatyw: górny kraniec CI 95% < 0\n"
    )

    arms = {}
    for name, state_fn in (("C1a", state_always_on), ("C1b", state_after_positive_funding)):
        out = hedged_carry_pnl(frame, state_fn(frame), costs)
        arms[name] = (out, summarize_pnl(out["pnl"]))

    print("1. KRYTERIUM — średni P&L netto per okres 8h (% nominału), CI z N_eff, annualizacja")
    print(
        f"  {'ramię':>4} | {'n':>5} | {'średnia':>9} | {'CI 95%':>23} | {'mediana':>9} | {'t':>7} | {'N_eff':>6} | {'t_neff':>7} | "
        f"{'rocznie nominał':>28} | {'rocznie KAPITAŁ':>28}"
    )
    print("  " + "-" * 150)
    for name, (_, w) in arms.items():
        _print_arm(name, w)
    for name, (_, w) in arms.items():
        print(f"  >>> ODCZYT KRYTERIUM {name}: {_verdict(w)}")

    print("\n2. DEKOMPOZYCJA — skąd bierze się wynik (suma za całą próbę, % nominału)")
    print(
        f"  {'ramię':>4} | {'okresy w pozycji':>16} | {'Σ funding':>10} | {'Σ hedge (Δbazy)':>15} | {'Σ koszty':>9} | "
        f"{'Σ P&L':>8} | {'przełączenia':>12} | {'max obsunięcie':>14}"
    )
    print("  " + "-" * 112)
    for name, (out, _w) in arms.items():
        print(
            f"  {name:>4} | {int(out['state'].sum()):7d} ({100 * out['state'].mean():5.1f}%) | "
            f"{100 * out['funding_received'].sum():+9.2f}% | {100 * out['hedge'].sum():+14.2f}% | "
            f"{100 * out['cost'].sum():8.2f}% | {100 * out['pnl'].sum():+7.2f}% | {int(out['n_switches'].sum()):12d} | "
            f"{100 * max_drawdown(out['pnl']):13.2f}%"
        )
    first, last = frame["basis"].iloc[0], frame["basis"].iloc[-1]
    print(
        f"  baza na wejściu C1a {100 * first:+.3f}%, na wyjściu {100 * last:+.3f}% (efekt poziomu bazy: {100 * (first - last):+.3f}% dla short perp)\n"
        f"  funding: średnia {100 * frame['f_next'].mean():.4f}%/8h, dodatni w {100 * (frame['f_next'] > 0).mean():.1f}% okresów"
    )

    print(
        "\n3. PER ROK (OPISOWO, bez werdyktów) — C1a: średni P&L/8h, rocznie na nominale, składowe"
    )
    out_a = arms["C1a"][0].copy()
    out_a["rok"] = pd.to_datetime(out_a["timestamp"], utc=True).dt.year
    g = out_a.groupby("rok")
    print(
        f"  {'rok':>4} | {'okresy':>6} | {'P&L/8h':>10} | {'rocznie nom.':>12} | {'funding':>9} | {'hedge':>9} | {'koszty':>7}"
    )
    print("  " + "-" * 78)
    for yr, grp in g:
        print(
            f"  {yr:>4} | {len(grp):6d} | {100 * grp['pnl'].mean():+9.5f}% | {100 * grp['pnl'].mean() * PERIODS_PER_YEAR:+11.2f}% | "
            f"{100 * grp['funding_received'].sum():+8.2f}% | {100 * grp['hedge'].sum():+8.2f}% | {100 * grp['cost'].sum():6.2f}%"
        )
    print("  C1b per rok (średni P&L/8h, koszty):")
    out_b = arms["C1b"][0].copy()
    out_b["rok"] = pd.to_datetime(out_b["timestamp"], utc=True).dt.year
    for yr, grp in out_b.groupby("rok"):
        print(
            f"  {yr:>4} | {100 * grp['pnl'].mean():+9.5f}% | koszty {100 * grp['cost'].sum():6.2f}% | "
            f"w pozycji {100 * grp['state'].mean():5.1f}% | przełączenia {int(grp['n_switches'].sum())}"
        )

    print("\n4. RYZYKO NOGI SHORT (OPISOWO — nie modelowane w P&L)")
    for days in (30, 90):
        print(
            f"  max wzrost perp w oknie {days} dni: +{100 * max_runup(frame['perp_close'], days * 3):.0f}% "
            f"(short 1× bez uzupełnień depozytu z zysków spot: likwidacja przy ~+100%)"
        )
    print(
        f"  baza: std {100 * frame['basis'].std():.3f}%, p1/p99 [{100 * frame['basis'].quantile(0.01):+.3f}; {100 * frame['basis'].quantile(0.99):+.3f}]%"
    )

    print("\n5. MIERZALNOŚĆ (zasada 18) — ex ante vs ex post")
    w = arms["C1a"][1]
    se_ante = SIGMA_DELTA_EX_ANTE / (len(frame) ** 0.5)
    print(
        f"  ex ante: n {len(frame)}, se(Δ) {100 * se_ante:.5f}% → wykrywalny |efekt| {100 * 2.8 * se_ante:.5f}%/8h "
        f"({100 * 2.8 * se_ante * PERIODS_PER_YEAR:.2f}%/rok nominału); funding {100 * FUNDING_MEAN_EX_ANTE:.4f}% → t ≈ {FUNDING_MEAN_EX_ANTE / se_ante:.1f}\n"
        f"  ex post C1a: sd P&L {100 * w['sd']:.5f}%, N_eff {w['n_eff']:.0f}/{w['n']}, se_neff {100 * w['se_neff']:.5f}% → "
        f"wykrywalny |efekt| {100 * 2.8 * w['se_neff']:.5f}%/8h ({100 * 2.8 * w['se_neff'] * PERIODS_PER_YEAR:.2f}%/rok nominału)"
    )
    print(f"\n  czas całkowity: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
