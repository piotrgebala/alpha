"""
CLAUDE.md zasada 3: target (triple-barrier) i stop-loss używają TEGO SAMEGO mnożnika ATR.

Źródłem prawdy jest stała `agents.labeling.ATR_MULTIPLIER`, importowana przez
`agents.risk_controller`. `config/settings.yaml` → `labeling.atr_multiplier` jest drugą,
NIEUŻYWANĄ przez kod kopią tej wartości (stan 2026-09-22) — nic jej nie wiązało ze stałą,
więc mogła się rozjechać bez śladu. Ten test to wiązanie.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import yaml

from agents import risk_controller
from agents.labeling import ATR_MULTIPLIER

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"


def test_config_atr_multiplier_matches_labeling_constant():
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert cfg["labeling"]["atr_multiplier"] == ATR_MULTIPLIER


def test_risk_controller_defaults_use_labeling_constant():
    """Każdy parametr `atr_multiplier` w risk_controller domyślnie = stała z labeling."""
    checked = 0
    for _, func in inspect.getmembers(risk_controller, inspect.isfunction):
        if func.__module__ != risk_controller.__name__:
            continue
        param = inspect.signature(func).parameters.get("atr_multiplier")
        if param is not None and param.default is not inspect.Parameter.empty:
            assert param.default == ATR_MULTIPLIER, func.__name__
            checked += 1
    # Test, który niczego nie sprawdził, nie jest testem (lessons: bramka musi móc zawieść).
    assert checked >= 1
