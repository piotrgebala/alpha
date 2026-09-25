"""
au3_audit.py — runda AU3: które zamrożone rundy dotknął błąd kanonicznego N_eff (mianownik 1 + 2Σρ ≤ 0)?

    py tools/au3_audit.py plan                       # komendy rund, które liczą N_eff (bezpośrednio/importem)
    py tools/au3_audit.py exec <worktree> <out_dir>  # tryb „old” wszędzie, „new” tylko tam, gdzie licznik > 0
    py tools/au3_audit.py run <old|new> <moduł> [argumenty…]   # (wewnętrzne) jeden skrypt z licznikiem

Tryb `old` podmienia `agents.labeling.effective_sample_size` na wzór sprzed AU3 i liczy wywołania
z mianownikiem ≤ 0; tryb `new` używa wzoru z repo (po naprawie) i liczy to samo. Podmiana następuje
PRZED importem skryptu, więc wszystkie `from agents.labeling import effective_sample_size` widzą ją.
Skrypty uruchamiane w osobnej kopii roboczej (`git worktree`) — artefakty rund w repo nietknięte.
"""

from __future__ import annotations

import ast
import atexit
import json
import os
import re
import runpy
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CMD_RE = re.compile(
    r"\b(?:py|python3?) -m (backtest\.[A-Za-z0-9_]+)((?: +--?[A-Za-z0-9_\-=.,]+| +[0-9][0-9a-z.]*| +[A-Z][A-Z0-9]*[0-9])*)"
)
TRIGGERS = ("summarize_pnl", "summarize_trade_returns", "effective_sample_size", "t_neff")
TIMEOUT_S = 45 * 60
WORKERS = 20
EXCLUDE = {"backtest.run_au2_ml"}  # własna pula 24 procesów; błąd obsłużony w samej rundzie AU2


def round_commands(repo: Path = REPO) -> list[tuple[str, str, tuple[str, ...]]]:
    """(katalog rundy, moduł, argumenty) z komend `py -m backtest.X …` w README rund; bez duplikatów."""
    seen, out = set(), []
    for readme in sorted(repo.glob("runs/*/README.md")):
        for mod, args in CMD_RE.findall(readme.read_text(encoding="utf-8", errors="replace")):
            key = (mod, tuple(args.split()))
            if key not in seen:
                seen.add(key)
                out.append((readme.parent.name, mod, key[1]))
    return out


def _imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
        elif isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
    return {m for m in mods if m.split(".")[0] in ("backtest", "agents", "data")}


def uses_neff(module: str, repo: Path = REPO, _memo: dict | None = None) -> bool:
    """Czy moduł (albo coś, co importuje z repo) sięga po N_eff — po tekście i importach, rekurencyjnie."""
    memo = {} if _memo is None else _memo
    if module in memo:
        return memo[module]
    memo[module] = False
    path = repo / (module.replace(".", "/") + ".py")
    if not path.is_file():
        return False
    if module != "agents.labeling" and any(t in path.read_text(encoding="utf-8") for t in TRIGGERS):
        memo[module] = True
        return True
    memo[module] = any(uses_neff(m, repo, memo) for m in _imports(path))
    return memo[module]


def old_effective_sample_size(returns, max_lag: int = 50) -> dict:
    """Wzór sprzed AU3 (bez ochrony mianownika) — do trybu `old`."""
    import numpy as np

    clean = returns.dropna()
    n = len(clean)
    autocorrs = [clean.autocorr(lag=k) for k in range(1, max_lag + 1)]
    autocorrs = [a for a in autocorrs if not np.isnan(a)]
    return {"n": n, "n_eff": n / (1 + 2 * sum(autocorrs)), "max_lag": max_lag}


def run_patched(mode: str, module: str, args: list[str]) -> None:
    """Jeden skrypt z licznikiem wywołań N_eff i zdarzeń „mianownik ≤ 0” (zapis do AU3_COUNT_FILE)."""
    import agents.labeling as lab

    fixed = lab.effective_sample_size
    counts = {"calls": 0, "bad_denominator": 0}

    def counted(returns, max_lag: int = 50):
        counts["calls"] += 1
        old = old_effective_sample_size(returns, max_lag)
        if old["n"] and not (old["n_eff"] > 0):
            counts["bad_denominator"] += 1
        return old if mode == "old" else fixed(returns, max_lag)

    lab.effective_sample_size = counted
    out = os.environ.get("AU3_COUNT_FILE")
    if out:
        atexit.register(lambda: Path(out).write_text(json.dumps(counts)))
    sys.argv = [module, *args]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


def _exec_one(worktree: Path, out_dir: Path, mode: str, rnd: str, mod: str, args: tuple) -> dict:
    tag = f"{mod.split('.')[-1]}{'_' + '_'.join(a.strip('-') for a in args) if args else ''}_{mode}"
    log, cnt = out_dir / f"{tag}.log", out_dir / f"{tag}.json"
    env = {
        **os.environ,
        "PYTHONUTF8": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "AU3_COUNT_FILE": str(cnt),
        "PYTHONPATH": str(worktree),
    }
    t0 = time.time()
    try:
        with open(log, "w", encoding="utf-8") as fh:
            rc = subprocess.run(
                [sys.executable, str(worktree / "tools/au3_audit.py"), "run", mode, mod, *args],
                cwd=worktree,
                env=env,
                stdout=fh,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_S,
            ).returncode
    except subprocess.TimeoutExpired:
        rc = "timeout"
    counts = json.loads(cnt.read_text()) if cnt.is_file() else {}
    return {
        "round": rnd,
        "module": mod,
        "args": list(args),
        "mode": mode,
        "rc": rc,
        "seconds": round(time.time() - t0),
        "log": log.name,
        **counts,
    }


def exec_all(worktree: Path, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = [
        c for c in round_commands(worktree) if uses_neff(c[1], worktree) and c[1] not in EXCLUDE
    ]
    with ThreadPoolExecutor(WORKERS) as ex:
        old = list(ex.map(lambda c: _exec_one(worktree, out_dir, "old", *c), plan))
        hit = [r for r in old if r.get("bad_denominator", 0) > 0]
        new = list(
            ex.map(
                lambda r: _exec_one(
                    worktree, out_dir, "new", r["round"], r["module"], tuple(r["args"])
                ),
                hit,
            )
        )
    res = old + new
    (out_dir / "wyniki.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def main(argv: list[str]) -> int:
    if argv[:1] == ["run"]:
        run_patched(argv[1], argv[2], argv[3:])
        return 0
    if argv[:1] == ["plan"]:
        for rnd, mod, args in round_commands():
            print(f"{'N_eff' if uses_neff(mod) else '-    '}  {rnd:<48} {mod} {' '.join(args)}")
        return 0
    if argv[:1] == ["exec"]:
        res = exec_all(Path(argv[1]), Path(argv[2]))
        for r in res:
            print(json.dumps(r, ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
