"""
liquidation_index.py — dzienny indeks likwidacji per giełda × symbol z plików JSONL kolektorów
(Binance: `data/collect_liquidations.py`, katalog `~/likwidacje`; Bybit: kolektor pełnych likwidacji,
katalog `~/likwidacje_bybit`). Higiena danych przed przyszłą kartą E1 — 0 wariantów, 0 odczytów cen.

Po co (docs/rag/11, sekcja 2 i 3, decyzja użytkownika 2026-09-27 „wykonaj wszystkie”): jeden mały
plik CSV na dzień pozwala policzyć częstość kaskad (rachunek mocy za 4–6 tyg.) i porównać Bybit
z LK0 bez otwierania surowych plików i BEZ oglądania cen.

Kolumny `indeks/<gielda>_<YYYY-MM-DD>.csv` (jeden wiersz na symbol, sortowane po symbolu):
- `gielda`, `dzien` (dzień UTC pliku źródłowego), `symbol`, `rynek` (`UM` = kontrakt w USDT/USDC,
  ilość w monecie; `CM` = kontrakt odwrotny, ilość w kontraktach/USD — patrz „Nominał” niżej);
- `zdarzenia`, `zdarzenia_long`, `zdarzenia_short` — liczba zdarzeń; long/short = strona
  ZLIKWIDOWANEJ POZYCJI (nie strona zlecenia);
- `nominal_usdt`, `nominal_long_usdt`, `nominal_short_usdt` — suma nominału w USDT;
- `maks_nominal_5min_usdt` — największa suma nominału w dowolnym oknie 5 min `[T, T + 5 min)`
  (okno przesuwne; maksimum zawsze wypada w oknie zaczynającym się na zdarzeniu). **Dla Binance ta
  kolumna ma SUFIT z próbkowania** — strumień `!forceOrder@arr` pokazuje ≤ 1 zlecenie na sekundę na
  symbol, więc w kaskadzie widać tylko próbkę. Nadaje się WYŁĄCZNIE do rang (który dzień/symbol
  był gorszy), nie do wielkości kaskady ani do porównania z Bybit 1:1;
- `pierwsze_utc`, `ostatnie_utc` — czas `T` pierwszego i ostatniego zdarzenia (ISO, ms, `Z`).

Mapowanie stron — ODWROTNE znaczenie pola `S` między giełdami (test `test_strony_*`):
- Binance: `S` = strona ZLECENIA likwidacyjnego. `SELL` = giełda sprzedaje = zlikwidowany LONG;
  `BUY` = zlikwidowany SHORT.
- Bybit (`allLiquidation`): `S` = strona POZYCJI. `Buy` = zlikwidowany LONG; `Sell` = SHORT.
Nominał: Binance `q × ap` (średnia cena wykonania), a gdy `ap` puste lub 0 → `q × p`;
Bybit `v × p` (`p` = cena upadłości). WYJĄTEK — kontrakty odwrotne (kolumna `rynek` = `CM`):
strumień `!forceOrder@arr` niesie też COIN-M Binance (`st` = 2, np. `BTCUSD_PERP`; ~0,5 % zdarzeń
LK0, zmierzone 2026-09-27), gdzie `q` to liczba KONTRAKTÓW po 100 USD (BTCUSD) albo 10 USD (reszta),
więc nominał = `q × wartość kontraktu`; `q × ap` zawyżałoby go ~1000× (BTCUSD_PERP: 790 mln USDT
„w 5 min” 2026-09-25 zamiast 0,95 mln). Bybit odwrotny (`BTCUSD`, `BTCUSDZ25`): `v` jest już w USD.
Arytmetyka na `Decimal` z tekstów JSON — sumy są dokładne, więc plik jest bajt w bajt ten sam
niezależnie od platformy; zaokrąglenie do 0,01 USDT na końcu.

Zasady:
- czyste funkcje (`side_of`, `notional`, `parse_line`, `aggregate`, `index_csv`, `closed_days`)
  testowane bez sieci (`tests/test_liquidation_index.py`); zapis tylko przez `write_if_changed`;
- tylko dni ZAMKNIĘTE: dzień z nazwy pliku < dziś UTC (plik bieżącego dnia jest w trakcie zapisu);
- plik źródłowy otwierany wyłącznie do odczytu; linia, której nie da się odczytać, jest
  pomijana i liczona (`zle_linie`), nie przerywa indeksu. „Nie da się odczytać” obejmuje też pola
  z sieci poza zakresem: `T` łamiące wspólną regułę czasu `data/liquidation_time.event_time_ms`
  (bool, nie liczba, poza 2019-01-01 … 2100-01-01 UTC; tę samą funkcję stosuje kolektor LK0 przy
  zapisie — zadanie 021) i symbol, który zepsułby CSV (przecinek,
  cudzysłów, biały znak, znak sterujący, początek `=`/`+`/`-`/`@` = formuła w arkuszu). Symbole
  spoza ASCII są DOZWOLONE — Binance ma prawdziwe kontrakty `龙虾USDT`, `币安人生USDT` (5 symboli,
  762 zdarzenia LK0 w dniach 2026-09-25…27, zmierzone przy przeglądzie);
- idempotencja: te same wejścia → te same bajty; `write_if_changed` nie dotyka pliku bez zmian.

    PYTHONUTF8=1 py -m data.liquidation_index --gielda binance --dir ~/likwidacje --out /tmp/indeks
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path

from data import liquidation_time as lt

GIELDY = ("binance", "bybit")
# podbić przy każdej zmianie kolumn lub definicji → kopia (manifest) przelicza wszystkie indeksy
INDEX_VERSION = 1
WINDOW_MS = 5 * 60 * 1000
CENT = Decimal("0.01")
MAX_NOTIONAL_USDT = Decimal("1e12")  # sufit jednej likwidacji (przegląd bezpieczeństwa 2026-09-27)
DAY_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")
# COIN-M Binance (`st` = 2, symbole `BTCUSD_PERP`, `ETHUSD_261225`): `q` to liczba KONTRAKTÓW
CM_CONTRACT_USD = {"BTCUSD": Decimal(100)}
CM_CONTRACT_USD_DEFAULT = Decimal(10)
_BINANCE_CM = re.compile(r"USD_(PERP|\d{6})$")
_BYBIT_INVERSE = re.compile(r"[A-Z0-9]+USD([FGHJKMNQUVXZ]\d{2})?")  # BTCUSD, BTCUSDZ25
# granice czasu zdarzenia: jedno źródło w `data/liquidation_time.py` (wspólne z kolektorami, bez
# importu kolektora z jego kodem sieciowym); poza nimi `_iso_ms` rzucałoby błąd z platformy
MIN_EVENT_MS, MAX_EVENT_MS = lt.MIN_EVENT_MS, lt.MAX_EVENT_MS  # 2019-01-01 … 2100-01-01 UTC
# symbol bezpieczny dla CSV bez cytowania: bez przecinka, cudzysłowów, białych i sterujących znaków,
# bez początku formuły arkusza (=, +, -, @); litery spoza ASCII dozwolone (docstring modułu)
_SYMBOL = re.compile(r"[^\s,\"'=+\-@\x00-\x1f\x7f][^\s,\"'\x00-\x1f\x7f]{0,39}")
COLUMNS = (
    "gielda",
    "dzien",
    "symbol",
    "rynek",
    "zdarzenia",
    "zdarzenia_long",
    "zdarzenia_short",
    "nominal_usdt",
    "nominal_long_usdt",
    "nominal_short_usdt",
    "maks_nominal_5min_usdt",
    "pierwsze_utc",
    "ostatnie_utc",
)
# strona z pola `S` → strona ZLIKWIDOWANEJ pozycji (docstring: odwrotne znaczenie między giełdami)
_SIDE = {
    "binance": {"SELL": "long", "BUY": "short"},
    "bybit": {"Buy": "long", "Sell": "short"},
}


@dataclass(frozen=True)
class Event:
    symbol: str
    market: str  # "UM" | "CM"
    t_ms: int
    side: str  # "long" | "short" — strona zlikwidowanej pozycji
    notional: Decimal


@dataclass
class DayIndex:
    gielda: str
    dzien: str
    rows: list[dict] = field(default_factory=list)
    lines: int = 0
    bad_lines: int = 0


# ------------------------------------------------------------------ czyste funkcje
def _check_exchange(gielda: str) -> None:
    if gielda not in GIELDY:
        raise ValueError(f"indeks likwidacji: nieznana giełda {gielda!r} (znane: {GIELDY})")


def side_of(gielda: str, s_field: str) -> str:
    """Pole `S` → strona zlikwidowanej pozycji. Wielkość liter musi zgadzać się z giełdą."""
    _check_exchange(gielda)
    try:
        return _SIDE[gielda][s_field]
    except (KeyError, TypeError):
        raise ValueError(f"indeks likwidacji: {gielda} nieznana strona S={s_field!r}") from None


def _dec(x) -> Decimal:
    if isinstance(x, bool) or x is None:
        raise ValueError(f"indeks likwidacji: zła liczba {x!r}")
    try:
        d = Decimal(str(x).strip()) if not isinstance(x, Decimal) else x
    except InvalidOperation:
        raise ValueError(f"indeks likwidacji: zła liczba {x!r}") from None
    if not d.is_finite() or d < 0:
        raise ValueError(f"indeks likwidacji: zła liczba {x!r}")
    return d


def market_of(gielda: str, rec: dict) -> str:
    """`UM` (kontrakt rozliczany w stablecoinie, ilość w monecie) albo `CM` (odwrotny: ilość w USD)."""
    _check_exchange(gielda)
    sym = str(rec.get("s", ""))
    if gielda == "binance":
        return "CM" if str(rec.get("st")) == "2" or _BINANCE_CM.search(sym) else "UM"
    return "CM" if _BYBIT_INVERSE.fullmatch(sym) else "UM"


def cm_contract_usd(rec: dict) -> Decimal:
    """Wartość kontraktu COIN-M Binance w USD: BTCUSD 100, pozostałe pary 10 (specyfikacja giełdy)."""
    pair = str(rec.get("ps") or str(rec.get("s", "")).split("_")[0])
    return CM_CONTRACT_USD.get(pair, CM_CONTRACT_USD_DEFAULT)


def notional(gielda: str, rec: dict) -> Decimal:
    """Nominał USDT (docstring modułu): UM Binance `q × ap` (gdy `ap` puste/0 → `q × p`), CM Binance
    `q × wartość kontraktu`, Bybit liniowy `v × p`, Bybit odwrotny `v` (wielkość już w USD)."""
    _check_exchange(gielda)
    cm = market_of(gielda, rec) == "CM"
    if gielda == "binance":
        q = _dec(rec["q"])
        if cm:
            return q * cm_contract_usd(rec)
        ap_raw = rec.get("ap")
        ap = _dec(ap_raw) if ap_raw not in (None, "") else Decimal(0)
        return q * (ap if ap > 0 else _dec(rec["p"]))
    v = _dec(rec["v"])
    return v if cm else v * _dec(rec["p"])


def parse_line(gielda: str, line: str) -> Event:
    """Jedna linia JSONL → `Event`; `ValueError` przy każdym błędzie (linia jest wtedy pomijana)."""
    try:
        rec = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"indeks likwidacji: zły JSON ({exc.msg})") from None
    if not isinstance(rec, dict):
        raise ValueError("indeks likwidacji: linia nie jest obiektem JSON")
    try:
        symbol, t_raw, s_raw = rec["s"], rec["T"], rec["S"]
    except KeyError as exc:
        raise ValueError(f"indeks likwidacji: brak pola {exc}") from None
    if not isinstance(symbol, str) or not _SYMBOL.fullmatch(symbol):
        raise ValueError(f"indeks likwidacji: zły symbol {str(symbol)[:60]!r}")
    try:  # wspólna reguła czasu (bool, nie liczba, 1e400 → inf, poza 2019…2100 = zła linia)
        t_ms = lt.event_time_ms(t_raw)
    except ValueError as exc:
        raise ValueError(f"indeks likwidacji: zły czas T: {exc}") from None
    try:
        nom = notional(gielda, rec)
    except KeyError as exc:
        raise ValueError(f"indeks likwidacji: brak pola {exc}") from None
    # Sufit nominału jednej likwidacji: realne zdarzenia to < 1e9 USDT; wartość absurdalna (np. v = p = 1e20)
    # wysadziłaby formatowanie sumy dnia (Decimal.quantize) i zatrzymała kopię CAŁEGO dnia — to zła linia.
    if not nom.is_finite() or nom > MAX_NOTIONAL_USDT:
        raise ValueError(f"indeks likwidacji: nominał poza zakresem ({str(nom)[:40]})")
    return Event(
        symbol=symbol,
        market=market_of(gielda, rec),
        t_ms=t_ms,
        side=side_of(gielda, s_raw),
        notional=nom,
    )


def max_window_sum(events: list[tuple[int, Decimal]], window_ms: int = WINDOW_MS) -> Decimal:
    """Największa suma nominału w oknie `[t, t + window_ms)` — dwa wskaźniki po posortowanym czasie."""
    pts = sorted(events, key=lambda e: e[0])
    best = Decimal(0)
    run = Decimal(0)
    lo = 0
    for t_hi, v_hi in pts:
        run += v_hi
        while pts[lo][0] <= t_hi - window_ms:  # zdarzenie `lo` wypadło z okna kończącego się na hi
            run -= pts[lo][1]
            lo += 1
        best = max(best, run)
    return best


def _iso_ms(t_ms: int) -> str:
    t = dt.datetime.fromtimestamp(t_ms / 1000.0, tz=dt.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t_ms % 1000:03d}Z"


def _fmt(d: Decimal) -> str:
    return str(d.quantize(CENT, rounding=ROUND_HALF_EVEN))


def aggregate(gielda: str, dzien: str, lines) -> DayIndex:
    """Linie JSONL jednego dnia → `DayIndex` (wiersze per symbol, liczba linii i złych linii)."""
    _check_exchange(gielda)
    out = DayIndex(gielda=gielda, dzien=dzien)
    per: dict[str, list[Event]] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        out.lines += 1
        try:
            ev = parse_line(gielda, line)
        except ValueError:
            out.bad_lines += 1
            continue
        per.setdefault(ev.symbol, []).append(ev)
    for sym in sorted(per):
        evs = per[sym]
        longs = [e for e in evs if e.side == "long"]
        shorts = [e for e in evs if e.side == "short"]
        ts = [e.t_ms for e in evs]
        out.rows.append(
            {
                "gielda": gielda,
                "dzien": dzien,
                "symbol": sym,
                "rynek": evs[0].market,
                "zdarzenia": str(len(evs)),
                "zdarzenia_long": str(len(longs)),
                "zdarzenia_short": str(len(shorts)),
                "nominal_usdt": _fmt(sum((e.notional for e in evs), Decimal(0))),
                "nominal_long_usdt": _fmt(sum((e.notional for e in longs), Decimal(0))),
                "nominal_short_usdt": _fmt(sum((e.notional for e in shorts), Decimal(0))),
                "maks_nominal_5min_usdt": _fmt(max_window_sum([(e.t_ms, e.notional) for e in evs])),
                "pierwsze_utc": _iso_ms(min(ts)),
                "ostatnie_utc": _iso_ms(max(ts)),
            }
        )
    return out


def index_csv(idx: DayIndex) -> bytes:
    """`DayIndex` → bajty CSV (UTF-8, `\\n`, bez cudzysłowów — pola nie zawierają przecinków)."""
    lines = [",".join(COLUMNS)]
    for r in idx.rows:
        vals = [r[c] for c in COLUMNS]
        if any("," in v or "\n" in v or '"' in v for v in vals):
            raise ValueError(f"indeks likwidacji: niedozwolony znak w wierszu {vals}")
        lines.append(",".join(vals))
    return ("\n".join(lines) + "\n").encode("utf-8")


def index_path(out_dir: Path, gielda: str, dzien: str) -> Path:
    return Path(out_dir) / f"{gielda}_{dzien}.csv"


def closed_days(src_dir: Path, today: dt.date) -> list[tuple[str, Path]]:
    """Pliki `YYYY-MM-DD.jsonl` z dniem < `today` (UTC), rosnąco. Brak katalogu → pusta lista."""
    src_dir = Path(src_dir)
    if not src_dir.is_dir():
        return []
    out = []
    for p in src_dir.iterdir():
        m = DAY_FILE.match(p.name)
        if not m or not p.is_file():
            continue
        try:
            day = dt.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if day < today:
            out.append((m.group(1), p))
    return sorted(out)


def utc_today(now: dt.datetime | None = None) -> dt.date:
    now = dt.datetime.now(tz=dt.timezone.utc) if now is None else now
    return now.astimezone(dt.timezone.utc).date()


# ------------------------------------------------------------------ zapis (jedyny efekt uboczny)
def write_if_changed(path: Path, data: bytes) -> str:
    """Zapis atomowy tylko przy zmianie: zwraca `nowy` / `bez zmian` / `zmieniony`."""
    path = Path(path)
    if path.exists():
        if path.read_bytes() == data:
            return "bez zmian"
        state = "zmieniony"
    else:
        state = "nowy"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return state


def build_index(gielda: str, dzien: str, src: Path) -> DayIndex:
    """Plik źródłowy (tylko odczyt) → `DayIndex`."""
    with open(src, encoding="utf-8", errors="replace") as f:
        return aggregate(gielda, dzien, f)


def main(argv: list[str]) -> int:
    gielda, src, out = None, None, None
    it = iter(argv)
    for a in it:
        if a == "--gielda":
            gielda = next(it)
        elif a == "--dir":
            src = Path(next(it)).expanduser()
        elif a == "--out":
            out = Path(next(it)).expanduser()
        else:
            print(f"nieznany argument {a!r}", file=sys.stderr)
            return 2
    if gielda not in GIELDY or src is None or out is None:
        print(
            "użycie: --gielda binance|bybit --dir <źródło> --out <katalog indeksu>", file=sys.stderr
        )
        return 2
    for dzien, path in closed_days(src, utc_today()):
        idx = build_index(gielda, dzien, path)
        state = write_if_changed(index_path(out, gielda, dzien), index_csv(idx))
        print(
            f"{gielda} {dzien}: linii {idx.lines}, złych {idx.bad_lines}, "
            f"symboli {len(idx.rows)} — {state}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
