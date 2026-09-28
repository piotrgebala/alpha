"""Testy tools/zuzycie_tokenow.py — monitor zużycia tokenów (syntetyczne zapisy JSONL, bez sieci)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import zuzycie_tokenow as zt


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
    assert "Modele (jednostki" in zt.report(s)
