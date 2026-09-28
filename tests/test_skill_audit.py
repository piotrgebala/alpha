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

import csv
import json
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import skill_audit as sa
from tools.skill_audit import (
    CSV_BUFFER_NAME,
    CSV_COLUMNS,
    CSV_NAME,
    LOG_DIR,
    UNKNOWN_COMMAND,
    _plural,
    append_csv,
    append_record,
    build_record,
    csv_row,
    extract_skill_use,
    hook_main,
    load_records,
    log_file_for_branch,
    main,
    rebuild_csv,
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
    """Repo z commitem bazowym na `master` i PRAWDZIWYMI `.gitattributes`/`.gitignore`."""
    _git("checkout", "-q", "-b", "master", cwd=repo)
    (repo / ".gitattributes").write_bytes((REPO / ".gitattributes").read_bytes())
    (repo / ".gitignore").write_bytes((REPO / ".gitignore").read_bytes())
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


# --------------------------------------------------------------------------- monitor CSV


def _read_csv(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.reader(fh, delimiter=";"))


def test_csv_row_splits_date_and_time_in_column_order():
    rec = build_record(
        extract_skill_use(_skill_payload("clas5-quant", "kalibracja")),
        now=NOW,
        branch="runda-x",
        session="s1",
    )
    row = dict(zip(CSV_COLUMNS, csv_row(rec), strict=True))
    assert row["data"] == "2026-09-23"
    assert row["godzina"] == "10:00:00"
    assert (row["skill"], row["galaz"], row["kto"]) == ("clas5-quant", "runda-x", "claude")


@pytest.mark.parametrize("dangerous", ["=HYPERLINK(1)", "+1", "-cmd", "@SUM(A1)", "\tx"])
def test_csv_neutralizes_cells_excel_would_run_as_formulas(dangerous):
    rec = {"skill": "s", "argumenty": dangerous, "czas": "2026-09-23T10:00:00+02:00"}
    cell = dict(zip(CSV_COLUMNS, csv_row(rec), strict=True))["argumenty"]
    assert cell == "'" + dangerous


def test_hook_writes_excel_friendly_csv(repo):
    payload = _skill_payload("clas5-quant", "kalibracja ąęśź; z średnikiem", cwd=str(repo))
    hook_main(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    path = repo / LOG_DIR / CSV_NAME
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")  # BOM: polskie znaki w Excelu
    header, row = _read_csv(path)
    assert header == list(CSV_COLUMNS)
    got = dict(zip(header, row, strict=True))
    assert got["argumenty"] == "kalibracja ąęśź; z średnikiem"  # średnik w cudzysłowie
    assert got["galaz"] == "runda-test"


def test_hook_in_worktree_writes_csv_to_main_repo(repo_with_master, tmp_path_factory):
    repo = repo_with_master
    wt = tmp_path_factory.mktemp("wt") / "runda"
    _git("worktree", "add", "-q", "-b", "runda-wt", str(wt), cwd=repo)
    hook_main(json.dumps(_skill_payload("clas5-runda", cwd=str(wt))))

    assert log_file_for_branch(wt, "runda-wt").exists()  # audyt: JSONL w worktree rundy
    assert not (wt / LOG_DIR / CSV_NAME).exists()  # monitor: JEDEN plik w głównym repo
    rows = _read_csv(repo / LOG_DIR / CSV_NAME)
    assert [r[CSV_COLUMNS.index("skill")] for r in rows[1:]] == ["clas5-runda"]


def test_locked_csv_rows_wait_in_buffer_and_are_flushed_in_order(tmp_path):
    path = tmp_path / "runs" / "skille" / CSV_NAME
    path.mkdir(parents=True)  # katalog w miejscu pliku = zapis niemożliwy, jak przy Excelu
    first = csv_row({"skill": "pierwszy", "czas": "2026-09-23T10:00:00+02:00"})
    assert append_csv(path, [first]) is False
    assert (path.parent / CSV_BUFFER_NAME).exists()

    path.rmdir()  # „Excel zamknięty”
    second = csv_row({"skill": "drugi", "czas": "2026-09-23T10:05:00+02:00"})
    assert append_csv(path, [second]) is True
    skills = [r[CSV_COLUMNS.index("skill")] for r in _read_csv(path)[1:]]
    assert skills == ["pierwszy", "drugi"]
    assert not (path.parent / CSV_BUFFER_NAME).exists()


def test_csv_failure_never_blocks_the_jsonl_audit_entry(repo, capsys):
    (repo / LOG_DIR / CSV_NAME).mkdir(parents=True)
    (repo / LOG_DIR / CSV_BUFFER_NAME).mkdir(parents=True)  # nawet bufor niezapisywalny
    assert hook_main(json.dumps(_skill_payload("clas5-quant", cwd=str(repo)))) == 0
    assert capsys.readouterr().out == ""
    records, _ = load_records(repo / LOG_DIR)
    assert [r["skill"] for r in records] == ["clas5-quant"]


def test_rebuild_csv_restores_full_history_from_jsonl(repo_with_master, capsys, monkeypatch):
    repo = repo_with_master
    skille = repo / LOG_DIR
    append_record(skille / "b.jsonl", {"skill": "drugi", "galaz": "b", "czas": "2026-09-23T11:00"})
    append_record(
        skille / "a.jsonl", {"skill": "pierwszy", "galaz": "a", "czas": "2026-09-23T09:00"}
    )
    (skille / CSV_NAME).write_text("stary;smieci\n", encoding="utf-8")
    (skille / CSV_BUFFER_NAME).write_text("x\n", encoding="utf-8")

    path, count = rebuild_csv(repo)
    assert count == 2
    rows = _read_csv(path)
    assert rows[0] == list(CSV_COLUMNS)
    assert [r[CSV_COLUMNS.index("skill")] for r in rows[1:]] == ["pierwszy", "drugi"]
    assert not (skille / CSV_BUFFER_NAME).exists()

    monkeypatch.chdir(repo)
    assert main(["csv"]) == 0
    assert "2 wiersze" in capsys.readouterr().out


def test_csv_monitor_never_shows_up_in_git_status(repo_with_master):
    repo = repo_with_master
    hook_main(json.dumps(_skill_payload("clas5-quant", cwd=str(repo))))
    status = _git("status", "--porcelain", "--untracked-files=all", cwd=repo).stdout
    assert "master.jsonl" in status  # audyt JSONL: do commita
    assert ".csv" not in status  # monitor CSV: lokalny, ignorowany


def test_cli_csv_on_locked_file_explains_instead_of_crashing(repo_with_master, capsys, monkeypatch):
    repo = repo_with_master
    (repo / LOG_DIR / CSV_NAME).mkdir(parents=True)  # plik niezapisywalny, jak otwarty w Excelu
    monkeypatch.chdir(repo)
    assert main(["csv"]) == 1
    assert "Excelu" in capsys.readouterr().err


# --------------------------------------------------------------------------- rejestracja bez ponownego wczytania
# Zasada 19 (decyzja użytkownika 2026-09-28): dowodem jest zapis rozmowy sesji, nie deklaracja Claude'a.

_T0 = "2026-09-28T10:00:00.000Z"
_KOMPRESJA = {
    "type": "system",
    "subtype": "compact_boundary",
    "timestamp": "2026-09-28T11:00:00.000Z",
}


def _wczytanie(name: str, ts: str = _T0, sidechain: bool = False) -> dict:
    blok = {"type": "tool_use", "name": "Skill", "input": {"skill": name}}
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "timestamp": ts,
        "message": {"content": [blok]},
    }


def _zapis(katalog: Path, wpisy: list[dict]) -> Path:
    sciezka = katalog / "sesja.jsonl"
    sciezka.write_text("\n".join(json.dumps(w) for w in wpisy) + "\n", encoding="utf-8")
    return sciezka


def _rejestruj(repo: Path, skill: str, wpisy: list[dict], sesja: str = "s1") -> tuple[int, str]:
    teraz = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
    return sa.register_without_reload(repo, skill, sesja, _zapis(repo, wpisy), now=teraz)


def _wpisy_galezi(repo: Path) -> list[dict]:
    return sa.load_records(sa.log_file_for_branch(repo, "runda-test"))[0]


def test_rejestracja_skilla_z_kontekstu_sesji(repo):
    kod, _ = _rejestruj(repo, "engineering:code-review", [_wczytanie("engineering:code-review")])
    assert kod == 0
    (wpis,) = _wpisy_galezi(repo)
    assert wpis["zdarzenie"] == sa.REJESTRACJA and wpis["skill"] == "engineering:code-review"
    assert wpis["sesja"] == "s1" and wpis["galaz"] == "runda-test" and wpis["kto"] == "claude"
    assert "bez ponownego wczytania" in wpis["argumenty"] and _T0 in wpis["argumenty"]
    assert (
        _rejestruj(repo, "engineering:code-review", [_wczytanie("engineering:code-review")])[0] == 0
    )
    assert len(_wpisy_galezi(repo)) == 1  # drugi raz nic nie dopisuje


def test_rejestracja_po_nazwie_bez_prefiksu_i_z_komendy_uzytkownika(repo):
    tresc = "<command-name>/anthropic-skills:ta-toolkit</command-name>"
    komenda = {"type": "user", "timestamp": _T0, "message": {"content": tresc}}
    assert _rejestruj(repo, "clas5-quant", [_wczytanie("anthropic-skills:clas5-quant")])[0] == 0
    assert _rejestruj(repo, "ta-toolkit", [komenda])[0] == 0
    nazwy = [w["skill"] for w in _wpisy_galezi(repo)]
    assert nazwy == ["anthropic-skills:clas5-quant", "anthropic-skills:ta-toolkit"]


@pytest.mark.parametrize(
    "wpisy",
    [
        [],
        [_wczytanie("dataviz")],
        [_wczytanie("engineering:code-review", sidechain=True)],  # tylko w subagencie
        [_wczytanie("engineering:code-review"), _KOMPRESJA],  # streszczenie po wczytaniu
    ],
)
def test_odmowa_gdy_skilla_nie_ma_w_kontekscie(repo, wpisy):
    kod, komunikat = _rejestruj(repo, "engineering:code-review", wpisy)
    assert kod == 1 and "zasada 19" in komunikat
    assert _wpisy_galezi(repo) == []


def test_wczytanie_po_streszczeniu_znow_wystarcza(repo):
    ponownie = _wczytanie("engineering:code-review", "2026-09-28T11:30:00.000Z")
    wpisy = [_wczytanie("engineering:code-review"), _KOMPRESJA, ponownie]
    assert _rejestruj(repo, "engineering:code-review", wpisy)[0] == 0


def test_nazwy_skilli_z_roznych_wtyczek_sie_nie_myla():
    assert sa._same_skill("anthropic-skills:clas5-quant", "clas5-quant")
    assert sa._same_skill("clas5-quant", "anthropic-skills:clas5-quant")
    assert not sa._same_skill("data:analyze", "x:analyze")


def test_odmowa_bez_sesji_albo_bez_zapisu(repo):
    teraz = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
    assert sa.register_without_reload(repo, "x", "", repo / "brak.jsonl", now=teraz)[0] == 1
    assert sa.register_without_reload(repo, "x", "s1", None, now=teraz)[0] == 1
    assert _wpisy_galezi(repo) == []


def test_zapis_sesji_szukany_w_katalogu_konfiguracji(tmp_path):
    (tmp_path / "projects" / "-repo").mkdir(parents=True)
    zapis = tmp_path / "projects" / "-repo" / "abc-1.jsonl"
    zapis.write_text("", encoding="utf-8")
    assert sa.session_transcript("abc-1", tmp_path) == zapis
    assert sa.session_transcript("../abc-1", tmp_path) is None
    assert sa.session_transcript("", tmp_path) is None


def test_polecenie_zarejestruj_przez_cli(repo, monkeypatch):
    projekt = repo / "konf" / "projects" / "-repo"
    projekt.mkdir(parents=True)
    _zapis(projekt, [_wczytanie("engineering:code-review")]).rename(projekt / "s9.jsonl")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(repo / "konf"))
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    assert sa.main(["zarejestruj", "engineering:code-review"]) == 1  # bez sesji: odmowa
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s9")
    assert sa.main(["zarejestruj", "engineering:code-review"]) == 0
    assert [w["sesja"] for w in _wpisy_galezi(repo)] == ["s9"]
    raport = sa.render_report(_wpisy_galezi(repo), 0, "runda-test")
    assert "W tym 1 bez ponownego wczytania" in raport


_ZDARZENIE = st.sampled_from(["A", "B", "A-sub", "kompresja", "szum"])


@settings(max_examples=80, deadline=None)
@given(zdarzenia=st.lists(_ZDARZENIE, max_size=10))
def test_last_load_zgodny_z_modelem_odniesienia(zdarzenia):
    """Właściwość: wynik = ostatnie wczytanie w głównej rozmowie; streszczenie liczy się tylko po nim."""
    wpisy, znaleziony, streszczony = [], False, False
    for i, z in enumerate(zdarzenia):
        ts = f"2026-09-28T10:{i:02d}:00.000Z"
        if z == "A":
            wpisy.append(_wczytanie("engineering:code-review", ts))
            znaleziony, streszczony = True, False
        elif z == "B":
            wpisy.append(_wczytanie("dataviz", ts))
        elif z == "A-sub":
            wpisy.append(_wczytanie("engineering:code-review", ts, sidechain=True))
        elif z == "kompresja":
            wpisy.append({**_KOMPRESJA, "timestamp": ts})
            streszczony = streszczony or znaleziony
        else:
            wpisy.append({"type": "user", "message": {"content": "code-review bez wczytania"}})
    with tempfile.TemporaryDirectory() as katalog:
        nazwa, _, po = sa.last_load(_zapis(Path(katalog), wpisy), "engineering:code-review")
    assert (nazwa is not None) == znaleziony
    assert po == (znaleziony and streszczony)
