"""
run_abstention_fix_k2.py

K2 — naprawa abstynencji + pochodzenie obciazenia na szumie (T6). Skrypt
jednorazowy/analityczny, zbudowany na `backtest/checkpoint_lib.py` (CLAUDE.md zasada 13).

KONFIGURACJA I REGULY DECYZJI SA ZAMROZONE w pre-rejestracji zapisanej w OSOBNYM commicie
PRZED kodem: `runs/2026-09-22_k2-naprawa-abstynencji/README.md` (commit 121c300).
Ten skrypt niczego nie dobiera - wykonuje zapisany plan i drukuje liczby.

CO MIERZY
---------
Abstynencja modelu (udzial swiec, na ktorych odmawia kierunku) zapada sie przy slabym
sygnale do ~99,5%, podczas gdy podloga wyznaczona rozkladem etykiet to ~66,6%. To ona,
a nie brak sygnalu, ograniczyla probe w S1b (n=345), H2.1 (n=98) i K1 (n~37).

Trzy ramiona, kazde na TEJ SAMEJ krzywej wykrywalnosci co K1 (wyrocznia o znanej sile `q`):
  A0 baseline    - dzisiejszy kod; regresja bit-identycznosci i punkt odniesienia
  A1 wagi klas   - `class_weight_mode="balanced"`; model NADAL moze odmowic (naprawa miekka)
  A2 wymuszenie  - `direction_policy="forced"` + `confidence_mode="conditional"`;
                   abstynencja z konstrukcji = 0%

CZEGO TEN SKRYPT NIE ROBI
-------------------------
Nie testuje zadnej hipotezy tradingowej i nie dotyka zadnego licznika wariantow (0 wariantow,
POZA licznikami - ta sama rola co K1, Z19, Z9). `oracle` nie wchodzi do
`feature_registry.yaml`. Warunek utrzymania zera zapisany w pre-rejestracji: **zadna liczba
z K2 nie moze byc cytowana jako wynik hipotezy tradingowej.**

Nie oglasza tez zwyciezcy w prozie - stosuje trzy PRE-REJESTROWANE bramki i drukuje, ktore
ramie ktora przeszlo. Decyzje o adopcji podpisuje czlowiek w README rundy.

Uzycie:
    py -m backtest.run_abstention_fix_k2
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import yaml

from agents.feature_miner import compute_all_features
from agents.labeling import compute_triple_barrier_labels
from agents.ml_optimizer import (
    CLASS_WEIGHT_BALANCED,
    CLASS_WEIGHT_NONE,
    CONFIDENCE_MODE_CLASS,
    CONFIDENCE_MODE_CONDITIONAL,
    DIRECTION_POLICY_ARGMAX3,
    DIRECTION_POLICY_FORCED,
    REVERSION_FEATURES,
)
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from backtest.metrics import observed_wald_ci, wald_half_width

# `_inject_oracle` IMPORTOWANE z K1, nie skopiowane. Druga kopia definicji wyroczni
# oznaczalaby, ze krzywe K1 i K2 moglyby sie rozjechac bez sladu w diffie - dokladnie
# klasa bledu, ktora H3 usunelo przy bramce kosztowej.
from backtest.run_positive_control_k1 import _inject_oracle

# --- KONFIGURACJA ZAMROZONA (identyczna z K1/S1b/H2.1) ---
TIMEFRAME = "4h"
VERTICAL_BARRIER_CANDLES = 3
CANDLES_PER_DAY = 6
CANDLE_MINUTES = 240
TRAIN_DAYS = 60
TEST_DAYS = 28
STEP_DAYS = 28
ORACLE = "oracle"

# --- SIATKA ZAMROZONA (pre-rejestracja, sekcja "Siatka i replikacja") ---
# K1 mial JEDNO losowanie na punkt - porownanie trzech ramion na takich krzywych
# porownywaloby trzy szumy, nie trzy ramiona.
GRID_FULL = {0.00: 12, 0.10: 3, 0.20: 3, 0.30: 3, 0.40: 3, 1.00: 1}
# Plan awaryjny, rowniez pre-rejestrowany: uruchamiany TYLKO gdy jeden przebieg A0
# przekroczy COST_GATE_SECONDS. Decyzja zapisana PRZED obejrzeniem wyniku.
GRID_REDUCED = {0.00: 3, 0.10: 2, 0.20: 2, 0.30: 2, 0.40: 2, 1.00: 1}
COST_GATE_SECONDS = 240.0

ARMS = {
    "A0": {"class_weight_mode": CLASS_WEIGHT_NONE,
           "direction_policy": DIRECTION_POLICY_ARGMAX3,
           "confidence_mode": CONFIDENCE_MODE_CLASS},
    "A1": {"class_weight_mode": CLASS_WEIGHT_BALANCED,
           "direction_policy": DIRECTION_POLICY_ARGMAX3,
           "confidence_mode": CONFIDENCE_MODE_CLASS},
    "A2": {"class_weight_mode": CLASS_WEIGHT_NONE,
           "direction_policy": DIRECTION_POLICY_FORCED,
           "confidence_mode": CONFIDENCE_MODE_CONDITIONAL},
}
ARM_OPIS = {
    "A0": "baseline (dzisiejszy kod)",
    "A1": "wagi klas `balanced`",
    "A2": "wymuszony kierunek + pewnosc warunkowa",
}

SEP = "=" * 108


def _oracle_seed(q: float, draw: int) -> int:
    """Ziarno per (sila, losowanie). Rozne losowania to NIEZALEZNE repliki tej samej sily."""
    return 100_000 + int(round(q * 100)) * 100 + draw


def _run_once(raw, labels, rule, q: float, draw: int, arm_kwargs: dict, **extra) -> dict:
    """Jeden pelny przebieg pipeline'u dla zadanej sily wyroczni i ramienia."""
    rng = np.random.default_rng(_oracle_seed(q, draw))
    df = raw.copy()
    df[ORACLE] = _inject_oracle(labels, q, rng).reindex(df.index)
    zgodnosc = float((df[ORACLE] == labels).mean())

    res = run_and_summarize(
        df,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, [*REVERSION_FEATURES, ORACLE])],
        vertical_barrier_candles=VERTICAL_BARRIER_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        candle_minutes=CANDLE_MINUTES,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        **arm_kwargs,
        **extra,
    )

    edge = res["edge_per_regime"]
    e = edge.loc[edge["regime"] == REGIME_ALL].iloc[0] if len(edge) else None
    folds = [f for f in res["backtest"]["folds_summary"] if not f["skipped"]]
    n_rows = sum(f["n_rows_evaluated"] for f in folds)
    n_abst = sum(f["n_signals_no_direction"] for f in folds)
    n_trades = int(e["n_trades"]) if e is not None else 0
    hit = float(e["hit_rate"]) if e is not None else float("nan")

    return {
        "q": q,
        "draw": draw,
        "zgodnosc": zgodnosc,
        "n_rows": n_rows,
        "abstynencja": n_abst / n_rows if n_rows else float("nan"),
        "n_trades": n_trades,
        "hits": int(round(hit * n_trades)) if n_trades and not np.isnan(hit) else 0,
        "hit_rate": hit,
        "ci_low": float(e["ci_low"]) if e is not None else float("nan"),
        "ci_high": float(e["ci_high"]) if e is not None else float("nan"),
        "break_even": float(e["break_even_p"]) if e is not None else float("nan"),
        "barrier_pct": float(e["barrier_pct"]) if e is not None else float("nan"),
        "trades": res["backtest"]["trades"],
    }


def _pooled(rows: list[dict]) -> dict:
    """
    Pooled trafnosc + 95% CI, zsumowane po losowaniach.

    Wzor NIE jest tu przepisany - konsumuje `metrics.observed_wald_ci`, to samo zrodlo,
    z ktorego korzysta `compute_hit_rate` per przebieg. Dwie kopie tej algebry mogly by
    sie rozjechac bez sladu w diffie (lekcja H3).
    """
    n = sum(r["n_trades"] for r in rows)
    h = sum(r["hits"] for r in rows)
    ci = observed_wald_ci(h, n)
    return {"n": n, "p": ci["hit_rate"], "half": ci["half_width"],
            "low": ci["ci_low"], "high": ci["ci_high"]}


def _rozrzut(wartosci) -> str:
    """Zakres zamiast falszywej precyzji (zasada 16b): min-mediana-max."""
    v = [x for x in wartosci if not (isinstance(x, float) and np.isnan(x))]
    if not v:
        return "brak"
    return f"{min(v):.2f} / {float(np.median(v)):.2f} / {max(v):.2f}"


def main() -> None:
    cfg = _load_cfg()
    rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
    raw = _load(cfg, TIMEFRAME)

    feats = compute_all_features(
        raw,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        candles_per_day=CANDLES_PER_DAY,
    )
    labeled = compute_triple_barrier_labels(feats, vertical_barrier_candles=VERTICAL_BARRIER_CANDLES)
    labels = labeled["label"]
    udzial_timeout = float((labels == 0.0).mean())

    print(SEP)
    print("K2 — NAPRAWA ABSTYNENCJI (konfiguracja i reguly decyzji ZAMROZONE w pre-rejestracji)")
    print(SEP)
    print(
        f"dane          : {len(raw)} swiec {TIMEFRAME}, {raw['timestamp'].min()} -> {raw['timestamp'].max()}\n"
        f"etykiety      : {labels.notna().sum()} nie-NaN, udzial klasy timeout "
        f"{udzial_timeout * 100:.2f}%  <- PODLOGA abstynencji dla poprawnie dzialajacego modelu\n"
        f"pipeline      : bez bramki rezimu, V={VERTICAL_BARRIER_CANDLES}, "
        f"walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS}, seed {PRIMARY_SEED}\n"
        f"cechy         : {REVERSION_FEATURES} + '{ORACLE}'\n"
    )

    # --- BRAMKA KOSZTOWA (decyzja pre-rejestrowana PRZED obejrzeniem wyniku) ---
    print(SEP)
    print("0. BRAMKA KOSZTOWA — czas jednego przebiegu A0 decyduje o gestosci siatki")
    print(SEP)
    t0 = time.perf_counter()
    proba_a0 = _run_once(raw, labels, rule, 0.0, 0, ARMS["A0"])
    czas_a0 = time.perf_counter() - t0
    grid = GRID_FULL if czas_a0 <= COST_GATE_SECONDS else GRID_REDUCED
    print(f"  jeden przebieg A0 = {czas_a0:.1f}s (prog {COST_GATE_SECONDS:.0f}s)")
    print(f"  >>> SIATKA {'PELNA' if grid is GRID_FULL else 'ZREDUKOWANA'}: {grid}")
    print(f"  laczna liczba przebiegow krzywej = {sum(grid.values()) * len(ARMS)}\n")

    # --- 1. KRZYWE WYKRYWALNOSCI ---
    print(SEP)
    print("1. KRZYWE WYKRYWALNOSCI — trzy ramiona na tej samej wyroczni")
    print(SEP)
    wyniki: dict[str, list[dict]] = {a: [] for a in ARMS}
    for arm, kwargs in ARMS.items():
        for q, n_draws in grid.items():
            for draw in range(n_draws):
                if arm == "A0" and q == 0.0 and draw == 0:
                    wyniki[arm].append(proba_a0)  # nie liczymy tego samego dwa razy
                    continue
                wyniki[arm].append(_run_once(raw, labels, rule, q, draw, kwargs))
        print(f"  {arm} ({ARM_OPIS[arm]}): {len(wyniki[arm])} przebiegow gotowych")

    print(f"\n  {'ramie':>5} | {'q':>5} | {'los.':>4} | {'abstyn.':>8} | {'n':>7} | "
          f"{'trafnosc':>9} | {'CI_low':>8} | {'prog BE':>8} | {'pasmo':>7}")
    print("  " + "-" * 92)
    for arm in ARMS:
        for q in grid:
            rows = [r for r in wyniki[arm] if r["q"] == q]
            pool = _pooled(rows)
            print(
                f"  {arm:>5} | {q:5.2f} | {len(rows):4d} | "
                f"{100 * float(np.nanmean([r['abstynencja'] for r in rows])):7.2f}% | "
                f"{pool['n']:7d} | {100 * pool['p']:8.2f}% | {100 * pool['low']:7.2f}% | "
                f"{100 * float(np.nanmean([r['break_even'] for r in rows])):7.2f}% | "
                f"{100 * wald_half_width(pool['n']) if pool['n'] else float('nan'):6.2f}pp"
            )
        print("  " + "-" * 92)

    # --- 2. BRAMKA 1: SPECYFICZNOSC (veto) ---
    print("\n" + SEP)
    print("2. BRAMKA 1 — SPECYFICZNOSC (NADRZEDNA, veto). Kryterium: na czystym szumie")
    print("   `ci_low > break_even` moze wystrzelic NAJWYZEJ RAZ, a pooled CI musi ZAWIERAC prog.")
    print(SEP)
    bramka1: dict[str, dict] = {}
    for arm in ARMS:
        szum = [r for r in wyniki[arm] if r["q"] == 0.0]
        wystrzaly = [r for r in szum if r["ci_low"] > r["break_even"]]
        pool = _pooled(szum)
        be = float(np.nanmean([r["break_even"] for r in szum]))
        # Czlon A: brak falszywych alarmow (max 1 na 12 losowan).
        czlon_a = len(wystrzaly) <= 1
        # Czlon B, DWA ODCZYTY - patrz sekcja 2b nizej. Skrypt liczy oba i NIE wybiera.
        czlon_b_doslowny = bool(pool["low"] <= be <= pool["high"])
        czlon_b_wg_celu = bool(pool["low"] <= be)
        bramka1[arm] = {
            "wystrzaly": len(wystrzaly),
            "n_losowan": len(szum),
            "pool": pool,
            "be": be,
            "doslowna": czlon_a and czlon_b_doslowny,
            "wg_celu": czlon_a and czlon_b_wg_celu,
        }
        print(
            f"  {arm}: falszywe alarmy {len(wystrzaly)}/{len(szum)} | pooled n={pool['n']:6d} "
            f"p={100 * pool['p']:.2f}% CI=[{100 * pool['low']:.2f}%; {100 * pool['high']:.2f}%] "
            f"prog={100 * be:.2f}%\n"
            f"       odczyt DOSLOWNY (CI zawiera prog)   : "
            f"{'ZDANA' if bramka1[arm]['doslowna'] else 'ODRZUCONE'}\n"
            f"       odczyt WG CELU  (CI nie nad progiem): "
            f"{'ZDANA' if bramka1[arm]['wg_celu'] else 'ODRZUCONE'}"
        )

    # --- 2b. USTERKA W SFORMULOWANIU BRAMKI 1 (zgloszenie, nie obejscie) ---
    print("\n" + SEP)
    print("2b. UWAGA METODOLOGICZNA — dwa odczyty czlonu B bramki 1 daja PRZECIWNE werdykty")
    print(SEP)
    szerokosci = {a: 200 * bramka1[a]["pool"]["half"] for a in ARMS}
    print(
        "  Pre-rejestracja zada, by pooled CI trafnosci ZAWIERALO prog oplacalnosci.\n"
        "  Na czystym szumie prawdziwa trafnosc to ~50%, a prog ~52,9% - te wielkosci sa\n"
        "  ROZNE z zalozenia. CI zawiera prog wylacznie wtedy, gdy jest dostatecznie SZEROKIE,\n"
        "  a szerokosc zalezy wylacznie od n. Tak zapisany czlon B mierzy wiec NIEPRECYZYJNOSC,\n"
        "  nie specyficznosc - i dziala dokladnie przeciwnie do celu rundy, ktorym jest\n"
        "  PODNIESIENIE n.\n"
    )
    print(f"  {'ramie':>5} | {'pooled n':>9} | {'szerokosc CI':>13} | {'|p - prog|':>11} | {'CI zawiera prog':>16}")
    print("  " + "-" * 66)
    for arm in ARMS:
        b = bramka1[arm]
        print(
            f"  {arm:>5} | {b['pool']['n']:9d} | {szerokosci[arm]:12.2f}pp | "
            f"{100 * abs(b['pool']['p'] - b['be']):10.2f}pp | "
            f"{str(b['doslowna']):>16}"
        )
    print(
        "\n  Dowod usterki jest w tej tabeli: A0 przechodzi odczyt doslowny WYLACZNIE dlatego,\n"
        "  ze jego CI jest szerokie. Zadne ramie nie podnioslo falszywego alarmu (0/12 w kazdym),\n"
        "  czyli wg CELU bramki - 'ramie kupujace n kosztem falszywych alarmow jest odrzucone' -\n"
        "  wszystkie trzy sa czyste.\n"
        "  SKRYPT NIE WYBIERA ODCZYTU. Decyzja nalezy do czlowieka i musi byc zapisana\n"
        "  w README rundy jako jawne odstepstwo albo jawne trzymanie sie litery."
    )

    # --- 3. BRAMKA 2: INTEGRALNOSC przy q=1 ---
    print("\n" + SEP)
    print("3. BRAMKA 2 — INTEGRALNOSC lancucha przy q=1,00. Sformulowana WARUNKOWO NA ETYKIECIE,")
    print("   symetrycznie dla wszystkich ramion: trafnosc na transakcjach o prawdziwej")
    print("   etykiecie != 0 ma wynosic ~100%. (A2 wymusza kierunek takze na swiecach timeout,")
    print("   gdzie poprawny kierunek NIE ISTNIEJE - stad zastrzezenie, zapisane Z GORY.)")
    print(SEP)
    # `compute_triple_barrier_labels` zwraca [label, exit_bar_offset] na RangeIndex
    # zgodnym z `feats` - znacznik czasu trzeba dolozyc stamtad.
    ts_label = pd.Series(labeled["label"].to_numpy(), index=feats["timestamp"].to_numpy())
    bramka2: dict[str, float] = {}
    for arm in ARMS:
        wyr = [r for r in wyniki[arm] if r["q"] == 1.0][0]
        tr = wyr["trades"]
        tr = tr.loc[~tr["kill_switch_active"]].copy()
        tr["prawdziwa_etykieta"] = tr["timestamp"].map(ts_label)
        kierunkowe = tr.loc[tr["prawdziwa_etykieta"].notna() & (tr["prawdziwa_etykieta"] != 0.0)]
        p_warunkowa = float((kierunkowe["gross_pnl"] > 0).mean()) if len(kierunkowe) else float("nan")
        bramka2[arm] = p_warunkowa
        print(
            f"  {arm}: n_all={len(tr):6d} | n(etykieta != 0)={len(kierunkowe):6d} | "
            f"trafnosc warunkowa={100 * p_warunkowa:6.2f}% | "
            f"trafnosc bezwarunkowa={100 * float((tr['gross_pnl'] > 0).mean()):6.2f}%"
        )

    # --- 4. BRAMKA 3: METRYKA WYBORU ---
    print("\n" + SEP)
    print("4. BRAMKA 3 — METRYKA WYBORU: najmniejsze `wald_half_width(n)` przy q=0, Z ROZRZUTEM")
    print("   po losowaniach (nie jako punkt). To jest szerokosc pasma 'oplacalne, ale")
    print("   NIEWIDZIALNE' - wlasciwosc przyrzadu, zalezna WYLACZNIE od n.")
    print(SEP)
    print(f"  {'ramie':>5} | {'n/losowanie (min/med/max)':>28} | {'pasmo pp (min/med/max)':>26} | "
          f"{'pooled n':>9} | {'pasmo pooled':>12}")
    print("  " + "-" * 96)
    for arm in ARMS:
        szum = [r for r in wyniki[arm] if r["q"] == 0.0]
        ns = [r["n_trades"] for r in szum]
        pasma = [100 * wald_half_width(n) if n else float("nan") for n in ns]
        pool = _pooled(szum)
        print(
            f"  {arm:>5} | {_rozrzut(ns):>28} | {_rozrzut(pasma):>26} | {pool['n']:9d} | "
            f"{100 * wald_half_width(pool['n']):11.2f}pp"
        )

    # --- 5. ABSTYNENCJA: cel rundy wyrazony LICZBA ---
    print("\n" + SEP)
    print("5. ABSTYNENCJA — cel naprawy wyrazony liczba, nie zyczeniem")
    print(SEP)
    print(f"  PODLOGA (udzial klasy timeout w etykietach) = {udzial_timeout * 100:.2f}%")
    print(f"\n  {'ramie':>5} | " + " | ".join(f"q={q:.2f}" for q in grid))
    print("  " + "-" * (8 + 8 * len(grid)))
    for arm in ARMS:
        kom = []
        for q in grid:
            rows = [r for r in wyniki[arm] if r["q"] == q]
            kom.append(f"{100 * float(np.nanmean([r['abstynencja'] for r in rows])):5.1f}%")
        print(f"  {arm:>5} | " + " | ".join(kom))

    # --- 6. T6: KILL-SWITCH JAKO ZRODLO OBCIAZENIA ---
    print("\n" + SEP)
    print("6. T6 — kill-switch jako zrodlo obciazenia na szumie (eksperyment SELEKCYJNY)")
    print(SEP)
    n_szum = grid[0.00]
    for arm in ("A0", "A2"):
        off_rows, on_rows = [], []
        # Ramie ON to DOKLADNIE przebiegi z sekcji 1 (kill-switch jest tam domyslnie
        # wlaczony) - liczenie ich drugi raz byloby marnowaniem czasu i, co gorsza,
        # otwieraloby mozliwosc cichego rozjazdu miedzy sekcjami.
        on_z_sekcji_1 = [r for r in wyniki[arm] if r["q"] == 0.0]
        for draw in range(n_szum):
            on = on_z_sekcji_1[draw]
            off = _run_once(raw, labels, rule, 0.0, draw, ARMS[arm], kill_switch_enabled=False)

            # ASERCJA OBOWIAZKOWA nr 1 (pre-rejestracja): "wylaczony" ma znaczyc wylaczony,
            # a nie "bardzo malo prawdopodobny". Bez tego 0,99 bylaby cicha konwencja.
            assert off["trades"]["kill_switch_active"].sum() == 0, (
                f"{arm} losowanie {draw}: ramie OFF stlumilo transakcje"
            )
            # ASERCJA OBOWIAZKOWA nr 2: identyczny zbior KANDYDATOW w obu ramionach -
            # dowod, ze T6 jest eksperymentem czysto selekcyjnym.
            klucz = ["regime", "fold_idx", "timestamp"]
            assert set(map(tuple, off["trades"][klucz].to_numpy())) == set(
                map(tuple, on["trades"][klucz].to_numpy())
            ), f"{arm} losowanie {draw}: zbiory kandydatow sie rozjechaly"

            on_rows.append(on)
            off_rows.append(off)

        p_on, p_off = _pooled(on_rows), _pooled(off_rows)
        roznica = p_on["p"] - p_off["p"]
        half = float(np.sqrt(p_on["half"] ** 2 + p_off["half"] ** 2))
        stlumione = sum(int(r["trades"]["kill_switch_active"].sum()) for r in on_rows)
        print(
            f"  {arm} ({ARM_OPIS[arm]}), {n_szum} losowan czystego szumu:\n"
            f"      ON : n={p_on['n']:6d}  p={100 * p_on['p']:.2f}%  "
            f"CI=[{100 * p_on['low']:.2f}%; {100 * p_on['high']:.2f}%]  stlumionych={stlumione}\n"
            f"      OFF: n={p_off['n']:6d}  p={100 * p_off['p']:.2f}%  "
            f"CI=[{100 * p_off['low']:.2f}%; {100 * p_off['high']:.2f}%]\n"
            f"      ROZNICA (ON - OFF) = {100 * roznica:+.2f} pp, "
            f"95% CI +/-{100 * half:.2f} pp -> "
            f"{'NIEODROZNIALNA OD ZERA' if abs(roznica) <= half else 'ISTOTNA'}\n"
            f"      obie asercje obowiazkowe: ZDANE\n"
        )

    # --- 7. PODSUMOWANIE BRAMEK ---
    print(SEP)
    print("7. PODSUMOWANIE BRAMEK (reguly zapisane PRZED uruchomieniem)")
    print(SEP)
    print(f"  {'ramie':>5} | {'1 doslownie':>12} | {'1 wg celu':>10} | {'2. integralnosc':>16} | "
          f"{'3. pasmo pooled':>16}")
    print("  " + "-" * 78)
    for arm in ARMS:
        pool = _pooled([r for r in wyniki[arm] if r["q"] == 0.0])
        b = bramka1[arm]
        print(
            f"  {arm:>5} | {'ZDANA' if b['doslowna'] else 'ODRZUC.':>12} | "
            f"{'ZDANA' if b['wg_celu'] else 'ODRZUC.':>10} | "
            f"{100 * bramka2[arm]:15.2f}% | {100 * wald_half_width(pool['n']):15.2f}pp"
        )
    print(
        "\n  Rozstrzygniecie zerowe ('brak adopcji') jest dopuszczalne i zapisane z gory.\n"
        "  Bramka 1 jest jedyna, ktora moze zabic kandydata. Decyzje podpisuje czlowiek\n"
        "  w README rundy - skrypt drukuje liczby."
    )


if __name__ == "__main__":
    main()
