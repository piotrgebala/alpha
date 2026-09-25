"""AU3: kanoniczny N_eff nie zapada się przy ujemnej sumie autokorelacji (regresja + właściwości)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from agents.labeling import effective_sample_size
from backtest.carry_hedged import summarize_pnl


def _collapsing_series() -> pd.Series:
    """Zróżnicowany szum (n = 220), na którym stary wzór dawał N_eff = −6 080."""
    return pd.Series(np.diff(np.random.default_rng(1).normal(size=221)))


def test_negative_denominator_gives_n_not_negative():
    x = _collapsing_series()
    acf = sum(x.autocorr(k) for k in range(1, 51))
    assert 1 + 2 * acf < 0  # przypadek, który psuł przyrząd
    assert effective_sample_size(x)["n_eff"] == len(x)


def test_summarize_pnl_and_trade_returns_no_collapse():
    x = _collapsing_series() + 0.2  # dodatnia średnia, ujemna autokorelacja
    w = summarize_pnl(x, periods_per_year=52, capital_per_notional=1.0)
    assert w["n_eff"] == len(x)
    assert w["t_neff"] == np.float64(w["t"])
    # checkpoint_lib.summarize_trade_returns: t_neff = t·√(min(N_eff, n)/n) — dawniej √(ujemne) = NaN
    assert np.isfinite(np.sqrt(min(effective_sample_size(x)["n_eff"], len(x)) / len(x)))


@settings(max_examples=150, deadline=None)
@given(st.lists(st.floats(-1, 1, allow_nan=False), min_size=10, max_size=300))
def test_n_eff_positive_finite_and_capped_by_callers(values):
    x = pd.Series(values)
    n_eff = effective_sample_size(x)["n_eff"]
    assert np.isfinite(n_eff) and n_eff > 0
    if x.std() > 0:
        w = summarize_pnl(x, periods_per_year=52, capital_per_notional=1.0)
        assert 1 <= w["n_eff"] <= len(x)
        assert abs(w["t_neff"]) <= abs(w["t"]) + 1e-9  # korekta tylko odejmuje pewność
