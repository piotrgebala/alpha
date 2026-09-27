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
# Po scaleniu takiej gałęzi wpis trzeba usunąć — pilnuje test_oczekiwane_not_stale.
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


def test_oczekiwane_not_stale():
    # wyjątek zostawiony po scaleniu ukryłby „wiersz-ducha”, gdyby runda kiedyś zniknęła
    stale = sorted(k for k in OCZEKIWANE if (RUNS / k).is_dir())
    assert not stale, f"katalog już jest w runs/ — usuń z OCZEKIWANE: {stale}"


def test_registry_has_no_errors():
    assert dsr.registry_errors(ROWS) == []


def test_no_duplicate_dirs():
    kat = [r["katalog"] for r in ROWS]
    assert len(kat) == len(set(kat))


def test_allowed_values():
    assert {r["baza"] for r in ROWS} <= dsr.BAZY
    assert {r["rodzaj"] for r in ROWS} <= dsr.RODZAJE
    assert {r["odczyt_programu"] for r in ROWS} <= dsr.ODCZYT


BASE = [dict(r) for r in ROWS[:3]]  # T4, W1, N1: poprawny prefiks rejestru


def _mut(**zmiany) -> dict[str, str]:
    return {**BASE[2], **zmiany}


# (wiersz 3 po zmianie, fragment jedynego oczekiwanego komunikatu) — po jednym na każdą regułę
BAD_ROWS = [
    (_mut(nr="7"), "numeracja ciągła"),
    (_mut(data="2026-09-22", katalog="2026-09-22_n1-x"), "wcześniejsza"),
    (_mut(katalog="x"), "nie zaczyna"),
    (_mut(katalog=BASE[1]["katalog"]), "duplikat"),
    (_mut(runda=" "), "pusta runda"),
    (_mut(uwagi=" "), "puste uwagi"),
    (_mut(baza="krypto"), "baza 'krypto'"),
    (_mut(rodzaj="cos"), "rodzaj 'cos'"),
    (_mut(odczyt_programu="moze"), "odczyt_programu 'moze'"),
    (_mut(wariantow="-1"), "wariantow '-1'"),
    (_mut(rodzaj="bez-wyniku", wariantow="0"), "sprzeczność"),
    (_mut(odczyt_programu="nie", wariantow="2"), "warianty zużyte"),
    (_mut(baza="stara-baza", odczyt_programu="nie", wariantow="1"), "warianty zużyte"),
    ({k: v for k, v in BASE[2].items() if k != "uwagi"}, "kolumny"),
    ({**BASE[2], None: ["nadmiar"]}, "kolumny"),
    (_mut(uwagi=None), "brak pól"),
]


def test_base_prefix_is_valid():
    assert dsr.registry_errors(BASE) == []


@pytest.mark.parametrize("zly, frag", BAD_ROWS, ids=[f for _, f in BAD_ROWS])
def test_registry_errors_catch_each_rule(zly, frag):
    errs = dsr.registry_errors([*BASE[:2], zly])
    assert len(errs) == 1, errs
    assert errs[0].startswith("wiersz 3") and frag in errs[0], errs


def test_registry_rules_that_must_not_fire():
    # 0 wariantów bez odczytu i warianty na innej bazie (TX1) nie są błędem
    assert dsr.registry_errors([*BASE[:2], _mut(odczyt_programu="nie", wariantow="0")]) == []
    tx = _mut(baza="tradfi-1990-2026", odczyt_programu="nie", wariantow="1")
    assert dsr.registry_errors([*BASE[:2], tx]) == []


def test_load_registry_short_row_and_bom(tmp_path):
    tekst = dsr.REJESTR.read_text(encoding="utf-8")
    bom = tmp_path / "bom.csv"
    bom.write_text("\ufeff" + tekst, encoding="utf-8")
    rows = dsr.load_registry(bom)
    assert rows == ROWS and dsr.registry_errors(rows) == []
    krotki = tmp_path / "krotki.csv"
    naglowek, pierwszy = tekst.splitlines()[:2]
    krotki.write_text(naglowek + "\n" + pierwszy.split(',"')[0] + "\n", encoding="utf-8")
    errs = dsr.registry_errors(dsr.load_registry(krotki))
    assert len(errs) == 1 and "brak pól" in errs[0]


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
    # Metoda AU4 (Σ wariantów) dla obu dat: pre-rejestracja AU4 podaje 40 w dniu AU4 (twardo)
    # i „~28” przy CP1 (przybliżenie za README CP1 — stąd zakres; rejestr daje 27).
    nr_au4 = int(_row("2026-09-25_au4-dsr-cp1")["nr"])
    nr_cp1 = int(_row("2026-09-24_cp1-premia-coinbase")["nr"])
    assert dsr.n_warianty(ROWS, nr_au4) == 40
    assert 27 <= dsr.n_warianty(ROWS, nr_cp1) <= 29
    # Metoda z odczytami 0-wariantowymi (Σ max(w, 1)) w dniu AU4 daje 50, nie 40: to zmiana
    # metody (10 odczytów 0-wariantowych sprzed AU4), nie przedłużenie liczenia AU4.
    assert dsr.n_program(ROWS, nr_au4) == 50
    zero_do_au4 = [r for r in dsr._odczyty(ROWS, nr_au4) if r["wariantow"] == "0"]
    assert len(zero_do_au4) == 10
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
    for n in (0, -3):
        with pytest.raises(ValueError, match="liczba prób"):
            dsr.required_t(n, 0.95)


@pytest.mark.parametrize("d", [0.05, 0.3, 0.5, 0.8, 0.95])
def test_required_t_exact_all_levels(d):
    # dsr < 0,5: pierwiastek leży poniżej SR0 (wcześniej brentq w [sr0; sr0 + 1] padał)
    t_star = dsr.required_t(41, d, n_obs=1880)
    assert t_star == pytest.approx(dsr.required_t(41, d), abs=0.01)
    sr0 = dsr.expected_max_sr(41, 1 / 1880)
    assert dsr.deflated_sharpe(t_star / np.sqrt(1880), sr0, 1880, 0.0, 3.0) == pytest.approx(d)


def test_required_t_exact_short_sample_and_heavy_tails():
    # krótka próba: próg wyraźnie wyżej niż asymptotyczny, ale istnieje
    assert dsr.required_t(41, 0.95, n_obs=3) > dsr.required_t(41, 0.95) + 5
    # g3 = 3, g4 = 7,8: wzór nie działa dla SR ∈ (0,45; 1,32); pierwiastek (SR ≈ 0,08) leży przed
    t_star = dsr.required_t(41, 0.95, n_obs=1880, g3=3.0, g4=7.8)
    sr0 = dsr.expected_max_sr(41, 1 / 1880)
    assert dsr.deflated_sharpe(t_star / np.sqrt(1880), sr0, 1880, 3.0, 7.8) == pytest.approx(0.95)
    # grube ogony + krótka próba: DSR ma asymptotę Φ(2√(T − 1)/√(g4 − 1)) < 0,95 → czytelny błąd
    for g4 in (20.0, 50.0):
        with pytest.raises(ValueError, match="nieosiągalne"):
            dsr.required_t(41, 0.95, n_obs=5, g4=g4)


def test_deflated_sharpe_rejects_negative_radicand():
    with pytest.raises(ValueError, match="nie działa"):
        dsr.deflated_sharpe(0.8, 0.0, 100, 3.0, 7.8)


def test_cli_prints_thresholds(capsys):
    dsr.main(["--n", "41"])
    out = capsys.readouterr().out
    assert "2.20" in out and "3.04" in out and "3.84" in out and "1.64" in out
    dsr.main([])
    out = capsys.readouterr().out
    n_reg, n_au4 = dsr.n_program(ROWS), dsr.n_warianty(ROWS)
    assert f"progi dla N + 1 = {n_au4 + 1} (metodą AU4) i {n_reg + 1} " in out
    assert "obowiązuje, zapisuje się w STATUS.md" in out  # skrypt nie wybiera metody N
    assert not re.search(r"obowiązuje\)|obowiązuje:", out)
    dsr.main(["--k", "9"])
    out = capsys.readouterr().out
    assert f"progi dla N + 9 = {n_au4 + 9} (metodą AU4) i {n_reg + 9} " in out
    assert f"  {n_au4 + 9:4d} |" in out and f"  {n_reg + 9:4d} |" in out
    dsr.main(["--k", "0"])  # runda 0-wariantowa z odczytem liczy się za 1
    assert f"N + 1 = {n_au4 + 1}" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        dsr.main(["--k", "-1"])
    with pytest.raises(ValueError):
        dsr.report(ROWS, k=-1)


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
