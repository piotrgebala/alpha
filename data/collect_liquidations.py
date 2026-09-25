"""
collect_liquidations.py — kolektor likwidacji Binance USDT-M (strumień `!forceOrder@arr`) do plików
dziennych JSONL; działa 24/7 na serwerze (cron co 5 min przez `tools/likwidacje.sh`, jedna instancja).

Po co (STATUS ETAP 5, propozycja 4; decyzja użytkownika 2026-09-25): rodzina E1 (kaskady likwidacji,
skill `quant-strategy-catalog`) jest wykluczona WYŁĄCZNIE danymi — archiwum Binance nie ma likwidacji
(P3), REST `allForceOrders` zniknął w 2021, a płatni dostawcy nie dokumentują głębokości historii.
Jedyne darmowe źródło to strumień na żywo — zbieranie od dziś jest bramą danych na 1–2 lata.

Ograniczenie źródła (dokumentacja Binance): dla każdego symbolu w oknie 1000 ms strumień pokazuje
TYLKO OSTATNIE zlecenie likwidacyjne — to PRÓBKA zdarzeń, nie pełna lista; wolumen z tego strumienia
jest zaniżony w kaskadach. Zapisujemy surowe pola bez przeliczeń (liczby jako teksty z JSON).

Adres (ustalony doświadczalnie 2026-09-25, `runs/2026-09-25_lk0-kolektor-likwidacji/`): dokumentowany
`wss://fstream.binance.com/ws/!forceOrder@arr` odpowiada poprawnym handshake'iem, ale NIE wysyła żadnych
ramek; Binance rozdzielił strumienie futures na kategorie (`/public/ws/…` dla trade/depth, `/market/ws/…`
dla reszty — tak łączy się ccxt 4.5.48) i tylko `/market/ws/!forceOrder@arr` nadaje (~25 zdarzeń/min).
Cisza 15 min = ponowne połączenie z wpisem w logu — gdyby adres znów się zmienił, widać to w `--status`.

Zasady:
- czyste funkcje `parse_event`, `day_path`, `backoff_s`, klasa `DayWriter` — testy bez sieci
  (`tests/test_collect_liquidations.py`); pętla `run` z podmienialnym połączeniem i uśpieniem;
- cienka warstwa sieciowa `_connect` (aiohttp; tylko `wss://`, adres STAŁY w kodzie);
- zapis append-only: jedna linia JSON na zdarzenie, plik per dzień UTC czasu zdarzenia `E`,
  `flush` po każdej linii; `status.json` (liczniki, ostatnie zdarzenie) do nadzoru z zewnątrz;
- wiadomość o nieznanym schemacie jest POMIJANA i liczona (nie zrywa połączenia); każdy błąd
  transportu = ponowne połączenie po wykładniczym odczekaniu 1 s → 60 s. Proces nie kończy się sam.

    PYTHONUTF8=1 py -m data.collect_liquidations --dir ~/likwidacje       # kolektor (w tle, cron)
    PYTHONUTF8=1 py -m data.collect_liquidations --dir ~/likwidacje --status
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

STREAM_URL = "wss://fstream.binance.com/market/ws/!forceOrder@arr"  # NIE `/ws/…` (docstring)
DEFAULT_DIR = Path("data/raw/liquidations")
RECEIVE_TIMEOUT_S = (
    900.0  # 15 min bez wiadomości = zerwane połączenie (normalnie zdarzenia co sekundy)
)
BACKOFF_MAX_S = 60.0
STATUS_EVERY_S = 30.0
MAX_MSG_BYTES = 4 * 1024 * 1024
ORDER_FIELDS = ("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z", "T")
MIN_EVENT_MS, MAX_EVENT_MS = 1_546_300_800_000, 4_102_444_800_000  # 2019-01-01 … 2100-01-01 UTC
NUMERIC_FIELDS = ("q", "p", "ap", "l", "z")


# ------------------------------------------------------------------ czyste funkcje
def parse_event(msg: dict) -> dict:
    """Wiadomość `forceOrder` → płaski rekord: `E` (ms), `st`/`ps` jeśli są, pola zlecenia jak w JSON."""
    if not isinstance(msg, dict) or msg.get("e") != "forceOrder" or "E" not in msg:
        raise ValueError(f"likwidacje: nieoczekiwana wiadomość {str(msg)[:200]}")
    order = msg.get("o")
    if not isinstance(order, dict):
        raise ValueError(f"likwidacje: brak zlecenia `o` w {str(msg)[:200]}")
    missing = [k for k in ORDER_FIELDS if k not in order]
    if missing:
        raise ValueError(f"likwidacje: brak pól {missing} w {str(order)[:200]}")
    rec: dict = {"E": int(msg["E"])}
    for k in ("st", "ps"):  # po migracji CM: typ symbolu (1 = UM, 2 = CM) i para — w praktyce
        if (
            k in order
        ):  # wewnątrz `o` (zmierzone 2026-09-25), w dokumentacji na wierzchu; bierzemy oba
            rec[k] = order[k]
        elif k in msg:
            rec[k] = msg[k]
    rec.update({k: order[k] for k in ORDER_FIELDS})
    return rec


def day_path(root: Path, event_ms: int) -> Path:
    """Plik dnia UTC, w którym zaszło zdarzenie (po `E`, nie po czasie zapisu)."""
    if not (
        MIN_EVENT_MS <= int(event_ms) <= MAX_EVENT_MS
    ):  # zamiast OSError/OverflowError z platformy
        raise ValueError(f"likwidacje: czas zdarzenia poza zakresem: {event_ms}")
    day = dt.datetime.fromtimestamp(event_ms / 1000.0, tz=dt.timezone.utc).date()
    return Path(root) / f"{day.isoformat()}.jsonl"


def backoff_s(attempt: int, cap: float = BACKOFF_MAX_S) -> float:
    """Odczekanie przed n-tą próbą połączenia: 1, 2, 4, … s, sufit `cap`."""
    return float(min(cap, 2.0 ** max(0, attempt)))


def _now_iso() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec="seconds")


class DayWriter:
    """Append-only JSONL, plik per dzień UTC zdarzenia; `flush` po każdej linii."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path: Path | None = None
        self._f = None
        self.count = 0
        self.last_event_ms: int | None = None

    def write(self, rec: dict) -> None:
        path = day_path(self.root, rec["E"])
        if path != self._path:
            self.close()
            self._f = open(path, "a", encoding="utf-8")  # noqa: SIM115 — plik żyje przez cały dzień
            self._path = path
        self._f.write(json.dumps(rec, separators=(",", ":")) + "\n")  # ASCII: linia = rekord
        self._f.flush()
        self.count += 1
        self.last_event_ms = int(rec["E"])

    def close(self) -> None:
        if self._f is not None:
            self._f.close()
            self._f = None
            self._path = None


def write_status(root: Path, **fields) -> Path:
    """`status.json` zapisany atomowo (plik tymczasowy + rename) — do nadzoru z zewnątrz."""
    path = Path(root) / "status.json"
    tmp = path.with_name("status.json.tmp")
    tmp.write_text(
        json.dumps({"written_utc": _now_iso(), **fields}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    os.replace(tmp, path)
    return path


def _file_log(root: Path):
    def log(msg: str) -> None:
        with open(Path(root) / "kolektor.log", "a", encoding="utf-8") as f:
            f.write(f"{_now_iso()} {msg}\n")

    return log


# ------------------------------------------------------------------ sieć (cienka warstwa)
@contextlib.asynccontextmanager
async def _connect(url: str = STREAM_URL):
    """Połączenie wss (aiohttp; `autoping` odpowiada na pingi serwera) → asynchroniczny iterator dict."""
    import aiohttp

    if not url.startswith("wss://"):
        raise ValueError(f"likwidacje: dozwolone tylko wss, dostałem {url[:60]!r}")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            url, receive_timeout=RECEIVE_TIMEOUT_S, max_msg_size=MAX_MSG_BYTES
        ) as ws:

            async def messages():
                async for m in ws:
                    if m.type == aiohttp.WSMsgType.TEXT:
                        yield json.loads(m.data)
                    elif m.type in (
                        aiohttp.WSMsgType.CLOSE,
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR,
                    ):
                        raise ConnectionError(f"likwidacje: strumień zamknięty ({m.type.name})")

            yield messages()


# ------------------------------------------------------------------ pętla główna
async def run(
    root: Path = DEFAULT_DIR,
    connect=None,
    sleep=None,
    max_reconnects: int | None = None,
    log=None,
    clock=None,
) -> dict:
    """
    Pętla kolektora: połącz → zapisuj zdarzenia → po błędzie/końcu strumienia odczekaj i połącz
    ponownie. `max_reconnects` (testy) kończy pętlę po n rozłączeniach; produkcyjnie `None` = zawsze.
    """
    connect = _connect if connect is None else connect
    sleep = asyncio.sleep if sleep is None else sleep
    clock = time.monotonic if clock is None else clock
    log = _file_log(root) if log is None else log
    writer = DayWriter(root)
    state = {
        "started_utc": _now_iso(),
        "pid": os.getpid(),
        "events": 0,
        "skipped": 0,
        "reconnects": 0,
        "last_event_ms": None,
        "last_error": None,
    }

    def status() -> None:
        state.update(events=writer.count, last_event_ms=writer.last_event_ms)
        write_status(root, **state)

    attempt, last_status = 0, -STATUS_EVERY_S
    while True:
        reason = "koniec strumienia"
        try:
            async with connect() as messages:
                log(f"połączono {STREAM_URL}")
                attempt = 0
                async for msg in messages:
                    try:
                        writer.write(parse_event(msg))
                    except (ValueError, TypeError, OverflowError, OSError) as exc:  # zła ≠ zerwanie
                        state["skipped"] += 1
                        if state["skipped"] <= 5 or state["skipped"] % 1000 == 0:
                            log(f"pominięto ({state['skipped']}): {exc}")
                        continue
                    if clock() - last_status >= STATUS_EVERY_S:
                        status()
                        last_status = clock()
        except asyncio.CancelledError:
            writer.close()
            status()
            raise
        except Exception as exc:  # noqa: BLE001 — każdy błąd transportu = ponowne połączenie
            reason = f"{type(exc).__name__}: {str(exc)[:160]}"
        state["reconnects"] += 1
        state["last_error"] = reason
        delay = backoff_s(attempt)
        attempt += 1
        log(f"rozłączono: {reason}; zdarzeń {writer.count}; ponowne połączenie za {delay:.0f} s")
        status()
        if max_reconnects is not None and state["reconnects"] >= max_reconnects:
            writer.close()
            return state
        await sleep(delay)


# ------------------------------------------------------------------ odczyt (analiza, poza kolektorem)
def load_day(path: Path):
    """JSONL jednego dnia → DataFrame: `E`/`T` jako czas UTC, ilości i ceny jako float."""
    import pandas as pd

    rows = [
        json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for c in ("E", "T"):
        df[c] = pd.to_datetime(df[c].astype("int64"), unit="ms", utc=True)
    for c in NUMERIC_FIELDS:
        df[c] = pd.to_numeric(df[c], errors="raise").astype(float)
    return df


def status_text(root: Path) -> str:
    """Stan kolektora dla człowieka: status.json + liczba zdarzeń w dzisiejszym pliku."""
    root = Path(root)
    p = root / "status.json"
    if not p.exists():
        return f"brak {p} — kolektor jeszcze nic nie zapisał"
    st = json.loads(p.read_text(encoding="utf-8"))
    last = st.get("last_event_ms")
    last_txt = (
        dt.datetime.fromtimestamp(last / 1000.0, tz=dt.timezone.utc).isoformat(timespec="seconds")
        if last
        else "-"
    )
    today = day_path(root, int(time.time() * 1000))
    n_today = sum(1 for _ in open(today, encoding="utf-8")) if today.exists() else 0
    return (
        f"kolektor pid {st.get('pid')} od {st.get('started_utc')}; status z {st.get('written_utc')}; "
        f"zdarzeń {st.get('events')} (pominiętych {st.get('skipped')}), ostatnie {last_txt}; "
        f"rozłączeń {st.get('reconnects')}, ostatni błąd: {st.get('last_error')}; dziś w pliku: {n_today}"
    )


def main(argv: list[str]) -> int:
    root = DEFAULT_DIR
    it = iter(argv)
    show = False
    for a in it:
        if a == "--dir":
            root = Path(next(it))
        elif a == "--status":
            show = True
        else:
            print(f"nieznany argument {a!r}", file=sys.stderr)
            return 2
    if show:
        print(status_text(root))
        return 0
    try:
        asyncio.run(run(root))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
