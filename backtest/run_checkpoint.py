"""
run_checkpoint.py

Commit 6 — pełny checkpoint go/no-go na REALNYCH danych z Binance (przez
data/fetch_ohlcv.get_ohlcv_cached). Skrypt jednorazowy/analityczny, celowo POZA
pytest (brak asercji, wymaga sieci przy pierwszym uruchomieniu i realnego czasu
treningu XGBoost x10 seedów) — wyniki liczbowe trafiają ręcznie do
STATUS.md (C6.5). Testy formuł/klasyfikacji są w tests/test_metrics.py
(syntetyczne, deterministyczne, bez sieci).

Kroki:
  1. Weryfikacja symbolu ccxt (C1.3) — potwierdza config/settings.yaml.
  2. Fetch/cache OHLCV (get_ohlcv_cached, no-op jeśli już w cache) + find_gaps.
  3. run_backtest z seed=42 (kanoniczny/domyślny, agents.ml_optimizer.DEFAULT_SEED) —
     C6.1 (Sharpe per fold), C6.2 (klasyfikacja), C6.4 (rozbicie per reżim).
  4. (pominięte przy --quick) Sweep seed 42..51 (10 seedów) — C6.3, stabilność:
     std zagregowanego (mean-of-valid-folds) Sharpe między seedami < 0.2.

Użycie:
    py -m backtest.run_checkpoint --quick   # tylko seed=42, szybki sanity-check
    py -m backtest.run_checkpoint           # pełny sweep 10 seedów (C6.3)
"""

from __future__ import annotations

import sys

import ccxt
import numpy as np
import pandas as pd
import yaml

from backtest.engine import run_backtest
from backtest.metrics import classify_checkpoint, compute_fold_metrics, summarize_by_regime
from data.fetch_ohlcv import find_gaps, get_ohlcv_cached

SEEDS = list(range(42, 52))  # 10 seedów — ustalone z użytkownikiem (C6.3)
PRIMARY_SEED = 42  # = agents.ml_optimizer.DEFAULT_SEED / config/settings.yaml model.seed
STABILITY_STD_THRESHOLD = 0.2  # ustalone z użytkownikiem (C6.3)


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _verify_symbol(exchange_id: str, symbol: str) -> None:
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class()
    exchange.load_markets()
    if symbol not in exchange.symbols:
        matches = [s for s in exchange.symbols if "BTC/USDT" in s]
        raise ValueError(f"Symbol {symbol!r} nie istnieje na {exchange_id}. Kandydaci: {matches}")
    print(f"[C1.3] Symbol {symbol!r} potwierdzony na {exchange_id}.")


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
    gaps = find_gaps(df, timeframe_minutes=5)
    if len(gaps) > 0:
        print(f"[data] UWAGA: {len(gaps)} dziur:")
        print(gaps)
    else:
        print("[data] brak dziur.")
    return df


def _run_and_summarize(raw_ohlcv: pd.DataFrame, seed: int) -> dict:
    result = run_backtest(raw_ohlcv, seed=seed)
    fold_metrics = compute_fold_metrics(result["trades"], result["folds_summary"])
    classification = classify_checkpoint(fold_metrics)
    return {"seed": seed, "fold_metrics": fold_metrics, "classification": classification}


def main(quick: bool) -> None:
    cfg = _load_config()
    data_cfg = cfg["data"]

    _verify_symbol(data_cfg["exchange_id"], data_cfg["primary_symbol"])
    raw_ohlcv = _fetch_data(cfg)

    print(f"\n[seed={PRIMARY_SEED}] uruchamiam run_backtest (primary/reported result)...")
    primary = _run_and_summarize(raw_ohlcv, PRIMARY_SEED)

    print(f"\n=== C6.1: Sharpe per fold (seed={PRIMARY_SEED}) ===")
    print(primary["fold_metrics"].to_string(index=False))

    print(f"\n=== C6.2: klasyfikacja (seed={PRIMARY_SEED}) ===")
    print(primary["classification"])

    print(f"\n=== C6.4: rozbicie per reżim (seed={PRIMARY_SEED}) ===")
    print(summarize_by_regime(primary["fold_metrics"]).to_string(index=False))

    if quick:
        print("\n[--quick] pomijam sweep 10 seedów (C6.3) — tylko sanity-check primary seed.")
        return

    print(f"\n[C6.3] sweep {len(SEEDS)} seedów: {SEEDS}")
    seed_results = {PRIMARY_SEED: primary}
    for seed in SEEDS:
        if seed == PRIMARY_SEED:
            continue
        print(f"  ... seed={seed}")
        seed_results[seed] = _run_and_summarize(raw_ohlcv, seed)

    mean_sharpes = [seed_results[s]["classification"]["mean_sharpe"] for s in SEEDS]
    mean_sharpes_clean = [m for m in mean_sharpes if not np.isnan(m)]
    stability_std = (
        float(np.std(mean_sharpes_clean, ddof=1)) if len(mean_sharpes_clean) > 1 else float("nan")
    )
    is_stable = (not np.isnan(stability_std)) and stability_std < STABILITY_STD_THRESHOLD

    print("\n=== C6.3: stabilność między seedami ===")
    for s in SEEDS:
        c = seed_results[s]["classification"]
        print(f"  seed={s:>3}  mean_sharpe={c['mean_sharpe']:.4f}  klasyfikacja={c['classification']}")
    print(
        f"std(mean_sharpe) między {len(SEEDS)} seedami = {stability_std:.4f} "
        f"({'STABILNY' if is_stable else 'NIESTABILNY'}, próg < {STABILITY_STD_THRESHOLD})"
    )


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
