"""
ta_rules.py — klasyczna analiza techniczna jako DETERMINISTYCZNE cechy i REGUŁY kierunkowe.

Runda A2 (2026-09-23, runs/2026-09-23_a2-rodziny-at/): port funkcji ze skilla `ta-toolkit`
(scripts/ta_features.py) z zachowaniem parametrów domyślnych skilla — to one są „zapisane z góry"
(CLAUDE.md zasada 1: bez strojenia na całej historii; każdy inny zestaw parametrów = osobny
wariant w liczniku). Kontrakt jak w agents/feature_miner.py: `compute_<nazwa>(df) -> pd.Series`,
ta sama długość i indeks, WYŁĄCZNIE dane do wiersza t włącznie.

DLACZEGO SWINGI SĄ OPÓŹNIONE: szczyt w barze t jest szczytem dopiero, gdy `confirm` kolejnych
barów jest niżej. Cecha w barze t widzi tylko swingi POTWIERDZONE do t — czyli swing z bara
t − confirm. „Ostatni szczyt na wykresie" bez tego opóźnienia to przeciek o `confirm` barów;
test przecieku (agent_5_compliance/test_leakage.py, parametryzowany po TA_FEATURE_FUNCTIONS)
wykrywa go jako NaN → wartość.

Cechy NIE wchodzą do `feature_miner.FEATURE_FUNCTIONS` (produkcyjny zestaw modelu zostaje
nietknięty); są rejestrowane w sekcji `ta_rules:` pliku agents/feature_registry.yaml, a test
pilnuje zgodności kluczy. Reguły (`rule_*`) zamieniają cechy na sygnał ∈ {−1, 0, +1}: stan
(sygnał trwa, dopóki trwa warunek) albo zdarzenie (sygnał tylko w świecy zmiany).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import talib

# --- parametry domyślne skilla `ta-toolkit` (jeden zestaw, bez wariantów) --------------------
SWING_CONFIRM = 5  # bary potwierdzające ekstremum
DT_TOL_ATR = 0.5  # podwójny szczyt/dno: tolerancja poziomów w ATR
DT_BOUNCE_ATR = 2.0  # podwójny szczyt/dno: minimalne odbicie między nimi w ATR
HS_SHOULDER_TOL_ATR = 1.0  # głowa z ramionami: tolerancja ramion w ATR
HS_HEAD_MIN_ATR = 1.0  # głowa z ramionami: minimalna przewaga głowy w ATR
EMA_FAST = 10
EMA_SLOW = 30
TRENDLINE_K = 3  # liczba potwierdzonych dołków w regresji
SR_LOOKBACK = 500  # bary, z których liczą się potwierdzone poziomy
BREAKOUT_N = 20  # bary zakresu wybicia
ATR_N = 14
FIB_BAND = (0.382, 0.618)  # pasmo zniesienia (podręcznikowe poziomy Fibonacciego)
SR_NEAR_ATR = 0.5  # „przy poziomie" = w odległości ≤ 0,5·ATR (ta sama skala co DT_TOL_ATR)


def _atr(df: pd.DataFrame, n: int = ATR_N) -> pd.Series:
    atr = talib.ATR(
        df["high"].to_numpy(float),
        df["low"].to_numpy(float),
        df["close"].to_numpy(float),
        timeperiod=n,
    )
    return pd.Series(atr, index=df.index)


# ---------------------------------------------------------------------------
# Narzędzia bazowe: potwierdzone swingi
# ---------------------------------------------------------------------------


def confirmed_swings(df: pd.DataFrame, confirm: int = SWING_CONFIRM) -> tuple[pd.Series, pd.Series]:
    """
    (swing_high, swing_low): w barze t wartość = poziom swingu z bara t − confirm, JEŚLI bar
    t − confirm był ekstremum okna [t − 2·confirm, t]; inaczej NaN. „Potwierdzony w t" = bary po
    nim aż do t nie przebiły go — cecha w t nigdy nie wie o ekstremum wymagającym barów > t.
    """
    high, low = df["high"], df["low"]
    win = 2 * confirm + 1
    roll_max = high.rolling(win, min_periods=win).max()
    roll_min = low.rolling(win, min_periods=win).min()
    cand_h = high.shift(confirm)
    cand_l = low.shift(confirm)
    return cand_h.where(cand_h == roll_max), cand_l.where(cand_l == roll_min)


def _last_k_confirmed(series: pd.Series, k: int) -> pd.DataFrame:
    """Dla każdego t: k ostatnich nie-NaN wartości serii do t włącznie (kolumna 0 = najnowsza)."""
    positions = np.flatnonzero(series.notna().to_numpy())
    values = series.to_numpy()[positions]
    n = len(series)
    last = np.searchsorted(positions, np.arange(n), side="right") - 1
    cols = {}
    for i in range(k):
        idx = last - i
        col = np.full(n, np.nan)
        ok = idx >= 0
        col[ok] = values[idx[ok]]
        cols[i] = col
    return pd.DataFrame(cols, index=series.index)


def _last_k_confirmed_pos(series: pd.Series, k: int, confirm: int) -> tuple[np.ndarray, np.ndarray]:
    """Jak `_last_k_confirmed`, plus POZYCJE barów kandydatów (potwierdzenie − confirm); −1 = brak."""
    positions = np.flatnonzero(series.notna().to_numpy())
    values = series.to_numpy()[positions]
    n = len(series)
    last = np.searchsorted(positions, np.arange(n), side="right") - 1
    vals = np.full((n, k), np.nan)
    pos = np.full((n, k), -1, dtype=int)
    for i in range(k):
        idx = last - i
        ok = idx >= 0
        vals[ok, i] = values[idx[ok]]
        pos[ok, i] = positions[idx[ok]] - confirm
    return vals, pos


# ---------------------------------------------------------------------------
# Cechy (parametry = domyślne skilla)
# ---------------------------------------------------------------------------


def compute_trend_structure(df: pd.DataFrame, confirm: int = SWING_CONFIRM) -> pd.Series:
    """+1: dwa ostatnie potwierdzone szczyty rosną I dołki rosną (HH+HL); −1: LH+LL; 0 inaczej."""
    sh, sl = confirmed_swings(df, confirm)
    highs = _last_k_confirmed(sh, 2)
    lows = _last_k_confirmed(sl, 2)
    up = (highs[0] > highs[1]) & (lows[0] > lows[1])
    down = (highs[0] < highs[1]) & (lows[0] < lows[1])
    out = pd.Series(0.0, index=df.index)
    out[up] = 1.0
    out[down] = -1.0
    out[highs[1].isna() | lows[1].isna()] = np.nan
    return out.rename("trend_structure")


def compute_double_top_bottom(
    df: pd.DataFrame,
    confirm: int = SWING_CONFIRM,
    tol_atr: float = DT_TOL_ATR,
    bounce_atr: float = DT_BOUNCE_ATR,
    atr_n: int = ATR_N,
) -> pd.Series:
    """
    −1 (podwójny szczyt): dwa ostatnie potwierdzone szczyty różnią się o ≤ tol_atr·ATR, a minimum
    low MIĘDZY nimi leży ≥ bounce_atr·ATR poniżej niższego z nich. +1 (podwójne dno) symetrycznie.
    0 inaczej; NaN, dopóki nie ma dwóch potwierdzonych swingów. STAN (trwa do następnego swingu).
    """
    sh, sl = confirmed_swings(df, confirm)
    atr = _atr(df, atr_n).to_numpy()
    hv, hp = _last_k_confirmed_pos(sh, 2, confirm)
    lv, lp = _last_k_confirmed_pos(sl, 2, confirm)
    high, low = df["high"].to_numpy(float), df["low"].to_numpy(float)
    n = len(df)
    out = np.full(n, np.nan)
    for t in range(n):
        a = atr[t]
        if np.isnan(a) or a == 0:
            continue
        val = 0.0
        if hp[t, 1] >= 0 and abs(hv[t, 0] - hv[t, 1]) <= tol_atr * a:
            p1, p0 = hp[t, 1], hp[t, 0]
            if p0 - p1 > 1:
                dip = low[p1 + 1 : p0].min()
                if min(hv[t, 0], hv[t, 1]) - dip >= bounce_atr * a:
                    val = -1.0
        if lp[t, 1] >= 0 and abs(lv[t, 0] - lv[t, 1]) <= tol_atr * a:
            p1, p0 = lp[t, 1], lp[t, 0]
            if p0 - p1 > 1:
                peak = high[p1 + 1 : p0].max()
                if peak - max(lv[t, 0], lv[t, 1]) >= bounce_atr * a:
                    val = 1.0 if val == 0.0 else 0.0  # oba naraz = niejednoznaczne
        if hp[t, 1] >= 0 or lp[t, 1] >= 0:
            out[t] = val
    return pd.Series(out, index=df.index, name="double_top_bottom")


def compute_head_shoulders(
    df: pd.DataFrame,
    confirm: int = SWING_CONFIRM,
    shoulder_tol_atr: float = HS_SHOULDER_TOL_ATR,
    head_min_atr: float = HS_HEAD_MIN_ATR,
    atr_n: int = ATR_N,
) -> pd.Series:
    """
    −1 (RGR): trzy ostatnie potwierdzone szczyty [S1, H, S2]: H ≥ S1 + head_min_atr·ATR,
    H ≥ S2 + head_min_atr·ATR, |S1 − S2| ≤ shoulder_tol_atr·ATR. +1 (odwrócona) na dołkach.
    0 inaczej; NaN bez trzech swingów. STAN.
    """
    sh, sl = confirmed_swings(df, confirm)
    a = _atr(df, atr_n).to_numpy()
    hv, _ = _last_k_confirmed_pos(sh, 3, confirm)  # kolumny: 0 = S2, 1 = H, 2 = S1
    lv, _ = _last_k_confirmed_pos(sl, 3, confirm)
    with np.errstate(invalid="ignore"):
        hs = (
            (hv[:, 1] >= hv[:, 2] + head_min_atr * a)
            & (hv[:, 1] >= hv[:, 0] + head_min_atr * a)
            & (np.abs(hv[:, 0] - hv[:, 2]) <= shoulder_tol_atr * a)
        )
        ihs = (
            (lv[:, 1] <= lv[:, 2] - head_min_atr * a)
            & (lv[:, 1] <= lv[:, 0] - head_min_atr * a)
            & (np.abs(lv[:, 0] - lv[:, 2]) <= shoulder_tol_atr * a)
        )
    out = np.zeros(len(df))
    out[hs] = -1.0
    out[ihs] = 1.0
    out[np.isnan(hv[:, 2]) | np.isnan(lv[:, 2]) | np.isnan(a)] = np.nan
    return pd.Series(out, index=df.index, name="head_shoulders")


def compute_ma_state(df: pd.DataFrame, fast: int = EMA_FAST, slow: int = EMA_SLOW) -> pd.Series:
    """(EMA_fast − EMA_slow) / close — ciągły stan; znak = która średnia wyżej."""
    ef = df["close"].ewm(span=fast, adjust=False, min_periods=fast).mean()
    es = df["close"].ewm(span=slow, adjust=False, min_periods=slow).mean()
    return ((ef - es) / df["close"]).rename("ma_state")


def compute_ma_cross_age(df: pd.DataFrame, fast: int = EMA_FAST, slow: int = EMA_SLOW) -> pd.Series:
    """Liczba barów od ostatniej zmiany znaku (EMA_fast − EMA_slow); 0 = świeże przecięcie."""
    s = np.sign(compute_ma_state(df, fast, slow))
    changed = (s != s.shift(1)) & s.notna() & s.shift(1).notna()
    grp = changed.cumsum()
    age = grp.groupby(grp).cumcount().astype(float)
    age[s.isna() | s.shift(1).isna()] = np.nan
    return age.rename("ma_cross_age")


def compute_trendline_distance(
    df: pd.DataFrame, confirm: int = SWING_CONFIRM, k: int = TRENDLINE_K
) -> pd.Series:
    """
    Linia = regresja (czas, poziom) przez k ostatnich potwierdzonych DOŁKÓW; cecha =
    (close − linia(t)) / close. Ujemna = cena poniżej linii („przełamanie linii trendu").
    """
    _, sl = confirmed_swings(df, confirm)
    positions = np.flatnonzero(sl.notna().to_numpy())
    values = sl.to_numpy()[positions]
    n = len(df)
    out = np.full(n, np.nan)
    last = np.searchsorted(positions, np.arange(n), side="right") - 1
    close = df["close"].to_numpy(float)
    for t in range(n):
        j = last[t]
        if j - (k - 1) < 0:
            continue
        xs = positions[j - k + 1 : j + 1].astype(float)
        ys = values[j - k + 1 : j + 1]
        slope, intercept = np.polyfit(xs, ys, 1)
        line = slope * t + intercept
        out[t] = (close[t] - line) / close[t]
    return pd.Series(out, index=df.index, name="trendline_distance")


def _fib_impulse_frame(df: pd.DataFrame, confirm: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(start, end, up_impulse) ostatniego potwierdzonego impulsu; NaN/−1, gdy brak obu swingów."""
    sh, sl = confirmed_swings(df, confirm)
    last_h = _last_k_confirmed(sh, 1)[0].to_numpy()
    last_l = _last_k_confirmed(sl, 1)[0].to_numpy()
    n = len(df)
    pos_h = np.flatnonzero(sh.notna().to_numpy())
    pos_l = np.flatnonzero(sl.notna().to_numpy())
    ph = np.searchsorted(pos_h, np.arange(n), side="right") - 1
    pl = np.searchsorted(pos_l, np.arange(n), side="right") - 1
    th = np.where(ph >= 0, pos_h[np.clip(ph, 0, None)] if len(pos_h) else -1, -1)
    tl = np.where(pl >= 0, pos_l[np.clip(pl, 0, None)] if len(pos_l) else -1, -1)
    up = th > tl  # ostatni to szczyt → impuls wzrostowy od dołka do szczytu
    start = np.where(up, last_l, last_h)
    end = np.where(up, last_h, last_l)
    valid = (th >= 0) & (tl >= 0)
    return start, end, np.where(valid, up, np.nan)


def compute_fib_position(df: pd.DataFrame, confirm: int = SWING_CONFIRM) -> pd.Series:
    """
    Pozycja close w OSTATNIM POTWIERDZONYM impulsie: 0 = start, 1 = koniec, 0,382/0,5/0,618 =
    zniesienia, 2,0 = rozszerzenie 1:1. NaN bez obu swingów albo przy impulsie zerowym.
    """
    start, end, up = _fib_impulse_frame(df, confirm)
    rng = end - start
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = (df["close"].to_numpy(float) - start) / rng
    pos[(rng == 0) | np.isnan(rng) | np.isnan(up)] = np.nan
    return pd.Series(pos, index=df.index, name="fib_position")


def compute_fib_impulse(df: pd.DataFrame, confirm: int = SWING_CONFIRM) -> pd.Series:
    """Kierunek ostatniego potwierdzonego impulsu: +1 wzrostowy, −1 spadkowy, NaN bez swingów."""
    start, end, up = _fib_impulse_frame(df, confirm)
    out = np.where(np.isnan(up), np.nan, np.where(up == 1.0, 1.0, -1.0))
    out[(end - start) == 0] = np.nan
    return pd.Series(out, index=df.index, name="fib_impulse")


def compute_sr_distance(
    df: pd.DataFrame,
    confirm: int = SWING_CONFIRM,
    lookback: int = SR_LOOKBACK,
    atr_n: int = ATR_N,
) -> pd.Series:
    """
    Poziomy = potwierdzone szczyty i dołki, których POTWIERDZENIE nastąpiło w [t − lookback, t].
    Cecha = (close − najbliższy poziom)/ATR ze znakiem: + = cena nad poziomem (wsparcie),
    − = pod (opór). „Odwrócenie biegunowości" wbudowane: poziom ma tylko stronę, nie etykietę.
    """
    sh, sl = confirmed_swings(df, confirm)
    atr = _atr(df, atr_n).to_numpy()
    close = df["close"].to_numpy(float)
    n = len(df)
    ph = np.flatnonzero(sh.notna().to_numpy())
    lh = sh.to_numpy()[ph]
    pl = np.flatnonzero(sl.notna().to_numpy())
    ll = sl.to_numpy()[pl]
    cpos = np.concatenate([ph, pl])
    clev = np.concatenate([lh, ll])
    order = np.argsort(cpos, kind="stable")
    cpos, clev = cpos[order], clev[order]
    out = np.full(n, np.nan)
    j0 = 0
    for t in range(n):
        while j0 < len(cpos) and cpos[j0] < t - lookback:
            j0 += 1
        j1 = np.searchsorted(cpos, t, side="right")
        if j1 <= j0 or np.isnan(atr[t]) or atr[t] == 0:
            continue
        d = close[t] - clev[j0:j1]
        out[t] = d[np.argmin(np.abs(d))] / atr[t]
    return pd.Series(out, index=df.index, name="sr_distance")


def compute_breakout(df: pd.DataFrame, n: int = BREAKOUT_N) -> pd.Series:
    """+1: close(t) > max(high[t−n..t−1]); −1: close(t) < min(low[t−n..t−1]); 0 inaczej.
    Zakres liczony BEZ bieżącego bara (`shift(1)`), inaczej close nigdy go nie przebije."""
    hi = df["high"].shift(1).rolling(n, min_periods=n).max()
    lo = df["low"].shift(1).rolling(n, min_periods=n).min()
    out = pd.Series(0.0, index=df.index)
    out[df["close"] > hi] = 1.0
    out[df["close"] < lo] = -1.0
    out[hi.isna()] = np.nan
    return out.rename("breakout")


TA_FEATURE_FUNCTIONS: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "trend_structure": compute_trend_structure,
    "double_top_bottom": compute_double_top_bottom,
    "head_shoulders": compute_head_shoulders,
    "ma_state": compute_ma_state,
    "ma_cross_age": compute_ma_cross_age,
    "trendline_distance": compute_trendline_distance,
    "fib_position": compute_fib_position,
    "fib_impulse": compute_fib_impulse,
    "sr_distance": compute_sr_distance,
    "breakout": compute_breakout,
}


def compute_ta_features(df: pd.DataFrame) -> pd.DataFrame:
    """Wszystkie cechy z TA_FEATURE_FUNCTIONS jako nowe kolumny; nie mutuje df."""
    out = df.copy()
    for name, fn in TA_FEATURE_FUNCTIONS.items():
        out[name] = fn(df)
    return out


# ---------------------------------------------------------------------------
# Reguły kierunkowe (A2) — sygnał ∈ {−1, 0, +1} z cech; parametry zapisane w pre-rejestracji
# ---------------------------------------------------------------------------


def _event(state: pd.Series) -> pd.Series:
    """Zdarzenie = świeca, w której stan zmienia wartość na niezerową (NaN traktowane jak 0)."""
    s = state.fillna(0.0)
    fired = (s != s.shift(1)) & (s != 0.0)
    return s.where(fired, 0.0)


def rule_trend_structure(f: pd.DataFrame) -> pd.Series:
    """STAN: long w strukturze HH+HL, short w LH+LL („graj z trendem")."""
    return f["trend_structure"].fillna(0.0).rename("rule_trend_structure")


def rule_breakout(f: pd.DataFrame) -> pd.Series:
    """ZDARZENIE z konstrukcji: kierunek wybicia z zakresu ostatnich BREAKOUT_N barów."""
    return f["breakout"].fillna(0.0).rename("rule_breakout")


def rule_double_top_bottom(f: pd.DataFrame) -> pd.Series:
    """ZDARZENIE: potwierdzenie podwójnego dna → long, podwójnego szczytu → short."""
    return _event(f["double_top_bottom"]).rename("rule_double_top_bottom")


def rule_head_shoulders(f: pd.DataFrame) -> pd.Series:
    """ZDARZENIE: odwrócona RGR → long, RGR → short."""
    return _event(f["head_shoulders"]).rename("rule_head_shoulders")


def rule_ma_cross(f: pd.DataFrame) -> pd.Series:
    """ZDARZENIE: świeże przecięcie EMA 10/30 (wiek 0) w kierunku znaku (EMA_fast − EMA_slow)."""
    direction = np.sign(f["ma_state"])
    return direction.where(f["ma_cross_age"] == 0, 0.0).fillna(0.0).rename("rule_ma_cross")


def rule_trendline_break(f: pd.DataFrame) -> pd.Series:
    """ZDARZENIE: zmiana znaku odległości od linii trendu (przez dołki) — nowy znak = kierunek."""
    return _event(np.sign(f["trendline_distance"])).rename("rule_trendline_break")


def rule_fib_retrace(f: pd.DataFrame) -> pd.Series:
    """STAN: close w paśmie zniesienia FIB_BAND ostatniego impulsu → kierunek impulsu."""
    pos = f["fib_position"]
    band = (pos >= FIB_BAND[0]) & (pos <= FIB_BAND[1])
    return f["fib_impulse"].where(band, 0.0).fillna(0.0).rename("rule_fib_retrace")


def rule_sr_bounce(f: pd.DataFrame) -> pd.Series:
    """STAN: |odległość od poziomu| ≤ SR_NEAR_ATR·ATR → odbicie od poziomu: nad → long, pod → short."""
    d = f["sr_distance"]
    near = d.abs() <= SR_NEAR_ATR
    return np.sign(d).where(near, 0.0).fillna(0.0).rename("rule_sr_bounce")


TA_RULE_FUNCTIONS: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "rule_trend_structure": rule_trend_structure,
    "rule_breakout": rule_breakout,
    "rule_double_top_bottom": rule_double_top_bottom,
    "rule_head_shoulders": rule_head_shoulders,
    "rule_ma_cross": rule_ma_cross,
    "rule_trendline_break": rule_trendline_break,
    "rule_fib_retrace": rule_fib_retrace,
    "rule_sr_bounce": rule_sr_bounce,
}
EVENT_RULES = frozenset(
    {
        "rule_breakout",
        "rule_double_top_bottom",
        "rule_head_shoulders",
        "rule_ma_cross",
        "rule_trendline_break",
    }
)
STATE_RULES = frozenset({"rule_trend_structure", "rule_fib_retrace", "rule_sr_bounce"})


def compute_ta_rules(features: pd.DataFrame) -> pd.DataFrame:
    """Wszystkie reguły z TA_RULE_FUNCTIONS jako kolumny (wejście: wynik `compute_ta_features`)."""
    out = pd.DataFrame(index=features.index)
    for name, fn in TA_RULE_FUNCTIONS.items():
        out[name] = fn(features)
    return out


def event_group_signal(rules: pd.DataFrame, members: frozenset[str] = EVENT_RULES) -> pd.Series:
    """
    A2: reguły ZDARZENIOWE jako jedna grupa — sign(Σ sygnałów), konflikt (+ i −) = 0. Powód
    (rachunek mocy z pre-rejestracji): pojedyncze zdarzenia AT są rzadkie (86–988 na 5,5 roku
    4h), więc osobno są NIEMIERZALNE; test rodziny (docs/rag/02) mierzy je razem, a werdykt
    dotyczy GRUPY, nie każdej reguły z osobna — tak jak `cdl_score_6` w A1.
    """
    cols = [c for c in rules.columns if c in members]
    return np.sign(rules[cols].sum(axis=1)).rename("rule_event_group")
