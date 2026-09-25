"""
run_mx2_filtry.py — runda MX2 (decyzja użytkownika 2026-09-25): pięć filtrów na sygnale MX1
(przecięcie EMA 10/30 po wcześniejszym przecięciu MACD 12/26/9, BTC 1h) — `agents/mx_filters.py`:
trend 28 dni, ADX(14) > 25, wolumen powyżej średniej 20, sesja USA 13–21 UTC, RSI(14) po stronie 50.
Przyrząd i populacja jak MX1 (reguły A2 na bazie Y1). Pre-rejestracja:
runs/2026-09-25_mx2-filtry-1h/README.md.

    PYTHONUTF8=1 py -m backtest.run_mx2_filtry --moc

Neutralny reporter rachunku mierzalności (CLAUDE.md zasada 18): częstość sygnałów po każdym filtrze,
bariera, próg, wymagana trafność (bramka zasady 18 przy z = 1,96; wymóg pozytywu przy pięciu ramionach
z_5 = 2,576) i dokładna moc (dwumian). Bez symulacji transakcji i bez wyników — pełny pomiar wymagałby
nowej pre-rejestracji i osobnego skryptu.
"""

from __future__ import annotations

import sys
import time
from statistics import NormalDist

import numpy as np
import pandas as pd
import yaml
from scipy.stats import binom

from agents.labeling import ATR_MULTIPLIER
from agents.ml_optimizer import REVERSION_FEATURES
from agents.mx_filters import FILTERS, compute_mx2_rules
from backtest.checkpoint_lib import PRIMARY_SEED, build_rule_signals, fetch_window, load_config
from backtest.engine import REGIME_ALL, collect_signals
from backtest.metrics import (
    break_even_hit_rate,
    expected_trades,
    measurability_report,
    required_trades,
    wald_half_width,
)

TIMEFRAME = "1h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 24
TRAIN_DAYS, TEST_DAYS, STEP_DAYS = 60, 28, 28
CONTROL_FEATURES = list(REVERSION_FEATURES)
FILL_RATE_REF = 0.994
COST_REF = 0.000808
P_STAR_Y1 = 0.5401
P_ASSUMED = 0.56
M_ARMS = len(FILTERS)
Z_BONF = NormalDist().inv_cdf(1 - 0.025 / M_ARMS)
MX1_SIGNALS_REF = 1254
Y1_ROWS_REF = 46368
POWER_AT = (0.56, 0.58, 0.60, 0.62, 0.65)
NAMES = {
    "rule_macd_ema_cross": "MX1 bez filtra (odniesienie)",
    "rule_mx2_trend28": "trend 28 dni zgodny",
    "rule_mx2_adx25": "ADX(14) > 25",
    "rule_mx2_wolumen": "wolumen > średnia 20",
    "rule_mx2_sesja_usa": "sesja USA 13–21 UTC",
    "rule_mx2_rsi50": "RSI(14) po stronie 50",
}
SEP = "=" * 104


def k_min_for(n: int, p_ref: float, z: float) -> int | None:
    """Najmniejsza liczba trafień, przy której dolny kraniec CI (Wald, z) przekracza p_ref."""
    for k in range(n + 1):
        p = k / n
        if p - z * np.sqrt(p * (1 - p) / n) > p_ref:
            return k
    return None


def ex_ante(fdf: pd.DataFrame, folds: list[dict], col: str) -> dict:
    signals, funnel = build_rule_signals(fdf, folds, col)
    n = funnel["n_signals"]
    b = np.array([ATR_MULTIPLIER * s["atr_14"] / s["entry_price"] for s in signals])
    b_med = float(np.median(b)) if n else float("nan")
    be_formula = break_even_hit_rate(COST_REF, b_med) if n else float("nan")
    p_ref = max(be_formula, P_STAR_Y1) if n else P_STAR_Y1
    n_exp = expected_trades(n, 0.0, FILL_RATE_REF)
    n_int = int(round(n_exp))
    k_bonf = k_min_for(n_int, p_ref, Z_BONF) if n_int > 0 else None
    power = {
        p: (float(binom.sf(k_bonf - 1, n_int, p)) if k_bonf is not None else 0.0) for p in POWER_AT
    }
    return {
        "n": n,
        "long": sum(s["signal_direction"] > 0 for s in signals),
        "short": sum(s["signal_direction"] < 0 for s in signals),
        "cost_gated": funnel["n_cost_gated"],
        "b_med": b_med,
        "be_formula": be_formula,
        "p_ref": p_ref,
        "n_exp": n_exp,
        "half_width": wald_half_width(n_int) if n_int > 0 else float("nan"),
        "report": measurability_report(P_ASSUMED, p_ref, n_exp),
        "need_bonf": (k_bonf / n_int) if k_bonf is not None else float("nan"),
        "power": power,
        "n_req_negative": required_trades(0.50, p_ref),
    }


def main(argv: list[str]) -> int:
    t0 = time.time()
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    print(SEP)
    print(
        "MX2 — pięć filtrów na sygnale MX1 (MACD, potem EMA 10/30; BTC 1h) — rachunek mierzalności"
    )
    print(SEP)
    df = fetch_window(data_cfg, TIMEFRAME)
    raw = pd.concat([df, compute_mx2_rules(df, CANDLES_PER_DAY)], axis=1)
    collected = collect_signals(
        raw,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, CONTROL_FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    folds, fdf = collected["folds_summary"], collected["df"]
    active = [f for f in folds if not f["skipped"]]
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    print(
        f"dane: {len(df)} świec {TIMEFRAME} ({df['timestamp'].min()} → {df['timestamp'].max()}); populacja: "
        f"{len(active)}/{len(folds)} okien, {n_rows} świec (Y1/MX1: {Y1_ROWS_REF} → "
        f"{'ZGODNA' if n_rows == Y1_ROWS_REF else 'ROZJAZD'})\n"
        f"bramka zasady 18: zakładana trafność {100 * P_ASSUMED:.0f}%, z = 1,96; wymóg pozytywu przy {M_ARMS} "
        f"filtrach: z_5 = {Z_BONF:.3f}; próg odniesienia = max(0,5(1 + C/B) na świecach sygnału, p* Y1 "
        f"{100 * P_STAR_Y1:.2f}%)\n"
    )
    cols = ["rule_macd_ema_cross", *[f"rule_mx2_{f}" for f in FILTERS]]
    ante = {c: ex_ante(fdf, folds, c) for c in cols}
    base_n = ante["rule_macd_ema_cross"]["n"]
    print(
        f"  kontrola: sygnały MX1 bez filtra {base_n} (MX1: {MX1_SIGNALS_REF} → "
        f"{'ZGODNE' if base_n == MX1_SIGNALS_REF else 'ROZJAZD'})\n"
    )
    print(
        f"  {'filtr':>28} | {'sygnały':>7} | {'bramka':>6} | {'zostaje':>7} | {'long/short':>11} | {'bariera':>7} | "
        f"{'próg':>6} | {'half-w.':>7} | {'trzeba (1,96)':>13} | {'trzeba (z_5)':>12} | {'zasada 18':>12}"
    )
    print("  " + "-" * 147)
    for c in cols:
        a = ante[c]
        print(
            f"  {NAMES[c]:>28} | {a['n']:7d} | {a['cost_gated']:6d} | {100 * a['n'] / base_n:6.1f}% | {a['long']:5d}/{a['short']:<5d} | "
            f"{100 * a['b_med']:6.3f}% | {100 * a['p_ref']:5.2f}% | {100 * a['half_width']:5.2f} pp | "
            f"{100 * a['report']['p_detectable']:12.2f}% | {100 * a['need_bonf']:11.2f}% | {a['report']['verdict']:>12}"
        )
    print(
        "\n  Dokładna moc (dwumian) przy wymogu pozytywu z_5 — szansa potwierdzenia, gdyby filtr naprawdę trafiał:"
    )
    print(f"  {'filtr':>28} | " + " | ".join(f"{100 * p:5.0f}%" for p in POWER_AT))
    for c in cols[1:]:
        a = ante[c]
        print(f"  {NAMES[c]:>28} | " + " | ".join(f"{100 * a['power'][p]:5.1f}%" for p in POWER_AT))
    print(
        "\n  Strona negatywna: required_trades(0,50; próg) = "
        + ", ".join(f"{NAMES[c]} {ante[c]['n_req_negative']:,.0f}" for c in cols[1:2])
        + " (dla wszystkich filtrów ten sam próg odniesienia)"
    )
    print(f"\n  (bez symulacji transakcji; czas {time.time() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
