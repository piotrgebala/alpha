"""
Testy pobierania historii funding rate (H2 — pierwsze w projekcie źródło informacji
spoza OHLCV).

Zakres: czyszczenie szeregu, wykrywanie dziur w siatce 8h, polityka retry, nazwa pliku
cache. Wszystko bez sieci — giełda podstawiana stubem.
"""

from pathlib import Path

import ccxt
import pandas as pd
import pytest

from data.fetch_funding import (
    FUNDING_COLUMNS,
    _cache_path,
    _clean_funding,
    _fetch_funding_page_with_retry,
    _raw_funding_to_df,
    find_funding_gaps,
)

END = "2026-09-22T00:00:00Z"


def _records(*pairs):
    """[(iso, rate), ...] → lista rekordów w formacie ccxt."""
    return [
        {"timestamp": int(pd.Timestamp(iso).timestamp() * 1000), "fundingRate": rate}
        for iso, rate in pairs
    ]


def _series(*pairs):
    return _raw_funding_to_df(_records(*pairs))


# --- konwersja i czyszczenie ---


def test_raw_funding_to_df_produces_expected_schema():
    df = _series(("2020-01-01T00:00:00Z", 0.0001))
    assert list(df.columns) == FUNDING_COLUMNS
    assert df["timestamp"].dt.tz is not None
    assert df.loc[0, "funding_rate"] == pytest.approx(0.0001)


def test_raw_funding_to_df_empty_input_keeps_schema():
    """Pusty wynik nie może dać DataFrame bez kolumn — to psuło testy w metrics.py."""
    df = _raw_funding_to_df([])
    assert list(df.columns) == FUNDING_COLUMNS
    assert df.empty


def test_clean_funding_rounds_subsecond_timestamps():
    """
    Binance zwraca znaczniki rozjechane o milisekundy (np. ...T00:00:00.007Z).
    Bez zaokrąglenia psułoby to i wykrywanie dziur, i późniejsze łączenie ze świecami.
    """
    df = _series(("2026-09-21T00:00:00.007Z", 4.2e-05))
    out = _clean_funding(df, END)
    assert out.loc[0, "timestamp"] == pd.Timestamp("2026-09-21T00:00:00Z")


def test_clean_funding_removes_duplicates_and_sorts():
    df = _series(
        ("2020-01-01T08:00:00Z", 0.0002),
        ("2020-01-01T00:00:00Z", 0.0001),
        ("2020-01-01T08:00:00Z", 0.0009),  # duplikat — zostaje PIERWSZY napotkany
    )
    out = _clean_funding(df, END)
    assert len(out) == 2
    assert out["timestamp"].is_monotonic_increasing
    assert out.loc[1, "funding_rate"] == pytest.approx(0.0002)


def test_clean_funding_respects_end_boundary_exclusive():
    df = _series(("2020-01-01T00:00:00Z", 0.0001), ("2020-01-02T00:00:00Z", 0.0002))
    out = _clean_funding(df, "2020-01-02T00:00:00Z")
    assert len(out) == 1
    assert out.loc[0, "timestamp"] == pd.Timestamp("2020-01-01T00:00:00Z")


# --- dziury w siatce 8h ---


def test_find_funding_gaps_clean_series_reports_nothing():
    df = _clean_funding(
        _series(
            ("2020-01-01T00:00:00Z", 0.0001),
            ("2020-01-01T08:00:00Z", 0.0001),
            ("2020-01-01T16:00:00Z", 0.0001),
        ),
        END,
    )
    assert find_funding_gaps(df).empty


def test_find_funding_gaps_detects_missing_settlement():
    df = _clean_funding(
        _series(
            ("2020-01-01T00:00:00Z", 0.0001),
            # brak 08:00
            ("2020-01-01T16:00:00Z", 0.0001),
        ),
        END,
    )
    gaps = find_funding_gaps(df)
    assert len(gaps) == 1
    assert gaps.iloc[0]["timestamp"] == pd.Timestamp("2020-01-01T16:00:00Z")


def test_find_funding_gaps_tolerates_seconds_of_drift():
    """Przesunięcie o sekundy to normalne zachowanie giełdy, nie dziura w danych."""
    df = _clean_funding(
        _series(("2020-01-01T00:00:00Z", 0.0001), ("2020-01-01T08:00:12Z", 0.0001)), END
    )
    assert find_funding_gaps(df).empty


def test_find_funding_gaps_handles_short_series():
    assert find_funding_gaps(pd.DataFrame(columns=FUNDING_COLUMNS)).empty
    assert find_funding_gaps(_series(("2020-01-01T00:00:00Z", 0.0001))).empty


# --- retry (ta sama polityka co fetch_ohlcv) ---


class _FlakyFundingExchange:
    """Stub: rzuca NetworkError `n_failures` razy, potem zwraca stałą stronę."""

    def __init__(self, n_failures: int):
        self.n_failures = n_failures
        self.calls = 0

    def fetch_funding_rate_history(self, symbol, since=None, limit=None):
        self.calls += 1
        if self.calls <= self.n_failures:
            raise ccxt.RequestTimeout("timeout")
        return [{"timestamp": since, "fundingRate": 0.0001}]


def test_funding_page_retries_on_network_error_then_succeeds(monkeypatch):
    monkeypatch.setattr("data.fetch_funding.time.sleep", lambda _s: None)
    ex = _FlakyFundingExchange(n_failures=2)
    page = _fetch_funding_page_with_retry(ex, "BTC/USDT:USDT", since=0, max_retries=5)
    assert page == [{"timestamp": 0, "fundingRate": 0.0001}]
    assert ex.calls == 3


def test_funding_page_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr("data.fetch_funding.time.sleep", lambda _s: None)
    ex = _FlakyFundingExchange(n_failures=10)
    with pytest.raises(ccxt.NetworkError):
        _fetch_funding_page_with_retry(ex, "BTC/USDT:USDT", since=0, max_retries=3)
    assert ex.calls == 3


def test_funding_page_does_not_retry_exchange_error(monkeypatch):
    """Zły symbol to błąd konfiguracji — retry tylko maskowałby problem."""
    monkeypatch.setattr("data.fetch_funding.time.sleep", lambda _s: None)

    class _BadSymbolExchange:
        calls = 0

        def fetch_funding_rate_history(self, *args, **kwargs):
            self.calls += 1
            raise ccxt.BadSymbol("no such market")

    ex = _BadSymbolExchange()
    with pytest.raises(ccxt.BadSymbol):
        _fetch_funding_page_with_retry(ex, "XXX", since=0, max_retries=5)
    assert ex.calls == 1


# --- cache ---


def test_cache_path_encodes_symbol_and_range():
    """Nazwa pliku koduje pełny zakres — zmiana okna daje NOWY plik, nie nadpisuje starego."""
    p = _cache_path("data/raw", "BTC/USDT:USDT", "2019-09-10T00:00:00Z", "2026-07-01T00:00:00Z")
    assert p == Path("data/raw") / "BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet"
    assert p != _cache_path(
        "data/raw", "BTC/USDT:USDT", "2023-07-01T00:00:00Z", "2026-07-01T00:00:00Z"
    )


def test_cache_path_does_not_collide_with_ohlcv():
    """Funding i świece leżą w tym samym katalogu — nazwy nie mogą się zderzyć."""
    from data.fetch_ohlcv import _cache_path as ohlcv_cache_path

    funding = _cache_path("data/raw", "BTC/USDT:USDT", "2019-09-10T00:00:00Z", "2026-07-01T00:00:00Z")
    candles = ohlcv_cache_path(
        "data/raw", "BTC/USDT:USDT", "4h", "2019-09-10T00:00:00Z", "2026-07-01T00:00:00Z"
    )
    assert funding != candles
