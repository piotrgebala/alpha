"""
audyt_hook.py

Hook audytowy wykonawców Claude Code (zadanie 002, `docs/rag/13_izolacja_wykonawcow.md`). Działa na
zdarzeniu `PreToolUse` dla narzędzi Bash, Read, Write, Edit, MultiEdit, NotebookEdit, WebFetch
oraz Grep i Glob (przeszukanie katalogu, np. `~/.ssh`, to też odczyt).
Każde wywołanie dopisuje JEDEN wiersz JSON do `~/.clas5_audyt/RRRR-MM-DD.jsonl` (data UTC; katalog
0700, plik 0600, tworzone przez hook; zmienna `CLAS5_AUDYT_DIR` zmienia katalog — testy). Wiersz ma
listę `flagi`; pusta lista = nic podejrzanego. Flagi:

- `siec_poza_lista` — polecenie sieciowe (curl, wget, git push/fetch/pull/clone/ls-remote,
  pip install, python z requests/urllib/socket/…, nc, ssh, scp, sftp, rsync, telnet, `gh`
  — domyślnie `api.github.com`, WebFetch) do hosta spoza `config/audyt_hosty.yaml` (hosty
  w polu `hosty_spoza_listy`);
- `siec_host_nieznany` — polecenie sieciowe, którego hosta nie da się ustalić z tekstu polecenia
  (np. `python -c` z `requests` i adresem w zmiennej);
- `zapis_poza_repo` — zapis (Write/Edit/MultiEdit/NotebookEdit, a w Bash: `>`/`>>`, `tee`, cel
  `cp`/`mv`, `sed -i`, `curl -o`, `wget -O`; ścieżki względne liczone po `cd` w poleceniu) poza
  repozytorium bieżącego katalogu (`cwd` z wejścia hooka; dla worktree — poza worktree i poza
  `runs/` oraz `data/` głównego checkoutu);
- `zapis_tmp` — zapis w katalogu tymczasowym (`/tmp`, `$TMPDIR`): wspólny zasób wielu sesji,
  czyli możliwy boczny kanał; osobna flaga, bo scratchpad sesji leży właśnie tam;
- `poswiadczenia` — dostęp (odczyt albo zapis) do `~/.ssh`, `.env`, `*.pem`, `*.key`, plików
  z `key`/`secret`/`token`/`credentials` w nazwie, `~/.config/gh`, `~/.git-credentials`, `.netrc`…;
- `dziennik_audytu` — narzędzie dotyka katalogu audytu (odczyt lub zapis własnego nadzoru);
- `wejscie_nieczytelne` / `blad_analizy` — hook nie zrozumiał wejścia; wiersz i tak powstaje,
  więc zły JSON nie jest sposobem na zniknięcie z dziennika.

TRYB PIERWSZY: TYLKO OZNACZA, NIGDY NIE BLOKUJE. Hook nie wypisuje nic na stdout (żadnej decyzji
`permissionDecision`), zawsze kończy się kodem 0, a każdy własny błąd połyka — tak jak
`frozen_guard.py`, `skill_audit.py` i `straznik_kontekstu.py`. Blokowanie dopiero po tygodniu
obserwacji i za decyzją użytkownika (plan w docs/rag/13).

Co trafia do dziennika: czas, sesja, id i typ agenta, cwd, narzędzie, skrót polecenia (maks.
`MAKS_ZNAKOW` znaków, z maskowaniem wzorców typu token/klucz/hasło/Bearer/dane w URL), ścieżka lub
adres, flagi, hosty i ścieżki, które flagi wywołały. NIGDY treść plików (`content`, `new_string`
i podobne pola nie są czytane) ani nieobcięte polecenie.

Analiza jest tekstowa (własny, mały tokenizer powłoki): wykrywa typowe przypadki, nie jest
piaskownicą. Zagnieżdżone `bash -c '…'`, `sh -c '…'` i `eval …` są analizowane tą samą funkcją
(do `MAKS_ZAGNIEZDZENIA` poziomów). Obejście przez np. `bash -c "$(echo … | base64 -d)"` nie
zostanie rozpoznane jako sieć — dlatego docelowa granica to osobny użytkownik systemu
(docs/rag/13), a hook to widoczność.

Szybkość: tylko biblioteka standardowa, bez YAML (lista hostów w prostym formacie czytana
ręcznie); podproces `git remote get-url` tylko dla `git push/fetch/pull` bez adresu w poleceniu.

Użycie:
    py tools/audyt_hook.py hook      # tryb hooka (JSON zdarzenia PreToolUse na stdin)
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLIK_HOSTOW = REPO / "config" / "audyt_hosty.yaml"
MAKS_ZNAKOW = 300  # skrót polecenia / ścieżki / adresu w dzienniku

F_SIEC = "siec_poza_lista"
F_SIEC_NIEZNANY = "siec_host_nieznany"
F_ZAPIS = "zapis_poza_repo"
F_TMP = "zapis_tmp"
F_POSW = "poswiadczenia"
F_AUDYT = "dziennik_audytu"
F_WEJSCIE = "wejscie_nieczytelne"
F_BLAD = "blad_analizy"

NARZEDZIA_ZAPISU = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
POLE_SCIEZKI = {"NotebookEdit": "notebook_path"}  # reszta narzędzi plikowych: `file_path`

# --- maskowanie sekretów w skrócie polecenia ------------------------------------------------------
_MASKI = (
    # hasło przyklejone do `-p` tylko tam, gdzie `-p<coś>` znaczy hasło: mysql/mariadb i sshpass;
    # `-p` z odstępem (pytanie o hasło) i `-P` (port) zostają; psql: `-p` to port — nie maskujemy
    (
        re.compile(
            r"((?:^|[\s;&|(/])(?:mysql[a-z_-]*|mariadb[a-z_-]*)\b"
            r"(?:[^;&|\n]*?\s)?-p['\"]?)([^\s;&|'\"]+)"
        ),
        r"\1***",
    ),
    # sshpass: `-p hasło` i `-phasło` (hasło zawsze po `-p`)
    (re.compile(r"(\bsshpass\s+(?:-[^p\s]\S*\s+)*-p\s*['\"]?)([^\s'\"]+)"), r"\1***"),
    (re.compile(r"(?i)(authorization\s*:\s*)(bearer\s+|basic\s+|token\s+)?[^\s'\"]+"), r"\1\2***"),
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1***"),
    (re.compile(r"(?i)(\b[a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@"), r"\1***:***@"),
    # curl/wget `-u user:haslo`, `--user=user:haslo`, `--proxy-user …` — maskowane tylko w formie z „:”
    (
        re.compile(r"(?i)((?:^|\s)(?:-u|-U|--user|--proxy-user)[ =]?['\"]?[^\s:'\"]*:)[^\s'\"]+"),
        r"\1***",
    ),
    (
        re.compile(
            r"(?i)(--?[a-z0-9_-]*(?:key|token|secret|password|passwd|pass|pwd)[a-z0-9_-]*[ =])"
            r"(['\"]?)[^\s'\"]+"
        ),
        r"\1\2***",
    ),
    (
        re.compile(
            r"(?i)([a-z0-9_]*(?:key|token|secret|password|passwd|pwd|signature|auth)[a-z0-9_]*"
            r"['\"]?\s*[=:]\s*)(['\"]?)[^\s'\"&,;)}]+"
        ),
        r"\1\2***",
    ),
    (
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}"
            r"|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})"
        ),
        "***",
    ),
    # długi ciąg z cyframi i literami (klucz, podpis HMAC, hash) — ścieżek z „/” i kropek nie łapie
    (
        re.compile(
            r"(?<![\w/.-])(?=[A-Za-z0-9+_-]*\d)(?=[A-Za-z0-9+_-]*[A-Za-z])[A-Za-z0-9+_-]{32,}=*"
        ),
        "***",
    ),
)


def maskuj(tekst: str, limit: int = MAKS_ZNAKOW) -> str:
    """Maskuje wzorce sekretów, POTEM obcina (sekret na granicy cięcia nie wycieka połową)."""
    for wzorzec, zamiana in _MASKI:
        tekst = wzorzec.sub(zamiana, tekst)
    return tekst if len(tekst) <= limit else tekst[:limit] + "…"


# --- lista hostów ---------------------------------------------------------------------------------
def wczytaj_hosty(sciezka: str | Path | None = None) -> frozenset[str]:
    """Hosty z listy `hosty:` pliku konfiguracyjnego (prosty podzbiór YAML). Brak pliku → pusta
    lista, czyli KAŻDE polecenie sieciowe zostanie oznaczone (bezpieczniejszy kierunek błędu)."""
    sciezka = sciezka or os.environ.get("CLAS5_AUDYT_HOSTY") or PLIK_HOSTOW
    try:
        tekst = Path(sciezka).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return frozenset()
    hosty, w_liscie = set(), False
    for linia in tekst.splitlines():
        bez = linia.split("#", 1)[0].rstrip()
        if not bez.strip():
            continue
        if not bez[0].isspace() and not bez.startswith("-"):
            w_liscie = bez.strip() == "hosty:"
            continue
        element = bez.strip()
        if w_liscie and element.startswith("- "):
            host = element[2:].strip().strip("\"'").lower()
            if host:
                hosty.add(host)
    return frozenset(hosty)


def normalizuj_host(host: str) -> str:
    return host.strip().strip("[]").rstrip(".").lower()


def host_dozwolony(host: str, hosty: frozenset[str]) -> bool:
    host = normalizuj_host(host)
    if host in hosty:
        return True
    return any(w.startswith("*.") and host.endswith(w[1:]) for w in hosty)


# --- tokenizer powłoki ----------------------------------------------------------------------------
SEPARATORY = set(";&|()\n`")


def segmenty(polecenie: str) -> list[list[str]]:
    """Dzieli polecenie na proste polecenia (po niecytowanych ; & | ( ) ` i nowej linii) i słowa
    (z usuniętymi cudzysłowami). Przekierowania jako osobne słowa `>`, `>>`, `<`, `<<`; `>&N`
    (duplikacja deskryptora) pomijane. Nigdy nie rzuca — niedomknięty cudzysłów kończy słowo."""
    wynik: list[list[str]] = []
    slowa: list[str] = []
    bufor: list[str] = []
    jest_slowo = False
    cudzyslow = None
    i, n = 0, len(polecenie)

    def zamknij_slowo():
        nonlocal bufor, jest_slowo
        if jest_slowo:
            slowa.append("".join(bufor))
        bufor, jest_slowo = [], False

    def zamknij_segment():
        nonlocal slowa
        zamknij_slowo()
        if slowa:
            wynik.append(slowa)
        slowa = []

    while i < n:
        c = polecenie[i]
        if cudzyslow:
            if c == cudzyslow:
                cudzyslow = None
            elif c == "\\" and cudzyslow == '"' and i + 1 < n and polecenie[i + 1] in '"\\$`':
                i += 1
                bufor.append(polecenie[i])
            else:
                bufor.append(c)
        elif c in "'\"":
            cudzyslow, jest_slowo = c, True
        elif c == "\\" and i + 1 < n:
            i += 1
            if polecenie[i] != "\n":
                bufor.append(polecenie[i])
                jest_slowo = True
        elif c in " \t\r":
            zamknij_slowo()
        elif c in SEPARATORY:
            zamknij_segment()
        elif c in "<>":
            zamknij_slowo()
            znak = c
            if i + 1 < n and polecenie[i + 1] == c:
                i += 1
                znak += c
            if c == ">" and i + 1 < n and polecenie[i + 1] == "&":  # 2>&1: nie plik
                i += 2
                while i < n and (polecenie[i].isdigit() or polecenie[i] == "-"):
                    i += 1
                continue
            if c == ">" and i + 1 < n and polecenie[i + 1] == "|":
                i += 1
            slowa.append(znak)
        else:
            bufor.append(c)
            jest_slowo = True
        i += 1
    zamknij_segment()
    return wynik


OPAKOWANIA = {"sudo", "env", "time", "nohup", "nice", "exec", "command", "xargs", "stdbuf", "!"}
_PRZYPISANIE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def program_i_argumenty(slowa: list[str]) -> tuple[str, list[str]]:
    """Pomija przypisania zmiennych i opakowania (sudo, env, timeout N, xargs…) → (program, args)."""
    i = 0
    while i < len(slowa):
        s = slowa[i]
        nazwa = s.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if _PRZYPISANIE.match(s) or (s.startswith("-") and i > 0):
            i += 1
        elif nazwa in OPAKOWANIA:
            i += 1
        elif nazwa == "timeout":
            i += 1
            while i < len(slowa) and (slowa[i].startswith("-") or slowa[i][:1].isdigit()):
                i += 1
        else:
            return nazwa, slowa[i + 1 :]
    return "", []


# --- sieć ---------------------------------------------------------------------------------------
_URL = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://(?:[^/\s@'\"]*@)?(\[[0-9a-f:.]+\]|[a-z0-9._-]+)")
_SCP = re.compile(r"^(?:[^@/\s]+@)?([A-Za-z0-9._-]+|\[[0-9a-fA-F:.]+\]):(?!//)")
_DOMENA = re.compile(r"(?i)^(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?:/.*)?$")
_BIBLIOTEKI_SIECI = re.compile(
    r"\b(requests|urllib|urllib3|socket|http\.client|httpx|aiohttp|websockets?|ftplib|smtplib"
    r"|ccxt|paramiko)\b"
)
PYTHON = re.compile(r"^(python(\d+(\.\d+)?)?|py|pypy3?)(\.exe)?$")
CURL_OPCJE_Z_ARG = {
    "-o", "--output", "-H", "--header", "-d", "--data", "--data-raw", "--data-binary", "-u",
    "--user", "-A", "--user-agent", "-e", "--referer", "-b", "--cookie", "-c", "--cookie-jar",
    "-T", "--upload-file", "-K", "--config", "-w", "--write-out", "-O", "-P", "-X", "--request",
    "--output-document", "--directory-prefix", "-F", "--form", "-m", "--max-time", "-r", "--range",
}  # fmt: skip
SSH_OPCJE_Z_ARG = set("-b -c -D -E -e -F -I -i -J -L -l -m -O -o -p -P -Q -R -S -W -w -B".split())


def hosty_z_tekstu(tekst: str) -> list[str]:
    return [normalizuj_host(m.group(1)) for m in _URL.finditer(tekst)]


def _pierwszy_argument(args: list[str], opcje_z_arg: set[str]) -> str | None:
    pomin = False
    for a in args:
        if pomin:
            pomin = False
        elif a in opcje_z_arg:
            pomin = True
        elif not a.startswith("-") and a not in ("<", "<<", ">", ">>"):
            return a
    return None


def _host_ssh(cel: str) -> str:
    cel = cel.split("@", 1)[-1]
    if cel.startswith("["):
        return normalizuj_host(cel.split("]", 1)[0])
    return normalizuj_host(cel.split(":", 1)[0])


def _url_zdalnego(cwd: str, nazwa: str) -> str | None:
    """Adres zdalnego repozytorium z konfiguracji gita (tylko `git remote get-url`, bez sieci)."""
    import subprocess  # leniwie: potrzebny tylko dla git push/fetch/pull bez adresu

    try:
        wynik = subprocess.run(
            ["git", "-C", cwd or ".", "remote", "get-url", nazwa],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return wynik.stdout.strip() or None if wynik.returncode == 0 else None


def _hosty_git_url(url: str) -> list[str]:
    hosty = hosty_z_tekstu(url)
    if not hosty and (m := _SCP.match(url)):
        hosty = [normalizuj_host(m.group(1))]
    return hosty


def siec_w_segmencie(
    program: str, args: list[str], cale: str, cwd: str
) -> tuple[bool, list[str]] | None:
    """None = segment nie jest poleceniem sieciowym; inaczej (host_znany, hosty)."""
    if program in ("curl", "wget"):
        hosty = hosty_z_tekstu(" ".join(args))
        if not hosty:
            poprzedni = ""
            for a in args:
                if not a.startswith("-") and poprzedni not in CURL_OPCJE_Z_ARG and _DOMENA.match(a):
                    hosty.append(normalizuj_host(a.split("/", 1)[0].split(":", 1)[0]))
                poprzedni = a
        return bool(hosty), hosty
    if program in ("nc", "ncat", "netcat", "telnet"):
        host = _pierwszy_argument(args, {"-p", "-s", "-w", "-i", "-x", "-X", "-e", "-c"})
        return (True, [normalizuj_host(host)]) if host else (False, [])
    if program in ("ssh", "sftp"):
        cel = _pierwszy_argument(args, SSH_OPCJE_Z_ARG)
        return (True, [_host_ssh(cel)]) if cel else (False, [])
    if program in ("scp", "rsync"):
        hosty = hosty_z_tekstu(" ".join(args))
        for a in args:
            if not a.startswith("-") and (m := _SCP.match(a)) and "/" not in m.group(1):
                hosty.append(normalizuj_host(m.group(1)))
        if program == "rsync" and not hosty:
            return None  # rsync lokalny
        return bool(hosty), hosty
    if program == "git":
        return _siec_git(args, cwd)
    if program == "gh":  # GitHub CLI: każde polecenie poza pomocą/wersją idzie do API GitHuba
        if not args or args[0] in ("help", "version", "--help", "-h", "--version", "completion"):
            return None
        for j, a in enumerate(args):
            if a.startswith("--hostname="):
                return True, [normalizuj_host(a.split("=", 1)[1])]
            if a == "--hostname" and j + 1 < len(args):
                return True, [normalizuj_host(args[j + 1])]
        return True, ["api.github.com"]
    if program in ("pip", "pip3") or (PYTHON.match(program) and args[:2] == ["-m", "pip"]):
        if PYTHON.match(program):
            args = args[2:]
        return _siec_pip(args)
    if program == "uv" and args[:2] == ["pip", "install"]:
        return _siec_pip(args[1:])
    if PYTHON.match(program):
        kod = None
        if "-c" in args and args.index("-c") + 1 < len(args):
            kod = args[args.index("-c") + 1]
        elif "-" in args or "<<" in args or "<" in args:
            kod = cale  # heredoc / skrypt ze stdin: treść jest w całym poleceniu
        if kod is None or not _BIBLIOTEKI_SIECI.search(kod):
            return None
        hosty = hosty_z_tekstu(kod)
        return bool(hosty), hosty
    return None


def _siec_git(args: list[str], cwd: str) -> tuple[bool, list[str]] | None:
    i, katalog = 0, cwd
    while i < len(args) and args[i].startswith("-"):
        if args[i] in ("-C", "-c", "--git-dir", "--work-tree") and i + 1 < len(args):
            if args[i] == "-C":
                katalog = os.path.join(cwd or ".", args[i + 1])
            i += 1
        i += 1
    if i >= len(args) or args[i] not in ("push", "fetch", "pull", "clone", "ls-remote"):
        return None
    reszta = [a for a in args[i + 1 :] if not a.startswith("-")]
    for a in reszta:
        if hosty := _hosty_git_url(a):
            return True, hosty
    if args[i] == "clone":
        return (False, []) if reszta else None  # clone lokalnej ścieżki nie jest siecią
    nazwa = reszta[0] if reszta and "/" not in reszta[0] else "origin"
    url = _url_zdalnego(katalog, nazwa)
    if url is None:
        return False, []
    hosty = _hosty_git_url(url)
    if not hosty and (url.startswith(("/", ".", "file:")) or os.path.isabs(url)):
        return None  # zdalne repo lokalne
    return bool(hosty), hosty


def _siec_pip(args: list[str]) -> tuple[bool, list[str]] | None:
    if not args or args[0] not in ("install", "download", "wheel"):
        return None
    hosty = hosty_z_tekstu(" ".join(args))
    if not any(a.startswith(("-i", "--index-url", "--extra-index-url")) for a in args):
        hosty.append("pypi.org")
    return True, hosty


# --- ścieżki --------------------------------------------------------------------------------------
_NAZWY_POSW = {
    ".git-credentials", ".netrc", "_netrc", ".pgpass", ".pypirc", ".npmrc", "credentials",
    "credentials.json", "credentials.yaml", "credentials.yml", "authorized_keys", "known_hosts",
}  # fmt: skip
_KATALOGI_POSW = {".ssh", ".gnupg", ".aws", ".kube", ".docker"}
_ROZSZERZENIA_POSW = (".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".ppk", ".asc", ".gpg")
_SLOWA_POSW = re.compile(
    r"(?i)(^|[._-])(api[_-]?)?(keys?|secrets?|tokens?|credentials?|passwords?)([._-]|$)"
)


def rozwin(sciezka: str, cwd: str) -> str:
    """Ścieżka bezwzględna z rozwiniętym `~`/`$HOME` i rozwiązanymi dowiązaniami."""
    dom = os.path.expanduser("~")
    s = sciezka.replace("${HOME}", dom).replace("$HOME", dom)
    s = os.path.expanduser(s)
    if not os.path.isabs(s):
        s = os.path.join(cwd or os.getcwd(), s)
    return os.path.realpath(s)


def czy_poswiadczenia(sciezka: str) -> bool:
    czesci = sciezka.replace("\\", "/").lower().split("/")
    nazwa = czesci[-1]
    if _KATALOGI_POSW & set(czesci[:-1]) or nazwa in _KATALOGI_POSW:
        return True
    if "/.config/gh" in "/".join(czesci) or nazwa in _NAZWY_POSW:
        return True
    if nazwa == ".env" or nazwa.startswith(".env.") or nazwa.endswith(".env"):
        return True
    if nazwa.endswith(_ROZSZERZENIA_POSW) or nazwa.startswith(("id_rsa", "id_ed25519", "id_ecdsa")):
        return True
    return bool(_SLOWA_POSW.search(nazwa))


def _pod(sciezka: str, katalog: str) -> bool:
    katalog = katalog.rstrip(os.sep) or os.sep
    return sciezka == katalog or sciezka.startswith(katalog + os.sep)


def katalogi_dozwolone(cwd: str) -> list[str]:
    """Korzeń repozytorium z `cwd` (szukanie `.git` w górę); dla worktree dodatkowo `runs/`
    i `data/` głównego checkoutu (plik `.git` worktree wskazuje `<główne>/.git/worktrees/<n>`)."""
    start = os.path.realpath(cwd or os.getcwd())
    korzen, sciezka = start, start
    while True:
        if os.path.exists(os.path.join(sciezka, ".git")):
            korzen = sciezka
            break
        wyzej = os.path.dirname(sciezka)
        if wyzej == sciezka:
            break
        sciezka = wyzej
    dozwolone = [korzen]
    plik_git = os.path.join(korzen, ".git")
    if os.path.isfile(plik_git):
        try:
            with open(plik_git, encoding="utf-8") as fh:
                wskaznik = fh.read(4096).strip()
        except OSError:
            wskaznik = ""
        if wskaznik.startswith("gitdir:"):
            gitdir = Path(os.path.realpath(os.path.join(korzen, wskaznik[7:].strip())))
            if gitdir.parent.name == "worktrees" and gitdir.parent.parent.name == ".git":
                glowny = gitdir.parent.parent.parent
                dozwolone += [str(glowny / "runs"), str(glowny / "data")]
    return dozwolone


def katalogi_tmp() -> list[str]:
    kandydaci = {"/tmp", "/var/tmp", os.environ.get("TMPDIR", ""), os.environ.get("TEMP", "")}
    return [os.path.realpath(k) for k in kandydaci if k]


# --- analiza jednego wywołania --------------------------------------------------------------------
class Wynik:
    def __init__(self) -> None:
        self.flagi: set[str] = set()
        self.hosty: list[str] = []
        self.sciezki: list[str] = []

    def oznacz(self, flaga: str, sciezka: str | None = None, host: str | None = None) -> None:
        self.flagi.add(flaga)
        if sciezka and sciezka not in self.sciezki and len(self.sciezki) < 20:
            self.sciezki.append(sciezka)
        if host and host not in self.hosty and len(self.hosty) < 20:
            self.hosty.append(host)


def sprawdz_siec(wynik: Wynik, znany: bool, hosty: list[str], dozwolone: frozenset[str]) -> None:
    if not znany:
        wynik.oznacz(F_SIEC_NIEZNANY)
    for h in hosty:
        if not host_dozwolony(h, dozwolone):
            wynik.oznacz(F_SIEC, host=h)


def sprawdz_sciezke(
    wynik: Wynik,
    surowa: str,
    cwd: str,
    katalog_audytu: str,
    *,
    zapis: bool,
    baza: str | None = None,
) -> None:
    """`cwd` wyznacza repozytorium (katalogi dozwolone), `baza` — katalog, względem którego
    rozwija się ścieżkę względną (po `cd` w poleceniu; domyślnie `cwd`)."""
    pelna = rozwin(surowa, baza or cwd)
    if czy_poswiadczenia(pelna):
        wynik.oznacz(F_POSW, sciezka=pelna)
    if _pod(pelna, katalog_audytu):
        wynik.oznacz(F_AUDYT, sciezka=pelna)
    if zapis and not pelna.startswith("/dev/"):
        if any(_pod(pelna, k) for k in katalogi_dozwolone(cwd)):
            return
        if any(_pod(pelna, k) for k in katalogi_tmp()):
            wynik.oznacz(F_TMP, sciezka=pelna)
        else:
            wynik.oznacz(F_ZAPIS, sciezka=pelna)


def _wyglada_na_sciezke(slowo: str) -> bool:
    return (
        bool(slowo) and not slowo.startswith("-") and ("/" in slowo or "." in slowo or "~" in slowo)
    )


POWLOKI = {"bash", "sh", "dash", "zsh", "ksh", "ash"}
MAKS_ZAGNIEZDZENIA = 3  # bash -c 'sh -c "…"' — głębiej nie schodzimy (i nie pętlimy)
_PRZEKIEROWANIA = (">", ">>", "<", "<<")


def polecenie_powloki(program: str, args: list[str]) -> str | None:
    """Tekst wewnętrznego polecenia z `bash -c '…'`, `sh -lc '…'` albo `eval …`; inaczej None."""
    if program == "eval":
        return " ".join(args) or None
    if program not in POWLOKI:
        return None
    ma_c, pomin = False, False
    for a in args:
        if pomin:  # argument opcji `-o`/`-O`/`+o`/`+O` (np. `bash -o pipefail -c '…'`)
            pomin = False
            continue
        if a in _PRZEKIEROWANIA:
            return None
        if a in ("-o", "-O", "+o", "+O"):
            pomin = True
        elif a.startswith("-") and not a.startswith("--") and len(a) > 1:
            ma_c = ma_c or "c" in a[1:]
        elif a.startswith("--"):
            continue
        elif ma_c:
            return a
        else:
            return None  # `bash skrypt.sh` — skrypt z pliku, nie z tekstu
    return None


def _cele_sed(args: list[str]) -> list[str]:
    """Pliki zmieniane przez `sed -i` (także `-i.bak`, `-Ei`, `--in-place`); bez `-i` — brak."""
    w_miejscu, jawny_skrypt, pliki, pomin = False, False, [], False
    for a in args:
        if pomin:
            pomin = False
        elif a in _PRZEKIEROWANIA:
            break
        elif a.startswith("--"):
            w_miejscu = w_miejscu or a.startswith("--in-place")
            if a in ("--expression", "--file"):
                jawny_skrypt, pomin = True, True
            elif a.startswith(("--expression=", "--file=")):
                jawny_skrypt = True
        elif a.startswith("-") and len(a) > 1:
            litery = a[1:]
            if litery.startswith("i"):
                w_miejscu = True  # `-i` / `-i.bak`: reszta to przyrostek kopii
                continue
            for k, lit in enumerate(litery):
                if lit == "i":
                    w_miejscu = True
                if lit in "ef":
                    jawny_skrypt = True
                    pomin = k == len(litery) - 1  # `-e skrypt` — argument w następnym słowie
                    break
        else:
            pliki.append(a)
    if not w_miejscu:
        return []
    return pliki if jawny_skrypt else pliki[1:]


def _cele_pobrania(program: str, args: list[str]) -> list[str]:
    """Plik zapisywany przez `curl -o/--output` albo `wget -O/--output-document`."""
    opcje = ("-o", "--output") if program == "curl" else ("-O", "--output-document")
    cele = []
    for j, a in enumerate(args):
        if a in opcje and j + 1 < len(args):
            cele.append(args[j + 1])
        elif a.startswith(opcje[1] + "="):
            cele.append(a.split("=", 1)[1])
        elif len(a) > 2 and a.startswith(opcje[0]) and not a.startswith("--"):
            cele.append(a[2:])
    return [c for c in cele if c != "-"]


def analizuj_bash(
    wynik: Wynik,
    polecenie: str,
    cwd: str,
    hosty: frozenset[str],
    katalog_audytu: str,
    baza: str | None = None,
    glebokosc: int = 0,
) -> None:
    """`cwd` = katalog sesji (wyznacza repozytorium); `baza` = bieżący katalog polecenia, zmieniany
    przez `cd` w kolejnych segmentach (przybliżenie: bez rozróżniania podpowłok i `||`)."""
    baza = baza or cwd
    for slowa in segmenty(polecenie):
        program, args = program_i_argumenty(slowa)
        if program == "cd":
            if "-" not in args:  # `cd -` (poprzedni katalog) — nieznany, baza bez zmian
                try:
                    baza = rozwin(next((a for a in args if not a.startswith("-")), "~"), baza)
                except ValueError:  # np. bajt zerowy w ścieżce — baza bez zmian
                    pass
            continue
        wewnetrzne = polecenie_powloki(program, args)
        if wewnetrzne is not None and glebokosc < MAKS_ZAGNIEZDZENIA:
            analizuj_bash(wynik, wewnetrzne, cwd, hosty, katalog_audytu, baza, glebokosc + 1)
        siec = siec_w_segmencie(program, args, polecenie, baza)
        if siec is not None:
            sprawdz_siec(wynik, siec[0], siec[1], hosty)
        cele: list[str] = []
        for j, s in enumerate(slowa[:-1]):
            if s in (">", ">>"):
                cele.append(slowa[j + 1])
        if program == "tee":
            cele += [a for a in args if not a.startswith("-") and a not in (">", ">>")]
        elif program in ("cp", "mv", "install") and len(args) >= 2 and not args[-1].startswith("-"):
            cele.append(args[-1])
        elif program == "sed":
            cele += _cele_sed(args)
        elif program in ("curl", "wget"):
            cele += _cele_pobrania(program, args)
        for cel in cele:
            sprawdz_sciezke(wynik, cel, cwd, katalog_audytu, zapis=True, baza=baza)
        for s in slowa:  # odczyty i inne użycia ścieżek wrażliwych
            if s not in cele and _wyglada_na_sciezke(s):
                sprawdz_sciezke(wynik, s, cwd, katalog_audytu, zapis=False, baza=baza)


def analizuj(
    dane: dict, hosty: frozenset[str], katalog_audytu: str
) -> tuple[Wynik, dict[str, str]]:
    wynik, pola = Wynik(), {}
    narzedzie = str(dane.get("tool_name") or "")
    wejscie = dane.get("tool_input")
    wejscie = wejscie if isinstance(wejscie, dict) else {}
    cwd = str(dane.get("cwd") or os.getcwd())
    if narzedzie == "Bash":
        polecenie = str(wejscie.get("command") or "")
        pola["polecenie"] = maskuj(polecenie)
        analizuj_bash(wynik, polecenie, cwd, hosty, katalog_audytu)
    elif narzedzie == "WebFetch":
        url = str(wejscie.get("url") or "")
        pola["url"] = maskuj(url)
        znalezione = hosty_z_tekstu(url)
        sprawdz_siec(wynik, bool(znalezione), znalezione, hosty)
    elif narzedzie == "Read" or narzedzie in NARZEDZIA_ZAPISU:
        sciezka = str(wejscie.get(POLE_SCIEZKI.get(narzedzie, "file_path")) or "")
        pola["sciezka"] = maskuj(sciezka)
        if sciezka:
            sprawdz_sciezke(
                wynik, sciezka, cwd, katalog_audytu, zapis=narzedzie in NARZEDZIA_ZAPISU
            )
    elif narzedzie in ("Grep", "Glob"):  # przeszukanie katalogu to też odczyt (np. ~/.ssh)
        sciezka = str(wejscie.get("path") or "")
        wzorzec = str(wejscie.get("pattern") or "") if narzedzie == "Glob" else ""
        pola["sciezka"] = maskuj(" ".join(x for x in (sciezka, wzorzec) if x))
        for kandydat in (sciezka, wzorzec):
            if _wyglada_na_sciezke(kandydat):
                sprawdz_sciezke(wynik, kandydat, cwd, katalog_audytu, zapis=False)
    return wynik, pola


# --- dziennik -------------------------------------------------------------------------------------
def katalog_audytu() -> Path:
    return Path(os.environ.get("CLAS5_AUDYT_DIR") or Path.home() / ".clas5_audyt")


def zapisz(rekord: dict, katalog: Path, teraz: datetime) -> Path:
    katalog.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(katalog, 0o700)
    except OSError:
        pass
    plik = katalog / f"{teraz:%Y-%m-%d}.jsonl"
    linia = json.dumps(rekord, ensure_ascii=True, separators=(",", ":")) + "\n"
    flagi = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(plik, flagi, 0o600)
    try:
        os.write(fd, linia.encode("ascii"))
    finally:
        os.close(fd)
    return plik


def _krotki(wartosc: object, limit: int = 200) -> str | None:
    """Identyfikatory Claude Code (sesja, agent, cwd, narzędzie): tylko obcięcie, bez maskowania —
    UUID sesji wygląda jak „długi ciąg z cyframi i literami”, a jest potrzebny do przeglądu."""
    if wartosc in (None, ""):
        return None
    tekst = str(wartosc)
    return tekst if len(tekst) <= limit else tekst[:limit] + "…"


def hook_main(
    raw: bytes | str,
    katalog: Path | None = None,
    hosty: frozenset[str] | None = None,
    teraz: datetime | None = None,
) -> Path | None:
    """Wejście hooka → jeden wiersz dziennika. Nigdy nie rzuca wyjątku; zwraca ścieżkę pliku."""
    try:
        teraz = teraz or datetime.now(timezone.utc)
        katalog = katalog or katalog_audytu()
        rekord: dict = {"czas": teraz.strftime("%Y-%m-%dT%H:%M:%SZ")}
        try:
            tekst = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
            dane = json.loads(tekst)
        except (ValueError, TypeError, RecursionError):
            dane = None
        if not isinstance(dane, dict):
            rekord["flagi"] = [F_WEJSCIE]
            return zapisz(rekord, katalog, teraz)
        rekord.update(
            sesja=_krotki(dane.get("session_id")),
            agent=_krotki(dane.get("agent_id")),
            agent_typ=_krotki(dane.get("agent_type")),
            cwd=_krotki(dane.get("cwd")),
            narzedzie=_krotki(dane.get("tool_name")),
        )
        try:
            lista = hosty if hosty is not None else wczytaj_hosty()
            katalog_r = os.path.realpath(str(katalog))
            wynik, pola = analizuj(dane, lista, katalog_r)
            rekord.update(pola)
            rekord["flagi"] = sorted(wynik.flagi)
            if wynik.hosty:
                rekord["hosty_spoza_listy"] = wynik.hosty
            if wynik.sciezki:
                rekord["sciezki_oznaczone"] = [maskuj(s) for s in wynik.sciezki]
        except Exception as blad:  # noqa: BLE001 — analiza padła, wiersz i tak powstaje
            rekord["flagi"] = [F_BLAD]
            rekord["blad"] = type(blad).__name__
        return zapisz(rekord, katalog, teraz)
    except Exception:  # noqa: BLE001 — hook NIE MOŻE przerwać sesji, patrz docstring
        return None


def main(argv: list[str] | None = None) -> int:
    try:
        argv = sys.argv[1:] if argv is None else argv
        if argv[:1] == ["hook"]:
            hook_main(sys.stdin.buffer.read())
    except Exception:  # noqa: BLE001
        pass
    return 0  # zawsze 0 i pusty stdout: tylko oznacza, nigdy nie blokuje


if __name__ == "__main__":
    raise SystemExit(main())
