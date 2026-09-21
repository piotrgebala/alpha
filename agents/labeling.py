"""
labeling.py

Target (triple-barrier, ATR-scaled) i walk-forward split dla Fazy 0.
Uzasadnienie pełne: docs/rag/03_ryzyko_i_sizing.md.

KONTRAKT triple-barrier:
    upper barrier:    entry + atr_multiplier * atr_14[t]
    lower barrier:    entry - atr_multiplier * atr_14[t]
    vertical barrier: t + vertical_barrier_candles świec — timeout
    label: która bariera trafiona pierwsza w oknie [t+1, t+vertical_barrier_candles] -> +1 / -1 / 0

KRYTYCZNE (CLAUDE.md zasada 3): atr_multiplier MUSI być identyczny z mnożnikiem
stop-lossa w risk_controller.py (Commit 5.5). Jedyne źródło prawdy dla tej wartości:
config/settings.yaml, sekcja `labeling`. Nie zmieniaj jednej strony bez drugiej —
rozjazd oznacza trening na innym zdarzeniu niż faktyczny handel.

Uwaga o "leakage" dla labeli (inaczej niż dla cech w feature_miner.py): labelki z
DEFINICJI patrzą w przyszłość — to nie jest leakage, to jest cel triple-barrier.
Ryzyko leakage tutaj to bug zaglądający DALEJ w przyszłość niż zadeklarowane
`vertical_barrier_candles`, albo błąd offsetu/alignmentu. Formalny test tego:
agent_5_compliance/test_leakage.py::test_triple_barrier_no_leakage (Commit 4).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from agents.feature_miner import compute_atr_14

# Źródło prawdy: config/settings.yaml, sekcja `labeling`. MUSI być identyczne z
# risk_controller.py (Commit 5.5, CLAUDE.md zasada 3) — rozjazd = trening na
# innym zdarzeniu niż handel.
ATR_MULTIPLIER = 1.5
VERTICAL_BARRIER_CANDLES = 12  # 1h @ timeframe 5m (docs/rag/03)

# Walk-forward — wartości startowe, docs/rag/03 / config/settings.yaml sekcja
# `walk_forward`. "Miesiące"/"tygodnie" przybliżone stałą liczbą dni (kalendarzowe
# miesiące są nieregularne) — świadome uproszczenie.
TRAIN_WINDOW_DAYS = 60  # ~2 miesiące
TEST_WINDOW_DAYS = 14  # 2 tygodnie
STEP_DAYS = 14  # przesunięcie co 2 tygodnie


def compute_triple_barrier_labels(
    df: pd.DataFrame,
    atr_multiplier: float = ATR_MULTIPLIER,
    vertical_barrier_candles: int = VERTICAL_BARRIER_CANDLES,
) -> pd.DataFrame:
    """
    Triple-barrier ATR-scaled labeling (docs/rag/03_ryzyko_i_sizing.md).

    Dla każdej świecy t (entry = close[t]):
        upper = entry + atr_multiplier * atr_14[t]
        lower = entry - atr_multiplier * atr_14[t]

    Patrzy w przód maksymalnie `vertical_barrier_candles` świec i sprawdza, która
    bariera została trafiona pierwsza: high >= upper -> +1, low <= lower -> -1,
    żadna w oknie -> 0 (vertical barrier / timeout).

    Założenie metodologiczne (brak danych intrabar — mamy tylko OHLC 5m): jeśli
    POJEDYNCZA świeca trafia OBIE bariery naraz, przyjmujemy, że pierwsza trafiona
    została ta bliższa cenie `open` tej świecy (cena "startuje" z open i dociera
    najpierw do bliższej bariery). To uproszczenie, nie fakt — kandydat do rewizji
    w Fazie 1, jeśli okaże się to istotne dla wyniku (np. przez dane intrabar).

    Wiersze bez atr_14 (warmup TA-Lib, pierwsze ~14 świec) albo bez pełnego okna
    do sprawdzenia (koniec datasetu) dostają label=NaN — NIE oznaczaj ich jako
    "0", bo to nie jest prawdziwy wynik vertical barrier, tylko brak danych.

    Args:
        df: DataFrame z kolumnami [timestamp, open, high, low, close, volume],
            posortowany chronologicznie.
        atr_multiplier: mnożnik ATR dla obu barier poziomych.
        vertical_barrier_candles: liczba świec do timeoutu (bariera pionowa).

    Returns:
        DataFrame [label, exit_bar_offset] indeksowany jak df.
        `label` in {1.0, -1.0, 0.0, NaN}.
        `exit_bar_offset` = liczba świec do wyjścia (diagnostyka, np. do
        średniego czasu trzymania pozycji w Commicie 6), NaN gdy label NaN.
    """
    n = len(df)
    atr = compute_atr_14(df)

    close = df["close"].to_numpy()
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    open_ = df["open"].to_numpy()
    atr_values = atr.to_numpy()

    labels = np.full(n, np.nan)
    exit_bar_offset = np.full(n, np.nan)

    for t in range(n):
        if np.isnan(atr_values[t]):
            continue  # ATR warmup — brak danych do zdefiniowania barier
        if t + vertical_barrier_candles >= n:
            continue  # niepełne okno w przód — brak danych, nie "0"

        entry_price = close[t]
        upper = entry_price + atr_multiplier * atr_values[t]
        lower = entry_price - atr_multiplier * atr_values[t]

        label = 0.0
        offset = float(vertical_barrier_candles)
        for k in range(t + 1, t + vertical_barrier_candles + 1):
            hit_upper = high[k] >= upper
            hit_lower = low[k] <= lower
            if hit_upper and hit_lower:
                # Obie bariery trafione w tej samej świecy — brak danych intrabar,
                # zakładamy, że bliższa barierze wobec open[k] padła pierwsza.
                dist_upper = upper - open_[k]
                dist_lower = open_[k] - lower
                label = 1.0 if dist_upper <= dist_lower else -1.0
                offset = float(k - t)
                break
            if hit_upper:
                label = 1.0
                offset = float(k - t)
                break
            if hit_lower:
                label = -1.0
                offset = float(k - t)
                break

        labels[t] = label
        exit_bar_offset[t] = offset

    return pd.DataFrame(
        {"label": labels, "exit_bar_offset": exit_bar_offset}, index=df.index
    )


def generate_walk_forward_folds(
    df: pd.DataFrame,
    train_days: int = TRAIN_WINDOW_DAYS,
    test_days: int = TEST_WINDOW_DAYS,
    step_days: int = STEP_DAYS,
    start_offset_days: float = 0.0,
) -> list[dict]:
    """
    Generuje chronologiczne, przesuwane okna walk-forward (docs/rag/03).

    NIGDY random split — leakage czasowy. Każdy fold ma train ściśle przed test
    (half-open intervals [start, end) — train_end == test_start, brak nakładania
    WEWNĄTRZ jednego foldu). Kolejne foldy mogą dzielić dane historyczne w swoich
    train-oknach (to normalne dla walk-forward, nie leakage — w KAŻDYM foldzie
    z osobna test jest zawsze ściśle po jego własnym train).

    `start_offset_days` (Commit 2.9): przesuwa start PIERWSZEGO foldu o zadaną liczbę
    dni względem pierwszej świecy danych. Używane WYŁĄCZNIE przez sweep stabilności
    fold-jitter (`backtest/checkpoint_lib.py`) — perturbuje ARBITRALNY wybór
    wyrównania granic foldów (dotąd zawsze "od pierwszej świecy"), NIE jest
    parametrem hipotezy ani kandydatem do kalibracji. Domyślne 0.0 = zachowanie
    identyczne jak przed Commitem 2.9. Kontekst: sweep stabilności po seedach
    (C6.3) okazał się pusty poznawczo, bo XGBoost w obecnej konfiguracji (bez
    subsample/colsample) jest deterministyczny — patrz docs/rag/03, aktualizacja
    2026-09-21.

    Args:
        df: DataFrame z kolumną `timestamp` (tz-aware, posortowana chronologicznie).
        train_days: długość okna treningowego w dniach.
        test_days: długość okna testowego w dniach.
        step_days: przesunięcie startu kolejnego foldu w dniach.
        start_offset_days: przesunięcie startu pierwszego foldu w dniach (>= 0).

    Returns:
        Lista dictów: {train_start, train_end, test_start, test_end,
        train_mask (np.ndarray bool), test_mask (np.ndarray bool)}.
        Pusta lista, jeśli danych jest za mało na choćby jeden pełny fold.
    """
    timestamps = df["timestamp"]
    data_end = timestamps.iloc[-1]

    train_delta = pd.Timedelta(days=train_days)
    test_delta = pd.Timedelta(days=test_days)
    step_delta = pd.Timedelta(days=step_days)

    folds = []
    train_start = timestamps.iloc[0] + pd.Timedelta(days=start_offset_days)
    while True:
        train_end = train_start + train_delta
        test_start = train_end
        test_end = test_start + test_delta
        if test_end > data_end:
            break

        train_mask = ((timestamps >= train_start) & (timestamps < train_end)).to_numpy()
        test_mask = ((timestamps >= test_start) & (timestamps < test_end)).to_numpy()
        folds.append(
            {
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
                "train_mask": train_mask,
                "test_mask": test_mask,
            }
        )
        train_start = train_start + step_delta

    return folds


def effective_sample_size(returns: pd.Series, max_lag: int = 50) -> dict:
    """
    Diagnostyka efektywnej liczby niezależnych próbek (docs/rag/03), oparta o
    autokorelację zwrotów: N_eff = N / (1 + 2 * sum(rho_k dla k=1..max_lag)).

    Informacyjne, NIE blokuje pipeline'u — pomaga interpretować istotność
    wyników (np. Sharpe'a) w Commicie 6, gdy N_eff jest dużo mniejsze niż N.

    Args:
        returns: seria zwrotów (może zawierać NaN, np. pierwszy wiersz pct_change).
        max_lag: maksymalny lag do zsumowania autokorelacji.

    Returns:
        {"n": liczba obserwacji po dropna, "n_eff": efektywna liczba próbek,
        "max_lag": użyty max_lag}.
    """
    clean = returns.dropna()
    n = len(clean)
    autocorrs = [clean.autocorr(lag=k) for k in range(1, max_lag + 1)]
    autocorrs = [a for a in autocorrs if not np.isnan(a)]
    n_eff = n / (1 + 2 * sum(autocorrs))
    return {"n": n, "n_eff": n_eff, "max_lag": max_lag}
