#!/usr/bin/env bash
# Codzienne odświeżenie strony „Tokeny CLAS-5” (docs/rag/12_zuzycie_tokenow.md).
#
# 1. Monitor `tools/zuzycie_tokenow.py --stan` przelicza dni z zapisów Claude Code tej maszyny
#    i dopisuje je do historii `runs/tokeny/stan.json` (lokalnie, poza gitem).
# 2. Wysyłka pliku do bazy strony: tylko narzędzie ArtifactData sesji Claude połączonej z claude.ai
#    (sesja `claude -p` go nie ma — sprawdzone 2026-09-28). Sposób wysyłki czeka na decyzję użytkownika
#    (STATUS.md); do tego czasu stronę odświeża sesja interaktywna na prośbę „odśwież stronę tokenów”.
set -euo pipefail
cd "$(dirname "$0")/.."
DIR="runs/tokeny"
STAN="$DIR/stan.json"
mkdir -p "$DIR"
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
PYTHONUTF8=1 "$PY" tools/zuzycie_tokenow.py --stan "$STAN"
