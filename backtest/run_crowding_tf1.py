"""
run_crowding_tf1.py — runda TF1: reguła TS1 z FILTREM TŁOKU (funding). Pozycja zgodna z trendem
jest zerowana, gdy strona, którą zajmuje, jest przeładowana lewarem: long przy sumie fundingu
z 7 dni > F_HI (longi płacą ~3× normalnej stawki), short przy sumie < −F_HI. N bez zmian
(ekspozycja maleje). Konfiguracja ZAMROŻONA w `runs/2026-09-24_tf1-trend-filtr-tloku/README.md`.

    PYTHONUTF8=1 py -m backtest.run_crowding_tf1 --moc   # udział filtrowanych pozycji + rozrzut różnicy
    PYTHONUTF8=1 py -m backtest.run_crowding_tf1

Kryterium (jedno ramię): różnica parowana dziennego zwrotu netto TF1 − TS1: POZYTYWNY, gdy
t_neff > 1,96; NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio, signal_sign
from backtest.xs_momentum import daily_funding_panel

UNIVERSE_DIR = "data/raw/universe"
F_HI = 0.0063  # 7 dni × 3 rozliczenia × 0,03 % = 3× bazowej stawki 0,01 %/8h
FUND_DAYS = 7
Z95 = 1.959964
SEP = "=" * 104


def funding_sum(funding_daily: pd.DataFrame, days: int = FUND_DAYS) -> pd.DataFrame:
    """Suma stawek z `days` dni ≤ t (dzień t włącznie — rozliczenia do 16:00 t są znane przed close t)."""
    return funding_daily.sort_index().rolling(days, min_periods=days).sum()


def make_keep_fn(fsum: pd.DataFrame, f_hi: float = F_HI):
    def keep(t, syms, sgn):
        row = (
            fsum.reindex(columns=syms).loc[t] if t in fsum.index else pd.Series(np.nan, index=syms)
        )
        f = row.to_numpy(dtype=float)
        s = np.asarray(sgn, dtype=float)
        crowded = ((s > 0) & (f > f_hi)) | ((s < 0) & (f < -f_hi))
        return np.where(crowded, 0.0, 1.0)

    return keep


def _load():
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, volume = load_universe(UNIVERSE_DIR)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    funding = daily_funding_panel(UNIVERSE_DIR)
    months = [m for m in pd.date_range("2021-02-01", "2026-07-01", freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, months)
    return fee, close, funding, members, pd.Timestamp("2021-02-01", tz="UTC"), end


def _filtered_share(close, funding, members, start, end):
    """Udział (członek × formowanie) wyzerowanych przez filtr — z fundingu i znaku, bez zwrotów."""
    s = signal_sign(close)
    fsum = funding_sum(funding.reindex(index=close.index, columns=close.columns).fillna(0.0))
    keep = make_keep_fn(fsum)
    tot = filt = 0
    for t in close.index[(close.index >= start) & (close.index < end)]:
        m = max(x for x in members if x <= t)
        syms = [c for c in members[m] if c in s.columns]
        sg = s.loc[t, syms].to_numpy(dtype=float)
        ok = np.isfinite(sg) & (sg != 0)
        k = keep(t, syms, np.nan_to_num(sg))
        tot += int(ok.sum())
        filt += int(((k == 0) & ok).sum())
    return filt / tot


def run(moc: bool) -> None:
    t0 = time.time()
    fee, close, funding, members, start, end = _load()
    fsum = funding_sum(funding.reindex(index=close.index, columns=close.columns).fillna(0.0))
    share = _filtered_share(close, funding, members, start, end)
    print(SEP)
    print(
        ("TF1 — RACHUNEK MOCY" if moc else "TF1 — TREND TS1 Z FILTREM TŁOKU (funding 7 dni)")
        + "; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"  filtr: long zerowany przy Σ funding 7 dni > {100 * F_HI:.2f}%, short przy < −{100 * F_HI:.2f}%; "
        f"udział pozycji (członek×dzień) wyzerowanych: {100 * share:.1f}%"
    )
    base, _ = portfolio(close, funding, members, start, end, fee)
    tf1, _ = portfolio(close, funding, members, start, end, fee, keep_fn=make_keep_fn(fsum))
    j = (
        tf1.dropna()
        .set_index("date")[["net", "gross_notional"]]
        .join(base.dropna().set_index("date")[["net"]], rsuffix="_ts1", how="inner")
    )
    diff = j["net"] - j["net_ts1"]
    wd = summarize_pnl(diff, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    if moc:
        print(
            f"  dni {wd['n']}; sd różnicy {100 * wd['sd'] * np.sqrt(DAYS_PER_YEAR):.2f}%/rok; se (N_eff) "
            f"{100 * wd['se_neff'] * DAYS_PER_YEAR:.2f}%/rok → half-width 95% ±{100 * Z95 * wd['se_neff'] * DAYS_PER_YEAR:.2f}%/rok"
        )
        print(f"  czas: {time.time() - t0:.0f}s")
        return
    for name, x in (("TF1 netto", j["net"]), ("TS1 netto", j["net_ts1"]), ("TF1 − TS1", diff)):
        w = summarize_pnl(x, periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
        print(
            f"  {name:>10} | {100 * w['mean'] * DAYS_PER_YEAR:+6.2f}%/rok [{100 * w['ci_low'] * DAYS_PER_YEAR:+6.2f}; "
            f"{100 * w['ci_high'] * DAYS_PER_YEAR:+6.2f}] | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):5.1f}%/rok | t_neff {w['t_neff']:+5.2f}"
        )
    if wd["t_neff"] > Z95:
        v = "POZYTYWNY — filtr tłoku poprawia trend"
    elif wd["ci_high"] < 0:
        v = "NEGATYWNY — filtr tłoku pogarsza trend"
    else:
        v = "NIEROZSTRZYGNIĘTY — różnica nieodróżnialna od zera"
    print(f"  >>> ODCZYT KRYTERIUM TF1: {v}")
    years = pd.to_datetime(j.index).year
    print(
        "  różnica per rok (Σ): "
        + "; ".join(f"{y}: {100 * g.sum():+.2f}%" for y, g in diff.groupby(years))
    )
    print(f"  nominał brutto TF1 mediana {j['gross_notional'].median():.2f}× (TS1 ~0,41×)")
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    run(bool(sys.argv[1:]) and sys.argv[1] == "--moc")
