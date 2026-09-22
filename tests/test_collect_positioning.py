"""Testy data/collect_positioning.py — bez sieci."""

from __future__ import annotations

import ccxt
import pandas as pd

from data import collect_positioning as cp

H = 3_600_000


class _Stub:
    def __init__(self, start_ms, n=3, fail=()):
        self.start_ms, self.n, self.fail = start_ms, n, set(fail)

    def __getattr__(self, method):
        if not method.startswith("fapiDataGet"):
            raise AttributeError(method)

        def call(params):
            if method in self.fail:
                raise ccxt.NetworkError("down")
            return [
                {
                    "symbol": params["symbol"],
                    "sumOpenInterest": str(100 + i),
                    "timestamp": str(self.start_ms + i * H),
                }
                for i in range(self.n)
            ]

        return call


def test_records_to_df_types():
    df = cp.records_to_df(
        [{"symbol": "BTCUSDT", "longShortRatio": "1.5", "timestamp": "1700000000000"}]
    )
    assert list(df.columns) == ["longShortRatio", "timestamp"]
    assert df["longShortRatio"].iloc[0] == 1.5
    assert str(df["timestamp"].dt.tz) == "UTC"


def test_merge_append_dedupes_and_keeps_newest():
    a = cp.records_to_df([{"x": "1", "timestamp": str(i * H)} for i in range(3)])
    b = cp.records_to_df([{"x": "9", "timestamp": str(i * H)} for i in range(2, 5)])
    m = cp.merge_append(a, b)
    assert len(m) == 5 and m["timestamp"].is_monotonic_increasing
    assert m.loc[m["timestamp"] == pd.Timestamp(2 * H, unit="ms", tz="UTC"), "x"].item() == 9


def test_collect_appends_across_runs(tmp_path):
    r1 = cp.collect(tmp_path, ["BTCUSDT"], _Stub(0, n=3))
    r2 = cp.collect(tmp_path, ["BTCUSDT"], _Stub(2 * H, n=3))  # 1 zachodzi, 2 nowe
    assert r1["BTCUSDT_openInterestHist"] == 3
    assert r2["BTCUSDT_openInterestHist"] == 2
    df = pd.read_parquet(tmp_path / "BTCUSDT_openInterestHist_1h.parquet")
    assert len(df) == 5


def test_collect_one_failing_endpoint_does_not_stop_others(tmp_path):
    rep = cp.collect(tmp_path, ["BTCUSDT"], _Stub(0, fail={"fapiDataGetTakerlongshortRatio"}))
    assert len(rep["errors"]) == 1
    assert rep["BTCUSDT_openInterestHist"] == 3
    assert not (tmp_path / "BTCUSDT_takerlongshortRatio_1h.parquet").exists()
