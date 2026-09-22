"""
diagnose_cost_feasibility.py

Commit 2d — diagnoza, czy hipoteza regime-gated jest w ogóle WYKONALNA KOSZTOWO przy
obecnej definicji reżimu i szerokości bariery triple-barrier. Skrypt read-only/
analityczny, poza pytest (jak `run_checkpoint.py` / `diagnose_range_signal.py` /
`diagnose_kill_switch_trigger.py`).

Kontekst: Commit 2c zamknął deadlock kill-switcha i potwierdził NO-GO na 23/40 foldach
(mean_sharpe=-47,38), ale przyczyna ujemnego wyniku pozostała otwarta. C2c.1 pokazał
serię strat long podczas spadku sklasyfikowanego jako `range` i zostawił dwie hipotezy:
(a) reguła reżimu źle etykietuje trwałe trendy (kandydat: C2.5, rekalibracja progów),
(b) model `range` nie ma edge'u. Ten skrypt sprawdza TRZECIĄ, wcześniej nie postawioną
możliwość: że przy obecnej definicji `range` (niski percentyl ATR) bariera zysku jest
WĘŻSZA NIŻ KOSZT round-trip, więc żadna jakość sygnału nie wystarczy — wynik jest
arytmetyczny, nie statystyczny.

Trzy bloki, wszystkie read-only (zero zmian w pipeline):
  1. Rozkład reguły reżimu na realnych danych — pokazuje, że
     `direction_persistence_10` jest DYSKRETNA (|sum(sign)|/10 ∈ {0, 0.1, ..., 1.0}),
     więc próg 0.7 wpada w lukę rozkładu; to on, nie `atr_pctrank_20d`, czyni reżim
     `trend` prawie pustym (C2.5, §7 STATUS.md).
  2. Wykonalność kosztowa: szerokość bariery (ATR_MULTIPLIER × atr_14) jako % ceny vs
     koszt round-trip, per reżim + wymagana trafność kierunku na break-even:
         p_break_even = 0.5 * (1 + koszt / bariera)
     (przy symetrycznych barierach ±B: p*B - (1-p)*B = koszt).
  3. Dekompozycja REALNYCH transakcji z `run_backtest` (kill_switch_active=False) na
     gross vs koszt — ile straty pochodzi ze złego kierunku, a ile z kosztu zjadającego
     poprawny kierunek.

Użycie:
    py -m backtest.diagnose_cost_feasibility
"""

from __future__ import annotations

import pandas as pd
import yaml

from agents.feature_miner import (
    compute_atr_14,
    compute_atr_pctrank_20d,
    compute_direction_persistence_10,
)
from agents.labeling import ATR_MULTIPLIER
from backtest.costs import SLIPPAGE_BPS, TAKER_FEE_RATE
from backtest.engine import run_backtest
from data.fetch_ohlcv import get_ohlcv_cached

# Koszt round-trip jako ułamek nominału, BEZ funding (zależny od kierunku i czasu
# trzymania, empirycznie ~0,0004% — pomijalny wobec fee+slippage, patrz C2c.1).
# Liczony z tych samych stałych co backtest.costs, nie hardkodowany.
COST_FLOOR_FRACTION = 2.0 * TAKER_FEE_RATE + 2.0 * (SLIPPAGE_BPS / 10_000.0)

# Siatka progów do bloku 1 — pary (trend_threshold, range_threshold) do porównania z
# obecnymi 0.7/0.3 z config/settings.yaml. Czysto opisowa (ile % świec trafia do
# którego reżimu), ŻADNEGO przeszukiwania po wyniku PnL — CLAUDE.md zasada 1.
THRESHOLD_GRID = [
    (0.7, 0.3),
    (0.6, 0.4),
    (0.6, 0.3),
    (0.5, 0.5),
    (0.5, 0.3),
    (0.45, 0.45),
    (0.4, 0.4),
    (0.4, 0.3),
    (0.3, 0.3),
    (0.3, 0.2),
]


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fetch_data(cfg: dict) -> pd.DataFrame:
    data_cfg = cfg["data"]
    return get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=data_cfg["timeframe"],
        start=data_cfg["start"],
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )


def _regime_series(
    atr_rank: pd.Series,
    persistence: pd.Series,
    trend_threshold: float,
    range_threshold: float,
) -> pd.Series:
    """Ta sama reguła co agents.feature_miner.classify_regime, ale na już policzonych
    seriach (blok 1 porównuje wiele par progów — liczenie cech raz, nie 10x)."""
    regime = pd.Series("ambiguous", index=atr_rank.index, name="regime")
    regime.loc[(atr_rank > trend_threshold) & (persistence > trend_threshold)] = "trend"
    regime.loc[(atr_rank < range_threshold) & (persistence < range_threshold)] = "range"
    return regime


def diagnose_regime_rule(atr_rank: pd.Series, persistence: pd.Series, valid: pd.Series) -> None:
    print("=" * 78)
    print("BLOK 1 — rozkład reguły reżimu na realnych danych")
    print("=" * 78)
    print(f"wiersze z policzalnymi cechami: {int(valid.sum())} / {len(valid)}")

    print("\n-- rozkład atr_pctrank_20d --")
    print(atr_rank[valid].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_string())

    print("\n-- rozkład direction_persistence_10 --")
    print(persistence[valid].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_string())

    print("\n-- direction_persistence_10 jest DYSKRETNA (|sum(sign)|/10) --")
    print(persistence[valid].round(2).value_counts().sort_index().to_string())

    print("\n-- udział reżimów przy różnych progach (opisowo, bez tuningu po PnL) --")
    n = int(valid.sum())
    print(f"{'trend_th':>9} {'range_th':>9} {'trend%':>9} {'range%':>9} {'ambig%':>9}")
    for trend_threshold, range_threshold in THRESHOLD_GRID:
        regime = _regime_series(atr_rank, persistence, trend_threshold, range_threshold)[valid]
        n_trend = int((regime == "trend").sum())
        n_range = int((regime == "range").sum())
        n_ambig = n - n_trend - n_range
        print(
            f"{trend_threshold:>9} {range_threshold:>9} "
            f"{100 * n_trend / n:>9.2f} {100 * n_range / n:>9.2f} {100 * n_ambig / n:>9.2f}"
        )


def diagnose_cost_feasibility(
    df: pd.DataFrame, atr: pd.Series, regime: pd.Series, valid: pd.Series
) -> None:
    print("\n" + "=" * 78)
    print("BLOK 2 — wykonalność kosztowa: szerokość bariery vs koszt round-trip")
    print("=" * 78)

    cost_pct = 100.0 * COST_FLOOR_FRACTION
    barrier_pct = 100.0 * ATR_MULTIPLIER * atr / df["close"]
    grouped = barrier_pct[valid].groupby(regime[valid])

    print(f"koszt round-trip (fee 2x + slippage 2x, bez funding) = {cost_pct:.3f}% nominału")
    print(f"\n-- bariera triple-barrier ({ATR_MULTIPLIER}xATR) jako % ceny, wg reżimu --")
    print(
        pd.DataFrame(
            {
                "n": grouped.size(),
                "mean%": grouped.mean(),
                "p25": grouped.quantile(0.25),
                "mediana": grouped.median(),
                "p75": grouped.quantile(0.75),
            }
        ).to_string()
    )

    print("\n-- odsetek świec, gdzie PEŁNE trafienie bariery NIE pokrywa kosztu --")
    print((barrier_pct[valid] < cost_pct).groupby(regime[valid]).mean().to_string())

    print("\n-- wymagana trafność kierunku na break-even: p = 0.5*(1 + koszt/bariera) --")
    print("   (bariery symetryczne ±B, bez uwzględnienia wyjść przez vertical barrier)")
    for regime_name in ["trend", "range", "ambiguous"]:
        mask = valid & (regime == regime_name)
        if not mask.any():
            print(f"   {regime_name:>10}: brak świec")
            continue
        barrier_median = float(barrier_pct[mask].median())
        p_break_even = 0.5 * (1.0 + cost_pct / barrier_median)
        verdict = "NIEOSIĄGALNE (>100%)" if p_break_even > 1.0 else ""
        print(
            f"   {regime_name:>10}: mediana bariery={barrier_median:.3f}% "
            f"-> wymagana trafność={100 * p_break_even:.1f}% {verdict}"
        )


def diagnose_realized_trades(df: pd.DataFrame, seed: int = 42) -> None:
    print("\n" + "=" * 78)
    print(f"BLOK 3 — dekompozycja realnych transakcji z run_backtest (seed={seed})")
    print("=" * 78)

    result = run_backtest(df, seed=seed)
    trades = result["trades"]
    real = trades.loc[~trades["kill_switch_active"]].copy()
    real["notional"] = real["position_size"] * real["entry_price"]
    real["cost_pct"] = 100.0 * real["cost"] / real["notional"]
    real["gross_pct"] = 100.0 * real["gross_pnl"] / real["notional"]
    real["abs_move_pct"] = (
        100.0 * (real["exit_price"] - real["entry_price"]).abs() / real["entry_price"]
    )

    for regime_name, group in real.groupby("regime"):
        right_direction = group.loc[group["gross_pnl"] > 0]
        print(f"\n-- {regime_name}: n={len(group)} --")
        print(f"   dobry kierunek (gross_pnl>0):        {100 * (group['gross_pnl'] > 0).mean():.1f}%")
        print(f"   mediana |ruchu| do wyjścia:          {group['abs_move_pct'].median():.3f}% ceny")
        print(f"   mediana kosztu:                      {group['cost_pct'].median():.3f}% nominału")
        print(
            f"   mediana gross={group['gross_pct'].median():.3f}%  "
            f"net={(group['gross_pct'] - group['cost_pct']).median():.3f}%"
        )
        if len(right_direction) > 0:
            eaten = float((right_direction["gross_pnl"] <= right_direction["cost"]).mean())
            print(f"   z dobrym kierunkiem, a i tak netto <=0: {100 * eaten:.1f}% (koszt zjadł zysk)")
        print(
            f"   suma: gross={group['gross_pnl'].sum():.0f}  "
            f"koszt={group['cost'].sum():.0f}  net={group['net_pnl'].sum():.0f}"
        )


def diagnose(df: pd.DataFrame, seed: int = 42) -> None:
    atr = compute_atr_14(df)
    atr_rank = compute_atr_pctrank_20d(df)
    persistence = compute_direction_persistence_10(df)
    valid = atr.notna() & atr_rank.notna() & persistence.notna()

    cfg_regime = _load_config()["regime_rule"]
    regime = _regime_series(
        atr_rank, persistence, cfg_regime["trend_threshold"], cfg_regime["range_threshold"]
    )

    diagnose_regime_rule(atr_rank, persistence, valid)
    diagnose_cost_feasibility(df, atr, regime, valid)
    diagnose_realized_trades(df, seed=seed)


def main() -> None:
    cfg = _load_config()
    df = _fetch_data(cfg)
    print(f"[data] {len(df)} świec: {df['timestamp'].min()} -> {df['timestamp'].max()}\n")
    diagnose(df)


if __name__ == "__main__":
    main()
