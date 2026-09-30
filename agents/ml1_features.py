"""
ml1_features.py — runda ML1 (zadanie 028): 11 cech na świecy DZIENNEJ BTC (karta `runs/DRAFT_028.md`
§4.1, reguły dostępności §4.1 i §14). Cztery cechy REVERSION liczy bez zmian `agents/feature_miner.py`
(te same funkcje co na 4h, na natywnych świecach 1d); ten moduł dokłada siedem cech spoza wykresu
w wersji dziennej oraz czyste funkcje reguły progu i kalibracji (§14.1, §14.6).

Kontrakt jak `sw_features` / `external_features`: najpierw DOPIĘCIE surowych wejść znanych przed
zamknięciem świecy `d` (otwarcie `d` 00:00 UTC, zamknięcie `d+1` 00:00; wejście po cenie zamknięcia),
potem czyste funkcje `compute_<nazwa>(df) -> pd.Series` (trailing). Reguły dopięcia (zapisane w karcie
PRZED danymi):
- funding: ostatnie rozliczenie o czasie ŚCIŚLE przed zamknięciem świecy (dla BTC 16:00 UTC dnia `d`);
  rozliczenie o 00:00 `d+1` należy do świecy następnej;
- archiwum `metrics` (5 min): odczyty w (open, open + 23 h 55 min] — odczyt o `open` i o `open + 24 h`
  nie należy do świecy; OI i proporcja kont = ostatni odczyt, przewaga kupujących = średnia log ze
  wszystkich odczytów świecy; wartości ≤ 0 (błędy archiwum) = NaN;
- źródła dzienne (`external_features.attach_daily`, klucz = OTWARCIE świecy, konserwatywnie):
  DVOL dnia `x` od świecy `x+1`, CoinMetrics od `x+2`, Fear & Greed (+4 h) od `x+1`; świeżość ≤ 7 dni.

Zmiany definicji wobec 4h (wymuszone świecą, zapisane w karcie §4.1): `oi_change_24h` = log(OI_d/OI_{d−1});
`taker_imbalance_24h` = średnia z jednej świecy (= 24 h, bez okna kroczącego); `vrp_30d` liczy zmienność
zrealizowaną z 30 dziennych log-zwrotów × √365.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from agents.external_features import attach_daily, daily_log_change
from agents.ml_optimizer import REVERSION_FEATURES

CANDLE = pd.Timedelta(days=1)
SNAPSHOT_OFFSET = CANDLE - pd.Timedelta(minutes=5)  # ostatni odczyt 5-min WEWNĄTRZ świecy 1d
RV_WINDOW_DAYS = 30
ANNUALIZATION = float(np.sqrt(365.0))
AVAILABLE_AFTER = {
    "coinmetrics": pd.Timedelta(days=2),
    "dvol": pd.Timedelta(days=1),
    "fng": pd.Timedelta(hours=4),
}

OI_SOURCE = "sum_open_interest"  # w BTC, nie w USD
LS_SOURCE = "count_long_short_ratio"
TAKER_SOURCE = "sum_taker_long_short_vol_ratio"
METRICS_SOURCES = (OI_SOURCE, LS_SOURCE, TAKER_SOURCE)
RAW = {OI_SOURCE: "oi_close", LS_SOURCE: "global_ls_close", TAKER_SOURCE: "taker_log_mean"}

# Kolejność = kolejność usuwania duplikatów (karta §4.1: przy |ρ| > 0,9 odpada cecha późniejsza).
ML1_EXTERNAL = [
    "funding_rate",
    "oi_change_24h",
    "global_ls_log",
    "taker_imbalance_24h",
    "vrp_30d",
    "ex_supply_change_7d",
    "fng_level",
]
ML1_FEATURES = [*REVERSION_FEATURES, *ML1_EXTERNAL]
DEDUP_ABS_RHO = 0.9


# ------------------------------------------------------------------ dopięcie wejść
def _opens(df: pd.DataFrame) -> pd.Series:
    if "timestamp" not in df.columns:
        raise ValueError("df: wymagana kolumna timestamp")
    return pd.to_datetime(df["timestamp"], utc=True).astype("datetime64[ns, UTC]")


def attach_funding_1d(df: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    """Dopina `funding_raw` = ostatnia stawka rozliczona ściśle przed zamknięciem świecy 1d."""
    if not {"timestamp", "funding_rate"} <= set(funding.columns):
        raise ValueError("funding: wymagane kolumny timestamp i funding_rate")
    left = pd.DataFrame(
        {"_key": _opens(df) + CANDLE - pd.Timedelta(1, "ns"), "_order": np.arange(len(df))}
    ).sort_values("_key")
    right = pd.DataFrame(
        {
            "_ts": pd.to_datetime(funding["timestamp"], utc=True).astype("datetime64[ns, UTC]"),
            "funding_raw": funding["funding_rate"].astype(float).to_numpy(),
        }
    ).sort_values("_ts")
    joined = pd.merge_asof(left, right, left_on="_key", right_on="_ts", direction="backward")
    out = df.copy()
    out["funding_raw"] = joined.sort_values("_order")["funding_raw"].to_numpy()
    return out


def clean_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    """Archiwum 5 min → (timestamp, 3 kolumny źródłowe) rosnąco; wartości ≤ 0 = NaN."""
    missing = {"timestamp", *METRICS_SOURCES} - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics: brak kolumn {sorted(missing)}")
    out = metrics[["timestamp", *METRICS_SOURCES]].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True).astype("datetime64[ns, UTC]")
    for c in METRICS_SOURCES:
        out[c] = out[c].astype(float)
        out.loc[out[c] <= 0, c] = np.nan
    return out.sort_values("timestamp").reset_index(drop=True)


def attach_metrics_1d(df: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Dopina do świec 1d: `oi_close`, `global_ls_close` (ostatni ważny odczyt w (open, open + 23 h 55 min])
    i `taker_log_mean` (średnia log proporcji ze wszystkich ważnych odczytów w tym przedziale). Brak → NaN.
    Odczyty późniejsze niż `open + 23 h 55 min` są niewidoczne z konstrukcji. Nie mutuje `df`.
    """
    m = clean_metrics(metrics)
    owner = (m["timestamp"] - pd.Timedelta(1, "ns")).dt.floor(CANDLE)
    inside = (m["timestamp"] - owner) <= SNAPSHOT_OFFSET
    m = m.loc[inside.to_numpy()].assign(_open=owner[inside].to_numpy())
    opens = _opens(df)
    out = df.copy()
    for src in (OI_SOURCE, LS_SOURCE):
        last = m.dropna(subset=[src]).groupby("_open")[src].last()
        out[RAW[src]] = opens.map(last).to_numpy(dtype=float)
    taker = np.log(m[TAKER_SOURCE]).groupby(m["_open"]).mean()
    out[RAW[TAKER_SOURCE]] = opens.map(taker).to_numpy(dtype=float)
    return out


def attach_daily_sources(
    df: pd.DataFrame, dvol: pd.DataFrame, coinmetrics: pd.DataFrame, fng: pd.DataFrame
) -> pd.DataFrame:
    """Dopina `dvol_d`, `ex_supply_change_7d_d`, `fng_d` z opóźnieniami AVAILABLE_AFTER (klucz = otwarcie)."""

    def _daily(d: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        out = d[["date", *cols]].copy()
        out["date"] = pd.to_datetime(out["date"], utc=True)
        return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)

    cm = daily_log_change(_daily(coinmetrics, ["SplyExNtv"]), "SplyExNtv", 7, "sply_chg_7d")
    out = attach_daily(df, _daily(dvol, ["close"]), {"close": "dvol_d"}, AVAILABLE_AFTER["dvol"])
    out = attach_daily(
        out, cm, {"sply_chg_7d": "ex_supply_change_7d_d"}, AVAILABLE_AFTER["coinmetrics"]
    )
    return attach_daily(out, _daily(fng, ["value"]), {"value": "fng_d"}, AVAILABLE_AFTER["fng"])


# ------------------------------------------------------------------ cechy (czyste, trailing)
def _need(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        raise ValueError(f"df: brak kolumny {col} — najpierw dopięcie wejść")
    return df[col].astype(float)


def compute_funding_rate(df: pd.DataFrame) -> pd.Series:
    """Stawka funding rozliczona ściśle przed zamknięciem świecy (surowa, jak H2.1)."""
    return _need(df, "funding_raw").rename("funding_rate")


def compute_oi_change_24h(df: pd.DataFrame) -> pd.Series:
    """log(OI_d / OI_{d−1}) z ostatnich odczytów kolejnych świec 1d."""
    oi = _need(df, "oi_close")
    return np.log(oi / oi.shift(1)).rename("oi_change_24h")


def compute_global_ls_log(df: pd.DataFrame) -> pd.Series:
    """log(proporcja kont long/short) — ostatni odczyt w świecy."""
    return np.log(_need(df, "global_ls_close")).rename("global_ls_log")


def compute_taker_imbalance_24h(df: pd.DataFrame) -> pd.Series:
    """Średnia log(kupno/sprzedaż agresorów) ze wszystkich odczytów świecy (jedna świeca = 24 h)."""
    return _need(df, "taker_log_mean").rename("taker_imbalance_24h")


def compute_rv_30d(df: pd.DataFrame) -> pd.Series:
    """Zmienność zrealizowana: odch. std 30 dziennych log-zwrotów (trailing) × √365."""
    lr = np.log(_need(df, "close")).diff()
    return (
        lr.rolling(RV_WINDOW_DAYS, min_periods=RV_WINDOW_DAYS).std(ddof=1) * ANNUALIZATION
    ).rename("rv_30d")


def compute_vrp_30d(df: pd.DataFrame) -> pd.Series:
    """DVOL_{d−1}/100 − zmienność zrealizowana 30 dni."""
    return (_need(df, "dvol_d") / 100.0 - compute_rv_30d(df)).rename("vrp_30d")


def compute_ex_supply_change_7d(df: pd.DataFrame) -> pd.Series:
    """log(SplyExNtv_x / SplyExNtv_{x−7}) dnia x ≤ d − 2."""
    return _need(df, "ex_supply_change_7d_d").rename("ex_supply_change_7d")


def compute_fng_level(df: pd.DataFrame) -> pd.Series:
    """Fear & Greed dnia x ≤ d − 1, / 100."""
    return (_need(df, "fng_d") / 100.0).rename("fng_level")


ML1_FEATURE_FUNCTIONS = {
    "funding_rate": compute_funding_rate,
    "oi_change_24h": compute_oi_change_24h,
    "global_ls_log": compute_global_ls_log,
    "taker_imbalance_24h": compute_taker_imbalance_24h,
    "vrp_30d": compute_vrp_30d,
    "ex_supply_change_7d": compute_ex_supply_change_7d,
    "fng_level": compute_fng_level,
}
assert list(ML1_FEATURE_FUNCTIONS) == ML1_EXTERNAL


def build_ml1_frame(
    ohlcv: pd.DataFrame,
    funding: pd.DataFrame,
    metrics: pd.DataFrame,
    dvol: pd.DataFrame,
    coinmetrics: pd.DataFrame,
    fng: pd.DataFrame,
) -> pd.DataFrame:
    """Świece 1d + siedem cech spoza wykresu (kolumny `ML1_EXTERNAL`). Nie mutuje wejść."""
    out = attach_funding_1d(ohlcv.reset_index(drop=True), funding)
    out = attach_metrics_1d(out, metrics)
    out = attach_daily_sources(out, dvol, coinmetrics, fng)
    for name, fn in ML1_FEATURE_FUNCTIONS.items():
        out[name] = fn(out)
    return out


def load_ml1_sources(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Pliki źródłowe z `data_dir` (tryb `dane` skryptu rundy) → słownik ramek dla build_ml1_frame."""
    d = Path(data_dir)
    return {
        "funding": pd.read_parquet(
            d / "BTC-USDT-USDT_funding_20190910T000000Z_20260930T000000Z.parquet"
        ),
        "metrics": pd.read_parquet(d / "binance_metrics_BTCUSDT_5m.parquet"),
        "dvol": pd.read_parquet(d / "deribit_dvol_BTC_1d.parquet"),
        "coinmetrics": pd.read_parquet(d / "coinmetrics_btc_1d.parquet"),
        "fng": pd.read_parquet(d / "alternative_fng_1d.parquet"),
    }


# ------------------------------------------------------------------ reguły §14 (czyste)
def dedup_features(
    frame: pd.DataFrame, features: list[str], abs_rho: float = DEDUP_ABS_RHO
) -> list[str]:
    """Zachłannie w kolejności `features`: odpada cecha z |Spearman| > abs_rho do którejś zachowanej."""
    rho = frame[features].corr(method="spearman")
    kept: list[str] = []
    for f in features:
        if not any(abs(rho.loc[f, k]) > abs_rho for k in kept):
            kept.append(f)
    return kept


def confidence_threshold(confidence: pd.Series | np.ndarray, top_share: float) -> float:
    """Wartość progu = kwantyl (1 − top_share) pewności (interpolacja liniowa numpy)."""
    c = np.asarray(confidence, dtype=float)
    c = c[~np.isnan(c)]
    if len(c) == 0 or not 0.0 < top_share < 1.0:
        raise ValueError("confidence_threshold: puste wejście albo udział spoza (0, 1)")
    return float(np.quantile(c, 1.0 - top_share))


def signal_hits(
    direction: np.ndarray, label: np.ndarray, close_entry: np.ndarray, close_timeout: np.ndarray
) -> np.ndarray:
    """
    Trafność sygnału (§14.6): etykieta ±1 → kierunek == etykieta (ruch do pierwszej bariery);
    etykieta 0 (timeout) → znak(close po V − close wejścia) == kierunek; zero ruchu = pudło.
    """
    direction = np.asarray(direction, dtype=float)
    label = np.asarray(label, dtype=float)
    move = np.sign(np.asarray(close_timeout, dtype=float) - np.asarray(close_entry, dtype=float))
    realized = np.where(label != 0.0, label, move)
    return (realized * direction) > 0


def calibration_table(confidence: np.ndarray, hits: np.ndarray, n_buckets: int) -> pd.DataFrame:
    """Kubełki = kwantyle pewności (po randze, remisy wg kolejności); n, trafność, ±Wald, granice."""
    conf = np.asarray(confidence, dtype=float)
    hit = np.asarray(hits, dtype=bool)
    if len(conf) != len(hit) or len(conf) < n_buckets:
        raise ValueError("calibration_table: długości różne albo mniej sygnałów niż kubełków")
    ranks = pd.Series(conf).rank(method="first").to_numpy()
    bucket = np.minimum((ranks - 1) * n_buckets // len(conf), n_buckets - 1).astype(int)
    rows = []
    for b in range(n_buckets):
        sel = bucket == b
        n = int(sel.sum())
        p = float(hit[sel].mean())
        rows.append(
            {
                "kubelek": b + 1,
                "n": n,
                "pewnosc_od": float(conf[sel].min()),
                "pewnosc_do": float(conf[sel].max()),
                "trafnosc": p,
                "wald_95": float(1.959964 * np.sqrt(p * (1 - p) / n)),
            }
        )
    return pd.DataFrame(rows)
