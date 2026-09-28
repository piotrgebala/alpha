"""Testy tools/pomiar_wysilku.py — pomiar T5 z docs/rag/12 (plan, komenda, ocena, podsumowanie).

Bez `claude` i sieci: `subprocess.run` podstawiany przez monkeypatch. Ocena Z2 uruchamia pytest
na prawdziwych piaskownicach w katalogu tymczasowym (ok. 0,6 s na ocenę).
"""

from __future__ import annotations

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
    ],
)
def test_liczba_przyklady(tekst, liczba):
    assert pw._liczba(tekst) == pytest.approx(liczba)


def test_liczba_bez_liczby_to_none():
    assert pw._liczba("") is None
    assert pw._liczba("NIEMIERZALNA") is None
    assert pw._liczba("1.2.3") is None


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
    """Klucze liczone na bieżącym repo; przesunięcie `expected_trades` w metrics.py = nowy klucz Z1."""
    pw.sprawdz_kopie_repo(REPO)
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


def test_sprawdz_kopie_repo_przesunieta_lub_za_krotka(tmp_path):
    pw.sprawdz_kopie_repo(_kopia_repo(tmp_path / "ok"))
    with pytest.raises(ValueError, match="klucz Z1"):
        pw.sprawdz_kopie_repo(_kopia_repo(tmp_path / "przesunieta", linia=649))
    with pytest.raises(ValueError, match="klucz Z1"):
        pw.sprawdz_kopie_repo(_kopia_repo(tmp_path / "krotka", linia=0, razem=10))


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


# --- wynik JSON i uruchamianie (subprocess.run podstawiony) ---------------------------------

PRZYKLAD_JSON = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
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


def test_rekord_z_json_koszt_tokeny_i_modele():
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
        "blad_api": False,
        "odpowiedz": PRZYKLAD_JSON["result"],
    }
    pusty = pw.rekord_z_json({"is_error": True})
    assert (pusty["koszt_usd"], pusty["wyjscie_wszystkie_modele"], pusty["modele"]) == (0.0, 0, {})
    assert (pusty["tury"], pusty["blad_api"], pusty["odpowiedz"]) == (None, True, "")


def _wpis(zadanie: str | None, narzedzia: str) -> dict:
    return next(w for w in pw.plan() if w["zadanie"] == zadanie and w["narzedzia"] == narzedzia)


def test_uruchom_jeden_z3_sciezka_szczesliwa(tmp_path, monkeypatch):
    wywolania = []

    def fake_run(cmd, **kw):
        wywolania.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(PRZYKLAD_JSON), stderr="")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    wpis, env = _wpis("Z3", "odczyt"), {"PATH": "/x"}
    r = pw.uruchom_jeden(wpis, tmp_path / "repo", tmp_path / "piaskownica", env)
    [(cmd, kw)] = wywolania
    assert cmd == pw.komenda(pw.ZADANIA["Z3"]["prompt"], wpis["model"], wpis["wysilek"], "odczyt")
    assert kw["cwd"] == tmp_path / "repo" and kw["env"] is env
    assert kw["stdin"] is subprocess.DEVNULL and kw["timeout"] == pw.LIMIT_CZASU_S
    assert not (tmp_path / "piaskownica").exists()  # odczyt nie buduje piaskownicy
    assert r["id"] == wpis["id"] and r["kod_wyjscia"] == 0 and "blad" not in r
    assert r["koszt_usd"] == 0.4213 and r["ocena"]["poprawna"] is True
    assert pw._udany(r)


def test_uruchom_jeden_wyjscie_nie_json_w_piaskownicy(tmp_path, monkeypatch):
    piaskownica = tmp_path / "piaskownica"

    def fake_run(cmd, **kw):
        assert kw["cwd"] == piaskownica and (piaskownica / "miary.py").exists()
        assert cmd[2] == pw.ROZGRZEWKA
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Error: brak sieci")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    r = pw.uruchom_jeden(_wpis(None, "zapis"), tmp_path / "repo", piaskownica, {})
    assert r["kod_wyjscia"] == 1 and r["blad"].startswith("wyjście nie jest JSON")
    assert "brak sieci" in r["blad"] and "ocena" not in r and "koszt_usd" not in r
    assert not pw._udany(r)


def test_uruchom_jeden_przekroczony_czas(tmp_path, monkeypatch):
    def fake_run(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    r = pw.uruchom_jeden(_wpis("Z1", "odczyt"), tmp_path, tmp_path / "piaskownica", {})
    assert (r["blad"], r["kod_wyjscia"], r["czas_s"]) == (
        "przekroczony czas",
        None,
        pw.LIMIT_CZASU_S,
    )
    assert "ocena" not in r and not pw._udany(r)


def test_main_uruchom_limit_wznowienie_i_budzet_serii(tmp_path, monkeypatch, capsys):
    """Nieudany przebieg wraca przy wznowieniu, udany nie; seria staje po wyczerpaniu budżetu."""
    repo, wyniki, piaskownica = (
        _kopia_repo(tmp_path / "repo"),
        tmp_path / "w.jsonl",
        tmp_path / "t5" / "p",
    )
    wywolania = []

    def fake_run(cmd, **kw):
        wywolania.append(kw)
        if len(wywolania) == 1:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="przerwane")
        o = {"total_cost_usd": 0.5, "result": "OK", "num_turns": 1, "is_error": False}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(o), stderr="")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    argv = [
        "uruchom",
        "--wyniki",
        str(wyniki),
        "--repo",
        str(repo),
        "--piaskownica",
        str(piaskownica),
    ]
    k = _kolejnosc(pw.ZIARNO)
    assert pw.main(argv + ["--limit", "3"]) == 0
    assert pw.main(argv + ["--limit", "2"]) == 0
    assert [r["id"] for r in pw.wczytaj(wyniki)] == [k[0], k[1], k[2], k[0], k[3]]
    monkeypatch.setattr(pw, "LIMIT_SERII_USD", 2.5)  # wydane 2,0 → jeszcze jeden przebieg
    assert pw.main(argv) == 0
    assert [r["id"] for r in pw.wczytaj(wyniki)] == [k[0], k[1], k[2], k[0], k[3], k[4]]
    assert "seria: wydane 2.50 USD, wykonano teraz 1" in capsys.readouterr().out
    bin_t5 = str(tmp_path / "t5" / "t5_bin")
    assert all(kw["env"]["PATH"].split(os.pathsep)[0] == bin_t5 for kw in wywolania)


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
        "wyjscie_wszystkie_modele": 1000,
        "tury": 3,
        "czas_s": 20.0,
        "blad_api": False,
    }
    if zad:
        r["ocena"] = {"poprawna": poprawna}
    return dict(r, **inne)


REKORDY = [
    _rek(None, "opus", "max", 0.05, powt=0),
    _rek(None, "sonnet", "low", 0.02, powt=0),
    _rek("Z1", "opus", "max", 1.0),
    _rek("Z1", "opus", "max", 1.0, powt=2),
    _rek("Z1", "opus", "low", 0.3),
    _rek("Z1", "opus", "low", 0.4, poprawna=False, powt=2),
    _rek("Z1", "opus", "medium", 0.7),
    _rek("Z1", "sonnet", "high", 0.9),
    _rek("Z1", "opus", "high", 3.0, blad_api=True),  # np. wyczerpany budżet przebiegu
    {
        "id": "Z1-sonnet-low-1",
        "zadanie": "Z1",
        "model": "sonnet",
        "wysilek": "low",
        "kod_wyjscia": 1,
        "blad": "wyjście nie jest JSON: ",
    },
    _rek("Z3", "sonnet", "low", 0.2),
]


def test_podsumuj_stosunek_do_odniesienia_opus_max():
    w = pw.podsumuj(REKORDY)
    klucze = [(r["zadanie"], r["model"], r["wysilek"]) for r in w]
    assert klucze == [  # kolejność: ZADANIA × KONFIGURACJE; rozgrzewki i nieudane poza tabelą
        ("Z1", "opus", "low"),
        ("Z1", "opus", "medium"),
        ("Z1", "opus", "max"),
        ("Z1", "sonnet", "high"),
        ("Z3", "sonnet", "low"),
    ]
    wiersz = dict(zip(klucze, w, strict=True))
    low = wiersz["Z1", "opus", "low"]
    assert (low["n"], low["poprawne"], low["koszty"], low["odniesienie_poprawne"]) == (
        2,
        1,
        [0.3, 0.4],
        2,
    )
    assert low["koszt_sredni"] == pytest.approx(0.35)
    assert low["wobec_odniesienia"] == pytest.approx(0.35)
    assert wiersz["Z1", "opus", "max"]["wobec_odniesienia"] == pytest.approx(1.0)
    assert wiersz["Z1", "sonnet", "high"]["wobec_odniesienia"] == pytest.approx(0.9)
    assert wiersz["Z3", "sonnet", "low"]["wobec_odniesienia"] is None  # brak odniesienia


def test_tabela_md_oznaczenie_progu_i_nieudane(tmp_path, capsys):
    tabela = pw.tabela_md(pw.podsumuj(REKORDY), REKORDY)
    linie = tabela.splitlines()
    assert "wobec opus max" in linie[0]
    wiersze = [x for x in linie if x.startswith("| Z")]
    assert len(wiersze) == 5

    def wiersz(zad: str, konf: str) -> str:
        return next(x for x in wiersze if x.startswith(f"| {zad} | {konf} |"))

    assert wiersz("Z1", "opus low").endswith(
        "| 1/2 | 0.300 / 0.400 | 0.350 | 0.35 (≤ 0.70) | 1 000 | 3.0 | 20 |"
    )
    assert "| 0.70 (≤ 0.70) |" in wiersz("Z1", "opus medium")  # granica włącznie
    assert "| 0.90 |" in wiersz("Z1", "sonnet high") and "≤" not in wiersz("Z1", "sonnet high")
    assert "| 1.00 |" in wiersz("Z1", "opus max")
    assert "| — |" in wiersz("Z3", "sonnet low")
    # „Razem” z nieudanymi: przebieg, który wyczerpał limit 3 USD, też kosztował
    assert linie[-1] == (
        "Razem 7.57 USD (w tym rozgrzewki 0.07); przebiegów udanych 9, nieudanych 2: "
        "Z1-opus-high-1, Z1-sonnet-low-1."
    )
    plik = tmp_path / "w.jsonl"
    plik.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in REKORDY) + "\n\n", encoding="utf-8"
    )
    assert pw.main(["podsumuj", "--wyniki", str(plik)]) == 0
    assert capsys.readouterr().out == tabela + "\n"
    assert pw.main(["podsumuj", "--wyniki", str(tmp_path / "brak.jsonl")]) == 0
    assert "Razem 0.00 USD" in capsys.readouterr().out
