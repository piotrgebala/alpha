"""
carry_product.py — analiza PRODUKTU cash-and-carry (runda D1): depozyt i likwidacja krótkiej
nogi, wariant COIN-M (inverse perp z zabezpieczeniem w BTC), basis kontraktów kwartalnych,
porównanie ze stopą T-bill.

Czyste funkcje (testy: `tests/test_carry_product.py`). Żadna nie zawiera reguły wejścia/wyjścia
poza „zawsze w pozycji" (C1a) — to analiza ryzyka i konstrukcji wyniku dodatniego C1, nie test
hipotezy. Przyrząd statystyczny (średnia, CI, N_eff) pozostaje w `backtest/carry_hedged.py`.

Konwencje: ceny i stawki jako `pd.Series` rosnąco po czasie; ułamki nominału (0,01 = 1 %);
rozliczenia co 8h → `PERIODS_PER_DAY = 3`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PERIODS_PER_DAY = 3
DAYS_PER_YEAR = 365.0
MAINTENANCE_MARGIN = 0.005  # Binance BTCUSDT USDT-M, pierwszy próg (0,4 %) z zapasem
LIQUIDATION_FEE = 0.0125  # opłata likwidacyjna (górna stawka Binance USDT-M), ułamek nominału
PERP_REENTRY_COST = 0.0007  # ponowne wejście samej nogi perp: taker 0,05 % + poślizg 0,02 %
MARGIN_GRID = (0.25, 0.5, 1.0, 1.5)
RESET_DAYS_GRID = (None, 30, 7, 1)
RUNUP_HORIZONS_DAYS = (1, 7, 30, 90)
MIN_DAYS_TO_EXPIRY = 7.0
DELIVERY_OFFSET = pd.Timedelta(hours=8)  # kontrakty kwartalne Binance rozliczają się 08:00 UTC


# --------------------------------------------------------------------------------------
# Q1 — run-up i symulacja depozytu
# --------------------------------------------------------------------------------------


def forward_runup(price: pd.Series, periods: int) -> pd.Series:
    """Największy wzrost ceny w ciągu następnych `periods` okresów: max_{1..k} P_{t+k}/P_t − 1."""
    p = price.astype(float).reset_index(drop=True)
    fwd_max = p[::-1].rolling(periods, min_periods=1).max()[::-1].shift(-1)
    if len(p) < 2:
        return pd.Series(dtype=float)
    return (fwd_max / p - 1.0).clip(lower=0.0).iloc[:-1]  # brak wzrostu = 0, nie ujemny


def max_runup_table(price: pd.Series, horizons_days=RUNUP_HORIZONS_DAYS) -> pd.DataFrame:
    """Per horyzont: max, p99, p95 rozkładu run-upu w oknie oraz udział okien z run-upem > 50 % i > 100 %."""
    rows = []
    for h in horizons_days:
        r = forward_runup(price, h * PERIODS_PER_DAY).dropna()
        rows.append(
            {
                "horizon_days": h,
                "max": float(r.max()) if len(r) else np.nan,
                "p99": float(r.quantile(0.99)) if len(r) else np.nan,
                "p95": float(r.quantile(0.95)) if len(r) else np.nan,
                "share_gt_50pct": float((r > 0.5).mean()) if len(r) else np.nan,
                "share_gt_100pct": float((r > 1.0).mean()) if len(r) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def liquidation_events(
    price: pd.Series,
    margin: float,
    reset_periods: int | None,
    maintenance: float = MAINTENANCE_MARGIN,
) -> dict:
    """
    Short perp z depozytem `margin` nominału; likwidacja, gdy P_t/P_ref − 1 ≥ margin − maintenance.

    `P_ref` = cena przy wejściu / ostatnim uzupełnieniu depozytu / ostatniej likwidacji. Uzupełnienie
    co `reset_periods` okresów (None = nigdy) ustawia `P_ref = P_t`. Po likwidacji pozycja jest
    odtwarzana po `P_t` (koszt LIQUIDATION_FEE + PERP_REENTRY_COST nominału).

    Returns: n_liquidations, liquidation_cost (ułamek nominału), max_usage (największy wzrost od
    P_ref, ułamek nominału), n_resets, rebalance_turnover (Σ|P_t/P_ref − 1| przy każdym
    uzupełnieniu i likwidacji = ułamek nominału przycinany na OBU nogach, żeby wrócić do
    nominału USD sprzed ruchu — Poprawka 1: bez tego siatka pomijała koszt uzupełnień).
    """
    if margin <= maintenance:
        raise ValueError("depozyt musi przekraczać maintenance margin")
    p = price.astype(float).to_numpy()
    if len(p) == 0:
        return {
            "n_liquidations": 0,
            "liquidation_cost": 0.0,
            "max_usage": 0.0,
            "n_resets": 0,
            "rebalance_turnover": 0.0,
        }
    threshold = margin - maintenance
    p_ref = p[0]
    n_liq = n_resets = 0
    max_usage = 0.0
    turnover = 0.0
    for t in range(1, len(p)):
        if reset_periods is not None and t % reset_periods == 0:
            turnover += abs(p[t] / p_ref - 1.0)
            p_ref = p[t]
            n_resets += 1
        usage = p[t] / p_ref - 1.0
        max_usage = max(max_usage, usage)
        if usage >= threshold:
            n_liq += 1
            turnover += abs(usage)
            p_ref = p[t]
    return {
        "n_liquidations": n_liq,
        "liquidation_cost": n_liq * (LIQUIDATION_FEE + PERP_REENTRY_COST),
        "max_usage": max_usage,
        "n_resets": n_resets,
        "rebalance_turnover": turnover,
    }


def margin_grid(
    price: pd.Series,
    annual_notional_return: float,
    margins=MARGIN_GRID,
    reset_days=RESET_DAYS_GRID,
    years: float | None = None,
    switch_cost: float = 0.0,
) -> pd.DataFrame:
    """
    Siatka depozyt × częstość uzupełnień: likwidacje, ich koszt, wykorzystanie depozytu, koszt
    uzupełnień (obrót × `switch_cost`; Poprawka 1) i zwrot C1a na kapitale (1 + M) po odjęciu
    obu kosztów (rozłożonych na `years` lat).
    """
    if years is None:
        years = len(price) / (PERIODS_PER_DAY * DAYS_PER_YEAR)
    rows = []
    for m in margins:
        for rd in reset_days:
            ev = liquidation_events(price, m, None if rd is None else rd * PERIODS_PER_DAY)
            annual_liq_cost = ev["liquidation_cost"] / years if years > 0 else np.nan
            annual_reb_cost = (
                ev["rebalance_turnover"] * switch_cost / years if years > 0 else np.nan
            )
            rows.append(
                {
                    "margin": m,
                    "reset_days": rd,
                    "n_liquidations": ev["n_liquidations"],
                    "n_resets": ev["n_resets"],
                    "max_usage": ev["max_usage"],
                    "annual_liq_cost": annual_liq_cost,
                    "rebalance_turnover": ev["rebalance_turnover"],
                    "annual_rebalance_cost": annual_reb_cost,
                    "annual_on_capital": (
                        annual_notional_return - annual_liq_cost - annual_reb_cost
                    )
                    / (1.0 + m),
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Q2 — COIN-M inverse perp z zabezpieczeniem w BTC
# --------------------------------------------------------------------------------------


def inverse_position_usd_value(price: pd.Series, entry_price: float) -> pd.Series:
    """
    Wartość USD pozycji „1 BTC + short N = P₀ USD kontraktów inverse": P + N(1/P − 1/P₀)·P = P₀.
    Tożsamość algebraiczna — stała niezależnie od ścieżki ceny (brak likwidacji przy 1×).
    """
    p = price.astype(float)
    return p + entry_price * (1.0 / p - 1.0 / entry_price) * p


def inverse_carry_pnl(funding: pd.DataFrame, switch_cost: float) -> pd.DataFrame:
    """
    P&L per rozliczenie (ułamek nominału USD) dla „zawsze w pozycji" na COIN-M: funding
    otrzymany w BTC × cena = stawka × nominał USD; koszt wejścia w pierwszym i wyjścia w ostatnim
    okresie. Bez nogi hedge (wartość USD stała — `inverse_position_usd_value`).
    """
    if "timestamp" not in funding.columns or "funding_rate" not in funding.columns:
        raise ValueError("funding: wymagane kolumny timestamp i funding_rate")
    f = funding.sort_values("timestamp").reset_index(drop=True)
    out = pd.DataFrame(
        {
            "timestamp": f["timestamp"].to_numpy(),
            "funding_received": f["funding_rate"].astype(float).to_numpy(),
            "cost": 0.0,
        }
    )
    if len(out):
        out.loc[0, "cost"] += switch_cost
        out.loc[len(out) - 1, "cost"] += switch_cost
    out["pnl"] = out["funding_received"] - out["cost"]
    return out


def floor_to_grid(ts: pd.Series, freq: str = "8h") -> pd.Series:
    """Znaczniki z jitterem ms (funding COIN-M) → pełna siatka."""
    return pd.to_datetime(ts, utc=True).dt.floor(freq)


# --------------------------------------------------------------------------------------
# Q3 — basis kontraktów kwartalnych
# --------------------------------------------------------------------------------------


def annualized_basis(
    dated: pd.DataFrame, spot: pd.DataFrame, min_days: float = MIN_DAYS_TO_EXPIRY
) -> pd.DataFrame:
    """
    Per świeca kontraktu (przed wygaśnięciem, z wolumenem): basis = (F − S)/S i annualizacja
    ×365/dni_do_wygaśnięcia. `S` = spot na ten sam `open_time` (inner join, bez wypełniania).

    Returns: contract, expiry, open_time, days_to_expiry, F, S, basis, annualized — rosnąco.
    """
    need = {"contract", "expiry", "open_time", "close", "volume"}
    if not need <= set(dated.columns):
        raise ValueError(f"dated: brak kolumn {sorted(need - set(dated.columns))}")
    d = dated.copy()
    d["delivery"] = pd.to_datetime(d["expiry"], utc=True) + DELIVERY_OFFSET
    d = d[(d["open_time"] < d["delivery"]) & (d["volume"] > 0)]
    s = spot[["timestamp", "close"]].rename(columns={"timestamp": "open_time", "close": "S"})
    j = d.merge(s, on="open_time", how="inner").rename(columns={"close": "F"})
    j["days_to_expiry"] = (j["delivery"] - j["open_time"]).dt.total_seconds() / 86_400.0
    j = j[j["days_to_expiry"] >= min_days]
    j["basis"] = (j["F"] - j["S"]) / j["S"]
    j["annualized"] = j["basis"] * DAYS_PER_YEAR / j["days_to_expiry"]
    cols = ["contract", "expiry", "open_time", "days_to_expiry", "F", "S", "basis", "annualized"]
    return j[cols].sort_values(["open_time", "days_to_expiry"]).reset_index(drop=True)


def front_contract(basis: pd.DataFrame) -> pd.DataFrame:
    """Dla każdego `open_time` kontrakt o najkrótszym czasie do wygaśnięcia (już ≥ min_days)."""
    return (
        basis.sort_values(["open_time", "days_to_expiry"])
        .drop_duplicates("open_time", keep="first")
        .reset_index(drop=True)
    )


def realized_funding_window(funding: pd.DataFrame, start, end) -> float:
    """Suma stawek funding rozliczonych w `(start, end]` (co short perp zebrałby w tym oknie)."""
    f = funding
    mask = (f["timestamp"] > start) & (f["timestamp"] <= end)
    return float(f.loc[mask, "funding_rate"].sum())


def basis_vs_funding(
    basis: pd.DataFrame, funding: pd.DataFrame, entry_days=(90, 60, 30), tol_days: float = 0.5
) -> pd.DataFrame:
    """
    Dla każdego kontraktu i wejścia `d` dni przed wygaśnięciem (świeca NAJBLIŻEJ `d`, o ile
    |days_to_expiry − d| ≤ tol): baza zamknięta na wejściu vs funding USDT-M zrealizowany do
    wygaśnięcia — obie wielkości w ułamku nominału ORAZ annualizowane.
    """
    rows = []
    for contract, g in basis.groupby("contract", sort=False):
        delivery = pd.to_datetime(g["expiry"].iloc[0], utc=True) + DELIVERY_OFFSET
        for d in entry_days:
            cand = g[(g["days_to_expiry"] - d).abs() <= tol_days]
            if cand.empty:
                continue
            row = cand.iloc[(cand["days_to_expiry"] - d).abs().argsort().iloc[0]]  # najbliżej d dni
            realized = realized_funding_window(funding, row["open_time"], delivery)
            days = float(row["days_to_expiry"])
            rows.append(
                {
                    "contract": contract,
                    "entry_days": d,
                    "open_time": row["open_time"],
                    "basis_locked": float(row["basis"]),
                    "basis_annualized": float(row["basis"]) * DAYS_PER_YEAR / days,
                    "funding_realized": realized,
                    "funding_annualized": realized * DAYS_PER_YEAR / days,
                }
            )
    out = pd.DataFrame(rows)
    if len(out):
        out["diff_annualized"] = out["basis_annualized"] - out["funding_annualized"]
    return out


# --------------------------------------------------------------------------------------
# Q4 — tabele roczne
# --------------------------------------------------------------------------------------


def yearly_sum(df: pd.DataFrame, value_col: str, time_col: str = "timestamp") -> pd.Series:
    """Suma `value_col` per rok kalendarzowy (UTC)."""
    years = pd.to_datetime(df[time_col], utc=True).dt.year
    return df.groupby(years)[value_col].sum()


def yearly_mean(df: pd.DataFrame, value_col: str, time_col: str) -> pd.Series:
    """Średnia `value_col` per rok (NaN pomijane) — np. T-bill z dni roboczych."""
    years = pd.to_datetime(df[time_col], utc=True).dt.year
    return df.groupby(years)[value_col].mean()


def yearly_fraction(df: pd.DataFrame, time_col: str = "timestamp") -> pd.Series:
    """Ułamek roku pokryty obserwacjami (do annualizacji lat niepełnych, np. 2026 H1)."""
    ts = pd.to_datetime(df[time_col], utc=True)
    years = ts.dt.year
    counts = ts.groupby(years).count()
    return counts / (PERIODS_PER_DAY * DAYS_PER_YEAR)
