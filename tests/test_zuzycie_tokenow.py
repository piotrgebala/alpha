"""Testy tools/zuzycie_tokenow.py — monitor zużycia tokenów (syntetyczne zapisy JSONL, bez sieci)."""

from __future__ import annotations

import collections
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import straznik_kontekstu as sk
from tools import zuzycie_tokenow as zt

TERAZ = datetime(
    2026, 9, 29, tzinfo=timezone.utc
)  # „teraz” symulacji: wszystkie sesje testowe zakończone


def _asst(mid, ts, inp=0, cw1h=0, cw5=0, cr=0, out=0, content=None):
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "id": mid,
            "content": content or [],
            "usage": {
                "input_tokens": inp,
                "cache_creation_input_tokens": cw1h + cw5,
                "cache_read_input_tokens": cr,
                "output_tokens": out,
                "cache_creation": {
                    "ephemeral_1h_input_tokens": cw1h,
                    "ephemeral_5m_input_tokens": cw5,
                },
            },
        },
    }


def _write(path: Path, recs) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8"
    )
    return path


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "proj"
    main = [
        # jedna odpowiedź w dwóch rekordach: pierwszy z niepełnym wyjściem (1), drugi pełny (100)
        _asst("m1", "2026-09-27T10:00:00Z", inp=2, cw1h=1000, cr=5000, out=1),
        _asst(
            "m1",
            "2026-09-27T10:00:01Z",
            inp=2,
            cw1h=1000,
            cr=5000,
            out=100,
            content=[
                {"type": "tool_use", "id": "t1", "name": "Skill", "input": {"skill": "clas5-quant"}}
            ],
        ),
        {
            "type": "user",
            "timestamp": "2026-09-27T10:00:02Z",
            "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]},
        },
        {
            "type": "user",
            "timestamp": "2026-09-27T10:00:03Z",
            "message": {"content": "Base directory for this skill: /x\n" + "a" * 100},
        },
        # przepisanie po przerwie: duży zapis, mały odczyt
        _asst("m2", "2026-09-28T06:00:00Z", inp=1, cw1h=600_000, cr=25_000, out=50),
        {
            "type": "attachment",
            "timestamp": "2026-09-28T06:00:01Z",
            "attachment": {"type": "prompt_snapshot", "x": "y" * 999},
        },
        {
            "type": "attachment",
            "timestamp": "2026-09-28T06:00:02Z",
            "attachment": {"type": "skill_listing", "x": "z"},
        },
        "to nie jest obiekt",
    ]
    p = _write(r / "sesja.jsonl", main)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("{uszkodzona linia\n")
    _write(
        r / "sesja" / "subagents" / "agent-a.jsonl",
        [_asst("s1", "2026-09-27T11:00:00Z", cw5=400, out=10)],
    )
    _write(
        r / "sesja" / "subagents" / "workflows" / "wf_1" / "agent-b.jsonl",
        [_asst("w1", "2026-09-27T12:00:00Z", cw1h=2000, cr=10_000, out=20)],
    )
    _write(r / "memory" / "x.jsonl", [_asst("mem", "2026-09-27T12:00:00Z", out=10**9)])
    return r


def test_source_classification(root):
    assert zt.source_of(root / "sesja.jsonl", root) == zt.MAIN
    assert zt.source_of(root / "sesja/subagents/agent-a.jsonl", root) == zt.SUB
    assert (
        zt.source_of(root / "sesja/subagents/workflows/wf_1/agent-b.jsonl", root) == "workflow:wf_1"
    )


def test_records_of_one_message_are_merged_with_max(root):
    scan = zt.scan_project(root)
    m1 = [c for c in scan.calls if c.ts.startswith("2026-09-27T10")]
    assert len(m1) == 1 and m1[0].counts["out"] == 100 and m1[0].counts["cw1h"] == 1000


def test_cost_weights_and_totals(root):
    s = zt.summarize(zt.scan_project(root))
    m1 = 2 * 1 + 1000 * 2 + 5000 * 0.1 + 100 * 5
    m2 = 1 + 600_000 * 2 + 25_000 * 0.1 + 50 * 5
    s1 = 400 * 1.25 + 10 * 5
    w1 = 2000 * 2 + 10_000 * 0.1 + 20 * 5
    assert s["razem_koszt"] == pytest.approx(m1 + m2 + s1 + w1)
    assert s["razem_wywolan"] == 4  # katalog memory pominięty
    groups = {(r["dzien"], r["zrodlo"]) for r in s["dni"]}
    assert groups == {
        ("2026-09-27", "główna sesja"),
        ("2026-09-27", "subagent"),
        ("2026-09-27", "workflow"),
        ("2026-09-28", "główna sesja"),
    }
    assert s["zrodla"][0]["zrodlo"] == "główna sesja"


def test_rewrite_detection(root):
    s = zt.summarize(zt.scan_project(root))
    assert [r["zapis"] for r in s["przepisania"]] == [600_000]
    border = zt.Call(
        "d",
        zt.MAIN,
        "t",
        zt._usage_counts(
            {"cache_creation_input_tokens": 200_000, "cache_read_input_tokens": 49_999}
        ),
    )
    assert border.is_rewrite
    warm = zt.Call(
        "d",
        zt.MAIN,
        "t",
        zt._usage_counts(
            {"cache_creation_input_tokens": 300_000, "cache_read_input_tokens": 50_000}
        ),
    )
    assert not warm.is_rewrite


def test_skills_content_and_bad_lines(root):
    s = zt.summarize(zt.scan_project(root))
    assert s["skille"] == {"clas5-quant": 1}
    ct = s["tresc_glownej_sesji_znaki"]
    assert ct["skille"] > 100 and "przypomnienia i załączniki" in ct
    assert ct["przypomnienia i załączniki"] < 999  # prompt_snapshot nie liczy się jako treść
    assert s["zle_linie"] == 2


def test_since_filter(root):
    s = zt.summarize(zt.scan_project(root, since="2026-09-28"))
    assert s["razem_wywolan"] == 1 and s["dni"][0]["dzien"] == "2026-09-28"


def test_old_usage_without_ttl_split_counts_as_5m():
    c = zt._usage_counts({"input_tokens": 1, "cache_creation_input_tokens": 80, "output_tokens": 2})
    assert c["cw5"] == 80 and c["cw1h"] == 0 and zt.cost(c) == pytest.approx(1 + 100 + 10)


def test_project_dir_slug(tmp_path):
    assert (
        zt.project_dir("/home/dantey1/alpha", home=tmp_path)
        == tmp_path / ".claude/projects/-home-dantey1-alpha"
    )


def test_main_report_json_and_errors(root, capsys, tmp_path):
    assert zt.main(["--katalog", str(root)]) == 0
    txt = capsys.readouterr().out
    assert (
        "ZUŻYCIE TOKENÓW" in txt
        and "Przepisania całego kontekstu" in txt
        and "clas5-quant ×1" in txt
    )
    assert zt.main(["--katalog", str(root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["razem_wywolan"] == 4
    assert zt.main(["--katalog", str(tmp_path / "brak")]) == 1
    assert zt.main(["--katalog", str(root), "--od", "wczoraj"]) == 2
    assert zt.summarize(zt.scan_project(tmp_path / "brak"))["razem_wywolan"] == 0


@settings(max_examples=100, deadline=None)
@given(
    parts=st.lists(
        st.tuples(*(st.integers(0, 10**6) for _ in range(5))),
        min_size=1,
        max_size=4,
    )
)
def test_merge_is_max_and_order_independent(tmp_path_factory, parts):
    """Scalanie rekordów jednej wiadomości = maksimum każdego licznika, niezależnie od kolejności."""
    d = tmp_path_factory.mktemp("h")
    recs = [
        _asst("m", "2026-09-27T00:00:00Z", inp=a, cw1h=b, cw5=c, cr=e, out=f)
        for a, b, c, e, f in parts
    ]
    for order in (recs, list(reversed(recs))):
        _write(d / "s.jsonl", order)
        scan = zt.scan_project(d)
        assert len(scan.calls) == 1
        got = scan.calls[0].counts
        for i, k in enumerate(("inp", "cw1h", "cw5", "cr", "out")):
            assert got[k] == max(p[i] for p in parts)


def test_cost_split_by_model(tmp_path):
    """Podział na modele: ten sam koszt jednostkowy, osobne wiersze; brak pola model → „?”."""
    rec_opus = _asst("a", "2026-09-28T00:00:00Z", cw1h=1000, out=10)
    rec_opus["message"]["model"] = "claude-opus-5-5"
    rec_haiku = _asst("b", "2026-09-28T00:00:01Z", cw1h=1000, out=10)
    rec_haiku["message"]["model"] = "claude-haiku-4-5-20251001"
    _write(tmp_path / "s.jsonl", [rec_opus, rec_haiku, _asst("c", "2026-09-28T00:00:02Z", out=1)])
    s = zt.summarize(zt.scan_project(tmp_path))
    by = {r["model"]: r for r in s["modele"]}
    assert set(by) == {"claude-opus-5-5", "claude-haiku-4-5-20251001", "?"}
    assert by["claude-opus-5-5"]["koszt"] == by["claude-haiku-4-5-20251001"]["koszt"] == 2050
    assert sum(r["koszt"] for r in s["modele"]) == pytest.approx(s["razem_koszt"])
    # USD po cenie modelu: Opus 1000·8 + 10·20, Haiku 1000·2 + 10·5 (USD za mln); „?” — bez ceny
    assert by["claude-opus-5-5"]["usd"] == pytest.approx(0.0082)
    assert by["claude-haiku-4-5-20251001"]["usd"] == pytest.approx(0.00205)
    assert by["?"]["usd"] is None and s["bez_ceny"] == {"wywolan": 1, "modele": ["?"]}
    assert s["razem_usd"] == pytest.approx(0.0082 + 0.00205)
    txt = zt.report(s)
    assert "Modele (USD" in txt and "USD nieznany — brak w cenniku" in txt
    assert "UWAGA: 1 wywołań modeli spoza cennika (?)" in txt


def test_day_rows_models_sources_context_sessions(root):
    """Wiersze strony: koszt i liczniki per model i źródło, kontekst, przepisania i sesje głównej sesji."""
    rows = zt.day_rows(zt.scan_project(root))
    assert sorted(rows) == ["2026-09-27", "2026-09-28"]
    d1, d2 = rows["2026-09-27"], rows["2026-09-28"]
    # główna 2 + 2·1000 + 0,1·5000 + 5·100 = 3002; subagent 1,25·400 + 5·10 = 550;
    # workflow 2·2000 + 0,1·10 000 + 5·20 = 5100; plik z memory/ poza liczeniem
    assert d1["z"] == {"main": [3002, 1], "sub": [550, 1], "wf": [5100, 1]}
    assert d1["m"] == {"?": [8652, 3, 2, 3400, 15_000, 130]}
    assert d1["ctx"] == [6002, 6002] and d1["prz"] == [0, 0] and d1["ses"] == 1
    assert d2["prz"] == [1, 1_202_751] and d2["ctx"] == [625_001, 625_001]
    # nowe klucze USD: rekordy bez pola model = „?” = koszt nieznany (null), nigdy po cichu 0
    assert d1["usd"] == {"?": None} and d1["usd_z"] == {"main": 0.0, "sub": 0.0, "wf": 0.0}


def test_day_rows_skip_synthetic_and_count_sessions(tmp_path):
    """Wpisy <synthetic> nie są wywołaniami modelu; sesje = osobne pliki głównej sesji danego dnia."""
    recs = [_asst(i, f"2026-09-28T0{i}:00:00Z", cw1h=10) for i in "123"]
    for r, model in zip(recs, ("claude-opus-5-5", zt.SYNTHETIC, "claude-opus-5-5"), strict=True):
        r["message"]["model"] = model
    _write(tmp_path / "s1.jsonl", recs[:2])
    _write(tmp_path / "s2.jsonl", recs[2:])
    r = zt.day_rows(zt.scan_project(tmp_path))["2026-09-28"]
    assert list(r["m"]) == ["claude-opus-5-5"] and r["m"]["claude-opus-5-5"][1] == 2
    assert r["ses"] == 2


def test_merge_days_freezes_old_days():
    """Dzień sprzed okna przeliczania zostaje z historii; nowszy i nieznany historii — ze skanu."""
    old = [{"d": "2026-09-01", "v": "hist"}, {"d": "2026-09-20", "v": "hist"}]
    new = {d: {"d": d, "v": "skan"} for d in ("2026-08-30", "2026-09-01", "2026-09-20")}
    got = zt.merge_days(old, new, "2026-09-28")
    assert [(r["d"], r["v"]) for r in got] == [
        ("2026-08-30", "skan"),
        ("2026-09-01", "hist"),
        ("2026-09-20", "skan"),
    ]


@settings(max_examples=100, deadline=None)
@given(old_k=st.sets(st.integers(0, 60)), new_k=st.sets(st.integers(0, 60)))
def test_merge_days_property(old_k, new_k):
    """Wynik: dni posortowane i unikalne, suma obu zbiorów; skan wygrywa tylko w oknie przeliczania."""
    today = date(2026, 9, 28)

    def iso(k):
        return (today - timedelta(days=k)).isoformat()

    old = [{"d": iso(k), "src": "hist"} for k in sorted(old_k, reverse=True)]
    new = {iso(k): {"d": iso(k), "src": "skan"} for k in new_k}
    got = zt.merge_days(old, new, today.isoformat())
    ds = [r["d"] for r in got]
    assert ds == sorted(set(ds)) and set(ds) == {iso(k) for k in old_k | new_k}
    for r in got:
        k = (today - date.fromisoformat(r["d"])).days
        from_scan = k in new_k and (k <= zt.FREEZE_DAYS or k not in old_k)
        assert r["src"] == ("skan" if from_scan else "hist")


def test_write_state_history_trim_and_errors(root, tmp_path):
    """Plik stanu = historia: stary dzień przeżywa kolejny zapis, limit ucina najstarsze, zapis atomowy."""
    path = tmp_path / "t" / "stan.json"
    now = datetime(2026, 9, 28, 5, 0, tzinfo=timezone.utc)
    st1 = zt.write_state(path, zt.scan_project(root), now)
    assert [r["d"] for r in st1["dni"]] == ["2026-09-27", "2026-09-28"]
    assert st1["wygenerowano"] == "2026-09-28T05:00:00Z" and not list(path.parent.glob("*.tmp"))
    hist = json.loads(path.read_text(encoding="utf-8"))
    hist["dni"].insert(0, {"d": "2026-08-01", "m": {}, "z": {}, "ctx": [0, 0], "prz": [0, 0]})
    path.write_text(json.dumps(hist), encoding="utf-8")
    st2 = zt.write_state(path, zt.scan_project(root), now)
    assert [r["d"] for r in st2["dni"]] == ["2026-08-01", "2026-09-27", "2026-09-28"]
    st3 = zt.write_state(path, zt.scan_project(root), now, limit=1)
    assert [r["d"] for r in st3["dni"]] == ["2026-09-28"]
    path.write_text("{uszkodzony", encoding="utf-8")
    with pytest.raises(ValueError):
        zt.write_state(path, zt.scan_project(root), now)


def test_main_stan(root, tmp_path, capsys):
    """--stan zapisuje dokument strony; zły plik historii = kod 1 (nie cichy reset historii)."""
    path = tmp_path / "stan.json"
    assert zt.main(["--katalog", str(root), "--stan", str(path)]) == 0
    assert "stan strony: dni 2" in capsys.readouterr().out
    assert json.loads(path.read_text(encoding="utf-8"))["kolumny_modelu"] == zt.MODEL_COLS
    path.write_text("[]", encoding="utf-8")
    assert zt.main(["--katalog", str(root), "--stan", str(path)]) == 1


# --- symulacja progów strażnika kontekstu (--progi) ---


def _call(ts, cr=0, cw5=0, cw1h=0, inp=0, source=zt.MAIN, model="claude-opus-5-5", session="s"):
    """Wywołanie modelu zbudowane wprost (bez zapisu JSONL); kontekst = inp + cw5 + cw1h + cr."""
    counts = collections.Counter(inp=inp, cw5=cw5, cw1h=cw1h, cr=cr, out=0)
    return zt.Call(ts[:10], source, ts, counts, model, session)


def _sesja(konteksty, session="s", godzina=0):
    """Sesja z samych odczytów cache: kontekst i-tego wywołania = konteksty[i]."""
    return [
        _call(f"2026-09-28T{godzina:02d}:{i // 60:02d}:{i % 60:02d}Z", cr=k, session=session)
        for i, k in enumerate(konteksty)
    ]


def _trzy_sesje():
    """R = mediana(60, 80, 70 tys.) = 70 tys.; K = mediana(42, 44, 43 tys.) = 43 tys.;
    koszty 88, 124 i 388 tys. — najdroższa jest C."""
    a = _sesja([40_000] * 9 + [60_000, 200_000, 260_000], session="A", godzina=0)
    b = _sesja(
        [40_000] * 9 + [80_000, 100_000, 160_000, 170_000, 180_000, 190_000],
        session="B",
        godzina=1,
    )
    c = _sesja(
        [40_000] * 9 + [70_000] + [300_000 + 10_000 * j for j in range(10)],
        session="C",
        godzina=2,
    )
    return a, b, c


def test_sesje_glowne_tylko_glowna_sesja_posortowana():
    """Subagent, workflow i wpisy <synthetic> odpadają, wywołania idą po czasie, krótkie sesje
    odpadają, sesje od najwcześniej zaczętej."""
    a = _sesja([1_000 * i for i in range(13)], session="a", godzina=1)
    b = _sesja([10] * 5, session="b", godzina=0)
    obce = [
        _call("2026-09-28T01:00:30Z", cr=5, source=zt.SUB, session="a"),
        _call("2026-09-28T01:00:31Z", cr=5, source="workflow:wf_1", session="a"),
        _call("2026-09-28T01:00:32Z", model=zt.SYNTHETIC, session="a"),
    ]
    scan = zt.Scan(calls=a[1::2] + obce + b + a[::2])  # kolejność zapisu ≠ kolejność czasu
    assert zt.sesje_glowne(scan) == [a]
    assert [cs[0].session for cs in zt.sesje_glowne(scan, min_wywolan=5)] == ["b", "a"]


def test_parametry_nowej_sesji_mediana_n_tego_wywolania():
    """R = mediana kontekstu n-tego wywołania, K = mediana kosztu n pierwszych; krótsze sesje
    pomijane; bez żadnej sesji albo przy n < 1 — ValueError."""
    sesje = [
        _sesja([1_000, 2_000, 30_000]),
        _sesja([1_000, 2_000, 50_000, 70_000]),
        _sesja([5_000, 5_000, 90_000, 1_000, 1_000]),
        _sesja([1_000, 2_000]),  # za krótka na n = 3
    ]
    par = zt.parametry_nowej_sesji(sesje, n=3, jednostki=True)
    assert (par["n"], par["sesji"]) == (3, 3)
    assert (par["R"], par["R_min"], par["R_max"]) == (50_000, 30_000, 90_000)
    # sam odczyt cache: koszt = 0,1 · suma kontekstów trzech pierwszych wywołań
    assert par["K"] == pytest.approx(5_300)
    assert (par["K_min"], par["K_max"]) == pytest.approx((3_300, 10_000))
    # w USD (domyślnie): odczyt Opusa 0,20 USD za mln = jednostki × 2e-6; R bez zmian
    usd = zt.parametry_nowej_sesji(sesje, n=3)
    assert usd["R"] == par["R"] and usd["K"] == pytest.approx(5_300 * 2e-6)
    for n in (0, 6):
        with pytest.raises(ValueError):
            zt.parametry_nowej_sesji(sesje, n=n)


def test_symuluj_prog_bardzo_wysoki_prog_nic_nie_zmienia():
    calls = _sesja([50_000 * i for i in range(1, 20)])
    assert zt.symuluj_prog(calls, 10**9, 60_000, 1_000_000) == (0, 0.0)


def _przyklad_reczny():
    return [
        _call("2026-09-28T00:00:01Z", cr=50_000, cw5=10_000),
        _call("2026-09-28T00:00:02Z", cr=60_000, cw5=50_000),
        _call("2026-09-28T00:00:03Z", cr=110_000, cw1h=5_000),
        _call("2026-09-28T00:00:04Z", cr=20_000, cw1h=100_000),
    ]


def test_symuluj_prog_przyklad_policzony_recznie_usd():
    """Ten sam przykład co niżej, w USD po cenach Opusa 5.5 (odczyt 0,20, zapis 5 min 5, zapis 1 h 8
    USD za mln): 0,2·60 + 5·40 = 212 mUSD; 0,2·100 = 20 mUSD; 0,2·20 + 8·80 = 644 mUSD (tys. tokenów
    × USD za mln = mUSD); K = 0,01 USD."""
    clears, saved = zt.symuluj_prog(_przyklad_reczny(), 100_000, 10_000, 0.01)
    assert clears == 1
    assert saved == pytest.approx(0.212 + 0.020 + 0.644 - 0.01)


def test_symuluj_prog_przyklad_policzony_recznie():
    """R = 10 tys., X = 100 tys., K = 5 tys. (dawne jednostki)."""
    calls = [
        _call("2026-09-28T00:00:01Z", cr=50_000, cw5=10_000),  # 60 tys.: poniżej progu
        # 110 tys. > X: czyszczenie, shift = 100 tys. → 0,1·60 tys. + 1,25·40 tys. = 56 tys.
        _call("2026-09-28T00:00:02Z", cr=60_000, cw5=50_000),
        # 115 − 100 = 15 tys. < X; 0,1·min(100, 110) tys. = 10 tys.; zapis poza przesunięciem
        _call("2026-09-28T00:00:03Z", cr=110_000, cw1h=5_000),
        # zapis 1 h (np. po przerwie): 0,1·20 tys. + 2·min(80, 100) tys. = 162 tys.
        _call("2026-09-28T00:00:04Z", cr=20_000, cw1h=100_000),
    ]
    assert calls == _przyklad_reczny()
    clears, saved = zt.symuluj_prog(calls, 100_000, 10_000, 5_000, jednostki=True)
    assert clears == 1
    assert saved == pytest.approx(56_000 + 10_000 + 162_000 - 5_000)


def test_symuluj_prog_spadek_kontekstu_zeruje_przesuniecie():
    """Spadek o ponad 20 tys. = streszczenie: czyszczenie przestaje działać, próg liczy się od nowa.
    Spadek o dokładnie 20 tys. jeszcze nie jest streszczeniem."""
    R, X = 10_000, 100_000
    przed = [
        _call("2026-09-28T00:00:01Z", cr=50_000, cw5=10_000),
        _call("2026-09-28T00:00:02Z", cr=60_000, cw5=50_000),  # czyszczenie: +56 tys.
    ]
    streszczenie = przed + [_call("2026-09-28T00:00:03Z", cr=30_000)]  # 110 → 30 tys.
    assert zt.symuluj_prog(streszczenie, X, R, 0, jednostki=True) == pytest.approx((1, 56_000))
    # po streszczeniu kontekst znów przekracza X: drugie czyszczenie, 0,1·30 + 1,25·70 tys.
    znowu = streszczenie + [_call("2026-09-28T00:00:04Z", cr=30_000, cw5=80_000)]
    assert zt.symuluj_prog(znowu, X, R, 0, jednostki=True) == pytest.approx((2, 56_000 + 90_500))
    granica = przed + [_call("2026-09-28T00:00:03Z", cr=90_000)]  # 110 → 90 tys.
    assert zt.symuluj_prog(granica, X, R, 0, jednostki=True) == pytest.approx((1, 56_000 + 9_000))


@pytest.mark.parametrize("X", [50_000, 49_999, 0])
def test_symuluj_prog_prog_nie_wyzszy_od_R_to_blad(X):
    with pytest.raises(ValueError, match="nie jest większy"):
        zt.symuluj_prog(_sesja([10_000, 60_000]), X, 50_000, 0)


_LICZNIKI = st.lists(
    st.fixed_dictionaries(
        {
            "cr": st.integers(0, 600_000),
            "cw5": st.integers(0, 300_000),
            "cw1h": st.integers(0, 300_000),
            "inp": st.integers(0, 50),
        }
    ),
    min_size=1,
    max_size=30,
)


def _z_licznikow(liczniki):
    return [_call(f"2026-09-28T00:00:{i:02d}Z", **d) for i, d in enumerate(liczniki)]


@settings(max_examples=200, deadline=None)
@given(
    liczniki=_LICZNIKI,
    R=st.integers(0, 200_000),
    dX=st.integers(1, 800_000),
    K=st.floats(0, 5e6),
)
def test_symuluj_prog_dokladnie_liniowy_w_K(liczniki, R, dX, K):
    """Liczba czyszczeń nie zależy od K, a oszczędność(K) = oszczędność(0) − czyszczenia·K."""
    calls = _z_licznikow(liczniki)
    c0, s0 = zt.symuluj_prog(calls, R + dX, R, 0)
    ck, sk_ = zt.symuluj_prog(calls, R + dX, R, K)
    assert ck == c0
    assert sk_ == s0 - c0 * K


@settings(max_examples=200, deadline=None)
@given(liczniki=_LICZNIKI, R=st.integers(0, 200_000), dX=st.integers(1, 800_000))
def test_symuluj_prog_bez_kosztu_startu_nie_traci(liczniki, R, dX):
    """Przy K = 0 czyszczenie tylko skraca kontekst: oszczędność nigdy nie jest ujemna."""
    clears, saved = zt.symuluj_prog(_z_licznikow(liczniki), R + dX, R, 0)
    assert clears >= 0 and saved >= 0


def test_raport_progow_tabele_zwrot_i_szczegoly():
    """Tabele = suma symulacji po sesjach (druga bez najdroższej), zwrot n* i mediana wywołań po
    przekroczeniu, liczby per sesja dla 250 tys.; wywołania subagenta nie wchodzą do sesji."""
    a, b, c = _trzy_sesje()
    subagent = _call("2026-09-28T05:00:00Z", cr=10**6, source=zt.SUB, session="C")
    scan = zt.Scan(calls=c + a + [subagent] + b)
    r = zt.raport_progow(
        scan, progi=(60_000, 150_000, 250_000), mnozniki=(1, 2), teraz=TERAZ, jednostki=True
    )
    assert r["miara"] == "jednostki" and r["sesje_wykluczone"] == []
    R, K = r["parametry"]["R"], r["parametry"]["K"]
    assert R == 70_000 and K == pytest.approx(43_000)
    assert r["sesji"] == 3 and r["progi_pominiete"] == [60_000]
    assert r["najdrozsza_sesja"]["sesja"] == "C"
    assert r["koszt_sesji"] == pytest.approx(88_000 + 124_000 + 388_000)
    assert r["koszt_bez_najdrozszej"] == pytest.approx(88_000 + 124_000)
    for klucz, sesje in (("tabela", (a, b, c)), ("tabela_bez_najdrozszej", (a, b))):
        koszt = sum(zt.cost(x.counts) for cs in sesje for x in cs)
        wiersze = r[klucz]
        assert [(w["prog"], w["mnoznik_K"]) for w in wiersze] == [
            (150_000, 1),
            (150_000, 2),
            (250_000, 1),
            (250_000, 2),
        ]
        for w in wiersze:
            wyniki = [zt.symuluj_prog(cs, w["prog"], R, K * w["mnoznik_K"], True) for cs in sesje]
            assert w["czyszczen"] == sum(n for n, _ in wyniki)
            assert w["oszczednosc"] == pytest.approx(sum(s for _, s in wyniki))
            assert w["oszczednosc_pct"] == pytest.approx(100 * w["oszczednosc"] / koszt)
    # n* = K / (0,1·(X − R)); po przekroczeniu 150 tys. zostało 1 (A), 3 (B) i 9 (C) wywołań,
    # po przekroczeniu 250 tys. — 0 (A) i 9 (C); B nie doszła do 250 tys.
    z150, z250 = r["zwrot"]
    assert z150["n_zwrotu"] == pytest.approx(43_000 / 8_000)
    assert (z150["sesji_ponad_progiem"], z150["mediana_wywolan_po_przekroczeniu"]) == (3, 3)
    assert z250["n_zwrotu"] == pytest.approx(43_000 / 18_000)
    assert (z250["sesji_ponad_progiem"], z250["mediana_wywolan_po_przekroczeniu"]) == (2, 4.5)
    assert r["sesje_przy_progu"]["prog"] == 250_000
    per = {s["sesja"]: s for s in r["sesje_przy_progu"]["sesje"]}
    assert (per["B"]["czyszczen"], per["B"]["oszczednosc"]) == (0, 0)
    assert per["B"]["wywolan_po_przekroczeniu"] is None
    assert (per["C"]["wywolan"], per["C"]["kontekst_max"]) == (20, 390_000)
    assert (per["C"]["czyszczen"], per["C"]["oszczednosc"]) == zt.symuluj_prog(
        c, 250_000, R, K, True
    )
    txt = zt.raport_progow_tekst(r)
    assert "R = 70 tys. tokenów (60–80 tys.)" in txt and "Pominięte progi" in txt
    assert "Bez najdroższej sesji C" in txt and "n* = K / (0,1 · (X − R))" in txt
    assert "K = 0.04 M (0.04–0.04 M)" in txt
    # to samo w USD (domyślnie): same odczyty cache Opusa → każda kwota = jednostki × 2e-6,
    # a procenty, czyszczenia i n* (K i cena odczytu skalują się razem) — bez zmian
    u = zt.raport_progow(scan, progi=(60_000, 150_000, 250_000), mnozniki=(1, 2), teraz=TERAZ)
    assert u["miara"] == "USD" and u["cennik"] == zt.CENNIK_DATA and u["wywolan_bez_ceny"] == 0
    assert u["parametry"]["K"] == pytest.approx(K * 2e-6)
    assert u["koszt_sesji"] == pytest.approx(r["koszt_sesji"] * 2e-6)
    for wu, wj in zip(u["tabela"], r["tabela"], strict=True):
        assert wu["czyszczen"] == wj["czyszczen"]
        assert wu["oszczednosc"] == pytest.approx(wj["oszczednosc"] * 2e-6)
        assert wu["oszczednosc_pct"] == pytest.approx(wj["oszczednosc_pct"])
    for zu, zj in zip(u["zwrot"], r["zwrot"], strict=True):
        assert zu["n_zwrotu"] == pytest.approx(zj["n_zwrotu"])
    assert u["model_ceny_odczytu"] == "claude-opus-5-5" and u["cena_odczytu"] == pytest.approx(2e-7)
    tu = zt.raport_progow_tekst(u)
    assert "Koszt w USD po cenie katalogowej" in tu and "n* = K / (c · (X − R))" in tu
    assert "c = 0,2 USD za mln tokenów — cena odczytu claude-opus-5-5" in tu


def test_raport_progow_skrajne_przypadki():
    """Wszystkie progi ≤ R — puste tabele; jedna sesja — brak tabeli bez najdroższej; brak sesji
    z 12 wywołaniami — ValueError."""
    a, b, c = _trzy_sesje()
    r = zt.raport_progow(zt.Scan(calls=a + b + c), progi=(60_000,), teraz=TERAZ)
    assert r["tabela"] == [] and r["zwrot"] == [] and r["progi_pominiete"] == [60_000]
    assert r["plaski_odcinek"] == {"tol_pkt": zt.PLASKO_PKT, "mnozniki": [], "wspolny": []}
    assert "brak progów do symulacji" in zt.raport_progow_tekst(r)
    jedna = zt.raport_progow(zt.Scan(calls=c), teraz=TERAZ)
    assert jedna["tabela_bez_najdrozszej"] == [] and jedna["koszt_bez_najdrozszej"] == 0
    assert "tylko jedna sesja" in zt.raport_progow_tekst(jedna)
    with pytest.raises(ValueError):
        zt.raport_progow(zt.Scan(calls=a[:11]), teraz=TERAZ)


def test_progi_symulacji_obejmuja_progi_straznika():
    """Domyślne progi symulacji zawierają oba progi strażnika; liczby per sesja — dla progu
    przekazania. Zmiana progu w straznik_kontekstu.py bez zmiany tutaj = czerwony test."""
    assert {sk.PROG_UWAGI, sk.PROG_PRZEKAZANIA} <= set(zt.PROGI_SYMULACJI)
    assert zt.PROG_SZCZEGOLOW == sk.PROG_PRZEKAZANIA


@pytest.fixture
def root_progi(tmp_path):
    """Dwie główne sesje po 14 wywołań (27 i 28 września), kontekst rośnie od 11. wywołania;
    do tego subagent."""
    r = tmp_path / "proj"
    for nr in (1, 2):
        recs = [
            _asst(
                f"m{nr}-{i}",
                f"2026-09-2{6 + nr}T10:{i:02d}:00Z",
                inp=1,
                cw1h=5_000,
                cr=40_000 + (0 if i < 10 else 100_000 * nr * (i - 9)),
                out=100,
            )
            for i in range(14)
        ]
        _write(r / f"sesja{nr}.jsonl", recs)
    _write(
        r / "sesja1" / "subagents" / "agent-a.jsonl",
        [_asst("s1", "2026-09-27T11:00:00Z", cw5=400, out=10)],
    )
    return r


def test_main_progi_tekst_json_od_i_bledy(root_progi, capsys, tmp_path):
    """--progi: raport tekstowy i JSON, --od zawęża sesje, brak sesji = kod 1, --stan się wyklucza."""
    assert zt.main(["--katalog", str(root_progi), "--progi"]) == 0
    txt = capsys.readouterr().out
    assert "SYMULACJA PROGÓW STRAŻNIKA KONTEKSTU" in txt and "Bez najdroższej sesji" in txt
    assert "ZUŻYCIE TOKENÓW" not in txt and "Koszt w USD" in txt
    assert zt.main(["--katalog", str(root_progi), "--progi", "--jednostki"]) == 0
    assert "Koszt w milionach dawnych jednostek" in capsys.readouterr().out
    assert zt.main(["--katalog", str(root_progi), "--jednostki"]) == 2
    assert "--jednostki działa tylko z --progi" in capsys.readouterr().err
    assert zt.main(["--katalog", str(root_progi), "--progi", "--json"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert r["sesji"] == 2 and r["parametry"]["R"] == 45_001
    assert len(r["tabela"]) == len(zt.PROGI_SYMULACJI) * len(zt.MNOZNIKI_K)
    assert zt.main(["--katalog", str(root_progi), "--progi", "--od", "2026-09-28"]) == 0
    assert "tylko jedna sesja" in capsys.readouterr().out
    assert zt.main(["--katalog", str(root_progi), "--progi", "--od", "2099-01-01"]) == 1
    assert "BŁĄD: symulacja progów" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        zt.main(["--katalog", str(root_progi), "--progi", "--stan", str(tmp_path / "s.json")])


# --- koszt według cennika (T8, docs/rag/12) ---


@pytest.mark.parametrize(
    ("inp", "cw1h", "cr", "out", "usd"),
    [
        # trzy przebiegi `claude -p` z T1 (Opus 5.5, total_cost_usd z API)
        (2, 5364, 15874, 4, 0.0461748),
        (2, 3705, 17533, 4, 0.0332346),
        (2, 0, 21238, 4, 0.0043356),
        # sesja weryfikacyjna T8 z zapisem rozmowy (suma modelUsage z JSON `claude -p`)
        (4, 6259, 37201, 508, 0.0676882),
    ],
)
def test_koszt_usd_wektory_z_claude_p(inp, cw1h, cr, out, usd):
    """Wzór cennika odtwarza `total_cost_usd` z API co do cyfry (liczone w całych centach za mln)."""
    c = collections.Counter(inp=inp, cw1h=cw1h, cr=cr, out=out)
    assert zt.koszt_usd(c, "claude-opus-5-5") == usd


def test_koszt_usd_sonnet_z_sesji_weryfikacyjnej():
    """Sesja T8 na Sonnecie 5: API podało 0.051364799999999995 (suma dwóch wywołań w float)."""
    c = collections.Counter(inp=4, cw1h=9374, cr=57104, out=244)
    usd = zt.koszt_usd(c, "claude-sonnet-5")
    assert usd == 0.0513648 and usd == pytest.approx(0.051364799999999995, rel=1e-12)


def test_cennik_dopasowanie_modelu_i_brak_ceny():
    """Dopasowanie po identyfikatorze z sufiksem daty / okna kontekstu; model spoza cennika = None
    (nigdy 0); <synthetic> = 0; odczyt Opusa 5.5 = 0,05 ceny wejścia, Fable 5.1 = 0,025."""
    haiku = zt.CENNIK_USD_ZA_MLN["claude-haiku-4-5"]
    assert zt.cennik_modelu("claude-haiku-4-5-20251001") == zt.cennik_modelu("claude-haiku-4-5")
    assert zt.cennik_modelu("claude-haiku-4-5") == haiku == (1.0, 1.25, 2.0, 0.10, 5.0)
    assert zt.cennik_modelu("claude-opus-5-5[1m]") == zt.CENNIK_USD_ZA_MLN["claude-opus-5-5"]
    for obcy in ("claude-sonnet-5-1", "claude-opus-5", "claude-opus-5-5-fast", "?", ""):
        assert zt.cennik_modelu(obcy) is None
        assert zt.koszt_usd(collections.Counter(out=1), obcy) is None
        assert zt.ceny_tokenu(obcy) is None and zt.ceny_tokenu(obcy, jednostki=True) == zt.WEIGHTS
    assert zt.koszt_usd(collections.Counter(out=10**6), zt.SYNTHETIC) == 0
    op, fa = zt.ceny_tokenu("claude-opus-5-5"), zt.ceny_tokenu("claude-fable-5-1")
    assert op["cr"] / op["inp"] == pytest.approx(0.05) and fa["cr"] / fa["inp"] == pytest.approx(
        0.025
    )
    assert fa["cw1h"] == pytest.approx(20e-6) and op["out"] == pytest.approx(20e-6)
    for inp, cw5, cw1h, _cr, out in zt.CENNIK_USD_ZA_MLN.values():
        assert (cw5, cw1h, out) == (1.25 * inp, 2 * inp, 5 * inp)  # mnożniki cennika
    assert zt.CENNIK_DATA == "2026-09-28" and zt.CENNIK_ZRODLO.endswith("about-claude/pricing")


def _z_modelem(rec, model):
    rec["message"]["model"] = model
    return rec


@pytest.fixture
def root_usd(tmp_path):
    """Główna sesja na Opusie (wektor z claude -p), subagent na Haiku, workflow na modelu spoza
    cennika."""
    r = tmp_path / "proj"
    _write(
        r / "s.jsonl",
        [
            _z_modelem(
                _asst("a", "2026-09-28T00:00:00Z", inp=2, cw1h=5364, cr=15874, out=4),
                "claude-opus-5-5",
            )
        ],
    )
    _write(
        r / "s" / "subagents" / "agent-a.jsonl",
        [
            _z_modelem(
                _asst("b", "2026-09-28T00:01:00Z", cw5=1200, out=100),
                "claude-haiku-4-5-20251001",
            )
        ],
    )
    _write(
        r / "s" / "subagents" / "workflows" / "wf_1" / "agent-c.jsonl",
        [_z_modelem(_asst("c", "2026-09-28T00:02:00Z", cr=1000, out=10), "claude-nowy-9")],
    )
    return r


def test_summarize_usd_per_model_i_zrodlo(root_usd, capsys):
    """USD razem, per model i per źródło obok jednostek; model spoza cennika osobno, z tokenami."""
    s = zt.summarize(zt.scan_project(root_usd))
    opus, haiku = 0.0461748, 0.002  # Haiku: 1200·1,25 + 100·5 = 2000 µUSD
    assert s["razem_usd"] == pytest.approx(opus + haiku)
    assert s["cennik"] == {"data": zt.CENNIK_DATA, "zrodlo": zt.CENNIK_ZRODLO}
    assert s["bez_ceny"] == {"wywolan": 1, "modele": ["claude-nowy-9"]}
    src = {r["zrodlo"]: r for r in s["zrodla"]}
    assert src[zt.MAIN]["usd"] == pytest.approx(opus) and src[zt.SUB]["usd"] == pytest.approx(haiku)
    assert src["workflow:wf_1"]["usd"] == 0 and src["workflow:wf_1"]["wywolan_bez_ceny"] == 1
    assert [r["zrodlo"] for r in s["zrodla"]] == [zt.MAIN, zt.SUB, "workflow:wf_1"]
    mod = {r["model"]: r for r in s["modele"]}
    assert mod["claude-nowy-9"]["usd"] is None and mod["claude-nowy-9"]["odczyt_cache"] == 1000
    assert {r["dzien"]: r["usd"] for r in s["dni"] if r["zrodlo"] == zt.MAIN} == {
        "2026-09-28": pytest.approx(opus)
    }
    txt = zt.report(s)
    assert "Koszt według cennika API z 2026-09-28: 0.05 USD" in txt
    assert "UWAGA: 1 wywołań modeli spoza cennika (claude-nowy-9)" in txt
    assert "USD nieznany — brak w cenniku; wejście 0, zapis cache 0, odczyt cache 1,000" in txt
    assert zt.main(["--katalog", str(root_usd), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["razem_usd"] == pytest.approx(opus + haiku)


def test_day_rows_usd_nowe_klucze_obok_tablic(root_usd):
    """Strona indeksuje tablice `m` (MODEL_COLS) i `z` (koszt, wywołań) — zostają bez zmian; USD to
    nowe klucze obok: `usd` per model (null = bez ceny) i `usd_z` per źródło (zaokrąglone do 0,0001).
    """
    r = zt.day_rows(zt.scan_project(root_usd))["2026-09-28"]
    assert set(r["m"]) == {"claude-opus-5-5", "claude-haiku-4-5-20251001", "claude-nowy-9"}
    assert all(len(v) == len(zt.MODEL_COLS) for v in r["m"].values())
    assert all(len(v) == 2 for v in r["z"].values()) and set(r["z"]) == {"main", "sub", "wf"}
    assert r["usd"] == {
        "claude-opus-5-5": 0.0462,
        "claude-haiku-4-5-20251001": 0.002,
        "claude-nowy-9": None,
    }
    assert r["usd_z"] == {"main": 0.0462, "sub": 0.002, "wf": 0.0}


def test_write_state_usd_zgodny_wstecz(root_usd, tmp_path):
    """`wersja` 1, stare klucze i tablice bez zmian, cennik i USD jako NOWE klucze; zamrożony dzień
    z historii bez kluczy USD przeżywa zapis bez zmian; limit rozmiaru ucina najstarsze dni."""
    path = tmp_path / "stan.json"
    now = datetime(2026, 9, 28, 5, 0, tzinfo=timezone.utc)
    stary = {"d": "2026-08-01", "m": {"claude-opus-5-5": [5, 1, 0, 0, 0, 1]}, "z": {}, "ses": 1}
    stary.update(ctx=[0, 0], prz=[0, 0])
    path.write_text(json.dumps({"wersja": 1, "dni": [stary]}), encoding="utf-8")
    st1 = zt.write_state(path, zt.scan_project(root_usd), now)
    assert st1["wersja"] == 1 and st1["kolumny_modelu"] == zt.MODEL_COLS
    assert st1["kolumny_zrodla"] == ["koszt", "wywolan"]
    assert st1["cennik"]["data"] == zt.CENNIK_DATA
    assert st1["cennik"]["usd_za_mln"]["claude-fable-5-1"] == [10.0, 12.5, 20.0, 0.25, 50.0]
    assert st1["dni"][0] == stary and "usd" not in st1["dni"][0]
    nowy = st1["dni"][1]
    assert nowy["usd"]["claude-opus-5-5"] == 0.0462 and nowy["usd"]["claude-nowy-9"] is None
    assert json.loads(path.read_text(encoding="utf-8")) == st1
    rozmiar = len(json.dumps(st1, ensure_ascii=False).encode())
    st2 = zt.write_state(path, zt.scan_project(root_usd), now, limit=rozmiar - 1)
    assert [r["d"] for r in st2["dni"]] == ["2026-09-28"]


# --- łańcuch rozmowy: poprzednik wywołania (T2, artefakty zapisu) ---


def _rek(uid, parent, typ="user", **kw):
    o = {"type": typ, "uuid": uid, "parentUuid": parent, "timestamp": kw.pop("ts")}
    o.update(kw)
    return o


def _odp(uid, parent, mid, ts, model="claude-opus-5-5", cr=1000):
    o = _asst(mid, ts, cr=cr)
    o.update(uuid=uid, parentUuid=parent)
    o["message"]["model"] = model
    return o


def test_poprzednicy_z_lancucha_parent_uuid(tmp_path):
    """Poprzednik = najbliższe INNE wywołanie w górę po parentUuid (przez wiadomości, wyniki narzędzi,
    kolejne rekordy tej samej odpowiedzi i wpisy <synthetic>); granica streszczenia (parentUuid null)
    = POCZATEK; rodzic spoza pliku albo rekord bez pól łańcucha = nieznany ("")."""
    t = "2026-09-28T00:00:{:02d}Z".format
    recs = [
        _rek("u1", None, ts=t(0)),
        _odp("a1", "u1", "m1", t(1)),
        _rek("t1", "a1", ts=t(2)),
        _odp("a2", "t1", "m2", t(3)),
        _odp("a2b", "a2", "m2", t(4)),  # druga część tej samej odpowiedzi
        _rek("t2", "a2b", ts=t(5)),
        _odp("a3", "t2", "m3", t(6)),
        _rek("t3", "a1", ts=t(7)),  # drugi strumień: odgałęzienie od m1
        _odp("a4", "t3", "m4", t(8)),
        _odp("s1", "a3", "syn", t(9), model=zt.SYNTHETIC),
        _rek("t4", "s1", ts=t(10)),
        _odp("a5", "t4", "m5", t(11)),  # przez wpis <synthetic> do m3
        _rek("cb", None, "system", subtype="compact_boundary", ts=t(12)),
        _rek("su", "cb", ts=t(13)),
        _odp("a6", "su", "m6", t(14)),  # po streszczeniu
        _odp("a7", "nie-ma", "m7", t(15)),  # rodzic spoza pliku
        _asst("m8", t(16), cr=5),  # dawny zapis bez uuid i parentUuid
    ]
    _write(tmp_path / "s.jsonl", recs)
    pop = {c.klucz: c.poprzednik for c in zt.scan_project(tmp_path).calls}
    assert pop == {
        "m1": zt.POCZATEK,
        "m2": "m1",
        "m3": "m2",
        "m4": "m1",
        "syn": "m3",
        "m5": "m3",
        "m6": zt.POCZATEK,
        "m7": "",
        "m8": "",
    }


def _z_lancuchem(calls, poprzednicy):
    """Nadaje wywołaniom klucze k0, k1, … i poprzedników (indeks, POCZATEK albo "")."""
    for i, (c, p) in enumerate(zip(calls, poprzednicy, strict=True)):
        c.klucz = f"k{i}"
        c.poprzednik = p if isinstance(p, str) else f"k{p}"
    return calls


def test_symuluj_prog_drugi_strumien_nie_jest_streszczeniem():
    """Główny strumień k0 → k1 → k3 → k5 i drugi strumień k2 → k4 odgałęziony od k0, przeplecione
    w czasie (R = 10 tys., X = 100 tys., K = 5 tys., jednostki). Po łańcuchu: jedno czyszczenie przy
    k1 (shift 110 tys.), potem k3 i k5 czytają o 110 tys. mniej: 3 × 0,1 × 110 tys. = 33 tys.
    Dawna metoda po czasie: każde przejście na krótszy strumień = „streszczenie” (reset), a powrót
    na dłuższy = nowe czyszczenie: 3 czyszczenia, 0,1 × (110 + 120 + 130) tys. = 36 tys."""
    konteksty = [50_000, 120_000, 60_000, 130_000, 70_000, 140_000]
    calls = _z_lancuchem(_sesja(konteksty), [zt.POCZATEK, 0, 0, 1, 2, 3])
    R, X, K = 10_000, 100_000, 5_000
    assert zt.symuluj_prog(calls, X, R, K, True) == pytest.approx((1, 33_000 - K))
    assert zt.symuluj_prog(calls, X, R, K, True, rozpoznaj_artefakty=False) == pytest.approx(
        (3, 36_000 - 3 * K)
    )
    assert zt.artefakty_sesji(calls) == {
        "rozgalezienia": 1,
        "poza_kolejnoscia": 4,
        "przelaczenia_modelu": 0,
        "poczatki_lancucha": 0,
    }


def test_symuluj_prog_przelaczenie_modelu_nie_jest_streszczeniem():
    """Opus → Fable: kontekst spada 120 → 95 tys. (bloki rozumowania Opusa wypadają), cache zapisuje
    się od nowa (95 tys. zapisu 1 h). Czyszczenie przy 120 tys. działa dalej, shift najwyżej do
    ctx − R = 85 tys. USD, R = 10 tys., X = 100 tys., K = 0:
    Opus 0,2·110 = 22 mUSD; Fable zapis 20·85 = 1700 mUSD; Fable odczyt 0,25·85 = 21,25 mUSD.
    Dawna metoda: spadek = reset, 105 tys. > X — drugie, fałszywe czyszczenie (0,25·95 mUSD)."""
    calls = [
        _call("2026-09-28T00:00:01Z", cr=50_000),
        _call("2026-09-28T00:00:02Z", cr=120_000),
        _call("2026-09-28T00:00:03Z", cw1h=95_000, model="claude-fable-5-1"),
        _call("2026-09-28T00:00:04Z", cr=105_000, model="claude-fable-5-1"),
    ]
    R, X = 10_000, 100_000
    assert zt.symuluj_prog(calls, X, R, 0) == pytest.approx((1, 0.022 + 1.7 + 0.02125))
    assert zt.symuluj_prog(calls, X, R, 0, rozpoznaj_artefakty=False) == pytest.approx(
        (2, 0.022 + 0.02375)
    )
    assert zt.artefakty_sesji(calls)["przelaczenia_modelu"] == 1
    # ten sam spadek przy tym samym modelu = streszczenie: reset i nowe czyszczenie
    for c in calls[2:]:
        c.model = "claude-opus-5-5"
    assert zt.symuluj_prog(calls, X, R, 0)[0] == 2
    assert zt.artefakty_sesji(calls)["przelaczenia_modelu"] == 0


def test_symuluj_prog_poczatek_lancucha_zeruje_przesuniecie():
    """POCZATEK (wznowienie po streszczeniu) zeruje shift także bez dużego spadku kontekstu; wywołanie
    modelu spoza cennika nie wnosi oszczędności w USD (w jednostkach — tak)."""
    calls = _z_lancuchem(_sesja([120_000, 115_000]), [zt.POCZATEK, zt.POCZATEK])
    R, X = 10_000, 100_000
    assert zt.symuluj_prog(calls, X, R, 0)[0] == 2
    assert zt.symuluj_prog(calls, X, R, 0, rozpoznaj_artefakty=False)[0] == 1
    assert zt.artefakty_sesji(calls)["poczatki_lancucha"] == 1
    obcy = _sesja([120_000, 130_000])
    for c in obcy:
        c.model = "claude-nowy-9"
    assert zt.symuluj_prog(obcy, X, R, 0) == (1, 0.0)
    assert zt.symuluj_prog(obcy, X, R, 0, jednostki=True) == pytest.approx((1, 2 * 11_000))


_LANCUCH = st.lists(
    st.fixed_dictionaries(
        {
            "cr": st.integers(0, 600_000),
            "cw5": st.integers(0, 300_000),
            "cw1h": st.integers(0, 300_000),
            "inp": st.integers(0, 50),
            "model": st.sampled_from(
                ["claude-opus-5-5", "claude-fable-5-1", "claude-sonnet-5", "claude-nowy-9"]
            ),
            "pop": st.integers(-2, 40),  # -2 POCZATEK, -1 nieznany, k ≥ 0 — wcześniejsze wywołanie
        }
    ),
    min_size=1,
    max_size=30,
)


@settings(max_examples=200, deadline=None)
@given(elems=_LANCUCH, R=st.integers(0, 200_000), dX=st.integers(1, 800_000), K=st.floats(0, 50))
def test_symuluj_prog_lancuch_liniowy_w_K_i_bez_straty(elems, R, dX, K):
    """Dowolny łańcuch (rozgałęzienia, początki, nieznani poprzednicy) i mieszanka modeli, także
    spoza cennika: liczba czyszczeń nie zależy od K, wynik = oszczędność(0) − czyszczenia·K,
    a przy K = 0 oszczędność nigdy nie jest ujemna — obiema metodami."""
    pops = [
        zt.POCZATEK if d["pop"] == -2 else "" if d["pop"] == -1 or i == 0 else d["pop"] % i
        for i, d in enumerate(elems)
    ]
    calls = [
        _call(
            f"2026-09-28T00:00:{i:02d}Z", d["cr"], d["cw5"], d["cw1h"], d["inp"], model=d["model"]
        )
        for i, d in enumerate(elems)
    ]
    calls = _z_lancuchem(calls, pops)
    for rozp in (True, False):
        c0, s0 = zt.symuluj_prog(calls, R + dX, R, 0, rozpoznaj_artefakty=rozp)
        ck, sk_ = zt.symuluj_prog(calls, R + dX, R, K, rozpoznaj_artefakty=rozp)
        assert ck == c0 and sk_ == s0 - c0 * K and s0 >= 0


@settings(max_examples=200, deadline=None)
@given(liczniki=_LICZNIKI, R=st.integers(0, 200_000), dX=st.integers(1, 800_000))
def test_symuluj_prog_lancuch_bez_rozgalezien_jak_dawna_metoda(liczniki, R, dX):
    """Jeden model i łańcuch bez rozgałęzień (poprzednik = poprzednie wywołanie): rozpoznanie
    artefaktów nic nie zmienia — wynik identyczny z dawną metodą."""
    calls = _z_lancuchem(_z_licznikow(liczniki), [zt.POCZATEK] + list(range(len(liczniki) - 1)))
    for jedn in (True, False):
        assert zt.symuluj_prog(calls, R + dX, R, 0, jedn) == zt.symuluj_prog(
            calls, R + dX, R, 0, jedn, rozpoznaj_artefakty=False
        )


def test_raport_progow_wyklucza_sesje_otwarte():
    """Sesja z wywołaniem w ostatnich 60 min przed `teraz` (granica włącznie) wypada z symulacji
    i trafia do „sesje_wykluczone”; gdy zostaje zero sesji — ValueError."""
    a, b, c = _trzy_sesje()
    koniec_c = datetime(2026, 9, 28, 2, 0, 19, tzinfo=timezone.utc)
    assert c[-1].ts == "2026-09-28T02:00:19Z"
    r = zt.raport_progow(zt.Scan(calls=a + b + c), teraz=koniec_c + timedelta(minutes=60))
    assert r["sesji"] == 2 and [s["sesja"] for s in r["sesje_wykluczone"]] == ["C"]
    assert r["sesje_wykluczone"][0]["ostatnie"] == c[-1].ts
    txt = zt.raport_progow_tekst(r)
    assert "Pominięte sesje z wywołaniem w ostatnich 60 min" in txt
    assert "C — ostatnie wywołanie 2026-09-28 02:00 UTC, 20 wywołań" in txt
    r2 = zt.raport_progow(
        zt.Scan(calls=a + b + c), teraz=koniec_c + timedelta(minutes=60, seconds=1)
    )
    assert r2["sesji"] == 3 and r2["sesje_wykluczone"] == []
    with pytest.raises(ValueError, match="zakończonych"):  # teraz = 00:30: wszystkie trzy „trwają”
        zt.raport_progow(zt.Scan(calls=a + b + c), teraz=koniec_c - timedelta(minutes=90))


def test_raport_progow_artefakty_i_czyszczenia_bez_rozpoznania():
    """Raport liczy zdarzenia łańcucha i czyszczenia przy 250 tys. obiema metodami (per sesja i razem)."""
    konteksty = [40_000] * 9 + [70_000, 300_000, 380_000, 310_000, 390_000, 320_000, 400_000]
    pops = [zt.POCZATEK] + list(range(10)) + [10, 11, 12, 13, 14]  # liniowo
    pops[12], pops[14] = 10, 12  # 310 i 320 tys. — drugi strumień od wywołania z 300 tys.
    pops[13], pops[15] = 11, 13
    calls = _z_lancuchem(_sesja(konteksty, session="D"), pops)
    r = zt.raport_progow(zt.Scan(calls=calls), teraz=TERAZ)
    a = r["artefakty"]
    assert (a["rozgalezienia"], a["przelaczenia_modelu"], a["poczatki_lancucha"]) == (1, 0, 0)
    assert a["prog"] == 250_000 and a["czyszczen"] < a["czyszczen_bez_rozpoznania"]
    per = r["sesje_przy_progu"]["sesje"][0]
    assert (per["czyszczen"], per["czyszczen_bez_rozpoznania"]) == (
        a["czyszczen"],
        a["czyszczen_bez_rozpoznania"],
    )
    assert "czyszczenia przy progu 250 tys. (K×1): bez rozpoznania" in zt.raport_progow_tekst(r)


def test_plaski_odcinek_do_5_pkt_od_najlepszego():
    """Progi do 5 pkt proc. od najlepszego (granica włącznie), osobno dla K; część wspólna tylko
    dla K×1 i K×2 (K×0,5 nie wchodzi)."""
    pct = {
        0.5: {150: 20.0, 200: 21.0, 250: 19.0, 300: 12.0},
        1.0: {150: 10.0, 200: 14.0, 250: 15.0, 300: 10.0},
        2.0: {150: 0.0, 200: 9.0, 250: 12.0, 300: 7.0},
    }
    wiersze = [
        {"prog": x * 1000, "mnoznik_K": m, "oszczednosc_pct": v}
        for m, d in pct.items()
        for x, v in d.items()
    ]
    p = zt.plaski_odcinek(wiersze)
    per = {m["mnoznik_K"]: m for m in p["mnozniki"]}
    assert per[1.0]["najlepszy_prog"] == 250_000
    assert per[1.0]["progi"] == [150_000, 200_000, 250_000, 300_000]
    assert per[2.0]["progi"] == [200_000, 250_000, 300_000]
    assert per[0.5]["progi"] == [150_000, 200_000, 250_000]
    assert p["wspolny"] == [200_000, 250_000, 300_000] and p["tol_pkt"] == 5.0
    assert zt.plaski_odcinek(wiersze, tol=1.0)["wspolny"] == [250_000]
    assert zt.plaski_odcinek([]) == {"tol_pkt": 5.0, "mnozniki": [], "wspolny": []}


def test_raport_progow_model_spoza_cennika_jawnie():
    """Sesja na modelu spoza cennika: koszt i oszczędność w USD liczą się jako 0, ale raport mówi to
    wprost (liczba takich wywołań, „UWAGA”), a n* jest nieznane zamiast wymyślone."""
    a, b, c = _trzy_sesje()
    for x in c:
        x.model = "claude-nowy-9"
    r = zt.raport_progow(zt.Scan(calls=c), teraz=TERAZ)
    assert r["wywolan_bez_ceny"] == 20 and r["koszt_sesji"] == 0
    assert r["cena_odczytu"] is None and all(z["n_zwrotu"] is None for z in r["zwrot"])
    txt = zt.raport_progow_tekst(r)
    assert "UWAGA: 20 wywołań modeli spoza cennika liczy się jako 0 USD" in txt
    assert "spoza cennika — n* nieznane" in txt
    mieszane = zt.raport_progow(zt.Scan(calls=a + b + c), teraz=TERAZ)
    assert (
        mieszane["wywolan_bez_ceny"] == 20 and mieszane["model_ceny_odczytu"] == "claude-opus-5-5"
    )
