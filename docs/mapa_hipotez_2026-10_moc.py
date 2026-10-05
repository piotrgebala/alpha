"""Rachunek mocy do mapy hipotez (zadanie 007) — BEZ DANYCH RYNKOWYCH, 0 odczytów.

Każda liczba wejściowa pochodzi z repo (wniosek / runda / docs/rag/11) albo jest jawnie
oznaczona jako HOJNE ZAŁOŻENIE (gdy efektu z badań po publikacji nie ma w repo ani w skillu).
Każda liczba mocy jest liczona dwiema drogami:
  droga 1 — funkcja projektu (`measurability_report`, `wald_half_width`) albo wzór analityczny,
  droga 2 — wzór Walda przepisany ręcznie ALBO symulacja Monte Carlo (ziarno stałe).

Uruchomienie (z katalogu głównego klonu, bez sieci):
    .venv/bin/python docs/mapa_hipotez_2026-10_moc.py > docs/mapa_hipotez_2026-10_moc.txt
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest.dsr import min_annual_sr, required_t  # noqa: E402
from backtest.metrics import expected_trades, measurability_report, wald_half_width  # noqa: E402

Z = 1.959963984540054  # 95 % dwustronnie (jak Z_TWO_SIDED_95)
Z80 = norm.ppf(0.80)  # 0,8416 — moc 80 %
RNG = np.random.default_rng(20261001)
REPS = 20_000


def hand_wald(assumed: float, p_star: float, n: float) -> tuple[float, float]:
    """Droga 2 dla trafności: próg wykrywalności p* + 1,96·√(0,25/n), liczony ręcznie."""
    hw = Z * math.sqrt(0.25 / n)
    return p_star + hw, 100.0 * (assumed - (p_star + hw))


def sim_power_hit(p_true: float, p_star: float, n: int) -> float:
    """Symulacja: odsetek prób, w których dolny kraniec Walda (obserwowany) > p*."""
    hits = RNG.binomial(n, p_true, size=REPS)
    p = hits / n
    ci_low = p - Z * np.sqrt(p * (1 - p) / n)
    return float(np.mean(ci_low > p_star))


def power_mean(effect_over_se: float, z: float) -> float:
    """Moc testu jednostronnego średniej: Φ(efekt/se − z)."""
    return float(norm.cdf(effect_over_se - z))


def sim_power_series(sr_annual: float, years: float, z: float, per_year: int = 52) -> float:
    """Symulacja: szereg tygodniowy o rocznym SR, test t > z. Druga droga dla mocy SR."""
    n = int(round(per_year * years))
    mu = sr_annual / math.sqrt(per_year)
    wins = 0
    for _ in range(REPS // 2000):  # porcje, żeby 36 lat × 52 tyg. nie zajęło GB pamięci
        x = RNG.normal(mu, 1.0, size=(2000, n))
        t = x.mean(axis=1) / (x.std(axis=1, ddof=1) / math.sqrt(n))
        wins += int(np.sum(t > z))
    return wins / (REPS // 2000 * 2000)


def sim_power_ic(ic: float, se: float, weeks: int, z: float) -> float:
    """Symulacja: tygodniowe IC ~ N(ic, se·√weeks), test t średniej > z (sd z próby)."""
    sd = se * math.sqrt(weeks)
    x = RNG.normal(ic, sd, size=(REPS, weeks))
    t = x.mean(axis=1) / (x.std(axis=1, ddof=1) / math.sqrt(weeks))
    return float(np.mean(t > z))


def row_hit(label: str, assumed: float, p_star: float, n: float) -> None:
    r = measurability_report(assumed, p_star, n)
    p_det2, margin2 = hand_wald(assumed, p_star, n)
    pw = sim_power_hit(assumed, p_star, int(round(n)))
    print(
        f"  {label}: measurability_report({assumed:.4f}, {p_star:.4f}, {n:.0f}) -> "
        f"p_det {r['p_detectable']:.4f}, pasmo ±{r['band_width_pp']:.2f} pp, "
        f"margines {r['margin_pp']:+.2f} pp, {r['verdict']}"
    )
    print(
        f"      droga 2 (Wald ręcznie): p_det {p_det2:.4f}, margines {margin2:+.2f} pp; "
        f"symulacja: moc (ci_low > p*) = {pw:.3f}"
    )


def main() -> None:
    print("=== DSR: próg t dla kolejnego odczytu historii 2021–2026 (wniosek 107) ===")
    for n in (41, 53):
        t = required_t(n, 0.95)
        print(
            f"  N = {n}: t(DSR 0,95) = {t:.2f}, min. SR roczny na 5,5 roku = {min_annual_sr(t):.2f}"
        )
    t1 = required_t(1, 0.95)
    t2 = required_t(2, 0.95)
    print(f"  nowe dane, własny licznik N = 1: t(DSR 0,95) = {t1:.2f} -> wiąże kryterium 1,96")
    print(f"  baza tradfi (TX1 = 1 odczyt), N = 2: t(DSR 0,95) = {t2:.2f}")
    T_HIST = required_t(41, 0.95)

    print("\n=== Y2 — kierunek BTC 1d ===")
    print("  wejścia: p* 0,5170 i n 978 (Y2, wniosek 69); reguła bez modelu: 5,5 roku dni")
    n_rule = expected_trades(int(5.5 * 365), 0.0)
    print(f"  expected_trades({int(5.5 * 365)}, 0.0) = {n_rule:.0f}")
    for sr in (0.3, 0.5, 0.9):
        p_ass = float(norm.cdf(sr / math.sqrt(365)))
        print(f"  SR {sr} -> p = Φ(SR/√365) = {p_ass:.4f}")
        row_hit(f"model n 978, SR {sr}", p_ass, 0.5170, 978)
        row_hit(f"reguła n {n_rule:.0f}, SR {sr}", p_ass, 0.5170, n_rule)
    print("  forma zwrotu (SR), 5,5 roku:")
    hw_sr = Z / math.sqrt(5.5)
    print(
        f"    half-width SR = 1,96/√5,5 = ±{hw_sr:.3f}; MDE80 = {(Z + Z80) / math.sqrt(5.5):.2f}; "
        f"MDE80 przy t {T_HIST:.2f} = {(T_HIST + Z80) / math.sqrt(5.5):.2f}"
    )
    for sr in (0.3, 0.5, 0.9):
        a = power_mean(sr * math.sqrt(5.5), Z)
        b = power_mean(sr * math.sqrt(5.5), T_HIST)
        sa = sim_power_series(sr, 5.5, Z)
        sb = sim_power_series(sr, 5.5, T_HIST)
        print(
            f"    SR {sr}: moc (t>1,96) wzór {a:.3f} / symulacja {sa:.3f}; "
            f"(t>{T_HIST:.2f}) wzór {b:.3f} / symulacja {sb:.3f}"
        )

    print("\n=== G1 — reguła cyklu fundingu 8h (BTC, 1 h przez rozliczenie) ===")
    n_g1 = expected_trades(int(3 * 365 * 5.5), 0.0)
    sigma = 0.70  # % na 1 h, OS1 wniosek 108 (0,69–0,73)
    for cost in (0.08, 0.09):  # % round trip: wniosek 90 (0,08), OS1 limit (0,09)
        b = sigma * math.sqrt(2 / math.pi)
        p_star = 0.5 * (1 + cost / b)
        print(
            f"  σ_1h {sigma} %, B = E|r| = {b:.3f} %, C = {cost} % -> p* = {p_star:.4f}; "
            f"expected_trades = {n_g1:.0f}"
        )
        row_hit(f"C {cost}, p 0,509 (docs/rag/11)", 0.509, p_star, n_g1)
        print(
            f"      granica dużego n: p 0,509 {'<' if 0.509 < p_star else '>'} p* {p_star:.4f} "
            "-> nieopłacalna przy każdym n"
        )
    se_ev = sigma / math.sqrt(n_g1)
    print(
        f"  forma zwrotu: se na zdarzenie = {sigma}/√{n_g1:.0f} = {se_ev:.4f} %; brutto potrzeba "
        f"C + 2,80·se = {0.08 + (Z + Z80) * se_ev:.3f} % (t 1,96) / "
        f"{0.08 + (T_HIST + Z80) * se_ev:.3f} % (t {T_HIST:.2f})"
    )
    sim_se = float(np.std(RNG.normal(0, sigma, size=(2000, int(n_g1))).mean(axis=1)))
    print(f"      druga droga (symulacja se średniej, 2000 prób): {sim_se:.4f} %")

    print("\n=== B3 — momentum resztowe top-50 (rank IC) ===")
    se = 0.0078  # AU2 (wniosek 92), półtrwanie 28 d
    weeks = int(round(5.4 * 52))
    print(
        f"  se średniego IC = {se} (AU2); MDE80 = {(Z + Z80) * se:.4f} (t 1,96), "
        f"{(T_HIST + Z80) * se:.4f} (t {T_HIST:.2f}); half-width = ±{Z * se:.4f}"
    )
    days = int(round(5.4 * 365))
    for infl in (2.1, 2.4):
        print(
            f"  druga droga se: sd IC dziennego 0,143/√{days} × {infl} (nakładanie 7 d, AU2) = "
            f"{0.143 / math.sqrt(days) * infl:.4f}"
        )
    for ic in (0.010, 0.015, 0.025):
        a = power_mean(ic / se, Z)
        b = power_mean(ic / se, T_HIST)
        sa = sim_power_ic(ic, se, weeks, Z)
        sb = sim_power_ic(ic, se, weeks, T_HIST)
        print(
            f"    IC {ic}: moc (t>1,96) wzór {a:.3f} / symulacja {sa:.3f}; "
            f"(t>{T_HIST:.2f}) wzór {b:.3f} / symulacja {sb:.3f}"
        )

    print("\n=== B4 — powrót reszty po PCA (zwrot, SR) ===")
    for sr in (0.5, 0.9):
        a = power_mean(sr * math.sqrt(5.5), Z)
        b = power_mean(sr * math.sqrt(5.5), T_HIST)
        sa = sim_power_series(sr, 5.5, Z)
        sb = sim_power_series(sr, 5.5, T_HIST)
        yrs = ((Z + Z80) / sr) ** 2
        yrs_d = ((T_HIST + Z80) / sr) ** 2
        print(
            f"  SR {sr}: moc 5,5 roku (t>1,96) wzór {a:.3f} / symulacja {sa:.3f}; "
            f"(t>{T_HIST:.2f}) wzór {b:.3f} / symulacja {sb:.3f}; "
            f"lat do mocy 80 %: {yrs:.1f} (t 1,96) / {yrs_d:.1f} (t {T_HIST:.2f})"
        )

    print("\n=== C1 — pary na kointegracji (trafność) ===")
    m, rho = 10, 0.86
    m_eff = m / (1 + (m - 1) * rho)
    print(f"  pary efektywne: {m}/(1+{m - 1}·{rho}) = {m_eff:.2f} (ρ 0,86 z TR1 vs TS1 — analogia)")
    for band_mult in (2, 4):
        p_star = 0.5 * (1 + 1 / band_mult)
        for n in (29, 29 * m_eff):
            row_hit(f"pasmo {band_mult}×C, n {n:.0f}, hojne p 0,70", 0.70, p_star, n)

    print("\n=== D3 — basis kwartalny vs funding (trafność 'basis > funding') ===")
    row_hit("n 22 kontrakty (D1), hojne p 0,60", 0.60, 0.50, 22)

    print("\n=== E1 — kaskady likwidacji (nowe dane, własny licznik) ===")
    for sigma_ev in (5.0, 8.0):
        for per_year in (150, 300):
            out = []
            for years in (1, 2, 3):
                n = per_year * (years - 90 / 365)
                mde = (Z + Z80) * sigma_ev / math.sqrt(n)
                sim = float(
                    np.std(RNG.normal(0, sigma_ev, size=(2000, int(n))).mean(axis=1)) * (Z + Z80)
                )
                out.append(f"{years} r.: n {n:.0f}, MDE {mde:.2f} % (symulacja {sim:.2f} %)")
            print(f"  σ {sigma_ev} %/24 h, {per_year} epizodów/rok: " + "; ".join(out))
    b = 5.0 * math.sqrt(2 / math.pi)
    for cost in (0.3, 1.0):
        p_star = 0.5 * (1 + cost / b)
        for n in (200, 400, 600):
            print(
                f"  C {cost} %, B {b:.2f} %, p* {p_star:.4f}, n {n}: "
                f"wald_half_width = ±{100 * wald_half_width(n):.2f} pp -> "
                f"p_det {p_star + wald_half_width(n):.4f} (ręcznie "
                f"{p_star + Z * math.sqrt(0.25 / n):.4f})"
            )

    print("\n=== HL — premia / funding HL vs Binance (nowe dane) ===")
    print(
        "  forma jednoaktywowa BTC tydzień (jak CP1); CP1 SR = 2,09/√5,5 = "
        f"{2.09 / math.sqrt(5.5):.2f} (w próbie, górna granica)"
    )
    for years in (1, 2, 3):
        mde = (Z + Z80) / math.sqrt(years)
        a = power_mean(0.89 * math.sqrt(years), Z)
        sa = sim_power_series(0.89, years, Z)
        print(
            f"    {years} r.: MDE80 SR {mde:.2f}; moc przy SR 0,89 wzór {a:.3f} / symulacja {sa:.3f}"
        )
    print("  forma przekrojowa (gdyby HL pokrywał top-50): se(T) = 0,0078·√(5,4/T)")
    for years in (1, 2, 3):
        se_t = 0.0078 * math.sqrt(5.4 / years)
        mde = (Z + Z80) * se_t
        sim = sim_power_ic(mde, se_t, int(round(52 * years)), Z)
        print(
            f"    {years} r.: se {se_t:.4f}, MDE80 IC {mde:.4f} "
            f"(druga droga: symulowana moc przy tym IC = {sim:.3f}, oczekiwane ≈ 0,80)"
        )

    print("\n=== PT1 — surowce i obligacje na danych bazowych (baza tradfi) ===")
    for years, lab in ((36.0, "1990–2026"), (13.7, "po 2013")):
        print(
            f"  {lab} ({years} lat): half-width SR ±{Z / math.sqrt(years):.3f}; "
            f"MDE80 {(Z + Z80) / math.sqrt(years):.3f}; przy t {t2:.2f} (N=2) "
            f"{(t2 + Z80) / math.sqrt(years):.3f}"
        )
        for sr in (0.3, 0.5):
            a = power_mean(sr * math.sqrt(years), Z)
            sa = sim_power_series(sr, years, Z)
            b = power_mean(sr * math.sqrt(years), t2)
            sb = sim_power_series(sr, years, t2)
            print(
                f"    SR {sr}: moc (t>1,96) wzór {a:.3f} / symulacja {sa:.3f}; "
                f"(t>{t2:.2f}) wzór {b:.3f} / symulacja {sb:.3f}"
            )


if __name__ == "__main__":
    main()
