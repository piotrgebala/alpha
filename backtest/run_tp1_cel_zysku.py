"""
run_tp1_cel_zysku.py — runda TP1 (decyzja użytkownika 2026-09-26: „sprawdź jednak”): wyjście na celu
zysku +1 % / +2 % ceny wejścia („małe zyski, większym wolumenem”) na nogach dziennika z pozycjami
„kup i trzymaj” w fazie — trend TS1 (likwidacja izolowana 2×) i premia Coinbase CP1 (3×) — przy RÓWNYM
RYZYKU: każdy szereg (bez celu i z celem) sterowany zmiennością jak dziennik (R1 na jednym szeregu: cel
20 %/rok, sufit 2, EWMA com 45, krok 7, rozbieg 60). X1 poza rundą (jego silnik co dzień wyrównuje nogi —
README). Silnik: `backtest/take_profit.py`. Pre-rejestracja: runs/2026-09-26_tp1-cel-zysku/README.md.

    PYTHONUTF8=1 py -m backtest.run_tp1_cel_zysku --moc   # szum różnic (bez średnich) i mierzalność

Neutralny reporter rachunku mierzalności (CLAUDE.md zasada 18): bez średnich wyników. Pełny pomiar
(średnie, werdykty) nie jest zaimplementowany — przy wyniku MIERZALNA wymagałby osobnego skryptu.
"""

from __future__ import annotations

import sys
import time
from statistics import NormalDist

import numpy as np
import pandas as pd

from agents.labeling import effective_sample_size
from backtest import run_ts_momentum_ts1 as ts1
from backtest.run_coinbase_cp1 import _load as load_cp
from backtest.sizing import DAYS_PER_YEAR, apply_rules
from backtest.take_profit import cp1_forms, leg_returns, ts1_forms
from backtest.ts_momentum import portfolio

FULL = "data/raw/universe_full"
OHLC_FULL = "data/raw/universe_ohlc_full/ohlc_1d.parquet"
LEV = {"TS1": 2.0, "CP1": 3.0}  # dźwignie dziennika (likwidacja izolowana)
MMR = 0.01
TARGETS = (0.01, 0.02)
M_ARMS = len(LEV) * len(TARGETS)
Z_BONF = NormalDist().inv_cdf(1 - 0.025 / M_ARMS)
Z95 = NormalDist().inv_cdf(0.975)
EFFECT = 0.05  # najmniejsza zmiana warta zmiany reguł dziennika: 5 pkt %/rok przy ryzyku 20 %/rok
SEP = "=" * 104


def load() -> dict:
    """Nogi dziennika na pełnych danych 2021–2026: ceny, funding, składy, znaki, ekstrema dnia."""
    o = pd.read_parquet(OHLC_FULL)
    o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
    high = o.pivot(index="open_time", columns="symbol", values="high")
    low = o.pivot(index="open_time", columns="symbol", values="low")
    fee, close, funding, members, start, end = ts1._load(FULL)
    close = close[close.index < end]
    fee_c, close_c, fund_c, mem_c, signs_c, _prem, start_c, end_c = load_cp()
    close_c = close_c[close_c.index < end_c]
    return {
        "TS1": dict(
            fee=fee,
            close=close,
            funding=funding,
            members=members,
            start=start,
            end=end,
            signs=None,
            forms=ts1_forms(close, members, start, end),
        ),
        "CP1": dict(
            fee=fee_c,
            close=close_c,
            funding=fund_c,
            members=mem_c,
            start=start_c,
            end=end_c,
            signs=signs_c,
            forms=cp1_forms(close_c, signs_c, mem_c, start_c, end_c),
        ),
        "high": high,
        "low": low,
    }


def canonical(name: str, L: dict, high: pd.DataFrame, low: pd.DataFrame) -> pd.Series:
    """Szereg netto z silnika dziennika: `portfolio` z likwidacją izolowaną (CP1 ze znakiem premii)."""
    cols = L["close"].columns
    liq = {
        "high": high.reindex(columns=cols),
        "low": low.reindex(columns=cols),
        "lev": LEV[name],
        "mmr": MMR,
    }
    kw = {"signs_override": L["signs"]} if L["signs"] is not None else {}
    avg, _ = portfolio(
        L["close"], L["funding"], L["members"], L["start"], L["end"], L["fee"], liq=liq, **kw
    )
    return avg.set_index("date")["net"]


def vol_target(r: pd.Series) -> pd.DataFrame:
    """Sterowanie zmiennością jak dziennik (R1 na jednym szeregu) — „większy wolumen” = ta sama zmienność."""
    return apply_rules(r.rename("noga").to_frame(), "R1").set_index("date")


def n_lots(forms_by_phase: list) -> int:
    return int(sum(np.count_nonzero(w) for forms in forms_by_phase for _, w in forms))


def main(argv: list[str]) -> int:
    t0 = time.time()
    print(SEP)
    print(
        "TP1 — wyjście na celu zysku +1 % / +2 % przy równym ryzyku (sterowanie zmiennością jak dziennik)"
    )
    print(SEP)
    data = load()
    print(
        f"ramiona: {list(LEV)} × cel {[f'{100 * t:.0f}%' for t in TARGETS]} = {M_ARMS}; z_{M_ARMS} = {Z_BONF:.3f}; "
        f"efekt istotny praktycznie: {100 * EFFECT:.0f} pkt %/rok; cel i likwidacja w jednej świecy → likwidacja\n"
    )
    arms = []
    print("0. ZGODNOŚĆ silnika bez celu z silnikiem dziennika i mechanika celu (bez średnich)")
    for name in LEV:
        L = data[name]
        series = {
            tp: leg_returns(
                L["close"],
                L["funding"],
                data["low"],
                data["high"],
                L["forms"],
                L["fee"],
                LEV[name],
                MMR,
                tp,
            )
            for tp in (None, *TARGETS)
        }
        ref = canonical(name, L, data["high"], data["low"])
        both = pd.concat([series[None]["net"].rename("a"), ref.rename("b")], axis=1, join="inner")
        print(
            f"  {name}: dni {len(both)}; max |różnica| {float((both['a'] - both['b']).abs().max()):.2e}"
        )
        vt = {tp: vol_target(series[tp]["net"]) for tp in (None, *TARGETS)}
        lots = n_lots(L["forms"])
        for tp in TARGETS:
            s = series[tp]
            print(
                f"     cel {100 * tp:.0f}%: pozycji {lots}, zamkniętych na celu {int(s['tp_exits'].sum())} "
                f"({100 * s['tp_exits'].sum() / lots:.0f}%), likwidacji {int(s['liquidations'].sum())} "
                f"(bez celu {int(series[None]['liquidations'].sum())}); mnożnik k mediana "
                f"{vt[tp]['k_noga'].median():.2f} vs bez celu {vt[None]['k_noga'].median():.2f}; "
                f"k na sufitcie 2 w {100 * (vt[tp]['k_noga'] >= 2.0 - 1e-12).mean():.0f}% dni"
            )
            d = (vt[tp]["ret"] - vt[None]["ret"]).dropna()
            n = len(d)
            n_eff = min(float(effective_sample_size(d)["n_eff"]), float(n))
            se_ann = float(d.std(ddof=1)) / np.sqrt(n_eff) * DAYS_PER_YEAR
            arms.append(
                dict(
                    name=name,
                    tp=tp,
                    n=n,
                    n_eff=n_eff,
                    sd_ann=float(d.std(ddof=1)) * np.sqrt(DAYS_PER_YEAR),
                    corr=float(vt[tp]["ret"].corr(vt[None]["ret"])),
                    hw_bonf=Z_BONF * se_ann,
                    hw95=Z95 * se_ann,
                )
            )

    print(
        "\n1. MIERZALNOŚĆ (zasada 18) — szum dziennej różnicy (cel − bez celu) przy równym ryzyku, BEZ średnich"
    )
    print(
        f"  {'noga':>4} | {'cel':>4} | {'dni':>5} | {'N_eff':>6} | {'korelacja':>9} | {'sd różnicy':>11} | "
        f"{'± (z_4)':>9} | {'± (1,96)':>9} | {'efekt':>6} | werdykt"
    )
    for a in arms:
        verdict = "MIERZALNA" if a["hw_bonf"] < EFFECT else "NIEMIERZALNA"
        years = (EFFECT and (a["hw_bonf"] / EFFECT) ** 2) * a["n"] / DAYS_PER_YEAR
        print(
            f"  {a['name']:>4} | {100 * a['tp']:3.0f}% | {a['n']:5d} | {a['n_eff']:6.0f} | {a['corr']:9.2f} | "
            f"{100 * a['sd_ann']:8.2f}%/r | {100 * a['hw_bonf']:6.2f} pp | {100 * a['hw95']:6.2f} pp | "
            f"{100 * EFFECT:4.0f} pp | {verdict} (potrzeba ~{years:.0f} lat danych)"
        )
    print(f"\n  (bez średnich wyników; czas {time.time() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
