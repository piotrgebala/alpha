#!/usr/bin/env bash
# Codzienne odświeżenie strony „Tokeny CLAS-5” — wariant B z docs/rag/12 (decyzja użytkownika 2026-09-28).
#
# 1. Monitor `tools/zuzycie_tokenow.py --stan` przelicza dni z zapisów Claude Code projektu na tej maszynie
#    i dopisuje je do historii `runs/tokeny/stan.json` (lokalnie, poza gitem).
# 2. Kopia pliku idzie na gałąź `tokeny-dane` publicznego repo: osobny klon `~/alpha-tokeny` (zmienna
#    TOKENY_DANE), commit + push. Na gałęzi są same liczby (dni, modele, źródła), bez treści rozmów.
# 3. Rutyna Cowork (05:00 UTC) klonuje tę gałąź jako dane i zapisuje stan.json do bazy strony.
# Cron serwera: 30 4 * * * bash $HOME/alpha/tools/odswiez_tokeny.sh >> $HOME/alpha/runs/tokeny/cron.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."
DIR="runs/tokeny"
STAN="$DIR/stan.json"
DANE="${TOKENY_DANE:-$HOME/alpha-tokeny}"
teraz() { date -u +%FT%TZ; }
mkdir -p "$DIR"
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

PYTHONUTF8=1 "$PY" tools/zuzycie_tokenow.py --stan "$STAN"

if [ "$(git -C "$DANE" symbolic-ref --short -q HEAD 2>/dev/null)" != "tokeny-dane" ]; then
  echo "$(teraz) BŁĄD: $DANE nie jest klonem gałęzi tokeny-dane (przygotowanie: docs/rag/12)" >&2
  exit 1
fi
cp "$STAN" "$DANE/stan.json"
git -C "$DANE" add stan.json
if git -C "$DANE" diff --cached --quiet; then
  echo "$(teraz) bez zmian"
  exit 0
fi
git -C "$DANE" commit -q -m "Tokeny: stan $(date -u +%F) ($(hostname))"
git -C "$DANE" push -q origin tokeny-dane
echo "$(teraz) wysłano stan.json ($(wc -c <"$DANE/stan.json") B) na gałąź tokeny-dane"
