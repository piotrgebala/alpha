"""
calibrate_regime_thresholds.py

Commit 2.5 — kalibracja progów reguły regime (`agents.feature_miner.classify_regime`)
na REALNYCH danych BTC. Skrypt jednorazowy/analityczny, poza pytest (jak
`run_checkpoint.py` / `diagnose_cost_feasibility.py`) — porównuje z góry zarejestrowany,
mały zestaw kandydatów przez PEŁNY pipeline walk-forward (ten sam `run_backtest`/
`metrics.py` co Commit 6), BEZ automatycznego wyboru "zwycięzcy" — decyzja zostaje przy
użytkowniku.

Dlaczego ten skrypt istnieje (kontekst): `backtest/diagnose_cost_feasibility.py` (blok 1)
pokazał, że `direction_persistence_10 = |sum(sign(return))| / 10` jest DYSKRETNA — przy
10 znakach zwrotu bez remisów (return == 0) suma ma tę samą parzystość co 10 (parzysta),
więc |suma|/10 przyjmuje WYŁĄCZNIE wartości {0.0, 0.2, 0.4, 0.6, 0.8, 1.0}; wartości
nieparzyste (0.1, 0.3, 0.5, 0.7, 0.9) mają masę ~0. Obecny `trend_threshold=0.7`
(config/settings.yaml) leży w luce między masami 0.6 i 0.8 — `persistence > 0.7` i
`persistence > 0.6` selekcjonują DOKŁADNIE ten sam zbiór świec ({0.8, 1.0}), więc dwa
pozornie różne progi dają identyczną populację. To czyni regime "trend" ustrukturalnie
prawie pustym niezależnie od `atr_pctrank_20d`.

METODOLOGIA (CLAUDE.md zasada 1 — nigdy nie optymalizuj progów na całym zbiorze naraz,
tylko wewnątrz walk-forward; docs/rag/02_cechy_i_leakage.md — ostrzeżenie o multiple
testing/data dredging):
  - Kandydaci wybrani WYŁĄCZNIE ze STRUKTURY formuły persistence (jej dyskretnego
    wsparcia {0, 0.2, 0.4, 0.6, 0.8, 1.0}) — NIE z podglądania Sharpe'a/PnL na tym
    zbiorze danych. Uzasadnienie każdego kandydata w CANDIDATE_THRESHOLDS niżej.
  - Mały, z góry zarejestrowany zestaw (4 kandydaci, nie siatka), żeby nie zamienić
    kalibracji w przeszukiwanie po wyniku (data dredging).
  - Każdy kandydat oceniany przez DOKŁADNIE ten sam pipeline co Commit 6
    (`run_backtest` -> `compute_fold_metrics` -> `classify_checkpoint` ->
    `summarize_by_regime`), z bramką kosztową aktywną domyślnie (Commit 2d,
    `min_barrier_to_cost_ratio=2.0`) — porównujemy WYŁĄCZNIE efekt progów regime,
    reszta pipeline'u niezmieniona.
  - 10-seedowy sweep stabilności (C6.3, seed 42..51) per kandydat — ten sam próg
    std < 0.2 co Commit 6.
  - Wynik: PEŁNA tabela porównawcza wszystkich kandydatów. Skrypt NIE wybiera
    "zwycięzcy" — to świadome ograniczenie (decyzja o zmianie config/settings.yaml
    należy do użytkownika, po przeczytaniu pełnego rozkładu, nie tylko najlepszej
    liczby).

Użycie:
    py -m backtest.calibrate_regime_thresholds --quick   # tylko seed=42 per kandydat
    py -m backtest.calibrate_regime_thresholds           # pełny sweep 10 seedów x 4 kandydatów
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import yaml

from agents.feature_miner import classify_regime
from backtest.engine import run_backtest
from backtest.metrics import classify_checkpoint, compute_fold_metrics, summarize_by_regime
from data.fetch_ohlcv import get_ohlcv_cached

PRIMARY_SEED = 42  # = agents.ml_optimizer.DEFAULT_SEED / config/settings.yaml model.seed
SEEDS = list(range(42, 52))  # 10 seedów — te same co Commit 6 (C6.3)
STABILITY_STD_THRESHOLD = 0.2  # ustalone z użytkownikiem (C6.3)

# Kandydaci (trend_threshold, range_threshold) + uzasadnienie STRUKTURALNE (nie z PnL):
#
#   (0.7, 0.3)  BASELINE — wartość startowa, config/settings.yaml (docs/rag/02).
#   (0.6, 0.4)  KONTROLA — 0.6 i 0.7 leżą w tej samej luce rozkładu persistence (brak
#               masy w (0.6, 0.8)), analogicznie 0.3/0.4 w luce (brak masy w (0.3, 0.4)
#               powyżej masy 0.2/poniżej masy 0.4). PRZEWIDYWANIE: identyczna populacja
#               trend/range co baseline. Jeśli wynik faktycznie się różni, to sygnał
#               błędu w tej diagnozie (albo w kodzie), nie realny efekt kalibracji —
#               ten kandydat jest testem samej hipotezy, nie próbą poprawy.
#   (0.5, 0.3)  Przecina PIERWSZĄ granicę masy na osi trend (persistence > 0.5 dołącza
#               masę 0.6, ~7% świec) — range bez zmian. Izoluje efekt samego trend.
#   (0.5, 0.5)  Przecina granicę masy na OBU osiach (trend: +masa 0.6; range:
#               persistence < 0.5 dołącza masę 0.4, ~22% świec). Test symetrycznego
#               poluzowania.
CANDIDATE_THRESHOLDS: list[tuple[float, float]] = [
    (0.7, 0.3),
    (0.6, 0.4),
    (0.5, 0.3),
    (0.5, 0.5),
]


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


def _describe_population(raw_ohlcv: pd.DataFrame, trend_threshold: float, range_threshold: float) -> dict:
    """Opisowy (read-only) rozkład populacji regime dla danej pary progów — informacyjnie,
    obok checkpointu, żeby tabela końcowa pokazywała TAKŻE, ile świec w ogóle wchodzi do
    gry, nie tylko wynik Sharpe."""
    regime = classify_regime(raw_ohlcv, trend_threshold=trend_threshold, range_threshold=range_threshold)
    n = len(regime)
    return {
        "pct_trend": float((regime == "trend").mean()) * 100.0,
        "pct_range": float((regime == "range").mean()) * 100.0,
        "pct_ambiguous": float((regime == "ambiguous").mean()) * 100.0,
        "n_candles": n,
    }


def _run_and_summarize(raw_ohlcv: pd.DataFrame, seed: int, trend_threshold: float, range_threshold: float) -> dict:
    result = run_backtest(
        raw_ohlcv, seed=seed, trend_threshold=trend_threshold, range_threshold=range_threshold
    )
    fold_metrics = compute_fold_metrics(result["trades"], result["folds_summary"])
    classification = classify_checkpoint(fold_metrics)
    per_regime = summarize_by_regime(fold_metrics)
    return {
        "seed": seed,
        "fold_metrics": fold_metrics,
        "classification": classification,
        "per_regime": per_regime,
    }


def _evaluate_candidate(raw_ohlcv: pd.DataFrame, trend_threshold: float, range_threshold: float, quick: bool) -> dict:
    label = f"trend_threshold={trend_threshold}, range_threshold={range_threshold}"
    print(f"\n{'=' * 88}\nKANDYDAT: {label}\n{'=' * 88}")

    population = _describe_population(raw_ohlcv, trend_threshold, range_threshold)
    print(
        f"[populacja] trend={population['pct_trend']:.2f}%  range={population['pct_range']:.2f}%  "
        f"ambiguous={population['pct_ambiguous']:.2f}%  (n={population['n_candles']})"
    )

    print(f"\n[seed={PRIMARY_SEED}] uruchamiam run_backtest...")
    primary = _run_and_summarize(raw_ohlcv, PRIMARY_SEED, trend_threshold, range_threshold)

    print(f"=== Sharpe per fold (seed={PRIMARY_SEED}) ===")
    print(primary["fold_metrics"].to_string(index=False))
    print(f"\n=== Klasyfikacja (seed={PRIMARY_SEED}) ===")
    print(primary["classification"])
    print(f"\n=== Rozbicie per reżim (seed={PRIMARY_SEED}) ===")
    print(primary["per_regime"].to_string(index=False))

    result = {
        "trend_threshold": trend_threshold,
        "range_threshold": range_threshold,
        "population": population,
        "primary": primary,
    }

    if quick:
        print(f"\n[--quick] pomijam sweep {len(SEEDS)} seedów dla tego kandydata.")
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
        seed_results[seed] = _run_and_summarize(raw_ohlcv, seed, trend_threshold, range_threshold)

    mean_sharpes = [seed_results[s]["classification"]["mean_sharpe"] for s in SEEDS]
    mean_sharpes_clean = [m for m in mean_sharpes if not np.isnan(m)]
    stability_std = (
        float(np.std(mean_sharpes_clean, ddof=1)) if len(mean_sharpes_clean) > 1 else float("nan")
    )
    is_stable = (not np.isnan(stability_std)) and stability_std < STABILITY_STD_THRESHOLD

    print(f"\n=== Stabilność między seedami (kandydat {label}) ===")
    for s in SEEDS:
        c = seed_results[s]["classification"]
        print(f"  seed={s:>3}  mean_sharpe={c['mean_sharpe']:.4f}  klasyfikacja={c['classification']}")
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

    print(f"\n[rejestr] {len(CANDIDATE_THRESHOLDS)} kandydatów (z góry ustalonych, patrz docstring modułu):")
    for t, r in CANDIDATE_THRESHOLDS:
        print(f"  - trend_threshold={t}, range_threshold={r}")

    results = [
        _evaluate_candidate(raw_ohlcv, t, r, quick) for t, r in CANDIDATE_THRESHOLDS
    ]

    print(f"\n{'=' * 88}\nTABELA PORÓWNAWCZA — WSZYSCY KANDYDACI (bez automatycznego wyboru zwycięzcy)\n{'=' * 88}")
    rows = []
    for res in results:
        c = res["primary"]["classification"]
        rows.append(
            {
                "trend_thr": res["trend_threshold"],
                "range_thr": res["range_threshold"],
                "%trend": round(res["population"]["pct_trend"], 2),
                "%range": round(res["population"]["pct_range"], 2),
                f"mean_sharpe(seed={PRIMARY_SEED})": round(c["mean_sharpe"], 4)
                if not np.isnan(c["mean_sharpe"])
                else float("nan"),
                f"klasyfikacja(seed={PRIMARY_SEED})": c["classification"],
                "n_valid_folds": c["n_valid_folds"],
                "stability_std(10 seed)": round(res["stability_std"], 4)
                if not np.isnan(res["stability_std"])
                else float("nan"),
                "stabilny": res["is_stable"],
            }
        )
    comparison = pd.DataFrame(rows)
    print(comparison.to_string(index=False))

    print(
        "\n[UWAGA] Ten skrypt CELOWO nie wybiera 'najlepszego' kandydata — decyzja, czy i który"
        "\nzestaw progów wpisać do config/settings.yaml, należy do użytkownika, po przeczytaniu"
        "\npełnego rozkładu Sharpe/populacji/stabilności powyżej, nie tylko najwyższej liczby"
        "\n(CLAUDE.md zasada 1 — unikanie optymalizacji progów na wyniku PnL)."
    )


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
