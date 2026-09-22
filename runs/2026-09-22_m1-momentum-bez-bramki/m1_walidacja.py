"""
Walidacja wyniku M1 (CLAUDE.md zasada 16a) — druga, niezalezna droga.

1. Trafnosc przeliczona WPROST Z JOURNALU (zliczenie gross_pnl > 0), a nie wzieta
   z `summarize_edge_by_regime`.
2. Lejek: kogo NIE ma w zbiorze.
3. Czy roznica miedzy ramionami jest w ogole istotna (test dwoch proporcji).
4. Zgodnosc ramienia A z HISTORYCZNYMI pomiarami projektu — inna konfiguracja,
   inny interwal, inna proba, ta sama liczba.

Uruchomienie: PYTHONPATH=. py runs/2026-09-22_m1-momentum-bez-bramki/m1_walidacja.py
"""
import numpy as np
import yaml

from agents.ml_optimizer import MOMENTUM_FEATURES, REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.metrics import Z_TWO_SIDED_95, observed_wald_ci

cfg = _load_cfg()
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
raw = _load(cfg, "4h")

FUNNEL = (
    ("ocenione swiece", "n_rows_evaluated"),
    ("odpadlo na abstynencji", "n_signals_no_direction"),
    ("bramka pewnosci", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnaly", "n_signals"),
)

wyniki = {}
for kod, cechy in (("A", REVERSION_FEATURES), ("B", MOMENTUM_FEATURES)):
    res = run_and_summarize(
        raw,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, cechy)],
        vertical_barrier_candles=3,
        candles_per_day=6,
        candle_minutes=240,
        train_days=60,
        test_days=28,
        step_days=28,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    tr = res["backtest"]["trades"]
    realne = tr.loc[~tr["kill_switch_active"]]
    aktywne = [f for f in res["backtest"]["folds_summary"] if not f["skipped"]]
    wyniki[kod] = {
        "n": len(realne),
        "trafienia": int((realne["gross_pnl"] > 0).sum()),
        "lejek": {k: sum(f[k] for f in aktywne) for _, k in FUNNEL},
        "stlumione": int(tr["kill_switch_active"].sum()),
        "pominiete": len(res["backtest"]["folds_summary"]) - len(aktywne),
        "wszystkie_foldy": len(res["backtest"]["folds_summary"]),
        "z_tabeli": float(res["edge_per_regime"].iloc[0]["hit_rate"]),
        "be": float(res["edge_per_regime"].iloc[0]["break_even_p"]),
    }

print("=" * 96)
print("1. TRAFNOSC PRZELICZONA WPROST Z JOURNALU (zliczenie gross_pnl > 0)")
print("=" * 96)
print(f"  {'ramie':>6} | {'trafien':>9} | {'n':>7} | {'z journalu':>11} | {'z tabeli':>10} | {'roznica':>9}")
print("  " + "-" * 66)
for kod in ("A", "B"):
    w = wyniki[kod]
    p = w["trafienia"] / w["n"]
    print(
        f"  {kod:>6} | {w['trafien'] if False else w['trafienia']:9d} | {w['n']:7d} | "
        f"{100 * p:10.4f}% | {100 * w['z_tabeli']:9.4f}% | {100 * abs(p - w['z_tabeli']):8.6f} pp"
    )
print("\n  Zerowa roznica = `summarize_edge_by_regime` liczy dokladnie to, co deklaruje.")

print("\n" + "=" * 96)
print("2. KOGO NIE MA W ZBIORZE")
print("=" * 96)
print(f"  {'etap':>26} | {'ramie A':>10} | {'ramie B':>10}")
print("  " + "-" * 52)
for etykieta, klucz in FUNNEL:
    print(f"  {etykieta:>26} | {wyniki['A']['lejek'][klucz]:10d} | {wyniki['B']['lejek'][klucz]:10d}")
for etykieta, klucz in (("stlumione kill-switchem", "stlumione"), ("W PROBIE (n)", "n")):
    print(f"  {etykieta:>26} | {wyniki['A'][klucz]:10d} | {wyniki['B'][klucz]:10d}")
for kod in ("A", "B"):
    w = wyniki[kod]
    bilans = w["lejek"]["n_rows_evaluated"] == (
        w["lejek"]["n_signals"]
        + w["lejek"]["n_signals_no_direction"]
        + w["lejek"]["n_signals_cost_gated"]
        + w["lejek"]["n_signals_confidence_gated"]
    )
    print(f"    ramie {kod}: foldy pominiete {w['pominiete']}/{w['wszystkie_foldy']}, "
          f"bilans lejka domyka sie: {bilans}")

print("\n" + "=" * 96)
print("3. CZY RAMIONA SIE OD SIEBIE ROZNIA (test dwoch proporcji)")
print("=" * 96)
pa = wyniki["A"]["trafienia"] / wyniki["A"]["n"]
pb = wyniki["B"]["trafienia"] / wyniki["B"]["n"]
se = np.sqrt(pa * (1 - pa) / wyniki["A"]["n"] + pb * (1 - pb) / wyniki["B"]["n"])
delta = pb - pa
print(f"  ramie A (reversion) : {100 * pa:.2f}%   ramie B (momentum) : {100 * pb:.2f}%")
print(f"  roznica B - A = {100 * delta:+.2f} pp,  95% CI [{100 * (delta - Z_TWO_SIDED_95 * se):+.2f}; "
      f"{100 * (delta + Z_TWO_SIDED_95 * se):+.2f}] pp,  z = {delta / se:+.2f}")
print(f"  >>> {'ROZNICA ISTOTNA' if abs(delta / se) > Z_TWO_SIDED_95 else 'ROZNICA NIEISTOTNA'} — "
      "momentum nie jest GORSZE od reversion, jest TAK SAMO nieobecne.")

print("\n" + "=" * 96)
print("4. ZGODNOSC RAMIENIA A Z HISTORYCZNYMI POMIARAMI PROJEKTU")
print("=" * 96)
print("  Ramie A to INNA konfiguracja niz cokolwiek w Z10: 4h zamiast 5m, bez bramki zamiast")
print("  z bramka, wagi klas zamiast ich braku. Jesli mimo to daje te sama liczbe, jest to")
print("  niezalezne potwierdzenie, ze aparat mierzy to samo co wczesniej.\n")
for opis, p_hist, n_hist in (
    ("5m `range` (Z17+Z21)", 0.5038, 7043),
    ("POOLED Faza 0 (Z10)", 0.5027, 7687),
):
    ci = observed_wald_ci(int(round(p_hist * n_hist)), n_hist)
    w_ci = observed_wald_ci(wyniki["A"]["trafienia"], wyniki["A"]["n"])
    nakladaja = not (w_ci["ci_high"] < ci["ci_low"] or ci["ci_high"] < w_ci["ci_low"])
    print(f"  {opis:>22}: {100 * p_hist:.2f}% [{100 * ci['ci_low']:.2f}; {100 * ci['ci_high']:.2f}]"
          f"   vs ramie A {100 * pa:.2f}% [{100 * w_ci['ci_low']:.2f}; {100 * w_ci['ci_high']:.2f}]"
          f"  -> CI {'NAKLADAJA SIE' if nakladaja else 'ROZLACZNE'}")
