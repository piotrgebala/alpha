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
