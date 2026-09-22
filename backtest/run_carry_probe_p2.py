"""
run_carry_probe_p2.py — sonda wykonalności carry przekrojowego (runda P2).

Pre-rejestracja: `runs/2026-09-22_p2-sonda-carry-przekrojowy/README.md` (commit 364e98d).
Skrypt jest neutralnym reporterem: drukuje pomiary 1–5 i stan kryteriów D1/D2; decyzję
podpisuje write-up rundy.

WARUNEK „0 WARIANTÓW": skrypt NIE liczy i NIE drukuje średniej `R` ani średniej `F − C + R`.
Szereg `F − C + R` trafia wyłącznie do `dispersion_neff`, która zwraca rozrzut i N_eff.

Użycie:
    py -m backtest.run_carry_probe_p2 <cache_dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import ccxt
import numpy as np
import pandas as pd

from backtest.carry_probe import (
    TOP_N,
    avg_pairwise_corr,
    compute_windows,
    dispersion_neff,
    k_effective,
    mean_ci_neff,
    prepare_symbol,
    required_windows,
    window_starts,
)
from data.fetch_universe import cache_paths, list_archive_symbols, list_tradifi_ids, select_universe

START = "2020-01-01T00:00:00Z"
END = "2026-07-01T00:00:00Z"
C_RT_BASE = 0.000767  # H3: realny koszt round-trip w modelu kosztów projektu
C_RT_TAKER = 0.0014  # wrażliwość: (taker 0,05% + poślizg 0,02%) × 2 końce


def load_universe(cache_dir: str) -> tuple[dict, dict]:
    ex = ccxt.binanceusdm()
    archive = list_archive_symbols()
    listed = {m["id"] for m in ex.load_markets().values()}
    universe = select_universe(archive, list_tradifi_ids(ex))
    data, missing = {}, []
    for sym in universe:
        f_path, k_path = cache_paths(cache_dir, sym)
        if not (f_path.exists() and k_path.exists()):
            missing.append(sym)
            continue
        fund, kl = pd.read_parquet(f_path), pd.read_parquet(k_path)
        if fund.empty or kl.empty:
            continue
        data[sym] = prepare_symbol(fund, kl)
    meta = {
        "archive": len(archive),
        "universe": len(universe),
        "with_data": len(data),
        "missing_cache": missing,
        "archive_only": sorted(s for s in data if s not in listed),
    }
    return data, meta


def fmt_pct(x: float, nd: int = 4) -> str:
    return f"{100 * x:.{nd}f}%"


def report_block(name: str, w: pd.DataFrame, c_col: str) -> dict:
    live = w[~w["skipped"]]
    net = live["F"] - live[c_col]
    econ = mean_ci_neff(net)
    fstats = mean_ci_neff(live["F"])
    total = live["F"] - live[c_col] + live["R"]
    disp = dispersion_neff(total)
    n_req = required_windows(econ["mean"], disp["std"])
    print(f"\n=== {name} ===")
    print(f"  okna ważne / wszystkie        : {len(live)} / {len(w)}")
    print(f"  zakwalifikowanych (mediana)   : {live['n_eligible'].median():.0f}")
    print(
        f"  koszyk (mediana n_short/long) : {live['n_short'].median():.0f} / {live['n_long'].median():.0f}"
    )
    print(
        f"  obrót (średnio short/long)    : {live['turnover_short'].mean():.3f} / {live['turnover_long'].mean():.3f}"
    )
    print(f"  trwałość rang (Spearman, śr.) : {live['persistence_spearman'].mean():.3f}")
    print(
        f"  F (funding otrzymany, 48h)    : śr. {fmt_pct(fstats['mean'])}  mediana {fmt_pct(fstats['median'])}"
    )
    print(f"  C (koszt, 48h)                : śr. {fmt_pct(live[c_col].mean())}")
    print(
        f"  mu_net = F − C                : śr. {fmt_pct(econ['mean'])}  mediana {fmt_pct(econ['median'])}  "
        f"CI95 [{fmt_pct(econ['ci_low'])}; {fmt_pct(econ['ci_high'])}]  (n={econ['n']}, N_eff={econ['n_eff']:.0f})"
    )
    print(f"  udział okien z F − C > 0      : {(net > 0).mean():.3f}")
    print(
        f"  sigma(F − C + R)              : {fmt_pct(disp['std'])}  (N_eff={disp['n_eff']:.0f} z n={disp['n']})"
    )
    print(
        f"  n_req (moc 80%)               : {n_req:,.0f} okien"
        if np.isfinite(n_req)
        else "  n_req (moc 80%)               : inf (mu_net <= 0)"
    )
    print(
        f"  N_eff dostępne / n_req        : {disp['n_eff'] / n_req:.3f}"
        if np.isfinite(n_req)
        else "  N_eff dostępne / n_req        : 0"
    )
    return {"econ": econ, "disp": disp, "n_req": n_req, "n_live": len(live)}


def main(cache_dir: str) -> int:
    data, meta = load_universe(cache_dir)
    print("P2 — sonda wykonalności carry przekrojowego")
    print(f"zakres {START} -> {END}, okna 48h, decyle, c_rt bazowy {fmt_pct(C_RT_BASE)}")

    print("\n=== Pomiar 1: uniwersum i przeżywalność ===")
    print(f"  symboli w archiwum            : {meta['archive']}")
    print(f"  uniwersum P2 (USDT, bez TRADIFI/stable): {meta['universe']}")
    print(f"  z danymi                      : {meta['with_data']}")
    print(
        f"  brak w cache                  : {len(meta['missing_cache'])} {meta['missing_cache'][:10]}"
    )
    print(
        f"  TYLKO w archiwum (niewidoczne na bieżącej liście giełdy): {len(meta['archive_only'])}"
    )
    print(f"    przykłady: {meta['archive_only'][:15]}")

    starts = window_starts(START, END)
    w_top, rets_top = compute_windows(data, starts, C_RT_BASE, top_n=TOP_N)
    w_all, _ = compute_windows(data, starts, C_RT_BASE, top_n=None)
    for w in (w_top, w_all):
        live = ~w["skipped"]
        w.loc[live, "C_taker"] = C_RT_TAKER * (
            w.loc[live, "turnover_short"] + w.loc[live, "turnover_long"]
        )
        w.loc[live, "C_full"] = 2 * C_RT_BASE

    print("\n=== Pomiary 2–4 ===")
    base = report_block("TOP50, koszt bazowy (PODSTAWOWY — kryteria D1/D2)", w_top, "C")
    report_block("TOP50, koszt taker 0,14% (wrażliwość)", w_top, "C_taker")
    report_block("TOP50, obrót = 1 (wrażliwość)", w_top, "C_full")
    report_block("ALL, koszt bazowy (wrażliwość)", w_all, "C")

    print("\n=== Pomiar 5: kontrola założenia z STATUS §17 (przekrój ≠ niezależne próby) ===")
    rho = avg_pairwise_corr(rets_top)
    k = float(w_top.loc[~w_top["skipped"], "n_eligible"].median())
    print(f"  przeciętna korelacja parowa zwrotów 48h (TOP50): {rho:.3f}")
    print(f"  k = {k:.0f} instrumentów -> k_eff = {k_effective(k, rho):.1f} niezależnych")
    print(
        f"  koszyk decylowy ({int(k * 0.1)} szt.) -> k_eff = {k_effective(max(2, int(k * 0.1)), rho):.2f}"
    )

    print("\n=== Kryteria (pre-rejestracja) ===")
    d1 = base["econ"]["ci_low"] > 0
    d2 = np.isfinite(base["n_req"]) and base["disp"]["n_eff"] >= base["n_req"]
    print(
        f"  D1 (ci_low mu_net > 0)        : {'SPEŁNIONE' if d1 else 'NIESPEŁNIONE'}  (ci_low = {fmt_pct(base['econ']['ci_low'])})"
    )
    print(
        f"  D2 (N_eff >= n_req)           : {'SPEŁNIONE' if d2 else 'NIESPEŁNIONE'}  (N_eff = {base['disp']['n_eff']:.0f}, n_req = {base['n_req']:,.0f})"
    )
    print(
        f"  WERDYKT                       : {'WYKONALNA' if d1 and d2 else ('NIEWYKONALNA ekonomicznie' if not d1 else 'NIEMIERZALNA')}"
    )

    out = Path(cache_dir) / "p2_windows_top50.parquet"
    w_top.drop(columns=["R"], errors="ignore").to_parquet(out, index=False)
    print(f"\n(szereg okien TOP50 bez kolumny R zapisany: {out})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "data/raw/universe"))
