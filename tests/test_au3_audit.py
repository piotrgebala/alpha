"""Testy tools/au3_audit.py (AU3): wyciąganie komend z README, wykrywanie N_eff, stary wzór."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import au3_audit as au  # noqa: E402

from agents.labeling import effective_sample_size  # noqa: E402


def test_round_commands_parses_module_and_args(tmp_path):
    d = tmp_path / "runs" / "2026-01-01_x1-test"
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        "`PYTHONUTF8=1 py -m backtest.run_x --moc 100` → moc.txt\n`py -m backtest.run_x --moc 100`\n"
        "`python3 -m backtest.run_y`\n",
        encoding="utf-8",
    )
    cmds = au.round_commands(tmp_path)
    assert cmds == [
        ("2026-01-01_x1-test", "backtest.run_x", ("--moc", "100")),
        ("2026-01-01_x1-test", "backtest.run_y", ()),
    ]


def test_uses_neff_follows_imports(tmp_path):
    (tmp_path / "backtest").mkdir()
    (tmp_path / "backtest/lib.py").write_text("def f(x):\n    return summarize_pnl(x)\n")
    (tmp_path / "backtest/run_a.py").write_text("from backtest.lib import f\n")
    (tmp_path / "backtest/run_b.py").write_text("import os\n")
    assert au.uses_neff("backtest.run_a", tmp_path)
    assert not au.uses_neff("backtest.run_b", tmp_path)


def test_old_formula_reproduces_negative_n_eff_and_fixed_does_not():
    x = pd.Series(np.diff(np.random.default_rng(1).normal(size=221)))
    assert au.old_effective_sample_size(x)["n_eff"] < 0
    assert effective_sample_size(x)["n_eff"] == len(x)
    y = pd.Series(np.random.default_rng(2).normal(size=300)).cumsum().diff()
    assert au.old_effective_sample_size(y)["n_eff"] == effective_sample_size(y)["n_eff"]
