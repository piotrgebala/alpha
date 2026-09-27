"""
live_journal.py — dziennik na żywo (papierowo) portfela z rundy SZ1: trend tygodniowy TS1 na
koszyku top-20 (likwidacja izolowana 2×) + premia Coinbase CP1 na BTC (likwidacja izolowana 3×),
połączone regułą R1 (budżet ryzyka: cel 20 %/rok, sufit 2, bez hamulca). Reguły ZAMROŻONE
w `dziennik/README.md` (pre-rejestracja dziennika); silnik ten sam co w rundach
(`ts_momentum.portfolio`, `run_coinbase_cp1.daily_premium/premium_signal`, `sizing.apply_rules`).

Obok, OSOBNO i poza portfelem R1 (poprawka 3): X1 — momentum przekrojowe top-20 (nogi po 5, sygnał
28 dni, trzymanie 7 dni) jako średnia 7 faz, kapitał 1 = 0,5 long + 0,5 short, bez dźwigni i likwidacji
(jak w rundach X1/X1F); silnik `xs_momentum.long_short_returns`; zapis `x1_sygnaly.csv`, `x1_wyniki.csv`.

Po co: sprawdzian MECHANIKI na 2–3 miesiące (czy sygnał liczy się na czas, czy dane są kompletne,
czy wynik papierowy zgadza się z przeliczeniem), nie dowód przewagi (wniosek 80, `runs/INDEX.md`).

Zasady zapisu (`dziennik/`):
- `sygnaly.csv` — pozycje ogłoszone PRZED wynikiem: dopisywane raz na dzień `as_of` (ostatnia
  zamknięta świeca), nigdy nadpisywane; ponowny przebieg tego samego dnia niczego nie dubluje;
- `wyniki.csv` — dzienny wynik papierowy od `JOURNAL_START`; istniejące wiersze NIE są zmieniane —
  gdy przeliczenie daje inną wartość (rewizja danych, zmiana kodu), przebieg zgłasza „HISTORIA
  ZMIENIONA” i zostawia stary zapis;
- `przebiegi.log` — czas przebiegu, ostatnia świeca każdego źródła, status progów;
- `stan_rynku.csv` (poprawka 7) i `fng.csv` (poprawka 8) — etykiety TYLKO do zapisu (zmienność/trend BTC,
  Fear & Greed z alternative.me), nie wpływają na pozycje; ich brak lub błąd nie zatrzymuje dziennika.
- `strategie.csv` (poprawka 10) — opis i dokładne założenia każdej aktywnej strategii (z `journal_strategies`),
  nadpisywany w każdym przebiegu; ten sam opis drukowany w raporcie i w `dziennik/STRATEGIE.md`;
- `transakcje.csv` (poprawka 9) — lista ZAMKNIĘTYCH transakcji (append-only): pozycja jednej fazy w jednej
  monecie od zamknięcia dnia formowania do zamknięcia dnia kolejnego formowania tej fazy albo do likwidacji;
  `transakcje_otwarte.csv` — widok pozycji otwartych na `as_of`, NADPISYWANY przy każdym przebiegu. Tylko
  zapis — wynik portfela liczą `wyniki.csv` / `x1_wyniki.csv`.
- `rozbicie.csv`, `fazy.csv`, `koszyk.csv` (poprawka 11) — TYLKO zapis (append-only, wykrywanie „historia
  zmieniona” jak wyżej): dzienny zwrot składowej (k = 1) rozbity na cenę, funding, koszt i obrót (suma
  składników = netto = wartość w `wyniki.csv` / `x1_wyniki.csv`, sprawdzane przed zapisem); netto każdej
  z 7 faz (średnia faz = netto składowej); ranking obrotu 1–50 na początek miesiąca (top-20 = skład
  koszyka silnika). Liczone z tych samych ramek silnika co wynik (bez drugiego przeliczenia); błąd
  nie zatrzymuje dziennika („rozbicie/fazy/koszyk BŁĄD <typ>” w `przebiegi.log`, pełny komunikat
  w wydruku). Rozbicie i fazy liczone OSOBNO dla każdej składowej: błąd X1 nie blokuje zapisu trendu
  i premii („rozbicie +N (x1 BŁĄD <typ>)”); brakujące dni dopisuje następny udany przebieg (liczy od
  startu), więc kolejność wierszy w pliku nie musi być chronologiczna — czytać po kluczu. Netto
  porównywane jest z wynikiem TEGO przebiegu (to samo, co trafia do `wyniki.csv` przy nowym dniu);
  równość z zapisanym plikiem jest ścisła, gdy „historia zmieniona” = 0.

    PYTHONUTF8=1 py -m backtest.live_journal              # pobranie danych + zapis
    PYTHONUTF8=1 py -m backtest.live_journal --bez-pobierania

Testy: `tests/test_live_journal.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import load_config
from backtest.journal_strategies import build as build_strategies
from backtest.journal_strategies import summarize as summarize_strategies
from backtest.journal_strategies import to_rows as strategy_rows
from backtest.rebalance_premium import (
    TOP_N,
    VOLUME_LOOKBACK_DAYS,
    monthly_members,
    monthly_ranking,
)
from backtest.run_coinbase_cp1 import daily_premium, premium_signal
from backtest.sizing import apply_rules
from backtest.ts_momentum import (
    HOLD_DAYS,
    PHASES,
    build_formations,
    ewma_vol,
    formation_dates,
    portfolio,
    signal_sign,
)
from backtest.xs_momentum import (
    CAPITAL_PER_LEG,
    LEG_SIZE,
    _month_of,
    daily_funding_panel,
    long_short_returns,
    rank_legs,
    signal_panel,
)

LIVE_DIR = Path("data/raw/live")
JOURNAL_DIR = Path("dziennik")
ENGINE_START = pd.Timestamp("2025-09-01", tz="UTC")  # pierwszy miesiąc silnika (rozbieg R1 ≥ 1 rok)
JOURNAL_START = pd.Timestamp("2026-09-24", tz="UTC")  # pierwszy dzień wyniku (poprawka 1, README)
LEV_TREND, LEV_CB, MMR = 2.0, 3.0, 0.01
WARN_DD = 0.184  # największe obsunięcie R1 w historii (SZ1 na pełnym uniwersum, RU1)
STOP_DD = 0.276  # 1,5 × powyższe — reguła zapisana z góry (poprawka 2)
X1_START = pd.Timestamp("2026-09-25", tz="UTC")  # pierwszy dzień wyniku X1 (poprawka 3)
X1_WARN_DD = 0.550  # największe obsunięcie X1 (średnia 7 faz) w historii 2021–2026 (runda X1F)
X1_STOP_DD = 0.825  # 1,5 × powyższe — ta sama reguła co dla R1, zapisana z góry (poprawka 3)
BTC = "BTCUSDT"
TOL = 1e-9
# Poprawka 7 (2026-09-25): etykieta stanu rynku — TYLKO zapis, nie wpływa na pozycje. Progi tercyli
# 30-dniowej zmienności BTC (roczna) zamrożone z historii 2021-01-01 → 2026-06-30 (perp BTCUSDT 1d).
VOL_TERCILES = (0.428, 0.6014)
VOL_WINDOW, TREND_WINDOW = 30, 90
# Poprawka 8 (2026-09-25): etykieta Fear & Greed (alternative.me) — TYLKO zapis do `fng.csv`, wartość
# i klasa wprost z publikacji (bez własnych progów); plik z `data.fetch_live.fetch_fng_safe`.
FNG_FILE = "alternative_fng_1d.parquet"
FNG_LABELS = ("Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed")  # klasy alternative.me
# Poprawka 9 (2026-09-26): lista transakcji — tylko zapis; kolumny w kolejności pliku.
TRADE_KEY = ["skladowa", "faza", "data_wejscia", "symbol"]
TRADE_COMMON = [
    "skladowa",
    "faza",
    "symbol",
    "kierunek",
    "data_wejscia",
    "cena_wejscia",
]
TRADE_SIZE = [
    "dzwignia",
    "waga",
    "k",
    "wielkosc_proc_kapitalu",
    "depozyt_proc_kapitalu",
]
TRADE_CLOSED_COLS = [
    *TRADE_COMMON,
    "data_wyjscia",
    "cena_wyjscia",
    "powod_wyjscia",
    *TRADE_SIZE,
    "zwrot_pozycji_proc",
    "wynik_cenowy_proc_kapitalu",
    "przed_startem",
]
TRADE_OPEN_COLS = [
    "as_of",
    *TRADE_COMMON,
    "cena_biezaca",
    "planowane_wyjscie",
    *TRADE_SIZE,
    "zwrot_biezacy_proc",
    "przed_startem",
]
# Poprawka 11 (2026-09-27): rozbicie zwrotu, wyniki per faza, skład koszyka — tylko zapis.
BREAKDOWN_KEY = ["date", "skladowa"]
BREAKDOWN_VALUES = [
    "cena",
    "funding",
    "koszt",
    "netto",
    "obrot",
    "likwidacje",
    "r_long",
    "r_short",
]
BREAKDOWN_COLS = [*BREAKDOWN_KEY, *BREAKDOWN_VALUES]
PHASE_KEY = ["date", "skladowa", "faza"]
PHASE_COLS = [*PHASE_KEY, "netto"]
BASKET_KEY = ["miesiac", "symbol"]
BASKET_COLS = [*BASKET_KEY, "pozycja", "sredni_obrot_30d", "czlonek_top20", "ma_funding"]
# `ma_funding` = stan pobrania w dniu zapisu (funding pobierany tylko dla członków koszyka od
# ENGINE_START) — późniejsze dociągnięcie pliku to nie zmiana historii, więc poza porównaniem.
BASKET_VALUES = ["pozycja", "sredni_obrot_30d", "czlonek_top20"]
BASKET_DEPTH = 50
X1_PHASE_COLS = ["r_long", "r_short", "r_ls_gross", "funding_net", "cost", "turnover", "r_net"]


# ------------------------------------------------------------------ dane
def load_live(live_dir: Path = LIVE_DIR) -> dict:
    """Panele dzienne (close, high, low, obrót), funding dzienny i premia Coinbase z `live_dir`."""
    from data.fetch_live import symbol_files

    frames = []
    for sym, p in symbol_files(live_dir).items():
        df = pd.read_parquet(p)
        if df.empty:
            continue
        frames.append(df.assign(symbol=sym))
    panel = pd.concat(frames, ignore_index=True)
    panel["open_time"] = pd.to_datetime(panel["open_time"], utc=True)
    piv = {
        k: panel.pivot(index="open_time", columns="symbol", values=v).sort_index()
        for k, v in (
            ("close", "close"),
            ("high", "high"),
            ("low", "low"),
            ("volume", "quote_volume"),
        )
    }
    cb = pd.read_parquet(Path(live_dir) / "coinbase_BTC-USD_1d.parquet")
    cb_open = pd.to_datetime(cb["open_time"], utc=True)
    cb = cb[cb_open + pd.Timedelta(days=1) <= pd.Timestamp.now(tz="UTC")]  # tylko zamknięte dni
    spot = pd.read_parquet(Path(live_dir) / "spot_BTC-USDT_8h.parquet")
    piv["premium"] = daily_premium(cb, spot)
    piv["funding"] = daily_funding_panel(live_dir)
    return piv


def truncate(data: dict, as_of: pd.Timestamp) -> dict:
    """Wszystko ≤ `as_of` (dzień ostatniej zamkniętej świecy) — jedyne dane, które wolno widzieć."""
    out = {}
    for k, v in data.items():
        out[k] = v[v.index <= as_of]
    return out


# ------------------------------------------------------------------ silnik
def _months(as_of: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.date_range(ENGINE_START, as_of, freq="MS"))


def components(
    data: dict, as_of: pd.Timestamp, fee: float, engines: dict | None = None
) -> tuple[pd.DataFrame, dict]:
    """
    Dzienne zwroty netto składowych (k = 1) do `as_of` + wejścia silnika (do pozycji).
    `engines` (poprawka 11, tylko zapis): gdy podany, dostaje pełne ramki silnika — średnią
    i 7 faz każdej składowej oraz skład koszyka — te same obiekty, z których powstał wynik.
    """
    d = truncate(data, as_of)
    end = as_of + pd.Timedelta(days=1)
    members = monthly_members(d["volume"], _months(as_of))
    liq = {"high": d["high"], "low": d["low"], "lev": LEV_TREND, "mmr": MMR}
    tr, tr_phases = portfolio(d["close"], d["funding"], members, ENGINE_START, end, fee, liq=liq)
    close_b = d["close"][[BTC]]
    signs_b = pd.DataFrame({BTC: premium_signal(d["premium"]).reindex(close_b.index)})
    mem_b = {m: [BTC] for m in members}
    liq_b = {"high": d["high"][[BTC]], "low": d["low"][[BTC]], "lev": LEV_CB, "mmr": MMR}
    cb, cb_phases = portfolio(
        close_b,
        d["funding"][[BTC]],
        mem_b,
        ENGINE_START,
        end,
        fee,
        signs_override=signs_b,
        liq=liq_b,
    )
    rets = pd.concat(
        [
            tr.dropna().set_index("date")["net"].rename("trend"),
            cb.dropna().set_index("date")["net"].rename("coinbase"),
        ],
        axis=1,
    ).dropna()
    ctx = {"members": members, "signs_b": signs_b, "close": d["close"], "end": end}
    if engines is not None:
        engines.update(
            trend=tr,
            trend_phases=tr_phases,
            coinbase=cb,
            coinbase_phases=cb_phases,
            members=members,
        )
    return rets, ctx


def next_multipliers(rets: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Reguła R1 na historii składowych + mnożniki na NASTĘPNY dzień: dopisany pusty wiersz jutra
    (mnożnik dnia i liczy się z r.iloc[:i], więc zwrot jutra nie wpływa na jego własny mnożnik).
    """
    tomorrow = rets.index[-1] + pd.Timedelta(days=1)
    ext = pd.concat([rets, pd.DataFrame({c: [0.0] for c in rets.columns}, index=[tomorrow])])
    out = apply_rules(ext, "R1").set_index("date")
    k_next = {c: float(out[f"k_{c}"].iloc[-1]) for c in rets.columns}
    return out.iloc[:-1], k_next


def phase_positions(
    close: pd.DataFrame,
    signs: pd.DataFrame,
    members: dict,
    as_of: pd.Timestamp,
    end: pd.Timestamp,
    lev: float,
) -> pd.DataFrame:
    """
    Wagi ostatniego formowania każdej fazy (≤ `as_of`), w jednostkach kapitału SKŁADOWEJ, i depozyt
    przy dźwigni `lev`. Faza formowana dokładnie w `as_of` = zlecenia do złożenia dziś.
    """
    vols = ewma_vol(close)
    rows = []
    for ph in range(PHASES):
        dates = [t for t in formation_dates(close.index, ENGINE_START, end, ph) if t <= as_of]
        if not dates:
            continue
        t = dates[-1]
        _, w = build_formations(signs, vols, members, [t])[0]
        for sym, wi in zip(close.columns, w, strict=True):
            if wi != 0:
                rows.append(
                    {
                        "phase": ph,
                        "formed": t.date().isoformat(),
                        "today": t == as_of,
                        "symbol": sym,
                        "sign": int(np.sign(wi)),
                        "weight": float(wi) / PHASES,
                    }
                )
    df = pd.DataFrame(rows, columns=["phase", "formed", "today", "symbol", "sign", "weight"])
    df["margin"] = df["weight"].abs() / lev
    return df


def positions(data: dict, as_of: pd.Timestamp, fee: float, engines: dict | None = None) -> tuple:
    """Pozycje na dzień po `as_of` (obie składowe, po mnożnikach R1), mnożniki, historia R1, zwroty."""
    rets, ctx = components(data, as_of, fee, engines)
    hist, k = next_multipliers(rets)
    close = ctx["close"]
    tr = phase_positions(
        close, signal_sign(close), ctx["members"], as_of, ctx["end"], LEV_TREND
    ).assign(component="trend")
    cb = phase_positions(
        close[[BTC]], ctx["signs_b"], {m: [BTC] for m in ctx["members"]}, as_of, ctx["end"], LEV_CB
    ).assign(component="coinbase")
    pos = pd.concat([tr, cb], ignore_index=True)
    pos["k"] = pos["component"].map(k)
    pos["exposure"] = pos["weight"] * pos["k"]
    pos["margin"] = pos["margin"] * pos["k"]
    pos.insert(0, "as_of", as_of.date().isoformat())
    return pos, k, hist, rets


def x1_component(
    close: pd.DataFrame,
    funding: pd.DataFrame,
    members: dict,
    as_of: pd.Timestamp,
    end: pd.Timestamp,
    fee: float,
    phases_out: list | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    X1 (poprawka 3): dzienny zwrot netto jako średnia 7 faz `long_short_returns` (fazy startują
    w kolejne dni od `ENGINE_START`, wspólne okno) + nogi ostatniego formowania każdej fazy (≤ `as_of`)
    w jednostkach kapitału X1 (±0,5/5 na monetę, / 7 faz). `phases_out` (poprawka 11, tylko zapis):
    gdy podana, dostaje pełną ramkę `long_short_returns` każdej fazy (po kolei 0–6).
    """
    signal = signal_panel(close)
    month_starts = sorted(members)
    series, rows = [], []
    for ph in range(PHASES):
        dates = formation_dates(close.index, ENGINE_START, end, ph)
        out = long_short_returns(close, funding, members, dates, fee)
        if phases_out is not None:
            phases_out.append(out)
        if len(out):
            series.append(out.set_index("date")["r_net"].rename(ph))
        past = [t for t in dates if t <= as_of]
        if not past:
            continue
        t = past[-1]
        m = _month_of(t, month_starts)
        legs = rank_legs(signal.loc[t], members[m]) if m is not None else None
        if legs is None:
            continue
        for sign, syms in ((1, legs[0]), (-1, legs[1])):
            for sym in syms:
                rows.append(
                    {
                        "phase": ph,
                        "formed": t.date().isoformat(),
                        "today": t == as_of,
                        "symbol": sym,
                        "sign": sign,
                        "weight": sign * CAPITAL_PER_LEG / LEG_SIZE / PHASES,
                    }
                )
    pos = pd.DataFrame(rows, columns=["phase", "formed", "today", "symbol", "sign", "weight"])
    if len(series) < PHASES:
        return pd.Series(dtype=float, name="x1"), pos
    panel = pd.concat(series, axis=1)
    panel = panel[panel.index >= max(s.first_valid_index() for _, s in panel.items())]
    return panel.mean(axis=1).rename("x1"), pos


def x1_rows(r: pd.Series, start: pd.Timestamp | None = None) -> pd.DataFrame:
    """Wynik papierowy X1 od `start` (domyślnie `X1_START`): zwrot, kapitał, obsunięcie."""
    s = r[r.index >= (X1_START if start is None else start)]
    eq = np.cumprod(1.0 + s.to_numpy())
    dd = 1.0 - eq / np.maximum.accumulate(np.maximum(eq, 1.0)) if len(s) else eq
    return pd.DataFrame(
        {
            "date": [d.date().isoformat() for d in s.index],
            "r_x1": s.to_numpy(),
            "equity": eq,
            "drawdown": dd,
        }
    )


# ------------------------------------------------------------------ zapis
def journal_rows(
    hist: pd.DataFrame, rets: pd.DataFrame, start: pd.Timestamp | None = None
) -> pd.DataFrame:
    """Wynik papierowy od `start` (domyślnie `JOURNAL_START`): zwroty, mnożniki, kapitał, obsunięcie."""
    h = hist[hist.index >= (JOURNAL_START if start is None else start)]
    if h.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "r_trend",
                "r_coinbase",
                "k_trend",
                "k_coinbase",
                "r_port",
                "equity",
                "drawdown",
            ]
        )
    r = rets.reindex(h.index)
    eq = np.cumprod(1.0 + h["ret"].to_numpy())
    dd = 1.0 - eq / np.maximum.accumulate(np.maximum(eq, 1.0))
    return pd.DataFrame(
        {
            "date": [d.date().isoformat() for d in h.index],
            "r_trend": r["trend"].to_numpy(),
            "r_coinbase": r["coinbase"].to_numpy(),
            "k_trend": h["k_trend"].to_numpy(),
            "k_coinbase": h["k_coinbase"].to_numpy(),
            "r_port": h["ret"].to_numpy(),
            "equity": eq,
            "drawdown": dd,
        }
    )


def append_rows(
    path: Path, new: pd.DataFrame, key: list[str], value_cols: list[str]
) -> tuple[int, list[str]]:
    """
    Dopisuje wiersze o nowych kluczach; istniejących NIE zmienia. Zwraca (liczba dopisanych,
    lista kluczy, dla których przeliczenie różni się od zapisu — „historia zmieniona”).
    """
    if path.exists():
        old = pd.read_csv(path, dtype={k: str for k in key})
    else:
        old = pd.DataFrame(columns=new.columns)
    new = new.astype({k: str for k in key})
    old_keys = set(map(tuple, old[key].astype(str).to_numpy())) if len(old) else set()
    changed = []
    if len(old):
        m = old.merge(new, on=key, suffixes=("_old", "_new"))
        for _, row in m.iterrows():
            for c in value_cols:
                a, b = row[f"{c}_old"], row[f"{c}_new"]
                if pd.api.types.is_number(a) and pd.api.types.is_number(b):
                    if not (np.isclose(a, b, rtol=0, atol=TOL) or (np.isnan(a) and np.isnan(b))):
                        changed.append("|".join(str(row[k]) for k in key) + f":{c}")
                elif str(a) != str(b):
                    changed.append("|".join(str(row[k]) for k in key) + f":{c}")
    add = new[[tuple(x) not in old_keys for x in new[key].astype(str).to_numpy()]]
    if len(add):
        path.parent.mkdir(parents=True, exist_ok=True)
        add.to_csv(path, mode="a", header=not path.exists(), index=False)
    return len(add), changed


def stop_status(drawdown: float, warn: float = WARN_DD, stop: float = STOP_DD) -> str:
    if drawdown >= stop:
        return "STOP"
    if drawdown >= warn:
        return "OSTRZEŻENIE"
    return "OK"


def market_state(close: pd.Series, start: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Etykieta stanu rynku per dzień d ≥ `start` z zamknięć BTC ≤ d (poprawka 7, tylko zapis):
    zmienność 30 dni (roczna) i jej tercyl wg zamrożonych progów, zwrot 90 dni i jego znak.
    """
    start = JOURNAL_START if start is None else start
    c = close.dropna().astype(float)
    vol = c.pct_change().rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std() * np.sqrt(365)
    r90 = c / c.shift(TREND_WINDOW) - 1.0
    lo, hi = VOL_TERCILES
    stan = np.where(vol < lo, "niska", np.where(vol < hi, "srednia", "wysoka"))
    out = pd.DataFrame(
        {
            "date": c.index.strftime("%Y-%m-%d"),
            "btc_vol30": vol.round(6).to_numpy(),
            "vol_stan": np.where(vol.isna(), "", stan),
            "btc_r90": r90.round(6).to_numpy(),
            "trend90": np.sign(r90).fillna(0).astype(int).to_numpy(),
        }
    )
    return out[(c.index >= start) & vol.notna().to_numpy() & r90.notna().to_numpy()].reset_index(
        drop=True
    )


def fng_rows(
    fng: pd.DataFrame, start: pd.Timestamp | None = None, now: pd.Timestamp | None = None
) -> pd.DataFrame:
    """
    Etykieta Fear & Greed per dzień ≥ `start` (poprawka 8, tylko zapis): `fng` = wartość 0–100 i
    `fng_etykieta` = klasa wprost z alternative.me (`parse_fng`: date, value, label). Tylko dni już
    opublikowane (≤ `now`); braki po awarii uzupełniają się przy następnym przebiegu z pełnej historii.
    """
    start = JOURNAL_START if start is None else start
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    d = pd.to_datetime(fng["date"], utc=True)
    keep = ((d >= start) & (d <= now)).to_numpy()
    labels = fng.loc[keep, "label"].astype(str)
    unknown = sorted(set(labels) - set(FNG_LABELS))
    if unknown:  # fail loud (jak `fetch_external`): do CSV trafiają tylko znane klasy
        raise ValueError(f"fng: nieznana klasa {unknown[:3]} — oczekiwano {FNG_LABELS}")
    out = pd.DataFrame(
        {
            "date": d[keep].dt.strftime("%Y-%m-%d").to_numpy(),
            "fng": fng.loc[keep, "value"].astype(float).round().astype(int).to_numpy(),
            "fng_etykieta": labels.to_numpy(),
        }
    )
    return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def phase_lots(
    close: pd.DataFrame,
    low: pd.DataFrame | None,
    high: pd.DataFrame | None,
    forms: list[tuple[int, np.ndarray]],
    as_of: pd.Timestamp,
    lev: float | None,
    mmr: float = MMR,
) -> list[dict]:
    """
    Pozycje jednej fazy (poprawka 9). Niezerowa waga formowania k żyje od zamknięcia dnia formowania
    do zamknięcia dnia formowania k+1 (≤ `as_of`) — to samo okno zwrotów co
    `ts_momentum.phase_returns_liq`. Likwidacja izolowana jak w silniku: pierwszy dzień, w którym
    minimum (long) / maksimum (short) odsuwa cenę od ceny wejścia o ≥ 1/lev − mmr; cena wyjścia =
    cena likwidacji, zwrot pozycji = −1/lev (cały depozyt). `lev=None` — bez likwidacji (X1).
    """
    pos_as_of = close.index.get_loc(as_of)
    thr = 1.0 / lev - mmr if lev else None
    lots = []
    for j, (t_pos, w) in enumerate(forms):
        if t_pos > pos_as_of:
            break
        nxt = forms[j + 1][0] if j + 1 < len(forms) else None
        rotated = nxt is not None and nxt <= pos_as_of
        end_pos = nxt if rotated else pos_as_of
        for s in np.flatnonzero(w):
            sym, wi = close.columns[s], float(w[s])
            entry = float(close.iat[t_pos, s])
            lot = {"symbol": sym, "w": wi, "t_pos": t_pos, "entry": entry, "next_pos": nxt}
            lot.update(status="otwarta", exit_pos=None, exit_price=np.nan, ret=np.nan)
            if thr is not None and end_pos > t_pos:
                if wi > 0:
                    ext = low[sym].iloc[t_pos + 1 : end_pos + 1].to_numpy(float) / entry
                    hit = np.flatnonzero(ext <= 1.0 - thr)
                else:
                    ext = high[sym].iloc[t_pos + 1 : end_pos + 1].to_numpy(float) / entry
                    hit = np.flatnonzero(ext >= 1.0 + thr)
                if len(hit):
                    lot.update(
                        status="likwidacja",
                        exit_pos=t_pos + 1 + int(hit[0]),
                        exit_price=entry * (1.0 - thr if wi > 0 else 1.0 + thr),
                        ret=-1.0 / lev,
                    )
            if lot["status"] == "otwarta" and rotated:
                exit_price = float(close.iat[nxt, s])
                lot.update(
                    status="rotacja",
                    exit_pos=nxt,
                    exit_price=exit_price,
                    ret=float(np.sign(wi)) * (exit_price / entry - 1.0),
                )
            lots.append(lot)
    return lots


def _k_at(
    hist: pd.DataFrame, k_next: dict, col: str, day: pd.Timestamp, as_of: pd.Timestamp
) -> float:
    """Mnożnik R1 składowej w pierwszym dniu trzymania pozycji (dzień po formowaniu)."""
    if day > as_of:
        return float(k_next[col])
    return float(hist.at[day, f"k_{col}"]) if day in hist.index else float("nan")


def trade_ledger(
    data: dict, as_of: pd.Timestamp, hist: pd.DataFrame, k_next: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lista transakcji (poprawka 9): (zamknięte, otwarte na `as_of`) dla trendu, premii Coinbase i X1 —
    pozycje, które żyły w okresie wyniku dziennika (wyjście ≥ start składowej) albo są otwarte.
    Wielkość = |waga × k| w % kapitału portfela (trend/premia: portfel R1; X1: własny kapitał X1).
    """
    d = truncate(data, as_of)
    close = d["close"]
    idx = close.index
    end = as_of + pd.Timedelta(days=1)
    members = monthly_members(d["volume"], _months(as_of))
    signs_b = pd.DataFrame({BTC: premium_signal(d["premium"]).reindex(idx)})
    specs = [
        ("trend", close, signal_sign(close), members, LEV_TREND, "trend", JOURNAL_START),
        (
            "premia_coinbase",
            close[[BTC]],
            signs_b,
            {m: [BTC] for m in members},
            LEV_CB,
            "coinbase",
            JOURNAL_START,
        ),
    ]
    closed, opened = [], []

    def emit(name, ph, lot, lev, weight, k, start):
        formed = idx[lot["t_pos"]]
        size = 100.0 * abs(weight * k)
        base = {
            "skladowa": name,
            "faza": ph,
            "symbol": lot["symbol"],
            "kierunek": "long" if weight > 0 else "short",
            "data_wejscia": formed.date().isoformat(),
            "cena_wejscia": lot["entry"],
            "dzwignia": lev,
            "waga": weight,
            "k": k,
            "wielkosc_proc_kapitalu": size,
            "depozyt_proc_kapitalu": size / lev,
            "przed_startem": bool(formed < start - pd.Timedelta(days=1)),
        }
        if lot["status"] == "otwarta":
            cur = float(close[lot["symbol"]].loc[as_of])
            opened.append(
                {
                    **base,
                    "as_of": as_of.date().isoformat(),
                    "cena_biezaca": cur,
                    "planowane_wyjscie": (formed + pd.Timedelta(days=HOLD_DAYS)).date().isoformat(),
                    "zwrot_biezacy_proc": 100.0
                    * float(np.sign(weight))
                    * (cur / lot["entry"] - 1.0),
                }
            )
            return
        exit_day = idx[lot["exit_pos"]]
        if exit_day < start:
            return  # zamknięta przed startem wyniku składowej — poza dziennikiem
        closed.append(
            {
                **base,
                "data_wyjscia": exit_day.date().isoformat(),
                "cena_wyjscia": lot["exit_price"],
                "powod_wyjscia": lot["status"],
                "zwrot_pozycji_proc": 100.0 * lot["ret"],
                "wynik_cenowy_proc_kapitalu": size * lot["ret"],
            }
        )

    for name, cl, signs, mem, lev, kcol, start in specs:
        vols = ewma_vol(cl)
        for ph in range(PHASES):
            forms = build_formations(
                signs, vols, mem, formation_dates(cl.index, ENGINE_START, end, ph)
            )
            for lot in phase_lots(
                cl, d["low"][cl.columns], d["high"][cl.columns], forms, as_of, lev
            ):
                day = idx[lot["t_pos"]] + pd.Timedelta(days=1)
                emit(
                    name,
                    ph,
                    lot,
                    lev,
                    lot["w"] / PHASES,
                    _k_at(hist, k_next, kcol, day, as_of),
                    start,
                )
    signal = signal_panel(close)
    month_starts = sorted(members)
    col_pos = {c: i for i, c in enumerate(close.columns)}
    for ph in range(PHASES):
        forms = []
        for t in formation_dates(idx, ENGINE_START, end, ph):
            m = _month_of(t, month_starts)
            legs = rank_legs(signal.loc[t], members[m]) if m is not None else None
            w = np.zeros(len(close.columns))
            if legs is not None:
                for sgn, syms in ((1.0, legs[0]), (-1.0, legs[1])):
                    for sym in syms:
                        w[col_pos[sym]] = sgn * CAPITAL_PER_LEG / LEG_SIZE
            forms.append((idx.get_loc(t), w))
        for lot in phase_lots(close, None, None, forms, as_of, None):
            emit("x1", ph, lot, 1.0, lot["w"] / PHASES, 1.0, X1_START)
    closed_df = pd.DataFrame(closed, columns=TRADE_CLOSED_COLS)
    open_df = pd.DataFrame(opened, columns=TRADE_OPEN_COLS)
    return (
        closed_df.sort_values(["data_wyjscia", "skladowa", "faza", "symbol"]).reset_index(
            drop=True
        ),
        open_df.sort_values(["skladowa", "faza", "symbol"]).reset_index(drop=True),
    )


def strategy_book() -> list[dict]:
    """Opisy aktywnych strategii (poprawka 10) z parametrami tego dziennika."""
    return build_strategies(
        {
            "JOURNAL_START": JOURNAL_START,
            "X1_START": X1_START,
            "LEV_TREND": LEV_TREND,
            "LEV_CB": LEV_CB,
            "MMR": MMR,
            "WARN_DD": WARN_DD,
            "STOP_DD": STOP_DD,
            "X1_WARN_DD": X1_WARN_DD,
            "X1_STOP_DD": X1_STOP_DD,
        }
    )


def summarize_trades(closed: pd.DataFrame | None, opened: pd.DataFrame | None, txt: str) -> str:
    """Jedna linia do wydruku: zamknięte w tym przebiegu i otwarte per składowa (poprawka 9)."""
    if opened is None:
        return f"  Transakcje (poprawka 9): {txt}"
    per = opened.groupby("skladowa").size().to_dict()
    liq = int((closed["powod_wyjscia"] == "likwidacja").sum()) if closed is not None else 0
    return (
        f"  Transakcje (poprawka 9): zamknięte dopisane {txt}; otwarte {len(opened)} "
        f"(trend {per.get('trend', 0)}, premia Coinbase {per.get('premia_coinbase', 0)}, "
        f"X1 {per.get('x1', 0)}); likwidacji w historii dziennika: {liq}"
    )


# ------------------------------------------------------------------ poprawka 11: tylko zapis
def _days(dates) -> pd.DatetimeIndex:
    """Daty wyniku (tekst RRRR-MM-DD albo znaczniki) → indeks dni UTC."""
    return pd.DatetimeIndex(pd.to_datetime(pd.Series(list(dates), dtype=object), utc=True))


def ts_breakdown(avg: pd.DataFrame, name: str, dates) -> pd.DataFrame:
    """
    Rozbicie zwrotu składowej silnika TS1 (trend / premia Coinbase, k = 1) na dni `dates`: średnia
    7 faz `ts_momentum.portfolio` — `cena` = gross (strata likwidacji jest w cenie), `funding`,
    `koszt` = −cost (wkład kosztu do zwrotu, ≤ 0), `netto` = net, `obrot` = turnover (w kapitale
    składowej), `likwidacje` = liczba pozycji zlikwidowanych tego dnia we wszystkich fazach.
    Brak dnia w silniku = ValueError.
    """
    days = _days(dates)
    a = avg.set_index("date").reindex(days)
    if a["net"].isna().any():
        raise ValueError(f"{name}: brak dni silnika {list(a.index[a['net'].isna()].date)[:3]}")
    liq = a["liquidations"] * PHASES if "liquidations" in a else pd.Series(0.0, index=days)
    return pd.DataFrame(
        {
            "date": days.strftime("%Y-%m-%d"),
            "skladowa": name,
            "cena": a["gross"].to_numpy(),
            "funding": a["funding"].to_numpy(),
            "koszt": -a["cost"].to_numpy(),
            "netto": a["net"].to_numpy(),
            "obrot": a["turnover"].to_numpy(),
            "likwidacje": liq.round().astype(int).to_numpy(),
            "r_long": np.nan,
            "r_short": np.nan,
        },
        columns=BREAKDOWN_COLS,
    )


def x1_panels(phases: list[pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Panele dni × faza (0–6) kolumn `long_short_returns` X1 na tym samym wspólnym oknie co
    `x1_component` (od pierwszego dnia, w którym wszystkie fazy mają zwrot).
    """
    frames = [f.set_index("date") for f in phases if len(f)]
    if len(frames) < PHASES:
        raise ValueError(f"x1: {len(frames)} faz z wynikiem < {PHASES}")
    net = pd.concat([f["r_net"].rename(ph) for ph, f in enumerate(frames)], axis=1)
    cut = max(s.first_valid_index() for _, s in net.items())
    out = {}
    for c in X1_PHASE_COLS:
        p = pd.concat([f[c].rename(ph) for ph, f in enumerate(frames)], axis=1)
        out[c] = p[p.index >= cut]
    return out


def x1_breakdown(panels: dict[str, pd.DataFrame], dates) -> pd.DataFrame:
    """
    Rozbicie zwrotu X1 na dni `dates` (średnie 7 faz): `cena` = 0,5·(r_long − r_short) (brutto obu
    nóg), `funding`, `koszt` = −cost, `netto` = r_net, `obrot`, `likwidacje` = 0 (X1 bez dźwigni
    i likwidacji), `r_long` / `r_short` = zwrot nogi long / short na jednostkę nogi.
    """
    days = _days(dates)
    mean = {c: p.reindex(days).mean(axis=1) for c, p in panels.items()}
    if mean["r_net"].isna().any():
        raise ValueError(f"x1: brak dni silnika {list(days[mean['r_net'].isna()].date)[:3]}")
    return pd.DataFrame(
        {
            "date": days.strftime("%Y-%m-%d"),
            "skladowa": "x1",
            "cena": mean["r_ls_gross"].to_numpy(),
            "funding": mean["funding_net"].to_numpy(),
            "koszt": -mean["cost"].to_numpy(),
            "netto": mean["r_net"].to_numpy(),
            "obrot": mean["turnover"].to_numpy(),
            "likwidacje": 0,
            "r_long": mean["r_long"].to_numpy(),
            "r_short": mean["r_short"].to_numpy(),
        },
        columns=BREAKDOWN_COLS,
    )


def phase_rows(phase_net: dict[int, pd.Series], name: str, dates) -> pd.DataFrame:
    """Netto każdej fazy (0–6) składowej w dni `dates` (`fazy.csv`); brak fazy albo dnia = błąd."""
    if sorted(phase_net) != list(range(PHASES)):
        raise ValueError(f"{name}: fazy {sorted(phase_net)} zamiast 0–{PHASES - 1}")
    days = _days(dates)
    if not len(days):
        return pd.DataFrame(columns=PHASE_COLS)
    parts = []
    for ph in range(PHASES):
        v = phase_net[ph].reindex(days)
        if v.isna().any():
            raise ValueError(f"{name}: faza {ph} bez wyniku {list(days[v.isna()].date)[:3]}")
        parts.append(
            pd.DataFrame(
                {
                    "date": days.strftime("%Y-%m-%d"),
                    "skladowa": name,
                    "faza": ph,
                    "netto": v.to_numpy(),
                }
            )
        )
    out = pd.concat(parts, ignore_index=True)[PHASE_COLS]
    return out.sort_values(["date", "faza"], kind="stable").reset_index(drop=True)


def _expected(expected: dict[str, pd.Series], name: str, dates: pd.Series) -> np.ndarray:
    e = expected[name].reindex(dates.to_numpy())
    if e.isna().any():
        raise ValueError(f"{name}: dni bez wyniku dziennika {list(dates[e.isna().to_numpy()])[:3]}")
    return e.to_numpy(dtype=float)


def check_breakdown(rows: pd.DataFrame, expected: dict[str, pd.Series], tol: float = TOL) -> None:
    """
    Kontrola przed zapisem `rozbicie.csv`: cena + funding + koszt = netto i netto = wynik składowej
    (`expected`: składowa → seria po dacie z `expected_results`, czyli wynik TEGO przebiegu, który
    przy nowym dniu trafia do `wyniki.csv` / `x1_wyniki.csv`), oba do `tol`; każdy dzień wyniku ma
    wiersz rozbicia. Niezgodność = ValueError (nic nie jest zapisane). Równość z PLIKIEM wyników jest
    ścisła, gdy przebieg zgłasza „historia zmieniona: 0” (inaczej plik trzyma starszy zapis).
    """
    total = rows["cena"] + rows["funding"] + rows["koszt"]
    bad = ~((total - rows["netto"]).abs() <= tol)
    if bad.any():
        raise ValueError(f"rozbicie: suma składników ≠ netto w {int(bad.sum())} wierszach")
    for name, g in rows.groupby("skladowa"):
        diff = np.abs(g["netto"].to_numpy(dtype=float) - _expected(expected, name, g["date"]))
        if not (diff <= tol).all():
            raise ValueError(f"rozbicie {name}: netto ≠ wynik dziennika (maks. {diff.max():.3g})")
    for name, e in expected.items():
        missing = set(e.index) - set(rows.loc[rows["skladowa"] == name, "date"])
        if missing:
            raise ValueError(f"rozbicie {name}: brak dni {sorted(missing)[:3]}")


def check_phases(rows: pd.DataFrame, expected: dict[str, pd.Series], tol: float = TOL) -> None:
    """Kontrola przed zapisem `fazy.csv`: w każdym dniu 7 faz, ich średnia = wynik składowej (`tol`)."""
    g = rows.groupby(["skladowa", "date"])["netto"].agg(["size", "mean"]).reset_index()
    if not (g["size"] == PHASES).all():
        raise ValueError("fazy: dzień bez kompletu 7 faz")
    for name, h in g.groupby("skladowa"):
        diff = np.abs(h["mean"].to_numpy(dtype=float) - _expected(expected, name, h["date"]))
        if not (diff <= tol).all():
            raise ValueError(f"fazy {name}: średnia faz ≠ wynik dziennika (maks. {diff.max():.3g})")
    for name, e in expected.items():
        if set(e.index) - set(g.loc[g["skladowa"] == name, "date"]):
            raise ValueError(f"fazy {name}: brak dni wyniku")


def expected_results(res: pd.DataFrame, res_x1: pd.DataFrame | None) -> dict[str, pd.Series]:
    """
    Wynik składowych po dacie (tekst) z przeliczenia TEGO przebiegu — to, co przebieg dopisuje do
    `wyniki.csv` / `x1_wyniki.csv` przy nowym dniu. Dla dni już zapisanych plik ma pierwszeństwo
    (append-only), więc przy „historia zmieniona” > 0 plik może się różnić od tej serii.
    """
    days = res["date"].to_numpy()
    out = {
        "trend": pd.Series(res["r_trend"].to_numpy(dtype=float), index=days),
        "coinbase": pd.Series(res["r_coinbase"].to_numpy(dtype=float), index=days),
    }
    if res_x1 is not None:
        out["x1"] = pd.Series(res_x1["r_x1"].to_numpy(dtype=float), index=res_x1["date"].to_numpy())
    return out


def component_breakdown(
    engines: dict, name: str, res: pd.DataFrame, res_x1: pd.DataFrame | None, expected: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    (`rozbicie.csv`, `fazy.csv`) jednej składowej (`trend` / `coinbase` na dni `res`, `x1` na dni
    `res_x1`) z ramek silnika tego przebiegu; obie kontrole przed zwrotem — niezgodność = ValueError.
    """
    if name == "x1":
        panels = x1_panels(engines["x1_phases"])
        rb = x1_breakdown(panels, res_x1["date"])
        fz = phase_rows(dict(panels["r_net"].items()), "x1", res_x1["date"])
    else:
        rb = ts_breakdown(engines[name], name, res["date"])
        per = {ph: f["net"] for ph, f in enumerate(engines[f"{name}_phases"])}
        fz = phase_rows(per, name, res["date"])
    rb = rb.astype({c: float for c in BREAKDOWN_VALUES if c != "likwidacje"})
    own = {name: expected[name]}
    check_breakdown(rb, own)
    check_phases(fz, own)
    return rb, fz


def breakdown_and_phases(
    engines: dict,
    res: pd.DataFrame,
    res_x1: pd.DataFrame | None,
    errors: dict[str, Exception] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    (`rozbicie.csv`, `fazy.csv`) z ramek silnika zebranych w tym przebiegu (`components`, `run_x1`)
    na dni wyniku: trend i premia od `JOURNAL_START`, X1 od `X1_START` (gdy X1 policzone). Każda
    składowa liczona i sprawdzana osobno (`component_breakdown`). Bez `errors` pierwszy błąd
    przerywa (ValueError); z `errors` (słownik) błąd składowej trafia do niego (składowa → wyjątek),
    a ta składowa jest pominięta — pozostałe zapisują się normalnie (błąd X1 nie blokuje trendu).
    """
    expected = expected_results(res, res_x1)
    names = ["trend", "coinbase"] + (["x1"] if res_x1 is not None else [])
    rb, fz = [], []
    for name in names:
        try:
            r, f = component_breakdown(engines, name, res, res_x1, expected)
        except Exception as exc:  # noqa: BLE001 — izolacja składowej tylko na życzenie (`errors`)
            if errors is None:
                raise
            errors[name] = exc
            continue
        if len(r):
            rb.append(r)
        if len(f):
            fz.append(f)
    rows_rb = pd.concat(rb, ignore_index=True) if rb else pd.DataFrame(columns=BREAKDOWN_COLS)
    rows_fz = pd.concat(fz, ignore_index=True) if fz else pd.DataFrame(columns=PHASE_COLS)
    rows_rb = rows_rb.sort_values(BREAKDOWN_KEY, kind="stable").reset_index(drop=True)
    rows_fz = rows_fz.sort_values(PHASE_KEY, kind="stable").reset_index(drop=True)
    return rows_rb, rows_fz


def error_text(exc: Exception, limit: int = 120) -> str:
    """Opis błędu do wydruku: „<typ>: <komunikat>” (komunikat skrócony do `limit` znaków)."""
    return f"{type(exc).__name__}: {str(exc)[:limit]}"


def basket_rows(
    volume: pd.DataFrame,
    funding: pd.DataFrame,
    members: dict,
    months: list[pd.Timestamp],
    depth: int = BASKET_DEPTH,
) -> pd.DataFrame:
    """
    Rejestr uniwersum (`koszyk.csv`): na początek każdego miesiąca z `months` ranking obrotu
    1–`depth` (`rebalance_premium.monthly_ranking` — miara `monthly_members`: średni obrót 30 dni,
    ≥ 30 dni historii), `czlonek_top20` = w koszyku silnika (`members`), `ma_funding` = ≥ 1
    rozliczenie fundingu w oknie 30 dni przed początkiem miesiąca w danych przebiegu.
    `sredni_obrot_30d` w pliku zaokrąglony do 1 USDT: liczba całkowita przechodzi przez CSV bez
    błędu ostatniego bitu (float rzędu 1e8 nie — powtórka dałaby fałszywą „historię zmienioną”).
    Top-20 rankingu ≠ skład koszyka silnika = ValueError.
    """
    ranking = monthly_ranking(volume, months, depth)
    rows = []
    for m in months:
        ranked = ranking[m]
        if sorted(s for s, _ in ranked[:TOP_N]) != list(members[m]):
            raise ValueError(f"koszyk {m:%Y-%m}: top-{TOP_N} rankingu ≠ skład koszyka silnika")
        win = funding.loc[
            (funding.index >= m - pd.Timedelta(days=VOLUME_LOOKBACK_DAYS)) & (funding.index < m)
        ]
        for pos, (sym, vol) in enumerate(ranked, start=1):
            rows.append(
                {
                    "miesiac": m.strftime("%Y-%m"),
                    "symbol": sym,
                    "pozycja": pos,
                    "sredni_obrot_30d": int(round(vol)),
                    "czlonek_top20": sym in members[m],
                    "ma_funding": bool(sym in win.columns and win[sym].notna().any()),
                }
            )
    return pd.DataFrame(rows, columns=BASKET_COLS)


def basket_months(as_of: pd.Timestamp, start: pd.Timestamp | None = None) -> list[pd.Timestamp]:
    """Miesiące rejestru koszyka: od miesiąca startu dziennika (`JOURNAL_START`) do `as_of`."""
    start = JOURNAL_START if start is None else start
    first = start.normalize() - pd.Timedelta(days=start.day - 1)
    return [m for m in _months(as_of) if m >= first]


def append_safe(
    path: Path,
    rows: pd.DataFrame | None,
    key: list[str],
    value_cols: list[str],
    error: str | None = None,
    details: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    `append_rows` dla plików tylko do zapisu (poprawka 11): zwraca (tekst do logu, „historia
    zmieniona”). Błąd liczenia (`error`) albo zapisu → („BŁĄD <typ>”, []) — dziennik idzie dalej;
    komunikat błędu zapisu trafia do `details` (wydruk), log zostaje krótki.
    """
    if error is not None:
        return error, []
    try:
        n, changed = append_rows(path, rows, key, value_cols)
    except Exception as exc:  # noqa: BLE001 — plik tylko do zapisu nie zatrzymuje dziennika
        if details is not None:
            details.append(f"zapis {path.name}: {error_text(exc)}")
        return f"BŁĄD {type(exc).__name__}", []
    return f"+{n}", changed


def summarize_p11(rb_txt: str, fz_txt: str, ks_txt: str, details: list[str] | None = None) -> str:
    """
    Linia do wydruku (poprawka 11, tylko zapis) + po jednej linii na błąd z komunikatem (`details`:
    „gdzie: <typ>: <komunikat>”) — log ma tylko „BŁĄD <typ>”, komunikat jest tu (jak X1 i opisy).
    """
    line = (
        f"  Rozbicie zwrotu, fazy, koszyk (poprawka 11, tylko zapis): rozbicie {rb_txt}, "
        f"fazy {fz_txt}, koszyk {ks_txt}"
    )
    return "\n".join([line] + [f"    BŁĄD {d}" for d in details or []])


def with_errors(txt: str, errors: dict[str, Exception]) -> str:
    """Pole logu + składowe pominięte przez błąd: „+N (x1 BŁĄD ValueError)”; bez błędów bez zmian."""
    if not errors or txt.startswith("BŁĄD"):
        return txt
    return f"{txt} (" + ", ".join(f"{n} BŁĄD {type(e).__name__}" for n, e in errors.items()) + ")"


# ------------------------------------------------------------------ przebieg
def run(fetch: bool = True, live_dir: Path = LIVE_DIR, journal_dir: Path = JOURNAL_DIR) -> str:
    started = pd.Timestamp.now(tz="UTC")
    if fetch:
        from data.fetch_live import run as fetch_run

        fetch_run(live_dir)
    cfg = load_config()
    fee = cfg["costs"]["taker_fee_rate"] + cfg["costs"]["slippage_bps"] / 10_000.0
    data = load_live(live_dir)
    last = {
        "binance": data["close"][BTC].last_valid_index(),  # BTC: obie składowe go potrzebują
        "coinbase_premia": data["premium"].index.max(),
    }
    as_of = min(last.values())
    engines: dict = {}  # poprawka 11: ramki silnika tego przebiegu (tylko do zapisu rozbicia)
    pos, k, hist, rets = positions(data, as_of, fee, engines)
    res = journal_rows(hist, rets)
    n_sig, ch_sig = append_rows(
        journal_dir / "sygnaly.csv",
        pos[
            [
                "as_of",
                "component",
                "phase",
                "formed",
                "today",
                "symbol",
                "sign",
                "weight",
                "k",
                "exposure",
                "margin",
            ]
        ],
        ["as_of", "component", "phase", "symbol"],
        ["sign", "weight", "k"],
    )
    n_res, ch_res = append_rows(
        journal_dir / "wyniki.csv",
        res,
        ["date"],
        ["r_trend", "r_coinbase", "r_port", "k_trend", "k_coinbase"],
    )
    # X1 osobno: jego błąd nie może zatrzymać dziennika głównego (kompletność liczona z logu)
    try:
        n_sig_x1, n_res_x1, ch_x1, eq_x1, dd_x1, pos_x1 = run_x1(
            data, as_of, fee, journal_dir, engines
        )
        status_x1 = stop_status(dd_x1, X1_WARN_DD, X1_STOP_DD)
        text_x1 = summarize_x1(pos_x1, eq_x1, dd_x1, status_x1)
    except Exception as exc:  # noqa: BLE001 — zapis błędu zamiast przerwania przebiegu
        n_sig_x1 = n_res_x1 = 0
        ch_x1, eq_x1, dd_x1 = [], float("nan"), float("nan")
        status_x1 = f"BŁĄD {type(exc).__name__}: {str(exc)[:120]}"
        text_x1 = f"  X1: {status_x1} (dziennik główny zapisany normalnie)"
    # etykieta stanu rynku (poprawka 7): osobny plik, błąd nie zatrzymuje dziennika
    try:
        n_st, ch_st = append_rows(
            journal_dir / "stan_rynku.csv",
            market_state(truncate(data, as_of)["close"][BTC]),
            ["date"],
            ["btc_vol30", "btc_r90"],
        )
    except (
        Exception
    ) as exc:  # noqa: BLE001 — błąd etykiety tylko do logu, nie jako „historia zmieniona”
        n_st, ch_st = f"BŁĄD {type(exc).__name__}", []
    st_txt = n_st if isinstance(n_st, str) else f"+{n_st}"
    # etykieta Fear & Greed (poprawka 8): osobny plik; brak pliku lub błąd tylko do logu
    try:
        fng_path = Path(live_dir) / FNG_FILE
        if fng_path.exists():
            rows_fg = fng_rows(pd.read_parquet(fng_path))
            n_fg, ch_fg = append_rows(
                journal_dir / "fng.csv", rows_fg, ["date"], ["fng", "fng_etykieta"]
            )
        else:
            rows_fg, n_fg, ch_fg = None, "brak pliku", []
    except Exception as exc:  # noqa: BLE001 — jak stan rynku: etykieta nie zatrzymuje dziennika
        rows_fg, n_fg, ch_fg = None, f"BŁĄD {type(exc).__name__}", []
    fg_txt = n_fg if isinstance(n_fg, str) else f"+{n_fg}"
    # lista transakcji (poprawka 9): zamknięte append-only, otwarte nadpisywane; błąd tylko do logu
    try:
        tr_closed, tr_open = trade_ledger(data, as_of, hist, k)
        n_tr, ch_tr = append_rows(
            journal_dir / "transakcje.csv",
            tr_closed,
            TRADE_KEY,
            [
                "cena_wejscia",
                "cena_wyjscia",
                "wielkosc_proc_kapitalu",
                "data_wyjscia",
                "powod_wyjscia",
            ],
        )
        journal_dir.mkdir(parents=True, exist_ok=True)
        tr_open.to_csv(journal_dir / "transakcje_otwarte.csv", index=False)
        tr_txt = f"+{n_tr}"
    except Exception as exc:  # noqa: BLE001 — lista transakcji nie zatrzymuje dziennika
        tr_closed, tr_open, ch_tr, tr_txt = None, None, [], f"BŁĄD {type(exc).__name__}"
    # opisy strategii (poprawka 10): zawsze w raporcie i w strategie.csv; błąd tylko do logu
    try:
        book = strategy_book()
        journal_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(strategy_rows(book)).to_csv(journal_dir / "strategie.csv", index=False)
        text_str, str_txt = summarize_strategies(book), f"{len(book)}"
    except Exception as exc:  # noqa: BLE001 — opis nie zatrzymuje dziennika
        text_str = f"  STRATEGIE AKTYWNE: BŁĄD opisu {type(exc).__name__}: {str(exc)[:120]}"
        str_txt = f"BŁĄD {type(exc).__name__}"
    # rozbicie zwrotu, fazy, koszyk (poprawka 11): tylko zapis, każdy plik osobno; błąd tylko do logu
    # (każda składowa rozbicia osobno: błąd X1 nie blokuje trendu i premii; komunikat → wydruk)
    p11_err: list[str] = []
    comp_err: dict[str, Exception] = {}
    try:
        rows_rb, rows_fz = breakdown_and_phases(engines, res, engines.get("x1_res"), comp_err)
        err_rf = None
    except Exception as exc:  # noqa: BLE001 — rozbicie nie zatrzymuje dziennika
        rows_rb = rows_fz = None
        err_rf = f"BŁĄD {type(exc).__name__}"
        p11_err.append(f"rozbicie/fazy: {error_text(exc)}")
    p11_err += [f"rozbicie/fazy {n}: {error_text(e)}" for n, e in comp_err.items()]
    rb_txt, ch_rb = append_safe(
        journal_dir / "rozbicie.csv", rows_rb, BREAKDOWN_KEY, BREAKDOWN_VALUES, err_rf, p11_err
    )
    fz_txt, ch_fz = append_safe(
        journal_dir / "fazy.csv", rows_fz, PHASE_KEY, ["netto"], err_rf, p11_err
    )
    rb_txt, fz_txt = with_errors(rb_txt, comp_err), with_errors(fz_txt, comp_err)
    try:
        d_now = truncate(data, as_of)
        rows_ks = basket_rows(
            d_now["volume"], d_now["funding"], engines["members"], basket_months(as_of)
        )
        err_ks = None
    except Exception as exc:  # noqa: BLE001 — rejestr koszyka nie zatrzymuje dziennika
        rows_ks, err_ks = None, f"BŁĄD {type(exc).__name__}"
        p11_err.append(f"koszyk: {error_text(exc)}")
    ks_txt, ch_ks = append_safe(
        journal_dir / "koszyk.csv", rows_ks, BASKET_KEY, BASKET_VALUES, err_ks, p11_err
    )
    dd = float(res["drawdown"].iloc[-1]) if len(res) else 0.0
    eq = float(res["equity"].iloc[-1]) if len(res) else 1.0
    status = stop_status(dd)
    changed = ch_sig + ch_res + ch_x1 + ch_st + ch_fg + ch_tr + ch_rb + ch_fz + ch_ks
    late = (started.normalize() - as_of).days > 1
    summary = (
        summarize(pos, k, as_of, eq, dd, status, late, changed, last)
        + "\n"
        + text_x1
        + "\n"
        + summarize_fng(rows_fg, fg_txt)
        + "\n"
        + summarize_trades(tr_closed, tr_open, tr_txt)
        + "\n"
        + text_str
        + "\n"
        + summarize_p11(rb_txt, fz_txt, ks_txt, p11_err)
    )
    log = (
        f"{started.isoformat()} | as_of {as_of.date()} | binance {last['binance'].date()} | "
        f"premia {last['coinbase_premia'].date()} | sygnały +{n_sig} | wyniki +{n_res} | "
        f"kapitał {eq:.4f} | obsunięcie {100 * dd:.1f}% | {status} | "
        f"X1 sygnały +{n_sig_x1} wyniki +{n_res_x1} kapitał {eq_x1:.4f} "
        f"obsunięcie {100 * dd_x1:.1f}% {status_x1} | stan rynku {st_txt} | F&G {fg_txt} | "
        f"transakcje {tr_txt} | opisy strategii {str_txt} | rozbicie {rb_txt} | fazy {fz_txt} | "
        f"koszyk {ks_txt} | historia zmieniona: {len(changed)}\n"
    )
    journal_dir.mkdir(parents=True, exist_ok=True)
    with open(journal_dir / "przebiegi.log", "a", encoding="utf-8") as f:
        f.write(log)
    return summary


def summarize(pos, k, as_of, eq, dd, status, late, changed, last) -> str:
    lines = [
        f"DZIENNIK — pozycje na {(as_of + pd.Timedelta(days=1)).date()} (dane do zamknięcia {as_of.date()})",
        f"  mnożniki R1: trend {k['trend']:.2f}, premia Coinbase {k['coinbase']:.2f}",
        f"  wynik papierowy od {JOURNAL_START.date()}: kapitał {eq:.4f} ({100 * (eq - 1):+.2f} %), "
        f"obsunięcie {100 * dd:.1f} % → {status} (ostrzeżenie od {100 * WARN_DD:.1f} %, STOP od {100 * STOP_DD:.1f} %)",
    ]
    if late:
        lines.append("  UWAGA: dane spóźnione — ostatnia zamknięta świeca starsza niż wczoraj")
    if changed:
        lines.append(
            f"  UWAGA: HISTORIA ZMIENIONA w {len(changed)} polach (zapis bez zmian): {changed[:5]}"
        )
    for comp, name in (("trend", "TREND (2×)"), ("coinbase", "PREMIA COINBASE (3×)")):
        p = pos[pos["component"] == comp]
        agg = p.groupby("symbol")["exposure"].sum().sort_values()
        lines.append(
            f"  {name}: ekspozycja netto {agg.sum():+.2f}× kapitału, brutto {agg.abs().sum():.2f}×, "
            f"depozyt {100 * p['margin'].sum():.1f} % kapitału (fazy osobno, jak SZ1; "
            f"po skompensowaniu faz {100 * agg.abs().sum() / (LEV_TREND if comp == 'trend' else LEV_CB):.1f} %)"
        )
        today = p[p["today"]]
        if len(today):
            lines.append(
                f"    dziś formowana faza {int(today['phase'].iloc[0])}: "
                + ", ".join(
                    f"{'LONG' if r.sign > 0 else 'SHORT'} {r.symbol} {100 * abs(r.exposure):.1f}%"
                    for r in today.sort_values("exposure").itertuples()
                )
            )
    return "\n".join(lines)


def run_x1(
    data: dict, as_of: pd.Timestamp, fee: float, journal_dir: Path, engines: dict | None = None
) -> tuple:
    """
    Pozycje i wynik X1 do `as_of` + zapis `x1_sygnaly.csv` / `x1_wyniki.csv` (append-only).
    `engines` (poprawka 11): po udanym zapisie dostaje ramki 7 faz i wiersze wyniku X1.
    """
    d = truncate(data, as_of)
    phases: list[pd.DataFrame] = []
    r_x1, pos_x1 = x1_component(
        d["close"],
        d["funding"],
        monthly_members(d["volume"], _months(as_of)),
        as_of,
        as_of + pd.Timedelta(days=1),
        fee,
        phases_out=phases,
    )
    pos_x1.insert(0, "as_of", as_of.date().isoformat())
    res_x1 = x1_rows(r_x1)
    n_sig, ch_sig = append_rows(
        journal_dir / "x1_sygnaly.csv", pos_x1, ["as_of", "phase", "symbol"], ["sign", "weight"]
    )
    n_res, ch_res = append_rows(journal_dir / "x1_wyniki.csv", res_x1, ["date"], ["r_x1"])
    if engines is not None:
        engines.update(x1_phases=phases, x1_res=res_x1)
    dd = float(res_x1["drawdown"].iloc[-1]) if len(res_x1) else 0.0
    eq = float(res_x1["equity"].iloc[-1]) if len(res_x1) else 1.0
    return n_sig, n_res, ch_sig + ch_res, eq, dd, pos_x1


def summarize_fng(rows: pd.DataFrame | None, txt: str) -> str:
    """Jedna linia do wydruku: ostatnia opublikowana wartość Fear & Greed (poprawka 8, tylko zapis)."""
    if rows is None or not len(rows):
        return f"  Fear & Greed (poprawka 8, tylko zapis): {txt}"
    last = rows.iloc[-1]
    return (
        f"  Fear & Greed (poprawka 8, tylko zapis): {last['date']} = {int(last['fng'])} "
        f"({last['fng_etykieta']}); dopisane {txt}"
    )


def summarize_x1(pos: pd.DataFrame, eq: float, dd: float, status: str) -> str:
    lines = [
        f"  X1 (papierowo, osobno, poza R1; od {X1_START.date()}): kapitał {eq:.4f} ({100 * (eq - 1):+.2f} %), "
        f"obsunięcie {100 * dd:.1f} % → {status} (ostrzeżenie od {100 * X1_WARN_DD:.1f} %, "
        f"STOP od {100 * X1_STOP_DD:.1f} %)",
    ]
    agg = pos.groupby("symbol")["weight"].sum()
    lines.append(
        f"    ekspozycja netto {agg.sum():+.2f}× kapitału X1, brutto {agg.abs().sum():.2f}× "
        f"(fazy po skompensowaniu; bez dźwigni, jak w backteście)"
    )
    today = pos[pos["today"]]
    if len(today):
        lines.append(
            f"    dziś formowana faza {int(today['phase'].iloc[0])}: "
            + ", ".join(
                f"{'LONG' if r.sign > 0 else 'SHORT'} {r.symbol} {100 * abs(r.weight):.1f}%"
                for r in today.sort_values(["sign", "symbol"], ascending=[False, True]).itertuples()
            )
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(run(fetch="--bez-pobierania" not in sys.argv[1:]))
