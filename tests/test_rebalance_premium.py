"""
test_rebalance_premium.py

Runda R1: definicja premii rebalansowej z pre-rejestracji (backtest/rebalance_premium.py) na
ręcznie zbudowanych panelach: dwa aktywa z ruchami odwracającymi się → rebalans wygrywa o x²,
trend jednego aktywa → buy-and-hold wygrywa, identyczne zwroty → premia i obrót 0, wycofanie
w trakcie miesiąca = gotówka w obu wersjach, dobór składu bez lookaheadu; własności w hypothesis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import backtest.rebalance_premium as rp

FEE = 0.001


def _close(rets: dict[str, list[float]], start: str = "2021-02-01") -> pd.DataFrame:
    n = len(next(iter(rets.values())))
    idx = pd.date_range(start, periods=n + 1, freq="D", tz="UTC") - pd.Timedelta(days=1)
    data = {sym: 100.0 * np.cumprod([1.0, *(1.0 + np.asarray(r))]) for sym, r in rets.items()}
    return pd.DataFrame(data, index=idx)


def _members(close: pd.DataFrame) -> dict[pd.Timestamp, list[str]]:
    return {close.index[1]: sorted(close.columns)}


def test_two_assets_reverting_moves_give_premium_exactly_x_squared() -> None:
    x = 0.10
    close = _close({"AUSDT": [x, -x], "BUSDT": [-x, x]})
    out = rp.daily_premium(close, _members(close), fee=0.0)
    assert out["r_rebal"].tolist() == pytest.approx([0.0, 0.0])
    assert out["r_bh"].tolist() == pytest.approx([0.0, -(x**2)])  # b&h: 0,55·0,9 + 0,45·1,1 = 0,99
    assert out["premium_gross"].sum() == pytest.approx(x**2)
    assert out["turnover"].iloc[0] == pytest.approx(2 * x / 2 * 2)  # |0,55−0,5| + |0,45−0,5| = 0,10


def test_trending_asset_makes_buy_and_hold_win() -> None:
    close = _close({"AUSDT": [0.1, 0.1], "BUSDT": [0.0, 0.0]})
    out = rp.daily_premium(close, _members(close), fee=0.0)
    assert rp.cumulative_growth(out["r_rebal"]) == pytest.approx(1.05**2 - 1)
    assert rp.cumulative_growth(out["r_bh"]) == pytest.approx(0.5 * 1.21 + 0.5 - 1)
    assert out["premium_gross"].sum() < 0


def test_identical_returns_give_zero_premium_and_zero_turnover() -> None:
    close = _close({"AUSDT": [0.05, -0.02, 0.03], "BUSDT": [0.05, -0.02, 0.03]})
    out = rp.daily_premium(close, _members(close), fee=FEE)
    assert (out["premium_gross"].abs() < 1e-15).all()
    assert (out["turnover"].abs() < 1e-15).all() and (out["cost"] == 0).all()


def test_delisted_member_is_cash_in_both_strategies() -> None:
    close = _close({"AUSDT": [0.1, 0.1, 0.1], "BUSDT": [0.0, 0.0, 0.0]})
    close.loc[close.index[2:], "BUSDT"] = np.nan  # B wycofane od 2. dnia miesiąca
    out = rp.daily_premium(close, _members(close), fee=0.0)
    # dzień 1: oba aktywa; dni 2–3: B = gotówka (0) → r_rebal = 0,05, r_bh z dryfującą wagą A
    assert out["r_rebal"].tolist() == pytest.approx([0.05, 0.05, 0.05])
    assert not out[["r_rebal", "r_bh", "premium_net"]].isna().any().any()


def test_membership_uses_only_data_before_the_month_start() -> None:
    idx = pd.date_range("2021-01-01", periods=70, freq="D", tz="UTC")
    rng = np.random.default_rng(0)
    vol = pd.DataFrame(
        rng.uniform(1e6, 2e6, (70, 4)), index=idx, columns=["AUSDT", "BUSDT", "CUSDT", "DUSDT"]
    )
    vol["CUSDT"] *= 10  # C ma najwyższy obrót przed miesiącem
    m = pd.Timestamp("2021-02-01", tz="UTC")
    before = rp.monthly_members(vol, [m], top_n=2)[m]
    vol2 = vol.copy()
    vol2.loc[vol2.index >= m, "AUSDT"] = 1e12  # przyszłość nie może wpłynąć na skład
    after = rp.monthly_members(vol2, [m], top_n=2)[m]
    assert before == after and "CUSDT" in before


def test_membership_excludes_stables_and_fails_loud_when_too_few() -> None:
    idx = pd.date_range("2021-01-01", periods=40, freq="D", tz="UTC")
    vol = pd.DataFrame(1e6, index=idx, columns=["AUSDT", "USDCUSDT", "BBTC"])
    m = pd.Timestamp("2021-02-01", tz="UTC")
    assert rp.monthly_members(vol, [m], top_n=1)[m] == ["AUSDT"]
    with pytest.raises(ValueError):
        rp.monthly_members(vol, [m], top_n=2)


@given(seed=st.integers(0, 3_000), n_assets=st.integers(1, 6), days=st.integers(2, 25))
@settings(max_examples=40, deadline=None)
def test_gross_identity_turnover_nonnegative_and_single_asset_zero(
    seed: int, n_assets: int, days: int
) -> None:
    rng = np.random.default_rng(seed)
    rets = {f"S{i}USDT": list(rng.normal(0.0, 0.05, days)) for i in range(n_assets)}
    close = _close(rets)
    out = rp.daily_premium(close, _members(close), fee=FEE)
    assert np.allclose(out["premium_gross"], out["r_rebal"] - out["r_bh"])
    assert np.allclose(out["premium_net"], out["premium_gross"] - FEE * out["turnover"])
    assert (out["turnover"] >= -1e-15).all()
    if n_assets == 1:
        assert np.allclose(out["premium_gross"], 0.0) and np.allclose(out["turnover"], 0.0)
