import pandas as pd, numpy as np
pd.set_option("display.width", 200)
m = pd.read_parquet("data/raw/external/binance_metrics_BTCUSDT_5m.parquet").set_index("timestamp")
print("== A. rząd wielkości: 2213 plików × 288 =", 2213*288, "; wiersze", len(m), "; różnica", 2213*288-len(m), "(luki z profilu: 634)")
print("== B. NaN w top-trader ratio: kiedy? ==")
na = m["count_toptrader_long_short_ratio"].isna()
runs = (na != na.shift()).cumsum()
seg = m[na].groupby(runs[na]).apply(lambda g: pd.Series({"od": g.index.min(), "do": g.index.max(), "n": len(g)}))
print(seg.sort_values("n", ascending=False).head(8).to_string())
print("NaN w bazie 2021-01-01→2026-07-01:", int(na[(m.index >= "2021-01-01") & (m.index < "2026-07-01")].sum()))
print("== C. zera w OI: kiedy? ==")
z = m[m["sum_open_interest"] <= 0]
print("n zer", len(z), "od", z.index.min(), "do", z.index.max()); print(z.index.to_series().dt.date.value_counts().head(5).to_string())
print("== D. zgodność archiwum vs kolektor REST (1h) za wspólne dni ==")
pairs = [("openInterestHist", "sumOpenInterest", "sum_open_interest"),
         ("topLongShortAccountRatio", "longShortRatio", "count_toptrader_long_short_ratio"),
         ("topLongShortPositionRatio", "longShortRatio", "sum_toptrader_long_short_ratio"),
         ("globalLongShortAccountRatio", "longShortRatio", "count_long_short_ratio")]
for ep, col, mcol in pairs:
    r = pd.read_parquet(f"data/raw/positioning/BTCUSDT_{ep}_1h.parquet").set_index("timestamp")
    j = r[[col]].join(m[[mcol]], how="inner").dropna()
    rel = ((j[col] - j[mcol]).abs() / j[mcol].abs()).replace([np.inf], np.nan)
    print(f"{ep:32s} wspólnych {len(j):4d} ({j.index.min().date()}→{j.index.max().date()}), max |rel| {rel.max():.2e}, mediana {rel.median():.2e}, dokładnie równych {(rel==0).mean():.3f}")
print("== E. OI value vs OI × cena (spójność): mediana |OI_value/(OI×close) − 1| ==")
px = pd.read_parquet("data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet")
tcol = "timestamp" if "timestamp" in px.columns else "open_time"
px = px.set_index(tcol)["close"]
mm = m[["sum_open_interest", "sum_open_interest_value"]].join(px, how="inner")
ratio = mm["sum_open_interest_value"] / (mm["sum_open_interest"] * mm["close"])
print("n", len(mm), "mediana", round(float((ratio-1).abs().median()), 4), "p99", round(float((ratio-1).abs().quantile(0.99)), 4))
print("== F. kontrakty: świece PO wygaśnięciu i z zerowym wolumenem ==")
d = pd.read_parquet("data/raw/external/binance_um_dated_BTCUSDT_8h.parquet")
post = d[d["open_time"] >= d["expiry"]]
print("świec po expiry:", len(post), "z tego wolumen 0:", int((post["volume"] == 0).sum()), "; wszystkich z wolumenem 0:", int((d["volume"] == 0).sum()))
print("== G. COIN-M funding: rozrzut ms wokół siatki 8h ==")
f = pd.read_parquet("data/raw/external/binance_cm_funding_BTCUSD_PERP.parquet")
off = (f["timestamp"] - f["timestamp"].dt.floor("8h")).dt.total_seconds()
print("offset s: max", off.max(), "udział > 1 s:", float((off > 1).mean()), "; masa 0.0001:", float((f["funding_rate"] == 0.0001).mean()))
print("== H. DVOL: BTC pokrycie bazy od 2021-03-24 ==")
dv = pd.read_parquet("data/raw/external/deribit_dvol_BTC_1d.parquet")
print("dni w bazie:", int(((dv["date"] >= "2021-01-01") & (dv["date"] < "2026-07-01")).sum()), "/ 2007 dni bazy; od 2021-03-24 oczekiwane:", (pd.Timestamp("2026-07-01") - pd.Timestamp("2021-03-24")).days)
print("== I. CoinMetrics: braki per metryka w bazie ==")
cm = pd.read_parquet("data/raw/external/coinmetrics_btc_1d.parquet")
cmb = cm[(cm["date"] >= "2021-01-01") & (cm["date"] < "2026-07-01")]
print(cmb.isna().sum().to_string())
