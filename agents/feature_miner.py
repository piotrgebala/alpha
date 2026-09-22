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

# Wartości startowe reguły regime (docs/rag/02_cechy_i_leakage.md), do kalibracji
# WYŁĄCZNIE wewnątrz walk-forward (CLAUDE.md zasada 1) — patrz
# backtest/calibrate_regime_thresholds.py (Commit 2.5). Źródło prawdy mirroring:
# config/settings.yaml sekcja `regime_rule`. Nazwane stałe (nie literały w sygnaturze
# funkcji) od Commitu 2.5 — zero magic numbers poza registry/configiem (docs/rag/05),
# ten sam wzorzec co ATR_MULTIPLIER w agents/labeling.py.
DEFAULT_TREND_THRESHOLD = 0.7
DEFAULT_RANGE_THRESHOLD = 0.3

# Konwersja "liczba świec na dzień" -> zależy WYŁĄCZNIE od timeframe danych wejściowych, nie od
# hipotezy (w odróżnieniu od progów regime wyżej). Mirroring config/settings.yaml sekcja
# `features.candles_per_day` (tam już udokumentowane: "zmień, jeśli timeframe inny" — Commit 2.6
# to pierwsze użycie tej furtki, dotąd nieużywanej programowo). Wartość startowa 288 = 24h*60/5min
# (timeframe 5m, Commit 1-2.5). Błędna wartość tutaj NIE jest tuningiem hipotezy — to bug
# jednostek: `atr_pctrank_20d` przestaje reprezentować "~20 dni kalendarzowych" i staje się oknem
# o niezdefiniowanej (błędnej) długości czasowej, patrz `compute_atr_pctrank_20d`.
DEFAULT_CANDLES_PER_DAY = 288

# ---------------------------------------------------------------------------
# Cechy bazowe (używane też przez risk_controller i triple-barrier labeling)
# ---------------------------------------------------------------------------


def compute_atr_14(df: pd.DataFrame) -> pd.Series:
    """Average True Range, Wilder smoothing, 14-period (TA-Lib)."""
    atr = talib.ATR(
        df["high"].values, df["low"].values, df["close"].values, timeperiod=14
    )
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
    df: pd.DataFrame,
    candles_per_day: int = DEFAULT_CANDLES_PER_DAY,
    window_days: int = 20,
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
    trend_threshold: float = DEFAULT_TREND_THRESHOLD,
    range_threshold: float = DEFAULT_RANGE_THRESHOLD,
    candles_per_day: int = DEFAULT_CANDLES_PER_DAY,
) -> pd.Series:
    """
    Klasyfikuje każdą świecę jako 'trend', 'range' albo 'ambiguous'.

        trend:  atr_pctrank_20d > trend_threshold AND direction_persistence_10 > trend_threshold
        range:  atr_pctrank_20d < range_threshold AND direction_persistence_10 < range_threshold
        ambiguous: wszystko inne -> wyklucz z Testu 1 i Testu 2

    Progi to wartości STARTOWE do kalibracji w walk-forward (Commit 4), nie finalne.
    To reguła deterministyczna (nie model) — patrz uzasadnienie: audytowalność +
    brak dodatkowego zużycia budżetu statystycznego na uczenie regime gate.

    `candles_per_day` (Commit 2.6): przekazywane WYŁĄCZNIE do `compute_atr_pctrank_20d`, żeby
    okno "~20 dni" pozostało ~20 dni KALENDARZOWYCH niezależnie od timeframe danych wejściowych
    (domyślnie 288 = 5m). To konwersja jednostek, nie parametr hipotezy — w odróżnieniu od
    `trend_threshold`/`range_threshold` NIE jest kandydatem do kalibracji.

    UWAGA (Commit 2.5, 2026-09-21): `direction_persistence_10` jest zmienną DYSKRETNĄ
    (`|sum(sign(return))|/10`, przyjmuje tylko wartości `k/10`) — patrz
    `backtest/diagnose_cost_feasibility.py` (blok 1). Próg 0.7 wpada w lukę jej
    rozkładu (masa siedzi na 0.6 i 0.8), co samo z siebie czyni `trend` prawie pustym,
    niezależnie od `atr_pctrank_20d`. Kalibracja progów: `backtest/
    calibrate_regime_thresholds.py` (poza pytest, jak inne skrypty analityczne) —
    porównuje z góry zarejestrowany, mały zestaw kandydatów (wybrany ze WŁASNOŚCI
    formuły persistence — dyskretne kroki k/10 — nie z podglądania Sharpe na tym
    zbiorze, CLAUDE.md zasada 1) przez pełny walk-forward checkpoint, bez
    automatycznego wyboru "zwycięzcy" — decyzja zostaje przy użytkowniku.
    """
    atr_rank = compute_atr_pctrank_20d(df, candles_per_day=candles_per_day)
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


def compute_adx_14(df: pd.DataFrame) -> pd.Series:
    """
    Average Directional Index, 14-period (TA-Lib) — siła trendu NIEZALEŻNA od
    kierunku, wartości ciągłe w [0, 100].

    Commit 2.8 (promocja z screeningu C2.7, `backtest/screen_feature_candidates.py`):
    korelacja Spearman cecha-cecha na realnych danych BTC pokazała, że `adx_14` jest
    JEDYNYM z 8 kandydatów screeningu nisko skorelowanym z resztą registry (w tym,
    zaskakująco, z `direction_persistence_10` — corr=+0,07, mimo że oba mają mierzyć
    "siłę trendu") — sensowny kandydat do formalnego testu OOS jako DODATEK do
    `MOMENTUM_FEATURES` (agents/ml_optimizer.py), nie zamiennik. Wynik formalnego
    testu OOS: `backtest/evaluate_feature_candidate.py`,
    `runs/2026-09-21_c2.8-adx14-oos-evaluation/README.md`.
    """
    adx = talib.ADX(
        df["high"].values, df["low"].values, df["close"].values, timeperiod=14
    )
    return pd.Series(adx, index=df.index, name="adx_14")


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
    "adx_14": compute_adx_14,
}


def compute_all_features(
    df: pd.DataFrame,
    trend_threshold: float = DEFAULT_TREND_THRESHOLD,
    range_threshold: float = DEFAULT_RANGE_THRESHOLD,
    candles_per_day: int = DEFAULT_CANDLES_PER_DAY,
) -> pd.DataFrame:
    """
    Dolicza wszystkie cechy z FEATURE_FUNCTIONS + kolumnę 'regime' jako nowe
    kolumny. Nie mutuje df wejściowego.

    `trend_threshold`/`range_threshold` przekazywane do `classify_regime` —
    parametryzowane od Commitu 2.5, żeby `backtest.engine.run_backtest` (a przez
    nią `backtest/calibrate_regime_thresholds.py`) mogło porównywać kandydatów bez
    duplikowania logiki regime gate.

    `candles_per_day` (Commit 2.6): przekazywane do `classify_regime` ->
    `compute_atr_pctrank_20d` — konwersja jednostek dla timeframe inny niż 5m (domyślny),
    żeby `backtest.engine.run_backtest` mogło uruchomić identyczny pipeline na danych 1h/4h
    (`backtest/checkpoint_timeframe_robustness.py`) bez łamania semantyki "~20 dni" okna ATR.
    """
    out = df.copy()
    for name, fn in FEATURE_FUNCTIONS.items():
        out[name] = fn(df)
    out["regime"] = classify_regime(
        df, trend_threshold, range_threshold, candles_per_day
    )
    return out


def split_by_regime(
    df_with_features: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filtruje do dwóch podzbiorów: (test1_trend_momentum, test2_range_reversion).
    Wymaga, żeby df_with_features miał już kolumnę 'regime' (patrz compute_all_features).
    """
    test1 = df_with_features[df_with_features["regime"] == "trend"].reset_index(
        drop=True
    )
    test2 = df_with_features[df_with_features["regime"] == "range"].reset_index(
        drop=True
    )
    return test1, test2
