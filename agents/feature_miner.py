"""
feature_miner.py

Czyste, bezstanowe funkcje liczące cechy z danych OHLCV.

KONTRAKT każdej funkcji compute_*:
    input:  pd.DataFrame z kolumnami [timestamp, open, high, low, close, volume]
    output: pd.Series tej samej długości, indeksowana jak df

ZASADA LEAKAGE: każda funkcja może używać wyłącznie danych do wiersza t włącznie.
Żadnych .shift(-n), żadnego rolling(center=True), żadnej normalizacji po całym
zbiorze (np. globalny mean/std) — tylko rolling/trailing. Formalny test tego
znajduje się w agent_5_compliance/test_leakage.py (Commit 3, nie w tym pliku).

Definicje, wzory i metadane: agents/feature_registry.yaml
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import talib

# ---------------------------------------------------------------------------
# Cechy bazowe (używane też przez risk_controller i triple-barrier labeling)
# ---------------------------------------------------------------------------


def compute_atr_14(df: pd.DataFrame) -> pd.Series:
    """Average True Range, Wilder smoothing, 14-period (TA-Lib)."""
    atr = talib.ATR(df["high"].values, df["low"].values, df["close"].values, timeperiod=14)
    return pd.Series(atr, index=df.index, name="atr_14")


def compute_rsi_14(df: pd.DataFrame) -> pd.Series:
    """RSI, Wilder smoothing, 14-period (TA-Lib)."""
    rsi = talib.RSI(df["close"].values, timeperiod=14)
    return pd.Series(rsi, index=df.index, name="rsi_14")


# ---------------------------------------------------------------------------
# Cechy regime gate (filtrowanie do Test 1 / Test 2, nie input do modelu)
# ---------------------------------------------------------------------------


def compute_direction_persistence_10(df: pd.DataFrame) -> pd.Series:
    """Udział zgodności kierunku w ostatnich 10 świecach: |sum(sign(return))| / 10."""
    ret = df["close"].pct_change()
    sign = np.sign(ret)
    persistence = sign.rolling(window=10, min_periods=10).sum().abs() / 10
    return persistence.rename("direction_persistence_10")


def compute_atr_pctrank_20d(
    df: pd.DataFrame, candles_per_day: int = 288, window_days: int = 20
) -> pd.Series:
    """
    Rolling percentyl atr_14 względem trailing okna ~20 dni.

    candles_per_day=288 zakłada timeframe 5m (24*60/5). Zmień, jeśli timeframe inny.

    Implementacja: pandas Rolling.rank(pct=True) liczy rangę OSTATNIEJ wartości
    okna względem całego okna — trailing, bez leakage. Zweryfikowane empirycznie
    jako wydajne (~0.1s na 105k wierszy przy window=5760).
    """
    atr = compute_atr_14(df)
    window = candles_per_day * window_days
    pctrank = atr.rolling(window=window, min_periods=window).rank(pct=True)
    return pctrank.rename("atr_pctrank_20d")


def classify_regime(
    df: pd.DataFrame,
    trend_threshold: float = 0.7,
    range_threshold: float = 0.3,
) -> pd.Series:
    """
    Klasyfikuje każdą świecę jako 'trend', 'range' albo 'ambiguous'.

        trend:  atr_pctrank_20d > trend_threshold AND direction_persistence_10 > trend_threshold
        range:  atr_pctrank_20d < range_threshold AND direction_persistence_10 < range_threshold
        ambiguous: wszystko inne -> wyklucz z Testu 1 i Testu 2

    Progi to wartości STARTOWE do kalibracji w walk-forward (Commit 4), nie finalne.
    To reguła deterministyczna (nie model) — patrz uzasadnienie: audytowalność +
    brak dodatkowego zużycia budżetu statystycznego na uczenie regime gate.
    """
    atr_rank = compute_atr_pctrank_20d(df)
    persistence = compute_direction_persistence_10(df)

    regime = pd.Series("ambiguous", index=df.index, name="regime")
    trend_mask = (atr_rank > trend_threshold) & (persistence > trend_threshold)
    range_mask = (atr_rank < range_threshold) & (persistence < range_threshold)
    regime.loc[trend_mask] = "trend"
    regime.loc[range_mask] = "range"
    return regime


# ---------------------------------------------------------------------------
# Cechy Test 1 — Momentum (używane tylko na świecach z regime == "trend")
# ---------------------------------------------------------------------------


def compute_return_lag_1(df: pd.DataFrame) -> pd.Series:
    """Log-return względem poprzedniej świecy. Współdzielona z Testem 2."""
    ret = np.log(df["close"] / df["close"].shift(1))
    return ret.rename("return_lag_1")


def compute_momentum_5(df: pd.DataFrame) -> pd.Series:
    """Log-return względem świecy t-5."""
    mom = np.log(df["close"] / df["close"].shift(5))
    return mom.rename("momentum_5")


def compute_ema_diff_9_21(df: pd.DataFrame) -> pd.Series:
    """(EMA9 - EMA21) / close — znormalizowane przez cenę (porównywalne między poziomami ceny)."""
    ema9 = talib.EMA(df["close"].values, timeperiod=9)
    ema21 = talib.EMA(df["close"].values, timeperiod=21)
    diff = (ema9 - ema21) / df["close"].values
    return pd.Series(diff, index=df.index, name="ema_diff_9_21")


def compute_volume_zscore_20(df: pd.DataFrame) -> pd.Series:
    """Rolling z-score wolumenu, okno 20, trailing. Współdzielona z Testem 2."""
    roll = df["volume"].rolling(window=20, min_periods=20)
    z = (df["volume"] - roll.mean()) / roll.std()
    return z.rename("volume_zscore_20")


# ---------------------------------------------------------------------------
# Cechy Test 2 — Mean-reversion (używane tylko na świecach z regime == "range")
# ---------------------------------------------------------------------------


def compute_price_zscore_20(df: pd.DataFrame) -> pd.Series:
    """Rolling z-score ceny zamknięcia, okno 20, trailing."""
    roll = df["close"].rolling(window=20, min_periods=20)
    z = (df["close"] - roll.mean()) / roll.std()
    return z.rename("price_zscore_20")


# ---------------------------------------------------------------------------
# Orkiestracja
# ---------------------------------------------------------------------------

FEATURE_FUNCTIONS = {
    "atr_14": compute_atr_14,
    "atr_pctrank_20d": compute_atr_pctrank_20d,
    "direction_persistence_10": compute_direction_persistence_10,
    "return_lag_1": compute_return_lag_1,
    "momentum_5": compute_momentum_5,
    "ema_diff_9_21": compute_ema_diff_9_21,
    "volume_zscore_20": compute_volume_zscore_20,
    "rsi_14": compute_rsi_14,
    "price_zscore_20": compute_price_zscore_20,
}


def compute_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dolicza wszystkie cechy z FEATURE_FUNCTIONS + kolumnę 'regime' jako nowe
    kolumny. Nie mutuje df wejściowego.
    """
    out = df.copy()
    for name, fn in FEATURE_FUNCTIONS.items():
        out[name] = fn(df)
    out["regime"] = classify_regime(df)
    return out


def split_by_regime(df_with_features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filtruje do dwóch podzbiorów: (test1_trend_momentum, test2_range_reversion).
    Wymaga, żeby df_with_features miał już kolumnę 'regime' (patrz compute_all_features).
    """
    test1 = df_with_features[df_with_features["regime"] == "trend"].reset_index(drop=True)
    test2 = df_with_features[df_with_features["regime"] == "range"].reset_index(drop=True)
    return test1, test2
