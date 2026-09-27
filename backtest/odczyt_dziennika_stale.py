"""Źródło stałych μ, σ odczytu dziennika (`backtest/odczyt_dziennika.py::LEGS`) — opisowo, 0 wariantów.

Po co: próg obalenia szczebla 3 (ADR-09) potrzebuje zakładanej średniej μ i zmienności σ każdej nogi
dziennika w DOKŁADNIE jego konfiguracji (trend 2× i premia Coinbase 3× z likwidacją izolowaną, portfel
R1, X1 jako średnia 7 faz). Rundy raportowały część tych liczb jako CAGR (średnia geometryczna) albo
bez likwidacji, więc ta komenda liczy je jeszcze raz z tych samych, zamrożonych silników.

Zasady: to NIE jest nowy odczyt historii — te same szeregi, które wydrukowały RU1 (`run_sz1`) i X1F
(`main`); nic nie jest dobierane ani strojone. μ = średnia dzienna × 365, σ = sd dzienne × √365
(arytmetycznie, jak `carry_hedged.summarize_pnl(periods_per_year=365, capital_per_notional=1)`).
Sprawdzenie drugą drogą: obok drukuje CAGR i zmienność (`sizing.summary`) do porównania z
`runs/2026-09-24_ru1-pelne-uniwersum/raw_output_sz1.txt` i `runs/2026-09-24_x1f-siedem-faz/raw_output.txt`.
Dane: `data/raw/universe_full`, `universe_ohlc_full`, Coinbase i spot BTC 8h (tylko odczyt).

    PYTHONUTF8=1 py -m backtest.odczyt_dziennika_stale          # ~2 min

Wydruk z 2026-09-27 jest w `dziennik/README.md` („Zmiana kryteriów odczytu”). Testy czystej części:
`tests/test_odczyt_dziennika.py`.
"""

from __future__ import annotations

import math

import pandas as pd

DAYS_PER_YEAR = 365


def mu_sigma(x: pd.Series) -> dict:
    """Szereg zwrotów dziennych → n, okres, μ i σ roczne (arytmetyczne), CAGR (geometryczny)."""
    x = x.dropna().astype(float)
    n = len(x)
    if n < 2:
        raise ValueError("za mało dni")
    growth = float((1.0 + x).prod())
    return {
        "n": n,
        "first": x.index.min(),
        "last": x.index.max(),
        "mu": float(x.mean()) * DAYS_PER_YEAR,
        "sigma": float(x.std(ddof=1)) * math.sqrt(DAYS_PER_YEAR),
        "cagr": growth ** (DAYS_PER_YEAR / n) - 1.0 if growth > 0 else -1.0,
    }


def _line(name: str, x: pd.Series) -> str:
    s = mu_sigma(x)
    first, last = (getattr(t, "date", lambda t=t: t)() for t in (s["first"], s["last"]))
    return (
        f"  {name:<34} {s['n']:5d} dni {first} → {last} | μ {100 * s['mu']:+6.2f} %/rok | "
        f"σ {100 * s['sigma']:5.2f} %/rok | CAGR {100 * s['cagr']:+6.2f} %"
    )


def legs() -> dict[str, pd.Series]:  # pragma: no cover - wymaga danych historycznych
    """Dzienne zwroty nóg dziennika na historii — silniki i wejścia jak w RU1 `run_sz1` i X1F `main`."""
    from backtest import run_ts_momentum_ts1 as ts1
    from backtest import run_universe_fix_ru1 as ru1
    from backtest import run_x1_phases_x1f as x1f
    from backtest.checkpoint_lib import load_config
    from backtest.rebalance_premium import load_universe, monthly_members
    from backtest.run_coinbase_cp1 import _load as load_cp
    from backtest.sizing import apply_rules
    from backtest.ts_momentum import PHASES, formation_dates, portfolio
    from backtest.xs_momentum import daily_funding_panel, long_short_returns

    # --- trend 2× i premia 3× z likwidacją izolowaną, R1 — kopia wejść RU1 run_sz1 (bez zmian)
    fee, close, funding, members, start, end = ts1._load(ru1.FULL)
    hi, lo = ru1._extremes(close)
    liq = {"high": hi, "low": lo, "lev": ru1.LEV_TS, "mmr": ru1.MMR}
    tr, _ = portfolio(close, funding, members, start, end, fee, liq=liq)
    fee_c, close_c, fund_c, mem_c, signs, _p, start_c, end_c = load_cp()
    hc, lc = ru1._extremes(close_c)
    liq_c = {"high": hc, "low": lc, "lev": ru1.LEV_CP, "mmr": ru1.MMR}
    cp, _ = portfolio(
        close_c, fund_c, mem_c, start_c, end_c, fee_c, signs_override=signs, liq=liq_c
    )
    trend = tr.dropna().set_index("date")["net"].rename("trend")
    coinbase = cp.dropna().set_index("date")["net"].rename("coinbase")
    rets = pd.concat([trend, coinbase], axis=1).dropna()
    r1 = apply_rules(rets, "R1").set_index("date")["ret"]

    # --- X1 jako średnia 7 faz — kopia wejść X1F main (bez zmian)
    cfg = load_config()
    fee_x = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close_x, volume = load_universe(x1f.FULL)
    lo_x, end_x = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(x1f.END, tz="UTC")
    close_x = close_x[(close_x.index >= lo_x) & (close_x.index < end_x)]
    volume = volume[(volume.index >= lo_x) & (volume.index < end_x)]
    funding_x = daily_funding_panel(x1f.FULL)
    start_x = pd.Timestamp(x1f.START, tz="UTC")
    months = [m for m in pd.date_range(x1f.START, x1f.END, freq="MS", tz="UTC") if m < end_x]
    members_x = monthly_members(volume, months)
    series = []
    for ph in range(PHASES):
        dates = formation_dates(close_x.index, start_x, end_x, ph)
        out = long_short_returns(close_x, funding_x, members_x, dates, fee_x)
        series.append(out.set_index("date")["r_net"].rename(ph))
    panel = pd.concat(series, axis=1)
    common = panel[panel.index >= max(s.first_valid_index() for _, s in panel.items())]
    return {
        "TS1 trend 2× (własne okno)": trend,
        "TS1 trend 2× (okno wspólne z CP1)": rets["trend"],
        "CP1 premia Coinbase 3×": rets["coinbase"],
        "R1 portfel (budżet ryzyka)": r1,
        "X1 średnia 7 faz": common.mean(axis=1),
    }


def main() -> None:  # pragma: no cover - wymaga danych historycznych
    print("μ, σ nóg dziennika na historii 2021–2026 (arytmetycznie; opisowo, 0 wariantów)")
    for name, x in legs().items():
        print(_line(name, x))


if __name__ == "__main__":  # pragma: no cover
    main()
