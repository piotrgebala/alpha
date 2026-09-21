"""
run_checkpoint_v2.py

Commit 2.9 — kanoniczny checkpoint go/no-go v2, następca `run_checkpoint.py`
(który pozostaje w repo NIEZMIENIONY jako zamrożony zapis metodologii Commitu 6 —
jego wynik jest udokumentowany w IMPLEMENTATION_PLAN.md i musi pozostać odtwarzalny).
Skrypt jednorazowy/analityczny, poza pytest. Pierwszy użytkownik wspólnej biblioteki
`backtest/checkpoint_lib.py` (Z13).

CO SIĘ ZMIENIA względem v1 (pełne uzasadnienie: docs/rag/03, aktualizacja 2026-09-21,
oraz TASKS.md Backlog Z1–Z3):
  1. (Z1) Sweep stabilności po SEEDACH zastąpiony sweepem FOLD-JITTER (offset startu
     okien walk-forward 0..9 dni). Powód: XGBoost w konfiguracji Fazy 0 (bez
     subsample/colsample) jest deterministyczny — seed niczego nie zmieniał i każdy
     dotychczasowy "std=0,0000 (STABILNY)" mierzył dokładnie nic.
  2. (Z2) Per-fold `t_stat` (bez annualizacji) obok Sharpe'a + zbiorcza diagnostyka
     pooled per regime (wszystkie transakcje reżimu połączone między foldami:
     sharpe_per_trade, t_stat).
  3. (Z3) N_eff (efektywna liczba niezależnych obserwacji, autokorelacja zwrotów —
     agents.labeling.effective_sample_size, C4.4) wpięte do raportu po raz pierwszy,
     wraz z konserwatywnym t_stat_neff.

CO SIĘ NIE ZMIENIA: kryteria klasyfikacji GO/WARUNKOWY/NO-GO (docs/rag/03) — nowe
miary są DIAGNOSTYKĄ obok werdyktu, nie nowym werdyktem. Pipeline (run_backtest)
identyczny; offset=0 w sweepie to dokładnie kanoniczny przebieg, porównywalny 1:1
z wynikami C6/C2c/C2d/C2.5/C2.6/C2.8.

Użycie:
    py -m backtest.run_checkpoint_v2 --quick   # tylko kanoniczny przebieg (offset=0)
    py -m backtest.run_checkpoint_v2           # + pełny sweep fold-jitter (10 offsetów)
"""

from __future__ import annotations

import sys

from backtest.checkpoint_lib import (
    PRIMARY_SEED,
    fetch_data,
    load_config,
    print_stability_report,
    run_and_summarize,
    sweep_fold_offsets,
)


def main(quick: bool) -> None:
    cfg = load_config()
    raw_ohlcv = fetch_data(cfg)

    print(f"\n[seed={PRIMARY_SEED}] kanoniczny przebieg (offset=0)...")
    primary = run_and_summarize(raw_ohlcv, seed=PRIMARY_SEED)

    print(f"\n=== Sharpe + t-stat per fold (seed={PRIMARY_SEED}) ===")
    print(primary["fold_metrics"].to_string(index=False))

    print("\n=== Klasyfikacja (kryteria docs/rag/03, NIEZMIENIONE) ===")
    print(primary["classification"])

    print("\n=== Rozbicie per reżim ===")
    print(primary["per_regime"].to_string(index=False))

    print("\n=== Diagnostyka pooled per reżim (Commit 2.9/Z2+Z3) ===")
    print(primary["pooled_per_regime"].to_string(index=False))
    print(
        "[interpretacja] |t_stat| < ~2 => średni zwrot per trade nieodróżnialny od zera\n"
        "przy tej liczbie obserwacji; t_stat_neff dodatkowo koryguje za autokorelację."
    )

    if quick:
        print("\n[--quick] pomijam sweep fold-jitter.")
        return

    print("\n[sweep] fold-jitter: offsety startu okien walk-forward 0..9 dni")
    sweep = sweep_fold_offsets(raw_ohlcv, seed=PRIMARY_SEED)
    print_stability_report(sweep)


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
