"""
funding_settlement.py — funding liczony DRUGĄ DROGĄ (zadanie 016, runda FD1): każde rozliczenie osobno,
nominał pozycji w chwili rozliczenia, wobec uproszczenia silników (dzienna suma stawek × waga z początku dnia).

Silniki `ts_momentum` / `xs_momentum` liczą składową funding dnia `d` jako −Σ_i w_{d,i} · f_{d,i}, gdzie
w_{d,i} to waga z początku dnia (po zamknięciu dnia d−1), a f_{d,i} = suma stawek z rozliczeń, których
znacznik czasu po `floor("D")` wypada w dniu d (`xs_momentum.daily_funding_panel`). Wzór giełdy (i freqtrade:
stawka × cena mark × ilość w chwili rozliczenia) liczy każde rozliczenie osobno. Różnice są trzy:

1. **dryf w ciągu dnia** — rozliczenie o 08:00 / 16:00 (i co 4 h / 1 h) płaci się od nominału
   ilość × cena(s), a nie od nominału z 00:00;
2. **granica 00:00** — rozliczenie dokładnie w chwili zmiany pozycji (formowanie po zamknięciu dnia =
   00:00 UTC): silnik przypisuje je NOWEJ pozycji (konwencja [wejście, wyjście)); zlecenie złożone chwilę
   po 00:00 płaci je STARĄ pozycją ((wejście, wyjście]); wzór z domkniętym przedziałem po obu stronach
   ([wejście, wyjście], freqtrade przy zamknięciu i ponownym otwarciu) liczy je DWA razy;
3. **ilość stała w tygodniu** — pozycja z dziennika to ilość kupiona raz na tydzień; X1 w silniku
   co dzień przywraca nogę do 0,5 kapitału (to założenie silnika, nie giełdy).

Konwencje tablic (dni × symbole, indeks dzienny UTC jak panel `close`):
- `W[d, i]` — waga z POCZĄTKU dnia d (jednostki kapitału fazy na początek dnia d), stała ilość od formowania;
- `R[d, i]` — zwrot ceny w dniu d (NaN → 0; 00:00 d → 00:00 d+1);
- `alive_end[d, i]` — pozycja istnieje na końcu dnia d (po ewentualnej likwidacji);
- `first[d]` — d jest pierwszym dniem okresu trzymania (dzień po formowaniu).
Rozliczenie (symbol i, chwila s) z d0 = floor(s): `ratio` = cena(s) / cena(00:00 d0); dla s = 00:00 ratio = 1.

Cena mark niedostępna w repo — zastępuje ją cena zamknięcia świecy (przybliżenie zapisane w README rundy).
Testy: `tests/test_funding_settlement.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

MIDNIGHT_TOL = pd.Timedelta(minutes=1)  # jitter znaczników rozliczeń Binance to milisekundy


# ----------------------------------------------------------------------------- rozliczenia


@dataclass
class Settlements:
    """Rozliczenia w formie płaskich tablic (po jednym wierszu na rozliczenie)."""

    sym: np.ndarray  # pozycja kolumny symbolu
    day: np.ndarray  # pozycja dnia floor(s) w indeksie dziennym (−1 = poza indeksem)
    frac: np.ndarray  # część doby od 00:00 (0 dla rozliczenia o północy)
    rate: np.ndarray  # stawka (NaN zostaje NaN — decyzja o zerze należy do wywołującego)
    ts: np.ndarray  # znacznik czasu UTC zaokrąglony do minuty, nanosekundy od 1970 (int64)

    @property
    def midnight(self) -> np.ndarray:
        return self.frac == 0.0


def build_settlements(
    raw: dict[str, pd.DataFrame], columns: list[str], index: pd.DatetimeIndex
) -> Settlements:
    """`raw[sym]` = ramka (timestamp, funding_rate). Znacznik zaokrąglony do minuty (jitter ms)."""
    col_pos = {c: i for i, c in enumerate(columns)}
    parts = []
    for sym, df in raw.items():
        if sym not in col_pos or df.empty:
            continue
        ts = pd.to_datetime(df["timestamp"], utc=True).dt.round("min")
        day = ts.dt.floor("D")
        frac = (ts - day) / pd.Timedelta(days=1)
        pos = index.get_indexer(pd.DatetimeIndex(day))
        parts.append(
            pd.DataFrame(
                {
                    "sym": col_pos[sym],
                    "day": pos,
                    "frac": frac.to_numpy(dtype=float),
                    "rate": df["funding_rate"].to_numpy(dtype=float),
                    "ts": ts.dt.tz_convert(None)
                    .to_numpy()
                    .astype("datetime64[ns]")
                    .astype("int64"),
                }
            )
        )
    if not parts:
        empty = np.array([], dtype=float)
        return Settlements(
            empty.astype(int), empty.astype(int), empty, empty, empty.astype("int64")
        )
    df = pd.concat(parts, ignore_index=True)
    return Settlements(
        df["sym"].to_numpy(dtype=int),
        df["day"].to_numpy(dtype=int),
        df["frac"].to_numpy(dtype=float),
        df["rate"].to_numpy(dtype=float),
        df["ts"].to_numpy(dtype="int64"),
    )


def daily_sum(st: Settlements, n_days: int, n_sym: int) -> np.ndarray:
    """Dzienna suma stawek jak `daily_funding_panel` (NaN, gdy w dniu brak rozliczeń albo stawki)."""
    out = np.full((n_days, n_sym), np.nan)
    ok = (st.day >= 0) & np.isfinite(st.rate)
    tot = np.zeros((n_days, n_sym))
    cnt = np.zeros((n_days, n_sym))
    np.add.at(tot, (st.day[ok], st.sym[ok]), st.rate[ok])
    np.add.at(cnt, (st.day[ok], st.sym[ok]), 1.0)
    out[cnt > 0] = tot[cnt > 0]
    return out


def interp_ratio(st: Settlements, R: np.ndarray) -> np.ndarray:
    """Przybliżenie ceny(s) / ceny(00:00): (1 + r_dnia)^część_doby (geometryczna interpolacja zamknięć)."""
    ratio = np.ones(len(st.rate))
    ok = st.day >= 0
    r = R[st.day[ok], st.sym[ok]]
    ratio[ok] = (1.0 + r) ** st.frac[ok]
    return ratio


# ----------------------------------------------------------------------------- dwie drogi


def engine_funding(W_eng: np.ndarray, fday: np.ndarray) -> np.ndarray:
    """(a) jak silnik: −w_dzień · f_dzień (NaN → 0), macierz dni × symbole."""
    return -W_eng * np.nan_to_num(fday, nan=0.0)


def settlement_funding(
    W: np.ndarray,
    R: np.ndarray,
    alive_end: np.ndarray,
    first: np.ndarray,
    st: Settlements,
    ratio: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    (b) każde rozliczenie osobno, nominał w chwili rozliczenia. Macierze dni × symbole (dzień, do którego
    trafia opłata w szeregu dziennym). Rozliczenia poza północą: −W[d0]·ratio·f w dniu d0. Północ d0:
    - `b0` [wejście, wyjście): −W[d0]·f w dniu d0 (jak silnik przypisuje granicę);
    - `b1` (wejście, wyjście]: −W[d0−1]·(1+R[d0−1])·alive_end[d0−1]·f w dniu d0−1 (stara pozycja);
    - `b2` [wejście, wyjście]: b1 + na pierwszym dniu okresu także −W[d0]·f (granica liczona dwa razy);
    - `new_edge` / `old_edge`: same opłaty z rozliczeń granicznych (północ pierwszego dnia okresu)
      przypisane nowej / starej pozycji — rachunek miejsca ryzyka nr 1.
    Stawka NaN → 0 (jak silnik).
    """
    n_days, n_sym = W.shape
    f = np.nan_to_num(st.rate, nan=0.0)
    ok = st.day >= 0
    mid = st.midnight & ok
    off = ~st.midnight & ok
    out = {k: np.zeros((n_days, n_sym)) for k in ("b0", "b1", "b2", "new_edge", "old_edge")}

    # poza północą — wspólne dla b0/b1/b2
    d, i = st.day[off], st.sym[off]
    c = -W[d, i] * ratio[off] * f[off]
    for k in ("b0", "b1", "b2"):
        np.add.at(out[k], (d, i), c)

    # północ: nowa pozycja (dzień d0)
    d, i, fm = st.day[mid], st.sym[mid], f[mid]
    c_new = -W[d, i] * fm
    np.add.at(out["b0"], (d, i), c_new)
    edge = first[d]
    np.add.at(out["b2"], (d[edge], i[edge]), c_new[edge])
    np.add.at(out["new_edge"], (d[edge], i[edge]), c_new[edge])

    # północ: stara pozycja (dzień d0−1)
    has_prev = d >= 1
    dp, ip, fp = d[has_prev] - 1, i[has_prev], fm[has_prev]
    c_old = -W[dp, ip] * (1.0 + R[dp, ip]) * alive_end[dp, ip] * fp
    np.add.at(out["b1"], (dp, ip), c_old)
    np.add.at(out["b2"], (dp, ip), c_old)
    edge_p = edge[has_prev]
    np.add.at(out["old_edge"], (dp[edge_p], ip[edge_p]), c_old[edge_p])
    return out


# ----------------------------------------------------------------------------- pozycje silników


@dataclass
class Positions:
    W: np.ndarray  # waga ze stałą ilością od formowania (początek dnia)
    W_eng: np.ndarray  # waga, od której silnik liczy funding
    R: np.ndarray
    alive_end: np.ndarray
    first: np.ndarray
    gross: np.ndarray  # zwrot brutto fazy w dniu (do kontroli zgodności z silnikiem)
    in_phase: np.ndarray  # dzień należy do szeregu fazy


def ts_liq_positions(
    returns: np.ndarray,
    formations: list[tuple[int, np.ndarray]],
    low_rel: np.ndarray,
    high_rel: np.ndarray,
    lev: float,
    mmr: float,
) -> Positions:
    """Pętla dni `ts_momentum.phase_returns_liq` bez zmian logiki — zwraca wagi, z których silnik liczy funding."""
    n_days, n_sym = returns.shape
    W = np.zeros((n_days, n_sym))
    R = np.nan_to_num(returns, nan=0.0)
    alive_end = np.zeros((n_days, n_sym))
    first = np.zeros(n_days, dtype=bool)
    gross = np.zeros(n_days)
    in_phase = np.zeros(n_days, dtype=bool)
    thr = 1.0 / lev - mmr
    for k, (t_pos, w_new) in enumerate(formations):
        t_next = formations[k + 1][0] if k + 1 < len(formations) else n_days - 1
        w_entry = w_new.astype(float).copy()
        cum = np.zeros(n_sym)
        alive = w_entry != 0
        equity = 1.0
        for d in range(t_pos + 1, t_next + 1):
            r = R[d]
            lr = np.nan_to_num(low_rel[d], nan=1.0)
            hr = np.nan_to_num(high_rel[d], nan=1.0)
            pf = 1.0 + cum
            liq = alive & (
                ((w_entry > 0) & (1.0 - pf * lr >= thr)) | ((w_entry < 0) & (pf * hr - 1.0 >= thr))
            )
            normal = alive & ~liq
            pnl = np.zeros(n_sym)
            pnl[normal] = w_entry[normal] * pf[normal] * r[normal]
            pnl[liq] = -np.abs(w_entry[liq]) / lev - w_entry[liq] * cum[liq]
            W[d] = np.where(alive, w_entry * pf, 0.0) / equity
            first[d] = d == t_pos + 1
            in_phase[d] = True
            gross[d] = float(pnl.sum()) / equity
            cum[normal] = pf[normal] * (1.0 + r[normal]) - 1.0
            alive = alive & ~liq
            alive_end[d] = alive
            equity += float(pnl.sum())
    return Positions(W, W.copy(), R, alive_end, first, gross, in_phase)


def xs_positions(
    close: pd.DataFrame,
    members: dict,
    dates: list[pd.Timestamp],
    legs_fn,
    capital_per_leg: float,
    leg_size: int,
    signal: pd.DataFrame,
) -> Positions:
    """
    Pętla `xs_momentum.long_short_returns`: `W_eng` = wagi silnika (noga przywracana do 0,5 co dzień),
    `W` = stała ilość od formowania (kapitał fazy = 1 + Σ w0·(cena/cena_wejścia − 1)).
    """
    returns = close.pct_change()
    idx = returns.index
    cols = list(close.columns)
    col_pos = {c: i for i, c in enumerate(cols)}
    n_days, n_sym = returns.shape
    Rraw = returns.to_numpy(dtype=float)
    R = np.nan_to_num(Rraw, nan=0.0)
    W = np.zeros((n_days, n_sym))
    W_eng = np.zeros((n_days, n_sym))
    alive_end = np.zeros((n_days, n_sym))
    first = np.zeros(n_days, dtype=bool)
    gross = np.zeros(n_days)
    in_phase = np.zeros(n_days, dtype=bool)
    month_starts = sorted(members)
    for k, t in enumerate(dates):
        t_next = dates[k + 1] if k + 1 < len(dates) else idx[-1] + pd.Timedelta(days=1)
        prev = [m for m in month_starts if m <= t]
        legs = legs_fn(signal.loc[t], members[prev[-1]], None, leg_size) if prev else None
        day_pos = np.where((idx > t) & (idx <= t_next))[0]
        if len(day_pos) == 0:
            continue
        w0 = np.zeros(n_sym)
        wl = np.zeros(n_sym)
        ws = np.zeros(n_sym)
        if legs is not None:
            for s in legs[0]:
                wl[col_pos[s]] = capital_per_leg / leg_size
            for s in legs[1]:
                ws[col_pos[s]] = capital_per_leg / leg_size
            w0 = wl - ws
        pf = np.ones(n_sym)
        for j, d in enumerate(day_pos):
            in_phase[d] = True
            first[d] = j == 0
            if legs is None:
                continue
            equity = 1.0 + float((w0 * (pf - 1.0)).sum())
            W[d] = w0 * pf / equity
            W_eng[d] = wl - ws
            r = R[d]
            vl, vs = wl.sum(), ws.sum()
            r_long = float((wl * r).sum() / vl) if vl > 0 else 0.0
            r_short = float((ws * r).sum() / vs) if vs > 0 else 0.0
            gross[d] = capital_per_leg * (r_long - r_short)
            alive_end[d] = (w0 != 0).astype(float)
            pf = pf * (1.0 + r)
            wl = wl * (1.0 + r)
            wl = wl / wl.sum() * capital_per_leg if wl.sum() > 0 else wl
            ws = ws * (1.0 + r)
            ws = ws / ws.sum() * capital_per_leg if ws.sum() > 0 else ws
    return Positions(W, W_eng, R, alive_end, first, gross, in_phase)


# ----------------------------------------------------------------------------- druga droga (dolarowo)


def dollar_way_b1(
    holdings: list[tuple[pd.Timestamp, pd.Timestamp, pd.Series]],
    returns: pd.DataFrame,
    settle: dict[str, tuple[np.ndarray, np.ndarray]],
    ratio_fn,
    capital: pd.Series | None = None,
    low_rel: pd.DataFrame | None = None,
    high_rel: pd.DataFrame | None = None,
    lev: float = 2.0,
    mmr: float = 0.01,
) -> pd.Series:
    """
    DRUGA DROGA liczby głównej (niezależna od tablic `Positions`): opłata w „dolarach” = ilość × cena(s) × stawka,
    rozliczenie po rozliczeniu, konwencja (wejście, wyjście], podzielona przez kapitał fazy z początku dnia,
    do którego trafia opłata.

    - `holdings` = [(pierwszy dzień, ostatni dzień, wagi ze znakiem w chwili formowania — ułamek kapitału)];
    - `returns` = dzienne zwroty tak, jak widzi je silnik (NaN → 0 = pozycja stoi w miejscu);
    - `settle[sym]` = (znaczniki czasu datetime64[ns] zaokrąglone do minuty, rosnąco; stawki);
    - `ratio_fn(sym, ts: DatetimeIndex) -> np.ndarray` = cena(s) / cena(00:00 tego dnia) poza północą;
    - `capital` = kapitał fazy na początek dnia (TS1: iloczyn 1 + gross silnika); None → kapitał stałej
      ilości liczony w okresie od 1 (X1: 1 + Σ w·(wzrost − 1));
    - `low_rel` / `high_rel` (TS1): minimum / maksimum dnia ÷ zamknięcie poprzedniego dnia → likwidacja
      izolowana jak w silniku (próg 1/lev − mmr od ceny wejścia); dzień likwidacji: rozliczenia w ciągu
      dnia płacone, północ kończąca dzień już nie.
    Zwraca szereg dziennych opłat (indeks = dni z `returns`).
    """
    days = returns.index
    out = np.zeros(len(days))
    one_day = pd.Timedelta(days=1)
    thr = 1.0 / lev - mmr
    for entry, last, w in holdings:
        w = w[w != 0]
        if w.empty:
            continue
        span = days[(days >= entry) & (days <= last)]
        r = returns.loc[span, w.index].fillna(0.0)
        g_end = (1.0 + r).cumprod()  # wzrost ceny od wejścia do końca dnia
        g_start = g_end.shift(1).fillna(1.0)  # do początku dnia
        if capital is not None:
            cap = capital.loc[span]
            cap_entry = float(cap.iloc[0])
        else:
            cap = 1.0 + (g_start * w).sum(axis=1) - float(w.sum())
            cap_entry = 1.0
        liq_day = pd.Series(pd.NaT, index=w.index, dtype="datetime64[ns, UTC]")
        if low_rel is not None:
            lr = low_rel.loc[span, w.index].fillna(1.0)
            hr = high_rel.loc[span, w.index].fillna(1.0)
            hit = ((w > 0) & (1.0 - g_start * lr >= thr)) | ((w < 0) & (g_start * hr - 1.0 >= thr))
            for sym in w.index[hit.any(axis=0).to_numpy()]:
                liq_day[sym] = hit.index[hit[sym].to_numpy()][0]
        for sym, wi in w.items():
            if sym not in settle:
                continue
            ts, rate = settle[sym]
            lo_t = np.datetime64(entry.tz_convert(None), "ns")
            if pd.isna(liq_day[sym]):  # (wejście, wyjście]: północ wyjścia wlicza się
                hi_t = np.datetime64((last + one_day).tz_convert(None), "ns")
                sel = (ts > lo_t) & (ts <= hi_t)
            else:  # likwidacja: do końca dnia likwidacji, bez północy kończącej ten dzień
                hi_t = np.datetime64((liq_day[sym] + one_day).tz_convert(None), "ns")
                sel = (ts > lo_t) & (ts < hi_t)
            if not sel.any():
                continue
            s = pd.DatetimeIndex(ts[sel]).tz_localize("UTC")
            f = np.nan_to_num(rate[sel], nan=0.0)
            day = s.floor("D")
            mid = np.asarray(s == day)
            attr = day.where(~mid, day - one_day)  # północ → dzień poprzedni (stara pozycja)
            notional = np.empty(len(s))
            # północ: nominał z końca poprzedniego dnia = cena zamknięcia
            notional[mid] = wi * cap_entry * g_end[sym].reindex(attr[mid]).to_numpy()
            if (~mid).any():
                notional[~mid] = (
                    wi
                    * cap_entry
                    * g_start[sym].reindex(day[~mid]).to_numpy()
                    * ratio_fn(sym, s[~mid])
                )
            denom = cap.reindex(attr).to_numpy()
            np.add.at(out, days.get_indexer(attr), -notional * f / denom)
    return pd.Series(out, index=days)


# ----------------------------------------------------------------------------- statystyka


def weekly_block_bootstrap(
    x: np.ndarray, n_boot: int = 10_000, block: int = 7, seed: int = 0, scale: float = 365.0
) -> tuple[float, float, float]:
    """Średnia × `scale` i przedział 95 % z bootstrapu blokowego (bloki `block` kolejnych dni, z powtórzeniami)."""
    x = np.asarray(x, dtype=float)
    n_blocks = len(x) // block
    if n_blocks < 2:
        raise ValueError("za mało bloków")
    blocks = x[: n_blocks * block].reshape(n_blocks, block)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, n_blocks, size=(n_boot, n_blocks))
    means = blocks[pick].mean(axis=(1, 2)) * scale
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(x.mean() * scale), float(lo), float(hi)


def load_raw_funding(
    universe_dir: str | Path, symbols: list[str]
) -> dict[str, pd.DataFrame]:  # pragma: no cover - IO
    out = {}
    for s in symbols:
        p = Path(universe_dir) / f"{s}_funding.parquet"
        if p.exists():
            out[s] = pd.read_parquet(p)
    return out
