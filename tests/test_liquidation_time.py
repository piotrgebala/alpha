"""Testy wspólnej reguły czasu likwidacji (`data/liquidation_time.py`, zadanie 021) — bez sieci:
granice, typy wartości z JSON, ucięte komunikaty, jedno miejsce granic w kodzie; właściwość
w `hypothesis`: indeks (a przez niego kopia), kolektor Binance (licznik `T` poza zakresem) i kolektor
Bybit (`_is_ms`) oceniają ten sam czas tak samo — jedna reguła, bez nowego progu.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data import collect_liquidations as cl
from data import collect_liquidations_bybit as clb
from data import liquidation_index as li
from data import liquidation_time as lt

D0 = 1_790_294_400_000  # 2026-09-25 00:00:00 UTC
UTC = dt.timezone.utc


def _bn_line(t) -> str:
    """Linia pliku LK0 (jak `json.dumps` kolektora) z dowolną wartością pola `T`."""
    rec = {"E": D0 + 5, "st": 1, "ps": "BTCUSDT", "s": "BTCUSDT", "S": "SELL", "o": "LIMIT"}
    rec.update({"f": "IOC", "q": "2", "p": "100", "ap": "101", "X": "FILLED", "l": "2", "z": "2"})
    rec["T"] = t
    return json.dumps(rec, separators=(",", ":"))


def _index_accepts(t) -> bool:
    try:
        li.parse_line("binance", _bn_line(t))
    except ValueError:
        return False
    return True


def _rule_accepts(t) -> bool:
    try:
        lt.event_time_ms(t)
    except ValueError:
        return False
    return True


# ------------------------------------------------------------------ granice i typy
def test_granice_to_polnoc_2019_i_2100_utc():
    assert dt.datetime.fromtimestamp(lt.MIN_EVENT_MS / 1000, tz=UTC) == dt.datetime(
        2019, 1, 1, tzinfo=UTC
    )
    assert dt.datetime.fromtimestamp(lt.MAX_EVENT_MS / 1000, tz=UTC) == dt.datetime(
        2100, 1, 1, tzinfo=UTC
    )


def test_czas_w_zakresie_wraca_jako_int_wlacznie_z_granicami():
    for t in (lt.MIN_EVENT_MS, D0, lt.MAX_EVENT_MS):
        assert lt.event_time_ms(t) == t and type(lt.event_time_ms(t)) is int


@pytest.mark.parametrize(
    "t", [lt.MIN_EVENT_MS - 1, lt.MAX_EVENT_MS + 1, 0, -1, 10**17, 10**20, -(10**16)]
)
def test_poza_zakresem_odrzucony(t):
    with pytest.raises(ValueError, match="poza zakresem 2019-01-01…2100-01-01 UTC"):
        lt.event_time_ms(t)


@pytest.mark.parametrize(
    "t", [None, True, False, "abc", "", "1e12", float("inf"), float("nan"), [D0], {"T": D0}]
)
def test_nie_liczba_odrzucona(t):
    with pytest.raises(ValueError, match="nie jest liczbą ms"):
        lt.event_time_ms(t)


def test_tekst_z_cyframi_i_ulamek_jak_int_tak_jak_indeks():
    """Reguła indeksu przeniesiona bez zmian: `int(...)` przyjmuje tekst z cyframi i ucina ułamek."""
    assert lt.event_time_ms(str(D0)) == D0
    assert lt.event_time_ms(D0 + 0.5) == D0
    assert _index_accepts(str(D0)) and _index_accepts(D0 + 0.5)


def test_komunikat_uciety_do_kilkudziesieciu_znakow():
    for t in ("x" * 500, 10**300, 10**5000):  # 10**5000: więcej cyfr niż limit int → tekst
        with pytest.raises(ValueError) as exc:
            lt.event_time_ms(t)
        assert len(str(exc.value)) <= lt.SHORT_CHARS + 40
    with pytest.raises(ValueError, match="<int> poza zakresem"):
        lt.event_time_ms(10**5000)
    assert lt.short_repr(10**5000) == "<int>"


def test_granice_w_kodzie_tylko_w_jednym_miejscu():
    """Jedno źródło granic: żaden moduł likwidacji (kolektory, indeks, kopia — także przyszłe
    `collect_liquidations*.py` / `liquidation_*.py`) nie ma własnej kopii liczb (zadanie 021).
    Inne moduły `data/` (np. `fetch_tradfi_perps`) mają własne, niezależne granice."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    modules = sorted(
        {*data_dir.glob("collect_liquidations*.py"), *data_dir.glob("liquidation_*.py")}
    )
    known = {
        "collect_liquidations.py",
        "collect_liquidations_bybit.py",
        "liquidation_backup.py",
        "liquidation_index.py",
        "liquidation_time.py",
    }
    assert known <= {p.name for p in modules}  # wzorce plików trafiają (test nie jest pusty)
    owners = [
        p.name
        for p in modules
        if "1_546_300_800_000" in p.read_text(encoding="utf-8")
        or "4_102_444_800_000" in p.read_text(encoding="utf-8")
    ]
    assert owners == ["liquidation_time.py"]
    assert cl.MIN_EVENT_MS == li.MIN_EVENT_MS == lt.MIN_EVENT_MS
    assert cl.MAX_EVENT_MS == li.MAX_EVENT_MS == lt.MAX_EVENT_MS


# ------------------------------------------------------------------ ta sama reguła wszędzie
_T_VALUES = st.one_of(
    st.integers(min_value=lt.MIN_EVENT_MS - 10, max_value=lt.MIN_EVENT_MS + 10),
    st.integers(min_value=lt.MAX_EVENT_MS - 10, max_value=lt.MAX_EVENT_MS + 10),
    st.integers(min_value=-(10**20), max_value=10**20),
    st.floats(allow_nan=True, allow_infinity=True),
    st.integers(min_value=-(10**15), max_value=10**15).map(str),
    st.text(max_size=12),
    st.none(),
    st.booleans(),
)


@given(t=_T_VALUES)
@settings(max_examples=400, deadline=None)
def test_ta_sama_regula_indeks_kolektor_binance_i_bybit(t):
    """Indeks (a przez niego kopia) odrzuca `T` ⇔ reguła odrzuca ⇔ kolektor Binance liczy rekord
    jako `T` poza zakresem. Bybit (T = klucz pliku) przyjmuje tylko liczby całkowite JSON — dla nich
    ocena jest ta sama, inne typy odrzuca zawsze."""
    ok = _rule_accepts(t)
    assert _index_accepts(t) == ok
    rec = {**json.loads(_bn_line(D0)), "T": t}  # rekord jak w pliku LK0, z badanym `T`
    assert (cl.t_problem(rec) is None) == ok
    if isinstance(t, int) and not isinstance(t, bool):
        assert clb._is_ms(t) == ok
    else:
        assert clb._is_ms(t) is False
