"""Testy poprawki 13 dziennika (zadanie 025): moneta wstrzymana lub wycofana — bez sieci, na danych
syntetycznych jak `zadania/025-dowody/dowod_syntetyczny.py` (scenariusze: baza, wycofanie, krach,
zamrożenie, zanik pliku).

Reguły: R1 wykrycie (brak świecy przy świecy BTC, obrót 0 albo open = high = low = close, status ≠
TRADING), R2 cena rozliczenia (mark z dnia wykrycia, bez niej ostatnie normalne zamknięcie
„przybliżona”), R3 likwidacja trendu na ekstremach mark, R4 brak nowych pozycji, R5 dni z obrotem 0
poza historią koszyka, R6 zapis („wycofanie”, pole logu „wstrzymane: …”), R7 alarm przy zniknięciu
pliku członka koszyka. Data wejścia (`POPRAWKA13_OD`) zawsze przez `monkeypatch`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from backtest import live_journal as lj
from backtest.negative_control import synthetic_ohlc, synthetic_returns
from backtest.ts_momentum import build_formations, ewma_vol, formation_dates
from backtest.xs_momentum import _month_of, signal_panel
from data import fetch_live
from tools import strona_dziennika as sd

FEE = 0.0007
D = pd.Timestamp("2026-08-20", tz="UTC")  # dzień zdarzenia (pierwszy dzień bez normalnej świecy)
START = pd.Timestamp("2026-08-01", tz="UTC")  # start wyniku i data wejścia poprawki w testach
DEAD, FROZ = "C01USDT", "C02USDT"
DAY = pd.Timedelta(days=1)


# ------------------------------------------------------------------ dane syntetyczne
def _write(
    out: Path,
    scenario: str = "baza",
    n_days: int = 480,
    n_coins: int = 22,
    start: str = "2025-06-01",
    event: pd.Timestamp = D,
    seed: int = 3,
) -> None:
    """Katalog jak `data/raw/live` (jak `dowod_syntetyczny.write_live`): świece 1d (open/high/low/close/
    obrót), funding 8h, Coinbase 1d, spot 8h. C01 i C02 mają największy obrót (zawsze w koszyku).
    Scenariusze od dnia `event`: „wycofanie” (C01: koniec świec i fundingu), „krach” (C01: −90 %,
    handel trwa), „zamrozenie” (C02: open = high = low = close = ostatnie zamknięcie, obrót 0),
    „luka” (C01: brak jednej świecy w dniu `event`), „obrot0” (C01: obrót 0 jednego dnia, ceny ruchome).
    """
    out.mkdir(parents=True, exist_ok=True)
    r = synthetic_returns(n_days, n_coins, seed=seed, start=start)
    r.columns = ["BTCUSDT"] + [f"C{i:02d}USDT" for i in range(1, n_coins)]
    o = synthetic_ohlc(r, seed=seed)
    rng = np.random.default_rng(seed)
    idx = r.index
    for c in r.columns:
        vol = rng.uniform(1e6, 1e8, n_days)
        if c == DEAD:
            vol = np.full(n_days, 2e10)
        if c == FROZ:
            vol = np.full(n_days, 1.5e10)
        df = pd.DataFrame(
            {
                "open_time": idx,
                "open": o["open"][c].to_numpy(),
                "high": o["high"][c].to_numpy(),
                "low": o["low"][c].to_numpy(),
                "close": o["close"][c].to_numpy(),
                "quote_volume": vol,
            }
        )
        ts = pd.date_range(idx[0], periods=3 * n_days, freq="8h")
        fu = pd.DataFrame({"timestamp": ts, "funding_rate": 1e-4})
        after = df["open_time"] >= event
        if c == DEAD and scenario == "wycofanie":
            df = df[~after]
            fu = fu[fu["timestamp"] < event]
        if c == DEAD and scenario == "krach":
            prev = float(df.loc[~after, "close"].iloc[-1])
            df.loc[after, ["open", "high", "low", "close"]] = (
                df.loc[after, ["open", "high", "low", "close"]] * 0.1
            )
            df.loc[df["open_time"] == event, ["open", "high"]] = prev
        if c == FROZ and scenario == "zamrozenie":
            last = float(df.loc[~after, "close"].iloc[-1])
            df.loc[after, ["open", "high", "low", "close"]] = last
            df.loc[after, "quote_volume"] = 0.0
        if c == DEAD and scenario == "luka":
            df = df[df["open_time"] != event]
        if c == DEAD and scenario == "obrot0":
            df.loc[df["open_time"] == event, "quote_volume"] = 0.0
        df.to_parquet(out / f"{c}_1d.parquet", index=False)
        fu.to_parquet(out / f"{c}_funding.parquet", index=False)
    btc = o["close"]["BTCUSDT"]
    prem = 1.0 + 0.001 * np.sin(np.arange(n_days) / 9.0)
    pd.DataFrame({"open_time": idx, "close": btc.to_numpy() * prem}).to_parquet(
        out / "coinbase_BTC-USD_1d.parquet", index=False
    )
    ts8 = pd.date_range(idx[0], periods=3 * n_days, freq="8h")
    pd.DataFrame({"timestamp": ts8, "close": np.repeat(btc.to_numpy(), 3)}).to_parquet(
        out / "spot_BTC-USDT_8h.parquet", index=False
    )
    ts_cm = pd.date_range("2026-09-01", "2026-09-24", freq="8h", tz="UTC")  # jak `_write_live`
    pd.DataFrame({"timestamp": ts_cm, "funding_rate": 1e-4}).to_parquet(
        out / lj.CARRY_FILE, index=False
    )


def _krach_candle(src_krach: Path, day: pd.Timestamp = D) -> pd.Series:
    """Świeca C01 z dnia `day` w scenariuszu „krach” — prawda, której dziennik bez świecy nie widzi."""
    k = pd.read_parquet(src_krach / f"{DEAD}_1d.parquet")
    k["open_time"] = pd.to_datetime(k["open_time"], utc=True)
    return k.set_index("open_time").loc[day]


def _write_mark(out: Path, rows: list[tuple]) -> None:
    """Plik ceny mark jak z `fetch_live.fetch_mark_safe`: (symbol, dzień, open, high, low, close)."""
    pd.DataFrame(
        [
            {
                "symbol": s,
                "open_time": pd.Timestamp(t),
                "open": o,
                "high": h,
                "low": lo,
                "close": c,
            }
            for s, t, o, h, lo, c in rows
        ]
    ).to_parquet(out / fetch_live.MARK_FILE, index=False)


def _write_status(out: Path, rows: dict[str, tuple[str, str | None]]) -> None:
    """Plik statusów jak z `fetch_live.save_statuses_safe` (symbol → (status, deliveryDate albo None))."""
    info = {
        "symbols": [
            {
                "symbol": s,
                "quoteAsset": "USDT",
                "status": stt,
                "contractType": "PERPETUAL",
                "deliveryDate": (int(pd.Timestamp(dd).value // 1_000_000) if dd else 4133404800000),
            }
            for s, (stt, dd) in rows.items()
        ]
    }
    fetch_live.contract_statuses(info).to_parquet(out / fetch_live.STATUS_FILE, index=False)


def _on(monkeypatch, od=START, start=START):
    monkeypatch.setattr(lj, "POPRAWKA13_OD", od)
    monkeypatch.setattr(lj, "JOURNAL_START", start)
    monkeypatch.setattr(lj, "X1_START", start)


@pytest.fixture(scope="module")
def dirs(tmp_path_factory):
    """Scenariusze z dowodu kroku 1 (480 dni do 2026-09-23) + wycofanie z ceną mark = świeca krachu."""
    root = tmp_path_factory.mktemp("p13")
    out = {}
    for sc in ("baza", "wycofanie", "krach", "zamrozenie"):
        _write(root / sc, sc)
        out[sc] = root / sc
    _write(root / "wycofanie_mark", "wycofanie")
    k = _krach_candle(out["krach"])
    _write_mark(root / "wycofanie_mark", [(DEAD, D, k["open"], k["high"], k["low"], k["close"])])
    _write_status(root / "wycofanie_mark", {DEAD: ("SETTLING", "2026-08-20 09:00")})
    out["wycofanie_mark"] = root / "wycofanie_mark"
    return out


# ------------------------------------------------------------------ R1: wykrycie
def test_halt_conditions_three_signals_and_no_false_alarms():
    idx = pd.date_range("2026-08-01", periods=8, freq="D", tz="UTC")
    close = pd.DataFrame(
        {"BTCUSDT": 100.0, "A": 10.0 + np.arange(8), "B": 5.0, "N": np.nan, "S": 3.0}, index=idx
    )
    close.loc[idx[5:], "A"] = np.nan  # (a) koniec świec
    close.loc[idx[:3], "N"] = np.nan  # nowa moneta: brak świec PRZED notowaniem to nie wstrzymanie
    close.loc[idx[3:], "N"] = 7.0 + np.arange(5)
    close.loc[idx[6:], "S"] = np.nan
    high, low = close * 1.01, close * 0.99
    opn = close * 1.001
    vol = close * 0 + 1e6  # NaN tam, gdzie brak świecy
    opn.loc[idx[2], "B"] = high.loc[idx[2], "B"] = low.loc[idx[2], "B"] = 5.0  # (b) cena stoi
    vol.loc[idx[4], "B"] = 0.0  # (b) obrót 0 (ceny ruchome)
    vol.loc[idx[1], "BTCUSDT"] = 0.0  # BTC nie podlega regule
    status = pd.DataFrame(
        {"status": ["TRADING", "SETTLING"], "contract_type": "PERPETUAL", "delivery": pd.NaT},
        index=["A", "S"],
    )
    d = {"close": close, "open": opn, "high": high, "low": low, "volume": vol, "status": status}
    raw = lj.halt_conditions(d)
    assert "BTCUSDT" not in raw.columns
    assert list(raw.index[raw["A"]]) == list(idx[5:])
    assert list(raw.index[raw["B"]]) == [idx[2], idx[4]]
    assert not raw["N"].any()
    assert list(raw.index[raw["S"]]) == list(idx[6:])
    # (c) status ≠ TRADING bez świecy w tabeli (np. symbol usunięty z exchangeInfo) = dni po ostatniej świecy
    d2 = dict(d, status=status.loc[["S"]])
    assert list(lj.halt_conditions(d2).index[lj.halt_conditions(d2)["A"]]) == list(idx[5:])
    # dzień bez świecy BTC (np. przerwa danych giełdy) nie jest wstrzymaniem monety
    close2 = close.copy()
    close2.loc[idx[7], "BTCUSDT"] = np.nan
    raw2 = lj.halt_conditions(dict(d, close=close2, status=None))
    assert not raw2.at[idx[7], "A"] and raw2.at[idx[6], "A"]


def test_halt_reason_names_the_signal():
    idx = pd.date_range("2026-08-01", periods=3, freq="D", tz="UTC")
    close = pd.DataFrame({"BTCUSDT": 1.0, "A": [1.0, np.nan, np.nan], "B": 2.0}, index=idx)
    vol = pd.DataFrame(
        {"BTCUSDT": 1.0, "A": [1.0, np.nan, np.nan], "B": [1.0, 0.0, 1.0]}, index=idx
    )
    st_ = pd.DataFrame({"status": ["SETTLING"]}, index=["A"])
    d = {"close": close, "volume": vol, "status": st_}
    assert lj._halt_reason(d, "A", idx[1]) == "status SETTLING"
    assert lj._halt_reason(dict(d, status=None), "A", idx[1]) == "brak świecy"
    assert lj._halt_reason(d, "B", idx[1]) == "obrót 0"
    assert lj._halt_reason(d, "B", idx[2]) == "open = high = low = close"


def _mini(n=40, coins=("A", "B")):
    """Minimalne dane do `halt_events`: BTC + monety, wszystkie członkami koszyka."""
    idx = pd.date_range("2026-08-01", periods=n, freq="D", tz="UTC")
    close = pd.DataFrame({"BTCUSDT": 100.0, **{c: 10.0 + np.arange(n) for c in coins}}, index=idx)
    d = {
        "close": close,
        "open": close * 1.001,
        "high": close * 1.02,
        "low": close * 0.98,
        "volume": close * 0 + 1e6,
        "funding": close * 0 + 1e-4,
        "status": pd.DataFrame(columns=["status", "contract_type", "delivery"]),
    }
    return d, {idx[0]: ["BTCUSDT", *coins]}


def test_halt_events_window_price_merge_and_legacy(monkeypatch):
    d, members = _mini()
    idx = d["close"].index
    # A: koniec świec od idx[10] (zdarzenie), B: seria zaczęta PRZED datą wejścia (dawne zasady)
    d["close"].loc[idx[10] :, "A"] = np.nan
    d["volume"].loc[idx[3:8], "B"] = 0.0
    # B: druga, krótka seria w oknie wyłączenia pierwszej (idx[20]) i trzecia po oknie (idx[30])
    d["volume"].loc[[idx[20], idx[23], idx[30]], "B"] = 0.0
    monkeypatch.setattr(lj, "POPRAWKA13_OD", idx[5])
    ev = {(e["symbol"], e["d1"]): e for e in lj.halt_events(d, members)}
    assert set(ev) == {("A", idx[10]), ("B", idx[20]), ("B", idx[30])}
    a = ev[("A", idx[10])]
    assert a["d2"] == idx[-1] and a["e"] == idx[-1]
    assert a["zrodlo"] == "przybliżona" and a["cena"] == d["close"].at[idx[9], "A"]
    b = ev[("B", idx[20])]
    # druga seria (idx[23]) w oknie [20, 26] przedłuża okno do max(26, 23), nie rozlicza drugi raz
    assert b["d2"] == idx[23] and b["e"] == idx[26]
    assert ev[("B", idx[30])]["e"] == idx[36]
    # ta sama seria A z ceną mark tego dnia → rozliczenie po mark, ekstrema do R3
    mk = pd.DataFrame({"A": [7.5]}, index=[idx[10]])
    d_m = dict(d, mark_close=mk, mark_high=mk * 1.1, mark_low=mk * 0.5)
    a_m = next(e for e in lj.halt_events(d_m, members) if e["symbol"] == "A")
    assert (a_m["cena"], a_m["zrodlo"]) == (7.5, "mark")
    assert a_m["mark_high"] == pytest.approx(8.25) and a_m["mark_low"] == pytest.approx(3.75)
    # wyłączona poprawka albo data wejścia po zdarzeniach = brak zdarzeń
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    assert lj.halt_events(d, members) == []
    monkeypatch.setattr(lj, "POPRAWKA13_OD", idx[-1] + DAY)
    assert lj.halt_events(d, members) == []


def test_apply_halts_panels_and_masks(monkeypatch):
    d, members = _mini()
    idx = d["close"].index
    d["close"].loc[idx[10] :, "A"] = np.nan
    monkeypatch.setattr(lj, "POPRAWKA13_OD", idx[0])
    mk = pd.DataFrame({"A": [7.5]}, index=[idx[10]])
    d = dict(d, mark_close=mk, mark_high=mk * 1.1, mark_low=mk * 0.5)
    ev = lj.halt_events(d, members)
    adj, excl, settle = lj.apply_halts(d, ev)
    a = adj["close"]["A"]
    assert (a.loc[idx[10] :] == 7.5).all() and a.loc[: idx[9]].equals(d["close"]["A"].loc[: idx[9]])
    assert adj["high"].at[idx[10], "A"] == pytest.approx(8.25)
    assert adj["low"].at[idx[10], "A"] == pytest.approx(3.75)
    assert (
        adj["high"]["A"].loc[idx[11] :].isna().all() and adj["low"]["A"].loc[idx[11] :].isna().all()
    )
    assert (adj["funding"]["A"].loc[idx[11] :] == 0).all()
    assert adj["funding"].at[idx[10], "A"] == 1e-4  # funding dnia wykrycia zostaje
    assert list(excl.index[excl["A"]]) == list(idx[10:]) and not excl["B"].any()
    assert list(settle.index[settle["A"]]) == [idx[10]]
    # dane wejściowe nietknięte, a bez zdarzeń panele = kopie wejścia
    assert d["close"]["A"].loc[idx[10] :].isna().all()
    same, ex0, se0 = lj.apply_halts(d, [])
    for k in ("close", "high", "low", "funding"):
        pd.testing.assert_frame_equal(same[k], d[k])
    assert not ex0.to_numpy().any() and not se0.to_numpy().any()


# ------------------------------------------------------------------ R5: koszyk
def test_basket_members_zero_volume_days_only_from_entry_date(monkeypatch):
    idx = pd.date_range("2026-06-01", "2026-09-30", freq="D", tz="UTC")
    rng = np.random.default_rng(1)
    vol = pd.DataFrame(
        {f"C{i:02d}USDT": rng.uniform(1e6, 1e7, len(idx)) for i in range(25)}, index=idx
    )
    vol["C00USDT"] = 1e9  # największy obrót…
    vol.loc[idx >= pd.Timestamp("2026-07-15", tz="UTC"), "C00USDT"] = 0.0  # …potem zamrożenie
    months = list(pd.date_range("2026-07-01", "2026-09-01", freq="MS", tz="UTC"))
    plain = lj.monthly_members(vol, months)
    assert "C00USDT" in plain[months[1]]  # dawna reguła wpuszcza (dni z obrotem 0 liczą się)
    monkeypatch.setattr(lj, "POPRAWKA13_OD", pd.Timestamp("2026-08-01", tz="UTC"))
    p13 = lj.basket_members(vol, months)
    assert p13[months[0]] == plain[months[0]]  # przed datą wejścia bez zmian
    assert "C00USDT" not in p13[months[1]] and "C00USDT" not in p13[months[2]]
    assert all(len(v) == 20 for v in p13.values()) and list(p13) == months
    rank = lj.basket_ranking(vol, months, 50)
    for m in months:  # rejestr koszyka: top-20 rankingu = skład silnika (inaczej ValueError)
        assert sorted(s for s, _ in rank[m][:20]) == p13[m]
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    assert lj.basket_members(vol, months) == plain


# ------------------------------------------------------------------ R2–R4 przez silnik
def test_no_event_view_equals_input_and_engine_is_bit_identical(dirs, monkeypatch):
    """Bez zdarzenia (baza) poprawka nie zmienia NICZEGO: składowe, X1 i transakcje = wersja wyłączona."""
    data = lj.load_live(dirs["baza"])
    as_of = data["close"].index[-1]
    _on(monkeypatch)
    v = lj.journal_view(data, as_of)
    assert v["events"] == [] and not v["excl"].to_numpy().any()
    on_rets, _ = lj.components(data, as_of, FEE)
    on_pos, k, hist, _ = lj.positions(data, as_of, FEE)
    on_led = lj.trade_ledger(data, as_of, hist, k)
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    off_rets, _ = lj.components(data, as_of, FEE)
    off_pos, _, _, _ = lj.positions(data, as_of, FEE)
    off_led = lj.trade_ledger(data, as_of, hist, k)
    pd.testing.assert_frame_equal(on_rets, off_rets, check_exact=True)
    pd.testing.assert_frame_equal(on_pos, off_pos, check_exact=True)
    for a, b in zip(on_led, off_led, strict=True):
        pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_krach_on_mark_equals_truth_on_event_day(dirs, monkeypatch):
    """Wycofanie z ceną mark = świeca krachu: trend w dniu D liczy cenę i likwidacje jak „prawda”
    (krach −90 % przy trwającym handlu). Dowód kroku 1: bez poprawki ukryte 2,23 pp kapitału trendu.
    """
    _on(monkeypatch)
    as_of = D + 2 * DAY
    e_w, e_k, e_old = {}, {}, {}
    lj.components(lj.load_live(dirs["wycofanie_mark"]), as_of, FEE, e_w)
    lj.components(lj.load_live(dirs["krach"]), as_of, FEE, e_k)
    tw, tk = e_w["trend"].set_index("date"), e_k["trend"].set_index("date")
    assert tw.at[D, "gross"] == pytest.approx(tk.at[D, "gross"], abs=1e-12)
    assert tw.at[D, "liquidations"] == tk.at[D, "liquidations"] > 0
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    lj.components(lj.load_live(dirs["wycofanie_mark"]), as_of, FEE, e_old)
    t_old = e_old["trend"].set_index("date")
    assert t_old.at[D, "liquidations"] == 0  # dawne zasady: brak świecy = „bez ruchu”
    assert abs(t_old.at[D, "gross"] - tk.at[D, "gross"]) > 0.01  # tyle ukrywał dziennik


def test_wycofanie_ledger_settles_on_detection_day(dirs, monkeypatch):
    """R2/R6: pozycje C01 trzymane w dniu D kończą się w D („wycofanie”, cena mark albo przybliżona),
    bez NaN; od D brak nowych pozycji (R4) i pozycji ogłaszanych na jutro."""
    _on(monkeypatch)
    for key, src in (("wycofanie_mark", "mark"), ("wycofanie", "przybliżona")):
        data = lj.load_live(dirs[key])
        as_of = D + 2 * DAY
        v = lj.journal_view(data, as_of)
        (ev,) = [e for e in v["events"] if e["symbol"] == DEAD]
        assert ev["d1"] == D and ev["zrodlo"] == src
        if src == "przybliżona":  # ostatnie normalne zamknięcie (D−1)
            assert ev["cena"] == data["close"].at[D - DAY, DEAD]
        pos, k, hist, _ = lj.positions(data, as_of, FEE)
        closed, opened = lj.trade_ledger(data, as_of, hist, k)
        c = closed[(closed["symbol"] == DEAD) & (closed["data_wyjscia"] >= D.date().isoformat())]
        assert len(c) and set(c["powod_wyjscia"]) <= {"wycofanie", "likwidacja"}
        assert (c["data_wyjscia"] == D.date().isoformat()).all()
        w = c[c["powod_wyjscia"] == "wycofanie"]
        assert len(w) and (w["cena_wyjscia"] == ev["cena"]).all()
        assert w["zwrot_pozycji_proc"].notna().all()
        sign = np.where(w["kierunek"] == "long", 1.0, -1.0)
        assert np.allclose(
            w["zwrot_pozycji_proc"], 100 * sign * (ev["cena"] / w["cena_wejscia"] - 1), atol=1e-9
        )
        assert set(c["skladowa"]) >= {"trend"}
        assert not (opened["symbol"] == DEAD).any()
        assert not (pos["symbol"] == DEAD).any()
        assert closed["cena_wyjscia"].notna().all() and opened["cena_biezaca"].notna().all()


def _engine_trend_phases(data, as_of):
    e: dict = {}
    lj.components(data, as_of, FEE, e)
    return e["trend_phases"]


@pytest.mark.parametrize("key", ["wycofanie_mark", "zamrozenie"])
def test_ledger_identity_with_settlements(dirs, monkeypatch, key):
    """Każde zamknięte formowanie fazy trendu (z rozliczeniami „wycofanie”): Π(1 + gross silnika) − 1 =
    Σ |waga·7| · zwrot pozycji — lista transakcji i wynik liczą się z tych samych paneli."""
    _on(monkeypatch)
    data = lj.load_live(dirs[key])
    as_of = data["close"].index[-2]
    pos, k, hist, _ = lj.positions(data, as_of, FEE)
    closed, opened = lj.trade_ledger(data, as_of, hist, k)
    per_phase = _engine_trend_phases(data, as_of)
    tr = closed[closed["skladowa"] == "trend"]
    sym = DEAD if key == "wycofanie_mark" else FROZ
    hit = tr[(tr["symbol"] == sym) & (tr["data_wyjscia"] >= D.date().isoformat())]
    want = {"wycofanie_mark": "likwidacja", "zamrozenie": "wycofanie"}[key]
    assert len(hit) and set(hit["powod_wyjscia"]) == {want}
    assert (hit["data_wyjscia"] == D.date().isoformat()).all()
    checked = 0
    for (ph, formed), g in tr.groupby(["faza", "data_wejscia"]):
        f0 = pd.Timestamp(formed, tz="UTC")
        if f0 < lj.JOURNAL_START:
            continue  # formowanie sprzed startu: pozycje zamknięte przed startem są poza listą
        eng = per_phase[ph]
        gross = eng.loc[(eng.index > f0) & (eng.index <= f0 + pd.Timedelta(days=7)), "gross"]
        lots = (g["waga"].abs() * lj.PHASES * g["zwrot_pozycji_proc"] / 100).sum()
        assert np.prod(1 + gross) - 1 == pytest.approx(lots, abs=1e-9)
        checked += 1
    assert checked >= 10
    # otwarte pozycje = pozycje ogłaszane (poza zlikwidowanymi), monety rozliczonej nie ma w żadnej
    comp = {"trend": "trend", "coinbase": "premia_coinbase"}
    want = {
        (comp[r.component], r.phase, r.formed, r.symbol, r.sign, round(r.weight, 12))
        for r in pos.itertuples()
    }
    liq_now = {
        (r.skladowa, r.faza, r.data_wejscia, r.symbol)
        for r in closed.itertuples()
        if r.powod_wyjscia == "likwidacja" and r.data_wejscia >= min(p[2] for p in want)
    }
    got = {
        (
            r.skladowa,
            r.faza,
            r.data_wejscia,
            r.symbol,
            1 if r.kierunek == "long" else -1,
            round(r.waga, 12),
        )
        for r in opened.itertuples()
        if r.skladowa != "x1"
    }
    assert got == {w for w in want if w[:4] not in liq_now}


def test_zamrozenie_no_new_positions_and_out_of_basket(dirs, monkeypatch):
    """Zamrożenie (świece płaskie, obrót 0, status TRADING): od D zero wag trendu i miejsc w nogach X1
    (R4), rozliczenie po ostatnim normalnym zamknięciu (bez ceny mark), koszyk 2026-09 bez C02 (R5).
    """
    _on(monkeypatch)
    data = lj.load_live(dirs["zamrozenie"])
    as_of = data["close"].index[-1]
    v = lj.journal_view(data, as_of)
    (ev,) = [e for e in v["events"] if e["symbol"] == FROZ]
    assert ev["d1"] == D and ev["zrodlo"] == "przybliżona"
    assert ev["cena"] == data["close"].at[D - DAY, FROZ]
    assert FROZ not in v["members"][pd.Timestamp("2026-09-01", tz="UTC")]
    assert FROZ in v["members"][pd.Timestamp("2026-08-01", tz="UTC")]
    close = v["close"]
    vols = ewma_vol(close)
    j = list(close.columns).index(FROZ)
    end = as_of + DAY
    sig = signal_panel(close)
    legs_fn = lj.masked_legs(v["excl"])
    ms = sorted(v["members"])
    n_forms = 0
    for ph in range(lj.PHASES):
        dates = [t for t in formation_dates(close.index, lj.ENGINE_START, end, ph) if t >= D]
        for t, (_, w) in zip(
            dates, build_formations(v["signs"], vols, v["members"], dates), strict=True
        ):
            assert w[j] == 0
            legs = legs_fn(sig.loc[t], v["members"][_month_of(t, ms)])
            assert legs is None or (FROZ not in legs[0] and FROZ not in legs[1])
            n_forms += 1
    assert n_forms >= 30
    # dawne zasady na tych samych danych: zamrożona moneta dostaje nowe pozycje (dowód kroku 1)
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    v0 = lj.journal_view(data, as_of)
    dates = [t for t in formation_dates(close.index, lj.ENGINE_START, end, 0) if t >= D]
    w0 = [
        w[j] for _, w in build_formations(v0["signs"], ewma_vol(v0["close"]), v0["members"], dates)
    ]
    assert any(x != 0 for x in w0)


# ------------------------------------------------------------------ przebieg: log, zapis, R7
def _run(src, jdir, monkeypatch, od=START):
    _on(monkeypatch, od)
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    return text, (jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()


def _files(jdir: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(jdir.glob("*.csv"))}


def test_run_without_event_is_byte_identical_to_disabled(dirs, tmp_path, monkeypatch):
    """Ścieżka bez zdarzenia: pliki bajt w bajt i linia logu (poza czasem) jak z poprawką wyłączoną."""
    t_on, log_on = _run(dirs["baza"], tmp_path / "on", monkeypatch)
    t_off, log_off = _run(dirs["baza"], tmp_path / "off", monkeypatch, od=None)
    assert _files(tmp_path / "on") == _files(tmp_path / "off")
    assert log_on[-1].split(" | ", 1)[1] == log_off[-1].split(" | ", 1)[1]
    assert "wstrzymane" not in log_on[-1] and "pliki świec" not in log_on[-1]
    assert "Wstrzymania" not in t_on and t_on.splitlines()[1:] == t_off.splitlines()[1:]


def test_run_logs_halt_field_parsed_by_page(tmp_path, monkeypatch):
    """Przebieg w dniu wycofania (+2): pole „wstrzymane: …” po „koszyk”, przed „historia zmieniona”;
    parser strony czyta linię, (h) milczy; transakcje.csv z „wycofanie”; powtórka bez zmian historii.
    """
    src = tmp_path / "live"
    _write(src, "wycofanie", n_days=449)  # ostatnia świeca 2026-08-23 = D + 3
    mark = 0.9 * float(pd.read_parquet(src / f"{DEAD}_1d.parquet")["close"].iloc[-1])
    _write_mark(src, [(DEAD, D, mark, mark * 1.05, mark * 0.95, mark)])
    _write_status(src, {DEAD: ("SETTLING", "2026-08-20 09:00")})
    jdir = tmp_path / "dziennik"
    text, log = _run(src, jdir, monkeypatch)
    line = log[-1]
    want = f"wstrzymane: {DEAD} od {D.date()}, cena {mark:.8g} (mark)"
    assert " | koszyk +" in line and line.endswith(f" | {want} | historia zmieniona: 0")
    assert line.index("| koszyk ") < line.index("| wstrzymane: ")
    assert sd.LOG_RE.match(line) and sd.error_fields(line) == []
    runs, bad = sd.parse_log("\n".join(log))
    assert bad == 0 and runs[-1]["changed"] == 0 and runs[-1]["carry"] == ""
    assert "Wstrzymania (poprawka 13" in text and "status SETTLING" in text
    tr = pd.read_csv(jdir / "transakcje.csv")
    w = tr[(tr["symbol"] == DEAD) & (tr["powod_wyjscia"] == "wycofanie")]
    assert len(w) and (w["data_wyjscia"] == D.date().isoformat()).all()
    assert np.allclose(w["cena_wyjscia"], mark)
    before = _files(jdir)
    _, log2 = _run(src, jdir, monkeypatch)
    assert (
        log2[-1].endswith(f" | {want} | historia zmieniona: 0")
        and _files(jdir).keys() == before.keys()
    )
    for name in before:
        if name != "transakcje_otwarte.csv" and name != "strategie.csv":
            assert _files(jdir)[name] == before[name], name


def test_run_missing_basket_file_raises_h_alarm(tmp_path, monkeypatch):
    """R7: członek koszyka z koszyk.csv bez świec w danych — bez pliku albo z plikiem pustym (pusta
    odpowiedź giełdy nadpisuje plik, a `price_panels` go pomija) → pole z „BŁĄD” (kontrola (h)
    strony); przed datą wejścia poprawki bez pola."""
    src = tmp_path / "live"
    _write(src, "baza")
    jdir = tmp_path / "dziennik"
    _run(src, jdir, monkeypatch)
    ks = pd.read_csv(jdir / "koszyk.csv")
    assert ks.loc[ks["symbol"].isin([DEAD, FROZ]), "czlonek_top20"].all()
    (src / f"{DEAD}_1d.parquet").unlink()
    (src / f"{DEAD}_funding.parquet").unlink()
    empty = pd.read_parquet(src / f"{FROZ}_1d.parquet").iloc[:0]
    empty.to_parquet(src / f"{FROZ}_1d.parquet", index=False)  # plik jest, świec brak
    assert lj.missing_basket_files(jdir, src) == [DEAD]  # samo istnienie pliku nie wystarcza…
    cols = lj.price_panels(src)["close"].columns
    assert lj.missing_basket_files(jdir, src, cols) == [DEAD, FROZ]  # …więc liczą się kolumny
    _, log = _run(src, jdir, monkeypatch)
    line = log[-1]
    want = f"BŁĄD brak {DEAD}, {FROZ}"
    assert f" | pliki świec {want} | historia zmieniona: " in line
    assert sd.LOG_RE.match(line) and sd.error_fields(line) == [("pliki świec", want)]
    runs, _ = sd.parse_log(line)
    assert any(p.startswith(f"(h) pliki świec: {want}") for p in sd.checks(_state(runs[-1]), line))
    assert runs[-1]["changed"] > 0  # zanik pliku przelicza historię — alarm mówi dlaczego
    # data wejścia po as_of: bez pola (linia jak przed poprawką)
    _, log3 = _run(src, jdir, monkeypatch, od=pd.Timestamp("2026-12-01", tz="UTC"))
    assert "pliki świec" not in log3[-1]


# ------------------------------------------------------------------ rejestr rozliczeń (przegląd 16c)
E = pd.Timestamp("2026-08-10", tz="UTC")  # dzień zdarzenia w danych małych (146 dni od 2026-05-01)
SMALL_OD = pd.Timestamp("2026-07-01", tz="UTC")  # data wejścia poprawki w danych małych


def _small_env(monkeypatch, od=SMALL_OD):
    """Silnik od 2026-06-01, wynik od 2026-07-01 — przebieg na danych małych trwa ~2 s."""
    monkeypatch.setattr(lj, "ENGINE_START", pd.Timestamp("2026-06-01", tz="UTC"))
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-07-01", tz="UTC"))
    monkeypatch.setattr(lj, "X1_START", pd.Timestamp("2026-07-01", tz="UTC"))
    monkeypatch.setattr(lj, "POPRAWKA13_OD", od)


def _cut(src: Path, dst: Path, last: pd.Timestamp) -> Path:
    """Kopia katalogu danych do dnia `last` włącznie — dane przebiegu, w którym `last` = as_of."""
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.iterdir()):
        df = pd.read_parquet(f)
        col = next((c for c in ("open_time", "timestamp") if c in df.columns), None)
        if col is not None:
            df = df[pd.to_datetime(df[col], utc=True) < last + DAY]
        df.to_parquet(dst / f.name, index=False)
    return dst


def _run_small(src: Path, jdir: Path) -> str:
    lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    return (jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()[-1]


def _mark_row(src: Path, sym: str, day: pd.Timestamp, scale: float) -> tuple:
    c = scale * float(
        pd.read_parquet(src / f"{sym}_1d.parquet").set_index("open_time")["close"].iloc[-1]
    )
    return (sym, day, c * 1.01, c * 1.08, c * 0.93, c)


def test_settlement_fixed_at_first_write_when_mark_arrives_late(tmp_path, monkeypatch):
    """Uwaga 1 przeglądu 16c: w dniu wykrycia pobranie ceny mark zawodzi → rozliczenie „przybliżona”
    zapisane w rejestrze i „BŁĄD” w logu tego przebiegu; następny przebieg ma już cenę mark, a mimo to
    cena i źródło zostają (historia zmieniona: 0). Bez rejestru ten sam przebieg zmieniłby historię.
    """
    _small_env(monkeypatch)
    full = tmp_path / "full"
    _small(full, "wycofanie", E, seed=3)
    _write_status(full, {DEAD: ("SETTLING", "2026-08-10 09:00")})
    jdir = tmp_path / "dziennik"
    t0 = _cut(full, tmp_path / "t0", E)
    line0 = _run_small(t0, jdir)
    prev_close = float(pd.read_parquet(t0 / f"{DEAD}_1d.parquet")["close"].iloc[-1])
    assert f" | wstrzymane: {DEAD} od {E.date()}, cena {prev_close:.8g} (przybliżona)" in line0
    assert f" | rozliczenie BŁĄD bez ceny mark {DEAD} | historia zmieniona: 0" in line0
    assert sd.LOG_RE.match(line0)
    assert sd.error_fields(line0) == [("rozliczenie", f"BŁĄD bez ceny mark {DEAD}")]
    reg0 = lj.read_settlements(jdir)
    assert reg0[["symbol", "d1", "zrodlo", "zapisano_as_of"]].values.tolist() == [
        [DEAD, str(E.date()), "przybliżona", str(E.date())]
    ]
    assert reg0["cena"].iloc[0] == prev_close and np.isnan(reg0["mark_high"].iloc[0])
    # ponowiony przebieg tej samej nocy: rejestr bez zmian, alarm nadal w logu
    assert " | rozliczenie BŁĄD bez ceny mark " in _run_small(t0, jdir)
    # następna noc: cena mark przyszła (świeca z dnia wykrycia jest w pliku)
    t1 = _cut(full, tmp_path / "t1", E + DAY)
    _write_mark(t1, [_mark_row(t0, DEAD, E, 0.5)])
    backup = tmp_path / "bez_rejestru"
    shutil.copytree(jdir, backup)
    line1 = _run_small(t1, jdir)
    assert line1.endswith("| historia zmieniona: 0") and "rozliczenie BŁĄD" not in line1
    assert f"cena {prev_close:.8g} (przybliżona)" in line1
    pd.testing.assert_frame_equal(lj.read_settlements(jdir), reg0)
    tr = pd.read_csv(jdir / "transakcje.csv")
    w = tr[(tr["symbol"] == DEAD) & (tr["powod_wyjscia"] == "wycofanie")]
    assert len(w) and (w["cena_wyjscia"] == prev_close).all()
    # kontrola: bez rejestru nowa cena mark przeliczyłaby rozliczenie (tak było przed poprawką 16c)
    (backup / lj.SETTLE_CSV).unlink()
    line_b = _run_small(t1, backup)
    assert int(sd.LOG_RE.match(line_b)["ch"]) > 0


def test_corrupted_mark_file_keeps_recorded_settlement_and_logs_error(tmp_path, monkeypatch):
    """Uwaga 1(b): zepsuty plik ceny mark nie zmienia zapisanego rozliczenia „mark” (rejestr), a log
    dostaje pole z „BŁĄD” (kontrola (h)); nieczytelny rejestr → własne pole z „BŁĄD”."""
    _small_env(monkeypatch)
    full = tmp_path / "full"
    _small(full, "wycofanie", E, seed=3)
    t0 = _cut(full, tmp_path / "t0", E)
    _write_mark(t0, [_mark_row(t0, DEAD, E, 0.7)])
    jdir = tmp_path / "dziennik"
    line0 = _run_small(t0, jdir)
    assert "(mark)" in line0 and "BŁĄD" not in line0 and line0.endswith("historia zmieniona: 0")
    reg0 = lj.read_settlements(jdir)
    assert reg0["zrodlo"].tolist() == ["mark"]
    t1 = _cut(full, tmp_path / "t1", E + 3 * DAY)
    (t1 / fetch_live.MARK_FILE).write_bytes(b"przerwany zapis")
    line1 = _run_small(t1, jdir)
    assert line1.endswith("| historia zmieniona: 0") and "(mark)" in line1
    errs = sd.error_fields(line1)
    assert len(errs) == 1 and errs[0][0] == "cena mark" and errs[0][1].startswith("BŁĄD ")
    pd.testing.assert_frame_equal(lj.read_settlements(jdir), reg0)
    # rejestr nieczytelny: przebieg idzie dalej, pole „rejestr rozliczeń BŁĄD …”, rejestru nie dopisuje
    (jdir / lj.SETTLE_CSV).write_text("zepsuty\n", encoding="utf-8")
    line2 = _run_small(t1, jdir)
    assert sd.LOG_RE.match(line2)
    assert ("rejestr rozliczeń", "BŁĄD ValueError") in sd.error_fields(line2)
    assert (jdir / lj.SETTLE_CSV).read_text(encoding="utf-8") == "zepsuty\n"


@pytest.mark.parametrize("scenario", ["wycofanie", "zamrozenie", "luka", "obrot0", "krach"])
def test_rows_up_to_t_identical_in_runs_t_and_later(tmp_path, monkeypatch, scenario):
    """Uwaga 2(c): po dacie wejścia kolejne przebiegi (przed zdarzeniem, w dniu wykrycia, po nim i po
    końcu wyłączenia) przeliczają całą historię i nie zmieniają ani jednego zapisanego wiersza."""
    _small_env(monkeypatch)
    full = tmp_path / "full"
    _small(full, scenario, E, seed=3)
    if scenario != "krach":
        base = _cut(full, tmp_path / "base", E - DAY)
        _write_mark(full, [_mark_row(base, s, E, 0.8) for s in (DEAD, FROZ)])
    jdir = tmp_path / "dziennik"
    for k, last in enumerate((E - 2 * DAY, E, E + 3 * DAY, E + 10 * DAY, E + 30 * DAY)):
        line = _run_small(_cut(full, tmp_path / f"t{k}", last), jdir)
        assert sd.LOG_RE.match(line)
        assert line.endswith("| historia zmieniona: 0"), (last.date(), line[-200:])
    reg = lj.read_settlements(jdir)
    if scenario == "krach":
        assert reg.empty
    else:
        assert reg["d1"].tolist() == [str(E.date())] and reg["zrodlo"].tolist() == ["mark"]


def _state(last_run: dict) -> dict:
    """Minimalny stan strony dla `sd.checks` (kontrole a–g bez zarzutów)."""
    return {
        "health": {"latest_as_of": "x", "hosts_last_day": []},
        "expected_as_of": "x",
        "criteria": {"consistency": {"after_first_result": 0}},
        "r1": {"drawdown": [0.0]},
        "x1": None,
        "log_unparsed": 0,
        "carry": {},
        "last_run": last_run,
    }


def test_missing_basket_files_and_load_tolerance(tmp_path, dirs):
    jdir = tmp_path / "j"
    assert lj.missing_basket_files(jdir, dirs["baza"]) == []  # brak koszyk.csv
    jdir.mkdir()
    pd.DataFrame(
        {
            "miesiac": ["2026-09"] * 3,
            "symbol": [DEAD, "ZZZUSDT", "YYYUSDT"],
            "pozycja": [1, 2, 3],
            "sredni_obrot_30d": [1, 1, 1],
            "czlonek_top20": [True, True, False],
            "funding_pobrany": [True, True, True],
        }
    ).to_csv(jdir / "koszyk.csv", index=False)
    assert lj.missing_basket_files(jdir, dirs["baza"]) == ["ZZZUSDT"]
    # nieczytelne pliki statusu i ceny mark nie zatrzymują dziennika (puste tabele)
    bad = tmp_path / "bad"
    _write(bad, "baza", n_days=200, start="2025-06-01")
    (bad / fetch_live.STATUS_FILE).write_bytes(b"to nie parquet")
    (bad / fetch_live.MARK_FILE).write_bytes(b"to nie parquet")
    p = lj.price_panels(bad)
    assert (
        p["status"].empty
        and p["mark_close"].empty
        and isinstance(p["mark_close"].index, pd.DatetimeIndex)
    )
    assert p["mark_blad"].startswith("BŁĄD ")  # zepsuty plik ceny mark → pole logu
    assert lj.price_panels(dirs["baza"])["mark_blad"] is None  # brak pliku to nie błąd
    t = lj.truncate(p, p["close"].index[50])  # wartości bez osi czasu przechodzą bez zmian
    assert t["mark_blad"] == p["mark_blad"] and t["status"] is p["status"]
    # nieczytelny rejestr rozliczeń = wyjątek (przebieg zgłasza „rejestr rozliczeń BŁĄD …”)
    assert lj.read_settlements(tmp_path / "brak").empty
    (jdir / lj.SETTLE_CSV).write_text("zla,naglowek\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        lj.read_settlements(jdir)


# ------------------------------------------------------------------ log: format i parser strony
def test_halt_log_fields_and_entries():
    ev = [
        {
            "symbol": "AUSDT",
            "d1": D,
            "d2": D + DAY,
            "e": D + 6 * DAY,
            "cena": 0.12345678912,
            "zrodlo": "mark",
            "przyczyna": "brak świecy",
        },
        {
            "symbol": "BUSDT",
            "d1": D,
            "d2": D,
            "e": D + 6 * DAY,
            "cena": np.nan,
            "zrodlo": "przybliżona",
            "przyczyna": "obrót 0",
        },
        {
            "symbol": "CUSDT",
            "d1": D,
            "d2": D + DAY,
            "e": D + 6 * DAY,
            "cena": 2.0,
            "zrodlo": "przybliżona",
            "przyczyna": "obrót 0",
        },
    ]
    members = {
        pd.Timestamp("2026-08-01", tz="UTC"): ["AUSDT", "BUSDT"],
        pd.Timestamp("2026-09-01", tz="UTC"): ["BTCUSDT"],
    }
    got = lj.halt_entries(ev, members, D + DAY)
    assert [e["symbol"] for e in got] == ["AUSDT"]  # B: seria skończona; C: spoza koszyka tygodnia
    # koszyk tygodnia = miesiąc as_of albo as_of − 7 dni
    assert [
        e["symbol"] for e in lj.halt_entries(ev, members, pd.Timestamp("2026-09-07", tz="UTC"))
    ] == []
    ev2 = [dict(ev[0], d2=pd.Timestamp("2026-09-05", tz="UTC"))]
    assert len(lj.halt_entries(ev2, members, pd.Timestamp("2026-09-05", tz="UTC"))) == 1
    f = lj.halt_log(got + [ev[1]], ["XUSDT", "YUSDT"])
    assert f == (
        " | wstrzymane: AUSDT od 2026-08-20, cena 0.12345679 (mark); BUSDT od 2026-08-20, cena brak "
        "(przybliżona) | pliki świec BŁĄD brak XUSDT, YUSDT"
    )
    assert (
        lj.halt_log([], []) == ""
        and lj.halt_log([], [], "BŁĄD KeyError") == " | pliki świec BŁĄD KeyError"
    )
    assert lj.summarize_halts([], []) == ""
    assert "do 2026-08-26" in lj.summarize_halts(got, [])


_BASE = (
    "2026-10-07T02:30:05.328711+00:00 | as_of 2026-10-06 | binance 2026-10-06 | premia 2026-10-06 | "
    "sygnały +147 | wyniki +1 | kapitał 1.0069 | obsunięcie 0.1% | OK | X1 sygnały +70 wyniki +1 "
    "kapitał 1.0221 obsunięcie 3.7% OK | stan rynku +1 | F&G +1 | transakcje +30 | opisy strategii 5 | "
    "rozbicie +3 | fazy +21 | koszyk +0"
)


@settings(max_examples=150, deadline=None)
@given(
    syms=st.lists(
        st.sampled_from(["AUSDT", "1000PEPEUSDT", "币安人生USDT", "XUSDT"]),
        min_size=0,
        max_size=3,
        unique=True,
    ),
    price=st.one_of(st.just(float("nan")), st.floats(1e-9, 1e7, allow_nan=False)),
    src=st.sampled_from(["mark", "przybliżona"]),
    missing=st.lists(st.sampled_from(["BUSDT", "1INCHUSDT"]), max_size=2, unique=True),
    carry=st.sampled_from(
        [
            ("", ""),
            (" | carry spóźnione", "spóźnione"),
            (" | carry BŁĄD OSError | carry zmiany 2", "BŁĄD OSError"),
        ]
    ),
    ch=st.integers(0, 5),
)
def test_halt_fields_keep_page_parser_and_h_semantics(syms, price, src, missing, carry, ch):
    """Każda linia z polami poprawki 13: LOG_RE czyta licznik „historia zmieniona”, stan rynku i X1;
    (h) zgłasza wyłącznie alarm plików (R7), pola carry czyta jak dotąd."""
    ev = [{"symbol": s, "d1": D, "cena": price, "zrodlo": src} for s in syms]
    line = _BASE + lj.halt_log(ev, missing) + carry[0] + f" | historia zmieniona: {ch}"
    assert "\n" not in line
    m = sd.LOG_RE.match(line)
    assert m and int(m["ch"]) == ch and m["stan"] == "+1" and m["x1"].startswith("sygnały +70")
    expected = [("pliki świec", "BŁĄD brak " + ", ".join(missing))] if missing else []
    assert sd.error_fields(line) == expected
    runs, bad = sd.parse_log(line)
    assert bad == 0 and runs[0]["carry"] == carry[1] and runs[0]["changed"] == ch


# ------------------------------------------------------------------ hypothesis: data wejścia i reguły
def _small(out: Path, scenario: str, event: pd.Timestamp, seed: int) -> None:
    _write(out, scenario, n_days=146, start="2026-05-01", event=event, seed=seed)


def _snapshot(data, as_of):
    """Wszystko, co dziennik zapisuje z silnika: zwroty trendu i premii, X1, transakcje zamknięte."""
    rets, _ = lj.components(data, as_of, FEE)
    v = lj.journal_view(data, as_of)
    x1, _ = lj.x1_component(
        v["close"], v["funding"], v["members"], as_of, as_of + DAY, FEE, excl=v["excl"]
    )
    hist = pd.DataFrame(columns=["k_trend", "k_coinbase"])
    closed, _ = lj.trade_ledger(data, as_of, hist, {"trend": 1.0, "coinbase": 1.0})
    return rets, x1, closed, v["members"]


@settings(
    max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    scenario=st.sampled_from(["wycofanie", "zamrozenie", "luka", "obrot0", "krach"]),
    event_day=st.integers(0, 40),
    entry_shift=st.integers(-12, 12),
    seed=st.integers(1, 4),
    with_mark=st.booleans(),
)
def test_property_rows_before_entry_date_identical(
    tmp_path_factory, monkeypatch, scenario, event_day, entry_shift, seed, with_mark
):
    """(a) Dla dowolnego zdarzenia i dowolnej daty wejścia E: wszystko, co dziennik zapisuje dla dni
    < E (zwroty trendu, premii i X1, transakcje zamknięte przed E, skład koszyka miesięcy < E), jest
    identyczne z wersją bez poprawki — przeliczenie historii nie zmienia żadnego zapisanego wiersza.
    """
    monkeypatch.setattr(lj, "ENGINE_START", pd.Timestamp("2026-06-01", tz="UTC"))
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-07-01", tz="UTC"))
    monkeypatch.setattr(lj, "X1_START", pd.Timestamp("2026-07-01", tz="UTC"))
    event = pd.Timestamp("2026-07-25", tz="UTC") + pd.Timedelta(days=event_day)
    entry = event + pd.Timedelta(days=entry_shift)
    src = tmp_path_factory.mktemp("prop")
    _small(src, scenario, event, seed)
    if with_mark:
        _write_mark(src, [(s, event, 1.0, 1.3, 0.4, 0.7) for s in (DEAD, FROZ)])
    data = lj.load_live(src)
    as_of = data["close"].index[-1]
    monkeypatch.setattr(lj, "POPRAWKA13_OD", entry)
    on = _snapshot(data, as_of)
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    off = _snapshot(data, as_of)
    pd.testing.assert_frame_equal(
        on[0][on[0].index < entry], off[0][off[0].index < entry], check_exact=True
    )
    pd.testing.assert_series_equal(
        on[1][on[1].index < entry], off[1][off[1].index < entry], check_exact=True
    )
    cut = entry.date().isoformat()
    ca, cb = on[2], off[2]
    pd.testing.assert_frame_equal(
        ca[ca["data_wyjscia"] < cut].reset_index(drop=True),
        cb[cb["data_wyjscia"] < cut].reset_index(drop=True),
        check_exact=True,
    )
    assert {m: v for m, v in on[3].items() if m < entry} == {
        m: v for m, v in off[3].items() if m < entry
    }


def _view_data(seed: int, n: int = 90) -> dict:
    """Dane w pamięci jak z `load_live` (BTC + C01…C21, od 2026-06-01): świece z rozrzutem, obrót
    równy (koszyk = 20 pierwszych alfabetycznie, C01 w środku), funding 0, statusy puste."""
    idx = pd.date_range("2026-06-01", periods=n, freq="D", tz="UTC")
    cols = ["BTCUSDT"] + [f"C{i:02d}USDT" for i in range(1, 22)]
    rng = np.random.default_rng(seed)
    close = pd.DataFrame(
        10 * np.exp(np.cumsum(rng.normal(0, 0.05, (n, len(cols))), axis=0)), index=idx, columns=cols
    )
    return {
        "close": close,
        "open": close * 1.003,
        "high": close * 1.03,
        "low": close * 0.97,
        "volume": close * 0 + 1e6,
        "funding": close * 0,
        "status": pd.DataFrame(columns=["status", "contract_type", "delivery"]),
    }


@settings(max_examples=40, deadline=None)
@given(
    seed=st.integers(0, 50),
    n_halt=st.integers(1, 12),
    i0=st.integers(32, 60),
    kind=st.sampled_from(["koniec", "zamrozenie", "obrot0", "luka"]),
    mark=st.one_of(
        st.none(),
        st.tuples(
            st.floats(1_000, 5_000),
            st.floats(0.01, 0.5),
            st.floats(0.01, 0.5),
            st.sampled_from([0.9, 1.1]),
        ),
        st.sampled_from([(np.nan, 0.1, 0.1, 0.9), (-1.0, 0.1, 0.1, 0.9), (0.0, 0.1, 0.1, 0.9)]),
    ),
)
def test_property_settlement_price_and_no_new_positions(seed, n_halt, i0, kind, mark):
    """Na widoku dziennika (`journal_view` — te same znaki, nogi i panele, z których liczy silnik):
    (b) od dnia wykrycia do końca wyłączenia moneta ma zerową wagę trendu i nie trafia do nóg X1
    (a przed wykryciem wagę ma — test nie jest pusty); (c) cena rozliczenia to DOKŁADNIE zamknięcie
    ceny mark z dnia wykrycia, a ekstrema R3 to dokładnie jego maksimum i minimum. Cena mark leży
    daleko od ceny ostatniej, open ≠ close ≠ high ≠ low, a dni obok mają inne świece mark — więc
    pomyłka pola (open/high/low/close ostatnie) albo dnia wychodzi. Bez poprawnej ceny mark:
    ostatnie normalne zamknięcie z flagą „przybliżona” i bez sprawdzenia likwidacji."""
    d = _view_data(seed)
    idx = d["close"].index
    sym, d1 = DEAD, idx[i0]
    span = idx[i0 : i0 + n_halt] if kind != "koniec" else idx[i0:]
    last = float(d["close"].at[idx[i0 - 1], sym])
    if kind in ("koniec", "luka"):
        for k in ("open", "high", "low", "close", "volume"):
            d[k].loc[span, sym] = np.nan
    elif kind == "zamrozenie":
        for k in ("open", "high", "low", "close"):
            d[k].loc[span, sym] = last
        d["volume"].loc[span, sym] = 0.0
    else:
        d["volume"].loc[span, sym] = 0.0
    if mark is not None:
        c, up, dn, a = mark
        days = [idx[i0 - 1], d1, idx[i0 + 1]]
        mk = {  # dni obok: inne świece (pomyłka dnia wychodzi)
            "mark_close": [2.0 * c, c, 3.0 * c],
            "mark_high": [2.5 * c, c * (1 + up), 3.5 * c],
            "mark_low": [1.5 * c, c * (1 - dn), 2.5 * c],
        }
        for k, vals in mk.items():
            d[k] = pd.DataFrame({sym: vals}, index=days)
    as_of = idx[-1]
    old = (lj.ENGINE_START, lj.POPRAWKA13_OD)
    lj.ENGINE_START, lj.POPRAWKA13_OD = idx[30], idx[31]
    try:
        v = lj.journal_view(d, as_of)
        dates = [formation_dates(idx, lj.ENGINE_START, as_of + DAY, ph) for ph in range(lj.PHASES)]
    finally:
        lj.ENGINE_START, lj.POPRAWKA13_OD = old
    ev = [e for e in v["events"] if e["symbol"] == sym]
    assert len(ev) == 1 and ev[0]["d1"] == d1 and ev[0]["d2"] == span[-1]
    e = ev[0]
    assert e["e"] == max(span[-1], d1 + pd.Timedelta(days=lj.HALT_MIN_DAYS - 1))
    if mark is not None and np.isfinite(mark[0]) and mark[0] > 0:
        c, up, dn, _ = mark
        assert e["zrodlo"] == "mark" and e["cena"] == c
        assert e["mark_high"] == c * (1 + up) and e["mark_low"] == c * (1 - dn)
        assert v["close"].at[d1, sym] == c
        assert v["high"].at[d1, sym] == c * (1 + up) and v["low"].at[d1, sym] == c * (1 - dn)
    else:
        assert e["zrodlo"] == "przybliżona" and e["cena"] == last
        assert np.isnan(v["high"].at[d1, sym]) and np.isnan(v["low"].at[d1, sym])
    # (b): znaki, σ̂ i skład z widoku — każde formowanie w oknie wyłączenia: waga 0, brak w nogach
    vols = ewma_vol(v["close"])
    j = list(v["close"].columns).index(sym)
    legs = lj.masked_legs(v["excl"])
    sig = signal_panel(v["close"])
    month_starts = sorted(v["members"])
    before = []
    for ts in dates:
        for t, (_, w) in zip(ts, build_formations(v["signs"], vols, v["members"], ts), strict=True):
            if e["d1"] <= t <= e["e"]:
                assert w[j] == 0
                lg = legs(sig.loc[t], v["members"][_month_of(t, month_starts)])
                assert lg is None or (sym not in lg[0] and sym not in lg[1])
            elif t < e["d1"]:
                before.append(w[j])
    assert any(x != 0 for x in before)  # przed wykryciem moneta ma pozycję — test nie jest pusty
    # po rozliczeniu: zwrot 0 i brak ekstremów (żadnej likwidacji po dniu wykrycia)
    win_after = (idx > e["d1"]) & (idx <= e["e"])
    assert (v["close"][sym].loc[win_after] == e["cena"]).all()
    assert v["low"][sym].loc[win_after].isna().all() and v["high"][sym].loc[win_after].isna().all()
    assert list(v["settle"].index[v["settle"][sym]]) == [d1]
    assert v["excl"][sym].loc[(idx >= e["d1"]) & (idx <= e["e"])].all()


# ------------------------------------------------------------------ fetch_live: statusy i cena mark
def test_contract_statuses_parse_and_sanitize():
    info = {
        "symbols": [
            {
                "symbol": "ALPACAUSDT",
                "quoteAsset": "USDT",
                "status": "SETTLING",
                "contractType": "PERPETUAL",
                "deliveryDate": "1746003600000",
            },
            {
                "symbol": "BTCUSDT",
                "quoteAsset": "USDT",
                "status": "TRADING",
                "contractType": "PERPETUAL",
                "deliveryDate": 4133404800000,
            },
            {
                "symbol": "BTCUSDT_261225",
                "quoteAsset": "USDT",
                "status": "TRADING",
                "contractType": "CURRENT_QUARTER",
            },
            {"symbol": "ETHBTC", "quoteAsset": "BTC", "status": "TRADING"},
            {"symbol": "../X", "quoteAsset": "USDT", "status": "TRADING"},
            {
                "symbol": "ODDUSDT",
                "quoteAsset": "USDT",
                "status": "bad|status\n",
                "contractType": None,
                "deliveryDate": "jutro",
            },
        ]
    }
    st_ = fetch_live.contract_statuses(info).set_index("symbol")
    assert list(st_.index) == ["ALPACAUSDT", "BTCUSDT", "ODDUSDT"]
    assert st_.at["ALPACAUSDT", "status"] == "SETTLING"
    assert st_.at["ALPACAUSDT", "delivery"] == pd.Timestamp("2025-04-30 09:00", tz="UTC")
    assert (
        st_.at["ODDUSDT", "status"] == "NIEZNANY"
        and st_.at["ODDUSDT", "contract_type"] == "NIEZNANY"
    )
    assert pd.isna(st_.at["ODDUSDT", "delivery"])
    assert fetch_live.contract_statuses({}).empty


def test_save_statuses_safe_removes_stale_file_on_error(tmp_path, capsys):
    path = fetch_live.save_statuses_safe({"symbols": []}, tmp_path)
    assert path is not None and path.exists()
    assert fetch_live.save_statuses_safe({"symbols": "zły format"}, tmp_path) is None
    assert not (tmp_path / fetch_live.STATUS_FILE).exists()
    assert "statusy kontraktów BŁĄD" in capsys.readouterr().out


class _FakeEx:
    """Giełda bez sieci: `fapiPublicGetMarkPriceKlines` z gotowych świec; zapisuje wywołania."""

    def __init__(self, candles: dict[str, list[list]], fail: tuple[str, ...] = ()):
        self.candles, self.fail, self.calls = candles, fail, []

    def fapiPublicGetMarkPriceKlines(self, params):
        self.calls.append(params)
        if params["symbol"] in self.fail:
            raise RuntimeError("giełda")
        rows = self.candles.get(params["symbol"], [])
        return [r for r in rows if params["startTime"] <= r[0] <= params["endTime"]]


def _k(day: str, o, h, lo, c) -> list:
    return [
        int(pd.Timestamp(day, tz="UTC").value // 1_000_000),
        str(o),
        str(h),
        str(lo),
        str(c),
        "0",
    ]


def test_parse_and_fetch_mark_only_closed_days():
    end = int(pd.Timestamp("2026-08-22 00:30", tz="UTC").value // 1_000_000)
    ex = _FakeEx(
        {
            "AUSDT": [
                _k("2026-08-20", 1, 2, 0.5, 1.5),
                _k("2026-08-21", 1.5, 1.6, 1.4, 1.45),
                _k("2026-08-22", 1, 1, 1, 1),
            ]
        }
    )
    start = int(pd.Timestamp("2026-08-20", tz="UTC").value // 1_000_000)
    df = fetch_live.fetch_mark_1d(ex, "AUSDT", start, end, pacing_s=0)
    assert list(df["open_time"].dt.date.astype(str)) == [
        "2026-08-20",
        "2026-08-21",
    ]  # 22.08 niezamknięta
    assert df["close"].tolist() == [1.5, 1.45] and len(ex.calls) == 1
    assert fetch_live.parse_mark_klines_1d([], end).empty


def test_fetch_mark_safe_only_for_unsettled_halts_and_merges(dirs, tmp_path, monkeypatch, capsys):
    src = tmp_path / "live"
    shutil.copytree(dirs["wycofanie"], src)
    end = int(pd.Timestamp("2026-09-24 00:30", tz="UTC").value // 1_000_000)
    ex = _FakeEx({DEAD: [_k("2026-08-20", 1, 2, 0.5, 1.5)]})
    nothing = {"symbols": [], "blad": None}
    monkeypatch.setattr(lj, "POPRAWKA13_OD", pd.Timestamp("2026-12-01", tz="UTC"))
    assert fetch_live.fetch_mark_safe(ex, src, end, pacing_s=0) == nothing and ex.calls == []
    monkeypatch.setattr(lj, "POPRAWKA13_OD", START)
    assert lj.halted_symbols(src) == [DEAD]
    # zdarzenie już w rejestrze rozliczeń: cena mark niepotrzebna — zero zapytań
    done = {(DEAD, str(D.date()))}
    assert lj.halted_symbols(src, done) == []
    assert fetch_live.fetch_mark_safe(ex, src, end, pacing_s=0, settled=done) == nothing
    assert ex.calls == []
    _write_mark(src, [("OLDUSDT", pd.Timestamp("2026-08-05", tz="UTC"), 1, 1, 1, 1)])
    got = fetch_live.fetch_mark_safe(ex, src, end, pacing_s=0, settled={("XUSDT", "2026-08-20")})
    assert got == {"symbols": [DEAD], "blad": None}
    assert [c["symbol"] for c in ex.calls] == [DEAD]
    assert ex.calls[0]["startTime"] == int(START.value // 1_000_000)
    m = pd.read_parquet(src / fetch_live.MARK_FILE)
    assert set(m["symbol"]) == {DEAD, "OLDUSDT"}  # stare świece zostają
    p = lj.price_panels(src)
    assert p["mark_close"].at[D, DEAD] == 1.5 and p["mark_blad"] is None
    # błąd pobrania monety: zapisane świece zostają, wydruk z błędem
    ex_bad = _FakeEx({}, fail=(DEAD,))
    assert fetch_live.fetch_mark_safe(ex_bad, src, end, pacing_s=0)["symbols"] == [DEAD]
    assert "cena mark BŁĄD: C01USDT RuntimeError" in capsys.readouterr().out
    assert pd.read_parquet(src / fetch_live.MARK_FILE).equals(m)
    # zepsuty plik: przebudowa z nowego pobrania (bez starych świec) + błąd do pola logu
    (src / fetch_live.MARK_FILE).write_bytes(b"przerwany zapis")
    got = fetch_live.fetch_mark_safe(ex, src, end, pacing_s=0)
    assert got["symbols"] == [DEAD] and got["blad"].startswith("BŁĄD ")
    assert set(pd.read_parquet(src / fetch_live.MARK_FILE)["symbol"]) == {DEAD}
    assert "nieczytelny — usunięty i przebudowany" in capsys.readouterr().out
    # zepsuty plik, a wszystko rozliczone: plik usunięty (następny odczyt bez błędu), błąd do logu
    (src / fetch_live.MARK_FILE).write_bytes(b"przerwany zapis")
    got = fetch_live.fetch_mark_safe(ex, src, end, pacing_s=0, settled=done)
    assert got["symbols"] == [] and got["blad"].startswith("BŁĄD ")
    assert not (src / fetch_live.MARK_FILE).exists() and lj.price_panels(src)["mark_blad"] is None
    # błąd ogólny (np. katalog bez świec) → błąd w wyniku, bez wyjątku
    empty = tmp_path / "pusty"
    empty.mkdir()
    assert fetch_live.fetch_mark_safe(ex, empty, end, pacing_s=0)["blad"] == "BŁĄD ValueError"
    # wyłączona poprawka = zero zapytań
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    ex.calls.clear()
    assert fetch_live.fetch_mark_safe(ex, src, end, pacing_s=0) == nothing and ex.calls == []


def test_fetch_live_run_saves_statuses_and_fetches_mark_last():
    import inspect

    src = inspect.getsource(fetch_live.run)
    assert src.index("save_statuses_safe(info, out_dir)") < src.index("fetch_klines_1d(")
    assert src.index("fetch_coinm_funding_safe(out_dir)") < src.index("fetch_mark_safe(ex, out_dir")
    assert "settled=settled" in src and '"mark_blad": mark["blad"]' in src
    # dziennik czyta rejestr PRZED pobraniem i przekazuje rozliczone zdarzenia
    run_src = inspect.getsource(lj.run)
    assert run_src.index("read_settlements(journal_dir)") < run_src.index("fetch_run(live_dir")
    assert run_src.index("settlement_rows(") < run_src.index('journal_dir / "sygnaly.csv"')
    for name in (fetch_live.STATUS_FILE, fetch_live.MARK_FILE):  # pliki pomocnicze to nie monety
        assert not name.endswith("_1d.parquet") and not name.endswith("_funding.parquet")


def test_funding_symbols_follow_journal_basket(tmp_path, monkeypatch):
    """Funding pobierany dla koszyka dziennika (R5): moneta, która wchodzi na miejsce zamrożonej, ma
    funding; skład przed datą wejścia bez zmian."""
    src = tmp_path / "live"
    _write(src, "zamrozenie", n_coins=24)
    now = pd.Timestamp("2026-09-20", tz="UTC")
    monkeypatch.setattr(lj, "POPRAWKA13_OD", None)
    old = set(fetch_live.funding_symbols(src, now))
    monkeypatch.setattr(lj, "POPRAWKA13_OD", START)
    new = set(fetch_live.funding_symbols(src, now))
    data = lj.load_live(src)
    v = lj.journal_view(data, data["close"].index[-1])
    assert {s for syms in v["members"].values() for s in syms} | {"BTCUSDT"} == new
    assert old <= new  # członkowie z dawnej reguły zostają (rozbieg), nowy członek 2026-09 dochodzi
