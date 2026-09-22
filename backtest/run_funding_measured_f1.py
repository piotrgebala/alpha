"""
run_funding_measured_f1.py

F1 — funding po raz pierwszy na probie zdolnej cokolwiek rozstrzygnac. Skrypt
jednorazowy/analityczny, zbudowany na `backtest/checkpoint_lib.py` (zasada 13).

KONFIGURACJA I KRYTERIUM SA ZAMROZONE w pre-rejestracji zapisanej w OSOBNYM commicie
PRZED kodem: `runs/2026-09-22_f1-funding-zmierzony/README.md`.

DLACZEGO TA RUNDA ISTNIEJE
--------------------------
H2.1 zadalo dobre pytanie na przyrzadzie, ktory nie umial odpowiedziec: werdykt
NIEROZSTRZYGNIETY przy n = 98, bo model odmawial kierunku w 99,32% swiec. Przeszkoda byla
INSTRUMENTALNA, nie informacyjna. K2/A1/K3 ja usunely i zmierzyly: 35 -> 8 033 transakcje
na tej samej konfiguracji.

P1 pokazalo, ze funding jest JEDYNYM zrodlem spoza OHLCV z wystarczajaca historia -
endpointy pozycjonowania Binance oddaja 30,8 dnia, czyli 40x za malo.

CZEGO TA RUNDA NIE MOZE ORZEC
-----------------------------
"Funding dziala". Wykrywalnosc przy tym `n` zaczyna sie od ~54%. Runda ma natomiast moc
orzec, ze funding NIE WYNOSI trafnosci do progu oplacalnosci.

Uzycie:
    py -m backtest.run_funding_measured_f1
"""

from __future__ import annotations

import numpy as np
import yaml

from agents.funding_features import FUNDING_COLUMN, attach_funding_rate
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.metrics import (
    Z_TWO_SIDED_95,
    measurability_report,
    required_trades,
    wald_half_width,
)
from data.fetch_funding import get_funding_rate_history_cached

# --- KONFIGURACJA ZAMROZONA (identyczna z H2.1, jedyna roznica: wagi klas z A1) ---
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

RAMIONA = {
    "A": ("odniesienie: 4 cechy OHLCV", REVERSION_FEATURES, 0),
    "B": ("kandydat: 4 cechy + funding_rate", [*REVERSION_FEATURES, FUNDING_COLUMN], 1),
}

# Prog pre-rejestrowany — WPISANY, nie liczony po wyniku.
N_WYMAGANE_DO_NEGATYWU = 4481

FUNNEL = (
    ("ocenione swiece", "n_rows_evaluated"),
    ("odpadlo na abstynencji", "n_signals_no_direction"),
    ("bramka pewnosci", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnaly", "n_signals"),
)

SEP = "=" * 104


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    df = _load(cfg, TIMEFRAME)

    funding = get_funding_rate_history_cached(
        symbol=cfg["primary_symbol"],
        start=(cfg.get("timeframe_start_overrides") or {}).get("4h", cfg["start"]),
        end=cfg["end"],
        cache_dir=cfg["cache_dir"],
        exchange_id=cfg["exchange_id"],
    )
    df = attach_funding_rate(df, funding)
    n_nan = int(df[FUNDING_COLUMN].isna().sum())

    print(SEP)
    print("F1 — FUNDING jako cecha, na przyrzadzie po adopcji A1 (konfiguracja ZAMROZONA)")
    print(SEP)
    print(
        f"dane      : {len(df)} swiec {TIMEFRAME}, {df['timestamp'].min()} -> {df['timestamp'].max()}\n"
        f"funding   : {len(funding)} rozliczen; swiec ze stawka {df[FUNDING_COLUMN].notna().sum()}, "
        f"NaN {n_nan} (sprzed 1. rozliczenia — wypadna jak rozbieg wskaznika)\n"
        f"pipeline  : BEZ bramki rezimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced` (A1),\n"
        f"            walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}\n"
        f"JEDNA zmienna: obecnosc cechy `{FUNDING_COLUMN}` (zasada 4).\n"
    )

    wyniki = {}
    for kod, (opis, cechy, _w) in RAMIONA.items():
        res = run_and_summarize(
            df,
            seed=PRIMARY_SEED,
            regime_feature_sets=[(REGIME_ALL, cechy)],
            vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
            candles_per_day=CANDLES_PER_DAY,
            candle_minutes=CANDLE_MINUTES,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            trend_threshold=rule["trend_threshold"],
            range_threshold=rule["range_threshold"],
        )
        e = res["edge_per_regime"].iloc[0]
        aktywne = [f for f in res["backtest"]["folds_summary"] if not f["skipped"]]
        trades = res["backtest"]["trades"]
        realne = trades.loc[~trades["kill_switch_active"]]
        wyniki[kod] = {
            "opis": opis,
            "lejek": {k: sum(f[k] for f in aktywne) for _, k in FUNNEL},
            "stlumione": int(trades["kill_switch_active"].sum()),
            "pominiete": len(res["backtest"]["folds_summary"]) - len(aktywne),
            "wszystkie": len(res["backtest"]["folds_summary"]),
            "n": int(e["n_trades"]),
            "trafienia": int((realne["gross_pnl"] > 0).sum()),
            "p": float(e["hit_rate"]),
            "ci_low": float(e["ci_low"]),
            "ci_high": float(e["ci_high"]),
            "break_even": float(e["break_even_p"]),
            "barrier": float(e["barrier_pct"]),
            "cost": float(e["cost_pct"]),
            "edge": res["edge_per_regime"],
            "klasyfikacja": res["classification"],
        }
        print(f"  policzone: ramie {kod} ({opis})")

    a, b = wyniki["A"], wyniki["B"]

    print("\n" + SEP)
    print("1. WYNIK — trafnosc wobec progu oplacalnosci")
    print(SEP)
    print(f"  {'ramie':>6} | {'n':>7} | {'trafnosc':>9} | {'CI 95%':>20} | {'prog BE':>8} | {'margines':>10}")
    print("  " + "-" * 78)
    for kod in RAMIONA:
        w = wyniki[kod]
        print(
            f"  {kod:>6} | {w['n']:7d} | {100 * w['p']:8.2f}% | "
            f"[{100 * w['ci_low']:7.2f}%; {100 * w['ci_high']:7.2f}%] | "
            f"{100 * w['break_even']:7.2f}% | {100 * (w['p'] - w['break_even']):+9.2f} pp"
        )

    print("\n" + SEP)
    print("2. LEJEK — kogo NIE ma w zbiorze")
    print(SEP)
    print(f"  {'etap':>26} | {'ramie A':>10} | {'ramie B':>10}")
    print("  " + "-" * 52)
    for etykieta, klucz in FUNNEL:
        print(f"  {etykieta:>26} | {a['lejek'][klucz]:10d} | {b['lejek'][klucz]:10d}")
    print(f"  {'stlumione kill-switchem':>26} | {a['stlumione']:10d} | {b['stlumione']:10d}")
    print(f"  {'W PROBIE (n)':>26} | {a['n']:10d} | {b['n']:10d}")
    for kod in RAMIONA:
        w = wyniki[kod]
        bilans = w["lejek"]["n_rows_evaluated"] == (
            w["lejek"]["n_signals"]
            + w["lejek"]["n_signals_no_direction"]
            + w["lejek"]["n_signals_cost_gated"]
            + w["lejek"]["n_signals_confidence_gated"]
        )
        print(f"    ramie {kod}: foldy pominiete {w['pominiete']}/{w['wszystkie']}, "
              f"bilans lejka domyka sie: {bilans}")

    print("\n" + SEP)
    print("3. KRYTERIUM — zapisane PRZED uruchomieniem")
    print(SEP)
    moc_ok = b["n"] >= N_WYMAGANE_DO_NEGATYWU
    print(
        f"  wymagane n do orzeczenia NEGATYWU (moc 80%) : {N_WYMAGANE_DO_NEGATYWU:,}\n"
        f"  zmierzone n w ramieniu B                    : {b['n']:,}  "
        f"({b['n'] / N_WYMAGANE_DO_NEGATYWU:.2f}x)  -> moc {'WYSTARCZA' if moc_ok else 'NIE WYSTARCZA'}\n"
        f"  pasmo przy tym n                            : {100 * wald_half_width(b['n']):.2f} pp\n"
    )
    if not moc_ok:
        werdykt = "NIEROZSTRZYGNIETY — n ponizej proby wymaganej do orzeczenia negatywu"
    elif b["ci_low"] > b["break_even"]:
        werdykt = "POZYTYWNY — ci_low > prog. SZUKAJ PRZECIEKU, nie ogłaszaj (funding ma wlasna siatke czasowa)"
    elif b["ci_high"] < b["break_even"]:
        werdykt = "NEGATYWNY — ci_high < prog. Funding NIE wynosi trafnosci do progu"
    else:
        werdykt = "NIEROZSTRZYGNIETY — CI przecina prog, nie interpretujemy w zadna strone"
    print(f"  >>> WERDYKT F1: {werdykt}")

    print("\n" + SEP)
    print("4. OBSERWACJA (NIE kryterium) — czy ramiona sie od siebie roznia")
    print(SEP)
    pa, pb = a["trafienia"] / a["n"], b["trafienia"] / b["n"]
    se = np.sqrt(pa * (1 - pa) / a["n"] + pb * (1 - pb) / b["n"])
    delta = pb - pa
    print(
        f"  trafnosc A = {100 * pa:.2f}%   trafnosc B = {100 * pb:.2f}%\n"
        f"  roznica B - A = {100 * delta:+.2f} pp, 95% CI "
        f"[{100 * (delta - Z_TWO_SIDED_95 * se):+.2f}; {100 * (delta + Z_TWO_SIDED_95 * se):+.2f}] pp, "
        f"z = {delta / se:+.2f}\n"
        f"  >>> {'ROZNICA ISTOTNA' if abs(delta / se) > Z_TWO_SIDED_95 else 'ROZNICA NIEISTOTNA'}"
    )
    print(
        f"\n  LICZBA DECYZJI: A = {a['lejek']['n_signals']:,}, B = {b['lejek']['n_signals']:,} "
        f"({b['lejek']['n_signals'] / a['lejek']['n_signals']:.2f}x).\n"
        "  H2.1 ustalilo, ze funding POTRAJA liczbe decyzji (35 -> 98). Pre-rejestracja F1\n"
        "  mowi wprost: to NIE jest wynik. 'Model chetniej dziala' != 'model dziala lepiej'."
    )

    print("\n" + SEP)
    print("5. MIERZALNOSC ex post (zasada 18)")
    print(SEP)
    for kod in RAMIONA:
        w = wyniki[kod]
        r = measurability_report(w["p"], w["break_even"], w["n"])
        print(f"  ramie {kod}: prog wykrywalnosci {100 * r['p_detectable']:.2f}%, "
              f"zmierzone {100 * w['p']:.2f}% -> {r['verdict']}")
    print(f"\n  required_trades({100 * pb:.2f}% vs prog {100 * b['break_even']:.2f}%) = "
          f"{required_trades(pb, b['break_even']):,.0f}")

    print("\n" + SEP)
    print("6. GEOMETRIA I PELNE TABELE (do raw_output)")
    print(SEP)
    print(f"  {'ramie':>6} | {'bariera B':>11} | {'koszt C':>10} | {'C/B':>8}")
    for kod in RAMIONA:
        w = wyniki[kod]
        print(f"  {kod:>6} | {100 * w['barrier']:10.4f}% | {100 * w['cost']:9.4f}% | "
              f"{w['cost'] / w['barrier']:8.4f}")
    print()
    for kod in RAMIONA:
        w = wyniki[kod]
        print(f"  --- ramie {kod}: {w['opis']} ---")
        print("  " + w["edge"].to_string(index=False).replace("\n", "\n  "))
        print("  " + str(w["klasyfikacja"]))
        print("  UWAGA: `classification` NIE jest kryterium (wniosek skumulowany 24).\n")


if __name__ == "__main__":
    main()
