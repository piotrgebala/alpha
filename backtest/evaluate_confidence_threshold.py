"""
evaluate_confidence_threshold.py

Commit 2.13 (Runda 3/4 programu "droga do GO") — formalny test OOS pre-rejestrowanej
hipotezy: czy odrzucanie sygnałów o niskiej `signal_confidence` podnosi trafność kierunku
na tyle, by przekroczyć próg break-even. Skrypt jednorazowy/analityczny, poza pytest
(jak `run_checkpoint_v2.py` / `evaluate_feature_candidate.py`), zbudowany na wspólnej
bibliotece `backtest/checkpoint_lib.py` (Z13).

HIPOTEZA (zarejestrowana PRZED uruchomieniem, patrz runs/2026-09-21_c2.12-*.md
sekcja "Rekomendacja"):
    Trafność kierunku rośnie monotonicznie z `signal_confidence` (zmierzone przed
    programem: range 48,1/48,9/53,4/57,1%, trend 42,4/46,5/50,5/63,3% po kwartylach).
    Przy progach break-even z C2.12 (range 66,6%, trend 58,9%) górny kwartyl powinien
    dać margines -9,5 pp w `range`, ale +4,4 pp w `trend`.

METODOLOGIA — pre-rejestrowana, bo tu jest całe ryzyko p-hackingu:
  1. Próg = kwantyl `signal_confidence` policzony na foldzie TRENINGOWYM, zastosowany do
     testowego (`backtest.engine._train_fold_confidence_threshold`). Nigdy kwantyl zbioru
     testowego.
  2. JEDNA wartość q = PREREGISTERED_CONFIDENCE_QUANTILE = 0.75. Zero sweepu po q —
     przeszukiwanie byłoby dobieraniem parametru po wyniku (CLAUDE.md zasada 1 i 4).
  3. Porównanie baseline (q=None) vs kandydat (q=0.75) przez ten sam pipeline, bez
     dotykania czegokolwiek innego (koszty, progi reżimu, cechy, model — bez zmian).

KRYTERIUM SUKCESU (pre-rejestrowane): pooled hit rate istotnie powyżej własnego
break-even (jednostronne z > 2) w co najmniej jednym reżimie ORAZ poprawa klasyfikacji.
Skrypt świadomie NIE wybiera "zwycięzcy" — decyzja należy do użytkownika.

Użycie:
    py -m backtest.evaluate_confidence_threshold
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import PRIMARY_SEED, fetch_data, load_config, run_and_summarize
from backtest.engine import PREREGISTERED_CONFIDENCE_QUANTILE


def _edge_with_significance(edge: pd.DataFrame) -> pd.DataFrame:
    """
    Dokłada do rozbicia edge'u (Commit 2.11) jednostronną istotność marginesu:

        z_margin = (hit_rate - break_even_p) / sqrt(0.25 / n)

    czyli "o ile odchyleń standardowych trafność przekracza próg opłacalności".
    To jest liczba, o którą pyta pre-rejestrowane kryterium sukcesu — nie sam znak
    marginesu, bo ten przy małym n bywa szumem.
    """
    out = edge.copy()
    out["z_margin"] = (out["hit_rate"] - out["break_even_p"]) / np.sqrt(0.25 / out["n_trades"])
    return out


def _print_variant(name: str, summary: dict) -> pd.DataFrame:
    print(f"\n{'=' * 78}\n{name}\n{'=' * 78}")
    print(summary["classification"])
    print("\n-- per reżim --")
    print(summary["per_regime"].to_string(index=False))
    print("\n-- pooled per reżim --")
    print(summary["pooled_per_regime"].to_string(index=False))
    edge = _edge_with_significance(summary["edge_per_regime"])
    print("\n-- rozbicie edge'u (2p-1)*B vs C + istotność marginesu --")
    print(edge.to_string(index=False))

    folds = pd.DataFrame(summary["backtest"]["folds_summary"])
    active = folds[~folds["skipped"]]
    if len(active):
        print(
            f"\n-- sygnały: przepuszczone={int(active['n_signals'].sum())}, "
            f"odrzucone przez pewność={int(active['n_signals_confidence_gated'].sum())}, "
            f"odrzucone przez koszt={int(active['n_signals_cost_gated'].sum())}"
        )
    return edge


def main() -> None:
    cfg = load_config()
    raw_ohlcv = fetch_data(cfg)

    print(f"\n[seed={PRIMARY_SEED}] baseline (q=None) — odtworzenie C2.12...")
    baseline = run_and_summarize(raw_ohlcv, seed=PRIMARY_SEED)
    edge_base = _print_variant("BASELINE — bez progu pewności (C2.12)", baseline)

    q = PREREGISTERED_CONFIDENCE_QUANTILE
    print(f"\n[seed={PRIMARY_SEED}] kandydat (q={q}, próg z foldu TRENINGOWEGO)...")
    candidate = run_and_summarize(raw_ohlcv, seed=PRIMARY_SEED, confidence_quantile=q)
    edge_cand = _print_variant(f"KANDYDAT — próg pewności q={q}", candidate)

    print(f"\n{'=' * 78}\nPORÓWNANIE — pre-rejestrowane kryterium sukcesu\n{'=' * 78}")
    merged = edge_base.merge(edge_cand, on="regime", suffixes=("_base", "_cand"))
    for _, r in merged.iterrows():
        print(
            f"\n[{r['regime']}]  n {int(r['n_trades_base'])} -> {int(r['n_trades_cand'])}\n"
            f"  hit_rate     {100 * r['hit_rate_base']:6.2f}%  ->  {100 * r['hit_rate_cand']:6.2f}%\n"
            f"  break_even_p {100 * r['break_even_p_base']:6.2f}%  ->  {100 * r['break_even_p_cand']:6.2f}%\n"
            f"  margin       {100 * r['margin_base']:+6.2f} pp ->  {100 * r['margin_cand']:+6.2f} pp\n"
            f"  z_margin     {r['z_margin_base']:+6.2f}    ->  {r['z_margin_cand']:+6.2f}"
            f"   {'<<< SPEŁNIA kryterium (z>2)' if r['z_margin_cand'] > 2 else ''}"
        )

    passes = (merged["z_margin_cand"] > 2).any()
    improved = (
        candidate["classification"]["classification"] != baseline["classification"]["classification"]
    )
    print(
        f"\n[kryterium] z_margin > 2 w co najmniej jednym reżimie: {passes}\n"
        f"[kryterium] zmiana klasyfikacji: {improved} "
        f"({baseline['classification']['classification']} -> "
        f"{candidate['classification']['classification']})\n"
        "[uwaga] Skrypt NIE wybiera zwycięzcy — decyzja przy użytkowniku (konwencja runs/)."
    )


if __name__ == "__main__":
    main()
