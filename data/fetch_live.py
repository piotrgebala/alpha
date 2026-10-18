"""
fetch_live.py — świeże dane do dziennika na żywo (`backtest/live_journal.py`, `dziennik/README.md`).

Osobny katalog `data/raw/live/` — zamrożone cache rund (`data/raw/universe`, …) zostają nietknięte.
Źródła (te same, co w rundach TS1/CP1, publiczne, bez klucza):
- Binance USDT-M: lista aktywnych perpetuali (`exchangeInfo`), świece 1d z open/high/low/close/obrót,
  funding — każdy przebieg nadpisuje pliki (dane na żywo, nie archiwum);
- Coinbase Exchange: BTC-USD 1d (`data.fetch_external.fetch_coinbase_daily`);
- Binance spot: BTC/USDT 8h (świeca 16:00 = zamknięcie o 24:00 UTC, jak `run_coinbase_cp1.daily_premium`);
- alternative.me: Fear & Greed dzienny (`data.fetch_external.fetch_fng`, poprawka 8) — TYLKO etykieta do
  zapisu; awaria tego źródła nie zatrzymuje pobierania ani dziennika (`fetch_fng_safe`);
- Binance COIN-M: funding `BTCUSD_PERP` od startu nogi carry (`data.fetch_external.fetch_coinm_funding`,
  poprawka 12) — tylko noga carry; awaria nie zatrzymuje pobierania ani dziennika (`fetch_coinm_funding_safe`).
- poprawka 13 (moneta wstrzymana lub wycofana): statusy kontraktów USDT z tego samego `exchangeInfo`
  (`STATUS_FILE`, `save_statuses_safe`) i dzienne świece ceny MARK (`markPriceKlines`, ten sam host
  fapi.binance.com) TYLKO dla monet koszyka z wykrytym wstrzymaniem (`MARK_FILE`, `fetch_mark_safe`) —
  zwykle żadnej, więc zwykle zero dodatkowych zapytań; awaria nie zatrzymuje pobierania ani dziennika.
Tylko świece ZAMKNIĘTE (open_time + 1 dzień ≤ teraz). Testy bez sieci: `tests/test_live_journal.py`,
`tests/test_live_journal_p13.py`.

    PYTHONUTF8=1 py -m data.fetch_live
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import pandas as pd

from data.fetch_universe import (
    DAY_MS,
    KLINES_PAGE_LIMIT,
    REQUEST_PACING_S,
    STABLE_BASES,
    _call_with_retry,
    fetch_funding_raw,
)

ENGINE_START = pd.Timestamp("2025-09-01", tz="UTC")  # = backtest.live_journal.ENGINE_START (test)

LIVE_DIR = Path("data/raw/live")
# nazwa pliku z odpowiedzi giełdy: A–Z, 0–9 albo litery spoza ASCII (np. 币安人生USDT — był w top-20
# w 2026-05, X1F); żadnych kropek, ukośników, dwukropków, spacji ani małych liter ASCII
SYMBOL_RE = re.compile(r"(?:[A-Z0-9]|(?![\x00-\x7f])\w){1,40}USDT")
LIVE_START = (
    "2025-06-01T00:00:00Z"  # rozbieg: składy miesięczne, sygnał 28 dni, σ̂ EWMA, budżet ryzyka
)
# Poprawka 13: pliki obok świec — nazwy NIE pasują do `*_1d.parquet` ani `*_funding.parquet`, więc
# nie trafiają do paneli monet (`symbol_files`) ani do fundingu (`daily_funding_panel`).
STATUS_FILE = "binance_status.parquet"  # symbol, status, contract_type, delivery (UTC)
MARK_FILE = "binance_mark_daily.parquet"  # symbol, open_time, open, high, low, close (cena mark 1d)
STATUS_RE = re.compile(r"[A-Z_]{1,40}")  # status / typ kontraktu z odpowiedzi giełdy (np. SETTLING)


def active_usdt_perpetuals(
    exchange_info: dict, stable_bases: frozenset = STABLE_BASES
) -> list[str]:
    """Aktywne perpetuale `*USDT` (bez TRADIFI i stablecoinów jako bazy) z odpowiedzi `exchangeInfo`."""
    out = []
    for s in exchange_info.get("symbols", []):
        sym = s.get("symbol", "")
        if s.get("contractType") != "PERPETUAL" or s.get("status") != "TRADING":
            continue
        if s.get("quoteAsset") != "USDT" or not SYMBOL_RE.fullmatch(sym):
            continue
        base = sym[: -len("USDT")]
        if base and base not in stable_bases:
            out.append(sym)
    return sorted(out)


def parse_klines_1d(rows: list[list], end_ms: int) -> pd.DataFrame:
    """Surowe świece Binance → open_time (UTC), open, high, low, close, quote_volume; tylko zamknięte."""
    cols = ["open_time", "open", "high", "low", "close", "quote_volume"]
    if not rows:
        return pd.DataFrame({c: pd.Series(dtype=float) for c in cols}).astype(
            {"open_time": "datetime64[ns, UTC]"}
        )
    df = pd.DataFrame(
        {
            "open_time": pd.to_datetime([int(r[0]) for r in rows], unit="ms", utc=True),
            "open": [float(r[1]) for r in rows],
            "high": [float(r[2]) for r in rows],
            "low": [float(r[3]) for r in rows],
            "close": [float(r[4]) for r in rows],
            "quote_volume": [float(r[7]) for r in rows],
        }
    )
    closed = df["open_time"] + pd.Timedelta(days=1) <= pd.Timestamp(end_ms, unit="ms", tz="UTC")
    return df[closed].drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def fetch_klines_1d(
    exchange, symbol: str, start_ms: int, end_ms: int, pacing_s: float = REQUEST_PACING_S
) -> pd.DataFrame:
    rows: list[list] = []
    since = start_ms
    while since < end_ms:
        page = _call_with_retry(
            exchange.fapiPublicGetKlines,
            {
                "symbol": symbol,
                "interval": "1d",
                "startTime": since,
                "endTime": end_ms - 1,
                "limit": KLINES_PAGE_LIMIT,
            },
        )
        if not page:
            break
        rows.extend(page)
        last_open = int(page[-1][0])
        if last_open < since or len(page) < KLINES_PAGE_LIMIT:
            break
        since = last_open + DAY_MS
        time.sleep(pacing_s)
    return parse_klines_1d(rows, end_ms)


def symbol_files(live_dir: Path) -> dict[str, Path]:
    """Pliki świec perpetuali `<SYMBOL>_1d.parquet` — bez `coinbase_BTC-USD_1d.parquet` i innych."""
    out = {}
    for f in sorted(Path(live_dir).glob("*_1d.parquet")):
        sym = f.name[: -len("_1d.parquet")]
        if SYMBOL_RE.fullmatch(sym):
            out[sym] = f
    return out


def funding_symbols(live_dir: Path, now: pd.Timestamp) -> list[str]:
    """
    Funding potrzebny silnikowi: członkowie koszyka w każdym miesiącu od `ENGINE_START` + BTC.
    Skład ten sam co w dzienniku (`live_journal.basket_members`: od daty wejścia poprawki 13 bez dni
    z obrotem 0 w historii koszyka), żeby moneta wchodząca na miejsce zamrożonej miała funding.
    """
    from backtest.live_journal import basket_members

    volume = pd.concat(
        {
            s: d.set_index(pd.to_datetime(d["open_time"], utc=True))["quote_volume"]
            for s, d in ((s, pd.read_parquet(f)) for s, f in symbol_files(live_dir).items())
            if len(d)
        },
        axis=1,
    ).sort_index()
    members = basket_members(volume, list(pd.date_range(ENGINE_START, now, freq="MS")))
    return sorted({s for syms in members.values() for s in syms} | {"BTCUSDT"})


def contract_statuses(exchange_info: dict) -> pd.DataFrame:
    """
    Poprawka 13 (R1): status każdego kontraktu `*USDT` o bezpiecznej nazwie (`SYMBOL_RE`) z odpowiedzi
    `exchangeInfo` — także wycofanych (SETTLING; sonda 2026-10-05): symbol, status, contract_type
    i delivery (UTC; u wycofanego = moment wycofania). Teksty spoza `STATUS_RE` → „NIEZNANY”,
    zła data → brak (NaT): do pliku trafiają tylko nazwy, wielkie litery i liczby.
    """
    rows = []
    for s in exchange_info.get("symbols", []):
        sym = s.get("symbol", "")
        if (
            s.get("quoteAsset") != "USDT"
            or not isinstance(sym, str)
            or not SYMBOL_RE.fullmatch(sym)
        ):
            continue
        status, kind = str(s.get("status", "")), str(s.get("contractType", ""))
        try:
            ms = int(s.get("deliveryDate"))
            delivery = (
                pd.Timestamp(ms, unit="ms", tz="UTC") if 0 < ms < 7_000_000_000_000 else pd.NaT
            )
        except (TypeError, ValueError, OverflowError):
            delivery = pd.NaT
        rows.append(
            {
                "symbol": sym,
                "status": status if STATUS_RE.fullmatch(status) else "NIEZNANY",
                "contract_type": kind if STATUS_RE.fullmatch(kind) else "NIEZNANY",
                "delivery": delivery,
            }
        )
    out = pd.DataFrame(rows, columns=["symbol", "status", "contract_type", "delivery"])
    out["delivery"] = pd.to_datetime(out["delivery"], utc=True)
    return out.drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True)


def save_statuses_safe(exchange_info: dict, out_dir: Path) -> Path | None:
    """
    Zapis `contract_statuses` do `out_dir / STATUS_FILE` (nadpisywany w każdym przebiegu). Błąd →
    wydruk, plik usunięty (stary stan nie może udawać bieżącego) i `None` — dziennik wykrywa wtedy
    wstrzymanie samymi świecami (warunek „brak świecy” pokrywa się ze statusem).
    """
    path = Path(out_dir) / STATUS_FILE
    try:
        contract_statuses(exchange_info).to_parquet(path, index=False)
        return path
    except Exception as exc:  # noqa: BLE001 — statusy pomocnicze, nie mogą zatrzymać pobierania
        print(f"[live] statusy kontraktów BŁĄD {type(exc).__name__}: {str(exc)[:120]}", flush=True)
        path.unlink(missing_ok=True)
        return None


def parse_mark_klines_1d(rows: list[list], end_ms: int) -> pd.DataFrame:
    """Surowe świece ceny mark → open_time (UTC), open, high, low, close; tylko zamknięte dni."""
    cols = ["open_time", "open", "high", "low", "close"]
    if not rows:
        return pd.DataFrame({c: pd.Series(dtype=float) for c in cols}).astype(
            {"open_time": "datetime64[ns, UTC]"}
        )
    df = pd.DataFrame(
        {
            "open_time": pd.to_datetime([int(r[0]) for r in rows], unit="ms", utc=True),
            "open": [float(r[1]) for r in rows],
            "high": [float(r[2]) for r in rows],
            "low": [float(r[3]) for r in rows],
            "close": [float(r[4]) for r in rows],
        }
    )
    closed = df["open_time"] + pd.Timedelta(days=1) <= pd.Timestamp(end_ms, unit="ms", tz="UTC")
    return df[closed].drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def fetch_mark_1d(
    exchange, symbol: str, start_ms: int, end_ms: int, pacing_s: float = REQUEST_PACING_S
) -> pd.DataFrame:
    """Świece dzienne ceny mark (`fapiPublicGetMarkPriceKlines`, publiczne, bez klucza) stronami."""
    rows: list[list] = []
    since = start_ms
    while since < end_ms:
        page = _call_with_retry(
            exchange.fapiPublicGetMarkPriceKlines,
            {
                "symbol": symbol,
                "interval": "1d",
                "startTime": since,
                "endTime": end_ms - 1,
                "limit": KLINES_PAGE_LIMIT,
            },
        )
        if not page:
            break
        rows.extend(page)
        last_open = int(page[-1][0])
        if last_open < since or len(page) < KLINES_PAGE_LIMIT:
            break
        since = last_open + DAY_MS
        time.sleep(pacing_s)
    return parse_mark_klines_1d(rows, end_ms)


MARK_COLS = ["symbol", "open_time", "open", "high", "low", "close"]


def _read_mark_file(path: Path) -> pd.DataFrame | None:
    """Istniejący `MARK_FILE` (brak pliku = None). Plik nieczytelny albo bez kolumn = wyjątek."""
    if not path.exists():
        return None
    old = pd.read_parquet(path)
    missing = [c for c in MARK_COLS if c not in old.columns]
    if missing:
        raise ValueError(f"{MARK_FILE}: brak kolumn {missing}")
    return old[MARK_COLS]


def fetch_mark_safe(
    exchange,
    out_dir: Path,
    end_ms: int,
    pacing_s: float = REQUEST_PACING_S,
    settled: set[tuple[str, str]] | None = None,
) -> dict:
    """
    Poprawka 13 (R2): cena mark 1d od daty wejścia poprawki TYLKO dla monet koszyka z wykrytym
    wstrzymaniem, którego rejestr rozliczeń dziennika jeszcze nie zapisał (`settled` = klucze
    (symbol, d1); `live_journal.halted_symbols` na świeżo pobranych plikach i statusach) — zwykle
    żadnej, czyli zero zapytań; zdarzenie już rozliczone bierze cenę z rejestru, więc późniejsza
    cena mark niczego nie zmienia. Nowe świece zastępują w `MARK_FILE` stare o tym samym kluczu
    (symbol, dzień), pozostałe zostają. Plik nieczytelny (np. przerwany zapis) jest przebudowywany
    z samego nowego pobrania — rozliczenia już zapisane się nie zmieniają (rejestr). Zwraca
    {"symbols": monety, "blad": None albo „BŁĄD <typ>” — do pola logu „cena mark BŁĄD …”}. Błąd
    pobrania pojedynczej monety → wydruk (dziennik rozliczy ją bez ceny mark i zgłosi to w logu).
    """
    from backtest import live_journal as lj

    out: dict = {"symbols": [], "blad": None}
    path = Path(out_dir) / MARK_FILE
    try:
        old = _read_mark_file(path)
    except Exception as exc:  # noqa: BLE001 — zepsuty plik: przebudowa, błąd do logu dziennika
        out["blad"] = f"BŁĄD {type(exc).__name__}"
        print(
            f"[live] cena mark BŁĄD {type(exc).__name__}: plik {MARK_FILE} nieczytelny — usunięty "
            "i przebudowany z nowego pobrania; zapisane rozliczenia bez zmian (rejestr)",
            flush=True,
        )
        path.unlink(missing_ok=True)
        old = None
    try:
        if lj.POPRAWKA13_OD is None:
            return out
        syms = [s for s in lj.halted_symbols(out_dir, settled) if SYMBOL_RE.fullmatch(s)]
        out["symbols"] = syms
        if not syms:
            return out
        start_ms = int(lj.POPRAWKA13_OD.value // 1_000_000)
        frames, failed = [], []
        for sym in syms:
            try:
                frames.append(fetch_mark_1d(exchange, sym, start_ms, end_ms).assign(symbol=sym))
            except Exception as exc:  # noqa: BLE001 — jedna moneta nie blokuje pozostałych
                failed.append(f"{sym} {type(exc).__name__}")
            time.sleep(pacing_s)
        parts = ([old] if old is not None else []) + [f[MARK_COLS] for f in frames if len(f)]
        if parts:
            mark = pd.concat(parts, ignore_index=True)
            mark["open_time"] = pd.to_datetime(mark["open_time"], utc=True)
            mark = mark.drop_duplicates(["symbol", "open_time"], keep="last")
            mark.sort_values(["symbol", "open_time"])[MARK_COLS].to_parquet(path, index=False)
        print(f"[live] cena mark (poprawka 13): {len(syms)} monet: {', '.join(syms)}", flush=True)
        if failed:
            print(f"[live] cena mark BŁĄD: {', '.join(failed)}", flush=True)
        return out
    except Exception as exc:  # noqa: BLE001 — cena mark pomocnicza, nie może zatrzymać pobierania
        out["blad"] = out["blad"] or f"BŁĄD {type(exc).__name__}"
        print(
            f"[live] cena mark BŁĄD {type(exc).__name__}: {str(exc)[:120]} — bez aktualizacji",
            flush=True,
        )
        return out


def fetch_fng_safe(out_dir: Path) -> Path | None:
    """
    Fear & Greed (alternative.me) do `out_dir` (poprawka 8): pełna historia, nadpisywana przy każdym
    przebiegu. Błąd sieci/schematu → wydruk i `None`; dziennik ma liczyć bez etykiety.
    """
    from data.fetch_external import fetch_fng

    try:
        return fetch_fng(out_dir, force=True)
    except Exception as exc:  # noqa: BLE001 — etykieta pomocnicza, nie może zatrzymać przebiegu
        print(
            f"[live] Fear & Greed BŁĄD {type(exc).__name__}: {str(exc)[:120]} — etykieta bez aktualizacji",
            flush=True,
        )
        return None


def fetch_coinm_funding_safe(out_dir: Path) -> Path | None:
    """
    Funding COIN-M `BTCUSD_PERP` do `out_dir` (poprawka 12, noga carry): historia od startu nogi
    (`journal_carry.CARRY_START`), pobierana od nowa i nadpisywana przy każdym przebiegu — plik rośnie
    o 3 rozliczenia dziennie (jedno zapytanie na ~330 dni), a późniejsza zmiana stawki po stronie
    giełdy wychodzi w dzienniku jako pole „carry zmiany N”. Błąd sieci/schematu (wyjątek) → wydruk
    i `None`; stary plik zostaje, pozostałe nogi liczą się normalnie, a dziennik zgłasza „carry
    spóźnione”. Pusta odpowiedź giełdy (HTTP 200 z `[]`) to nie wyjątek: plik zostaje nadpisany
    pustym. Wtedy `carry_wyniki.csv` zostaje nietknięty, ten jeden przebieg zgłasza „carry
    spóźnione”, a następny pobiera całą historię od nowa i dopisuje zaległe dni.
    """
    from backtest.journal_carry import CARRY_START, CARRY_SYMBOL
    from data.fetch_external import fetch_coinm_funding

    try:
        return fetch_coinm_funding(
            CARRY_SYMBOL, CARRY_START.strftime("%Y-%m-%d"), out_dir, force=True
        )
    except Exception as exc:  # noqa: BLE001 — noga tylko do zapisu, nie może zatrzymać przebiegu
        print(
            f"[live] funding COIN-M {CARRY_SYMBOL} BŁĄD {type(exc).__name__}: {str(exc)[:120]} "
            "— carry bez aktualizacji",
            flush=True,
        )
        return None


def run(
    out_dir: Path = LIVE_DIR, start: str = LIVE_START, settled: set[tuple[str, str]] | None = None
) -> dict:
    """
    Pobranie wszystkich źródeł dziennika do `out_dir`. `settled` (poprawka 13) = zdarzenia już
    zapisane w rejestrze rozliczeń dziennika — dla nich cena mark nie jest pobierana. Zwraca
    {"symbols", "fetched_at", "mark_blad"} (`mark_blad` = błąd ceny mark do pola logu albo None).
    """
    import ccxt

    from data.fetch_external import fetch_coinbase_daily
    from data.fetch_ohlcv import get_ohlcv

    out_dir.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now(tz="UTC")
    end_ms = int(now.value // 1_000_000)
    start_ms = int(pd.Timestamp(start).value // 1_000_000)
    ex = ccxt.binanceusdm({"enableRateLimit": False})
    info = ex.fapiPublicGetExchangeInfo()
    symbols = active_usdt_perpetuals(info)
    save_statuses_safe(info, out_dir)  # poprawka 13 (R1): statusy, także wycofanych
    print(f"[live] {len(symbols)} aktywnych perpetuali USDT", flush=True)
    for i, sym in enumerate(symbols, 1):
        kl = fetch_klines_1d(ex, sym, start_ms, end_ms)
        time.sleep(REQUEST_PACING_S)
        kl.to_parquet(out_dir / f"{sym}_1d.parquet", index=False)
        if i % 100 == 0:
            print(f"[live] świece {i}/{len(symbols)}", flush=True)
    need = funding_symbols(out_dir, now)
    print(
        f"[live] funding dla {len(need)} członków koszyka od {ENGINE_START.date()} + BTC",
        flush=True,
    )
    for sym in need:
        fu = fetch_funding_raw(ex, sym, start_ms, end_ms)
        time.sleep(REQUEST_PACING_S)
        fu.to_parquet(out_dir / f"{sym}_funding.parquet", index=False)
    fetch_coinbase_daily("BTC-USD", start[:10], out_dir, force=True)
    spot = get_ohlcv("BTC/USDT", "8h", start, now.strftime("%Y-%m-%dT%H:%M:%SZ"), "binance")
    spot = spot[spot["timestamp"] + pd.Timedelta(hours=8) <= now]
    spot.to_parquet(out_dir / "spot_BTC-USDT_8h.parquet", index=False)
    fetch_fng_safe(out_dir)
    fetch_coinm_funding_safe(out_dir)
    # poprawka 13 (R2): tylko monety z wykrytym, jeszcze nierozliczonym wstrzymaniem
    mark = fetch_mark_safe(ex, out_dir, end_ms, settled=settled)
    return {"symbols": len(symbols), "fetched_at": now.isoformat(), "mark_blad": mark["blad"]}


if __name__ == "__main__":
    info = run(Path(sys.argv[1]) if len(sys.argv) > 1 else LIVE_DIR)
    print(f"[live] koniec: {info}", flush=True)
