"""
fetch_tradfi_perps.py — perpetuale TradFi (akcje, ETF-y, surowce, waluty) z Bybit i Binance (runda PT1).

Tylko publiczne endpointy REST, bez klucza API; adresy stałe w kodzie, wyłącznie ``https://``.

- ``migawka``: surowe odpowiedzi tickerów obu giełd (najlepsza oferta kupna / sprzedaży, obrót 24 h,
  cena indeksu i mark, bieżący funding) zapisane jako ``.json.gz`` — parsowanie osobno, żeby plik był
  wierną kopią źródła. Tryb pętli (``--co`` sekund, ``--do`` czas UTC) zbiera kilka migawek w różnych
  godzinach handlu rynku bazowego.

Dane POZA repo (``data/raw`` w .gitignore): ``data/raw/tradfi_perps/``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import time
import urllib.request
from pathlib import Path

BYBIT = "https://api.bybit.com"
BINANCE = "https://fapi.binance.com"
OUT = Path("data/raw/tradfi_perps")
MIGAWKA_URLS = {
    "bybit_tickers": f"{BYBIT}/v5/market/tickers?category=linear",
    "binance_book": f"{BINANCE}/fapi/v1/ticker/bookTicker",
    "binance_24h": f"{BINANCE}/fapi/v1/ticker/24hr",
    "binance_premium": f"{BINANCE}/fapi/v1/premiumIndex",
}


def _get(url: str, timeout: float = 20.0):
    """GET → JSON; odmawia adresów spoza https (adresy są stałymi modułu, ale pilnujemy i tak)."""
    if not url.startswith("https://"):
        raise ValueError(f"tylko https: {url!r}")
    req = urllib.request.Request(url, headers={"User-Agent": "alpha-pt1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def migawka(out_dir: Path = OUT / "migawki", now: dt.datetime | None = None, get=_get) -> Path:
    """Jedna migawka: wszystkie odpowiedzi z ``MIGAWKA_URLS`` w jednym pliku ``<czas UTC>.json.gz``."""
    now = now or dt.datetime.now(dt.UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    rec = {"czas_utc": now.isoformat()}
    for key, url in MIGAWKA_URLS.items():
        rec[key] = get(url)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stamp}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(rec, fh)
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("migawka", help="migawka tickerów (raz albo w pętli)")
    m.add_argument("--co", type=int, default=0, help="odstęp pętli w sekundach (0 = jedna migawka)")
    m.add_argument("--do", default="", help="koniec pętli, czas UTC ISO, np. 2026-09-29T00:00")
    args = ap.parse_args(argv)
    if args.cmd == "migawka":
        if args.co <= 0:
            print(migawka())
            return 0
        do_utc = dt.datetime.fromisoformat(args.do).replace(tzinfo=dt.UTC)
        return 0 if petla_migawek(args.co, do_utc) > 0 else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
