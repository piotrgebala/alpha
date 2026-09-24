"""Testy backtest/ts_momentum.py (runda TS1): sygnał, σ̂, wagi, P&L fazy, test przyszłości."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import ts_momentum as tm


def _panel(n: int = 120, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    r = rng.normal(0, 0.03, size=(n, 3))
    return pd.DataFrame(100 * np.exp(np.cumsum(r, axis=0)), index=idx, columns=["A", "B", "C"])


def test_signal_sign_uses_lookback_return():
    close = _panel()
    s = tm.signal_sign(close, 28)
    t = close.index[60]
    expected = np.sign(close.loc[t] / close.shift(28).loc[t] - 1.0)
    assert (s.loc[t] == expected).all()
    assert s.iloc[:28].isna().all().all()


@pytest.mark.parametrize("cut", [40, 70, 100])
def test_signal_and_vol_do_not_look_ahead(cut):
    close = _panel()
    full_s, full_v = tm.signal_sign(close), tm.ewma_vol(close)
    trunc = close.iloc[: cut + 1]
    s, v = tm.signal_sign(trunc), tm.ewma_vol(trunc)
    t = close.index[cut]
    pd.testing.assert_series_equal(full_s.loc[t], s.loc[t])
    pd.testing.assert_series_equal(full_v.loc[t], v.loc[t])


def test_ewma_vol_constant_returns():
    idx = pd.date_range("2021-01-01", periods=200, freq="D", tz="UTC")
    r = np.where(np.arange(200) % 2 == 0, 0.02, -0.02)
    close = pd.DataFrame({"A": 100 * np.cumprod(1 + r)}, index=idx)
    v = tm.ewma_vol(close)["A"]
    assert v.iloc[-1] == pytest.approx(0.02 * np.sqrt(365), rel=1e-6)


def test_position_weights_cap_and_normalisation():
    w = tm.position_weights(np.array([1, -1, 0, np.nan]), np.array([0.8, 0.1, 0.5, 0.5]))
    # N = 2 ważne; A: 0,4/0,8 = 0,5 → 0,25; B: min(3, 4) = 3 → −1,5
    assert w == pytest.approx([0.25, -1.5, 0.0, 0.0])


@given(
    st.lists(st.sampled_from([-1.0, 1.0]), min_size=1, max_size=20),
    st.floats(min_value=0.01, max_value=5.0),
)
@settings(max_examples=60, deadline=None)
def test_weights_sign_symmetry_and_cap(signs, vol):
    s = np.array(signs)
    v = np.full(len(s), vol)
    w = tm.position_weights(s, v)
    assert np.allclose(tm.position_weights(-s, v), -w)
    assert np.all(np.abs(w) <= tm.CAP / len(s) + 1e-12)
    assert np.all(np.sign(w) == s)


def test_phase_returns_zero_when_prices_flat():
    n, k = 30, 3
    rets = np.zeros((n, k))
    fund = np.zeros((n, k))
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    forms = [(5, np.array([0.5, -0.5, 0.0])), (12, np.array([0.5, -0.5, 0.0]))]
    out = tm.phase_returns(rets, fund, idx, forms, fee=0.001)
    assert out["gross"].abs().max() == 0.0
    # koszt tylko przy pierwszym formowaniu (obrót 1,0), drugie bez zmian wag
    assert out["cost"].sum() == pytest.approx(0.001 * 1.0)


def test_phase_returns_first_return_is_day_after_formation_and_funding_sign():
    n = 10
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    rets = np.zeros((n, 2))
    rets[3, 0] = 0.10  # dzień formowania: nie może wejść do P&L
    rets[4, 0] = 0.05
    fund = np.zeros((n, 2))
    fund[4, 0] = 0.001
    fund[4, 1] = 0.001
    out = tm.phase_returns(rets, fund, idx, [(3, np.array([1.0, -1.0]))], fee=0.0)
    first = out.iloc[0]
    assert first["date"] == idx[4]
    assert first["gross"] == pytest.approx(0.05)
    # long płaci 0,001, short otrzymuje 0,001 → netto 0
    assert first["funding"] == pytest.approx(0.0)
    out2 = tm.phase_returns(rets, fund, idx, [(3, np.array([1.0, 0.0]))], fee=0.0)
    assert out2.iloc[0]["funding"] == pytest.approx(-0.001)


def test_markov_signs_persistence():
    rng = np.random.default_rng(1)
    fn = tm.MarkovSigns(p_flip=0.0)
    a = fn(np.ones(3), ["A", "B", "C"], rng)
    b = fn(np.ones(3), ["A", "B", "C"], rng)
    assert np.array_equal(a, b)
    fn1 = tm.MarkovSigns(p_flip=1.0)
    a = fn1(np.ones(2), ["A", "B"], rng)
    b = fn1(np.ones(2), ["A", "B"], rng)
    assert np.array_equal(a, -b)


def test_formation_dates_phases_are_shifted():
    idx = pd.date_range("2021-01-01", periods=40, freq="D", tz="UTC")
    start, end = idx[0], idx[-1]
    d0 = tm.formation_dates(idx, start, end, 0)
    d3 = tm.formation_dates(idx, start, end, 3)
    assert d0[1] - d0[0] == pd.Timedelta(days=7)
    assert d3[0] - d0[0] == pd.Timedelta(days=3)


def test_portfolio_runs_and_averages_phases():
    close = _panel(200)
    members = {pd.Timestamp("2021-02-01", tz="UTC"): ["A", "B", "C"]}
    fund = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    avg, phases = tm.portfolio(
        close, fund, members, pd.Timestamp("2021-02-01", tz="UTC"), close.index[-1], fee=0.0007
    )
    assert len(phases) == tm.PHASES
    assert len(avg) > 100
    d = avg["date"].iloc[10]
    manual = np.mean([p.loc[d, "net"] for p in phases])
    assert avg["net"].iloc[10] == pytest.approx(manual)


def test_shift_signs_preserves_cross_section_and_rolls_time():
    close = _panel(80)
    s = tm.signal_sign(close)
    sh = tm.shift_signs(s, 14)
    np.testing.assert_array_equal(sh.iloc[40].to_numpy(), s.iloc[26].to_numpy())
    np.testing.assert_array_equal(sh.iloc[5].to_numpy(), s.iloc[-9].to_numpy())


def test_members_rank_band_excludes_top():
    from backtest.run_ts_momentum_oos import members_rank_band

    idx = pd.date_range("2021-01-01", periods=60, freq="D", tz="UTC")
    vol = pd.DataFrame({f"C{i}USDT": float(100 - i) for i in range(60)}, index=idx)
    m = pd.Timestamp("2021-02-15", tz="UTC")
    band = members_rank_band(vol, [m], lo=5, hi=12)[m]
    assert band == sorted(f"C{i}USDT" for i in range(5, 12))


def test_keep_fn_zeroes_positions_without_renormalising():
    close = _panel(200)
    members = {pd.Timestamp("2021-02-01", tz="UTC"): ["A", "B", "C"]}
    signs = tm.signal_sign(close)
    vols = tm.ewma_vol(close)
    t = close.index[60]
    full = tm.build_formations(signs, vols, members, [t])[0][1]
    kept = tm.build_formations(
        signs,
        vols,
        members,
        [t],
        keep_fn=lambda t, syms, s: [1.0 if x != "A" else 0.0 for x in syms],
    )[0][1]
    assert kept[0] == 0.0
    assert kept[1:] == pytest.approx(full[1:])


def test_signs_override_replaces_signal_and_default_unchanged():
    close = _panel(200)
    members = {pd.Timestamp("2021-02-01", tz="UTC"): ["A", "B", "C"]}
    fund = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    start, end = pd.Timestamp("2021-02-01", tz="UTC"), close.index[-1]
    base, _ = tm.portfolio(close, fund, members, start, end, fee=0.0)
    same, _ = tm.portfolio(
        close, fund, members, start, end, fee=0.0, signs_override=tm.signal_sign(close)
    )
    pd.testing.assert_frame_equal(base, same)
    flipped, _ = tm.portfolio(
        close, fund, members, start, end, fee=0.0, signs_override=-tm.signal_sign(close)
    )
    assert (flipped["net_notional"] * base["net_notional"] <= 1e-12).all()


def _liq_setup(n=20, k=2, seed=3):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0, 0.05, size=(n, k))
    fund = rng.normal(0, 0.0005, size=(n, k))
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    forms = [(2, np.array([0.3, -0.2])), (9, np.array([-0.1, 0.4]))]
    return rets, fund, idx, forms


def test_phase_returns_liq_equals_plain_without_liquidation():
    rets, fund, idx, forms = _liq_setup()
    ones = np.ones_like(rets)
    a = tm.phase_returns(rets, fund, idx, forms, 0.001)
    b = tm.phase_returns_liq(rets, fund, idx, forms, 0.001, ones, ones, lev=3.0, mmr=-10.0)
    for col in ("gross", "funding", "cost", "net", "gross_notional", "turnover"):
        assert b[col].to_numpy() == pytest.approx(a[col].to_numpy(), abs=1e-12), col


def test_liquidation_long_loses_margin_and_stays_out():
    n = 12
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    rets = np.zeros((n, 1))
    low = np.ones((n, 1))
    low[4, 0] = 0.6  # minimum -40 % -> likwidacja longa 3x (prog 32,3 %)
    rets[6, 0] = 0.5  # po likwidacji zysk nie moze juz wejsc
    out = tm.phase_returns_liq(
        rets, np.zeros((n, 1)), idx, [(1, np.array([0.3]))], 0.0, low, np.ones((n, 1)), lev=3.0
    )
    assert out["liquidations"].sum() == 1
    assert out["gross"].sum() == pytest.approx(-0.1)
    assert out.loc[out["date"] == idx[6], "gross"].iloc[0] == 0.0


def test_liquidation_short_on_high():
    n = 8
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    z = np.zeros((n, 1))
    high = np.ones((n, 1))
    high[3, 0] = 1.4
    out = tm.phase_returns_liq(z, z, idx, [(1, np.array([-0.3]))], 0.0, np.ones((n, 1)), high, 3.0)
    assert out["liquidations"].sum() == 1
    assert out["gross"].sum() == pytest.approx(-0.1)


@given(st.floats(min_value=0.5, max_value=3.0), st.floats(min_value=0.0, max_value=0.9))
@settings(max_examples=50, deadline=None)
def test_liquidated_position_loses_exactly_margin(up, drop):
    n = 6
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    rets = np.zeros((n, 1))
    rets[2, 0] = up - 1.0
    low = np.ones((n, 1))
    low[3, 0] = 1.0 - drop
    out = tm.phase_returns_liq(
        rets, np.zeros((n, 1)), idx, [(1, np.array([0.3]))], 0.0, low, np.ones((n, 1)), 3.0
    )
    if out["liquidations"].sum() > 0:
        # skumulowany wynik pozycji po likwidacji = -depozyt (w jednostkach kapitalu z formowania)
        assert np.prod(1 + out["gross"]) - 1 == pytest.approx(-0.1, abs=1e-9)
    else:
        assert np.prod(1 + out["gross"]) - 1 >= -0.1 - 1e-9 or up < 1
