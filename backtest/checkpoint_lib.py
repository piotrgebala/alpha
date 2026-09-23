"""
checkpoint_lib.py

Commit 2.9 (Z13) — wspólna biblioteka pomocnicza dla skryptów checkpointowych
(poza pytest, jak skrypty, którym służy). Powstała, bo `_load_config`/`_fetch_data`/
`_run_and_summarize`/sweep/stabilność były skopiowane 4x (run_checkpoint,
calibrate_regime_thresholds, checkpoint_timeframe_robustness,
evaluate_feature_candidate) — w tym 4 kopie STABILITY_STD_THRESHOLD.

ZASADA UŻYCIA (FORWARD-LOOKING): historyczne skrypty NIE są refaktoryzowane wstecz —
to zamrożone zapisy zakończonych eksperymentów, odtwarzalne komendą z sekcji
"Metadane" ich plików `runs/*.md`. Ta biblioteka obowiązuje OD NOWYCH skryptów
(pierwszy: `backtest/run_checkpoint_v2.py`).

STABILNOŚĆ — ZMIANA METODOLOGII (Commit 2.9, Z1; docs/rag/03, aktualizacja
2026-09-21): sweep po seedach (C6.3) okazał się PUSTY POZNAWCZO — XGBoost w
konfiguracji Fazy 0 (DEFAULT_XGB_PARAMS bez subsample/colsample_bytree) jest w pełni
deterministyczny, więc seed niczego nie zmienia; stąd std=0,0000 identyczne do
ostatniej cyfry w KAŻDYM eksperymencie od Commitu 6 (C6, 2c, 2d, C2.5x4, C2.6x2,
C2.8x2 — ~10 niezależnych potwierdzeń). Zamiennik: `sweep_fold_offsets` — jitter
przesunięcia startu okien walk-forward (0..9 dni). Perturbuje ARBITRALNY wybór
wyrównania granic foldów (dotąd zawsze "od pierwszej świecy"), NIE model i NIE
hipotezę — offset=0 to dokładnie kanoniczny przebieg, więc porównywalność z
historycznymi wynikami jest zachowana.

UWAGA O PROGU: stary próg std < 0.2 był skalibrowany dla (pustego) szumu seedów i
NIE przenosi się na fold-jitter — różne offsety dają REALNIE różne podziały danych,
więc naturalna wariancja jest większa. Ten moduł świadomie NIE rejestruje nowego
progu pass/fail (to byłby parametr dobrany bez uzasadnienia — CLAUDE.md zasada 1
stosowana do metodologii): raportuje rozkład (std, zakres) + spójność znaku
(sign-consistency: ułamek offsetów z mean_sharpe < 0). Interpretacja i ewentualny
próg — decyzja użytkownika po obejrzeniu pierwszych realnych rozkładów.
"""

from __future__ import annotations

import pandas as pd
import yaml

from backtest.engine import run_backtest
from backtest.metrics import (
    classify_checkpoint,
    compute_fold_metrics,
    summarize_by_regime,
    summarize_edge_by_regime,
    summarize_pooled_by_regime,
)
from data.fetch_ohlcv import find_gaps, get_ohlcv_cached

PRIMARY_SEED = 42  # = agents.ml_optimizer.DEFAULT_SEED / config/settings.yaml model.seed

# Offsety startu okien walk-forward do sweepu stabilności fold-jitter (dni).
# 0 = kanoniczny przebieg (identyczny z historycznymi wynikami); 1..9 = perturbacje.
# Zakres 0..9 dni < step_days=14, więc kolejne offsety dają faktycznie różne
# (nie okresowo powtarzające się) wyrównania foldów.
FOLD_OFFSETS_DAYS: list[float] = [float(d) for d in range(10)]


def load_config(path: str = "config/settings.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_data(cfg: dict, timeframe_minutes: int = 5) -> pd.DataFrame:
    """Fetch/cache primary_symbol wg configu + raport dziur (find_gaps)."""
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
    gaps = find_gaps(df, timeframe_minutes=timeframe_minutes)
    if len(gaps) > 0:
        print(f"[data] UWAGA: {len(gaps)} dziur:")
        print(gaps)
    else:
        print("[data] brak dziur.")
    return df


def fetch_native(data_cfg: dict, timeframe: str) -> pd.DataFrame:
    """
    W1: natywne świece zadanego interwału z trwałego cache (bez sieci, gdy plik już jest).
    Respektuje `timeframe_start_overrides` (Z5b: 4h ma dłuższą historię niż 5m/1h). Ta sama
    logika, którą zamrożone skrypty rund (Z9 → F1) miały jako prywatny `_load` — od W1 mieszka
    tu, żeby nowe skrypty nie importowały z plików zamrożonych.
    """
    start = (data_cfg.get("timeframe_start_overrides") or {}).get(timeframe, data_cfg["start"])
    return get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=timeframe,
        start=start,
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )


def fetch_window(data_cfg: dict, timeframe: str) -> pd.DataFrame:
    """
    N1 / CLAUDE.md zasada 20: natywne świece od `data_cfg["min_start"]` włącznie. Filtr nakładany
    na pełny cache (bez nowego pobierania), więc zamknięte rundy zachowują swoje pliki, a nowe
    rundy nie mogą przypadkiem sięgnąć przed datę graniczną. Brak klucza `min_start` = błąd
    głośny, nie ciche „całe dane".
    """
    if "min_start" not in data_cfg:
        raise ValueError("data_cfg bez `min_start` — zasada 20 wymaga jawnej daty granicznej")
    df = fetch_native(data_cfg, timeframe)
    min_start = pd.Timestamp(data_cfg["min_start"])
    if min_start.tzinfo is None:
        min_start = min_start.tz_localize("UTC")
    return df.loc[pd.to_datetime(df["timestamp"], utc=True) >= min_start].reset_index(drop=True)


def summarize_result(result: dict, seed: int = PRIMARY_SEED) -> dict:
    """
    W1: miary raportowe dla GOTOWEGO wyniku `run_backtest`/`simulate_equity` — wydzielone
    z `run_and_summarize`, żeby jeden trening (`engine.collect_signals`) mógł obsłużyć wiele
    wariantów wykonania (`engine.simulate_equity`) bez powtarzania kosztownej części.
    """
    fold_metrics = compute_fold_metrics(result["trades"], result["folds_summary"])
    return {
        "seed": seed,
        "backtest": result,
        "fold_metrics": fold_metrics,
        "classification": classify_checkpoint(fold_metrics),
        "per_regime": summarize_by_regime(fold_metrics),
        "pooled_per_regime": summarize_pooled_by_regime(result["trades"]),
        "edge_per_regime": summarize_edge_by_regime(result["trades"]),
    }


def run_and_summarize(
    raw_ohlcv: pd.DataFrame, seed: int = PRIMARY_SEED, **run_backtest_kwargs
) -> dict:
    """
    Jeden pełny przebieg pipeline'u + wszystkie miary raportowe:
    per-fold metrics (z t_stat, Commit 2.9/Z2), klasyfikacja GO/WARUNKOWY/NO-GO
    (kryteria docs/rag/03 — NIEZMIENIONE), rozbicie per reżim oraz NOWA diagnostyka
    pooled per regime (Sharpe per trade, t-stat, N_eff — Commit 2.9/Z2+Z3).
    """
    return summarize_result(run_backtest(raw_ohlcv, seed=seed, **run_backtest_kwargs), seed)


def sweep_fold_offsets(
    raw_ohlcv: pd.DataFrame,
    offsets_days: list[float] | None = None,
    seed: int = PRIMARY_SEED,
    **run_backtest_kwargs,
) -> dict:
    """
    Sweep stabilności fold-jitter (Commit 2.9, Z1 — patrz docstring modułu):
    uruchamia pełny pipeline dla każdego offsetu startu okien walk-forward i
    raportuje rozkład `mean_sharpe` + spójność znaku. BEZ progu pass/fail —
    decyzja interpretacyjna przy użytkowniku.

    Returns:
        {
          "per_offset": pd.DataFrame [offset_days, mean_sharpe, classification,
              n_valid_folds, n_total_folds],
          "std": std mean_sharpe po offsetach z policzalnym wynikiem (ddof=1),
          "range": (min, max) mean_sharpe,
          "sign_consistency_negative": ułamek offsetów z mean_sharpe < 0,
          "n_valid_offsets": ile offsetów dało policzalny mean_sharpe,
        }
    """
    offsets = FOLD_OFFSETS_DAYS if offsets_days is None else offsets_days
    rows: list[dict] = []
    for offset in offsets:
        print(f"  ... fold_start_offset_days={offset:g}")
        summary = run_and_summarize(
            raw_ohlcv, seed=seed, fold_start_offset_days=offset, **run_backtest_kwargs
        )
        c = summary["classification"]
        rows.append(
            {
                "offset_days": offset,
                "mean_sharpe": c["mean_sharpe"],
                "classification": c["classification"],
                "n_valid_folds": c["n_valid_folds"],
                "n_total_folds": c["n_total_folds"],
            }
        )

    per_offset = pd.DataFrame(rows)
    valid = per_offset.dropna(subset=["mean_sharpe"])
    n_valid = len(valid)
    std = float(valid["mean_sharpe"].std(ddof=1)) if n_valid > 1 else float("nan")
    value_range = (
        (float(valid["mean_sharpe"].min()), float(valid["mean_sharpe"].max()))
        if n_valid > 0
        else (float("nan"), float("nan"))
    )
    sign_consistency_negative = (
        float((valid["mean_sharpe"] < 0).mean()) if n_valid > 0 else float("nan")
    )
    return {
        "per_offset": per_offset,
        "std": std,
        "range": value_range,
        "sign_consistency_negative": sign_consistency_negative,
        "n_valid_offsets": n_valid,
    }


def print_stability_report(sweep: dict) -> None:
    """Czytelny raport sweepu fold-jitter — bez werdyktu pass/fail (patrz docstring modułu)."""
    print("\n=== Stabilność fold-jitter (Commit 2.9/Z1 — zamiast pustego sweepu seedów) ===")
    print(sweep["per_offset"].to_string(index=False))
    lo, hi = sweep["range"]
    print(
        f"\nstd(mean_sharpe) po {sweep['n_valid_offsets']} offsetach = {sweep['std']:.4f}; "
        f"zakres = [{lo:.4f}, {hi:.4f}]; "
        f"spójność znaku (ujemny) = {sweep['sign_consistency_negative']:.0%}"
    )
    print(
        "[UWAGA] Celowo BEZ progu pass/fail — stary próg std<0.2 dotyczył (pustego) szumu\n"
        "seedów i nie przenosi się na realną perturbację podziału danych. Interpretacja\n"
        "rozkładu należy do użytkownika (patrz backtest/checkpoint_lib.py, docstring)."
    )
