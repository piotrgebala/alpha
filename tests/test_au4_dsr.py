"""Testy backtest/run_au4_dsr.py (AU4): oczekiwane maksimum Sharpe'a i deflated Sharpe."""

from __future__ import annotations

import math

import numpy as np
import pytest

from backtest import run_au4_dsr as au


def test_expected_max_sr_matches_simulation():
    rng = np.random.default_rng(0)
    for n in (10, 30):
        sim = rng.standard_normal((20_000, n)).max(axis=1).mean()
        assert au.expected_max_sr(n, 1.0) == pytest.approx(
            sim, rel=0.03
        )  # przybliżenie BLdP, lekko zachowawcze
    assert au.expected_max_sr(1, 1.0) == 0.0


def test_deflated_sharpe_reduces_to_probabilistic_sharpe():
    # SR0 = 0, rozkład normalny (kurtoza 3): DSR = Φ(SR·√(T−1) / √(1 + SR²/2))
    sr, t = 0.05, 1000
    assert au.deflated_sharpe(sr, 0.0, t, 0.0, 3.0) == pytest.approx(
        0.5 * (1 + math.erf(sr * np.sqrt(t - 1) / np.sqrt(1 + sr**2 / 2) / np.sqrt(2))), abs=1e-9
    )
    # wyższy próg i grubsze ogony obniżają DSR
    base = au.deflated_sharpe(sr, 0.02, t, 0.0, 3.0)
    assert base < au.deflated_sharpe(sr, 0.0, t, 0.0, 3.0)
    assert au.deflated_sharpe(sr, 0.02, t, 0.0, 20.0) < base
