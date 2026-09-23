"""
run_ta_a1.py — runda A1: formacje świecowe z podręcznika jako REGUŁA szukania pozycji (A1a)
i jako JEDNA dodatkowa cecha modelu (A1b). Pre-rejestracja (commit f514bcf, PRZED tym kodem):
runs/2026-09-23_a1-formacje-swiecowe/README.md.

Uruchomienie:  py -m backtest.run_ta_a1

Skrypt jest NEUTRALNYM REPORTEREM: liczy i drukuje. Odczyt kryterium z pre-rejestracji
(POZYTYWNY / NEGATYWNY / NIEROZSTRZYGNIĘTY) wypisuje jako wynik reguły, a werdykt podpisuje
Claude w README rundy. Buduje na backtest/checkpoint_lib.py (`fetch_window`,
`build_rule_signals`, `summarize_result`, `summarize_trade_returns`) i backtest/engine.py
(`collect_signals`, `simulate_equity`). Tabele per formacja / per kierunek są OPISOWE —
pre-rejestracja zakazuje werdyktów na podzbiorach (loteria multiple-testing).
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import talib
import yaml

from agents.feature_miner import CDL_SCORE_6_PATTERNS
from agents.ml_optimizer import REVERSION_FEATURES
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

# --- konfiguracja ZAMROŻONA w pre-rejestracji (ta sama co kontrola N1) -----------------------
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
FEATURE = "cdl_score_6"
CONTROL_FEATURES = list(REVERSION_FEATURES)
A1B_FEATURES = [*REVERSION_FEATURES, FEATURE]
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1

# --- liczby z pre-rejestracji (ex ante) ------------------------------------------------------
N_SIGNAL_CANDLES_2021 = 2637  # świece ze score != 0 na 12 042 świecach od 2021 (zliczenie)
OOS_SHARE_REF = 11592 / 12042  # udział świec OOS (pierwsze 60 dni = trening)
ABSTENTION_REF = 0.4038  # kontrola N1
FILL_RATE_REF = 0.994  # W1a
BE_REF = 0.5307  # próg ±B kontroli N1
N1_CONTROL_REF = {"n": 6789, "p": 0.4958, "r_mean": -0.001069}  # regresja: kontrola = N1

FUNNEL = (
    ("świece ocenione", "n_rows_evaluated"),
    ("bez kierunku (abstynencja)", "n_signals_no_direction"),
    ("bramka pewności", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnały kandydujące", "n_signals"),
)
SEP = "=" * 104
PATTERN_PL = {
    "CDLENGULFING": "objęcie",
    "CDLHAMMER": "młot",
    "CDLSHOOTINGSTAR": "spadająca gwiazda",
    "CDLMORNINGSTAR": "gwiazda poranna",
    "CDLEVENINGSTAR": "gwiazda wieczorna",
    "CDLRISEFALL3METHODS": "trójka hossy/bessy",
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


def _verdict(w: dict) -> str:
    """Kryterium z pre-rejestracji A1 — odczyt reguły, nie decyzja."""
    if w["t_neff"] > Z_TWO_SIDED_95 and w["ci_low"] > w["p_star"]:
        return "POZYTYWNY — t_neff > 1,96 i ci_low(p) > p*. NAJPIERW SZUKAJ PRZECIEKU, nie ogłaszaj"
    if w["t_neff"] < -Z_TWO_SIDED_95 and w["n"] >= _n_required(w):
        return f"NEGATYWNY — t_neff < −1,96 przy n >= required_trades(0,50; BE) = {_n_required(w):,.0f}"
    return "NIEROZSTRZYGNIĘTY — |t_neff| < 1,96, ci_low(p) <= p* albo n poniżej wymaganego"


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
        f"{100 * w['p_star']:5.2f}% | {100 * w['be_symmetric']:5.2f}%"
    )


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


def main() -> None:
    t0 = time.time()
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]

    print(SEP)
    print(
        "A1 — FORMACJE ŚWIECOWE: reguła bez modelu (A1a) i jedna cecha modelu (A1b); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    df = fetch_window(data_cfg, TIMEFRAME)
    print(
        f"dane      : {len(df)} świec {TIMEFRAME} od {df['timestamp'].min()} do {df['timestamp'].max()}"
        f" (zasada 20: min_start = {data_cfg['min_start']})\n"
        f"pipeline  : BEZ bramki reżimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced`, walk-forward "
        f"{TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}, wejście {ENTRY.kind} k={VALIDITY}, "
        f"pojedyncze wyjście TP/SL/timeout\n"
        f"kontrola  : cechy {CONTROL_FEATURES}\n"
        f"A1a       : reguła kierunek = sign({FEATURE}), confidence 1,0, bez modelu\n"
        f"A1b       : cechy {A1B_FEATURES}  (JEDNA cecha więcej niż kontrola)\n"
    )

    print("0. LEJEK — kontrola i A1b (dwa treningi), A1a (reguła)")
    control_c = _collect(df, CONTROL_FEATURES, rule)
    print(f"  trening kontroli zakończony po {time.time() - t0:.0f} s")
    n_rows_ctrl, n_abst_ctrl = _print_funnel("kontrola", control_c)
    a1b_c = _collect(df, A1B_FEATURES, rule)
    print(f"  trening A1b zakończony po {time.time() - t0:.0f} s")
    n_rows_b, n_abst_b = _print_funnel("A1b", a1b_c)

    fdf = control_c["df"]
    assert fdf[FEATURE].equals(a1b_c["df"][FEATURE]), "cecha musi być identyczna w obu treningach"
    rule_signals, rule_funnel = build_rule_signals(fdf, control_c["folds_summary"], FEATURE)
    print(
        f"  [A1a] świece w oknach OOS: {rule_funnel['n_rows_window']} (kontrola oceniła {n_rows_ctrl}); "
        f"bez formacji/konflikt: {rule_funnel['n_no_signal']}; bez etykiety/ATR: {rule_funnel['n_label_nan']}; "
        f"bramka kosztowa: {rule_funnel['n_cost_gated']}; sygnały: {rule_funnel['n_signals']} "
        f"(long {sum(s['signal_direction'] > 0 for s in rule_signals)}, "
        f"short {sum(s['signal_direction'] < 0 for s in rule_signals)})"
    )
    in_oos = fdf.loc[
        fdf["timestamp"]
        >= min(f["test_start"] for f in control_c["folds_summary"] if not f["skipped"])
    ]
    print(
        f"  [A1a] rozkład {FEATURE} w oknie OOS: "
        f"{in_oos[FEATURE].value_counts().sort_index().to_dict()}"
    )

    control = _simulate(fdf, control_c["candidate_signals"], control_c["folds_summary"])
    a1a = _simulate(fdf, rule_signals, control_c["folds_summary"])
    a1b = _simulate(a1b_c["df"], a1b_c["candidate_signals"], a1b_c["folds_summary"])
    arms = (("kontrola", control), ("A1a", a1a), ("A1b", a1b))

    print(
        "\n1. KRYTERIUM — zwrot netto per trade (t_neff) i trafność wobec p* (dwa warunki, pre-rejestracja)"
    )
    print(
        f"  {'ramię':>9} | {'n':>5} | {'r̄ netto':>9} | {'CI 95%':>21} | {'mediana':>8} | "
        f"{'t':>6} | {'N_eff':>6} | {'t_neff':>6} | {'p':>7} | {'CI(p)':>17} | {'p*':>6} | {'BE ±B':>6}"
    )
    print("  " + "-" * 128)
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
        f"  regresja kontroli wobec N1 (n {N1_CONTROL_REF['n']}, p {100 * N1_CONTROL_REF['p']:.2f}%, "
        f"r̄ {100 * N1_CONTROL_REF['r_mean']:+.4f}%): {'ZGODNA' if ok else 'ROZJAZD — sprawdź pipeline'}"
    )
    print(
        "  r̄ = średni zwrot netto w % nominału wejścia; t_neff po korekcie N_eff; p* = (L̄ + C)/(W̄ + L̄);\n"
        "  „BE ±B” = 0,5(1+C/B) z `summarize_edge_by_regime` — diagnostyka przy wypłatach asymetrycznych (W1b)."
    )

    print(
        "\n2. PORÓWNANIE PAROWANE A1b − kontrola (te same świece i wypełnienia) — obserwacja, nie kryterium"
    )
    a = control["real"].set_index("timestamp")["net_ret"]
    b = a1b["real"].set_index("timestamp")["net_ret"]
    both = pd.concat([a.rename("ctrl"), b.rename("a1b")], axis=1, join="inner")
    diff = both["a1b"] - both["ctrl"]
    se_d = diff.std(ddof=1) / np.sqrt(len(diff))
    same_dir = pd.concat(
        [
            control["real"].set_index("timestamp")["signal_direction"].rename("c"),
            a1b["real"].set_index("timestamp")["signal_direction"].rename("b"),
        ],
        axis=1,
        join="inner",
    )
    print(
        f"  wspólnych transakcji {len(both)} (kontrola {len(a)}, A1b {len(b)}); "
        f"identycznych (różnica 0): {int((diff.abs() < 1e-12).sum())}; "
        f"ten sam kierunek: {int((same_dir['c'] == same_dir['b']).sum())}\n"
        f"  średnia różnica {100 * diff.mean():+.4f}% nominału, 95% CI "
        f"[{100 * (diff.mean() - Z_TWO_SIDED_95 * se_d):+.4f}; {100 * (diff.mean() + Z_TWO_SIDED_95 * se_d):+.4f}], "
        f"t = {diff.mean() / se_d:+.2f}; mediana różnicy {100 * diff.median():+.4f}%\n"
        f"  tylko w kontroli: {len(a.index.difference(b.index))}, tylko w A1b: {len(b.index.difference(a.index))}"
    )

    print(
        "\n3. A1a OPISOWO — skąd biorą się pieniądze (bez werdyktów na podzbiorach — pre-rejestracja)"
    )
    real = a1a["real"].copy()
    reasons = [
        ("cel (tp)", real.loc[real["exit_reason"] == EXIT_REASON_TP]),
        ("stop (sl)", real.loc[real["exit_reason"] == EXIT_REASON_SL]),
        ("timeout", real.loc[real["exit_reason"] == EXIT_REASON_TIMEOUT]),
    ]
    _print_group_table("3a. powód wyjścia", reasons)
    _print_group_table(
        "3b. kierunek",
        [
            ("long (formacje bycze)", real.loc[real["signal_direction"] > 0]),
            ("short (niedźwiedzie)", real.loc[real["signal_direction"] < 0]),
        ],
    )
    o, h, lo_, c = (fdf[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    patt = pd.DataFrame(
        {name: np.sign(getattr(talib, name)(o, h, lo_, c)) for name in CDL_SCORE_6_PATTERNS},
        index=fdf.index,
    )
    patt["timestamp"] = fdf["timestamp"].to_numpy()
    patt[FEATURE] = fdf[FEATURE].to_numpy()
    joined = real.merge(patt, on="timestamp", how="left")
    _print_group_table(
        "3c. formacja obecna w świecy sygnału (transakcja może mieć > 1 formację)",
        [(PATTERN_PL[name], joined.loc[joined[name] != 0]) for name in CDL_SCORE_6_PATTERNS],
    )
    _print_group_table(
        "3d. |score| (liczba zgodnych formacji)",
        [
            ("|score| = 1", joined.loc[joined[FEATURE].abs() == 1]),
            ("|score| >= 2", joined.loc[joined[FEATURE].abs() >= 2]),
        ],
    )
    for name, w in arms:
        print(
            f"  {name}: W̄ = {100 * w['w_mean']:.4f}%, L̄ = {100 * w['l_mean']:.4f}%, C = {100 * w['cost']:.4f}%, "
            f"std zwrotu {100 * w['r_std']:.3f}%, p5/p95 [{100 * w['r_p5']:+.3f}%; {100 * w['r_p95']:+.3f}%], "
            f"niewypełnione {w['n_unfilled']}, stłumione {w['n_suppressed']}"
        )

    print("\n4. MIERZALNOŚĆ (zasada 18) — ex ante wg pre-rejestracji i ex post")
    n_a1a_ante = expected_trades(int(N_SIGNAL_CANDLES_2021 * OOS_SHARE_REF), 0.0, FILL_RATE_REF)
    n_a1a_post = expected_trades(
        rule_funnel["n_signals"], 0.0, 1 - a1a["n_unfilled"] / max(rule_funnel["n_signals"], 1)
    )
    n_b_ante = expected_trades(n_rows_ctrl, ABSTENTION_REF, FILL_RATE_REF)
    n_b_post = expected_trades(
        n_rows_b,
        n_abst_b / n_rows_b,
        1 - a1b["n_unfilled"] / max(len(a1b_c["candidate_signals"]), 1),
    )
    for name, w, n_ante, n_post in (
        ("A1a", a1a, n_a1a_ante, n_a1a_post),
        ("A1b", a1b, n_b_ante, n_b_post),
    ):
        rep = measurability_report(0.56, BE_REF, n_ante)
        print(
            f"  {name}: expected_trades ex ante = {n_ante:,.0f}; ex post = {n_post:,.0f}; journal = {w['n']:,}\n"
            f"       pasmo trafności ex ante {100 * wald_half_width(int(n_ante)):.2f} pp / ex post {100 * wald_half_width(w['n']):.2f} pp; "
            f"p_detectable ex ante (BE {100 * BE_REF:.2f}%) = {100 * rep['p_detectable']:.2f}% → hipoteza „p ≥ 56%” {rep['verdict']}\n"
            f"       required_trades(0,50; BE ramienia {100 * w['be_symmetric']:.2f}%) = {_n_required(w):,.0f} "
            f"→ guard negatywu {'spełniony' if w['n'] >= _n_required(w) else 'NIESPEŁNIONY'}\n"
            f"       se zwrotu netto = {100 * w['se']:.4f}% → wykrywalny efekt (moc 80%) |r̄| >= {100 * 2.8 * w['se']:.4f}%"
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
