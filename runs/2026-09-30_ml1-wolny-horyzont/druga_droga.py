"""Druga droga kluczowych liczb ML1 — bez agents/ml1_features i bez agents/labeling (niezależnie)."""

import json

import numpy as np
import pandas as pd
import talib

R = "runs/2026-09-30_ml1-wolny-horyzont"
sig = pd.read_csv(f"{R}/sygnaly_oos_wf.csv", parse_dates=["timestamp"])
thr = json.load(open(f"{R}/wf_prog.json"))["threshold"]

# 1. próg: ręczna interpolacja liniowa kwantyla 0,80
c = np.sort(sig["signal_confidence"].to_numpy())
pos = 0.8 * (len(c) - 1)
lo = int(np.floor(pos))
thr2 = c[lo] + (pos - lo) * (c[lo + 1] - c[lo])
print(f"1. próg: skrypt {thr:.9f}, ręcznie {thr2:.9f}, różnica {abs(thr - thr2):.2e}")

# 2. trafność od zera z surowych świec (własna pętla barier, ATR z TA-Lib)
o = pd.read_parquet("data/raw/ml1/BTC-USDT-USDT_1d_20190910T000000Z_20260930T000000Z.parquet")
o = o[(o["timestamp"] >= "2021-01-01") & (o["timestamp"] <= "2025-12-31")].reset_index(drop=True)
atr = talib.ATR(o["high"].values, o["low"].values, o["close"].values, timeperiod=14)
pos_of = {t: i for i, t in enumerate(pd.to_datetime(o["timestamp"], utc=True))}
hits = []
for _, s in sig.iterrows():
    i = pos_of[pd.Timestamp(s["timestamp"]).tz_convert("UTC")]
    e = o["close"].iat[i]
    up, dn = e + 1.5 * atr[i], e - 1.5 * atr[i]
    res = None
    for k in range(i + 1, i + 8):
        hu, hd = o["high"].iat[k] >= up, o["low"].iat[k] <= dn
        if hu and hd:
            res = 1.0 if (up - o["open"].iat[k]) <= (o["open"].iat[k] - dn) else -1.0
            break
        if hu or hd:
            res = 1.0 if hu else -1.0
            break
    if res is None:
        res = np.sign(o["close"].iat[i + 7] - e)
    hits.append(res * s["signal_direction"] > 0)
hits = np.array(hits)
print(
    f"2. zgodność trafienia sygnału (niezależna pętla vs skrypt): {int((hits == sig['hit'].to_numpy()).sum())}/{len(sig)}"
)
top = sig["signal_confidence"] >= thr2
print(
    f"   trafność wszystkie {100 * hits.mean():.2f} % (n {len(hits)}); ponad progiem {100 * hits[top].mean():.2f} % (n {int(top.sum())})"
)
srt = np.argsort(sig["signal_confidence"].to_numpy(), kind="stable")
for b in range(5):
    idx = srt[b * 182 : (b + 1) * 182]
    print(f"   kubełek {b + 1}: trafność {100 * hits[idx].mean():.2f} %")


# 3. przedziały z poprawką na nakładanie: liczba NIENAKŁADAJĄCYCH się sygnałów (odstęp ≥ 7 dni)
def nonoverlap(ts: pd.Series) -> int:
    n, last = 0, None
    for t in ts.sort_values():
        if last is None or (t - last).days >= 7:
            n += 1
            last = t
    return n


print("3. ±Wald z n nienakładających się sygnałów (odstęp ≥ 7 dni) — przybliżenie N_eff")
for name, m in (("wszystkie", np.ones(len(sig), bool)), ("ponad progiem", top.to_numpy())):
    ne = nonoverlap(sig.loc[m, "timestamp"])
    p = hits[m].mean()
    print(
        f"   {name}: n {int(m.sum())}, nienakładające się {ne}, trafność {100 * p:.2f} % ±{100 * 1.96 * np.sqrt(p * (1 - p) / ne):.1f} pp"
    )
for b in range(5):
    idx = srt[b * 182 : (b + 1) * 182]
    ne = nonoverlap(sig["timestamp"].iloc[idx])
    p = hits[idx].mean()
    print(
        f"   kubełek {b + 1}: nienakładające się {ne}, ±{100 * 1.96 * np.sqrt(p * (1 - p) / ne):.1f} pp"
    )

# 4. rozbieg z CSV
rz = pd.read_csv(f"{R}/sygnaly_rozbieg_2026.csv")
d = rz["signal_direction"]
print(
    f"4. rozbieg z CSV: świec {len(rz)}, long {int((d > 0).sum())}, short {int((d < 0).sum())}, "
    f"zero {int((d == 0).sum())}, ponad progiem {int(((d != 0) & (rz['signal_confidence'] >= thr)).sum())}"
)
