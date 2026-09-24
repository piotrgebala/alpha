"""
run_signal_strength_sc1.py — runda SC1: wielkość pozycji proporcjonalna do SIŁY sygnału zamiast
samego znaku („pewność” reguły), na dwóch kandydatach (m = 2, próg z = 2,241 Bonferroni):
- trend (TS1): z = log(close_t/close_{t−28}) / (σ̂_t · √(28/365));
- premia Coinbase (CP1): z = (średnia premii 7 dni − średnia 90 dni) / (sd premii 90 dni / √7);
s = clip(z, −2, 2) / 2, potem × c, gdzie c = 1 / średnia |s| w okresie oceny liczona WYŁĄCZNIE
z sygnałów (ta sama średnia ekspozycja co wersja znakowa, bez zaglądania w zwroty).
Konfiguracja ZAMROŻONA w `runs/2026-09-24_sc1-sila-sygnalu/README.md`.

    PYTHONUTF8=1 py -m backtest.run_signal_strength_sc1 --moc
    PYTHONUTF8=1 py -m backtest.run_signal_strength_sc1

Kryterium na ramię: różnica parowana dziennego zwrotu netto (siła − znak): POZYTYWNY, gdy
t_neff > 2,241; NEGATYWNY, gdy górny kraniec przedziału (±2,241·se) < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.run_coinbase_cp1 import LONG, SHORT
from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.run_ts_momentum_ts1 import _load as load_ts
from backtest.ts_momentum import DAYS_PER_YEAR, LOOKBACK_DAYS, ewma_vol, portfolio

Z_M2 = 2.241
CLIP = 2.0
SEP = "=" * 104


def strength(z: pd.DataFrame | pd.Series, clip: float = CLIP):
    """s = clip(z, ±clip) / clip — wartości w [−1, 1], znak jak z."""
    return z.clip(-clip, clip) / clip


def ts_strength(close: pd.DataFrame) -> pd.DataFrame:
    lr = np.log(close / close.shift(LOOKBACK_DAYS))
    return strength(lr / (ewma_vol(close) * np.sqrt(LOOKBACK_DAYS / DAYS_PER_YEAR)))


def cp_strength(prem: pd.Series) -> pd.Series:
    m_s = prem.rolling(SHORT, min_periods=SHORT).mean()
    m_l = prem.rolling(LONG, min_periods=LONG).mean()
    sd = prem.rolling(LONG, min_periods=LONG).std()
    return strength((m_s - m_l) / (sd / np.sqrt(SHORT)))


def exposure_scale(s: pd.DataFrame, members: dict, start, end) -> float:
    """c = 1 / średnia |s| u członków w okresie oceny (tylko sygnał)."""
    vals = []
    months = sorted(members)
    for t in s.index[(s.index >= start) & (s.index < end)]:
        m = [x for x in months if x <= t]
        if not m:
            continue
        v = s.loc[t, [c for c in members[m[-1]] if c in s.columns]].to_numpy(dtype=float)
        vals.extend(np.abs(v[np.isfinite(v) & (v != 0)]))
    return 1.0 / float(np.mean(vals))


def _diff(a: pd.DataFrame, b: pd.DataFrame) -> tuple[dict, pd.Series]:
    j = (
        a.dropna()
        .set_index("date")[["net"]]
        .join(b.dropna().set_index("date")[["net"]], rsuffix="_sign", how="inner")
    )
    d = j["net"] - j["net_sign"]
    return summarize_pnl(d, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0), d


def arms():
    fee, close, funding, members, start, end = load_ts("data/raw/universe")
    s_ts = ts_strength(close)
    c_ts = exposure_scale(s_ts, members, start, end)
    fee_c, close_c, fund_c, mem_c, signs_c, prem, start_c, end_c = load_cp()
    s_cp = pd.DataFrame({"BTCUSDT": cp_strength(prem).reindex(close_c.index)})
    c_cp = exposure_scale(s_cp, mem_c, start_c, end_c)
    return [
        ("trend", (close, funding, members, start, end, fee), s_ts * c_ts, None, c_ts),
        ("coinbase", (close_c, fund_c, mem_c, start_c, end_c, fee_c), s_cp * c_cp, signs_c, c_cp),
    ]


def main(argv: list[str]) -> None:
    moc = bool(argv) and argv[0] == "--moc"
    t0 = time.time()
    print(SEP)
    print(
        ("SC1 — RACHUNEK MOCY (rozrzut różnicy)" if moc else "SC1 — SIŁA SYGNAŁU vs ZNAK")
        + "; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    for name, args, strong, signs, c in arms():
        base, _ = portfolio(*args, signs_override=signs)
        alt, _ = portfolio(*args, signs_override=strong)
        w, d = _diff(alt, base)
        hw = Z_M2 * w["se_neff"] * DAYS_PER_YEAR
        print(f"  ramię {name}: c = {c:.2f} (średnia |s| = {1 / c:.2f}); dni {w['n']}")
        if moc:
            print(
                f"    sd różnicy {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):.2f}%/rok → half-width (z 2,241) ±{100 * hw:.2f}%/rok"
            )
            continue
        wa = summarize_pnl(
            alt.dropna()["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0
        )
        wb = summarize_pnl(
            base.dropna()["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0
        )
        lo, hi = w["mean"] - Z_M2 * w["se_neff"], w["mean"] + Z_M2 * w["se_neff"]
        print(
            f"    znak: {100 * wb['mean'] * DAYS_PER_YEAR:+.1f}%/rok (t_neff {wb['t_neff']:+.2f}); "
            f"siła: {100 * wa['mean'] * DAYS_PER_YEAR:+.1f}%/rok (t_neff {wa['t_neff']:+.2f}); "
            f"nominał brutto mediana znak {base.dropna()['gross_notional'].median():.2f}× / siła {alt.dropna()['gross_notional'].median():.2f}×"
        )
        print(
            f"    różnica: {100 * w['mean'] * DAYS_PER_YEAR:+.2f}%/rok [{100 * lo * DAYS_PER_YEAR:+.2f}; {100 * hi * DAYS_PER_YEAR:+.2f}] (z 2,241), t_neff {w['t_neff']:+.2f}"
        )
        v = "POZYTYWNY" if w["t_neff"] > Z_M2 else ("NEGATYWNY" if hi < 0 else "NIEROZSTRZYGNIĘTY")
        print(f"    >>> ODCZYT KRYTERIUM SC1-{name}: {v}")
        years = pd.to_datetime(d.index).year
        print(
            "    różnica per rok (Σ): "
            + "; ".join(f"{y}: {100 * g.sum():+.2f}%" for y, g in d.groupby(years))
        )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
