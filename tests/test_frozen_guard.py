"""
test_frozen_guard.py

Testy hooka zasady 13 (`tools/frozen_guard.py`): odmowa edycji zamrożonych skryptów.

Dwie właściwości są ważniejsze od samej odmowy, bo ich złamanie szkodzi SESJI: hook nigdy
nie rzuca wyjątku i nigdy nie pisze na stdout, gdy zezwala (Claude Code czyta stdout hooka
jako jego decyzję). Trzecia grupa to spójność PRAWDZIWEJ listy `runs/ZAMROZONE.txt` z repo:
każdy wpis istnieje, żadna wspólna biblioteka nie jest zamrożona, a każdy skrypt uruchamiany
komendą w README rundy jest na liście — inaczej nowa runda „zapomni” zamrozić swój skrypt.
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path

import pytest

from tools.frozen_guard import (
    GUARDED_TOOLS,
    LIST_RELATIVE,
    absolute_path,
    extract_target_path,
    find_root,
    frozen_reason,
    hook_main,
    list_status,
    main,
    normalize,
    read_frozen_list,
)

REPO = Path(__file__).resolve().parents[1]
CANONICAL_LIBS = {
    "backtest/__init__.py",
    "backtest/engine.py",
    "backtest/metrics.py",
    "backtest/costs.py",
    "backtest/checkpoint_lib.py",
    "backtest/run_checkpoint_v2.py",
}


def make_repo(root: Path, frozen: list[str], free: list[str] = ()) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel in [*frozen, *free]:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# skrypt\n", encoding="utf-8")
    (root / LIST_RELATIVE).parent.mkdir(parents=True, exist_ok=True)
    (root / LIST_RELATIVE).write_text(
        "# nagłówek\n\n" + "\n".join(f"{rel}   # runda" for rel in frozen) + "\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(
        tmp_path / "repo",
        frozen=["backtest/run_checkpoint.py", "backtest/stare/diagnoza.py"],
        free=["backtest/engine.py", "tools/frozen_guard.py"],
    )


def payload(path: str | Path, tool: str = "Edit", cwd: str | Path | None = None, key=None):
    key = key or ("notebook_path" if tool == "NotebookEdit" else "file_path")
    event = {"tool_name": tool, "tool_input": {key: str(path)}}
    if cwd is not None:
        event["cwd"] = str(cwd)
    return event


def run_hook(capsys, event) -> tuple[int, str]:
    raw = event if isinstance(event, (bytes, str)) else json.dumps(event)
    code = hook_main(raw)
    return code, capsys.readouterr().out


def decision(out: str) -> dict:
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 1, out
    return json.loads(lines[0])["hookSpecificOutput"]


# --- normalizacja i wyciąganie ścieżki --------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "backtest/run_checkpoint.py",
        "backtest\\run_checkpoint.py",
        "./backtest/run_checkpoint.py",
        "backtest//run_checkpoint.py",
        " BACKTEST/Run_Checkpoint.PY ",
        "./backtest\\./run_checkpoint.py",
    ],
)
def test_normalize_collapses_separators_dots_and_case(raw):
    assert normalize(raw) == "backtest/run_checkpoint.py"


@pytest.mark.parametrize("tool", sorted(GUARDED_TOOLS))
def test_extract_target_path_for_every_guarded_tool(tool):
    event = payload("x/y.py", tool=tool)
    assert extract_target_path(event) == "x/y.py"


@pytest.mark.parametrize(
    "event",
    [
        None,
        [],
        "Edit",
        {"tool_name": "Read", "tool_input": {"file_path": "backtest/run_checkpoint.py"}},
        {
            "tool_name": "Bash",
            "tool_input": {"command": "sed -i s/a/b/ backtest/run_checkpoint.py"},
        },
        {"tool_name": "Edit"},
        {"tool_name": "Edit", "tool_input": "backtest/run_checkpoint.py"},
        {"tool_name": "Edit", "tool_input": {"file_path": 123}},
        {"tool_name": "Edit", "tool_input": {"file_path": "   "}},
        {"tool_input": {"file_path": "backtest/run_checkpoint.py"}},
    ],
)
def test_extract_target_path_ignores_non_edit_events_and_bad_shapes(event):
    assert extract_target_path(event) is None


@pytest.mark.skipif(os.name != "nt", reason="litera dysku istnieje tylko na Windows")
def test_absolute_path_git_bash_drive_on_windows():
    win = absolute_path("/c/Users/x/repo/a.py", None, windows=True)
    assert str(win).replace("\\", "/").lower().startswith("c:/users/x/repo/a.py")


def test_absolute_path_git_bash_drive_ignored_on_posix():
    posix = absolute_path("/c/Users/x/repo/a.py", None, windows=False)
    assert str(posix).replace("\\", "/").endswith("/c/Users/x/repo/a.py")


def test_absolute_path_resolves_relative_against_event_cwd(tmp_path: Path):
    got = absolute_path("backtest/run_checkpoint.py", str(tmp_path))
    assert got == Path(os.path.abspath(tmp_path / "backtest" / "run_checkpoint.py"))


# --- lista ------------------------------------------------------------------------------


def test_read_frozen_list_tolerates_comments_blank_lines_crlf_and_bom(tmp_path: Path):
    path = tmp_path / "ZAMROZONE.txt"
    path.write_bytes(
        b"\xef\xbb\xbf# komentarz\r\n\r\n  backtest\\a.py  # C6\r\nbacktest/B.py\r\n#x/y.py\r\n"
    )
    assert read_frozen_list(path) == {"backtest/a.py", "backtest/b.py"}


def test_find_root_walks_up_from_the_file_not_from_cwd(repo: Path, tmp_path: Path):
    assert find_root(repo / "backtest" / "stare" / "diagnoza.py") == repo
    assert find_root(tmp_path / "gdzie_indziej" / "plik.py") is None


# --- decyzja hooka ----------------------------------------------------------------------


def test_denies_frozen_file_with_reason_naming_the_rule(repo: Path, capsys):
    code, out = run_hook(capsys, payload(repo / "backtest" / "run_checkpoint.py"))
    assert code == 0
    got = decision(out)
    assert got["hookEventName"] == "PreToolUse"
    assert got["permissionDecision"] == "deny"
    assert "backtest/run_checkpoint.py" in got["permissionDecisionReason"]
    assert "zasada 13" in got["permissionDecisionReason"]


def test_denies_frozen_file_in_subdirectory(repo: Path, capsys):
    _, out = run_hook(capsys, payload(repo / "backtest" / "stare" / "diagnoza.py"))
    assert decision(out)["permissionDecision"] == "deny"


def test_deny_output_is_one_ascii_json_line(repo: Path, capsys):
    _, out = run_hook(capsys, payload(repo / "backtest" / "run_checkpoint.py"))
    assert out.count("\n") == 1 and out.isascii()


def test_allows_free_file_silently(repo: Path, capsys):
    code, out = run_hook(capsys, payload(repo / "backtest" / "engine.py"))
    assert code == 0 and out == ""


def test_allows_new_file_that_does_not_exist_yet(repo: Path, capsys):
    code, out = run_hook(capsys, payload(repo / "backtest" / "run_nowa_runda.py", tool="Write"))
    assert code == 0 and out == ""


def test_matching_ignores_case_of_file_name(repo: Path, capsys):
    _, out = run_hook(capsys, payload(repo / "backtest" / "RUN_CHECKPOINT.PY"))
    assert decision(out)["permissionDecision"] == "deny"


@pytest.mark.skipif(os.name != "nt", reason="ukośniki wsteczne są separatorem tylko na Windows")
def test_matching_accepts_backslash_paths(repo: Path, capsys):
    raw = str(repo / "backtest" / "run_checkpoint.py").replace("/", "\\")
    _, out = run_hook(capsys, payload(raw))
    assert decision(out)["permissionDecision"] == "deny"


def test_relative_path_is_resolved_against_event_cwd(repo: Path, tmp_path: Path, capsys):
    _, out = run_hook(capsys, payload("backtest/run_checkpoint.py", cwd=repo))
    assert decision(out)["permissionDecision"] == "deny"
    other = tmp_path / "inne"
    other.mkdir()
    code, out = run_hook(capsys, payload("backtest/run_checkpoint.py", cwd=other))
    assert code == 0 and out == ""


def test_worktree_uses_its_own_list(repo: Path, tmp_path: Path, capsys):
    """Plik w worktree rozstrzyga lista worktree, nawet gdy `cwd` zdarzenia wskazuje główne repo."""
    wt = make_repo(
        tmp_path / "wt", frozen=["backtest/inny.py"], free=["backtest/run_checkpoint.py"]
    )
    code, out = run_hook(capsys, payload(wt / "backtest" / "run_checkpoint.py", cwd=repo))
    assert code == 0 and out == ""
    _, out = run_hook(capsys, payload(wt / "backtest" / "inny.py", cwd=repo))
    assert decision(out)["permissionDecision"] == "deny"


def test_notebook_edit_uses_notebook_path(tmp_path: Path, capsys):
    root = make_repo(tmp_path / "nb", frozen=["runs/analiza.ipynb"])
    _, out = run_hook(capsys, payload(root / "runs" / "analiza.ipynb", tool="NotebookEdit"))
    assert decision(out)["permissionDecision"] == "deny"


def test_multiedit_uses_file_path(repo: Path, capsys):
    _, out = run_hook(capsys, payload(repo / "backtest" / "run_checkpoint.py", tool="MultiEdit"))
    assert decision(out)["permissionDecision"] == "deny"


def test_read_tool_on_frozen_file_is_allowed(repo: Path, capsys):
    code, out = run_hook(capsys, payload(repo / "backtest" / "run_checkpoint.py", tool="Read"))
    assert code == 0 and out == ""


def test_file_outside_any_repo_is_allowed(tmp_path: Path, capsys):
    code, out = run_hook(capsys, payload(tmp_path / "luzem" / "run_checkpoint.py"))
    assert code == 0 and out == ""


def test_unreadable_list_allows(repo: Path, capsys):
    (repo / LIST_RELATIVE).write_bytes(b"\xff\xfe\x00garbage")
    code, out = run_hook(capsys, payload(repo / "backtest" / "run_checkpoint.py"))
    assert code == 0 and out == ""


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{",
        b"[]",
        b"null",
        b'"tekst"',
        b'{"tool_name": "Edit"}',
        b'{"tool_name": "Edit", "tool_input": null}',
        b'{"tool_name": "Edit", "tool_input": {"file_path": ""}}',
        b'{"tool_name": "Edit", "tool_input": {"file_path": "a.py"}, "cwd": 7}',
        bytes([0xFF, 0xFE, 0x00, 0x01]),
        "{" * 10_000,
    ],
)
def test_hook_never_raises_and_stays_silent_on_garbage(raw, capsys):
    code, out = run_hook(capsys, raw)
    assert code == 0 and out == ""


def test_frozen_reason_is_none_for_free_file(repo: Path):
    assert frozen_reason(payload(repo / "backtest" / "engine.py")) is None


# --- CLI --------------------------------------------------------------------------------


def test_cli_lista_reports_missing_files(repo: Path, monkeypatch, capsys):
    (repo / LIST_RELATIVE).write_text(
        "backtest/run_checkpoint.py\nbacktest/znikl.py\n", encoding="utf-8"
    )
    monkeypatch.chdir(repo / "backtest")
    assert main(["lista"]) == 1
    out = capsys.readouterr().out
    assert "BRAK  backtest/znikl.py" in out and "OK    backtest/run_checkpoint.py" in out


def test_cli_lista_ok_returns_zero(repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["lista"]) == 0


def test_cli_sprawdz(repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["sprawdz", "backtest/run_checkpoint.py"]) == 1
    assert main(["sprawdz", "backtest/engine.py"]) == 0


def test_cli_outside_repo_returns_two(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["lista"]) == 2


def test_list_status_pairs(repo: Path):
    entries, missing = list_status(repo)
    assert entries == ["backtest/run_checkpoint.py", "backtest/stare/diagnoza.py"]
    assert missing == []


# --- PRAWDZIWA lista w repo -------------------------------------------------------------


def real_entries() -> list[str]:
    entries, missing = list_status(REPO)
    assert missing == [], f"wpisy bez pliku: {missing}"
    return entries


def test_real_list_has_no_canonical_library():
    frozen = {normalize(e) for e in real_entries()}
    assert not (frozen & CANONICAL_LIBS), "wspólne biblioteki nie są zamrożone (zasada 13)"


def test_real_list_covers_every_script_run_from_a_round_readme():
    """Każdy `py -m backtest.<skrypt>` z README rundy → skrypt na liście (poza kanonicznymi)."""
    pattern = re.compile(r"\b(?:py|python3?)(?: -m)? backtest[./]([A-Za-z0-9_]+)")
    used = set()
    for readme in REPO.glob("runs/*/README.md"):
        used.update(pattern.findall(readme.read_text(encoding="utf-8", errors="replace")))
    frozen = {normalize(e) for e in real_entries()}
    missing = sorted(
        name
        for name in used
        if f"backtest/{name}.py" not in CANONICAL_LIBS and f"backtest/{name}.py" not in frozen
    )
    assert missing == [], f"skrypty rund poza listą zamrożonych: {missing}"


def test_real_list_covers_pyproject_formatter_exclusions():
    """Skrypt, którego black/ruff nie dotykają (pyproject), tym bardziej jest zamrożony."""
    conf = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    excluded = {
        normalize(e) for e in conf["tool"]["ruff"]["extend-exclude"] if e.startswith("backtest/")
    }
    frozen = {normalize(e) for e in real_entries()}
    assert excluded <= frozen, sorted(excluded - frozen)


def test_real_hook_denies_frozen_script_and_allows_tools(capsys):
    _, out = run_hook(capsys, payload(REPO / "backtest" / "run_checkpoint.py", cwd=REPO))
    assert decision(out)["permissionDecision"] == "deny"
    code, out = run_hook(capsys, payload(REPO / "tools" / "frozen_guard.py", cwd=REPO))
    assert code == 0 and out == ""
