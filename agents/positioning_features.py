"""
positioning_features.py — cechy z POZYCJONOWANIA (archiwum Binance `futures/um/daily/metrics`,
5 min, podłączone w P3) dla modelu 4h BTC — runda O1.

Kontrakt (jak `agents/ta_rules.py`): najpierw `attach_positioning(df, metrics)` dopina do świec 4h
SUROWY snapshot pozycjonowania znany w chwili zamknięcia świecy, potem czyste funkcje
`compute_<nazwa>(df) -> pd.Series` (trailing, bez globalnych statystyk) liczą cechy z tych
kolumn. Test przecieku (`agent_5_compliance/test_leakage.py`) obejmuje obie warstwy: dopięcie
(snapshot z przyszłości nie może zmienić wartości) i cechę (bit w bit do CUTOFF).

Dlaczego snapshot z `open + 3h55m`, nie z `open + 4h`: archiwum ma odczyty co 5 min o pełnych
minutach (`create_time`); odczyt o `open + 4h` jest PIERWSZYM odczytem następnej świecy i
formalnie równoczesny z ceną zamknięcia, więc bezpieczniej wziąć ostatni odczyt WEWNĄTRZ świecy.
Brak odczytu w oknie świecy → NaN (bez sięgania wstecz poza świecę i nigdy w przód).

Jedna cecha na rundę (CLAUDE.md zasada 4): O1 = `oi_change_24h` — logarytmiczna zmiana open
interest (w BTC, nie w USD — bez efektu ceny) w 6 świecach 4h. Mechanizm: narastanie OI =
narastanie dźwigni → kaskady likwidacji; kierunek uczy model łącznie z cechami zwrotu.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

METRICS_PATH = Path("data/raw/external/binance_metrics_BTCUSDT_5m.parquet")
CANDLE_MINUTES = 240
SNAPSHOT_OFFSET = pd.Timedelta(minutes=CANDLE_MINUTES - 5)  # ostatni odczyt 5-min WEWNĄTRZ świecy
OI_COLUMN = "sum_open_interest"  # OI w BTC (kontrakty), nie `sum_open_interest_value` (USD)
OI_CHANGE_CANDLES = 6  # 24h przy 4h
RAW_COLUMN = "oi_close"


def load_metrics(path: str | Path = METRICS_PATH) -> pd.DataFrame:
    """Archiwum 5 min → (timestamp, oi) z OI ≤ 0 (błędy archiwum, P3: 473 odczytów) jako NaN."""
    m = pd.read_parquet(path)
    if "timestamp" not in m.columns or OI_COLUMN not in m.columns:
        raise ValueError(f"metrics: wymagane kolumny timestamp i {OI_COLUMN}")
    out = pd.DataFrame(
        {"timestamp": pd.to_datetime(m["timestamp"], utc=True), "oi": m[OI_COLUMN].astype(float)}
    )
    out.loc[out["oi"] <= 0, "oi"] = np.nan
    return out.dropna(subset=["oi"]).sort_values("timestamp").reset_index(drop=True)


def attach_positioning(
    df: pd.DataFrame, metrics: pd.DataFrame, offset: pd.Timedelta = SNAPSHOT_OFFSET
) -> pd.DataFrame:
    """
    Dla każdej świecy (`timestamp` = otwarcie) dopina `oi_close` = OI z OSTATNIEGO odczytu
    o czasie w przedziale (open, open + offset]; brak odczytu w przedziale → NaN.
    Nie mutuje `df`. Odczyty późniejsze niż `open + offset` są niewidoczne z konstrukcji.
    """
    if "timestamp" not in df.columns:
        raise ValueError("df: wymagana kolumna timestamp")
    left = pd.DataFrame(
        {
            "_key": pd.to_datetime(df["timestamp"], utc=True) + offset,
            "_open": pd.to_datetime(df["timestamp"], utc=True),
            "_order": np.arange(len(df)),
        }
    ).sort_values("_key")
    right = metrics[["timestamp", "oi"]].rename(columns={"timestamp": "_snap"}).sort_values("_snap")
    joined = pd.merge_asof(
        left, right, left_on="_key", right_on="_snap", direction="backward", tolerance=offset
    )
    # tolerance = offset gwarantuje `_snap >= open`; wykluczamy dokładnie `open` (należy do
    # poprzedniej świecy jako jej „open + 4h”) — chcemy odczytów ściśle WEWNĄTRZ świecy
    inside = joined["_snap"] > joined["_open"]
    joined.loc[~inside, "oi"] = np.nan
    joined = joined.sort_values("_order")
    out = df.copy()
    out[RAW_COLUMN] = joined["oi"].to_numpy()
    return out


def compute_oi_change_24h(df: pd.DataFrame) -> pd.Series:
    """log(OI_t / OI_{t−6}) na świecach 4h; NaN przez pierwsze 6 świec i przy NaN wejścia."""
    if RAW_COLUMN not in df.columns:
        raise ValueError(f"df: brak kolumny {RAW_COLUMN} — najpierw attach_positioning")
    oi = df[RAW_COLUMN].astype(float)
    return np.log(oi / oi.shift(OI_CHANGE_CANDLES)).rename("oi_change_24h")


POSITIONING_FEATURE_FUNCTIONS = {"oi_change_24h": compute_oi_change_24h}


def compute_positioning_features(df: pd.DataFrame) -> pd.DataFrame:
    """Dolicza wszystkie cechy pozycjonowania jako nowe kolumny (nie mutuje df)."""
    out = df.copy()
    for name, fn in POSITIONING_FEATURE_FUNCTIONS.items():
        out[name] = fn(df)
    return out
