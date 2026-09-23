"""
run_partial_tp_n1.py

N1 — nowy cel modelu: częściowe wyjście 50 % na bliższym celu (+1,67 % ceny = 5 % depozytu przy
dźwigni 3× / 1,5·ATR), stop przesunięty na cenę wejścia, reszta do dalszego celu, limit czasu 12 h.
Skrypt jednorazowy/analityczny, zbudowany na `backtest/checkpoint_lib.py` i `backtest/execution.py`
(zasada 13). KONFIGURACJA, REGUŁY I KRYTERIA SĄ ZAMROŻONE w pre-rejestracji zapisanej w OSOBNYM
commicie PRZED kodem: `runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md` (commit fa1abdb).

Jeden trening na oknie od `data.min_start` (zasada 20), potem dwie symulacje na TYCH SAMYCH
sygnałach: kontrola (pojedyncze wyjście, W1a) i N1 (wyjście wielonogowe). Werdykt N1 na zwrocie
netto (t_neff) z progiem uogólnionym p* — nie na trafności (lekcja W1b).

Skrypt jest NEUTRALNYM REPORTEREM: liczy i drukuje; werdykt podpisuje Claude w README rundy.

Użycie:
    py -m backtest.run_partial_tp_n1
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import yaml

from agents.labeling import effective_sample_size
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, fetch_window, load_config, summarize_result
from backtest.costs import (
    EXIT_REASON_BE_STOP,
    EXIT_REASON_SL,
    EXIT_REASON_TIMEOUT,
    EXIT_REASON_TP,
)
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule, ManagedExitRule
from backtest.metrics import (
    Z_TWO_SIDED_95,
    expected_trades,
    measurability_report,
    wald_half_width,
)

# --- KONFIGURACJA ZAMROŻONA (jak W1a: ramię A M1/F1 + wykonanie `limit_close`, k = 1) ---
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
FEATURES = REVERSION_FEATURES
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1

# Reguły użytkownika (pre-rejestracja, sekcja „Reguły prowadzenia pozycji”).
RULE = ManagedExitRule(partial_fraction=0.5, near_pct=0.0167)

# Pre-rejestrowany próg mocy dla werdyktu NEGATYWNEGO.
N_REQUIRED_NEGATIVE = 4000
ABSTENTION_REF = 0.4384  # K3/M1/F1 — do rachunku mocy ex ante
FILL_RATE_REF = 0.994  # W1a

FUNNEL = (
    ("ocenione świece", "n_rows_evaluated"),
    ("odpadło na abstynencji", "n_signals_no_direction"),
    ("bramka pewności", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnały kandydujące", "n_signals"),
)
SEP = "=" * 104


def _simulate(collected: dict, exit_rule: ManagedExitRule | None) -> dict:
    result = simulate_equity(
        collected["df"],
        collected["candidate_signals"],
        collected["folds_summary"],
        candle_minutes=CANDLE_MINUTES,
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        fill_model=FILL_MODEL_PATH,
        entry_rule=ENTRY,
        entry_validity_candles=VALIDITY,
        exit_rule=exit_rule,
    )
    return summarize_result(result, PRIMARY_SEED)


def _pack(summary: dict) -> dict:
    res = summary["backtest"]
    trades = res["trades"]
    real = trades.loc[~trades["kill_switch_active"]].copy()
    notional = real["position_size"] * real["entry_price"]
    real["gross_ret"] = real["gross_pnl"] / notional
    real["net_ret"] = real["net_pnl"] / notional
    real["cost_ret"] = real["cost"] / notional
    e = summary["edge_per_regime"].iloc[0]
    pooled = summary["pooled_per_regime"].iloc[0]
    n = len(real)
    r = real["net_ret"]
    se = float(r.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    t = float(r.mean() / se) if se and se > 0 else float("nan")
    n_eff = effective_sample_size(r)["n_eff"] if n > 1 else float("nan")
    t_neff = float(t * np.sqrt(n_eff / n)) if n > 1 else float("nan")
    wins = real["gross_ret"] > 0
    w_mean = float(real.loc[wins, "gross_ret"].mean()) if wins.any() else float("nan")
    l_mean = float(-real.loc[~wins, "gross_ret"].mean()) if (~wins).any() else float("nan")
    c_mean = float(real["cost_ret"].mean()) if n else float("nan")
    p_star = (l_mean + c_mean) / (w_mean + l_mean) if n and (w_mean + l_mean) > 0 else float("nan")
    return {
        "n": n,
        "n_unfilled": len(res["unfilled"]),
        "n_suppressed": int(trades["kill_switch_active"].sum()),
        "p": float(e["hit_rate"]),
        "ci_low": float(e["ci_low"]),
        "ci_high": float(e["ci_high"]),
        "be_symmetric": float(e["break_even_p"]),
        "p_star": p_star,
        "w_mean": w_mean,
        "l_mean": l_mean,
        "cost": c_mean,
        "r_mean": float(r.mean()),
        "r_median": float(r.median()),
        "r_std": float(r.std(ddof=1)),
        "r_p5": float(r.quantile(0.05)),
        "r_p95": float(r.quantile(0.95)),
        "se": se,
        "t": t,
        "n_eff": float(n_eff),
        "t_neff": t_neff,
        "t_equity": float(pooled["t_stat"]),
        "t_neff_equity": float(pooled["t_stat_neff"]),
        "edge": summary["edge_per_regime"],
        "pooled": summary["pooled_per_regime"],
        "classification": summary["classification"],
        "real": real,
    }


def _verdict(w: dict) -> str:
    if w["t_neff"] > Z_TWO_SIDED_95 and w["ci_low"] > w["p_star"]:
        return "POZYTYWNY — t_neff > 1,96 i ci_low(p) > p*. NAJPIERW SZUKAJ PRZECIEKU, nie ogłaszaj"
    if w["t_neff"] < -Z_TWO_SIDED_95 and w["n"] >= N_REQUIRED_NEGATIVE:
        return "NEGATYWNY — średni zwrot netto istotnie ujemny przy n >= wymaganym"
    return "NIEROZSTRZYGNIĘTY — |t_neff| < 1,96, ci_low(p) <= p* albo n poniżej wymaganego"


def _path_type(row: pd.Series) -> str:
    if row["n_legs"] == 1:
        return "stop (cała)" if row["exit_reason"] == EXIT_REASON_SL else "timeout (cała)"
    tail = {
        EXIT_REASON_TP: "dalszy cel",
        EXIT_REASON_BE_STOP: "stop na wejściu",
        EXIT_REASON_TIMEOUT: "timeout",
    }
    return "bliższy cel → " + tail.get(row["exit_reason"], row["exit_reason"])


def main() -> None:
    t0 = time.time()
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]

    print(SEP)
    print("N1 — NOWY CEL MODELU: częściowe wyjście 50 % + stop na wejściu (konfiguracja ZAMROŻONA)")
    print(SEP)
    df = fetch_window(data_cfg, TIMEFRAME)
    print(
        f"dane      : {len(df)} świec {TIMEFRAME} od {df['timestamp'].min()} do {df['timestamp'].max()}"
        f" (zasada 20: min_start = {data_cfg['min_start']})\n"
        f"pipeline  : BEZ bramki reżimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced`, cechy {FEATURES},\n"
        f"            walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}, wejście {ENTRY.kind} k={VALIDITY}\n"
        f"JEDNA zmienna: zarządzanie pozycją po wejściu (exit_rule={RULE}); etykieta bez zmian.\n"
    )

    collected = collect_signals(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    print(f"  trening zakończony po {time.time() - t0:.0f} s")
    active = [f for f in collected["folds_summary"] if not f["skipped"]]
    print(f"  foldy: {len(active)} aktywne / {len(collected['folds_summary'])} łącznie")
    for label, key in FUNNEL:
        print(f"  {label:>24}: {sum(f[key] for f in active):8d}")
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    print(f"  {'abstynencja':>24}: {100 * n_abst / n_rows:7.2f}%")

    control = _pack(_simulate(collected, None))
    n1 = _pack(_simulate(collected, RULE))

    print("\n1. WYNIK — zwrot netto per trade (kryterium) i trafność (próg uogólniony p*)")
    print(
        f"  {'ramię':>9} | {'n':>5} | {'r̄ netto':>9} | {'CI 95%':>21} | {'mediana':>8} | "
        f"{'t':>6} | {'N_eff':>6} | {'t_neff':>6} | {'p':>7} | {'CI(p)':>17} | {'p*':>6} | {'BE ±B':>6}"
    )
    print("  " + "-" * 128)
    for name, w in (("kontrola", control), ("N1", n1)):
        half = Z_TWO_SIDED_95 * w["se"]
        print(
            f"  {name:>9} | {w['n']:5d} | {100 * w['r_mean']:+8.4f}% | "
            f"[{100 * (w['r_mean'] - half):+8.4f}; {100 * (w['r_mean'] + half):+8.4f}] | {100 * w['r_median']:+7.4f}% | "
            f"{w['t']:+6.2f} | {w['n_eff']:6.0f} | {w['t_neff']:+6.2f} | {100 * w['p']:6.2f}% | "
            f"[{100 * w['ci_low']:6.2f}; {100 * w['ci_high']:6.2f}] | {100 * w['p_star']:5.2f}% | {100 * w['be_symmetric']:5.2f}%"
        )
    print(f"  >>> WERDYKT N1: {_verdict(n1)}")
    print(f"  (kontrola: {_verdict(control)} — odniesienie, 0 wariantów)")
    print(
        "  r̄ = średni zwrot netto w % nominału wejścia; t z próby, t_neff po korekcie N_eff (autokorelacja);\n"
        "  p* = (L̄ + C)/(W̄ + L̄) — trafność zerująca oczekiwaną wypłatę przy ZMIERZONYCH W̄/L̄; „BE ±B” = 0,5(1+C/B)\n"
        "  z `summarize_edge_by_regime` — przy wypłatach asymetrycznych DIAGNOSTYKA, nie próg (W1b)."
    )

    print(
        "\n2. PORÓWNANIE PAROWANE N1 − kontrola (te same sygnały i wypełnienia) — obserwacja, nie kryterium"
    )
    a = control["real"].set_index("timestamp")["net_ret"]
    b = n1["real"].set_index("timestamp")["net_ret"]
    both = pd.concat([a.rename("ctrl"), b.rename("n1")], axis=1, join="inner")
    diff = both["n1"] - both["ctrl"]
    se_d = diff.std(ddof=1) / np.sqrt(len(diff))
    print(
        f"  wspólnych transakcji {len(both)} (kontrola {len(a)}, N1 {len(b)}); "
        f"identycznych (różnica 0): {int((diff.abs() < 1e-12).sum())}\n"
        f"  średnia różnica {100 * diff.mean():+.4f}% nominału, 95% CI "
        f"[{100 * (diff.mean() - Z_TWO_SIDED_95 * se_d):+.4f}; {100 * (diff.mean() + Z_TWO_SIDED_95 * se_d):+.4f}], "
        f"t = {diff.mean() / se_d:+.2f}; mediana różnicy {100 * diff.median():+.4f}%"
    )

    print("\n3. ŚCIEŻKI WYJŚCIA N1 — kogo NIE ma w zbiorze i skąd biorą się pieniądze")
    real = n1["real"].copy()
    real["ścieżka"] = real.apply(_path_type, axis=1)
    g = (
        real.groupby("ścieżka")
        .agg(
            n=("net_ret", "size"),
            udział=("net_ret", lambda s: len(s) / len(real)),
            brutto=("gross_ret", "mean"),
            netto=("net_ret", "mean"),
            wygrane=("gross_ret", lambda s: (s > 0).mean()),
        )
        .sort_values("n", ascending=False)
    )
    print(
        f"  {'ścieżka':>28} | {'n':>5} | {'udział':>7} | {'brutto śr.':>10} | {'netto śr.':>10} | {'wygrane':>7}"
    )
    print("  " + "-" * 82)
    for name, row in g.iterrows():
        print(
            f"  {name:>28} | {int(row['n']):5d} | {100 * row['udział']:6.1f}% | {100 * row['brutto']:+9.4f}% | "
            f"{100 * row['netto']:+9.4f}% | {100 * row['wygrane']:6.1f}%"
        )
    for name, w in (("kontrola", control), ("N1", n1)):
        print(
            f"  {name}: W̄ = {100 * w['w_mean']:.4f}%, L̄ = {100 * w['l_mean']:.4f}%, C = {100 * w['cost']:.4f}%, "
            f"std zwrotu {100 * w['r_std']:.3f}%, p5/p95 [{100 * w['r_p5']:+.3f}%; {100 * w['r_p95']:+.3f}%], "
            f"niewypełnione {w['n_unfilled']}, stłumione {w['n_suppressed']}"
        )
    near_hit = (real["n_legs"] == 2).mean()
    print(f"  udział transakcji z bliższym celem: {100 * near_hit:.1f}%")

    print("\n4. MIERZALNOŚĆ (zasada 18) — ex ante wg pre-rejestracji i ex post")
    n_exp = expected_trades(n_rows, ABSTENTION_REF, FILL_RATE_REF)
    n_exp_post = expected_trades(
        n_rows, n_abst / n_rows, 1 - n1["n_unfilled"] / max(len(collected["candidate_signals"]), 1)
    )
    print(
        f"  expected_trades ex ante (abstynencja {100 * ABSTENTION_REF:.2f}%, wypełnienia {100 * FILL_RATE_REF:.1f}%) = {n_exp:,.0f}; "
        f"ex post = {n_exp_post:,.0f}; journal N1 = {n1['n']:,}\n"
        f"  se zwrotu netto N1 = {100 * n1['se']:.4f}% → wykrywalny efekt (moc 80%) |r̄| >= {100 * 2.8 * n1['se']:.4f}%; "
        f"próg mocy dla negatywu n >= {N_REQUIRED_NEGATIVE:,}: {'spełniony' if n1['n'] >= N_REQUIRED_NEGATIVE else 'NIESPEŁNIONY'}\n"
        f"  trafność (diagnostyka): pasmo {100 * wald_half_width(n1['n']):.2f} pp; "
        f"measurability_report(p_kontroli, BE ±B kontroli, n) = {measurability_report(control['p'], control['be_symmetric'], n1['n'])['verdict']}"
    )

    print("\n" + SEP)
    print("5. PEŁNE TABELE (do raw_output)")
    print(SEP)
    for name, w in (("kontrola", control), ("N1", n1)):
        print(f"  --- {name} ---")
        print("  " + w["edge"].to_string(index=False).replace("\n", "\n  "))
        print("  " + w["pooled"].to_string(index=False).replace("\n", "\n  "))
        print("  " + str(w["classification"]))
        print(
            "  UWAGA: `classification` NIE jest kryterium (wniosek 24); `barrier_pct`/`break_even_p` liczone z OSTATNIEJ nogi — diagnostyka."
        )
    print(f"\n  czas całkowity: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
