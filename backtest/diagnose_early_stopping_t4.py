"""
diagnose_early_stopping_t4.py

T4 — czy early stopping na malych oknach 4h wybiera liczbe drzew z sygnalu, czy z szumu.
Skrypt jednorazowy/analityczny (zasada 13). Pre-rejestracja w OSOBNYM commicie PRZED kodem:
`runs/2026-09-23_t4-kalibracja-early-stopping/README.md`.

Zasada konstrukcji: liczymy WYLACZNIE na danych treningowych kazdego okna walk-forward
(zagniezdzony podzial). Etykiety okien testowych nie sa czytane; `run_and_summarize` nie
jest wolane, journal transakcji nie jest drukowany ani analizowany. Przebieg produkcyjny
sluzy tylko do przechwycenia DOKLADNIE tego `train_df`, ktory silnik podaje do
`train_regime_model` (opakowanie funkcji, nie kopia logiki silnika).

Uzycie:
    py -m backtest.diagnose_early_stopping_t4
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb
import yaml
from scipy import stats

import backtest.engine as engine
from agents.ml_optimizer import (
    DEFAULT_VALIDATION_FRACTION,
    DEFAULT_XGB_PARAMS,
    EARLY_STOPPING_ROUNDS,
    LABEL_TO_CLASS,
    MIN_VALIDATION_ROWS,
    NUM_BOOST_ROUND,
    REVERSION_FEATURES,
    class_weight_map,
)
from backtest.checkpoint_lib import PRIMARY_SEED
from backtest.diagnose_timeframe_geometry import _load, _load_cfg

# --- KONFIGURACJA ZAMROZONA (ramie A z F1 / K3-C2) ---
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
FEATURES = REVERSION_FEATURES

FRACTIONS = (0.1, 0.2, 0.3)  # D3 — obserwacja, nie wybor
PRIMARY_FRACTION = 0.2  # D1 — miara glowna (= wartosc produkcyjna)
FIXED_TREES = (1, 10, 50, NUM_BOOST_ROUND)
TIMEOUT_CLASS = LABEL_TO_CLASS[0.0]

SEP = "=" * 100


def split_sizes(n: int, fraction: float) -> tuple[int, int, bool]:
    """(n_fit, n_val, czy max() zmienil n_val) — ta sama regula co `train_regime_model`."""
    by_fraction = int(round(n * fraction))
    n_val = max(MIN_VALIDATION_ROWS, by_fraction)
    return n - n_val, n_val, n_val != by_fraction


def early_stopping_pick(val_curve: np.ndarray, patience: int = EARLY_STOPPING_ROUNDS) -> int:
    """Indeks drzewa, ktory wybralby early stopping XGBoost (strict `<`, stop po `patience`)."""
    best = 0
    for i in range(1, len(val_curve)):
        if val_curve[i] < val_curve[best]:
            best = i
        if i - best >= patience:
            break
    return best


def _classes(frame: pd.DataFrame) -> np.ndarray:
    return frame["label"].map(LABEL_TO_CLASS).to_numpy(dtype=np.int32)


def _dmatrix(frame: pd.DataFrame, weight_map: dict[int, float]) -> xgb.DMatrix:
    labels = _classes(frame)
    weights = np.array([weight_map.get(int(c), 1.0) for c in labels], dtype=np.float32)
    return xgb.DMatrix(frame[FEATURES], label=labels, weight=weights)


def curves(fit: pd.DataFrame, evals: dict[str, pd.DataFrame]) -> tuple[xgb.Booster, dict]:
    """Pelne 200 rund na `fit`, krzywe WAZONEGO mlogloss na kazdym zbiorze z `evals`."""
    weight_map = class_weight_map(_classes(fit), "balanced")
    history: dict = {}
    booster = xgb.train(
        {**DEFAULT_XGB_PARAMS, "seed": PRIMARY_SEED},
        _dmatrix(fit, weight_map),
        num_boost_round=NUM_BOOST_ROUND,
        evals=[(_dmatrix(frame, weight_map), name) for name, frame in evals.items()],
        evals_result=history,
        verbose_eval=False,
    )
    return booster, {k: np.asarray(v["mlogloss"]) for k, v in history.items()}


def abstention(booster: xgb.Booster, frame: pd.DataFrame, n_trees: int) -> float:
    proba = booster.predict(xgb.DMatrix(frame[FEATURES]), iteration_range=(0, n_trees))
    return float(np.mean(np.argmax(proba, axis=1) == TIMEOUT_CLASS))


def mean_ci(x: np.ndarray) -> tuple[float, float, float, float]:
    """(srednia, mediana, ci_low, ci_high) — 95% CI t-Studenta po oknach."""
    x = np.asarray(x, dtype=float)
    half = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return float(x.mean()), float(np.median(x)), float(x.mean() - half), float(x.mean() + half)


def capture_training_frames(df: pd.DataFrame, rule: dict) -> tuple[list[pd.DataFrame], list[dict]]:
    captured: list[pd.DataFrame] = []
    original = engine.train_regime_model

    def spy(train_df, test_df, *args, **kwargs):
        # test_df przechodzi dalej nietkniety — diagnostyka go nie zapisuje.
        captured.append(train_df.copy())
        return original(train_df, test_df, *args, **kwargs)

    engine.train_regime_model = spy
    try:
        result = engine.run_backtest(
            df,
            seed=PRIMARY_SEED,
            regime_feature_sets=[(engine.REGIME_ALL, FEATURES)],
            vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
            candles_per_day=CANDLES_PER_DAY,
            candle_minutes=CANDLE_MINUTES,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            trend_threshold=rule["trend_threshold"],
            range_threshold=rule["range_threshold"],
        )
    finally:
        engine.train_regime_model = original
    active = [f for f in result["folds_summary"] if not f["skipped"]]
    assert len(active) == len(captured), (len(active), len(captured))
    return captured, result["folds_summary"]


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    df = _load(cfg, TIMEFRAME)

    print(SEP)
    print("T4 — early stopping: sygnal czy szum (zagniezdzony podzial, TYLKO dane treningowe)")
    print(SEP)
    print(
        f"dane     : {len(df)} swiec {TIMEFRAME}, {df['timestamp'].min()} -> {df['timestamp'].max()}\n"
        f"pipeline : bez bramki rezimu, V={VERTICAL_BARRIER_CANDLES}, wagi `balanced`, "
        f"walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}\n"
        f"cechy    : {FEATURES}\n"
        f"produkcja: validation_fraction={DEFAULT_VALIDATION_FRACTION}, "
        f"MIN_VALIDATION_ROWS={MIN_VALIDATION_ROWS}, EARLY_STOPPING_ROUNDS={EARLY_STOPPING_ROUNDS}, "
        f"num_boost_round={NUM_BOOST_ROUND}\n"
    )

    frames, folds_summary = capture_training_frames(df, rule)
    active = [f for f in folds_summary if not f["skipped"]]

    # ---------------------------------------------------------------- D0
    rows0 = []
    for fs, train_df in zip(active, frames, strict=True):
        clean = train_df.dropna(subset=[*FEATURES, "label"]).iloc[:-VERTICAL_BARRIER_CANDLES]
        n_fit, n_val, bound = split_sizes(len(clean), DEFAULT_VALIDATION_FRACTION)
        rows0.append(
            {
                "fold": fs["fold_idx"],
                "n_clean": len(clean),
                "n_val": n_val,
                "max_binds": bound,
                "es_used": bool(fs["early_stopping_used"]),
                "trees": fs["best_iteration"] + 1,
            }
        )
    d0 = pd.DataFrame(rows0)

    print(SEP)
    print("D0 — FAKTY O KONFIGURACJI PRODUKCYJNEJ")
    print(SEP)
    print(
        f"  okna: {len(folds_summary)} wszystkie, {len(active)} aktywne, "
        f"{len(folds_summary) - len(active)} pominiete\n"
        f"  n_clean (po dropna i embargu): min {d0.n_clean.min()}, mediana {d0.n_clean.median():.0f}, "
        f"max {d0.n_clean.max()}\n"
        f"  n_val: min {d0.n_val.min()}, mediana {d0.n_val.median():.0f}, max {d0.n_val.max()}\n"
        f"  okna, w ktorych max({MIN_VALIDATION_ROWS}, .) ZMIENIA n_val: {int(d0.max_binds.sum())}/{len(d0)}\n"
        f"  okna z early stoppingiem: {int(d0.es_used.sum())}/{len(d0)}\n"
        f"  liczba drzew (best_iteration+1): min {d0.trees.min()}, kwartyle "
        f"{d0.trees.quantile(0.25):.0f}/{d0.trees.median():.0f}/{d0.trees.quantile(0.75):.0f}, "
        f"max {d0.trees.max()}\n"
        f"  okna z < 5 drzewami: {int((d0.trees < 5).sum())}/{len(d0)}; "
        f"okna z {NUM_BOOST_ROUND} drzewami: {int((d0.trees == NUM_BOOST_ROUND).sum())}/{len(d0)}"
    )
    print("\n  histogram liczby drzew:")
    bins = [0, 1, 2, 5, 10, 20, 50, 100, 199, 200]
    hist = pd.cut(d0.trees, bins=bins, right=True).value_counts().sort_index()
    for interval, count in hist.items():
        print(f"    {str(interval):>12} : {count:3d}")

    # ---------------------------------------------------------------- D1-D4
    rows = []
    replication_mismatch = 0
    for fs, train_df in zip(active, frames, strict=True):
        clean = train_df.dropna(subset=[*FEATURES, "label"]).iloc[:-VERTICAL_BARRIER_CANDLES]
        n_fit, _, _ = split_sizes(len(clean), DEFAULT_VALIDATION_FRACTION)
        outer_fit, inner_test = clean.iloc[:n_fit], clean.iloc[n_fit:]

        # Kontrola replikacji: moja rekonstrukcja decyzji produkcyjnej == folds_summary.
        _, prod_curves = curves(outer_fit, {"val": inner_test})
        if early_stopping_pick(prod_curves["val"]) != fs["best_iteration"]:
            replication_mismatch += 1

        pool = outer_fit.iloc[:-VERTICAL_BARRIER_CANDLES]  # embargo wzgledem wewnetrznego testu
        for fraction in FRACTIONS:
            n_in_fit, n_in_val, _ = split_sizes(len(pool), fraction)
            if n_in_fit < MIN_VALIDATION_ROWS:
                continue
            inner_fit, inner_val = pool.iloc[:n_in_fit], pool.iloc[n_in_fit:]
            booster, c = curves(inner_fit, {"val": inner_val, "test": inner_test})
            k_es = early_stopping_pick(c["val"])
            k_or = int(np.argmin(c["test"]))
            rec = {
                "fold": fs["fold_idx"],
                "fraction": fraction,
                "n_inner_fit": n_in_fit,
                "n_inner_val": n_in_val,
                "n_inner_test": len(inner_test),
                "trees_es": k_es + 1,
                "trees_oracle": k_or + 1,
                "L_es": c["test"][k_es],
                "L_oracle": c["test"][k_or],
                "abst_es": abstention(booster, inner_test, k_es + 1),
                "abst_200": abstention(booster, inner_test, NUM_BOOST_ROUND),
                "abst_true": float(np.mean(_classes(inner_test) == TIMEOUT_CLASS)),
            }
            for t in FIXED_TREES:
                rec[f"L_{t}"] = c["test"][t - 1]
            rows.append(rec)
    res = pd.DataFrame(rows)

    print(
        "\n  kontrola replikacji decyzji produkcyjnej (moj early stopping == silnik): "
        f"{len(active) - replication_mismatch}/{len(active)} zgodnych"
    )

    prim = res[res.fraction == PRIMARY_FRACTION].copy()
    print("\n" + SEP)
    print(
        f"D1 — MIARA GLOWNA (f={PRIMARY_FRACTION}): strata na wewnetrznym tescie, "
        "early stopping vs stala liczba drzew"
    )
    print(SEP)
    print(
        f"  okien w analizie: {len(prim)}; wewnetrzny trening mediana {prim.n_inner_fit.median():.0f}, "
        f"walidacja mediana {prim.n_inner_val.median():.0f}, test mediana {prim.n_inner_test.median():.0f}"
    )
    print(
        f"\n  {'porownanie':>28} | {'srednia':>9} | {'mediana':>9} | {'95% CI sredniej':>22} | "
        f"{'ES lepszy w':>11}"
    )
    print("  " + "-" * 92)
    for t in FIXED_TREES:
        diff = (prim.L_es - prim[f"L_{t}"]).to_numpy()
        m, med, lo, hi = mean_ci(diff)
        print(
            f"  {f'L(ES) - L({t} drzew)':>28} | {m:+9.5f} | {med:+9.5f} | "
            f"[{lo:+9.5f}; {hi:+9.5f}] | {int((diff < 0).sum()):4d}/{len(diff)}"
        )
    regret = (prim.L_es - prim.L_oracle).to_numpy()
    m, med, lo, hi = mean_ci(regret)
    print(
        f"  {'L(ES) - L(wyrocznia)':>28} | {m:+9.5f} | {med:+9.5f} | [{lo:+9.5f}; {hi:+9.5f}] | "
        "  (>=0 z konstr.)"
    )
    print(
        "\n  poziom odniesienia: srednia strata L(1 drzewo) = "
        f"{prim['L_1'].mean():.5f}, L({NUM_BOOST_ROUND}) = {prim[f'L_{NUM_BOOST_ROUND}'].mean():.5f}, "
        f"L(ES) = {prim.L_es.mean():.5f}, L(wyrocznia) = {prim.L_oracle.mean():.5f}"
    )

    print("\n" + SEP)
    print("D2 — CZY ES TRAFIA W LICZBE DRZEW NAJLEPSZA NA NIEWIDZIANYCH DANYCH")
    print(SEP)
    rho, p_rho = stats.spearmanr(prim.trees_es, prim.trees_oracle)
    print(f"  Spearman(drzewa ES, drzewa wyroczni) = {rho:+.3f} (p = {p_rho:.3f}, n = {len(prim)})")
    for col, name in (("trees_es", "ES"), ("trees_oracle", "wyrocznia")):
        s = prim[col]
        print(
            f"  {name:>10}: kwartyle {s.quantile(0.25):.0f}/{s.median():.0f}/{s.quantile(0.75):.0f}, "
            f"< 5 drzew w {int((s < 5).sum())}/{len(s)}, = {NUM_BOOST_ROUND} w "
            f"{int((s == NUM_BOOST_ROUND).sum())}/{len(s)}"
        )

    print("\n" + SEP)
    print("D3 — WRAZLIWOSC NA validation_fraction (OBSERWACJA, nie wybor)")
    print(SEP)
    print(
        f"  {'f':>5} | {'okien':>5} | {'n_val med':>9} | {'drzewa ES med':>13} | "
        f"{'L(ES)-L(200) sr.':>16} | {'95% CI':>22} | {'L(ES)-L(wyr.) sr.':>17}"
    )
    for fraction in FRACTIONS:
        sub = res[res.fraction == fraction]
        m, _, lo, hi = mean_ci((sub.L_es - sub[f"L_{NUM_BOOST_ROUND}"]).to_numpy())
        print(
            f"  {fraction:5.1f} | {len(sub):5d} | {sub.n_inner_val.median():9.0f} | "
            f"{sub.trees_es.median():13.0f} | {m:+16.5f} | [{lo:+9.5f}; {hi:+9.5f}] | "
            f"{(sub.L_es - sub.L_oracle).mean():+17.5f}"
        )

    print("\n" + SEP)
    print(
        f"D4 — ABSTYNENCJA na wewnetrznym tescie (f={PRIMARY_FRACTION}): udzial przewidywan 'timeout'"
    )
    print(SEP)
    m_es, _, lo_es, hi_es = mean_ci(prim.abst_es.to_numpy())
    m_200, _, lo_200, hi_200 = mean_ci(prim.abst_200.to_numpy())
    m_d, med_d, lo_d, hi_d = mean_ci((prim.abst_es - prim.abst_200).to_numpy())
    print(f"  przy ES          : {100 * m_es:6.2f}%  CI [{100 * lo_es:.2f}%; {100 * hi_es:.2f}%]")
    print(
        f"  przy {NUM_BOOST_ROUND} drzewach : {100 * m_200:6.2f}%  CI [{100 * lo_200:.2f}%; {100 * hi_200:.2f}%]"
    )
    print(
        f"  roznica ES - 200 : {100 * m_d:+6.2f} pp (mediana {100 * med_d:+.2f}), "
        f"CI [{100 * lo_d:+.2f}; {100 * hi_d:+.2f}] pp"
    )
    print(
        f"  (faktyczny udzial etykiety 'timeout' w wewnetrznym tescie: {100 * prim.abst_true.mean():.2f}%)"
    )

    print("\n" + SEP)
    print("TABELA PER OKNO (f=0.2)")
    print(SEP)
    cols = [
        "fold",
        "n_inner_fit",
        "n_inner_val",
        "n_inner_test",
        "trees_es",
        "trees_oracle",
        "L_es",
        "L_oracle",
        "L_1",
        f"L_{NUM_BOOST_ROUND}",
        "abst_es",
        "abst_200",
    ]
    with pd.option_context("display.width", 200, "display.max_rows", 500):
        print(prim[cols].round(5).to_string(index=False))


if __name__ == "__main__":
    main()
