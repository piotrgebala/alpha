#!/usr/bin/env bash
# setup_serwer.sh — jednorazowe przygotowanie serwera Linux dla CLAS-5 (2026-09-24).
# Tworzy .venv z przypiętymi wersjami (requirements-lock.txt), dodaje polecenie `py` (komendy
# z CLAUDE.md i hooków działają bez zmian), opcjonalnie rozpakowuje dane i sprawdza dostęp do Binance.
#
#   bash tools/setup_serwer.sh                    # tylko środowisko
#   bash tools/setup_serwer.sh ~/data_raw.zip     # + rozpakowanie danych do data/raw
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || { echo "Potrzebny Python >= 3.11 (jest: $(python3 --version))"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements-lock.txt
ln -sf python .venv/bin/py

ZIP="${1:-}"
if [ -n "$ZIP" ]; then
  n=$(find data/raw -type f ! -name .gitkeep | wc -l)
  if [ "$n" -gt 0 ]; then
    echo "data/raw ma już $n plików — nie rozpakowuję (usuń je ręcznie, jeśli chcesz podmienić)."
  else
    # moduł zipfile, nie `unzip`: poprawne nazwy spoza ASCII (np. 币安人生USDT_1d.parquet)
    .venv/bin/python -m zipfile -e "$ZIP" data/
  fi
fi
echo "Plików w data/raw: $(find data/raw -type f ! -name .gitkeep | wc -l) (paczka z 2026-09-24: 3852)"

code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 https://fapi.binance.com/fapi/v1/time || true)
echo "Binance fapi: HTTP $code (200 = OK; 451/403 = blokada regionu; 000 = brak sieci)"
echo
echo "Gotowe. Dalej:"
echo "  source .venv/bin/activate      # albo dopisz tę linię do ~/.bashrc"
echo "  py -m pytest -q                # oczekiwane: wszystkie testy zielone"
