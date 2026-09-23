"""
test_ta_rules.py

Runda A2: cechy analizy technicznej ze skilla `ta-toolkit` przeniesione do agents/ta_rules.py
i reguły kierunkowe z nich. Test przecieku każdej cechy mieszka w agent_5_compliance/
test_leakage.py (parametryzowany po TA_FEATURE_FUNCTIONS — CLAUDE.md zasada 2). Tu: semantyka
potwierdzonych swingów (opóźnienie o `confirm` barów), kontrakt cech, semantyka reguł
(stan vs zdarzenie, pasma, znaki) i własności w hypothesis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

import agents.ta_rules as ta


def _df(
    close: np.ndarray, high: np.ndarray | None = None, low: np.ndarray | None = None
) -> pd.DataFrame:
    n = len(close)
    high = np.asarray(close) + 1.0 if high is None else high
    low = np.asarray(close) - 1.0 if low is None else low
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="4h", tz="UTC"),
            "open": np.asarray(close, dtype=float),
            "high": np.asarray(high, dtype=float),
            "low": np.asarray(low, dtype=float),
            "close": np.asarray(close, dtype=float),
            "volume": np.full(n, 10.0),
        }
    )


def _random_ohlcv(seed: int, n: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, n))
    open_ = np.r_[100.0, close[:-1]] * (1.0 + rng.normal(0.0, 0.003, n))
    high = np.maximum(open_, close) * (1.0 + rng.uniform(0.0, 0.01, n))
    low = np.minimum(open_, close) * (1.0 - rng.uniform(0.0, 0.01, n))
    df = _df(close, high, low)
    df["open"] = open_
    return df


# --- swingi ------------------------------------------------------------------------------------


def test_confirmed_swing_high_is_known_exactly_confirm_bars_after_the_peak() -> None:
    n = 40
    close = np.full(n, 100.0)
    high = np.full(n, 101.0)
    high[20] = 110.0
    sh, _ = ta.confirmed_swings(_df(close, high=high), confirm=5)
    assert sh.iloc[20:25].isna().all()  # w barach 20–24 szczyt jeszcze NIE jest potwierdzony
    assert sh.iloc[25] == 110.0  # potwierdzony dokładnie po 5 barach
    assert sh.iloc[26:31].isna().all()  # okno nadal zawiera szczyt, kandydat już nie jest maksimum


def test_trend_structure_reads_rising_zigzag_as_uptrend() -> None:
    x = np.arange(240)
    close = 100.0 + 0.5 * x + 4.0 * np.sin(x / 3.0)
    ts = ta.compute_trend_structure(_df(close))
    assert set(ts.dropna().unique()) <= {-1.0, 0.0, 1.0}
    assert (ts.dropna().tail(60) == 1.0).all()
    ts_down = ta.compute_trend_structure(_df(close[::-1].copy()))
    assert (ts_down.dropna().tail(60) == -1.0).all()


def test_breakout_fires_only_when_close_leaves_the_prior_range() -> None:
    close = np.full(60, 100.0)
    close[40] = 105.0  # wybicie w górę
    close[41] = 100.0
    close[50] = 95.0  # wybicie w dół
    b = ta.compute_breakout(_df(close), n=20)
    assert b.iloc[40] == 1.0 and b.iloc[41] == 0.0 and b.iloc[50] == -1.0
    assert b.iloc[:20].isna().all()
    assert (b.iloc[20:40] == 0.0).all()


def test_ta_features_contract_same_index_all_columns_float() -> None:
    df = _random_ohlcv(3, 400)
    out = ta.compute_ta_features(df)
    for name in ta.TA_FEATURE_FUNCTIONS:
        assert name in out.columns and out[name].index.equals(df.index)
        assert out[name].dtype.kind == "f"
    assert out["ma_cross_age"].dropna().min() == 0.0
    assert set(out["fib_impulse"].dropna().unique()) <= {-1.0, 1.0}
    assert set(out["breakout"].dropna().unique()) <= {-1.0, 0.0, 1.0}


def _rising_with_spikes(n: int = 80) -> pd.DataFrame:
    """Monotonicznie rosnący szereg (bez remisów → bez swingów) z jawnie wstawionymi ekstremami:
    dołek 80,0 w barze 30, szczyt 200 w barze 50, dołek 80,2 w barze 60."""
    close = 100.0 + 0.1 * np.arange(n)
    high, low = close + 0.5, close - 0.5
    low[30], high[50], low[60] = 80.0, 200.0, 80.2
    return _df(close, high, low)


def test_sr_distance_uses_the_confirmed_level_and_forgets_it_after_lookback() -> None:
    df = _rising_with_spikes()
    atr = ta._atr(df).to_numpy()
    d = ta.compute_sr_distance(df, lookback=3)
    # dołek z bara 30 potwierdzony w 35; przez `lookback` barów jest jedynym poziomem
    for t in range(35, 39):
        assert d.iloc[t] == (df["close"].iloc[t] - 80.0) / atr[t] > 0
    assert d.iloc[:35].isna().all()  # przed potwierdzeniem nie ma żadnego poziomu
    assert np.isnan(d.iloc[39])  # potwierdzenie w 35 < 39 − 3 → poziom wygasł


def test_fib_position_is_zero_at_impulse_start_and_one_at_its_end() -> None:
    df = _rising_with_spikes()
    pos = ta.compute_fib_position(df)
    imp = ta.compute_fib_impulse(df)
    assert pos.iloc[35:55].isna().all()  # jest dołek (80), nie ma jeszcze szczytu → brak impulsu
    for t in range(55, 60):  # szczyt 200 z bara 50 potwierdzony w 55 → impuls 80 → 200
        assert pos.iloc[t] == (df["close"].iloc[t] - 80.0) / 120.0
        assert imp.iloc[t] == 1.0
    probe = df.copy()
    probe.loc[57, "close"] = 80.0
    assert ta.compute_fib_position(probe).iloc[57] == 0.0
    probe.loc[57, "close"] = 200.0
    assert ta.compute_fib_position(probe).iloc[57] == 1.0


def test_double_bottom_is_confirmed_once_at_the_second_low_and_rule_fires_once() -> None:
    df = _rising_with_spikes()
    state = ta.compute_double_top_bottom(df)
    # drugi dołek (80,2 w barze 60) potwierdzony w 65: |80,0 − 80,2| ≤ 0,5·ATR, odbicie do 200 ≥ 2·ATR
    assert state.iloc[65] == 1.0
    assert (state.iloc[36:65].fillna(0.0) == 0.0).all()
    rule = ta.rule_double_top_bottom(pd.DataFrame({"double_top_bottom": state}))
    fired = rule.iloc[55:80]
    assert fired.iloc[10] == 1.0 and (fired.drop(index=fired.index[10]) == 0.0).all()


# --- reguły ------------------------------------------------------------------------------------


def test_event_rules_fire_only_where_the_state_changes_to_nonzero() -> None:
    state = pd.Series([np.nan, 0.0, 1.0, 1.0, 1.0, 0.0, -1.0, -1.0, 1.0])
    f = pd.DataFrame({"double_top_bottom": state, "head_shoulders": state})
    expected = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0]
    assert ta.rule_double_top_bottom(f).tolist() == expected
    assert ta.rule_head_shoulders(f).tolist() == expected


def test_ma_cross_rule_fires_at_age_zero_in_the_direction_of_the_new_state() -> None:
    f = pd.DataFrame(
        {
            "ma_state": [np.nan, -0.1, -0.2, 0.1, 0.2, -0.05],
            "ma_cross_age": [np.nan, np.nan, 1.0, 0.0, 1.0, 0.0],
        }
    )
    assert ta.rule_ma_cross(f).tolist() == [0.0, 0.0, 0.0, 1.0, 0.0, -1.0]


def test_trendline_break_rule_fires_on_sign_change_only() -> None:
    f = pd.DataFrame({"trendline_distance": [np.nan, 0.01, 0.02, -0.01, -0.03, 0.005, 0.01]})
    assert ta.rule_trendline_break(f).tolist() == [0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0]


def test_sr_bounce_rule_only_within_half_atr_with_the_sign_of_the_distance() -> None:
    f = pd.DataFrame({"sr_distance": [0.3, -0.4, 0.6, -0.5, np.nan, 0.0]})
    assert ta.rule_sr_bounce(f).tolist() == [1.0, -1.0, 0.0, -1.0, 0.0, 0.0]


def test_fib_retrace_rule_uses_band_and_impulse_direction() -> None:
    f = pd.DataFrame(
        {
            "fib_position": [0.2, 0.4, 0.618, 0.7, 0.5, 0.382],
            "fib_impulse": [1.0, 1.0, -1.0, -1.0, np.nan, 1.0],
        }
    )
    assert ta.rule_fib_retrace(f).tolist() == [0.0, 1.0, -1.0, 0.0, 0.0, 1.0]


def test_rule_sets_partition_all_rules() -> None:
    assert ta.EVENT_RULES | ta.STATE_RULES == set(ta.TA_RULE_FUNCTIONS)
    assert not (ta.EVENT_RULES & ta.STATE_RULES)


def test_event_group_signal_is_sign_of_sum_with_conflicts_zeroed() -> None:
    rules = pd.DataFrame(
        {
            "rule_breakout": [1.0, 0.0, 1.0, 0.0],
            "rule_double_top_bottom": [0.0, -1.0, -1.0, 0.0],
            "rule_head_shoulders": [0.0, 0.0, 0.0, 0.0],
            "rule_ma_cross": [1.0, 0.0, 0.0, 0.0],
            "rule_trendline_break": [0.0, -1.0, 0.0, 0.0],
            "rule_trend_structure": [-1.0, -1.0, -1.0, -1.0],  # stanowa — poza grupą
        }
    )
    assert ta.event_group_signal(rules).tolist() == [1.0, -1.0, 0.0, 0.0]


@given(seed=st.integers(0, 5_000), n=st.integers(80, 400))
@settings(max_examples=25, deadline=None)
def test_rules_are_ternary_and_events_never_exceed_state_changes(seed: int, n: int) -> None:
    df = _random_ohlcv(seed, n)
    feats = ta.compute_ta_features(df)
    rules = ta.compute_ta_rules(feats)
    assert list(rules.columns) == list(ta.TA_RULE_FUNCTIONS)
    for name in rules:
        assert set(rules[name].unique()) <= {-1.0, 0.0, 1.0}
        assert not rules[name].isna().any()
    for state_col, rule_col in (
        ("double_top_bottom", "rule_double_top_bottom"),
        ("head_shoulders", "rule_head_shoulders"),
    ):
        s = feats[state_col].fillna(0.0)
        changes = int((s != s.shift(1)).sum())
        assert int((rules[rule_col] != 0).sum()) <= changes
    near = feats["sr_distance"].abs() <= ta.SR_NEAR_ATR
    assert (rules["rule_sr_bounce"][~near.fillna(False)] == 0.0).all()
    in_band = feats["fib_position"].between(*ta.FIB_BAND)
    assert (rules["rule_fib_retrace"][~in_band.fillna(False)] == 0.0).all()
