"""Testy data/fetch_korea.py (runda KP1) — parser Upbit i stronicowanie bez sieci."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from data import fetch_korea as fk


def _row(day: str, close: float = 100.0) -> dict:
    return {
        "market": "KRW-BTC",
        "candle_date_time_utc": f"{day}T00:00:00",
        "candle_date_time_kst": f"{day}T09:00:00",
        "opening_price": 99.0,
        "high_price": 101.0,
        "low_price": 98.0,
        "trade_price": close,
        "timestamp": 0,
        "candle_acc_trade_price": 1000.0,
        "candle_acc_trade_volume": 10.0,
    }


def test_parse_upbit_days_sorts_ascending_dedupes_and_casts():
    rows = [_row("2021-01-03", 3.0), _row("2021-01-02", 2.0), _row("2021-01-02", 2.0)]
    df = fk.parse_upbit_days(rows)
    assert list(df.columns) == list(fk.UPBIT_FIELDS.values())
    assert len(df) == 2
    assert str(df["open_time"].dt.tz) == "UTC"
    assert df["open_time"].is_monotonic_increasing
    assert df["close"].tolist() == [2.0, 3.0]
    assert df["close"].dtype == float


def test_parse_upbit_days_fails_loud_on_missing_field():
    bad = _row("2021-01-02")
    del bad["trade_price"]
    with pytest.raises(ValueError, match="brak pól"):
        fk.parse_upbit_days([_row("2021-01-03"), bad])


def test_parse_upbit_days_fails_on_candle_not_at_utc_midnight():
    bad = _row("2021-01-02")
    bad["candle_date_time_utc"] = "2021-01-02T09:00:00"  # pomylony czas KST jako UTC
    with pytest.raises(ValueError, match="00:00 UTC"):
        fk.parse_upbit_days([bad])


def test_parse_upbit_days_empty_and_next_to():
    empty = fk.parse_upbit_days([])
    assert empty.empty and list(empty.columns) == list(fk.UPBIT_FIELDS.values())
    assert fk.next_to(empty) is None
    df = fk.parse_upbit_days([_row("2021-01-03"), _row("2021-01-02")])
    assert fk.next_to(df) == "2021-01-02T00:00:00Z"


def test_fetch_upbit_daily_paginates_backwards_without_gaps(tmp_path, monkeypatch):
    days = pd.date_range("2019-01-01", periods=450, freq="D", tz="UTC")
    calls = []

    def fake_http_get(url: str) -> bytes:
        to = pd.Timestamp(url.split("to=")[1].replace("%3A", ":"))
        calls.append(to)
        before = [d for d in days if d < to][-fk.UPBIT_MAX_CANDLES :]
        return json.dumps([_row(d.strftime("%Y-%m-%d")) for d in reversed(before)]).encode()

    monkeypatch.setattr(fk, "http_get", fake_http_get)
    monkeypatch.setattr(fk.time, "sleep", lambda s: None)
    now = days[-1] + pd.Timedelta(hours=5)
    path = fk.fetch_upbit_daily("KRW-BTC", "2019-01-01", tmp_path, now=now)
    df = pd.read_parquet(path)
    assert len(calls) == 3  # 200 + 200 + 49
    assert df["open_time"].tolist() == list(days[:-1])  # dzień w toku pominięty, bez dziur
    assert fk.fetch_upbit_daily("KRW-BTC", "2019-01-01", tmp_path, now=now) is None  # idempotencja
