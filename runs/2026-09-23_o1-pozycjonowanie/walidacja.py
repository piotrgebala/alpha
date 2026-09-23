"""Walidacja O1 drugą drogą (bramka 16a). Uruchomienie: PYTHONPATH=. PYTHONUTF8=1 py runs/.../walidacja.py

Liczy trafność i średni zwrot netto ramienia O1 wprost z journalu (numpy, bez summarize_trade_returns),
sprawdza populację świec, brak lookaheadu dopięcia na REALNYCH danych (snapshoty przesunięte w przód
zmieniają cechę; snapshoty o `open + 4h` nie są używane) i redundancję z wolumenem.
"""

import numpy as np
import pandas as pd
import yaml

from agents.positioning_features import (
    SNAPSHOT_OFFSET,
    attach_positioning,
    compute_positioning_features,
    load_metrics,
)
from backtest.checkpoint_lib import fetch_window, load_config
from backtest.run_positioning_o1 import O1_FEATURES, _collect, _simulate

data_cfg = load_config()["data"]
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
df = fetch_window(data_cfg, "4h")
metrics = load_metrics()
raw = compute_positioning_features(attach_positioning(df, metrics))

print("== A. dopięcie bez lookaheadu na realnych danych ==")
m_shift = metrics.copy()
m_shift["timestamp"] = m_shift["timestamp"] + pd.Timedelta(hours=4)
raw_shift = compute_positioning_features(attach_positioning(df, m_shift))
diff = (raw["oi_close"] - raw_shift["oi_close"]).abs()
print(
    f"  snapshoty przesunięte o +4h zmieniają oi_close w {int((diff > 0).sum())} z {len(df)} świec "
    f"(mediana |Δ| {diff.median():.1f} BTC) — użyta wersja bierze odczyty z wnętrza świecy"
)
# odczyt dokładnie o open+4h: podmieniamy wartość w metrics dla znaczników równych zamknięciom świec
closes = set(pd.to_datetime(df["timestamp"], utc=True) + pd.Timedelta(hours=4))
m_boundary = metrics.copy()
mask = m_boundary["timestamp"].isin(closes)
m_boundary.loc[mask, "oi"] = m_boundary.loc[mask, "oi"] * 10.0
raw_b = compute_positioning_features(attach_positioning(df, m_boundary))
print(
    f"  podmiana odczytów o open+4h (×10) zmienia oi_close w {int((~((raw_b['oi_close'] == raw['oi_close']) | (raw_b['oi_close'].isna() & raw['oi_close'].isna()))).sum())} świec "
    f"(oczekiwane 0: odczyt graniczny należy do następnej świecy i nie jest jej ostatnim odczytem wewnętrznym)"
)
print(f"  offset użyty: {SNAPSHOT_OFFSET}; świec bez odczytu wewnętrznego: {int(raw['oi_close'].isna().sum())}")

print("== B. O1 wprost z journalu (numpy) ==")
o1_c = _collect(raw, O1_FEATURES, rule)
o1 = _simulate(o1_c["df"], o1_c["candidate_signals"], o1_c["folds_summary"])
real = o1["real"]
p = float((real["gross_ret"] > 0).mean())
r = real["net_ret"].to_numpy(dtype=float)
se = r.std(ddof=1) / np.sqrt(len(r))
print(
    f"  n {len(real)}; p = {100 * p:.2f}% (skrypt: {100 * o1['p']:.2f}%); r̄ netto {100 * r.mean():+.4f}% "
    f"(skrypt {100 * o1['r_mean']:+.4f}%), t (bez N_eff) {r.mean() / se:+.2f}; mediana {100 * np.median(r):+.4f}%"
)
w = real.loc[real["gross_ret"] > 0, "gross_ret"].mean()
losses = -real.loc[real["gross_ret"] <= 0, "gross_ret"].mean()
c = float((real["gross_ret"] - real["net_ret"]).mean())
print(f"  p* = (L̄ + C)/(W̄ + L̄) = ({100 * losses:.4f} + {100 * c:.4f})/({100 * w:.4f} + {100 * losses:.4f}) = {100 * (losses + c) / (w + losses):.2f}% (skrypt {100 * o1['p_star']:.2f}%)")

print("== C. kogo nie ma ==")
fdf = o1_c["df"]
folds = o1_c["folds_summary"]
first_oos = min(f["test_start"] for f in folds if not f["skipped"])
oos = fdf[fdf["timestamp"] >= first_oos]
print(
    f"  świec OOS {len(oos)}; z NaN cechy oi_change_24h {int(oos['oi_change_24h'].isna().sum())}; "
    f"z NaN etykiety {int(oos['label'].isna().sum()) if 'label' in oos.columns else 'n/d'}; "
    f"korelacja oi_change_24h z volume_zscore_20 {fdf['oi_change_24h'].corr(fdf['volume_zscore_20']):+.3f}, "
    f"z return_lag_1 {fdf['oi_change_24h'].corr(fdf['return_lag_1']):+.3f}, z rsi_14 {fdf['oi_change_24h'].corr(fdf['rsi_14']):+.3f}"
)
print("== D. rozkład cechy w OOS (kwantyle %) ==")
q = oos["oi_change_24h"].quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
print("  " + ", ".join(f"p{int(100 * k):02d} {100 * v:+.2f}" for k, v in q.items()))
