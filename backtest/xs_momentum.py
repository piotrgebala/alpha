"""
xs_momentum.py — momentum przekrojowe (runda X1, rodzina B1): ranking uniwersum point-in-time
po zwrocie z ostatnich `SIGNAL_LOOKBACK_DAYS`, long top-`LEG_SIZE` / short bottom-`LEG_SIZE`,
trzymanie `HOLD_DAYS` dni (buy-and-hold w oknie), koszty obrotu obu nóg i funding per symbol.

Czyste funkcje (testy: `tests/test_xs_momentum.py`). Konwencje:
- `close`: panel dzienny (indeks = dzień UTC, kolumny = symbole) z `rebalance_premium.load_universe`;
- sygnał na dzień `t` używa WYŁĄCZNIE zamknięć ≤ `t`; pozycja wchodzi po zamknięciu `t`,
  pierwszy zwrot pochodzi z dnia `t + 1` (brak lookaheadu — test);
- kapitał = 1 = 0,5 noga long + 0,5 noga short; zwrot portfela = 0,5·(r_long − r_short);
- obrót w jednostkach kapitału (pełna wymiana obu nóg = 2,0), koszt = `fee` × obrót;
- funding dzienny = suma rozliczeń danego dnia; long PŁACI, short OTRZYMUJE (znak stawki);
- wycofany członek (brak ceny) = gotówka (zwrot 0), jak w R1;
- `legs_fn(signal_row, members, rng)` → (longs, shorts) pozwala podmienić ranking na LOSOWY
  (rachunek mocy z symulacji — wniosek 58) bez zmiany reszty maszynerii.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SIGNAL_LOOKBACK_DAYS = 28
HOLD_DAYS = 7
LEG_SIZE = 5  # kwartyl z top-20
CAPITAL_PER_LEG = 0.5


def daily_funding_panel(universe_dir: str | Path) -> pd.DataFrame:
    """Panel dzienny: suma stawek funding rozliczonych w danym dniu UTC per symbol (jitter ms → dzień)."""
    frames = []
    for path in sorted(Path(universe_dir).glob("*_funding.parquet")):
        df = pd.read_parquet(path)
        if df.empty:
            continue
        day = pd.to_datetime(df["timestamp"], utc=True).dt.floor("D")
        s = df["funding_rate"].astype(float).groupby(day).sum()
        s.name = path.name[: -len("_funding.parquet")]
        frames.append(s)
    if not frames:
        raise ValueError(f"brak plików *_funding.parquet w {universe_dir}")
    return pd.concat(frames, axis=1).sort_index()


def signal_panel(close: pd.DataFrame, lookback: int = SIGNAL_LOOKBACK_DAYS) -> pd.DataFrame:
    """Zwrot z `lookback` dni: close_t / close_{t−lookback} − 1 (NaN, gdy brak którejś ceny)."""
    return close / close.shift(lookback) - 1.0


def rebalance_dates(
    index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp, hold_days: int = HOLD_DAYS
) -> list[pd.Timestamp]:
    """Co `hold_days` dni kalendarzowych od pierwszego dnia indeksu ≥ `start`, do `end` (wyłącznie)."""
    days = index[(index >= start) & (index < end)]
    if len(days) == 0:
        return []
    out, nxt = [], days[0]
    for d in days:
        if d >= nxt:
            out.append(d)
            nxt = d + pd.Timedelta(days=hold_days)
    return out


def rank_legs(
    signal_row: pd.Series, members: list[str], rng=None, leg_size: int = LEG_SIZE
) -> tuple[list[str], list[str]] | None:
    """Top-`leg_size` (long) i bottom-`leg_size` (short) po sygnale wśród członków z sygnałem; remis → nazwa."""
    s = signal_row.reindex(members).dropna()
    if len(s) < 2 * leg_size:
        return None
    ranked = sorted(s.items(), key=lambda kv: (-kv[1], kv[0]))
    longs = sorted(k for k, _ in ranked[:leg_size])
    shorts = sorted(k for k, _ in ranked[-leg_size:])
    return longs, shorts


def random_legs(
    signal_row: pd.Series, members: list[str], rng, leg_size: int = LEG_SIZE
) -> tuple[list[str], list[str]] | None:
    """Losowe, rozłączne nogi spośród członków Z SYGNAŁEM (ta sama populacja co ranking) — rachunek mocy."""
    s = signal_row.reindex(members).dropna()
    if len(s) < 2 * leg_size:
        return None
    pick = list(rng.choice(sorted(s.index), size=2 * leg_size, replace=False))
    return sorted(pick[:leg_size]), sorted(pick[leg_size:])


def _month_of(day: pd.Timestamp, month_starts: list[pd.Timestamp]) -> pd.Timestamp | None:
    prev = [m for m in month_starts if m <= day]
    return prev[-1] if prev else None


def long_short_returns(
    close: pd.DataFrame,
    funding_daily: pd.DataFrame,
    members: dict[pd.Timestamp, list[str]],
    dates: list[pd.Timestamp],
    fee: float,
    legs_fn=rank_legs,
    lookback: int = SIGNAL_LOOKBACK_DAYS,
    leg_size: int = LEG_SIZE,
    rng=None,
) -> pd.DataFrame:
    """
    Dzienny szereg portfela long-short (kapitał 1). Formowanie w dniu `t` ∈ `dates` po sygnale
    z zamknięć ≤ t (`legs_fn`), trzymanie do następnej daty formowania (wagi dryfują), zwroty
    od dnia t+1. Kolumny: date, formation, r_long, r_short, r_ls_gross, funding_net, turnover,
    cost, r_net, n_long, n_short. Tygodnie bez wystarczającej liczby członków z sygnałem pomijane
    (pozycja zamknięta → obrót zamknięcia liczony przy następnym formowaniu).
    """
    returns = close.pct_change()
    signal = signal_panel(close, lookback)
    fund = funding_daily.reindex(index=returns.index, columns=returns.columns).fillna(0.0)
    month_starts = sorted(members)
    rows = []
    w_long: pd.Series = pd.Series(dtype=float)  # wagi w jednostkach kapitału (suma 0,5 na nogę)
    w_short: pd.Series = pd.Series(dtype=float)
    for k, t in enumerate(dates):
        t_next = dates[k + 1] if k + 1 < len(dates) else returns.index[-1] + pd.Timedelta(days=1)
        m = _month_of(t, month_starts)
        legs = legs_fn(signal.loc[t], members[m], rng, leg_size) if m is not None else None
        if legs is None:
            new_long, new_short = pd.Series(dtype=float), pd.Series(dtype=float)
        else:
            new_long = pd.Series(CAPITAL_PER_LEG / leg_size, index=legs[0])
            new_short = pd.Series(CAPITAL_PER_LEG / leg_size, index=legs[1])
        turnover = float(
            new_long.subtract(w_long, fill_value=0.0).abs().sum()
            + new_short.subtract(w_short, fill_value=0.0).abs().sum()
        )
        w_long, w_short = new_long, new_short
        cost_today = fee * turnover
        days = returns.index[(returns.index > t) & (returns.index <= t_next)]
        if len(days) == 0:
            continue
        for d in days:
            if len(w_long) == 0:
                rows.append(
                    {
                        "date": d,
                        "formation": t,
                        "r_long": 0.0,
                        "r_short": 0.0,
                        "r_ls_gross": 0.0,
                        "funding_net": 0.0,
                        "turnover": turnover if d == days[0] else 0.0,
                        "cost": cost_today if d == days[0] else 0.0,
                        "r_net": -(cost_today if d == days[0] else 0.0),
                        "n_long": 0,
                        "n_short": 0,
                    }
                )
                continue
            r_l = returns.loc[d, w_long.index].fillna(0.0)
            r_s = returns.loc[d, w_short.index].fillna(0.0)
            f_l = fund.loc[d, w_long.index]
            f_s = fund.loc[d, w_short.index]
            v_l, v_s = float(w_long.sum()), float(w_short.sum())
            r_long = float((w_long * r_l).sum() / v_l) if v_l > 0 else 0.0
            r_short = float((w_short * r_s).sum() / v_s) if v_s > 0 else 0.0
            r_ls = CAPITAL_PER_LEG * (r_long - r_short)
            funding_net = float((w_short * f_s).sum() - (w_long * f_l).sum())
            c = cost_today if d == days[0] else 0.0
            rows.append(
                {
                    "date": d,
                    "formation": t,
                    "r_long": r_long,
                    "r_short": r_short,
                    "r_ls_gross": r_ls,
                    "funding_net": funding_net,
                    "turnover": turnover if d == days[0] else 0.0,
                    "cost": c,
                    "r_net": r_ls + funding_net - c,
                    "n_long": int((r_l != 0).sum()),
                    "n_short": int((r_s != 0).sum()),
                }
            )
            # dryf wag (buy-and-hold w oknie), znormalizowany do stałej wartości nogi 0,5
            w_long = w_long * (1.0 + r_l)
            w_long = w_long / w_long.sum() * CAPITAL_PER_LEG if w_long.sum() > 0 else w_long
            w_short = w_short * (1.0 + r_s)
            w_short = w_short / w_short.sum() * CAPITAL_PER_LEG if w_short.sum() > 0 else w_short
    return pd.DataFrame(rows)


def weekly_ic(
    close: pd.DataFrame,
    members: dict[pd.Timestamp, list[str]],
    dates: list[pd.Timestamp],
    lookback: int = SIGNAL_LOOKBACK_DAYS,
    hold_days: int = HOLD_DAYS,
) -> pd.DataFrame:
    """Per data formowania: Spearman między sygnałem (≤ t) a zwrotem t → t+hold_days wśród członków; n par."""
    signal = signal_panel(close, lookback)
    fwd = close.shift(-hold_days) / close - 1.0
    month_starts = sorted(members)
    rows = []
    for t in dates:
        m = _month_of(t, month_starts)
        if m is None:
            continue
        pair = pd.DataFrame({"s": signal.loc[t], "f": fwd.loc[t]}).reindex(members[m]).dropna()
        if len(pair) < 4:
            continue
        rows.append(
            {
                "formation": t,
                "ic": float(pair["s"].corr(pair["f"], method="spearman")),
                "n": len(pair),
            }
        )
    return pd.DataFrame(rows)


def simulate_null_means(
    close: pd.DataFrame,
    funding_daily: pd.DataFrame,
    members: dict[pd.Timestamp, list[str]],
    dates: list[pd.Timestamp],
    fee: float,
    n_sim: int,
    seed: int = 0,
    leg_size: int = LEG_SIZE,
) -> pd.DataFrame:
    """
    Rachunek mocy z symulacji (wniosek 58): `n_sim` losowych rankingów na TYCH SAMYCH danych →
    per symulacja: średni dzienny zwrot netto, brutto, funding, koszt, sd dzienna. Rozrzut średnich
    między symulacjami = empiryczne se pod H0 (bez patrzenia na prawdziwy sygnał).
    """
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_sim):
        out = long_short_returns(
            close,
            funding_daily,
            members,
            dates,
            fee,
            legs_fn=random_legs,
            leg_size=leg_size,
            rng=rng,
        )
        rows.append(
            {
                "sim": i,
                "n_days": len(out),
                "mean_net": out["r_net"].mean(),
                "mean_gross": out["r_ls_gross"].mean(),
                "mean_funding": out["funding_net"].mean(),
                "mean_cost": out["cost"].mean(),
                "sd_net": out["r_net"].std(ddof=1),
                "acf1_net": out["r_net"].autocorr(1),
            }
        )
    return pd.DataFrame(rows)
