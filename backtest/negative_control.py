"""
negative_control.py — KONTROLA NEGATYWNA przyrządu: dane syntetyczne, w których z definicji NIE MA
żadnej informacji o przyszłym kierunku, a mimo to wyglądają jak krypto (grube ogony, grupowanie
zmienności, wspólny czynnik rynkowy). Silnik uruchomiony na takich danych musi dać wynik ≈ 0
w granicach szumu; wyraźny „zysk” oznacza błąd w przyrządzie (zajrzenie w przyszłość, zła
rachuba zwrotów), a nie sygnał. Uzupełnia kontrolę POZYTYWNĄ K1 (wyrocznia ze znanym sygnałem).

Źródło wytycznej: przegląd projektu SIGMA (`docs/rag/Repo lessons i sigma — co przydatne dla
alpha.md`, wytyczna 2) — tam brak takiej kontroli pozwolił bramce AUC 0,84 przejść na etykiecie
liczonej z PRZYSZŁEGO wygładzonego wskaźnika. Procedura: `docs/skills/bramki-jakosci.md` A6.

Model zwrotów dziennych (monety i = 1..N, dni t):
    r_it = σ_it · (√ρ · f_t + √(1 − ρ) · e_it),   f_t, e_it ~ t-Student(df) / sd (wariancja 1)
    σ²_it = ω + α · (r_{i,t−1})² + β · σ²_{i,t−1}   (GARCH(1,1); średnia zmienność = `daily_vol`)
Średnia zwrotu = 0, brak autokorelacji zwrotów (autokorelacja jest tylko w ich KWADRATACH).
Testy: `tests/test_negative_control.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _t_unit(rng, df: float, size) -> np.ndarray:
    """Losowania t-Studenta przeskalowane do wariancji 1 (df > 2)."""
    return rng.standard_t(df, size=size) / np.sqrt(df / (df - 2.0))


def synthetic_returns(
    n_days: int,
    n_coins: int,
    seed: int = 0,
    df: float = 3.0,
    rho: float = 0.5,
    daily_vol: float = 0.04,
    garch: tuple[float, float] = (0.08, 0.90),
    start: str = "2021-01-01",
) -> pd.DataFrame:
    """Panel dziennych zwrotów prostych bez informacji o przyszłości (opis modelu w docstringu modułu)."""
    if df <= 2:
        raise ValueError("df musi być > 2 (skończona wariancja)")
    alpha, beta = garch
    if alpha < 0 or beta < 0 or alpha + beta >= 1:
        raise ValueError("GARCH wymaga alpha, beta ≥ 0 i alpha + beta < 1")
    rng = np.random.default_rng(seed)
    f = _t_unit(rng, df, n_days)
    e = _t_unit(rng, df, (n_days, n_coins))
    z = np.sqrt(rho) * f[:, None] + np.sqrt(1.0 - rho) * e
    var_bar = daily_vol**2
    omega = var_bar * (1.0 - alpha - beta)
    r = np.empty((n_days, n_coins))
    var = np.full(n_coins, var_bar)
    for t in range(n_days):
        r[t] = np.sqrt(var) * z[t]
        var = omega + alpha * r[t] ** 2 + beta * var
    r = np.clip(r, -0.95, None)  # cena nie spada do zera jednego dnia
    idx = pd.date_range(start, periods=n_days, freq="D", tz="UTC")
    cols = [f"C{i:02d}USDT" for i in range(n_coins)]
    return pd.DataFrame(r, index=idx, columns=cols)


def synthetic_ohlc(
    returns: pd.DataFrame, seed: int = 0, start_price: float = 100.0
) -> dict[str, pd.DataFrame]:
    """
    Panele open/high/low/close z dziennych zwrotów: open = poprzednie close, high/low wysunięte
    poza max/min(open, close) o losową część dziennej zmienności (|N(0,1)| · 0,5 · |r| + mały luz).
    """
    rng = np.random.default_rng(seed + 10_000)
    close = start_price * (1.0 + returns).cumprod()
    open_ = close.shift(1)
    open_.iloc[0] = start_price
    top = np.maximum(open_, close)
    bot = np.minimum(open_, close)
    scale = 0.5 * returns.abs() + 0.002
    up = np.abs(rng.standard_normal(returns.shape)) * scale
    dn = np.abs(rng.standard_normal(returns.shape)) * scale
    high = top * (1.0 + up)
    low = bot * np.clip(1.0 - dn, 0.05, None)
    return {"open": open_, "high": high, "low": low, "close": close}


def all_members(
    close: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> dict[pd.Timestamp, list[str]]:
    """Koszyk miesięczny = wszystkie monety (syntetyczne dane nie mają przeżywalności)."""
    months = pd.date_range(start.normalize(), end, freq="MS", tz="UTC")
    if len(months) == 0 or months[0] > start:
        months = months.insert(0, start)
    return {m: list(close.columns) for m in months}


def autocorr(x: np.ndarray, lag: int = 1) -> float:
    """Autokorelacja rzędu `lag` (średnia z całej próby)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    return float((x[lag:] * x[:-lag]).sum() / (x * x).sum())


def excess_kurtosis(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    return float((x**4).mean() / (x**2).mean() ** 2 - 3.0)
