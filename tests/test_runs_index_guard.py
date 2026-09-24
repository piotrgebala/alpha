"""
Strażnik księgi rund (CLAUDE.md zasady 11, 14, 19): `runs/INDEX.md` i katalogi `runs/` muszą się
zgadzać, a runda zamknięta od 2026-09-24 musi mieć komplet dokumentacji. Wcześniej pilnowała tego
tylko prośba w instrukcji; wskazówka z przeglądu AI_devs (`docs/rag/Repo lessons i sigma — co
przydatne dla alpha.md`): „strażnik w kodzie przed wpisem do INDEX, nie prośba w prompcie”.

Na gałęzi rundy między pre-rejestracją a zamknięciem test jest ŚWIADOMIE czerwony (katalog bez
wiersza w INDEX, status PRE-REJESTRACJA) — zielony pytest to warunek scalenia, nie commitu
pre-rejestracji.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RUNS = Path(__file__).resolve().parents[1] / "runs"
INDEX = RUNS / "INDEX.md"
DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_[a-z0-9][a-z0-9.\-]*$")
LINK_RE = re.compile(r"\]\((\d{4}-\d{2}-\d{2}_[^)/]+)/README\.md\)")
STRICT_FROM = "2026-09-24"  # od tej daty wymagany pełny komplet (starsze rundy — stan zastany)


def _run_dirs() -> list[Path]:
    return sorted(p for p in RUNS.iterdir() if p.is_dir() and DIR_RE.match(p.name))


def _index_links() -> set[str]:
    return set(LINK_RE.findall(INDEX.read_text(encoding="utf-8")))


def test_every_index_link_has_readme():
    missing = sorted(d for d in _index_links() if not (RUNS / d / "README.md").is_file())
    assert not missing, f"INDEX wskazuje na rundy bez README: {missing}"


def test_every_run_dir_is_in_index():
    linked = _index_links()
    orphans = [p.name for p in _run_dirs() if p.name not in linked]
    assert not orphans, f"katalogi rund bez wiersza w runs/INDEX.md: {orphans}"


def test_run_dir_names_are_valid():
    bad = [
        p.name
        for p in RUNS.iterdir()
        if p.is_dir() and p.name[:2] == "20" and not DIR_RE.match(p.name)
    ]
    assert not bad, f"nazwy katalogów niezgodne z YYYY-MM-DD_<id>-<slug>: {bad}"


def _strict_dirs() -> list[Path]:
    return [p for p in _run_dirs() if DIR_RE.match(p.name).group(1) >= STRICT_FROM]


@pytest.mark.parametrize("run", _strict_dirs(), ids=lambda p: p.name)
def test_recent_run_is_complete(run: Path):
    text = (run / "README.md").read_text(encoding="utf-8")
    low = text.lower()
    problems = []
    if "pre-rejestracja" not in low:
        problems.append("brak pre-rejestracji")
    if not re.search(r"^## Wniosek", text, flags=re.M):
        problems.append("brak sekcji '## Wniosek'")
    if "użyte skille" not in low:
        problems.append("brak sekcji „Użyte skille” (zasada 19)")
    if not any(run.glob("raw_output*.txt")) and not any(run.glob("moc*.txt")):
        problems.append("brak raw_output*.txt / moc*.txt (zasada 11)")
    if re.search(r"^> \*\*STATUS: PRE-REJESTRACJA", text, flags=re.M):
        problems.append("status nadal PRE-REJESTRACJA, a runda jest w INDEX")
    assert not problems, f"{run.name}: " + "; ".join(problems)
