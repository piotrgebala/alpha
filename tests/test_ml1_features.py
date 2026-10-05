"""Testy jednostkowe agents/ml1_features.py (runda ML1, zadanie 028). Przeciek: agent_5_compliance/test_leakage.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.ml1_features import (
    ANNUALIZATION,
    ML1_EXTERNAL,
    ML1_FEATURES,
    attach_metrics_1d,
    calibration_table,
    clean_metrics,
    compute_oi_change_24h,
    compute_rv_30d,
    compute_vrp_30d,
    confidence_threshold,
    dedup_features,
    signal_hits,
)
from agents.ml_optimizer import REVERSION_FEATURES


def test_feature_list_is_the_card_list() -> None:
    """Karta §4.1: dokładnie 11 cech, 4 REVERSION + 7 spoza wykresu, bez toptrader_ls_log."""
    assert len(ML1_FEATURES) == 11 == len(set(ML1_FEATURES))
    assert ML1_FEATURES[:4] == REVERSION_FEATURES
    assert ML1_EXTERNAL == [
        "funding_rate",
        "oi_change_24h",
        "global_ls_log",
        "taker_imbalance_24h",
        "vrp_30d",
        "ex_supply_change_7d",
        "fng_level",
    ]
    assert "toptrader_ls_log" not in ML1_FEATURES


def _metrics(day: str, oi: list[float], ls: list[float], tk: list[float], minutes: list[int]):
    ts = pd.Timestamp(day, tz="UTC") + pd.to_timedelta(minutes, unit="min")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "sum_open_interest": oi,
            "count_long_short_ratio": ls,
            "sum_taker_long_short_vol_ratio": tk,
        }
    )


def test_clean_metrics_nonpositive_to_nan_and_missing_column() -> None:
    m = _metrics("2024-01-01", [0.0, 5.0], [-1.0, 2.0], [1.0, 1.0], [5, 10])
    out = clean_metrics(m)
    assert np.isnan(out.loc[0, "sum_open_interest"]) and np.isnan(
        out.loc[0, "count_long_short_ratio"]
    )
    with pytest.raises(ValueError, match="brak kolumn"):
        clean_metrics(m.drop(columns=["count_long_short_ratio"]))


def test_attach_metrics_last_valid_reading_and_taker_mean() -> None:
    """Ostatni WAŻNY odczyt (≤ 0 pomijany), średnia log z odczytów świecy; świeca bez odczytów → NaN."""
    m = _metrics("2024-01-01", [10.0, 20.0, 0.0], [1.5, 2.0, 3.0], [2.0, 0.5, 4.0], [5, 60, 1435])
    df = pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=2, freq="1D", tz="UTC")})
    out = attach_metrics_1d(df, m)
    assert out.loc[0, "oi_close"] == 20.0  # odczyt 0.0 o 23:55 = błąd archiwum → pominięty
    assert out.loc[0, "global_ls_close"] == 3.0
    assert out.loc[0, "taker_log_mean"] == pytest.approx(np.mean(np.log([2.0, 0.5, 4.0])))
    assert out.loc[1, ["oi_close", "global_ls_close", "taker_log_mean"]].isna().all()


def test_oi_change_is_log_ratio_of_consecutive_candles() -> None:
    df = pd.DataFrame({"oi_close": [100.0, 110.0, np.nan, 121.0]})
    out = compute_oi_change_24h(df)
    assert np.isnan(out.iloc[0]) and np.isnan(out.iloc[2]) and np.isnan(out.iloc[3])
    assert out.iloc[1] == pytest.approx(np.log(1.1))


def test_vrp_uses_30_daily_returns_annualized_sqrt365() -> None:
    rng = np.random.default_rng(3)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 40)))
    df = pd.DataFrame({"close": close, "dvol_d": np.full(40, 60.0)})
    rv = compute_rv_30d(df)
    assert rv.iloc[:30].isna().all() and rv.iloc[30:].notna().all()
    manual = np.std(np.diff(np.log(close[:31])), ddof=1) * np.sqrt(365.0)
    assert rv.iloc[30] == pytest.approx(manual)
    assert ANNUALIZATION == pytest.approx(np.sqrt(365.0))
    assert compute_vrp_30d(df).iloc[30] == pytest.approx(0.60 - manual)


def test_dedup_drops_later_duplicate_in_card_order() -> None:
    x = np.arange(50, dtype=float)
    frame = pd.DataFrame({"a": x, "b": np.sin(x), "c": x**2, "d": -x})
    assert dedup_features(frame, ["a", "b", "c", "d"]) == ["a", "b"]
    assert dedup_features(frame, ["b", "d", "a"]) == ["b", "d"]


def test_confidence_threshold_errors() -> None:
    with pytest.raises(ValueError):
        confidence_threshold([], 0.2)
    with pytest.raises(ValueError):
        confidence_threshold([0.5, 0.6], 1.0)


@settings(max_examples=60, deadline=None)
@given(
    st.lists(st.floats(0.34, 1.0, allow_nan=False), min_size=20, max_size=400, unique=True),
    st.sampled_from([0.1, 0.2, 0.25, 0.5]),
)
def test_threshold_admits_top_share(conf: list[float], share: float) -> None:
    """Właściwość: przy unikalnych pewnościach ≥ próg przechodzi ⌈share·n⌉ ± 1 sygnałów, nigdy dolny kraniec."""
    c = np.array(conf)
    thr = confidence_threshold(c, share)
    admitted = int((c >= thr).sum())
    assert abs(admitted - share * len(c)) <= 1.0 + 1e-9
    assert c.min() < thr <= c.max()


def test_signal_hits_barrier_and_timeout() -> None:
    direction = np.array([1, -1, 1, -1, 1, 1])
    label = np.array([1, 1, 0, 0, 0, -1])
    entry = np.array([100.0] * 6)
    timeout = np.array([50.0, 50.0, 101.0, 101.0, 100.0, 200.0])
    # ±1: zgodność z etykietą (cena timeoutu bez znaczenia); 0: znak ruchu do zamknięcia po V; zero = pudło
    assert signal_hits(direction, label, entry, timeout).tolist() == [
        True,
        False,
        True,
        False,
        False,
        False,
    ]


@settings(max_examples=60, deadline=None)
@given(
    st.lists(st.floats(0.34, 1.0, allow_nan=False), min_size=10, max_size=300),
    st.integers(2, 6),
    st.randoms(use_true_random=False),
)
def test_calibration_partitions_signals(conf: list[float], k: int, rnd) -> None:
    """Właściwość: kubełki rozłączne i wyczerpujące, rozmiary różnią się o ≤ 1, granice rosnące."""
    if len(conf) < k:
        return
    hits = np.array([rnd.random() < 0.5 for _ in conf])
    tab = calibration_table(np.array(conf), hits, k)
    assert tab["n"].sum() == len(conf)
    assert tab["n"].max() - tab["n"].min() <= 1
    assert (np.diff(tab["pewnosc_od"].to_numpy()) >= 0).all()
    assert tab["pewnosc_do"].iloc[:-1].le(tab["pewnosc_od"].iloc[1:].to_numpy()).all()
    weighted = float((tab["trafnosc"] * tab["n"]).sum() / tab["n"].sum())
    assert weighted == pytest.approx(hits.mean())


def test_calibration_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        calibration_table(np.array([0.5, 0.6]), np.array([True]), 2)
    with pytest.raises(ValueError):
        calibration_table(np.array([0.5]), np.array([True]), 5)
