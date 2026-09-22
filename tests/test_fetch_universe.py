"""Testy data/fetch_universe.py — bez sieci (stuby giełdy i listingu S3)."""

from __future__ import annotations

import ccxt
import pandas as pd

from data import fetch_universe as fu

START_MS = int(pd.Timestamp("2021-01-01T00:00:00Z").value // 1_000_000)
END_MS = int(pd.Timestamp("2021-03-01T00:00:00Z").value // 1_000_000)


def test_parse_archive_listing():
    xml = (
        "<ListBucketResult><CommonPrefixes><Prefix>data/futures/um/monthly/fundingRate/BTCUSDT/</Prefix>"
        "</CommonPrefixes><CommonPrefixes><Prefix>data/futures/um/monthly/fundingRate/LUNAUSDT/</Prefix>"
        "</CommonPrefixes></ListBucketResult>"
    )
    assert fu.parse_archive_listing(xml) == ["BTCUSDT", "LUNAUSDT"]


def test_list_archive_symbols_paginates_with_marker():
    pages = {
        "": "<IsTruncated>true</IsTruncated><Prefix>data/futures/um/monthly/fundingRate/AUSDT/</Prefix>",
        "data/futures/um/monthly/fundingRate/AUSDT/": "<IsTruncated>false</IsTruncated>"
        "<Prefix>data/futures/um/monthly/fundingRate/BUSDT/</Prefix>",
    }

    def fetch(url):
        marker = url.split("&marker=")[1] if "&marker=" in url else ""
        return pages[marker]

    assert fu.list_archive_symbols(fetch=fetch) == ["AUSDT", "BUSDT"]


def test_select_universe_keeps_delisted_drops_tradifi_stables_and_non_usdt():
    archive = [
        "BTCUSDT",
        "LUNAUSDT",
        "USDCUSDT",
        "TSLAUSDT",
        "ETHBUSD",
        "BTCUSDT_230929",
        "1000PEPEUSDT",
    ]
    out = fu.select_universe(archive, tradifi_ids={"TSLAUSDT"})
    assert out == ["1000PEPEUSDT", "BTCUSDT", "LUNAUSDT"]


class _StubExchange:
    """Giełda z 8h fundingiem i dziennymi świecami, stronicowanie jak na Binance."""

    def __init__(self):
        self.calls = 0

    def fapiPublicGetFundingRate(self, params):
        self.calls += 1
        out, ts = [], params["startTime"]
        step = 8 * 3_600_000
        ts = ts + (-ts) % step  # najbliższe rozliczenie >= startTime
        while ts <= params["endTime"] and len(out) < params["limit"]:
            out.append({"fundingTime": ts + 5, "fundingRate": "0.0001"})
            ts += step
        return out

    def fapiPublicGetKlines(self, params):
        out, ts = [], params["startTime"]
        while ts <= params["endTime"] and len(out) < params["limit"]:
            out.append([ts, "1", "1", "1", "2.0", "10", ts + fu.DAY_MS - 1, "123.0"])
            ts += fu.DAY_MS
        return out


def test_fetch_funding_raw_paginates_without_duplicates(monkeypatch):
    monkeypatch.setattr(fu, "FUNDING_PAGE_LIMIT", 50)
    ex = _StubExchange()
    df = fu.fetch_funding_raw(ex, "XUSDT", START_MS, END_MS, pacing_s=0)
    assert ex.calls > 1
    assert df["timestamp"].is_monotonic_increasing and df["timestamp"].is_unique
    assert len(df) == (END_MS - START_MS) // (8 * 3_600_000)


def test_fetch_klines_keeps_only_closed_candles():
    df = fu.fetch_klines_1d_raw(_StubExchange(), "XUSDT", START_MS, END_MS, pacing_s=0)
    assert len(df) == (END_MS - START_MS) // fu.DAY_MS
    assert (
        df["open_time"] + pd.Timedelta(days=1) <= pd.Timestamp(END_MS, unit="ms", tz="UTC")
    ).all()
    assert df["quote_volume"].iloc[0] == 123.0


def test_call_with_retry_retries_network_error_only(monkeypatch):
    monkeypatch.setattr(fu.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def flaky(params):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ccxt.NetworkError("boom")
        return ["ok"]

    assert fu._call_with_retry(flaky, {}) == ["ok"]


def test_fetch_universe_cached_skips_cached_symbols(tmp_path):
    ex = _StubExchange()
    r1 = fu.fetch_universe_cached(
        ["AUSDT"], "2021-01-01T00:00:00Z", "2021-01-10T00:00:00Z", tmp_path, ex, pacing_s=0
    )
    r2 = fu.fetch_universe_cached(
        ["AUSDT"], "2021-01-01T00:00:00Z", "2021-01-10T00:00:00Z", tmp_path, ex, pacing_s=0
    )
    assert r1["fetched"] == 1 and r2["cached"] == 1


def test_bad_symbol_is_recorded_as_empty_not_fatal(tmp_path):
    class _Bad(_StubExchange):
        def fapiPublicGetKlines(self, params):
            raise ccxt.BadSymbol("Invalid symbol.")

    r = fu.fetch_universe_cached(
        ["ZUSDT"], "2021-01-01T00:00:00Z", "2021-01-10T00:00:00Z", tmp_path, _Bad(), pacing_s=0
    )
    assert r["empty"] == ["ZUSDT"]
    f_path, k_path = fu.cache_paths(tmp_path, "ZUSDT")
    assert f_path.exists() and k_path.exists()
