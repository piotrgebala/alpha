"""
run_ml1_wolny_horyzont.py — runda ML1 (zadanie 028): jeden model XGBoost na świecy 1d BTC,
11 cech zapisanych z góry, V = 7 dni. Karta pre-rejestracji: `runs/DRAFT_028.md` (§14 = reguła
progu pewności i uzupełnienia przed uczeniem). Katalog rundy: `runs/2026-09-30_ml1-wolny-horyzont/`.

Tryby (kolejność = kolejność kroków zadania 028; każdy drukuje na stdout, nic nie ocenia):

    PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont dane       # pobranie/przedłużenie danych do data/raw/ml1
    PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont pokrycie   # tabela pokrycia 11 cech (od, do, dziury)
    PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont moc        # rachunek mierzalności progu (zasada 18)
    PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont wf         # walk-forward 2021–2025: próg + kalibracja
    PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont zamroz     # jeden model 2021–2025 + manifest z hashami
    PYTHONUTF8=1 py -m backtest.run_ml1_wolny_horyzont rozbieg    # 2026: tylko mechanika (bez zwrotów)

Czego ten skrypt NIE liczy (decyzja użytkownika 2026-09-30, opcja A): zwrotu, t zwrotu ani trafności
na 2026 (rozbieg); zwrotu ani t zwrotu na walk-forward 2021–2025 (tam tylko próg i kalibracja).
Neutralny reporter — werdykt podpisuje Claude w README rundy.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import fetch_window, load_config
from backtest.metrics import expected_trades, measurability_report, wald_half_width

# --- konfiguracja ZAMROŻONA (karta runs/DRAFT_028.md §4–§5, §14) -------------------------------
TIMEFRAME = "1d"
DATA_END = "2026-09-30T00:00:00Z"  # wyłącznie: ostatnia pełna świeca = 2026-09-29
TRAIN_START = pd.Timestamp("2021-01-01", tz="UTC")  # zasada 20 (fetch_window i tak filtruje)
TRAIN_END = pd.Timestamp("2025-12-31", tz="UTC")  # ostatnia świeca uczenia (włącznie)
RUNIN_START = pd.Timestamp("2026-01-01", tz="UTC")  # rozbieg bez werdyktu
ML1_DIR = "data/raw/ml1"  # dane przedłużone do DATA_END (poza gitem)
SEP = "=" * 110

# Reguła progu pewności (decyzja użytkownika 2026-09-30 „Dopisz”, warunki 1–5) — karta §14.1
TOP_SHARE = 0.20  # górne 20 % pewności wśród sygnałów z kierunkiem (górny kwintyl)
N_BUCKETS = 5  # kubełki kalibracji = kwintyle pewności (próg = granica górnego kubełka)

# Założenia rachunku mocy (karta §7 i §14.2)
P_STAR = 0.5089  # break_even_hit_rate(0,0008; 1,5 × ATR 3 %)
ABSTENTION_MID = 0.378  # SW etap 2
OVERLAP_MID = 2.0  # transakcje 7-dniowe nachodzą na siebie → niezależnych 2× mniej
HYP_P = (0.52, 0.53, 0.55, 0.60)


def ml1_data_cfg() -> dict:
    """Konfiguracja danych z settings.yaml z końcem DATA_END i cache w ML1_DIR (min_start bez zmian)."""
    cfg = dict(load_config()["data"])
    cfg["end"] = DATA_END
    cfg["cache_dir"] = ML1_DIR
    return cfg


# ------------------------------------------------------------------ dane
def dane() -> None:
    """Przedłuża dane do DATA_END w data/raw/ml1 (kopia repo głównego nietknięta)."""
    import datetime as dt
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    from data.fetch_external import (
        ARCHIVE_FILE_URL,
        fetch_coinmetrics,
        fetch_dvol,
        fetch_fng,
        http_get,
        parse_metrics_csv,
        read_zip_csv,
        s3_list,
        COINMETRICS_METRICS,
    )
    from data.fetch_funding import get_funding_rate_history_cached
    from data.fetch_ohlcv import get_ohlcv_cached

    out = Path(ML1_DIR)
    out.mkdir(parents=True, exist_ok=True)
    cfg = load_config()["data"]
    start_1d = cfg["timeframe_start_overrides"]["1d"]
    print(SEP)
    print(f"ML1 — DANE do {DATA_END} w {out} (dziś {dt.datetime.now(dt.UTC):%Y-%m-%d %H:%M} UTC)")
    print(SEP)
    ohlcv = get_ohlcv_cached(
        cfg["primary_symbol"], TIMEFRAME, start_1d, DATA_END, str(out), cfg["exchange_id"]
    )
    print(f"  OHLCV 1d: {len(ohlcv)} świec {ohlcv['timestamp'].min()} → {ohlcv['timestamp'].max()}")
    fund = get_funding_rate_history_cached(
        cfg["primary_symbol"], start_1d, DATA_END, str(out), cfg["exchange_id"]
    )
    print(f"  funding: {len(fund)} rozliczeń {fund['timestamp'].min()} → {fund['timestamp'].max()}")
    # archiwum metrics: kopia z repo głównego (do 2026-09-22) + brakujące dni z data.binance.vision
    old_path = Path("data/raw/external/binance_metrics_BTCUSDT_5m.parquet")
    old = pd.read_parquet(old_path)
    last_day = pd.to_datetime(old["timestamp"], utc=True).max().floor("1D")
    keys, _ = s3_list("data/futures/um/daily/metrics/BTCUSDT/")
    new_keys = [k for k in keys if pd.Timestamp(k[-14:-4], tz="UTC") >= last_day]
    print(f"  metrics: kopia do {last_day.date()}; dni do pobrania {[k[-14:-4] for k in new_keys]}")
    with ThreadPoolExecutor(max_workers=4) as ex:
        frames = list(
            ex.map(
                lambda k: parse_metrics_csv(read_zip_csv(http_get(ARCHIVE_FILE_URL + k))), new_keys
            )
        )
    merged = (
        pd.concat([old, *frames], ignore_index=True)
        .assign(timestamp=lambda d: pd.to_datetime(d["timestamp"], utc=True))
        .drop_duplicates("timestamp", keep="first")  # kopia wygrywa na zakładce (bez rewizji)
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    merged.to_parquet(out / "binance_metrics_BTCUSDT_5m.parquet", index=False)
    print(
        f"  metrics: {len(merged)} odczytów {merged['timestamp'].min()} → {merged['timestamp'].max()}"
    )
    fetch_dvol("BTC", "2019-01-01", out, force=True)
    fetch_coinmetrics("btc", COINMETRICS_METRICS, "2019-01-01", out, force=True)
    fetch_fng(out, force=True)
    print(SEP)


# ------------------------------------------------------------------ pokrycie
def _gaps(ts: pd.Series, lo: pd.Timestamp | None = None) -> tuple[str, str, int, list[str]]:
    t = pd.to_datetime(ts, utc=True).dt.floor("1D").drop_duplicates().sort_values()
    if lo is not None:
        t = t[t >= lo]
    full = pd.date_range(t.min(), t.max(), freq="1D", tz="UTC")
    miss = full.difference(t)
    runs: list[str] = []
    if len(miss):
        grp = (pd.Series(miss).diff() != pd.Timedelta(days=1)).cumsum()
        for _, g in pd.Series(miss).groupby(grp.to_numpy()):
            a, b = g.iloc[0].date(), g.iloc[-1].date()
            runs.append(f"{a}" if a == b else f"{a}→{b} ({len(g)} d)")
    return str(t.min().date()), str(t.max().date()), len(miss), runs


def name_file(name: str) -> str:
    return {
        "DVOL": "deribit_dvol_BTC_1d.parquet",
        "CoinMetrics": "coinmetrics_btc_1d.parquet",
        "F&G": "alternative_fng_1d.parquet",
    }[name]


def pokrycie() -> None:
    """Od, do, dziury (dni bez żadnego ważnego odczytu) źródeł 11 cech; bez cen i zwrotów."""
    lo = pd.Timestamp("2021-01-01", tz="UTC")
    d = ML1_DIR
    ohlcv = pd.read_parquet(f"{d}/BTC-USDT-USDT_1d_20190910T000000Z_20260930T000000Z.parquet")
    fund = pd.read_parquet(f"{d}/BTC-USDT-USDT_funding_20190910T000000Z_20260930T000000Z.parquet")
    m = pd.read_parquet(f"{d}/binance_metrics_BTCUSDT_5m.parquet")
    dvol = pd.read_parquet(f"{d}/deribit_dvol_BTC_1d.parquet")
    cm = pd.read_parquet(f"{d}/coinmetrics_btc_1d.parquet")
    fng = pd.read_parquet(f"{d}/alternative_fng_1d.parquet")
    rows = [
        ("1–4 OHLCV 1d BTCUSDT perp (volume w BTC)", ohlcv["timestamp"]),
        ("5 funding_rate (rozliczenia 8h)", fund["timestamp"]),
        ("6 oi_change_24h (sum_open_interest > 0)", m.loc[m["sum_open_interest"] > 0, "timestamp"]),
        (
            "7 global_ls_log (count_long_short_ratio > 0)",
            m.loc[m["count_long_short_ratio"] > 0, "timestamp"],
        ),
        (
            "8 taker_imbalance_24h (sum_taker_long_short_vol_ratio > 0)",
            m.loc[m["sum_taker_long_short_vol_ratio"] > 0, "timestamp"],
        ),
        ("9 vrp_30d (DVOL BTC 1d)", dvol["date"]),
        ("10 ex_supply_change_7d (SplyExNtv)", cm.loc[cm["SplyExNtv"].notna(), "date"]),
        ("11 fng_level (alternative.me)", fng["date"]),
    ]
    print(SEP)
    print(f"ML1 — POKRYCIE DANYCH DZIENNYCH 11 CECH (BTC), od {lo.date()} (zasada 20), pliki {d}")
    print(SEP)
    for name, ts in rows:
        a, b, n, runs = _gaps(ts, lo)
        print(f"  {name:60} od {a} do {b} | dni bez odczytu {n:3d} | {'; '.join(runs) or '—'}")
    # dni z NIEPEŁNĄ dobą odczytów 5-min (≥ 1 h brakujących odczytów) — dotyczy cech 6–8
    mm = m.assign(day=pd.to_datetime(m["timestamp"], utc=True).dt.floor("1D"))
    mm = mm[mm["day"] >= lo]
    cnt = mm.groupby("day").size()
    short = cnt[cnt < 288 - 12]
    print(
        f"  metrics: dni z < 276 z 288 odczytów 5-min: {len(short)} {[str(x.date()) for x in short.index[:12]]}"
    )
    # zasada 20: filtr fetch_window na przedłużonym pliku + zgodność z kopią repo głównego
    win = fetch_window(ml1_data_cfg(), TIMEFRAME)
    print(
        f"  fetch_window (min_start {load_config()['data']['min_start']}): {len(win)} świec {win['timestamp'].min()} → {win['timestamp'].max()}"
    )
    for name, new_df, old_file in (
        ("OHLCV 1d", ohlcv, "data/raw/BTC-USDT-USDT_1d_20190910T000000Z_20260701T000000Z.parquet"),
        (
            "funding",
            fund,
            "data/raw/BTC-USDT-USDT_funding_20190910T000000Z_20260701T000000Z.parquet",
        ),
    ):
        old = pd.read_parquet(old_file)
        both = old.merge(new_df, on="timestamp", suffixes=("_s", "_n"))
        cols = [c for c in old.columns if c != "timestamp"]
        diff = max(float((both[f"{c}_s"] - both[f"{c}_n"]).abs().max()) for c in cols)
        print(
            f"  zgodność {name} z kopią repo głównego (do 2026-06-30): wspólnych {len(both)}/{len(old)}, max |różnica| {diff:.3g}"
        )
    for name, new_df, col in (
        ("DVOL", dvol, "close"),
        ("CoinMetrics", cm, "SplyExNtv"),
        ("F&G", fng, "value"),
    ):
        old = pd.read_parquet(f"data/raw/external/{name_file(name)}")
        both = old[["date", col]].merge(new_df[["date", col]], on="date", suffixes=("_s", "_n"))
        both = both[pd.to_datetime(both["date"], utc=True) >= lo]
        d_abs = (both[f"{col}_s"].astype(float) - both[f"{col}_n"].astype(float)).abs()
        print(
            f"  zgodność {name}.{col} z kopią z 2026-09-23 (od {lo.date()}): wspólnych {len(both)}, "
            f"dni z różnicą {int((d_abs > 1e-9).sum())}, max |różnica| {float(d_abs.max()):.4g}"
        )
    print(SEP)


# ------------------------------------------------------------------ moc (reguła progu)
def moc() -> None:
    """Rachunek mierzalności reguły progu (zasada 18), tor P od dnia zamrożenia. Bez danych rynkowych."""
    print(SEP)
    print(
        f"ML1 — MIERZALNOŚĆ REGUŁY PROGU: górne {TOP_SHARE:.0%} pewności; p* {P_STAR:.4f}; "
        f"abstynencja {ABSTENTION_MID:.3f}; nakładanie {OVERLAP_MID:.0f}×"
    )
    print(SEP)
    print(
        f"  {'szereg':>22} | {'mies.':>5} | {'decyzje':>7} | {'n niezal.':>9} | {'±Wald':>7} | "
        f"{'p potrzebne':>11} | " + " | ".join(f"p {100 * p:.0f} %" for p in HYP_P)
    )
    for label, share in (
        ("wszystkie sygnały", 1.0),
        (f"ponad progiem ({TOP_SHARE:.0%})", TOP_SHARE),
    ):
        for months in (6, 12, 24, 60):
            days = round(months * 365.25 / 12)
            n = expected_trades(days / OVERLAP_MID, ABSTENTION_MID, share)
            reps = [measurability_report(p, P_STAR, n) for p in HYP_P]
            print(
                f"  {label:>22} | {months:5d} | {days:7d} | {n:9.1f} | {100 * wald_half_width(n):6.2f}pp | "
                f"{100 * reps[0]['p_detectable']:10.2f}% | "
                + " | ".join(f"{r['verdict'][:4]:>6}" for r in reps)
            )
    n_year = expected_trades(365 / OVERLAP_MID, ABSTENTION_MID, TOP_SHARE)
    print(
        f"\n  n niezależnych rocznie ponad progiem: {n_year:.1f} (decyzji z kierunkiem rocznie {365 * (1 - ABSTENTION_MID):.0f})"
    )
    for p in HYP_P:
        need = (1.959964 / 2 / (p - P_STAR)) ** 2  # n z wald_half_width(n) = p − p* (p(1−p) ≈ 0,25)
        print(
            f"  p {100 * p:.0f} %: potrzeba n ≈ {need:7.0f} niezależnych → ponad progiem ≈ {need / n_year:6.1f} lat"
        )
    print("\n  Druga droga (ręcznie, bez metrics.py): ±Wald = 1,96·√(0,25/n)")
    for n in (18.0, 36.3, 72.5):
        print(
            f"    n {n:5.1f}: {100 * 1.96 * np.sqrt(0.25 / n):.4f} pp (metrics.wald_half_width: {100 * wald_half_width(n):.4f} pp)"
        )
    print(SEP)


MODES = {"dane": dane, "pokrycie": pokrycie, "moc": moc}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pokrycie"
    MODES[mode]()
