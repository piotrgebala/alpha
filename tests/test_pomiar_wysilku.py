"""Testy tools/pomiar_wysilku.py — pomiar T5 z docs/rag/12 (plan, komenda, ocena, strażnik kopii,
wznawianie, podsumowanie).

Bez `claude` i sieci: `claude` podstawiany przez monkeypatch `subprocess.run` (git i pytest idą
naprawdę). Strażnik i `kopia` na prawdziwych repozytoriach git w katalogu tymczasowym; ocena Z2
uruchamia pytest na prawdziwych piaskownicach (ok. 0,6 s na ocenę).
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from backtest import metrics
from tools import pomiar_wysilku as pw

REPO = Path(__file__).resolve().parents[1]
BLOKI = [("Z1", 1), ("Z2", 1), ("Z3", 1), ("Z1", 2), ("Z2", 2), ("Z3", 2)]
PRAWDZIWY_RUN = subprocess.run  # git i pytest idą naprawdę, gdy `claude` jest podstawiony


# --- plan i komenda ---------------------------------------------------------------------------


def _sprawdz_plan(wpisy: list[dict]) -> None:
    assert len(wpisy) == 56
    assert len({w["id"] for w in wpisy}) == 56  # id = klucz wznawiania
    rozgrzewki, bloki = wpisy[:14], wpisy[14:]
    assert all(w["zadanie"] is None and w["powtorzenie"] == 0 for w in rozgrzewki)
    assert sorted((w["narzedzia"], w["model"], w["wysilek"]) for w in rozgrzewki) == sorted(
        (nz, m, e) for nz in pw.NARZEDZIA for m, e in pw.KONFIGURACJE
    )
    for i, (zad, powt) in enumerate(BLOKI):
        blok = bloki[7 * i : 7 * (i + 1)]
        assert {(w["zadanie"], w["powtorzenie"], w["narzedzia"]) for w in blok} == {
            (zad, powt, pw.ZADANIA[zad]["narzedzia"])
        }
        assert sorted((w["model"], w["wysilek"]) for w in blok) == sorted(pw.KONFIGURACJE)


@settings(max_examples=50, deadline=None)
@given(ziarno=st.integers(min_value=0, max_value=2**64))
@example(ziarno=pw.ZIARNO)
def test_plan_rozgrzewki_potem_bloki_kazdy_przebieg_raz(ziarno):
    _sprawdz_plan(pw.plan(ziarno))


def _kolejnosc(ziarno: int) -> list[str]:
    return [w["id"] for w in pw.plan(ziarno)]


def test_plan_deterministyczny_dla_ziarna_inny_dla_innego():
    assert pw.plan() == pw.plan(pw.ZIARNO) == pw.plan(pw.ZIARNO)
    assert _kolejnosc(1) != _kolejnosc(2)
    assert sorted(_kolejnosc(1)) == sorted(_kolejnosc(2))


def test_main_plan_wypisuje_id_w_kolejnosci(capsys):
    assert pw.main(["plan"]) == 0
    assert capsys.readouterr().out.splitlines() == _kolejnosc(pw.ZIARNO)


def _wartosci(cmd: list[str], flaga: str) -> list[str]:
    """Wartości flagi do następnej flagi `--…` (listy narzędzi są wariadyczne)."""
    i = j = cmd.index(flaga) + 1
    while j < len(cmd) and not cmd[j].startswith("--"):
        j += 1
    return cmd[i:j]


@pytest.mark.parametrize("narzedzia", ["odczyt", "zapis"])
def test_komenda_model_wysilek_budzet_i_narzedzia(narzedzia):
    for model, wysilek in pw.KONFIGURACJE:
        cmd = pw.komenda("PROMPT", model, wysilek, narzedzia)
        assert cmd[:3] == ["claude", "-p", "PROMPT"]  # prompt przed listami wariadycznymi
        assert _wartosci(cmd, "--model") == [pw.MODELE[model]]
        assert re.fullmatch(r"claude-(opus|sonnet)-\d[\d-]*", pw.MODELE[model])  # pełne id
        assert _wartosci(cmd, "--effort") == [wysilek]
        assert _wartosci(cmd, "--output-format") == ["json"]
        assert "--no-session-persistence" in cmd
        assert _wartosci(cmd, "--max-budget-usd") == [str(pw.LIMIT_PRZEBIEGU_USD)]
        tryb = "acceptEdits" if narzedzia == "zapis" else "default"
        assert _wartosci(cmd, "--permission-mode") == [tryb]
        dozwolone = _wartosci(cmd, "--allowedTools")
        zabronione = _wartosci(cmd, "--disallowedTools")
        assert cmd[-len(zabronione) - 1] == "--disallowedTools"  # nic nie stoi za listą
        assert {"Skill", "Agent"} <= set(zabronione)
        assert not set(dozwolone) & set(zabronione)
        assert ("Edit" in zabronione) is (narzedzia == "odczyt")
        assert ("Edit" in dozwolone) is (narzedzia == "zapis")


# --- odczyt odpowiedzi: _liczba, linia_wyniku, ocen_z1, ocen_z3 --------------------------------


@pytest.mark.parametrize(
    "tekst,liczba",
    [
        ("0,54", 0.54),
        ("0,540", 0.54),
        ("0,563", 0.563),  # zero całkowite + trzy cyfry po przecinku = ułamek, nie tysiące
        ("0.5631 (56,31 %)", 0.5631),
        ("56,3 %", 0.563),
        ("56,310 %", 0.5631),
        ("1 800", 1800),
        ("1 800 transakcji", 1800),
        ("1,800", 1800),
        ("1800.", 1800),
        ("≈ 1800", 1800),
        ("1,800.0", 1800),  # oba znaki: dziesiętny jest ostatni
        ("1.800,0", 1800),
        ("1 800,0", 1800),
        ("1 800.5", 1800.5),
        ("1,800,000", 1_800_000),  # jeden znak kilka razy = tysiące
        ("1.800.000", 1_800_000),
        ("12,345.678", 12345.678),
    ],
)
def test_liczba_przyklady(tekst, liczba):
    assert pw._liczba(tekst) == pytest.approx(liczba)


def test_liczba_bez_liczby_to_none():
    assert pw._liczba("") is None
    assert pw._liczba("NIEMIERZALNA") is None
    assert pw._liczba("1.2.3") is None
    assert pw._liczba("1,80.5") is None  # grupa tysięcy nie ma 3 cyfr
    assert pw._liczba("1.800,000.5") is None  # dziesiętny dwa razy


@settings(max_examples=300, deadline=None)
@given(
    calkowita=st.one_of(st.just(0), st.integers(0, 99_999)),
    ulamek=st.text("0123456789", min_size=1, max_size=6),
    przecinek=st.booleans(),
    procent=st.booleans(),
    ogon=st.sampled_from(["", " ", ".", ";", " (zaokr.)", " transakcji"]),
)
def test_liczba_odtwarza_zapis_z_kropka_lub_przecinkiem(
    calkowita, ulamek, przecinek, procent, ogon
):
    """Jedyny zapis dwuznaczny — 1,800 (niezerowe 1–3 cyfry, dokładnie 3 po przecinku, bez %) —
    czyta się jako separator tysięcy; każdy inny wraca jako ta sama liczba."""
    assume(not (przecinek and not procent and 1 <= calkowita <= 999 and len(ulamek) == 3))
    kropka = f"{calkowita}.{ulamek}"
    zapis = (kropka.replace(".", ",") if przecinek else kropka) + (" %" if procent else "") + ogon
    assert pw._liczba(zapis) == pytest.approx(float(kropka) / (100 if procent else 1))


@settings(max_examples=100, deadline=None)
@given(x=st.integers(0, 10**9), sep=st.sampled_from([" ", " ", " ", ","]))
def test_liczba_calkowita_z_separatorem_tysiecy(x, sep):
    assert pw._liczba(f"{x:,}".replace(",", sep)) == x


@settings(max_examples=300, deadline=None)
@given(
    calkowita=st.integers(0, 10**9),
    ulamek=st.one_of(st.just(""), st.text("0123456789", min_size=1, max_size=4)),
    styl=st.sampled_from(
        [(",", "."), (" ", ","), (" ", ","), (" ", "."), (".", ","), ("", "."), ("", ",")]
    ),
    procent=st.booleans(),
    ogon=st.sampled_from(["", " ", ".", ";", " (zaokr.)", " transakcji"]),
)
def test_liczba_separatory_tysiecy_i_dziesietne(calkowita, ulamek, styl, procent, ogon):
    """Zapis angielski (1,800.5), polski (1 800,5), niemiecki (1.800,5) i bez grup: spacje to
    tysiące, przy obu znakach dziesiętny jest ostatni, jeden znak kilka razy = tysiące. Dwuznaczny
    jest tylko jeden znak z dokładnie 3 cyframi za nim (1,800 / 1.800) — ma przykłady wyżej."""
    tysiace, dziesietny = styl
    zapis = f"{calkowita:,}".replace(",", tysiace) + (dziesietny + ulamek if ulamek else "")
    assume(not re.fullmatch(r"[1-9]\d{0,2}[.,]\d{3}", re.sub(r"\s", "", zapis)))
    oczekiwana = float(f"{calkowita}.{ulamek or 0}") / (100 if procent else 1)
    assert pw._liczba(zapis + (" %" if procent else "") + ogon) == pytest.approx(oczekiwana)


def test_linia_wyniku_ostatnia_i_bez_znacznikow_markdown():
    tekst = "WYNIK: stara\nuzasadnienie\n**WYNIK:** `p\\*=0,54`; n=1800\n\n"
    assert pw.linia_wyniku(tekst) == "p*=0,54; n=1800"
    assert pw.linia_wyniku("wynik : x") == "x"
    assert pw.linia_wyniku("bez linii z wynikiem") is None


Z1_OK = "WYNIK: backtest/metrics.py:648; expected_trades; abstention_rate"


@pytest.mark.parametrize(
    "tekst",
    [
        Z1_OK,
        "Szukałem w backtest/.\n\n**WYNIK:** `backtest/metrics.py:648`; `expected_trades()`; "
        "`abstention_rate`\n",
        "WYNIK: /home/u/alpha/backtest/metrics.py:648; expected_trades; abstention_rate",
        "WYNIK: backtest/metrics.py:650; expected_trades; abstention_rate",  # wnętrze sygnatury
        "WYNIK: ./backtest/metrics.py:L652; expected_trades; abstention_rate",
        "WYNIK: backtest/metrics.py:1; zla; zly\nPoprawka:\n" + Z1_OK,
    ],
)
def test_ocen_z1_poprawna_takze_w_innym_zapisie(tekst):
    assert pw.ocen_z1(tekst)["poprawna"] is True


@pytest.mark.parametrize(
    "tekst,bledne",
    [
        ("WYNIK: backtest/metrics.py:675; expected_trades; abstention_rate", "linia"),
        ("WYNIK: backtest/metrics.py:647; expected_trades; abstention_rate", "linia"),
        ("WYNIK: backtest/metrics.py:653; expected_trades; abstention_rate", "linia"),
        ("WYNIK: backtest/metrics.py:648; measurability_report; abstention_rate", "funkcja"),
        ("WYNIK: backtest/metrics.py:648; expected_trades; admission_rate", "argument"),
        ("WYNIK: backtest/checkpoint_lib.py:648; expected_trades; abstention_rate", "sciezka"),
    ],
)
def test_ocen_z1_bledna_linia_funkcja_argument_sciezka(tekst, bledne):
    o = pw.ocen_z1(tekst)
    assert o["poprawna"] is False and o["powod"]
    assert [k for k in ("sciezka", "linia", "funkcja", "argument") if not o[k]] == [bledne]


def test_ocen_z1_brak_linii_wynik_lub_zly_format():
    assert pw.ocen_z1("backtest/metrics.py:648") == {"poprawna": False, "powod": "brak linii WYNIK"}
    o = pw.ocen_z1("WYNIK: backtest/metrics.py 648, expected_trades, abstention_rate")
    assert o["poprawna"] is False and o["powod"].startswith("format")


Z3_OK = "WYNIK: p*=0,54; n=1800; p_det=0,5631; werdykt=NIEMIERZALNA"


@pytest.mark.parametrize(
    "tekst",
    [
        Z3_OK,
        "Rachunek jak w zasadzie 18.\n\n**WYNIK:** p\\*=0,54; n=1 800; p_det=0,5631; "
        "werdykt=**NIEMIERZALNA**\n",
        "WYNIK: `p*=0,540`; `n=1800`; `p_det=0,563`; `werdykt=NIEMIERZALNA`",
        "WYNIK: p*=54 %; n=1,800; p_det=56,31 %; werdykt=niemierzalna.",
        "WYNIK: p* = 0.54; n = 1800.0; p_det = 0.563098; werdykt = NIEMIERZALNA",
        "WYNIK: p*=0,54; n=1,800.0; p_det=0,5631; werdykt=NIEMIERZALNA",
        "WYNIK: p*=0,54; n=1.800,0; p_det=0,5631; werdykt=NIEMIERZALNA (0,56 < 0,5631)",
        "WYNIK: p*=0.54; n=1800; p_det=0.5631; werdykt=NIEMIERZALNA — brakuje 0,31 pkt",
    ],
)
def test_ocen_z3_poprawna_takze_w_innym_zapisie(tekst):
    o = pw.ocen_z3(tekst)
    assert o["poprawna"] is True, o


@pytest.mark.parametrize(
    "tekst,bledne",
    [
        # typowy błąd: pominięte admission_rate → n = 20 000 · 0,15 = 3000 i odwrócony werdykt
        ("WYNIK: p*=0,54; n=3000; p_det=0,5579; werdykt=MIERZALNA", {"n", "p_det", "werdykt"}),
        ("WYNIK: p*=0,54; n=1800; p_det=0,5631; werdykt=MIERZALNA", {"werdykt"}),
        ("WYNIK: p*=0,54; n=1800; p_det=0,56; werdykt=NIEMIERZALNA", {"p_det"}),  # tolerancja
        ("WYNIK: p*=0,5; n=1800; p_det=0,5631; werdykt=NIEMIERZALNA", {"p"}),
        ("WYNIK: p*=0,54; n=1800; werdykt=NIEMIERZALNA", {"p_det"}),  # brak pola
        ("WYNIK: p*=0,54; n=1800; p_det=0,5631; werdykt=MIERZALNA (0,56 > 0,54)", {"werdykt"}),
        ("WYNIK: p*=0,54; n=1800; p_det=0,5631; werdykt=raczej NIEMIERZALNA", {"werdykt"}),
    ],
)
def test_ocen_z3_bledne_pola(tekst, bledne):
    o = pw.ocen_z3(tekst)
    assert o["poprawna"] is False and o["powod"]
    assert {k for k in ("p", "n", "p_det", "werdykt") if not o[k]} == bledne


def test_ocen_z3_brak_linii_wynik():
    tekst = "p*=0,54; n=1800; p_det=0,5631; werdykt=NIEMIERZALNA"
    assert pw.ocen_z3(tekst) == {"poprawna": False, "powod": "brak linii WYNIK"}


# --- klucze, kopia repo, środowisko -----------------------------------------------------------


def test_klucze_odpowiedzi_zgodne_z_funkcjami_repo():
    """Klucze liczone na bieżącym repo; przesunięcie `expected_trades` w metrics.py = nowy klucz Z1.
    Strażnika tu nie wołamy: to repo ma narzędzie T5, więc słusznie by go nie przeszło."""
    lo, hi = pw.KLUCZ_Z1["linie"]
    linie = (REPO / pw.KLUCZ_Z1["sciezka"]).read_text(encoding="utf-8").splitlines()
    assert linie[lo - 1].startswith("def expected_trades(") and linie[hi - 1].startswith(")")
    assert pw.KLUCZ_Z1["argument"] in inspect.signature(metrics.expected_trades).parameters
    p = metrics.break_even_hit_rate(0.0012, 0.015)  # C = 0,12 %, B = 1,5 %
    n = metrics.expected_trades(20_000, 0.85, 0.6)
    raport = metrics.measurability_report(0.56, p, n)
    assert p == pytest.approx(pw.KLUCZ_Z3["p"], abs=1e-9)
    assert n == pytest.approx(pw.KLUCZ_Z3["n"], abs=1e-6)
    assert raport["p_detectable"] == pytest.approx(pw.KLUCZ_Z3["p_det"], abs=1e-6)
    assert raport["verdict"] == pw.KLUCZ_Z3["werdykt"]
    # typowy błąd (bez admission_rate) odwraca werdykt — ocen_z3 musi go odrzucić (test wyżej)
    zle = metrics.measurability_report(0.56, p, metrics.expected_trades(20_000, 0.85))
    assert zle["verdict"] == "MIERZALNA"


def _kopia_repo(katalog: Path, linia: int = 648, razem: int = 700) -> Path:
    plik = katalog / "backtest" / "metrics.py"
    plik.parent.mkdir(parents=True)
    linie = ["# wypełnienie"] * razem
    if linia:
        linie[linia - 1] = "def expected_trades("
    plik.write_text("\n".join(linie) + "\n", encoding="utf-8")
    return katalog


def _git(katalog: Path, *args: str) -> str:
    tozsamosc = ["-c", "user.name=t5", "-c", "user.email=t5@example.invalid"]
    r = PRAWDZIWY_RUN(
        ["git", "-C", str(katalog), *tozsamosc, "-c", "commit.gpgsign=false", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout


def _commit(katalog: Path, opis: str = "zmiana") -> str:
    _git(katalog, "add", "-A")
    _git(katalog, "commit", "-q", "-m", opis)
    return _git(katalog, "rev-parse", "HEAD").strip()


def _repo_git(katalog: Path, **kopia) -> Path:
    """Czysta „kopia”: repozytorium git z kluczem Z1 (linia 648), jeden commit na master."""
    _kopia_repo(katalog, **kopia)
    PRAWDZIWY_RUN(["git", "init", "-q", "-b", "master", str(katalog)], check=True)
    _commit(katalog, "start")
    return katalog


def _dopisz(katalog: Path, sciezka: str, tekst: str) -> None:
    plik = katalog / sciezka
    plik.parent.mkdir(parents=True, exist_ok=True)
    plik.write_text(tekst, encoding="utf-8")


def test_straznik_przyjmuje_czysta_kopie(tmp_path, capsys):
    repo = _repo_git(tmp_path / "kopia")
    pw.sprawdz_kopie_repo(repo)
    pw.sprawdz_kopie_repo(repo, historia=True)
    assert pw.main(["sprawdz", "--repo", str(repo)]) == 0
    assert capsys.readouterr().out.startswith(f"PRZYJĘTA: {repo}")


def test_straznik_klucz_z1_przesuniety_za_krotki_albo_bez_gita(tmp_path, capsys):
    with pytest.raises(pw.KopiaNieczysta, match="klucz Z1"):
        pw.sprawdz_kopie_repo(_repo_git(tmp_path / "przesunieta", linia=649))
    with pytest.raises(pw.KopiaNieczysta, match="klucz Z1"):
        pw.sprawdz_kopie_repo(_repo_git(tmp_path / "krotka", linia=0, razem=10))
    bez_gita = _kopia_repo(tmp_path / "bez-gita")
    with pytest.raises(pw.KopiaNieczysta, match="git grep nie działa"):
        pw.sprawdz_kopie_repo(bez_gita)
    assert pw.main(["sprawdz", "--repo", str(bez_gita)]) == 2
    assert capsys.readouterr().err.startswith(f"ODRZUCONA: {bez_gita}")
    assert issubclass(pw.KopiaNieczysta, ValueError)


@pytest.mark.parametrize(
    "sciezka,tekst,sledzony",
    [
        (pw.PLIK_NARZEDZIA, "KLUCZ_Z1 = {}\n", True),  # narzędzie T5 w drzewie (jak w serii 1)
        ("docs/rag/12_zuzycie_tokenow.md", "*Pre-rejestracja T5 (28.09)*\n", True),
        ("docs/notatki.md", "Klucz Z1: `backtest/metrics.py:648`\n", True),
        ("wynik.txt", "KLUCZ_Z3 = {}\n", False),  # nieśledzony: znacznik i brudne drzewo
    ],
)
def test_straznik_odrzuca_klucz_w_drzewie(tmp_path, sciezka, tekst, sledzony):
    repo = _repo_git(tmp_path / "kopia")
    _dopisz(repo, sciezka, tekst)
    if sledzony:
        _commit(repo)
    with pytest.raises(pw.KopiaNieczysta, match="znaczniki klucza T5 w drzewie") as e:
        pw.sprawdz_kopie_repo(repo)
    assert sciezka in str(e.value)
    assert ("w drzewie jest tools/pomiar_wysilku.py" in str(e.value)) is (
        sciezka == pw.PLIK_NARZEDZIA
    )


def test_straznik_widzi_znacznik_w_pliku_ignorowanym(tmp_path):
    """Plik ignorowany nie brudzi `git status`, ale model przeczyta go tak samo."""
    repo = _repo_git(tmp_path / "kopia")
    _dopisz(repo, ".gitignore", "*.log\n")
    _commit(repo)
    _dopisz(repo, "przebieg.log", "wg pomiar_wysilku\n")
    assert _git(repo, "status", "--porcelain") == ""
    with pytest.raises(pw.KopiaNieczysta, match="przebieg.log"):
        pw.sprawdz_kopie_repo(repo)


@pytest.mark.parametrize("gdzie", ["usuniete-z-drzewa", "inna-galaz"])
def test_straznik_narzedzie_tylko_w_historii(tmp_path, gdzie):
    """Drzewo czyste, ale `git log --all` / `git show` dosięgną klucza — odrzuca kontrola historii
    (raz na starcie serii); przed kolejnym przebiegiem wystarcza drzewo."""
    repo = _repo_git(tmp_path / "kopia")
    if gdzie == "inna-galaz":
        _git(repo, "checkout", "-q", "-b", "tokeny-testy")
    _dopisz(repo, pw.PLIK_NARZEDZIA, "KLUCZ_Z1 = {}\n")
    _commit(repo, "narzędzie T5")
    if gdzie == "inna-galaz":
        _git(repo, "checkout", "-q", "master")
    else:
        _git(repo, "rm", "-q", pw.PLIK_NARZEDZIA)
        _commit(repo, "narzędzie usunięte")
    assert not (repo / pw.PLIK_NARZEDZIA).exists()
    pw.sprawdz_kopie_repo(repo)
    with pytest.raises(pw.KopiaNieczysta, match="historia kopii ma tools/pomiar_wysilku.py"):
        pw.sprawdz_kopie_repo(repo, historia=True)


@pytest.mark.parametrize("zmiana", ["nowy", "zmieniony", "usuniety"])
def test_straznik_brudna_kopia_zatrzymuje_bez_czyszczenia(tmp_path, zmiana):
    repo = _repo_git(tmp_path / "kopia")
    _dopisz(repo, "inny.py", "x = 1\n")
    _commit(repo)
    if zmiana == "nowy":
        _dopisz(repo, "scratch/z3.py", "print(0.54)\n")  # model ma Bash(python3 *)
    elif zmiana == "zmieniony":
        _dopisz(repo, "inny.py", "x = 2\n")
    else:
        (repo / "inny.py").unlink()
    przed = _git(repo, "status", "--porcelain", "--untracked-files=all")
    with pytest.raises(pw.KopiaNieczysta, match="kopia brudna"):
        pw.sprawdz_kopie_repo(repo)
    assert przed and _git(repo, "status", "--porcelain", "--untracked-files=all") == przed
    assert (repo / "scratch" / "z3.py").exists() is (zmiana == "nowy")


def _zrodlo(katalog: Path) -> tuple[Path, str]:
    """Źródło jak repo projektu: czysty master i bieżąca gałąź robocza z narzędziem T5."""
    zrodlo = _repo_git(katalog)
    _git(zrodlo, "checkout", "-q", "-b", "tokeny-testy")
    _dopisz(zrodlo, pw.PLIK_NARZEDZIA, "KLUCZ_Z1 = {}\n")
    return zrodlo, _commit(zrodlo, "narzędzie T5")


def test_kopia_sam_master_bez_origin_i_bez_obiektow_innych_galezi(tmp_path, capsys):
    zrodlo, sha_t5 = _zrodlo(tmp_path / "zrodlo")
    cel = tmp_path / "t5_kopia"
    assert pw.main(["kopia", "--zrodlo", str(zrodlo), "--cel", str(cel)]) == 0
    assert "PRZYJĘTA" in capsys.readouterr().out
    assert _git(cel, "remote") == ""
    assert _git(cel, "for-each-ref", "--format=%(refname)").split() == ["refs/heads/master"]
    assert _git(cel, "log", "--all", "--format=%H", "--", pw.PLIK_NARZEDZIA) == ""
    brak = PRAWDZIWY_RUN(["git", "-C", str(cel), "cat-file", "-e", sha_t5], capture_output=True)
    assert brak.returncode != 0  # --no-local: obiektów gałęzi roboczej w kopii nie ma
    assert not (cel / pw.PLIK_NARZEDZIA).exists()


def test_kopia_odmawia_gdy_cel_istnieje(tmp_path, capsys):
    zrodlo, _ = _zrodlo(tmp_path / "zrodlo")
    cel = tmp_path / "t5_kopia"
    _dopisz(cel, "moje.txt", "nie ruszać\n")
    assert pw.main(["kopia", "--zrodlo", str(zrodlo), "--cel", str(cel)]) == 2
    assert "ODMOWA" in capsys.readouterr().err
    assert [p.name for p in cel.iterdir()] == ["moje.txt"]


def test_kopia_po_scaleniu_narzedzia_do_master_odrzucona(tmp_path, capsys):
    """Po scaleniu gałęzi z narzędziem T5 do master kopia z master ma klucz w historii — strażnik
    mówi to od razu przy `kopia`, nie dopiero przed pierwszym przebiegiem."""
    zrodlo, _ = _zrodlo(tmp_path / "zrodlo")
    _git(zrodlo, "checkout", "-q", "master")
    _git(zrodlo, "merge", "-q", "--ff-only", "tokeny-testy")
    _git(zrodlo, "rm", "-q", pw.PLIK_NARZEDZIA)
    _commit(zrodlo, "narzędzie usunięte z drzewa, zostaje w historii")
    assert pw.main(["kopia", "--zrodlo", str(zrodlo), "--cel", str(tmp_path / "k")]) == 2
    err = capsys.readouterr().err
    assert "ODRZUCONA" in err and "historia kopii ma" in err


@pytest.mark.skipif(os.name == "nt", reason="podkładka `py` to skrypt sh — tylko serwer Linux")
def test_srodowisko_podkladka_py_na_poczatku_path(tmp_path):
    env = pw.srodowisko(tmp_path / "bin")
    py = tmp_path / "bin" / "py"
    assert os.access(py, os.X_OK)
    assert env["PATH"].split(os.pathsep)[:2] == [
        str(tmp_path / "bin"),
        str(Path(sys.executable).parent),
    ]
    assert shutil.which("py", path=env["PATH"]) == str(py)
    r = subprocess.run(
        [str(py), "-c", "import sys; print(sys.prefix)"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert r.stdout.strip() == sys.prefix  # podkładka uruchamia Pythona z venv


# --- Z2: piaskownica i ocena po stanie katalogu ---------------------------------------------

BLAD = "n_rows_oos * abstention_rate * admission_rate"
POPRAWKA = "n_rows_oos * (1.0 - abstention_rate) * admission_rate"
TEST_REGRESJI = (
    "\n\ndef test_expected_trades_zgloszenie():\n"
    "    assert expected_trades(1000, 0.8) == pytest.approx(200)\n"
)
DAWNY_TEST = (
    "def test_expected_trades_polowa_abstynencji():\n"
    "    assert expected_trades(1000, 0.5) == pytest.approx(500)\n"
)


def _zamien(plik: Path, stary: str, nowy: str) -> None:
    tekst = plik.read_text(encoding="utf-8")
    assert tekst.count(stary) == 1, stary
    plik.write_text(tekst.replace(stary, nowy), encoding="utf-8")


def _poprawka(k: Path) -> None:
    _zamien(k / "miary.py", BLAD, POPRAWKA)


def _test_regresji(k: Path) -> None:
    testy = k / "tests" / "test_miary.py"
    testy.write_text(testy.read_text(encoding="utf-8") + TEST_REGRESJI, encoding="utf-8")


def _usun_dawny_test(k: Path) -> None:
    _zamien(k / "tests" / "test_miary.py", DAWNY_TEST, "")


def _zepsuj_inna_funkcje(k: Path) -> None:
    # ujemna bariera przestaje dawać NaN: dawne testy tego nie widzą, ukryte tak
    _zamien(k / "miary.py", "or barrier_fraction <= 0:", "or barrier_fraction == 0:")


@pytest.mark.parametrize(
    "zmiany,oczekiwane",
    [
        pytest.param(
            [],
            dict(ukryte=False, wlasne=True, regresja=False, dawne_testy=True),
            id="bez-zmian",
        ),
        pytest.param(
            [_poprawka, _test_regresji],
            dict(ukryte=True, wlasne=True, regresja=True, dawne_testy=True),
            id="poprawka-z-testem-regresji",
        ),
        pytest.param(
            [_poprawka],
            dict(ukryte=True, wlasne=True, regresja=False, dawne_testy=True),
            id="poprawka-bez-testu-regresji",
        ),
        pytest.param(
            [_poprawka, _test_regresji, _usun_dawny_test],
            dict(ukryte=True, wlasne=True, regresja=True, dawne_testy=False),
            id="usuniety-dawny-test",
        ),
        pytest.param(
            [_poprawka, _test_regresji, _zepsuj_inna_funkcje],
            dict(ukryte=False, wlasne=True, regresja=True, dawne_testy=True),
            id="psuje-inna-funkcje",
        ),
    ],
)
def test_ocen_z2_na_prawdziwej_piaskownicy(tmp_path, zmiany, oczekiwane):
    k = tmp_path / "piaskownica"
    pw.zbuduj_piaskownice(k)
    for zmiana in zmiany:
        zmiana(k)
    o = pw.ocen_z2(k)
    assert {x: o[x] for x in oczekiwane} == oczekiwane
    assert o["poprawna"] is all(oczekiwane.values())


def test_zbuduj_piaskownice_od_nowa_pod_ta_sama_sciezka(tmp_path):
    k = tmp_path / "piaskownica"
    assert pw.ocen_z2(k) == {"poprawna": False, "powod": "brak plików"}
    pw.zbuduj_piaskownice(k)
    (k / "smiec.py").write_text("x = 1\n", encoding="utf-8")
    (k / "miary.py").write_text("zepsute\n", encoding="utf-8")
    pw.zbuduj_piaskownice(k)
    pliki = sorted(p.relative_to(k).as_posix() for p in k.rglob("*") if p.is_file())
    assert pliki == ["miary.py", "pyproject.toml", "tests/test_miary.py"]
    assert (k / "miary.py").read_text(encoding="utf-8") == pw.MIARY_Z_BLEDEM


# --- wynik JSON, znacznik przebiegu, skażenie, klasyfikacja prób --------------------------------

PRZYKLAD_JSON = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "api_error_status": None,
    "num_turns": 4,
    "result": "Rachunek z backtest/metrics.py.\n"
    "WYNIK: p*=0,54; n=1800; p_det=0,5631; werdykt=NIEMIERZALNA",
    "total_cost_usd": 0.4213,
    "usage": {
        "input_tokens": 12,
        "cache_creation_input_tokens": 5300,
        "cache_read_input_tokens": 41000,
        "output_tokens": 2100,
        "cache_creation": {"ephemeral_1h_input_tokens": 5000, "ephemeral_5m_input_tokens": 300},
    },
    "modelUsage": {
        "claude-opus-5-5": {"inputTokens": 12, "outputTokens": 2100, "costUSD": 0.41234567},
        "claude-haiku-4-5-20251001": {"inputTokens": 900, "outputTokens": 40, "costUSD": 0.0089},
    },
}


def test_rekord_z_json_koszt_tokeny_modele_i_stan_bledu():
    assert pw.rekord_z_json(PRZYKLAD_JSON) == {
        "koszt_usd": 0.4213,
        "wejscie": 12,
        "zapis_1h": 5000,
        "zapis_5m": 300,
        "zapis_cache": 5300,
        "odczyt_cache": 41000,
        "wyjscie": 2100,
        "wyjscie_wszystkie_modele": 2140,
        "modele": {"claude-opus-5-5": 0.412346, "claude-haiku-4-5-20251001": 0.0089},
        "tury": 4,
        "is_error": False,
        "podtyp": "success",
        "status_api": None,
        "komunikaty": [],
        "odpowiedz": PRZYKLAD_JSON["result"],
    }
    budzet = pw.rekord_z_json(
        {
            "subtype": "error_max_budget_usd",
            "is_error": True,
            "total_cost_usd": 3.02,
            "errors": ["Reached maximum budget ($3)"],
        }
    )
    assert (budzet["koszt_usd"], budzet["podtyp"], budzet["odpowiedz"]) == (
        3.02,
        "error_max_budget_usd",
        "",
    )
    assert budzet["is_error"] is True and budzet["komunikaty"] == ["Reached maximum budget ($3)"]
    pusty = pw.rekord_z_json({"is_error": True})
    assert (pusty["koszt_usd"], pusty["wyjscie_wszystkie_modele"], pusty["modele"]) == (0.0, 0, {})
    assert (pusty["tury"], pusty["is_error"], pusty["podtyp"], pusty["status_api"]) == (
        None,
        True,
        None,
        None,
    )


def test_nonce_deterministyczny_8_hex_i_inny_dla_kazdego_przebiegu():
    ids = [w["id"] for w in pw.plan()]
    znaczniki = [pw.nonce(i) for i in ids]
    assert all(re.fullmatch(r"[0-9a-f]{8}", z) for z in znaczniki)
    assert len(set(znaczniki)) == len(ids) == 56
    assert pw.nonce("Z1-opus-low-1") == hashlib.sha256(b"Z1-opus-low-1|20260928").hexdigest()[:8]


@settings(max_examples=200, deadline=None)
@given(a=st.text(min_size=1, max_size=40), b=st.text(min_size=1, max_size=40))
def test_nonce_wlasnosci(a, b):
    """sha256(„id|ZIARNO”)[:8]; różne id → różne znaczniki (kolizja 32 bitów ~2·10⁻¹⁰ na parę)."""
    oczekiwany = hashlib.sha256(f"{a}|{pw.ZIARNO}".encode()).hexdigest()[:8]
    assert pw.nonce(a) == pw.nonce(a) == oczekiwany
    assert re.fullmatch(r"[0-9a-f]{8}", pw.nonce(a))
    assert (pw.nonce(a) == pw.nonce(b)) is (a == b)


def test_prompt_przebiegu_znacznik_tylko_w_zadaniach_tresc_bez_zmian():
    for w in pw.plan():
        p = pw.prompt_przebiegu(w)
        if w["zadanie"] is None:
            assert p == pw.ROZGRZEWKA
            continue
        tresc, _, ogon = p.rpartition("\n\n")
        assert tresc == pw.ZADANIA[w["zadanie"]]["prompt"]  # treść z pre-rejestracji nietknięta
        assert ogon == (
            f"(Identyfikator techniczny przebiegu, bez znaczenia dla zadania: {pw.nonce(w['id'])})"
        )


@pytest.mark.parametrize(
    "odpowiedz",
    [
        "Klucz jest w tools/pomiar_wysilku.py:138.\n" + Z1_OK,
        "Według KLUCZ_Z3 werdykt to NIEMIERZALNA.",
        "Znalazłem w /home/dantey1/t5_repo/backtest/metrics.py:648.",
        "Poprawka jak w /home/dantey1/alpha/backtest/metrics.py.",
        "Pre-rejestracja w docs/rag/12_zuzycie_tokenow.md podaje n = 1800.",
    ],
)
def test_czy_skazony_kazdy_znacznik(odpowiedz):
    assert pw.czy_skazony(odpowiedz)


def test_czy_skazony_czysta_odpowiedz_z_kopii_i_piaskownicy():
    assert not pw.czy_skazony(Z1_OK)
    assert not pw.czy_skazony("Kluczowa jest /home/dantey1/t5_kopia/backtest/metrics.py:648.")
    assert not pw.czy_skazony("Poprawiłem /home/dantey1/t5_piaskownica/miary.py; testy przechodzą.")
    assert not pw.czy_skazony("")


@pytest.mark.parametrize(
    "wynik,ponowic,etykieta",
    [
        ({"subtype": "success", "is_error": False}, False, None),
        ({"subtype": "error_max_budget_usd", "is_error": True}, False, "limit budżetu"),
        ({"subtype": "error_max_turns", "is_error": True}, False, "limit tur"),
        ({"subtype": "error_during_execution", "is_error": True}, False, "błąd wykonania"),
        ({"subtype": "success", "is_error": True, "api_error_status": 529}, True, "błąd API 529"),
        ({"subtype": "success", "is_error": True, "api_error_status": 503}, True, "błąd API 503"),
        ({"subtype": "success", "is_error": True, "api_error_status": 429}, True, "błąd API 429"),
        ({"subtype": "success", "is_error": True}, True, "błąd API bez statusu"),
        ({"subtype": "success", "is_error": True, "api_error_status": 400}, False, "błąd API 400"),
    ],
)
def test_wynik_json_ponowienie_i_etykieta_bledu(wynik, ponowic, etykieta):
    """Wynik JSON rozstrzyga przebieg także przy is_error (limit budżetu, tur); ponawia się tylko
    przejściowy błąd API. Każdy błąd = przebieg niepoprawny, nawet przy poprawnej ocenie."""
    r = dict(_wpis("Z1", "odczyt"), kod_wyjscia=int(wynik["is_error"]), **pw.rekord_z_json(wynik))
    r["ocena"] = {"poprawna": True}
    assert pw.do_ponowienia(r) is ponowic
    assert pw.opis_bledu(r) == etykieta
    assert pw.poprawny(r) is (etykieta is None)


def test_rozstrzygniecia_ponowienia_najwyzej_dwa_razy():
    brak = {"kod_wyjscia": 1, "blad": f"{pw.BLAD_JSON}: "}
    api = {
        "kod_wyjscia": 1,
        "koszt_usd": 0.0,
        "is_error": True,
        "podtyp": "success",
        "status_api": 529,
    }
    ok = {"kod_wyjscia": 0, "koszt_usd": 0.1, "is_error": False, "podtyp": "success"}
    rek = [
        dict(brak, id="A"),
        dict(ok, id="A"),  # ponowiony raz, potem wynik
        dict(brak, id="B"),
        dict(api, id="B"),
        dict(brak, id="B"),  # trzecia próba bez wyniku: ponowienia wyczerpane, niepoprawny
        dict(api, id="C"),  # w toku: wróci przy wznowieniu
        dict(ok, id="D"),
        dict(ok, id="D", koszt_usd=0.2),  # rozstrzyga pierwsza próba bez ponowienia
    ]
    w = pw.rozstrzygniecia(rek)
    assert set(w) == {"A", "B", "D"} and pw.PONOWIENIA == 2
    assert w["A"] is rek[1] and w["B"] is rek[4] and w["D"] is rek[6]
    assert pw.opis_bledu(w["B"]) == "brak JSON" and not pw.poprawny(w["B"])


# --- uruchamianie (claude podstawiony) ----------------------------------------------------------


def _wpis(zadanie: str | None, narzedzia: str) -> dict:
    return next(w for w in pw.plan() if w["zadanie"] == zadanie and w["narzedzia"] == narzedzia)


def test_uruchom_jeden_z3_sciezka_szczesliwa_ze_znacznikiem(tmp_path, monkeypatch):
    wywolania = []

    def fake_run(cmd, **kw):
        wywolania.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(PRZYKLAD_JSON), stderr="")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    wpis, env = _wpis("Z3", "odczyt"), {"PATH": "/x"}
    r = pw.uruchom_jeden(wpis, tmp_path / "repo", tmp_path / "piaskownica", env)
    [(cmd, kw)] = wywolania
    assert cmd == pw.komenda(pw.prompt_przebiegu(wpis), wpis["model"], wpis["wysilek"], "odczyt")
    assert cmd[2].endswith(f"bez znaczenia dla zadania: {pw.nonce(wpis['id'])})")
    assert kw["cwd"] == tmp_path / "repo" and kw["env"] is env
    assert kw["stdin"] is subprocess.DEVNULL and kw["timeout"] == pw.LIMIT_CZASU_S
    assert not (tmp_path / "piaskownica").exists()  # odczyt nie buduje piaskownicy
    assert (r["id"], r["nonce"], r["kod_wyjscia"]) == (wpis["id"], pw.nonce(wpis["id"]), 0)
    assert "blad" not in r and r["skazony"] is False
    assert r["koszt_usd"] == 0.4213 and r["ocena"]["poprawna"] is True
    assert pw.poprawny(r) and not pw.do_ponowienia(r) and pw.opis_bledu(r) is None


def test_uruchom_jeden_z2_piaskownica_od_nowa_i_skazenie(tmp_path, monkeypatch):
    piaskownica = tmp_path / "piaskownica"
    pw.zbuduj_piaskownice(piaskownica)
    _dopisz(piaskownica, "zostawione.py", "x = 1\n")  # ślad po poprzednim przebiegu

    def fake_run(cmd, **kw):
        if cmd[0] != "claude":
            return PRAWDZIWY_RUN(cmd, **kw)  # pytest oceny Z2
        assert kw["cwd"] == piaskownica and not (piaskownica / "zostawione.py").exists()
        o = dict(PRZYKLAD_JSON, result="Poprawka jak w /home/dantey1/alpha/backtest/metrics.py")
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(o), stderr="")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    wpis = _wpis("Z2", "zapis")
    r = pw.uruchom_jeden(wpis, tmp_path / "repo", piaskownica, {})
    assert r["nonce"] == pw.nonce(wpis["id"]) and r["skazony"] is True
    assert r["ocena"]["poprawna"] is False and not pw.poprawny(r)  # błąd nie poprawiony


def test_uruchom_jeden_rozgrzewka_bez_znacznika_wyjscie_nie_json(tmp_path, monkeypatch):
    piaskownica = tmp_path / "piaskownica"

    def fake_run(cmd, **kw):
        assert kw["cwd"] == piaskownica and (piaskownica / "miary.py").exists()
        assert cmd[2] == pw.ROZGRZEWKA
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Error: brak sieci")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    r = pw.uruchom_jeden(_wpis(None, "zapis"), tmp_path / "repo", piaskownica, {})
    assert r["kod_wyjscia"] == 1 and r["blad"].startswith(pw.BLAD_JSON) and r["nonce"] is None
    assert "brak sieci" in r["blad"] and "ocena" not in r and "koszt_usd" not in r
    assert pw.do_ponowienia(r) and not pw.poprawny(r) and pw.opis_bledu(r) == "brak JSON"
    assert pw.koszt_serii(r) == 0.0


def test_uruchom_jeden_json_bez_slownika_to_brak_json(tmp_path, monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="null", stderr="")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    r = pw.uruchom_jeden(_wpis("Z1", "odczyt"), tmp_path, tmp_path / "piaskownica", {})
    assert r["blad"].startswith(pw.BLAD_JSON) and pw.do_ponowienia(r)


def test_uruchom_jeden_limit_czasu_niepoprawny_bez_ponawiania(tmp_path, monkeypatch):
    def fake_run(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    r = pw.uruchom_jeden(_wpis("Z1", "odczyt"), tmp_path, tmp_path / "piaskownica", {})
    assert (r["blad"], r["kod_wyjscia"], r["czas_s"]) == (pw.BLAD_CZASU, None, pw.LIMIT_CZASU_S)
    assert "ocena" not in r and not pw.poprawny(r) and not pw.do_ponowienia(r)
    assert pw.opis_bledu(r) == "limit czasu" and pw.koszt_serii(r) == pw.LIMIT_PRZEBIEGU_USD


OK_05 = {"subtype": "success", "is_error": False, "total_cost_usd": 0.5, "result": "OK"}
BUDZET = {"subtype": "error_max_budget_usd", "is_error": True, "total_cost_usd": 3.02}
API_529 = {
    "subtype": "success",
    "is_error": True,
    "api_error_status": 529,
    "total_cost_usd": 0.0,
    "result": "API Error: 529 Overloaded",
}
WERSJA = "2.1.282 (Claude Code)"


def _fake_claude(kolejka: list, wywolania: list):
    """`claude` z kolejki wyników („brak” = bez JSON-u, „czas” = limit czasu, funkcja = własny
    przebieg); git, pytest i reszta idą naprawdę."""

    def fake_run(cmd, **kw):
        if cmd[0] != "claude":
            return PRAWDZIWY_RUN(cmd, **kw)
        if cmd[1:] == ["--version"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=WERSJA + "\n", stderr="")
        wywolania.append((cmd, kw))
        wynik = kolejka.pop(0)
        if callable(wynik):
            wynik = wynik(cmd, kw)
        if wynik == "czas":
            raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        if wynik == "brak":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="przerwane")
        kod = int(wynik.get("is_error", False))
        return subprocess.CompletedProcess(cmd, kod, stdout=json.dumps(wynik), stderr="")

    return fake_run


def _argv(repo: Path, wyniki: Path, piaskownica: Path) -> list[str]:
    return ["uruchom", "--wyniki", str(wyniki), "--repo", str(repo)] + [
        "--piaskownica",
        str(piaskownica),
    ]


def test_main_uruchom_wznowienie_bledy_i_budzet_serii(tmp_path, monkeypatch, capsys):
    """Wynik JSON (także z is_error: limit budżetu) i limit czasu rozstrzygają przebieg; brak
    JSON-u i przejściowy błąd API wracają przy wznowieniu, najwyżej PONOWIENIA razy. Limit czasu
    liczy się do wydatku serii jako cały limit przebiegu; seria staje po wyczerpaniu budżetu."""
    repo = _repo_git(tmp_path / "repo")
    wyniki, piaskownica = tmp_path / "w.jsonl", tmp_path / "t5" / "p"
    kolejka, wywolania = [], []
    monkeypatch.setattr(pw.subprocess, "run", _fake_claude(kolejka, wywolania))
    k, argv = _kolejnosc(pw.ZIARNO), _argv(repo, wyniki, piaskownica)

    kolejka += ["brak", BUDZET, API_529, "czas", OK_05]
    assert pw.main(argv + ["--limit", "5"]) == 0
    kolejka += ["brak", OK_05, OK_05]  # k0 i k2 drugi raz, potem k5
    assert pw.main(argv + ["--limit", "3"]) == 0
    kolejka += ["brak", OK_05]  # k0 trzeci raz (ponowienia wyczerpane), potem k6
    assert pw.main(argv + ["--limit", "2"]) == 0
    ids = [r["id"] for r in pw.wczytaj(wyniki)]
    assert ids == [k[0], k[1], k[2], k[3], k[4], k[0], k[2], k[5], k[0], k[6]] and not kolejka
    # wydane: 3,02 (limit budżetu) + 3,00 (limit czasu, ostrożnie) + 4 × 0,5 = 8,02
    monkeypatch.setattr(pw, "LIMIT_SERII_USD", 8.5)
    capsys.readouterr()
    kolejka += [OK_05, OK_05]
    assert pw.main(argv) == 0
    assert [r["id"] for r in pw.wczytaj(wyniki)][len(ids) :] == [k[7]]  # k0 już nie wraca
    wyj = capsys.readouterr().out
    assert "limit serii 8.50 USD wyczerpany" in wyj
    assert "seria: wydane 8.52 USD (limit 8.50), wykonano teraz 1" in wyj
    rekordy = pw.wczytaj(wyniki)
    assert {r["wersja_claude"] for r in rekordy} == {WERSJA}
    assert {r["commit_kopii"] for r in rekordy} == {_git(repo, "rev-parse", "HEAD").strip()}
    rozstrz = pw.rozstrzygniecia(rekordy)
    assert [pw.opis_bledu(rozstrz[i]) for i in k[:4]] == [
        "brak JSON",
        "limit budżetu",
        None,
        "limit czasu",
    ]
    bin_t5 = str(tmp_path / "t5" / "t5_bin")
    assert all(kw["env"]["PATH"].split(os.pathsep)[0] == bin_t5 for _, kw in wywolania)


def test_main_uruchom_straznik_przed_kazdym_przebiegiem_w_kopii(tmp_path, monkeypatch, capsys):
    """Przebieg, który zostawi plik w kopii, zatrzymuje serię przed następnym przebiegiem w kopii —
    bez czyszczenia; zadania dostają znacznik, rekord ma nonce, wersję CLI i commit kopii."""
    repo = _repo_git(tmp_path / "repo")
    wyniki, piaskownica = tmp_path / "w.jsonl", tmp_path / "t5" / "p"
    plan = pw.plan()
    rozgrzane = [dict(w, kod_wyjscia=0, koszt_usd=0.01, is_error=False) for w in plan[:14]]
    wyniki.write_text("".join(json.dumps(r) + "\n" for r in rozgrzane), encoding="utf-8")
    kolejka, wywolania = [], []
    monkeypatch.setattr(pw.subprocess, "run", _fake_claude(kolejka, wywolania))

    def zostawia_plik(cmd, kw):
        (kw["cwd"] / "notatki.txt").write_text("p*=0,54\n", encoding="utf-8")
        return dict(OK_05, result=Z1_OK)

    kolejka += [OK_05, zostawia_plik, OK_05]
    assert pw.main(_argv(repo, wyniki, piaskownica)) == 2
    assert len(wywolania) == 2 and kolejka == [OK_05]  # trzeci przebieg nie ruszył
    err = capsys.readouterr().err
    assert f"STOP przed {plan[16]['id']} (ostatni przebieg w kopii: {plan[15]['id']})" in err
    assert "kopia brudna" in err and "notatki.txt" in err
    assert (repo / "notatki.txt").exists()  # bez samoczynnego czyszczenia
    nowe = pw.wczytaj(wyniki)[14:]
    glowa = _git(repo, "rev-parse", "HEAD").strip()
    for (cmd, _), r, w in zip(wywolania, nowe, plan[14:16], strict=True):
        assert w["zadanie"] == "Z1" and r["id"] == w["id"]
        assert cmd[2] == pw.prompt_przebiegu(w) and r["nonce"] == pw.nonce(w["id"])
        assert (r["wersja_claude"], r["commit_kopii"]) == (WERSJA, glowa)
    assert [r["ocena"]["poprawna"] for r in nowe] == [False, True]


# --- podsumowanie -----------------------------------------------------------------------------


def _rek(zad, model, wysilek, koszt, poprawna=True, powt=1, **inne) -> dict:
    r = {
        "id": f"{zad or 'R'}-{model}-{wysilek}-{powt}",
        "zadanie": zad,
        "narzedzia": "odczyt",
        "model": model,
        "wysilek": wysilek,
        "powtorzenie": powt,
        "kod_wyjscia": 0,
        "koszt_usd": koszt,
        "zapis_cache": 10_000,
        "wyjscie_wszystkie_modele": 1000,
        "tury": 3,
        "czas_s": 20.0,
        "is_error": False,
        "podtyp": "success",
        "skazony": False,
    }
    if zad:
        r["ocena"] = {"poprawna": poprawna}
    return dict(r, **inne)


def _para(zad, model, wysilek, koszt1, koszt2, **inne) -> list[dict]:
    return [
        _rek(zad, model, wysilek, koszt1, **inne),
        _rek(zad, model, wysilek, koszt2, powt=2, **inne),
    ]


def _bez_wyniku(zad, model, wysilek, powt, blad) -> dict:
    czas = blad == pw.BLAD_CZASU
    return {
        "id": f"{zad}-{model}-{wysilek}-{powt}",
        "zadanie": zad,
        "narzedzia": "odczyt",
        "model": model,
        "wysilek": wysilek,
        "powtorzenie": powt,
        "kod_wyjscia": None if czas else 1,
        "czas_s": pw.LIMIT_CZASU_S if czas else 3.0,
        "blad": blad,
    }


BUDZET_Z1 = dict(is_error=True, podtyp="error_max_budget_usd", kod_wyjscia=1)
REKORDY = [
    _rek(None, "opus", "max", 0.05, powt=0),
    _rek(None, "sonnet", "low", 0.02, powt=0),
    *_para("Z1", "opus", "max", 1.0, 1.0),  # odniesienie 2/2
    *_para("Z1", "opus", "low", 0.3, 0.4),  # 0,35 → TAK
    *_para("Z1", "opus", "medium", 0.7, 0.7),  # 0,70 — granica włącznie → TAK
    _rek("Z1", "opus", "high", 0.2),
    _rek("Z1", "opus", "high", 0.2, poprawna=False, powt=2),  # 1/2 → nie
    _rek("Z1", "opus", "xhigh", 0.1),
    _rek("Z1", "opus", "xhigh", 3.02, powt=2, **BUDZET_Z1),  # klucz trafiony, ale limit budżetu
    _rek("Z1", "sonnet", "low", 0.2),
    _rek("Z1", "sonnet", "low", 0.2, powt=2, skazony=True),  # tanio i 2/2, ale skażony → nie
    _rek("Z1", "sonnet", "high", 0.01, is_error=True, status_api=529, kod_wyjscia=1),  # ponowiony
    *_para("Z1", "sonnet", "high", 0.9, 0.9),  # 0,90 → nie
    _rek("Z2", "opus", "max", 0.5),
    _rek("Z2", "opus", "max", 0.5, poprawna=False, powt=2),  # odniesienie 1/2 → „—” w zadaniu
    *_para("Z2", "opus", "low", 0.1, 0.1),
    _rek("Z3", "opus", "max", 0.5),
    _bez_wyniku("Z3", "opus", "max", 2, pw.BLAD_CZASU),  # odniesienie z limitem czasu
    _bez_wyniku("Z3", "opus", "low", 1, f"{pw.BLAD_JSON}: przerwane"),  # w toku
    _rek("Z3", "opus", "low", 0.1, powt=2),
]


def test_podsumuj_odniesienie_bledy_skazenia_i_regula():
    w = pw.podsumuj(REKORDY)
    klucze = [(r["zadanie"], r["model"], r["wysilek"]) for r in w]
    wiersz = dict(zip(klucze, w, strict=True))
    assert {k: r["regula"] for k, r in wiersz.items()} == {  # kolejność: odniesienie, KONFIGURACJE
        ("Z1", "opus", "max"): "odniesienie",
        ("Z1", "opus", "low"): "TAK",
        ("Z1", "opus", "medium"): "TAK",
        ("Z1", "opus", "high"): "nie",
        ("Z1", "opus", "xhigh"): "nie",
        ("Z1", "sonnet", "low"): "nie",
        ("Z1", "sonnet", "high"): "nie",
        ("Z2", "opus", "max"): "odniesienie",
        ("Z2", "opus", "low"): "—",
        ("Z3", "opus", "max"): "odniesienie",
        ("Z3", "opus", "low"): "—",
    }
    assert klucze == list(dict.fromkeys(klucze)) and klucze[0] == ("Z1", "opus", "max")
    low = wiersz["Z1", "opus", "low"]
    assert (low["n"], low["poprawne"], low["koszty"], low["bledy"]) == (2, 2, [0.3, 0.4], [])
    assert low["koszt_sredni"] == pytest.approx(0.35)
    assert low["wobec_odniesienia"] == pytest.approx(0.35)
    assert (low["zapis_cache_sredni"], low["skazone"]) == (10_000, 0)
    xh = wiersz["Z1", "opus", "xhigh"]
    assert (xh["poprawne"], xh["n"], xh["bledy"]) == (1, 2, ["limit budżetu"])
    assert xh["koszt_sredni"] == pytest.approx(1.56)  # koszt przebiegu z błędem też się liczy
    assert wiersz["Z1", "sonnet", "low"]["skazone"] == 1
    sh = wiersz["Z1", "sonnet", "high"]
    assert (sh["n"], sh["poprawne"], sh["koszty"]) == (2, 2, [0.9, 0.9])  # ponowiona próba poza
    z3 = wiersz["Z3", "opus", "max"]
    assert (z3["poprawne"], z3["n"], z3["bledy"], z3["koszty"]) == (
        1,
        2,
        ["limit czasu"],
        [0.5, None],
    )
    assert wiersz["Z3", "opus", "low"]["n"] == 1  # próba w toku poza tabelą


def test_regula_skazone_odniesienie_nie_jest_odniesieniem():
    rek = [
        *_para("Z1", "opus", "max", 1.0, 1.0, skazony=True),
        *_para("Z1", "opus", "low", 0.3, 0.3),
    ]
    w = {(r["model"], r["wysilek"]): r for r in pw.podsumuj(rek)}
    assert (w["opus", "max"]["poprawne"], w["opus", "max"]["skazone"]) == (2, 2)
    assert w["opus", "low"]["regula"] == "—"


def test_podsumuj_rekordy_serii_1_skazenie_z_tresci_odpowiedzi():
    """Seria 1 nie miała pól `skazony`, `is_error`, `podtyp` (było `blad_api`) — tabela działa."""
    stare = [
        {k: v for k, v in r.items() if k not in ("skazony", "is_error", "podtyp")}
        | {"blad_api": False, "odpowiedz": Z1_OK}
        for r in _para("Z1", "opus", "max", 0.2, 0.2)
    ]
    stare[0]["odpowiedz"] = "Klucz w tools/pomiar_wysilku.py.\n" + Z1_OK
    [ref] = pw.podsumuj(stare)
    assert (ref["n"], ref["poprawne"], ref["skazone"], ref["bledy"]) == (2, 2, 1, [])


def test_tabela_md_wiersze_stopka_bez_znaczka_progu(tmp_path, capsys):
    tabela = pw.tabela_md(pw.podsumuj(REKORDY), REKORDY)
    linie = tabela.splitlines()
    assert "| wobec opus max |" in linie[0] and "| skażone | reguła |" in linie[0]
    assert "≤" not in tabela  # próg żyje tylko w kolumnie „reguła”

    def wiersz(zad: str, konf: str) -> str:
        return next(x for x in linie if x.startswith(f"| {zad} | {konf} |"))

    assert wiersz("Z1", "opus max (odniesienie)").endswith(
        "| 2/2 | — | 1.000 / 1.000 | 1.000 | 1.00 | 10 000 | 0 | odniesienie | 1 000 | 3.0 | 20 |"
    )
    assert wiersz("Z1", "opus low").endswith(
        "| 2/2 | — | 0.300 / 0.400 | 0.350 | 0.35 | 10 000 | 0 | TAK | 1 000 | 3.0 | 20 |"
    )
    assert "| 1/2 | limit budżetu | 0.100 / 3.020 | 1.560 | 1.56 |" in wiersz("Z1", "opus xhigh")
    assert "| 0.20 | 10 000 | 1 | nie |" in wiersz("Z1", "sonnet low")
    assert "| 0.20 | 10 000 | 0 | — | 1 000 |" in wiersz("Z2", "opus low")
    assert "| 1/2 | limit czasu | 0.500 / ? | 0.500 | 1.00 |" in wiersz(
        "Z3", "opus max (odniesienie)"
    )
    assert linie[-4:] == [
        "",
        "Razem 11.70 USD z wyników JSON, wszystkie próby (w tym rozgrzewki 0.07); "
        "do limitu serii 14.70 USD (limit czasu liczony jako 3.00).",
        "Przebiegi z błędem (niepoprawne): 2: Z1-opus-xhigh-2 (limit budżetu), "
        "Z3-opus-max-2 (limit czasu).",
        "Do ponowienia przy wznowieniu: 1: Z3-opus-low-1 (prób 1 z 3).",
    ]
    plik = tmp_path / "w.jsonl"
    plik.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in REKORDY) + "\n\n", encoding="utf-8"
    )
    assert pw.main(["podsumuj", "--wyniki", str(plik)]) == 0
    assert capsys.readouterr().out == tabela + "\n"
    assert pw.main(["podsumuj", "--wyniki", str(tmp_path / "brak.jsonl")]) == 0
    assert "Razem 0.00 USD" in capsys.readouterr().out
