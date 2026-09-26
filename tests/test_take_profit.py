"""Testy backtest/take_profit.py (TP1): bez celu = silnik dziennika co do bitu; wyjście na celu
(long/short), koszt wyjścia, brak fundingu po wyjściu, konflikt z likwidacją, bez dźwigni bez likwidacji.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import take_profit as tpm
from backtest.ts_momentum import phase_returns_liq


def _random_case(seed=0, n_days=60, n_sym=6):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-01", periods=n_days, freq="D", tz="UTC")
    r = rng.standard_t(3, (n_days, n_sym)) * 0.04
    close = 100 * np.exp(np.cumsum(r, axis=0))
    close = pd.DataFrame(close, index=idx)
    high = close * (1 + np.abs(rng.normal(0, 0.03, close.shape)))
    low = close * (1 - np.abs(rng.normal(0, 0.03, close.shape)))
    rets = close.pct_change().to_numpy()
    fund = rng.normal(0, 1e-4, close.shape)
    lo_rel = (low / close.shift(1)).to_numpy()
    hi_rel = (high / close.shift(1)).to_numpy()
    forms = [
        (t, rng.normal(0, 0.1, n_sym) * (rng.random(n_sym) > 0.3)) for t in range(5, n_days - 1, 7)
    ]
    return idx, rets, fund, lo_rel, hi_rel, forms


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_without_target_equals_journal_engine(seed):
    idx, rets, fund, lo, hi, forms = _random_case(seed)
    ref = phase_returns_liq(rets, fund, idx, forms, 0.0007, lo, hi, 2.0, 0.01)
    got = tpm.phase_returns_tp(rets, fund, idx, forms, 0.0007, lo, hi, 2.0, 0.01, None)
    pd.testing.assert_frame_equal(got[ref.columns], ref, check_exact=True)
    assert (got["tp_exits"] == 0).all()


def _one_lot(w, close, high, low, lev=None, tp=0.02, fee=0.001, funding=0.0):
    idx = pd.date_range("2025-01-01", periods=len(close), freq="D", tz="UTC")
    c = pd.DataFrame({"A": close}, index=idx)
    rets = c.pct_change().to_numpy()
    lo = (pd.DataFrame({"A": low}, index=idx) / c.shift(1)).to_numpy()
    hi = (pd.DataFrame({"A": high}, index=idx) / c.shift(1)).to_numpy()
    fund = np.full(c.shape, funding)
    forms = [(0, np.array([w])), (len(close) - 1, np.array([0.0]))]
    return tpm.phase_returns_tp(rets, fund, idx, forms, fee, lo, hi, lev, 0.01, tp)


def test_long_exits_at_target_then_sits_in_cash():
    close = [100, 101, 99, 105, 90, 80]
    high = [100, 101.5, 101, 106, 91, 81]  # dzień 3: maksimum 106 ≥ 102 → wyjście po 102
    low = [100, 100, 98, 99, 89, 79]
    out = _one_lot(0.5, close, high, low, funding=1e-3)
    assert out["tp_exits"].tolist() == [0, 0, 1, 0, 0]
    total_gross = np.prod(1 + out["gross"]) - 1
    assert total_gross == pytest.approx(
        0.5 * 0.02, abs=1e-12
    )  # zysk = waga × cel, dalszy spadek bez wpływu
    equity_before = 1 + 0.5 * (99 / 100 - 1)  # kapitał fazy przed dniem wyjścia (P&L dni 1–2)
    assert out["cost"].iloc[2] == pytest.approx(0.001 * 0.5 * 1.02 / equity_before, rel=1e-12)
    assert (out["funding"].iloc[3:] == 0).all()  # po wyjściu brak fundingu
    assert (out["gross"].iloc[3:] == 0).all()


def test_short_exits_at_target():
    close = [100, 99, 101, 97, 110]
    high = [100, 100, 102, 98, 111]
    low = [
        100,
        98.5,
        99,
        97.5,
        109,
    ]  # dzień 2: minimum 98,5 ≤ 98 ? nie; dzień 4: 97,5 ≤ 98 → wyjście
    out = _one_lot(-0.4, close, high, low)
    assert out["tp_exits"].tolist() == [0, 0, 1, 0]
    assert np.prod(1 + out["gross"]) - 1 == pytest.approx(0.4 * 0.02, abs=1e-12)


def test_same_candle_liquidation_beats_target():
    close = [100, 100, 100]
    high = [100, 103, 100]  # cel +2 % osiągnięty…
    low = [100, 50, 100]  # …i w tej samej świecy likwidacja przy 2× (próg 51 %)
    out = _one_lot(0.5, close, high, low, lev=2.0)
    assert out["liquidations"].iloc[0] == 1 and out["tp_exits"].iloc[0] == 0
    assert out["gross"].iloc[0] == pytest.approx(-0.5 / 2.0)


def test_no_leverage_means_no_liquidation_but_target_works():
    close = [100, 40, 45, 60]
    high = [100, 41, 46, 61]
    low = [100, 30, 44, 59]
    out = _one_lot(0.5, close, high, low, lev=None, tp=0.5)  # cel +50 % nieosiągnięty
    assert out["liquidations"].sum() == 0 and out["tp_exits"].sum() == 0
    assert np.prod(1 + out["gross"]) - 1 == pytest.approx(0.5 * (60 / 100 - 1), abs=1e-12)


def test_no_lookahead_prefix_is_stable():
    idx, rets, fund, lo, hi, forms = _random_case(5)
    full = tpm.phase_returns_tp(rets, fund, idx, forms, 0.0007, lo, hi, 2.0, 0.01, 0.02)
    cut = 30
    rets2, lo2, hi2 = rets.copy(), lo.copy(), hi.copy()
    rets2[cut + 1 :] *= -3.0  # inna przyszłość po dniu `cut`
    lo2[cut + 1 :] = 0.2
    hi2[cut + 1 :] = 5.0
    part = tpm.phase_returns_tp(rets2, fund, idx, forms, 0.0007, lo2, hi2, 2.0, 0.01, 0.02)
    upto = full["date"] <= idx[cut]
    pd.testing.assert_frame_equal(full.loc[upto], part.loc[upto])
