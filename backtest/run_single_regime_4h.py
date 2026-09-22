"""
run_single_regime_4h.py

Eksperyment S1 — pierwsza runda NOWEJ serii hipotezowej: architektura JEDNOREŻIMOWA na
świecach 4h. Skrypt jednorazowy/analityczny, poza pytest, na `backtest/checkpoint_lib.py`.

KONFIGURACJA JEST ZAMROŻONA — pochodzi z pre-rejestracji zapisanej PRZED uruchomieniem
czegokolwiek: `runs/2026-09-22_z5b-long-history-4h-preregistration/README.md`. Skrypt jej nie
wybiera i nie stroi; wyłącznie wykonuje i raportuje.

Dlaczego ta konfiguracja (streszczenie łańcucha pomiarów, pełne uzasadnienia w runs/):
  - reżim `range`, BEZ `trend` — Z16: `trend` ma 0,49% świec ze spójną etykietą, a próby
    wydłużenia jego epizodów zapadają udział do 0,05-1,5%; jest niewykonalny na każdym
    interwale (Z19).
  - świece 4h natywne — Z9: resample z 5m psuje WOLUMEN (11% świec 1h), a `volume_zscore_20`
    jest cechą modelu. 4h obniża też próg opłacalności, bo koszt jest stały per transakcja,
    a ATR rośnie z interwałem.
  - historia od 2019-09 — Z19/Z5b: na 4h wiążącym ograniczeniem była LICZEBNOŚĆ PRÓBY
    (1 551 wobec wymaganych); 6,8 roku daje 4 076.
  - V = 3 — Z16/Z5b: jedyny horyzont, przy którym `range` jest spójny (70,2% świec z pełnym
    oknem etykiety wewnątrz epizodu). Wybrany MIMO wyższego progu niż V=12, bo spójność to
    wymóg poprawności, nie preferencja.
  - okna 60/28/28 dni — Z5b: przy 14 dniach fold ma ~22 świece `range`, poniżej
    MIN_TRAIN_ROWS=30, więc byłby pomijany. Artefakt jednostek (dni vs świece), nie rynku.

KRYTERIUM SUKCESU (pre-rejestrowane): dolny kraniec 95% CI trafności kierunku > break-even.
KLAUZULA NIEROZSTRZYGALNOŚCI: realne n < MIN_N_FOR_CONCLUSION => wynik nierozstrzygalny,
bez interpretowania w którąkolwiek stronę.

Skrypt świadomie NIE ogłasza zwycięzcy ani nie podejmuje decyzji — drukuje liczby i to,
czy pre-rejestrowane kryterium jest spełnione. Decyzja i jej podpis należą do dokumentacji.

Użycie:
    py -m backtest.run_single_regime_4h
"""

from __future__ import annotations

import pandas as pd
import yaml

from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.metrics import min_detectable_hit_rate

# --- KONFIGURACJA ZAMROŻONA (pre-rejestracja z 2026-09-22) ---
TIMEFRAME = "4h"
REGIME = "range"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

# Próg opłacalności policzony w Z5b z REALNEGO rozkładu wypłat przy V=3 (z uwzględnieniem
# 60,8% timeoutów), nie z założenia "każda transakcja trafia barierę".
PREREGISTERED_BREAK_EVEN = 0.5460
MIN_N_FOR_CONCLUSION = 925


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    df = _load(cfg, TIMEFRAME)

    print("=" * 96)
    print(
        "S1 — architektura jednoreżimowa na 4h (konfiguracja ZAMROŻONA w pre-rejestracji)"
    )
    print("=" * 96)
    print(
        f"dane: {len(df)} świec {TIMEFRAME}, {df['timestamp'].min()} -> {df['timestamp'].max()}\n"
        f"reżim: {REGIME} (bez `trend`)  |  V = {VERTICAL_BARRIER_CANDLES} "
        f"({VERTICAL_BARRIER_CANDLES * CANDLE_MINUTES / 60:.0f}h)  |  "
        f"walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS} dni  |  seed {PRIMARY_SEED}\n"
        f"kryterium sukcesu: dolny kraniec 95% CI > {100 * PREREGISTERED_BREAK_EVEN:.2f}%\n"
        f"klauzula nierozstrzygalności: n < {MIN_N_FOR_CONCLUSION}\n"
    )

    result = run_and_summarize(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME, REVERSION_FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        candle_minutes=CANDLE_MINUTES,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )

    print("=== Klasyfikacja (kryteria docs/rag/03, NIEZMIENIONE) ===")
    print(result["classification"])
    print("\n=== Diagnostyka pooled ===")
    print(result["pooled_per_regime"].to_string(index=False))
    print("\n=== Rozbicie edge'u ===")
    print(result["edge_per_regime"].to_string(index=False))

    folds = pd.DataFrame(result["backtest"]["folds_summary"])
    active = folds[~folds["skipped"]]
    print(
        f"\n=== Foldy === łącznie={len(folds)}, aktywne={len(active)}, "
        f"pominięte={int(folds['skipped'].sum())}"
    )
    if len(active):
        print(
            f"sygnały przepuszczone={int(active['n_signals'].sum())}, "
            f"odrzucone przez koszt={int(active['n_signals_cost_gated'].sum())}"
        )

    edge = result["edge_per_regime"]
    row = edge.loc[edge["regime"] == REGIME]
    print("\n" + "=" * 96)
    print("WERDYKT wobec PRE-REJESTROWANEGO kryterium")
    print("=" * 96)
    if row.empty:
        print("Brak transakcji w reżimie — wynik NIEROZSTRZYGALNY.")
        return
    r = row.iloc[0]
    n, hit, ci_low = int(r["n_trades"]), r["hit_rate"], r["ci_low"]
    required = min_detectable_hit_rate(PREREGISTERED_BREAK_EVEN, n)
    print(
        f"  n                       = {n}\n"
        f"  trafność zmierzona      = {100 * hit:.2f}%\n"
        f"  95% CI                  = [{100 * r['ci_low']:.2f}%; {100 * r['ci_high']:.2f}%]\n"
        f"  break-even (pre-rej.)   = {100 * PREREGISTERED_BREAK_EVEN:.2f}%\n"
        f"  break-even (zmierzone)  = {100 * r['break_even_p']:.2f}%\n"
        f"  trzeba było zmierzyć    = {100 * required:.2f}%\n"
    )
    if n < MIN_N_FOR_CONCLUSION:
        print(
            f"  >>> NIEROZSTRZYGALNE: n={n} < {MIN_N_FOR_CONCLUSION} (klauzula pre-rejestracji).\n"
            f"      Wyniku NIE interpretujemy w żadną stronę."
        )
    elif ci_low > PREREGISTERED_BREAK_EVEN:
        print(
            "  >>> KRYTERIUM SPEŁNIONE: dolny kraniec CI przekracza próg opłacalności."
        )
    else:
        print(
            "  >>> KRYTERIUM NIESPEŁNIONE: dolny kraniec CI nie przekracza progu.\n"
            "      Zgodnie z regułą STOP to koniec tej linii hipotezy."
        )


if __name__ == "__main__":
    main()
