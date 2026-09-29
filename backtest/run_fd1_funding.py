"""
run_fd1_funding.py — runda FD1 (zadanie 016, 0 wariantów, opisowo): składowa funding nóg dziennika TS1 (7 faz, 2×
z likwidacją izolowaną, jak RU1 / dziennik) i X1 (średnia 7 faz, jak X1F / dziennik) policzona dwiema drogami:

(a) jak silnik — dzienna suma stawek × waga z początku dnia (`ts_momentum.phase_returns_liq`,
    `xs_momentum.long_short_returns`, bez zmian);
(b) rozliczenie po rozliczeniu — ilość stała od formowania × cena w chwili rozliczenia × stawka, konwencja
    (wejście, wyjście] (zlecenie dziennika po 00:00 UTC), `backtest/funding_settlement.py`.

Skrypt jest neutralnym reporterem: drukuje składową funding, różnicę (b) − (a) w %/rok kapitału nogi z przedziałem
(bootstrap blokowy po tygodniach), rozbicie, trzy miejsca ryzyka i kontrole. Nie drukuje zwrotu netto, t ani Sharpe'a
nóg. Werdykt wobec KO1 podpisuje README rundy.

Ceny w chwili rozliczenia: 00:00 = zamknięcie dnia; poza północą BTC ze świec 1h (kontrola: 4h), pozostałe monety —
brak cen w ciągu dnia w repo → interpolacja geometryczna zamknięć (przybliżenie; sprawdzone na BTC).

    PYTHONUTF8=1 OMP_NUM_THREADS=4 py -m backtest.run_fd1_funding \
        > runs/2026-09-29_fd1-funding-druga-droga/raw_output.txt
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from backtest import funding_settlement as fs

FULL = "data/raw/universe_full"
OHLC_FULL = "data/raw/universe_ohlc_full/ohlc_1d.parquet"
BTC_1H = "data/raw/BTC-USDT-USDT_1h_20201201T000000Z_20260701T000000Z.parquet"
BTC_4H = "data/raw/BTC-USDT-USDT_4h_20190910T000000Z_20260701T000000Z.parquet"
BTC = "BTCUSDT"
DATA_START, START, END = "2021-01-01", "2021-02-01", "2026-07-01"
LEV_TS, MMR = 2.0, 0.01  # dziennik: trend 2× (RU1 LEV_TS), mmr 1 %
SEED = 20260929
N_BOOT = 10_000
KO1 = {"TS1": 0.008, "X1": 0.033}  # koszt wykonania taker, %/rok (wniosek 99)
SHARE = 0.25  # próg porównywalności z pre-rejestracji: 25 % kosztu KO1 nogi
YEAR = 365.0
SEP = "=" * 108


# ----------------------------------------------------------------------------- dane


def load_inputs():  # pragma: no cover - IO
    """Panele jak w RU1 (TS1) i X1F (X1): zamknięcia od 2021-01-01, członkowie miesięczni, funding dzienny."""
    from backtest.checkpoint_lib import load_config
    from backtest.rebalance_premium import load_universe, monthly_members
    from backtest.xs_momentum import daily_funding_panel

    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, volume = load_universe(FULL)
    lo, end = pd.Timestamp(DATA_START, tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    funding = daily_funding_panel(FULL)
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    members = monthly_members(volume, months)
    o = pd.read_parquet(OHLC_FULL)
    o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
    hi = o.pivot(index="open_time", columns="symbol", values="high").reindex(
        index=close.index, columns=close.columns
    )
    lo_ = o.pivot(index="open_time", columns="symbol", values="low").reindex(
        index=close.index, columns=close.columns
    )
    return fee, close, funding, members, hi, lo_


def candle_close_at_end(path: str, hours: int) -> pd.Series:  # pragma: no cover - IO
    """Cena zamknięcia świecy indeksowana chwilą KOŃCA świecy (= cena w chwili rozliczenia)."""
    df = pd.read_parquet(path)
    t = pd.to_datetime(df["timestamp"], utc=True) + pd.Timedelta(hours=hours)
    p = pd.Series(df["close"].to_numpy(dtype=float), index=pd.DatetimeIndex(t))
    return p[~p.index.duplicated(keep="first")].sort_index()


def override_ratio(
    st: fs.Settlements, ratio: np.ndarray, col: int, price_end: pd.Series
) -> tuple[np.ndarray, int, int]:
    """Podmienia przybliżenie ceny(s)/ceny(00:00) na świece dla jednej kolumny (BTC); zwraca (ratio, n, n_ok)."""
    rows = np.where((st.sym == col) & ~st.midnight & (st.day >= 0))[0]
    s = pd.DatetimeIndex(st.ts[rows].astype("datetime64[ns]")).tz_localize("UTC")
    num = price_end.reindex(s).to_numpy()
    den = price_end.reindex(s.floor("D")).to_numpy()
    ok = np.isfinite(num) & np.isfinite(den) & (den > 0)
    out = ratio.copy()
    out[rows[ok]] = num[ok] / den[ok]
    return out, len(rows), int(ok.sum())


# ----------------------------------------------------------------------------- nogi


@dataclass
class Leg:
    name: str
    index: pd.DatetimeIndex
    columns: list[str]
    R: np.ndarray
    rets_df: pd.DataFrame
    fday: np.ndarray  # dzienny panel fundingu silnika (NaN = brak rozliczeń)
    phases: list = field(default_factory=list)  # (Positions, ramka silnika po dacie, holdings)
    capital: list = field(default_factory=list)  # kapitał fazy na początek dnia (TS1) albo None
    low_rel: pd.DataFrame | None = None
    high_rel: pd.DataFrame | None = None
    fc: int = 0  # pierwszy dzień wspólnego okna 7 faz


def build_ts1(fee, close, funding, members, hi, lo) -> Leg:  # pragma: no cover - dane
    from backtest.ts_momentum import (
        PHASES,
        build_formations,
        ewma_vol,
        formation_dates,
        portfolio,
        signal_sign,
    )

    start, end = pd.Timestamp(START, tz="UTC"), pd.Timestamp(END, tz="UTC")
    liq = {"high": hi, "low": lo, "lev": LEV_TS, "mmr": MMR}
    avg, per_phase = portfolio(close, funding, members, start, end, fee, liq=liq)
    rets = close.pct_change(fill_method=None)
    prev = close.shift(1)
    low_rel, high_rel = lo / prev, hi / prev
    signs, vols = signal_sign(close), ewma_vol(close)
    leg = Leg(
        "TS1",
        close.index,
        list(close.columns),
        np.nan_to_num(rets.to_numpy(dtype=float), nan=0.0),
        rets,
        funding.reindex(index=close.index, columns=close.columns).to_numpy(dtype=float),
        low_rel=low_rel,
        high_rel=high_rel,
    )
    for ph in range(PHASES):
        forms = build_formations(signs, vols, members, formation_dates(close.index, start, end, ph))
        pos = fs.ts_liq_positions(
            rets.to_numpy(dtype=float),
            forms,
            low_rel.to_numpy(dtype=float),
            high_rel.to_numpy(dtype=float),
            LEV_TS,
            MMR,
        )
        eng = per_phase[ph]
        holdings = []
        for k, (t_pos, w_new) in enumerate(forms):
            t_next = forms[k + 1][0] if k + 1 < len(forms) else len(close) - 1
            if t_pos + 1 > t_next:  # formowanie w ostatnim dniu danych — bez dni trzymania
                continue
            holdings.append(
                (close.index[t_pos + 1], close.index[t_next], pd.Series(w_new, index=close.columns))
            )
        leg.phases.append((pos, eng, holdings))
        leg.capital.append((1.0 + eng["gross"]).cumprod().shift(1).fillna(1.0))
    leg.fc = close.index.get_loc(max(p.index.min() for _, p, _ in leg.phases))
    leg.engine_avg = avg.set_index("date")
    return leg


def build_x1(fee, close, funding, members) -> Leg:  # pragma: no cover - dane
    from backtest.ts_momentum import PHASES, formation_dates
    from backtest.xs_momentum import (
        CAPITAL_PER_LEG,
        LEG_SIZE,
        long_short_returns,
        rank_legs,
        signal_panel,
    )

    start, end = pd.Timestamp(START, tz="UTC"), pd.Timestamp(END, tz="UTC")
    rets = close.pct_change()  # jak silnik X1 (domyślne wypełnienie)
    signal = signal_panel(close)
    leg = Leg(
        "X1",
        close.index,
        list(close.columns),
        np.nan_to_num(rets.to_numpy(dtype=float), nan=0.0),
        rets,
        funding.reindex(index=close.index, columns=close.columns).to_numpy(dtype=float),
    )
    month_starts = sorted(members)
    for ph in range(PHASES):
        dates = formation_dates(close.index, start, end, ph)
        eng = long_short_returns(close, funding, members, dates, fee).set_index("date")
        eng = eng.rename(columns={"funding_net": "funding", "r_ls_gross": "gross"})
        pos = fs.xs_positions(close, members, dates, rank_legs, CAPITAL_PER_LEG, LEG_SIZE, signal)
        holdings = []
        for k, t in enumerate(dates):
            prev = [m for m in month_starts if m <= t]
            legs = rank_legs(signal.loc[t], members[prev[-1]]) if prev else None
            if legs is None:
                continue
            w = pd.Series(0.0, index=close.columns)
            w[legs[0]] = CAPITAL_PER_LEG / LEG_SIZE
            w[legs[1]] = -CAPITAL_PER_LEG / LEG_SIZE
            last = dates[k + 1] if k + 1 < len(dates) else close.index[-1]
            days = close.index[(close.index > t) & (close.index <= last)]
            if len(days):
                holdings.append((days[0], days[-1], w))
        leg.phases.append((pos, eng, holdings))
        leg.capital.append(None)
    leg.fc = close.index.get_loc(max(p.index.min() for _, p, _ in leg.phases))
    return leg


# ----------------------------------------------------------------------------- analiza


def pct(x: float) -> str:
    return f"{100 * x:+.3f}"


def boot_line(label: str, daily: np.ndarray, seed: int = SEED) -> tuple[float, float, float]:
    m, lo, hi = fs.weekly_block_bootstrap(daily, N_BOOT, 7, seed, YEAR)
    print(f"  {label:<58} {pct(m):>8} %/rok   95% [{pct(lo)}; {pct(hi)}]")
    return m, lo, hi


def analyse(
    leg: Leg,
    st: fs.Settlements,
    ratios: dict[str, np.ndarray],
    cnt: np.ndarray,
    has_file: np.ndarray,
    close_nan: np.ndarray,
):
    """Wszystkie tablice dla jednej nogi; zwraca słownik szeregów dziennych (portfel = średnia faz, okno wspólne)."""
    n_days, n_sym = leg.R.shape
    P = len(leg.phases)
    fc = leg.fc
    keys = ["a", "ctrl", "q1", "b1", "b2", "new_edge", "old_edge"] + [f"b0_{m}" for m in ratios]
    keys += [f"b1_{m}" for m in ratios] + ["b1_eng", "b0_eng", "d2_diff", "ruin"]
    daily = {k: np.zeros(n_days) for k in keys}
    sym = {k: np.zeros(n_sym) for k in ("a", "b1", "b1_eng", "pos_days", "abs_a")}
    capstat = {"min": np.inf, "ruin_holdings": 0}
    btc = leg.columns.index(BTC) if BTC in leg.columns else -1
    btc_drift = {m: 0.0 for m in ratios}
    mid_cnt = np.zeros((n_days, n_sym))
    ok = (st.day >= 0) & st.midnight
    np.add.at(mid_cnt, (st.day[ok], st.sym[ok]), 1.0)
    cls = np.full((n_days, n_sym), "inne", dtype=object)
    cls[cnt == 0] = "brak"
    cls[cnt == 3] = "8h"
    cls[cnt == 6] = "4h"
    cls[cnt == 24] = "1h"
    # dni, |a|, b1−a, dryf, (D1) b1_eng−a
    risk2 = {c: np.zeros(5) for c in ("8h", "4h", "1h", "inne", "brak")}
    # n, silnik (nowa), (b) stara, (D1) stara na wagach silnika
    risk1 = {c: np.zeros(4) for c in ("obie", "tylko_nowa", "tylko_stara")}
    risk3 = {"dni_poz": 0.0, "bez_rozl": 0.0, "bez_pliku": 0.0, "bez_ceny": 0.0, "dziura": 0.0}
    risk3.update({"niepelne": 0.0, "nan_stawki": 0.0, "granica_abs": 0.0})
    checks = {"funding": 0.0, "gross": 0.0}
    per_phase_diff = []
    win = np.zeros(n_days, dtype=bool)
    win[fc:] = True
    med_abs_rate = float(np.nanmedian(np.abs(st.rate)))
    for pos, eng, _ in leg.phases:
        a = fs.engine_funding(pos.W_eng, leg.fday)
        eng_f = eng["funding"].reindex(leg.index[pos.in_phase]).to_numpy()
        checks["funding"] = max(
            checks["funding"], float(np.max(np.abs(a.sum(1)[pos.in_phase] - eng_f)))
        )
        eng_g = eng["gross"].reindex(leg.index[pos.in_phase]).to_numpy()
        checks["gross"] = max(
            checks["gross"], float(np.max(np.abs(pos.gross[pos.in_phase] - eng_g)))
        )
        ones = np.ones(len(st.rate))
        ctrl = fs.settlement_funding(pos.W_eng, pos.R, pos.alive_end, pos.first, st, ones)["b0"]
        q1 = fs.settlement_funding(pos.W, pos.R, pos.alive_end, pos.first, st, ones)["b0"]
        daily["a"] += a.sum(1)
        daily["ctrl"] += ctrl.sum(1)
        daily["q1"] += q1.sum(1)
        head = None
        for m, ratio in ratios.items():
            b = fs.settlement_funding(pos.W, pos.R, pos.alive_end, pos.first, st, ratio)
            daily[f"b0_{m}"] += b["b0"].sum(1)
            daily[f"b1_{m}"] += b["b1"].sum(1)
            if btc >= 0:
                btc_drift[m] += float((b["b0"][win, btc] - q1[win, btc]).sum())
            if m == "1h":
                head = b
        daily["b1"] += head["b1"].sum(1)
        daily["b2"] += head["b2"].sum(1)
        daily["new_edge"] += head["new_edge"].sum(1)
        daily["old_edge"] += head["old_edge"].sum(1)
        diff = head["b1"] - a
        per_phase_diff.append(float(diff[win].sum(1).mean() * YEAR))
        # diagnostyka po wyniku: (D1) wagi silnika, (D2) bez okresów ruiny stałej ilości
        beng = fs.settlement_funding(pos.W_eng, pos.R, pos.alive_end, pos.first, st, ratios["1h"])
        daily["b1_eng"] += beng["b1"].sum(1)
        daily["b0_eng"] += beng["b0"].sum(1)
        sym["b1_eng"] += beng["b1"][win].sum(0)
        diff_eng = beng["b1"] - a
        rd = fs.ruin_days(pos)
        daily["d2_diff"] += diff.sum(1) * ~rd
        daily["ruin"] += rd.astype(float)
        capstat["min"] = min(capstat["min"], float(np.nanmin(pos.cap_end[win & pos.in_phase])))
        capstat["ruin_holdings"] += int((rd & pos.first & win).sum())
        sym["a"] += a[win].sum(0)
        sym["b1"] += head["b1"][win].sum(0)
        held = (pos.W != 0) & win[:, None]
        sym["pos_days"] += held.sum(0)
        sym["abs_a"] += np.abs(a[win]).sum(0)
        drift = head["b0"] - q1
        for c in risk2:
            m_ = held & (cls == c)
            risk2[c] += [
                m_.sum(),
                np.abs(a[m_]).sum(),
                diff[m_].sum(),
                drift[m_].sum(),
                diff_eng[m_].sum(),
            ]
        # miejsce ryzyka nr 1: rozliczenia o północy w pierwszym dniu okresu (granica formowania)
        d0 = np.where(pos.first & (np.arange(n_days) >= fc + 1))[0]
        for d in d0:
            has = mid_cnt[d] > 0
            new = (pos.W[d] != 0) & has
            old = (pos.W[d - 1] * pos.alive_end[d - 1] != 0) & has
            for c, m_ in (
                ("obie", new & old),
                ("tylko_nowa", new & ~old),
                ("tylko_stara", ~new & old),
            ):
                risk1[c] += [
                    m_.sum(),
                    head["new_edge"][d, m_].sum(),
                    head["old_edge"][d - 1, m_].sum(),
                    beng["old_edge"][d - 1, m_].sum(),
                ]
        # miejsce ryzyka nr 3: brakujące stawki
        fnan = ~np.isfinite(leg.fday)
        risk3["dni_poz"] += held.sum()
        miss = held & fnan
        risk3["bez_rozl"] += miss.sum()
        risk3["bez_pliku"] += (miss & ~has_file[None, :]).sum()
        risk3["bez_ceny"] += (miss & has_file[None, :] & close_nan).sum()
        gap = miss & has_file[None, :] & ~close_nan
        risk3["dziura"] += gap.sum()
        risk3["granica_abs"] += float((np.abs(pos.W) * gap).sum() * 3 * med_abs_rate)
        risk3["niepelne"] += (held & (cls == "inne")).sum()
    for k in daily:
        daily[k] = daily[k][fc:] / P
    for k in ("a", "b1", "b1_eng", "pos_days", "abs_a"):
        sym[k] = sym[k] / P
    risk3["nan_stawki"] = int(np.isnan(st.rate[(st.day >= fc)]).sum())
    return {
        "daily": daily,
        "sym": sym,
        "capstat": capstat,
        "risk1": risk1,
        "risk2": risk2,
        "risk3": risk3,
        "checks": checks,
        "per_phase": per_phase_diff,
        "btc_drift": btc_drift,
        "n_days": n_days - fc,
        "med_abs_rate": med_abs_rate,
    }


def pandas_b1(
    W: np.ndarray, R: np.ndarray, alive_end: np.ndarray, st: fs.Settlements, ratio: np.ndarray
) -> np.ndarray:
    """
    Druga droga (D1): konwencja (wejście, wyjście] przez złączenia pandas zamiast rozrzutu `np.add.at`.
    Poza północą: waga dnia × cena(s)/cena(00:00) × stawka; północ: waga końca poprzedniego dnia × stawka.
    """
    n_days = W.shape[0]
    d_i, s_i = np.nonzero(W)
    start = pd.DataFrame({"day": d_i, "sym": s_i, "w": W[d_i, s_i]})
    start["w_end"] = start["w"] * (1.0 + R[d_i, s_i]) * alive_end[d_i, s_i]
    sets = pd.DataFrame(
        {
            "day": st.day,
            "sym": st.sym,
            "mid": st.midnight,
            "f": np.nan_to_num(st.rate, nan=0.0),
            "ratio": ratio,
        }
    )
    sets = sets[sets["day"] >= 0]
    off = sets[~sets["mid"]].merge(start[["day", "sym", "w"]], on=["day", "sym"])
    off_c = (-off["w"] * off["ratio"] * off["f"]).groupby(off["day"]).sum()
    mid = sets[sets["mid"]].assign(day=lambda x: x["day"] - 1)
    mid = mid.merge(start[["day", "sym", "w_end"]], on=["day", "sym"])
    mid_c = (-mid["w_end"] * mid["f"]).groupby(mid["day"]).sum()
    out = np.zeros(n_days)
    tot = off_c.add(mid_c, fill_value=0.0)
    out[tot.index.to_numpy(dtype=int)] = tot.to_numpy()
    return out


def second_way(leg: Leg, settle: dict, ratio_fn) -> np.ndarray:  # pragma: no cover - dane
    """Druga droga liczby głównej: (b) dolarowo (`dollar_way_b1`) − (a) wprost z kolumny funding silnika."""
    tot = np.zeros(len(leg.index))
    for (_, eng, holdings), cap in zip(leg.phases, leg.capital, strict=True):
        b = fs.dollar_way_b1(
            holdings,
            leg.rets_df,
            settle,
            ratio_fn,
            capital=cap,
            low_rel=leg.low_rel,
            high_rel=leg.high_rel,
            lev=LEV_TS,
            mmr=MMR,
        )
        a = eng["funding"].reindex(leg.index).fillna(0.0)
        tot += (b - a).to_numpy()
    return tot[leg.fc :] / len(leg.phases)


# ----------------------------------------------------------------------------- wydruk


def report(leg: Leg, res: dict) -> dict:  # pragma: no cover - wydruk
    d = res["daily"]
    idx = leg.index[leg.fc :]
    diff = d["b1"] - d["a"]
    print(SEP)
    print(
        f"{leg.name}: okno wspólne 7 faz {idx[0].date()} → {idx[-1].date()} ({len(idx)} dni); "
        f"jednostka: % kapitału nogi na rok (średnia dzienna × 365)"
    )
    print(SEP)
    print("1. Kontrole")
    print(
        f"  odtworzenie silnika (7 faz): max |funding − silnik| = {res['checks']['funding']:.2e}, "
        f"max |gross − silnik| = {res['checks']['gross']:.2e}"
    )
    if hasattr(leg, "engine_avg"):
        ea = leg.engine_avg["funding"].reindex(idx).to_numpy()
        print(
            f"  portfel (a) wobec kolumny funding portfolio(): max |różnica| = {np.max(np.abs(d['a'] - ea)):.2e}"
        )
    ctrl = d["ctrl"] - d["a"]
    print(
        f"  kontrola zerowa (wagi silnika, cena stała w dniu, konwencja silnika) − (a): "
        f"{pct(ctrl.mean() * YEAR)} %/rok, max |dzień| {np.max(np.abs(ctrl)):.2e}"
    )
    print("2. Składowa funding (znak: + = noga otrzymuje, − = płaci)")
    print(
        f"  (a) silnik: dzienna suma × waga                               {pct(d['a'].mean() * YEAR):>8} %/rok"
    )
    print(
        f"  (b) rozliczenie po rozliczeniu, (wejście, wyjście], BTC 1h    {pct(d['b1'].mean() * YEAR):>8} %/rok"
    )
    print("3. Różnica (b) − (a) i rozbicie (bootstrap blokowy tygodniowy, 10 000 losowań)")
    m, lo, hi = boot_line("(b) − (a) — LICZBA GŁÓWNA", diff)
    boot_line("  (0) kontrola zerowa", ctrl)
    boot_line("  (1) model ilości: stała ilość − waga silnika", d["q1"] - d["ctrl"])
    boot_line("  (2) dryf ceny w ciągu dnia (BTC 1h, reszta interpolacja)", d["b0_1h"] - d["q1"])
    boot_line("  (3) przypisanie 00:00: stara zamiast nowej pozycji", d["b1"] - d["b0_1h"])
    boot_line("(b2) − (a): przedział domknięty [wejście, wyjście] — dwa razy", d["b2"] - d["a"])
    ser = pd.Series(diff, index=idx)
    yearly = ser.groupby(ser.index.year).mean() * YEAR
    print("  per rok (%/rok): " + ", ".join(f"{y}: {pct(v)}" for y, v in yearly.items()))
    print(
        f"  per rok: mediana {pct(yearly.median())}, zakres [{pct(yearly.min())}; {pct(yearly.max())}]; "
        f"średnia dzienna × 365 {pct(diff.mean() * YEAR)}, mediana dzienna × 365 {pct(np.median(diff) * YEAR)}"
    )
    pp = np.array(res["per_phase"])
    print(
        f"  per faza (każda osobno, %/rok kapitału fazy): mediana {pct(np.median(pp))}, "
        f"zakres [{pct(pp.min())}; {pct(pp.max())}]"
    )
    s = res["sym"]
    n = res["n_days"]
    held = s["pos_days"] > 0
    contrib = (s["b1"] - s["a"]) / n * YEAR
    c = pd.Series(contrib[held], index=np.array(leg.columns)[held])
    days_ = pd.Series(s["pos_days"][held], index=c.index)
    a_c = pd.Series(s["a"][held] / n * YEAR, index=c.index)
    print(
        f"  per moneta ({len(c)} monet z pozycją; wkład w %/rok kapitału nogi): mediana {pct(c.median())}, "
        f"zakres [{pct(c.min())}; {pct(c.max())}], suma {pct(c.sum())}"
    )
    top = c.reindex(c.abs().sort_values(ascending=False).index[:8])
    print(
        "  8 monet o największym |wkładzie|: "
        + "; ".join(
            f"{k} {pct(v)} (dni poz. {days_[k]:.0f}, (a) {pct(a_c[k])})" for k, v in top.items()
        )
    )
    print("4. Miejsce ryzyka nr 1 — rozliczenie o 00:00 w dniu zmiany pozycji (granica formowania)")
    r1 = res["risk1"]
    print(
        "  kategoria (moneta w starej / nowej pozycji) | n rozliczeń (suma 7 faz) | silnik (nowa) %/rok | (b) (stara) %/rok"
    )
    for k, lab in (
        ("obie", "w obu (silnik: nowa, giełda: stara)"),
        ("tylko_nowa", "tylko w nowej (silnik liczy, giełda nie)"),
        ("tylko_stara", "tylko w starej (silnik: WCALE, giełda liczy)"),
    ):
        v = r1[k]
        print(
            f"  {lab:<46} | {v[0]:8.0f} | {pct(v[1] / len(leg.phases) / n * YEAR):>8} | {pct(v[2] / len(leg.phases) / n * YEAR):>8}"
        )
    print(
        "  (przedział domknięty [wejście, wyjście] = obie kolumny naraz — rozliczenia „w obu” liczone DWA razy)"
    )
    print(
        "5. Miejsce ryzyka nr 2 — interwał rozliczeń w dniach pozycji (klasa z liczby rozliczeń w dniu)"
    )
    r2 = res["risk2"]
    tot_days = sum(v[0] for v in r2.values())
    tot_abs = sum(v[1] for v in r2.values())
    print(
        "  klasa | dni pozycji (moneta×dzień×faza) | udział dni | udział |(a)| | (b)−(a) %/rok | w tym dryf %/rok"
    )
    for k, v in r2.items():
        print(
            f"  {k:<5} | {v[0]:10.0f} | {100 * v[0] / tot_days:6.2f} % | {100 * v[1] / tot_abs if tot_abs else 0:6.2f} % | "
            f"{pct(v[2] / len(leg.phases) / n * YEAR):>8} | {pct(v[3] / len(leg.phases) / n * YEAR):>8}"
        )
    print("6. Miejsce ryzyka nr 3 — brakujące stawki (silnik: NaN → 0)")
    r3 = res["risk3"]
    print(
        f"  dni pozycji (moneta×dzień×faza): {r3['dni_poz']:.0f}; bez żadnego rozliczenia: {r3['bez_rozl']:.0f} "
        f"({100 * r3['bez_rozl'] / r3['dni_poz']:.3f} %), w tym: moneta bez pliku fundingu {r3['bez_pliku']:.0f}, "
        f"brak ceny dnia (wycofana / dziura w cenach) {r3['bez_ceny']:.0f}, dziura w fundingu przy cenie {r3['dziura']:.0f}"
    )
    print(
        f"  dni pozycji z niepełną / nietypową liczbą rozliczeń (≠ 0, 3, 6, 24): {r3['niepelne']:.0f}; "
        f"stawki NaN w plikach (od początku okna): {r3['nan_stawki']}"
    )
    bound = r3["granica_abs"] / len(leg.phases) / n * YEAR
    print(
        f"  ograniczenie z góry wpływu dziur w fundingu przy cenie: 3 rozliczenia × mediana |stawki| "
        f"{100 * res['med_abs_rate']:.4f} % × |waga| = {100 * bound:.4f} %/rok (BRAK DANYCH — nie uzupełniano)"
    )
    return {"m": m, "lo": lo, "hi": hi, "yearly": yearly, "coins": c}


def report_posthoc(leg: Leg, res: dict) -> dict:  # pragma: no cover - wydruk
    """Diagnostyka dopisana PO obejrzeniu pierwszego przebiegu (X1: ruina kapitału stałej ilości, MYX 2025-09)."""
    d = res["daily"]
    idx = leg.index[leg.fc :]
    n = res["n_days"]
    P = len(leg.phases)
    cs = res["capstat"]
    print(
        f"P. {leg.name} — DIAGNOSTYKA PO WYNIKU (nie była w pre-rejestracji; nie zastępuje liczby głównej)"
    )
    print(
        f"  kapitał fazy przy stałej ilości (koniec dnia, względem formowania): minimum {cs['min']:+.3f}; "
        f"okresów trzymania z ruiną (kapitał ≤ 0): {cs['ruin_holdings']}; dni faz w tych okresach: "
        f"{d['ruin'].sum() * P:.0f} z {n * P}"
    )
    print(
        "  (D1) każde rozliczenie osobno na WAGACH SILNIKA (model pozycji silnika bez zmian; BTC 1h):"
    )
    d1 = d["b1_eng"] - d["a"]
    m1, lo1, hi1 = boot_line("  (b′) − (a)", d1)
    boot_line("    dryf ceny w ciągu dnia", d["b0_eng"] - d["ctrl"])
    boot_line("    przypisanie 00:00: stara zamiast nowej pozycji", d["b1_eng"] - d["b0_eng"])
    ser = pd.Series(d1, index=idx)
    yearly = ser.groupby(ser.index.year).mean() * YEAR
    print("    per rok (%/rok): " + ", ".join(f"{y}: {pct(v)}" for y, v in yearly.items()))
    print(
        f"    per rok: mediana {pct(yearly.median())}, zakres [{pct(yearly.min())}; {pct(yearly.max())}]; "
        f"mediana dzienna × 365 {pct(np.median(d1) * YEAR)}"
    )
    s = res["sym"]
    held = s["pos_days"] > 0
    c = pd.Series(((s["b1_eng"] - s["a"]) / n * YEAR)[held], index=np.array(leg.columns)[held])
    top = c.reindex(c.abs().sort_values(ascending=False).index[:5])
    print(
        f"    per moneta ({len(c)}): mediana {pct(c.median())}, zakres [{pct(c.min())}; {pct(c.max())}]; "
        "największe |wkłady|: " + "; ".join(f"{k} {pct(v)}" for k, v in top.items())
    )
    r2 = res["risk2"]
    print(
        "    per klasa interwału (%/rok): "
        + ", ".join(f"{k}: {pct(v[4] / P / n * YEAR)}" for k, v in r2.items())
    )
    r1 = res["risk1"]
    print(
        "    granica 00:00, stara pozycja na wagach silnika (%/rok): "
        + ", ".join(f"{k}: {pct(v[3] / P / n * YEAR)}" for k, v in r1.items())
    )
    print(
        "  (D2) liczba główna (stała ilość) BEZ okresów ruiny — dni faz w ruinie wyzerowane w obu drogach:"
    )
    m2, lo2, hi2 = boot_line("  (b) − (a) bez ruiny", d["d2_diff"])
    ser2 = pd.Series(d["d2_diff"], index=idx)
    y2 = ser2.groupby(ser2.index.year).mean() * YEAR
    print(
        "    per rok (%/rok): "
        + ", ".join(f"{y}: {pct(v)}" for y, v in y2.items())
        + f"; mediana {pct(y2.median())}, zakres [{pct(y2.min())}; {pct(y2.max())}]"
    )
    return {"d1": (m1, lo1, hi1), "d2": (m2, lo2, hi2)}


def main() -> None:  # pragma: no cover - przebieg na danych
    warnings.filterwarnings("ignore", category=FutureWarning)  # pct_change() w silniku X1
    t0 = time.time()
    fee, close, funding, members, hi, lo = load_inputs()
    raw = fs.load_raw_funding(FULL, list(close.columns))
    st = fs.build_settlements(raw, list(close.columns), close.index)
    n_days, n_sym = close.shape
    has_file = np.array([c in raw and not raw[c].empty for c in close.columns])
    cnt = np.zeros((n_days, n_sym))
    ok = st.day >= 0
    np.add.at(cnt, (st.day[ok], st.sym[ok]), 1.0)
    print(SEP)
    print(
        "FD1 — funding nóg dziennika drugą drogą: dzienna suma × waga (silnik) wobec rozliczenia po rozliczeniu"
    )
    print(SEP)
    print(
        f"dane  : {FULL} — {n_sym} symboli 1d, {close.index[0].date()} → {close.index[-1].date()}; "
        f"pliki fundingu: {int(has_file.sum())}; rozliczeń w oknie: {int(ok.sum())}"
    )
    off = pd.Series(st.frac[ok] * 24).round(6)
    print(
        "rozliczenia wg godziny UTC (po zaokrągleniu do minuty): "
        + ", ".join(f"{h:g}h: {n}" for h, n in off.value_counts().sort_index().items() if n > 0)
    )
    mine = np.nan_to_num(fs.daily_sum(st, n_days, n_sym), nan=0.0)
    eng_panel = funding.reindex(index=close.index, columns=close.columns).fillna(0.0).to_numpy()
    mism = np.abs(mine - eng_panel) > 1e-15
    print(
        f"przypisanie do dnia: zaokrąglenie do minuty wobec floor('D') silnika — różnych komórek moneta×dzień: "
        f"{int(mism.sum())}"
    )
    # ceny w chwili rozliczenia
    p1h = candle_close_at_end(BTC_1H, 1)
    p4h = candle_close_at_end(BTC_4H, 4)
    btc_col = list(close.columns).index(BTC)
    daily_btc = close[BTC]
    t_end = daily_btc.index + pd.Timedelta(days=1)
    rel = (p1h.reindex(t_end).to_numpy() / daily_btc.to_numpy()) - 1.0
    print(
        f"BTC: zamknięcie świecy 1h o 24:00 wobec zamknięcia dnia — max |różnica względna| "
        f"{np.nanmax(np.abs(rel)):.2e} (n = {int(np.isfinite(rel).sum())})"
    )
    legs = [build_ts1(fee, close, funding, members, hi, lo), build_x1(fee, close, funding, members)]
    summary = {}
    for leg in legs:
        interp = fs.interp_ratio(st, leg.R)
        r1h, n_b, n_ok1 = override_ratio(st, interp, btc_col, p1h)
        r4h, _, n_ok4 = override_ratio(st, interp, btc_col, p4h)
        ratios = {"interp": interp, "4h": r4h, "1h": r1h}
        res = analyse(leg, st, ratios, cnt, has_file, close.isna().to_numpy())
        summary[leg.name] = report(leg, res)
        print(
            "7. Przybliżenie ceny mark — sprawdzenie na BTC (jedyna moneta ze świecami w ciągu dnia)"
        )
        print(
            f"  rozliczenia BTC poza północą: {n_b}; ze świecą 1h: {n_ok1}, 4h: {n_ok4} "
            f"(bez świecy → interpolacja)"
        )
        nb = res["n_days"] * len(leg.phases)
        print(
            "  dryf w ciągu dnia tylko z pozycji BTC (%/rok kapitału nogi): "
            + ", ".join(f"{m}: {pct(v / nb * YEAR)}" for m, v in res["btc_drift"].items())
        )
        d = res["daily"]
        print(
            "  dryf całej nogi przy różnych cenach BTC (%/rok): "
            + ", ".join(
                f"{m}: {pct((d[f'b0_{m}'] - d['q1']).mean() * YEAR)}"
                for m in ("interp", "4h", "1h")
            )
        )
        rows = (st.sym == btc_col) & ~st.midnight & (st.day >= leg.fc)
        e = interp[rows] - r1h[rows]
        print(
            f"  |cena interpolowana − cena 1h| / cena 00:00 w chwili rozliczenia BTC: mediana {np.median(np.abs(e)):.4f}, "
            f"95. percentyl {np.percentile(np.abs(e), 95):.4f}, średnia ze znakiem {np.mean(e):+.5f}"
        )
        # druga droga liczby głównej
        rets_df = leg.rets_df

        def ratio_fn(sym, s, rets_df=rets_df):
            if sym == BTC:
                num = p1h.reindex(s).to_numpy()
                den = p1h.reindex(s.floor("D")).to_numpy()
                good = np.isfinite(num) & np.isfinite(den)
                out = np.where(good, num / np.where(good, den, 1.0), np.nan)
            else:
                out = np.full(len(s), np.nan)
            day = s.floor("D")
            frac = np.asarray((s - day) / pd.Timedelta(days=1))
            r = rets_df[sym].reindex(day).fillna(0.0).to_numpy()
            return np.where(np.isfinite(out), out, (1.0 + r) ** frac)

        settle = {}
        for sym_, df in raw.items():
            if df.empty:
                continue
            ts = pd.to_datetime(df["timestamp"], utc=True).dt.round("min")
            ts = ts.dt.tz_convert(None).to_numpy().astype("datetime64[ns]")
            order = np.argsort(ts, kind="stable")
            settle[sym_] = (ts[order], df["funding_rate"].to_numpy(dtype=float)[order])
        t1 = time.time()
        dw = second_way(leg, settle, ratio_fn)
        num_m = (res["daily"]["b1"] - res["daily"]["a"]).mean() * YEAR
        print(
            "8. Druga droga liczby głównej (pandas, ilość × cena × stawka; (a) wprost z kolumny silnika)"
        )
        print(
            f"  (b) − (a): numpy na wagach {100 * num_m:+.6f} %/rok; dolarowo {100 * dw.mean() * YEAR:+.6f} %/rok; "
            f"max |różnica dzienna| {np.max(np.abs(dw - (res['daily']['b1'] - res['daily']['a']))):.2e} "
            f"({time.time() - t1:.0f} s)"
        )
        summary[leg.name].update(report_posthoc(leg, res))
        tot = np.zeros(len(leg.index))
        for pos, eng, _ in leg.phases:
            b = pandas_b1(pos.W_eng, pos.R, pos.alive_end, st, r1h)
            tot += b - eng["funding"].reindex(leg.index).fillna(0.0).to_numpy()
        pw = tot[leg.fc :] / len(leg.phases)
        d1 = res["daily"]["b1_eng"] - res["daily"]["a"]
        print(
            f"  druga droga (D1): numpy {100 * d1.mean() * YEAR:+.6f} %/rok; złączenia pandas, (a) z kolumny "
            f"silnika {100 * pw.mean() * YEAR:+.6f} %/rok; max |różnica dzienna| {np.max(np.abs(pw - d1)):.2e}"
        )
    print(SEP)
    print(
        "9. Skala KO1 (koszt wykonania taker, wniosek 99) i próg porównywalności z pre-rejestracji (25 %)"
    )
    for name, s in summary.items():
        thr = SHARE * KO1[name]
        print(
            f"  {name}: KO1 {100 * KO1[name]:.1f} %/rok, próg {100 * thr:.3f} %/rok | (b) − (a) {pct(s['m'])} "
            f"[{pct(s['lo'])}; {pct(s['hi'])}] | |średnia| / KO1 = {abs(s['m']) / KO1[name]:.3f} | "
            f"przedział w ±progu: {'tak' if (s['lo'] > -thr and s['hi'] < thr) else 'nie'} | "
            f"przedział obejmuje 0: {'tak' if s['lo'] <= 0 <= s['hi'] else 'nie'}"
        )
        for key, lab in (("d1", "(D1) wagi silnika"), ("d2", "(D2) bez okresów ruiny")):
            m_, lo_, hi_ = s[key]
            print(
                f"     po wyniku {lab}: {pct(m_)} [{pct(lo_)}; {pct(hi_)}] | |średnia| / KO1 = "
                f"{abs(m_) / KO1[name]:.3f} | przedział w ±progu: "
                f"{'tak' if (lo_ > -thr and hi_ < thr) else 'nie'}"
            )
    print(f"czas: {time.time() - t0:.0f} s")
    print(SEP)


if __name__ == "__main__":
    main()
