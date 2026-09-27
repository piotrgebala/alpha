"""
Strażnik rejestru odczytów historii (`runs/odczyty_historii.csv`) i testy `backtest/dsr.py`.

Po co: próg t w pre-rejestracji zależy od liczby odczytów programu (DSR — Sharpe po korekcie na
liczbę prób; AU4, wniosek 96). Rejestr bez wiersza dla nowej rundy zaniżałby N, więc strażnik
wymaga wiersza dla każdego katalogu rundy od 2026-09-23 (nowa baza, zasada 20). Wzory muszą
odtwarzać liczby AU4 (`runs/2026-09-25_au4-dsr-cp1/raw_output.txt`) i przeglądu `docs/rag/11`.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import dsr

RUNS = Path(__file__).resolve().parents[1] / "runs"
AU4_RAW = RUNS / "2026-09-25_au4-dsr-cp1" / "raw_output.txt"
DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_[a-z0-9][a-z0-9.\-]*$")
OD_DATY = "2026-09-23"
# Rundy z gałęzi równoległych, dopisane do rejestru z góry (katalog pojawi się po scaleniu).
OCZEKIWANE = {"2026-09-27_lb0-kolektor-bybit"}

ROWS = dsr.load_registry()


def _row(katalog: str) -> dict[str, str]:
    return next(r for r in ROWS if r["katalog"] == katalog)


# ---------------------------------------------------------------------------- (a)–(c) rejestr


def test_every_run_dir_since_new_base_has_row():
    kat = {r["katalog"] for r in ROWS}
    dirs = [
        p.name
        for p in RUNS.iterdir()
        if p.is_dir() and DIR_RE.match(p.name) and DIR_RE.match(p.name).group(1) >= OD_DATY
    ]
    missing = sorted(d for d in dirs if d not in kat)
    assert not missing, f"katalogi rund bez wiersza w runs/odczyty_historii.csv: {missing}"


def test_every_row_points_to_existing_dir():
    ghosts = [
        r["katalog"]
        for r in ROWS
        if not (RUNS / r["katalog"]).is_dir() and r["katalog"] not in OCZEKIWANE
    ]
    assert not ghosts, f"wiersze rejestru bez katalogu w runs/: {ghosts}"


def test_registry_has_no_errors():
    assert dsr.registry_errors(ROWS) == []


def test_no_duplicate_dirs():
    kat = [r["katalog"] for r in ROWS]
    assert len(kat) == len(set(kat))


def test_allowed_values():
    assert {r["baza"] for r in ROWS} <= dsr.BAZY
    assert {r["rodzaj"] for r in ROWS} <= dsr.RODZAJE
    assert {r["odczyt_programu"] for r in ROWS} <= dsr.ODCZYT


def test_registry_errors_catch_bad_rows():
    good = dict(ROWS[0])
    bad = [
        {**good, "baza": "krypto"},
        {**good, "nr": "2", "rodzaj": "cos"},
        {**good, "nr": "3", "katalog": good["katalog"], "odczyt_programu": "moze"},
        {**good, "nr": "4", "katalog": "x", "wariantow": "-1", "uwagi": ""},
    ]
    errs = "\n".join(dsr.registry_errors(bad))
    for frag in ("baza", "rodzaj", "duplikat", "odczyt_programu", "nie zaczyna", "wariantow"):
        assert frag in errs


def test_zero_variant_readings_named_in_review_count():
    # docs/rag/11 §4E: rundy 0-wariantowe drukujące zwrot lub t są odczytami programu
    for kat in (
        "2026-09-24_x1f-siedem-faz",
        "2026-09-24_ru1-pelne-uniwersum",
        "2026-09-24_ru2-korekta-pozostalych",
        "2026-09-24_ru3-data-startu",
        "2026-09-25_ru4-tl1-pelne-oi",
        "2026-09-24_cp1-poza-proba",
    ):
        r = _row(kat)
        assert (r["odczyt_programu"], r["wariantow"]) == ("tak", "0"), kat
    for kat in (
        "2026-09-25_mx1-macd-ema-1h",
        "2026-09-26_tp1-cel-zysku",
        "2026-09-25_lk0-kolektor-likwidacji",
    ):
        assert _row(kat)["odczyt_programu"] == "nie", kat


def test_n_matches_au4_counts():
    # AU4 (pre-rejestracja): 40 wariantów na dzień AU4, ~28 w chwili odczytu CP1
    nr_au4 = int(_row("2026-09-25_au4-dsr-cp1")["nr"])
    nr_cp1 = int(_row("2026-09-24_cp1-premia-coinbase")["nr"])
    assert dsr.n_warianty(ROWS, nr_au4) == 40
    assert dsr.n_program(ROWS, nr_cp1) == 28
    assert dsr.n_program(ROWS) >= dsr.n_warianty(ROWS) >= 40


def test_n_program_counts_zero_variant_reading_as_one():
    rows = [
        {"nr": "1", "odczyt_programu": "tak", "wariantow": "3"},
        {"nr": "2", "odczyt_programu": "tak", "wariantow": "0"},
        {"nr": "3", "odczyt_programu": "nie", "wariantow": "1"},
    ]
    assert dsr.n_program(rows) == 4
    assert dsr.n_warianty(rows) == 3
    assert dsr.n_program(rows, do_nr=1) == 3


# ---------------------------------------------------------------------------- (d) liczby AU4 i przeglądu


def _au4_table() -> list[tuple[int, float, float, float]]:
    rows = []
    for line in AU4_RAW.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s+(\d+) \|\s+([\d.]+) \|\s+([\d.]+) \|\s+([\d.]+) \|", line)
        if m:
            rows.append((int(m[1]), float(m[2]), float(m[3]), float(m[4])))
    assert [r[0] for r in rows] == [5, 10, 20, 28, 40]
    return rows


def test_expected_max_t_and_dsr_reproduce_au4_output():
    # CP1 z raw_output AU4: SR dzienny 0,0482, T 1 880, skośność +0,31, kurtoza 7,8
    sr, t_obs, g3, g4 = 0.0482, 1880, 0.31, 7.8
    for n, sr0_roczny, emax, dsr_au4 in _au4_table():
        assert dsr.expected_max_t(n) == pytest.approx(emax, abs=0.01)
        sr0 = dsr.expected_max_sr(n, 1.0 / t_obs)
        assert sr0 * np.sqrt(365) == pytest.approx(sr0_roczny, abs=0.01)
        assert dsr.deflated_sharpe(sr, sr0, t_obs, g3, g4) == pytest.approx(dsr_au4, abs=0.01)


def test_review_numbers_for_41_readings():
    assert dsr.expected_max_t(41) == pytest.approx(2.20, abs=0.01)
    assert dsr.required_t(41, 0.80) == pytest.approx(3.04, abs=0.01)
    assert dsr.required_t(41, 0.95) == pytest.approx(3.84, abs=0.01)
    assert dsr.min_annual_sr(dsr.required_t(41, 0.95), 5.5) == pytest.approx(1.64, abs=0.01)


def test_required_t_exact_converges_to_asymptotic():
    asym = dsr.required_t(41, 0.95)
    assert dsr.required_t(41, 0.95, n_obs=1_000_000) == pytest.approx(asym, abs=0.01)
    # grube ogony i krótka próba podnoszą próg
    assert dsr.required_t(41, 0.95, n_obs=500, g4=20.0) > dsr.required_t(41, 0.95, n_obs=500)
    # z definicji: przy t* DSR = zadany poziom
    t_star = dsr.required_t(10, 0.8, n_obs=1880, g3=0.3, g4=7.8)
    sr0 = dsr.expected_max_sr(10, 1 / 1880)
    assert dsr.deflated_sharpe(t_star / np.sqrt(1880), sr0, 1880, 0.3, 7.8) == pytest.approx(0.8)


def test_expected_max_t_matches_simulation():
    rng = np.random.default_rng(0)
    for n in (10, 41):
        sim = rng.standard_normal((20_000, n)).max(axis=1).mean()
        assert dsr.expected_max_t(n) == pytest.approx(sim, rel=0.03)
    assert dsr.expected_max_t(1) == 0.0


def test_required_t_rejects_bad_input():
    with pytest.raises(ValueError):
        dsr.required_t(10, 1.0)
    with pytest.raises(ValueError):
        dsr.required_t(10, 0.95, n_obs=2)


def test_cli_prints_thresholds(capsys):
    dsr.main(["--n", "41"])
    out = capsys.readouterr().out
    assert "2.20" in out and "3.04" in out and "3.84" in out and "1.64" in out
    dsr.main([])
    out = capsys.readouterr().out
    assert f"Następny odczyt historii będzie {dsr.n_program(ROWS) + 1}." in out


# ---------------------------------------------------------------------------- (e) właściwości


@settings(max_examples=200, deadline=None)
@given(st.integers(min_value=1, max_value=10**6), st.integers(min_value=1, max_value=10**6))
def test_expected_max_t_increases_with_n(n, k):
    assert dsr.expected_max_t(n + k) > dsr.expected_max_t(n)


@settings(max_examples=100, deadline=None)
@given(
    st.integers(min_value=2, max_value=10_000),
    st.floats(min_value=0.5, max_value=0.99),
    st.floats(min_value=0.001, max_value=0.3),
)
def test_required_t_increases_with_dsr_and_n(n, d, step):
    assert dsr.required_t(n, min(d + step, 0.999)) > dsr.required_t(n, d)
    assert dsr.required_t(n + 1, d) > dsr.required_t(n, d)
