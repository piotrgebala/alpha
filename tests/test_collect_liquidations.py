"""Testy kolektora likwidacji (`data/collect_liquidations.py`) — bez sieci: parser, pliki dzienne,
odczekanie, pętla z podmienionym połączeniem (zapis, pomijanie złych wiadomości, ponowne łączenie).
"""

from __future__ import annotations

import asyncio
import contextlib
import json

import pytest

from data import collect_liquidations as cl

DAY_MS = 86_400_000
E0 = 1_790_294_400_000  # 2026-09-25 00:00:00 UTC


def _msg(e_ms: int, sym: str = "BTCUSDT", side: str = "SELL", q: str = "0.014") -> dict:
    return {
        "e": "forceOrder",
        "E": e_ms,
        "o": {
            "s": sym,
            "S": side,
            "o": "LIMIT",
            "f": "IOC",
            "q": q,
            "p": "9910",
            "ap": "9910.5",
            "X": "FILLED",
            "l": q,
            "z": q,
            "T": e_ms - 3,
        },
        "ps": sym,
        "st": 1,
    }


def test_parse_event_flattens_and_keeps_raw_strings():
    rec = cl.parse_event(_msg(E0 + 5))
    assert rec["E"] == E0 + 5 and rec["s"] == "BTCUSDT" and rec["S"] == "SELL"
    assert rec["q"] == "0.014" and rec["ap"] == "9910.5" and rec["T"] == E0 + 2  # bez przeliczeń
    assert rec["st"] == 1 and rec["ps"] == "BTCUSDT"
    assert list(rec) == ["E", "st", "ps", *cl.ORDER_FIELDS]
    assert "st" not in cl.parse_event({k: v for k, v in _msg(E0).items() if k not in ("st", "ps")})
    # jak na żywo (2026-09-25): `ps`/`st` wewnątrz zlecenia, nie na wierzchu
    live = {k: v for k, v in _msg(E0).items() if k not in ("st", "ps")}
    live["o"] = {**live["o"], "ps": "XAUUSDT", "st": 1}
    rec2 = cl.parse_event(live)
    assert rec2["ps"] == "XAUUSDT" and rec2["st"] == 1 and rec2["s"] == "BTCUSDT"


@pytest.mark.parametrize(
    "bad",
    [
        {"e": "aggTrade", "E": E0, "o": {}},
        {"e": "forceOrder", "o": {}},
        {"e": "forceOrder", "E": E0, "o": "x"},
        {"e": "forceOrder", "E": E0, "o": {"s": "BTCUSDT"}},
        "nie-dict",
    ],
)
def test_parse_event_rejects_unknown_schema(bad):
    with pytest.raises(ValueError, match="likwidacje"):
        cl.parse_event(bad)


def test_day_path_uses_utc_day_of_event(tmp_path):
    assert cl.day_path(tmp_path, E0 + DAY_MS - 1).name == "2026-09-25.jsonl"
    assert cl.day_path(tmp_path, E0 + DAY_MS).name == "2026-09-26.jsonl"
    for bad in (0, -1, 10**20, cl.MAX_EVENT_MS + 1):
        with pytest.raises(ValueError, match="poza zakresem"):
            cl.day_path(tmp_path, bad)


def test_backoff_doubles_and_caps():
    assert [cl.backoff_s(i) for i in range(8)] == [1, 2, 4, 8, 16, 32, 60, 60]


def test_day_writer_rotates_by_day_and_appends(tmp_path):
    w = cl.DayWriter(tmp_path)
    w.write(cl.parse_event(_msg(E0 + 1)))
    w.write(cl.parse_event(_msg(E0 + DAY_MS + 1, "ETHUSDT")))
    w.close()
    w2 = cl.DayWriter(tmp_path)  # nowy proces tego samego dnia → dopisuje, nie nadpisuje
    w2.write(cl.parse_event(_msg(E0 + DAY_MS + 2, "SOLUSDT")))
    w2.close()
    d1 = (tmp_path / "2026-09-25.jsonl").read_text(encoding="utf-8").splitlines()
    d2 = (tmp_path / "2026-09-26.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["s"] for x in d1] == ["BTCUSDT"]
    assert [json.loads(x)["s"] for x in d2] == ["ETHUSDT", "SOLUSDT"]
    assert w2.count == 1 and w2.last_event_ms == E0 + DAY_MS + 2


def _fake_connect(batches: list[list]):
    """Każde połączenie oddaje kolejną paczkę: wiadomości (dict) albo wyjątek do rzucenia."""
    it = iter(batches)

    @contextlib.asynccontextmanager
    async def connect():
        batch = next(it)

        async def gen():
            for m in batch:
                if isinstance(m, Exception):
                    raise m
                yield m

        yield gen()

    return connect


def test_run_writes_skips_bad_messages_and_reconnects(tmp_path):
    batches = [
        [
            _msg(E0 + 1),
            {"e": "aggTrade", "E": E0},  # inny typ → pominięte
            _msg(10**20),  # data poza zakresem (OverflowError) → pominięte, nie zerwanie
            _msg(E0 + 2),
            ConnectionError("zerwane"),
        ],
        [_msg(E0 + DAY_MS + 3)],  # drugie połączenie kończy się normalnie (koniec strumienia)
    ]
    delays, logs = [], []

    async def fake_sleep(s):
        delays.append(s)

    state = asyncio.run(
        cl.run(
            tmp_path,
            connect=_fake_connect(batches),
            sleep=fake_sleep,
            max_reconnects=2,
            log=logs.append,
            clock=lambda: 1e9,  # status zapisywany od razu
        )
    )
    assert state["events"] == 3 and state["skipped"] == 2 and state["reconnects"] == 2
    assert delays == [1.0]  # po 2. rozłączeniu pętla kończy się (max_reconnects) bez odczekania
    assert "koniec strumienia" in state["last_error"]
    st = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert st["events"] == 3 and st["reconnects"] == 2 and st["last_event_ms"] == E0 + DAY_MS + 3
    assert sum(1 for x in logs if x.startswith("pominięto")) == 2
    assert sum(1 for x in logs if x.startswith("rozłączono: ConnectionError")) == 1
    assert (tmp_path / "2026-09-25.jsonl").exists() and (tmp_path / "2026-09-26.jsonl").exists()
    assert "kolektor pid" in cl.status_text(tmp_path)


def test_load_day_converts_numbers_and_times(tmp_path):
    w = cl.DayWriter(tmp_path)
    w.write(cl.parse_event(_msg(E0 + 1, q="1.5")))
    w.write(cl.parse_event(_msg(E0 + 2, "ETHUSDT", "BUY", q="2")))
    w.close()
    df = cl.load_day(tmp_path / "2026-09-25.jsonl")
    assert df["q"].tolist() == [1.5, 2.0] and df["ap"].dtype == float
    assert str(df["E"].dt.tz) == "UTC" and df["E"].iloc[0].isoformat().startswith("2026-09-25")
    assert df["s"].tolist() == ["BTCUSDT", "ETHUSDT"]


def test_stream_url_is_market_category():
    assert cl.STREAM_URL.startswith("wss://fstream.binance.com/market/ws/")  # `/ws/…` milczy


def test_connect_rejects_non_wss():
    async def go():
        async with cl._connect("https://fstream.binance.com/market/ws/!forceOrder@arr"):
            pass

    with pytest.raises(ValueError, match="tylko wss"):
        asyncio.run(go())
