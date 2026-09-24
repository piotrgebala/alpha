"""Testy `dziennik/zapisz_do_gita.sh` (poprawka 5 dziennika): commit i push plików dziennika —
tylko na master, tylko pliki dziennika, bez chowania cudzych zmian, bez wypychania cudzej pracy.
Scenariusze na tymczasowych repozytoriach (bare „origin” + klony); wymagają bash i git."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dziennik" / "zapisz_do_gita.sh"
BASH = shutil.which("bash") or (
    r"C:\Program Files\Git\bin\bash.exe"
    if Path(r"C:\Program Files\Git\bin\bash.exe").exists()
    else None
)
pytestmark = pytest.mark.skipif(
    BASH is None or shutil.which("git") is None, reason="wymaga bash i git"
)

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_NOSYSTEM": "1",
}


def git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def run_script(clone: Path) -> str:
    out = subprocess.run(
        [BASH, "dziennik/zapisz_do_gita.sh"],
        cwd=clone,
        env=ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return out.stdout + out.stderr


@pytest.fixture
def repos(tmp_path: Path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "master", str(origin))
    seed = tmp_path / "seed"
    git(tmp_path, "clone", "-q", origin.as_posix(), str(seed))
    (seed / "dziennik").mkdir()
    shutil.copy(SCRIPT, seed / "dziennik" / "zapisz_do_gita.sh")
    (seed / "dziennik" / "sygnaly.csv").write_text("as_of,x\n2026-09-23,1\n", encoding="utf-8")
    (seed / "dziennik" / "przebiegi.log").write_text("przebieg 1\n", encoding="utf-8")
    (seed / "kod.py").write_text("A = 1\n", encoding="utf-8")
    git(seed, "symbolic-ref", "HEAD", "refs/heads/master")
    git(seed, "add", ".")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "master")
    journal = tmp_path / "dziennik_klon"
    other = tmp_path / "serwer_klon"
    git(tmp_path, "clone", "-q", origin.as_posix(), str(journal))
    git(tmp_path, "clone", "-q", origin.as_posix(), str(other))
    return origin, journal, other


def origin_files_last_commit(origin: Path) -> list[str]:
    return git(origin, "show", "--name-only", "--format=", "master").splitlines()


def append(path: Path, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def test_commits_and_pushes_only_journal_files(repos):
    origin, journal, _ = repos
    append(journal / "dziennik" / "sygnaly.csv", "2026-09-24,2\n")
    append(journal / "dziennik" / "przebiegi.log", "przebieg 2\n")
    (journal / "notatka.txt").write_text("nie do repo\n", encoding="utf-8")
    out = run_script(journal)
    assert "===== zapis do gita: wypchnięte" in out
    assert sorted(origin_files_last_commit(origin)) == [
        "dziennik/przebiegi.log",
        "dziennik/sygnaly.csv",
    ]
    msg = git(origin, "log", "-1", "--format=%s", "master")
    assert re.fullmatch(r"Dziennik: przebieg \d{4}-\d{2}-\d{2} \(.+\)", msg), msg  # z nazwą maszyny
    assert run_script(journal).count("brak zmian") == 1  # idempotentnie


def test_skips_when_not_on_master(repos):
    origin, journal, _ = repos
    before = git(origin, "rev-parse", "master")
    git(journal, "checkout", "-q", "-b", "runda")
    append(journal / "dziennik" / "sygnaly.csv", "2026-09-24,2\n")
    out = run_script(journal)
    assert "pominięty — gałąź runda" in out
    assert git(origin, "rev-parse", "master") == before


def test_does_not_push_unpushed_non_journal_work(repos):
    origin, journal, _ = repos
    before = git(origin, "rev-parse", "master")
    (journal / "kod.py").write_text("A = 2\n", encoding="utf-8")
    git(journal, "commit", "-q", "-am", "praca niezrecenzowana")
    append(journal / "dziennik" / "sygnaly.csv", "2026-09-24,2\n")
    out = run_script(journal)
    assert "push pominięty" in out
    assert git(origin, "rev-parse", "master") == before


def test_origin_moved_and_dirty_copy_keeps_user_changes(repos):
    origin, journal, other = repos
    (other / "kod.py").write_text("A = 3\n", encoding="utf-8")
    git(other, "commit", "-q", "-am", "praca z serwera")
    git(other, "push", "-q", "origin", "master")
    (journal / "kod.py").write_text("A = 99  # edycja w toku\n", encoding="utf-8")
    append(journal / "dziennik" / "sygnaly.csv", "2026-09-24,2\n")
    out = run_script(journal)
    assert "bez pull" in out
    assert (journal / "kod.py").read_text(encoding="utf-8") == "A = 99  # edycja w toku\n"
    assert git(journal, "stash", "list") == ""
    assert "<<<<<<<" not in (journal / "kod.py").read_text(encoding="utf-8")


def test_origin_moved_clean_copy_rebases_and_pushes(repos):
    origin, journal, other = repos
    (other / "kod.py").write_text("A = 3\n", encoding="utf-8")
    git(other, "commit", "-q", "-am", "praca z serwera")
    git(other, "push", "-q", "origin", "master")
    append(journal / "dziennik" / "sygnaly.csv", "2026-09-24,2\n")
    out = run_script(journal)
    assert "wypchnięte po pull --rebase" in out
    log = git(origin, "log", "--format=%s", "master").splitlines()
    assert log[0].startswith("Dziennik: przebieg") and log[1] == "praca z serwera"
    assert (journal / "kod.py").read_text(encoding="utf-8") == "A = 3\n"
