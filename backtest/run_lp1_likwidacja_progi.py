"""
run_lp1_likwidacja_progi.py — runda LP1 (zadanie 017): płaski próg likwidacji dziennika (1/L − 1 %)
wobec progów depozytu Binance (migawka freqtrade 84b4628) i ceny mark (archiwum markPriceKlines 1d).

0 wariantów, POZA licznikami. Liczy tylko progi i liczbę przekroczeń progu — NIE liczy zwrotu strategii.
Skrypt jest neutralnym reporterem; werdykt w `runs/2026-09-29_lp1-likwidacja-progi-binance/README.md`.

    # z katalogu głównego repo, po pobraniu danych:
    #   migawka progów → data/raw/binance_tiers/binance_leverage_tiers.json (sha256 w README)
    #   PYTHONUTF8=1 py -m data.fetch_mark_1d data/raw/universe_full
    PYTHONUTF8=1 py -m backtest.run_lp1_likwidacja_progi \
        [--universe-dir data/raw/universe_full] \
        [--ohlc data/raw/universe_ohlc_full/ohlc_1d.parquet] \
        [--mark data/raw/mark_1d/mark_1d.parquet] \
        [--tiers data/raw/binance_tiers/binance_leverage_tiers.json] \
        [--out runs/2026-09-29_lp1-likwidacja-progi-binance]
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.liq_binance import (
    binance_distance,
    bracket,
    contingency,
    crossing_flags,
    flat_distance,
    flagged_cells,
    forward_extremes,
    load_tiers,
    tier_key,
)
from backtest.rebalance_premium import load_universe, monthly_members
from data.fetch_universe_ohlc import END, FIRST_MONTH

RUN_DIR = "runs/2026-09-29_lp1-likwidacja-progi-binance"
NOTIONALS = (1_000.0, 10_000.0, 100_000.0)
LEVERAGES = (2.0, 3.0)
FLAT_MMR = (
    0.01  # MMR dziennika (live_journal.MMR) — przepisany, NIE importowany (moduł poza łańcuchem)
)
STEP2_NOTIONAL = 10_000.0  # pre-rejestracja: próg Binance w kroku 2 przy N = 10 tys. USDT
HORIZONS = (1, 7)  # 1 dzień; 7 = trzymanie trendu TS1 (HOLD_DAYS)
SIDES = ((1, "long"), (-1, "short"))
DECISION_REL = 0.10  # pre-rejestracja: |różnica względna| ≥ 10 % przy h = 7 → rozważyć Poprawkę


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(df: pd.DataFrame) -> str:
    """Hash treści (niezależny od wersji parquet): posortowany CSV z 10 cyframi znaczącymi."""
    d = df.sort_values(["symbol", "open_time"]).reset_index(drop=True)
    text = d.to_csv(index=False, float_format="%.10g", date_format="%Y-%m-%d")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def members_by_month(universe_dir: str) -> dict[pd.Timestamp, list[str]]:
    _, volume = load_universe(universe_dir)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(FIRST_MONTH, END, freq="MS", tz="UTC") if m < end]
    return monthly_members(volume, months)


def pivots(ohlc: pd.DataFrame, cols: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    o = ohlc.copy()
    o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
    return {c: o.pivot(index="open_time", columns="symbol", values=c).sort_index() for c in cols}


def pct(x: float) -> str:
    return f"{100 * x:.3f}"


# --------------------------------------------------------------------------------------------------
# 0. Profil danych (data:explore-data) — archiwum mark wobec ceny ostatniej
# --------------------------------------------------------------------------------------------------


def profile(mark: pd.DataFrame, last: pd.DataFrame) -> None:
    print("\n=== 0. PROFIL DANYCH: markPriceKlines 1d wobec ceny ostatniej (klines 1d) ===")
    for name, d in (("mark", mark), ("last", last)):
        num = d[["open", "high", "low", "close"]]
        print(
            f"[{name}] wiersze {len(d)}, symbole {d['symbol'].nunique()}, "
            f"dni {pd.to_datetime(d['open_time']).dt.date.min()} … {pd.to_datetime(d['open_time']).dt.date.max()}, "
            f"duplikaty (symbol, dzień) {int(d.duplicated(['symbol', 'open_time']).sum())}, "
            f"NaN {int(num.isna().sum().sum())}, wartości ≤ 0 {int((num <= 0).sum().sum())}, "
            f"high < low {int((d['high'] < d['low']).sum())}, "
            f"high < max(open, close) {int((d['high'] < d[['open', 'close']].max(axis=1) - 1e-12).sum())}, "
            f"low > min(open, close) {int((d['low'] > d[['open', 'close']].min(axis=1) + 1e-12).sum())}"
        )
    key = ["symbol", "open_time"]
    j = last.merge(mark, on=key, how="outer", suffixes=("_l", "_m"), indicator=True)
    only_l = j[j["_merge"] == "left_only"]
    only_m = j[j["_merge"] == "right_only"]
    print(
        f"[pokrycie] wspólne (symbol, dzień): {int((j['_merge'] == 'both').sum())}; "
        f"tylko last: {len(only_l)}; tylko mark: {len(only_m)}"
    )
    if len(only_l):
        g = only_l.groupby("symbol")["open_time"].agg(["count", "min", "max"])
        for s, r in g.sort_values("count", ascending=False).iterrows():
            print(
                f"[pokrycie] tylko last: {s} {int(r['count'])} dni, {r['min'].date()} … {r['max'].date()}"
            )
    both = j[j["_merge"] == "both"]
    for col in ("close", "low", "high"):
        r = both[f"{col}_m"] / both[f"{col}_l"]
        q = r.quantile([0.0, 0.001, 0.01, 0.5, 0.99, 0.999, 1.0])
        print(
            f"[mark/last {col}] min {q.iloc[0]:.4f}  p0,1 {q.iloc[1]:.4f}  p1 {q.iloc[2]:.4f}  "
            f"mediana {q.iloc[3]:.5f}  p99 {q.iloc[4]:.4f}  p99,9 {q.iloc[5]:.4f}  max {q.iloc[6]:.4f}"
        )
    # knot ostatniej ceny głębszy niż mark: ile dni low_last < low_mark (i o ile)
    dl = both["low_l"] / both["low_m"] - 1.0
    dh = both["high_l"] / both["high_m"] - 1.0
    print(
        f"[knoty] low_last < low_mark: {int((dl < 0).sum())} z {len(both)} "
        f"(mediana różnicy w tych dniach {100 * dl[dl < 0].median():.3f} %); "
        f"high_last > high_mark: {int((dh > 0).sum())} (mediana {100 * dh[dh > 0].median():.3f} %)"
    )
    lr = np.log(both["low_l"] / both["low_m"]).abs()
    top = both.assign(lr=lr).nlargest(8, "lr")
    for _, r in top.iterrows():
        print(
            f"[knoty, największe |ln(low_last/low_mark)|] {r['symbol']} {r['open_time'].date()} "
            f"low_last {r['low_l']:.6g} low_mark {r['low_m']:.6g} close_last {r['close_l']:.6g}"
        )


# --------------------------------------------------------------------------------------------------
# 1. Progi per moneta
# --------------------------------------------------------------------------------------------------


def step1(members: dict, tiers: dict) -> tuple[pd.DataFrame, list[str]]:
    months_in = pd.Series(
        [s for syms in members.values() for s in syms], dtype=object
    ).value_counts()
    symbols = sorted(months_in.index, key=lambda s: (-months_in[s], s))
    print(
        "\n=== 1. PROGI DEPOZYTU BINANCE (migawka 2026-06-18) wobec płaskiego progu 1/L − 1 % ==="
    )
    print(
        f"monety w top-20 point-in-time (miesiące {FIRST_MONTH[:7]} … 2026-06): {len(symbols)}; "
        f"miesięcy: {len(members)}"
    )
    flat = {lev: flat_distance(lev, FLAT_MMR) for lev in LEVERAGES}
    print(
        "płaski próg dziennika: "
        + ", ".join(f"{int(lev)}× → {pct(v)} %" for lev, v in flat.items())
    )
    rows, missing = [], []
    for s in symbols:
        key = tier_key(s)
        if key not in tiers:
            missing.append(s)
            continue
        for n in NOTIONALS:
            t = bracket(tiers[key], n)
            row = {
                "symbol": s,
                "miesiace_top20": int(months_in[s]),
                "nominal": n,
                "mmr": t.mmr,
                "cum": t.cum,
                "max_lev_progu": t.max_lev,
            }
            for lev in LEVERAGES:
                for side, sname in SIDES:
                    d = binance_distance(lev, t.mmr, t.cum, n, side)
                    row[f"odl_{int(lev)}x_{sname}"] = d
                    row[f"roznica_pp_{int(lev)}x_{sname}"] = 100 * (d - flat[lev])
            rows.append(row)
    tab = pd.DataFrame(rows)
    print(
        f"BRAK W MIGAWCE (wycofane albo przemianowane; progów nie zgadujemy): {len(missing)} → "
        + ", ".join(f"{s}({int(months_in[s])} mies.)" for s in missing)
    )
    print(
        "\nkolumny: symbol | mies. w top-20 | nominał | MMR % | cum USDT | max dźwignia progu | "
        "odległość Binance % [2× long, 2× short, 3× long, 3× short] | różnica wobec płaskiego (pp)"
    )
    for _, r in tab.iterrows():
        d = [r[f"odl_{int(lev)}x_{sn}"] for lev in LEVERAGES for _, sn in SIDES]
        dd = [r[f"roznica_pp_{int(lev)}x_{sn}"] for lev in LEVERAGES for _, sn in SIDES]
        print(
            f"{r['symbol']:<16} {r['miesiace_top20']:>3} {int(r['nominal']):>7} "
            f"{100 * r['mmr']:>6.3f} {r['cum']:>9.1f} {r['max_lev_progu']:>5.0f} | "
            + " ".join(f"{100 * x:7.3f}" for x in d)
            + " | "
            + " ".join(f"{x:+6.2f}" for x in dd)
        )
    print(
        "\npodsumowanie: ile monet ma odległość Binance MNIEJSZĄ niż płaski próg "
        "(Binance likwiduje wcześniej → nasz model zaniża liczbę likwidacji)"
    )
    for n in NOTIONALS:
        sub = tab[tab["nominal"] == n]
        for lev in LEVERAGES:
            for _, sn in SIDES:
                x = sub[f"roznica_pp_{int(lev)}x_{sn}"]
                print(
                    f"  N={int(n):>6} {int(lev)}× {sn:<5}: mniejsza {int((x < -1e-9).sum()):>3}, "
                    f"większa {int((x > 1e-9).sum()):>3}, równa {int((x.abs() <= 1e-9).sum()):>3} "
                    f"z {len(x)}; różnica pp min {x.min():+.2f} mediana {x.median():+.2f} max {x.max():+.2f}"
                )
    return tab, missing


# --------------------------------------------------------------------------------------------------
# 2. Przekroczenia progu: ostatnia vs mark
# --------------------------------------------------------------------------------------------------


def member_mask(index: pd.DatetimeIndex, columns: pd.Index, members: dict) -> pd.DataFrame:
    mask = pd.DataFrame(False, index=index, columns=columns)
    for m, syms in members.items():
        rows = (index >= m) & (index < m + pd.offsets.MonthBegin(1))
        cols = [s for s in syms if s in columns]
        mask.loc[rows, cols] = True
    return mask


def step2(members: dict, tiers: dict, last: dict, mark: dict, out_dir: Path) -> dict:
    print("\n=== 2. PRZEKROCZENIA PROGU: ekstremum ceny ostatniej vs ceny mark ===")
    idx = last["close"].index
    cols = last["close"].columns
    mlow = mark["low"].reindex(index=idx, columns=cols)
    mhigh = mark["high"].reindex(index=idx, columns=cols)
    member = member_mask(idx, cols, members)
    has_tier = pd.Series({s: tier_key(s) in tiers for s in cols})
    thr_bin = {}
    for lev in LEVERAGES:
        for side, sn in SIDES:
            v = {}
            for s in cols:
                if has_tier[s]:
                    t = bracket(tiers[tier_key(s)], STEP2_NOTIONAL)
                    v[s] = binance_distance(lev, t.mmr, t.cum, STEP2_NOTIONAL, side)
            thr_bin[(lev, sn)] = pd.Series(v).reindex(cols)
    results, cell_rows = {}, []
    for h in HORIZONS:
        lo_l, hi_l = forward_extremes(last["low"], last["high"], h)
        lo_m, hi_m = forward_extremes(mlow, mhigh, h)
        entry = last["close"]
        base = member & entry.notna()
        ok_last = base & lo_l.notna() & hi_l.notna()
        valid = ok_last & lo_m.notna() & hi_m.notna()
        valid_t = valid.copy()
        valid_t.loc[:, ~has_tier.reindex(cols).to_numpy(dtype=bool)] = False
        print(f"\n--- okno h = {h} d ---")
        print(
            f"komórki (moneta, dzień wejścia) w koszyku z ceną wejścia: {int(base.to_numpy().sum())}; "
            f"bez pełnego okna ceny ostatniej: {int((base & ~ok_last).to_numpy().sum())}; "
            f"bez pełnego okna mark: {int((ok_last & ~valid).to_numpy().sum())}; "
            f"ważne: {int(valid.to_numpy().sum())}; ważne z progami Binance: {int(valid_t.to_numpy().sum())}"
        )
        for lev in LEVERAGES:
            flat = flat_distance(lev, FLAT_MMR)
            for side, sn in SIDES:
                tb = thr_bin[(lev, sn)]
                lf_l, sf_l = crossing_flags(entry, lo_l, hi_l, flat, flat)
                lf_m, sf_m = crossing_flags(entry, lo_m, hi_m, flat, flat)
                lb_l, sb_l = crossing_flags(entry, lo_l, hi_l, tb.fillna(np.inf), tb.fillna(np.inf))
                lb_m, sb_m = crossing_flags(entry, lo_m, hi_m, tb.fillna(np.inf), tb.fillna(np.inf))
                if side == 1:
                    f_l, f_m, b_l, b_m = lf_l, lf_m, lb_l, lb_m
                else:
                    f_l, f_m, b_l, b_m = sf_l, sf_m, sb_l, sb_m
                c_flat = contingency(f_l, f_m, valid)
                c_flat_t = contingency(f_l, f_m, valid_t)
                c_bin = contingency(b_l, b_m, valid_t)
                n_fl = c_flat_t["tylko_last"] + c_flat_t["oba"]
                n_fm = c_flat_t["tylko_mark"] + c_flat_t["oba"]
                n_bl = c_bin["tylko_last"] + c_bin["oba"]
                n_bm = c_bin["tylko_mark"] + c_bin["oba"]
                results[(h, lev, sn)] = {
                    "flat_all": c_flat,
                    "flat_t": c_flat_t,
                    "bin": c_bin,
                    "flat_last": n_fl,
                    "flat_mark": n_fm,
                    "bin_last": n_bl,
                    "bin_mark": n_bm,
                    "valid_t": int(valid_t.to_numpy().sum()),
                    "daily_fl": (f_l & valid_t).sum(axis=1),
                    "daily_bm": (b_m & valid_t).sum(axis=1),
                }
                print(
                    f"[h={h} {int(lev)}× {sn}] próg płaski {pct(flat)} %; próg Binance N=10 tys. "
                    f"mediana {pct(tb.median())} % (min {pct(tb.min())}, max {pct(tb.max())})"
                )
                for label, c, fl_a, fl_b in (
                    ("płaski, wszystkie monety", c_flat, f_l, f_m),
                    ("płaski, monety z progami", c_flat_t, f_l, f_m),
                    ("Binance N=10 tys.", c_bin, b_l, b_m),
                ):
                    v = valid if label.startswith("płaski, wszystkie") else valid_t
                    only_l = flagged_cells(fl_a & ~fl_b, v)
                    only_m = flagged_cells(fl_b & ~fl_a, v)
                    print(
                        f"    {label:<26} n={c['n']:>6}  tylko last {c['tylko_last']:>4} "
                        f"(monet {len({s for _, s in only_l}):>3}, dni {len({d for d, _ in only_l}):>3})  "
                        f"tylko mark {c['tylko_mark']:>4} (monet {len({s for _, s in only_m}):>3}, "
                        f"dni {len({d for d, _ in only_m}):>3})  oba {c['oba']:>4}  żaden {c['zaden']}"
                    )
                rel = (n_bm - n_fl) / n_fl if n_fl else float("nan")
                print(
                    f"    likwidacje na monetach z progami: dziennik (płaski, last) {n_fl}; "
                    f"Binance-próg z last {n_bl} (efekt progu {n_bl - n_fl:+d}); "
                    f"płaski z mark {n_fm} (efekt ceny {n_fm - n_fl:+d}); "
                    f"model Binance (Binance-próg, mark) {n_bm} → różnica {n_bm - n_fl:+d} "
                    f"({100 * rel:+.1f} %)"
                )
                # zapis komórek z jakimkolwiek przekroczeniem (audyt, druga droga)
                any_x = (f_l | f_m | b_l | b_m) & valid
                ext_l = lo_l if side == 1 else hi_l
                ext_m = lo_m if side == 1 else hi_m
                for d, s in flagged_cells(any_x, valid):
                    cell_rows.append(
                        {
                            "h": h,
                            "L": int(lev),
                            "strona": sn,
                            "dzien_wejscia": d.date().isoformat(),
                            "symbol": s,
                            "wejscie_close_last": entry.at[d, s],
                            "ekstremum_last": ext_l.at[d, s],
                            "ekstremum_mark": ext_m.at[d, s],
                            "prog_plaski": flat,
                            "prog_binance": tb.get(s, np.nan),
                            "plaski_last": bool(f_l.at[d, s]),
                            "plaski_mark": bool(f_m.at[d, s]),
                            "binance_last": bool(b_l.at[d, s]),
                            "binance_mark": bool(b_m.at[d, s]),
                            "z_progami": bool(has_tier[s]),
                        }
                    )
    cells = pd.DataFrame(cell_rows)
    cells.to_csv(out_dir / "przekroczenia.csv", index=False, float_format="%.10g")
    print(f"\nzapisano {len(cells)} komórek z przekroczeniem → {out_dir / 'przekroczenia.csv'}")
    return {
        "results": results,
        "member": member,
        "has_tier": has_tier,
        "thr_bin": thr_bin,
        "mlow": mlow,
        "mhigh": mhigh,
    }


def decision(results: dict) -> None:
    print("\n=== REGUŁA DECYZJI (pre-rejestracja): h = 7, long + short, monety z progami ===")
    for lev in LEVERAGES:
        fl = sum(results[(7, lev, sn)]["flat_last"] for _, sn in SIDES)
        bm = sum(results[(7, lev, sn)]["bin_mark"] for _, sn in SIDES)
        bl = sum(results[(7, lev, sn)]["bin_last"] for _, sn in SIDES)
        fm = sum(results[(7, lev, sn)]["flat_mark"] for _, sn in SIDES)
        rel = (bm - fl) / fl if fl else float("nan")
        n = results[(7, lev, "long")]["valid_t"]
        print(
            f"{int(lev)}×: dziennik (płaski, last) {fl}; Binance (próg, mark) {bm}; "
            f"różnica {bm - fl:+d} ({100 * rel:+.1f} %; próg decyzji ±{100 * DECISION_REL:.0f} %) "
            f"| rozkład: tylko próg {bl - fl:+d}, tylko cena {fm - fl:+d} | komórek (na stronę) {n}; "
            f"częstość dziennik {100 * fl / (2 * n):.3f} %, Binance {100 * bm / (2 * n):.3f} % pozycji-okien"
        )


def interval(results: dict, h: int = 7, n_boot: int = 10_000, seed: int = 20260929) -> None:
    """
    Bramka 16b: zakres dla wielkości z reguły decyzji. Bootstrap blokowy po MIESIĄCACH dnia wejścia
    (okna 7-dniowe nakładają się, a krach jednego dnia trafia do wielu komórek — pojedyncze komórki
    nie są niezależne), percentyle 2,5/97,5; obok rozkład po latach. Ziarno stałe (powtarzalność).
    """
    print(f"\n=== ZAKRES (bramka 16b): różnica względna Binance/mark wobec dziennika, h = {h} ===")
    rng = np.random.default_rng(seed)
    for lev in LEVERAGES:
        fl = sum(results[(h, lev, sn)]["daily_fl"] for _, sn in SIDES)
        bm = sum(results[(h, lev, sn)]["daily_bm"] for _, sn in SIDES)
        keep = fl.index >= pd.Timestamp(FIRST_MONTH, tz="UTC")  # tylko miesiące z koszykiem
        fl, bm = fl[keep], bm[keep]
        month = fl.index.tz_localize(None).to_period("M")
        m_fl = fl.groupby(month).sum().to_numpy(dtype=float)
        m_bm = bm.groupby(month).sum().to_numpy(dtype=float)
        k = len(m_fl)
        draws = rng.integers(0, k, size=(n_boot, k))
        s_fl, s_bm = m_fl[draws].sum(axis=1), m_bm[draws].sum(axis=1)
        rel = (s_bm - s_fl) / s_fl
        lo, med, hi = np.percentile(rel, [2.5, 50, 97.5])
        point = (m_bm.sum() - m_fl.sum()) / m_fl.sum()
        print(
            f"{int(lev)}×: punkt {100 * point:+.1f} %; bootstrap po {k} miesiącach: mediana "
            f"{100 * med:+.1f} %, 95 % [{100 * lo:+.1f}; {100 * hi:+.1f}] %; "
            f"P(|różnica| ≥ {100 * DECISION_REL:.0f} %) = "
            f"{100 * np.mean(np.abs(rel) >= DECISION_REL):.1f} %"
        )
        year = fl.index.year
        y_fl, y_bm = fl.groupby(year).sum(), bm.groupby(year).sum()
        parts = []
        for y in y_fl.index:
            if y_fl[y]:
                d = 100 * (y_bm[y] - y_fl[y]) / y_fl[y]
                parts.append(f"{y} {int(y_fl[y])}→{int(y_bm[y])} ({d:+.1f} %)")
            else:
                parts.append(f"{y} 0→{int(y_bm[y])}")
        print("    po latach (dziennik → Binance/mark): " + "; ".join(parts))


def posthoc(members: dict, tiers: dict, last: dict, s2: dict, h: int = 7) -> None:
    """
    POST HOC (dopisane po obejrzeniu wyniku, POZA regułą decyzji): (a) okna z zamrożoną ceną ostatnią
    (high == low w którymś dniu wejścia…t+h — handel wstrzymany/wycofanie, cena mark dalej żyje);
    (b) próg Binance przy N = 1 tys. i 100 tys. zamiast 10 tys.
    """
    print(f"\n=== POST HOC (poza regułą decyzji; h = {h}) ===")
    cols = last["close"].columns
    lo_l, hi_l = forward_extremes(last["low"], last["high"], h)
    lo_m, hi_m = forward_extremes(s2["mlow"], s2["mhigh"], h)
    entry = last["close"]
    frozen = (last["high"] == last["low"]).astype(float).where(last["high"].notna())
    frozen_win = frozen.rolling(h + 1, min_periods=1).max().shift(-h).fillna(0.0) > 0
    valid = s2["member"] & entry.notna() & lo_l.notna() & hi_l.notna() & lo_m.notna() & hi_m.notna()
    valid.loc[:, ~s2["has_tier"].reindex(cols).to_numpy(dtype=bool)] = False
    live = valid & ~frozen_win
    fr = flagged_cells(frozen_win, valid)
    print(
        f"(a) okna z zamrożoną ceną ostatnią: {len(fr)} komórek, monety: "
        + ", ".join(sorted({s for _, s in fr}))
    )
    for lev in LEVERAGES:
        flat = flat_distance(lev, FLAT_MMR)
        for n_not in (1_000.0, STEP2_NOTIONAL, 100_000.0):
            tot = {"fl": 0, "bm": 0, "fl_live": 0, "bm_live": 0, "bl_live": 0, "fm_live": 0}
            for side, sn in SIDES:
                v = {}
                for s in cols:
                    if tier_key(s) in tiers:
                        t = bracket(tiers[tier_key(s)], n_not)
                        v[s] = binance_distance(lev, t.mmr, t.cum, n_not, side)
                tb = pd.Series(v).reindex(cols).fillna(np.inf)
                f_l = crossing_flags(entry, lo_l, hi_l, flat, flat)[0 if side == 1 else 1]
                f_m = crossing_flags(entry, lo_m, hi_m, flat, flat)[0 if side == 1 else 1]
                b_l = crossing_flags(entry, lo_l, hi_l, tb, tb)[0 if side == 1 else 1]
                b_m = crossing_flags(entry, lo_m, hi_m, tb, tb)[0 if side == 1 else 1]
                cnt = lambda f, m: int((f & m).to_numpy().sum())  # noqa: E731
                tot["fl"] += cnt(f_l, valid)
                tot["bm"] += cnt(b_m, valid)
                tot["fl_live"] += cnt(f_l, live)
                tot["bm_live"] += cnt(b_m, live)
                tot["bl_live"] += cnt(b_l, live)
                tot["fm_live"] += cnt(f_m, live)
                print(
                    f"    {int(lev)}× N={int(n_not):>6} {sn:<5} bez zamrożonych: dziennik {cnt(f_l, live)}, "
                    f"Binance/last {cnt(b_l, live)}, płaski/mark {cnt(f_m, live)}, "
                    f"Binance/mark {cnt(b_m, live)}"
                )
            rel = (tot["bm"] - tot["fl"]) / tot["fl"]
            rel_live = (tot["bm_live"] - tot["fl_live"]) / tot["fl_live"]
            print(
                f"{int(lev)}× N={int(n_not):>6}: wszystkie okna — dziennik {tot['fl']}, Binance/mark {tot['bm']} "
                f"({100 * rel:+.1f} %) | bez zamrożonych — dziennik {tot['fl_live']}, Binance/mark "
                f"{tot['bm_live']} ({100 * rel_live:+.1f} %); efekt progu {tot['bl_live'] - tot['fl_live']:+d}, "
                f"efekt ceny {tot['fm_live'] - tot['fl_live']:+d}"
            )


def hand_cases(ohlc: pd.DataFrame, markdf: pd.DataFrame, tiers: dict, out_dir: Path) -> None:
    """Trzy przypadki do przeliczenia ręcznego (surowe wiersze, nie macierze)."""
    print("\n=== PRZYPADKI DO PRZELICZENIA RĘCZNEGO (surowe wiersze archiwów) ===")
    c = pd.read_csv(out_dir / "przekroczenia.csv")
    picks = [
        (
            "knot ceny ostatniej (tylko last, płaski próg)",
            c[
                (c.h == 1)
                & (c.L == 3)
                & (c.strona == "long")
                & c.plaski_last
                & ~c.plaski_mark
                & c.z_progami
            ],
        ),
        (
            "zamrożona cena ostatnia (tylko mark, płaski próg)",
            c[
                (c.h == 1)
                & (c.L == 2)
                & (c.strona == "long")
                & ~c.plaski_last
                & c.plaski_mark
                & c.z_progami
            ],
        ),
        (
            "efekt progu (Binance tak, płaski nie; cena ostatnia)",
            c[(c.h == 1) & (c.L == 3) & (c.strona == "short") & c.binance_last & ~c.plaski_last],
        ),
    ]
    for label, sub in picks:
        if sub.empty:
            print(f"[{label}] brak komórki")
            continue
        r = sub.sort_values(["dzien_wejscia", "symbol"]).iloc[0]
        d0 = pd.Timestamp(r["dzien_wejscia"], tz="UTC")
        d1 = d0 + pd.Timedelta(days=1)
        lrow = ohlc[(ohlc.symbol == r.symbol) & ohlc.open_time.isin([d0, d1])]
        mrow = markdf[(markdf.symbol == r.symbol) & (markdf.open_time == d1)]
        t = bracket(tiers[tier_key(r.symbol)], STEP2_NOTIONAL)
        print(
            f"[{label}] {r.symbol}, wejście {d0.date()} (L={r.L}, {r.strona}); MMR {t.mmr}, cum {t.cum}"
        )
        for _, x in lrow.iterrows():
            print(
                f"    last {x.open_time.date()}: open {x.open:.8g} high {x.high:.8g} low {x.low:.8g} close {x.close:.8g}"
            )
        for _, x in mrow.iterrows():
            print(
                f"    mark {x.open_time.date()}: open {x.open:.8g} high {x.high:.8g} low {x.low:.8g} close {x.close:.8g}"
            )
        print(
            f"    progi: płaski {r.prog_plaski:.6f}, Binance {r.prog_binance:.6f}; flagi: płaski/last "
            f"{r.plaski_last}, płaski/mark {r.plaski_mark}, Binance/last {r.binance_last}, "
            f"Binance/mark {r.binance_mark}"
        )


# --------------------------------------------------------------------------------------------------
# Druga droga: pętla po wierszach długiego formatu (bez forward_extremes / crossing_flags / macierzy)
# --------------------------------------------------------------------------------------------------


def second_path(
    ohlc: pd.DataFrame, markdf: pd.DataFrame, members: dict, tiers: dict, h: int, lev: float
) -> dict[str, int]:
    mem = {(m.year, m.month): set(syms) for m, syms in members.items()}
    L = {}
    for r in ohlc.itertuples(index=False):
        L[(r.symbol, pd.Timestamp(r.open_time).date())] = (r.low, r.high, r.close)
    M = {}
    for r in markdf.itertuples(index=False):
        M[(r.symbol, pd.Timestamp(r.open_time).date())] = (r.low, r.high)
    flat = 1.0 / lev - FLAT_MMR
    cnt = {"flat_last": 0, "bin_mark": 0}
    one = pd.Timedelta(days=1)
    for (s, d), (_, _, entry) in L.items():
        if s not in mem.get((d.year, d.month), set()) or tier_key(s) not in tiers:
            continue
        days = [d + one * k for k in range(1, h + 1)]
        if not all((s, x) in L and (s, x) in M for x in days):
            continue
        low_l = min(L[(s, x)][0] for x in days)
        high_l = max(L[(s, x)][1] for x in days)
        low_m = min(M[(s, x)][0] for x in days)
        high_m = max(M[(s, x)][1] for x in days)
        t = [x for x in tiers[tier_key(s)] if x.floor <= STEP2_NOTIONAL < x.cap][0]
        core = 1.0 / lev + t.cum / STEP2_NOTIONAL - t.mmr
        thr_long, thr_short = core / (1.0 - t.mmr), core / (1.0 + t.mmr)
        cnt["flat_last"] += int(low_l <= entry * (1 - flat)) + int(high_l >= entry * (1 + flat))
        cnt["bin_mark"] += int(low_m <= entry * (1 - thr_long)) + int(
            high_m >= entry * (1 + thr_short)
        )
    return cnt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe-dir", default="data/raw/universe_full")
    ap.add_argument("--ohlc", default="data/raw/universe_ohlc_full/ohlc_1d.parquet")
    ap.add_argument("--mark", default="data/raw/mark_1d/mark_1d.parquet")
    ap.add_argument("--tiers", default="data/raw/binance_tiers/binance_leverage_tiers.json")
    ap.add_argument("--out", default=RUN_DIR)
    a = ap.parse_args()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    lo = pd.Timestamp("2021-01-01", tz="UTC")  # zasada 20
    ohlc = pd.read_parquet(a.ohlc)
    ohlc["open_time"] = pd.to_datetime(ohlc["open_time"], utc=True)
    ohlc = ohlc[ohlc["open_time"] >= lo].reset_index(drop=True)
    markdf = pd.read_parquet(a.mark)
    markdf["open_time"] = pd.to_datetime(markdf["open_time"], utc=True)
    markdf = markdf[markdf["open_time"] >= lo].reset_index(drop=True)

    print("=== LP1 — likwidacja: płaski próg dziennika wobec progów Binance i ceny mark ===")
    print(f"sha256 migawki progów ({a.tiers}): {sha256_file(a.tiers)}")
    print(
        f"sha256 pliku mark ({a.mark}): {sha256_file(a.mark)}; treść (kanoniczny CSV): {canonical_hash(markdf)}"
    )
    print(
        f"sha256 pliku last ({a.ohlc}): {sha256_file(a.ohlc)}; treść (kanoniczny CSV): {canonical_hash(ohlc)}"
    )

    profile(markdf, ohlc)
    members = members_by_month(a.universe_dir)
    tiers = load_tiers(a.tiers)
    tab, _missing = step1(members, tiers)
    tab.to_csv(out_dir / "progi_per_moneta.csv", index=False, float_format="%.10g")
    print(f"zapisano → {out_dir / 'progi_per_moneta.csv'}")

    last = pivots(ohlc, ("close", "low", "high"))
    mark = pivots(markdf, ("low", "high"))
    s2 = step2(members, tiers, last, mark, out_dir)
    decision(s2["results"])
    interval(s2["results"])
    posthoc(members, tiers, last, s2)
    hand_cases(ohlc, markdf, tiers, out_dir)

    print("\n=== DRUGA DROGA (pętla po wierszach, bez funkcji macierzowych) ===")
    for h, lev in ((7, 2.0), (7, 3.0), (1, 3.0)):
        c = second_path(ohlc, markdf, members, tiers, h, lev)
        r = s2["results"]
        fl = sum(r[(h, lev, sn)]["flat_last"] for _, sn in SIDES)
        bm = sum(r[(h, lev, sn)]["bin_mark"] for _, sn in SIDES)
        ok = "ZGODNE" if (c["flat_last"], c["bin_mark"]) == (fl, bm) else "NIEZGODNE"
        print(
            f"h={h} {int(lev)}×: pętla płaski/last {c['flat_last']}, Binance/mark {c['bin_mark']} "
            f"| macierz {fl}, {bm} → {ok}"
        )


if __name__ == "__main__":
    main()
