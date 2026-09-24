"""
sw_features.py — seria SW (cechy spoza wykresu, 2026-09-24): osiem cech spoza OHLCV na świecach 4h
BTC, każda ze ZNAKIEM Z MECHANIZMU zapisanym przed danymi, plus reguła bez modelu.

Po co: audyt AU1 (wniosek 87) wykazał, że cechy spoza wykresu badane jako 5. cecha modelu z oknem
60 dni NIE zostały zmierzone (model przenosi ~15–17 % przewagi słabej cechy). Seria SW mierzy je
dwiema drogami (decyzja użytkownika 2026-09-24): etap 1 — każda cecha osobno jako reguła, etap 2 —
jeden model ze wszystkimi naraz (okno 365 dni). Pre-rejestracja: `runs/2026-09-24_sw-cechy-spoza-wykresu/`.

Kontrakt jak w `positioning_features` / `external_features`: najpierw dopięcie surowych wejść znanych
w chwili świecy, potem czyste funkcje `compute_<nazwa>(df) -> pd.Series` (trailing). Nowe tu są trzy
cechy pozycjonowania (archiwum Binance `metrics`, 5 min): proporcja long/short dużych graczy, proporcja
long/short wszystkich kont, przewaga kupujących (taker). Pozostałe pięć — istniejące, przetestowane
funkcje (F1, O1, L1, V1, G1).

Reguła etapu 1: kierunek = znak_mechanizmu × sign(cecha − mediana cechy z ostatnich 365 dni).
Mediana, nie średnia: funding ma masę punktową na stawce bazowej (35,85 %, wniosek 15) — przy
medianie świeca ze stawką bazową daje 0 (brak transakcji), a nie sztuczny kierunek.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from agents.external_features import compute_external_feature
from agents.funding_features import FUNDING_COLUMN, attach_funding_rate
from agents.positioning_features import (
    METRICS_PATH,
    SNAPSHOT_OFFSET,
    attach_positioning,
    compute_oi_change_24h,
    load_metrics,
)

CANDLES_PER_DAY = 6
CANDLE = pd.Timedelta(hours=4)
RULE_WINDOW = 365 * CANDLES_PER_DAY  # mediana z 365 dni (= okno modelu etapu 2)
RULE_MIN_PERIODS = 180 * CANDLES_PER_DAY  # reguła startuje po pół roku historii cechy
TAKER_WINDOW = 6  # 24h

SNAPSHOT_COLUMNS = {
    "sum_toptrader_long_short_ratio": "toptrader_close",
    "count_long_short_ratio": "global_ls_close",
}
TAKER_SOURCE = "sum_taker_long_short_vol_ratio"
TAKER_RAW = "taker_log_mean"

# Kolejność = kolejność usuwania duplikatów w etapie 2 (przy |r| > 0,9 odpada cecha późniejsza).
# Znak: +1 = graj W KIERUNKU odchylenia cechy, −1 = PRZECIW (kontrariańsko). Zapisane przed danymi.
SW_FEATURES = {
    "funding_rate": (-1, "wysoki funding = tłok longów na dźwigni → korekta (rodzina D1)"),
    "oi_change_24h": (-1, "szybki przyrost OI = narastająca dźwignia → rozładowanie (E1)"),
    "toptrader_ls_log": (
        +1,
        "duzi gracze (top 20 % wg depozytu) lepiej poinformowani → za nimi (E2)",
    ),
    "global_ls_log": (-1, "przewaga kont long = tłok drobnych graczy → przeciw (E2)"),
    "taker_imbalance_24h": (+1, "przewaga agresywnych kupujących = przepływ zleceń → kontynuacja"),
    "vrp_30d": (
        +1,
        "wysoka premia za zmienność = przepłacone ubezpieczenie → premia za ryzyko (H1)",
    ),
    "ex_supply_change_7d": (-1, "napływ BTC na giełdy poprzedza sprzedaż (F1 on-chain)"),
    "fng_level": (-1, "chciwość → gorsze zwroty, strach → lepsze (kontrariańsko)"),
}


# ------------------------------------------------------------------ pozycjonowanie (nowe wejścia)
def load_metrics_extra(path: str | Path = METRICS_PATH) -> pd.DataFrame:
    """Archiwum 5 min → (timestamp, 3 kolumny proporcji); wartości ≤ 0 (błędy archiwum) = NaN."""
    m = pd.read_parquet(path)
    cols = [*SNAPSHOT_COLUMNS, TAKER_SOURCE]
    missing = {"timestamp", *cols} - set(m.columns)
    if missing:
        raise ValueError(f"metrics: brak kolumn {sorted(missing)}")
    out = m[["timestamp", *cols]].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)
    for c in cols:
        out[c] = out[c].astype(float)
        out.loc[out[c] <= 0, c] = np.nan
    return out.sort_values("timestamp").reset_index(drop=True)


def attach_positioning_extra(
    df: pd.DataFrame, metrics: pd.DataFrame, offset: pd.Timedelta = SNAPSHOT_OFFSET
) -> pd.DataFrame:
    """
    Dopina do świec 4h (`timestamp` = otwarcie): ostatni odczyt proporcji long/short (dwie kolumny)
    ściśle wewnątrz świecy, (open, open + offset], oraz średnią log(taker ratio) ze WSZYSTKICH
    odczytów w tym przedziale. Odczyt o `open` i o `open + 4h` nie należy do świecy (jak w O1).
    Brak odczytu → NaN. Nie mutuje `df`; odczyty późniejsze niż `open + offset` są niewidoczne.
    """
    if "timestamp" not in df.columns:
        raise ValueError("df: wymagana kolumna timestamp")
    opens = pd.to_datetime(df["timestamp"], utc=True).astype("datetime64[ns, UTC]")
    ts = pd.to_datetime(metrics["timestamp"], utc=True).astype("datetime64[ns, UTC]")
    # świeca, do której należy odczyt: open = podłoga(ts − 1 ns) do 4h; ważny, gdy ts − open ≤ offset
    owner = (ts - pd.Timedelta(1, "ns")).dt.floor(CANDLE)
    inside = (ts - owner) <= offset
    m = metrics.loc[inside.to_numpy()].assign(_open=owner[inside].to_numpy())
    out = df.copy()
    for src, dst in SNAPSHOT_COLUMNS.items():
        last = m.dropna(subset=[src]).groupby("_open")[src].last()
        out[dst] = opens.map(last).to_numpy(dtype=float)
    taker = np.log(m[TAKER_SOURCE]).groupby(m["_open"]).mean()
    out[TAKER_RAW] = opens.map(taker).to_numpy(dtype=float)
    return out


def compute_toptrader_ls_log(df: pd.DataFrame) -> pd.Series:
    """log(proporcja pozycji long/short 20 % największych kont) — ostatni odczyt w świecy."""
    if "toptrader_close" not in df.columns:
        raise ValueError("df: brak toptrader_close — najpierw attach_positioning_extra")
    return np.log(df["toptrader_close"].astype(float)).rename("toptrader_ls_log")


def compute_global_ls_log(df: pd.DataFrame) -> pd.Series:
    """log(proporcja kont long/short, wszystkie konta) — ostatni odczyt w świecy."""
    if "global_ls_close" not in df.columns:
        raise ValueError("df: brak global_ls_close — najpierw attach_positioning_extra")
    return np.log(df["global_ls_close"].astype(float)).rename("global_ls_log")


def compute_taker_imbalance_24h(df: pd.DataFrame) -> pd.Series:
    """Średnia z 6 świec (24h) średniego log(wolumen kupna/sprzedaży agresorów) w świecy."""
    if TAKER_RAW not in df.columns:
        raise ValueError(f"df: brak {TAKER_RAW} — najpierw attach_positioning_extra")
    x = df[TAKER_RAW].astype(float)
    return x.rolling(TAKER_WINDOW, min_periods=TAKER_WINDOW).mean().rename("taker_imbalance_24h")


SW_POSITIONING_FUNCTIONS = {
    "toptrader_ls_log": compute_toptrader_ls_log,
    "global_ls_log": compute_global_ls_log,
    "taker_imbalance_24h": compute_taker_imbalance_24h,
}


# ------------------------------------------------------------------ reguła etapu 1
def rule_score(
    x: pd.Series, sign: int, window: int = RULE_WINDOW, min_periods: int = RULE_MIN_PERIODS
) -> pd.Series:
    """
    Kierunek reguły: `sign` × sign(x − mediana x z ostatnich `window` świec, łącznie z bieżącą).
    Trailing (bez przyszłości); NaN, dopóki okno ma < `min_periods` obserwacji albo x jest NaN;
    0, gdy x równa się medianie (brak transakcji).
    """
    if sign not in (-1, 1):
        raise ValueError("sign musi być −1 albo +1")
    med = x.rolling(window, min_periods=min_periods).median()
    out = sign * np.sign(x - med)
    return out.where(x.notna() & med.notna())


# ------------------------------------------------------------------ składanie ramki
def build_sw_frame(
    df: pd.DataFrame,
    funding: pd.DataFrame,
    metrics_oi: pd.DataFrame | None = None,
    metrics_extra: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Świece 4h + osiem cech SW (kolumny o nazwach z `SW_FEATURES`). Nie mutuje `df`."""
    out = attach_funding_rate(df, funding)
    out = attach_positioning(out, load_metrics() if metrics_oi is None else metrics_oi)
    out["oi_change_24h"] = compute_oi_change_24h(out)
    extra = load_metrics_extra() if metrics_extra is None else metrics_extra
    out = attach_positioning_extra(out, extra)
    for name, fn in SW_POSITIONING_FUNCTIONS.items():
        out[name] = fn(out)
    for name in ("vrp_30d", "ex_supply_change_7d", "fng_level"):
        out = compute_external_feature(out, name)
    missing = set(SW_FEATURES) - set(out.columns)
    if missing:
        raise RuntimeError(f"brak cech: {sorted(missing)}")
    assert FUNDING_COLUMN in SW_FEATURES
    return out
