"""Testy poprawki 12 dziennika: noga carry COIN-M (`backtest/journal_carry.py` + zapis w `live_journal`).

Czyste funkcje: agregacja dzienna rozliczeń, koszt wejścia tylko pierwszego dnia, dzień zamknięty
dopiero po rozliczeniu z dnia następnego, braki oznaczone (nie pominięte), zgodność z D1
(`inverse_carry_pnl` i okno z zamrożonego reportera), test właściwości w `hypothesis`.
Przebieg dziennika: append-only z „historia zmieniona”, linia `przebiegi.log` bez nowych pól na
ścieżce bez błędów, błąd carry nie zatrzymuje dziennika i nie rusza innych plików.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import journal_carry as jc
from backtest import live_journal as lj
from backtest.carry_hedged import CarryCosts
from backtest.carry_product import floor_to_grid, inverse_carry_pnl
from backtest.checkpoint_lib import load_config
from tests.test_live_journal import _write_live
from tools import strona_dziennika as sd

SW = 0.0019  # koszt wejścia D1: spot 0,10 % + taker 0,05 % + 2 × poślizg 2 pb (czyste funkcje: podany wprost)
SW_CFG = jc.carry_costs(
    load_config()["costs"]
).switch_cost  # to samo z configu (przebieg dziennika)
START = pd.Timestamp("2026-09-10", tz="UTC")
ROOT = Path(__file__).resolve().parents[1]


def _funding(first="2026-09-08", days=6, extra=1, rates=None, jitter=None, drop=()):
    """Rozliczenia co 8 h od `first` przez `days` pełnych dni + `extra` rozliczeń dnia następnego."""
    ts = pd.date_range(first, periods=3 * days + extra, freq="8h", tz="UTC")
    r = (
        np.asarray(rates, dtype=float)
        if rates is not None
        else 1e-4 * (1 + np.arange(len(ts)) / 10)
    )
    df = pd.DataFrame({"timestamp": ts, "funding_rate": r[: len(ts)]})
    if jitter is not None:
        df["timestamp"] = df["timestamp"] + pd.to_timedelta(jitter[: len(ts)], unit="ms")
    return df.drop(index=list(drop)).reset_index(drop=True)


def _d1_window(funding: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Przygotowanie DOSŁOWNIE jak zamrożony reporter D1 (Q2): siatka, duplikaty, sortowanie, okno."""
    from backtest.run_carry_product_d1 import _window

    cm = funding.copy()
    cm["timestamp"] = floor_to_grid(cm["timestamp"])
    cm = cm.drop_duplicates("timestamp").sort_values("timestamp")
    return _window(cm, "timestamp", start.isoformat(), end.isoformat())


# ------------------------------------------------------------------ czyste funkcje
def test_carry_costs_are_d1_costs_from_config():
    cost = load_config()["costs"]
    d1 = CarryCosts(  # tak buduje koszty `run_carry_product_d1.main`
        spot_fee=cost["spot_fee_rate"],
        perp_fee=cost["taker_fee_rate"],
        slippage=cost["slippage_bps"] / 10_000.0,
    )
    assert jc.carry_costs(cost) == d1
    assert jc.carry_costs(cost).switch_cost == pytest.approx(SW, abs=1e-15)


def test_daily_rows_sum_three_settlements_and_charge_entry_once():
    f = _funding(first="2026-09-10", days=5)
    rows = jc.carry_rows(f, START, SW)
    assert list(rows.columns) == jc.CARRY_COLS
    assert rows["date"].tolist() == [f"2026-09-{d}" for d in range(10, 15)]
    assert rows["rozliczenia"].tolist() == [3] * 5 and rows["komplet"].all()
    rates = f["funding_rate"].to_numpy()[:15].reshape(5, 3).sum(axis=1)
    assert np.allclose(rows["suma_stawek"], rates, rtol=0, atol=1e-15)
    assert rows["koszt"].tolist() == [SW, 0.0, 0.0, 0.0, 0.0]  # koszt wejścia tylko pierwszego dnia
    assert np.allclose(rows["netto"], rows["suma_stawek"] - rows["koszt"], rtol=0, atol=1e-15)
    assert np.allclose(rows["netto_skum"], np.cumsum(rows["netto"]), rtol=0, atol=1e-15)


def test_day_is_written_only_when_closed_and_history_is_a_prefix():
    f = _funding(first="2026-09-10", days=3, extra=0)  # ostatnie rozliczenie: 12.09 16:00
    rows = jc.carry_rows(f, START, SW)
    assert rows["date"].tolist() == ["2026-09-10", "2026-09-11"]  # 12.09 jeszcze nie zamknięty
    later = jc.carry_rows(_funding(first="2026-09-10", days=3, extra=2), START, SW)
    assert later["date"].tolist() == ["2026-09-10", "2026-09-11", "2026-09-12"]
    pd.testing.assert_frame_equal(later.iloc[:2], rows)  # nowy dzień nie zmienia starych wierszy


def test_missing_settlements_are_flagged_not_skipped():
    # 11.09 bez rozliczenia 08:00 (indeks 4), 12.09 bez żadnego (6, 7, 8)
    f = _funding(first="2026-09-10", days=4, drop=(4, 6, 7, 8))
    rows = jc.carry_rows(f, START, SW).set_index("date")
    assert rows.loc["2026-09-11", "rozliczenia"] == 2 and not rows.loc["2026-09-11", "komplet"]
    assert rows.loc["2026-09-12", "rozliczenia"] == 0 and not rows.loc["2026-09-12", "komplet"]
    assert rows.loc["2026-09-12", "netto"] == 0.0
    assert rows.loc[["2026-09-10", "2026-09-13"], "komplet"].all()
    assert len(rows) == 4


def test_jitter_is_floored_like_d1_and_rhythm_change_is_flagged():
    base = jc.carry_rows(_funding(first="2026-09-10", days=3), START, SW)
    jit = np.random.default_rng(0).integers(0, 8, 10)  # ms, jak na giełdzie (0–7 ms)
    pd.testing.assert_frame_equal(
        jc.carry_rows(_funding(first="2026-09-10", days=3, jitter=jit), START, SW), base
    )
    # dzień 11.09 rozliczany co 4 h: D1 łączy 04:00 z 00:00 (zostaje pierwszy), liczba to pokazuje
    f = _funding(first="2026-09-10", days=3)
    extra = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-09-11 04:00", "2026-09-11 12:00"], utc=True),
            "funding_rate": [0.5, 0.5],
        }
    )
    f4 = pd.concat([f, extra]).sort_values("timestamp").reset_index(drop=True)
    rows = jc.carry_rows(f4, START, SW).set_index("date")
    assert rows.loc["2026-09-11", "rozliczenia"] == 5 and not rows.loc["2026-09-11", "komplet"]
    assert rows.loc["2026-09-11", "suma_stawek"] == pytest.approx(
        base.set_index("date").loc["2026-09-11", "suma_stawek"]
    )


def test_settlements_before_start_do_not_count():
    f = _funding(first="2026-09-08", days=4)  # 08.09 i 09.09 przed startem
    rows = jc.carry_rows(f, START, SW)
    assert rows["date"].iloc[0] == "2026-09-10" and rows["koszt"].iloc[0] == SW
    same = jc.carry_rows(f[f["timestamp"] >= START], START, SW)
    pd.testing.assert_frame_equal(rows, same)


def test_empty_inputs_give_empty_rows_with_columns():
    empty = pd.DataFrame(
        {
            "timestamp": pd.Series(dtype="datetime64[ns, UTC]"),
            "funding_rate": pd.Series(dtype=float),
        }
    )
    for f in (
        empty,
        _funding(first="2026-09-01", days=3),  # wszystko przed startem
        _funding(first="2026-09-10", days=0, extra=3),  # tylko pierwszy dzień, niezamknięty
    ):
        rows = jc.carry_rows(f, START, SW)
        assert rows.empty and list(rows.columns) == jc.CARRY_COLS


def test_missing_columns_fail_loud():
    with pytest.raises(ValueError, match="timestamp i funding_rate"):
        jc.carry_rows(pd.DataFrame({"timestamp": [], "rate": []}), START, SW)


def test_net_equals_d1_inverse_carry_pnl_on_same_data():
    """Σ netto − koszt wyjścia = wynik D1 (`inverse_carry_pnl`) za te same zamknięte dni; stawki 1:1."""
    rng = np.random.default_rng(12)
    f = _funding(
        first="2026-09-08",
        days=9,
        rates=rng.normal(1e-4, 2e-4, 40),
        jitter=rng.integers(0, 8, 40),
        drop=(13,),
    )
    rows = jc.carry_rows(f, START, SW)
    end = pd.Timestamp(rows["date"].iloc[-1], tz="UTC") + pd.Timedelta(days=1)
    d1 = inverse_carry_pnl(_d1_window(f, START, end), SW)
    assert rows["netto_skum"].iloc[-1] - SW == pytest.approx(d1["pnl"].sum(), abs=1e-15)
    assert rows["suma_stawek"].sum() == pytest.approx(d1["funding_received"].sum(), abs=1e-15)
    own = jc.settlement_pnl(f, START, SW)
    own = own[own["timestamp"] < end]
    assert np.array_equal(own["funding_received"].to_numpy(), d1["funding_received"].to_numpy())
    assert own["cost"].sum() == SW and d1["cost"].sum() == pytest.approx(
        2 * SW
    )  # D1: wejście + wyjście


def test_inverse_carry_pnl_single_settlement_keeps_only_entry_cost():
    one = pd.DataFrame({"timestamp": [START], "funding_rate": [2e-4]})
    p = jc.settlement_pnl(one, START, SW)
    assert p["cost"].tolist() == [SW] and p["pnl"].tolist() == [2e-4 - SW]


@settings(max_examples=80, deadline=None)
@given(
    rates=st.lists(
        st.floats(-0.003, 0.003, allow_nan=False, allow_infinity=False), min_size=4, max_size=90
    ),
    keep=st.lists(st.booleans(), min_size=90, max_size=90),
    jitter=st.lists(st.integers(0, 7), min_size=90, max_size=90),
)
def test_property_net_is_rates_minus_one_entry_cost(rates, keep, jitter):
    n = len(rates)
    ts = pd.date_range(START, periods=n, freq="8h") + pd.to_timedelta(jitter[:n], unit="ms")
    f = pd.DataFrame({"timestamp": ts, "funding_rate": rates})[np.array(keep[:n])]
    rows = jc.carry_rows(f, START, SW)
    if rows.empty:
        return
    days = pd.date_range(START, periods=len(rows), freq="D").strftime("%Y-%m-%d").tolist()
    assert rows["date"].tolist() == days  # każdy dzień od startu dokładnie raz, bez dziur
    used = f[floor_to_grid(f["timestamp"]).dt.floor("D") <= pd.Timestamp(days[-1], tz="UTC")]
    cost = rows["koszt"].sum()
    assert cost == (SW if len(used) else 0.0)  # koszt wejścia dokładnie raz (gdy jest rozliczenie)
    assert rows["netto"].sum() == pytest.approx(rows["suma_stawek"].sum() - cost, abs=1e-12)
    assert rows["netto"].sum() == pytest.approx(used["funding_rate"].sum() - cost, abs=1e-12)
    assert rows["netto_skum"].iloc[-1] == pytest.approx(rows["netto"].sum(), abs=1e-12)
    assert rows["rozliczenia"].sum() == len(used)
    assert (rows["komplet"] == (rows["rozliczenia"] == 3)).all()


# ------------------------------------------------------------------ opis strategii i README
def test_strategy_book_has_carry_with_start_file_and_cost():
    book = {s["id"]: s for s in lj.strategy_book()}
    c = book["carry"]
    assert c["wynik_od"] == jc.CARRY_START.date().isoformat() and c["wynik_w"] == jc.CARRY_CSV
    assert jc.CARRY_SYMBOL in c["opis"] and any("0,19 %" in z for z in c["zalozenia"])


def test_carry_start_and_readme_section_agree():
    assert (
        jc.CARRY_START == pd.Timestamp("2026-09-29", tz="UTC") and lj.CARRY_START == jc.CARRY_START
    )
    doc = (ROOT / "dziennik" / "README.md").read_text(encoding="utf-8")
    assert "## Poprawka 12 (2026-09-28" in doc
    section = doc.split("## Poprawka 12 (2026-09-28", 1)[1].split("\n## ", 1)[0]
    for needle in ("2026-09-29", jc.CARRY_SYMBOL, jc.CARRY_CSV, "komplet", "0,19 %"):
        assert needle in section, needle


# ------------------------------------------------------------------ pobieranie (bez sieci)
def test_fetch_coinm_funding_safe_uses_carry_start_and_swallows_errors(
    tmp_path, monkeypatch, capsys
):
    import data.fetch_external as fe
    from data import fetch_live

    calls = []

    def fake(symbol, start, out_dir, force=False):
        calls.append((symbol, start, Path(out_dir), force))
        return Path(out_dir) / jc.CARRY_FILE

    monkeypatch.setattr(fe, "fetch_coinm_funding", fake)
    assert fetch_live.fetch_coinm_funding_safe(tmp_path) == tmp_path / jc.CARRY_FILE
    assert calls == [(jc.CARRY_SYMBOL, "2026-09-29", tmp_path, True)]

    def boom(*a, **k):
        raise ConnectionError("sieć")

    monkeypatch.setattr(fe, "fetch_coinm_funding", boom)
    assert fetch_live.fetch_coinm_funding_safe(tmp_path) is None
    assert "funding COIN-M BTCUSD_PERP BŁĄD ConnectionError" in capsys.readouterr().out


def test_fetch_live_run_fetches_carry_after_other_sources():
    import inspect

    from data import fetch_live

    src = inspect.getsource(fetch_live.run)
    assert src.index("fetch_fng_safe(out_dir)") < src.index("fetch_coinm_funding_safe(out_dir)")
    assert fetch_live.fetch_coinm_funding_safe.__module__ == "data.fetch_live"


# ------------------------------------------------------------------ przebieg dziennika
# Format linii `przebiegi.log` sprzed poprawki 12 (commit 0bfeef5), ścieżka bez błędów: dokładnie te
# pola w tej kolejności — bez miejsca na nowe. Parser strony w rutynie Cowork jest wklejony (nie z repo).
PRE_P12_LOG = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\S+ \| as_of \d{4}-\d{2}-\d{2} \| binance \d{4}-\d{2}-\d{2} \| "
    r"premia \d{4}-\d{2}-\d{2} \| sygnały \+\d+ \| wyniki \+\d+ \| kapitał \d+\.\d{4} \| "
    r"obsunięcie \d+\.\d% \| (?:OK|OSTRZEŻENIE|STOP) \| X1 sygnały \+\d+ wyniki \+\d+ "
    r"kapitał \d+\.\d{4} obsunięcie \d+\.\d% (?:OK|OSTRZEŻENIE|STOP) \| stan rynku \+\d+ \| "
    r"F&G \+\d+ \| transakcje \+\d+ \| opisy strategii \d+ \| rozbicie \+\d+ \| fazy \+\d+ \| "
    r"koszyk \+\d+ \| historia zmieniona: \d+$"
)


@pytest.fixture(scope="module")
def live_src(tmp_path_factory):
    """Dane na żywo jak w testach dziennika (480 dni do 2026-09-23) + funding COIN-M do 24.09 00:00."""
    src = tmp_path_factory.mktemp("live_carry")
    _write_live(src)
    rng = np.random.default_rng(5)
    ts = pd.date_range("2026-09-01", "2026-09-24", freq="8h", tz="UTC")
    pd.DataFrame(
        {
            "timestamp": ts + pd.to_timedelta(rng.integers(0, 8, len(ts)), unit="ms"),
            "funding_rate": rng.normal(1e-4, 1e-4, len(ts)),
        }
    ).to_parquet(src / jc.CARRY_FILE, index=False)
    return src


def test_coinm_file_is_neither_usdt_symbol_nor_usdt_funding(live_src):
    from backtest.xs_momentum import daily_funding_panel
    from data.fetch_live import symbol_files

    assert (live_src / jc.CARRY_FILE).exists()
    assert not any(jc.CARRY_SYMBOL in s for s in symbol_files(live_src))
    assert not any(
        jc.CARRY_SYMBOL in c or "cm_" in c for c in daily_funding_panel(live_src).columns
    )


def _run(src, jdir, monkeypatch, carry_start="2026-09-10"):
    monkeypatch.setattr(lj, "JOURNAL_START", pd.Timestamp("2026-08-01", tz="UTC"))
    monkeypatch.setattr(lj, "X1_START", pd.Timestamp("2026-08-01", tz="UTC"))
    monkeypatch.setattr(lj, "CARRY_START", pd.Timestamp(carry_start, tz="UTC"))
    text = lj.run(fetch=False, live_dir=src, journal_dir=jdir)
    return text, (jdir / "przebiegi.log").read_text(encoding="utf-8").splitlines()


def test_run_writes_carry_append_only_and_flags_changed_history(tmp_path, live_src, monkeypatch):
    jdir = tmp_path / "dziennik"
    text, log = _run(live_src, jdir, monkeypatch)
    ca = pd.read_csv(jdir / jc.CARRY_CSV)
    assert list(ca.columns) == jc.CARRY_COLS
    assert (
        ca["date"].tolist()
        == pd.date_range("2026-09-10", "2026-09-23").strftime("%Y-%m-%d").tolist()
    )
    assert (
        ca["komplet"].all()
        and (ca["rozliczenia"] == 3).all()
        and ca["koszt"].iloc[0] == pytest.approx(SW_CFG, abs=1e-15)
    )
    expected = jc.carry_rows(pd.read_parquet(live_src / jc.CARRY_FILE), START, SW_CFG)
    # odczyt CSV gubi ostatni bit (0,0019000000000000002 → 0,0019); „historia zmieniona” ma tolerancję 1e-9
    pd.testing.assert_frame_equal(ca, expected, check_exact=False, rtol=0, atol=1e-15)
    assert (
        "Carry COIN-M (poprawka 12" in text and "dopisane +14; 2026-09-23: rozliczenia 3/3" in text
    )
    # powtórka: nic nowego, historia bez zmian
    text2, log2 = _run(live_src, jdir, monkeypatch)
    assert "dopisane +0" in text2 and "HISTORIA ZMIENIONA" not in text2
    assert log2[1].endswith("historia zmieniona: 0") and len(pd.read_csv(jdir / jc.CARRY_CSV)) == 14
    # ręcznie zmieniony wiersz → „historia zmieniona”, stary zapis zostaje
    ca.loc[3, "netto"] += 0.01
    ca.to_csv(jdir / jc.CARRY_CSV, index=False)
    text3, log3 = _run(live_src, jdir, monkeypatch)
    assert "HISTORIA ZMIENIONA w 1 polach" in text3 and "2026-09-13:netto" in text3
    assert log3[2].endswith("historia zmieniona: 1")
    assert pd.read_csv(jdir / jc.CARRY_CSV)["netto"].iloc[3] == pytest.approx(
        ca["netto"].iloc[3], abs=1e-15
    )


def test_new_day_is_appended_without_touching_old_rows(tmp_path, live_src, monkeypatch):
    src = tmp_path / "live"
    src.mkdir()
    for p in live_src.iterdir():
        (src / p.name).write_bytes(p.read_bytes())
    f = pd.read_parquet(src / jc.CARRY_FILE)
    f[f["timestamp"] < pd.Timestamp("2026-09-23 08:00", tz="UTC")].to_parquet(src / jc.CARRY_FILE)
    jdir = tmp_path / "dziennik"
    text, log = _run(src, jdir, monkeypatch)  # dane carry kończą się 23.09 00:00 → zamknięty 22.09
    before = (jdir / jc.CARRY_CSV).read_bytes()
    assert pd.read_csv(jdir / jc.CARRY_CSV)["date"].iloc[-1] == "2026-09-22"
    assert re.search(r"\| koszyk \+\d+ \| carry spóźnione \| historia zmieniona: 0$", log[0])
    assert "UWAGA: dane carry spóźnione" in text
    f.to_parquet(src / jc.CARRY_FILE)  # następny przebieg ma już 24.09 00:00
    text2, log2 = _run(src, jdir, monkeypatch)
    after = (jdir / jc.CARRY_CSV).read_bytes()
    assert after.startswith(before) and after.count(b"\n") == before.count(b"\n") + 1
    assert "carry" not in log2[1] and PRE_P12_LOG.match(log2[1])


def test_no_error_log_line_keeps_pre_poprawka12_format(tmp_path, live_src, monkeypatch):
    """
    Ścieżka bez błędów: linia logu ma dokładnie pola sprzed poprawki 12 i jest identyczna (poza czasem
    przebiegu) z przebiegiem, w którym carry nie ma jeszcze nic do zapisania. Jedyna różnica wobec kodu
    sprzed poprawki: „opisy strategii 5” zamiast 4 (piąty opis — mechanizm poprawki 10).
    """
    _, log_on = _run(live_src, tmp_path / "z_carry", monkeypatch)
    _, log_off = _run(live_src, tmp_path / "bez_carry", monkeypatch, carry_start="2026-12-01")
    assert (tmp_path / "z_carry" / jc.CARRY_CSV).exists()
    assert not (tmp_path / "bez_carry" / jc.CARRY_CSV).exists()
    assert PRE_P12_LOG.match(log_on[0]) and "carry" not in log_on[0]
    assert log_on[0].split(" | ", 1)[1] == log_off[0].split(" | ", 1)[1]
    assert "| opisy strategii 5 |" in log_on[0]
    runs, bad = sd.parse_log(log_on[0] + "\n")  # parser strony z repo czyta linię
    assert bad == 0 and len(runs) == 1


def test_carry_error_does_not_stop_journal_nor_touch_other_files(tmp_path, live_src, monkeypatch):
    _, _ = _run(live_src, tmp_path / "ok", monkeypatch)

    def boom(*a, **k):
        raise RuntimeError("test")

    monkeypatch.setattr(lj, "carry_rows", boom)
    text, log = _run(live_src, tmp_path / "blad", monkeypatch)
    assert "mnożniki R1" in text and "BŁĄD carry: RuntimeError: test" in text
    assert re.search(
        r"\| koszyk \+\d+ \| carry BŁĄD RuntimeError \| historia zmieniona: 0$", log[0]
    )
    assert "RuntimeError: test" not in log[0]
    runs, bad = sd.parse_log(log[0] + "\n")
    assert bad == 0 and runs[0]["changed"] == 0
    assert not (tmp_path / "blad" / jc.CARRY_CSV).exists()
    others = sorted(p.name for p in (tmp_path / "ok").glob("*.csv") if p.name != jc.CARRY_CSV)
    assert len(others) >= 12
    for name in others:
        assert (tmp_path / "ok" / name).read_bytes() == (
            tmp_path / "blad" / name
        ).read_bytes(), name


def test_missing_carry_file_is_logged_and_journal_goes_on(tmp_path, live_src, monkeypatch):
    src = tmp_path / "live"
    src.mkdir()
    for p in live_src.iterdir():
        if p.name != jc.CARRY_FILE:
            (src / p.name).write_bytes(p.read_bytes())
    text, log = _run(src, tmp_path / "dziennik", monkeypatch)
    assert "| carry brak pliku | historia zmieniona: 0" in log[0]
    assert "dopisane brak pliku" in text and (tmp_path / "dziennik" / "wyniki.csv").exists()


def test_before_carry_start_nothing_is_late(tmp_path, live_src, monkeypatch):
    # dzień dziennika (as_of 23.09) przed startem carry → brak wierszy i brak alarmu
    text, log = _run(live_src, tmp_path / "dziennik", monkeypatch, carry_start="2026-09-29")
    assert "carry" not in log[0] and "jeszcze żaden dzień od startu nie jest zamknięty" in text
