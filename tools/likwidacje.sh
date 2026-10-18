#!/usr/bin/env bash
# likwidacje.sh — kolektory likwidacji pod nadzorem crona:
#   */5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje.sh
# 1) Bybit (data/collect_liquidations_bybit.py, pełne likwidacje, runda LB0) — start W TLE pod własną
#    blokadą flock w swoim katalogu danych ($HOME/likwidacje_bybit); gdy już działa, podproces kończy się
#    od razu. Wyjście: kolektor.out w tym katalogu. Wyłącznik: plik $HOME/likwidacje_bybit/WYLACZONY —
#    gdy istnieje, cron NIE startuje kolektora Bybit (działający proces trzeba wtedy zakończyć ręcznie).
# 2) Binance (data/collect_liquidations.py, próbka, runda LK0) — bez zmian: exec pod blokadą
#    $HOME/likwidacje/.lock (skrypt zamienia się w kolektor i trzyma blokadę).
# Obok (blok 1c): stan rynku Hyperliquid (data/collect_hl_stan.py, runda HS0) — ten sam wzór co Bybit.
# flock trzyma JEDNĄ instancję każdego kolektora na maszynie (blokady w katalogach danych, wspólne dla
# wszystkich klonów); gdy oba działają, skrypt kończy się od razu; gdy któryś padł (błąd, restart
# serwera) — cron wznawia go w ≤ 5 min. Dane POZA repo (pliki dzienne JSONL, status.json,
# kolektor.log, kolektor.out) — niezależne od tego, z którego klonu kolektor wystartował.
# Ręczny start z klonu:
#   nohup bash tools/likwidacje.sh >/dev/null 2>&1 &
# Stan: PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations --dir "$HOME/likwidacje" --status
#       PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations_bybit --status
#       PYTHONUTF8=1 .venv/bin/python -m data.collect_hl_stan --status
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

# 1b) Kopia zapasowa + dzienny indeks (tools/likwidacje_kopia.sh, ETAP 6): wywołanie co 5 min, praca raz
#     na dobę po 00:15 UTC; własna blokada w katalogu kopii. Ten sam podwójny fork co Bybit i PRZED
#     `exec 9>` — kopia nie dziedziczy blokady Binance i nie zatrzymuje kolektorów.
if [ -f tools/likwidacje_kopia.sh ]; then
    ( setsid bash tools/likwidacje_kopia.sh </dev/null >/dev/null 2>&1 & )
fi

# 1c) Stan rynku Hyperliquid (data/collect_hl_stan.py, runda HS0, zadanie 010): `metaAndAssetCtxs` co 60 s
#     do $HOME/likwidacje_hl/stan (zmiana: CLAS5_HL_STAN_DIR). Wzór Bybit: podwójny fork + setsid, PRZED
#     `exec 9>`; własna blokada flock w katalogu danych (fd 7) przekazana kolektorowi przez --blokada-fd 7
#     (kolektor sprawdza, że to ta sama blokada; ręcznie uruchomiony bierze ją sam). Wyłącznik: plik
#     $HOME/likwidacje_hl/stan/WYLACZONY — cron nie startuje kolektora, a działający kończy się przed
#     najbliższą migawką. Kopii poza serwerem nie ma (~20 MB/dobę) — ryzyko zapisane w README rundy HS0.
#     Stan: PYTHONUTF8=1 .venv/bin/python -m data.collect_hl_stan --status
HDIR="${CLAS5_HL_STAN_DIR:-$HOME/likwidacje_hl/stan}"
mkdir -p "$HDIR"
HL_CMD='exec 7>"$1/.lock"; flock -n 7 || exit 0; export PYTHONUTF8=1 OMP_NUM_THREADS=1;
exec .venv/bin/python -m data.collect_hl_stan --dir "$1" --blokada-fd 7 >> "$1/kolektor.out" 2>&1'
if [ ! -e "$HDIR/WYLACZONY" ]; then
    if command -v setsid >/dev/null 2>&1; then
        ( setsid bash -c "$HL_CMD" _ "$HDIR" </dev/null >/dev/null 2>&1 & )
    else
        ( nohup bash -c "$HL_CMD" _ "$HDIR" </dev/null >/dev/null 2>&1 & )
    fi
fi

DIR="${CLAS5_LIKWIDACJE_DIR:-$HOME/likwidacje}"
mkdir -p "$DIR"
exec 9>"$DIR/.lock"
flock -n 9 || exit 0
export PYTHONUTF8=1 OMP_NUM_THREADS=1
exec .venv/bin/python -m data.collect_liquidations --dir "$DIR" >> "$DIR/kolektor.out" 2>&1
