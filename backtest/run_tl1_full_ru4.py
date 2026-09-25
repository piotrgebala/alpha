"""
run_tl1_full_ru4.py — runda RU4 (korekta danych, 0 wariantów): TL1 (tłok lewara na przekroju top-20)
na PEŁNYM uniwersum. TL1 liczono na obciętym `data/raw/universe` (287/685, RU1); RU2 przeliczyła inne
rundy, TL1 czekała na OI nowych członków. Reguła TL1 bez zmian — zamrożony `run_crowding_tl1`
z podmienionym katalogiem uniwersum i panelem OI (`oi_daily_full.parquet`, `data.fetch_oi_panel`
z `universe_dir=universe_full`). Pokrycie sygnału u członków wypisuje sam TL1.

    PYTHONUTF8=1 py -m backtest.run_tl1_full_ru4 --moc
    PYTHONUTF8=1 py -m backtest.run_tl1_full_ru4
"""

from __future__ import annotations

import sys

from backtest import run_crowding_tl1 as tl1

FULL = "data/raw/universe_full"
OI_FULL = "data/raw/oi_panel/oi_daily_full.parquet"


def main(argv: list[str]) -> None:
    tl1.UNIVERSE_DIR = FULL
    tl1.OI_PANEL = OI_FULL
    print(f"RU4: TL1 na {FULL}, panel OI {OI_FULL} (pokrycie wypisuje TL1)")
    tl1.run("--moc" in argv)


if __name__ == "__main__":
    main(sys.argv[1:])
