"""Testy rachunku E1K (`backtest/run_e1k_czestosc.py`) — bez sieci i bez cen: dni zamknięte, przerwy,
przedział Poissona, σ dnia, próg uogólniony (tożsamość p > p* ⇔ μ > C, także w granicy dużego n),
wymagane n, iloraz do progu i przebieg end-to-end na syntetycznych plikach obu giełd.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import e1_kaskady as e1
from backtest import run_e1k_czestosc as rk
from backtest.metrics import measurability_report

D0 = 1_790_812_800_000  # 2026-10-01 00:00 UTC
MIN = 60_000


def test_closed_day_files(tmp_path):
    for d in ("2026-10-01", "2026-10-02", "2026-10-03"):
        (tmp_path / f"{d}.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "status.json").write_text("{}", encoding="utf-8")
    assert [d for d, _ in rk.closed_day_files(tmp_path, "2026-10-03")] == [
        "2026-10-01",
        "2026-10-02",
    ]


def test_gaps_detects_silence_and_tail():
    evs = [e1.Liq("X", D0 + m * MIN, "long", Decimal(1)) for m in (0, 10, 40)]
    g = rk.gaps(evs, D0, D0 + 60 * MIN)
    assert g == [(D0 + 10 * MIN, D0 + 40 * MIN), (D0 + 40 * MIN, D0 + 60 * MIN)]


def test_poisson_ci_known_values():
    lo, hi = rk.poisson_ci(0)
    assert lo == 0.0 and hi == pytest.approx(3.689, abs=1e-3)
    lo, hi = rk.poisson_ci(9)
    assert lo == pytest.approx(4.115, abs=1e-3) and hi == pytest.approx(17.084, abs=1e-3)


def test_sigma_day():
    assert rk.sigma_day(0.05, 1) == pytest.approx(0.05)
    assert rk.sigma_day(0.05, 0.3) == pytest.approx(0.05)  # k < 1 traktowane jak 1
    assert rk.sigma_day(0.05, 4, rho=1.0) == pytest.approx(0.05)
    assert rk.sigma_day(0.05, 4, rho=0.0) == pytest.approx(0.025)


def test_required_n_hand_value():
    assert rk.required_n(0.0075, 0.05, 0.005) == pytest.approx(
        (1.96 * 0.05 / 0.0025) ** 2, rel=1e-4
    )
    assert math.isinf(rk.required_n(0.005, 0.05, 0.005))
    assert rk.required_n(0.0075, 0.05, 0.005, rk.Z80) > rk.required_n(0.0075, 0.05, 0.005)


@settings(max_examples=300, deadline=None)
@given(
    st.floats(min_value=-0.03, max_value=0.03),
    st.floats(min_value=0.01, max_value=0.15),
    st.floats(min_value=0.0, max_value=0.02),
)
def test_generalized_p_star_identity(mu, s, c):
    """p(W̄ + L̄) − L̄ − C = μ − C  ⇒  p > p* ⇔ μ > C (karta §6)."""
    p, ps = rk.generalized_p_star(mu, s, c)
    if abs(mu - c) > 1e-6:
        assert (p > ps) == (mu > c)


def test_large_n_generalized_does_not_punish_goal_but_simple_does():
    big = 1_000_000
    p, ps = rk.generalized_p_star(0.0060, 0.05, 0.005)  # μ = 1,2 × C
    assert measurability_report(p, ps, big)["verdict"] == "MIERZALNA"
    assert measurability_report(p, rk.simple_p_star(0.05, 0.005), big)["verdict"] == "NIEMIERZALNA"
    p, ps = rk.generalized_p_star(0.0045, 0.05, 0.005)
    assert measurability_report(p, ps, big)["verdict"] == "NIEMIERZALNA"


def test_max_ratio():
    thr = {("2026-10", "X"): Decimal(100)}
    evs = [
        e1.Liq("X", D0, "long", Decimal(30)),
        e1.Liq("X", D0 + 10 * MIN, "long", Decimal(30)),
        e1.Liq("X", D0 + 70 * MIN, "short", Decimal(10)),
        e1.Liq("Y", D0, "long", Decimal(10**9)),  # spoza uniwersum
    ]
    out = rk.max_ratio(evs, thr)
    assert out[0][:3] == (pytest.approx(0.6), "X", "long")
    assert {(s, side) for _, s, side, _ in out} == {("X", "long"), ("X", "short")}


def _bybit(t, sym, side, v, p):
    return json.dumps({"T": t, "s": sym, "S": side, "v": v, "p": p, "pos": "x", "ts": t, "rcv": t})


def _binance(t, sym, side, q, ap):
    return json.dumps(
        {
            "E": t,
            "st": 1,
            "ps": sym,
            "s": sym,
            "S": side,
            "o": "LIMIT",
            "f": "IOC",
            "q": q,
            "p": ap,
            "ap": ap,
            "X": "FILLED",
            "l": q,
            "z": q,
            "T": t,
        }
    )


def test_end_to_end_synthetic(tmp_path, capsys):
    by, bn = tmp_path / "by", tmp_path / "bn"
    by.mkdir()
    bn.mkdir()
    kosz = tmp_path / "koszyk.csv"
    kosz.write_text(
        "miesiac,symbol,pozycja,sredni_obrot_30d,czlonek_top20,funding_pobrany\n"
        "2026-10,BTCUSDT,1,1000000,True,True\n",
        encoding="utf-8",
    )
    # próg 5 000 USDT; Bybit: kaskada longów 6 000 (Buy = long), Binance: 3 000 (poniżej)
    (by / "2026-10-01.jsonl").write_text(
        "\n".join(
            [
                _bybit(D0 + MIN, "BTCUSDT", "Buy", "30", "100"),
                _bybit(D0 + 2 * MIN, "BTCUSDT", "Buy", "30", "100"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (by / "2026-10-02.jsonl").write_text(
        _bybit(D0 + 86_400_000 + MIN, "BTCUSDT", "Buy", "1", "100") + "\n", encoding="utf-8"
    )
    (bn / "2026-10-01.jsonl").write_text(
        _binance(D0 + MIN, "BTCUSDT", "SELL", "30", "100") + "\n", encoding="utf-8"
    )
    assert (
        rk.main(
            ["--bybit", str(by), "--binance", str(bn), "--koszyk", str(kosz), "--do", "2026-10-03"]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "KASKADY: 1 " in out and "KASKADY: 0 " in out
    assert "RACHUNEK MIERZALNOŚCI" in out and "GRANICA DUŻEGO n" in out
    assert "1.577 × C" in out


def test_load_missing_data_fails_loud(tmp_path):
    with pytest.raises(SystemExit, match="BRAK DANYCH"):
        rk.load("bybit", tmp_path, "2026-10-05")
