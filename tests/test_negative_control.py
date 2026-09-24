"""Testy backtest/negative_control.py (runda NC1): dane syntetyczne bez informacji o przyszłości."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import negative_control as nc
from backtest.carry_hedged import summarize_pnl
from backtest.ts_momentum import portfolio


def test_returns_shape_and_determinism():
    a = nc.synthetic_returns(300, 5, seed=1)
    b = nc.synthetic_returns(300, 5, seed=1)
    c = nc.synthetic_returns(300, 5, seed=2)
    assert a.shape == (300, 5)
    assert isinstance(a.index, pd.DatetimeIndex) and a.index.tz is not None
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_no_autocorrelation_but_fat_tails_and_vol_clustering():
    r = nc.synthetic_returns(20_000, 2, seed=3)["C00USDT"].to_numpy()
    band = 4.0 / np.sqrt(len(r))
    # brak pamięci KIERUNKU: znaki zwrotów są dokładnie niezależne (σ zależy tylko od przeszłości,
    # szok symetryczny); surowa autokorelacja przy GARCH ma większy rozrzut niż 1/√n, stąd luźniej
    s = np.sign(r)
    for lag in (1, 7, 28):
        assert abs(nc.autocorr(s, lag)) < band
        assert abs(nc.autocorr(r, lag)) < 2 * band
    assert nc.autocorr(r**2, 1) > 0.05  # kwadraty: grupowanie zmienności (GARCH)
    assert nc.excess_kurtosis(r) > 1.0  # grube ogony
    assert r.std() == pytest.approx(0.04, rel=0.25)


def test_common_factor_correlation():
    r = nc.synthetic_returns(20_000, 3, seed=4, rho=0.5)
    c = r.corr().to_numpy()[np.triu_indices(3, 1)]
    assert c == pytest.approx([0.5] * 3, abs=0.07)
    r0 = nc.synthetic_returns(20_000, 3, seed=4, rho=0.0)
    assert np.abs(r0.corr().to_numpy()[np.triu_indices(3, 1)]).max() < 0.05


def test_invalid_parameters():
    with pytest.raises(ValueError):
        nc.synthetic_returns(10, 2, df=2.0)
    with pytest.raises(ValueError):
        nc.synthetic_returns(10, 2, garch=(0.5, 0.6))


def test_ohlc_consistency():
    r = nc.synthetic_returns(500, 4, seed=5)
    o = nc.synthetic_ohlc(r, seed=5)
    hi, lo, op, cl = o["high"], o["low"], o["open"], o["close"]
    assert (hi >= np.maximum(op, cl) - 1e-12).all().all()
    assert (lo <= np.minimum(op, cl) + 1e-12).all().all()
    assert (lo > 0).all().all()
    assert cl.pct_change().iloc[1:].to_numpy() == pytest.approx(r.iloc[1:].to_numpy())


def _trend_t(seed: int, peek: bool = False) -> float:
    r = nc.synthetic_returns(1_200, 10, seed=seed)
    close = 100.0 * (1.0 + r).cumprod()
    fund = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    start = close.index[120].normalize()
    end = close.index[-1] + pd.Timedelta(days=1)
    members = nc.all_members(close, start, end)
    over = np.sign(close.shift(-7) / close - 1.0) if peek else None
    out, _ = portfolio(close, fund, members, start, end, 0.0, phases=1, signs_override=over)
    return summarize_pnl(out.dropna()["gross"], periods_per_year=365, capital_per_notional=1.0)[
        "t_neff"
    ]


def test_trend_engine_finds_nothing_on_noise():
    """Kontrola negatywna silnika TS1: na szumie |t| < 3 (fałszywy alarm na tym poziomie ~0,3 %)."""
    for seed in (0, 1, 2):
        assert abs(_trend_t(seed)) < 3.0


def test_trend_engine_detects_deliberate_lookahead():
    """Kontrola czułości: ten sam silnik z celowym zajrzeniem w przyszły tydzień → ogromne t."""
    assert _trend_t(0, peek=True) > 5.0


def test_all_members_covers_period():
    idx = pd.date_range("2021-01-01", periods=100, freq="D", tz="UTC")
    close = pd.DataFrame(1.0, index=idx, columns=["A", "B"])
    m = nc.all_members(close, idx[10], idx[-1])
    assert min(m) <= idx[10]
    assert all(v == ["A", "B"] for v in m.values())
