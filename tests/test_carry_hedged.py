"""
test_carry_hedged.py

Runda C1: definicja P&L cash-and-carry z pre-rejestracji (backtest/carry_hedged.py) musi być
odtwarzalna na ręcznie zbudowanych danych: znak fundingu (short dostaje przy > 0), wyrównanie
stawki rozliczonej o T_{t+1} do świecy t, hedge doskonały (spot = perp) zostawia sam funding,
koszty tylko przy przejściach stanu plus zamknięcie na końcu próby, C1a koszt na obu końcach.
Własność w hypothesis: P&L jest addytywny w stanie, a suma kosztów to koszt × przejścia.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import backtest.carry_hedged as ch

COSTS = ch.CarryCosts(spot_fee=0.001, perp_fee=0.0005, slippage=0.0002)


def _series(closes: list[float], rates: list[float], perp: list[float] | None = None):
    ts = pd.date_range("2021-01-01", periods=len(closes), freq="8h", tz="UTC")
    spot = pd.DataFrame({"timestamp": ts, "close": closes})
    perp_df = pd.DataFrame({"timestamp": ts, "close": perp if perp is not None else closes})
    funding = pd.DataFrame({"timestamp": ts, "funding_rate": rates})
    return spot, perp_df, funding


def test_switch_cost_is_both_legs_taker_plus_slippage_on_each() -> None:
    assert COSTS.switch_cost == pytest.approx(0.001 + 0.0002 + 0.0005 + 0.0002)


def test_alignment_funding_received_in_period_t_is_the_rate_settled_at_its_close() -> None:
    spot, perp, funding = _series([100, 110, 121, 133.1], [0.0001, 0.0002, -0.0003, 0.0004])
    frame = ch.align_carry_frame(spot, perp, funding)
    assert len(frame) == 2  # pierwszy okres bez r, ostatni bez f_next
    assert frame["f_now"].tolist() == [0.0002, -0.0003]
    assert frame["f_next"].tolist() == [-0.0003, 0.0004]
    assert frame["r_spot"].tolist() == pytest.approx([0.1, 0.1])


def test_perfect_hedge_leaves_funding_minus_costs_and_short_pays_negative_rates() -> None:
    spot, perp, funding = _series([100, 130, 90, 150, 120], [0.0, 0.0002, -0.0003, 0.0004, 0.0])
    frame = ch.align_carry_frame(spot, perp, funding)
    out = ch.hedged_carry_pnl(frame, ch.state_always_on(frame), COSTS)
    assert out["hedge"].tolist() == pytest.approx([0.0, 0.0, 0.0])
    assert out["funding_received"].tolist() == pytest.approx([-0.0003, 0.0004, 0.0])
    assert out["cost"].tolist() == pytest.approx([COSTS.switch_cost, 0.0, COSTS.switch_cost])
    assert out["pnl"].sum() == pytest.approx(0.0001 - 2 * COSTS.switch_cost)


def test_hedge_gains_when_perp_falls_relative_to_spot() -> None:
    spot, perp, funding = _series([100, 100, 100], [0.0, 0.0, 0.0], perp=[101, 100, 100])
    frame = ch.align_carry_frame(spot, perp, funding)
    out = ch.hedged_carry_pnl(frame, ch.state_always_on(frame), COSTS)
    # okres 0: spot 100→100 (0), perp 101→100 (−0,99 %) → short zarabia +0,99 %
    assert out["hedge"].iloc[0] == pytest.approx(0.0 - (100 / 101 - 1))


def test_costs_only_at_state_transitions_plus_final_close() -> None:
    n = 7
    spot, perp, funding = _series([100.0] * n, [0.0] * n)
    frame = ch.align_carry_frame(spot, perp, funding)  # 5 okresów
    state = pd.Series([0.0, 1.0, 1.0, 0.0, 1.0])
    out = ch.hedged_carry_pnl(frame, state, COSTS)
    c = COSTS.switch_cost
    assert out["cost"].tolist() == pytest.approx(
        [0.0, c, 0.0, c, 2 * c]
    )  # wejście, wyjście, wejście + zamknięcie
    assert out["n_switches"].tolist() == [0, 1, 0, 1, 1]
    assert (out["pnl"] == -out["cost"]).all()


def test_state_after_positive_funding_uses_the_rate_known_at_decision_time() -> None:
    spot, perp, funding = _series([100] * 5, [0.0001, -0.0001, 0.0002, 0.0, 0.0003])
    frame = ch.align_carry_frame(spot, perp, funding)
    assert ch.state_after_positive_funding(frame).tolist() == [
        0.0,
        1.0,
        0.0,
    ]  # f_now: −1e-4, 2e-4, 0


def test_fails_loud_on_mismatched_timestamps_or_missing_columns() -> None:
    spot, perp, funding = _series([100, 101, 102], [0.0, 0.0, 0.0])
    with pytest.raises(ValueError):
        ch.align_carry_frame(spot, perp.iloc[:2], funding)
    with pytest.raises(ValueError):
        ch.align_carry_frame(spot.rename(columns={"close": "c"}), perp, funding)
    frame = ch.align_carry_frame(spot, perp, funding)
    with pytest.raises(ValueError):
        ch.hedged_carry_pnl(frame, pd.Series([2.0]), COSTS)


def test_summarize_pnl_arithmetics_and_neff_cap() -> None:
    rng = np.random.default_rng(0)
    pnl = pd.Series(rng.normal(0.0001, 0.0003, 500))
    w = ch.summarize_pnl(pnl)
    assert w["n"] == 500 and 0 < w["n_eff"] <= 500
    assert w["t"] == pytest.approx(w["mean"] / w["se"])
    assert w["annual_notional"] == pytest.approx(w["mean"] * ch.PERIODS_PER_YEAR)
    assert w["annual_capital"] == pytest.approx(w["annual_notional"] / ch.CAPITAL_PER_NOTIONAL)
    assert w["ci_low"] < w["mean"] < w["ci_high"]


def test_max_drawdown_and_runup_on_hand_series() -> None:
    assert ch.max_drawdown(pd.Series([0.01, -0.02, -0.01, 0.05])) == pytest.approx(0.03)
    assert ch.max_runup(pd.Series([100.0, 110.0, 150.0, 120.0]), periods=2) == pytest.approx(0.5)


@given(seed=st.integers(0, 2_000), n=st.integers(4, 60))
@settings(max_examples=30, deadline=None)
def test_pnl_is_additive_in_state_and_costs_count_transitions(seed: int, n: int) -> None:
    rng = np.random.default_rng(seed)
    closes = list(100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, n)))
    perp = list(np.asarray(closes) * (1.0 + rng.normal(0.0, 0.0005, n)))
    rates = list(rng.normal(0.0001, 0.0002, n))
    spot_df, perp_df, fund_df = _series(closes, rates, perp)
    frame = ch.align_carry_frame(spot_df, perp_df, fund_df)
    state = pd.Series(rng.integers(0, 2, len(frame)).astype(float))
    out = ch.hedged_carry_pnl(frame, state, COSTS)
    raw = state.to_numpy() * (frame["f_next"] + frame["r_spot"] - frame["r_perp"]).to_numpy()
    assert np.allclose(out["pnl"].to_numpy(), raw - out["cost"].to_numpy())
    transitions = int((state != state.shift(1, fill_value=0.0)).sum())
    final_close = int(state.iloc[-1] == 1.0)
    assert out["cost"].sum() == pytest.approx(COSTS.switch_cost * (transitions + final_close))
    assert (out.loc[out["state"] == 0.0, "funding_received"] == 0.0).all()
