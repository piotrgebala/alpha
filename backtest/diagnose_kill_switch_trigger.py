"""
diagnose_kill_switch_trigger.py

Commit 2c — diagnoza PRZYCZYNY serii strat, która uruchamia kill-switch w fold_idx=0
`range` (IMPLEMENTATION_PLAN.md §5 Commit 2b, otwarte pytanie z C2b.1b). Skrypt
read-only/analityczny, poza pytest (jak `run_checkpoint.py`/`diagnose_range_signal.py`) —
inspekcja SZCZEGÓŁÓW pierwszych realnych transakcji (kill_switch_active=False) przed
momentem, gdy equity zamraża się na stałe.

Pytanie: czy seria strat to (a) błędny kierunek predykcji (gross_pnl < 0 — model się
mylił), (b) koszty transakcyjne zjadające dodatni gross_pnl (net_pnl < 0 <= gross_pnl),
czy (c) nadmierny sizing wzmacniający zwykłe straty ponad oczekiwania. Rozróżnienie ma
znaczenie dla wyboru mechanizmu naprawy kill-switcha (Commit 2c) — inny fix, jeśli to
problem kosztów, inny jeśli to jakość modelu na starcie datasetu.

Użycie:
    py -m backtest.diagnose_kill_switch_trigger
"""

from __future__ import annotations

import pandas as pd
import yaml

from backtest.costs import funding_cost, round_trip_fee_cost, slippage_cost
from backtest.engine import run_backtest
from data.fetch_ohlcv import get_ohlcv_cached


def _load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fetch_data(cfg: dict) -> pd.DataFrame:
    data_cfg = cfg["data"]
    df = get_ohlcv_cached(
        symbol=data_cfg["primary_symbol"],
        timeframe=data_cfg["timeframe"],
        start=data_cfg["start"],
        end=data_cfg["end"],
        cache_dir=data_cfg["cache_dir"],
        exchange_id=data_cfg["exchange_id"],
    )
    return df


def _annotate_trade_costs(trades: pd.DataFrame) -> pd.DataFrame:
    """Rozbija skalarny `cost` (total_round_trip_cost) z powrotem na trzy składniki
    (fee/funding/slippage), przeliczając je z pól już obecnych w trade journal —
    bez modyfikacji backtest.engine/costs (czysta post-hoc diagnostyka)."""
    real = trades.loc[~trades["kill_switch_active"]].copy()
    notional = real["position_size"] * real["entry_price"]
    real["notional"] = notional
    real["fee"] = notional.apply(round_trip_fee_cost)
    real["funding"] = [
        funding_cost(n, hc, int(d))
        for n, hc, d in zip(notional, real["exit_bar_offset"], real["signal_direction"])
    ]
    real["slippage"] = 2.0 * notional.apply(slippage_cost)
    real["gross_pnl_negative"] = real["gross_pnl"] < 0
    real["cost_ate_gain"] = (real["gross_pnl"] >= 0) & (real["net_pnl"] < 0)
    return real


def diagnose(df: pd.DataFrame, seed: int = 42) -> None:
    result = run_backtest(df, seed=seed)
    trades = result["trades"]
    real = _annotate_trade_costs(trades)

    print(f"=== Wszystkie realne transakcje (kill_switch_active=False): {len(real)} ===")
    cols = [
        "timestamp",
        "regime",
        "fold_idx",
        "signal_direction",
        "signal_confidence",
        "entry_price",
        "exit_price",
        "position_size",
        "exit_bar_offset",
        "gross_pnl",
        "fee",
        "funding",
        "slippage",
        "cost",
        "net_pnl",
        "equity_before",
        "equity_after",
    ]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(real[cols].to_string(index=False))

    print("\n=== Rozkład przyczyn straty ===")
    n_total = len(real)
    n_gross_negative = int(real["gross_pnl_negative"].sum())
    n_cost_ate_gain = int(real["cost_ate_gain"].sum())
    n_net_negative = int((real["net_pnl"] < 0).sum())
    print(f"n_total={n_total}")
    print(f"n_net_pnl<0 (strata netto)={n_net_negative}")
    print(f"  z czego gross_pnl<0 (zly kierunek predykcji)={n_gross_negative}")
    print(f"  z czego gross_pnl>=0 ale koszty zjadly zysk (cost_ate_gain)={n_cost_ate_gain}")

    print("\n=== Statystyki opisowe (realne transakcje) ===")
    print(real[["signal_confidence", "position_size", "gross_pnl", "cost", "net_pnl"]].describe())

    print("\n=== Koszt jako % notional (mean) ===")
    print(f"fee/notional={float((real['fee'] / real['notional']).mean()):.6f}")
    print(f"funding/notional={float((real['funding'] / real['notional']).mean()):.6f}")
    print(f"slippage/notional={float((real['slippage'] / real['notional']).mean()):.6f}")
    print(f"cost/notional={float((real['cost'] / real['notional']).mean()):.6f}")

    print("\n=== Rozklad kierunku sygnalu (direction) ===")
    print(real["signal_direction"].value_counts())

    print("\n=== Equity toru w okolicy pierwszych transakcji ===")
    print(real[["timestamp", "equity_before", "equity_after"]].head(15).to_string(index=False))


def main() -> None:
    cfg = _load_config()
    df = _fetch_data(cfg)
    diagnose(df)


if __name__ == "__main__":
    main()
