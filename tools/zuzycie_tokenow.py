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
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

WEIGHTS = {"inp": 1.0, "cw5": 1.25, "cw1h": 2.0, "cr": 0.1, "out": 5.0}
REWRITE_MIN_WRITE = 200_000
REWRITE_MAX_READ = 50_000
MAIN = "główna sesja"
SUB = "subagent"
SKILL_MARK = "Base directory for this skill"


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--katalog", type=Path, help="katalog zapisów (domyślnie: projekt z bieżącego katalogu)"
    )
    ap.add_argument("--od", default="", help="od dnia UTC, RRRR-MM-DD")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.od and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.od):
        print("BŁĄD: --od w formacie RRRR-MM-DD", file=sys.stderr)
        return 2
    root = a.katalog or project_dir(Path.cwd())
    if not root.is_dir():
        print(f"BŁĄD: brak katalogu zapisów {root}", file=sys.stderr)
        return 1
    s = summarize(scan_project(root, a.od))
    print(json.dumps(s, ensure_ascii=False, indent=1) if a.json else report(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
