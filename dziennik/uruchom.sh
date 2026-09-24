#!/usr/bin/env bash
# uruchom.sh — dziennik CLAS-5 na serwerze Linux (odpowiednik uruchom.bat; dziennik/README.md).
# Dziennik działa TYLKO W JEDNYM MIEJSCU naraz (komputer ALBO serwer) i w OSOBNYM klonie
# (~/alpha-dziennik, zawsze master) — inaczej dwa przebiegi dopisują te same dni.
# Cron: 30 2 * * * bash $HOME/alpha-dziennik/dziennik/uruchom.sh
#   (02:30 czasu serwera; w strefie Europe/Warsaw = 00:30 UTC latem, 01:30 UTC zimą — po zamknięciu
#    dziennej świecy o 00:00 UTC; w strefie UTC = 02:30 UTC — też dobrze)
cd "$(dirname "$0")/.."
exec 9>/tmp/clas5-dziennik.lock
flock -n 9 || { echo "===== inny przebieg dziennika trwa — wyjście" >> dziennik/ostatni_wydruk.txt; exit 0; }
export PYTHONUTF8=1 GIT_TERMINAL_PROMPT=0
PY=.venv/bin/python
LOG=dziennik/ostatni_wydruk.txt
bash dziennik/aktualizuj.sh >> "$LOG" 2>&1
RC=1
for n in 1 2 3; do
  echo "===== start $(date -u '+%F %T UTC') (próba $n)" >> "$LOG"
  "$PY" -m backtest.live_journal >> "$LOG" 2>&1
  RC=$?
  echo "===== koniec $(date -u '+%F %T UTC'), kod $RC" >> "$LOG"
  [ "$RC" -eq 0 ] && break
  [ "$n" -lt 3 ] && sleep 1800
done
[ "$RC" -eq 0 ] || exit "$RC"
bash dziennik/zapisz_do_gita.sh >> "$LOG" 2>&1 || true
exit 0
