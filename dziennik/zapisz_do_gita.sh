#!/usr/bin/env bash
# zapisz_do_gita.sh — po udanym przebiegu dziennika: commit plików dziennika i push na master
# (poprawka 5, decyzja użytkownika 2026-09-24). Tylko na gałęzi master; tylko pliki dziennika;
# przy konflikcie nic nie psuje — przerywa rebase i zostawia commit lokalnie do następnego razu.
set -u
cd "$(dirname "$0")/.."
export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never  # bez okien logowania w zadaniu w tle
br=$(git rev-parse --abbrev-ref HEAD)
if [ "$br" != "master" ]; then
  echo "===== zapis do gita pominięty: gałąź $br, nie master"
  exit 0
fi
files=$(ls dziennik/*.csv dziennik/przebiegi.log 2>/dev/null)
git add -- $files
if git diff --cached --quiet; then
  echo "===== zapis do gita: brak zmian"
  exit 0
fi
git commit -q -m "Dziennik: przebieg $(date -u '+%F')" -- $files || { echo "===== commit nieudany"; exit 1; }
if git push -q origin master 2>/dev/null; then
  echo "===== zapis do gita: wypchnięte"
  exit 0
fi
# ktoś inny wypchnął wcześniej (np. praca z serwera) — dociągnij i spróbuj raz jeszcze
if git pull -q --rebase --autostash origin master; then
  git push -q origin master && echo "===== zapis do gita: wypchnięte po pull --rebase" && exit 0
else
  git rebase --abort 2>/dev/null
fi
echo "===== zapis do gita: push nieudany — commit zostaje lokalnie, następny przebieg spróbuje ponownie"
exit 1
