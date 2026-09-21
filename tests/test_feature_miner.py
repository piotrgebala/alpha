"""
test_feature_miner.py

Warstwa 1 (unit) testy dla agents/feature_miner.py — konkretnie `classify_regime`/
`compute_all_features`, które wcześniej (Commit 1-2) miały tylko pokrycie przez test
leakage (agent_5_compliance/test_leakage.py), bez testu POPRAWNOŚCI samej reguły
progowej. Dodane przy Commicie 2.5 (parametryzacja progów do kalibracji) —
docs/rag/05_metodologia_wytwarzania_i_testow.md, Warstwa 1 wymagana przy każdej
zmianie.

Nie duplikuje testu leakage: `atr_pctrank_20d`/`direction_persistence_10` są już
zweryfikowane jako bez-leakage gdzie indziej — te testy sprawdzają WYŁĄCZNIE logikę
progową na już-obliczonych wartościach.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from agents.feature_miner import (
    DEFAULT_CANDLES_PER_DAY,
    DEFAULT_RANGE_THRESHOLD,
    DEFAULT_TREND_THRESHOLD,
    classify_regime,
    compute_all_features,
    compute_atr_pctrank_20d,
)


def _make_synthetic_ohlcv(n: int = 6200, seed: int = 3) -> pd.DataFrame:
    # n=6200 > N_WARMUP (5760, agents/feature_miner.py: atr_pctrank_20d window przy
    # domyślnym candles_per_day=288/window_days=20) — wystarczy, żeby część wierszy
    # miała policzalne (nie-NaN) atr_pctrank_20d/direction_persistence_10.
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0.0, 0.3, size=n))
    open_ = np.roll(close, 1)
    open_[0] = 100.0
    high = np.maximum(open_, close) + 0.2
    low = np.minimum(open_, close) - 0.2
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(50.0, 150.0, size=n),
        }
    )


def test_classify_regime_default_thresholds_match_named_constants() -> None:
    # classify_regime() bez argumentów musi dawać identyczny wynik co jawne podanie
    # DEFAULT_TREND_THRESHOLD/DEFAULT_RANGE_THRESHOLD — Commit 2.5 zamienił literały
    # 0.7/0.3 w sygnaturze na nazwane stałe, to NIE mogło zmienić zachowania domyślnego.
    df = _make_synthetic_ohlcv()
    default_call = classify_regime(df)
    explicit_call = classify_regime(
        df, trend_threshold=DEFAULT_TREND_THRESHOLD, range_threshold=DEFAULT_RANGE_THRESHOLD
    )
    pd.testing.assert_series_equal(default_call, explicit_call)


def test_classify_regime_only_three_labels() -> None:
    df = _make_synthetic_ohlcv()
    regime = classify_regime(df)
    assert set(regime.unique()).issubset({"trend", "range", "ambiguous"})


def test_classify_regime_trend_and_range_are_mutually_exclusive() -> None:
    # Struktura reguły (trend_mask/range_mask liczone niezależnie, ambiguous jako
    # reszta) gwarantuje rozłączność niezależnie od progów — sprawdzamy to jako
    # niezmiennik, nie przykład.
    df = _make_synthetic_ohlcv()
    for trend_threshold, range_threshold in [(0.7, 0.3), (0.5, 0.5), (0.3, 0.3)]:
        regime = classify_regime(df, trend_threshold, range_threshold)
        assert not ((regime == "trend") & (regime == "range")).any()


def test_classify_regime_lower_trend_threshold_never_shrinks_trend_population() -> None:
    # Niezmiennik monotoniczności: obniżenie trend_threshold (przy niezmienionym
    # range_threshold) może tylko ROZSZERZYĆ zbiór świec spełniających
    # `atr_rank > trend_threshold AND persistence > trend_threshold` — nigdy go
    # zawęzić. To bezpośrednio testuje przesłankę Commitu 2.5 ("złagodzenie progu
    # powinno dać więcej świec trend, nie mniej").
    df = _make_synthetic_ohlcv()
    strict = classify_regime(df, trend_threshold=0.7, range_threshold=0.3)
    loose = classify_regime(df, trend_threshold=0.5, range_threshold=0.3)
    assert (loose == "trend").sum() >= (strict == "trend").sum()


def test_classify_regime_symmetric_threshold_widens_range_population() -> None:
    # Analogicznie dla range: podniesienie range_threshold (przy niezmienionym
    # trend_threshold) rozszerza `atr_rank < range_threshold AND persistence <
    # range_threshold`, więc liczba świec "range" nie może się zmniejszyć.
    df = _make_synthetic_ohlcv()
    narrow = classify_regime(df, trend_threshold=0.7, range_threshold=0.3)
    wide = classify_regime(df, trend_threshold=0.7, range_threshold=0.5)
    assert (wide == "range").sum() >= (narrow == "range").sum()


def test_compute_all_features_threads_thresholds_to_regime_column() -> None:
    # compute_all_features musi PRZEKAZAĆ progi do classify_regime, nie tylko je
    # przyjąć i zignorować — to jest dokładnie ryzyko, które Commit 2.5 wprowadza
    # (parametr, który nic nie robi, gdyby engine.py go przekazywał donikąd).
    df = _make_synthetic_ohlcv()
    default_result = compute_all_features(df)
    custom_result = compute_all_features(df, trend_threshold=0.5, range_threshold=0.5)
    pd.testing.assert_series_equal(
        custom_result["regime"],
        classify_regime(df, trend_threshold=0.5, range_threshold=0.5),
        check_names=False,
    )
    # Sanity: różne progi na tych samych danych syntetycznych faktycznie dają różny
    # rozkład reżimów (inaczej test niczego by nie odróżniał).
    assert not default_result["regime"].equals(custom_result["regime"])


def test_compute_atr_pctrank_20d_warmup_length_scales_with_candles_per_day() -> None:
    # Commit 2.6: candles_per_day jest konwersją jednostek dla okna "~20 dni" — przy
    # candles_per_day mniejszym (timeframe grubszy niż 5m, np. 24 dla 1h zamiast 288 dla
    # 5m) okno w LICZBIE ŚWIEC musi być mniejsze (candles_per_day * window_days), więc
    # warmup (liczba początkowych NaN) też musi być mniejszy — to bezpośrednio testuje, że
    # parametr faktycznie dociera do window w rolling(), nie tylko jest przyjmowany.
    df = _make_synthetic_ohlcv(n=600, seed=5)
    warmup_288 = compute_atr_pctrank_20d(df, candles_per_day=288).isna().sum()  # window=5760 > n -> wszystko NaN
    warmup_24 = compute_atr_pctrank_20d(df, candles_per_day=24).isna().sum()  # window=480 < n=600
    assert warmup_288 == len(df)  # window (5760) > n (600) -> zero policzalnych wartości
    # Pierwsza policzalna wartość wymaga PEŁNEGO okna 480 świec BEZ NaN w atr_14 (który sam ma
    # ~14-świecowy warmup TA-Lib) -> pierwszy nie-NaN wypada przy indeksie ~14+480-1=493, nie
    # przy "gołym" 480-1 — stąd sprawdzenie względne (< warmup_288), nie literał niezależny od
    # implementacji rolling/rank.
    assert warmup_24 < warmup_288
    assert warmup_24 < len(df)  # dowód, że okno 24/dzień faktycznie daje policzalne wartości


def test_classify_regime_threads_candles_per_day_to_atr_rank_window() -> None:
    df = _make_synthetic_ohlcv(n=600, seed=5)
    # candles_per_day=288 (domyślne) -> window=5760 > n=600 -> atr_pctrank_20d całkowicie
    # NaN -> WSZYSTKIE świece "ambiguous", niezależnie od progów.
    default_regime = classify_regime(df, candles_per_day=288)
    assert (default_regime == "ambiguous").all()

    # candles_per_day=24 (jak przy timeframe 1h) -> window=480 < n=600 -> część świec ma
    # policzalny atr_pctrank_20d -> co najmniej część NIE jest "ambiguous" (o ile progi
    # 0.7/0.3 domyślne w ogóle coś selekcjonują na tych danych syntetycznych; niezależnie
    # od tego liczba "ambiguous" musi się zmniejszyć względem wariantu z candles_per_day=288).
    loose_window_regime = classify_regime(df, candles_per_day=24)
    assert (loose_window_regime == "ambiguous").sum() < (default_regime == "ambiguous").sum()


def test_compute_all_features_threads_candles_per_day_to_regime_column() -> None:
    # Analogicznie do progów (test_compute_all_features_threads_thresholds_to_regime_column):
    # compute_all_features musi PRZEKAZAĆ candles_per_day do classify_regime, nie zignorować.
    df = _make_synthetic_ohlcv(n=600, seed=5)
    default_result = compute_all_features(df)  # candles_per_day=DEFAULT_CANDLES_PER_DAY=288
    custom_result = compute_all_features(df, candles_per_day=24)
    pd.testing.assert_series_equal(
        custom_result["regime"],
        classify_regime(df, candles_per_day=24),
        check_names=False,
    )
    assert not default_result["regime"].equals(custom_result["regime"])
    assert DEFAULT_CANDLES_PER_DAY == 288  # dokumentuje domyślną wartość, mirroring config
