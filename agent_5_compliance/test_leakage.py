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
from agents.ta_rules import TA_FEATURE_FUNCTIONS
from agents.positioning_features import POSITIONING_FEATURE_FUNCTIONS, RAW_COLUMN
from agents.external_features import EXTERNAL_FEATURE_FUNCTIONS
from agents.sw_features import (
    SW_POSITIONING_FUNCTIONS,
    attach_positioning_extra,
    rule_score,
)
from agents.funding_features import attach_funding_rate
from agents.labeling import compute_triple_barrier_labels

FEATURE_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "agents" / "feature_registry.yaml"

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


def test_ta_rule_functions_match_registry() -> None:
    """A2: cechy AT (agents/ta_rules.py) rejestrowane w sekcji `ta_rules:` registry, 1:1 z kodem."""
    with open(FEATURE_REGISTRY_PATH, encoding="utf-8") as f:
        registry = set(yaml.safe_load(f)["ta_rules"].keys())
    code = set(TA_FEATURE_FUNCTIONS.keys())
    assert (
        code == registry
    ), f"registry-only: {sorted(registry - code)}, code-only: {sorted(code - registry)}"


@pytest.mark.parametrize("feature_name", sorted(TA_FEATURE_FUNCTIONS.keys()))
def test_ta_rule_feature_no_leakage(synthetic_ohlcv: pd.DataFrame, feature_name: str) -> None:
    """
    A2 (CLAUDE.md zasada 2): to samo kryterium co `test_feature_no_leakage` dla cech AT ze skilla
    `ta-toolkit` — swingi, linie trendu, poziomy S/O i impulsy Fibonacciego są miejscem, gdzie
    AT leakuje najczęściej („ostatni szczyt" widoczny z przyszłości); tutaj każda cecha musi być
    bit w bit identyczna do CUTOFF niezależnie od tego, czy szereg kończy się na CUTOFF, czy
    ciągnie dalej.
    """
    fn = TA_FEATURE_FUNCTIONS[feature_name]
    df_full = synthetic_ohlcv
    df_past = df_full.iloc[:CUTOFF].reset_index(drop=True)
    pd.testing.assert_series_equal(
        fn(df_past).reset_index(drop=True),
        fn(df_full).iloc[:CUTOFF].reset_index(drop=True),
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


# ---------------------------------------------------------------------------
# H2.1b -- funding rate jako CECHA (pierwsze zrodlo informacji spoza OHLCV).
#
# CLAUDE.md zasada 2: test leakage PRZED wejsciem cechy do modelu, nie po.
# Ten blok jest bramka - czerwony test zatrzymuje runde H2.1 (regula STOP).
#
# Ryzyko jest tu INNE niz przy cechach z feature_miner.py. Tamte licza z OHLCV,
# wiec przeciek oznaczalby zle okno (centered zamiast trailing). Tutaj zlaczamy
# DWA ZRODLA o roznych siatkach czasowych (swiece co 4h, funding co 8h), wiec
# przeciek oznaczalby przypisanie swiecy stawki rozliczonej PO niej. Metoda
# truncate-vs-extend wykrywa oba, ale dokladamy trzeci test, ktory celuje
# wprost w ten mechanizm.
# ---------------------------------------------------------------------------


def _make_funding(n_periods: int = 60, start: str = "2020-01-01T00:00:00Z") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n_periods, freq="8h", tz="UTC")
    rng = np.random.default_rng(11)
    return pd.DataFrame({"timestamp": ts, "funding_rate": rng.normal(1e-4, 5e-5, n_periods)})


def _make_candles(n: int = 100, start: str = "2020-01-01T00:00:00Z") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n, freq="4h", tz="UTC")
    rng = np.random.default_rng(3)
    close = 100.0 + np.cumsum(rng.normal(0.0, 1.0, n))
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1_000.0,
        }
    )


def test_funding_feature_no_leakage_truncate_vs_extend() -> None:
    """
    Metoda 1 (ta sama co dla cech OHLCV): wartosci na df[:T] musza byc bit-identyczne
    z wartosciami na pelnym df do indeksu T-1.
    """
    candles, funding = _make_candles(), _make_funding()
    cut = 60

    full = attach_funding_rate(candles, funding)
    truncated = attach_funding_rate(candles.iloc[:cut], funding)

    pd.testing.assert_series_equal(
        full["funding_rate"].iloc[:cut],
        truncated["funding_rate"],
        check_names=False,
    )


def test_funding_feature_ignores_future_funding_records() -> None:
    """
    Metoda 2 (mutate-the-future), celowana w mechanizm zlaczenia dwoch zrodel:
    podmiana WSZYSTKICH rozliczen funding PO punkcie odciecia na zupelnie inne
    wartosci nie moze ruszyc ani jednej swiecy przed tym punktem.
    """
    candles, funding = _make_candles(), _make_funding()
    cutoff = candles["timestamp"].iloc[50]

    sabotaged = funding.copy()
    future = sabotaged["timestamp"] > cutoff
    assert future.any(), "fikstura musi zawierac rozliczenia po punkcie odciecia"
    sabotaged.loc[future, "funding_rate"] = 999.0

    before = attach_funding_rate(candles, funding)
    after = attach_funding_rate(candles, sabotaged)
    mask = candles["timestamp"] <= cutoff

    pd.testing.assert_series_equal(
        before.loc[mask.values, "funding_rate"],
        after.loc[mask.values, "funding_rate"],
        check_names=False,
    )


def test_funding_feature_never_uses_rate_settled_after_candle() -> None:
    """
    Metoda 3 (bezposrednia): dla KAZDEJ swiecy przypisana stawka musi pochodzic
    z rozliczenia o znaczniku <= znacznik swiecy. To jest dowod wprost, nie przez
    porownanie przebiegow.
    """
    candles, funding = _make_candles(), _make_funding()
    out = attach_funding_rate(candles, funding)
    lookup = dict(zip(funding["timestamp"], funding["funding_rate"], strict=True))

    for ts, value in zip(out["timestamp"], out["funding_rate"], strict=True):
        if pd.isna(value):
            continue
        zrodla = [t for t, v in lookup.items() if v == value]
        assert any(t <= ts for t in zrodla), f"swieca {ts} dostala stawke z przyszlosci"


def test_funding_feature_nan_before_first_settlement() -> None:
    """
    Swiece sprzed pierwszego rozliczenia dostaja NaN, a nie wsteczne wypelnienie.

    Wsteczne wypelnienie byloby przeciekiem najgorszego rodzaju: cicho podstawialoby
    przyszlosc w miejsce nieistniejacej jeszcze informacji.
    """
    funding = _make_funding(start="2020-01-05T00:00:00Z")
    candles = _make_candles(start="2020-01-01T00:00:00Z")
    out = attach_funding_rate(candles, funding)

    przed = out["timestamp"] < funding["timestamp"].min()
    assert przed.any(), "fikstura musi miec swiece sprzed pierwszego rozliczenia"
    assert out.loc[przed.values, "funding_rate"].isna().all()


def test_funding_feature_rejects_unsorted_input() -> None:
    """
    `merge_asof` na nieposortowanym wejsciu daje BLEDNE wyniki po cichu - a to jest
    dokladnie ten rodzaj usterki, ktory w tym projekcie produkowal falszywe liczby.
    """
    candles, funding = _make_candles(), _make_funding()
    with pytest.raises(ValueError):
        attach_funding_rate(candles.iloc[::-1], funding)
    with pytest.raises(ValueError):
        attach_funding_rate(candles, funding.iloc[::-1])


def test_funding_feature_preserves_candle_index() -> None:
    """
    Silnik POLEGA na zachowanym oryginalnym indeksie (patrz docstring backtest/engine.py) -
    `merge_asof` domyslnie go resetuje, wiec to jest realna pulapka, nie teoretyczna.
    """
    candles, funding = _make_candles(), _make_funding()
    przyciete = candles.iloc[20:60]
    out = attach_funding_rate(przyciete, funding)
    assert list(out.index) == list(przyciete.index)


def test_positioning_feature_functions_match_registry() -> None:
    """O1: cechy pozycjonowania (agents/positioning_features.py) 1:1 z sekcją `positioning:` registry."""
    with open(FEATURE_REGISTRY_PATH, encoding="utf-8") as f:
        registry = set(yaml.safe_load(f)["positioning"].keys())
    code = set(POSITIONING_FEATURE_FUNCTIONS.keys())
    assert (
        code == registry
    ), f"registry-only: {sorted(registry - code)}, code-only: {sorted(code - registry)}"


def _with_synthetic_oi(df: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """Dopina syntetyczny `oi_close` (random-walk lognormalny) — kontrakt wejścia cech pozycjonowania."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    out[RAW_COLUMN] = 50_000.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, len(df))))
    return out


@pytest.mark.parametrize("feature_name", sorted(POSITIONING_FEATURE_FUNCTIONS.keys()))
def test_positioning_feature_no_leakage(synthetic_ohlcv: pd.DataFrame, feature_name: str) -> None:
    """
    O1 (CLAUDE.md zasada 2): cecha pozycjonowania musi być bit w bit identyczna do CUTOFF
    niezależnie od tego, czy szereg kończy się na CUTOFF, czy ciągnie dalej (shift-forward).
    """
    fn = POSITIONING_FEATURE_FUNCTIONS[feature_name]
    df_full = _with_synthetic_oi(synthetic_ohlcv)
    df_past = df_full.iloc[:CUTOFF].reset_index(drop=True)
    pd.testing.assert_series_equal(
        fn(df_past).reset_index(drop=True),
        fn(df_full).iloc[:CUTOFF].reset_index(drop=True),
        check_names=False,
        check_exact=True,
    )


def test_external_feature_functions_match_registry() -> None:
    """L1/V1/G1: cechy zewnętrzne (agents/external_features.py) 1:1 z sekcją `external:` registry."""
    with open(FEATURE_REGISTRY_PATH, encoding="utf-8") as f:
        registry = set(yaml.safe_load(f)["external"].keys())
    code = set(EXTERNAL_FEATURE_FUNCTIONS.keys())
    assert (
        code == registry
    ), f"registry-only: {sorted(registry - code)}, code-only: {sorted(code - registry)}"


def _with_synthetic_external(df: pd.DataFrame, seed: int = 11) -> pd.DataFrame:
    """Syntetyczne kolumny dopięte (jak po attach_daily): dzienne wartości powtarzane na 6 świec."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    n_days = len(df) // 6 + 1
    out["ex_supply_change_7d_d"] = np.repeat(rng.normal(0.0, 0.01, n_days), 6)[: len(df)]
    out["dvol_d"] = np.repeat(rng.uniform(30.0, 120.0, n_days), 6)[: len(df)]
    out["fng_d"] = np.repeat(rng.integers(5, 96, n_days).astype(float), 6)[: len(df)]
    return out


@pytest.mark.parametrize("feature_name", sorted(EXTERNAL_FEATURE_FUNCTIONS.keys()))
def test_external_feature_no_leakage(synthetic_ohlcv: pd.DataFrame, feature_name: str) -> None:
    """L1/V1/G1 (CLAUDE.md zasada 2): shift-forward bit w bit do CUTOFF (jak cechy AT i pozycjonowania)."""
    fn = EXTERNAL_FEATURE_FUNCTIONS[feature_name]
    df_full = _with_synthetic_external(synthetic_ohlcv)
    df_past = df_full.iloc[:CUTOFF].reset_index(drop=True)
    pd.testing.assert_series_equal(
        fn(df_past).reset_index(drop=True),
        fn(df_full).iloc[:CUTOFF].reset_index(drop=True),
        check_names=False,
        check_exact=True,
    )


# ------------------------------------------------------------------ SW (2026-09-24)
def test_sw_positioning_functions_match_registry() -> None:
    """SW: cechy pozycjonowania serii SW (agents/sw_features.py) 1:1 z sekcją `sw_positioning:`."""
    with open(FEATURE_REGISTRY_PATH, encoding="utf-8") as f:
        registry = set(yaml.safe_load(f)["sw_positioning"].keys())
    code = set(SW_POSITIONING_FUNCTIONS.keys())
    assert (
        code == registry
    ), f"registry-only: {sorted(registry - code)}, code-only: {sorted(code - registry)}"


def _synthetic_metrics(start: pd.Timestamp, n_candles: int, seed: int = 13) -> pd.DataFrame:
    """Odczyty co 5 min (jak archiwum) z trzema proporcjami > 0."""
    rng = np.random.default_rng(seed)
    ts = pd.date_range(start, periods=n_candles * 48, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "sum_toptrader_long_short_ratio": np.exp(rng.normal(0.2, 0.1, len(ts))),
            "count_long_short_ratio": np.exp(rng.normal(0.3, 0.1, len(ts))),
            "sum_taker_long_short_vol_ratio": np.exp(rng.normal(0.0, 0.2, len(ts))),
        }
    )


def _as_4h(df: pd.DataFrame) -> pd.DataFrame:
    """Syntetyczne świece z siatką 4h UTC (cechy SW dopinają odczyty do świec 4h)."""
    return df.assign(timestamp=pd.date_range("2025-01-01", periods=len(df), freq="4h", tz="UTC"))


def _with_sw_positioning(df: pd.DataFrame) -> pd.DataFrame:
    df = _as_4h(df)
    start = pd.to_datetime(df["timestamp"].iloc[0], utc=True)
    return attach_positioning_extra(df, _synthetic_metrics(start, len(df) + 2))


@pytest.mark.parametrize("feature_name", sorted(SW_POSITIONING_FUNCTIONS.keys()))
def test_sw_positioning_feature_no_leakage(
    synthetic_ohlcv: pd.DataFrame, feature_name: str
) -> None:
    """SW (zasada 2): shift-forward bit w bit do CUTOFF — cecha nie zależy od świec po CUTOFF."""
    fn = SW_POSITIONING_FUNCTIONS[feature_name]
    df_full = _with_sw_positioning(synthetic_ohlcv)
    df_past = df_full.iloc[:CUTOFF].reset_index(drop=True)
    pd.testing.assert_series_equal(
        fn(df_past).reset_index(drop=True),
        fn(df_full).iloc[:CUTOFF].reset_index(drop=True),
        check_names=False,
        check_exact=True,
    )


def test_sw_attach_ignores_readings_after_candle(synthetic_ohlcv: pd.DataFrame) -> None:
    """Dopięcie: odczyty z chwili zamknięcia świecy i później nie zmieniają wartości tej świecy."""
    df = _as_4h(synthetic_ohlcv.iloc[:200].reset_index(drop=True))
    start = pd.to_datetime(df["timestamp"].iloc[0], utc=True)
    m = _synthetic_metrics(start, 202)
    base = attach_positioning_extra(df, m)
    cut = pd.to_datetime(df["timestamp"].iloc[100], utc=True)  # otwarcie świecy 100
    m2 = m.copy()
    late = m2["timestamp"] >= cut  # od zamknięcia świecy 99 wzwyż
    for c in (
        "sum_toptrader_long_short_ratio",
        "count_long_short_ratio",
        "sum_taker_long_short_vol_ratio",
    ):
        m2.loc[late, c] = m2.loc[late, c] * 7.0
    changed = attach_positioning_extra(df, m2)
    cols = ["toptrader_close", "global_ls_close", "taker_log_mean"]
    pd.testing.assert_frame_equal(base.loc[:99, cols], changed.loc[:99, cols])
    assert not np.allclose(base.loc[101:, "taker_log_mean"], changed.loc[101:, "taker_log_mean"])


def test_sw_rule_score_is_trailing() -> None:
    """Reguła SW: mediana trailing — dopisanie przyszłości nie zmienia kierunku przeszłych świec."""
    rng = np.random.default_rng(5)
    x = pd.Series(rng.normal(0.0, 1.0, 3000))
    x.iloc[::7] = 0.0001  # masa punktowa jak funding
    full = rule_score(x, -1, window=500, min_periods=200)
    past = rule_score(x.iloc[:1500], -1, window=500, min_periods=200)
    pd.testing.assert_series_equal(full.iloc[:1500], past, check_exact=True)
    assert full.iloc[:199].isna().all() and full.iloc[250:].notna().all()
    assert set(full.dropna().unique()) <= {-1.0, 0.0, 1.0}
