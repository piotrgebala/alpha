"""
run_p4_pokrycie_onchain.py — brama danych P4 (bez hipotezy, 0 wariantów): jakie pokrycie danymi on-chain
ma koszyk top-20 / top-50 perpetuali Binance (skład miesięczny z danych sprzed miesiąca, jak X1/AU2)?

Źródło: katalog CoinMetrics community (`/v4/catalog-v2/asset-metrics`, ten sam host co `fetch_external`),
dla każdej metryki: aktywa z częstością 1d dostępną za darmo i data początku. Symbol perpetuala →
identyfikator CoinMetrics: bez `USDT`, bez mnożnika (`1000`, `1000000`, `1M`), małe litery.
Pokrycie miesiąca = udział członków koszyka, dla których metryka istnieje od początku miesiąca.

    PYTHONUTF8=1 py -m backtest.run_p4_pokrycie_onchain
"""

from __future__ import annotations

import json
import re
import urllib.parse

import pandas as pd

from backtest.run_au2_szerokosc import feasible_members
from backtest.rebalance_premium import load_universe
from data.fetch_external import http_get

CATALOG = "https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics"
METRICS = ["FlowInExUSD", "FlowOutExUSD", "SplyExNtv", "AdrActCnt", "CapMVRVCur", "TxCnt"]
FULL = "data/raw/universe_full"
START, END = "2021-02-01", "2026-07-01"
SEP = "=" * 104


def cm_asset(symbol: str) -> str:
    """`1000PEPEUSDT` → `pepe`, `BTCUSDT` → `btc`, `1000000MOGUSDT` → `mog`, `1MBABYDOGEUSDT` → `babydoge`."""
    base = re.sub(r"USDT$", "", symbol)
    base = re.sub(r"^(1000000|100000|10000|1000|1M)(?=[A-Z])", "", base)
    return base.lower()


def parse_catalog(pages: list[dict], metric: str) -> dict[str, pd.Timestamp]:
    """{aktywo: początek 1d community} dla jednej metryki z listy stron odpowiedzi katalogu."""
    out = {}
    for page in pages:
        for a in page.get("data", []):
            for m in a.get("metrics", []):
                if m.get("metric") != metric:
                    continue
                for f in m.get("frequencies", []):
                    if f.get("frequency") == "1d" and f.get("community"):
                        out[a["asset"]] = pd.Timestamp(f["min_time"]).tz_convert("UTC")
    return out


def coverage(members: dict, avail: dict[str, pd.Timestamp]) -> pd.Series:
    """Udział członków miesiąca, których metryka jest dostępna od początku miesiąca."""
    rows = {}
    for m, syms in sorted(members.items()):
        ok = [s for s in syms if cm_asset(s) in avail and avail[cm_asset(s)] <= m]
        rows[m] = len(ok) / len(syms)
    return pd.Series(rows)


def fetch_catalog(metric: str) -> list[dict]:
    pages, url = [], f"{CATALOG}?{urllib.parse.urlencode({'metrics': metric, 'page_size': 1000})}"
    while url:
        page = json.loads(http_get(url))
        pages.append(page)
        url = page.get("next_page_url")
    return pages


def main() -> None:
    _, volume = load_universe(FULL)
    lo, end = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp(END, tz="UTC")
    volume = volume[(volume.index >= lo) & (volume.index < end)]
    months = [m for m in pd.date_range(START, END, freq="MS", tz="UTC") if m < end]
    print(SEP)
    print(
        "P4 — pokrycie danymi on-chain (CoinMetrics community, 1d) koszyków top-20 / top-50 perpetuali"
    )
    print(SEP)
    avail = {m: parse_catalog(fetch_catalog(m), m) for m in METRICS}
    for top_n in (20, 50):
        members, _ = feasible_members(volume, months, top_n)
        print(f"\n  TOP-{top_n} ({len(members)} miesięcy):")
        for metric in METRICS:
            c = coverage(members, avail[metric])
            print(
                f"    {metric:<12} aktywów w katalogu {len(avail[metric]):4d} | pokrycie koszyka średnio {100 * c.mean():5.1f}% "
                f"[min {100 * c.min():5.1f}%, 2021 {100 * c[c.index.year == 2021].mean():5.1f}%, 2025–26 {100 * c[c.index.year >= 2025].mean():5.1f}%]"
            )
        miss = pd.Series(
            [
                s
                for syms in members.values()
                for s in syms
                if cm_asset(s) not in avail["FlowInExUSD"]
            ]
        ).value_counts()
        print(
            "    najczęstsi członkowie BEZ przepływów na giełdy (miesięcy w koszyku): "
            + ", ".join(f"{k} {v}" for k, v in miss.head(12).items())
        )
    print(SEP)


if __name__ == "__main__":
    main()
