#!/usr/bin/env bash
# zapisz_do_gita.sh — po udanym przebiegu dziennika: commit plików dziennika i push na master
# (poprawka 5, decyzja użytkownika 2026-09-24; poprawki po przeglądzie tego samego dnia).
#
# Działa w OSOBNYM klonie dziennika (C:\Users\pitge\GIT\alpha-dziennik, na serwerze ~/alpha-dziennik),
# w którym nikt nie pracuje. Mimo to zachowuje się bezpiecznie także w cudzej kopii roboczej:
# - tylko na gałęzi master, nigdy w trakcie rebase / przy blokadzie indeksu;
# - commituje wyłącznie pliki dziennika (jawna lista ścieżek);
# - nie chowa niczyich zmian (--no-autostash) i nie ściąga zmian do brudnej kopii;
# - nie wypycha, jeśli na lokalnym master są niewypchnięte zmiany spoza dziennika;
# - przy konflikcie przerywa rebase; commit zostaje lokalnie, następny przebieg spróbuje ponownie.
# Każdy wynik kończy się linią „===== zapis do gita: …” w dziennik/ostatni_wydruk.txt.
set -u
cd "$(dirname "$0")/.."
export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never  # bez okien logowania w zadaniu w tle
export GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=60  # zerwana sieć = błąd po minucie, nie wiszenie

say() { echo "===== zapis do gita: $*"; }

gitdir=$(git rev-parse --git-dir) || { say "to nie jest repo git"; exit 1; }
if [ -d "$gitdir/rebase-merge" ] || [ -d "$gitdir/rebase-apply" ] || [ -f "$gitdir/MERGE_HEAD" ]; then
  say "pominięty — repo w trakcie rebase/merge (napraw ręcznie)"
  exit 1
fi
if [ -f "$gitdir/index.lock" ]; then
  say "pominięty — blokada indeksu (.git/index.lock); inny proces gita albo pozostałość po awarii"
  exit 1
fi
br=$(git rev-parse --abbrev-ref HEAD)
if [ "$br" != "master" ]; then
  say "pominięty — gałąź $br, nie master"
  exit 0
fi

files=()
for f in dziennik/*.csv dziennik/przebiegi.log; do
  [ -f "$f" ] && files+=("$f")
done
if [ "${#files[@]}" -eq 0 ]; then
  say "brak plików dziennika — nic do zapisania"
  exit 1
fi
git add -- "${files[@]}" || { say "git add nieudany"; exit 1; }
if git diff --cached --quiet -- "${files[@]}"; then
  say "brak zmian"
else
  git commit -q -m "Dziennik: przebieg $(date -u '+%F') ($(hostname))" -- "${files[@]}" || { say "commit nieudany"; exit 1; }
fi

git fetch -q origin master || { say "fetch nieudany — commit zostaje lokalnie"; exit 1; }
if [ -z "$(git rev-list origin/master..master)" ]; then
  say "nic do wypchnięcia"
  exit 0
fi
if [ -n "$(git diff --name-only origin/master...master -- . ':(exclude)dziennik')" ]; then
  say "push pominięty — na lokalnym master są niewypchnięte zmiany spoza dziennika"
  exit 1
fi
if git push -q origin master; then
  say "wypchnięte"
  exit 0
fi
# origin przesunął się (np. praca z serwera) — rebase tylko w czystej kopii, bez chowania zmian
if [ -n "$(git status --porcelain --untracked-files=no -- . ':(exclude)dziennik')" ]; then
  say "push odrzucony, kopia robocza ma niezacommitowane zmiany — bez pull; commit zostaje lokalnie"
  exit 1
fi
if git pull -q --rebase --no-autostash origin master && git push -q origin master; then
  say "wypchnięte po pull --rebase"
  exit 0
fi
git rebase --abort 2>/dev/null
say "push nieudany — commit zostaje lokalnie, następny przebieg spróbuje ponownie"
exit 1
