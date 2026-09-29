"""PT1 — druga droga dla P3 (bramka 16a, komplet migawek): spread i koszt strony policzone wprost z surowych
migawek, bez modułów rundy. Sesja USA = 13:30–20:00 UTC (pn 2026-09-28, czas letni, dzień sesji NYSE).
Dodatkowo (16b): zakres median po pojedynczych migawkach, akcje wg regionu, `interestRate` Binance we wszystkich
migawkach (P2). Uruchom z katalogu repo:
`py runs/2026-09-28_pt1-perpy-tradfi/druga_droga_p3.py > runs/2026-09-28_pt1-perpy-tradfi/druga_droga_p3.txt`.
"""

import glob
import gzip
import json

import pandas as pd

root = "data/raw/tradfi_perps"
taker = {"bybit": 0.0275, "binance": 0.04}  # % nominału, oficjalne stawki TradFi
taker_std = {"bybit": 0.055, "binance": 0.05}  # standard (i BTCUSDT)
rdzen = json.load(open(f"{root}/rdzen.json", encoding="utf-8"))
spis = {
    g: pd.read_parquet(f"{root}/spis_{g}.parquet").set_index("symbol") for g in ("bybit", "binance")
}

wiersze, stopy = [], []
pliki = sorted(glob.glob(f"{root}/migawki/*.json.gz"))
for p in pliki:
    s = json.load(gzip.open(p, "rt", encoding="utf-8"))
    t = pd.Timestamp(s["czas_utc"])
    sesja = t.weekday() < 5 and "13:30" <= t.strftime("%H:%M") < "20:00"
    kw = [
        ("bybit", r["symbol"], r["bid1Price"], r["ask1Price"])
        for r in s["bybit_tickers"]["result"]["list"]
    ]
    kw += [("binance", r["symbol"], r["bidPrice"], r["askPrice"]) for r in s["binance_book"]]
    for g, sym, b, a in kw:
        if sym not in spis[g].index:
            continue
        b, a = float(b or 0), float(a or 0)
        sp = (a - b) / ((a + b) / 2) * 1e4 if b > 0 and a >= b else float("nan")
        wiersze.append({"g": g, "sym": sym, "t": t, "sesja": sesja, "sp": sp})
    stopy += [
        (r["symbol"], float(r["interestRate"]))
        for r in s["binance_premium"]
        if r["symbol"] in spis["binance"].index
    ]
m = pd.DataFrame(wiersze)
m["kl"] = [spis[g].at[s, "klasa"] for g, s in zip(m.g, m.sym, strict=True)]
m["btc"] = m.kl == "BTC_kontrola"
m["rdz"] = [s in rdzen[g] for g, s in zip(m.g, m.sym, strict=True)]
m["k"] = m.sp / 2 / 100 + [taker_std[g] if b else taker[g] for g, b in zip(m.g, m.btc, strict=True)]
print(
    f"migawki: {len(pliki)} ({m.t.min():%H:%M}–{m.t.max():%H:%M} UTC), w sesji USA: {m[m.sesja].t.nunique()}, poza: {m[~m.sesja].t.nunique()}"
)

inst = m.groupby(["g", "sym"]).sp.median().rename("sp").to_frame()
inst["sp_s"] = m[m.sesja].groupby(["g", "sym"]).sp.median()
inst["sp_p"] = m[~m.sesja].groupby(["g", "sym"]).sp.median()
inst = inst.reset_index()
inst["kl"] = [spis[g].at[s, "klasa"] for g, s in zip(inst.g, inst.sym, strict=True)]
inst["reg"] = [spis[g].at[s, "region"] for g, s in zip(inst.g, inst.sym, strict=True)]
inst["btc"] = inst.kl == "BTC_kontrola"
inst["rdz"] = [s in rdzen[g] for g, s in zip(inst.g, inst.sym, strict=True)]
for c in ("sp", "sp_s", "sp_p"):
    stawka = [taker_std[g] if b else taker[g] for g, b in zip(inst.g, inst.btc, strict=True)]
    inst["k" + c[2:]] = inst[c] / 2 / 100 + stawka
inst["k_std"] = inst.sp / 2 / 100 + inst.g.map(taker_std)

for g, d in inst[inst.rdz].groupby("g"):
    bez = d[~d.btc]
    nad = bez[bez.k > 0.07]
    print(
        f"{g:8s} rdzeń (z BTC, {len(d)}): spread {d.sp.median():.2f} pb, koszt strony {d.k.median():.4f} % "
        f"(w sesji {d.k_s.median():.4f}, poza {d.k_p.median():.4f}; stawka standard {d.k_std.median():.4f}) | "
        f"bez BTC ({len(bez)}): {bez.k.median():.4f} %, > 0,07 %: {len(nad)} — "
        + ", ".join(f"{s.replace('USDT', '')} {k:.3f}" for s, k in zip(nad.sym, nad.k, strict=True))
    )
for (g, kl), d in inst[~inst.btc].groupby(["g", "kl"]):
    print(
        f"{g:8s} {kl:10s} n={len(d):3d} spread med {d.sp.median():5.1f} (sesja {d.sp_s.median():5.1f}, "
        f"poza {d.sp_p.median():5.1f}) p90 {d.sp.quantile(0.9):5.1f} pb | koszt strony med {d.k.median():.4f} % "
        f"(sesja {d.k_s.median():.4f}, poza {d.k_p.median():.4f}) | udział > 0,07 %: {(d.k > 0.07).mean():.1%}"
    )
print("zakres po migawkach (16b) — mediana po instrumentach policzona osobno w każdej migawce:")
for g in ("bybit", "binance"):
    r = m[(m.g == g) & m.rdz].groupby("t").k.median()
    a = m[(m.g == g) & (m.kl == "akcje")].groupby("t").k.median()
    print(
        f"  {g:8s} rdzeń {r.min():.4f}–{r.max():.4f} %, akcje {a.min():.4f}–{a.max():.4f} % ({len(r)} migawek)"
    )
print("akcje wg regionu (giełda macierzysta akcji z HK/KR/CN zamknięta we wszystkich migawkach):")
for (g, azja), d in inst[inst.kl == "akcje"].groupby(["g", inst.reg != "US"]):
    print(
        f"  {g:8s} {'HK/KR/CN' if azja else 'USA':8s} n={len(d):3d} koszt strony med {d.k.median():.4f} % "
        f"(sesja {d.k_s.median():.4f}, poza {d.k_p.median():.4f}) | udział > 0,07 %: {(d.k > 0.07).mean():.1%}"
    )
st = pd.DataFrame(stopy, columns=["sym", "ir"])
st["kl"] = [spis["binance"].at[s, "klasa"] for s in st.sym]
print("interestRate Binance we wszystkich migawkach (klasa → wartość: liczba odczytów):")
for kl, d in st.groupby("kl"):
    print(f"  {kl:12s} {d.ir.round(10).value_counts().to_dict()}")
