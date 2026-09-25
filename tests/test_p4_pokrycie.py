"""Testy backtest/run_p4_pokrycie_onchain.py (P4): mapowanie symboli i pokrycie."""

from __future__ import annotations

import pandas as pd

from backtest import run_p4_pokrycie_onchain as p4


def test_cm_asset_mapping():
    assert p4.cm_asset("BTCUSDT") == "btc"
    assert p4.cm_asset("1000PEPEUSDT") == "pepe"
    assert p4.cm_asset("1000000MOGUSDT") == "mog"
    assert p4.cm_asset("1MBABYDOGEUSDT") == "babydoge"
    assert p4.cm_asset("1INCHUSDT") == "1inch"  # „1” bez mnożnika zostaje


def test_parse_catalog_and_coverage():
    pages = [
        {
            "data": [
                {
                    "asset": "btc",
                    "metrics": [
                        {
                            "metric": "X",
                            "frequencies": [
                                {
                                    "frequency": "1d",
                                    "min_time": "2011-01-01T00:00:00Z",
                                    "community": True,
                                }
                            ],
                        }
                    ],
                },
                {
                    "asset": "sol",
                    "metrics": [
                        {
                            "metric": "X",
                            "frequencies": [
                                {
                                    "frequency": "1d",
                                    "min_time": "2022-06-01T00:00:00Z",
                                    "community": True,
                                }
                            ],
                        }
                    ],
                },
                {
                    "asset": "eth",
                    "metrics": [
                        {
                            "metric": "X",
                            "frequencies": [
                                {
                                    "frequency": "1d",
                                    "min_time": "2015-01-01T00:00:00Z",
                                    "community": False,
                                }
                            ],
                        }
                    ],
                },
            ]
        }
    ]
    avail = p4.parse_catalog(pages, "X")
    assert set(avail) == {"btc", "sol"}
    m1, m2 = pd.Timestamp("2022-01-01", tz="UTC"), pd.Timestamp("2022-07-01", tz="UTC")
    cov = p4.coverage(
        {m1: ["BTCUSDT", "SOLUSDT"], m2: ["BTCUSDT", "SOLUSDT", "ETHUSDT", "XRPUSDT"]}, avail
    )
    assert cov[m1] == 0.5 and cov[m2] == 0.5
