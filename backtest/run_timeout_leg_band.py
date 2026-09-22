"""
run_timeout_leg_band.py

Runda H3 — PASMO niepewności co do nogi wyjścia „timeout". Skrypt jednorazowy/analityczny,
poza pytest, zbudowany na `backtest/checkpoint_lib.py` (CLAUDE.md zasada 13).

KONFIGURACJA JEST ZAMROŻONA — to konfiguracja S1b (`backtest/run_single_regime_4h.py`),
przeniesiona bez zmian. Trzy powody, w kolejności ważności:
  1. Na tej konfiguracji target JUŻ widzieliśmy (S1b opublikowane), więc ponowny przebieg
     NIE zużywa nowego spojrzenia. Pomiar na konfiguracji H2.1 spaliłby darmowe spojrzenie
     na baseline hipotezy, której jeszcze nie uruchomiono.
  2. Konfiguracja H2.1 („bez bramki reżimu") dziś NIE JEST uruchamialna — silnik filtruje
     po kolumnie `regime`, więc jej brak wymaga zmiany silnika, co należy do H2.1 (zasada 4).
  3. Jest do czego porównać co do cyfry.

CO TEN SKRYPT MIERZY: jak bardzo werdykt zależy od założenia, którego NIE UMIEMY zmierzyć
(czy zlecenie limit na barierze pionowej by się wypełniło). Dwa krańce, bo koszt jest
afiniczny w stopie wypełnienia — dwa punkty dają całą prostą, a parametr ciągły dodałby
wyłącznie stopień swobody, którego nie ma czym skalibrować (`docs/rag/04`).

CZEGO NIE RAPORTUJE (reguła D5 pre-rejestracji): trafności, CI trafności, z_stat, marginesu
ani klasyfikacji. Te trafiają do `raw_output.txt` (zasada 11 jest bezwarunkowa), ale nie są
wynikiem tej rundy. Powód mechaniczny: koszt może ruszyć trafność WYŁĄCZNIE przez selekcję
(inna krzywa equity -> inny moment kill-switcha), czyli byłby to szum selekcyjny.

Skrypt świadomie NIE ogłasza zwycięzcy — drukuje liczby.

Użycie:
    py -m backtest.run_timeout_leg_band
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.costs import (
    EXECUTION_MAKER_LIMIT,
    MAKER,
    TAKER,
    funding_cost,
    gate_cost_fraction,
)
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.metrics import Z_TWO_SIDED_95, break_even_hit_rate

# --- KONFIGURACJA ZAMROŻONA (przeniesiona z run_single_regime_4h.py) ---
TIMEFRAME = "4h"
REGIME = "range"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

FUNNEL_KEYS = (
    "n_rows_evaluated",
    "n_signals_no_direction",
    "n_signals_confidence_gated",
    "n_signals_cost_gated",
    "n_signals",
)


def _run(df: pd.DataFrame, rule: dict, **extra) -> dict:
    return run_and_summarize(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME, REVERSION_FEATURES)],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        candle_minutes=CANDLE_MINUTES,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        **extra,
    )


def _real_trades(result: dict) -> pd.DataFrame:
    t = result["backtest"]["trades"]
    return t[~t["kill_switch_active"].astype(bool)].copy()


def _cost_breakdown(trades: pd.DataFrame) -> dict:
    """Rozbija koszt na fee+slippage vs funding (wzorzec: diagnose_kill_switch_trigger.py)."""
    notional = trades["position_size"] * trades["entry_price"]
    funding = np.array(
        [
            funding_cost(
                notional=n,
                holding_candles=h,
                direction=d,
                candle_minutes=CANDLE_MINUTES,
            )
            for n, h, d in zip(
                notional, trades["exit_bar_offset"], trades["signal_direction"]
            )
        ]
    )
    # Mianownik z zerem zamaskowanym na NaN — dokładnie jak w
    # `metrics.summarize_edge_by_regime`.
    #
    # Zakres ochrony, żeby nie przecenić: przy DZISIEJSZYM modelu kosztu zerowy nominał
    # daje też zerowy koszt, więc dzielenie to 0/0 = NaN, a `Series.mean()` NaN pomija —
    # nic się nie psuje. Dziura otwiera się dopiero, gdy koszt przestanie być czysto
    # proporcjonalny do nominału (np. opłata minimalna per transakcja): wtedy jest to
    # `nonzero/0 = inf`, `.mean()` robi się `inf` i CAŁE pasmo progu z tej jednej liczby
    # wychodzi błędne — po cichu, bo nic nie rzuca wyjątkiem. Maskowanie zamyka to
    # zawczasu i robi wykluczenie takiego wiersza jawnym, a nie przypadkowym.
    #
    # W przebiegu H3 zerowych nominałów nie było, więc `raw_output.txt` zostaje bez
    # zmian — to zabezpieczenie na ponowne uruchomienie, nie korekta wyniku.
    denom = notional.replace(0.0, np.nan)
    total_frac = trades["cost"] / denom
    return {
        "cost_frac_mean": float(total_frac.mean()),
        "cost_frac_median": float(total_frac.median()),
        "funding_frac_mean": float((funding / denom).mean()),
        "fee_slip_frac_mean": float(((trades["cost"] - funding) / denom).mean()),
    }


def _exit_mix(trades: pd.DataFrame) -> dict:
    counts = trades["exit_reason"].value_counts()
    n = len(trades)
    return {r: int(counts.get(r, 0)) for r in ("tp", "sl", "timeout")} | {"n": n}


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    df = _load(cfg, TIMEFRAME)

    print("=" * 98)
    print("H3 — PASMO nogi `timeout` (konfiguracja ZAMROZONA = S1b)")
    print("=" * 98)
    print(
        f"dane: {len(df)} swiec {TIMEFRAME}, {df['timestamp'].min()} -> {df['timestamp'].max()}\n"
        f"rezim: {REGIME} | V = {VERTICAL_BARRIER_CANDLES} | "
        f"walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS} dni | seed {PRIMARY_SEED}\n"
    )

    # --- 0. KONTROLA BIT-IDENTYCZNOSCI (brak argumentu vs jawne TAKER) ---
    print("=" * 98)
    print("0. KONTROLA: brak argumentu vs jawne timeout_leg=TAKER")
    print("=" * 98)
    base = _run(df, rule)
    taker = _run(df, rule, timeout_leg=TAKER)
    same_equity = base["backtest"]["final_equity"] == taker["backtest"]["final_equity"]
    same_trades = base["backtest"]["trades"].equals(taker["backtest"]["trades"])
    print(f"  final_equity identyczne : {same_equity}")
    print(f"  journal identyczny      : {same_trades}")
    print(f"  >>> BASELINE {'ZACHOWANY' if same_equity and same_trades else 'ZLAMANY'}\n")

    maker = _run(df, rule, timeout_leg=MAKER)

    # --- 1. LEJEK (dowod uczciwosci porownania) ---
    print("=" * 98)
    print("1. LEJEK SYGNALOW — musi byc IDENTYCZNY (bramka bierze max po powodach wyjscia)")
    print("=" * 98)
    print(f"  {'licznik':>30} | {'TAKER':>10} | {'MAKER':>10} | {'zgodne':>7}")
    print("  " + "-" * 66)
    funnel_ok = True
    for key in FUNNEL_KEYS:
        a = sum(f[key] for f in taker["backtest"]["folds_summary"])
        b = sum(f[key] for f in maker["backtest"]["folds_summary"])
        funnel_ok &= a == b
        print(f"  {key:>30} | {a:10d} | {b:10d} | {str(a == b):>7}")
    print(f"\n  bramka kosztowa = {gate_cost_fraction(EXECUTION_MAKER_LIMIT):.6f} "
          f"(niewrazliwa na timeout_leg z konstrukcji)")
    print(f"  >>> LEJEK {'IDENTYCZNY' if funnel_ok else 'ROZJECHANY'}\n")

    # --- 2. KOSZT ---
    print("=" * 98)
    print("2. KOSZT — glowny przedmiot rundy")
    print("=" * 98)
    rows = {}
    for name, res in (("TAKER", taker), ("MAKER", maker)):
        tr = _real_trades(res)
        rows[name] = _cost_breakdown(tr) | _exit_mix(tr)
    print(f"  {'miara':>28} | {'TAKER':>12} | {'MAKER':>12} | {'delta':>12}")
    print("  " + "-" * 72)
    for label, key in (
        ("koszt sredni (% nominalu)", "cost_frac_mean"),
        ("koszt mediana (% nominalu)", "cost_frac_median"),
        ("  w tym fee+slippage", "fee_slip_frac_mean"),
        ("  w tym funding", "funding_frac_mean"),
    ):
        a, b = rows["TAKER"][key], rows["MAKER"][key]
        print(f"  {label:>28} | {a * 100:11.5f}% | {b * 100:11.5f}% | {(b - a) * 100:+11.5f}%")

    print(f"\n  {'rozklad wyjsc':>28} | {'TAKER':>12} | {'MAKER':>12}")
    print("  " + "-" * 58)
    for r in ("tp", "sl", "timeout", "n"):
        print(f"  {r:>28} | {rows['TAKER'][r]:12d} | {rows['MAKER'][r]:12d}")
    n_t = rows["TAKER"]["n"]
    share_to = rows["TAKER"]["timeout"] / n_t if n_t else 0.0
    half = Z_TWO_SIDED_95 * np.sqrt(share_to * (1 - share_to) / n_t) if n_t else 0.0
    print(
        f"\n  udzial timeoutow (TAKER) = {share_to * 100:.2f}% "
        f"(95% CI [{(share_to - half) * 100:.2f}%; {(share_to + half) * 100:.2f}%]) "
        f"— to jest DZWIGNIA calego efektu"
    )

    # --- 3. PROG OPLACALNOSCI ---
    print("\n" + "=" * 98)
    print("3. PROG OPLACALNOSCI")
    print("=" * 98)
    edges = {}
    for name, res in (("TAKER", taker), ("MAKER", maker)):
        e = res["edge_per_regime"]
        edges[name] = e.loc[e["regime"] == REGIME].iloc[0]
    b_t, b_m = edges["TAKER"]["barrier_pct"], edges["MAKER"]["barrier_pct"]
    print(f"  barrier_pct (B): TAKER={b_t:.6f}  MAKER={b_m:.6f}  "
          f"identyczne={np.isclose(b_t, b_m)}")
    be_t, be_m = edges["TAKER"]["break_even_p"], edges["MAKER"]["break_even_p"]
    print(f"\n  {'wariant':>10} | {'koszt C':>10} | {'break-even p':>13}")
    print("  " + "-" * 40)
    print(f"  {'TAKER':>10} | {edges['TAKER']['cost_pct'] * 100:9.5f}% | {be_t * 100:12.2f}%")
    print(f"  {'MAKER':>10} | {edges['MAKER']['cost_pct'] * 100:9.5f}% | {be_m * 100:12.2f}%")
    print(f"\n  >>> PASMO PROGU: [{min(be_t, be_m) * 100:.2f}%; {max(be_t, be_m) * 100:.2f}%], "
          f"szerokosc {abs(be_t - be_m) * 100:.2f} pp")

    # --- 4. WALIDACJA DRUGA DROGA (zasada 16a) ---
    print("\n" + "=" * 98)
    print("4. WALIDACJA drugą drogą — koszt z journalu vs policzony z mieszanki wyjsc")
    print("=" * 98)
    from backtest.costs import execution_legs, round_trip_cost_fraction

    for name, timeout_leg in (("TAKER", TAKER), ("MAKER", MAKER)):
        r = rows[name]
        n = r["n"]
        analytic = sum(
            (r[reason] / n)
            * round_trip_cost_fraction(
                entry_leg=execution_legs(EXECUTION_MAKER_LIMIT, reason, timeout_leg)[0],
                exit_leg=execution_legs(EXECUTION_MAKER_LIMIT, reason, timeout_leg)[1],
            )
            for reason in ("tp", "sl", "timeout")
        )
        measured_fee_slip = r["fee_slip_frac_mean"]
        print(
            f"  {name}: analitycznie={analytic:.8f}  z journalu(fee+slip)={measured_fee_slip:.8f}  "
            f"zgodne={np.isclose(analytic, measured_fee_slip, atol=1e-9)}"
        )

    # --- 5. SPROSTOWANIE TABELI GEOMETRII Z H2.0 ---
    print("\n" + "=" * 98)
    print("5. SPROSTOWANIE progu z H2.0 (liczonego kosztem BRAMKOWYM, nie realnym)")
    print("=" * 98)
    b_eff = 0.014424  # B_eff z H2.0, ta sama geometria
    gate = gate_cost_fraction(EXECUTION_MAKER_LIMIT)
    print(f"  H2.0 (koszt bramkowy {gate * 100:.4f}%)  -> prog "
          f"{break_even_hit_rate(gate, b_eff) * 100:.2f}%   <- ZAWYZONE")
    for name in ("TAKER", "MAKER"):
        c = edges[name]["cost_pct"]
        print(f"  H3 {name} (koszt realny {c * 100:.4f}%) -> prog "
              f"{break_even_hit_rate(c, b_eff) * 100:.2f}%")

    # --- 6. LICZBY OBJETE ZAKAZEM D5 (do raw_output, nie do werdyktu) ---
    print("\n" + "=" * 98)
    print("6. LICZBY OBJETE ZAKAZEM RAPORTOWANIA (regula D5) — tylko do raw_output")
    print("=" * 98)
    print("  Ponizsze NIE sa wynikiem tej rundy i nie uczestnicza w zadnej decyzji.")
    print("  Koszt moze ruszyc trafnosc WYLACZNIE przez selekcje (inny moment kill-switcha).\n")
    for name, res in (("TAKER", taker), ("MAKER", maker)):
        print(f"  --- {name} ---")
        print("  " + res["edge_per_regime"].to_string(index=False).replace("\n", "\n  "))
        print("  " + str(res["classification"]))
        print()


if __name__ == "__main__":
    main()
