"""G — ropa: korelacja dziennych zwrotów indeksu giełdy z FRED o każdej godzinie UTC (czas letni USA; zimą +1 h)."""
import numpy as np
import pandas as pd
R = "data/raw/tradfi_perps"
DST = [(pd.Timestamp("2025-03-09 07:00", tz="UTC"), pd.Timestamp("2025-11-02 06:00", tz="UTC")),
       (pd.Timestamp("2026-03-08 07:00", tz="UTC"), pd.Timestamp("2026-11-01 06:00", tz="UTC"))]
lato = lambda t: any(a <= t < b for a, b in DST)
def fred(s):
    d = pd.read_parquet(f"data/raw/external/fred_{s}_1d.parquet").dropna(subset=["value"])
    return pd.Series(d["value"].to_numpy(float), index=pd.DatetimeIndex(pd.to_datetime(d["date"], utc=True)).normalize())
for g in ("bybit", "binance"):
    ix = pd.read_parquet(f"{R}/swiece_{g}_index_1h.parquet")
    ix["czas"] = pd.to_datetime(ix["czas"], utc=True)
    for sym, ser in (("CLUSDT", "DCOILWTICO"), ("BZUSDT", "DCOILBRENTEU")):
        c = ix[ix.symbol == sym].set_index("czas")["close"].sort_index()
        f = fred(ser); f = f[(f.index >= c.index.min().normalize()) & (f.index <= c.index.max().normalize())]
        wyn = {}
        for h in range(24):
            koniec = [d + pd.Timedelta(hours=h) + (pd.Timedelta(0) if lato(d + pd.Timedelta(hours=h)) else pd.Timedelta(hours=1)) for d in f.index]
            p = pd.Series([c.get(t - pd.Timedelta(hours=1), np.nan) for t in koniec], index=f.index)
            raz = pd.DataFrame({"p": p, "f": f}).dropna()
            zw = np.log(raz).diff().dropna()
            wyn[h] = (zw.p.corr(zw.f), len(zw), (raz.p / raz.f - 1).median(), (raz.p / raz.f - 1).abs().median())
        t = pd.DataFrame(wyn, index=["kor", "n", "odch_med", "abs_odch_med"]).T
        best = t.kor.idxmax()
        print(f"{g} {sym}↔{ser}: 16:00 kor {t.loc[16,'kor']:.3f} (n {int(t.loc[16,'n'])}) | 19:00 kor {t.loc[19,'kor']:.3f} | "
              f"max {t.kor.max():.3f} o {best}:00 | poziom perp/FRED−1: mediana {t.loc[best,'odch_med']:+.2%} (|.| {t.loc[best,'abs_odch_med']:.2%}), "
              f"zakres median po godzinach {t.odch_med.min():+.2%} … {t.odch_med.max():+.2%}")
        print("   kor po godzinach:", " ".join(f"{h}:{v:.2f}" for h, v in t.kor.items()))
