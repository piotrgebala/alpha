"""
test_rebalance_premium.py

Runda R1: definicja premii rebalansowej z pre-rejestracji (backtest/rebalance_premium.py) na
ręcznie zbudowanych panelach: dwa aktywa z ruchami odwracającymi się → rebalans wygrywa o x²,
trend jednego aktywa → buy-and-hold wygrywa, identyczne zwroty → premia i obrót 0, wycofanie
w trakcie miesiąca = gotówka w obu wersjach, dobór składu bez lookaheadu; własności w hypothesis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import backtest.rebalance_premium as rp

FEE = 0.001


def _close(rets: dict[str, list[float]], start: str = "2021-02-01") -> pd.DataFrame:
    n = len(next(iter(rets.values())))
    idx = pd.date_range(start, periods=n + 1, freq="D", tz="UTC") - pd.Timedelta(days=1)
    data = {sym: 100.0 * np.cumprod([1.0, *(1.0 + np.asarray(r))]) for sym, r in rets.items()}
    return pd.DataFrame(data, index=idx)


def _members(close: pd.DataFrame) -> dict[pd.Timestamp, list[str]]:
    return {close.index[1]: sorted(close.columns)}


def test_two_assets_reverting_moves_give_premium_exactly_x_squared() -> None:
    x = 0.10
    close = _close({"AUSDT": [x, -x], "BUSDT": [-x, x]})
    out = rp.daily_premium(close, _members(close), fee=0.0)
    assert out["r_rebal"].tolist() == pytest.approx([0.0, 0.0])
    assert out["r_bh"].tolist() == pytest.approx([0.0, -(x**2)])  # b&h: 0,55·0,9 + 0,45·1,1 = 0,99
    assert out["premium_gross"].sum() == pytest.approx(x**2)
    assert out["turnover"].iloc[0] == pytest.approx(x)  # |0,55−0,5| + |0,45−0,5| = 0,10


def test_trending_asset_makes_buy_and_hold_win() -> None:
    close = _close({"AUSDT": [0.1, 0.1], "BUSDT": [0.0, 0.0]})
    out = rp.daily_premium(close, _members(close), fee=0.0)
    assert rp.cumulative_growth(out["r_rebal"]) == pytest.approx(1.05**2 - 1)
    assert rp.cumulative_growth(out["r_bh"]) == pytest.approx(0.5 * 1.21 + 0.5 - 1)
    assert out["premium_gross"].sum() < 0


def test_identical_returns_give_zero_premium_and_zero_turnover() -> None:
    close = _close({"AUSDT": [0.05, -0.02, 0.03], "BUSDT": [0.05, -0.02, 0.03]})
    out = rp.daily_premium(close, _members(close), fee=FEE)
    assert (out["premium_gross"].abs() < 1e-15).all()
    assert (out["turnover"].abs() < 1e-15).all() and (out["cost"] == 0).all()


def test_delisted_member_is_cash_in_both_strategies() -> None:
    close = _close({"AUSDT": [0.1, 0.1, 0.1], "BUSDT": [0.0, 0.0, 0.0]})
    close.loc[close.index[2:], "BUSDT"] = np.nan  # B wycofane od 2. dnia miesiąca
    out = rp.daily_premium(close, _members(close), fee=0.0)
    # dzień 1: oba aktywa; dni 2–3: B = gotówka (0) → r_rebal = 0,05, r_bh z dryfującą wagą A
    assert out["r_rebal"].tolist() == pytest.approx([0.05, 0.05, 0.05])
    assert not out[["r_rebal", "r_bh", "premium_net"]].isna().any().any()


def test_membership_uses_only_data_before_the_month_start() -> None:
    idx = pd.date_range("2021-01-01", periods=70, freq="D", tz="UTC")
    rng = np.random.default_rng(0)
    vol = pd.DataFrame(
        rng.uniform(1e6, 2e6, (70, 4)), index=idx, columns=["AUSDT", "BUSDT", "CUSDT", "DUSDT"]
    )
    vol["CUSDT"] *= 10  # C ma najwyższy obrót przed miesiącem
    m = pd.Timestamp("2021-02-01", tz="UTC")
    before = rp.monthly_members(vol, [m], top_n=2)[m]
    vol2 = vol.copy()
    vol2.loc[vol2.index >= m, "AUSDT"] = 1e12  # przyszłość nie może wpłynąć na skład
    after = rp.monthly_members(vol2, [m], top_n=2)[m]
    assert before == after and "CUSDT" in before


def test_membership_excludes_stables_and_fails_loud_when_too_few() -> None:
    idx = pd.date_range("2021-01-01", periods=40, freq="D", tz="UTC")
    vol = pd.DataFrame(1e6, index=idx, columns=["AUSDT", "USDCUSDT", "BBTC"])
    m = pd.Timestamp("2021-02-01", tz="UTC")
    assert rp.monthly_members(vol, [m], top_n=1)[m] == ["AUSDT"]
    with pytest.raises(ValueError):
        rp.monthly_members(vol, [m], top_n=2)


@given(seed=st.integers(0, 3_000), n_assets=st.integers(1, 6), days=st.integers(2, 25))
@settings(max_examples=40, deadline=None)
def test_gross_identity_turnover_nonnegative_and_single_asset_zero(
    seed: int, n_assets: int, days: int
) -> None:
    rng = np.random.default_rng(seed)
    rets = {f"S{i}USDT": list(rng.normal(0.0, 0.05, days)) for i in range(n_assets)}
    close = _close(rets)
    out = rp.daily_premium(close, _members(close), fee=FEE)
    assert np.allclose(out["premium_gross"], out["r_rebal"] - out["r_bh"])
    assert np.allclose(out["premium_net"], out["premium_gross"] - FEE * out["turnover"])
    assert (out["turnover"] >= -1e-15).all()
    if n_assets == 1:
        assert np.allclose(out["premium_gross"], 0.0) and np.allclose(out["turnover"], 0.0)


# ------------------------------------------------------------------ poprawka 11: ranking 1–50


@given(
    seed=st.integers(0, 10_000),
    n_sym=st.integers(20, 60),
    depth=st.integers(20, 50),
    ties=st.booleans(),
    holes=st.floats(0.0, 0.3),
)
@settings(max_examples=60, deadline=None)
def test_ranking_top_n_is_monthly_members_exactly(seed, n_sym, depth, ties, holes) -> None:
    """Pierwsze TOP_N miejsc rankingu (posortowane) = `monthly_members` — remisy, dziury, stablecoiny."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-12-01", periods=95, freq="D", tz="UTC")
    cols = [f"S{i:02d}USDT" for i in range(n_sym)] + ["USDCUSDT", "XBTC"]
    shape = (len(idx), len(cols))
    vals = rng.integers(1, 6, shape) * 1e6 if ties else rng.lognormal(15, 2, shape)
    vol = pd.DataFrame(vals, index=idx, columns=cols)
    vol = vol.mask(rng.random(vol.shape) < holes)  # brak notowań → próg 30 dni historii
    months = [pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-02-01", tz="UTC")]
    ranking = rp.monthly_ranking(vol, months, depth)
    try:
        members = rp.monthly_members(vol, months)
    except ValueError:  # < TOP_N kandydatów: silnik głośno odmawia, ranking jest krótszy
        assert any(len(ranking[m]) < rp.TOP_N for m in months)
        return
    for m in months:
        r = ranking[m]
        assert sorted(s for s, _ in r[: rp.TOP_N]) == members[m]
        assert len(r) <= depth and len({s for s, _ in r}) == len(r)
        v = [x for _, x in r]
        assert v == sorted(v, reverse=True)
        assert {s for s, _ in r} <= set(rp.eligible_symbols(cols))


def test_ranking_uses_only_data_before_month_and_same_tie_break() -> None:
    idx = pd.date_range("2021-01-01", periods=70, freq="D", tz="UTC")
    vol = pd.DataFrame(1e6, index=idx, columns=["BUSDT", "AUSDT", "CUSDT"])
    m = pd.Timestamp("2021-02-01", tz="UTC")
    before = rp.monthly_ranking(vol, [m], depth=3)[m]
    assert [s for s, _ in before] == ["AUSDT", "BUSDT", "CUSDT"]  # remis → alfabetycznie
    vol.loc[vol.index >= m, "CUSDT"] = 1e12  # przyszłość nie zmienia rankingu
    assert rp.monthly_ranking(vol, [m], depth=3)[m] == before
    assert rp.monthly_ranking(vol, [m], depth=2)[m] == before[:2]


def _real_volume(kind: str) -> tuple[pd.DataFrame, list[pd.Timestamp]]:
    """Prawdziwy panel obrotu (TYLKO odczyt): `data/raw/live` dziennika albo archiwum RU1."""
    import os
    from pathlib import Path

    default = Path(__file__).resolve().parents[1] / "data" / "raw"
    root = Path(os.environ.get("CLAS5_DANE_RAW", default))
    if kind == "live":
        cands = [root / "live", Path.home() / "alpha-dziennik" / "data" / "raw" / "live"]
    else:
        cands = [root / "universe_full"]
    src = next((p for p in cands if len(list(p.glob("*_1d.parquet"))) >= 100), None)
    if src is None:
        pytest.skip(f"brak prawdziwego panelu {kind} (ustaw CLAS5_DANE_RAW)")
    if kind == "universe_full":
        _, vol = rp.load_universe(src)
        return vol, list(pd.date_range("2021-02-01", "2026-06-01", freq="MS", tz="UTC"))
    from data.fetch_live import symbol_files  # jak dziennik: bez pliku Coinbase

    frames = {}
    for sym, p in symbol_files(src).items():
        d = pd.read_parquet(p, columns=["open_time", "quote_volume"])
        if len(d):
            frames[sym] = d.set_index(pd.to_datetime(d["open_time"], utc=True))["quote_volume"]
    vol = pd.concat(frames, axis=1, sort=True)
    start = pd.Timestamp("2025-09-01", tz="UTC")  # ENGINE_START dziennika
    return vol, list(pd.date_range(start, vol.index.max(), freq="MS"))


@pytest.mark.parametrize("kind", ["live", "universe_full"])
def test_ranking_top20_equals_members_on_real_panel(kind) -> None:
    """Skład top-20 z rankingu 1–50 = `monthly_members` co do bajtu na prawdziwym panelu."""
    vol, months = _real_volume(kind)
    members = rp.monthly_members(vol, months)
    ranking = rp.monthly_ranking(vol, months, depth=50)
    for m in months:
        top = sorted(s for s, _ in ranking[m][: rp.TOP_N])
        assert repr(top).encode("utf-8") == repr(members[m]).encode("utf-8"), m
        assert len(ranking[m]) == 50
