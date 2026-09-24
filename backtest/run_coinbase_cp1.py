"""
run_coinbase_cp1.py — runda CP1: premia Coinbase jako sygnał kierunku BTC na horyzoncie tygodnia.
premia_d = close Coinbase BTC-USD / close Binance spot BTC-USDT − 1 (oba zamknięcia o 00:00 UTC
dnia d+1). Sygnał na zamknięciu d = znak(średnia premii z 7 dni − średnia z 90 dni) — odchylenie
od własnej normy usuwa stały składnik kursu USDT/USD. Pozycja w perpetualu BTCUSDT, silnik TS1
(σ̂ EWMA, cel 40 %/rok, sufit 3×, 7 faz tygodniowych, realny funding, koszty).
Konfiguracja ZAMROŻONA w `runs/2026-09-24_cp1-premia-coinbase/README.md`.

    PYTHONUTF8=1 py -m backtest.run_coinbase_cp1 --moc
    PYTHONUTF8=1 py -m backtest.run_coinbase_cp1

Kryterium: POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0 (sygnał przesunięty w czasie);
NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio, signal_sign
from backtest.xs_momentum import daily_funding_panel

COINBASE = "data/raw/external/coinbase_BTC-USD_1d.parquet"
SPOT_8H = "data/raw/BTC-USDT_8h_20210101T000000Z_20260701T000000Z.parquet"
UNIVERSE_DIR = "data/raw/universe"
START = "2021-05-01"  # rozbieg 90 dni średniej premii od 2021-01-01 (zasada 20)
END = "2026-07-01"
SHORT, LONG = 7, 90
N_SIM = 100
Z95 = 1.959964
SEP = "=" * 104


def daily_premium(cb: pd.DataFrame, spot8h: pd.DataFrame) -> pd.Series:
    """Premia dzienna: zamknięcie Coinbase dnia d / zamknięcie spot Binance (świeca 8h z 16:00 d) − 1."""
    cb_close = cb.set_index(pd.to_datetime(cb["open_time"], utc=True))["close"].astype(float)
    s = spot8h.copy()
    s["open_time"] = pd.to_datetime(
        s["open_time"] if "open_time" in s else s["timestamp"], utc=True
    )
    s16 = s[s["open_time"].dt.hour == 16]
    last = s16.set_index(s16["open_time"].dt.floor("D"))["close"].astype(float)
    idx = cb_close.index.intersection(last.index)
    return (cb_close.loc[idx] / last.loc[idx] - 1.0).sort_index()


def premium_signal(prem: pd.Series, short: int = SHORT, long: int = LONG) -> pd.Series:
    """znak(średnia z `short` dni − średnia z `long` dni), dane ≤ d."""
    return np.sign(
        prem.rolling(short, min_periods=short).mean() - prem.rolling(long, min_periods=long).mean()
    )


def _load():
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    b = pd.read_parquet(f"{UNIVERSE_DIR}/BTCUSDT_1d.parquet")
    close = pd.DataFrame(
        {"BTCUSDT": b.set_index(pd.to_datetime(b["open_time"], utc=True))["close"].astype(float)}
    )
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    prem = daily_premium(pd.read_parquet(COINBASE), pd.read_parquet(SPOT_8H))
    prem = prem[(prem.index >= lo) & (prem.index < end)]
    sig = premium_signal(prem).reindex(close.index)
    signs = pd.DataFrame({"BTCUSDT": sig})
    funding = daily_funding_panel(UNIVERSE_DIR)[["BTCUSDT"]]
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    members = {m: ["BTCUSDT"] for m in months}
    return fee, close, funding, members, signs, prem, pd.Timestamp(START, tz="UTC"), end


def _shifts(n_days: int) -> list[int]:
    rng = np.random.default_rng(0)
    return [int(7 * rng.integers(8, n_days // 7 - 8)) for _ in range(N_SIM)]


def run(moc: bool) -> None:
    t0 = time.time()
    fee, close, funding, members, signs, prem, start, end = _load()
    print(SEP)
    print(
        ("CP1 — RACHUNEK MOCY" if moc else "CP1 — PREMIA COINBASE → KIERUNEK BTC (tydzień)")
        + "; konfiguracja ZAMROŻONA"
    )
    print(SEP)
    s_eval = signs["BTCUSDT"][(signs.index >= start)]
    print(
        f"  premia: {len(prem)} dni ({prem.index.min().date()} → {prem.index.max().date()}), mediana {100 * prem.median():+.3f}%, "
        f"p5/p95 [{100 * prem.quantile(0.05):+.3f}%; {100 * prem.quantile(0.95):+.3f}%], braki w sygnale od startu: {int(s_eval.isna().sum())}\n"
        f"  sygnał: udział dni long {100 * (s_eval > 0).mean():.1f}%, zmiana znaku {100 * (s_eval.diff().abs() > 0).mean():.1f}% dni; "
        f"zgodność z trendem 28 dni (TS1 na BTC): {100 * (s_eval == signal_sign(close)['BTCUSDT'].reindex(s_eval.index)).mean():.1f}%"
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
        hw = Z95 * se * DAYS_PER_YEAR
        print(
            f"  dni {n_days}; zmienność H0 {100 * sd * np.sqrt(DAYS_PER_YEAR):.1f}%/rok; half-width 95% {100 * hw:.1f}%/rok "
            f"= {hw / (sd * np.sqrt(DAYS_PER_YEAR)):.2f} SR; q97,5 H0 {100 * np.quantile(null[:, 0], 0.975) * DAYS_PER_YEAR:+.1f}%/rok"
        )
        print(f"  czas: {time.time() - t0:.0f}s")
        return
    avg, phases = portfolio(close, funding, members, start, end, fee, signs_override=signs)
    avg = avg.dropna()
    w = summarize_pnl(avg["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    q975 = float(np.quantile(null[:, 0], 0.975))
    print(
        f"  CP1 netto | {w['n']} dni | {100 * w['mean'] * DAYS_PER_YEAR:+.1f}%/rok [{100 * w['ci_low'] * DAYS_PER_YEAR:+.1f}; "
        f"{100 * w['ci_high'] * DAYS_PER_YEAR:+.1f}] | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):.1f}%/rok | t_neff {w['t_neff']:+.2f}; "
        f"H0 q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok, CP1 powyżej {100 * (null[:, 0] < w['mean']).mean():.0f}% H0"
    )
    if w["t_neff"] > Z95 and w["mean"] > q975:
        v = "POZYTYWNY"
    elif w["ci_high"] < 0:
        v = "NEGATYWNY"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM CP1: {v}")
    years = pd.to_datetime(avg["date"]).dt.year
    print(
        "  per rok (Σ netto): "
        + "; ".join(f"{y}: {100 * g['net'].sum():+.1f}%" for y, g in avg.groupby(years))
    )
    print(
        "  7 faz (%/rok): "
        + ", ".join(f"{100 * p['net'].mean() * DAYS_PER_YEAR:+.1f}" for p in phases)
    )
    ts, _ = portfolio(close, funding, members, start, end, fee)
    jj = avg.set_index("date")[["net"]].join(
        ts.dropna().set_index("date")[["net"]], rsuffix="_ts", how="inner"
    )
    print(
        f"  opisowo: trend 28 dni na BTC w tym okresie {100 * jj['net_ts'].mean() * DAYS_PER_YEAR:+.1f}%/rok; "
        f"korelacja CP1 z trendem {np.corrcoef(jj['net'], jj['net_ts'])[0, 1]:+.2f}"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    run(bool(sys.argv[1:]) and sys.argv[1] == "--moc")
