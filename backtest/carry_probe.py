"""
carry_probe.py — czyste funkcje sondy P2 (carry przekrojowy, hipoteza 4A).

Pre-rejestracja: `runs/2026-09-22_p2-sonda-carry-przekrojowy/README.md` (commit 364e98d).
Moduł NIE liczy średniego zwrotu z ruchu cen ani łącznego P&L — tylko to, co pre-rejestracja
dopuszcza (mechanizm `F`, koszt `C`, rozrzut `F − C + R` i jego autokorelację).

Konwencja czasu (brak podglądania przyszłości):
- decyzja w chwili `t` = zamknięcie świecy dziennej o otwarciu `t − 1 dzień`;
- SYGNAŁ = suma stawek funding z rozliczeń o znaczniku w `[t − 48h, t)` — wszystkie znane
  przed `t`. Znaczniki Binance mają opóźnienia rzędu milisekund (np. 08:00:00.014), więc
  rozliczenie „o t" ma znacznik > t i do sygnału NIE wchodzi;
- OTRZYMANY funding = rozliczenia w `[t + 1 min, t + 48h + 1 min)`: pozycja otwarta tuż po
  rozliczeniu w `t` dostaje rozliczenia t+8h … t+48h (6 przy siatce 8h). Rozliczenie w `t`
  należy do pozycji z poprzedniego okna — każde rozliczenie jest liczone dokładnie raz;
- sumy są po CZASIE, nie po liczbie okresów — część symboli rozlicza się co 4h lub 1h.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from agents.labeling import effective_sample_size

HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS
MINUTE_MS = 60_000
WINDOW_MS = 48 * HOUR_MS

MIN_HISTORY_DAYS = 30
VOLUME_LOOKBACK_DAYS = 30
TOP_N = 50
DECILE = 0.10
MIN_BASKET = 2
MIN_ELIGIBLE = 20

Z_TWO_SIDED_95 = 1.959964  # te same stałe co backtest/metrics.py
Z_POWER_80 = 0.841621


@dataclass(frozen=True)
class SymbolData:
    """Dane jednego symbolu w postaci gotowej do szybkich zapytań przedziałowych."""

    fund_ts: np.ndarray  # int64 ms, rosnąco
    fund_cum: np.ndarray  # float, len = len(fund_ts) + 1, fund_cum[0] = 0
    close_by_ts: dict  # czas ZAMKNIĘCIA świecy (ms) -> close
    close_ts: np.ndarray  # int64 ms, rosnąco (czasy zamknięcia)
    close_vals: np.ndarray
    vol_cum: np.ndarray  # len = len(close_ts) + 1


def _to_ms(ts: pd.Series) -> np.ndarray:
    """Znaczniki czasu -> int64 ms, niezależnie od rozdzielczości (ns/us/ms) kolumny."""
    return pd.to_datetime(ts, utc=True).dt.as_unit("ms").astype("int64").to_numpy(dtype=np.int64)


def prepare_symbol(fund: pd.DataFrame, klines: pd.DataFrame) -> SymbolData:
    """`fund`: timestamp, funding_rate; `klines`: open_time, close, quote_volume (świece 1d)."""
    f_ts = _to_ms(fund["timestamp"])
    order = np.argsort(f_ts, kind="stable")
    f_ts = f_ts[order]
    f_rates = fund["funding_rate"].to_numpy(dtype=float)[order]
    k_open = _to_ms(klines["open_time"])
    k_order = np.argsort(k_open, kind="stable")
    close_ts = k_open[k_order] + DAY_MS
    closes = klines["close"].to_numpy(dtype=float)[k_order]
    vols = klines["quote_volume"].to_numpy(dtype=float)[k_order]
    return SymbolData(
        fund_ts=f_ts,
        fund_cum=np.concatenate([[0.0], np.cumsum(f_rates)]),
        close_by_ts=dict(zip(close_ts.tolist(), closes.tolist(), strict=True)),
        close_ts=close_ts,
        close_vals=closes,
        vol_cum=np.concatenate([[0.0], np.cumsum(vols)]),
    )


def funding_sum(sd: SymbolData, a_ms: int, b_ms: int) -> float:
    """Suma stawek z rozliczeń o znaczniku w `[a_ms, b_ms)`."""
    i = np.searchsorted(sd.fund_ts, a_ms, side="left")
    j = np.searchsorted(sd.fund_ts, b_ms, side="left")
    return float(sd.fund_cum[j] - sd.fund_cum[i])


def signal_at(sd: SymbolData, t_ms: int) -> float:
    return funding_sum(sd, t_ms - WINDOW_MS, t_ms)


def received_funding(sd: SymbolData, t_ms: int) -> float:
    return funding_sum(sd, t_ms + MINUTE_MS, t_ms + WINDOW_MS + MINUTE_MS)


def price_at(sd: SymbolData, t_ms: int) -> float:
    """Zamknięcie świecy dziennej zamkniętej DOKŁADNIE w `t_ms`; NaN, gdy brak."""
    return sd.close_by_ts.get(int(t_ms), float("nan"))


def exit_price(sd: SymbolData, t_ms: int) -> float:
    """
    Cena wyjścia z okna `[t, t+48h]`: ostatnie zamknięcie w `(t, t+48h]`. Symbol wycofany
    w trakcie okna wychodzi po ostatnim dostępnym zamknięciu (nie znika ze zbioru);
    brak jakiegokolwiek zamknięcia po `t` — wyjście po cenie wejścia.
    """
    j = np.searchsorted(sd.close_ts, t_ms + WINDOW_MS, side="right") - 1
    if j >= 0 and sd.close_ts[j] > t_ms:
        return float(sd.close_vals[j])
    return price_at(sd, t_ms)


def volume_trailing(sd: SymbolData, t_ms: int, days: int = VOLUME_LOOKBACK_DAYS) -> float:
    """Suma obrotu ze świec zamkniętych w `(t − days, t]`."""
    i = np.searchsorted(sd.close_ts, t_ms - days * DAY_MS, side="right")
    j = np.searchsorted(sd.close_ts, t_ms, side="right")
    return float(sd.vol_cum[j] - sd.vol_cum[i])


def is_eligible(sd: SymbolData, t_ms: int, min_history_days: int = MIN_HISTORY_DAYS) -> bool:
    """≥ `min_history_days` historii funding przed `t` i świeca zamknięta dokładnie w `t`."""
    if len(sd.fund_ts) == 0 or sd.fund_ts[0] > t_ms - min_history_days * DAY_MS:
        return False
    return not np.isnan(price_at(sd, t_ms))


def window_starts(start: str, end: str) -> list[int]:
    """Nienakładające się okna 48h od `start`; ostatnie kończy się ≤ `end`."""
    s = int(pd.Timestamp(start).value // 1_000_000)
    e = int(pd.Timestamp(end).value // 1_000_000)
    return list(range(s, e - WINDOW_MS + 1, WINDOW_MS))


def select_baskets(
    signal: pd.Series, frac: float = DECILE, min_size: int = MIN_BASKET
) -> tuple[list, list]:
    """
    (SHORT, LONG): górny i dolny decyl sygnału. Remisy rozstrzyga nazwa symbolu — wynik
    deterministyczny (masa punktowa funding na stawce bazowej, H2.0: 35,85% obserwacji).
    """
    k = max(min_size, int(np.floor(len(signal) * frac)))
    ordered = sorted(signal.items(), key=lambda kv: (kv[1], kv[0]))
    longs = [s for s, _ in ordered[:k]]
    shorts = [s for s, _ in ordered[-k:]]
    return shorts, longs


def turnover(prev: list | None, cur: list) -> float:
    """Udział miejsc w koszyku zmienionych względem poprzedniego okna (pierwsze okno = 1)."""
    if not prev or not cur:
        return 1.0
    return 1.0 - len(set(prev) & set(cur)) / len(cur)


def universe_at(data: dict, t_ms: int, top_n: int | None = TOP_N) -> list[str]:
    """Symbole zakwalifikowane w `t`; przy `top_n` — tylko `top_n` o największym obrocie 30 d."""
    elig = [s for s, sd in data.items() if is_eligible(sd, t_ms)]
    if top_n is None or len(elig) <= top_n:
        return sorted(elig)
    vol = sorted(((volume_trailing(data[s], t_ms), s) for s in elig), key=lambda x: (-x[0], x[1]))
    return sorted(s for _, s in vol[:top_n])


def compute_windows(
    data: dict,
    starts: list[int],
    c_rt: float,
    top_n: int | None = TOP_N,
    min_eligible: int = MIN_ELIGIBLE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Per okno: n_eligible, rozmiary koszyków, F, obroty, C, R, trwałość rang.

    Returns:
        (windows, sym_returns): `windows` — jeden wiersz na okno (pominięte okna z
        `n_eligible < min_eligible` mają `skipped=True`); `sym_returns` — zwroty 48h
        wszystkich symboli uniwersum per okno (do korelacji parowych, pomiar 5).
    """
    rows, ret_rows = [], []
    prev_s, prev_l = None, None
    for t in starts:
        uni = universe_at(data, t, top_n)
        if len(uni) < min_eligible:
            rows.append({"t": t, "n_eligible": len(uni), "skipped": True})
            prev_s, prev_l = None, None
            continue
        sig = pd.Series({s: signal_at(data[s], t) for s in uni})
        nxt = pd.Series({s: received_funding(data[s], t) for s in uni})
        ret = pd.Series({s: exit_price(data[s], t) / price_at(data[s], t) - 1.0 for s in uni})
        shorts, longs = select_baskets(sig)
        to_s, to_l = turnover(prev_s, shorts), turnover(prev_l, longs)
        rows.append(
            {
                "t": t,
                "n_eligible": len(uni),
                "skipped": False,
                "n_short": len(shorts),
                "n_long": len(longs),
                "F": float(nxt[shorts].mean() - nxt[longs].mean()),
                "turnover_short": to_s,
                "turnover_long": to_l,
                "C": c_rt * (to_s + to_l),
                "R": float(ret[longs].mean() - ret[shorts].mean()),
                "persistence_spearman": float(sig.rank().corr(nxt.rank())),
            }
        )
        ret_rows.append(ret.rename(t))
        prev_s, prev_l = shorts, longs
    windows = pd.DataFrame(rows)
    sym_returns = pd.DataFrame(ret_rows) if ret_rows else pd.DataFrame()
    return windows, sym_returns


def mean_ci_neff(x: pd.Series, max_lag: int = 50) -> dict:
    """Średnia z CI95, błąd standardowy korygowany przez N_eff (kanoniczne `effective_sample_size`)."""
    x = pd.Series(x).dropna()
    ess = effective_sample_size(x, max_lag=max_lag)
    n_eff = max(1.0, min(float(ess["n_eff"]), float(len(x))))
    se = float(x.std(ddof=1)) / np.sqrt(n_eff)
    m = float(x.mean())
    return {
        "n": int(len(x)),
        "n_eff": n_eff,
        "mean": m,
        "median": float(x.median()),
        "ci_low": m - Z_TWO_SIDED_95 * se,
        "ci_high": m + Z_TWO_SIDED_95 * se,
    }


def dispersion_neff(x: pd.Series, max_lag: int = 50) -> dict:
    """Rozrzut i N_eff szeregu — BEZ średniej w wyniku (warunek „0 wariantów" P2)."""
    x = pd.Series(x).dropna()
    ess = effective_sample_size(x, max_lag=max_lag)
    return {
        "n": int(len(x)),
        "n_eff": max(1.0, min(float(ess["n_eff"]), float(len(x)))),
        "std": float(x.std(ddof=1)),
    }


def required_windows(mu: float, sigma: float) -> float:
    """Okna potrzebne do wykrycia średniej `mu` przy rozrzucie `sigma` (moc 80%, α=5% dwustronnie)."""
    if not np.isfinite(mu) or mu <= 0 or not np.isfinite(sigma):
        return float("inf")
    return float(((Z_TWO_SIDED_95 + Z_POWER_80) * sigma / mu) ** 2)


def avg_pairwise_corr(sym_returns: pd.DataFrame, min_periods: int = 30) -> float:
    """Przeciętna korelacja parowa zwrotów 48h między symbolami (pary z ≥ `min_periods` wspólnymi oknami)."""
    if sym_returns.empty:
        return float("nan")
    corr = sym_returns.corr(min_periods=min_periods).to_numpy()
    iu = np.triu_indices_from(corr, k=1)
    vals = corr[iu]
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()) if len(vals) else float("nan")


def k_effective(k: float, rho: float) -> float:
    """Efektywna liczba niezależnych instrumentów: k / (1 + (k − 1)·ρ̄)."""
    return float(k / (1.0 + (k - 1.0) * rho))
