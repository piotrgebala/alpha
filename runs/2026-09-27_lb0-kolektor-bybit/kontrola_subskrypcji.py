"""
Kontrola naprawy nieudanej subskrypcji na ŻYWYM Bybit (publiczny wss, bez zapisu na dysk).

Jedno żądanie: BTCUSDT + nieistniejący temat + ETHUSDT. Bybit odrzuca całe żądanie i podaje zły
temat; kolektor ma go odrzucić i od razu wysłać ponownie BTCUSDT + ETHUSDT. Oczekiwane liczniki:
nieudane 1, ponowione tematy 2, udane 1, odrzucony 1 temat.

    PYTHONUTF8=1 .venv/bin/python runs/2026-09-27_lb0-kolektor-bybit/kontrola_subskrypcji.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # katalog repo (import `data`)

from data import collect_liquidations_bybit as clb  # noqa: E402

ARGS = [clb.TOPIC_PREFIX + s for s in ("BTCUSDT", "NIEMATAKIEGOUSDT", "ETHUSDT")]


async def main() -> int:
    stats, rejected, records = clb.new_stats(), set(), []
    reason, is_error = await clb._cycle(
        [[ARGS]],
        connect=clb._connect,
        on_record=records.append,
        stats=stats,
        clock=time.monotonic,
        wall=time.time,
        log=lambda s: print(s, flush=True),
        deadline=time.monotonic() + 15,
        silence_s=60,
        ping_s=clb.PING_EVERY_S,
        tick=lambda: None,
        connected=[],
        rejected_topics=rejected,
    )
    print(f"powód: {reason}; błąd: {is_error}")
    print(
        f"subskrypcje nieudane: {stats['sub_fail']}, udane: {stats['sub_ok']}, "
        f"ponowione tematy: {stats['resubscribed']}, odrzucone: {sorted(rejected)}; "
        f"likwidacji w 15 s: {len(records)}"
    )
    ok = (
        stats["sub_fail"] == 1
        and stats["sub_ok"] == 1
        and stats["resubscribed"] == 2
        and rejected == {ARGS[1]}
        and not is_error
    )
    print("wynik: " + ("ZGODNY z oczekiwaniem" if ok else "NIEZGODNY z oczekiwaniem"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
