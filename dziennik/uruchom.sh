#!/usr/bin/env bash
# uruchom.sh — dziennik CLAS-5 na serwerze Linux (odpowiednik uruchom.bat; dziennik/README.md, poprawka 5).
# Dziennik może działać TYLKO W JEDNYM MIEJSCU naraz (komputer ALBO serwer) — inaczej dwa przebiegi
# dopisują te same dni. Cron (czas serwera w UTC): 30 0 * * * bash /ścieżka/do/alpha/dziennik/uruchom.sh
cd "$(dirname "$0")/.."
export PYTHONUTF8=1
PY=.venv/bin/python
LOG=dziennik/ostatni_wydruk.txt
echo "===== start $(date -u '+%F %T UTC')" >> "$LOG"
"$PY" -m backtest.live_journal >> "$LOG" 2>&1
RC=$?
echo "===== koniec $(date -u '+%F %T UTC'), kod $RC" >> "$LOG"
[ "$RC" -eq 0 ] || exit "$RC"
bash dziennik/zapisz_do_gita.sh >> "$LOG" 2>&1 || true
exit 0
