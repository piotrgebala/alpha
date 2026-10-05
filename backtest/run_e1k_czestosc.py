"""
run_e1k_czestosc.py — runda E1K (zadanie 011): realna częstość kaskad likwidacji według karty
`runs/DRAFT_E1.md` (definicja: `backtest/e1_kaskady.py`, commit części A `580092c`) i rachunek
mierzalności (CLAUDE.md zasada 18). 0 wariantów, 0 odczytów E1.

Czyta WYŁĄCZNIE liczniki likwidacji: czas, symbol, stronę i nominał (`data/liquidation_index.parse_line`).
Żadnej ceny po likwidacji, żadnych świec, żadnego zwrotu. Rozrzut zwrotu σ i efekt μ to założenia
z mapy 007 i zadania 026 (karta §9), nie pomiary.

    PYTHONUTF8=1 py -m backtest.run_e1k_czestosc --bybit ~/likwidacje_bybit --binance ~/likwidacje \
        --koszyk dziennik/koszyk.csv --do 2026-10-05
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from scipy import stats

from backtest import e1_kaskady as e1
from backtest.metrics import break_even_hit_rate, expected_trades, measurability_report
from data import liquidation_index as li

DAY_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")
DAY_MS = 86_400_000
GAP_MS = 15 * 60 * 1000  # przerwa w strumieniu wartą odnotowania
Z = 1.959963984540054
Z80 = 0.8416212335729143

# karta §9 — scenariusze zapisane z góry
MU_BASE, SIGMA_BASE, C_BASE = 0.0075, 0.05, 0.005
MUS = (0.0, 0.005, 0.0075, 0.010, 0.013)
SIGMAS = (0.05, 0.08)
COSTS = (0.003, 0.005, 0.010)
RHO = 0.6
HORIZONS_Y = (1, 2, 3, 5)
REASONABLE_Y = 3


@dataclass
class Load:
    events: list[e1.Liq]
    first_ms: int
    end_ms: int  # koniec ostatniego zamkniętego dnia
    lines: int
    bad: int
    cm_skipped: int
    days: list[str]


def closed_day_files(d: Path, until: str) -> list[tuple[str, Path]]:
    out = []
    for p in sorted(d.iterdir()):
        m = DAY_FILE.match(p.name)
        if m and m.group(1) < until:
            out.append((m.group(1), p))
    return out


def load(gielda: str, d: Path, until: str) -> Load:
    evs: list[e1.Liq] = []
    lines = bad = cm = 0
    files = closed_day_files(d, until)
    for _, p in files:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                lines += 1
                try:
                    ev = li.parse_line(gielda, line)
                except ValueError:
                    bad += 1
                    continue
                if ev.market != "UM":
                    cm += 1
                    continue
                evs.append(e1.Liq(ev.symbol, ev.t_ms, ev.side, ev.notional))
    if not evs:
        raise SystemExit(f"{gielda}: BRAK DANYCH w {d}")
    last_day = dt.datetime.strptime(files[-1][0], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
    end_ms = int(last_day.timestamp() * 1000) + DAY_MS
    return Load(evs, min(e.t_ms for e in evs), end_ms, lines, bad, cm, [f for f, _ in files])


def iso(t_ms: int) -> str:
    return dt.datetime.fromtimestamp(t_ms / 1000, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def gaps(evs: list[e1.Liq], first: int, end: int) -> list[tuple[int, int]]:
    ts = sorted(e.t_ms for e in evs)
    out = []
    prev = first
    for t in ts + [end]:
        if t - prev > GAP_MS:
            out.append((prev, t))
        prev = max(prev, t)
    return out


def max_ratio(evs: list[e1.Liq], thr) -> list[tuple[float, str, str, int]]:
    """Największa suma strony w oknie (t − W, t] / próg — per moneta i strona (opis bliskości progu)."""
    per: dict[tuple[str, str], list[e1.Liq]] = {}
    for e in evs:
        if (e1.month_of(e.t_ms), e.symbol) in thr:
            per.setdefault((e.symbol, e.side), []).append(e)
    out = []
    for (sym, side), xs in per.items():
        xs.sort(key=lambda e: e.t_ms)
        best, best_t, lo, run = 0.0, 0, 0, 0.0
        for x in xs:
            run += float(x.notional)
            while xs[lo].t_ms <= x.t_ms - e1.WINDOW_MS:
                run -= float(xs[lo].notional)
                lo += 1
            r = run / float(thr[(e1.month_of(x.t_ms), sym)])
            if r > best:
                best, best_t = r, x.t_ms
        out.append((best, sym, side, best_t))
    return sorted(out, reverse=True)


def poisson_ci(k: int, conf: float = 0.95) -> tuple[float, float]:
    a = 1 - conf
    lo = 0.0 if k == 0 else stats.chi2.ppf(a / 2, 2 * k) / 2
    hi = stats.chi2.ppf(1 - a / 2, 2 * k + 2) / 2
    return lo, hi


def sigma_day(sigma: float, k: float, rho: float = RHO) -> float:
    k = max(k, 1.0)
    return sigma * math.sqrt((1 + (k - 1) * rho) / k)


def generalized_p_star(mu: float, s: float, c: float) -> tuple[float, float]:
    """(p, p*) dla zwrotu brutto N(mu, s): p = P(r > 0), p* = (L̄ + C)/(W̄ + L̄)."""
    a = mu / s
    p = stats.norm.cdf(a)
    phi = stats.norm.pdf(a)
    w = mu + s * phi / p
    lo = -mu + s * phi / (1 - p)
    return float(p), float((lo + c) / (w + lo))


def simple_p_star(s: float, c: float) -> float:
    """Uproszczony próg 0,5(1 + C/B) z B = E|r| przy μ = 0 (σ·√(2/π)) — tylko do testu granicy."""
    return break_even_hit_rate(c, s * math.sqrt(2 / math.pi))


def required_n(mu: float, s: float, c: float, z_power: float = 0.0) -> float:
    net = mu - c
    if net <= 0:
        return math.inf
    return ((Z + z_power) * s / net) ** 2


def universe_thr(universe):
    return e1.thresholds(universe)


def describe(name: str, ld: Load, casc: list[e1.Cascade], universe, out) -> dict:
    span_d = (ld.end_ms - ld.first_ms) / DAY_MS
    days = Counter(c.day for c in casc)
    n_c = len(casc)
    n_d = len(days)
    k_bar = n_c / n_d if n_d else float("nan")
    lo, hi = poisson_ci(n_c)
    lo_d, hi_d = poisson_ci(n_d)
    out(f"\n=== {name} ===")
    out(f"pliki dni zamkniętych: {ld.days[0]} … {ld.days[-1]} ({len(ld.days)})")
    out(f"okres: {iso(ld.first_ms)} → {iso(ld.end_ms)} UTC = {span_d:.3f} dnia")
    out(
        f"linie {ld.lines}, złe {ld.bad}, odwrotne (CM, pominięte) {ld.cm_skipped}, liniowe {len(ld.events)}"
    )
    months = sorted({m for m, _ in universe})
    for m in months:
        mem = sorted(s for mm, s in universe if mm == m)
        t0 = int(
            dt.datetime.strptime(m, "%Y-%m").replace(tzinfo=dt.timezone.utc).timestamp() * 1000
        )
        seen = {e.symbol for e in ld.events if e1.month_of(e.t_ms) == m}
        if not any(e1.month_of(e.t_ms) == m for e in ld.events):
            continue
        missing = [s for s in mem if s not in seen]
        n_in = sum(1 for e in ld.events if e1.month_of(e.t_ms) == m and e.symbol in mem)
        out(
            f"uniwersum {m}: {len(mem)} monet, z likwidacjami w danych {len(mem) - len(missing)}, "
            f"bez żadnej likwidacji: {missing or '—'}; likwidacji w uniwersum {n_in}"
        )
        _ = t0
    g = gaps(ld.events, ld.first_ms, ld.end_ms)
    out(f"przerwy > 15 min bez żadnej likwidacji (cały rynek): {len(g)}")
    for a, b in g:
        out(f"  {iso(a)} → {iso(b)} ({(b - a) / 60000:.0f} min)")
    mr = max_ratio(ld.events, universe_thr(universe))
    out("największa suma w oknie 60 min / próg (5 najbliższych progu par moneta–strona):")
    for r, sym, side, t in mr[:5]:
        out(f"  {sym:<14} {side:<5} {r:.3f} ({iso(t)})")
    out(
        f"par moneta–strona z ilorazem ≥ 0,5: {sum(1 for r, *_ in mr if r >= 0.5)}, ≥ 0,25: "
        f"{sum(1 for r, *_ in mr if r >= 0.25)}, wszystkich: {len(mr)}"
    )
    out(
        f"KASKADY: {n_c} (95 % Poisson [{lo:.1f}; {hi:.1f}]), dni z ≥ 1 kaskadą: {n_d} [{lo_d:.1f}; {hi_d:.1f}]"
    )
    if n_c:
        out(
            f"  na dzień obserwacji: {n_c / span_d:.3f}; na rok: {365 * n_c / span_d:.0f} "
            f"[{365 * lo / span_d:.0f}; {365 * hi / span_d:.0f}]"
        )
        out(
            f"  dni z kaskadą na rok: {365 * n_d / span_d:.0f} [{365 * lo_d / span_d:.0f}; {365 * hi_d / span_d:.0f}]; "
            f"średnio {k_bar:.2f} kaskady na taki dzień; na miesiąc (30 d): {30 * n_c / span_d:.0f}"
        )
        out(f"  strona zlikwidowana: {dict(Counter(c.side for c in casc))}")
        out(f"  monety: {dict(Counter(c.symbol for c in casc).most_common())}")
        out(f"  dni: {dict(sorted(days.items()))}")
        ratios = sorted(float(c.window_notional / c.threshold) for c in casc)
        out(
            f"  suma w oknie / próg w chwili t*: min {ratios[0]:.3f}, mediana {ratios[len(ratios) // 2]:.3f}, "
            f"maks {ratios[-1]:.3f}"
        )
        for c in casc:
            out(
                f"    {iso(c.t_ms)} {c.symbol:<14} {c.side:<5} kier {c.direction:+d} "
                f"okno {float(c.window_notional):>14,.0f} próg {float(c.threshold):>12,.0f}"
            )
    return {"n_c": n_c, "n_d": n_d, "span": span_d, "k": k_bar, "lo_d": lo_d, "hi_d": hi_d}


def measurability(st_: dict, out) -> None:
    f = st_["n_d"] / st_["span"]  # udział dni z kaskadą (dni obserwacji z ułamkiem)
    rate_d = 365 * f
    rate_lo = 365 * st_["lo_d"] / st_["span"]
    rate_hi = 365 * st_["hi_d"] / st_["span"]
    k = st_["k"] if st_["n_d"] else 1.0
    out("\n=== RACHUNEK MIERZALNOŚCI (karta §9; Bybit) ===")
    out(
        f"udział dni z kaskadą f = {f:.4f} → abstynencja 1 − f = {1 - f:.4f}; k̄ = {k:.2f}; ρ = {RHO}"
    )
    out(f"dni z kaskadą na rok: {rate_d:.0f} (Poisson 95 %: {rate_lo:.0f} – {rate_hi:.0f})")
    for y in HORIZONS_Y:
        n = expected_trades(int(365 * y), min(max(1 - f, 0.0), 1.0))
        out(f"  expected_trades(n_dni={int(365 * y)}, abstynencja={1 - f:.4f}) = {n:.0f}  ({y} l.)")
    n3 = expected_trades(int(365 * REASONABLE_Y), min(max(1 - f, 0.0), 1.0))
    out(
        f"\nScenariusz rozstrzygający μ {MU_BASE:.2%}, σ {SIGMA_BASE:.0%}, C {C_BASE:.1%} przy n = {n3:.0f} "
        f"(3 lata):"
    )
    for label, mu, sg, c in [("ROZSTRZYGAJĄCY", MU_BASE, SIGMA_BASE, C_BASE)] + [
        ("opis", m, s, cc) for m in MUS for s in SIGMAS for cc in COSTS
    ]:
        sd = sigma_day(sg, k)
        n50 = required_n(mu, sd, c)
        n80 = required_n(mu, sd, c, Z80)
        y50 = n50 / rate_d if rate_d > 0 else math.inf
        y80 = n80 / rate_d if rate_d > 0 else math.inf
        mde3 = c + Z * sd / math.sqrt(n3) if n3 > 0 else math.inf
        p, ps = generalized_p_star(mu, sd, c)
        rep = (
            measurability_report(p, ps, n3)
            if n3 >= 1
            else {"verdict": "N/D", "p_detectable": math.nan}
        )
        ret_ok = (mu - c) > Z * sd / math.sqrt(n3) if n3 > 0 else False
        both = ret_ok and rep["verdict"] == "MIERZALNA"
        out(
            f"  [{label}] μ {mu:.2%} σ {sg:.0%} C {c:.1%}: σ_dnia {sd:.2%}; potrzebne n50 {n50:,.0f} "
            f"(~{y50:,.1f} l.), n80 {n80:,.0f} (~{y80:,.1f} l.); MDE brutto po 3 l. {mde3:.2%}; "
            f"p {p:.4f} p* {ps:.4f} p_wykr(3 l.) {rep['p_detectable']:.4f} → trafność {rep['verdict']}, "
            f"zwrot {'MIERZALNA' if ret_ok else 'NIEMIERZALNA'} ⇒ {'MIERZALNA' if both else 'NIEMIERZALNA'}"
        )
        if label == "ROZSTRZYGAJĄCY":
            out(
                f"    lata przy Poissonie 95 % częstości ({rate_lo:.0f}–{rate_hi:.0f} dni/rok): n50 "
                f"{n50 / rate_hi if rate_hi else math.inf:,.1f} – {n50 / rate_lo if rate_lo else math.inf:,.1f} l.; "
                f"n80 {n80 / rate_hi if rate_hi else math.inf:,.1f} – {n80 / rate_lo if rate_lo else math.inf:,.1f} l."
            )
            out(
                f"    ile dni z kaskadą na rok trzeba, by zdążyć w 3 lata: 50 % mocy {n50 / 3:,.0f}, "
                f"80 % {n80 / 3:,.0f} (rok ma 365)"
            )

    out(
        "\nScenariusz rozstrzygający przy częstości założonej (nie zmierzonej): górna granica Poissona i każdy dzień"
    )
    for lab, rd in (
        ("górna granica 95 %", rate_hi),
        ("365 dni/rok (sufit jednostki „dzień”)", 365.0),
    ):
        for y in HORIZONS_Y:
            n = expected_trades(int(365 * y), min(max(1 - rd / 365, 0.0), 1.0))
            sd = sigma_day(SIGMA_BASE, max(k, 1.0))
            p, ps = generalized_p_star(MU_BASE, sd, C_BASE)
            rep = measurability_report(p, ps, n)
            ret_ok = (MU_BASE - C_BASE) > Z * sd / math.sqrt(n)
            out(
                f"  {lab}: {y} l. → n {n:.0f}; wald_half_width {rep['band_width_pp']:.2f} pp; p {p:.4f} "
                f"p* {ps:.4f} p_wykr {rep['p_detectable']:.4f} → trafność {rep['verdict']}; MDE netto "
                f"{Z * sd / math.sqrt(n):.2%} wobec założonego netto {MU_BASE - C_BASE:.2%} → zwrot "
                f"{'MIERZALNA' if ret_ok else 'NIEMIERZALNA'}"
            )

    out("\n=== GRANICA DUŻEGO n (n = 1 000 000; σ_dnia = 5 %, C = 0,5 %) ===")
    big = 1_000_000
    for mu in (C_BASE - 0.0005, C_BASE + 0.0005, 1.5 * C_BASE, 1.6 * C_BASE):
        p, ps = generalized_p_star(mu, 0.05, C_BASE)
        pss = simple_p_star(0.05, C_BASE)
        r_gen = measurability_report(p, ps, big)["verdict"]
        r_sim = measurability_report(p, pss, big)["verdict"]
        r_ret = "MIERZALNA" if (mu - C_BASE) > Z * 0.05 / math.sqrt(big) else "NIEMIERZALNA"
        out(
            f"  μ {mu:.3%}: p {p:.5f}; p* uogólnione {ps:.5f} → {r_gen}; p* uproszczone {pss:.5f} → {r_sim}; "
            f"zwrot → {r_ret}"
        )
    # μ, przy którym uproszczony próg zaczyna przepuszczać (rozwiązanie numeryczne)
    lo_mu, hi_mu = 0.0, 0.05
    target = simple_p_star(0.05, C_BASE)
    for _ in range(80):
        mid = (lo_mu + hi_mu) / 2
        if stats.norm.cdf(mid / 0.05) > target:
            hi_mu = mid
        else:
            lo_mu = mid
    out(
        f"  uproszczony próg wymaga μ > {hi_mu:.4%} = {hi_mu / C_BASE:.3f} × C (karze cel); uogólniony: μ > C"
    )


def concordance(bybit: list[e1.Cascade], binance: list[e1.Cascade], out) -> None:
    hit = 0
    for c in bybit:
        if any(
            b.symbol == c.symbol and b.side == c.side and abs(b.t_ms - c.t_ms) <= 3_600_000
            for b in binance
        ):
            hit += 1
    out(
        f"\nzgodność: kaskad Bybit z kaskadą Binance (ta sama moneta i strona, ±60 min): {hit}/{len(bybit)}"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bybit", type=Path, required=True)
    ap.add_argument("--binance", type=Path, required=True)
    ap.add_argument("--koszyk", type=Path, required=True)
    ap.add_argument("--do", required=True, help="pierwszy dzień NIEzamknięty (YYYY-MM-DD)")
    a = ap.parse_args(argv)
    out = print
    out("E1K — częstość kaskad (karta runs/DRAFT_E1.md, część A 580092c); 0 cen, 0 odczytów E1")
    out(
        f"W = {e1.WINDOW_MS // 60000} min, θ = {e1.THETA}, H = {e1.HOLD_MS // 3_600_000} h, "
        f"wejście floor_min(t*) + {e1.ENTRY_DELAY_MIN} min"
    )
    universe = e1.load_universe(a.koszyk)
    thr = e1.thresholds(universe)
    out(
        f"koszyk: {a.koszyk} — {len(universe)} par (miesiąc, moneta) top-20, miesiące "
        f"{sorted({m for m, _ in universe})}"
    )
    by = load("bybit", a.bybit, a.do)
    casc_by = e1.detect_cascades(by.events, thr)
    st_by = describe("BYBIT (pełne; źródło sygnału)", by, casc_by, universe, out)
    bn = load("binance", a.binance, a.do)
    casc_bn = e1.detect_cascades(bn.events, thr)
    describe("BINANCE (próbka ≤ 1/s/symbol; tylko dolna granica)", bn, casc_bn, universe, out)
    concordance(casc_by, casc_bn, out)
    measurability(st_by, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
