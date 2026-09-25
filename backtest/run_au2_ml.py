"""
run_au2_ml.py — AU2 kroki 1–2 (kalibracja przyrządu przekrojowego z ML, 0 wariantów hipotez).

Świat symulacji na PRAWDZIWYCH danych top-50 (skład miesięczny z danych sprzed miesiąca):
- cechy: 10 prawdziwych (lista A, zamrożona) + nośnik `x` (losowy AR(1), półtrwanie 28 dni),
  rangowane w przekroju członków każdego dnia; wszystkie z danych ≤ t (test przecieku);
- cel: zwrot 7-dniowy od zamknięcia t, **permutowany między członkami w obrębie każdego dnia**
  (zachowuje przekrój, daty i korelacje; niszczy związek cecha → zwrot);
  ramię pozytywne: + a · z(x), a skalowane tak, by wyrocznia (ranking po x) zarabiała
  `strength` %/rok netto;
- pipeline: walk-forward kwartalny (test 2022-04 → 2026-06), trening 365 dni, purging 7 + embargo
  7 dni; w każdym kwartale wybór 1 z 24 konfiguracji (8 zestawów cech × 3 modele) po średnim IC
  na walidacji (ostatnie 90 dni okna, też z purgingiem), refit na całym oknie, predykcja kwartału;
- koszyk: long 10 / short 10 z 50 po wyniku modelu, trzymanie 7 dni, formowanie codzienne
  (= 7 faz), koszt `fee` × obrót względem portfela tej samej fazy tydzień wcześniej;
- werdykt (drugi warunek z decyzji użytkownika): POZYTYWNY, gdy t_neff tygodniowego zwrotu netto
  (średnia faz) > 1,96 ORAZ dolny kraniec CI 95 % średniego dziennego rank IC > 0.
Obok ML ten sam werdykt dla przyrządu prostego: ranking wprost po nośniku `x` (bez modelu i bez
przeszukiwania) — punkt odniesienia krzywej mocy. Konfiguracja ZAMROŻONA w
`runs/2026-09-25_au2-kroki-1-2/README.md`.

    PYTHONUTF8=1 py -m backtest.run_au2_ml [--szybko]
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from backtest.carry_hedged import summarize_pnl
from backtest.checkpoint_lib import load_config
from backtest.rebalance_premium import load_universe
from backtest.run_au2_szerokosc import ar1_signal, daily_rank_ic, feasible_members, member_mask
from backtest.xs_momentum import daily_funding_panel

FULL = "data/raw/universe_full"
OI_PANEL = "data/raw/oi_panel/oi_daily.parquet"
START, END = "2021-02-01", "2026-07-01"
TEST_START = "2022-04-01"
TOP_N, LEG, HOLD = 50, 10, 7
TRAIN_DAYS, VAL_DAYS, PURGE, EMBARGO = 365, 90, 7, 7
CARRIER_HALF_LIFE = 28
FEATURES = ["r7", "r28", "r90", "vol30", "turn30", "dturn", "fund7", "doi7", "beta90", "dist90"]
FEATURE_SETS = {
    "S1_all": FEATURES,
    "S2_price": ["r7", "r28", "r90", "dist90"],
    "S3_risk": ["vol30", "beta90"],
    "S4_liquidity": ["turn30", "dturn"],
    "S5_positioning": ["fund7", "doi7"],
    "S6_price_risk": ["r7", "r28", "r90", "dist90", "vol30", "beta90"],
    "S7_price_liq_pos": ["r7", "r28", "r90", "dist90", "turn30", "dturn", "fund7", "doi7"],
    "S8_no_beta_dist": ["r7", "r28", "r90", "vol30", "turn30", "dturn", "fund7", "doi7"],
}
MODELS = ("ridge", "xgb_reg", "xgb_rank")
STRENGTHS = (5, 10, 15, 20, 30)  # %/rok netto wyroczni
S_NEG, S_POS = 40, 20
RIDGE_ALPHA = 1.0
XGB_PARAMS = {
    "n_estimators": 100,
    "max_depth": 3,
    "eta": 0.05,
    "subsample": 0.8,
    "nthread": 1,
    "seed": 0,
}
Z95 = 1.959964
SEP = "=" * 104


# ------------------------------------------------------------------ cechy (dane ≤ t)


def build_features(
    close: pd.DataFrame, qvol: pd.DataFrame, funding: pd.DataFrame, oi: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Lista A: 10 cech per dzień × symbol, wyłącznie z okien kończących się na t (trailing)."""
    ret = close.pct_change(fill_method=None)
    btc = ret["BTCUSDT"]
    var_b = btc.rolling(90, min_periods=60).var()
    cov = ret.rolling(90, min_periods=60).cov(btc)
    fund = funding.reindex(index=close.index, columns=close.columns)
    oi_w = oi.reindex(index=close.index, columns=close.columns)
    return {
        "r7": close / close.shift(7) - 1.0,
        "r28": close / close.shift(28) - 1.0,
        "r90": close / close.shift(90) - 1.0,
        "vol30": ret.rolling(30, min_periods=20).std(),
        "turn30": np.log(qvol.rolling(30, min_periods=20).mean()),
        "dturn": np.log(
            qvol.rolling(7, min_periods=5).mean() / qvol.rolling(30, min_periods=20).mean()
        ),
        "fund7": fund.rolling(7, min_periods=5).sum(),
        "doi7": np.log(oi_w / oi_w.shift(7)),
        "beta90": cov.div(var_b, axis=0),
        "dist90": close / close.rolling(90, min_periods=60).max() - 1.0,
    }


def cross_rank(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Ranga procentowa (0–1] w przekroju członków każdego wiersza; poza `valid` i NaN → NaN."""
    return pd.DataFrame(np.where(valid, x, np.nan)).rank(axis=1, pct=True).to_numpy()


def cross_z(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Z-score w przekroju członków każdego wiersza."""
    v = np.where(valid, x, np.nan)
    mu = np.nanmean(v, axis=1, keepdims=True)
    sd = np.nanstd(v, axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (v - mu) / sd


def permute_within_rows(y: np.ndarray, valid: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Permutacja wartości `y` między komórkami `valid` każdego wiersza (osobno per dzień)."""
    out = np.full_like(y, np.nan)
    for t in range(y.shape[0]):
        idx = np.flatnonzero(valid[t])
        out[t, idx] = y[t, rng.permutation(idx)]
    return out


# ------------------------------------------------------------------ modele


def fit_predict(
    model: str, xtr: np.ndarray, ytr: np.ndarray, qtr: np.ndarray, xte: np.ndarray
) -> np.ndarray:
    """Trening na (xtr, ytr) i predykcja xte. Ridge: NaN → 0,5 (środek rangi), cechy wycentrowane."""
    if model == "ridge":
        a = np.nan_to_num(xtr, nan=0.5) - 0.5
        b = ytr - ytr.mean()
        w = np.linalg.solve(a.T @ a + RIDGE_ALPHA * len(a) / 100.0 * np.eye(a.shape[1]), a.T @ b)
        return (np.nan_to_num(xte, nan=0.5) - 0.5) @ w
    import xgboost as xgb

    params = {**XGB_PARAMS, "objective": "reg:squarederror"}
    if model == "xgb_rank":
        params["objective"] = "rank:pairwise"
        order = np.argsort(qtr, kind="stable")
        xtr, ytr, qtr = xtr[order], ytr[order], qtr[order]
    dtr = xgb.DMatrix(xtr, label=ytr)
    if model == "xgb_rank":
        dtr.set_group(np.unique(qtr, return_counts=True)[1])
    rounds = params.pop("n_estimators")
    booster = xgb.train(params, dtr, num_boost_round=rounds)
    return booster.predict(xgb.DMatrix(xte))
    order = np.argsort(qtr, kind="stable")
    _, counts = np.unique(qtr[order], return_counts=True)
    m = xgb.XGBRanker(objective="rank:pairwise", **XGB_PARAMS)
    m.fit(xtr[order], ytr[order], group=counts)
    return m.predict(xte)


# ------------------------------------------------------------------ koszyk i werdykt


def basket_returns(
    score: np.ndarray, fwd: np.ndarray, valid: np.ndarray, fee: float, leg: int = LEG
) -> pd.DataFrame:
    """
    Per dzień formowania: zwrot 7-dniowy koszyka 0,5·(średnia long − średnia short), obrót względem
    portfela tej samej fazy (t−7) w jednostkach kapitału (pełna wymiana obu nóg = 2,0), koszt.
    """
    n_days, n_sym = score.shape
    rows, prev = [], {}
    for t in range(n_days):
        ok = valid[t] & np.isfinite(score[t]) & np.isfinite(fwd[t])
        idx = np.flatnonzero(ok)
        if len(idx) < 2 * leg:
            rows.append((np.nan, np.nan, np.nan))
            continue
        order = idx[np.argsort(score[t, idx], kind="stable")]
        short, long_ = order[:leg], order[-leg:]
        w = np.zeros(n_sym)
        w[long_] = 0.5 / leg
        w[short] = -0.5 / leg
        gross = 0.5 * (fwd[t, long_].mean() - fwd[t, short].mean())
        before = prev.get(t % HOLD)
        turnover = np.abs(w - before).sum() if before is not None else np.abs(w).sum()
        prev[t % HOLD] = w
        rows.append((gross, turnover, fee * turnover))
    return pd.DataFrame(rows, columns=["gross", "turnover", "cost"])


def weekly_phase_average(per_formation: pd.Series) -> pd.Series:
    """Formowanie codzienne → 7 faz tygodniowych (bez nakładania) → średnia faz per tydzień."""
    x = per_formation.reset_index(drop=True)
    phase, week = x.index % HOLD, x.index // HOLD
    return x.groupby([week, phase]).first().groupby(level=0).mean()


def n_eff_guarded(x: pd.Series) -> float:
    """
    N_eff z tego samego wzoru co `effective_sample_size`, ale gdy mianownik 1 + 2·Σρ ≤ 0 (suma
    zaszumionych autokorelacji < −0,5) → N_eff = n (bez korekty), zamiast ujemnego N_eff, które
    kanoniczny `summarize_pnl` przycina do 1 (błąd wykryty w AU2 krokach 1–2).
    """
    x = x.dropna()
    n = len(x)
    rho = np.nansum([x.autocorr(k) for k in range(1, 51)])
    den = 1.0 + 2.0 * rho
    return float(n) if den <= 0 else float(max(1.0, min(n / den, n)))


def _t_guarded(x: pd.Series) -> tuple[float, float]:
    x = x.dropna()
    se = x.std(ddof=1) / np.sqrt(n_eff_guarded(x))
    return float(x.mean() / se), float(x.mean() - Z95 * se)


def verdict(bask: pd.DataFrame, ic: np.ndarray) -> dict:
    """
    Werdykt dwuwarunkowy: t_neff tygodniowego zwrotu netto > 1,96 ORAZ ci_low(średnie IC) > 0.
    `positive` — kanoniczny `summarize_pnl` (pre-rejestracja); `positive_fix` — z `n_eff_guarded`.
    """
    net = weekly_phase_average(bask["gross"] - bask["cost"])
    w = summarize_pnl(net, periods_per_year=52, capital_per_notional=1.0)
    s = summarize_pnl(pd.Series(ic), periods_per_year=365, capital_per_notional=1.0)
    t_fix, _ = _t_guarded(net)
    _, ic_lo_fix = _t_guarded(pd.Series(ic))
    return {
        "net_annual": 52 * w["mean"],
        "t_neff": w["t_neff"],
        "ic_mean": s["mean"],
        "ic_ci_low": s["mean"] - Z95 * s["se_neff"],
        "positive": bool(w["t_neff"] > Z95 and s["mean"] - Z95 * s["se_neff"] > 0),
        "t_fix": t_fix,
        "ic_ci_low_fix": ic_lo_fix,
        "positive_fix": bool(t_fix > Z95 and ic_lo_fix > 0),
    }


# ------------------------------------------------------------------ dane i jeden przebieg

_DATA: dict = {}


def load_data() -> dict:
    """Panel top-50 na dniach 2021-02-01 → END−7: cechy (rangi), zwrot 7 dni, maska członków."""
    if _DATA:
        return _DATA
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    close, qvol = load_universe(FULL)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    close, qvol = (
        close[(close.index >= lo) & (close.index < end)],
        qvol[(qvol.index >= lo) & (qvol.index < end)],
    )
    funding = daily_funding_panel(FULL)
    oi_raw = pd.read_parquet(OI_PANEL)
    oi = oi_raw.pivot_table(
        index=pd.to_datetime(oi_raw["date"], utc=True), columns="symbol", values="oi_value"
    )
    feats = build_features(close, qvol, funding, oi)
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    members, _ = feasible_members(qvol, months, TOP_N)
    fwd = close.shift(-HOLD) / close - 1.0
    days = close.index[
        (close.index >= pd.Timestamp(START, tz="UTC"))
        & (close.index < end - pd.Timedelta(days=HOLD))
    ]
    valid = (
        (member_mask(close.index, close.columns, members) & fwd.notna() & close.notna())
        .loc[days]
        .to_numpy()
    )
    ranks = {k: cross_rank(v.loc[days].to_numpy(), valid) for k, v in feats.items()}
    coverage = {k: float(np.isfinite(ranks[k])[valid].mean()) for k in FEATURES}
    _DATA.update(
        fee=fee,
        days=days,
        valid=valid,
        fwd=fwd.loc[days].to_numpy(),
        ranks=ranks,
        coverage=coverage,
        test_start=int(np.searchsorted(days, pd.Timestamp(TEST_START, tz="UTC"))),
    )
    return _DATA


def quarters(days: pd.DatetimeIndex, test_start: int) -> list[tuple[int, int]]:
    """Kolejne kwartały kalendarzowe od `test_start` (indeksy dni: [a, b))."""
    q = days[test_start:].tz_localize(None).to_period("Q")
    out, a = [], test_start
    for i in range(test_start + 1, len(days) + 1):
        if i == len(days) or q[i - test_start] != q[i - test_start - 1]:
            out.append((a, i))
            a = i
    return out


def _rows(t0: int, t1: int, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d, s = np.nonzero(valid[t0:t1])
    return d + t0, s


def run_one(arm: str, strength: float, seed: int, budget: bool = True) -> dict:
    """Jeden świat: permutacja celu (+ wstrzyknięcie), pełny walk-forward z przeszukiwaniem."""
    D = load_data()
    rng = np.random.default_rng(seed)
    valid, fwd_real = D["valid"], D["fwd"]
    carrier = cross_rank(ar1_signal(fwd_real.shape, CARRIER_HALF_LIFE, rng), valid)
    z = cross_z(carrier, valid)
    y = permute_within_rows(fwd_real, valid, rng)
    test_idx = np.arange(D["test_start"], len(D["days"]))
    oracle = basket_returns(
        np.where(np.arange(len(y))[:, None] >= D["test_start"], z, np.nan), y, valid, D["fee"]
    )
    a = 0.0
    if arm == "pos":
        spread = basket_returns(
            np.where(np.arange(len(y))[:, None] >= D["test_start"], z, np.nan), z, valid, 0.0
        )
        s_mean = spread["gross"].iloc[test_idx].mean()
        c_mean = oracle["cost"].iloc[test_idx].mean()
        a = (strength / 100.0 / 52.0 + c_mean) / s_mean
        y = y + a * np.nan_to_num(z)
        y[~valid] = np.nan
    target = cross_rank(y, valid)
    feats = {**D["ranks"], "x": carrier}
    configs = (
        [(fs, m) for fs in FEATURE_SETS for m in MODELS] if budget else [("S1_all", "xgb_reg")]
    )
    score = np.full_like(y, np.nan)
    chosen = []
    for q0, q1 in quarters(D["days"], D["test_start"]):
        tr0, tr1 = max(0, q0 - PURGE - EMBARGO - TRAIN_DAYS), q0 - PURGE - EMBARGO
        va0 = tr1 - VAL_DAYS
        best, best_ic = configs[0], -np.inf
        if len(configs) > 1:
            d_in, s_in = _rows(tr0, va0 - PURGE, valid)
            d_va, s_va = _rows(va0, tr1, valid)
            for fs, m in configs:
                cols = FEATURE_SETS[fs] + ["x"]
                xin = np.column_stack([feats[c][d_in, s_in] for c in cols])
                xva = np.column_stack([feats[c][d_va, s_va] for c in cols])
                p = np.full_like(y, np.nan)
                p[d_va, s_va] = fit_predict(m, xin, target[d_in, s_in], d_in, xva)
                ic = np.nanmean(daily_rank_ic(p[va0:tr1], y[va0:tr1], valid[va0:tr1]))
                if ic > best_ic:
                    best, best_ic = (fs, m), ic
        fs, m = best
        cols = FEATURE_SETS[fs] + ["x"]
        d_tr, s_tr = _rows(tr0, tr1, valid)
        d_te, s_te = _rows(q0, q1, valid)
        xtr = np.column_stack([feats[c][d_tr, s_tr] for c in cols])
        xte = np.column_stack([feats[c][d_te, s_te] for c in cols])
        score[d_te, s_te] = fit_predict(m, xtr, target[d_tr, s_tr], d_tr, xte)
        chosen.append(f"{fs}/{m}")
    ic_ml = daily_rank_ic(score[test_idx], y[test_idx], valid[test_idx])
    ml = verdict(basket_returns(score, y, valid, D["fee"]).iloc[test_idx], ic_ml)
    simple_score = np.where(np.arange(len(y))[:, None] >= D["test_start"], carrier, np.nan)
    ic_s = daily_rank_ic(simple_score[test_idx], y[test_idx], valid[test_idx])
    simple = verdict(basket_returns(simple_score, y, valid, D["fee"]).iloc[test_idx], ic_s)
    return {
        "arm": arm,
        "strength": strength,
        "seed": seed,
        "a": a,
        "ml": ml,
        "simple": simple,
        "chosen": chosen,
    }


def _job(args):
    return run_one(*args)


def main(argv: list[str]) -> None:
    quick = "--szybko" in argv
    t0 = time.time()
    D = load_data()
    print(SEP)
    print(
        "AU2 kroki 1–2 — przyrząd przekrojowy z ML: ramię negatywne (permutacja) i pozytywne (siatka sił)"
    )
    print(SEP)
    print(
        f"  dni {len(D['days'])} ({D['days'][0].date()} → {D['days'][-1].date()}), test od {D['days'][D['test_start']].date()}, "
        f"kwartałów {len(quarters(D['days'], D['test_start']))}, par/dzień mediana {np.median(D['valid'].sum(1)):.0f}, koszt {100 * D['fee']:.3f} % × obrót"
    )
    print(
        "  pokrycie cech (udział komórek członków z wartością): "
        + ", ".join(f"{k} {100 * v:.0f}%" for k, v in D["coverage"].items())
    )
    s_neg, s_pos = (4, 2) if quick else (S_NEG, S_POS)
    jobs = [("neg", 0.0, 1000 + i) for i in range(s_neg)]
    jobs += [("pos", float(s), 2000 + 100 * s + i) for s in STRENGTHS for i in range(s_pos)]
    workers = max(1, min(len(jobs), (os.cpu_count() or 2) - 8))  # zapas dla innych procesów serwera
    with ProcessPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(_job, jobs))
    if not quick:  # surowe wyniki na dysk przed jakimkolwiek wydrukiem
        pd.to_pickle(res, "runs/2026-09-25_au2-kroki-1-2/przebiegi_surowe.pkl")
    report(res, workers, t0, quick)


def report(res: list[dict], workers: int, t0: float, quick: bool = False) -> None:
    rows = []
    for r in res:
        for inst in ("ml", "simple"):
            v = r[inst]
            rows.append(
                {
                    "arm": r["arm"],
                    "strength": r["strength"],
                    "seed": r["seed"],
                    "instrument": inst,
                    **{
                        k: v[k]
                        for k in (
                            "net_annual",
                            "t_neff",
                            "ic_mean",
                            "ic_ci_low",
                            "positive",
                            "t_fix",
                            "ic_ci_low_fix",
                            "positive_fix",
                        )
                    },
                }
            )
    df = pd.DataFrame(rows)
    out_dir = "runs/2026-09-25_au2-kroki-1-2"
    if not quick:
        df.to_csv(f"{out_dir}/przebiegi.csv", index=False)
    print("\n  1. Ramię negatywne (cel permutowany, pełny budżet 24 konfiguracji):")
    for inst in ("ml", "simple"):
        g = df[(df["arm"] == "neg") & (df["instrument"] == inst)]
        k, n = int(g["positive"].sum()), len(g)
        kf = int(g["positive_fix"].sum())
        print(
            f"    {inst:<6}: POZYTYWNYCH {k}/{n} ({100 * k / n:.1f}%); t_neff mediana {g['t_neff'].median():+.2f} [p5 {g['t_neff'].quantile(0.05):+.2f}; p95 {g['t_neff'].quantile(0.95):+.2f}]; "
            f"średnie IC mediana {g['ic_mean'].median():+.4f}; zwrot netto mediana {100 * g['net_annual'].median():+.1f}%/rok; "
            f"POPRAWIONE N_eff: POZYTYWNYCH {kf}/{n}, t mediana {g['t_fix'].median():+.2f}"
        )
    print("\n  2. Ramię pozytywne (moc = odsetek werdyktów POZYTYWNYCH):")
    for s in STRENGTHS:
        line = f"    wyrocznia +{s:>2}%/rok: "
        for inst in ("ml", "simple"):
            g = df[(df["arm"] == "pos") & (df["strength"] == s) & (df["instrument"] == inst)]
            line += (
                f"{inst} moc {100 * g['positive'].mean():5.1f}% / poprawiona N_eff "
                f"{100 * g['positive_fix'].mean():5.1f}% (IC mediana {g['ic_mean'].median():+.4f}, "
                f"netto mediana {100 * g['net_annual'].median():+.1f}%/rok) | "
            )
        print(line)
    picks = pd.Series([c for r in res for c in r["chosen"]]).value_counts()
    print(
        "\n  3. Wybory przeszukiwania (konfiguracja × kwartał, wszystkie przebiegi): "
        + "; ".join(f"{k} {v}" for k, v in picks.head(8).items())
    )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s, przebiegów {len(res)}, procesów {workers}")


if __name__ == "__main__":
    main(sys.argv[1:])
