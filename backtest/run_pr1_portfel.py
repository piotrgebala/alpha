"""
run_pr1_portfel.py — runda PR1 (opisowo, 0 wariantów): reguły portfela nóg dziennika pod szczebel 4
ADR-09 (mała realna kwota). Wejście: dzienne zwroty netto nóg przy k = 1 z KR1 (TS1 trend, X1 średnia
7 faz, CP1 premia Coinbase; wspólne okno). Reguły:
- R0 — równy podział kapitału; R1 — dziennik (wagi ∝ 1/σ, cel 20 %/rok, sufit 2, kowariancja EWMA
  com 45, krok 7 dni, rozbieg 60) z `sizing.apply_rules`, bez zmian;
- ERC — równy wkład każdej nogi do wariancji portfela (uwzględnia korelacje), ta sama skala,
  sufit, krok i rozbieg. Dla 2 nóg ERC ≡ 1/σ (tożsamość); różnica pojawia się od 3 nóg.
Miary ryzyka na 100 % kapitału strategii: zmienność, CAGR, max obsunięcie, najgorszy dzień / tydzień /
miesiąc, ES 95 % tygodniowy (średnia z 5 % najgorszych tygodni), ES 99 % dzienny; przełożenie na %
całego kapitału przy depozycie 5 % (ADR-09) przez medianowy udział depozytu (trend 2×, CP1 3×, X1 1×).
Konfiguracja ZAMROŻONA w `runs/2026-09-25_pr1-portfel/README.md`.

    PYTHONUTF8=1 py -m backtest.run_pr1_portfel
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from backtest.run_kr1_korelacje import legs
from backtest.sizing import DAYS_PER_YEAR, _ewma_cov, apply_rules, summary

LEVERAGE = {"TS1": 2.0, "CP1": 3.0, "X1": 1.0}  # dźwignie nóg z dziennika (SZ1, poprawka 3)
MARGIN_SHARE = 0.05  # ADR-09 szczebel 4: najwyżej 5 % kapitału jako depozyt
SETS = (["TS1", "CP1"], ["TS1", "CP1", "X1"])
SEP = "=" * 104


def erc_weights(cov: np.ndarray) -> np.ndarray:
    """Wagi (suma 1, ≥ 0) o równym wkładzie do wariancji portfela: w_i·(Σw)_i = const."""
    n = len(cov)
    sig = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    w0 = (1.0 / sig) / (1.0 / sig).sum()
    if n == 1:
        return np.array([1.0])

    def loss(w: np.ndarray) -> float:
        rc = w * (cov @ w)
        return float(((rc[:, None] - rc[None, :]) ** 2).sum())

    res = minimize(
        loss,
        w0,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
        options={"ftol": 1e-16, "maxiter": 1000},
    )
    if not res.success:  # reporter neutralny: brak zbieżności = błąd, nie cicha podmiana wag
        raise RuntimeError(f"ERC: SLSQP nie zbiegł ({res.message})")
    w = np.clip(res.x, 0.0, None)
    return w / w.sum()


def apply_erc(
    returns: pd.DataFrame,
    target_vol: float = 0.20,
    cap: float = 2.0,
    com: float = 45.0,
    warmup: int = 60,
    step: int = 7,
) -> pd.DataFrame:
    """Jak `sizing.apply_rules(..., "R1")`, ale wagi ERC zamiast 1/σ; mnożniki z danych sprzed dnia."""
    r = returns.fillna(0.0)
    n, s = r.shape
    k = np.full(s, 1.0 / s)
    rows = []
    for i in range(n):
        if i % step == 0:
            if i >= warmup:
                cov = _ewma_cov(r.iloc[:i], com)
                w = erc_weights(cov)
                pvol = float(np.sqrt(w @ cov @ w) * np.sqrt(DAYS_PER_YEAR))
                k = np.minimum(cap, w * target_vol / pvol) if pvol > 0 else np.zeros(s)
            else:
                k = np.full(s, 1.0 / s)
        ret = float(k @ r.iloc[i].to_numpy())
        rows.append((r.index[i], ret, *k))
    return pd.DataFrame(rows, columns=["date", "ret", *[f"k_{c}" for c in r.columns]])


def risk_metrics(ret: pd.Series) -> dict:
    """Miary ryzyka dziennego szeregu zwrotów (na 100 % kapitału strategii)."""
    x = ret.astype(float)
    week = x.resample("W-FRI").sum()
    q_w, q_d = week.quantile(0.05), x.quantile(0.01)
    out = summary(x)
    out.update(
        worst_day=float(x.min()),
        worst_week=float(week.min()),
        es95_week=float(week[week <= q_w].mean()),
        es99_day=float(x[x <= q_d].mean()),
        n_weeks=int(len(week)),
    )
    return out


def margin_share(k: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Depozyt jako udział kapitału strategii per dzień: Σ_s k_s / dźwignia_s."""
    return sum(k[f"k_{c}"] / LEVERAGE[c] for c in cols)


def _fmt(m: dict) -> str:
    return (
        f"CAGR {100 * m['cagr']:+6.1f}% | zmienność {100 * m['vol']:5.1f}% | max DD {100 * m['max_dd']:5.1f}% | "
        f"najg. dzień {100 * m['worst_day']:6.1f}% | tydzień {100 * m['worst_week']:6.1f}% | miesiąc {100 * m['worst_month']:6.1f}% | "
        f"ES95 tyg. {100 * m['es95_week']:6.1f}% | ES99 dz. {100 * m['es99_day']:6.1f}%"
    )


def main() -> None:
    lg = legs()
    print(SEP)
    print(
        "PR1 — reguły portfela nóg dziennika (R0 równo / R1 = dziennik 1/σ / ERC z korelacjami); opisowo"
    )
    print(SEP)
    print(
        f"  wspólne dni {len(lg)} ({lg.index.min().date()} → {lg.index.max().date()}); cel 20 %/rok, sufit k ≤ 2, EWMA com 45, krok 7, rozbieg 60"
    )
    print("\n  Nogi osobno (k = 1):")
    for c in lg:
        print(f"    {c:<4} {_fmt(risk_metrics(lg[c]))}")
    for cols in SETS:
        name = "+".join(cols)
        print(f"\n  Portfel {name}:")
        r0 = apply_rules(lg[cols], "R0").set_index("date")
        r1 = apply_rules(lg[cols], "R1").set_index("date")
        er = apply_erc(lg[cols]).set_index("date")
        for label, df in (("R0 równo", r0), ("R1 dziennik (1/σ)", r1), ("ERC (korelacje)", er)):
            m = risk_metrics(df["ret"])
            print(f"    {label:<19} {_fmt(m)}")
        kcols = [f"k_{c}" for c in cols]
        diff = float((r1[kcols] - er[kcols]).abs().to_numpy().max())
        print(
            f"    |k R1 − k ERC| max: {diff:.4f}  (2 nogi → tożsamość; 3 nogi → różnica z korelacji)"
        )
        for label, df in (("R1", r1), ("ERC", er)):
            med = ", ".join(
                f"{c} {df[f'k_{c}'].median():.2f} [{df[f'k_{c}'].quantile(0.1):.2f}; {df[f'k_{c}'].quantile(0.9):.2f}]"
                for c in cols
            )
            ms = margin_share(df, cols)
            print(
                f"    mnożniki {label:<3} mediana [p10; p90]: {med}; depozyt/kapitał mediana {100 * ms.median():.0f}% [p10 {100 * ms.quantile(0.1):.0f}; p90 {100 * ms.quantile(0.9):.0f}]"
            )
        m1 = risk_metrics(r1["ret"])
        ms_med = float(margin_share(r1, cols).median())
        scale = MARGIN_SHARE / ms_med  # kapitał strategii jako udział całego kapitału
        print(
            f"    ADR-09 (R1): depozyt {100 * MARGIN_SHARE:.0f}% całego kapitału → kapitał strategii ≈ {100 * scale:.0f}% całego; "
            f"w % CAŁEGO kapitału: max DD {100 * m1['max_dd'] * scale:.1f}%, najg. tydzień {100 * m1['worst_week'] * scale:.1f}%, "
            f"ES95 tyg. {100 * m1['es95_week'] * scale:.1f}%, CAGR {100 * m1['cagr'] * scale:+.1f} pkt/rok"
        )
    print(SEP)


if __name__ == "__main__":
    main()
