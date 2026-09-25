#!/usr/bin/env bash
# likwidacje.sh — kolektor likwidacji Binance (data/collect_liquidations.py) pod nadzorem crona:
#   */5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje.sh
# flock trzyma JEDNĄ instancję na maszynie (blokada w katalogu danych, wspólna dla wszystkich klonów);
# gdy kolektor działa, skrypt kończy się od razu; gdy padł (błąd, restart serwera) — cron wznawia go
# w ≤ 5 min. Dane POZA repo: $HOME/likwidacje (pliki dzienne JSONL, status.json, kolektor.log,
# kolektor.out) — niezależne od tego, z którego klonu kolektor wystartował. Ręczny start z klonu:
#   nohup bash tools/likwidacje.sh >/dev/null 2>&1 &
# Stan: PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations --dir "$HOME/likwidacje" --status
cd "$(dirname "$0")/.."
DIR="${CLAS5_LIKWIDACJE_DIR:-$HOME/likwidacje}"
mkdir -p "$DIR"
exec 9>"$DIR/.lock"
flock -n 9 || exit 0
export PYTHONUTF8=1 OMP_NUM_THREADS=1
exec .venv/bin/python -m data.collect_liquidations --dir "$DIR" >> "$DIR/kolektor.out" 2>&1
