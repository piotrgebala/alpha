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
   źródło zmienione po fakcie albo uszkodzone archiwum → przeliczenie i wpis w `kopia.log`;
3. `manifest.csv` (dzień, giełda, linie, złe linie, bajty i sha256 źródła i archiwum, wersja
   i sha256 indeksu — nowa `INDEX_VERSION` albo uszkodzony indeks → przeliczenie indeksu);
4. `git add` + commit tylko przy zmianach (dwa przebiegi bez nowych danych → 0 nowych commitów);
5. push na `origin` z `GIT_SSH_COMMAND="ssh -i ${CLAS5_KOPIA_KEY:-~/.ssh/likwidacje_deploy}
   -o IdentitiesOnly=yes -o BatchMode=yes"`; brak `origin` albo błąd push → wpis
   „BRAK ZDALNEJ KOPII: …” w `kopia.log` i kod wyjścia 0 (kopia nigdy nie zatrzymuje kolektorów).

Tryb dzienny: wywołanie co 5 min (cron przez `tools/likwidacje_kopia.sh`) robi pracę raz na dobę —
pierwsze po 00:15 UTC (spóźnione zdarzenia z poprzedniej doby zdążą się dopisać); znacznik
`.ostatni_przebieg` = dzień UTC ostatniego udanego przebiegu. `--teraz` wymusza przebieg.
Pliki bieżącego dnia NIGDY nie są kopiowane (są w trakcie zapisu). W katalogu kopii poza gitem:
`kopia.log`, `status.json`, `.ostatni_przebieg`, `.lock`, `kopia.out` (`.gitignore`).

Zasady:
- czyste funkcje (`gzip_bytes`, `verify_archive`, `is_due`, `manifest_csv`/`parse_manifest`)
  testowane bez sieci (`tests/test_liquidation_backup.py`, push na lokalne `git init --bare`);
- git przez `subprocess` z listą argumentów (bez powłoki), `GIT_TERMINAL_PROMPT=0`, limit czasu push;
- jedyne połączenie sieciowe to `git push` na skonfigurowany ręcznie `origin` (security-review).

    PYTHONUTF8=1 py -m data.liquidation_backup                 # tryb dzienny (katalogi domyślne)
    PYTHONUTF8=1 py -m data.liquidation_backup --teraz --kopia /tmp/kopia --binance ~/likwidacje
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from data import liquidation_index as li

DAILY_AFTER = dt.time(0, 15)
MARKER = ".ostatni_przebieg"
LOG_NAME = "kopia.log"
STATUS_NAME = "status.json"
MANIFEST_NAME = "manifest.csv"
BRANCH = "main"
GIT_USER = "clas5-kopia"
PUSH_TIMEOUT_S = 300
GITIGNORE = "kopia.log\nkopia.out\nstatus.json\n.ostatni_przebieg\n.lock\n*.tmp\n"
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


def is_due(now: dt.datetime, marker_day: str | None, teraz: bool = False) -> bool:
    """Czy przebieg dzienny ma dziś pracować: `--teraz` albo (po 00:15 UTC i nie było go dziś)."""
    if teraz:
        return True
    now = now.astimezone(dt.timezone.utc)
    return now.time() >= DAILY_AFTER and marker_day != now.date().isoformat()


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
    full_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", **(env or {})}
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=full_env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


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
    ssh = f'ssh -i "{key}" -o IdentitiesOnly=yes -o BatchMode=yes'
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


def backup_day(kopia: Path, gielda: str, dzien: str, src: Path, prev: dict | None, log) -> dict:
    """Jeden zamknięty dzień: archiwum + weryfikacja + indeks → wiersz manifestu z polem `_stan`."""
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
        state = "zmieniony"
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
    archive = gzip_bytes(data, f"{dzien}.jsonl")
    li.write_if_changed(arch_path, archive)
    problems = verify_archive(arch_path.read_bytes(), data)
    if problems:
        raise RuntimeError(f"weryfikacja {gielda} {dzien}: {'; '.join(problems)}")
    idx = li.aggregate(gielda, dzien, data.decode("utf-8", errors="replace").split("\n"))
    idx_bytes = li.index_csv(idx)
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
                row = backup_day(kopia, gielda, dzien, path, manifest.get((gielda, dzien)), log)
            except Exception as exc:  # noqa: BLE001 — błąd dnia nie zatrzymuje pozostałych
                s.errors.append(f"{gielda} {dzien}: {type(exc).__name__}: {exc}")
                log(f"BŁĄD: {gielda} {dzien}: {type(exc).__name__}: {exc}")
                continue
            state = row.pop("_stan")
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
    log(
        f"przebieg: nowe {s.new}, zmienione {s.changed}, bez zmian {s.unchanged}, "
        f"błędy {len(s.errors)}, commit {s.commit or '-'}, zdalna kopia: {s.remote}"
    )
    return s


def write_status(kopia: Path, now: dt.datetime, s: Summary) -> None:
    head = _git(kopia, "rev-parse", "--short", "HEAD")
    payload = {
        "przebieg_utc": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
        "dni_w_przebiegu": len(s.days),
        "nowe": s.new,
        "zmienione": s.changed,
        "bez_zmian": s.unchanged,
        "bledy": s.errors,
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
        f"błędy {len(s.errors)}; brak źródła: {', '.join(s.missing_sources) or '-'}; "
        f"commit {s.commit or '-'}; zdalna kopia: {s.remote} ({s.remote_msg})"
    )
    return "\n".join(lines)


def main(argv: list[str], now_fn=None) -> int:
    now_fn = now_fn or (lambda: dt.datetime.now(tz=dt.timezone.utc))
    kopia, sources, teraz = default_kopia_dir(), default_sources(), False
    it = iter(argv)
    for a in it:
        if a == "--teraz":
            teraz = True
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
    now = now_fn()
    if not is_due(now, marker_day, teraz):
        return 0
    try:
        s = run_backup(kopia, sources, now=now, now_fn=now_fn)
    except (
        Exception
    ) as exc:  # noqa: BLE001 — błąd całego przebiegu: log + kod 1, znacznik bez zmian
        _logger(kopia, now_fn)(f"BŁĄD przebiegu: {type(exc).__name__}: {exc}")
        print(f"BŁĄD przebiegu: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    write_status(kopia, now, s)
    print(summary_text(s))
    if s.errors:
        return 1  # znacznik nie powstaje → następne wywołanie (za 5 min) ponawia
    marker.write_text(now.astimezone(dt.timezone.utc).date().isoformat() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
