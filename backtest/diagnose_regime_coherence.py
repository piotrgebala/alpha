"""
diagnose_regime_coherence.py

Zadanie Z16 (Backlog II) — czy bramka reżimu i target triple-barrier mierzą TEN SAM
horyzont? Skrypt read-only/analityczny, poza pytest (jak `run_checkpoint_v2.py` /
`diagnose_cost_feasibility.py`), zbudowany na `backtest/checkpoint_lib.py` (Z13).
Logika jest w czystym, przetestowanym `agents/regime_coherence.py` — tu tylko
uruchomienie na realnych danych i raport.

KONTEKST: program "droga do GO" (C2.11-C2.13) pokazał, że człon `p` nierówności
(2p-1)*B > C jest nieruchomy: dwie niezależne, pre-rejestrowane próby jego podniesienia
dały wynik negatywny (C2.13 wręcz odwrotny do przewidywanego). Audyt po regule STOP
postawił hipotezę WYJAŚNIAJĄCĄ: `p` był mierzony na sygnale o wewnętrznie niespójnej
specyfikacji, bo bramka kwalifikuje świecę do reżimu trwającego kilka świec, a etykieta
ocenia ruch przez VERTICAL_BARRIER_CANDLES=12 świec (60 min).

Ten skrypt tę hipotezę MIERZY, a nie zakłada. Trzy bloki, wszystkie read-only:
  1. Tabela spójności obecnej reguły (progi z config/settings.yaml) dla horyzontów
     12/48/144/576 świec — długości epizodów vs okno etykiety.
  2. Konsekwencja dla członu B: jaka szerokość bariery jest wymagana przy zmierzonej
     trafności i koszcie, jaki horyzont to implikuje (skalowanie ~sqrt(t)) i czy
     jakikolwiek epizod reżimu jest dość długi. To formalnie domyka Backlog Z8
     BEZ wydawania budżetu multiple-testing.
  3. Przesiew KANDYDATÓW na regułę reżimu pod kryterium dopuszczalności
     (`is_rule_admissible`): mediana epizodu >= horyzont ORAZ udział reżimu >= 5%.
     Czysto opisowy — kryterium jest definicyjne, nie strojone po PnL, i nie dotyka
     modelu, więc kosztuje 0 wariantów (CLAUDE.md zasada 1).

Użycie:
    py -m backtest.diagnose_regime_coherence
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from agents.feature_miner import (
    compute_atr_14,
    compute_atr_pctrank_20d,
    compute_direction_persistence_10,
)
from agents.labeling import ATR_MULTIPLIER, VERTICAL_BARRIER_CANDLES
from agents.regime_coherence import (
    DEFAULT_HORIZONS_CANDLES,
    assert_contiguous_timestamps,
    coherence_table,
    is_rule_admissible,
    regime_episodes,
)
from backtest.checkpoint_lib import fetch_data, load_config
from backtest.costs import EXECUTION_MAKER_LIMIT, gate_cost_fraction
from backtest.diagnose_cost_feasibility import _regime_series

# Zmierzone w C2.12 (model wykonania maker_limit) — trafność kierunku per reżim.
# Wpisane jawnie jako DANE WEJŚCIOWE do arytmetyki bloku 2, nie liczone tu od nowa
# (liczy je backtest/metrics.py::summarize_edge_by_regime w kanonicznym checkpointcie).
MEASURED_HIT_RATE = {"range": 0.510692, "trend": 0.498592}

# Kandydaci na regułę reżimu do przesiewu (blok 3). Dobrani, żeby rozpiąć MECHANIZM
# (próg persistence vs próg ATR vs wygładzanie), nie żeby przeszukać przestrzeń po wyniku
# — żaden z nich nie jest tu oceniany PnL-em ani promowany do modelu.
CANDIDATE_RULES = [
    ("obecna (0.7/0.3)", 0.7, 0.3, 1),
    ("luźniejsza (0.5/0.5)", 0.5, 0.5, 1),
    ("luźniejsza (0.4/0.4)", 0.4, 0.4, 1),
    ("obecna + wygładzenie 12", 0.7, 0.3, 12),
    ("0.5/0.5 + wygładzenie 12", 0.5, 0.5, 12),
    ("0.5/0.5 + wygładzenie 48", 0.5, 0.5, 48),
]


def _smooth_regime(regime: pd.Series, window: int) -> pd.Series:
    """
    Wygładzanie reżimu modą w oknie kroczącym (tylko PRZESZŁOŚĆ — okno kończy się na
    bieżącej świecy, więc zero leakage'u). Sprawdza mechanizm: czy krótkie epizody to
    realna zmiana reżimu, czy migotanie wokół progu.

    window=1 zwraca serię bez zmian (brak wygładzania).
    """
    if window <= 1:
        return regime
    codes, uniques = pd.factorize(regime)
    coded = pd.Series(codes, index=regime.index)
    smoothed = (
        coded.rolling(window=window, min_periods=1)
        .apply(lambda w: np.bincount(w.astype(int)).argmax(), raw=False)
        .astype(int)
    )
    return pd.Series(uniques[smoothed.to_numpy()], index=regime.index, name="regime")


def _print_block_1(regime: pd.Series) -> pd.DataFrame:
    print("=" * 96)
    print("BLOK 1 — spójność OBECNEJ reguły reżimu z horyzontem etykiety")
    print("=" * 96)
    print(
        f"VERTICAL_BARRIER_CANDLES = {VERTICAL_BARRIER_CANDLES} świec "
        f"= {VERTICAL_BARRIER_CANDLES * 5} min (horyzont, na którym liczona jest etykieta)\n"
    )

    episodes = regime_episodes(regime)
    print("-- długości nieprzerwanych epizodów reżimu (świece 5m) --")
    for name in ("trend", "range", "ambiguous"):
        lengths = episodes.loc[episodes["regime"] == name, "length"]
        if not len(lengths):
            print(f"{name:10s} — reżim nie wystąpił")
            continue
        print(
            f"{name:10s} epizodów={len(lengths):6d}  mediana={lengths.median():6.1f}  "
            f"p90={lengths.quantile(0.9):6.1f}  max={lengths.max():5d} "
            f"({lengths.max() * 5:6d} min)  świec={lengths.sum():7d}"
        )

    table = coherence_table(regime, horizons=DEFAULT_HORIZONS_CANDLES)
    print("\n-- tabela spójności: ile świec ma CAŁE okno etykiety wewnątrz epizodu --")
    cols = [
        "regime",
        "horizon_candles",
        "horizon_minutes",
        "median_length",
        "n_episodes_ge_horizon",
        "n_episodes",
        "n_windows_inside",
        "share_windows_inside",
        "coherent",
    ]
    print(table[cols].to_string(index=False))
    print(
        "\n[interpretacja] coherent = mediana długości epizodu >= horyzont etykiety.\n"
        "share_windows_inside = ułamek świec reżimu, dla których etykieta opisuje ruch\n"
        "WYŁĄCZNIE wewnątrz reżimu, który zakwalifikował wejście. Niskie wartości znaczą,\n"
        "że bramka i target mierzą różne rzeczy — i że `p` nie jest interpretowalne."
    )
    return table


def _print_block_2(regime: pd.Series, df: pd.DataFrame) -> None:
    print("\n" + "=" * 96)
    print("BLOK 2 — konsekwencja dla członu B (domknięcie Backlog Z8 bez wydawania wariantu)")
    print("=" * 96)

    # Koszt zgodnie z modelem wykonania z C2.12: bramka nie zna powodu wyjścia, więc
    # bierze najdroższy osiągalny. Do H3 stała tu ręczna kopia pary nóg
    # (`entry_leg=MAKER, exit_leg=TAKER`); dziś to `gate_cost_fraction` — ta sama funkcja,
    # z której korzysta silnik. Wartość bez zmian (0,0009), więc liczby tego bloku są
    # odtwarzalne co do cyfry; zmienia się tylko to, że dołożenie czwartego powodu wyjścia
    # przesunie ten skrypt razem z bramką, zamiast go po cichu zostawić.
    cost = gate_cost_fraction(EXECUTION_MAKER_LIMIT)
    atr = compute_atr_14(df)
    atr_over_price = (atr / df["close"]).reindex(regime.index)
    episodes = regime_episodes(regime)

    print(f"koszt round-trip C = {100 * cost:.4f}% nominału (model maker_limit, C2.12)\n")
    print(
        f"{'reżim':8s} {'p':>9s} {'2p-1':>9s} {'B_obecne':>10s} {'B_wymagane':>11s} "
        f"{'krotność':>9s} {'implik. horyzont':>17s} {'max epizod':>11s}"
    )
    for name in ("range", "trend"):
        p = MEASURED_HIT_RATE[name]
        edge = 2.0 * p - 1.0
        mask = regime == name
        atr_med = float(atr_over_price[mask].median()) if mask.any() else float("nan")
        b_now = ATR_MULTIPLIER * atr_med
        lengths = episodes.loc[episodes["regime"] == name, "length"]
        max_ep = int(lengths.max()) if len(lengths) else 0

        if edge <= 0:
            print(
                f"{name:8s} {p:9.4f} {edge:+9.4f} {100 * b_now:9.4f}% {'—':>11s} "
                f"{'—':>9s} {'ŻADEN nie pomaga':>17s} {max_ep:>8d} św."
            )
            continue

        b_req = cost / edge
        mult = b_req / b_now
        # Ruch ceny skaluje się ~sqrt(czas), więc horyzont ~ (krotność)^2 * obecny horyzont.
        horizon_req = (mult**2) * VERTICAL_BARRIER_CANDLES
        print(
            f"{name:8s} {p:9.4f} {edge:+9.4f} {100 * b_now:9.4f}% {100 * b_req:10.4f}% "
            f"{mult:8.1f}x {horizon_req:11.0f} św. {max_ep:>8d} św."
        )

    print(
        "\n[interpretacja] B_wymagane = C/(2p-1) — szerokość bariery, przy której wartość\n"
        "oczekiwana transakcji przestaje być ujemna PRZY NIEZMIENIONEJ trafności. Implikowany\n"
        "horyzont z przeskalowania ~sqrt(t). Jeśli przekracza NAJDŁUŻSZY zmierzony epizod\n"
        "reżimu, to poszerzanie bariery jest niewykonalne przy tej definicji reżimu —\n"
        "bariera i tak byłaby testowana poza reżimem, który uzasadnił wejście.\n"
        "Gdy 2p-1 <= 0 (trend), ŻADNA szerokość nie pomaga: szersza bariera pogarsza wynik."
    )


def _print_block_3(atr_rank: pd.Series, persistence: pd.Series, valid: pd.Series) -> pd.DataFrame:
    print("\n" + "=" * 96)
    print("BLOK 3 — przesiew kandydatów na regułę reżimu (kryterium dopuszczalności, 0 wariantów)")
    print("=" * 96)
    print(
        f"Kryterium: mediana epizodu >= {VERTICAL_BARRIER_CANDLES} świec (horyzont etykiety)\n"
        "ORAZ udział reżimu >= 5% świec. Oba warunki definicyjne, żaden nie oceniany PnL-em.\n"
    )

    rows: list[dict] = []
    print(f"{'reguła':28s} {'trend: med/udz':>18s} {'range: med/udz':>18s} {'dopuszczalna':>13s}")
    for label, trend_th, range_th, smooth in CANDIDATE_RULES:
        regime = _regime_series(atr_rank, persistence, trend_th, range_th)[valid]
        regime = _smooth_regime(regime.reset_index(drop=True), smooth)
        verdict = is_rule_admissible(regime, horizon=VERTICAL_BARRIER_CANDLES)
        t, r = verdict["per_regime"]["trend"], verdict["per_regime"]["range"]
        print(
            f"{label:28s} {t['median_length']:8.1f} / {100 * t['share']:5.2f}% "
            f"{r['median_length']:8.1f} / {100 * r['share']:5.2f}% "
            f"{('TAK' if verdict['admissible'] else 'nie'):>13s}"
        )
        rows.append(
            {
                "rule": label,
                "trend_median": t["median_length"],
                "trend_share": t["share"],
                "range_median": r["median_length"],
                "range_share": r["share"],
                "admissible": verdict["admissible"],
            }
        )

    print(
        "\n[interpretacja] Reguła niedopuszczalna NIE jest 'zła' — jest niespójna z targetem\n"
        "o tym horyzoncie. Dopuszczalność to warunek KONIECZNY, by pomiar `p` cokolwiek\n"
        "znaczył; nie jest warunkiem wystarczającym istnienia edge'u. Wybór reguły do testu\n"
        "OOS to osobna runda i osobny wariant w księdze (Backlog Z7) — ten blok go NIE wybiera."
    )
    return pd.DataFrame(rows)


def main() -> None:
    cfg = load_config()
    df = fetch_data(cfg)
    assert_contiguous_timestamps(df["timestamp"])
    print(f"[data] seria ciągła, {len(df)} świec\n")

    atr_rank = compute_atr_pctrank_20d(df)
    persistence = compute_direction_persistence_10(df)
    valid = compute_atr_14(df).notna() & atr_rank.notna() & persistence.notna()

    rule = cfg["regime_rule"]
    regime_full = _regime_series(
        atr_rank, persistence, rule["trend_threshold"], rule["range_threshold"]
    )
    # `valid` odcina wyłącznie PREFIKS warmupu wskaźników, więc seria pozostaje ciągła
    # (gdyby odfiltrowywał wiersze ze środka, epizody zlepiłyby się — patrz docstring
    # agents/regime_coherence.py).
    assert_contiguous_timestamps(df.loc[valid, "timestamp"])
    regime = regime_full[valid].reset_index(drop=True)
    print(f"[regime] świec z policzalnymi cechami: {len(regime)}\n")

    _print_block_1(regime)
    _print_block_2(regime, df.loc[valid].reset_index(drop=True))
    _print_block_3(atr_rank, persistence, valid)


if __name__ == "__main__":
    main()
