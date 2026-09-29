"""Testy `backtest/funding_settlement.py` (zadanie 016, runda FD1): dwie drogi liczenia fundingu."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import funding_settlement as fs
from backtest.ts_momentum import phase_returns_liq
from backtest.xs_momentum import long_short_returns, rank_legs, signal_panel

IDX = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")


def _st(rows: list[tuple[int, int, float, float]]) -> fs.Settlements:
    """rows = (sym, day, frac, rate)."""
    a = np.array(rows, dtype=float).reshape(-1, 4)
    return fs.Settlements(
        a[:, 0].astype(int), a[:, 1].astype(int), a[:, 2], a[:, 3], np.zeros(len(a), dtype="int64")
    )


def test_one_coin_three_settlements_hand_computed():
    """1 moneta, long 1× kapitału po cenie 100, rozliczenia 00:00/08:00/16:00 przy cenach 100/110/120."""
    returns = np.array([[np.nan], [0.25]])  # 100 → 125
    nan = np.full((2, 1), np.nan)
    pos = fs.ts_liq_positions(returns, [(0, np.array([1.0]))], nan, nan, lev=2.0, mmr=0.01)
    st_ = _st([(0, 1, 0.0, 0.001), (0, 1, 1 / 3, 0.002), (0, 1, 2 / 3, 0.003)])
    ratio = np.array([1.0, 1.1, 1.2])  # znana ścieżka ceny
    fday = fs.daily_sum(st_, 2, 1)
    a = fs.engine_funding(pos.W_eng, fday).sum()
    b = fs.settlement_funding(pos.W, pos.R, pos.alive_end, pos.first, st_, ratio)
    # ręcznie: ilość 0,01 szt.; (a) = −1·(0,001+0,002+0,003); (b) = −0,01·(100·0,001+110·0,002+120·0,003)
    assert a == pytest.approx(-0.006, abs=1e-15)
    assert b["b0"].sum() == pytest.approx(-0.0068, abs=1e-15)
    # (wejście, wyjście]: północ wejścia należy do poprzedniej (nieistniejącej) pozycji
    assert b["b1"].sum() == pytest.approx(-0.0058, abs=1e-15)
    assert b["b2"].sum() == pytest.approx(-0.0068, abs=1e-15)


def test_boundary_midnight_once_old_new_twice():
    """Formowanie long 1 → short 0,5; rozliczenie 0,01 dokładnie w chwili zmiany (00:00 dnia 2)."""
    returns = np.array([[np.nan], [0.1], [0.0]])
    nan = np.full((3, 1), np.nan)
    forms = [(0, np.array([1.0])), (1, np.array([-0.5]))]
    pos = fs.ts_liq_positions(returns, forms, nan, nan, lev=2.0, mmr=0.01)
    st_ = _st([(0, 2, 0.0, 0.01)])
    b = fs.settlement_funding(pos.W, pos.R, pos.alive_end, pos.first, st_, np.ones(1))
    a = fs.engine_funding(pos.W_eng, fs.daily_sum(st_, 3, 1))
    assert a.sum() == pytest.approx(0.005)  # silnik: nowa pozycja (short 0,5 otrzymuje)
    assert b["b0"].sum() == pytest.approx(0.005)
    assert b["b1"][1, 0] == pytest.approx(-0.011)  # stara: long 1 × (1+0,1) płaci, dzień 1
    assert b["b2"].sum() == pytest.approx(-0.006)  # dwa razy
    assert b["new_edge"].sum() == pytest.approx(0.005)
    assert b["old_edge"].sum() == pytest.approx(-0.011)


def test_build_settlements_rounds_jitter_and_daily_sum_nan():
    raw = {
        "AAA": pd.DataFrame(
            {
                # jednostka ms jak w parquet z repo — znacznik ma wyjść w nanosekundach
                "timestamp": pd.to_datetime(
                    ["2024-01-02 00:00:00.004", "2024-01-02 16:00:00.005"], utc=True
                ).as_unit("ms"),
                "funding_rate": [0.001, np.nan],
            }
        )
    }
    st_ = fs.build_settlements(raw, ["AAA", "BBB"], IDX)
    assert st_.ts[0] == pd.Timestamp("2024-01-02").value  # ns od 1970, zaokrąglone do minuty
    assert list(st_.day) == [1, 1]
    assert st_.midnight.tolist() == [True, False]
    assert st_.frac[1] == pytest.approx(2 / 3)
    fd = fs.daily_sum(st_, 3, 2)
    assert fd[1, 0] == pytest.approx(0.001)
    assert np.isnan(fd[0, 0]) and np.isnan(fd[1, 1])


def test_interp_ratio():
    st_ = _st([(0, 1, 0.5, 0.0), (0, 1, 0.0, 0.0)])
    R = np.array([[0.0], [0.21]])
    assert fs.interp_ratio(st_, R).tolist() == pytest.approx([1.1, 1.0])


def test_bootstrap_constant_series():
    m, lo, hi = fs.weekly_block_bootstrap(np.full(70, 0.001), n_boot=200)
    assert m == pytest.approx(0.365) and lo == pytest.approx(0.365) and hi == pytest.approx(0.365)


def _panel(seed: int, n_days: int = 60, n_sym: int = 12):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n_days, freq="D", tz="UTC")
    cols = [f"S{i:02d}" for i in range(n_sym)]
    close = pd.DataFrame(
        100 * np.exp(np.cumsum(rng.normal(0, 0.04, (n_days, n_sym)), axis=0)),
        index=idx,
        columns=cols,
    )
    close.iloc[40:, 3] = np.nan  # wycofany członek
    fund = pd.DataFrame(rng.normal(0, 3e-4, (n_days, n_sym)), index=idx, columns=cols)
    fund.iloc[5:9, 2] = np.nan
    return close, fund


def test_ts_liq_positions_reproduce_engine_funding_and_gross():
    close, fund = _panel(1)
    rets = close.pct_change(fill_method=None).to_numpy()
    f = fund.fillna(0.0).to_numpy()
    rng = np.random.default_rng(2)
    forms = [(t, rng.normal(0, 0.3, close.shape[1])) for t in range(30, 60, 7)]
    prev = close.shift(1)
    lo = (close * 0.8 / prev).to_numpy()
    hi = (close * 1.3 / prev).to_numpy()
    eng = phase_returns_liq(rets, f, close.index, forms, 0.0, lo, hi, 2.0, 0.01)
    pos = fs.ts_liq_positions(rets, forms, lo, hi, 2.0, 0.01)
    mine = fs.engine_funding(pos.W_eng, fund.to_numpy()).sum(axis=1)[pos.in_phase]
    assert np.allclose(mine, eng["funding"].to_numpy(), atol=1e-14)
    assert np.allclose(pos.gross[pos.in_phase], eng["gross"].to_numpy(), atol=1e-14)
    assert eng["liquidations"].sum() > 0  # kontrola: ścieżka likwidacji przećwiczona


def test_xs_positions_reproduce_engine_funding_and_gross():
    close, fund = _panel(3)
    members = {close.index[0]: list(close.columns)}
    dates = list(close.index[30::7])
    eng = long_short_returns(close, fund, members, dates, 0.0, leg_size=3)
    pos = fs.xs_positions(close, members, dates, rank_legs, 0.5, 3, signal_panel(close))
    mine = fs.engine_funding(pos.W_eng, fund.to_numpy()).sum(axis=1)[pos.in_phase]
    assert np.allclose(mine, eng["funding_net"].to_numpy(), atol=1e-14)
    assert np.allclose(pos.gross[pos.in_phase], eng["r_ls_gross"].to_numpy(), atol=1e-14)
    # stała ilość: pierwszy dzień okresu = wagi silnika
    d0 = np.where(pos.first & pos.in_phase)[0]
    assert np.allclose(pos.W[d0], pos.W_eng[d0])


@settings(max_examples=50, deadline=None)
@given(
    rates=st.lists(st.floats(-0.003, 0.003), min_size=1, max_size=6),
    w=st.floats(-2.0, 2.0),
    r=st.floats(-0.3, 0.3),
)
def test_property_midnight_only_b0_equals_engine(rates, w, r):
    """Tylko rozliczenia o północy i ta sama waga → (b) w konwencji silnika = (a) dokładnie."""
    n = len(rates) + 1
    returns = np.full((n, 1), r)
    returns[0] = np.nan
    nan = np.full((n, 1), np.nan)
    pos = fs.ts_liq_positions(
        returns, [(0, np.array([w]))], nan, nan, lev=1.0, mmr=-10.0
    )  # próg 11 = bez likwidacji
    st_ = _st([(0, d + 1, 0.0, f) for d, f in enumerate(rates)])
    b = fs.settlement_funding(pos.W, pos.R, pos.alive_end, pos.first, st_, np.ones(len(rates)))
    a = fs.engine_funding(pos.W_eng, fs.daily_sum(st_, n, 1))
    assert b["b0"].sum() == pytest.approx(a.sum(), abs=1e-12)


# ----------------------------------------------------------------------------- druga droga (dolarowo)


def _settle_dict(st_: fs.Settlements, cols: list[str]) -> dict:
    out = {}
    for j, c in enumerate(cols):
        m = st_.sym == j
        order = np.argsort(st_.ts[m])
        out[c] = (st_.ts[m][order].astype("datetime64[ns]"), st_.rate[m][order])
    return out


def test_dollar_way_hand_computed_with_exit_midnight():
    """Jak test ręczny wyżej + rozliczenie 0,004 o północy wyjścia (cena 125): (b) = −0,0108 obiema drogami."""
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    raw = {
        "AAA": pd.DataFrame(
            {
                "timestamp": idx[1] + pd.to_timedelta([0, 8, 16, 24], unit="h"),
                "funding_rate": [0.001, 0.002, 0.003, 0.004],
            }
        )
    }
    st_ = fs.build_settlements(raw, ["AAA"], idx)
    returns = np.array([[np.nan], [0.25], [0.0]])
    nan = np.full((3, 1), np.nan)
    forms = [(0, np.array([1.0])), (2, np.array([0.0]))]
    pos = fs.ts_liq_positions(returns, forms, nan, nan, 2.0, 0.01)
    ratio = np.array([1.0, 1.1, 1.2, 1.0])
    b = fs.settlement_funding(pos.W, pos.R, pos.alive_end, pos.first, st_, ratio)
    assert b["b1"].sum() == pytest.approx(
        -0.0108, abs=1e-15
    )  # −(1,1·0,002 + 1,2·0,003 + 1,25·0,004)

    rets = pd.DataFrame(returns, index=idx, columns=["AAA"])
    known = {
        pd.Timestamp("2024-01-02 08:00", tz="UTC"): 1.1,
        pd.Timestamp("2024-01-02 16:00", tz="UTC"): 1.2,
    }
    dollars = fs.dollar_way_b1(
        [(idx[1], idx[1], pd.Series({"AAA": 1.0}))],
        rets,
        _settle_dict(st_, ["AAA"]),
        lambda sym, s: np.array([known[t] for t in s]),
    )
    assert dollars.sum() == pytest.approx(-0.0108, abs=1e-15)
    assert dollars.iloc[1] == pytest.approx(-0.0108, abs=1e-15)  # cała opłata w dniu trzymania


def _interp_fn(rets: pd.DataFrame):
    def fn(sym, s):
        day = s.floor("D")
        frac = np.asarray((s - day) / pd.Timedelta(days=1))
        r = rets[sym].reindex(day).fillna(0.0).to_numpy()
        return (1.0 + r) ** frac

    return fn


def _synthetic_settlements(close: pd.DataFrame, seed: int) -> fs.Settlements:
    rng = np.random.default_rng(seed)
    raw = {}
    for j, c in enumerate(close.columns):
        step = 4 if j == 0 else 8  # pierwsza moneta co 4 h (miejsce ryzyka nr 2)
        ts = pd.date_range(close.index[0], close.index[-1], freq=f"{step}h")
        ts = ts + pd.to_timedelta(rng.integers(0, 9, len(ts)), unit="ms")  # jitter jak Binance
        rate = rng.normal(1e-4, 3e-4, len(ts))
        rate[rng.random(len(ts)) < 0.02] = np.nan
        raw[c] = pd.DataFrame({"timestamp": ts, "funding_rate": rate})
    return fs.build_settlements(raw, list(close.columns), close.index)


def _holdings(forms, index, columns, n_days):
    out = []
    for k, (t_pos, w_new) in enumerate(forms):
        t_next = forms[k + 1][0] if k + 1 < len(forms) else n_days - 1
        out.append((index[t_pos + 1], index[t_next], pd.Series(w_new, index=columns)))
    return out


def test_dollar_way_matches_numpy_ts1_with_liquidation():
    close, _ = _panel(4, n_days=90)
    rets_np = close.pct_change(fill_method=None).to_numpy()
    rets = pd.DataFrame(rets_np, index=close.index, columns=close.columns)
    rng = np.random.default_rng(5)
    forms = [(t, rng.normal(0, 0.5, close.shape[1])) for t in range(30, 90, 7)]
    prev = close.shift(1)
    lo, hi = close * 0.75 / prev, close * 1.35 / prev
    st_ = _synthetic_settlements(close, 6)
    pos = fs.ts_liq_positions(rets_np, forms, lo.to_numpy(), hi.to_numpy(), 2.0, 0.01)
    b = fs.settlement_funding(
        pos.W, pos.R, pos.alive_end, pos.first, st_, fs.interp_ratio(st_, pos.R)
    )
    f = np.nan_to_num(fs.daily_sum(st_, *close.shape), nan=0.0)
    eng = phase_returns_liq(
        rets_np, f, close.index, forms, 0.0, lo.to_numpy(), hi.to_numpy(), 2.0, 0.01
    )
    assert eng["liquidations"].sum() > 0
    gross = eng.set_index("date")["gross"]
    capital = (1.0 + gross).cumprod().shift(1).fillna(1.0)
    dollars = fs.dollar_way_b1(
        _holdings(forms, close.index, close.columns, len(close)),
        rets,
        _settle_dict(st_, list(close.columns)),
        _interp_fn(rets),
        capital,
        lo,
        hi,
    )
    mine = pd.Series(b["b1"].sum(axis=1), index=close.index)
    assert np.allclose(mine.to_numpy(), dollars.to_numpy(), atol=1e-13)
    assert abs(mine.sum()) > 1e-4  # kontrola: porównanie nie jest trywialne (same zera)


def test_dollar_way_matches_numpy_x1_fixed_quantity():
    close, _ = _panel(7, n_days=90)
    members = {close.index[0]: list(close.columns)}
    dates = list(close.index[30::7])
    st_ = _synthetic_settlements(close, 8)
    signal = signal_panel(close)
    pos = fs.xs_positions(close, members, dates, rank_legs, 0.5, 3, signal)
    b = fs.settlement_funding(
        pos.W, pos.R, pos.alive_end, pos.first, st_, fs.interp_ratio(st_, pos.R)
    )
    rets = close.pct_change()
    holdings = []
    for k, t in enumerate(dates):
        legs = rank_legs(signal.loc[t], members[close.index[0]], None, 3)
        w = pd.Series(0.0, index=close.columns)
        w[legs[0]] = 0.5 / 3
        w[legs[1]] = -0.5 / 3
        last = dates[k + 1] if k + 1 < len(dates) else close.index[-1]
        holdings.append((t + pd.Timedelta(days=1), last, w))
    dollars = fs.dollar_way_b1(
        holdings, rets, _settle_dict(st_, list(close.columns)), _interp_fn(rets)
    )
    mine = pd.Series(b["b1"].sum(axis=1), index=close.index)
    assert np.allclose(mine.to_numpy(), dollars.to_numpy(), atol=1e-13)
    assert abs(mine.sum()) > 1e-4
