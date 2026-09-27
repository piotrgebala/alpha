"""Testy dziennego indeksu likwidacji (`data/liquidation_index.py`) — bez sieci: mapowanie stron
(odwrotne znaczenie `S` na Binance i Bybit), nominał, okno 5 min, agregat na syntetycznym JSONL obu
formatów, tylko dni zamknięte, determinizm bajt w bajt, zapis tylko przy zmianie.
"""

from __future__ import annotations

import datetime as dt
import json
import random
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data import liquidation_index as li

D0 = 1_790_294_400_000  # 2026-09-25 00:00:00 UTC
MIN = 60_000


def bn(t: int, sym: str = "BTCUSDT", side: str = "SELL", q="2", p="100", ap="101") -> str:
    """Linia w formacie kolektora Binance (LK0)."""
    rec = {
        "E": t + 5,
        "st": 1,
        "ps": sym,
        "s": sym,
        "S": side,
        "o": "LIMIT",
        "f": "IOC",
        "q": q,
        "p": p,
        "ap": ap,
        "X": "FILLED",
        "l": q,
        "z": q,
        "T": t,
    }
    return json.dumps(rec, separators=(",", ":"))


def bb(t: int, sym: str = "BTCUSDT", side: str = "Buy", v="0.5", p="60000") -> str:
    """Linia w formacie kolektora Bybit (pola T, s, S, v, p + pole odbioru)."""
    return json.dumps({"T": t, "s": sym, "S": side, "v": v, "p": p, "odebrano_ms": t + 40})


# ------------------------------------------------------------------ strony
def test_strony_binance_sell_to_zlikwidowany_long():
    assert li.side_of("binance", "SELL") == "long"
    assert li.side_of("binance", "BUY") == "short"


def test_strony_bybit_buy_to_zlikwidowany_long():
    assert li.side_of("bybit", "Buy") == "long"
    assert li.side_of("bybit", "Sell") == "short"


def test_strony_odwrotne_miedzy_gieldami_ta_sama_likwidacja_longa():
    """Zlikwidowany LONG: na Binance S=SELL (zlecenie sprzedaży), na Bybit S=Buy (strona pozycji)."""
    a = li.aggregate("binance", "2026-09-25", [bn(D0, side="SELL")])
    b = li.aggregate("bybit", "2026-09-25", [bb(D0, side="Buy")])
    for idx in (a, b):
        assert idx.rows[0]["zdarzenia_long"] == "1"
        assert idx.rows[0]["zdarzenia_short"] == "0"
    # a „BUY” Binance to SHORT, choć po nazwie wygląda jak Bybit „Buy”
    c = li.aggregate("binance", "2026-09-25", [bn(D0, side="BUY")])
    assert c.rows[0]["zdarzenia_short"] == "1"


@pytest.mark.parametrize(
    "gielda,s", [("binance", "Sell"), ("binance", "Buy"), ("bybit", "SELL"), ("bybit", "BUY")]
)
def test_strony_zla_wielkosc_liter_to_blad_nie_zgadywanie(gielda, s):
    with pytest.raises(ValueError):
        li.side_of(gielda, s)


def test_nieznana_gielda():
    with pytest.raises(ValueError):
        li.side_of("okx", "Buy")


# ------------------------------------------------------------------ nominał
def test_nominal_binance_q_razy_ap():
    assert li.notional("binance", {"q": "2", "p": "100", "ap": "101"}) == Decimal("202")


@pytest.mark.parametrize("ap", ["0", "0.000", "", None])
def test_nominal_binance_ap_puste_lub_zero_to_q_razy_p(ap):
    rec = {"q": "2", "p": "100"}
    if ap is not None:
        rec["ap"] = ap
    assert li.notional("binance", rec) == Decimal("200")


def test_nominal_bybit_v_razy_p_tekst_i_liczba():
    assert li.notional("bybit", {"v": "0.5", "p": "60000"}) == Decimal("30000")
    assert li.notional("bybit", {"v": 0.5, "p": 60000}) == Decimal("30000")


# ------------------------------------------------------------------ kontrakty odwrotne (CM)
def _cm(sym: str, q: str, st=2, ps=None) -> dict:
    rec = {"s": sym, "q": q, "p": "83435", "ap": "83750.8"}
    if st is not None:
        rec["st"] = st
    if ps is not None:
        rec["ps"] = ps
    return rec


def test_binance_coin_m_nominal_z_wartosci_kontraktu():
    """COIN-M: `q` = liczba kontraktów (BTCUSD po 100 USD, reszta po 10 USD), nie ilość monety."""
    assert li.market_of("binance", _cm("BTCUSD_PERP", "24", ps="BTCUSD")) == "CM"
    assert li.notional("binance", _cm("BTCUSD_PERP", "24", ps="BTCUSD")) == Decimal("2400")
    assert li.notional("binance", _cm("BTCUSD_261225", "4")) == Decimal("400")  # bez `ps`
    assert li.notional("binance", _cm("ETHUSD_PERP", "11", ps="ETHUSD")) == Decimal("110")
    # bez pola `st` rozpoznanie po nazwie symbolu
    assert li.notional("binance", _cm("XRPUSD_PERP", "113", st=None)) == Decimal("1130")


def test_binance_usdt_m_z_data_dostawy_to_nie_coin_m():
    rec = {"s": "BTCUSDT_261225", "st": 1, "q": "0.01", "p": "80000", "ap": "80000"}
    assert li.market_of("binance", rec) == "UM"
    assert li.notional("binance", rec) == Decimal("800")


def test_bybit_odwrotny_v_w_usd_liniowy_v_razy_p():
    assert li.market_of("bybit", {"s": "BTCUSD"}) == "CM"
    assert li.notional("bybit", {"s": "BTCUSD", "v": "1000", "p": "60000"}) == Decimal("1000")
    assert li.notional("bybit", {"s": "BTCUSDZ25", "v": "50", "p": "60000"}) == Decimal("50")
    assert li.market_of("bybit", {"s": "BTCUSDT"}) == "UM"
    assert li.market_of("bybit", {"s": "BTCPERP"}) == "UM"


def test_kolumna_rynek_w_indeksie():
    line = json.dumps(
        {"E": D0, "st": 2, "ps": "BTCUSD", "s": "BTCUSD_PERP", "S": "BUY", "o": "LIMIT",
         "f": "IOC", "q": "3", "p": "84772", "ap": "84500", "X": "FILLED", "l": "3", "z": "3",
         "T": D0}
    )  # fmt: skip
    (r,) = li.aggregate("binance", "2026-09-25", [line, bn(D0, "BTCUSDT")]).rows[1:]
    assert r["symbol"] == "BTCUSD_PERP" and r["rynek"] == "CM"
    assert r["nominal_usdt"] == "300.00" and r["zdarzenia_short"] == "1"


@pytest.mark.parametrize("bad", ["abc", "-1", "NaN", "inf", True])
def test_nominal_zle_liczby(bad):
    with pytest.raises(ValueError):
        li.notional("bybit", {"v": bad, "p": "1"})


# ------------------------------------------------------------------ okno 5 min
def test_okno_5min_granica_polotwarta():
    ev = [(0, Decimal(1)), (5 * MIN - 1, Decimal(2)), (5 * MIN, Decimal(4))]
    # [0, 5 min) = 1 + 2 = 3; [5 min − 1 ms, 10 min − 1 ms) = 2 + 4 = 6
    assert li.max_window_sum(ev) == Decimal(6)
    assert li.max_window_sum([(0, Decimal(1)), (5 * MIN, Decimal(1))]) == Decimal(1)


def test_okno_5min_kolejnosc_wejscia_bez_znaczenia():
    ev = [(10 * MIN, Decimal(5)), (0, Decimal(1)), (MIN, Decimal(1)), (11 * MIN, Decimal(5))]
    assert li.max_window_sum(ev) == Decimal(10)
    assert li.max_window_sum([]) == Decimal(0)


def _brute(ev, w=li.WINDOW_MS):
    return max(
        (sum((v for t, v in ev if s <= t < s + w), Decimal(0)) for s, _ in ev), default=Decimal(0)
    )


@given(
    st.lists(st.tuples(st.integers(0, 3_600_000), st.integers(0, 10_000).map(Decimal)), max_size=60)
)
@settings(max_examples=200, deadline=None)
def test_wlasnosc_okno_zgodne_z_brute_force(ev):
    assert li.max_window_sum(ev) == _brute(ev)


# ------------------------------------------------------------------ agregat
def test_agregat_binance_syntetyczny():
    lines = [
        bn(D0 + 1 * MIN, "BTCUSDT", "SELL", q="2", p="100", ap="101"),  # long 202
        bn(D0 + 2 * MIN, "BTCUSDT", "BUY", q="1", p="100", ap="0"),  # short 100 (ap=0 → p)
        bn(D0 + 30 * MIN, "BTCUSDT", "SELL", q="3", p="100", ap="100"),  # long 300, poza oknem
        bn(D0 + 3 * MIN, "ACEUSDT", "BUY", q="10", p="0.5", ap="0.51"),  # short 5.1
        "",
        "{zly json",
        json.dumps({"s": "X", "S": "SELL", "T": D0}),  # brak q/p
        bn(D0, "BTCUSDT", "Sell"),  # zła strona dla Binance
    ]
    idx = li.aggregate("binance", "2026-09-25", lines)
    assert idx.lines == 7 and idx.bad_lines == 3
    assert [r["symbol"] for r in idx.rows] == ["ACEUSDT", "BTCUSDT"]
    ace, btc = idx.rows
    assert (
        btc["zdarzenia"] == "3" and btc["zdarzenia_long"] == "2" and btc["zdarzenia_short"] == "1"
    )
    assert btc["nominal_usdt"] == "602.00"
    assert btc["nominal_long_usdt"] == "502.00" and btc["nominal_short_usdt"] == "100.00"
    assert btc["maks_nominal_5min_usdt"] == "302.00"
    assert btc["pierwsze_utc"] == "2026-09-25T00:01:00.000Z"
    assert btc["ostatnie_utc"] == "2026-09-25T00:30:00.000Z"
    assert ace["nominal_usdt"] == "5.10" and ace["nominal_short_usdt"] == "5.10"
    assert ace["gielda"] == "binance" and ace["dzien"] == "2026-09-25"


def test_agregat_bybit_syntetyczny():
    lines = [
        bb(D0 + 123, "ETHUSDT", "Buy", v="2", p="2500"),  # long 5000
        bb(D0 + 4 * MIN, "ETHUSDT", "Sell", v="1", p="2400.5"),  # short 2400.5
        bb(D0 + 20 * MIN, "ETHUSDT", "Buy", v="0.1", p="2300"),  # long 230
    ]
    idx = li.aggregate("bybit", "2026-09-25", lines)
    (r,) = idx.rows
    assert (r["zdarzenia"], r["zdarzenia_long"], r["zdarzenia_short"]) == ("3", "2", "1")
    assert r["nominal_usdt"] == "7630.50"
    assert r["nominal_long_usdt"] == "5230.00" and r["nominal_short_usdt"] == "2400.50"
    assert r["maks_nominal_5min_usdt"] == "7400.50"
    assert r["pierwsze_utc"] == "2026-09-25T00:00:00.123Z"


def test_format_binance_nie_czyta_sie_jako_bybit():
    """Pomylenie katalogów nie daje cichych liczb: linia Binance w indeksie Bybit = zła linia."""
    idx = li.aggregate("bybit", "2026-09-25", [bn(D0)])
    assert idx.bad_lines == 1 and idx.rows == []


def test_csv_naglowek_i_pusty_dzien():
    data = li.index_csv(li.aggregate("binance", "2026-09-25", []))
    assert data == (",".join(li.COLUMNS) + "\n").encode()


def test_csv_odrzuca_przecinek_w_symbolu():
    """Druga linia obrony: wiersz z przecinkiem złożony z pominięciem `parse_line` → błąd CSV."""
    idx = li.aggregate("bybit", "2026-09-25", [bb(D0, sym="AB")])
    idx.rows[0]["symbol"] = "A,B"
    with pytest.raises(ValueError):
        li.index_csv(idx)


# ------------------------------------------------------------------ złe pola z sieci = zła linia
@pytest.mark.parametrize(
    "t", [10**17, 10**18, 10**30, -(10**16), -1, 0, li.MIN_EVENT_MS - 1, li.MAX_EVENT_MS + 1]
)
def test_czas_poza_zakresem_to_zla_linia_nie_blad_dnia(t):
    """T spoza 2019…2100 (np. 10**17 → „year 3170843 is out of range”) liczy się w `zle_linie`."""
    for gielda, line in (("binance", bn(t)), ("bybit", bb(t))):
        idx = li.aggregate(gielda, "2026-09-25", [line, bn(D0) if gielda == "binance" else bb(D0)])
        assert idx.bad_lines == 1 and len(idx.rows) == 1
        assert li.index_csv(idx).count(b"\n") == 2  # nagłówek + 1 wiersz


@pytest.mark.parametrize("t", ["1e400", "true", "null", '"abc"', "1.5e300"])
def test_czas_niecalkowity_lub_nieskonczony_to_zla_linia(t):
    line = bb(D0).replace(f'"T": {D0}', f'"T": {t}')
    assert line != bb(D0)
    idx = li.aggregate("bybit", "2026-09-25", [line, bb(D0)])
    assert idx.bad_lines == 1 and len(idx.rows) == 1


def test_czas_na_granicach_zakresu_przyjety():
    idx = li.aggregate("bybit", "2019-01-01", [bb(li.MIN_EVENT_MS), bb(li.MAX_EVENT_MS)])
    assert idx.bad_lines == 0
    assert idx.rows[0]["pierwsze_utc"] == "2019-01-01T00:00:00.000Z"
    assert idx.rows[0]["ostatnie_utc"] == "2100-01-01T00:00:00.000Z"


@pytest.mark.parametrize(
    "sym", ["X,Y", 'A"B', "A B", "A\nB", "A\tB", "=CMD()", "+1", "-1USDT", "@SUM", "", "A" * 41]
)
def test_symbol_niebezpieczny_dla_csv_to_zla_linia(sym):
    idx = li.aggregate("bybit", "2026-09-25", [bb(D0, sym=sym), bb(D0 + 1)])
    assert idx.bad_lines == 1 and [r["symbol"] for r in idx.rows] == ["BTCUSDT"]
    li.index_csv(idx)  # nie rzuca


@pytest.mark.parametrize(
    "sym", ["1000PEPEUSDT", "BTCUSDT_261225", "BTCUSD_PERP", "龙虾USDT", "币安人生USDT", "A" * 40]
)
def test_prawdziwe_symbole_przyjete(sym):
    """Symbole spoza ASCII to prawdziwe kontrakty Binance (LK0 2026-09-25…27) — nie odrzucamy."""
    idx = li.aggregate("binance", "2026-09-25", [bn(D0, sym)])
    assert idx.bad_lines == 0 and idx.rows[0]["symbol"] == sym
    assert sym.encode() in li.index_csv(idx)


def test_coin_m_rozpoznany_po_st_2_takze_przy_nazwie_spoza_wzorca():
    """`st` = 2 wystarcza (symbol bez `_PERP` / daty) — obie reguły `market_of` są potrzebne."""
    rec = {"s": "BTCUSD", "st": 2, "q": "7", "p": "83000", "ap": "83100"}
    assert li.market_of("binance", rec) == "CM"
    assert li.notional("binance", rec) == Decimal("700")  # 7 × 100 USD, nie 7 × 83 100
    rec_str = {**rec, "st": "2", "s": "ETHUSD", "q": "5"}
    assert li.notional("binance", rec_str) == Decimal("50")
    assert li.market_of("binance", {**rec, "st": 1}) == "UM"


def _gen_lines(draw_rows):
    return [
        bn(D0 + t, f"S{s}USDT", "SELL" if long_ else "BUY", q=str(q), p=str(p), ap=str(ap))
        for t, s, long_, q, p, ap in draw_rows
    ]


row_st = st.tuples(
    st.integers(0, 86_399_999),
    st.integers(0, 3),
    st.booleans(),
    st.integers(1, 1000),
    st.integers(1, 1000),
    st.integers(0, 1000),
)


@given(st.lists(row_st, min_size=1, max_size=40), st.randoms(use_true_random=False))
@settings(max_examples=100, deadline=None)
def test_wlasnosc_niezmienniki_i_niezaleznosc_od_kolejnosci(rows, rnd):
    lines = _gen_lines(rows)
    idx = li.aggregate("binance", "2026-09-25", lines)
    assert sum(int(r["zdarzenia"]) for r in idx.rows) == len(rows)
    for r in idx.rows:
        assert int(r["zdarzenia_long"]) + int(r["zdarzenia_short"]) == int(r["zdarzenia"])
        tot = Decimal(r["nominal_usdt"])
        assert Decimal(r["nominal_long_usdt"]) + Decimal(r["nominal_short_usdt"]) == tot
        assert Decimal(0) < Decimal(r["maks_nominal_5min_usdt"]) <= tot
        assert r["pierwsze_utc"] <= r["ostatnie_utc"]
    shuffled = list(lines)
    rnd.shuffle(shuffled)
    assert li.index_csv(li.aggregate("binance", "2026-09-25", shuffled)) == li.index_csv(idx)


# ------------------------------------------------------------------ dni zamknięte i zapis
def test_dni_zamkniete_pomija_dzisiejszy_przyszly_i_obce_pliki(tmp_path):
    for n in (
        "2026-09-25.jsonl",
        "2026-09-26.jsonl",
        "2026-09-27.jsonl",
        "2026-09-28.jsonl",
        "status.json",
        "kolektor.log",
        "2026-13-01.jsonl",
    ):
        (tmp_path / n).write_text("", encoding="utf-8")
    (tmp_path / "2026-09-24.jsonl").mkdir()  # katalog o nazwie dnia — nie plik
    days = li.closed_days(tmp_path, dt.date(2026, 9, 27))
    assert [d for d, _ in days] == ["2026-09-25", "2026-09-26"]


def test_dni_zamkniete_brak_katalogu(tmp_path):
    assert li.closed_days(tmp_path / "nie_ma", dt.date(2026, 9, 27)) == []


def test_utc_today_z_innej_strefy():
    now = dt.datetime(2026, 9, 27, 1, 30, tzinfo=dt.timezone(dt.timedelta(hours=2)))
    assert li.utc_today(now) == dt.date(2026, 9, 26)


def test_write_if_changed_stany(tmp_path):
    p = tmp_path / "a" / "x.csv"
    assert li.write_if_changed(p, b"1\n") == "nowy"
    mtime = p.stat().st_mtime_ns
    assert li.write_if_changed(p, b"1\n") == "bez zmian"
    assert p.stat().st_mtime_ns == mtime
    assert li.write_if_changed(p, b"2\n") == "zmieniony"
    assert p.read_bytes() == b"2\n"
    assert not list(tmp_path.glob("a/*.tmp"))


def test_cli_buduje_indeks_dni_zamknietych_idempotentnie(tmp_path, capsys, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "2026-09-25.jsonl").write_text(bn(D0) + "\n", encoding="utf-8")
    today = li.utc_today()
    (src / f"{today.isoformat()}.jsonl").write_text(bn(D0) + "\n", encoding="utf-8")
    out = tmp_path / "indeks"
    args = ["--gielda", "binance", "--dir", str(src), "--out", str(out)]
    assert li.main(args) == 0
    first = (out / "binance_2026-09-25.csv").read_bytes()
    assert not (out / f"binance_{today.isoformat()}.csv").exists()
    assert li.main(args) == 0
    assert (out / "binance_2026-09-25.csv").read_bytes() == first
    assert "bez zmian" in capsys.readouterr().out
    assert li.main(["--gielda", "okx", "--dir", str(src), "--out", str(out)]) == 2


def test_build_index_na_linii_z_prawdziwego_pliku(tmp_path):
    """Linia skopiowana 1:1 z ~/likwidacje/2026-09-26.jsonl (format kolektora LK0)."""
    line = (
        '{"E":1790380805406,"st":1,"ps":"USDBRLUSDT","s":"USDBRLUSDT","S":"SELL","o":"LIMIT",'
        '"f":"IOC","q":"2.35","p":"5.16260","ap":"5.19850","X":"FILLED","l":"2.35","z":"2.35",'
        '"T":1790380801893}'
    )
    p = tmp_path / "2026-09-26.jsonl"
    p.write_text(line + "\n", encoding="utf-8")
    (r,) = li.build_index("binance", "2026-09-26", p).rows
    assert r["nominal_usdt"] == "12.22"  # 2,35 × 5,19850 = 12,216475
    assert r["zdarzenia_long"] == "1"
    assert r["pierwsze_utc"] == "2026-09-26T00:00:01.893Z"


def test_losowe_linie_nie_wywracaja_agregatu():
    rnd = random.Random(7)
    junk = [
        "".join(chr(rnd.randint(32, 126)) for _ in range(rnd.randint(0, 40))) for _ in range(50)
    ]
    idx = li.aggregate("bybit", "2026-09-25", junk + [bb(D0)])
    assert len(idx.rows) == 1


def test_absurd_notional_is_a_bad_line_not_a_failed_day():
    """Przegląd bezpieczeństwa 2026-09-27: v = p = 1e20 wysadzało Decimal.quantize w sumie dnia."""
    good = json.dumps({"T": 1790532228154, "s": "BTCUSDT", "S": "Buy", "v": "0.5", "p": "100000"})
    huge = json.dumps({"T": 1790532228155, "s": "BTCUSDT", "S": "Buy", "v": "1e20", "p": "1e20"})
    idx = li.aggregate("bybit", "2026-09-27", [good, huge])
    assert idx.bad_lines == 1
    assert [r["zdarzenia"] for r in idx.rows] == ["1"]
