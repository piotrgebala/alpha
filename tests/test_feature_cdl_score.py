"""
test_feature_cdl_score.py

Runda A1: `compute_cdl_score_6` (agents/feature_miner.py) — suma znaków sześciu formacji
świecowych TA-Lib. Test przecieku mieszka w agent_5_compliance/test_leakage.py (parametryzowany
po FEATURE_FUNCTIONS, obejmuje tę cechę automatycznie — CLAUDE.md zasada 2). Tutaj: wartości na
świecach zbudowanych ręcznie, normalizacja wariantu ±80 do ±1, doji poza wskaźnikiem, kontrakt
(nazwa, indeks, długość) i własność w hypothesis na losowych świecach.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import talib
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.feature_miner import CDL_SCORE_6_PATTERNS, FEATURE_FUNCTIONS, compute_cdl_score_6


def _flat(n: int) -> dict[str, np.ndarray]:
    """n białych świec 100 → 100,5 z cieniami 0,5 — żadna formacja z zestawu nie odpala."""
    return {
        "open": np.full(n, 100.0),
        "high": np.full(n, 101.0),
        "low": np.full(n, 99.5),
        "close": np.full(n, 100.5),
    }


def _df(cols: dict[str, np.ndarray]) -> pd.DataFrame:
    n = len(cols["open"])
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="4h", tz="UTC"),
            **cols,
            "volume": np.full(n, 10.0),
        }
    )


def _engulfing_fixture() -> pd.DataFrame:
    c = _flat(14)
    o, cl, h, lo = c["open"], c["close"], c["high"], c["low"]
    # 5: czarna 101 → 100 po białej 100 → 100,5: korpus obejmuje z RÓWNOŚCIĄ na dole
    #    (close == open poprzedniej) — TA-Lib 0.7.1 zwraca −80 („słabsze" objęcie bessy)
    o[5], cl[5], h[5], lo[5] = 101.0, 100.0, 101.2, 99.8
    # 6: biała 99,7 → 101,5 obejmuje korpus 5 (100–101) z zapasem — objęcie hossy +100
    o[6], cl[6], h[6], lo[6] = 99.7, 101.5, 101.7, 99.6
    # 11 biała 100 → 101, 12 czarna 101,3 → 99,7 obejmuje ją — objęcie bessy −100
    o[11], cl[11], h[11], lo[11] = 100.0, 101.0, 101.2, 99.8
    o[12], cl[12], h[12], lo[12] = 101.3, 99.7, 101.4, 99.6
    return _df(c)


def _raw(df: pd.DataFrame, fn: str) -> np.ndarray:
    return getattr(talib, fn)(
        df["open"].to_numpy(float),
        df["high"].to_numpy(float),
        df["low"].to_numpy(float),
        df["close"].to_numpy(float),
    )


def test_fixture_is_what_it_claims_including_the_80_variant() -> None:
    raw = _raw(_engulfing_fixture(), "CDLENGULFING")
    assert raw[5] == -80 and raw[6] == 100 and raw[12] == -100
    assert all(raw[i] == 0 for i in range(len(raw)) if i not in (5, 6, 12))


def test_score_is_sign_sum_with_80_normalised_to_1() -> None:
    s = compute_cdl_score_6(_engulfing_fixture())
    assert s.name == "cdl_score_6"
    assert s.iloc[5] == -1.0 and s.iloc[6] == 1.0 and s.iloc[12] == -1.0
    assert (s.drop(index=[5, 6, 12]) == 0.0).all()


def test_doji_is_present_in_talib_but_absent_from_the_score() -> None:
    c = _flat(30)
    c["open"][20], c["close"][20], c["high"][20], c["low"][20] = 100.0, 100.0, 101.0, 99.0
    df = _df(c)
    assert _raw(df, "CDLDOJI")[20] == 100  # formacja jest…
    assert compute_cdl_score_6(df).iloc[20] == 0.0  # …ale nie ma kierunku, więc się nie liczy


def test_registered_under_its_name() -> None:
    assert FEATURE_FUNCTIONS["cdl_score_6"] is compute_cdl_score_6
    assert "CDLDOJI" not in CDL_SCORE_6_PATTERNS and len(CDL_SCORE_6_PATTERNS) == 6


@given(seed=st.integers(0, 10_000), n=st.integers(15, 80))
@settings(max_examples=40, deadline=None)
def test_score_is_bounded_integer_sum_of_pattern_signs(seed: int, n: int) -> None:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, n))
    open_ = np.r_[100.0, close[:-1]] * (1.0 + rng.normal(0.0, 0.003, n))
    high = np.maximum(open_, close) * (1.0 + rng.uniform(0.0, 0.01, n))
    low = np.minimum(open_, close) * (1.0 - rng.uniform(0.0, 0.01, n))
    df = _df({"open": open_, "high": high, "low": low, "close": close})

    s = compute_cdl_score_6(df)
    assert len(s) == n and s.index.equals(df.index)
    assert np.all(np.mod(s.to_numpy(), 1.0) == 0.0)
    assert s.abs().max() <= len(CDL_SCORE_6_PATTERNS)
    raw = np.column_stack([np.sign(_raw(df, fn)) for fn in CDL_SCORE_6_PATTERNS])
    assert np.array_equal(s.to_numpy(), raw.sum(axis=1))
    assert np.all(s.to_numpy()[(raw != 0).sum(axis=1) == 0] == 0.0)
