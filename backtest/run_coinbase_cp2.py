"""
run_coinbase_cp2.py — runda CP2: replikacja CP1 (premia Coinbase → znak pozycji na tydzień) na ETH
i SOL — test GENERALIZACJI tej samej reguły bez retuningu (CLAUDE.md zasada 9). Reguła co do bajtu
z `run_coinbase_cp1.py` (`daily_premium`, `premium_signal`: 7 vs 90 dni, silnik TS1: σ̂ EWMA,
cel 40 %/rok, sufit 3×, 7 faz, realny funding, koszt z config); zmienia się tylko instrument
(premia i perpetual tej samej monety). Konfiguracja ZAMROŻONA w
`runs/2026-09-24_cp2-premia-coinbase-eth-sol/README.md`.

    PYTHONUTF8=1 py -m backtest.run_coinbase_cp2 --moc
    PYTHONUTF8=1 py -m backtest.run_coinbase_cp2

Kryterium per ramię (m = 2, Bonferroni z = 2,241): POZYTYWNY, gdy t_neff > 2,241 ORAZ średnia
> q97,5 H0 (sygnał przesunięty cyklicznie o losową liczbę tygodni, 100 portfeli); NEGATYWNY, gdy
górny kraniec (średnia + 2,241·se) < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.run_coinbase_cp1 import COINBASE as COINBASE_BTC
from backtest.run_coinbase_cp1 import END, SPOT_8H as SPOT_BTC, UNIVERSE_DIR, _shifts
from backtest.run_coinbase_cp1 import daily_premium, premium_signal
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio, signal_sign
from backtest.xs_momentum import daily_funding_panel

Z_M2 = 2.241
LONG_WARMUP_DAYS = 90
SEP = "=" * 104
ARMS = {
    # start = pierwszy dzień miesiąca po rozbiegu 90 dni premii (ETH jak CP1: dane od 2021-01-01)
    "ETH": "2021-05-01",
    # Coinbase SOL-USD od 2021-06-17 → 90 dni rozbiegu → 2021-09-15 → pełny miesiąc od 2021-10-01
    "SOL": "2021-10-01",
}


def _paths(asset: str) -> tuple[str, str, str]:
    return (
        f"data/raw/external/coinbase_{asset}-USD_1d.parquet",
        f"data/raw/{asset}-USDT_8h_20210101T000000Z_20260701T000000Z.parquet",
        f"{asset}USDT",
    )


def load_arm(asset: str):
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    cb_path, spot_path, sym = _paths(asset)
    b = pd.read_parquet(f"{UNIVERSE_DIR}/{sym}_1d.parquet")
    close = pd.DataFrame(
        {sym: b.set_index(pd.to_datetime(b["open_time"], utc=True))["close"].astype(float)}
    )
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    prem = daily_premium(pd.read_parquet(cb_path), pd.read_parquet(spot_path))
    prem = prem[(prem.index >= lo) & (prem.index < end)]
    signs = pd.DataFrame({sym: premium_signal(prem).reindex(close.index)})
    funding = daily_funding_panel(UNIVERSE_DIR)[[sym]]
    start = pd.Timestamp(ARMS[asset], tz="UTC")
    months = [m for m in pd.date_range(ARMS[asset], END, freq="MS", tz="UTC") if m < end]
    members = {m: [sym] for m in months}
    return fee, close, funding, members, signs, prem, start, end


def btc_signal(index: pd.DatetimeIndex) -> pd.Series:
    """Sygnał CP1 BTC (do opisu: czy ramię to ten sam sygnał na innej monecie)."""
    lo = pd.Timestamp("2021-01-01", tz="UTC")
    p = daily_premium(pd.read_parquet(COINBASE_BTC), pd.read_parquet(SPOT_BTC))
    return premium_signal(p[p.index >= lo]).reindex(index)


def run_arm(asset: str, moc: bool) -> None:
    fee, close, funding, members, signs, prem, start, end = load_arm(asset)
    sym = close.columns[0]
    s_eval = signs[sym][signs.index >= start]
    bs = btc_signal(s_eval.index)
    ok = s_eval.notna() & bs.notna()
    print(
        f"  [{asset}] premia {len(prem)} dni ({prem.index.min().date()} → {prem.index.max().date()}), "
        f"mediana {100 * prem.median():+.3f}%; braki w sygnale od startu {int(s_eval.isna().sum())}\n"
        f"  [{asset}] sygnał: long {100 * (s_eval > 0).mean():.1f}% dni; zmiana znaku {100 * (s_eval.diff().abs() > 0).mean():.1f}% dni; "
        f"zgodność z sygnałem CP1 BTC {100 * (s_eval[ok] == bs[ok]).mean():.1f}%; "
        f"z trendem 28 dni {asset} {100 * (s_eval == signal_sign(close)[sym].reindex(s_eval.index)).mean():.1f}%"
    )
    null = []
    for k in _shifts(len(close)):
        a, _ = portfolio(
            close, funding, members, start, end, fee, signs_override=signs, sign_shift_days=k
        )
        a = a.dropna()
        null.append((float(a["net"].mean()), float(a["net"].std(ddof=1))))
    null = np.array(null)
    n_days = len(a)
    if moc:
        sd = float(np.median(null[:, 1]))
        se = max(float(null[:, 0].std(ddof=1)), sd / np.sqrt(n_days))
        hw = Z_M2 * se * DAYS_PER_YEAR
        print(
            f"  [{asset}] dni {n_days}; zmienność H0 {100 * sd * np.sqrt(DAYS_PER_YEAR):.1f}%/rok; half-width (z 2,241) "
            f"{100 * hw:.1f}%/rok = {hw / (sd * np.sqrt(DAYS_PER_YEAR)):.2f} SR; q97,5 H0 {100 * np.quantile(null[:, 0], 0.975) * DAYS_PER_YEAR:+.1f}%/rok"
        )
        return
    avg, phases = portfolio(close, funding, members, start, end, fee, signs_override=signs)
    avg = avg.dropna()
    w = summarize_pnl(avg["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    lo_, hi_ = w["mean"] - Z_M2 * w["se_neff"], w["mean"] + Z_M2 * w["se_neff"]
    q975 = float(np.quantile(null[:, 0], 0.975))
    print(
        f"  [{asset}] netto | {w['n']} dni | {100 * w['mean'] * DAYS_PER_YEAR:+.1f}%/rok [{100 * lo_ * DAYS_PER_YEAR:+.1f}; "
        f"{100 * hi_ * DAYS_PER_YEAR:+.1f}] (z 2,241) | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):.1f}%/rok | t_neff {w['t_neff']:+.2f}; "
        f"H0 q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok, powyżej {100 * (null[:, 0] < w['mean']).mean():.0f}% H0"
    )
    if w["t_neff"] > Z_M2 and w["mean"] > q975:
        v = "POZYTYWNY"
    elif hi_ < 0:
        v = "NEGATYWNY"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM CP2-{asset}: {v}")
    years = pd.to_datetime(avg["date"]).dt.year
    print(
        f"  [{asset}] per rok (Σ netto): "
        + "; ".join(f"{y}: {100 * g['net'].sum():+.1f}%" for y, g in avg.groupby(years))
    )
    print(
        f"  [{asset}] 7 faz (%/rok): "
        + ", ".join(f"{100 * p['net'].mean() * DAYS_PER_YEAR:+.1f}" for p in phases)
    )
    ts, _ = portfolio(close, funding, members, start, end, fee)
    jj = avg.set_index("date")[["net"]].join(
        ts.dropna().set_index("date")[["net"]], rsuffix="_ts", how="inner"
    )
    print(
        f"  [{asset}] opisowo: trend 28 dni na {asset} w tym okresie {100 * jj['net_ts'].mean() * DAYS_PER_YEAR:+.1f}%/rok; "
        f"korelacja z trendem {np.corrcoef(jj['net'], jj['net_ts'])[0, 1]:+.2f}"
    )


def main(argv: list[str]) -> None:
    moc = bool(argv) and argv[0] == "--moc"
    t0 = time.time()
    print(SEP)
    print(
        ("CP2 — RACHUNEK MOCY" if moc else "CP2 — PREMIA COINBASE → KIERUNEK ETH / SOL (tydzień)")
        + "; reguła CP1 bez zmian; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    for asset in ARMS:
        run_arm(asset, moc)
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
