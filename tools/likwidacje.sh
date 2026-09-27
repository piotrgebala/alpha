#!/usr/bin/env bash
# likwidacje.sh — kolektory likwidacji pod nadzorem crona:
#   */5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje.sh
# 1) Bybit (data/collect_liquidations_bybit.py, pełne likwidacje, runda LB0) — start W TLE pod własną
#    blokadą flock w swoim katalogu danych ($HOME/likwidacje_bybit); gdy już działa, podproces kończy się
#    od razu. Wyjście: kolektor.out w tym katalogu. Wyłącznik: plik $HOME/likwidacje_bybit/WYLACZONY —
#    gdy istnieje, cron NIE startuje kolektora Bybit (działający proces trzeba wtedy zakończyć ręcznie).
# 2) Binance (data/collect_liquidations.py, próbka, runda LK0) — bez zmian: exec pod blokadą
#    $HOME/likwidacje/.lock (skrypt zamienia się w kolektor i trzyma blokadę).
# flock trzyma JEDNĄ instancję każdego kolektora na maszynie (blokady w katalogach danych, wspólne dla
# wszystkich klonów); gdy oba działają, skrypt kończy się od razu; gdy któryś padł (błąd, restart
# serwera) — cron wznawia go w ≤ 5 min. Dane POZA repo (pliki dzienne JSONL, status.json,
# kolektor.log, kolektor.out) — niezależne od tego, z którego klonu kolektor wystartował.
# Ręczny start z klonu:
#   nohup bash tools/likwidacje.sh >/dev/null 2>&1 &
# Stan: PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations --dir "$HOME/likwidacje" --status
#       PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations_bybit --status
cd "$(dirname "$0")/.."

BDIR="${CLAS5_LIKWIDACJE_BYBIT_DIR:-$HOME/likwidacje_bybit}"
mkdir -p "$BDIR"
# Podproces w nowej sesji (setsid): bierze blokadę Bybit (fd 8) i zamienia się w kolektor; blokada
# Binance (fd 9) nie jest jeszcze otwarta, więc kolektor Bybit jej nie dziedziczy (i odwrotnie) —
# ten blok MUSI stać przed `exec 9>`. Podwójny fork `( … & )`: rodzicem kolektora Bybit zostaje init,
# a nie ta powłoka (która za chwilę zamienia się w kolektor Binance i nie zbierałaby jego statusu —
# po awarii Bybit zostawałby proces-zombie).
BYBIT_CMD='exec 8>"$1/.lock"; flock -n 8 || exit 0; export PYTHONUTF8=1 OMP_NUM_THREADS=1;
exec .venv/bin/python -m data.collect_liquidations_bybit --dir "$1" >> "$1/kolektor.out" 2>&1'
if [ ! -e "$BDIR/WYLACZONY" ]; then
    if command -v setsid >/dev/null 2>&1; then
        ( setsid bash -c "$BYBIT_CMD" _ "$BDIR" </dev/null >/dev/null 2>&1 & )
    else
        ( nohup bash -c "$BYBIT_CMD" _ "$BDIR" </dev/null >/dev/null 2>&1 & )
    fi
fi

DIR="${CLAS5_LIKWIDACJE_DIR:-$HOME/likwidacje}"
mkdir -p "$DIR"
exec 9>"$DIR/.lock"
flock -n 9 || exit 0
export PYTHONUTF8=1 OMP_NUM_THREADS=1
exec .venv/bin/python -m data.collect_liquidations --dir "$DIR" >> "$DIR/kolektor.out" 2>&1
