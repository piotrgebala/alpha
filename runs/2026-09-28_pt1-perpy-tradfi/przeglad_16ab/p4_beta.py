"""F — przedziały β weekendu: per instrument (n = weekendy) i per klasa (n efektywne = liczba zamknięć)."""
import numpy as np
import pandas as pd
from scipy import stats
z = pd.read_csv("runs/2026-09-28_pt1-perpy-tradfi/zamkniety_rynek.csv")
def ci(b, r2, n):
    se = abs(b) * np.sqrt((1 - r2) / (r2 * (n - 2)))
    return b - stats.t.ppf(.975, n - 2) * se, b + stats.t.ppf(.975, n - 2) * se, b - 1.96 * se, b + 1.96 * se
w = z[(z.klasa != "waluty") & (z.klasa != "BTC_kontrola") & (z.weekend_n >= 3)].copy()
print("per instrument (bez walut i BTC, n ≥ 3): β", round(w.weekend_beta.min(), 2), "–", round(w.weekend_beta.max(), 2),
      " R²", round(w.weekend_r2.min(), 2), "–", round(w.weekend_r2.max(), 2), " instrumentów", len(w))
print("  skrajne β:", w.nsmallest(3, "weekend_beta")[["gielda", "symbol", "weekend_n", "weekend_beta", "weekend_r2"]].round(3).to_string(index=False).replace("\n", " | "))
print("  najwyższe β:", w.nlargest(3, "weekend_beta")[["gielda", "symbol", "weekend_n", "weekend_beta", "weekend_r2"]].round(3).to_string(index=False).replace("\n", " | "))
w[["t_lo", "t_hi", "z_lo", "z_hi"]] = [ci(b, r, n) for b, r, n in zip(w.weekend_beta, w.weekend_r2, w.weekend_n)]
print("  instrumenty z CI(t) obejmującym 0,5:")
print(w[w.t_lo <= 0.5][["gielda", "symbol", "weekend_n", "weekend_beta", "weekend_r2", "t_lo", "t_hi", "z_lo", "z_hi"]].round(2).to_string(index=False))
# per klasa: MNK łączny z raportu (raw_output), n efektywne = liczba zamknięć
klasy = [  # gielda, klasa, n_par, zamkniec, beta, r2 — z raw_output.txt (tabela „P4 — per klasa”)
    ("bybit", "akcje", 101, 22, 0.979085, 0.574298), ("bybit", "ETF", 127, 21, 0.977811, 0.844608),
    ("bybit", "ETF_oblig", 20, 9, 1.040647, 0.766892), ("bybit", "surowce", 105, 29, 0.896521, 0.793849),
    ("binance", "akcje", 111, 33, 0.939341, 0.463261), ("binance", "ETF", 160, 28, 0.952942, 0.826859),
    ("binance", "ETF_oblig", 18, 9, 1.058558, 0.778104), ("binance", "surowce", 258, 42, 0.884581, 0.666841),
    ("bybit", "waluty", 9, 3, 0.035660, 0.018777)]
print("\nper klasa: β [95 % CI t, n = zamknięcia] (dla porównania CI przy n = pary)")
for g, k, n, nz, b, r2 in klasy:
    if nz < 4:
        print(f"  {g} {k}: β {b:.2f}, zamknięć {nz} — CI nieokreślony sensownie"); continue
    lo, hi, _, _ = ci(b, r2, nz); lo2, hi2, _, _ = ci(b, r2, n)
    print(f"  {g:8s} {k:10s} β {b:.2f} [{lo:.2f}; {hi:.2f}] (zamknięć {nz}); przy n = {n} par: [{lo2:.2f}; {hi2:.2f}]")
