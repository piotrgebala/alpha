"""
rebalance_premium.py — R1: premia rebalansowa koszyka równych wag (rodzina B2 katalogu).

Runda R1 (2026-09-23, runs/2026-09-23_r1-premia-rebalansowa/README.md): inny target niż kierunek.
Ten sam koszyk (skład wybierany point-in-time na początku miesiąca) w dwóch wersjach:
A — równe wagi przywracane CODZIENNIE, B — równe wagi na starcie miesiąca, potem trzymanie.
Premia dnia = r_A − r_B − opłata × obrót A. Czyste funkcje (bez sieci, bez configu), testowalne
niezależnie od skryptu rundy:

    r_A,t = (1/N) Σ_i r_it
    r_B,t = Σ_i w_i,t−1 r_it ;  w_i,t = w_i,t−1 (1 + r_it) / (1 + r_B,t) ;  w_i,start = 1/N
    turnover_t = Σ_i |(1 + r_it) / (N (1 + r_A,t)) − 1/N|
    premium_net_t = r_A,t − r_B,t − fee · turnover_t

Wycofany członek (brak ceny po ostatnim notowaniu) = gotówka: zwrot 0 w OBU wersjach do końca
miesiąca. Obrót na starcie miesiąca (zmiana składu) jest wspólny dla A i B i się skraca.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from data.fetch_universe import STABLE_BASES

TOP_N = 20  # P2, poprawka 1 użytkownika: 20 największych po obrocie
VOLUME_LOOKBACK_DAYS = 30
MIN_HISTORY_DAYS = 30
QUOTE = "USDT"


def load_universe(universe_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Panele (close, quote_volume): indeks = dzień UTC (open_time), kolumny = symbole."""
    frames = []
    for path in sorted(Path(universe_dir).glob("*_1d.parquet")):
        df = pd.read_parquet(path)
        if df.empty:
            continue
        df = df[["open_time", "close", "quote_volume"]].copy()
        df["symbol"] = path.name[: -len("_1d.parquet")]
        frames.append(df)
    if not frames:
        raise ValueError(f"brak plików *_1d.parquet w {universe_dir}")
    panel = pd.concat(frames, ignore_index=True)
    panel["open_time"] = pd.to_datetime(panel["open_time"], utc=True)
    if panel.duplicated(["symbol", "open_time"]).any():
        raise ValueError("duplikaty (symbol, dzień) w uniwersum")
    close = panel.pivot(index="open_time", columns="symbol", values="close").sort_index()
    volume = panel.pivot(index="open_time", columns="symbol", values="quote_volume").sort_index()
    return close, volume


def eligible_symbols(symbols: list[str], stable_bases: frozenset[str] = STABLE_BASES) -> list[str]:
    """Jak P2 `select_universe`: `*USDT`, baza niepusta i nie-stablecoin (TRADIFI odsiane przy pobraniu)."""
    out = []
    for sym in symbols:
        if not sym.endswith(QUOTE):
            continue
        base = sym[: -len(QUOTE)]
        if base and base not in stable_bases:
            out.append(sym)
    return sorted(out)


def monthly_members(
    volume: pd.DataFrame,
    month_starts: list[pd.Timestamp],
    top_n: int = TOP_N,
    lookback_days: int = VOLUME_LOOKBACK_DAYS,
    min_history_days: int = MIN_HISTORY_DAYS,
) -> dict[pd.Timestamp, list[str]]:
    """
    Skład koszyka na początek każdego miesiąca WYŁĄCZNIE z danych sprzed tego dnia:
    kandydaci z ≥ `min_history_days` notowaniami w oknie `lookback_days` przed `m`, top-`top_n`
    po średnim obrocie w tym oknie (remis → alfabetycznie). Fail loud, gdy kandydatów < top_n.
    """
    cols = eligible_symbols(list(volume.columns))
    members: dict[pd.Timestamp, list[str]] = {}
    for m in month_starts:
        window = volume.loc[
            (volume.index >= m - pd.Timedelta(days=lookback_days)) & (volume.index < m), cols
        ]
        ok = window.notna().sum() >= min_history_days
        mean_vol = window.mean()[ok].dropna()
        if len(mean_vol) < top_n:
            raise ValueError(f"{m.date()}: tylko {len(mean_vol)} kandydatów < top_n={top_n}")
        ranked = sorted(mean_vol.items(), key=lambda kv: (-kv[1], kv[0]))
        members[m] = sorted(s for s, _ in ranked[:top_n])
    return members


def _month_days(
    index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp | None
) -> pd.DatetimeIndex:
    mask = index >= start
    if end is not None:
        mask &= index < end
    return index[mask]


def daily_premium(
    close: pd.DataFrame, members: dict[pd.Timestamp, list[str]], fee: float
) -> pd.DataFrame:
    """
    Per dzień: r_rebal (A), r_bh (B), turnover, cost, premium_gross, premium_net, n_active.
    Wycofany członek (NaN po ostatniej cenie) = zwrot 0 w obu wersjach (gotówka).
    Dni pierwszego miesiąca zaczynają się od jego pierwszego dnia (zwrot względem dnia poprzedniego).
    """
    returns = close.pct_change()
    starts = sorted(members)
    rows = []
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else None
        cols = members[start]
        n = len(cols)
        raw = returns.loc[_month_days(returns.index, start, end), cols]
        r = raw.fillna(0.0)  # wycofany = gotówka (zwrot 0) w obu wersjach
        active = raw.notna().sum(axis=1)
        w = np.full(n, 1.0 / n)
        for day, row in r.iterrows():
            ri = row.to_numpy(dtype=float)
            r_a = float(ri.mean())
            r_b = float(np.dot(w, ri))
            drifted_a = (1.0 + ri) / (n * (1.0 + r_a))
            turnover = float(np.abs(drifted_a - 1.0 / n).sum())
            rows.append(
                {
                    "date": day,
                    "month": start,
                    "r_rebal": r_a,
                    "r_bh": r_b,
                    "turnover": turnover,
                    "cost": fee * turnover,
                    "premium_gross": r_a - r_b,
                    "premium_net": r_a - r_b - fee * turnover,
                    "n_active": int(active.loc[day]),
                }
            )
            w = w * (1.0 + ri) / (1.0 + r_b)
    out = pd.DataFrame(rows)
    return out


def cumulative_growth(daily_returns: pd.Series) -> float:
    """Skumulowany zwrot (ułamek) z szeregu dziennych zwrotów prostych."""
    return float(np.prod(1.0 + daily_returns.to_numpy(dtype=float)) - 1.0)
