"""
mx_filters.py — runda MX2 (decyzja użytkownika 2026-09-25): pięć filtrów nałożonych na sygnał MX1
(przecięcie EMA 10/30 po wcześniejszym przecięciu MACD 12/26/9, `agents/ta_macd.py`). Każdy filtr
zostawia tylko te sygnały MX1, które spełniają jeden warunek — jeden zestaw parametrów, bez wariantów
(pre-rejestracja `runs/2026-09-25_mx2-filtry-1h/README.md`):

- `trend28`   — znak zwrotu z ostatnich 28 dni zgodny z kierunkiem sygnału (definicja trendu TS1,
                czyli reguły z dziennika; na 1h: 28 × 24 świece wstecz);
- `adx25`     — ADX(14) > 25 (Wilder; podręcznikowe „rynek w trendzie”; `feature_miner.compute_adx_14`);
- `wolumen`   — wolumen świecy powyżej średniej z 20 świec (`feature_miner.compute_volume_zscore_20` > 0);
- `sesja_usa` — świeca sygnału otwarta między 13:00 a 20:59 UTC (godziny sesji USA, bez korekty czasu
                letniego — jedno stałe okno);
- `rsi50`     — RSI(14) > 50 dla long i < 50 dla short (`feature_miner.compute_rsi_14`; potwierdzenie
                momentum, NIE wariant „wykupienia” 70/30).

Wszystkie wejścia liczone wyłącznie z danych ≤ t, na CIĄGŁYM szeregu świec (przed pipeline'em).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from agents.feature_miner import compute_adx_14, compute_rsi_14, compute_volume_zscore_20
from agents.ta_macd import compute_mx_rules

FILTERS = ("trend28", "adx25", "wolumen", "sesja_usa", "rsi50")
TREND_DAYS = 28
ADX_MIN = 25.0
RSI_MID = 50.0
US_HOURS = range(13, 21)  # otwarcie świecy 13:00 … 20:00 UTC


def compute_filter_inputs(df: pd.DataFrame, candles_per_day: int = 24) -> pd.DataFrame:
    """Wejścia filtrów: zwrot 28 dni, ADX(14), z-score wolumenu (20), RSI(14), godzina UTC."""
    close = df["close"]
    return pd.DataFrame(
        {
            "ret28": close / close.shift(TREND_DAYS * candles_per_day) - 1.0,
            "adx_14": compute_adx_14(df).to_numpy(),
            "volume_zscore_20": compute_volume_zscore_20(df).to_numpy(),
            "rsi_14": compute_rsi_14(df).to_numpy(),
            "hour": pd.to_datetime(df["timestamp"], utc=True).dt.hour.to_numpy(),
        },
        index=df.index,
    )


def filter_pass(inputs: pd.DataFrame, direction: pd.Series) -> pd.DataFrame:
    """Czy sygnał o kierunku `direction` (±1) przechodzi każdy z filtrów; NaN → nie przechodzi."""
    d = direction
    return pd.DataFrame(
        {
            "trend28": np.sign(inputs["ret28"]) == d,
            "adx25": inputs["adx_14"] > ADX_MIN,
            "wolumen": inputs["volume_zscore_20"] > 0,
            "sesja_usa": inputs["hour"].isin(list(US_HOURS)),
            "rsi50": ((d > 0) & (inputs["rsi_14"] > RSI_MID))
            | ((d < 0) & (inputs["rsi_14"] < RSI_MID)),
        },
        index=inputs.index,
    )


def compute_mx2_rules(df: pd.DataFrame, candles_per_day: int = 24) -> pd.DataFrame:
    """Sygnał MX1 (`rule_macd_ema_cross`) i pięć jego wersji z filtrem (`rule_mx2_<filtr>`)."""
    base = compute_mx_rules(df)["rule_macd_ema_cross"]
    ok = filter_pass(compute_filter_inputs(df, candles_per_day), base)
    out = {"rule_macd_ema_cross": base}
    for name in FILTERS:
        out[f"rule_mx2_{name}"] = base.where(ok[name] & (base != 0), 0.0).rename(f"rule_mx2_{name}")
    return pd.DataFrame(out, index=df.index)
