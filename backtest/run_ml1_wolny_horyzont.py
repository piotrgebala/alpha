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


# ------------------------------------------------------------------ wspólne: ramka 11 cech
RUN_DIR = "runs/2026-09-30_ml1-wolny-horyzont"
PREREG_COMMIT = "e99dc82530229f5acff22eb527bc86f2535e7109"  # commit karty §14 (pre-rejestracja)
V_CANDLES = 7
CANDLES_PER_DAY = 1
TRAIN_DAYS, TEST_DAYS, STEP_DAYS = 365, 91, 91
MODEL_FILE = "model_ml1.json"


def _frame() -> pd.DataFrame:
    """Świece 1d od 2021-01-01 (fetch_window, zasada 20) + 7 cech ML1 + 4 cechy REVERSION i ATR."""
    from agents.feature_miner import compute_all_features
    from agents.ml1_features import build_ml1_frame, load_ml1_sources

    ohlcv = fetch_window(ml1_data_cfg(), TIMEFRAME)
    frame = build_ml1_frame(ohlcv, **load_ml1_sources(ML1_DIR))
    rule = load_config()["regime_rule"]
    return compute_all_features(
        frame,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
        candles_per_day=CANDLES_PER_DAY,
    )


def _sha256(path: str) -> str:
    import hashlib

    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _git(*args: str) -> str:
    import subprocess

    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ wf (krok 2)
def wf() -> None:
    """Walk-forward 2021–2025 (karta §14.4): wartość progu i kalibracja. Bez zwrotu i t zwrotu."""
    import json
    import time

    from scipy.stats import spearmanr

    from agents.ml1_features import (
        ML1_FEATURES,
        calibration_table,
        confidence_threshold,
        dedup_features,
        signal_hits,
    )
    from backtest.checkpoint_lib import PRIMARY_SEED
    from backtest.engine import REGIME_ALL, collect_signals

    t0 = time.time()
    frame = _frame()
    ts = frame["timestamp"]
    train = frame.loc[ts <= TRAIN_END].reset_index(drop=True)  # ucięte PRZED etykietami
    first_window = train["timestamp"] < train["timestamp"].min() + pd.Timedelta(days=TRAIN_DAYS)
    rho = train.loc[first_window, ML1_FEATURES].corr(method="spearman")
    kept = dedup_features(train.loc[first_window], ML1_FEATURES)
    print(SEP)
    print(
        f"ML1 WF — walk-forward {TRAIN_DAYS}/{TEST_DAYS}/{STEP_DAYS} dni na świecach 1d "
        f"{train['timestamp'].min().date()} → {train['timestamp'].max().date()}; V = {V_CANDLES}; "
        f"pre-rejestracja {PREREG_COMMIT[:7]}; HEAD {_git('rev-parse', '--short', 'HEAD')}"
    )
    print(SEP)
    print("1. Braki cech w ramce uczenia (świece, na których cecha = NaN):")
    for f in ML1_FEATURES:
        x = train[f]
        print(
            f"  {f:>22}: NaN {int(x.isna().sum()):4d} / {len(x)}; pierwsza wartość {train.loc[x.first_valid_index(), 'timestamp'].date()}"
        )
    n_complete = int(train[ML1_FEATURES].notna().all(axis=1).sum())
    print(f"  świece z kompletem 11 cech: {n_complete} / {len(train)}")
    print(
        f"\n2. Usuwanie duplikatów (|Spearman| > 0,9) na pierwszym oknie uczenia "
        f"({train['timestamp'].min().date()} + {TRAIN_DAYS} dni):"
    )
    print(rho.round(2).to_string())
    dropped = [f for f in ML1_FEATURES if f not in kept]
    print(f"  cechy modelu ({len(kept)}): {kept}; odpadły: {dropped or 'żadna'}")

    rule = load_config()["regime_rule"]
    c = collect_signals(
        train,
        seed=PRIMARY_SEED,
        regime_feature_sets=[(REGIME_ALL, kept)],
        vertical_barrier_candles=V_CANDLES,
        candles_per_day=CANDLES_PER_DAY,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        trend_threshold=rule["trend_threshold"],
        range_threshold=rule["range_threshold"],
    )
    df = c["df"]
    folds = c["folds_summary"]
    active = [f for f in folds if not f["skipped"]]
    print(f"\n3. Foldy: {len(active)}/{len(folds)} aktywnych; trening {time.time() - t0:.0f} s")
    print(
        f"  {'fold':>4} | {'test od':>10} | {'test do':>10} | {'ocenione':>8} | {'bez kier.':>9} | "
        f"{'bramka koszt.':>13} | {'sygnały':>7} | {'early stop':>10} | {'best_it':>7}"
    )
    for f in folds:
        if f["skipped"]:
            print(f"  {f['fold_idx']!s:>4} | POMINIĘTY: {f['skip_reason']}")
            continue
        print(
            f"  {f['fold_idx']:4d} | {str(f['test_start'].date()):>10} | {str(f['test_end'].date()):>10} | "
            f"{f['n_rows_evaluated']:8d} | {f['n_signals_no_direction']:9d} | {f['n_signals_cost_gated']:13d} | "
            f"{f['n_signals']:7d} | {str(f['early_stopping_used']):>10} | {f['best_iteration']:7d}"
        )
    n_rows = sum(f["n_rows_evaluated"] for f in active)
    n_abst = sum(f["n_signals_no_direction"] for f in active)
    print(
        f"  razem: świece ocenione {n_rows}, bez kierunku {n_abst} (abstynencja {100 * n_abst / max(n_rows, 1):.1f} %), "
        f"sygnały {len(c['candidate_signals'])}"
    )

    sig = pd.DataFrame(c["candidate_signals"])
    idx = sig["original_index"].to_numpy()
    sig["close_timeout"] = df["close"].to_numpy()[idx + V_CANDLES]
    sig["hit"] = signal_hits(
        sig["signal_direction"], sig["label"], sig["entry_price"], sig["close_timeout"]
    )
    thr = confidence_threshold(sig["signal_confidence"], TOP_SHARE)
    sig["ponad_progiem"] = sig["signal_confidence"] >= thr
    n_all = len(sig)
    n_top = int(sig["ponad_progiem"].sum())
    print(
        f"\n4. PRÓG (§14.1): kwantyl {1 - TOP_SHARE:.2f} pewności {n_all} sygnałów OOS = {thr:.6f}; "
        f"ponad progiem {n_top} ({100 * n_top / n_all:.1f} %); long/short wszystkie "
        f"{int((sig['signal_direction'] > 0).sum())}/{int((sig['signal_direction'] < 0).sum())}, ponad progiem "
        f"{int((sig.loc[sig['ponad_progiem'], 'signal_direction'] > 0).sum())}/"
        f"{int((sig.loc[sig['ponad_progiem'], 'signal_direction'] < 0).sum())}"
    )
    print(
        f"  pewność: min {sig['signal_confidence'].min():.4f}, mediana {sig['signal_confidence'].median():.4f}, "
        f"max {sig['signal_confidence'].max():.4f}; sygnały per rok OOS: "
        + ", ".join(f"{y}: {n}" for y, n in sig.groupby(sig["timestamp"].dt.year).size().items())
    )
    tab = calibration_table(sig["signal_confidence"].to_numpy(), sig["hit"].to_numpy(), N_BUCKETS)
    print(
        "\n5. KALIBRACJA (§14.6): trafność sygnału = kierunek zgodny z ruchem do pierwszej bariery "
        "±1,5·ATR albo do zamknięcia po 7 dniach; bez kosztów, bez zwrotu; ±Wald bez korekty na nakładanie"
    )
    print(tab.round(4).to_string(index=False))
    p_all = float(sig["hit"].mean())
    p_top = float(sig.loc[sig["ponad_progiem"], "hit"].mean())
    rho_b = spearmanr(tab["kubelek"], tab["trafnosc"]).statistic
    print(
        f"  wszystkie sygnały: n {n_all}, trafność {100 * p_all:.2f} % ±{100 * 1.959964 * np.sqrt(p_all * (1 - p_all) / n_all):.2f} pp"
    )
    print(
        f"  ponad progiem:     n {n_top}, trafność {100 * p_top:.2f} % ±{100 * 1.959964 * np.sqrt(p_top * (1 - p_top) / n_top):.2f} pp"
    )
    grows = bool(p_top > p_all and rho_b > 0)
    print(
        f"  korelacja rang kubełek–trafność {rho_b:+.2f}; warunek „rosnąca trafność” (§14.6: górny kubełek > wszystkie "
        f"ORAZ korelacja > 0): {'SPEŁNIONY' if grows else 'NIESPEŁNIONY → ryzyko do karty, reguła bez zmian'}"
    )
    tab.to_csv(f"{RUN_DIR}/kalibracja_wf.csv", index=False)
    sig[
        [
            "timestamp",
            "fold_idx",
            "signal_direction",
            "signal_confidence",
            "label",
            "hit",
            "ponad_progiem",
        ]
    ].to_csv(f"{RUN_DIR}/sygnaly_oos_wf.csv", index=False)
    with open(f"{RUN_DIR}/wf_prog.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "features": kept,
                "dropped_by_dedup": dropped,
                "top_share": TOP_SHARE,
                "threshold": thr,
                "n_signals_oos": n_all,
                "n_above": n_top,
                "abstention_oos": n_abst / max(n_rows, 1),
                "folds_active": len(active),
                "prereg_commit": PREREG_COMMIT,
                "code_commit": _git("rev-parse", "HEAD"),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n  zapisano: {RUN_DIR}/wf_prog.json, kalibracja_wf.csv, sygnaly_oos_wf.csv")
    print(SEP)


# ------------------------------------------------------------------ zamroz (krok 3)
def zamroz() -> None:
    """Jeden model na 2021-01-01 → 2025-12-31 (karta §14.5) + manifest z hashami. Bez douczania."""
    import json
    import platform

    import xgboost as xgb

    from agents.labeling import ATR_MULTIPLIER, compute_triple_barrier_labels
    from agents.ml_optimizer import (
        DEFAULT_XGB_PARAMS,
        EARLY_STOPPING_ROUNDS,
        NUM_BOOST_ROUND,
        best_iteration_or_last,
        predict_signal,
        train_regime_model,
    )
    from backtest.checkpoint_lib import PRIMARY_SEED
    from backtest.engine import DEFAULT_CLASS_WEIGHT_MODE
    from agents.ml_optimizer import DEFAULT_VALIDATION_FRACTION

    with open(f"{RUN_DIR}/wf_prog.json", encoding="utf-8") as f:
        wfp = json.load(f)
    kept = wfp["features"]
    frame = _frame()
    train = frame.loc[frame["timestamp"] <= TRAIN_END].reset_index(drop=True)
    lab = compute_triple_barrier_labels(train, vertical_barrier_candles=V_CANDLES)
    train["label"] = lab["label"]
    clean = train.dropna(subset=[*kept, "label"])
    booster = train_regime_model(
        train,
        train,  # na ścieżce validation_fraction test_df nie jest używany (tylko kontrola niepustości)
        kept,
        seed=PRIMARY_SEED,
        validation_fraction=DEFAULT_VALIDATION_FRACTION,
        embargo_candles=V_CANDLES,
        class_weight_mode=DEFAULT_CLASS_WEIGHT_MODE,
    )
    path = f"{RUN_DIR}/{MODEL_FILE}"
    booster.save_model(path)
    loaded = xgb.Booster()
    loaded.load_model(path)
    p_mem = predict_signal(booster, clean, kept)
    p_file = predict_signal(loaded, clean, kept)
    same = bool(p_mem.equals(p_file))
    best = best_iteration_or_last(booster)
    data_files = {
        name: _sha256(f"{ML1_DIR}/{name}")
        for name in (
            "BTC-USDT-USDT_1d_20190910T000000Z_20260930T000000Z.parquet",
            "BTC-USDT-USDT_funding_20190910T000000Z_20260930T000000Z.parquet",
            "binance_metrics_BTCUSDT_5m.parquet",
            "deribit_dvol_BTC_1d.parquet",
            "coinmetrics_btc_1d.parquet",
            "alternative_fng_1d.parquet",
        )
    }
    manifest = {
        "runda": "ML1 (zadanie 028)",
        "model_file": MODEL_FILE,
        "model_sha256": _sha256(path),
        "features": kept,
        "train_first_candle": str(train["timestamp"].min()),
        "train_last_candle": str(TRAIN_END),
        "train_rows_with_label_and_features": int(len(clean)),
        "train_rows_used_after_embargo": int(len(clean) - V_CANDLES),
        "label_counts": {
            str(k): int(v) for k, v in clean["label"].value_counts().sort_index().items()
        },
        "xgb_params": {**DEFAULT_XGB_PARAMS, "seed": PRIMARY_SEED},
        "num_boost_round": NUM_BOOST_ROUND,
        "early_stopping_rounds": EARLY_STOPPING_ROUNDS,
        "validation_fraction": DEFAULT_VALIDATION_FRACTION,
        "embargo_candles": V_CANDLES,
        "class_weight_mode": DEFAULT_CLASS_WEIGHT_MODE,
        "direction_policy": "argmax3",
        "confidence_mode": "class",
        "best_iteration": best,
        "early_stopping_used": getattr(booster, "best_iteration", None) is not None,
        "vertical_barrier_candles": V_CANDLES,
        "atr_multiplier": ATR_MULTIPLIER,
        "timeframe": TIMEFRAME,
        "top_share": TOP_SHARE,
        "threshold": wfp["threshold"],
        "threshold_source": "kwantyl 0,80 pewności sygnałów OOS walk-forward 2021–2025 (wf_prog.json)",
        "prereg_commit": PREREG_COMMIT,
        "code_commit": _git("rev-parse", "HEAD"),
        "worktree_clean_code": _git("status", "--porcelain", "--", "backtest", "agents") == "",
        "data_dir": ML1_DIR,
        "data_sha256": data_files,
        "versions": {
            "python": platform.python_version(),
            "xgboost": xgb.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "frozen_at_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
    }
    with open(f"{RUN_DIR}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(SEP)
    print(f"ML1 ZAMROŻENIE — jeden model na {train['timestamp'].min().date()} → {TRAIN_END.date()}")
    print(SEP)
    for k in (
        "model_sha256",
        "features",
        "train_rows_with_label_and_features",
        "train_rows_used_after_embargo",
        "label_counts",
        "best_iteration",
        "early_stopping_used",
        "threshold",
        "prereg_commit",
        "code_commit",
        "worktree_clean_code",
        "versions",
    ):
        print(f"  {k}: {manifest[k]}")
    print(f"  predykcje z pamięci == predykcje z pliku (dane uczenia, {len(clean)} świec): {same}")
    print(f"  zapisano {path} i {RUN_DIR}/manifest.json")
    print(SEP)


# ------------------------------------------------------------------ rozbieg (krok 4)
def rozbieg() -> None:
    """2026-01-01 → ostatni pełny dzień: tylko mechanika (sygnały, udział ponad progiem, dziury). Bez zwrotów."""
    import json

    import xgboost as xgb

    from agents.ml1_features import ML1_FEATURES
    from agents.ml_optimizer import predict_signal

    with open(f"{RUN_DIR}/manifest.json", encoding="utf-8") as f:
        man = json.load(f)
    path = f"{RUN_DIR}/{man['model_file']}"
    sha_ok = _sha256(path) == man["model_sha256"]
    booster = xgb.Booster()
    booster.load_model(path)
    kept = man["features"]
    thr = man["threshold"]
    frame = _frame()
    run = frame.loc[frame["timestamp"] >= RUNIN_START].reset_index(drop=True)
    print(SEP)
    print(
        f"ML1 ROZBIEG — {run['timestamp'].min().date()} → {run['timestamp'].max().date()} ({len(run)} świec); "
        f"model {man['model_sha256'][:12]}… (sha256 zgodny z manifestem: {sha_ok}); próg {thr:.6f}"
    )
    print(
        "  TYLKO MECHANIKA: bez etykiet, trafności, zwrotu i t (decyzja użytkownika 2026-09-30, opcja A)"
    )
    print(SEP)
    print("1. Dziury w cechach (świece 2026 z NaN):")
    for f in ML1_FEATURES:
        nan_days = run.loc[run[f].isna(), "timestamp"].dt.date.astype(str).tolist()
        mark = "" if f in kept else " (poza modelem)"
        print(f"  {f:>22}{mark}: {len(nan_days)} {nan_days[:8]}")
    pred = predict_signal(booster, run, kept)
    run = run.join(pred)
    has = run["signal_direction"].notna()
    dirn = run.loc[has, "signal_direction"]
    n_dir = int((dirn != 0).sum())
    top = has & (run["signal_direction"] != 0) & (run["signal_confidence"] >= thr)
    print(
        f"\n2. Sygnały: świece z predykcją {int(has.sum())}/{len(run)}; long {int((dirn > 0).sum())}, short "
        f"{int((dirn < 0).sum())}, bez kierunku {int((dirn == 0).sum())} (abstynencja {100 * (dirn == 0).mean():.1f} %)"
    )
    print(
        f"   ponad progiem: {int(top.sum())} z {n_dir} sygnałów z kierunkiem ({100 * top.sum() / max(n_dir, 1):.1f} %; "
        f"zapisany udział {100 * TOP_SHARE:.0f} %)"
    )
    print(
        f"   pewność sygnałów z kierunkiem: min {run.loc[run['signal_direction'].fillna(0) != 0, 'signal_confidence'].min():.4f}, "
        f"mediana {run.loc[run['signal_direction'].fillna(0) != 0, 'signal_confidence'].median():.4f}, "
        f"max {run.loc[run['signal_direction'].fillna(0) != 0, 'signal_confidence'].max():.4f}"
    )
    run["miesiac"] = run["timestamp"].dt.strftime("%Y-%m")
    run["ponad_progiem"] = top
    month = run.groupby("miesiac").agg(
        swiece=("timestamp", "size"),
        z_predykcja=("signal_direction", lambda s: int(s.notna().sum())),
        long=("signal_direction", lambda s: int((s > 0).sum())),
        short=("signal_direction", lambda s: int((s < 0).sum())),
        ponad_progiem=("ponad_progiem", "sum"),
    )
    print("\n3. Per miesiąc:")
    print(month.to_string())
    last = run.iloc[-1]
    print(
        f"\n4. Ostatnia świeca {last['timestamp'].date()}: kierunek {last['signal_direction']}, "
        f"pewność {last['signal_confidence']:.4f}, ponad progiem {bool(last['ponad_progiem'])}"
    )
    run[["timestamp", "signal_direction", "signal_confidence", "ponad_progiem"]].to_csv(
        f"{RUN_DIR}/sygnaly_rozbieg_2026.csv", index=False
    )
    print(f"  zapisano {RUN_DIR}/sygnaly_rozbieg_2026.csv")
    print(SEP)


# ------------------------------------------------------------------ foldy (diagnostyka progu, bez etykiet)
def foldy() -> None:
    """Skąd pochodzą sygnały ponad progiem: per fold walk-forward (tylko pewność, bez etykiet i trafności)."""
    import json

    sig = pd.read_csv(f"{RUN_DIR}/sygnaly_oos_wf.csv")
    with open(f"{RUN_DIR}/wf_prog.json", encoding="utf-8") as f:
        thr = json.load(f)["threshold"]
    g = sig.groupby("fold_idx").agg(
        sygnaly=("signal_confidence", "size"),
        ponad_progiem=("ponad_progiem", "sum"),
        pewnosc_mediana=("signal_confidence", "median"),
        pewnosc_max=("signal_confidence", "max"),
    )
    print(SEP)
    print(
        f"ML1 FOLDY — sygnały ponad progiem {thr:.6f} per fold walk-forward (best_iteration: tabela trybu wf)"
    )
    print(SEP)
    print(g.round(4).to_string())
    below = int((g["pewnosc_max"] < thr).sum())
    top = g.sort_values("ponad_progiem", ascending=False)
    share4 = float(top["ponad_progiem"].iloc[:4].sum() / g["ponad_progiem"].sum())
    print(
        f"  foldy, w których ŻADEN sygnał nie sięga progu: {below}/{len(g)}; "
        f"4 foldy z największą liczbą dają {100 * share4:.1f} % sygnałów ponad progiem "
        f"(foldy {top.index[:4].tolist()})"
    )
    print(SEP)


MODES = {
    "dane": dane,
    "pokrycie": pokrycie,
    "moc": moc,
    "wf": wf,
    "zamroz": zamroz,
    "rozbieg": rozbieg,
    "foldy": foldy,
}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pokrycie"
    MODES[mode]()
