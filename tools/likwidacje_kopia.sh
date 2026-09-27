#!/usr/bin/env bash
# likwidacje_kopia.sh — kopia zapasowa likwidacji (data/liquidation_backup.py) pod cronem; linię crona
# dodaje koordynator/użytkownik (tu jej NIE instalujemy), np.:
#   */5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje_kopia.sh
# Wywołanie co 5 min robi pracę raz na dobę (pierwsze po 00:15 UTC; znacznik .ostatni_przebieg);
# ręcznie od razu:  bash tools/likwidacje_kopia.sh --teraz
# flock trzyma JEDNĄ instancję (blokada w katalogu kopii). Kopia tylko CZYTA katalogi kolektorów
# ($HOME/likwidacje, $HOME/likwidacje_bybit) i działa z niskim priorytetem CPU i dysku — nie zatrzymuje
# kolektorów. Po błędzie ponawia najwcześniej po 60 min; zaległy push ponawia sam (co 60 min).
# Katalog kopii: ${CLAS5_KOPIA_DIR:-$HOME/likwidacje_kopia} (lokalne repo git; push tylko przy
# skonfigurowanym origin, klucz ${CLAS5_KOPIA_KEY:-$HOME/.ssh/likwidacje_deploy}).
# Stan: kopia.log, status.json i manifest.csv w katalogu kopii; wydruk przebiegu w kopia.out.
cd "$(dirname "$0")/.." || exit 1
KOPIA="${CLAS5_KOPIA_DIR:-$HOME/likwidacje_kopia}"
PY="${CLAS5_PYTHON:-.venv/bin/python}"
mkdir -p "$KOPIA"
exec 9>"$KOPIA/.lock"
flock -n 9 || exit 0
export PYTHONUTF8=1 OMP_NUM_THREADS=1
# ionice -c3 (dysk tylko w bezczynności) + nice: kopia nie konkuruje z kolektorami o dysk i CPU
IONICE=()
command -v ionice >/dev/null 2>&1 && IONICE=(ionice -c3)
"${IONICE[@]}" nice -n 10 "$PY" -m data.liquidation_backup --kopia "$KOPIA" "$@" >> "$KOPIA/kopia.out" 2>&1
