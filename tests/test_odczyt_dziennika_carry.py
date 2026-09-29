"""Testy kryterium 6 odczytu dziennika — noga carry COIN-M, kryteria (a)–(c) z Poprawki 12
(`backtest/odczyt_dziennika.py`: `carry_criteria`, `compare_carry`, `exchange_check`, wydruk).

Bez sieci: pobranie zastępuje atrapa (`fetch`) albo podstawiony `data.fetch_external.http_get`
(wtedy działa prawdziwa `data.fetch_live.fetch_coinm_funding_safe`). Repo git syntetyczne — wzorzec
z test_odczyt_dziennika / test_strona_dziennika. Liczniki (a)–(c) pochodzą z prawdziwej
`tools/strona_dziennika.carry_state` (te same definicje co strona), a wiersze pliku carry
z prawdziwej `journal_carry.carry_rows` zapisanej tak jak w dzienniku (`to_csv` bez indeksu).
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import urllib.error
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import journal_carry as jc
from backtest import odczyt_dziennika as od
from backtest.checkpoint_lib import load_config
from tests.test_odczyt_dziennika import _journal
from tests.test_strona_dziennika import FILES, _git, _repo
from tools import strona_dziennika as sd

ROOT = Path(__file__).resolve().parents[1]
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="brak gita")
COST = jc.carry_costs(load_config(str(od.CONFIG_PATH))["costs"]).switch_cost  # 0,19 % (D1)
MET, UNMET, EARLY, NO_DATA, UNCHECKED = od.MET, od.UNMET, od.EARLY, od.NO_DATA, od.UNCHECKED


# ------------------------------------------------------------------ pomocnicze


def _days(first: str, n: int) -> list[str]:
    d0 = date.fromisoformat(first)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def _run(day: str, carry: str = "", n: int = 0) -> dict:
    """Przebieg w kształcie `strona_dziennika.parse_log` (tylko pola, których używa carry_state)."""
    return {"ts": f"{day}T02:30+00:00", "day": day, "carry": carry, "carry_changed": n}


def _crow(d: str, komplet: bool = True, rozl: int = 3, cum: float = 0.001) -> dict:
    """Wiersz `carry_wyniki.csv` tak, jak czyta go csv.DictReader (same napisy)."""
    return {
        "date": d,
        "rozliczenia": str(rozl),
        "komplet": str(komplet),
        "suma_stawek": "0.0001",
        "koszt": "0.0",
        "netto": "0.0001",
        "netto_skum": str(cum),
    }


def _funding(last: str, drop: tuple[str, ...] = ()) -> pd.DataFrame:
    """Rozliczenia co 8 h od startu carry do `last` 00:00 włącznie (zamyka dzień przed `last`);
    stawki także ujemne i zerowe; `drop` — znaczniki rozliczeń, których giełda nie opublikowała."""
    ts = pd.date_range(sd.CARRY_START, last, freq="8h", tz="UTC")
    f = pd.DataFrame(
        {"timestamp": ts, "funding_rate": [1e-4 * ((i % 5) - 1) for i in range(len(ts))]}
    )
    gone = pd.to_datetime(list(drop), utc=True)
    return f[~f["timestamp"].isin(gone)].reset_index(drop=True)


def _file_rows(df: pd.DataFrame) -> list[dict]:
    """Wiersze jak w dzienniku (`append_rows` → `to_csv` bez indeksu), czytane jak na stronie."""
    return list(csv.DictReader(io.StringIO(df.to_csv(index=False))))


def _crit(rows: list[dict], runs: list[dict], ref_day=None, exchange=None) -> dict:
    last = runs[-1]["day"] if runs else None
    return od.carry_criteria(sd.carry_state(rows, runs), last, ref_day, exchange)


def _fake_fetch(funding: pd.DataFrame | None, calls: list | None = None):
    """Atrapa `fetch_coinm_funding_safe(out_dir)`: parquet w `out_dir` jak funkcja dziennika
    i wydruk na stdout (który nie może trafić do stdout odczytu); None = nieudane pobranie.
    """

    def fetch(out_dir: Path):
        if calls is not None:
            calls.append(Path(out_dir))
        if funding is None:
            print(
                "[live] funding COIN-M BTCUSD_PERP BŁĄD URLError: <urlopen error brak sieci> "
                "— carry bez aktualizacji"
            )
            return None
        path = Path(out_dir) / jc.CARRY_FILE
        funding.to_parquet(path, index=False)
        print(f"[external] coinm funding BTCUSD_PERP: {len(funding)} rekordów")
        return path

    return fetch


def _no_fetch(out_dir: Path):
    raise AssertionError("odczyt bez flagi (albo bez wierszy) nie może pobierać")


# ------------------------------------------------------------------ (a) terminowość


@pytest.mark.parametrize(
    "runs, trouble, status",
    [(20, 0, MET), (20, 1, MET), (19, 1, UNMET), (100, 5, MET), (100, 6, UNMET)],
    ids=["zero", "5proc-granica", "5,3proc", "5-na-100", "6-na-100"],
)
def test_a_threshold_is_inclusive(runs, trouble, status):
    rs = [
        _run(d, "spóźnione" if i < trouble else "") for i, d in enumerate(_days("2026-09-30", runs))
    ]
    a = _crit([], rs)["criteria"]["a"]
    assert a["status"] == status and (a["runs"], a["trouble"]) == (runs, trouble)
    assert a["share"] == pytest.approx(trouble / runs)


def test_a_counts_trouble_fields_from_check_date_and_not_carry_changes():
    rs = [
        _run("2026-09-29", "brak pliku"),  # przed oknem (a) — nie liczy się
        _run("2026-09-30", "BŁĄD RuntimeError"),
        _run("2026-10-01", "", 2),  # „carry zmiany” to (c), nie (a)
        _run("2026-10-02", "spóźnione"),
        *[_run(d) for d in _days("2026-10-03", 37)],
    ]
    a = _crit([], rs)["criteria"]["a"]
    assert (a["runs"], a["trouble"]) == (40, 2) and a["status"] == MET  # 2/40 = 5 %
    assert a["last_trouble"] == {"ts": "2026-10-02T02:30+00:00", "what": "spóźnione"}


def test_a_too_early_and_no_data():
    assert _crit([], [_run("2026-09-29")])["criteria"]["a"]["status"] == EARLY
    assert _crit([], [])["criteria"]["a"]["status"] == NO_DATA  # pusty log


# ------------------------------------------------------------------ (b) kompletność


def test_b_false_day_is_listed_and_threshold_inclusive():
    days = _days(sd.CARRY_START, 20)
    rows = [_crow(d, komplet=(i != 5), rozl=(2 if i == 5 else 3)) for i, d in enumerate(days)]
    b = _crit(rows, [_run("2026-10-19")])["criteria"]["b"]
    assert b["status"] == MET and b["share"] == pytest.approx(0.95)  # 19/20 — granica włącznie
    assert b["incomplete"] == [days[5]] and b["settlements"] == {days[5]: 2}
    assert b["to_explain"] == [days[5]]  # próg spełniony, a dzień i tak do wyjaśnienia
    rows[7] = _crow(days[7], komplet=False, rozl=0)  # dzień bez żadnego rozliczenia
    b2 = _crit(rows, [_run("2026-10-19")])["criteria"]["b"]
    assert b2["status"] == UNMET and b2["share"] == pytest.approx(0.90)
    assert b2["settlements"] == {days[5]: 2, days[7]: 0}
    assert _crit(rows[:5], [_run("2026-10-04")])["criteria"]["b"]["to_explain"] == []


def test_b_row_missing_from_file_counts_as_incomplete_day_like_the_page():
    days = _days(sd.CARRY_START, 20)
    rows = [_crow(d) for i, d in enumerate(days) if i != 9]  # dziura w datach
    b = _crit(rows, [_run("2026-10-19")])["criteria"]["b"]
    assert (b["days"], b["n_days"], b["missing"]) == (19, 20, [days[9]])
    assert b["status"] == MET and b["share"] == pytest.approx(0.95)
    assert b["to_explain"] == [days[9]]
    rows[0] = _crow(days[0], komplet=False, rozl=2)
    assert _crit(rows, [_run("2026-10-19")])["criteria"]["b"]["status"] == UNMET  # 18/20


def test_b_render_says_met_without_qualifier_only_when_nothing_to_explain():
    rows = [_crow(d) for d in _days(sd.CARRY_START, 20)]
    car = {**_crit(rows, [_run("2026-10-19")]), "exchange_requested": False, "exchange": None}
    txt = "\n".join(od._render_carry(car))
    assert f"→ {MET}: 20 z 20 dni z kompletem 3 rozliczeń (100.0 %)\n" in txt
    assert "co do progu" not in txt and "wyjaśnić" not in txt


def test_b_too_early_until_first_day_can_close():
    # dzień 29.09 zamyka dopiero przebieg 30.09 (rozliczenie 30.09 00:00 w danych)
    assert _crit([], [_run("2026-09-29")])["criteria"]["b"]["status"] == EARLY
    assert _crit([], [_run("2026-09-30")])["criteria"]["b"]["status"] == NO_DATA
    assert _crit([], [])["criteria"]["b"]["status"] == NO_DATA


# ------------------------------------------------------------------ (c) zgodność z giełdą


@pytest.mark.parametrize(
    "exchange, status",
    [
        (None, UNCHECKED),
        ({"status": NO_DATA}, NO_DATA),
        ({"status": MET}, MET),
        ({"status": UNMET}, UNMET),
    ],
    ids=["bez-flagi", "brak-sieci", "zgodne", "rozne"],
)
def test_c_is_met_only_with_exchange_check(exchange, status):
    rows = [_crow(d) for d in _days(sd.CARRY_START, 3)]
    c = _crit(rows, [_run("2026-10-02")], exchange=exchange)["criteria"]["c"]
    assert c["status"] == status and c["log_ok"] and c["log_runs"] == 0


def test_c_carry_changes_field_in_log_fails_even_when_exchange_matches():
    rows = [_crow(d) for d in _days(sd.CARRY_START, 3)]
    runs = [_run("2026-09-30"), _run("2026-10-01", "", 1), _run("2026-10-02", "spóźnione", 2)]
    c = _crit(rows, runs, exchange={"status": MET})["criteria"]["c"]
    assert c["status"] == UNMET and (c["log_runs"], c["log_max"]) == (2, 2) and not c["log_ok"]


def test_c_without_rows_follows_b():
    assert _crit([], [_run("2026-09-29")])["criteria"]["c"]["status"] == EARLY
    assert _crit([], [_run("2026-10-05")], exchange=None)["criteria"]["c"]["status"] == NO_DATA


def test_unreadable_carry_file_is_no_data_everywhere():
    c = od.carry_criteria({"start": sd.CARRY_START, "error": "KeyError: 'komplet'"}, "2026-10-05")
    assert {k: v["status"] for k, v in c["criteria"].items()} == dict.fromkeys("abc", NO_DATA)
    assert c["result"] is None and c["error"] == "KeyError: 'komplet'"


# ------------------------------------------------------------------ wynik opisowo


def test_result_is_sum_and_same_sum_per_year():
    rows = [_crow(d, cum=0.0003 * (i + 1)) for i, d in enumerate(_days(sd.CARRY_START, 10))]
    res = _crit(rows, [_run("2026-10-09")])["result"]
    # 10 dni kalendarzowych 29.09 → 08.10, netto_skum 0,003 → 0,003 × 365/10 = 0,1095 /rok
    assert res == {
        "first": "2026-09-29",
        "last": "2026-10-08",
        "days": 10,
        "netto_skum": pytest.approx(0.003),
        "annual": pytest.approx(0.1095),
    }
    assert _crit([], [_run("2026-09-29")])["result"] is None


def test_note_when_carry_file_ends_before_r1():
    rows = [_crow(d) for d in _days(sd.CARRY_START, 5)]  # 29.09 → 03.10
    assert _crit(rows, [_run("2026-10-06")], ref_day="2026-10-05")["note"].startswith(
        "plik carry kończy się na 2026-10-03, wynik R1 na 2026-10-05"
    )
    assert _crit(rows, [_run("2026-10-04")], ref_day="2026-10-03")["note"] is None


# ------------------------------------------------------------------ plik vs przeliczenie


def test_compare_identical_rows_and_newer_fresh_days_ignored():
    df = jc.carry_rows(_funding("2026-10-10"), jc.CARRY_START, COST)
    fresh = jc.carry_rows(_funding("2026-10-15"), jc.CARRY_START, COST)  # pobranie później
    cmp = od.compare_carry(_file_rows(df), fresh, jc.CARRY_VALUES)
    assert cmp["diffs"] == {} and cmp["compared"] == len(df) == 11
    assert (cmp["fresh_rows"], cmp["fresh_last"]) == (16, "2026-10-14")


@pytest.mark.parametrize(
    "delta, flagged", [(1e-8, True), (-1e-8, True), (1e-10, False), (-5e-10, False)]
)
def test_compare_tolerance_is_1e9(delta, flagged):
    """Brzeg z zadania: różnica 1e-8 w przeliczeniu = różnica; 1e-10 = zgodne (do 1e-9)."""
    df = jc.carry_rows(_funding("2026-10-10"), jc.CARRY_START, COST)
    rows = _file_rows(df)
    rows[4]["netto_skum"] = repr(float(rows[4]["netto_skum"]) + delta)
    cmp = od.compare_carry(rows, df, jc.CARRY_VALUES)
    assert cmp["diffs"] == ({"2026-10-03": ["netto_skum"]} if flagged else {})


def test_compare_reports_flag_gaps_extra_and_duplicate_days():
    df = jc.carry_rows(_funding("2026-10-10"), jc.CARRY_START, COST)
    rows = _file_rows(df)
    rows[2]["komplet"] = "False"
    rows[2]["rozliczenia"] = "2"
    del rows[5]  # dzień, którego w pliku brak (dziura przed ostatnim dniem pliku)
    rows.append(dict(rows[0]))  # duplikat daty
    rows.append({**rows[1], "date": "2026-09-20"})  # dzień spoza przeliczenia
    cmp = od.compare_carry(rows, df, jc.CARRY_VALUES)
    assert cmp["diffs"] == {
        "2026-09-20": ["brak w przeliczeniu"],
        "2026-09-29": ["duplikat w pliku"],
        "2026-10-01": ["rozliczenia", "komplet"],
        "2026-10-04": ["brak w pliku"],
    }


@settings(max_examples=60, deadline=None)
@given(
    rates=st.lists(st.floats(-1e-3, 1e-3), min_size=4, max_size=30),
    pick=st.integers(0, 10_000),
    col=st.sampled_from(["suma_stawek", "koszt", "netto", "netto_skum"]),
    delta=st.one_of(st.floats(2e-9, 1e-2), st.floats(-1e-2, -2e-9)),
)
def test_compare_detects_any_change_above_tolerance_only(rates, pick, col, delta):
    ts = pd.date_range(sd.CARRY_START, periods=len(rates), freq="8h", tz="UTC")
    df = jc.carry_rows(pd.DataFrame({"timestamp": ts, "funding_rate": rates}), jc.CARRY_START, COST)
    rows = _file_rows(df)
    assert od.compare_carry(rows, df, jc.CARRY_VALUES)["diffs"] == {}
    i = pick % len(rows)
    small = [dict(r) for r in rows]
    small[i][col] = repr(float(rows[i][col]) + 4e-10 * (1 if delta > 0 else -1))
    assert od.compare_carry(small, df, jc.CARRY_VALUES)["diffs"] == {}
    rows[i][col] = repr(float(rows[i][col]) + delta)
    assert od.compare_carry(rows, df, jc.CARRY_VALUES)["diffs"] == {rows[i]["date"]: [col]}


# ------------------------------------------------------------------ krok z siecią (atrapa)


def test_exchange_check_matches_file_and_leaves_nothing(capsys):
    calls: list[Path] = []
    rows = _file_rows(jc.carry_rows(_funding("2026-10-10"), jc.CARRY_START, COST))
    ex = od.exchange_check(rows, _fake_fetch(_funding("2026-10-13"), calls))
    assert ex["status"] == MET and ex["diffs"] == {} and ex["compared"] == 11
    assert ex["switch_cost"] == pytest.approx(0.0019) and ex["fresh_last"] == "2026-10-12"
    assert len(calls) == 1 and not calls[0].exists()  # katalog tymczasowy usunięty
    out = capsys.readouterr()
    assert out.out == "" and "coinm funding BTCUSD_PERP" in out.err  # stdout czysty dla --json


def test_exchange_check_flags_1e8_difference():
    rows = _file_rows(jc.carry_rows(_funding("2026-10-10"), jc.CARRY_START, COST))
    rows[3]["suma_stawek"] = repr(float(rows[3]["suma_stawek"]) + 1e-8)
    ex = od.exchange_check(rows, _fake_fetch(_funding("2026-10-10")))
    assert ex["status"] == UNMET and ex["diffs"] == {"2026-10-02": ["suma_stawek"]}


@pytest.mark.parametrize(
    "funding, why",
    [
        (None, "pobranie nieudane ([live] funding COIN-M BTCUSD_PERP BŁĄD URLError"),
        (_funding("2026-10-10").iloc[:0], "giełda nie zwróciła żadnego rozliczenia od 2026-09-29"),
        (
            _funding("2026-09-29T16:00"),
            "w pobranych danych żaden dzień od startu nie jest zamknięty",
        ),
        (_funding("2026-10-10").rename(columns={"funding_rate": "x"}), "błąd ValueError"),
    ],
    ids=["brak-sieci", "pusta-odpowiedz", "bez-zamknietego-dnia", "zly-format"],
)
def test_exchange_check_without_data_is_no_data_never_match(funding, why):
    rows = [_crow(d) for d in _days(sd.CARRY_START, 3)]
    ex = od.exchange_check(rows, _fake_fetch(funding))
    assert ex["status"] == NO_DATA and ex["why"].startswith(why), ex["why"]
    assert ex["diffs"] == {} and ex["compared"] == 0


def test_exchange_check_without_rows_does_not_fetch():
    ex = od.exchange_check([], _no_fetch)
    assert ex["status"] == NO_DATA and ex["why"] == "brak wierszy w carry_wyniki.csv do porównania"


def _http_records(funding: pd.DataFrame) -> bytes:
    """Odpowiedź `dapi/v1/fundingRate` (lista rekordów) dla ramki rozliczeń."""
    return json.dumps(
        [
            {
                "symbol": "BTCUSD_PERP",
                "fundingTime": int(t.value // 1_000_000),
                "fundingRate": f"{r:.8f}",
                "markPrice": "65000.0",
            }
            for t, r in zip(funding["timestamp"], funding["funding_rate"], strict=True)
        ]
    ).encode()


def test_exchange_check_uses_journal_fetch_function_from_carry_start(monkeypatch):
    """Prawdziwa funkcja dziennika `fetch_coinm_funding_safe`; sieć podmieniona na HTTP."""
    urls: list[str] = []

    def http_get(url: str, **_kw) -> bytes:
        urls.append(url)
        return _http_records(_funding("2026-10-12"))

    monkeypatch.setattr("data.fetch_external.http_get", http_get)
    rows = _file_rows(jc.carry_rows(_funding("2026-10-10"), jc.CARRY_START, COST))
    ex = od.exchange_check(rows)
    assert ex["status"] == MET and ex["compared"] == 11 and ex["fresh_last"] == "2026-10-11"
    start_ms = int(pd.Timestamp(sd.CARRY_START, tz="UTC").value // 1_000_000)
    assert len(urls) == 1 and urls[0].startswith("https://dapi.binance.com/dapi/v1/fundingRate?")
    assert "symbol=BTCUSD_PERP" in urls[0] and f"startTime={start_ms}" in urls[0]

    def offline(url: str, **_kw) -> bytes:
        raise urllib.error.URLError("brak sieci")

    monkeypatch.setattr("data.fetch_external.http_get", offline)
    ex = od.exchange_check(rows)
    assert ex["status"] == NO_DATA and "URLError" in ex["why"]


# ------------------------------------------------------------------ odczyt z repo git


def _with_fields(log: str, fields: dict[str, str]) -> str:
    """Pola carry w liniach przebiegów z dni `fields` (dzień UTC → pola), przed licznikiem."""
    out = []
    for line in log.splitlines():
        if line[:10] in fields:
            line = line.replace(
                " | historia zmieniona", f" | {fields[line[:10]]} | historia zmieniona"
            )
        out.append(line)
    return "\n".join(out) + "\n"


def _carry_repo(
    tmp_path: Path, carry_csv: str | None, fields: dict[str, str] | None = None
) -> Path:
    """Dziennik 92 dni wyniku R1 (24.09 → 24.12, przebieg 25.12), plik carry, pola w logu."""
    files = _journal(92)
    if carry_csv is not None:
        files["carry_wyniki.csv"] = carry_csv
    if fields:
        files["przebiegi.log"] = _with_fields(files["przebiegi.log"], fields)
    repo = _repo(tmp_path, files)
    _git(repo, "commit", "-q", "--amend", "-m", "Dziennik: przebieg 2026-12-25 (host1)")
    _git(repo, "update-ref", "refs/remotes/origin/master", "HEAD")
    return repo


FALSE_DAY = "2026-10-05"  # giełda nie opublikowała rozliczenia 08:00 → komplet = False
FUNDING_1224 = _funding("2026-12-25", drop=(f"{FALSE_DAY}T08:00:00+00:00",))  # 29.09 → 24.12
CARRY_1224 = jc.carry_rows(FUNDING_1224, jc.CARRY_START, COST)


@needs_git
def test_binding_reading_with_carry_file_and_exchange_check(tmp_path):
    repo = _carry_repo(tmp_path, CARRY_1224.to_csv(index=False), {"2026-11-01": "carry spóźnione"})
    rep = od.reading(str(repo), as_of=date(2026, 12, 24))
    assert rep["status"]["binding"] and rep["warnings"] == []
    car = rep["carry"]
    a, b, c = (car["criteria"][k] for k in "abc")
    assert (a["runs"], a["trouble"], a["status"]) == (87, 1, MET)  # przebiegi 30.09 → 25.12
    assert (b["complete"], b["n_days"], b["status"]) == (86, 87, MET)
    assert b["incomplete"] == [FALSE_DAY] and b["settlements"] == {FALSE_DAY: 2}
    assert c["status"] == UNCHECKED and car["exchange"] is None and car["note"] is None
    total = float(CARRY_1224["netto_skum"].iloc[-1])
    assert car["result"]["days"] == 87 and car["result"]["last"] == "2026-12-24"
    assert car["result"]["netto_skum"] == pytest.approx(total, abs=1e-8)
    assert car["result"]["annual"] == pytest.approx(total * 365 / 87, abs=1e-8)
    txt = od.render(rep)
    sec = txt.split("Carry COIN-M (Poprawka 12)", 1)[1]
    for k in "abc":
        assert f"  ({k}) {od.CARRY_CRITERIA[k]}\n" in sec
    assert f"→ {MET}: 1 z 87 przebiegów od 2026-09-30 z kłopotem" in sec
    assert f"→ {MET} co do progu: 86 z 87 dni z kompletem 3 rozliczeń" in sec
    assert f"dni z False: {FALSE_DAY} (2 rozl.) — każdy wyjaśnić w dokumentacji odczytu" in sec
    assert (
        f"→ {UNCHECKED}: pole „carry zmiany” w 0 przebiegach; ponowne pobranie nie uruchomione"
        in sec
    )
    assert od.CARRY_RESULT in sec and od.CARRY_UNMET in sec and "UWAGA" not in txt

    ok = od.reading(
        str(repo),
        as_of=date(2026, 12, 24),
        carry_exchange=True,
        fetch=_fake_fetch(_funding("2026-12-28", drop=(f"{FALSE_DAY}T08:00:00+00:00",))),
    )
    assert ok["carry"]["criteria"]["c"]["status"] == MET
    assert ok["carry"]["exchange"]["compared"] == 87
    assert "przeliczenie z ponownego pobrania = plik do 1e-9 (87 dni" in od.render(ok)


@needs_git
def test_carry_changes_in_log_and_1e8_difference_fail_c(tmp_path):
    df = CARRY_1224.copy()
    df.loc[40, "netto"] += 1e-8  # zapis różni się od przeliczenia o 1e-8
    repo = _carry_repo(tmp_path, df.to_csv(index=False), {"2026-12-20": "carry zmiany 1"})
    rep = od.reading(
        str(repo), as_of=date(2026, 12, 24), carry_exchange=True, fetch=_fake_fetch(FUNDING_1224)
    )
    c, ex = rep["carry"]["criteria"]["c"], rep["carry"]["exchange"]
    assert c["status"] == UNMET and c["log_runs"] == 1
    assert ex["status"] == UNMET and ex["diffs"] == {df.loc[40, "date"]: ["netto"]}
    txt = od.render(rep)
    head = f"→ {UNMET} (błąd mechaniki do wyjaśnienia): pole „carry zmiany” w 1 przebiegu"
    assert f"{head} (najwięcej 1 dzień); przeliczenie ≠ plik w 1 dniu: " in txt
    assert f"w 1 dniu: {df.loc[40, 'date']}: netto\n" in txt


@needs_git
def test_reading_without_carry_file(tmp_path):
    fields = {d: "carry brak pliku" for d in _days("2026-09-29", 88)}  # przebiegi 29.09 → 25.12
    repo = _carry_repo(tmp_path, None, fields)
    rep = od.reading(str(repo), as_of=date(2026, 12, 24), carry_exchange=True, fetch=_no_fetch)
    car = rep["carry"]
    assert {k: v["status"] for k, v in car["criteria"].items()} == {
        "a": UNMET,
        "b": NO_DATA,
        "c": NO_DATA,
    }
    assert (car["criteria"]["a"]["runs"], car["criteria"]["a"]["trouble"]) == (87, 87)
    assert car["result"] is None and car["exchange"] is None  # bez wierszy — bez pobierania
    txt = od.render(rep)
    assert "brak wierszy w carry_wyniki.csv mimo przebiegów po 2026-09-29" in txt
    assert "ponowne pobranie pominięte (brak wierszy w pliku)" in txt
    assert "brak zamkniętego dnia carry w carry_wyniki.csv" in txt


@needs_git
def test_bad_carry_file_is_no_data_and_does_not_block_reading(tmp_path):
    repo = _carry_repo(tmp_path, "date,netto\n2026-09-29,0.1\n")
    rep = od.reading(str(repo), as_of=date(2026, 12, 24), carry_exchange=True, fetch=_no_fetch)
    assert rep["legs"] and rep["carry"]["error"].startswith("KeyError")
    assert {v["status"] for v in rep["carry"]["criteria"].values()} == {NO_DATA}
    assert f"→ {NO_DATA}: nie da się odczytać carry_wyniki.csv (KeyError" in od.render(rep)


@needs_git
def test_preview_before_carry_start_is_too_early(tmp_path):
    rep = od.reading(str(_repo(tmp_path, FILES)))  # dziennik z 26.09: carry jeszcze nie ruszył
    assert {v["status"] for v in rep["carry"]["criteria"].values()} == {EARLY}
    txt = od.render(rep)
    assert (
        "Carry COIN-M (Poprawka 12)" in txt and f"→ {EARLY}: żadnego przebiegu od 2026-09-30" in txt
    )
    assert f"(krok z siecią: {od.CARRY_FLAG})" in txt


@needs_git
def test_main_flag_keeps_json_stdout_clean(tmp_path, capsys, monkeypatch):
    repo = _carry_repo(tmp_path, CARRY_1224.to_csv(index=False))
    monkeypatch.setattr("data.fetch_live.fetch_coinm_funding_safe", _fake_fetch(FUNDING_1224))
    assert od.main(["--repo", str(repo), "--as-of", "2026-12-24", "--json", od.CARRY_FLAG]) == 0
    out = capsys.readouterr()
    rep = json.loads(out.out)  # wydruk pobierania nie trafił do stdout
    assert rep["carry"]["exchange"]["status"] == MET and rep["carry"]["exchange_requested"]
    assert rep["carry"]["thresholds"] == {
        "trouble_max": 0.05,
        "check_from": "2026-09-30",
        "complete_min": 0.95,
        "start": "2026-09-29",
        "tol": 1e-9,
    }
    assert "coinm funding BTCUSD_PERP" in out.err


@needs_git
def test_main_without_flag_never_fetches(tmp_path, capsys, monkeypatch):
    repo = _carry_repo(tmp_path, CARRY_1224.to_csv(index=False))
    monkeypatch.setattr("data.fetch_live.fetch_coinm_funding_safe", _no_fetch)
    assert od.main(["--repo", str(repo), "--as-of", "2026-12-24"]) == 0
    assert f"→ {UNCHECKED}: pole „carry zmiany” w 0 przebiegach" in capsys.readouterr().out


# ------------------------------------------------------------------ umowa z README i dziennikiem


def _readme_block() -> str:
    text = (ROOT / "dziennik" / "README.md").read_text(encoding="utf-8")
    block = text.split("**Kryterium odczytu po ~3 miesiącach**", 1)[1]
    block = block.split("**Ścieżka odwrotu.**", 1)[0]
    return " ".join(block.replace("`", "").replace("**", "").split())


def _pct_readme(s: str) -> float:
    return float(s.replace(",", ".")) / 100


def test_carry_criteria_wording_and_thresholds_match_readme():
    """Brzmienie (a)–(c) w wydruku = README (Poprawka 12), a progi i daty skryptu = progi README."""
    flat = _readme_block()
    for key, text in od.CARRY_CRITERIA.items():
        assert f"({key}) {text}" in flat, key
    assert od.CARRY_RESULT in flat and od.CARRY_UNMET in flat
    a = re.search(
        r"\(a\) terminowość: .*? w ≤ (\d+(?:,\d+)?) % przebiegów od (\d{4}-\d{2}-\d{2})", flat
    )
    b = re.search(
        r"\(b\) kompletność: komplet = True w ≥ (\d+(?:,\d+)?) % dni od (\d{4}-\d{2}-\d{2})", flat
    )
    c = re.search(r"\(c\) .*? pobranie historii od (\d{4}-\d{2}-\d{2}) .*?, do (\de-\d+),", flat)
    assert _pct_readme(a[1]) == pytest.approx(od.CARRY_TROUBLE_MAX) and a[2] == sd.CARRY_CHECK_FROM
    assert _pct_readme(b[1]) == pytest.approx(od.CARRY_COMPLETE_MIN) and b[2] == sd.CARRY_START
    assert c[1] == sd.CARRY_START and float(c[2]) == od.CARRY_TOL
    # kryterium 6 listy odczytu odsyła do tych samych (a)–(c)
    readme = (ROOT / "dziennik" / "README.md").read_text(encoding="utf-8")
    assert "6. **Carry COIN-M (poprawka 12" in readme


def test_carry_constants_match_journal():
    """(c): tolerancja jak porównanie zapisu w dzienniku, start jak pobieranie nogi w dzienniku."""
    from backtest.live_journal import TOL

    assert od.CARRY_TOL == TOL
    assert jc.CARRY_START.date().isoformat() == sd.CARRY_START  # start pobrania w fetch_live
    assert od.CONFIG_PATH.is_file()
