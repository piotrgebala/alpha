"""Testy tools/strona_dziennika.py — dane strony „Dziennik CLAS-5” (rutyna Cowork, 06:30 UTC).

Strażnik: każdy rekord prawdziwego dziennik/przebiegi.log musi się czytać. Zmiana formatu logu
w live_journal bez zmiany LOG_RE daje czerwony test zamiast cichego „nieczytelne N” na stronie
(tak zepsuło się 2026-09-26 po polu „F&G” i 2026-09-27 po polach „transakcje” i „opisy strategii”).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import strona_dziennika as sd

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "dziennik" / "przebiegi.log"
NOW = datetime(2026, 9, 27, 6, 30, tzinfo=timezone.utc)

HEAD = (
    "2026-09-27T02:30:05.328711+00:00 | as_of 2026-09-26 | binance 2026-09-26 | "
    "premia 2026-09-26 | sygnały +147 | wyniki +1 | kapitał 1.0069 | obsunięcie 0.1% | OK"
)
X1 = " | X1 sygnały +70 wyniki +1 kapitał 1.0221 obsunięcie 3.7% OK"
TAIL = " | historia zmieniona: 0"
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="brak gita")


# ------------------------------------------------------------------ parser logu


def test_every_record_of_repo_log_parses():
    if not LOG.exists():
        pytest.skip("brak dziennik/przebiegi.log w tym klonie")
    text = LOG.read_text(encoding="utf-8")
    runs, bad = sd.parse_log(text)
    unread = [r for r in sd.log_records(text) if not sd.LOG_RE.match(r)]
    assert bad == 0, f"LOG_RE nie czyta rekordów przebiegi.log (popraw LOG_RE): {unread[:2]}"
    assert len(runs) == len(sd.log_records(text)) > 0


@pytest.mark.parametrize(
    "line, x1, stan",
    [
        (HEAD + TAIL, "", ""),  # najstarszy format (przed X1)
        (HEAD + X1 + TAIL, "sygnały +70 wyniki +1 kapitał 1.0221 obsunięcie 3.7% OK", ""),
        (
            HEAD + X1 + " | stan rynku +1" + TAIL,
            "sygnały +70 wyniki +1 kapitał 1.0221 obsunięcie 3.7% OK",
            "+1",
        ),  # poprawka 7
        (HEAD + X1 + " | stan rynku +1 | F&G +1" + TAIL, None, "+1"),  # poprawka 8
        (
            HEAD + X1 + " | stan rynku +1 | F&G +1 | transakcje +31 | opisy strategii 4" + TAIL,
            None,
            "+1",
        ),  # poprawki 9 i 10
        (
            HEAD
            + X1
            + " | stan rynku +1 | F&G +1 | transakcje +31 | opisy strategii 4"
            + " | rozbicie +8 | fazy +56 | koszyk +50"
            + TAIL,
            "sygnały +70 wyniki +1 kapitał 1.0221 obsunięcie 3.7% OK",
            "+1",
        ),  # poprawka 11
        (
            HEAD
            + X1
            + " | stan rynku +0 | F&G +0 | transakcje +0 | opisy strategii 4"
            + " | rozbicie BŁĄD ValueError | fazy BŁĄD ValueError | koszyk BŁĄD KeyError"
            + TAIL,
            None,
            "+0",
        ),  # poprawka 11: błąd liczenia nowych plików
        (
            HEAD
            + X1
            + " | stan rynku +0 | F&G +0 | transakcje +0 | opisy strategii 4"
            + " | rozbicie +2 (x1 BŁĄD ValueError) | fazy +14 (x1 BŁĄD ValueError) | koszyk +0"
            + TAIL,
            "sygnały +70 wyniki +1 kapitał 1.0221 obsunięcie 3.7% OK",
            "+0",
        ),  # poprawka 11: błąd jednej składowej (X1), trend i premia zapisane
        (
            HEAD
            + X1
            + " | stan rynku +1 | F&G +1 | transakcje +0 | opisy strategii 5"
            + " | rozbicie +3 | fazy +21 | koszyk +0 | carry spóźnione"
            + TAIL,
            "sygnały +70 wyniki +1 kapitał 1.0221 obsunięcie 3.7% OK",
            "+1",
        ),  # poprawka 12: pole carry TYLKO przy kłopocie (bez kłopotu linia jak w poprawce 11)
        (
            HEAD
            + X1
            + " | stan rynku +1 | F&G +1 | transakcje +0 | opisy strategii 5"
            + " | rozbicie +3 | fazy +21 | koszyk +0 | carry BŁĄD RuntimeError"
            + TAIL,
            None,
            "+1",
        ),  # poprawka 12: błąd nogi carry
        (
            HEAD + X1 + " | stan rynku BŁĄD ValueError | F&G BŁĄD KeyError | nowe pole 7" + TAIL,
            None,
            "BŁĄD ValueError",
        ),  # błędy pól i pole z przyszłości
    ],
    ids=[
        "bez-X1",
        "X1",
        "stan-rynku",
        "F&G",
        "transakcje-opisy",
        "rozbicie-fazy-koszyk",
        "rozbicie-bledy",
        "rozbicie-blad-x1",
        "carry-spoznione",
        "carry-blad",
        "bledy-nowe-pole",
    ],
)
def test_parse_log_reads_every_journal_format(line, x1, stan):
    runs, bad = sd.parse_log(line + "\n")
    assert bad == 0 and len(runs) == 1
    r = runs[0]
    assert (r["as_of"], r["binance"], r["premia"]) == ("2026-09-26",) * 3
    assert (r["sig"], r["res"], r["eq"], r["dd"], r["status"]) == (147, 1, 1.0069, 0.1, "OK")
    assert r["ts"] == "2026-09-27T02:30+00:00" and r["day"] == "2026-09-27"
    assert r["stan"] == stan and r["changed"] == 0
    if x1 is not None:
        assert r["x1"] == x1


def test_parse_log_joins_multiline_error_and_counts_garbage():
    broken = HEAD + " | X1 sygnały +0 wyniki +0 kapitał 1.0000 obsunięcie 0.0% BŁĄD ValueError: a"
    text = "\n".join(
        [
            broken,
            "druga linia komunikatu | stan rynku +0" + TAIL,  # ciąg poprzedniego rekordu
            "",
            "2026-09-28T02:30:00+00:00 | śmieci bez formatu",
            HEAD.replace("2026-09-27T02:30", "2026-09-29T02:30") + TAIL.replace("0", "3"),
        ]
    )
    runs, bad = sd.parse_log(text)
    assert bad == 1  # tylko śmieci; pusta linia się nie liczy
    assert [r["changed"] for r in runs] == [0, 3]
    assert runs[0]["x1"].endswith("BŁĄD ValueError: a druga linia komunikatu")
    assert runs[0]["stan"] == "+0"


def test_parse_log_sorts_by_time_and_rejects_bad_timestamp():
    later = HEAD.replace("2026-09-27T02:30", "2026-09-28T02:30") + TAIL
    bad_ts = "2026-99-99Tzz | as_of" + HEAD.split("| as_of", 1)[1] + TAIL
    runs, bad = sd.parse_log("\n".join([later, HEAD + TAIL, bad_ts]))
    assert [r["day"] for r in runs] == ["2026-09-27", "2026-09-28"]
    assert bad == 1


_FIELD = (
    st.text(
        alphabet=st.sampled_from("abcdefghijklmnoprstuwyzęółśąźżćń0123456789+-&.%: "),
        min_size=1,
        max_size=24,
    )
    .map(str.strip)
    .filter(lambda s: s and not s.startswith("historia zmieniona"))
)


@settings(max_examples=150, deadline=None)
@given(
    as_of=st.dates(min_value=date(2021, 1, 1), max_value=date(2035, 12, 31)),
    n_sig=st.integers(0, 10_000),
    n_res=st.integers(0, 10_000),
    eq=st.floats(0.01, 50.0, allow_nan=False),
    dd=st.floats(0.0, 1.0, allow_nan=False),
    status=st.sampled_from(["OK", "OSTRZEŻENIE", "STOP"]),
    with_x1=st.booleans(),
    stan=st.one_of(st.none(), _FIELD),
    extra=st.lists(_FIELD, max_size=4),
    changed=st.integers(0, 50),
)
def test_parse_log_round_trip_of_journal_line(
    as_of, n_sig, n_res, eq, dd, status, with_x1, stan, extra, changed
):
    """Linia złożona jak w live_journal.run() (pola w tej samej kolejności) czyta się z powrotem."""
    x1 = f"sygnały +{n_sig} wyniki +{n_res} kapitał {eq:.4f} obsunięcie {100 * dd:.1f}% {status}"
    parts = [
        "2026-09-27T02:30:05.100000+00:00",
        f"as_of {as_of}",
        f"binance {as_of}",
        f"premia {as_of}",
        f"sygnały +{n_sig}",
        f"wyniki +{n_res}",
        f"kapitał {eq:.4f}",
        f"obsunięcie {100 * dd:.1f}%",
        status,
    ]
    parts += [f"X1 {x1}"] if with_x1 else []
    parts += [f"stan rynku {stan}"] if stan is not None else []
    parts += extra + [f"historia zmieniona: {changed}"]
    runs, bad = sd.parse_log(" | ".join(parts))
    assert bad == 0 and len(runs) == 1
    r = runs[0]
    assert r["as_of"] == as_of.isoformat() and (r["sig"], r["res"]) == (n_sig, n_res)
    assert r["eq"] == round(float(f"{eq:.4f}"), 6) and r["dd"] == round(float(f"{100 * dd:.1f}"), 2)
    assert r["status"] == status and r["changed"] == changed
    assert r["x1"] == (x1 if with_x1 else "")
    assert r["stan"] == (stan or "")


def test_parse_commits_reads_journal_commits_only():
    text = "\n".join(
        [
            "2026-09-27T04:30:12+02:00|Dziennik: przebieg 2026-09-27 (dantey1)",
            "2026-09-24T09:50:00+00:00|Dziennik: przebieg 2026-09-24",
            "2026-09-24T10:00:00+00:00|Merge: coś innego",
        ]
    )
    assert sd.parse_commits(text) == [
        {"ts": "2026-09-27T02:30+00:00", "date": "2026-09-27", "host": "dantey1"},
        {"ts": "2026-09-24T09:50+00:00", "date": "2026-09-24", "host": ""},
    ]


def test_num_rounds_and_rejects_non_numbers():
    assert sd.num("1.23456789") == 1.234568 and sd.num("0.123456", 2) == 0.12
    assert [sd.num(x) for x in (None, "", "abc", "nan", "inf", "-inf")] == [None] * 6


# ------------------------------------------------------------------ kontrole a–e


def _state(**kw) -> dict:
    s = {
        "expected_as_of": "2026-09-26",
        "log_unparsed": 0,
        "health": {"latest_as_of": "2026-09-26", "hosts_last_day": ["dantey1"]},
        "criteria": {"consistency": {"after_first_result": 0}},
        "r1": {"equity": [1.0, 1.0069], "drawdown": [0.0, 0.00137]},
        "x1": {"drawdown": [0.0, 0.036673]},
    }
    for path, value in kw.items():
        node = s
        *head, last = path.split("__")
        for key in head:
            node = node[key]
        node[last] = value
    return s


def test_checks_pass_on_healthy_state():
    s = _state()
    assert sd.checks(s) == []
    assert sd.verdict_line(s, []) == "Dziennik odświeżony: dane za 2026-09-26, kapitał R1 1.0069."


@pytest.mark.parametrize(
    "kw, prefix",
    [
        (
            {"health__latest_as_of": "2026-09-25"},
            "(a) dane za 2026-09-25, oczekiwane za 2026-09-26",
        ),
        ({"criteria__consistency__after_first_result": 2}, "(b)"),
        ({"r1__drawdown": [0.0, 0.19]}, "(c) obsunięcie R1 19.0 %"),
        ({"r1__drawdown": []}, "(c) brak obsunięcia R1"),
        ({"x1__drawdown": [0.6]}, "(c) obsunięcie X1 60.0 %"),
        ({"health__hosts_last_day": ["a", "b"]}, "(d)"),
        ({"log_unparsed": 3}, "(e) nieczytelne linie przebiegi.log: 3"),
    ],
)
def test_checks_name_the_failing_point(kw, prefix):
    s = _state(**kw)
    probs = sd.checks(s)
    assert len(probs) == 1 and probs[0].startswith(prefix)
    assert sd.verdict_line(s, probs).startswith("UWAGA: " + prefix)


def test_verdict_line_without_equity_does_not_crash():
    assert sd.verdict_line(_state(r1__equity=[None]), []).endswith("kapitał R1 brak.")


def test_checks_skip_x1_when_absent_and_warn_exactly_at_threshold():
    assert sd.checks(_state(x1=None)) == []
    probs = sd.checks(_state(r1__drawdown=[sd.TH["r1"]["warn"]]))
    assert len(probs) == 1 and probs[0].startswith("(c) obsunięcie R1")


# ------------------------------------------------------------------ stan z repo git


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True,
        capture_output=True,
    )


def _repo(tmp_path: Path, files: dict[str, str], ref: bool = True) -> Path:
    repo = tmp_path / "alpha"
    (repo / "dziennik").mkdir(parents=True)
    for name, body in files.items():
        (repo / "dziennik" / name).write_text(body, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Dziennik: przebieg 2026-09-26 (host1)")
    if ref:
        _git(repo, "update-ref", "refs/remotes/origin/master", "HEAD")
    return repo


FILES = {
    "wyniki.csv": "date,equity,drawdown,r_port,r_trend,r_coinbase,k_trend,k_coinbase\n"
    "2026-09-25,1.0010,0.0,0.001,0.002,0.0,1.5,0.5\n"
    "2026-09-26,1.0025,0.0,0.0015,0.001,0.0005,1.6,0.4\n",
    "x1_wyniki.csv": "date,equity,drawdown,r_x1\n2026-09-26,0.98,0.02,-0.02\n",
    "sygnaly.csv": "as_of,component,symbol,exposure,margin,k,today\n"
    "2026-09-25,trend,BTCUSDT,0.2,0.1,1.5,True\n"
    "2026-09-26,trend,BTCUSDT,0.2,0.1,1.6,False\n"
    "2026-09-26,trend,BTCUSDT,0.1,0.05,1.6,True\n"
    "2026-09-26,trend,ETHUSDT,-0.3,0.15,1.6,True\n"
    "2026-09-26,coinbase,BTCUSDT,0.6,0.2,0.4,True\n",
    "x1_sygnaly.csv": "as_of,symbol,weight\n2026-09-26,SOLUSDT,0.1\n2026-09-26,XRPUSDT,-0.1\n",
    "stan_rynku.csv": "date,btc_vol30,vol_stan,btc_r90,trend90\n2026-09-26,0.35,średnia,0.1,1\n",
    "przebiegi.log": HEAD.replace("2026-09-27T02:30", "2026-09-26T02:30").replace("+1 |", "+0 |", 1)
    + TAIL
    + "\n"
    + HEAD
    + X1
    + " | stan rynku +1 | F&G +1"
    + TAIL
    + "\n",
}


@needs_git
def test_build_state_from_git_repo(tmp_path):
    state, n_runs = sd.build_state(str(_repo(tmp_path, FILES)), NOW)
    assert n_runs == 2 and state["log_unparsed"] == 0
    assert (
        state["expected_as_of"] == "2026-09-26"
        and state["generated_at"] == "2026-09-27T06:30+00:00"
    )
    assert state["health"]["latest_as_of"] == "2026-09-26"
    assert state["health"]["hosts_last_day"] == ["host1"]
    assert state["health"]["last_journal_date"] == "2026-09-26"
    assert state["r1"]["equity"] == [1.001, 1.0025] and state["r1"]["k_cb"] == [0.5, 0.4]
    assert state["x1"]["r"] == [-0.02]
    assert state["daily"]["as_of"] == ["2026-09-25", "2026-09-26"]
    # 26.09: trend netto BTC 0,3, ETH −0,3 → depozyt (0,3 + 0,3)/2 + premia 0,6/3 = 0,5
    assert state["daily"]["margin_net"][-1] == 0.5 and state["daily"]["trend_net"][-1] == 0.0
    pos = state["positions"]
    assert pos["for_day"] == "2026-09-27" and pos["k"] == {"trend": 1.6, "coinbase": 0.4}
    assert (pos["trend"]["long"], pos["trend"]["short"]) == (1, 1)
    assert pos["cb"] == {"exposure": 0.6, "margin": 0.2, "symbol": "BTCUSDT"}
    assert [o["sym"] for o in pos["orders"]] == ["BTCUSDT", "ETHUSDT", "BTCUSDT"]
    assert pos["x1"] == {"long": [["SOLUSDT", 0.1]], "short": [["XRPUSDT", -0.1]]}
    assert state["market"]["stan"] == ["średnia"]
    # oczekiwane as_of od 23.09 (dzień przed startem R1) do 26.09; brak 23 i 24
    assert state["criteria"]["completeness"] == {
        "days": 4,
        "covered": 2,
        "missing": ["2026-09-23", "2026-09-24"],
    }
    assert state["criteria"]["consistency"] == {"events": 0, "after_first_result": 0}
    assert sd.checks(state) == []
    assert sd.build_state(str(_repo(tmp_path / "b", FILES)), NOW)[0]["r1"] == state["r1"]


@needs_git
def test_history_change_after_first_result_is_flagged(tmp_path):
    files = dict(FILES)
    files["przebiegi.log"] = FILES["przebiegi.log"] + (
        HEAD.replace("2026-09-27T02:30", "2026-09-27T03:00") + " | historia zmieniona: 2\n"
    )
    state, _ = sd.build_state(str(_repo(tmp_path, files)), NOW)
    assert state["criteria"]["consistency"] == {"events": 1, "after_first_result": 1}
    assert sd.checks(state)[0].startswith("(b) historia zmieniona po pierwszym wyniku: 1")


@needs_git
def test_history_change_before_any_result_is_not_counted(tmp_path):
    """Bez żadnego wyniku (same „wyniki +0”) zdarzenie jest sprzed pierwszego wyniku."""
    files = dict(FILES)
    files["przebiegi.log"] = HEAD.replace("wyniki +1", "wyniki +0") + " | historia zmieniona: 3\n"
    state, _ = sd.build_state(str(_repo(tmp_path, files)), NOW)
    assert state["criteria"]["consistency"] == {"events": 1, "after_first_result": 0}
    assert state["health"]["history_events"][0]["before_first_result"] is True


@needs_git
def test_main_writes_json_and_verdict(tmp_path, capsys):
    out = tmp_path / "stan.json"
    assert sd.main([str(_repo(tmp_path, FILES)), str(out)]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].startswith(f"OK {out}: {out.stat().st_size} B")
    assert lines[-1].startswith(("Dziennik odświeżony:", "UWAGA:"))
    assert json.loads(out.read_text(encoding="utf-8"))["v"] == 1


@needs_git
@pytest.mark.parametrize("drop", ["wyniki.csv", "sygnaly.csv", "przebiegi.log"])
def test_main_refuses_empty_state(tmp_path, capsys, drop):
    files = {k: v for k, v in FILES.items() if k != drop}
    out = tmp_path / "stan.json"
    assert sd.main([str(_repo(tmp_path, files)), str(out)]) == 1
    assert "pusty stan dziennika" in capsys.readouterr().err
    assert not out.exists()


@needs_git
def test_main_fails_without_origin_master(tmp_path, capsys):
    out = tmp_path / "stan.json"
    assert sd.main([str(_repo(tmp_path, FILES, ref=False)), str(out)]) == 1
    assert "BŁĄD: RuntimeError" in capsys.readouterr().err and not out.exists()


def test_main_usage_error():
    assert sd.main([]) == 2
