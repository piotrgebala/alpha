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

from backtest.costs import (
    EXIT_REASON_BE_STOP,
    EXIT_REASON_SL,
    EXIT_REASON_TIMEOUT,
    EXIT_REASON_TP,
    EXIT_REASON_TP_PARTIAL,
    MAKER,
    TAKER,
)

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
class ExitLeg:
    """Jedna noga wyjścia: ułamek pozycji, świeca DECYZYJNA wyjścia, cena, powód."""

    fraction: float
    idx: int
    price: float
    reason: str


@dataclass(frozen=True)
class ManagedExitRule:
    """
    N1: prowadzenie pozycji dwoma celami. Bliższy z (`E·(1 ± near_pct)`, `E ± M·ATR`) zamyka
    `partial_fraction` pozycji i przesuwa stop na cenę wejścia; dalszy zamyka resztę. `M` to
    ten sam `atr_multiplier`, który dostaje `simulate_trade` (zasada 3 — jedno źródło mnożnika).
    Reguły 1–7 zapisane PRZED kodem: runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md.
    """

    partial_fraction: float = 0.5
    near_pct: float = 0.0167  # +5 % depozytu przy dźwigni 3× → 1,67 % ceny

    def __post_init__(self) -> None:
        if not 0.0 < self.partial_fraction < 1.0:
            raise ValueError(
                f"partial_fraction musi być w (0, 1), dostałem: {self.partial_fraction!r}"
            )
        if not np.isfinite(self.near_pct) or self.near_pct <= 0:
            raise ValueError(f"near_pct musi być > 0, dostałem: {self.near_pct!r}")


@dataclass(frozen=True)
class TradeOutcome:
    filled: bool
    entry_level: float
    resolution: str
    fill_idx: int | None = None  # indeks ŚWIECY DECYZYJNEJ wypełnienia
    fill_price: float = float("nan")
    fill_at_open: bool = False
    exit_idx: int | None = None  # indeks ŚWIECY DECYZYJNEJ wyjścia (ostatniej nogi)
    exit_price: float = float("nan")
    exit_reason: str | None = None
    tp_level: float = float("nan")
    sl_level: float = float("nan")
    # N1: wszystkie nogi wyjścia w porządku czasowym (indeksy świec DECYZYJNYCH); pojedyncze
    # wyjście = jedna noga o ułamku 1,0. Ułamki sumują się do 1 (test własnościowy).
    legs: tuple[ExitLeg, ...] = ()


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


# --- wyjście wielonogowe (N1) ----------------------------------------------------------------


def managed_targets(
    direction: float, entry: float, atr_t: float, atr_multiplier: float, rule: ManagedExitRule
) -> tuple[float, float]:
    """(bliższy, dalszy) cel — reguła 1 pre-rejestracji N1: dwa zlecenia limit w księdze,
    bliższe wypełnia się pierwsze (także gdy `M·ATR < near_pct·E`, czyli cele „odwrócone")."""
    target_pct = float(entry * (1.0 + direction * rule.near_pct))
    target_atr = float(entry + direction * atr_multiplier * atr_t)
    if abs(target_pct - entry) <= abs(target_atr - entry):
        return target_pct, target_atr
    return target_atr, target_pct


def simulate_managed_exit(
    direction: float,
    fill: Fill,
    atr_t: float,
    atr_multiplier: float,
    rule: ManagedExitRule,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    last_idx: int,
    tie_rule: str,
) -> tuple[ExitLeg, ...]:
    """
    Reguły 2–6 pre-rejestracji N1 na ścieżce od świecy wypełnienia do `last_idx`:
      faza 1 — stop `E ∓ M·ATR` (cała pozycja) vs bliższy cel; w świecy wypełnienia liczy się
               tylko stop, chyba że wypełnienie na otwarciu (jak `simulate_exit`);
      faza 2 — po bliższym celu: `partial_fraction` wychodzi po cenie celu (maker), stop = `E`
               (break-even, taker) dla reszty, dalszy cel dla reszty; w świecy bliższego celu
               (gdy nie na otwarciu) zdarzenie po celu liczy się TYLKO, gdy dowodzi go zamknięcie
               świecy (Poprawka 1 pre-rejestracji: close za dalszym celem → dalszy cel, close za
               wejściem → stop na wejściu; inaczej nic), od następnej świecy normalnie;
      timeout — zamknięcie `last_idx` po rynku dla tego, co zostało.
    Zwraca nogi w porządku czasowym; ułamki sumują się do 1.
    """
    entry = fill.price
    stop = float(entry - direction * atr_multiplier * atr_t)
    near, far = managed_targets(direction, entry, atr_t, atr_multiplier, rule)

    near_idx: int | None = None
    for j in range(fill.idx, last_idx + 1):
        allow_target = j > fill.idx or fill.at_open
        hit = _first_barrier(
            direction, near, stop, open_[j], high[j], low[j], tie_rule, allow_target
        )
        if hit == EXIT_REASON_SL:
            return (ExitLeg(1.0, j, stop, EXIT_REASON_SL),)
        if hit == EXIT_REASON_TP:
            near_idx = j
            break
    if near_idx is None:
        return (ExitLeg(1.0, last_idx, float(close[last_idx]), EXIT_REASON_TIMEOUT),)

    first = ExitLeg(rule.partial_fraction, near_idx, near, EXIT_REASON_TP_PARTIAL)
    rest = 1.0 - rule.partial_fraction
    near_at_open = bool(open_[near_idx] >= near) if direction > 0 else bool(open_[near_idx] <= near)
    if not near_at_open:
        # Poprawka 1 pre-rejestracji N1 (PRZED uruchomieniem): bliższy cel padł w ŚRODKU świecy,
        # w nieznanej chwili τ. Zdarzenie po τ jest dowiedzione tylko przez ZAMKNIĘCIE świecy:
        # close za dalszym celem ⇒ ścieżka od celu bliższego (< far) do close (>= far) przecięła
        # far po τ; close za wejściem ⇒ ścieżka od celu (> E) do close (<= E) przecięła E po τ.
        # Ekstremum świecy NIE jest dowodem — minimum świecy wypełnienia leży poniżej wejścia
        # z samej konstrukcji wypełnienia limitem, więc reguła „liczy się stop" zamykałaby
        # drugą połowę mechanicznie. Nic niedowiedzionego = nic się nie stało (neutralnie).
        c_near = close[near_idx]
        if (direction > 0 and c_near >= far) or (direction < 0 and c_near <= far):
            return (first, ExitLeg(rest, near_idx, far, EXIT_REASON_TP))
        if (direction > 0 and c_near <= entry) or (direction < 0 and c_near >= entry):
            return (first, ExitLeg(rest, near_idx, float(entry), EXIT_REASON_BE_STOP))
    for j in range(near_idx, last_idx + 1):
        if j == near_idx and not near_at_open:
            continue  # rozstrzygnięte wyżej przez zamknięcie świecy
        hit = _first_barrier(direction, far, entry, open_[j], high[j], low[j], tie_rule, True)
        if hit == EXIT_REASON_SL:
            return (first, ExitLeg(rest, j, float(entry), EXIT_REASON_BE_STOP))
        if hit == EXIT_REASON_TP:
            return (first, ExitLeg(rest, j, far, EXIT_REASON_TP))
    return (first, ExitLeg(rest, last_idx, float(close[last_idx]), EXIT_REASON_TIMEOUT))


# --- cała transakcja -------------------------------------------------------------------------


def _exit_legs(
    direction: float,
    fill: Fill,
    atr_t: float,
    atr_multiplier: float,
    exit_rule: ManagedExitRule | None,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    last_idx: int,
    tie_rule: str,
) -> tuple[ExitLeg, ...]:
    if exit_rule is None:
        tp, sl = barrier_levels(direction, fill.price, atr_t, atr_multiplier)
        exit_ = simulate_exit(direction, fill, tp, sl, open_, high, low, close, last_idx, tie_rule)
        return (ExitLeg(1.0, exit_.idx, exit_.price, exit_.reason),)
    return simulate_managed_exit(
        direction,
        fill,
        atr_t,
        atr_multiplier,
        exit_rule,
        open_,
        high,
        low,
        close,
        last_idx,
        tie_rule,
    )


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
    exit_rule: ManagedExitRule | None = None,
) -> TradeOutcome:
    """
    Jedna transakcja od sygnału `t`: zlecenie ważne `validity` świec decyzyjnych (nie dłużej niż
    do `timeout_idx`), wyjście najpóźniej na zamknięciu świecy `timeout_idx`.

    `intrabar` = None → RESOLUTION_BAR; inaczej ścieżka drobna musi pokrywać świece
    `t+1..timeout_idx` w całości (ValueError, gdy nie — fail loud).
    `exit_rule` = None → pojedyncze wyjście TP/SL/timeout (W1); inaczej wyjście wielonogowe (N1).
    Pola `exit_*` opisują OSTATNIĄ nogę; komplet nóg w `legs`.
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
        legs = _exit_legs(
            direction,
            fill,
            atr_t,
            atr_multiplier,
            exit_rule,
            open_,
            high,
            low,
            close,
            timeout_idx,
            TIE_CLOSER_TO_OPEN,
        )
        last = legs[-1]
        return TradeOutcome(
            filled=True,
            entry_level=level,
            resolution=RESOLUTION_BAR,
            fill_idx=fill.idx,
            fill_price=fill.price,
            fill_at_open=fill.at_open,
            exit_idx=last.idx,
            exit_price=last.price,
            exit_reason=last.reason,
            tp_level=tp,
            sl_level=sl,
            legs=legs,
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
    sub_legs = _exit_legs(
        direction,
        fill,
        atr_t,
        atr_multiplier,
        exit_rule,
        intrabar.open,
        intrabar.high,
        intrabar.low,
        intrabar.close,
        intrabar.last_sub_idx(timeout_idx),
        TIE_SL_FIRST,
    )
    legs = tuple(
        ExitLeg(leg.fraction, intrabar.bar_of(leg.idx), leg.price, leg.reason) for leg in sub_legs
    )
    last = legs[-1]
    return TradeOutcome(
        filled=True,
        entry_level=level,
        resolution=RESOLUTION_INTRABAR,
        fill_idx=intrabar.bar_of(fill.idx),
        fill_price=fill.price,
        fill_at_open=fill.at_open,
        exit_idx=last.idx,
        exit_price=last.price,
        exit_reason=last.reason,
        tp_level=tp,
        sl_level=sl,
        legs=legs,
    )
