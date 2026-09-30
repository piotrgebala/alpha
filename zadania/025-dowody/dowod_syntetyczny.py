"""
Zadanie 025, krok 1 — dowód na danych SYNTETYCZNYCH: co robi dziennik (`backtest/live_journal.py`),
gdy moneta z koszyka (a) znika z giełdy (świece się kończą), (b) ma zamrożoną cenę (świece są, ale
open = high = low = close i obrót 0), (c) naprawdę spada o 90 % w dniu wycofania, a dziennik tego nie widzi.

Tylko odczyt kodu dziennika; wszystkie pliki w katalogu tymczasowym (nic w `dziennik/` ani `data/raw`).
Nie czyta wyników dziennika. Kod dziennika bez zmian — jedyna ingerencja: JOURNAL_START / X1_START
przestawione w pamięci na 2026-08-01 (jak w `tests/test_live_journal.py`), żeby zdarzenie wpadło w okres wyniku.

    cd <repo> && PYTHONUTF8=1 .venv/bin/python zadania/025-dowody/dowod_syntetyczny.py
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import live_journal as lj
from backtest.negative_control import synthetic_ohlc, synthetic_returns
from backtest.rebalance_premium import monthly_members
from backtest.ts_momentum import build_formations, ewma_vol, formation_dates, signal_sign
from backtest.xs_momentum import _month_of, rank_legs, signal_panel

FEE = 0.0007
D = pd.Timestamp("2026-08-20", tz="UTC")  # dzień zdarzenia (pierwszy dzień bez normalnej świecy)
DEAD, FROZ = "C01USDT", "C02USDT"
N_DAYS, N_COINS, SEED = 480, 22, 3  # 2025-06-01 … 2026-09-23, jak `tests/test_live_journal.py`
START = pd.Timestamp("2026-08-01", tz="UTC")
SEP = "-" * 100


def write_live(out: Path, scenario: str) -> None:
    """Katalog jak `data/raw/live`: świece 1d, funding 8h, Coinbase 1d, spot 8h (bez F&G i carry)."""
    r = synthetic_returns(N_DAYS, N_COINS, seed=SEED, start="2025-06-01")
    r.columns = ["BTCUSDT"] + [f"C{i:02d}USDT" for i in range(1, N_COINS)]
    o = synthetic_ohlc(r, seed=SEED)
    rng = np.random.default_rng(SEED)
    idx = r.index
    for c in r.columns:
        vol = rng.uniform(1e6, 1e8, N_DAYS)
        if c == DEAD:
            vol = np.full(N_DAYS, 2e10)  # zawsze w top-20
        if c == FROZ:
            vol = np.full(N_DAYS, 1.5e10)
        df = pd.DataFrame(
            {
                "open_time": idx,
                "open": o["open"][c].to_numpy(),
                "high": o["high"][c].to_numpy(),
                "low": o["low"][c].to_numpy(),
                "close": o["close"][c].to_numpy(),
                "quote_volume": vol,
            }
        )
        ts = pd.date_range(idx[0], periods=3 * N_DAYS, freq="8h")
        fu = pd.DataFrame({"timestamp": ts, "funding_rate": 1e-4})
        after = df["open_time"] >= D
        if c == DEAD and scenario == "wycofanie":
            df = df[~after]  # plik kończy się dzień przed D (giełda przestała notować)
            fu = fu[fu["timestamp"] < D]
        if c == DEAD and scenario == "krach":
            # rzeczywistość, której dziennik w scenariuszu „wycofanie” nie widzi: −90 % w dniu D, potem dalej
            prev = float(df.loc[~after, "close"].iloc[-1])
            k = df.loc[after, ["open", "high", "low", "close"]] * 0.1
            df.loc[after, ["open", "high", "low", "close"]] = k
            df.loc[df["open_time"] == D, ["open", "high"]] = prev
        if c == FROZ and scenario == "zamrozenie":
            last = float(df.loc[~after, "close"].iloc[-1])
            df.loc[after, ["open", "high", "low", "close"]] = last
            df.loc[after, "quote_volume"] = 0.0
        df.to_parquet(out / f"{c}_1d.parquet", index=False)
        fu.to_parquet(out / f"{c}_funding.parquet", index=False)
    btc = o["close"]["BTCUSDT"]
    prem = 1.0 + 0.001 * np.sin(np.arange(N_DAYS) / 9.0)
    pd.DataFrame({"open_time": idx, "close": btc.to_numpy() * prem}).to_parquet(
        out / "coinbase_BTC-USD_1d.parquet", index=False
    )
    ts8 = pd.date_range(idx[0], periods=3 * N_DAYS, freq="8h")
    pd.DataFrame({"timestamp": ts8, "close": np.repeat(btc.to_numpy(), 3)}).to_parquet(
        out / "spot_BTC-USDT_8h.parquet", index=False
    )


def log_fields(jdir: Path) -> str:
    line = (jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()[-1]
    keep = [f for f in line.split(" | ") if f.startswith(("as_of", "transakcje", "historia"))]
    return " | ".join(keep)


def main() -> None:
    lj.JOURNAL_START = START
    lj.X1_START = START
    root = Path(tempfile.mkdtemp(prefix="z025_"))
    data, eng = {}, {}
    try:
        print(SEP)
        print("1. PRZEBIEG DZIENNIKA (`lj.run(fetch=False)`) — czy się wywraca")
        for sc in ("baza", "wycofanie", "krach", "zamrozenie"):
            src, jdir = root / sc, root / f"dz_{sc}"
            src.mkdir()
            write_live(src, sc)
            text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
            ok = text.startswith("DZIENNIK")
            print(f"  {sc:<11} przebieg OK={ok}; log: {log_fields(jdir)}")
            data[sc] = lj.load_live(src)
        as_of = data["baza"]["close"].index[-1]
        print(f"  as_of = {as_of.date()}, dzień zdarzenia D = {D.date()}")

        print(SEP)
        print(f"2. WYCOFANIE {DEAD}: świece kończą się {(D - pd.Timedelta(days=1)).date()}")
        cw = data["wycofanie"]["close"][DEAD]
        print(
            f"  panel close: ostatnia wartość {cw.last_valid_index().date()}, potem NaN (dni NaN: {int(cw.isna().sum())})"
        )
        for sc in ("wycofanie", "krach"):
            e: dict = {}
            rets, _ = lj.components(data[sc], as_of, FEE, e)
            eng[sc] = (rets, e)
        rw, ew = eng["wycofanie"]
        rk, ek = eng["krach"]
        tw = ew["trend"].set_index("date")
        tk = ek["trend"].set_index("date")
        print(
            "  składowa trend (k = 1), dzień D i D+1: zwrot netto i liczba likwidacji (suma 7 faz)"
        )
        for d in (D, D + pd.Timedelta(days=1)):
            print(
                f"    {d.date()}: wycofanie net {tw.at[d, 'net']:+.5f}, likw. {tw.at[d, 'liquidations'] * 7:.0f}"
                f"  |  krach (prawda) net {tk.at[d, 'net']:+.5f}, likw. {tk.at[d, 'liquidations'] * 7:.0f}"
                f"  |  różnica {tw.at[d, 'net'] - tk.at[d, 'net']:+.5f}"
            )
        # pozycje ogłaszane (sygnały) po D: fazy, które wciąż trzymają monetę bez ceny
        print("  pozycje ogłaszane w `sygnaly.csv` (lj.positions) — fazy trendu z monetą bez ceny:")
        for k in (0, 3, 6, 7):
            a = D + pd.Timedelta(days=k)
            pos, *_ = lj.positions(data["wycofanie"], a, FEE)
            p = pos[(pos["symbol"] == DEAD) & (pos["component"] == "trend")]
            print(
                f"    as_of {a.date()}: faz z {DEAD} = {len(p)}, ekspozycja {p['exposure'].sum():+.4f}, "
                f"daty formowania {sorted(p['formed'].unique())}"
            )
        pos, k_next, hist, _ = lj.positions(data["wycofanie"], as_of, FEE)
        closed, opened = lj.trade_ledger(data["wycofanie"], as_of, hist, k_next)
        c = closed[(closed["symbol"] == DEAD) & (closed["data_wyjscia"] >= D.date().isoformat())]
        print(f"  `transakcje.csv` — zamknięte pozycje {DEAD} z wyjściem ≥ D: {len(c)}")
        cols = [
            "skladowa",
            "faza",
            "data_wejscia",
            "data_wyjscia",
            "cena_wyjscia",
            "powod_wyjscia",
            "zwrot_pozycji_proc",
        ]
        print(c[cols].head(8).to_string(index=False))
        # otwarte pozycje w dniu po D (as_of = D + 2): cena bieżąca NaN
        pos2, k2, hist2, _ = lj.positions(data["wycofanie"], D + pd.Timedelta(days=2), FEE)
        _, op2 = lj.trade_ledger(data["wycofanie"], D + pd.Timedelta(days=2), hist2, k2)
        o2 = op2[op2["symbol"] == DEAD]
        print(
            f"  `transakcje_otwarte.csv` przy as_of {(D + pd.Timedelta(days=2)).date()}: {len(o2)} pozycji {DEAD}, "
            f"cena_biezaca NaN: {int(o2['cena_biezaca'].isna().sum())}, zwrot_biezacy NaN: "
            f"{int(o2['zwrot_biezacy_proc'].isna().sum())}"
        )
        mem = monthly_members(lj.truncate(data["wycofanie"], as_of)["volume"], lj._months(as_of))
        print(
            "  skład koszyka (monthly_members): "
            + ", ".join(f"{m:%Y-%m}: {DEAD in v}" for m, v in mem.items() if m >= START)
        )

        print(SEP)
        print(
            f"3. ZAMROŻENIE {FROZ}: od D open = high = low = close = ostatnie zamknięcie, obrót 0"
        )
        dz = lj.truncate(data["zamrozenie"], as_of)
        close = dz["close"]
        signs, vols = signal_sign(close), ewma_vol(close)
        mem = monthly_members(dz["volume"], lj._months(as_of))
        print(
            "  skład koszyka: "
            + ", ".join(f"{m:%Y-%m}: {FROZ in v}" for m, v in mem.items() if m >= START)
        )
        j = list(close.columns).index(FROZ)
        end = as_of + pd.Timedelta(days=1)
        rows = []
        for ph in range(7):
            dates = [
                t
                for t in formation_dates(close.index, lj.ENGINE_START, end, ph)
                if t >= D - pd.Timedelta(days=7)
            ]
            for t, (_, w) in zip(dates, build_formations(signs, vols, mem, dates), strict=True):
                rows.append((t.date(), ph, signs.at[t, FROZ], vols.at[t, FROZ], w[j]))
        fz = pd.DataFrame(
            rows, columns=["formowanie", "faza", "znak", "sigma", "waga"]
        ).sort_values("formowanie")
        print("  TS1: wagi zamrożonej monety przy kolejnych formowaniach (co 7. wiersz):")
        print(fz.iloc[::7].to_string(index=False))
        froz_after = fz[pd.to_datetime(fz["formowanie"]).dt.tz_localize("UTC") >= D]
        print(
            f"  formowań po D z wagą ≠ 0: {int((froz_after['waga'] != 0).sum())} z {len(froz_after)}; "
            f"ostatnie ≠ 0: {froz_after.loc[froz_after['waga'] != 0, 'formowanie'].max()}"
        )
        lots = []
        for ph in range(7):
            forms = build_formations(
                signs, vols, mem, formation_dates(close.index, lj.ENGINE_START, end, ph)
            )
            for lot in lj.phase_lots(close, dz["low"], dz["high"], forms, as_of, lj.LEV_TREND):
                if lot["symbol"] == FROZ and close.index[lot["t_pos"]] >= D - pd.Timedelta(days=7):
                    lots.append(lot["status"])
        print(
            f"  pozycje {FROZ} od D−7: statusy {pd.Series(lots).value_counts().to_dict()} (likwidacja niemożliwa: high = low)"
        )
        sig = signal_panel(close)
        ms = sorted(mem)
        legs = []
        for ph in range(7):
            for t in formation_dates(close.index, lj.ENGINE_START, end, ph):
                if t < D:
                    continue
                lg = rank_legs(sig.loc[t], mem[_month_of(t, ms)])
                if lg and (FROZ in lg[0] or FROZ in lg[1]):
                    legs.append(
                        (
                            t.date(),
                            "long" if FROZ in lg[0] else "short",
                            round(float(sig.at[t, FROZ]), 4),
                        )
                    )
        print(
            f"  X1: formowania po D z {FROZ} w nodze (data, noga, sygnał 28 d): {len(legs)}; pierwsze {legs[:4]}; ostatnie {legs[-3:]}"
        )

        print(SEP)
        print(
            "4. ŚWIEŻY KATALOG DANYCH: plik wycofanej monety znika (np. nowa maszyna, `fetch_live` pobiera tylko TRADING)"
        )
        src, jdir = root / "wycofanie", root / "dz_wycofanie"
        (src / f"{DEAD}_1d.parquet").unlink()
        (src / f"{DEAD}_funding.parquet").unlink()
        lj.run(fetch=False, live_dir=src, journal_dir=jdir)
        print(f"  drugi przebieg bez pliku {DEAD}: {log_fields(jdir)}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
