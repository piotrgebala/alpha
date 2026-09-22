"""
run_positive_control_k1.py

K1 — KONTROLA POZYTYWNA aparatu pomiarowego. Skrypt jednorazowy/analityczny,
na `backtest/checkpoint_lib.py` (CLAUDE.md zasada 13).

DLACZEGO TA RUNDA ISTNIEJE
--------------------------
Projekt wyprodukował 15 wyników negatywnych albo nierozstrzygniętych i **ani razu nie
sprawdził, czy jego własny aparat pomiarowy potrafi wykryć sygnał, o którym wiadomo, że
JEST**. Istnieje jeden test jednostkowy (`test_train_regime_model_learns_separable_pattern`),
ale on bada SAM MODEL. Między surowymi danymi a werdyktem stoi osiem etapów — cechy,
etykiety, podział walk-forward, trening, próg pewności, bramka kosztowa, kill-switch,
metryki — i każdy z nich może sygnał zniszczyć.

To nie jest obawa teoretyczna. Ten projekt trzykrotnie złapał pipeline na cichym psuciu
pomiaru: przeciek early stopping (Z17, zawyżał `p`), martwy próg walidacji (Z17b, wyłączał
mechanizm w 92% foldów), resample psujący wolumen (Z9, 11% świec 1h). **Wszystkie trzy
wykryto przypadkiem albo ręcznym audytem, żadnej przez test.**

Dopóki nie wiemy, czy aparat widzi sygnał, nie wiemy, czy 15 negatywnych wyników znaczy
„nie ma sygnału", czy „nie umiemy go zobaczyć".

METODA
------
Na PRAWDZIWYCH świecach BTC 4h (te same, na których biegły S1/S1b/H2.1 — więc realny ATR,
realne etykiety, realny rozkład klas) wstrzykujemy jedną syntetyczną cechę `oracle`:

    z prawdopodobieństwem q:  oracle = prawdziwa etykieta triple-barrier
    z prawdopodobieństwem 1-q: oracle = losowa etykieta z {-1, 0, +1}

`q` to **siła wstrzykniętego sygnału**. `q = 0` to czysty szum (cecha bez informacji —
kontrola NEGATYWNA, aparat NIE MOŻE tu niczego znaleźć). `q = 1` to wyrocznia doskonała.

Potem uruchamiamy **niezmieniony pipeline produkcyjny** i porównujemy, co zmierzył, z tym,
co wstrzyknęliśmy. Wynikiem jest KRZYWA WYKRYWALNOŚCI, nie pojedyncze zaliczone/niezaliczone.

CZEGO TA RUNDA NIE ROBI
-----------------------
Nie testuje żadnej hipotezy tradingowej i nie dotyka żadnego licznika wariantów. To
**kalibracja przyrządu**, dokładnie w tej samej roli co Z19 (rachunek mocy) czy Z9
(walidacja danych). `oracle` nie wchodzi do `feature_registry.yaml` i nie ma prawa
pojawić się w żadnej rundzie hipotezowej — istnieje wyłącznie tutaj.

Użycie:
    py -m backtest.run_positive_control_k1
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from agents.feature_miner import compute_all_features
from agents.labeling import compute_triple_barrier_labels
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL

TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

ORACLE = "oracle"
LABEL_VALUES = (-1.0, 0.0, 1.0)

# Siła wstrzykniętego sygnału. q=0 to kontrola NEGATYWNA (czysty szum).
INJECTION_STRENGTHS = (0.0, 0.05, 0.10, 0.20, 0.40, 1.00)


def _inject_oracle(labels: pd.Series, q: float, rng: np.random.Generator) -> pd.Series:
    """
    Cecha, która zna prawdziwą etykietę z prawdopodobieństwem `q`, a poza tym zgaduje.

    Przy q=0 zgodność z etykietą to i tak ~1/3 przez przypadek — i to jest właściwy punkt
    odniesienia dla „brak informacji", nie zero.
    """
    noise = rng.choice(LABEL_VALUES, size=len(labels))
    keep_truth = rng.random(len(labels)) < q
    out = np.where(keep_truth, labels.to_numpy(dtype=float), noise)
    return pd.Series(out, index=labels.index)


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    raw = _load(cfg, TIMEFRAME)

    # Etykiety liczymy PRODUKCYJNĄ funkcją na PRODUKCYJNYCH cechach — `oracle` ma być
    # wyrocznią wobec tego samego targetu, który mierzy reszta projektu.
    feats = compute_all_features(
        raw,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        candles_per_day=CANDLES_PER_DAY,
    )
    labeled = compute_triple_barrier_labels(
        feats, vertical_barrier_candles=VERTICAL_BARRIER_CANDLES
    )
    labels = labeled["label"]

    print("=" * 100)
    print("K1 — KONTROLA POZYTYWNA aparatu pomiarowego")
    print("=" * 100)
    print(
        f"dane      : {len(raw)} swiec {TIMEFRAME} (te same co S1/S1b/H2.1)\n"
        f"etykiety  : {labels.notna().sum()} nie-NaN, rozklad "
        f"{dict((labels.value_counts(normalize=True).sort_index() * 100).round(2))}\n"
        f"pipeline  : NIEZMIENIONY (bez bramki rezimu, V={VERTICAL_BARRIER_CANDLES}, "
        f"walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED})\n"
        f"cechy     : {REVERSION_FEATURES} + '{ORACLE}'\n"
    )
    print("q = sila wstrzyknietego sygnalu. q=0 to KONTROLA NEGATYWNA (czysty szum):")
    print("    aparat NIE MOZE tam niczego znalezc. Jesli znajdzie - mamy przeciek.\n")

    rows = []
    for q in INJECTION_STRENGTHS:
        rng = np.random.default_rng(1000 + int(q * 100))
        df = raw.copy()
        df[ORACLE] = _inject_oracle(labels, q, rng).reindex(df.index)
        zgodnosc = float((df[ORACLE] == labels).mean())

        print(f"--- q = {q:.2f}  (faktyczna zgodnosc cechy z etykieta: {zgodnosc * 100:.1f}%) ---")
        res = run_and_summarize(
            df,
            seed=PRIMARY_SEED,
            regime_feature_sets=[(REGIME_ALL, [*REVERSION_FEATURES, ORACLE])],
            vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
            candles_per_day=CANDLES_PER_DAY,
            candle_minutes=CANDLE_MINUTES,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            trend_threshold=rule["trend_threshold"],
            range_threshold=rule["range_threshold"],
        )
        edge = res["edge_per_regime"]
        e = edge.loc[edge["regime"] == REGIME_ALL].iloc[0] if len(edge) else None
        folds = [f for f in res["backtest"]["folds_summary"] if not f["skipped"]]
        n_rows = sum(f["n_rows_evaluated"] for f in folds)
        n_abst = sum(f["n_signals_no_direction"] for f in folds)

        rows.append(
            {
                "q": q,
                "zgodnosc_cechy": zgodnosc,
                "n_trades": int(e["n_trades"]) if e is not None else 0,
                "hit_rate": float(e["hit_rate"]) if e is not None else float("nan"),
                "ci_low": float(e["ci_low"]) if e is not None else float("nan"),
                "ci_high": float(e["ci_high"]) if e is not None else float("nan"),
                "break_even": float(e["break_even_p"]) if e is not None else float("nan"),
                "margin": float(e["margin"]) if e is not None else float("nan"),
                "abstynencja": n_abst / n_rows if n_rows else float("nan"),
                "klasyfikacja": res["classification"]["classification"],
                "n_valid_folds": res["classification"]["n_valid_folds"],
            }
        )

    print("\n" + "=" * 100)
    print("KRZYWA WYKRYWALNOSCI — co wstrzyknieto vs co aparat zmierzyl")
    print("=" * 100)
    print(
        f"  {'q':>5} | {'zgodnosc':>8} | {'abstyn.':>8} | {'n_trades':>8} | "
        f"{'trafnosc':>8} | {'CI_low':>7} | {'prog':>6} | {'margines':>8} | {'werdykt':>9}"
    )
    print("  " + "-" * 92)
    for r in rows:
        print(
            f"  {r['q']:5.2f} | {r['zgodnosc_cechy'] * 100:7.1f}% | "
            f"{r['abstynencja'] * 100:7.1f}% | {r['n_trades']:8d} | "
            f"{r['hit_rate'] * 100:7.2f}% | {r['ci_low'] * 100:6.2f}% | "
            f"{r['break_even'] * 100:5.2f}% | {r['margin'] * 100:+7.2f} pp | "
            f"{r['klasyfikacja']:>9}"
        )

    print("\n" + "=" * 100)
    print("ODCZYT")
    print("=" * 100)
    null_row = rows[0]
    print(
        f"  KONTROLA NEGATYWNA (q=0): trafnosc {null_row['hit_rate'] * 100:.2f}%, "
        f"margines {null_row['margin'] * 100:+.2f} pp, werdykt {null_row['klasyfikacja']}"
    )
    print(
        "    -> aparat NIE powinien tu znalezc przewagi. Znalezienie jej oznaczaloby przeciek."
    )
    najslabszy = next(
        (r for r in rows[1:] if r["ci_low"] > r["break_even"]), None
    )
    if najslabszy:
        print(
            f"\n  NAJSLABSZY WYKRYTY SYGNAL: q = {najslabszy['q']:.2f} "
            f"(zgodnosc cechy {najslabszy['zgodnosc_cechy'] * 100:.1f}%) -> "
            f"trafnosc {najslabszy['hit_rate'] * 100:.2f}%, "
            f"CI_low {najslabszy['ci_low'] * 100:.2f}% > prog {najslabszy['break_even'] * 100:.2f}%"
        )
        print("    -> APARAT DZIALA. Ponizej tej sily sygnal jest dla niego niewidoczny.")
    else:
        print("\n  >>> ZADNA sila sygnalu nie przebila progu oplacalnosci.")
        print("      APARAT NIE POTRAFI WYKRYC NAWET WYROCZNI DOSKONALEJ (q=1).")
        print("      Wszystkie dotychczasowe wyniki negatywne sa NIEINTERPRETOWALNE.")

    print()
    pd.DataFrame(rows).to_csv(
        "runs/2026-09-22_k1-kontrola-pozytywna/krzywa_wykrywalnosci.csv", index=False
    )
    print("  zapisano: runs/2026-09-22_k1-kontrola-pozytywna/krzywa_wykrywalnosci.csv")


if __name__ == "__main__":
    main()
