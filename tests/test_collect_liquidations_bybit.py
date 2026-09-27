"""Testy kolektora pełnych likwidacji Bybit (`data/collect_liquidations_bybit.py`) — bez sieci:
parser (w tym mapowanie strony POZYCJI), odrzucanie złych symboli/liczb/czasów, plan subskrypcji
(≤ 10 tematów na żądanie, limit znaków na połączenie — właściwości w hypothesis), lista instrumentów
z paginacją i limitem rozmiaru, naprawa nieudanej subskrypcji (`after_sub_fail` — także jako
właściwość na symulowanym Bybit), pętla z fałszywym połączeniem (zapis per dzień UTC, liczniki, ping,
ponowne łączenie po ciszy mimo pongów, odświeżenie listy symboli i ponowna próba po błędzie,
odczekanie przy połączeniu, które pada przed otwarciem), kontrola pozytywna bez zapisu na dysk
i jej kod wyjścia.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from dataclasses import dataclass

import aiohttp
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data import collect_liquidations as cl
from data import collect_liquidations_bybit as clb

DAY_MS = 86_400_000
T0 = 1_790_294_400_000  # 2026-09-25 00:00:00 UTC
WALL0 = 1_790_294_400.5  # czas odbioru (s) podstawiany w testach


def _msg(t_ms: int, sym: str = "BTCUSDT", side: str = "Buy", v: str = "0.5", p: str = "60000"):
    return {
        "topic": f"allLiquidation.{sym}",
        "type": "snapshot",
        "ts": t_ms + 100,
        "data": [{"T": t_ms, "s": sym, "S": side, "v": v, "p": p}],
    }


# ------------------------------------------------------------------ parser
def test_parse_message_maps_position_side_and_keeps_raw_strings():
    recs, rejected = clb.parse_message(_msg(T0 + 5, side="Buy"), rcv_ms=T0 + 300)
    assert rejected == 0 and len(recs) == 1
    r = recs[0]
    assert r == {
        "T": T0 + 5,
        "s": "BTCUSDT",
        "S": "Buy",
        "v": "0.5",
        "p": "60000",
        "pos": "long",  # Bybit: Buy = zlikwidowano pozycję LONG (w Binance odwrotnie)
        "ts": T0 + 105,
        "rcv": T0 + 300,
    }
    assert tuple(r) == clb.RECORD_FIELDS
    (short,), _ = clb.parse_message(_msg(T0, side="Sell"))
    assert short["pos"] == "short" and "rcv" not in short


def test_parse_message_keeps_good_items_and_counts_bad_ones():
    msg = _msg(T0 + 1, "ETHUSDT")
    good = dict(msg["data"][0])
    msg["data"] = [
        good,
        {**good, "s": "SOLUSDT"},  # symbol ≠ temat
        {**good, "S": "BUY"},  # nieznana strona
        {**good, "v": "0"},
        {**good, "v": "-1"},
        {**good, "p": "abc"},
        {**good, "p": 60000},  # liczba zamiast tekstu
        {**good, "v": "nan"},
        {**good, "v": "1e999"},  # nieskończoność
        {**good, "T": 10**20},
        {**good, "T": str(T0)},
        {**good, "T": True},
        {k: v for k, v in good.items() if k != "p"},
        "nie-obiekt",
        {**good, "v": "1.5e-3"},  # zapis wykładniczy, dodatni → przyjęty
    ]
    recs, rejected = clb.parse_message(msg)
    assert rejected == 13 and [r["v"] for r in recs] == ["0.5", "1.5e-3"]


@pytest.mark.parametrize(
    "bad",
    [
        "nie-dict",
        {"topic": "publicTrade.BTCUSDT", "ts": T0, "data": []},
        {"topic": "allLiquidation.btcusdt", "ts": T0, "data": []},
        {"topic": "allLiquidation.BTCUSDC", "ts": T0, "data": []},
        {"topic": "allLiquidation." + "A" * 41 + "USDT", "ts": T0, "data": []},
        {"topic": "allLiquidation.BTC-USDT", "ts": T0, "data": []},
        {"topic": "allLiquidation.BTCUSDT", "ts": T0, "data": {"T": T0}},
        {"topic": "allLiquidation.BTCUSDT", "data": []},
        {"topic": "allLiquidation.BTCUSDT", "ts": 5, "data": []},
        {"topic": "allLiquidation.BTCUSDT", "ts": True, "data": []},
    ],
)
def test_parse_message_unknown_schema_is_none(bad):
    assert clb.parse_message(bad) is None


@pytest.mark.parametrize(
    "msg,kind",
    [
        (_msg(T0), "data"),
        ({"success": True, "ret_msg": "pong", "conn_id": "x", "op": "ping"}, "pong"),
        ({"ret_msg": "pong"}, "pong"),
        ({"success": True, "ret_msg": "", "conn_id": "x", "op": "subscribe"}, "sub_ok"),
        ({"success": False, "ret_msg": "error:handler not found", "op": "subscribe"}, "sub_fail"),
        ({"op": "auth"}, "unknown"),
        ([1, 2], "unknown"),
    ],
)
def test_classify(msg, kind):
    assert clb.classify(msg) == kind


# ------------------------------------------------------------------ plan subskrypcji
symbol_st = st.from_regex(r"[A-Z0-9]{1,40}USDT", fullmatch=True)


@settings(max_examples=150, deadline=None)
@given(
    symbols=st.lists(symbol_st, max_size=120),
    per_request=st.integers(1, 12),
    max_chars=st.integers(70, 2000),
)
def test_subscribe_batches_properties(symbols, per_request, max_chars):
    plan = clb.subscribe_batches(symbols, per_request=per_request, max_chars=max_chars)
    flat = [t for conn in plan for req in conn for t in req]
    assert flat == [clb.TOPIC_PREFIX + s for s in sorted(set(symbols))]  # nic nie ginie, bez dubli
    for conn in plan:
        assert conn and all(1 <= len(req) <= per_request for req in conn)
        assert sum(clb.topic_chars(t) for req in conn for t in req) <= max_chars
    assert len(plan) <= max(1, len(flat))
    sizes = [sum(len(req) for req in conn) for conn in plan]
    assert not sizes or max(sizes) - min(sizes) <= 1  # po równo — żadnego „ogona” z kilku monet
    total = sum(clb.topic_chars(t) for t in flat)
    assert len(plan) >= -(-total // max_chars)  # nie mniej połączeń, niż wymaga budżet


def test_subscribe_batches_real_scale_fits_bybit_limit():
    # skala z 2026-09-27: 777 symboli, ~20 tys. znaków tematów — więcej niż budżet jednego połączenia
    symbols = [f"SYM{i:04d}X{'Y' * (i % 9)}USDT" for i in range(777)]
    plan = clb.subscribe_batches(symbols)
    assert len(plan) == 2
    assert [sum(len(r) for r in conn) for conn in plan] == [389, 388]  # po równo, nie 688 + 89
    for conn in plan:
        topics = [t for req in conn for t in req]
        compact = json.dumps(topics, separators=(",", ":"))
        assert len(compact) <= clb.ARGS_CHARS_BUDGET < clb.ARGS_CHARS_LIMIT
        assert all(len(req) <= clb.TOPICS_PER_REQUEST for req in conn)
    assert clb.subscribe_batches([]) == []


def test_subscribe_batches_rejects_impossible_limits():
    with pytest.raises(ValueError, match="per_request"):
        clb.subscribe_batches(["BTCUSDT"], per_request=0)
    with pytest.raises(ValueError, match="budżet"):
        clb.subscribe_batches(["BTCUSDT"], max_chars=10)


# ------------------------------------------------------------------ instrumenty
def _inst(symbol, status="Trading", kind="LinearPerpetual", settle="USDT"):
    return {"symbol": symbol, "status": status, "contractType": kind, "settleCoin": settle}


def _page(rows, cursor=""):
    return {"retCode": 0, "retMsg": "OK", "result": {"list": rows, "nextPageCursor": cursor}}


def test_parse_instruments_filters_and_returns_cursor():
    rows = [
        _inst("BTCUSDT"),
        _inst("ETHUSDC", settle="USDC"),
        _inst("XUSDT", settle="USDC"),  # nazwa pasuje do wzorca — odrzuca go dopiero rozliczenie
        _inst("BTCUSDT-26DEC26", kind="LinearFutures"),
        _inst("OLDUSDT", status="Closed"),
        _inst("NEWUSDT", status="PreLaunch"),
        _inst("weirdUSDT"),
        {"symbol": 5},
        "x",
        _inst("1000PEPEUSDT"),
    ]
    syms, cursor = clb.parse_instruments(_page(rows, "abc"))
    assert syms == ["BTCUSDT", "1000PEPEUSDT"] and cursor == "abc"
    assert clb.parse_instruments(_page([_inst("BTCUSDT")]))[1] == ""


@pytest.mark.parametrize(
    "bad",
    [{"retCode": 10001, "retMsg": "err"}, {"retCode": 0, "result": {}}, "x", {"retCode": 0}],
)
def test_parse_instruments_rejects_errors(bad):
    with pytest.raises(ValueError, match="likwidacje bybit"):
        clb.parse_instruments(bad)


def test_fetch_symbols_follows_cursor_and_deduplicates():
    pages = {"": _page([_inst("ETHUSDT"), _inst("BTCUSDT")], "c1"), "c1": _page([_inst("BTCUSDT")])}
    calls = []

    async def get_json(params):
        calls.append(dict(params))
        return pages[params.get("cursor", "")]

    assert asyncio.run(clb.fetch_symbols(get_json)) == ["BTCUSDT", "ETHUSDT"]
    assert calls == [
        {"category": "linear", "limit": "1000"},
        {"category": "linear", "limit": "1000", "cursor": "c1"},
    ]


def test_fetch_symbols_guards_endless_paging_and_empty_list():
    async def endless(params):
        return _page([_inst("BTCUSDT")], "again")

    async def empty(params):
        return _page([_inst("ETHUSDC", settle="USDC")])

    with pytest.raises(ValueError, match="stron"):
        asyncio.run(clb.fetch_symbols(endless, max_pages=3))
    with pytest.raises(ValueError, match="pusta"):
        asyncio.run(clb.fetch_symbols(empty))


# ------------------------------------------------------------------ fałszywe połączenie
@dataclass
class Wait:
    """Upływ `s` sekund bez żadnej wiadomości (zegar testu przesuwa się, nic nie śpi naprawdę)."""

    s: float


class Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


class FakeConn:
    def __init__(self, script, clock) -> None:
        self.script = list(script)
        self.clock = clock
        self.sent: list[dict] = []

    async def send(self, obj):
        self.sent.append(obj)

    async def recv(self, timeout):
        await asyncio.sleep(0)
        while self.script:
            item = self.script[0]
            if isinstance(item, Wait):
                if item.s > timeout:
                    item.s -= timeout
                    self.clock.t += timeout
                    raise asyncio.TimeoutError
                self.clock.t += item.s
                self.script.pop(0)
                continue
            self.script.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return None  # koniec strumienia


@dataclass
class ConnectFail:
    """Połączenie, które pada PRZED otwarciem, po `s` sekundach (np. limit czasu TCP/TLS)."""

    s: float


def _fake_connect(scripts, clock, conns):
    it = iter(scripts)

    @contextlib.asynccontextmanager
    async def connect():
        script = next(it)
        if isinstance(script, ConnectFail):
            await asyncio.sleep(0)
            clock.t += script.s
            raise ConnectionError("nie udało się połączyć")
        conn = FakeConn(script, clock)
        conns.append(conn)
        yield conn

    return connect


def _get_json_seq(*symbol_lists):
    """Kolejne wywołania listy instrumentów → kolejne listy symboli (ostatnia się powtarza)."""
    lists = list(symbol_lists)

    async def get_json(params):
        syms = lists.pop(0) if len(lists) > 1 else lists[0]
        if isinstance(syms, Exception):
            raise syms
        return _page([_inst(s) for s in syms])

    return get_json


def _run(tmp_path, scripts, symbols=(["BTCUSDT", "ETHUSDT"],), **kw):
    clock, conns, delays, logs = Clock(), [], [], []

    async def fake_sleep(s):
        delays.append(s)

    state = asyncio.run(
        clb.run(
            tmp_path,
            connect=_fake_connect(scripts, clock, conns),
            get_json=_get_json_seq(*symbols),
            sleep=fake_sleep,
            clock=clock,
            wall=lambda: WALL0,
            log=logs.append,
            **kw,
        )
    )
    return state, conns, delays, logs


SUB_OK = {"success": True, "ret_msg": "", "conn_id": "c", "op": "subscribe"}
PONG = {"success": True, "ret_msg": "pong", "conn_id": "c", "op": "ping"}


def test_run_writes_by_utc_day_counts_and_pings(tmp_path):
    bad_item = _msg(T0 + 3)
    bad_item["data"].append({**bad_item["data"][0], "v": "-2"})
    script = [
        SUB_OK,
        _msg(T0 + 1, "BTCUSDT", "Buy"),
        {"topic": "publicTrade.BTCUSDT"},  # nieznany schemat → pominięte
        {"success": False, "ret_msg": "error:handler not found", "op": "subscribe"},
        Wait(25),  # ≥ 20 s ciszy → ping
        PONG,
        bad_item,  # 1 dobra + 1 zła likwidacja
        _msg(T0 + DAY_MS - 1, "ETHUSDT", "Sell"),
        _msg(T0 + DAY_MS, "ETHUSDT", "Sell"),  # nowy dzień UTC
        ConnectionError("zerwane"),
    ]
    state, conns, delays, logs = _run(tmp_path, [script], max_cycles=1)
    sent = conns[0].sent
    assert sent[0] == {
        "op": "subscribe",
        "req_id": "0-0",
        "args": ["allLiquidation.BTCUSDT", "allLiquidation.ETHUSDT"],
    }
    assert {"op": "ping"} in sent
    assert state["events"] == 4 and state["skipped"] == 2 and state["pongs"] == 1
    assert state["sub_ok"] == 1 and state["sub_fail"] == 1 and state["messages"] == 4
    assert state["reconnects"] == 1 and "ConnectionError" in state["last_error"]
    assert state["symbols"] == 2 and state["connections"] == 1
    d1 = [json.loads(x) for x in (tmp_path / "2026-09-25.jsonl").read_text().splitlines()]
    d2 = [json.loads(x) for x in (tmp_path / "2026-09-26.jsonl").read_text().splitlines()]
    assert [(r["s"], r["pos"]) for r in d1] == [
        ("BTCUSDT", "long"),
        ("BTCUSDT", "long"),
        ("ETHUSDT", "short"),
    ]
    assert [r["T"] for r in d2] == [T0 + DAY_MS] and d2[0]["rcv"] == int(WALL0 * 1000)
    st_ = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert st_["events"] == 4 and st_["last_event_ms"] == T0 + DAY_MS and st_["sub_fail"] == 1
    assert st_["source"] == clb.STREAM_URL
    assert any("NIEUDANA" in x for x in logs)
    txt = clb.status_text(tmp_path)
    assert "kolektor pid" in txt and "symboli 2 w 1 połączeniach" in txt


def test_run_reconnects_after_silence_with_backoff(tmp_path):
    # Bybit odpowiada na każdy ping (pong co ~20 s), ale likwidacji brak: pong NIE jest znakiem
    # życia danych — po 15 min i tak ponowne połączenie (strażnik „połączenie żyje, dane nie płyną”).
    scripts = [
        [SUB_OK, _msg(T0 + 1), *([Wait(20), PONG] * 60)],
        [SUB_OK, _msg(T0 + 2), ConnectionError("x")],
    ]
    state, conns, delays, logs = _run(tmp_path, scripts, max_cycles=2)
    assert state["reconnects"] == 2 and state["events"] == 2 and len(conns) == 2
    assert state["pongs"] >= 40
    assert delays == [1.0]  # po drugim rozłączeniu pętla kończy się (max_cycles) bez odczekania
    assert any("cisza > 900 s" in x for x in logs)
    pings = sum(1 for m in conns[0].sent if m == {"op": "ping"})
    assert 40 <= pings <= 46  # ping co 20 s (nie częściej) przez ~900 s ciszy


def test_run_backoff_grows_for_quick_failures_and_resets_after_stable_cycle(tmp_path):
    scripts = [
        [ConnectionError("a")],
        [ConnectionError("b")],
        [ConnectionError("c")],
        [SUB_OK, _msg(T0 + 1), Wait(70), _msg(T0 + 2), ConnectionError("d")],  # cykl > 60 s
        [ConnectionError("e")],
    ]
    state, _, delays, _ = _run(tmp_path, scripts, max_cycles=5)
    assert delays == [1.0, 2.0, 4.0, 1.0]


def test_run_refreshes_symbols_and_resubscribes_new_listing(tmp_path):
    scripts = [
        [SUB_OK, _msg(T0 + 1), Wait(10**6)],  # połączenie żyje do końca okna odświeżenia
        [SUB_OK, _msg(T0 + 2, "NEWUSDT"), ConnectionError("koniec testu")],
    ]
    state, conns, delays, logs = _run(
        tmp_path,
        scripts,
        symbols=(["BTCUSDT"], ["BTCUSDT", "NEWUSDT"]),
        max_cycles=2,
        refresh_s=100.0,
        silence_s=10**7,
    )
    assert state["refreshes"] == 1 and state["reconnects"] == 1 and delays == []
    assert conns[0].sent[0]["args"] == ["allLiquidation.BTCUSDT"]
    assert conns[1].sent[0]["args"] == ["allLiquidation.BTCUSDT", "allLiquidation.NEWUSDT"]
    assert any("nowe 1: NEWUSDT" in x for x in logs) and state["symbols"] == 2


def test_run_keeps_old_symbols_when_refresh_fails(tmp_path):
    scripts = [
        [SUB_OK, Wait(10**6)],
        [SUB_OK, ConnectionError("koniec testu")],
    ]
    state, conns, _, logs = _run(
        tmp_path,
        scripts,
        symbols=(["BTCUSDT"], OSError("sieć"), ["ETHUSDT"]),
        max_cycles=2,
        refresh_s=100.0,
        silence_s=10**7,
    )
    assert conns[1].sent[0]["args"] == ["allLiquidation.BTCUSDT"]
    assert any("zostaje stara lista" in x for x in logs)


def test_run_retries_symbol_list_with_backoff(tmp_path):
    scripts = [[SUB_OK, _msg(T0 + 1), ConnectionError("x")]]
    state, _, delays, _ = _run(
        tmp_path,
        scripts,
        symbols=(OSError("dns"), OSError("dns"), ["BTCUSDT"]),
        max_cycles=3,
    )
    assert delays == [1.0, 2.0] and state["events"] == 1 and state["reconnects"] == 3


def test_run_multiple_connections_one_failure_restarts_all(tmp_path, monkeypatch):
    orig = clb.subscribe_batches
    monkeypatch.setattr(clb, "subscribe_batches", lambda s: orig(s, max_chars=60))
    scripts = [
        [SUB_OK, _msg(T0 + 1, "AAAUSDT"), Wait(10**6)],
        [SUB_OK, _msg(T0 + 2, "CCCUSDT"), ConnectionError("zerwane #1")],
    ]
    state, conns, delays, _ = _run(
        tmp_path, scripts, symbols=(["AAAUSDT", "BBBUSDT", "CCCUSDT"],), max_cycles=1
    )
    assert state["connections"] == 2 and len(conns) == 2
    assert [c.sent[0]["req_id"] for c in conns] == ["0-0", "1-0"]
    assert state["events"] == 2 and state["reconnects"] == 1 and "zerwane #1" in state["last_error"]


# ------------------------------------------------------------------ kontrola pozytywna
def test_probe_counts_and_does_not_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    clock, conns, out = Clock(), [], []
    script = [
        SUB_OK,
        _msg(T0 + 1, "BTCUSDT", "Buy", v="2", p="100"),
        _msg(T0 + 2, "ETHUSDT", "Sell", v="1", p="50"),
        _msg(T0 + 3, "BTCUSDT", "Sell", v="1", p="10"),
        _msg(T0 + 4, "XRPUSDT", "Buy", v="1", p="1"),
        Wait(10**6),
    ]
    summary = asyncio.run(
        clb.probe(
            60,
            connect=_fake_connect([script], clock, conns),
            get_json=_get_json_seq(["BTCUSDT", "ETHUSDT", "XRPUSDT"]),
            clock=clock,
            wall=lambda: WALL0,
            out=out.append,
        )
    )
    assert summary["events"] == 4 and summary["long"] == 2 and summary["short"] == 2
    assert summary["symbols"] == 3 and summary["notional_usd"] == pytest.approx(261.0)
    assert summary["per_min"] == pytest.approx(4.0) and summary["error"] is False
    assert summary["top"][0] == ("BTCUSDT", 2)
    assert sum(1 for x in out if x.startswith("przykład ")) == 3
    assert list(tmp_path.iterdir()) == []  # próba nic nie zapisuje


def test_probe_warns_on_zero_events():
    clock, out = Clock(), []
    summary = asyncio.run(
        clb.probe(
            30,
            connect=_fake_connect([[SUB_OK, Wait(10**6)]], clock, []),
            get_json=_get_json_seq(["BTCUSDT"]),
            clock=clock,
            wall=lambda: WALL0,
            out=out.append,
        )
    )
    assert summary["events"] == 0 and any(x.startswith("UWAGA: 0 likwidacji") for x in out)


# ------------------------------------------------------------------ warstwa sieciowa i odczyt
class _Msg:
    def __init__(self, type_, data=None):
        self.type, self.data = type_, data


class _FakeWs:
    def __init__(self, frames, gate):
        self.frames, self.gate, self.sent = frames, gate, []

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        await self.gate.wait()  # ramki przychodzą dopiero po pierwszym przekroczeniu czasu
        for f in self.frames:
            yield f

    async def send_str(self, s):
        self.sent.append(s)


def test_ws_conn_timeout_does_not_break_stream_and_bad_json_is_marked():
    async def go():
        gate = asyncio.Event()
        ws = _FakeWs(
            [
                _Msg(aiohttp.WSMsgType.TEXT, json.dumps(_msg(T0))),
                _Msg(aiohttp.WSMsgType.TEXT, "{nie json"),
                _Msg(aiohttp.WSMsgType.CLOSE),
            ],
            gate,
        )
        conn = clb._WsConn(ws)
        with pytest.raises(asyncio.TimeoutError):
            await conn.recv(0.01)
        gate.set()
        first = await conn.recv(1.0)
        second = await conn.recv(1.0)
        end = await conn.recv(1.0)
        await conn.send({"op": "ping"})
        await conn.close()
        return first, second, end, ws.sent

    first, second, end, sent = asyncio.run(go())
    assert first["topic"] == "allLiquidation.BTCUSDT"
    assert "_niepoprawny_json" in second and clb.classify(second) == "unknown"
    assert end is None and sent == ['{"op": "ping"}']


def test_connect_and_get_json_reject_non_tls():
    async def go_ws():
        async with clb._connect("ws://stream.bybit.com/v5/public/linear"):
            pass

    with pytest.raises(ValueError, match="tylko wss"):
        asyncio.run(go_ws())
    with pytest.raises(ValueError, match="tylko https"):
        asyncio.run(clb._get_json({}, url="http://api.bybit.com/v5/market/instruments-info"))


def test_urls_are_fixed_bybit_public_endpoints():
    assert clb.STREAM_URL == "wss://stream.bybit.com/v5/public/linear"
    assert clb.INSTRUMENTS_URL == "https://api.bybit.com/v5/market/instruments-info"


def test_load_day_converts_numbers_and_times(tmp_path):
    w = cl.DayWriter(tmp_path, time_key="T")
    for m in (_msg(T0 + 1, v="1.5"), _msg(T0 + 2, "ETHUSDT", "Sell", v="2")):
        (rec,), _ = clb.parse_message(m, rcv_ms=T0 + 500)
        w.write(rec)
    w.close()
    df = clb.load_day(tmp_path / "2026-09-25.jsonl")
    assert df["v"].tolist() == [1.5, 2.0] and df["p"].dtype == float
    assert str(df["T"].dt.tz) == "UTC" and df["T"].iloc[0].isoformat().startswith("2026-09-25")
    assert df["pos"].tolist() == ["long", "short"]


def test_main_arguments(tmp_path, capsys):
    assert clb.main(["--nieznany"]) == 2
    assert clb.main(["--probe"]) == 2
    assert clb.main(["--probe", "0"]) == 2
    assert clb.main(["--probe", "abc"]) == 2
    assert clb.main(["--dir", str(tmp_path), "--status"]) == 0
    assert "brak" in capsys.readouterr().out


def test_default_dir_is_outside_repo():
    assert clb.DEFAULT_DIR.name == "likwidacje_bybit" and clb.DEFAULT_DIR.is_absolute()


# ------------------------------------------------------------------ nieudana subskrypcja
TOPIC = clb.TOPIC_PREFIX
NOT_FOUND = "error:handler not found,topic:"


def test_after_sub_fail_drops_named_topic_and_resends_rest():
    args = [TOPIC + "BTCUSDT", TOPIC + "BADUSDT", TOPIC + "ETHUSDT"]
    resend, rejected = clb.after_sub_fail(args, NOT_FOUND + TOPIC + "BADUSDT")
    assert resend == [[TOPIC + "BTCUSDT", TOPIC + "ETHUSDT"]] and rejected == [TOPIC + "BADUSDT"]
    assert clb.after_sub_fail([TOPIC + "BADUSDT"], NOT_FOUND + TOPIC + "BADUSDT") == (
        [],
        [TOPIC + "BADUSDT"],
    )


def test_after_sub_fail_already_subscribed_is_not_rejected():
    # odpowiedź żywego Bybit 2026-09-27: `error:already subscribed,topic:allLiquidation.ETHUSDT`
    args = [TOPIC + "BTCUSDT", TOPIC + "ETHUSDT"]
    resend, rejected = clb.after_sub_fail(args, "error:already subscribed,topic:" + args[1])
    assert resend == [[TOPIC + "BTCUSDT"]] and rejected == []


@pytest.mark.parametrize(
    "ret_msg", ["error:handler not found", None, "topic:" + TOPIC + "OBCYUSDT"]
)
def test_after_sub_fail_without_usable_topic_splits_into_singles(ret_msg):
    args = [TOPIC + "AUSDT", TOPIC + "BUSDT"]
    assert clb.after_sub_fail(args, ret_msg) == ([[TOPIC + "AUSDT"], [TOPIC + "BUSDT"]], [])
    assert clb.after_sub_fail(args[:1], ret_msg) == ([], args[:1])  # jeden temat → odrzucony


@settings(max_examples=150, deadline=None)
@given(
    symbols=st.lists(symbol_st, min_size=1, max_size=15, unique=True),
    data=st.data(),
    names_topic=st.booleans(),
)
def test_after_sub_fail_converges_on_simulated_bybit(symbols, data, names_topic):
    # Symulowany Bybit: żądanie z choćby jednym złym tematem jest odrzucane w całości; odpowiedź
    # podaje PIERWSZY zły temat (albo — wariant ostrożny — żadnego). Po naprawie: każdy dobry temat
    # subskrybowany, każdy zły odrzucony, liczba żądań ograniczona.
    args = [TOPIC + s for s in symbols]
    bad = set(data.draw(st.lists(st.sampled_from(args), unique=True)))
    subscribed, rejected, queue, steps = set(), set(), [args], 0
    while queue:
        steps += 1
        assert steps <= 2 * len(args) + 2
        req = queue.pop()
        first_bad = next((t for t in req if t in bad), None)
        if first_bad is None:
            assert not subscribed & set(req)  # nic nie jest subskrybowane dwa razy
            subscribed.update(req)
            continue
        msg = NOT_FOUND + first_bad if names_topic else "error:handler not found"
        resend, rej = clb.after_sub_fail(req, msg)
        assert all(1 <= len(r) <= len(req) for r in resend)
        rejected.update(rej)
        queue.extend(resend)
    assert subscribed == set(args) - bad and rejected == bad


def _sub_fail(req_id: str, topic: str) -> dict:
    return {
        "success": False,
        "ret_msg": NOT_FOUND + TOPIC + topic,
        "conn_id": "c",
        "req_id": req_id,
        "op": "subscribe",
    }


def test_run_repairs_failed_subscription_and_skips_bad_topic_until_refresh(tmp_path):
    scripts = [
        [
            _sub_fail("0-0", "BADUSDT"),  # całe żądanie odrzucone przez jeden zły temat
            {**SUB_OK, "req_id": "0-r1"},
            _msg(T0 + 1, "ETHUSDT"),
            ConnectionError("zerwane"),
        ],
        [{**SUB_OK, "req_id": "0-0"}, ConnectionError("znowu")],
    ]
    state, conns, _, logs = _run(
        tmp_path, scripts, symbols=(["BADUSDT", "BTCUSDT", "ETHUSDT"],), max_cycles=2
    )
    good = [TOPIC + "BTCUSDT", TOPIC + "ETHUSDT"]
    assert conns[0].sent[0]["args"] == [TOPIC + "BADUSDT", *good]
    assert {"op": "subscribe", "req_id": "0-r1", "args": good} in conns[0].sent  # od razu
    assert conns[1].sent[0]["args"] == good  # po ponownym połączeniu zły temat już nie wraca
    assert state["sub_fail"] == 1 and state["resubscribed"] == 2 and state["events"] == 1
    assert state["rejected_topics"] == [TOPIC + "BADUSDT"] and state["rejected_count"] == 1
    assert state["symbols"] == 2
    assert any("odrzucony przez Bybit" in x for x in logs)
    assert "tematy odrzucone 1" in clb.status_text(tmp_path)


def test_run_gives_rejected_topic_new_chance_after_refresh(tmp_path):
    scripts = [
        [_sub_fail("0-0", "BADUSDT"), Wait(10**6)],
        [SUB_OK, ConnectionError("koniec testu")],
    ]
    state, conns, _, _ = _run(
        tmp_path,
        scripts,
        symbols=(["BADUSDT", "BTCUSDT"],),
        max_cycles=2,
        refresh_s=100.0,
        silence_s=10**7,
    )
    assert conns[0].sent[1] == {"op": "subscribe", "req_id": "0-r1", "args": [TOPIC + "BTCUSDT"]}
    assert conns[1].sent[0]["args"] == [TOPIC + "BADUSDT", TOPIC + "BTCUSDT"]
    assert state["refreshes"] == 1 and state["rejected_count"] == 0


def test_run_retries_failed_refresh_after_retry_interval_not_full_period(tmp_path):
    clock, conns, calls = Clock(), [], []
    answers = [["BTCUSDT"], OSError("sieć"), ["ETHUSDT"]]

    async def get_json(params):
        calls.append(clock.t)
        a = answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return _page([_inst(s) for s in a])

    async def fake_sleep(s):
        pass

    scripts = [
        [SUB_OK, Wait(10**6)],
        [SUB_OK, Wait(10**6)],
        [SUB_OK, ConnectionError("koniec testu")],
    ]
    asyncio.run(
        clb.run(
            tmp_path,
            connect=_fake_connect(scripts, clock, conns),
            get_json=get_json,
            sleep=fake_sleep,
            clock=clock,
            wall=lambda: WALL0,
            log=[].append,
            max_cycles=3,
            refresh_s=1000.0,
            refresh_retry_s=100.0,
            silence_s=10**7,
        )
    )
    # lista: start, nieudane odświeżenie po 1000 s, ponowna próba po 100 s (nie po kolejnych 1000)
    assert [t - calls[0] for t in calls] == pytest.approx([0, 1000, 1100], abs=1.0)
    assert conns[1].sent[0]["args"] == [TOPIC + "BTCUSDT"]
    assert conns[2].sent[0]["args"] == [TOPIC + "ETHUSDT"]


def test_run_backoff_keeps_growing_when_connection_fails_before_opening(tmp_path):
    # połączenie wisi 70 s i pada przed otwarciem: cykl > 60 s, ale nic się nie połączyło —
    # odczekanie NIE może się zerować (limit 500 połączeń / 5 min na IP)
    scripts = [ConnectFail(70), ConnectFail(70), ConnectFail(70)]
    state, conns, delays, _ = _run(tmp_path, scripts, max_cycles=3)
    assert delays == [1.0, 2.0] and conns == [] and state["reconnects"] == 3


@pytest.mark.parametrize("events,error,code", [(3, False, 0), (0, False, 1), (3, True, 1)])
def test_main_probe_exit_code(monkeypatch, events, error, code):
    seen = []

    async def fake_probe(seconds, out=print, **kw):
        seen.append(seconds)
        return {"events": events, "error": error}

    monkeypatch.setattr(clb, "probe", fake_probe)
    assert clb.main(["--probe", "5"]) == code and seen == [5.0]


def test_read_limited_rejects_oversized_body():
    async def chunks(parts):
        for part in parts:
            yield part

    assert asyncio.run(clb.read_limited(chunks([b"ab", b"cd"]), limit=4)) == b"abcd"
    with pytest.raises(ValueError, match="większa"):
        asyncio.run(clb.read_limited(chunks([b"ab", b"cde"]), limit=4))
    assert clb.MAX_REST_BYTES >= 8 * 1024 * 1024  # lista 2026-09-27 ma ~0,8 MB
