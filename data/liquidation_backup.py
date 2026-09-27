"""
liquidation_backup.py — kopia zapasowa plików likwidacji (Binance LK0 `~/likwidacje`, Bybit
`~/likwidacje_bybit`) do lokalnego repozytorium git, z dziennym indeksem i manifestem sum kontrolnych;
push na zdalne repo tylko wtedy, gdy skonfigurowano `origin`.

Po co (docs/rag/11, sekcje 2, 3 i 6; decyzja użytkownika 2026-09-27 „wykonaj wszystkie”): LK0 to
jedyny zbiór, którego nie da się odtworzyć wstecz (strumień na żywo od 2026-09-25), a dziś nie ma
ŻADNEJ kopii — utrata serwera = utrata całego LK0. Higiena danych: 0 wariantów, 0 odczytów cen.

Co robi jeden przebieg (dla każdego ZAMKNIĘTEGO dnia obu katalogów; dzień UTC < dziś UTC):
1. czyta plik źródłowy (tylko odczyt; do katalogów kolektorów nic nie zapisuje), liczy sha256;
2. gdy manifest ma ten sam sha256 źródła, a archiwum ma sha256 z manifestu — dzień bez zmian;
   inaczej: gzip deterministyczny (`mtime=0`, stała nazwa `YYYY-MM-DD.jsonl` w nagłówku, poziom 9)
   → `<kopia>/<gielda>/YYYY-MM-DD.jsonl.gz`, weryfikacja (rozpakowane archiwum == źródło bajt w bajt,
   ta sama liczba linii), indeks `<kopia>/indeks/<gielda>_YYYY-MM-DD.csv` (`data/liquidation_index.py`);
   źródło zmienione po fakcie (DOPISANE zdarzenia) albo uszkodzone archiwum → przeliczenie i wpis
   w `kopia.log`; źródło SKRÓCONE albo z innym początkiem niż archiwum (pliki kolektorów są tylko
   dopisywane, więc to uszkodzenie, nie nowe dane) → archiwum, indeks i manifest ZOSTAJĄ, wpis
   „ŹRÓDŁO SKRÓCONE/NADPISANE” w logu i pole `alarmy` w `status.json` (nie jest błędem — nie
   wywołuje ponowień); świadome przyjęcie nowej wersji: `--przyjmij-skrocone`;
3. `manifest.csv` (dzień, giełda, linie, złe linie, bajty i sha256 źródła i archiwum, wersja
   i sha256 indeksu — nowa `INDEX_VERSION` albo uszkodzony indeks → przeliczenie indeksu);
4. `git add` + commit tylko przy zmianach (dwa przebiegi bez nowych danych → 0 nowych commitów);
5. push na `origin` z `GIT_SSH_COMMAND="ssh -i ${CLAS5_KOPIA_KEY:-~/.ssh/likwidacje_deploy}
   -o IdentitiesOnly=yes -o BatchMode=yes"` (ścieżka klucza cytowana `shlex.quote` — git wykonuje
   tę wartość przez powłokę); brak `origin` albo błąd push → wpis „BRAK ZDALNEJ KOPII: …”
   w `kopia.log` i kod wyjścia 0 (kopia nigdy nie zatrzymuje kolektorów). Pierwszy push przez ssh
   wymaga hosta w `~/.ssh/known_hosts` (`BatchMode=yes` nie zapyta) — `ssh-keyscan` przed cronem.

Tryb dzienny: wywołanie co 5 min (cron przez `tools/likwidacje_kopia.sh`) robi pracę raz na dobę —
pierwsze po 00:15 UTC (spóźnione zdarzenia z poprzedniej doby zdążą się dopisać); znacznik
`.ostatni_przebieg` = dzień UTC ostatniego udanego przebiegu. `--teraz` wymusza przebieg.
Ponowienia ograniczone: przebieg z błędem (kod 1) zapisuje `.ostatni_blad` i następny pełny
przebieg rusza najwcześniej po `RETRY_AFTER` (60 min), nie co 5 min; nieudany push na
skonfigurowany `origin` zapisuje `.push_zalegly` i kolejne wywołania (co `RETRY_AFTER`) robią
TYLKO tani `git push`, bez przeliczania dni — zdalna kopia dogania po awarii sieci w godzinę,
nie w dobę. Pliki bieżącego dnia NIGDY nie są kopiowane (są w trakcie zapisu). W katalogu kopii
poza gitem: `kopia.log`, `status.json`, `.ostatni_przebieg`, `.ostatni_blad`, `.push_zalegly`,
`.lock`, `kopia.out` (`.gitignore`).

Zasady:
- czyste funkcje (`gzip_bytes`, `verify_archive`, `is_due`, `manifest_csv`/`parse_manifest`)
  testowane bez sieci (`tests/test_liquidation_backup.py`, push na lokalne `git init --bare`);
- git przez `subprocess` z listą argumentów (bez powłoki), `GIT_TERMINAL_PROMPT=0`, limit czasu push
  (po przekroczeniu zabijana cała grupa procesów — także zawieszony `ssh`); jawne `--git-dir`
  i `--work-tree` katalogu kopii, a ze środowiska usuwane zmienne `GIT_*` sterujące repozytorium
  i tożsamością (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_AUTHOR_*`, …) — wywołanie
  z hooka innego repo nie może commitować do cudzego repozytorium ani zmienić jego konfiguracji;
- jedyne połączenie sieciowe to `git push` na skonfigurowany ręcznie `origin` (security-review).

    PYTHONUTF8=1 py -m data.liquidation_backup                 # tryb dzienny (katalogi domyślne)
    PYTHONUTF8=1 py -m data.liquidation_backup --teraz --kopia /tmp/kopia --binance ~/likwidacje
    PYTHONUTF8=1 py -m data.liquidation_backup --teraz --przyjmij-skrocone   # po decyzji człowieka
"""

from __future__ import annotations

import contextlib
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import shlex
import signal
import subprocess
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from data import liquidation_index as li

DAILY_AFTER = dt.time(0, 15)
MARKER = ".ostatni_przebieg"
ERROR_MARKER = ".ostatni_blad"
PUSH_MARKER = ".push_zalegly"
RETRY_AFTER = dt.timedelta(minutes=60)
LOG_NAME = "kopia.log"
STATUS_NAME = "status.json"
MANIFEST_NAME = "manifest.csv"
BRANCH = "main"
GIT_USER = "clas5-kopia"
PUSH_TIMEOUT_S = 300
GITIGNORE = (
    "kopia.log\nkopia.out\nstatus.json\n.ostatni_przebieg\n.ostatni_blad\n.push_zalegly\n"
    ".lock\n*.tmp\n"
)
# zmienne GIT_* przepuszczane do gita (reszta GIT_* usuwana — docstring, „Zasady”)
GIT_ENV_KEEP = frozenset({"GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM"})
MANIFEST_COLUMNS = (
    "dzien",
    "gielda",
    "linie",
    "zle_linie",
    "bajty_zrodla",
    "sha256_zrodla",
    "bajty_archiwum",
    "sha256_archiwum",
    "wersja_indeksu",
    "sha256_indeksu",
)
MANIFEST_REQUIRED = ("dzien", "gielda", "linie", "sha256_zrodla", "sha256_archiwum")


def default_kopia_dir() -> Path:
    return Path(os.environ.get("CLAS5_KOPIA_DIR") or Path.home() / "likwidacje_kopia")


def default_sources() -> dict[str, Path]:
    return {
        "binance": Path(os.environ.get("CLAS5_LIKWIDACJE_DIR") or Path.home() / "likwidacje"),
        "bybit": Path(
            os.environ.get("CLAS5_LIKWIDACJE_BYBIT_DIR") or Path.home() / "likwidacje_bybit"
        ),
    }


def default_key() -> Path:
    return Path(os.environ.get("CLAS5_KOPIA_KEY") or Path.home() / ".ssh" / "likwidacje_deploy")


# ------------------------------------------------------------------ czyste funkcje
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def count_lines(data: bytes) -> int:
    """Liczba linii (ostatnia bez `\\n` też się liczy)."""
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def gzip_bytes(data: bytes, name: str) -> bytes:
    """Gzip deterministyczny: `mtime=0`, stała nazwa w nagłówku, poziom 9, OS = 255 (Python)."""
    buf = io.BytesIO()
    with gzip.GzipFile(filename=name, mode="wb", fileobj=buf, mtime=0, compresslevel=9) as gz:
        gz.write(data)
    return buf.getvalue()


def verify_archive(archive: bytes, source: bytes) -> list[str]:
    """Problemy archiwum wobec źródła (pusta lista = poprawne): rozpakowanie, bajty, linie."""
    try:
        unpacked = gzip.decompress(archive)
    except (OSError, EOFError, ValueError, zlib.error) as exc:
        return [f"nie da się rozpakować ({type(exc).__name__}: {exc})"]
    problems = []
    if count_lines(unpacked) != count_lines(source):
        problems.append(f"linie {count_lines(unpacked)} ≠ źródło {count_lines(source)}")
    if unpacked != source:
        problems.append("rozpakowane bajty ≠ źródło")
    return problems


def is_due(
    now: dt.datetime,
    marker_day: str | None,
    teraz: bool = False,
    last_error: dt.datetime | None = None,
) -> bool:
    """Czy przebieg dzienny ma teraz pracować: `--teraz` albo (po 00:15 UTC, nie było go dziś
    i od ostatniego błędu minęło `RETRY_AFTER` — trwały błąd nie daje 288 przebiegów na dobę)."""
    if teraz:
        return True
    now = now.astimezone(dt.timezone.utc)
    if now.time() < DAILY_AFTER or marker_day == now.date().isoformat():
        return False
    return last_error is None or now - last_error >= RETRY_AFTER


def read_time_marker(path: Path) -> dt.datetime | None:
    """Znacznik z czasem ISO (`.ostatni_blad`, `.push_zalegly`) → datetime UTC; brak/zły → None."""
    try:
        t = dt.datetime.fromisoformat(Path(path).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    return t.astimezone(dt.timezone.utc) if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def write_time_marker(path: Path, now: dt.datetime) -> None:
    stamp = now.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    li.write_if_changed(Path(path), (stamp + "\n").encode("utf-8"))


def ssh_command(key: Path) -> str:
    """Wartość `GIT_SSH_COMMAND` (git wykonuje ją przez powłokę → ścieżka klucza cytowana)."""
    return f"ssh -i {shlex.quote(str(key))} -o IdentitiesOnly=yes -o BatchMode=yes"


def git_env(base: dict, extra: dict | None = None) -> dict:
    """Środowisko dla gita: bez `GIT_*` spoza `GIT_ENV_KEEP` (np. `GIT_DIR` z hooka innego repo),
    z `GIT_TERMINAL_PROMPT=0` i `extra` (np. `GIT_SSH_COMMAND`)."""
    env = {k: v for k, v in base.items() if not k.startswith("GIT_") or k in GIT_ENV_KEEP}
    return {**env, "GIT_TERMINAL_PROMPT": "0", **(extra or {})}


def manifest_csv(rows: dict[tuple[str, str], dict]) -> bytes:
    """Manifest → bajty CSV, sortowane po (giełda, dzień)."""
    out = [",".join(MANIFEST_COLUMNS)]
    for key in sorted(rows):
        out.append(",".join(str(rows[key][c]) for c in MANIFEST_COLUMNS))
    return ("\n".join(out) + "\n").encode("utf-8")


def parse_manifest(data: bytes) -> dict[tuple[str, str], dict]:
    """Manifest → wiersze po (giełda, dzień). Starszy nagłówek (bez nowych kolumn) jest przyjmowany,
    brakujące pola = "" (dzień zostanie wtedy przeliczony); brak kolumn kluczowych = błąd."""
    lines = data.decode("utf-8").splitlines()
    if not lines:
        return {}
    head = lines[0].split(",")
    missing = [c for c in MANIFEST_REQUIRED if c not in head]
    if missing:
        raise ValueError(f"kopia: manifest bez kolumn {missing} (nagłówek {head})")
    rows = {}
    for line in lines[1:]:
        if line:
            raw = dict(zip(head, line.split(","), strict=True))
            r = {c: raw.get(c, "") for c in MANIFEST_COLUMNS}
            rows[(r["gielda"], r["dzien"])] = r
    return rows


# ------------------------------------------------------------------ git (cienka warstwa)
def _git(repo: Path, *args: str, env: dict | None = None, timeout: float = 120):
    """git w katalogu kopii: jawne `--git-dir`/`--work-tree` (poza `init`), oczyszczone środowisko;
    po `timeout` zabija całą grupę procesów (zawieszony `ssh` nie trzyma potoków) i rzuca
    `subprocess.TimeoutExpired`."""
    repo = Path(repo)
    cmd = ["git", *args]
    if args[:1] != ("init",):
        cmd = ["git", f"--git-dir={repo / '.git'}", f"--work-tree={repo}", *args]
    posix = hasattr(os, "killpg")
    proc = subprocess.Popen(
        cmd,
        cwd=repo,
        env=git_env(dict(os.environ), env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=posix,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if posix:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
        else:  # pragma: no cover — Windows: bez grup procesów
            proc.kill()
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def _git_ok(repo: Path, *args: str) -> str:
    r = _git(repo, *args)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout.strip()


def ensure_repo(kopia: Path) -> bool:
    """Lokalne repo git w katalogu kopii (gałąź main, lokalny użytkownik); True = właśnie utworzone."""
    kopia.mkdir(parents=True, exist_ok=True)
    created = False
    if not (kopia / ".git").exists():
        _git_ok(kopia, "init", "-q", "-b", BRANCH)
        created = True
    for k, v in (
        ("user.name", GIT_USER),
        ("user.email", GIT_USER),
        ("commit.gpgsign", "false"),
        ("core.autocrlf", "false"),
    ):
        _git_ok(kopia, "config", k, v)
    li.write_if_changed(kopia / ".gitignore", GITIGNORE.encode("utf-8"))
    return created


def commit_changes(kopia: Path, message: str) -> str | None:
    """`git add -A` + commit tylko przy zmianach; zwraca skrót nowego commita albo None."""
    _git_ok(kopia, "add", "-A")
    if not _git_ok(kopia, "status", "--porcelain"):
        return None
    _git_ok(kopia, "commit", "-q", "-m", message)
    return _git_ok(kopia, "rev-parse", "--short", "HEAD")


def push(kopia: Path, key: Path) -> tuple[str, str]:
    """Push na `origin` → (`ok` | `brak remote` | `błąd push`, opis)."""
    if _git(kopia, "remote", "get-url", "origin").returncode != 0:
        return "brak remote", "brak skonfigurowanego remote origin"
    ssh = ssh_command(key)
    try:
        r = _git(
            kopia,
            "push",
            "-q",
            "origin",
            f"{BRANCH}:{BRANCH}",
            env={"GIT_SSH_COMMAND": ssh},
            timeout=PUSH_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return "błąd push", f"przekroczony limit {PUSH_TIMEOUT_S} s"
    if r.returncode != 0:
        return "błąd push", (r.stderr or r.stdout).strip().replace("\n", " | ")[:300]
    return "ok", "push na origin"


# ------------------------------------------------------------------ przebieg
@dataclass
class Summary:
    days: list[dict] = field(default_factory=list)  # wiersze manifestu dni dotkniętych przebiegiem
    new: int = 0
    changed: int = 0  # źródło zmienione po fakcie albo archiwum/indeks odtworzone ze źródła
    unchanged: int = 0
    errors: list[str] = field(default_factory=list)
    alarms: list[str] = field(default_factory=list)  # źródło skrócone/nadpisane — kopia zachowana
    missing_sources: list[str] = field(default_factory=list)
    commit: str | None = None
    remote: str = "-"
    remote_msg: str = ""


def _logger(kopia: Path, now_fn):
    def log(msg: str) -> None:
        stamp = now_fn().astimezone(dt.timezone.utc).isoformat(timespec="seconds")
        with open(kopia / LOG_NAME, "a", encoding="utf-8") as f:
            f.write(f"{stamp} {msg}\n")

    return log


def _int(x) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0


def shrink_problem(data: bytes, prev: dict, old_source: bytes | None) -> str | None:
    """Czy nowe źródło NIE jest dopisaniem do poprzedniego (pliki kolektorów są append-only)?
    Opis problemu albo None. `old_source` = rozpakowane poprzednie archiwum (None = nieznane —
    wtedy tylko porównanie liczby linii i bajtów z manifestu)."""
    lines, old_lines = count_lines(data), _int(prev.get("linie"))
    if lines < old_lines:
        return f"linie {old_lines} → {lines}"
    if len(data) < _int(prev.get("bajty_zrodla")):
        return f"bajty {prev.get('bajty_zrodla')} → {len(data)}"
    if old_source is not None and not data.startswith(old_source):
        return "początek pliku inny niż w archiwum"
    return None


def backup_day(
    kopia: Path,
    gielda: str,
    dzien: str,
    src: Path,
    prev: dict | None,
    log,
    accept_shrink: bool = False,
) -> dict:
    """Jeden zamknięty dzień: archiwum + weryfikacja + indeks → wiersz manifestu z polem `_stan`
    (`nowy` / `zmieniony` / `naprawiony` / `bez zmian` / `alarm`; przy `alarm` także `_alarm`)."""
    data = src.read_bytes()
    src_sha = sha256(data)
    arch_path = kopia / gielda / f"{dzien}.jsonl.gz"
    idx_path = li.index_path(kopia / "indeks", gielda, dzien)
    arch_ok = (
        prev is not None
        and arch_path.exists()
        and sha256(arch_path.read_bytes()) == prev["sha256_archiwum"]
    )
    idx_ok = (
        prev is not None
        and prev.get("wersja_indeksu") == str(li.INDEX_VERSION)
        and idx_path.exists()
        and sha256(idx_path.read_bytes()) == prev.get("sha256_indeksu")
    )
    state = "nowy" if prev is None else "naprawiony"
    if prev is not None and prev["sha256_zrodla"] != src_sha:
        old_source = gzip.decompress(arch_path.read_bytes()) if arch_ok else None
        problem = shrink_problem(data, prev, old_source)
        if problem and not accept_shrink:
            msg = (
                f"ŹRÓDŁO SKRÓCONE/NADPISANE: {gielda} {dzien} — {problem}; archiwum, indeks "
                "i manifest BEZ ZMIAN (przyjęcie nowej wersji: --przyjmij-skrocone)"
            )
            log(msg)
            return {**prev, "_stan": "alarm", "_alarm": msg}
        state = "zmieniony"
        if problem:
            log(f"PRZYJĘTO SKRÓCONE ŹRÓDŁO: {gielda} {dzien} — {problem} (--przyjmij-skrocone)")
        log(
            f"ZMIENIONY PO FAKCIE: {gielda} {dzien} — sha256 źródła {prev['sha256_zrodla'][:12]} → "
            f"{src_sha[:12]}, linie {prev['linie']} → {count_lines(data)}; przeliczam"
        )
    elif arch_ok and idx_ok:
        return {**prev, "_stan": "bez zmian"}
    elif prev is not None and not arch_ok:
        what = "USZKODZONE ARCHIWUM" if arch_path.exists() else "BRAK ARCHIWUM"
        log(f"{what}: {gielda} {dzien} — sha256 ≠ manifest; odtwarzam ze źródła")
    elif prev is not None and prev.get("wersja_indeksu") != str(li.INDEX_VERSION):
        log(
            f"NOWA WERSJA INDEKSU: {gielda} {dzien} — {prev.get('wersja_indeksu')} → "
            f"{li.INDEX_VERSION}; przeliczam indeks"
        )
    elif prev is not None:
        what = "USZKODZONY INDEKS" if idx_path.exists() else "BRAK INDEKSU"
        log(f"{what}: {gielda} {dzien} — odtwarzam ze źródła")
    # najpierw wszystko w pamięci (błąd indeksu nie zostawia archiwum bez wiersza manifestu)
    idx = li.aggregate(gielda, dzien, data.decode("utf-8", errors="replace").split("\n"))
    idx_bytes = li.index_csv(idx)
    archive = gzip_bytes(data, f"{dzien}.jsonl")
    li.write_if_changed(arch_path, archive)
    problems = verify_archive(arch_path.read_bytes(), data)
    if problems:
        raise RuntimeError(f"weryfikacja {gielda} {dzien}: {'; '.join(problems)}")
    li.write_if_changed(idx_path, idx_bytes)
    if idx.bad_lines:
        log(f"UWAGA: {gielda} {dzien} — {idx.bad_lines} złych linii pominiętych w indeksie")
    return {
        "dzien": dzien,
        "gielda": gielda,
        "linie": count_lines(data),
        "zle_linie": idx.bad_lines,
        "bajty_zrodla": len(data),
        "sha256_zrodla": src_sha,
        "bajty_archiwum": len(archive),
        "sha256_archiwum": sha256(archive),
        "wersja_indeksu": li.INDEX_VERSION,
        "sha256_indeksu": sha256(idx_bytes),
        "_stan": state,
    }


def run_backup(
    kopia: Path,
    sources: dict[str, Path],
    now: dt.datetime | None = None,
    key: Path | None = None,
    now_fn=None,
    accept_shrink: bool = False,
) -> Summary:
    """Pełny przebieg (bez bramki dziennej): archiwa, indeksy, manifest, commit, push."""
    now_fn = now_fn or (lambda: dt.datetime.now(tz=dt.timezone.utc))
    now = now or now_fn()
    today = li.utc_today(now)
    kopia = Path(kopia)
    if ensure_repo(kopia):
        _logger(kopia, now_fn)(f"utworzono repozytorium kopii {kopia} (gałąź {BRANCH})")
    log = _logger(kopia, now_fn)
    man_path = kopia / MANIFEST_NAME
    manifest = parse_manifest(man_path.read_bytes()) if man_path.exists() else {}
    s = Summary()
    for gielda, src_dir in sources.items():
        if not Path(src_dir).is_dir():
            s.missing_sources.append(gielda)
            log(f"brak katalogu źródłowego {gielda}: {src_dir} — pomijam")
            continue
        for dzien, path in li.closed_days(src_dir, today):
            try:
                row = backup_day(
                    kopia, gielda, dzien, path, manifest.get((gielda, dzien)), log, accept_shrink
                )
            except Exception as exc:  # noqa: BLE001 — błąd dnia nie zatrzymuje pozostałych
                s.errors.append(f"{gielda} {dzien}: {type(exc).__name__}: {exc}")
                log(f"BŁĄD: {gielda} {dzien}: {type(exc).__name__}: {exc}")
                continue
            state = row.pop("_stan")
            if state == "alarm":
                s.alarms.append(row.pop("_alarm"))
                continue  # wiersz manifestu bez zmian
            manifest[(gielda, dzien)] = row
            s.days.append({**row, "stan": state})
            if state == "nowy":
                s.new += 1
            elif state in ("zmieniony", "naprawiony"):
                s.changed += 1
            else:
                s.unchanged += 1
    li.write_if_changed(man_path, manifest_csv(manifest))
    s.commit = commit_changes(
        kopia, f"Kopia likwidacji {today.isoformat()}: nowe dni {s.new}, zmienione {s.changed}"
    )
    s.remote, s.remote_msg = push(kopia, key or default_key())
    if s.remote != "ok":
        log(f"BRAK ZDALNEJ KOPII: {s.remote_msg}")
    if s.remote == "błąd push":  # remote jest, sieć/serwer nie — ponowienie samego push
        write_time_marker(kopia / PUSH_MARKER, now)
    else:
        (kopia / PUSH_MARKER).unlink(missing_ok=True)
    log(
        f"przebieg: nowe {s.new}, zmienione {s.changed}, bez zmian {s.unchanged}, "
        f"alarmy {len(s.alarms)}, błędy {len(s.errors)}, commit {s.commit or '-'}, "
        f"zdalna kopia: {s.remote}"
    )
    return s


def retry_push(kopia: Path, now: dt.datetime, key: Path, log) -> tuple[str, str] | None:
    """Zaległy push (`.push_zalegly` starszy niż `RETRY_AFTER`) → tylko `git push`, bez
    przeliczania dni. None = nic do zrobienia; inaczej wynik `push`."""
    marker = kopia / PUSH_MARKER
    last = read_time_marker(marker)
    if last is None or now.astimezone(dt.timezone.utc) - last < RETRY_AFTER:
        return None
    ahead = _git(kopia, "rev-list", "--count", f"refs/remotes/origin/{BRANCH}..{BRANCH}")
    if ahead.returncode == 0 and ahead.stdout.strip() == "0":
        marker.unlink(missing_ok=True)
        log("zaległy push: origin już ma wszystkie commity — znacznik usunięty")
        return "ok", "origin aktualny"
    remote, msg = push(kopia, key)
    if remote == "ok":
        marker.unlink(missing_ok=True)
        log("zaległy push: zdalna kopia dogoniona")
    elif remote == "błąd push":
        write_time_marker(marker, now)
        log(f"BRAK ZDALNEJ KOPII (ponowienie): {msg}")
    else:
        marker.unlink(missing_ok=True)
        log(f"BRAK ZDALNEJ KOPII (ponowienie): {msg}")
    status_path = kopia / STATUS_NAME
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    payload.update(
        {
            "zdalna_kopia": remote,
            "zdalna_kopia_opis": msg,
            "push_ponowiony_utc": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
        }
    )
    li.write_if_changed(
        status_path, json.dumps(payload, ensure_ascii=False, indent=1).encode("utf-8")
    )
    return remote, msg


def write_status(kopia: Path, now: dt.datetime, s: Summary) -> None:
    head = (
        _git(kopia, "rev-parse", "--short", "HEAD")
        if (kopia / ".git").exists()
        else subprocess.CompletedProcess([], 1, "", "")
    )
    payload = {
        "przebieg_utc": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
        "dni_w_przebiegu": len(s.days),
        "nowe": s.new,
        "zmienione": s.changed,
        "bez_zmian": s.unchanged,
        "bledy": s.errors,
        "alarmy": s.alarms,
        "brak_zrodla": s.missing_sources,
        "commit": s.commit,
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "zdalna_kopia": s.remote,
        "zdalna_kopia_opis": s.remote_msg,
    }
    li.write_if_changed(
        kopia / STATUS_NAME, json.dumps(payload, ensure_ascii=False, indent=1).encode("utf-8")
    )


def summary_text(s: Summary) -> str:
    lines = []
    for d in sorted(s.days, key=lambda r: (r["gielda"], r["dzien"])):
        lines.append(
            f"{d['gielda']:8s} {d['dzien']}  linie {int(d['linie']):>7d}  złe {d['zle_linie']}  "
            f"źródło {int(d['bajty_zrodla']):>9d} B  gz {int(d['bajty_archiwum']):>8d} B  "
            f"sha256(gz) {d['sha256_archiwum'][:16]}  [{d['stan']}]"
        )
    lines.append(
        f"razem dni {len(s.days)} (nowe {s.new}, zmienione {s.changed}, bez zmian {s.unchanged}); "
        f"alarmy {len(s.alarms)}; błędy {len(s.errors)}; "
        f"brak źródła: {', '.join(s.missing_sources) or '-'}; "
        f"commit {s.commit or '-'}; zdalna kopia: {s.remote} ({s.remote_msg})"
    )
    lines.extend(f"ALARM: {a}" for a in s.alarms)
    return "\n".join(lines)


def main(argv: list[str], now_fn=None) -> int:
    now_fn = now_fn or (lambda: dt.datetime.now(tz=dt.timezone.utc))
    kopia, sources, teraz, accept = default_kopia_dir(), default_sources(), False, False
    it = iter(argv)
    for a in it:
        if a == "--teraz":
            teraz = True
        elif a == "--przyjmij-skrocone":
            accept = True
        elif a == "--kopia":
            kopia = Path(next(it)).expanduser()
        elif a in ("--binance", "--bybit"):
            sources[a[2:]] = Path(next(it)).expanduser()
        else:
            print(f"nieznany argument {a!r}", file=sys.stderr)
            return 2
    kopia.mkdir(parents=True, exist_ok=True)
    marker = kopia / MARKER
    marker_day = marker.read_text(encoding="utf-8").strip() if marker.exists() else None
    err_marker = kopia / ERROR_MARKER
    now = now_fn()
    if not is_due(now, marker_day, teraz, read_time_marker(err_marker)):
        if (kopia / ".git").exists():
            try:
                retry_push(kopia, now, default_key(), _logger(kopia, now_fn))
            except Exception as exc:  # noqa: BLE001 — ponowienie push nigdy nie daje kodu ≠ 0
                _logger(kopia, now_fn)(f"BRAK ZDALNEJ KOPII (ponowienie): {exc}")
        return 0
    try:
        s = run_backup(kopia, sources, now=now, now_fn=now_fn, accept_shrink=accept)
    except (
        Exception
    ) as exc:  # noqa: BLE001 — błąd całego przebiegu: log + kod 1, znacznik bez zmian
        msg = f"BŁĄD przebiegu: {type(exc).__name__}: {exc}"
        _logger(kopia, now_fn)(msg)
        print(msg, file=sys.stderr)
        write_time_marker(err_marker, now)
        write_status(kopia, now, Summary(errors=[msg]))
        return 1
    write_status(kopia, now, s)
    print(summary_text(s))
    if s.errors:
        # znacznik dnia nie powstaje → ponowienie, ale najwcześniej za RETRY_AFTER (nie co 5 min)
        write_time_marker(err_marker, now)
        return 1
    err_marker.unlink(missing_ok=True)
    marker.write_text(now.astimezone(dt.timezone.utc).date().isoformat() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
