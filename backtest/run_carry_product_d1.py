"""
run_carry_product_d1.py — runda D1: produkt cash-and-carry po dodatnim C1a — depozyt i likwidacja
krótkiej nogi (Q1), wariant COIN-M (Q2), basis kontraktów kwartalnych (Q3), stopa T-bill (Q4).
Pre-rejestracja (PRZED tym skryptem): runs/2026-09-23_d1-produkt-carry/README.md.

Uruchomienie:  py -m backtest.run_carry_product_d1   (Windows: PYTHONUTF8=1)

Skrypt czyta WYŁĄCZNIE cache (data/raw, data/raw/external) i config — bez sieci. Neutralny
reporter: drukuje tabele i przedziały z pre-rejestracji; nie wybiera „najlepszego wariantu";
interpretację podpisuje Claude w README rundy, decyzję o produkcie podejmuje użytkownik.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import (
    CarryCosts,
    align_carry_frame,
    hedged_carry_pnl,
    state_always_on,
    summarize_pnl,
)
from backtest.carry_product import (
    DAYS_PER_YEAR,
    MAINTENANCE_MARGIN,
    PERIODS_PER_DAY,
    annualized_basis,
    basis_vs_funding,
    floor_to_grid,
    front_contract,
    inverse_carry_pnl,
    margin_grid,
    max_runup_table,
    yearly_fraction,
    yearly_mean,
    yearly_sum,
)
from backtest.checkpoint_lib import load_config
from data.fetch_funding import get_funding_rate_history_cached
from data.fetch_ohlcv import get_ohlcv_cached

SPOT_SYMBOL = "BTC/USDT"
PERP_SYMBOL = "BTC/USDT:USDT"
TIMEFRAME = "8h"
START = "2021-01-01T00:00:00Z"  # zasada 20
EXTERNAL_DIR = "data/raw/external"
CM_FUNDING_PATH = f"{EXTERNAL_DIR}/binance_cm_funding_BTCUSD_PERP.parquet"
DATED_PATH = f"{EXTERNAL_DIR}/binance_um_dated_BTCUSDT_8h.parquet"
FRED_PATH = f"{EXTERNAL_DIR}/fred_DTB3_1d.parquet"
ENTRY_DAYS = (90, 60, 30)
SEP = "=" * 104


def _ci(w: dict, key: str, scale: float = 100.0, digits: int = 2) -> str:
    lo, hi = w[key]
    return f"[{scale * lo:+.{digits}f}; {scale * hi:+.{digits}f}]"


def _window(df: pd.DataFrame, col: str, start: str, end: str) -> pd.DataFrame:
    ts = pd.to_datetime(df[col], utc=True)
    return df[(ts >= pd.Timestamp(start)) & (ts < pd.Timestamp(end))].reset_index(drop=True)


def _yearly_annualized(pnl: pd.DataFrame, capital: float) -> pd.Series:
    """Σ P&L per rok / ułamek roku / kapitał → zwrot roczny na kapitale (lata niepełne annualizowane)."""
    return yearly_sum(pnl, "pnl") / yearly_fraction(pnl) / capital


def main() -> None:
    t0 = time.time()
    cfg = load_config()
    data_cfg, cost_cfg = cfg["data"], cfg["costs"]
    end = data_cfg["end"]
    costs = CarryCosts(
        spot_fee=cost_cfg["spot_fee_rate"],
        perp_fee=cost_cfg["taker_fee_rate"],
        slippage=cost_cfg["slippage_bps"] / 10_000.0,
    )
    print(SEP)
    print(
        "D1 — PRODUKT CASH-AND-CARRY: depozyt/likwidacja (Q1), COIN-M (Q2), basis kwartalny (Q3), T-bill (Q4)"
    )
    print(SEP)

    spot = get_ohlcv_cached(SPOT_SYMBOL, TIMEFRAME, START, end, data_cfg["cache_dir"], "binance")
    perp = get_ohlcv_cached(
        PERP_SYMBOL, TIMEFRAME, START, end, data_cfg["cache_dir"], "binanceusdm"
    )
    funding_um = get_funding_rate_history_cached(
        PERP_SYMBOL,
        data_cfg["timeframe_start_overrides"]["4h"],
        end,
        data_cfg["cache_dir"],
        data_cfg["exchange_id"],
    )
    funding_um = funding_um[funding_um["timestamp"] >= pd.Timestamp(START)].reset_index(drop=True)
    frame = align_carry_frame(spot, perp, funding_um)
    c1a = hedged_carry_pnl(frame, state_always_on(frame), costs)
    w_c1a = summarize_pnl(c1a["pnl"])
    years = len(perp) / (PERIODS_PER_DAY * DAYS_PER_YEAR)
    print(
        f"dane   : spot {len(spot)} / perp {len(perp)} / funding USDT-M {len(funding_um)} od {START[:10]} do {end[:10]} "
        f"({years:.2f} roku); C1a odtworzone: {100 * w_c1a['annual_notional']:+.2f}%/rok nominału "
        f"{_ci(w_c1a, 'annual_notional_ci')}, kapitał 2×: {100 * w_c1a['annual_capital']:+.2f}%\n"
        f"koszty : wejście {100 * costs.switch_cost:.2f}% nominału i tyle samo wyjście; likwidacja 1,25% + 0,07% ponowne wejście; "
        f"maintenance {100 * MAINTENANCE_MARGIN:.1f}%\n"
    )

    # ------------------------------------------------------------------ Q1
    print(
        "Q1. DEPOZYT I LIKWIDACJA KRÓTKIEJ NOGI USDT-M — run-up ceny perp w oknie (rozkład, % ceny startowej)"
    )
    price = perp["close"].reset_index(drop=True)
    ru = max_runup_table(price)
    print(
        f"  {'okno [dni]':>10} | {'max':>8} | {'p99':>8} | {'p95':>8} | {'udział > 50%':>12} | {'udział > 100%':>13}"
    )
    print("  " + "-" * 72)
    for _, r in ru.iterrows():
        print(
            f"  {int(r['horizon_days']):10d} | {100 * r['max']:+7.1f}% | {100 * r['p99']:+7.1f}% | {100 * r['p95']:+7.1f}% | "
            f"{100 * r['share_gt_50pct']:11.2f}% | {100 * r['share_gt_100pct']:12.2f}%"
        )
    print(
        "\n  siatka depozyt M (nominału) × uzupełnienie depozytu co N dni: likwidacje 2021→2026-07, koszt, "
        "maks. wykorzystanie depozytu, koszt uzupełnień (obrót × 0,19%), zwrot C1a na kapitale (1+M) po obu kosztach"
    )
    grid = margin_grid(price, w_c1a["annual_notional"], years=years, switch_cost=costs.switch_cost)
    print(
        f"  {'M':>5} | {'uzupełnienie':>12} | {'likwidacje':>10} | {'uzupełnień':>10} | {'max wykorzystanie':>17} | "
        f"{'koszt likw./rok':>15} | {'obrót uzup.':>11} | {'koszt uzup./rok':>15} | {'rocznie na kapitale':>19}"
    )
    print("  " + "-" * 136)
    for _, r in grid.iterrows():
        reset = "nigdy" if pd.isna(r["reset_days"]) else f"{int(r['reset_days'])} dni"
        print(
            f"  {r['margin']:5.2f} | {reset:>12} | {int(r['n_liquidations']):10d} | {int(r['n_resets']):10d} | "
            f"{100 * r['max_usage']:+16.1f}% | {100 * r['annual_liq_cost']:14.2f}% | {100 * r['rebalance_turnover']:10.0f}% | "
            f"{100 * r['annual_rebalance_cost']:14.2f}% | {100 * r['annual_on_capital']:+18.2f}%"
        )
    print(
        f"  próg likwidacji = M − {100 * MAINTENANCE_MARGIN:.1f}% (wzrost ceny od ostatniego uzupełnienia)\n"
    )

    # ------------------------------------------------------------------ Q2
    print(
        "Q2. CARRY COIN-M (1 BTC zabezpieczenia + short inverse; wartość USD stała, kapitał 1×) vs USDT-M"
    )
    cm = pd.read_parquet(CM_FUNDING_PATH)
    cm["timestamp"] = floor_to_grid(cm["timestamp"])
    cm = cm.drop_duplicates("timestamp").sort_values("timestamp")
    cm = _window(cm, "timestamp", START, end)
    cm_pnl = inverse_carry_pnl(cm, costs.switch_cost)
    w_cm = summarize_pnl(cm_pnl["pnl"], capital_per_notional=1.0)
    um_only = pd.DataFrame({"timestamp": frame["timestamp"], "funding_rate": frame["f_next"]})
    um_pnl = inverse_carry_pnl(um_only, costs.switch_cost)  # ten sam rachunek: sam funding − koszty
    w_um1 = summarize_pnl(um_pnl["pnl"], capital_per_notional=1.0)
    print(
        f"  {'rynek':>7} | {'n':>5} | {'średnia/8h':>11} | {'CI 95% (N_eff)':>27} | {'mediana':>9} | {'N_eff':>6} | {'t_neff':>7} | "
        f"{'rocznie nominał':>28} | {'rocznie na kapitale':>28}"
    )
    print("  " + "-" * 150)
    for name, w, cap in (("COIN-M", w_cm, 1.0), ("USDT-M", w_um1, 2.0)):
        ann_cap = (w["annual_notional"] / cap, tuple(x / cap for x in w["annual_notional_ci"]))
        print(
            f"  {name:>7} | {w['n']:5d} | {100 * w['mean']:+10.5f}% | [{100 * w['ci_low']:+9.5f}; {100 * w['ci_high']:+9.5f}] | "
            f"{100 * w['median']:+8.5f}% | {w['n_eff']:6.0f} | {w['t_neff']:+7.2f} | "
            f"{100 * w['annual_notional']:+6.2f}% {_ci(w, 'annual_notional_ci')} | "
            f"{100 * ann_cap[0]:+6.2f}% [{100 * ann_cap[1][0]:+.2f}; {100 * ann_cap[1][1]:+.2f}] (kapitał {cap:.0f}×)"
        )
    diff = cm[["timestamp", "funding_rate"]].merge(
        um_only, on="timestamp", suffixes=("_cm", "_um"), how="inner"
    )
    d = diff["funding_rate_cm"] - diff["funding_rate_um"]
    w_d = summarize_pnl(d, capital_per_notional=1.0)
    print(
        f"  różnica stawek COIN-M − USDT-M na wspólnych {w_d['n']} rozliczeniach: {100 * w_d['mean']:+.5f}%/8h "
        f"[{100 * w_d['ci_low']:+.5f}; {100 * w_d['ci_high']:+.5f}] (N_eff {w_d['n_eff']:.0f}) = "
        f"{100 * w_d['annual_notional']:+.2f}%/rok {_ci(w_d, 'annual_notional_ci')}; "
        f"masa punktowa COIN-M na 0,0100%: {100 * (cm['funding_rate'] == 0.0001).mean():.1f}%, "
        f"ujemne: {100 * (cm['funding_rate'] < 0).mean():.1f}%; korelacja stawek {diff['funding_rate_cm'].corr(diff['funding_rate_um']):.2f}"
    )
    print(
        f"  half-width ex post COIN-M: {100 * (w_cm['ci_high'] - w_cm['mean']) * PERIODS_PER_DAY * DAYS_PER_YEAR:.2f}%/rok "
        f"(pre-rejestracja: ~1,2%/rok)\n"
    )

    # ------------------------------------------------------------------ Q3
    print(
        "Q3. BASIS KONTRAKTÓW KWARTALNYCH (F − S)/S annualizowany, front = najkrótszy ≥ 7 dni do wygaśnięcia"
    )
    dated = pd.read_parquet(DATED_PATH)
    dated["open_time"] = pd.to_datetime(dated["open_time"], utc=True)
    dated["expiry"] = pd.to_datetime(dated["expiry"], utc=True)
    basis = annualized_basis(dated, spot)
    front = front_contract(basis)
    fy = front["open_time"].dt.year
    print(
        f"  świec kontraktów po filtrach: {len(basis)} ({basis['contract'].nunique()} kontraktów), front: {len(front)} świec 8h, "
        f"{front['open_time'].min().date()} → {front['open_time'].max().date()}"
    )
    print(
        f"  {'rok':>6} | {'n':>5} | {'mediana':>8} | {'p25':>8} | {'p75':>8} | {'p05':>8} | {'p95':>8} | {'udział < 0':>10} | {'średnia':>8}"
    )
    print("  " + "-" * 92)
    for y, g in front.groupby(fy):
        a = g["annualized"]
        print(
            f"  {y:6d} | {len(a):5d} | {100 * a.median():+7.2f}% | {100 * a.quantile(0.25):+7.2f}% | {100 * a.quantile(0.75):+7.2f}% | "
            f"{100 * a.quantile(0.05):+7.2f}% | {100 * a.quantile(0.95):+7.2f}% | {100 * (a < 0).mean():9.1f}% | {100 * a.mean():+7.2f}%"
        )
    a = front["annualized"]
    print(
        f"  {'razem':>6} | {len(a):5d} | {100 * a.median():+7.2f}% | {100 * a.quantile(0.25):+7.2f}% | {100 * a.quantile(0.75):+7.2f}% | "
        f"{100 * a.quantile(0.05):+7.2f}% | {100 * a.quantile(0.95):+7.2f}% | {100 * (a < 0).mean():9.1f}% | {100 * a.mean():+7.2f}%"
    )
    expired = basis[basis["expiry"] + pd.Timedelta(hours=8) <= pd.Timestamp(end)]
    cmp = basis_vs_funding(expired, funding_um, entry_days=ENTRY_DAYS)
    print(
        f"\n  ex post: baza zamknięta na wejściu vs funding USDT-M zrealizowany do wygaśnięcia — kontrakty wygasłe do {end[:10]}: "
        f"{expired['contract'].nunique()}; obie wielkości annualizowane"
    )
    print(
        f"  {'wejście':>8} | {'n':>3} | {'baza: mediana':>13} | {'funding: mediana':>16} | {'różnica: mediana':>16} | "
        f"{'różnica: min':>12} | {'różnica: max':>12} | {'baza > funding':>14}"
    )
    print("  " + "-" * 116)
    for dd, g in cmp.groupby("entry_days"):
        print(
            f"  {dd:5d} dni | {len(g):3d} | {100 * g['basis_annualized'].median():+12.2f}% | {100 * g['funding_annualized'].median():+15.2f}% | "
            f"{100 * g['diff_annualized'].median():+15.2f}% | {100 * g['diff_annualized'].min():+11.2f}% | "
            f"{100 * g['diff_annualized'].max():+11.2f}% | {100 * (g['diff_annualized'] > 0).mean():13.0f}%"
        )
    g90 = cmp[cmp["entry_days"] == ENTRY_DAYS[0]].sort_values("open_time")
    print(
        f"\n  per kontrakt, wejście {ENTRY_DAYS[0]} dni przed wygaśnięciem (annualizowane; baza zamknięta / funding zrealizowany / różnica):"
    )
    for _, r in g90.iterrows():
        print(
            f"    {r['contract']:>15} wejście {r['open_time'].date()}  baza {100 * r['basis_annualized']:+6.2f}%  "
            f"funding {100 * r['funding_annualized']:+6.2f}%  różnica {100 * r['diff_annualized']:+6.2f}%"
        )
    print()

    # ------------------------------------------------------------------ Q4
    print(
        "Q4. PER ROK: stopa T-bill 3M (FRED DTB3, % p.a.) obok zwrotu na KAPITALE (lata niepełne annualizowane)"
    )
    fred = pd.read_parquet(FRED_PATH)
    tb = yearly_mean(_window(fred, "date", START, end), "value", "date") / 100.0
    c1a_y = _yearly_annualized(c1a, 2.0)
    cm_y = _yearly_annualized(cm_pnl, 1.0)
    fr_y = front.groupby(fy)["annualized"].mean() / 2.0  # baza frontu, kapitał 2× (kontrakt USDT-M)
    print(
        f"  {'rok':>6} | {'T-bill':>7} | {'C1a USDT-M 2×':>14} | {'nadwyżka':>9} | {'COIN-M 1×':>10} | {'nadwyżka':>9} | "
        f"{'basis front 2×':>15} | {'nadwyżka':>9}"
    )
    print("  " + "-" * 100)
    for y in sorted(set(tb.index) | set(c1a_y.index) | set(cm_y.index)):
        t = tb.get(y, np.nan)
        a1, a2, a3 = c1a_y.get(y, np.nan), cm_y.get(y, np.nan), fr_y.get(y, np.nan)
        print(
            f"  {y:6d} | {100 * t:6.2f}% | {100 * a1:+13.2f}% | {100 * (a1 - t):+8.2f}% | {100 * a2:+9.2f}% | {100 * (a2 - t):+8.2f}% | "
            f"{100 * a3:+14.2f}% | {100 * (a3 - t):+8.2f}%"
        )
    print(
        "  uwagi: C1a i COIN-M = zrealizowany P&L (funding + hedge − koszty) / kapitał; basis front = ŚREDNIA stopa zamknięta\n"
        "  na wejściu w danym roku (nie P&L), na kapitale 2× jak każdy kontrakt USDT-M; T-bill = średnia dzienna stopa w roku.\n"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
