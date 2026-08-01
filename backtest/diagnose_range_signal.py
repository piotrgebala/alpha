"""
diagnose_range_signal.py

Commit 2b (post-Commit-6 NO-GO, IMPLEMENTATION_PLAN.md §5) — diagnostyka C2b.1: dlaczego
model_reversion (regime="range") wygenerował sygnał (signal_direction != 0) tylko w 1/20
foldów walk-forward na realnych danych (Commit 6). Skrypt analityczny, POZA pytest (jak
backtest/run_checkpoint.py) — celowo READ-ONLY, nie zmienia żadnego już scalonego pliku
pipeline'u (agents/, backtest/engine.py), tylko go importuje i raportuje.

Nie duplikuje backtest.engine._collect_candidate_signals 1:1, bo ta funkcja odrzuca wiersze
z signal_direction == 0.0 PRZED zwróceniem wyniku — dokładnie ta informacja (jak wygląda
PEŁNY rozkład predict_proba, nie tylko przypadki, gdzie model faktycznie zasygnalizował)
jest tu potrzebna do diagnozy.

Per fold reżimu "range", raportuje:
  1. Rozkład klas triple-barrier label {-1.0, 0.0, 1.0} w train_df i test_df — czy problem
     to strukturalny brak zdarzeń +1/-1 w danych (regime "range" = niska zmienność z
     definicji -> bariera 1.5xATR rzadko trafiona w 12 świec), niezależnie od cech.
  2. Feature importance wytrenowanego modelu (booster.get_score(importance_type="gain")) —
     czy istniejące cechy (rsi_14, price_zscore_20, return_lag_1, volume_zscore_20) w ogóle
     coś różnicują, czy model ich nie używa.
  3. Rozkład signal_confidence (predict_proba argmax) na PEŁNYM test_df (nie tylko
     wierszach z direction != 0) — czy model jest permanentnie "pewny" klasy 0, czy to
     marginalny argmax blisko remisu z inną klasą.

Interpretacja (decision gate, nie zakodowana tutaj jako automatyczna decyzja — patrz
IMPLEMENTATION_PLAN.md §5 "Commit 2b"):
  - Jeśli train/test label dist jest ~all class 0 NIEZALEŻNIE od foldu -> strukturalny
    problem regime/bariery, nowe cechy prawdopodobnie nie pomogą (poza zakresem tej sesji:
    progi regime i mnożnik ATR zostają bez zmian).
  - Jeśli labels są sensownie rozłożone, ale feature importance ~0 dla wszystkich cech ->
    brakuje separacji w istniejącym zestawie cech -> kandydat na C2b.2 (nowa cecha).

Użycie:
    py -m backtest.diagnose_range_signal
"""

from __future__ import annotations

import pandas as pd
import yaml

from agents.feature_miner import compute_all_features
from agents.labeling import compute_triple_barrier_labels, generate_walk_forward_folds
from agents.ml_optimizer import DEFAULT_SEED, REVERSION_FEATURES, predict_signal, train_regime_model
from backtest.engine import MIN_TRAIN_ROWS
from data.fetch_ohlcv import get_ohlcv_cached

REGIME_NAME = "range"


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fetch_data(cfg: dict) -> pd.DataFrame:
    data_cfg = cfg["data"]
    return get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=data_cfg["timeframe"],
        start=data_cfg["start"],
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )


def _label_distribution(label_series: pd.Series) -> dict:
    """% udział każdej klasy triple-barrier w danej serii (train albo test danego foldu)."""
    counts = label_series.value_counts(dropna=True).to_dict()
    total = sum(counts.values())
    if total == 0:
        return {"n": 0, "pct_0": None, "pct_plus1": None, "pct_minus1": None}
    return {
        "n": total,
        "pct_0": round(100 * counts.get(0.0, 0) / total, 1),
        "pct_plus1": round(100 * counts.get(1.0, 0) / total, 1),
        "pct_minus1": round(100 * counts.get(-1.0, 0) / total, 1),
    }


def diagnose(df: pd.DataFrame, seed: int = DEFAULT_SEED) -> list[dict]:
    """
    Powtarza dokładnie split reżimu + generację foldów z backtest.engine (ta sama funkcja,
    te same domyślne train/test/step_days), ale trenuje/predykuje tutaj bezpośrednio, żeby
    mieć dostęp do boostera (feature importance) i pełnego rozkładu predict_proba.
    """
    regime_df = df[df["regime"] == REGIME_NAME]
    folds = generate_walk_forward_folds(regime_df)

    reports: list[dict] = []
    for fold_idx, fold in enumerate(folds):
        train_df = regime_df[fold["train_mask"]]
        test_df = regime_df[fold["test_mask"]]

        train_clean = train_df.dropna(subset=[*REVERSION_FEATURES, "label"])
        test_clean = test_df.dropna(subset=[*REVERSION_FEATURES, "label"])

        report: dict = {
            "fold_idx": fold_idx,
            "test_start": fold["test_start"],
            "test_end": fold["test_end"],
            "n_train_valid": len(train_clean),
            "n_test_valid": len(test_clean),
            "train_label_dist": _label_distribution(train_clean["label"]),
            "test_label_dist": _label_distribution(test_clean["label"]),
        }

        if len(train_clean) < MIN_TRAIN_ROWS or len(test_clean) < MIN_TRAIN_ROWS:
            report["skipped"] = True
            reports.append(report)
            continue

        booster = train_regime_model(train_df, test_df, REVERSION_FEATURES, seed=seed)
        signals = predict_signal(booster, test_df, REVERSION_FEATURES)

        # Matchuje dokładnie, co backtest.engine._collect_candidate_signals liczyłoby jako
        # "n_signals" (wymaga też niepustego label, nie tylko cech) — porównywalne 1:1 z
        # folds_summary z Commitu 6.
        signals_with_label = signals.join(test_df[["label"]])
        signals_valid = signals_with_label.dropna(subset=["label"])
        n_signals_nonzero = int((signals_valid["signal_direction"] != 0.0).sum())

        importance = booster.get_score(importance_type="gain")
        importance_full = {f: round(importance.get(f, 0.0), 4) for f in REVERSION_FEATURES}

        confidence_by_direction = (
            signals.groupby("signal_direction")["signal_confidence"]
            .agg(["count", "mean"])
            .round(4)
            .to_dict(orient="index")
        )

        report.update(
            {
                "skipped": False,
                "best_iteration": booster.best_iteration,
                "feature_importance_gain": importance_full,
                "n_signals_nonzero": n_signals_nonzero,
                "n_test_with_label": len(signals_valid),
                "confidence_by_direction": confidence_by_direction,
            }
        )
        reports.append(report)

    return reports


def _print_report(reports: list[dict]) -> None:
    n_evaluated = sum(1 for r in reports if not r["skipped"])
    print(f"[diagnose_range_signal] regime={REGIME_NAME!r}: {len(reports)} folds total, "
          f"{n_evaluated} evaluated (not skipped by MIN_TRAIN_ROWS={MIN_TRAIN_ROWS})\n")

    for r in reports:
        print(f"--- fold {r['fold_idx']} ({r['test_start']} -> {r['test_end']}) ---")
        print(f"  n_train_valid={r['n_train_valid']}  n_test_valid={r['n_test_valid']}")
        print(f"  train label dist: {r['train_label_dist']}")
        print(f"  test  label dist: {r['test_label_dist']}")
        if r["skipped"]:
            print("  SKIPPED (< MIN_TRAIN_ROWS)\n")
            continue
        print(f"  feature importance (gain): {r['feature_importance_gain']}")
        print(f"  n_signals_nonzero={r['n_signals_nonzero']} / n_test_with_label={r['n_test_with_label']}")
        print(f"  confidence by direction {{direction: {{count, mean}}}}: {r['confidence_by_direction']}")
        print()

    # Zagregowany sygnał do decision gate (opisowy, nie automatyczna decyzja).
    evaluated = [r for r in reports if not r["skipped"]]
    if evaluated:
        avg_pct_0_test = sum(r["test_label_dist"]["pct_0"] for r in evaluated) / len(evaluated)
        total_signals = sum(r["n_signals_nonzero"] for r in evaluated)
        total_test_rows = sum(r["n_test_with_label"] for r in evaluated)
        max_importance_per_feature = {
            f: max(r["feature_importance_gain"][f] for r in evaluated) for f in REVERSION_FEATURES
        }
        print("=== SUMMARY (decision gate input, IMPLEMENTATION_PLAN.md §5 Commit 2b) ===")
        print(f"  evaluated folds: {len(evaluated)}/{len(reports)}")
        print(f"  avg %% test labels == 0 (timeout) across evaluated folds: {avg_pct_0_test:.1f}%")
        print(f"  total nonzero signals across evaluated folds: {total_signals}/{total_test_rows}")
        print(f"  max feature importance (gain) seen for any fold, per feature: {max_importance_per_feature}")
    else:
        print("=== SUMMARY: no folds evaluated (all skipped by MIN_TRAIN_ROWS) ===")


def main() -> None:
    cfg = _load_config()
    raw = _fetch_data(cfg)
    df = compute_all_features(raw.reset_index(drop=True))
    labels = compute_triple_barrier_labels(df)
    df["label"] = labels["label"]

    reports = diagnose(df)
    _print_report(reports)


if __name__ == "__main__":
    main()
