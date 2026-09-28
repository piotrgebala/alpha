"""
druga_droga.py — bramka 16a rundy OS1 (CLAUDE.md zasada 16; docs/skills/bramki-jakosci.md A3):
niezależne przeliczenie kluczowych liczb rachunku mierzalności.

NIEZALEŻNE od kodu rundy: nie importuje backtest.run_os1_otwarcia, backtest.metrics, backtest.costs
ani backtest.checkpoint_lib. Parquet czytany wprost; godziny otwarć ze stref IANA przez zoneinfo
(dzień po dniu, bez pandas.tz_localize); dni robocze własną pętlą po datach i drugi raz przez
numpy.busday_count; koszty wprost z config/settings.yaml (sekcja `costs`); wzory wpisane ręcznie.

Liczy WYŁĄCZNIE wielkości bez kierunku: liczby dni i transakcji, średni i medianę |zwrotu| okna,
próg p*, połowę szerokości przedziału, wymaganą trafność. NIE liczy średnich zwrotów ze znakiem,
odchyleń z danych ani trafności reguł — runda ich celowo nie zna (policzenie = zużycie wariantu).
Rachunek zależny od odchylenia (prior F1, „druga miara”) idzie na σ przepisanych z raw_output.txt.

    PYTHONPATH=. .venv/bin/python runs/2026-09-28_os1-otwarcia-sesji/druga_droga.py \
        > runs/2026-09-28_os1-otwarcia-sesji/druga_droga.txt
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "data/raw/BTC-USDT-USDT_30m_20210101T000000Z_20260701T000000Z.parquet"
SETTINGS = ROOT / "config/settings.yaml"
KROK = 30  # minut
Z = 1.96
SESJE = {
    "tokio": ("Asia/Tokyo", 9, 0),
    "londyn": ("Europe/London", 8, 0),
    "nowy_jork": ("America/New_York", 9, 30),
}
F1_OKNO, F2_SYGNAL, F2_POZYCJA = (0, 60), (0, 30), (30, 240)  # [od, do) minut od otwarcia
F1_ROZBIEG, F1_WSTECZ = 65, timedelta(days=365)
DRYF_F1, RHO_F2 = 0.0007, math.sqrt(0.0144)  # priory z pre-rejestracji
# Liczby rundy przepisane z raw_output.txt — tylko do porównania (σ także do arytmetyki priorów).
R_N = {"F1": 1368, "F2": 1433}
R_B = {
    "F1": {"tokio": 0.4791, "londyn": 0.3940, "nowy_jork": 0.6889},
    "F2": {"tokio": 0.8448, "londyn": 0.7011, "nowy_jork": 1.1276},
}
R_MED = {
    "F1": {"tokio": 0.3085, "londyn": 0.2465, "nowy_jork": 0.4797},
    "F2": {"tokio": 0.5097, "londyn": 0.4291, "nowy_jork": 0.7810},
}
R_SIG = {
    "F1": {"tokio": 0.7335, "londyn": 0.6926, "nowy_jork": 0.9915},
    "F2": {"tokio": 1.2935, "londyn": 1.1264, "nowy_jork": 1.6301},
}
R_GODZ = {
    "tokio": {"00:00": 1433},
    "londyn": {"07:00": 832, "08:00": 601},
    "nowy_jork": {"13:30": 932, "14:30": 501},
}
R_RAZEM = {  # n, B %, p* taker, p* limit, ± pp, wymagana taker, wymagana limit
    "F1": (4104, 0.5206, 63.44, 58.64, 1.53, 64.97, 60.17),
    "F2": (4299, 0.8912, 57.85, 55.05, 1.49, 59.35, 56.54),
}
R_WYM = {  # wymagana taker / limit per sesja
    "F1": {"tokio": (67.26, 62.04), "londyn": (70.42, 64.07), "nowy_jork": (62.81, 59.18)},
    "F2": {"tokio": (60.88, 57.92), "londyn": (62.57, 59.01), "nowy_jork": (58.80, 56.58)},
}


def zgodnosc(moje: float, runda: float, miejsca: int) -> str:
    return (
        "zgodne"
        if round(moje, miejsca) == round(runda, miejsca)
        else f"RÓŻNICA ({moje:.{miejsca + 2}f})"
    )


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def main() -> None:
    cfg = yaml.safe_load(SETTINGS.read_text(encoding="utf-8"))
    start, end = pd.Timestamp(cfg["data"]["min_start"]), pd.Timestamp(cfg["data"]["end"])
    k = cfg["costs"]
    slip = k["slippage_bps"] / 1e4
    koszty = {
        "taker": 2 * (k["taker_fee_rate"] + slip),
        "limit": k["maker_fee_rate"] + k["taker_fee_rate"] + slip,
    }

    df = pd.read_parquet(PARQUET)
    df = df.loc[(df["timestamp"] >= start) & (df["timestamp"] < end)].reset_index(drop=True)
    minuty = (
        (df["timestamp"] - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(minutes=1)
    ).to_numpy()
    m0, m1 = int(start.timestamp()) // 60, int(end.timestamp()) // 60
    siatka = set(range(m0, m1, KROK))
    pozycja = {int(m): i for i, m in enumerate(minuty)}
    o, c, v = df["open"].to_numpy(), df["close"].to_numpy(), df["volume"].to_numpy()
    print(
        f"parquet po filtrze [{start:%Y-%m-%d}, {end:%Y-%m-%d}): {len(df)} świec; duplikaty {len(minuty) - len(pozycja)}; "
        f"poza siatką {int(np.sum(minuty % KROK != 0))}; brakujących w siatce {len(siatka - set(pozycja))}; "
        f"NaN open/close {int(df[['open', 'close']].isna().sum().sum())}; wolumen 0: {int((v == 0).sum())}; "
        f"high == low: {int((df['high'] == df['low']).sum())} (znaczniki: {sorted(set(df.loc[(v == 0) | (df['high'] == df['low']), 'timestamp'].astype(str)))})"
    )
    print(
        f"koszty z settings.yaml: taker/taker {koszty['taker']:.4%}, limit na wejściu {koszty['limit']:.4%}"
    )

    ost = (end - pd.Timedelta(minutes=1)).date()
    dni, d = [], start.date()
    while d <= ost:
        if d.weekday() < 5:
            dni.append(d)
        d += timedelta(days=1)
    bus = int(np.busday_count(start.date(), ost + timedelta(days=1)))
    kal = (ost - start.date()).days + 1
    print(
        f"dni kalendarzowe {kal}; pon–pt pętlą {len(dni)}, numpy.busday_count {bus}; weekendy poza zbiorem {kal - len(dni)}"
    )

    def okno(mm: int, a: int, b: int) -> tuple[float | None, int]:
        """|zwrot| od open świecy mm+a do close świecy mm+b−30; None przy brakującej świecy. Plus liczba świec z wolumenem 0."""
        idx = [pozycja.get(mm + x) for x in range(a, b, KROK)]
        if any(i is None for i in idx) or not (np.isfinite(o[idx[0]]) and np.isfinite(c[idx[-1]])):
            return None, 0
        return abs(c[idx[-1]] / o[idx[0]] - 1.0), int(sum(v[i] == 0 for i in idx))

    wyn, otwarcia = {}, {}
    for s, (tz, hh, mi) in SESJE.items():
        otw = [
            datetime(x.year, x.month, x.day, hh, mi, tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)
            for x in dni
        ]
        otwarcia[s] = otw
        godz = dict(sorted(Counter(t.strftime("%H:%M") for t in otw).items()))
        f1_abs, f1_dni, f2_abs, zero_vol = [], [], [], 0
        for x, t in zip(dni, otw, strict=True):
            mm = int(t.timestamp()) // 60
            a1, z1 = okno(mm, *F1_OKNO)
            sg, zs = okno(mm, *F2_SYGNAL)
            a2, z2 = okno(mm, *F2_POZYCJA)
            zero_vol += z1 + zs + z2
            if a1 is not None:
                f1_abs.append(a1)
                f1_dni.append(x)
            if a2 is not None and sg is not None:
                f2_abs.append(a2)
        # F1: transakcja, gdy ≥ 65 ważnych dni w [D − 365 dni, D) — własne dwa wskaźniki zamiast rolling
        lo, handel = 0, []
        for j, x in enumerate(f1_dni):
            while f1_dni[lo] < x - F1_WSTECZ:
                lo += 1
            handel.append(j - lo >= F1_ROZBIEG)
        f1_handel_abs = [a for a, h in zip(f1_abs, handel, strict=True) if h]
        pierwszy = f1_dni[handel.index(True)]
        wyn[s] = {"F1": (sum(handel), f1_abs, f1_handel_abs), "F2": (len(f2_abs), f2_abs, f2_abs)}
        print(
            f"\n[{s}] dni {len(dni)}; otwarcia UTC {godz} — runda {R_GODZ[s]}: {'zgodne' if godz == R_GODZ[s] else 'RÓŻNICA'}; "
            f"świec z wolumenem 0 w oknach: {zero_vol}"
        )
        for f in ("F1", "F2"):
            n, pelne, _ = wyn[s][f]
            b, med = 100 * np.mean(pelne), 100 * np.median(pelne)
            print(
                f"  {f}: dni z pełnym oknem {len(pelne)}, transakcji {n} (runda {R_N[f]}: {'zgodne' if n == R_N[f] else 'RÓŻNICA'}); "
                f"B {b:.4f}% ({zgodnosc(b, R_B[f][s], 4)}), mediana |r| {med:.4f}% ({zgodnosc(med, R_MED[f][s], 4)}), "
                f"mediana niższa od średniej o {1 - med / b:.1%}"
                + (f"; pierwsza transakcja F1 {pierwszy}" if f == "F1" else "")
            )

    print(
        "\n=== Rachunek (wzory ręcznie: p* = 0,5·(1 + C/B); ± = 1,96·√(0,25/n); wymagana = p* + ±) ==="
    )
    for f in ("F1", "F2"):
        for s in list(SESJE) + ["RAZEM"]:
            grupa = list(SESJE) if s == "RAZEM" else [s]
            n = sum(wyn[g][f][0] for g in grupa)
            b = float(
                np.mean([a for g in grupa for a in wyn[g][f][1]])
            )  # średnia z puli, nie średnia średnich
            hw = Z * math.sqrt(0.25 / n)
            ps = {kk: 0.5 * (1 + cc / b) for kk, cc in koszty.items()}
            wym = {kk: 100 * (p + hw) for kk, p in ps.items()}
            cb = koszty["taker"] / b
            linia = (
                f"{f} {s:9s} n {n:5d} | B {100 * b:.4f}% | C/B taker {cb:.1%} | p* taker {100 * ps['taker']:.4f}% limit "
                f"{100 * ps['limit']:.4f}% | ± {100 * hw:.4f} pp | wymagana taker {wym['taker']:.4f}% limit {wym['limit']:.4f}%"
            )
            if s == "RAZEM":
                rn, rb, rpt, rpl, rhw, rwt, rwl = R_RAZEM[f]
                linia += (
                    f"\n    vs runda: n {'zgodne' if n == rn else 'RÓŻNICA'}, B {zgodnosc(100 * b, rb, 4)}, "
                    f"p* {zgodnosc(100 * ps['taker'], rpt, 2)}/{zgodnosc(100 * ps['limit'], rpl, 2)}, "
                    f"± {zgodnosc(100 * hw, rhw, 2)}, wymagana {zgodnosc(wym['taker'], rwt, 2)}/{zgodnosc(wym['limit'], rwl, 2)}"
                    f"; zaokrąglone do 0,1: p* {100 * ps['taker']:.1f}/{100 * ps['limit']:.1f}, wymagana "
                    f"{wym['taker']:.1f}/{wym['limit']:.1f}"
                )
            else:
                rt, rl = R_WYM[f][s]
                linia += (
                    f"  [vs runda {zgodnosc(wym['taker'], rt, 2)}/{zgodnosc(wym['limit'], rl, 2)}]"
                )
            print(linia)

    print(
        "\n=== Priory i „druga miara” (arytmetyka na σ z raw_output.txt; σ NIE liczone tu z danych) ==="
    )
    p2 = 0.5 + math.asin(RHO_F2) / math.pi
    p1 = {s: phi(DRYF_F1 / (R_SIG["F1"][s] / 100)) for s in SESJE}
    p1_lap = {s: 1 - 0.5 * math.exp(-DRYF_F1 / float(np.mean(wyn[s]["F1"][1]))) for s in SESJE}
    print(f"F2 ρ {RHO_F2:.3f} → 0,5 + arcsin(ρ)/π = {100 * p2:.3f}%")
    print(
        "F1 Φ(0,0007/σ): "
        + ", ".join(f"{s} {100 * p:.3f}%" for s, p in p1.items())
        + f"; RAZEM {100 * np.mean(list(p1.values())):.3f}% (runda 53,55 %, README 53,6 %)"
    )
    print(
        "F1 wrażliwość na grube ogony (Laplace, b = średni |r|: 1 − 0,5·e^(−μ/b)): "
        + ", ".join(f"{s} {100 * p:.2f}%" for s, p in p1_lap.items())
        + f"; RAZEM {100 * np.mean(list(p1_lap.values())):.2f}%"
        + " (stosunek mediana/średnia |r|: normalny 0,845, Laplace 0,693)"
    )
    sig = math.sqrt(np.mean([(x / 100) ** 2 for x in R_SIG["F2"].values()]))
    se = sig / math.sqrt(4299)
    brutto = RHO_F2 * sig * math.sqrt(2 / math.pi)
    print(
        f"F2 RAZEM: σ z puli {100 * sig:.4f}%, σ·√(2/π) {100 * sig * math.sqrt(2 / math.pi):.4f}%; brutto z prioru {100 * brutto:.5f}% "
        f"vs próg t=1,96 limit {100 * (koszty['limit'] + Z * se):.5f}% / taker {100 * (koszty['taker'] + Z * se):.5f}%; "
        f"moc 80 % (2,8·se) {100 * (koszty['limit'] + 2.8 * se):.4f}% / {100 * (koszty['taker'] + 2.8 * se):.4f}%"
    )
    gm = min(
        (
            (otwarcia["nowy_jork"][i] - otwarcia["londyn"][i]).total_seconds() / 60 - 240
            for i in range(len(dni))
        ),
        default=0,
    )
    fund = {s: sum(t.hour in (0, 8, 16) and t.minute == 0 for t in otwarcia[s]) for s in SESJE}
    rozjazd = sum(
        a.strftime("%H:%M") == "08:00" and b.strftime("%H:%M") == "13:30"
        for a, b in zip(otwarcia["londyn"], otwarcia["nowy_jork"], strict=True)
    )
    print(
        f"\nKogo nie ma / co się nakłada: najmniejsza przerwa koniec okna Londynu → otwarcie NY {gm:.0f} min (bez nakładania: {gm > 0}); "
        f"dni rozjazdu czasu letniego USA/UK (Londyn 08:00 + NY 13:30 UTC) {rozjazd}; otwarcia w godzinie fundingu Binance "
        f"(00/08/16 UTC): {fund}"
    )


if __name__ == "__main__":
    main()
