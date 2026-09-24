"""
run_coinbase_cp1_oos.py — odczyt prospektywny CP1P: reguła CP1 (`run_coinbase_cp1.py`, bez zmian:
premia Coinbase 7 vs 90 dni → znak pozycji BTC, silnik TS1) na danych 2026-07-01 → 2026-09-23,
których projekt nie oglądał. Opisowo, 0 wariantów, próg obalenia zapisany z góry
(`runs/2026-09-24_cp1-poza-proba/README.md`).

    PYTHONUTF8=1 py -m backtest.run_coinbase_cp1_oos
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import load_config
from backtest.run_coinbase_cp1 import COINBASE, daily_premium, premium_signal
from backtest.ts_momentum import DAYS_PER_YEAR, portfolio
from backtest.xs_momentum import daily_funding_panel

SPOT_OLD = "data/raw/BTC-USDT_8h_20210101T000000Z_20260701T000000Z.parquet"
SPOT_NEW = "data/raw/BTC-USDT_8h_20260301T000000Z_20260924T000000Z.parquet"
UNIVERSE_Q3_DIR = "data/raw/universe_2026q3"
START, END = "2026-07-01", "2026-09-24"
CP1_MEAN, CP1_SD = 0.320, 0.348
Z95 = 1.959964
SEP = "=" * 104


def main() -> None:
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    spot = pd.concat([pd.read_parquet(SPOT_OLD), pd.read_parquet(SPOT_NEW)])
    spot = spot.drop_duplicates("timestamp").sort_values("timestamp")
    prem = daily_premium(pd.read_parquet(COINBASE), spot)
    b = pd.read_parquet(f"{UNIVERSE_Q3_DIR}/BTCUSDT_1d.parquet")
    close = pd.DataFrame(
        {"BTCUSDT": b.set_index(pd.to_datetime(b["open_time"], utc=True))["close"].astype(float)}
    )
    end = pd.Timestamp(END, tz="UTC")
    close = close[close.index < end]
    signs = pd.DataFrame({"BTCUSDT": premium_signal(prem).reindex(close.index)})
    funding = daily_funding_panel(UNIVERSE_Q3_DIR)[["BTCUSDT"]]
    start = pd.Timestamp(START, tz="UTC")
    members = {
        pd.Timestamp(m, tz="UTC"): ["BTCUSDT"] for m in ("2026-07-01", "2026-08-01", "2026-09-01")
    }
    avg, phases = portfolio(close, funding, members, start, end, fee, signs_override=signs)
    avg = avg.dropna()
    n = len(avg)
    mean_ann = float(avg["net"].mean()) * DAYS_PER_YEAR
    floor = CP1_MEAN - Z95 * CP1_SD / np.sqrt(n / DAYS_PER_YEAR)
    s_eval = signs["BTCUSDT"][signs.index >= start]
    print(SEP)
    print("CP1P — REGUŁA CP1 (zamrożona) NA NOWYCH DANYCH 2026-07-01 → 2026-09-23 (BTC, 7 faz)")
    print(SEP)
    print(
        f"  premia: dane do {prem.index.max().date()}; w okresie mediana {100 * prem[prem.index >= start].median():+.3f}%; "
        f"sygnał: dni long {100 * (s_eval > 0).mean():.0f}%, zmiany znaku {int((s_eval.diff().abs() > 0).sum())}"
    )
    print(
        f"  dni ze wszystkimi fazami: {n} ({avg['date'].min().date()} → {avg['date'].max().date()}); zwrot netto skumulowany "
        f"{100 * (np.prod(1 + avg['net']) - 1):+.2f}% (brutto {100 * avg['gross'].sum():+.2f}%, funding {100 * avg['funding'].sum():+.2f}%, "
        f"koszt {100 * avg['cost'].sum():.2f}%) = {100 * mean_ann:+.1f}%/rok; zmienność {100 * avg['net'].std() * np.sqrt(DAYS_PER_YEAR):.1f}%/rok"
    )
    btc = close["BTCUSDT"]
    print(
        f"  BTC w tym czasie: {100 * (btc[btc.index <= avg['date'].max()].iloc[-1] / btc[btc.index < avg['date'].min()].iloc[-1] - 1):+.1f}%"
    )
    print(
        f"  PRÓG OBALENIA (z góry): przy prawdziwym +{100 * CP1_MEAN:.0f}%/rok i zmienności {100 * CP1_SD:.1f}%/rok "
        f"średnia z {n} dni poniżej {100 * floor:+.0f}%/rok zdarza się w < 2,5% przypadków"
    )
    print(
        f"  >>> ODCZYT CP1P (opisowy): {'CP1 OBALONE' if mean_ann < floor else 'brak obalenia (i brak potwierdzenia)'}"
    )
    print(
        "  7 faz (skumulowane netto): "
        + ", ".join(
            f"{100 * (np.prod(1 + p['net'][p.index >= avg['date'].min()]) - 1):+.1f}%"
            for p in phases
        )
    )
    print(SEP)


if __name__ == "__main__":
    main()
