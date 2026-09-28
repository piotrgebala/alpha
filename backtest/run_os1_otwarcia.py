"""
run_os1_otwarcia.py — runda OS1 (pomysł użytkownika 2026-09-28): czy na otwarciach sesji — Tokio 09:00 JST,
Londyn 08:00 czasu lokalnego, Nowy Jork 09:30 ET (czas letni/zimowy przez strefy IANA) — BTC perp daje ruch
kierunkowy, na którym prosta reguła zarabia po kosztach. Pre-rejestracja: runs/2026-09-28_os1-otwarcia-sesji/README.md.

    PYTHONUTF8=1 py -m backtest.run_os1_otwarcia --moc

Neutralny reporter rachunku mierzalności (CLAUDE.md zasada 18) na natywnych świecach 30m od 2021-01-01:
liczba dni roboczych z pełnym oknem, rozrzut ruchu w oknach reguł (odchylenie, średni i mediana ruchu bez
znaku), próg opłacalności, szerokość przyrządu i wymagana trafność. Skrypt NIE liczy średnich zwrotów, trafności
ani wyniku reguł — pełny pomiar wymagałby werdyktu MIERZALNA i osobnego przebiegu.
"""

from __future__ import annotations

import math
import sys
from statistics import NormalDist

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import fetch_window, load_config
from backtest.costs import MAKER, round_trip_cost_fraction
from backtest.metrics import break_even_hit_rate, measurability_report, wald_half_width

TIMEFRAME = "30m"
STEP = pd.Timedelta(minutes=30)
# Sesja → (strefa IANA, godzina otwarcia czasu lokalnego). Dni: pon–pt, bez kalendarza świąt giełdowych.
SESSIONS = {
    "tokio": ("Asia/Tokyo", "09:00"),
    "londyn": ("Europe/London", "08:00"),
    "nowy_jork": ("America/New_York", "09:30"),
}
F1_MINUTES = 60  # F1 „dryf otwarcia”: pozycja [otwarcie, +60 min]
F2_SIGNAL_MINUTES = 30  # F2 „momentum otwarcia”: kierunek z [otwarcie, +30 min] ...
F2_EXIT_MINUTES = 240  # ... trzymanie [+30 min, +240 min]
F1_LOOKBACK_DAYS = 365  # znak F1 = znak średniej tego samego okna z poprzednich 365 dni
F1_MIN_OBS = 65  # ≈ 91 dni kalendarzowych dni roboczych przed pierwszą transakcją F1
# Priory z literatury (README, „Pre-rejestracja”): górne granice, nie oczekiwania.
F1_PRIOR_DRIFT = (
    0.0007  # 0,07 %/h — najlepsza z 24 godzin (22:00 UTC, Padysak–Vojtko), NIE otwarcie sesji
)
F2_PRIOR_RHO = math.sqrt(
    0.0144
)  # R² 1,44 % pierwszej półgodziny doby (Shen–Urquhart–Wang 2022, in-sample)
CONVENTION_P = 0.56  # konwencja projektu (A1/A2/Y1/MX1), nie pomiar


def session_opens(days: pd.DatetimeIndex, tz: str, hhmm: str) -> pd.DatetimeIndex:
    """Otwarcie sesji w UTC dla każdego dnia kalendarzowego `days` (czas lokalny `hhmm` w strefie `tz`)."""
    local = pd.to_datetime([f"{d:%Y-%m-%d} {hhmm}" for d in days]).tz_localize(tz)
    return local.tz_convert("UTC")


def window_return(
    open_: pd.Series, close: pd.Series, starts: pd.DatetimeIndex, begin_min: int, end_min: int
) -> pd.Series:
    """Zwrot od otwarcia świecy `start+begin_min` do zamknięcia świecy kończącej się w `start+end_min`.

    Dzień z brakującą którąkolwiek świecą okna = NaN (bez uzupełniania).
    """
    need = [pd.Timedelta(minutes=m) for m in range(begin_min, end_min, 30)]
    ok = np.ones(len(starts), dtype=bool)
    for off in need:
        ok &= (starts + off).isin(open_.index)
    first = open_.reindex(starts + pd.Timedelta(minutes=begin_min)).to_numpy()
    last = close.reindex(starts + pd.Timedelta(minutes=end_min) - STEP).to_numpy()
    r = pd.Series(last / first - 1.0, index=starts)
    return r.where(ok)


def f1_tradable_days(valid: pd.Series) -> int:
    """Dni, w których F1 ma ≥ F1_MIN_OBS ważnych obserwacji w poprzednich F1_LOOKBACK_DAYS dniach."""
    idx = valid.index[valid.to_numpy()]
    counts = pd.Series(1.0, index=idx).rolling(f"{F1_LOOKBACK_DAYS}D", closed="left").count()
    return int((counts >= F1_MIN_OBS).sum())


def dispersion(r: pd.Series) -> dict:
    a = r.dropna()
    return {
        "n": len(a),
        "std": float(a.std(ddof=1)),
        "mabs": float(a.abs().mean()),
        "medabs": float(a.abs().median()),
    }


def main(argv: list[str]) -> int:
    if "--moc" not in argv:
        print("użycie: py -m backtest.run_os1_otwarcia --moc")
        return 2
    cfg = load_config()
    data_cfg = dict(cfg["data"])
    data_cfg["timeframe_start_overrides"] = {
        **(data_cfg.get("timeframe_start_overrides") or {}),
        TIMEFRAME: data_cfg["min_start"],
    }
    df = fetch_window(data_cfg, TIMEFRAME)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    open_ = pd.Series(df["open"].to_numpy(), index=ts)
    close = pd.Series(df["close"].to_numpy(), index=ts)
    full = pd.date_range(ts.min(), ts.max(), freq=STEP)
    print(
        f"świece {TIMEFRAME}: {len(df)} od {ts.min()} do {ts.max()}; brakujących w siatce: {len(full.difference(ts))}"
    )

    last_day = (ts.max() - pd.Timedelta(minutes=F2_EXIT_MINUTES)).normalize().tz_localize(None)
    days = pd.bdate_range(ts.min().normalize().tz_localize(None), last_day)
    costs = {
        "taker/taker": round_trip_cost_fraction(),
        "maker wejście": round_trip_cost_fraction(entry_leg=MAKER),
    }
    print(
        f"dni robocze (pon–pt): {len(days)}; koszt obrotu: "
        + ", ".join(f"{k} {v:.4%}" for k, v in costs.items())
    )

    rows = []
    for name, (tz, hhmm) in SESSIONS.items():
        starts = session_opens(days, tz, hhmm)
        hours = pd.Series(starts.strftime("%H:%M")).value_counts().to_dict()
        r1 = window_return(open_, close, starts, 0, F1_MINUTES)
        r2 = window_return(open_, close, starts, F2_SIGNAL_MINUTES, F2_EXIT_MINUTES)
        sig = window_return(open_, close, starts, 0, F2_SIGNAL_MINUTES)
        d1, d2 = dispersion(r1), dispersion(r2)
        n2 = int((r2.notna() & sig.notna()).sum())
        n1 = f1_tradable_days(r1.notna())
        print(f"\n[{name}] otwarcia w UTC: {hours}")
        for lab, d, n in (("F1 okno 60 min", d1, n1), ("F2 trzymanie 3,5 h", d2, n2)):
            print(
                f"  {lab}: dni z pełnym oknem {d['n']}, transakcji {n}; odchylenie {d['std']:.4%}, "
                f"średni ruch bez znaku {d['mabs']:.4%}, mediana bez znaku {d['medabs']:.4%}"
            )
        rows.append({"sesja": name, "F1": (n1, d1), "F2": (n2, d2)})

    print(
        "\n=== Rachunek mierzalności (zasada 18; brama z = 1,96; N_eff przyjęte = n — górna granica) ==="
    )
    p1_prior = {s["sesja"]: NormalDist().cdf(F1_PRIOR_DRIFT / s["F1"][1]["std"]) for s in rows}
    p2_prior = 0.5 + math.asin(F2_PRIOR_RHO) / math.pi
    print(
        f"prior F2: ρ {F2_PRIOR_RHO:.3f} → trafność {p2_prior:.2%}; prior F1 (0,07 %/h): "
        + ", ".join(f"{k} {v:.2%}" for k, v in p1_prior.items())
        + f"; konwencja {CONVENTION_P:.0%}"
    )
    for formula in ("F1", "F2"):
        groups = [(s["sesja"], [s]) for s in rows] + [("RAZEM (3 sesje)", rows)]
        for label, group in groups:
            n = sum(g[formula][0] for g in group)
            w = [g[formula][0] for g in group]
            mabs = float(np.average([g[formula][1]["mabs"] for g in group], weights=w))
            std = float(np.sqrt(np.average([g[formula][1]["std"] ** 2 for g in group], weights=w)))
            hw = wald_half_width(n)
            se = std / math.sqrt(n)
            if formula == "F1":
                prior = float(np.average([p1_prior[g["sesja"]] for g in group], weights=w))
                gross_prior = F1_PRIOR_DRIFT
            else:
                prior = p2_prior
                gross_prior = F2_PRIOR_RHO * std * math.sqrt(2 / math.pi)
            for cname, c in costs.items():
                pstar = break_even_hit_rate(c, mabs)
                verdicts = {
                    lab: measurability_report(p, pstar, n)["verdict"]
                    for lab, p in (("prior", prior), ("56%", CONVENTION_P))
                }
                print(
                    f"{formula} {label:16s} {cname:13s} n {n:5d} | B {mabs:.4%} p* {pstar:.2%} ±{hw:.2%} "
                    f"→ wymagana {pstar + hw:.2%} | prior {prior:.2%}: {verdicts['prior']} | 56 %: {verdicts['56%']} "
                    f"| zwrot: brutto z prioru {gross_prior:.4%}, próg t=1,96 {c + 1.96 * se:.4%}, moc 80 % {c + 2.8 * se:.4%}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
