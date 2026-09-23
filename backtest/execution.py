"""
execution.py

W1 (2026-09-23) — symulacja WYKONANIA na ścieżce cen: wypełnienie zlecenia wejścia oraz wyjście
TP / SL / timeout liczone z kolejnych świec, zamiast odczytu wyjścia z etykiety triple-barrier.
Reguły 1–6 są ZAPISANE w pre-rejestracji PRZED tym kodem i kod ma je odtwarzać co do litery:
`runs/2026-09-23_w1-wykonanie-po-cenie/README.md`. ADR: `docs/rag/04` (sekcja „symulacja
wypełnień”).

Czyste funkcje na tablicach numpy (open/high/low/close). Konwencje:
- `t` = indeks świecy SYGNAŁU (decyzyjnej, np. 4h); zlecenie składane na jej zamknięciu;
  wszystkie odczyty cen dotyczą świec `> t` — brak lookaheadu (test własnościowy);
- `direction` = +1 long / −1 short;
- „przebicie” poziomu jest ŚCISŁE (`low < P` dla zlecenia czekającego poniżej rynku,
  `high > P` dla czekającego powyżej) — dotknięcie nie wystarcza (konserwatywnie);
- bariery wyjścia liczone od CENY WYPEŁNIENIA (na żywo TP/SL stawia się od wejścia), dotknięcie
  bariery (`>=` / `<=`) tak jak w etykiecie (`agents/labeling.py`);
- timeout = zamknięcie świecy `t + V` (od SYGNAŁU — horyzont prognozy), po rynku.

Dwie rozdzielczości tej samej logiki:
- `RESOLUTION_BAR`     — tylko świece decyzyjne. W świecy wypełnienia, gdy wypełnienie nie nastąpiło
                         na otwarciu, liczy się WYŁĄCZNIE SL (mógł paść po wypełnieniu), TP nie
                         (mógł paść przed) — konserwatywnie. Obie bariery w jednej świecy → reguła
                         etykiety (bliższa otwarciu pierwsza).
- `RESOLUTION_INTRABAR` — ścieżka drobniejszych świec (5m) wewnątrz świec decyzyjnych. Te same
                         reguły na świecach 5m; obie bariery w jednej świecy 5m → SL pierwszy.

Poślizg NIE jest tu wliczany w cenę: model kosztów (`backtest/costs.py`) nalicza go jako koszt
nogi taker, tak samo jak dotąd — dzięki temu `gross_pnl` mierzy tylko geometrię cen.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backtest.costs import EXIT_REASON_SL, EXIT_REASON_TIMEOUT, EXIT_REASON_TP, MAKER, TAKER

ENTRY_LIMIT_CLOSE = "limit_close"
ENTRY_LIMIT_PULLBACK = "limit_pullback"
ENTRY_STOP_BREAKOUT = "stop_breakout"
VALID_ENTRY_RULES = (ENTRY_LIMIT_CLOSE, ENTRY_LIMIT_PULLBACK, ENTRY_STOP_BREAKOUT)

# Pre-rejestracja W1: JEDNA wartość cofnięcia (1/3 bariery), zero sweepu.
DEFAULT_PULLBACK_ATR = 0.5
# Pre-rejestracja W1: ważność = 1 świeca decyzyjna, z horyzontu modelu, nie z wyniku.
DEFAULT_ENTRY_VALIDITY_CANDLES = 1

RESOLUTION_BAR = "bar"
RESOLUTION_INTRABAR = "intrabar"

TIE_CLOSER_TO_OPEN = "closer_to_open"  # reguła etykiety (agents/labeling.py)
TIE_SL_FIRST = "sl_first"  # konserwatywnie, na świecach 5m


@dataclass(frozen=True)
class EntryRule:
    """Nazwany wariant wejścia (pre-rejestracja W1, tabela wariantów)."""

    kind: str
    pullback_atr: float = DEFAULT_PULLBACK_ATR

    def __post_init__(self) -> None:
        if self.kind not in VALID_ENTRY_RULES:
            raise ValueError(f"kind musi być jednym z {VALID_ENTRY_RULES}, dostałem: {self.kind!r}")
        if not np.isfinite(self.pullback_atr) or self.pullback_atr < 0:
            raise ValueError(f"pullback_atr musi być >= 0, dostałem: {self.pullback_atr!r}")

    @property
    def is_stop(self) -> bool:
        return self.kind == ENTRY_STOP_BREAKOUT

    @property
    def entry_leg(self) -> str:
        """Limit spoczywa w księdze (maker); stop po aktywacji krzyżuje księgę (taker)."""
        return TAKER if self.is_stop else MAKER

    def level(
        self, direction: float, close_t: float, high_t: float, low_t: float, atr_t: float
    ) -> float:
        if self.kind == ENTRY_LIMIT_CLOSE:
            return float(close_t)
        if self.kind == ENTRY_LIMIT_PULLBACK:
            return float(close_t - direction * self.pullback_atr * atr_t)
        return float(high_t if direction > 0 else low_t)


@dataclass(frozen=True)
class Fill:
    idx: int  # indeks świecy (w rozdzielczości ścieżki), w której nastąpiło wypełnienie
    price: float
    at_open: bool  # poziom był już spełniony na otwarciu świecy → cała jej ścieżka liczy się dalej


@dataclass(frozen=True)
class ExitEvent:
    idx: int  # indeks świecy (w rozdzielczości ścieżki)
    price: float
    reason: str


@dataclass(frozen=True)
class TradeOutcome:
    filled: bool
    entry_level: float
    resolution: str
    fill_idx: int | None = None  # indeks ŚWIECY DECYZYJNEJ wypełnienia
    fill_price: float = float("nan")
    fill_at_open: bool = False
    exit_idx: int | None = None  # indeks ŚWIECY DECYZYJNEJ wyjścia
    exit_price: float = float("nan")
    exit_reason: str | None = None
    tp_level: float = float("nan")
    sl_level: float = float("nan")


@dataclass(frozen=True)
class IntrabarPath:
    """Ścieżka drobniejszych świec przypięta do świec decyzyjnych.

    `start[j]` = indeks pierwszej świecy 5m świecy decyzyjnej `j` (−1 = brak danych),
    `count[j]` = liczba świec 5m w świecy `j`.
    """

    start: np.ndarray
    count: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray

    def covers(self, first_bar: int, last_bar: int) -> bool:
        return bool(np.all(self.start[first_bar : last_bar + 1] >= 0))

    def last_sub_idx(self, bar: int) -> int:
        return int(self.start[bar] + self.count[bar] - 1)

    def bar_of(self, sub_idx: int) -> int:
        """Świeca decyzyjna zawierająca świecę 5m o indeksie `sub_idx`."""
        starts = self.start
        covered = np.where(starts >= 0)[0]
        pos = np.searchsorted(starts[covered], sub_idx, side="right") - 1
        return int(covered[pos])


def build_intrabar_path(
    bar_timestamps: pd.Series, intrabar: pd.DataFrame, candle_minutes: int
) -> IntrabarPath:
    """
    Przypina świece drobne (np. 5m) do świec decyzyjnych (np. 4h) po znaczniku czasu.
    Wymaga posortowanych, pełnych bloków: każda świeca decyzyjna z danymi ma DOKŁADNIE
    `candle_minutes / interwał_drobny` świec — inaczej ValueError (fail loud, nie ciche luki).
    Świece decyzyjne bez danych drobnych dostają `start = -1`.
    """
    sub = intrabar.sort_values("timestamp").reset_index(drop=True)
    sub_ts = pd.to_datetime(sub["timestamp"], utc=True)
    bucket = sub_ts.dt.floor(f"{candle_minutes}min")
    grouped = bucket.groupby(bucket).agg(["size"])
    first_index = bucket.drop_duplicates(keep="first")
    start_by_bucket = pd.Series(first_index.index.to_numpy(), index=first_index.to_numpy())
    count_by_bucket = grouped["size"]

    sub_minutes = int(round((sub_ts.iloc[1] - sub_ts.iloc[0]).total_seconds() / 60))
    expected = candle_minutes // sub_minutes

    bars = pd.to_datetime(pd.Series(bar_timestamps).reset_index(drop=True), utc=True)
    start = np.full(len(bars), -1, dtype=np.int64)
    count = np.zeros(len(bars), dtype=np.int64)
    for j, ts in enumerate(bars):
        if ts in start_by_bucket.index:
            n_sub = int(count_by_bucket.loc[ts])
            if n_sub != expected:
                raise ValueError(
                    f"świeca decyzyjna {ts} ma {n_sub} świec drobnych, oczekiwano {expected}"
                )
            start[j] = int(start_by_bucket.loc[ts])
            count[j] = n_sub
    return IntrabarPath(
        start=start,
        count=count,
        open=sub["open"].to_numpy(dtype=float),
        high=sub["high"].to_numpy(dtype=float),
        low=sub["low"].to_numpy(dtype=float),
        close=sub["close"].to_numpy(dtype=float),
    )


# --- wypełnienie -----------------------------------------------------------------------------


def _waits_below(is_stop: bool, direction: float) -> bool:
    """Czy zlecenie czeka PONIŻEJ rynku (wypełnia je ruch w dół): long limit i short stop."""
    return (direction > 0) != is_stop


def crossed(is_stop: bool, direction: float, level: float, high_j: float, low_j: float) -> bool:
    """Ścisłe przebicie poziomu zlecenia w świecy."""
    return low_j < level if _waits_below(is_stop, direction) else high_j > level


def fill_price_at(
    is_stop: bool, direction: float, level: float, open_j: float
) -> tuple[float, bool]:
    """(cena wypełnienia, czy poziom był spełniony już na otwarciu) — regułą 1 pre-rejestracji."""
    if _waits_below(is_stop, direction):
        return (min(open_j, level), open_j <= level)
    return (max(open_j, level), open_j >= level)


def simulate_fill(
    rule: EntryRule,
    direction: float,
    level: float,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    first_idx: int,
    last_idx: int,
) -> Fill | None:
    """Pierwsza świeca w `[first_idx, last_idx]`, w której zlecenie zostaje wypełnione."""
    for j in range(first_idx, last_idx + 1):
        if crossed(rule.is_stop, direction, level, high[j], low[j]):
            price, at_open = fill_price_at(rule.is_stop, direction, level, open_[j])
            return Fill(idx=j, price=float(price), at_open=bool(at_open))
    return None


# --- wyjście ---------------------------------------------------------------------------------


def barrier_levels(
    direction: float, fill_price: float, atr_t: float, atr_multiplier: float
) -> tuple[float, float]:
    """(TP, SL) od ceny wypełnienia, tym samym mnożnikiem co etykieta (CLAUDE.md zasada 3)."""
    return (
        float(fill_price + direction * atr_multiplier * atr_t),
        float(fill_price - direction * atr_multiplier * atr_t),
    )


def _first_barrier(
    direction: float,
    tp: float,
    sl: float,
    open_j: float,
    high_j: float,
    low_j: float,
    tie_rule: str,
    allow_tp: bool = True,
) -> str | None:
    upper, lower = max(tp, sl), min(tp, sl)
    hit_upper = high_j >= upper
    hit_lower = low_j <= lower
    upper_is_tp = direction > 0
    if not allow_tp:
        # świeca wypełnienia bez wypełnienia na otwarciu: liczy się tylko SL
        return EXIT_REASON_SL if (hit_lower if upper_is_tp else hit_upper) else None
    if hit_upper and hit_lower:
        if tie_rule == TIE_SL_FIRST:
            return EXIT_REASON_SL
        upper_first = (upper - open_j) <= (open_j - lower)  # dokładnie jak w labeling.py
        return EXIT_REASON_TP if upper_first == upper_is_tp else EXIT_REASON_SL
    if hit_upper:
        return EXIT_REASON_TP if upper_is_tp else EXIT_REASON_SL
    if hit_lower:
        return EXIT_REASON_SL if upper_is_tp else EXIT_REASON_TP
    return None


def simulate_exit(
    direction: float,
    fill: Fill,
    tp: float,
    sl: float,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    last_idx: int,
    tie_rule: str,
) -> ExitEvent:
    """Pierwsze wyjście od świecy wypełnienia do `last_idx` włącznie; brak bariery → timeout."""
    for j in range(fill.idx, last_idx + 1):
        allow_tp = j > fill.idx or fill.at_open
        reason = _first_barrier(direction, tp, sl, open_[j], high[j], low[j], tie_rule, allow_tp)
        if reason == EXIT_REASON_TP:
            return ExitEvent(idx=j, price=tp, reason=EXIT_REASON_TP)
        if reason == EXIT_REASON_SL:
            return ExitEvent(idx=j, price=sl, reason=EXIT_REASON_SL)
    return ExitEvent(idx=last_idx, price=float(close[last_idx]), reason=EXIT_REASON_TIMEOUT)


# --- cała transakcja -------------------------------------------------------------------------


def simulate_trade(
    rule: EntryRule,
    direction: float,
    t: int,
    validity: int,
    timeout_idx: int,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr_t: float,
    atr_multiplier: float,
    intrabar: IntrabarPath | None = None,
) -> TradeOutcome:
    """
    Jedna transakcja od sygnału `t`: zlecenie ważne `validity` świec decyzyjnych (nie dłużej niż
    do `timeout_idx`), wyjście najpóźniej na zamknięciu świecy `timeout_idx`.

    `intrabar` = None → RESOLUTION_BAR; inaczej ścieżka drobna musi pokrywać świece
    `t+1..timeout_idx` w całości (ValueError, gdy nie — fail loud).
    """
    if validity < 1:
        raise ValueError(f"validity musi być >= 1, dostałem: {validity}")
    if timeout_idx <= t:
        raise ValueError(f"timeout_idx ({timeout_idx}) musi być > t ({t})")
    level = rule.level(direction, close[t], high[t], low[t], atr_t)
    last_fill_bar = min(t + validity, timeout_idx)

    if intrabar is None:
        fill = simulate_fill(rule, direction, level, open_, high, low, t + 1, last_fill_bar)
        if fill is None:
            return TradeOutcome(filled=False, entry_level=level, resolution=RESOLUTION_BAR)
        tp, sl = barrier_levels(direction, fill.price, atr_t, atr_multiplier)
        exit_ = simulate_exit(
            direction, fill, tp, sl, open_, high, low, close, timeout_idx, TIE_CLOSER_TO_OPEN
        )
        return TradeOutcome(
            filled=True,
            entry_level=level,
            resolution=RESOLUTION_BAR,
            fill_idx=fill.idx,
            fill_price=fill.price,
            fill_at_open=fill.at_open,
            exit_idx=exit_.idx,
            exit_price=exit_.price,
            exit_reason=exit_.reason,
            tp_level=tp,
            sl_level=sl,
        )

    if not intrabar.covers(t + 1, timeout_idx):
        raise ValueError(f"ścieżka drobna nie pokrywa świec {t + 1}..{timeout_idx}")
    fill = simulate_fill(
        rule,
        direction,
        level,
        intrabar.open,
        intrabar.high,
        intrabar.low,
        int(intrabar.start[t + 1]),
        intrabar.last_sub_idx(last_fill_bar),
    )
    if fill is None:
        return TradeOutcome(filled=False, entry_level=level, resolution=RESOLUTION_INTRABAR)
    tp, sl = barrier_levels(direction, fill.price, atr_t, atr_multiplier)
    exit_ = simulate_exit(
        direction,
        fill,
        tp,
        sl,
        intrabar.open,
        intrabar.high,
        intrabar.low,
        intrabar.close,
        intrabar.last_sub_idx(timeout_idx),
        TIE_SL_FIRST,
    )
    return TradeOutcome(
        filled=True,
        entry_level=level,
        resolution=RESOLUTION_INTRABAR,
        fill_idx=intrabar.bar_of(fill.idx),
        fill_price=fill.price,
        fill_at_open=fill.at_open,
        exit_idx=intrabar.bar_of(exit_.idx),
        exit_price=exit_.price,
        exit_reason=exit_.reason,
        tp_level=tp,
        sl_level=sl,
    )
