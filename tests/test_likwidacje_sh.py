"""Testy skryptu nadzoru `tools/likwidacje.sh` — na katalogach tymczasowych z FAŁSZYWYM pythonem
(nigdy prawdziwy kolektor, nigdy prawdziwe `~/likwidacje`): kopia skryptu w piaskownicy, w której
`.venv/bin/python` tylko zapisuje wywołanie i swój pid w katalogu `--dir` i czeka `FAKE_HOLD` s
(Bybit: `FAKE_HOLD_BYBIT`, stan HL: `FAKE_HOLD_HL`, jeśli ustawione) — przez `exec sleep`, więc jak
prawdziwy kolektor nie zbiera statusów cudzych procesów potomnych.

Sprawdza: start kolektorów, gdy żaden nie działa; natychmiastowe wyjście, gdy wszystkie działają;
niezależne blokady (Bybit i stan HL nie dziedziczą blokady Binance — także gdy startują w jednym
przebiegu i Binance kończy się pierwszy); brak procesu-zombie po wyjściu kolektora Bybit i HL;
wyłączniki `WYLACZONY`; część Binance bez zmian w działaniu. Stan HL (runda HS0): blokada w katalogu
danych przekazana kolektorowi jako deskryptor 7 (`--blokada-fd 7`, plik `.lock` tego katalogu).
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
# fałszywy python: zapisuje argumenty w <--dir>/wywolania.txt, pid w <--dir>/pid i czeka
d=""; prev=""
for a in "$@"; do [ "$prev" = "--dir" ] && d="$a"; prev="$a"; done
echo "$*|PYTHONUTF8=$PYTHONUTF8" >> "$d/wywolania.txt"
echo "$$" > "$d/pid"
case "$*" in
  *collect_liquidations_bybit*) h="${FAKE_HOLD_BYBIT:-${FAKE_HOLD:-0}}" ;;
  *collect_hl_stan*) h="${FAKE_HOLD_HL:-${FAKE_HOLD:-0}}"
    if [ -e "/proc/$$/fd/7" ]; then readlink "/proc/$$/fd/7" > "$d/fd7.txt"; fi ;;
  *) h="${FAKE_HOLD:-0}" ;;
esac
exec sleep "$h"
"""


def _sandbox(
    tmp_path: Path,
    hold: float = 0.0,
    hold_bybit: float | None = None,
    hold_hl: float | None = None,
):
    """Piaskownica; katalog stanu HL zawsze `tmp_path / "hl"` (zmienna `CLAS5_HL_STAN_DIR`)."""
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
        "CLAS5_HL_STAN_DIR": str(tmp_path / "hl"),
        "FAKE_HOLD": str(hold),
    }
    if hold_bybit is not None:
        env["FAKE_HOLD_BYBIT"] = str(hold_bybit)
    if hold_hl is not None:
        env["FAKE_HOLD_HL"] = str(hold_hl)
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
    hl = tmp_path / "hl"
    locks = [_hold(bn / ".lock"), _hold(bb / ".lock"), _hold(hl / ".lock")]
    try:
        rc, took = _run(script, env)
        time.sleep(0.5)  # czas na ewentualny start podprocesu Bybit / HL
    finally:
        for f in locks:
            f.close()
    assert rc == 0 and took < 5.0
    assert not (bn / "wywolania.txt").exists() and not (bb / "wywolania.txt").exists()
    assert not (hl / "wywolania.txt").exists()


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


def test_bybit_outliving_binance_does_not_keep_binance_lock(tmp_path):
    # Strażnik kolejności w skrypcie: gdyby blok Bybit stał ZA `exec 9>…/.lock`, kolektor Bybit
    # odziedziczyłby deskryptor blokady Binance i po padnięciu Binance dalej ją trzymał — cron już
    # nigdy nie wznowiłby Binance. Tu oba startują w jednym przebiegu; Binance kończy się pierwszy.
    script, env, bn, bb = _sandbox(tmp_path, hold=0.5, hold_bybit=4.0)
    rc, _ = _run(script, env)  # wraca po wyjściu (fałszywego) kolektora Binance
    assert rc == 0
    assert _wait_for(bb / "wywolania.txt")
    assert _is_locked(bb / ".lock"), "kolektor Bybit powinien jeszcze żyć i trzymać swoją blokadę"
    assert not _is_locked(bn / ".lock"), "Bybit trzyma blokadę Binance"
    _wait_unlocked(bb / ".lock")


def _proc_state(pid: int) -> str | None:
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("State:"):
                return line.split()[1]
    except OSError:
        return None
    return None


@pytest.mark.skipif(not Path("/proc/self/status").exists(), reason="potrzebne /proc (Linux)")
def test_finished_bybit_is_not_left_as_zombie(tmp_path):
    # Bybit kończy się po 0,2 s, Binance żyje 4 s. Bez podwójnego forka rodzicem Bybit byłby proces
    # Binance (powłoka po `exec`), który nie zbiera statusów — zostałby proces-zombie (stan Z).
    script, env, bn, bb = _sandbox(tmp_path, hold=4.0, hold_bybit=0.2)
    proc = subprocess.Popen(["bash", str(script)], env=env)
    try:
        assert _wait_for(bb / "pid")
        pid = int((bb / "pid").read_text(encoding="utf-8"))
        end = time.monotonic() + 3.0
        while time.monotonic() < end and _proc_state(pid) is not None:
            time.sleep(0.05)
        assert proc.poll() is None, "test wymaga, by Binance jeszcze żył"
        assert (
            _proc_state(pid) is None
        ), f"kolektor Bybit został jako proces w stanie {_proc_state(pid)}"
    finally:
        proc.wait(timeout=30)


def test_off_switch_file_skips_bybit_only(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path)
    bb.mkdir()
    (bb / "WYLACZONY").write_text("", encoding="utf-8")
    rc, _ = _run(script, env)
    time.sleep(0.5)  # czas na ewentualny start podprocesu Bybit
    assert rc == 0 and (bn / "wywolania.txt").exists()
    assert not (bb / "wywolania.txt").exists()


# ------------------------------------------------------------------ stan rynku Hyperliquid (HS0)
def test_hl_starts_in_background_with_own_lock_passed_as_fd7(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path, hold_hl=3.0)
    hl = tmp_path / "hl"
    rc, took = _run(script, env)
    assert rc == 0 and took < 2.5  # nie czeka na kolektor HL (tło)
    assert _wait_for(hl / "wywolania.txt")
    assert (hl / "wywolania.txt").read_text(encoding="utf-8") == (
        f"-m data.collect_hl_stan --dir {hl} --blokada-fd 7|PYTHONUTF8=1\n"
    )
    assert _is_locked(hl / ".lock")  # kolektor HL trzyma SWOJĄ blokadę
    if Path("/proc/self/fd").exists():  # deskryptor 7 to plik .lock katalogu HL
        assert _wait_for(hl / "fd7.txt")
        fd7 = Path((hl / "fd7.txt").read_text(encoding="utf-8").strip())
        assert fd7.resolve() == (hl / ".lock").resolve()
    assert not _is_locked(bn / ".lock")  # … i NIE trzyma blokady Binance
    assert (hl / "kolektor.out").exists()
    assert not (tmp_path / "home" / "likwidacje_hl").exists()  # katalog ze zmiennej, nie z $HOME
    _wait_unlocked(hl / ".lock")


def test_hl_second_run_does_not_start_second_hl(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path, hold_hl=3.0)
    hl = tmp_path / "hl"
    _run(script, env)
    assert _wait_for(hl / "wywolania.txt")
    _run(script, env)
    time.sleep(0.5)
    assert len((hl / "wywolania.txt").read_text(encoding="utf-8").splitlines()) == 1
    _wait_unlocked(hl / ".lock")


def test_hl_running_does_not_block_other_collectors(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path)
    hl = tmp_path / "hl"
    lock = _hold(hl / ".lock")
    try:
        rc, _ = _run(script, env)
        time.sleep(0.5)
    finally:
        lock.close()
    assert rc == 0 and (bn / "wywolania.txt").exists() and _wait_for(bb / "wywolania.txt")
    assert not (hl / "wywolania.txt").exists()


def test_hl_outliving_binance_keeps_only_its_own_lock(tmp_path):
    # Strażnik kolejności: blok HL MUSI stać przed `exec 9>…/.lock` — inaczej kolektor HL odziedziczyłby
    # blokadę Binance (albo Binance blokadę HL) i cron nie wznowiłby kolektora, który padł.
    script, env, bn, bb = _sandbox(tmp_path, hold=0.5, hold_bybit=0.2, hold_hl=4.0)
    hl = tmp_path / "hl"
    rc, _ = _run(script, env)  # wraca po wyjściu (fałszywego) kolektora Binance
    assert rc == 0
    assert _wait_for(hl / "wywolania.txt")
    assert _is_locked(hl / ".lock"), "kolektor HL powinien jeszcze żyć i trzymać swoją blokadę"
    assert not _is_locked(bn / ".lock"), "HL trzyma blokadę Binance"
    # Uwaga 5 z przeglądu 16c: sprawdzić blokadę Bybit BEZ czekania — po wyjściu procesu Bybit, póki HL
    # żyje (czekanie do zwolnienia przepuściłoby HL trzymającego blokadę Bybit aż do własnego końca).
    assert _wait_for(bb / "pid")
    pid_bybit = int((bb / "pid").read_text(encoding="utf-8"))
    koniec = time.monotonic() + 3.0
    while time.monotonic() < koniec and _proc_state(pid_bybit) is not None:
        time.sleep(0.05)
    assert _proc_state(pid_bybit) is None, "fałszywy kolektor Bybit (0,2 s) powinien już skończyć"
    assert _is_locked(hl / ".lock"), "test wymaga, by HL jeszcze żył"
    assert not _is_locked(bb / ".lock"), "HL trzyma blokadę Bybit"
    _wait_unlocked(hl / ".lock")


@pytest.mark.skipif(not Path("/proc/self/status").exists(), reason="potrzebne /proc (Linux)")
def test_finished_hl_is_not_left_as_zombie(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path, hold=4.0, hold_hl=0.2)
    hl = tmp_path / "hl"
    proc = subprocess.Popen(["bash", str(script)], env=env)
    try:
        assert _wait_for(hl / "pid")
        pid = int((hl / "pid").read_text(encoding="utf-8"))
        end = time.monotonic() + 3.0
        while time.monotonic() < end and _proc_state(pid) is not None:
            time.sleep(0.05)
        assert proc.poll() is None, "test wymaga, by Binance jeszcze żył"
        assert (
            _proc_state(pid) is None
        ), f"kolektor HL został jako proces w stanie {_proc_state(pid)}"
    finally:
        proc.wait(timeout=30)


def test_hl_off_switch_skips_hl_only(tmp_path):
    script, env, bn, bb = _sandbox(tmp_path)
    hl = tmp_path / "hl"
    hl.mkdir()
    (hl / "WYLACZONY").write_text("", encoding="utf-8")
    rc, _ = _run(script, env)
    time.sleep(0.5)  # czas na ewentualny start podprocesu HL
    assert rc == 0 and (bn / "wywolania.txt").exists() and _wait_for(bb / "wywolania.txt")
    assert not (hl / "wywolania.txt").exists()
