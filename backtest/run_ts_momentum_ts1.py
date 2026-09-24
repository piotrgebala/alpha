"""
run_ts_momentum_ts1.py — runda TS1: momentum w czasie (TSMOM) na koszyku top-20 perpetuali USDT-M
point-in-time od 2021 (zasada 20). Konfiguracja ZAMROŻONA w pre-rejestracji
(`runs/2026-09-24_ts1-trend-koszyk/README.md`).

    PYTHONUTF8=1 py -m backtest.run_ts_momentum_ts1 --moc [n_sim]   # tylko H0 (rachunek mocy)
    PYTHONUTF8=1 py -m backtest.run_ts_momentum_ts1                  # pełny przebieg

Kryterium (jedno ramię, m = 1): POZYTYWNY, gdy t_neff > 1,96 dziennego zwrotu netto (średnia
7 faz) ORAZ średnia > 97,5 percentyla średnich z H0 (prawdziwe znaki przesunięte cyklicznie
o losową liczbę tygodni — ta sama trwałość i zgodność między monetami, te same wagi i koszty);
NEGATYWNY, gdy górny kraniec CI 95 % < 0; inaczej NIEROZSTRZYGNIĘTY.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe, monthly_members
from backtest.ts_momentum import (
    CAP,
    DAYS_PER_YEAR,
    EWMA_COM,
    HOLD_DAYS,
    LOOKBACK_DAYS,
    PHASES,
    TARGET_VOL,
    MarkovSigns,
    always_long,
    portfolio,
    signal_sign,
)
from backtest.xs_momentum import daily_funding_panel

UNIVERSE_DIR = "data/raw/universe"
DATA_START = "2021-01-01"  # zasada 20
FIRST_MONTH = "2021-02-01"  # pierwszy miesiąc z pełnym oknem obrotu i sygnału wewnątrz 2021
END = "2026-07-01"
N_SIM_DEFAULT = 100
Z95 = 1.959964
SEP = "=" * 104


def _load(universe_dir: str):
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, volume = load_universe(universe_dir)
    lo, end = pd.Timestamp(DATA_START, tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    funding = daily_funding_panel(universe_dir)
    month_starts = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, month_starts)
    return fee, close, funding, members, pd.Timestamp(FIRST_MONTH, tz="UTC"), end


def _p_flip(close: pd.DataFrame, members, start, end) -> float:
    """Częstość zmiany znaku sygnału między kolejnymi formowaniami u członków (trwałość, nie wynik)."""
    s = signal_sign(close)
    days = s.index[(s.index >= start) & (s.index < end)][::HOLD_DAYS]
    flips, total = 0, 0
    month_starts = sorted(members)
    for a, b in zip(days[:-1], days[1:], strict=False):
        m = [x for x in month_starts if x <= a]
        if not m:
            continue
        syms = [c for c in members[m[-1]] if c in s.columns]
        sa, sb = s.loc[a, syms], s.loc[b, syms]
        ok = sa.notna() & sb.notna() & (sa != 0) & (sb != 0)
        flips += int((sa[ok] != sb[ok]).sum())
        total += int(ok.sum())
    return flips / total


def _shifts(n_days: int, n_sim: int) -> list[int]:
    """Przesunięcia H0: wielokrotności 7 dni, co najmniej 8 tygodni od zera w obie strony."""
    rng = np.random.default_rng(0)
    weeks = n_days // 7
    return [int(7 * rng.integers(8, weeks - 8)) for _ in range(n_sim)]


def _null(close, funding, members, start, end, fee, n_sim):
    out = []
    for k in _shifts(len(close), n_sim):
        avg, _ = portfolio(close, funding, members, start, end, fee, sign_shift_days=k)
        avg = avg.dropna()
        out.append((float(avg["net"].mean()), float(avg["net"].std(ddof=1))))
    return np.array(out)


def _header(fee, close, members, start, end, p_flip):
    n_syms = len({s for v in members.values() for s in v})
    print(
        f"dane   : uniwersum {close.shape[1]} symboli 1d ({close.index.min().date()} → {close.index.max().date()}, zasada 20), "
        f"{len(members)} koszyków miesięcznych top-20 po obrocie ({n_syms} różnych symboli)\n"
        f"reguła : s = znak zwrotu {LOOKBACK_DAYS} dni, σ̂ = √(365·EWMA(r², com={EWMA_COM})), w = s·min({CAP:g}, {TARGET_VOL:.2f}/σ̂)/N; "
        f"formowanie co {HOLD_DAYS} dni, {PHASES} faz po 1/{PHASES} kapitału; koszt {100 * fee:.3f}% × obrót; funding realny (long płaci)\n"
        f"okres  : {start.date()} → {end.date()}; trwałość sygnału p_flip = {p_flip:.3f}; H0 kanoniczne: znaki przesunięte cyklicznie o losową liczbę tygodni\n"
    )


def run_power(universe_dir: str, n_sim: int) -> None:
    t0 = time.time()
    fee, close, funding, members, start, end = _load(universe_dir)
    p_flip = _p_flip(close, members, start, end)
    print(SEP)
    print(f"TS1 — RACHUNEK MOCY: {n_sim} portfeli H0 (bez patrzenia na wynik reguły)")
    print(SEP)
    _header(fee, close, members, start, end, p_flip)
    rng = np.random.default_rng(0)
    indep = []
    for _ in range(n_sim):
        avg, _ = portfolio(
            close, funding, members, start, end, fee, lambda: MarkovSigns(p_flip), rng
        )
        indep.append((float(avg["net"].mean()), float(avg["net"].std(ddof=1))))
    shifted = _null(close, funding, members, start, end, fee, n_sim)
    n_days = len(avg)
    for name, arr in (
        ("H0 niezależne losowe znaki (odrzucone jako za wąskie)", np.array(indep)),
        ("H0 KANONICZNE: znaki przesunięte w czasie", shifted),
    ):
        means, sd = arr[:, 0], float(np.median(arr[:, 1]))
        se = float(means.std(ddof=1))
        se_a = sd / np.sqrt(n_days)
        hw = Z95 * max(se, se_a) * DAYS_PER_YEAR
        print(f"  {name}:")
        print(
            f"    dni {n_days}; sd dzienna netto (mediana) {100 * sd * np.sqrt(DAYS_PER_YEAR):.1f}%/rok; "
            f"średnia {100 * means.mean() * DAYS_PER_YEAR:+.2f}%/rok; se empiryczne {100 * se * DAYS_PER_YEAR:.2f}%/rok "
            f"(analityczne {100 * se_a * DAYS_PER_YEAR:.2f}%/rok, ×{se / se_a:.2f})"
        )
        print(
            f"    half-width 95% = {100 * hw:.1f}%/rok = {hw / (sd * np.sqrt(DAYS_PER_YEAR)):.2f} SR; "
            f"q2,5 {100 * np.quantile(means, 0.025) * DAYS_PER_YEAR:+.1f}%/rok, q97,5 {100 * np.quantile(means, 0.975) * DAYS_PER_YEAR:+.1f}%/rok"
        )
    print(f"  czas: {time.time() - t0:.0f}s")


def _verdict(w: dict, q975: float) -> str:
    if w["t_neff"] > Z95 and w["mean"] > q975:
        return "POZYTYWNY — t_neff > 1,96 ORAZ średnia ponad 97,5 percentylem H0"
    if w["ci_high"] < 0:
        return "NEGATYWNY — górny kraniec CI 95% średniego zwrotu netto poniżej zera"
    return "NIEROZSTRZYGNIĘTY — nie spełnia żadnego z warunków"


def _curve(net: pd.Series, k: float) -> tuple[float, float]:
    eq = np.cumprod(1.0 + k * net.to_numpy())
    if np.any(eq <= 0):
        return -1.0, 1.0
    years = len(net) / DAYS_PER_YEAR
    cagr = eq[-1] ** (1 / years) - 1
    dd = float(np.max(1 - eq / np.maximum.accumulate(eq)))
    return float(cagr), dd


def _row(name: str, w: dict) -> str:
    return (
        f"  {name:>14} | {w['n']:5d} | {100 * w['mean'] * DAYS_PER_YEAR:+7.1f}%/rok "
        f"[{100 * w['ci_low'] * DAYS_PER_YEAR:+6.1f}; {100 * w['ci_high'] * DAYS_PER_YEAR:+6.1f}] | "
        f"mediana/dzień {100 * w['median']:+.3f}% | sd {100 * w['sd'] * np.sqrt(DAYS_PER_YEAR):5.1f}%/rok | "
        f"t {w['t']:+5.2f} | N_eff {w['n_eff']:6.0f} | t_neff {w['t_neff']:+5.2f}"
    )


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--moc":
        run_power(UNIVERSE_DIR, int(argv[1]) if len(argv) > 1 else N_SIM_DEFAULT)
        return
    t0 = time.time()
    fee, close, funding, members, start, end = _load(UNIVERSE_DIR)
    p_flip = _p_flip(close, members, start, end)
    print(SEP)
    print("TS1 — MOMENTUM W CZASIE (TSMOM) NA KOSZYKU TOP-20, long i short; konfiguracja ZAMROŻONA")
    print(SEP)
    _header(fee, close, members, start, end, p_flip)

    avg, phases = portfolio(close, funding, members, start, end, fee)
    avg = avg.dropna()
    w = summarize_pnl(avg["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    wg = summarize_pnl(avg["gross"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0)
    null = _null(close, funding, members, start, end, fee, N_SIM_DEFAULT)[:, 0]
    q025, q975 = np.quantile(null, [0.025, 0.975])

    print("1. KRYTERIUM — dzienny zwrot netto portfela (średnia 7 faz, % kapitału), CI z N_eff")
    print(_row("TS1 netto", w))
    print(_row("TS1 brutto", wg))
    rank = float((null < w["mean"]).mean())
    print(
        f"  H0 ({len(null)} portfeli ze znakami przesuniętymi w czasie): średnia {100 * null.mean() * DAYS_PER_YEAR:+.1f}%/rok, "
        f"q2,5 {100 * q025 * DAYS_PER_YEAR:+.1f}%, q97,5 {100 * q975 * DAYS_PER_YEAR:+.1f}%/rok; TS1 powyżej {100 * rank:.0f}% portfeli H0"
    )
    print(f"  >>> ODCZYT KRYTERIUM TS1: {_verdict(w, q975)}")

    print("\n2. DEKOMPOZYCJA (sumy za próbę, % kapitału) i ekspozycja")
    print(
        f"  Σ brutto {100 * avg['gross'].sum():+.1f}% | Σ funding {100 * avg['funding'].sum():+.1f}% | "
        f"Σ koszt {100 * avg['cost'].sum():.1f}% | Σ netto {100 * avg['net'].sum():+.1f}% | "
        f"obrót {avg['turnover'].sum() / (len(avg) / DAYS_PER_YEAR):.1f} kapitału/rok\n"
        f"  nominał brutto: mediana {avg['gross_notional'].median():.2f}× (p10 {avg['gross_notional'].quantile(0.1):.2f}, p90 {avg['gross_notional'].quantile(0.9):.2f}); "
        f"nominał netto (long − short): średnia {avg['net_notional'].mean():+.2f}×, udział dni netto-long {100 * (avg['net_notional'] > 0).mean():.0f}%"
    )
    print(
        f"  rozkład dzienny netto: p05 {100 * avg['net'].quantile(0.05):+.2f}%, p50 {100 * avg['net'].median():+.3f}%, "
        f"p95 {100 * avg['net'].quantile(0.95):+.2f}%, min {100 * avg['net'].min():+.2f}%, max {100 * avg['net'].max():+.2f}%; "
        f"skośność {avg['net'].skew():+.2f}"
    )
    years = pd.to_datetime(avg["date"]).dt.year
    print(
        f"  {'rok':>6} | {'dni':>4} | {'Σ netto':>8} | {'Σ funding':>9} | {'sd/rok':>7} | {'nominał netto':>13}"
    )
    for y, g in avg.groupby(years):
        print(
            f"  {y:6d} | {len(g):4d} | {100 * g['net'].sum():+7.1f}% | {100 * g['funding'].sum():+8.1f}% | "
            f"{100 * g['net'].std() * np.sqrt(DAYS_PER_YEAR):6.1f}% | {g['net_notional'].mean():+12.2f}×"
        )
    ph_ann = [100 * p["net"].mean() * DAYS_PER_YEAR for p in phases]
    print(
        f"  7 faz osobno (%/rok): {', '.join(f'{x:+.1f}' for x in ph_ann)} — rozrzut {max(ph_ann) - min(ph_ann):.1f} pp"
    )

    print(
        "\n3. OPISOWO (0 wariantów) — zawsze long z tymi samymi wagami, różnica parowana, sam BTC"
    )
    lg, _ = portfolio(close, funding, members, start, end, fee, lambda: always_long)
    lg = lg.dropna().set_index("date")
    joined = avg.set_index("date")[["net"]].join(lg[["net"]], rsuffix="_long", how="inner")
    print(
        _row(
            "zawsze long",
            summarize_pnl(
                joined["net_long"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0
            ),
        )
    )
    print(
        _row(
            "TS1 − long",
            summarize_pnl(
                joined["net"] - joined["net_long"],
                periods_per_year=DAYS_PER_YEAR,
                capital_per_notional=1.0,
            ),
        )
    )
    corr = float(np.corrcoef(joined["net"], joined["net_long"])[0, 1])
    print(f"  korelacja TS1 z zawsze-long: {corr:+.2f}")
    btc_members = {m: ["BTCUSDT"] for m in members}
    btc, _ = portfolio(close[["BTCUSDT"]], funding, btc_members, start, end, fee)
    print(
        _row(
            "sam BTC (opis)",
            summarize_pnl(
                btc.dropna()["net"], periods_per_year=DAYS_PER_YEAR, capital_per_notional=1.0
            ),
        )
    )

    print("\n4. PRZEŁOŻENIE NA DŹWIGNIĘ (mnożnik k wag reguły; bez likwidacji, z kapitalizacją)")
    g_med = float(avg["gross_notional"].median())
    var = float(avg["net"].var(ddof=1))
    k_kelly = float(avg["net"].mean() / var) if var > 0 else float("nan")
    for label, k in (
        ("k = 1 (reguła)", 1.0),
        (f"k = {3.0 / g_med:.2f} (brutto 3× kapitału)", 3.0 / g_med),
        (f"k Kelly = {k_kelly:+.2f}", k_kelly),
    ):
        if not np.isfinite(k) or k <= 0:
            print(f"  {label}: niezdefiniowane (średnia ≤ 0 → optymalna dźwignia 0)")
            continue
        cagr, dd = _curve(avg["net"], k)
        print(f"  {label:>32}: CAGR {100 * cagr:+.1f}%/rok, max obsunięcie {100 * dd:.1f}%")
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
