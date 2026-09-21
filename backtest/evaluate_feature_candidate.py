"""
evaluate_feature_candidate.py

Commit 2.8 — formalny test OOS pojedynczej cechy dodanej do feature setu modelu
(CLAUDE.md zasada 4: "jedna cecha na raz, mierzona na out-of-sample — nigdy grid
search po wielu kombinacjach naraz"). Skrypt jednorazowy/analityczny, poza pytest
(jak `calibrate_regime_thresholds.py` / `checkpoint_timeframe_robustness.py`).

KONTEKST: Commit 2.7 (screening korelacji, `backtest/screen_feature_candidates.py`)
przeglądnął 8 kandydatek nowych cech i wyróżnił `adx_14` jako JEDYNĄ nisko
skorelowaną z resztą registry (corr=+0.07 z `direction_persistence_10`, mimo że oba
mają mierzyć "siłę trendu") — ale ta korelacja była WYŁĄCZNIE opisowa/eksploracyjna
(cały zbiór, nie OOS) i nie stanowiła dowodu edge'u (docs/rag/02, "Rozszerzanie
feature setu — protokół"). Ten skrypt jest tym jedynym krokiem o wadze dowodowej:
formalny walk-forward checkpoint porównujący DWA warianty modelu Test 1 (trend):

  BASELINE:  MOMENTUM_FEATURES  (4 cechy, bez zmian — agents/ml_optimizer.py)
  KANDYDAT:  MOMENTUM_FEATURES + ["adx_14"]  (5 cech — jedna cecha DODANA, nie
             zamiana żadnej istniejącej)

Model Test 2 (range, REVERSION_FEATURES) NIEZMIENIONY w obu wariantach — `adx_14`
został wyróżniony w C2.7 konkretnie jako kandydat trend-strength dla Test 1, nie
Test 2 (FAMILY_ASSIGNMENT w screeningu). Testowanie go jednocześnie w obu modelach
byłoby dwoma eksperymentami naraz, nie jednym.

METODOLOGIA (identyczna z C2.5/C2.6, ten sam `run_backtest`/`metrics.py`):
  - `regime_feature_sets` (Commit 2.8, `backtest/engine.py`) pozwala nadpisać
    domyślny `REGIME_FEATURE_SETS` bez duplikacji pipeline'u ani zmiany
    `agents/ml_optimizer.py` na stałe — promocja `adx_14` do `MOMENTUM_FEATURES`
    (jeśli w ogóle) jest OSOBNĄ decyzją, PO przeczytaniu wyniku tego skryptu.
  - Wszystko inne niezmienione: progi regime (0.7/0.3), ATR_MULTIPLIER, bramka
    kosztowa (min_barrier_to_cost_ratio=2.0), timeframe (5m), hiperparametry XGBoost.
  - 10-seedowy sweep stabilności (ten sam próg std < 0.2 co Commit 6/C2.5/C2.6).
  - Wynik: PEŁNA tabela porównawcza (baseline vs kandydat, ogólnie i per regime).
    Skrypt NIE wybiera "zwycięzcy" — decyzja, czy dopisać `adx_14` do
    `MOMENTUM_FEATURES` na stałe, należy do użytkownika.

Użycie:
    py -m backtest.evaluate_feature_candidate --quick   # tylko seed=42 per wariant
    py -m backtest.evaluate_feature_candidate           # pełny sweep 10 seedów x 2 warianty
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import yaml

from agents.ml_optimizer import MOMENTUM_FEATURES, REVERSION_FEATURES
from backtest.engine import run_backtest
from backtest.metrics import (
    classify_checkpoint,
    compute_fold_metrics,
    summarize_by_regime,
)
from data.fetch_ohlcv import get_ohlcv_cached

PRIMARY_SEED = (
    42  # = agents.ml_optimizer.DEFAULT_SEED / config/settings.yaml model.seed
)
SEEDS = list(range(42, 52))  # 10 seedów — te same co Commit 6/C2.5/C2.6
STABILITY_STD_THRESHOLD = 0.2

CANDIDATE_FEATURE = "adx_14"

# Dwa warianty do porównania — WYŁĄCZNIE Test 1 (trend) się zmienia, Test 2 (range)
# identyczny w obu (patrz docstring modułu — jeden eksperyment, nie dwa naraz).
VARIANTS: dict[str, list[tuple[str, list[str]]]] = {
    "baseline (bez adx_14)": [
        ("trend", MOMENTUM_FEATURES),
        ("range", REVERSION_FEATURES),
    ],
    f"kandydat (+{CANDIDATE_FEATURE})": [
        ("trend", [*MOMENTUM_FEATURES, CANDIDATE_FEATURE]),
        ("range", REVERSION_FEATURES),
    ],
}


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fetch_data(cfg: dict) -> pd.DataFrame:
    data_cfg = cfg["data"]
    df = get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=data_cfg["timeframe"],
        start=data_cfg["start"],
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )
    print(f"[data] {len(df)} świec: {df['timestamp'].min()} -> {df['timestamp'].max()}")
    return df


def _run_and_summarize(
    raw_ohlcv: pd.DataFrame, seed: int, regime_feature_sets: list[tuple[str, list[str]]]
) -> dict:
    result = run_backtest(raw_ohlcv, seed=seed, regime_feature_sets=regime_feature_sets)
    fold_metrics = compute_fold_metrics(result["trades"], result["folds_summary"])
    classification = classify_checkpoint(fold_metrics)
    per_regime = summarize_by_regime(fold_metrics)
    return {
        "seed": seed,
        "fold_metrics": fold_metrics,
        "classification": classification,
        "per_regime": per_regime,
    }


def _evaluate_variant(
    raw_ohlcv: pd.DataFrame,
    label: str,
    regime_feature_sets: list[tuple[str, list[str]]],
    quick: bool,
) -> dict:
    trend_features = dict(regime_feature_sets)["trend"]
    print(f"\n{'=' * 88}\nWARIANT: {label}\n{'=' * 88}")
    print(f"  MOMENTUM_FEATURES (trend): {trend_features}")
    print(
        f"  REVERSION_FEATURES (range, niezmienione): {dict(regime_feature_sets)['range']}"
    )

    print(f"\n[seed={PRIMARY_SEED}] uruchamiam run_backtest...")
    primary = _run_and_summarize(raw_ohlcv, PRIMARY_SEED, regime_feature_sets)

    print(f"=== Sharpe per fold (seed={PRIMARY_SEED}) ===")
    print(primary["fold_metrics"].to_string(index=False))
    print(f"\n=== Klasyfikacja (seed={PRIMARY_SEED}) ===")
    print(primary["classification"])
    print(f"\n=== Rozbicie per reżim (seed={PRIMARY_SEED}) ===")
    print(primary["per_regime"].to_string(index=False))

    result = {
        "label": label,
        "trend_features": trend_features,
        "primary": primary,
    }

    if quick:
        print("\n[--quick] pomijam sweep 10 seedów dla tego wariantu.")
        result["stability_std"] = float("nan")
        result["is_stable"] = None
        result["seed_results"] = {PRIMARY_SEED: primary}
        return result

    print(f"\n[sweep] {len(SEEDS)} seedów: {SEEDS}")
    seed_results = {PRIMARY_SEED: primary}
    for seed in SEEDS:
        if seed == PRIMARY_SEED:
            continue
        print(f"  ... seed={seed}")
        seed_results[seed] = _run_and_summarize(raw_ohlcv, seed, regime_feature_sets)

    mean_sharpes = [seed_results[s]["classification"]["mean_sharpe"] for s in SEEDS]
    mean_sharpes_clean = [m for m in mean_sharpes if not np.isnan(m)]
    stability_std = (
        float(np.std(mean_sharpes_clean, ddof=1))
        if len(mean_sharpes_clean) > 1
        else float("nan")
    )
    is_stable = (
        not np.isnan(stability_std)
    ) and stability_std < STABILITY_STD_THRESHOLD

    print(f"\n=== Stabilność między seedami (wariant: {label}) ===")
    for s in SEEDS:
        c = seed_results[s]["classification"]
        print(
            f"  seed={s:>3}  mean_sharpe={c['mean_sharpe']:.4f}  klasyfikacja={c['classification']}"
        )
    print(
        f"std(mean_sharpe) między {len(SEEDS)} seedami = {stability_std:.4f} "
        f"({'STABILNY' if is_stable else 'NIESTABILNY'}, próg < {STABILITY_STD_THRESHOLD})"
    )

    result["stability_std"] = stability_std
    result["is_stable"] = is_stable
    result["seed_results"] = seed_results
    return result


def main(quick: bool) -> None:
    cfg = _load_config()
    raw_ohlcv = _fetch_data(cfg)

    print(
        f"\n[rejestr] {len(VARIANTS)} warianty (baseline + 1 kandydat, CLAUDE.md zasada 4):"
    )
    for label, feature_sets in VARIANTS.items():
        print(f"  - {label}: trend={dict(feature_sets)['trend']}")

    results = [
        _evaluate_variant(raw_ohlcv, label, feature_sets, quick)
        for label, feature_sets in VARIANTS.items()
    ]

    print(
        f"\n{'=' * 88}\nTABELA PORÓWNAWCZA — baseline vs kandydat (bez automatycznego wyboru zwycięzcy)\n{'=' * 88}"
    )
    rows = []
    for res in results:
        c = res["primary"]["classification"]
        per_regime = res["primary"]["per_regime"].set_index("regime")
        trend_sharpe = (
            per_regime.loc["trend", "mean_sharpe"]
            if "trend" in per_regime.index
            else float("nan")
        )
        rows.append(
            {
                "wariant": res["label"],
                "n_trend_features": len(res["trend_features"]),
                f"mean_sharpe(seed={PRIMARY_SEED})": (
                    round(c["mean_sharpe"], 4)
                    if not np.isnan(c["mean_sharpe"])
                    else float("nan")
                ),
                f"trend_sharpe(seed={PRIMARY_SEED})": (
                    round(trend_sharpe, 4)
                    if not np.isnan(trend_sharpe)
                    else float("nan")
                ),
                f"klasyfikacja(seed={PRIMARY_SEED})": c["classification"],
                "n_valid_folds": c["n_valid_folds"],
                "stability_std(10 seed)": (
                    round(res["stability_std"], 4)
                    if not np.isnan(res["stability_std"])
                    else float("nan")
                ),
                "stabilny": res["is_stable"],
            }
        )
    comparison = pd.DataFrame(rows)
    print(comparison.to_string(index=False))

    print(
        "\n[UWAGA] Ten skrypt CELOWO nie wybiera 'najlepszego' wariantu — decyzja, czy dopisać"
        f"\n'{CANDIDATE_FEATURE}' na stałe do MOMENTUM_FEATURES (agents/ml_optimizer.py), należy do"
        "\nużytkownika, po przeczytaniu pełnej tabeli powyżej, nie tylko najwyższej liczby"
        "\n(CLAUDE.md zasada 1/4 — unikanie optymalizacji na wyniku PnL, jedna cecha na raz)."
    )


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
