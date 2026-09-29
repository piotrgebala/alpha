"""Czy brak high/low 币安人生USDT w 2026-05 mógł zmienić wynik rund z likwidacją (tylko odczyt).

Pod zniekształconą nazwą silnik (`ts_momentum.portfolio` → `phase_returns_liq`) dostaje NaN
high/low → `nan_to_num(..., nan=1.0)` → pozycja nigdy nie jest likwidowana, a cel zysku (TP1) nigdy
nie jest trafiany. Tu: największy ruch przeciw pozycji w 7 dniach po każdym zamknięciu w 2026-05
(long: spadek do minimum low; short: wzrost do maksimum high) wobec progu likwidacji
1/dźwignia − MMR (MMR 1 %: 2× → 49 %, 3× → 32,3 %) i największy ruch na korzyść wobec celów TP1.

    PYTHONUTF8=1 py zadania/024-dowody/ruch_maj.py data/raw/universe_ohlc_full/ohlc_1d.parquet
"""

import sys

import pandas as pd

o = pd.read_parquet(sys.argv[1])
o = o[o["symbol"] == "币安人生USDT"].copy()
o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
o = o.set_index("open_time").sort_index()
print(
    f"币安人生USDT w universe_ohlc_full: {len(o)} dni, {o.index.min().date()} … {o.index.max().date()}"
)
maj = o[(o.index >= "2026-05-01") & (o.index < "2026-06-01")]
rows = []
for t, c in maj["close"].items():
    okno = o[(o.index > t) & (o.index <= t + pd.Timedelta(days=7))]
    if okno.empty:
        continue
    rows.append(
        {
            "dzien": t.date(),
            "long_max_spadek": 1 - okno["low"].min() / c,
            "short_max_wzrost": okno["high"].max() / c - 1,
            "long_max_zysk": okno["high"].max() / c - 1,
            "short_max_zysk": 1 - okno["low"].min() / c,
            "dni_okna": len(okno),
        }
    )
r = pd.DataFrame(rows)
print(f"wejść (zamknięcia 2026-05 z ≥ 1 dniem okna): {len(r)}")
for kol in ("long_max_spadek", "short_max_wzrost", "long_max_zysk", "short_max_zysk"):
    print(f"  {kol}: max {100 * r[kol].max():.1f} %, mediana {100 * r[kol].median():.1f} %")
for lev in (2, 3):
    prog = 1 / lev - 0.01
    n_l = int((r["long_max_spadek"] >= prog).sum())
    n_s = int((r["short_max_wzrost"] >= prog).sum())
    print(
        f"  próg likwidacji {lev}× ({100 * prog:.1f} %): wejść long z przekroczeniem {n_l}, short {n_s}"
    )
for cel in (0.01, 0.02):
    n_l = int((r["long_max_zysk"] >= cel).sum())
    n_s = int((r["short_max_zysk"] >= cel).sum())
    print(
        f"  cel TP1 +{100 * cel:.0f} %: wejść long z trafieniem {n_l}/{len(r)}, short {n_s}/{len(r)}"
    )

# Strona pozycji trendu (ts_momentum.signal_sign: znak zwrotu z 28 dni; close = close z universe_full,
# równy co do bitu w 61/61 dniach — druga_droga.txt, sekcja B). Każdy dzień maja to dzień formowania
# którejś z 7 faz, więc sprawdzamy znak w każdym dniu.
znak = (o["close"] / o["close"].shift(28) - 1.0).apply(
    lambda x: (x > 0) - (x < 0) if x == x else None
)
zm = znak[(znak.index >= "2026-05-01") & (znak.index < "2026-06-01")]
print(f"znak trendu (28 dni) w dniach 2026-05: {dict(zm.value_counts(dropna=False))}")
po_dniu = r.set_index("dzien")
for d, s in zm.items():
    if s != 1:
        w = po_dniu.loc[d.date()] if d.date() in po_dniu.index else None
        ruch = (
            "brak okna"
            if w is None
            else f"short: max wzrost w 7 dniach {100 * w['short_max_wzrost']:.1f} %"
        )
        print(f"  {d.date()}: znak {s}; {ruch} (progi: 2× 49,0 %, 3× 32,3 %)")
