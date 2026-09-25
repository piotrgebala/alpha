"""Test backtest/run_ko1_koszty.py (KO1): scenariusze stawek kosztu z config."""

from __future__ import annotations

import pytest

from backtest import run_ko1_koszty as ko


def test_scenarios_ordered_and_mixed_correctly():
    sc = ko.scenarios()
    assert sc["taker"] == pytest.approx(0.0007)
    assert sc["maker 100%"] == pytest.approx(0.0002)
    assert sc["maker 90%"] == pytest.approx(0.9 * 0.0002 + 0.1 * 0.0007)
    assert sc["maker 100%"] < sc["maker 90%"] < sc["taker"]
