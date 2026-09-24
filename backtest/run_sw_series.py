"""
run_sw_series.py — seria SW (cechy spoza wykresu, 2026-09-24). Trzy tryby:

    PYTHONUTF8=1 py -m backtest.run_sw_series profil   # cechy bez celu: braki, masa, korelacje, mierzalność
    PYTHONUTF8=1 py -m backtest.run_sw_series etap1    # 8 reguł bez modelu (każda cecha osobno)
    PYTHONUTF8=1 py -m backtest.run_sw_series etap2    # jeden model XGBoost ze wszystkimi cechami, okno 365 dni

Konfiguracja ZAMROŻONA w `runs/2026-09-24_sw-cechy-spoza-wykresu/README.md` (pre-rejestracja przed
trybami etap1/etap2). Silnik kanoniczny jak A1/O1: `collect_signals` + `simulate_equity` (4h, V = 3,
wejście limit po close, wypełnienia po ścieżce, pojedyncze wyjście), `build_rule_signals` dla reguł.
Neutralny reporter: drukuje odczyt kryterium; werdykt podpisuje Claude w README serii.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from agents.ml_optimizer import REVERSION_FEATURES
from agents.sw_features import SW_FEATURES, build_sw_frame, rule_score
from backtest.checkpoint_lib import (
    PRIMARY_SEED,
    build_rule_signals,
    fetch_window,
    load_config,
    summarize_result,
    summarize_trade_returns,
)
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule
from backtest.metrics import expected_trades, measurability_report
from data.fetch_funding import get_funding_rate_history_cached

# --- konfiguracja ZAMROŻONA --------------------------------------------------------------------
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
RULE_TRAIN_DAYS = 60  # etap 1: populacja reguły = okna testowe potoku kontrolnego (jak A1)
MODEL_TRAIN_DAYS = 365  # etap 2: okno uczenia (AU1: 60 dni gubi słabą cechę, 365 ją widzi)
TEST_DAYS = 28
STEP_DAYS = 28
CONTROL_FEATURES = list(REVERSION_FEATURES)
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1
M_SERIES = 9  # 8 reguł + 1 model: Bonferroni dla całej serii
Z_STAR = float(norm.ppf(1 - 0.05 / (2 * M_SERIES)))  # 2,773
DEDUP_ABS_RHO = 0.9  # etap 2: |Spearman| > 0,9 na pierwszym oknie uczenia → odpada cecha późniejsza
MODEL_EXCLUDED = {
    "toptrader_ls_log": "dziura w archiwum 2021-12 → 2022-12 (silnik odrzuca wiersze z NaN)"
}
# --- liczby odniesienia (ex ante) --------------------------------------------------------------
N1_CONTROL_REF = {"n": 6789, "p": 0.4958, "r_mean": -0.001069, "se": 0.000214}
ABSTENTION_REF = 0.4038
FILL_RATE_REF = 0.994
BE_REF = 0.5307
RULE_EFFECT_HYP = (
    0.0020  # AU1: wyrocznia q = 0,2 jako reguła = +0,20 %/tr (strefa ślepa modelu 60 dni)
)
RULE_P_HYP = 0.5528
MODEL_EFFECT_HYP = 0.0010  # AU1: ta sama wyrocznia w modelu z oknem 365 dni = +0,10 %/tr
Z_POWER80 = 0.8416
SEP = "=" * 110


def _load() -> pd.DataFrame:
    cfg = load_config()["data"]
    df = fetch_window(cfg, TIMEFRAME)
    funding = get_funding_rate_history_cached(
        symbol=cfg["primary_symbol"],
        start=(cfg.get("timeframe_start_overrides") or {}).get("4h", cfg["start"]),
        end=cfg["end"],
        cache_dir=cfg["cache_dir"],
        exchange_id=cfg["exchange_id"],
    )
    sw = build_sw_frame(df, funding)
    for name, (sign, _) in SW_FEATURES.items():
        sw[f"score_{name}"] = rule_score(sw[name], sign)
    return sw


def _collect(df: pd.DataFrame, features: list[str], train_days: int, rule: dict) -> dict:
    return collect_signals(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, features)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        train_days=train_days,
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


def _ci_p(w: dict, z: float) -> tuple[float, float]:
    half = z * np.sqrt(w["p"] * (1 - w["p"]) / max(w["n"], 1))
    return w["p"] - half, w["p"] + half


def _verdict(w: dict) -> str:
    lo, _ = _ci_p(w, Z_STAR)
    if w["t_neff"] > Z_STAR and lo > w["p_star"]:
        return f"POZYTYWNY — t_neff > {Z_STAR:.3f} i ci_low*(p) > p*. NAJPIERW SZUKAJ PRZECIEKU"
    if w["t_neff"] < -Z_STAR:
        return f"NEGATYWNY — t_neff < −{Z_STAR:.3f} (reguła/model traci istotnie; odwrócenie znaku = nowa hipoteza)"
    return f"NIEROZSTRZYGNIĘTY — |t_neff| < {Z_STAR:.3f} albo ci_low*(p) <= p*"


def _header() -> str:
    return (
        f"  {'ramię':>22} | {'n':>5} | {'r̄ netto':>9} | {'CI 95%':>21} | {'mediana':>8} | "
        f"{'t_neff':>6} | {'N_eff':>6} | {'p':>7} | {'CI*(p)':>17} | {'p*':>6}"
    )


def _row(name: str, w: dict) -> str:
    half = 1.959964 * w["se"]
    lo, hi = _ci_p(w, Z_STAR)
    return (
        f"  {name:>22} | {w['n']:5d} | {100 * w['r_mean']:+8.4f}% | "
        f"[{100 * (w['r_mean'] - half):+8.4f}; {100 * (w['r_mean'] + half):+8.4f}] | "
        f"{100 * w['r_median']:+7.4f}% | {w['t_neff']:+6.2f} | {w['n_eff']:6.0f} | "
        f"{100 * w['p']:6.2f}% | [{100 * lo:6.2f}; {100 * hi:6.2f}] | {100 * w['p_star']:5.2f}%"
    )


def _se_at(n: float) -> float:
    return N1_CONTROL_REF["se"] * np.sqrt(N1_CONTROL_REF["n"] / max(n, 1.0))


# ------------------------------------------------------------------ profil (bez celu)
def profil() -> None:
    sw = _load()
    ts = sw["timestamp"]
    print(SEP)
    print("SW — PROFIL CECH (bez celu i bez zwrotów przyszłych); dane od", ts.min(), "do", ts.max())
    print(SEP)
    print(f"świec 4h: {len(sw)}; próg serii: Bonferroni m = {M_SERIES} → z* = {Z_STAR:.3f}")
    print("\n1. Cechy: dostępność, masa punktowa, rozkład")
    print(
        f"  {'cecha':>20} | {'znak':>4} | {'braki':>6} | {'1. wartość':>16} | {'masa':>6} | "
        f"{'p01':>9} | {'p50':>9} | {'p99':>9} | {'acf1':>6}"
    )
    for name, (sign, _) in SW_FEATURES.items():
        x = sw[name]
        mass = float(x.round(8).value_counts(normalize=True).iloc[0]) if x.notna().any() else np.nan
        first = x.first_valid_index()
        print(
            f"  {name:>20} | {sign:+4d} | {100 * x.isna().mean():5.1f}% | "
            f"{str(ts.loc[first])[:16] if first is not None else '—':>16} | {100 * mass:5.1f}% | "
            f"{x.quantile(0.01):+9.4f} | {x.median():+9.4f} | {x.quantile(0.99):+9.4f} | {x.autocorr(1):+6.3f}"
        )
    print("\n2. Reguła etapu 1: udział świec z kierunkiem (znak × sign(cecha − mediana 365 dni))")
    oos_start = ts.min() + pd.Timedelta(days=RULE_TRAIN_DAYS)
    oos = ts >= oos_start
    n_oos = int(oos.sum())
    print(f"  świece w oknach testowych potoku kontrolnego (od {oos_start.date()}): {n_oos}")
    print(
        f"  {'cecha':>20} | {'z kierunkiem':>12} | {'long':>6} | {'short':>6} | {'zero':>5} | "
        f"{'n oczek.':>8} | {'mierzalność (trafność)':>28} | {'SE r̄':>7} | {'t hip.':>6} | werdykt"
    )
    for name in SW_FEATURES:
        s = sw.loc[oos, f"score_{name}"]
        n_dir = int((s.fillna(0) != 0).sum())
        n_exp = expected_trades(n_dir, 0.0, FILL_RATE_REF)
        rep = measurability_report(RULE_P_HYP, BE_REF, n_exp)
        se = _se_at(n_exp)
        t_h = RULE_EFFECT_HYP / se
        ok = "MIERZALNA" if (rep["measurable"] and t_h >= Z_STAR + Z_POWER80) else "NIEMIERZALNA"
        print(
            f"  {name:>20} | {n_dir:12d} | {int((s > 0).sum()):6d} | {int((s < 0).sum()):6d} | "
            f"{int((s == 0).sum()):5d} | {n_exp:8.0f} | {rep['verdict']:>11} pasmo {rep['band_width_pp']:4.2f} pp "
            f"| {100 * se:6.4f}% | {t_h:6.2f} | {ok}"
        )
    print(
        f"  hipoteza efektu: reguła +{100 * RULE_EFFECT_HYP:.2f} %/tr (trafność {100 * RULE_P_HYP:.2f} %, AU1 q = 0,2); "
        f"SE r̄ skalowane z kontroli N1 ({100 * N1_CONTROL_REF['se']:.4f} % przy n {N1_CONTROL_REF['n']}); "
        f"MIERZALNA = trafność mierzalna i t_hip ≥ z* + 0,84 (moc 80 %)"
    )
    print("\n3. Korelacje MIĘDZY cechami (Spearman), cały okres")
    feats = list(SW_FEATURES)
    print(sw[feats].corr(method="spearman").round(2).to_string())
    first_window = ts < ts.min() + pd.Timedelta(days=MODEL_TRAIN_DAYS)
    rho = sw.loc[first_window, feats].corr(method="spearman")
    print(
        f"\n4. Etap 2 — usuwanie duplikatów na PIERWSZYM oknie uczenia ({ts.min().date()} + 365 dni), |ρ| > {DEDUP_ABS_RHO}"
    )
    print(rho.round(2).to_string())
    kept = []
    for f in feats:
        if f in MODEL_EXCLUDED:
            print(f"  {f}: WYŁĄCZONA z modelu — {MODEL_EXCLUDED[f]}")
            continue
        dup = [k for k in kept if abs(rho.loc[f, k]) > DEDUP_ABS_RHO]
        if dup:
            print(f"  {f}: duplikat {dup} → odpada")
        else:
            kept.append(f)
    print(f"  cechy modelu etapu 2: {kept}")
    rows = sw[kept].notna().all(axis=1)
    first_ok = sw.loc[rows, "timestamp"].min()
    test_start = first_ok + pd.Timedelta(days=MODEL_TRAIN_DAYS)
    n_rows_oos = int((rows & (ts >= test_start)).sum())
    n_exp2 = expected_trades(n_rows_oos, ABSTENTION_REF, FILL_RATE_REF)
    se2 = _se_at(n_exp2)
    t2 = MODEL_EFFECT_HYP / se2
    rep2 = measurability_report(0.5293, BE_REF, n_exp2)
    print(
        f"  pierwsza świeca z kompletem cech: {first_ok}; pierwszy test: {test_start.date()}; świec OOS {n_rows_oos}; "
        f"n oczekiwane = {n_exp2:.0f} (abstynencja {100 * ABSTENTION_REF:.1f} %, wypełnienia {100 * FILL_RATE_REF:.1f} %)\n"
        f"  hipoteza efektu modelu +{100 * MODEL_EFFECT_HYP:.2f} %/tr (AU1: q = 0,2 w oknie 365 dni); SE r̄ {100 * se2:.4f} %; "
        f"t_hip {t2:.2f} vs z* + 0,84 = {Z_STAR + Z_POWER80:.2f} → "
        f"{'MIERZALNA' if t2 >= Z_STAR + Z_POWER80 else 'NIEMIERZALNA'} (zwrot); trafność: {rep2['verdict']} "
        f"(52,93 % wobec progu ±B {100 * BE_REF:.2f} % — próg ±B diagnostyczny, kryterium to p* i zwrot)"
    )
    print(SEP)


# ------------------------------------------------------------------ etap 1
def etap1() -> None:
    t0 = time.time()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    sw = _load()
    print(SEP)
    print(
        f"SW ETAP 1 — 8 reguł bez modelu; kryterium z* = {Z_STAR:.3f} (Bonferroni m = {M_SERIES}); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    control_c = _collect(sw, CONTROL_FEATURES, RULE_TRAIN_DAYS, rule)
    fdf = control_c["df"]
    folds = control_c["folds_summary"]
    print(
        f"  potok kontrolny: {sum(not f['skipped'] for f in folds)} aktywnych foldów; trening {time.time() - t0:.0f} s"
    )
    control = _simulate(fdf, control_c["candidate_signals"], folds)
    ok = (
        control["n"] == N1_CONTROL_REF["n"]
        and abs(control["p"] - N1_CONTROL_REF["p"]) < 5e-4
        and abs(control["r_mean"] - N1_CONTROL_REF["r_mean"]) < 2e-5
    )
    print(_header())
    print(_row("kontrola (N1)", control) + f"  regresja: {'ZGODNA' if ok else 'ROZJAZD'}")
    results = {}
    for name, (sign, _why) in SW_FEATURES.items():
        signals, funnel = build_rule_signals(fdf, folds, f"score_{name}")
        w = _simulate(fdf, signals, folds)
        results[name] = (w, funnel, signals)
        print(_row(f"{name} ({sign:+d})", w))
    print(
        "\n  lejek reguł (świece w oknach OOS / bez kierunku / bez etykiety / bramka kosztowa / sygnały):"
    )
    for name, (_w, f, s) in results.items():
        print(
            f"  {name:>22}: {f['n_rows_window']} / {f['n_no_signal']} / {f['n_label_nan']} / {f['n_cost_gated']} / "
            f"{f['n_signals']} (long {sum(x['signal_direction'] > 0 for x in s)}, short {sum(x['signal_direction'] < 0 for x in s)})"
        )
    print("\n  >>> ODCZYT KRYTERIUM (z* dla serii):")
    for name, (w, _, _) in results.items():
        print(f"  {name:>22}: {_verdict(w)}")
    print(SEP)


# ------------------------------------------------------------------ etap 2
def etap2() -> None:
    t0 = time.time()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    sw = _load()
    ts = sw["timestamp"]
    feats = [f for f in SW_FEATURES if f not in MODEL_EXCLUDED]
    rho = sw.loc[ts < ts.min() + pd.Timedelta(days=MODEL_TRAIN_DAYS), feats].corr(method="spearman")
    kept = []
    for f in feats:
        if not any(abs(rho.loc[f, k]) > DEDUP_ABS_RHO for k in kept):
            kept.append(f)
    print(SEP)
    print(
        f"SW ETAP 2 — jeden model XGBoost, cechy {kept}; okno {MODEL_TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}; z* = {Z_STAR:.3f}"
    )
    print(SEP)
    model_c = _collect(sw, kept, MODEL_TRAIN_DAYS, rule)
    print(f"  trening modelu: {time.time() - t0:.0f} s")
    control_c = _collect(
        sw.dropna(subset=kept).reset_index(drop=True), CONTROL_FEATURES, MODEL_TRAIN_DAYS, rule
    )
    print(f"  trening kontroli (4 cechy wykresu, te same świece): {time.time() - t0:.0f} s")
    for name, c in (("model SW", model_c), ("kontrola", control_c)):
        active = [f for f in c["folds_summary"] if not f["skipped"]]
        n_rows = sum(f["n_rows_evaluated"] for f in active)
        n_abst = sum(f["n_signals_no_direction"] for f in active)
        print(
            f"  [{name}] foldy aktywne {len(active)}/{len(c['folds_summary'])}; świece ocenione {n_rows}; "
            f"abstynencja {100 * n_abst / max(n_rows, 1):.1f} %; pierwszy test {min(f['test_start'] for f in active)}"
        )
    model = _simulate(model_c["df"], model_c["candidate_signals"], model_c["folds_summary"])
    control = _simulate(control_c["df"], control_c["candidate_signals"], control_c["folds_summary"])
    print(_header())
    print(_row("model SW", model))
    print(_row("kontrola 365 (opis)", control))
    print(f"\n  >>> ODCZYT KRYTERIUM model SW: {_verdict(model)}")
    print(SEP)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "profil"
    {"profil": profil, "etap1": etap1, "etap2": etap2}[mode]()
