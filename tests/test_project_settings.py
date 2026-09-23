"""
test_project_settings.py

Niezmienniki wspólnej konfiguracji Claude Code (`.claude/settings.json`), która przez repo
trafia do KAŻDEGO środowiska pracującego na projekcie (sesja lokalna, inna maszyna, sesja
chmurowa). Decyzja użytkownika 2026-09-23: wtyczki mają działać w projekcie i w chmurze.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
CLAUDE_MD = (REPO / "CLAUDE.md").read_text(encoding="utf-8")

# Wtyczki z chmury konta claude.ai nie potrzebują źródła w repo — przychodzą synchronizacją.
CLOUD_MARKETPLACE = "synced"
# Wartości `skillOverrides`, które Claude Code rozumie (sprawdzone w kodzie 2.1.280).
SKILL_OVERRIDE_VALUES = {"on", "name-only", "user-invocable-only", "off"}


def hooks_for(event: str) -> list[tuple[str, str]]:
    """(matcher, komenda) każdego hooka zdarzenia."""
    out = []
    for group in SETTINGS.get("hooks", {}).get(event, []):
        for hook in group.get("hooks", []):
            out.append((group.get("matcher", ""), hook.get("command", "")))
    return out


def rule_19_skills() -> set[str]:
    """Nazwy skilli z tabeli „moment pracy → skill” w CLAUDE.md (zasada 19)."""
    table = re.search(r"\| moment pracy \| skill \|\n(.*?)\n\n", CLAUDE_MD, re.S)
    assert table, "tabela zasady 19 nie znaleziona w CLAUDE.md"
    names = set()
    for row in table.group(1).splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) == 2:
            names.update(re.findall(r"`([^`]+)`", cells[1]))
    return names


def test_every_non_cloud_plugin_declares_its_marketplace_in_the_repo():
    """
    Wtyczka włączona w projekcie, ale bez źródła w `extraKnownMarketplaces`, działa tylko na
    maszynie, która to źródło zna z ustawień użytkownika — w każdym innym środowisku po cichu
    się nie wczyta (stan `code-review@claude-plugins-official` do 2026-09-23).
    """
    declared = set(SETTINGS.get("extraKnownMarketplaces", {}))
    missing = sorted(
        plugin
        for plugin, enabled in SETTINGS.get("enabledPlugins", {}).items()
        if enabled and plugin.rsplit("@", 1)[-1] not in declared | {CLOUD_MARKETPLACE}
    )
    assert missing == []


def test_declared_marketplaces_point_to_github_repos():
    for name, entry in SETTINGS.get("extraKnownMarketplaces", {}).items():
        source = entry["source"]
        assert source["source"] == "github", name
        assert source["repo"].count("/") == 1, name


def test_security_guidance_runs_only_pattern_layer():
    """
    Decyzja użytkownika 2026-09-23: z `security-guidance` zostaje tylko szybkie sprawdzanie
    wzorców przy edycji. Przeglądy modelem (diff po każdej turze, agent przy commit/push)
    zużywają limit konta przy wielu commitach dziennie, a celują w błędy aplikacji webowych.
    Wyłączniki sprawdzone w kodzie wtyczki 2.0.8: ENABLE_CODE_SECURITY_REVIEW to wyłącznik
    główny, dwa pozostałe to podwójna blokada na wypadek zmiany jego znaczenia.
    """
    if not SETTINGS.get("enabledPlugins", {}).get("security-guidance@claude-plugins-official"):
        return
    env = SETTINGS.get("env", {})
    for switch in ("ENABLE_CODE_SECURITY_REVIEW", "ENABLE_STOP_REVIEW", "ENABLE_COMMIT_REVIEW"):
        assert env.get(switch) == "0", switch
    assert env.get("ENABLE_PATTERN_RULES", "1") != "0"  # warstwa wzorców zostaje
    assert env.get("SECURITY_GUIDANCE_DISABLE", "") != "1"  # wtyczka nie jest wyłączona


def test_frozen_guard_hook_guards_every_file_editing_tool():
    """Zasada 13 pilnowana programem (T10): hook PreToolUse `tools/frozen_guard.py` na
    KAŻDYM narzędziu edycji plików — luka w matcherze to cicha dziura w zasadzie."""
    matches = [
        (matcher, command)
        for matcher, command in hooks_for("PreToolUse")
        if "tools/frozen_guard.py" in command
    ]
    assert matches, "brak hooka tools/frozen_guard.py w PreToolUse"
    for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        assert any(re.fullmatch(matcher, tool) for matcher, _ in matches), tool


def test_skill_overrides_are_valid_and_never_hide_a_rule_19_skill():
    """Ukrywać przed modelem wolno tylko skille spoza tabeli zasady 19 — inaczej skill
    obowiązkowy zniknąłby z listy wyboru po cichu. Wartości: te, które Claude Code rozumie."""
    mandatory = rule_19_skills()
    assert mandatory, "tabela zasady 19 w CLAUDE.md jest pusta?"
    for name, value in SETTINGS.get("skillOverrides", {}).items():
        assert value in SKILL_OVERRIDE_VALUES, (name, value)
        bare = name.split(":", 1)[-1]
        assert name not in mandatory and bare not in mandatory, name


def test_project_sessions_carry_no_account_connectors():
    """Decyzja użytkownika 2026-09-23 (T10): łączniki konta claude.ai (Gmail, Kalendarz,
    Drive, Docs, Strava) nie mają zastosowania w CLAS-5 — w sesjach projektu wyłączone."""
    assert SETTINGS.get("disableClaudeAiConnectors") is True


def test_every_enabled_plugin_is_documented_in_claude_md():
    """Lista wtyczek w CLAUDE.md ma odzwierciedlać konfigurację (jedna informacja, jedno
    miejsce) — wtyczka włączona, o której CLAUDE.md milczy, to nieaktualny dokument."""
    for plugin, enabled in SETTINGS.get("enabledPlugins", {}).items():
        if enabled:
            assert f"`{plugin.split('@', 1)[0]}`" in CLAUDE_MD, plugin
