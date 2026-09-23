"""
run_horizon_y.py — serie Y1 (1h) / Y2 (1d): model KONTROLNY projektu (4 cechy REVERSION, bez bramki
reżimu, wagi klas `balanced`, wejście limit po close k = 1, pojedyncze wyjście, V = 3 ŚWIECE,
bariera 1,5·ATR) uruchomiony na INNYM INTERWALE jako NOWA BAZA (CLAUDE.md zasada 20: od 2021-01-01).
Pre-rejestracje (PRZED tym skryptem): runs/2026-09-23_y1-horyzont-1h/, runs/2026-09-23_y2-horyzont-1d/.

Uruchomienie:  py -m backtest.run_horizon_y 1h|1d          (Windows: PYTHONUTF8=1)
               py -m backtest.run_horizon_y 1h|1d --moc    # rachunek mierzalności PRZED treningiem

Neutralny reporter: kryterium dwóch warunków (jedno ramię, m = 1 per seria); werdykt w README.
Na 1d okna walk-forward są dłuższe (365/91/91 dni), bo 60 dni = 60 wierszy — zapisane w
pre-rejestracji jako parametr bazy, nie strojenie.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd
import yaml

from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import (
    PRIMARY_SEED,
    fetch_window,
    load_config,
    summarize_result,
    summarize_trade_returns,
)
from backtest.costs import EXIT_REASON_SL, EXIT_REASON_TIMEOUT, EXIT_REASON_TP
from backtest.engine import FILL_MODEL_PATH, REGIME_ALL, collect_signals, simulate_equity
from backtest.execution import ENTRY_LIMIT_CLOSE, EntryRule
from backtest.metrics import (
    Z_TWO_SIDED_95,
    break_even_hit_rate,
    expected_trades,
    measurability_report,
    required_trades,
    wald_half_width,
)

HORIZONS = {
    "1h": {
        "series": "Y1",
        "candles_per_day": 24,
        "candle_minutes": 60,
        "train_days": 60,
        "test_days": 28,
        "step_days": 28,
    },
    "1d": {
        "series": "Y2",
        "candles_per_day": 1,
        "candle_minutes": 1440,
        "train_days": 365,
        "test_days": 91,
        "step_days": 91,
    },
}
VERTICAL_BARRIER_CANDLES = 3
ATR_MULTIPLIER = 1.5
ATR_WINDOW = 14
FEATURES = list(REVERSION_FEATURES)
ENTRY = EntryRule(ENTRY_LIMIT_CLOSE)
VALIDITY = 1
ABSTENTION_REF = 0.4038  # kontrola 4h — jedyne odniesienie ex ante
FILL_RATE_REF = 0.994
COST_REF = 0.000808  # C per transakcja z kontroli 4h (ten sam model wykonania; ułamek nominału)
P_ASSUMED = 0.56
CONTROL_4H = {"n": 6789, "p": 0.4958, "r_mean": -0.001069, "p_star": 0.5364}
FUNNEL = (
    ("świece ocenione", "n_rows_evaluated"),
    ("bez kierunku (abstynencja)", "n_signals_no_direction"),
    ("bramka pewności", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnały kandydujące", "n_signals"),
)
SEP = "=" * 104


def _atr_fraction(df: pd.DataFrame, window: int = ATR_WINDOW) -> pd.Series:
    """ATR(window) / close — przybliżenie bariery w ułamku ceny (do progu ex ante)."""
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift(1)).abs()
    lc = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(window).mean() / df["close"]


def _verdict(w: dict) -> str:
    if w["t_neff"] > Z_TWO_SIDED_95 and w["ci_low"] > w["p_star"]:
        return "POZYTYWNY — t_neff > 1,96 i ci_low(p) > p*. NAJPIERW SZUKAJ PRZECIEKU"
    if w["t_neff"] < -Z_TWO_SIDED_95 and w["n"] >= required_trades(0.50, w["be_symmetric"]):
        return f"NEGATYWNY — t_neff < −1,96 przy n >= required_trades(0,50; BE) = {required_trades(0.50, w['be_symmetric']):,.0f}"
    return "NIEROZSTRZYGNIĘTY — |t_neff| poniżej progu, ci_low(p) <= p* albo n poniżej wymaganego"


def _print_funnel(name: str, collected: dict) -> tuple[int, int]:
    active = [f for f in collected["folds_summary"] if not f["skipped"]]
    print(f"  [{name}] foldy: {len(active)} aktywne / {len(collected['folds_summary'])} łącznie")
    for label, key in FUNNEL:
        print(f"  {label:>28}: {sum(f[key] for f in active):8d}")
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    print(f"  {'abstynencja':>28}: {100 * n_abst / n_rows:7.2f}%")
    return n_rows, n_abst


def _wald(hits: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = hits / n
    half = Z_TWO_SIDED_95 * np.sqrt(p * (1.0 - p) / n)
    return p, p - half, p + half


def _print_group_table(title: str, groups: list[tuple[str, pd.DataFrame]]) -> None:
    print(f"  {title}")
    print(
        f"  {'grupa':>12} | {'n':>5} | {'udział':>7} | {'p':>7} | {'CI 95% (p)':>17} | "
        f"{'r̄ netto':>9} | {'r̄ brutto':>9} | {'mediana':>8}"
    )
    print("  " + "-" * 94)
    total = sum(len(g) for _, g in groups) or 1
    for name, g in groups:
        n = len(g)
        if n == 0:
            print(
                f"  {name:>12} | {0:5d} |       — |       — |                 — |         — |         — |        —"
            )
            continue
        p, lo, hi = _wald(int((g["gross_ret"] > 0).sum()), n)
        print(
            f"  {name:>12} | {n:5d} | {100 * n / total:6.1f}% | {100 * p:6.2f}% | [{100 * lo:6.2f}; {100 * hi:6.2f}] | "
            f"{100 * g['net_ret'].mean():+8.4f}% | {100 * g['gross_ret'].mean():+8.4f}% | {100 * g['net_ret'].median():+7.4f}%"
        )


def _load(tf: str):
    data_cfg = load_config()["data"]
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    df = fetch_window(data_cfg, tf)
    return data_cfg, rule, df


def _ex_ante(tf: str, df: pd.DataFrame, cfg: dict) -> dict:
    """Rachunek mierzalności PRZED treningiem: bariera z ATR, próg, n z abstynencji 4h."""
    atr_frac = _atr_fraction(df).dropna()
    barrier = ATR_MULTIPLIER * float(atr_frac.median())
    be = break_even_hit_rate(COST_REF, barrier)
    n_candles = len(df)
    warm = cfg["train_days"] * cfg["candles_per_day"]
    n_oos = max(n_candles - warm, 0)
    n_exp = expected_trades(n_oos, ABSTENTION_REF, FILL_RATE_REF)
    rep = measurability_report(P_ASSUMED, be, n_exp)
    return {
        "n_candles": n_candles,
        "n_oos": n_oos,
        "atr_median": float(atr_frac.median()),
        "atr_p10": float(atr_frac.quantile(0.10)),
        "atr_p90": float(atr_frac.quantile(0.90)),
        "barrier": barrier,
        "be": be,
        "n_exp": n_exp,
        "half_width": wald_half_width(n_exp),
        "report": rep,
    }


def print_ex_ante(tf: str) -> None:
    cfg = HORIZONS[tf]
    data_cfg, _rule, df = _load(tf)
    ea = _ex_ante(tf, df, cfg)
    print(SEP)
    print(f"{cfg['series']} — MIERZALNOŚĆ EX ANTE dla interwału {tf} (przed treningiem; zasada 18)")
    print(SEP)
    print(
        f"  świece {tf}: {ea['n_candles']} od {df['timestamp'].min()} do {df['timestamp'].max()} (min_start {data_cfg['min_start']}); "
        f"pierwsze okno treningu {cfg['train_days']} dni = {cfg['train_days'] * cfg['candles_per_day']} świec → OOS ≈ {ea['n_oos']} świec\n"
        f"  ATR({ATR_WINDOW})/close: mediana {100 * ea['atr_median']:.3f}% (p10 {100 * ea['atr_p10']:.3f}%, p90 {100 * ea['atr_p90']:.3f}%); "
        f"bariera 1,5·ATR ≈ {100 * ea['barrier']:.3f}% ceny; koszt C = {100 * COST_REF:.4f}% (kontrola 4h)\n"
        f"  próg ±B = 0,5(1 + C/B) = {100 * ea['be']:.2f}%; oczekiwane n = expected_trades({ea['n_oos']}; {ABSTENTION_REF}; {FILL_RATE_REF}) = {ea['n_exp']:,.0f}; "
        f"half-width {100 * ea['half_width']:.2f} pp; luka (0,56 − próg) = {100 * (P_ASSUMED - ea['be']):+.2f} pp\n"
        f"  measurability_report(p = {P_ASSUMED}, BE = {ea['be']:.4f}, n = {ea['n_exp']:,.0f}) → {ea['report'].get('verdict', ea['report'])}"
    )
    print(SEP)


def main(argv: list[str]) -> None:
    if not argv or argv[0] not in HORIZONS:
        raise SystemExit("podaj interwał: 1h | 1d [--moc]")
    tf = argv[0]
    if "--moc" in argv:
        print_ex_ante(tf)
        return
    cfg = HORIZONS[tf]
    series = cfg["series"]
    t0 = time.time()
    data_cfg, rule, df = _load(tf)
    ea = _ex_ante(tf, df, cfg)
    print(SEP)
    print(
        f"{series} — MODEL KONTROLNY NA INTERWALE {tf} jako NOWA BAZA (4 cechy REVERSION, V = {VERTICAL_BARRIER_CANDLES} świece, "
        f"walk-forward {cfg['train_days']}/{cfg['test_days']}/{cfg['step_days']}); konfiguracja ZAMROŻONA"
    )
    print(SEP)
    print(
        f"dane      : {len(df)} świec {tf} od {df['timestamp'].min()} do {df['timestamp'].max()} (zasada 20: min_start = {data_cfg['min_start']})\n"
        f"ex ante   : bariera ≈ {100 * ea['barrier']:.3f}% ceny, próg ±B {100 * ea['be']:.2f}%, oczekiwane n {ea['n_exp']:,.0f}, "
        f"half-width {100 * ea['half_width']:.2f} pp → {ea['report'].get('verdict', ea['report'])}\n"
        f"pipeline  : BEZ bramki reżimu, V={VERTICAL_BARRIER_CANDLES} świece, wagi klas `balanced`, seed {PRIMARY_SEED}, "
        f"wejście {ENTRY.kind} k={VALIDITY}, pojedyncze wyjście, candles_per_day {cfg['candles_per_day']}\n"
        f"cechy     : {FEATURES}\n"
        f"odniesienie 4h: n {CONTROL_4H['n']}, p {100 * CONTROL_4H['p']:.2f}%, r̄ {100 * CONTROL_4H['r_mean']:+.4f}%, p* {100 * CONTROL_4H['p_star']:.2f}%\n"
        f"kryterium : jedno ramię (m = 1): POZYTYWNY t_neff > 1,96 i ci_low(p) > p*; NEGATYWNY t_neff < −1,96 przy n >= required\n"
    )

    print("0. LEJEK")
    collected = collect_signals(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=cfg["candles_per_day"],
        train_days=cfg["train_days"],
        test_days=cfg["test_days"],
        step_days=cfg["step_days"],
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    print(f"  trening zakończony po {time.time() - t0:.0f} s")
    n_rows, n_abst = _print_funnel(series, collected)
    result = simulate_equity(
        collected["df"],
        collected["candidate_signals"],
        collected["folds_summary"],
        candle_minutes=cfg["candle_minutes"],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        fill_model=FILL_MODEL_PATH,
        entry_rule=ENTRY,
        entry_validity_candles=VALIDITY,
    )
    w = summarize_trade_returns(summarize_result(result, PRIMARY_SEED))

    print(
        "\n1. KRYTERIUM — zwrot netto per trade (t_neff) i trafność wobec p* (jedno ramię, z = 1,96)"
    )
    half = Z_TWO_SIDED_95 * w["se"]
    print(
        f"  {series}: n {w['n']} | r̄ netto {100 * w['r_mean']:+.4f}% [{100 * (w['r_mean'] - half):+.4f}; {100 * (w['r_mean'] + half):+.4f}] | "
        f"mediana {100 * w['r_median']:+.4f}% | t {w['t']:+.2f} | N_eff {w['n_eff']:.0f} | t_neff {w['t_neff']:+.2f} | "
        f"p {100 * w['p']:.2f}% [{100 * w['ci_low']:.2f}; {100 * w['ci_high']:.2f}] | p* {100 * w['p_star']:.2f}% | BE ±B {100 * w['be_symmetric']:.2f}%"
    )
    print(f"  >>> ODCZYT KRYTERIUM {series}: {_verdict(w)}")

    print("\n2. OPIS — powód wyjścia, kierunek, geometria wypłaty")
    real = w["real"].copy()
    _print_group_table(
        f"{series} — powód wyjścia",
        [
            ("cel (tp)", real.loc[real["exit_reason"] == EXIT_REASON_TP]),
            ("stop (sl)", real.loc[real["exit_reason"] == EXIT_REASON_SL]),
            ("timeout", real.loc[real["exit_reason"] == EXIT_REASON_TIMEOUT]),
        ],
    )
    _print_group_table(
        f"{series} — kierunek",
        [
            ("long", real.loc[real["signal_direction"] > 0]),
            ("short", real.loc[real["signal_direction"] < 0]),
        ],
    )
    print(
        f"  {series}: W̄ = {100 * w['w_mean']:.4f}%, L̄ = {100 * w['l_mean']:.4f}%, C = {100 * w['cost']:.4f}%, "
        f"std zwrotu {100 * w['r_std']:.3f}%, p5/p95 [{100 * w['r_p5']:+.3f}%; {100 * w['r_p95']:+.3f}%], "
        f"niewypełnione {w['n_unfilled']}, stłumione {w['n_suppressed']}"
    )
    years = pd.to_datetime(real["timestamp"], utc=True).dt.year
    print(f"  {'rok':>6} | {'n':>5} | {'p':>7} | {'r̄ netto':>9} | {'Σ netto':>9}")
    print("  " + "-" * 48)
    for y, g in real.groupby(years):
        print(
            f"  {y:6d} | {len(g):5d} | {100 * (g['gross_ret'] > 0).mean():6.2f}% | {100 * g['net_ret'].mean():+8.4f}% | {100 * g['net_ret'].sum():+8.2f}%"
        )

    print("\n3. MIERZALNOŚĆ — ex ante vs ex post")
    n_post = expected_trades(n_rows, n_abst / n_rows, FILL_RATE_REF)
    print(
        f"  ex ante: bariera {100 * ea['barrier']:.3f}%, próg {100 * ea['be']:.2f}%, n {ea['n_exp']:,.0f}, half-width {100 * ea['half_width']:.2f} pp; "
        f"ex post: BE ±B {100 * w['be_symmetric']:.2f}%, p* {100 * w['p_star']:.2f}%, świece ocenione {n_rows}, abstynencja {100 * n_abst / n_rows:.2f}%, "
        f"expected_trades {n_post:,.0f}, journal {w['n']:,}, half-width {100 * wald_half_width(w['n']):.2f} pp"
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
