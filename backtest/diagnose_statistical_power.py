"""
diagnose_statistical_power.py

Zadanie Z19 (Backlog II) — czy eksperyment na grubszym interwale w ogóle MOŻE cokolwiek
rozstrzygnąć? Skrypt read-only, poza pytest, na trwałym cache w `data/raw/`.

Po co, skoro Z9 pokazał obiecujące progi: Z9 policzył, że na 4h próg opłacalności spada do
52,74%, czyli w okolice realistyczne. Ale niski próg jest bezużyteczny, jeśli próba jest za
mała, by odróżnić „trafność powyżej progu" od szumu. Grubszy interwał daje jednocześnie
LEPSZY próg i MNIEJSZĄ próbę (6 576 świec 4h wobec 315 648 świec 5m) — te dwa efekty idą
w przeciwne strony i trzeba je zestawić PRZED uruchomieniem eksperymentu, nie po.

Kluczowa liczba: `min_detectable_hit_rate` = trafność, którą trzeba ZMIERZYĆ, żeby dolny
kraniec przedziału ufności przekroczył próg opłacalności. Jeśli wypada absurdalnie wysoko,
eksperyment nie rozstrzygnie niczego niezależnie od wyniku — i uczciwiej go nie uruchamiać,
niż potem interpretować nierozstrzygalną liczbę jako przesłankę.

Szacunek liczby transakcji jest GÓRNYM OGRANICZENIEM: zakłada, że każda świeca reżimu
w oknie testowym staje się transakcją. W rzeczywistości odpadają świece bez sygnału
kierunkowego (`direction == 0`), odrzucone przez bramkę kosztową i foldy poniżej
`MIN_TRAIN_ROWS`. Jeśli NAWET górne ograniczenie nie wystarcza, wniosek jest rozstrzygający.

Użycie:
    py -m backtest.diagnose_statistical_power
"""

from __future__ import annotations

import pandas as pd
import yaml

from agents.feature_miner import (
    compute_atr_14,
    compute_atr_pctrank_20d,
    compute_direction_persistence_10,
)
from agents.labeling import ATR_MULTIPLIER, STEP_DAYS, TEST_WINDOW_DAYS, TRAIN_WINDOW_DAYS
from backtest.costs import MAKER, TAKER, round_trip_cost_fraction
from backtest.diagnose_cost_feasibility import _regime_series
from backtest.engine import MIN_TRAIN_ROWS
from backtest.metrics import break_even_hit_rate, min_detectable_hit_rate, required_trades
from backtest.diagnose_timeframe_geometry import CANDLES_PER_DAY, _load, _load_cfg

REGIME_WINDOW_DAYS = 20  # atr_pctrank_20d — warmup, w którym reżim jest nieokreślony

# Z5b: okna walk-forward SKALOWANE do interwału. Stałe 60/14/14 dni są zdefiniowane w dniach,
# więc na 4h dają tylko 84 świece testowe na fold (~22 świec `range`) — poniżej MIN_TRAIN_ROWS,
# czyli fold byłby pomijany. To artefakt jednostek, nie właściwość rynku, więc okno testowe
# na 4h rośnie do 28 dni. Okno treningowe zostaje: 60 dni na 4h to 360 świec (~94 `range`),
# czyli powyżej progu. Wartości NIE są strojone pod wynik — wynikają z MIN_TRAIN_ROWS.
WALK_FORWARD = {
    "5m": (TRAIN_WINDOW_DAYS, TEST_WINDOW_DAYS, STEP_DAYS),
    "1h": (TRAIN_WINDOW_DAYS, TEST_WINDOW_DAYS, STEP_DAYS),
    "4h": (TRAIN_WINDOW_DAYS, 28, 28),
}


def main() -> None:
    cfg = _load_cfg()
    with open("config/settings.yaml", encoding="utf-8") as f:
        cfg_rule = yaml.safe_load(f)["regime_rule"]

    cost = round_trip_cost_fraction(entry_leg=MAKER, exit_leg=TAKER)
    print("=" * 100)
    print("Z19 — czy eksperyment na grubszym interwale może cokolwiek rozstrzygnąć?")
    print("=" * 100)
    print(
        f"koszt C = {100 * cost:.4f}%  |  walk-forward {TRAIN_WINDOW_DAYS}/{TEST_WINDOW_DAYS}/"
        f"{STEP_DAYS} dni  |  MIN_TRAIN_ROWS = {MIN_TRAIN_ROWS}\n"
    )

    rows: list[dict] = []
    for timeframe in ("5m", "1h", "4h"):
        df = _load(cfg, timeframe)
        per_day = CANDLES_PER_DAY[timeframe]
        atr = compute_atr_14(df)
        atr_rank = compute_atr_pctrank_20d(df, candles_per_day=per_day)
        persistence = compute_direction_persistence_10(df)
        valid = atr.notna() & atr_rank.notna() & persistence.notna()
        regime = _regime_series(
            atr_rank, persistence, cfg_rule["trend_threshold"], cfg_rule["range_threshold"]
        )
        atr_over_price = atr / df["close"]

        train_days, test_window_days, step_days = WALK_FORWARD[timeframe]
        span_days = (df["timestamp"].max() - df["timestamp"].min()).total_seconds() / 86400.0
        # Okna testowe pokrywają wszystko po warmupie i po PIERWSZYM oknie treningowym.
        test_days = max(0.0, span_days - REGIME_WINDOW_DAYS - train_days)
        test_coverage = test_days / span_days if span_days else 0.0
        n_folds = int(test_days // step_days)

        for name in ("range", "trend"):
            mask = valid & (regime == name)
            regime_candles = int(mask.sum())
            # GÓRNE ograniczenie: wszystkie świece reżimu, które trafiają w okna testowe.
            n_upper = int(regime_candles * test_coverage)
            per_fold = n_upper / n_folds if n_folds else 0.0

            barrier = ATR_MULTIPLIER * float(atr_over_price[mask].median()) if regime_candles else float("nan")
            be = break_even_hit_rate(cost, barrier)
            p_min = min_detectable_hit_rate(be, n_upper)
            n_needed = required_trades(be, 0.5) if not pd.isna(be) else float("nan")

            rows.append(
                {
                    "interwał": timeframe,
                    "lat": round(span_days / 365.25, 1),
                    "okno test": test_window_days,
                    "reżim": name,
                    "świec reżimu": regime_candles,
                    "n (górne ogr.)": n_upper,
                    "na fold": round(per_fold, 1),
                    "fold >= 30?": "tak" if per_fold >= MIN_TRAIN_ROWS else "NIE",
                    "break_even": be,
                    "trzeba zmierzyć": p_min,
                    "n dla mocy 80%": round(n_needed) if n_needed == n_needed else float("nan"),
                    "moc wystarcza?": "tak" if n_upper >= n_needed else "NIE",
                }
            )

    table = pd.DataFrame(rows)
    fmt = table.copy()
    for col in ("break_even", "trzeba zmierzyć"):
        fmt[col] = (100 * fmt[col]).round(2).astype(str) + "%"
    print(fmt.to_string(index=False))

    print(
        "\n[legenda]\n"
        "  n (górne ogr.)  - wszystkie świece reżimu w oknach testowych; REALNE n będzie MNIEJSZE\n"
        "                    (odpadają brak sygnału, bramka kosztowa, foldy < MIN_TRAIN_ROWS)\n"
        "  na fold         - średnio świec reżimu na jeden fold testowy; poniżej MIN_TRAIN_ROWS\n"
        "                    fold jest POMIJANY przez backtest.engine\n"
        "  trzeba zmierzyć - trafność, przy której DOLNY kraniec 95% CI przekracza break_even,\n"
        "                    czyli minimum, by uczciwie orzec rentowność\n"
        "  n dla mocy 80%  - liczba transakcji potrzebna, by odróżnić break_even od 50%\n"
    )

    print("=" * 100)
    print("WNIOSEK — wykonalność per konfiguracja")
    print("=" * 100)
    for _, r in table.iterrows():
        verdict = []
        if r["fold >= 30?"] == "NIE":
            verdict.append(f"foldy za małe ({r['na fold']} < {MIN_TRAIN_ROWS} świec/fold)")
        if r["moc wystarcza?"] == "NIE":
            verdict.append(f"za mała próba (n<={r['n (górne ogr.)']} vs wymagane {r['n dla mocy 80%']})")
        status = "WYKONALNE" if not verdict else "NIEWYKONALNE: " + "; ".join(verdict)
        print(
            f"  {r['interwał']:3s} {r['reżim']:6s} -> {status}\n"
            f"      trzeba zmierzyć trafność >= {100 * r['trzeba zmierzyć']:.2f}% "
            f"(break-even {100 * r['break_even']:.2f}%)"
        )


if __name__ == "__main__":
    main()
