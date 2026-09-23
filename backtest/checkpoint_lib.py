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

import numpy as np
import pandas as pd
import yaml

from agents.labeling import ATR_MULTIPLIER, effective_sample_size
from agents.risk_controller import MIN_BARRIER_TO_COST_RATIO, is_cost_feasible
from backtest.costs import DEFAULT_TIMEOUT_LEG, gate_cost_fraction
from backtest.engine import DEFAULT_EXECUTION_MODEL, REGIME_ALL, run_backtest
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


def build_rule_signals(
    df: pd.DataFrame,
    folds_summary: list[dict],
    score_col: str,
    *,
    confidence: float = 1.0,
    regime: str = REGIME_ALL,
    execution_model: str = DEFAULT_EXECUTION_MODEL,
    timeout_leg: str = DEFAULT_TIMEOUT_LEG,
    min_barrier_to_cost_ratio: float = MIN_BARRIER_TO_COST_RATIO,
) -> tuple[list[dict], dict]:
    """
    A1: sygnały kandydujące z REGUŁY (bez modelu) w formacie `engine.simulate_equity`:
    kierunek = sign(df[score_col]), pewność stała (`confidence`; reguła nie ma posteriora).

    Populacja świec = DOKŁADNIE okna testowe AKTYWNYCH foldów pipeline'u modelowego
    (`[test_start, test_end)` jak w `generate_walk_forward_folds`), z etykietą i ATR nie-NaN,
    po bramce kosztowej silnika (`is_cost_feasible`) — te same filtry co
    `engine._collect_candidate_signals`, żeby reguła i model były porównywalne co do populacji
    (pierwsze `train_days` to wyłącznie trening modelu; reguła też ich nie ocenia).

    `df` musi być tym, co zwraca `collect_signals` (kolumny `timestamp`, `close`, `atr_14`,
    `label`, `exit_bar_offset`, `score_col`; indeks 0..n−1 — `original_index` jest pozycyjny
    w silniku). Zwraca (sygnały posortowane po `timestamp`, lejek: n_rows_window,
    n_no_signal, n_label_nan, n_cost_gated, n_signals).
    """
    if score_col not in df.columns:
        raise ValueError(f"df bez kolumny {score_col!r}")
    if not df.index.equals(pd.RangeIndex(len(df))):
        raise ValueError("df musi mieć indeks 0..n-1 (original_index jest pozycyjny w silniku)")
    active = [f for f in folds_summary if not f["skipped"]]
    if not active:
        raise ValueError("brak aktywnych foldów — reguła nie ma okna OOS do oceny")

    ts = df["timestamp"]
    fold_of = pd.Series(np.nan, index=df.index, dtype=float)
    for fold in sorted(active, key=lambda f: f["test_start"]):
        mask = (ts >= fold["test_start"]) & (ts < fold["test_end"]) & fold_of.isna()
        fold_of[mask] = fold["fold_idx"]
    in_window = fold_of.notna()

    cost_fraction = gate_cost_fraction(execution_model, timeout_leg)
    funnel = {
        "n_rows_window": int(in_window.sum()),
        "n_no_signal": 0,
        "n_label_nan": 0,
        "n_cost_gated": 0,
        "n_signals": 0,
    }
    signals: list[dict] = []
    for idx, row in df.loc[in_window].iterrows():
        score = row[score_col]
        if pd.isna(score) or score == 0:
            funnel["n_no_signal"] += 1
            continue
        if pd.isna(row["label"]) or pd.isna(row["atr_14"]):
            funnel["n_label_nan"] += 1
            continue
        if not is_cost_feasible(
            atr_14=row["atr_14"],
            entry_price=row["close"],
            cost_fraction=cost_fraction,
            atr_multiplier=ATR_MULTIPLIER,
            min_barrier_to_cost_ratio=min_barrier_to_cost_ratio,
        ):
            funnel["n_cost_gated"] += 1
            continue
        signals.append(
            {
                "original_index": idx,
                "timestamp": row["timestamp"],
                "regime": regime,
                "fold_idx": int(fold_of[idx]),
                "signal_direction": float(np.sign(score)),
                "signal_confidence": float(confidence),
                "entry_price": row["close"],
                "atr_14": row["atr_14"],
                "label": row["label"],
                "exit_bar_offset": row["exit_bar_offset"],
            }
        )
        funnel["n_signals"] += 1
    signals.sort(key=lambda s: s["timestamp"])
    return signals, funnel


def summarize_trade_returns(summary: dict) -> dict:
    """
    N1/A1: statystyki zwrotu netto PER TRANSAKCJA (% nominału wejścia) z gotowego wyniku
    `summarize_result` — kryterium z wytycznej CLAUDE.md (dwa warunki: t_neff zwrotu netto
    i `ci_low(p)` wobec progu) potrzebuje r̄, se, t, t_neff obok trafności
    z `summarize_edge_by_regime`. `p* = (L̄ + C)/(W̄ + L̄)` to próg uogólniony (ADR docs/rag/03,
    N1) — przy wypłatach asymetrycznych `break_even_p = 0,5(1 + C/B)` jest tylko diagnostyką.

    Wymaga jednej grupy reżimu w `edge_per_regime` (pipeline bez bramki, `REGIME_ALL`) —
    przy dwóch reżimach liczby pooled nie mają jednego progu; fail loud.
    """
    edge = summary["edge_per_regime"]
    if len(edge) != 1:
        raise ValueError(
            f"summarize_trade_returns oczekuje jednej grupy reżimu, dostałem {len(edge)}"
        )
    res = summary["backtest"]
    trades = res["trades"]
    real = trades.loc[~trades["kill_switch_active"]].copy()
    notional = real["position_size"] * real["entry_price"]
    real["gross_ret"] = real["gross_pnl"] / notional
    real["net_ret"] = real["net_pnl"] / notional
    real["cost_ret"] = real["cost"] / notional
    e = edge.iloc[0]
    pooled = summary["pooled_per_regime"].iloc[0]
    n = len(real)
    r = real["net_ret"]
    se = float(r.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    t = float(r.mean() / se) if se and se > 0 else float("nan")
    # Jak `metrics.summarize_pooled_by_regime`: N_eff ograniczone do n. Ujemna autokorelacja
    # zwrotów (A1a: nakładające się pozycje z kolejnych świec z formacją) daje ze wzoru
    # N / (1 + 2Σρ) wartość > n, a to zawyżałoby |t_neff| ponad |t| — korekta ma tylko
    # ODEJMOWAĆ pewność, nigdy dodawać. Wykryte po przebiegu A1 (Poprawka 2, raportowa).
    n_eff = min(float(effective_sample_size(r)["n_eff"]), float(n)) if n > 1 else float("nan")
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
        "r_mean": float(r.mean()) if n else float("nan"),
        "r_median": float(r.median()) if n else float("nan"),
        "r_std": float(r.std(ddof=1)) if n > 1 else float("nan"),
        "r_p5": float(r.quantile(0.05)) if n else float("nan"),
        "r_p95": float(r.quantile(0.95)) if n else float("nan"),
        "se": se,
        "t": t,
        "n_eff": n_eff,
        "t_neff": t_neff,
        "t_equity": float(pooled["t_stat"]),
        "t_neff_equity": float(pooled["t_stat_neff"]),
        "edge": edge,
        "pooled": summary["pooled_per_regime"],
        "classification": summary["classification"],
        "real": real,
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
