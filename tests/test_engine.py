"""
test_engine.py

Warstwa 4 (integracyjne) testy dla backtest/engine.py — cały pipeline: cechy ->
labels -> regime split -> walk-forward -> trening+predykcja -> sizing -> koszty ->
equity curve. Nie testuje jakości modelu (to Commit 6 / realne dane) — sprawdza,
że pipeline wykonuje się end-to-end na danych syntetycznych i produkuje poprawnie
ustrukturyzowany wynik.

`_make_pipeline_test_ohlcv` konstruuje dane z jawnie odseparowanymi segmentami ATR/
kierunku (ambiguous warmup -> trend -> range), żeby DETERMINISTYCZNIE (dla ustalonego
seeda) wywołać OBA reżimy classify_regime — czysto losowe dane (i.i.d.) dają reżim
"range" dużo częściej niż "trend" (ryzyko odnotowane w STATUS.md C2.5), więc nie
gwarantowałyby ćwiczenia obu ścieżek.

UWAGA (Commit 2d): testy w tym pliku, które powstały PRZED bramką wykonalności kosztowej,
przekazują jawnie `min_barrier_to_cost_ratio=0.0` (bramka wyłączona). Powód: segment
"range" w `_make_pipeline_test_ohlcv` ma z KONSTRUKCJI bardzo mały ATR (szum std=0.15
wokół stałego poziomu), czyli dokładnie przypadek, który bramka blokuje — bez tego
wyłączenia testy kill-switcha przestałyby testować kill-switcha, bo nie doszłoby do
żadnej transakcji. Sama bramka ma własny test integracyjny niżej
(`test_run_backtest_cost_gate_blocks_narrow_barrier_signals`).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agents.labeling import ATR_MULTIPLIER
from agents.ml_optimizer import REVERSION_FEATURES
from agents.risk_controller import MIN_BARRIER_TO_COST_RATIO
import backtest.engine as engine_module
from backtest.costs import (
    MAKER,
    TAKER,
    funding_cost,
    gate_cost_fraction,
    total_round_trip_cost,
)
from backtest.engine import (
    DEFAULT_CANDLES_PER_DAY,
    DEFAULT_TREND_THRESHOLD,
    EXECUTION_MAKER_LIMIT,
    EXECUTION_TAKER_ONLY,
    PREREGISTERED_CONFIDENCE_QUANTILE,
    TRADE_COLUMNS,
    _execution_legs,
    _resolve_exit_reason,
    _train_fold_confidence_threshold,
    run_backtest,
)

N_WARMUP = (
    5760  # 20 dni @ 5m - wymagane, by atr_pctrank_20d (feature_miner.py) nie było NaN
)
N_TREND = 2880  # 10 dni - segment o wysokim, trwałym ATR + konsekwentny kierunek -> regime="trend"
N_RANGE = 2880  # 10 dni - segment o niskim ATR + losowym kierunku -> regime="range"


def _make_pipeline_test_ohlcv(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[tuple[float, float, float, float]] = []
    price = 100.0

    # Warmup: umiarkowany losowy ruch — punkt odniesienia ATR, klasyfikowany "ambiguous".
    # std=0.15 (nie 1.0) świadomie mały — kumulatywne odchylenie po 5760 krokach
    # (~11 przy std=0.15) musi zostać dużo mniejsze niż price=100 startowe, żeby cena
    # nigdy nie spadła <= 0 (co dałoby invalid log w return_lag_1/momentum_5).
    for _ in range(N_WARMUP):
        step = rng.normal(0.0, 0.15)
        o, c = price, price + step
        h, low_ = max(o, c) + 0.5, min(o, c) - 0.5
        rows.append((o, h, low_, c))
        price = c

    # Trend: silny konsekwentny dryf w górę + wysoki true range -> wysoki atr_pctrank_20d
    # ORAZ wysoki direction_persistence_10 -> regime="trend".
    for _ in range(N_TREND):
        o = price
        c = price + rng.uniform(3.0, 4.0)
        h, low_ = c + 1.0, o - 1.0
        rows.append((o, h, low_, c))
        price = c

    # Range: mały szum wokół stałego poziomu -> niski atr_pctrank_20d oraz niski
    # direction_persistence_10 (losowy znak zwrotu) -> regime="range".
    range_level = price
    for _ in range(N_RANGE):
        o = range_level + rng.normal(0.0, 0.15)
        c = range_level + rng.normal(0.0, 0.15)
        h, low_ = max(o, c) + 0.05, min(o, c) - 0.05
        rows.append((o, h, low_, c))

    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df["volume"] = rng.uniform(50.0, 150.0, size=len(df))
    df["timestamp"] = pd.date_range(
        "2026-01-01", periods=len(df), freq="5min", tz="UTC"
    )
    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def test_run_backtest_produces_trades_for_both_regimes() -> None:
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)

    result = run_backtest(
        raw_ohlcv,
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    folds_summary = result["folds_summary"]
    regimes_with_signals = {
        f["regime"] for f in folds_summary if not f["skipped"] and f["n_signals"] > 0
    }
    assert "trend" in regimes_with_signals
    assert "range" in regimes_with_signals

    trades = result["trades"]
    assert list(trades.columns) == TRADE_COLUMNS
    assert len(trades) > 0
    not_suppressed = ~trades["kill_switch_active"]
    assert (trades.loc[not_suppressed, "position_size"] > 0).all()
    assert (trades["cost"] >= 0).all()
    assert set(trades["signal_direction"].unique()).issubset({-1.0, 1.0})

    equity_curve = result["equity_curve"]
    assert list(equity_curve.columns) == ["timestamp", "equity"]
    assert equity_curve["timestamp"].is_monotonic_increasing
    assert equity_curve["equity"].iloc[0] == 10_000.0
    assert result["final_equity"] == equity_curve["equity"].iloc[-1]


def test_run_backtest_empty_regime_has_correct_schema() -> None:
    # Dataset krótszy niż okno rolling atr_pctrank_20d (5760 świec) -> regime
    # zawsze "ambiguous" -> ZERO sygnałów w obu reżimach, ale bez crasha.
    rng = np.random.default_rng(1)
    n = 500
    close = 100.0 + np.cumsum(rng.normal(0.0, 0.5, size=n))
    open_ = np.roll(close, 1)
    open_[0] = 100.0
    high = np.maximum(open_, close) + 0.3
    low = np.minimum(open_, close) - 0.3
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(50.0, 150.0, size=n),
        }
    )

    result = run_backtest(df, train_days=1, test_days=1, step_days=1)

    assert list(result["trades"].columns) == TRADE_COLUMNS
    assert len(result["trades"]) == 0
    assert len(result["equity_curve"]) == 1
    assert result["final_equity"] == 10_000.0
    assert all(f["skipped"] for f in result["folds_summary"])


def _oversized_risk_controller_fn(
    *, signal_direction, signal_confidence, regime, atr_14, entry_price, equity
):
    """Stub risk_controller_fn celowo PRZESADZONY (~50x normalnego stosunku
    notional/equity, ignorujący normalny cap 3x z agents.risk_controller).
    Uzasadnienie: gross_pnl I cost skalują się liniowo z position_size, więc samo
    powiększenie position_size nie wymusza straty (proporcja zysk/koszt się nie
    zmienia) — ale oversized position_size wielokrotnie przekraczający normalny
    leverage cap sprawia, że JEDNA transakcja w złym kierunku (model nie jest
    100% trafny, szczególnie na "range") generuje spadek equity o dziesiątki %,
    deterministycznie wywołując kill-switch niezależnie od jakości predykcji.
    """
    oversized_position_size = (equity * 50.0) / entry_price
    return {
        "position_size": oversized_position_size,
        "stop_price": entry_price - signal_direction * ATR_MULTIPLIER * atr_14,
        "take_profit_price": entry_price + signal_direction * ATR_MULTIPLIER * atr_14,
    }


def test_run_backtest_kill_switch_suppresses_signals_after_large_drawdown() -> None:
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)

    result = run_backtest(
        raw_ohlcv,
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        risk_controller_fn=_oversized_risk_controller_fn,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    trades = result["trades"]
    assert trades["kill_switch_active"].any()

    suppressed = trades[trades["kill_switch_active"]]
    assert (suppressed["position_size"] == 0.0).all()
    assert (suppressed["equity_before"] == suppressed["equity_after"]).all()


def test_run_backtest_kill_switch_re_arms_after_cooldown() -> None:
    # Commit 2c: bez cooldown/re-arm, equity zamrożone przez suppresję nigdy się nie
    # zmienia (position_size=0.0 -> net_pnl=0.0), więc peak_equity/drawdown też się
    # nie zmieniają -> kill-switch, raz aktywny, zostawałby aktywny NA ZAWSZE
    # (deadlock potwierdzony empirycznie w Commit 2b). Cooldown celowo BARDZO krótki
    # (ułamek dnia), żeby zaobserwować re-arm w krótkim oknie danych syntetycznych
    # bez czekania na realne KILL_SWITCH_COOLDOWN_DAYS=7 dni.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)

    result = run_backtest(
        raw_ohlcv,
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        risk_controller_fn=_oversized_risk_controller_fn,
        kill_switch_cooldown_days=0.01,  # ~14 minut — wyłącznie do testu
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    trades = result["trades"].sort_values("timestamp").reset_index(drop=True)
    assert trades["kill_switch_active"].any()

    first_suppressed_pos = trades.index[trades["kill_switch_active"]][0]
    later_rows = trades.iloc[first_suppressed_pos:]
    later_active = later_rows.loc[~later_rows["kill_switch_active"]]
    assert len(later_active) > 0, (
        "Kill-switch powinien ponownie się uzbroić (re-arm) po cooldownie i wpuścić "
        "kolejny sygnał, zamiast zostać aktywny na zawsze (deadlock z Commit 2b)."
    )
    assert (later_active["position_size"] > 0.0).all()


def test_run_backtest_cost_gate_blocks_narrow_barrier_signals() -> None:
    # Commit 2d (Warstwa 4, integracyjny): ta sama próbka syntetyczna, dwa przebiegi —
    # bramka wyłączona (0.0) vs włączona (wartość startowa 2.0). Segment "range" w
    # `_make_pipeline_test_ohlcv` ma z konstrukcji bardzo wąską barierę względem kosztu,
    # więc bramka MUSI odciąć część sygnałów i policzyć je w n_signals_cost_gated.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
    )

    without_gate = run_backtest(raw_ohlcv, min_barrier_to_cost_ratio=0.0, **kwargs)
    with_gate = run_backtest(raw_ohlcv, min_barrier_to_cost_ratio=2.0, **kwargs)

    n_signals_off = sum(f["n_signals"] for f in without_gate["folds_summary"])
    n_signals_on = sum(f["n_signals"] for f in with_gate["folds_summary"])
    n_gated_off = sum(f["n_signals_cost_gated"] for f in without_gate["folds_summary"])
    n_gated_on = sum(f["n_signals_cost_gated"] for f in with_gate["folds_summary"])

    # Bramka wyłączona -> nikt nie jest odrzucany; włączona -> odrzuca i zmniejsza pulę.
    assert n_gated_off == 0
    assert n_gated_on > 0
    assert n_signals_on < n_signals_off

    # Zachowanie księgowe: każdy sygnał jest albo dopuszczony, albo odrzucony — bez
    # gubienia po drodze (te same sygnały kandydujące, inny podział).
    assert n_signals_on + n_gated_on == n_signals_off

    # Schemat i niezmienniki trade journalu bez zmian (bramka nie dodaje wierszy).
    assert list(with_gate["trades"].columns) == TRADE_COLUMNS
    real = with_gate["trades"].loc[~with_gate["trades"]["kill_switch_active"]]
    assert (real["position_size"] > 0).all()


def test_run_backtest_cost_gate_default_is_enabled() -> None:
    # Bramka jest domyślnie WŁĄCZONA (MIN_BARRIER_TO_COST_RATIO), nie opt-in — wywołanie
    # bez jawnego argumentu musi dawać ten sam wynik co jawne podanie wartości startowej.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
    )

    default_run = run_backtest(raw_ohlcv, **kwargs)
    explicit_run = run_backtest(
        raw_ohlcv, min_barrier_to_cost_ratio=MIN_BARRIER_TO_COST_RATIO, **kwargs
    )

    assert sum(f["n_signals"] for f in default_run["folds_summary"]) == sum(
        f["n_signals"] for f in explicit_run["folds_summary"]
    )
    assert default_run["final_equity"] == explicit_run["final_equity"]


def test_run_backtest_threads_regime_thresholds_to_signal_population() -> None:
    # Commit 2.5 (Warstwa 4, integracyjny): `trend_threshold`/`range_threshold` muszą
    # dotrzeć od run_backtest() aż do compute_all_features()/classify_regime() —
    # weryfikujemy to zachowaniem, nie samym przekazaniem argumentu (por.
    # test_compute_all_features_threads_thresholds_to_regime_column w
    # tests/test_feature_miner.py, który sprawdza to na poziomie niżej).
    #
    # Segment "trend" w `_make_pipeline_test_ohlcv` ma z konstrukcji wysoki, ale
    # SKOŃCZONY atr_pctrank_20d/direction_persistence_10 — próg 0.99 jest wybrany, by
    # być wyżej niż jakakolwiek świeca może osiągnąć, więc MUSI wyzerować sygnały w
    # reżimie trend, gdyby próg faktycznie nie docierał do classify_regime (np. gdyby
    # run_backtest go przyjmował, ale nie przekazywał dalej), test by tego nie wykrył.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    baseline = run_backtest(
        raw_ohlcv, trend_threshold=DEFAULT_TREND_THRESHOLD, **kwargs
    )
    unreachable_threshold = run_backtest(raw_ohlcv, trend_threshold=0.99, **kwargs)

    def _trend_signals(result: dict) -> int:
        return sum(
            f["n_signals"] for f in result["folds_summary"] if f["regime"] == "trend"
        )

    assert _trend_signals(baseline) > 0
    assert _trend_signals(unreachable_threshold) == 0


def test_run_backtest_threads_candles_per_day_to_signal_population() -> None:
    # Commit 2.6 (Warstwa 4, integracyjny): `candles_per_day` musi dotrzeć od run_backtest()
    # aż do compute_atr_pctrank_20d() (przez compute_all_features -> classify_regime) — ten
    # sam wzorzec co test_run_backtest_threads_regime_thresholds_to_signal_population dla C2.5.
    #
    # candles_per_day=100_000 daje okno atr_pctrank_20d = 100_000*20 = 2_000_000 świec —
    # znacznie więcej niż len(_make_pipeline_test_ohlcv())=11520 — więc atr_pctrank_20d
    # MUSI być w całości NaN -> regime w całości "ambiguous" -> ZERO sygnałów w OBU
    # reżimach, gdyby parametr faktycznie docierał do classify_regime. Gdyby run_backtest
    # przyjmował go, ale nie przekazywał dalej (pozostając przy domyślnym 288), baseline
    # trend/range nadal miałby sygnały — test by tego nie wykrył.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    baseline = run_backtest(
        raw_ohlcv, candles_per_day=DEFAULT_CANDLES_PER_DAY, **kwargs
    )
    starved = run_backtest(raw_ohlcv, candles_per_day=100_000, **kwargs)

    def _total_signals(result: dict) -> int:
        return sum(f["n_signals"] for f in result["folds_summary"])

    assert _total_signals(baseline) > 0
    assert _total_signals(starved) == 0


def test_run_backtest_threads_regime_feature_sets_to_model_training() -> None:
    # Commit 2.8 (Warstwa 4, integracyjny): `regime_feature_sets` musi dotrzeć od
    # run_backtest() aż do _collect_candidate_signals() (trening modelu per regime),
    # nie zostać po cichu zignorowane na rzecz modułowej stałej REGIME_FEATURE_SETS.
    # Dowód: podanie nieistniejącej nazwy kolumny jako cechy MUSI wywołać KeyError przy
    # `train_df.dropna(subset=[*feature_columns, "label"])` — gdyby run_backtest
    # przyjmował parametr, ale go nie przekazywał dalej (nadal używając baseline
    # MOMENTUM_FEATURES), błędu by nie było.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )
    bogus_feature_sets = [
        ("trend", ["nonexistent_feature_xyz"]),
        ("range", REVERSION_FEATURES),
    ]

    with pytest.raises(KeyError):
        run_backtest(raw_ohlcv, regime_feature_sets=bogus_feature_sets, **kwargs)


def test_run_backtest_threads_fold_start_offset_to_walk_forward() -> None:
    # Commit 2.9 (Z1, Warstwa 4, integracyjny): `fold_start_offset_days` musi dotrzeć
    # od run_backtest() przez _collect_candidate_signals() do
    # generate_walk_forward_folds() — dowód zachowaniem: pierwszy fold każdego reżimu
    # w folds_summary startuje o DOKŁADNIE offset dni później niż w baseline. Gdyby
    # parametr był przyjmowany, ale nieprzekazywany, train_start byłyby identyczne.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    baseline = run_backtest(raw_ohlcv, fold_start_offset_days=0.0, **kwargs)
    shifted = run_backtest(raw_ohlcv, fold_start_offset_days=1.0, **kwargs)

    def _first_train_start(result: dict, regime: str):
        starts = [
            f["train_start"]
            for f in result["folds_summary"]
            if f["regime"] == regime and f["train_start"] is not None
        ]
        return min(starts) if starts else None

    for regime in ("trend", "range"):
        base_start = _first_train_start(baseline, regime)
        shifted_start = _first_train_start(shifted, regime)
        assert base_start is not None and shifted_start is not None
        assert shifted_start == base_start + pd.Timedelta(days=1)


def test_run_backtest_threads_candle_minutes_to_funding_cost() -> None:
    # Commit 2.9 (Z11, Warstwa 4, integracyjny): `candle_minutes` musi dotrzeć od
    # run_backtest() do backtest.costs.total_round_trip_cost — składnik funding
    # zależy od REALNEGO czasu trzymania (candles * minuty), nie liczby świec.
    # Dowód zachowaniem: te same dane i sygnały, inne candle_minutes -> inne koszty
    # (fee/slippage identyczne, funding przeskalowany 12x), a domyślne == jawne 5.
    raw_ohlcv = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(
        train_days=5,
        test_days=2,
        step_days=2,
        num_boost_round=50,
        early_stopping_rounds=10,
        min_barrier_to_cost_ratio=0.0,  # Commit 2d — patrz UWAGA w docstringu modułu
    )

    default_run = run_backtest(raw_ohlcv, **kwargs)
    explicit_5 = run_backtest(raw_ohlcv, candle_minutes=5, **kwargs)
    minutes_60 = run_backtest(raw_ohlcv, candle_minutes=60, **kwargs)

    real_default = default_run["trades"].loc[
        ~default_run["trades"]["kill_switch_active"]
    ]
    real_5 = explicit_5["trades"].loc[~explicit_5["trades"]["kill_switch_active"]]
    real_60 = minutes_60["trades"].loc[~minutes_60["trades"]["kill_switch_active"]]

    # Domyślna wartość == jawne 5 (bez zmiany zachowania sprzed Commitu 2.9).
    assert real_default["cost"].sum() == pytest.approx(real_5["cost"].sum())

    # PIERWSZA transakcja obu przebiegów jest w pełni porównywalna (identyczny sygnał,
    # identyczne equity startowe -> identyczny position_size i gross), różni się
    # WYŁĄCZNIE komponentem funding kosztu (12x dłuższy czas trzymania w minutach).
    # Dalsze transakcje mogą się już rozjechać (inne koszty -> inna ścieżka equity ->
    # inny moment kill-switcha) — i to rozjechanie też jest dowodem threadingu, ale
    # asercja na pierwszej transakcji jest deterministyczna.
    first_5 = real_5.iloc[0]
    first_60 = real_60.iloc[0]
    assert first_60["timestamp"] == first_5["timestamp"]
    assert first_60["gross_pnl"] == pytest.approx(first_5["gross_pnl"])
    assert first_60["cost"] != pytest.approx(first_5["cost"])


# ---------------------------------------------------------------------------
# Commit 2.12 (Backlog Z6): model wykonania maker/taker + kolumna exit_reason
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "direction, label, expected",
    [
        (1.0, 1.0, "tp"),  # long, trafiona górna bariera
        (1.0, -1.0, "sl"),  # long, trafiona dolna bariera
        (-1.0, -1.0, "tp"),  # short, trafiona dolna bariera => ZYSK
        (-1.0, 1.0, "sl"),  # short, trafiona górna bariera => STRATA
        (1.0, 0.0, "timeout"),
        (-1.0, 0.0, "timeout"),
    ],
)
def test_resolve_exit_reason_needs_direction_and_label(
    direction: float, label: float, expected: str
) -> None:
    """Sam `label` nie wystarcza: short na etykiecie -1 to TP, nie SL."""
    assert _resolve_exit_reason(direction, label) == expected


def test_resolve_exit_reason_nan_label_is_timeout() -> None:
    assert _resolve_exit_reason(1.0, float("nan")) == "timeout"


def test_execution_legs_taker_only_ignores_exit_reason() -> None:
    for reason in ("tp", "sl", "timeout"):
        assert _execution_legs(EXECUTION_TAKER_ONLY, reason) == (TAKER, TAKER)


def test_execution_legs_maker_limit_depends_on_exit_reason() -> None:
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "tp") == (MAKER, MAKER)
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "sl") == (MAKER, TAKER)
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "timeout") == (MAKER, TAKER)


def test_execution_legs_rejects_unknown_model() -> None:
    with pytest.raises(ValueError):
        _execution_legs("maker_only", "tp")


def test_run_backtest_journal_exit_reason_matches_direction_times_label() -> None:
    """Kolumna w journalu musi zgadzać się z czystą funkcją na KAŻDYM wierszu."""
    result = run_backtest(
        _make_pipeline_test_ohlcv(seed=7),
        train_days=5,
        test_days=2,
        step_days=2,
        min_barrier_to_cost_ratio=0.0,  # syntetyczne ATR jest małe wobec ceny
    )
    real = result["trades"].loc[~result["trades"]["kill_switch_active"]]
    assert len(real) > 0
    assert set(real["exit_reason"].unique()) <= {"tp", "sl", "timeout"}
    # Transakcje TP muszą mieć dodatni gross_pnl, SL ujemny — to definicja obu pojęć.
    assert (real.loc[real["exit_reason"] == "tp", "gross_pnl"] > 0).all()
    assert (real.loc[real["exit_reason"] == "sl", "gross_pnl"] < 0).all()


def test_run_backtest_taker_only_reproduces_pre_c212_costs() -> None:
    """
    REGRESJA BASELINE'U: execution_model='taker_only' musi dać DOKŁADNIE ten sam koszt
    co model sprzed Commitu 2.12 (2x taker + 2x slippage + funding). Bez tego nie da się
    uczciwie porównać rund — C2.10/C2.11 przestałyby być odtwarzalne.
    """
    raw = _make_pipeline_test_ohlcv(seed=7)
    result = run_backtest(
        raw,
        train_days=5,
        test_days=2,
        step_days=2,
        min_barrier_to_cost_ratio=0.0,
        execution_model=EXECUTION_TAKER_ONLY,
    )
    real = result["trades"].loc[~result["trades"]["kill_switch_active"]]
    assert len(real) > 0
    for _, row in real.iterrows():
        notional = row["position_size"] * row["entry_price"]
        expected = total_round_trip_cost(
            notional=notional,
            holding_candles=row["exit_bar_offset"],
            direction=row["signal_direction"],
        )
        assert row["cost"] == pytest.approx(expected)


def test_run_backtest_maker_model_is_cheaper_than_taker_only() -> None:
    """Sedno Rundy 2 na poziomie pipeline'u, nie tylko formuły."""
    raw = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0)
    taker = run_backtest(raw, execution_model=EXECUTION_TAKER_ONLY, **kwargs)
    maker = run_backtest(raw, execution_model=EXECUTION_MAKER_LIMIT, **kwargs)

    def mean_cost_fraction(result: dict) -> float:
        real = result["trades"].loc[~result["trades"]["kill_switch_active"]]
        return (real["cost"] / (real["position_size"] * real["entry_price"])).mean()

    assert mean_cost_fraction(maker) < mean_cost_fraction(taker)


# ---------------------------------------------------------------------------
# Commit 2.13: prog pewnosci kalibrowany WEWNATRZ walk-forward
# ---------------------------------------------------------------------------


class _StubBooster:
    """Nie dotyka XGBoost — testujemy politykę progu, nie uczenie modelu."""


def test_confidence_threshold_disabled_returns_none(monkeypatch) -> None:
    assert _train_fold_confidence_threshold(_StubBooster(), pd.DataFrame(), [], None) is None


def test_confidence_threshold_comes_from_train_not_test(monkeypatch) -> None:
    """
    NAJWAŻNIEJSZY test tej rundy: próg MUSI pochodzić z foldu treningowego.
    Rozkłady są rozjechane celowo — gdyby próg liczył się z testu, wyszłoby ~0.9,
    a nie ~0.5, więc test jednoznacznie odróżnia obie implementacje.
    """
    train_conf = pd.DataFrame(
        {"signal_direction": [1.0] * 5, "signal_confidence": [0.1, 0.2, 0.3, 0.4, 0.5]}
    )
    test_conf = pd.DataFrame(
        {"signal_direction": [1.0] * 5, "signal_confidence": [0.9, 0.9, 0.9, 0.9, 0.9]}
    )
    seen: list[int] = []

    def fake_predict_signal(booster, df, feature_columns):
        seen.append(len(df))
        return train_conf if len(df) == 5 else test_conf

    monkeypatch.setattr("backtest.engine.predict_signal", fake_predict_signal)
    threshold = _train_fold_confidence_threshold(
        _StubBooster(), pd.DataFrame(index=range(5)), [], confidence_quantile=1.0
    )
    assert threshold == pytest.approx(0.5)  # max z TRENINGU, nie 0.9 z testu


def test_confidence_threshold_ignores_flat_signals(monkeypatch) -> None:
    """direction == 0 to brak sygnału — nie może współtworzyć rozkładu progu."""
    frame = pd.DataFrame(
        {
            "signal_direction": [0.0, 0.0, 1.0, -1.0],
            "signal_confidence": [0.99, 0.99, 0.10, 0.20],
        }
    )
    monkeypatch.setattr("backtest.engine.predict_signal", lambda *a, **k: frame)
    threshold = _train_fold_confidence_threshold(
        _StubBooster(), pd.DataFrame(index=range(4)), [], confidence_quantile=1.0
    )
    assert threshold == pytest.approx(0.20)


def test_confidence_threshold_none_when_no_directional_signals(monkeypatch) -> None:
    frame = pd.DataFrame({"signal_direction": [0.0, 0.0], "signal_confidence": [0.5, 0.6]})
    monkeypatch.setattr("backtest.engine.predict_signal", lambda *a, **k: frame)
    assert (
        _train_fold_confidence_threshold(
            _StubBooster(), pd.DataFrame(index=range(2)), [], confidence_quantile=0.75
        )
        is None
    )


def test_run_backtest_confidence_quantile_none_reproduces_baseline() -> None:
    """q=None musi dać wynik bit-identyczny z baseline'em — inaczej rundy nieporównywalne."""
    raw = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0)
    base = run_backtest(raw, **kwargs)
    explicit_none = run_backtest(raw, confidence_quantile=None, **kwargs)
    assert base["final_equity"] == explicit_none["final_equity"]
    assert len(base["trades"]) == len(explicit_none["trades"])


def test_run_backtest_confidence_quantile_zero_admits_everything() -> None:
    """q=0 to prog rowny minimum -> nic nie powinno zostac odrzucone przez pewnosc."""
    raw = _make_pipeline_test_ohlcv(seed=7)
    result = run_backtest(
        raw,
        train_days=5,
        test_days=2,
        step_days=2,
        min_barrier_to_cost_ratio=0.0,
        confidence_quantile=0.0,
    )
    gated = sum(f["n_signals_confidence_gated"] for f in result["folds_summary"])
    assert gated == 0


def test_run_backtest_higher_quantile_never_admits_more_signals() -> None:
    """
    Niezmiennik monotoniczności: ostrzejszy próg nie może przepuścić WIĘCEJ SYGNAŁÓW.

    Mierzone na `n_signals` (etap `_collect_candidate_signals`, przed symulacją equity),
    bo tylko tam ta własność musi zachodzić. Na poziomie WYKONANYCH transakcji
    monotoniczność NIE obowiązuje i nie jest to błąd bramki, tylko zależność od ścieżki:
    odfiltrowanie stratnej transakcji zmienia krzywą equity, co zmienia stan kill-switcha,
    a ten decyduje o supresji późniejszych sygnałów. Empirycznie (fixture seed=7):
    q=0.0 -> 1131 transakcji, q=0.5 -> 1139. Asercja na transakcjach testowałaby więc
    nieprawdziwą własność systemu.
    """
    raw = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0)
    counts = []
    for q in (0.0, 0.5, PREREGISTERED_CONFIDENCE_QUANTILE):
        result = run_backtest(raw, confidence_quantile=q, **kwargs)
        counts.append(sum(f["n_signals"] for f in result["folds_summary"]))
    assert counts[0] >= counts[1] >= counts[2]
    assert counts[0] > counts[2], "próg 0.75 musi cokolwiek odfiltrować na tym fixture"


def test_run_backtest_confidence_gate_accounting_is_consistent() -> None:
    """Odrzucenia przez pewność muszą być policzone, a nie zniknąć po cichu."""
    raw = _make_pipeline_test_ohlcv(seed=7)
    result = run_backtest(
        raw,
        train_days=5,
        test_days=2,
        step_days=2,
        min_barrier_to_cost_ratio=0.0,
        confidence_quantile=PREREGISTERED_CONFIDENCE_QUANTILE,
    )
    active = [f for f in result["folds_summary"] if not f["skipped"]]
    assert active, "fixture musi wyprodukować choć jeden aktywny fold"
    assert sum(f["n_signals_confidence_gated"] for f in active) > 0
    for fold in active:
        assert fold["confidence_threshold"] is not None


# ---------------------------------------------------------------------------
# Z22 (Backlog II): horyzont etykiety jako parametr run_backtest
# ---------------------------------------------------------------------------


def test_run_backtest_vertical_barrier_changes_timeout_share() -> None:
    """
    Krótszy horyzont => cena rzadziej zdąża trafić barierę => WIĘCEJ timeoutów.
    Niezmiennik kierunkowy, nie konkretna liczba.
    """
    raw = _make_pipeline_test_ohlcv(seed=7)
    kwargs = dict(train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0)

    def timeout_share(v: int) -> float:
        result = run_backtest(raw, vertical_barrier_candles=v, **kwargs)
        real = result["trades"].loc[~result["trades"]["kill_switch_active"]]
        assert len(real) > 0
        return float((real["exit_reason"] == "timeout").mean())

    assert timeout_share(3) > timeout_share(12)


def test_run_backtest_embargo_follows_vertical_barrier_by_default() -> None:
    """
    Embargo musi iść za horyzontem etykiety — inaczej ogon treningu z etykietami
    sięgającymi w okno testowe wróciłby do walidacji (regres Z17+Z21).
    """
    captured: dict = {}
    original = engine_module._collect_candidate_signals

    def spy(*args, **kwargs):
        captured["embargo"] = kwargs["embargo_candles"]
        return original(*args, **kwargs)

    engine_module._collect_candidate_signals = spy
    try:
        run_backtest(
            _make_pipeline_test_ohlcv(seed=7),
            train_days=5, test_days=2, step_days=2,
            min_barrier_to_cost_ratio=0.0, vertical_barrier_candles=7,
        )
    finally:
        engine_module._collect_candidate_signals = original
    assert captured["embargo"] == 7


def test_run_backtest_explicit_embargo_overrides_default() -> None:
    captured: dict = {}
    original = engine_module._collect_candidate_signals

    def spy(*args, **kwargs):
        captured["embargo"] = kwargs["embargo_candles"]
        return original(*args, **kwargs)

    engine_module._collect_candidate_signals = spy
    try:
        run_backtest(
            _make_pipeline_test_ohlcv(seed=7),
            train_days=5, test_days=2, step_days=2,
            min_barrier_to_cost_ratio=0.0, vertical_barrier_candles=7, embargo_candles=0,
        )
    finally:
        engine_module._collect_candidate_signals = original
    assert captured["embargo"] == 0


def test_run_backtest_single_regime_produces_only_that_regime() -> None:
    """Architektura jednoreżimowa: przekazanie jednego zestawu cech => tylko ten reżim."""
    result = run_backtest(
        _make_pipeline_test_ohlcv(seed=7),
        train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0,
        regime_feature_sets=[("range", REVERSION_FEATURES)],
    )
    assert {f["regime"] for f in result["folds_summary"]} == {"range"}


def test_folds_summary_counts_model_abstention() -> None:
    """
    Walidacja S1: `direction == 0` bylo NAJWIEKSZYM filtrem lejka (70,9% swiec OOS na 4h)
    i jedynym bez licznika, przez co `p` czytano jak wielkosc bezwarunkowa. Bilans lejka
    musi sie domykac: ocenione = bez_kierunku + przepuszczone + odrzucone przez bramki.
    """
    result = run_backtest(
        _make_pipeline_test_ohlcv(seed=7),
        train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0,
    )
    active = [f for f in result["folds_summary"] if not f["skipped"]]
    assert active, "fixture musi wyprodukowac aktywny fold"
    for fold in active:
        assert fold["n_rows_evaluated"] == (
            fold["n_signals"]
            + fold["n_signals_no_direction"]
            + fold["n_signals_cost_gated"]
            + fold["n_signals_confidence_gated"]
        ), "bilans lejka musi sie domykac w kazdym foldzie"
    assert sum(f["n_rows_evaluated"] for f in active) > 0


def test_skipped_folds_report_zero_funnel_counters() -> None:
    result = run_backtest(
        _make_pipeline_test_ohlcv(seed=7),
        train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0,
    )
    for fold in result["folds_summary"]:
        if fold["skipped"]:
            assert fold["n_signals_no_direction"] == 0
            assert fold["n_rows_evaluated"] == 0


# --- H3: noga "timeout" jako pasmo + bramka niemogaca rozjechac sie z journalem ---

_H3_KWARGS = dict(train_days=5, test_days=2, step_days=2, min_barrier_to_cost_ratio=0.0)
_FUNNEL_KEYS = (
    "n_rows_evaluated",
    "n_signals_no_direction",
    "n_signals_confidence_gated",
    "n_signals_cost_gated",
    "n_signals",
)


def test_execution_legs_threads_timeout_leg() -> None:
    """Wariant dociera przez cienka delegacje w engine do costs.execution_legs."""
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "timeout", MAKER) == (MAKER, MAKER)
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "timeout", TAKER) == (MAKER, TAKER)
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "tp", MAKER) == (MAKER, MAKER)
    assert _execution_legs(EXECUTION_MAKER_LIMIT, "sl", MAKER) == (MAKER, TAKER)


def test_execution_legs_rejects_unknown_exit_reason() -> None:
    """Do H3 literowka w `exit_reason` cicho wybierala TAKER."""
    with pytest.raises(ValueError):
        _execution_legs(EXECUTION_MAKER_LIMIT, "vertical")


@pytest.mark.parametrize("execution_model", [EXECUTION_MAKER_LIMIT, EXECUTION_TAKER_ONLY])
@pytest.mark.parametrize("timeout_leg", [MAKER, TAKER])
def test_cost_gate_value_equals_gate_cost_fraction(execution_model, timeout_leg) -> None:
    """
    TEST SPOJNOSCI BRAMKA<->JOURNAL na poziomie pipeline'u.

    Przechwytuje `cost_fraction`, ktory silnik realnie wstrzykuje do `is_cost_feasible`,
    i porownuje z `gate_cost_fraction`. Do H3 ta wartosc byla literalem w engine.py, nie
    zwiazanym z niczym. Ten test PEKA NATYCHMIAST, gdyby ktos do literalu wrocil.
    """
    captured: dict = {}
    original = engine_module.is_cost_feasible

    def spy(*args, **kwargs):
        captured["cost_fraction"] = kwargs["cost_fraction"]
        return original(*args, **kwargs)

    engine_module.is_cost_feasible = spy
    try:
        run_backtest(
            _make_pipeline_test_ohlcv(seed=7),
            execution_model=execution_model,
            timeout_leg=timeout_leg,
            **_H3_KWARGS,
        )
    finally:
        engine_module.is_cost_feasible = original

    assert captured["cost_fraction"] == gate_cost_fraction(execution_model, timeout_leg)


@pytest.mark.parametrize("timeout_leg", [MAKER, TAKER])
def test_journal_cost_never_exceeds_gate_cost_fraction(timeout_leg) -> None:
    """
    Integracyjny odpowiednik property testu z test_costs.py: na REALNYCH wierszach
    journalu koszt (bez funding) nigdy nie przekracza tego, co zalozyla bramka.

    Funding odejmowany, bo bramka swiadomie go nie zawiera (costs.round_trip_cost_fraction).
    """
    result = run_backtest(
        _make_pipeline_test_ohlcv(seed=7), timeout_leg=timeout_leg, **_H3_KWARGS
    )
    trades = result["trades"]
    real = trades[~trades["kill_switch_active"].astype(bool)]
    assert len(real) > 0, "fikstura musi produkowac transakcje, inaczej test nic nie sprawdza"
    gate = gate_cost_fraction(EXECUTION_MAKER_LIMIT, timeout_leg)
    for _, row in real.iterrows():
        notional = row["position_size"] * row["entry_price"]
        funding = funding_cost(
            notional=notional,
            holding_candles=row["exit_bar_offset"],
            direction=row["signal_direction"],
        )
        assert (row["cost"] - funding) / notional <= gate + 1e-12


def test_run_backtest_timeout_leg_default_reproduces_baseline() -> None:
    """
    BRAMA RUNDY: domyslny `timeout_leg` musi dac wynik BIT-IDENTYCZNY z baseline'em.

    Bez tego H3 nie jest analiza wrazliwosci, tylko cicha zmiana pipeline'u - a wszystkie
    wczesniejsze rundy przestalyby byc porownywalne.
    """
    raw = _make_pipeline_test_ohlcv(seed=7)
    base = run_backtest(raw, **_H3_KWARGS)
    explicit = run_backtest(raw, timeout_leg=TAKER, **_H3_KWARGS)
    assert base["final_equity"] == explicit["final_equity"]
    pd.testing.assert_frame_equal(base["trades"], explicit["trades"])
    assert base["folds_summary"] == explicit["folds_summary"]


def test_run_backtest_timeout_leg_does_not_change_signal_funnel() -> None:
    """
    UCZCIWOSC POROWNANIA, wymuszona konstrukcja: bramka bierze MAKSIMUM po powodach
    wyjscia, a maksimum realizuje `sl` niezaleznie od nogi timeout. Wiec oba warianty
    pasma ogladaja DOKLADNIE te same sygnaly, a roznica w wyniku nie moze pochodzic
    z innego lejka - tylko z kosztu.
    """
    raw = _make_pipeline_test_ohlcv(seed=7)
    taker = run_backtest(raw, timeout_leg=TAKER, **_H3_KWARGS)
    maker = run_backtest(raw, timeout_leg=MAKER, **_H3_KWARGS)
    for key in _FUNNEL_KEYS:
        assert sum(f[key] for f in taker["folds_summary"]) == sum(
            f[key] for f in maker["folds_summary"]
        ), f"lejek rozjechal sie na {key}"


def _merged_real_rows(raw):
    """
    Zlacza oba przebiegi pasma i zostawia wiersze REALNE W OBU.

    Kill-switch jest sciezkowo zalezny: tanszy koszt -> inna krzywa equity -> inny moment
    zadzialania (zmierzone na fiksturze: 152 vs 120 wierszy stlumionych, 32 rozjazdu).
    Wiersze stlumione maja exit_price=NaN i exit_reason=None, wiec porownywanie ich
    mierzyloby selekcje, nie koszt.
    """
    taker = run_backtest(raw, timeout_leg=TAKER, **_H3_KWARGS)["trades"]
    maker = run_backtest(raw, timeout_leg=MAKER, **_H3_KWARGS)["trades"]
    merged = taker.merge(maker, on=["timestamp", "regime", "fold_idx"], suffixes=("_t", "_m"))
    both_real = ~merged["kill_switch_active_t"].astype(bool) & ~merged[
        "kill_switch_active_m"
    ].astype(bool)
    return merged[both_real]


def test_run_backtest_timeout_maker_cheaper_only_on_timeout_rows() -> None:
    """
    Wariant maker obniza koszt WYLACZNIE wierszy `timeout`, i to o dokladna wartosc
    (taker - maker + slippage) = 0,0005 nominalu.

    Porownanie w UDZIALE NOMINALU, nie w kwocie: nominal zalezy od wielkosci pozycji,
    a ta od equity, ktora rozjezdza sie miedzy przebiegami. Koszt jako ulamek nominalu
    jest od tego wolny.
    """
    merged = _merged_real_rows(_make_pipeline_test_ohlcv(seed=7))
    assert len(merged) > 0
    assert (merged["exit_reason_t"] == "timeout").any(), "fikstura musi zawierac timeouty"

    for _, row in merged.iterrows():
        frac_t = row["cost_t"] / (row["position_size_t"] * row["entry_price_t"])
        frac_m = row["cost_m"] / (row["position_size_m"] * row["entry_price_m"])
        if row["exit_reason_t"] == "timeout":
            assert frac_t - frac_m == pytest.approx(0.0005)
        else:
            assert frac_t - frac_m == pytest.approx(0.0)


def test_run_backtest_gross_return_per_unit_identical_across_timeout_leg() -> None:
    """
    Dowod, ze runda rusza WYLACZNIE koszt.

    Niezmiennikiem jest ZWROT BRUTTO NA JEDNOSTKE, nie `gross_pnl` w kwocie: kwota skaluje
    sie z wielkoscia pozycji, ta z equity, a equity zalezy od kosztu. To wlasnie dlatego
    H3 nie raportuje trafnosci - trafnosc moze sie tu ruszyc wylacznie przez SELEKCJE
    (inny moment kill-switcha), czyli bylaby szumem selekcyjnym, nie sygnalem.

    Gdyby ktos kiedys dolozyl model CENY wyjscia dla zlecenia limit, ten test zapali sie
    pierwszy - i slusznie, bo to juz nie bylaby zmiana samego kosztu.
    """
    merged = _merged_real_rows(_make_pipeline_test_ohlcv(seed=7))
    assert len(merged) > 0
    for side in ("entry_price", "exit_price", "exit_reason", "exit_bar_offset"):
        assert (merged[f"{side}_t"] == merged[f"{side}_m"]).all(), f"{side} sie rozjechalo"

    ret_t = (
        merged["signal_direction_t"]
        * (merged["exit_price_t"] - merged["entry_price_t"])
        / merged["entry_price_t"]
    )
    ret_m = (
        merged["signal_direction_m"]
        * (merged["exit_price_m"] - merged["entry_price_m"])
        / merged["entry_price_m"]
    )
    assert (ret_t - ret_m).abs().max() < 1e-15


def test_run_backtest_timeout_leg_changes_trade_set_only_via_kill_switch() -> None:
    """
    Dokumentuje ZNANA sciezkowa zaleznosc: tanszy koszt zmienia krzywa equity, a przez nia
    momenty zadzialania kill-switcha - wiec ZBIOR wykonanych transakcji sie rozni, mimo
    identycznego lejka sygnalow. To jest jedyny kanal, ktorym pasmo moze ruszyc trafnosc,
    i powod, dla ktorego regula D5 rundy H3 zakazuje jej raportowania.
    """
    raw = _make_pipeline_test_ohlcv(seed=7)
    taker = run_backtest(raw, timeout_leg=TAKER, **_H3_KWARGS)["trades"]
    maker = run_backtest(raw, timeout_leg=MAKER, **_H3_KWARGS)["trades"]
    merged = taker.merge(maker, on=["timestamp", "regime", "fold_idx"], suffixes=("_t", "_m"))
    assert len(merged) == len(taker) == len(maker), "lejek sygnalow musi byc identyczny"
    n_killed_t = merged["kill_switch_active_t"].astype(bool).sum()
    n_killed_m = merged["kill_switch_active_m"].astype(bool).sum()
    assert n_killed_m <= n_killed_t, "tanszy koszt nie moze zwiekszac liczby stlumien"


def test_run_backtest_rejects_unknown_timeout_leg() -> None:
    """
    Walidacja musi padac PRZED treningiem pierwszego modelu (fail fast), a nie po
    dwudziestu minutach przebiegu.
    """
    with pytest.raises(ValueError):
        run_backtest(_make_pipeline_test_ohlcv(seed=7), timeout_leg="limit", **_H3_KWARGS)
