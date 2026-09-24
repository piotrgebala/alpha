"""
ts_momentum.py — momentum w czasie (time-series momentum, TSMOM; runda TS1, rodzina A1 katalogu
na horyzoncie tygodniowym): KAŻDA moneta z koszyka top-20 point-in-time dostaje własny zakład
o kierunek — long, gdy jej zwrot z `LOOKBACK_DAYS` dni jest dodatni, short, gdy ujemny — z wagą
skalowaną zmiennością: w_i = s_i · min(CAP, TARGET_VOL / σ̂_i) / N (Moskowitz–Ooi–Pedersen 2012).

Konwencje (jak `xs_momentum.py`, testy: `tests/test_ts_momentum.py`):
- `close`: panel dzienny (indeks = dzień UTC, kolumny = symbole) z `rebalance_premium.load_universe`;
- sygnał i σ̂ na dzień `t` używają WYŁĄCZNIE zamknięć ≤ `t`; pozycja wchodzi po zamknięciu `t`,
  pierwszy zwrot z dnia `t + 1` (test przyszłości);
- wagi w jednostkach kapitału (1 = cały kapitał); zwrot dzienny brutto = Σ w_i · r_i;
- funding: pozycja o wadze w płaci w · f (long przy f > 0 płaci, short otrzymuje);
- koszt = `fee` × obrót (Σ |w_nowe − w_przed|) w dniu formowania;
- wagi dryfują w tygodniu (buy-and-hold): w ← w·(1 + r)/(1 + zwrot portfela brutto);
- wycofany członek (brak ceny) = gotówka (zwrot 0), jak w R1/X1;
- `PHASES` = 7 pod-portfeli po 1/7 kapitału, każdy formowany w inny dzień tygodnia — wniosek 68
  (X1 wrażliwe na fazę rebalansu): mierzonym obiektem jest ich średnia, nie jedna faza.
Silnik jest w numpy (tablice dni × symbole), żeby symulacje H0 (losowe znaki) były tanie.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LOOKBACK_DAYS = 28
HOLD_DAYS = 7
PHASES = 7
TARGET_VOL = 0.40  # roczna zmienność docelowa pojedynczej pozycji (MOP 2012)
CAP = 3.0  # sufit wagi pojedynczej monety (zasada 5: min(), dźwignia 3× wygrywa)
EWMA_COM = 60  # środek masy EWMA kwadratów zwrotów (MOP 2012)
VOL_MIN_PERIODS = 30
DAYS_PER_YEAR = 365


def signal_sign(close: pd.DataFrame, lookback: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """Znak zwrotu z `lookback` dni: +1 / −1 / 0 (brak ceny → NaN)."""
    ret = close / close.shift(lookback) - 1.0
    return np.sign(ret)


def ewma_vol(
    close: pd.DataFrame, com: int = EWMA_COM, min_periods: int = VOL_MIN_PERIODS
) -> pd.DataFrame:
    """Roczna zmienność σ̂_t = √(365 · EWMA(r²)) z dziennych zwrotów ≤ t (bez centrowania)."""
    r = close.pct_change(fill_method=None)
    return np.sqrt(DAYS_PER_YEAR * (r**2).ewm(com=com, min_periods=min_periods).mean())


def position_weights(
    signs: np.ndarray, vols: np.ndarray, target: float = TARGET_VOL, cap: float = CAP
) -> np.ndarray:
    """w = s · min(cap, target/σ) / N po członkach z ważnym znakiem (≠ 0) i σ > 0; reszta 0."""
    signs = np.asarray(signs, dtype=float)
    vols = np.asarray(vols, dtype=float)
    ok = np.isfinite(signs) & (signs != 0) & np.isfinite(vols) & (vols > 0)
    w = np.zeros_like(signs, dtype=float)
    n = int(ok.sum())
    if n == 0:
        return w
    w[ok] = signs[ok] * np.minimum(cap, target / vols[ok]) / n
    return w


def formation_dates(
    index: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
    phase: int,
    hold: int = HOLD_DAYS,
) -> list[pd.Timestamp]:
    """Co `hold` dni od dnia `start + phase` (dni kalendarzowe z indeksu), do `end` wyłącznie."""
    first = start + pd.Timedelta(days=phase)
    days = index[(index >= first) & (index < end)]
    return list(days[::hold]) if len(days) else []


def _month_of(day: pd.Timestamp, month_starts: list[pd.Timestamp]) -> pd.Timestamp | None:
    prev = [m for m in month_starts if m <= day]
    return prev[-1] if prev else None


def phase_returns(
    returns: np.ndarray,
    funding: np.ndarray,
    index: pd.DatetimeIndex,
    formations: list[tuple[int, np.ndarray]],
    fee: float,
) -> pd.DataFrame:
    """
    Dzienny szereg jednej fazy. `formations` = [(pozycja dnia formowania w `index`, wektor wag)].
    Zwroty od dnia po formowaniu do dnia kolejnego formowania włącznie (ostatnie — do końca).
    Kolumny: date, gross, funding, cost, net, gross_notional, net_notional, turnover.
    """
    n_days, n_sym = returns.shape
    w = np.zeros(n_sym)
    rows = []
    for k, (t_pos, w_new) in enumerate(formations):
        t_next = formations[k + 1][0] if k + 1 < len(formations) else n_days - 1
        turnover = float(np.abs(w_new - w).sum())
        w = w_new.astype(float).copy()
        cost_today = fee * turnover
        for d in range(t_pos + 1, t_next + 1):
            r = np.nan_to_num(returns[d], nan=0.0)
            f = np.nan_to_num(funding[d], nan=0.0)
            gross = float(w @ r)
            fund = -float(w @ f)
            c = cost_today if d == t_pos + 1 else 0.0
            rows.append(
                (
                    index[d],
                    gross,
                    fund,
                    c,
                    gross + fund - c,
                    float(np.abs(w).sum()),
                    float(w.sum()),
                    turnover if d == t_pos + 1 else 0.0,
                )
            )
            denom = 1.0 + gross
            w = w * (1.0 + r) / denom if denom > 0 else np.zeros_like(w)
    return pd.DataFrame(
        rows,
        columns=[
            "date",
            "gross",
            "funding",
            "cost",
            "net",
            "gross_notional",
            "net_notional",
            "turnover",
        ],
    )


def build_formations(
    signs: pd.DataFrame,
    vols: pd.DataFrame,
    members: dict[pd.Timestamp, list[str]],
    dates: list[pd.Timestamp],
    sign_fn=None,
    rng=None,
    target: float = TARGET_VOL,
    cap: float = CAP,
) -> list[tuple[int, np.ndarray]]:
    """
    Wagi na każdy dzień formowania: członkowie miesiąca (point-in-time), znak z `signs`
    (albo z `sign_fn(real_signs, symbols, rng)` — H0 / zawsze long), σ̂ z `vols`.
    """
    cols = list(signs.columns)
    col_pos = {c: i for i, c in enumerate(cols)}
    month_starts = sorted(members)
    out = []
    for t in dates:
        m = _month_of(t, month_starts)
        w = np.zeros(len(cols))
        if m is not None:
            syms = [s for s in members[m] if s in col_pos]
            idx = np.array([col_pos[s] for s in syms], dtype=int)
            s_row = signs.loc[t].to_numpy(dtype=float)[idx]
            if sign_fn is not None:
                valid = np.isfinite(s_row) & (s_row != 0)
                s_row = np.where(valid, sign_fn(s_row, syms, rng), np.nan)
            w[idx] = position_weights(s_row, vols.loc[t].to_numpy(dtype=float)[idx], target, cap)
        out.append((signs.index.get_loc(t), w))
    return out


class MarkovSigns:
    """H0: losowy znak per symbol z trwałością — przy każdym formowaniu zmiana z prawd. `p_flip`."""

    def __init__(self, p_flip: float):
        self.p_flip = p_flip
        self.state: dict[str, float] = {}

    def __call__(self, real: np.ndarray, syms: list[str], rng) -> np.ndarray:
        out = np.empty(len(syms))
        for i, s in enumerate(syms):
            if s not in self.state:
                self.state[s] = 1.0 if rng.random() < 0.5 else -1.0
            elif rng.random() < self.p_flip:
                self.state[s] = -self.state[s]
            out[i] = self.state[s]
        return out


def shift_signs(signs: pd.DataFrame, shift_days: int) -> pd.DataFrame:
    """
    H0 TS1: prawdziwy panel znaków przesunięty CYKLICZNIE o `shift_days` wierszy. Zachowuje
    trwałość znaku każdej monety i zgodność znaków między monetami (wspólny rytm rynku),
    niszczy tylko dopasowanie znaku do przyszłego zwrotu. Losowe znaki niezależne per moneta
    (`MarkovSigns`) znoszą się w koszyku i dają za wąski rozkład H0 (moc TS1, 2026-09-24).
    """
    rolled = np.roll(signs.to_numpy(), shift_days, axis=0)
    return pd.DataFrame(rolled, index=signs.index, columns=signs.columns)


def always_long(real: np.ndarray, syms: list[str], rng) -> np.ndarray:
    """Odniesienie opisowe: te same wagi co reguła, zawsze long (dryf/beta rynku)."""
    return np.ones(len(syms))


def portfolio(
    close: pd.DataFrame,
    funding_daily: pd.DataFrame,
    members: dict[pd.Timestamp, list[str]],
    start: pd.Timestamp,
    end: pd.Timestamp,
    fee: float,
    sign_fn_factory=None,
    rng=None,
    phases: int = PHASES,
    lookback: int = LOOKBACK_DAYS,
    sign_shift_days: int | None = None,
) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    """
    Średnia `phases` pod-portfeli (każdy 1/phases kapitału) — dzienny szereg w dniach, w których
    WSZYSTKIE fazy mają pozycję (od pierwszego zwrotu ostatniej fazy). Zwraca (średnia, fazy).
    `sign_fn_factory()` tworzy świeżą funkcję znaku na fazę (H0 ma stan per faza).
    `sign_shift_days` — H0 kanoniczne TS1: prawdziwe znaki przesunięte cyklicznie w czasie
    (`shift_signs`), wagi i σ̂ z właściwego dnia.
    """
    close = close[close.index < end]
    signs = signal_sign(close, lookback)
    if sign_shift_days is not None:
        signs = shift_signs(signs, sign_shift_days)
    vols = ewma_vol(close)
    rets = close.pct_change(fill_method=None).to_numpy(dtype=float)
    fund = funding_daily.reindex(index=close.index, columns=close.columns).fillna(0.0)
    fund = fund.to_numpy(dtype=float)
    per_phase = []
    for ph in range(phases):
        dates = formation_dates(close.index, start, end, ph)
        fn = sign_fn_factory() if sign_fn_factory is not None else None
        forms = build_formations(signs, vols, members, dates, sign_fn=fn, rng=rng)
        per_phase.append(phase_returns(rets, fund, close.index, forms, fee).set_index("date"))
    first_common = max(p.index.min() for p in per_phase)
    cols = ["gross", "funding", "cost", "net", "gross_notional", "net_notional", "turnover"]
    stacked = [p.loc[p.index >= first_common, cols] for p in per_phase]
    avg = sum(stacked) / phases
    return avg.reset_index(), per_phase
