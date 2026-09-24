"""
run_universe_fix_ru2.py — runda RU2: korekta danych dla pozostałych rund liczonych na obciętym
uniwersum (wniosek 82). Reguły zamrożone co do bajtu — skrypt tylko podmienia katalog danych
(`data/raw/universe` → `data/raw/universe_full`, OHLC → `universe_ohlc_full`) w module rundy
w czasie wykonania; pliki rund nietknięte (zasada 13).
Pre-rejestracja: `runs/2026-09-24_ru2-korekta-pozostalych/README.md`.

    PYTHONUTF8=1 py -m backtest.run_universe_fix_ru2 tr1|x2|lq1|tf1|r1
"""

from __future__ import annotations

import sys

from backtest import rebalance_premium
from backtest import run_crowding_tf1 as tf1
from backtest import run_rebalance_premium_r1 as r1
from backtest import run_ts_liq_lq1 as lq1
from backtest import run_ts_momentum_oos as oos
from backtest import run_ts_momentum_ts1 as ts1
from backtest import run_xs_momentum_x2 as x2

FULL = "data/raw/universe_full"
OHLC_FULL = "data/raw/universe_ohlc_full/ohlc_1d.parquet"


def run_tr1() -> None:
    oos.UNIVERSE_DIR = FULL
    oos.main(["tr1"])


def run_x2() -> None:
    x2.main([FULL])


def run_lq1() -> None:
    lq1._load = lambda _dir: ts1._load(FULL)
    lq1.OHLC = OHLC_FULL
    lq1.main()


def run_tf1() -> None:
    tf1.UNIVERSE_DIR = FULL
    tf1.run(False)


def run_r1() -> None:
    r1.load_universe = lambda _dir: rebalance_premium.load_universe(FULL)
    r1.main()


if __name__ == "__main__":
    {"tr1": run_tr1, "x2": run_x2, "lq1": run_lq1, "tf1": run_tf1, "r1": run_r1}[sys.argv[1]]()
