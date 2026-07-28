"""
costs.py

Modelowanie kosztów transakcyjnych Binance USDS-M Futures (perpetuals) — docs/rag/04
_narzedzia_zewnetrzne.md i IMPLEMENTATION_PLAN.md §5 Commit 5. Wartości startowe, do
kalibracji, gdy dostępne będą realne dane funding rate (Faza 1, LEAN
`Lean.DataSource.BinanceFundingRate`) — źródło prawdy: config/settings.yaml sekcja
`costs`.

Trzy składniki pełnego obrotu (round-trip):
    fee       - taker fee, wejście I wyjście (zakładamy market order w obie strony)
    funding   - funding rate za czas trzymania pozycji (long płaci dodatni funding,
                short otrzymuje, i odwrotnie przy funding ujemnym)
    slippage  - stały bps, wejście I wyjście

Uproszczenie Fazy 0 (jawne): funding_rate_8h to JEDNA stała średnia historyczna, nie
modelowanie zmienności funding w czasie — Faza 1 podłączy realne dane.
"""

from __future__ import annotations

# Źródło prawdy: config/settings.yaml, sekcja `costs`. Wartości startowe.
TAKER_FEE_RATE = 0.0005  # 0.05% za stronę (Binance USDS-M Futures, VIP0 taker)
FUNDING_RATE_8H = 0.0001  # 0.01% / 8h — przybliżenie, brak jeszcze realnych danych funding
SLIPPAGE_BPS = 2.0  # 2 bps = 0.02%, stała wartość startowa

CANDLE_MINUTES = 5  # timeframe — config/settings.yaml data.timeframe="5m"
FUNDING_PERIOD_HOURS = 8  # Binance USDS-M Futures rozlicza funding 3x/dzień


def round_trip_fee_cost(notional: float, taker_fee_rate: float = TAKER_FEE_RATE) -> float:
    """Koszt fee za pełny obrót (wejście + wyjście), 2x taker fee — zakładamy market orders."""
    return 2.0 * notional * taker_fee_rate


def funding_cost(
    notional: float,
    holding_candles: float,
    direction: int,
    funding_rate_8h: float = FUNDING_RATE_8H,
    candle_minutes: int = CANDLE_MINUTES,
) -> float:
    """
    Koszt (albo przychód, jeśli ujemny) funding rate za czas trzymania pozycji.

    direction: +1 long (płaci dodatni funding), -1 short (otrzymuje dodatni funding
    — stąd znak `direction` bezpośrednio we wzorze, nie wartość absolutna).

    Args:
        notional: wartość nominalna pozycji (position_size * entry_price).
        holding_candles: liczba świec trzymania pozycji (np. exit_bar_offset).
        direction: +1 (long) albo -1 (short).
        funding_rate_8h: stopa funding za jeden okres rozliczeniowy (8h).
        candle_minutes: długość świecy w minutach (timeframe).
    """
    holding_hours = holding_candles * candle_minutes / 60.0
    periods = holding_hours / FUNDING_PERIOD_HOURS
    return direction * notional * funding_rate_8h * periods


def slippage_cost(notional: float, slippage_bps: float = SLIPPAGE_BPS) -> float:
    """Koszt poślizgu dla JEDNEGO wykonania (nie round-trip) — stała liczba bps."""
    return notional * (slippage_bps / 10_000.0)


def total_round_trip_cost(
    notional: float,
    holding_candles: float,
    direction: int,
    taker_fee_rate: float = TAKER_FEE_RATE,
    funding_rate_8h: float = FUNDING_RATE_8H,
    slippage_bps: float = SLIPPAGE_BPS,
    candle_minutes: int = CANDLE_MINUTES,
) -> float:
    """
    Suma wszystkich kosztów pełnego obrotu: fee (wejście+wyjście) + funding (czas
    trzymania) + slippage (wejście+wyjście, stąd `2 *`).
    """
    fee = round_trip_fee_cost(notional, taker_fee_rate)
    funding = funding_cost(notional, holding_candles, direction, funding_rate_8h, candle_minutes)
    slip = 2.0 * slippage_cost(notional, slippage_bps)
    return fee + funding + slip
