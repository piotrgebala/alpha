"""
run_kr2_tradfi.py — runda KR2 (opisowo, 0 wariantów): na ile krypto i nogi dziennika chodzą razem
z rynkami tradycyjnymi — akcje USA (S&P 500, Nasdaq), Japonia (Nikkei), złoto (PAXG spot), ropa (Brent),
dolar (indeks DTWEXBGS), stopy USA (rentowność 2 i 10 lat, bony 3M), strach (VIX).

Zwroty TYGODNIOWE piątek→piątek (krypto zamyka o 24:00 UTC, USA ~21:00 UTC — dzienne korelacje byłyby
zaniżone przesunięciem). Stopy i VIX: zmiana poziomu (pkt proc.), reszta: zwrot procentowy. Okno 2021-01 → 2026-06.
Tylko korelacje z tego samego tygodnia — NIE prognoza (wyprzedzanie = nowa hipoteza, poza rundą).

    PYTHONUTF8=1 py -m backtest.run_kr2_tradfi
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.run_kr1_korelacje import legs

EXT, TRADFI, UNI = "data/raw/external", "data/raw/tradfi", "data/raw/universe_full"
LEVELS = {  # nazwa → (plik, typ: "ret" zwrot % albo "diff" zmiana poziomu)
    "S&P500": (f"{EXT}/fred_SP500_1d.parquet", "ret"),
    "Nasdaq": (f"{TRADFI}/fred_NASDAQCOM_1d.parquet", "ret"),
    "Nikkei": (f"{TRADFI}/fred_NIKKEI225_1d.parquet", "ret"),
    "złoto": (f"{EXT}/binance_spot_PAXG-USDT_1d.parquet", "ret"),
    "ropa": (f"{TRADFI}/fred_DCOILBRENTEU_1d.parquet", "ret"),
    "dolar": (f"{EXT}/fred_DTWEXBGS_1d.parquet", "ret"),
    "USA 10 l.": (f"{TRADFI}/fred_DGS10_1d.parquet", "diff"),
    "USA 2 l.": (f"{TRADFI}/fred_DGS2_1d.parquet", "diff"),
    "bony 3M": (f"{EXT}/fred_DTB3_1d.parquet", "diff"),
    "VIX": (f"{EXT}/fred_VIXCLS_1d.parquet", "diff"),
}
LO, HI = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")
SEP = "=" * 104


def daily_level(path: str) -> pd.Series:
    """Poziom dzienny z pliku FRED (date, value) albo świec (timestamp/open_time, close); braki pominięte."""
    d = pd.read_parquet(path)
    if "value" in d:
        s = pd.Series(
            d["value"].astype(float).to_numpy(), index=pd.to_datetime(d["date"], utc=True)
        )
    else:
        t = d["timestamp"] if "timestamp" in d else d["open_time"]
        s = pd.Series(d["close"].astype(float).to_numpy(), index=pd.to_datetime(t, utc=True))
    return s.dropna().sort_index()


def weekly_change(level: pd.Series, kind: str) -> pd.Series:
    """Ostatni poziom tygodnia (do piątku) → zwrot % albo zmiana poziomu tydzień do tygodnia."""
    w = level.resample("W-FRI").last()
    return (w.pct_change(fill_method=None) if kind == "ret" else w.diff()).dropna()


def crypto_weekly() -> pd.DataFrame:
    out = {}
    for name, sym in (("BTC", "BTCUSDT"), ("ETH", "ETHUSDT")):
        b = pd.read_parquet(f"{UNI}/{sym}_1d.parquet")
        out[name] = weekly_change(daily_level_from_klines(b), "ret")
    lg = legs()
    for c in lg:
        out[f"noga {c}"] = lg[c].resample("W-FRI").sum()
    return pd.DataFrame(out)


def daily_level_from_klines(b: pd.DataFrame) -> pd.Series:
    return pd.Series(
        b["close"].astype(float).to_numpy(), index=pd.to_datetime(b["open_time"], utc=True)
    ).sort_index()


def main() -> None:
    crypto = crypto_weekly()
    trad = pd.DataFrame({k: weekly_change(daily_level(p), kind) for k, (p, kind) in LEVELS.items()})
    df = crypto.join(trad, how="inner")
    df = df[(df.index >= LO) & (df.index < HI)].dropna()
    print(SEP)
    print(
        "KR2 — korelacje tygodniowe krypto i nóg dziennika z rynkami tradycyjnymi (ten sam tydzień, nie prognoza)"
    )
    print(SEP)
    print(
        f"  tygodni: {len(df)} ({df.index.min().date()} → {df.index.max().date()}); ±{1.96 / np.sqrt(len(df)):.2f} ≈ szerokość 95 % przy korelacji 0"
    )
    c = df.corr()
    cols = list(LEVELS)
    print("  " + " " * 10 + "".join(f"{k:>10}" for k in cols))
    for r in crypto.columns:
        print(f"  {r:<10}" + "".join(f"{c.loc[r, k]:+10.2f}" for k in cols))
    print("\n  BTC — korelacja per rok:")
    print("  " + " " * 6 + "".join(f"{k:>10}" for k in cols))
    for y, g in df.groupby(df.index.year):
        cy = g.corr()
        print(f"  {y} ({len(g):2d})" + "".join(f"{cy.loc['BTC', k]:+10.2f}" for k in cols))
    beta = df["BTC"].cov(df["Nasdaq"]) / df["Nasdaq"].var()
    print(
        f"\n  beta BTC do Nasdaq: {beta:.2f} (1 % ruchu Nasdaq ≈ {beta:.1f} % ruchu BTC w tym samym tygodniu)"
    )
    print(SEP)


if __name__ == "__main__":
    main()
