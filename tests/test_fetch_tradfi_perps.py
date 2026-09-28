"""Testy data/fetch_tradfi_perps.py (runda PT1) — bez sieci: fałszywe `get`/`otworz`, zegar i uśpienie."""

from __future__ import annotations

import datetime as dt
import email.message
import gzip
import itertools
import json
import urllib.error
import urllib.parse

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data import fetch_tradfi_perps as ft

T0 = 1_780_000_000_000  # 2026-05-28, w zakresie _ms


# ------------------------------------------------------------------ https i ponowienia
def _http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    hdrs = email.message.Message()
    if retry_after is not None:
        hdrs["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://x", code, "err", hdrs, None)


class FalszywyOtworz:
    """Kolejka odpowiedzi: bajty albo wyjątek; zapisuje wywołane adresy."""

    def __init__(self, odpowiedzi):
        self.odpowiedzi = list(odpowiedzi)
        self.adresy: list[str] = []

    def __call__(self, url, timeout):
        self.adresy.append(url)
        o = self.odpowiedzi.pop(0)
        if isinstance(o, Exception):
            raise o
        return o


def _klient(otworz, **kw):
    sleeps: list[float] = []
    zegar = itertools.count(0.0, 10.0)  # każdy odczyt zegara +10 s → pacing nigdy nie czeka
    k = ft.Klient(
        otworz=otworz,
        sleep=sleeps.append,
        zegar=lambda: next(zegar),
        log=lambda _m: None,
        **kw,
    )
    return k, sleeps


@pytest.mark.parametrize("url", ["http://api.bybit.com/x", "ftp://x/y", "file:///etc/passwd"])
def test_non_https_rejected_everywhere(url):
    with pytest.raises(ValueError, match="https"):
        ft._get(url)
    with pytest.raises(ValueError, match="https"):
        ft._otworz(url, 1.0)
    otworz = FalszywyOtworz([b"{}"])
    k, _ = _klient(otworz)
    with pytest.raises(ValueError, match="https"):
        k(url)
    assert otworz.adresy == []  # odmowa PRZED jakimkolwiek połączeniem


def test_klient_retries_429_respecting_retry_after():
    otworz = FalszywyOtworz([_http_error(429, "7"), b'{"ok": 1}'])
    k, sleeps = _klient(otworz, backoff_s=1.0)
    assert k("https://fapi.binance.com/fapi/v1/klines?symbol=X") == {"ok": 1}
    assert len(otworz.adresy) == 2
    assert max(sleeps) >= 7.0  # nie krócej niż Retry-After
    assert k.licznik["ponowienia"] == 1


@pytest.mark.parametrize("blad", [_http_error(503), urllib.error.URLError("reset"), TimeoutError()])
def test_klient_retries_5xx_and_network_errors(blad):
    otworz = FalszywyOtworz([blad, b"[1, 2]"])
    k, sleeps = _klient(otworz, backoff_s=0.5)
    assert k("https://api.bybit.com/v5/market/kline") == [1, 2]
    assert sleeps == [0.5]


def test_klient_retries_bybit_rate_limit_retcode():
    otworz = FalszywyOtworz([b'{"retCode": 10006, "retMsg": "Too many visits"}', b'{"retCode": 0}'])
    k, _ = _klient(otworz)
    assert k("https://api.bybit.com/v5/market/kline") == {"retCode": 0}
    assert len(otworz.adresy) == 2


@pytest.mark.parametrize("code", [400, 403, 404, 418])
def test_klient_does_not_retry_other_4xx(code):
    otworz = FalszywyOtworz([_http_error(code), b"{}"])
    k, sleeps = _klient(otworz)
    with pytest.raises(urllib.error.HTTPError):
        k("https://fapi.binance.com/fapi/v1/klines")
    assert len(otworz.adresy) == 1 and sleeps == []


def test_klient_gives_up_after_all_attempts():
    otworz = FalszywyOtworz([_http_error(502)] * 3)
    k, sleeps = _klient(otworz, proby=3, backoff_s=1.0)
    with pytest.raises(urllib.error.HTTPError):
        k("https://api.bybit.com/v5/market/kline")
    assert len(otworz.adresy) == 3
    assert sleeps == [1.0, 2.0]  # wykładniczo, bez uśpienia po ostatniej próbie


def test_klient_pacing_uses_longest_prefix_per_host():
    sleeps: list[float] = []
    teraz = [0.0]
    k = ft.Klient(
        otworz=lambda url, t: b"{}",
        sleep=lambda s: (sleeps.append(s), teraz.__setitem__(0, teraz[0] + s)),
        zegar=lambda: teraz[0],
        log=lambda _m: None,
    )
    k(ft.BINANCE_FUNDING + "?symbol=A")
    k(ft.BINANCE_FUNDING + "?symbol=B")
    assert sleeps == [pytest.approx(ft.PACING_S[ft.BINANCE_FUNDING])]
    k("https://api.bybit.com/v5/market/kline")  # inny host: bez czekania
    assert len(sleeps) == 1


# ------------------------------------------------------------------ stronicowanie (właściwości)
def _serwer_wstecz(czasy, rozmiary, zakladka):
    """Bybit: rekordy z czasem ≤ end, malejąco; rozmiary stron z cyklu; + do `zakladka` JUŻ WYSŁANYCH
    rekordów z czasem > end (powtórzona granica strony)."""
    malejaco = sorted(czasy, reverse=True)
    cykl = itertools.cycle(rozmiary)
    wyslane: set[int] = set()

    def strona(end):
        pod = [t for t in malejaco if t <= end][: next(cykl)]
        nad = sorted(t for t in wyslane if t > end)[:zakladka]
        wyslane.update(pod)
        return [{"t": t} for t in sorted(nad + pod, reverse=True)]

    return strona


def _serwer_naprzod(czasy, rozmiary, zakladka):
    """Binance: rekordy z czasem ≥ start, rosnąco; + do `zakladka` już wysłanych z czasem < start."""
    rosnaco = sorted(czasy)
    cykl = itertools.cycle(rozmiary)
    wyslane: set[int] = set()

    def strona(start):
        nad = [t for t in rosnaco if t >= start][: next(cykl)]
        pod = sorted((t for t in wyslane if t < start), reverse=True)[:zakladka]
        wyslane.update(nad)
        return [{"t": t} for t in sorted(pod + nad)]

    return strona


_czasy = st.sets(st.integers(T0, T0 + 5_000), max_size=120)
_rozmiary = st.lists(st.integers(1, 40), min_size=1, max_size=8)


@settings(max_examples=150, deadline=None)
@given(
    _czasy, _rozmiary, st.integers(0, 3), st.integers(T0 - 10, T0 + 5_010), st.integers(0, 5_020)
)
def test_backward_paging_no_duplicates_no_gaps_sorted(czasy, rozmiary, zakladka, od, dlugosc):
    koniec = od + dlugosc
    wynik = ft.stronicuj_wstecz(
        _serwer_wstecz(czasy, rozmiary, zakladka), koniec, od, lambda r: r["t"]
    )
    t = [r["t"] for r in wynik]
    assert t == sorted(x for x in czasy if od <= x <= koniec)  # komplet, rosnąco, bez powtórzeń


@settings(max_examples=150, deadline=None)
@given(
    _czasy, _rozmiary, st.integers(0, 3), st.integers(T0 - 10, T0 + 5_010), st.integers(0, 5_020)
)
def test_forward_paging_no_duplicates_no_gaps_sorted(czasy, rozmiary, zakladka, od, dlugosc):
    do = od + dlugosc
    wynik = ft.stronicuj_naprzod(
        _serwer_naprzod(czasy, rozmiary, zakladka), od, do, lambda r: r["t"]
    )
    t = [r["t"] for r in wynik]
    assert t == sorted(x for x in czasy if od <= x <= do)


def test_paging_detects_server_ignoring_cursor():
    stala = [{"t": T0 + 100}]  # nieznany rekord spoza żądanego okna
    with pytest.raises(ValueError, match="brak postępu"):
        ft.stronicuj_wstecz(lambda end: stala, T0 + 50, T0, lambda r: r["t"])
    with pytest.raises(ValueError, match="brak postępu"):
        ft.stronicuj_naprzod(lambda start: [{"t": T0}], T0 + 50, T0 + 100, lambda r: r["t"])


def test_paging_page_limit_guard():
    with pytest.raises(ValueError, match="więcej niż 3 stron"):
        ft.stronicuj_wstecz(lambda end: [{"t": end}], T0 + 10, T0, lambda r: r["t"], max_stron=3)


# ------------------------------------------------------------------ parsery
def test_wynik_bybit_rejects_error_payloads():
    for zly in ({"retCode": 10001, "retMsg": "params error"}, {"retCode": 0}, [], None):
        with pytest.raises(ValueError, match="bybit"):
            ft._wynik_bybit(zly)


def test_parse_funding_bybit_and_binance():
    by = ft.parsuj_funding_bybit(
        [{"symbol": "XAUUSDT", "fundingRate": "0.00032007", "fundingRateTimestamp": str(T0)}],
        "XAUUSDT",
    )
    assert by == [{"symbol": "XAUUSDT", "czas_ms": T0, "fundingRate": pytest.approx(0.00032007)}]
    bn = ft.parsuj_funding_binance(
        [
            {
                "symbol": "XAUUSDT",
                "fundingTime": T0 + 1,
                "fundingRate": "-0.0001",
                "markPrice": "4219.9",
            }
        ],
        "XAUUSDT",
    )
    assert bn[0]["czas_ms"] == T0 + 1 and bn[0]["fundingRate"] == pytest.approx(-0.0001)
    with pytest.raises(ValueError, match="zły rekord"):
        ft.parsuj_funding_bybit(
            [{"symbol": "OTHER", "fundingRate": "0", "fundingRateTimestamp": T0}], "X"
        )
    with pytest.raises(ValueError):
        ft.parsuj_funding_binance([{"symbol": "X", "fundingTime": T0, "fundingRate": "nan"}], "X")
    with pytest.raises(ValueError, match="poza zakresem"):
        ft.parsuj_funding_bybit(
            [{"symbol": "X", "fundingRate": "0", "fundingRateTimestamp": "5"}], "X"
        )


def test_parse_klines_both_exchanges():
    by = ft.parsuj_kline_bybit([[str(T0), "1.1", "1.2", "1.0", "1.15", "10", "11.5"]], "EURUSDUSDT")
    assert by[0] == {
        "symbol": "EURUSDUSDT",
        "czas_ms": T0,
        "open": 1.1,
        "high": 1.2,
        "low": 1.0,
        "close": 1.15,
        "volume": 10.0,
        "turnover": 11.5,
    }
    idx = ft.parsuj_kline_bybit([[str(T0), "1", "2", "0.5", "1.5"]], "X")  # indeks: bez wolumenu
    assert "volume" not in idx[0] and idx[0]["close"] == 1.5
    bn = ft.parsuj_kline_binance(
        [
            [
                T0,
                "4135.08",
                "4151.06",
                "4131.37",
                "4139.82",
                "3.5",
                T0 + 3_599_999,
                "142.1",
                3600,
                "0",
            ]
        ],
        "XAUUSDT",
    )
    assert bn[0]["close"] == pytest.approx(4139.82) and bn[0]["n"] == 3600
    with pytest.raises(ValueError, match="zły wiersz"):
        ft.parsuj_kline_bybit([[str(T0), "1"]], "X")


def _bybit_instr(symbol, stype, base, region="US", interval=480, launch=T0):
    return {
        "symbol": symbol,
        "symbolType": stype,
        "baseCoin": base,
        "marketRegion": region,
        "fullName": base,
        "status": "Trading",
        "launchTime": str(launch),
        "fundingInterval": interval,
        "upperFundingRate": "0.005",
        "lowerFundingRate": "-0.005",
        "leverageFilter": {"maxLeverage": "25.00"},
        "priceFilter": {"tickSize": "0.01"},
    }


def test_parse_spis_bybit_filters_tradfi_and_classifies():
    strona = {
        "retCode": 0,
        "result": {
            "list": [
                _bybit_instr("EURUSDUSDT", "forex", "EURUSD", region=""),
                _bybit_instr("XAUUSDT", "commodity", "XAU", region="", interval=240),
                _bybit_instr("TLTUSDT", "ETF", "TLT"),
                _bybit_instr("SPYUSDT", "ETF", "SPY"),
                _bybit_instr("AAPLUSDT", "stock", "AAPL"),
                _bybit_instr("BTCUSDT", "", "BTC", region=""),
                _bybit_instr("DOGEUSDT", "", "DOGE", region=""),
                _bybit_instr("PEPEUSDT", "innovation", "PEPE", region=""),
            ]
        },
    }
    df = ft.parsuj_spis_bybit([strona]).set_index("symbol")
    assert set(df.index) == {"EURUSDUSDT", "XAUUSDT", "TLTUSDT", "SPYUSDT", "AAPLUSDT", "BTCUSDT"}
    assert df.loc["TLTUSDT", "klasa"] == "ETF_oblig" and df.loc["SPYUSDT", "klasa"] == "ETF"
    assert df.loc["XAUUSDT", "interwal_h"] == 4.0 and df.loc["AAPLUSDT", "max_dzwignia"] == 25.0
    assert df.loc["BTCUSDT", "klasa"] == "BTC_kontrola"
    assert json.loads(df.loc["AAPLUSDT", "surowe"])["baseCoin"] == "AAPL"  # pełny rekord źródła


def test_parse_spis_binance_merges_funding_info_and_cross_references_etf():
    def s(sym, ut, base):
        return {
            "symbol": sym,
            "pair": sym,
            "contractType": "TRADIFI_PERPETUAL" if sym != "BTCUSDT" else "PERPETUAL",
            "underlyingType": ut,
            "underlyingSubType": ["TradFi"],
            "baseAsset": base,
            "status": "TRADING",
            "onboardDate": T0,
            "filters": [{"filterType": "PRICE_FILTER", "tickSize": "0.01"}],
        }

    info = {
        "symbols": [
            s("SPYUSDT", "EQUITY", "SPY"),
            s("SOXLUSDT", "EQUITY", "SOXL"),
            s("AAPLUSDT", "EQUITY", "AAPL"),
            s("TMFUSDT", "EQUITY", "TMF"),
            s("HK0700USDT", "HK_EQUITY", "HK0700"),
            s("USDBRLUSDT", "FX", "USDBRL"),
            s("OPENAIUSDT", "PREMARKET", "OPENAI"),
            s("BTCUSDT", "COIN", "BTC"),
            {**s("ETHUSDT", "COIN", "ETH"), "contractType": "PERPETUAL"},
        ]
    }
    fi = [{"symbol": "SPYUSDT", "fundingIntervalHours": 4, "adjustedFundingRateCap": "0.01"}]
    df = ft.parsuj_spis_binance(info, fi, bybit_etf=frozenset({"SOXLUSDT"})).set_index("symbol")
    assert "ETHUSDT" not in df.index
    assert (df.loc["SPYUSDT", "klasa"], df.loc["SPYUSDT", "klasa_zrodlo"]) == ("ETF", "lista ETF")
    assert (df.loc["SOXLUSDT", "klasa"], df.loc["SOXLUSDT", "klasa_zrodlo"]) == (
        "ETF",
        "Bybit symbolType=ETF",
    )
    assert df.loc["AAPLUSDT", "klasa"] == "akcje" and df.loc["TMFUSDT", "klasa"] == "ETF_oblig"
    assert (df.loc["HK0700USDT", "klasa"], df.loc["HK0700USDT", "region"]) == ("akcje", "HK")
    assert (
        df.loc["USDBRLUSDT", "klasa"] == "waluty" and df.loc["OPENAIUSDT", "klasa"] == "przed_IPO"
    )
    assert df.loc["SPYUSDT", "interwal_h"] == 4.0 and df.loc["AAPLUSDT", "interwal_h"] == 8.0
    assert df.loc["AAPLUSDT", "interwal_zrodlo"] == "domyślny 8 h"


def test_do_ramki_dedupes_and_sorts():
    rek = [
        {"symbol": "B", "czas_ms": T0, "fundingRate": 1.0},
        {"symbol": "A", "czas_ms": T0 + 1, "fundingRate": 2.0},
        {"symbol": "A", "czas_ms": T0, "fundingRate": 3.0},
        {"symbol": "A", "czas_ms": T0, "fundingRate": 9.0},  # powtórzenie czasu
    ]
    df = ft.do_ramki(rek, ("fundingRate",))
    assert list(zip(df["symbol"], df["fundingRate"], strict=True)) == [
        ("A", 3.0),
        ("A", 2.0),
        ("B", 1.0),
    ]
    assert str(df["czas"].dt.tz) == "UTC"


# ------------------------------------------------------------------ pobieranie z fałszywym get
def _parametry(url):
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))


def test_pobierz_funding_bybit_pages_backwards_via_endtime():
    czasy = [T0 + i * 8 * ft.HOUR_MS for i in range(450)]  # > 2 strony po 200
    wywolania = []

    def get(url):
        p = _parametry(url)
        wywolania.append(p)
        assert url.startswith(ft.BYBIT_FUNDING) and p["limit"] == "200"
        lst = [t for t in sorted(czasy, reverse=True) if t <= int(p["endTime"])][:200]
        return {
            "retCode": 0,
            "result": {
                "list": [
                    {"symbol": "X", "fundingRate": "0.0001", "fundingRateTimestamp": str(t)}
                    for t in lst
                ]
            },
        }

    wynik = ft.pobierz_funding_bybit(get, "X", od_ms=T0 - 1, do_ms=czasy[-1] + 10)
    assert [r["czas_ms"] for r in wynik] == czasy
    assert len(wywolania) == 4  # 200 + 200 + 50 + pusta strona


def test_pobierz_funding_binance_pages_forward_via_starttime():
    czasy = [T0 + i * 4 * ft.HOUR_MS + 1 for i in range(2_100)]

    def get(url):
        p = _parametry(url)
        assert url.startswith(ft.BINANCE_FUNDING) and p["limit"] == "1000"
        lst = [t for t in czasy if t >= int(p["startTime"])][:1000]
        return [
            {"symbol": "X", "fundingTime": t, "fundingRate": "0", "markPrice": "1"} for t in lst
        ]

    wynik = ft.pobierz_funding_binance(get, "X", od_ms=T0, do_ms=czasy[-1] + ft.HOUR_MS)
    assert [r["czas_ms"] for r in wynik] == czasy


def test_pobierz_swiece_binance_index_uses_pair():
    adresy = []

    def get(url):
        adresy.append(url)
        return []

    ft.pobierz_swiece_binance(get, "XAUUSDT", "XAUUSDT_PAIR", "index", T0, T0 + ft.HOUR_MS)
    ft.pobierz_swiece_binance(get, "XAUUSDT", "XAUUSDT_PAIR", "mark", T0, T0 + ft.HOUR_MS)
    assert _parametry(adresy[0])["pair"] == "XAUUSDT_PAIR" and "symbol" not in _parametry(adresy[0])
    assert _parametry(adresy[1])["symbol"] == "XAUUSDT"


def test_pobierz_spis_bybit_follows_cursor():
    strony = {
        "": {
            "retCode": 0,
            "result": {
                "list": [_bybit_instr("AAPLUSDT", "stock", "AAPL")],
                "nextPageCursor": "c=1&x",
            },
        },
        "c=1&x": {
            "retCode": 0,
            "result": {"list": [_bybit_instr("BTCUSDT", "", "BTC")], "nextPageCursor": ""},
        },
    }
    df = ft.pobierz_spis_bybit(lambda url: strony[_parametry(url).get("cursor", "")])
    assert list(df["symbol"]) == ["AAPLUSDT", "BTCUSDT"]


# ------------------------------------------------------------------ migawka i rdzeń
def test_migawka_writes_gzip_with_all_sources(tmp_path):
    teraz = dt.datetime(2026, 9, 28, 18, 19, 1, tzinfo=dt.UTC)
    path = ft.migawka(tmp_path, now=teraz, get=lambda url: {"url": url})
    assert path.name == "20260928T181901Z.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        rec = json.load(fh)
    assert rec["czas_utc"] == teraz.isoformat()
    assert {k: v["url"] for k, v in rec.items() if k != "czas_utc"} == ft.MIGAWKA_URLS


def test_obroty_migawki_reads_both_exchanges(tmp_path):
    rec = {
        "bybit_tickers": {
            "retCode": 0,
            "result": {"list": [{"symbol": "AAPLUSDT", "turnover24h": "12.5"}]},
        },
        "binance_24h": [{"symbol": "AAPLUSDT", "quoteVolume": "99"}],
    }
    path = tmp_path / "m.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(rec, fh)
    assert ft.obroty_migawki(path) == {"bybit": {"AAPLUSDT": 12.5}, "binance": {"AAPLUSDT": 99.0}}


def test_wybierz_rdzen_follows_preregistered_rule():
    spis = pd.DataFrame(
        [
            ("EURUSDUSDT", "EURUSD", "waluty", ""),
            ("XAUUSDT", "XAU", "surowce", ""),
            ("SPYUSDT", "SPY", "ETF", "US"),
            ("TLTUSDT", "TLT", "ETF_oblig", "US"),
            ("SOXLUSDT", "SOXL", "ETF", "US"),  # ETF spoza listy — nie wchodzi
            ("HK0700USDT", "HK0700", "akcje", "HK"),  # akcja spoza USA — nie wchodzi
            *[(f"S{i}USDT", f"S{i}", "akcje", "US") for i in range(8)],
            ("BTCUSDT", "BTC", "BTC_kontrola", ""),
        ],
        columns=["symbol", "baza", "klasa", "region"],
    )
    obrot = {f"S{i}USDT": float(i) for i in range(7)} | {"S7USDT": float("nan"), "HK0700USDT": 1e9}
    rdzen = ft.wybierz_rdzen(spis, obrot)
    assert rdzen == sorted(
        [
            "EURUSDUSDT",
            "XAUUSDT",
            "SPYUSDT",
            "TLTUSDT",
            "S6USDT",
            "S5USDT",
            "S4USDT",
            "S3USDT",
            "S2USDT",
            "BTCUSDT",
        ]
    )
