"""Walidacja Y1/Y2 drugą drogą (bramka 16a). Uruchomienie:
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-23_y1-horyzont-1h/walidacja.py   (wynik dla obu baz)

Dla każdej bazy: trafność i r̄ netto wprost z journalu (numpy), p* z W̄/L̄/C, bariera ex post
(średnia |zwrot brutto| przy wyjściu tp/sl) vs ex ante z ATR, jakość danych (luki, duplikaty),
liczba foldów i świec OOS, abstynencja ex post.
"""

import numpy as np
import pandas as pd
import yaml

from backtest.costs import EXIT_REASON_SL, EXIT_REASON_TP
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.checkpoint_lib import (
    PRIMARY_SEED,
    fetch_window,
    load_config,
    summarize_result,
    summarize_trade_returns,
)
from backtest.run_horizon_y import (
    ENTRY,
    FEATURES,
    HORIZONS,
    VALIDITY,
    VERTICAL_BARRIER_CANDLES,
    _ex_ante,
)

data_cfg = load_config()["data"]
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]

for tf, cfg in HORIZONS.items():
    print(f"===== {cfg['series']} — {tf} =====")
    df = fetch_window(data_cfg, tf)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    step = pd.Timedelta(minutes=cfg["candle_minutes"])
    gaps = int(((ts.diff() > step)).sum())
    print(
        f"  dane: {len(df)} świec, duplikaty {int(ts.duplicated().sum())}, luki (> {step}) {gaps}, "
        f"OHLC spójne: {bool(((df['high'] >= df[['open', 'close']].max(axis=1)) & (df['low'] <= df[['open', 'close']].min(axis=1))).all())}"
    )
    ea = _ex_ante(tf, df, cfg)
    c = collect_signals(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=cfg["candles_per_day"],
        train_days=cfg["train_days"],
        test_days=cfg["test_days"],
        step_days=cfg["step_days"],
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    res = simulate_equity(
        c["df"],
        c["candidate_signals"],
        c["folds_summary"],
        candle_minutes=cfg["candle_minutes"],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        fill_model=FILL_MODEL_PATH,
        entry_rule=ENTRY,
        entry_validity_candles=VALIDITY,
    )
    w = summarize_trade_returns(summarize_result(res, PRIMARY_SEED))
    real = w["real"]
    p = float((real["gross_ret"] > 0).mean())
    r = real["net_ret"].to_numpy(dtype=float)
    wins = real.loc[real["gross_ret"] > 0, "gross_ret"].mean()
    losses = -real.loc[real["gross_ret"] <= 0, "gross_ret"].mean()
    cost = float((real["gross_ret"] - real["net_ret"]).mean())
    active = [f for f in c["folds_summary"] if not f["skipped"]]
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    tp = real.loc[real["exit_reason"] == EXIT_REASON_TP, "gross_ret"].mean()
    sl = -real.loc[real["exit_reason"] == EXIT_REASON_SL, "gross_ret"].mean()
    print(
        f"  journal: n {len(real)}; p = {100 * p:.2f}% (skrypt {100 * w['p']:.2f}%); r̄ netto {100 * r.mean():+.4f}% (skrypt {100 * w['r_mean']:+.4f}%); "
        f"mediana {100 * np.median(r):+.4f}%; p* = ({100 * losses:.3f} + {100 * cost:.4f})/({100 * wins:.3f} + {100 * losses:.3f}) = {100 * (losses + cost) / (wins + losses):.2f}% (skrypt {100 * w['p_star']:.2f}%)"
    )
    print(
        f"  bariera ex post: średni zysk przy tp {100 * tp:.3f}%, strata przy sl {100 * sl:.3f}% vs ex ante 1,5·ATR = {100 * ea['barrier']:.3f}%; "
        f"foldy aktywne {len(active)}/{len(c['folds_summary'])}; świece OOS {n_rows} (ex ante ≈ {ea['n_oos']}); abstynencja {100 * n_abst / n_rows:.2f}% (założona 40,38%); "
        f"koszt C ex post {100 * cost:.4f}% (założony 0,0808%)"
    )
    years = pd.to_datetime(real["timestamp"], utc=True).dt.year
    print(
        "  per rok (n, p, Σ netto): "
        + "; ".join(
            f"{y}: {len(g)}, {100 * (g['gross_ret'] > 0).mean():.1f}%, {100 * g['net_ret'].sum():+.1f}%"
            for y, g in real.groupby(years)
        )
    )
