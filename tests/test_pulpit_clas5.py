"""Testy tools/pulpit_clas5.py — strona „Pulpit CLAS-5” (Dziennik | Tokeny | Mapa | Radar w jednym artefakcie).

Strażnicy: (1) ładunek zakładki to dokładnie szkielet platformy + preludium + źródło (bajt w bajt),
a preludium jest pierwszym skryptem dziecka; (2) w blokach JSON nie ma surowego „<”, więc nic nie
zamknie bloku przed czasem; (3) zapisany tools/pulpit_clas5.html jest aktualny — edycja źródła
zakładki bez ponownego złożenia daje czerwony test zamiast cicho nieaktualnej strony.
Zachowań w przeglądarce (klawiatura, motyw, linki) testy nie odtwarzają: pilnują składni JS
(`node --check`, gdy jest node) i obecności kluczowych elementów; resztę sprawdza się na
opublikowanej stronie.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from tools import pulpit_clas5 as pc

ROOT = Path(__file__).resolve().parents[1]
IDS = ["dziennik", "tokeny", "mapa", "radar"]
OTWARCIE = '<script type="application/json" id="strona-{}">'
BLOK_RE = re.compile(r'<script type="application/json" id="strona-([a-z]+)">(.*?)</script>', re.S)
PLIKI = [pc.SZABLON, *(sciezka for _, sciezka in pc.ZAKLADKI)]


@pytest.fixture(scope="module")
def zlozony() -> str:
    return pc.zloz()


def bloki(tresc: str) -> dict[str, str]:
    return dict(BLOK_RE.findall(tresc))


def powloka(tresc: str) -> str:
    """Złożona strona bez bloków z ładunkami — to, co pisze sama powłoka."""
    return BLOK_RE.sub("", tresc)


def kopia_zrodel(cel: Path, crlf: bool = False) -> None:
    for sciezka in PLIKI:
        dane = (ROOT / sciezka).read_bytes().replace(b"\r\n", b"\n")
        if crlf:
            dane = dane.replace(b"\n", b"\r\n")
        (cel / sciezka).parent.mkdir(parents=True, exist_ok=True)
        (cel / sciezka).write_bytes(dane)


# ------------------------------------------------------------------ ładunki zakładek


@pytest.mark.parametrize("ident,sciezka", pc.ZAKLADKI)
def test_ladunek_to_szkielet_preludium_i_zrodlo(zlozony, ident, sciezka):
    dok = json.loads(bloki(zlozony)[ident])
    glowa = pc.SZKIELET_GLOWA + pc.PRELUDIUM + pc.SZKIELET_BODY
    assert dok.startswith(glowa)
    assert dok.endswith(pc.SZKIELET_KONIEC)
    czesc = dok[len(glowa) : len(dok) - len(pc.SZKIELET_KONIEC)]
    assert czesc.encode("utf-8") == (ROOT / sciezka).read_bytes().replace(b"\r\n", b"\n")


def test_szkielet_to_opakowanie_platformy():
    szkielet = pc.SZKIELET_GLOWA + pc.SZKIELET_BODY
    assert szkielet.startswith("<!doctype html><html><head><meta charset=utf8><meta name=viewport")
    assert szkielet.endswith("</style></head><body>\n")
    assert len(szkielet.encode("utf-8")) == 537  # bajt w bajt z opublikowanych Tokenów i Mapy
    assert "<script" not in szkielet.lower()
    assert pc.SZKIELET_KONIEC == "\n</body></html>\n"


@pytest.mark.parametrize("ident", IDS)
def test_preludium_pierwszym_skryptem_w_head(zlozony, ident):
    dok = json.loads(bloki(zlozony)[ident])
    pierwszy = dok.lower().find("<script")
    assert pierwszy == dok.find(pc.PRELUDIUM) == len(pc.SZKIELET_GLOWA)
    assert pierwszy < dok.find("</head>") < dok.find("<body>")


def test_preludium_ma_runtime_motyw_i_linki():
    p = pc.PRELUDIUM
    assert p.startswith("<script>") and p.endswith("</script>")
    assert p.lower().count("<script") == 1 and p.lower().count("</script") == 1
    assert "<!--" not in p
    assert "w.claude = p.claude" in p  # (a) runtime rodzica, bez opakowania
    assert "getAttribute('data-theme')" in p and "removeAttribute('data-theme')" in p  # (b)
    assert re.search(r"addEventListener\('click',.*\}, true\);", p, re.S)  # (c) faza capture
    assert "a.target = '_blank'" in p and "a.rel = 'noopener'" in p and "w.open(" in p


@pytest.mark.parametrize("ident,sciezka", pc.ZAKLADKI)
def test_zrodla_to_fragmenty_bez_opakowania(ident, sciezka):
    tekst = pc.czytaj(ROOT / sciezka).lower()
    assert tekst.startswith("<title>")
    assert not re.search(r"<!doctype|<html[\s>]|<head[\s>]|<body[\s>]|</body>|</html>", tekst)


# ------------------------------------------------------------------ bloki JSON


def test_bloki_json_bez_surowego_lt(zlozony):
    assert zlozony.count('<script type="application/json"') == len(IDS)
    for ident in IDS:
        start = zlozony.index(OTWARCIE.format(ident)) + len(OTWARCIE.format(ident))
        tekst = zlozony[start : zlozony.index("</script>", start)]
        assert "<" not in tekst, ident
        assert tekst == bloki(zlozony)[ident]


@settings(max_examples=200, deadline=None)
@example("</script><!-- <script>alert(1)</script>")
@example("")
@given(st.text())
def test_blok_json_wlasnosc_round_trip_bez_lt(tekst):
    blok = pc.blok_json("x", tekst)
    otwarcie = OTWARCIE.format("x")
    assert blok.startswith(otwarcie) and blok.endswith("</script>")
    srodek = blok[len(otwarcie) : -len("</script>")]
    assert "<" not in srodek
    assert json.loads(srodek) == tekst


# ------------------------------------------------------------------ powłoka


def test_tytul_w_pierwszych_8_kb(zlozony):
    assert zlozony.startswith("<title>Pulpit CLAS-5</title>")
    assert b"<title>Pulpit CLAS-5</title>" in zlozony.encode("utf-8")[:8192]


def test_powloka_to_fragment_bez_szkieletu():
    szablon = pc.czytaj(ROOT / pc.SZABLON)
    assert not re.search(r"<!doctype|<html[\s>]|<head[\s>]|<body[\s>]", szablon.lower())
    assert szablon.count(pc.ZNACZNIK) == 1
    assert re.search(r"html,body\{height:100%\}", szablon) and "100vh" not in szablon


def test_zakladki_z_panelami_i_ladunkami(zlozony):
    sz = powloka(zlozony)
    assert len(re.findall(r'role="tablist"', sz)) == 1
    karty = re.findall(r'<button[^>]*role="tab"[^>]*>', sz)
    assert [re.search(r'id="tab-([a-z]+)"', k).group(1) for k in karty] == IDS
    for karta, ident in zip(karty, IDS, strict=True):
        assert f'aria-controls="panel-{ident}"' in karta
    assert sum('aria-selected="true"' in k for k in karty) == 1
    for ident in IDS:
        assert re.search(
            rf'<section[^>]*role="tabpanel"[^>]*id="panel-{ident}"[^>]*aria-labelledby="tab-{ident}"',
            sz,
        )
    assert [ident for ident, _ in pc.ZAKLADKI] == IDS
    assert list(bloki(zlozony)) == IDS
    assert "var ZAKLADKI = ['dziennik', 'tokeny', 'mapa', 'radar'];" in sz


def test_hosty_zewnetrzne_powloki(zlozony):
    sz = powloka(zlozony)
    hosty = set(re.findall(r"https?://([^/\"'\s)>]+)", sz))
    assert hosty <= {"fonts.googleapis.com", "fonts.gstatic.com", "claude.ai"}, hosty
    for url in re.findall(r"https?://claude\.ai[^\"'\s<]*", sz):
        assert re.fullmatch(r"https://claude\.ai/artifact/[A-Za-z0-9]+", url), url
    assert not re.search(r"""(?:src|href)=["']//""", sz)


PALETA = {
    "jasny": {"--bg": "#ffffff", "--ink": "#141414", "--muted": "#6a6a66", "--hair": "#e4e4e0"},
    "ciemny": {"--bg": "#17181a", "--ink": "#ecece8", "--muted": "#9a9a96", "--hair": "#2a2b2e"},
}
AKCENTY = {
    "jasny": {"--accent": "#c41e24", "--s2": "#2e6da8", "--good": "#2f7d4f"},
    "ciemny": {"--accent": "#e4574d", "--s2": "#4e97db", "--good": "#5caf7f"},
}


def _zmienne(css: str) -> dict[str, str]:
    return dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", css))


def test_motyw_jasny_i_ciemny_w_obu_miejscach():
    sz = pc.czytaj(ROOT / pc.SZABLON)
    jasny = re.search(r"^:root\{(.*?)\}", sz, re.S | re.M).group(1)
    media = re.search(
        r'@media \(prefers-color-scheme: dark\)\{:root:not\(\[data-theme="light"\]\)\{(.*?)\}\}',
        sz,
        re.S,
    ).group(1)
    wymuszony = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', sz, re.S).group(1)
    for nazwa, css in (("jasny", jasny), ("ciemny", media), ("ciemny", wymuszony)):
        zmienne = _zmienne(css)
        for klucz, wartosc in {**PALETA[nazwa], **AKCENTY[nazwa]}.items():
            assert zmienne.get(klucz) == wartosc, (nazwa, klucz)
    assert media == wymuszony
    assert "color-scheme:dark" in media and "color-scheme:light" in jasny


# ------------------------------------------------------------------ plik do publikacji


def test_zapisany_pulpit_aktualny(zlozony):
    rada = "tools/pulpit_clas5.html nieaktualny — uruchom python3 tools/pulpit_clas5.py"
    assert pc.WYJSCIE.exists(), rada
    assert pc.czytaj(pc.WYJSCIE) == zlozony, rada


def test_zlozenie_deterministyczne_i_niezalezne_od_crlf(tmp_path, zlozony):
    assert pc.zloz() == zlozony
    kopia_zrodel(tmp_path, crlf=True)
    assert pc.zloz(tmp_path) == zlozony


def test_znacznik_ladunkow_dokladnie_raz(tmp_path):
    kopia_zrodel(tmp_path)
    for tresc in ("<title>x</title>", pc.ZNACZNIK * 2):
        (tmp_path / pc.SZABLON).write_text(tresc, encoding="utf-8")
        with pytest.raises(ValueError):
            pc.zloz(tmp_path)


def test_main_zapis_i_sprawdz(tmp_path, monkeypatch, capsys):
    plik, rutyna = tmp_path / "pulpit.html", tmp_path / "rutyna.md"
    monkeypatch.setattr(pc, "WYJSCIE", plik)
    monkeypatch.setattr(pc, "RUTYNA", rutyna)
    assert pc.main(["--sprawdz"]) == 1  # brak plików
    assert pc.main([]) == 0
    assert plik.read_bytes() == pc.zloz().encode("utf-8")  # UTF-8, końce linii LF
    assert rutyna.read_bytes() == pc.instrukcja_rutyny().encode("utf-8")
    assert pc.main(["--sprawdz"]) == 0
    plik.write_text(pc.zloz() + " ", encoding="utf-8")
    assert pc.main(["--sprawdz"]) == 1
    plik.write_text(pc.zloz(), encoding="utf-8", newline="\n")
    rutyna.write_text(pc.instrukcja_rutyny() + " ", encoding="utf-8")
    assert pc.main(["--sprawdz"]) == 1  # sama instrukcja rutyny nieaktualna
    wyjscie = capsys.readouterr()
    assert "razem" in wyjscie.out and "suma SHA-256" in wyjscie.out
    assert "NIEAKTUALNY: rutyna.md" in wyjscie.err


def _skrypt_powloki() -> str:
    return re.findall(r"<script>(.*?)</script>", pc.czytaj(ROOT / pc.SZABLON), re.S)[0]


def test_powloka_przekazuje_nonce_do_skryptow_dziecka():
    skrypt = _skrypt_powloki()
    przechwycenie = "var NONCE = (document.currentScript && document.currentScript.nonce) || '';"
    assert przechwycenie in skrypt
    # synchronicznie: przed pierwszą funkcją wewnątrz IIFE, zanim cokolwiek trafi do obsługi zdarzeń
    poczatek = skrypt.index("'use strict';")
    assert poczatek < skrypt.index(przechwycenie) < skrypt.index("function ", poczatek)
    assert "getAttribute('nonce')" not in skrypt  # atrybut przeglądarka ukrywa, liczy się .nonce
    assert r"/<script(?=[\s>])[^>]*>/gi" in skrypt
    assert "f.srcdoc = zNonce(dok, NONCE);" in skrypt


@pytest.mark.skipif(shutil.which("node") is None, reason="brak node")
def test_znonce_z_nonce_i_bez_node(tmp_path, zlozony):
    funkcja = re.search(
        r"^  function zNonce\(html, nonce\) \{\n.*?^  \}\n", _skrypt_powloki(), re.S | re.M
    )
    dokumenty = [json.loads(tekst) for tekst in bloki(zlozony).values()]
    reczny = '<script nonce="stary">a</script><SCRIPT type="module">b</SCRIPT><scripts>c'
    przypadki = [[html, nonce] for html in [*dokumenty, reczny] for nonce in ("", 'ab+/="&')]
    (tmp_path / "wejscie.json").write_text(json.dumps(przypadki), encoding="utf-8")
    (tmp_path / "nonce.js").write_text(
        funkcja.group(0)
        + "const fs = require('fs');\n"
        + "const p = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));\n"
        + "process.stdout.write(JSON.stringify(p.map(([h, n]) => zNonce(h, n))));\n",
        encoding="utf-8",
    )
    wynik = subprocess.run(
        ["node", str(tmp_path / "nonce.js"), str(tmp_path / "wejscie.json")],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert wynik.returncode == 0, wynik.stderr
    wstawka = ' nonce="ab+/=&quot;&amp;"'
    wyjscia = json.loads(wynik.stdout)
    for (html, nonce), wyjscie in zip(przypadki, wyjscia, strict=True):
        if not nonce:
            assert wyjscie == html  # bez nonce dokument bez zmian
            continue
        tagi = re.findall(r"<script(?=[\s>])[^>]*>", wyjscie, re.I)
        assert len(tagi) == len(re.findall(r"<script(?=[\s>])[^>]*>", html, re.I))
        assert all(len(re.findall(r"\snonce\s*=", t, re.I)) == 1 for t in tagi)  # bez podwajania
        assert wyjscie.replace(wstawka, "") == html  # tylko wstawka, nic więcej
    assert [wyjscia[2 * k + 1].count(wstawka) for k in range(len(IDS))] == [2, 2, 1, 2]  # preludium + strona
    assert wyjscia[-1].count(wstawka) == 1  # tylko <SCRIPT type="module">


@pytest.mark.skipif(shutil.which("node") is None, reason="brak node")
def test_skrypty_powloki_i_preludium_poprawne_skladniowo(tmp_path):
    szablon = pc.czytaj(ROOT / pc.SZABLON)
    skrypty = re.findall(r"<script>(.*?)</script>", szablon, re.S)
    skrypty.append(pc.PRELUDIUM[len("<script>") : -len("</script>")])
    assert len(skrypty) == 2
    for n, kod in enumerate(skrypty):
        plik = tmp_path / f"skrypt{n}.js"
        plik.write_text(kod, encoding="utf-8")
        wynik = subprocess.run(["node", "--check", str(plik)], capture_output=True, text=True)
        assert wynik.returncode == 0, wynik.stderr


# ------------------------------------------------------------------ instrukcja rutyny zakładki Dziennik


def _z_instrukcji(tekst: str) -> tuple[str, str]:
    """(skrypt między znacznikami, suma z linii „Musi wyjść:”) — tak, jak czyta je rutyna."""
    skrypt = tekst.split("=====POCZĄTEK SKRYPTU=====\n", 1)[1].split("\n" + pc.KONIEC_SKRYPTU, 1)[0]
    return skrypt, re.search(r"^Musi wyjść: ([0-9a-f]{64})$", tekst, re.M)[1]


def test_zapisana_instrukcja_rutyny_aktualna():
    rada = (
        "tools/rutyna_dziennika.md nieaktualna — uruchom python3 tools/pulpit_clas5.py "
        "i wklej nową instrukcję w rutynę Cowork"
    )
    assert pc.RUTYNA.exists(), rada
    assert pc.czytaj(pc.RUTYNA) == pc.instrukcja_rutyny(), rada


@pytest.mark.parametrize("konce", ["\n", "\r\n"])
def test_instrukcja_niesie_skrypt_danych_i_jego_sume(tmp_path, konce):
    """Druga droga: plik zapisany jak w kroku 1 rutyny (także z CRLF), suma liczona jej poleceniem."""
    skrypt, suma = _z_instrukcji(pc.instrukcja_rutyny())
    assert skrypt == pc.czytaj(ROOT / pc.SKRYPT_RUTYNY).rstrip()
    (tmp_path / "gen_dziennik.py").write_bytes((skrypt + "\n").replace("\n", konce).encode("utf-8"))
    polecenie = re.search(r'^python3 -c "(.+)"$', pc.czytaj(ROOT / pc.SZABLON_RUTYNY), re.M)[1]
    wynik = subprocess.run(
        [sys.executable, "-c", polecenie], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert wynik.stdout.strip() == suma == pc.suma_skryptu(skrypt)


def test_instrukcja_odrzuca_zly_szablon_i_znacznik_w_skrypcie(tmp_path):
    for sciezka in (pc.SZABLON_RUTYNY, pc.SKRYPT_RUTYNY):
        (tmp_path / sciezka).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / sciezka).write_text(pc.czytaj(ROOT / sciezka), encoding="utf-8")
    assert pc.instrukcja_rutyny(tmp_path) == pc.instrukcja_rutyny()
    szablon = pc.czytaj(ROOT / pc.SZABLON_RUTYNY)
    for zly in (szablon.replace("@SUMA@", ""), szablon + "@SKRYPT@", szablon + pc.KONIEC_SKRYPTU):
        (tmp_path / pc.SZABLON_RUTYNY).write_text(zly, encoding="utf-8")
        with pytest.raises(ValueError):
            pc.instrukcja_rutyny(tmp_path)
    (tmp_path / pc.SZABLON_RUTYNY).write_text(szablon, encoding="utf-8")
    (tmp_path / pc.SKRYPT_RUTYNY).write_text(f"x = 1\n# {pc.KONIEC_SKRYPTU}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        pc.instrukcja_rutyny(tmp_path)


@settings(max_examples=200, deadline=None)
@given(st.text().map(lambda t: t.replace("\r", "")))  # st.text() bez samotnych surogatów (UTF-8)
def test_suma_skryptu_nie_zalezy_od_crlf_ani_koncowych_bialych_znakow(tekst):
    assert pc.suma_skryptu(tekst.replace("\n", "\r\n") + " \n\t") == pc.suma_skryptu(tekst)
