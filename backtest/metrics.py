"""
metrics.py

Commit 6 — Checkpoint go/no-go (IMPLEMENTATION_PLAN.md, docs/rag/03_ryzyko_i_sizing.md).
Sharpe po kosztach per fold, klasyfikacja GO/WARUNKOWY/NO-GO, rozbicie per reżim rynkowy.
`backtest.engine.run_backtest` celowo NIE liczy Sharpe'a (patrz docstring tego modułu) —
to jawnie zadanie C6.1-C6.4, zaimplementowane tutaj jako czyste, testowalne funkcje
operujące na `trades`/`folds_summary` zwróconych przez `run_backtest`.

METODOLOGIA SHARPE (ustalona z użytkownikiem, brak w docs/rag — trzeba było doprecyzować):
- risk-free rate = 0.
- Zwrot per trade = net_pnl / equity_before (NIE equity curve resamplowana kalendarzowo) —
  sygnały są rzadkie/nierównomierne w czasie (regime-gated), więc zwrot per-trade jest
  właściwą jednostką obserwacji, nie dzienna/godzinowa próbka equity.
- Wiersze z kill_switch_active=True są WYKLUCZONE z liczenia zwrotów — to nie są realne
  transakcje (position_size=0.0, equity_before==equity_after z definicji).
- Annualizacja: sqrt(trades_per_year), gdzie trades_per_year jest szacowane OSOBNO per
  fold z częstości transakcji w TYM foldzie: (n_trades / test_window_days) * 365.25.
  test_window_days pochodzi z folds_summary[i]["test_start"/"test_end"] tego foldu
  (nie globalna stała) — foldy przy granicy danych mogą być krótsze.
- Fold z <2 transakcjami lub zerową wariancją zwrotów -> Sharpe niedefiniowalny (NaN),
  wykluczony z mianownika w classify_checkpoint (raportowany osobno jako "insufficient data").

KRYTERIA KLASYFIKACJI (docs/rag/03_ryzyko_i_sizing.md, tabela GO/WARUNKOWY/NO-GO) —
progi metodologiczne, NIE parametry modelu/tradingu, więc świadomie NIE w
config/settings.yaml (analogicznie do MIN_TRAIN_ROWS w backtest/engine.py):
    GO:        >60% foldów (z policzalnym Sharpe) ma Sharpe > 0.5
    NO-GO:     >50% foldów (z policzalnym Sharpe) ma Sharpe <= 0 (większość)
    WARUNKOWY: wszystko pomiędzy (w tym niestabilny/mieszany znak między foldami)
Konstrukcyjnie rozłączne: >60% foldów z Sharpe>0.5 wyklucza >50% foldów z Sharpe<=0.

C6.4 (rozbicie per reżim rynkowy): interpretacja jako trend vs range (kolumna `regime`
w trades/folds_summary), NIE kalendarzowa — realny zakres danych (2025-07 -> 2026-07)
nie sięga 2023, więc dosłowna treść TASKS.md ("2023 vs 2024-25") nie pasuje do
faktycznie dostępnych danych. `summarize_by_regime` po prostu woła classify_checkpoint
osobno na podzbiorze fold_metrics dla każdego reżimu.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from agents.labeling import effective_sample_size

DAYS_PER_YEAR = 365.25

# Commit 2.9 (Z3): minimalna liczba transakcji, przy której liczenie N_eff (autokorelacja
# zwrotów) ma jakikolwiek sens — poniżej tego progu estymator autokorelacji jest czystym
# szumem, więc raportujemy NaN zamiast liczby udającej informację. Próg metodologiczny
# raportowania, NIE parametr strategii — świadomie poza config/settings.yaml (jak
# MIN_TRAIN_ROWS w backtest/engine.py i progi klasyfikacji niżej).
MIN_TRADES_FOR_N_EFF = 10

# Commit 2.11: minimalna liczba transakcji, przy której raportujemy z-stat i przedział
# ufności trafności kierunku. Poniżej tego progu CI jest szersze niż cały sensowny zakres
# p (aproksymacja normalna dwumianu zawodzi przy n*p < 5), więc liczba udawałaby precyzję,
# której nie ma. Sama `hit_rate` jest raportowana zawsze — to surowy ułamek, nie estymator
# z niepewnością. Próg metodologiczny raportowania, NIE parametr strategii.
MIN_TRADES_FOR_HIT_RATE_CI = 20

# Progi klasyfikacji checkpointu — docs/rag/03_ryzyko_i_sizing.md, tabela GO/WARUNKOWY/NO-GO.
SHARPE_THRESHOLD = 0.5
GO_FRACTION = 0.6
NO_GO_FRACTION = 0.5


def compute_trade_returns(trades: pd.DataFrame) -> pd.Series:
    """
    Zwrot per trade = net_pnl / equity_before. Wyklucza wiersze kill_switch_active
    (nie są realnymi transakcjami — patrz docstring modułu).

    Zachowuje oryginalny index `trades` (po odfiltrowaniu kill-switcha), żeby dało się
    łatwo dociąć per-fold maską boolean przed wywołaniem tej funkcji.
    """
    real_trades = trades.loc[~trades["kill_switch_active"]]
    return real_trades["net_pnl"] / real_trades["equity_before"]


def compute_sharpe_ratio(
    returns: pd.Series, periods_per_year: float, risk_free_rate: float = 0.0
) -> float:
    """
    Annualizowany Sharpe: (mean(returns) - risk_free_rate) / std(returns) * sqrt(periods_per_year).

    Zwraca NaN, gdy Sharpe jest niedefiniowalny: <2 obserwacje albo zerowa wariancja
    (dzielenie przez zero) — celowo NIE +/-inf, żeby dało się jednoznacznie odróżnić
    "brak wystarczających danych" od "policzalny, ale skrajny" wynik.
    """
    if len(returns) < 2:
        return float("nan")
    std = returns.std(ddof=1)
    if std == 0 or pd.isna(std):
        return float("nan")
    mean_excess = returns.mean() - risk_free_rate
    return float((mean_excess / std) * np.sqrt(periods_per_year))


def compute_fold_metrics(
    trades: pd.DataFrame, folds_summary: list[dict]
) -> pd.DataFrame:
    """
    Per-fold (regime, fold_idx) Sharpe po kosztach — C6.1.

    Iteruje po folds_summary (a nie po grupach w trades), żeby foldy bez ŻADNYCH
    transakcji (skipped=True, albo fold_idx=None dla całkowicie pustego reżimu —
    patrz backtest/engine.py._collect_candidate_signals) też trafiły do wyniku z
    n_trades=0/sharpe=NaN, zamiast po prostu zniknąć z tabeli.

    Returns:
        DataFrame: regime, fold_idx, test_start, test_end, n_trades, mean_return,
        std_return, sharpe, skip_reason (passthrough z folds_summary, informacyjnie).
    """
    rows: list[dict] = []
    for fold in folds_summary:
        regime = fold["regime"]
        fold_idx = fold["fold_idx"]
        test_start = fold["test_start"]
        test_end = fold["test_end"]

        if fold_idx is None or test_start is None or test_end is None:
            rows.append(
                {
                    "regime": regime,
                    "fold_idx": fold_idx,
                    "test_start": test_start,
                    "test_end": test_end,
                    "n_trades": 0,
                    "mean_return": float("nan"),
                    "std_return": float("nan"),
                    "sharpe": float("nan"),
                    "skip_reason": fold.get("skip_reason"),
                }
            )
            continue

        fold_mask = (trades["regime"] == regime) & (trades["fold_idx"] == fold_idx)
        fold_returns = compute_trade_returns(trades.loc[fold_mask])
        n_trades = len(fold_returns)

        test_window_days = (test_end - test_start).total_seconds() / 86400.0
        if n_trades < 2 or test_window_days <= 0:
            sharpe = float("nan")
        else:
            trades_per_year = (n_trades / test_window_days) * DAYS_PER_YEAR
            sharpe = compute_sharpe_ratio(fold_returns, trades_per_year)

        rows.append(
            {
                "regime": regime,
                "fold_idx": fold_idx,
                "test_start": test_start,
                "test_end": test_end,
                "n_trades": n_trades,
                "mean_return": fold_returns.mean() if n_trades > 0 else float("nan"),
                "std_return": (
                    fold_returns.std(ddof=1) if n_trades > 1 else float("nan")
                ),
                "sharpe": sharpe,
                "t_stat": compute_t_stat(fold_returns),
                "skip_reason": fold.get("skip_reason"),
            }
        )

    return pd.DataFrame(rows)


def compute_t_stat(returns: pd.Series) -> float:
    """
    Commit 2.9 (Z2): zwykła t-statystyka średniego zwrotu per trade wobec zera:

        t = mean(returns) / (std(returns) / sqrt(n))

    BEZ annualizacji — w odróżnieniu od `compute_sharpe_ratio`, gdzie mnożnik
    sqrt(trades_per_year) przy n=30-40 transakcji w foldzie nadmuchuje wartości do
    rzędów ±20-60, statystycznie bezsensownych. t-stat mówi wprost: "o ile odchyleń
    standardowych ŚREDNIEJ wynik różni się od zera przy TEJ liczbie obserwacji" —
    |t| < ~2 to wynik nieodróżnialny od szumu niezależnie od znaku Sharpe'a.

    UWAGA: to nadal zakłada niezależność obserwacji — przy autokorelacji zwrotów
    realna informacja jest mniejsza (patrz N_eff w `summarize_pooled_by_regime`).
    NaN dla n < 2 albo zerowej wariancji (spójnie z compute_sharpe_ratio).
    """
    n = len(returns)
    if n < 2:
        return float("nan")
    std = returns.std(ddof=1)
    if std == 0 or pd.isna(std):
        return float("nan")
    return float(returns.mean() / (std / np.sqrt(n)))


def summarize_pooled_by_regime(trades: pd.DataFrame) -> pd.DataFrame:
    """
    Commit 2.9 (Z2+Z3): DIAGNOSTYKA zbiorcza per regime — wszystkie realne transakcje
    reżimu POŁĄCZONE między foldami w jeden strumień zwrotów, zamiast średniej z
    per-foldowych Sharpe'ów liczonych na 30-40 obserwacjach każdy.

    Po co, skoro jest classify_checkpoint: per-fold Sharpe przy tak małych n jest
    zdominowany przez szum estymacji std; pooling podnosi n do setek/tysięcy i
    pozwala uczciwie zapytać "czy średni zwrot per trade w tym reżimie różni się
    od zera". To NIE zastępuje klasyfikacji checkpointu (kryteria GO/WARUNKOWY/NO-GO
    z docs/rag/03 pozostają bez zmian) — uzupełnia ją o miary istotności.

    Zastrzeżenie metodologiczne (jawne): pooling łączy transakcje generowane przez
    RÓŻNE modele (każdy fold trenuje własny) — opisuje więc strumień wyników CAŁEGO
    pipeline'u walk-forward, nie pojedynczego modelu. Dokładnie tym strumieniem
    handlowałby system w praktyce, więc to właściwa jednostka opisu strategii.

    Kolumny wyniku, per regime:
        n_trades        - liczba realnych transakcji (bez kill_switch_active)
        mean_return     - średni zwrot per trade
        std_return      - odch. std. zwrotu per trade
        sharpe_per_trade- mean/std, BEZ annualizacji (porównywalne między reżimami
                          o różnej częstości transakcji)
        t_stat          - mean / (std/sqrt(n)) — istotność przy założeniu niezależności
        n_eff           - efektywna liczba niezależnych obserwacji (autokorelacja
                          zwrotów, agents.labeling.effective_sample_size, C4.4 —
                          wpięta do raportu po raz pierwszy w Commicie 2.9); NaN gdy
                          n < MIN_TRADES_FOR_N_EFF albo estymator zdegenerowany
        t_stat_neff     - t-stat przeskalowany do N_eff: mean / (std/sqrt(n_eff)) —
                          konserwatywna istotność uwzględniająca autokorelację
    """
    rows: list[dict] = []
    for regime, group in trades.groupby("regime"):
        returns = compute_trade_returns(group)
        n = len(returns)
        mean = float(returns.mean()) if n > 0 else float("nan")
        std = float(returns.std(ddof=1)) if n > 1 else float("nan")
        sharpe_per_trade = mean / std if n > 1 and std > 0 else float("nan")
        t_stat = compute_t_stat(returns)

        n_eff = float("nan")
        t_stat_neff = float("nan")
        if n >= MIN_TRADES_FOR_N_EFF:
            ess = effective_sample_size(returns.reset_index(drop=True))
            candidate_n_eff = ess["n_eff"]
            # Estymator N_eff = n/(1+2*sum(rho)) potrafi się zdegenerować: sum(rho)
            # <= -0.5 daje wartość ujemną/ogromną (raportuj NaN), a lekko ujemna
            # suma autokorelacji (typowa dla i.i.d. szumu) daje n_eff nieznacznie
            # > n — przycinaj do n, bo "więcej informacji niż obserwacji" nie ma
            # interpretacji w roli, do której N_eff tu służy (konserwatywna korekta
            # istotności W DÓŁ przy dodatniej autokorelacji).
            if candidate_n_eff > 0:
                n_eff = float(min(candidate_n_eff, n))
                if std and std > 0 and not pd.isna(std):
                    t_stat_neff = float(mean / (std / np.sqrt(n_eff)))

        rows.append(
            {
                "regime": regime,
                "n_trades": n,
                "mean_return": mean,
                "std_return": std,
                "sharpe_per_trade": sharpe_per_trade,
                "t_stat": t_stat,
                "n_eff": n_eff,
                "t_stat_neff": t_stat_neff,
            }
        )
    return pd.DataFrame(rows)


def classify_checkpoint(
    fold_metrics: pd.DataFrame,
    sharpe_threshold: float = SHARPE_THRESHOLD,
    go_fraction: float = GO_FRACTION,
    no_go_fraction: float = NO_GO_FRACTION,
) -> dict:
    """
    Klasyfikacja GO / WARUNKOWY / NO-GO wg kryteriów z docs/rag/03 — C6.2.

    Foldy z Sharpe=NaN (insufficient data) są wykluczone z mianownika ułamków, ale
    liczone osobno w n_total_folds/n_valid_folds dla przejrzystości raportu. Gdy
    n_valid_folds == 0 (zero foldów z policzalnym Sharpe w całym przebiegu) -> WARUNKOWY
    (ani kryterium GO, ani NO-GO nie jest formalnie spełnione przy braku jakichkolwiek
    danych — to NIE jest to samo co "Sharpe <= 0", więc NO-GO byłoby nieuprawnione).
    """
    n_total_folds = len(fold_metrics)
    valid = fold_metrics.dropna(subset=["sharpe"])
    n_valid_folds = len(valid)

    if n_valid_folds == 0:
        return {
            "classification": "WARUNKOWY",
            "n_valid_folds": 0,
            "n_total_folds": n_total_folds,
            "fraction_above_threshold": float("nan"),
            "fraction_le_zero": float("nan"),
            "fraction_positive_sign": float("nan"),
            "mean_sharpe": float("nan"),
        }

    fraction_above_threshold = float((valid["sharpe"] > sharpe_threshold).mean())
    fraction_le_zero = float((valid["sharpe"] <= 0).mean())
    fraction_positive_sign = float((valid["sharpe"] > 0).mean())
    mean_sharpe = float(valid["sharpe"].mean())

    if fraction_above_threshold > go_fraction:
        classification = "GO"
    elif fraction_le_zero > no_go_fraction:
        classification = "NO-GO"
    else:
        classification = "WARUNKOWY"

    return {
        "classification": classification,
        "n_valid_folds": n_valid_folds,
        "n_total_folds": n_total_folds,
        "fraction_above_threshold": fraction_above_threshold,
        "fraction_le_zero": fraction_le_zero,
        "fraction_positive_sign": fraction_positive_sign,
        "mean_sharpe": mean_sharpe,
    }


def break_even_hit_rate(cost_fraction: float, barrier_fraction: float) -> float:
    """
    Commit 2.11 (instrumentacja edge'u): jaka trafność kierunku jest potrzebna, żeby
    wyjść na zero przy SYMETRYCZNYCH barierach ±B i koszcie round-trip C.

        p * B - (1 - p) * B = C   =>   p = 0.5 * (1 + C / B)

    Symetria barier nie jest założeniem upraszczającym, tylko właściwością pipeline'u:
    `backtest.engine._resolve_exit_price` odtwarza barierę triple-barrier (±ATR_MULTIPLIER
    * atr_14), więc wypłata transakcji jest w pełni określona przez to, czy kierunek
    zgadzał się z etykietą. Stąd cały werdykt GO/NO-GO redukuje się do nierówności
    (2p - 1) * B > C — a ta funkcja podaje jej punkt równowagi.

    Zwraca NaN dla niedodatniej bariery (brak sensownego punktu odniesienia) — celowo
    NIE +inf, spójnie z konwencją NaN w compute_sharpe_ratio/compute_t_stat.
    """
    if barrier_fraction is None or pd.isna(barrier_fraction) or barrier_fraction <= 0:
        return float("nan")
    if cost_fraction is None or pd.isna(cost_fraction):
        return float("nan")
    return float(0.5 * (1.0 + cost_fraction / barrier_fraction))


def compute_hit_rate(trades: pd.DataFrame) -> dict:
    """
    Commit 2.11: trafność kierunku PRZED kosztami — czy model w ogóle wie cokolwiek.

    "Trafienie" = `gross_pnl > 0`, czyli kierunek pozycji zgodny z etykietą (albo, dla
    wyjść po barierze pionowej, z ruchem ceny do zamknięcia). Świadomie liczone na
    `gross_pnl`, nie `net_pnl`: `net_pnl` miesza jakość sygnału z modelem kosztów, a
    właśnie ich rozdzielenie jest celem tej miary (cały werdykt C2.10 liczył się z netto,
    `gross_pnl` było zapisywane i nigdy nieczytane przez ten moduł).

    Wyklucza wiersze kill_switch_active — jak compute_trade_returns.

    Returns:
        dict: n_trades, hit_rate, z_stat (wobec H0: p=0.5), ci_low/ci_high (95% Wald).
        Wszystko NaN przy n=0; z_stat i CI NaN przy n < MIN_TRADES_FOR_HIT_RATE_CI.
    """
    real_trades = trades.loc[~trades["kill_switch_active"]]
    n = len(real_trades)
    if n == 0:
        return {
            "n_trades": 0,
            "hit_rate": float("nan"),
            "z_stat": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
        }

    hit_rate = float((real_trades["gross_pnl"] > 0).mean())
    if n < MIN_TRADES_FOR_HIT_RATE_CI:
        return {
            "n_trades": n,
            "hit_rate": hit_rate,
            "z_stat": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
        }

    # z wobec H0: p=0.5 -> se pod hipotezą zerową = sqrt(0.25/n), NIE sqrt(p(1-p)/n).
    z_stat = float((hit_rate - 0.5) / np.sqrt(0.25 / n))
    # CI Walda wokół ESTYMATY -> tu już se z obserwowanego p.
    half_width = 1.96 * np.sqrt(hit_rate * (1.0 - hit_rate) / n)
    return {
        "n_trades": n,
        "hit_rate": hit_rate,
        "z_stat": z_stat,
        "ci_low": float(hit_rate - half_width),
        "ci_high": float(hit_rate + half_width),
    }


def summarize_edge_by_regime(trades: pd.DataFrame) -> pd.DataFrame:
    """
    Commit 2.11: rozbicie nierówności GO — (2p - 1) * B > C — na człony, per reżim.

    Po co obok summarize_pooled_by_regime: tamta mówi, CZY wynik netto różni się od zera.
    Ta mówi, DLACZEGO — rozdziela jakość sygnału (p) od geometrii wypłaty (B) i modelu
    kosztów (C), więc od razu widać, który człon blokuje werdykt. Bez tego rozbicia
    "NO-GO" nie odróżnia "model nie ma pojęcia" od "model ma rację, ale koszt zjada
    barierę" — a to dwie całkiem różne diagnozy prowadzące do różnych następnych kroków.

    Kolumny per regime:
        n_trades, hit_rate, ci_low, ci_high, z_stat  - trafność kierunku (compute_hit_rate)
        barrier_pct  - średnia |exit - entry| / entry, czyli B jako ułamek ceny
        cost_pct     - średni koszt round-trip jako ułamek nominału, czyli C
        break_even_p - 0.5 * (1 + C/B), wymagana trafność (break_even_hit_rate)
        margin       - hit_rate - break_even_p; DODATNI margines to warunek konieczny
                       (nie wystarczający) dodatniej wartości oczekiwanej transakcji

    UWAGA metodologiczna: `barrier_pct` i `cost_pct` są liczone jako średnie po
    transakcjach, więc `break_even_p` z ich ilorazu to przybliżenie pierwszego rzędu
    (E[C]/E[B] != E[C/B]). Miara diagnostyczna do czytania rzędu wielkości i kierunku
    zmian między rundami — NIE wchodzi do kryteriów klasyfikacji z docs/rag/03, które
    pozostają NIEZMIENIONE.
    """
    rows: list[dict] = []
    for regime, group in trades.groupby("regime"):
        real_trades = group.loc[~group["kill_switch_active"]]
        hit = compute_hit_rate(group)

        notional = real_trades["position_size"] * real_trades["entry_price"]
        notional = notional.replace(0.0, np.nan)
        entry_price = real_trades["entry_price"].replace(0.0, np.nan)

        barrier_pct = float(
            ((real_trades["exit_price"] - real_trades["entry_price"]).abs() / entry_price).mean()
        ) if len(real_trades) else float("nan")
        cost_pct = float((real_trades["cost"] / notional).mean()) if len(real_trades) else float("nan")

        break_even_p = break_even_hit_rate(cost_pct, barrier_pct)
        margin = (
            hit["hit_rate"] - break_even_p
            if not (pd.isna(hit["hit_rate"]) or pd.isna(break_even_p))
            else float("nan")
        )

        rows.append(
            {
                "regime": regime,
                **hit,
                "barrier_pct": barrier_pct,
                "cost_pct": cost_pct,
                "break_even_p": break_even_p,
                "margin": margin,
            }
        )
    return pd.DataFrame(rows)


def summarize_by_regime(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Rozbicie klasyfikacji per reżim rynkowy (trend vs range) — C6.4. Jedna zagregowana
    liczba Sharpe po całym okresie maskuje niestabilność między reżimami (docs/rag/03) —
    ta funkcja woła classify_checkpoint OSOBNO na podzbiorze fold_metrics każdego reżimu.

    Returns:
        DataFrame: jeden wiersz per regime, kolumny = regime + klucze classify_checkpoint.
    """
    rows: list[dict] = []
    for regime, group in fold_metrics.groupby("regime"):
        result = classify_checkpoint(group)
        rows.append({"regime": regime, **result})
    return pd.DataFrame(rows)
