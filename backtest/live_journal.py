"""
live_journal.py — dziennik na żywo (papierowo) portfela z rundy SZ1: trend tygodniowy TS1 na
koszyku top-20 (likwidacja izolowana 2×) + premia Coinbase CP1 na BTC (likwidacja izolowana 3×),
połączone regułą R1 (budżet ryzyka: cel 20 %/rok, sufit 2, bez hamulca). Reguły ZAMROŻONE
w `dziennik/README.md` (pre-rejestracja dziennika); silnik ten sam co w rundach
(`ts_momentum.portfolio`, `run_coinbase_cp1.daily_premium/premium_signal`, `sizing.apply_rules`).

Po co: sprawdzian MECHANIKI na 2–3 miesiące (czy sygnał liczy się na czas, czy dane są kompletne,
czy wynik papierowy zgadza się z przeliczeniem), nie dowód przewagi (wniosek 80, `runs/INDEX.md`).

Zasady zapisu (`dziennik/`):
- `sygnaly.csv` — pozycje ogłoszone PRZED wynikiem: dopisywane raz na dzień `as_of` (ostatnia
  zamknięta świeca), nigdy nadpisywane; ponowny przebieg tego samego dnia niczego nie dubluje;
- `wyniki.csv` — dzienny wynik papierowy od `JOURNAL_START`; istniejące wiersze NIE są zmieniane —
  gdy przeliczenie daje inną wartość (rewizja danych, zmiana kodu), przebieg zgłasza „HISTORIA
  ZMIENIONA” i zostawia stary zapis;
- `przebiegi.log` — czas przebiegu, ostatnia świeca każdego źródła, status progów.

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
from backtest.rebalance_premium import monthly_members
from backtest.run_coinbase_cp1 import daily_premium, premium_signal
from backtest.sizing import apply_rules
from backtest.ts_momentum import (
    PHASES,
    build_formations,
    ewma_vol,
    formation_dates,
    portfolio,
    signal_sign,
)
from backtest.xs_momentum import daily_funding_panel

LIVE_DIR = Path("data/raw/live")
JOURNAL_DIR = Path("dziennik")
ENGINE_START = pd.Timestamp("2025-09-01", tz="UTC")  # pierwszy miesiąc silnika (rozbieg R1 ≥ 1 rok)
JOURNAL_START = pd.Timestamp("2026-09-24", tz="UTC")  # pierwszy dzień wyniku (poprawka 1, README)
LEV_TREND, LEV_CB, MMR = 2.0, 3.0, 0.01
WARN_DD = 0.177  # największe obsunięcie R1 w historii (SZ1)
STOP_DD = 0.265  # 1,5 × powyższe — zapisane z góry
BTC = "BTCUSDT"
TOL = 1e-9


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


def components(data: dict, as_of: pd.Timestamp, fee: float) -> tuple[pd.DataFrame, dict]:
    """Dzienne zwroty netto składowych (k = 1) do `as_of` + wejścia silnika (do pozycji)."""
    d = truncate(data, as_of)
    end = as_of + pd.Timedelta(days=1)
    members = monthly_members(d["volume"], _months(as_of))
    liq = {"high": d["high"], "low": d["low"], "lev": LEV_TREND, "mmr": MMR}
    tr, _ = portfolio(d["close"], d["funding"], members, ENGINE_START, end, fee, liq=liq)
    close_b = d["close"][[BTC]]
    signs_b = pd.DataFrame({BTC: premium_signal(d["premium"]).reindex(close_b.index)})
    mem_b = {m: [BTC] for m in members}
    liq_b = {"high": d["high"][[BTC]], "low": d["low"][[BTC]], "lev": LEV_CB, "mmr": MMR}
    cb, _ = portfolio(
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


def positions(data: dict, as_of: pd.Timestamp, fee: float) -> tuple:
    """Pozycje na dzień po `as_of` (obie składowe, po mnożnikach R1), mnożniki, historia R1, zwroty."""
    rets, ctx = components(data, as_of, fee)
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


def stop_status(drawdown: float) -> str:
    if drawdown >= STOP_DD:
        return "STOP"
    if drawdown >= WARN_DD:
        return "OSTRZEŻENIE"
    return "OK"


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
    pos, k, hist, rets = positions(data, as_of, fee)
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
    dd = float(res["drawdown"].iloc[-1]) if len(res) else 0.0
    eq = float(res["equity"].iloc[-1]) if len(res) else 1.0
    status = stop_status(dd)
    late = (started.normalize() - as_of).days > 1
    summary = summarize(pos, k, as_of, eq, dd, status, late, ch_sig + ch_res, last)
    log = (
        f"{started.isoformat()} | as_of {as_of.date()} | binance {last['binance'].date()} | "
        f"premia {last['coinbase_premia'].date()} | sygnały +{n_sig} | wyniki +{n_res} | "
        f"kapitał {eq:.4f} | obsunięcie {100 * dd:.1f}% | {status} | "
        f"historia zmieniona: {len(ch_sig) + len(ch_res)}\n"
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


if __name__ == "__main__":
    print(run(fetch="--bez-pobierania" not in sys.argv[1:]))
