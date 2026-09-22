"""
test_regime_coherence.py

Testy dla agents/regime_coherence.py (Z16, Backlog II). Czysto syntetyczne dane —
sprawdzają podział na epizody, arytmetykę okien mieszczących się w epizodzie, kryterium
dopuszczalności reguły oraz guard na nieciągłość serii. Warstwa 1 + Warstwa 3
(property-based, `hypothesis`) — patrz docs/rag/05.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.regime_coherence import (
    assert_contiguous_timestamps,
    coherence_table,
    is_rule_admissible,
    regime_episodes,
    windows_fully_inside,
)


def _regime(seq: list[str]) -> pd.Series:
    return pd.Series(seq, name="regime")


# ---------------------------------------------------------------------------
# regime_episodes
# ---------------------------------------------------------------------------


def test_regime_episodes_splits_consecutive_runs() -> None:
    reg = _regime(["range", "range", "trend", "trend", "trend", "range"])
    ep = regime_episodes(reg)
    assert list(ep["regime"]) == ["range", "trend", "range"]
    assert list(ep["length"]) == [2, 3, 1]
    assert list(ep["start_pos"]) == [0, 2, 5]


def test_regime_episodes_single_uniform_run() -> None:
    ep = regime_episodes(_regime(["trend"] * 7))
    assert len(ep) == 1
    assert ep.iloc[0]["length"] == 7


def test_regime_episodes_empty_input_is_empty_frame_not_error() -> None:
    ep = regime_episodes(pd.Series([], dtype=object))
    assert len(ep) == 0
    assert list(ep.columns) == ["regime", "start_pos", "length"]


def test_regime_episodes_alternating_gives_unit_episodes() -> None:
    ep = regime_episodes(_regime(["trend", "range"] * 5))
    assert len(ep) == 10
    assert set(ep["length"]) == {1}


# ---------------------------------------------------------------------------
# windows_fully_inside
# ---------------------------------------------------------------------------


def test_windows_fully_inside_manual_arithmetic() -> None:
    # epizody o długościach 5 i 3, horyzont 3 -> (5-3+1) + (3-3+1) = 3 + 1 = 4
    assert windows_fully_inside([5, 3], horizon=3) == 4


def test_windows_fully_inside_zero_when_all_episodes_too_short() -> None:
    """Sedno Z16: epizody krótsze od horyzontu nie dają ANI JEDNEGO poprawnego okna."""
    assert windows_fully_inside([1, 2, 2, 5], horizon=12) == 0


def test_windows_fully_inside_horizon_one_counts_every_candle() -> None:
    assert windows_fully_inside([4, 6], horizon=1) == 10


def test_windows_fully_inside_rejects_nonpositive_horizon() -> None:
    with pytest.raises(ValueError):
        windows_fully_inside([5], horizon=0)


def test_windows_fully_inside_empty_is_zero() -> None:
    assert windows_fully_inside([], horizon=5) == 0


# ---------------------------------------------------------------------------
# coherence_table
# ---------------------------------------------------------------------------


def test_coherence_table_flags_incoherent_rule() -> None:
    """
    Reprodukuje kształt problemu zmierzonego na realnych danych: epizody krótsze niż
    okno etykiety => coherent=False i zero poprawnych okien.
    """
    reg = _regime((["trend", "trend", "range", "range", "range"] * 20))
    table = coherence_table(reg, horizons=(12,)).set_index("regime")
    for name in ("trend", "range"):
        assert table.loc[name, "coherent"] is np.False_ or not table.loc[name, "coherent"]
        assert table.loc[name, "n_windows_inside"] == 0
        assert table.loc[name, "median_length"] < 12


def test_coherence_table_flags_coherent_rule() -> None:
    reg = _regime((["trend"] * 20 + ["range"] * 20) * 3)
    table = coherence_table(reg, horizons=(12,)).set_index("regime")
    for name in ("trend", "range"):
        assert table.loc[name, "coherent"]
        assert table.loc[name, "median_length"] == 20
        # 3 epizody po 20 świec, horyzont 12 -> 3 * (20-12+1) = 27
        assert table.loc[name, "n_windows_inside"] == 27


def test_coherence_table_missing_regime_gives_nan_not_zero() -> None:
    """Reżim, który nie wystąpił, musi dać NaN — 0 udawałoby pomiar."""
    table = coherence_table(_regime(["range"] * 30), horizons=(12,)).set_index("regime")
    assert math.isnan(table.loc["trend", "median_length"])
    assert table.loc["trend", "n_episodes"] == 0
    assert not table.loc["trend", "coherent"]


def test_coherence_table_one_row_per_regime_and_horizon() -> None:
    table = coherence_table(_regime(["trend", "range"] * 30), horizons=(3, 12, 48))
    assert len(table) == 6
    assert set(table["horizon_candles"]) == {3, 12, 48}


def test_coherence_table_horizon_minutes_assumes_5m_candles() -> None:
    table = coherence_table(_regime(["range"] * 20), horizons=(12,))
    assert table.iloc[0]["horizon_minutes"] == 60


# ---------------------------------------------------------------------------
# is_rule_admissible
# ---------------------------------------------------------------------------


def test_rule_inadmissible_when_episodes_too_short() -> None:
    reg = _regime((["trend", "trend", "range", "range"] * 50))
    verdict = is_rule_admissible(reg, horizon=12)
    assert verdict["admissible"] is False
    assert all(not v["coherent"] for v in verdict["per_regime"].values())


def test_rule_inadmissible_when_regime_too_rare_despite_long_episodes() -> None:
    """
    Oba warunki są konieczne: długie epizody nie wystarczą, jeśli reżim obejmuje
    znikomy ułamek świec (fold nie miałby obserwacji — por. MIN_TRAIN_ROWS).
    """
    reg = _regime(["trend"] * 20 + ["ambiguous"] * 2000 + ["range"] * 20)
    verdict = is_rule_admissible(reg, horizon=12, min_regime_share=0.05)
    assert verdict["admissible"] is False
    for name in ("trend", "range"):
        assert verdict["per_regime"][name]["coherent"]
        assert not verdict["per_regime"][name]["enough_share"]


def test_rule_admissible_when_both_conditions_hold() -> None:
    reg = _regime((["trend"] * 20 + ["range"] * 20) * 5)
    verdict = is_rule_admissible(reg, horizon=12, min_regime_share=0.05)
    assert verdict["admissible"] is True


# ---------------------------------------------------------------------------
# guard na nieciągłość serii
# ---------------------------------------------------------------------------


def test_assert_contiguous_passes_on_clean_series() -> None:
    ts = pd.Series(pd.date_range("2026-01-01", periods=50, freq="5min", tz="UTC"))
    assert_contiguous_timestamps(ts)  # nie podnosi


def test_assert_contiguous_detects_hole_in_the_middle() -> None:
    """
    Dziura w środku zlepiłaby dwa epizody w jeden i ZAWYŻYŁA mierzoną długość —
    czyli zniekształciła dokładnie tę wielkość, o którą chodzi w Z16.
    """
    head = pd.date_range("2026-01-01", periods=10, freq="5min", tz="UTC")
    tail = pd.date_range("2026-01-01 05:00", periods=10, freq="5min", tz="UTC")
    with pytest.raises(ValueError, match="ciągła"):
        assert_contiguous_timestamps(pd.Series(head.append(tail)))


def test_assert_contiguous_trivial_for_short_series() -> None:
    assert_contiguous_timestamps(pd.Series([], dtype="datetime64[ns, UTC]"))
    assert_contiguous_timestamps(pd.Series(pd.date_range("2026-01-01", periods=1, tz="UTC")))


# ---------------------------------------------------------------------------
# Warstwa 3: property-based
# ---------------------------------------------------------------------------


@given(st.lists(st.sampled_from(["trend", "range", "ambiguous"]), min_size=0, max_size=200))
@settings(max_examples=200, deadline=None)
def test_episodes_partition_the_series_exactly(seq: list[str]) -> None:
    """Epizody muszą być dokładnym podziałem serii — nic nie zgubione, nic podwojone."""
    ep = regime_episodes(_regime(seq))
    assert int(ep["length"].sum() if len(ep) else 0) == len(seq)
    # rekonstrukcja
    rebuilt: list[str] = []
    for _, row in ep.iterrows():
        rebuilt.extend([row["regime"]] * int(row["length"]))
    assert rebuilt == seq


@given(
    lengths=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=40),
    h_low=st.integers(min_value=1, max_value=50),
    extra=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=200, deadline=None)
def test_windows_inside_monotonically_nonincreasing_in_horizon(
    lengths: list[int], h_low: int, extra: int
) -> None:
    """Dłuższe okno etykiety nie może zmieścić się w WIĘCEJ miejscach niż krótsze."""
    assert windows_fully_inside(lengths, h_low) >= windows_fully_inside(lengths, h_low + extra)


@given(
    lengths=st.lists(st.integers(min_value=1, max_value=60), min_size=1, max_size=30),
    horizon=st.integers(min_value=1, max_value=60),
)
@settings(max_examples=200, deadline=None)
def test_windows_inside_never_exceeds_total_candles(lengths: list[int], horizon: int) -> None:
    assert windows_fully_inside(lengths, horizon) <= sum(lengths)


@given(st.lists(st.sampled_from(["trend", "range"]), min_size=1, max_size=150))
@settings(max_examples=150, deadline=None)
def test_horizon_one_is_always_coherent_and_counts_everything(seq: list[str]) -> None:
    """Przy horyzoncie 1 świecy spójność jest trywialnie spełniona dla każdej reguły."""
    table = coherence_table(_regime(seq), horizons=(1,))
    for _, row in table.iterrows():
        if row["n_episodes"] > 0:
            assert row["coherent"]
            assert row["n_windows_inside"] == row["regime_candles"]
