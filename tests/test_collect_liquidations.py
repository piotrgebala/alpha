"""Testy kolektora likwidacji (`data/collect_liquidations.py`) — bez sieci: parser, pliki dzienne,
odczekanie, pętla z podmienionym połączeniem (zapis, pomijanie złych wiadomości, ponowne łączenie),
czas transakcji `T` sprawdzany przy zapisie regułą indeksu (zadanie 021): rekord poprawny, `T`
z przyszłości, `T` z poprzedniego dnia przy `E` po północy, brak `T`.
"""

from __future__ import annotations

import asyncio
import contextlib
import json

import pytest

from data import collect_liquidations as cl
from data import liquidation_index as li

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


# ------------------------------------------------------------------ zakres T przy zapisie (zadanie 021)
def _run_one(tmp_path, msgs: list) -> tuple[dict, list[str]]:
    """Jedno połączenie z podanymi wiadomościami, koniec strumienia, koniec pętli → (stan, log)."""
    logs: list[str] = []

    async def no_sleep(_s):
        return None

    state = asyncio.run(
        cl.run(
            tmp_path,
            connect=_fake_connect([msgs]),
            sleep=no_sleep,
            max_reconnects=1,
            log=logs.append,
            clock=lambda: 1e9,
        )
    )
    return state, logs


def _lines(path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _with_t(msg: dict, t) -> dict:
    msg["o"]["T"] = t
    return msg


def test_t_problem_ta_sama_regula_co_indeks_bez_nowego_progu():
    rec = cl.parse_event(_msg(E0 + 5))
    assert cl.t_problem(rec) is None
    assert "poza zakresem 2019-01-01…2100-01-01 UTC" in cl.t_problem({**rec, "T": 10**20})
    assert "nie jest liczbą ms" in cl.t_problem({**rec, "T": "abc"})
    assert "nie jest liczbą ms" in cl.t_problem({**rec, "T": None})
    assert cl.t_problem({k: v for k, v in rec.items() if k != "T"}).endswith(": brak T")
    # reguła nie porównuje T z E: doba wcześniej i doba później (w 2019…2100) są poprawne
    assert cl.t_problem({**rec, "T": E0 - DAY_MS}) is None
    assert cl.t_problem({**rec, "T": E0 + DAY_MS}) is None


def test_run_rekord_poprawny_licznik_T_zero(tmp_path):
    state, logs = _run_one(tmp_path, [_msg(E0 + 5)])
    assert state["events"] == 1 and state["skipped"] == 0
    assert state["t_out_of_range"] == 0 and state["t_out_of_range_examples"] == []
    st_ = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert st_["t_out_of_range"] == 0 and st_["t_out_of_range_examples"] == []
    assert not [x for x in logs if x.startswith("T poza zakresem")]
    txt = cl.status_text(tmp_path)
    assert "(pominiętych 0; T poza zakresem 0 (zapisane bez zmian))" in txt
    assert "przykłady T" not in txt
    assert json.loads(_lines(tmp_path / "2026-09-25.jsonl")[0]) == cl.parse_event(_msg(E0 + 5))


def test_run_T_z_przyszlosci_zapisany_bez_zmian_policzony_w_statusie_i_logu(tmp_path):
    far = _with_t(_msg(E0 + 7), 10**20)  # po 2100 roku → łamie regułę indeksu
    tomorrow = _with_t(_msg(E0 + 8, "ETHUSDT"), E0 + DAY_MS + 8)  # jutro, ale w 2019…2100
    state, logs = _run_one(tmp_path, [_msg(E0 + 5), far, tomorrow])
    assert state["events"] == 3 and state["skipped"] == 0 and state["t_out_of_range"] == 1
    lines = _lines(tmp_path / "2026-09-25.jsonl")  # plik dnia wg E, nie wg T
    assert lines[1] == json.dumps(cl.parse_event(far), separators=(",", ":"))  # bajt w bajt
    assert json.loads(lines[1])["T"] == 10**20 and json.loads(lines[2])["T"] == E0 + DAY_MS + 8
    (example,) = state["t_out_of_range_examples"]
    assert example.startswith(f"'BTCUSDT' E={E0 + 7}: T ") and "poza zakresem" in example
    t_logs = [x for x in logs if x.startswith("T poza zakresem")]
    assert t_logs == [f"T poza zakresem (1), zapisano bez zmian: {example}"]
    st_ = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert st_["t_out_of_range"] == 1 and st_["t_out_of_range_examples"] == [example]
    txt = cl.status_text(tmp_path)
    assert "T poza zakresem 1 (zapisane bez zmian)" in txt
    assert txt.endswith(f"; przykłady T poza zakresem: {example}")
    # indeks (a przez niego kopia) liczy TEN SAM rekord jako złą linię — teraz widać to przy zapisie
    idx = li.aggregate("binance", "2026-09-25", lines)
    assert idx.lines == 3 and idx.bad_lines == state["t_out_of_range"] == 1


def test_run_T_z_poprzedniego_dnia_przy_E_po_polnocy_poprawny(tmp_path):
    msg = _with_t(
        _msg(E0 + DAY_MS + 40), E0 + DAY_MS - 20
    )  # E 26.09 00:00:00,040; T 25.09 23:59:59,980
    state, logs = _run_one(tmp_path, [msg])
    assert state["events"] == 1 and state["skipped"] == 0 and state["t_out_of_range"] == 0
    assert not (tmp_path / "2026-09-25.jsonl").exists()  # plik wg E — układ plików bez zmian
    lines = _lines(tmp_path / "2026-09-26.jsonl")
    assert lines == [json.dumps(cl.parse_event(msg), separators=(",", ":"))]
    idx = li.aggregate("binance", "2026-09-26", lines)  # indeks też przyjmuje
    assert idx.bad_lines == 0 and idx.rows[0]["pierwsze_utc"] == "2026-09-25T23:59:59.980Z"
    assert not [x for x in logs if x.startswith("T poza zakresem")]


def test_run_brak_T_to_nieznany_schemat_pominiety_i_policzony(tmp_path):
    no_t = _msg(E0 + 9)
    del no_t["o"]["T"]
    state, logs = _run_one(tmp_path, [no_t, _msg(E0 + 10)])
    assert state["events"] == 1 and state["skipped"] == 1 and state["t_out_of_range"] == 0
    assert [json.loads(x)["E"] for x in _lines(tmp_path / "2026-09-25.jsonl")] == [E0 + 10]
    (skip_log,) = [x for x in logs if x.startswith("pominięto")]
    assert skip_log.startswith("pominięto (1): likwidacje: brak pól ['T']")


def test_run_zle_E_i_zle_T_tylko_pominiety_bez_licznika_T(tmp_path):
    """Bez dnia pliku (E poza zakresem) rekordu nie da się zapisać — liczy się jak dotąd w `skipped`,
    a licznik `T` obejmuje wyłącznie rekordy ZAPISANE."""
    state, _ = _run_one(tmp_path, [_msg(10**20)])  # E i T poza zakresem
    assert state["events"] == 0 and state["skipped"] == 1 and state["t_out_of_range"] == 0
    assert not list(tmp_path.glob("*.jsonl"))


def test_run_licznik_T_przyklady_i_log_ograniczone(tmp_path):
    msgs = [_with_t(_msg(E0 + i), -i) for i in range(1001)]  # wszystkie T przed 2019
    state, logs = _run_one(tmp_path, msgs)
    assert state["events"] == 1001 and state["t_out_of_range"] == 1001
    assert len(_lines(tmp_path / "2026-09-25.jsonl")) == 1001  # żaden rekord nie zginął
    assert len(state["t_out_of_range_examples"]) == cl.T_EXAMPLES
    numbers = [x.split(")")[0] for x in logs if x.startswith("T poza zakresem")]
    assert numbers == [f"T poza zakresem ({n}" for n in (1, 2, 3, 4, 5, 1000)]


def test_status_text_procesu_sprzed_zmiany_bez_licznika_T(tmp_path):
    """Stary proces (bez pola `t_out_of_range`) → tekst jak dotąd; po restarcie pole się pojawia."""
    cl.write_status(tmp_path, pid=7, events=3, skipped=0, reconnects=0, last_event_ms=E0)
    txt = cl.status_text(tmp_path)
    assert "kolektor pid 7" in txt and "(pominiętych 0)" in txt and "T poza zakresem" not in txt
