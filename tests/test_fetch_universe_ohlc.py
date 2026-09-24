"""Testy czystej funkcji data/fetch_universe_ohlc.py (LQ1) — bez sieci."""

import pandas as pd

from data.fetch_universe_ohlc import membership_months


def test_membership_months_adds_previous_month():
    m = pd.Timestamp("2022-03-01", tz="UTC")
    out = membership_months({m: ["AUSDT", "BUSDT"]})
    assert out == {
        ("AUSDT", "2022-03"),
        ("AUSDT", "2022-02"),
        ("BUSDT", "2022-03"),
        ("BUSDT", "2022-02"),
    }
