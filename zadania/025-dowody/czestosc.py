"""
Zadanie 025, część B — jak często moneta z koszyka top-20 była wstrzymana albo wycofana, GDY była w koszyku.
Opisowo, 0 wariantów, bez zwrotów strategii. Tylko dane lokalne od 2021-01-01 (zasada 20), tylko odczyt.

Skład: `rebalance_premium.monthly_members` — ta sama funkcja, której używa dziennik (`live_journal.py:238`, `:613`,
`:1388`) — na panelu obrotu archiwum `data/raw/universe_full` (685 kontraktów, też wycofane; panel rund RU1+),
okno i miesiące jak `run_universe_fix_ru1._members` / TS1: obrót od 2021-01-01, miesiące 2021-02 … 2026-06.
Dziennik liczy skład na `data/raw/live` (od 2025-06), którego nie da się użyć wstecz: `fetch_live` pobiera tylko
kontrakty TRADING, więc wycofanych tam nie ma (sekcja 5).

Zdarzenie w parze (moneta, miesiąc koszyka), okno W = [początek miesiąca, początek następnego):
- `koniec`     — ostatnia świeca monety L < 2026-06-30 (koniec archiwum) i L + 1 dzień ∈ W;
- `zamrożenie` — ≥ 3 kolejne dni z obrotem 0 albo open = high = low = close (OHLC z `universe_ohlc_full`),
                 seria przecina W;
- `dziura`     — dzień w W bez świecy monety, choć moneta ma świece przed nim i po nim.
Okno rozszerzone W+ = [m, m_nast + 7 dni) (pozycja z ostatniego formowania miesiąca żyje jeszcze 7 dni) — tylko opis.

Druga droga (sekcja 3): niezależna implementacja — każdy plik czytany osobno (bez pivotu), własny ranking top-20
(bez `monthly_members`), serie liczone pętlą po datach; porównanie list zdarzeń co do pary i rodzaju.
Trzecia, częściowa (sekcja 4): dni, w których cena ostatnia stoi (high = low), a cena mark się rusza (`mark_1d`, LP1).
`listings/events.csv` nie ma dat wycofania (tylko wejścia na giełdę) — nie nadaje się na drugą drogę.

    cd <repo> && PYTHONUTF8=1 PYTHONPATH=. .venv/bin/python zadania/025-dowody/czestosc.py [katalog data/raw]
"""

from __future__ import annotations

import math
import sys
from bisect import bisect_left
from collections import defaultdict
from pathlib import Path

import pandas as pd
from scipy.stats import beta

from backtest.rebalance_premium import eligible_symbols, load_universe, monthly_members

RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/dantey1/alpha/data/raw")
FULL = RAW / "universe_full"
OHLC = RAW / "universe_ohlc_full" / "ohlc_1d.parquet"
MARK = RAW / "mark_1d" / "mark_1d.parquet"
LO = pd.Timestamp("2021-01-01", tz="UTC")  # zasada 20
END = pd.Timestamp("2026-07-01", tz="UTC")
DATA_LAST = END - pd.Timedelta(days=1)
MONTHS = [m for m in pd.date_range(pd.Timestamp("2021-02-01", tz="UTC"), END, freq="MS") if m < END]
MIN_RUN = 3
EXT = pd.Timedelta(days=7)
DAY = pd.Timedelta(days=1)
SEP = "=" * 110
KNOWN = [
    ("FTTUSDT", "2022-11"),
    ("FTTUSDT", "2022-12"),
    ("LUNAUSDT", "2022-05"),
    ("ALPACAUSDT", "2025-05"),
]


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def clopper_pearson(k: int, n: int, a: float = 0.05) -> tuple[float, float]:
    lo = 0.0 if k == 0 else float(beta.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a / 2, k + 1, n - k))
    return lo, hi


def windows(m: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    nxt = m + pd.offsets.MonthBegin(1)
    return m, nxt


# ------------------------------------------------------------------ droga 1: panel + funkcja dziennika
def route1() -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    close, volume = load_universe(FULL)
    keep = (close.index >= LO) & (close.index < END)
    close, volume = close[keep], volume[keep]
    members = monthly_members(volume, MONTHS)
    o = pd.read_parquet(OHLC)
    o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
    piv = {
        c: o.pivot(index="open_time", columns="symbol", values=c).reindex(index=close.index)
        for c in ("open", "high", "low", "close")
    }
    syms = sorted({s for v in members.values() for s in v})
    rows = []
    for s in syms:
        c = close[s]
        present = c.notna()
        zero = (volume[s] == 0) & present
        if s in piv["open"].columns:
            op, hi, lw, cl = (piv[k][s] for k in ("open", "high", "low", "close"))
            flat = (op == hi) & (hi == lw) & (lw == cl) & present
        else:
            flat = pd.Series(False, index=c.index)
        flag = zero | flat
        grp = (~flag).cumsum()
        runs = []
        for _, g in flag[flag].groupby(grp[flag]):
            if len(g) >= MIN_RUN:
                runs.append((g.index[0], g.index[-1], len(g)))
        first, last = c.first_valid_index(), c.last_valid_index()
        inside = c.loc[first:last]
        gaps = list(inside.index[inside.isna()])
        normal = present & ~flag

        def last_normal(before: pd.Timestamp, normal: pd.Series = normal) -> pd.Timestamp | None:
            nm = normal[normal.index < before]
            nm = nm[nm]
            return nm.index[-1] if len(nm) else None

        for m in MONTHS:
            if s not in members[m]:
                continue
            a, b = windows(m)
            for w_end, scope in ((b, "W"), (b + EXT, "W+")):
                if last < DATA_LAST and a <= last + DAY < w_end:
                    rows.append(
                        (
                            s,
                            m,
                            scope,
                            "koniec",
                            last_normal(last + DAY),
                            last,
                            None,
                            zero.loc[last] | flat.loc[last],
                        )
                    )
                for r0, r1, n in runs:
                    if r0 < w_end and r1 >= a:
                        kind = (
                            "zero+plaska"
                            if (zero.loc[r0:r1].all() and flat.loc[r0:r1].all())
                            else (
                                "zero"
                                if zero.loc[r0:r1].all()
                                else ("plaska" if flat.loc[r0:r1].all() else "mieszana")
                            )
                        )
                        rows.append((s, m, scope, "zamrozenie", last_normal(r0), r0, n, kind))
                g_in = [d for d in gaps if a <= d < w_end]
                if g_in:
                    rows.append(
                        (s, m, scope, "dziura", last_normal(g_in[0]), g_in[0], len(g_in), None)
                    )
    ev = pd.DataFrame(
        rows,
        columns=[
            "symbol",
            "miesiac",
            "okno",
            "rodzaj",
            "ostatnia_normalna",
            "start",
            "dni",
            "szczegol",
        ],
    )
    return ev, members, close


# ------------------------------------------------------------------ droga 2: pliki osobno, własny ranking, pętle
def route2() -> tuple[set, dict]:
    files = {p.name[: -len("_1d.parquet")]: p for p in sorted(FULL.glob("*_1d.parquet"))}
    ok_syms = set(eligible_symbols(list(files)))
    series: dict[str, dict] = {}
    for s, p in files.items():
        d = pd.read_parquet(p, columns=["open_time", "close", "quote_volume"])
        if not len(d):
            continue
        t = pd.to_datetime(d["open_time"], utc=True)
        m = (t >= LO) & (t < END)
        series[s] = {
            ti: (float(cv), float(qv))
            for ti, cv, qv in zip(t[m], d["close"][m], d["quote_volume"][m], strict=True)
        }
    ohlc: dict[str, dict] = defaultdict(dict)
    o = pd.read_parquet(OHLC)
    for s, t, op, hi, lw, cl in zip(
        o["symbol"],
        pd.to_datetime(o["open_time"], utc=True),
        o["open"],
        o["high"],
        o["low"],
        o["close"],
        strict=True,
    ):
        ohlc[s][t] = (op, hi, lw, cl)
    sorted_days = {s: sorted(v) for s, v in series.items()}
    members: dict = {}
    for m in MONTHS:
        cand = []
        for s in ok_syms:
            ds = sorted_days.get(s, [])
            i0, i1 = bisect_left(ds, m - pd.Timedelta(days=30)), bisect_left(ds, m)
            v = [series[s][t][1] for t in ds[i0:i1] if not math.isnan(series[s][t][1])]
            if len(v) >= 30:
                cand.append((-(sum(v) / len(v)), s))
        cand.sort()
        members[m] = sorted(s for _, s in cand[:20])
    events = set()
    for s in sorted({x for v in members.values() for x in v}):
        days = sorted(series[s])
        flagged = []
        for t in days:
            cv, qv = series[s][t]
            q = ohlc[s].get(t)
            fl = qv == 0.0 or (q is not None and q[0] == q[1] == q[2] == q[3])
            flagged.append(fl)
        runs, i = [], 0
        while i < len(days):
            if flagged[i]:
                j = i
                while j + 1 < len(days) and flagged[j + 1] and days[j + 1] - days[j] == DAY:
                    j += 1
                if j - i + 1 >= MIN_RUN:
                    runs.append((days[i], days[j]))
                i = j + 1
            else:
                i += 1
        gaps = [days[k] + DAY for k in range(len(days) - 1) if days[k + 1] - days[k] > DAY]
        last = days[-1]
        for m in MONTHS:
            if s not in members[m]:
                continue
            a, b = windows(m)
            if last < DATA_LAST and a <= last + DAY < b:
                events.add((s, m, "koniec"))
            if any(r0 < b and r1 >= a for r0, r1 in runs):
                events.add((s, m, "zamrozenie"))
            if any(a <= g < b for g in gaps) or any(
                days[k] < a and days[k + 1] > a for k in range(len(days) - 1)
            ):
                events.add((s, m, "dziura"))
    return events, members


def main() -> None:
    print(SEP)
    print(
        "Zadanie 025 / B — częstość wstrzymań i wycofań w koszyku top-20 (opis, 0 wariantów, bez zwrotów)"
    )
    print(
        f"komenda: PYTHONUTF8=1 PYTHONPATH=. .venv/bin/python zadania/025-dowody/czestosc.py {RAW}"
    )
    print(
        f"dane: {FULL} (świece 1d + obrót), {OHLC} (OHLC członków), {MARK} (mark, sekcja 4); od {LO.date()}"
    )
    print(
        f"miesiące koszyka: {MONTHS[0]:%Y-%m} … {MONTHS[-1]:%Y-%m} ({len(MONTHS)}); zdarzenie: seria ≥ {MIN_RUN} dni"
    )
    ev, members, close = route1()
    n_pairs = sum(len(v) for v in members.values())
    print(SEP)
    print(
        "1. DROGA 1 — `monthly_members` (funkcja dziennika) na panelu `universe_full`, okno W = miesiąc koszyka"
    )
    print(
        f"   mianownik: {n_pairs} par (moneta, miesiąc) w koszyku = {len(MONTHS)} miesięcy × 20; różnych monet: {len({s for v in members.values() for s in v})}"
    )
    w = ev[ev["okno"] == "W"]
    pairs = sorted({(r.symbol, r.miesiac) for r in w.itertuples()})
    k = len(pairs)
    lo_w, hi_w = wilson(k, n_pairs)
    lo_c, hi_c = clopper_pearson(k, n_pairs)
    print(
        f"   par ze zdarzeniem: {k}  →  częstość {100 * k / n_pairs:.2f} %  (Wilson 95 % [{100 * lo_w:.2f}; {100 * hi_w:.2f}] %, dokładny Clopper–Pearson [{100 * lo_c:.2f}; {100 * hi_c:.2f}] %)"
    )
    by_kind = w.groupby("rodzaj").apply(
        lambda g: len({(r.symbol, r.miesiac) for r in g.itertuples()}), include_groups=False
    )
    print(
        f"   wg rodzaju (para liczona w każdym rodzaju, który w niej wystąpił): {by_kind.to_dict()}"
    )
    months_hit = sorted({m for _, m in pairs})
    print(
        f"   miesięcy koszyka z ≥ 1 zdarzeniem: {len(months_hit)} z {len(MONTHS)} → na miesiąc {100 * len(months_hit) / len(MONTHS):.1f} %"
        f" (Wilson [{100 * wilson(len(months_hit), len(MONTHS))[0]:.1f}; {100 * wilson(len(months_hit), len(MONTHS))[1]:.1f}] %)"
    )
    print(f"   różnych monet ze zdarzeniem: {len({s for s, _ in pairs})}")
    print("   lista (okno W):")
    show = w.sort_values(["miesiac", "symbol", "rodzaj"])
    for r in show.itertuples():
        ln = r.ostatnia_normalna.date() if r.ostatnia_normalna is not None else "—"
        extra = (
            f", seria {r.dni} dni ({r.szczegol})"
            if r.rodzaj == "zamrozenie"
            else (
                f", dni bez świecy w W: {r.dni}"
                if r.rodzaj == "dziura"
                else f", ostatnia świeca {r.start.date()} (sama oflagowana: {bool(r.szczegol)})"
            )
        )
        print(
            f"     {r.symbol:<14} koszyk {r.miesiac:%Y-%m}  {r.rodzaj:<10} ostatnia normalna świeca {ln}; start {r.start.date()}{extra}"
        )
    wp = ev[ev["okno"] == "W+"]
    pairs_ext = sorted({(r.symbol, r.miesiac) for r in wp.itertuples()})
    extra_pairs = sorted(set(pairs_ext) - set(pairs))
    print(
        f"   okno rozszerzone W+ (+7 dni po końcu miesiąca, opis): {len(pairs_ext)} par; dodatkowe: {[(s, f'{m:%Y-%m}') for s, m in extra_pairs]}"
    )
    per_year = pd.Series([m.year for _, m in pairs]).value_counts().sort_index().to_dict()
    print(f"   wg roku (pary ze zdarzeniem / 240 par rocznie, 2021: 220): {per_year}")

    print(SEP)
    print("2. ZNANE PRZYPADKI (LP1): czy były w koszyku i czy droga 1 je widzi")
    for s, mm in KNOWN:
        m = pd.Timestamp(mm + "-01", tz="UTC")
        inb = s in members.get(m, [])
        e = w[(w["symbol"] == s) & (w["miesiac"] == m)]
        print(
            f"   {s:<11} {mm}: w koszyku = {inb}; zdarzenia: {sorted(set(e['rodzaj'])) or 'brak'}"
        )
    for s in ("FTTUSDT", "LUNAUSDT", "ALPACAUSDT"):
        ms = [f"{m:%Y-%m}" for m in MONTHS if s in members[m]]
        print(f"   {s:<11} miesiące w koszyku: {ms}")

    print(SEP)
    print(
        "3. DRUGA DROGA — pliki osobno, własny ranking top-20 (bez `monthly_members`), serie pętlą"
    )
    ev2, members2 = route2()
    same_members = all(members2[m] == members[m] for m in MONTHS)
    diff_m = [f"{m:%Y-%m}" for m in MONTHS if members2[m] != members[m]]
    print(
        f"   skład identyczny z drogą 1 we wszystkich miesiącach: {same_members} (różne: {diff_m})"
    )
    ev1 = {(r.symbol, r.miesiac, r.rodzaj) for r in w.itertuples()}
    pairs2 = {(s, m) for s, m, _ in ev2}
    print(
        f"   par ze zdarzeniem: droga 1 = {k}, droga 2 = {len(pairs2)}; zdarzeń (para, rodzaj): {len(ev1)} vs {len(ev2)}"
    )
    print(f"   tylko w drodze 1: {sorted((s, f'{m:%Y-%m}', r) for s, m, r in ev1 - ev2)}")
    print(f"   tylko w drodze 2: {sorted((s, f'{m:%Y-%m}', r) for s, m, r in ev2 - ev1)}")

    print(SEP)
    print(
        "4. TRZECIA DROGA (częściowa) — cena ostatnia stoi (high = low), a mark się rusza (`mark_1d`, jak LP1)"
    )
    if MARK.exists():
        mk = pd.read_parquet(MARK)
        mk["open_time"] = pd.to_datetime(mk["open_time"], utc=True)
        o = pd.read_parquet(OHLC)
        o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
        j = o.merge(mk, on=["symbol", "open_time"], suffixes=("", "_mark"))
        j = j[(j["open_time"] >= LO) & (j["open_time"] < END)]
        stuck = j[(j["high"] == j["low"]) & (j["high_mark"] > j["low_mark"])]
        hits = set()
        for r in stuck.itertuples():
            m = r.open_time.normalize().replace(day=1)
            if r.symbol in members.get(m, []):
                hits.add((r.symbol, m))
        print(
            f"   dni „ostatnia stoi, mark się rusza” u członka koszyka: {len(stuck)} dni łącznie w archiwum; par (moneta, miesiąc) w koszyku: {sorted((s, f'{m:%Y-%m}') for s, m in hits)}"
        )
        print(f"   te pary są wśród zdarzeń drogi 1: {all(p in set(pairs) for p in hits)}")
        for s, m in sorted(hits):
            g = stuck[
                (stuck["symbol"] == s)
                & (stuck["open_time"] >= m)
                & (stuck["open_time"] < m + pd.offsets.MonthBegin(1))
            ]
            fr = float(g["close"].iloc[0])
            dev_lo = float(g["low_mark"].min()) / fr - 1
            dev_hi = float(g["high_mark"].max()) / fr - 1
            print(
                f"     {s} {m:%Y-%m}: {len(g)} dni, cena ostatnia {fr:g}, mark w tych dniach od {100 * dev_lo:+.1f} % do {100 * dev_hi:+.1f} % wobec niej"
            )
    else:
        print(f"   BRAK DANYCH: {MARK}")

    print(SEP)
    print(
        "5. KOGO NIE MA W ZBIORZE DZIENNIKA — skład z `data/raw/live` (pobrany raz, tylko TRADING) vs archiwum, 2025-09 … 2026-06"
    )
    live = RAW / "live"
    from data.fetch_live import symbol_files

    frames = {}
    for s, p in symbol_files(live).items():
        d = pd.read_parquet(p, columns=["open_time", "quote_volume"])
        if len(d):
            frames[s] = d.set_index(pd.to_datetime(d["open_time"], utc=True))["quote_volume"]
    if frames:
        vol_live = pd.concat(frames, axis=1, sort=True)
        last_live = max(v.index.max() for v in frames.values())
        ms = [m for m in MONTHS if m >= pd.Timestamp("2025-09-01", tz="UTC")]
        ml = monthly_members(vol_live, ms)
        print(f"   plików świec w live: {len(frames)}, ostatnia świeca {last_live.date()}")
        for m in ms:
            miss, extra = sorted(set(members[m]) - set(ml[m])), sorted(set(ml[m]) - set(members[m]))
            if miss or extra:
                print(f"     {m:%Y-%m}: tylko w archiwum {miss}; tylko w live {extra}")
                for s in miss:
                    c = close[s]
                    print(
                        f"       {s}: plik w live = {(live / f'{s}_1d.parquet').exists()}; w archiwum ostatnia świeca {c.last_valid_index().date()}"
                    )
        print(
            f"   miesięcy z innym składem: {sum(set(members[m]) != set(ml[m]) for m in ms)} z {len(ms)}"
        )
    else:
        print(f"   BRAK DANYCH: {live}")
    print(SEP)
    print(
        "6. CO SILNIK DZIENNIKA ZROBIŁBY Z TĄ MONETĄ W MIESIĄCU ZDARZENIA (pozycje, bez zwrotów; archiwum, start faz 2021-02-01)"
    )
    print(
        "   TS1 (trend): znak i waga w jednostkach kapitału fazy przy formowaniach w W od dnia zdarzenia; X1: noga"
    )
    from backtest.ts_momentum import build_formations, ewma_vol, formation_dates, signal_sign
    from backtest.xs_momentum import rank_legs, signal_panel

    signs, vols, sig = signal_sign(close), ewma_vol(close), signal_panel(close)
    t0 = MONTHS[0]
    for r in w.sort_values("miesiac").itertuples():
        a, b = windows(r.miesiac)
        j = list(close.columns).index(r.symbol)
        ts_rows, x1_rows = [], []
        for ph in range(7):
            dates = [
                t for t in formation_dates(close.index, t0, END, ph) if max(a, r.start) <= t < b
            ]
            for t, (_, wv) in zip(
                dates, build_formations(signs, vols, members, dates), strict=True
            ):
                ts_rows.append((t, wv[j]))
                legs = rank_legs(sig.loc[t], members[r.miesiac])
                x1_rows.append(
                    "long"
                    if legs and r.symbol in legs[0]
                    else ("short" if legs and r.symbol in legs[1] else "-")
                )
        nz = [(t, wv) for t, wv in ts_rows if wv != 0]
        cnt = pd.Series(x1_rows).value_counts().to_dict() if x1_rows else {}
        rng = (
            f"{min(abs(wv) for _, wv in nz):.4f}–{max(abs(wv) for _, wv in nz):.4f}" if nz else "—"
        )
        sgn = sorted({"long" if wv > 0 else "short" for _, wv in nz})
        # pozycje WNIESIONE w zdarzenie: formowania w 7 dniach przed zdarzeniem (żyją jeszcze w dniu zdarzenia)
        held_ts, held_x1 = [], []
        for ph in range(7):
            dates = [
                t
                for t in formation_dates(close.index, t0, END, ph)
                if r.start - pd.Timedelta(days=7) <= t < r.start
            ]
            for t, (_, wv) in zip(
                dates, build_formations(signs, vols, members, dates), strict=True
            ):
                mt = t.normalize().replace(day=1)
                if wv[j] != 0:
                    held_ts.append(wv[j])
                legs = (
                    rank_legs(sig.loc[t], members[mt]) if r.symbol in members.get(mt, []) else None
                )
                if legs and (r.symbol in legs[0] or r.symbol in legs[1]):
                    held_x1.append("long" if r.symbol in legs[0] else "short")
        print(
            f"     {r.symbol:<11} {r.miesiac:%Y-%m} ({r.rodzaj}, od {r.start.date()}):"
            f" WNIESIONE w zdarzenie (formowania D−7…D−1): TS1 {len(held_ts)} faz"
            f" ({sorted({'long' if x > 0 else 'short' for x in held_ts})}, |waga| {max((abs(x) for x in held_ts), default=0):.4f}),"
            f" X1 {len(held_x1)} faz {sorted(set(held_x1))};"
            f" NOWE od zdarzenia w W: formowań {len(ts_rows)}, TS1 z pozycją {len(nz)} ({sgn}, |waga| {rng}), X1 nogi {cnt}"
        )
    print(SEP)
    print(
        "Miesiące 2026-07 … 2026-09 (okres dziennika): BRAK DANYCH w archiwum (koniec 2026-06-30); `data/raw/live` nie ma wycofanych."
    )


if __name__ == "__main__":
    main()
