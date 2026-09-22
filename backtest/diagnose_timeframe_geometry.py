"""
diagnose_timeframe_geometry.py

Backlog Z9 + geometria B/C na grubszych interwałach. Skrypt read-only/analityczny, poza
pytest (jak `diagnose_regime_coherence.py`), na trwałym cache w `data/raw/`.

Trzy pytania, wszystkie mierzone na NATYWNYCH świecach z giełdy:

  1. (Z9, pytanie oryginalne) Czy agregacja 5m -> 1h/4h zniekształca dane? C2.6 testował
     hipotezę na świecach RESAMPLOWANYCH z 5m, bo sandbox nie miał dostępu do Binance.
     Teraz mamy natywne — porównujemy jedno z drugim.

  2. Czy grubszy interwał naprawia SPÓJNOŚĆ bramki z horyzontem (Z16)? Na 5m mediana
     epizodu `range` to 5 świec przy horyzoncie 12 — niespójne. Na grubszych świecach
     epizody liczone są w innych jednostkach, więc relacja może się zmienić.

  3. Czy grubszy interwał zmienia relację B/C na tyle, by próg opłacalności spadł
     w zasięg realistycznej trafności? To jedyny nietknięty mechanizm: koszt round-trip
     jest STAŁY per transakcja, a ATR rośnie z interwałem (~sqrt(czas)), więc iloraz
     B/C poprawia się bez zakładania czegokolwiek o modelu.

Kluczowe zastrzeżenie: blok 3 liczy próg opłacalności `break_even_p = 0.5*(1 + C/B)` —
to pokazuje, JAK NISKO trzeba zejść z wymaganiem wobec trafności. NIE jest to obietnica,
że model taką trafność osiągnie; `p` na grubszych świecach trzeba zmierzyć osobno
(C2.6 mierzył je na resamplowanych danych i z nieproporcjonalnym horyzontem — confound Z8).

Użycie:
    py -m backtest.diagnose_timeframe_geometry
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from agents.feature_miner import (
    compute_atr_14,
    compute_atr_pctrank_20d,
    compute_direction_persistence_10,
)
from agents.labeling import ATR_MULTIPLIER, VERTICAL_BARRIER_CANDLES
from agents.regime_coherence import coherence_table, regime_episodes
from backtest.costs import EXECUTION_MAKER_LIMIT, gate_cost_fraction
from backtest.diagnose_cost_feasibility import _regime_series
from data.fetch_ohlcv import TIMEFRAME_MINUTES, get_ohlcv_cached, resample_ohlcv

# Świec na dobę per interwał — wejście do `compute_atr_pctrank_20d` (okno 20 dni).
CANDLES_PER_DAY = {"5m": 288, "1h": 24, "4h": 6}

# Horyzonty etykiety do sprawdzenia, w świecach danego interwału. 12 to obecna wartość
# `VERTICAL_BARRIER_CANDLES`; 3 i 48 pokazują, jak kryterium spójności reaguje na zmianę.
HORIZONS = (3, 12, 48)


def _load_cfg() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["data"]


def _load(cfg: dict, timeframe: str) -> pd.DataFrame:
    """
    Z trwałego cache — bez sieci, jeśli plik już jest (patrz data/fetch_ohlcv.py).

    Respektuje `timeframe_start_overrides` (Z5b): 4h ma dłuższą historię niż 5m/1h, bo
    tam wiążącym ograniczeniem eksperymentu jest liczebność próby (Z19).
    """
    start = (cfg.get("timeframe_start_overrides") or {}).get(timeframe, cfg["start"])
    return get_ohlcv_cached(
        symbol=cfg["primary_symbol"],
        timeframe=timeframe,
        start=start,
        end=cfg["end"],
        cache_dir=cfg["cache_dir"],
        exchange_id=cfg["exchange_id"],
    )


def block_1_native_vs_resampled(native: dict[str, pd.DataFrame]) -> None:
    print("=" * 96)
    print("BLOK 1 (Z9) — natywne świece vs agregacja z 5m: czy resample zniekształca?")
    print("=" * 96)
    base = native["5m"]
    for timeframe in ("1h", "4h"):
        resampled = resample_ohlcv(base, timeframe)
        nat = native[timeframe]
        merged = nat.merge(resampled, on="timestamp", suffixes=("_nat", "_res"), how="inner")
        print(f"\n-- {timeframe} -- natywnych={len(nat)}, z resample={len(resampled)}, wspólnych={len(merged)}")
        if merged.empty:
            print("   brak wspólnych świec — nie da się porównać")
            continue
        for col in ("open", "high", "low", "close", "volume"):
            a, b = merged[f"{col}_nat"], merged[f"{col}_res"]
            denom = a.abs().replace(0.0, np.nan)
            rel = ((a - b).abs() / denom).replace([np.inf, -np.inf], np.nan)
            n_exact = int((a == b).sum())
            print(
                f"   {col:7s} identycznych={100 * n_exact / len(merged):6.2f}%  "
                f"maks |błąd wzgl.|={100 * rel.max():.6f}%  mediana={100 * rel.median():.8f}%"
            )


def block_2_coherence(native: dict[str, pd.DataFrame], cfg_rule: dict) -> None:
    print("\n" + "=" * 96)
    print("BLOK 2 — czy grubszy interwał naprawia spójność bramki z horyzontem?")
    print("=" * 96)
    for timeframe in ("5m", "1h", "4h"):
        df = native[timeframe]
        atr_rank = compute_atr_pctrank_20d(df, candles_per_day=CANDLES_PER_DAY[timeframe])
        persistence = compute_direction_persistence_10(df)
        valid = compute_atr_14(df).notna() & atr_rank.notna() & persistence.notna()
        regime = _regime_series(
            atr_rank, persistence, cfg_rule["trend_threshold"], cfg_rule["range_threshold"]
        )[valid].reset_index(drop=True)

        minutes = TIMEFRAME_MINUTES[timeframe]
        episodes = regime_episodes(regime)
        print(f"\n-- {timeframe} -- świec z cechami: {len(regime)}")
        for name in ("trend", "range"):
            lengths = episodes.loc[episodes["regime"] == name, "length"]
            if not len(lengths):
                print(f"   {name:6s} reżim nie wystąpił")
                continue
            share = 100 * lengths.sum() / len(regime)
            print(
                f"   {name:6s} epizodów={len(lengths):5d}  mediana={lengths.median():5.1f} świec "
                f"({lengths.median() * minutes:7.0f} min)  udział={share:5.2f}%"
            )
        table = coherence_table(regime, horizons=HORIZONS)
        keep = ["regime", "horizon_candles", "median_length", "n_windows_inside",
                "share_windows_inside", "coherent"]
        print(table[keep].to_string(index=False))


def block_3_geometry(native: dict[str, pd.DataFrame], cfg_rule: dict) -> None:
    print("\n" + "=" * 96)
    print("BLOK 3 — relacja B/C: jak nisko schodzi PRÓG OPŁACALNOŚCI na grubszym interwale?")
    print("=" * 96)
    # H3: koszt bramkowy z JEDNEGO źródła (`gate_cost_fraction`), nie z ręcznej kopii
    # pary nóg. Wartość niezmieniona (0,0009), liczby tego bloku odtwarzalne co do cyfry.
    # Ten moduł NIE jest zamrożonym zapisem rundy w sensie zasady 13 — importują z niego
    # `_load`/`_load_cfg` cztery żywe skrypty (S1, H2.1, K1, H3).
    cost = gate_cost_fraction(EXECUTION_MAKER_LIMIT)
    print(f"koszt round-trip C = {100 * cost:.4f}% nominału (stały per transakcja, model C2.12)\n")
    print(
        f"{'interwał':9s} {'reżim':8s} {'ATR/cena':>10s} {'B=1.5xATR':>11s} "
        f"{'break-even p':>13s} {'zmierzone p':>12s} {'luka':>9s}"
    )
    # `p` zmierzone na 5m po naprawie Z17+Z21 (runs/2026-09-22_z17-z21-*.md). Na 1h/4h
    # NIE jest zmierzone — stąd kolumna pokazuje je tylko dla 5m, jako punkt odniesienia.
    measured_5m = {"range": 0.503763, "trend": 0.508361}
    for timeframe in ("5m", "1h", "4h"):
        df = native[timeframe]
        atr_rank = compute_atr_pctrank_20d(df, candles_per_day=CANDLES_PER_DAY[timeframe])
        persistence = compute_direction_persistence_10(df)
        atr = compute_atr_14(df)
        valid = atr.notna() & atr_rank.notna() & persistence.notna()
        regime = _regime_series(
            atr_rank, persistence, cfg_rule["trend_threshold"], cfg_rule["range_threshold"]
        )
        atr_over_price = atr / df["close"]
        for name in ("range", "trend"):
            mask = valid & (regime == name)
            if not mask.any():
                continue
            atr_med = float(atr_over_price[mask].median())
            barrier = ATR_MULTIPLIER * atr_med
            break_even = 0.5 * (1.0 + cost / barrier)
            if timeframe == "5m":
                p = measured_5m[name]
                gap = f"{100 * (p - break_even):+8.2f}pp"
                p_txt = f"{100 * p:11.2f}%"
            else:
                p_txt, gap = f"{'niezmierz.':>12s}", f"{'—':>9s}"
            print(
                f"{timeframe:9s} {name:8s} {100 * atr_med:9.4f}% {100 * barrier:10.4f}% "
                f"{100 * break_even:12.2f}% {p_txt} {gap}"
            )

    print(
        "\n[interpretacja] Koszt jest STAŁY per transakcja, a ATR rośnie z interwałem, więc\n"
        "próg opłacalności spada bez żadnych założeń o modelu. To jedyny mechanizm w projekcie,\n"
        "który obniża wymaganie wobec `p` nie dotykając `p`. UWAGA: niższy próg nie oznacza,\n"
        "że model go osiągnie — `p` na 1h/4h wymaga osobnego, pre-rejestrowanego pomiaru."
    )


def main() -> None:
    cfg = _load_cfg()
    with open("config/settings.yaml", encoding="utf-8") as f:
        cfg_rule = yaml.safe_load(f)["regime_rule"]

    native = {tf: _load(cfg, tf) for tf in ("5m", "1h", "4h")}
    for tf, df in native.items():
        print(f"[data] {tf}: {len(df)} świec {df['timestamp'].min()} -> {df['timestamp'].max()}")
    print()

    block_1_native_vs_resampled(native)
    block_2_coherence(native, cfg_rule)
    block_3_geometry(native, cfg_rule)


if __name__ == "__main__":
    main()
