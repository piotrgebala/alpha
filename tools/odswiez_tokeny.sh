#!/usr/bin/env bash
# Codzienne odświeżenie strony „Tokeny CLAS-5” — wariant B z docs/rag/12 (decyzja użytkownika 2026-09-28).
#
# 1. Monitor `tools/zuzycie_tokenow.py --wszystkie --stan` przelicza dni z zapisów Claude Code WSZYSTKICH
#    repozytoriów tej maszyny (z podziałem na repo) i dopisuje je do historii `runs/tokeny/stan.json`
#    (lokalnie, poza gitem).
# 2. Stan tej maszyny idzie na gałąź `tokeny-dane` publicznego repo jako `maszyny/<maszyna>.json`
#    (osobny klon `~/alpha-tokeny`, zmienna TOKENY_DANE; nazwa maszyny: TOKENY_MASZYNA albo hostname).
#    `stan.json` w korzeniu gałęzi = suma stanów wszystkich maszyn (`--polacz`). Na gałęzi są same liczby
#    (dni, modele, repozytoria, źródła), bez treści rozmów. Każda maszyna pisze tylko swój plik, więc
#    push z dwóch maszyn nie koliduje; stan.json jest pochodny i budowany na świeżym stanie origin.
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

MASZYNA="$(printf '%s' "${TOKENY_MASZYNA:-$(hostname)}" | tr -c 'A-Za-z0-9._-' '_')"

PYTHONUTF8=1 "$PY" tools/zuzycie_tokenow.py --wszystkie --stan "$STAN"

if [ "$(git -C "$DANE" symbolic-ref --short -q HEAD 2>/dev/null)" != "tokeny-dane" ]; then
  echo "$(teraz) BŁĄD: $DANE nie jest klonem gałęzi tokeny-dane (przygotowanie: docs/rag/12)" >&2
  exit 1
fi
# klon danych jest tylko lustrem gałęzi: świeży stan origin (gdy gałąź już tam jest), potem nasz plik
wyslij() {
  if git -C "$DANE" fetch -q origin tokeny-dane 2>/dev/null; then
    git -C "$DANE" reset -q --hard FETCH_HEAD
  fi
  mkdir -p "$DANE/maszyny"
  cp "$STAN" "$DANE/maszyny/$MASZYNA.json"
  PYTHONUTF8=1 "$PY" tools/zuzycie_tokenow.py --polacz "$DANE/maszyny" --stan "$DANE/stan.json"
  git -C "$DANE" add stan.json maszyny
  if git -C "$DANE" diff --cached --quiet; then
    echo "$(teraz) bez zmian"
    return 2
  fi
  git -C "$DANE" commit -q -m "Tokeny: stan $(date -u +%F) ($MASZYNA)"
  git -C "$DANE" push -q origin tokeny-dane
}
rc=0
wyslij || rc=$?
if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
  echo "$(teraz) push odrzucony — ponawiam raz na świeżym stanie origin" >&2
  rc=0
  wyslij || rc=$?
fi
[ "$rc" -eq 2 ] && exit 0
[ "$rc" -ne 0 ] && exit "$rc"
echo "$(teraz) wysłano stan.json ($(wc -c <"$DANE/stan.json") B, maszyna $MASZYNA) na gałąź tokeny-dane"
