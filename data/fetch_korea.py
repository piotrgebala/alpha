"""
fetch_korea.py — dane do rundy KP1 (premia koreańska) w `data/raw/external/`.

Dwa źródła, publiczne, bez klucza:
- Upbit (giełda koreańska): świece dzienne `KRW-BTC`; świeca dnia d zaczyna się o 00:00 UTC
  (09:00 KST), czyli tak jak świece Coinbase i Binance;
- FRED `DEXKOUS` (kurs USD/KRW, „noon buying rates in New York”, tylko dni robocze USA) —
  pobierany istniejącym `fetch_external.fetch_fred`, bez zmian w tamtym module.

Osobny moduł zamiast rozszerzania `fetch_external.py`: tamten importuje `data/fetch_live.py`,
z którego korzysta dziennik papierowy (zmiana = decyzja użytkownika, CLAUDE.md). Stąd tylko
importy gotowych funkcji; zasady te same: czysty `parse_*` testowany bez sieci, fail loud,
idempotencja, parquet z czasem UTC.

Użycie:
    py -m data.fetch_korea [out_dir] [--force]
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd

from data.fetch_external import (
    DEFAULT_OUT_DIR,
    DEFAULT_START,
    REST_PACING_S,
    _skip_existing,
    describe,
    fetch_fred,
    http_get,
    save_parquet,
    target_path,
)

UPBIT_DAYS_URL = "https://api.upbit.com/v1/candles/days"
UPBIT_MAX_CANDLES = 200  # limit Upbit na jedno zapytanie
UPBIT_FIELDS = {
    "candle_date_time_utc": "open_time",
    "opening_price": "open",
    "high_price": "high",
    "low_price": "low",
    "trade_price": "close",
    "candle_acc_trade_volume": "volume",
    "candle_acc_trade_price": "quote_volume",
}
FX_SERIES = "DEXKOUS"


def parse_upbit_days(rows: list[dict]) -> pd.DataFrame:
    """
    Świece dzienne Upbit (lista słowników, malejąco) → rosnąco: open_time (UTC), OHLC, wolumen
    w BTC i w KRW. Brak pola albo świeca nie o 00:00 UTC → ValueError (fail loud).
    """
    cols = list(UPBIT_FIELDS.values())
    if not rows:
        return pd.DataFrame({c: pd.Series(dtype=float) for c in cols}).astype(
            {"open_time": "datetime64[ns, UTC]"}
        )
    bad = [r for r in rows if not set(UPBIT_FIELDS) <= r.keys()]
    if bad:
        raise ValueError(f"upbit: brak pól {sorted(set(UPBIT_FIELDS) - bad[0].keys())}")
    df = pd.DataFrame(rows)[list(UPBIT_FIELDS)].rename(columns=UPBIT_FIELDS)
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    if (df["open_time"] != df["open_time"].dt.floor("D")).any():
        raise ValueError("upbit: świeca dzienna nie zaczyna się o 00:00 UTC")
    for c in cols[1:]:
        df[c] = df[c].astype(float)
    return df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def next_to(batch: pd.DataFrame) -> str | None:
    """Parametr `to` następnego zapytania (Upbit zwraca świece PRZED `to`): najstarsza świeca."""
    if batch.empty:
        return None
    return batch["open_time"].min().strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_upbit_daily(
    market: str,
    start: str,
    out_dir: str | Path,
    force: bool = False,
    pacing_s: float = REST_PACING_S,
    now: pd.Timestamp | None = None,
) -> Path | None:
    """Świece dzienne Upbit od `start` do ostatniej zamkniętej (≤ 200 na zapytanie, wstecz)."""
    path = target_path(out_dir, f"upbit_{market}_1d")
    if _skip_existing(path, force):
        return None
    lo = pd.Timestamp(start, tz="UTC")
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    to = now.floor("D").strftime("%Y-%m-%dT%H:%M:%SZ")  # bez dnia w toku
    frames = []
    while to is not None:
        q = urllib.parse.urlencode({"market": market, "count": UPBIT_MAX_CANDLES, "to": to})
        rows = json.loads(http_get(f"{UPBIT_DAYS_URL}?{q}"))
        if not isinstance(rows, list):
            raise ValueError(f"upbit: nieoczekiwana odpowiedź {str(rows)[:200]}")
        batch = parse_upbit_days(rows)
        frames.append(batch)
        new_to = (
            next_to(batch)
            if len(batch) == UPBIT_MAX_CANDLES and batch["open_time"].min() > lo
            else None
        )
        if new_to is not None and new_to >= to:  # ISO UTC: porządek tekstowy = czasowy
            raise ValueError(
                f"upbit: kursor nie cofa się ({to} → {new_to}) — API zignorowało `to`?"
            )
        to = new_to
        time.sleep(pacing_s)
    df = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("open_time")
        .sort_values("open_time")
        .reset_index(drop=True)
    )
    df = df[df["open_time"] >= lo].reset_index(drop=True)
    print(f"[korea] upbit {market}: {len(df)} dni")
    return save_parquet(df, path)


def run(out_dir: str | Path = DEFAULT_OUT_DIR, force: bool = False, start: str = DEFAULT_START):
    paths = [
        fetch_upbit_daily("KRW-BTC", start, out_dir, force),
        fetch_fred(FX_SERIES, start, out_dir, force),
    ]
    for p in paths:
        if p is not None:
            print(f"[korea] OK  {describe(p)}")
    return paths


def main(argv: list[str]) -> int:
    out_dir = next((a for a in argv if a != "--force"), DEFAULT_OUT_DIR)
    run(out_dir, force="--force" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
