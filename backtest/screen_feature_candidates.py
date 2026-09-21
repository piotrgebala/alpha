"""
screen_feature_candidates.py

Commit 2.7 — przegląd kandydatek nowych cech PRZED formalnym testem OOS, zgodnie z
"Rozszerzanie feature setu — protokół" (docs/rag/02_cechy_i_leakage.md, sekcja na końcu
pliku) i CLAUDE.md zasada 4 ("jedna cecha na raz, mierzona OOS — nigdy grid search po
wielu kombinacjach naraz").

KONTEKST: po C2.5 (rekalibracja progów regime — NO-GO, falsyfikacja) i C2.6 (odporność na
timeframe 1h/4h — NO-GO, edge kierunkowy nieobecny/ujemny), otwarte pytanie użytkownika:
"czy nie lepiej zrobić X zmiennych i sprawdzić korelacje między nimi, a dopiero później
zbudować model". Odpowiedź metodologiczna (uzgodniona z użytkownikiem): TAK dla korelacji
cecha-cecha (bezpieczne, cały zbiór, brak ryzyka leakage/data dredging — służy wyłącznie do
wykrycia REDUNDANCJI, np. |corr| > 0.7 = dwie cechy niosą tę samą informację). Korelacja
cecha-target jest z definicji podglądaniem etykiety na całym zbiorze — więc jest tutaj
WYŁĄCZNIE opisowa/eksploracyjna (nigdy jako bramka selekcji, nigdy jako "dowód" edge'u).
Jedyny krok o wadze dowodowej to formalny walk-forward jednej, pojedynczej cechy (przyszły
Commit, poza tym skryptem).

CO TEN SKRYPT ROBI (trzy bloki, wszystkie read-only — zero zmian w pipeline/config):
  1. Dolicza 8 nowych kandydatek (4 rodziny: volatility, momentum, mean-reversion, volume),
     każda świadomie NIE-redundantna z 9 cechami już w `agents/feature_miner.FEATURE_FUNCTIONS`
     na podstawie definicji wzoru (nie podglądania wyniku).
  2. Macierz korelacji Spearman cecha-cecha (17x17: 9 istniejących + 8 nowych) na całym
     zbiorze — identyfikuje pary redundantne (|corr| > 0.7).
  3. Korelacja Spearman cecha-target (etykieta triple-barrier jako -1/0/1 porządkowe),
     osobno dla regime=trend i regime=range — WYŁĄCZNIE opisowa, oznaczona w output jako
     EKSPLORACYJNE, bez p-value (żeby nie sugerować istotności statystycznej, której to
     porównanie nie ustala — patrz punkt 1 protokołu, multiple testing).

CZEGO TEN SKRYPT NIE ROBI: nie trenuje modelu, nie uruchamia walk-forward, nie wybiera
"zwycięskiej" cechy, nie dodaje niczego do `agents/feature_miner.FEATURE_FUNCTIONS` ani do
`agents/ml_optimizer.MOMENTUM_FEATURES`/`REVERSION_FEATURES`. Formalne testy jednostkowe +
leakage (CLAUDE.md zasada 2/10) mają sens dopiero, gdy JEDNA cecha z tego przeglądu zostanie
wybrana do promocji — nie na etapie screeningu.

Użycie:
    py -m backtest.screen_feature_candidates
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import talib
import yaml

from agents.feature_miner import FEATURE_FUNCTIONS, compute_all_features
from agents.labeling import compute_triple_barrier_labels
from agents.ml_optimizer import MOMENTUM_FEATURES, REVERSION_FEATURES
from data.fetch_ohlcv import get_ohlcv_cached

# Próg redundancji cecha-cecha — opisowy, nie jest bramką automatycznego odrzucenia (decyzja
# przy użytkowniku, jak w calibrate_regime_thresholds.py / diagnose_cost_feasibility.py).
REDUNDANCY_THRESHOLD = 0.7

# Przypisanie do rodziny + modelu docelowego (Test 1 = trend/momentum, Test 2 = range/mean-
# reversion) — WYŁĄCZNIE opisowe metadane dla czytelności output, nie wpływa na obliczenia.
FAMILY_ASSIGNMENT = {
    "atr_14": "volatility (regime gate)",
    "atr_pctrank_20d": "volatility (regime gate)",
    "direction_persistence_10": "trend-strength (regime gate)",
    "return_lag_1": "momentum (Test 1 + Test 2, wspólna)",
    "momentum_5": "momentum (Test 1, w modelu)",
    "ema_diff_9_21": "momentum (Test 1, w modelu)",
    "volume_zscore_20": "volume (Test 1 + Test 2, wspólna, w modelu)",
    "rsi_14": "mean-reversion (Test 2, w modelu)",
    "price_zscore_20": "mean-reversion (Test 2, w modelu)",
    "bb_width_20": "volatility (KANDYDAT)",
    "realized_vol_20": "volatility (KANDYDAT)",
    "roc_20": "momentum (KANDYDAT, Test 1)",
    "adx_14": "trend-strength (KANDYDAT, Test 1)",
    "bb_pctb_20": "mean-reversion (KANDYDAT, Test 2)",
    "vwap_deviation_20": "mean-reversion (KANDYDAT, Test 2)",
    "obv_zscore_20": "volume (KANDYDAT)",
    "volume_roc_10": "volume (KANDYDAT)",
}

# ---------------------------------------------------------------------------
# 8 nowych kandydatek, 4 rodziny — czyste, bezstanowe funkcje, ten sam kontrakt co
# agents/feature_miner.py (trailing/rolling wyłącznie, zero .shift(-n), zero normalizacji po
# całym zbiorze). NIE wchodzą do agents/feature_miner.FEATURE_FUNCTIONS na tym etapie — to
# screening przed-rejestracyjny (CLAUDE.md zasada 2: formalny test leakage dopiero przy
# wejściu do modelu, nie na etapie eksploracji).
# ---------------------------------------------------------------------------


def compute_bb_width_20(df: pd.DataFrame) -> pd.Series:
    """Szerokość wstęgi Bollingera, okno 20 (TA-Lib BBANDS, 2 odch. std): (upper-lower)/middle.
    Rodzina volatility — inna baza niż atr_14 (close-to-close band, nie high-low range).
    """
    upper, middle, lower = talib.BBANDS(
        df["close"].values, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
    )
    width = (upper - lower) / middle
    return pd.Series(width, index=df.index, name="bb_width_20")


def compute_realized_vol_20(df: pd.DataFrame) -> pd.Series:
    """Rolling odch. std. log-zwrotów, okno 20, trailing — zmienność close-to-close,
    komplementarna do ATR (high-low range) i bb_width_20 (band width)."""
    log_ret = np.log(df["close"] / df["close"].shift(1))
    vol = log_ret.rolling(window=20, min_periods=20).std()
    return vol.rename("realized_vol_20")


def compute_roc_20(df: pd.DataFrame) -> pd.Series:
    """Log-return względem świecy t-20 — dłuższy horyzont niż istniejące momentum_5 (t-5)."""
    roc = np.log(df["close"] / df["close"].shift(20))
    return roc.rename("roc_20")


def compute_adx_14(df: pd.DataFrame) -> pd.Series:
    """Average Directional Index, 14-period (TA-Lib) — siła trendu NIEZALEŻNA od kierunku,
    ciągła (w odróżnieniu od dyskretnej direction_persistence_10, patrz C2.5)."""
    adx = talib.ADX(
        df["high"].values, df["low"].values, df["close"].values, timeperiod=14
    )
    return pd.Series(adx, index=df.index, name="adx_14")


def compute_bb_pctb_20(df: pd.DataFrame) -> pd.Series:
    """Pozycja %B w obrębie wstęg Bollingera, okno 20: (close-lower)/(upper-lower).
    Komplementarna do price_zscore_20 (ta sama idea "gdzie w rozkładzie", inna normalizacja).
    """
    upper, _middle, lower = talib.BBANDS(
        df["close"].values, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
    )
    pctb = (df["close"].values - lower) / (upper - lower)
    return pd.Series(pctb, index=df.index, name="bb_pctb_20")


def compute_vwap_deviation_20(df: pd.DataFrame) -> pd.Series:
    """Odchylenie close od rolling VWAP (typical_price=(high+low+close)/3, ważony wolumenem),
    okno 20, trailing: (close-vwap)/vwap. Waży cenę wolumenem — price_zscore_20 nie."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = typical_price * df["volume"]
    rolling_pv = pv.rolling(window=20, min_periods=20).sum()
    rolling_vol = df["volume"].rolling(window=20, min_periods=20).sum()
    vwap = rolling_pv / rolling_vol
    deviation = (df["close"] - vwap) / vwap
    return deviation.rename("vwap_deviation_20")


def compute_obv_zscore_20(df: pd.DataFrame) -> pd.Series:
    """Rolling z-score skumulowanego On-Balance-Volume (TA-Lib OBV), okno 20 — poziom
    kumulacji/dystrybucji wolumenu w czasie, inne niż CHWILOWY volume_zscore_20."""
    obv = talib.OBV(df["close"].values, df["volume"].values)
    obv_series = pd.Series(obv, index=df.index)
    roll = obv_series.rolling(window=20, min_periods=20)
    z = (obv_series - roll.mean()) / roll.std()
    return z.rename("obv_zscore_20")


def compute_volume_roc_10(df: pd.DataFrame) -> pd.Series:
    """Rate-of-change wolumenu względem t-10: volume[t]/volume[t-10] - 1."""
    roc = df["volume"] / df["volume"].shift(10) - 1.0
    return roc.rename("volume_roc_10")


CANDIDATE_FUNCTIONS = {
    "bb_width_20": compute_bb_width_20,
    "realized_vol_20": compute_realized_vol_20,
    "roc_20": compute_roc_20,
    "adx_14": compute_adx_14,
    "bb_pctb_20": compute_bb_pctb_20,
    "vwap_deviation_20": compute_vwap_deviation_20,
    "obv_zscore_20": compute_obv_zscore_20,
    "volume_roc_10": compute_volume_roc_10,
}


# ---------------------------------------------------------------------------
# Orkiestracja / raportowanie
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_data(cfg: dict) -> pd.DataFrame:
    data_cfg = cfg["data"]
    df = get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=data_cfg["timeframe"],
        start=data_cfg["start"],
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )
    print(f"[data] {len(df)} świec, {df['timestamp'].min()} -> {df['timestamp'].max()}")
    return df


def _build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """9 istniejących cech + regime (compute_all_features) + 8 nowych kandydatek + label."""
    out = compute_all_features(df)
    for name, fn in CANDIDATE_FUNCTIONS.items():
        out[name] = fn(df)
    labels = compute_triple_barrier_labels(df)
    out["label"] = labels["label"]
    return out


def _print_redundancy_pairs(corr: pd.DataFrame, feature_names: list[str]) -> None:
    print(
        f"\n[blok 2] Pary cecha-cecha z |Spearman corr| > {REDUNDANCY_THRESHOLD} (potencjalna redundancja):"
    )
    pairs = []
    for i, a in enumerate(feature_names):
        for b in feature_names[i + 1 :]:
            c = corr.loc[a, b]
            if pd.notna(c) and abs(c) > REDUNDANCY_THRESHOLD:
                pairs.append((a, b, c))
    if not pairs:
        print(f"  (brak par powyżej progu {REDUNDANCY_THRESHOLD})")
        return
    pairs.sort(key=lambda t: -abs(t[2]))
    for a, b, c in pairs:
        print(
            f"  {a:28s} <-> {b:28s}  corr={c:+.3f}   [{FAMILY_ASSIGNMENT.get(a, '?')}] / [{FAMILY_ASSIGNMENT.get(b, '?')}]"
        )


def _print_target_correlation(
    feat_df: pd.DataFrame, feature_names: list[str], regime: str
) -> None:
    subset = feat_df[feat_df["regime"] == regime]
    subset = subset.dropna(subset=["label"])
    n = len(subset)
    print(
        f"\n  regime='{regime}': n={n} świec z etykietą (po odrzuceniu warmup/NaN label)"
    )
    if n == 0:
        print("    (brak świec w tym reżimie z ważną etykietą — nie liczę korelacji)")
        return
    rows = []
    for name in feature_names:
        c = subset[name].corr(subset["label"], method="spearman")
        rows.append((name, c))
    rows.sort(key=lambda t: -abs(t[1]) if pd.notna(t[1]) else 0)
    for name, c in rows:
        marker = " <- KANDYDAT" if "KANDYDAT" in FAMILY_ASSIGNMENT.get(name, "") else ""
        c_str = f"{c:+.4f}" if pd.notna(c) else "   NaN"
        print(
            f"    {name:28s} spearman={c_str}   [{FAMILY_ASSIGNMENT.get(name, '?')}]{marker}"
        )


def main() -> None:
    cfg = _load_config()
    df = _load_data(cfg)
    feat_df = _build_feature_frame(df)

    existing_names = list(FEATURE_FUNCTIONS.keys())
    candidate_names = list(CANDIDATE_FUNCTIONS.keys())
    all_names = existing_names + candidate_names

    print(
        f"\n[blok 1] {len(existing_names)} cech istniejących + {len(candidate_names)} kandydatek = {len(all_names)} razem"
    )
    print(f"  Istniejące (agents/feature_miner.FEATURE_FUNCTIONS): {existing_names}")
    print(f"  Nowe kandydatki (ten skrypt, poza registry):         {candidate_names}")
    print(
        f"  W modelu Test 1 (MOMENTUM_FEATURES, agents/ml_optimizer.py): {MOMENTUM_FEATURES}"
    )
    print(
        f"  W modelu Test 2 (REVERSION_FEATURES, agents/ml_optimizer.py): {REVERSION_FEATURES}"
    )

    nan_counts = feat_df[all_names].isna().sum()
    print("\n  Liczba NaN per cecha (warmup wskaźnika, oczekiwane na początku serii):")
    for name in all_names:
        print(f"    {name:28s} {int(nan_counts[name]):6d} / {len(feat_df)}")

    # --- Blok 2: korelacja cecha-cecha, Spearman, cały zbiór (bezpieczne — brak leakage,
    # nie dotyka etykiety) ---
    corr_matrix = feat_df[all_names].corr(method="spearman")
    print(
        "\n[blok 2] Macierz korelacji Spearman cecha-cecha (cały zbiór, zaokrąglone do 2 miejsc):"
    )
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(corr_matrix.round(2).to_string())
    _print_redundancy_pairs(corr_matrix, all_names)

    # --- Blok 3: korelacja cecha-target, Spearman, per regime — EKSPLORACYJNE, nie selekcja ---
    print(
        "\n[blok 3] Korelacja Spearman cecha-target (label triple-barrier jako -1/0/1)"
    )
    print("  UWAGA: to jest OPISOWE/EKSPLORACYJNE na CAŁYM zbiorze (nie OOS) — patrz")
    print(
        "  docs/rag/02_cechy_i_leakage.md 'Rozszerzanie feature setu — protokół', punkt 1"
    )
    print(
        "  (multiple testing / data dredging). NIE jest to bramka selekcji ani dowód edge'u."
    )
    print(
        "  Jedyny krok o wadze dowodowej: formalny walk-forward JEDNEJ wybranej cechy (przyszły Commit)."
    )
    print("  Cechy dopasowane do modelu docelowego regime'u (patrz FAMILY_ASSIGNMENT):")
    trend_feature_names = [n for n in all_names if n not in ("label",)]
    _print_target_correlation(feat_df, trend_feature_names, regime="trend")
    _print_target_correlation(feat_df, trend_feature_names, regime="range")

    print(
        "\n[koniec] Ten skrypt nie wybiera 'zwycięskiej' cechy i nie modyfikuje registry/configu."
    )
    print(
        "  Decyzja, którą JEDNĄ cechę testować formalnie w walk-forward, należy do użytkownika."
    )


if __name__ == "__main__":
    main()
