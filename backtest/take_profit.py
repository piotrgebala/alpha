"""
take_profit.py — runda TP1 (decyzja użytkownika 2026-09-26): wyjście na CELU ZYSKU w tygodniowych
silnikach dziennika z pozycjami „kup i trzymaj” w fazie (trend TS1, premia Coinbase CP1). X1 poza modułem:
jego silnik co dzień wyrównuje wartość nóg i nie ma likwidacji — cel zysku na pojedynczej pozycji nie ma
tam jednoznacznego odpowiednika (próba odwzorowania pozycjami: korelacja z dziennikiem 0,09; TP1 README).

`phase_returns_tp` = `ts_momentum.phase_returns_liq` + jedno zdarzenie: pozycja, której dzienne
maksimum (long) / minimum (short) sięga ceny wejścia × (1 ± tp), zamyka się TEGO dnia po cenie celu
(zlecenie z limitem czeka w arkuszu; luka otwarcia ponad cel liczona po celu — na niekorzyść), płaci
koszt wyjścia od nominału i do następnego formowania fazy stoi w gotówce (bez fundingu, bez odsetek).
Cel i likwidacja w tej samej świecy → likwidacja (kolejności w świecy dziennej nie znamy; wariant
niekorzystny). `tp=None` → wynik identyczny z `phase_returns_liq`; `lev=None` → bez likwidacji.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.ts_momentum import PHASES, build_formations, ewma_vol, formation_dates, signal_sign

COLUMNS = [
    "date",
    "gross",
    "funding",
    "cost",
    "net",
    "gross_notional",
    "net_notional",
    "turnover",
    "liquidations",
    "tp_exits",
]
MEAN_COLS = ["gross", "funding", "cost", "net", "gross_notional", "net_notional", "turnover"]


def phase_returns_tp(
    returns: np.ndarray,
    funding: np.ndarray,
    index: pd.DatetimeIndex,
    formations: list[tuple[int, np.ndarray]],
    fee: float,
    low_rel: np.ndarray,
    high_rel: np.ndarray,
    lev: float | None = None,
    mmr: float = 0.01,
    tp: float | None = None,
) -> pd.DataFrame:
    """Dzienny szereg jednej fazy z likwidacją izolowaną (`lev`) i celem zysku (`tp`, ułamek ceny)."""
    n_days, n_sym = returns.shape
    thr = 1.0 / lev - mmr if lev else None
    none = np.zeros(n_sym, dtype=bool)
    w_cur = np.zeros(n_sym)
    rows = []
    for k, (t_pos, w_new) in enumerate(formations):
        t_next = formations[k + 1][0] if k + 1 < len(formations) else n_days - 1
        turnover = float(np.abs(w_new - w_cur).sum())
        w_entry = w_new.astype(float).copy()
        cum = np.zeros(n_sym)
        alive = w_entry != 0
        equity = 1.0
        w_cur = w_entry.copy()
        cost_today = fee * turnover
        target = None if tp is None else np.where(w_entry > 0, 1.0 + tp, 1.0 - tp)
        for d in range(t_pos + 1, t_next + 1):
            r = np.nan_to_num(returns[d], nan=0.0)
            f = np.nan_to_num(funding[d], nan=0.0)
            lr = np.nan_to_num(low_rel[d], nan=1.0)
            hr = np.nan_to_num(high_rel[d], nan=1.0)
            pf = 1.0 + cum
            w_start = w_cur.copy()
            liq = none
            if thr is not None:
                liq = alive & (
                    ((w_entry > 0) & (1.0 - pf * lr >= thr))
                    | ((w_entry < 0) & (pf * hr - 1.0 >= thr))
                )
            hit = none
            if tp is not None:
                hit = (
                    alive
                    & ~liq
                    & (
                        ((w_entry > 0) & (pf * hr >= 1.0 + tp))
                        | ((w_entry < 0) & (pf * lr <= 1.0 - tp))
                    )
                )
            normal = alive & ~liq & ~hit
            pnl = np.zeros(n_sym)
            pnl[normal] = w_entry[normal] * pf[normal] * r[normal]
            if thr is not None:
                pnl[liq] = -np.abs(w_entry[liq]) / lev - w_entry[liq] * cum[liq]
            if tp is not None:
                pnl[hit] = w_entry[hit] * (target[hit] - pf[hit])
            fund = -float((w_entry * pf * f)[alive].sum()) / equity
            gross = float(pnl.sum()) / equity
            c = cost_today if d == t_pos + 1 else 0.0
            if tp is not None and hit.any():
                c += fee * float((np.abs(w_entry) * target)[hit].sum()) / equity
            cum[normal] = pf[normal] * (1.0 + r[normal]) - 1.0
            alive = alive & ~liq & ~hit
            equity += float(pnl.sum())
            if equity > 0:
                w_cur = np.where(alive, w_entry * (1.0 + cum), 0.0) / equity
            else:
                w_cur = np.zeros(n_sym)
            rows.append(
                (
                    index[d],
                    gross,
                    fund,
                    c,
                    gross + fund - c,
                    float(np.abs(w_start).sum()),
                    float(w_start.sum()),
                    turnover if d == t_pos + 1 else 0.0,
                    int(liq.sum()),
                    int(hit.sum()),
                )
            )
    return pd.DataFrame(rows, columns=COLUMNS)


def ts1_forms(close: pd.DataFrame, members: dict, start: pd.Timestamp, end: pd.Timestamp) -> list:
    """Formowania 7 faz trendu TS1 (znak zwrotu 28 dni, wagi z celu zmienności) — jak `portfolio`."""
    signs, vols = signal_sign(close), ewma_vol(close)
    return [
        build_formations(signs, vols, members, formation_dates(close.index, start, end, ph))
        for ph in range(PHASES)
    ]


def cp1_forms(
    close: pd.DataFrame, signs: pd.DataFrame, members: dict, start: pd.Timestamp, end: pd.Timestamp
) -> list:
    """Formowania 7 faz premii Coinbase (znak z premii zamiast znaku zwrotu) — jak `portfolio`."""
    s = signs.reindex(index=close.index, columns=close.columns)
    vols = ewma_vol(close)
    return [
        build_formations(s, vols, members, formation_dates(close.index, start, end, ph))
        for ph in range(PHASES)
    ]


def leg_returns(
    close: pd.DataFrame,
    funding_daily: pd.DataFrame,
    low: pd.DataFrame,
    high: pd.DataFrame,
    forms_by_phase: list,
    fee: float,
    lev: float | None,
    mmr: float = 0.01,
    tp: float | None = None,
) -> pd.DataFrame:
    """Średnia 7 faz (dni, w których wszystkie fazy mają pozycję) + suma zdarzeń (likwidacje, cele)."""
    rets = close.pct_change(fill_method=None).to_numpy(dtype=float)
    fund = funding_daily.reindex(index=close.index, columns=close.columns).fillna(0.0)
    prev = close.shift(1)
    lo = (low.reindex(index=close.index, columns=close.columns) / prev).to_numpy(dtype=float)
    hi = (high.reindex(index=close.index, columns=close.columns) / prev).to_numpy(dtype=float)
    per = [
        phase_returns_tp(
            rets, fund.to_numpy(dtype=float), close.index, forms, fee, lo, hi, lev, mmr, tp
        ).set_index("date")
        for forms in forms_by_phase
    ]
    first = max(p.index.min() for p in per)
    stacked = [p.loc[p.index >= first] for p in per]
    avg = sum(s[MEAN_COLS] for s in stacked) / len(per)
    events = sum(s[["liquidations", "tp_exits"]] for s in stacked)
    return avg.join(events)
