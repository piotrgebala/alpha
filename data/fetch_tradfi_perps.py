"""
fetch_tradfi_perps.py — perpetuale TradFi (akcje, ETF-y, surowce, waluty) z Bybit i Binance (runda PT1).

Tylko publiczne endpointy REST, bez klucza API; adresy stałe w kodzie, wyłącznie ``https://``.

- ``migawka``: surowe odpowiedzi tickerów obu giełd (najlepsza oferta kupna / sprzedaży, obrót 24 h,
  cena indeksu i mark, bieżący funding) zapisane jako ``.json.gz`` — parsowanie osobno, żeby plik był
  wierną kopią źródła. Przed zapisem ``sprawdz_migawke`` (Bybit ``retCode == 0`` i ``result.list``,
  Binance — listy rekordów); zapis atomowy (plik ``.tmp`` + ``os.replace``), więc przerwany zapis
  nie zostawia uciętego ``.json.gz``. Tryb pętli (``--co`` sekund, ``--do`` czas UTC) zbiera kilka
  migawek w różnych godzinach handlu rynku bazowego.
- ``spis``: instrumenty TradFi obu giełd + BTCUSDT (kontrola). Bybit ``instruments-info`` (kursor
  stron; TradFi = ``symbolType ∈ {stock, ETF, commodity, forex}``), Binance ``exchangeInfo``
  (``contractType == TRADIFI_PERPETUAL``) + ``fundingInfo`` (interwał, cap/floor) →
  ``spis_{bybit,binance}.parquet`` (kolumny wybrane + ``surowe`` = pełny rekord JSON ze źródła).
- ``funding``: historia stawek od ``FUNDING_OD`` dla całego spisu. Bybit ``funding/history`` (lista
  malejąco — stronicowanie WSTECZ, ``endTime = min − 1``), Binance ``fundingRate`` (rosnąco —
  stronicowanie NAPRZÓD, ``startTime = max + 1``); deduplikacja po czasie →
  ``funding_{bybit,binance}.parquet`` (symbol, czas UTC, fundingRate).
- ``swiece``: świece 1 h ceny ostatniej, indeksu i mark dla RDZENIA rundy (reguła pre-rejestracji:
  waluty, surowce, ETF-y z ``ETF_RDZEN``, 5 akcji USA o największym obrocie 24 h w PIERWSZEJ migawce,
  BTCUSDT) od startu instrumentu (BTCUSDT od ``FUNDING_OD``) → ``swiece_{gielda}_{rodzaj}_1h.parquet``
  + ``rdzen.json`` (skład rdzenia i obroty, z których wynika).
- ``premia``: minutowy indeks premii Bybit (``premium-index-price-kline``) dla ``PREMIA_SYMBOLE``
  z ostatnich ``PREMIA_DNI`` dni → ``premia_bybit_1m.parquet`` (druga droga P2: odtworzenie fundingu
  ze wzoru giełdy).

Klasy (``klasa_bybit`` / ``klasa_binance``): waluty, surowce, ETF, ETF_oblig (TLT/TBT/TMF), akcje,
przed_IPO (Binance PREMARKET), BTC_kontrola. Binance nie oznacza ETF-ów (``underlyingType = EQUITY``
także dla SPY czy SOXL) — ETF = baza z listy pre-rejestracji ALBO ten sam symbol ma na Bybit
``symbolType = ETF`` (kolumna ``klasa_zrodlo`` mówi, która reguła zadziałała).

Warstwa sieciowa: ``Klient`` — odczekanie między żądaniami (limity: Binance 2400 wag/min, ``fundingRate``
+ ``fundingInfo`` 500 żądań / 5 min / IP; Bybit 600 żądań / 5 s / IP) i ponowienie z wykładniczym
odczekaniem przy HTTP 429/5xx, błędach sieci i ``retCode 10006`` Bybit (``Retry-After`` najwyżej
``RETRY_AFTER_MAX_S`` = 300 s); HTTP 418 (blokada IP Binance) → ``BlokadaIP``, który przerywa CAŁĄ
komendę (pętle per symbol go nie łapią); pozostałe 4xx → błąd od razu (pętla per symbol zapisuje
błąd i idzie dalej). Stronicowanie (``stronicuj_wstecz`` / ``stronicuj_naprzod``) i parsery są
czyste — testy bez sieci: ``tests/test_fetch_tradfi_perps.py``.

    PYTHONUTF8=1 py -m data.fetch_tradfi_perps {migawka,spis,funding,swiece,premia}

Dane POZA repo (``data/raw`` w .gitignore): ``data/raw/tradfi_perps/``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pandas as pd

BYBIT = "https://api.bybit.com"
BINANCE = "https://fapi.binance.com"
OUT = Path("data/raw/tradfi_perps")
MIGAWKA_URLS = {
    "bybit_tickers": f"{BYBIT}/v5/market/tickers?category=linear",
    "binance_book": f"{BINANCE}/fapi/v1/ticker/bookTicker",
    "binance_24h": f"{BINANCE}/fapi/v1/ticker/24hr",
    "binance_premium": f"{BINANCE}/fapi/v1/premiumIndex",
}

BYBIT_INSTR = f"{BYBIT}/v5/market/instruments-info"
BYBIT_FUNDING = f"{BYBIT}/v5/market/funding/history"
BYBIT_KLINE = {
    "last": f"{BYBIT}/v5/market/kline",
    "index": f"{BYBIT}/v5/market/index-price-kline",
    "mark": f"{BYBIT}/v5/market/mark-price-kline",
    "premia": f"{BYBIT}/v5/market/premium-index-price-kline",
}
BINANCE_INFO = f"{BINANCE}/fapi/v1/exchangeInfo"
BINANCE_FUNDING_INFO = f"{BINANCE}/fapi/v1/fundingInfo"
BINANCE_FUNDING = f"{BINANCE}/fapi/v1/fundingRate"
BINANCE_KLINE = {
    "last": f"{BINANCE}/fapi/v1/klines",
    "index": f"{BINANCE}/fapi/v1/indexPriceKlines",
    "mark": f"{BINANCE}/fapi/v1/markPriceKlines",
}

KONTROLA = "BTCUSDT"
BYBIT_TRADFI_TYPES = ("stock", "ETF", "commodity", "forex")
BINANCE_TRADFI = "TRADIFI_PERPETUAL"
FUNDING_OD = "2025-12-01"
ETF_RDZEN = ("SPY", "QQQ", "IWM", "EWJ", "EWZ", "EWY", "TLT", "TBT", "TMF", "XLE", "GDX")
ETF_OBLIG = ("TLT", "TBT", "TMF")
N_AKCJI_RDZEN = 5
PREMIA_SYMBOLE = ("EURUSDUSDT", "USDJPYUSDT", "XAUUSDT", "BTCUSDT")
PREMIA_DNI = 14
RODZAJE = ("last", "index", "mark")
KLASY = ("waluty", "surowce", "ETF", "ETF_oblig", "akcje", "przed_IPO", "BTC_kontrola")
BINANCE_REGION = {"EQUITY": "US", "HK_EQUITY": "HK", "KR_EQUITY": "KR", "CN_EQUITY": "CN"}

MINUTE_MS = 60_000
HOUR_MS = 3_600_000
MIN_MS = 1_420_070_400_000  # 2015-01-01 — znacznik czasu spoza zakresu = błąd parsera
MAX_MS = 4_102_444_800_000  # 2100-01-01
BYBIT_KLINE_LIMIT = 1000
BYBIT_FUNDING_LIMIT = 200
BINANCE_KLINE_LIMIT = 1500
BINANCE_FUNDING_LIMIT = 1000
MAX_STRON = 2000

RETRY_HTTP = (429, 500, 502, 503, 504)
HTTP_BLOKADA_IP = 418  # Binance: IP zablokowane po ignorowaniu 429 — dotyczy wszystkich symboli
RETRY_AFTER_MAX_S = 300.0  # górny limit odczekania z nagłówka Retry-After
BYBIT_RETCODE_LIMIT = 10006  # Bybit: „Too many visits” w treści odpowiedzi HTTP 200
PROBY = 6
BACKOFF_S = 2.0
# Odczekanie między żądaniami: najdłuższy pasujący prefiks adresu wygrywa.
PACING_S = {
    f"{BYBIT}/": 0.06,  # 600 żądań / 5 s / IP → z dużym zapasem
    f"{BINANCE}/": 0.2,
    BINANCE_FUNDING: 0.65,  # wspólny limit fundingRate + fundingInfo: 500 / 5 min / IP
    BINANCE_FUNDING_INFO: 0.65,
    **{u: 0.3 for u in BINANCE_KLINE.values()},  # limit 1500 → waga 10; 0,3 s → ≤ 2000 wag/min
}


# ------------------------------------------------------------------ sieć (cienka warstwa)
def _get(url: str, timeout: float = 20.0):
    """GET → JSON; odmawia adresów spoza https (adresy są stałymi modułu, ale pilnujemy i tak)."""
    if not url.startswith("https://"):
        raise ValueError(f"tylko https: {url!r}")
    req = urllib.request.Request(url, headers={"User-Agent": "alpha-pt1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _otworz(url: str, timeout: float) -> bytes:
    """GET → surowe bajty (tylko https)."""
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError(f"tylko https: {url[:80]!r}")
    req = urllib.request.Request(url, headers={"User-Agent": "alpha-pt1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _retry_after_s(err: urllib.error.HTTPError) -> float:
    """
    Nagłówek ``Retry-After`` w sekundach, przycięty do ``[0, RETRY_AFTER_MAX_S]`` (0, gdy brak albo
    nieczytelny) — odpowiedź serwera nie uśpi pobierania na godziny.
    """
    try:
        v = float((err.headers or {}).get("Retry-After") or 0)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(v) else min(max(v, 0.0), RETRY_AFTER_MAX_S)


class BlokadaIP(RuntimeError):
    """
    HTTP 418 (Binance blokuje IP po ignorowaniu 429). Dotyczy wszystkich symboli, więc przerywa CAŁĄ
    komendę: pętle per symbol w ``cmd_*`` przepuszczają go dalej zamiast zapisać jako błąd symbolu.
    """


class Klient:
    """
    GET → JSON z odczekaniem między żądaniami (``pacing``: prefiks adresu → sekundy, najdłuższy
    pasujący wygrywa; zegar per host) i ponowieniem przy HTTP 429/5xx, błędach sieci, ucięciu
    JSON i ``retCode 10006`` Bybit (odczekanie ``backoff_s · 2^próba``, nie krócej niż
    ``Retry-After`` przycięty do ``RETRY_AFTER_MAX_S``). HTTP 418 (blokada IP Binance)
    → ``BlokadaIP`` od razu; pozostałe 4xx → ``HTTPError`` od razu.
    ``otworz``, ``sleep`` i ``zegar`` są podmienialne (testy bez sieci).
    """

    def __init__(
        self,
        otworz: Callable[[str, float], bytes] = _otworz,
        sleep: Callable[[float], None] = time.sleep,
        zegar: Callable[[], float] = time.monotonic,
        pacing: dict[str, float] | None = None,
        proby: int = PROBY,
        backoff_s: float = BACKOFF_S,
        timeout: float = 30.0,
        log: Callable[[str], None] = print,
    ) -> None:
        self._otworz, self._sleep, self._zegar, self._log = otworz, sleep, zegar, log
        self.pacing = dict(PACING_S if pacing is None else pacing)
        self.proby, self.backoff_s, self.timeout = proby, backoff_s, timeout
        self._ostatnio: dict[str, float] = {}
        self.licznik: Counter = Counter()

    def _odstep(self, url: str) -> float:
        pasujace = [p for p in self.pacing if url.startswith(p)]
        return self.pacing[max(pasujace, key=len)] if pasujace else 0.0

    def __call__(self, url: str):
        czesci = urllib.parse.urlsplit(url)
        if czesci.scheme != "https":
            raise ValueError(f"tylko https: {url[:80]!r}")
        host, odstep = czesci.hostname or "", self._odstep(url)
        ostatni: Exception | None = None
        for proba in range(self.proby):
            if host in self._ostatnio:
                brak = odstep - (self._zegar() - self._ostatnio[host])
                if brak > 0:
                    self._sleep(brak)
            self._ostatnio[host] = self._zegar()
            self.licznik["zadania"] += 1
            minimum = 0.0
            try:
                payload = json.loads(self._otworz(url, self.timeout))
            except urllib.error.HTTPError as e:
                if e.code == HTTP_BLOKADA_IP:
                    raise BlokadaIP(
                        f"HTTP 418 — blokada IP ({host}; Retry-After: "
                        f"{(e.headers or {}).get('Retry-After')!r}); komenda przerwana: {url[:120]}"
                    ) from e
                if e.code not in RETRY_HTTP:
                    raise
                ostatni, minimum = e, _retry_after_s(e)
            except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:
                ostatni = e
            else:
                if isinstance(payload, dict) and payload.get("retCode") == BYBIT_RETCODE_LIMIT:
                    ostatni = RuntimeError(f"bybit retCode {BYBIT_RETCODE_LIMIT}: {url[:120]}")
                else:
                    return payload
            if proba + 1 < self.proby:
                czekaj = max(self.backoff_s * 2**proba, minimum)
                self.licznik["ponowienia"] += 1
                self._log(
                    f"[pt1] ponowienie {proba + 1}/{self.proby - 1} za {czekaj:.1f} s: {ostatni!r}"
                )
                self._sleep(czekaj)
        assert ostatni is not None
        raise ostatni


def _url(base: str, **params) -> str:
    """Adres stały modułu + zakodowane parametry (wartości z odpowiedzi serwera tylko jako parametry)."""
    return f"{base}?{urllib.parse.urlencode(params)}" if params else base


# ------------------------------------------------------------------ stronicowanie (czyste)
def _nowe_na_stronie(rekordy: list, czas, zebrane: dict, w_oknie) -> list[tuple[int, object]]:
    """
    Rekordy strony w żądanym oknie (``w_oknie(t)``). Rekord spoza okna jest dozwolony tylko jako
    powtórzenie już zebranego (zakładka stron) i tylko obok nowych rekordów. Serwer ignoruje kursor
    → ``ValueError`` (brak postępu): nieznany rekord spoza okna albo NIEPUSTA strona bez żadnego
    rekordu w oknie (ta sama strona odesłana ponownie — cichy koniec uciąłby historię). Pusta
    strona → pusta lista (koniec historii).
    """
    nowe = []
    for r in rekordy:
        t = czas(r)
        if w_oknie(t):
            nowe.append((t, r))
        elif t not in zebrane:
            raise ValueError(f"stronicowanie: brak postępu (rekord {t} spoza żądanego okna)")
    if rekordy and not nowe:
        raise ValueError(
            f"stronicowanie: brak postępu (strona {len(rekordy)} rekordów bez nowego w oknie — "
            "serwer ignoruje kursor)"
        )
    return nowe


def stronicuj_wstecz(
    strona: Callable[[int], list],
    koniec_ms: int,
    od_ms: int,
    czas: Callable[[object], int],
    max_stron: int = MAX_STRON,
) -> list:
    """
    Stronicowanie WSTECZ (Bybit: lista malejąco, parametr ``end``/``endTime`` włącznie).
    ``strona(end)`` → rekordy z czasem ≤ ``end`` (dowolna kolejność; powtórzenia już zebranych
    rekordów z czasem > ``end`` są pomijane). Następna strona: ``end = min(czas) − 1``. Koniec:
    pusta strona albo ``min(czas) ≤ od_ms``; niepusta strona bez nowego rekordu → ``ValueError``.
    Wynik: bez powtórzeń czasu (pierwsze wystąpienie wygrywa), rosnąco, tylko
    ``od_ms ≤ czas ≤ koniec_ms``.
    """
    zebrane: dict[int, object] = {}
    end = koniec_ms
    for _ in range(max_stron):
        nowe = _nowe_na_stronie(strona(end), czas, zebrane, lambda t, e=end: t <= e)
        if not nowe:
            break
        for t, r in nowe:
            zebrane.setdefault(t, r)
        najstarszy = min(t for t, _ in nowe)
        if najstarszy <= od_ms:
            break
        end = najstarszy - 1
    else:
        raise ValueError(f"stronicowanie wstecz: więcej niż {max_stron} stron")
    return [zebrane[t] for t in sorted(zebrane) if od_ms <= t <= koniec_ms]


def stronicuj_naprzod(
    strona: Callable[[int], list],
    od_ms: int,
    do_ms: int,
    czas: Callable[[object], int],
    max_stron: int = MAX_STRON,
) -> list:
    """
    Stronicowanie NAPRZÓD (Binance: lista rosnąco od ``startTime`` włącznie).
    ``strona(start)`` → rekordy z czasem ≥ ``start`` (powtórzenia już zebranych z czasem < ``start``
    są pomijane). Następna strona: ``start = max(czas) + 1``. Koniec: pusta strona albo
    ``max(czas) ≥ do_ms``; niepusta strona bez nowego rekordu → ``ValueError``. Wynik: bez powtórzeń
    czasu, rosnąco, tylko ``od_ms ≤ czas ≤ do_ms``.
    """
    zebrane: dict[int, object] = {}
    start = od_ms
    for _ in range(max_stron):
        nowe = _nowe_na_stronie(strona(start), czas, zebrane, lambda t, s=start: t >= s)
        if not nowe:
            break
        for t, r in nowe:
            zebrane.setdefault(t, r)
        najmlodszy = max(t for t, _ in nowe)
        if najmlodszy >= do_ms:
            break
        start = najmlodszy + 1
    else:
        raise ValueError(f"stronicowanie naprzód: więcej niż {max_stron} stron")
    return [zebrane[t] for t in sorted(zebrane) if od_ms <= t <= do_ms]


# ------------------------------------------------------------------ parsery (czyste)
def _ms(x) -> int:
    """Znacznik czasu w ms (int albo tekst cyfr) z kontrolą zakresu 2015–2100."""
    if isinstance(x, bool):
        raise ValueError(f"czas: zły typ {x!r}")
    v = int(x)
    if not MIN_MS <= v <= MAX_MS:
        raise ValueError(f"czas poza zakresem: {x!r}")
    return v


def _liczba(x) -> float:
    """Liczba skończona z tekstu/liczby; ``ValueError`` przy braku, NaN albo nieskończoności."""
    if isinstance(x, bool) or x is None or x == "":
        raise ValueError(f"liczba: brak/zły typ {x!r}")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"liczba nieskończona: {x!r}")
    return v


def _liczba_lub_nan(x) -> float:
    try:
        return _liczba(x)
    except (TypeError, ValueError):
        return float("nan")


def _wynik_bybit(payload) -> dict:
    """Odpowiedź Bybit v5 → ``result`` (``retCode == 0`` i lista ``result.list``), inaczej ``ValueError``."""
    if not isinstance(payload, dict) or payload.get("retCode") != 0:
        raise ValueError(f"bybit: odpowiedź z błędem: {str(payload)[:200]}")
    res = payload.get("result")
    if not isinstance(res, dict) or not isinstance(res.get("list"), list):
        raise ValueError(f"bybit: brak result.list: {str(payload)[:200]}")
    return res


def klasa_bybit(symbol: str, symbol_type: str, baza: str) -> str:
    """Klasa PT1 z ``symbolType`` Bybit (ETF obligacyjne TLT/TBT/TMF osobno)."""
    if symbol == KONTROLA:
        return "BTC_kontrola"
    if symbol_type == "forex":
        return "waluty"
    if symbol_type == "commodity":
        return "surowce"
    if symbol_type == "ETF":
        return "ETF_oblig" if baza in ETF_OBLIG else "ETF"
    if symbol_type == "stock":
        return "akcje"
    return "inne"


def klasa_binance(
    symbol: str, underlying_type: str, baza: str, bybit_etf: frozenset = frozenset()
) -> tuple[str, str]:
    """
    Klasa PT1 z ``underlyingType`` Binance → (klasa, źródło reguły). Akcje (EQUITY, HK/KR/CN_EQUITY)
    są ETF-em, gdy baza jest na liście ``ETF_RDZEN`` albo ten sam symbol ma na Bybit ``symbolType = ETF``.
    """
    if symbol == KONTROLA:
        return "BTC_kontrola", "kontrola"
    if underlying_type == "FX":
        return "waluty", "underlyingType"
    if underlying_type == "COMMODITY":
        return "surowce", "underlyingType"
    if underlying_type == "PREMARKET":
        return "przed_IPO", "underlyingType"
    if underlying_type in BINANCE_REGION:
        if baza in ETF_OBLIG:
            return "ETF_oblig", "lista ETF"
        if baza in ETF_RDZEN:
            return "ETF", "lista ETF"
        if symbol in bybit_etf:
            return "ETF", "Bybit symbolType=ETF"
        return "akcje", "underlyingType"
    return "inne", "underlyingType"


def parsuj_spis_bybit(strony: list) -> pd.DataFrame:
    """Strony ``instruments-info`` → spis TradFi + BTCUSDT (jeden wiersz na symbol)."""
    wiersze = {}
    for payload in strony:
        for r in _wynik_bybit(payload)["list"]:
            if not isinstance(r, dict) or not isinstance(r.get("symbol"), str):
                raise ValueError(f"bybit spis: zły rekord {str(r)[:120]}")
            if r["symbol"] != KONTROLA and r.get("symbolType") not in BYBIT_TRADFI_TYPES:
                continue
            baza = str(r.get("baseCoin", ""))
            lev = r.get("leverageFilter") if isinstance(r.get("leverageFilter"), dict) else {}
            cena = r.get("priceFilter") if isinstance(r.get("priceFilter"), dict) else {}
            wiersze[r["symbol"]] = {
                "symbol": r["symbol"],
                "baza": baza,
                "symbolType": str(r.get("symbolType", "")),
                "region": str(r.get("marketRegion", "")),
                "nazwa": str(r.get("fullName", "")),
                "status": str(r.get("status", "")),
                "start": pd.to_datetime(_ms(r["launchTime"]), unit="ms", utc=True),
                "interwal_h": _liczba(r["fundingInterval"]) / 60.0,
                "cap": _liczba_lub_nan(r.get("upperFundingRate")),
                "floor": _liczba_lub_nan(r.get("lowerFundingRate")),
                "max_dzwignia": _liczba_lub_nan(lev.get("maxLeverage")),
                "tick": _liczba_lub_nan(cena.get("tickSize")),
                "klasa": klasa_bybit(r["symbol"], str(r.get("symbolType", "")), baza),
                "klasa_zrodlo": "symbolType",
                "surowe": json.dumps(r, sort_keys=True),
            }
    if not wiersze:
        raise ValueError("bybit spis: brak instrumentów TradFi")
    return pd.DataFrame(sorted(wiersze.values(), key=lambda w: w["symbol"]))


def parsuj_spis_binance(info, funding_info, bybit_etf: frozenset = frozenset()) -> pd.DataFrame:
    """``exchangeInfo`` + ``fundingInfo`` → spis TradFi + BTCUSDT. Brak w ``fundingInfo`` → 8 h (domyślny)."""
    if not isinstance(info, dict) or not isinstance(info.get("symbols"), list):
        raise ValueError(f"binance spis: brak `symbols`: {str(info)[:200]}")
    if not isinstance(funding_info, list):
        raise ValueError(f"binance fundingInfo: oczekiwano listy: {str(funding_info)[:200]}")
    fi = {f["symbol"]: f for f in funding_info if isinstance(f, dict) and "symbol" in f}
    wiersze = {}
    for s in info["symbols"]:
        if not isinstance(s, dict) or not isinstance(s.get("symbol"), str):
            raise ValueError(f"binance spis: zły rekord {str(s)[:120]}")
        if s["symbol"] != KONTROLA and s.get("contractType") != BINANCE_TRADFI:
            continue
        baza, ut = str(s.get("baseAsset", "")), str(s.get("underlyingType", ""))
        klasa, zrodlo = klasa_binance(s["symbol"], ut, baza, bybit_etf)
        f = fi.get(s["symbol"], {})
        tick = next(
            (
                x.get("tickSize")
                for x in s.get("filters", [])
                if x.get("filterType") == "PRICE_FILTER"
            ),
            None,
        )
        sub = s.get("underlyingSubType")
        wiersze[s["symbol"]] = {
            "symbol": s["symbol"],
            "pair": str(s.get("pair", s["symbol"])),
            "baza": baza,
            "underlyingType": ut,
            "underlyingSubType": (
                ",".join(map(str, sub)) if isinstance(sub, list) else str(sub or "")
            ),
            "region": BINANCE_REGION.get(ut, ""),
            "status": str(s.get("status", "")),
            "start": pd.to_datetime(_ms(s["onboardDate"]), unit="ms", utc=True),
            "interwal_h": float(f.get("fundingIntervalHours", 8)),
            "interwal_zrodlo": "fundingInfo" if f else "domyślny 8 h",
            "cap": _liczba_lub_nan(f.get("adjustedFundingRateCap")),
            "floor": _liczba_lub_nan(f.get("adjustedFundingRateFloor")),
            "max_dzwignia": float("nan"),  # tylko leverageBracket z kluczem API
            "tick": _liczba_lub_nan(tick),
            "klasa": klasa,
            "klasa_zrodlo": zrodlo,
            "surowe": json.dumps(s, sort_keys=True),
        }
    if not wiersze:
        raise ValueError("binance spis: brak instrumentów TradFi")
    return pd.DataFrame(sorted(wiersze.values(), key=lambda w: w["symbol"]))


def parsuj_funding_bybit(rows, symbol: str) -> list[dict]:
    """``funding/history`` ``result.list`` → rekordy {symbol, czas_ms, fundingRate}; zły rekord = błąd."""
    out = []
    for r in rows:
        if not isinstance(r, dict) or r.get("symbol") != symbol:
            raise ValueError(f"bybit funding: zły rekord dla {symbol}: {str(r)[:120]}")
        out.append(
            {
                "symbol": symbol,
                "czas_ms": _ms(r["fundingRateTimestamp"]),
                "fundingRate": _liczba(r["fundingRate"]),
            }
        )
    return out


def parsuj_funding_binance(rows, symbol: str) -> list[dict]:
    """``fundingRate`` → rekordy {symbol, czas_ms, fundingRate, markPrice}; zły rekord = błąd."""
    if not isinstance(rows, list):
        raise ValueError(f"binance funding: oczekiwano listy dla {symbol}: {str(rows)[:200]}")
    out = []
    for r in rows:
        if not isinstance(r, dict) or r.get("symbol") != symbol:
            raise ValueError(f"binance funding: zły rekord dla {symbol}: {str(r)[:120]}")
        out.append(
            {
                "symbol": symbol,
                "czas_ms": _ms(r["fundingTime"]),
                "fundingRate": _liczba(r["fundingRate"]),
                "markPrice": _liczba_lub_nan(r.get("markPrice")),
            }
        )
    return out


def parsuj_kline_bybit(rows, symbol: str) -> list[dict]:
    """Świece Bybit ``[start, o, h, l, c, (volume, turnover)]`` (teksty) → rekordy."""
    out = []
    for r in rows:
        if not isinstance(r, list) or len(r) < 5:
            raise ValueError(f"bybit kline: zły wiersz dla {symbol}: {str(r)[:120]}")
        rec = {"symbol": symbol, "czas_ms": _ms(r[0])}
        rec.update(zip(("open", "high", "low", "close"), map(_liczba, r[1:5]), strict=True))
        if len(r) >= 7:
            rec["volume"], rec["turnover"] = _liczba(r[5]), _liczba(r[6])
        out.append(rec)
    return out


def parsuj_kline_binance(rows, symbol: str) -> list[dict]:
    """Świece Binance ``[open_time, o, h, l, c, volume, close_time, quote_volume, count, …]`` → rekordy."""
    if not isinstance(rows, list):
        raise ValueError(f"binance kline: oczekiwano listy dla {symbol}: {str(rows)[:200]}")
    out = []
    for r in rows:
        if not isinstance(r, list) or len(r) < 9:
            raise ValueError(f"binance kline: zły wiersz dla {symbol}: {str(r)[:120]}")
        rec = {"symbol": symbol, "czas_ms": _ms(r[0])}
        rec.update(zip(("open", "high", "low", "close"), map(_liczba, r[1:5]), strict=True))
        rec["volume"], rec["turnover"], rec["n"] = _liczba(r[5]), _liczba(r[7]), _liczba(r[8])
        out.append(rec)
    return out


def do_ramki(rekordy: list[dict], kolumny: tuple[str, ...]) -> pd.DataFrame:
    """Rekordy z ``czas_ms`` → ramka (``czas`` UTC ms), posortowana po (symbol, czas), bez powtórzeń."""
    df = pd.DataFrame(rekordy, columns=["symbol", "czas_ms", *kolumny])
    df.insert(1, "czas", pd.to_datetime(df.pop("czas_ms"), unit="ms", utc=True))
    df = df.drop_duplicates(["symbol", "czas"], keep="first")
    return df.sort_values(["symbol", "czas"]).reset_index(drop=True)


# ------------------------------------------------------------------ pobieranie (get podmienialny)
def sprawdz_migawke(rec: dict) -> None:
    """
    Treść migawki (klucze ``MIGAWKA_URLS``): Bybit — ``retCode == 0`` i lista ``result.list``,
    Binance — lista; elementy list to rekordy (słowniki). Zła treść (błąd limitu w odpowiedzi
    HTTP 200, słownik błędu Binance zamiast listy) → ``ValueError``.
    """
    for key in MIGAWKA_URLS:
        payload = rec.get(key)
        if key.startswith("bybit_"):
            try:
                lista = _wynik_bybit(payload)["list"]
            except ValueError as exc:
                raise ValueError(f"migawka {key}: {exc}") from exc
        elif isinstance(payload, list):
            lista = payload
        else:
            raise ValueError(f"migawka {key}: oczekiwano listy: {str(payload)[:200]}")
        if not all(isinstance(r, dict) for r in lista):
            raise ValueError(f"migawka {key}: element listy nie jest rekordem: {str(lista)[:200]}")


def migawka(out_dir: Path = OUT / "migawki", now: dt.datetime | None = None, get=_get) -> Path:
    """
    Jedna migawka: wszystkie odpowiedzi z ``MIGAWKA_URLS`` w jednym pliku ``<czas UTC>.json.gz``.
    Zła treść → ``ValueError`` przed zapisem; zapis do ``.tmp`` + ``os.replace`` (błąd w trakcie
    zapisu nie zostawia pliku docelowego ani ``.tmp``).
    """
    now = now or dt.datetime.now(dt.UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    rec = {"czas_utc": now.isoformat()}
    for key, url in MIGAWKA_URLS.items():
        rec[key] = get(url)
    sprawdz_migawke(rec)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stamp}.json.gz"
    tmp = path.with_name(f"{path.name}.tmp")  # nie pasuje do wzorca *.json.gz czytników
    try:
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(rec, fh)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)  # po udanym os.replace pliku .tmp już nie ma
    return path


def petla_migawek(co_s: int, do_utc: dt.datetime, out_dir: Path = OUT / "migawki") -> int:
    """Migawka co ``co_s`` sekund do ``do_utc``; błąd jednej migawki nie przerywa pętli. Zwraca liczbę udanych."""
    ok = 0
    while dt.datetime.now(dt.UTC) < do_utc:
        try:
            print(migawka(out_dir), flush=True)
            ok += 1
        except Exception as exc:  # noqa: BLE001 — sieć: zapisz i próbuj dalej
            print(f"BŁĄD migawki: {exc!r}", flush=True)
        time.sleep(co_s)
    return ok


def pobierz_spis_bybit(get, max_stron: int = 50) -> pd.DataFrame:
    """Wszystkie strony ``instruments-info`` (kursor) → ``parsuj_spis_bybit``."""
    strony, kursor = [], ""
    for _ in range(max_stron):
        params = {"category": "linear", "limit": "1000"}
        if kursor:
            params["cursor"] = kursor
        payload = get(_url(BYBIT_INSTR, **params))
        strony.append(payload)
        kursor = _wynik_bybit(payload).get("nextPageCursor") or ""
        if not isinstance(kursor, str) or not kursor:
            break
    else:
        raise ValueError(f"bybit spis: więcej niż {max_stron} stron")
    return parsuj_spis_bybit(strony)


def pobierz_spis_binance(get, bybit_etf: frozenset = frozenset()) -> pd.DataFrame:
    return parsuj_spis_binance(get(BINANCE_INFO), get(BINANCE_FUNDING_INFO), bybit_etf)


def pobierz_funding_bybit(get, symbol: str, od_ms: int, do_ms: int) -> list[dict]:
    def strona(end: int) -> list[dict]:
        url = _url(
            BYBIT_FUNDING, category="linear", symbol=symbol, endTime=end, limit=BYBIT_FUNDING_LIMIT
        )
        return parsuj_funding_bybit(_wynik_bybit(get(url))["list"], symbol)

    return stronicuj_wstecz(strona, do_ms, od_ms, czas=lambda r: r["czas_ms"])


def pobierz_funding_binance(get, symbol: str, od_ms: int, do_ms: int) -> list[dict]:
    def strona(start: int) -> list[dict]:
        url = _url(BINANCE_FUNDING, symbol=symbol, startTime=start, limit=BINANCE_FUNDING_LIMIT)
        return parsuj_funding_binance(get(url), symbol)

    return stronicuj_naprzod(strona, od_ms, do_ms, czas=lambda r: r["czas_ms"])


def pobierz_swiece_bybit(
    get, symbol: str, rodzaj: str, od_ms: int, do_ms: int, interwal: str = "60"
) -> list[dict]:
    """Świece Bybit (``rodzaj`` ∈ last/index/mark/premia) z ``[od_ms, do_ms]`` — stronicowanie wstecz."""
    base = BYBIT_KLINE[rodzaj]

    def strona(end: int) -> list[dict]:
        url = _url(
            base,
            category="linear",
            symbol=symbol,
            interval=interwal,
            end=end,
            limit=BYBIT_KLINE_LIMIT,
        )
        return parsuj_kline_bybit(_wynik_bybit(get(url))["list"], symbol)

    return stronicuj_wstecz(strona, do_ms, od_ms, czas=lambda r: r["czas_ms"])


def pobierz_swiece_binance(
    get, symbol: str, pair: str, rodzaj: str, od_ms: int, do_ms: int
) -> list[dict]:
    """Świece 1 h Binance (``rodzaj`` ∈ last/index/mark; indeks po ``pair``) — stronicowanie naprzód."""
    base = BINANCE_KLINE[rodzaj]
    klucz = {"pair": pair} if rodzaj == "index" else {"symbol": symbol}

    def strona(start: int) -> list[dict]:
        url = _url(base, **klucz, interval="1h", startTime=start, limit=BINANCE_KLINE_LIMIT)
        return parsuj_kline_binance(get(url), symbol)

    return stronicuj_naprzod(strona, od_ms, do_ms, czas=lambda r: r["czas_ms"])


# ------------------------------------------------------------------ rdzeń rundy (czyste)
def obroty_migawki(sciezka: Path) -> dict[str, dict[str, float]]:
    """Obrót 24 h (USDT) z migawki: Bybit ``turnover24h``, Binance ``quoteVolume``."""
    with gzip.open(sciezka, "rt", encoding="utf-8") as fh:
        d = json.load(fh)
    bybit = {
        r["symbol"]: _liczba_lub_nan(r.get("turnover24h"))
        for r in _wynik_bybit(d["bybit_tickers"])["list"]
    }
    binance = {r["symbol"]: _liczba_lub_nan(r.get("quoteVolume")) for r in d["binance_24h"]}
    return {"bybit": bybit, "binance": binance}


def wybierz_rdzen(
    spis: pd.DataFrame, obrot: dict[str, float], n_akcji: int = N_AKCJI_RDZEN
) -> list[str]:
    """
    Rdzeń PT1 (reguła pre-rejestracji): wszystkie waluty i surowce + ETF-y z ``ETF_RDZEN`` obecne na
    giełdzie + ``n_akcji`` akcji USA (klasa akcje, region US) o największym obrocie 24 h + BTCUSDT.
    Brak obrotu (NaN) → akcja poza wyborem. Wynik posortowany.
    """
    wybor = set(spis.loc[spis["klasa"].isin(["waluty", "surowce"]), "symbol"])
    wybor |= set(
        spis.loc[spis["klasa"].isin(["ETF", "ETF_oblig"]) & spis["baza"].isin(ETF_RDZEN), "symbol"]
    )
    akcje = spis.loc[(spis["klasa"] == "akcje") & (spis["region"] == "US"), "symbol"]
    ranking = sorted(
        ((obrot.get(s, float("nan")), s) for s in akcje),
        key=lambda x: (-x[0] if math.isfinite(x[0]) else math.inf, x[1]),
    )
    wybor |= {s for v, s in ranking[:n_akcji] if math.isfinite(v)}
    if KONTROLA in set(spis["symbol"]):
        wybor.add(KONTROLA)
    return sorted(wybor)


# ------------------------------------------------------------------ komendy
def _teraz_ms() -> int:
    return int(time.time() * 1000)


def _od_ms(data: str) -> int:
    return int(pd.Timestamp(data, tz="UTC").value // 1_000_000)


def _zapisz(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def cmd_spis(get, out: Path = OUT) -> tuple[Path, Path]:
    bybit = pobierz_spis_bybit(get)
    etf = frozenset(bybit.loc[bybit["symbolType"] == "ETF", "symbol"])
    binance = pobierz_spis_binance(get, etf)
    for nazwa, df in (("bybit", bybit), ("binance", binance)):
        licz = df.groupby("klasa").size().to_dict()
        print(f"[pt1] spis {nazwa}: {len(df)} instrumentów {licz}")
    return _zapisz(bybit, out / "spis_bybit.parquet"), _zapisz(
        binance, out / "spis_binance.parquet"
    )


def _wczytaj_spis(out: Path, gielda: str) -> pd.DataFrame:
    path = out / f"spis_{gielda}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"brak {path} — najpierw `spis`")
    return pd.read_parquet(path)


def cmd_funding(get, out: Path = OUT, od: str = FUNDING_OD, do_ms: int | None = None) -> list[Path]:
    """Funding wszystkich instrumentów spisu obu giełd od ``od``; błąd symbolu nie przerywa reszty."""
    od_ms, do_ms = _od_ms(od), do_ms or _teraz_ms()
    sciezki = []
    for gielda, pobierz, kolumny in (
        ("bybit", pobierz_funding_bybit, ("fundingRate",)),
        ("binance", pobierz_funding_binance, ("fundingRate", "markPrice")),
    ):
        rekordy, bledy = [], []
        for symbol in _wczytaj_spis(out, gielda)["symbol"]:
            try:
                rekordy += pobierz(get, symbol, od_ms, do_ms)
            except BlokadaIP:
                raise  # blokada IP dotyczy wszystkich symboli — przerwij całą komendę
            except Exception as exc:  # noqa: BLE001 — jeden symbol nie zatrzymuje spisu
                bledy.append(symbol)
                print(f"[pt1] BŁĄD funding {gielda} {symbol}: {exc!r}")
        df = do_ramki(rekordy, kolumny)
        print(
            f"[pt1] funding {gielda}: {len(df)} odczytów, {df['symbol'].nunique()} symboli, "
            f"błędy: {bledy or 'brak'}"
        )
        sciezki.append(_zapisz(df, out / f"funding_{gielda}.parquet"))
    return sciezki


def cmd_swiece(get, out: Path = OUT, do_ms: int | None = None) -> list[Path]:
    """Świece 1 h (last/index/mark) rdzenia; rdzeń z PIERWSZEJ migawki zapisany w ``rdzen.json``."""
    teraz = do_ms or _teraz_ms()
    ostatnia_pelna = (teraz // HOUR_MS) * HOUR_MS - HOUR_MS  # otwarcie ostatniej zamkniętej świecy
    migawki = sorted((out / "migawki").glob("*.json.gz"))
    if not migawki:
        raise FileNotFoundError("brak migawek — rdzeń wymaga pierwszej migawki")
    obroty = obroty_migawki(migawki[0])
    rdzen: dict = {"migawka": migawki[0].name}
    sciezki = []
    for gielda in ("bybit", "binance"):
        spis = _wczytaj_spis(out, gielda).set_index("symbol", drop=False)
        symbole = wybierz_rdzen(spis.reset_index(drop=True), obroty[gielda])
        akcje = spis.loc[symbole].query("klasa == 'akcje'")["symbol"]
        rdzen[gielda] = symbole
        rdzen[f"{gielda}_akcje_obrot24h"] = {s: obroty[gielda].get(s) for s in akcje}
        print(f"[pt1] rdzeń {gielda} ({len(symbole)}): {symbole}")
        for rodzaj in RODZAJE:
            rekordy, bledy = [], []
            for symbol in symbole:
                w = spis.loc[symbol]
                od_ms = int(pd.Timestamp(w["start"]).value // 1_000_000)
                if symbol == KONTROLA:
                    od_ms = _od_ms(FUNDING_OD)
                od_ms = (od_ms // HOUR_MS) * HOUR_MS
                try:
                    if gielda == "bybit":
                        rekordy += pobierz_swiece_bybit(get, symbol, rodzaj, od_ms, ostatnia_pelna)
                    else:
                        rekordy += pobierz_swiece_binance(
                            get, symbol, str(w["pair"]), rodzaj, od_ms, ostatnia_pelna
                        )
                except BlokadaIP:
                    raise  # blokada IP dotyczy wszystkich symboli — przerwij całą komendę
                except Exception as exc:  # noqa: BLE001
                    bledy.append(symbol)
                    print(f"[pt1] BŁĄD świece {gielda} {rodzaj} {symbol}: {exc!r}")
            kol = ("open", "high", "low", "close", "volume", "turnover")
            if gielda == "binance":
                kol = (*kol, "n")
            df = do_ramki(rekordy, kol)
            print(f"[pt1] świece {gielda} {rodzaj}: {len(df)} godzin, błędy: {bledy or 'brak'}")
            sciezki.append(_zapisz(df, out / f"swiece_{gielda}_{rodzaj}_1h.parquet"))
    (out / "rdzen.json").write_text(
        json.dumps(rdzen, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return sciezki


def cmd_premia(get, out: Path = OUT, dni: int = PREMIA_DNI, do_ms: int | None = None) -> Path:
    """Minutowy indeks premii Bybit dla ``PREMIA_SYMBOLE`` z ostatnich ``dni`` dni (pełne minuty)."""
    teraz = do_ms or _teraz_ms()
    koniec = (teraz // MINUTE_MS) * MINUTE_MS - MINUTE_MS
    od_ms = koniec - dni * 24 * HOUR_MS
    rekordy = []
    for symbol in PREMIA_SYMBOLE:
        r = pobierz_swiece_bybit(get, symbol, "premia", od_ms, koniec, interwal="1")
        print(f"[pt1] premia {symbol}: {len(r)} minut")
        rekordy += r
    return _zapisz(
        do_ramki(rekordy, ("open", "high", "low", "close")), out / "premia_bybit_1m.parquet"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("migawka", help="migawka tickerów (raz albo w pętli)")
    m.add_argument("--co", type=int, default=0, help="odstęp pętli w sekundach (0 = jedna migawka)")
    m.add_argument("--do", default="", help="koniec pętli, czas UTC ISO, np. 2026-09-29T00:00")
    sub.add_parser("spis", help="spis instrumentów TradFi obu giełd + BTCUSDT")
    f = sub.add_parser("funding", help="historia fundingu całego spisu")
    f.add_argument("--od", default=FUNDING_OD, help="początek okna (UTC), domyślnie %(default)s")
    sub.add_parser("swiece", help="świece 1 h (cena, indeks, mark) rdzenia")
    p = sub.add_parser("premia", help="minutowy indeks premii Bybit (druga droga P2)")
    p.add_argument("--dni", type=int, default=PREMIA_DNI)
    args = ap.parse_args(argv)
    if args.cmd == "migawka":
        if args.co <= 0:
            print(migawka())
            return 0
        do_utc = dt.datetime.fromisoformat(args.do).replace(tzinfo=dt.UTC)
        return 0 if petla_migawek(args.co, do_utc) > 0 else 1
    klient = Klient()
    if args.cmd == "spis":
        cmd_spis(klient)
    elif args.cmd == "funding":
        cmd_funding(klient, od=args.od)
    elif args.cmd == "swiece":
        cmd_swiece(klient)
    elif args.cmd == "premia":
        cmd_premia(klient, dni=args.dni)
    print(f"[pt1] żądania: {dict(klient.licznik)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
