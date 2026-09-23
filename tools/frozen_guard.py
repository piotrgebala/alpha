"""
frozen_guard.py

Hook `PreToolUse` Claude Code pilnujący zasady 13 z `CLAUDE.md`: historyczne skrypty
analityczne są ZAMROŻONE (odtwarzalne zapisy zakończonych eksperymentów). Lista mieszka
w `runs/ZAMROZONE.txt` — jedna ścieżka względem katalogu głównego repo na linię, `#` zaczyna
komentarz. Gdy narzędzie edycji pliku (Edit / Write / MultiEdit / NotebookEdit) celuje w plik
z listy, hook odpowiada JSON-em `permissionDecision: deny` z wyjaśnieniem; przy zezwoleniu
milczy (stdout pusty). Zawsze kończy się kodem 0.

Ta sama zasada bezpieczeństwa co w `skill_audit.py`: hook NIGDY nie blokuje sesji przez
własny błąd — zły JSON, brak listy, brak pola, wyjątek → cicho zezwala. Odmowa jest jedynym
skutkiem, jaki hook może wywołać, i tylko dla pliku, który jest na liście.

Listę znajduje się, idąc w górę od katalogu EDYTOWANEGO PLIKU (nie od `cwd`), dzięki czemu
hook działa w worktree i przy ścieżkach spoza bieżącego katalogu. Porównanie ścieżek jest
niewrażliwe na wielkość liter i separatory (`\\` vs `/`), bo repo żyje na Windows, a sesja
chmurowa na Linuksie.

Świadome ograniczenie: hook widzi tylko narzędzia edycji plików. Polecenie powłoki
(`sed -i`, przekierowanie `>`) go omija — tam zasada 13 obowiązuje jako zasada, nie automat.

Użycie:
    py tools/frozen_guard.py hook            # tryb hooka (JSON zdarzenia na stdin)
    py tools/frozen_guard.py lista           # wypisz listę i sprawdź, czy pliki istnieją
    py tools/frozen_guard.py sprawdz <plik>  # czy plik jest zamrożony (kod 1 = tak)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

LIST_RELATIVE = Path("runs") / "ZAMROZONE.txt"
GUARDED_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
_PATH_KEYS = ("file_path", "notebook_path")
_GIT_BASH_DRIVE = re.compile(r"^/([A-Za-z])/")

# Tekst trafia do JSON-a z ensure_ascii=True, więc polskie znaki są bezpieczne niezależnie
# od kodowania konsoli; Claude Code odkodowuje je przed pokazaniem.
REASON = (
    "Plik {rel} jest ZAMROŻONY (CLAUDE.md zasada 13: odtwarzalny zapis zakończonego "
    "eksperymentu; lista w runs/ZAMROZONE.txt). Nowy kod pisz w nowym skrypcie na bazie "
    "backtest/checkpoint_lib.py. Jeśli zmiana TEGO pliku jest naprawdę potrzebna, najpierw "
    "usuń go z listy i odnotuj powód w STATUS.md."
)


def normalize(rel: str) -> str:
    """Kanoniczna postać ścieżki względnej: `/` jako separator, bez `./` i `//`, małe litery."""
    parts = [p for p in rel.strip().replace("\\", "/").split("/") if p not in ("", ".")]
    return "/".join(parts).casefold()


def _entries(path: Path) -> list[str]:
    entries = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            entries.append(entry)
    return entries


def read_frozen_list(path: Path) -> set[str]:
    return {normalize(entry) for entry in _entries(path)}


def extract_target_path(payload: object) -> str | None:
    """Ścieżka pliku z `tool_input` (Edit/Write/MultiEdit: `file_path`, NotebookEdit:
    `notebook_path`); None, gdy zdarzenie nie dotyczy narzędzia edycji albo brak pola."""
    if not isinstance(payload, dict) or payload.get("tool_name") not in GUARDED_TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    for key in _PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def absolute_path(raw: str, cwd: str | None, windows: bool = os.name == "nt") -> Path:
    """Ścieżka bezwzględna; względną rozwiązuje względem `cwd` zdarzenia. Na Windows
    przyjmuje też postać Git Bash (`/c/Users/...`)."""
    text = raw.strip()
    match = _GIT_BASH_DRIVE.match(text)
    if windows and match:
        text = f"{match.group(1).upper()}:/{text[3:]}"
    path = Path(text)
    if not path.is_absolute() and cwd:
        path = Path(cwd) / path
    return Path(os.path.abspath(path))


def find_root(file: Path) -> Path | None:
    """Katalog główny repo = pierwszy w górę od pliku, w którym istnieje runs/ZAMROZONE.txt."""
    for candidate in (file.parent, *file.parent.parents):
        if (candidate / LIST_RELATIVE).is_file():
            return candidate
    return None


def frozen_reason(payload: object) -> str | None:
    """Tekst odmowy, gdy edycja celuje w zamrożony plik; None = zezwolić."""
    raw = extract_target_path(payload)
    if raw is None:
        return None
    cwd = payload.get("cwd")
    target = absolute_path(raw, cwd if isinstance(cwd, str) else None)
    root = find_root(target)
    if root is None:
        return None
    try:
        rel = target.relative_to(root)
    except ValueError:
        return None
    if normalize(str(rel)) in read_frozen_list(root / LIST_RELATIVE):
        return REASON.format(rel=rel.as_posix())
    return None


def deny_json(reason: str) -> str:
    # ensure_ascii: wynik nie zależy od kodowania konsoli (cp1250 na Windows).
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        ensure_ascii=True,
    )


def hook_main(raw: bytes | str) -> int:
    """Tryb hooka: czyta zdarzenie, przy zamrożonym pliku wypisuje odmowę. Zawsze 0."""
    try:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        reason = frozen_reason(json.loads(text))
        if reason:
            out = getattr(sys.stdout, "buffer", None)
            line = deny_json(reason) + "\n"
            if out is not None:
                out.write(line.encode("ascii"))
                out.flush()
            else:
                sys.stdout.write(line)
                sys.stdout.flush()
    except Exception:  # noqa: BLE001 — hook nie może zablokować sesji własnym błędem
        pass
    return 0


def list_status(root: Path) -> tuple[list[str], list[str]]:
    """(wpisy listy, wpisy wskazujące na nieistniejące pliki)."""
    entries = _entries(root / LIST_RELATIVE)
    missing = [entry for entry in entries if not (root / entry).is_file()]
    return entries, missing


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "hook"
    if command == "hook":
        return hook_main(sys.stdin.buffer.read())
    root = find_root(Path.cwd() / "_")
    if root is None:
        print(f"Nie znaleziono {LIST_RELATIVE.as_posix()} w bieżącym katalogu ani wyżej.")
        return 2
    if command == "lista":
        entries, missing = list_status(root)
        for entry in entries:
            print(("BRAK  " if entry in missing else "OK    ") + entry)
        print(f"{len(entries)} wpisów, brakujących plików: {len(missing)}")
        return 1 if missing else 0
    if command == "sprawdz" and len(args) == 2:
        payload = {"tool_name": "Edit", "tool_input": {"file_path": args[1]}, "cwd": os.getcwd()}
        reason = frozen_reason(payload)
        print(reason or f"{args[1]}: nie jest na liście zamrożonych.")
        return 1 if reason else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
