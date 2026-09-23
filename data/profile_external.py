"""
profile_external.py — profil zbiorów z `data/raw/external/` (runda P3), BEZ związku ze zwrotami.

Co liczy (własności danych, `data:explore-data`): zakres dat, liczbę wierszy, oczekiwaną
liczbę punktów przy natywnym ziarnie i brakujące punkty (luki), duplikaty znacznika, wartości
niedodatnie tam, gdzie nie mają sensu, kwantyle każdej kolumny liczbowej, masę punktową
(udział najczęstszej wartości — wniosek 15: progi percentylowe na takich cechach są złudne),
autokorelację lag-1 SAMEJ zmiennej (do N_eff przyszłych rund) oraz pokrycie bazy z zasady 20
(`2021-01-01 → 2026-07-01`) — brama G1 z pre-rejestracji P3.

Czego NIE liczy (warunek zera wariantów P3): niczego, co wiąże zmienną z przyszłym zwrotem.

Użycie:
    py -m data.profile_external [dir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_START = pd.Timestamp("2021-01-01", tz="UTC")
BASE_END = pd.Timestamp("2026-07-01", tz="UTC")  # koniec wyłączny, jak `fetch_window`
TIME_COLUMNS = ("timestamp", "open_time", "date")
QUANTILES = (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)


def time_column(df: pd.DataFrame) -> str:
    for c in TIME_COLUMNS:
        if c in df.columns:
            return c
    raise ValueError(f"brak kolumny czasu {TIME_COLUMNS} w {list(df.columns)}")


def infer_step(ts: pd.Series) -> pd.Timedelta | None:
    """Najczęstsza różnica między kolejnymi znacznikami (natywne ziarno); None przy < 2 punktach."""
    if len(ts) < 2:
        return None
    d = ts.sort_values().diff().dropna()
    return d.mode().iloc[0] if len(d) else None


def coverage(ts: pd.Series, step: pd.Timedelta | None, start=BASE_START, end=BASE_END) -> dict:
    """
    Pokrycie bazy `[start, end)` przy ziarnie `step`: oczekiwane punkty, obecne, ułamek.

    Dla ziarna dziennego kalendarzowego (FRED — dni robocze) ułamek liczy się względem dni
    OBECNYCH w szeregu (nie ma czego brakować w weekend), więc raportowana jest też liczba
    dni kalendarzowych bez obserwacji — interpretacja należy do czytelnika.
    """
    inside = ts[(ts >= start) & (ts < end)]
    if step is None or step <= pd.Timedelta(0):
        return {"expected": np.nan, "present": int(len(inside)), "fraction": np.nan}
    expected = int((end - start) / step)
    present = int(inside.nunique())
    return {"expected": expected, "present": present, "fraction": present / expected}


def gaps(ts: pd.Series, step: pd.Timedelta | None) -> pd.DataFrame:
    """Odcinki dłuższe niż `step` między kolejnymi znacznikami: start, koniec, ile punktów brakuje."""
    if step is None:
        return pd.DataFrame(columns=["from", "to", "missing_points"])
    s = ts.sort_values().reset_index(drop=True)
    d = s.diff()
    idx = np.flatnonzero((d > step).to_numpy())
    return pd.DataFrame(
        {
            "from": s.iloc[idx - 1].to_numpy(),
            "to": s.iloc[idx].to_numpy(),
            "missing_points": ((d.iloc[idx] / step).round().astype(int) - 1).to_numpy(),
        }
    )


def point_mass(x: pd.Series) -> tuple[float, float]:
    """(najczęstsza wartość, jej udział) wśród nie-NaN; (nan, 0) gdy pusto."""
    x = x.dropna()
    if x.empty:
        return float("nan"), 0.0
    vc = x.value_counts()
    return float(vc.index[0]), float(vc.iloc[0] / len(x))


def lag1_autocorr(x: pd.Series) -> float:
    x = x.dropna()
    if len(x) < 3 or x.std(ddof=0) == 0:
        return float("nan")
    return float(x.autocorr(lag=1))


def profile_frame(df: pd.DataFrame, name: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """(nagłówek zbioru, tabela kolumn, tabela luk)."""
    tcol = time_column(df)
    ts = pd.to_datetime(df[tcol], utc=True)
    step = infer_step(ts)
    cov = coverage(ts, step)
    head = {
        "zbiór": name,
        "wiersze": int(len(df)),
        "od": ts.min(),
        "do": ts.max(),
        "ziarno": step,
        "duplikaty_znacznika": int(ts.duplicated().sum()),
        "baza_oczekiwane": cov["expected"],
        "baza_obecne": cov["present"],
        "baza_pokrycie": cov["fraction"],
    }
    rows = []
    for col in df.columns:
        if col == tcol or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        x = df[col].astype(float)
        mode_val, mode_share = point_mass(x)
        q = x.quantile(QUANTILES)
        rows.append(
            {
                "kolumna": col,
                "n": int(x.notna().sum()),
                "braki": int(x.isna().sum()),
                "niedodatnie": int((x <= 0).sum()),
                "min": x.min(),
                "p01": q.iloc[0],
                "p05": q.iloc[1],
                "p25": q.iloc[2],
                "p50": q.iloc[3],
                "p75": q.iloc[4],
                "p95": q.iloc[5],
                "p99": q.iloc[6],
                "max": x.max(),
                "masa_pkt_wartość": mode_val,
                "masa_pkt_udział": mode_share,
                "acf1": lag1_autocorr(x),
            }
        )
    return head, pd.DataFrame(rows), gaps(ts, step)


def main(argv: list[str]) -> int:
    d = Path(argv[0]) if argv else Path("data/raw/external")
    files = sorted(d.glob("*.parquet"))
    if not files:
        print(f"brak plików parquet w {d}")
        return 1
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.float_format", lambda v: f"{v:,.6g}")
    heads = []
    for f in files:
        df = pd.read_parquet(f)
        head, cols, gp = profile_frame(df, f.stem)
        heads.append(head)
        print("=" * 100)
        print(
            f"{f.stem}: {head['wiersze']} wierszy, {head['od']} → {head['do']}, ziarno {head['ziarno']}"
        )
        print(
            f"  duplikaty znacznika: {head['duplikaty_znacznika']}; pokrycie bazy 2021-01-01→2026-07-01: "
            f"{head['baza_obecne']} / {head['baza_oczekiwane']} = {head['baza_pokrycie']:.4f}"
            if not np.isnan(head["baza_pokrycie"])
            else f"  duplikaty znacznika: {head['duplikaty_znacznika']}; pokrycie bazy: n/d"
        )
        if "contract" in df.columns:
            per = df.groupby("contract", sort=False).agg(
                od=("open_time", "min"), do=("open_time", "max"), n=("open_time", "size")
            )
            print("  kontrakty:")
            print(per.to_string())
        print(cols.to_string(index=False))
        if len(gp):
            print(
                f"  luki ({len(gp)}), łącznie brakujących punktów: {int(gp['missing_points'].sum())}"
            )
            print(gp.head(20).to_string(index=False))
            if len(gp) > 20:
                print(f"  ... i {len(gp) - 20} dalszych")
        else:
            print("  luki: brak")
    print("=" * 100)
    print("PODSUMOWANIE (brama G1: pokrycie bazy z zasady 20)")
    summary = pd.DataFrame(heads)[
        ["zbiór", "wiersze", "od", "do", "ziarno", "duplikaty_znacznika", "baza_pokrycie"]
    ]
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
