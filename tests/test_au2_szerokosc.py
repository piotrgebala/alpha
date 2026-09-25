"""Testy backtest/run_au2_szerokosc.py (AU2 krok 0): szerokość efektywna i szum rank IC."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import run_au2_szerokosc as au


def test_participation_ratio_extremes():
    assert au.participation_ratio(np.eye(10)) == pytest.approx(10.0)
    assert au.participation_ratio(np.ones((10, 10))) == pytest.approx(1.0)


def test_effective_breadth_factor_model_and_market_removal():
    """Jeden silny czynnik rynkowy: surowo ~1–2 niezależne, po odjęciu średniej przekroju ~N−1."""
    rng = np.random.default_rng(0)
    days = pd.date_range("2021-01-01", periods=200, freq="D", tz="UTC")
    n = 20
    market = rng.standard_normal((200, 1)) * 3.0
    ret = pd.DataFrame(
        market + rng.standard_normal((200, n)), index=days, columns=[f"S{i}" for i in range(n)]
    )
    m = pd.Timestamp("2021-06-01", tz="UTC")
    br = au.effective_breadth(ret, {m: list(ret.columns)})
    row = br.iloc[0]
    assert row["n"] == n
    assert row["mean_corr"] > 0.8
    assert row["pr_raw"] < 2.0
    assert row["pr_resid"] > 0.8 * (n - 1)


def test_effective_breadth_drops_members_with_short_history():
    days = pd.date_range("2021-01-01", periods=120, freq="D", tz="UTC")
    rng = np.random.default_rng(1)
    ret = pd.DataFrame(rng.standard_normal((120, 4)), index=days, columns=list("ABCD"))
    ret.loc[days[:60], "D"] = np.nan  # D ma tylko ~1/3 okna 90 dni przed miesiącem
    br = au.effective_breadth(ret, {pd.Timestamp("2021-04-30", tz="UTC"): list("ABCD")})
    assert br.iloc[0]["n"] == 3


def test_daily_rank_ic_perfect_inverse_and_mask():
    rng = np.random.default_rng(2)
    f = rng.standard_normal((5, 8))
    valid = np.ones_like(f, dtype=bool)
    assert au.daily_rank_ic(f, f, valid) == pytest.approx(np.ones(5))
    assert au.daily_rank_ic(-f, f, valid) == pytest.approx(-np.ones(5))
    valid[0, 3:] = False  # 3 pary → za mało
    valid[1, 5:] = False  # 5 par → liczone tylko na nich
    s = f.copy()
    s[1, 5:] = -100.0  # śmieci poza maską nie mogą wpływać
    ic = au.daily_rank_ic(s, f, valid)
    assert np.isnan(ic[0])
    assert ic[1] == pytest.approx(1.0)


def test_ar1_signal_autocorrelation_matches_half_life():
    x = au.ar1_signal((20_000, 3), half_life=7, rng=np.random.default_rng(3))
    phi = 0.5 ** (1 / 7)
    ac = np.mean([np.corrcoef(x[:-1, j], x[1:, j])[0, 1] for j in range(3)])
    assert ac == pytest.approx(phi, abs=0.02)
    assert x.std() == pytest.approx(1.0, abs=0.05)


def test_member_mask_uses_month_membership():
    days = pd.date_range("2021-01-30", periods=5, freq="D", tz="UTC")
    members = {
        pd.Timestamp("2021-01-01", tz="UTC"): ["A"],
        pd.Timestamp("2021-02-01", tz="UTC"): ["B"],
    }
    mask = au.member_mask(days, pd.Index(["A", "B"]), members)
    assert mask["A"].tolist() == [True, True, False, False, False]
    assert mask["B"].tolist() == [False, False, True, True, True]


def test_positive_control_injected_ic_is_recovered_and_null_is_centred():
    """Kontrola pozytywna: sygnał = zwrot + szum o znanym IC → średnie IC ≈ wstrzyknięte; losowy ≈ 0."""
    rng = np.random.default_rng(4)
    f = rng.standard_normal((400, 50))
    valid = np.ones_like(f, dtype=bool)
    target = 0.10
    noise = rng.standard_normal(f.shape)
    s = target * f + np.sqrt(1 - target**2) * noise
    ic = np.nanmean(au.daily_rank_ic(s, f, valid))
    assert ic == pytest.approx(target, abs=0.02)
    fwd = pd.DataFrame(f)
    r = au.ic_noise(fwd, pd.DataFrame(valid), half_life=7, n_sim=30, seed=0)
    assert abs(r["mean_of_means"]) < 3 * r["se_mean_ic"] / np.sqrt(30) + 1e-3
    assert r["se_mean_ic"] > 0
