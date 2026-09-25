"""
ta_macd.py — runda MX1 (decyzja użytkownika 2026-09-25): MACD 12/26/9 jako potwierdzenie przecięcia
EMA 10/30 („najpierw przecięcie MACD, potem przecięcie EMA”). Osobny moduł, żeby NIE zmieniać
`agents.ta_rules.TA_FEATURE_FUNCTIONS` ani `EVENT_RULES` — zamrożona runda A2 z nich korzysta.

Definicje (pre-rejestracja `runs/2026-09-25_mx1-macd-ema-1h/README.md`; parametry podręcznikowe,
jeden zestaw, bez wariantów):
- linia MACD = EMA12(close) − EMA26(close); linia sygnału = EMA9(linii MACD); histogram = linia
  MACD − linia sygnału (znak = po której stronie linii sygnału jest MACD). EMA jak
  `ta_rules.compute_ma_state`: pandas `ewm(span, adjust=False, min_periods=span)`.
- sygnał w świecy t: świeże przecięcie EMA 10/30 (`ma_cross_age == 0`) w kierunku
  d = znak(EMA10 − EMA30) ORAZ histogram MACD ma znak d w świecy t−1 i w świecy t — MACD przeciął
  linię sygnału w kierunku d WCZEŚNIEJ (najpóźniej w t−1) i do świecy t nie zawrócił. Przecięcie
  MACD w tej samej świecy co EMA nie jest „wcześniejsze” → 0. Tylko dane ≤ t.
Regułę liczy się na CIĄGŁYM szeregu świec (przed pipeline'em), bo `shift(1)` ma oznaczać poprzednią
świecę, a nie poprzedni wiersz po odsianiu.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from agents.ta_rules import compute_ma_cross_age, compute_ma_state, rule_ma_cross

MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9


def _ema(x: pd.Series, span: int) -> pd.Series:
    return x.ewm(span=span, adjust=False, min_periods=span).mean()


def compute_macd_hist(
    df: pd.DataFrame, fast: int = MACD_FAST, slow: int = MACD_SLOW, signal: int = MACD_SIGNAL
) -> pd.Series:
    """(linia MACD − linia sygnału) / close; NaN w rozbiegu."""
    macd = _ema(df["close"], fast) - _ema(df["close"], slow)
    sig = _ema(macd, signal)
    return ((macd - sig) / df["close"]).rename("macd_hist")


def compute_mx_features(df: pd.DataFrame) -> pd.DataFrame:
    """Stan i wiek przecięcia EMA 10/30 (jak A2) + histogram MACD 12/26/9."""
    return pd.DataFrame(
        {
            "ma_state": compute_ma_state(df),
            "ma_cross_age": compute_ma_cross_age(df),
            "macd_hist": compute_macd_hist(df),
        },
        index=df.index,
    )


def rule_macd_ema_cross(f: pd.DataFrame) -> pd.Series:
    """ZDARZENIE: przecięcie EMA 10/30 potwierdzone WCZEŚNIEJSZYM przecięciem MACD w tym samym kierunku."""
    ema = rule_ma_cross(f)
    h = np.sign(f["macd_hist"])
    ok = (ema != 0) & (h == ema) & (h.shift(1) == ema)
    return ema.where(ok, 0.0).rename("rule_macd_ema_cross")


def compute_mx_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Kolumny reguł na ciągłym szeregu: `rule_ma_cross` (odniesienie) i `rule_macd_ema_cross` (MX1)."""
    f = compute_mx_features(df)
    return pd.DataFrame(
        {"rule_ma_cross": rule_ma_cross(f), "rule_macd_ema_cross": rule_macd_ema_cross(f)},
        index=df.index,
    )
