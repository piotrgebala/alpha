"""
test_skill_audit.py

Testy rejestru użycia skilli (`tools/skill_audit.py`, CLAUDE.md zasada 19).

Najważniejsze są trzy właściwości hooka, bo ich złamanie szkodzi SESJI, a nie tylko
rejestrowi: hook nigdy nie rzuca wyjątku, nigdy nie pisze na stdout (przy części zdarzeń
stdout trafia do kontekstu modelu) i nigdy nie zapisuje treści wiadomości użytkownika.
Testy integracyjne pracują na prawdziwym gicie: zapis do pliku gałęzi, scalenie rundy przy
„brudnym” rejestrze na master (błąd wykryty w przeglądzie przed scaleniem) oraz reguła
`merge=union` z PRAWDZIWEGO `.gitattributes` projektu.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.skill_audit import (
    LOG_DIR,
    UNKNOWN_COMMAND,
    _plural,
    append_record,
    build_record,
    extract_skill_use,
    hook_main,
    load_records,
    log_file_for_branch,
    main,
    render_report,
)

REPO = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 23, 10, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _skill_payload(skill: str, args: str = "", **extra) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "session_id": "sesja-1",
        "tool_name": "Skill",
        "tool_input": {"skill": skill, "args": args},
        **extra,
    }


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _use_skill(repo: Path, skill: str) -> None:
    hook_main(json.dumps(_skill_payload(skill, cwd=str(repo))))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Świeże repo git na gałęzi `runda-test`, z katalogiem runs/ (jak repo projektu)."""
    _git("init", "-q", cwd=tmp_path)
    _git("checkout", "-q", "-b", "runda-test", cwd=tmp_path)
    (tmp_path / "runs").mkdir()
    return tmp_path


@pytest.fixture
def repo_with_master(repo: Path) -> Path:
    """Repo z commitem bazowym na `master` i PRAWDZIWYM `.gitattributes` projektu."""
    _git("checkout", "-q", "-b", "master", cwd=repo)
    (repo / ".gitattributes").write_bytes((REPO / ".gitattributes").read_bytes())
    (repo / "runs" / "INDEX.md").write_text("spis\n", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "baza", cwd=repo)
    return repo


# --------------------------------------------------------------------------- ekstrakcja


def test_skill_tool_call_is_recorded_as_claude():
    use = extract_skill_use(_skill_payload("engineering:code-review", "przegląd diffu"))
    assert use == {
        "zdarzenie": "PostToolUse",
        "kto": "claude",
        "skill": "engineering:code-review",
        "argumenty": "przegląd diffu",
        "agent": "",
    }


def test_directory_scoped_skill_name_is_recorded():
    """Przegląd przed scaleniem: filtr prywatności odrzucał `apps/web:deploy` — luka w audycie."""
    assert extract_skill_use(_skill_payload("apps/web:deploy"))["skill"] == "apps/web:deploy"


@pytest.mark.parametrize(
    "payload",
    [
        {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"}},
        {"hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": "zle"},
        _skill_payload(""),
        _skill_payload("   "),
        {"hook_event_name": "SessionStart"},
        {},
    ],
)
def test_non_skill_or_malformed_events_are_ignored(payload):
    assert extract_skill_use(payload) is None


def test_long_args_are_shortened_to_one_line():
    use = extract_skill_use(_skill_payload("clas5-runda", "a\n" * 500))
    assert "\n" not in use["argumenty"]
    assert len(use["argumenty"]) == 200
    assert use["argumenty"].endswith("…")


def test_subagent_type_is_recorded():
    use = extract_skill_use(_skill_payload("clas5-quant", agent_type="general-purpose"))
    assert use["agent"] == "general-purpose"


def test_plugin_prefix_is_split_into_its_own_field():
    for skill, plugin in [
        ("engineering:code-review", "engineering"),
        ("anthropic-skills:clas5-runda", "anthropic-skills"),
        ("update-config", ""),
    ]:
        rec = build_record(
            extract_skill_use(_skill_payload(skill)), now=NOW, branch="b", session="s"
        )
        assert rec["wtyczka"] == plugin
        assert rec["czas"] == "2026-09-23T10:00:00+02:00"


# --------------------------------------------------------------------------- prywatność


def test_user_command_records_only_the_name_never_the_text():
    payload = {
        "hook_event_name": "UserPromptExpansion",
        "prompt": "/clas5-runda TAJNE-haslo-123 i reszta zdania",
    }
    use = extract_skill_use(payload)
    assert use["skill"] == "clas5-runda"
    assert use["kto"] == "uzytkownik"
    assert use["argumenty"] == ""
    assert "TAJNE" not in json.dumps(build_record(use, now=NOW, branch="b", session="s"))


def test_user_command_name_from_dedicated_field():
    use = extract_skill_use(
        {"hook_event_name": "UserPromptExpansion", "command_name": "/code-review"}
    )
    assert use["skill"] == "code-review"


def test_unknown_expansion_format_records_field_names_not_values():
    payload = {"hook_event_name": "UserPromptExpansion", "cos_nowego": "sekretna-tresc"}
    use = extract_skill_use(payload)
    assert use["skill"] == UNKNOWN_COMMAND
    assert use["klucze"] == ["cos_nowego", "hook_event_name"]
    serialized = json.dumps(build_record(use, now=NOW, branch="b", session="s"))
    assert "sekretna-tresc" not in serialized


@pytest.mark.parametrize(
    "prompt",
    [
        "zwykłe zdanie z hasłem Mama123",
        "",
        "/",
        "/ spacja",
        "/ Haslo123",  # regresja: „pierwsze słowo po ukośniku” zapisywało hasło
        "/nazwa;rm -rf",
        "/c/Users/ktos/plik.txt",  # ścieżka to nie komenda
        None,
    ],
)
def test_plain_prompts_are_never_recorded(prompt):
    assert extract_skill_use({"hook_event_name": "UserPromptSubmit", "prompt": prompt}) is None


@pytest.mark.parametrize("prompt", ["/clas5-runda", "  /clas5-runda\targumenty"])
def test_slash_command_name_at_end_or_before_whitespace(prompt):
    use = extract_skill_use({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
    assert use["skill"] == "clas5-runda"


# --------------------------------------------------------------------------- hook: bezpieczeństwo


@pytest.mark.parametrize(
    "raw",
    [b"", b"to nie jest json", b"[]", b"\xff\xfe\x00", b'{"cwd": 5}', "{}", b"null"],
)
def test_hook_never_raises_never_prints_and_exits_zero(raw, capsys):
    assert hook_main(raw) == 0
    out = capsys.readouterr()
    assert out.out == ""


def test_hook_outside_git_repo_writes_nothing(tmp_path, capsys):
    payload = json.dumps(_skill_payload("clas5-quant", cwd=str(tmp_path)))
    assert hook_main(payload.encode()) == 0
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr().out == ""


def test_hook_skips_repo_without_runs_dir(tmp_path):
    _git("init", "-q", cwd=tmp_path)
    assert hook_main(json.dumps(_skill_payload("clas5-quant", cwd=str(tmp_path)))) == 0
    assert not (tmp_path / "runs").exists()


# --------------------------------------------------------------------------- hook: zapis (git)


def test_branch_file_names_are_sanitized(tmp_path):
    assert log_file_for_branch(tmp_path, "task/Z17b-x").name == "task_Z17b-x.jsonl"
    assert log_file_for_branch(tmp_path, "worktree-t4").name == "worktree-t4.jsonl"
    assert log_file_for_branch(tmp_path, "(odlaczony HEAD @abc)").parent == tmp_path / LOG_DIR
    assert log_file_for_branch(tmp_path, "..").name == "_.jsonl"  # brak wyjścia poza katalog
    # Przegląd przed scaleniem: bardzo długa gałąź przekraczała limit nazwy pliku.
    assert len(log_file_for_branch(tmp_path, "x" * 400).name) == 100 + len(".jsonl")


def test_hook_appends_record_to_branch_file_with_polish_text(repo, capsys):
    payload = _skill_payload("clas5-quant", "kalibracja ąęśź", cwd=str(repo), session_id="abc")
    assert hook_main(json.dumps(payload, ensure_ascii=False).encode("utf-8")) == 0
    assert capsys.readouterr().out == ""

    lines = log_file_for_branch(repo, "runda-test").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["galaz"] == "runda-test"
    assert rec["skill"] == "clas5-quant"
    assert rec["argumenty"] == "kalibracja ąęśź"
    assert rec["sesja"] == "abc"
    assert rec["kto"] == "claude"


def test_hook_is_append_only(repo):
    for skill in ("clas5-runda", "clas5-quant"):
        _use_skill(repo, skill)
    records, bad = load_records(repo / LOG_DIR)
    assert [r["skill"] for r in records] == ["clas5-runda", "clas5-quant"]
    assert bad == 0


def test_round_merges_into_master_while_master_log_is_dirty(repo_with_master):
    """
    Błąd wykryty w przeglądzie przed scaleniem: przy JEDNYM pliku rejestru skill wczytany na
    master (np. do przeglądu) zmieniał plik w kopii roboczej, a runda zmieniała go w commitach
    — `git merge` odmawiał. Przy pliku na gałąź scalenie musi przejść.
    """
    repo = repo_with_master
    _git("checkout", "-q", "-b", "runda-x", cwd=repo)
    _use_skill(repo, "clas5-runda")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "runda", cwd=repo)

    _git("checkout", "-q", "master", cwd=repo)
    _use_skill(repo, "engineering:code-review")  # niezacommitowany wpis na master
    _git("merge", "-q", "--no-ff", "--no-edit", "runda-x", cwd=repo)  # check=True

    records, bad = load_records(repo / LOG_DIR)
    by_branch = {(r["galaz"], r["skill"]) for r in records}
    assert by_branch == {("runda-x", "clas5-runda"), ("master", "engineering:code-review")}
    assert bad == 0


def test_real_gitattributes_unions_appends_to_the_same_file(repo_with_master):
    """
    Rzadki przypadek: dwie sesje dopisują do pliku TEJ SAMEJ gałęzi w dwóch klonach. Bez
    `merge=union` scalenie kończy się konfliktem na końcu pliku. Test używa PRAWDZIWEGO
    `.gitattributes` projektu, więc pilnuje konfiguracji, a nie jej kopii.
    """
    repo = repo_with_master
    shared = log_file_for_branch(repo, "wspolna")
    append_record(shared, {"skill": "baza", "galaz": "wspolna"})
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "baza", cwd=repo)

    _git("checkout", "-q", "-b", "klon-a", cwd=repo)
    append_record(shared, {"skill": "skill-a", "galaz": "wspolna"})
    _git("commit", "-q", "-am", "a", cwd=repo)

    _git("checkout", "-q", "master", cwd=repo)
    append_record(shared, {"skill": "skill-b", "galaz": "wspolna"})
    _git("commit", "-q", "-am", "b", cwd=repo)

    _git("merge", "-q", "--no-edit", "klon-a", cwd=repo)  # check=True: konflikt = błąd
    records, bad = load_records(shared)
    assert sorted(r["skill"] for r in records) == ["baza", "skill-a", "skill-b"]
    assert bad == 0


# --------------------------------------------------------------------------- raport


def test_load_records_counts_corrupted_lines_instead_of_hiding_them(tmp_path):
    log = tmp_path / "rejestr.jsonl"
    log.write_text(
        json.dumps({"skill": "ok", "galaz": "b"}) + "\nśmieci\n" + json.dumps({"brak": 1}) + "\n\n",
        encoding="utf-8",
    )
    records, bad = load_records(log)
    assert [r["skill"] for r in records] == ["ok"]
    assert bad == 2


def test_load_records_reads_all_branch_files_in_time_order(tmp_path):
    append_record(
        tmp_path / "b.jsonl", {"skill": "drugi", "galaz": "b", "czas": "2026-09-23T10:00"}
    )
    append_record(
        tmp_path / "a.jsonl", {"skill": "trzeci", "galaz": "a", "czas": "2026-09-23T11:00"}
    )
    append_record(
        tmp_path / "a.jsonl", {"skill": "pierwszy", "galaz": "a", "czas": "2026-09-23T09:00"}
    )
    records, bad = load_records(tmp_path)
    assert [r["skill"] for r in records] == ["pierwszy", "drugi", "trzeci"]
    assert bad == 0


def test_load_records_missing_path_is_empty(tmp_path):
    assert load_records(tmp_path / "nie-ma.jsonl") == ([], 0)


def test_report_filters_one_branch_and_summarizes():
    recs = [
        {"skill": "clas5-runda", "galaz": "runda-x", "kto": "claude", "czas": "t1"},
        {"skill": "clas5-quant", "galaz": "runda-x", "kto": "claude", "czas": "t2"},
        {"skill": "clas5-runda", "galaz": "runda-x", "kto": "claude", "czas": "t3"},
        {"skill": "dataviz", "galaz": "inna", "kto": "claude", "czas": "t4"},
    ]
    one = render_report(recs, 0, branch="runda-x")
    assert "`dataviz`" not in one
    assert "Razem: 3 wczytania, 2 różne skille: `clas5-quant`, `clas5-runda`." in one

    summary = render_report(recs, 0)
    assert "| `runda-x` | 3 |" in summary
    assert "| `inna` | 1 | `dataviz` |" in summary


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (1, "1 skill"),
        (2, "2 skille"),
        (4, "4 skille"),
        (5, "5 skilli"),
        (12, "12 skilli"),
        (22, "22 skille"),
        (25, "25 skilli"),
    ],
)
def test_polish_plural_forms_in_report(n, expected):
    assert _plural(n, "skill", "skille", "skilli") == expected


def test_report_for_branch_without_entries_says_so():
    assert "Brak wpisów" in render_report([], 0, branch="nowa")


def test_report_warns_about_corrupted_lines():
    assert "2 uszkodzonych wierszy" in render_report([], 2)


def test_report_escapes_pipe_in_args():
    recs = [{"skill": "s", "galaz": "b", "kto": "claude", "czas": "t", "argumenty": "a|b"}]
    assert "a\\|b" in render_report(recs, 0, branch="b")


def test_cli_raport_prints_report_for_file_and_directory(tmp_path, capsys):
    append_record(tmp_path / "g.jsonl", {"skill": "clas5-quant", "galaz": "g", "kto": "claude"})
    for target in (tmp_path / "g.jsonl", tmp_path):
        assert main(["raport", "--plik", str(target), "--galaz", "g"]) == 0
        assert "`clas5-quant`" in capsys.readouterr().out


# --------------------------------------------------------------------------- konfiguracja projektu


def test_project_settings_register_both_hooks():
    """Cicha utrata hooka = cicha utrata audytu. Ten test pilnuje, że oba wpisy istnieją."""
    settings = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks = settings["hooks"]

    skill_cmds = [
        h["command"]
        for entry in hooks["PostToolUse"]
        if entry.get("matcher") == "Skill"
        for h in entry["hooks"]
    ]
    expansion_cmds = [
        h["command"] for entry in hooks["UserPromptExpansion"] for h in entry["hooks"]
    ]
    for cmds in (skill_cmds, expansion_cmds):
        assert any("tools/skill_audit.py" in c and c.rstrip().endswith("|| true") for c in cmds)


def test_gitattributes_declares_union_merge_for_branch_logs():
    rules = [r.split() for r in (REPO / ".gitattributes").read_text(encoding="utf-8").splitlines()]
    pattern = (LOG_DIR / "*.jsonl").as_posix()
    assert any(r and r[0] == pattern and "merge=union" in r for r in rules)
