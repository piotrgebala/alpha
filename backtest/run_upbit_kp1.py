"""
run_upbit_kp1.py — runda KP1: premia koreańska (Upbit) jako sygnał kierunku BTC na tydzień.

premia_d = close Upbit KRW-BTC / (close spot Binance BTC-USDT × USD/KRW) − 1; oba zamknięcia
o 00:00 UTC dnia d+1, kurs USD/KRW = FRED DEXKOUS z dnia ≤ d (noon New York, czyli przed
zamknięciem dnia d; weekendy i święta USA → ostatni dzień roboczy, najwyżej `FX_MAX_STALE_DAYS`).
Liczone zamrożonym `daily_premium` z CP1 na cenie Upbit przeliczonej na dolary. Sygnał i silnik
bez zmian wobec CP1 (`premium_signal` 7 vs 90 dni, silnik TS1: σ̂ EWMA, cel 40 %/rok, sufit 3×,
7 faz tygodniowych, realny funding, koszt z config); kierunek `DIRECTION` i założony efekt
`ASSUMED_SR` ZAMROŻONE w pre-rejestracji `runs/2026-09-25_kp1-premia-koreanska/README.md`.

    PYTHONUTF8=1 py -m backtest.run_upbit_kp1 --profil   # profil danych, bez sygnału i zwrotów
    PYTHONUTF8=1 py -m backtest.run_upbit_kp1 --moc      # zgodność sygnałów + rachunek mocy
    PYTHONUTF8=1 py -m backtest.run_upbit_kp1            # wynik — tylko gdy MIERZALNA (zasada 18)

Kryterium (jedno ramię): POZYTYWNY, gdy t_neff > 1,96 ORAZ średnia > q97,5 H0 (sygnał
przesunięty cyklicznie o losową liczbę tygodni, 100 portfeli); NEGATYWNY, gdy górny kraniec
CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.run_coinbase_cp1 import END, SPOT_8H, START, UNIVERSE_DIR, Z95, _shifts
from backtest.run_coinbase_cp1 import COINBASE, daily_premium, premium_signal
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio, signal_sign
from backtest.xs_momentum import daily_funding_panel

UPBIT = "data/raw/external/upbit_KRW-BTC_1d.parquet"
FX = "data/raw/external/fred_DEXKOUS_1d.parquet"
FX_MAX_STALE_DAYS = 5  # weekend + święto USA; dłuższa dziura = brak premii tego dnia
DIRECTION = 1  # +1: premia ponad normą → long (jak CP1); ustalone w pre-rejestracji
ASSUMED_SR = 0.15  # założony efekt (Sharpe netto) z pre-rejestracji — tylko do linii mocy
SEP = "=" * 104


def fx_asof(days: pd.DatetimeIndex, fx: pd.DataFrame, max_stale_days: int = FX_MAX_STALE_DAYS):
    """
    Kurs USD/KRW dla każdego dnia `days`: ostatnia NIEPUSTA obserwacja z datą ≤ dnia (nigdy
    późniejsza). Starsza niż `max_stale_days` dni → NaN. Zwraca (kurs, wiek obserwacji w dniach).
    """
    obs = fx.dropna(subset=["value"])
    s = pd.Series(
        obs["value"].astype(float).to_numpy(), index=pd.to_datetime(obs["date"], utc=True)
    )
    s = s[~s.index.duplicated(keep="last")].sort_index()
    pos = s.index.searchsorted(days, side="right") - 1
    ok = pos >= 0
    rate = np.full(len(days), np.nan)
    age = np.full(len(days), np.nan)
    rate[ok] = s.to_numpy()[pos[ok]]
    age[ok] = (days[ok] - s.index[pos[ok]]).days
    rate[age > max_stale_days] = np.nan
    return pd.Series(rate, index=days), pd.Series(age, index=days)


def korea_premium(upbit: pd.DataFrame, spot8h: pd.DataFrame, fx: pd.DataFrame) -> pd.Series:
    """Premia dzienna Upbit: (close KRW / kurs USD/KRW dnia ≤ d) / close spot Binance − 1."""
    up = upbit.set_index(pd.to_datetime(upbit["open_time"], utc=True))["close"].astype(float)
    rate, _ = fx_asof(up.index, fx)
    usd = (up / rate).dropna()
    return daily_premium(pd.DataFrame({"open_time": usd.index, "close": usd.to_numpy()}), spot8h)


def _window(s: pd.Series) -> pd.Series:
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    return s[(s.index >= lo) & (s.index < end)]


def _load():
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    b = pd.read_parquet(f"{UNIVERSE_DIR}/BTCUSDT_1d.parquet")
    close = pd.DataFrame(
        {"BTCUSDT": b.set_index(pd.to_datetime(b["open_time"], utc=True))["close"].astype(float)}
    )
    close = close.loc[_window(close["BTCUSDT"]).index]
    spot = pd.read_parquet(SPOT_8H)
    prem = _window(korea_premium(pd.read_parquet(UPBIT), spot, pd.read_parquet(FX)))
    cb = _window(daily_premium(pd.read_parquet(COINBASE), spot))
    sig = (DIRECTION * premium_signal(prem)).reindex(close.index)
    signs = pd.DataFrame({"BTCUSDT": sig})
    cp1 = premium_signal(cb).reindex(close.index)
    funding = daily_funding_panel(UNIVERSE_DIR)[["BTCUSDT"]]
    end = pd.Timestamp(END, tz="UTC")
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    members = {m: ["BTCUSDT"] for m in months}
    return fee, close, funding, members, signs, prem, cb, cp1, pd.Timestamp(START, tz="UTC"), end


def profile() -> None:
    """Profil danych (data:explore-data): luki, duplikaty, kurs, rozkład premii — bez sygnału."""
    up = pd.read_parquet(UPBIT)
    fx = pd.read_parquet(FX)
    t = pd.to_datetime(up["open_time"], utc=True)
    full = pd.date_range(t.min(), t.max(), freq="D", tz="UTC")
    print(
        f"  Upbit KRW-BTC 1d: {len(up)} wierszy, {t.min().date()} → {t.max().date()}, "
        f"brakujące dni {len(full.difference(t))}, duplikaty {int(t.duplicated().sum())}, "
        f"close ≤ 0: {int((up['close'] <= 0).sum())}, dni z wolumenem 0: {int((up['volume'] == 0).sum())}"
    )
    fxd = pd.to_datetime(fx["date"], utc=True)
    print(
        f"  FRED DEXKOUS: {len(fx)} dni roboczych, {fxd.min().date()} → {fxd.max().date()}, "
        f"braki (święta) {int(fx['value'].isna().sum())}, zakres {fx['value'].min():.1f}–{fx['value'].max():.1f} KRW/USD, "
        f"max zmiana dzienna {100 * fx['value'].dropna().pct_change().abs().max():.2f}%"
    )
    days = _window(pd.Series(1.0, index=t)).index
    rate, age = fx_asof(days, fx)
    print(
        f"  kurs dla dni 2021-01-01 → {END}: wiek obserwacji mediana {age.median():.0f} d, max {age.max():.0f} d, "
        f"dni bez kursu (> {FX_MAX_STALE_DAYS} d) {int(rate.isna().sum())}"
    )
    spot = pd.read_parquet(SPOT_8H)
    p = _window(korea_premium(up, spot, fx))
    cb = _window(daily_premium(pd.read_parquet(COINBASE), spot))
    q = p.quantile([0.01, 0.05, 0.5, 0.95, 0.99])
    d = p.diff().abs()
    print(
        f"  premia koreańska: {len(p)} dni ({p.index.min().date()} → {p.index.max().date()}); "
        f"p1 / p5 / mediana / p95 / p99: {' / '.join(f'{100 * v:+.2f}%' for v in q)}\n"
        f"  min {100 * p.min():+.2f}% ({p.idxmin().date()}), max {100 * p.max():+.2f}% ({p.idxmax().date()}); "
        f"dni z |premią| > 10 %: {int((p.abs() > 0.10).sum())}; max |zmiana dzienna| {100 * d.max():.2f} pp ({d.idxmax().date()})"
    )
    print(
        "  mediana premii per rok: "
        + "; ".join(f"{y}: {100 * g.median():+.2f}%" for y, g in p.groupby(p.index.year))
    )
    j = pd.concat({"kr": p, "cb": cb}, axis=1).dropna()
    print(
        f"  wobec premii Coinbase (CP1), {len(j)} wspólnych dni: korelacja poziomów {j['kr'].corr(j['cb']):+.2f}, "
        f"zmian dziennych {j['kr'].diff().corr(j['cb'].diff()):+.2f}"
    )


def run(moc: bool) -> None:
    fee, close, funding, members, signs, prem, cb, cp1, start, end = _load()
    s_eval = signs["BTCUSDT"][signs.index >= start]
    c_eval = cp1.reindex(s_eval.index)
    ok = s_eval.notna() & c_eval.notna()
    print(
        f"  premia: {len(prem)} dni ({prem.index.min().date()} → {prem.index.max().date()}); "
        f"braki w sygnale od startu: {int(s_eval.isna().sum())}\n"
        f"  sygnał (kierunek {DIRECTION:+d}): long {100 * (s_eval > 0).mean():.1f}% dni, zmiana znaku "
        f"{100 * (s_eval.diff().abs() > 0).mean():.1f}% dni; zgodność z sygnałem CP1 (Coinbase) "
        f"{100 * (s_eval[ok] == DIRECTION * c_eval[ok]).mean():.1f}% na {int(ok.sum())} dniach; "
        f"z trendem 28 dni na BTC {100 * (s_eval == signal_sign(close)['BTCUSDT'].reindex(s_eval.index)).mean():.1f}%"
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
    q975 = float(np.quantile(null[:, 0], 0.975))
    if moc:
        sd = float(np.median(null[:, 1]))
        se = max(float(null[:, 0].std(ddof=1)), sd / np.sqrt(n_days))
        vol = sd * np.sqrt(DAYS_PER_YEAR)
        hw = Z95 * se * DAYS_PER_YEAR
        se_sr = hw / Z95 / vol
        print(
            f"  dni {n_days}; zmienność H0 {100 * vol:.1f}%/rok; half-width 95% {100 * hw:.1f}%/rok "
            f"= {hw / vol:.2f} SR; q97,5 H0 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok\n"
            f"  moc przy założonym efekcie SR {ASSUMED_SR:.2f} (≈ {100 * ASSUMED_SR * vol:+.1f}%/rok): "
            f"{100 * norm.sf(Z95 - ASSUMED_SR / se_sr):.0f}%; przy SR 0,9 (wynik CP1): {100 * norm.sf(Z95 - 0.9 / se_sr):.0f}%"
        )
        return
    avg, phases = portfolio(close, funding, members, start, end, fee, signs_override=signs)
    avg = avg.dropna()
    w = summarize_pnl(avg["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    print(
        f"  KP1 netto | {w['n']} dni | {100 * w['mean'] * DAYS_PER_YEAR:+.1f}%/rok [{100 * w['ci_low'] * DAYS_PER_YEAR:+.1f}; "
        f"{100 * w['ci_high'] * DAYS_PER_YEAR:+.1f}] | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):.1f}%/rok | t_neff {w['t_neff']:+.2f}; "
        f"H0 q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok, KP1 powyżej {100 * (null[:, 0] < w['mean']).mean():.0f}% H0"
    )
    if w["t_neff"] > Z95 and w["mean"] > q975:
        v = "POZYTYWNY"
    elif w["ci_high"] < 0:
        v = "NEGATYWNY"
    else:
        v = "NIEROZSTRZYGNIĘTY"
    print(f"  >>> ODCZYT KRYTERIUM KP1: {v}")
    years = pd.to_datetime(avg["date"]).dt.year
    print(
        "  per rok (Σ netto): "
        + "; ".join(f"{y}: {100 * g['net'].sum():+.1f}%" for y, g in avg.groupby(years))
    )
    print(
        "  7 faz (%/rok): "
        + ", ".join(f"{100 * p['net'].mean() * DAYS_PER_YEAR:+.1f}" for p in phases)
    )


def main(argv: list[str]) -> None:
    mode = argv[0] if argv else ""
    t0 = time.time()
    title = {
        "--profil": "KP1 — PROFIL DANYCH (bez sygnału i zwrotów)",
        "--moc": "KP1 — ZGODNOŚĆ SYGNAŁÓW I RACHUNEK MOCY",
    }.get(mode, "KP1 — PREMIA KOREAŃSKA → KIERUNEK BTC (tydzień)")
    print(SEP)
    print(title + "; konfiguracja ZAMROŻONA")
    print(SEP)
    if mode == "--profil":
        profile()
    else:
        run(moc=mode == "--moc")
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
