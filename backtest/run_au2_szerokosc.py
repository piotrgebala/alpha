"""
run_au2_szerokosc.py — runda AU2, krok 0 (kalibracja przyrządu przekrojowego, 0 wariantów hipotez):
ile niezależnych zakładów jest naprawdę w koszyku top-N i jakie najmniejsze rank IC (korelacja
rankingu sygnału z rankingiem zwrotu tygodniowego) przyrząd odróżnia od zera na 5 latach.

Bez żadnego prawdziwego sygnału — tylko zwroty i losowe sygnały:
1. szerokość efektywna: co miesiąc macierz korelacji dziennych zwrotów członków (okno 90 dni przed
   początkiem miesiąca), surowa i po odjęciu średniej przekroju (to widzi koszyk long/short);
   współczynnik uczestnictwa (Σλ)² / Σλ² = „ile niezależnych monet”;
2. szum IC: `N_SIM` losowych sygnałów AR(1) (półtrwanie 7 i 28 dni) na prawdziwych zwrotach
   7-dniowych, formowanie codziennie (= średnia 7 faz tygodniowych); rozrzut średniego IC między
   symulacjami = błąd przyrządu → najmniejsze wykrywalne IC przy mocy 80 % (dwustronnie, 5 %);
3. prawo fundamentalne: IC potrzebne na IR = IC · √(szerokość × 52).
Konfiguracja i reguła decyzji ZAMROŻONE w `runs/2026-09-25_au2-moc-przekrojowa/README.md`.

    PYTHONUTF8=1 py -m backtest.run_au2_szerokosc
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from backtest.rebalance_premium import load_universe, monthly_members

FULL = "data/raw/universe_full"
START, END = "2021-02-01", "2026-07-01"
TOP_NS = (20, 50, 100)
CORR_WINDOW = 90
MIN_COVERAGE = 0.9  # członek w macierzy korelacji, gdy ma ≥ 90 % dni okna
HOLD_DAYS = 7
HALF_LIVES = (7, 28)
N_SIM = 200
IR_TARGETS = (0.5, 0.75, 1.0)
Z95, Z80 = 1.959964, 0.841621
WEEKS_PER_YEAR = 52
SEP = "=" * 104


def participation_ratio(corr: np.ndarray) -> float:
    """(Σλ)² / Σλ² macierzy korelacji (λ < 0 z numeryki → 0): 1 = jeden czynnik, N = niezależne."""
    lam = np.clip(np.linalg.eigvalsh(corr), 0.0, None)
    return float(lam.sum() ** 2 / (lam**2).sum())


def effective_breadth(
    returns: pd.DataFrame,
    members: dict[pd.Timestamp, list[str]],
    window: int = CORR_WINDOW,
    min_coverage: float = MIN_COVERAGE,
) -> pd.DataFrame:
    """Per miesiąc: liczba członków w macierzy, średnia korelacja, uczestnictwo surowe i po odjęciu rynku."""
    rows = []
    for m, syms in sorted(members.items()):
        win = returns.loc[(returns.index >= m - pd.Timedelta(days=window)) & (returns.index < m)]
        win = win.reindex(columns=syms)
        win = win.loc[:, win.notna().mean() >= min_coverage]
        if win.shape[1] < 3:
            continue
        resid = win.sub(win.mean(axis=1), axis=0)
        c_raw, c_res = win.corr().to_numpy(), resid.corr().to_numpy()
        off = ~np.eye(len(c_raw), dtype=bool)
        rows.append(
            {
                "month": m,
                "n": win.shape[1],
                "mean_corr": float(np.nanmean(c_raw[off])),
                "pr_raw": participation_ratio(np.nan_to_num(c_raw)),
                "pr_resid": participation_ratio(np.nan_to_num(c_res)),
            }
        )
    return pd.DataFrame(rows)


def member_mask(index: pd.DatetimeIndex, columns: pd.Index, members: dict) -> pd.DataFrame:
    """Maska dzień × symbol: członek koszyka w miesiącu, do którego należy dzień (skład z początku miesiąca)."""
    mask = pd.DataFrame(False, index=index, columns=columns)
    starts = sorted(members)
    for i, m in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else index.max() + pd.Timedelta(days=1)
        rows = (index >= m) & (index < nxt)
        mask.loc[rows, mask.columns.intersection(members[m])] = True
    return mask


def daily_rank_ic(signal: np.ndarray, fwd: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Spearman per wiersz (dzień) między sygnałem a zwrotem, tylko komórki `valid`; < 4 par → NaN."""
    s = np.where(valid, signal, np.nan)
    f = np.where(valid, fwd, np.nan)
    rs = pd.DataFrame(s).rank(axis=1).to_numpy()
    rf = pd.DataFrame(f).rank(axis=1).to_numpy()
    rs = rs - np.nanmean(rs, axis=1, keepdims=True)
    rf = rf - np.nanmean(rf, axis=1, keepdims=True)
    num = np.nansum(rs * rf, axis=1)
    den = np.sqrt(np.nansum(rs**2, axis=1) * np.nansum(rf**2, axis=1))
    n = valid.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ic = num / den
    ic[n < 4] = np.nan
    return ic


def ar1_signal(shape: tuple[int, int], half_life: float, rng: np.random.Generator) -> np.ndarray:
    """Losowy sygnał AR(1) per kolumna, φ = 0,5^(1/półtrwanie); stacjonarny od pierwszego wiersza."""
    phi = 0.5 ** (1.0 / half_life)
    eps = rng.standard_normal(shape)
    out = np.empty(shape)
    out[0] = eps[0]
    k = np.sqrt(1.0 - phi**2)
    for t in range(1, shape[0]):
        out[t] = phi * out[t - 1] + k * eps[t]
    return out


def ic_noise(
    fwd: pd.DataFrame, valid: pd.DataFrame, half_life: float, n_sim: int, seed: int = 0
) -> dict:
    """Rozrzut średniego IC (codzienne formowanie) pod H0 z `n_sim` losowych sygnałów AR(1)."""
    rng = np.random.default_rng(seed)
    f, v = fwd.to_numpy(), valid.to_numpy()
    means, sds, ns = [], [], []
    for _ in range(n_sim):
        ic = daily_rank_ic(ar1_signal(f.shape, half_life, rng), f, v)
        means.append(np.nanmean(ic))
        sds.append(np.nanstd(ic, ddof=1))
    ns = v.sum(axis=1)
    return {
        "se_mean_ic": float(np.std(means, ddof=1)),
        "mean_of_means": float(np.mean(means)),
        "daily_ic_sd": float(np.median(sds)),
        "median_n": float(np.median(ns[ns >= 4])),
        "days": int((ns >= 4).sum()),
    }


def main() -> None:
    t0 = time.time()
    close, volume = load_universe(FULL)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    close = close[(close.index >= lo) & (close.index < end)]
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    returns = close.pct_change(fill_method=None)
    fwd = close.shift(-HOLD_DAYS) / close - 1.0
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    start = pd.Timestamp(START, tz="UTC")
    eval_days = close.index[
        (close.index >= start) & (close.index < end - pd.Timedelta(days=HOLD_DAYS))
    ]
    print(SEP)
    print(
        "AU2 krok 0 — szerokość efektywna i szum rank IC przyrządu przekrojowego; bez prawdziwego sygnału"
    )
    print(SEP)
    print(
        f"  uniwersum: {close.shape[1]} kontraktów, dni {close.index.min().date()} → {close.index.max().date()}; "
        f"ocena {eval_days.min().date()} → {eval_days.max().date()} ({len(eval_days)} dni formowania, trzymanie {HOLD_DAYS} dni)"
    )
    for top_n in TOP_NS:
        members = monthly_members(volume, months, top_n=top_n)
        br = effective_breadth(returns, members)
        pr_res = float(br["pr_resid"].median())
        print(
            f"\n  TOP-{top_n}: miesięcy {len(br)}, członków w macierzy mediana {br['n'].median():.0f}"
        )
        print(
            f"    średnia korelacja par: mediana {br['mean_corr'].median():.2f} [p10 {br['mean_corr'].quantile(0.1):.2f}; p90 {br['mean_corr'].quantile(0.9):.2f}]"
        )
        print(
            f"    szerokość efektywna surowa (uczestnictwo): mediana {br['pr_raw'].median():.1f} [p10 {br['pr_raw'].quantile(0.1):.1f}; p90 {br['pr_raw'].quantile(0.9):.1f}]"
        )
        print(
            f"    szerokość po odjęciu rynku (long/short):   mediana {pr_res:.1f} [p10 {br['pr_resid'].quantile(0.1):.1f}; p90 {br['pr_resid'].quantile(0.9):.1f}]"
        )
        valid = member_mask(close.index, close.columns, members) & fwd.notna() & close.notna()
        valid = valid.loc[eval_days]
        f = fwd.loc[eval_days]
        br_year = pr_res * WEEKS_PER_YEAR
        ic_ir = "; ".join(f"IR {ir:.2f} → IC {ir / np.sqrt(br_year):.3f}" for ir in IR_TARGETS)
        print(f"    prawo fundamentalne (szerokość {pr_res:.1f} × {WEEKS_PER_YEAR} tyg.): {ic_ir}")
        for hl in HALF_LIVES:
            r = ic_noise(f, valid, hl, N_SIM, seed=top_n * 100 + hl)
            mde = (Z95 + Z80) * r["se_mean_ic"]
            print(
                f"    szum IC, sygnał losowy półtrwanie {hl:>2} d: {r['days']} dni, par/dzień mediana {r['median_n']:.0f}, "
                f"sd IC dziennego {r['daily_ic_sd']:.3f}, średnia pod H0 {r['mean_of_means']:+.4f}, "
                f"se średniego IC {r['se_mean_ic']:.4f} → half-width 95% {Z95 * r['se_mean_ic']:.3f}, "
                f"najmniejsze wykrywalne IC (moc 80%) {mde:.3f}"
            )
    print(SEP)
    print(f"czas: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
