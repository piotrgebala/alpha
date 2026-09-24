"""
run_train_window_wf1.py — runda WF1: długość okna UCZENIA modelu kontrolnego 4h (decyzja użytkownika
2026-09-24: „może okno jest za wąskie”). Model kontrolny projektu bez zmian (4 cechy REVERSION, bez
bramki reżimu, wagi klas `balanced`, V = 3 świece, bariera 1,5·ATR, wejście limit po close k = 1,
pojedyncze wyjście, koszty z config, walk-forward test/krok 28/28 dni); JEDNA zmienna: train_days.
Ramiona: 60 (kontrola, 0 wariantów), 365, 730 dni (m = 2, Bonferroni z = 2,241).
Wszystkie ramiona oceniane na TYCH SAMYCH świecach: sygnały z `timestamp` ≥ COMMON_START (pierwszy
dzień testu ramienia 730 przy danych od 2021-01-01, zasada 20), filtr czasu zapisany z góry.
Konfiguracja ZAMROŻONA w `runs/2026-09-24_wf1-okno-uczenia/README.md`.

    PYTHONUTF8=1 py -m backtest.run_train_window_wf1 --moc
    PYTHONUTF8=1 py -m backtest.run_train_window_wf1
"""

from __future__ import annotations

import sys
import time

import pandas as pd

from backtest.checkpoint_lib import PRIMARY_SEED, summarize_result, summarize_trade_returns
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.metrics import expected_trades, measurability_report, required_trades, wald_half_width
from backtest.run_horizon_y import (
    ABSTENTION_REF,
    COST_REF,
    ENTRY,
    FEATURES,
    FILL_RATE_REF,
    P_ASSUMED,
    VALIDITY,
    VERTICAL_BARRIER_CANDLES,
    _atr_fraction,
    _load,
)
from backtest.metrics import break_even_hit_rate

TF = "4h"
CANDLES_PER_DAY, CANDLE_MINUTES = 6, 240
TEST_DAYS = STEP_DAYS = 28
ARMS = (60, 365, 730)  # 60 = kontrola
Z_M2 = 2.241
SEP = "=" * 104


def common_start(df: pd.DataFrame) -> pd.Timestamp:
    """Pierwszy dzień testu najdłuższego ramienia: start danych + max(train_days)."""
    return pd.Timestamp(df["timestamp"].min()) + pd.Timedelta(days=max(ARMS))


def run_arm(df: pd.DataFrame, rule: dict, train_days: int, start: pd.Timestamp) -> dict:
    collected = collect_signals(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        train_days=train_days,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    active = [f for f in collected["folds_summary"] if not f["skipped"]]
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    out = {"folds": len(active), "abst": n_abst / n_rows if n_rows else float("nan")}
    for lab, sig in (
        (
            "wspólne",
            [s for s in collected["candidate_signals"] if pd.Timestamp(s["timestamp"]) >= start],
        ),
        ("pełne", collected["candidate_signals"]),
    ):
        res = simulate_equity(
            collected["df"],
            sig,
            collected["folds_summary"],
            candle_minutes=CANDLE_MINUTES,
            vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
            fill_model=FILL_MODEL_PATH,
            entry_rule=ENTRY,
            entry_validity_candles=VALIDITY,
        )
        out[lab] = summarize_trade_returns(summarize_result(res, PRIMARY_SEED))
    return out


def verdict(w: dict, z: float) -> str:
    if w["t_neff"] > z and w["ci_low"] > w["p_star"]:
        return "POZYTYWNY (najpierw szukaj przecieku)"
    if w["t_neff"] < -z and w["n"] >= required_trades(0.50, w["be_symmetric"]):
        return "NEGATYWNY"
    return "NIEROZSTRZYGNIĘTY"


def main(argv: list[str]) -> None:
    t0 = time.time()
    data_cfg, rule, df = _load(TF)
    start = common_start(df)
    n_common = int((df["timestamp"] >= start).sum())
    barrier = 1.5 * float(_atr_fraction(df).dropna().median())
    be = break_even_hit_rate(COST_REF, barrier)
    n_exp = expected_trades(n_common, ABSTENTION_REF, FILL_RATE_REF)
    rep = measurability_report(P_ASSUMED, be, n_exp)
    print(SEP)
    print(
        ("WF1 — MIERZALNOŚĆ" if "--moc" in argv else "WF1 — DŁUGOŚĆ OKNA UCZENIA MODELU 4h")
        + "; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"  dane 4h: {len(df)} świec od {df['timestamp'].min()} (zasada 20); ramiona train_days {ARMS} (60 = kontrola), test/krok {TEST_DAYS}/{STEP_DAYS}\n"
        f"  wspólny okres oceny od {start} ({n_common} świec); próg ±B ≈ {100 * be:.2f}%; oczekiwane n na ramię {n_exp:,.0f}; "
        f"half-width {100 * wald_half_width(n_exp):.2f} pp (z 1,96) / {100 * wald_half_width(n_exp) * Z_M2 / 1.96:.2f} pp (z 2,241)\n"
        f"  measurability_report(p = {P_ASSUMED}, BE = {be:.4f}, n = {n_exp:,.0f}) → {rep.get('verdict', rep)}"
    )
    if "--moc" in argv:
        return
    print(
        "\n  ramię | foldy | abstynencja | okres   |     n | p [CI 95 %]              | p*     | r̄ netto/trade [CI z]        | t_neff | werdykt"
    )
    for td in ARMS:
        r = run_arm(df, rule, td, start)
        z = 1.96 if td == 60 else Z_M2
        for lab in ("wspólne", "pełne"):
            w = r[lab]
            half = z * w["se"]
            v = verdict(w, z) if lab == "wspólne" else "opisowo"
            print(
                f"  {td:5d} | {r['folds']:5d} | {100 * r['abst']:10.1f}% | {lab:7s} | {w['n']:5d} | {100 * w['p']:.2f}% [{100 * w['ci_low']:.2f}; {100 * w['ci_high']:.2f}] | "
                f"{100 * w['p_star']:.2f}% | {100 * w['r_mean']:+.4f}% [{100 * (w['r_mean'] - half):+.4f}; {100 * (w['r_mean'] + half):+.4f}] | {w['t_neff']:+.2f} | {v}"
            )
        print(f"         czas {time.time() - t0:.0f}s")
    print(SEP)


if __name__ == "__main__":
    main(sys.argv[1:])
