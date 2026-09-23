"""
external_features.py — cechy z DZIENNYCH źródeł zewnętrznych (P3: CoinMetrics on-chain, Deribit
DVOL, alternative.me Fear & Greed) dla modelu 4h BTC — serie L1 / V1 / G1.

Kontrakt (jak `agents/positioning_features.py`): najpierw `attach_daily(df, daily, ...)` dopina
do świec 4h wartość dzienną ZNANĄ w chwili otwarcia świecy — z jawnym opóźnieniem publikacji
`available_after` (wartość dnia `d` widoczna dopiero dla świec o `open >= d + available_after`)
i limitem świeżości (`tolerance`: starsza wartość niż 7 dni → NaN). Potem czyste funkcje
`compute_<nazwa>(df) -> pd.Series` (trailing) liczą cechy z dopiętych kolumn. Test przecieku
(`agent_5_compliance/test_leakage.py`) obejmuje dopięcie (dni późniejsze niewidoczne) i cechę
(shift-forward bit w bit).

Opóźnienia publikacji (pre-rejestracja, konserwatywnie):
- CoinMetrics community: wartość dnia `d` (UTC) publikowana po zamknięciu dnia, z opóźnieniem
  godzin → używamy od `d + 2 dni 00:00 UTC`;
- DVOL (świeca 1D): zamknięcie dnia `d` znane o `d + 1 dzień 00:00 UTC`;
- Fear & Greed: wartość dnia `d` publikowana ok. 00:00 UTC dnia `d` → używamy od `d + 4h`.

Jedna cecha na serię (CLAUDE.md zasada 4):
- L1 `ex_supply_change_7d` = log(SplyExNtv_d / SplyExNtv_{d−7}) — monety płynące na giełdy;
- V1 `vrp_30d` = DVOL_d/100 − zrealizowana zmienność 30 dni (180 świec 4h, annualizowana);
- G1 `fng_level` = Fear & Greed / 100 (poziom, bez progów).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

EXTERNAL_DIR = Path("data/raw/external")
STALENESS_TOLERANCE = pd.Timedelta(days=7)
CANDLES_PER_DAY = 6
RV_WINDOW_CANDLES = 30 * CANDLES_PER_DAY  # 30 dni na 4h
ANNUALIZATION = np.sqrt(365.0 * CANDLES_PER_DAY)

SOURCES = {
    "coinmetrics": {
        "path": EXTERNAL_DIR / "coinmetrics_btc_1d.parquet",
        "available_after": pd.Timedelta(days=2),
    },
    "dvol": {
        "path": EXTERNAL_DIR / "deribit_dvol_BTC_1d.parquet",
        "available_after": pd.Timedelta(days=1),
    },
    "fng": {
        "path": EXTERNAL_DIR / "alternative_fng_1d.parquet",
        "available_after": pd.Timedelta(hours=4),
    },
}


def load_daily(source: str, columns: list[str]) -> pd.DataFrame:
    """Plik dzienny źródła → (date, *columns) rosnąco, bez duplikatów dnia; brak kolumny → ValueError."""
    spec = SOURCES[source]
    d = pd.read_parquet(spec["path"])
    missing = {"date", *columns} - set(d.columns)
    if missing:
        raise ValueError(f"{source}: brak kolumn {sorted(missing)}")
    out = d[["date", *columns]].copy()
    out["date"] = pd.to_datetime(out["date"], utc=True)
    return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def daily_log_change(daily: pd.DataFrame, column: str, days: int, name: str) -> pd.DataFrame:
    """Dokłada do ramki dziennej `name` = log(x_d / x_{d−days}) (po kolejnych wierszach; NaN warm-up)."""
    out = daily.copy()
    out[name] = np.log(out[column].astype(float) / out[column].astype(float).shift(days))
    return out


def attach_daily(
    df: pd.DataFrame,
    daily: pd.DataFrame,
    columns: dict[str, str],
    available_after: pd.Timedelta,
    tolerance: pd.Timedelta = STALENESS_TOLERANCE,
) -> pd.DataFrame:
    """
    Dla każdej świecy (`timestamp` = otwarcie `t`) dopina wartości dnia `d` = największy dzień
    z `d + available_after <= t`, o ile `t − (d + available_after) <= tolerance`; inaczej NaN.
    `columns` = {kolumna_dzienna: nazwa_w_df}. Nie mutuje `df`; dni późniejsze niewidoczne.
    """
    if "timestamp" not in df.columns:
        raise ValueError("df: wymagana kolumna timestamp")
    missing = set(columns) - set(daily.columns)
    if missing:
        raise ValueError(f"daily: brak kolumn {sorted(missing)}")
    # jednostka czasu ujednolicona do ns (parquet 4h ma µs, ramki dzienne ns — merge_asof wymaga zgodności)
    left = pd.DataFrame(
        {
            "_key": (pd.to_datetime(df["timestamp"], utc=True) - available_after).astype(
                "datetime64[ns, UTC]"
            ),
            "_order": np.arange(len(df)),
        }
    ).sort_values("_key")
    right = daily[["date", *columns]].rename(columns={"date": "_day"}).sort_values("_day")
    right["_day"] = pd.to_datetime(right["_day"], utc=True).astype("datetime64[ns, UTC]")
    joined = pd.merge_asof(
        left, right, left_on="_key", right_on="_day", direction="backward", tolerance=tolerance
    ).sort_values("_order")
    out = df.copy()
    for src, dst in columns.items():
        out[dst] = joined[src].to_numpy()
    return out


# --- cechy (czyste funkcje na dopiętych kolumnach) ----------------------------------------------


def compute_ex_supply_change_7d(df: pd.DataFrame) -> pd.Series:
    """L1: log-zmiana podaży BTC na giełdach z 7 dni (dopięta kolumna dzienna `ex_supply_change_7d_d`)."""
    if "ex_supply_change_7d_d" not in df.columns:
        raise ValueError("df: brak kolumny ex_supply_change_7d_d — najpierw attach_daily")
    return df["ex_supply_change_7d_d"].astype(float).rename("ex_supply_change_7d")


def compute_realized_vol_30d(df: pd.DataFrame) -> pd.Series:
    """Zrealizowana zmienność: std log-zwrotów 4h w oknie 180 świec (trailing), annualizowana."""
    lr = np.log(df["close"].astype(float)).diff()
    return (lr.rolling(RV_WINDOW_CANDLES).std(ddof=1) * ANNUALIZATION).rename("rv_30d")


def compute_vrp_30d(df: pd.DataFrame) -> pd.Series:
    """V1: premia za ryzyko zmienności = DVOL_d/100 (dopięte `dvol_d`) − zrealizowana 30 dni."""
    if "dvol_d" not in df.columns:
        raise ValueError("df: brak kolumny dvol_d — najpierw attach_daily")
    return (df["dvol_d"].astype(float) / 100.0 - compute_realized_vol_30d(df)).rename("vrp_30d")


def compute_fng_level(df: pd.DataFrame) -> pd.Series:
    """G1: Fear & Greed / 100 (dopięte `fng_d`), poziom bez progów."""
    if "fng_d" not in df.columns:
        raise ValueError("df: brak kolumny fng_d — najpierw attach_daily")
    return (df["fng_d"].astype(float) / 100.0).rename("fng_level")


EXTERNAL_FEATURE_FUNCTIONS = {
    "ex_supply_change_7d": compute_ex_supply_change_7d,
    "vrp_30d": compute_vrp_30d,
    "fng_level": compute_fng_level,
}

# Które kolumny dzienne (i z jakiego źródła) potrzebuje każda cecha — do `attach_all`.
FEATURE_SOURCES = {
    "ex_supply_change_7d": ("coinmetrics", {"ex_supply_change_7d_d": "ex_supply_change_7d_d"}),
    "vrp_30d": ("dvol", {"close": "dvol_d"}),
    "fng_level": ("fng", {"value": "fng_d"}),
}


def attach_feature_inputs(df: pd.DataFrame, feature: str) -> pd.DataFrame:
    """Wczytuje źródło cechy, liczy pochodne dzienne (L1: log-zmiana 7 dni) i dopina do świec."""
    source, columns = FEATURE_SOURCES[feature]
    if feature == "ex_supply_change_7d":
        daily = daily_log_change(
            load_daily(source, ["SplyExNtv"]), "SplyExNtv", 7, "ex_supply_change_7d_d"
        )
    else:
        daily = load_daily(source, list(columns))
    return attach_daily(df, daily, columns, SOURCES[source]["available_after"])


def compute_external_feature(df: pd.DataFrame, feature: str) -> pd.DataFrame:
    """Dopięcie wejść + policzenie JEDNEJ cechy jako nowej kolumny (nie mutuje df)."""
    out = attach_feature_inputs(df, feature)
    out[feature] = EXTERNAL_FEATURE_FUNCTIONS[feature](out)
    return out
