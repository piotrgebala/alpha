import pandas as pd
R = "data/raw/tradfi_perps"
f = {"bybit": pd.read_parquet(f"{R}/funding_bybit.parquet"), "binance": pd.read_parquet(f"{R}/funding_binance.parquet")}
spis = {g: pd.read_parquet(f"{R}/spis_{g}.parquet").set_index("symbol") for g in f}
for g in f:
    f[g]["czas"] = pd.to_datetime(f[g]["czas"], utc=True).dt.floor("min")
fc = pd.read_csv("runs/2026-09-28_pt1-perpy-tradfi/funding.csv")
kl = fc[fc.gielda == "bybit"].set_index("symbol").klasa
def w(x, od, do, incl):
    m = (x.czas >= od) if incl else (x.czas > od)
    x = x[m & (x.czas <= do)]
    return x.fundingRate.sum() / ((do - od).total_seconds() / (365 * 86400)) * 100, len(x)
for s in ["XAUUSDT", "XAGUSDT", "NVDAUSDT", "MUUSDT", "MSTRUSDT", "CLUSDT"]:
    a, b = f["bybit"][f["bybit"].symbol == s], f["binance"][f["binance"].symbol == s]
    do = min(a.czas.max(), b.czas.max())
    out = []
    for nazwa, od in (("pierwszy odczyt", max(a.czas.min(), b.czas.min())),
                      ("start ze spisu", max(pd.Timestamp(spis["bybit"].loc[s, "start"]), pd.Timestamp(spis["binance"].loc[s, "start"])))):
        for incl in (False, True):
            ra, rb = w(a, od, do, incl), w(b, od, do, incl)
            out.append(f"{nazwa}{'≥' if incl else '>'}: {ra[0]:.2f} vs {rb[0]:.2f}")
    # średnia × nominalne odczyty/rok (interwał modalny)
    print(s, " | ".join(out))
# znak różnicy per klasa na wspólnym oknie
rows = []
for s in sorted(set(f["bybit"].symbol) & set(f["binance"].symbol) - {"BTCUSDT"}):
    a, b = f["bybit"][f["bybit"].symbol == s], f["binance"][f["binance"].symbol == s]
    od = max(a.czas.min(), b.czas.min()); do = min(a.czas.max(), b.czas.max())
    if (do - od).days < 20: continue
    rows.append({"symbol": s, "klasa": kl.get(s, "?"), "bybit": w(a, od, do, False)[0], "binance": w(b, od, do, False)[0]})
t = pd.DataFrame(rows); t["d"] = t.bybit - t.binance
print(t.groupby("klasa").agg(n=("d", "size"), med_bybit=("bybit", "median"), med_binance=("binance", "median"),
      med_roznicy=("d", "median"), sr_roznicy=("d", "mean"), med_abs=("d", lambda v: v.abs().median()),
      udz_abs_gt5=("d", lambda v: (v.abs() > 5).mean())).round(2).to_string())
print("wszystkie:", len(t), "med |d|", round(t.d.abs().median(), 2), "udział |d|>5:", round((t.d.abs() > 5).mean(), 3),
      ">10:", int((t.d.abs() > 10).sum()), "korelacja", round(t.bybit.corr(t.binance), 3))
print("|d|>10:", t[t.d.abs() > 10].sort_values("d")[["symbol", "klasa", "bybit", "binance"]].round(1).to_string(index=False))
