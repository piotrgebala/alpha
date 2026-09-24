"""Testy czystych funkcji data/fetch_listings.py (runda NL1) — bez sieci."""

from __future__ import annotations

import pandas as pd
import pytest

from data import fetch_listings as fl


def test_parse_first_key_date():
    xml = (
        "<ListBucketResult><Contents><Key>data/futures/um/daily/klines/WIFUSDT/1d/"
        "WIFUSDT-1d-2024-01-18.zip</Key></Contents></ListBucketResult>"
    )
    assert fl.parse_first_key_date(xml) == pd.Timestamp("2024-01-18", tz="UTC")
    assert fl.parse_first_key_date("<ListBucketResult></ListBucketResult>") is None


@pytest.mark.parametrize(
    "sym,base",
    [
        ("1000PEPEUSDT", "PEPE"),
        ("PEPEUSDT", "PEPE"),
        ("1MBABYDOGEUSDT", "BABYDOGE"),
        ("1000000MOGUSDT", "MOG"),
        ("1INCHUSDT", "1INCH"),
        ("BTCUSDT", "BTC"),
    ],
)
def test_normalized_base(sym, base):
    assert fl.normalized_base(sym) == base


def test_classify_symbol():
    assert fl.classify_symbol("BTCDOMUSDT", None) == "INDEX"
    assert fl.classify_symbol("USDCUSDT", None) == "STABLE"
    assert fl.classify_symbol("XYZUSDT", None) == "CRYPTO"
    assert fl.classify_symbol("TSLAUSDT", {"contractType": "TRADIFI_PERPETUAL"}) == "TRADIFI"
    assert (
        fl.classify_symbol("ABCUSDT", {"contractType": "PERPETUAL", "underlyingType": "PREMARKET"})
        == "CRYPTO"
    )
    assert fl.classify_symbol("ABCUSDC", None) == "NOT_USDT"


def test_parse_archive_funding_csv():
    text = "calc_time,funding_interval_hours,last_funding_rate\n1709251200000,4,0.00166492\n1709265600000,4,-0.0001\n"
    df = fl.parse_archive_funding_csv(text)
    assert list(df.columns) == ["timestamp", "funding_rate", "interval_h"]
    assert df["timestamp"].iloc[0] == pd.Timestamp("2024-03-01", tz="UTC")
    assert df["funding_rate"].iloc[1] == pytest.approx(-0.0001)
    with pytest.raises(ValueError):
        fl.parse_archive_funding_csv("a,b\n1,2\n")


def test_window_months_spans_month_boundary():
    assert fl.window_months(pd.Timestamp("2024-03-25", tz="UTC"), 20) == ["2024-03", "2024-04"]
    assert fl.window_months(pd.Timestamp("2024-03-01", tz="UTC"), 20) == ["2024-03"]


def test_select_events_reasons():
    ts = lambda s: pd.Timestamp(s, tz="UTC")  # noqa: E731
    firsts = {
        "PEPEUSDT": ts("2023-05-01"),
        "1000PEPEUSDT": ts("2023-05-05"),
        "OLDUSDT": ts("2020-06-01"),
        "NEWUSDT": ts("2024-01-10"),
        "LATEUSDT": ts("2026-06-20"),
        "TSLAUSDT": ts("2025-10-01"),
        "NOFILEUSDT": None,
    }
    infos = {"TSLAUSDT": {"contractType": "TRADIFI_PERPETUAL"}}
    ev = fl.select_events(firsts, infos, last_day=ts("2026-06-15")).set_index("symbol")
    assert ev.loc["PEPEUSDT", "in_sample"]
    assert ev.loc["1000PEPEUSDT", "reason"] == "redenominacja/duplikat bazy"
    assert ev.loc["OLDUSDT", "reason"].startswith("przed bazą")
    assert ev.loc["NEWUSDT", "in_sample"]
    assert ev.loc["LATEUSDT", "reason"] == "okno poza końcem danych"
    assert ev.loc["TSLAUSDT", "reason"] == "klasa:TRADIFI"
    assert "NOFILEUSDT" not in ev.index
