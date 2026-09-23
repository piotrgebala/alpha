"""Testy agents/external_features.py (L1/V1/G1) — dopięcie dzienne z opóźnieniem publikacji i cechy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agents import external_features as ef


def _candles(n: int, start: str = "2021-01-01") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n, freq="4h", tz="UTC")
    rng = np.random.default_rng(0)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({"timestamp": ts, "close": close})


def _daily(days: int, start: str = "2020-12-25") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range(start, periods=days, freq="D", tz="UTC"),
            "value": np.arange(days, dtype=float),
        }
    )


def test_attach_daily_respects_publication_lag_and_ignores_future():
    df = _candles(12)  # 2021-01-01 00:00 → 2021-01-02 20:00
    daily = _daily(10)  # 2020-12-25 (0) … 2021-01-03 (9)
    out = ef.attach_daily(df, daily, {"value": "v"}, available_after=pd.Timedelta(days=1))
    # świeca 2021-01-01 00:00: największy dzień d z d + 1 dzień ≤ t → d = 2020-12-31 (wartość 6)
    assert out.loc[0, "v"] == 6.0
    # świeca 2021-01-02 00:00 → d = 2021-01-01 (7); świeca 2021-01-01 20:00 → nadal 6
    assert out.loc[6, "v"] == 7.0 and out.loc[5, "v"] == 6.0
    # zmiana wartości dni PÓŹNIEJSZYCH nie zmienia świec
    daily2 = daily.copy()
    daily2.loc[daily2["date"] >= "2021-01-02", "value"] = 999.0
    out2 = ef.attach_daily(df, daily2, {"value": "v"}, available_after=pd.Timedelta(days=1))
    assert (out2["v"].iloc[:12] == out["v"].iloc[:12]).all()
    assert "v" not in df.columns


def test_attach_daily_lag_hours_and_staleness():
    df = _candles(6)  # 00:00, 04:00, …, 20:00 dnia 2021-01-01
    daily = _daily(10)
    out = ef.attach_daily(df, daily, {"value": "v"}, available_after=pd.Timedelta(hours=4))
    assert out.loc[0, "v"] == 6.0  # o 00:00 dzień 2021-01-01 (7) jeszcze niedostępny
    assert out.loc[1, "v"] == 7.0  # od 04:00 dostępny
    stale = daily[daily["date"] < "2020-12-20"]  # brak świeżych dni
    out3 = ef.attach_daily(df, _daily(3, "2020-12-10"), {"value": "v"}, pd.Timedelta(days=1))
    assert out3["v"].isna().all() and len(stale) == 0
    with pytest.raises(ValueError):
        ef.attach_daily(df, daily, {"nie_ma": "v"}, pd.Timedelta(days=1))


def test_daily_log_change_and_ex_supply_feature():
    daily = _daily(10)
    daily["SplyExNtv"] = 100.0 * 1.01 ** np.arange(10)
    d7 = ef.daily_log_change(daily, "SplyExNtv", 7, "x7")
    assert d7["x7"].iloc[:7].isna().all()
    assert d7["x7"].iloc[7] == pytest.approx(7 * np.log(1.01))
    df = _candles(4)
    df["ex_supply_change_7d_d"] = [0.01, np.nan, -0.02, 0.0]
    f = ef.compute_ex_supply_change_7d(df)
    assert f.iloc[0] == 0.01 and np.isnan(f.iloc[1])
    with pytest.raises(ValueError):
        ef.compute_ex_supply_change_7d(_candles(3))


def test_vrp_and_fng_features():
    df = _candles(400)
    df["dvol_d"] = 60.0
    rv = ef.compute_realized_vol_30d(df)
    assert (
        rv.iloc[: ef.RV_WINDOW_CANDLES].isna().all()
        and rv.iloc[ef.RV_WINDOW_CANDLES :].notna().all()
    )
    # sd log-zwrotu ≈ 0,01 na 4h → annualizowana ≈ 0,01·√2190 ≈ 0,47
    assert 0.35 < rv.iloc[-1] < 0.6
    vrp = ef.compute_vrp_30d(df)
    assert vrp.iloc[-1] == pytest.approx(0.60 - rv.iloc[-1])
    df["fng_d"] = 25.0
    assert (ef.compute_fng_level(df) == 0.25).all()
    with pytest.raises(ValueError):
        ef.compute_vrp_30d(_candles(3))
    with pytest.raises(ValueError):
        ef.compute_fng_level(_candles(3))


def test_registry_and_sources_consistent():
    assert set(ef.EXTERNAL_FEATURE_FUNCTIONS) == set(ef.FEATURE_SOURCES)
    for _feat, (src, cols) in ef.FEATURE_SOURCES.items():
        assert src in ef.SOURCES and cols
