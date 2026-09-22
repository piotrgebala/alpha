"""
run_funding_feature_h21.py

Eksperyment H2.1c — czy informacja SPOZA OHLCV rusza trafność kierunku.

KONFIGURACJA ZAMROŻONA w pre-rejestracji (`runs/2026-09-22_h2.0-funding-wykonalnosc/`,
z poprawką zawężającą zapisaną w `STATUS.md` §17 i w commicie `8435939` PRZED uruchomieniem):

    interwał            4h natywne, 2019-09 → 2026-07 (14 916 świec, 6,8 roku)
    bramka reżimu       BRAK (wartownik REGIME_ALL) — bramkowanie dwukrotnie zagłodziło próbę
    V                   3 (12h) — spójność bramka↔horyzont (Z16)
    walk-forward        60/28/28 dni, seed 42
    model kosztów       NIEZMIENIONY (maker/taker, `timeout_leg` domyślne = TAKER, H3)
    KRYTERIUM SUKCESU   ci_low(p) > 52,69%   (sprostowane w H3 z zawyżonego 53,12%)
    KLAUZULA            n < 1 000 ⇒ NIEROZSTRZYGNIĘTE, bez interpretacji w żadną stronę
    REGUŁA STOP         1 wariant. Wynik negatywny ⇒ koniec serii H2.

DWA RAMIONA, nie jedno — i to jest poprawka wobec pierwotnej pre-rejestracji:

    A (baseline)  bez bramki, REVERSION_FEATURES (4 cechy)       → 0 wariantów, odniesienie
    B (kandydat)  bez bramki, te 4 cechy + `funding_rate`        → 1 wariant, WYCZERPUJE H2

    (Zestaw cech jest TEN SAM co w S1/S1b — `REVERSION_FEATURES`. Projekt nigdy nie
    karmił jednego modelu wszystkimi 10 cechami: `MOMENTUM_FEATURES` i `REVERSION_FEATURES`
    to rozłączne czwórki. Zmianą jest wyłącznie usunięcie bramki i dodanie funding.)

Pierwotny zapis zmieniał naraz DWIE rzeczy wobec S1b (usunięcie bramki + nowa cecha), co
łamie zasadę 4: przy wyniku negatywnym nie dałoby się orzec, która zmiana zawiodła. Rozbicie
jest dopuszczalne, bo to ZAOSTRZENIE — próg 52,69% pochodzi z geometrii kosztu, a nie
z obejrzanej trafności, więc pomiar ramienia A nie może przesunąć bramki.

Skrypt świadomie NIE ogłasza zwycięzcy — drukuje liczby i to, czy pre-rejestrowane kryterium
jest spełnione. Decyzję podpisuje dokumentacja rundy.

Użycie:
    py -m backtest.run_funding_feature_h21
"""

from __future__ import annotations

import pandas as pd
import yaml

from agents.funding_features import FUNDING_COLUMN, attach_funding_rate
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.metrics import min_detectable_hit_rate
from data.fetch_funding import get_funding_rate_history_cached

TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

# Pre-rejestrowane, NIE do zmiany po obejrzeniu wyniku.
PREREGISTERED_BREAK_EVEN = 0.5269
MIN_N_FOR_CONCLUSION = 1_000

# Trafność zbiorcza projektu (Z10, 7 687 transakcji) — punkt odniesienia dla "ile trzeba dołożyć".
PROJECT_POOLED_HIT_RATE = 0.5027


def _arm(df: pd.DataFrame, rule: dict, features: list[str]) -> dict:
    return run_and_summarize(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, features)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        candle_minutes=CANDLE_MINUTES,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )


def _edge_row(result: dict) -> pd.Series:
    e = result["edge_per_regime"]
    return e.loc[e["regime"] == REGIME_ALL].iloc[0]


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    df = _load(cfg, TIMEFRAME)

    funding = get_funding_rate_history_cached(
        symbol=cfg["primary_symbol"],
        start=(cfg.get("timeframe_start_overrides") or {}).get("4h", cfg["start"]),
        end=cfg["end"],
        cache_dir=cfg["cache_dir"],
        exchange_id=cfg["exchange_id"],
    )
    df = attach_funding_rate(df, funding)

    print("=" * 98)
    print("H2.1c — funding jako 11. cecha, BEZ bramki rezimu (konfiguracja ZAMROZONA)")
    print("=" * 98)
    print(
        f"dane      : {len(df)} swiec {TIMEFRAME}, {df['timestamp'].min()} -> {df['timestamp'].max()}\n"
        f"funding   : {len(funding)} rekordow, swiec ze stawka {df[FUNDING_COLUMN].notna().sum()}, "
        f"NaN {df[FUNDING_COLUMN].isna().sum()} (sprzed 1. rozliczenia)\n"
        f"bramka    : BRAK (REGIME_ALL)  |  V = {VERTICAL_BARRIER_CANDLES}  |  "
        f"walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}  |  seed {PRIMARY_SEED}\n"
        f"KRYTERIUM : ci_low > {100 * PREREGISTERED_BREAK_EVEN:.2f}%   "
        f"KLAUZULA: n < {MIN_N_FOR_CONCLUSION}\n"
    )

    arms = {
        "A baseline (4 cechy OHLCV)": REVERSION_FEATURES,
        "B kandydat (4 + funding)": [*REVERSION_FEATURES, FUNDING_COLUMN],
    }
    results = {}
    for name, feats in arms.items():
        print(f"--- uruchamiam: {name} ({len(feats)} cech) ---")
        results[name] = _arm(df, rule, feats)

    print("\n" + "=" * 98)
    print("LEJEK SYGNALOW")
    print("=" * 98)
    print(f"  {'licznik':>30} | {'A baseline':>12} | {'B kandydat':>12}")
    print("  " + "-" * 60)
    for key in (
        "n_rows_evaluated",
        "n_signals_no_direction",
        "n_signals_cost_gated",
        "n_signals",
    ):
        vals = [
            sum(f[key] for f in r["backtest"]["folds_summary"] if not f["skipped"])
            for r in results.values()
        ]
        print(f"  {key:>30} | {vals[0]:12d} | {vals[1]:12d}")
    for name, r in results.items():
        folds = pd.DataFrame(r["backtest"]["folds_summary"])
        print(
            f"  {name}: foldy {len(folds)}, pominiete {int(folds['skipped'].sum())}, "
            f"z early stoppingiem {int(folds.get('early_stopping_used', pd.Series(dtype=bool)).sum())}"
        )

    print("\n" + "=" * 98)
    print("ROZBICIE EDGE'U")
    print("=" * 98)
    for name, r in results.items():
        print(f"\n--- {name} ---")
        print(r["edge_per_regime"].to_string(index=False))
        print(r["pooled_per_regime"].to_string(index=False))
        print(r["classification"])

    a, b = (_edge_row(results[k]) for k in arms)
    print("\n" + "=" * 98)
    print("DELTA — czy cecha spoza OHLCV ruszyla trafnosc")
    print("=" * 98)
    print(f"  {'miara':>22} | {'A baseline':>12} | {'B kandydat':>12} | {'delta':>10}")
    print("  " + "-" * 66)
    for label, key, scale in (
        ("n transakcji", "n_trades", 1),
        ("trafnosc %", "hit_rate", 100),
        ("ci_low %", "ci_low", 100),
        ("ci_high %", "ci_high", 100),
        ("break-even %", "break_even_p", 100),
        ("margines pp", "margin", 100),
    ):
        va, vb = a[key] * scale, b[key] * scale
        fmt = "12.0f" if key == "n_trades" else "12.2f"
        print(f"  {label:>22} | {va:{fmt}} | {vb:{fmt}} | {vb - va:+10.2f}")

    print("\n" + "=" * 98)
    print("WERDYKT wobec PRE-REJESTROWANEGO kryterium (ramie B)")
    print("=" * 98)
    n, hit, ci_low = int(b["n_trades"]), b["hit_rate"], b["ci_low"]
    print(f"  n                       = {n}")
    print(f"  trafnosc zmierzona      = {100 * hit:.2f}%")
    print(f"  95% CI                  = [{100 * ci_low:.2f}%; {100 * b['ci_high']:.2f}%]")
    print(f"  prog pre-rejestrowany   = {100 * PREREGISTERED_BREAK_EVEN:.2f}%")
    print(f"  trzeba bylo zmierzyc    = {100 * min_detectable_hit_rate(PREREGISTERED_BREAK_EVEN, n):.2f}%")
    print(
        f"  przyrost nad projektem  = {100 * (hit - PROJECT_POOLED_HIT_RATE):+.2f} pp "
        f"(zbiorcza trafnosc projektu: {100 * PROJECT_POOLED_HIT_RATE:.2f}%, Z10)"
    )
    print()
    if n < MIN_N_FOR_CONCLUSION:
        print(f"  >>> NIEROZSTRZYGNIETE: n={n} < {MIN_N_FOR_CONCLUSION}")
        print("      Klauzula pre-rejestrowana. Wyniku NIE interpretuje w zadna strone.")
    elif ci_low > PREREGISTERED_BREAK_EVEN:
        print("  >>> KRYTERIUM SPELNIONE — dolny kraniec CI przebija prog oplacalnosci.")
    else:
        print(
            f"  >>> KRYTERIUM NIESPELNIONE: przepada o "
            f"{100 * (PREREGISTERED_BREAK_EVEN - ci_low):.2f} pp."
        )


if __name__ == "__main__":
    main()
