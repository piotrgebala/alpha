"""zuzycie_tokenow.py — ile tokenów zużywa praca Claude Code nad projektem i na co (monitor, tylko odczyt).

Po co (prośba użytkownika 2026-09-28: „monitorować zużycie i optymalizować bez utraty jakości”): pomiar
PRZED jakąkolwiek optymalizacją. Pierwszy pomiar (docs/rag/12) pokazał, że koszt nie siedzi tam, gdzie
podejrzewano (wyjścia narzędzi), tylko w długości głównej sesji, przepisaniach kontekstu po przerwie
i workflow wieloagentowych.

Źródło: zapisy rozmów Claude Code na tej maszynie — `~/.claude/projects/<katalog projektu>/*.jsonl`
(główne sesje) i podkatalogi `<sesja>/subagents/` (subagenci) oraz `<sesja>/subagents/workflows/<id>/`
(workflow). Niczego nie zapisuje. Inne maszyny (Windows, Cowork) mają własne zapisy — tu ich nie ma.

Zasady liczenia:
- jedna odpowiedź modelu bywa zapisana w kilku rekordach (bloki treści, zapis przed końcem strumienia)
  z tym samym `message.id` — scalamy je, biorąc NAJWIĘKSZĄ wartość każdego licznika (pierwszy rekord
  potrafi mieć wyjście 1 zamiast pełnego);
- koszt ważony w „jednostkach wejścia” = proporcje cennika modeli Claude: wejście 1, zapis cache 5 min
  1,25, zapis cache 1 h 2, odczyt cache 0,1, wyjście 5. To stosunek, nie złotówki — służy do porównań;
- kontekst wywołania = wejście + zapis + odczyt cache (tyle model „przeczytał” w tym wywołaniu);
- przepisanie kontekstu = wywołanie z zapisem ≥ 200 tys. przy odczycie < 50 tys. (cache wygasł po
  przerwie > 1 h albo po streszczeniu rozmowy) — cały kontekst zapisany od nowa po podwójnej cenie.

    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py                 # cały zapis tego projektu
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --od 2026-09-27 # od dnia (UTC)
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --json          # dane do dalszej obróbki
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --stan runs/tokeny/stan.json  # dane strony „Tokeny CLAS-5”
    PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py --progi         # symulacja progów strażnika kontekstu

Strona „Tokeny CLAS-5” (docs/rag/12) czyta dokument bazy zbudowany przez `--stan`: wiersz na dzień
z podziałem na modele i źródła, kontekstem i przepisaniami głównej sesji oraz liczbą sesji. Plik stanu
jest zarazem historią: Claude Code kasuje zapisy rozmów po 30 dniach (`cleanupPeriodDays`), więc dni
starsze niż FREEZE_DAYS zostają w pliku takie, jak policzono je ostatnio, zamiast znikać z wykresów.

Symulacja progów (`--progi`) sprawdza na danych progi strażnika kontekstu (`tools/straznik_kontekstu.py`):
co by było, gdyby główną sesję czyścić (/clear + nota przekazania) zawsze, gdy jej kontekst przekroczy
próg X. Nowa sesja zaczyna z kontekstem R i jednorazowym kosztem K — oba zmierzone na początkach
prawdziwych sesji (mediana). To przybliżenie: zakłada, że po czyszczeniu praca biegnie tak samo, tylko
na krótszym kontekście.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import statistics
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WEIGHTS = {"inp": 1.0, "cw5": 1.25, "cw1h": 2.0, "cr": 0.1, "out": 5.0}
REWRITE_MIN_WRITE = 200_000
REWRITE_MAX_READ = 50_000
MAIN = "główna sesja"
SUB = "subagent"
SKILL_MARK = "Base directory for this skill"
SYNTHETIC = "<synthetic>"  # wpisy harnessu bez wywołania modelu (zero tokenów) — poza stroną
GROUP_KEY = {
    MAIN: "main",
    SUB: "sub",
    "workflow": "wf",
}  # krótkie klucze źródeł w dokumencie strony
MODEL_COLS = ["koszt", "wywolan", "wejscie", "zapis_cache", "odczyt_cache", "wyjscie"]
FREEZE_DAYS = 14  # dni starszych nie przeliczamy — część ich zapisów mogła już zniknąć (30 dni)
DOC_LIMIT = 240_000  # bajtów; dokument bazy strony ma limit 256 KiB — nadmiar = najstarsze dni
# Symulacja progów (--progi). 150 i 250 tys. to PROG_UWAGI i PROG_PRZEKAZANIA z tools/straznik_kontekstu.py
# — bez importu, bo ten moduł ma działać sam (zgodność wartości pilnuje test).
PROGI_SYMULACJI = (150_000, 200_000, 250_000, 300_000, 400_000)
MNOZNIKI_K = (0.5, 1.0, 2.0)  # koszt startu nowej sesji jest niepewny: połowa, tyle samo, dwa razy
MIN_WYWOLAN_SESJI = 12  # krótsza sesja nie ma czego czyścić ani początku do zmierzenia
N_NOWEJ_SESJI = 10  # w tylu wywołaniach nowa sesja wczytuje to, czego potrzebuje do pracy
SPADEK_STRESZCZENIA = 20_000  # większy spadek kontekstu = streszczenie rozmowy albo nowy początek
PROG_SZCZEGOLOW = 250_000  # dla tego progu raport podaje liczby per sesja (w --json)


def project_dir(cwd: str | Path, home: Path | None = None) -> Path:
    """Katalog zapisów Claude Code dla projektu: znaki spoza [A-Za-z0-9] w ścieżce → „-”."""
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(cwd).resolve()))
    return (home or Path.home()) / ".claude" / "projects" / slug


def source_of(path: Path, root: Path) -> str:
    """Główna sesja / subagent / workflow:<id> — z położenia pliku względem katalogu projektu."""
    parts = path.relative_to(root).parts
    if "workflows" in parts:
        i = parts.index("workflows")
        return "workflow:" + (parts[i + 1] if i + 1 < len(parts) - 1 else "?")
    if "subagents" in parts:
        return SUB
    return MAIN


def _usage_counts(u: dict) -> collections.Counter:
    cc = u.get("cache_creation") or {}
    c = collections.Counter(
        inp=int(u.get("input_tokens") or 0),
        cw5=int(cc.get("ephemeral_5m_input_tokens") or 0),
        cw1h=int(cc.get("ephemeral_1h_input_tokens") or 0),
        cr=int(u.get("cache_read_input_tokens") or 0),
        out=int(u.get("output_tokens") or 0),
    )
    if not cc:  # starszy zapis bez podziału na TTL — traktujemy jak 5 min
        c["cw5"] = int(u.get("cache_creation_input_tokens") or 0)
    return c


def cost(c: collections.Counter) -> float:
    return sum(c[k] * w for k, w in WEIGHTS.items())


def context_size(c: collections.Counter) -> int:
    return c["inp"] + c["cw5"] + c["cw1h"] + c["cr"]


@dataclass
class Call:
    day: str
    source: str
    ts: str
    counts: collections.Counter
    model: str = "?"
    session: str = ""

    @property
    def is_rewrite(self) -> bool:
        write = self.counts["cw5"] + self.counts["cw1h"]
        return write >= REWRITE_MIN_WRITE and self.counts["cr"] < REWRITE_MAX_READ


@dataclass
class Scan:
    calls: list[Call] = field(default_factory=list)
    skills: collections.Counter = field(default_factory=collections.Counter)
    content: collections.Counter = field(default_factory=collections.Counter)
    bad_lines: int = 0
    files: int = 0


def _len(x) -> int:
    return len(x) if isinstance(x, str) else len(json.dumps(x, ensure_ascii=False))


def scan_file(path: Path, source: str, scan: Scan, since: str = "") -> None:
    """Wywołania modelu z jednego pliku (scalone po message.id) + dla głównej sesji: skille i treść."""
    merged: dict[str, Call] = {}
    tool_names: dict[str, str] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                scan.bad_lines += 1
                continue
            if not isinstance(o, dict):
                scan.bad_lines += 1
                continue
            day = str(o.get("timestamp") or "")[:10]
            if since and day and day < since:
                continue
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = msg.get("content")
            if o.get("type") == "assistant":
                u = msg.get("usage")
                if isinstance(u, dict):
                    key = str(msg.get("id") or o.get("requestId") or o.get("uuid"))
                    c = _usage_counts(u)
                    prev = merged.get(key)
                    if prev is None:
                        merged[key] = Call(
                            day,
                            source,
                            str(o.get("timestamp") or ""),
                            c,
                            str(msg.get("model") or "?"),
                            path.stem,
                        )
                    else:
                        prev.counts = collections.Counter(
                            {k: max(prev.counts[k], c[k]) for k in set(prev.counts) | set(c)}
                        )
                if source == MAIN and isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_use":
                            tool_names[str(b.get("id"))] = str(b.get("name"))
                            scan.content["asystent: argumenty narzędzi"] += _len(b.get("input"))
                            if b.get("name") == "Skill" and isinstance(b.get("input"), dict):
                                scan.skills[str(b["input"].get("skill"))] += 1
                        elif b.get("type") == "text":
                            scan.content["asystent: tekst"] += _len(b.get("text", ""))
            elif o.get("type") == "user" and source == MAIN:
                blocks = [content] if isinstance(content, str) else content or []
                for b in blocks:
                    if isinstance(b, str):
                        key = "skille" if SKILL_MARK in b else "wiadomości użytkownika/systemu"
                        scan.content[key] += len(b)
                    elif isinstance(b, dict) and b.get("type") == "tool_result":
                        name = tool_names.get(str(b.get("tool_use_id")), "?")
                        name = name if name in ("Bash", "Read") else "inne narzędzia"
                        cc = b.get("content")
                        n = (
                            sum(_len(x.get("text", "")) for x in cc if isinstance(x, dict))
                            if isinstance(cc, list)
                            else _len(cc)
                        )
                        scan.content["wyniki: " + name] += n
                    elif isinstance(b, dict) and b.get("type") == "text":
                        t = b.get("text", "")
                        key = "skille" if SKILL_MARK in t else "wiadomości użytkownika/systemu"
                        scan.content[key] += len(t)
            elif o.get("type") == "attachment" and source == MAIN:
                a = o.get("attachment")
                kind = a.get("type") if isinstance(a, dict) else None
                if kind == "invoked_skills":
                    scan.content["skille"] += _len(a)
                elif kind != "prompt_snapshot":  # zapis diagnostyczny harnessu, nie nowa treść
                    scan.content["przypomnienia i załączniki"] += _len(a)
    scan.calls.extend(merged.values())
    scan.files += 1


def scan_project(root: Path, since: str = "") -> Scan:
    scan = Scan()
    if not root.is_dir():
        return scan
    for path in sorted(root.rglob("*.jsonl")):
        if "memory" in path.relative_to(root).parts:
            continue
        scan_file(path, source_of(path, root), scan, since)
    return scan


def summarize(scan: Scan) -> dict:
    """Liczby do raportu: dzień × grupa źródeł, źródła, konteksty, przepisania, skille, treść."""
    by_day: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    by_src: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_model: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    ctx: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
    rewrites = []
    for call in scan.calls:
        group = "workflow" if call.source.startswith("workflow:") else call.source
        c = collections.Counter(call.counts)
        c["calls"] = 1
        c["koszt"] = cost(call.counts)
        by_day[(call.day, group)] += c
        by_src[call.source] += c
        by_model[call.model] += c
        ctx[(call.day, group)].append(context_size(call.counts))
        if call.source == MAIN and call.is_rewrite:
            rewrites.append(
                {
                    "ts": call.ts,
                    "zapis": call.counts["cw5"] + call.counts["cw1h"],
                    "koszt": cost(call.counts),
                }
            )
    total = sum((cost(c.counts) for c in scan.calls), 0.0)
    return {
        "razem_koszt": total,
        "razem_wywolan": len(scan.calls),
        "dni": [
            {
                "dzien": d,
                "zrodlo": g,
                "wywolan": c["calls"],
                "wejscie": c["inp"],
                "zapis_cache": c["cw5"] + c["cw1h"],
                "odczyt_cache": c["cr"],
                "wyjscie": c["out"],
                "koszt": c["koszt"],
                "kontekst_mediana": int(statistics.median(ctx[(d, g)])),
                "kontekst_max": max(ctx[(d, g)]),
            }
            for (d, g), c in sorted(by_day.items())
        ],
        "zrodla": sorted(
            ({"zrodlo": s, "wywolan": c["calls"], "koszt": c["koszt"]} for s, c in by_src.items()),
            key=lambda r: -r["koszt"],
        ),
        "przepisania": sorted(rewrites, key=lambda r: r["ts"]),
        "skille": dict(scan.skills.most_common()),
        "tresc_glownej_sesji_znaki": dict(scan.content.most_common()),
        "modele": sorted(
            (
                {
                    "model": m,
                    "wywolan": c["calls"],
                    "zapis_cache": c["cw5"] + c["cw1h"],
                    "odczyt_cache": c["cr"],
                    "wyjscie": c["out"],
                    "koszt": c["koszt"],
                }
                for m, c in by_model.items()
            ),
            key=lambda r: -r["koszt"],
        ),
        "zle_linie": scan.bad_lines,
        "pliki": scan.files,
    }


def day_rows(scan: Scan) -> dict[str, dict]:
    """Wiersz na dzień dla strony: modele [MODEL_COLS], źródła [koszt, wywołań], kontekst głównej
    sesji [mediana, maks.], przepisania [liczba, koszt] i liczba głównych sesji z wywołaniem tego dnia.
    """
    rows: dict[str, dict] = {}
    ctx: dict[str, list[int]] = collections.defaultdict(list)
    sessions: dict[str, set[str]] = collections.defaultdict(set)
    for call in scan.calls:
        if not call.day or call.model == SYNTHETIC:
            continue
        r = rows.setdefault(
            call.day, {"d": call.day, "m": {}, "z": {}, "ctx": [0, 0], "prz": [0, 0], "ses": 0}
        )
        c, k = call.counts, cost(call.counts)
        m = r["m"].setdefault(call.model, [0.0] + [0] * (len(MODEL_COLS) - 1))
        for i, v in enumerate((k, 1, c["inp"], c["cw5"] + c["cw1h"], c["cr"], c["out"])):
            m[i] += v
        group = "workflow" if call.source.startswith("workflow:") else call.source
        z = r["z"].setdefault(GROUP_KEY[group], [0.0, 0])
        z[0] += k
        z[1] += 1
        if call.source == MAIN:
            ctx[call.day].append(context_size(c))
            sessions[call.day].add(call.session)
            if call.is_rewrite:
                r["prz"][0] += 1
                r["prz"][1] += k
    for d, r in rows.items():
        for v in (*r["m"].values(), *r["z"].values(), r["prz"]):
            v[0] = round(v[0]) if isinstance(v[0], float) else v[0]
        r["prz"][1] = round(r["prz"][1])
        if ctx[d]:
            r["ctx"] = [int(statistics.median(ctx[d])), max(ctx[d])]
        r["ses"] = len(sessions[d])
    return rows


def merge_days(old: list[dict], new: dict[str, dict], today: str) -> list[dict]:
    """Historia + świeże przeliczenie: dzień z ostatnich FREEZE_DAYS (albo nieznany historii) bierze
    wartość świeżą, starszy zostaje z historii — jego zapisy mogły już zostać skasowane."""
    cutoff = (date.fromisoformat(today) - timedelta(days=FREEZE_DAYS)).isoformat()
    out = {r["d"]: r for r in old}
    for d, r in new.items():
        if d >= cutoff or d not in out:
            out[d] = r
    return [out[d] for d in sorted(out)]


def write_state(
    path: Path, scan: Scan, now: datetime | None = None, limit: int = DOC_LIMIT
) -> dict:
    """Dokument strony „Tokeny CLAS-5”: scala plik `path` (historia) ze świeżym skanem, przycina
    najstarsze dni do `limit` bajtów i zapisuje atomowo. Uszkodzony plik historii = błąd, nie reset.
    """
    now = now or datetime.now(timezone.utc)
    old = json.loads(path.read_text(encoding="utf-8"))["dni"] if path.exists() else []
    state = {
        "wersja": 1,
        "wygenerowano": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zrodlo": "zapisy Claude Code projektu alpha na serwerze Linux (bez Windows i Cowork)",
        "kolumny_modelu": MODEL_COLS,
        "kolumny_zrodla": ["koszt", "wywolan"],
        "dni": merge_days(old, day_rows(scan), now.date().isoformat()),
    }
    while len(state["dni"]) > 1 and len(json.dumps(state, ensure_ascii=False).encode()) > limit:
        state["dni"].pop(0)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)
    return state


def report(s: dict) -> str:
    """Raport tekstowy (koszt w milionach jednostek wejścia, patrz docstring)."""
    tot = s["razem_koszt"] or 1.0
    out = [
        f"ZUŻYCIE TOKENÓW — plików {s['pliki']}, wywołań modelu {s['razem_wywolan']}, "
        f"koszt ważony {s['razem_koszt'] / 1e6:.1f} M jednostek wejścia (złe linie {s['zle_linie']})",
        "",
        f"{'dzień':10} {'źródło':13} {'wywołań':>7} {'zapis cache':>12} {'odczyt cache':>13} "
        f"{'wyjście':>9} {'koszt M':>8} {'kontekst med./max (tys.)':>25}",
    ]
    for r in s["dni"]:
        out.append(
            f"{r['dzien']:10} {r['zrodlo']:13} {r['wywolan']:7d} {r['zapis_cache']:12,d} "
            f"{r['odczyt_cache']:13,d} {r['wyjscie']:9,d} {r['koszt'] / 1e6:8.2f} "
            f"{r['kontekst_mediana'] / 1e3:14.0f} / {r['kontekst_max'] / 1e3:5.0f}"
        )
    out += ["", "Źródła (od największego kosztu):"]
    for r in s["zrodla"]:
        out.append(
            f"  {r['zrodlo']:32} {r['koszt'] / 1e6:8.2f} M ({100 * r['koszt'] / tot:4.1f} %), "
            f"wywołań {r['wywolan']}"
        )
    out += [
        "",
        "Modele (jednostki liczone tak samo dla każdego modelu — cena za token RÓŻNI się: Haiku "
        "i Sonnet są wielokrotnie tańsze od Opusa i Fable, więc ich realny udział jest mniejszy):",
    ]
    for r in s["modele"]:
        out.append(
            f"  {r['model']:32} {r['koszt'] / 1e6:8.2f} M ({100 * r['koszt'] / tot:4.1f} %), "
            f"wywołań {r['wywolan']}"
        )
    rw = s["przepisania"]
    rw_cost = sum(r["koszt"] for r in rw)
    out += [
        "",
        f"Przepisania całego kontekstu głównej sesji (cache wygasł po przerwie > 1 h lub po "
        f"streszczeniu): {len(rw)}, koszt {rw_cost / 1e6:.2f} M ({100 * rw_cost / tot:.1f} %)",
    ]
    for r in rw[-10:]:
        out.append(
            f"  {r['ts'][:16]}  zapis {r['zapis'] / 1e3:5.0f} tys.  koszt {r['koszt'] / 1e6:.2f} M"
        )
    out += ["", "Wczytania skilli w głównej sesji (każde dokłada pełną treść skilla do kontekstu):"]
    out.append(
        "  " + ", ".join(f"{k} ×{v}" for k, v in s["skille"].items()) if s["skille"] else "  brak"
    )
    ct = s["tresc_glownej_sesji_znaki"]
    ctot = sum(ct.values()) or 1
    out += [
        "",
        "Treść dodana do kontekstu głównej sesji (znaki; bez rozumowania modelu, które nie trafia do zapisu):",
    ]
    for k, v in ct.items():
        out.append(f"  {k:40} {v:12,d}  {100 * v / ctot:5.1f} %")
    return "\n".join(out)


def sesje_glowne(scan: Scan, min_wywolan: int = MIN_WYWOLAN_SESJI) -> list[list[Call]]:
    """Wywołania głównej sesji (bez wpisów <synthetic>) pogrupowane po sesji, każda posortowana po
    czasie. Zostają sesje z co najmniej `min_wywolan` wywołaniami, od najwcześniej zaczętej."""
    by_session: dict[str, list[Call]] = collections.defaultdict(list)
    for call in scan.calls:
        if call.source == MAIN and call.model != SYNTHETIC:
            by_session[call.session].append(call)
    sesje = [sorted(cs, key=lambda c: c.ts) for cs in by_session.values() if len(cs) >= min_wywolan]
    return sorted(sesje, key=lambda cs: (cs[0].ts, cs[0].session))


def parametry_nowej_sesji(sesje: list[list[Call]], n: int = N_NOWEJ_SESJI) -> dict:
    """Start od nowa zmierzony na początkach prawdziwych sesji (mediana, żeby jedna nietypowa sesja
    nie przesuwała wyniku; obok zakres):
    - R = kontekst n-tego wywołania: tyle czyta nowa sesja, gdy już wczytała, czego potrzebuje;
    - K = koszt ważony n pierwszych wywołań: jednorazowy koszt startu od nowa.
    Sesje krótsze niż n wywołań są pomijane; gdy nie zostaje żadna — ValueError."""
    if n < 1:
        raise ValueError(f"n = {n}: liczba wywołań startu musi być co najmniej 1")
    ok = [cs for cs in sesje if len(cs) >= n]
    if not ok:
        raise ValueError(f"brak głównych sesji z co najmniej {n} wywołaniami")
    rs = [context_size(cs[n - 1].counts) for cs in ok]
    ks = [sum(cost(c.counts) for c in cs[:n]) for cs in ok]
    return {
        "n": n,
        "sesji": len(ok),
        "R": statistics.median(rs),
        "R_min": min(rs),
        "R_max": max(rs),
        "K": statistics.median(ks),
        "K_min": min(ks),
        "K_max": max(ks),
    }


def symuluj_prog(calls: list[Call], X: float, R: float, K: float) -> tuple[int, float]:
    """Jedna sesja „na niby”: gdy kontekst przekracza próg X, czyścimy ją (/clear + nota
    przekazania) — nowa sesja ma kontekst R i kosztuje jednorazowo K. Wynik: (liczba czyszczeń,
    oszczędność w jednostkach wejścia; ujemna = czyszczenia się nie zwróciły).

    `shift` = tokeny usunięte z początku kontekstu przez ostatnie czyszczenie; każde następne
    wywołanie czyta o tyle mniej. Ta część byłaby odczytem cache (waga odczytu), a to, co z niej
    wykracza poza odczyt — zapisem cache po wadze zapisu tego wywołania (np. po przerwie > 1 h).
    Spadek prawdziwego kontekstu o więcej niż SPADEK_STRESZCZENIA (streszczenie rozmowy, nowy
    początek) zeruje `shift`. Koszt K odejmujemy raz na końcu (czyszczenia × K): wynik jest
    dokładnie liniowy w K, a liczba czyszczeń od K nie zależy. Próg X ≤ R — ValueError (nowa sesja
    zaczynałaby już nad progiem)."""
    if X <= R:
        raise ValueError(
            f"próg X = {X / 1e3:g} tys. nie jest większy od kontekstu nowej sesji "
            f"R = {R / 1e3:g} tys."
        )
    shift, clears, saved, prev = 0.0, 0, 0.0, None
    for call in calls:
        c = call.counts
        ctx = context_size(c)
        if prev is not None and ctx < prev - SPADEK_STRESZCZENIA:
            shift = 0.0  # prawdziwe streszczenie: wcześniejsze czyszczenie przestaje działać
        prev = ctx
        if ctx - shift > X:
            shift = ctx - R
            clears += 1
        if shift > 0:
            cr, cw = c["cr"], c["cw5"] + c["cw1h"]
            w = WEIGHTS["cw1h"] if c["cw1h"] else WEIGHTS["cw5"]
            saved += WEIGHTS["cr"] * min(shift, cr) + w * max(0, min(shift - cr, cw))
    return clears, saved - clears * K


def _po_przekroczeniu(calls: list[Call], X: float) -> int | None:
    """Ile wywołań zostało w sesji PO pierwszym wywołaniu z kontekstem > X; None = nie przekroczyła."""
    for i, call in enumerate(calls):
        if context_size(call.counts) > X:
            return len(calls) - i - 1
    return None


def raport_progow(
    scan: Scan,
    progi: tuple[int, ...] = PROGI_SYMULACJI,
    mnozniki: tuple[float, ...] = MNOZNIKI_K,
) -> dict:
    """Symulacja progów strażnika kontekstu na prawdziwych sesjach głównych: parametry nowej sesji
    (R, K z zakresami), tabela próg × mnożnik K (czyszczenia, oszczędność, % kosztu tych sesji),
    ta sama tabela bez najdroższej sesji (R i K bez zmian), zwrot z jednego czyszczenia i liczby per
    sesja dla PROG_SZCZEGOLOW (K×1). Próg nie większy od R jest pomijany i trafia do
    „progi_pominiete”. Bez sesji do zmierzenia — ValueError."""
    sesje = sesje_glowne(scan)
    if not sesje:
        raise ValueError(f"brak głównych sesji z co najmniej {MIN_WYWOLAN_SESJI} wywołaniami")
    par = parametry_nowej_sesji(sesje)
    R, K = par["R"], par["K"]
    koszty = [sum(cost(c.counts) for c in cs) for cs in sesje]
    top = max(range(len(sesje)), key=koszty.__getitem__)
    reszta = [i for i in range(len(sesje)) if i != top]
    dobre = [X for X in progi if X > R]

    def tabela(idx: list[int]) -> list[dict]:
        koszt = sum(koszty[i] for i in idx)
        wiersze = []
        for X in dobre:
            for m in mnozniki:
                wyniki = [symuluj_prog(sesje[i], X, R, K * m) for i in idx]
                saved = sum(s for _, s in wyniki)
                wiersze.append(
                    {
                        "prog": X,
                        "mnoznik_K": m,
                        "czyszczen": sum(c for c, _ in wyniki),
                        "oszczednosc": saved,
                        "oszczednosc_pct": 100 * saved / koszt if koszt else 0.0,
                    }
                )
        return wiersze

    zwrot = []
    for X in dobre:
        po = [n for n in (_po_przekroczeniu(cs, X) for cs in sesje) if n is not None]
        zwrot.append(
            {
                "prog": X,
                "n_zwrotu": K / (WEIGHTS["cr"] * (X - R)),
                "sesji_ponad_progiem": len(po),
                "mediana_wywolan_po_przekroczeniu": statistics.median(po) if po else None,
            }
        )
    szczegoly = None
    if PROG_SZCZEGOLOW > R:
        szczegoly = {"prog": PROG_SZCZEGOLOW, "mnoznik_K": 1.0, "sesje": []}
        for cs, koszt in zip(sesje, koszty, strict=True):
            clears, saved = symuluj_prog(cs, PROG_SZCZEGOLOW, R, K)
            szczegoly["sesje"].append(
                {
                    "sesja": cs[0].session,
                    "start": cs[0].ts,
                    "wywolan": len(cs),
                    "koszt": koszt,
                    "kontekst_max": max(context_size(c.counts) for c in cs),
                    "czyszczen": clears,
                    "oszczednosc": saved,
                    "wywolan_po_przekroczeniu": _po_przekroczeniu(cs, PROG_SZCZEGOLOW),
                }
            )
    naj = sesje[top]
    return {
        "sesji": len(sesje),
        "min_wywolan": MIN_WYWOLAN_SESJI,
        "koszt_sesji": sum(koszty),
        "parametry": par,
        "progi_pominiete": [X for X in progi if X <= R],
        "tabela": tabela(list(range(len(sesje)))),
        "najdrozsza_sesja": {
            "sesja": naj[0].session,
            "start": naj[0].ts,
            "wywolan": len(naj),
            "koszt": koszty[top],
        },
        "tabela_bez_najdrozszej": tabela(reszta) if reszta else [],
        "koszt_bez_najdrozszej": sum(koszty[i] for i in reszta),
        "zwrot": zwrot,
        "sesje_przy_progu": szczegoly,
    }


def _pl(x: float) -> str:
    """Liczba w tekście po polsku: przecinek dziesiętny, bez zbędnych zer (0,1; 2)."""
    return f"{x:g}".replace(".", ",")


def _tabela_progow(wiersze: list[dict]) -> list[str]:
    """Wiersz na próg: liczba czyszczeń raz (nie zależy od K), potem oszczędność dla każdego K."""
    if not wiersze:
        return ["  brak progów do symulacji"]
    grupy: dict[float, list[dict]] = {}
    for w in wiersze:
        grupy.setdefault(w["prog"], []).append(w)
    etykiety = ["K×" + _pl(w["mnoznik_K"]) for w in next(iter(grupy.values()))]
    out = [f"  {'próg X':>10}  {'czyszczeń':>10}" + "".join(f"{e:>22}" for e in etykiety)]
    for prog, ws in grupy.items():
        cz = "/".join(str(c) for c in sorted({w["czyszczen"] for w in ws}))
        out.append(
            f"  {prog / 1e3:5.0f} tys.  {cz:>10}"
            + "".join(
                f"{w['oszczednosc'] / 1e6:+10.2f} M ({w['oszczednosc_pct']:+5.1f} %)" for w in ws
            )
        )
    return out


def raport_progow_tekst(r: dict) -> str:
    """Raport tekstowy symulacji progów (koszt w milionach jednostek wejścia, M)."""
    p, naj = r["parametry"], r["najdrozsza_sesja"]
    wr = _pl(WEIGHTS["cr"])
    out = [
        "SYMULACJA PROGÓW STRAŻNIKA KONTEKSTU",
        "Co by było, gdyby główną sesję czyścić (/clear + nota przekazania) zawsze, gdy jej kontekst",
        "(tokeny czytane w jednym wywołaniu) przekroczy próg X. Koszt w milionach jednostek wejścia (M).",
        "",
        f"Dane: {r['sesji']} głównych sesji z co najmniej {r['min_wywolan']} wywołaniami, koszt "
        f"rzeczywisty {r['koszt_sesji'] / 1e6:.2f} M.",
        "Nowa sesja po czyszczeniu (mediana z początków tych sesji, w nawiasie zakres):",
        f"  R = {p['R'] / 1e3:.0f} tys. tokenów ({p['R_min'] / 1e3:.0f}–{p['R_max'] / 1e3:.0f} "
        f"tys.) — kontekst po {p['n']}. wywołaniu: tyle czyta nowa sesja,",
        "      gdy już wczytała, czego potrzebuje;",
        f"  K = {p['K'] / 1e6:.2f} M ({p['K_min'] / 1e6:.2f}–{p['K_max'] / 1e6:.2f} M) — koszt "
        f"{p['n']} pierwszych wywołań: jednorazowy koszt startu od nowa.",
        "",
        "Oszczędność = tańsze wywołania po czyszczeniu (krótszy kontekst) minus K za każde czyszczenie.",
        "Wynik ujemny = czyszczenie się nie opłaca. K×0,5 i K×2 sprawdzają, czy wniosek przetrwa, gdy",
        "start nowej sesji kosztuje połowę albo dwa razy tyle. Spadek prawdziwego kontekstu o ponad "
        f"{SPADEK_STRESZCZENIA / 1e3:.0f} tys.",
        "(streszczenie rozmowy) kończy działanie wcześniejszego czyszczenia.",
    ]
    if r["progi_pominiete"]:
        out.append(
            "Pominięte progi (nie wyższe od R — nowa sesja zaczynałaby już nad nimi): "
            + ", ".join(f"{x / 1e3:.0f} tys." for x in r["progi_pominiete"])
        )
    out += ["", f"Wszystkie sesje ({r['sesji']}, koszt {r['koszt_sesji'] / 1e6:.2f} M):"]
    out += _tabela_progow(r["tabela"])
    udzial = 100 * naj["koszt"] / (r["koszt_sesji"] or 1)
    out += [
        "",
        f"Bez najdroższej sesji {naj['sesja'][:8]} (start {naj['start'][:10]}, {naj['wywolan']} "
        f"wywołań, {naj['koszt'] / 1e6:.2f} M = {udzial:.1f} % kosztu),",
        f"żeby jedna olbrzymia sesja nie przesądzała wniosku ({r['sesji'] - 1} sesji, koszt "
        f"{r['koszt_bez_najdrozszej'] / 1e6:.2f} M; R i K bez zmian):",
    ]
    out += (
        _tabela_progow(r["tabela_bez_najdrozszej"])
        if r["tabela_bez_najdrozszej"]
        else ["  tylko jedna sesja — nie ma czego porównać"]
    )
    out += [
        "",
        "Zwrot z jednego czyszczenia. Po czyszczeniu przy progu X każde następne wywołanie czyta",
        f"co najmniej X − R tokenów mniej z cache (waga {wr}). Czyszczenie zwraca się więc po około",
        f"n* = K / ({wr} · (X − R)) wywołaniach. Obok: ile wywołań naprawdę zostało w sesjach po",
        "pierwszym przekroczeniu progu (mediana). Więcej pozostałych wywołań niż n* = czyszczenie",
        "zwykle by się zwróciło.",
        f"  {'próg X':>10}  {'n*':>8}  {'sesji ponad progiem':>20}  "
        f"{'mediana wywołań po przekroczeniu':>33}",
    ]
    for z in r["zwrot"]:
        med = z["mediana_wywolan_po_przekroczeniu"]
        ponad = f"{z['sesji_ponad_progiem']} z {r['sesji']}"
        out.append(
            f"  {z['prog'] / 1e3:5.0f} tys.  {z['n_zwrotu']:8.1f}  {ponad:>20}  "
            f"{'—' if med is None else f'{med:g}':>33}"
        )
    if r["sesje_przy_progu"]:
        out += [
            "",
            f"Liczby per sesja dla progu {PROG_SZCZEGOLOW / 1e3:.0f} tys. (K×1): --progi --json, "
            "klucz „sesje_przy_progu”.",
        ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--katalog", type=Path, help="katalog zapisów (domyślnie: projekt z bieżącego katalogu)"
    )
    ap.add_argument("--od", default="", help="od dnia UTC, RRRR-MM-DD")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    tryb = ap.add_mutually_exclusive_group()
    tryb.add_argument(
        "--stan", type=Path, help="zapisz dokument strony „Tokeny CLAS-5” (i historię)"
    )
    tryb.add_argument(
        "--progi",
        action="store_true",
        help="symulacja progów strażnika kontekstu: co by było, gdyby czyścić sesję po "
        "przekroczeniu progu",
    )
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.od and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.od):
        print("BŁĄD: --od w formacie RRRR-MM-DD", file=sys.stderr)
        return 2
    root = a.katalog or project_dir(Path.cwd())
    if not root.is_dir():
        print(f"BŁĄD: brak katalogu zapisów {root}", file=sys.stderr)
        return 1
    if a.stan:
        try:
            st = write_state(a.stan, scan_project(root, a.od))
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"BŁĄD: plik stanu {a.stan}: {e}", file=sys.stderr)
            return 1
        dni = st["dni"]
        print(
            f"stan strony: dni {len(dni)} ({dni[0]['d'] if dni else '-'} → "
            f"{dni[-1]['d'] if dni else '-'}), {a.stan.stat().st_size / 1e3:.0f} KB → {a.stan}"
        )
        return 0
    if a.progi:
        try:
            r = raport_progow(scan_project(root, a.od))
        except ValueError as e:
            print(f"BŁĄD: symulacja progów: {e}", file=sys.stderr)
            return 1
        print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else raport_progow_tekst(r))
        return 0
    s = summarize(scan_project(root, a.od))
    print(json.dumps(s, ensure_ascii=False, indent=1) if a.json else report(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
