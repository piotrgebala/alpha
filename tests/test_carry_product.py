"""Testy backtest/carry_product.py (runda D1) — czyste funkcje, bez danych z dysku."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import carry_product as cp


def _ts(n: int, start: str = "2021-01-01") -> pd.Series:
    return pd.Series(pd.date_range(start, periods=n, freq="8h", tz="UTC"))


# ---------------------------------------------------------------- Q1: run-up i depozyt


def test_forward_runup_constant_price_is_zero_and_jump_is_captured():
    flat = pd.Series([100.0] * 10)
    assert (cp.forward_runup(flat, 3).dropna() == 0).all()
    jump = pd.Series([100.0, 100.0, 150.0, 120.0, 120.0])
    r = cp.forward_runup(jump, 2)
    assert r.iloc[0] == pytest.approx(0.5)  # z t=0 widzi 150 w oknie 2
    assert r.iloc[1] == pytest.approx(0.5)
    assert r.iloc[2] == pytest.approx(0.0)  # po szczycie tylko spadki


def test_max_runup_table_shape_and_monotone_in_horizon():
    rng = np.random.default_rng(0)
    price = pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, 2000))))
    t = cp.max_runup_table(price, horizons_days=(1, 7, 30))
    assert list(t["horizon_days"]) == [1, 7, 30]
    assert t["max"].is_monotonic_increasing  # dłuższe okno ⊇ krótsze
    assert ((t["share_gt_50pct"] >= 0) & (t["share_gt_50pct"] <= 1)).all()


def test_liquidation_exactly_once_when_price_crosses_threshold_without_resets():
    m, mm = 0.5, cp.MAINTENANCE_MARGIN
    thr = m - mm
    price = pd.Series([100.0, 110.0, 100.0 * (1 + thr) + 0.01, 100.0 * (1 + thr) + 0.02])
    ev = cp.liquidation_events(price, m, None)
    assert ev["n_liquidations"] == 1  # po likwidacji P_ref = nowa cena, drobny ruch nie liczy
    assert ev["liquidation_cost"] == pytest.approx(cp.LIQUIDATION_FEE + cp.PERP_REENTRY_COST)
    assert ev["max_usage"] == pytest.approx(thr + 0.0001, abs=1e-3)


def test_liquidation_avoided_by_frequent_resets_and_absent_on_declines():
    price = pd.Series(100.0 * 1.2 ** np.arange(8))  # +20 % co okres → +330 % łącznie
    assert cp.liquidation_events(price, 1.0, None)["n_liquidations"] >= 1
    ev = cp.liquidation_events(price, 1.0, 1)  # uzupełnienie co okres: nigdy > 20 % od P_ref
    assert ev["n_liquidations"] == 0 and ev["n_resets"] == 7
    down = pd.Series(100.0 * 0.9 ** np.arange(8))
    assert cp.liquidation_events(down, 0.25, None) == {
        "n_liquidations": 0,
        "liquidation_cost": 0.0,
        "max_usage": 0.0,
        "n_resets": 0,
    }
    with pytest.raises(ValueError):
        cp.liquidation_events(price, cp.MAINTENANCE_MARGIN, None)


def test_margin_grid_shape_and_capital_scaling():
    price = pd.Series([100.0] * 30)
    g = cp.margin_grid(price, 0.10, margins=(0.5, 1.0), reset_days=(None, 1), years=1.0)
    assert len(g) == 4 and g["n_liquidations"].eq(0).all()
    row = g[(g["margin"] == 1.0) & (g["reset_days"].isna())].iloc[0]
    assert row["annual_on_capital"] == pytest.approx(0.10 / 2.0)


# ---------------------------------------------------------------- Q2: COIN-M


@settings(max_examples=50, deadline=None)
@given(st.lists(st.floats(0.05, 20.0), min_size=1, max_size=50), st.floats(0.5, 2.0))
def test_inverse_position_usd_value_is_constant_for_any_price_path(factors, p0):
    price = pd.Series(p0 * np.array(factors))
    v = cp.inverse_position_usd_value(price, p0)
    assert np.allclose(v.to_numpy(), p0, rtol=1e-9)


def test_inverse_carry_pnl_sums_funding_minus_two_switch_costs():
    f = pd.DataFrame({"timestamp": _ts(4), "funding_rate": [0.0001, -0.0002, 0.0003, 0.0001]})
    out = cp.inverse_carry_pnl(f, switch_cost=0.0019)
    assert out["pnl"].sum() == pytest.approx(0.0003 - 2 * 0.0019)
    assert out.loc[0, "cost"] == pytest.approx(0.0019) and out.loc[3, "cost"] == pytest.approx(
        0.0019
    )
    assert (out.loc[1:2, "cost"] == 0).all()
    with pytest.raises(ValueError):
        cp.inverse_carry_pnl(pd.DataFrame({"x": [1]}), 0.0)


def test_floor_to_grid_removes_ms_jitter():
    ts = pd.Series(
        pd.to_datetime(
            ["2020-08-20 08:00:00.003", "2020-08-20 16:00:00"], utc=True, format="ISO8601"
        )
    )
    out = cp.floor_to_grid(ts)
    assert list(out) == list(pd.to_datetime(["2020-08-20 08:00", "2020-08-20 16:00"], utc=True))


# ---------------------------------------------------------------- Q3: basis


def _dated_frame(r_annual: float, spot_price: float = 100.0, n: int = 60) -> tuple:
    """Kontrakt wygasający po 30 dniach; F = S·(1 + r·d/365) → annualized == r dokładnie."""
    expiry = pd.Timestamp("2021-02-01", tz="UTC")
    open_time = _ts(n, "2021-01-01")
    delivery = expiry + cp.DELIVERY_OFFSET
    days = (delivery - open_time).dt.total_seconds() / 86_400.0
    f = spot_price * (1 + r_annual * days / 365.0)
    dated = pd.DataFrame(
        {
            "contract": "BTCUSDT_210201",
            "expiry": expiry,
            "open_time": open_time,
            "close": f,
            "volume": 1.0,
        }
    )
    spot = pd.DataFrame({"timestamp": open_time, "close": spot_price})
    return dated, spot


def test_annualized_basis_recovers_rate_and_filters():
    dated, spot = _dated_frame(0.12)
    b = cp.annualized_basis(dated, spot, min_days=7)
    assert np.allclose(b["annualized"], 0.12)
    assert (b["days_to_expiry"] >= 7).all()
    assert (b["open_time"] < pd.Timestamp("2021-02-01", tz="UTC") + cp.DELIVERY_OFFSET).all()
    # świece po wygaśnięciu i bez wolumenu odpadają
    dated2 = dated.copy()
    dated2.loc[dated2.index[:3], "volume"] = 0.0
    assert len(cp.annualized_basis(dated2, spot, 7)) == len(b) - 3
    with pytest.raises(ValueError):
        cp.annualized_basis(dated.drop(columns=["volume"]), spot)


def test_front_contract_picks_shortest_maturity():
    b = pd.DataFrame(
        {
            "contract": ["A", "B", "A", "B"],
            "open_time": pd.to_datetime(
                ["2021-01-01", "2021-01-01", "2021-01-02", "2021-01-02"], utc=True
            ),
            "days_to_expiry": [30.0, 90.0, 29.0, 89.0],
            "annualized": [0.1, 0.2, 0.1, 0.2],
        }
    )
    fr = cp.front_contract(b)
    assert list(fr["contract"]) == ["A", "A"] and len(fr) == 2


def test_realized_funding_window_is_half_open_and_basis_vs_funding_aligns():
    dated, spot = _dated_frame(0.12)
    ts = _ts(200, "2020-12-15")  # do 2021-02-19: pokrywa wygaśnięcie 2021-02-01
    funding = pd.DataFrame({"timestamp": ts, "funding_rate": 0.0001})
    start, end = ts.iloc[10], ts.iloc[20]
    assert cp.realized_funding_window(funding, start, end) == pytest.approx(10 * 0.0001)
    b = cp.annualized_basis(dated, spot, min_days=7)
    cmp = cp.basis_vs_funding(b, funding, entry_days=(30, 20), tol_days=0.5)
    assert set(cmp["entry_days"]) == {30, 20}
    row = cmp[cmp["entry_days"] == 20].iloc[0]
    assert row["basis_annualized"] == pytest.approx(0.12)
    assert row["funding_realized"] == pytest.approx(60 * 0.0001)  # 20 dni × 3 rozliczenia
    assert row["diff_annualized"] == pytest.approx(0.12 - 60 * 0.0001 * 365 / 20)


# ---------------------------------------------------------------- Q4: tabele roczne


def test_yearly_sum_mean_fraction():
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2021-12-31 16:00", "2022-01-01", "2022-06-01"], utc=True, format="ISO8601"
            ),
            "pnl": [1.0, 2.0, 3.0],
        }
    )
    assert cp.yearly_sum(df, "pnl").to_dict() == {2021: 1.0, 2022: 5.0}
    fred = pd.DataFrame(
        {
            "date": pd.to_datetime(["2021-01-04", "2021-01-05", "2022-01-03"], utc=True),
            "value": [0.1, np.nan, 4.0],
        }
    )
    assert cp.yearly_mean(fred, "value", "date").to_dict() == {2021: 0.1, 2022: 4.0}
    frac = cp.yearly_fraction(df)
    assert frac[2022] == pytest.approx(2 / (3 * 365))
