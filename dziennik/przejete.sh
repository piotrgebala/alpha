#!/usr/bin/env bash
# przejete.sh — czy dziennik przejęła inna maszyna (serwer)? Używa go tylko uruchom.bat (komputer).
# Kod 0 = tak: w ostatnich 3 dniach na origin/master jest zapis dziennika z nazwą INNEJ maszyny
# („Dziennik: przebieg RRRR-MM-DD (host)”); kod 1 = nie (liczymy dalej na tej maszynie).
cd "$(dirname "$0")/.."
h=$(hostname)
git log origin/master --since='3 days ago' --format='%s' --grep='^Dziennik: przebieg' \
  | grep -E '^Dziennik: przebieg [0-9]{4}-[0-9]{2}-[0-9]{2} \(.+\)$' \
  | grep -vF "($h)" \
  | grep -q .
