"""Testy backtest/odczyt_dziennika.py (odczyt dziennika, szczebel 3 ADR-09) i czystej części
backtest/odczyt_dziennika_stale.py (μ, σ nóg). Repo git syntetyczne — wzorzec z test_strona_dziennika.
"""

from __future__ import annotations

import json
import math
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import odczyt_dziennika as od
from backtest.odczyt_dziennika_stale import mu_sigma
from tests.test_strona_dziennika import FILES, _git, _repo
from tools import strona_dziennika as sd

ROOT = Path(__file__).resolve().parents[1]
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="brak gita")
LEG = od.Leg("T", "test", "wyniki.csv", "r_port", 0.10, 0.20, "ręcznie")


# ------------------------------------------------------------------ próg obalenia


def test_refutation_matches_hand_computation():
    # n = 146 dni = 0,4 roku → SE = 0,20/√0,4 = 0,316228; próg = 0,10 − 2,31·0,316228 = −0,630486
    r = od.refutation(0.10, 0.20, 146, z=2.31)
    assert r["se"] == pytest.approx(0.316228, abs=1e-6)
    assert r["threshold"] == pytest.approx(-0.630486, abs=1e-6)
    assert r["years_to_detect"] == pytest.approx(16.0)  # (2·0,2/0,1)²
    assert od.refutation(0.10, 0.20, 365)["threshold"] == pytest.approx(0.10 - od.Z_READ * 0.20)
    assert od.refutation(-0.01, 0.2, 365)["years_to_detect"] == math.inf
    with pytest.raises(ValueError):
        od.refutation(0.1, 0.2, 0)


def test_leg_reading_crosses_only_below_threshold_at_binding_reading():
    # n = 92: SE = 0,2/√(92/365) = 0,398366; próg = 0,1 − 2,31·0,398366 = −0,820226 /rok
    thr_daily = -0.820226 / 365
    below = od.leg_reading(LEG, [-0.003] * 92)  # −1,095/rok < próg
    above = od.leg_reading(LEG, [-0.002] * 92)  # −0,730/rok > próg
    assert -0.003 < thr_daily < -0.002
    assert below["threshold"] == pytest.approx(-0.820226, abs=1e-6)
    assert below["binding"] and below["reading"] == 1
    assert below["crossed"] and below["verdict"] == "próg obalenia PRZEKROCZONY (obalona)"
    assert not above["crossed"]
    assert above["verdict"] == "próg obalenia nieprzekroczony (brak obalenia)"
    assert below["mean"] == pytest.approx(-1.095) and below["total"] == pytest.approx(-0.276)
    assert below["threshold_period"] == pytest.approx(-0.820226 * 92 / 365, abs=1e-6)


def test_too_early_is_only_a_preview():
    g = od.leg_reading(LEG, [-0.05] * 89)
    assert not g["binding"] and g["label"] == "ZA WCZEŚNIE — tylko podgląd"
    assert g["crossed"] and g["verdict"] == "podgląd: średnia poniżej progu (nie wiąże)"
    assert "obalona" not in g["verdict"]


@pytest.mark.parametrize(
    "n, binding, reading",
    [
        (0, False, 0),
        (89, False, 0),
        (90, True, 1),
        (92, True, 1),
        (99, True, 1),
        (100, False, 0),
        (179, False, 0),
        (180, True, 2),
        (189, True, 2),
        (190, False, 0),
        (363, True, 3),
        (372, True, 3),
        (373, False, 0),
    ],
)
def test_reading_status_windows(n, binding, reading):
    s = od.reading_status(n)
    assert (s["binding"], s["reading"]) == (binding, reading)
    if n > 372:
        assert s["label"].startswith("po planie 3 odczytów")
    elif 100 <= n <= 179:
        assert s["label"].startswith("podgląd między odczytami")


def test_first_reading_date_is_christmas_eve_result():
    last = date.fromisoformat(sd.R1_START) + timedelta(days=od.READ_DAYS[0] - 1)
    assert last.isoformat() == "2026-12-24"
    assert sd.READING == "2026-12-25"


def test_leg_with_missing_values_counts_them_and_ignores_them():
    vals = ["0.01", "", None, "nan", "inf", "abc", "-0.01", 0.02]
    g = od.leg_reading(LEG, vals)
    assert (g["n"], g["missing"]) == (3, 5)
    assert g["mean"] == pytest.approx(0.02 / 3 * 365)
    empty = od.leg_reading(LEG, ["", "nan"])
    assert (empty["n"], empty["missing"], empty["verdict"]) == (0, 2, "brak danych")


@settings(max_examples=100, deadline=None)
@given(
    mu=st.floats(-0.5, 1.0),
    sigma=st.floats(0.01, 1.0),
    n=st.integers(1, 2000),
    daily=st.floats(-0.05, 0.05),
)
def test_threshold_properties(mu, sigma, n, daily):
    """Próg rośnie z n ku μ; przekroczenie ⇔ średnia < próg."""
    a, b = od.refutation(mu, sigma, n), od.refutation(mu, sigma, n + 1)
    assert a["threshold"] < b["threshold"] < mu
    g = od.leg_reading(od.Leg("T", "t", "f", "c", mu, sigma, "s"), [daily] * n)
    assert g["crossed"] == (daily * 365 < g["threshold"])


# ------------------------------------------------------------------ kryterium 4b


def _alternating(vol: float, n: int = 92) -> list[float]:
    """±a na przemian, sd (ddof=1) dobrane tak, by zmienność roczna = vol."""
    a = vol / math.sqrt(365) / math.sqrt(n / (n - 1))
    return [a if i % 2 == 0 else -a for i in range(n)]


@pytest.mark.parametrize(
    "vol, ok",
    [(0.13, True), (0.31, True), (0.1299, False), (0.3101, False), (0.20, True)],
)
def test_vol_band_edges_inclusive(vol, ok):
    r = od.vol_band(_alternating(vol))
    assert r["vol"] == pytest.approx(vol, rel=1e-9)
    assert r["ok"] is ok and r["n"] == 92


def test_vol_band_too_few_days():
    assert od.vol_band(["0.01"])["ok"] is None and od.vol_band([])["vol"] is None


@settings(max_examples=60, deadline=None)
@given(
    xs=st.lists(st.floats(-0.2, 0.2), min_size=2, max_size=60),
    c=st.floats(0.1, 10.0),
)
def test_vol_band_scales_with_returns(xs, c):
    a, b = od.vol_band(xs), od.vol_band([c * x for x in xs])
    assert b["vol"] == pytest.approx(c * a["vol"], rel=1e-9, abs=1e-12)


# ------------------------------------------------------------------ symulacja z


def test_simulate_z_matches_exact_value_and_is_reproducible():
    z = od.simulate_z(n_sim=400_000, seed=7)
    # dokładna całka normalna 3-wymiarowa (scipy) = 2,3113; błąd kwantyla przy 4e5 ≈ 0,011
    assert z == pytest.approx(2.3113, abs=0.03)
    assert od.simulate_z(n_sim=50_000, seed=7) == od.simulate_z(n_sim=50_000, seed=7, batch=7_000)
    assert round(z, 2) == pytest.approx(od.Z_READ, abs=0.03)


def test_simulate_z_single_reading_is_normal_quantile_and_z_between_bounds():
    assert od.simulate_z(days=(92,), n_sim=400_000, seed=1) == pytest.approx(1.96, abs=0.02)
    # z między jednym odczytem (1,96) a Bonferronim bez korelacji (2,394)
    assert 1.96 < od.Z_READ < 2.394
    with pytest.raises(ValueError):
        od.simulate_z(days=(182, 92))


def test_simulate_z_exact_second_way():
    stats = pytest.importorskip("scipy.stats")
    d = od.READ_DAYS
    cov = [[math.sqrt(min(a, b) / max(a, b)) for b in d] for a in d]
    mvn = stats.multivariate_normal(mean=[0.0] * 3, cov=cov)
    # łączna szansa fałszywego obalenia przy Z_READ ≈ 2,5 %; przy 1,96 ≈ 5,7 % (docs/rag/11)
    assert 1 - mvn.cdf([od.Z_READ] * 3) == pytest.approx(od.ALPHA, abs=0.0005)
    assert 1 - mvn.cdf([1.96] * 3) == pytest.approx(0.0567, abs=0.001)


# ------------------------------------------------------------------ kryteria 1–4


def _crit(**kw) -> dict:
    c = {
        "completeness": {"days": 100, "covered": 95, "missing": []},
        "timeliness": {"days": 100, "late": ["x"] * 5},
        "consistency": {"events": 2, "after_first_result": 0},
        "margin": {"median": 0.23, "min": 0.1, "max": 0.4, "n": 100},
        "k_max": {"trend": 2.0, "coinbase": 1.2, "cap": 2.0},
    }
    for path, v in kw.items():
        a, b = path.split("__")
        c[a][b] = v
    return {"criteria": c}


def test_mechanics_thresholds_at_edges():
    m = od.mechanics(_crit())
    assert all(m[k]["ok"] for k in m)
    assert m["1_kompletnosc"]["share"] == 0.95 and m["3_terminowosc"]["share"] == 0.95


@pytest.mark.parametrize(
    "kw, key",
    [
        ({"completeness__covered": 94}, "1_kompletnosc"),
        ({"consistency__after_first_result": 1}, "2_spojnosc"),
        ({"timeliness__late": ["x"] * 6}, "3_terminowosc"),
        ({"margin__median": 0.351}, "4_zgodnosc_sz1"),
        ({"margin__median": 0.149}, "4_zgodnosc_sz1"),
        ({"margin__median": None}, "4_zgodnosc_sz1"),
        ({"k_max__trend": 2.01}, "4_zgodnosc_sz1"),
        ({"k_max__coinbase": None}, "4_zgodnosc_sz1"),
        ({"completeness__days": 0}, "1_kompletnosc"),
    ],
)
def test_mechanics_names_failing_criterion(kw, key):
    m = od.mechanics(_crit(**kw))
    assert [k for k in m if not m[k]["ok"]] == [key]


# ------------------------------------------------------------------ odczyt z repo git


START = date(2026, 9, 24)


def _journal(n_days: int, r_port: float = 0.0005, x1: bool = True) -> dict[str, str]:
    """Dziennik n dni wyniku od 24.09: sygnały od 23.09, log przebiegu każdego dnia."""
    days = [START + timedelta(days=i) for i in range(n_days)]
    asofs = [START - timedelta(days=1)] + days[:-1] + [days[-1]]
    res = ["date,r_trend,r_coinbase,k_trend,k_coinbase,r_port,equity,drawdown"]
    xr = ["date,r_x1,equity,drawdown"]
    for i, d in enumerate(days):
        rp = r_port if i % 2 == 0 else -r_port / 2
        res.append(f"{d},{2 * rp},{rp},1.5,0.5,{rp},1.0,0.0")
        if d > START:
            xr.append(f"{d},{-rp},1.0,0.0")
    sig = ["as_of,component,symbol,exposure,margin,k,today"]
    log = []
    for a in sorted(set(asofs)):
        sig.append(f"{a},trend,BTCUSDT,0.2,0.1,1.5,True")
        sig.append(f"{a},coinbase,BTCUSDT,0.3,0.12,0.5,True")
        ts = f"{a + timedelta(days=1)}T02:30:00+00:00"
        res_n = 0 if a < START else 1
        log.append(
            f"{ts} | as_of {a} | binance {a} | premia {a} | sygnały +2 | wyniki +{res_n} | "
            f"kapitał 1.0 | obsunięcie 0.0% | OK | historia zmieniona: 0"
        )
    files = {
        "wyniki.csv": "\n".join(res) + "\n",
        "sygnaly.csv": "\n".join(sig) + "\n",
        "przebiegi.log": "\n".join(log) + "\n",
    }
    if x1:
        files["x1_wyniki.csv"] = "\n".join(xr) + "\n"
    return files


def _now(n_days: int) -> datetime:
    last = START + timedelta(days=n_days - 1)
    return datetime.combine(last + timedelta(days=1), datetime.min.time(), timezone.utc).replace(
        hour=6, minute=30
    )


@needs_git
def test_reading_on_first_planned_day_is_binding(tmp_path):
    repo = _repo(tmp_path, _journal(92))
    rep = od.reading(str(repo), now=_now(92))
    assert rep["window"] == {"first": "2026-09-24", "last": "2026-12-24", "n": 92}
    assert rep["status"]["binding"] and rep["status"]["reading"] == 1
    assert all(v["ok"] for v in rep["mechanics"].values()), rep["mechanics"]
    assert rep["mechanics"]["1_kompletnosc"]["days"] == 93  # as_of 23.09 → 24.12
    assert rep["mechanics"]["4_zgodnosc_sz1"]["margin"]["median"] == pytest.approx(0.22)
    assert [g["key"] for g in rep["legs"]] == ["TS1", "CP1", "R1", "X1"]
    x1 = rep["legs"][-1]
    assert x1["n"] == 91 and x1["binding"]  # X1 od 25.09
    r1 = next(g for g in rep["legs"] if g["key"] == "R1")
    assert r1["mean"] == pytest.approx((46 * 0.0005 - 46 * 0.00025) / 92 * 365)
    assert r1["verdict"] == "próg obalenia nieprzekroczony (brak obalenia)"
    assert rep["vol_band"]["binding"] and rep["vol_band"]["ok"] is False  # ~1 %/rok < 13 %
    txt = od.render(rep)
    assert "odczyt wiążący 1 z 3" in txt and "Brak obalenia ≠ potwierdzenie" in txt
    assert "ZA WCZEŚNIE" not in txt


@needs_git
def test_reading_short_journal_says_too_early_and_skips_absent_x1(tmp_path):
    repo = _repo(tmp_path, _journal(10, x1=False))
    rep = od.reading(str(repo), now=_now(10))
    assert [g["key"] for g in rep["legs"]] == ["TS1", "CP1", "R1"]
    assert not rep["status"]["binding"] and not rep["vol_band"]["binding"]
    txt = od.render(rep)
    assert "STATUS: ZA WCZEŚNIE — tylko podgląd" in txt and "X1" not in txt.split("Kryterium 5")[1]
    assert "obalona" not in txt


@needs_git
def test_as_of_reads_journal_snapshot(tmp_path):
    repo = _repo(tmp_path, _journal(92))  # commit „Dziennik: przebieg 2026-09-26 (host1)”
    _git(repo, "commit", "-q", "--amend", "-m", "Dziennik: przebieg 2026-12-25 (host1)")
    first = sd.git(str(repo), "rev-parse", "HEAD").strip()
    for name, body in _journal(95).items():
        (repo / "dziennik" / name).write_text(body, encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "Dziennik: przebieg 2026-12-28 (host1)")
    _git(repo, "update-ref", "refs/remotes/origin/master", "HEAD")
    rep = od.reading(str(repo), as_of=date(2026, 12, 24))
    assert rep["ref"] == first and rep["as_of"] == "2026-12-24"
    assert rep["window"]["n"] == 92 and rep["mechanics"]["1_kompletnosc"]["share"] == 1.0
    assert sd.REF == "origin/master"  # ref przywrócony
    assert od.reading(str(repo))["window"]["n"] == 95
    with pytest.raises(ValueError, match="brak commita dziennika"):
        od.snapshot_ref(str(repo), date(2026, 12, 20))


@needs_git
def test_main_text_json_and_errors(tmp_path, capsys):
    repo = str(_repo(tmp_path, FILES))
    assert od.main(["--repo", repo]) == 0
    out = capsys.readouterr().out
    assert "STATUS: ZA WCZEŚNIE — tylko podgląd" in out and "UWAGA: ZA WCZEŚNIE" in out
    assert od.main(["--repo", repo, "--json"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["status"]["binding"] is False and rep["plan"]["z"] == od.Z_READ
    assert od.main(["--repo", repo, "--as-of", "2026-01-01"]) == 1
    assert "BŁĄD: ValueError" in capsys.readouterr().err
    norepo = _repo(tmp_path / "b", FILES, ref=False)
    assert od.main(["--repo", str(norepo)]) == 1


# ------------------------------------------------------------------ stałe i dokumentacja


def test_mu_sigma_hand_computed():
    idx = pd.date_range("2021-01-01", periods=4, freq="D", tz="UTC")
    s = mu_sigma(pd.Series([0.01, -0.01, 0.02, float("nan")], index=idx))
    assert s["n"] == 3 and s["mu"] == pytest.approx(0.02 / 3 * 365)
    assert s["sigma"] == pytest.approx(pd.Series([0.01, -0.01, 0.02]).std() * math.sqrt(365))
    assert s["cagr"] == pytest.approx((1.01 * 0.99 * 1.02) ** (365 / 3) - 1)
    with pytest.raises(ValueError):
        mu_sigma(pd.Series([0.01]))


def test_readme_records_the_same_constants():
    """Umowa odczytu w dziennik/README.md i stałe skryptu nie mogą się rozjechać."""
    text = (ROOT / "dziennik" / "README.md").read_text(encoding="utf-8")
    sec = text.split("Zmiana kryteriów odczytu", 1)[1].split("\n## ", 1)[0]
    fmt = lambda x: f"{100 * x:.2f}".replace(".", ",")  # noqa: E731
    for g in od.LEGS:
        row = next(line for line in sec.splitlines() if line.startswith(f"| {g.key} "))
        assert fmt(g.mu) in row and fmt(g.sigma) in row, row
    assert f"z = {od.Z_READ:.2f}".replace(".", ",") in sec
    assert re.search(r"\[13; 31\]", sec) and "python -m backtest.odczyt_dziennika" in sec.replace(
        "py -m", "python -m"
    )
