"""Testy agents/positioning_features.py (runda O1) — dopięcie snapshotu bez lookaheadu i cecha OI."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agents import positioning_features as pf


def _candles(n: int, start: str = "2021-01-01") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"timestamp": ts, "close": np.linspace(100.0, 110.0, n)})


def _metrics(ts_list, oi_list) -> pd.DataFrame:
    return pd.DataFrame(
        {"timestamp": pd.to_datetime(ts_list, utc=True), "oi": np.asarray(oi_list, dtype=float)}
    )


def test_attach_uses_last_snapshot_inside_candle_and_never_future():
    df = _candles(2)  # świece 00:00 i 04:00
    m = _metrics(
        ["2021-01-01 00:00", "2021-01-01 03:55", "2021-01-01 04:00", "2021-01-01 07:55"],
        [1.0, 2.0, 3.0, 4.0],
    )
    out = pf.attach_positioning(df, m)
    assert out.loc[0, "oi_close"] == 2.0  # ostatni WEWNĄTRZ świecy 00:00 (03:55), nie 04:00
    assert out.loc[1, "oi_close"] == 4.0
    # odczyt DOKŁADNIE o otwarciu należy do poprzedniej świecy — sam nie wystarcza
    only_open = _metrics(["2021-01-01 04:00"], [9.0])
    out2 = pf.attach_positioning(df, only_open)
    assert np.isnan(out2.loc[0, "oi_close"]) and np.isnan(out2.loc[1, "oi_close"])
    assert "oi_close" not in df.columns  # nie mutuje


def test_attach_gap_inside_candle_takes_earlier_snapshot_but_not_previous_candle():
    df = _candles(2)
    m = _metrics(["2021-01-01 00:05", "2021-01-01 01:00"], [5.0, 7.0])  # tylko pierwsza świeca
    out = pf.attach_positioning(df, m)
    assert out.loc[0, "oi_close"] == 7.0  # ostatni dostępny w świecy 00:00–03:55
    assert np.isnan(out.loc[1, "oi_close"])  # świeca 04:00 bez odczytu → NaN, bez sięgania wstecz


def test_load_metrics_masks_nonpositive(tmp_path):
    p = tmp_path / "m.parquet"
    pd.DataFrame(
        {
            "timestamp": pd.date_range("2021-01-01", periods=4, freq="5min", tz="UTC"),
            "sum_open_interest": [10.0, 0.0, -1.0, 12.0],
        }
    ).to_parquet(p, index=False)
    m = pf.load_metrics(p)
    assert list(m["oi"]) == [10.0, 12.0]  # zera i ujemne odrzucone → asof weźmie poprzedni ważny
    with pytest.raises(ValueError):
        pd.DataFrame({"x": [1]}).to_parquet(p, index=False)
        pf.load_metrics(p)


def test_oi_change_24h_values_and_warmup():
    df = _candles(16)
    df["oi_close"] = 100.0 * 1.1 ** np.arange(16)
    f = pf.compute_oi_change_24h(df)
    assert f.iloc[:6].isna().all()
    assert f.iloc[6] == pytest.approx(6 * np.log(1.1))
    df.loc[7, "oi_close"] = np.nan  # NaN wejścia propaguje się na t=7 (licznik) i t=13 (mianownik)
    f2 = pf.compute_oi_change_24h(df)
    assert np.isnan(f2.iloc[7]) and np.isnan(f2.iloc[13])
    assert f2.drop([7, 13]).iloc[6:].notna().all()
    with pytest.raises(ValueError):
        pf.compute_oi_change_24h(_candles(3))


def test_compute_positioning_features_adds_registered_columns():
    df = _candles(8)
    df["oi_close"] = np.linspace(50.0, 60.0, 8)
    out = pf.compute_positioning_features(df)
    assert set(pf.POSITIONING_FEATURE_FUNCTIONS) <= set(out.columns)
    assert "oi_change_24h" not in df.columns
    assert out["oi_change_24h"].notna().sum() == 2  # 8 świec − 6 warm-up
