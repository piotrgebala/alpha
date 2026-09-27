"""Testy kopii zapasowej likwidacji (`data/liquidation_backup.py`, `tools/likwidacje_kopia.sh`) —
bez sieci: deterministyczny gzip, weryfikacja wykrywa uszkodzenie, pomijanie dnia bieżącego,
idempotencja (dwa przebiegi → 0 nowych commitów), źródło zmienione po fakcie, brak katalogu Bybit,
brak remote → kod 0 i wpis w logu, push na lokalne `git init --bare`, bramka dzienna 00:15 UTC;
po przeglądzie 2026-09-27: źródło skrócone = alarm bez nadpisania kopii, ponowienia po błędzie
najwcześniej po 60 min, zaległy push bez przeliczania, GIT_SSH_COMMAND (fałszywy `ssh` w PATH),
limit czasu push, `GIT_DIR` z otoczenia nie przekierowuje kopii do cudzego repo, zła linia (T)
nie blokuje dnia.
"""

from __future__ import annotations

import datetime as dt
import gzip
import os
import shutil
import shlex
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data import liquidation_backup as lb
from data import liquidation_index as li
from tests.test_liquidation_index import D0, MIN, bb, bn

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="brak git")

REPO = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 9, 27, 6, 0, tzinfo=dt.timezone.utc)
TODAY = NOW.date()
DAY_MS = 86_400_000


@pytest.fixture(autouse=True)
def _git_bez_konfiguracji_uzytkownika(monkeypatch, tmp_path):
    """Globalna konfiguracja git użytkownika nie wpływa na testy (hooki, podpisy, gałąź domyślna)."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("CLAS5_KOPIA_KEY", str(tmp_path / "brak_klucza"))


def _sources(tmp_path: Path, bybit: bool = True, today: dt.date = TODAY) -> dict[str, Path]:
    """Pliki dni `today`−2, `today`−1 (zamknięte) i `today` (bieżący — nie do kopii). Testy
    z wstrzykniętym zegarem biorą `NOW`; test skryptu powłoki (prawdziwy zegar) — `utc_today()`."""
    d0 = int(dt.datetime.combine(today, dt.time(), dt.timezone.utc).timestamp() * 1000) - 2 * DAY_MS
    n0, n1, n2 = ((today - dt.timedelta(days=k)).isoformat() for k in (2, 1, 0))
    b = tmp_path / "likwidacje"
    b.mkdir()
    (b / f"{n0}.jsonl").write_text(
        "\n".join([bn(d0 + MIN), bn(d0 + 2 * MIN, "ETHUSDT", "BUY")]) + "\n", encoding="utf-8"
    )
    (b / f"{n1}.jsonl").write_text(bn(d0 + DAY_MS + MIN) + "\n", encoding="utf-8")
    (b / f"{n2}.jsonl").write_text(bn(d0 + 2 * DAY_MS) + "\n", encoding="utf-8")  # dziś
    (b / "status.json").write_text("{}", encoding="utf-8")
    out = {"binance": b, "bybit": tmp_path / "likwidacje_bybit"}
    if bybit:
        y = out["bybit"]
        y.mkdir()
        (y / f"{n1}.jsonl").write_text(
            "\n".join([bb(d0 + DAY_MS + 5), bb(d0 + DAY_MS + 9, side="Sell")]) + "\n",
            encoding="utf-8",
        )
        (y / f"{n2}.jsonl").write_text(bb(d0 + 2 * DAY_MS) + "\n", encoding="utf-8")
    return out


def test_sources_domyslnie_na_stalym_now():
    assert D0 == int(dt.datetime(2026, 9, 25, tzinfo=dt.timezone.utc).timestamp() * 1000)


def _commits(repo: Path) -> int:
    r = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True
    )
    return int(r.stdout.strip()) if r.returncode == 0 else 0


def _log(kopia: Path) -> str:
    p = kopia / lb.LOG_NAME
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ------------------------------------------------------------------ czyste funkcje
def test_gzip_deterministyczny_naglowek_i_zawartosc():
    data = b'{"a":1}\n{"b":2}\n'
    a = lb.gzip_bytes(data, "2026-09-25.jsonl")
    assert a == lb.gzip_bytes(data, "2026-09-25.jsonl")
    assert a[4:8] == b"\x00\x00\x00\x00"  # MTIME = 0
    assert b"2026-09-25.jsonl\x00" in a[:40]  # stała nazwa w nagłówku (FNAME)
    assert gzip.decompress(a) == data


@given(st.binary(max_size=5000))
@settings(max_examples=100, deadline=None)
def test_wlasnosc_gzip_odwracalny_i_powtarzalny(data):
    a = lb.gzip_bytes(data, "x.jsonl")
    assert gzip.decompress(a) == data
    assert a == lb.gzip_bytes(data, "x.jsonl")
    assert lb.verify_archive(a, data) == []


def test_weryfikacja_wykrywa_uszkodzony_plik():
    data = "".join(bn(D0 + i * 1000) + "\n" for i in range(200)).encode()
    good = lb.gzip_bytes(data, "d.jsonl")
    assert lb.verify_archive(good, data) == []
    flipped = bytearray(good)
    flipped[len(good) // 2] ^= 0xFF
    assert lb.verify_archive(bytes(flipped), data)
    assert lb.verify_archive(good[: len(good) - 10], data)  # ucięte
    assert lb.verify_archive(b"to nie gzip", data)
    other = lb.gzip_bytes(data + b"x\n", "d.jsonl")
    probs = lb.verify_archive(other, data)
    assert any("linie" in p for p in probs) and any("bajty" in p for p in probs)


def test_liczba_linii():
    assert lb.count_lines(b"") == 0
    assert lb.count_lines(b"a\nb\n") == 2
    assert lb.count_lines(b"a\nb") == 2


@pytest.mark.parametrize(
    "hhmm,marker,teraz,expected",
    [
        ((0, 10), None, False, False),  # przed 00:15 UTC
        ((0, 15), None, False, True),
        ((6, 0), "2026-09-27", False, False),  # już dziś był
        ((6, 0), "2026-09-26", False, True),
        ((0, 5), "2026-09-27", True, True),  # --teraz zawsze
    ],
)
def test_bramka_dzienna(hhmm, marker, teraz, expected):
    now = dt.datetime(2026, 9, 27, *hhmm, tzinfo=dt.timezone.utc)
    assert lb.is_due(now, marker, teraz) is expected


def test_bramka_dzienna_liczy_w_utc():
    now = dt.datetime(2026, 9, 27, 2, 10, tzinfo=dt.timezone(dt.timedelta(hours=2)))  # 00:10 UTC
    assert lb.is_due(now, None) is False


def test_manifest_w_obie_strony():
    row = {c: "1" for c in lb.MANIFEST_COLUMNS} | {"dzien": "2026-09-25", "gielda": "bybit"}
    rows = {("bybit", "2026-09-25"): row}
    assert lb.parse_manifest(lb.manifest_csv(rows)) == rows
    with pytest.raises(ValueError):
        lb.parse_manifest(b"zly,naglowek\n")


# ------------------------------------------------------------------ przebieg
def test_przebieg_pomija_dzis_archiwizuje_indeksuje_i_weryfikuje(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.errors == [] and s.new == 3 and s.changed == 0
    assert sorted(p.name for p in (kopia / "binance").iterdir()) == [
        "2026-09-25.jsonl.gz",
        "2026-09-26.jsonl.gz",
    ]
    assert [p.name for p in (kopia / "bybit").iterdir()] == ["2026-09-26.jsonl.gz"]
    assert not list(kopia.rglob("2026-09-27*"))  # dzień bieżący nigdy nie jest kopiowany
    for g, d in (("binance", "2026-09-25"), ("binance", "2026-09-26"), ("bybit", "2026-09-26")):
        arch = (kopia / g / f"{d}.jsonl.gz").read_bytes()
        assert gzip.decompress(arch) == (src[g] / f"{d}.jsonl").read_bytes()
        assert (kopia / "indeks" / f"{g}_{d}.csv").exists()
    man = lb.parse_manifest((kopia / "manifest.csv").read_bytes())
    assert man[("binance", "2026-09-25")]["linie"] == "2"
    assert man[("bybit", "2026-09-26")]["linie"] == "2"
    by = (kopia / "indeks" / "bybit_2026-09-26.csv").read_text(encoding="utf-8").splitlines()
    assert by[1].split(",")[4:7] == ["2", "1", "1"]  # zdarzenia, long (Buy), short (Sell)
    assert _commits(kopia) == 1
    assert (kopia / ".gitignore").read_text(encoding="utf-8") == lb.GITIGNORE
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=kopia, capture_output=True, text=True
    ).stdout.split()
    assert "kopia.log" not in tracked and "manifest.csv" in tracked


def test_idempotencja_dwa_przebiegi_zero_nowych_commitow(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.run_backup(kopia, src, now=NOW)
    snap = {p: p.read_bytes() for p in kopia.rglob("*") if p.is_file() and ".git" not in p.parts}
    s2 = lb.run_backup(kopia, src, now=NOW + dt.timedelta(days=0, hours=1))
    assert s2.commit is None and s2.unchanged == 3 and s2.new == 0
    assert _commits(kopia) == 1
    for p, b in snap.items():
        if p.name != lb.LOG_NAME:
            assert p.read_bytes() == b, p


def test_zrodlo_tylko_do_odczytu_i_nietkniete(tmp_path):
    src = _sources(tmp_path)
    before = {p: p.read_bytes() for d in src.values() for p in d.iterdir()}
    for d in src.values():
        for p in d.iterdir():
            p.chmod(stat.S_IRUSR)
        d.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        s = lb.run_backup(tmp_path / "kopia", src, now=NOW)
    finally:
        for d in src.values():
            d.chmod(stat.S_IRWXU)
    assert s.errors == []
    assert {p: p.read_bytes() for d in src.values() for p in d.iterdir()} == before


def test_zrodlo_zmienione_po_fakcie_przelicza_i_loguje(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.run_backup(kopia, src, now=NOW)
    with open(src["binance"] / "2026-09-26.jsonl", "a", encoding="utf-8") as f:
        f.write(bn(D0 + DAY_MS + 3 * MIN, "SOLUSDT") + "\n")
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.changed == 1 and s.unchanged == 2 and s.commit is not None
    assert "ZMIENIONY PO FAKCIE: binance 2026-09-26" in _log(kopia)
    arch = (kopia / "binance" / "2026-09-26.jsonl.gz").read_bytes()
    assert gzip.decompress(arch).count(b"\n") == 2
    assert "SOLUSDT" in (kopia / "indeks" / "binance_2026-09-26.csv").read_text(encoding="utf-8")
    assert _commits(kopia) == 2


def test_uszkodzone_archiwum_odtworzone_ze_zrodla(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.run_backup(kopia, src, now=NOW)
    p = kopia / "binance" / "2026-09-25.jsonl.gz"
    good = p.read_bytes()
    p.write_bytes(good[:-8] + b"\x00" * 8)
    (kopia / "indeks" / "bybit_2026-09-26.csv").unlink()
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.errors == [] and s.changed == 2
    assert p.read_bytes() == good
    assert (kopia / "indeks" / "bybit_2026-09-26.csv").exists()
    log = _log(kopia)
    assert "USZKODZONE ARCHIWUM: binance 2026-09-25" in log
    assert "BRAK INDEKSU: bybit 2026-09-26" in log
    assert _commits(kopia) == 1  # odtworzone bajty = te same, co w commicie → brak commita


def test_nowa_wersja_indeksu_i_uszkodzony_indeks_przeliczone(tmp_path, monkeypatch):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.run_backup(kopia, src, now=NOW)
    p = kopia / "indeks" / "binance_2026-09-25.csv"
    good = p.read_bytes()
    p.write_bytes(good.replace(b"binance,", b"binanse,", 1))
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.changed == 1 and p.read_bytes() == good
    assert "USZKODZONY INDEKS: binance 2026-09-25" in _log(kopia)
    monkeypatch.setattr(lb.li, "INDEX_VERSION", 99)
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.changed == 3 and "NOWA WERSJA INDEKSU: bybit 2026-09-26 — 1 → 99" in _log(kopia)
    man = lb.parse_manifest((kopia / "manifest.csv").read_bytes())
    assert {r["wersja_indeksu"] for r in man.values()} == {"99"}
    assert _commits(kopia) == 2  # zmienił się tylko manifest (wersja), indeksy te same bajty


def test_stary_naglowek_manifestu_przyjety_i_uzupelniony(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.run_backup(kopia, src, now=NOW)
    man_path = kopia / "manifest.csv"
    old_cols = lb.MANIFEST_COLUMNS[:8]
    rows = lb.parse_manifest(man_path.read_bytes())
    old = [",".join(old_cols)] + [",".join(r[c] for c in old_cols) for r in rows.values()]
    man_path.write_text("\n".join(old) + "\n", encoding="utf-8")
    parsed = lb.parse_manifest(man_path.read_bytes())
    assert all(r["wersja_indeksu"] == "" for r in parsed.values())
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.errors == [] and s.changed == 3
    assert man_path.read_bytes() == lb.manifest_csv(rows)


def test_brak_katalogu_bybit_nie_przeszkadza(tmp_path):
    src = _sources(tmp_path, bybit=False)
    kopia = tmp_path / "kopia"
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.errors == [] and s.new == 2 and s.missing_sources == ["bybit"]
    assert "brak katalogu źródłowego bybit" in _log(kopia)


def test_brak_remote_kod_0_i_wpis_w_logu(tmp_path, capsys):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    args = ["--teraz", "--kopia", str(kopia), "--binance", str(src["binance"])]
    args += ["--bybit", str(src["bybit"])]
    assert lb.main(args, now_fn=lambda: NOW) == 0
    assert "BRAK ZDALNEJ KOPII: brak skonfigurowanego remote origin" in _log(kopia)
    assert '"zdalna_kopia": "brak remote"' in (kopia / "status.json").read_text(encoding="utf-8")
    out = capsys.readouterr().out
    assert "razem dni 3" in out and "zdalna kopia: brak remote" in out


def test_push_na_lokalne_bare_repo(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    bare = tmp_path / "zdalne.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    lb.ensure_repo(kopia)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=kopia, check=True)
    s = lb.run_backup(kopia, src, now=NOW)
    assert s.remote == "ok", s.remote_msg
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=kopia, capture_output=True, text=True
    ).stdout
    remote = subprocess.run(
        ["git", "rev-parse", "main"], cwd=bare, capture_output=True, text=True
    ).stdout
    assert head == remote and head.strip()
    assert "BRAK ZDALNEJ KOPII" not in _log(kopia)
    s2 = lb.run_backup(kopia, src, now=NOW)  # nic nowego, push „up to date” też ok
    assert s2.remote == "ok" and s2.commit is None


def test_blad_push_kod_0_i_wpis_w_logu(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.ensure_repo(kopia)
    subprocess.run(
        ["git", "remote", "add", "origin", str(tmp_path / "nie_istnieje.git")],
        cwd=kopia,
        check=True,
    )
    args = ["--teraz", "--kopia", str(kopia), "--binance", str(src["binance"])]
    assert lb.main(args + ["--bybit", str(src["bybit"])], now_fn=lambda: NOW) == 0
    assert "BRAK ZDALNEJ KOPII:" in _log(kopia)
    assert (kopia / lb.MARKER).read_text(encoding="utf-8").strip() == "2026-09-27"
    assert _commits(kopia) == 1  # lokalna kopia jest, mimo braku zdalnej


def test_tryb_dzienny_raz_na_dobe(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    args = ["--kopia", str(kopia), "--binance", str(src["binance"]), "--bybit", str(src["bybit"])]
    t = dt.datetime(2026, 9, 27, 0, 10, tzinfo=dt.timezone.utc)
    assert lb.main(args, now_fn=lambda: t) == 0
    assert not (kopia / ".git").exists()  # przed 00:15 UTC nic
    t2 = t + dt.timedelta(minutes=10)
    assert lb.main(args, now_fn=lambda: t2) == 0
    assert (kopia / lb.MARKER).read_text(encoding="utf-8").strip() == "2026-09-27"
    log_after = _log(kopia)
    assert lb.main(args, now_fn=lambda: t2 + dt.timedelta(minutes=5)) == 0
    assert _log(kopia) == log_after  # drugie wywołanie tego dnia nic nie robi
    assert lb.main(args + ["--teraz"], now_fn=lambda: t2 + dt.timedelta(minutes=10)) == 0
    assert _log(kopia) != log_after
    assert _commits(kopia) == 1


def test_blad_dnia_kod_1_bez_znacznika(tmp_path, monkeypatch):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    monkeypatch.setattr(lb, "verify_archive", lambda a, s: ["symulowane uszkodzenie"])
    args = ["--teraz", "--kopia", str(kopia), "--binance", str(src["binance"])]
    assert lb.main(args + ["--bybit", str(src["bybit"])], now_fn=lambda: NOW) == 1
    assert "BŁĄD: binance 2026-09-25" in _log(kopia)
    assert not (kopia / lb.MARKER).exists()  # następne wywołanie ponowi
    assert lb.read_time_marker(kopia / lb.ERROR_MARKER) == NOW  # … ale nie wcześniej niż za 60 min


def test_zly_argument():
    assert lb.main(["--cos"]) == 2


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("flock") is None, reason="flock/bash tylko na Linuksie"
)
def test_skrypt_powloki_teraz(tmp_path):
    src = _sources(tmp_path, today=li.utc_today())  # skrypt liczy „dziś” z prawdziwego zegara
    kopia = tmp_path / "kopia"
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "CLAS5_KOPIA_DIR": str(kopia),
        "CLAS5_LIKWIDACJE_DIR": str(src["binance"]),
        "CLAS5_LIKWIDACJE_BYBIT_DIR": str(src["bybit"]),
        "CLAS5_PYTHON": sys.executable,
    }
    r = subprocess.run(
        ["bash", str(REPO / "tools" / "likwidacje_kopia.sh"), "--teraz"],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr
    assert (kopia / "manifest.csv").exists() and _commits(kopia) == 1
    assert "razem dni 3" in (kopia / "kopia.out").read_text(encoding="utf-8")


# ------------------------------------------------------------------ poprawki po przeglądzie
def _main(kopia: Path, src: dict[str, Path], now: dt.datetime, *extra: str) -> int:
    args = ["--kopia", str(kopia), "--binance", str(src["binance"]), "--bybit", str(src["bybit"])]
    return lb.main(args + list(extra), now_fn=lambda: now)


def _status(kopia: Path) -> dict:
    import json

    return json.loads((kopia / lb.STATUS_NAME).read_text(encoding="utf-8"))


def test_zla_linia_czasu_nie_blokuje_dnia(tmp_path):
    """T = 10**17 (rok 3170843) → zła linia w indeksie; dzień w manifeście, kod 0, znacznik dnia."""
    src = _sources(tmp_path)
    with open(src["binance"] / "2026-09-25.jsonl", "a", encoding="utf-8") as f:
        f.write(bn(10**17) + "\n")
    kopia = tmp_path / "kopia"
    assert _main(kopia, src, NOW, "--teraz") == 0
    man = lb.parse_manifest((kopia / "manifest.csv").read_bytes())
    assert man[("binance", "2026-09-25")]["zle_linie"] == "1"
    assert man[("binance", "2026-09-25")]["linie"] == "3"
    assert (kopia / "indeks" / "binance_2026-09-25.csv").exists()
    assert (kopia / lb.MARKER).exists() and not (kopia / lb.ERROR_MARKER).exists()
    assert "1 złych linii" in _log(kopia)


def test_blad_indeksu_nie_zostawia_archiwum_bez_manifestu(tmp_path, monkeypatch):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"

    def boom(idx):
        raise ValueError("symulowany błąd indeksu")

    monkeypatch.setattr(lb.li, "index_csv", boom)
    s = lb.run_backup(kopia, src, now=NOW)
    assert len(s.errors) == 3
    assert not (kopia / "binance").exists() and not (kopia / "bybit").exists()


def _source_100(tmp_path: Path) -> dict[str, Path]:
    src = _sources(tmp_path)
    lines = [bn(D0 + i * 1000) for i in range(100)]
    (src["binance"] / "2026-09-25.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return src


@pytest.mark.parametrize(
    "damage",
    ["ucięty", "inny początek", "krótszy o bajty"],
)
def test_zrodlo_skrocone_alarm_bez_nadpisania_kopii(tmp_path, damage):
    src = _source_100(tmp_path)
    kopia = tmp_path / "kopia"
    assert _main(kopia, src, NOW, "--teraz") == 0
    arch = kopia / "binance" / "2026-09-25.jsonl.gz"
    good_arch = arch.read_bytes()
    good_man = (kopia / "manifest.csv").read_bytes()
    good_idx = (kopia / "indeks" / "binance_2026-09-25.csv").read_bytes()
    f = src["binance"] / "2026-09-25.jsonl"
    data = f.read_bytes()
    if damage == "ucięty":
        f.write_bytes(data.split(b"\n", 1)[0] + b"\n")
    elif damage == "inny początek":  # ta sama długość i liczba linii, podmieniony pierwszy znak
        f.write_bytes(b"[" + data[1:])
    else:  # ostatnia linia bez końcówki, ale liczba linii ta sama
        f.write_bytes(data[:-5])
    commits = _commits(kopia)
    assert _main(kopia, src, NOW + dt.timedelta(minutes=1), "--teraz") == 0  # alarm ≠ błąd
    assert arch.read_bytes() == good_arch
    assert (kopia / "manifest.csv").read_bytes() == good_man
    assert (kopia / "indeks" / "binance_2026-09-25.csv").read_bytes() == good_idx
    assert _commits(kopia) == commits
    st_ = _status(kopia)
    assert st_["bledy"] == [] and len(st_["alarmy"]) == 1
    assert "ŹRÓDŁO SKRÓCONE/NADPISANE: binance 2026-09-25" in st_["alarmy"][0]
    assert "ŹRÓDŁO SKRÓCONE/NADPISANE: binance 2026-09-25" in _log(kopia)
    assert not (kopia / lb.ERROR_MARKER).exists()  # alarm nie włącza ponowień


def test_zrodlo_skrocone_przyjete_swiadomie(tmp_path):
    src = _source_100(tmp_path)
    kopia = tmp_path / "kopia"
    assert _main(kopia, src, NOW, "--teraz") == 0
    f = src["binance"] / "2026-09-25.jsonl"
    f.write_bytes(f.read_bytes().split(b"\n", 1)[0] + b"\n")
    assert _main(kopia, src, NOW, "--teraz", "--przyjmij-skrocone") == 0
    arch = (kopia / "binance" / "2026-09-25.jsonl.gz").read_bytes()
    assert gzip.decompress(arch).count(b"\n") == 1
    assert "PRZYJĘTO SKRÓCONE ŹRÓDŁO: binance 2026-09-25 — linie 100 → 1" in _log(kopia)
    assert _status(kopia)["alarmy"] == [] and _commits(kopia) == 2


def test_shrink_problem_czysta_funkcja():
    prev = {"linie": "2", "bajty_zrodla": "4"}
    assert lb.shrink_problem(b"a\nb\nc\n", prev, b"a\nb\n") is None  # dopisanie
    assert lb.shrink_problem(b"a\nbc", prev, b"a\nb\n") is not None  # dokończona ≠ prefiks
    assert "linie" in lb.shrink_problem(b"a\n", prev, None)
    assert "początek" in lb.shrink_problem(b"x\nb\nc\n", {"linie": "2"}, b"a\nb\n")
    assert lb.shrink_problem(b"a\nb\nc\n", {"linie": "2", "bajty_zrodla": ""}, None) is None


@pytest.mark.parametrize(
    "hhmm,last_err_min_ago,expected",
    [((6, 0), None, True), ((6, 0), 5, False), ((6, 0), 59, False), ((6, 0), 60, True)],
)
def test_bramka_dzienna_ogranicza_ponowienia_po_bledzie(hhmm, last_err_min_ago, expected):
    now = dt.datetime(2026, 9, 27, *hhmm, tzinfo=dt.timezone.utc)
    last = None if last_err_min_ago is None else now - dt.timedelta(minutes=last_err_min_ago)
    assert lb.is_due(now, "2026-09-26", False, last) is expected
    assert lb.is_due(now, "2026-09-26", True, last) is True  # --teraz zawsze


def test_trwaly_blad_ponawiany_co_godzine_nie_co_5_min(tmp_path, monkeypatch):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    monkeypatch.setattr(lb, "verify_archive", lambda a, s: ["symulowane uszkodzenie"])
    t = dt.datetime(2026, 9, 27, 0, 20, tzinfo=dt.timezone.utc)
    assert _main(kopia, src, t) == 1
    log1 = _log(kopia)
    for m in (5, 30, 55):
        assert _main(kopia, src, t + dt.timedelta(minutes=m)) == 0  # nic nie robi
    assert _log(kopia) == log1
    assert _main(kopia, src, t + dt.timedelta(minutes=61)) == 1  # ponowienie po godzinie
    assert _log(kopia) != log1
    monkeypatch.undo()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("CLAS5_KOPIA_KEY", str(tmp_path / "brak_klucza"))
    assert _main(kopia, src, t + dt.timedelta(minutes=70), "--teraz") == 0
    assert not (kopia / lb.ERROR_MARKER).exists() and (kopia / lb.MARKER).exists()


def test_blad_calego_przebiegu_status_i_ograniczenie(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    kopia.mkdir()
    (kopia / "manifest.csv").write_text("dzien,gielda\n", encoding="utf-8")  # zepsuty manifest
    t = dt.datetime(2026, 9, 27, 1, 0, tzinfo=dt.timezone.utc)
    assert _main(kopia, src, t) == 1
    st_ = _status(kopia)
    assert st_["bledy"] and "manifest" in st_["bledy"][0]
    assert lb.read_time_marker(kopia / lb.ERROR_MARKER) == t
    log1 = _log(kopia)
    assert _main(kopia, src, t + dt.timedelta(minutes=5)) == 0 and _log(kopia) == log1


def test_zalegly_push_ponawiany_bez_przeliczania(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    bare = tmp_path / "zdalne.git"  # jeszcze nie istnieje → push się nie uda
    lb.ensure_repo(kopia)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=kopia, check=True)
    t = dt.datetime(2026, 9, 27, 0, 20, tzinfo=dt.timezone.utc)
    assert _main(kopia, src, t) == 0
    assert _status(kopia)["zdalna_kopia"] == "błąd push"
    assert lb.read_time_marker(kopia / lb.PUSH_MARKER) == t
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)  # sieć „wróciła”
    manifest = (kopia / "manifest.csv").read_bytes()
    assert _main(kopia, src, t + dt.timedelta(minutes=30)) == 0  # za wcześnie na ponowienie
    assert "dogoniona" not in _log(kopia)
    assert _main(kopia, src, t + dt.timedelta(minutes=61)) == 0
    assert "zaległy push: zdalna kopia dogoniona" in _log(kopia)
    assert not (kopia / lb.PUSH_MARKER).exists()
    assert "ZMIENIONY" not in _log(kopia) and (kopia / "manifest.csv").read_bytes() == manifest
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=kopia, capture_output=True, text=True)
    remote = subprocess.run(["git", "rev-parse", "main"], cwd=bare, capture_output=True, text=True)
    assert head.stdout == remote.stdout and head.stdout.strip()
    st_ = _status(kopia)
    assert st_["zdalna_kopia"] == "ok" and "push_ponowiony_utc" in st_
    assert _commits(kopia) == 1


def test_brak_remote_nie_zostawia_znacznika_zaleglego_push(tmp_path):
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    assert _main(kopia, src, NOW, "--teraz") == 0
    assert not (kopia / lb.PUSH_MARKER).exists()


def _fake_ssh(tmp_path: Path, monkeypatch, body: str) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    ssh = bindir / "ssh"
    ssh.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    ssh.chmod(0o755)
    args_file = tmp_path / "ssh_args.txt"
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("SSH_ARGS_FILE", str(args_file))
    return args_file


@pytest.mark.skipif(sys.platform == "win32", reason="fałszywy ssh jako skrypt sh")
def test_git_ssh_command_klucz_identitiesonly_batchmode(tmp_path, monkeypatch):
    args_file = _fake_ssh(
        tmp_path, monkeypatch, 'for a in "$@"; do echo "$a" >> "$SSH_ARGS_FILE"; done\nexit 255'
    )
    key = tmp_path / 'klucz z "cudzy" $HOME `id`'  # znaki powłoki w ścieżce → shlex.quote
    monkeypatch.setenv("CLAS5_KOPIA_KEY", str(key))
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    lb.ensure_repo(kopia)
    subprocess.run(
        ["git", "remote", "add", "origin", "ssh://git@example.invalid/x.git"], cwd=kopia, check=True
    )
    assert _main(kopia, src, NOW, "--teraz") == 0
    args = args_file.read_text(encoding="utf-8").splitlines()
    i = args.index("-i")
    assert args[i + 1] == str(key)  # ścieżka dotarła do ssh 1:1, bez interpretacji powłoki
    joined = " ".join(args)
    assert "-o IdentitiesOnly=yes" in joined and "-o BatchMode=yes" in joined
    assert "git@example.invalid" in args
    assert _status(kopia)["zdalna_kopia"] == "błąd push"
    assert "BRAK ZDALNEJ KOPII:" in _log(kopia)


def test_ssh_command_cytuje_sciezke():
    key = Path('/tmp/a b/"x" $y')
    parts = shlex.split(lb.ssh_command(key))
    assert parts == ["ssh", "-i", str(key), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes"]


@pytest.mark.skipif(sys.platform == "win32", reason="fałszywy ssh jako skrypt sh; killpg")
def test_limit_czasu_push_zabija_zawieszony_ssh(tmp_path, monkeypatch):
    _fake_ssh(tmp_path, monkeypatch, "exec sleep 30")
    monkeypatch.setattr(lb, "PUSH_TIMEOUT_S", 1)
    kopia = tmp_path / "kopia"
    lb.ensure_repo(kopia)
    subprocess.run(
        ["git", "remote", "add", "origin", "ssh://git@example.invalid/x.git"], cwd=kopia, check=True
    )
    assert lb.commit_changes(kopia, "pierwszy")  # jest co wypchnąć (.gitignore)
    t0 = time.monotonic()
    remote, msg = lb.push(kopia, tmp_path / "klucz")
    assert remote == "błąd push" and "limit 1 s" in msg
    assert time.monotonic() - t0 < 15  # grupa procesów zabita — `sleep 30` nie trzyma potoków


def test_git_env_usuwa_zmienne_sterujace_repozytorium():
    base = {
        "PATH": "/bin",
        "HOME": "/h",
        "GIT_DIR": "/cudze/.git",
        "GIT_WORK_TREE": "/cudze",
        "GIT_INDEX_FILE": "/cudze/idx",
        "GIT_AUTHOR_NAME": "ktoś",
        "GIT_SSH": "/bin/zly",
        "GIT_CONFIG_PARAMETERS": "'core.hookspath'='/x'",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    env = lb.git_env(base, {"GIT_SSH_COMMAND": "ssh"})
    assert env == {
        "PATH": "/bin",
        "HOME": "/h",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_SSH_COMMAND": "ssh",
    }


def test_git_dir_z_otoczenia_nie_przekierowuje_kopii(tmp_path, monkeypatch):
    """Wywołanie z hooka innego repo (GIT_DIR/GIT_WORK_TREE w środowisku) nie może commitować
    do tamtego repo ani przepisać jego user.name/email."""
    victim = tmp_path / "cudze"
    victim.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "master", str(victim)], check=True)
    for k, v in (("user.name", "wlasciciel"), ("user.email", "w@x")):
        subprocess.run(["git", "config", k, v], cwd=victim, check=True)
    (victim / "a.txt").write_text("a", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=victim, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "a"], cwd=victim, check=True)
    config_before = (victim / ".git" / "config").read_bytes()
    head_before = (victim / ".git" / "refs" / "heads" / "master").read_bytes()
    src = _sources(tmp_path)
    kopia = tmp_path / "kopia"
    monkeypatch.setenv("GIT_DIR", str(victim / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(victim))
    monkeypatch.setenv("GIT_INDEX_FILE", str(victim / ".git" / "index"))
    assert _main(kopia, src, NOW, "--teraz") == 0
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_WORK_TREE")
    monkeypatch.delenv("GIT_INDEX_FILE")
    assert (victim / ".git" / "config").read_bytes() == config_before
    assert (victim / ".git" / "refs" / "heads" / "master").read_bytes() == head_before
    assert _commits(victim) == 1
    assert (kopia / ".git").is_dir() and _commits(kopia) == 1
    author = subprocess.run(
        ["git", "log", "-1", "--format=%an"], cwd=kopia, capture_output=True, text=True
    ).stdout.strip()
    assert author == lb.GIT_USER


def test_skrypt_powloki_ma_niski_priorytet_dysku():
    text = (REPO / "tools" / "likwidacje_kopia.sh").read_text(encoding="utf-8")
    assert "ionice -c3" in text and "nice -n 10" in text
