"""
run_execution_w1.py

W1 — wykonanie po konkretnej cenie: uczciwy model wypełnień w backteście. Skrypt
jednorazowy/analityczny, zbudowany na `backtest/checkpoint_lib.py` i `backtest/execution.py`
(zasada 13). KONFIGURACJA, WARIANTY, REGUŁY WYPEŁNIEŃ I KRYTERIA SĄ ZAMROŻONE w pre-rejestracji
zapisanej w OSOBNYM commicie PRZED kodem: `runs/2026-09-23_w1-wykonanie-po-cenie/README.md`
(commit 9b09177).

Dwie części:
  A. pełna historia 4h (6,8 roku), JEDEN trening (`collect_signals`), potem: kontrola
     (tryb "label" — musi odtworzyć ramię A z M1/F1 co do sztuki), trzy warianty wejścia
     przy k = 1 (każdy z werdyktem per pre-rejestracja) oraz wrażliwość k = 2, 3 (bez werdyktu);
  B. kalibracja: okno 2023-07 → 2026-07, jeden trening, każdy wariant przy k = 1 liczony trybem
     4h i trybem 5m — pomiar błędu przybliżenia trybu 4h (bez werdyktu).

Skrypt jest NEUTRALNYM REPORTEREM: liczy i drukuje; werdykt podpisuje Claude w README rundy.

Użycie:
    py -m backtest.run_execution_w1
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import yaml

from agents.labeling import ATR_MULTIPLIER
from agents.ml_optimizer import REVERSION_FEATURES
from agents.risk_controller import MIN_BARRIER_TO_COST_RATIO
from backtest.checkpoint_lib import PRIMARY_SEED, fetch_native, load_config, summarize_result
from backtest.costs import (
    EXECUTION_MAKER_LIMIT,
    EXECUTION_TAKER_ONLY,
    EXIT_REASON_SL,
    EXIT_REASON_TIMEOUT,
    EXIT_REASON_TP,
    gate_cost_fraction,
)
from backtest.engine import (
    FILL_MODEL_LABEL,
    FILL_MODEL_PATH,
    REGIME_ALL,
    collect_signals,
    simulate_equity,
)
from backtest.execution import (
    ENTRY_LIMIT_CLOSE,
    ENTRY_LIMIT_PULLBACK,
    ENTRY_STOP_BREAKOUT,
    EntryRule,
)
from backtest.metrics import (
    Z_TWO_SIDED_95,
    expected_trades,
    measurability_report,
    required_trades,
    wald_half_width,
)

# --- KONFIGURACJA ZAMROŻONA (ramię A z M1/F1 = konfiguracja kanoniczna po K3/A1) ---
TIMEFRAME = "4h"
INTRABAR_TIMEFRAME = "5m"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
FEATURES = REVERSION_FEATURES

# Liczby odniesienia ramienia A (M1/F1) — kontrola musi je odtworzyć CO DO SZTUKI.
REF_N = 8033
REF_HITS = 4046

# Warianty (3, każdy z werdyktem) — pre-rejestracja, tabela wariantów.
VARIANTS = {
    "W1a": ("limit po close świecy sygnału", EntryRule(ENTRY_LIMIT_CLOSE)),
    "W1b": ("limit na cofnięciu 0,5·ATR", EntryRule(ENTRY_LIMIT_PULLBACK, 0.5)),
    "W1c": ("stop na wybiciu ponad high / pod low", EntryRule(ENTRY_STOP_BREAKOUT)),
}
PRIMARY_VALIDITY = 1
SENSITIVITY_VALIDITY = (2, 3)  # tylko opisowo, bez werdyktu (H3/D5)

# Okno części kalibracyjnej = zasięg danych 5m w cache (config: data.start/end, 2023-07 → 2026-07);
# w części B `timeframe_start_overrides` jest wyzerowane, żeby 4h i 5m miały to samo okno.

FUNNEL = (
    ("ocenione świece", "n_rows_evaluated"),
    ("odpadło na abstynencji", "n_signals_no_direction"),
    ("bramka pewności", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnały kandydujące", "n_signals"),
)
SEP = "=" * 104
REASONS = (EXIT_REASON_TP, EXIT_REASON_SL, EXIT_REASON_TIMEOUT)


def _collect(df: pd.DataFrame, rule: dict) -> dict:
    return collect_signals(
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


def _simulate(
    collected: dict, *, fill_model: str, entry_rule=None, validity=PRIMARY_VALIDITY, intrabar=None
):
    result = simulate_equity(
        collected["df"],
        collected["candidate_signals"],
        collected["folds_summary"],
        candle_minutes=CANDLE_MINUTES,
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        fill_model=fill_model,
        entry_rule=entry_rule,
        entry_validity_candles=validity,
        intrabar_ohlcv=intrabar,
    )
    return summarize_result(result, PRIMARY_SEED)


def _pack(summary: dict, collected: dict) -> dict:
    """Wszystkie liczby jednego przebiegu w jednym słowniku (żeby raport nie liczył dwa razy)."""
    res = summary["backtest"]
    trades = res["trades"]
    real = trades.loc[~trades["kill_switch_active"]]
    e = summary["edge_per_regime"].iloc[0]
    n_candidates = len(collected["candidate_signals"])
    n_unfilled = len(res["unfilled"])
    notional = real["position_size"] * real["entry_price"]
    reasons = real["exit_reason"].value_counts()
    out = {
        "n_candidates": n_candidates,
        "n_unfilled": n_unfilled,
        "n_suppressed": int(trades["kill_switch_active"].sum()),
        "n": int(e["n_trades"]),
        "hits": int((real["gross_pnl"] > 0).sum()),
        "p": float(e["hit_rate"]),
        "ci_low": float(e["ci_low"]),
        "ci_high": float(e["ci_high"]),
        "z": float(e["z_stat"]),
        "break_even": float(e["break_even_p"]),
        "barrier": float(e["barrier_pct"]),
        "cost": float(e["cost_pct"]),
        "cost_median": float((real["cost"] / notional).median()) if len(real) else float("nan"),
        "share": {
            r: float((real["exit_reason"] == r).mean()) if len(real) else float("nan")
            for r in REASONS
        },
        "counts": {r: int(reasons.get(r, 0)) for r in REASONS},
        "holding_mean": (
            float((real["exit_bar_offset"] - real["fill_bar_offset"] + 1).mean())
            if len(real)
            else float("nan")
        ),
        "fill_offset_mean": float(real["fill_bar_offset"].mean()) if len(real) else float("nan"),
        # dwa mianowniki, jawnie: % NOMINAŁU (ekonomika jednej transakcji) i % EQUITY
        # (to, co liczy `summarize_pooled_by_regime`: net_pnl / equity_before, sizing 0,5% ryzyka)
        "ret_mean": float((real["net_pnl"] / notional).mean()) if len(real) else float("nan"),
        "ret_median": float((real["net_pnl"] / notional).median()) if len(real) else float("nan"),
        "ret_eq_median": (
            float((real["net_pnl"] / real["equity_before"]).median()) if len(real) else float("nan")
        ),
        "classification": summary["classification"],
        "edge": summary["edge_per_regime"],
        "pooled": summary["pooled_per_regime"],
        "trades": trades,
        "unfilled": res["unfilled"],
    }
    out["fill_rate"] = 1.0 - n_unfilled / n_candidates if n_candidates else float("nan")
    return out


def _fill_rate_by_direction(collected: dict, packed: dict) -> dict[str, float]:
    cands = pd.DataFrame(collected["candidate_signals"])
    unfilled_ts = set(packed["unfilled"]["timestamp"])
    rates = {}
    for name, d in (("long", 1.0), ("short", -1.0)):
        sub = cands.loc[cands["signal_direction"] == d]
        rates[name] = 1.0 - sub["timestamp"].isin(unfilled_ts).mean() if len(sub) else float("nan")
    return rates


def _selection_diagnostic(collected: dict, packed: dict) -> dict:
    """Poprawność kierunku wg ETYKIETY (label ≠ 0) wśród wypełnionych vs niewypełnionych."""
    cands = pd.DataFrame(collected["candidate_signals"])
    unfilled_ts = set(packed["unfilled"]["timestamp"])
    suppressed_ts = set(packed["trades"].loc[packed["trades"]["kill_switch_active"], "timestamp"])
    cands = cands.loc[cands["label"] != 0.0]
    correct = cands["signal_direction"] * cands["label"] > 0
    is_unf = cands["timestamp"].isin(unfilled_ts)
    is_sup = cands["timestamp"].isin(suppressed_ts)
    filled = correct[~is_unf & ~is_sup]
    unf = correct[is_unf]
    n_f, n_u = len(filled), len(unf)
    p_f = float(filled.mean()) if n_f else float("nan")
    p_u = float(unf.mean()) if n_u else float("nan")
    if n_f and n_u:
        se = np.sqrt(p_f * (1 - p_f) / n_f + p_u * (1 - p_u) / n_u)
        delta = p_f - p_u
        ci = (delta - Z_TWO_SIDED_95 * se, delta + Z_TWO_SIDED_95 * se)
        z = delta / se if se > 0 else float("nan")
    else:
        delta, ci, z = float("nan"), (float("nan"), float("nan")), float("nan")
    return {
        "n_filled": n_f,
        "p_filled": p_f,
        "n_unfilled": n_u,
        "p_unfilled": p_u,
        "delta": delta,
        "ci": ci,
        "z": z,
    }


def _verdict(packed: dict, p_reference: float) -> tuple[str, float]:
    """Kryterium per wariant — pre-rejestracja, sekcja „Kryterium”."""
    n_req = required_trades(p_reference, packed["break_even"])
    if packed["ci_low"] > packed["break_even"]:
        return "POZYTYWNY — ci_low > próg. NAJPIERW SZUKAJ PRZECIEKU, nie ogłaszaj", n_req
    if packed["ci_high"] < packed["break_even"] and packed["n"] >= n_req:
        return "NEGATYWNY — ci_high < próg przy n >= wymaganym", n_req
    return "NIEROZSTRZYGNIĘTY — CI przecina próg albo n poniżej wymaganego", n_req


def _print_funnel(collected: dict) -> None:
    active = [f for f in collected["folds_summary"] if not f["skipped"]]
    print(f"  foldy: {len(active)} aktywne / {len(collected['folds_summary'])} łącznie")
    for label, key in FUNNEL:
        print(f"  {label:>24}: {sum(f[key] for f in active):8d}")
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    print(f"  {'abstynencja':>24}: {100 * n_abst / n_rows:7.2f}%")


def _print_geometry_row(name: str, w: dict) -> None:
    print(
        f"  {name:>26} | {w['n']:6d} | {100 * w['fill_rate']:6.1f}% | "
        f"{100 * w['share'][EXIT_REASON_TP]:5.1f}/{100 * w['share'][EXIT_REASON_SL]:5.1f}/"
        f"{100 * w['share'][EXIT_REASON_TIMEOUT]:5.1f} | {100 * w['barrier']:7.4f}% | "
        f"{100 * w['cost']:7.4f}% | {100 * w['break_even']:6.2f}% | {w['holding_mean']:4.2f}"
    )


GEOMETRY_HEADER = (
    f"  {'wariant':>26} | {'n':>6} | {'wypełn.':>7} | {'tp/sl/timeout %':>17} | "
    f"{'bariera B':>9} | {'koszt C':>8} | {'próg BE':>7} | {'świec':>5}"
)


def main() -> None:
    t0 = time.time()
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]

    print(SEP)
    print("W1 — WYKONANIE PO KONKRETNEJ CENIE: uczciwy model wypełnień (konfiguracja ZAMROŻONA)")
    print(SEP)
    df_full = fetch_native(data_cfg, TIMEFRAME)
    print(
        f"dane      : {len(df_full)} świec {TIMEFRAME}, {df_full['timestamp'].min()} -> {df_full['timestamp'].max()}\n"
        f"pipeline  : BEZ bramki reżimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced`, cechy {FEATURES},\n"
        f"            walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}, "
        f"model kosztów `{EXECUTION_MAKER_LIMIT}`, bramka kosztowa {gate_cost_fraction(EXECUTION_MAKER_LIMIT):.4f}\n"
        f"JEDNA zmienna: mechanika wypełnień i wyjść (fill_model), reszta jak ramię A z M1/F1.\n"
    )

    # ------------------------------------------------------------------ CZĘŚĆ A
    print(SEP)
    print("CZĘŚĆ A — pełna historia, jeden trening, kontrola + 3 warianty (k = 1)")
    print(SEP)
    collected = _collect(df_full, rule)
    print(f"  trening zakończony po {time.time() - t0:.0f} s")
    _print_funnel(collected)

    control = _pack(_simulate(collected, fill_model=FILL_MODEL_LABEL), collected)
    ok = control["n"] == REF_N and control["hits"] == REF_HITS
    print("\n0. KONTROLA — tryb `label` musi odtworzyć ramię A z M1/F1 co do sztuki")
    print(
        f"  n = {control['n']} (ref {REF_N}), trafień = {control['hits']} (ref {REF_HITS}), "
        f"p = {100 * control['p']:.4f}%  ->  {'ZGODNE' if ok else 'NIEZGODNE — WYNIK RUNDY NIEWAŻNY'}"
    )
    print(
        f"  próg BE = {100 * control['break_even']:.2f}%, B = {100 * control['barrier']:.4f}%, "
        f"C = {100 * control['cost']:.4f}%, CI [{100 * control['ci_low']:.2f}%; {100 * control['ci_high']:.2f}%]"
    )

    variants = {}
    for code, (desc, entry_rule) in VARIANTS.items():
        variants[code] = _pack(
            _simulate(collected, fill_model=FILL_MODEL_PATH, entry_rule=entry_rule), collected
        )
        variants[code]["desc"] = desc
        variants[code]["by_direction"] = _fill_rate_by_direction(collected, variants[code])
        variants[code]["selection"] = _selection_diagnostic(collected, variants[code])

    print("\n1. WYNIK — trafność wobec progu opłacalności (warianty z werdyktem)")
    print(
        f"  {'wariant':>6} | {'n':>6} | {'niewyp.':>7} | {'trafność':>9} | {'CI 95%':>20} | {'próg BE':>8} | {'margines':>10} | werdykt"
    )
    print("  " + "-" * 118)
    for code, w in (("kontrola", control), *variants.items()):
        if code == "kontrola":
            verdict, n_req = "(odniesienie, 0 wariantów)", float("nan")
        else:
            verdict, n_req = _verdict(w, control["p"])
        print(
            f"  {code:>6} | {w['n']:6d} | {w['n_unfilled']:7d} | {100 * w['p']:8.2f}% | "
            f"[{100 * w['ci_low']:7.2f}%; {100 * w['ci_high']:7.2f}%] | {100 * w['break_even']:7.2f}% | "
            f"{100 * (w['p'] - w['break_even']):+9.2f} pp | {verdict}"
            + ("" if np.isnan(n_req) else f" (wymagane n = {n_req:,.0f})")
        )

    print("\n2. WYPEŁNIENIA I SELEKCJA — kogo NIE ma w zbiorze")
    print(
        f"  {'wariant':>6} | {'wypełn. ogółem':>14} | {'long':>7} | {'short':>7} | {'popr. kier. wypełnione':>23} | {'niewypełnione':>14} | {'różnica (pp), CI 95%':>26} | z"
    )
    print("  " + "-" * 122)
    for code, w in variants.items():
        s, bd = w["selection"], w["by_direction"]
        print(
            f"  {code:>6} | {100 * w['fill_rate']:13.2f}% | {100 * bd['long']:6.1f}% | {100 * bd['short']:6.1f}% | "
            f"{100 * s['p_filled']:7.2f}% (n={s['n_filled']:5d}) | {100 * s['p_unfilled']:6.2f}% (n={s['n_unfilled']:4d}) | "
            f"{100 * s['delta']:+6.2f} [{100 * s['ci'][0]:+6.2f}; {100 * s['ci'][1]:+6.2f}] | {s['z']:+.2f}"
        )
    print(
        "  (poprawność kierunku wg ETYKIETY na sygnałach z label != 0; diagnostyka, nie kryterium)"
    )

    print("\n3. GEOMETRIA WYPŁATY I KOSZT (k = 1)")
    print(GEOMETRY_HEADER)
    print("  " + "-" * 104)
    _print_geometry_row("kontrola (label)", control)
    for code, w in variants.items():
        _print_geometry_row(f"{code} {w['desc']}"[:26], w)
    print(
        "  (świec = średnia liczba świec od wypełnienia do wyjścia włącznie; koszt = średni % nominału)"
    )
    for code, w in variants.items():
        print(
            f"  {code}: koszt mediana {100 * w['cost_median']:.4f}%, zwrot netto per trade średnia "
            f"{100 * w['ret_mean']:+.4f}% / mediana {100 * w['ret_median']:+.4f}%, "
            f"wypełnienie średnio po {w['fill_offset_mean']:.2f} świecy"
        )
    # Reguła 6 pre-rejestracji: lejek liczony WSPÓLNĄ bramką maker; dla W1c (noga taker na
    # wejściu) podajemy osobno, ile transakcji nie przeszłoby bramki z kosztem taker
    # (`gate_cost_fraction(taker_only)` = 0,0014) przy MIN_BARRIER_TO_COST_RATIO = 2.
    w1c = variants["W1c"]["trades"]
    real_c = w1c.loc[~w1c["kill_switch_active"]]
    taker_gate = gate_cost_fraction(EXECUTION_TAKER_ONLY)
    atr_by_ts = pd.Series(
        [s["atr_14"] for s in collected["candidate_signals"]],
        index=[s["timestamp"] for s in collected["candidate_signals"]],
    )
    barrier_frac = ATR_MULTIPLIER * real_c["timestamp"].map(atr_by_ts) / real_c["entry_price"]
    n_would_fail = int((barrier_frac < MIN_BARRIER_TO_COST_RATIO * taker_gate).sum())
    print(
        f"  W1c: transakcji, które NIE przeszłyby bramki kosztowej z nogą taker "
        f"({MIN_BARRIER_TO_COST_RATIO:.0f} x {taker_gate:.4f}): {n_would_fail} z {len(real_c)} "
        f"(diagnostyka; lejek liczony bramką maker {gate_cost_fraction(EXECUTION_MAKER_LIMIT):.4f}, wspólną)"
    )

    print(
        "\n3b. ZWROT NETTO PER TRADE — pooled t-stat / N_eff (zasada 12: statystyka nośna obok trafności)"
    )
    print(
        f"  {'wariant':>8} | {'n':>6} | {'średnia %':>10} | {'mediana %':>10} | {'std %':>8} | "
        f"{'t_stat':>7} | {'N_eff':>7} | {'t_neff':>7}"
    )
    print("  " + "-" * 86)
    for code, w in (
        ("kontrola", control),
        *((c, v) for c, v in variants.items() if not c.startswith("_")),
    ):
        pooled = w["pooled"].iloc[0]
        print(
            f"  {code:>8} | {int(pooled['n_trades']):6d} | {100 * pooled['mean_return']:+9.4f}% | "
            f"{100 * w['ret_eq_median']:+9.4f}% | {100 * pooled['std_return']:7.4f}% | "
            f"{pooled['t_stat']:+7.2f} | {pooled['n_eff']:7.0f} | {pooled['t_stat_neff']:+7.2f}"
        )
    print(
        "  (zwrot = net_pnl / equity_before, jak w `summarize_pooled_by_regime`; zwrot w % NOMINAŁU jest\n"
        "   w sekcji 3. |t| < ~2 => średni zwrot netto per trade nieodróżnialny od zera; trafność > próg NIE\n"
        "   wystarcza, gdy wypłaty nie są symetryczne ±B — np. małe wygrane na timeoutach i pełne straty na SL)"
    )

    print(
        "\n4. WRAŻLIWOŚĆ NA CZAS WAŻNOŚCI k = 2, 3 — TYLKO OPISOWO (bez trafności i werdyktu, H3/D5)"
    )
    print(GEOMETRY_HEADER)
    print("  " + "-" * 104)
    for k in SENSITIVITY_VALIDITY:
        for code, (_desc, entry_rule) in VARIANTS.items():
            w = _pack(
                _simulate(collected, fill_model=FILL_MODEL_PATH, entry_rule=entry_rule, validity=k),
                collected,
            )
            _print_geometry_row(f"{code} k={k}", w)
            w.setdefault("k", k)
            variants.setdefault("_sens", {})[(code, k)] = w

    print("\n5. MIERZALNOŚĆ ex post (zasada 18) — warianty z werdyktem")
    n_rows = sum(f["n_rows_evaluated"] for f in collected["folds_summary"] if not f["skipped"])
    n_abst = sum(
        f["n_signals_no_direction"] for f in collected["folds_summary"] if not f["skipped"]
    )
    for code, w in variants.items():
        if code.startswith("_"):
            continue
        r = measurability_report(w["p"], w["break_even"], w["n"])
        n_exp = expected_trades(n_rows, n_abst / n_rows, w["fill_rate"])
        print(
            f"  {code}: n z expected_trades(abstynencja, wypełnienia) = {n_exp:,.0f} vs journal {w['n']:,} | "
            f"pasmo {100 * wald_half_width(w['n']):.2f} pp | próg wykrywalności {100 * r['p_detectable']:.2f}% "
            f"-> {r['verdict']} | required_trades({100 * control['p']:.2f}% vs {100 * w['break_even']:.2f}%) = "
            f"{required_trades(control['p'], w['break_even']):,.0f}"
        )

    # ------------------------------------------------------------------ CZĘŚĆ B
    print("\n" + SEP)
    print("CZĘŚĆ B — KALIBRACJA: tryb 4h vs tryb 5m na oknie 2023-07 → 2026-07 (bez werdyktu)")
    print(SEP)
    cal_cfg = dict(data_cfg)
    cal_cfg["timeframe_start_overrides"] = {}  # okno 2023-07 → 2026-07, wspólne dla 4h i 5m
    df_cal = fetch_native(cal_cfg, TIMEFRAME)
    df_5m = fetch_native(cal_cfg, INTRABAR_TIMEFRAME)
    print(
        f"  4h: {len(df_cal)} świec, 5m: {len(df_5m)} świec, {df_cal['timestamp'].min()} -> {df_cal['timestamp'].max()}"
    )
    # zgodność agregatu 5m z natywnymi 4h (kontrola danych; jedna świeca niezgodna — znana z pre-rejestracji)
    agg = (
        df_5m.assign(b=df_5m["timestamp"].dt.floor("4h"))
        .groupby("b")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
        )
    )
    m = df_cal.set_index("timestamp").join(agg, rsuffix="_5m", how="inner")
    bad = m.index[
        (
            m[["open", "high", "low", "close"]].to_numpy()
            != m[["open_5m", "high_5m", "low_5m", "close_5m"]].to_numpy()
        ).any(axis=1)
    ]
    print(f"  świec 4h niezgodnych z agregatem 5m: {len(bad)} -> {[str(x) for x in bad]}")

    collected_cal = _collect(df_cal, rule)
    print(f"  trening (okno kalibracyjne) zakończony po {time.time() - t0:.0f} s")
    _print_funnel(collected_cal)
    print(
        f"\n  {'wariant':>6} | {'tryb':>8} | {'n':>5} | {'niewyp.':>7} | {'tp/sl/timeout %':>17} | {'bariera B':>9} | {'koszt C':>8} | {'próg BE':>7} | zgodność z trybem 4h"
    )
    print("  " + "-" * 118)
    calib = {}
    for code, (_desc, entry_rule) in VARIANTS.items():
        bar = _pack(
            _simulate(collected_cal, fill_model=FILL_MODEL_PATH, entry_rule=entry_rule),
            collected_cal,
        )
        fine = _pack(
            _simulate(
                collected_cal, fill_model=FILL_MODEL_PATH, entry_rule=entry_rule, intrabar=df_5m
            ),
            collected_cal,
        )
        calib[code] = (bar, fine)
        tb = bar["trades"].loc[~bar["trades"]["kill_switch_active"]].set_index("timestamp")
        tf = fine["trades"].loc[~fine["trades"]["kill_switch_active"]].set_index("timestamp")
        both = tb.join(tf, lsuffix="_4h", rsuffix="_5m", how="inner")
        only_bar, only_fine = len(tb.index.difference(tf.index)), len(tf.index.difference(tb.index))
        same_reason = (
            float((both["exit_reason_4h"] == both["exit_reason_5m"]).mean())
            if len(both)
            else float("nan")
        )
        same_price = (
            float(np.isclose(both["exit_price_4h"], both["exit_price_5m"]).mean())
            if len(both)
            else float("nan")
        )
        same_entry = (
            float(np.isclose(both["entry_price_4h"], both["entry_price_5m"]).mean())
            if len(both)
            else float("nan")
        )
        for mode, w in (("4h", bar), ("5m", fine)):
            extra = (
                ""
                if mode == "4h"
                else (
                    f"powód wyjścia zgodny {100 * same_reason:.1f}%, cena wyjścia {100 * same_price:.1f}%, "
                    f"cena wejścia {100 * same_entry:.1f}%; tylko 4h {only_bar}, tylko 5m {only_fine}"
                )
            )
            print(
                f"  {code:>6} | {mode:>8} | {w['n']:5d} | {w['n_unfilled']:7d} | "
                f"{100 * w['share'][EXIT_REASON_TP]:5.1f}/{100 * w['share'][EXIT_REASON_SL]:5.1f}/{100 * w['share'][EXIT_REASON_TIMEOUT]:5.1f} | "
                f"{100 * w['barrier']:8.4f}% | {100 * w['cost']:7.4f}% | {100 * w['break_even']:6.2f}% | {extra}"
            )
        # kierunek obciążenia trybu 4h (na tych samych transakcjach): zmiana powodu wyjścia
        if len(both):
            cross = pd.crosstab(both["exit_reason_4h"], both["exit_reason_5m"])
            print("  macierz powodów wyjścia (wiersze: tryb 4h, kolumny: tryb 5m):")
            print("  " + cross.to_string().replace("\n", "\n  "))

    print("\n" + SEP)
    print("6. POZA DECYZJĄ (H3/D5) — trafność w części kalibracyjnej i przy k = 2, 3; pełne tabele")
    print(SEP)
    print(
        "  Liczby poniżej NIE uczestniczą w werdykcie rundy (pre-rejestracja: „Czego runda NIE raportuje”)."
    )
    for code, (bar, fine) in calib.items():
        for mode, w in (("4h", bar), ("5m", fine)):
            print(
                f"  kalibracja {code} {mode}: n={w['n']}, p={100 * w['p']:.2f}% [{100 * w['ci_low']:.2f}; {100 * w['ci_high']:.2f}], BE={100 * w['break_even']:.2f}%"
            )
    for (code, k), w in variants.get("_sens", {}).items():
        print(
            f"  k={k} {code}: n={w['n']}, p={100 * w['p']:.2f}% [{100 * w['ci_low']:.2f}; {100 * w['ci_high']:.2f}], BE={100 * w['break_even']:.2f}%"
        )
    print()
    for code, w in (
        ("kontrola", control),
        *((c, v) for c, v in variants.items() if not c.startswith("_")),
    ):
        print(f"  --- {code} ---")
        print("  " + w["edge"].to_string(index=False).replace("\n", "\n  "))
        print("  " + str(w["classification"]))
        print("  UWAGA: `classification` NIE jest kryterium (wniosek skumulowany 24).")
    print(f"\n  czas całkowity: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
