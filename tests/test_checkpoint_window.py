"""
test_checkpoint_window.py

CLAUDE.md zasada 20: nowe rundy liczą się od `data.min_start`. Filtr mieszka w jednym miejscu
(`backtest/checkpoint_lib.py::fetch_window`), a `fetch_native` (skrypty zamrożone) go NIE nakłada.
"""

from __future__ import annotations

import pandas as pd
import pytest
import yaml

import backtest.checkpoint_lib as lib

CFG = {
    "primary_symbol": "BTC/USDT:USDT",
    "start": "2019-09-10T00:00:00Z",
    "end": "2026-07-01T00:00:00Z",
    "cache_dir": "data/raw",
    "exchange_id": "binanceusdm",
    "timeframe_start_overrides": {"4h": "2019-09-10T00:00:00Z"},
    "min_start": "2021-01-01T00:00:00Z",
}


@pytest.fixture
def fake_cache(monkeypatch):
    ts = pd.date_range("2020-06-01", "2021-06-01", freq="4h", tz="UTC")
    df = pd.DataFrame(
        {"timestamp": ts, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}
    )
    calls = []

    def fake(**kwargs):
        calls.append(kwargs)
        return df.copy()

    monkeypatch.setattr(lib, "get_ohlcv_cached", fake)
    return df, calls


def test_fetch_window_keeps_only_candles_from_min_start(fake_cache):
    df, calls = fake_cache
    out = lib.fetch_window(CFG, "4h")
    assert (out["timestamp"] >= pd.Timestamp("2021-01-01", tz="UTC")).all()
    assert len(out) == (df["timestamp"] >= pd.Timestamp("2021-01-01", tz="UTC")).sum()
    assert list(out.index) == list(range(len(out)))
    # klucz cache bez zmian: start z override, nie z min_start (żadnego nowego pobierania)
    assert calls[0]["start"] == "2019-09-10T00:00:00Z"


def test_fetch_native_does_not_filter(fake_cache):
    df, _ = fake_cache
    assert len(lib.fetch_native(CFG, "4h")) == len(df)


def test_fetch_window_requires_min_start(fake_cache):
    cfg = {k: v for k, v in CFG.items() if k != "min_start"}
    with pytest.raises(ValueError):
        lib.fetch_window(cfg, "4h")


def test_project_config_declares_min_start_from_2021():
    data_cfg = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["data"]
    assert pd.Timestamp(data_cfg["min_start"]) == pd.Timestamp("2021-01-01T00:00:00Z")
