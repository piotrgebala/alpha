"""Testy data/fetch_external.py — parsery i listing bez sieci (runda P3)."""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from data import fetch_external as fe

METRICS_HEADER = (
    "create_time,symbol,sum_open_interest,sum_open_interest_value,"
    "count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,"
    "count_long_short_ratio,sum_taker_long_short_vol_ratio"
)


def test_parse_metrics_csv_dedupes_keep_last_and_casts_float():
    text = (
        METRICS_HEADER + "\n"
        "2020-09-01 00:00:00,BTCUSDT,39080.231,456144339.23,1.175,1.230,1.357,0.783\n"
        "2020-09-01 00:00:00,BTCUSDT,39081.000,456144340.00,1.176,1.231,1.358,0.784\n"
        "2020-09-01 00:05:00,BTCUSDT,39090.000,456200000.00,1.180,1.240,1.360,0.790\n"
    )
    df = fe.parse_metrics_csv(text)
    assert len(df) == 2
    assert str(df["timestamp"].dt.tz) == "UTC"
    assert df.loc[0, "sum_open_interest"] == pytest.approx(39081.0)  # ostatni duplikat wygrywa
    assert df["timestamp"].is_monotonic_increasing
    assert list(df.columns) == ["timestamp", *fe.METRICS_COLUMNS]


def test_parse_metrics_csv_fails_loud_on_missing_column():
    text = "create_time,symbol,sum_open_interest\n2020-09-01 00:00:00,BTCUSDT,1\n"
    with pytest.raises(ValueError, match="brak kolumn"):
        fe.parse_metrics_csv(text)


def _klines_row(open_ms: int, close: float = 100.0) -> str:
    return f"{open_ms},99,101,98,{close},10,{open_ms + 8 * 3_600_000 - 1},1000,7,5,500,0"


def test_parse_klines_csv_with_and_without_header_and_microseconds():
    ms = 1_640_995_200_000  # 2022-01-01 00:00 UTC
    no_header = _klines_row(ms) + "\n" + _klines_row(ms + 8 * 3_600_000, 101.0) + "\n"
    with_header = ",".join(fe.KLINES_RAW_COLUMNS) + "\n" + _klines_row(ms * 1000) + "\n"
    a = fe.parse_klines_csv(no_header)
    b = fe.parse_klines_csv(with_header)
    assert len(a) == 2 and len(b) == 1
    assert a.loc[0, "open_time"] == pd.Timestamp("2022-01-01", tz="UTC")
    assert b.loc[0, "open_time"] == pd.Timestamp("2022-01-01", tz="UTC")  # µs → ms
    assert list(a.columns) == fe.KLINES_KEEP
    assert a["count"].dtype == "int64"


def test_parse_klines_csv_fails_on_wrong_width():
    with pytest.raises(ValueError, match="kolumn"):
        fe.parse_klines_csv("1,2,3\n")


def test_parse_funding_records_sorts_and_dedupes():
    recs = [
        {"symbol": "BTCUSD_PERP", "fundingTime": 1597104000000, "fundingRate": "0.00020000"},
        {"symbol": "BTCUSD_PERP", "fundingTime": 1597075200000, "fundingRate": "0.00010000"},
        {"symbol": "BTCUSD_PERP", "fundingTime": 1597075200000, "fundingRate": "0.00010000"},
    ]
    df = fe.parse_funding_records(recs)
    assert len(df) == 2
    assert df["timestamp"].is_monotonic_increasing
    assert df.loc[0, "funding_rate"] == pytest.approx(0.0001)
    assert fe.parse_funding_records([]).empty
    with pytest.raises(ValueError):
        fe.parse_funding_records([{"fundingTime": 1}])


def test_parse_dvol_and_coinbase_and_fng_shapes():
    dvol = fe.parse_dvol(
        [[1616544000000, 84.8, 95.9, 80.5, 95.0], [1616457600000, 80.0, 81, 79, 80]]
    )
    assert list(dvol["date"].dt.strftime("%Y-%m-%d")) == ["2021-03-23", "2021-03-24"]
    with pytest.raises(ValueError):
        fe.parse_dvol([[1, 2, 3]])

    cb = fe.parse_coinbase_candles(
        [
            [1609545600, 29000, 33000, 29400, 32100, 20.5],
            [1609459200, 28700, 29688, 28990, 29412, 22.2],
        ]
    )
    assert cb["open_time"].is_monotonic_increasing
    assert cb.loc[0, "close"] == pytest.approx(29412.0)
    with pytest.raises(ValueError):
        fe.parse_coinbase_candles([[1, 2]])

    fng = fe.parse_fng(
        [
            {"value": "27", "value_classification": "Fear", "timestamp": "1758585600"},
            {"value": "30", "value_classification": "Fear", "timestamp": "1758499200"},
        ]
    )
    assert fng["date"].is_monotonic_increasing and fng.loc[0, "value"] == 30.0
    assert fe.parse_fng([]).empty


def test_parse_coinmetrics_nulls_become_nan_and_missing_metric_fails():
    rows = [
        {
            "asset": "btc",
            "time": "2021-01-01T00:00:00.000000000Z",
            "AdrActCnt": "1000",
            "TxCnt": None,
        },
        {
            "asset": "btc",
            "time": "2021-01-02T00:00:00.000000000Z",
            "AdrActCnt": "1100",
            "TxCnt": "5",
        },
    ]
    df = fe.parse_coinmetrics(rows, ["AdrActCnt", "TxCnt"])
    assert df["TxCnt"].isna().tolist() == [True, False]
    assert df.loc[1, "AdrActCnt"] == 1100.0
    with pytest.raises(ValueError, match="brak kolumn"):
        fe.parse_coinmetrics(rows, ["AdrActCnt", "HashRate"])


def test_parse_fred_csv_dot_is_missing_and_header_checked():
    df = fe.parse_fred_csv("observation_date,DTB3\n2020-12-01,0.09\n2020-12-02,.\n", "DTB3")
    assert df["value"].isna().tolist() == [False, True]
    with pytest.raises(ValueError):
        fe.parse_fred_csv("observation_date,SOFR\n2020-12-01,0.1\n", "DTB3")


@given(
    start=st.dates(dt.date(2019, 1, 1), dt.date(2026, 12, 31)),
    length=st.integers(0, 3000),
    max_days=st.integers(1, 1000),
)
def test_date_chunks_cover_range_exactly_without_overlap(start, length, max_days):
    end = start + dt.timedelta(days=length)
    chunks = fe.date_chunks(start, end, max_days)
    assert chunks[0][0] == start and chunks[-1][1] == end
    for (a, b), (c, _d) in zip(chunks, chunks[1:], strict=False):
        assert a <= b and c == b + dt.timedelta(days=1)
    assert all((b - a).days + 1 <= max_days for a, b in chunks)
    assert sum((b - a).days + 1 for a, b in chunks) == length + 1


def test_date_chunks_empty_and_invalid():
    assert fe.date_chunks(dt.date(2021, 1, 2), dt.date(2021, 1, 1), 10) == []
    with pytest.raises(ValueError):
        fe.date_chunks(dt.date(2021, 1, 1), dt.date(2021, 1, 2), 0)


def test_contract_expiry():
    assert fe.contract_expiry("BTCUSDT_220325") == pd.Timestamp("2022-03-25", tz="UTC")
    with pytest.raises(ValueError):
        fe.contract_expiry("BTCUSDT")


def test_s3_list_paginates_and_splits_keys_and_prefixes():
    p = "data/futures/um/daily/metrics/BTCUSDT/"
    pages = {
        "": (
            "<IsTruncated>true</IsTruncated>"
            f"<Key>{p}BTCUSDT-metrics-2020-09-01.zip</Key><Key>{p}BTCUSDT-metrics-2020-09-01.zip.CHECKSUM</Key>"
        ),
        f"{p}BTCUSDT-metrics-2020-09-01.zip.CHECKSUM": (
            "<IsTruncated>false</IsTruncated>"
            f"<Key>{p}BTCUSDT-metrics-2020-09-02.zip</Key><Prefix>{p}</Prefix><Prefix>{p}sub/</Prefix>"
        ),
    }

    def fetch(url):
        marker = url.split("&marker=")[1] if "&marker=" in url else ""
        return pages[marker]

    zips, subdirs = fe.s3_list(p, fetch=fetch)
    assert zips == [f"{p}BTCUSDT-metrics-2020-09-01.zip", f"{p}BTCUSDT-metrics-2020-09-02.zip"]
    assert subdirs == [f"{p}sub/"]


def test_save_is_idempotent_unless_force(tmp_path):
    path = fe.target_path(tmp_path, "x")
    fe.save_parquet(pd.DataFrame({"a": [1]}), path)
    assert fe._skip_existing(path, force=False) is True
    assert fe._skip_existing(path, force=True) is False


def test_run_rejects_unknown_source(tmp_path):
    with pytest.raises(ValueError, match="nieznane"):
        fe.run(tmp_path, only=["nie-ma"])


def test_http_get_rejects_non_https_before_any_network():
    for bad in (
        "http://example.com/x",
        "file:///C:/Windows/win.ini",
        "ftp://h/x",
        "data:text/plain,x",
    ):
        with pytest.raises(ValueError, match="tylko https"):
            fe.http_get(bad)


def test_coinmetrics_pagination_uses_token_on_fixed_host(monkeypatch, tmp_path):
    """Adres kolejnej strony budowany z tokenu; `next_page_url` z odpowiedzi jest ignorowany."""
    calls: list[str] = []
    pages = [
        {
            "data": [{"time": "2021-01-01T00:00:00Z", "AdrActCnt": "1"}],
            "next_page_token": "abc",
            "next_page_url": "http://127.0.0.1:9000/evil",
        },
        {"data": [{"time": "2021-01-02T00:00:00Z", "AdrActCnt": "2"}]},
    ]

    def fake_get(url, *a, **k):
        calls.append(url)
        return json.dumps(pages[len(calls) - 1]).encode()

    monkeypatch.setattr(fe, "http_get", fake_get)
    monkeypatch.setattr(fe.time, "sleep", lambda s: None)
    path = fe.fetch_coinmetrics("btc", ["AdrActCnt"], "2021-01-01", tmp_path)
    assert len(calls) == 2
    assert all(u.startswith(fe.COINMETRICS_URL + "?") for u in calls)
    assert "next_page_token=abc" in calls[1] and "evil" not in calls[1]
    assert len(pd.read_parquet(path)) == 2
