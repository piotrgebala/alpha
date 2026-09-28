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
# Skille konta spoza tabeli zasady 19, których projekt używa (strony HTML, zużycie tokenów) —
# ukryć ich nie wolno (decyzja użytkownika 2026-09-28, B2).
PROTECTED_SKILLS = {"styl-dashbordow", "explain-usage"}
# Wtyczki konta bez zastosowania w CLAS-5 (B2, pomiar T1 w docs/rag/12).
DISABLED_ACCOUNT_PLUGINS = ("finance@synced", "langfuse@synced", "productivity@synced")


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
    """Ukrywać przed modelem wolno tylko skille spoza tabeli zasady 19 i spoza PROTECTED_SKILLS —
    inaczej skill, którego projekt używa, zniknąłby z listy wyboru po cichu. Wartości: te, które
    Claude Code rozumie."""
    assert rule_19_skills(), "tabela zasady 19 w CLAUDE.md jest pusta?"
    mandatory = rule_19_skills() | PROTECTED_SKILLS
    for name, value in SETTINGS.get("skillOverrides", {}).items():
        assert value in SKILL_OVERRIDE_VALUES, (name, value)
        bare = name.split(":", 1)[-1]
        assert name not in mandatory and bare not in mandatory, name


def test_account_plugins_outside_the_project_stay_disabled():
    """Decyzja użytkownika 2026-09-28 (B2): wtyczki konta `finance`, `langfuse`, `productivity`
    są w sesjach projektu wyłączone — pomiar T1 (docs/rag/12): razem z 6 skillami konta
    w `skillOverrides` 2,4 tys. tokenów startu każdej sesji i subagenta, a projekt ich nie używa.
    Fałsz w ustawieniach projektu przebija włączenie z konta (kolejność: użytkownik < projekt)."""
    plugins = SETTINGS.get("enabledPlugins", {})
    for plugin in DISABLED_ACCOUNT_PLUGINS:
        assert plugins.get(plugin) is False, plugin


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


def test_context_guard_runs_after_every_tool_on_every_prompt_and_in_status_line():
    """Strażnik kontekstu (docs/rag/12): po KAŻDYM narzędziu (bez matchera), na starcie tury
    i w linii statusu; przez `py || python3` jak pozostałe hooki (Windows / serwer / Cowork)."""
    guard = "tools/straznik_kontekstu.py"
    for event in ("PostToolUse", "UserPromptSubmit"):
        matchers = [m for m, command in hooks_for(event) if f'{guard}" hook' in command]
        assert matchers in ([""], ["*"]), event
    status = SETTINGS.get("statusLine", {})
    assert status.get("type") == "command"
    assert f'{guard}" status' in status.get("command", "")
    assert "python3" in status["command"]


# Wtyczki, z których pochodzą skille obowiązkowe (tabela zasady 19). B2 wyłączał wtyczki konta
# spoza projektu — te trzy muszą zostać włączone, inaczej skill znika z listy wyboru po cichu.
MANDATORY_SKILL_PLUGINS = (
    "engineering@synced",
    "data@synced",
    "claude-code-setup@claude-plugins-official",
)
# Przedrostek skilli konta z chmury (`anthropic-skills:<nazwa>`) — to nie wtyczka `enabledPlugins`.
ACCOUNT_SKILLS_PREFIX = "anthropic-skills"


def test_plugins_with_rule_19_skills_stay_enabled():
    """Skille `engineering:…`, `data:…` i `claude-code-setup:…` z tabeli zasady 19 przychodzą
    z wtyczek: wtyczka wyłączona w ustawieniach projektu = skill obowiązkowy niedostępny w każdej
    sesji. Lista pokrywa przedrostki z tabeli (nowy przedrostek w tabeli = dopisz tu wtyczkę)."""
    plugins = SETTINGS.get("enabledPlugins", {})
    for plugin in MANDATORY_SKILL_PLUGINS:
        assert plugins.get(plugin) is True, plugin
    prefixes = {name.split(":", 1)[0] for name in rule_19_skills() if ":" in name}
    assert prefixes - {ACCOUNT_SKILLS_PREFIX} == {
        p.split("@", 1)[0] for p in MANDATORY_SKILL_PLUGINS
    }
