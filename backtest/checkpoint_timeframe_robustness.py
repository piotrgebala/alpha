"""
checkpoint_timeframe_robustness.py

Commit 2.6 — sprawdza, czy NO-GO (Commit 6 -> 2c -> 2d -> 2.5) jest artefaktem
konkretnego timeframe (5m), czy utrzymuje się na grubszych interwałach (1h, 4h), gdzie
bariera zysku (ATR_MULTIPLIER * atr_14) rośnie względem STAŁEGO kosztu round-trip. Skrypt
jednorazowy/analityczny, poza pytest (jak `run_checkpoint.py` / `calibrate_regime_thresholds.py`).

KONTEKST: Commit 2d pokazał, że w reżimie `range` na 5m mediana bariery (0,130% ceny) jest
WĘŻSZA niż koszt round-trip (0,140% nominału) — wymagana trafność break-even 103,9%,
arytmetycznie nieosiągalna. Na 5m pozycja trzymana max. 12 świec = 1h (VERTICAL_BARRIER_CANDLES).
Dłuższy interwał daje więcej ruchu ceny na świecę (większe ATR jako % ceny), więc bariera
strukturalnie rośnie, NIEZALEŻNIE od jakichkolwiek innych zmian.

UWAGA O ŹRÓDLE DANYCH: to środowisko NIE MA dostępu sieciowego do Binance
(`fapi.binance.com` blokowane przez proxy — zweryfikowane empirycznie, `curl` zwraca 403 na
CONNECT). Natywny fetch 1h/4h przez `data.fetch_ohlcv.get_ohlcv_cached` jest tu niemożliwy.
Dane 1h/4h są więc AGREGOWANE z tego samego, już zweryfikowanego źródła 5m (Commit 1,
`find_gaps` = zero dziur na pełnym roku) przez `data.fetch_ohlcv.resample_ohlcv` — patrz
docstring tej funkcji dla dokładnych ograniczeń tego podejścia względem natywnego fetcha.

CO JEST ZMIENIANE, a co CELOWO NIE (jeden eksperyment = jedna zmienna, CLAUDE.md zasada 1/4):
  ZMIENIANE:
    - timeframe danych wejściowych (5m -> 1h -> 4h, przez resample)
    - `candles_per_day` (288 -> 24 -> 6) — WYŁĄCZNIE konwersja jednostek, żeby okno
      atr_pctrank_20d nadal reprezentowało ~20 dni kalendarzowych (Commit 2.6, patrz
      agents/feature_miner.py). To NIE jest tuning parametru hipotezy.
  NIEZMIENIANE (świadomie, dla czystości eksperymentu):
    - trend_threshold/range_threshold = 0.7/0.3 (baseline C2.5, WYCZERPANE jako kierunek)
    - ATR_MULTIPLIER = 1.5 (CLAUDE.md zasada 3)
    - min_barrier_to_cost_ratio = 2.0 (Commit 2d, bramka kosztowa AKTYWNA)
    - VERTICAL_BARRIER_CANDLES = 12 — UWAGA: to oznacza, że REALNY czas trzymania pozycji
      rośnie wraz z timeframe (12 świec = 1h @ 5m, ALE 12h @ 1h, 48h @ 4h). To ŚWIADOMY
      efekt uboczny "zmieniamy tylko timeframe" (dosłowna interpretacja polecenia) — NIE
      próba jednoczesnego przetestowania "innego horyzontu czasowego". Jeśli wynik na 1h/4h
      wypadnie inaczej niż na 5m, część przyczyny może być tu, nie tylko w barierze ATR-vs-
      koszt — flagowane w output, decyzja o rozdzieleniu tych dwóch zmiennych (timeframe vs
      horyzont trzymania) należy do użytkownika w kolejnej rundzie.

Użycie:
    py -m backtest.checkpoint_timeframe_robustness --quick   # tylko seed=42 per timeframe
    py -m backtest.checkpoint_timeframe_robustness           # pełny sweep 10 seedów x 2 timeframe'y
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import yaml

from backtest.engine import run_backtest
from backtest.metrics import classify_checkpoint, compute_fold_metrics, summarize_by_regime
from data.fetch_ohlcv import find_gaps, get_ohlcv_cached, resample_ohlcv

PRIMARY_SEED = 42
SEEDS = list(range(42, 52))  # te same 10 seedów co Commit 6/2c/2d/2.5
STABILITY_STD_THRESHOLD = 0.2

# Timeframe -> candles_per_day (konwersja jednostek dla atr_pctrank_20d, patrz docstring
# modułu i agents/feature_miner.py) + oczekiwana liczba świec po resample (weryfikacja
# integralności: 105_120 świec 5m / 12 = 8_760 świec 1h; / 48 = 2_190 świec 4h — dokładny
# podział bez reszty, bo źródło zaczyna się dokładnie o północy UTC i ma zero dziur,
# Commit 1).
TIMEFRAME_CONFIG = {
    "1h": {"candles_per_day": 24, "expected_candles": 8_760},
    "4h": {"candles_per_day": 6, "expected_candles": 2_190},
}


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_base_5m_data(cfg: dict) -> pd.DataFrame:
    data_cfg = cfg["data"]
    df = get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=data_cfg["timeframe"],
        start=data_cfg["start"],
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )
    print(f"[data] baza 5m: {len(df)} świec, {df['timestamp'].min()} -> {df['timestamp'].max()}")
    gaps = find_gaps(df, timeframe_minutes=5)
    if len(gaps) > 0:
        raise RuntimeError(f"Baza 5m ma {len(gaps)} dziur — resample do 1h/4h byłby niepoprawny")
    return df


def _prepare_timeframe_data(base_5m: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df = resample_ohlcv(base_5m, timeframe)
    expected = TIMEFRAME_CONFIG[timeframe]["expected_candles"]
    print(f"[data] {timeframe}: {len(df)} świec (oczekiwane {expected}), " f"{df['timestamp'].min()} -> {df['timestamp'].max()}")
    if len(df) != expected:
        print(
            f"[data] UWAGA: liczba świec {timeframe} ({len(df)}) różni się od oczekiwanej "
            f"({expected}) — sprawdź resample_ohlcv/wyrównanie granic."
        )
    return df


def _run_and_summarize(raw_ohlcv: pd.DataFrame, seed: int, candles_per_day: int) -> dict:
    result = run_backtest(raw_ohlcv, seed=seed, candles_per_day=candles_per_day)
    fold_metrics = compute_fold_metrics(result["trades"], result["folds_summary"])
    classification = classify_checkpoint(fold_metrics)
    per_regime = summarize_by_regime(fold_metrics)
    return {
        "seed": seed,
        "fold_metrics": fold_metrics,
        "classification": classification,
        "per_regime": per_regime,
    }


def _evaluate_timeframe(base_5m: pd.DataFrame, timeframe: str, quick: bool) -> dict:
    print(f"\n{'=' * 88}\nTIMEFRAME: {timeframe}\n{'=' * 88}")
    candles_per_day = TIMEFRAME_CONFIG[timeframe]["candles_per_day"]
    raw_ohlcv = _prepare_timeframe_data(base_5m, timeframe)

    print(f"\n[seed={PRIMARY_SEED}] uruchamiam run_backtest (candles_per_day={candles_per_day})...")
    primary = _run_and_summarize(raw_ohlcv, PRIMARY_SEED, candles_per_day)

    print(f"=== Sharpe per fold (seed={PRIMARY_SEED}) ===")
    print(primary["fold_metrics"].to_string(index=False))
    print(f"\n=== Klasyfikacja (seed={PRIMARY_SEED}) ===")
    print(primary["classification"])
    print(f"\n=== Rozbicie per reżim (seed={PRIMARY_SEED}) ===")
    print(primary["per_regime"].to_string(index=False))

    result = {"timeframe": timeframe, "n_candles": len(raw_ohlcv), "primary": primary}

    if quick:
        print(f"\n[--quick] pomijam sweep {len(SEEDS)} seedów dla {timeframe}.")
        result["stability_std"] = float("nan")
        result["is_stable"] = None
        return result

    print(f"\n[sweep] {len(SEEDS)} seedów: {SEEDS}")
    seed_results = {PRIMARY_SEED: primary}
    for seed in SEEDS:
        if seed == PRIMARY_SEED:
            continue
        print(f"  ... seed={seed}")
        seed_results[seed] = _run_and_summarize(raw_ohlcv, seed, candles_per_day)

    mean_sharpes = [seed_results[s]["classification"]["mean_sharpe"] for s in SEEDS]
    mean_sharpes_clean = [m for m in mean_sharpes if not np.isnan(m)]
    stability_std = (
        float(np.std(mean_sharpes_clean, ddof=1)) if len(mean_sharpes_clean) > 1 else float("nan")
    )
    is_stable = (not np.isnan(stability_std)) and stability_std < STABILITY_STD_THRESHOLD

    print(f"\n=== Stabilność między seedami ({timeframe}) ===")
    for s in SEEDS:
        c = seed_results[s]["classification"]
        print(f"  seed={s:>3}  mean_sharpe={c['mean_sharpe']:.4f}  klasyfikacja={c['classification']}")
    print(
        f"std(mean_sharpe) między {len(SEEDS)} seedami = {stability_std:.4f} "
        f"({'STABILNY' if is_stable else 'NIESTABILNY'}, próg < {STABILITY_STD_THRESHOLD})"
    )

    result["stability_std"] = stability_std
    result["is_stable"] = is_stable
    return result


def main(quick: bool) -> None:
    cfg = _load_config()
    base_5m = _load_base_5m_data(cfg)

    results = [_evaluate_timeframe(base_5m, tf, quick) for tf in TIMEFRAME_CONFIG]

    print(f"\n{'=' * 88}\nTABELA PORÓWNAWCZA — 5m (referencja, Commit 2.5) vs 1h vs 4h\n{'=' * 88}")
    rows = []
    for res in results:
        c = res["primary"]["classification"]
        rows.append(
            {
                "timeframe": res["timeframe"],
                "n_candles": res["n_candles"],
                f"mean_sharpe(seed={PRIMARY_SEED})": round(c["mean_sharpe"], 4)
                if not np.isnan(c["mean_sharpe"])
                else float("nan"),
                f"klasyfikacja(seed={PRIMARY_SEED})": c["classification"],
                "n_valid_folds": c["n_valid_folds"],
                "n_total_folds": c["n_total_folds"],
                "stability_std(10 seed)": round(res["stability_std"], 4)
                if not np.isnan(res["stability_std"])
                else float("nan"),
                "stabilny": res["is_stable"],
            }
        )
    comparison = pd.DataFrame(rows)
    print(comparison.to_string(index=False))
    print(
        "\n[REFERENCJA] 5m (Commit 2.5, baseline 0.7/0.3): mean_sharpe(seed=42)=-14.3078, "
        "NO-GO, 6/40 foldów ważnych, std(10 seed)=0.0000."
    )
    print(
        "\n[UWAGA] Ten skrypt NIE wybiera 'zwycięzcy' między timeframe'ami — to nie jest "
        "\nporównanie kandydatów do wyboru najlepszego, tylko test odporności tej samej "
        "\nhipotezy na zmianę granulacji danych. Interpretacja wyniku (w tym efektu ubocznego "
        "\nVERTICAL_BARRIER_CANDLES=12 opisanego w docstringu modułu) należy do użytkownika."
    )


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
