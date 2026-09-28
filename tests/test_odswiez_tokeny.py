"""Testy skryptu `tools/odswiez_tokeny.sh` (strona „Tokeny CLAS-5”, docs/rag/12) — w piaskownicy: kopia
skryptu i monitora, fałszywy HOME z jednym zapisem rozmowy, „origin” jako lokalne repo bare. Nigdy
prawdziwy GitHub, nigdy prawdziwe `~/.claude`.

Sprawdza: stan.json trafia na gałąź `tokeny-dane` w origin (commit + push), historia zostaje lokalnie
w `runs/tokeny/`, brak klonu danych albo klon na złej gałęzi = kod 1 bez wysyłki.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or not shutil.which("bash") or not shutil.which("git"),
    reason="skrypt odświeżania działa na serwerze Linux (bash, git)",
)


def _git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def sandbox(tmp_path):
    repo = tmp_path / "alpha"
    (repo / "tools").mkdir(parents=True)
    for name in ("odswiez_tokeny.sh", "zuzycie_tokenow.py"):
        shutil.copy(ROOT / "tools" / name, repo / "tools" / name)
    home = tmp_path / "home"
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))
    rec = {
        "type": "assistant",
        "timestamp": "2026-09-28T01:00:00Z",
        "message": {
            "id": "m1",
            "model": "claude-opus-5-5",
            "content": [],
            "usage": {"input_tokens": 1, "cache_read_input_tokens": 10, "output_tokens": 2},
        },
    }
    proj = home / ".claude" / "projects" / slug
    proj.mkdir(parents=True)
    (proj / "s.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")
    origin = tmp_path / "origin.git"
    _git("init", "-q", "--bare", str(origin))
    dane = home / "alpha-tokeny"
    dane.mkdir()
    _git("init", "-q", cwd=dane)
    _git("checkout", "-q", "-b", "tokeny-dane", cwd=dane)
    _git("config", "user.name", "test", cwd=dane)
    _git("config", "user.email", "test@example.com", cwd=dane)
    _git("remote", "add", "origin", str(origin), cwd=dane)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["HOME"] = str(home)
    return repo, dane, origin, env


def _run(repo, env):
    return subprocess.run(
        ["bash", str(repo / "tools" / "odswiez_tokeny.sh")],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_pushes_state_to_data_branch(sandbox):
    repo, dane, origin, env = sandbox
    r = _run(repo, env)
    assert r.returncode == 0, r.stderr
    assert "wysłano stan.json" in r.stdout
    pushed = json.loads(_git("--git-dir", str(origin), "show", "tokeny-dane:stan.json"))
    assert pushed["wersja"] == 1 and [d["d"] for d in pushed["dni"]] == ["2026-09-28"]
    assert pushed["dni"][0]["m"]["claude-opus-5-5"][1] == 1
    assert (repo / "runs" / "tokeny" / "stan.json").exists()
    log = _git("--git-dir", str(origin), "log", "--format=%s", "tokeny-dane")
    assert log.startswith("Tokeny: stan ")


def test_missing_or_wrong_data_clone_fails_without_push(sandbox):
    repo, dane, origin, env = sandbox
    _git("checkout", "-q", "-b", "master", cwd=dane)
    r = _run(repo, env)
    assert r.returncode == 1 and "tokeny-dane" in r.stderr
    shutil.rmtree(dane)
    r = _run(repo, env)
    assert r.returncode == 1
    assert _git("--git-dir", str(origin), "branch", "--list") == ""
