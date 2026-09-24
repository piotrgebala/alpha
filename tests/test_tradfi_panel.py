"""Testy data/tradfi_panel.py (runda TX1): siatka kalendarzowa, waluty, obligacje, ceny ≤ 0."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data import tradfi_panel as tp


def _s(values, dates):
    return pd.Series(values, index=pd.to_datetime(dates))


def test_calendar_ffill_carries_only_past_values():
    s = _s([1.0, 2.0], ["2024-01-05", "2024-01-08"])  # piątek, poniedziałek
    out = tp.calendar_ffill(s, "2024-01-04", "2024-01-09")
    assert np.isnan(out.iloc[0])  # przed pierwszą obserwacją — brak
    assert out.loc["2024-01-06":"2024-01-07"].tolist() == [1.0, 1.0]  # weekend = piątek
    assert out.loc["2024-01-08"] == 2.0 and out.loc["2024-01-09"] == 2.0


def test_fx_inversion_and_direct_quote():
    raw = {
        "DEXJPUS": _s([100.0, 125.0], ["2024-01-01", "2024-01-02"]),
        "DEXUSEU": _s([1.1, 1.2], ["2024-01-01", "2024-01-02"]),
    }
    p = tp.build_panel(raw, "2024-01-01", "2024-01-02")
    assert p["DEXJPUS"].tolist() == pytest.approx([0.01, 0.008])  # USD za 1 JPY
    assert p["DEXUSEU"].tolist() == pytest.approx([1.1, 1.2])


def test_bond_index_price_and_carry():
    y = tp.calendar_ffill(
        _s([4.0, 4.0, 5.0], ["2024-01-01", "2024-01-02", "2024-01-03"]), "2024-01-01", "2024-01-03"
    )
    idx = tp.bond_index(y, 8.5)
    r = idx.pct_change().dropna().to_numpy()
    assert r[0] == pytest.approx(0.04 / 365)  # brak zmiany rentowności: tylko odsetki
    assert r[1] == pytest.approx(-8.5 * 0.01 + 0.04 / 365)  # +1 pp rentowności: strata ~8,5 %
    assert idx.iloc[0] == 1.0


def test_nonpositive_price_rejected():
    raw = {"DCOILBRENTEU": _s([10.0, -1.0], ["2024-01-01", "2024-01-02"])}
    with pytest.raises(ValueError):
        tp.build_panel(raw, "2024-01-01", "2024-01-02")


def test_series_lists_consistent():
    assert len(tp.ALL_SERIES) == 19 and len(set(tp.ALL_SERIES)) == 19
    assert "DCOILWTICO" not in tp.ALL_SERIES and "DHHNGSP" not in tp.ALL_SERIES
    assert set(tp.ASSET_CLASS) == set(tp.ALL_SERIES)
