"""
run_measurability_k3.py

K3 — czy adopcja A1 (wagi klas) przenosi sie z syntetycznej wyroczni na REALNE cechy.
Skrypt jednorazowy/analityczny, zbudowany na `backtest/checkpoint_lib.py` (zasada 13).

KONFIGURACJE I REGULY ODCZYTU SA ZAMROZONE w pre-rejestracji zapisanej w OSOBNYM commicie
PRZED kodem: `runs/2026-09-22_k3-mierzalnosc-po-a1/README.md`.

CO TEN SKRYPT MIERZY
--------------------
Ile DECYZJI podejmuje model - nie czy sa trafne. S1b (n=345) i H2.1 (n=98) dostaly werdykt
"nierozstrzygniety" wylacznie dlatego, ze proba byla za mala. Obie mierzono modelem, ktory
odmawial kierunku w 90,5% i 99,32% swiec. K2 pokazala, ze wagi klas to naprawiaja NA
WYROCZNI; tutaj sprawdzamy realne cechy.

CZEGO NIE RAPORTUJE (regula D pre-rejestracji)
----------------------------------------------
Trafnosci, CI trafnosci, z_stat, marginesu ani klasyfikacji. Te trafiaja do `raw_output.txt`
(zasada 11 jest bezwarunkowa), ale sekcja "Wynik" i decyzja ich nie uzywaja.

Powod NIE jest kosmetyczny: obie konfiguracje naleza do serii ZAMKNIETYCH (C1 - regula STOP
hipotezy jednorezimowej, C2 - licznik H2 wyczerpany 1/1). Zaraportowanie ich trafnosci byloby
ponownym spojrzeniem na target w zamknietej serii, czyli wznowieniem jej tylnymi drzwiami.

Uzycie:
    py -m backtest.run_measurability_k3
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from agents.feature_miner import compute_all_features
from agents.labeling import compute_triple_barrier_labels
from agents.ml_optimizer import (
    CLASS_WEIGHT_BALANCED,
    CLASS_WEIGHT_NONE,
    REVERSION_FEATURES,
)
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.metrics import min_detectable_hit_rate, wald_half_width

# --- KONFIGURACJA ZAMROZONA (identyczna z S1b / H2.1 ramie A) ---
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28

# Dwie konfiguracje, ktore dostaly werdykt "nierozstrzygniety" z powodu wielkosci proby.
KONFIGURACJE = {
    "C1": {
        "opis": "bramka rezimu `range` (S1b)",
        "regime_feature_sets": [("range", REVERSION_FEATURES)],
        "n_przed": 345,
        "abstynencja_przed": 0.905,
        "runda": "S1b",
    },
    "C2": {
        "opis": "BEZ bramki rezimu (H2.1 ramie A)",
        "regime_feature_sets": [(REGIME_ALL, REVERSION_FEATURES)],
        "n_przed": 98,
        "abstynencja_przed": 0.9932,
        "runda": "H2.1",
    },
}

RAMIONA = {
    "none": ("stan SPRZED adopcji A1", CLASS_WEIGHT_NONE),
    "balanced": ("stan PO adopcji A1", CLASS_WEIGHT_BALANCED),
}

# Kotwica odczytu, zlozona z DWOCH ZMIERZONYCH liczb projektu (pre-rejestracja):
#   luka = prog oplacalnosci (H3) - zmierzona trafnosc projektu (Z10)
PROG_OPLACALNOSCI_H3 = 0.5269
TRAFNOSC_PROJEKTU_Z10 = 0.5027
LUKA_PP = 100 * (PROG_OPLACALNOSCI_H3 - TRAFNOSC_PROJEKTU_Z10)

FUNNEL = (
    ("ocenione swiece", "n_rows_evaluated"),
    ("odpadlo na abstynencji", "n_signals_no_direction"),
    ("bramka pewnosci", "n_signals_confidence_gated"),
    ("bramka kosztowa", "n_signals_cost_gated"),
    ("sygnaly", "n_signals"),
)

SEP = "=" * 104


def _przebieg(raw: pd.DataFrame, rule: dict, cfg: dict, tryb_wag: str) -> dict:
    res = run_and_summarize(
        raw,
        seed=PRIMARY_SEED,
        regime_feature_sets=cfg["regime_feature_sets"],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        candle_minutes=CANDLE_MINUTES,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        class_weight_mode=tryb_wag,
    )

    wszystkie = res["backtest"]["folds_summary"]
    aktywne = [f for f in wszystkie if not f["skipped"]]
    lejek = {klucz: sum(f[klucz] for f in aktywne) for _, klucz in FUNNEL}

    trades = res["backtest"]["trades"]
    stlumione = int(trades["kill_switch_active"].sum())
    n = int((~trades["kill_switch_active"]).sum())

    edge = res["edge_per_regime"]
    e = edge.iloc[0] if len(edge) else None
    break_even = float(e["break_even_p"]) if e is not None else float("nan")

    return {
        "lejek": lejek,
        "foldy_pominiete": len(wszystkie) - len(aktywne),
        "foldy_wszystkie": len(wszystkie),
        "stlumione": stlumione,
        "n": n,
        "abstynencja": (
            lejek["n_signals_no_direction"] / lejek["n_rows_evaluated"]
            if lejek["n_rows_evaluated"] else float("nan")
        ),
        "break_even": break_even,
        "pasmo_pp": 100 * wald_half_width(n) if n > 0 else float("nan"),
        "min_wykrywalna": min_detectable_hit_rate(break_even, n) if n > 0 else float("nan"),
        # Objete zakazem raportowania (regula D) - tylko do raw_output.
        "_zakazane": res["edge_per_regime"],
        "_klasyfikacja": res["classification"],
    }


def main() -> None:
    cfg_data = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    raw = _load(cfg_data, TIMEFRAME)

    feats = compute_all_features(
        raw,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        candles_per_day=CANDLES_PER_DAY,
    )
    labeled = compute_triple_barrier_labels(feats, vertical_barrier_candles=VERTICAL_BARRIER_CANDLES)
    podloga = float((labeled["label"] == 0.0).mean())

    print(SEP)
    print("K3 — MIERZALNOSC PO ADOPCJI A1 (konfiguracje i reguly odczytu ZAMROZONE)")
    print(SEP)
    print(
        f"dane      : {len(raw)} swiec {TIMEFRAME}, {raw['timestamp'].min()} -> {raw['timestamp'].max()}\n"
        f"cechy     : {REVERSION_FEATURES}  (bez `oracle` — to sa REALNE cechy)\n"
        f"pipeline  : V={VERTICAL_BARRIER_CANDLES}, walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, "
        f"seed {PRIMARY_SEED}\n"
        f"PODLOGA abstynencji (udzial klasy timeout w etykietach) = {100 * podloga:.2f}%\n"
        f"KOTWICA ODCZYTU: luka = {100 * PROG_OPLACALNOSCI_H3:.2f}% (prog, H3) − "
        f"{100 * TRAFNOSC_PROJEKTU_Z10:.2f}% (trafnosc, Z10) = {LUKA_PP:.2f} pp\n"
    )

    wyniki: dict[tuple[str, str], dict] = {}
    for kod, cfg in KONFIGURACJE.items():
        for tryb, (opis_ramienia, wartosc) in RAMIONA.items():
            wyniki[(kod, tryb)] = _przebieg(raw, rule, cfg, wartosc)
            print(f"  policzone: {kod} / {tryb:8s} ({cfg['opis']}, {opis_ramienia})")

    # --- 1. LEJEK: kogo NIE ma w zbiorze (zasada 16a) ---
    print("\n" + SEP)
    print("1. LEJEK — kogo NIE ma w zbiorze")
    print(SEP)
    for kod, cfg in KONFIGURACJE.items():
        print(f"\n  {kod}: {cfg['opis']}")
        print(f"    {'etap':>26} | {'none':>12} | {'balanced':>12} | {'zmiana':>12}")
        print("    " + "-" * 70)
        for etykieta, klucz in FUNNEL:
            a = wyniki[(kod, "none")]["lejek"][klucz]
            b = wyniki[(kod, "balanced")]["lejek"][klucz]
            print(f"    {etykieta:>26} | {a:12d} | {b:12d} | {b - a:+12d}")
        a, b = wyniki[(kod, "none")], wyniki[(kod, "balanced")]
        print(f"    {'stlumione kill-switchem':>26} | {a['stlumione']:12d} | {b['stlumione']:12d} | "
              f"{b['stlumione'] - a['stlumione']:+12d}")
        print(f"    {'W PROBIE (n)':>26} | {a['n']:12d} | {b['n']:12d} | {b['n'] - a['n']:+12d}")
        print(f"    foldy pominiete: none {a['foldy_pominiete']}/{a['foldy_wszystkie']}, "
              f"balanced {b['foldy_pominiete']}/{b['foldy_wszystkie']}")
        bilans = all(
            w["lejek"]["n_rows_evaluated"]
            == w["lejek"]["n_signals"] + w["lejek"]["n_signals_no_direction"]
            + w["lejek"]["n_signals_cost_gated"] + w["lejek"]["n_signals_confidence_gated"]
            for w in (a, b)
        )
        print(f"    bilans lejka domyka sie: {bilans}")

    # --- 2. ABSTYNENCJA wobec podlogi ---
    print("\n" + SEP)
    print("2. ABSTYNENCJA wobec PODLOGI wyznaczonej rozkladem etykiet")
    print(SEP)
    print(f"  PODLOGA = {100 * podloga:.2f}%\n")
    print(f"  {'konf.':>6} | {'runda':>6} | {'przed (zapis)':>14} | {'none':>9} | {'balanced':>9} | {'zmiana':>9}")
    print("  " + "-" * 68)
    for kod, cfg in KONFIGURACJE.items():
        a, b = wyniki[(kod, "none")], wyniki[(kod, "balanced")]
        print(
            f"  {kod:>6} | {cfg['runda']:>6} | {100 * cfg['abstynencja_przed']:13.2f}% | "
            f"{100 * a['abstynencja']:8.2f}% | {100 * b['abstynencja']:8.2f}% | "
            f"{100 * (b['abstynencja'] - a['abstynencja']):+8.2f} pp"
        )

    # --- 3. MIERZALNOSC ---
    print("\n" + SEP)
    print("3. MIERZALNOSC — pasmo 'oplacalne, ale NIEWIDZIALNE' i prog wykrywalnosci")
    print(SEP)
    print(f"  {'konf.':>6} | {'ramie':>9} | {'n':>8} | {'prog BE':>8} | {'pasmo':>9} | "
          f"{'min. wykrywalna trafnosc':>25}")
    print("  " + "-" * 82)
    for kod in KONFIGURACJE:
        for tryb in RAMIONA:
            w = wyniki[(kod, tryb)]
            print(
                f"  {kod:>6} | {tryb:>9} | {w['n']:8d} | {100 * w['break_even']:7.2f}% | "
                f"{w['pasmo_pp']:8.2f}pp | {100 * w['min_wykrywalna']:24.2f}%"
            )
        print("  " + "-" * 82)

    # --- 4. ODCZYT wg reguly zapisanej PRZED uruchomieniem ---
    print("\n" + SEP)
    print("4. ODCZYT — regula zapisana PRZED uruchomieniem")
    print(SEP)
    print(f"  Kotwica: luka do zamkniecia = {LUKA_PP:.2f} pp (52,69% H3 − 50,27% Z10).\n")
    for kod, cfg in KONFIGURACJE.items():
        a, b = wyniki[(kod, "none")], wyniki[(kod, "balanced")]
        spadla = b["abstynencja"] < a["abstynencja"] - 0.01  # >1 pp, poza szumem zaokraglen
        if not spadla:
            odczyt = "(c) ABSTYNENCJA NIE SPADA — A1 nie przenosi sie z wyroczni na realne cechy"
        elif b["pasmo_pp"] < LUKA_PP:
            odczyt = "(a) MIERZALNE — pasmo wezsze niz luka; konfiguracja wraca do gry"
        else:
            odczyt = "(b) POPRAWA REALNA, ALE NIEWYSTARCZAJACA — priorytetem zostaje T4"
        print(
            f"  {kod} ({cfg['opis']}):\n"
            f"      abstynencja {100 * a['abstynencja']:.2f}% -> {100 * b['abstynencja']:.2f}%, "
            f"n {a['n']} -> {b['n']}, pasmo {a['pasmo_pp']:.2f}pp -> {b['pasmo_pp']:.2f}pp\n"
            f"      >>> {odczyt}\n"
        )
    print(
        "  PRZYPOMNIENIE Z PRE-REJESTRACJI: wzrost `n` jest TAUTOLOGIA, nie odkryciem.\n"
        "  Ta runda nie moze stwierdzic, ze cokolwiek zarabia — najwyzej, ze pewne pytania\n"
        "  wolno znow zadac. Wezsze pasmo przy rozcienczonym sygnale to pulapka A2 z K2,\n"
        "  a ta runda NIE MA JAK jej wykryc, bo nie patrzy na trafnosc."
    )

    # --- 5. LICZBY OBJETE ZAKAZEM (regula D) ---
    print("\n" + SEP)
    print("5. LICZBY OBJETE ZAKAZEM RAPORTOWANIA (regula D) — tylko do raw_output")
    print(SEP)
    print("  Ponizsze NIE sa wynikiem tej rundy i nie uczestnicza w zadnej decyzji.")
    print("  Obie konfiguracje naleza do serii ZAMKNIETYCH — ich trafnosc jest poza zasiegiem\n"
          "  tej rundy, bo jej raportowanie wznowiloby seria tylnymi drzwiami.\n")
    for kod in KONFIGURACJE:
        for tryb in RAMIONA:
            w = wyniki[(kod, tryb)]
            print(f"  --- {kod} / {tryb} ---")
            print("  " + w["_zakazane"].to_string(index=False).replace("\n", "\n  "))
            print("  " + str(w["_klasyfikacja"]))
            print()


if __name__ == "__main__":
    main()
