"""
carry_hedged.py — C1: ekonomia cash-and-carry (long spot + short perpetual) per okres funding.

Runda C1 (2026-09-23, runs/2026-09-23_c1-cash-and-carry/README.md): inny target niż kierunek —
przepływ funding zbierany bez ekspozycji kierunkowej. Czyste funkcje (bez sieci, bez configu),
żeby definicja P&L z pre-rejestracji była testowalna niezależnie od skryptu rundy:

    pnl_t = s_t · [ f_{t+1} + (spot_{t+1}/spot_t − 1) − (perp_{t+1}/perp_t − 1) ]
            − koszt · 1[s_t = 1, s_{t−1} = 0] − koszt · 1[s_t = 0, s_{t−1} = 1]
            − koszt · 1[t ostatni, s_t = 1]                     (zamknięcie na końcu próby)

Konwencje: znacznik świecy 8h = OTWARCIE; stawka rozliczona o T_{t+1} (zamknięcie świecy t)
jest fundingiem OTRZYMANYM w okresie t przez short perp, gdy > 0 (znak Binance: dodatnia =
long płaci short). Stan s_t ustalany o T_t z informacji znanych o T_t.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from agents.labeling import effective_sample_size

PERIODS_PER_YEAR = 3 * 365  # rozliczenia co 8 h
CAPITAL_PER_NOTIONAL = 2.0  # nominał spot (1,0) + depozyt pod short perp przyjęty 1,0 (dźwignia 1×)


@dataclass(frozen=True)
class CarryCosts:
    """Opłaty za stronę (ułamki nominału). Wejście i wyjście = obie nogi taker + poślizg na każdej."""

    spot_fee: float
    perp_fee: float
    slippage: float

    @property
    def switch_cost(self) -> float:
        return self.spot_fee + self.slippage + self.perp_fee + self.slippage


def align_carry_frame(
    spot: pd.DataFrame, perp: pd.DataFrame, funding: pd.DataFrame
) -> pd.DataFrame:
    """
    Jedna ramka per okres t (świeca 8h otwarta o T_t): `r_spot`, `r_perp` = zmiana zamknięcia
    świecy t względem świecy t−1 (cena o T_{t+1} / cena o T_t − 1), `f_now` = stawka rozliczona
    o T_t (znana przy decyzji), `f_next` = stawka rozliczona o T_{t+1} (otrzymana w okresie t),
    `basis` = (perp − spot)/spot na zamknięciu świecy t. Pierwszy okres (brak r) i ostatni
    (brak f_next) odpadają. Zbiory znaczników muszą być identyczne — fail loud.
    """
    for name, df, col in (
        ("spot", spot, "close"),
        ("perp", perp, "close"),
        ("funding", funding, "funding_rate"),
    ):
        if "timestamp" not in df.columns or col not in df.columns:
            raise ValueError(f"{name}: wymagane kolumny timestamp i {col}")
    s = spot[["timestamp", "close"]].rename(columns={"close": "spot_close"})
    p = perp[["timestamp", "close"]].rename(columns={"close": "perp_close"})
    f = funding[["timestamp", "funding_rate"]].rename(columns={"funding_rate": "f_now"})
    if not (set(s["timestamp"]) == set(p["timestamp"]) == set(f["timestamp"])):
        raise ValueError(
            "znaczniki spot / perp / funding nie są identyczne — wyrównaj dane przed pomiarem"
        )
    frame = s.merge(p, on="timestamp", validate="one_to_one").merge(
        f, on="timestamp", validate="one_to_one"
    )
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame["r_spot"] = frame["spot_close"].pct_change()
    frame["r_perp"] = frame["perp_close"].pct_change()
    frame["f_next"] = frame["f_now"].shift(-1)
    frame["basis"] = (frame["perp_close"] - frame["spot_close"]) / frame["spot_close"]
    return frame.dropna(subset=["r_spot", "r_perp", "f_next"]).reset_index(drop=True)


def state_always_on(frame: pd.DataFrame) -> pd.Series:
    """C1a: pozycja przez całą próbę."""
    return pd.Series(1.0, index=frame.index, name="state")


def state_after_positive_funding(frame: pd.DataFrame) -> pd.Series:
    """C1b: w pozycji w okresie t, gdy stawka rozliczona o T_t (znana przy decyzji) była dodatnia."""
    return (frame["f_now"] > 0).astype(float).rename("state")


def hedged_carry_pnl(frame: pd.DataFrame, state: pd.Series, costs: CarryCosts) -> pd.DataFrame:
    """P&L per okres (ułamek nominału) rozbity na funding, hedge (zmiana bazy) i koszty."""
    s = state.astype(float).reset_index(drop=True)
    if len(s) != len(frame) or not set(s.unique()) <= {0.0, 1.0}:
        raise ValueError("state musi mieć długość ramki i wartości {0, 1}")
    prev = s.shift(1, fill_value=0.0)
    entries = (s == 1.0) & (prev == 0.0)
    exits = (s == 0.0) & (prev == 1.0)
    cost = costs.switch_cost * (entries.astype(float) + exits.astype(float))
    if len(s) and s.iloc[-1] == 1.0:
        cost.iloc[-1] += costs.switch_cost  # zamknięcie pozycji na końcu próby
    out = pd.DataFrame(
        {
            "timestamp": frame["timestamp"].to_numpy(),
            "state": s.to_numpy(),
            "funding_received": (s * frame["f_next"]).to_numpy(),
            "hedge": (s * (frame["r_spot"] - frame["r_perp"])).to_numpy(),
            "cost": cost.to_numpy(),
        }
    )
    out["pnl"] = out["funding_received"] + out["hedge"] - out["cost"]
    out["n_switches"] = (entries | exits).astype(int).to_numpy()
    return out


def summarize_pnl(pnl: pd.Series, z: float = 1.959964) -> dict:
    """Średni P&L per okres z CI (se z N_eff ≤ n), t, t_neff, annualizacja na nominale i kapitale."""
    x = pnl.dropna().astype(float)
    n = len(x)
    if n < 2:
        return {"n": n}
    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    se = sd / np.sqrt(n)
    n_eff = min(float(effective_sample_size(x)["n_eff"]), float(n))
    se_neff = sd / np.sqrt(n_eff)
    t = mean / se if se > 0 else float("nan")
    t_neff = mean / se_neff if se_neff > 0 else float("nan")
    return {
        "n": n,
        "mean": mean,
        "median": float(x.median()),
        "sd": sd,
        "se": se,
        "n_eff": n_eff,
        "se_neff": se_neff,
        "t": t,
        "t_neff": t_neff,
        "ci_low": mean - z * se_neff,
        "ci_high": mean + z * se_neff,
        "annual_notional": mean * PERIODS_PER_YEAR,
        "annual_notional_ci": (
            (mean - z * se_neff) * PERIODS_PER_YEAR,
            (mean + z * se_neff) * PERIODS_PER_YEAR,
        ),
        "annual_capital": mean * PERIODS_PER_YEAR / CAPITAL_PER_NOTIONAL,
        "annual_capital_ci": (
            (mean - z * se_neff) * PERIODS_PER_YEAR / CAPITAL_PER_NOTIONAL,
            (mean + z * se_neff) * PERIODS_PER_YEAR / CAPITAL_PER_NOTIONAL,
        ),
        "total": float(x.sum()),
    }


def max_drawdown(pnl: pd.Series) -> float:
    """Największe obsunięcie skumulowanego P&L (ułamek nominału, liczba dodatnia)."""
    cum = pnl.cumsum()
    return float((cum.cummax() - cum).max())


def max_runup(price: pd.Series, periods: int) -> float:
    """Największy wzrost ceny w oknie `periods` okresów (ryzyko nogi short bez uzupełnień depozytu)."""
    return float((price.rolling(periods).max() / price.shift(periods) - 1.0).max())
