"""
regime_coherence.py

Zadanie Z16 (Backlog II) — pomiar SPÓJNOŚCI bramki reżimu z horyzontem etykiety.

Dlaczego ten moduł istnieje: bramka reżimu (`agents.feature_miner.classify_regime`)
kwalifikuje POJEDYNCZĄ świecę, a target (`agents.labeling.compute_triple_barrier_labels`)
ocenia, co stanie się przez następne `VERTICAL_BARRIER_CANDLES` świec. Jeśli nieprzerwany
epizod reżimu jest KRÓTSZY niż to okno, etykieta opisuje w większości ruch ceny spoza
reżimu, który uzasadnił wejście — czyli bramka i target mierzą różne rzeczy. Taka
niespójność czyni pomiar trafności kierunku (`p`) nieinterpretowalnym, niezależnie od
jakości modelu.

To NIE jest miara wyniku (Sharpe, PnL) ani kryterium GO/NO-GO — to test POPRAWNOŚCI
SPECYFIKACJI sygnału, wykonalny bez uruchamiania modelu i bez wydawania budżetu
multiple-testing (docs/rag/02). Funkcje są czyste i przetestowane, żeby ten sam kryterium
dało się użyć do przesiewania KANDYDATÓW na regułę reżimu (Backlog Z7) bez dotykania modelu.

UWAGA KRYTYCZNA: `regime_episodes` liczy epizody po POZYCJACH w serii, nie po czasie.
Wywołujący MUSI podać serię ciągłą w czasie (bez dziur w środku). Odfiltrowanie wiersza
ze środka zlepiłoby dwa rozdzielone epizody w jeden i zawyżyło ich długość — dlatego
`assert_contiguous_timestamps` istnieje i jest używane przez skrypt diagnostyczny.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Horyzonty do tabeli spójności, w świecach 5m. 12 = obecny VERTICAL_BARRIER_CANDLES (1h);
# pozostałe to horyzonty, które byłyby potrzebne, gdyby szerokość bariery miała pokryć
# koszt przy realistycznej trafności (patrz runs/ C2.11-C2.13: wymagane B ~ 3% ceny).
DEFAULT_HORIZONS_CANDLES = (12, 48, 144, 576)

# Kryterium dopuszczalności reguły reżimu: mediana długości epizodu musi pokryć CAŁE okno
# etykiety. Wartość progu nie jest strojona — to warunek definicyjny ("sygnał ma opisywać
# ruch wewnątrz reżimu, który go uzasadnił"), nie parametr dobrany pod wynik.
COHERENCE_CRITERION = "median_length >= horizon"


def assert_contiguous_timestamps(timestamps: pd.Series, candle_minutes: int = 5) -> None:
    """
    Podnosi ValueError, jeśli `timestamps` ma dziurę w środku (różnica > jedna świeca).

    Bez tego `regime_episodes` cicho zlepiłoby epizody rozdzielone luką — błąd, który
    zawyżałby długości epizodów, czyli dokładnie wielkość, którą ten moduł mierzy.
    """
    if len(timestamps) < 2:
        return
    deltas = timestamps.diff().dropna().dt.total_seconds() / 60.0
    bad = deltas[deltas > candle_minutes]
    if len(bad) > 0:
        raise ValueError(
            f"Seria nie jest ciągła: {len(bad)} dziur (maks {bad.max():.0f} min). "
            "regime_episodes liczy epizody po pozycjach, więc dziura zlepiłaby dwa epizody."
        )


def regime_episodes(regime: pd.Series) -> pd.DataFrame:
    """
    Dzieli serię reżimów na NIEPRZERWANE epizody.

    Args:
        regime: seria etykiet reżimu ("trend"/"range"/"ambiguous"), ciągła w czasie.

    Returns:
        DataFrame: regime, start_pos (pozycja startu, 0-based), length (w świecach).
        Pusty DataFrame o tych kolumnach dla pustego wejścia.
    """
    if len(regime) == 0:
        return pd.DataFrame({"regime": [], "start_pos": [], "length": []}).astype(
            {"start_pos": int, "length": int}
        )

    values = regime.to_numpy()
    is_start = np.concatenate(([True], values[1:] != values[:-1]))
    starts = np.flatnonzero(is_start)
    lengths = np.diff(np.concatenate((starts, [len(values)])))
    return pd.DataFrame(
        {"regime": values[starts], "start_pos": starts, "length": lengths}
    )


def windows_fully_inside(lengths: np.ndarray | pd.Series, horizon: int) -> int:
    """
    Liczba pozycji startowych, dla których CAŁE okno `horizon` świec mieści się wewnątrz
    jednego epizodu: sum(max(0, L - horizon + 1)).

    To jest liczba świec, dla których etykieta triple-barrier opisuje ruch wyłącznie
    wewnątrz reżimu, który zakwalifikował wejście.
    """
    if horizon < 1:
        raise ValueError(f"horizon musi być >= 1, dostałem {horizon}")
    arr = np.asarray(lengths, dtype=float)
    if arr.size == 0:
        return 0
    return int(np.clip(arr - horizon + 1, 0, None).sum())


def coherence_table(
    regime: pd.Series,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS_CANDLES,
    regimes_of_interest: tuple[str, ...] = ("trend", "range"),
) -> pd.DataFrame:
    """
    Tabela spójności: dla każdego reżimu i każdego horyzontu — czy epizody są dość długie.

    Kolumny:
        regime, horizon_candles, horizon_minutes
        n_episodes            - liczba nieprzerwanych epizodów tego reżimu
        median_length, p90_length, max_length  - w świecach
        regime_candles        - łączna liczba świec w tym reżimie
        n_episodes_ge_horizon - ile epizodów pomieści pełne okno etykiety
        share_episodes_ge_horizon
        n_windows_inside      - liczba świec z CAŁYM oknem etykiety wewnątrz epizodu
        share_windows_inside  - jako ułamek świec reżimu
        coherent              - czy median_length >= horizon (COHERENCE_CRITERION)

    NaN w statystykach długości, gdy reżim nie wystąpił ani raz (zamiast 0, które
    udawałoby pomiar).
    """
    episodes = regime_episodes(regime)
    rows: list[dict] = []
    for name in regimes_of_interest:
        lengths = episodes.loc[episodes["regime"] == name, "length"]
        n_episodes = int(len(lengths))
        regime_candles = int(lengths.sum()) if n_episodes else 0
        median_length = float(lengths.median()) if n_episodes else float("nan")
        p90_length = float(lengths.quantile(0.9)) if n_episodes else float("nan")
        max_length = int(lengths.max()) if n_episodes else 0

        for horizon in horizons:
            n_ge = int((lengths >= horizon).sum()) if n_episodes else 0
            n_inside = windows_fully_inside(lengths, horizon)
            rows.append(
                {
                    "regime": name,
                    "horizon_candles": horizon,
                    "horizon_minutes": horizon * 5,
                    "n_episodes": n_episodes,
                    "median_length": median_length,
                    "p90_length": p90_length,
                    "max_length": max_length,
                    "regime_candles": regime_candles,
                    "n_episodes_ge_horizon": n_ge,
                    "share_episodes_ge_horizon": (n_ge / n_episodes) if n_episodes else float("nan"),
                    "n_windows_inside": n_inside,
                    "share_windows_inside": (
                        n_inside / regime_candles if regime_candles else float("nan")
                    ),
                    "coherent": bool(median_length >= horizon) if n_episodes else False,
                }
            )
    return pd.DataFrame(rows)


def is_rule_admissible(
    regime: pd.Series,
    horizon: int,
    min_regime_share: float = 0.05,
    regimes_of_interest: tuple[str, ...] = ("trend", "range"),
) -> dict:
    """
    Kryterium dopuszczalności reguły reżimu — przesiew KANDYDATÓW bez dotykania modelu
    (Backlog Z7). Reguła jest dopuszczalna dla danego horyzontu, gdy KAŻDY reżim
    jednocześnie:
        (a) ma medianę długości epizodu >= horizon  (spójność bramka<->target), oraz
        (b) obejmuje >= min_regime_share świec      (dość próbek, by cokolwiek zmierzyć).

    Oba warunki są definicyjne, nie strojone pod wynik: (a) to wymóg, żeby etykieta
    opisywała ruch wewnątrz reżimu; (b) to wymóg, żeby fold miał w ogóle obserwacje
    (por. MIN_TRAIN_ROWS=30 w backtest/engine.py).

    Returns:
        dict: admissible (bool), per_regime (dict nazwa -> dict z median_length, share,
        coherent, enough_share), horizon.
    """
    table = coherence_table(regime, horizons=(horizon,), regimes_of_interest=regimes_of_interest)
    total = len(regime)
    per_regime: dict[str, dict] = {}
    for _, row in table.iterrows():
        share = row["regime_candles"] / total if total else float("nan")
        per_regime[row["regime"]] = {
            "median_length": row["median_length"],
            "share": share,
            "coherent": bool(row["coherent"]),
            "enough_share": bool(share >= min_regime_share),
        }
    admissible = bool(
        per_regime and all(v["coherent"] and v["enough_share"] for v in per_regime.values())
    )
    return {"admissible": admissible, "horizon": horizon, "per_regime": per_regime}
