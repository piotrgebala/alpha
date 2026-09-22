"""
funding_features.py

Doczepianie funding rate do świec jako CECHY MODELU — pierwsze w projekcie źródło informacji
spoza OHLCV (runda H2.1; diagnoza, która to uzasadnia: `runs/2026-09-22_z10-zamkniecie-fazy-0/`).

Dlaczego osobny moduł, a nie funkcja w `agents/feature_miner.py`: wszystkie funkcje
w `FEATURE_FUNCTIONS` mają kontrakt `compute_*(df: OHLCV) -> Series` — liczą cechę
WYŁĄCZNIE z ceny i wolumenu. Funding przychodzi z zewnątrz i ma własną siatkę czasową
(co 8h: 00:00 / 08:00 / 16:00 UTC), więc nie mieści się w tym kontrakcie. Wciskanie go tam
zmusiłoby `compute_all_features` do przyjmowania drugiego źródła danych i zatarłoby granicę,
która w tym projekcie ma znaczenie: `feature_miner` liczy z OHLCV, ten moduł ZŁĄCZA dwa źródła.

CAUSALITY — jedyna rzecz, która tu może pójść źle:
    Funding rozlicza się w momencie `t_f`. Na świecy o znaczniku `t_c` model zna wyłącznie
    rozliczenia z `t_f <= t_c`. Realizuje to `merge_asof(direction="backward")` — z definicji
    patrzy wstecz. Formalny dowód: `agent_5_compliance/test_leakage.py` (zasada 2 — test PRZED
    wejściem cechy do modelu, nie po).

DLACZEGO SUROWA STAWKA, A NIE Z-SCORE (poprawka do pre-rejestracji z H2.0):
    H2.0 zapisało „funding rate + `funding_zscore` w oknie rozszerzającym się wstecz" — czyli
    DWIE cechy naraz, co łamie zasadę 4. Zawężone do JEDNEJ, i to surowej, z trzech powodów:
      1. XGBoost jest modelem drzewiastym, więc **niewrażliwym na monotoniczne przeskalowanie**
         pojedynczej cechy — normalizacja nic nie wnosi do zdolności modelu do znalezienia
         progu. Sam znajduje swoje podziały.
      2. Każdy wybór okna (rozszerzające vs kroczące, jaka długość) to **wolny parametr,
         którego nie ma czym skalibrować** — dokładnie ta pułapka, której uniknęliśmy w H3.
      3. Problem progu percentylowego (masa punktowa 35,85% obserwacji na stawce bazowej,
         H2.0) **znika sam**: drzewo dzieli po wartości, nie po percentylu.
    Walk-forward domyka kwestię dryfu poziomu funding w czasie: model trenuje na 60 dniach
    i stosuje do kolejnych 28, więc widzi rozkład LOKALNY, nie sześcioletni.
"""

from __future__ import annotations

import pandas as pd

FUNDING_COLUMN = "funding_rate"


def attach_funding_rate(
    candles: pd.DataFrame,
    funding: pd.DataFrame,
    column: str = FUNDING_COLUMN,
) -> pd.DataFrame:
    """
    Dokleja do świec ostatnią stawkę funding rozliczoną W MOMENCIE ŚWIECY LUB WCZEŚNIEJ.

    Args:
        candles: OHLCV z kolumną `timestamp` (UTC, tz-aware), chronologicznie.
        funding: wynik `data.fetch_funding.get_funding_rate_history_cached`
            (kolumny `timestamp`, `funding_rate`).
        column: nazwa kolumny wynikowej.

    Returns:
        Kopia `candles` z dodatkową kolumną. Świece PRZED pierwszym rozliczeniem funding
        dostają `NaN` — świadomie, bo w tamtym momencie ta informacja jeszcze nie istniała.
        Silnik i tak odsiewa wiersze z NaN w cechach (`dropna(subset=[*feature_columns])`),
        więc wypadną tak samo jak rozbieg każdego innego wskaźnika.

    Raises:
        ValueError: gdy któraś ramka jest nieposortowana albo brakuje kolumn — `merge_asof`
            po cichu daje błędne wyniki na nieposortowanym wejściu, a to jest dokładnie ten
            rodzaj usterki, który w tym projekcie produkował fałszywe wyniki.
    """
    if "timestamp" not in candles.columns:
        raise ValueError("candles musi mieć kolumnę 'timestamp'")
    if not {"timestamp", FUNDING_COLUMN} <= set(funding.columns):
        raise ValueError(f"funding musi mieć kolumny 'timestamp' i '{FUNDING_COLUMN}'")
    if not candles["timestamp"].is_monotonic_increasing:
        raise ValueError("candles musi być posortowane chronologicznie")
    if not funding["timestamp"].is_monotonic_increasing:
        raise ValueError("funding musi być posortowane chronologicznie")

    merged = pd.merge_asof(
        candles,
        funding[["timestamp", FUNDING_COLUMN]].rename(columns={FUNDING_COLUMN: column}),
        on="timestamp",
        direction="backward",  # wyłącznie wstecz — TU mieszka poprawność przyczynowa
    )
    merged.index = candles.index
    return merged
