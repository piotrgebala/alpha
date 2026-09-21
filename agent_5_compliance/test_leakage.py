"""
test_leakage.py

Formalny test leakage (Warstwa 2 piramidy testow, docs/rag/05_metodologia_wytwarzania_i_testow.md)
dla wszystkich funkcji cech w agents/feature_miner.py. Metodologia pelna:
docs/rag/02_cechy_i_leakage.md, sekcja "Metodologia testu leakage".

Dwie uzupelniajace sie metody:

1. Truncate-vs-extend (test_feature_no_leakage, parametryzowany po wszystkich
   kluczach FEATURE_FUNCTIONS): licz ceche na df[:T] i na df[:T+k] (pelnym df),
   porownaj wartosci do indeksu T-1 wlacznie -- musza byc bit-identyczne. Jesli
   funkcja nielegalnie zaglada w przyszlosc (np. rolling(center=True), globalna
   normalizacja po calym zbiorze), wartosci przed T zmienia sie po dodaniu
   wierszy T..T+k-1.

2. Mutate-the-future (test_atr_pctrank_20d_trailing_not_centered): dla cechy
   z najwyzszym ryzykiem leakage (`atr_pctrank_20d`, priorytet z docs/rag/02),
   podmienia swiece PO punkcie odciecia na zupelnie inne dane i sprawdza, ze
   wartosci przed punktem odciecia sie nie zmieniaja -- bardziej bezposredni
   dowod "trailing, nie centered" niz metoda 1 sama w sobie.

Nieformalny sanity check (9/9 na danych syntetycznych) byl zrobiony przy
Commicie 2 (agents/feature_miner.py) -- ten plik jest formalna, automatyczna
wersja odpalana w CI (.github/workflows/tests.yml), nie duplikatem.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from agents.feature_miner import FEATURE_FUNCTIONS, compute_atr_pctrank_20d
from agents.labeling import compute_triple_barrier_labels

FEATURE_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent / "agents" / "feature_registry.yaml"
)

# atr_pctrank_20d z domyslnymi parametrami (candles_per_day=288, window_days=20)
# potrzebuje 5760 wierszy, zanim da nie-NaN wynik -- dane musza byc odpowiednio
# duze, zeby test parametryzowany faktycznie cwiczyl te sciezke kodu, nie tylko
# porownywal same NaN.
N_ROWS = 6000
CUTOFF = 5900


def _make_synthetic_ohlcv(n_rows: int, seed: int) -> pd.DataFrame:
    """
    Deterministyczny, syntetyczny OHLCV: random-walk cen (log-returns ~N(0, 0.001))
    + poprawny kontrakt OHLC (high = max(open,close)*(1+u), low = min(open,close)*(1-u)).
    Nie modeluje realnej mikrostruktury rynku -- potrzebny tylko poprawny ksztalt
    danych wejsciowych zgodny z kontraktem funkcji compute_* z feature_miner.py.
    """
    rng = np.random.default_rng(seed)
    log_returns = rng.normal(loc=0.0, scale=0.001, size=n_rows)
    close = 100.0 * np.cumprod(1.0 + log_returns)
    open_ = np.empty(n_rows)
    open_[0] = 100.0
    open_[1:] = close[:-1]
    spread = rng.uniform(0.0, 0.002, size=n_rows)
    high = np.maximum(open_, close) * (1.0 + spread)
    low = np.minimum(open_, close) * (1.0 - spread)
    volume = rng.uniform(10.0, 1000.0, size=n_rows)
    timestamp = pd.date_range("2026-01-01", periods=n_rows, freq="5min")
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


@pytest.fixture(scope="module")
def synthetic_ohlcv() -> pd.DataFrame:
    return _make_synthetic_ohlcv(N_ROWS, seed=42)


def test_feature_functions_matches_registry() -> None:
    """
    Sanity (Commit 2.9/Z15): FEATURE_FUNCTIONS musi byc 1:1 zgodne z kluczami
    `features` w agents/feature_registry.yaml (zrodlo prawdy metadanych cech).
    Wczesniejsza wersja hardkodowala liste nazw (test_feature_functions_covers_all_
    nine/ten) i wymagala recznej edycji przy kazdej nowej cesze — teraz czyta YAML,
    wiec rozjazd registry<->kod jest lapany przez pytest lokalnie, nie dopiero przez
    inline-check w .github/workflows/tests.yml (ktory zostaje jako druga linia).
    """
    with open(FEATURE_REGISTRY_PATH, encoding="utf-8") as f:
        registry = set(yaml.safe_load(f)["features"].keys())
    code = set(FEATURE_FUNCTIONS.keys())
    assert (
        code == registry
    ), f"registry-only: {sorted(registry - code)}, code-only: {sorted(code - registry)}"


@pytest.mark.parametrize("feature_name", sorted(FEATURE_FUNCTIONS.keys()))
def test_feature_no_leakage(synthetic_ohlcv: pd.DataFrame, feature_name: str) -> None:
    """
    C3.1: dla kazdej funkcji w FEATURE_FUNCTIONS, wartosci cechy do indeksu
    CUTOFF-1 musza byc bit-identyczne niezaleznie od tego, czy DataFrame konczy
    sie na CUTOFF, czy ciagnie sie dalej do N_ROWS (df[:T] vs df[:T+k], patrz
    docs/rag/02).
    """
    fn = FEATURE_FUNCTIONS[feature_name]
    df_full = synthetic_ohlcv
    df_past = df_full.iloc[:CUTOFF].reset_index(drop=True)

    series_past = fn(df_past)
    series_full = fn(df_full)

    pd.testing.assert_series_equal(
        series_past.reset_index(drop=True),
        series_full.iloc[:CUTOFF].reset_index(drop=True),
        check_names=False,
        check_exact=True,
    )


def test_atr_pctrank_20d_trailing_not_centered() -> None:
    """
    C3.2 (priorytet z docs/rag/02): atr_pctrank_20d ma najwieksze ryzyko
    leakage w calym zestawie cech, bo rolling window MUSI byc trailing
    (konczacy sie na aktualnej swiecy), nigdy centered. Ten test podmienia
    WYLACZNIE swiece PO punkcie odciecia na zupelnie inne dane i sprawdza, ze
    wartosci PRZED punktem odciecia sie nie zmieniaja -- zlapaloby regresje do
    rolling(center=True) bardziej bezposrednio niz test_feature_no_leakage.
    """
    window_kwargs = {
        "candles_per_day": 10,
        "window_days": 5,
    }  # window=50, szybszy test niz 5760
    n_rows = 300
    cutoff = 250

    df = _make_synthetic_ohlcv(n_rows, seed=1)
    original = compute_atr_pctrank_20d(df, **window_kwargs)

    future_replacement = _make_synthetic_ohlcv(n_rows - cutoff, seed=999)
    mutated_df = df.copy()
    for col in ("open", "high", "low", "close", "volume"):
        mutated_df.loc[cutoff:, col] = future_replacement[col].values

    mutated = compute_atr_pctrank_20d(mutated_df, **window_kwargs)

    pd.testing.assert_series_equal(
        original.iloc[:cutoff].reset_index(drop=True),
        mutated.iloc[:cutoff].reset_index(drop=True),
        check_names=False,
        check_exact=True,
    )


def test_triple_barrier_no_leakage(synthetic_ohlcv: pd.DataFrame) -> None:
    """
    C4.5: labelki z definicji patrza w przyszlosc (to NIE jest leakage -- to jest
    cel triple-barrier). Ryzyko leakage tutaj to bug zagladajacy DALEJ w przyszlosc
    niz zadeklarowane `vertical_barrier_candles`, albo blad offsetu/alignmentu.

    Metodologia (analogiczna do test_feature_no_leakage, ale dostosowana): licz
    labelki na df[:CUTOFF] i na pelnym df, porownaj WYLACZNIE wiersze t, ktorych
    PELNE okno w przod miesci sie w obcietych danych (t + vertical_barrier_candles
    < CUTOFF) -- te musza byc bit-identyczne niezaleznie od tego, czy df konczy sie
    na CUTOFF czy ciagnie sie dalej. Wiersze blizej granicy obciecia POPRAWNIE
    roznia sie (NaN w wersji obcietej z braku danych w przod, nie bug) -- celowo
    wykluczone z porownania.
    """
    vertical_barrier_candles = 12
    df_full = synthetic_ohlcv
    df_past = df_full.iloc[:CUTOFF].reset_index(drop=True)

    result_past = compute_triple_barrier_labels(
        df_past, vertical_barrier_candles=vertical_barrier_candles
    )
    result_full = compute_triple_barrier_labels(
        df_full, vertical_barrier_candles=vertical_barrier_candles
    )

    comparable = CUTOFF - vertical_barrier_candles
    pd.testing.assert_frame_equal(
        result_past.iloc[:comparable].reset_index(drop=True),
        result_full.iloc[:comparable].reset_index(drop=True),
        check_exact=True,
    )
