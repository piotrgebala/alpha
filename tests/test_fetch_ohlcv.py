"""
Testy logiki przetwarzania danych OHLCV.

Celowo NIE testują samego połączenia z giełdą (wymagałoby sieci i byłoby
niedeterministyczne w CI). Testują _clean_ohlcv i find_gaps na syntetycznych
danych — to jest logika, którą faktycznie da się i trzeba zweryfikować.
"""

import pandas as pd
import pytest

from data.fetch_ohlcv import _clean_ohlcv, find_gaps


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
