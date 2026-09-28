"""C (Simpson) — ten sam instrument na wspólnym oknie: funding roczny Bybit vs Binance; B — średnie/mediany klas."""
import pandas as pd
R = "data/raw/tradfi_perps"
f = {"bybit": pd.read_parquet(f"{R}/funding_bybit.parquet"), "binance": pd.read_parquet(f"{R}/funding_binance.parquet")}
for g in f:
    f[g]["czas"] = pd.to_datetime(f[g]["czas"], utc=True).dt.floor("min")

def roczny(x, od, do):
    x = x[(x.czas > od) & (x.czas <= do)].sort_values("czas")
    lat = (do - od).total_seconds() / (365 * 86400)
    # dwie drogi: suma stawek / długość okna w latach oraz średnia × odczyty/rok (średni odstęp)
    sr_odst = (x.czas.iloc[-1] - x.czas.iloc[0]).total_seconds() / 3600 / (len(x) - 1)
    return x.fundingRate.sum() / lat * 100, x.fundingRate.mean() * 8760 / sr_odst * 100, len(x)

wsp = sorted(set(f["bybit"].symbol) & set(f["binance"].symbol) - {"BTCUSDT"})
print("wspólne symbole:", len(wsp))
rows = []
for s in wsp:
    a, b = f["bybit"][f["bybit"].symbol == s], f["binance"][f["binance"].symbol == s]
    od = max(a.czas.min(), b.czas.min()); do = min(a.czas.max(), b.czas.max())
    if (do - od).days < 20:
        continue
    ra, rb = roczny(a, od, do), roczny(b, od, do)
    rows.append({"symbol": s, "od": od.date(), "dni": (do - od).days, "bybit_suma": ra[0], "bybit_srxk": ra[1], "n_a": ra[2],
                 "binance_suma": rb[0], "binance_srxk": rb[1], "n_b": rb[2]})
t = pd.DataFrame(rows).set_index("symbol")
print(t.loc[[s for s in ["XAUUSDT", "XAGUSDT", "CLUSDT", "BZUSDT", "NVDAUSDT", "MUUSDT", "MSTRUSDT"] if s in t.index]].round(2).to_string())
t["roznica"] = t.bybit_suma - t.binance_suma
print("\nwszystkie wspólne (≥20 dni):", len(t), " |różnica| mediana", round(t.roznica.abs().median(), 2),
      " korelacja Bybit~Binance", round(t.bybit_suma.corr(t.binance_suma), 3))
print(t.sort_values("roznica").round(2).head(5).to_string()); print(t.sort_values("roznica").round(2).tail(5).to_string())

# pełne okna (funding.csv reportera) — mediany/średnie klas, pozostałe instrumenty
fc = pd.read_csv("runs/2026-09-28_pt1-perpy-tradfi/funding.csv")
print()
for (g, k), d in fc.groupby(["gielda", "klasa"]):
    v = d.f_rok.dropna()
    extra = "" if len(v) > 3 else "  wartości: " + ", ".join(f"{s.replace('USDT','')} {x:+.1f}" for s, x in zip(d.symbol, d.f_rok))
    print(f"{g:8s} {k:13s} n={len(v):3d} mediana={v.median():+6.2f} średnia={v.mean():+6.2f} p25={v.quantile(.25):+6.2f} p75={v.quantile(.75):+6.2f}{extra}")
print()
for s in ["NVDAUSDT", "MUUSDT", "MSTRUSDT", "XAUUSDT", "XAGUSDT", "CLUSDT", "BZUSDT"]:
    print(s, fc[fc.symbol == s][["gielda", "n", "pierwszy", "f_rok", "r_usd"]].round(2).to_string(header=False, index=False).replace("\n", " | "))
# r_USD (DFF) na oknie złota Bybit
dff = pd.read_parquet("data/raw/external/fred_DFF_1d.parquet")
print("DFF kolumny", list(dff.columns))
