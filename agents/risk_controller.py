"""
risk_controller.py

Sizing i kill-switch dla Fazy 0 (IMPLEMENTATION_PLAN.md §5 Commit 5.5). Zastępuje
tymczasowy `backtest.engine._placeholder_risk_controller` — formuła identyczna,
teraz w formalnym, testowanym (hypothesis, Warstwa 3 DoD) module. Pełne
uzasadnienie: docs/rag/03_ryzyko_i_sizing.md.

KONTRAKT (ml_optimizer -> risk_controller), docs/rag/03:
    ml_optimizer emituje:
      { signal_direction: -1|0|1, signal_confidence: float,
        regime: "trend"|"range", atr_14: float, entry_price: float }
    risk_controller zwraca:
      { position_size: float, stop_price: float, take_profit_price: float }

Dwie warstwy:
  - compute_position_size(...) -> float: czysty numeryczny rdzeń sizingu
    (size_risk/size_leverage/min()) — testowany bezpośrednio przez hypothesis
    (docs/rag/05_metodologia_wytwarzania_i_testow.md, przykład property testu).
  - compute_sizing(...) -> dict: pełny kontrakt powyżej, wywołuje
    compute_position_size po przeskalowaniu risk_per_trade przez signal_confidence
    (słabszy sygnał, mniejsza pozycja, nie próg odcięcia). To jest funkcja
    wstrzykiwana jako `risk_controller_fn` domyślnie w backtest.engine.run_backtest.

SIZING (leverage cap zawsze wygrywa, jawnie — CLAUDE.md zasada 5):
    size_risk     = (equity * effective_risk_per_trade) / (atr_multiplier * atr_14)
    size_leverage = (equity * max_leverage) / entry_price
    position_size = min(size_risk, size_leverage)

    gdzie effective_risk_per_trade = risk_per_trade * signal_confidence.

    `size_leverage` NIE zależy od signal_confidence — jest twardym sufitem, inaczej
    "leverage cap zawsze wygrywa" przestałoby być prawdziwym hard cap.

KRYTYCZNE (CLAUDE.md zasada 3): `atr_multiplier` domyślnie importowany z
`agents.labeling.ATR_MULTIPLIER` — TEN SAM mnożnik co bariera triple-barrier.
Nigdy nie redefiniuj 1.5 osobno tutaj.

KILL-SWITCH (docs/rag/03 — "fail-safe nie fail-soft"):
    drawdown = (peak_equity - equity) / peak_equity
    triggered = drawdown > drawdown_threshold

    Prosta, czysta, bezstanowa funkcja — caller (backtest.engine.run_backtest)
    trzyma `peak_equity` jako running max i wywołuje to na nowo przy KAŻDYM
    sygnale (dynamiczny re-check, nie permanentny latch — decyzja potwierdzona
    2026-08-01: kill-switch wznawia normalną pracę, gdy equity odzyska się
    powyżej progu). Cel (Faza 0): zobaczyć historycznie, jak często by się
    aktywował, zanim jest komponentem produkcyjnym (Faza 3: niezależny
    proces/wątek monitorujący konto, nie część głównej pętli decyzyjnej).
"""

from __future__ import annotations

from agents.labeling import ATR_MULTIPLIER

# Wartości startowe (docs/rag/03_ryzyko_i_sizing.md), do kalibracji WYŁĄCZNIE
# wewnątrz walk-forward (CLAUDE.md zasada 1). Źródło prawdy mirroring:
# config/settings.yaml sekcja `risk`.
RISK_PER_TRADE = 0.005  # 0.5% equity, fixed-fractional (NIE Kelly na tym etapie)
MAX_LEVERAGE = 3.0  # konserwatywnie, wartość startowa
KILL_SWITCH_DRAWDOWN_PCT = 0.15  # drawdown od peaku equity > 15% -> stop nowych sygnałów


def compute_position_size(
    equity: float,
    atr_14: float,
    entry_price: float,
    risk_per_trade: float = RISK_PER_TRADE,
    max_leverage: float = MAX_LEVERAGE,
    atr_multiplier: float = ATR_MULTIPLIER,
) -> float:
    """
    Czysty numeryczny rdzeń sizingu — bez signal_confidence/signal_direction
    (caller przeskalowuje risk_per_trade PRZED wywołaniem, patrz compute_sizing).

        size_risk     = (equity * risk_per_trade) / (atr_multiplier * atr_14)
        size_leverage = (equity * max_leverage) / entry_price
        position_size = min(size_risk, size_leverage)

    "Dlaczego min(), nie któraś z formuł osobno" (docs/rag/03): bez jawnej reguły,
    w niskiej zmienności (mały ATR -> mały stop_distance) fixed-fractional może
    wypluć pozycję większą niż limit leverage. Reguła musi być jawna, nie coś do
    odkrycia w runtime.

    Args:
        equity: equity konta (USD), > 0.
        atr_14: ATR-14 w momencie sygnału (jednostki ceny), > 0.
        entry_price: cena wejścia, > 0.
        risk_per_trade: ułamek equity ryzykowany na transakcję (już przeskalowany
            przez signal_confidence, jeśli dotyczy).
        max_leverage: twardy sufit dźwigni.
        atr_multiplier: mnożnik ATR dla stop-lossa — MUSI być identyczny z
            barierą triple-barrier (agents.labeling.ATR_MULTIPLIER).

    Returns:
        position_size (jednostki bazowe instrumentu), zawsze >= 0.
    """
    size_risk = (equity * risk_per_trade) / (atr_multiplier * atr_14)
    size_leverage = (equity * max_leverage) / entry_price
    return min(size_risk, size_leverage)


def compute_sizing(
    signal_direction: float,
    signal_confidence: float,
    regime: str,
    atr_14: float,
    entry_price: float,
    equity: float,
    risk_per_trade: float = RISK_PER_TRADE,
    max_leverage: float = MAX_LEVERAGE,
    atr_multiplier: float = ATR_MULTIPLIER,
) -> dict:
    """
    Kontrakt pełny ml_optimizer -> risk_controller (docs/rag/03). Domyślna
    implementacja `risk_controller_fn` w backtest.engine.run_backtest — zastępuje
    dawny `_placeholder_risk_controller` (formuła identyczna, teraz formalny moduł).

    `signal_confidence` skaluje WYŁĄCZNIE `risk_per_trade` (size_risk) —
    `size_leverage` zostaje twardym sufitem NIEZALEŻNYM od confidence (CLAUDE.md
    zasada 5 — "leverage cap zawsze wygrywa" musi być prawdziwym hard cap).

    `regime` jest przyjmowany dla kompletności kontraktu (docs/rag/03) — nie
    wpływa jeszcze na sizing (możliwe rozszerzenie: regime-specific risk params,
    Faza 1+).

    Args:
        signal_direction: -1.0 (short), 0.0 (brak sygnału), 1.0 (long).
        signal_confidence: predict_proba klasy argmax, z agents.ml_optimizer.
        regime: "trend" albo "range".
        atr_14: ATR-14 w momencie sygnału.
        entry_price: cena wejścia.
        equity: equity konta w momencie sygnału.
        risk_per_trade/max_leverage/atr_multiplier: patrz compute_position_size.

    Returns:
        {"position_size": float, "stop_price": float, "take_profit_price": float}
    """
    effective_risk_per_trade = risk_per_trade * signal_confidence
    position_size = compute_position_size(
        equity,
        atr_14,
        entry_price,
        risk_per_trade=effective_risk_per_trade,
        max_leverage=max_leverage,
        atr_multiplier=atr_multiplier,
    )

    stop_price = entry_price - signal_direction * atr_multiplier * atr_14
    take_profit_price = entry_price + signal_direction * atr_multiplier * atr_14

    return {
        "position_size": position_size,
        "stop_price": stop_price,
        "take_profit_price": take_profit_price,
    }


def check_kill_switch(
    equity: float,
    peak_equity: float,
    drawdown_threshold: float = KILL_SWITCH_DRAWDOWN_PCT,
) -> bool:
    """
    Kill-switch: drawdown equity od peaku > drawdown_threshold -> True (zatrzymaj
    generowanie nowych sygnałów). Czysta, bezstanowa funkcja — caller trzyma
    `peak_equity` jako running max i wywołuje to na nowo przy każdym sygnale
    (dynamiczny re-check, nie permanentny latch — decyzja 2026-08-01).

    Fail-safe, nie fail-soft (docs/rag/03): jeśli `peak_equity <= 0` (stan
    zdegenerowany, konto już zdmuchnięte do zera albo poniżej), zwraca True
    zamiast dzielić przez zero albo milcząco kontynuować.

    Args:
        equity: aktualne equity.
        peak_equity: najwyższe equity osiągnięte do tej pory (running max,
            liczone przez caller na danych TYLKO z przeszłości/teraźniejszości).
        drawdown_threshold: próg ułamkowy (0.15 = 15%).

    Returns:
        True jeśli kill-switch aktywny (drawdown > próg, albo peak_equity <= 0).
    """
    if peak_equity <= 0:
        return True
    drawdown = (peak_equity - equity) / peak_equity
    return drawdown > drawdown_threshold
