"""Statyczne domkniecie importow: ktore skrypty (bezposrednio lub przez importy) czytaja katalogi
z nazwami w cp866 (universe_full, universe_2026q3, live) i czy lacza je z danymi o poprawnych nazwach.
"""

import ast
import os
import re
import sys

ROOT = sys.argv[1]
PKGS = ("backtest", "data", "tools", "agents", "agent_5_compliance", "dziennik")
AFFECTED = {
    "universe_full": re.compile(r"universe_full"),
    "universe_2026q3": re.compile(r"universe_2026q3"),
    "live": re.compile(r"data/raw/live|LIVE_DIR|symbol_files\(|load_live\("),
}
JOINED = {
    "universe_ohlc_full": re.compile(r"universe_ohlc_full"),
    "mark_1d": re.compile(r"mark_1d"),
    "oi_panel": re.compile(r"oi_daily"),
    "listings": re.compile(r"raw/listings"),
}

mods = {}
for pkg in PKGS:
    base = os.path.join(ROOT, pkg)
    if not os.path.isdir(base):
        continue
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if fn.endswith(".py"):
                p = os.path.join(dp, fn)
                name = os.path.relpath(p, ROOT)[:-3].replace(os.sep, ".")
                mods[name] = p

src = {m: open(p, encoding="utf-8").read() for m, p in mods.items()}


def imports(m):
    out = set()
    try:
        tree = ast.parse(src[m])
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in mods:
                    out.add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module in mods:
                out.add(node.module)
            for a in node.names:
                cand = f"{node.module}.{a.name}"
                if cand in mods:
                    out.add(cand)
    return out


deps = {m: imports(m) for m in mods}


def closure(m):
    seen, stack = set(), [m]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(deps.get(x, ()))
    return seen


frozen = set()
with open(os.path.join(ROOT, "runs", "ZAMROZONE.txt"), encoding="utf-8") as fh:
    for line in fh:
        line = line.split("#")[0].strip()
        if line.endswith(".py"):
            frozen.add(line[:-3].replace("/", "."))

rows = []
for m in sorted(mods):
    if not (
        m.startswith("backtest.run_")
        or m.startswith("data.")
        or m.startswith("tools.")
        or m in ("backtest.odczyt_dziennika_stale", "backtest.live_journal")
    ):
        continue
    cl = closure(m)
    direct = {k for k, rx in AFFECTED.items() if rx.search(src[m])}
    via = {k for k, rx in AFFECTED.items() for d in cl - {m} if rx.search(src[d])}
    if not direct and not via:
        continue
    joined = {k for k, rx in JOINED.items() for d in cl if rx.search(src[d])}
    rows.append(
        (
            m,
            "Z" if m in frozen else "-",
            sorted(direct) + [f"przez:{v}" for v in sorted(via - direct)],
            sorted(joined),
        )
    )

for m, fz, d, j in rows:
    print(f"{fz} {m:45s} katalogi={d} laczy_z={j}")
