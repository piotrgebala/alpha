"""Testy `backtest/liq_binance.py` (zadanie 017, runda LP1) — bez sieci."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

import dataclasses

from backtest.liq_binance import (
    Tier,
    binance_distance,
    binance_liq_price,
    bracket,
    contingency,
    crossing_flags,
    flagged_cells,
    flat_distance,
    forward_extremes,
    parse_tiers,
    tier_key,
)

# Dwa pierwsze progi BTC z migawki freqtrade 84b4628 (przepisane ręcznie).
RAW = {
    "BTC/USDT:USDT": [
        {
            "minNotional": 300000.0,
            "maxNotional": 800000.0,
            "maintenanceMarginRate": 0.005,
            "maxLeverage": 100.0,
            "info": {"cum": 300.0},
        },
        {
            "minNotional": 0.0,
            "maxNotional": 300000.0,
            "maintenanceMarginRate": 0.004,
            "maxLeverage": 150.0,
            "info": {"cum": "0.0"},
        },
    ],
    "BTC/USDC:USDC": [],
}


def test_tier_key():
    assert tier_key("BTCUSDT") == "BTC/USDT:USDT"
    assert tier_key("1000BONKUSDT") == "1000BONK/USDT:USDT"
    with pytest.raises(ValueError):
        tier_key("BTCUSDC")


def test_parse_and_bracket():
    tiers = parse_tiers(RAW)
    assert list(tiers) == ["BTC/USDT:USDT"]  # USDC odrzucone
    t = tiers["BTC/USDT:USDT"]
    assert [x.floor for x in t] == [0.0, 300000.0]  # posortowane
    assert bracket(t, 10_000).mmr == 0.004
    assert bracket(t, 300_000).mmr == 0.005  # granica należy do wyższego progu
    assert bracket(t, 299_999.99).cum == 0.0
    with pytest.raises(ValueError):
        bracket(t, 800_000)


def test_hand_computed_btc_tier1_2x():
    # Ręcznie: long 2×, MMR 0,4 %, cum 0 → (0,5 − 0,004)/(1 − 0,004) = 0,496/0,996 = 0,49799197
    assert binance_distance(2.0, 0.004, 0.0, 10_000, +1) == pytest.approx(0.496 / 0.996, abs=1e-12)
    assert binance_distance(2.0, 0.004, 0.0, 10_000, +1) == pytest.approx(0.49799197, abs=1e-8)
    # short: 0,496 / 1,004 = 0,49402390
    assert binance_distance(2.0, 0.004, 0.0, 10_000, -1) == pytest.approx(0.49402390, abs=1e-8)


def test_hand_computed_btc_tier2_3x_with_cum():
    # Ręcznie: long 3×, N = 500 000, MMR 0,5 %, cum 300:
    # (1/3 + 300/500 000 − 0,005)/(0,995) = (0,3333333 + 0,0006 − 0,005)/0,995 = 0,3289333/0,995 = 0,33058626
    assert binance_distance(3.0, 0.005, 300.0, 500_000, +1) == pytest.approx(0.33058626, abs=1e-8)


def test_flat_distance():
    assert flat_distance(2.0) == pytest.approx(0.49)
    assert flat_distance(3.0) == pytest.approx(1 / 3 - 0.01)


@given(
    entry=st.floats(0.001, 1e5),
    lev=st.floats(1.0, 20.0),
    mmr=st.floats(0.001, 0.05),
    cum=st.floats(0.0, 1e4),
    qty=st.floats(0.01, 1e4),
    side=st.sampled_from([1, -1]),
)
def test_distance_matches_liq_price_formula(entry, lev, mmr, cum, qty, side):
    """Druga droga: odległość z ceny LP = binance_distance (ta sama algebra, inny zapis)."""
    n = qty * entry
    lp = binance_liq_price(entry, lev, mmr, cum, qty, side)
    dist = (1 - lp / entry) if side == 1 else (lp / entry - 1)
    assert dist == pytest.approx(binance_distance(lev, mmr, cum, n, side), rel=1e-9, abs=1e-12)


def test_equity_equals_maintenance_at_liq_price():
    """Definicja: w cenie LP kapitał pozycji = wymagany depozyt (N_mark·MMR − cum)."""
    entry, lev, mmr, cum, qty = 100.0, 3.0, 0.02, 50.0, 30.0
    for side in (1, -1):
        lp = binance_liq_price(entry, lev, mmr, cum, qty, side)
        equity = qty * entry / lev + side * qty * (lp - entry)
        assert equity == pytest.approx(qty * lp * mmr - cum, abs=1e-9)


def test_forward_extremes_and_crossings():
    idx = pd.date_range("2021-01-01", periods=5, tz="UTC")
    close = pd.DataFrame({"A": [100.0, 100, 100, 100, 100]}, index=idx)
    low = pd.DataFrame({"A": [99.0, 60, 98, 97, 96]}, index=idx)
    high = pd.DataFrame({"A": [101.0, 102, 150, 101, 101]}, index=idx)
    lo1, hi1 = forward_extremes(low, high, 1)
    assert lo1["A"].iloc[0] == 60 and np.isnan(lo1["A"].iloc[-1])
    lo2, hi2 = forward_extremes(low, high, 2)
    assert lo2["A"].iloc[0] == 60 and hi2["A"].iloc[0] == 150 and np.isnan(lo2["A"].iloc[3])
    lx, sx = crossing_flags(close, lo1, hi1, 0.4, 0.49)
    assert lx["A"].tolist() == [True, False, False, False, False]
    assert sx["A"].tolist() == [False, True, False, False, False]
    # próg per symbol (Series)
    lx2, _ = crossing_flags(close, lo1, hi1, pd.Series({"A": 0.41}), pd.Series({"A": 0.9}))
    assert not lx2["A"].iloc[0]


def test_contingency():
    idx = pd.RangeIndex(4)
    a = pd.DataFrame({"X": [True, True, False, False]}, index=idx)
    b = pd.DataFrame({"X": [True, False, True, False]}, index=idx)
    v = pd.DataFrame({"X": [True, True, True, False]}, index=idx)
    assert contingency(a, b, v) == {"n": 3, "tylko_last": 1, "tylko_mark": 1, "oba": 1, "zaden": 0}


def test_bracket_empty_list_is_value_error():
    with pytest.raises(ValueError):
        bracket([], 1_000)


def test_flagged_cells_respects_valid_mask():
    idx = pd.date_range("2021-01-01", periods=3, tz="UTC")
    flags = pd.DataFrame({"A": [True, False, True], "B": [False, True, False]}, index=idx)
    valid = pd.DataFrame({"A": [True, True, False], "B": [True, True, True]}, index=idx)
    assert flagged_cells(flags, valid) == [(idx[0], "A"), (idx[1], "B")]


def test_tier_dataclass_frozen():
    t = Tier(0, 1, 0.01, 0, 10)
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.mmr = 0.02  # type: ignore[misc]
