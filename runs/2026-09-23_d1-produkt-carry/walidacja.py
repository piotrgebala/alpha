import pandas as pd, numpy as np
from backtest import carry_product as cp
START, END = "2021-01-01", "2026-07-01"
perp = pd.read_parquet("data/raw/BTC-USDT-USDT_8h_20210101T000000Z_20260701T000000Z.parquet")
print("== A. likwidacje po cenach HIGH (zamiast close) dla konfiguracji z 0 likwidacji po close ==")
for m, rd in ((1.0, 30), (0.5, 7), (0.25, 1), (1.5, 30)):
    ev_c = cp.liquidation_events(perp["close"], m, rd * 3)
    ev_h = cp.liquidation_events(perp["high"], m, rd * 3)
    print(f"  M={m:.2f} reset {rd:2d} d: close → likw. {ev_c['n_liquidations']}, max wyk. {100*ev_c['max_usage']:.1f}% | high → likw. {ev_h['n_liquidations']}, max wyk. {100*ev_h['max_usage']:.1f}%")
print("== B. run-up 30 dni z close vs C1 (+90 %): ==", round(100*cp.forward_runup(perp['close'], 90).max(), 1), "%")
print("== C. COIN-M: suma fundingu 2021→2026-07 drugą drogą ==")
cm = pd.read_parquet("data/raw/external/binance_cm_funding_BTCUSD_PERP.parquet")
cm["timestamp"] = cp.floor_to_grid(cm["timestamp"]); cm = cm.drop_duplicates("timestamp")
w = cm[(cm["timestamp"] >= START) & (cm["timestamp"] < END)]
tot = w["funding_rate"].sum(); n = len(w); yrs = n / 1095
print(f"  n {n}, Σ funding {100*tot:.2f}% nominału, − koszty 0,38% = {100*(tot-0.0038):.2f}%; /{yrs:.2f} roku = {100*(tot-0.0038)/yrs:.2f}%/rok (skrypt: 9,07%)")
um = pd.read_parquet("data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet")
u = um[(um["timestamp"] >= START) & (um["timestamp"] < END)]
print(f"  USDT-M: n {len(u)}, Σ {100*u['funding_rate'].sum():.2f}% → {100*(u['funding_rate'].sum()-0.0038)/(len(u)/1095):.2f}%/rok (skrypt 10,89%); różnica sum/rok {100*((w['funding_rate'].sum()-u['funding_rate'].sum())/yrs):+.2f}% (skrypt −1,82%)")
print("  N_eff z samej autokorelacji lag-1 (proxy pre-rejestracji) vs kanoniczny:")
from agents.labeling import effective_sample_size
rho = w["funding_rate"].autocorr(1); print(f"  acf1 {rho:.3f} → n(1−ρ)/(1+ρ) = {n*(1-rho)/(1+rho):.0f}; effective_sample_size → {effective_sample_size(w['funding_rate'].reset_index(drop=True))['n_eff']:.0f}")
print("== D. T-bill: średnie roczne DTB3 drugą drogą (mediana zamiast średniej) ==")
fr = pd.read_parquet("data/raw/external/fred_DTB3_1d.parquet"); fr = fr[(fr["date"] >= START) & (fr["date"] < END)]
print((fr.groupby(fr["date"].dt.year)["value"].agg(["mean", "median", "count"])).round(2).to_string())
print("== E. basis: front 2024 mediana z niezależnego rachunku (perp jako S zamiast spot) ==")
d = pd.read_parquet("data/raw/external/binance_um_dated_BTCUSDT_8h.parquet")
b = cp.annualized_basis(d, perp.rename(columns={"timestamp": "timestamp"}))
f = cp.front_contract(b); print(f"  front n {len(f)}; mediana 2024 z perp jako S: {100*f[f['open_time'].dt.year==2024]['annualized'].median():.2f}% (skrypt ze spot: 11,23%); razem {100*f['annualized'].median():.2f}% (5,88%)")
print("== F. kogo nie ma: świece kontraktów odrzucone filtrem ==")
d["delivery"] = pd.to_datetime(d["expiry"], utc=True) + pd.Timedelta(hours=8)
print(f"  wszystkich {len(d)}, po wygaśnięciu {int((d['open_time'] >= d['delivery']).sum())}, wolumen 0 {int((d['volume'] == 0).sum())}, < 7 dni do wygaśnięcia {int(((d['delivery'] - d['open_time']).dt.total_seconds()/86400 < 7).sum())}, po 2026-07-01 {int((d['open_time'] >= pd.Timestamp(END, tz='UTC')).sum())}")
