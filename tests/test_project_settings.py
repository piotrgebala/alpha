"""
test_project_settings.py

Niezmienniki wspólnej konfiguracji Claude Code (`.claude/settings.json`), która przez repo
trafia do KAŻDEGO środowiska pracującego na projekcie (sesja lokalna, inna maszyna, sesja
chmurowa). Decyzja użytkownika 2026-09-23: wtyczki mają działać w projekcie i w chmurze.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))

# Wtyczki z chmury konta claude.ai nie potrzebują źródła w repo — przychodzą synchronizacją.
CLOUD_MARKETPLACE = "synced"


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
