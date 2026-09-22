# -*- coding: utf-8 -*-
"""K1 walidacja: czy przy CZYSTYM SZUMIE aparat ma systematyczne obciazenie dodatnie?"""
import numpy as np, pandas as pd, yaml
from agents.feature_miner import compute_all_features
from agents.labeling import compute_triple_barrier_labels
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL

cfg = _load_cfg()
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
raw = _load(cfg, "4h")
feats = compute_all_features(raw, trend_threshold=rule["trend_threshold"],
                             range_threshold=rule["range_threshold"], candles_per_day=6)
labels = compute_triple_barrier_labels(feats, vertical_barrier_candles=3)["label"]

print("KONTROLA NEGATYWNA na 6 niezaleznych losowaniach czystego szumu")
print("=" * 78)
print(f"  {'seed':>5} | {'n':>5} | {'trafnosc':>8} | {'prog':>6} | {'margines':>9} | {'CI_low>prog':>11}")
print("  " + "-" * 62)
wyniki = []
for seed in range(6):
    rng = np.random.default_rng(7000 + seed)
    df = raw.copy()
    df["oracle"] = pd.Series(rng.choice([-1.0, 0.0, 1.0], size=len(labels)), index=labels.index).reindex(df.index)
    res = run_and_summarize(df, seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, [*REVERSION_FEATURES, "oracle"])],
        vertical_barrier_candles=3, candles_per_day=6, candle_minutes=240,
        train_days=60, test_days=28, step_days=28,
        trend_threshold=rule["trend_threshold"], range_threshold=rule["range_threshold"])
    e = res["edge_per_regime"]
    if not len(e):
        print(f"  {seed:5d} |     0 | brak transakcji"); continue
    r = e.iloc[0]
    przebil = r["ci_low"] > r["break_even_p"]
    wyniki.append((r["hit_rate"], r["margin"], przebil))
    print(f"  {seed:5d} | {int(r['n_trades']):5d} | {r['hit_rate']*100:7.2f}% | "
          f"{r['break_even_p']*100:5.2f}% | {r['margin']*100:+8.2f} pp | {str(przebil):>11}")

h = np.array([w[0] for w in wyniki]); m = np.array([w[1] for w in wyniki])
print()
print(f"  trafnosc: srednia {h.mean()*100:.2f}%, mediana {np.median(h)*100:.2f}%, "
      f"zakres [{h.min()*100:.2f}%; {h.max()*100:.2f}%]")
print(f"  margines: srednia {m.mean()*100:+.2f} pp, dodatnich {(m>0).sum()}/{len(m)}")
print(f"  kryterium PRE-REJESTROWANE (ci_low > prog) przebite: {sum(w[2] for w in wyniki)}/{len(wyniki)}")
print()
print("  ODCZYT: jesli srednia trafnosc ~50% i kryterium przebite 0/6 -> aparat NIE ma")
print("  obciazenia dodatniego, a pojedynczy odczyt 54% przy q=0 byl szumem przy n=50.")
