"""
test_labeling.py

Warstwa 1 (unit) + Warstwa 3 (hypothesis property-based, wymagane przez DoD dla
labeling.py — docs/rag/05_metodologia_wytwarzania_i_testow.md) testy dla
agents/labeling.py.

Test leakage (Warstwa 2) dla compute_triple_barrier_labels żyje osobno w
agent_5_compliance/test_leakage.py::test_triple_barrier_no_leakage (C4.5) —
nie duplikowany tutaj.

Scenariusze triple-barrier są ręcznie skonstruowane (nie losowe): kilkadziesiąt
"płaskich" świec o stałym true range = 2.0 stabilizuje atr_14 do znanej,
policzalnej wartości (pobieranej dynamicznie przez compute_atr_14, nie
zahardkodowanej — atr_14 jest już zweryfikowane jako leakage-free w Commicie 3,
więc liczenie go na samym prefiksie [warmup+entry] daje dokładnie tę samą
wartość co na pełnym df), a następnie świece "w przód" są budowane względem
`upper`/`lower` policzonych z tej wartości.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.feature_miner import compute_atr_14
from agents.labeling import (
    ATR_MULTIPLIER,
    compute_triple_barrier_labels,
    effective_sample_size,
    generate_walk_forward_folds,
)

N_WARMUP = 20  # świec do ustabilizowania atr_14 (TA-Lib ATR-14 potrzebuje >=14)
ENTRY_PRICE = 100.0


def _make_df_from_ohlc(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df["volume"] = 100.0
    df["timestamp"] = pd.date_range("2026-01-01", periods=len(df), freq="5min", tz="UTC")
    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def _warmup_rows(n: int, price: float) -> list[tuple[float, float, float, float]]:
    """n płaskich świec o stałym true range = 2.0 (high=price+1, low=price-1, close=price)."""
    return [(price, price + 1.0, price - 1.0, price) for _ in range(n)]


@pytest.fixture(scope="module")
def entry_atr() -> float:
    """atr_14 w świecy entry, policzone na prefiksie [warmup + entry] (bez świec w przód —
    atr_14 jest trailing/leakage-free, więc ta wartość jest identyczna niezależnie od
    tego, co dzieje się później)."""
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE)
    ]
    df = _make_df_from_ohlc(rows)
    return compute_atr_14(df).iloc[-1]


# ---------------------------------------------------------------------------
# Warstwa 1: compute_triple_barrier_labels, scenariusze ręczne
# ---------------------------------------------------------------------------


def test_triple_barrier_upper_hit(entry_atr: float) -> None:
    upper = ENTRY_PRICE + ATR_MULTIPLIER * entry_atr
    lower = ENTRY_PRICE - ATR_MULTIPLIER * entry_atr
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE),  # entry
        (
            ENTRY_PRICE,
            upper - 1.0,
            lower + 1.0,
            ENTRY_PRICE,
        ),  # offset 1: brak trafienia
        (
            ENTRY_PRICE,
            upper + 0.5,
            lower + 1.0,
            ENTRY_PRICE,
        ),  # offset 2: upper trafiona
        (ENTRY_PRICE, upper - 1.0, lower + 1.0, ENTRY_PRICE),  # offset 3: filler
    ]
    df = _make_df_from_ohlc(rows)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=3)

    entry_idx = N_WARMUP
    assert result["label"].iloc[entry_idx] == 1.0
    assert result["exit_bar_offset"].iloc[entry_idx] == 2.0


def test_triple_barrier_lower_hit(entry_atr: float) -> None:
    upper = ENTRY_PRICE + ATR_MULTIPLIER * entry_atr
    lower = ENTRY_PRICE - ATR_MULTIPLIER * entry_atr
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE),  # entry
        (
            ENTRY_PRICE,
            upper - 1.0,
            lower + 1.0,
            ENTRY_PRICE,
        ),  # offset 1: brak trafienia
        (
            ENTRY_PRICE,
            upper - 1.0,
            lower + 1.0,
            ENTRY_PRICE,
        ),  # offset 2: brak trafienia
        (
            ENTRY_PRICE,
            upper - 1.0,
            lower - 0.5,
            ENTRY_PRICE,
        ),  # offset 3: lower trafiona
    ]
    df = _make_df_from_ohlc(rows)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=3)

    entry_idx = N_WARMUP
    assert result["label"].iloc[entry_idx] == -1.0
    assert result["exit_bar_offset"].iloc[entry_idx] == 3.0


def test_triple_barrier_vertical_timeout(entry_atr: float) -> None:
    upper = ENTRY_PRICE + ATR_MULTIPLIER * entry_atr
    lower = ENTRY_PRICE - ATR_MULTIPLIER * entry_atr
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE),  # entry
        (ENTRY_PRICE, upper - 1.0, lower + 1.0, ENTRY_PRICE),
        (ENTRY_PRICE, upper - 1.0, lower + 1.0, ENTRY_PRICE),
        (ENTRY_PRICE, upper - 1.0, lower + 1.0, ENTRY_PRICE),
    ]
    df = _make_df_from_ohlc(rows)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=3)

    entry_idx = N_WARMUP
    assert result["label"].iloc[entry_idx] == 0.0
    assert result["exit_bar_offset"].iloc[entry_idx] == 3.0


def test_triple_barrier_same_candle_tiebreak_upper_closer(entry_atr: float) -> None:
    upper = ENTRY_PRICE + ATR_MULTIPLIER * entry_atr
    lower = ENTRY_PRICE - ATR_MULTIPLIER * entry_atr
    open_k = upper - 0.1  # open bardzo blisko upper -> upper "trafiona pierwsza"
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE),  # entry
        (open_k, upper + 0.5, lower - 0.5, ENTRY_PRICE),  # obie bariery trafione naraz
    ]
    df = _make_df_from_ohlc(rows)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=1)

    entry_idx = N_WARMUP
    assert result["label"].iloc[entry_idx] == 1.0
    assert result["exit_bar_offset"].iloc[entry_idx] == 1.0


def test_triple_barrier_same_candle_tiebreak_lower_closer(entry_atr: float) -> None:
    upper = ENTRY_PRICE + ATR_MULTIPLIER * entry_atr
    lower = ENTRY_PRICE - ATR_MULTIPLIER * entry_atr
    open_k = lower + 0.1  # open bardzo blisko lower -> lower "trafiona pierwsza"
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE),  # entry
        (open_k, upper + 0.5, lower - 0.5, ENTRY_PRICE),  # obie bariery trafione naraz
    ]
    df = _make_df_from_ohlc(rows)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=1)

    entry_idx = N_WARMUP
    assert result["label"].iloc[entry_idx] == -1.0
    assert result["exit_bar_offset"].iloc[entry_idx] == 1.0


def test_triple_barrier_atr_warmup_is_nan() -> None:
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE) for _ in range(5)
    ]
    df = _make_df_from_ohlc(rows)
    atr = compute_atr_14(df)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=3)

    nan_atr_mask = atr.isna()
    assert nan_atr_mask.sum() > 0  # sanity: rzeczywiście jest warmup do przetestowania
    assert result["label"][nan_atr_mask.to_numpy()].isna().all()


def test_triple_barrier_tail_insufficient_window_is_nan() -> None:
    vertical = 3
    rows = _warmup_rows(N_WARMUP, ENTRY_PRICE) + [
        (ENTRY_PRICE, ENTRY_PRICE + 0.1, ENTRY_PRICE - 0.1, ENTRY_PRICE) for _ in range(10)
    ]
    df = _make_df_from_ohlc(rows)
    result = compute_triple_barrier_labels(df, vertical_barrier_candles=vertical)

    n = len(df)
    tail_labels = result["label"].iloc[n - vertical :]
    assert tail_labels.isna().all()


# ---------------------------------------------------------------------------
# Warstwa 1: generate_walk_forward_folds
# ---------------------------------------------------------------------------


def _make_daily_df(n_days: int) -> pd.DataFrame:
    """Jedna świeca dziennie (freq='D') — upraszcza liczenie oczekiwanej liczby foldów."""
    timestamps = pd.date_range("2026-01-01", periods=n_days, freq="D", tz="UTC")
    n = len(timestamps)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.0] * n,
            "volume": [10.0] * n,
        }
    )


def test_walk_forward_folds_chronological_and_no_overlap() -> None:
    df = _make_daily_df(200)
    folds = generate_walk_forward_folds(df, train_days=60, test_days=14, step_days=14)

    assert len(folds) > 0
    for fold in folds:
        assert fold["train_start"] < fold["train_end"] == fold["test_start"] < fold["test_end"]
        assert not (fold["train_mask"] & fold["test_mask"]).any()
        assert fold["train_mask"].sum() > 0
        assert fold["test_mask"].sum() > 0


def test_walk_forward_folds_expected_count() -> None:
    # 200 dni danych; fold i wymaga test_end = i*14 + 74 <= 199 (ostatni dzień, 0-indeksowany)
    # -> i <= 8.93 -> i = 0..8 -> 9 foldów.
    df = _make_daily_df(200)
    folds = generate_walk_forward_folds(df, train_days=60, test_days=14, step_days=14)
    assert len(folds) == 9


def test_walk_forward_folds_too_little_data_returns_empty() -> None:
    df = _make_daily_df(50)  # 60 (train) + 14 (test) = 74 > 50 dostępnych dni
    folds = generate_walk_forward_folds(df, train_days=60, test_days=14, step_days=14)
    assert folds == []


def test_walk_forward_folds_start_offset_shifts_first_fold() -> None:
    # Commit 2.9 (Z1): offset przesuwa start PIERWSZEGO foldu o dokładnie tyle dni,
    # a domyślne 0.0 zachowuje się identycznie jak przed parametryzacją.
    df = _make_daily_df(200)
    baseline = generate_walk_forward_folds(df, train_days=60, test_days=14, step_days=14)
    offset = generate_walk_forward_folds(
        df, train_days=60, test_days=14, step_days=14, start_offset_days=7.0
    )
    explicit_zero = generate_walk_forward_folds(
        df, train_days=60, test_days=14, step_days=14, start_offset_days=0.0
    )

    assert len(baseline) > 0 and len(offset) > 0
    assert offset[0]["train_start"] == baseline[0]["train_start"] + pd.Timedelta(days=7)
    # Offset skraca dostępne dane — liczba foldów nie może wzrosnąć.
    assert len(offset) <= len(baseline)
    # Domyślna wartość == jawne 0.0 (bez zmiany zachowania sprzed Commitu 2.9).
    assert len(explicit_zero) == len(baseline)
    for a, b in zip(explicit_zero, baseline, strict=True):
        assert a["train_start"] == b["train_start"]
        assert a["test_end"] == b["test_end"]


# ---------------------------------------------------------------------------
# Warstwa 1: effective_sample_size
# ---------------------------------------------------------------------------


def test_effective_sample_size_iid_noise_close_to_n() -> None:
    rng = np.random.default_rng(0)
    returns = pd.Series(rng.normal(0.0, 1.0, size=2000))
    result = effective_sample_size(returns, max_lag=20)

    assert result["n"] == 2000
    # i.i.d. -> autokorelacje bliskie 0 -> N_eff bliskie N (w granicach szumu estymacji)
    assert result["n_eff"] > 0.7 * result["n"]


def test_effective_sample_size_autocorrelated_series_much_smaller_than_n() -> None:
    rng = np.random.default_rng(0)
    noise = rng.normal(0.0, 1.0, size=2000)
    # rolling mean silnie wygładza szereg -> sąsiednie wartości mocno skorelowane
    autocorrelated = pd.Series(noise).rolling(window=20, min_periods=1).mean()
    result = effective_sample_size(autocorrelated, max_lag=20)

    assert result["n_eff"] < 0.3 * result["n"]


# ---------------------------------------------------------------------------
# Warstwa 3: hypothesis property-based test (wymagane przez DoD dla labeling.py)
# ---------------------------------------------------------------------------


def _make_synthetic_ohlcv(n_rows: int, seed: int) -> pd.DataFrame:
    """
    Mały, deterministyczny generator OHLCV — celowo zduplikowany z
    agent_5_compliance/test_leakage.py::_make_synthetic_ohlcv, żeby tests/ i
    agent_5_compliance/ pozostały wzajemnie niezależnymi plikami testowymi.
    """
    rng = np.random.default_rng(seed)
    log_returns = rng.normal(loc=0.0, scale=0.001, size=n_rows)
    close = 100.0 * np.cumprod(1.0 + log_returns)
    open_ = np.empty(n_rows)
    open_[0] = 100.0
    open_[1:] = close[:-1]
    spread = rng.uniform(0.0, 0.002, size=n_rows)
    high = np.maximum(open_, close) * (1.0 + spread)
    low = np.minimum(open_, close) * (1.0 - spread)
    volume = rng.uniform(10.0, 1000.0, size=n_rows)
    timestamp = pd.date_range("2026-01-01", periods=n_rows, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n_rows=st.integers(min_value=50, max_value=150),
    atr_multiplier=st.floats(min_value=0.1, max_value=5.0),
    vertical_barrier_candles=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=50, deadline=None)
def test_triple_barrier_label_and_offset_always_valid(
    seed: int, n_rows: int, atr_multiplier: float, vertical_barrier_candles: int
) -> None:
    """
    Własność wymagana przez DoD (docs/rag/05) dla labeling.py: niezależnie od
    losowych danych i parametrów, `label` zawsze należy do {-1.0, 0.0, 1.0, NaN},
    a `exit_bar_offset` (gdy label nie jest NaN) zawsze mieści się w
    [1, vertical_barrier_candles].
    """
    df = _make_synthetic_ohlcv(n_rows, seed)
    result = compute_triple_barrier_labels(
        df,
        atr_multiplier=atr_multiplier,
        vertical_barrier_candles=vertical_barrier_candles,
    )

    non_nan_labels = result["label"].dropna()
    assert set(non_nan_labels.unique()).issubset({-1.0, 0.0, 1.0})

    non_nan = result.dropna()
    assert (non_nan["exit_bar_offset"] >= 1).all()
    assert (non_nan["exit_bar_offset"] <= vertical_barrier_candles).all()


@given(offset_days=st.floats(min_value=0.0, max_value=30.0, allow_nan=False))
@settings(max_examples=50, deadline=None)
def test_walk_forward_folds_offset_preserves_chronology_invariants(
    offset_days: float,
) -> None:
    """
    Commit 2.9 (Z1), własność wymagana przez DoD (docs/rag/05) dla labeling.py:
    dla DOWOLNEGO nieujemnego offsetu każdy wygenerowany fold zachowuje niezmienniki
    walk-forward (train ściśle przed test, brak nakładania masek wewnątrz foldu),
    a pierwszy fold startuje dokładnie o `offset_days` później niż pierwsza świeca.
    Offset perturbuje WYRÓWNANIE granic foldów, nigdy ich chronologię.
    """
    timestamps = pd.date_range("2026-01-01", periods=200, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 10.0,
        }
    )
    folds = generate_walk_forward_folds(
        df, train_days=60, test_days=14, step_days=14, start_offset_days=offset_days
    )

    for fold in folds:
        assert fold["train_start"] < fold["train_end"] == fold["test_start"] < fold["test_end"]
        assert not (fold["train_mask"] & fold["test_mask"]).any()

    if folds:
        expected_start = timestamps[0] + pd.Timedelta(days=offset_days)
        assert folds[0]["train_start"] == expected_start
