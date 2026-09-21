"""
Testy logiki przetwarzania danych OHLCV.

Celowo NIE testują samego połączenia z giełdą (wymagałoby sieci i byłoby
niedeterministyczne w CI). Testują _clean_ohlcv i find_gaps na syntetycznych
danych — to jest logika, którą faktycznie da się i trzeba zweryfikować.
"""

import pandas as pd
import pytest

from data.fetch_ohlcv import _clean_ohlcv, find_gaps, resample_ohlcv


def _make_df(timestamps: list[str]) -> pd.DataFrame:
    n = len(timestamps)
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps, utc=True),
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.5] * n,
            "volume": [10.0] * n,
        }
    )


def test_clean_ohlcv_removes_duplicate_timestamps():
    df = _make_df(
        ["2026-01-01T00:00Z", "2026-01-01T00:05Z", "2026-01-01T00:05Z", "2026-01-01T00:10Z"]
    )
    cleaned = _clean_ohlcv(df, end="2026-01-02T00:00Z")
    assert cleaned["timestamp"].is_unique
    assert len(cleaned) == 3


def test_clean_ohlcv_sorts_chronologically():
    df = _make_df(["2026-01-01T00:10Z", "2026-01-01T00:00Z", "2026-01-01T00:05Z"])
    cleaned = _clean_ohlcv(df, end="2026-01-02T00:00Z")
    assert cleaned["timestamp"].is_monotonic_increasing


def test_clean_ohlcv_respects_end_boundary_exclusive():
    df = _make_df(["2026-01-01T00:00Z", "2026-01-01T00:05Z", "2026-01-01T00:10Z"])
    cleaned = _clean_ohlcv(df, end="2026-01-01T00:10Z")
    assert cleaned["timestamp"].max() < pd.Timestamp("2026-01-01T00:10Z", tz="UTC")
    assert len(cleaned) == 2


def test_find_gaps_clean_data_reports_nothing():
    timestamps = pd.date_range("2026-01-01", periods=10, freq="5min", tz="UTC")
    df = _make_df([t.isoformat() for t in timestamps])
    gaps = find_gaps(df, timeframe_minutes=5)
    assert len(gaps) == 0


def test_find_gaps_detects_missing_candles():
    # dziura: brakuje świec między 00:05 i 01:00
    timestamps = ["2026-01-01T00:00Z", "2026-01-01T00:05Z", "2026-01-01T01:00Z"]
    df = _make_df(timestamps)
    gaps = find_gaps(df, timeframe_minutes=5)
    assert len(gaps) == 1
    assert gaps.iloc[0]["gap_before"] == pd.Timedelta(minutes=55)


def test_find_gaps_does_not_raise():
    """find_gaps raportuje, nie blokuje pipeline — kluczowe dla fault tolerance z PRD."""
    timestamps = ["2026-01-01T00:00Z", "2026-01-05T00:00Z"]  # ogromna dziura
    df = _make_df(timestamps)
    gaps = find_gaps(df, timeframe_minutes=5)  # nie powinno rzucić
    assert len(gaps) == 1


def _make_5m_ohlcv_with_known_values(n_hours: int = 3) -> pd.DataFrame:
    """
    12 świec 5m na godzinę, wartości tak dobrane, żeby agregacja 1h była ręcznie
    weryfikowalna: open/high/low/close rosną monotonicznie w obrębie każdej godziny,
    więc oczekiwany wynik resample to (open=pierwsza świeca, high=ostatnia=max,
    low=pierwsza=min, close=ostatnia, volume=suma 12 świec = 12*10=120).
    """
    n = n_hours * 12
    timestamps = pd.date_range("2026-01-01T00:00", periods=n, freq="5min", tz="UTC")
    idx_in_hour = pd.Series(range(n)) % 12
    base = 100.0 + (pd.Series(range(n)) // 12) * 100.0  # poziom bazowy różny per godzina
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": base + idx_in_hour,
            "high": base + idx_in_hour + 0.5,
            "low": base + idx_in_hour - 0.5,
            "close": base + idx_in_hour + 0.1,
            "volume": [10.0] * n,
        }
    )


def test_resample_ohlcv_aggregates_ohlc_and_volume_correctly():
    df = _make_5m_ohlcv_with_known_values(n_hours=2)
    resampled = resample_ohlcv(df, "1h")

    assert len(resampled) == 2
    assert list(resampled.columns) == ["timestamp", "open", "high", "low", "close", "volume"]

    first_hour = resampled.iloc[0]
    assert first_hour["timestamp"] == pd.Timestamp("2026-01-01T00:00", tz="UTC")
    assert first_hour["open"] == pytest.approx(100.0)  # pierwsza świeca 5m tej godziny
    assert first_hour["high"] == pytest.approx(100.0 + 11 + 0.5)  # ostatnia świeca ma max high
    assert first_hour["low"] == pytest.approx(100.0 - 0.5)  # pierwsza świeca ma min low
    assert first_hour["close"] == pytest.approx(100.0 + 11 + 0.1)  # ostatnia świeca 5m
    assert first_hour["volume"] == pytest.approx(120.0)  # suma 12 x 10.0


def test_resample_ohlcv_4h_bucket_matches_three_1h_buckets():
    # Niezmiennik spójności: agregacja 5m->4h musi dać ten sam wynik co agregacja
    # 5m->1h, a potem 1h->4h (agregacja jest asocjatywna dla open/high/low/close/volume).
    df = _make_5m_ohlcv_with_known_values(n_hours=8)
    direct_4h = resample_ohlcv(df, "4h")

    hourly = resample_ohlcv(df, "1h")
    two_step_4h = resample_ohlcv(hourly, "4h")

    pd.testing.assert_frame_equal(direct_4h, two_step_4h)


def test_resample_ohlcv_drops_incomplete_trailing_bucket():
    # 90 minut = 1 pełna godzina + 30 min niepełnej — niepełny bucket musi zniknąć
    # (dropna), a nie zostać zwrócony z brakującymi polami.
    timestamps = pd.date_range("2026-01-01T00:00", periods=18, freq="5min", tz="UTC")  # 90 min
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100.0] * 18,
            "high": [101.0] * 18,
            "low": [99.0] * 18,
            "close": [100.5] * 18,
            "volume": [10.0] * 18,
        }
    )
    resampled = resample_ohlcv(df, "1h")
    assert len(resampled) == 1
    assert resampled["timestamp"].iloc[0] == pd.Timestamp("2026-01-01T00:00", tz="UTC")


def test_resample_ohlcv_rejects_unsupported_timeframe():
    df = _make_5m_ohlcv_with_known_values(n_hours=1)
    with pytest.raises(ValueError):
        resample_ohlcv(df, "15m")
