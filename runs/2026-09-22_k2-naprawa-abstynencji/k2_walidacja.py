"""
Walidacja wyniku K2 (CLAUDE.md zasada 16a) — druga, niezalezna droga.

1. Trafnosc bezwarunkowa A2 przy q=1 (65,65%) przeliczona z ROZKLADU ETYKIET,
   a nie z journalu: A2 wymusza kierunek na wszystkich swiecach, wiec
   p_bezwarunkowa = udzial_kierunkowych * 1,00 + udzial_timeoutow * p_na_timeoutach.
2. "Kogo NIE ma w zbiorze" — pelny lejek dla A0 i A2 na czystym szumie.
3. Czy A0 i A1 przy q=1 daja naprawde identyczny journal (podejrzanie rowne liczby).
"""
import numpy as np
import pandas as pd
import yaml

from agents.feature_miner import compute_all_features
from agents.labeling import compute_triple_barrier_labels
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.run_abstention_fix_k2 import ARMS, ORACLE, _oracle_seed
from backtest.run_positive_control_k1 import _inject_oracle

CFG = _load_cfg()
RULE = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
RAW = _load(CFG, "4h")
FEATS = compute_all_features(RAW, trend_threshold=RULE["trend_threshold"],
                             range_threshold=RULE["range_threshold"], candles_per_day=6)
LABELED = compute_triple_barrier_labels(FEATS, vertical_barrier_candles=3)
LABELS = LABELED["label"]
TS_LABEL = pd.Series(LABELED["label"].to_numpy(), index=FEATS["timestamp"].to_numpy())


def run(q, draw, arm):
    rng = np.random.default_rng(_oracle_seed(q, draw))
    df = RAW.copy()
    df[ORACLE] = _inject_oracle(LABELS, q, rng).reindex(df.index)
    return run_and_summarize(
        df, seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, [*REVERSION_FEATURES, ORACLE])],
        vertical_barrier_candles=3, candles_per_day=6, candle_minutes=240,
        train_days=60, test_days=28, step_days=28,
        trend_threshold=RULE["trend_threshold"], range_threshold=RULE["range_threshold"],
        **ARMS[arm])


print("=" * 100)
print("1. TRAFNOSC BEZWARUNKOWA A2 przy q=1 — przeliczona z ROZKLADU ETYKIET")
print("=" * 100)
res = run(1.0, 0, "A2")
tr = res["backtest"]["trades"]
tr = tr.loc[~tr["kill_switch_active"]].copy()
tr["etykieta"] = tr["timestamp"].map(TS_LABEL)
kier = tr.loc[tr["etykieta"].notna() & (tr["etykieta"] != 0.0)]
tmo = tr.loc[tr["etykieta"] == 0.0]

p_kier = float((kier["gross_pnl"] > 0).mean())
p_tmo = float((tmo["gross_pnl"] > 0).mean())
udzial_kier = len(kier) / len(tr)
przewidziane = udzial_kier * p_kier + (1 - udzial_kier) * p_tmo
zmierzone = float((tr["gross_pnl"] > 0).mean())

print(f"  n_all               = {len(tr)}")
print(f"  n(etykieta != 0)    = {len(kier)}  udzial = {100 * udzial_kier:.2f}%")
print(f"  n(etykieta == 0)    = {len(tmo)}   udzial = {100 * (1 - udzial_kier):.2f}%")
print(f"  udzial timeoutow w ETYKIETACH (caly zbior) = {100 * float((LABELS == 0.0).mean()):.2f}%")
print(f"    -> zgodnosc udzialow: {100 * (1 - udzial_kier):.2f}% vs {100 * float((LABELS == 0.0).mean()):.2f}%")
print(f"  trafnosc na swiecach kierunkowych = {100 * p_kier:.2f}%")
print(f"  trafnosc na swiecach timeout      = {100 * p_tmo:.2f}%  <- wymuszony kierunek tam,")
print("                                          gdzie poprawny kierunek NIE ISTNIEJE")
print(f"\n  PRZEWIDZIANE z rozkladu = {100 * przewidziane:.4f}%")
print(f"  ZMIERZONE w journalu    = {100 * zmierzone:.4f}%")
print(f"  >>> {'ZGODNE' if abs(przewidziane - zmierzone) < 1e-9 else 'ROZJAZD'}")

print("\n" + "=" * 100)
print("2. KOGO NIE MA W ZBIORZE — pelny lejek na czystym szumie (q=0, losowanie 0)")
print("=" * 100)
print(f"  {'ramie':>5} | {'ocenione':>9} | {'bez kier.':>10} | {'bramka':>8} | {'bramka':>8} | "
      f"{'sygnaly':>8} | {'stlumione':>10} | {'w probie':>9}")
print(f"  {'':>5} | {'swiece':>9} | {'(abstyn.)':>10} | {'pewnosci':>8} | {'kosztowa':>8} | "
      f"{'':>8} | {'kill-sw.':>10} | {'':>9}")
print("  " + "-" * 86)
for arm in ("A0", "A1", "A2"):
    r = run(0.0, 0, arm)
    folds = [f for f in r["backtest"]["folds_summary"] if not f["skipped"]]
    pominiete = len([f for f in r["backtest"]["folds_summary"] if f["skipped"]])
    t = r["backtest"]["trades"]
    s = lambda k: sum(f[k] for f in folds)
    print(f"  {arm:>5} | {s('n_rows_evaluated'):9d} | {s('n_signals_no_direction'):10d} | "
          f"{s('n_signals_confidence_gated'):8d} | {s('n_signals_cost_gated'):8d} | "
          f"{s('n_signals'):8d} | {int(t['kill_switch_active'].sum()):10d} | "
          f"{int((~t['kill_switch_active']).sum()):9d}")
    print(f"        (foldow pominietych: {pominiete} z {len(r['backtest']['folds_summary'])}; "
          f"bilans lejka domyka sie: "
          f"{s('n_rows_evaluated') == s('n_signals') + s('n_signals_no_direction') + s('n_signals_cost_gated') + s('n_signals_confidence_gated')})")

print("\n" + "=" * 100)
print("3. CZY A0 i A1 przy q=1 DAJA IDENTYCZNY JOURNAL? (podejrzanie rowne liczby)")
print("=" * 100)
a0 = run(1.0, 0, "A0")["backtest"]["trades"]
a1 = run(1.0, 0, "A1")["backtest"]["trades"]
print(f"  A0: {len(a0)} wierszy, A1: {len(a1)} wierszy")
print(f"  journale identyczne co do wartosci: {a0.equals(a1)}")
if not a0.equals(a1):
    roz = [c for c in a0.columns if not a0[c].equals(a1[c])]
    print(f"  kolumny, ktore sie roznia: {roz}")
