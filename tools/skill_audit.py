"""
skill_audit.py — rejestr użycia skilli (CLAUDE.md, zasada 19).

Dwie role w jednym pliku:

1. HOOK Claude Code. Program Claude Code (nie model) uruchamia ten plik po każdym wczytaniu
   skilla i podaje na stdin JSON zdarzenia. Skrypt dopisuje JEDEN wiersz do pliku rejestru
   bieżącej gałęzi git: `runs/skille/<gałąź>.jsonl` w katalogu głównym repo, w którym pracuje
   sesja (także w worktree rundy). Dlatego rejestr jest audytowalny: wpis powstaje bez udziału
   Claude'a, więc Claude nie może ani „zapomnieć” wczytanego skilla, ani dopisać niewczytanego.

2. RAPORT. `py tools/skill_audit.py raport [--galaz NAZWA]` — użycia skilli pogrupowane per
   gałąź git. W tym projekcie runda = gałąź, więc to jest źródło sekcji „Użyte skille”
   w README rundy.

Dlaczego plik NA GAŁĄŹ, a nie jeden wspólny (przegląd kodu przed scaleniem, 2026-09-23):
przy jednym pliku wczytanie skilla na master (np. do przeglądu przed scaleniem) zmieniało plik
w kopii roboczej, a gałąź rundy zmieniała go w commitach — `git merge` odmawiał wtedy scalenia
(„local changes would be overwritten”), i to przy KAŻDEJ rundzie. Plik per gałąź sprawia, że
scalenie rundy tylko DODAJE jej plik. Reguła `merge=union` w `.gitattributes` zostaje na
rzadki przypadek dwóch sesji dopisujących do tej samej gałęzi w dwóch klonach.

Trzy twarde reguły hooka (każda ma test w `tests/test_skill_audit.py`):
- NIGDY nie blokuje sesji — każdy błąd jest połykany, kod wyjścia zawsze 0.
- NIGDY nie pisze na stdout — przy części zdarzeń (np. UserPromptSubmit) stdout trafia do
  kontekstu modelu, więc każdy znak byłby wstrzyknięciem treści do rozmowy.
- NIGDY nie zapisuje treści wiadomości użytkownika — z komendy `/nazwa ...` bierze wyłącznie
  nazwę (rozmowa może zawierać dane wrażliwe, a rejestr jest commitowany do repo).

Skrypt jest samodzielny (tylko biblioteka standardowa): hook uruchamia go jako plik, poza
pakietami repo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("runs") / "skille"
MAX_ARGS_CHARS = 200
MAX_NAME_CHARS = 100
GIT_TIMEOUT_S = 5

# Nazwa KOMENDY UŻYTKOWNIKA: litery, cyfry i `_ . : -`, bez spacji i ukośników. To
# zabezpieczenie prywatności — do rejestru nie trafi fragment zwykłego zdania ani ścieżka.
# (Nazwy skilli wczytanych przez Claude'a nie przechodzą przez ten filtr: podaje je program,
# a nie użytkownik, i mogą zawierać ukośnik, np. skille katalogowe `apps/web:deploy`.)
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")
_SLASH_RE = re.compile(r"/([A-Za-z0-9][A-Za-z0-9_.:-]{0,99})(?:\s|$)")

# Kandydaci na pole z nazwą komendy w zdarzeniach komend użytkownika (nieudokumentowane).
_COMMAND_NAME_KEYS = ("command_name", "commandName", "command", "skill", "name")
UNKNOWN_COMMAND = "nierozpoznana-komenda"


# --------------------------------------------------------------------------- ekstrakcja


def _shorten(text: str, limit: int = MAX_ARGS_CHARS) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _slash_command_name(prompt: object) -> str | None:
    """
    Nazwa z `/nazwa argumenty`, albo None. Argumentów i reszty tekstu NIE zwraca.

    Nazwa musi stać TUŻ za ukośnikiem i kończyć się spacją albo końcem tekstu. Wersja
    „pierwsze słowo po ukośniku” zapisałaby z wiadomości „/ Haslo123” słowo „Haslo123”
    (wykryte testem `test_plain_prompts_are_never_recorded`).
    """
    if not isinstance(prompt, str):
        return None
    match = _SLASH_RE.match(prompt.lstrip())
    return match.group(1) if match else None


def extract_skill_use(payload: dict) -> dict | None:
    """
    Z payloadu hooka wyciąga {skill, kto, argumenty, zdarzenie, agent} albo None, jeśli
    zdarzenie nie jest wczytaniem skilla. Funkcja czysta — bez gita i bez zegara, żeby
    hook liczył gałąź dopiero wtedy, gdy wiadomo, że jest co zapisać.
    """
    event = str(payload.get("hook_event_name") or "")
    tool = payload.get("tool_name")

    if tool is not None or event in ("PreToolUse", "PostToolUse"):
        if tool != "Skill":
            return None
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return None
        name = _shorten(str(tool_input.get("skill") or ""), MAX_NAME_CHARS).lstrip("/")
        if not name:
            return None
        return {
            "zdarzenie": event or "PostToolUse",
            "kto": "claude",
            "skill": name,
            "argumenty": _shorten(str(tool_input.get("args") or "")),
            "agent": str(payload.get("agent_type") or ""),
        }

    if event in ("UserPromptExpansion", "UserPromptSubmit"):
        name = None
        for key in _COMMAND_NAME_KEYS:
            value = payload.get(key)
            if isinstance(value, str) and _NAME_RE.match(value.strip().lstrip("/")):
                name = value.strip().lstrip("/")
                break
        if name is None:
            name = _slash_command_name(payload.get("prompt"))
        use = {"zdarzenie": event, "kto": "uzytkownik", "argumenty": "", "agent": ""}
        if name is not None:
            # Argumentów komendy użytkownika świadomie NIE zapisujemy (prywatność).
            return {**use, "skill": name}
        if event == "UserPromptExpansion":
            # Format tego zdarzenia nie jest opisany w dokumentacji Claude Code (sprawdzone
            # 2026-09-23). Zamiast gubić wpis po cichu, zapisujemy „nierozpoznaną komendę”
            # z listą samych NAZW pól (bez wartości) — luka jest widoczna w rejestrze
            # i wskazuje, którą nazwę pola dopisać do _COMMAND_NAME_KEYS.
            return {**use, "skill": UNKNOWN_COMMAND, "klucze": sorted(map(str, payload))}
        return None

    return None


# --------------------------------------------------------------------------- git


def _git(args: list[str], cwd: str | Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def repo_root(cwd: str | Path) -> Path | None:
    top = _git(["rev-parse", "--show-toplevel"], cwd)
    return Path(top) if top else None


def current_branch(root: str | Path) -> str:
    """Nazwa gałęzi; działa też na świeżym repo bez commitów. Odłączony HEAD jest nazwany."""
    branch = _git(["symbolic-ref", "--short", "-q", "HEAD"], root)
    if branch:
        return branch
    sha = _git(["rev-parse", "--short", "HEAD"], root)
    return f"(odlaczony HEAD @{sha})" if sha else "(nieznana)"


def log_file_for_branch(root: Path, branch: str) -> Path:
    """
    `runs/skille/<gałąź>.jsonl`; znaki spoza [A-Za-z0-9._-] (np. `/` z `task/Z17b`) → `_`.
    Nazwa pliku skrócona do MAX_NAME_CHARS — bardzo długa gałąź przekroczyłaby limit systemu
    plików i wpis przepadłby po cichu. Pełna nazwa gałęzi zostaje w polu `galaz` wpisu.
    """
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", branch).strip("._")[:MAX_NAME_CHARS] or "_"
    return root / LOG_DIR / f"{safe}.jsonl"


# --------------------------------------------------------------------------- zapis


def build_record(use: dict, *, now: datetime, branch: str, session: str) -> dict:
    skill = use["skill"]
    record = {
        "czas": now.isoformat(timespec="seconds"),
        "zdarzenie": use["zdarzenie"],
        "kto": use["kto"],
        "skill": skill,
        "wtyczka": skill.split(":", 1)[0] if ":" in skill else "",
        "argumenty": use["argumenty"],
        "galaz": branch,
        "sesja": session,
        "agent": use["agent"],
    }
    if "klucze" in use:
        record["klucze"] = use["klucze"]
    return record


def append_record(log_path: Path, record: dict) -> None:
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def hook_main(raw: bytes | str) -> int:
    """Wejście hooka. Zawsze zwraca 0 i nic nie drukuje — patrz docstring modułu."""
    try:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        payload = json.loads(text) if text.strip() else {}
        if not isinstance(payload, dict):
            return 0
        use = extract_skill_use(payload)
        if use is None:
            return 0
        root = repo_root(payload.get("cwd") or os.getcwd())
        # Tylko repo z katalogiem runs/ — hook nie tworzy plików w obcych repozytoriach.
        if root is None or not (root / LOG_DIR.parent).is_dir():
            return 0
        branch = current_branch(root)
        record = build_record(
            use,
            now=datetime.now().astimezone(),
            branch=branch,
            session=str(payload.get("session_id") or ""),
        )
        append_record(log_file_for_branch(root, branch), record)
    except Exception:  # noqa: BLE001 — hook NIE MOŻE przerwać sesji, patrz docstring
        pass
    return 0


# --------------------------------------------------------------------------- raport


def load_records(path: Path) -> tuple[list[dict], int]:
    """
    (poprawne wpisy, liczba wierszy uszkodzonych) z pliku albo ze wszystkich `*.jsonl`
    katalogu. Uszkodzone są liczone, nie ukrywane.
    """
    records: list[dict] = []
    bad = 0
    files = sorted(path.glob("*.jsonl")) if path.is_dir() else [path] if path.exists() else []
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if isinstance(rec, dict) and rec.get("skill"):
                records.append(rec)
            else:
                bad += 1
    records.sort(key=lambda r: str(r.get("czas") or ""))
    return records, bad


def _plural(n: int, one: str, few: str, many: str) -> str:
    """Polska odmiana liczebnika: 1 skill, 2–4 skille, 5+ skilli (z wyjątkiem 12–14)."""
    if n == 1:
        return f"{n} {one}"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} {few}"
    return f"{n} {many}"


def _table(records: list[dict]) -> list[str]:
    lines = ["| czas | kto | skill | argumenty (skrót) |", "|---|---|---|---|"]
    for r in records:
        args = str(r.get("argumenty") or "").replace("|", "\\|")
        agent = f" (agent: {r['agent']})" if r.get("agent") else ""
        lines.append(
            f"| {r.get('czas', '')} | {r.get('kto', '')}{agent} | `{r['skill']}` | {args} |"
        )
    return lines


def render_report(records: list[dict], bad: int, branch: str | None = None) -> str:
    out: list[str] = []
    if branch is not None:
        records = [r for r in records if r.get("galaz") == branch]
        out.append(f"### Użyte skille — gałąź `{branch}` (rejestr automatyczny)")
        out.append("")
        if not records:
            out.append("_Brak wpisów w rejestrze dla tej gałęzi._")
        else:
            out.extend(_table(records))
            distinct = sorted({r["skill"] for r in records})
            out.append("")
            out.append(
                f"Razem: {_plural(len(records), 'wczytanie', 'wczytania', 'wczytań')}, "
                f"{_plural(len(distinct), 'różny skill', 'różne skille', 'różnych skilli')}: "
                + ", ".join(f"`{s}`" for s in distinct)
                + "."
            )
    else:
        out.append("## Rejestr użycia skilli — podsumowanie per gałąź")
        out.append("")
        if not records:
            out.append("_Rejestr jest pusty._")
        else:
            out.append("| gałąź | wczytań | skille |")
            out.append("|---|---|---|")
            by_branch: dict[str, list[dict]] = {}
            for r in records:
                by_branch.setdefault(str(r.get("galaz") or "(nieznana)"), []).append(r)
            for name, recs in by_branch.items():
                distinct = sorted({r["skill"] for r in recs})
                out.append(
                    f"| `{name}` | {len(recs)} | " + ", ".join(f"`{s}`" for s in distinct) + " |"
                )
    if bad:
        out.append("")
        out.append(f"**Uwaga: {bad} uszkodzonych wierszy w rejestrze pominięto** — sprawdź plik.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["hook"]:
        return hook_main(sys.stdin.buffer.read())

    parser = argparse.ArgumentParser(description="Rejestr użycia skilli (CLAUDE.md, zasada 19).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    rep = sub.add_parser("raport", help="użycia skilli per gałąź (runda)")
    rep.add_argument("--galaz", help="tylko ta gałąź (np. gałąź rundy)")
    rep.add_argument(
        "--plik", help="plik albo katalog rejestru (domyślnie runs/skille/ w bieżącym repo)"
    )
    args = parser.parse_args(argv)

    if args.plik:
        path = Path(args.plik)
    else:
        root = repo_root(os.getcwd())
        if root is None:
            parser.error("nie jestem w repozytorium git — podaj --plik")
        path = root / LOG_DIR
    records, bad = load_records(path)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(render_report(records, bad, args.galaz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
