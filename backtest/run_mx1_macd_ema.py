"""
run_mx1_macd_ema.py — runda MX1 (decyzja użytkownika 2026-09-25): przecięcie EMA 10/30 potwierdzone
WCZEŚNIEJSZYM przecięciem MACD 12/26/9 (`agents/ta_macd.py`) jako REGUŁA kierunkowa na BTC 1h, bez
modelu. Przyrząd jak A2 (`checkpoint_lib.build_rule_signals`: populacja = okna OOS pipeline'u
modelowego, bramka kosztowa silnika; wejście limit po close k = 1, bariera 1,5·ATR, V = 3 świece,
pojedyncze wyjście) na bazie 1h jak Y1 (walk-forward 60/28/28 dni, 24 świece na dzień).
Pre-rejestracja (PRZED przebiegiem): runs/2026-09-25_mx1-macd-ema-1h/README.md.

    PYTHONUTF8=1 py -m backtest.run_mx1_macd_ema --moc   # częstość sygnałów i mierzalność (ex ante)

Neutralny reporter rachunku mierzalności (CLAUDE.md zasada 18): bez symulacji transakcji i bez
wyników. Wynik rundy: NIEMIERZALNA → runda nie startuje; pełny przebieg nie jest zaimplementowany
(byłby nieprzetestowanym kodem w zamrożonym pliku) — ewentualny pomiar = nowa pre-rejestracja
i nowy skrypt. Ramię „samo przecięcie EMA” = odniesienie opisowe (0 wariantów).
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd
import yaml

from agents.labeling import ATR_MULTIPLIER
from agents.ml_optimizer import REVERSION_FEATURES
from agents.ta_macd import compute_macd_hist, compute_mx_rules
from backtest.checkpoint_lib import PRIMARY_SEED, build_rule_signals, fetch_window, load_config
from backtest.engine import REGIME_ALL, collect_signals
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule
from backtest.metrics import (
    break_even_hit_rate,
    expected_trades,
    measurability_report,
    required_trades,
    wald_half_width,
)

# --- konfiguracja ZAMROŻONA w pre-rejestracji (baza 1h jak Y1, przyrząd reguł jak A2) ---------
TIMEFRAME = "1h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 24
CANDLE_MINUTES = 60
TRAIN_DAYS, TEST_DAYS, STEP_DAYS = 60, 28, 28
CONTROL_FEATURES = list(REVERSION_FEATURES)  # model tylko wyznacza populację i etykiety (jak A2)
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1
CANDIDATE = "rule_macd_ema_cross"
REFERENCE = "rule_ma_cross"
FILL_RATE_REF = 0.994
COST_REF = 0.000808  # C per transakcja (model wykonania jak Y1/kontrola 4h)
P_STAR_Y1 = 0.5401  # p* zmierzone w Y1 na tej samej bazie i tym samym silniku
P_ASSUMED = 0.56  # „obietnica podręcznika” — konwencja A1/A2/Y1
Y1_ROWS_REF = 46368  # świece ocenione w Y1 (ta sama populacja — kontrola regresji)
NAMES = {CANDIDATE: "MX1: MACD, potem EMA 10/30", REFERENCE: "odniesienie: samo EMA 10/30"}
SEP = "=" * 104


def _collect(df: pd.DataFrame, rule: dict) -> dict:
    return collect_signals(
        df,
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


def ex_ante(fdf: pd.DataFrame, folds: list[dict], col: str) -> dict:
    """Częstość sygnałów, bariera na świecach sygnału, próg i mierzalność — BEZ wyników transakcji."""
    signals, funnel = build_rule_signals(fdf, folds, col)
    n = funnel["n_signals"]
    b = np.array([ATR_MULTIPLIER * s["atr_14"] / s["entry_price"] for s in signals])
    b_med = float(np.median(b)) if n else float("nan")
    be_formula = break_even_hit_rate(COST_REF, b_med) if n else float("nan")
    p_ref = max(be_formula, P_STAR_Y1)
    n_exp = expected_trades(n, 0.0, FILL_RATE_REF)
    rep = measurability_report(P_ASSUMED, p_ref, n_exp)
    return {
        "signals": signals,
        "funnel": funnel,
        "n": n,
        "long": sum(s["signal_direction"] > 0 for s in signals),
        "short": sum(s["signal_direction"] < 0 for s in signals),
        "b_med": b_med,
        "be_formula": be_formula,
        "p_ref": p_ref,
        "n_exp": n_exp,
        "half_width": wald_half_width(int(round(n_exp))) if n_exp >= 1 else float("nan"),
        "report": rep,
        "n_req_negative": required_trades(0.50, p_ref),
    }


def main(argv: list[str]) -> int:
    t0 = time.time()
    moc_only = "--moc" in argv
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    print(SEP)
    print(
        "MX1 — przecięcie EMA 10/30 potwierdzone wcześniejszym przecięciem MACD 12/26/9, BTC 1h, reguła bez modelu"
    )
    print(SEP)
    df = fetch_window(data_cfg, TIMEFRAME)
    gaps = int(
        (pd.to_datetime(df["timestamp"], utc=True).diff() != pd.Timedelta(hours=1)).sum() - 1
    )
    raw = pd.concat(
        [df, compute_mx_rules(df)], axis=1
    )  # reguły na CIĄGŁYM szeregu (przed pipeline'em)
    hist = compute_macd_hist(df)
    print(
        f"dane      : {len(df)} świec {TIMEFRAME} od {df['timestamp'].min()} do {df['timestamp'].max()}; "
        f"przerwy w szeregu (≠ 1 h): {gaps}\n"
        f"przyrząd  : bariera {ATR_MULTIPLIER}·ATR, V = {VERTICAL_BARRIER_CANDLES} świece, walk-forward "
        f"{TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS} dni, wejście {ENTRY.kind} k = {VALIDITY}, populacja = okna OOS (A2)\n"
    )
    collected = _collect(raw, rule)
    folds = collected["folds_summary"]
    fdf = collected["df"]
    active = [f for f in folds if not f["skipped"]]
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    print(
        f"0. POPULACJA: foldy {len(active)}/{len(folds)}, świece ocenione {n_rows} "
        f"(Y1: {Y1_ROWS_REF} → {'ZGODNA' if n_rows == Y1_ROWS_REF else 'ROZJAZD — sprawdź pipeline'})"
    )
    first_oos = min(f["test_start"] for f in active)
    in_oos = pd.to_datetime(df["timestamp"], utc=True) >= first_oos
    macd_cross = int(
        (
            (np.sign(hist) != np.sign(hist.shift(1)))
            & hist.notna()
            & hist.shift(1).notna()
            & in_oos
        ).sum()
    )
    print(f"   przecięcia MACD/sygnał w oknie OOS: {macd_cross} (kontekst)")

    print(
        "\n1. RACHUNEK MIERZALNOŚCI EX ANTE (zasada 18) — z częstości sygnałów i bariery, bez wyników transakcji"
    )
    ante = {col: ex_ante(fdf, folds, col) for col in (CANDIDATE, REFERENCE)}
    for col, a in ante.items():
        f, rep = a["funnel"], a["report"]
        print(
            f"  {NAMES[col]:>28}: świece OOS {f['n_rows_window']}, bez sygnału {f['n_no_signal']}, "
            f"bez etykiety/ATR {f['n_label_nan']}, bramka kosztowa {f['n_cost_gated']} → sygnały {a['n']} "
            f"(long {a['long']}, short {a['short']})\n"
            f"  {'':>28}  bariera (mediana) {100 * a['b_med']:.3f}% → próg ±B ze wzoru {100 * a['be_formula']:.2f}%; "
            f"próg odniesienia max(wzór, p* Y1 {100 * P_STAR_Y1:.2f}%) = {100 * a['p_ref']:.2f}%\n"
            f"  {'':>28}  expected_trades({a['n']}; 0; {FILL_RATE_REF}) = {a['n_exp']:,.0f}; half-width "
            f"{100 * a['half_width']:.2f} pp; trzeba zmierzyć ≥ {100 * rep['p_detectable']:.2f}% → dla zakładanej "
            f"{100 * P_ASSUMED:.0f}%: {rep['verdict']}; negatyw wymaga n ≥ {a['n_req_negative']:,.0f}"
        )
    kept = ante[CANDIDATE]["n"] / max(ante[REFERENCE]["n"], 1)
    print(f"  MACD przepuszcza {100 * kept:.1f}% przecięć EMA 10/30 w populacji OOS")
    measurable = ante[CANDIDATE]["report"]["verdict"] == "MIERZALNA"
    print(f"\n  (bez symulacji transakcji; czas {time.time() - t0:.0f} s)")
    if not moc_only:
        print(
            "  NIEMIERZALNA — zasada 18: runda nie startuje."
            if not measurable
            else "  MIERZALNA — pełny pomiar wymaga nowej pre-rejestracji i osobnego skryptu."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
