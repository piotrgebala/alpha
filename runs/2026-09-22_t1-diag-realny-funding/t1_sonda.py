"""
T1 — SONDA przed implementacja: czy realny funding zmienia cokolwiek wobec stalej?

Mierzy funding per transakcja na TRZY sposoby dla tej samej populacji transakcji:
  (0) MODEL OBECNY   - stala 0,0001 razy ulamkowa liczba okresow 8h
  (1) REALNE STAWKI, ulamkowo - srednia stawka z okna trzymania razy ulamek okresow
  (2) REALNE STAWKI, dyskretnie - SUMA rozliczen, ktore faktycznie wypadly w oknie
      (tak dziala gielda: funding pobiera sie w momentach 00/08/16 UTC, nie proporcjonalnie)

Populacja: konfiguracja C2/balanced z K3 (bez bramki rezimu, po adopcji A1) - najwieksza,
wiec najlepiej pokazuje efekt.
"""
import numpy as np
import pandas as pd
import yaml

from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.costs import FUNDING_PERIOD_HOURS, FUNDING_RATE_8H
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from data.fetch_funding import get_funding_rate_history_cached

CANDLE_MINUTES = 240

cfg = _load_cfg()
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
raw = _load(cfg, "4h")
funding = get_funding_rate_history_cached(
    symbol=cfg["primary_symbol"],
    start=(cfg.get("timeframe_start_overrides") or {}).get("4h", cfg["start"]),
    end=cfg["end"], cache_dir=cfg["cache_dir"], exchange_id=cfg["exchange_id"],
).sort_values("timestamp").reset_index(drop=True)

res = run_and_summarize(
    raw, seed=PRIMARY_SEED,
    regime_feature_sets=[(REGIME_ALL, REVERSION_FEATURES)],
    vertical_barrier_candles=3, candles_per_day=6, candle_minutes=CANDLE_MINUTES,
    train_days=60, test_days=28, step_days=28,
    trend_threshold=rule["trend_threshold"], range_threshold=rule["range_threshold"],
)
tr = res["backtest"]["trades"]
tr = tr.loc[~tr["kill_switch_active"]].copy()
tr["notional"] = tr["position_size"] * tr["entry_price"]
tr["wejscie"] = pd.to_datetime(tr["timestamp"], utc=True)
tr["wyjscie"] = tr["wejscie"] + pd.to_timedelta(tr["exit_bar_offset"] * CANDLE_MINUTES, unit="m")
tr["godziny"] = tr["exit_bar_offset"] * CANDLE_MINUTES / 60.0

ts = funding["timestamp"].to_numpy()
rate = funding["funding_rate"].to_numpy()

suma_dyskretna = np.empty(len(tr))
srednia_w_oknie = np.empty(len(tr))
liczba_rozliczen = np.empty(len(tr), dtype=int)
for i, (we, wy) in enumerate(zip(tr["wejscie"].to_numpy(), tr["wyjscie"].to_numpy())):
    maska = (ts > we) & (ts <= wy)
    w_oknie = rate[maska]
    liczba_rozliczen[i] = len(w_oknie)
    suma_dyskretna[i] = w_oknie.sum()
    srednia_w_oknie[i] = w_oknie.mean() if len(w_oknie) else FUNDING_RATE_8H

okresy = tr["godziny"].to_numpy() / FUNDING_PERIOD_HOURS
kierunek = tr["signal_direction"].to_numpy()

warianty = {
    "(0) stala, ulamkowo  [MODEL OBECNY]": kierunek * FUNDING_RATE_8H * okresy,
    "(1) realne, ulamkowo": kierunek * srednia_w_oknie * okresy,
    "(2) realne, dyskretnie [POPRAWNE]": kierunek * suma_dyskretna,
}

print("=" * 96)
print("T1 SONDA — funding jako UŁAMEK NOMINAŁU, trzy modele na tej samej populacji")
print("=" * 96)
print(f"  transakcji: {len(tr)}  |  srednie trzymanie: {tr['godziny'].mean():.1f}h "
      f"({tr['exit_bar_offset'].mean():.2f} swiecy)")
print(f"  rozliczen funding w oknie: srednio {liczba_rozliczen.mean():.2f}, "
      f"rozklad {dict(pd.Series(liczba_rozliczen).value_counts().sort_index())}")
print(f"  udzial long: {100 * (kierunek > 0).mean():.2f}%  short: {100 * (kierunek < 0).mean():.2f}%")
print(f"  stala w modelu: {FUNDING_RATE_8H}  |  realna srednia stawka: {rate.mean():.8f} "
      f"| mediana: {np.median(rate):.8f}\n")
print(f"  {'wariant':>36} | {'srednia':>12} | {'mediana':>12} | {'|srednia|':>12}")
print("  " + "-" * 80)
for nazwa, wart in warianty.items():
    print(f"  {nazwa:>36} | {100 * wart.mean():11.5f}% | {100 * np.median(wart):11.5f}% | "
          f"{100 * np.abs(wart).mean():11.5f}%")

print("\n" + "=" * 96)
print("WPLYW NA CALKOWITY KOSZT I PROG OPLACALNOSCI")
print("=" * 96)
koszt_bez_funding = (tr["cost"].to_numpy() / tr["notional"].to_numpy()) - warianty["(0) stala, ulamkowo  [MODEL OBECNY]"]
bariera = ((tr["exit_price"] - tr["entry_price"]).abs() / tr["entry_price"]).mean()
print(f"  bariera srednia B = {100 * bariera:.4f}% nominalu\n")
print(f"  {'wariant':>36} | {'koszt C':>10} | {'break-even':>11} | {'delta BE':>10}")
print("  " + "-" * 76)
be0 = None
for nazwa, wart in warianty.items():
    c = float((koszt_bez_funding + wart).mean())
    be = 0.5 * (1 + c / bariera)
    if be0 is None:
        be0 = be
    print(f"  {nazwa:>36} | {100 * c:9.5f}% | {100 * be:10.3f}% | {100 * (be - be0):+9.3f} pp")

print("\n" + "=" * 96)
print("KONTROLA PREMISY T1 zapisanej w STATUS.md")
print("=" * 96)
print("  STATUS.md twierdzi: 'Zmierzony sredni funding to -0,00243% (przychod!), a model")
print("  zaklada +0,01% kosztu'.")
print(f"\n  -0,00243% to SIGNOWANY koszt per transakcja, policzony JUZ ZE STALA 0,0001")
print(f"  i z mieszanka kierunkow. Tutaj ten sam rachunek daje "
      f"{100 * warianty['(0) stala, ulamkowo  [MODEL OBECNY]'].mean():.5f}%.")
print(f"  +0,01% to STAWKA za okres 8h, nie koszt per transakcja.")
print(f"  To sa DWIE ROZNE WIELKOSCI — porownywanie ich jest bledem kategorii.")
print(f"\n  Wlasciwe porownanie stawek: model {FUNDING_RATE_8H:.6f} vs realna srednia "
      f"{rate.mean():.6f} (+{100 * (rate.mean() / FUNDING_RATE_8H - 1):.1f}%), mediana {np.median(rate):.6f}.")
