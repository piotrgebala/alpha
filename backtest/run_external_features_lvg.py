"""
run_external_features_lvg.py — serie L1 / V1 / G1: JEDNA cecha z dziennego źródła zewnętrznego
(P3) jako 5. cecha modelu 4h BTC, parowo z kontrolą (4 cechy REVERSION, ten sam seed, te same
świece). Pre-rejestracje (PRZED tym skryptem, jeden commit dla trzech serii):
runs/2026-09-23_l1-onchain-podaz/, runs/2026-09-23_v1-premia-zmiennosci/, runs/2026-09-23_g1-strach-chciwosc/.

Uruchomienie:  py -m backtest.run_external_features_lvg L1|V1|G1   (Windows: PYTHONUTF8=1)

Neutralny reporter (wzorzec O1): odczyt kryterium dwóch warunków (jedno ramię, m = 1 per seria),
porównanie parowane, opis, mierzalność; werdykt podpisuje Claude w README serii.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd
import yaml

from agents.external_features import (
    FEATURE_SOURCES,
    SOURCES,
    compute_external_feature,
)
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import (
    PRIMARY_SEED,
    fetch_window,
    load_config,
    summarize_result,
    summarize_trade_returns,
)
from backtest.costs import EXIT_REASON_SL, EXIT_REASON_TIMEOUT, EXIT_REASON_TP
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule
from backtest.metrics import (
    Z_TWO_SIDED_95,
    expected_trades,
    measurability_report,
    required_trades,
    wald_half_width,
)

SERIES = {
    "L1": ("ex_supply_change_7d", "ON-CHAIN: zmiana podaży BTC na giełdach 7 dni (CoinMetrics)"),
    "V1": ("vrp_30d", "PREMIA ZA RYZYKO ZMIENNOŚCI: DVOL/100 − zrealizowana 30 dni"),
    "G1": ("fng_level", "FEAR & GREED: poziom indeksu / 100"),
}
# --- konfiguracja ZAMROŻONA (ta sama co kontrola N1/A1/A2/O1) ---------------------------------
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
CONTROL_FEATURES = list(REVERSION_FEATURES)
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1
ABSTENTION_REF = 0.4038
FILL_RATE_REF = 0.994
BE_REF = 0.5307
P_ASSUMED = 0.56
N1_CONTROL_REF = {"n": 6789, "p": 0.4958, "r_mean": -0.001069}
FUNNEL = (
    ("świece ocenione", "n_rows_evaluated"),
    ("bez kierunku (abstynencja)", "n_signals_no_direction"),
    ("bramka pewności", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnały kandydujące", "n_signals"),
)
SEP = "=" * 104


def _collect(df: pd.DataFrame, features: list[str], rule: dict) -> dict:
    return collect_signals(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, features)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )


def _simulate(df: pd.DataFrame, signals: list[dict], folds: list[dict]) -> dict:
    result = simulate_equity(
        df,
        signals,
        folds,
        candle_minutes=CANDLE_MINUTES,
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        fill_model=FILL_MODEL_PATH,
        entry_rule=ENTRY,
        entry_validity_candles=VALIDITY,
    )
    return summarize_trade_returns(summarize_result(result, PRIMARY_SEED))


def _n_required(w: dict) -> float:
    return required_trades(0.50, w["be_symmetric"])


def _verdict(w: dict) -> str:
    """Kryterium dwóch warunków (m = 1) — odczyt reguły, nie decyzja."""
    if w["t_neff"] > Z_TWO_SIDED_95 and w["ci_low"] > w["p_star"]:
        return "POZYTYWNY — t_neff > 1,96 i ci_low(p) > p*. NAJPIERW SZUKAJ PRZECIEKU"
    if w["t_neff"] < -Z_TWO_SIDED_95 and w["n"] >= _n_required(w):
        return f"NEGATYWNY — t_neff < −1,96 przy n >= required_trades(0,50; BE) = {_n_required(w):,.0f}"
    return "NIEROZSTRZYGNIĘTY — |t_neff| poniżej progu, ci_low(p) <= p* albo n poniżej wymaganego"


def _print_funnel(name: str, collected: dict) -> tuple[int, int]:
    active = [f for f in collected["folds_summary"] if not f["skipped"]]
    print(f"  [{name}] foldy: {len(active)} aktywne / {len(collected['folds_summary'])} łącznie")
    for label, key in FUNNEL:
        print(f"  {label:>28}: {sum(f[key] for f in active):8d}")
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    print(f"  {'abstynencja':>28}: {100 * n_abst / n_rows:7.2f}%")
    return n_rows, n_abst


def _print_row(name: str, w: dict) -> None:
    half = Z_TWO_SIDED_95 * w["se"]
    print(
        f"  {name:>9} | {w['n']:5d} | {100 * w['r_mean']:+8.4f}% | "
        f"[{100 * (w['r_mean'] - half):+8.4f}; {100 * (w['r_mean'] + half):+8.4f}] | "
        f"{100 * w['r_median']:+7.4f}% | {w['t']:+6.2f} | {w['n_eff']:6.0f} | {w['t_neff']:+6.2f} | "
        f"{100 * w['p']:6.2f}% | [{100 * w['ci_low']:6.2f}; {100 * w['ci_high']:6.2f}] | "
        f"{100 * w['p_star']:5.2f}% | {100 * w['be_symmetric']:5.2f}%"
    )


def _wald(hits: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = hits / n
    half = Z_TWO_SIDED_95 * np.sqrt(p * (1.0 - p) / n)
    return p, p - half, p + half


def _print_group_table(title: str, groups: list[tuple[str, pd.DataFrame]]) -> None:
    print(f"  {title}")
    print(
        f"  {'grupa':>22} | {'n':>5} | {'udział':>7} | {'p':>7} | {'CI 95% (p)':>17} | "
        f"{'r̄ netto':>9} | {'r̄ brutto':>9} | {'mediana':>8}"
    )
    print("  " + "-" * 104)
    total = sum(len(g) for _, g in groups) or 1
    for name, g in groups:
        n = len(g)
        if n == 0:
            print(
                f"  {name:>22} | {0:5d} |       — |       — |                 — |         — |         — |        —"
            )
            continue
        p, lo, hi = _wald(int((g["gross_ret"] > 0).sum()), n)
        print(
            f"  {name:>22} | {n:5d} | {100 * n / total:6.1f}% | {100 * p:6.2f}% | [{100 * lo:6.2f}; {100 * hi:6.2f}] | "
            f"{100 * g['net_ret'].mean():+8.4f}% | {100 * g['gross_ret'].mean():+8.4f}% | {100 * g['net_ret'].median():+7.4f}%"
        )


def _describe_arm(name: str, w: dict) -> None:
    real = w["real"].copy()
    _print_group_table(
        f"{name} — powód wyjścia",
        [
            ("cel (tp)", real.loc[real["exit_reason"] == EXIT_REASON_TP]),
            ("stop (sl)", real.loc[real["exit_reason"] == EXIT_REASON_SL]),
            ("timeout", real.loc[real["exit_reason"] == EXIT_REASON_TIMEOUT]),
        ],
    )
    _print_group_table(
        f"{name} — kierunek",
        [
            ("long", real.loc[real["signal_direction"] > 0]),
            ("short", real.loc[real["signal_direction"] < 0]),
        ],
    )
    print(
        f"  {name}: W̄ = {100 * w['w_mean']:.4f}%, L̄ = {100 * w['l_mean']:.4f}%, C = {100 * w['cost']:.4f}%, "
        f"std zwrotu {100 * w['r_std']:.3f}%, p5/p95 [{100 * w['r_p5']:+.3f}%; {100 * w['r_p95']:+.3f}%], "
        f"niewypełnione {w['n_unfilled']}, stłumione {w['n_suppressed']}"
    )


def main(series: str) -> None:
    if series not in SERIES:
        raise SystemExit(f"podaj serię: {sorted(SERIES)}")
    feature, title = SERIES[series]
    source = FEATURE_SOURCES[feature][0]
    t0 = time.time()
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    print(SEP)
    print(f"{series} — {title} jako 5. cecha modelu 4h BTC vs kontrola; konfiguracja ZAMROŻONA")
    print(SEP)
    df = fetch_window(data_cfg, TIMEFRAME)
    raw = compute_external_feature(df, feature)
    feat = raw[feature]
    arm_features = [*CONTROL_FEATURES, feature]
    first_valid = raw.loc[feat.notna(), "timestamp"].min()
    print(
        f"dane      : {len(df)} świec {TIMEFRAME} od {df['timestamp'].min()} do {df['timestamp'].max()}"
        f" (zasada 20: min_start = {data_cfg['min_start']}); źródło `{source}`, dostępność wartości dnia d od "
        f"d + {SOURCES[source]['available_after']}\n"
        f"cecha     : {feature}; NaN {int(feat.isna().sum())} z {len(feat)} świec, pierwsza wartość {first_valid}\n"
        f"            rozkład: p01 {feat.quantile(0.01):+.4f}, p05 {feat.quantile(0.05):+.4f}, p50 {feat.median():+.4f}, "
        f"p95 {feat.quantile(0.95):+.4f}, p99 {feat.quantile(0.99):+.4f}; masa punktowa "
        f"{100 * feat.round(6).value_counts(normalize=True).iloc[0]:.2f}%; acf1 {feat.autocorr(1):+.3f}\n"
        f"pipeline  : BEZ bramki reżimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced`, walk-forward "
        f"{TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}, wejście {ENTRY.kind} k={VALIDITY}, pojedyncze wyjście\n"
        f"kontrola  : cechy {CONTROL_FEATURES}\n"
        f"{series:<9} : cechy {arm_features}\n"
        f"kryterium : jedno ramię (m = 1): POZYTYWNY t_neff > 1,96 i ci_low(p) > p*; NEGATYWNY t_neff < −1,96 przy n >= required\n"
    )

    print(f"0. LEJEK — kontrola i {series} (dwa treningi)")
    control_c = _collect(raw, CONTROL_FEATURES, rule)
    print(f"  trening kontroli zakończony po {time.time() - t0:.0f} s")
    n_rows_ctrl, _ = _print_funnel("kontrola", control_c)
    arm_c = _collect(raw, arm_features, rule)
    print(f"  trening {series} zakończony po {time.time() - t0:.0f} s")
    n_rows_arm, n_abst_arm = _print_funnel(series, arm_c)
    fdf = control_c["df"]
    corr = {c: float(fdf[feature].corr(fdf[c])) for c in CONTROL_FEATURES}
    print("  korelacja cechy z kontrolą: " + ", ".join(f"{c} {v:+.3f}" for c, v in corr.items()))

    control = _simulate(fdf, control_c["candidate_signals"], control_c["folds_summary"])
    arm = _simulate(arm_c["df"], arm_c["candidate_signals"], arm_c["folds_summary"])

    print(
        "\n1. KRYTERIUM — zwrot netto per trade (t_neff) i trafność wobec p* (jedno ramię, z = 1,96)"
    )
    print(
        f"  {'ramię':>9} | {'n':>5} | {'r̄ netto':>9} | {'CI 95%':>21} | {'mediana':>8} | "
        f"{'t':>6} | {'N_eff':>6} | {'t_neff':>6} | {'p':>7} | {'CI 95%(p)':>17} | {'p*':>6} | {'BE ±B':>6}"
    )
    print("  " + "-" * 128)
    _print_row("kontrola", control)
    _print_row(series, arm)
    print(f"  >>> ODCZYT KRYTERIUM {series}: {_verdict(arm)}")
    print(f"  (kontrola: {_verdict(control)} — odniesienie, 0 wariantów)")
    ok = (
        control["n"] == N1_CONTROL_REF["n"]
        and abs(control["p"] - N1_CONTROL_REF["p"]) < 5e-4
        and abs(control["r_mean"] - N1_CONTROL_REF["r_mean"]) < 2e-5
    )
    print(
        f"  regresja kontroli wobec N1/A1/A2/O1 (n {N1_CONTROL_REF['n']}, p {100 * N1_CONTROL_REF['p']:.2f}%, "
        f"r̄ {100 * N1_CONTROL_REF['r_mean']:+.4f}%): {'ZGODNA' if ok else 'ROZJAZD — sprawdź pipeline'}"
    )

    print(
        f"\n2. PORÓWNANIE PAROWANE {series} − kontrola (te same świece i wypełnienia) — obserwacja, nie kryterium"
    )
    a = control["real"].set_index("timestamp")
    b = arm["real"].set_index("timestamp")
    both = a[["net_ret", "gross_ret", "signal_direction"]].join(
        b[["net_ret", "gross_ret", "signal_direction"]], how="inner", lsuffix="_c", rsuffix="_a"
    )
    d = both["net_ret_a"] - both["net_ret_c"]
    se_d = float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan")
    same_dir = (
        float((both["signal_direction_c"] == both["signal_direction_a"]).mean())
        if len(both)
        else float("nan")
    )
    print(
        f"  wspólnych transakcji {len(both)} (kontrola {len(a)}, {series} {len(b)}); ten sam kierunek w {100 * same_dir:.1f}%; "
        f"średnia różnica netto {100 * d.mean():+.4f}% [{100 * (d.mean() - Z_TWO_SIDED_95 * se_d):+.4f}; "
        f"{100 * (d.mean() + Z_TWO_SIDED_95 * se_d):+.4f}], mediana {100 * d.median():+.4f}%, różnic ≠ 0: {int((d != 0).sum())}\n"
        f"  tylko w kontroli: {len(a.index.difference(b.index))}, tylko w {series}: {len(b.index.difference(a.index))}; "
        f"świece ocenione {series} {n_rows_arm} vs kontrola {n_rows_ctrl}, abstynencja {series} {100 * n_abst_arm / n_rows_arm:.2f}%"
    )

    print("\n3. OPIS — powód wyjścia, kierunek, geometria wypłaty")
    _describe_arm("kontrola", control)
    _describe_arm(series, arm)

    print("\n4. MIERZALNOŚĆ — ex ante (pre-rejestracja) vs ex post")
    n_ante = expected_trades(n_rows_ctrl, ABSTENTION_REF, FILL_RATE_REF)
    n_post = expected_trades(n_rows_arm, n_abst_arm / n_rows_arm, FILL_RATE_REF)
    rep = measurability_report(P_ASSUMED, BE_REF, n_ante)
    print(
        f"  {series}: expected_trades ex ante = {n_ante:,.0f}; ex post = {n_post:,.0f}; journal = {arm['n']:,}; "
        f"half-width ex ante {100 * wald_half_width(n_ante):.2f} pp, ex post {100 * wald_half_width(arm['n']):.2f} pp; "
        f"measurability_report(p={P_ASSUMED}, BE={BE_REF}, n={n_ante:,.0f}) → {rep.get('verdict', rep)}"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
