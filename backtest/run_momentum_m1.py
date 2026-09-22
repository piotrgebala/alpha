"""
run_momentum_m1.py

M1 — momentum po raz pierwszy na probie zdolnej cokolwiek rozstrzygnac. Skrypt
jednorazowy/analityczny, zbudowany na `backtest/checkpoint_lib.py` (zasada 13).

KONFIGURACJA I KRYTERIUM SA ZAMROZONE w pre-rejestracji zapisanej w OSOBNYM commicie
PRZED kodem: `runs/2026-09-22_m1-momentum-bez-bramki/README.md`.

DLACZEGO TA RUNDA ISTNIEJE
--------------------------
Wniosek skumulowany 12 wymienia momentum jako rzecz, ktorej Faza 0 NIE wykazala: probe
zagladzila sama bramka rezimu (0,53% swiec), wiec byla to NIEWYKONALNOSC POMIARU, a nie
brak edge'u. 96% liczby zamykajacej Faze 0 (7 687 transakcji) to cechy mean-reversion;
momentum zmierzono na 299 transakcjach z przedzialem szerokim na 11 punktow.

Zdjecie bramki (H2.1a) i adopcja wag klas (K2 -> K3) daja na tej konfiguracji ~8 000
transakcji zamiast 35. Dopiero to czyni pomiar wykonalnym.

CZEGO TA RUNDA NIE MOZE ORZEC
-----------------------------
"Momentum dziala". Wykrywalnosc przy tym `n` zaczyna sie od 54,02% trafnosci, czyli wyzej
niz cokolwiek, co projekt kiedykolwiek zmierzyl. Runda ma natomiast moc orzec, ze momentum
NIE DOBIJA do progu oplacalnosci: required_trades(50,84% wobec 52,93%) = 4 481, a mamy
~8 100 — 1,8x wymaganej proby przy mocy 80%.

Uzycie:
    py -m backtest.run_momentum_m1
"""

from __future__ import annotations

import yaml

from agents.ml_optimizer import MOMENTUM_FEATURES, REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.metrics import measurability_report, required_trades, wald_half_width

# --- KONFIGURACJA ZAMROZONA (identyczna z K3/C2, zmienia sie WYLACZNIE zestaw cech) ---
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

RAMIONA = {
    "A": ("odniesienie: REVERSION (4 cechy)", REVERSION_FEATURES, 0),
    "B": ("kandydat: MOMENTUM (4 cechy)", MOMENTUM_FEATURES, 1),
}

# Progi pre-rejestrowane — wpisane, NIE liczone po wyniku.
N_WYMAGANE_DO_NEGATYWU = 4481  # required_trades(50,84% vs 52,93%), moc 80%
POMIAR_MOMENTUM_5M = 0.5084  # jedyny istniejacy pomiar momentum (n=299, 5m)

SEP = "=" * 104


def _przebieg(raw, rule, cechy):
    return run_and_summarize(
        raw,
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


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    raw = _load(cfg, TIMEFRAME)

    print(SEP)
    print("M1 — MOMENTUM bez bramki rezimu (konfiguracja i kryterium ZAMROZONE)")
    print(SEP)
    print(
        f"dane      : {len(raw)} swiec {TIMEFRAME}, {raw['timestamp'].min()} -> {raw['timestamp'].max()}\n"
        f"pipeline  : BEZ bramki rezimu, V={VERTICAL_BARRIER_CANDLES}, wagi klas `balanced` (A1),\n"
        f"            walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}\n"
        f"ramie A   : {REVERSION_FEATURES}\n"
        f"ramie B   : {MOMENTUM_FEATURES}\n"
        f"JEDNA zmienna: zestaw cech. Wszystko inne identyczne (zasada 4).\n"
    )

    wyniki = {}
    for kod, (opis, cechy, _war) in RAMIONA.items():
        res = _przebieg(raw, rule, cechy)
        edge = res["edge_per_regime"]
        e = edge.iloc[0] if len(edge) else None
        aktywne = [f for f in res["backtest"]["folds_summary"] if not f["skipped"]]
        n_rows = sum(f["n_rows_evaluated"] for f in aktywne)
        n_abst = sum(f["n_signals_no_direction"] for f in aktywne)
        wyniki[kod] = {
            "opis": opis,
            "n": int(e["n_trades"]),
            "p": float(e["hit_rate"]),
            "ci_low": float(e["ci_low"]),
            "ci_high": float(e["ci_high"]),
            "break_even": float(e["break_even_p"]),
            "barrier": float(e["barrier_pct"]),
            "cost": float(e["cost_pct"]),
            "share_timeout": float(e["share_timeout"]),
            "abstynencja": n_abst / n_rows if n_rows else float("nan"),
            "n_rows": n_rows,
            "edge": edge,
            "klasyfikacja": res["classification"],
        }
        print(f"  policzone: ramie {kod} ({opis})")

    print("\n" + SEP)
    print("1. WYNIK — trafnosc wobec progu oplacalnosci")
    print(SEP)
    print(
        f"  {'ramie':>6} | {'abstyn.':>8} | {'n':>7} | {'trafnosc':>9} | {'CI 95%':>20} | "
        f"{'prog BE':>8} | {'margines':>10}"
    )
    print("  " + "-" * 88)
    for kod in RAMIONA:
        w = wyniki[kod]
        print(
            f"  {kod:>6} | {100 * w['abstynencja']:7.2f}% | {w['n']:7d} | {100 * w['p']:8.2f}% | "
            f"[{100 * w['ci_low']:7.2f}%; {100 * w['ci_high']:7.2f}%] | {100 * w['break_even']:7.2f}% | "
            f"{100 * (w['p'] - w['break_even']):+9.2f} pp"
        )

    print("\n" + SEP)
    print("2. GEOMETRIA — skad bierze sie prog (wielkosci niezalezne od trafnosci)")
    print(SEP)
    print(f"  {'ramie':>6} | {'bariera B':>11} | {'koszt C':>10} | {'C/B':>8} | {'udzial timeout':>15}")
    print("  " + "-" * 62)
    for kod in RAMIONA:
        w = wyniki[kod]
        print(
            f"  {kod:>6} | {100 * w['barrier']:10.4f}% | {100 * w['cost']:9.4f}% | "
            f"{w['cost'] / w['barrier']:8.4f} | {100 * w['share_timeout']:14.2f}%"
        )

    print("\n" + SEP)
    print("3. KRYTERIUM — zapisane PRZED uruchomieniem")
    print(SEP)
    b = wyniki["B"]
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
        werdykt = "POZYTYWNY — ci_low > prog. PIERWSZY w historii projektu: szukaj przecieku, nie ogłaszaj"
    elif b["ci_high"] < b["break_even"]:
        werdykt = "NEGATYWNY — ci_high < prog. Momentum NIE dobija do progu oplacalnosci"
    else:
        werdykt = "NIEROZSTRZYGNIETY — CI przecina prog, nie interpretujemy w zadna strone"
    print(f"  >>> WERDYKT M1: {werdykt}")

    print("\n" + SEP)
    print("4. MIERZALNOSC ex post (zasada 18) — czy pytanie bylo dobrze postawione")
    print(SEP)
    for kod in RAMIONA:
        w = wyniki[kod]
        r = measurability_report(w["p"], w["break_even"], w["n"])
        print(
            f"  ramie {kod}: prog wykrywalnosci {100 * r['p_detectable']:.2f}%, "
            f"zmierzone {100 * w['p']:.2f}% -> {r['verdict']}"
        )
    print(
        f"\n  Kontrola zalozenia z pre-rejestracji: required_trades({100 * POMIAR_MOMENTUM_5M:.2f}% "
        f"vs {100 * b['break_even']:.2f}%) = {required_trades(POMIAR_MOMENTUM_5M, b['break_even']):,.0f}"
    )

    print("\n" + SEP)
    print("5. PELNE TABELE (do raw_output)")
    print(SEP)
    for kod in RAMIONA:
        w = wyniki[kod]
        print(f"  --- ramie {kod}: {w['opis']} ---")
        print("  " + w["edge"].to_string(index=False).replace("\n", "\n  "))
        print("  " + str(w["klasyfikacja"]))
        print(
            "  UWAGA: `classification` NIE jest kryterium tej rundy — K1 wykazalo, ze potrafi\n"
            "  zwrocic GO czystemu szumowi (wniosek skumulowany 24).\n"
        )


if __name__ == "__main__":
    main()
