"""
collect_liquidations_bybit.py — kolektor PEŁNYCH likwidacji Bybit (perpetuale liniowe USDT, temat
`allLiquidation.{symbol}`) do plików dziennych JSONL; działa 24/7 na serwerze obok kolektora Binance
(cron co 5 min przez `tools/likwidacje.sh`, jedna instancja — osobna blokada w katalogu danych).

Po co (docs/rag/11, przegląd kandydatów 2026-09-27, pozycja „Kolektor pełnych likwidacji Bybit”;
decyzja użytkownika „wykonaj wszystkie”): kolektor Binance (LK0) widzi tylko PRÓBKĘ — najwyżej jedno
zlecenie likwidacyjne na sekundę na symbol — więc najsłabiej widzi właśnie kaskady, o które chodzi
w rodzinie E1. Bybit publikuje WSZYSTKIE likwidacje (push co 500 ms). Historia jest płatna, darmowe
dane są tylko od dnia uruchomienia — dlatego zbieramy od dziś. Jeden licznik E1 dla LK0 i Bybit;
0 odczytów, dopóki rachunek mocy z realnej częstości zdarzeń nie powie „mierzalna”.

Fakty z dokumentacji Bybit v5 (sprawdzone 2026-09-27, potwierdzone kontrolą pozytywną
`runs/2026-09-27_lb0-kolektor-bybit/`):
- adres `wss://stream.bybit.com/v5/public/linear`; subskrypcja `{"op":"subscribe","args":[...]}`
  — najwyżej 10 tematów na żądanie, łączna długość tematów na połączenie ≤ 21 000 znaków; ping
  `{"op":"ping"}` co 20 s; limit 500 połączeń / 5 min na IP;
- wiadomość: `{"topic":"allLiquidation.X","type":"snapshot","ts":ms,"data":[{"T","s","S","v","p"}]}`;
- **`S` to strona POZYCJI**: "Buy" = zlikwidowano pozycję LONG, "Sell" = SHORT. W Binance (LK0) jest
  odwrotnie — tam `S` to strona zlecenia likwidacyjnego (SELL = zlikwidowany long). Dlatego rekord
  ma jawne pole `pos` ("long"/"short"), żeby przy łączeniu źródeł nie pomylić kierunku;
- `p` = cena upadłości (nie cena wykonania), `v` = wielkość w monetach.

Zasady:
- czyste funkcje `parse_message`, `classify`, `subscribe_batches`, `parse_instruments` — testy bez
  sieci (`tests/test_collect_liquidations_bybit.py`); `DayWriter`, `day_path`, `backoff_s`,
  `write_status` z `data.collect_liquidations` (ten sam format plików i statusu co LK0, bez
  licznika `t_out_of_range` — patrz niżej);
- pętla `run` z podmienialnym połączeniem, pobieraniem listy symboli, zegarem i uśpieniem;
- cienka warstwa sieciowa (`_connect`, `_get_json`; aiohttp; adresy STAŁE w kodzie, tylko
  `wss://` i `https://`); żadnych kluczy — dane publiczne;
- zapis append-only: jedna linia JSON na likwidację (`T` ms, `s`, `S`, `v`, `p` — surowo, liczby jako
  teksty; `pos` — kierunek zlikwidowanej pozycji; `ts` — czas wysłania wiadomości przez Bybit;
  `rcv` — czas odbioru na serwerze, ms), plik per dzień UTC czasu `T`;
- lista symboli z REST co 24 h (nowe listingi) — wtedy wszystkie połączenia są zamykane i otwierane
  od nowa z nowym planem subskrypcji; tematy dzielone PO RÓWNO między połączenia (żadne nie dostaje
  garstki rzadkich monet); cisza > 15 min bez żadnej likwidacji na połączeniu = ponowne połączenie
  (pong NIE jest znakiem życia — ten strażnik łapie „połączenie żyje, dane nie płyną”); każdy błąd
  transportu = ponowne połączenie po odczekaniu 1 s → 60 s (odczekanie zeruje się dopiero po
  cyklu dłuższym niż 60 s — chroni limit 500 połączeń / 5 min);
- wiadomość o nieznanym schemacie albo zła likwidacja (symbol, liczba, czas) jest POMIJANA i liczona
  (nie zrywa połączenia); czas sprawdza ta sama funkcja co LK0, indeks i kopia
  (`data/liquidation_time.event_time_ms`, zadanie 021). Inaczej niż w LK0 likwidacja z `T` spoza
  reguły NIE jest zapisywana: tu `T` wyznacza plik dnia, więc bez zmiany formatu nie ma dla niej
  miejsca — zostaje pominięta i policzona w `skipped` (wpis w logu z treścią wiadomości);
- nieudana subskrypcja (Bybit odrzuca CAŁE żądanie, gdy jeden temat jest zły, i podaje tylko
  pierwszy zły temat — sprawdzone na żywo 2026-09-27) jest liczona, logowana i NAPRAWIANA od razu:
  zły temat (`handler not found`) wypada z planu do najbliższego udanego odświeżenia listy,
  pozostałe tematy żądania są wysyłane ponownie (`after_sub_fail`); odpowiedź bez tematu → tematy
  żądania po jednym;
- odpowiedź REST z listą instrumentów ma limit rozmiaru (`MAX_REST_BYTES`), jak wiadomości wss.

    PYTHONUTF8=1 py -m data.collect_liquidations_bybit                       # kolektor (w tle, cron)
    PYTHONUTF8=1 py -m data.collect_liquidations_bybit --status
    PYTHONUTF8=1 py -m data.collect_liquidations_bybit --probe 180          # kontrola pozytywna
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import math
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

from data import collect_liquidations as cl
from data import liquidation_time as lt

STREAM_URL = "wss://stream.bybit.com/v5/public/linear"
INSTRUMENTS_URL = "https://api.bybit.com/v5/market/instruments-info"
DEFAULT_DIR = Path.home() / "likwidacje_bybit"
TOPIC_PREFIX = "allLiquidation."
TOPICS_PER_REQUEST = 10  # limit Bybit na jedno żądanie subskrypcji
ARGS_CHARS_LIMIT = 21_000  # limit Bybit: łączna długość tematów na połączenie
ARGS_CHARS_BUDGET = 18_000  # budżet z zapasem ~14 % (tematy liczone z cudzysłowami i przecinkiem)
PING_EVERY_S = 20.0
SILENCE_S = 900.0  # 15 min bez likwidacji na połączeniu = ponowne połączenie
REFRESH_SYMBOLS_S = 86_400.0  # lista symboli co 24 h (nowe listingi)
REFRESH_RETRY_S = 3_600.0  # nieudane odświeżenie listy → stara lista, następna próba za 1 h
STABLE_CYCLE_S = 60.0  # cykl krótszy = odczekanie rośnie dalej (limit połączeń na IP)
STATUS_EVERY_S = 30.0
MAX_PAGES = 20
MAX_MSG_BYTES = 4 * 1024 * 1024
MAX_REST_BYTES = 8 * 1024 * 1024  # lista instrumentów 2026-09-27: ~0,8 MB (777 monet) — zapas ~10×
FAILED_TOPIC_RE = re.compile(r"topic:([^,\s]+)")  # `error:handler not found,topic:allLiquidation.X`
SYMBOL_RE = re.compile(r"[A-Z0-9]{1,40}USDT")
NUM_RE = re.compile(r"\d+(\.\d+)?([eE][-+]?\d+)?")
SIDE_TO_POSITION = {"Buy": "long", "Sell": "short"}  # Bybit: S = strona zlikwidowanej POZYCJI
RECORD_FIELDS = ("T", "s", "S", "v", "p", "pos", "ts", "rcv")


# ------------------------------------------------------------------ czyste funkcje
def _is_ms(x) -> bool:
    """Czas w ms jako liczba całkowita JSON (nie bool, nie tekst, nie ułamek — `T` jest tu kluczem
    pliku dnia) w zakresie wspólnej reguły `liquidation_time.event_time_ms` (LK0, indeks, kopia)."""
    if not isinstance(x, int) or isinstance(x, bool):
        return False
    try:
        lt.event_time_ms(x)
    except ValueError:
        return False
    return True


def _is_positive_number_text(x) -> bool:
    if not isinstance(x, str) or not NUM_RE.fullmatch(x):
        return False
    val = float(x)
    return math.isfinite(val) and val > 0


def parse_item(item, symbol: str, ts: int, rcv_ms: int | None) -> dict:
    """Jedna likwidacja z `data` → rekord; `ValueError`, gdy pole ma zły typ lub wartość."""
    if not isinstance(item, dict):
        raise ValueError(f"likwidacje bybit: element nie jest obiektem: {str(item)[:120]}")
    missing = [k for k in ("T", "s", "S", "v", "p") if k not in item]
    if missing:
        raise ValueError(f"likwidacje bybit: brak pól {missing} w {str(item)[:120]}")
    if item["s"] != symbol:
        raise ValueError(f"likwidacje bybit: symbol {item['s']!r} ≠ temat {symbol!r}")
    if item["S"] not in SIDE_TO_POSITION:
        raise ValueError(f"likwidacje bybit: nieznana strona {str(item['S'])[:20]!r}")
    for k in ("v", "p"):
        if not _is_positive_number_text(item[k]):
            raise ValueError(f"likwidacje bybit: pole {k} nie jest dodatnią liczbą: {item[k]!r}")
    if not _is_ms(item["T"]):
        raise ValueError(f"likwidacje bybit: czas zdarzenia poza zakresem: {item['T']!r}")
    rec = {k: item[k] for k in ("T", "s", "S", "v", "p")}
    rec["pos"] = SIDE_TO_POSITION[item["S"]]
    rec["ts"] = ts
    if rcv_ms is not None:
        rec["rcv"] = int(rcv_ms)
    return rec


def parse_message(msg, rcv_ms: int | None = None) -> tuple[list[dict], int] | None:
    """
    Wiadomość `allLiquidation.{symbol}` → (rekordy, liczba odrzuconych elementów).
    `None`, gdy wiadomość nie ma znanego schematu (inny temat, zły symbol, brak `ts`/`data`).
    """
    if not isinstance(msg, dict):
        return None
    topic = msg.get("topic")
    if not isinstance(topic, str) or not topic.startswith(TOPIC_PREFIX):
        return None
    symbol = topic[len(TOPIC_PREFIX) :]
    data, ts = msg.get("data"), msg.get("ts")
    if not SYMBOL_RE.fullmatch(symbol) or not isinstance(data, list) or not _is_ms(ts):
        return None
    records, rejected = [], 0
    for item in data:
        try:
            records.append(parse_item(item, symbol, ts, rcv_ms))
        except (ValueError, TypeError, OverflowError):
            rejected += 1
    return records, rejected


def classify(msg) -> str:
    """Rodzaj wiadomości: data / pong / sub_ok / sub_fail / unknown."""
    if not isinstance(msg, dict):
        return "unknown"
    topic = msg.get("topic")
    if isinstance(topic, str) and topic.startswith(TOPIC_PREFIX):
        return "data"
    op = msg.get("op")
    if op == "ping" or (op in (None, "pong") and msg.get("ret_msg") == "pong"):
        return "pong"
    if op == "subscribe":
        return "sub_ok" if msg.get("success") is True else "sub_fail"
    return "unknown"


def topic_chars(topic: str) -> int:
    """Ile znaków temat zajmuje w liście `args` (z cudzysłowami i przecinkiem — ostrożnie)."""
    return len(json.dumps(topic)) + 1


def subscribe_batches(
    symbols,
    per_request: int = TOPICS_PER_REQUEST,
    max_chars: int = ARGS_CHARS_BUDGET,
) -> list[list[list[str]]]:
    """
    Symbole → plan subskrypcji: połączenia → żądania (≤ `per_request` tematów) → tematy.
    Najmniejsza liczba połączeń `k`, przy której tematy podzielone PO RÓWNO (kolejne bloki po
    ⌈N/k⌉ lub ⌊N/k⌋ tematów) mieszczą się w `max_chars` na połączenie — żadne połączenie nie
    dostaje samego ogona alfabetu (kilku rzadkich monet, które 15 min ciszy rozłączałoby w kółko).
    Symbole bez powtórzeń, posortowane (plan deterministyczny); pusta lista → brak połączeń.
    """
    if per_request < 1:
        raise ValueError("likwidacje bybit: per_request < 1")
    topics = [TOPIC_PREFIX + s for s in sorted(set(symbols))]
    for t in topics:
        if topic_chars(t) > max_chars:
            raise ValueError(f"likwidacje bybit: temat dłuższy niż budżet połączenia: {t[:60]}")
    n = len(topics)
    conns: list[list[str]] = []
    k = max(1, math.ceil(sum(topic_chars(t) for t in topics) / max_chars)) if n else 0
    while k:  # k = n zawsze się mieści (każdy temat osobno), więc pętla się kończy
        size, extra = divmod(n, k)
        bounds = [i * size + min(i, extra) for i in range(k + 1)]
        conns = [topics[bounds[i] : bounds[i + 1]] for i in range(k)]
        if all(sum(topic_chars(t) for t in c) <= max_chars for c in conns):
            break
        k += 1
    return [[c[i : i + per_request] for i in range(0, len(c), per_request)] for c in conns]


def after_sub_fail(args: list[str], ret_msg) -> tuple[list[list[str]], list[str]]:
    """
    Nieudane żądanie subskrypcji → (żądania do ponownego wysłania, tematy odrzucone).
    Bybit odrzuca całe żądanie i w `ret_msg` podaje PIERWSZY zły temat
    (`error:handler not found,topic:allLiquidation.X`). Ten temat wypada, reszta idzie ponownie
    jednym żądaniem (kolejny zły temat wyjdzie w następnej odpowiedzi). `already subscribed` —
    temat już działa, więc nie jest odrzucany, tylko nie wysyła się go drugi raz. Brak tematu
    w odpowiedzi → tematy po jednym (każdy dostanie własną odpowiedź); pojedynczy temat bez
    wskazania → odrzucony. Każdy krok zmniejsza żądanie, więc ponawianie się kończy.
    """
    args = list(dict.fromkeys(args))
    m = FAILED_TOPIC_RE.search(ret_msg) if isinstance(ret_msg, str) else None
    bad = m.group(1) if m else None
    if bad in args:
        rest = [t for t in args if t != bad]
        rejected = [] if "already subscribed" in ret_msg else [bad]
        return ([rest] if rest else []), rejected
    if len(args) > 1:
        return [[t] for t in args], []
    return [], args


def parse_instruments(payload) -> tuple[list[str], str]:
    """
    Strona odpowiedzi `instruments-info` → (symbole do subskrypcji, kursor następnej strony).
    Filtr: status Trading, kontrakt LinearPerpetual, rozliczenie USDT, symbol `[A-Z0-9]{1,40}USDT`.
    """
    if not isinstance(payload, dict) or payload.get("retCode") != 0:
        raise ValueError(f"likwidacje bybit: odpowiedź instrumentów z błędem: {str(payload)[:200]}")
    result = payload.get("result")
    rows = result.get("list") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("likwidacje bybit: brak `result.list` w odpowiedzi instrumentów")
    symbols = [
        r["symbol"]
        for r in rows
        if isinstance(r, dict)
        and r.get("status") == "Trading"
        and r.get("contractType") == "LinearPerpetual"
        and r.get("settleCoin") == "USDT"
        and isinstance(r.get("symbol"), str)
        and SYMBOL_RE.fullmatch(r["symbol"])
    ]
    cursor = result.get("nextPageCursor") or ""
    return symbols, cursor if isinstance(cursor, str) else ""


async def fetch_symbols(get_json, max_pages: int = MAX_PAGES) -> list[str]:
    """Wszystkie strony `instruments-info` (kursor) → posortowana lista symboli bez powtórzeń."""
    symbols: list[str] = []
    cursor = ""
    for _ in range(max_pages):
        params = {"category": "linear", "limit": "1000"}
        if cursor:
            params["cursor"] = cursor
        page_symbols, cursor = parse_instruments(await get_json(params))
        symbols.extend(page_symbols)
        if not cursor:
            break
    else:
        raise ValueError(f"likwidacje bybit: więcej niż {max_pages} stron instrumentów")
    if not symbols:
        raise ValueError("likwidacje bybit: pusta lista symboli")
    return sorted(set(symbols))


# ------------------------------------------------------------------ sieć (cienka warstwa)
class _WsConn:
    """Połączenie wss: osobne zadanie czyta ramki do kolejki, więc `recv(timeout)` nie psuje gniazda."""

    def __init__(self, ws) -> None:
        self._ws = ws
        self._q: asyncio.Queue = asyncio.Queue()
        self._task = asyncio.create_task(self._pump())

    async def _pump(self) -> None:
        import aiohttp

        try:
            async for m in self._ws:
                if m.type == aiohttp.WSMsgType.TEXT:
                    try:
                        self._q.put_nowait(json.loads(m.data))
                    except ValueError:
                        self._q.put_nowait({"_niepoprawny_json": str(m.data)[:200]})
                elif m.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                ):
                    break
        except Exception as exc:  # noqa: BLE001 — błąd transportu przekazany do `recv`
            self._q.put_nowait(exc)
        finally:
            self._q.put_nowait(None)

    async def send(self, obj: dict) -> None:
        await self._ws.send_str(json.dumps(obj))

    async def recv(self, timeout: float):
        item = await asyncio.wait_for(self._q.get(), timeout)
        if isinstance(item, Exception):
            raise item
        return item

    async def close(self) -> None:
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await self._task


@contextlib.asynccontextmanager
async def _connect(url: str = STREAM_URL):
    """Połączenie wss (aiohttp; `autoping` odpowiada na pingi serwera) → obiekt `send`/`recv`."""
    import aiohttp

    if not url.startswith("wss://"):
        raise ValueError(f"likwidacje bybit: dozwolone tylko wss, dostałem {url[:60]!r}")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url, max_msg_size=MAX_MSG_BYTES, autoping=True) as ws:
            conn = _WsConn(ws)
            try:
                yield conn
            finally:
                await conn.close()


async def read_limited(chunks, limit: int = MAX_REST_BYTES) -> bytes:
    """Kawałki treści odpowiedzi → bajty; `ValueError`, gdy treść przekracza `limit` bajtów."""
    buf = bytearray()
    async for chunk in chunks:
        buf += chunk
        if len(buf) > limit:
            raise ValueError(f"likwidacje bybit: odpowiedź REST większa niż {limit} B")
    return bytes(buf)


async def _get_json(params: dict, url: str = INSTRUMENTS_URL, limit: int = MAX_REST_BYTES):
    """GET listy instrumentów (publiczny REST Bybit, tylko https, limit czasu 30 s i rozmiaru)."""
    import aiohttp

    if not url.startswith("https://"):
        raise ValueError(f"likwidacje bybit: dozwolone tylko https, dostałem {url[:60]!r}")
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            if resp.content_length is not None and resp.content_length > limit:
                raise ValueError(f"likwidacje bybit: odpowiedź REST większa niż {limit} B")
            return json.loads(await read_limited(resp.content.iter_chunked(65_536), limit))


# ------------------------------------------------------------------ sesja i cykl połączeń
def new_stats() -> dict:
    return {
        "events": 0,
        "messages": 0,
        "skipped": 0,
        "pongs": 0,
        "sub_ok": 0,
        "sub_fail": 0,
        "resubscribed": 0,
    }


async def _session(
    conn_id: int,
    requests: list[list[str]],
    *,
    connect,
    on_record,
    stats: dict,
    clock,
    wall,
    log,
    deadline: float,
    silence_s: float,
    ping_s: float,
    tick,
    connected: list,
    rejected_topics: set,
) -> str:
    """
    Jedno połączenie: subskrypcja, ping co `ping_s`, odbiór do `deadline` albo do błędu.
    Nieudane żądanie subskrypcji jest naprawiane od razu (`after_sub_fail`): zły temat trafia do
    `rejected_topics` (wspólne dla cykli — `run` pomija je w planie do udanego odświeżenia listy),
    reszta tematów żądania jest wysyłana ponownie z nowym `req_id`.
    """
    async with connect() as conn:
        connected.append(conn_id)
        n_topics = sum(len(r) for r in requests)
        log(f"połączono #{conn_id} {STREAM_URL}: {n_topics} tematów w {len(requests)} żądaniach")
        pending: dict[str, list[str]] = {}  # req_id → tematy żądania bez odpowiedzi
        for i, args in enumerate(requests):
            pending[f"{conn_id}-{i}"] = list(args)
            await conn.send({"op": "subscribe", "req_id": f"{conn_id}-{i}", "args": args})
        n_retry = 0
        last_ping = last_data = clock()
        while True:
            now = clock()
            if now >= deadline:
                return "koniec okna (odświeżenie listy symboli albo koniec próby)"
            if now - last_data > silence_s:
                raise TimeoutError(f"cisza > {silence_s:.0f} s na połączeniu #{conn_id}")
            if now - last_ping >= ping_s:
                await conn.send({"op": "ping"})
                last_ping = now
            timeout = max(0.05, min(ping_s - (now - last_ping), deadline - now))
            try:
                msg = await conn.recv(timeout)
            except asyncio.TimeoutError:
                continue
            if msg is None:
                raise ConnectionError(f"koniec strumienia na połączeniu #{conn_id}")
            kind = classify(msg)
            if kind == "data":
                parsed = parse_message(msg, rcv_ms=int(wall() * 1000))
                if parsed is None:
                    stats["skipped"] += 1
                    if stats["skipped"] <= 5 or stats["skipped"] % 1000 == 0:
                        log(f"pominięto wiadomość ({stats['skipped']}): {str(msg)[:200]}")
                else:
                    records, rejected = parsed
                    stats["messages"] += 1
                    last_data = clock()
                    for rec in records:
                        try:
                            on_record(rec)
                        except (ValueError, TypeError, OverflowError, OSError) as exc:
                            rejected += 1
                            log(f"nie zapisano rekordu: {exc}")
                        else:
                            stats["events"] += 1
                    if rejected:
                        stats["skipped"] += rejected
                        if stats["skipped"] <= 5 or stats["skipped"] % 1000 == 0:
                            log(f"pominięto {rejected} likwidacji: {str(msg)[:200]}")
            elif kind == "pong":
                stats["pongs"] += 1
            elif kind == "sub_ok":
                stats["sub_ok"] += 1
                pending.pop(str(msg.get("req_id")), None)
            elif kind == "sub_fail":
                stats["sub_fail"] += 1
                log(f"subskrypcja NIEUDANA na #{conn_id}: {str(msg)[:300]}")
                args = pending.pop(str(msg.get("req_id")), None)
                if args is None:
                    log(f"nieznane req_id {str(msg.get('req_id'))[:40]!r} — nie ma czego ponowić")
                    tick()
                    continue
                resend, bad = after_sub_fail(args, msg.get("ret_msg"))
                for t in bad:
                    rejected_topics.add(t)
                    log(f"temat odrzucony przez Bybit (do odświeżenia listy): {t[:80]}")
                for retry in resend:
                    n_retry += 1
                    req_id = f"{conn_id}-r{n_retry}"
                    pending[req_id] = retry
                    stats["resubscribed"] += len(retry)
                    await conn.send({"op": "subscribe", "req_id": req_id, "args": retry})
                log(f"ponowiono {sum(map(len, resend))} tematów w {len(resend)} żądaniach")
            else:
                stats["skipped"] += 1
                if stats["skipped"] <= 5 or stats["skipped"] % 1000 == 0:
                    log(f"pominięto wiadomość ({stats['skipped']}): {str(msg)[:200]}")
            tick()


async def _cycle(plan, **kw) -> tuple[str, bool]:
    """
    Wszystkie połączenia planu naraz; cykl kończy się, gdy skończy się PIERWSZE z nich (błąd albo
    koniec okna) — pozostałe są zamykane. Zwraca (powód, czy_błąd).
    """
    tasks = [asyncio.create_task(_session(i, reqs, **kw)) for i, reqs in enumerate(plan)]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    for t in done:
        if not t.cancelled() and t.exception() is not None:
            exc = t.exception()
            return f"{type(exc).__name__}: {str(exc)[:160]}", True
    return next(iter(done)).result(), False


# ------------------------------------------------------------------ pętla główna
async def run(
    root: Path = DEFAULT_DIR,
    connect=None,
    get_json=None,
    sleep=None,
    clock=None,
    wall=None,
    log=None,
    max_cycles: int | None = None,
    refresh_s: float = REFRESH_SYMBOLS_S,
    silence_s: float = SILENCE_S,
    ping_s: float = PING_EVERY_S,
    refresh_retry_s: float = REFRESH_RETRY_S,
) -> dict:
    """
    Pętla kolektora: lista symboli → plan subskrypcji → cykl połączeń → zapis → po błędzie
    odczekanie i ponowne połączenie; po 24 h świeża lista symboli i nowy plan (nieudane
    odświeżenie → stara lista, następna próba za `refresh_retry_s`). Tematy odrzucone przez
    Bybit przy subskrypcji wypadają z planu do najbliższego udanego odświeżenia listy.
    `max_cycles` (testy) kończy pętlę po n cyklach; produkcyjnie `None` = zawsze.
    """
    connect = _connect if connect is None else connect
    get_json = _get_json if get_json is None else get_json
    sleep = asyncio.sleep if sleep is None else sleep
    clock = time.monotonic if clock is None else clock
    wall = time.time if wall is None else wall
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    log = cl._file_log(root) if log is None else log
    writer = cl.DayWriter(root, time_key="T")
    stats = new_stats()
    state = {
        "started_utc": cl._now_iso(),
        "pid": os.getpid(),
        "source": STREAM_URL,
        "symbols": 0,
        "connections": 0,
        "reconnects": 0,
        "refreshes": 0,
        "last_event_ms": None,
        "last_error": None,
    }
    last_status = [-math.inf]
    rejected_topics: set[str] = set()

    def status() -> None:
        state.update(stats, events=writer.count, last_event_ms=writer.last_event_ms)
        state["rejected_topics"] = sorted(rejected_topics)[:20]
        state["rejected_count"] = len(rejected_topics)
        cl.write_status(root, **state)
        last_status[0] = clock()

    def tick() -> None:
        if clock() - last_status[0] >= STATUS_EVERY_S:
            status()

    symbols: list[str] | None = None
    fetched_at = -math.inf
    attempt = cycles = 0
    try:
        while True:
            if symbols is None or clock() - fetched_at >= refresh_s:
                try:
                    new = await fetch_symbols(get_json)
                except Exception as exc:  # noqa: BLE001 — sieć/format = spróbuj później
                    reason = f"lista symboli: {type(exc).__name__}: {str(exc)[:160]}"
                    if symbols is None:
                        state["reconnects"] += 1
                        state["last_error"] = reason
                        delay = cl.backoff_s(attempt)
                        attempt += 1
                        log(f"{reason}; ponowna próba za {delay:.0f} s")
                        status()
                        cycles += 1
                        if max_cycles is not None and cycles >= max_cycles:
                            return state
                        await sleep(delay)
                        continue
                    log(f"{reason}; zostaje stara lista ({len(symbols)} symboli)")
                    fetched_at = clock() - refresh_s + refresh_retry_s
                else:
                    added = sorted(set(new) - set(symbols or []))
                    removed = sorted(set(symbols or []) - set(new))
                    log(
                        f"lista symboli: {len(new)} (nowe {len(added)}: {' '.join(added[:10])}; "
                        f"usunięte {len(removed)}: {' '.join(removed[:10])})"
                    )
                    symbols, fetched_at = new, clock()
                    rejected_topics.clear()  # świeża lista — odrzucone tematy dostają nową szansę
            live = [s for s in symbols if TOPIC_PREFIX + s not in rejected_topics]
            if not live:  # wszystko odrzucone (nie powinno się zdarzyć) — wróć do pełnej listy
                rejected_topics.clear()
                live = symbols
            plan = subscribe_batches(live)
            state.update(symbols=len(live), connections=len(plan))
            connected: list = []
            started = clock()
            reason, is_error = await _cycle(
                plan,
                connect=connect,
                on_record=writer.write,
                stats=stats,
                clock=clock,
                wall=wall,
                log=log,
                deadline=fetched_at + refresh_s,
                silence_s=silence_s,
                ping_s=ping_s,
                tick=tick,
                connected=connected,
                rejected_topics=rejected_topics,
            )
            cycles += 1
            if len(connected) == len(plan) and clock() - started >= STABLE_CYCLE_S:
                attempt = 0
            if is_error:
                state["reconnects"] += 1
                state["last_error"] = reason
                delay = cl.backoff_s(attempt)
                attempt += 1
                log(
                    f"rozłączono: {reason}; zdarzeń {writer.count}; "
                    f"ponowne połączenie za {delay:.0f} s"
                )
            else:
                state["refreshes"] += 1
                delay = 0.0
                log(f"{reason}; zdarzeń {writer.count}; ponowne połączenie od razu")
            status()
            if max_cycles is not None and cycles >= max_cycles:
                return state
            if delay:
                await sleep(delay)
    finally:
        writer.close()
        with contextlib.suppress(OSError):
            status()


# ------------------------------------------------------------------ kontrola pozytywna
async def probe(
    seconds: float,
    connect=None,
    get_json=None,
    clock=None,
    wall=None,
    out=print,
) -> dict:
    """
    Kontrola pozytywna źródła: pobierz listę symboli, połącz i subskrybuj wszystko, licz likwidacje
    przez `seconds` s, wypisz liczniki i 3 przykładowe zdarzenia. NIC nie zapisuje na dysk.
    """
    connect = _connect if connect is None else connect
    get_json = _get_json if get_json is None else get_json
    clock = time.monotonic if clock is None else clock
    wall = time.time if wall is None else wall
    symbols = await fetch_symbols(get_json)
    plan = subscribe_batches(symbols)
    n_req = sum(len(c) for c in plan)
    chars = [sum(topic_chars(t) for r in c for t in r) for c in plan]
    out(f"źródło: {STREAM_URL}; lista symboli: {INSTRUMENTS_URL}")
    out(
        f"symboli: {len(symbols)}; połączeń: {len(plan)}; żądań subskrypcji: {n_req} "
        f"(znaki tematów na połączenie: {chars}; limit Bybit {ARGS_CHARS_LIMIT})"
    )
    records: list[dict] = []
    rejected: set[str] = set()
    stats = new_stats()
    start_ms = int(wall() * 1000)
    out(f"start próby: {cl._now_iso()} ({start_ms} ms), czas {seconds:.0f} s")
    reason, is_error = await _cycle(
        plan,
        connect=connect,
        on_record=records.append,
        stats=stats,
        clock=clock,
        wall=wall,
        log=out,
        deadline=clock() + seconds,
        silence_s=max(SILENCE_S, seconds + 1),
        ping_s=PING_EVERY_S,
        tick=lambda: None,
        connected=[],
        rejected_topics=rejected,
    )
    end_ms = int(wall() * 1000)
    out(f"koniec próby: {cl._now_iso()} ({end_ms} ms); powód: {reason}; błąd: {is_error}")
    summary = summarize(records, seconds)
    summary.update(
        stats,
        window_ms=[start_ms, end_ms],
        error=is_error,
        reason=reason,
        rejected_topics=sorted(rejected),
    )
    out(
        f"subskrypcje udane: {stats['sub_ok']} / {n_req}, nieudane: {stats['sub_fail']} "
        f"(ponowione tematy: {stats['resubscribed']}, odrzucone: {len(rejected)} "
        f"{' '.join(sorted(rejected)[:10])}); "
        f"pongi: {stats['pongs']}; wiadomości z likwidacjami: {stats['messages']}; "
        f"pominięte: {stats['skipped']}"
    )
    out(
        f"likwidacji: {summary['events']} ({summary['per_min']:.1f}/min na {seconds:.0f} s), "
        f"symboli: {summary['symbols']}; zlikwidowane longi: {summary['long']}, "
        f"shorty: {summary['short']}; nominał (v × cena upadłości) ≈ "
        f"{summary['notional_usd']:,.0f} USD"
    )
    out("najczęstsze symbole: " + ", ".join(f"{s} {n}" for s, n in summary["top"]))
    for i, rec in enumerate(records[:3], 1):
        out(f"przykład {i}: {json.dumps(rec, separators=(',', ':'))}")
    if not records:
        out(
            "UWAGA: 0 likwidacji — źródło nie potwierdzone (sprawdź adres/temat, jak w LK0), "
            "zanim kolektor zostanie uznany za działający"
        )
    return summary


def summarize(records: list[dict], seconds: float | None = None) -> dict:
    """Liczniki próby: zdarzenia, symbole, kierunki, nominał, top-5 symboli, tempo na minutę."""
    n = len(records)
    if records and seconds is None:
        span = (max(r["T"] for r in records) - min(r["T"] for r in records)) / 1000.0
    else:
        span = seconds or 0.0
    return {
        "events": n,
        "symbols": len({r["s"] for r in records}),
        "long": sum(1 for r in records if r["pos"] == "long"),
        "short": sum(1 for r in records if r["pos"] == "short"),
        "notional_usd": sum(float(r["v"]) * float(r["p"]) for r in records),
        "top": Counter(r["s"] for r in records).most_common(5),
        "per_min": (60.0 * n / span) if span > 0 else float(n),
    }


# ------------------------------------------------------------------ odczyt (analiza, poza kolektorem)
def load_day(path: Path):
    """JSONL jednego dnia → DataFrame: `T`/`ts`/`rcv` jako czas UTC, `v`/`p` jako float."""
    import pandas as pd

    rows = [
        json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for c in ("T", "ts", "rcv"):
        if c in df:
            df[c] = pd.to_datetime(df[c].astype("int64"), unit="ms", utc=True)
    for c in ("v", "p"):
        df[c] = pd.to_numeric(df[c], errors="raise").astype(float)
    return df


def status_text(root: Path) -> str:
    """Stan kolektora dla człowieka: tekst jak w LK0 + symbole, połączenia, subskrypcje."""
    base = cl.status_text(root)
    p = Path(root) / "status.json"
    if not p.exists():
        return base
    st = json.loads(p.read_text(encoding="utf-8"))
    return (
        f"{base}; symboli {st.get('symbols')} w {st.get('connections')} połączeniach; "
        f"subskrypcje udane {st.get('sub_ok')}, nieudane {st.get('sub_fail')}, "
        f"tematy odrzucone {st.get('rejected_count', 0)}; "
        f"odświeżeń listy {st.get('refreshes')}"
    )


def main(argv: list[str]) -> int:
    root = DEFAULT_DIR
    it = iter(argv)
    show = False
    probe_s: float | None = None
    try:
        for a in it:
            if a == "--dir":
                root = Path(next(it)).expanduser()
            elif a == "--status":
                show = True
            elif a == "--probe":
                probe_s = float(next(it))
                if not (0 < probe_s <= 3600):
                    raise ValueError("--probe: od 0 do 3600 s")
            else:
                print(f"nieznany argument {a!r}", file=sys.stderr)
                return 2
    except (StopIteration, ValueError) as exc:
        print(f"zły argument: {exc or 'brak wartości'}", file=sys.stderr)
        return 2
    if show:
        print(status_text(root))
        return 0
    if probe_s is not None:
        summary = asyncio.run(probe(probe_s, out=lambda s: print(s, flush=True)))
        return 0 if summary["events"] > 0 and not summary["error"] else 1
    try:
        asyncio.run(run(root))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
