"""
run_ta_rules_a2.py — runda A2: pozostałe rodziny analizy technicznej ze skilla `ta-toolkit` jako
REGUŁY szukania pozycji (A2.1 struktura trendu, A2.2 zniesienie Fibonacciego, A2.3 wsparcie/opór,
A2.4 grupa zdarzeń) i jako CECHY modelu (A2.5). Pre-rejestracja (PRZED tym skryptem):
runs/2026-09-23_a2-rodziny-at/README.md.

Uruchomienie:  py -m backtest.run_ta_rules_a2   (Windows: PYTHONUTF8=1)

Skrypt jest NEUTRALNYM REPORTEREM: liczy i drukuje odczyt kryterium z pre-rejestracji (z korektą
Bonferroniego dla pozytywu, m = 5); werdykt podpisuje Claude w README rundy. Pięć reguł
zdarzeniowych osobno NIEMIERZALNYCH nie jest symulowanych osobno (zasada 18) — tylko zliczane
i widoczne opisowo wewnątrz grupy. Buduje na backtest/checkpoint_lib.py i backtest/engine.py.
"""

from __future__ import annotations

import time
from statistics import NormalDist

import numpy as np
import pandas as pd
import yaml

from agents.ml_optimizer import REVERSION_FEATURES
from agents.ta_rules import (
    EVENT_RULES,
    TA_FEATURE_FUNCTIONS,
    compute_ta_features,
    compute_ta_rules,
    event_group_signal,
)
from backtest.checkpoint_lib import (
    PRIMARY_SEED,
    build_rule_signals,
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

# --- konfiguracja ZAMROŻONA w pre-rejestracji (ta sama co kontrola N1/A1) --------------------
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
CONTROL_FEATURES = list(REVERSION_FEATURES)
TA_FEATURES = list(TA_FEATURE_FUNCTIONS)
A25_FEATURES = [*REVERSION_FEATURES, *TA_FEATURES]
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1

RULE_ARMS = (
    ("A2.1", "struktura trendu", "rule_trend_structure"),
    ("A2.2", "Fibonacci", "rule_fib_retrace"),
    ("A2.3", "wsparcie/opór", "rule_sr_bounce"),
    ("A2.4", "grupa zdarzeń", "rule_event_group"),
)
UNMEASURABLE_ALONE = tuple(sorted(EVENT_RULES))  # zasada 18: osobno nie startują
M_ARMS = 5  # A2.1–A2.5 — korekta Bonferroniego dla pozytywu
Z_BONF = NormalDist().inv_cdf(1 - 0.025 / M_ARMS)

# --- liczby z pre-rejestracji (ex ante) ------------------------------------------------------
N_SIGNALS_EX_ANTE = {
    "rule_trend_structure": 6847,
    "rule_fib_retrace": 2281,
    "rule_sr_bounce": 9664,
    "rule_event_group": 2187,
}
ABSTENTION_REF = 0.4038
FILL_RATE_REF = 0.994
BE_REF = 0.5307
P_ASSUMED = 0.56  # „obietnica podręcznika" — konwencja z A1
N1_CONTROL_REF = {"n": 6789, "p": 0.4958, "r_mean": -0.001069}

FUNNEL = (
    ("świece ocenione", "n_rows_evaluated"),
    ("bez kierunku (abstynencja)", "n_signals_no_direction"),
    ("bramka pewności", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnały kandydujące", "n_signals"),
)
SEP = "=" * 104
RULE_PL = {
    "rule_breakout": "wybicie z zakresu",
    "rule_double_top_bottom": "podwójny szczyt/dno",
    "rule_head_shoulders": "głowa z ramionami",
    "rule_ma_cross": "przecięcie EMA 10/30",
    "rule_trendline_break": "przełamanie linii trendu",
}


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


def _ci_low_bonf(w: dict) -> float:
    p, n = w["p"], w["n"]
    return p - Z_BONF * np.sqrt(p * (1.0 - p) / n) if n else float("nan")


def _verdict(w: dict) -> str:
    """Kryterium z pre-rejestracji A2 — odczyt reguły, nie decyzja."""
    if w["t_neff"] > Z_BONF and _ci_low_bonf(w) > w["p_star"]:
        return f"POZYTYWNY — t_neff > {Z_BONF:.3f} i ci_low(p; z_5) > p*. NAJPIERW SZUKAJ PRZECIEKU"
    if w["t_neff"] < -Z_TWO_SIDED_95 and w["n"] >= _n_required(w):
        return f"NEGATYWNY — t_neff < −1,96 przy n >= required_trades(0,50; BE) = {_n_required(w):,.0f}"
    return "NIEROZSTRZYGNIĘTY — |t_neff| poniżej progu, ci_low(p) <= p* albo n poniżej wymaganego"


def _wald(hits: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = hits / n
    half = Z_TWO_SIDED_95 * np.sqrt(p * (1.0 - p) / n)
    return p, p - half, p + half


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
        f"{100 * _ci_low_bonf(w):6.2f}% | {100 * w['p_star']:5.2f}% | {100 * w['be_symmetric']:5.2f}%"
    )


def _print_group_table(title: str, groups: list[tuple[str, pd.DataFrame]]) -> None:
    print(f"  {title}")
    print(
        f"  {'grupa':>26} | {'n':>5} | {'udział':>7} | {'p':>7} | {'CI 95% (p)':>17} | "
        f"{'r̄ netto':>9} | {'r̄ brutto':>9} | {'mediana':>8}"
    )
    print("  " + "-" * 108)
    total = sum(len(g) for _, g in groups) or 1
    for name, g in groups:
        n = len(g)
        if n == 0:
            print(
                f"  {name:>26} | {0:5d} |       — |       — |                 — |         — |         — |        —"
            )
            continue
        p, lo, hi = _wald(int((g["gross_ret"] > 0).sum()), n)
        print(
            f"  {name:>26} | {n:5d} | {100 * n / total:6.1f}% | {100 * p:6.2f}% | [{100 * lo:6.2f}; {100 * hi:6.2f}] | "
            f"{100 * g['net_ret'].mean():+8.4f}% | {100 * g['gross_ret'].mean():+8.4f}% | {100 * g['net_ret'].median():+7.4f}%"
        )


def _describe_arm(name: str, w: dict, fdf: pd.DataFrame, member_cols: list[str]) -> None:
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
    if member_cols:
        joined = real.merge(
            fdf[["timestamp", *member_cols]], on="timestamp", how="left", validate="one_to_one"
        )
        _print_group_table(
            f"{name} — reguła obecna w świecy sygnału (OPISOWO, bez werdyktów; transakcja może mieć > 1)",
            [(RULE_PL.get(c, c), joined.loc[joined[c] != 0]) for c in member_cols],
        )
    print(
        f"  {name}: W̄ = {100 * w['w_mean']:.4f}%, L̄ = {100 * w['l_mean']:.4f}%, C = {100 * w['cost']:.4f}%, "
        f"std zwrotu {100 * w['r_std']:.3f}%, p5/p95 [{100 * w['r_p5']:+.3f}%; {100 * w['r_p95']:+.3f}%], "
        f"niewypełnione {w['n_unfilled']}, stłumione {w['n_suppressed']}"
    )


def main() -> None:
    t0 = time.time()
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]

    print(SEP)
    print(
        "A2 — RODZINY ANALIZY TECHNICZNEJ jako reguły (A2.1–A2.4) i jako cechy modelu (A2.5); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    df = fetch_window(data_cfg, TIMEFRAME)
    raw_ta = compute_ta_features(df)  # cechy AT liczone na surowym df PRZED pipeline'em (trailing)
    print(
        f"dane      : {len(df)} świec {TIMEFRAME} od {df['timestamp'].min()} do {df['timestamp'].max()}"
        f" (zasada 20: min_start = {data_cfg['min_start']})\n"
        f"pipeline  : BEZ bramki reżimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced`, walk-forward "
        f"{TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}, wejście {ENTRY.kind} k={VALIDITY}, "
        f"pojedyncze wyjście\n"
        f"kontrola  : cechy {CONTROL_FEATURES}\n"
        f"A2.1–A2.4 : reguły bez modelu (confidence 1,0): {[c for _, _, c in RULE_ARMS]}\n"
        f"A2.5      : cechy {A25_FEATURES}\n"
        f"Bonferroni: m = {M_ARMS} ramion → z_5 = {Z_BONF:.3f} dla POZYTYWU; negatyw przy 1,96 + guard n\n"
    )

    print("0. LEJEK — kontrola i A2.5 (dwa treningi), reguły")
    control_c = _collect(raw_ta, CONTROL_FEATURES, rule)
    print(f"  trening kontroli zakończony po {time.time() - t0:.0f} s")
    n_rows_ctrl, _ = _print_funnel("kontrola", control_c)
    a25_c = _collect(raw_ta, A25_FEATURES, rule)
    print(f"  trening A2.5 zakończony po {time.time() - t0:.0f} s")
    n_rows_25, n_abst_25 = _print_funnel("A2.5", a25_c)

    fdf = control_c["df"]
    rules = compute_ta_rules(fdf)
    rules["rule_event_group"] = event_group_signal(rules)
    for col in rules.columns:
        fdf[col] = rules[col].to_numpy()
    folds = control_c["folds_summary"]
    first_oos = min(f["test_start"] for f in folds if not f["skipped"])
    in_oos = fdf["timestamp"] >= first_oos

    print("  [reguły NIEMIERZALNE osobno — zasada 18: zliczenie, bez symulacji]")
    for col in UNMEASURABLE_ALONE:
        s = fdf.loc[in_oos, col]
        print(
            f"  {RULE_PL.get(col, col):>28}: {int((s != 0).sum()):5d} sygnałów OOS "
            f"(long {int((s > 0).sum())}, short {int((s < 0).sum())}) → nie startuje"
        )

    arms: list[tuple[str, dict]] = []
    control = _simulate(fdf, control_c["candidate_signals"], folds)
    arms.append(("kontrola", control))
    rule_meta: dict[str, dict] = {}
    for arm_id, _label, col in RULE_ARMS:
        signals, funnel = build_rule_signals(fdf, folds, col)
        print(
            f"  [{arm_id} {col}] świece OOS {funnel['n_rows_window']}; bez sygnału {funnel['n_no_signal']}; "
            f"bez etykiety/ATR {funnel['n_label_nan']}; bramka kosztowa {funnel['n_cost_gated']}; "
            f"sygnały {funnel['n_signals']} (long {sum(s['signal_direction'] > 0 for s in signals)}, "
            f"short {sum(s['signal_direction'] < 0 for s in signals)})"
        )
        w = _simulate(fdf, signals, folds)
        rule_meta[arm_id] = {"col": col, "n_signals": funnel["n_signals"]}
        arms.append((arm_id, w))
    a25 = _simulate(a25_c["df"], a25_c["candidate_signals"], a25_c["folds_summary"])
    arms.append(("A2.5", a25))

    print(
        "\n1. KRYTERIUM — zwrot netto per trade (t_neff) i trafność wobec p*; pozytyw przy z_5 (Bonferroni)"
    )
    print(
        f"  {'ramię':>9} | {'n':>5} | {'r̄ netto':>9} | {'CI 95%':>21} | {'mediana':>8} | "
        f"{'t':>6} | {'N_eff':>6} | {'t_neff':>6} | {'p':>7} | {'CI 95%(p)':>17} | {'ci_low z5':>9} | {'p*':>6} | {'BE ±B':>6}"
    )
    print("  " + "-" * 140)
    for name, w in arms:
        _print_row(name, w)
    for name, w in arms[1:]:
        print(f"  >>> ODCZYT KRYTERIUM {name}: {_verdict(w)}")
    print(f"  (kontrola: {_verdict(control)} — odniesienie, 0 wariantów)")
    ok = (
        control["n"] == N1_CONTROL_REF["n"]
        and abs(control["p"] - N1_CONTROL_REF["p"]) < 5e-4
        and abs(control["r_mean"] - N1_CONTROL_REF["r_mean"]) < 2e-5
    )
    print(
        f"  regresja kontroli wobec N1/A1 (n {N1_CONTROL_REF['n']}, p {100 * N1_CONTROL_REF['p']:.2f}%, "
        f"r̄ {100 * N1_CONTROL_REF['r_mean']:+.4f}%): {'ZGODNA' if ok else 'ROZJAZD — sprawdź pipeline'}"
    )
    print(
        "  r̄ = średni zwrot netto w % nominału; t_neff z N_eff ≤ n; p* = (L̄ + C)/(W̄ + L̄); „ci_low z5” = dolny\n"
        f"  kraniec CI trafności przy z = {Z_BONF:.3f} (pięć ramion naraz); „BE ±B” = 0,5(1+C/B) — diagnostyka."
    )

    print(
        "\n2. PORÓWNANIE PAROWANE A2.5 − kontrola (te same świece i wypełnienia) — obserwacja, nie kryterium"
    )
    a = control["real"].set_index("timestamp")["net_ret"]
    b = a25["real"].set_index("timestamp")["net_ret"]
    both = pd.concat([a.rename("ctrl"), b.rename("a25")], axis=1, join="inner")
    diff = both["a25"] - both["ctrl"]
    se_d = diff.std(ddof=1) / np.sqrt(len(diff))
    same_dir = pd.concat(
        [
            control["real"].set_index("timestamp")["signal_direction"].rename("c"),
            a25["real"].set_index("timestamp")["signal_direction"].rename("b"),
        ],
        axis=1,
        join="inner",
    )
    print(
        f"  wspólnych transakcji {len(both)} (kontrola {len(a)}, A2.5 {len(b)}); "
        f"identycznych (różnica 0): {int((diff.abs() < 1e-12).sum())}; "
        f"ten sam kierunek: {int((same_dir['c'] == same_dir['b']).sum())}\n"
        f"  średnia różnica {100 * diff.mean():+.4f}% nominału, 95% CI "
        f"[{100 * (diff.mean() - Z_TWO_SIDED_95 * se_d):+.4f}; {100 * (diff.mean() + Z_TWO_SIDED_95 * se_d):+.4f}], "
        f"t = {diff.mean() / se_d:+.2f}; mediana różnicy {100 * diff.median():+.4f}%\n"
        f"  tylko w kontroli: {len(a.index.difference(b.index))}, tylko w A2.5: {len(b.index.difference(a.index))}; "
        f"świece ocenione A2.5 {n_rows_25} vs kontrola {n_rows_ctrl}, abstynencja A2.5 {100 * n_abst_25 / n_rows_25:.2f}%"
    )

    print(
        "\n3. OPISOWO — skąd biorą się pieniądze (bez werdyktów na podzbiorach — pre-rejestracja)"
    )
    for arm_id, _label, col in RULE_ARMS:
        w = dict(arms)[arm_id]
        members = sorted(EVENT_RULES) if col == "rule_event_group" else []
        _describe_arm(arm_id, w, fdf, members)
    _describe_arm("A2.5", a25, fdf, [])
    print(
        f"  kontrola: W̄ = {100 * control['w_mean']:.4f}%, L̄ = {100 * control['l_mean']:.4f}%, "
        f"C = {100 * control['cost']:.4f}%, niewypełnione {control['n_unfilled']}, stłumione {control['n_suppressed']}"
    )

    print("\n4. MIERZALNOŚĆ (zasada 18) — ex ante wg pre-rejestracji i ex post")
    for arm_id, _label, col in RULE_ARMS:
        w = dict(arms)[arm_id]
        n_ante = expected_trades(N_SIGNALS_EX_ANTE[col], 0.0, FILL_RATE_REF)
        n_post = expected_trades(
            rule_meta[arm_id]["n_signals"],
            0.0,
            1 - w["n_unfilled"] / max(rule_meta[arm_id]["n_signals"], 1),
        )
        rep = measurability_report(P_ASSUMED, BE_REF, n_ante)
        print(
            f"  {arm_id}: expected_trades ex ante = {n_ante:,.0f}; ex post = {n_post:,.0f}; journal = {w['n']:,}; "
            f"pasmo {100 * wald_half_width(int(n_ante)):.2f} / {100 * wald_half_width(w['n']):.2f} pp; "
            f"p_detectable ex ante = {100 * rep['p_detectable']:.2f}% → „p ≥ 56%” {rep['verdict']}; "
            f"required_trades = {_n_required(w):,.0f} → guard {'spełniony' if w['n'] >= _n_required(w) else 'NIESPEŁNIONY'}; "
            f"se = {100 * w['se']:.4f}% → |r̄| >= {100 * 2.8 * w['se']:.4f}%"
        )
    n_ante = expected_trades(n_rows_ctrl, ABSTENTION_REF, FILL_RATE_REF)
    n_post = expected_trades(
        n_rows_25,
        n_abst_25 / n_rows_25,
        1 - a25["n_unfilled"] / max(len(a25_c["candidate_signals"]), 1),
    )
    print(
        f"  A2.5: expected_trades ex ante = {n_ante:,.0f}; ex post = {n_post:,.0f}; journal = {a25['n']:,}; "
        f"pasmo {100 * wald_half_width(int(n_ante)):.2f} / {100 * wald_half_width(a25['n']):.2f} pp; "
        f"required_trades = {_n_required(a25):,.0f} → guard {'spełniony' if a25['n'] >= _n_required(a25) else 'NIESPEŁNIONY'}; "
        f"se = {100 * a25['se']:.4f}% → |r̄| >= {100 * 2.8 * a25['se']:.4f}%"
    )

    print("\n" + SEP)
    print("5. PEŁNE TABELE (do raw_output)")
    print(SEP)
    for name, w in arms:
        print(f"  --- {name} ---")
        print("  " + w["edge"].to_string(index=False).replace("\n", "\n  "))
        print("  " + w["pooled"].to_string(index=False).replace("\n", "\n  "))
        print("  " + str(w["classification"]))
        print(
            "  UWAGA: `classification` NIE jest kryterium (wniosek 24); `break_even_p` = diagnostyka ±B."
        )
    print(f"\n  czas całkowity: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
