"""Testy czystych funkcji sondy P2 (backtest/carry_probe.py), w tym test przecieku (zasada 2)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest.carry_probe import (
    DAY_MS,
    HOUR_MS,
    WINDOW_MS,
    avg_pairwise_corr,
    compute_windows,
    exit_price,
    is_eligible,
    k_effective,
    mean_ci_neff,
    dispersion_neff,
    prepare_symbol,
    price_at,
    received_funding,
    required_windows,
    select_baskets,
    signal_at,
    turnover,
    universe_at,
    volume_trailing,
    window_starts,
)

T0 = int(pd.Timestamp("2021-03-01T00:00:00Z").value // 1_000_000)


def _make(fund_ms, rates, open_days_ms, closes, vols=None):
    fund = pd.DataFrame(
        {"timestamp": pd.to_datetime(fund_ms, unit="ms", utc=True), "funding_rate": rates}
    )
    kl = pd.DataFrame(
        {
            "open_time": pd.to_datetime(open_days_ms, unit="ms", utc=True),
            "close": closes,
            "quote_volume": vols if vols is not None else [1.0] * len(closes),
        }
    )
    return prepare_symbol(fund, kl)


def _regular(start_ms, days, rate=0.0001, interval_h=8, jitter_ms=14, price=100.0, drift=0.0):
    n_f = days * 24 // interval_h
    fund_ms = [start_ms + i * interval_h * HOUR_MS + jitter_ms for i in range(n_f)]
    opens = [start_ms + d * DAY_MS for d in range(days)]
    closes = [price * (1 + drift) ** d for d in range(days)]
    return _make(fund_ms, [rate] * n_f, opens, closes)


def test_signal_excludes_settlement_at_t_and_received_counts_six():
    start = T0 - 40 * DAY_MS
    sd = _regular(start, 60, rate=0.001)
    # sygnał: rozliczenia t-48h+jitter … t-8h+jitter => 6 sztuk; rozliczenie o t (t+14ms) poza
    assert signal_at(sd, T0) == pytest.approx(0.006)
    # otrzymany: t+8h … t+48h => 6 sztuk
    assert received_funding(sd, T0) == pytest.approx(0.006)


def test_funding_summed_by_time_not_by_period_count():
    start = T0 - 40 * DAY_MS
    sd4h = _regular(start, 60, rate=0.001, interval_h=4)
    assert signal_at(sd4h, T0) == pytest.approx(0.012)


def test_price_at_uses_candle_closing_exactly_at_t():
    start = T0 - 5 * DAY_MS
    sd = _make(
        [start], [0.0], [start + d * DAY_MS for d in range(10)], [float(d) for d in range(10)]
    )
    # świeca otwarta o T0 - 1d zamyka się o T0; jej indeks to 4
    assert price_at(sd, T0) == 4.0
    assert np.isnan(price_at(sd, T0 + HOUR_MS))


def test_exit_price_for_symbol_delisted_mid_window():
    start = T0 - 5 * DAY_MS
    opens = [start + d * DAY_MS for d in range(6)]  # ostatnia świeca zamyka się o T0 + 1d
    sd = _make([start], [0.0], opens, [1, 2, 3, 4, 5, 6.0])
    assert price_at(sd, T0) == 5.0
    assert exit_price(sd, T0) == 6.0  # nie znika — wychodzi po ostatnim zamknięciu


def test_exit_price_without_any_later_close_is_entry():
    start = T0 - 5 * DAY_MS
    sd = _make([start], [0.0], [start + d * DAY_MS for d in range(5)], [1, 2, 3, 4, 5.0])
    assert exit_price(sd, T0) == price_at(sd, T0) == 5.0


def test_eligibility_requires_30_days_of_funding_history():
    young = _regular(T0 - 20 * DAY_MS, 25)
    old = _regular(T0 - 40 * DAY_MS, 45)
    assert not is_eligible(young, T0)
    assert is_eligible(old, T0)


def test_select_baskets_deciles_and_deterministic_ties():
    sig = pd.Series({f"S{i:02d}": 0.0001 for i in range(30)})
    sig["S05"] = 0.01
    sig["S06"] = -0.01
    shorts, longs = select_baskets(sig)
    assert len(shorts) == len(longs) == 3
    assert "S05" in shorts and "S06" in longs
    assert select_baskets(sig) == (shorts, longs)
    assert not set(shorts) & set(longs)


def test_select_baskets_minimum_size():
    sig = pd.Series({f"S{i}": float(i) for i in range(12)})
    shorts, longs = select_baskets(sig)
    assert len(shorts) == 2 and len(longs) == 2


def test_turnover():
    assert turnover(None, ["A", "B"]) == 1.0
    assert turnover(["A", "B"], ["A", "B"]) == 0.0
    assert turnover(["A", "B"], ["A", "C"]) == 0.5


def test_window_starts_non_overlapping_and_bounded():
    s = window_starts("2020-01-01T00:00:00Z", "2020-01-11T00:00:00Z")
    assert len(s) == 5
    assert all(b - a == WINDOW_MS for a, b in zip(s, s[1:], strict=False))


def test_required_windows():
    assert required_windows(0.0, 1.0) == float("inf")
    assert required_windows(-0.1, 1.0) == float("inf")
    assert required_windows(1.0, 1.0) == pytest.approx((1.959964 + 0.841621) ** 2)


def test_k_effective_limits():
    assert k_effective(50, 0.0) == pytest.approx(50)
    assert k_effective(50, 1.0) == pytest.approx(1)


def test_dispersion_neff_does_not_return_mean():
    out = dispersion_neff(pd.Series(np.random.default_rng(0).normal(5, 1, 500)))
    assert "mean" not in out and set(out) == {"n", "n_eff", "std"}


def test_mean_ci_neff_contains_true_mean_for_iid_noise():
    x = pd.Series(np.random.default_rng(1).normal(0.001, 0.01, 2000))
    r = mean_ci_neff(x)
    assert r["ci_low"] < 0.001 < r["ci_high"]


def test_avg_pairwise_corr_identical_series_is_one():
    rng = np.random.default_rng(2)
    base = rng.normal(size=100)
    df = pd.DataFrame({"A": base, "B": base * 2, "C": base + 1e-12})
    assert avg_pairwise_corr(df) == pytest.approx(1.0)


def _universe(n_sym, high_idx=0, low_idx=1, days=80):
    data = {}
    start = T0 - 40 * DAY_MS
    for i in range(n_sym):
        rate = 0.001 if i == high_idx else (-0.001 if i == low_idx else 0.0001)
        data[f"S{i:02d}"] = _regular(start, days, rate=rate)
    return data


def test_compute_windows_carry_sign_and_skip_small_universe():
    data = _universe(25)
    w, rets = compute_windows(data, [T0], c_rt=0.0)
    row = w.iloc[0]
    assert not row["skipped"]
    # SHORT dostaje +0,006 (wysoki funding), LONG płaci -0,006 => F > 0
    assert row["F"] > 0
    assert row["C"] == 0.0
    small, _ = compute_windows(_universe(10), [T0], c_rt=0.001)
    assert bool(small.iloc[0]["skipped"])


def test_compute_windows_cost_uses_turnover():
    data = _universe(25)
    w, _ = compute_windows(data, [T0, T0 + WINDOW_MS], c_rt=0.001)
    assert w.iloc[0]["C"] == pytest.approx(0.002)  # pierwsze okno: pełny obrót obu nóg
    assert w.iloc[1]["C"] == pytest.approx(0.0)  # stałe stawki => te same koszyki


def test_universe_top_n_by_trailing_volume():
    data = _universe(25)
    start = T0 - 40 * DAY_MS
    opens = [start + d * DAY_MS for d in range(80)]
    fund_ms = [start + i * 8 * HOUR_MS + 14 for i in range(80 * 3)]
    data["BIG"] = _make(fund_ms, [0.0] * len(fund_ms), opens, [1.0] * 80, [1e9] * 80)
    assert "BIG" in universe_at(data, T0, top_n=3)
    assert len(universe_at(data, T0, top_n=3)) == 3


# --- Test przecieku (CLAUDE.md zasada 2): wszystko, co jest SYGNAŁEM albo KWALIFIKACJĄ w t,
#     musi dać identyczny wynik po obcięciu danych z przyszłości.


def _truncate(fund: pd.DataFrame, kl: pd.DataFrame, t_ms: int):
    t = pd.Timestamp(t_ms, unit="ms", tz="UTC")
    f = fund[fund["timestamp"] < t]
    k = kl[kl["open_time"] + pd.Timedelta(days=1) <= t]
    return prepare_symbol(f, k)


@settings(max_examples=60, deadline=None)
@given(
    seed=st.integers(0, 10_000),
    interval_h=st.sampled_from([1, 4, 8]),
    t_day=st.integers(31, 70),
)
def test_no_lookahead_in_signal_eligibility_and_volume(seed, interval_h, t_day):
    rng = np.random.default_rng(seed)
    start = T0 - 40 * DAY_MS
    days = 90
    n_f = days * 24 // interval_h
    fund = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [start + i * interval_h * HOUR_MS + int(rng.integers(0, 50)) for i in range(n_f)],
                unit="ms",
                utc=True,
            ),
            "funding_rate": rng.normal(0.0001, 0.0005, n_f),
        }
    )
    kl = pd.DataFrame(
        {
            "open_time": pd.to_datetime(
                [start + d * DAY_MS for d in range(days)], unit="ms", utc=True
            ),
            "close": np.cumprod(1 + rng.normal(0, 0.03, days)) * 100,
            "quote_volume": rng.uniform(1e6, 1e8, days),
        }
    )
    t = start + t_day * DAY_MS
    full = prepare_symbol(fund, kl)
    past = _truncate(fund, kl, t)
    assert signal_at(full, t) == pytest.approx(signal_at(past, t), abs=1e-15)
    assert is_eligible(full, t) == is_eligible(past, t)
    assert volume_trailing(full, t) == pytest.approx(volume_trailing(past, t))
    assert price_at(full, t) == price_at(past, t)


def test_leakage_detector_fires_on_forward_window():
    """Bramka musi móc zawieść: sygnał liczony z okna przyszłego MUSI różnić się po obcięciu."""
    start = T0 - 40 * DAY_MS
    rng = np.random.default_rng(3)
    n_f = 90 * 3
    fund = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [start + i * 8 * HOUR_MS + 14 for i in range(n_f)], unit="ms", utc=True
            ),
            "funding_rate": rng.normal(0.0001, 0.0005, n_f),
        }
    )
    kl = pd.DataFrame(
        {
            "open_time": pd.to_datetime(
                [start + d * DAY_MS for d in range(90)], unit="ms", utc=True
            ),
            "close": [100.0] * 90,
            "quote_volume": [1.0] * 90,
        }
    )
    t = start + 50 * DAY_MS
    full, past = prepare_symbol(fund, kl), _truncate(fund, kl, t)
    assert received_funding(full, t) != pytest.approx(received_funding(past, t))
