"""Testy backtest/xs_momentum.py (runda X1) — czyste funkcje, bez danych z dysku."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import xs_momentum as xm


def _days(n: int, start: str = "2021-01-01") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="D", tz="UTC")


def _close_from_returns(rets: dict[str, list[float]], start: str = "2021-01-01") -> pd.DataFrame:
    n = len(next(iter(rets.values()))) + 1
    idx = _days(n, start)
    return pd.DataFrame(
        {s: 100.0 * np.cumprod([1.0, *(1.0 + np.asarray(r))]) for s, r in rets.items()}, index=idx
    )


def _no_funding(close: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(0.0, index=close.index, columns=close.columns)


# ---------------------------------------------------------------- sygnał, daty, nogi


def test_signal_panel_uses_only_past_closes():
    close = _close_from_returns({"A": [0.1] * 30})
    sig = xm.signal_panel(close, lookback=28)
    assert sig["A"].iloc[:28].isna().all()
    assert sig["A"].iloc[28] == pytest.approx(1.1**28 - 1)


def test_rebalance_dates_every_hold_days_within_window():
    idx = _days(30)
    d = xm.rebalance_dates(idx, idx[3], idx[25], hold_days=7)
    assert d == [idx[3], idx[10], idx[17], idx[24]]
    assert xm.rebalance_dates(idx, idx[29], idx[29]) == []


def test_rank_legs_top_bottom_ties_and_insufficient():
    row = pd.Series({"A": 0.5, "B": 0.4, "C": np.nan, "D": -0.1, "E": -0.2, "F": 0.0, "G": 0.5})
    legs = xm.rank_legs(row, ["A", "B", "C", "D", "E", "F", "G"], leg_size=2)
    assert legs == (["A", "G"], ["D", "E"])  # remis A/G → oba w top-2 (nazwa rozstrzyga kolejność)
    assert xm.rank_legs(row, ["A", "B", "C"], leg_size=2) is None  # 2 z sygnałem < 4


def test_random_legs_disjoint_and_sized():
    rng = np.random.default_rng(1)
    row = pd.Series({s: float(i) for i, s in enumerate("ABCDEFGHIJ")})
    longs, shorts = xm.random_legs(row, list("ABCDEFGHIJ"), rng, leg_size=3)
    assert len(longs) == 3 and len(shorts) == 3 and not set(longs) & set(shorts)


# ---------------------------------------------------------------- long-short


def _two_asset_case(x: float, y: float, fee: float = 0.0):
    """A rośnie o x dziennie, B spada o y; sygnał (28 dni) ustawia A jako long, B jako short."""
    close = _close_from_returns({"A": [x] * 40, "B": [-y] * 40})
    members = {close.index[0]: ["A", "B"]}
    dates = xm.rebalance_dates(close.index, close.index[28], close.index[-1], hold_days=7)
    out = xm.long_short_returns(close, _no_funding(close), members, dates, fee, leg_size=1)
    return close, dates, out


def test_long_short_gross_is_half_spread_and_no_lookahead():
    close, dates, out = _two_asset_case(0.02, 0.01)
    assert out["date"].iloc[0] == dates[0] + pd.Timedelta(days=1)  # pierwszy zwrot z t+1
    assert np.allclose(out["r_ls_gross"], 0.5 * (0.02 + 0.01))
    assert np.allclose(out["r_long"], 0.02) and np.allclose(out["r_short"], -0.01)
    assert (out["n_long"] == 1).all() and (out["n_short"] == 1).all()


def test_turnover_full_replacement_then_zero_and_cost_only_on_formation_day():
    close, dates, out = _two_asset_case(0.02, 0.01, fee=0.001)
    form_rows = out[out["date"] == dates[0] + pd.Timedelta(days=1)]
    assert form_rows["turnover"].iloc[0] == pytest.approx(1.0)  # z gotówki: kupno 0,5 + 0,5
    later = out[(out["formation"] == dates[1])]
    assert later["turnover"].iloc[0] == pytest.approx(
        0.0
    )  # ten sam skład, 1 aktywo/nogę → brak dryfu
    assert out["cost"].sum() == pytest.approx(0.001 * 1.0)
    assert np.allclose(out["r_net"], out["r_ls_gross"] + out["funding_net"] - out["cost"])


def test_identical_returns_give_zero_gross():
    close = _close_from_returns({"A": [0.01] * 40, "B": [0.01] * 40})
    members = {close.index[0]: ["A", "B"]}
    dates = xm.rebalance_dates(close.index, close.index[28], close.index[-1])
    out = xm.long_short_returns(close, _no_funding(close), members, dates, 0.0, leg_size=1)
    assert np.allclose(out["r_ls_gross"], 0.0)


def test_funding_sign_long_pays_short_receives():
    close = _close_from_returns({"A": [0.02] * 40, "B": [-0.01] * 40})
    fund = _no_funding(close)
    fund["A"] = 0.001  # long płaci
    fund["B"] = 0.0005  # short otrzymuje
    members = {close.index[0]: ["A", "B"]}
    dates = xm.rebalance_dates(close.index, close.index[28], close.index[-1])
    out = xm.long_short_returns(close, fund, members, dates, 0.0, leg_size=1)
    assert np.allclose(out["funding_net"], 0.5 * 0.0005 - 0.5 * 0.001)


def test_delisted_member_is_cash():
    close = _close_from_returns({"A": [0.02] * 40, "B": [-0.01] * 40})
    close.loc[close.index[33:], "B"] = np.nan  # B wycofane w trakcie
    members = {close.index[0]: ["A", "B"]}
    dates = xm.rebalance_dates(close.index, close.index[28], close.index[-1])
    out = xm.long_short_returns(close, _no_funding(close), members, dates, 0.0, leg_size=1)
    tail = out[out["date"] > close.index[33]]
    assert np.allclose(tail["r_short"], 0.0) and (tail["n_short"] == 0).all()


@settings(max_examples=40, deadline=None)
@given(
    st.lists(st.floats(-0.3, 0.5), min_size=35, max_size=35),
    st.lists(st.floats(-0.3, 0.5), min_size=35, max_size=35),
)
def test_gross_identity_for_any_paths(ra, rb):
    close = _close_from_returns({"A": ra, "B": rb})
    members = {close.index[0]: ["A", "B"]}
    dates = xm.rebalance_dates(close.index, close.index[28], close.index[-1])
    out = xm.long_short_returns(close, _no_funding(close), members, dates, 0.0, leg_size=1)
    assert np.allclose(out["r_ls_gross"], 0.5 * (out["r_long"] - out["r_short"]))


# ---------------------------------------------------------------- IC i funding panel


def test_weekly_ic_perfect_and_inverse():
    rng = np.random.default_rng(0)
    idx = _days(60)
    close = pd.DataFrame(
        100.0 * np.exp(np.cumsum(rng.normal(0, 0.03, (60, 8)), axis=0)),
        index=idx,
        columns=list("ABCDEFGH"),
    )
    sig = xm.signal_panel(close, 28)
    fwd = close.shift(-7) / close - 1.0
    t = idx[30]
    # sygnał zgodny z przyszłym zwrotem → IC = 1 (konstruujemy close tak, by sygnał = fwd)
    ic = xm.weekly_ic(close, {idx[0]: list("ABCDEFGH")}, [t], lookback=28, hold_days=7)
    assert len(ic) == 1 and -1.0 <= ic["ic"].iloc[0] <= 1.0 and ic["n"].iloc[0] == 8
    assert sig.loc[t].notna().all() and fwd.loc[t].notna().all()


def test_daily_funding_panel_sums_settlements_and_floors_jitter(tmp_path):
    ts = pd.to_datetime(
        [
            "2021-01-01 00:00:00.003",
            "2021-01-01 08:00:00",
            "2021-01-01 16:00:00",
            "2021-01-02 00:00:00",
        ],
        utc=True,
        format="ISO8601",
    )
    pd.DataFrame({"timestamp": ts, "funding_rate": [0.0001, 0.0002, 0.0003, 0.0004]}).to_parquet(
        tmp_path / "XUSDT_funding.parquet", index=False
    )
    panel = xm.daily_funding_panel(tmp_path)
    assert list(panel.columns) == ["XUSDT"]
    assert panel.loc[pd.Timestamp("2021-01-01", tz="UTC"), "XUSDT"] == pytest.approx(0.0006)
    assert panel.loc[pd.Timestamp("2021-01-02", tz="UTC"), "XUSDT"] == pytest.approx(0.0004)
    with pytest.raises(ValueError):
        xm.daily_funding_panel(tmp_path / "nie-ma")
