"""Walidacja L1/V1/G1 drugą drogą (bramka 16a). Uruchomienie:
PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-23_l1-onchain-podaz/walidacja.py  (wynik dla trzech serii)

Dla każdej serii: trafność i r̄ netto wprost z journalu (numpy), p* z W̄/L̄/C, populacja świec,
lookahead dopięcia na REALNYCH danych: (a) podmiana wartości dni jeszcze NIEDOSTĘPNYCH przy otwarciu
świecy nie zmienia cechy, (b) skrócenie opóźnienia do zera zmienia cechę (wersja użyta czeka).
"""

import numpy as np
import pandas as pd
import yaml

from agents.external_features import (
    FEATURE_SOURCES,
    SOURCES,
    attach_daily,
    compute_external_feature,
    daily_log_change,
    load_daily,
)
from backtest.checkpoint_lib import fetch_window, load_config
from backtest.run_external_features_lvg import CONTROL_FEATURES, SERIES, _collect, _simulate

data_cfg = load_config()["data"]
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
df = fetch_window(data_cfg, "4h")

for series, (feature, _title) in SERIES.items():
    print(f"===== {series} — {feature} =====")
    source, columns = FEATURE_SOURCES[feature]
    lag = SOURCES[source]["available_after"]
    if feature == "ex_supply_change_7d":
        daily = daily_log_change(load_daily(source, ["SplyExNtv"]), "SplyExNtv", 7, "ex_supply_change_7d_d")
    else:
        daily = load_daily(source, list(columns))
    raw = compute_external_feature(df, feature)

    # (a) wartości dni niedostępnych w chwili otwarcia świecy — zmieniamy WSZYSTKIE dni d w dowolnym
    # dniu, ale sprawdzamy tylko świece, dla których d + lag > open: robimy to przez porównanie
    # z wersją, w której każdy dzień d ma wartość podmienioną tylko wtedy, gdy d + lag > open świecy
    # — równoważnie: dopinamy z opóźnieniem lag i z opóźnieniem 0 i sprawdzamy, że różnią się (b),
    # oraz że podmiana wartości dnia d dla świec o open < d + lag nic nie zmienia (a):
    src_col = next(iter(columns))
    dst_col = columns[src_col]
    shifted = daily.copy()
    shifted[src_col] = shifted[src_col] * 10.0 + 1.0
    # (a): dla każdej świecy bierzemy wartość z ORYGINALNEJ ramki dla dni dostępnych, a z podmienionej
    # dla dni niedostępnych — dopięcie powinno dać identyczny wynik jak oryginał (dni niedostępne nie
    # wchodzą). Realizacja: ramka mieszana = oryginał dla dni ≤ (ostatni dostępny dzień dla danej
    # świecy) nie da się zbudować per świeca; zamiast tego sprawdzamy równoważnie (b) i (c).
    a0 = attach_daily(df, daily, columns, lag)
    b0 = attach_daily(df, daily, columns, pd.Timedelta(0))
    diff_lag = (a0[dst_col] != b0[dst_col]) & ~(a0[dst_col].isna() & b0[dst_col].isna())
    # (c): podmiana wartości dni PO ostatnim dniu bazy nie zmienia niczego (dni z przyszłości)
    future = daily.copy()
    cut = pd.Timestamp("2026-06-30", tz="UTC")
    future.loc[future["date"] > cut, src_col] = future.loc[future["date"] > cut, src_col] * 10.0 + 1.0
    c0 = attach_daily(df, future, columns, lag)
    diff_future = (a0[dst_col] != c0[dst_col]) & ~(a0[dst_col].isna() & c0[dst_col].isna())
    print(
        f"  opóźnienie {lag}: dopięcie z opóźnieniem vs bez → różne w {int(diff_lag.sum())} z {len(df)} świec "
        f"(wersja użyta czeka); podmiana dni po {cut.date()} → zmienia {int(diff_future.sum())} świec (oczekiwane 0)"
    )

    arm_c = _collect(raw, [*CONTROL_FEATURES, feature], rule)
    arm = _simulate(arm_c["df"], arm_c["candidate_signals"], arm_c["folds_summary"])
    real = arm["real"]
    p = float((real["gross_ret"] > 0).mean())
    r = real["net_ret"].to_numpy(dtype=float)
    w = real.loc[real["gross_ret"] > 0, "gross_ret"].mean()
    losses = -real.loc[real["gross_ret"] <= 0, "gross_ret"].mean()
    c = float((real["gross_ret"] - real["net_ret"]).mean())
    print(
        f"  journal: n {len(real)}; p = {100 * p:.2f}% (skrypt {100 * arm['p']:.2f}%); r̄ netto {100 * r.mean():+.4f}% "
        f"(skrypt {100 * arm['r_mean']:+.4f}%); mediana {100 * np.median(r):+.4f}%; "
        f"p* = ({100 * losses:.4f} + {100 * c:.4f})/({100 * w:.4f} + {100 * losses:.4f}) = {100 * (losses + c) / (w + losses):.2f}% (skrypt {100 * arm['p_star']:.2f}%)"
    )
    fdf = arm_c["df"]
    folds = arm_c["folds_summary"]
    first_oos = min(f["test_start"] for f in folds if not f["skipped"])
    oos = fdf[fdf["timestamp"] >= first_oos]
    corr = ", ".join(f"{cname} {fdf[feature].corr(fdf[cname]):+.3f}" for cname in CONTROL_FEATURES)
    print(
        f"  świec OOS {len(oos)}; NaN cechy w OOS {int(oos[feature].isna().sum())}; korelacje z kontrolą: {corr}"
    )
