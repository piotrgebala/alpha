#!/usr/bin/env bash
# aktualizuj.sh — przed przebiegiem dziennika: kod z origin/master (uruchom.bat i uruchom.sh).
# Samonaprawa w klonie dziennika: gdy rebase się nie udaje (np. obie maszyny policzyły tę samą noc
# i ta przegrała wyścig o push), a lokalnie różnią się WYŁĄCZNIE pliki dziennika — przyjmuje stan
# origin/master; przebieg dopisze wtedy bieżący dzień. Nigdy nie rusza cudzej pracy spoza dziennik/.
cd "$(dirname "$0")/.."
export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=60
if [ "$(git rev-parse --abbrev-ref HEAD)" != "master" ]; then
  echo "===== aktualizacja kodu pominięta — gałąź nie master"
  exit 0
fi
if ! git fetch -q origin master; then
  echo "===== aktualizacja kodu nieudana (fetch) — przebieg na dotychczasowym kodzie"
  exit 0
fi
git pull -q --rebase --no-autostash origin master && exit 0
git rebase --abort 2>/dev/null
if [ -z "$(git diff --name-only origin/master...HEAD -- . ':(exclude)dziennik')" ] \
  && [ -z "$(git status --porcelain --untracked-files=no -- . ':(exclude)dziennik')" ]; then
  git reset -q --hard origin/master
  echo "===== samonaprawa: lokalne commity dziennika zastąpione stanem origin/master; przebieg dopisze bieżący dzień"
  exit 0
fi
echo "===== aktualizacja kodu nieudana — przebieg na dotychczasowym kodzie"
