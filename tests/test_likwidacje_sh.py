"""Testy skryptu nadzoru `tools/likwidacje.sh` — na katalogach tymczasowych z FAŁSZYWYM pythonem
(nigdy prawdziwy kolektor, nigdy prawdziwe `~/likwidacje`): kopia skryptu w piaskownicy, w której
`.venv/bin/python` tylko zapisuje wywołanie w swoim katalogu `--dir` i czeka `FAKE_HOLD` s.

Sprawdza: start obu kolektorów, gdy żaden nie działa; natychmiastowe wyjście, gdy oba działają;
niezależne blokady (Bybit nie dziedziczy blokady Binance); część Binance bez zmian w działaniu.
"""

from __future__ import annotations

import fcntl
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or not shutil.which("flock") or not shutil.which("bash"),
    reason="skrypt nadzoru działa tylko na serwerze Linux (flock, bash)",
)

FAKE_PY = """#!/usr/bin/env bash
# fałszywy python: zapisuje argumenty w <--dir>/wywolania.txt i czeka FAKE_HOLD s
d=""; prev=""
for a in "$@"; do [ "$prev" = "--dir" ] && d="$a"; prev="$a"; done
echo "$*|PYTHONUTF8=$PYTHONUTF8" >> "$d/wywolania.txt"
sleep "${FAKE_HOLD:-0}"
"""


def _sandbox(tmp_path: Path, hold: float = 0.0):
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    shutil.copy(ROOT / "tools" / "likwidacje.sh", repo / "tools" / "likwidacje.sh")
    py = repo / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text(FAKE_PY, encoding="utf-8")
    py.chmod(0o755)
    home, bn, bb = tmp_path / "home", tmp_path / "binance", tmp_path / "bybit"
    home.mkdir()
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),  # domyślne katalogi też w piaskownicy
        "CLAS5_LIKWIDACJE_DIR": str(bn),
        "CLAS5_LIKWIDACJE_BYBIT_DIR": str(bb),
        "FAKE_HOLD": str(hold),
    }
    return repo / "tools" / "likwidacje.sh", env, bn, bb


def _run(script: Path, env: dict) -> tuple[int, float]:
    t0 = time.monotonic()
    rc = subprocess.run(["bash", str(script)], env=env, timeout=30).returncode
    return rc, time.monotonic() - t0


def _wait_for(path: Path, timeout: float = 10.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists() and path.read_text(encoding="utf-8").strip():
            return True
        time.sleep(0.05)
    return False


def _hold(lock: Path):
    lock.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock, "a")  # noqa: SIM115 — blokada żyje do zamknięcia pliku
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return f


def _is_locked(lock: Path) -> bool:
    with open(lock, "a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(f, fcntl.LOCK_UN)
        return False


def _wait_unlocked(lock: Path, timeout: float = 15.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end and _is_locked(lock):
        time.sleep(0.1)


def test_starts_both_collectors_when_none_runs(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path)
    rc, _ = _run(script, env)
    assert rc == 0
    calls_bn = (bn / "wywolania.txt").read_text(encoding="utf-8")
    assert calls_bn == f"-m data.collect_liquidations --dir {bn}|PYTHONUTF8=1\n"  # jak dotąd
    assert _wait_for(bb / "wywolania.txt")
    assert (bb / "wywolania.txt").read_text(encoding="utf-8") == (
        f"-m data.collect_liquidations_bybit --dir {bb}|PYTHONUTF8=1\n"
    )
    assert (bn / "kolektor.out").exists() and (bb / "kolektor.out").exists()
    assert not (tmp_path / "home" / "likwidacje").exists()


def test_exits_immediately_when_both_run(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path)
    locks = [_hold(bn / ".lock"), _hold(bb / ".lock")]
    try:
        rc, took = _run(script, env)
        time.sleep(0.5)  # czas na ewentualny start podprocesu Bybit
    finally:
        for f in locks:
            f.close()
    assert rc == 0 and took < 5.0
    assert not (bn / "wywolania.txt").exists() and not (bb / "wywolania.txt").exists()


def test_bybit_running_binance_down_starts_only_binance(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path)
    lock = _hold(bb / ".lock")
    try:
        rc, _ = _run(script, env)
        time.sleep(0.5)
    finally:
        lock.close()
    assert rc == 0 and (bn / "wywolania.txt").exists()
    assert not (bb / "wywolania.txt").exists()


def test_binance_running_bybit_down_starts_bybit_with_separate_lock(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path, hold=3.0)
    lock = _hold(bn / ".lock")
    try:
        rc, took = _run(script, env)
        assert rc == 0 and took < 2.5  # nie czeka na kolektor Bybit (tło)
        assert not (bn / "wywolania.txt").exists()
        assert _wait_for(bb / "wywolania.txt")
        assert _is_locked(bb / ".lock")  # kolektor Bybit trzyma SWOJĄ blokadę
    finally:
        lock.close()
    assert not _is_locked(bn / ".lock")  # … i NIE trzyma blokady Binance
    _wait_unlocked(bb / ".lock")


def test_second_run_does_not_start_second_bybit(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path, hold=3.0)
    lock = _hold(bn / ".lock")
    try:
        _run(script, env)
        assert _wait_for(bb / "wywolania.txt")
        _run(script, env)
        time.sleep(0.5)
    finally:
        lock.close()
    assert len((bb / "wywolania.txt").read_text(encoding="utf-8").splitlines()) == 1
    _wait_unlocked(bb / ".lock")
