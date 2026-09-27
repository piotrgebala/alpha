"""Stan dziennika CLAS-5 → JSON dla strony „Dziennik CLAS-5” (artefakt claude.ai, podgląd na tablecie).

Uruchamia go codzienna rutyna w chmurze Claude (06:30 UTC, po nocnym przebiegu dziennika): klonuje
repo, pobiera TEN plik z origin/master, a wynik zapisuje w bazie strony (ArtifactData, kolekcja
„dziennik”, dokument „stan”). Tylko biblioteka standardowa — rutyna nie instaluje zależności.
Czyta wyłącznie origin/master:dziennik/* i commity „Dziennik: przebieg …”; niczego nie zapisuje
w repo. Ostatnia linia wydruku to gotowe zdanie do powiadomienia: „Dziennik odświeżony: …” albo
„UWAGA: …” (kontrole a–e). Pusty stan albo błąd gita = kod wyjścia 1 i brak pliku wyjściowego,
żeby strona nie dostała pustych danych.

    python3 tools/strona_dziennika.py <klon repo alpha> <plik wyjściowy .json>

Format linii `dziennik/przebiegi.log` pilnuje tests/test_strona_dziennika.py (każda linia z repo
musi się czytać). Nowe pole dopisane w logu przed „historia zmieniona” czyta się samo; zmiana pól
podstawowych wymaga zmiany LOG_RE.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import statistics
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

REF = "origin/master"
R1_START, X1_START, READING = "2026-09-24", "2026-09-25", "2026-12-25"
TH = {"r1": {"warn": 0.184, "stop": 0.276}, "x1": {"warn": 0.55, "stop": 0.825}}
LEV = {"trend": 2.0, "coinbase": 3.0}

TS_START = re.compile(r"^\d{4}-\d{2}-\d{2}T")
COMMIT_RE = re.compile(r"Dziennik: przebieg (\d{4}-\d{2}-\d{2})(?: \((.+)\))?$")
LOG_RE = re.compile(
    r"^(?P<ts>\S+) \| as_of (?P<as_of>\S+) \| binance (?P<binance>\S+) \| premia (?P<premia>\S+) \| "
    r"sygnały \+(?P<sig>\d+) \| wyniki \+(?P<res>\d+) \| kapitał (?P<eq>\S+) \| "
    r"obsunięcie (?P<dd>\S+)% \| (?P<status>[^|]+?)(?: \| X1 (?P<x1>[^|]+?))?"
    r"(?: \| stan rynku (?P<stan>[^|]+?))?(?: \| (?!historia zmieniona)[^|]+?)*"
    r" \| historia zmieniona: (?P<ch>\d+)\s*$"
)


def git(repo: str, *args: str, check: bool = False) -> str:
    """Wyjście `git -C repo …` (UTF-8). check=True: błąd gita przerywa (zły klon, brak refu)."""
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.strip()[:200]}")
    return proc.stdout


def rows(repo: str, name: str) -> list[dict]:
    """Wiersze `origin/master:dziennik/<name>`; brak pliku = pusta lista."""
    txt = git(repo, "show", f"{REF}:dziennik/{name}")
    return list(csv.DictReader(io.StringIO(txt))) if txt.strip() else []


def num(x, n: int = 6) -> float | None:
    """Liczba zaokrąglona do n miejsc; brak, tekst, NaN i nieskończoność → None."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return round(v, n) if v == v and abs(v) != float("inf") else None


def parse_commits(text: str) -> list[dict]:
    """Linie `%cI|%s` z git log → commity „Dziennik: przebieg <data> (<maszyna>)”."""
    out = []
    for line in text.splitlines():
        ts, _, subj = line.partition("|")
        m = COMMIT_RE.match(subj.strip())
        if m:
            utc = datetime.fromisoformat(ts).astimezone(timezone.utc)
            out.append({"ts": utc.isoformat(timespec="minutes"), "date": m[1], "host": m[2] or ""})
    return out


def log_records(text: str) -> list[str]:
    """Linie logu → rekordy. Linia bez znacznika czasu na początku to ciąg poprzedniej
    (np. wieloliniowy komunikat błędu w polu X1) — dokleja się ją, zamiast liczyć jako nieczytelną.
    """
    recs: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if recs and not TS_START.match(s):
            recs[-1] += " " + s
        else:
            recs.append(s)
    return recs


def parse_log(text: str) -> tuple[list[dict], int]:
    """`przebiegi.log` → (przebiegi posortowane po czasie, liczba rekordów nieczytelnych)."""
    runs, bad = [], 0
    for rec in log_records(text):
        m = LOG_RE.match(rec)
        if not m:
            bad += 1
            continue
        d = m.groupdict()
        try:
            t = datetime.fromisoformat(d["ts"]).astimezone(timezone.utc)
        except ValueError:
            bad += 1
            continue
        runs.append(
            {
                "ts": t.isoformat(timespec="minutes"),
                "day": t.date().isoformat(),
                "as_of": d["as_of"],
                "binance": d["binance"],
                "premia": d["premia"],
                "sig": int(d["sig"]),
                "res": int(d["res"]),
                "eq": num(d["eq"]),
                "dd": num(d["dd"], 2),
                "status": d["status"].strip(),
                "x1": (d["x1"] or "").strip(),
                "stan": (d["stan"] or "").strip(),
                "changed": int(d["ch"]),
            }
        )
    runs.sort(key=lambda r: r["ts"])
    return runs, bad


def _net(rs: list[dict]) -> dict[str, float]:
    """Ekspozycja netto per symbol (suma po fazach)."""
    net: dict[str, float] = {}
    for r in rs:
        net[r["symbol"]] = net.get(r["symbol"], 0.0) + float(r["exposure"])
    return net


def _split(rs: list[dict]) -> tuple[list[dict], list[dict]]:
    tr = [r for r in rs if r["component"] == "trend"]
    cb = [r for r in rs if r["component"] == "coinbase"]
    return tr, cb


def _positions(repo: str, sig: list[dict], d: str) -> dict:
    """Pozycje na dzień d (ostatni as_of): trend, premia Coinbase, zlecenia dnia, X1."""
    rs = [r for r in sig if r["as_of"] == d]
    tr, cb = _split(rs)
    nt = sorted(_net(tr).items(), key=lambda kv: -kv[1])
    nc = _net(cb)
    k = {
        c: num(next((r["k"] for r in rs if r["component"] == c), None), 4)
        for c in ("trend", "coinbase")
    }
    x1rows = [r for r in rows(repo, "x1_sygnaly.csv") if r["as_of"] == d]
    xnet: dict[str, float] = {}
    for r in x1rows:
        xnet[r["symbol"]] = xnet.get(r["symbol"], 0.0) + float(r["weight"])
    x1 = None
    if x1rows:
        x1 = {
            "long": sorted(
                [[s, num(v, 5)] for s, v in xnet.items() if v > 1e-12], key=lambda z: -z[1]
            ),
            "short": sorted(
                [[s, num(v, 5)] for s, v in xnet.items() if v < -1e-12], key=lambda z: z[1]
            ),
        }
    return {
        "as_of": d,
        "for_day": (date.fromisoformat(d) + timedelta(days=1)).isoformat(),
        "k": k,
        "cb": {
            "exposure": num(sum(nc.values()), 5),
            "margin": num(sum(float(r["margin"]) for r in cb), 5),
            "symbol": next(iter(nc), "BTCUSDT"),
        },
        "trend": {
            "long": sum(v > 0 for _, v in nt),
            "short": sum(v < 0 for _, v in nt),
            "net": num(sum(v for _, v in nt), 5),
            "gross": num(sum(abs(v) for _, v in nt), 5),
            "margin_phases": num(sum(float(r["margin"]) for r in tr), 5),
            "margin_net": num(sum(abs(v) for _, v in nt) / LEV["trend"], 5),
            "top_long": [[s, num(v, 5)] for s, v in nt if v > 0][:10],
            "top_short": [[s, num(v, 5)] for s, v in reversed(nt) if v < 0][:6],
        },
        "orders": [
            {"comp": r["component"], "sym": r["symbol"], "exp": num(r["exposure"], 5)}
            for r in rs
            if r["today"] == "True"
        ],
        "x1": x1,
    }


def build_state(repo: str, now: datetime) -> tuple[dict, int]:
    """Stan strony z origin/master klonu `repo` na chwilę `now` (UTC) → (stan, liczba przebiegów)."""
    expected = (now.date() - timedelta(days=1)).isoformat()

    # --- commity zapisu dziennika
    log_fmt = ("log", REF, "--grep=^Dziennik: przebieg", "--format=%cI|%s")
    commits = parse_commits(git(repo, *log_fmt, check=True))
    by_day: dict[str, set] = {}
    for c in commits:
        if c["host"]:
            by_day.setdefault(c["date"], set()).add(c["host"])
    last_day = max((c["date"] for c in commits), default=None)

    # --- przebiegi.log
    runs, bad_lines = parse_log(git(repo, "show", f"{REF}:dziennik/przebiegi.log"))
    first_result_ts = next((r["ts"] for r in runs if r["res"] > 0), None)

    # --- wyniki
    res = rows(repo, "wyniki.csv")
    keys = ("dates", "equity", "drawdown", "r", "r_trend", "r_cb", "k_trend", "k_cb")
    r1: dict[str, list] = {k: [] for k in keys}
    for r in res:
        r1["dates"].append(r["date"])
        r1["equity"].append(num(r["equity"]))
        r1["drawdown"].append(num(r["drawdown"]))
        r1["r"].append(num(r["r_port"]))
        r1["r_trend"].append(num(r["r_trend"]))
        r1["r_cb"].append(num(r["r_coinbase"]))
        r1["k_trend"].append(num(r["k_trend"], 4))
        r1["k_cb"].append(num(r["k_coinbase"], 4))
    xr = rows(repo, "x1_wyniki.csv")
    x1 = None
    if xr:
        x1 = {
            "dates": [r["date"] for r in xr],
            "equity": [num(r["equity"]) for r in xr],
            "drawdown": [num(r["drawdown"]) for r in xr],
            "r": [num(r.get("r_x1")) for r in xr],
        }

    # --- sygnały: dzienne agregaty i pozycje na ostatni as_of
    sig = rows(repo, "sygnaly.csv")
    days = sorted({r["as_of"] for r in sig})
    daily: dict[str, list] = {
        "as_of": [],
        "margin_phases": [],
        "margin_net": [],
        "trend_net": [],
        "cb_exposure": [],
    }
    for d in days:
        rs = [r for r in sig if r["as_of"] == d]
        tr, cb = _split(rs)
        mnet = (
            sum(abs(v) for v in _net(tr).values()) / LEV["trend"]
            + sum(abs(v) for v in _net(cb).values()) / LEV["coinbase"]
        )
        daily["as_of"].append(d)
        daily["margin_phases"].append(num(sum(float(r["margin"]) for r in rs), 5))
        daily["margin_net"].append(num(mnet, 5))
        daily["trend_net"].append(num(sum(_net(tr).values()), 5))
        daily["cb_exposure"].append(num(sum(_net(cb).values()), 5))
    pos = _positions(repo, sig, days[-1]) if days else None

    # --- stan rynku
    st = rows(repo, "stan_rynku.csv")
    market = None
    if st:
        market = {
            "dates": [r["date"] for r in st],
            "vol30": [num(r["btc_vol30"], 4) for r in st],
            "stan": [r["vol_stan"] for r in st],
            "r90": [num(r["btc_r90"], 4) for r in st],
            "trend90": [int(float(r["trend90"] or 0)) for r in st],
        }

    # --- kryteria mechaniki (README dziennika, odczyt ok. 25.12)
    start_asof = date.fromisoformat(R1_START) - timedelta(days=1)
    exp_days = []
    if expected >= start_asof.isoformat():
        span = (date.fromisoformat(expected) - start_asof).days + 1
        exp_days = [(start_asof + timedelta(days=i)).isoformat() for i in range(span)]
    missing = [d for d in exp_days if d not in days]
    first_run_of_day: dict[str, dict] = {}
    for r in runs:
        first_run_of_day.setdefault(r["day"], r)
    late = [
        dd
        for dd, r in first_run_of_day.items()
        if (date.fromisoformat(dd) - date.fromisoformat(r["as_of"])).days > 1
    ]
    events = [
        {
            "ts": r["ts"],
            "as_of": r["as_of"],
            "n": r["changed"],
            "before_first_result": bool(first_result_ts) and r["ts"] < first_result_ts,
        }
        for r in runs
        if r["changed"] > 0
    ]
    mp = [m for m in daily["margin_phases"] if m is not None]
    k_trend = max((k for k in r1["k_trend"] if k is not None), default=None)
    k_cb = max((k for k in r1["k_cb"] if k is not None), default=None)

    state = {
        "v": 1,
        "generated_at": now.isoformat(timespec="minutes"),
        "expected_as_of": expected,
        "repo": {
            "head": git(repo, "rev-parse", "--short", REF, check=True).strip(),
            "head_ts": git(repo, "log", "-1", "--format=%cI", REF).strip(),
        },
        "start": {"r1": R1_START, "x1": X1_START, "reading": READING},
        "thresholds": TH,
        "last_run": runs[-1] if runs else None,
        "log_tail": runs[-14:],
        "log_unparsed": bad_lines,
        "commits": commits[:40],
        "health": {
            "last_journal_date": last_day,
            "hosts_last_day": sorted(by_day.get(last_day, [])),
            "double_days": sorted(d for d, h in by_day.items() if len(h) > 1),
            "latest_as_of": days[-1] if days else None,
            "history_events": events,
        },
        "criteria": {
            "completeness": {
                "days": len(exp_days),
                "covered": len(exp_days) - len(missing),
                "missing": missing,
            },
            "timeliness": {"days": len(first_run_of_day), "late": sorted(late)},
            "consistency": {
                "events": len(events),
                "after_first_result": sum(not e["before_first_result"] for e in events),
            },
            "margin": {
                "median": num(statistics.median(mp), 5) if mp else None,
                "min": num(min(mp), 5) if mp else None,
                "max": num(max(mp), 5) if mp else None,
                "n": len(mp),
            },
            "k_max": {"trend": k_trend, "coinbase": k_cb, "cap": 2.0},
        },
        "r1": r1,
        "x1": x1,
        "daily": daily,
        "positions": pos,
        "market": market,
    }
    return state, len(runs)


def require_nonempty(state: dict) -> None:
    """Pusty stan (zły klon, zmieniony format plików) nie może nadpisać strony."""
    empty = [
        name
        for name, part in (
            ("wyniki R1", state["r1"]["dates"]),
            ("przebiegi", state["log_tail"]),
            ("sygnały", state["daily"]["as_of"]),
        )
        if not part
    ]
    if empty:
        raise ValueError(f"pusty stan dziennika ({', '.join(empty)}) — strona zostaje bez zmian")


def checks(state: dict) -> list[str]:
    """Kontrole a–e (dawniej w treści rutyny); pusta lista = wszystko w porządku."""
    probs = []
    latest, exp = state["health"]["latest_as_of"], state["expected_as_of"]
    if latest != exp:
        probs.append(f"(a) dane za {latest}, oczekiwane za {exp}")
    after = state["criteria"]["consistency"]["after_first_result"]
    if after:
        probs.append(f"(b) historia zmieniona po pierwszym wyniku: {after} raz(y)")
    for key, label in (("r1", "R1"), ("x1", "X1")):
        part = state.get(key)
        if part is None and key == "x1":
            continue
        dd = [v for v in (part or {}).get("drawdown", []) if v is not None]
        warn = TH[key]["warn"]
        if not dd:
            probs.append(f"(c) brak obsunięcia {label}")
        elif dd[-1] >= warn:
            probs.append(
                f"(c) obsunięcie {label} {100 * dd[-1]:.1f} % "
                f"(próg ostrzeżenia {100 * warn:.1f} %)"
            )
    hosts = state["health"]["hosts_last_day"]
    if len(hosts) > 1:
        probs.append(f"(d) ostatni dzień zapisało {len(hosts)} maszyn: {', '.join(hosts)}")
    if state["log_unparsed"]:
        probs.append(f"(e) nieczytelne linie przebiegi.log: {state['log_unparsed']}")
    return probs


def verdict_line(state: dict, probs: list[str]) -> str:
    """Jedno zdanie do powiadomienia na telefon."""
    if probs:
        return "UWAGA: " + "; ".join(probs) + "."
    eq = [v for v in state["r1"]["equity"] if v is not None]
    last = eq[-1] if eq else "brak"
    return f"Dziennik odświeżony: dane za {state['health']['latest_as_of']}, kapitał R1 {last}."


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("Użycie: python3 tools/strona_dziennika.py <klon repo alpha> <plik .json>")
        return 2
    repo, out_path = args
    try:
        state, n_runs = build_state(repo, datetime.now(timezone.utc))
        require_nonempty(state)
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"BŁĄD: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, separators=(",", ":"))
    print(
        f"OK {out_path}: {os.path.getsize(out_path)} B, as_of {state['health']['latest_as_of']}, "
        f"wyniki {len(state['r1']['dates'])}, przebiegi {n_runs} "
        f"(nieprzeczytane {state['log_unparsed']}), head {state['repo']['head']}"
    )
    print(verdict_line(state, checks(state)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
